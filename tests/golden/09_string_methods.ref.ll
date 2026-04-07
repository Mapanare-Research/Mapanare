; ModuleID = '09_string_methods'
source_filename = "09_string_methods"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"hello world", align 2
@.str.1 = private constant [5 x i8] c"world", align 2

declare i1 @__mn_str_contains({ptr, i64}, {ptr, i64})
declare {ptr, i64} @__mn_str_from_bool(i1)
declare void @__mn_str_println({ptr, i64})
declare {ptr, i64} @__mn_str_to_upper({ptr, i64})

define i64 @main() {
pre_entry:
  %s.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %s.a.3
  %t1.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.7
  %t2.a.11 = alloca i1, align 8
  store i1 0, ptr %t2.a.11
  %t3.a.14 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.14
  %t4.a.16 = alloca i1, align 8
  store i1 0, ptr %t4.a.16
  %t5.a.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.19
  %t6.a.21 = alloca i1, align 8
  store i1 0, ptr %t6.a.21
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [11 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 11, 1
  store {ptr, i64} %s.2, ptr %s.a.3
  %sp.4 = getelementptr inbounds [5 x i8], ptr @.str.1, i64 0, i64 0
  %s.5 = insertvalue {ptr, i64} undef, ptr %sp.4, 0
  %s.6 = insertvalue {ptr, i64} %s.5, i64 5, 1
  store {ptr, i64} %s.6, ptr %t1.a.7
  %l.8 = load {ptr, i64}, ptr %s.a.3
  %l.9 = load {ptr, i64}, ptr %t1.a.7
  %rt.10 = call i1 @__mn_str_contains({ptr, i64} %l.8, {ptr, i64} %l.9)
  store i1 %rt.10, ptr %t2.a.11
  %l.12 = load i1, ptr %t2.a.11
  %rt.13 = call {ptr, i64} @__mn_str_from_bool(i1 %l.12)
  store {ptr, i64} %rt.13, ptr %t3.a.14
  %l.15 = load {ptr, i64}, ptr %t3.a.14
  call void @__mn_str_println({ptr, i64} %l.15)
  store i1 0, ptr %t4.a.16
  %l.17 = load {ptr, i64}, ptr %s.a.3
  %rt.18 = call {ptr, i64} @__mn_str_to_upper({ptr, i64} %l.17)
  store {ptr, i64} %rt.18, ptr %t5.a.19
  %l.20 = load {ptr, i64}, ptr %t5.a.19
  call void @__mn_str_println({ptr, i64} %l.20)
  store i1 0, ptr %t6.a.21
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
