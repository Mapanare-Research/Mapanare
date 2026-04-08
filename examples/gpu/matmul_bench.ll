; ModuleID = 'matmul_bench'
source_filename = "matmul_bench"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [16 x i8] c"No GPU available", align 8
@.str.1 = private constant [7 x i8] c"Matmul ", align 8
@.str.2 = private constant [1 x i8] c"x", align 8
@.str.3 = private constant [9 x i8] c" done on ", align 8
@.str.4 = private constant [12 x i8] c"result[0] = ", align 8
@.str.5 = private constant [12 x i8] c"result[1] = ", align 8

declare i64 @__mn_gpu_available() nounwind
declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind
declare ptr @__mn_range(i64, i64)
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_list_free(ptr) nounwind willreturn
declare i1 @__iter_has_next(ptr)
declare i64 @__iter_next(ptr)
declare i1 @__mn_range_free(ptr) nounwind willreturn
declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_matmul(ptr, ptr, i64, i64, i64) nounwind
declare {ptr, i64} @__mn_str_from_int(i64) nounwind
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind
declare {ptr, i64} @__mn_gpu_device_name() nounwind
declare ptr @__mn_list_get(ptr, i64) nounwind readonly
declare {ptr, i64} @__mn_str_from_float(double) nounwind
declare void @__mn_list_push(ptr, ptr) nounwind

