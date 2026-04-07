; ModuleID = '10_result'
source_filename = "10_result"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [16 x i8] c"division by zero", align 2

declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define internal {i1, {i64, {ptr, i64}}} @divide(i64 %a, i64 %b) {
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
  %sp.6 = getelementptr inbounds [16 x i8], ptr @.str.0, i64 0, i64 0
  %s.7 = insertvalue {ptr, i64} undef, ptr %sp.6, 0
  %s.8 = insertvalue {ptr, i64} %s.7, i64 16, 1
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
  %r.a.7 = alloca {i1, {i64, {ptr, i64}}}, align 8
  store {i1, {i64, {ptr, i64}}} zeroinitializer, ptr %r.a.7
  %tag3.a.11 = alloca i64, align 8
  store i64 0, ptr %tag3.a.11
  %v4.a.15 = alloca i64, align 8
  store i64 0, ptr %v4.a.15
  %t5.a.18 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.18
  %t6.a.20 = alloca i1, align 8
  store i1 0, ptr %t6.a.20
  %e7.a.23 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %e7.a.23
  %t8.a.25 = alloca i1, align 8
  store i1 0, ptr %t8.a.25
  br label %entry
entry:
  store i64 10, ptr %t0.a.0
  store i64 2, ptr %t1.a.1
  %l.2 = load i64, ptr %t0.a.0
  %l.3 = load i64, ptr %t1.a.1
  %c.4 = call {i1, {i64, {ptr, i64}}} @divide(i64 %l.2, i64 %l.3)
  store {i1, {i64, {ptr, i64}}} %c.4, ptr %t2.a.5
  %l.6 = load {i1, {i64, {ptr, i64}}}, ptr %t2.a.5
  store {i1, {i64, {ptr, i64}}} %l.6, ptr %r.a.7
  %l.8 = load {i1, {i64, {ptr, i64}}}, ptr %r.a.7
  %et.9 = extractvalue {i1, {i64, {ptr, i64}}} %l.8, 0
  %etz.10 = zext i1 %et.9 to i64
  store i64 %etz.10, ptr %tag3.a.11
  %l.12 = load i64, ptr %tag3.a.11
  switch i64 %l.12, label %match_merge0 [
    i64 1, label %match_arm1
    i64 0, label %match_arm2
  ]
match_merge0:
  ret i64 0
match_arm1:
  %l.13 = load {i1, {i64, {ptr, i64}}}, ptr %r.a.7
  %ok.14 = extractvalue {i1, {i64, {ptr, i64}}} %l.13, 1, 0
  store i64 %ok.14, ptr %v4.a.15
  %l.16 = load i64, ptr %v4.a.15
  %rt.17 = call {ptr, i64} @__mn_str_from_int(i64 %l.16)
  store {ptr, i64} %rt.17, ptr %t5.a.18
  %l.19 = load {ptr, i64}, ptr %t5.a.18
  call void @__mn_str_println({ptr, i64} %l.19)
  store i1 0, ptr %t6.a.20
  br label %match_merge0
match_arm2:
  %l.21 = load {i1, {i64, {ptr, i64}}}, ptr %r.a.7
  %er.22 = extractvalue {i1, {i64, {ptr, i64}}} %l.21, 1, 1
  store {ptr, i64} %er.22, ptr %e7.a.23
  %l.24 = load {ptr, i64}, ptr %e7.a.23
  call void @__mn_str_println({ptr, i64} %l.24)
  store i1 0, ptr %t8.a.25
  br label %match_merge0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
