; ModuleID = '17_option'
source_filename = "17_option"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [4 x i8] c"none", align 2
@.str.1 = private constant [4 x i8] c"none", align 2

declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define internal {i1, i64} @find_positive(i64 %x) {
pre_entry:
  %x.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i1, align 8
  store i1 0, ptr %t1.a.4
  %t3.a.9 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t3.a.9
  %t5.a.11 = alloca i64, align 8
  store i64 0, ptr %t5.a.11
  %t7.a.15 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t7.a.15
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %x.addr
  %l.2 = load i64, ptr %t0.a.0
  %i.3 = icmp sgt i64 %l.1, %l.2
  store i1 %i.3, ptr %t1.a.4
  %l.5 = load i1, ptr %t1.a.4
  br i1 %l.5, label %if_then0, label %if_else1
if_then0:
  %l.6 = load i64, ptr %x.addr
  %ws.7 = insertvalue {i1, i64} undef, i1 1, 0
  %ws.8 = insertvalue {i1, i64} %ws.7, i64 %l.6, 1
  store {i1, i64} %ws.8, ptr %t3.a.9
  %l.10 = load {i1, i64}, ptr %t3.a.9
  ret {i1, i64} %l.10
if_else1:
  br label %if_merge2
if_merge2:
  store i64 0, ptr %t5.a.11
  %l.12 = load i64, ptr %t5.a.11
  %ws.13 = insertvalue {i1, i64} undef, i1 1, 0
  %ws.14 = insertvalue {i1, i64} %ws.13, i64 %l.12, 1
  store {i1, i64} %ws.14, ptr %t7.a.15
  %l.16 = load {i1, i64}, ptr %t7.a.15
  ret {i1, i64} %l.16
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.3 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t1.a.3
  %a.a.5 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %a.a.5
  %tag2.a.9 = alloca i64, align 8
  store i64 0, ptr %tag2.a.9
  %t9.a.11 = alloca i64, align 8
  store i64 0, ptr %t9.a.11
  %t11.a.15 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t11.a.15
  %b.a.17 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %b.a.17
  %tag12.a.21 = alloca i64, align 8
  store i64 0, ptr %tag12.a.21
  %v3.a.25 = alloca i64, align 8
  store i64 0, ptr %v3.a.25
  %t4.a.28 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.28
  %t5.a.30 = alloca i1, align 8
  store i1 0, ptr %t5.a.30
  %t6.a.34 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.34
  %t7.a.36 = alloca i1, align 8
  store i1 0, ptr %t7.a.36
  %v13.a.39 = alloca i64, align 8
  store i64 0, ptr %v13.a.39
  %t14.a.42 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t14.a.42
  %t15.a.44 = alloca i1, align 8
  store i1 0, ptr %t15.a.44
  %t16.a.48 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t16.a.48
  %t17.a.50 = alloca i1, align 8
  store i1 0, ptr %t17.a.50
  br label %entry
entry:
  store i64 42, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %c.2 = call {i1, i64} @find_positive(i64 %l.1)
  store {i1, i64} %c.2, ptr %t1.a.3
  %l.4 = load {i1, i64}, ptr %t1.a.3
  store {i1, i64} %l.4, ptr %a.a.5
  %l.6 = load {i1, i64}, ptr %a.a.5
  %et.7 = extractvalue {i1, i64} %l.6, 0
  %etz.8 = zext i1 %et.7 to i64
  store i64 %etz.8, ptr %tag2.a.9
  %l.10 = load i64, ptr %tag2.a.9
  switch i64 %l.10, label %match_arm2 [
    i64 1, label %match_arm1
  ]
match_merge0:
  store i64 7, ptr %t9.a.11
  %l.12 = load i64, ptr %t9.a.11
  %ws.13 = insertvalue {i1, i64} undef, i1 1, 0
  %ws.14 = insertvalue {i1, i64} %ws.13, i64 %l.12, 1
  store {i1, i64} %ws.14, ptr %t11.a.15
  %l.16 = load {i1, i64}, ptr %t11.a.15
  store {i1, i64} %l.16, ptr %b.a.17
  %l.18 = load {i1, i64}, ptr %b.a.17
  %et.19 = extractvalue {i1, i64} %l.18, 0
  %etz.20 = zext i1 %et.19 to i64
  store i64 %etz.20, ptr %tag12.a.21
  %l.22 = load i64, ptr %tag12.a.21
  switch i64 %l.22, label %match_arm5 [
    i64 1, label %match_arm4
  ]
match_arm1:
  %l.23 = load {i1, i64}, ptr %a.a.5
  %sm.24 = extractvalue {i1, i64} %l.23, 1
  store i64 %sm.24, ptr %v3.a.25
  %l.26 = load i64, ptr %v3.a.25
  %rt.27 = call {ptr, i64} @__mn_str_from_int(i64 %l.26)
  store {ptr, i64} %rt.27, ptr %t4.a.28
  %l.29 = load {ptr, i64}, ptr %t4.a.28
  call void @__mn_str_println({ptr, i64} %l.29)
  store i1 0, ptr %t5.a.30
  br label %match_merge0
match_arm2:
  %sp.31 = getelementptr inbounds [4 x i8], ptr @.str.0, i64 0, i64 0
  %s.32 = insertvalue {ptr, i64} undef, ptr %sp.31, 0
  %s.33 = insertvalue {ptr, i64} %s.32, i64 4, 1
  store {ptr, i64} %s.33, ptr %t6.a.34
  %l.35 = load {ptr, i64}, ptr %t6.a.34
  call void @__mn_str_println({ptr, i64} %l.35)
  store i1 0, ptr %t7.a.36
  br label %match_merge0
match_merge3:
  ret i64 0
match_arm4:
  %l.37 = load {i1, i64}, ptr %b.a.17
  %sm.38 = extractvalue {i1, i64} %l.37, 1
  store i64 %sm.38, ptr %v13.a.39
  %l.40 = load i64, ptr %v13.a.39
  %rt.41 = call {ptr, i64} @__mn_str_from_int(i64 %l.40)
  store {ptr, i64} %rt.41, ptr %t14.a.42
  %l.43 = load {ptr, i64}, ptr %t14.a.42
  call void @__mn_str_println({ptr, i64} %l.43)
  store i1 0, ptr %t15.a.44
  br label %match_merge3
match_arm5:
  %sp.45 = getelementptr inbounds [4 x i8], ptr @.str.1, i64 0, i64 0
  %s.46 = insertvalue {ptr, i64} undef, ptr %sp.45, 0
  %s.47 = insertvalue {ptr, i64} %s.46, i64 4, 1
  store {ptr, i64} %s.47, ptr %t16.a.48
  %l.49 = load {ptr, i64}, ptr %t16.a.48
  call void @__mn_str_println({ptr, i64} %l.49)
  store i1 0, ptr %t17.a.50
  br label %match_merge3
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
