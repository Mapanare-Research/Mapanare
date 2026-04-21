; ModuleID = '40_gpu_tensor'
source_filename = "40_gpu_tensor"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [7 x i8] c"add[0]=", align 8
@.str.1 = private constant [7 x i8] c"add[1]=", align 8
@.str.2 = private constant [7 x i8] c"mul[0]=", align 8
@.str.3 = private constant [7 x i8] c"mul[3]=", align 8
@.str.4 = private constant [27 x i8] c"GPU not available, skipping", align 8

declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind willreturn
declare void @__mn_list_push(ptr, ptr) nounwind
declare i64 @__mn_gpu_available() nounwind readonly willreturn
declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_add(ptr, ptr) nounwind willreturn
declare ptr @__mn_list_get(ptr, i64) nounwind readonly willreturn
declare {ptr, i64} @__mn_str_from_float(double) nounwind willreturn
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_mul(ptr, ptr) nounwind willreturn
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_list_free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca double, align 8
  store double 0.000000e+00, ptr %t0.a.0
  %t1.a.1 = alloca double, align 8
  store double 0.000000e+00, ptr %t1.a.1
  %t2.a.2 = alloca double, align 8
  store double 0.000000e+00, ptr %t2.a.2
  %t3.a.3 = alloca double, align 8
  store double 0.000000e+00, ptr %t3.a.3
  %lp.5 = alloca {ptr, i64, i64, i64, i64}, align 8
  %ea.7 = alloca double, align 8
  %ea.10 = alloca double, align 8
  %ea.13 = alloca double, align 8
  %ea.16 = alloca double, align 8
  %t4.a.19 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t4.a.19
  %t5.a.20 = alloca double, align 8
  store double 0.000000e+00, ptr %t5.a.20
  %t6.a.21 = alloca double, align 8
  store double 0.000000e+00, ptr %t6.a.21
  %t7.a.22 = alloca double, align 8
  store double 0.000000e+00, ptr %t7.a.22
  %t8.a.23 = alloca double, align 8
  store double 0.000000e+00, ptr %t8.a.23
  %lp.25 = alloca {ptr, i64, i64, i64, i64}, align 8
  %ea.27 = alloca double, align 8
  %ea.30 = alloca double, align 8
  %ea.33 = alloca double, align 8
  %ea.36 = alloca double, align 8
  %t9.a.39 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t9.a.39
  %t10.a.42 = alloca i1, align 8
  store i1 0, ptr %t10.a.42
  %gta.46 = alloca {ptr, i64, i64, i64, i64}, align 8
  %gtb.47 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t11.a.49 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t11.a.49
  %t12.a.53 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t12.a.53
  %t13.a.54 = alloca i64, align 8
  store i64 0, ptr %t13.a.54
  %lp.57 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t14.a.60 = alloca double, align 8
  store double 0.000000e+00, ptr %t14.a.60
  %str_track.63 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.63
  %t15.a.64 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t15.a.64
  %str_track.68 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.68
  %t16.a.69 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t16.a.69
  %t17.a.71 = alloca i1, align 8
  store i1 0, ptr %t17.a.71
  %t18.a.75 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t18.a.75
  %t19.a.76 = alloca i64, align 8
  store i64 0, ptr %t19.a.76
  %lp.79 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t20.a.82 = alloca double, align 8
  store double 0.000000e+00, ptr %t20.a.82
  %str_track.85 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.85
  %t21.a.86 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t21.a.86
  %str_track.90 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.90
  %t22.a.91 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t22.a.91
  %t23.a.93 = alloca i1, align 8
  store i1 0, ptr %t23.a.93
  %gta.96 = alloca {ptr, i64, i64, i64, i64}, align 8
  %gtb.97 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t24.a.99 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t24.a.99
  %t25.a.103 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t25.a.103
  %t26.a.104 = alloca i64, align 8
  store i64 0, ptr %t26.a.104
  %lp.107 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t27.a.110 = alloca double, align 8
  store double 0.000000e+00, ptr %t27.a.110
  %str_track.113 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.113
  %t28.a.114 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t28.a.114
  %str_track.118 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.118
  %t29.a.119 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t29.a.119
  %t30.a.121 = alloca i1, align 8
  store i1 0, ptr %t30.a.121
  %t31.a.125 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t31.a.125
  %t32.a.126 = alloca i64, align 8
  store i64 0, ptr %t32.a.126
  %lp.129 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t33.a.132 = alloca double, align 8
  store double 0.000000e+00, ptr %t33.a.132
  %str_track.135 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.135
  %t34.a.136 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t34.a.136
  %str_track.140 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.140
  %t35.a.141 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t35.a.141
  %t36.a.143 = alloca i1, align 8
  store i1 0, ptr %t36.a.143
  %t37.a.147 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t37.a.147
  %t38.a.149 = alloca i1, align 8
  store i1 0, ptr %t38.a.149
  br label %entry
