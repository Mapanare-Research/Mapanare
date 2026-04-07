; ModuleID = '25_fizzbuzz'
source_filename = "25_fizzbuzz"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [8 x i8] c"FizzBuzz", align 2
@.str.1 = private constant [4 x i8] c"Fizz", align 2
@.str.2 = private constant [4 x i8] c"Buzz", align 2

declare {ptr, i64} @__mn_str_from_int(i64)
declare ptr @__mn_range(i64, i64)
declare i1 @__iter_has_next(ptr)
declare i64 @__iter_next(ptr)
declare void @__mn_str_println({ptr, i64})
declare i1 @__mn_range_free(ptr)

define internal {ptr, i64} @fizzbuzz(i64 %n) {
pre_entry:
  %n.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  %t2.a.5 = alloca i64, align 8
  store i64 0, ptr %t2.a.5
  %t3.a.9 = alloca i1, align 8
  store i1 0, ptr %t3.a.9
  %t4.a.14 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.14
  %t6.a.16 = alloca i64, align 8
  store i64 0, ptr %t6.a.16
  %t7.a.20 = alloca i64, align 8
  store i64 0, ptr %t7.a.20
  %t8.a.21 = alloca i64, align 8
  store i64 0, ptr %t8.a.21
  %t9.a.25 = alloca i1, align 8
  store i1 0, ptr %t9.a.25
  %t10.a.30 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.30
  %t12.a.32 = alloca i64, align 8
  store i64 0, ptr %t12.a.32
  %t13.a.36 = alloca i64, align 8
  store i64 0, ptr %t13.a.36
  %t14.a.37 = alloca i64, align 8
  store i64 0, ptr %t14.a.37
  %t15.a.41 = alloca i1, align 8
  store i1 0, ptr %t15.a.41
  %t16.a.46 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t16.a.46
  %t18.a.50 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t18.a.50
  store i64 %n, ptr %n.addr
  br label %entry
entry:
  store i64 15, ptr %t0.a.0
  %l.1 = load i64, ptr %n.addr
  %l.2 = load i64, ptr %t0.a.0
  %i.3 = srem i64 %l.1, %l.2
  store i64 %i.3, ptr %t1.a.4
  store i64 0, ptr %t2.a.5
  %l.6 = load i64, ptr %t1.a.4
  %l.7 = load i64, ptr %t2.a.5
  %i.8 = icmp eq i64 %l.6, %l.7
  store i1 %i.8, ptr %t3.a.9
  %l.10 = load i1, ptr %t3.a.9
  br i1 %l.10, label %if_then0, label %if_else1
if_then0:
  %sp.11 = getelementptr inbounds [8 x i8], ptr @.str.0, i64 0, i64 0
  %s.12 = insertvalue {ptr, i64} undef, ptr %sp.11, 0
  %s.13 = insertvalue {ptr, i64} %s.12, i64 8, 1
  store {ptr, i64} %s.13, ptr %t4.a.14
  %l.15 = load {ptr, i64}, ptr %t4.a.14
  ret {ptr, i64} %l.15
if_else1:
  br label %if_merge2
if_merge2:
  store i64 3, ptr %t6.a.16
  %l.17 = load i64, ptr %n.addr
  %l.18 = load i64, ptr %t6.a.16
  %i.19 = srem i64 %l.17, %l.18
  store i64 %i.19, ptr %t7.a.20
  store i64 0, ptr %t8.a.21
  %l.22 = load i64, ptr %t7.a.20
  %l.23 = load i64, ptr %t8.a.21
  %i.24 = icmp eq i64 %l.22, %l.23
  store i1 %i.24, ptr %t9.a.25
  %l.26 = load i1, ptr %t9.a.25
  br i1 %l.26, label %if_then3, label %if_else4
if_then3:
  %sp.27 = getelementptr inbounds [4 x i8], ptr @.str.1, i64 0, i64 0
  %s.28 = insertvalue {ptr, i64} undef, ptr %sp.27, 0
  %s.29 = insertvalue {ptr, i64} %s.28, i64 4, 1
  store {ptr, i64} %s.29, ptr %t10.a.30
  %l.31 = load {ptr, i64}, ptr %t10.a.30
  ret {ptr, i64} %l.31
if_else4:
  br label %if_merge5
if_merge5:
  store i64 5, ptr %t12.a.32
  %l.33 = load i64, ptr %n.addr
  %l.34 = load i64, ptr %t12.a.32
  %i.35 = srem i64 %l.33, %l.34
  store i64 %i.35, ptr %t13.a.36
  store i64 0, ptr %t14.a.37
  %l.38 = load i64, ptr %t13.a.36
  %l.39 = load i64, ptr %t14.a.37
  %i.40 = icmp eq i64 %l.38, %l.39
  store i1 %i.40, ptr %t15.a.41
  %l.42 = load i1, ptr %t15.a.41
  br i1 %l.42, label %if_then6, label %if_else7
if_then6:
  %sp.43 = getelementptr inbounds [4 x i8], ptr @.str.2, i64 0, i64 0
  %s.44 = insertvalue {ptr, i64} undef, ptr %sp.43, 0
  %s.45 = insertvalue {ptr, i64} %s.44, i64 4, 1
  store {ptr, i64} %s.45, ptr %t16.a.46
  %l.47 = load {ptr, i64}, ptr %t16.a.46
  ret {ptr, i64} %l.47
if_else7:
  br label %if_merge8
if_merge8:
  %l.48 = load i64, ptr %n.addr
  %rt.49 = call {ptr, i64} @__mn_str_from_int(i64 %l.48)
  store {ptr, i64} %rt.49, ptr %t18.a.50
  %l.51 = load {ptr, i64}, ptr %t18.a.50
  ret {ptr, i64} %l.51
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.5 = alloca ptr, align 8
  store ptr null, ptr %t2.a.5
  %has_next4.a.8 = alloca i1, align 8
  store i1 0, ptr %has_next4.a.8
  %next5.a.12 = alloca i64, align 8
  store i64 0, ptr %next5.a.12
  %t6.a.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.15
  %t7.a.17 = alloca i1, align 8
  store i1 0, ptr %t7.a.17
  %range_free8.a.20 = alloca i1, align 8
  store i1 0, ptr %range_free8.a.20
  br label %entry
entry:
  store i64 1, ptr %t0.a.0
  store i64 16, ptr %t1.a.1
  %l.2 = load i64, ptr %t0.a.0
  %l.3 = load i64, ptr %t1.a.1
  %c.4 = call ptr @__mn_range(i64 %l.2, i64 %l.3)
  store ptr %c.4, ptr %t2.a.5
  br label %for_header0
for_header0:
  %l.6 = load ptr, ptr %t2.a.5
  %c.7 = call i1 @__iter_has_next(ptr %l.6)
  store i1 %c.7, ptr %has_next4.a.8
  %l.9 = load i1, ptr %has_next4.a.8
  br i1 %l.9, label %for_body1, label %for_exit2
for_body1:
  %l.10 = load ptr, ptr %t2.a.5
  %c.11 = call i64 @__iter_next(ptr %l.10)
  store i64 %c.11, ptr %next5.a.12
  %l.13 = load i64, ptr %next5.a.12
  %c.14 = call {ptr, i64} @fizzbuzz(i64 %l.13)
  store {ptr, i64} %c.14, ptr %t6.a.15
  %l.16 = load {ptr, i64}, ptr %t6.a.15
  call void @__mn_str_println({ptr, i64} %l.16)
  store i1 0, ptr %t7.a.17
  br label %for_header0
for_exit2:
  %l.18 = load ptr, ptr %t2.a.5
  %c.19 = call i1 @__mn_range_free(ptr %l.18)
  store i1 %c.19, ptr %range_free8.a.20
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.14.0"}
