; ModuleID = '03_function'
source_filename = "03_function"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define internal i64 @add(i64 %a, i64 %b) {
pre_entry:
  %a.addr = alloca i64, align 8
  %b.addr = alloca i64, align 8
  %t0.a.3 = alloca i64, align 8
  store i64 0, ptr %t0.a.3
  store i64 %a, ptr %a.addr
  store i64 %b, ptr %b.addr
  br label %entry
entry:
  %l.0 = load i64, ptr %a.addr
  %l.1 = load i64, ptr %b.addr
  %i.2 = add nsw i64 %l.0, %l.1
  store i64 %i.2, ptr %t0.a.3
  %l.4 = load i64, ptr %t0.a.3
  ret i64 %l.4
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.5 = alloca i64, align 8
  store i64 0, ptr %t2.a.5
  %t3.a.8 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.8
  %t4.a.10 = alloca i1, align 8
  store i1 0, ptr %t4.a.10
  br label %entry
entry:
  store i64 10, ptr %t0.a.0
  store i64 20, ptr %t1.a.1
  %l.2 = load i64, ptr %t0.a.0
  %l.3 = load i64, ptr %t1.a.1
  %c.4 = call i64 @add(i64 %l.2, i64 %l.3)
  store i64 %c.4, ptr %t2.a.5
  %l.6 = load i64, ptr %t2.a.5
  %rt.7 = call {ptr, i64} @__mn_str_from_int(i64 %l.6)
  store {ptr, i64} %rt.7, ptr %t3.a.8
  %l.9 = load {ptr, i64}, ptr %t3.a.8
  call void @__mn_str_println({ptr, i64} %l.9)
  store i1 0, ptr %t4.a.10
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.14.0"}