entry:
  store double 0x3FF0000000000000, ptr %t0.a.0
  store double 0x4000000000000000, ptr %t1.a.1
  store double 0x4008000000000000, ptr %t2.a.2
  store double 0x4010000000000000, ptr %t3.a.3
  %ln.4 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.4, ptr %lp.5
  %l.6 = load double, ptr %t0.a.0
  store double %l.6, ptr %ea.7
  call void @__mn_list_push(ptr %lp.5, ptr %ea.7)
  %l.9 = load double, ptr %t1.a.1
  store double %l.9, ptr %ea.10
  call void @__mn_list_push(ptr %lp.5, ptr %ea.10)
  %l.12 = load double, ptr %t2.a.2
  store double %l.12, ptr %ea.13
  call void @__mn_list_push(ptr %lp.5, ptr %ea.13)
  %l.15 = load double, ptr %t3.a.3
  store double %l.15, ptr %ea.16
  call void @__mn_list_push(ptr %lp.5, ptr %ea.16)
  %ll.18 = load {ptr, i64, i64, i64, i64}, ptr %lp.5
  store {ptr, i64, i64, i64, i64} %ll.18, ptr %t4.a.19
  store double 0x4014000000000000, ptr %t5.a.20
  store double 0x4018000000000000, ptr %t6.a.21
  store double 0x401C000000000000, ptr %t7.a.22
  store double 0x4020000000000000, ptr %t8.a.23
  %ln.24 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.24, ptr %lp.25
  %l.26 = load double, ptr %t5.a.20
  store double %l.26, ptr %ea.27
  call void @__mn_list_push(ptr %lp.25, ptr %ea.27)
  %l.29 = load double, ptr %t6.a.21
  store double %l.29, ptr %ea.30
  call void @__mn_list_push(ptr %lp.25, ptr %ea.30)
  %l.32 = load double, ptr %t7.a.22
  store double %l.32, ptr %ea.33
  call void @__mn_list_push(ptr %lp.25, ptr %ea.33)
  %l.35 = load double, ptr %t8.a.23
  store double %l.35, ptr %ea.36
  call void @__mn_list_push(ptr %lp.25, ptr %ea.36)
  %ll.38 = load {ptr, i64, i64, i64, i64}, ptr %lp.25
  store {ptr, i64, i64, i64, i64} %ll.38, ptr %t9.a.39
  %rt.40 = call i64 @__mn_gpu_available()
  %ga.41 = icmp ne i64 %rt.40, 0
  store i1 %ga.41, ptr %t10.a.42
  %l.43 = load i1, ptr %t10.a.42
  br i1 %l.43, label %if_then0, label %if_else1
