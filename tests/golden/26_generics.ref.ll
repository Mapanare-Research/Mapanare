; ModuleID = '26_generics'
source_filename = "26_generics"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 8
@.str.0 = private constant [5 x i8] c"world", align 8

declare i32 @printf(ptr, ...)
declare {ptr, i64} @__mn_str_from_bool(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

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
  %str_track.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.15
  %t5.a.16 = alloca i1, align 8
  store i1 0, ptr %t5.a.16
  %t6.a.20 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.20
  %t7.a.23 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t7.a.23
  %t8.a.25 = alloca i1, align 8
  store i1 0, ptr %t8.a.25
  %t9.a.26 = alloca i64, align 8
  store i64 0, ptr %t9.a.26
  %t10.a.27 = alloca i64, align 8
  store i64 0, ptr %t10.a.27
  %t11.a.31 = alloca i64, align 8
  store i64 0, ptr %t11.a.31
  %t12.a.35 = alloca i1, align 8
  store i1 0, ptr %t12.a.35
  %t13.a.36 = alloca i64, align 8
  store i64 0, ptr %t13.a.36
  %t14.a.37 = alloca i1, align 8
  store i1 0, ptr %t14.a.37
  %t15.a.42 = alloca {i64, i1}, align 8
  store {i64, i1} zeroinitializer, ptr %t15.a.42
  %t16.a.45 = alloca i64, align 8
  store i64 0, ptr %t16.a.45
  %t17.a.49 = alloca i1, align 8
  store i1 0, ptr %t17.a.49
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
  %zx.13 = zext i1 %l.12 to i64
  %rt.14 = call {ptr, i64} @__mn_str_from_bool(i64 %zx.13)
  store {ptr, i64} %rt.14, ptr %str_track.15
  call void @__mn_str_println({ptr, i64} %rt.14)
  store i1 0, ptr %t5.a.16
  %sp.17 = getelementptr inbounds [5 x i8], ptr @.str.0, i64 0, i64 0
  %s.18 = insertvalue {ptr, i64} undef, ptr %sp.17, 0
  %s.19 = insertvalue {ptr, i64} %s.18, i64 5, 1
  store {ptr, i64} %s.19, ptr %t6.a.20
  %l.21 = load {ptr, i64}, ptr %t6.a.20
  store {ptr, i64} zeroinitializer, ptr %str_track.15
  %c.22 = call {ptr, i64} @identity__String({ptr, i64} %l.21)
  store {ptr, i64} %c.22, ptr %t7.a.23
  %l.24 = load {ptr, i64}, ptr %t7.a.23
  call void @__mn_str_println({ptr, i64} %l.24)
  store i1 0, ptr %t8.a.25
  store i64 10, ptr %t9.a.26
  store i64 20, ptr %t10.a.27
  %l.28 = load i64, ptr %t9.a.26
  %l.29 = load i64, ptr %t10.a.27
  %c.30 = call i64 @first__Int_Int(i64 %l.28, i64 %l.29)
  store i64 %c.30, ptr %t11.a.31
  %l.32 = load i64, ptr %t11.a.31
  %fp.33 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.34 = call i32 (ptr, ...) @printf(ptr %fp.33, i64 %l.32)
  store i1 0, ptr %t12.a.35
  store i64 100, ptr %t13.a.36
  store i1 1, ptr %t14.a.37
  %l.38 = load i64, ptr %t13.a.36
  %si.39 = insertvalue {i64, i1} undef, i64 %l.38, 0
  %l.40 = load i1, ptr %t14.a.37
  %si.41 = insertvalue {i64, i1} %si.39, i1 %l.40, 1
  store {i64, i1} %si.41, ptr %t15.a.42
  %fg.43 = getelementptr inbounds {i64, i1}, ptr %t15.a.42, i32 0, i32 0
  %fv.44 = load i64, ptr %fg.43
  store i64 %fv.44, ptr %t16.a.45
  %l.46 = load i64, ptr %t16.a.45
  %fp.47 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.48 = call i32 (ptr, ...) @printf(ptr %fp.47, i64 %l.46)
  store i1 0, ptr %t17.a.49
  %drop.s.50 = load {ptr, i64}, ptr %str_track.15
  %drop.p.51 = extractvalue {ptr, i64} %drop.s.50, 0
  %drop.null.52 = icmp eq ptr %drop.p.51, null
  br i1 %drop.null.52, label %drop.skip.53, label %drop.check.53
drop.check.53:
  call void @__mn_str_free({ptr, i64} %drop.s.50)
  br label %drop.skip.53
drop.skip.53:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.32.0"}
