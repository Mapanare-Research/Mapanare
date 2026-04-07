; ModuleID = '29_generic_impl'
source_filename = "29_generic_impl"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 2

declare i32 @printf(ptr, ...)

define internal i64 @Box__Int_get({i64} %self) {
pre_entry:
  %self.addr = alloca {i64}, align 8
  %t0.a.2 = alloca i64, align 8
  store i64 0, ptr %t0.a.2
  store {i64} %self, ptr %self.addr
  br label %entry
entry:
  %fg.0 = getelementptr inbounds {i64}, ptr %self.addr, i32 0, i32 0
  %fv.1 = load i64, ptr %fg.0
  store i64 %fv.1, ptr %t0.a.2
  %l.3 = load i64, ptr %t0.a.2
  ret i64 %l.3
}

define internal i64 @Box__Int_set({i64} %self, i64 %v) {
pre_entry:
  %self.addr = alloca {i64}, align 8
  %v.addr = alloca i64, align 8
  store {i64} %self, ptr %self.addr
  store i64 %v, ptr %v.addr
  br label %entry
entry:
  %l.0 = load i64, ptr %v.addr
  ret i64 %l.0
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.3 = alloca {i64}, align 8
  store {i64} zeroinitializer, ptr %t1.a.3
  %t3.a.6 = alloca i64, align 8
  store i64 0, ptr %t3.a.6
  %t4.a.10 = alloca i1, align 8
  store i1 0, ptr %t4.a.10
  %t5.a.11 = alloca i64, align 8
  store i64 0, ptr %t5.a.11
  %t7.a.15 = alloca i64, align 8
  store i64 0, ptr %t7.a.15
  %t8.a.19 = alloca i1, align 8
  store i1 0, ptr %t8.a.19
  %t9.a.20 = alloca i64, align 8
  store i64 0, ptr %t9.a.20
  %t10.a.23 = alloca {i64}, align 8
  store {i64} zeroinitializer, ptr %t10.a.23
  %t12.a.26 = alloca i64, align 8
  store i64 0, ptr %t12.a.26
  %t13.a.30 = alloca i1, align 8
  store i1 0, ptr %t13.a.30
  br label %entry
entry:
  store i64 42, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %si.2 = insertvalue {i64} undef, i64 %l.1, 0
  store {i64} %si.2, ptr %t1.a.3
  %l.4 = load {i64}, ptr %t1.a.3
  %c.5 = call i64 @Box__Int_get({i64} %l.4)
  store i64 %c.5, ptr %t3.a.6
  %l.7 = load i64, ptr %t3.a.6
  %fp.8 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.9 = call i32 (ptr, ...) @printf(ptr %fp.8, i64 %l.7)
  store i1 0, ptr %t4.a.10
  store i64 99, ptr %t5.a.11
  %l.12 = load {i64}, ptr %t1.a.3
  %l.13 = load i64, ptr %t5.a.11
  %c.14 = call i64 @Box__Int_set({i64} %l.12, i64 %l.13)
  store i64 %c.14, ptr %t7.a.15
  %l.16 = load i64, ptr %t7.a.15
  %fp.17 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.18 = call i32 (ptr, ...) @printf(ptr %fp.17, i64 %l.16)
  store i1 0, ptr %t8.a.19
  store i64 7, ptr %t9.a.20
  %l.21 = load i64, ptr %t9.a.20
  %si.22 = insertvalue {i64} undef, i64 %l.21, 0
  store {i64} %si.22, ptr %t10.a.23
  %l.24 = load {i64}, ptr %t10.a.23
  %c.25 = call i64 @Box__Int_get({i64} %l.24)
  store i64 %c.25, ptr %t12.a.26
  %l.27 = load i64, ptr %t12.a.26
  %fp.28 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.29 = call i32 (ptr, ...) @printf(ptr %fp.28, i64 %l.27)
  store i1 0, ptr %t13.a.30
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.14.0"}
