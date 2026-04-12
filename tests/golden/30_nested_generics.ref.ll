; ModuleID = '30_nested_generics'
source_filename = "30_nested_generics"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 8

declare i32 @printf(ptr, ...)
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.6 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %t2.a.6
  %inner.a.8 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %inner.a.8
  %t3.a.9 = alloca i64, align 8
  store i64 0, ptr %t3.a.9
  %t4.a.14 = alloca {{i64, i64}, i64}, align 8
  store {{i64, i64}, i64} zeroinitializer, ptr %t4.a.14
  %t5.a.17 = alloca i64, align 8
  store i64 0, ptr %t5.a.17
  %t6.a.21 = alloca i1, align 8
  store i1 0, ptr %t6.a.21
  %t7.a.24 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %t7.a.24
  %t8.a.27 = alloca i64, align 8
  store i64 0, ptr %t8.a.27
  %t9.a.31 = alloca i1, align 8
  store i1 0, ptr %t9.a.31
  %t10.a.34 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %t10.a.34
  %t11.a.37 = alloca i64, align 8
  store i64 0, ptr %t11.a.37
  %t12.a.41 = alloca i1, align 8
  store i1 0, ptr %t12.a.41
  %t13.a.42 = alloca i64, align 8
  store i64 0, ptr %t13.a.42
  %t14.a.43 = alloca i1, align 8
  store i1 0, ptr %t14.a.43
  %t15.a.48 = alloca {i64, i1}, align 8
  store {i64, i1} zeroinitializer, ptr %t15.a.48
  %t16.a.51 = alloca i64, align 8
  store i64 0, ptr %t16.a.51
  %t17.a.55 = alloca i1, align 8
  store i1 0, ptr %t17.a.55
  br label %entry
entry:
  store i64 10, ptr %t0.a.0
  store i64 20, ptr %t1.a.1
  %l.2 = load i64, ptr %t0.a.0
  %si.3 = insertvalue {i64, i64} undef, i64 %l.2, 0
  %l.4 = load i64, ptr %t1.a.1
  %si.5 = insertvalue {i64, i64} %si.3, i64 %l.4, 1
  store {i64, i64} %si.5, ptr %t2.a.6
  %l.7 = load {i64, i64}, ptr %t2.a.6
  store {i64, i64} %l.7, ptr %inner.a.8
  store i64 99, ptr %t3.a.9
  %l.10 = load {i64, i64}, ptr %inner.a.8
  %si.11 = insertvalue {{i64, i64}, i64} undef, {i64, i64} %l.10, 0
  %l.12 = load i64, ptr %t3.a.9
  %si.13 = insertvalue {{i64, i64}, i64} %si.11, i64 %l.12, 1
  store {{i64, i64}, i64} %si.13, ptr %t4.a.14
  %fg.15 = getelementptr inbounds {{i64, i64}, i64}, ptr %t4.a.14, i32 0, i32 1
  %fv.16 = load i64, ptr %fg.15
  store i64 %fv.16, ptr %t5.a.17
  %l.18 = load i64, ptr %t5.a.17
  %fp.19 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.20 = call i32 (ptr, ...) @printf(ptr %fp.19, i64 %l.18)
  store i1 0, ptr %t6.a.21
  %fg.22 = getelementptr inbounds {{i64, i64}, i64}, ptr %t4.a.14, i32 0, i32 0
  %fv.23 = load {i64, i64}, ptr %fg.22
  store {i64, i64} %fv.23, ptr %t7.a.24
  %fg.25 = getelementptr inbounds {i64, i64}, ptr %t7.a.24, i32 0, i32 0
  %fv.26 = load i64, ptr %fg.25
  store i64 %fv.26, ptr %t8.a.27
  %l.28 = load i64, ptr %t8.a.27
  %fp.29 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.30 = call i32 (ptr, ...) @printf(ptr %fp.29, i64 %l.28)
  store i1 0, ptr %t9.a.31
  %fg.32 = getelementptr inbounds {{i64, i64}, i64}, ptr %t4.a.14, i32 0, i32 0
  %fv.33 = load {i64, i64}, ptr %fg.32
  store {i64, i64} %fv.33, ptr %t10.a.34
  %fg.35 = getelementptr inbounds {i64, i64}, ptr %t10.a.34, i32 0, i32 1
  %fv.36 = load i64, ptr %fg.35
  store i64 %fv.36, ptr %t11.a.37
  %l.38 = load i64, ptr %t11.a.37
  %fp.39 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.40 = call i32 (ptr, ...) @printf(ptr %fp.39, i64 %l.38)
  store i1 0, ptr %t12.a.41
  store i64 42, ptr %t13.a.42
  store i1 1, ptr %t14.a.43
  %l.44 = load i64, ptr %t13.a.42
  %si.45 = insertvalue {i64, i1} undef, i64 %l.44, 0
  %l.46 = load i1, ptr %t14.a.43
  %si.47 = insertvalue {i64, i1} %si.45, i1 %l.46, 1
  store {i64, i1} %si.47, ptr %t15.a.48
  %fg.49 = getelementptr inbounds {i64, i1}, ptr %t15.a.48, i32 0, i32 0
  %fv.50 = load i64, ptr %fg.49
  store i64 %fv.50, ptr %t16.a.51
  %l.52 = load i64, ptr %t16.a.51
  %fp.53 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.54 = call i32 (ptr, ...) @printf(ptr %fp.53, i64 %l.52)
  store i1 0, ptr %t17.a.55
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.34.0"}
