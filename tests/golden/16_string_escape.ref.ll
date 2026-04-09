; ModuleID = '16_string_escape'
source_filename = "16_string_escape"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"line1\0Aline2", align 2
@.str.1 = private constant [9 x i8] c"col1\09col2", align 2
@.str.2 = private constant [10 x i8] c"back\5Cslash", align 2

declare void @__mn_str_println({ptr, i64})

define i64 @main() {
pre_entry:
  %msg.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %msg.a.3
  %t1.a.5 = alloca i1, align 8
  store i1 0, ptr %t1.a.5
  %tab.a.9 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %tab.a.9
  %t3.a.11 = alloca i1, align 8
  store i1 0, ptr %t3.a.11
  %bs.a.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %bs.a.15
  %t5.a.17 = alloca i1, align 8
  store i1 0, ptr %t5.a.17
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [11 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 11, 1
  store {ptr, i64} %s.2, ptr %msg.a.3
  %l.4 = load {ptr, i64}, ptr %msg.a.3
  call void @__mn_str_println({ptr, i64} %l.4)
  store i1 0, ptr %t1.a.5
  %sp.6 = getelementptr inbounds [9 x i8], ptr @.str.1, i64 0, i64 0
  %s.7 = insertvalue {ptr, i64} undef, ptr %sp.6, 0
  %s.8 = insertvalue {ptr, i64} %s.7, i64 9, 1
  store {ptr, i64} %s.8, ptr %tab.a.9
  %l.10 = load {ptr, i64}, ptr %tab.a.9
  call void @__mn_str_println({ptr, i64} %l.10)
  store i1 0, ptr %t3.a.11
  %sp.12 = getelementptr inbounds [10 x i8], ptr @.str.2, i64 0, i64 0
  %s.13 = insertvalue {ptr, i64} undef, ptr %sp.12, 0
  %s.14 = insertvalue {ptr, i64} %s.13, i64 10, 1
  store {ptr, i64} %s.14, ptr %bs.a.15
  %l.16 = load {ptr, i64}, ptr %bs.a.15
  call void @__mn_str_println({ptr, i64} %l.16)
  store i1 0, ptr %t5.a.17
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.14.0"}
