; ModuleID = '12_while'
source_filename = "12_while"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define i64 @main() {
pre_entry:
  %i.a.0 = alloca i64, align 8
  store i64 0, ptr %i.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.5 = alloca i1, align 8
  store i1 0, ptr %t2.a.5
  %t3.a.7 = alloca i64, align 8
  store i64 0, ptr %t3.a.7
  %t4.a.11 = alloca i64, align 8
  store i64 0, ptr %t4.a.11
  %t5.a.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.15
  %t6.a.17 = alloca i1, align 8
  store i1 0, ptr %t6.a.17
  br label %entry
entry:
  store i64 0, ptr %i.a.0
  br label %while_header0
while_header0:
  store i64 5, ptr %t1.a.1
  %l.2 = load i64, ptr %i.a.0
  %l.3 = load i64, ptr %t1.a.1
  %i.4 = icmp slt i64 %l.2, %l.3
  store i1 %i.4, ptr %t2.a.5
  %l.6 = load i1, ptr %t2.a.5
  br i1 %l.6, label %while_body1, label %while_exit2
while_body1:
  store i64 1, ptr %t3.a.7
  %l.8 = load i64, ptr %i.a.0
  %l.9 = load i64, ptr %t3.a.7
  %i.10 = add nsw i64 %l.8, %l.9
  store i64 %i.10, ptr %t4.a.11
  %l.12 = load i64, ptr %t4.a.11
  store i64 %l.12, ptr %i.a.0
  br label %while_header0
while_exit2:
  %l.13 = load i64, ptr %i.a.0
  %rt.14 = call {ptr, i64} @__mn_str_from_int(i64 %l.13)
  store {ptr, i64} %rt.14, ptr %t5.a.15
  %l.16 = load {ptr, i64}, ptr %t5.a.15
  call void @__mn_str_println({ptr, i64} %l.16)
  store i1 0, ptr %t6.a.17
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.0.1"}
