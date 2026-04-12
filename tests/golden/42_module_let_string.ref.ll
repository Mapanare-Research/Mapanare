; ModuleID = '42_module_let_string'
source_filename = "42_module_let_string"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@MAX = private constant i64 100
@GREETING = private constant [5 x i8] c"hello"
@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 8
@.str.0 = private constant [5 x i8] c"hello", align 8

declare i32 @printf(ptr, ...)
declare void @__mn_str_println({ptr, i64})
declare void @__mn_intern_destroy()

define internal i64 @get_max() {
pre_entry:
  %MAX0.a.0 = alloca i64, align 8
  store i64 0, ptr %MAX0.a.0
  br label %entry
entry:
  store i64 100, ptr %MAX0.a.0
  %l.1 = load i64, ptr %MAX0.a.0
  ret i64 %l.1
}

define i64 @main() {
pre_entry:
  %t0.a.1 = alloca i64, align 8
  store i64 0, ptr %t0.a.1
  %t1.a.5 = alloca i1, align 8
  store i1 0, ptr %t1.a.5
  %GREETING2.a.9 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %GREETING2.a.9
  %t3.a.11 = alloca i1, align 8
  store i1 0, ptr %t3.a.11
  br label %entry
entry:
  %c.0 = call i64 @get_max()
  store i64 %c.0, ptr %t0.a.1
  %l.2 = load i64, ptr %t0.a.1
  %fp.3 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.4 = call i32 (ptr, ...) @printf(ptr %fp.3, i64 %l.2)
  store i1 0, ptr %t1.a.5
  %sp.6 = getelementptr inbounds [5 x i8], ptr @.str.0, i64 0, i64 0
  %s.7 = insertvalue {ptr, i64} undef, ptr %sp.6, 0
  %s.8 = insertvalue {ptr, i64} %s.7, i64 5, 1
  store {ptr, i64} %s.8, ptr %GREETING2.a.9
  %l.10 = load {ptr, i64}, ptr %GREETING2.a.9
  call void @__mn_str_println({ptr, i64} %l.10)
  store i1 0, ptr %t3.a.11
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
