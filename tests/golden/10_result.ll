; ModuleID = "10_result"
target triple = "x86_64-unknown-linux-gnu"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define internal {i1, {i64, {i8*, i64}}} @"divide"(i64 %"a", i64 %"b")
{
pre_entry:
  %"a.a" = alloca i64
  store i64 0, i64* %"a.a"
  %"a.b" = alloca i64
  store i64 0, i64* %"a.b"
  %"a.t0" = alloca i64
  store i64 0, i64* %"a.t0"
  %"a.t1" = alloca i1
  store i1 0, i1* %"a.t1"
  %"a.t2" = alloca {i8*, i64}
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.t2"
  %"a.t4" = alloca {i1, {i8*, {i8*, i64}}}
  store {i1, {i8*, {i8*, i64}}} zeroinitializer, {i1, {i8*, {i8*, i64}}}* %"a.t4"
  %"a.t6" = alloca i64
  store i64 0, i64* %"a.t6"
  %"a.t8" = alloca {i1, {i64, i8*}}
  store {i1, {i64, i8*}} zeroinitializer, {i1, {i64, i8*}}* %"a.t8"
  store i64 0, i64* %"a.a"
  store i64 0, i64* %"a.a"
  store i64 0, i64* %"a.b"
  store i64 0, i64* %"a.b"
  store i64 0, i64* %"a.t0"
  store i1 0, i1* %"a.t1"
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.t2"
  store {i1, {i8*, {i8*, i64}}} zeroinitializer, {i1, {i8*, {i8*, i64}}}* %"a.t4"
  store i64 0, i64* %"a.t6"
  store {i1, {i64, i8*}} zeroinitializer, {i1, {i64, i8*}}* %"a.t8"
  br label %"entry"
entry:
  store i64 %"a", i64* %"a.a"
  store i64 %"b", i64* %"a.b"
  store i64 0, i64* %"a.t0"
  %"t1" = icmp eq i64 %"b", 0
  store i1 %"t1", i1* %"a.t1"
  br i1 %"t1", label %"if_then0", label %"if_else1"
if_then0:
  %".str.0.ptr" = getelementptr inbounds [16 x i8], [16 x i8]* @".str.0", i64 0, i64 0
  %".str.0.s0" = insertvalue {i8*, i64} undef, i8* %".str.0.ptr", 0
  %".str.0.s1" = insertvalue {i8*, i64} %".str.0.s0", i64 16, 1
  store {i8*, i64} %".str.0.s1", {i8*, i64}* %"a.t2"
  %"t4.tag" = insertvalue {i1, {i8*, {i8*, i64}}} undef, i1 0, 0
  %"t4" = insertvalue {i1, {i8*, {i8*, i64}}} %"t4.tag", {i8*, i64} %".str.0.s1", 1, 1
  store {i1, {i8*, {i8*, i64}}} %"t4", {i1, {i8*, {i8*, i64}}}* %"a.t4"
  %"ret.c.tmp" = alloca {i1, {i8*, {i8*, i64}}}
  store {i1, {i8*, {i8*, i64}}} %"t4", {i1, {i8*, {i8*, i64}}}* %"ret.c.tmp"
  %"ret.c.ptr" = bitcast {i1, {i8*, {i8*, i64}}}* %"ret.c.tmp" to {i1, {i64, {i8*, i64}}}*
  %"ret.c" = load {i1, {i64, {i8*, i64}}}, {i1, {i64, {i8*, i64}}}* %"ret.c.ptr"
  ret {i1, {i64, {i8*, i64}}} %"ret.c"
if_else1:
  br label %"if_merge2"
if_merge2:
  %"l.a" = load i64, i64* %"a.a"
  %"l.b" = load i64, i64* %"a.b"
  %"t6" = sdiv i64 %"l.a", %"l.b"
  store i64 %"t6", i64* %"a.t6"
  %"t8.tag" = insertvalue {i1, {i64, i8*}} undef, i1 1, 0
  %"t8" = insertvalue {i1, {i64, i8*}} %"t8.tag", i64 %"t6", 1, 0
  store {i1, {i64, i8*}} %"t8", {i1, {i64, i8*}}* %"a.t8"
  %"ret.c.tmp.1" = alloca {i1, {i64, {i8*, i64}}}
  store {i1, {i64, {i8*, i64}}} zeroinitializer, {i1, {i64, {i8*, i64}}}* %"ret.c.tmp.1"
  %"ret.c.src" = bitcast {i1, {i64, {i8*, i64}}}* %"ret.c.tmp.1" to {i1, {i64, i8*}}*
  store {i1, {i64, i8*}} %"t8", {i1, {i64, i8*}}* %"ret.c.src"
  %"ret.c.1" = load {i1, {i64, {i8*, i64}}}, {i1, {i64, {i8*, i64}}}* %"ret.c.tmp.1"
  ret {i1, {i64, {i8*, i64}}} %"ret.c.1"
}

