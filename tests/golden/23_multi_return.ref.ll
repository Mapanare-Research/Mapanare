; ModuleID = '23_multi_return'
source_filename = "23_multi_return"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal {i64, i64} @swap({i64, i64} %p) {
pre_entry:
  %p.addr = alloca {i64, i64}, align 8
  %t0.a.2 = alloca i64, align 8
  store i64 0, ptr %t0.a.2
  %t1.a.5 = alloca i64, align 8
  store i64 0, ptr %t1.a.5
  %t2.a.10 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %t2.a.10
  store {i64, i64} %p, ptr %p.addr
  br label %entry
entry:
  %fg.0 = getelementptr inbounds {i64, i64}, ptr %p.addr, i32 0, i32 1
  %fv.1 = load i64, ptr %fg.0
  store i64 %fv.1, ptr %t0.a.2
  %fg.3 = getelementptr inbounds {i64, i64}, ptr %p.addr, i32 0, i32 0
  %fv.4 = load i64, ptr %fg.3
  store i64 %fv.4, ptr %t1.a.5
  %l.6 = load i64, ptr %t0.a.2
  %si.7 = insertvalue {i64, i64} undef, i64 %l.6, 0
  %l.8 = load i64, ptr %t1.a.5
  %si.9 = insertvalue {i64, i64} %si.7, i64 %l.8, 1
  store {i64, i64} %si.9, ptr %t2.a.10
  %l.11 = load {i64, i64}, ptr %t2.a.10
  ret {i64, i64} %l.11
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.6 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %t2.a.6
  %t3.a.9 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %t3.a.9
  %t4.a.12 = alloca i64, align 8
  store i64 0, ptr %t4.a.12
  %str_track.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.15
  %t5.a.16 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.16
  %t6.a.18 = alloca i1, align 8
  store i1 0, ptr %t6.a.18
  %t7.a.21 = alloca i64, align 8
  store i64 0, ptr %t7.a.21
  %str_track.24 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.24
  %t8.a.25 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t8.a.25
  %t9.a.27 = alloca i1, align 8
  store i1 0, ptr %t9.a.27
  br label %entry
entry:
  store i64 1, ptr %t0.a.0
  store i64 2, ptr %t1.a.1
  %l.2 = load i64, ptr %t0.a.0
  %si.3 = insertvalue {i64, i64} undef, i64 %l.2, 0
  %l.4 = load i64, ptr %t1.a.1
  %si.5 = insertvalue {i64, i64} %si.3, i64 %l.4, 1
  store {i64, i64} %si.5, ptr %t2.a.6
  %l.7 = load {i64, i64}, ptr %t2.a.6
  %c.8 = call {i64, i64} @swap({i64, i64} %l.7)
  store {i64, i64} %c.8, ptr %t3.a.9
  %fg.10 = getelementptr inbounds {i64, i64}, ptr %t3.a.9, i32 0, i32 0
  %fv.11 = load i64, ptr %fg.10
  store i64 %fv.11, ptr %t4.a.12
  %l.13 = load i64, ptr %t4.a.12
  %rt.14 = call {ptr, i64} @__mn_str_from_int(i64 %l.13)
  store {ptr, i64} %rt.14, ptr %str_track.15
  store {ptr, i64} %rt.14, ptr %t5.a.16
  %l.17 = load {ptr, i64}, ptr %t5.a.16
  call void @__mn_str_println({ptr, i64} %l.17)
  store i1 0, ptr %t6.a.18
  %fg.19 = getelementptr inbounds {i64, i64}, ptr %t3.a.9, i32 0, i32 1
  %fv.20 = load i64, ptr %fg.19
  store i64 %fv.20, ptr %t7.a.21
  %l.22 = load i64, ptr %t7.a.21
  %rt.23 = call {ptr, i64} @__mn_str_from_int(i64 %l.22)
  store {ptr, i64} %rt.23, ptr %str_track.24
  store {ptr, i64} %rt.23, ptr %t8.a.25
  %l.26 = load {ptr, i64}, ptr %t8.a.25
  call void @__mn_str_println({ptr, i64} %l.26)
  store i1 0, ptr %t9.a.27
  %drop.s.28 = load {ptr, i64}, ptr %str_track.15
  %drop.p.29 = extractvalue {ptr, i64} %drop.s.28, 0
  %drop.null.30 = icmp eq ptr %drop.p.29, null
  br i1 %drop.null.30, label %drop.skip.31, label %drop.check.31
drop.check.31:
  call void @__mn_str_free({ptr, i64} %drop.s.28)
  br label %drop.skip.31
drop.skip.31:
  %drop.s.32 = load {ptr, i64}, ptr %str_track.24
  %drop.p.33 = extractvalue {ptr, i64} %drop.s.32, 0
  %drop.null.34 = icmp eq ptr %drop.p.33, null
  br i1 %drop.null.34, label %drop.skip.35, label %drop.check.35
drop.check.35:
  call void @__mn_str_free({ptr, i64} %drop.s.32)
  br label %drop.skip.35
drop.skip.35:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.33.0"}