if_then0:
  %l.44 = load {ptr, i64, i64, i64, i64}, ptr %t4.a.19
  %l.45 = load {ptr, i64, i64, i64, i64}, ptr %t9.a.39
  store {ptr, i64, i64, i64, i64} %l.44, ptr %gta.46
  store {ptr, i64, i64, i64, i64} %l.45, ptr %gtb.47
  %rt.48 = call {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_add(ptr %gta.46, ptr %gtb.47)
  store {ptr, i64, i64, i64, i64} %rt.48, ptr %t11.a.49
  %sp.50 = getelementptr inbounds [7 x i8], ptr @.str.0, i64 0, i64 0
  %s.51 = insertvalue {ptr, i64} undef, ptr %sp.50, 0
  %s.52 = insertvalue {ptr, i64} %s.51, i64 7, 1
  store {ptr, i64} %s.52, ptr %t12.a.53
  store i64 0, ptr %t13.a.54
  %l.55 = load {ptr, i64, i64, i64, i64}, ptr %t11.a.49
  %l.56 = load i64, ptr %t13.a.54
  store {ptr, i64, i64, i64, i64} %l.55, ptr %lp.57
  %rt.58 = call ptr @__mn_list_get(ptr %lp.57, i64 %l.56)
  %el.59 = load double, ptr %rt.58
  store double %el.59, ptr %t14.a.60
  %l.61 = load double, ptr %t14.a.60
  %rt.62 = call {ptr, i64} @__mn_str_from_float(double %l.61)
  store {ptr, i64} %rt.62, ptr %str_track.63
  store {ptr, i64} %rt.62, ptr %t15.a.64
  %l.65 = load {ptr, i64}, ptr %t12.a.53
  %l.66 = load {ptr, i64}, ptr %t15.a.64
  %rt.67 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.65, {ptr, i64} %l.66)
  store {ptr, i64} %rt.67, ptr %str_track.68
  store {ptr, i64} %rt.67, ptr %t16.a.69
  %l.70 = load {ptr, i64}, ptr %t16.a.69
  call void @__mn_str_println({ptr, i64} %l.70)
  store i1 0, ptr %t17.a.71
  %sp.72 = getelementptr inbounds [7 x i8], ptr @.str.1, i64 0, i64 0
  %s.73 = insertvalue {ptr, i64} undef, ptr %sp.72, 0
  %s.74 = insertvalue {ptr, i64} %s.73, i64 7, 1
  store {ptr, i64} %s.74, ptr %t18.a.75
  store i64 1, ptr %t19.a.76
  %l.77 = load {ptr, i64, i64, i64, i64}, ptr %t11.a.49
  %l.78 = load i64, ptr %t19.a.76
  store {ptr, i64, i64, i64, i64} %l.77, ptr %lp.79
  %rt.80 = call ptr @__mn_list_get(ptr %lp.79, i64 %l.78)
  %el.81 = load double, ptr %rt.80
  store double %el.81, ptr %t20.a.82
  %l.83 = load double, ptr %t20.a.82
  %rt.84 = call {ptr, i64} @__mn_str_from_float(double %l.83)
  store {ptr, i64} %rt.84, ptr %str_track.85
  store {ptr, i64} %rt.84, ptr %t21.a.86
  %l.87 = load {ptr, i64}, ptr %t18.a.75
  %l.88 = load {ptr, i64}, ptr %t21.a.86
  %rt.89 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.87, {ptr, i64} %l.88)
  store {ptr, i64} %rt.89, ptr %str_track.90
  store {ptr, i64} %rt.89, ptr %t22.a.91
  %l.92 = load {ptr, i64}, ptr %t22.a.91
  call void @__mn_str_println({ptr, i64} %l.92)
  store i1 0, ptr %t23.a.93
  %l.94 = load {ptr, i64, i64, i64, i64}, ptr %t4.a.19
  %l.95 = load {ptr, i64, i64, i64, i64}, ptr %t9.a.39
  store {ptr, i64, i64, i64, i64} %l.94, ptr %gta.96
  store {ptr, i64, i64, i64, i64} %l.95, ptr %gtb.97
  %rt.98 = call {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_mul(ptr %gta.96, ptr %gtb.97)
  store {ptr, i64, i64, i64, i64} %rt.98, ptr %t24.a.99
  %sp.100 = getelementptr inbounds [7 x i8], ptr @.str.2, i64 0, i64 0
  %s.101 = insertvalue {ptr, i64} undef, ptr %sp.100, 0
  %s.102 = insertvalue {ptr, i64} %s.101, i64 7, 1
  store {ptr, i64} %s.102, ptr %t25.a.103
  store i64 0, ptr %t26.a.104
  %l.105 = load {ptr, i64, i64, i64, i64}, ptr %t24.a.99
  %l.106 = load i64, ptr %t26.a.104
  store {ptr, i64, i64, i64, i64} %l.105, ptr %lp.107
  %rt.108 = call ptr @__mn_list_get(ptr %lp.107, i64 %l.106)
  %el.109 = load double, ptr %rt.108
  store double %el.109, ptr %t27.a.110
  %l.111 = load double, ptr %t27.a.110
  %rt.112 = call {ptr, i64} @__mn_str_from_float(double %l.111)
  store {ptr, i64} %rt.112, ptr %str_track.113
  store {ptr, i64} %rt.112, ptr %t28.a.114
  %l.115 = load {ptr, i64}, ptr %t25.a.103
  %l.116 = load {ptr, i64}, ptr %t28.a.114
  %rt.117 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.115, {ptr, i64} %l.116)
  store {ptr, i64} %rt.117, ptr %str_track.118
  store {ptr, i64} %rt.117, ptr %t29.a.119
  %l.120 = load {ptr, i64}, ptr %t29.a.119
  call void @__mn_str_println({ptr, i64} %l.120)
  store i1 0, ptr %t30.a.121
  %sp.122 = getelementptr inbounds [7 x i8], ptr @.str.3, i64 0, i64 0
  %s.123 = insertvalue {ptr, i64} undef, ptr %sp.122, 0
  %s.124 = insertvalue {ptr, i64} %s.123, i64 7, 1
  store {ptr, i64} %s.124, ptr %t31.a.125
  store i64 3, ptr %t32.a.126
  %l.127 = load {ptr, i64, i64, i64, i64}, ptr %t24.a.99
  %l.128 = load i64, ptr %t32.a.126
  store {ptr, i64, i64, i64, i64} %l.127, ptr %lp.129
  %rt.130 = call ptr @__mn_list_get(ptr %lp.129, i64 %l.128)
  %el.131 = load double, ptr %rt.130
  store double %el.131, ptr %t33.a.132
  %l.133 = load double, ptr %t33.a.132
  %rt.134 = call {ptr, i64} @__mn_str_from_float(double %l.133)
  store {ptr, i64} %rt.134, ptr %str_track.135
  store {ptr, i64} %rt.134, ptr %t34.a.136
  %l.137 = load {ptr, i64}, ptr %t31.a.125
  %l.138 = load {ptr, i64}, ptr %t34.a.136
  %rt.139 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.137, {ptr, i64} %l.138)
  store {ptr, i64} %rt.139, ptr %str_track.140
  store {ptr, i64} %rt.139, ptr %t35.a.141
  %l.142 = load {ptr, i64}, ptr %t35.a.141
  call void @__mn_str_println({ptr, i64} %l.142)
  store i1 0, ptr %t36.a.143
  br label %if_merge2
if_else1:
  %sp.144 = getelementptr inbounds [27 x i8], ptr @.str.4, i64 0, i64 0
  %s.145 = insertvalue {ptr, i64} undef, ptr %sp.144, 0
  %s.146 = insertvalue {ptr, i64} %s.145, i64 27, 1
  store {ptr, i64} %s.146, ptr %t37.a.147
  %l.148 = load {ptr, i64}, ptr %t37.a.147
  call void @__mn_str_println({ptr, i64} %l.148)
  store i1 0, ptr %t38.a.149
  br label %if_merge2
if_merge2:
  %drop.s.150 = load {ptr, i64}, ptr %str_track.63
  %drop.p.151 = extractvalue {ptr, i64} %drop.s.150, 0
  %drop.null.152 = icmp eq ptr %drop.p.151, null
  br i1 %drop.null.152, label %drop.skip.153, label %drop.check.153
drop.check.153:
  call void @__mn_str_free({ptr, i64} %drop.s.150)
  br label %drop.skip.153
drop.skip.153:
  %drop.s.154 = load {ptr, i64}, ptr %str_track.68
  %drop.p.155 = extractvalue {ptr, i64} %drop.s.154, 0
  %drop.null.156 = icmp eq ptr %drop.p.155, null
  br i1 %drop.null.156, label %drop.skip.157, label %drop.check.157
