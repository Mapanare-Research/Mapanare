; ModuleID = "03_function"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define internal i64 @"add"(i64 %"a", i64 %"b")
{
pre_entry:
  %"a.a" = alloca i64
  %"a.b" = alloca i64
  %"a.t0" = alloca i64
  br label %"entry"
entry:
  store i64 %"a", i64* %"a.a"
  store i64 %"b", i64* %"a.b"
  %"t0" = add i64 %"a", %"b"
  store i64 %"t0", i64* %"a.t0"
  ret i64 %"t0"
}

define void @"main"()
{
pre_entry:
  %"a.t0" = alloca i64
  %"a.t1" = alloca i64
  %"a.t2" = alloca i64
  %"a.t3" = alloca {i8*, i64}
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.t3"
  %"a.t4" = alloca i1
  br label %"entry"
entry:
  store i64 10, i64* %"a.t0"
  store i64 20, i64* %"a.t1"
  %"t2" = call i64 @"add"(i64 10, i64 20)
  store i64 %"t2", i64* %"a.t2"
  %"t3" = call {i8*, i64} @"__mn_str_from_int"(i64 %"t2")
  store {i8*, i64} %"t3", {i8*, i64}* %"a.t3"
  call void @"__mn_str_println"({i8*, i64} %"t3")
  store i1 0, i1* %"a.t4"
  ret void
}

declare external {i8*, i64} @"__mn_str_from_int"(i64 %".1")

declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }