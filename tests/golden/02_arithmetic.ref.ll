; ModuleID = '02_arithmetic'
source_filename = "02_arithmetic"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define i64 @main() {
pre_entry:
  %x.a.0 = alloca i64, align 8
  store i64 0, ptr %x.a.0
  %t5.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.3
  %t6.a.5 = alloca i1, align 8
  store i1 0, ptr %t6.a.5
  br label %entry
entry:
  store i64 14, ptr %x.a.0
  %l.1 = load i64, ptr %x.a.0
  %rt.2 = call {ptr, i64} @__mn_str_from_int(i64 %l.1)
  store {ptr, i64} %rt.2, ptr %t5.a.3
  %l.4 = load {ptr, i64}, ptr %t5.a.3
  call void @__mn_str_println({ptr, i64} %l.4)
  store i1 0, ptr %t6.a.5
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
