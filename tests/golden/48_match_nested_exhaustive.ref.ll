; ModuleID = '48_match_nested_exhaustive'
source_filename = "48_match_nested_exhaustive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [0 x i8] c"", align 8
@.str.1 = private constant [4 x i8] c"ok: ", align 8
@.str.2 = private constant [5 x i8] c"err: ", align 8
@.str.3 = private constant [4 x i8] c"zero", align 8
@.str.4 = private constant [4 x i8] c"fail", align 8

declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_intern_destroy()

define internal {ptr, i64} @classify({i1, {i64, {ptr, i64}}} %x) {
pre_entry:
  %x.addr = alloca {i1, {i64, {ptr, i64}}}, align 8
  %tag0.a.3 = alloca i64, align 8
  store i64 0, ptr %tag0.a.3
  %match_result8.a.8 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %match_result8.a.8
  %v1.a.12 = alloca i64, align 8
  store i64 0, ptr %v1.a.12
  %t2.a.16 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.16
  %str_track.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.19
  %t3.a.20 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.20
  %str_track.24 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.24
  %t4.a.25 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.25
  %e5.a.29 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %e5.a.29
  %t6.a.33 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.33
  %str_track.37 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.37
  %t7.a.38 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t7.a.38
  store {i1, {i64, {ptr, i64}}} %x, ptr %x.addr
  br label %entry
entry:
  %l.0 = load {i1, {i64, {ptr, i64}}}, ptr %x.addr
  %et.1 = extractvalue {i1, {i64, {ptr, i64}}} %l.0, 0
  %etz.2 = zext i1 %et.1 to i64
  store i64 %etz.2, ptr %tag0.a.3
  %l.4 = load i64, ptr %tag0.a.3
  switch i64 %l.4, label %match_merge0 [
    i64 1, label %match_arm1
    i64 0, label %match_arm2
  ]
match_merge0:
  %sp.5 = getelementptr inbounds [0 x i8], ptr @.str.0, i64 0, i64 0
  %s.6 = insertvalue {ptr, i64} undef, ptr %sp.5, 0
  %s.7 = insertvalue {ptr, i64} %s.6, i64 0, 1
  store {ptr, i64} %s.7, ptr %match_result8.a.8
  %l.9 = load {ptr, i64}, ptr %match_result8.a.8
  ret {ptr, i64} %l.9
match_arm1:
  %l.10 = load {i1, {i64, {ptr, i64}}}, ptr %x.addr
  %ok.11 = extractvalue {i1, {i64, {ptr, i64}}} %l.10, 1, 0
  store i64 %ok.11, ptr %v1.a.12
  %sp.13 = getelementptr inbounds [4 x i8], ptr @.str.1, i64 0, i64 0
  %s.14 = insertvalue {ptr, i64} undef, ptr %sp.13, 0
  %s.15 = insertvalue {ptr, i64} %s.14, i64 4, 1
  store {ptr, i64} %s.15, ptr %t2.a.16
  %l.17 = load i64, ptr %v1.a.12
  %rt.18 = call {ptr, i64} @__mn_str_from_int(i64 %l.17)
  store {ptr, i64} %rt.18, ptr %str_track.19
  store {ptr, i64} %rt.18, ptr %t3.a.20
  %l.21 = load {ptr, i64}, ptr %t2.a.16
  %l.22 = load {ptr, i64}, ptr %t3.a.20
  %rt.23 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.21, {ptr, i64} %l.22)
  store {ptr, i64} %rt.23, ptr %str_track.24
  store {ptr, i64} %rt.23, ptr %t4.a.25
  %l.26 = load {ptr, i64}, ptr %t4.a.25
  ret {ptr, i64} %l.26
match_arm2:
  %l.27 = load {i1, {i64, {ptr, i64}}}, ptr %x.addr
  %er.28 = extractvalue {i1, {i64, {ptr, i64}}} %l.27, 1, 1
  store {ptr, i64} %er.28, ptr %e5.a.29
  %sp.30 = getelementptr inbounds [5 x i8], ptr @.str.2, i64 0, i64 0
  %s.31 = insertvalue {ptr, i64} undef, ptr %sp.30, 0
  %s.32 = insertvalue {ptr, i64} %s.31, i64 5, 1
  store {ptr, i64} %s.32, ptr %t6.a.33
  %l.34 = load {ptr, i64}, ptr %t6.a.33
  %l.35 = load {ptr, i64}, ptr %e5.a.29
  %rt.36 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.34, {ptr, i64} %l.35)
  store {ptr, i64} %rt.36, ptr %str_track.37
  store {ptr, i64} %rt.36, ptr %t7.a.38
  %l.39 = load {ptr, i64}, ptr %t7.a.38
  ret {ptr, i64} %l.39
}

