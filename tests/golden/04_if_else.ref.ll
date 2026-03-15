; ModuleID = "04_if_else"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define void @"main"()
{
pre_entry:
  %"a.t3" = alloca {i8*, i64}
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.t3"
  %"a.t4" = alloca i1
  br label %"entry"
entry:
  br label %"if_then0"
if_then0:
  %".str.0.ptr" = getelementptr inbounds [3 x i8], [3 x i8]* @".str.0", i64 0, i64 0
  %".str.0.s0" = insertvalue {i8*, i64} undef, i8* %".str.0.ptr", 0
  %".str.0.s1" = insertvalue {i8*, i64} %".str.0.s0", i64 3, 1
  store {i8*, i64} %".str.0.s1", {i8*, i64}* %"a.t3"
  call void @"__mn_str_println"({i8*, i64} %".str.0.s1")
  store i1 0, i1* %"a.t4"
  br label %"if_merge2"
if_merge2:
  ret void
}

@".str.0" = private constant [3 x i8] c"big", align 2
declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }