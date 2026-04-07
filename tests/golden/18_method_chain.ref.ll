; ModuleID = '18_method_chain'
source_filename = "18_method_chain"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [13 x i8] c"Hello, World!", align 2
@.str.1 = private constant [5 x i8] c"World", align 2
@.str.2 = private constant [5 x i8] c"World", align 2

declare {ptr, i64} @__mn_str_to_upper({ptr, i64})
declare void @__mn_str_println({ptr, i64})
declare i1 @__mn_str_contains({ptr, i64}, {ptr, i64})
declare {ptr, i64} @__mn_str_from_bool(i1)
declare i64 @__mn_str_find({ptr, i64}, {ptr, i64})
declare {ptr, i64} @__mn_str_from_int(i64)

define i64 @main() {
pre_entry:
  %s.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %s.a.3
  %t1.a.6 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.6
  %t2.a.8 = alloca i1, align 8
  store i1 0, ptr %t2.a.8
  %t3.a.12 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.12
  %t4.a.16 = alloca i1, align 8
  store i1 0, ptr %t4.a.16
  %t5.a.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.19
  %t6.a.21 = alloca i1, align 8
  store i1 0, ptr %t6.a.21
  %t7.a.25 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t7.a.25
  %t8.a.29 = alloca i64, align 8
  store i64 0, ptr %t8.a.29
  %t9.a.32 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t9.a.32
  %t10.a.34 = alloca i1, align 8
  store i1 0, ptr %t10.a.34
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [13 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 13, 1
  store {ptr, i64} %s.2, ptr %s.a.3
  %l.4 = load {ptr, i64}, ptr %s.a.3
  %rt.5 = call {ptr, i64} @__mn_str_to_upper({ptr, i64} %l.4)
  store {ptr, i64} %rt.5, ptr %t1.a.6
  %l.7 = load {ptr, i64}, ptr %t1.a.6
  call void @__mn_str_println({ptr, i64} %l.7)
  store i1 0, ptr %t2.a.8
  %sp.9 = getelementptr inbounds [5 x i8], ptr @.str.1, i64 0, i64 0
  %s.10 = insertvalue {ptr, i64} undef, ptr %sp.9, 0
  %s.11 = insertvalue {ptr, i64} %s.10, i64 5, 1
  store {ptr, i64} %s.11, ptr %t3.a.12
  %l.13 = load {ptr, i64}, ptr %s.a.3
  %l.14 = load {ptr, i64}, ptr %t3.a.12
  %rt.15 = call i1 @__mn_str_contains({ptr, i64} %l.13, {ptr, i64} %l.14)
  store i1 %rt.15, ptr %t4.a.16
  %l.17 = load i1, ptr %t4.a.16
  %rt.18 = call {ptr, i64} @__mn_str_from_bool(i1 %l.17)
  store {ptr, i64} %rt.18, ptr %t5.a.19
  %l.20 = load {ptr, i64}, ptr %t5.a.19
  call void @__mn_str_println({ptr, i64} %l.20)
  store i1 0, ptr %t6.a.21
  %sp.22 = getelementptr inbounds [5 x i8], ptr @.str.2, i64 0, i64 0
  %s.23 = insertvalue {ptr, i64} undef, ptr %sp.22, 0
  %s.24 = insertvalue {ptr, i64} %s.23, i64 5, 1
  store {ptr, i64} %s.24, ptr %t7.a.25
  %l.26 = load {ptr, i64}, ptr %s.a.3
  %l.27 = load {ptr, i64}, ptr %t7.a.25
  %rt.28 = call i64 @__mn_str_find({ptr, i64} %l.26, {ptr, i64} %l.27)
  store i64 %rt.28, ptr %t8.a.29
  %l.30 = load i64, ptr %t8.a.29
  %rt.31 = call {ptr, i64} @__mn_str_from_int(i64 %l.30)
  store {ptr, i64} %rt.31, ptr %t9.a.32
  %l.33 = load {ptr, i64}, ptr %t9.a.32
  call void @__mn_str_println({ptr, i64} %l.33)
  store i1 0, ptr %t10.a.34
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
