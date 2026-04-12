; ModuleID = '04_if_else'
source_filename = "04_if_else"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [3 x i8] c"big", align 8

declare void @__mn_str_println({ptr, i64})
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t3.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.3
  %t4.a.5 = alloca i1, align 8
  store i1 0, ptr %t4.a.5
  br label %entry
entry:
  br label %if_then0
if_then0:
  %sp.0 = getelementptr inbounds [3 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 3, 1
  store {ptr, i64} %s.2, ptr %t3.a.3
  %l.4 = load {ptr, i64}, ptr %t3.a.3
  call void @__mn_str_println({ptr, i64} %l.4)
  store i1 0, ptr %t4.a.5
  br label %if_merge2
if_merge2:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
