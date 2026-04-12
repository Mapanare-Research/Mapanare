; ModuleID = '33_break_continue'
source_filename = "33_break_continue"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 8

declare ptr @__mn_range(i64, i64)
declare i1 @__iter_has_next(ptr)
declare i64 @__iter_next(ptr)
declare i1 @__mn_range_free(ptr) nounwind willreturn
declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind willreturn
declare void @__mn_list_push(ptr, ptr) nounwind
declare ptr @__mn_list_get(ptr, i64) nounwind readonly willreturn
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_list_free(ptr) nounwind willreturn
declare i32 @printf(ptr, ...)
declare void @__mn_intern_destroy()

define internal i64 @sum_until(i64 %limit) {
pre_entry:
  %limit.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %sum.a.2 = alloca i64, align 8
  store i64 0, ptr %sum.a.2
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %i.a.5 = alloca i64, align 8
  store i64 0, ptr %i.a.5
  %t2.a.6 = alloca i64, align 8
  store i64 0, ptr %t2.a.6
  %t3.a.10 = alloca i1, align 8
  store i1 0, ptr %t3.a.10
  %t4.a.15 = alloca i1, align 8
  store i1 0, ptr %t4.a.15
  %t6.a.21 = alloca i64, align 8
  store i64 0, ptr %t6.a.21
  %t7.a.23 = alloca i64, align 8
  store i64 0, ptr %t7.a.23
  %t8.a.27 = alloca i64, align 8
  store i64 0, ptr %t8.a.27
  store i64 %limit, ptr %limit.addr
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  store i64 %l.1, ptr %sum.a.2
  store i64 0, ptr %t1.a.3
  %l.4 = load i64, ptr %t1.a.3
  store i64 %l.4, ptr %i.a.5
  br label %while_header0
while_header0:
  store i64 20, ptr %t2.a.6
  %l.7 = load i64, ptr %i.a.5
  %l.8 = load i64, ptr %t2.a.6
  %i.9 = icmp slt i64 %l.7, %l.8
  store i1 %i.9, ptr %t3.a.10
  %l.11 = load i1, ptr %t3.a.10
  br i1 %l.11, label %while_body1, label %while_exit2
while_body1:
  %l.12 = load i64, ptr %i.a.5
  %l.13 = load i64, ptr %limit.addr
  %i.14 = icmp sge i64 %l.12, %l.13
  store i1 %i.14, ptr %t4.a.15
  %l.16 = load i1, ptr %t4.a.15
  br i1 %l.16, label %if_then3, label %if_else4
while_exit2:
  %l.17 = load i64, ptr %sum.a.2
  ret i64 %l.17
if_then3:
  br label %while_exit2
if_else4:
  br label %if_merge5
if_merge5:
  %l.18 = load i64, ptr %sum.a.2
  %l.19 = load i64, ptr %i.a.5
  %i.20 = add nsw i64 %l.18, %l.19
  store i64 %i.20, ptr %t6.a.21
  %l.22 = load i64, ptr %t6.a.21
  store i64 %l.22, ptr %sum.a.2
  store i64 1, ptr %t7.a.23
  %l.24 = load i64, ptr %i.a.5
  %l.25 = load i64, ptr %t7.a.23
  %i.26 = add nsw i64 %l.24, %l.25
  store i64 %i.26, ptr %t8.a.27
  %l.28 = load i64, ptr %t8.a.27
  store i64 %l.28, ptr %i.a.5
  br label %while_header0
}

define internal i64 @skip_evens() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %sum.a.2 = alloca i64, align 8
  store i64 0, ptr %sum.a.2
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %i.a.5 = alloca i64, align 8
  store i64 0, ptr %i.a.5
  %t2.a.6 = alloca i64, align 8
  store i64 0, ptr %t2.a.6
  %t3.a.10 = alloca i1, align 8
  store i1 0, ptr %t3.a.10
  %t4.a.12 = alloca i64, align 8
  store i64 0, ptr %t4.a.12
  %t5.a.16 = alloca i64, align 8
  store i64 0, ptr %t5.a.16
  %t6.a.18 = alloca i64, align 8
  store i64 0, ptr %t6.a.18
  %t7.a.22 = alloca i64, align 8
  store i64 0, ptr %t7.a.22
  %t8.a.23 = alloca i64, align 8
  store i64 0, ptr %t8.a.23
  %t9.a.27 = alloca i1, align 8
  store i1 0, ptr %t9.a.27
  %t11.a.33 = alloca i64, align 8
  store i64 0, ptr %t11.a.33
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  store i64 %l.1, ptr %sum.a.2
  store i64 0, ptr %t1.a.3
  %l.4 = load i64, ptr %t1.a.3
  store i64 %l.4, ptr %i.a.5
  br label %while_header0
while_header0:
  store i64 10, ptr %t2.a.6
  %l.7 = load i64, ptr %i.a.5
  %l.8 = load i64, ptr %t2.a.6
  %i.9 = icmp slt i64 %l.7, %l.8
  store i1 %i.9, ptr %t3.a.10
  %l.11 = load i1, ptr %t3.a.10
  br i1 %l.11, label %while_body1, label %while_exit2
while_body1:
  store i64 1, ptr %t4.a.12
  %l.13 = load i64, ptr %i.a.5
  %l.14 = load i64, ptr %t4.a.12
  %i.15 = add nsw i64 %l.13, %l.14
  store i64 %i.15, ptr %t5.a.16
  %l.17 = load i64, ptr %t5.a.16
  store i64 %l.17, ptr %i.a.5
  store i64 2, ptr %t6.a.18
  %l.19 = load i64, ptr %i.a.5
  %l.20 = load i64, ptr %t6.a.18
  %i.21 = srem i64 %l.19, %l.20
  store i64 %i.21, ptr %t7.a.22
  store i64 0, ptr %t8.a.23
  %l.24 = load i64, ptr %t7.a.22
  %l.25 = load i64, ptr %t8.a.23
  %i.26 = icmp eq i64 %l.24, %l.25
  store i1 %i.26, ptr %t9.a.27
  %l.28 = load i1, ptr %t9.a.27
  br i1 %l.28, label %if_then3, label %if_else4
while_exit2:
  %l.29 = load i64, ptr %sum.a.2
  ret i64 %l.29
if_then3:
  br label %while_header0
if_else4:
  br label %if_merge5
if_merge5:
  %l.30 = load i64, ptr %sum.a.2
  %l.31 = load i64, ptr %i.a.5
  %i.32 = add nsw i64 %l.30, %l.31
  store i64 %i.32, ptr %t11.a.33
  %l.34 = load i64, ptr %t11.a.33
  store i64 %l.34, ptr %sum.a.2
  br label %while_header0
}

define internal i64 @break_in_for() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %result.a.2 = alloca i64, align 8
  store i64 0, ptr %result.a.2
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %t2.a.4 = alloca i64, align 8
  store i64 0, ptr %t2.a.4
  %t3.a.8 = alloca ptr, align 8
  store ptr null, ptr %t3.a.8
  %has_next5.a.11 = alloca i1, align 8
  store i1 0, ptr %has_next5.a.11
  %next6.a.15 = alloca i64, align 8
  store i64 0, ptr %next6.a.15
  %t7.a.16 = alloca i64, align 8
  store i64 0, ptr %t7.a.16
  %t8.a.20 = alloca i1, align 8
  store i1 0, ptr %t8.a.20
  %range_free11.a.24 = alloca i1, align 8
  store i1 0, ptr %range_free11.a.24
  %t10.a.29 = alloca i64, align 8
  store i64 0, ptr %t10.a.29
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  store i64 %l.1, ptr %result.a.2
  store i64 0, ptr %t1.a.3
  store i64 100, ptr %t2.a.4
  %l.5 = load i64, ptr %t1.a.3
  %l.6 = load i64, ptr %t2.a.4
  %c.7 = call ptr @__mn_range(i64 %l.5, i64 %l.6)
  store ptr %c.7, ptr %t3.a.8
  br label %for_header0
for_header0:
  %l.9 = load ptr, ptr %t3.a.8
  %c.10 = call i1 @__iter_has_next(ptr %l.9)
  store i1 %c.10, ptr %has_next5.a.11
  %l.12 = load i1, ptr %has_next5.a.11
  br i1 %l.12, label %for_body1, label %for_exit2
for_body1:
  %l.13 = load ptr, ptr %t3.a.8
  %c.14 = call i64 @__iter_next(ptr %l.13)
  store i64 %c.14, ptr %next6.a.15
  store i64 5, ptr %t7.a.16
  %l.17 = load i64, ptr %next6.a.15
  %l.18 = load i64, ptr %t7.a.16
  %i.19 = icmp eq i64 %l.17, %l.18
  store i1 %i.19, ptr %t8.a.20
  %l.21 = load i1, ptr %t8.a.20
  br i1 %l.21, label %if_then3, label %if_else4
for_exit2:
  %l.22 = load ptr, ptr %t3.a.8
  %c.23 = call i1 @__mn_range_free(ptr %l.22)
  store i1 %c.23, ptr %range_free11.a.24
  %l.25 = load i64, ptr %result.a.2
  ret i64 %l.25
if_then3:
  br label %for_exit2
if_else4:
  br label %if_merge5
if_merge5:
  %l.26 = load i64, ptr %result.a.2
  %l.27 = load i64, ptr %next6.a.15
  %i.28 = add nsw i64 %l.26, %l.27
  store i64 %i.28, ptr %t10.a.29
  %l.30 = load i64, ptr %t10.a.29
  store i64 %l.30, ptr %result.a.2
  br label %for_header0
}

define internal i64 @nested_break() {
pre_entry:
  %t1.a.0 = alloca i64, align 8
  store i64 0, ptr %t1.a.0
  %found.a.2 = alloca i64, align 8
  store i64 0, ptr %found.a.2
  %t2.a.3 = alloca i64, align 8
  store i64 0, ptr %t2.a.3
  %t3.a.4 = alloca i64, align 8
  store i64 0, ptr %t3.a.4
  %t4.a.5 = alloca i64, align 8
  store i64 0, ptr %t4.a.5
  %t5.a.6 = alloca i64, align 8
  store i64 0, ptr %t5.a.6
  %t6.a.7 = alloca i64, align 8
  store i64 0, ptr %t6.a.7
  %lp.9 = alloca {ptr, i64, i64, i64, i64}, align 8
  %ea.11 = alloca i64, align 8
  %ea.14 = alloca i64, align 8
  %ea.17 = alloca i64, align 8
  %ea.20 = alloca i64, align 8
  %ea.23 = alloca i64, align 8
  %t7.a.26 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t7.a.26
  %t8.a.27 = alloca i64, align 8
  store i64 0, ptr %t8.a.27
  %t9.a.28 = alloca i64, align 8
  store i64 0, ptr %t9.a.28
  %t10.a.32 = alloca ptr, align 8
  store ptr null, ptr %t10.a.32
  %has_next12.a.35 = alloca i1, align 8
  store i1 0, ptr %has_next12.a.35
  %next13.a.39 = alloca i64, align 8
  store i64 0, ptr %next13.a.39
  %lp.42 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t14.a.45 = alloca i64, align 8
  store i64 0, ptr %t14.a.45
  %t15.a.46 = alloca i64, align 8
  store i64 0, ptr %t15.a.46
  %t16.a.50 = alloca i1, align 8
  store i1 0, ptr %t16.a.50
  %range_free18.a.54 = alloca i1, align 8
  store i1 0, ptr %range_free18.a.54
  br label %entry
entry:
  store i64 -1, ptr %t1.a.0
  %l.1 = load i64, ptr %t1.a.0
  store i64 %l.1, ptr %found.a.2
  store i64 10, ptr %t2.a.3
  store i64 20, ptr %t3.a.4
  store i64 30, ptr %t4.a.5
  store i64 40, ptr %t5.a.6
  store i64 50, ptr %t6.a.7
  %ln.8 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.8, ptr %lp.9
  %l.10 = load i64, ptr %t2.a.3
  store i64 %l.10, ptr %ea.11
  call void @__mn_list_push(ptr %lp.9, ptr %ea.11)
  %l.13 = load i64, ptr %t3.a.4
  store i64 %l.13, ptr %ea.14
  call void @__mn_list_push(ptr %lp.9, ptr %ea.14)
  %l.16 = load i64, ptr %t4.a.5
  store i64 %l.16, ptr %ea.17
  call void @__mn_list_push(ptr %lp.9, ptr %ea.17)
  %l.19 = load i64, ptr %t5.a.6
  store i64 %l.19, ptr %ea.20
  call void @__mn_list_push(ptr %lp.9, ptr %ea.20)
  %l.22 = load i64, ptr %t6.a.7
  store i64 %l.22, ptr %ea.23
  call void @__mn_list_push(ptr %lp.9, ptr %ea.23)
  %ll.25 = load {ptr, i64, i64, i64, i64}, ptr %lp.9
  store {ptr, i64, i64, i64, i64} %ll.25, ptr %t7.a.26
  store i64 0, ptr %t8.a.27
  store i64 5, ptr %t9.a.28
  %l.29 = load i64, ptr %t8.a.27
  %l.30 = load i64, ptr %t9.a.28
  %c.31 = call ptr @__mn_range(i64 %l.29, i64 %l.30)
  store ptr %c.31, ptr %t10.a.32
  br label %for_header0
for_header0:
  %l.33 = load ptr, ptr %t10.a.32
  %c.34 = call i1 @__iter_has_next(ptr %l.33)
  store i1 %c.34, ptr %has_next12.a.35
  %l.36 = load i1, ptr %has_next12.a.35
  br i1 %l.36, label %for_body1, label %for_exit2
for_body1:
  %l.37 = load ptr, ptr %t10.a.32
  %c.38 = call i64 @__iter_next(ptr %l.37)
  store i64 %c.38, ptr %next13.a.39
  %l.40 = load {ptr, i64, i64, i64, i64}, ptr %t7.a.26
  %l.41 = load i64, ptr %next13.a.39
  store {ptr, i64, i64, i64, i64} %l.40, ptr %lp.42
  %rt.43 = call ptr @__mn_list_get(ptr %lp.42, i64 %l.41)
  %el.44 = load i64, ptr %rt.43
  store i64 %el.44, ptr %t14.a.45
  store i64 30, ptr %t15.a.46
  %l.47 = load i64, ptr %t14.a.45
  %l.48 = load i64, ptr %t15.a.46
  %i.49 = icmp eq i64 %l.47, %l.48
  store i1 %i.49, ptr %t16.a.50
  %l.51 = load i1, ptr %t16.a.50
  br i1 %l.51, label %if_then3, label %if_else4
for_exit2:
  %l.52 = load ptr, ptr %t10.a.32
  %c.53 = call i1 @__mn_range_free(ptr %l.52)
  store i1 %c.53, ptr %range_free18.a.54
  %l.55 = load i64, ptr %found.a.2
  %drop.lv.56 = load {ptr, i64, i64, i64, i64}, ptr %t7.a.26
  %drop.lp.57 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.56, 0
  %drop.lnull.58 = icmp eq ptr %drop.lp.57, null
  br i1 %drop.lnull.58, label %drop.lskip.59, label %drop.lcheck.59
if_then3:
  %l.60 = load i64, ptr %next13.a.39
  store i64 %l.60, ptr %found.a.2
  br label %for_exit2
if_else4:
  br label %if_merge5
if_merge5:
  br label %for_header0
drop.lcheck.59:
  call void @__mn_list_free(ptr %t7.a.26)
  br label %drop.lskip.59
drop.lskip.59:
  ret i64 %l.55
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %t2.a.7 = alloca i1, align 8
  store i1 0, ptr %t2.a.7
  %t3.a.9 = alloca i64, align 8
  store i64 0, ptr %t3.a.9
  %t4.a.13 = alloca i1, align 8
  store i1 0, ptr %t4.a.13
  %t5.a.15 = alloca i64, align 8
  store i64 0, ptr %t5.a.15
  %t6.a.19 = alloca i1, align 8
  store i1 0, ptr %t6.a.19
  %t7.a.21 = alloca i64, align 8
  store i64 0, ptr %t7.a.21
  %t8.a.25 = alloca i1, align 8
  store i1 0, ptr %t8.a.25
  br label %entry
entry:
  store i64 5, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %c.2 = call i64 @sum_until(i64 %l.1)
  store i64 %c.2, ptr %t1.a.3
  %l.4 = load i64, ptr %t1.a.3
  %fp.5 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.6 = call i32 (ptr, ...) @printf(ptr %fp.5, i64 %l.4)
  store i1 0, ptr %t2.a.7
  %c.8 = call i64 @skip_evens()
  store i64 %c.8, ptr %t3.a.9
  %l.10 = load i64, ptr %t3.a.9
  %fp.11 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.12 = call i32 (ptr, ...) @printf(ptr %fp.11, i64 %l.10)
  store i1 0, ptr %t4.a.13
  %c.14 = call i64 @break_in_for()
  store i64 %c.14, ptr %t5.a.15
  %l.16 = load i64, ptr %t5.a.15
  %fp.17 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.18 = call i32 (ptr, ...) @printf(ptr %fp.17, i64 %l.16)
  store i1 0, ptr %t6.a.19
  %c.20 = call i64 @nested_break()
  store i64 %c.20, ptr %t7.a.21
  %l.22 = load i64, ptr %t7.a.21
  %fp.23 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.24 = call i32 (ptr, ...) @printf(ptr %fp.23, i64 %l.22)
  store i1 0, ptr %t8.a.25
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.33.0"}
