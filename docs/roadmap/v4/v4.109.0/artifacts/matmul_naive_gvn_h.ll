; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/matmul_naive.bc'
source_filename = "matmul_naive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"checksum = ", align 8

; Function Attrs: nounwind willreturn
declare { ptr, i64, i64, i64, i64 } @__mn_list_new(i64) #0

; Function Attrs: nounwind
declare void @__mn_list_push(ptr, ptr) #1

; Function Attrs: nounwind
declare ptr @__mn_list_get(ptr, i64) #1

; Function Attrs: nounwind willreturn
declare { ptr, i64 } @__mn_str_from_int(i64) #0

; Function Attrs: nounwind willreturn
declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 }) #0

declare void @__mn_str_println({ ptr, i64 })

; Function Attrs: nounwind willreturn
declare void @__mn_str_free({ ptr, i64 }) #0

; Function Attrs: nounwind willreturn
declare void @free(ptr) #0

; Function Attrs: nounwind willreturn
declare void @__mn_list_free(ptr) #0

declare void @__mn_intern_destroy()

; Function Attrs: nounwind willreturn
define i64 @main() #0 {
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
  store i64 64, ptr %n.a.0, align 8
  store i64 4096, ptr %t1.a.1, align 8
  %ln.2 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  store { ptr, i64, i64, i64, i64 } %ln.2, ptr %t2.a.3, align 8
  store { ptr, i64, i64, i64, i64 } %ln.2, ptr %a.a.5, align 8
  %ln.6 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  store { ptr, i64, i64, i64, i64 } %ln.6, ptr %t3.a.7, align 8
  store { ptr, i64, i64, i64, i64 } %ln.6, ptr %b.a.9, align 8
  %ln.10 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  store { ptr, i64, i64, i64, i64 } %ln.10, ptr %t4.a.11, align 8
  store { ptr, i64, i64, i64, i64 } %ln.10, ptr %c.a.13, align 8
  store i64 0, ptr %t5.a.14, align 8
  store i64 0, ptr %idx.a.16, align 8
  br label %while_header0

while_header0:                                    ; preds = %while_body1, %pre_entry
  %l.197 = phi { ptr, i64, i64, i64, i64 } [ %ul.57, %while_body1 ], [ %ln.6, %pre_entry ]
  %l.184 = phi { ptr, i64, i64, i64, i64 } [ %ul.39, %while_body1 ], [ %ln.2, %pre_entry ]
  %l.227 = phi { ptr, i64, i64, i64, i64 } [ %ul.61, %while_body1 ], [ %ln.10, %pre_entry ]
  %l.63 = phi i64 [ %i.65, %while_body1 ], [ 0, %pre_entry ]
  %i.19 = icmp slt i64 %l.63, 4096
  store i1 %i.19, ptr %t6.a.20, align 1
  br i1 %i.19, label %while_body1, label %while_exit2

