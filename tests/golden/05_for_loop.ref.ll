; ModuleID = '05_for_loop'
source_filename = "05_for_loop"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare ptr @__mn_range(i64, i64)
declare i1 @__iter_has_next(ptr)
declare i64 @__iter_next(ptr)
declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define i64 @main() {
pre_entry:
  %sum.a.0 = alloca i64, align 8
  store i64 0, ptr %sum.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.2 = alloca i64, align 8
  store i64 0, ptr %t2.a.2
  %t3.a.6 = alloca ptr, align 8
  store ptr null, ptr %t3.a.6
  %has_next5.a.9 = alloca i1, align 8
  store i1 0, ptr %has_next5.a.9
  %next6.a.13 = alloca i64, align 8
  store i64 0, ptr %next6.a.13
  %t7.a.17 = alloca i64, align 8
  store i64 0, ptr %t7.a.17
  %t8.a.21 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t8.a.21
  %t9.a.23 = alloca i1, align 8
  store i1 0, ptr %t9.a.23
  br label %entry
entry:
  store i64 0, ptr %sum.a.0
  store i64 0, ptr %t1.a.1
  store i64 10, ptr %t2.a.2
  %l.3 = load i64, ptr %t1.a.1
  %l.4 = load i64, ptr %t2.a.2
  %c.5 = call ptr @__mn_range(i64 %l.3, i64 %l.4)
  store ptr %c.5, ptr %t3.a.6
  br label %for_header0
for_header0:
  %l.7 = load ptr, ptr %t3.a.6
  %c.8 = call i1 @__iter_has_next(ptr %l.7)
  store i1 %c.8, ptr %has_next5.a.9
  %l.10 = load i1, ptr %has_next5.a.9
  br i1 %l.10, label %for_body1, label %for_exit2
for_body1:
  %l.11 = load ptr, ptr %t3.a.6
  %c.12 = call i64 @__iter_next(ptr %l.11)
  store i64 %c.12, ptr %next6.a.13
  %l.14 = load i64, ptr %sum.a.0
  %l.15 = load i64, ptr %next6.a.13
  %i.16 = add nsw i64 %l.14, %l.15
  store i64 %i.16, ptr %t7.a.17
  %l.18 = load i64, ptr %t7.a.17
  store i64 %l.18, ptr %sum.a.0
  br label %for_header0
for_exit2:
  %l.19 = load i64, ptr %sum.a.0
  %rt.20 = call {ptr, i64} @__mn_str_from_int(i64 %l.19)
  store {ptr, i64} %rt.20, ptr %t8.a.21
  %l.22 = load {ptr, i64}, ptr %t8.a.21
  call void @__mn_str_println({ptr, i64} %l.22)
  store i1 0, ptr %t9.a.23
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
