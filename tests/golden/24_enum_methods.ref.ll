; ModuleID = '24_enum_methods'
source_filename = "24_enum_methods"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [0 x i8] c"", align 8
@.str.1 = private constant [3 x i8] c"red", align 8
@.str.2 = private constant [5 x i8] c"green", align 8
@.str.3 = private constant [4 x i8] c"blue", align 8

declare void @__mn_str_println({ptr, i64})
declare void @__mn_intern_destroy()

define internal {ptr, i64} @color_name({i64, ptr} %c) {
pre_entry:
  %c.addr = alloca {i64, ptr}, align 8
  %tag0.a.2 = alloca i64, align 8
  store i64 0, ptr %tag0.a.2
  %match_result4.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %match_result4.a.7
  %t1.a.12 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.12
  %t2.a.17 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.17
  %t3.a.22 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.22
  store {i64, ptr} %c, ptr %c.addr
  br label %entry
entry:
  %l.0 = load {i64, ptr}, ptr %c.addr
  %et.1 = extractvalue {i64, ptr} %l.0, 0
  store i64 %et.1, ptr %tag0.a.2
  %l.3 = load i64, ptr %tag0.a.2
  switch i64 %l.3, label %match_merge0 [
    i64 0, label %match_arm1
    i64 1, label %match_arm2
    i64 2, label %match_arm3
  ]
match_merge0:
  %sp.4 = getelementptr inbounds [0 x i8], ptr @.str.0, i64 0, i64 0
  %s.5 = insertvalue {ptr, i64} undef, ptr %sp.4, 0
  %s.6 = insertvalue {ptr, i64} %s.5, i64 0, 1
  store {ptr, i64} %s.6, ptr %match_result4.a.7
  %l.8 = load {ptr, i64}, ptr %match_result4.a.7
  ret {ptr, i64} %l.8
match_arm1:
  %sp.9 = getelementptr inbounds [3 x i8], ptr @.str.1, i64 0, i64 0
  %s.10 = insertvalue {ptr, i64} undef, ptr %sp.9, 0
  %s.11 = insertvalue {ptr, i64} %s.10, i64 3, 1
  store {ptr, i64} %s.11, ptr %t1.a.12
  %l.13 = load {ptr, i64}, ptr %t1.a.12
  ret {ptr, i64} %l.13
match_arm2:
  %sp.14 = getelementptr inbounds [5 x i8], ptr @.str.2, i64 0, i64 0
  %s.15 = insertvalue {ptr, i64} undef, ptr %sp.14, 0
  %s.16 = insertvalue {ptr, i64} %s.15, i64 5, 1
  store {ptr, i64} %s.16, ptr %t2.a.17
  %l.18 = load {ptr, i64}, ptr %t2.a.17
  ret {ptr, i64} %l.18
match_arm3:
  %sp.19 = getelementptr inbounds [4 x i8], ptr @.str.3, i64 0, i64 0
  %s.20 = insertvalue {ptr, i64} undef, ptr %sp.19, 0
  %s.21 = insertvalue {ptr, i64} %s.20, i64 4, 1
  store {ptr, i64} %s.21, ptr %t3.a.22
  %l.23 = load {ptr, i64}, ptr %t3.a.22
  ret {ptr, i64} %l.23
}

define i64 @main() {
pre_entry:
  %t0.a.2 = alloca {i64, ptr}, align 8
  store {i64, ptr} zeroinitializer, ptr %t0.a.2
  %t1.a.5 = alloca {i64, ptr}, align 8
  store {i64, ptr} zeroinitializer, ptr %t1.a.5
  %t2.a.8 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.8
  %t3.a.10 = alloca i1, align 8
  store i1 0, ptr %t3.a.10
  %t4.a.13 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.13
  %t5.a.15 = alloca i1, align 8
  store i1 0, ptr %t5.a.15
  br label %entry
entry:
  %ei.0 = insertvalue {i64, ptr} undef, i64 0, 0
  %ei.1 = insertvalue {i64, ptr} %ei.0, ptr null, 1
  store {i64, ptr} %ei.1, ptr %t0.a.2
  %ei.3 = insertvalue {i64, ptr} undef, i64 2, 0
  %ei.4 = insertvalue {i64, ptr} %ei.3, ptr null, 1
  store {i64, ptr} %ei.4, ptr %t1.a.5
  %l.6 = load {i64, ptr}, ptr %t0.a.2
  %c.7 = call {ptr, i64} @color_name({i64, ptr} %l.6)
  store {ptr, i64} %c.7, ptr %t2.a.8
  %l.9 = load {ptr, i64}, ptr %t2.a.8
  call void @__mn_str_println({ptr, i64} %l.9)
  store i1 0, ptr %t3.a.10
  %l.11 = load {i64, ptr}, ptr %t1.a.5
  %c.12 = call {ptr, i64} @color_name({i64, ptr} %l.11)
  store {ptr, i64} %c.12, ptr %t4.a.13
  %l.14 = load {ptr, i64}, ptr %t4.a.13
  call void @__mn_str_println({ptr, i64} %l.14)
  store i1 0, ptr %t5.a.15
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.32.0"}
