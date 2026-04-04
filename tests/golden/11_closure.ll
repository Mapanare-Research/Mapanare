; ModuleID = '11_closure'
source_filename = "11_closure"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare ptr @malloc(i64)
declare {ptr, i64} @__mn_str_from_int(i64)
declare void @__mn_str_println({ptr, i64})

define internal i64 @lambda1(ptr %__env_ptr, i64 %n) {
pre_entry:
  %__env_ptr.addr = alloca ptr, align 8
  %n.addr = alloca i64, align 8
  %x.a.4 = alloca i64, align 8
  store i64 0, ptr %x.a.4
  %t0.a.8 = alloca i64, align 8
  store i64 0, ptr %t0.a.8
  store ptr %__env_ptr, ptr %__env_ptr.addr
  store i64 %n, ptr %n.addr
  br label %entry
entry:
  %l.0 = load ptr, ptr %__env_ptr.addr
  %elp.1 = bitcast ptr %l.0 to {i64}*
  %elf.2 = getelementptr inbounds {i64}, ptr %elp.1, i32 0, i32 0
  %elv.3 = load i64, ptr %elf.2
  store i64 %elv.3, ptr %x.a.4
  %l.5 = load i64, ptr %n.addr
  %l.6 = load i64, ptr %x.a.4
  %i.7 = add nsw i64 %l.5, %l.6
  store i64 %i.7, ptr %t0.a.8
  %l.9 = load i64, ptr %t0.a.8
  ret i64 %l.9
}

define i64 @main() {
pre_entry:
  %x.a.0 = alloca i64, align 8
  store i64 0, ptr %x.a.0
  %t2.a.6 = alloca {ptr, ptr}, align 8
  store {ptr, ptr} zeroinitializer, ptr %t2.a.6
  %t3.a.7 = alloca i64, align 8
  store i64 0, ptr %t3.a.7
  %t4.a.13 = alloca i64, align 8
  store i64 0, ptr %t4.a.13
  %t5.a.16 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.16
  %t6.a.18 = alloca i1, align 8
  store i1 0, ptr %t6.a.18
  br label %entry
entry:
  store i64 10, ptr %x.a.0
  %ce.1 = call ptr @malloc(i64 8)
  %l.2 = load i64, ptr %x.a.0
  %cf.3 = getelementptr inbounds {i64}, ptr %ce.1, i32 0, i32 0
  store i64 %l.2, ptr %cf.3
  %cc.4 = insertvalue {ptr, ptr} undef, ptr @lambda1, 0
  %cc.5 = insertvalue {ptr, ptr} %cc.4, ptr %ce.1, 1
  store {ptr, ptr} %cc.5, ptr %t2.a.6
  store i64 5, ptr %t3.a.7
  %l.8 = load {ptr, ptr}, ptr %t2.a.6
  %l.9 = load i64, ptr %t3.a.7
  %cfn.10 = extractvalue {ptr, ptr} %l.8, 0
  %cen.11 = extractvalue {ptr, ptr} %l.8, 1
  %ccr.12 = call i64 %cfn.10(ptr %cen.11, i64 %l.9)
  store i64 %ccr.12, ptr %t4.a.13
  %l.14 = load i64, ptr %t4.a.13
  %rt.15 = call {ptr, i64} @__mn_str_from_int(i64 %l.14)
  store {ptr, i64} %rt.15, ptr %t5.a.16
  %l.17 = load {ptr, i64}, ptr %t5.a.16
  call void @__mn_str_println({ptr, i64} %l.17)
  store i1 0, ptr %t6.a.18
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.0.1"}
