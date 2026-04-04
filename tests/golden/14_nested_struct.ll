; ModuleID = '14_nested_struct'
source_filename = "14_nested_struct"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.6 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %t2.a.6
  %t3.a.9 = alloca i64, align 8
  store i64 0, ptr %t3.a.9
  %t4.a.12 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.12
  %t5.a.14 = alloca i1, align 8
  store i1 0, ptr %t5.a.14
  br label %entry
entry:
  store i64 10, ptr %t0.a.0
  store i64 20, ptr %t1.a.1
  %l.2 = load i64, ptr %t0.a.0
  %si.3 = insertvalue {i64, i64} undef, i64 %l.2, 0
  %l.4 = load i64, ptr %t1.a.1
  %si.5 = insertvalue {i64, i64} %si.3, i64 %l.4, 1
  store {i64, i64} %si.5, ptr %t2.a.6
  %fg.7 = getelementptr inbounds {i64, i64}, ptr %t2.a.6, i32 0, i32 0
  %fv.8 = load i64, ptr %fg.7
  store i64 %fv.8, ptr %t3.a.9
  %l.10 = load i64, ptr %t3.a.9
  %rt.11 = call {ptr, i64} @__mn_str_from_int(i64 %l.10)
  store {ptr, i64} %rt.11, ptr %t4.a.12
  %l.13 = load {ptr, i64}, ptr %t4.a.12
  call void @__mn_str_println({ptr, i64} %l.13)
  store i1 0, ptr %t5.a.14
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.0.1"}
