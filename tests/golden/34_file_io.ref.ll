; ModuleID = '34_file_io'
source_filename = "34_file_io"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [19 x i8] c"/tmp/mn_test_34.txt", align 8
@.str.1 = private constant [11 x i8] c"hello world", align 8
@.str.2 = private constant [19 x i8] c"/tmp/mn_test_34.txt", align 8
@.str.3 = private constant [19 x i8] c"/tmp/mn_test_34.txt", align 8
@.str.4 = private constant [9 x i8] c" appended", align 8
@.str.5 = private constant [19 x i8] c"/tmp/mn_test_34.txt", align 8
@.str.6 = private constant [19 x i8] c"/tmp/mn_test_34.txt", align 8
@.str.7 = private constant [26 x i8] c"/tmp/mn_nonexistent_34.txt", align 8
@.str.8 = private constant [4 x i8] c"/tmp", align 8

declare i64 @__mn_file_write({ptr, i64}, {ptr, i64})
declare {ptr, i64} @__mn_file_read_or_empty({ptr, i64})
declare void @__mn_str_println({ptr, i64})
declare i64 @__mn_file_append({ptr, i64}, {ptr, i64}) nounwind willreturn
declare i64 @__mn_file_exists({ptr, i64}) nounwind readonly willreturn
declare {ptr, i64} @__mn_str_from_bool(i64) nounwind willreturn
declare {ptr, i64, i64, i64, i64} @__mn_dir_list_strings({ptr, i64}) nounwind willreturn
declare i64 @__mn_list_len(ptr) nounwind readonly willreturn
declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t0.a.3
  %t1.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.7
  %t2.a.11 = alloca i1, align 8
  store i1 0, ptr %t2.a.11
  %t3.a.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.15
  %str_track.18 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.18
  %t4.a.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.19
  %t5.a.21 = alloca i1, align 8
  store i1 0, ptr %t5.a.21
  %t6.a.25 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.25
  %t7.a.29 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t7.a.29
  %t8.a.33 = alloca i1, align 8
  store i1 0, ptr %t8.a.33
  %t9.a.37 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t9.a.37
  %str_track.40 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.40
  %t10.a.41 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.41
  %t11.a.43 = alloca i1, align 8
  store i1 0, ptr %t11.a.43
  %t12.a.47 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t12.a.47
  %t13.a.51 = alloca i1, align 8
  store i1 0, ptr %t13.a.51
  %str_track.55 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.55
  %t14.a.56 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t14.a.56
  %t15.a.58 = alloca i1, align 8
  store i1 0, ptr %t15.a.58
  %t16.a.62 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t16.a.62
  %t17.a.66 = alloca i1, align 8
  store i1 0, ptr %t17.a.66
  %str_track.70 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.70
  %t18.a.71 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t18.a.71
  %t19.a.73 = alloca i1, align 8
  store i1 0, ptr %t19.a.73
  %t20.a.77 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t20.a.77
  %t21.a.80 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t21.a.80
  %ll.82 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t22.a.84 = alloca i64, align 8
  store i64 0, ptr %t22.a.84
  %str_track.87 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.87
  %t23.a.88 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t23.a.88
  %t24.a.90 = alloca i1, align 8
  store i1 0, ptr %t24.a.90
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [19 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 19, 1
  store {ptr, i64} %s.2, ptr %t0.a.3
  %sp.4 = getelementptr inbounds [11 x i8], ptr @.str.1, i64 0, i64 0
  %s.5 = insertvalue {ptr, i64} undef, ptr %sp.4, 0
  %s.6 = insertvalue {ptr, i64} %s.5, i64 11, 1
  store {ptr, i64} %s.6, ptr %t1.a.7
  %l.8 = load {ptr, i64}, ptr %t0.a.3
  %l.9 = load {ptr, i64}, ptr %t1.a.7
  %rt.10 = call i64 @__mn_file_write({ptr, i64} %l.8, {ptr, i64} %l.9)
  store i1 0, ptr %t2.a.11
  %sp.12 = getelementptr inbounds [19 x i8], ptr @.str.2, i64 0, i64 0
  %s.13 = insertvalue {ptr, i64} undef, ptr %sp.12, 0
  %s.14 = insertvalue {ptr, i64} %s.13, i64 19, 1
  store {ptr, i64} %s.14, ptr %t3.a.15
  %l.16 = load {ptr, i64}, ptr %t3.a.15
  %rt.17 = call {ptr, i64} @__mn_file_read_or_empty({ptr, i64} %l.16)
  store {ptr, i64} %rt.17, ptr %str_track.18
  store {ptr, i64} %rt.17, ptr %t4.a.19
  %l.20 = load {ptr, i64}, ptr %t4.a.19
  call void @__mn_str_println({ptr, i64} %l.20)
  store i1 0, ptr %t5.a.21
  %sp.22 = getelementptr inbounds [19 x i8], ptr @.str.3, i64 0, i64 0
  %s.23 = insertvalue {ptr, i64} undef, ptr %sp.22, 0
  %s.24 = insertvalue {ptr, i64} %s.23, i64 19, 1
  store {ptr, i64} %s.24, ptr %t6.a.25
  %sp.26 = getelementptr inbounds [9 x i8], ptr @.str.4, i64 0, i64 0
  %s.27 = insertvalue {ptr, i64} undef, ptr %sp.26, 0
  %s.28 = insertvalue {ptr, i64} %s.27, i64 9, 1
  store {ptr, i64} %s.28, ptr %t7.a.29
  %l.30 = load {ptr, i64}, ptr %t6.a.25
  %l.31 = load {ptr, i64}, ptr %t7.a.29
  %rt.32 = call i64 @__mn_file_append({ptr, i64} %l.30, {ptr, i64} %l.31)
  store i1 0, ptr %t8.a.33
  %sp.34 = getelementptr inbounds [19 x i8], ptr @.str.5, i64 0, i64 0
  %s.35 = insertvalue {ptr, i64} undef, ptr %sp.34, 0
  %s.36 = insertvalue {ptr, i64} %s.35, i64 19, 1
  store {ptr, i64} %s.36, ptr %t9.a.37
  %l.38 = load {ptr, i64}, ptr %t9.a.37
  %rt.39 = call {ptr, i64} @__mn_file_read_or_empty({ptr, i64} %l.38)
  store {ptr, i64} %rt.39, ptr %str_track.40
  store {ptr, i64} %rt.39, ptr %t10.a.41
  %l.42 = load {ptr, i64}, ptr %t10.a.41
  call void @__mn_str_println({ptr, i64} %l.42)
  store i1 0, ptr %t11.a.43
  %sp.44 = getelementptr inbounds [19 x i8], ptr @.str.6, i64 0, i64 0
  %s.45 = insertvalue {ptr, i64} undef, ptr %sp.44, 0
  %s.46 = insertvalue {ptr, i64} %s.45, i64 19, 1
  store {ptr, i64} %s.46, ptr %t12.a.47
  %l.48 = load {ptr, i64}, ptr %t12.a.47
  %rt.49 = call i64 @__mn_file_exists({ptr, i64} %l.48)
  %tb.50 = icmp ne i64 %rt.49, 0
  store i1 %tb.50, ptr %t13.a.51
  %l.52 = load i1, ptr %t13.a.51
  %zx.53 = zext i1 %l.52 to i64
  %rt.54 = call {ptr, i64} @__mn_str_from_bool(i64 %zx.53)
  store {ptr, i64} %rt.54, ptr %str_track.55
  store {ptr, i64} %rt.54, ptr %t14.a.56
  %l.57 = load {ptr, i64}, ptr %t14.a.56
  call void @__mn_str_println({ptr, i64} %l.57)
  store i1 0, ptr %t15.a.58
  %sp.59 = getelementptr inbounds [26 x i8], ptr @.str.7, i64 0, i64 0
  %s.60 = insertvalue {ptr, i64} undef, ptr %sp.59, 0
  %s.61 = insertvalue {ptr, i64} %s.60, i64 26, 1
  store {ptr, i64} %s.61, ptr %t16.a.62
  %l.63 = load {ptr, i64}, ptr %t16.a.62
  %rt.64 = call i64 @__mn_file_exists({ptr, i64} %l.63)
  %tb.65 = icmp ne i64 %rt.64, 0
  store i1 %tb.65, ptr %t17.a.66
  %l.67 = load i1, ptr %t17.a.66
  %zx.68 = zext i1 %l.67 to i64
  %rt.69 = call {ptr, i64} @__mn_str_from_bool(i64 %zx.68)
  store {ptr, i64} %rt.69, ptr %str_track.70
  store {ptr, i64} %rt.69, ptr %t18.a.71
  %l.72 = load {ptr, i64}, ptr %t18.a.71
  call void @__mn_str_println({ptr, i64} %l.72)
  store i1 0, ptr %t19.a.73
  %sp.74 = getelementptr inbounds [4 x i8], ptr @.str.8, i64 0, i64 0
  %s.75 = insertvalue {ptr, i64} undef, ptr %sp.74, 0
  %s.76 = insertvalue {ptr, i64} %s.75, i64 4, 1
  store {ptr, i64} %s.76, ptr %t20.a.77
  %l.78 = load {ptr, i64}, ptr %t20.a.77
  %rt.79 = call {ptr, i64, i64, i64, i64} @__mn_dir_list_strings({ptr, i64} %l.78)
  store {ptr, i64, i64, i64, i64} %rt.79, ptr %t21.a.80
  %l.81 = load {ptr, i64, i64, i64, i64}, ptr %t21.a.80
  store {ptr, i64, i64, i64, i64} %l.81, ptr %ll.82
  %rt.83 = call i64 @__mn_list_len(ptr %ll.82)
  store i64 %rt.83, ptr %t22.a.84
  %l.85 = load i64, ptr %t22.a.84
  %rt.86 = call {ptr, i64} @__mn_str_from_int(i64 %l.85)
  store {ptr, i64} %rt.86, ptr %str_track.87
  store {ptr, i64} %rt.86, ptr %t23.a.88
  %l.89 = load {ptr, i64}, ptr %t23.a.88
  call void @__mn_str_println({ptr, i64} %l.89)
  store i1 0, ptr %t24.a.90
  %drop.s.91 = load {ptr, i64}, ptr %str_track.18
  %drop.p.92 = extractvalue {ptr, i64} %drop.s.91, 0
  %drop.null.93 = icmp eq ptr %drop.p.92, null
  br i1 %drop.null.93, label %drop.skip.94, label %drop.check.94
drop.check.94:
  call void @__mn_str_free({ptr, i64} %drop.s.91)
  br label %drop.skip.94
drop.skip.94:
  %drop.s.95 = load {ptr, i64}, ptr %str_track.40
  %drop.p.96 = extractvalue {ptr, i64} %drop.s.95, 0
  %drop.null.97 = icmp eq ptr %drop.p.96, null
  br i1 %drop.null.97, label %drop.skip.98, label %drop.check.98
drop.check.98:
  call void @__mn_str_free({ptr, i64} %drop.s.95)
  br label %drop.skip.98
drop.skip.98:
  %drop.s.99 = load {ptr, i64}, ptr %str_track.55
  %drop.p.100 = extractvalue {ptr, i64} %drop.s.99, 0
  %drop.null.101 = icmp eq ptr %drop.p.100, null
  br i1 %drop.null.101, label %drop.skip.102, label %drop.check.102
drop.check.102:
  call void @__mn_str_free({ptr, i64} %drop.s.99)
  br label %drop.skip.102
drop.skip.102:
  %drop.s.103 = load {ptr, i64}, ptr %str_track.70
  %drop.p.104 = extractvalue {ptr, i64} %drop.s.103, 0
  %drop.null.105 = icmp eq ptr %drop.p.104, null
  br i1 %drop.null.105, label %drop.skip.106, label %drop.check.106
drop.check.106:
  call void @__mn_str_free({ptr, i64} %drop.s.103)
  br label %drop.skip.106
drop.skip.106:
  %drop.s.107 = load {ptr, i64}, ptr %str_track.87
  %drop.p.108 = extractvalue {ptr, i64} %drop.s.107, 0
  %drop.null.109 = icmp eq ptr %drop.p.108, null
  br i1 %drop.null.109, label %drop.skip.110, label %drop.check.110
drop.check.110:
  call void @__mn_str_free({ptr, i64} %drop.s.107)
  br label %drop.skip.110
drop.skip.110:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.32.0"}