define i64 @main() {
pre_entry:
  %t0.a.2 = alloca i1, align 8
  store i1 0, ptr %t0.a.2
  %n.a.4 = alloca i64, align 8
  store i64 0, ptr %n.a.4
  %t2.a.6 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t2.a.6
  %a.a.8 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %a.a.8
  %t3.a.10 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t3.a.10
  %b.a.12 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %b.a.12
  %t4.a.13 = alloca i64, align 8
  store i64 0, ptr %t4.a.13
  %t5.a.14 = alloca i64, align 8
  store i64 0, ptr %t5.a.14
  %t6.a.18 = alloca ptr, align 8
  store ptr null, ptr %t6.a.18
  %t44.a.22 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t44.a.22
  %t45.a.24 = alloca i1, align 8
  store i1 0, ptr %t45.a.24
  %has_next8.a.35 = alloca i1, align 8
  store i1 0, ptr %has_next8.a.35
  %next9.a.39 = alloca i64, align 8
  store i64 0, ptr %next9.a.39
  %t10.a.43 = alloca i64, align 8
  store i64 0, ptr %t10.a.43
  %t11.a.47 = alloca i64, align 8
  store i64 0, ptr %t11.a.47
  %t12.a.51 = alloca i1, align 8
  store i1 0, ptr %t12.a.51
  %range_free18.a.55 = alloca i1, align 8
  store i1 0, ptr %range_free18.a.55
  %gma.61 = alloca {ptr, i64, i64, i64, i64}, align 8
  %gmb.62 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t19.a.64 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t19.a.64
  %t20.a.68 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t20.a.68
  %str_track.71 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.71
  %t21.a.72 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t21.a.72
  %str_track.76 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.76
  %t22.a.77 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t22.a.77
  %t23.a.81 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t23.a.81
  %str_track.85 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.85
  %t24.a.86 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t24.a.86
  %str_track.89 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.89
  %t25.a.90 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t25.a.90
  %str_track.94 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.94
  %t26.a.95 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t26.a.95
  %t27.a.99 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t27.a.99
  %str_track.103 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.103
  %t28.a.104 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t28.a.104
  %str_track.106 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.106
  %t29.a.107 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t29.a.107
  %str_track.111 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.111
  %t30.a.112 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t30.a.112
  %t31.a.114 = alloca i1, align 8
  store i1 0, ptr %t31.a.114
  %t32.a.118 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t32.a.118
  %t33.a.119 = alloca i64, align 8
  store i64 0, ptr %t33.a.119
  %lp.122 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t34.a.125 = alloca double, align 8
  store double 0.000000e+00, ptr %t34.a.125
  %str_track.128 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.128
  %t35.a.129 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t35.a.129
  %str_track.133 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.133
  %t36.a.134 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t36.a.134
  %t37.a.136 = alloca i1, align 8
  store i1 0, ptr %t37.a.136
  %t38.a.140 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t38.a.140
  %t39.a.141 = alloca i64, align 8
  store i64 0, ptr %t39.a.141
  %lp.144 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t40.a.147 = alloca double, align 8
  store double 0.000000e+00, ptr %t40.a.147
  %str_track.150 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.150
  %t41.a.151 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t41.a.151
  %str_track.155 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.155
  %t42.a.156 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t42.a.156
  %t43.a.158 = alloca i1, align 8
  store i1 0, ptr %t43.a.158
  %t13.a.159 = alloca double, align 8
  store double 0.000000e+00, ptr %t13.a.159
  %ea.161 = alloca double, align 8
  %t14.a.163 = alloca double, align 8
  store double 0.000000e+00, ptr %t14.a.163
  %ea.165 = alloca double, align 8
  %t16.a.170 = alloca i64, align 8
  store i64 0, ptr %t16.a.170
  %t17.a.173 = alloca double, align 8
  store double 0.000000e+00, ptr %t17.a.173
  %ea.175 = alloca double, align 8
  br label %entry
entry:
  %rt.0 = call i64 @__mn_gpu_available()
  %ga.1 = icmp ne i64 %rt.0, 0
  store i1 %ga.1, ptr %t0.a.2
  %l.3 = load i1, ptr %t0.a.2
  br i1 %l.3, label %if_then0, label %if_else1
if_then0:
  store i64 64, ptr %n.a.4
  %ln.5 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.5, ptr %t2.a.6
  %l.7 = load {ptr, i64, i64, i64, i64}, ptr %t2.a.6
  store {ptr, i64, i64, i64, i64} %l.7, ptr %a.a.8
  %ln.9 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.9, ptr %t3.a.10
  %l.11 = load {ptr, i64, i64, i64, i64}, ptr %t3.a.10
  store {ptr, i64, i64, i64, i64} %l.11, ptr %b.a.12
  store i64 0, ptr %t4.a.13
  store i64 4096, ptr %t5.a.14
  %l.15 = load i64, ptr %t4.a.13
  %l.16 = load i64, ptr %t5.a.14
  %c.17 = call ptr @__mn_range(i64 %l.15, i64 %l.16)
  store ptr %c.17, ptr %t6.a.18
  br label %for_header3
if_else1:
  %sp.19 = getelementptr inbounds [16 x i8], ptr @.str.0, i64 0, i64 0
  %s.20 = insertvalue {ptr, i64} undef, ptr %sp.19, 0
  %s.21 = insertvalue {ptr, i64} %s.20, i64 16, 1
  store {ptr, i64} %s.21, ptr %t44.a.22
  %l.23 = load {ptr, i64}, ptr %t44.a.22
  call void @__mn_str_println({ptr, i64} %l.23)
  store i1 0, ptr %t45.a.24
  br label %if_merge2
if_merge2:
  %drop.lv.25 = load {ptr, i64, i64, i64, i64}, ptr %a.a.8
  %drop.lp.26 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.25, 0
  %drop.lnull.27 = icmp eq ptr %drop.lp.26, null
  br i1 %drop.lnull.27, label %drop.lskip.28, label %drop.lcheck.28
for_header3:
  %l.33 = load ptr, ptr %t6.a.18
  %c.34 = call i1 @__iter_has_next(ptr %l.33)
  store i1 %c.34, ptr %has_next8.a.35
  %l.36 = load i1, ptr %has_next8.a.35
  br i1 %l.36, label %for_body4, label %for_exit5
for_body4:
  %l.37 = load ptr, ptr %t6.a.18
  %c.38 = call i64 @__iter_next(ptr %l.37)
  store i64 %c.38, ptr %next9.a.39
  %l.40 = load i64, ptr %next9.a.39
  %l.41 = load i64, ptr %n.a.4
  %i.42 = sdiv i64 %l.40, %l.41
  store i64 %i.42, ptr %t10.a.43
  %l.44 = load i64, ptr %next9.a.39
  %l.45 = load i64, ptr %n.a.4
  %i.46 = srem i64 %l.44, %l.45
  store i64 %i.46, ptr %t11.a.47
  %l.48 = load i64, ptr %t10.a.43
  %l.49 = load i64, ptr %t11.a.47
  %i.50 = icmp eq i64 %l.48, %l.49
  store i1 %i.50, ptr %t12.a.51
  %l.52 = load i1, ptr %t12.a.51
  br i1 %l.52, label %if_then6, label %if_else7
for_exit5:
  %l.53 = load ptr, ptr %t6.a.18
  %c.54 = call i1 @__mn_range_free(ptr %l.53)
  store i1 %c.54, ptr %range_free18.a.55
  %l.56 = load {ptr, i64, i64, i64, i64}, ptr %a.a.8
  %l.57 = load {ptr, i64, i64, i64, i64}, ptr %b.a.12
  %l.58 = load i64, ptr %n.a.4
  %l.59 = load i64, ptr %n.a.4
  %l.60 = load i64, ptr %n.a.4
  store {ptr, i64, i64, i64, i64} %l.56, ptr %gma.61
  store {ptr, i64, i64, i64, i64} %l.57, ptr %gmb.62
  %rt.63 = call {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_matmul(ptr %gma.61, ptr %gmb.62, i64 %l.58, i64 %l.59, i64 %l.60)
  store {ptr, i64, i64, i64, i64} %rt.63, ptr %t19.a.64
  %sp.65 = getelementptr inbounds [7 x i8], ptr @.str.1, i64 0, i64 0
  %s.66 = insertvalue {ptr, i64} undef, ptr %sp.65, 0
  %s.67 = insertvalue {ptr, i64} %s.66, i64 7, 1
  store {ptr, i64} %s.67, ptr %t20.a.68
  %l.69 = load i64, ptr %n.a.4
  %rt.70 = call {ptr, i64} @__mn_str_from_int(i64 %l.69)
  store {ptr, i64} %rt.70, ptr %str_track.71
  store {ptr, i64} %rt.70, ptr %t21.a.72
  %l.73 = load {ptr, i64}, ptr %t20.a.68
  %l.74 = load {ptr, i64}, ptr %t21.a.72
  %rt.75 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.73, {ptr, i64} %l.74)
  store {ptr, i64} %rt.75, ptr %str_track.76
  store {ptr, i64} %rt.75, ptr %t22.a.77
  %sp.78 = getelementptr inbounds [1 x i8], ptr @.str.2, i64 0, i64 0
  %s.79 = insertvalue {ptr, i64} undef, ptr %sp.78, 0
  %s.80 = insertvalue {ptr, i64} %s.79, i64 1, 1
  store {ptr, i64} %s.80, ptr %t23.a.81
  %l.82 = load {ptr, i64}, ptr %t22.a.77
  %l.83 = load {ptr, i64}, ptr %t23.a.81
  %rt.84 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.82, {ptr, i64} %l.83)
  store {ptr, i64} %rt.84, ptr %str_track.85
  store {ptr, i64} %rt.84, ptr %t24.a.86
  %l.87 = load i64, ptr %n.a.4
  %rt.88 = call {ptr, i64} @__mn_str_from_int(i64 %l.87)
  store {ptr, i64} %rt.88, ptr %str_track.89
  store {ptr, i64} %rt.88, ptr %t25.a.90
  %l.91 = load {ptr, i64}, ptr %t24.a.86
  %l.92 = load {ptr, i64}, ptr %t25.a.90
  %rt.93 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.91, {ptr, i64} %l.92)
  store {ptr, i64} %rt.93, ptr %str_track.94
  store {ptr, i64} %rt.93, ptr %t26.a.95
  %sp.96 = getelementptr inbounds [9 x i8], ptr @.str.3, i64 0, i64 0
  %s.97 = insertvalue {ptr, i64} undef, ptr %sp.96, 0
  %s.98 = insertvalue {ptr, i64} %s.97, i64 9, 1
  store {ptr, i64} %s.98, ptr %t27.a.99
  %l.100 = load {ptr, i64}, ptr %t26.a.95
  %l.101 = load {ptr, i64}, ptr %t27.a.99
  %rt.102 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.100, {ptr, i64} %l.101)
  store {ptr, i64} %rt.102, ptr %str_track.103
  store {ptr, i64} %rt.102, ptr %t28.a.104
  %rt.105 = call {ptr, i64} @__mn_gpu_device_name()
  store {ptr, i64} %rt.105, ptr %str_track.106
  store {ptr, i64} %rt.105, ptr %t29.a.107
  %l.108 = load {ptr, i64}, ptr %t28.a.104
  %l.109 = load {ptr, i64}, ptr %t29.a.107
  %rt.110 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.108, {ptr, i64} %l.109)
  store {ptr, i64} %rt.110, ptr %str_track.111
  store {ptr, i64} %rt.110, ptr %t30.a.112
  %l.113 = load {ptr, i64}, ptr %t30.a.112
  call void @__mn_str_println({ptr, i64} %l.113)
  store i1 0, ptr %t31.a.114
  %sp.115 = getelementptr inbounds [12 x i8], ptr @.str.4, i64 0, i64 0
  %s.116 = insertvalue {ptr, i64} undef, ptr %sp.115, 0
  %s.117 = insertvalue {ptr, i64} %s.116, i64 12, 1
  store {ptr, i64} %s.117, ptr %t32.a.118
  store i64 0, ptr %t33.a.119
  %l.120 = load {ptr, i64, i64, i64, i64}, ptr %t19.a.64
  %l.121 = load i64, ptr %t33.a.119
  store {ptr, i64, i64, i64, i64} %l.120, ptr %lp.122
  %rt.123 = call ptr @__mn_list_get(ptr %lp.122, i64 %l.121)
  %el.124 = load double, ptr %rt.123
  store double %el.124, ptr %t34.a.125
  %l.126 = load double, ptr %t34.a.125
  %rt.127 = call {ptr, i64} @__mn_str_from_float(double %l.126)
  store {ptr, i64} %rt.127, ptr %str_track.128
  store {ptr, i64} %rt.127, ptr %t35.a.129
  %l.130 = load {ptr, i64}, ptr %t32.a.118
  %l.131 = load {ptr, i64}, ptr %t35.a.129
  %rt.132 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.130, {ptr, i64} %l.131)
  store {ptr, i64} %rt.132, ptr %str_track.133
  store {ptr, i64} %rt.132, ptr %t36.a.134
  %l.135 = load {ptr, i64}, ptr %t36.a.134
  call void @__mn_str_println({ptr, i64} %l.135)
  store i1 0, ptr %t37.a.136
  %sp.137 = getelementptr inbounds [12 x i8], ptr @.str.5, i64 0, i64 0
  %s.138 = insertvalue {ptr, i64} undef, ptr %sp.137, 0
  %s.139 = insertvalue {ptr, i64} %s.138, i64 12, 1
  store {ptr, i64} %s.139, ptr %t38.a.140
  store i64 1, ptr %t39.a.141
  %l.142 = load {ptr, i64, i64, i64, i64}, ptr %t19.a.64
  %l.143 = load i64, ptr %t39.a.141
  store {ptr, i64, i64, i64, i64} %l.142, ptr %lp.144
  %rt.145 = call ptr @__mn_list_get(ptr %lp.144, i64 %l.143)
  %el.146 = load double, ptr %rt.145
  store double %el.146, ptr %t40.a.147
  %l.148 = load double, ptr %t40.a.147
  %rt.149 = call {ptr, i64} @__mn_str_from_float(double %l.148)
  store {ptr, i64} %rt.149, ptr %str_track.150
  store {ptr, i64} %rt.149, ptr %t41.a.151
  %l.152 = load {ptr, i64}, ptr %t38.a.140
  %l.153 = load {ptr, i64}, ptr %t41.a.151
  %rt.154 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.152, {ptr, i64} %l.153)
  store {ptr, i64} %rt.154, ptr %str_track.155
  store {ptr, i64} %rt.154, ptr %t42.a.156
  %l.157 = load {ptr, i64}, ptr %t42.a.156
  call void @__mn_str_println({ptr, i64} %l.157)
  store i1 0, ptr %t43.a.158
  br label %if_merge2