while_body1:                                      ; preds = %while_header0
  store i64 3, ptr %t7.a.22, align 8
  %i.25 = mul nsw i64 %l.63, 3
  store i64 %i.25, ptr %t8.a.26, align 8
  store i64 7, ptr %t9.a.27, align 8
  %i.30 = add nsw i64 %i.25, 7
  store i64 %i.30, ptr %t10.a.31, align 8
  store i64 100, ptr %t11.a.32, align 8
  %i.35 = srem i64 %i.30, 100
  store i64 %i.35, ptr %t12.a.36, align 8
  store i64 %i.35, ptr %ea.38, align 8
  call void @__mn_list_push(ptr %t2.a.3, ptr %ea.38)
  %ul.39 = load { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, align 8
  store { ptr, i64, i64, i64, i64 } %ul.39, ptr %a.a.5, align 8
  store i64 5, ptr %t13.a.40, align 8
  %i.43 = mul nsw i64 %l.63, 5
  store i64 %i.43, ptr %t14.a.44, align 8
  store i64 13, ptr %t15.a.45, align 8
  %i.48 = add nsw i64 %i.43, 13
  store i64 %i.48, ptr %t16.a.49, align 8
  store i64 100, ptr %t17.a.50, align 8
  %i.53 = srem i64 %i.48, 100
  store i64 %i.53, ptr %t18.a.54, align 8
  store i64 %i.53, ptr %ea.56, align 8
  call void @__mn_list_push(ptr %t3.a.7, ptr %ea.56)
  %ul.57 = load { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, align 8
  store { ptr, i64, i64, i64, i64 } %ul.57, ptr %b.a.9, align 8
  store i64 0, ptr %t19.a.58, align 8
  store i64 0, ptr %ea.60, align 8
  call void @__mn_list_push(ptr %t4.a.11, ptr %ea.60)
  %ul.61 = load { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, align 8
  store { ptr, i64, i64, i64, i64 } %ul.61, ptr %c.a.13, align 8
  store i64 1, ptr %t20.a.62, align 8
  %i.65 = add nsw i64 %l.63, 1
  store i64 %i.65, ptr %t21.a.66, align 8
  store i64 %i.65, ptr %idx.a.16, align 8
  br label %while_header0

while_exit2:                                      ; preds = %while_header0
  store i64 0, ptr %t22.a.68, align 8
  store i64 0, ptr %i.a.70, align 8
  br label %while_header3

while_header3:                                    ; preds = %while_exit8, %while_exit2
  %l.22025 = phi i64 [ %l.22026, %while_exit8 ], [ 64, %while_exit2 ]
  %l.15518 = phi i64 [ %l.155, %while_exit8 ], [ 64, %while_exit2 ]
  %drop.lv.146 = phi { ptr, i64, i64, i64, i64 } [ %drop.lv.14614, %while_exit8 ], [ %l.197, %while_exit2 ]
  %drop.lv.142 = phi { ptr, i64, i64, i64, i64 } [ %drop.lv.14210, %while_exit8 ], [ %l.184, %while_exit2 ]
  %drop.lv.150 = phi { ptr, i64, i64, i64, i64 } [ %l.806, %while_exit8 ], [ %l.227, %while_exit2 ]
  %l.176 = phi i64 [ %i.168, %while_exit8 ], [ 0, %while_exit2 ]
  %i.73 = icmp slt i64 %l.176, %l.15518
  store i1 %i.73, ptr %t23.a.74, align 1
  br i1 %i.73, label %while_body4, label %while_exit5

while_body4:                                      ; preds = %while_header3
  store i64 0, ptr %t24.a.76, align 8
  store i64 0, ptr %j.a.78, align 8
  br label %while_header6

while_exit5:                                      ; preds = %while_header3
  store i64 0, ptr %t45.a.79, align 8
  store { ptr, i64, i64, i64, i64 } %drop.lv.150, ptr %lp.82, align 8
  %rt.83 = call ptr @__mn_list_get(ptr %lp.82, i64 0)
  store ptr %rt.83, ptr %t46.a.84, align 8
  store i64 63, ptr %t48.a.85, align 8
  store { ptr, i64, i64, i64, i64 } %drop.lv.150, ptr %lp.88, align 8
  %rt.89 = call ptr @__mn_list_get(ptr %lp.88, i64 63)
  store ptr %rt.89, ptr %t49.a.90, align 8
  %p2i.93 = ptrtoint ptr %rt.83 to i64
  %p2i.94 = ptrtoint ptr %rt.89 to i64
  %i.95 = add nsw i64 %p2i.93, %p2i.94
  store i64 %i.95, ptr %t50.a.96, align 8
  store i64 4032, ptr %t53.a.97, align 8
  store { ptr, i64, i64, i64, i64 } %drop.lv.150, ptr %lp.100, align 8
  %rt.101 = call ptr @__mn_list_get(ptr %lp.100, i64 4032)
  store ptr %rt.101, ptr %t54.a.102, align 8
  %p2i.105 = ptrtoint ptr %rt.101 to i64
  %i.106 = add nsw i64 %i.95, %p2i.105
  store i64 %i.106, ptr %t55.a.107, align 8
  store i64 4095, ptr %t57.a.108, align 8
  store { ptr, i64, i64, i64, i64 } %drop.lv.150, ptr %lp.111, align 8
  %rt.112 = call ptr @__mn_list_get(ptr %lp.111, i64 4095)
  store ptr %rt.112, ptr %t58.a.113, align 8
  %p2i.116 = ptrtoint ptr %rt.112 to i64
  %i.117 = add nsw i64 %i.106, %p2i.116
  store i64 %i.117, ptr %t59.a.118, align 8
  store { ptr, i64 } { ptr @.str.0, i64 11 }, ptr %t60.a.122, align 8
  %rt.124 = call { ptr, i64 } @__mn_str_from_int(i64 %i.117)
  store { ptr, i64 } %rt.124, ptr %str_track.125, align 8
  store { ptr, i64 } %rt.124, ptr %t61.a.126, align 8
  %rt.129 = call { ptr, i64 } @__mn_str_concat({ ptr, i64 } { ptr @.str.0, i64 11 }, { ptr, i64 } %rt.124)
  store { ptr, i64 } %rt.129, ptr %str_track.130, align 8
  store { ptr, i64 } %rt.129, ptr %t62.a.131, align 8
  call void @__mn_str_println({ ptr, i64 } %rt.129)
  store i1 false, ptr %t63.a.133, align 1
  %drop.p.135 = extractvalue { ptr, i64 } %rt.124, 0
  %drop.null.136 = icmp eq ptr %drop.p.135, null
  br i1 %drop.null.136, label %drop.skip.137, label %drop.check.137

while_header6:                                    ; preds = %while_exit11, %while_body4
  %l.22026 = phi i64 [ %l.177, %while_exit11 ], [ %l.22025, %while_body4 ]
  %l.21923 = phi i64 [ %l.219, %while_exit11 ], [ %l.176, %while_body4 ]
  %l.155 = phi i64 [ %l.177, %while_exit11 ], [ %l.15518, %while_body4 ]
  %l.194 = phi i64 [ %i.235, %while_exit11 ], [ 0, %while_body4 ]
  %drop.lv.14614 = phi { ptr, i64, i64, i64, i64 } [ %drop.lv.14613, %while_exit11 ], [ %drop.lv.146, %while_body4 ]
  %drop.lv.14210 = phi { ptr, i64, i64, i64, i64 } [ %drop.lv.1429, %while_exit11 ], [ %drop.lv.142, %while_body4 ]
  %l.806 = phi { ptr, i64, i64, i64, i64 } [ %l.227, %while_exit11 ], [ %drop.lv.150, %while_body4 ]
  %i.156 = icmp slt i64 %l.194, %l.155
  store i1 %i.156, ptr %t25.a.157, align 1
  br i1 %i.156, label %while_body7, label %while_exit8

while_body7:                                      ; preds = %while_header6
  store i64 0, ptr %t26.a.159, align 8
  store i64 0, ptr %sum.a.161, align 8
  store i64 0, ptr %t27.a.162, align 8
  store i64 0, ptr %k.a.164, align 8
  br label %while_header9

while_exit8:                                      ; preds = %while_header6
  store i64 1, ptr %t43.a.165, align 8
  %i.168 = add nsw i64 %l.21923, 1
  store i64 %i.168, ptr %t44.a.169, align 8
  store i64 %i.168, ptr %i.a.70, align 8
  br label %while_header3

while_header9:                                    ; preds = %while_body10, %while_body7
  %l.208 = phi i64 [ %i.210, %while_body10 ], [ 0, %while_body7 ]
  %l.177 = phi i64 [ 64, %while_body10 ], [ %l.22026, %while_body7 ]
  %l.219 = phi i64 [ %l.176, %while_body10 ], [ %l.21923, %while_body7 ]
  %l.172 = phi i64 [ 64, %while_body10 ], [ %l.155, %while_body7 ]
  %l.214 = phi i64 [ %i.216, %while_body10 ], [ 0, %while_body7 ]
  %drop.lv.14613 = phi { ptr, i64, i64, i64, i64 } [ %l.197, %while_body10 ], [ %drop.lv.14614, %while_body7 ]
  %drop.lv.1429 = phi { ptr, i64, i64, i64, i64 } [ %l.184, %while_body10 ], [ %drop.lv.14210, %while_body7 ]
  %i.173 = icmp slt i64 %l.214, %l.172
  store i1 %i.173, ptr %t28.a.174, align 1
  br i1 %i.173, label %while_body10, label %while_exit11

while_body10:                                     ; preds = %while_header9
  %i.178 = mul nsw i64 %l.176, %l.177
  store i64 %i.178, ptr %t29.a.179, align 8
  %i.182 = add nsw i64 %i.178, %l.214
  store i64 %i.182, ptr %t30.a.183, align 8
  store { ptr, i64, i64, i64, i64 } %l.184, ptr %lp.186, align 8
  %rt.187 = call ptr @__mn_list_get(ptr %lp.186, i64 %i.182)
  store ptr %rt.187, ptr %t31.a.188, align 8
  %i.191 = mul nsw i64 %l.214, 64
  store i64 %i.191, ptr %t32.a.192, align 8
  %i.195 = add nsw i64 %i.191, %l.194
  store i64 %i.195, ptr %t33.a.196, align 8
  store { ptr, i64, i64, i64, i64 } %l.197, ptr %lp.199, align 8
  %rt.200 = call ptr @__mn_list_get(ptr %lp.199, i64 %i.195)
  store ptr %rt.200, ptr %t34.a.201, align 8
  %p2i.204 = ptrtoint ptr %rt.187 to i64
  %p2i.205 = ptrtoint ptr %rt.200 to i64
  %i.206 = mul nsw i64 %p2i.204, %p2i.205
  store i64 %i.206, ptr %t35.a.207, align 8
  %i.210 = add nsw i64 %l.208, %i.206
  store i64 %i.210, ptr %t36.a.211, align 8
  store i64 %i.210, ptr %sum.a.161, align 8
  store i64 1, ptr %t37.a.213, align 8
  %i.216 = add nsw i64 %l.214, 1
  store i64 %i.216, ptr %t38.a.217, align 8
  store i64 %i.216, ptr %k.a.164, align 8
  br label %while_header9

while_exit11:                                     ; preds = %while_header9
  %i.221 = mul nsw i64 %l.219, %l.177
  store i64 %i.221, ptr %t39.a.222, align 8
  %i.225 = add nsw i64 %i.221, %l.194
  store i64 %i.225, ptr %t40.a.226, align 8
  store { ptr, i64, i64, i64, i64 } %l.227, ptr %lp.230, align 8
  %rt.231 = call ptr @__mn_list_get(ptr %lp.230, i64 %i.225)
  store i64 %l.208, ptr %rt.231, align 8
  store i64 1, ptr %t41.a.232, align 8
  %i.235 = add nsw i64 %l.194, 1
  store i64 %i.235, ptr %t42.a.236, align 8
  store i64 %i.235, ptr %j.a.78, align 8
  br label %while_header6

drop.check.137:                                   ; preds = %while_exit5
  call void @__mn_str_free({ ptr, i64 } %rt.124)
  br label %drop.skip.137

drop.skip.137:                                    ; preds = %drop.check.137, %while_exit5
  %drop.p.139 = extractvalue { ptr, i64 } %rt.129, 0
  %drop.null.140 = icmp eq ptr %drop.p.139, null
  br i1 %drop.null.140, label %drop.skip.141, label %drop.check.141

drop.check.141:                                   ; preds = %drop.skip.137
  call void @__mn_str_free({ ptr, i64 } %rt.129)
  br label %drop.skip.141

drop.skip.141:                                    ; preds = %drop.check.141, %drop.skip.137
  %drop.lp.143 = extractvalue { ptr, i64, i64, i64, i64 } %drop.lv.142, 0
  %drop.lnull.144 = icmp eq ptr %drop.lp.143, null
  br i1 %drop.lnull.144, label %drop.lskip.145, label %drop.lcheck.145

drop.lcheck.145:                                  ; preds = %drop.skip.141
  call void @__mn_list_free(ptr %a.a.5)
  br label %drop.lskip.145

drop.lskip.145:                                   ; preds = %drop.lcheck.145, %drop.skip.141
  %drop.lp.147 = extractvalue { ptr, i64, i64, i64, i64 } %drop.lv.146, 0
  %drop.lnull.148 = icmp eq ptr %drop.lp.147, null
  br i1 %drop.lnull.148, label %drop.lskip.149, label %drop.lcheck.149

drop.lcheck.149:                                  ; preds = %drop.lskip.145
  call void @__mn_list_free(ptr %b.a.9)
  br label %drop.lskip.149

drop.lskip.149:                                   ; preds = %drop.lcheck.149, %drop.lskip.145
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

attributes #0 = { nounwind willreturn }
attributes #1 = { nounwind }

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
