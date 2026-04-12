; ModuleID = '21_list_ops'
source_filename = "21_list_ops"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare i64 @__mn_list_len(ptr) nounwind readonly willreturn
declare ptr @__mn_range(i64, i64)
declare i1 @__iter_has_next(ptr)
declare i64 @__iter_next(ptr)
declare ptr @__mn_list_get(ptr, i64) nounwind readonly willreturn
declare i1 @__mn_range_free(ptr) nounwind willreturn
declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind willreturn
declare void @__mn_list_push(ptr, ptr) nounwind
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal i64 @sum_list({ptr, i64, i64, i64, i64} %items) {
pre_entry:
  %items.addr = alloca {ptr, i64, i64, i64, i64}, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %total.a.2 = alloca i64, align 8
  store i64 0, ptr %total.a.2
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %ll.5 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t2.a.7 = alloca i64, align 8
  store i64 0, ptr %t2.a.7
  %t3.a.11 = alloca ptr, align 8
  store ptr null, ptr %t3.a.11
  %has_next5.a.14 = alloca i1, align 8
  store i1 0, ptr %has_next5.a.14
  %next6.a.18 = alloca i64, align 8
  store i64 0, ptr %next6.a.18
  %lp.21 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t7.a.24 = alloca i64, align 8
  store i64 0, ptr %t7.a.24
  %t8.a.28 = alloca i64, align 8
  store i64 0, ptr %t8.a.28
  %range_free9.a.32 = alloca i1, align 8
  store i1 0, ptr %range_free9.a.32
  store {ptr, i64, i64, i64, i64} %items, ptr %items.addr
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  store i64 %l.1, ptr %total.a.2
  store i64 0, ptr %t1.a.3
  %l.4 = load {ptr, i64, i64, i64, i64}, ptr %items.addr
  store {ptr, i64, i64, i64, i64} %l.4, ptr %ll.5
  %rt.6 = call i64 @__mn_list_len(ptr %ll.5)
  store i64 %rt.6, ptr %t2.a.7
  %l.8 = load i64, ptr %t1.a.3
  %l.9 = load i64, ptr %t2.a.7
  %c.10 = call ptr @__mn_range(i64 %l.8, i64 %l.9)
  store ptr %c.10, ptr %t3.a.11
  br label %for_header0
for_header0:
  %l.12 = load ptr, ptr %t3.a.11
  %c.13 = call i1 @__iter_has_next(ptr %l.12)
  store i1 %c.13, ptr %has_next5.a.14
  %l.15 = load i1, ptr %has_next5.a.14
  br i1 %l.15, label %for_body1, label %for_exit2
for_body1:
  %l.16 = load ptr, ptr %t3.a.11
  %c.17 = call i64 @__iter_next(ptr %l.16)
  store i64 %c.17, ptr %next6.a.18
  %l.19 = load {ptr, i64, i64, i64, i64}, ptr %items.addr
  %l.20 = load i64, ptr %next6.a.18
  store {ptr, i64, i64, i64, i64} %l.19, ptr %lp.21
  %rt.22 = call ptr @__mn_list_get(ptr %lp.21, i64 %l.20)
  %el.23 = load i64, ptr %rt.22
  store i64 %el.23, ptr %t7.a.24
  %l.25 = load i64, ptr %total.a.2
  %l.26 = load i64, ptr %t7.a.24
  %i.27 = add nsw i64 %l.25, %l.26
  store i64 %i.27, ptr %t8.a.28
  %l.29 = load i64, ptr %t8.a.28
  store i64 %l.29, ptr %total.a.2
  br label %for_header0
for_exit2:
  %l.30 = load ptr, ptr %t3.a.11
  %c.31 = call i1 @__mn_range_free(ptr %l.30)
  store i1 %c.31, ptr %range_free9.a.32
  %l.33 = load i64, ptr %total.a.2
  ret i64 %l.33
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
  %lp.5 = alloca {ptr, i64, i64, i64, i64}, align 8
  %ea.7 = alloca i64, align 8
  %ea.10 = alloca i64, align 8
  %ea.13 = alloca i64, align 8
  %ea.16 = alloca i64, align 8
  %t4.a.19 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t4.a.19
  %nums.a.21 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %nums.a.21
  %t5.a.24 = alloca i64, align 8
  store i64 0, ptr %t5.a.24
  %str_track.27 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.27
  %t6.a.28 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.28
  %t7.a.30 = alloca i1, align 8
  store i1 0, ptr %t7.a.30
  %t8.a.31 = alloca i64, align 8
  store i64 0, ptr %t8.a.31
  %ea.33 = alloca i64, align 8
  %ll.36 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t9.a.38 = alloca i64, align 8
  store i64 0, ptr %t9.a.38
  %str_track.41 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.41
  %t10.a.42 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.42
  %t11.a.44 = alloca i1, align 8
  store i1 0, ptr %t11.a.44
  %t12.a.47 = alloca i64, align 8
  store i64 0, ptr %t12.a.47
  %str_track.50 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.50
  %t13.a.51 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t13.a.51
  %t14.a.53 = alloca i1, align 8
  store i1 0, ptr %t14.a.53
  br label %entry
entry:
  store i64 10, ptr %t0.a.0
  store i64 20, ptr %t1.a.1
  store i64 30, ptr %t2.a.2
  store i64 40, ptr %t3.a.3
  %ln.4 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.4, ptr %lp.5
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
  %ll.18 = load {ptr, i64, i64, i64, i64}, ptr %lp.5
  store {ptr, i64, i64, i64, i64} %ll.18, ptr %t4.a.19
  %l.20 = load {ptr, i64, i64, i64, i64}, ptr %t4.a.19
  store {ptr, i64, i64, i64, i64} %l.20, ptr %nums.a.21
  %l.22 = load {ptr, i64, i64, i64, i64}, ptr %nums.a.21
  %c.23 = call i64 @sum_list({ptr, i64, i64, i64, i64} %l.22)
  store i64 %c.23, ptr %t5.a.24
  %l.25 = load i64, ptr %t5.a.24
  %rt.26 = call {ptr, i64} @__mn_str_from_int(i64 %l.25)
  store {ptr, i64} %rt.26, ptr %str_track.27
  store {ptr, i64} %rt.26, ptr %t6.a.28
  %l.29 = load {ptr, i64}, ptr %t6.a.28
  call void @__mn_str_println({ptr, i64} %l.29)
  store i1 0, ptr %t7.a.30
  store i64 50, ptr %t8.a.31
  %l.32 = load i64, ptr %t8.a.31
  store i64 %l.32, ptr %ea.33
  call void @__mn_list_push(ptr %t4.a.19, ptr %ea.33)
  %ul.34 = load {ptr, i64, i64, i64, i64}, ptr %t4.a.19
  store {ptr, i64, i64, i64, i64} %ul.34, ptr %nums.a.21
  %l.35 = load {ptr, i64, i64, i64, i64}, ptr %nums.a.21
  store {ptr, i64, i64, i64, i64} %l.35, ptr %ll.36
  %rt.37 = call i64 @__mn_list_len(ptr %ll.36)
  store i64 %rt.37, ptr %t9.a.38
  %l.39 = load i64, ptr %t9.a.38
  %rt.40 = call {ptr, i64} @__mn_str_from_int(i64 %l.39)
  store {ptr, i64} %rt.40, ptr %str_track.41
  store {ptr, i64} %rt.40, ptr %t10.a.42
  %l.43 = load {ptr, i64}, ptr %t10.a.42
  call void @__mn_str_println({ptr, i64} %l.43)
  store i1 0, ptr %t11.a.44
  %l.45 = load {ptr, i64, i64, i64, i64}, ptr %nums.a.21
  %c.46 = call i64 @sum_list({ptr, i64, i64, i64, i64} %l.45)
  store i64 %c.46, ptr %t12.a.47
  %l.48 = load i64, ptr %t12.a.47
  %rt.49 = call {ptr, i64} @__mn_str_from_int(i64 %l.48)
  store {ptr, i64} %rt.49, ptr %str_track.50
  store {ptr, i64} %rt.49, ptr %t13.a.51
  %l.52 = load {ptr, i64}, ptr %t13.a.51
  call void @__mn_str_println({ptr, i64} %l.52)
  store i1 0, ptr %t14.a.53
  %drop.s.54 = load {ptr, i64}, ptr %str_track.27
  %drop.p.55 = extractvalue {ptr, i64} %drop.s.54, 0
  %drop.null.56 = icmp eq ptr %drop.p.55, null
  br i1 %drop.null.56, label %drop.skip.57, label %drop.check.57
drop.check.57:
  call void @__mn_str_free({ptr, i64} %drop.s.54)
  br label %drop.skip.57
drop.skip.57:
  %drop.s.58 = load {ptr, i64}, ptr %str_track.41
  %drop.p.59 = extractvalue {ptr, i64} %drop.s.58, 0
  %drop.null.60 = icmp eq ptr %drop.p.59, null
  br i1 %drop.null.60, label %drop.skip.61, label %drop.check.61
drop.check.61:
  call void @__mn_str_free({ptr, i64} %drop.s.58)
  br label %drop.skip.61
drop.skip.61:
  %drop.s.62 = load {ptr, i64}, ptr %str_track.50
  %drop.p.63 = extractvalue {ptr, i64} %drop.s.62, 0
  %drop.null.64 = icmp eq ptr %drop.p.63, null
  br i1 %drop.null.64, label %drop.skip.65, label %drop.check.65
drop.check.65:
  call void @__mn_str_free({ptr, i64} %drop.s.62)
  br label %drop.skip.65
drop.skip.65:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.33.0"}
