# NetScope - Multi-stage build: compile eBPF (on Linux), build Go agent, minimal runtime image.
# Build from repo root: docker build -t netscope/agent:latest -f Dockerfile .

# Stage 1: eBPF build (requires clang, kernel headers; typically run on Linux)
FROM debian:bookworm-slim AS ebpf-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    clang \
    llvm \
    libbpf-dev \
    linux-headers-generic \
    make \
    && rm -rf /var/lib/apt/lists/*
# Use host kernel headers if building on target kernel; or copy from builder.
COPY ebpf/ /build/ebpf/
WORKDIR /build/ebpf
# If KERNEL_HEADERS not set, use generic; for production use --build-arg with node kernel.
ARG KERNEL_HEADERS=
RUN make

# Stage 2: Go agent build
FROM golang:1.21-alpine AS go-builder
RUN apk add --no-cache git ca-certificates
WORKDIR /app
COPY agent/go.mod ./
RUN go mod tidy && go mod download
COPY agent/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /agent .

# Stage 3: Runtime (minimal; eBPF object copied from stage 1 or added at deploy)
FROM alpine:3.19
RUN apk add --no-cache ca-certificates
COPY --from=go-builder /agent /usr/local/bin/network-observability-agent
# eBPF object: built in ebpf-builder (Linux). For non-Linux build hosts, copy pre-built ebpf/tcp_observability.o into context.
RUN mkdir -p /etc/network-observability
COPY --from=ebpf-builder /build/ebpf/tcp_observability.o /etc/network-observability/tcp_observability.o
ENTRYPOINT ["/usr/local/bin/network-observability-agent"]
CMD ["--metrics-addr=:9090", "--ebpf-object=/etc/network-observability/tcp_observability.o"]
