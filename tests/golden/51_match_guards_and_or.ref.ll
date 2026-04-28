; ModuleID = '51_match_guards_and_or'
source_filename = "51_match_guards_and_or"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [14 x i8] c"zero or absent", align 8
@.str.1 = private constant [11 x i8] c"unreachable", align 8
@.str.2 = private constant [14 x i8] c"small positive", align 8
@.str.3 = private constant [14 x i8] c"large positive", align 8
@.str.4 = private constant [8 x i8] c"negative", align 8

declare void @__mn_str_println({ptr, i64})
declare void @__mn_intern_destroy()

define internal {ptr, i64} @describe({i1, i64} %opt) nounwind willreturn {
pre_entry:
  %opt.addr = alloca {i1, i64}, align 8
  %phi.match_result22 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %phi.match_result22
  %tag0.a.3 = alloca i64, align 8
  store i64 0, ptr %tag0.a.3
  %t3.a.9 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.9
  %x4.a.12 = alloca i64, align 8
  store i64 0, ptr %x4.a.12
  %t5.a.13 = alloca i64, align 8
  store i64 0, ptr %t5.a.13
  %t6.a.17 = alloca i1, align 8
  store i1 0, ptr %t6.a.17
  %t7.a.18 = alloca i64, align 8
  store i64 0, ptr %t7.a.18
  %t8.a.22 = alloca i1, align 8
  store i1 0, ptr %t8.a.22
  %t9.a.26 = alloca i1, align 8
  store i1 0, ptr %t9.a.26
  %x12.a.30 = alloca i64, align 8
  store i64 0, ptr %x12.a.30
  %t13.a.31 = alloca i64, align 8
  store i64 0, ptr %t13.a.31
  %t14.a.35 = alloca i1, align 8
  store i1 0, ptr %t14.a.35
  %x17.a.39 = alloca i64, align 8
  store i64 0, ptr %x17.a.39
  %t18.a.40 = alloca i64, align 8
  store i64 0, ptr %t18.a.40
  %t19.a.44 = alloca i1, align 8
  store i1 0, ptr %t19.a.44
  %t21.a.49 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t21.a.49
  %pay_01.a.52 = alloca i64, align 8
  store i64 0, ptr %pay_01.a.52
  %tag2.a.54 = alloca i64, align 8
  store i64 0, ptr %tag2.a.54
  %t11.a.59 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t11.a.59
  %tag10.a.63 = alloca i64, align 8
  store i64 0, ptr %tag10.a.63
  %t16.a.68 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t16.a.68
  %tag15.a.72 = alloca i64, align 8
  store i64 0, ptr %tag15.a.72
  %t20.a.77 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t20.a.77
  store {i1, i64} %opt, ptr %opt.addr
  br label %entry
entry:
  %l.0 = load {i1, i64}, ptr %opt.addr
  %et.1 = extractvalue {i1, i64} %l.0, 0
  %etz.2 = zext i1 %et.1 to i64
  store i64 %etz.2, ptr %tag0.a.3
  %l.4 = load i64, ptr %tag0.a.3
  switch i64 %l.4, label %match_merge0 [
    i64 1, label %match_case_Some6
    i64 0, label %match_case_None7
  ]
match_merge0:
  %l.5 = load {ptr, i64}, ptr %phi.match_result22
  ret {ptr, i64} %l.5
match_arm1:
  %sp.6 = getelementptr inbounds [14 x i8], ptr @.str.0, i64 0, i64 0
  %s.7 = insertvalue {ptr, i64} undef, ptr %sp.6, 0
  %s.8 = insertvalue {ptr, i64} %s.7, i64 14, 1
  store {ptr, i64} %s.8, ptr %t3.a.9
  %ps.78 = load {ptr, i64}, ptr %t3.a.9
  store {ptr, i64} %ps.78, ptr %phi.match_result22
  br label %match_merge0
match_arm2:
  %l.10 = load {i1, i64}, ptr %opt.addr
  %sm.11 = extractvalue {i1, i64} %l.10, 1
  store i64 %sm.11, ptr %x4.a.12
  store i64 0, ptr %t5.a.13
  %l.14 = load i64, ptr %x4.a.12
  %l.15 = load i64, ptr %t5.a.13
  %i.16 = icmp sgt i64 %l.14, %l.15
  store i1 %i.16, ptr %t6.a.17
  store i64 10, ptr %t7.a.18
  %l.19 = load i64, ptr %x4.a.12
  %l.20 = load i64, ptr %t7.a.18
  %i.21 = icmp slt i64 %l.19, %l.20
  store i1 %i.21, ptr %t8.a.22
  %l.23 = load i1, ptr %t6.a.17
  %l.24 = load i1, ptr %t8.a.22
  %bl.25 = and i1 %l.23, %l.24
  store i1 %bl.25, ptr %t9.a.26
  %l.27 = load i1, ptr %t9.a.26
  br i1 %l.27, label %guard_pass10, label %guard_fail11
match_arm3:
  %l.28 = load {i1, i64}, ptr %opt.addr
  %sm.29 = extractvalue {i1, i64} %l.28, 1
  store i64 %sm.29, ptr %x12.a.30
  store i64 0, ptr %t13.a.31
  %l.32 = load i64, ptr %x12.a.30
  %l.33 = load i64, ptr %t13.a.31
  %i.34 = icmp sgt i64 %l.32, %l.33
  store i1 %i.34, ptr %t14.a.35
  %l.36 = load i1, ptr %t14.a.35
  br i1 %l.36, label %guard_pass12, label %guard_fail13
match_arm4:
  %l.37 = load {i1, i64}, ptr %opt.addr
  %sm.38 = extractvalue {i1, i64} %l.37, 1
  store i64 %sm.38, ptr %x17.a.39
  store i64 0, ptr %t18.a.40
  %l.41 = load i64, ptr %x17.a.39
  %l.42 = load i64, ptr %t18.a.40
  %i.43 = icmp slt i64 %l.41, %l.42
  store i1 %i.43, ptr %t19.a.44
  %l.45 = load i1, ptr %t19.a.44
  br i1 %l.45, label %guard_pass14, label %guard_fail15
match_arm5:
  %sp.46 = getelementptr inbounds [11 x i8], ptr @.str.1, i64 0, i64 0
  %s.47 = insertvalue {ptr, i64} undef, ptr %sp.46, 0
  %s.48 = insertvalue {ptr, i64} %s.47, i64 11, 1
  store {ptr, i64} %s.48, ptr %t21.a.49
  %ps.82 = load {ptr, i64}, ptr %t21.a.49
  store {ptr, i64} %ps.82, ptr %phi.match_result22
  br label %match_merge0
match_case_Some6:
  %l.50 = load {i1, i64}, ptr %opt.addr
  %sm.51 = extractvalue {i1, i64} %l.50, 1
  store i64 %sm.51, ptr %pay_01.a.52
  %l.53 = load i64, ptr %pay_01.a.52
  store i64 %l.53, ptr %tag2.a.54
  %l.55 = load i64, ptr %tag2.a.54
  switch i64 %l.55, label %match_default9 [
    i64 0, label %match_case_08
  ]
match_case_None7:
  br label %match_arm1
match_case_08:
  br label %match_arm1
match_default9:
  br label %match_arm2
guard_pass10:
  %sp.56 = getelementptr inbounds [14 x i8], ptr @.str.2, i64 0, i64 0
  %s.57 = insertvalue {ptr, i64} undef, ptr %sp.56, 0
  %s.58 = insertvalue {ptr, i64} %s.57, i64 14, 1
  store {ptr, i64} %s.58, ptr %t11.a.59
  %ps.79 = load {ptr, i64}, ptr %t11.a.59
  store {ptr, i64} %ps.79, ptr %phi.match_result22
  br label %match_merge0
guard_fail11:
  %l.60 = load {i1, i64}, ptr %opt.addr
  %et.61 = extractvalue {i1, i64} %l.60, 0
  %etz.62 = zext i1 %et.61 to i64
  store i64 %etz.62, ptr %tag10.a.63
  %l.64 = load i64, ptr %tag10.a.63
  switch i64 %l.64, label %match_arm5 [
    i64 1, label %match_arm3
  ]
guard_pass12:
  %sp.65 = getelementptr inbounds [14 x i8], ptr @.str.3, i64 0, i64 0
  %s.66 = insertvalue {ptr, i64} undef, ptr %sp.65, 0
  %s.67 = insertvalue {ptr, i64} %s.66, i64 14, 1
  store {ptr, i64} %s.67, ptr %t16.a.68
  %ps.80 = load {ptr, i64}, ptr %t16.a.68
  store {ptr, i64} %ps.80, ptr %phi.match_result22
  br label %match_merge0
guard_fail13:
  %l.69 = load {i1, i64}, ptr %opt.addr
  %et.70 = extractvalue {i1, i64} %l.69, 0
  %etz.71 = zext i1 %et.70 to i64
  store i64 %etz.71, ptr %tag15.a.72
  %l.73 = load i64, ptr %tag15.a.72
  switch i64 %l.73, label %match_arm5 [
    i64 1, label %match_arm4
  ]
guard_pass14:
  %sp.74 = getelementptr inbounds [8 x i8], ptr @.str.4, i64 0, i64 0
  %s.75 = insertvalue {ptr, i64} undef, ptr %sp.74, 0
  %s.76 = insertvalue {ptr, i64} %s.75, i64 8, 1
  store {ptr, i64} %s.76, ptr %t20.a.77
  %ps.81 = load {ptr, i64}, ptr %t20.a.77
  store {ptr, i64} %ps.81, ptr %phi.match_result22
  br label %match_merge0
guard_fail15:
  br label %match_arm5
}

