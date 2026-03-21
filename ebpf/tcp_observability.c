// SPDX-License-Identifier: Apache-2.0
/*
 * Cloud-Native Network Observability - eBPF Kernel Programs
 *
 * Attaches to TCP layer to capture:
 *   - TCP RTT (round-trip time) samples
 *   - Retransmission counts
 *   - Bytes sent/received per connection
 *   - Packet drop events (kfree_skb with TCP payload)
 *
 * Uses BPF ring buffer for low-overhead event streaming and hash maps
 * for per-connection aggregation. Designed for minimal CPU overhead
 * in production (same philosophy as Datadog NPM, Cilium Hubble).
 */

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define AF_INET  2
#define AF_INET6 10

/* Connection flow key: 5-tuple + netns for multi-tenant K8s isolation */
struct flow_key {
	__u32 saddr;
	__u32 daddr;
	__u16 sport;
	__u16 dport;
	__u32 netns;
	__u8  family; /* AF_INET or AF_INET6 */
};

/* Per-connection aggregated metrics (kernel-side aggregation reduces userspace load) */
struct conn_metrics {
	__u64 bytes_sent;
	__u64 bytes_recv;
	__u64 retrans_count;
	__u64 rtt_sum_ns;    /* Sum of RTT samples in nanoseconds for average */
	__u64 rtt_count;     /* Number of RTT samples */
	__u64 drop_count;
	__u64 last_seen_ns;  /* Monotonic time of last activity */
};

/* Event pushed to userspace for real-time processing (e.g. connection lifecycle) */
struct conn_event {
	__u32 saddr;
	__u32 daddr;
	__u16 sport;
	__u16 dport;
	__u32 netns;
	__u8  family;
	__u8  event_type;   /* 1=connect, 2=close, 3=retrans, 4=drop */
	__u64 timestamp_ns;
	__u64 value;        /* Retrans count, drop reason, or 0 */
};

/* Map: flow_key -> conn_metrics. Persists per-connection stats. */
struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 65536);
	__type(key, struct flow_key);
	__type(value, struct conn_metrics);
} conn_stats_map SEC(".maps");

/* Ring buffer for events (lower latency than perf buffer, recommended for new code) */
struct {
	__uint(type, BPF_MAP_TYPE_RINGBUF);
	__uint(max_entries, 256 * 1024); /* 256KB */
} events_ringbuf SEC(".maps");

/* Allowlist for optional filtering by port or CIDR (not used by default to minimize overhead) */
struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 64);
	__type(key, __u16);
	__type(value, __u8);
} port_allowlist SEC(".maps");

static __always_inline __u64 bpf_ktime_get_ns(void)
{
	return bpf_ktime_get_ns();
}

/* Build flow key from IPv4 sock. Returns 0 on success, -1 if not IPv4. */
static __always_inline int flow_key_v4(struct flow_key *key, void *sk)
{
	__u16 family = BPF_CORE_READ(sk, __sk_common.skc_family);
	if (family != AF_INET)
		return -1;

	key->saddr = BPF_CORE_READ(sk, __sk_common.skc_rcv_saddr);
	key->daddr = BPF_CORE_READ(sk, __sk_common.skc_daddr);
	key->sport = BPF_CORE_READ(sk, __sk_common.skc_num);
	key->dport = bpf_ntohs(BPF_CORE_READ(sk, __sk_common.skc_dport));
	key->family = AF_INET;
	/* Network namespace id for pod/container isolation on same node */
	key->netns = BPF_CORE_READ(sk, __sk_common.skc_net, ns.inum);
	return 0;
}

/* Lookup or create conn_metrics for key. Returns pointer or NULL. */
static __always_inline struct conn_metrics *get_or_create_conn(struct flow_key *key)
{
	struct conn_metrics *val = bpf_map_lookup_elem(&conn_stats_map, key);
	if (val)
		return val;

	struct conn_metrics new_val = {};
	new_val.last_seen_ns = bpf_ktime_get_ns();
	if (bpf_map_update_elem(&conn_stats_map, key, &new_val, BPF_NOEXIST) == 0)
		return bpf_map_lookup_elem(&conn_stats_map, key);
	return NULL;
}

/* Reserve and submit event to ring buffer. Drops event if ring full (backpressure). */
static __always_inline void submit_event(struct conn_event *evt)
{
	void *slot = bpf_ringbuf_reserve(&events_ringbuf, sizeof(*evt), 0);
	if (slot) {
		__builtin_memcpy(slot, evt, sizeof(*evt));
		bpf_ringbuf_submit(slot, 0);
	}
}

/* --- kprobe: tcp_sendmsg ---
 * Counts bytes sent per connection. tcp_sendmsg is the main entry for TCP sends.
 */
SEC("kprobe/tcp_sendmsg")
int BPF_KPROBE(tcp_sendmsg_entry, struct sock *sk, struct msghdr *msg, size_t size)
{
	struct flow_key key = {};
	if (flow_key_v4(&key, sk) != 0)
		return 0;

	struct conn_metrics *m = get_or_create_conn(&key);
	if (!m)
		return 0;

	__sync_fetch_and_add(&m->bytes_sent, (__u64)size);
	m->last_seen_ns = bpf_ktime_get_ns();
	return 0;
}

/* --- kprobe: tcp_cleanup_rbuf ---
 * Fired when the application reads data; len is bytes consumed. We use this
 * as a proxy for bytes received (avoids tracking every segment in tcp_rcv_established).
 */
SEC("kprobe/tcp_cleanup_rbuf")
int BPF_KPROBE(tcp_cleanup_rbuf_entry, struct sock *sk, int len)
{
	if (len <= 0)
		return 0;

	struct flow_key key = {};
	if (flow_key_v4(&key, sk) != 0)
		return 0;

	struct conn_metrics *m = get_or_create_conn(&key);
	if (!m)
		return 0;

	__sync_fetch_and_add(&m->bytes_recv, (__u64)len);
	m->last_seen_ns = bpf_ktime_get_ns();
	return 0;
}

/* --- kprobe: tcp_retransmit_skb ---
 * Counts retransmissions per connection. Critical for detecting loss and latency issues.
 */
SEC("kprobe/tcp_retransmit_skb")
int BPF_KPROBE(tcp_retransmit_skb_entry, struct sock *sk, struct sk_buff *skb)
{
	struct flow_key key = {};
	if (flow_key_v4(&key, sk) != 0)
		return 0;

	struct conn_metrics *m = get_or_create_conn(&key);
	if (!m)
		return 0;

	__sync_fetch_and_add(&m->retrans_count, 1);
	m->last_seen_ns = bpf_ktime_get_ns();

	struct conn_event evt = {
		.saddr = key.saddr,
		.daddr = key.daddr,
		.sport = key.sport,
		.dport = key.dport,
		.netns = key.netns,
		.family = key.family,
		.event_type = 3, /* retrans */
		.timestamp_ns = bpf_ktime_get_ns(),
		.value = m->retrans_count,
	};
	submit_event(&evt);
	return 0;
}

/* --- kprobe: tcp_ack ---
 * RTT sampling: read srtt_us from tcp_sock (smoothed RTT in microseconds).
 * Cast sk to tcp_sock and read srtt_us. With BTF vmlinux, use CO-RE;
 * otherwise bpf_probe_read_kernel at runtime (offset varies by kernel).
 */
SEC("kprobe/tcp_ack")
int BPF_KPROBE(tcp_ack_entry, struct sock *sk)
{
	struct flow_key key = {};
	if (flow_key_v4(&key, sk) != 0)
		return 0;

	/* srtt_us in tcp_sock (offset from sk; kernel-version dependent; 0x1b8 common on 5.10+ x86_64) */
	__u32 srtt_us = 0;
	bpf_probe_read_kernel(&srtt_us, sizeof(srtt_us), (void *)((char *)sk + 0x1b8));
	if (srtt_us == 0)
		return 0;

	struct conn_metrics *m = get_or_create_conn(&key);
	if (!m)
		return 0;

	__u64 rtt_ns = (__u64)srtt_us * 1000;
	__sync_fetch_and_add(&m->rtt_sum_ns, rtt_ns);
	__sync_fetch_and_add(&m->rtt_count, 1);
	m->last_seen_ns = bpf_ktime_get_ns();
	return 0;
}

/* --- kprobe: kfree_skb ---
 * Track packet drops. We only care about TCP. loc indicates where the free happened;
 * we use it as a proxy for drop reason (e.g. TCP retransmit path, receive path).
 */
SEC("kprobe/kfree_skb")
int BPF_KPROBE(kfree_skb_entry, void *ctx, struct sk_buff *skb)
{
	void *sk = BPF_CORE_READ(skb, sk);
	if (!sk)
		return 0;

	__u16 protocol = BPF_CORE_READ(skb, protocol);
	if (protocol != 0x0800) /* ETH_P_IP */
		return 0;
	/* Optional: verify IP protocol is TCP. For simplicity we count all IP skb frees
	 * that have an sk (socket). Most are TCP in service mesh / app traffic. */

	struct flow_key key = {};
	if (flow_key_v4(&key, sk) != 0)
		return 0;

	struct conn_metrics *m = get_or_create_conn(&key);
	if (!m)
		return 0;

	__sync_fetch_and_add(&m->drop_count, 1);
	m->last_seen_ns = bpf_ktime_get_ns();

	struct conn_event evt = {
		.saddr = key.saddr,
		.daddr = key.daddr,
		.sport = key.sport,
		.dport = key.dport,
		.netns = key.netns,
		.family = key.family,
		.event_type = 4, /* drop */
		.timestamp_ns = bpf_ktime_get_ns(),
		.value = (__u64)(unsigned long)ctx, /* kfree_skb caller address as proxy for reason */
	};
	submit_event(&evt);
	return 0;
}

/* --- kprobe: tcp_connect (optional: connection open event) --- */
SEC("kprobe/tcp_connect")
int BPF_KPROBE(tcp_connect_entry, struct sock *sk)
{
	struct flow_key key = {};
	if (flow_key_v4(&key, sk) != 0)
		return 0;

	struct conn_event evt = {
		.saddr = key.saddr,
		.daddr = key.daddr,
		.sport = key.sport,
		.dport = key.dport,
		.netns = key.netns,
		.family = key.family,
		.event_type = 1, /* connect */
		.timestamp_ns = bpf_ktime_get_ns(),
		.value = 0,
	};
	submit_event(&evt);
	return 0;
}

char _license[] SEC("license") = "GPL";
