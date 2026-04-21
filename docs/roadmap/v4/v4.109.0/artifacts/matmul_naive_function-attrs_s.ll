; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/matmul_naive_stripped.bc'
source_filename = "matmul_naive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"checksum = ", align 8

declare { ptr, i64, i64, i64, i64 } @__mn_list_new(i64)

declare void @__mn_list_push(ptr, ptr)

declare ptr @__mn_list_get(ptr, i64)

declare { ptr, i64 } @__mn_str_from_int(i64)

declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 })

declare void @__mn_str_println({ ptr, i64 })

declare void @__mn_str_free({ ptr, i64 })

declare void @free(ptr)

declare void @__mn_list_free(ptr)

declare void @__mn_intern_destroy()

define noundef i64 @main() {
pre_entry:
  %n.a.0 = alloca i64, align 8
  store i64 0, ptr %n.a.0, align 8
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1, align 8
  %t2.a.3 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store { ptr, i64, i64, i64, i64 } zeroinitializer, ptr %t2.a.3, align 8
  %a.a.5 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store { ptr, i64, i64, i64, i64 } zeroinitializer, ptr %a.a.5, align 8
  %t3.a.7 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store { ptr, i64, i64, i64, i64 } zeroinitializer, ptr %t3.a.7, align 8
  %b.a.9 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store { ptr, i64, i64, i64, i64 } zeroinitializer, ptr %b.a.9, align 8
  %t4.a.11 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store { ptr, i64, i64, i64, i64 } zeroinitializer, ptr %t4.a.11, align 8
  %c.a.13 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store { ptr, i64, i64, i64, i64 } zeroinitializer, ptr %c.a.13, align 8
  %t5.a.14 = alloca i64, align 8
  store i64 0, ptr %t5.a.14, align 8
  %idx.a.16 = alloca i64, align 8
  store i64 0, ptr %idx.a.16, align 8
  %t6.a.20 = alloca i1, align 8
  store i1 false, ptr %t6.a.20, align 1
  %t7.a.22 = alloca i64, align 8
  store i64 0, ptr %t7.a.22, align 8
  %t8.a.26 = alloca i64, align 8
  store i64 0, ptr %t8.a.26, align 8
  %t9.a.27 = alloca i64, align 8
  store i64 0, ptr %t9.a.27, align 8
  %t10.a.31 = alloca i64, align 8
  store i64 0, ptr %t10.a.31, align 8
  %t11.a.32 = alloca i64, align 8
  store i64 0, ptr %t11.a.32, align 8
  %t12.a.36 = alloca i64, align 8
  store i64 0, ptr %t12.a.36, align 8
  %ea.38 = alloca i64, align 8
  %t13.a.40 = alloca i64, align 8
  store i64 0, ptr %t13.a.40, align 8
  %t14.a.44 = alloca i64, align 8
  store i64 0, ptr %t14.a.44, align 8
  %t15.a.45 = alloca i64, align 8
  store i64 0, ptr %t15.a.45, align 8
  %t16.a.49 = alloca i64, align 8
  store i64 0, ptr %t16.a.49, align 8
  %t17.a.50 = alloca i64, align 8
  store i64 0, ptr %t17.a.50, align 8
  %t18.a.54 = alloca i64, align 8
  store i64 0, ptr %t18.a.54, align 8
  %ea.56 = alloca i64, align 8
  %t19.a.58 = alloca i64, align 8
  store i64 0, ptr %t19.a.58, align 8
  %ea.60 = alloca i64, align 8
  %t20.a.62 = alloca i64, align 8
  store i64 0, ptr %t20.a.62, align 8
  %t21.a.66 = alloca i64, align 8
  store i64 0, ptr %t21.a.66, align 8
  %t22.a.68 = alloca i64, align 8
  store i64 0, ptr %t22.a.68, align 8
  %i.a.70 = alloca i64, align 8
  store i64 0, ptr %i.a.70, align 8
  %t23.a.74 = alloca i1, align 8
  store i1 false, ptr %t23.a.74, align 1
  %t24.a.76 = alloca i64, align 8
  store i64 0, ptr %t24.a.76, align 8
  %j.a.78 = alloca i64, align 8
  store i64 0, ptr %j.a.78, align 8
  %t45.a.79 = alloca i64, align 8
  store i64 0, ptr %t45.a.79, align 8
  %lp.82 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t46.a.84 = alloca ptr, align 8
  store ptr null, ptr %t46.a.84, align 8
  %t48.a.85 = alloca i64, align 8
  store i64 0, ptr %t48.a.85, align 8
  %lp.88 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t49.a.90 = alloca ptr, align 8
  store ptr null, ptr %t49.a.90, align 8
  %t50.a.96 = alloca i64, align 8
  store i64 0, ptr %t50.a.96, align 8
  %t53.a.97 = alloca i64, align 8
  store i64 0, ptr %t53.a.97, align 8
  %lp.100 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t54.a.102 = alloca ptr, align 8
  store ptr null, ptr %t54.a.102, align 8
  %t55.a.107 = alloca i64, align 8
  store i64 0, ptr %t55.a.107, align 8
  %t57.a.108 = alloca i64, align 8
  store i64 0, ptr %t57.a.108, align 8
  %lp.111 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t58.a.113 = alloca ptr, align 8
  store ptr null, ptr %t58.a.113, align 8
  %t59.a.118 = alloca i64, align 8
  store i64 0, ptr %t59.a.118, align 8
  %t60.a.122 = alloca { ptr, i64 }, align 8
  store { ptr, i64 } zeroinitializer, ptr %t60.a.122, align 8
  %str_track.125 = alloca { ptr, i64 }, align 8
  store { ptr, i64 } zeroinitializer, ptr %str_track.125, align 8
  %t61.a.126 = alloca { ptr, i64 }, align 8
  store { ptr, i64 } zeroinitializer, ptr %t61.a.126, align 8
  %str_track.130 = alloca { ptr, i64 }, align 8
  store { ptr, i64 } zeroinitializer, ptr %str_track.130, align 8
  %t62.a.131 = alloca { ptr, i64 }, align 8
  store { ptr, i64 } zeroinitializer, ptr %t62.a.131, align 8
  %t63.a.133 = alloca i1, align 8
  store i1 false, ptr %t63.a.133, align 1
  %t25.a.157 = alloca i1, align 8
  store i1 false, ptr %t25.a.157, align 1
  %t26.a.159 = alloca i64, align 8
  store i64 0, ptr %t26.a.159, align 8
  %sum.a.161 = alloca i64, align 8
  store i64 0, ptr %sum.a.161, align 8
  %t27.a.162 = alloca i64, align 8
  store i64 0, ptr %t27.a.162, align 8
  %k.a.164 = alloca i64, align 8
  store i64 0, ptr %k.a.164, align 8
  %t43.a.165 = alloca i64, align 8
  store i64 0, ptr %t43.a.165, align 8
  %t44.a.169 = alloca i64, align 8
  store i64 0, ptr %t44.a.169, align 8
  %t28.a.174 = alloca i1, align 8
  store i1 false, ptr %t28.a.174, align 1
  %t29.a.179 = alloca i64, align 8
  store i64 0, ptr %t29.a.179, align 8
  %t30.a.183 = alloca i64, align 8
  store i64 0, ptr %t30.a.183, align 8
  %lp.186 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t31.a.188 = alloca ptr, align 8
  store ptr null, ptr %t31.a.188, align 8
  %t32.a.192 = alloca i64, align 8
  store i64 0, ptr %t32.a.192, align 8
  %t33.a.196 = alloca i64, align 8
  store i64 0, ptr %t33.a.196, align 8
  %lp.199 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t34.a.201 = alloca ptr, align 8
  store ptr null, ptr %t34.a.201, align 8
  %t35.a.207 = alloca i64, align 8
  store i64 0, ptr %t35.a.207, align 8
  %t36.a.211 = alloca i64, align 8
  store i64 0, ptr %t36.a.211, align 8
  %t37.a.213 = alloca i64, align 8
  store i64 0, ptr %t37.a.213, align 8
  %t38.a.217 = alloca i64, align 8
  store i64 0, ptr %t38.a.217, align 8
  %t39.a.222 = alloca i64, align 8
  store i64 0, ptr %t39.a.222, align 8
  %t40.a.226 = alloca i64, align 8
  store i64 0, ptr %t40.a.226, align 8
  %lp.230 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t41.a.232 = alloca i64, align 8
  store i64 0, ptr %t41.a.232, align 8
  %t42.a.236 = alloca i64, align 8
  store i64 0, ptr %t42.a.236, align 8
  br label %entry

entry:                                            ; preds = %pre_entry
  store i64 64, ptr %n.a.0, align 8
  store i64 4096, ptr %t1.a.1, align 8
  %ln.2 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  store { ptr, i64, i64, i64, i64 } %ln.2, ptr %t2.a.3, align 8
  %l.4 = load { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, align 8
  store { ptr, i64, i64, i64, i64 } %l.4, ptr %a.a.5, align 8
  %ln.6 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  store { ptr, i64, i64, i64, i64 } %ln.6, ptr %t3.a.7, align 8
  %l.8 = load { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, align 8
  store { ptr, i64, i64, i64, i64 } %l.8, ptr %b.a.9, align 8
  %ln.10 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  store { ptr, i64, i64, i64, i64 } %ln.10, ptr %t4.a.11, align 8
  %l.12 = load { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, align 8
  store { ptr, i64, i64, i64, i64 } %l.12, ptr %c.a.13, align 8
  store i64 0, ptr %t5.a.14, align 8
  %l.15 = load i64, ptr %t5.a.14, align 8
  store i64 %l.15, ptr %idx.a.16, align 8
  br label %while_header0

while_header0:                                    ; preds = %while_body1, %entry
  %l.17 = load i64, ptr %idx.a.16, align 8
  %l.18 = load i64, ptr %t1.a.1, align 8
  %i.19 = icmp slt i64 %l.17, %l.18
  store i1 %i.19, ptr %t6.a.20, align 1
  %l.21 = load i1, ptr %t6.a.20, align 1
  br i1 %l.21, label %while_body1, label %while_exit2

while_body1:                                      ; preds = %while_header0
  store i64 3, ptr %t7.a.22, align 8
  %l.23 = load i64, ptr %idx.a.16, align 8
  %l.24 = load i64, ptr %t7.a.22, align 8
  %i.25 = mul i64 %l.23, %l.24
  store i64 %i.25, ptr %t8.a.26, align 8
  store i64 7, ptr %t9.a.27, align 8
  %l.28 = load i64, ptr %t8.a.26, align 8
  %l.29 = load i64, ptr %t9.a.27, align 8
  %i.30 = add i64 %l.28, %l.29
  store i64 %i.30, ptr %t10.a.31, align 8
  store i64 100, ptr %t11.a.32, align 8
  %l.33 = load i64, ptr %t10.a.31, align 8
  %l.34 = load i64, ptr %t11.a.32, align 8
  %i.35 = srem i64 %l.33, %l.34
  store i64 %i.35, ptr %t12.a.36, align 8
  %l.37 = load i64, ptr %t12.a.36, align 8
  store i64 %l.37, ptr %ea.38, align 8
  call void @__mn_list_push(ptr %t2.a.3, ptr %ea.38)
  %ul.39 = load { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, align 8
  store { ptr, i64, i64, i64, i64 } %ul.39, ptr %a.a.5, align 8
  store i64 5, ptr %t13.a.40, align 8
  %l.41 = load i64, ptr %idx.a.16, align 8
  %l.42 = load i64, ptr %t13.a.40, align 8
  %i.43 = mul i64 %l.41, %l.42
  store i64 %i.43, ptr %t14.a.44, align 8
  store i64 13, ptr %t15.a.45, align 8
  %l.46 = load i64, ptr %t14.a.44, align 8
  %l.47 = load i64, ptr %t15.a.45, align 8
  %i.48 = add i64 %l.46, %l.47
  store i64 %i.48, ptr %t16.a.49, align 8
  store i64 100, ptr %t17.a.50, align 8
  %l.51 = load i64, ptr %t16.a.49, align 8
  %l.52 = load i64, ptr %t17.a.50, align 8
  %i.53 = srem i64 %l.51, %l.52
  store i64 %i.53, ptr %t18.a.54, align 8
  %l.55 = load i64, ptr %t18.a.54, align 8
  store i64 %l.55, ptr %ea.56, align 8
  call void @__mn_list_push(ptr %t3.a.7, ptr %ea.56)
  %ul.57 = load { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, align 8
  store { ptr, i64, i64, i64, i64 } %ul.57, ptr %b.a.9, align 8
  store i64 0, ptr %t19.a.58, align 8
  %l.59 = load i64, ptr %t19.a.58, align 8
  store i64 %l.59, ptr %ea.60, align 8
  call void @__mn_list_push(ptr %t4.a.11, ptr %ea.60)
  %ul.61 = load { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, align 8
  store { ptr, i64, i64, i64, i64 } %ul.61, ptr %c.a.13, align 8
  store i64 1, ptr %t20.a.62, align 8
  %l.63 = load i64, ptr %idx.a.16, align 8
  %l.64 = load i64, ptr %t20.a.62, align 8
  %i.65 = add i64 %l.63, %l.64
  store i64 %i.65, ptr %t21.a.66, align 8
  %l.67 = load i64, ptr %t21.a.66, align 8
  store i64 %l.67, ptr %idx.a.16, align 8
  br label %while_header0

while_exit2:                                      ; preds = %while_header0
  store i64 0, ptr %t22.a.68, align 8
  %l.69 = load i64, ptr %t22.a.68, align 8
  store i64 %l.69, ptr %i.a.70, align 8
  br label %while_header3

while_header3:                                    ; preds = %while_exit8, %while_exit2
  %l.71 = load i64, ptr %i.a.70, align 8
  %l.72 = load i64, ptr %n.a.0, align 8
  %i.73 = icmp slt i64 %l.71, %l.72
  store i1 %i.73, ptr %t23.a.74, align 1
  %l.75 = load i1, ptr %t23.a.74, align 1
  br i1 %l.75, label %while_body4, label %while_exit5

while_body4:                                      ; preds = %while_header3
  store i64 0, ptr %t24.a.76, align 8
  %l.77 = load i64, ptr %t24.a.76, align 8
  store i64 %l.77, ptr %j.a.78, align 8
  br label %while_header6

while_exit5:                                      ; preds = %while_header3
  store i64 0, ptr %t45.a.79, align 8
  %l.80 = load { ptr, i64, i64, i64, i64 }, ptr %c.a.13, align 8
  %l.81 = load i64, ptr %t45.a.79, align 8
  store { ptr, i64, i64, i64, i64 } %l.80, ptr %lp.82, align 8
  %rt.83 = call ptr @__mn_list_get(ptr %lp.82, i64 %l.81)
  store ptr %rt.83, ptr %t46.a.84, align 8
  store i64 63, ptr %t48.a.85, align 8
  %l.86 = load { ptr, i64, i64, i64, i64 }, ptr %c.a.13, align 8
  %l.87 = load i64, ptr %t48.a.85, align 8
  store { ptr, i64, i64, i64, i64 } %l.86, ptr %lp.88, align 8
  %rt.89 = call ptr @__mn_list_get(ptr %lp.88, i64 %l.87)
  store ptr %rt.89, ptr %t49.a.90, align 8
  %l.91 = load ptr, ptr %t46.a.84, align 8
  %l.92 = load ptr, ptr %t49.a.90, align 8
  %p2i.93 = ptrtoint ptr %l.91 to i64
  %p2i.94 = ptrtoint ptr %l.92 to i64
  %i.95 = add i64 %p2i.93, %p2i.94
  store i64 %i.95, ptr %t50.a.96, align 8
  store i64 4032, ptr %t53.a.97, align 8
  %l.98 = load { ptr, i64, i64, i64, i64 }, ptr %c.a.13, align 8
  %l.99 = load i64, ptr %t53.a.97, align 8
  store { ptr, i64, i64, i64, i64 } %l.98, ptr %lp.100, align 8
  %rt.101 = call ptr @__mn_list_get(ptr %lp.100, i64 %l.99)
  store ptr %rt.101, ptr %t54.a.102, align 8
  %l.103 = load i64, ptr %t50.a.96, align 8
  %l.104 = load ptr, ptr %t54.a.102, align 8
  %p2i.105 = ptrtoint ptr %l.104 to i64
  %i.106 = add i64 %l.103, %p2i.105
  store i64 %i.106, ptr %t55.a.107, align 8
  store i64 4095, ptr %t57.a.108, align 8
  %l.109 = load { ptr, i64, i64, i64, i64 }, ptr %c.a.13, align 8
  %l.110 = load i64, ptr %t57.a.108, align 8
  store { ptr, i64, i64, i64, i64 } %l.109, ptr %lp.111, align 8
  %rt.112 = call ptr @__mn_list_get(ptr %lp.111, i64 %l.110)
  store ptr %rt.112, ptr %t58.a.113, align 8
  %l.114 = load i64, ptr %t55.a.107, align 8
  %l.115 = load ptr, ptr %t58.a.113, align 8
  %p2i.116 = ptrtoint ptr %l.115 to i64
  %i.117 = add i64 %l.114, %p2i.116
  store i64 %i.117, ptr %t59.a.118, align 8
  %sp.119 = getelementptr inbounds [11 x i8], ptr @.str.0, i64 0, i64 0
  %s.120 = insertvalue { ptr, i64 } undef, ptr %sp.119, 0
  %s.121 = insertvalue { ptr, i64 } %s.120, i64 11, 1
  store { ptr, i64 } %s.121, ptr %t60.a.122, align 8
  %l.123 = load i64, ptr %t59.a.118, align 8
  %rt.124 = call { ptr, i64 } @__mn_str_from_int(i64 %l.123)
  store { ptr, i64 } %rt.124, ptr %str_track.125, align 8
  store { ptr, i64 } %rt.124, ptr %t61.a.126, align 8
  %l.127 = load { ptr, i64 }, ptr %t60.a.122, align 8
  %l.128 = load { ptr, i64 }, ptr %t61.a.126, align 8
  %rt.129 = call { ptr, i64 } @__mn_str_concat({ ptr, i64 } %l.127, { ptr, i64 } %l.128)
  store { ptr, i64 } %rt.129, ptr %str_track.130, align 8
  store { ptr, i64 } %rt.129, ptr %t62.a.131, align 8
  %l.132 = load { ptr, i64 }, ptr %t62.a.131, align 8
  call void @__mn_str_println({ ptr, i64 } %l.132)
  store i1 false, ptr %t63.a.133, align 1
  %drop.s.134 = load { ptr, i64 }, ptr %str_track.125, align 8
  %drop.p.135 = extractvalue { ptr, i64 } %drop.s.134, 0
  %drop.null.136 = icmp eq ptr %drop.p.135, null
  br i1 %drop.null.136, label %drop.skip.137, label %drop.check.137

while_header6:                                    ; preds = %while_exit11, %while_body4
  %l.154 = load i64, ptr %j.a.78, align 8
  %l.155 = load i64, ptr %n.a.0, align 8
  %i.156 = icmp slt i64 %l.154, %l.155
  store i1 %i.156, ptr %t25.a.157, align 1
  %l.158 = load i1, ptr %t25.a.157, align 1
  br i1 %l.158, label %while_body7, label %while_exit8

while_body7:                                      ; preds = %while_header6
  store i64 0, ptr %t26.a.159, align 8
  %l.160 = load i64, ptr %t26.a.159, align 8
  store i64 %l.160, ptr %sum.a.161, align 8
  store i64 0, ptr %t27.a.162, align 8
  %l.163 = load i64, ptr %t27.a.162, align 8
  store i64 %l.163, ptr %k.a.164, align 8
  br label %while_header9

while_exit8:                                      ; preds = %while_header6
  store i64 1, ptr %t43.a.165, align 8
  %l.166 = load i64, ptr %i.a.70, align 8
  %l.167 = load i64, ptr %t43.a.165, align 8
  %i.168 = add i64 %l.166, %l.167
  store i64 %i.168, ptr %t44.a.169, align 8
  %l.170 = load i64, ptr %t44.a.169, align 8
  store i64 %l.170, ptr %i.a.70, align 8
  br label %while_header3

while_header9:                                    ; preds = %while_body10, %while_body7
  %l.171 = load i64, ptr %k.a.164, align 8
  %l.172 = load i64, ptr %n.a.0, align 8
  %i.173 = icmp slt i64 %l.171, %l.172
  store i1 %i.173, ptr %t28.a.174, align 1
  %l.175 = load i1, ptr %t28.a.174, align 1
  br i1 %l.175, label %while_body10, label %while_exit11

while_body10:                                     ; preds = %while_header9
  %l.176 = load i64, ptr %i.a.70, align 8
  %l.177 = load i64, ptr %n.a.0, align 8
  %i.178 = mul i64 %l.176, %l.177
  store i64 %i.178, ptr %t29.a.179, align 8
  %l.180 = load i64, ptr %t29.a.179, align 8
  %l.181 = load i64, ptr %k.a.164, align 8
  %i.182 = add i64 %l.180, %l.181
  store i64 %i.182, ptr %t30.a.183, align 8
  %l.184 = load { ptr, i64, i64, i64, i64 }, ptr %a.a.5, align 8
  %l.185 = load i64, ptr %t30.a.183, align 8
  store { ptr, i64, i64, i64, i64 } %l.184, ptr %lp.186, align 8
  %rt.187 = call ptr @__mn_list_get(ptr %lp.186, i64 %l.185)
  store ptr %rt.187, ptr %t31.a.188, align 8
  %l.189 = load i64, ptr %k.a.164, align 8
  %l.190 = load i64, ptr %n.a.0, align 8
  %i.191 = mul i64 %l.189, %l.190
  store i64 %i.191, ptr %t32.a.192, align 8
  %l.193 = load i64, ptr %t32.a.192, align 8
  %l.194 = load i64, ptr %j.a.78, align 8
  %i.195 = add i64 %l.193, %l.194
  store i64 %i.195, ptr %t33.a.196, align 8
  %l.197 = load { ptr, i64, i64, i64, i64 }, ptr %b.a.9, align 8
  %l.198 = load i64, ptr %t33.a.196, align 8
  store { ptr, i64, i64, i64, i64 } %l.197, ptr %lp.199, align 8
  %rt.200 = call ptr @__mn_list_get(ptr %lp.199, i64 %l.198)
  store ptr %rt.200, ptr %t34.a.201, align 8
  %l.202 = load ptr, ptr %t31.a.188, align 8
  %l.203 = load ptr, ptr %t34.a.201, align 8
  %p2i.204 = ptrtoint ptr %l.202 to i64
  %p2i.205 = ptrtoint ptr %l.203 to i64
  %i.206 = mul i64 %p2i.204, %p2i.205
  store i64 %i.206, ptr %t35.a.207, align 8
  %l.208 = load i64, ptr %sum.a.161, align 8
  %l.209 = load i64, ptr %t35.a.207, align 8
  %i.210 = add i64 %l.208, %l.209
  store i64 %i.210, ptr %t36.a.211, align 8
  %l.212 = load i64, ptr %t36.a.211, align 8
  store i64 %l.212, ptr %sum.a.161, align 8
  store i64 1, ptr %t37.a.213, align 8
  %l.214 = load i64, ptr %k.a.164, align 8
  %l.215 = load i64, ptr %t37.a.213, align 8
  %i.216 = add i64 %l.214, %l.215
  store i64 %i.216, ptr %t38.a.217, align 8
  %l.218 = load i64, ptr %t38.a.217, align 8
  store i64 %l.218, ptr %k.a.164, align 8
  br label %while_header9

while_exit11:                                     ; preds = %while_header9
  %l.219 = load i64, ptr %i.a.70, align 8
  %l.220 = load i64, ptr %n.a.0, align 8
  %i.221 = mul i64 %l.219, %l.220
  store i64 %i.221, ptr %t39.a.222, align 8
  %l.223 = load i64, ptr %t39.a.222, align 8
  %l.224 = load i64, ptr %j.a.78, align 8
  %i.225 = add i64 %l.223, %l.224
  store i64 %i.225, ptr %t40.a.226, align 8
  %l.227 = load { ptr, i64, i64, i64, i64 }, ptr %c.a.13, align 8
  %l.228 = load i64, ptr %t40.a.226, align 8
  %l.229 = load i64, ptr %sum.a.161, align 8
  store { ptr, i64, i64, i64, i64 } %l.227, ptr %lp.230, align 8
  %rt.231 = call ptr @__mn_list_get(ptr %lp.230, i64 %l.228)
  store i64 %l.229, ptr %rt.231, align 8
  store i64 1, ptr %t41.a.232, align 8
  %l.233 = load i64, ptr %j.a.78, align 8
  %l.234 = load i64, ptr %t41.a.232, align 8
  %i.235 = add i64 %l.233, %l.234
  store i64 %i.235, ptr %t42.a.236, align 8
  %l.237 = load i64, ptr %t42.a.236, align 8
  store i64 %l.237, ptr %j.a.78, align 8
  br label %while_header6

drop.check.137:                                   ; preds = %while_exit5
  call void @__mn_str_free({ ptr, i64 } %drop.s.134)
  br label %drop.skip.137

drop.skip.137:                                    ; preds = %drop.check.137, %while_exit5
  %drop.s.138 = load { ptr, i64 }, ptr %str_track.130, align 8
  %drop.p.139 = extractvalue { ptr, i64 } %drop.s.138, 0
  %drop.null.140 = icmp eq ptr %drop.p.139, null
  br i1 %drop.null.140, label %drop.skip.141, label %drop.check.141

drop.check.141:                                   ; preds = %drop.skip.137
  call void @__mn_str_free({ ptr, i64 } %drop.s.138)
  br label %drop.skip.141

drop.skip.141:                                    ; preds = %drop.check.141, %drop.skip.137
  %drop.lv.142 = load { ptr, i64, i64, i64, i64 }, ptr %a.a.5, align 8
  %drop.lp.143 = extractvalue { ptr, i64, i64, i64, i64 } %drop.lv.142, 0
  %drop.lnull.144 = icmp eq ptr %drop.lp.143, null
  br i1 %drop.lnull.144, label %drop.lskip.145, label %drop.lcheck.145

drop.lcheck.145:                                  ; preds = %drop.skip.141
  call void @__mn_list_free(ptr %a.a.5)
  br label %drop.lskip.145

drop.lskip.145:                                   ; preds = %drop.lcheck.145, %drop.skip.141
  %drop.lv.146 = load { ptr, i64, i64, i64, i64 }, ptr %b.a.9, align 8
  %drop.lp.147 = extractvalue { ptr, i64, i64, i64, i64 } %drop.lv.146, 0
  %drop.lnull.148 = icmp eq ptr %drop.lp.147, null
  br i1 %drop.lnull.148, label %drop.lskip.149, label %drop.lcheck.149

drop.lcheck.149:                                  ; preds = %drop.lskip.145
  call void @__mn_list_free(ptr %b.a.9)
  br label %drop.lskip.149

drop.lskip.149:                                   ; preds = %drop.lcheck.149, %drop.lskip.145
  %drop.lv.150 = load { ptr, i64, i64, i64, i64 }, ptr %c.a.13, align 8
  %drop.lp.151 = extractvalue { ptr, i64, i64, i64, i64 } %drop.lv.150, 0
  %drop.lnull.152 = icmp eq ptr %drop.lp.151, null
  br i1 %drop.lnull.152, label %drop.lskip.153, label %drop.lcheck.153

drop.lcheck.153:                                  ; preds = %drop.lskip.149
  call void @__mn_list_free(ptr %c.a.13)
  br label %drop.lskip.153

drop.lskip.153:                                   ; preds = %drop.lcheck.153, %drop.lskip.149
  call void @__mn_intern_destroy()
  ret i64 0
}

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
