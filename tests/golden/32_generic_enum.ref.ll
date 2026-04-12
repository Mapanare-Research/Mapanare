; ModuleID = '32_generic_enum'
source_filename = "32_generic_enum"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 8

declare i32 @printf(ptr, ...)
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t3.a.0 = alloca i64, align 8
  store i64 0, ptr %t3.a.0
  %t4.a.4 = alloca i1, align 8
  store i1 0, ptr %t4.a.4
  %t8.a.5 = alloca i64, align 8
  store i64 0, ptr %t8.a.5
  %t9.a.9 = alloca i1, align 8
  store i1 0, ptr %t9.a.9
  br label %entry
entry:
  store i64 42, ptr %t3.a.0
  %l.1 = load i64, ptr %t3.a.0
  %fp.2 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.3 = call i32 (ptr, ...) @printf(ptr %fp.2, i64 %l.1)
  store i1 0, ptr %t4.a.4
  store i64 99, ptr %t8.a.5
  %l.6 = load i64, ptr %t8.a.5
  %fp.7 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.8 = call i32 (ptr, ...) @printf(ptr %fp.7, i64 %l.6)
  store i1 0, ptr %t9.a.9
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
