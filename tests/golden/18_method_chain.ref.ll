; ModuleID = '18_method_chain'
source_filename = "18_method_chain"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [13 x i8] c"Hello, World!", align 8
@.str.1 = private constant [5 x i8] c"World", align 8
@.str.2 = private constant [5 x i8] c"World", align 8

declare {ptr, i64} @__mn_str_to_upper({ptr, i64})
declare void @__mn_str_println({ptr, i64})
declare i1 @__mn_str_contains({ptr, i64}, {ptr, i64})
declare {ptr, i64} @__mn_str_from_bool(i64) nounwind willreturn
declare i64 @__mn_str_find({ptr, i64}, {ptr, i64})
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %s.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %s.a.3
  %str_track.6 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.6
  %t1.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.7
  %t2.a.9 = alloca i1, align 8
  store i1 0, ptr %t2.a.9
  %t3.a.13 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.13
  %t4.a.17 = alloca i1, align 8
  store i1 0, ptr %t4.a.17
  %str_track.21 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.21
  %t5.a.22 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.22
  %t6.a.24 = alloca i1, align 8
  store i1 0, ptr %t6.a.24
  %t7.a.28 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t7.a.28
  %t8.a.32 = alloca i64, align 8
  store i64 0, ptr %t8.a.32
  %str_track.35 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.35
  %t9.a.36 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t9.a.36
  %t10.a.38 = alloca i1, align 8
  store i1 0, ptr %t10.a.38
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [13 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 13, 1
  store {ptr, i64} %s.2, ptr %s.a.3
  %l.4 = load {ptr, i64}, ptr %s.a.3
  %rt.5 = call {ptr, i64} @__mn_str_to_upper({ptr, i64} %l.4)
  store {ptr, i64} %rt.5, ptr %str_track.6
  store {ptr, i64} %rt.5, ptr %t1.a.7
  %l.8 = load {ptr, i64}, ptr %t1.a.7
  call void @__mn_str_println({ptr, i64} %l.8)
  store i1 0, ptr %t2.a.9
  %sp.10 = getelementptr inbounds [5 x i8], ptr @.str.1, i64 0, i64 0
  %s.11 = insertvalue {ptr, i64} undef, ptr %sp.10, 0
  %s.12 = insertvalue {ptr, i64} %s.11, i64 5, 1
  store {ptr, i64} %s.12, ptr %t3.a.13
  %l.14 = load {ptr, i64}, ptr %s.a.3
  %l.15 = load {ptr, i64}, ptr %t3.a.13
  %rt.16 = call i1 @__mn_str_contains({ptr, i64} %l.14, {ptr, i64} %l.15)
  store i1 %rt.16, ptr %t4.a.17
  %l.18 = load i1, ptr %t4.a.17
  %zx.19 = zext i1 %l.18 to i64
  %rt.20 = call {ptr, i64} @__mn_str_from_bool(i64 %zx.19)
  store {ptr, i64} %rt.20, ptr %str_track.21
  store {ptr, i64} %rt.20, ptr %t5.a.22
  %l.23 = load {ptr, i64}, ptr %t5.a.22
  call void @__mn_str_println({ptr, i64} %l.23)
  store i1 0, ptr %t6.a.24
  %sp.25 = getelementptr inbounds [5 x i8], ptr @.str.2, i64 0, i64 0
  %s.26 = insertvalue {ptr, i64} undef, ptr %sp.25, 0
  %s.27 = insertvalue {ptr, i64} %s.26, i64 5, 1
  store {ptr, i64} %s.27, ptr %t7.a.28
  %l.29 = load {ptr, i64}, ptr %s.a.3
  %l.30 = load {ptr, i64}, ptr %t7.a.28
  %rt.31 = call i64 @__mn_str_find({ptr, i64} %l.29, {ptr, i64} %l.30)
  store i64 %rt.31, ptr %t8.a.32
  %l.33 = load i64, ptr %t8.a.32
  %rt.34 = call {ptr, i64} @__mn_str_from_int(i64 %l.33)
  store {ptr, i64} %rt.34, ptr %str_track.35
  store {ptr, i64} %rt.34, ptr %t9.a.36
  %l.37 = load {ptr, i64}, ptr %t9.a.36
  call void @__mn_str_println({ptr, i64} %l.37)
  store i1 0, ptr %t10.a.38
  %drop.s.39 = load {ptr, i64}, ptr %str_track.6
  %drop.p.40 = extractvalue {ptr, i64} %drop.s.39, 0
  %drop.null.41 = icmp eq ptr %drop.p.40, null
  br i1 %drop.null.41, label %drop.skip.42, label %drop.check.42
drop.check.42:
  call void @__mn_str_free({ptr, i64} %drop.s.39)
  br label %drop.skip.42
drop.skip.42:
  %drop.s.43 = load {ptr, i64}, ptr %str_track.21
  %drop.p.44 = extractvalue {ptr, i64} %drop.s.43, 0
  %drop.null.45 = icmp eq ptr %drop.p.44, null
  br i1 %drop.null.45, label %drop.skip.46, label %drop.check.46
drop.check.46:
  call void @__mn_str_free({ptr, i64} %drop.s.43)
  br label %drop.skip.46
drop.skip.46:
  %drop.s.47 = load {ptr, i64}, ptr %str_track.35
  %drop.p.48 = extractvalue {ptr, i64} %drop.s.47, 0
  %drop.null.49 = icmp eq ptr %drop.p.48, null
  br i1 %drop.null.49, label %drop.skip.50, label %drop.check.50
drop.check.50:
  call void @__mn_str_free({ptr, i64} %drop.s.47)
  br label %drop.skip.50
drop.skip.50:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.32.0"}
