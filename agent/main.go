// SPDX-License-Identifier: Apache-2.0
//
// Cloud-Native Network Observability - Userspace Agent
//
// Loads eBPF programs, collects metrics from kernel maps/ring buffer,
// enriches with Kubernetes metadata (pod, namespace, service), and
// exposes Prometheus metrics at /metrics. Designed to run as a
// DaemonSet (one pod per node).

package main

import (
	"context"
	"flag"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"netscope/agent/ebpfimpl"
	"netscope/agent/k8s"
	"netscope/agent/metrics"
)

var (
	metricsAddr   = flag.String("metrics-addr", ":9090", "Listen address for /metrics")
	ebpfObjPath   = flag.String("ebpf-object", "/etc/network-observability/tcp_observability.o", "Path to compiled eBPF object")
	nodeName      = flag.String("node-name", "", "Kubernetes node name (default: hostname or NODE_NAME env)")
	pollInterval  = flag.Duration("poll-interval", 15*time.Second, "Interval for scraping eBPF maps")
	enableK8s     = flag.Bool("enable-kubernetes", true, "Enrich metrics with pod/namespace/service labels")
	kubeconfig    = flag.String("kubeconfig", "", "Path to kubeconfig (empty for in-cluster)")
)

func main() {
	flag.Parse()

	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	slog.SetDefault(logger)

	if *nodeName == "" {
		*nodeName = os.Getenv("NODE_NAME")
		if *nodeName == "" {
			hostname, _ := os.Hostname()
			*nodeName = hostname
		}
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Load and attach eBPF
	loader, err := ebpfimpl.NewLoader(*ebpfObjPath)
	if err != nil {
		slog.Error("failed to load eBPF", "path", *ebpfObjPath, "error", err)
		os.Exit(1)
	}
	defer loader.Close()

	if err := loader.AttachAll(); err != nil {
		slog.Error("failed to attach eBPF programs", "error", err)
		os.Exit(1)
	}
	slog.Info("eBPF programs loaded and attached")

	// Kubernetes pod/service resolver (optional)
	var resolver k8s.IPResolver
	if *enableK8s {
		resolver, err = k8s.NewIPResolver(ctx, *nodeName, *kubeconfig)
		if err != nil {
			slog.Warn("kubernetes resolver disabled", "error", err)
		} else {
			defer resolver.Close()
			slog.Info("kubernetes enrichment enabled", "node", *nodeName)
		}
	}

	// Prometheus collector that reads from eBPF and optionally enriches with K8s
	collector := metrics.NewCollector(loader, resolver, *nodeName)
	if err := prometheus.DefaultRegisterer.Register(collector); err != nil {
		slog.Error("failed to register collector", "error", err)
		os.Exit(1)
	}
	// Initial scrape so /metrics has data on first Prometheus poll
	_ = collector.Scrape(ctx)

	// Background: poll eBPF maps and consume ring buffer
	go func() {
		ticker := time.NewTicker(*pollInterval)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				if err := collector.Scrape(ctx); err != nil {
					slog.Warn("scrape failed", "error", err)
				}
			}
		}
	}()

	http.Handle("/metrics", promhttp.Handler())
	http.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})
	http.HandleFunc("/ready", func(w http.ResponseWriter, _ *http.Request) {
		if loader.Ready() {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte("ready"))
		} else {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("eBPF not ready"))
		}
	})

	srv := &http.Server{Addr: *metricsAddr, ReadHeaderTimeout: 5 * time.Second}
	go func() {
		slog.Info("metrics server listening", "addr", *metricsAddr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			slog.Error("metrics server error", "error", err)
		}
	}()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	slog.Info("shutting down")
	if err := srv.Shutdown(ctx); err != nil {
		slog.Error("server shutdown", "error", err)
	}
	cancel()
}
