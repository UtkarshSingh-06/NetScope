// SPDX-License-Identifier: Apache-2.0
// Package ebpfimpl loads the compiled eBPF object and attaches programs.
// Map and ring buffer types must match ebpf/tcp_observability.c.

package ebpfimpl

import (
	"encoding/binary"
	"fmt"
	"os"
	"sync"

	"github.com/cilium/ebpf"
	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/ringbuf"
)

// FlowKey matches struct flow_key in the eBPF C code.
type FlowKey struct {
	Saddr  uint32
	Daddr  uint32
	Sport  uint16
	Dport  uint16
	Netns  uint32
	Family uint8
	_      [3]byte // padding
}

// ConnMetrics matches struct conn_metrics in the eBPF C code.
type ConnMetrics struct {
	BytesSent    uint64
	BytesRecv    uint64
	RetransCount uint64
	RttSumNs     uint64
	RttCount     uint64
	DropCount    uint64
	LastSeenNs   uint64
}

// ConnEvent matches struct conn_event for ring buffer events.
type ConnEvent struct {
	Saddr       uint32
	Daddr       uint32
	Sport       uint16
	Dport       uint16
	Netns       uint32
	Family      uint8
	EventType   uint8
	_           [2]byte
	TimestampNs uint64
	Value       uint64
}

// Loader holds the eBPF collection, links, and map/ringbuf access.
type Loader struct {
	coll   *ebpf.Collection
	links  []link.Link
	connMap *ebpf.Map
	ringBuf *ebpf.Map
	ringReader *ringbuf.Reader
	ready  bool
	mu     sync.RWMutex
}

// NewLoader opens the eBPF object file and loads it into the kernel.
func NewLoader(objPath string) (*Loader, error) {
	spec, err := ebpf.LoadCollectionSpec(objPath)
	if err != nil {
		return nil, fmt.Errorf("load collection spec: %w", err)
	}

	coll, err := ebpf.NewCollection(spec)
	if err != nil {
		return nil, fmt.Errorf("new collection: %w", err)
	}

	connMap, ok := coll.Maps["conn_stats_map"]
	if !ok {
		coll.Close()
		return nil, fmt.Errorf("map conn_stats_map not found")
	}
	ringMap, ok := coll.Maps["events_ringbuf"]
	if !ok {
		coll.Close()
		return nil, fmt.Errorf("map events_ringbuf not found")
	}

	reader, err := ringbuf.NewReader(ringMap)
	if err != nil {
		coll.Close()
		return nil, fmt.Errorf("ringbuf new reader: %w", err)
	}

	l := &Loader{
		coll:       coll,
		connMap:    connMap,
		ringBuf:    ringMap,
		ringReader: reader,
	}
	return l, nil
}

// AttachAll attaches all programs in the collection (kprobes).
func (l *Loader) AttachAll() error {
	progs := []string{
		"tcp_sendmsg_entry",
		"tcp_cleanup_rbuf_entry",
		"tcp_retransmit_skb_entry",
		"tcp_ack_entry",
		"kfree_skb_entry",
		"tcp_connect_entry",
	}
	for _, progName := range progs {
		prog, ok := l.coll.Programs[progName]
		if !ok {
			continue
		}
		link, err := link.Kprobe(progNameToKernel(progName), prog, nil)
		if err != nil {
			l.Close()
			return fmt.Errorf("attach %s: %w", progName, err)
		}
		l.links = append(l.links, link)
	}
	l.mu.Lock()
	l.ready = true
	l.mu.Unlock()
	return nil
}

func progNameToKernel(progName string) string {
	// kprobe name is the part after the first "_" in our naming: tcp_sendmsg_entry -> tcp_sendmsg
	m := map[string]string{
		"tcp_sendmsg_entry":       "tcp_sendmsg",
		"tcp_cleanup_rbuf_entry":  "tcp_cleanup_rbuf",
		"tcp_retransmit_skb_entry": "tcp_retransmit_skb",
		"tcp_ack_entry":           "tcp_ack",
		"kfree_skb_entry":         "kfree_skb",
		"tcp_connect_entry":       "tcp_connect",
	}
	if k, ok := m[progName]; ok {
		return k
	}
	return progName
}

// Ready returns whether eBPF is attached and ready.
func (l *Loader) Ready() bool {
	l.mu.RLock()
	defer l.mu.RUnlock()
	return l.ready
}

// IterateConnStats calls fn for each entry in the connection stats map.
// The map can be modified by the kernel concurrently; iteration is a snapshot.
func (l *Loader) IterateConnStats(fn func(key FlowKey, value ConnMetrics) error) error {
	it := l.connMap.Iterate()
	var key FlowKey
	var val ConnMetrics
	for it.Next(&key, &val) {
		if err := fn(key, val); err != nil {
			return err
		}
	}
	return it.Err()
}

// ReadEvents reads from the ring buffer; non-blocking. Returns number of events read.
func (l *Loader) ReadEvents(fn func(ConnEvent)) (int, error) {
	order := binary.NativeEndian
	const eventSize = 36 // C struct: 4+4+2+2+4+1+1+2+8+8
	var n int
	for i := 0; i < 1024; i++ {
		record, err := l.ringReader.Read()
		if err != nil {
			if err == ringbuf.ErrClosed {
				return n, nil
			}
			return n, err
		}
		if len(record.RawSample) < eventSize {
			continue
		}
		var evt ConnEvent
		evt.Saddr = order.Uint32(record.RawSample[0:4])
		evt.Daddr = order.Uint32(record.RawSample[4:8])
		evt.Sport = order.Uint16(record.RawSample[8:10])
		evt.Dport = order.Uint16(record.RawSample[10:12])
		evt.Netns = order.Uint32(record.RawSample[12:16])
		evt.Family = record.RawSample[16]
		evt.EventType = record.RawSample[17]
		evt.TimestampNs = order.Uint64(record.RawSample[20:28])
		evt.Value = order.Uint64(record.RawSample[28:36])
		fn(evt)
		n++
	}
	return n, nil
}

// Close detaches programs and frees the collection.
func (l *Loader) Close() error {
	l.mu.Lock()
	l.ready = false
	l.mu.Unlock()
	if l.ringReader != nil {
		l.ringReader.Close()
	}
	for _, lnk := range l.links {
		lnk.Close()
	}
	if l.coll != nil {
		l.coll.Close()
	}
	return nil
}

// CopyObjectToDest copies the eBPF object to a path (e.g. for container init).
func CopyObjectToDest(src, dest string) error {
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dest, data, 0644)
}
