; ModuleID = "12_while"
target triple = "x86_64-pc-windows-msvc"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define void @"main"()
{
pre_entry:
  %"a.i" = alloca i64
  %"a.t1" = alloca i64
  %"a.t2" = alloca i1
  %"a.t3" = alloca i64
  %"a.t4" = alloca i64
  %"a.t5" = alloca {i8*, i64}
  %"a.t6" = alloca i1
  br label %"entry"
entry:
  store i64 0, i64* %"a.i"
  br label %"while_header0"
while_header0:
  store i64 5, i64* %"a.t1"
  %"l.i" = load i64, i64* %"a.i"
  %"t2" = icmp slt i64 %"l.i", 5
  store i1 %"t2", i1* %"a.t2"
  br i1 %"t2", label %"while_body1", label %"while_exit2"
while_body1:
  store i64 1, i64* %"a.t3"
  %"l.i.1" = load i64, i64* %"a.i"
  %"t4" = add i64 %"l.i.1", 1
  store i64 %"t4", i64* %"a.t4"
  store i64 %"t4", i64* %"a.i"
  br label %"while_header0"
while_exit2:
  %"l.i.2" = load i64, i64* %"a.i"
  %"t5" = call {i8*, i64} @"__mn_str_from_int"(i64 %"l.i.2")
  store {i8*, i64} %"t5", {i8*, i64}* %"a.t5"
  call void @"__mn_str_println"({i8*, i64} %"t5")
  store i1 0, i1* %"a.t6"
  ret void
}

declare external {i8*, i64} @"__mn_str_from_int"(i64 %".1")

declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }