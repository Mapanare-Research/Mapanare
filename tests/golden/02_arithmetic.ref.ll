; ModuleID = '02_arithmetic'
source_filename = "02_arithmetic"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %x.a.0 = alloca i64, align 8
  store i64 0, ptr %x.a.0
  %str_track.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.3
  %t5.a.4 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.4
  %t6.a.6 = alloca i1, align 8
  store i1 0, ptr %t6.a.6
  br label %entry
entry:
  store i64 14, ptr %x.a.0
  %l.1 = load i64, ptr %x.a.0
  %rt.2 = call {ptr, i64} @__mn_str_from_int(i64 %l.1)
  store {ptr, i64} %rt.2, ptr %str_track.3
  store {ptr, i64} %rt.2, ptr %t5.a.4
  %l.5 = load {ptr, i64}, ptr %t5.a.4
  call void @__mn_str_println({ptr, i64} %l.5)
  store i1 0, ptr %t6.a.6
  %drop.s.7 = load {ptr, i64}, ptr %str_track.3
  %drop.p.8 = extractvalue {ptr, i64} %drop.s.7, 0
  %drop.null.9 = icmp eq ptr %drop.p.8, null
  br i1 %drop.null.9, label %drop.skip.10, label %drop.check.10
drop.check.10:
  call void @__mn_str_free({ptr, i64} %drop.s.7)
  br label %drop.skip.10
drop.skip.10:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
