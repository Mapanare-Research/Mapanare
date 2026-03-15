; ModuleID = "15_multifunction"
target triple = "x86_64-pc-windows-msvc"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define internal i64 @"double"(i64 %"x")
{
pre_entry:
  %"a.x" = alloca i64
  %"a.t0" = alloca i64
  %"a.t1" = alloca i64
  br label %"entry"
entry:
  store i64 %"x", i64* %"a.x"
  store i64 2, i64* %"a.t0"
  %"t1" = mul i64 %"x", 2
  store i64 %"t1", i64* %"a.t1"
  ret i64 %"t1"
}

define internal i64 @"triple"(i64 %"x")
{
pre_entry:
  %"a.x" = alloca i64
  %"a.t0" = alloca i64
  %"a.t1" = alloca i64
  br label %"entry"
entry:
  store i64 %"x", i64* %"a.x"
  store i64 3, i64* %"a.t0"
  %"t1" = mul i64 %"x", 3
  store i64 %"t1", i64* %"a.t1"
  ret i64 %"t1"
}

define void @"main"()
{
pre_entry:
  %"a.t0" = alloca i64
  %"a.t1" = alloca i64
  %"a.t2" = alloca {i8*, i64}
  %"a.t3" = alloca i1
  %"a.t4" = alloca i64
  %"a.t5" = alloca i64
  %"a.t6" = alloca {i8*, i64}
  %"a.t7" = alloca i1
  br label %"entry"
entry:
  store i64 5, i64* %"a.t0"
  %"t1" = call i64 @"double"(i64 5)
  store i64 %"t1", i64* %"a.t1"
  %"t2" = call {i8*, i64} @"__mn_str_from_int"(i64 %"t1")
  store {i8*, i64} %"t2", {i8*, i64}* %"a.t2"
  call void @"__mn_str_println"({i8*, i64} %"t2")
  store i1 0, i1* %"a.t3"
  store i64 5, i64* %"a.t4"
  %"t5" = call i64 @"triple"(i64 5)
  store i64 %"t5", i64* %"a.t5"
  %"t6" = call {i8*, i64} @"__mn_str_from_int"(i64 %"t5")
  store {i8*, i64} %"t6", {i8*, i64}* %"a.t6"
  call void @"__mn_str_println"({i8*, i64} %"t6")
  store i1 0, i1* %"a.t7"
  ret void
}

declare external {i8*, i64} @"__mn_str_from_int"(i64 %".1")

declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }