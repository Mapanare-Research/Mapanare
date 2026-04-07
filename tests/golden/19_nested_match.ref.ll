; ModuleID = '19_nested_match'
source_filename = "19_nested_match"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare ptr @malloc(i64)
declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define internal i64 @area({i64, ptr} %s) {
pre_entry:
  %s.addr = alloca {i64, ptr}, align 8
  %tag0.a.2 = alloca i64, align 8
  store i64 0, ptr %tag0.a.2
  %match_result8.a.4 = alloca i64, align 8
  store i64 0, ptr %match_result8.a.4
  %r1.a.10 = alloca i64, align 8
  store i64 0, ptr %r1.a.10
  %t2.a.14 = alloca i64, align 8
  store i64 0, ptr %t2.a.14
  %t3.a.15 = alloca i64, align 8
  store i64 0, ptr %t3.a.15
  %t4.a.19 = alloca i64, align 8
  store i64 0, ptr %t4.a.19
  %w5.a.25 = alloca i64, align 8
  store i64 0, ptr %w5.a.25
  %h6.a.30 = alloca i64, align 8
  store i64 0, ptr %h6.a.30
  %t7.a.34 = alloca i64, align 8
  store i64 0, ptr %t7.a.34
  store {i64, ptr} %s, ptr %s.addr
  br label %entry
entry:
  %l.0 = load {i64, ptr}, ptr %s.addr
  %et.1 = extractvalue {i64, ptr} %l.0, 0
  store i64 %et.1, ptr %tag0.a.2
  %l.3 = load i64, ptr %tag0.a.2
  switch i64 %l.3, label %match_merge0 [
    i64 0, label %match_arm1
    i64 1, label %match_arm2
  ]
match_merge0:
  store i64 0, ptr %match_result8.a.4
  %l.5 = load i64, ptr %match_result8.a.4
  ret i64 %l.5
match_arm1:
  %l.6 = load {i64, ptr}, ptr %s.addr
  %pr.7 = extractvalue {i64, ptr} %l.6, 1
  %pf.8 = getelementptr inbounds {i64}, ptr %pr.7, i32 0, i32 0
  %pv.9 = load i64, ptr %pf.8
  store i64 %pv.9, ptr %r1.a.10
  %l.11 = load i64, ptr %r1.a.10
  %l.12 = load i64, ptr %r1.a.10
  %i.13 = mul nsw i64 %l.11, %l.12
  store i64 %i.13, ptr %t2.a.14
  store i64 3, ptr %t3.a.15
  %l.16 = load i64, ptr %t2.a.14
  %l.17 = load i64, ptr %t3.a.15
  %i.18 = mul nsw i64 %l.16, %l.17
  store i64 %i.18, ptr %t4.a.19
  %l.20 = load i64, ptr %t4.a.19
  ret i64 %l.20
match_arm2:
  %l.21 = load {i64, ptr}, ptr %s.addr
  %pr.22 = extractvalue {i64, ptr} %l.21, 1
  %pf.23 = getelementptr inbounds {i64, i64}, ptr %pr.22, i32 0, i32 0
  %pv.24 = load i64, ptr %pf.23
  store i64 %pv.24, ptr %w5.a.25
  %l.26 = load {i64, ptr}, ptr %s.addr
  %pr.27 = extractvalue {i64, ptr} %l.26, 1
  %pf.28 = getelementptr inbounds {i64, i64}, ptr %pr.27, i32 0, i32 1
  %pv.29 = load i64, ptr %pf.28
  store i64 %pv.29, ptr %h6.a.30
  %l.31 = load i64, ptr %w5.a.25
  %l.32 = load i64, ptr %h6.a.30
  %i.33 = mul nsw i64 %l.31, %l.32
  store i64 %i.33, ptr %t7.a.34
  %l.35 = load i64, ptr %t7.a.34
  ret i64 %l.35
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t2.a.6 = alloca {i64, ptr}, align 8
  store {i64, ptr} zeroinitializer, ptr %t2.a.6
  %t3.a.9 = alloca i64, align 8
  store i64 0, ptr %t3.a.9
  %t4.a.12 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.12
  %t5.a.14 = alloca i1, align 8
  store i1 0, ptr %t5.a.14
  %t6.a.15 = alloca i64, align 8
  store i64 0, ptr %t6.a.15
  %t7.a.16 = alloca i64, align 8
  store i64 0, ptr %t7.a.16
  %t9.a.24 = alloca {i64, ptr}, align 8
  store {i64, ptr} zeroinitializer, ptr %t9.a.24
  %t10.a.27 = alloca i64, align 8
  store i64 0, ptr %t10.a.27
  %t11.a.30 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t11.a.30
  %t12.a.32 = alloca i1, align 8
  store i1 0, ptr %t12.a.32
  br label %entry
entry:
  store i64 5, ptr %t0.a.0
  %ep.1 = call ptr @malloc(i64 8)
  %l.2 = load i64, ptr %t0.a.0
  %ef.3 = getelementptr inbounds {i64}, ptr %ep.1, i32 0, i32 0
  store i64 %l.2, ptr %ef.3
  %ei.4 = insertvalue {i64, ptr} undef, i64 0, 0
  %ei.5 = insertvalue {i64, ptr} %ei.4, ptr %ep.1, 1
  store {i64, ptr} %ei.5, ptr %t2.a.6
  %l.7 = load {i64, ptr}, ptr %t2.a.6
  %c.8 = call i64 @area({i64, ptr} %l.7)
  store i64 %c.8, ptr %t3.a.9
  %l.10 = load i64, ptr %t3.a.9
  %rt.11 = call {ptr, i64} @__mn_str_from_int(i64 %l.10)
  store {ptr, i64} %rt.11, ptr %t4.a.12
  %l.13 = load {ptr, i64}, ptr %t4.a.12
  call void @__mn_str_println({ptr, i64} %l.13)
  store i1 0, ptr %t5.a.14
  store i64 4, ptr %t6.a.15
  store i64 6, ptr %t7.a.16
  %ep.17 = call ptr @malloc(i64 16)
  %l.18 = load i64, ptr %t6.a.15
  %ef.19 = getelementptr inbounds {i64, i64}, ptr %ep.17, i32 0, i32 0
  store i64 %l.18, ptr %ef.19
  %l.20 = load i64, ptr %t7.a.16
  %ef.21 = getelementptr inbounds {i64, i64}, ptr %ep.17, i32 0, i32 1
  store i64 %l.20, ptr %ef.21
  %ei.22 = insertvalue {i64, ptr} undef, i64 1, 0
  %ei.23 = insertvalue {i64, ptr} %ei.22, ptr %ep.17, 1
  store {i64, ptr} %ei.23, ptr %t9.a.24
  %l.25 = load {i64, ptr}, ptr %t9.a.24
  %c.26 = call i64 @area({i64, ptr} %l.25)
  store i64 %c.26, ptr %t10.a.27
  %l.28 = load i64, ptr %t10.a.27
  %rt.29 = call {ptr, i64} @__mn_str_from_int(i64 %l.28)
  store {ptr, i64} %rt.29, ptr %t11.a.30
  %l.31 = load {ptr, i64}, ptr %t11.a.30
  call void @__mn_str_println({ptr, i64} %l.31)
  store i1 0, ptr %t12.a.32
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.14.0"}
