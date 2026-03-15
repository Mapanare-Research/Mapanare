; ModuleID = "02_arithmetic"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define void @"main"()
{
pre_entry:
  %"a.x" = alloca i64
  %"a.t5" = alloca {i8*, i64}
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.t5"
  %"a.t6" = alloca i1
  br label %"entry"
entry:
  store i64 14, i64* %"a.x"
  %"t5" = call {i8*, i64} @"__mn_str_from_int"(i64 14)
  store {i8*, i64} %"t5", {i8*, i64}* %"a.t5"
  call void @"__mn_str_println"({i8*, i64} %"t5")
  store i1 0, i1* %"a.t6"
  ret void
}

declare external {i8*, i64} @"__mn_str_from_int"(i64 %".1")

declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }