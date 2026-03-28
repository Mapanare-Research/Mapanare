; ModuleID = '01_hello'
source_filename = "01_hello"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-w64-windows-gnu"

@.str.0 = private constant [5 x i8] c"hello", align 2

declare void @__mn_str_print({i8*, i64}*)

define i64 @main() {
pre_entry:
  %t0.a.3 = alloca {i8*, i64}, align 8
  store {i8*, i64} zeroinitializer, {i8*, i64}* %t0.a.3
  %sarg.5 = alloca {i8*, i64}, align 8
  %t1.a.6 = alloca i1, align 8
  store i1 0, i1* %t1.a.6
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [5 x i8], [5 x i8]* @.str.0, i64 0, i64 0
  %s.1 = insertvalue {i8*, i64} undef, i8* %sp.0, 0
  %s.2 = insertvalue {i8*, i64} %s.1, i64 5, 1
  store {i8*, i64} %s.2, {i8*, i64}* %t0.a.3
  %l.4 = load {i8*, i64}, {i8*, i64}* %t0.a.3
  store {i8*, i64} %l.4, {i8*, i64}* %sarg.5
  call void @__mn_str_print({i8*, i64}* %sarg.5)
  store i1 0, i1* %t1.a.6
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"2.0.0"}
