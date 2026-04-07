; ModuleID = '26_generics'
source_filename = "26_generics"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 2
@.str.0 = private constant [5 x i8] c"world", align 2

declare i32 @printf(ptr, ...)

define internal i64 @identity__Int(i64 %x) {
pre_entry:
  %x.addr = alloca i64, align 8
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  %l.0 = load i64, ptr %x.addr
  ret i64 %l.0
}

define internal i64 @identity__Bool(i64 %x) {
pre_entry:
  %x.addr = alloca i64, align 8
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  %l.0 = load i64, ptr %x.addr
  ret i64 %l.0
}

define internal i64 @identity__String(i64 %x) {
pre_entry:
  %x.addr = alloca i64, align 8
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  %l.0 = load i64, ptr %x.addr
  ret i64 %l.0
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
  %t4.a.12 = alloca i64, align 8
  store i64 0, ptr %t4.a.12
  %t5.a.16 = alloca i1, align 8
  store i1 0, ptr %t5.a.16
  %t6.a.20 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.20
  %rc.22 = alloca {ptr, i64}, align 8
  %t7.a.25 = alloca i64, align 8
  store i64 0, ptr %t7.a.25
  %t8.a.29 = alloca i1, align 8
  store i1 0, ptr %t8.a.29
  %t9.a.30 = alloca i64, align 8
  store i64 0, ptr %t9.a.30
  %t10.a.31 = alloca i64, align 8
  store i64 0, ptr %t10.a.31
  %t11.a.35 = alloca i64, align 8
  store i64 0, ptr %t11.a.35
  %t12.a.39 = alloca i1, align 8
  store i1 0, ptr %t12.a.39
  %t13.a.40 = alloca i64, align 8
  store i64 0, ptr %t13.a.40
  %t14.a.41 = alloca i1, align 8
  store i1 0, ptr %t14.a.41
  %t15.a.46 = alloca {i64, i1}, align 8
  store {i64, i1} zeroinitializer, ptr %t15.a.46
  %t16.a.49 = alloca i64, align 8
  store i64 0, ptr %t16.a.49
  %t17.a.53 = alloca i1, align 8
  store i1 0, ptr %t17.a.53
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
  %zx.10 = zext i1 %l.9 to i64
  %c.11 = call i64 @identity__Bool(i64 %zx.10)
  store i64 %c.11, ptr %t4.a.12
  %l.13 = load i64, ptr %t4.a.12
  %fp.14 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.15 = call i32 (ptr, ...) @printf(ptr %fp.14, i64 %l.13)
  store i1 0, ptr %t5.a.16
  %sp.17 = getelementptr inbounds [5 x i8], ptr @.str.0, i64 0, i64 0
  %s.18 = insertvalue {ptr, i64} undef, ptr %sp.17, 0
  %s.19 = insertvalue {ptr, i64} %s.18, i64 5, 1
  store {ptr, i64} %s.19, ptr %t6.a.20
  %l.21 = load {ptr, i64}, ptr %t6.a.20
  store {ptr, i64} %l.21, ptr %rc.22
  %rv.23 = load i64, ptr %rc.22
  %c.24 = call i64 @identity__String(i64 %rv.23)
  store i64 %c.24, ptr %t7.a.25
  %l.26 = load i64, ptr %t7.a.25
  %fp.27 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.28 = call i32 (ptr, ...) @printf(ptr %fp.27, i64 %l.26)
  store i1 0, ptr %t8.a.29
  store i64 10, ptr %t9.a.30
  store i64 20, ptr %t10.a.31
  %l.32 = load i64, ptr %t9.a.30
  %l.33 = load i64, ptr %t10.a.31
  %c.34 = call i64 @first__Int_Int(i64 %l.32, i64 %l.33)
  store i64 %c.34, ptr %t11.a.35
  %l.36 = load i64, ptr %t11.a.35
  %fp.37 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.38 = call i32 (ptr, ...) @printf(ptr %fp.37, i64 %l.36)
  store i1 0, ptr %t12.a.39
  store i64 100, ptr %t13.a.40
  store i1 1, ptr %t14.a.41
  %l.42 = load i64, ptr %t13.a.40
  %si.43 = insertvalue {i64, i1} undef, i64 %l.42, 0
  %l.44 = load i1, ptr %t14.a.41
  %si.45 = insertvalue {i64, i1} %si.43, i1 %l.44, 1
  store {i64, i1} %si.45, ptr %t15.a.46
  %fg.47 = getelementptr inbounds {i64, i1}, ptr %t15.a.46, i32 0, i32 0
  %fv.48 = load i64, ptr %fg.47
  store i64 %fv.48, ptr %t16.a.49
  %l.50 = load i64, ptr %t16.a.49
  %fp.51 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.52 = call i32 (ptr, ...) @printf(ptr %fp.51, i64 %l.50)
  store i1 0, ptr %t17.a.53
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
