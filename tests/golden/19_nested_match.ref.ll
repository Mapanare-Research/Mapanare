; ModuleID = '19_nested_match'
source_filename = "19_nested_match"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare noalias ptr @malloc(i64) nounwind willreturn
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

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
  %box_track.2 = alloca ptr, align 8
  store ptr null, ptr %box_track.2
  %t2.a.7 = alloca {i64, ptr}, align 8
  store {i64, ptr} zeroinitializer, ptr %t2.a.7
  %t3.a.10 = alloca i64, align 8
  store i64 0, ptr %t3.a.10
  %str_track.13 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.13
  %t4.a.14 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.14
  %t5.a.16 = alloca i1, align 8
  store i1 0, ptr %t5.a.16
  %t6.a.17 = alloca i64, align 8
  store i64 0, ptr %t6.a.17
  %t7.a.18 = alloca i64, align 8
  store i64 0, ptr %t7.a.18
  %box_track.20 = alloca ptr, align 8
  store ptr null, ptr %box_track.20
  %t9.a.27 = alloca {i64, ptr}, align 8
  store {i64, ptr} zeroinitializer, ptr %t9.a.27
  %t10.a.30 = alloca i64, align 8
  store i64 0, ptr %t10.a.30
  %str_track.33 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.33
  %t11.a.34 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t11.a.34
  %t12.a.36 = alloca i1, align 8
  store i1 0, ptr %t12.a.36
  br label %entry
entry:
  store i64 5, ptr %t0.a.0
  %ep.1 = call ptr @malloc(i64 8)
  store ptr %ep.1, ptr %box_track.2
  %l.3 = load i64, ptr %t0.a.0
  %ef.4 = getelementptr inbounds {i64}, ptr %ep.1, i32 0, i32 0
  store i64 %l.3, ptr %ef.4
  %ei.5 = insertvalue {i64, ptr} undef, i64 0, 0
  %ei.6 = insertvalue {i64, ptr} %ei.5, ptr %ep.1, 1
  store {i64, ptr} %ei.6, ptr %t2.a.7
  %l.8 = load {i64, ptr}, ptr %t2.a.7
  store ptr null, ptr %box_track.2
  %c.9 = call i64 @area({i64, ptr} %l.8)
  store i64 %c.9, ptr %t3.a.10
  %l.11 = load i64, ptr %t3.a.10
  %rt.12 = call {ptr, i64} @__mn_str_from_int(i64 %l.11)
  store {ptr, i64} %rt.12, ptr %str_track.13
  store {ptr, i64} %rt.12, ptr %t4.a.14
  %l.15 = load {ptr, i64}, ptr %t4.a.14
  call void @__mn_str_println({ptr, i64} %l.15)
  store i1 0, ptr %t5.a.16
  store i64 4, ptr %t6.a.17
  store i64 6, ptr %t7.a.18
  %ep.19 = call ptr @malloc(i64 16)
  store ptr %ep.19, ptr %box_track.20
  %l.21 = load i64, ptr %t6.a.17
  %ef.22 = getelementptr inbounds {i64, i64}, ptr %ep.19, i32 0, i32 0
  store i64 %l.21, ptr %ef.22
  %l.23 = load i64, ptr %t7.a.18
  %ef.24 = getelementptr inbounds {i64, i64}, ptr %ep.19, i32 0, i32 1
  store i64 %l.23, ptr %ef.24
  %ei.25 = insertvalue {i64, ptr} undef, i64 1, 0
  %ei.26 = insertvalue {i64, ptr} %ei.25, ptr %ep.19, 1
  store {i64, ptr} %ei.26, ptr %t9.a.27
  %l.28 = load {i64, ptr}, ptr %t9.a.27
  store ptr null, ptr %box_track.20
  %c.29 = call i64 @area({i64, ptr} %l.28)
  store i64 %c.29, ptr %t10.a.30
  %l.31 = load i64, ptr %t10.a.30
  %rt.32 = call {ptr, i64} @__mn_str_from_int(i64 %l.31)
  store {ptr, i64} %rt.32, ptr %str_track.33
  store {ptr, i64} %rt.32, ptr %t11.a.34
  %l.35 = load {ptr, i64}, ptr %t11.a.34
  call void @__mn_str_println({ptr, i64} %l.35)
  store i1 0, ptr %t12.a.36
  %drop.s.37 = load {ptr, i64}, ptr %str_track.13
  %drop.p.38 = extractvalue {ptr, i64} %drop.s.37, 0
  %drop.null.39 = icmp eq ptr %drop.p.38, null
  br i1 %drop.null.39, label %drop.skip.40, label %drop.check.40
drop.check.40:
  call void @__mn_str_free({ptr, i64} %drop.s.37)
  br label %drop.skip.40
drop.skip.40:
  %drop.s.41 = load {ptr, i64}, ptr %str_track.33
  %drop.p.42 = extractvalue {ptr, i64} %drop.s.41, 0
  %drop.null.43 = icmp eq ptr %drop.p.42, null
  br i1 %drop.null.43, label %drop.skip.44, label %drop.check.44
drop.check.44:
  call void @__mn_str_free({ptr, i64} %drop.s.41)
  br label %drop.skip.44
drop.skip.44:
  %drop.bp.45 = load ptr, ptr %box_track.2
  %drop.bnull.46 = icmp eq ptr %drop.bp.45, null
  br i1 %drop.bnull.46, label %drop.bskip.47, label %drop.bcheck.47
drop.bcheck.47:
  call void @free(ptr %drop.bp.45)
  br label %drop.bskip.47
drop.bskip.47:
  %drop.bp.48 = load ptr, ptr %box_track.20
  %drop.bnull.49 = icmp eq ptr %drop.bp.48, null
  br i1 %drop.bnull.49, label %drop.bskip.50, label %drop.bcheck.50
drop.bcheck.50:
  call void @free(ptr %drop.bp.48)
  br label %drop.bskip.50
drop.bskip.50:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.33.0"}
