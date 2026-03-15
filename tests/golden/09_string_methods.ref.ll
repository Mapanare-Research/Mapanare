; ModuleID = "09_string_methods"
target triple = "x86_64-pc-windows-msvc"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define void @"main"()
{
pre_entry:
  %"a.s" = alloca {i8*, i64}
  %"a.t1" = alloca {i8*, i64}
  %"a.t2" = alloca i1
  %"a.t3" = alloca {i8*, i64}
  %"a.t4" = alloca i1
  %"a.t5" = alloca {i8*, i64}
  %"a.t6" = alloca i1
  br label %"entry"
entry:
  %".str.0.ptr" = getelementptr inbounds [11 x i8], [11 x i8]* @".str.0", i64 0, i64 0
  %".str.0.s0" = insertvalue {i8*, i64} undef, i8* %".str.0.ptr", 0
  %".str.0.s1" = insertvalue {i8*, i64} %".str.0.s0", i64 11, 1
  store {i8*, i64} %".str.0.s1", {i8*, i64}* %"a.s"
  %".str.1.ptr" = getelementptr inbounds [5 x i8], [5 x i8]* @".str.1", i64 0, i64 0
  %".str.1.s0" = insertvalue {i8*, i64} undef, i8* %".str.1.ptr", 0
  %".str.1.s1" = insertvalue {i8*, i64} %".str.1.s0", i64 5, 1
  store {i8*, i64} %".str.1.s1", {i8*, i64}* %"a.t1"
  %"t2" = call i1 @"__mn_str_contains"({i8*, i64} %".str.0.s1", {i8*, i64} %".str.1.s1")
  store i1 %"t2", i1* %"a.t2"
  %"t3" = call {i8*, i64} @"__mn_str_from_bool"(i1 %"t2")
  store {i8*, i64} %"t3", {i8*, i64}* %"a.t3"
  call void @"__mn_str_println"({i8*, i64} %"t3")
  store i1 0, i1* %"a.t4"
  %"t5" = call {i8*, i64} @"__mn_str_to_upper"({i8*, i64} %".str.0.s1")
  store {i8*, i64} %"t5", {i8*, i64}* %"a.t5"
  call void @"__mn_str_println"({i8*, i64} %"t5")
  store i1 0, i1* %"a.t6"
  ret void
}

@".str.0" = private constant [11 x i8] c"hello world", align 2
@".str.1" = private constant [5 x i8] c"world", align 2
declare external i1 @"__mn_str_contains"({i8*, i64} %".1", {i8*, i64} %".2")

declare external {i8*, i64} @"__mn_str_from_bool"(i1 %".1")

declare external void @"__mn_str_println"({i8*, i64} %".1")

declare external {i8*, i64} @"__mn_str_to_upper"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }