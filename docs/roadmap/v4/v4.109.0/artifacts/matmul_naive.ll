; ModuleID = 'matmul_naive'
source_filename = "matmul_naive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"checksum = ", align 8

declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind willreturn
declare void @__mn_list_push(ptr, ptr) nounwind
declare ptr @__mn_list_get(ptr, i64) nounwind
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_list_free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() nounwind willreturn {
pre_entry:
  %n.a.0 = alloca i64, align 8
  store i64 0, ptr %n.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.3 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t2.a.3
  %a.a.5 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %a.a.5
  %t3.a.7 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t3.a.7
  %b.a.9 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %b.a.9
  %t4.a.11 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t4.a.11
  %c.a.13 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %c.a.13
  %t5.a.14 = alloca i64, align 8
  store i64 0, ptr %t5.a.14
  %idx.a.16 = alloca i64, align 8
  store i64 0, ptr %idx.a.16
  %t6.a.20 = alloca i1, align 8
  store i1 0, ptr %t6.a.20
  %t7.a.22 = alloca i64, align 8
  store i64 0, ptr %t7.a.22
  %t8.a.26 = alloca i64, align 8
  store i64 0, ptr %t8.a.26
  %t9.a.27 = alloca i64, align 8
  store i64 0, ptr %t9.a.27
  %t10.a.31 = alloca i64, align 8
  store i64 0, ptr %t10.a.31
  %t11.a.32 = alloca i64, align 8
  store i64 0, ptr %t11.a.32
  %t12.a.36 = alloca i64, align 8
  store i64 0, ptr %t12.a.36
  %ea.38 = alloca i64, align 8
  %t13.a.40 = alloca i64, align 8
  store i64 0, ptr %t13.a.40
  %t14.a.44 = alloca i64, align 8
  store i64 0, ptr %t14.a.44
  %t15.a.45 = alloca i64, align 8
  store i64 0, ptr %t15.a.45
  %t16.a.49 = alloca i64, align 8
  store i64 0, ptr %t16.a.49
  %t17.a.50 = alloca i64, align 8
  store i64 0, ptr %t17.a.50
  %t18.a.54 = alloca i64, align 8
  store i64 0, ptr %t18.a.54
  %ea.56 = alloca i64, align 8
  %t19.a.58 = alloca i64, align 8
  store i64 0, ptr %t19.a.58
  %ea.60 = alloca i64, align 8
  %t20.a.62 = alloca i64, align 8
  store i64 0, ptr %t20.a.62
  %t21.a.66 = alloca i64, align 8
  store i64 0, ptr %t21.a.66
  %t22.a.68 = alloca i64, align 8
  store i64 0, ptr %t22.a.68
  %i.a.70 = alloca i64, align 8
  store i64 0, ptr %i.a.70
  %t23.a.74 = alloca i1, align 8
  store i1 0, ptr %t23.a.74
  %t24.a.76 = alloca i64, align 8
  store i64 0, ptr %t24.a.76
  %j.a.78 = alloca i64, align 8
  store i64 0, ptr %j.a.78
  %t45.a.79 = alloca i64, align 8
  store i64 0, ptr %t45.a.79
  %lp.82 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t46.a.84 = alloca ptr, align 8
  store ptr null, ptr %t46.a.84
  %t48.a.85 = alloca i64, align 8
  store i64 0, ptr %t48.a.85
  %lp.88 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t49.a.90 = alloca ptr, align 8
  store ptr null, ptr %t49.a.90
  %t50.a.96 = alloca i64, align 8
  store i64 0, ptr %t50.a.96
  %t53.a.97 = alloca i64, align 8
  store i64 0, ptr %t53.a.97
  %lp.100 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t54.a.102 = alloca ptr, align 8
  store ptr null, ptr %t54.a.102
  %t55.a.107 = alloca i64, align 8
  store i64 0, ptr %t55.a.107
  %t57.a.108 = alloca i64, align 8
  store i64 0, ptr %t57.a.108
  %lp.111 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t58.a.113 = alloca ptr, align 8
  store ptr null, ptr %t58.a.113
  %t59.a.118 = alloca i64, align 8
  store i64 0, ptr %t59.a.118
  %t60.a.122 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t60.a.122
  %str_track.125 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.125
  %t61.a.126 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t61.a.126
  %str_track.130 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.130
  %t62.a.131 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t62.a.131
  %t63.a.133 = alloca i1, align 8
  store i1 0, ptr %t63.a.133
  %t25.a.157 = alloca i1, align 8
  store i1 0, ptr %t25.a.157
  %t26.a.159 = alloca i64, align 8
  store i64 0, ptr %t26.a.159
  %sum.a.161 = alloca i64, align 8
  store i64 0, ptr %sum.a.161
  %t27.a.162 = alloca i64, align 8
  store i64 0, ptr %t27.a.162
  %k.a.164 = alloca i64, align 8
  store i64 0, ptr %k.a.164
  %t43.a.165 = alloca i64, align 8
  store i64 0, ptr %t43.a.165
  %t44.a.169 = alloca i64, align 8
  store i64 0, ptr %t44.a.169
  %t28.a.174 = alloca i1, align 8
  store i1 0, ptr %t28.a.174
  %t29.a.179 = alloca i64, align 8
  store i64 0, ptr %t29.a.179
  %t30.a.183 = alloca i64, align 8
  store i64 0, ptr %t30.a.183
  %lp.186 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t31.a.188 = alloca ptr, align 8
  store ptr null, ptr %t31.a.188
  %t32.a.192 = alloca i64, align 8
  store i64 0, ptr %t32.a.192
  %t33.a.196 = alloca i64, align 8
  store i64 0, ptr %t33.a.196
  %lp.199 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t34.a.201 = alloca ptr, align 8
  store ptr null, ptr %t34.a.201
  %t35.a.207 = alloca i64, align 8
  store i64 0, ptr %t35.a.207
  %t36.a.211 = alloca i64, align 8
  store i64 0, ptr %t36.a.211
  %t37.a.213 = alloca i64, align 8
  store i64 0, ptr %t37.a.213
  %t38.a.217 = alloca i64, align 8
  store i64 0, ptr %t38.a.217
  %t39.a.222 = alloca i64, align 8
  store i64 0, ptr %t39.a.222
  %t40.a.226 = alloca i64, align 8
  store i64 0, ptr %t40.a.226
  %lp.230 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t41.a.232 = alloca i64, align 8
  store i64 0, ptr %t41.a.232
  %t42.a.236 = alloca i64, align 8
  store i64 0, ptr %t42.a.236
  br label %entry
entry:
  store i64 64, ptr %n.a.0
  store i64 4096, ptr %t1.a.1
  %ln.2 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.2, ptr %t2.a.3
  %l.4 = load {ptr, i64, i64, i64, i64}, ptr %t2.a.3
  store {ptr, i64, i64, i64, i64} %l.4, ptr %a.a.5
  %ln.6 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.6, ptr %t3.a.7
  %l.8 = load {ptr, i64, i64, i64, i64}, ptr %t3.a.7
  store {ptr, i64, i64, i64, i64} %l.8, ptr %b.a.9
  %ln.10 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.10, ptr %t4.a.11
  %l.12 = load {ptr, i64, i64, i64, i64}, ptr %t4.a.11
  store {ptr, i64, i64, i64, i64} %l.12, ptr %c.a.13
  store i64 0, ptr %t5.a.14
  %l.15 = load i64, ptr %t5.a.14
  store i64 %l.15, ptr %idx.a.16
  br label %while_header0
while_header0:
  %l.17 = load i64, ptr %idx.a.16
  %l.18 = load i64, ptr %t1.a.1
  %i.19 = icmp slt i64 %l.17, %l.18
  store i1 %i.19, ptr %t6.a.20
  %l.21 = load i1, ptr %t6.a.20
  br i1 %l.21, label %while_body1, label %while_exit2
while_body1:
  store i64 3, ptr %t7.a.22
  %l.23 = load i64, ptr %idx.a.16
  %l.24 = load i64, ptr %t7.a.22
  %i.25 = mul nsw i64 %l.23, %l.24
  store i64 %i.25, ptr %t8.a.26
  store i64 7, ptr %t9.a.27
  %l.28 = load i64, ptr %t8.a.26
  %l.29 = load i64, ptr %t9.a.27
  %i.30 = add nsw i64 %l.28, %l.29
  store i64 %i.30, ptr %t10.a.31
  store i64 100, ptr %t11.a.32
  %l.33 = load i64, ptr %t10.a.31
  %l.34 = load i64, ptr %t11.a.32
  %i.35 = srem i64 %l.33, %l.34
  store i64 %i.35, ptr %t12.a.36
  %l.37 = load i64, ptr %t12.a.36
  store i64 %l.37, ptr %ea.38
  call void @__mn_list_push(ptr %t2.a.3, ptr %ea.38)
  %ul.39 = load {ptr, i64, i64, i64, i64}, ptr %t2.a.3
  store {ptr, i64, i64, i64, i64} %ul.39, ptr %a.a.5
  store i64 5, ptr %t13.a.40
  %l.41 = load i64, ptr %idx.a.16
  %l.42 = load i64, ptr %t13.a.40
  %i.43 = mul nsw i64 %l.41, %l.42
  store i64 %i.43, ptr %t14.a.44
  store i64 13, ptr %t15.a.45
  %l.46 = load i64, ptr %t14.a.44
  %l.47 = load i64, ptr %t15.a.45
  %i.48 = add nsw i64 %l.46, %l.47
  store i64 %i.48, ptr %t16.a.49
  store i64 100, ptr %t17.a.50
  %l.51 = load i64, ptr %t16.a.49
  %l.52 = load i64, ptr %t17.a.50
  %i.53 = srem i64 %l.51, %l.52
  store i64 %i.53, ptr %t18.a.54
  %l.55 = load i64, ptr %t18.a.54
  store i64 %l.55, ptr %ea.56
  call void @__mn_list_push(ptr %t3.a.7, ptr %ea.56)
  %ul.57 = load {ptr, i64, i64, i64, i64}, ptr %t3.a.7
  store {ptr, i64, i64, i64, i64} %ul.57, ptr %b.a.9
  store i64 0, ptr %t19.a.58
  %l.59 = load i64, ptr %t19.a.58
  store i64 %l.59, ptr %ea.60
  call void @__mn_list_push(ptr %t4.a.11, ptr %ea.60)
  %ul.61 = load {ptr, i64, i64, i64, i64}, ptr %t4.a.11
  store {ptr, i64, i64, i64, i64} %ul.61, ptr %c.a.13
  store i64 1, ptr %t20.a.62
  %l.63 = load i64, ptr %idx.a.16
  %l.64 = load i64, ptr %t20.a.62
  %i.65 = add nsw i64 %l.63, %l.64
  store i64 %i.65, ptr %t21.a.66
  %l.67 = load i64, ptr %t21.a.66
  store i64 %l.67, ptr %idx.a.16
  br label %while_header0
while_exit2:
  store i64 0, ptr %t22.a.68
  %l.69 = load i64, ptr %t22.a.68
  store i64 %l.69, ptr %i.a.70
  br label %while_header3
while_header3:
  %l.71 = load i64, ptr %i.a.70
  %l.72 = load i64, ptr %n.a.0
  %i.73 = icmp slt i64 %l.71, %l.72
  store i1 %i.73, ptr %t23.a.74
  %l.75 = load i1, ptr %t23.a.74
  br i1 %l.75, label %while_body4, label %while_exit5
while_body4:
  store i64 0, ptr %t24.a.76
  %l.77 = load i64, ptr %t24.a.76
  store i64 %l.77, ptr %j.a.78
  br label %while_header6
while_exit5:
  store i64 0, ptr %t45.a.79
  %l.80 = load {ptr, i64, i64, i64, i64}, ptr %c.a.13
  %l.81 = load i64, ptr %t45.a.79
  store {ptr, i64, i64, i64, i64} %l.80, ptr %lp.82
  %rt.83 = call ptr @__mn_list_get(ptr %lp.82, i64 %l.81)
  store ptr %rt.83, ptr %t46.a.84
  store i64 63, ptr %t48.a.85
  %l.86 = load {ptr, i64, i64, i64, i64}, ptr %c.a.13
  %l.87 = load i64, ptr %t48.a.85
  store {ptr, i64, i64, i64, i64} %l.86, ptr %lp.88
  %rt.89 = call ptr @__mn_list_get(ptr %lp.88, i64 %l.87)
  store ptr %rt.89, ptr %t49.a.90
  %l.91 = load ptr, ptr %t46.a.84
  %l.92 = load ptr, ptr %t49.a.90
  %p2i.93 = ptrtoint ptr %l.91 to i64
  %p2i.94 = ptrtoint ptr %l.92 to i64
  %i.95 = add nsw i64 %p2i.93, %p2i.94
  store i64 %i.95, ptr %t50.a.96
  store i64 4032, ptr %t53.a.97
  %l.98 = load {ptr, i64, i64, i64, i64}, ptr %c.a.13
  %l.99 = load i64, ptr %t53.a.97
  store {ptr, i64, i64, i64, i64} %l.98, ptr %lp.100
  %rt.101 = call ptr @__mn_list_get(ptr %lp.100, i64 %l.99)
  store ptr %rt.101, ptr %t54.a.102
  %l.103 = load i64, ptr %t50.a.96
  %l.104 = load ptr, ptr %t54.a.102
  %p2i.105 = ptrtoint ptr %l.104 to i64
  %i.106 = add nsw i64 %l.103, %p2i.105
  store i64 %i.106, ptr %t55.a.107
  store i64 4095, ptr %t57.a.108
  %l.109 = load {ptr, i64, i64, i64, i64}, ptr %c.a.13
  %l.110 = load i64, ptr %t57.a.108
  store {ptr, i64, i64, i64, i64} %l.109, ptr %lp.111
  %rt.112 = call ptr @__mn_list_get(ptr %lp.111, i64 %l.110)
  store ptr %rt.112, ptr %t58.a.113
  %l.114 = load i64, ptr %t55.a.107
  %l.115 = load ptr, ptr %t58.a.113
  %p2i.116 = ptrtoint ptr %l.115 to i64
  %i.117 = add nsw i64 %l.114, %p2i.116
  store i64 %i.117, ptr %t59.a.118
  %sp.119 = getelementptr inbounds [11 x i8], ptr @.str.0, i64 0, i64 0
  %s.120 = insertvalue {ptr, i64} undef, ptr %sp.119, 0
  %s.121 = insertvalue {ptr, i64} %s.120, i64 11, 1
  store {ptr, i64} %s.121, ptr %t60.a.122
  %l.123 = load i64, ptr %t59.a.118
  %rt.124 = call {ptr, i64} @__mn_str_from_int(i64 %l.123)
  store {ptr, i64} %rt.124, ptr %str_track.125
  store {ptr, i64} %rt.124, ptr %t61.a.126
  %l.127 = load {ptr, i64}, ptr %t60.a.122
  %l.128 = load {ptr, i64}, ptr %t61.a.126
  %rt.129 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.127, {ptr, i64} %l.128)
  store {ptr, i64} %rt.129, ptr %str_track.130
  store {ptr, i64} %rt.129, ptr %t62.a.131
  %l.132 = load {ptr, i64}, ptr %t62.a.131
  call void @__mn_str_println({ptr, i64} %l.132)
  store i1 0, ptr %t63.a.133
  %drop.s.134 = load {ptr, i64}, ptr %str_track.125
  %drop.p.135 = extractvalue {ptr, i64} %drop.s.134, 0
  %drop.null.136 = icmp eq ptr %drop.p.135, null
  br i1 %drop.null.136, label %drop.skip.137, label %drop.check.137
while_header6:
  %l.154 = load i64, ptr %j.a.78
  %l.155 = load i64, ptr %n.a.0
  %i.156 = icmp slt i64 %l.154, %l.155
  store i1 %i.156, ptr %t25.a.157
  %l.158 = load i1, ptr %t25.a.157
  br i1 %l.158, label %while_body7, label %while_exit8
while_body7:
  store i64 0, ptr %t26.a.159
  %l.160 = load i64, ptr %t26.a.159
  store i64 %l.160, ptr %sum.a.161
  store i64 0, ptr %t27.a.162
  %l.163 = load i64, ptr %t27.a.162
  store i64 %l.163, ptr %k.a.164
  br label %while_header9
while_exit8:
  store i64 1, ptr %t43.a.165
  %l.166 = load i64, ptr %i.a.70
  %l.167 = load i64, ptr %t43.a.165
  %i.168 = add nsw i64 %l.166, %l.167
  store i64 %i.168, ptr %t44.a.169
  %l.170 = load i64, ptr %t44.a.169
  store i64 %l.170, ptr %i.a.70
  br label %while_header3
while_header9:
  %l.171 = load i64, ptr %k.a.164
  %l.172 = load i64, ptr %n.a.0
  %i.173 = icmp slt i64 %l.171, %l.172
  store i1 %i.173, ptr %t28.a.174
  %l.175 = load i1, ptr %t28.a.174
  br i1 %l.175, label %while_body10, label %while_exit11
while_body10:
  %l.176 = load i64, ptr %i.a.70
  %l.177 = load i64, ptr %n.a.0
  %i.178 = mul nsw i64 %l.176, %l.177
  store i64 %i.178, ptr %t29.a.179
  %l.180 = load i64, ptr %t29.a.179
  %l.181 = load i64, ptr %k.a.164
  %i.182 = add nsw i64 %l.180, %l.181
  store i64 %i.182, ptr %t30.a.183
  %l.184 = load {ptr, i64, i64, i64, i64}, ptr %a.a.5
  %l.185 = load i64, ptr %t30.a.183
  store {ptr, i64, i64, i64, i64} %l.184, ptr %lp.186
  %rt.187 = call ptr @__mn_list_get(ptr %lp.186, i64 %l.185)
  store ptr %rt.187, ptr %t31.a.188
  %l.189 = load i64, ptr %k.a.164
  %l.190 = load i64, ptr %n.a.0
  %i.191 = mul nsw i64 %l.189, %l.190
  store i64 %i.191, ptr %t32.a.192
  %l.193 = load i64, ptr %t32.a.192
  %l.194 = load i64, ptr %j.a.78
  %i.195 = add nsw i64 %l.193, %l.194
  store i64 %i.195, ptr %t33.a.196
  %l.197 = load {ptr, i64, i64, i64, i64}, ptr %b.a.9
  %l.198 = load i64, ptr %t33.a.196
  store {ptr, i64, i64, i64, i64} %l.197, ptr %lp.199
  %rt.200 = call ptr @__mn_list_get(ptr %lp.199, i64 %l.198)
  store ptr %rt.200, ptr %t34.a.201
  %l.202 = load ptr, ptr %t31.a.188
  %l.203 = load ptr, ptr %t34.a.201
  %p2i.204 = ptrtoint ptr %l.202 to i64
  %p2i.205 = ptrtoint ptr %l.203 to i64
  %i.206 = mul nsw i64 %p2i.204, %p2i.205
  store i64 %i.206, ptr %t35.a.207
  %l.208 = load i64, ptr %sum.a.161
  %l.209 = load i64, ptr %t35.a.207
  %i.210 = add nsw i64 %l.208, %l.209
  store i64 %i.210, ptr %t36.a.211
  %l.212 = load i64, ptr %t36.a.211
  store i64 %l.212, ptr %sum.a.161
  store i64 1, ptr %t37.a.213
  %l.214 = load i64, ptr %k.a.164
  %l.215 = load i64, ptr %t37.a.213
  %i.216 = add nsw i64 %l.214, %l.215
  store i64 %i.216, ptr %t38.a.217
  %l.218 = load i64, ptr %t38.a.217
  store i64 %l.218, ptr %k.a.164
  br label %while_header9
