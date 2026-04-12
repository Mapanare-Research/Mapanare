; ModuleID = '43_module_let_math'
source_filename = "43_module_let_math"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@BLOCK_SIZE = private constant i64 256
@GRID_SIZE = private constant i64 1
@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 8
@.str.0 = private constant [31 x i8] c"threads computed via module let", align 8

declare i32 @printf(ptr, ...)
declare void @__mn_str_println({ptr, i64})
declare void @__mn_intern_destroy()

define internal i64 @compute_threads() {
pre_entry:
  %t2.a.0 = alloca i64, align 8
  store i64 0, ptr %t2.a.0
  br label %entry
entry:
  store i64 256, ptr %t2.a.0
  %l.1 = load i64, ptr %t2.a.0
  ret i64 %l.1
}

define i64 @main() {
pre_entry:
  %t0.a.1 = alloca i64, align 8
  store i64 0, ptr %t0.a.1
  %t1.a.5 = alloca i1, align 8
  store i1 0, ptr %t1.a.5
  %t2.a.9 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.9
  %t3.a.11 = alloca i1, align 8
  store i1 0, ptr %t3.a.11
  br label %entry
entry:
  %c.0 = call i64 @compute_threads()
  store i64 %c.0, ptr %t0.a.1
  %l.2 = load i64, ptr %t0.a.1
  %fp.3 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.4 = call i32 (ptr, ...) @printf(ptr %fp.3, i64 %l.2)
  store i1 0, ptr %t1.a.5
  %sp.6 = getelementptr inbounds [31 x i8], ptr @.str.0, i64 0, i64 0
  %s.7 = insertvalue {ptr, i64} undef, ptr %sp.6, 0
  %s.8 = insertvalue {ptr, i64} %s.7, i64 31, 1
  store {ptr, i64} %s.8, ptr %t2.a.9
  %l.10 = load {ptr, i64}, ptr %t2.a.9
  call void @__mn_str_println({ptr, i64} %l.10)
  store i1 0, ptr %t3.a.11
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
