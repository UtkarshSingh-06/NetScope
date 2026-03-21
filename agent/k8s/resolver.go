// SPDX-License-Identifier: Apache-2.0
// Package k8s provides IP-to-Pod/Namespace/Service resolution using the Kubernetes API.
// Used to enrich Prometheus metrics with east-west traffic context (pod, namespace, service).

package k8s

import (
	"context"
	"net"
	"sync"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

// IPResolver resolves an IP (and optional port) to pod name, namespace, and service name.
type IPResolver interface {
	Resolve(ip uint32, port uint16, isSource bool) (pod, namespace, service string)
	Close()
}

type resolver struct {
	clientset *kubernetes.Clientset
	nodeName  string
	cache     *ipCache
	stop      context.CancelFunc
}

type ipCache struct {
	mu      sync.RWMutex
	entries map[string]cacheEntry
	ttl     time.Duration
}

type cacheEntry struct {
	pod, namespace, service string
	expires                 time.Time
}

// NewIPResolver builds an in-cluster or kubeconfig-based client and starts
// a background reflector that lists pods on this node and builds IP -> (pod, ns, svc).
func NewIPResolver(ctx context.Context, nodeName, kubeconfigPath string) (IPResolver, error) {
	var config *rest.Config
	var err error
	if kubeconfigPath != "" {
		config, err = clientcmd.BuildConfigFromFlags("", kubeconfigPath)
	} else {
		config, err = rest.InClusterConfig()
	}
	if err != nil {
		return nil, err
	}
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, err
	}
	cache := &ipCache{
		entries: make(map[string]cacheEntry),
		ttl:     30 * time.Second,
	}
	r := &resolver{
		clientset: clientset,
		nodeName:  nodeName,
		cache:     cache,
	}
	ctx, cancel := context.WithCancel(ctx)
	r.stop = cancel
	go r.refreshLoop(ctx)
	return r, nil
}

func (r *resolver) refreshLoop(ctx context.Context) {
	ticker := time.NewTicker(15 * time.Second)
	defer ticker.Stop()
	r.refresh(ctx)
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			r.refresh(ctx)
		}
	}
}

func (r *resolver) refresh(ctx context.Context) {
	pods, err := r.clientset.CoreV1().Pods("").List(ctx, metav1.ListOptions{
		FieldSelector: "spec.nodeName=" + r.nodeName,
	})
	if err != nil {
		return
	}
	svcList, _ := r.clientset.CoreV1().Services("").List(ctx, metav1.ListOptions{})
	svcByNS := make(map[string][]corev1.Service)
	for i := range svcList.Items {
		s := &svcList.Items[i]
		svcByNS[s.Namespace] = append(svcByNS[s.Namespace], *s)
	}

	r.cache.mu.Lock()
	defer r.cache.mu.Unlock()
	expires := time.Now().Add(r.cache.ttl)
	for i := range pods.Items {
		pod := &pods.Items[i]
		for _, status := range pod.Status.PodIPs {
			ip := status.IP
			if ip == "" {
				continue
			}
			svc := findServiceForPod(svcByNS[pod.Namespace], pod)
			r.cache.entries[ip] = cacheEntry{
				pod:       pod.Name,
				namespace: pod.Namespace,
				service:   svc,
				expires:   expires,
			}
		}
		if pod.Status.PodIP != "" && pod.Status.PodIP != pod.Status.HostIP {
			if _, ok := r.cache.entries[pod.Status.PodIP]; !ok {
				svc := findServiceForPod(svcByNS[pod.Namespace], pod)
				r.cache.entries[pod.Status.PodIP] = cacheEntry{
					pod:       pod.Name,
					namespace: pod.Namespace,
					service:   svc,
					expires:   expires,
				}
			}
		}
	}
}

func findServiceForPod(services []corev1.Service, pod *corev1.Pod) string {
	for _, svc := range services {
		for key, val := range svc.Spec.Selector {
			if v, ok := pod.Labels[key]; !ok || v != val {
				goto next
			}
		}
		return svc.Name
	next:
	}
	return ""
}

func (r *resolver) Resolve(ip uint32, port uint16, isSource bool) (pod, namespace, service string) {
	ipStr := uint32ToIP(ip).String()
	r.cache.mu.RLock()
	e, ok := r.cache.entries[ipStr]
	r.cache.mu.RUnlock()
	if !ok || time.Now().After(e.expires) {
		return "", "", ""
	}
	return e.pod, e.namespace, e.service
}

func (r *resolver) Close() {
	if r.stop != nil {
		r.stop()
	}
}

func uint32ToIP(u uint32) net.IP {
	return net.IPv4(byte(u), byte(u>>8), byte(u>>16), byte(u>>24))
}