if_then6:
  store double 0x3FF0000000000000, ptr %t13.a.159
  %l.160 = load double, ptr %t13.a.159
  store double %l.160, ptr %ea.161
  call void @__mn_list_push(ptr %t2.a.6, ptr %ea.161)
  %ul.162 = load {ptr, i64, i64, i64, i64}, ptr %t2.a.6
  store {ptr, i64, i64, i64, i64} %ul.162, ptr %a.a.8
  br label %if_merge8
if_else7:
  store double 0.000000e+00, ptr %t14.a.163
  %l.164 = load double, ptr %t14.a.163
  store double %l.164, ptr %ea.165
  call void @__mn_list_push(ptr %t2.a.6, ptr %ea.165)
  %ul.166 = load {ptr, i64, i64, i64, i64}, ptr %t2.a.6
  store {ptr, i64, i64, i64, i64} %ul.166, ptr %a.a.8
  br label %if_merge8
if_merge8:
  %l.167 = load i64, ptr %next9.a.39
  %l.168 = load i64, ptr %n.a.4
  %i.169 = srem i64 %l.167, %l.168
  store i64 %i.169, ptr %t16.a.170
  %l.171 = load i64, ptr %t16.a.170
  %cf.172 = sitofp i64 %l.171 to double
  store double %cf.172, ptr %t17.a.173
  %l.174 = load double, ptr %t17.a.173
  store double %l.174, ptr %ea.175
  call void @__mn_list_push(ptr %t3.a.10, ptr %ea.175)
  %ul.176 = load {ptr, i64, i64, i64, i64}, ptr %t3.a.10
  store {ptr, i64, i64, i64, i64} %ul.176, ptr %b.a.12
  br label %for_header3
drop.lcheck.28:
  call void @__mn_list_free(ptr %a.a.8)
  br label %drop.lskip.28
drop.lskip.28:
  %drop.lv.29 = load {ptr, i64, i64, i64, i64}, ptr %b.a.12
  %drop.lp.30 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.29, 0
  %drop.lnull.31 = icmp eq ptr %drop.lp.30, null
  br i1 %drop.lnull.31, label %drop.lskip.32, label %drop.lcheck.32
drop.lcheck.32:
  call void @__mn_list_free(ptr %b.a.12)
  br label %drop.lskip.32
drop.lskip.32:
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.46.0"}
