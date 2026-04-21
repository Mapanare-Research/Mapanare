; ModuleID = '65_list_int_indexing'
source_filename = "65_list_int_indexing"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind willreturn
declare void @__mn_list_push(ptr, ptr) nounwind
declare ptr @__mn_list_get(ptr, i64) nounwind
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_list_free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() nounwind willreturn {
pre_entry:
  %t0.a.1 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t0.a.1
  %arr.a.3 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %arr.a.3
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  %ea.6 = alloca i64, align 8
  %t2.a.8 = alloca i64, align 8
  store i64 0, ptr %t2.a.8
  %ea.10 = alloca i64, align 8
  %t3.a.12 = alloca i64, align 8
  store i64 0, ptr %t3.a.12
  %ea.14 = alloca i64, align 8
  %t4.a.16 = alloca i64, align 8
  store i64 0, ptr %t4.a.16
  %lp.19 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t5.a.22 = alloca i64, align 8
  store i64 0, ptr %t5.a.22
  %str_track.25 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.25
  %t6.a.26 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.26
  %t7.a.28 = alloca i1, align 8
  store i1 0, ptr %t7.a.28
  %t8.a.29 = alloca i64, align 8
  store i64 0, ptr %t8.a.29
  %lp.32 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t9.a.35 = alloca i64, align 8
  store i64 0, ptr %t9.a.35
  %str_track.38 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.38
  %t10.a.39 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.39
  %t11.a.41 = alloca i1, align 8
  store i1 0, ptr %t11.a.41
  %t12.a.42 = alloca i64, align 8
  store i64 0, ptr %t12.a.42
  %lp.45 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t13.a.48 = alloca i64, align 8
  store i64 0, ptr %t13.a.48
  %str_track.51 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.51
  %t14.a.52 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t14.a.52
  %t15.a.54 = alloca i1, align 8
  store i1 0, ptr %t15.a.54
  %t16.a.55 = alloca i64, align 8
  store i64 0, ptr %t16.a.55
  %ea.57 = alloca i64, align 8
  %t17.a.59 = alloca i64, align 8
  store i64 0, ptr %t17.a.59
  %lp.62 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t18.a.65 = alloca i64, align 8
  store i64 0, ptr %t18.a.65
  %str_track.68 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.68
  %t19.a.69 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t19.a.69
  %t20.a.71 = alloca i1, align 8
  store i1 0, ptr %t20.a.71
  %t21.a.72 = alloca i64, align 8
  store i64 0, ptr %t21.a.72
  %lp.75 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t22.a.78 = alloca i64, align 8
  store i64 0, ptr %t22.a.78
  %t23.a.79 = alloca i64, align 8
  store i64 0, ptr %t23.a.79
  %lp.82 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t24.a.85 = alloca i64, align 8
  store i64 0, ptr %t24.a.85
  %t25.a.89 = alloca i64, align 8
  store i64 0, ptr %t25.a.89
  %str_track.92 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.92
  %t26.a.93 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t26.a.93
  %t27.a.95 = alloca i1, align 8
  store i1 0, ptr %t27.a.95
  br label %entry
entry:
  %ln.0 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.0, ptr %t0.a.1
  %l.2 = load {ptr, i64, i64, i64, i64}, ptr %t0.a.1
  store {ptr, i64, i64, i64, i64} %l.2, ptr %arr.a.3
  store i64 42, ptr %t1.a.4
  %l.5 = load i64, ptr %t1.a.4
  store i64 %l.5, ptr %ea.6
  call void @__mn_list_push(ptr %t0.a.1, ptr %ea.6)
  %ul.7 = load {ptr, i64, i64, i64, i64}, ptr %t0.a.1
  store {ptr, i64, i64, i64, i64} %ul.7, ptr %arr.a.3
  store i64 99, ptr %t2.a.8
  %l.9 = load i64, ptr %t2.a.8
  store i64 %l.9, ptr %ea.10
  call void @__mn_list_push(ptr %t0.a.1, ptr %ea.10)
  %ul.11 = load {ptr, i64, i64, i64, i64}, ptr %t0.a.1
  store {ptr, i64, i64, i64, i64} %ul.11, ptr %arr.a.3
  store i64 7, ptr %t3.a.12
  %l.13 = load i64, ptr %t3.a.12
  store i64 %l.13, ptr %ea.14
  call void @__mn_list_push(ptr %t0.a.1, ptr %ea.14)
  %ul.15 = load {ptr, i64, i64, i64, i64}, ptr %t0.a.1
  store {ptr, i64, i64, i64, i64} %ul.15, ptr %arr.a.3
  store i64 0, ptr %t4.a.16
  %l.17 = load {ptr, i64, i64, i64, i64}, ptr %arr.a.3
  %l.18 = load i64, ptr %t4.a.16
  store {ptr, i64, i64, i64, i64} %l.17, ptr %lp.19
  %rt.20 = call ptr @__mn_list_get(ptr %lp.19, i64 %l.18)
  %el.21 = load i64, ptr %rt.20
  store i64 %el.21, ptr %t5.a.22
  %l.23 = load i64, ptr %t5.a.22
  %rt.24 = call {ptr, i64} @__mn_str_from_int(i64 %l.23)
  store {ptr, i64} %rt.24, ptr %str_track.25
  store {ptr, i64} %rt.24, ptr %t6.a.26
  %l.27 = load {ptr, i64}, ptr %t6.a.26
  call void @__mn_str_println({ptr, i64} %l.27)
  store i1 0, ptr %t7.a.28
  store i64 0, ptr %t8.a.29
  %l.30 = load {ptr, i64, i64, i64, i64}, ptr %arr.a.3
  %l.31 = load i64, ptr %t8.a.29
  store {ptr, i64, i64, i64, i64} %l.30, ptr %lp.32
  %rt.33 = call ptr @__mn_list_get(ptr %lp.32, i64 %l.31)
  %el.34 = load i64, ptr %rt.33
  store i64 %el.34, ptr %t9.a.35
  %l.36 = load i64, ptr %t9.a.35
  %rt.37 = call {ptr, i64} @__mn_str_from_int(i64 %l.36)
  store {ptr, i64} %rt.37, ptr %str_track.38
  store {ptr, i64} %rt.37, ptr %t10.a.39
  %l.40 = load {ptr, i64}, ptr %t10.a.39
  call void @__mn_str_println({ptr, i64} %l.40)
  store i1 0, ptr %t11.a.41
  store i64 1, ptr %t12.a.42
  %l.43 = load {ptr, i64, i64, i64, i64}, ptr %arr.a.3
  %l.44 = load i64, ptr %t12.a.42
  store {ptr, i64, i64, i64, i64} %l.43, ptr %lp.45
  %rt.46 = call ptr @__mn_list_get(ptr %lp.45, i64 %l.44)
  %el.47 = load i64, ptr %rt.46
  store i64 %el.47, ptr %t13.a.48
  %l.49 = load i64, ptr %t13.a.48
  %rt.50 = call {ptr, i64} @__mn_str_from_int(i64 %l.49)
  store {ptr, i64} %rt.50, ptr %str_track.51
  store {ptr, i64} %rt.50, ptr %t14.a.52
  %l.53 = load {ptr, i64}, ptr %t14.a.52
  call void @__mn_str_println({ptr, i64} %l.53)
  store i1 0, ptr %t15.a.54
  store i64 100, ptr %t16.a.55
  %l.56 = load i64, ptr %t16.a.55
  store i64 %l.56, ptr %ea.57
  call void @__mn_list_push(ptr %t0.a.1, ptr %ea.57)
  %ul.58 = load {ptr, i64, i64, i64, i64}, ptr %t0.a.1
  store {ptr, i64, i64, i64, i64} %ul.58, ptr %arr.a.3
  store i64 3, ptr %t17.a.59
  %l.60 = load {ptr, i64, i64, i64, i64}, ptr %arr.a.3
  %l.61 = load i64, ptr %t17.a.59
  store {ptr, i64, i64, i64, i64} %l.60, ptr %lp.62
  %rt.63 = call ptr @__mn_list_get(ptr %lp.62, i64 %l.61)
  %el.64 = load i64, ptr %rt.63
  store i64 %el.64, ptr %t18.a.65
  %l.66 = load i64, ptr %t18.a.65
  %rt.67 = call {ptr, i64} @__mn_str_from_int(i64 %l.66)
  store {ptr, i64} %rt.67, ptr %str_track.68
  store {ptr, i64} %rt.67, ptr %t19.a.69
  %l.70 = load {ptr, i64}, ptr %t19.a.69
  call void @__mn_str_println({ptr, i64} %l.70)
  store i1 0, ptr %t20.a.71
  store i64 0, ptr %t21.a.72
  %l.73 = load {ptr, i64, i64, i64, i64}, ptr %arr.a.3
  %l.74 = load i64, ptr %t21.a.72
  store {ptr, i64, i64, i64, i64} %l.73, ptr %lp.75
  %rt.76 = call ptr @__mn_list_get(ptr %lp.75, i64 %l.74)
  %el.77 = load i64, ptr %rt.76
  store i64 %el.77, ptr %t22.a.78
  store i64 1, ptr %t23.a.79
  %l.80 = load {ptr, i64, i64, i64, i64}, ptr %arr.a.3
  %l.81 = load i64, ptr %t23.a.79
  store {ptr, i64, i64, i64, i64} %l.80, ptr %lp.82
  %rt.83 = call ptr @__mn_list_get(ptr %lp.82, i64 %l.81)
  %el.84 = load i64, ptr %rt.83
  store i64 %el.84, ptr %t24.a.85
  %l.86 = load i64, ptr %t22.a.78
  %l.87 = load i64, ptr %t24.a.85
  %i.88 = add nsw i64 %l.86, %l.87
  store i64 %i.88, ptr %t25.a.89
  %l.90 = load i64, ptr %t25.a.89
  %rt.91 = call {ptr, i64} @__mn_str_from_int(i64 %l.90)
  store {ptr, i64} %rt.91, ptr %str_track.92
  store {ptr, i64} %rt.91, ptr %t26.a.93
  %l.94 = load {ptr, i64}, ptr %t26.a.93
  call void @__mn_str_println({ptr, i64} %l.94)
  store i1 0, ptr %t27.a.95
  %drop.s.96 = load {ptr, i64}, ptr %str_track.25
  %drop.p.97 = extractvalue {ptr, i64} %drop.s.96, 0
  %drop.null.98 = icmp eq ptr %drop.p.97, null
  br i1 %drop.null.98, label %drop.skip.99, label %drop.check.99
drop.check.99:
  call void @__mn_str_free({ptr, i64} %drop.s.96)
  br label %drop.skip.99
drop.skip.99:
  %drop.s.100 = load {ptr, i64}, ptr %str_track.38
  %drop.p.101 = extractvalue {ptr, i64} %drop.s.100, 0
  %drop.null.102 = icmp eq ptr %drop.p.101, null
  br i1 %drop.null.102, label %drop.skip.103, label %drop.check.103
drop.check.103:
  call void @__mn_str_free({ptr, i64} %drop.s.100)
  br label %drop.skip.103
drop.skip.103:
  %drop.s.104 = load {ptr, i64}, ptr %str_track.51
  %drop.p.105 = extractvalue {ptr, i64} %drop.s.104, 0
  %drop.null.106 = icmp eq ptr %drop.p.105, null
  br i1 %drop.null.106, label %drop.skip.107, label %drop.check.107
drop.check.107:
  call void @__mn_str_free({ptr, i64} %drop.s.104)
  br label %drop.skip.107
drop.skip.107:
  %drop.s.108 = load {ptr, i64}, ptr %str_track.68
  %drop.p.109 = extractvalue {ptr, i64} %drop.s.108, 0
  %drop.null.110 = icmp eq ptr %drop.p.109, null
  br i1 %drop.null.110, label %drop.skip.111, label %drop.check.111
drop.check.111:
  call void @__mn_str_free({ptr, i64} %drop.s.108)
  br label %drop.skip.111
drop.skip.111:
  %drop.s.112 = load {ptr, i64}, ptr %str_track.92
  %drop.p.113 = extractvalue {ptr, i64} %drop.s.112, 0
  %drop.null.114 = icmp eq ptr %drop.p.113, null
  br i1 %drop.null.114, label %drop.skip.115, label %drop.check.115
drop.check.115:
  call void @__mn_str_free({ptr, i64} %drop.s.112)
  br label %drop.skip.115
drop.skip.115:
  %drop.lv.116 = load {ptr, i64, i64, i64, i64}, ptr %arr.a.3
  %drop.lp.117 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.116, 0
  %drop.lnull.118 = icmp eq ptr %drop.lp.117, null
  br i1 %drop.lnull.118, label %drop.lskip.119, label %drop.lcheck.119
drop.lcheck.119:
  call void @__mn_list_free(ptr %arr.a.3)
  br label %drop.lskip.119
drop.lskip.119:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.122.0"}
!1 = !{!"Mapanare TBAA"}
!2 = !{!"int", !1}
!3 = !{!"float", !1}
!4 = !{!"ptr", !1}
!5 = !{!"bool", !1}
!6 = !{!2, !2, i64 0}
!7 = !{!3, !3, i64 0}
!8 = !{!4, !4, i64 0}
!9 = !{!5, !5, i64 0}
