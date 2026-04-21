; ModuleID = '08_list'
source_filename = "08_list"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind willreturn
declare void @__mn_list_push(ptr, ptr) nounwind
declare i64 @__mn_list_len(ptr) nounwind readonly willreturn
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_list_free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.2 = alloca i64, align 8
  store i64 0, ptr %t2.a.2
  %lp.4 = alloca {ptr, i64, i64, i64, i64}, align 8
  %ea.6 = alloca i64, align 8
  %ea.9 = alloca i64, align 8
  %ea.12 = alloca i64, align 8
  %t3.a.15 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t3.a.15
  %items.a.17 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %items.a.17
  %t4.a.18 = alloca i64, align 8
  store i64 0, ptr %t4.a.18
  %ea.20 = alloca i64, align 8
  %ll.23 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t5.a.25 = alloca i64, align 8
  store i64 0, ptr %t5.a.25
  %str_track.28 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.28
  %t6.a.29 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.29
  %t7.a.31 = alloca i1, align 8
  store i1 0, ptr %t7.a.31
  br label %entry
entry:
  store i64 1, ptr %t0.a.0
  store i64 2, ptr %t1.a.1
  store i64 3, ptr %t2.a.2
  %ln.3 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.3, ptr %lp.4
  %l.5 = load i64, ptr %t0.a.0
  store i64 %l.5, ptr %ea.6
  call void @__mn_list_push(ptr %lp.4, ptr %ea.6)
  %l.8 = load i64, ptr %t1.a.1
  store i64 %l.8, ptr %ea.9
  call void @__mn_list_push(ptr %lp.4, ptr %ea.9)
  %l.11 = load i64, ptr %t2.a.2
  store i64 %l.11, ptr %ea.12
  call void @__mn_list_push(ptr %lp.4, ptr %ea.12)
  %ll.14 = load {ptr, i64, i64, i64, i64}, ptr %lp.4
  store {ptr, i64, i64, i64, i64} %ll.14, ptr %t3.a.15
  %l.16 = load {ptr, i64, i64, i64, i64}, ptr %t3.a.15
  store {ptr, i64, i64, i64, i64} %l.16, ptr %items.a.17
  store i64 4, ptr %t4.a.18
  %l.19 = load i64, ptr %t4.a.18
  store i64 %l.19, ptr %ea.20
  call void @__mn_list_push(ptr %t3.a.15, ptr %ea.20)
  %ul.21 = load {ptr, i64, i64, i64, i64}, ptr %t3.a.15
  store {ptr, i64, i64, i64, i64} %ul.21, ptr %items.a.17
  %l.22 = load {ptr, i64, i64, i64, i64}, ptr %items.a.17
  store {ptr, i64, i64, i64, i64} %l.22, ptr %ll.23
  %rt.24 = call i64 @__mn_list_len(ptr %ll.23)
  store i64 %rt.24, ptr %t5.a.25
  %l.26 = load i64, ptr %t5.a.25
  %rt.27 = call {ptr, i64} @__mn_str_from_int(i64 %l.26)
  store {ptr, i64} %rt.27, ptr %str_track.28
  store {ptr, i64} %rt.27, ptr %t6.a.29
  %l.30 = load {ptr, i64}, ptr %t6.a.29
  call void @__mn_str_println({ptr, i64} %l.30)
  store i1 0, ptr %t7.a.31
  %drop.s.32 = load {ptr, i64}, ptr %str_track.28
  %drop.p.33 = extractvalue {ptr, i64} %drop.s.32, 0
  %drop.null.34 = icmp eq ptr %drop.p.33, null
  br i1 %drop.null.34, label %drop.skip.35, label %drop.check.35
drop.check.35:
  call void @__mn_str_free({ptr, i64} %drop.s.32)
  br label %drop.skip.35
drop.skip.35:
  %drop.lv.36 = load {ptr, i64, i64, i64, i64}, ptr %items.a.17
  %drop.lp.37 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.36, 0
  %drop.lnull.38 = icmp eq ptr %drop.lp.37, null
  br i1 %drop.lnull.38, label %drop.lskip.39, label %drop.lcheck.39
drop.lcheck.39:
  call void @__mn_list_free(ptr %items.a.17)
  br label %drop.lskip.39
drop.lskip.39:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
