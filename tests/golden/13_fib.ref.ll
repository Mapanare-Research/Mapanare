; ModuleID = "13_fib"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define internal i64 @"fib"(i64 %"n")
{
pre_entry:
  %"a.n" = alloca i64
  %"a.t0" = alloca i64
  %"a.t1" = alloca i1
  %"a.t3" = alloca i64
  %"a.t4" = alloca i64
  %"a.t5" = alloca i64
  %"a.t6" = alloca i64
  %"a.t7" = alloca i64
  %"a.t8" = alloca i64
  %"a.t9" = alloca i64
  br label %"entry"
entry:
  store i64 %"n", i64* %"a.n"
  store i64 1, i64* %"a.t0"
  %"t1" = icmp sle i64 %"n", 1
  store i1 %"t1", i1* %"a.t1"
  br i1 %"t1", label %"if_then0", label %"if_else1"
if_then0:
  %"l.n" = load i64, i64* %"a.n"
  ret i64 %"l.n"
if_else1:
  br label %"if_merge2"
if_merge2:
  store i64 1, i64* %"a.t3"
  %"l.n.1" = load i64, i64* %"a.n"
  %"t4" = sub i64 %"l.n.1", 1
  store i64 %"t4", i64* %"a.t4"
  %"t5" = call i64 @"fib"(i64 %"t4")
  store i64 %"t5", i64* %"a.t5"
  store i64 2, i64* %"a.t6"
  %"l.n.2" = load i64, i64* %"a.n"
  %"t7" = sub i64 %"l.n.2", 2
  store i64 %"t7", i64* %"a.t7"
  %"t8" = call i64 @"fib"(i64 %"t7")
  store i64 %"t8", i64* %"a.t8"
  %"t9" = add i64 %"t5", %"t8"
  store i64 %"t9", i64* %"a.t9"
  ret i64 %"t9"
}

define void @"main"()
{
pre_entry:
  %"a.t0" = alloca i64
  %"a.t1" = alloca i64
  %"a.t2" = alloca {i8*, i64}
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.t2"
  %"a.t3" = alloca i1
  br label %"entry"
entry:
  store i64 10, i64* %"a.t0"
  %"t1" = call i64 @"fib"(i64 10)
  store i64 %"t1", i64* %"a.t1"
  %"t2" = call {i8*, i64} @"__mn_str_from_int"(i64 %"t1")
  store {i8*, i64} %"t2", {i8*, i64}* %"a.t2"
  call void @"__mn_str_println"({i8*, i64} %"t2")
  store i1 0, i1* %"a.t3"
  ret void
}

declare external {i8*, i64} @"__mn_str_from_int"(i64 %".1")

declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }