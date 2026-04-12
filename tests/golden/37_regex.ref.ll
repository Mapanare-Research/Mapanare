; ModuleID = '37_regex'
source_filename = "37_regex"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [6 x i8] c"[0-9]+", align 8
@.str.1 = private constant [9 x i8] c"abc123def", align 8
@.str.2 = private constant [6 x i8] c"[0-9]+", align 8
@.str.3 = private constant [6 x i8] c"abcdef", align 8
@.str.4 = private constant [6 x i8] c"[0-9]+", align 8
@.str.5 = private constant [12 x i8] c"abc123def456", align 8
@.str.6 = private constant [3 x i8] c"NUM", align 8

declare i64 @__mn_regex_compile_str({ptr, i64}) nounwind willreturn
declare i64 @__mn_regex_exec_str(i64, {ptr, i64}, i64) nounwind willreturn
declare i64 @__mn_regex_free(i64) nounwind willreturn
declare {ptr, i64} @__mn_str_from_bool(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare {ptr, i64} @__mn_regex_replace_str(i64, {ptr, i64}, {ptr, i64}, i64) nounwind willreturn
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t0.a.3
  %t1.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.7
  %t2.a.14 = alloca i1, align 8
  store i1 0, ptr %t2.a.14
  %str_track.18 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.18
  %t3.a.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.19
  %t4.a.21 = alloca i1, align 8
  store i1 0, ptr %t4.a.21
  %t5.a.25 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.25
  %t6.a.29 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.29
  %t7.a.36 = alloca i1, align 8
  store i1 0, ptr %t7.a.36
  %str_track.40 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.40
  %t8.a.41 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t8.a.41
  %t9.a.43 = alloca i1, align 8
  store i1 0, ptr %t9.a.43
  %t10.a.47 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.47
  %t11.a.51 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t11.a.51
  %t12.a.55 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t12.a.55
  %str_track.62 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.62
  %t13.a.63 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t13.a.63
  %t14.a.65 = alloca i1, align 8
  store i1 0, ptr %t14.a.65
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [6 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 6, 1
  store {ptr, i64} %s.2, ptr %t0.a.3
  %sp.4 = getelementptr inbounds [9 x i8], ptr @.str.1, i64 0, i64 0
  %s.5 = insertvalue {ptr, i64} undef, ptr %sp.4, 0
  %s.6 = insertvalue {ptr, i64} %s.5, i64 9, 1
  store {ptr, i64} %s.6, ptr %t1.a.7
  %l.8 = load {ptr, i64}, ptr %t0.a.3
  %l.9 = load {ptr, i64}, ptr %t1.a.7
  %rt.10 = call i64 @__mn_regex_compile_str({ptr, i64} %l.8)
  %rt.11 = call i64 @__mn_regex_exec_str(i64 %rt.10, {ptr, i64} %l.9, i64 0)
  %rt.12 = call i64 @__mn_regex_free(i64 %rt.10)
  %rm.13 = icmp sgt i64 %rt.11, 0
  store i1 %rm.13, ptr %t2.a.14
  %l.15 = load i1, ptr %t2.a.14
  %zx.16 = zext i1 %l.15 to i64
  %rt.17 = call {ptr, i64} @__mn_str_from_bool(i64 %zx.16)
  store {ptr, i64} %rt.17, ptr %str_track.18
  store {ptr, i64} %rt.17, ptr %t3.a.19
  %l.20 = load {ptr, i64}, ptr %t3.a.19
  call void @__mn_str_println({ptr, i64} %l.20)
  store i1 0, ptr %t4.a.21
  %sp.22 = getelementptr inbounds [6 x i8], ptr @.str.2, i64 0, i64 0
  %s.23 = insertvalue {ptr, i64} undef, ptr %sp.22, 0
  %s.24 = insertvalue {ptr, i64} %s.23, i64 6, 1
  store {ptr, i64} %s.24, ptr %t5.a.25
  %sp.26 = getelementptr inbounds [6 x i8], ptr @.str.3, i64 0, i64 0
  %s.27 = insertvalue {ptr, i64} undef, ptr %sp.26, 0
  %s.28 = insertvalue {ptr, i64} %s.27, i64 6, 1
  store {ptr, i64} %s.28, ptr %t6.a.29
  %l.30 = load {ptr, i64}, ptr %t5.a.25
  %l.31 = load {ptr, i64}, ptr %t6.a.29
  %rt.32 = call i64 @__mn_regex_compile_str({ptr, i64} %l.30)
  %rt.33 = call i64 @__mn_regex_exec_str(i64 %rt.32, {ptr, i64} %l.31, i64 0)
  %rt.34 = call i64 @__mn_regex_free(i64 %rt.32)
  %rm.35 = icmp sgt i64 %rt.33, 0
  store i1 %rm.35, ptr %t7.a.36
  %l.37 = load i1, ptr %t7.a.36
  %zx.38 = zext i1 %l.37 to i64
  %rt.39 = call {ptr, i64} @__mn_str_from_bool(i64 %zx.38)
  store {ptr, i64} %rt.39, ptr %str_track.40
  store {ptr, i64} %rt.39, ptr %t8.a.41
  %l.42 = load {ptr, i64}, ptr %t8.a.41
  call void @__mn_str_println({ptr, i64} %l.42)
  store i1 0, ptr %t9.a.43
  %sp.44 = getelementptr inbounds [6 x i8], ptr @.str.4, i64 0, i64 0
  %s.45 = insertvalue {ptr, i64} undef, ptr %sp.44, 0
  %s.46 = insertvalue {ptr, i64} %s.45, i64 6, 1
  store {ptr, i64} %s.46, ptr %t10.a.47
  %sp.48 = getelementptr inbounds [12 x i8], ptr @.str.5, i64 0, i64 0
  %s.49 = insertvalue {ptr, i64} undef, ptr %sp.48, 0
  %s.50 = insertvalue {ptr, i64} %s.49, i64 12, 1
  store {ptr, i64} %s.50, ptr %t11.a.51
  %sp.52 = getelementptr inbounds [3 x i8], ptr @.str.6, i64 0, i64 0
  %s.53 = insertvalue {ptr, i64} undef, ptr %sp.52, 0
  %s.54 = insertvalue {ptr, i64} %s.53, i64 3, 1
  store {ptr, i64} %s.54, ptr %t12.a.55
  %l.56 = load {ptr, i64}, ptr %t10.a.47
  %l.57 = load {ptr, i64}, ptr %t11.a.51
  %l.58 = load {ptr, i64}, ptr %t12.a.55
  %rt.59 = call i64 @__mn_regex_compile_str({ptr, i64} %l.56)
  %rt.60 = call {ptr, i64} @__mn_regex_replace_str(i64 %rt.59, {ptr, i64} %l.57, {ptr, i64} %l.58, i64 1)
  %rt.61 = call i64 @__mn_regex_free(i64 %rt.59)
  store {ptr, i64} %rt.60, ptr %str_track.62
  store {ptr, i64} %rt.60, ptr %t13.a.63
  %l.64 = load {ptr, i64}, ptr %t13.a.63
  call void @__mn_str_println({ptr, i64} %l.64)
  store i1 0, ptr %t14.a.65
  %drop.s.66 = load {ptr, i64}, ptr %str_track.18
  %drop.p.67 = extractvalue {ptr, i64} %drop.s.66, 0
  %drop.null.68 = icmp eq ptr %drop.p.67, null
  br i1 %drop.null.68, label %drop.skip.69, label %drop.check.69
drop.check.69:
  call void @__mn_str_free({ptr, i64} %drop.s.66)
  br label %drop.skip.69
drop.skip.69:
  %drop.s.70 = load {ptr, i64}, ptr %str_track.40
  %drop.p.71 = extractvalue {ptr, i64} %drop.s.70, 0
  %drop.null.72 = icmp eq ptr %drop.p.71, null
  br i1 %drop.null.72, label %drop.skip.73, label %drop.check.73
drop.check.73:
  call void @__mn_str_free({ptr, i64} %drop.s.70)
  br label %drop.skip.73
drop.skip.73:
  %drop.s.74 = load {ptr, i64}, ptr %str_track.62
  %drop.p.75 = extractvalue {ptr, i64} %drop.s.74, 0
  %drop.null.76 = icmp eq ptr %drop.p.75, null
  br i1 %drop.null.76, label %drop.skip.77, label %drop.check.77
drop.check.77:
  call void @__mn_str_free({ptr, i64} %drop.s.74)
  br label %drop.skip.77
drop.skip.77:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
