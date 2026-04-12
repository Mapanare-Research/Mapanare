; ModuleID = '47_try_operator'
source_filename = "47_try_operator"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [6 x i8] c"failed", align 8

declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal {i1, {i64, {ptr, i64}}} @might_fail(i1 %ok) {
pre_entry:
  %ok.addr = alloca i1, align 8
  %t0.a.1 = alloca i64, align 8
  store i64 0, ptr %t0.a.1
  %t2.a.5 = alloca {i1, {i64, ptr}}, align 8
  store {i1, {i64, ptr}} zeroinitializer, ptr %t2.a.5
  %rc.7 = alloca {i1, {i64, {ptr, i64}}}, align 8
  %t4.a.12 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.12
  %t6.a.16 = alloca {i1, {ptr, {ptr, i64}}}, align 8
  store {i1, {ptr, {ptr, i64}}} zeroinitializer, ptr %t6.a.16
  %rc.18 = alloca {i1, {ptr, {ptr, i64}}}, align 8
  store i1 %ok, ptr %ok.addr
  br label %entry
entry:
  %l.0 = load i1, ptr %ok.addr
  br i1 %l.0, label %if_then0, label %if_else1
if_then0:
  store i64 42, ptr %t0.a.1
  %l.2 = load i64, ptr %t0.a.1
  %wo.3 = insertvalue {i1, {i64, ptr}} undef, i1 1, 0
  %wo.4 = insertvalue {i1, {i64, ptr}} %wo.3, i64 %l.2, 1, 0
  store {i1, {i64, ptr}} %wo.4, ptr %t2.a.5
  %l.6 = load {i1, {i64, ptr}}, ptr %t2.a.5
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %rc.7
  store {i1, {i64, ptr}} %l.6, ptr %rc.7
  %rv.8 = load {i1, {i64, {ptr, i64}}}, ptr %rc.7
  ret {i1, {i64, {ptr, i64}}} %rv.8
if_else1:
  br label %if_merge2
if_merge2:
  %sp.9 = getelementptr inbounds [6 x i8], ptr @.str.0, i64 0, i64 0
  %s.10 = insertvalue {ptr, i64} undef, ptr %sp.9, 0
  %s.11 = insertvalue {ptr, i64} %s.10, i64 6, 1
  store {ptr, i64} %s.11, ptr %t4.a.12
  %l.13 = load {ptr, i64}, ptr %t4.a.12
  %we.14 = insertvalue {i1, {ptr, {ptr, i64}}} undef, i1 0, 0
  %we.15 = insertvalue {i1, {ptr, {ptr, i64}}} %we.14, {ptr, i64} %l.13, 1, 1
  store {i1, {ptr, {ptr, i64}}} %we.15, ptr %t6.a.16
  %l.17 = load {i1, {ptr, {ptr, i64}}}, ptr %t6.a.16
  store {i1, {ptr, {ptr, i64}}} %l.17, ptr %rc.18
  %rv.19 = load {i1, {i64, {ptr, i64}}}, ptr %rc.18
  ret {i1, {i64, {ptr, i64}}} %rv.19
}