while_exit11:
  %l.219 = load i64, ptr %i.a.70
  %l.220 = load i64, ptr %n.a.0
  %i.221 = mul nsw i64 %l.219, %l.220
  store i64 %i.221, ptr %t39.a.222
  %l.223 = load i64, ptr %t39.a.222
  %l.224 = load i64, ptr %j.a.78
  %i.225 = add nsw i64 %l.223, %l.224
  store i64 %i.225, ptr %t40.a.226
  %l.227 = load {ptr, i64, i64, i64, i64}, ptr %c.a.13
  %l.228 = load i64, ptr %t40.a.226
  %l.229 = load i64, ptr %sum.a.161
  store {ptr, i64, i64, i64, i64} %l.227, ptr %lp.230
  %rt.231 = call ptr @__mn_list_get(ptr %lp.230, i64 %l.228)
  store i64 %l.229, ptr %rt.231
  store i64 1, ptr %t41.a.232
  %l.233 = load i64, ptr %j.a.78
  %l.234 = load i64, ptr %t41.a.232
  %i.235 = add nsw i64 %l.233, %l.234
  store i64 %i.235, ptr %t42.a.236
  %l.237 = load i64, ptr %t42.a.236
  store i64 %l.237, ptr %j.a.78
  br label %while_header6
drop.check.137:
  call void @__mn_str_free({ptr, i64} %drop.s.134)
  br label %drop.skip.137
