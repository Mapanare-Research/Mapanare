; ModuleID = "01_hello"
target triple = "x86_64-pc-windows-msvc"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define void @"main"()
{
pre_entry:
  %"a.t0" = alloca {i8*, i64}
  %"a.t1" = alloca i1
  br label %"entry"
entry:
  %".str.0.ptr" = getelementptr inbounds [5 x i8], [5 x i8]* @".str.0", i64 0, i64 0
  %".str.0.s0" = insertvalue {i8*, i64} undef, i8* %".str.0.ptr", 0
  %".str.0.s1" = insertvalue {i8*, i64} %".str.0.s0", i64 5, 1
  store {i8*, i64} %".str.0.s1", {i8*, i64}* %"a.t0"
  call void @"__mn_str_println"({i8*, i64} %".str.0.s1")
  store i1 0, i1* %"a.t1"
  ret void
}

@".str.0" = private constant [5 x i8] c"hello", align 2
declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }