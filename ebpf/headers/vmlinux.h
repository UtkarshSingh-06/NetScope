/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/*
 * Minimal types and macros for eBPF CO-RE compatibility.
 * In production, generate from BTF: bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
 * This header provides the minimal subset needed for TCP observability.
 */
#ifndef __VMLINUX_H__
#define __VMLINUX_H__

typedef signed char __s8;
typedef unsigned char __u8;
typedef short int __s16;
typedef short unsigned int __u16;
typedef int __s32;
typedef unsigned int __u32;
typedef long int __s64;
typedef long unsigned int __u64;

typedef __u8 u8;
typedef __u16 u16;
typedef __u32 u32;
typedef __u64 u64;

/* Required for BPF ring buffer and map definitions */
struct pt_regs {
	unsigned long r15;
	unsigned long r14;
	unsigned long r13;
	unsigned long r12;
	unsigned long rbp;
	unsigned long rbx;
	unsigned long r11;
	unsigned long r10;
	unsigned long r9;
	unsigned long r8;
	unsigned long rax;
	unsigned long rcx;
	unsigned long rdx;
	unsigned long rsi;
	unsigned long rdi;
	unsigned long orig_rax;
	unsigned long rip;
	unsigned long cs;
	unsigned long eflags;
	unsigned long rsp;
	unsigned long ss;
};

#endif /* __VMLINUX_H__ */
