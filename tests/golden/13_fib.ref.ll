; ModuleID = '13_fib'
source_filename = "13_fib"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal i64 @fib(i64 %n) {
pre_entry:
  %n.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i1, align 8
  store i1 0, ptr %t1.a.4
  %t3.a.7 = alloca i64, align 8
  store i64 0, ptr %t3.a.7
  %t4.a.11 = alloca i64, align 8
  store i64 0, ptr %t4.a.11
  %t5.a.14 = alloca i64, align 8
  store i64 0, ptr %t5.a.14
  %t6.a.15 = alloca i64, align 8
  store i64 0, ptr %t6.a.15
  %t7.a.19 = alloca i64, align 8
  store i64 0, ptr %t7.a.19
  %t8.a.22 = alloca i64, align 8
  store i64 0, ptr %t8.a.22
  %t9.a.26 = alloca i64, align 8
  store i64 0, ptr %t9.a.26
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
  %l.6 = load i64, ptr %n.addr
  ret i64 %l.6
if_else1:
  br label %if_merge2
if_merge2:
  store i64 1, ptr %t3.a.7
  %l.8 = load i64, ptr %n.addr
  %l.9 = load i64, ptr %t3.a.7
  %i.10 = sub nsw i64 %l.8, %l.9
  store i64 %i.10, ptr %t4.a.11
  %l.12 = load i64, ptr %t4.a.11
  %c.13 = call i64 @fib(i64 %l.12)
  store i64 %c.13, ptr %t5.a.14
  store i64 2, ptr %t6.a.15
  %l.16 = load i64, ptr %n.addr
  %l.17 = load i64, ptr %t6.a.15
  %i.18 = sub nsw i64 %l.16, %l.17
  store i64 %i.18, ptr %t7.a.19
  %l.20 = load i64, ptr %t7.a.19
  %c.21 = call i64 @fib(i64 %l.20)
  store i64 %c.21, ptr %t8.a.22
  %l.23 = load i64, ptr %t5.a.14
  %l.24 = load i64, ptr %t8.a.22
  %i.25 = add nsw i64 %l.23, %l.24
  store i64 %i.25, ptr %t9.a.26
  %l.27 = load i64, ptr %t9.a.26
  ret i64 %l.27
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
  br label %entry
entry:
  store i64 10, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %c.2 = call i64 @fib(i64 %l.1)
  store i64 %c.2, ptr %t1.a.3
  %l.4 = load i64, ptr %t1.a.3
  %rt.5 = call {ptr, i64} @__mn_str_from_int(i64 %l.4)
  store {ptr, i64} %rt.5, ptr %str_track.6
  store {ptr, i64} %rt.5, ptr %t2.a.7
  %l.8 = load {ptr, i64}, ptr %t2.a.7
  call void @__mn_str_println({ptr, i64} %l.8)
  store i1 0, ptr %t3.a.9
  %drop.s.10 = load {ptr, i64}, ptr %str_track.6
  %drop.p.11 = extractvalue {ptr, i64} %drop.s.10, 0
  %drop.null.12 = icmp eq ptr %drop.p.11, null
  br i1 %drop.null.12, label %drop.skip.13, label %drop.check.13
drop.check.13:
  call void @__mn_str_free({ptr, i64} %drop.s.10)
  br label %drop.skip.13
drop.skip.13:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.33.0"}