drop.check.157:
  call void @__mn_str_free({ptr, i64} %drop.s.154)
  br label %drop.skip.157
drop.skip.157:
  %drop.s.158 = load {ptr, i64}, ptr %str_track.85
  %drop.p.159 = extractvalue {ptr, i64} %drop.s.158, 0
  %drop.null.160 = icmp eq ptr %drop.p.159, null
  br i1 %drop.null.160, label %drop.skip.161, label %drop.check.161
drop.check.161:
  call void @__mn_str_free({ptr, i64} %drop.s.158)
  br label %drop.skip.161
drop.skip.161:
  %drop.s.162 = load {ptr, i64}, ptr %str_track.90
  %drop.p.163 = extractvalue {ptr, i64} %drop.s.162, 0
  %drop.null.164 = icmp eq ptr %drop.p.163, null
  br i1 %drop.null.164, label %drop.skip.165, label %drop.check.165
drop.check.165:
  call void @__mn_str_free({ptr, i64} %drop.s.162)
  br label %drop.skip.165
drop.skip.165:
  %drop.s.166 = load {ptr, i64}, ptr %str_track.113
  %drop.p.167 = extractvalue {ptr, i64} %drop.s.166, 0
  %drop.null.168 = icmp eq ptr %drop.p.167, null
  br i1 %drop.null.168, label %drop.skip.169, label %drop.check.169
drop.check.169:
  call void @__mn_str_free({ptr, i64} %drop.s.166)
  br label %drop.skip.169
drop.skip.169:
  %drop.s.170 = load {ptr, i64}, ptr %str_track.118
  %drop.p.171 = extractvalue {ptr, i64} %drop.s.170, 0
  %drop.null.172 = icmp eq ptr %drop.p.171, null
  br i1 %drop.null.172, label %drop.skip.173, label %drop.check.173
drop.check.173:
  call void @__mn_str_free({ptr, i64} %drop.s.170)
  br label %drop.skip.173
drop.skip.173:
  %drop.s.174 = load {ptr, i64}, ptr %str_track.135
  %drop.p.175 = extractvalue {ptr, i64} %drop.s.174, 0
  %drop.null.176 = icmp eq ptr %drop.p.175, null
  br i1 %drop.null.176, label %drop.skip.177, label %drop.check.177
drop.check.177:
  call void @__mn_str_free({ptr, i64} %drop.s.174)
  br label %drop.skip.177
drop.skip.177:
  %drop.s.178 = load {ptr, i64}, ptr %str_track.140
  %drop.p.179 = extractvalue {ptr, i64} %drop.s.178, 0
  %drop.null.180 = icmp eq ptr %drop.p.179, null
  br i1 %drop.null.180, label %drop.skip.181, label %drop.check.181
drop.check.181:
  call void @__mn_str_free({ptr, i64} %drop.s.178)
  br label %drop.skip.181
drop.skip.181:
  %drop.lv.182 = load {ptr, i64, i64, i64, i64}, ptr %t4.a.19
  %drop.lp.183 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.182, 0
  %drop.lnull.184 = icmp eq ptr %drop.lp.183, null
  br i1 %drop.lnull.184, label %drop.lskip.185, label %drop.lcheck.185
drop.lcheck.185:
  call void @__mn_list_free(ptr %t4.a.19)
  br label %drop.lskip.185
drop.lskip.185:
  %drop.lv.186 = load {ptr, i64, i64, i64, i64}, ptr %t9.a.39
  %drop.lp.187 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.186, 0
  %drop.lnull.188 = icmp eq ptr %drop.lp.187, null
  br i1 %drop.lnull.188, label %drop.lskip.189, label %drop.lcheck.189
drop.lcheck.189:
  call void @__mn_list_free(ptr %t9.a.39)
  br label %drop.lskip.189
drop.lskip.189:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
