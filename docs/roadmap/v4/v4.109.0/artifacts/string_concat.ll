; ModuleID = 'string_concat'
source_filename = "string_concat"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [0 x i8] c"", align 8
@.str.1 = private constant [5 x i8] c"hello", align 8
@.str.2 = private constant [6 x i8] c"len = ", align 8

declare ptr @__mn_sb_new(i64)
declare void @__mn_sb_append(ptr, {ptr, i64})
declare {ptr, i64} @__mn_sb_finish(ptr)
declare i64 @__mn_str_len({ptr, i64}) nounwind readonly willreturn
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() nounwind willreturn {
pre_entry:
  %t0.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t0.a.3
  %result.a.5 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %result.a.5
  %t1.a.6 = alloca i64, align 8
  store i64 0, ptr %t1.a.6
  %i.a.8 = alloca i64, align 8
  store i64 0, ptr %i.a.8
  %sb_cap_1.a.9 = alloca i64, align 8
  store i64 0, ptr %sb_cap_1.a.9
  %sb_1.a.12 = alloca ptr, align 8
  store ptr null, ptr %sb_1.a.12
  %sb_seed_1.a.15 = alloca i1, align 8
  store i1 0, ptr %sb_seed_1.a.15
  %t2.a.16 = alloca i64, align 8
  store i64 0, ptr %t2.a.16
  %t3.a.20 = alloca i1, align 8
  store i1 0, ptr %t3.a.20
  %t4.a.25 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.25
  %sb_app_1.a.28 = alloca i1, align 8
  store i1 0, ptr %sb_app_1.a.28
  %t6.a.29 = alloca i64, align 8
  store i64 0, ptr %t6.a.29
  %t7.a.33 = alloca i64, align 8
  store i64 0, ptr %t7.a.33
  %str_track.37 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.37
  %t8.a.41 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t8.a.41
  %t9.a.44 = alloca i64, align 8
  store i64 0, ptr %t9.a.44
  %str_track.47 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.47
  %t10.a.48 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.48
  %str_track.52 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.52
  %t11.a.53 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t11.a.53
  %t12.a.55 = alloca i1, align 8
  store i1 0, ptr %t12.a.55
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [0 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 0, 1
  store {ptr, i64} %s.2, ptr %t0.a.3
  %l.4 = load {ptr, i64}, ptr %t0.a.3
  store {ptr, i64} %l.4, ptr %result.a.5
  store i64 0, ptr %t1.a.6
  %l.7 = load i64, ptr %t1.a.6
  store i64 %l.7, ptr %i.a.8
  store i64 64, ptr %sb_cap_1.a.9
  %l.10 = load i64, ptr %sb_cap_1.a.9
  %rt.11 = call ptr @__mn_sb_new(i64 %l.10)
  store ptr %rt.11, ptr %sb_1.a.12
  %l.13 = load ptr, ptr %sb_1.a.12
  %l.14 = load {ptr, i64}, ptr %result.a.5
  call void @__mn_sb_append(ptr %l.13, {ptr, i64} %l.14)
  store i1 0, ptr %sb_seed_1.a.15
  br label %while_header0
while_header0:
  store i64 10000, ptr %t2.a.16
  %l.17 = load i64, ptr %i.a.8
  %l.18 = load i64, ptr %t2.a.16
  %i.19 = icmp slt i64 %l.17, %l.18
  store i1 %i.19, ptr %t3.a.20
  %l.21 = load i1, ptr %t3.a.20
  br i1 %l.21, label %while_body1, label %while_exit2
while_body1:
  %sp.22 = getelementptr inbounds [5 x i8], ptr @.str.1, i64 0, i64 0
  %s.23 = insertvalue {ptr, i64} undef, ptr %sp.22, 0
  %s.24 = insertvalue {ptr, i64} %s.23, i64 5, 1
  store {ptr, i64} %s.24, ptr %t4.a.25
  %l.26 = load ptr, ptr %sb_1.a.12
  %l.27 = load {ptr, i64}, ptr %t4.a.25
  call void @__mn_sb_append(ptr %l.26, {ptr, i64} %l.27)
  store i1 0, ptr %sb_app_1.a.28
  store i64 1, ptr %t6.a.29
  %l.30 = load i64, ptr %i.a.8
  %l.31 = load i64, ptr %t6.a.29
  %i.32 = add nsw i64 %l.30, %l.31
  store i64 %i.32, ptr %t7.a.33
  %l.34 = load i64, ptr %t7.a.33
  store i64 %l.34, ptr %i.a.8
  br label %while_header0
while_exit2:
  %l.35 = load ptr, ptr %sb_1.a.12
  %rt.36 = call {ptr, i64} @__mn_sb_finish(ptr %l.35)
  store {ptr, i64} %rt.36, ptr %str_track.37
  store {ptr, i64} %rt.36, ptr %result.a.5
  %sp.38 = getelementptr inbounds [6 x i8], ptr @.str.2, i64 0, i64 0
  %s.39 = insertvalue {ptr, i64} undef, ptr %sp.38, 0
  %s.40 = insertvalue {ptr, i64} %s.39, i64 6, 1
  store {ptr, i64} %s.40, ptr %t8.a.41
  %l.42 = load {ptr, i64}, ptr %result.a.5
  %rt.43 = call i64 @__mn_str_len({ptr, i64} %l.42)
  store i64 %rt.43, ptr %t9.a.44
  %l.45 = load i64, ptr %t9.a.44
  %rt.46 = call {ptr, i64} @__mn_str_from_int(i64 %l.45)
  store {ptr, i64} %rt.46, ptr %str_track.47
  store {ptr, i64} %rt.46, ptr %t10.a.48
  %l.49 = load {ptr, i64}, ptr %t8.a.41
  %l.50 = load {ptr, i64}, ptr %t10.a.48
  %rt.51 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.49, {ptr, i64} %l.50)
  store {ptr, i64} %rt.51, ptr %str_track.52
  store {ptr, i64} %rt.51, ptr %t11.a.53
  %l.54 = load {ptr, i64}, ptr %t11.a.53
  call void @__mn_str_println({ptr, i64} %l.54)
  store i1 0, ptr %t12.a.55
  %drop.s.56 = load {ptr, i64}, ptr %str_track.37
  %drop.p.57 = extractvalue {ptr, i64} %drop.s.56, 0
  %drop.null.58 = icmp eq ptr %drop.p.57, null
  br i1 %drop.null.58, label %drop.skip.59, label %drop.check.59
drop.check.59:
  call void @__mn_str_free({ptr, i64} %drop.s.56)
  br label %drop.skip.59
drop.skip.59:
  %drop.s.60 = load {ptr, i64}, ptr %str_track.47
  %drop.p.61 = extractvalue {ptr, i64} %drop.s.60, 0
  %drop.null.62 = icmp eq ptr %drop.p.61, null
  br i1 %drop.null.62, label %drop.skip.63, label %drop.check.63
drop.check.63:
  call void @__mn_str_free({ptr, i64} %drop.s.60)
  br label %drop.skip.63
drop.skip.63:
  %drop.s.64 = load {ptr, i64}, ptr %str_track.52
  %drop.p.65 = extractvalue {ptr, i64} %drop.s.64, 0
  %drop.null.66 = icmp eq ptr %drop.p.65, null
  br i1 %drop.null.66, label %drop.skip.67, label %drop.check.67
drop.check.67:
  call void @__mn_str_free({ptr, i64} %drop.s.64)
  br label %drop.skip.67
drop.skip.67:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.109.0"}
!1 = !{!"Mapanare TBAA"}
!2 = !{!"int", !1}
!3 = !{!"float", !1}
!4 = !{!"ptr", !1}
!5 = !{!"bool", !1}
!6 = !{!2, !2, i64 0}
!7 = !{!3, !3, i64 0}
!8 = !{!4, !4, i64 0}
!9 = !{!5, !5, i64 0}
