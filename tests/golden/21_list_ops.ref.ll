; ModuleID = '21_list_ops'
source_filename = "21_list_ops"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare i64 @__mn_list_len(ptr)
declare ptr @__mn_range(i64, i64)
declare i1 @__iter_has_next(ptr)
declare i64 @__iter_next(ptr)
declare ptr @__mn_list_get(ptr, i64)
declare i1 @__mn_range_free(ptr)
declare {ptr, i64, i64, i64} @__mn_list_new(i64)
declare void @__mn_list_push(ptr, ptr)
declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define internal i64 @sum_list({ptr, i64, i64, i64} %items) {
pre_entry:
  %items.addr = alloca {ptr, i64, i64, i64}, align 8
  %total.a.0 = alloca i64, align 8
  store i64 0, ptr %total.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %ll.3 = alloca {ptr, i64, i64, i64}, align 8
  %t2.a.5 = alloca i64, align 8
  store i64 0, ptr %t2.a.5
  %t3.a.9 = alloca ptr, align 8
  store ptr null, ptr %t3.a.9
  %has_next5.a.12 = alloca i1, align 8
  store i1 0, ptr %has_next5.a.12
  %next6.a.16 = alloca i64, align 8
  store i64 0, ptr %next6.a.16
  %lp.19 = alloca {ptr, i64, i64, i64}, align 8
  %t7.a.22 = alloca i64, align 8
  store i64 0, ptr %t7.a.22
  %t8.a.26 = alloca i64, align 8
  store i64 0, ptr %t8.a.26
  %range_free9.a.30 = alloca i1, align 8
  store i1 0, ptr %range_free9.a.30
  store {ptr, i64, i64, i64} %items, ptr %items.addr
  br label %entry
entry:
  store i64 0, ptr %total.a.0
  store i64 0, ptr %t1.a.1
  %l.2 = load {ptr, i64, i64, i64}, ptr %items.addr
  store {ptr, i64, i64, i64} %l.2, ptr %ll.3
  %rt.4 = call i64 @__mn_list_len(ptr %ll.3)
  store i64 %rt.4, ptr %t2.a.5
  %l.6 = load i64, ptr %t1.a.1
  %l.7 = load i64, ptr %t2.a.5
  %c.8 = call ptr @__mn_range(i64 %l.6, i64 %l.7)
  store ptr %c.8, ptr %t3.a.9
  br label %for_header0
for_header0:
  %l.10 = load ptr, ptr %t3.a.9
  %c.11 = call i1 @__iter_has_next(ptr %l.10)
  store i1 %c.11, ptr %has_next5.a.12
  %l.13 = load i1, ptr %has_next5.a.12
  br i1 %l.13, label %for_body1, label %for_exit2
for_body1:
  %l.14 = load ptr, ptr %t3.a.9
  %c.15 = call i64 @__iter_next(ptr %l.14)
  store i64 %c.15, ptr %next6.a.16
  %l.17 = load {ptr, i64, i64, i64}, ptr %items.addr
  %l.18 = load i64, ptr %next6.a.16
  store {ptr, i64, i64, i64} %l.17, ptr %lp.19
  %rt.20 = call ptr @__mn_list_get(ptr %lp.19, i64 %l.18)
  %el.21 = load i64, ptr %rt.20
  store i64 %el.21, ptr %t7.a.22
  %l.23 = load i64, ptr %total.a.0
  %l.24 = load i64, ptr %t7.a.22
  %i.25 = add nsw i64 %l.23, %l.24
  store i64 %i.25, ptr %t8.a.26
  %l.27 = load i64, ptr %t8.a.26
  store i64 %l.27, ptr %total.a.0
  br label %for_header0
for_exit2:
  %l.28 = load ptr, ptr %t3.a.9
  %c.29 = call i1 @__mn_range_free(ptr %l.28)
  store i1 %c.29, ptr %range_free9.a.30
  %l.31 = load i64, ptr %total.a.0
  ret i64 %l.31
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.2 = alloca i64, align 8
  store i64 0, ptr %t2.a.2
  %t3.a.3 = alloca i64, align 8
  store i64 0, ptr %t3.a.3
  %lp.5 = alloca {ptr, i64, i64, i64}, align 8
  %ea.7 = alloca i64, align 8
  %ea.10 = alloca i64, align 8
  %ea.13 = alloca i64, align 8
  %ea.16 = alloca i64, align 8
  %t4.a.19 = alloca {ptr, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64} zeroinitializer, ptr %t4.a.19
  %nums.a.21 = alloca {ptr, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64} zeroinitializer, ptr %nums.a.21
  %t5.a.24 = alloca i64, align 8
  store i64 0, ptr %t5.a.24
  %t6.a.27 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.27
  %t7.a.29 = alloca i1, align 8
  store i1 0, ptr %t7.a.29
  %t8.a.30 = alloca i64, align 8
  store i64 0, ptr %t8.a.30
  %ea.32 = alloca i64, align 8
  %ll.35 = alloca {ptr, i64, i64, i64}, align 8
  %t9.a.37 = alloca i64, align 8
  store i64 0, ptr %t9.a.37
  %t10.a.40 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.40
  %t11.a.42 = alloca i1, align 8
  store i1 0, ptr %t11.a.42
  %t12.a.45 = alloca i64, align 8
  store i64 0, ptr %t12.a.45
  %t13.a.48 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t13.a.48
  %t14.a.50 = alloca i1, align 8
  store i1 0, ptr %t14.a.50
  br label %entry
entry:
  store i64 10, ptr %t0.a.0
  store i64 20, ptr %t1.a.1
  store i64 30, ptr %t2.a.2
  store i64 40, ptr %t3.a.3
  %ln.4 = call {ptr, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64} %ln.4, ptr %lp.5
  %l.6 = load i64, ptr %t0.a.0
  store i64 %l.6, ptr %ea.7
  call void @__mn_list_push(ptr %lp.5, ptr %ea.7)
  %l.9 = load i64, ptr %t1.a.1
  store i64 %l.9, ptr %ea.10
  call void @__mn_list_push(ptr %lp.5, ptr %ea.10)
  %l.12 = load i64, ptr %t2.a.2
  store i64 %l.12, ptr %ea.13
  call void @__mn_list_push(ptr %lp.5, ptr %ea.13)
  %l.15 = load i64, ptr %t3.a.3
  store i64 %l.15, ptr %ea.16
  call void @__mn_list_push(ptr %lp.5, ptr %ea.16)
  %ll.18 = load {ptr, i64, i64, i64}, ptr %lp.5
  store {ptr, i64, i64, i64} %ll.18, ptr %t4.a.19
  %l.20 = load {ptr, i64, i64, i64}, ptr %t4.a.19
  store {ptr, i64, i64, i64} %l.20, ptr %nums.a.21
  %l.22 = load {ptr, i64, i64, i64}, ptr %nums.a.21
  %c.23 = call i64 @sum_list({ptr, i64, i64, i64} %l.22)
  store i64 %c.23, ptr %t5.a.24
  %l.25 = load i64, ptr %t5.a.24
  %rt.26 = call {ptr, i64} @__mn_str_from_int(i64 %l.25)
  store {ptr, i64} %rt.26, ptr %t6.a.27
  %l.28 = load {ptr, i64}, ptr %t6.a.27
  call void @__mn_str_println({ptr, i64} %l.28)
  store i1 0, ptr %t7.a.29
  store i64 50, ptr %t8.a.30
  %l.31 = load i64, ptr %t8.a.30
  store i64 %l.31, ptr %ea.32
  call void @__mn_list_push(ptr %t4.a.19, ptr %ea.32)
  %ul.33 = load {ptr, i64, i64, i64}, ptr %t4.a.19
  store {ptr, i64, i64, i64} %ul.33, ptr %nums.a.21
  %l.34 = load {ptr, i64, i64, i64}, ptr %nums.a.21
  store {ptr, i64, i64, i64} %l.34, ptr %ll.35
  %rt.36 = call i64 @__mn_list_len(ptr %ll.35)
  store i64 %rt.36, ptr %t9.a.37
  %l.38 = load i64, ptr %t9.a.37
  %rt.39 = call {ptr, i64} @__mn_str_from_int(i64 %l.38)
  store {ptr, i64} %rt.39, ptr %t10.a.40
  %l.41 = load {ptr, i64}, ptr %t10.a.40
  call void @__mn_str_println({ptr, i64} %l.41)
  store i1 0, ptr %t11.a.42
  %l.43 = load {ptr, i64, i64, i64}, ptr %nums.a.21
  %c.44 = call i64 @sum_list({ptr, i64, i64, i64} %l.43)
  store i64 %c.44, ptr %t12.a.45
  %l.46 = load i64, ptr %t12.a.45
  %rt.47 = call {ptr, i64} @__mn_str_from_int(i64 %l.46)
  store {ptr, i64} %rt.47, ptr %t13.a.48
  %l.49 = load {ptr, i64}, ptr %t13.a.48
  call void @__mn_str_println({ptr, i64} %l.49)
  store i1 0, ptr %t14.a.50
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.14.0"}
