; ModuleID = '11_closure'
source_filename = "11_closure"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare noalias ptr @malloc(i64) nounwind willreturn
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal i64 @lambda1(ptr %__env_ptr, i64 %n) {
pre_entry:
  %__env_ptr.addr = alloca ptr, align 8
  %n.addr = alloca i64, align 8
  %x.a.3 = alloca i64, align 8
  store i64 0, ptr %x.a.3
  %t0.a.7 = alloca i64, align 8
  store i64 0, ptr %t0.a.7
  store ptr %__env_ptr, ptr %__env_ptr.addr
  store i64 %n, ptr %n.addr
  br label %entry
entry:
  %l.0 = load ptr, ptr %__env_ptr.addr
  %elf.1 = getelementptr inbounds {i64}, ptr %l.0, i32 0, i32 0
  %elv.2 = load i64, ptr %elf.1
  store i64 %elv.2, ptr %x.a.3
  %l.4 = load i64, ptr %n.addr
  %l.5 = load i64, ptr %x.a.3
  %i.6 = add nsw i64 %l.4, %l.5
  store i64 %i.6, ptr %t0.a.7
  %l.8 = load i64, ptr %t0.a.7
  ret i64 %l.8
}

define i64 @main() {
pre_entry:
  %x.a.0 = alloca i64, align 8
  store i64 0, ptr %x.a.0
  %clos_track.6 = alloca {ptr, ptr}, align 8
  store {ptr, ptr} zeroinitializer, ptr %clos_track.6
  %t2.a.7 = alloca {ptr, ptr}, align 8
  store {ptr, ptr} zeroinitializer, ptr %t2.a.7
  %t3.a.8 = alloca i64, align 8
  store i64 0, ptr %t3.a.8
  %t4.a.14 = alloca i64, align 8
  store i64 0, ptr %t4.a.14
  %str_track.17 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.17
  %t5.a.18 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.18
  %t6.a.20 = alloca i1, align 8
  store i1 0, ptr %t6.a.20
  br label %entry
entry:
  store i64 10, ptr %x.a.0
  %ce.1 = call ptr @malloc(i64 8)
  %l.2 = load i64, ptr %x.a.0
  %cf.3 = getelementptr inbounds {i64}, ptr %ce.1, i32 0, i32 0
  store i64 %l.2, ptr %cf.3
  %cc.4 = insertvalue {ptr, ptr} undef, ptr @lambda1, 0
  %cc.5 = insertvalue {ptr, ptr} %cc.4, ptr %ce.1, 1
  store {ptr, ptr} %cc.5, ptr %clos_track.6
  store {ptr, ptr} %cc.5, ptr %t2.a.7
  store i64 5, ptr %t3.a.8
  %l.9 = load {ptr, ptr}, ptr %t2.a.7
  %l.10 = load i64, ptr %t3.a.8
  %cfn.11 = extractvalue {ptr, ptr} %l.9, 0
  %cen.12 = extractvalue {ptr, ptr} %l.9, 1
  %ccr.13 = call i64 %cfn.11(ptr %cen.12, i64 %l.10)
  store i64 %ccr.13, ptr %t4.a.14
  %l.15 = load i64, ptr %t4.a.14
  %rt.16 = call {ptr, i64} @__mn_str_from_int(i64 %l.15)
  store {ptr, i64} %rt.16, ptr %str_track.17
  store {ptr, i64} %rt.16, ptr %t5.a.18
  %l.19 = load {ptr, i64}, ptr %t5.a.18
  call void @__mn_str_println({ptr, i64} %l.19)
  store i1 0, ptr %t6.a.20
  %drop.s.21 = load {ptr, i64}, ptr %str_track.17
  %drop.p.22 = extractvalue {ptr, i64} %drop.s.21, 0
  %drop.null.23 = icmp eq ptr %drop.p.22, null
  br i1 %drop.null.23, label %drop.skip.24, label %drop.check.24
drop.check.24:
  call void @__mn_str_free({ptr, i64} %drop.s.21)
  br label %drop.skip.24
drop.skip.24:
  %drop.c.25 = load {ptr, ptr}, ptr %clos_track.6
  %drop.ep.26 = extractvalue {ptr, ptr} %drop.c.25, 1
  %drop.enull.27 = icmp eq ptr %drop.ep.26, null
  br i1 %drop.enull.27, label %drop.cskip.28, label %drop.ccheck.28
drop.ccheck.28:
  call void @free(ptr %drop.ep.26)
  br label %drop.cskip.28
drop.cskip.28:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.32.0"}
