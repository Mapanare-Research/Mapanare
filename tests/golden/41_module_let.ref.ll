; ModuleID = '41_module_let'
source_filename = "41_module_let"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@MAX_SIZE = private constant i64 100
@PI_APPROX = private constant i64 3
@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 8

declare i32 @printf(ptr, ...)
declare void @__mn_intern_destroy()

define internal i64 @get_max() {
pre_entry:
  %MAX_SIZE0.a.0 = alloca i64, align 8
  store i64 0, ptr %MAX_SIZE0.a.0
  br label %entry
entry:
  store i64 100, ptr %MAX_SIZE0.a.0
  %l.1 = load i64, ptr %MAX_SIZE0.a.0
  ret i64 %l.1
}

define i64 @main() {
pre_entry:
  %t0.a.1 = alloca i64, align 8
  store i64 0, ptr %t0.a.1
  %t1.a.5 = alloca i1, align 8
  store i1 0, ptr %t1.a.5
  %PI_APPROX2.a.6 = alloca i64, align 8
  store i64 0, ptr %PI_APPROX2.a.6
  %t3.a.10 = alloca i1, align 8
  store i1 0, ptr %t3.a.10
  br label %entry
entry:
  %c.0 = call i64 @get_max()
  store i64 %c.0, ptr %t0.a.1
  %l.2 = load i64, ptr %t0.a.1
  %fp.3 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.4 = call i32 (ptr, ...) @printf(ptr %fp.3, i64 %l.2)
  store i1 0, ptr %t1.a.5
  store i64 3, ptr %PI_APPROX2.a.6
  %l.7 = load i64, ptr %PI_APPROX2.a.6
  %fp.8 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.9 = call i32 (ptr, ...) @printf(ptr %fp.8, i64 %l.7)
  store i1 0, ptr %t3.a.10
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.32.0"}
