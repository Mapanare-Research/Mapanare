; ModuleID = '35_stdin'
source_filename = "35_stdin"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [7 x i8] c"Hello, ", align 8
@.str.1 = private constant [1 x i8] c"!", align 8

declare {ptr, i64} @__mn_read_line() nounwind willreturn
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %str_track.1 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.1
  %t0.a.2 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t0.a.2
  %t1.a.6 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.6
  %str_track.10 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.10
  %t2.a.11 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.11
  %t3.a.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.15
  %str_track.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.19
  %t4.a.20 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.20
  %t5.a.22 = alloca i1, align 8
  store i1 0, ptr %t5.a.22
  br label %entry
entry:
  %rt.0 = call {ptr, i64} @__mn_read_line()
  store {ptr, i64} %rt.0, ptr %str_track.1
  store {ptr, i64} %rt.0, ptr %t0.a.2
  %sp.3 = getelementptr inbounds [7 x i8], ptr @.str.0, i64 0, i64 0
  %s.4 = insertvalue {ptr, i64} undef, ptr %sp.3, 0
  %s.5 = insertvalue {ptr, i64} %s.4, i64 7, 1
  store {ptr, i64} %s.5, ptr %t1.a.6
  %l.7 = load {ptr, i64}, ptr %t1.a.6
  %l.8 = load {ptr, i64}, ptr %t0.a.2
  %rt.9 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.7, {ptr, i64} %l.8)
  store {ptr, i64} %rt.9, ptr %str_track.10
  store {ptr, i64} %rt.9, ptr %t2.a.11
  %sp.12 = getelementptr inbounds [1 x i8], ptr @.str.1, i64 0, i64 0
  %s.13 = insertvalue {ptr, i64} undef, ptr %sp.12, 0
  %s.14 = insertvalue {ptr, i64} %s.13, i64 1, 1
  store {ptr, i64} %s.14, ptr %t3.a.15
  %l.16 = load {ptr, i64}, ptr %t2.a.11
  %l.17 = load {ptr, i64}, ptr %t3.a.15
  %rt.18 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.16, {ptr, i64} %l.17)
  store {ptr, i64} %rt.18, ptr %str_track.19
  store {ptr, i64} %rt.18, ptr %t4.a.20
  %l.21 = load {ptr, i64}, ptr %t4.a.20
  call void @__mn_str_println({ptr, i64} %l.21)
  store i1 0, ptr %t5.a.22
  %drop.s.23 = load {ptr, i64}, ptr %str_track.1
  %drop.p.24 = extractvalue {ptr, i64} %drop.s.23, 0
  %drop.null.25 = icmp eq ptr %drop.p.24, null
  br i1 %drop.null.25, label %drop.skip.26, label %drop.check.26
drop.check.26:
  call void @__mn_str_free({ptr, i64} %drop.s.23)
  br label %drop.skip.26
drop.skip.26:
  %drop.s.27 = load {ptr, i64}, ptr %str_track.10
  %drop.p.28 = extractvalue {ptr, i64} %drop.s.27, 0
  %drop.null.29 = icmp eq ptr %drop.p.28, null
  br i1 %drop.null.29, label %drop.skip.30, label %drop.check.30
drop.check.30:
  call void @__mn_str_free({ptr, i64} %drop.s.27)
  br label %drop.skip.30
drop.skip.30:
  %drop.s.31 = load {ptr, i64}, ptr %str_track.19
  %drop.p.32 = extractvalue {ptr, i64} %drop.s.31, 0
  %drop.null.33 = icmp eq ptr %drop.p.32, null
  br i1 %drop.null.33, label %drop.skip.34, label %drop.check.34
drop.check.34:
  call void @__mn_str_free({ptr, i64} %drop.s.31)
  br label %drop.skip.34
drop.skip.34:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.32.0"}
