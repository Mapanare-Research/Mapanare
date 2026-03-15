; ModuleID = "14_nested_struct"
target triple = "x86_64-pc-windows-msvc"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define void @"main"()
{
pre_entry:
  %"a.t0" = alloca i64
  %"a.t1" = alloca i64
  %"a.t2" = alloca {i64, i64}
  %"a.t3" = alloca i64
  %"a.t4" = alloca {i8*, i64}
  %"a.t5" = alloca i1
  br label %"entry"
entry:
  store i64 10, i64* %"a.t0"
  store i64 20, i64* %"a.t1"
  %"t2.f0" = insertvalue {i64, i64} undef, i64 10, 0
  %"t2.f1" = insertvalue {i64, i64} %"t2.f0", i64 20, 1
  store {i64, i64} %"t2.f1", {i64, i64}* %"a.t2"
  %"t3" = extractvalue {i64, i64} %"t2.f1", 0
  store i64 %"t3", i64* %"a.t3"
  %"t4" = call {i8*, i64} @"__mn_str_from_int"(i64 %"t3")
  store {i8*, i64} %"t4", {i8*, i64}* %"a.t4"
  call void @"__mn_str_println"({i8*, i64} %"t4")
  store i1 0, i1* %"a.t5"
  ret void
}

declare external {i8*, i64} @"__mn_str_from_int"(i64 %".1")

declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }