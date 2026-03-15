; ModuleID = "05_for_loop"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define void @"main"()
{
pre_entry:
  %"a.sum" = alloca i64
  %"a.t1" = alloca i64
  %"a.t2" = alloca i64
  %"a.t3" = alloca i8*
  %"a.has_next5" = alloca i1
  %"a.next6" = alloca i8*
  %"a.t7" = alloca i64
  %"a.t8" = alloca {i8*, i64}
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.t8"
  %"a.t9" = alloca i1
  br label %"entry"
entry:
  store i64 0, i64* %"a.sum"
  store i64 0, i64* %"a.t1"
  store i64 10, i64* %"a.t2"
  %"t3" = call i8* @"__range"(i64 0, i64 10)
  store i8* %"t3", i8** %"a.t3"
  br label %"for_header0"
for_header0:
  %"l.t3" = load i8*, i8** %"a.t3"
  %"has_next5" = call i1 @"__iter_has_next"(i8* %"l.t3")
  store i1 %"has_next5", i1* %"a.has_next5"
  br i1 %"has_next5", label %"for_body1", label %"for_exit2"
for_body1:
  %"l.t3.1" = load i8*, i8** %"a.t3"
  %"next6" = call i8* @"__iter_next"(i8* %"l.t3.1")
  store i8* %"next6", i8** %"a.next6"
  %"l.sum" = load i64, i64* %"a.sum"
  %"t7.rc" = ptrtoint i8* %"next6" to i64
  %"t7" = add i64 %"l.sum", %"t7.rc"
  store i64 %"t7", i64* %"a.t7"
  store i64 %"t7", i64* %"a.sum"
  br label %"for_header0"
for_exit2:
  %"l.sum.1" = load i64, i64* %"a.sum"
  %"t8" = call {i8*, i64} @"__mn_str_from_int"(i64 %"l.sum.1")
  store {i8*, i64} %"t8", {i8*, i64}* %"a.t8"
  call void @"__mn_str_println"({i8*, i64} %"t8")
  store i1 0, i1* %"a.t9"
  ret void
}

declare i8* @"__range"(i64 %".1", i64 %".2")

declare i1 @"__iter_has_next"(i8* %".1")

declare i8* @"__iter_next"(i8* %".1")

declare external {i8*, i64} @"__mn_str_from_int"(i64 %".1")

declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }