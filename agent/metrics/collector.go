// SPDX-License-Identifier: Apache-2.0
// Package metrics exposes eBPF connection stats as Prometheus metrics
// with optional Kubernetes labels (pod, namespace, service, node).

package metrics

import (
	"context"
	"net"
	"strconv"
	"sync"

	"github.com/prometheus/client_golang/prometheus"
	"netscope/agent/ebpfimpl"
	"netscope/agent/k8s"
)

// Collector implements prometheus.Collector by reading from eBPF maps
// and optionally enriching with K8s metadata.
type Collector struct {
	loader   *ebpfimpl.Loader
	resolver k8s.IPResolver
	nodeName string

	// Gauges: current snapshot of per-flow metrics (reset each scrape; we report deltas or latest)
	bytesSent   *prometheus.Desc
	bytesRecv   *prometheus.Desc
	retrans     *prometheus.Desc
	rttAvgNs    *prometheus.Desc
	rttSamples  *prometheus.Desc
	drops       *prometheus.Desc

	// Optional: counters for events from ring buffer (retrans/drop events)
	eventRetrans *prometheus.Desc
	eventDrops   *prometheus.Desc

	mu             sync.Mutex
	lastKeys       map[flowKey]connSnapshot
	retransEvents  uint64
	dropEvents     uint64
}

type flowKey struct {
	saddr, daddr uint32
	sport, dport uint16
	netns        uint32
}

type connSnapshot struct {
	bytesSent, bytesRecv uint64
	retrans, drops       uint64
	rttSum, rttCount     uint64
}

func NewCollector(loader *ebpfimpl.Loader, resolver k8s.IPResolver, nodeName string) *Collector {
	commonLabels := []string{"node", "src_ip", "dst_ip", "src_port", "dst_port"}
	k8sLabels := []string{"src_pod", "src_namespace", "src_svc", "dst_pod", "dst_namespace", "dst_svc"}
	allLabels := commonLabels
	if resolver != nil {
		allLabels = append(commonLabels, k8sLabels...)
	}
	return &Collector{
		loader:   loader,
		resolver: resolver,
		nodeName: nodeName,
		bytesSent: prometheus.NewDesc(
			"network_observability_tcp_bytes_sent_total",
			"Total bytes sent on this connection (from eBPF tcp_sendmsg).",
			allLabels, nil,
		),
		bytesRecv: prometheus.NewDesc(
			"network_observability_tcp_bytes_recv_total",
			"Total bytes received on this connection (from eBPF tcp_cleanup_rbuf).",
			allLabels, nil,
		),
		retrans: prometheus.NewDesc(
			"network_observability_tcp_retransmissions_total",
			"Number of TCP retransmissions for this connection.",
			allLabels, nil,
		),
		rttAvgNs: prometheus.NewDesc(
			"network_observability_tcp_rtt_avg_nanoseconds",
			"Average RTT in nanoseconds (smoothed RTT from kernel).",
			allLabels, nil,
		),
		rttSamples: prometheus.NewDesc(
			"network_observability_tcp_rtt_samples_total",
			"Number of RTT samples used for average.",
			allLabels, nil,
		),
		drops: prometheus.NewDesc(
			"network_observability_tcp_drops_total",
			"Number of packet drops (kfree_skb) for this connection.",
			allLabels, nil,
		),
		eventRetrans: prometheus.NewDesc(
			"network_observability_events_retrans_total",
			"Retransmission events from ring buffer (per node).",
			[]string{"node"}, nil,
		),
			eventDrops: prometheus.NewDesc(
			"network_observability_events_drops_total",
			"Drop events from ring buffer (per node).",
			[]string{"node"}, nil,
		),
		lastKeys:     make(map[flowKey]connSnapshot),
		retransEvents: 0,
		dropEvents:    0,
	}
}

// Scrape reads eBPF maps and ring buffer; updates internal state for Describe/Collect.
func (c *Collector) Scrape(ctx context.Context) error {
	// Consume ring buffer events (optional counters)
	var retransEvents, dropEvents uint64
	c.loader.ReadEvents(func(evt ebpfimpl.ConnEvent) {
		switch evt.EventType {
		case 3:
			retransEvents++
		case 4:
			dropEvents++
		}
	})
	c.mu.Lock()
	c.retransEvents = retransEvents
	c.dropEvents = dropEvents
	c.mu.Unlock()

	// Iterate conn_stats_map and store latest snapshot for Collect
	snapshot := make(map[flowKey]connSnapshot)
	err := c.loader.IterateConnStats(func(key ebpfimpl.FlowKey, val ebpfimpl.ConnMetrics) error {
		if key.Family != 2 {
			return nil
		}
		k := flowKey{key.Saddr, key.Daddr, key.Sport, key.Dport, key.Netns}
		snapshot[k] = connSnapshot{
			bytesSent: val.BytesSent,
			bytesRecv: val.BytesRecv,
			retrans:   val.RetransCount,
			drops:     val.DropCount,
			rttSum:    val.RttSumNs,
			rttCount:  val.RttCount,
		}
		return nil
	})
	if err != nil {
		return err
	}
	c.mu.Lock()
	c.lastKeys = snapshot
	c.mu.Unlock()
	return nil
}

// Describe implements prometheus.Collector.
func (c *Collector) Describe(ch chan<- *prometheus.Desc) {
	ch <- c.bytesSent
	ch <- c.bytesRecv
	ch <- c.retrans
	ch <- c.rttAvgNs
	ch <- c.rttSamples
	ch <- c.drops
	ch <- c.eventRetrans
	ch <- c.eventDrops
}

// Collect implements prometheus.Collector; reports current snapshot from last Scrape.
func (c *Collector) Collect(ch chan<- prometheus.Metric) {
	c.mu.Lock()
	snapshot := make(map[flowKey]connSnapshot)
	for k, v := range c.lastKeys {
		snapshot[k] = v
	}
	re, de := c.retransEvents, c.dropEvents
	c.mu.Unlock()

	for k, s := range snapshot {
		srcIP := net.IP(uint32ToBytes(k.saddr))
		dstIP := net.IP(uint32ToBytes(k.daddr))
		labels := []string{c.nodeName, srcIP.String(), dstIP.String(),
			portStr(k.sport), portStr(k.dport)}
		if c.resolver != nil {
			srcPod, srcNs, srcSvc := c.resolver.Resolve(k.saddr, k.sport, true)
			dstPod, dstNs, dstSvc := c.resolver.Resolve(k.daddr, k.dport, false)
			labels = append(labels, srcPod, srcNs, srcSvc, dstPod, dstNs, dstSvc)
		}
		ch <- prometheus.MustNewConstMetric(c.bytesSent, prometheus.CounterValue, float64(s.bytesSent), labels...)
		ch <- prometheus.MustNewConstMetric(c.bytesRecv, prometheus.CounterValue, float64(s.bytesRecv), labels...)
		ch <- prometheus.MustNewConstMetric(c.retrans, prometheus.CounterValue, float64(s.retrans), labels...)
		ch <- prometheus.MustNewConstMetric(c.drops, prometheus.CounterValue, float64(s.drops), labels...)
		ch <- prometheus.MustNewConstMetric(c.rttSamples, prometheus.CounterValue, float64(s.rttCount), labels...)
		var rttAvg float64
		if s.rttCount > 0 {
			rttAvg = float64(s.rttSum) / float64(s.rttCount)
		}
		ch <- prometheus.MustNewConstMetric(c.rttAvgNs, prometheus.GaugeValue, rttAvg, labels...)
	}
	ch <- prometheus.MustNewConstMetric(c.eventRetrans, prometheus.CounterValue, float64(re), c.nodeName)
	ch <- prometheus.MustNewConstMetric(c.eventDrops, prometheus.CounterValue, float64(de), c.nodeName)
}

func uint32ToBytes(u uint32) []byte {
	return []byte{byte(u), byte(u >> 8), byte(u >> 16), byte(u >> 24)}
}

func portStr(p uint16) string {
	return strconv.FormatUint(uint64(p), 10)
}