define i64 @main() nounwind willreturn {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t2.a.4 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t2.a.4
  %t3.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.7
  %t4.a.9 = alloca i1, align 8
  store i1 0, ptr %t4.a.9
  %t5.a.10 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t5.a.10
  %t6.a.13 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.13
  %t7.a.15 = alloca i1, align 8
  store i1 0, ptr %t7.a.15
  %t8.a.16 = alloca i64, align 8
  store i64 0, ptr %t8.a.16
  %t10.a.20 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t10.a.20
  %t11.a.23 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t11.a.23
  %t12.a.25 = alloca i1, align 8
  store i1 0, ptr %t12.a.25
  %t13.a.26 = alloca i64, align 8
  store i64 0, ptr %t13.a.26
  %t15.a.30 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t15.a.30
  %t16.a.33 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t16.a.33
  %t17.a.35 = alloca i1, align 8
  store i1 0, ptr %t17.a.35
  %t19.a.36 = alloca i64, align 8
  store i64 0, ptr %t19.a.36
  %t21.a.40 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t21.a.40
  %t22.a.43 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t22.a.43
  %t23.a.45 = alloca i1, align 8
  store i1 0, ptr %t23.a.45
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %ws.2 = insertvalue {i1, i64} undef, i1 1, 0
  %ws.3 = insertvalue {i1, i64} %ws.2, i64 %l.1, 1
  store {i1, i64} %ws.3, ptr %t2.a.4
  %l.5 = load {i1, i64}, ptr %t2.a.4
  %c.6 = call {ptr, i64} @describe({i1, i64} %l.5)
  store {ptr, i64} %c.6, ptr %t3.a.7
  %l.8 = load {ptr, i64}, ptr %t3.a.7
  call void @__mn_str_println({ptr, i64} %l.8)
  store i1 0, ptr %t4.a.9
  store {i1, i64} zeroinitializer, ptr %t5.a.10
  %l.11 = load {i1, i64}, ptr %t5.a.10
  %c.12 = call {ptr, i64} @describe({i1, i64} %l.11)
  store {ptr, i64} %c.12, ptr %t6.a.13
  %l.14 = load {ptr, i64}, ptr %t6.a.13
  call void @__mn_str_println({ptr, i64} %l.14)
  store i1 0, ptr %t7.a.15
  store i64 5, ptr %t8.a.16
  %l.17 = load i64, ptr %t8.a.16
  %ws.18 = insertvalue {i1, i64} undef, i1 1, 0
  %ws.19 = insertvalue {i1, i64} %ws.18, i64 %l.17, 1
  store {i1, i64} %ws.19, ptr %t10.a.20
  %l.21 = load {i1, i64}, ptr %t10.a.20
  %c.22 = call {ptr, i64} @describe({i1, i64} %l.21)
  store {ptr, i64} %c.22, ptr %t11.a.23
  %l.24 = load {ptr, i64}, ptr %t11.a.23
  call void @__mn_str_println({ptr, i64} %l.24)
  store i1 0, ptr %t12.a.25
  store i64 42, ptr %t13.a.26
  %l.27 = load i64, ptr %t13.a.26
  %ws.28 = insertvalue {i1, i64} undef, i1 1, 0
  %ws.29 = insertvalue {i1, i64} %ws.28, i64 %l.27, 1
  store {i1, i64} %ws.29, ptr %t15.a.30
  %l.31 = load {i1, i64}, ptr %t15.a.30
  %c.32 = call {ptr, i64} @describe({i1, i64} %l.31)
  store {ptr, i64} %c.32, ptr %t16.a.33
  %l.34 = load {ptr, i64}, ptr %t16.a.33
  call void @__mn_str_println({ptr, i64} %l.34)
  store i1 0, ptr %t17.a.35
  store i64 -1, ptr %t19.a.36
  %l.37 = load i64, ptr %t19.a.36
  %ws.38 = insertvalue {i1, i64} undef, i1 1, 0
  %ws.39 = insertvalue {i1, i64} %ws.38, i64 %l.37, 1
  store {i1, i64} %ws.39, ptr %t21.a.40
  %l.41 = load {i1, i64}, ptr %t21.a.40
  %c.42 = call {ptr, i64} @describe({i1, i64} %l.41)
  store {ptr, i64} %c.42, ptr %t22.a.43
  %l.44 = load {ptr, i64}, ptr %t22.a.43
  call void @__mn_str_println({ptr, i64} %l.44)
  store i1 0, ptr %t23.a.45
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"5.7.0"}
