; ModuleID = "08_list"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define void @"main"()
{
pre_entry:
  %"a.t0" = alloca i64
  %"a.t1" = alloca i64
  %"a.t2" = alloca i64
  %"a.t3" = alloca {i8*, i64, i64, i64}
  store {i8*, i64, i64, i64} zeroinitializer, {i8*, i64, i64, i64}* %"a.t3"
  %"a.t4" = alloca i64
  %"a.t5" = alloca {i8*, i64, i64, i64}
  store {i8*, i64, i64, i64} zeroinitializer, {i8*, i64, i64, i64}* %"a.t5"
  %"a.t6" = alloca i64
  %"a.t7" = alloca {i8*, i64}
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.t7"
  %"a.t8" = alloca i1
  br label %"entry"
entry:
  store i64 1, i64* %"a.t0"
  store i64 2, i64* %"a.t1"
  store i64 3, i64* %"a.t2"
  %"t3.new" = call {i8*, i64, i64, i64} @"__mn_list_new"(i64 8)
  %"t3.ptr" = alloca {i8*, i64, i64, i64}
  store {i8*, i64, i64, i64} %"t3.new", {i8*, i64, i64, i64}* %"t3.ptr"
  %"t3.e0" = alloca i64
  store i64 1, i64* %"t3.e0"
  %".7" = bitcast i64* %"t3.e0" to i8*
  call void @"__mn_list_push"({i8*, i64, i64, i64}* %"t3.ptr", i8* %".7")
  %"t3.e1" = alloca i64
  store i64 2, i64* %"t3.e1"
  %".10" = bitcast i64* %"t3.e1" to i8*
  call void @"__mn_list_push"({i8*, i64, i64, i64}* %"t3.ptr", i8* %".10")
  %"t3.e2" = alloca i64
  store i64 3, i64* %"t3.e2"
  %".13" = bitcast i64* %"t3.e2" to i8*
  call void @"__mn_list_push"({i8*, i64, i64, i64}* %"t3.ptr", i8* %".13")
  %"t3" = load {i8*, i64, i64, i64}, {i8*, i64, i64, i64}* %"t3.ptr"
  store {i8*, i64, i64, i64} %"t3", {i8*, i64, i64, i64}* %"a.t3"
  store i64 4, i64* %"a.t4"
  %"t5.rl" = load {i8*, i64, i64, i64}, {i8*, i64, i64, i64}* %"a.t3"
  %"t5.lptr" = alloca {i8*, i64, i64, i64}
  store {i8*, i64, i64, i64} %"t5.rl", {i8*, i64, i64, i64}* %"t5.lptr"
  %"t5.eptr" = alloca i64
  store i64 4, i64* %"t5.eptr"
  %".20" = bitcast i64* %"t5.eptr" to i8*
  call void @"__mn_list_push"({i8*, i64, i64, i64}* %"t5.lptr", i8* %".20")
  %"t5" = load {i8*, i64, i64, i64}, {i8*, i64, i64, i64}* %"t5.lptr"
  store {i8*, i64, i64, i64} %"t5", {i8*, i64, i64, i64}* %"a.t5"
  store {i8*, i64, i64, i64} %"t5", {i8*, i64, i64, i64}* %"a.t3"
  %"t6.tmp" = alloca {i8*, i64, i64, i64}
  store {i8*, i64, i64, i64} %"t5", {i8*, i64, i64, i64}* %"t6.tmp"
  %"t6" = call i64 @"__mn_list_len"({i8*, i64, i64, i64}* %"t6.tmp")
  store i64 %"t6", i64* %"a.t6"
  %"t7" = call {i8*, i64} @"__mn_str_from_int"(i64 %"t6")
  store {i8*, i64} %"t7", {i8*, i64}* %"a.t7"
  call void @"__mn_str_println"({i8*, i64} %"t7")
  store i1 0, i1* %"a.t8"
  ret void
}

declare external {i8*, i64, i64, i64} @"__mn_list_new"(i64 %".1")

declare external void @"__mn_list_push"({i8*, i64, i64, i64}* %".1", i8* %".2")

declare external i64 @"__mn_list_len"({i8*, i64, i64, i64}* %".1")

declare external {i8*, i64} @"__mn_str_from_int"(i64 %".1")

declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }