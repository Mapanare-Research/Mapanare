; ModuleID = "11_closure"
target triple = "x86_64-pc-windows-msvc"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"

define void @"main"()
{
pre_entry:
  %"a.t2" = alloca {i8*, i8*}
  %"a.t3" = alloca i64
  %"a.t4" = alloca i8*
  %"a.t5" = alloca {i8*, i64}
  %"a.t6" = alloca i1
  br label %"entry"
entry:
  %"t2.env" = call i8* @"__mn_alloc"(i64 8)
  %"t2.envp" = bitcast i8* %"t2.env" to {i64}*
  %"t2.f0" = getelementptr {i64}, {i64}* %"t2.envp", i32 0, i32 0
  store i64 0, i64* %"t2.f0"
  %"t2.c0" = insertvalue {i8*, i8*} undef, i8* null, 0
  %"t2" = insertvalue {i8*, i8*} %"t2.c0", i8* %"t2.env", 1
  store {i8*, i8*} %"t2", {i8*, i8*}* %"a.t2"
  store i64 5, i64* %"a.t3"
  %"t4.cc.ptr" = bitcast i8* null to {i8*, i8*}*
  %"t4.cc" = load {i8*, i8*}, {i8*, i8*}* %"t4.cc.ptr"
  %"t4.fn" = extractvalue {i8*, i8*} %"t4.cc", 0
  %"t4.env" = extractvalue {i8*, i8*} %"t4.cc", 1
  %"t4.fptr" = bitcast i8* %"t4.fn" to i8* (i8*, i64)*
  %"t4" = call i8* %"t4.fptr"(i8* %"t4.env", i64 5)
  store i8* %"t4", i8** %"a.t4"
  %".str.0.ptr" = getelementptr inbounds [3 x i8], [3 x i8]* @".str.0", i64 0, i64 0
  %".str.0.s0" = insertvalue {i8*, i64} undef, i8* %".str.0.ptr", 0
  %".str.0.s1" = insertvalue {i8*, i64} %".str.0.s0", i64 3, 1
  store {i8*, i64} %".str.0.s1", {i8*, i64}* %"a.t5"
  call void @"__mn_str_println"({i8*, i64} %".str.0.s1")
  store i1 0, i1* %"a.t6"
  ret void
}

declare external i8* @"__mn_alloc"(i64 %".1")

@".str.0" = private constant [3 x i8] c"<?>", align 2
declare external void @"__mn_str_println"({i8*, i64} %".1")

!mapanare.version = !{ !0 }
!0 = !{ !"1.0.0" }