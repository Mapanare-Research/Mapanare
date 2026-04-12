; ModuleID = '05_for_loop'
source_filename = "05_for_loop"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare ptr @__mn_range(i64, i64)
declare i1 @__iter_has_next(ptr)
declare i64 @__iter_next(ptr)
declare i1 @__mn_range_free(ptr) nounwind willreturn
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %sum.a.2 = alloca i64, align 8
  store i64 0, ptr %sum.a.2
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %t2.a.4 = alloca i64, align 8
  store i64 0, ptr %t2.a.4
  %t3.a.8 = alloca ptr, align 8
  store ptr null, ptr %t3.a.8
  %has_next5.a.11 = alloca i1, align 8
  store i1 0, ptr %has_next5.a.11
  %next6.a.15 = alloca i64, align 8
  store i64 0, ptr %next6.a.15
  %t7.a.19 = alloca i64, align 8
  store i64 0, ptr %t7.a.19
  %range_free8.a.23 = alloca i1, align 8
  store i1 0, ptr %range_free8.a.23
  %str_track.26 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.26
  %t9.a.27 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t9.a.27
  %t10.a.29 = alloca i1, align 8
  store i1 0, ptr %t10.a.29
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  store i64 %l.1, ptr %sum.a.2
  store i64 0, ptr %t1.a.3
  store i64 10, ptr %t2.a.4
  %l.5 = load i64, ptr %t1.a.3
  %l.6 = load i64, ptr %t2.a.4
  %c.7 = call ptr @__mn_range(i64 %l.5, i64 %l.6)
  store ptr %c.7, ptr %t3.a.8
  br label %for_header0
for_header0:
  %l.9 = load ptr, ptr %t3.a.8
  %c.10 = call i1 @__iter_has_next(ptr %l.9)
  store i1 %c.10, ptr %has_next5.a.11
  %l.12 = load i1, ptr %has_next5.a.11
  br i1 %l.12, label %for_body1, label %for_exit2
for_body1:
  %l.13 = load ptr, ptr %t3.a.8
  %c.14 = call i64 @__iter_next(ptr %l.13)
  store i64 %c.14, ptr %next6.a.15
  %l.16 = load i64, ptr %sum.a.2
  %l.17 = load i64, ptr %next6.a.15
  %i.18 = add nsw i64 %l.16, %l.17
  store i64 %i.18, ptr %t7.a.19
  %l.20 = load i64, ptr %t7.a.19
  store i64 %l.20, ptr %sum.a.2
  br label %for_header0
for_exit2:
  %l.21 = load ptr, ptr %t3.a.8
  %c.22 = call i1 @__mn_range_free(ptr %l.21)
  store i1 %c.22, ptr %range_free8.a.23
  %l.24 = load i64, ptr %sum.a.2
  %rt.25 = call {ptr, i64} @__mn_str_from_int(i64 %l.24)
  store {ptr, i64} %rt.25, ptr %str_track.26
  store {ptr, i64} %rt.25, ptr %t9.a.27
  %l.28 = load {ptr, i64}, ptr %t9.a.27
  call void @__mn_str_println({ptr, i64} %l.28)
  store i1 0, ptr %t10.a.29
  %drop.s.30 = load {ptr, i64}, ptr %str_track.26
  %drop.p.31 = extractvalue {ptr, i64} %drop.s.30, 0
  %drop.null.32 = icmp eq ptr %drop.p.31, null
  br i1 %drop.null.32, label %drop.skip.33, label %drop.check.33
drop.check.33:
  call void @__mn_str_free({ptr, i64} %drop.s.30)
  br label %drop.skip.33
drop.skip.33:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.33.0"}
