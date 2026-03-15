; ModuleID = "07_enum_match"
target triple = "x86_64-pc-windows-msvc"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define void @"main"()
{
pre_entry:
  %"a.t0" = alloca i8*
  %"a.c" = alloca i8*
  %"a.tag1" = alloca i32
  %"a.t2" = alloca {i8*, i64}
  %"a.t3" = alloca i1
  %"a.t4" = alloca {i8*, i64}
  %"a.t5" = alloca i1
  br label %"entry"
entry:
  %"t0" = call i8* @"Color_Green"()
  store i8* %"t0", i8** %"a.t0"
  store i8* %"t0", i8** %"a.c"
  %"tag1.eptr" = bitcast i8* %"t0" to {i32, [8 x i8]}*
  %"tag1.loaded" = load {i32, [8 x i8]}, {i32, [8 x i8]}* %"tag1.eptr"
  %"tag1" = extractvalue {i32, [8 x i8]} %"tag1.loaded", 0
  store i32 %"tag1", i32* %"a.tag1"
  switch i32 %"tag1", label %"match_arm2" [i32 1, label %"match_arm1"]
match_merge0:
  ret void
match_arm1:
  %".str.0.ptr" = getelementptr inbounds [5 x i8], [5 x i8]* @".str.0", i64 0, i64 0
  %".str.0.s0" = insertvalue {i8*, i64} undef, i8* %".str.0.ptr", 0
  %".str.0.s1" = insertvalue {i8*, i64} %".str.0.s0", i64 5, 1
  store {i8*, i64} %".str.0.s1", {i8*, i64}* %"a.t2"
  call void @"__mn_str_println"({i8*, i64} %".str.0.s1")
  store i1 0, i1* %"a.t3"
  br label %"match_merge0"
match_arm2:
  %".str.1.ptr" = getelementptr inbounds [5 x i8], [5 x i8]* @".str.1", i64 0, i64 0
  %".str.1.s0" = insertvalue {i8*, i64} undef, i8* %".str.1.ptr", 0
  %".str.1.s1" = insertvalue {i8*, i64} %".str.1.s0", i64 5, 1
  store {i8*, i64} %".str.1.s1", {i8*, i64}* %"a.t4"
  call void @"__mn_str_println"({i8*, i64} %".str.1.s1")
  store i1 0, i1* %"a.t5"
  br label %"match_merge0"
}

declare i8* @"Color_Green"()

@".str.0" = private constant [5 x i8] c"green", align 2
declare external void @"__mn_str_println"({i8*, i64} %".1")

@".str.1" = private constant [5 x i8] c"other", align 2
!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }