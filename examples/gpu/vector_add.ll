; ModuleID = 'vector_add'
source_filename = "vector_add"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"Running on ", align 8
@.str.1 = private constant [16 x i8] c"No GPU available", align 8
@.str.2 = private constant [2 x i8] c": ", align 8

declare i64 @__mn_gpu_available() nounwind
declare {ptr, i64} @__mn_gpu_device_name() nounwind
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind
declare void @__mn_str_println({ptr, i64})
declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind
declare ptr @__mn_range(i64, i64)
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_list_free(ptr) nounwind willreturn
declare i1 @__iter_has_next(ptr)
declare i64 @__iter_next(ptr)
declare void @__mn_list_push(ptr, ptr) nounwind
declare i1 @__mn_range_free(ptr) nounwind willreturn
declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_add(ptr, ptr) nounwind
declare {ptr, i64} @__mn_str_from_int(i64) nounwind
declare ptr @__mn_list_get(ptr, i64) nounwind readonly
declare {ptr, i64} @__mn_str_from_float(double) nounwind

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
  %t5.a.19 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t5.a.19
  %a.a.21 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %a.a.21
  %t6.a.23 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t6.a.23
  %b.a.25 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %b.a.25
  %t7.a.26 = alloca i64, align 8
  store i64 0, ptr %t7.a.26
  %t8.a.27 = alloca i64, align 8
  store i64 0, ptr %t8.a.27
  %t9.a.31 = alloca ptr, align 8
  store ptr null, ptr %t9.a.31
  %t33.a.35 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t33.a.35
  %t34.a.37 = alloca i1, align 8
  store i1 0, ptr %t34.a.37
  %has_next11.a.56 = alloca i1, align 8
  store i1 0, ptr %has_next11.a.56
  %next12.a.60 = alloca i64, align 8
  store i64 0, ptr %next12.a.60
  %t13.a.63 = alloca double, align 8
  store double 0.000000e+00, ptr %t13.a.63
  %ea.65 = alloca double, align 8
  %t14.a.69 = alloca double, align 8
  store double 0.000000e+00, ptr %t14.a.69
  %t15.a.70 = alloca double, align 8
  store double 0.000000e+00, ptr %t15.a.70
  %t16.a.74 = alloca double, align 8
  store double 0.000000e+00, ptr %t16.a.74
  %ea.76 = alloca double, align 8
  %range_free17.a.80 = alloca i1, align 8
  store i1 0, ptr %range_free17.a.80
  %gta.83 = alloca {ptr, i64, i64, i64, i64}, align 8
  %gtb.84 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t18.a.86 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t18.a.86
  %t19.a.87 = alloca i64, align 8
  store i64 0, ptr %t19.a.87
  %t20.a.88 = alloca i64, align 8
  store i64 0, ptr %t20.a.88
  %t21.a.92 = alloca ptr, align 8
  store ptr null, ptr %t21.a.92
  %has_next23.a.95 = alloca i1, align 8
  store i1 0, ptr %has_next23.a.95
  %next24.a.99 = alloca i64, align 8
  store i64 0, ptr %next24.a.99
  %str_track.102 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.102
  %t25.a.103 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t25.a.103
  %t26.a.107 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t26.a.107
  %str_track.111 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.111
  %t27.a.112 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t27.a.112
  %lp.115 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t28.a.118 = alloca double, align 8
  store double 0.000000e+00, ptr %t28.a.118
  %str_track.121 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.121
  %t29.a.122 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t29.a.122
  %str_track.126 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.126
  %t30.a.127 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t30.a.127
  %t31.a.129 = alloca i1, align 8
  store i1 0, ptr %t31.a.129
  %range_free32.a.132 = alloca i1, align 8
  store i1 0, ptr %range_free32.a.132
  br label %entry
entry:
  %rt.0 = call i64 @__mn_gpu_available()
  %ga.1 = icmp ne i64 %rt.0, 0
  store i1 %ga.1, ptr %t0.a.2
  %l.3 = load i1, ptr %t0.a.2
  br i1 %l.3, label %if_then0, label %if_else1
if_then0:
  %sp.4 = getelementptr inbounds [11 x i8], ptr @.str.0, i64 0, i64 0
  %s.5 = insertvalue {ptr, i64} undef, ptr %sp.4, 0
  %s.6 = insertvalue {ptr, i64} %s.5, i64 11, 1
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
  %ln.18 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.18, ptr %t5.a.19
  %l.20 = load {ptr, i64, i64, i64, i64}, ptr %t5.a.19
  store {ptr, i64, i64, i64, i64} %l.20, ptr %a.a.21
  %ln.22 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.22, ptr %t6.a.23
  %l.24 = load {ptr, i64, i64, i64, i64}, ptr %t6.a.23
  store {ptr, i64, i64, i64, i64} %l.24, ptr %b.a.25
  store i64 0, ptr %t7.a.26
  store i64 1000, ptr %t8.a.27
  %l.28 = load i64, ptr %t7.a.26
  %l.29 = load i64, ptr %t8.a.27
  %c.30 = call ptr @__mn_range(i64 %l.28, i64 %l.29)
  store ptr %c.30, ptr %t9.a.31
  br label %for_header3
if_else1:
  %sp.32 = getelementptr inbounds [16 x i8], ptr @.str.1, i64 0, i64 0
  %s.33 = insertvalue {ptr, i64} undef, ptr %sp.32, 0
  %s.34 = insertvalue {ptr, i64} %s.33, i64 16, 1
  store {ptr, i64} %s.34, ptr %t33.a.35
  %l.36 = load {ptr, i64}, ptr %t33.a.35
  call void @__mn_str_println({ptr, i64} %l.36)
  store i1 0, ptr %t34.a.37
  br label %if_merge2
if_merge2:
  %drop.s.38 = load {ptr, i64}, ptr %str_track.9
  %drop.p.39 = extractvalue {ptr, i64} %drop.s.38, 0
  %drop.null.40 = icmp eq ptr %drop.p.39, null
  br i1 %drop.null.40, label %drop.skip.41, label %drop.check.41
for_header3:
  %l.54 = load ptr, ptr %t9.a.31
  %c.55 = call i1 @__iter_has_next(ptr %l.54)
  store i1 %c.55, ptr %has_next11.a.56
  %l.57 = load i1, ptr %has_next11.a.56
  br i1 %l.57, label %for_body4, label %for_exit5
for_body4:
  %l.58 = load ptr, ptr %t9.a.31
  %c.59 = call i64 @__iter_next(ptr %l.58)
  store i64 %c.59, ptr %next12.a.60
  %l.61 = load i64, ptr %next12.a.60
  %cf.62 = sitofp i64 %l.61 to double
  store double %cf.62, ptr %t13.a.63
  %l.64 = load double, ptr %t13.a.63
  store double %l.64, ptr %ea.65
  call void @__mn_list_push(ptr %t5.a.19, ptr %ea.65)
  %ul.66 = load {ptr, i64, i64, i64, i64}, ptr %t5.a.19
  store {ptr, i64, i64, i64, i64} %ul.66, ptr %a.a.21
  %l.67 = load i64, ptr %next12.a.60
  %cf.68 = sitofp i64 %l.67 to double
  store double %cf.68, ptr %t14.a.69
  store double 0x4000000000000000, ptr %t15.a.70
  %l.71 = load double, ptr %t14.a.69
  %l.72 = load double, ptr %t15.a.70
  %f.73 = fmul double %l.71, %l.72
  store double %f.73, ptr %t16.a.74
  %l.75 = load double, ptr %t16.a.74
  store double %l.75, ptr %ea.76
  call void @__mn_list_push(ptr %t6.a.23, ptr %ea.76)
  %ul.77 = load {ptr, i64, i64, i64, i64}, ptr %t6.a.23
  store {ptr, i64, i64, i64, i64} %ul.77, ptr %b.a.25
  br label %for_header3
for_exit5:
  %l.78 = load ptr, ptr %t9.a.31
  %c.79 = call i1 @__mn_range_free(ptr %l.78)
  store i1 %c.79, ptr %range_free17.a.80
  %l.81 = load {ptr, i64, i64, i64, i64}, ptr %a.a.21
  %l.82 = load {ptr, i64, i64, i64, i64}, ptr %b.a.25
  store {ptr, i64, i64, i64, i64} %l.81, ptr %gta.83
  store {ptr, i64, i64, i64, i64} %l.82, ptr %gtb.84
  %rt.85 = call {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_add(ptr %gta.83, ptr %gtb.84)
  store {ptr, i64, i64, i64, i64} %rt.85, ptr %t18.a.86
  store i64 0, ptr %t19.a.87
  store i64 5, ptr %t20.a.88
  %l.89 = load i64, ptr %t19.a.87
  %l.90 = load i64, ptr %t20.a.88
  %c.91 = call ptr @__mn_range(i64 %l.89, i64 %l.90)
  store ptr %c.91, ptr %t21.a.92
  br label %for_header6
for_header6:
  %l.93 = load ptr, ptr %t21.a.92
  %c.94 = call i1 @__iter_has_next(ptr %l.93)
  store i1 %c.94, ptr %has_next23.a.95
  %l.96 = load i1, ptr %has_next23.a.95
  br i1 %l.96, label %for_body7, label %for_exit8
for_body7:
  %l.97 = load ptr, ptr %t21.a.92
  %c.98 = call i64 @__iter_next(ptr %l.97)
  store i64 %c.98, ptr %next24.a.99
  %l.100 = load i64, ptr %next24.a.99
  %rt.101 = call {ptr, i64} @__mn_str_from_int(i64 %l.100)
  store {ptr, i64} %rt.101, ptr %str_track.102
  store {ptr, i64} %rt.101, ptr %t25.a.103
  %sp.104 = getelementptr inbounds [2 x i8], ptr @.str.2, i64 0, i64 0
  %s.105 = insertvalue {ptr, i64} undef, ptr %sp.104, 0
  %s.106 = insertvalue {ptr, i64} %s.105, i64 2, 1
  store {ptr, i64} %s.106, ptr %t26.a.107
  %l.108 = load {ptr, i64}, ptr %t25.a.103
  %l.109 = load {ptr, i64}, ptr %t26.a.107
  %rt.110 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.108, {ptr, i64} %l.109)
  store {ptr, i64} %rt.110, ptr %str_track.111
  store {ptr, i64} %rt.110, ptr %t27.a.112
  %l.113 = load {ptr, i64, i64, i64, i64}, ptr %t18.a.86
  %l.114 = load i64, ptr %next24.a.99
  store {ptr, i64, i64, i64, i64} %l.113, ptr %lp.115
  %rt.116 = call ptr @__mn_list_get(ptr %lp.115, i64 %l.114)
  %el.117 = load double, ptr %rt.116
  store double %el.117, ptr %t28.a.118
  %l.119 = load double, ptr %t28.a.118
  %rt.120 = call {ptr, i64} @__mn_str_from_float(double %l.119)
  store {ptr, i64} %rt.120, ptr %str_track.121
  store {ptr, i64} %rt.120, ptr %t29.a.122
  %l.123 = load {ptr, i64}, ptr %t27.a.112
  %l.124 = load {ptr, i64}, ptr %t29.a.122
  %rt.125 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.123, {ptr, i64} %l.124)
  store {ptr, i64} %rt.125, ptr %str_track.126
  store {ptr, i64} %rt.125, ptr %t30.a.127
  %l.128 = load {ptr, i64}, ptr %t30.a.127
  call void @__mn_str_println({ptr, i64} %l.128)
  store i1 0, ptr %t31.a.129
  br label %for_header6
for_exit8:
  %l.130 = load ptr, ptr %t21.a.92
  %c.131 = call i1 @__mn_range_free(ptr %l.130)
  store i1 %c.131, ptr %range_free32.a.132
  br label %if_merge2
drop.check.41:
  call void @__mn_str_free({ptr, i64} %drop.s.38)
  br label %drop.skip.41
drop.skip.41:
  %drop.s.42 = load {ptr, i64}, ptr %str_track.14
  %drop.p.43 = extractvalue {ptr, i64} %drop.s.42, 0
  %drop.null.44 = icmp eq ptr %drop.p.43, null
  br i1 %drop.null.44, label %drop.skip.45, label %drop.check.45
drop.check.45:
  call void @__mn_str_free({ptr, i64} %drop.s.42)
  br label %drop.skip.45
drop.skip.45:
  %drop.lv.46 = load {ptr, i64, i64, i64, i64}, ptr %a.a.21
  %drop.lp.47 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.46, 0
  %drop.lnull.48 = icmp eq ptr %drop.lp.47, null
  br i1 %drop.lnull.48, label %drop.lskip.49, label %drop.lcheck.49
drop.lcheck.49:
  call void @__mn_list_free(ptr %a.a.21)
  br label %drop.lskip.49
drop.lskip.49:
  %drop.lv.50 = load {ptr, i64, i64, i64, i64}, ptr %b.a.25
  %drop.lp.51 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.50, 0
  %drop.lnull.52 = icmp eq ptr %drop.lp.51, null
  br i1 %drop.lnull.52, label %drop.lskip.53, label %drop.lcheck.53
drop.lcheck.53:
  call void @__mn_list_free(ptr %b.a.25)
  br label %drop.lskip.53
drop.lskip.53:
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.46.0"}