define internal {i1, {i64, {ptr, i64}}} @do_work() {
pre_entry:
  %t0.a.0 = alloca i1, align 8
  store i1 0, ptr %t0.a.0
  %t1.a.3 = alloca {i1, {i64, {ptr, i64}}}, align 8
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %t1.a.3
  %tag2.a.7 = alloca i64, align 8
  store i64 0, ptr %tag2.a.7
  %t3.a.12 = alloca i64, align 8
  store i64 0, ptr %t3.a.12
  %t4.a.13 = alloca i64, align 8
  store i64 0, ptr %t4.a.13
  %t5.a.17 = alloca i64, align 8
  store i64 0, ptr %t5.a.17
  %t7.a.21 = alloca {i1, {i64, ptr}}, align 8
  store {i1, {i64, ptr}} zeroinitializer, ptr %t7.a.21
  %rc.23 = alloca {i1, {i64, {ptr, i64}}}, align 8
  br label %entry
entry:
  store i1 1, ptr %t0.a.0
  %l.1 = load i1, ptr %t0.a.0
  %c.2 = call {i1, {i64, {ptr, i64}}} @might_fail(i1 %l.1)
  store {i1, {i64, {ptr, i64}}} %c.2, ptr %t1.a.3
  %l.4 = load {i1, {i64, {ptr, i64}}}, ptr %t1.a.3
  %et.5 = extractvalue {i1, {i64, {ptr, i64}}} %l.4, 0
  %etz.6 = zext i1 %et.5 to i64
  store i64 %etz.6, ptr %tag2.a.7
  %l.8 = load i64, ptr %tag2.a.7
  %bc.9 = icmp ne i64 %l.8, 0
  br i1 %bc.9, label %prop_ok0, label %prop_err1
prop_ok0:
  %l.10 = load {i1, {i64, {ptr, i64}}}, ptr %t1.a.3
  %uw.11 = extractvalue {i1, {i64, {ptr, i64}}} %l.10, 1
  store i64 %uw.11, ptr %t3.a.12
  store i64 8, ptr %t4.a.13
  %l.14 = load i64, ptr %t3.a.12
  %l.15 = load i64, ptr %t4.a.13
  %i.16 = add nsw i64 %l.14, %l.15
  store i64 %i.16, ptr %t5.a.17
  %l.18 = load i64, ptr %t5.a.17
  %wo.19 = insertvalue {i1, {i64, ptr}} undef, i1 1, 0
  %wo.20 = insertvalue {i1, {i64, ptr}} %wo.19, i64 %l.18, 1, 0
  store {i1, {i64, ptr}} %wo.20, ptr %t7.a.21
  %l.22 = load {i1, {i64, ptr}}, ptr %t7.a.21
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %rc.23
  store {i1, {i64, ptr}} %l.22, ptr %rc.23
  %rv.24 = load {i1, {i64, {ptr, i64}}}, ptr %rc.23
  ret {i1, {i64, {ptr, i64}}} %rv.24
prop_err1:
  %l.25 = load {i1, {i64, {ptr, i64}}}, ptr %t1.a.3
  ret {i1, {i64, {ptr, i64}}} %l.25
}

define internal {i1, {i64, {ptr, i64}}} @do_work_fail() {
pre_entry:
  %t0.a.0 = alloca i1, align 8
  store i1 0, ptr %t0.a.0
  %t1.a.3 = alloca {i1, {i64, {ptr, i64}}}, align 8
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %t1.a.3
  %tag2.a.7 = alloca i64, align 8
  store i64 0, ptr %tag2.a.7
  %t3.a.12 = alloca i64, align 8
  store i64 0, ptr %t3.a.12
  %t4.a.13 = alloca i64, align 8
  store i64 0, ptr %t4.a.13
  %t5.a.17 = alloca i64, align 8
  store i64 0, ptr %t5.a.17
  %t7.a.21 = alloca {i1, {i64, ptr}}, align 8
  store {i1, {i64, ptr}} zeroinitializer, ptr %t7.a.21
  %rc.23 = alloca {i1, {i64, {ptr, i64}}}, align 8
  br label %entry
entry:
  store i1 0, ptr %t0.a.0
  %l.1 = load i1, ptr %t0.a.0
  %c.2 = call {i1, {i64, {ptr, i64}}} @might_fail(i1 %l.1)
  store {i1, {i64, {ptr, i64}}} %c.2, ptr %t1.a.3
  %l.4 = load {i1, {i64, {ptr, i64}}}, ptr %t1.a.3
  %et.5 = extractvalue {i1, {i64, {ptr, i64}}} %l.4, 0
  %etz.6 = zext i1 %et.5 to i64
  store i64 %etz.6, ptr %tag2.a.7
  %l.8 = load i64, ptr %tag2.a.7
  %bc.9 = icmp ne i64 %l.8, 0
  br i1 %bc.9, label %prop_ok0, label %prop_err1
prop_ok0:
  %l.10 = load {i1, {i64, {ptr, i64}}}, ptr %t1.a.3
  %uw.11 = extractvalue {i1, {i64, {ptr, i64}}} %l.10, 1
  store i64 %uw.11, ptr %t3.a.12
  store i64 8, ptr %t4.a.13
  %l.14 = load i64, ptr %t3.a.12
  %l.15 = load i64, ptr %t4.a.13
  %i.16 = add nsw i64 %l.14, %l.15
  store i64 %i.16, ptr %t5.a.17
  %l.18 = load i64, ptr %t5.a.17
  %wo.19 = insertvalue {i1, {i64, ptr}} undef, i1 1, 0
  %wo.20 = insertvalue {i1, {i64, ptr}} %wo.19, i64 %l.18, 1, 0
  store {i1, {i64, ptr}} %wo.20, ptr %t7.a.21
  %l.22 = load {i1, {i64, ptr}}, ptr %t7.a.21
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %rc.23
  store {i1, {i64, ptr}} %l.22, ptr %rc.23
  %rv.24 = load {i1, {i64, {ptr, i64}}}, ptr %rc.23
  ret {i1, {i64, {ptr, i64}}} %rv.24
prop_err1:
  %l.25 = load {i1, {i64, {ptr, i64}}}, ptr %t1.a.3
  ret {i1, {i64, {ptr, i64}}} %l.25
}

define i64 @main() {
pre_entry:
  %t0.a.1 = alloca {i1, {i64, {ptr, i64}}}, align 8
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %t0.a.1
  %r1.a.3 = alloca {i1, {i64, {ptr, i64}}}, align 8
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %r1.a.3
  %tag1.a.7 = alloca i64, align 8
  store i64 0, ptr %tag1.a.7
  %t8.a.10 = alloca {i1, {i64, {ptr, i64}}}, align 8
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %t8.a.10
  %r2.a.12 = alloca {i1, {i64, {ptr, i64}}}, align 8
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %r2.a.12
  %tag9.a.16 = alloca i64, align 8
  store i64 0, ptr %tag9.a.16
  %v2.a.20 = alloca i64, align 8
  store i64 0, ptr %v2.a.20
  %str_track.23 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.23
  %t3.a.24 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.24
  %t4.a.26 = alloca i1, align 8
  store i1 0, ptr %t4.a.26
  %e5.a.29 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %e5.a.29
  %t6.a.31 = alloca i1, align 8
  store i1 0, ptr %t6.a.31
  %v10.a.38 = alloca i64, align 8
  store i64 0, ptr %v10.a.38
  %str_track.41 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.41
  %t11.a.42 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t11.a.42
  %t12.a.44 = alloca i1, align 8
  store i1 0, ptr %t12.a.44
  %e13.a.47 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %e13.a.47
  %t14.a.49 = alloca i1, align 8
  store i1 0, ptr %t14.a.49
  br label %entry
entry:
  %c.0 = call {i1, {i64, {ptr, i64}}} @do_work()
  store {i1, {i64, {ptr, i64}}} %c.0, ptr %t0.a.1
  %l.2 = load {i1, {i64, {ptr, i64}}}, ptr %t0.a.1
  store {i1, {i64, {ptr, i64}}} %l.2, ptr %r1.a.3
  %l.4 = load {i1, {i64, {ptr, i64}}}, ptr %r1.a.3
  %et.5 = extractvalue {i1, {i64, {ptr, i64}}} %l.4, 0
  %etz.6 = zext i1 %et.5 to i64
  store i64 %etz.6, ptr %tag1.a.7
  %l.8 = load i64, ptr %tag1.a.7
  switch i64 %l.8, label %match_merge0 [
    i64 1, label %match_arm1
    i64 0, label %match_arm2
  ]
match_merge0:
  %c.9 = call {i1, {i64, {ptr, i64}}} @do_work_fail()
  store {i1, {i64, {ptr, i64}}} %c.9, ptr %t8.a.10
  %l.11 = load {i1, {i64, {ptr, i64}}}, ptr %t8.a.10
  store {i1, {i64, {ptr, i64}}} %l.11, ptr %r2.a.12
  %l.13 = load {i1, {i64, {ptr, i64}}}, ptr %r2.a.12
  %et.14 = extractvalue {i1, {i64, {ptr, i64}}} %l.13, 0
  %etz.15 = zext i1 %et.14 to i64
  store i64 %etz.15, ptr %tag9.a.16
  %l.17 = load i64, ptr %tag9.a.16
  switch i64 %l.17, label %match_merge3 [
    i64 1, label %match_arm4
    i64 0, label %match_arm5
  ]
match_arm1:
  %l.18 = load {i1, {i64, {ptr, i64}}}, ptr %r1.a.3
  %ok.19 = extractvalue {i1, {i64, {ptr, i64}}} %l.18, 1, 0
  store i64 %ok.19, ptr %v2.a.20
  %l.21 = load i64, ptr %v2.a.20
  %rt.22 = call {ptr, i64} @__mn_str_from_int(i64 %l.21)
  store {ptr, i64} %rt.22, ptr %str_track.23
  store {ptr, i64} %rt.22, ptr %t3.a.24
  %l.25 = load {ptr, i64}, ptr %t3.a.24
  call void @__mn_str_println({ptr, i64} %l.25)
  store i1 0, ptr %t4.a.26
  br label %match_merge0
match_arm2:
  %l.27 = load {i1, {i64, {ptr, i64}}}, ptr %r1.a.3
  %er.28 = extractvalue {i1, {i64, {ptr, i64}}} %l.27, 1, 1
  store {ptr, i64} %er.28, ptr %e5.a.29
  %l.30 = load {ptr, i64}, ptr %e5.a.29
  call void @__mn_str_println({ptr, i64} %l.30)
  store i1 0, ptr %t6.a.31
  br label %match_merge0
match_merge3:
  %drop.s.32 = load {ptr, i64}, ptr %str_track.23
  %drop.p.33 = extractvalue {ptr, i64} %drop.s.32, 0
  %drop.null.34 = icmp eq ptr %drop.p.33, null
  br i1 %drop.null.34, label %drop.skip.35, label %drop.check.35
match_arm4:
  %l.36 = load {i1, {i64, {ptr, i64}}}, ptr %r2.a.12
  %ok.37 = extractvalue {i1, {i64, {ptr, i64}}} %l.36, 1, 0
  store i64 %ok.37, ptr %v10.a.38
  %l.39 = load i64, ptr %v10.a.38
  %rt.40 = call {ptr, i64} @__mn_str_from_int(i64 %l.39)
  store {ptr, i64} %rt.40, ptr %str_track.41
  store {ptr, i64} %rt.40, ptr %t11.a.42
  %l.43 = load {ptr, i64}, ptr %t11.a.42
  call void @__mn_str_println({ptr, i64} %l.43)
  store i1 0, ptr %t12.a.44
  br label %match_merge3
match_arm5:
  %l.45 = load {i1, {i64, {ptr, i64}}}, ptr %r2.a.12
  %er.46 = extractvalue {i1, {i64, {ptr, i64}}} %l.45, 1, 1
  store {ptr, i64} %er.46, ptr %e13.a.47
  %l.48 = load {ptr, i64}, ptr %e13.a.47
  call void @__mn_str_println({ptr, i64} %l.48)
  store i1 0, ptr %t14.a.49
  br label %match_merge3
drop.check.35:
  call void @__mn_str_free({ptr, i64} %drop.s.32)
  br label %drop.skip.35
drop.skip.35:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.32.0"}
