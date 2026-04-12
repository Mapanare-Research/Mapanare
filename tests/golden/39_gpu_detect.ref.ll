; ModuleID = '39_gpu_detect'
source_filename = "39_gpu_detect"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [5 x i8] c"GPU: ", align 8
@.str.1 = private constant [6 x i8] c"VRAM: ", align 8
@.str.2 = private constant [16 x i8] c"No GPU available", align 8

declare i64 @__mn_gpu_available() nounwind readonly willreturn
declare {ptr, i64} @__mn_gpu_device_name() nounwind willreturn
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare i64 @__mn_gpu_device_memory() nounwind readonly willreturn
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.2 = alloca i1, align 8
  store i1 0, ptr %t0.a.2
  %t1.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.7
  %str_track.9 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.9
  %t2.a.10 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.10
  %str_track.14 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.14
  %t3.a.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.15
  %t4.a.17 = alloca i1, align 8
  store i1 0, ptr %t4.a.17
  %t5.a.21 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.21
  %t6.a.23 = alloca i64, align 8
  store i64 0, ptr %t6.a.23
  %str_track.26 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.26
  %t7.a.27 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t7.a.27
  %str_track.31 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.31
  %t8.a.32 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t8.a.32
  %t9.a.34 = alloca i1, align 8
  store i1 0, ptr %t9.a.34
  %t10.a.38 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.38
  %t11.a.40 = alloca i1, align 8
  store i1 0, ptr %t11.a.40
  br label %entry
entry:
  %rt.0 = call i64 @__mn_gpu_available()
  %ga.1 = icmp ne i64 %rt.0, 0
  store i1 %ga.1, ptr %t0.a.2
  %l.3 = load i1, ptr %t0.a.2
  br i1 %l.3, label %if_then0, label %if_else1
if_then0:
  %sp.4 = getelementptr inbounds [5 x i8], ptr @.str.0, i64 0, i64 0
  %s.5 = insertvalue {ptr, i64} undef, ptr %sp.4, 0
  %s.6 = insertvalue {ptr, i64} %s.5, i64 5, 1
  store {ptr, i64} %s.6, ptr %t1.a.7
  %rt.8 = call {ptr, i64} @__mn_gpu_device_name()
  store {ptr, i64} %rt.8, ptr %str_track.9
  store {ptr, i64} %rt.8, ptr %t2.a.10
  %l.11 = load {ptr, i64}, ptr %t1.a.7
  %l.12 = load {ptr, i64}, ptr %t2.a.10
  %rt.13 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.11, {ptr, i64} %l.12)
  store {ptr, i64} %rt.13, ptr %str_track.14
  store {ptr, i64} %rt.13, ptr %t3.a.15
  %l.16 = load {ptr, i64}, ptr %t3.a.15
  call void @__mn_str_println({ptr, i64} %l.16)
  store i1 0, ptr %t4.a.17
  %sp.18 = getelementptr inbounds [6 x i8], ptr @.str.1, i64 0, i64 0
  %s.19 = insertvalue {ptr, i64} undef, ptr %sp.18, 0
  %s.20 = insertvalue {ptr, i64} %s.19, i64 6, 1
  store {ptr, i64} %s.20, ptr %t5.a.21
  %rt.22 = call i64 @__mn_gpu_device_memory()
  store i64 %rt.22, ptr %t6.a.23
  %l.24 = load i64, ptr %t6.a.23
  %rt.25 = call {ptr, i64} @__mn_str_from_int(i64 %l.24)
  store {ptr, i64} %rt.25, ptr %str_track.26
  store {ptr, i64} %rt.25, ptr %t7.a.27
  %l.28 = load {ptr, i64}, ptr %t5.a.21
  %l.29 = load {ptr, i64}, ptr %t7.a.27
  %rt.30 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.28, {ptr, i64} %l.29)
  store {ptr, i64} %rt.30, ptr %str_track.31
  store {ptr, i64} %rt.30, ptr %t8.a.32
  %l.33 = load {ptr, i64}, ptr %t8.a.32
  call void @__mn_str_println({ptr, i64} %l.33)
  store i1 0, ptr %t9.a.34
  br label %if_merge2
if_else1:
  %sp.35 = getelementptr inbounds [16 x i8], ptr @.str.2, i64 0, i64 0
  %s.36 = insertvalue {ptr, i64} undef, ptr %sp.35, 0
  %s.37 = insertvalue {ptr, i64} %s.36, i64 16, 1
  store {ptr, i64} %s.37, ptr %t10.a.38
  %l.39 = load {ptr, i64}, ptr %t10.a.38
  call void @__mn_str_println({ptr, i64} %l.39)
  store i1 0, ptr %t11.a.40
  br label %if_merge2
if_merge2:
  %drop.s.41 = load {ptr, i64}, ptr %str_track.9
  %drop.p.42 = extractvalue {ptr, i64} %drop.s.41, 0
  %drop.null.43 = icmp eq ptr %drop.p.42, null
  br i1 %drop.null.43, label %drop.skip.44, label %drop.check.44
drop.check.44:
  call void @__mn_str_free({ptr, i64} %drop.s.41)
  br label %drop.skip.44
drop.skip.44:
  %drop.s.45 = load {ptr, i64}, ptr %str_track.14
  %drop.p.46 = extractvalue {ptr, i64} %drop.s.45, 0
  %drop.null.47 = icmp eq ptr %drop.p.46, null
  br i1 %drop.null.47, label %drop.skip.48, label %drop.check.48
drop.check.48:
  call void @__mn_str_free({ptr, i64} %drop.s.45)
  br label %drop.skip.48
drop.skip.48:
  %drop.s.49 = load {ptr, i64}, ptr %str_track.26
  %drop.p.50 = extractvalue {ptr, i64} %drop.s.49, 0
  %drop.null.51 = icmp eq ptr %drop.p.50, null
  br i1 %drop.null.51, label %drop.skip.52, label %drop.check.52
drop.check.52:
  call void @__mn_str_free({ptr, i64} %drop.s.49)
  br label %drop.skip.52
drop.skip.52:
  %drop.s.53 = load {ptr, i64}, ptr %str_track.31
  %drop.p.54 = extractvalue {ptr, i64} %drop.s.53, 0
  %drop.null.55 = icmp eq ptr %drop.p.54, null
  br i1 %drop.null.55, label %drop.skip.56, label %drop.check.56
drop.check.56:
  call void @__mn_str_free({ptr, i64} %drop.s.53)
  br label %drop.skip.56
drop.skip.56:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.33.0"}
