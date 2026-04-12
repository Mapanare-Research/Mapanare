; ModuleID = '20_recursion'
source_filename = "20_recursion"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal i64 @factorial(i64 %n) {
pre_entry:
  %n.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i1, align 8
  store i1 0, ptr %t1.a.4
  %t2.a.6 = alloca i64, align 8
  store i64 0, ptr %t2.a.6
  %t4.a.8 = alloca i64, align 8
  store i64 0, ptr %t4.a.8
  %t5.a.12 = alloca i64, align 8
  store i64 0, ptr %t5.a.12
  %t6.a.15 = alloca i64, align 8
  store i64 0, ptr %t6.a.15
  %t7.a.19 = alloca i64, align 8
  store i64 0, ptr %t7.a.19
  store i64 %n, ptr %n.addr
  br label %entry
entry:
  store i64 1, ptr %t0.a.0
  %l.1 = load i64, ptr %n.addr
  %l.2 = load i64, ptr %t0.a.0
  %i.3 = icmp sle i64 %l.1, %l.2
  store i1 %i.3, ptr %t1.a.4
  %l.5 = load i1, ptr %t1.a.4
  br i1 %l.5, label %if_then0, label %if_else1
if_then0:
  store i64 1, ptr %t2.a.6
  %l.7 = load i64, ptr %t2.a.6
  ret i64 %l.7
if_else1:
  br label %if_merge2
if_merge2:
  store i64 1, ptr %t4.a.8
  %l.9 = load i64, ptr %n.addr
  %l.10 = load i64, ptr %t4.a.8
  %i.11 = sub nsw i64 %l.9, %l.10
  store i64 %i.11, ptr %t5.a.12
  %l.13 = load i64, ptr %t5.a.12
  %c.14 = call i64 @factorial(i64 %l.13)
  store i64 %c.14, ptr %t6.a.15
  %l.16 = load i64, ptr %n.addr
  %l.17 = load i64, ptr %t6.a.15
  %i.18 = mul nsw i64 %l.16, %l.17
  store i64 %i.18, ptr %t7.a.19
  %l.20 = load i64, ptr %t7.a.19
  ret i64 %l.20
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %str_track.6 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.6
  %t2.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.7
  %t3.a.9 = alloca i1, align 8
  store i1 0, ptr %t3.a.9
  %t4.a.10 = alloca i64, align 8
  store i64 0, ptr %t4.a.10
  %t5.a.13 = alloca i64, align 8
  store i64 0, ptr %t5.a.13
  %str_track.16 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.16
  %t6.a.17 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.17
  %t7.a.19 = alloca i1, align 8
  store i1 0, ptr %t7.a.19
  br label %entry
entry:
  store i64 5, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %c.2 = call i64 @factorial(i64 %l.1)
  store i64 %c.2, ptr %t1.a.3
  %l.4 = load i64, ptr %t1.a.3
  %rt.5 = call {ptr, i64} @__mn_str_from_int(i64 %l.4)
  store {ptr, i64} %rt.5, ptr %str_track.6
  store {ptr, i64} %rt.5, ptr %t2.a.7
  %l.8 = load {ptr, i64}, ptr %t2.a.7
  call void @__mn_str_println({ptr, i64} %l.8)
  store i1 0, ptr %t3.a.9
  store i64 10, ptr %t4.a.10
  %l.11 = load i64, ptr %t4.a.10
  %c.12 = call i64 @factorial(i64 %l.11)
  store i64 %c.12, ptr %t5.a.13
  %l.14 = load i64, ptr %t5.a.13
  %rt.15 = call {ptr, i64} @__mn_str_from_int(i64 %l.14)
  store {ptr, i64} %rt.15, ptr %str_track.16
  store {ptr, i64} %rt.15, ptr %t6.a.17
  %l.18 = load {ptr, i64}, ptr %t6.a.17
  call void @__mn_str_println({ptr, i64} %l.18)
  store i1 0, ptr %t7.a.19
  %drop.s.20 = load {ptr, i64}, ptr %str_track.6
  %drop.p.21 = extractvalue {ptr, i64} %drop.s.20, 0
  %drop.null.22 = icmp eq ptr %drop.p.21, null
  br i1 %drop.null.22, label %drop.skip.23, label %drop.check.23
drop.check.23:
  call void @__mn_str_free({ptr, i64} %drop.s.20)
  br label %drop.skip.23
drop.skip.23:
  %drop.s.24 = load {ptr, i64}, ptr %str_track.16
  %drop.p.25 = extractvalue {ptr, i64} %drop.s.24, 0
  %drop.null.26 = icmp eq ptr %drop.p.25, null
  br i1 %drop.null.26, label %drop.skip.27, label %drop.check.27
drop.check.27:
  call void @__mn_str_free({ptr, i64} %drop.s.24)
  br label %drop.skip.27
drop.skip.27:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
