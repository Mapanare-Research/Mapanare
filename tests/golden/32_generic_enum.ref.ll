; ModuleID = '32_generic_enum'
source_filename = "32_generic_enum"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 2

declare ptr @malloc(i64)
declare i32 @printf(ptr, ...)

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t2.a.7 = alloca {i64, ptr}, align 8
  store {i64, ptr} zeroinitializer, ptr %t2.a.7
  %t3.a.8 = alloca i64, align 8
  store i64 0, ptr %t3.a.8
  %t4.a.12 = alloca i1, align 8
  store i1 0, ptr %t4.a.12
  %t5.a.13 = alloca i64, align 8
  store i64 0, ptr %t5.a.13
  %t7.a.20 = alloca {i64, ptr}, align 8
  store {i64, ptr} zeroinitializer, ptr %t7.a.20
  %t8.a.21 = alloca i64, align 8
  store i64 0, ptr %t8.a.21
  %t9.a.25 = alloca i1, align 8
  store i1 0, ptr %t9.a.25
  br label %entry
entry:
  store i64 42, ptr %t0.a.0
  %ep.1 = call ptr @malloc(i64 8)
  %l.2 = load i64, ptr %t0.a.0
  %ef.3 = getelementptr inbounds {ptr}, ptr %ep.1, i32 0, i32 0
  %i2p.4 = inttoptr i64 %l.2 to ptr
  store ptr %i2p.4, ptr %ef.3
  %ei.5 = insertvalue {i64, ptr} undef, i64 0, 0
  %ei.6 = insertvalue {i64, ptr} %ei.5, ptr %ep.1, 1
  store {i64, ptr} %ei.6, ptr %t2.a.7
  store i64 42, ptr %t3.a.8
  %l.9 = load i64, ptr %t3.a.8
  %fp.10 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.11 = call i32 (ptr, ...) @printf(ptr %fp.10, i64 %l.9)
  store i1 0, ptr %t4.a.12
  store i64 99, ptr %t5.a.13
  %ep.14 = call ptr @malloc(i64 8)
  %l.15 = load i64, ptr %t5.a.13
  %ef.16 = getelementptr inbounds {ptr}, ptr %ep.14, i32 0, i32 0
  %i2p.17 = inttoptr i64 %l.15 to ptr
  store ptr %i2p.17, ptr %ef.16
  %ei.18 = insertvalue {i64, ptr} undef, i64 0, 0
  %ei.19 = insertvalue {i64, ptr} %ei.18, ptr %ep.14, 1
  store {i64, ptr} %ei.19, ptr %t7.a.20
  store i64 99, ptr %t8.a.21
  %l.22 = load i64, ptr %t8.a.21
  %fp.23 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.24 = call i32 (ptr, ...) @printf(ptr %fp.23, i64 %l.22)
  store i1 0, ptr %t9.a.25
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.14.0"}
