; ModuleID = '22_string_builder'
source_filename = "22_string_builder"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [0 x i8] c"", align 2
@.str.1 = private constant [1 x i8] c"*", align 2
@.str.2 = private constant [1 x i8] c"-", align 2

declare ptr @__mn_range(i64, i64)
declare i1 @__iter_has_next(ptr)
declare i64 @__iter_next(ptr)
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64})
declare void @__mn_str_println({ptr, i64})

define internal {ptr, i64} @repeat_str({ptr, i64} %s, i64 %n) {
pre_entry:
  %s.addr = alloca {ptr, i64}, align 8
  %n.addr = alloca i64, align 8
  %result.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %result.a.3
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  %t2.a.8 = alloca ptr, align 8
  store ptr null, ptr %t2.a.8
  %has_next4.a.11 = alloca i1, align 8
  store i1 0, ptr %has_next4.a.11
  %next5.a.15 = alloca i64, align 8
  store i64 0, ptr %next5.a.15
  %t6.a.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.19
  store {ptr, i64} %s, ptr %s.addr
  store i64 %n, ptr %n.addr
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [0 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 0, 1
  store {ptr, i64} %s.2, ptr %result.a.3
  store i64 0, ptr %t1.a.4
  %l.5 = load i64, ptr %t1.a.4
  %l.6 = load i64, ptr %n.addr
  %c.7 = call ptr @__mn_range(i64 %l.5, i64 %l.6)
  store ptr %c.7, ptr %t2.a.8
  br label %for_header0
for_header0:
  %l.9 = load ptr, ptr %t2.a.8
  %c.10 = call i1 @__iter_has_next(ptr %l.9)
  store i1 %c.10, ptr %has_next4.a.11
  %l.12 = load i1, ptr %has_next4.a.11
  br i1 %l.12, label %for_body1, label %for_exit2
for_body1:
  %l.13 = load ptr, ptr %t2.a.8
  %c.14 = call i64 @__iter_next(ptr %l.13)
  store i64 %c.14, ptr %next5.a.15
  %l.16 = load {ptr, i64}, ptr %result.a.3
  %l.17 = load {ptr, i64}, ptr %s.addr
  %rt.18 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.16, {ptr, i64} %l.17)
  store {ptr, i64} %rt.18, ptr %t6.a.19
  %l.20 = load {ptr, i64}, ptr %t6.a.19
  store {ptr, i64} %l.20, ptr %result.a.3
  br label %for_header0
for_exit2:
  %l.21 = load {ptr, i64}, ptr %result.a.3
  ret {ptr, i64} %l.21
}

define i64 @main() {
pre_entry:
  %t0.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t0.a.3
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  %t2.a.8 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.8
  %t3.a.10 = alloca i1, align 8
  store i1 0, ptr %t3.a.10
  %t4.a.14 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.14
  %t5.a.15 = alloca i64, align 8
  store i64 0, ptr %t5.a.15
  %t6.a.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.19
  %t7.a.21 = alloca i1, align 8
  store i1 0, ptr %t7.a.21
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [1 x i8], ptr @.str.1, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 1, 1
  store {ptr, i64} %s.2, ptr %t0.a.3
  store i64 5, ptr %t1.a.4
  %l.5 = load {ptr, i64}, ptr %t0.a.3
  %l.6 = load i64, ptr %t1.a.4
  %c.7 = call {ptr, i64} @repeat_str({ptr, i64} %l.5, i64 %l.6)
  store {ptr, i64} %c.7, ptr %t2.a.8
  %l.9 = load {ptr, i64}, ptr %t2.a.8
  call void @__mn_str_println({ptr, i64} %l.9)
  store i1 0, ptr %t3.a.10
  %sp.11 = getelementptr inbounds [1 x i8], ptr @.str.2, i64 0, i64 0
  %s.12 = insertvalue {ptr, i64} undef, ptr %sp.11, 0
  %s.13 = insertvalue {ptr, i64} %s.12, i64 1, 1
  store {ptr, i64} %s.13, ptr %t4.a.14
  store i64 3, ptr %t5.a.15
  %l.16 = load {ptr, i64}, ptr %t4.a.14
  %l.17 = load i64, ptr %t5.a.15
  %c.18 = call {ptr, i64} @repeat_str({ptr, i64} %l.16, i64 %l.17)
  store {ptr, i64} %c.18, ptr %t6.a.19
  %l.20 = load {ptr, i64}, ptr %t6.a.19
  call void @__mn_str_println({ptr, i64} %l.20)
  store i1 0, ptr %t7.a.21
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
