; ModuleID = 'fib_recursive'
source_filename = "fib_recursive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [10 x i8] c"fib(35) = ", align 8

declare {ptr, i64} @__mn_str_from_int(i64)
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64})
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64})
declare void @free(ptr)
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
  %i.10 = sub i64 %l.8, %l.9
  store i64 %i.10, ptr %t4.a.11
  %l.12 = load i64, ptr %t4.a.11
  %c.13 = call i64 @fib(i64 %l.12)
  store i64 %c.13, ptr %t5.a.14
  store i64 2, ptr %t6.a.15
  %l.16 = load i64, ptr %n.addr
  %l.17 = load i64, ptr %t6.a.15
  %i.18 = sub i64 %l.16, %l.17
  store i64 %i.18, ptr %t7.a.19
  %l.20 = load i64, ptr %t7.a.19
  %c.21 = call i64 @fib(i64 %l.20)
  store i64 %c.21, ptr %t8.a.22
  %l.23 = load i64, ptr %t5.a.14
  %l.24 = load i64, ptr %t8.a.22
  %i.25 = add i64 %l.23, %l.24
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
  %t2.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.7
  %str_track.10 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.10
  %t3.a.11 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.11
  %str_track.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.15
  %t4.a.16 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.16
  %t5.a.18 = alloca i1, align 8
  store i1 0, ptr %t5.a.18
  br label %entry
entry:
  store i64 35, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %c.2 = call i64 @fib(i64 %l.1)
  store i64 %c.2, ptr %t1.a.3
  %sp.4 = getelementptr inbounds [10 x i8], ptr @.str.0, i64 0, i64 0
  %s.5 = insertvalue {ptr, i64} undef, ptr %sp.4, 0
  %s.6 = insertvalue {ptr, i64} %s.5, i64 10, 1
  store {ptr, i64} %s.6, ptr %t2.a.7
  %l.8 = load i64, ptr %t1.a.3
  %rt.9 = call {ptr, i64} @__mn_str_from_int(i64 %l.8)
  store {ptr, i64} %rt.9, ptr %str_track.10
  store {ptr, i64} %rt.9, ptr %t3.a.11
  %l.12 = load {ptr, i64}, ptr %t2.a.7
  %l.13 = load {ptr, i64}, ptr %t3.a.11
  %rt.14 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.12, {ptr, i64} %l.13)
  store {ptr, i64} %rt.14, ptr %str_track.15
  store {ptr, i64} %rt.14, ptr %t4.a.16
  %l.17 = load {ptr, i64}, ptr %t4.a.16
  call void @__mn_str_println({ptr, i64} %l.17)
  store i1 0, ptr %t5.a.18
  %drop.s.19 = load {ptr, i64}, ptr %str_track.10
  %drop.p.20 = extractvalue {ptr, i64} %drop.s.19, 0
  %drop.null.21 = icmp eq ptr %drop.p.20, null
  br i1 %drop.null.21, label %drop.skip.22, label %drop.check.22
drop.check.22:
  call void @__mn_str_free({ptr, i64} %drop.s.19)
  br label %drop.skip.22
drop.skip.22:
  %drop.s.23 = load {ptr, i64}, ptr %str_track.15
  %drop.p.24 = extractvalue {ptr, i64} %drop.s.23, 0
  %drop.null.25 = icmp eq ptr %drop.p.24, null
  br i1 %drop.null.25, label %drop.skip.26, label %drop.check.26
drop.check.26:
  call void @__mn_str_free({ptr, i64} %drop.s.23)
  br label %drop.skip.26
drop.skip.26:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.109.0"}
!1 = !{!"Mapanare TBAA"}
!2 = !{!"int", !1}
!3 = !{!"float", !1}
!4 = !{!"ptr", !1}
!5 = !{!"bool", !1}
!6 = !{!2, !2, i64 0}
!7 = !{!3, !3, i64 0}
!8 = !{!4, !4, i64 0}
!9 = !{!5, !5, i64 0}
