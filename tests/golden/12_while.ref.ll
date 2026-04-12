; ModuleID = '12_while'
source_filename = "12_while"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %i.a.2 = alloca i64, align 8
  store i64 0, ptr %i.a.2
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %t2.a.7 = alloca i1, align 8
  store i1 0, ptr %t2.a.7
  %t3.a.9 = alloca i64, align 8
  store i64 0, ptr %t3.a.9
  %t4.a.13 = alloca i64, align 8
  store i64 0, ptr %t4.a.13
  %str_track.17 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.17
  %t5.a.18 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.18
  %t6.a.20 = alloca i1, align 8
  store i1 0, ptr %t6.a.20
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  store i64 %l.1, ptr %i.a.2
  br label %while_header0
while_header0:
  store i64 5, ptr %t1.a.3
  %l.4 = load i64, ptr %i.a.2
  %l.5 = load i64, ptr %t1.a.3
  %i.6 = icmp slt i64 %l.4, %l.5
  store i1 %i.6, ptr %t2.a.7
  %l.8 = load i1, ptr %t2.a.7
  br i1 %l.8, label %while_body1, label %while_exit2
while_body1:
  store i64 1, ptr %t3.a.9
  %l.10 = load i64, ptr %i.a.2
  %l.11 = load i64, ptr %t3.a.9
  %i.12 = add nsw i64 %l.10, %l.11
  store i64 %i.12, ptr %t4.a.13
  %l.14 = load i64, ptr %t4.a.13
  store i64 %l.14, ptr %i.a.2
  br label %while_header0
while_exit2:
  %l.15 = load i64, ptr %i.a.2
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
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.33.0"}
