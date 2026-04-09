; ModuleID = '15_multifunction'
source_filename = "15_multifunction"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define internal i64 @double(i64 %x) {
pre_entry:
  %x.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  store i64 2, ptr %t0.a.0
  %l.1 = load i64, ptr %x.addr
  %l.2 = load i64, ptr %t0.a.0
  %i.3 = mul nsw i64 %l.1, %l.2
  store i64 %i.3, ptr %t1.a.4
  %l.5 = load i64, ptr %t1.a.4
  ret i64 %l.5
}

define internal i64 @triple(i64 %x) {
pre_entry:
  %x.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  store i64 3, ptr %t0.a.0
  %l.1 = load i64, ptr %x.addr
  %l.2 = load i64, ptr %t0.a.0
  %i.3 = mul nsw i64 %l.1, %l.2
  store i64 %i.3, ptr %t1.a.4
  %l.5 = load i64, ptr %t1.a.4
  ret i64 %l.5
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %t2.a.6 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.6
  %t3.a.8 = alloca i1, align 8
  store i1 0, ptr %t3.a.8
  %t4.a.9 = alloca i64, align 8
  store i64 0, ptr %t4.a.9
  %t5.a.12 = alloca i64, align 8
  store i64 0, ptr %t5.a.12
  %t6.a.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.15
  %t7.a.17 = alloca i1, align 8
  store i1 0, ptr %t7.a.17
  br label %entry
entry:
  store i64 5, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %c.2 = call i64 @double(i64 %l.1)
  store i64 %c.2, ptr %t1.a.3
  %l.4 = load i64, ptr %t1.a.3
  %rt.5 = call {ptr, i64} @__mn_str_from_int(i64 %l.4)
  store {ptr, i64} %rt.5, ptr %t2.a.6
  %l.7 = load {ptr, i64}, ptr %t2.a.6
  call void @__mn_str_println({ptr, i64} %l.7)
  store i1 0, ptr %t3.a.8
  store i64 5, ptr %t4.a.9
  %l.10 = load i64, ptr %t4.a.9
  %c.11 = call i64 @triple(i64 %l.10)
  store i64 %c.11, ptr %t5.a.12
  %l.13 = load i64, ptr %t5.a.12
  %rt.14 = call {ptr, i64} @__mn_str_from_int(i64 %l.13)
  store {ptr, i64} %rt.14, ptr %t6.a.15
  %l.16 = load {ptr, i64}, ptr %t6.a.15
  call void @__mn_str_println({ptr, i64} %l.16)
  store i1 0, ptr %t7.a.17
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.14.0"}