drop.skip.137:
  %drop.s.138 = load {ptr, i64}, ptr %str_track.130
  %drop.p.139 = extractvalue {ptr, i64} %drop.s.138, 0
  %drop.null.140 = icmp eq ptr %drop.p.139, null
  br i1 %drop.null.140, label %drop.skip.141, label %drop.check.141
drop.check.141:
  call void @__mn_str_free({ptr, i64} %drop.s.138)
  br label %drop.skip.141
drop.skip.141:
  %drop.lv.142 = load {ptr, i64, i64, i64, i64}, ptr %a.a.5
  %drop.lp.143 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.142, 0
  %drop.lnull.144 = icmp eq ptr %drop.lp.143, null
  br i1 %drop.lnull.144, label %drop.lskip.145, label %drop.lcheck.145
drop.lcheck.145:
  call void @__mn_list_free(ptr %a.a.5)
  br label %drop.lskip.145
drop.lskip.145:
  %drop.lv.146 = load {ptr, i64, i64, i64, i64}, ptr %b.a.9
  %drop.lp.147 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.146, 0
  %drop.lnull.148 = icmp eq ptr %drop.lp.147, null
  br i1 %drop.lnull.148, label %drop.lskip.149, label %drop.lcheck.149
drop.lcheck.149:
  call void @__mn_list_free(ptr %b.a.9)
  br label %drop.lskip.149
drop.lskip.149:
  %drop.lv.150 = load {ptr, i64, i64, i64, i64}, ptr %c.a.13
  %drop.lp.151 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.150, 0
  %drop.lnull.152 = icmp eq ptr %drop.lp.151, null
  br i1 %drop.lnull.152, label %drop.lskip.153, label %drop.lcheck.153
drop.lcheck.153:
  call void @__mn_list_free(ptr %c.a.13)
  br label %drop.lskip.153
drop.lskip.153:
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