define internal {i1, {i64, {ptr, i64}}} @try_divide(i64 %a, i64 %b) {
pre_entry:
  %a.addr = alloca i64, align 8
  %b.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i1, align 8
  store i1 0, ptr %t1.a.4
  %t2.a.9 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.9
  %t4.a.13 = alloca {i1, {ptr, {ptr, i64}}}, align 8
  store {i1, {ptr, {ptr, i64}}} zeroinitializer, ptr %t4.a.13
  %rc.15 = alloca {i1, {ptr, {ptr, i64}}}, align 8
  %t6.a.20 = alloca i64, align 8
  store i64 0, ptr %t6.a.20
  %t8.a.24 = alloca {i1, {i64, ptr}}, align 8
  store {i1, {i64, ptr}} zeroinitializer, ptr %t8.a.24
  %rc.26 = alloca {i1, {i64, {ptr, i64}}}, align 8
  store i64 %a, ptr %a.addr
  store i64 %b, ptr %b.addr
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %b.addr
  %l.2 = load i64, ptr %t0.a.0
  %i.3 = icmp eq i64 %l.1, %l.2
  store i1 %i.3, ptr %t1.a.4
  %l.5 = load i1, ptr %t1.a.4
  br i1 %l.5, label %if_then0, label %if_else1
if_then0:
  %sp.6 = getelementptr inbounds [4 x i8], ptr @.str.3, i64 0, i64 0
  %s.7 = insertvalue {ptr, i64} undef, ptr %sp.6, 0
  %s.8 = insertvalue {ptr, i64} %s.7, i64 4, 1
  store {ptr, i64} %s.8, ptr %t2.a.9
  %l.10 = load {ptr, i64}, ptr %t2.a.9
  %we.11 = insertvalue {i1, {ptr, {ptr, i64}}} undef, i1 0, 0
  %we.12 = insertvalue {i1, {ptr, {ptr, i64}}} %we.11, {ptr, i64} %l.10, 1, 1
  store {i1, {ptr, {ptr, i64}}} %we.12, ptr %t4.a.13
  %l.14 = load {i1, {ptr, {ptr, i64}}}, ptr %t4.a.13
  store {i1, {ptr, {ptr, i64}}} %l.14, ptr %rc.15
  %rv.16 = load {i1, {i64, {ptr, i64}}}, ptr %rc.15
  ret {i1, {i64, {ptr, i64}}} %rv.16
if_else1:
  br label %if_merge2
if_merge2:
  %l.17 = load i64, ptr %a.addr
  %l.18 = load i64, ptr %b.addr
  %i.19 = sdiv i64 %l.17, %l.18
  store i64 %i.19, ptr %t6.a.20
  %l.21 = load i64, ptr %t6.a.20
  %wo.22 = insertvalue {i1, {i64, ptr}} undef, i1 1, 0
  %wo.23 = insertvalue {i1, {i64, ptr}} %wo.22, i64 %l.21, 1, 0
  store {i1, {i64, ptr}} %wo.23, ptr %t8.a.24
  %l.25 = load {i1, {i64, ptr}}, ptr %t8.a.24
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %rc.26
  store {i1, {i64, ptr}} %l.25, ptr %rc.26
  %rv.27 = load {i1, {i64, {ptr, i64}}}, ptr %rc.26
  ret {i1, {i64, {ptr, i64}}} %rv.27
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.5 = alloca {i1, {i64, {ptr, i64}}}, align 8
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %t2.a.5
  %t3.a.8 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.8
  %t4.a.10 = alloca i1, align 8
  store i1 0, ptr %t4.a.10
  %t5.a.11 = alloca i64, align 8
  store i64 0, ptr %t5.a.11
  %t6.a.12 = alloca i64, align 8
  store i64 0, ptr %t6.a.12
  %t7.a.16 = alloca {i1, {i64, {ptr, i64}}}, align 8
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %t7.a.16
  %t8.a.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t8.a.19
  %t9.a.21 = alloca i1, align 8
  store i1 0, ptr %t9.a.21
  %t10.a.22 = alloca i64, align 8
  store i64 0, ptr %t10.a.22
  %t12.a.26 = alloca {i1, {i64, ptr}}, align 8
  store {i1, {i64, ptr}} zeroinitializer, ptr %t12.a.26
  %rc.28 = alloca {i1, {i64, {ptr, i64}}}, align 8
  %t13.a.31 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t13.a.31
  %t14.a.33 = alloca i1, align 8
  store i1 0, ptr %t14.a.33
  %t15.a.37 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t15.a.37
  %t17.a.41 = alloca {i1, {ptr, {ptr, i64}}}, align 8
  store {i1, {ptr, {ptr, i64}}} zeroinitializer, ptr %t17.a.41
  %rc.43 = alloca {i1, {ptr, {ptr, i64}}}, align 8
  %t18.a.46 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t18.a.46
  %t19.a.48 = alloca i1, align 8
  store i1 0, ptr %t19.a.48
  br label %entry
entry:
  store i64 10, ptr %t0.a.0
  store i64 2, ptr %t1.a.1
  %l.2 = load i64, ptr %t0.a.0
  %l.3 = load i64, ptr %t1.a.1
  %c.4 = call {i1, {i64, {ptr, i64}}} @try_divide(i64 %l.2, i64 %l.3)
  store {i1, {i64, {ptr, i64}}} %c.4, ptr %t2.a.5
  %l.6 = load {i1, {i64, {ptr, i64}}}, ptr %t2.a.5
  %c.7 = call {ptr, i64} @classify({i1, {i64, {ptr, i64}}} %l.6)
  store {ptr, i64} %c.7, ptr %t3.a.8
  %l.9 = load {ptr, i64}, ptr %t3.a.8
  call void @__mn_str_println({ptr, i64} %l.9)
  store i1 0, ptr %t4.a.10
  store i64 10, ptr %t5.a.11
  store i64 0, ptr %t6.a.12
  %l.13 = load i64, ptr %t5.a.11
  %l.14 = load i64, ptr %t6.a.12
  %c.15 = call {i1, {i64, {ptr, i64}}} @try_divide(i64 %l.13, i64 %l.14)
  store {i1, {i64, {ptr, i64}}} %c.15, ptr %t7.a.16
  %l.17 = load {i1, {i64, {ptr, i64}}}, ptr %t7.a.16
  %c.18 = call {ptr, i64} @classify({i1, {i64, {ptr, i64}}} %l.17)
  store {ptr, i64} %c.18, ptr %t8.a.19
  %l.20 = load {ptr, i64}, ptr %t8.a.19
  call void @__mn_str_println({ptr, i64} %l.20)
  store i1 0, ptr %t9.a.21
  store i64 42, ptr %t10.a.22
  %l.23 = load i64, ptr %t10.a.22
  %wo.24 = insertvalue {i1, {i64, ptr}} undef, i1 1, 0
  %wo.25 = insertvalue {i1, {i64, ptr}} %wo.24, i64 %l.23, 1, 0
  store {i1, {i64, ptr}} %wo.25, ptr %t12.a.26
  %l.27 = load {i1, {i64, ptr}}, ptr %t12.a.26
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %rc.28
  store {i1, {i64, ptr}} %l.27, ptr %rc.28
  %rv.29 = load {i1, {i64, {ptr, i64}}}, ptr %rc.28
  %c.30 = call {ptr, i64} @classify({i1, {i64, {ptr, i64}}} %rv.29)
  store {ptr, i64} %c.30, ptr %t13.a.31
  %l.32 = load {ptr, i64}, ptr %t13.a.31
  call void @__mn_str_println({ptr, i64} %l.32)
  store i1 0, ptr %t14.a.33
  %sp.34 = getelementptr inbounds [4 x i8], ptr @.str.4, i64 0, i64 0
  %s.35 = insertvalue {ptr, i64} undef, ptr %sp.34, 0
  %s.36 = insertvalue {ptr, i64} %s.35, i64 4, 1
  store {ptr, i64} %s.36, ptr %t15.a.37
  %l.38 = load {ptr, i64}, ptr %t15.a.37
  %we.39 = insertvalue {i1, {ptr, {ptr, i64}}} undef, i1 0, 0
  %we.40 = insertvalue {i1, {ptr, {ptr, i64}}} %we.39, {ptr, i64} %l.38, 1, 1
  store {i1, {ptr, {ptr, i64}}} %we.40, ptr %t17.a.41
  %l.42 = load {i1, {ptr, {ptr, i64}}}, ptr %t17.a.41
  store {i1, {ptr, {ptr, i64}}} %l.42, ptr %rc.43
  %rv.44 = load {i1, {i64, {ptr, i64}}}, ptr %rc.43
  %c.45 = call {ptr, i64} @classify({i1, {i64, {ptr, i64}}} %rv.44)
  store {ptr, i64} %c.45, ptr %t18.a.46
  %l.47 = load {ptr, i64}, ptr %t18.a.46
  call void @__mn_str_println({ptr, i64} %l.47)
  store i1 0, ptr %t19.a.48
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
