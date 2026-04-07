; ModuleID = '26_generics'
source_filename = "26_generics"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 2
@.str.0 = private constant [5 x i8] c"world", align 2

declare i32 @printf(ptr, ...)
declare {ptr, i64} @__mn_str_from_bool(i1)
declare void @__mn_str_println({ptr, i64})

define internal i64 @identity__Int(i64 %x) {
pre_entry:
  %x.addr = alloca i64, align 8
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  %l.0 = load i64, ptr %x.addr
  ret i64 %l.0
}

define internal i1 @identity__Bool(i1 %x) {
pre_entry:
  %x.addr = alloca i1, align 8
  store i1 %x, ptr %x.addr
  br label %entry
entry:
  %l.0 = load i1, ptr %x.addr
  ret i1 %l.0
}

define internal {ptr, i64} @identity__String({ptr, i64} %x) {
pre_entry:
  %x.addr = alloca {ptr, i64}, align 8
  store {ptr, i64} %x, ptr %x.addr
  br label %entry
entry:
  %l.0 = load {ptr, i64}, ptr %x.addr
  ret {ptr, i64} %l.0
}

define internal i64 @first__Int_Int(i64 %a, i64 %b) {
pre_entry:
  %a.addr = alloca i64, align 8
  %b.addr = alloca i64, align 8
  store i64 %a, ptr %a.addr
  store i64 %b, ptr %b.addr
  br label %entry
entry:
  %l.0 = load i64, ptr %a.addr
  ret i64 %l.0
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %t2.a.7 = alloca i1, align 8
  store i1 0, ptr %t2.a.7
  %t3.a.8 = alloca i1, align 8
  store i1 0, ptr %t3.a.8
  %t4.a.11 = alloca i1, align 8
  store i1 0, ptr %t4.a.11
  %t5.a.14 = alloca i1, align 8
  store i1 0, ptr %t5.a.14
  %t6.a.18 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.18
  %t7.a.21 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t7.a.21
  %t8.a.23 = alloca i1, align 8
  store i1 0, ptr %t8.a.23
  %t9.a.24 = alloca i64, align 8
  store i64 0, ptr %t9.a.24
  %t10.a.25 = alloca i64, align 8
  store i64 0, ptr %t10.a.25
  %t11.a.29 = alloca i64, align 8
  store i64 0, ptr %t11.a.29
  %t12.a.33 = alloca i1, align 8
  store i1 0, ptr %t12.a.33
  %t13.a.34 = alloca i64, align 8
  store i64 0, ptr %t13.a.34
  %t14.a.35 = alloca i1, align 8
  store i1 0, ptr %t14.a.35
  %t15.a.40 = alloca {i64, i1}, align 8
  store {i64, i1} zeroinitializer, ptr %t15.a.40
  %t16.a.43 = alloca i64, align 8
  store i64 0, ptr %t16.a.43
  %t17.a.47 = alloca i1, align 8
  store i1 0, ptr %t17.a.47
  br label %entry
entry:
  store i64 42, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %c.2 = call i64 @identity__Int(i64 %l.1)
  store i64 %c.2, ptr %t1.a.3
  %l.4 = load i64, ptr %t1.a.3
  %fp.5 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.6 = call i32 (ptr, ...) @printf(ptr %fp.5, i64 %l.4)
  store i1 0, ptr %t2.a.7
  store i1 1, ptr %t3.a.8
  %l.9 = load i1, ptr %t3.a.8
  %c.10 = call i1 @identity__Bool(i1 %l.9)
  store i1 %c.10, ptr %t4.a.11
  %l.12 = load i1, ptr %t4.a.11
  %rt.13 = call {ptr, i64} @__mn_str_from_bool(i1 %l.12)
  call void @__mn_str_println({ptr, i64} %rt.13)
  store i1 0, ptr %t5.a.14
  %sp.15 = getelementptr inbounds [5 x i8], ptr @.str.0, i64 0, i64 0
  %s.16 = insertvalue {ptr, i64} undef, ptr %sp.15, 0
  %s.17 = insertvalue {ptr, i64} %s.16, i64 5, 1
  store {ptr, i64} %s.17, ptr %t6.a.18
  %l.19 = load {ptr, i64}, ptr %t6.a.18
  %c.20 = call {ptr, i64} @identity__String({ptr, i64} %l.19)
  store {ptr, i64} %c.20, ptr %t7.a.21
  %l.22 = load {ptr, i64}, ptr %t7.a.21
  call void @__mn_str_println({ptr, i64} %l.22)
  store i1 0, ptr %t8.a.23
  store i64 10, ptr %t9.a.24
  store i64 20, ptr %t10.a.25
  %l.26 = load i64, ptr %t9.a.24
  %l.27 = load i64, ptr %t10.a.25
  %c.28 = call i64 @first__Int_Int(i64 %l.26, i64 %l.27)
  store i64 %c.28, ptr %t11.a.29
  %l.30 = load i64, ptr %t11.a.29
  %fp.31 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.32 = call i32 (ptr, ...) @printf(ptr %fp.31, i64 %l.30)
  store i1 0, ptr %t12.a.33
  store i64 100, ptr %t13.a.34
  store i1 1, ptr %t14.a.35
  %l.36 = load i64, ptr %t13.a.34
  %si.37 = insertvalue {i64, i1} undef, i64 %l.36, 0
  %l.38 = load i1, ptr %t14.a.35
  %si.39 = insertvalue {i64, i1} %si.37, i1 %l.38, 1
  store {i64, i1} %si.39, ptr %t15.a.40
  %fg.41 = getelementptr inbounds {i64, i1}, ptr %t15.a.40, i32 0, i32 0
  %fv.42 = load i64, ptr %fg.41
  store i64 %fv.42, ptr %t16.a.43
  %l.44 = load i64, ptr %t16.a.43
  %fp.45 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.46 = call i32 (ptr, ...) @printf(ptr %fp.45, i64 %l.44)
  store i1 0, ptr %t17.a.47
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
