; ModuleID = '63_else_sino'
source_filename = "63_else_sino"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [8 x i8] c"positive", align 8
@.str.1 = private constant [8 x i8] c"negative", align 8
@.str.2 = private constant [4 x i8] c"zero", align 8

declare void @__mn_str_println({ptr, i64})
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal {ptr, i64} @classify(i64 %x) nounwind willreturn {
pre_entry:
  %x.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i1, align 8
  store i1 0, ptr %t1.a.4
  %t2.a.9 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.9
  %t3.a.11 = alloca i64, align 8
  store i64 0, ptr %t3.a.11
  %t4.a.15 = alloca i1, align 8
  store i1 0, ptr %t4.a.15
  %t5.a.20 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.20
  %t6.a.25 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.25
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %x.addr
  %l.2 = load i64, ptr %t0.a.0
  %i.3 = icmp sgt i64 %l.1, %l.2
  store i1 %i.3, ptr %t1.a.4
  %l.5 = load i1, ptr %t1.a.4
  br i1 %l.5, label %if_then0, label %if_else1
if_then0:
  %sp.6 = getelementptr inbounds [8 x i8], ptr @.str.0, i64 0, i64 0
  %s.7 = insertvalue {ptr, i64} undef, ptr %sp.6, 0
  %s.8 = insertvalue {ptr, i64} %s.7, i64 8, 1
  store {ptr, i64} %s.8, ptr %t2.a.9
  %l.10 = load {ptr, i64}, ptr %t2.a.9
  ret {ptr, i64} %l.10
if_else1:
  store i64 0, ptr %t3.a.11
  %l.12 = load i64, ptr %x.addr
  %l.13 = load i64, ptr %t3.a.11
  %i.14 = icmp slt i64 %l.12, %l.13
  store i1 %i.14, ptr %t4.a.15
  %l.16 = load i1, ptr %t4.a.15
  br i1 %l.16, label %if_then3, label %if_else4
if_then3:
  %sp.17 = getelementptr inbounds [8 x i8], ptr @.str.1, i64 0, i64 0
  %s.18 = insertvalue {ptr, i64} undef, ptr %sp.17, 0
  %s.19 = insertvalue {ptr, i64} %s.18, i64 8, 1
  store {ptr, i64} %s.19, ptr %t5.a.20
  %l.21 = load {ptr, i64}, ptr %t5.a.20
  ret {ptr, i64} %l.21
if_else4:
  %sp.22 = getelementptr inbounds [4 x i8], ptr @.str.2, i64 0, i64 0
  %s.23 = insertvalue {ptr, i64} undef, ptr %sp.22, 0
  %s.24 = insertvalue {ptr, i64} %s.23, i64 4, 1
  store {ptr, i64} %s.24, ptr %t6.a.25
  %l.26 = load {ptr, i64}, ptr %t6.a.25
  ret {ptr, i64} %l.26
}

define internal i64 @sign(i64 %x) nounwind willreturn {
pre_entry:
  %x.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i1, align 8
  store i1 0, ptr %t1.a.4
  %t2.a.6 = alloca i64, align 8
  store i64 0, ptr %t2.a.6
  %t3.a.8 = alloca i64, align 8
  store i64 0, ptr %t3.a.8
  %t4.a.12 = alloca i1, align 8
  store i1 0, ptr %t4.a.12
  %t7.a.14 = alloca i64, align 8
  store i64 0, ptr %t7.a.14
  %t8.a.16 = alloca i64, align 8
  store i64 0, ptr %t8.a.16
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %x.addr
  %l.2 = load i64, ptr %t0.a.0
  %i.3 = icmp sgt i64 %l.1, %l.2
  store i1 %i.3, ptr %t1.a.4
  %l.5 = load i1, ptr %t1.a.4
  br i1 %l.5, label %if_then0, label %if_else1
if_then0:
  store i64 1, ptr %t2.a.6
  %l.7 = load i64, ptr %t2.a.6
  ret i64 %l.7
if_else1:
  store i64 0, ptr %t3.a.8
  %l.9 = load i64, ptr %x.addr
  %l.10 = load i64, ptr %t3.a.8
  %i.11 = icmp slt i64 %l.9, %l.10
  store i1 %i.11, ptr %t4.a.12
  %l.13 = load i1, ptr %t4.a.12
  br i1 %l.13, label %if_then3, label %if_else4
if_then3:
  store i64 -1, ptr %t7.a.14
  %l.15 = load i64, ptr %t7.a.14
  ret i64 %l.15
if_else4:
  store i64 0, ptr %t8.a.16
  %l.17 = load i64, ptr %t8.a.16
  ret i64 %l.17
}

define i64 @main() nounwind willreturn {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.3
  %t2.a.5 = alloca i1, align 8
  store i1 0, ptr %t2.a.5
  %t5.a.6 = alloca i64, align 8
  store i64 0, ptr %t5.a.6
  %t6.a.9 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.9
  %t7.a.11 = alloca i1, align 8
  store i1 0, ptr %t7.a.11
  %t8.a.12 = alloca i64, align 8
  store i64 0, ptr %t8.a.12
  %t9.a.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t9.a.15
  %t10.a.17 = alloca i1, align 8
  store i1 0, ptr %t10.a.17
  %t11.a.18 = alloca i64, align 8
  store i64 0, ptr %t11.a.18
  %t12.a.21 = alloca i64, align 8
  store i64 0, ptr %t12.a.21
  %str_track.24 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.24
  %t13.a.25 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t13.a.25
  %t14.a.27 = alloca i1, align 8
  store i1 0, ptr %t14.a.27
  %t17.a.28 = alloca i64, align 8
  store i64 0, ptr %t17.a.28
  %t18.a.31 = alloca i64, align 8
  store i64 0, ptr %t18.a.31
  %str_track.34 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.34
  %t19.a.35 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t19.a.35
  %t20.a.37 = alloca i1, align 8
  store i1 0, ptr %t20.a.37
  %t21.a.38 = alloca i64, align 8
  store i64 0, ptr %t21.a.38
  %t22.a.41 = alloca i64, align 8
  store i64 0, ptr %t22.a.41
  %str_track.44 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.44
  %t23.a.45 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t23.a.45
  %t24.a.47 = alloca i1, align 8
  store i1 0, ptr %t24.a.47
  br label %entry
entry:
  store i64 42, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %c.2 = call {ptr, i64} @classify(i64 %l.1)
  store {ptr, i64} %c.2, ptr %t1.a.3
  %l.4 = load {ptr, i64}, ptr %t1.a.3
  call void @__mn_str_println({ptr, i64} %l.4)
  store i1 0, ptr %t2.a.5
  store i64 -7, ptr %t5.a.6
  %l.7 = load i64, ptr %t5.a.6
  %c.8 = call {ptr, i64} @classify(i64 %l.7)
  store {ptr, i64} %c.8, ptr %t6.a.9
  %l.10 = load {ptr, i64}, ptr %t6.a.9
  call void @__mn_str_println({ptr, i64} %l.10)
  store i1 0, ptr %t7.a.11
  store i64 0, ptr %t8.a.12
  %l.13 = load i64, ptr %t8.a.12
  %c.14 = call {ptr, i64} @classify(i64 %l.13)
  store {ptr, i64} %c.14, ptr %t9.a.15
  %l.16 = load {ptr, i64}, ptr %t9.a.15
  call void @__mn_str_println({ptr, i64} %l.16)
  store i1 0, ptr %t10.a.17
  store i64 5, ptr %t11.a.18
  %l.19 = load i64, ptr %t11.a.18
  %c.20 = call i64 @sign(i64 %l.19)
  store i64 %c.20, ptr %t12.a.21
  %l.22 = load i64, ptr %t12.a.21
  %rt.23 = call {ptr, i64} @__mn_str_from_int(i64 %l.22)
  store {ptr, i64} %rt.23, ptr %str_track.24
  store {ptr, i64} %rt.23, ptr %t13.a.25
  %l.26 = load {ptr, i64}, ptr %t13.a.25
  call void @__mn_str_println({ptr, i64} %l.26)
  store i1 0, ptr %t14.a.27
  store i64 -5, ptr %t17.a.28
  %l.29 = load i64, ptr %t17.a.28
  %c.30 = call i64 @sign(i64 %l.29)
  store i64 %c.30, ptr %t18.a.31
  %l.32 = load i64, ptr %t18.a.31
  %rt.33 = call {ptr, i64} @__mn_str_from_int(i64 %l.32)
  store {ptr, i64} %rt.33, ptr %str_track.34
  store {ptr, i64} %rt.33, ptr %t19.a.35
  %l.36 = load {ptr, i64}, ptr %t19.a.35
  call void @__mn_str_println({ptr, i64} %l.36)
  store i1 0, ptr %t20.a.37
  store i64 0, ptr %t21.a.38
  %l.39 = load i64, ptr %t21.a.38
  %c.40 = call i64 @sign(i64 %l.39)
  store i64 %c.40, ptr %t22.a.41
  %l.42 = load i64, ptr %t22.a.41
  %rt.43 = call {ptr, i64} @__mn_str_from_int(i64 %l.42)
  store {ptr, i64} %rt.43, ptr %str_track.44
  store {ptr, i64} %rt.43, ptr %t23.a.45
  %l.46 = load {ptr, i64}, ptr %t23.a.45
  call void @__mn_str_println({ptr, i64} %l.46)
  store i1 0, ptr %t24.a.47
  %drop.s.48 = load {ptr, i64}, ptr %str_track.24
  %drop.p.49 = extractvalue {ptr, i64} %drop.s.48, 0
  %drop.null.50 = icmp eq ptr %drop.p.49, null
  br i1 %drop.null.50, label %drop.skip.51, label %drop.check.51
drop.check.51:
  call void @__mn_str_free({ptr, i64} %drop.s.48)
  br label %drop.skip.51
drop.skip.51:
  %drop.s.52 = load {ptr, i64}, ptr %str_track.34
  %drop.p.53 = extractvalue {ptr, i64} %drop.s.52, 0
  %drop.null.54 = icmp eq ptr %drop.p.53, null
  br i1 %drop.null.54, label %drop.skip.55, label %drop.check.55
drop.check.55:
  call void @__mn_str_free({ptr, i64} %drop.s.52)
  br label %drop.skip.55
drop.skip.55:
  %drop.s.56 = load {ptr, i64}, ptr %str_track.44
  %drop.p.57 = extractvalue {ptr, i64} %drop.s.56, 0
  %drop.null.58 = icmp eq ptr %drop.p.57, null
  br i1 %drop.null.58, label %drop.skip.59, label %drop.check.59
drop.check.59:
  call void @__mn_str_free({ptr, i64} %drop.s.56)
  br label %drop.skip.59
drop.skip.59:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.103.0"}
!1 = !{!"Mapanare TBAA"}
!2 = !{!"int", !1}
!3 = !{!"float", !1}
!4 = !{!"ptr", !1}
!5 = !{!"bool", !1}
!6 = !{!2, !2, i64 0}
!7 = !{!3, !3, i64 0}
!8 = !{!4, !4, i64 0}
!9 = !{!5, !5, i64 0}
