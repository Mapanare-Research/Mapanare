; ModuleID = '09_string_methods'
source_filename = "09_string_methods"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"hello world", align 8
@.str.1 = private constant [5 x i8] c"world", align 8

declare i1 @__mn_str_contains({ptr, i64}, {ptr, i64})
declare {ptr, i64} @__mn_str_from_bool(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare {ptr, i64} @__mn_str_to_upper({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %s.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %s.a.3
  %t1.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.7
  %t2.a.11 = alloca i1, align 8
  store i1 0, ptr %t2.a.11
  %str_track.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.15
  %t3.a.16 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.16
  %t4.a.18 = alloca i1, align 8
  store i1 0, ptr %t4.a.18
  %str_track.21 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.21
  %t5.a.22 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.22
  %t6.a.24 = alloca i1, align 8
  store i1 0, ptr %t6.a.24
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [11 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 11, 1
  store {ptr, i64} %s.2, ptr %s.a.3
  %sp.4 = getelementptr inbounds [5 x i8], ptr @.str.1, i64 0, i64 0
  %s.5 = insertvalue {ptr, i64} undef, ptr %sp.4, 0
  %s.6 = insertvalue {ptr, i64} %s.5, i64 5, 1
  store {ptr, i64} %s.6, ptr %t1.a.7
  %l.8 = load {ptr, i64}, ptr %s.a.3
  %l.9 = load {ptr, i64}, ptr %t1.a.7
  %rt.10 = call i1 @__mn_str_contains({ptr, i64} %l.8, {ptr, i64} %l.9)
  store i1 %rt.10, ptr %t2.a.11
  %l.12 = load i1, ptr %t2.a.11
  %zx.13 = zext i1 %l.12 to i64
  %rt.14 = call {ptr, i64} @__mn_str_from_bool(i64 %zx.13)
  store {ptr, i64} %rt.14, ptr %str_track.15
  store {ptr, i64} %rt.14, ptr %t3.a.16
  %l.17 = load {ptr, i64}, ptr %t3.a.16
  call void @__mn_str_println({ptr, i64} %l.17)
  store i1 0, ptr %t4.a.18
  %l.19 = load {ptr, i64}, ptr %s.a.3
  %rt.20 = call {ptr, i64} @__mn_str_to_upper({ptr, i64} %l.19)
  store {ptr, i64} %rt.20, ptr %str_track.21
  store {ptr, i64} %rt.20, ptr %t5.a.22
  %l.23 = load {ptr, i64}, ptr %t5.a.22
  call void @__mn_str_println({ptr, i64} %l.23)
  store i1 0, ptr %t6.a.24
  %drop.s.25 = load {ptr, i64}, ptr %str_track.15
  %drop.p.26 = extractvalue {ptr, i64} %drop.s.25, 0
  %drop.null.27 = icmp eq ptr %drop.p.26, null
  br i1 %drop.null.27, label %drop.skip.28, label %drop.check.28
drop.check.28:
  call void @__mn_str_free({ptr, i64} %drop.s.25)
  br label %drop.skip.28
drop.skip.28:
  %drop.s.29 = load {ptr, i64}, ptr %str_track.21
  %drop.p.30 = extractvalue {ptr, i64} %drop.s.29, 0
  %drop.null.31 = icmp eq ptr %drop.p.30, null
  br i1 %drop.null.31, label %drop.skip.32, label %drop.check.32
drop.check.32:
  call void @__mn_str_free({ptr, i64} %drop.s.29)
  br label %drop.skip.32
drop.skip.32:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.33.0"}
