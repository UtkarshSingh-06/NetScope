# eBPF object build for network observability
# Requires: clang, libbpf (headers), llvm (for -target bpf)
# On Ubuntu: clang llvm libbpf-dev; kernel headers: linux-headers-$(uname -r)

CLANG   ?= clang
LLC     ?= llc
ARCH    := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')
OUT_DIR := .
SRC     := tcp_observability.c
OBJ     := $(OUT_DIR)/tcp_observability.o

# Include paths for libbpf and kernel
KERNEL_HEADERS ?= /lib/modules/$(shell uname -r)/build
BPF_HEADERS    := $(CURDIR)/headers
CFLAGS         := -O2 -target bpf -D__TARGET_ARCH_$(ARCH) \
	-I$(KERNEL_HEADERS)/include \
	-I$(KERNEL_HEADERS)/include/uapi \
	-I$(KERNEL_HEADERS)/include/generated/uapi \
	-I$(BPF_HEADERS) \
	-I/usr/include \
	-Wno-address-of-packed-member

# Prefer libbpf from system or from kernel tree
ifneq ($(wildcard /usr/include/bpf/bpf_helpers.h),)
  CFLAGS += -I/usr/include
endif
ifneq ($(wildcard $(KERNEL_HEADERS)/tools/lib/bpf/bpf_helpers.h),)
  CFLAGS += -I$(KERNEL_HEADERS)/tools/include
  CFLAGS += -I$(KERNEL_HEADERS)/tools/include/uapi
endif

.PHONY: all clean

all: $(OBJ)

$(OBJ): $(SRC)
	$(CLANG) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ)