define void @"main"()
{
pre_entry:
  %"a.t0" = alloca i64
  store i64 0, i64* %"a.t0"
  %"a.t1" = alloca i64
  store i64 0, i64* %"a.t1"
  %"a.t2" = alloca {i1, {i64, {i8*, i64}}}
  store {i1, {i64, {i8*, i64}}} zeroinitializer, {i1, {i64, {i8*, i64}}}* %"a.t2"
  %"a.r" = alloca {i1, {i64, {i8*, i64}}}
  store {i1, {i64, {i8*, i64}}} zeroinitializer, {i1, {i64, {i8*, i64}}}* %"a.r"
  %"a.tag3" = alloca i1
  store i1 0, i1* %"a.tag3"
  %"a.v4" = alloca i64
  store i64 0, i64* %"a.v4"
  %"a.t5" = alloca {i8*, i64}
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.t5"
  %"a.t6" = alloca i1
  store i1 0, i1* %"a.t6"
  %"a.e7" = alloca {i8*, i64}
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.e7"
  %"a.t8" = alloca i1
  store i1 0, i1* %"a.t8"
  store i64 0, i64* %"a.t0"
  store i64 0, i64* %"a.t1"
  store {i1, {i64, {i8*, i64}}} zeroinitializer, {i1, {i64, {i8*, i64}}}* %"a.t2"
  store {i1, {i64, {i8*, i64}}} zeroinitializer, {i1, {i64, {i8*, i64}}}* %"a.r"
  store i1 0, i1* %"a.tag3"
  store i64 0, i64* %"a.v4"
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.t5"
  store i1 0, i1* %"a.t6"
  store {i8*, i64} zeroinitializer, {i8*, i64}* %"a.e7"
  store i1 0, i1* %"a.t8"
  br label %"entry"
entry:
  store i64 10, i64* %"a.t0"
  store i64 2, i64* %"a.t1"
  %"t2" = call {i1, {i64, {i8*, i64}}} @"divide"(i64 10, i64 2)
  store {i1, {i64, {i8*, i64}}} %"t2", {i1, {i64, {i8*, i64}}}* %"a.t2"
  store {i1, {i64, {i8*, i64}}} %"t2", {i1, {i64, {i8*, i64}}}* %"a.r"
  %"tag3" = extractvalue {i1, {i64, {i8*, i64}}} %"t2", 0
  store i1 %"tag3", i1* %"a.tag3"
  switch i1 %"tag3", label %"match_merge0" [i1 1, label %"match_arm1" i1 0, label %"match_arm2"]
match_merge0:
  ret void
match_arm1:
  %"l.r" = load {i1, {i64, {i8*, i64}}}, {i1, {i64, {i8*, i64}}}* %"a.r"
  %"v4" = extractvalue {i1, {i64, {i8*, i64}}} %"l.r", 1, 0
  store i64 %"v4", i64* %"a.v4"
  %"t5" = call {i8*, i64} @"__mn_str_from_int"(i64 %"v4")
  store {i8*, i64} %"t5", {i8*, i64}* %"a.t5"
  call void @"__mn_str_println"({i8*, i64} %"t5")
  store i1 0, i1* %"a.t6"
  br label %"match_merge0"
match_arm2:
  %"l.r.1" = load {i1, {i64, {i8*, i64}}}, {i1, {i64, {i8*, i64}}}* %"a.r"
  %"e7" = extractvalue {i1, {i64, {i8*, i64}}} %"l.r.1", 1, 1
  store {i8*, i64} %"e7", {i8*, i64}* %"a.e7"
  call void @"__mn_str_println"({i8*, i64} %"e7")
  store i1 0, i1* %"a.t8"
  br label %"match_merge0"
}

@".str.0" = private constant [16 x i8] c"division by zero", align 2
declare external {i8*, i64} @"__mn_str_from_int"(i64 %".1")

declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.10" }