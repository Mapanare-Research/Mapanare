; ModuleID = '31_generic_multi'
source_filename = "31_generic_multi"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 2

declare i32 @printf(ptr, ...)

define internal i64 @Container__Int_get({i64, i64} %self) {
pre_entry:
  %self.addr = alloca {i64, i64}, align 8
  %t0.a.2 = alloca i64, align 8
  store i64 0, ptr %t0.a.2
  store {i64, i64} %self, ptr %self.addr
  br label %entry
entry:
  %fg.0 = getelementptr inbounds {i64, i64}, ptr %self.addr, i32 0, i32 0
  %fv.1 = load i64, ptr %fg.0
  store i64 %fv.1, ptr %t0.a.2
  %l.3 = load i64, ptr %t0.a.2
  ret i64 %l.3
}

define internal i64 @Container__Int_times({i64, i64} %self) {
pre_entry:
  %self.addr = alloca {i64, i64}, align 8
  %t0.a.2 = alloca i64, align 8
  store i64 0, ptr %t0.a.2
  store {i64, i64} %self, ptr %self.addr
  br label %entry
entry:
  %fg.0 = getelementptr inbounds {i64, i64}, ptr %self.addr, i32 0, i32 1
  %fv.1 = load i64, ptr %fg.0
  store i64 %fv.1, ptr %t0.a.2
  %l.3 = load i64, ptr %t0.a.2
  ret i64 %l.3
}

define internal i64 @identity__Int(i64 %x) {
pre_entry:
  %x.addr = alloca i64, align 8
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  %l.0 = load i64, ptr %x.addr
  ret i64 %l.0
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.6 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %t2.a.6
  %t4.a.9 = alloca i64, align 8
  store i64 0, ptr %t4.a.9
  %t5.a.13 = alloca i1, align 8
  store i1 0, ptr %t5.a.13
  %t7.a.16 = alloca i64, align 8
  store i64 0, ptr %t7.a.16
  %t8.a.20 = alloca i1, align 8
  store i1 0, ptr %t8.a.20
  %t9.a.21 = alloca i64, align 8
  store i64 0, ptr %t9.a.21
  %t10.a.22 = alloca i64, align 8
  store i64 0, ptr %t10.a.22
  %t11.a.27 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %t11.a.27
  %t13.a.30 = alloca i64, align 8
  store i64 0, ptr %t13.a.30
  %t14.a.34 = alloca i1, align 8
  store i1 0, ptr %t14.a.34
  %t16.a.37 = alloca i64, align 8
  store i64 0, ptr %t16.a.37
  %t17.a.41 = alloca i1, align 8
  store i1 0, ptr %t17.a.41
  %t18.a.42 = alloca i64, align 8
  store i64 0, ptr %t18.a.42
  %t19.a.45 = alloca i64, align 8
  store i64 0, ptr %t19.a.45
  %t20.a.49 = alloca i1, align 8
  store i1 0, ptr %t20.a.49
  br label %entry
entry:
  store i64 42, ptr %t0.a.0
  store i64 1, ptr %t1.a.1
  %l.2 = load i64, ptr %t0.a.0
  %si.3 = insertvalue {i64, i64} undef, i64 %l.2, 0
  %l.4 = load i64, ptr %t1.a.1
  %si.5 = insertvalue {i64, i64} %si.3, i64 %l.4, 1
  store {i64, i64} %si.5, ptr %t2.a.6
  %l.7 = load {i64, i64}, ptr %t2.a.6
  %c.8 = call i64 @Container__Int_get({i64, i64} %l.7)
  store i64 %c.8, ptr %t4.a.9
  %l.10 = load i64, ptr %t4.a.9
  %fp.11 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.12 = call i32 (ptr, ...) @printf(ptr %fp.11, i64 %l.10)
  store i1 0, ptr %t5.a.13
  %l.14 = load {i64, i64}, ptr %t2.a.6
  %c.15 = call i64 @Container__Int_times({i64, i64} %l.14)
  store i64 %c.15, ptr %t7.a.16
  %l.17 = load i64, ptr %t7.a.16
  %fp.18 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.19 = call i32 (ptr, ...) @printf(ptr %fp.18, i64 %l.17)
  store i1 0, ptr %t8.a.20
  store i64 100, ptr %t9.a.21
  store i64 3, ptr %t10.a.22
  %l.23 = load i64, ptr %t9.a.21
  %si.24 = insertvalue {i64, i64} undef, i64 %l.23, 0
  %l.25 = load i64, ptr %t10.a.22
  %si.26 = insertvalue {i64, i64} %si.24, i64 %l.25, 1
  store {i64, i64} %si.26, ptr %t11.a.27
  %l.28 = load {i64, i64}, ptr %t11.a.27
  %c.29 = call i64 @Container__Int_get({i64, i64} %l.28)
  store i64 %c.29, ptr %t13.a.30
  %l.31 = load i64, ptr %t13.a.30
  %fp.32 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.33 = call i32 (ptr, ...) @printf(ptr %fp.32, i64 %l.31)
  store i1 0, ptr %t14.a.34
  %l.35 = load {i64, i64}, ptr %t11.a.27
  %c.36 = call i64 @Container__Int_times({i64, i64} %l.35)
  store i64 %c.36, ptr %t16.a.37
  %l.38 = load i64, ptr %t16.a.37
  %fp.39 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.40 = call i32 (ptr, ...) @printf(ptr %fp.39, i64 %l.38)
  store i1 0, ptr %t17.a.41
  store i64 77, ptr %t18.a.42
  %l.43 = load i64, ptr %t18.a.42
  %c.44 = call i64 @identity__Int(i64 %l.43)
  store i64 %c.44, ptr %t19.a.45
  %l.46 = load i64, ptr %t19.a.45
  %fp.47 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.48 = call i32 (ptr, ...) @printf(ptr %fp.47, i64 %l.46)
  store i1 0, ptr %t20.a.49
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
