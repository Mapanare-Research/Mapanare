; ModuleID = '07_enum_match'
source_filename = "07_enum_match"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [5 x i8] c"green", align 8
@.str.1 = private constant [5 x i8] c"other", align 8

declare void @__mn_str_println({ptr, i64})
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.2 = alloca {i64, ptr}, align 8
  store {i64, ptr} zeroinitializer, ptr %t0.a.2
  %c.a.4 = alloca {i64, ptr}, align 8
  store {i64, ptr} zeroinitializer, ptr %c.a.4
  %tag1.a.7 = alloca i64, align 8
  store i64 0, ptr %tag1.a.7
  %t2.a.12 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.12
  %t3.a.14 = alloca i1, align 8
  store i1 0, ptr %t3.a.14
  %t4.a.18 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.18
  %t5.a.20 = alloca i1, align 8
  store i1 0, ptr %t5.a.20
  br label %entry
entry:
  %ei.0 = insertvalue {i64, ptr} undef, i64 1, 0
  %ei.1 = insertvalue {i64, ptr} %ei.0, ptr null, 1
  store {i64, ptr} %ei.1, ptr %t0.a.2
  %l.3 = load {i64, ptr}, ptr %t0.a.2
  store {i64, ptr} %l.3, ptr %c.a.4
  %l.5 = load {i64, ptr}, ptr %c.a.4
  %et.6 = extractvalue {i64, ptr} %l.5, 0
  store i64 %et.6, ptr %tag1.a.7
  %l.8 = load i64, ptr %tag1.a.7
  switch i64 %l.8, label %match_arm2 [
    i64 1, label %match_arm1
  ]
match_merge0:
  call void @__mn_intern_destroy()
  ret i64 0
match_arm1:
  %sp.9 = getelementptr inbounds [5 x i8], ptr @.str.0, i64 0, i64 0
  %s.10 = insertvalue {ptr, i64} undef, ptr %sp.9, 0
  %s.11 = insertvalue {ptr, i64} %s.10, i64 5, 1
  store {ptr, i64} %s.11, ptr %t2.a.12
  %l.13 = load {ptr, i64}, ptr %t2.a.12
  call void @__mn_str_println({ptr, i64} %l.13)
  store i1 0, ptr %t3.a.14
  br label %match_merge0
match_arm2:
  %sp.15 = getelementptr inbounds [5 x i8], ptr @.str.1, i64 0, i64 0
  %s.16 = insertvalue {ptr, i64} undef, ptr %sp.15, 0
  %s.17 = insertvalue {ptr, i64} %s.16, i64 5, 1
  store {ptr, i64} %s.17, ptr %t4.a.18
  %l.19 = load {ptr, i64}, ptr %t4.a.18
  call void @__mn_str_println({ptr, i64} %l.19)
  store i1 0, ptr %t5.a.20
  br label %match_merge0
}


!mapanare.version = !{!0}
!0 = !{!"4.33.0"}
