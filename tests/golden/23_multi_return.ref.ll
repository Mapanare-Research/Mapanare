; ModuleID = '23_multi_return'
source_filename = "23_multi_return"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

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
  %t5.a.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.15
  %t6.a.17 = alloca i1, align 8
  store i1 0, ptr %t6.a.17
  %t7.a.20 = alloca i64, align 8
  store i64 0, ptr %t7.a.20
  %t8.a.23 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t8.a.23
  %t9.a.25 = alloca i1, align 8
  store i1 0, ptr %t9.a.25
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
  store {ptr, i64} %rt.14, ptr %t5.a.15
  %l.16 = load {ptr, i64}, ptr %t5.a.15
  call void @__mn_str_println({ptr, i64} %l.16)
  store i1 0, ptr %t6.a.17
  %fg.18 = getelementptr inbounds {i64, i64}, ptr %t3.a.9, i32 0, i32 1
  %fv.19 = load i64, ptr %fg.18
  store i64 %fv.19, ptr %t7.a.20
  %l.21 = load i64, ptr %t7.a.20
  %rt.22 = call {ptr, i64} @__mn_str_from_int(i64 %l.21)
  store {ptr, i64} %rt.22, ptr %t8.a.23
  %l.24 = load {ptr, i64}, ptr %t8.a.23
  call void @__mn_str_println({ptr, i64} %l.24)
  store i1 0, ptr %t9.a.25
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
