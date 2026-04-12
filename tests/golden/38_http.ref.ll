; ModuleID = '38_http'
source_filename = "38_http"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [29 x i8] c"http://httpbin.org/robots.txt", align 8

declare {ptr, i64} @__mn_http_get({ptr, i64}) nounwind willreturn
declare i64 @__mn_str_len({ptr, i64}) nounwind readonly willreturn
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t0.a.3
  %str_track.6 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.6
  %t1.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.7
  %t2.a.10 = alloca i64, align 8
  store i64 0, ptr %t2.a.10
  %str_track.13 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.13
  %t3.a.14 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.14
  %t4.a.16 = alloca i1, align 8
  store i1 0, ptr %t4.a.16
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [29 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 29, 1
  store {ptr, i64} %s.2, ptr %t0.a.3
  %l.4 = load {ptr, i64}, ptr %t0.a.3
  %rt.5 = call {ptr, i64} @__mn_http_get({ptr, i64} %l.4)
  store {ptr, i64} %rt.5, ptr %str_track.6
  store {ptr, i64} %rt.5, ptr %t1.a.7
  %l.8 = load {ptr, i64}, ptr %t1.a.7
  %rt.9 = call i64 @__mn_str_len({ptr, i64} %l.8)
  store i64 %rt.9, ptr %t2.a.10
  %l.11 = load i64, ptr %t2.a.10
  %rt.12 = call {ptr, i64} @__mn_str_from_int(i64 %l.11)
  store {ptr, i64} %rt.12, ptr %str_track.13
  store {ptr, i64} %rt.12, ptr %t3.a.14
  %l.15 = load {ptr, i64}, ptr %t3.a.14
  call void @__mn_str_println({ptr, i64} %l.15)
  store i1 0, ptr %t4.a.16
  %drop.s.17 = load {ptr, i64}, ptr %str_track.6
  %drop.p.18 = extractvalue {ptr, i64} %drop.s.17, 0
  %drop.null.19 = icmp eq ptr %drop.p.18, null
  br i1 %drop.null.19, label %drop.skip.20, label %drop.check.20
drop.check.20:
  call void @__mn_str_free({ptr, i64} %drop.s.17)
  br label %drop.skip.20
drop.skip.20:
  %drop.s.21 = load {ptr, i64}, ptr %str_track.13
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
