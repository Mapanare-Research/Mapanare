; ModuleID = 'quicksort'
source_filename = "quicksort"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"checksum = ", align 8

declare ptr @__mn_list_get(ptr, i64)
declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64)
declare void @__mn_list_push(ptr, ptr)
declare {ptr, i64} @__mn_str_from_int(i64)
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64})
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64})
declare void @free(ptr)
declare void @__mn_intern_destroy()

define internal i64 @partition({ptr, i64, i64, i64, i64} %arr, i64 %lo, i64 %hi) {
pre_entry:
  %arr.addr = alloca {ptr, i64, i64, i64, i64}, align 8
  %lo.addr = alloca i64, align 8
  %hi.addr = alloca i64, align 8
  %lp.2 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t0.a.5 = alloca i64, align 8
  store i64 0, ptr %t0.a.5
  %i.a.7 = alloca i64, align 8
  store i64 0, ptr %i.a.7
  %j.a.9 = alloca i64, align 8
  store i64 0, ptr %j.a.9
  %t1.a.13 = alloca i1, align 8
  store i1 0, ptr %t1.a.13
  %lp.17 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t2.a.20 = alloca i64, align 8
  store i64 0, ptr %t2.a.20
  %t3.a.24 = alloca i1, align 8
  store i1 0, ptr %t3.a.24
  %lp.28 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t11.a.31 = alloca i64, align 8
  store i64 0, ptr %t11.a.31
  %lp.34 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t12.a.37 = alloca i64, align 8
  store i64 0, ptr %t12.a.37
  %lp.41 = alloca {ptr, i64, i64, i64, i64}, align 8
  %lp.46 = alloca {ptr, i64, i64, i64, i64}, align 8
  %lp.51 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t4.a.54 = alloca i64, align 8
  store i64 0, ptr %t4.a.54
  %lp.57 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t5.a.60 = alloca i64, align 8
  store i64 0, ptr %t5.a.60
  %lp.64 = alloca {ptr, i64, i64, i64, i64}, align 8
  %lp.69 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t6.a.71 = alloca i64, align 8
  store i64 0, ptr %t6.a.71
  %t7.a.75 = alloca i64, align 8
  store i64 0, ptr %t7.a.75
  %t9.a.77 = alloca i64, align 8
  store i64 0, ptr %t9.a.77
  %t10.a.81 = alloca i64, align 8
  store i64 0, ptr %t10.a.81
  store {ptr, i64, i64, i64, i64} %arr, ptr %arr.addr
  store i64 %lo, ptr %lo.addr
  store i64 %hi, ptr %hi.addr
  br label %entry
entry:
  %l.0 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.1 = load i64, ptr %hi.addr
  store {ptr, i64, i64, i64, i64} %l.0, ptr %lp.2
  %rt.3 = call ptr @__mn_list_get(ptr %lp.2, i64 %l.1)
  %el.4 = load i64, ptr %rt.3
  store i64 %el.4, ptr %t0.a.5
  %l.6 = load i64, ptr %lo.addr
  store i64 %l.6, ptr %i.a.7
  %l.8 = load i64, ptr %lo.addr
  store i64 %l.8, ptr %j.a.9
  br label %while_header0
while_header0:
  %l.10 = load i64, ptr %j.a.9
  %l.11 = load i64, ptr %hi.addr
  %i.12 = icmp slt i64 %l.10, %l.11
  store i1 %i.12, ptr %t1.a.13
  %l.14 = load i1, ptr %t1.a.13
  br i1 %l.14, label %while_body1, label %while_exit2
while_body1:
  %l.15 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.16 = load i64, ptr %j.a.9
  store {ptr, i64, i64, i64, i64} %l.15, ptr %lp.17
  %rt.18 = call ptr @__mn_list_get(ptr %lp.17, i64 %l.16)
  %el.19 = load i64, ptr %rt.18
  store i64 %el.19, ptr %t2.a.20
  %l.21 = load i64, ptr %t2.a.20
  %l.22 = load i64, ptr %t0.a.5
  %i.23 = icmp slt i64 %l.21, %l.22
  store i1 %i.23, ptr %t3.a.24
  %l.25 = load i1, ptr %t3.a.24
  br i1 %l.25, label %if_then3, label %if_else4
while_exit2:
  %l.26 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.27 = load i64, ptr %i.a.7
  store {ptr, i64, i64, i64, i64} %l.26, ptr %lp.28
  %rt.29 = call ptr @__mn_list_get(ptr %lp.28, i64 %l.27)
  %el.30 = load i64, ptr %rt.29
  store i64 %el.30, ptr %t11.a.31
  %l.32 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.33 = load i64, ptr %hi.addr
  store {ptr, i64, i64, i64, i64} %l.32, ptr %lp.34
  %rt.35 = call ptr @__mn_list_get(ptr %lp.34, i64 %l.33)
  %el.36 = load i64, ptr %rt.35
  store i64 %el.36, ptr %t12.a.37
  %l.38 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.39 = load i64, ptr %i.a.7
  %l.40 = load i64, ptr %t12.a.37
  store {ptr, i64, i64, i64, i64} %l.38, ptr %lp.41
  %rt.42 = call ptr @__mn_list_get(ptr %lp.41, i64 %l.39)
  store i64 %l.40, ptr %rt.42
  %l.43 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.44 = load i64, ptr %hi.addr
  %l.45 = load i64, ptr %t11.a.31
  store {ptr, i64, i64, i64, i64} %l.43, ptr %lp.46
  %rt.47 = call ptr @__mn_list_get(ptr %lp.46, i64 %l.44)
  store i64 %l.45, ptr %rt.47
  %l.48 = load i64, ptr %i.a.7
  ret i64 %l.48
if_then3:
  %l.49 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.50 = load i64, ptr %i.a.7
  store {ptr, i64, i64, i64, i64} %l.49, ptr %lp.51
  %rt.52 = call ptr @__mn_list_get(ptr %lp.51, i64 %l.50)
  %el.53 = load i64, ptr %rt.52
  store i64 %el.53, ptr %t4.a.54
  %l.55 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.56 = load i64, ptr %j.a.9
  store {ptr, i64, i64, i64, i64} %l.55, ptr %lp.57
  %rt.58 = call ptr @__mn_list_get(ptr %lp.57, i64 %l.56)
  %el.59 = load i64, ptr %rt.58
  store i64 %el.59, ptr %t5.a.60
  %l.61 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.62 = load i64, ptr %i.a.7
  %l.63 = load i64, ptr %t5.a.60
  store {ptr, i64, i64, i64, i64} %l.61, ptr %lp.64
  %rt.65 = call ptr @__mn_list_get(ptr %lp.64, i64 %l.62)
  store i64 %l.63, ptr %rt.65
  %l.66 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.67 = load i64, ptr %j.a.9
  %l.68 = load i64, ptr %t4.a.54
  store {ptr, i64, i64, i64, i64} %l.66, ptr %lp.69
  %rt.70 = call ptr @__mn_list_get(ptr %lp.69, i64 %l.67)
  store i64 %l.68, ptr %rt.70
  store i64 1, ptr %t6.a.71
  %l.72 = load i64, ptr %i.a.7
  %l.73 = load i64, ptr %t6.a.71
  %i.74 = add i64 %l.72, %l.73
  store i64 %i.74, ptr %t7.a.75
  %l.76 = load i64, ptr %t7.a.75
  store i64 %l.76, ptr %i.a.7
  br label %if_merge5
if_else4:
  br label %if_merge5
if_merge5:
  store i64 1, ptr %t9.a.77
  %l.78 = load i64, ptr %j.a.9
  %l.79 = load i64, ptr %t9.a.77
  %i.80 = add i64 %l.78, %l.79
  store i64 %i.80, ptr %t10.a.81
  %l.82 = load i64, ptr %t10.a.81
  store i64 %l.82, ptr %j.a.9
  br label %while_header0
}

define internal void @qsort({ptr, i64, i64, i64, i64} %arr, i64 %lo, i64 %hi) {
pre_entry:
  %arr.addr = alloca {ptr, i64, i64, i64, i64}, align 8
  %lo.addr = alloca i64, align 8
  %hi.addr = alloca i64, align 8
  %t0.a.3 = alloca i1, align 8
  store i1 0, ptr %t0.a.3
  %t1.a.9 = alloca i64, align 8
  store i64 0, ptr %t1.a.9
  %t2.a.10 = alloca i64, align 8
  store i64 0, ptr %t2.a.10
  %t3.a.14 = alloca i64, align 8
  store i64 0, ptr %t3.a.14
  %t4.a.18 = alloca i1, align 8
  store i1 0, ptr %t4.a.18
  %t5.a.19 = alloca i64, align 8
  store i64 0, ptr %t5.a.19
  %t6.a.23 = alloca i64, align 8
  store i64 0, ptr %t6.a.23
  %t7.a.27 = alloca i1, align 8
  store i1 0, ptr %t7.a.27
  store {ptr, i64, i64, i64, i64} %arr, ptr %arr.addr
  store i64 %lo, ptr %lo.addr
  store i64 %hi, ptr %hi.addr
  br label %entry
entry:
  %l.0 = load i64, ptr %lo.addr
  %l.1 = load i64, ptr %hi.addr
  %i.2 = icmp slt i64 %l.0, %l.1
  store i1 %i.2, ptr %t0.a.3
  %l.4 = load i1, ptr %t0.a.3
  br i1 %l.4, label %if_then0, label %if_else1
if_then0:
  %l.5 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.6 = load i64, ptr %lo.addr
  %l.7 = load i64, ptr %hi.addr
  %c.8 = call i64 @partition({ptr, i64, i64, i64, i64} %l.5, i64 %l.6, i64 %l.7)
  store i64 %c.8, ptr %t1.a.9
  store i64 1, ptr %t2.a.10
  %l.11 = load i64, ptr %t1.a.9
  %l.12 = load i64, ptr %t2.a.10
  %i.13 = sub i64 %l.11, %l.12
  store i64 %i.13, ptr %t3.a.14
  %l.15 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.16 = load i64, ptr %lo.addr
  %l.17 = load i64, ptr %t3.a.14
  call void @qsort({ptr, i64, i64, i64, i64} %l.15, i64 %l.16, i64 %l.17)
  store i1 0, ptr %t4.a.18
  store i64 1, ptr %t5.a.19
  %l.20 = load i64, ptr %t1.a.9
  %l.21 = load i64, ptr %t5.a.19
  %i.22 = add i64 %l.20, %l.21
  store i64 %i.22, ptr %t6.a.23
  %l.24 = load {ptr, i64, i64, i64, i64}, ptr %arr.addr
  %l.25 = load i64, ptr %t6.a.23
  %l.26 = load i64, ptr %hi.addr
  call void @qsort({ptr, i64, i64, i64, i64} %l.24, i64 %l.25, i64 %l.26)
  store i1 0, ptr %t7.a.27
  br label %if_merge2
if_else1:
  br label %if_merge2
if_merge2:
  ret void
}

define i64 @main() {
pre_entry:
  %t0.a.1 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t0.a.1
  %arr.a.3 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %arr.a.3
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  %seed.a.6 = alloca i64, align 8
  store i64 0, ptr %seed.a.6
  %t2.a.7 = alloca i64, align 8
  store i64 0, ptr %t2.a.7
  %i.a.9 = alloca i64, align 8
  store i64 0, ptr %i.a.9
  %t3.a.10 = alloca i64, align 8
  store i64 0, ptr %t3.a.10
  %t4.a.14 = alloca i1, align 8
  store i1 0, ptr %t4.a.14
  %_inl1_t0.a.16 = alloca i64, align 8
  store i64 0, ptr %_inl1_t0.a.16
  %_inl1_t1.a.20 = alloca i64, align 8
  store i64 0, ptr %_inl1_t1.a.20
  %_inl1_t2.a.21 = alloca i64, align 8
  store i64 0, ptr %_inl1_t2.a.21
  %_inl1_t3.a.25 = alloca i64, align 8
  store i64 0, ptr %_inl1_t3.a.25
  %_inl1_t4.a.26 = alloca i64, align 8
  store i64 0, ptr %_inl1_t4.a.26
  %_inl1_t5.a.30 = alloca i64, align 8
  store i64 0, ptr %_inl1_t5.a.30
  %t6.a.32 = alloca i64, align 8
  store i64 0, ptr %t6.a.32
  %t7.a.36 = alloca i64, align 8
  store i64 0, ptr %t7.a.36
  %ea.38 = alloca i64, align 8
  %t8.a.40 = alloca i64, align 8
  store i64 0, ptr %t8.a.40
  %t9.a.44 = alloca i64, align 8
  store i64 0, ptr %t9.a.44
  %t10.a.46 = alloca i64, align 8
  store i64 0, ptr %t10.a.46
  %t11.a.47 = alloca i64, align 8
  store i64 0, ptr %t11.a.47
  %t12.a.51 = alloca i1, align 8
  store i1 0, ptr %t12.a.51
  %t13.a.52 = alloca i64, align 8
  store i64 0, ptr %t13.a.52
  %checksum.a.54 = alloca i64, align 8
  store i64 0, ptr %checksum.a.54
  %t14.a.55 = alloca i64, align 8
  store i64 0, ptr %t14.a.55
  %k.a.57 = alloca i64, align 8
  store i64 0, ptr %k.a.57
  %t15.a.58 = alloca i64, align 8
  store i64 0, ptr %t15.a.58
  %t16.a.62 = alloca i1, align 8
  store i1 0, ptr %t16.a.62
  %lp.66 = alloca {ptr, i64, i64, i64, i64}, align 8
  %t17.a.68 = alloca ptr, align 8
  store ptr null, ptr %t17.a.68
  %t18.a.73 = alloca i64, align 8
  store i64 0, ptr %t18.a.73
  %t19.a.75 = alloca i64, align 8
  store i64 0, ptr %t19.a.75
  %t20.a.79 = alloca i64, align 8
  store i64 0, ptr %t20.a.79
  %t21.a.84 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t21.a.84
  %str_track.87 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.87
  %t22.a.88 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t22.a.88
  %str_track.92 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.92
  %t23.a.93 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t23.a.93
  %t24.a.95 = alloca i1, align 8
  store i1 0, ptr %t24.a.95
  br label %entry
entry:
  %ln.0 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 8)
  store {ptr, i64, i64, i64, i64} %ln.0, ptr %t0.a.1
  %l.2 = load {ptr, i64, i64, i64, i64}, ptr %t0.a.1
  store {ptr, i64, i64, i64, i64} %l.2, ptr %arr.a.3
  store i64 42, ptr %t1.a.4
  %l.5 = load i64, ptr %t1.a.4
  store i64 %l.5, ptr %seed.a.6
  store i64 0, ptr %t2.a.7
  %l.8 = load i64, ptr %t2.a.7
  store i64 %l.8, ptr %i.a.9
  br label %while_header0
while_header0:
  store i64 10000, ptr %t3.a.10
  %l.11 = load i64, ptr %i.a.9
  %l.12 = load i64, ptr %t3.a.10
  %i.13 = icmp slt i64 %l.11, %l.12
  store i1 %i.13, ptr %t4.a.14
  %l.15 = load i1, ptr %t4.a.14
  br i1 %l.15, label %while_body1, label %while_exit2
while_body1:
  br label %_inl1_entry
_inl1_entry:
  store i64 1103515245, ptr %_inl1_t0.a.16
  %l.17 = load i64, ptr %seed.a.6
  %l.18 = load i64, ptr %_inl1_t0.a.16
  %i.19 = mul i64 %l.17, %l.18
  store i64 %i.19, ptr %_inl1_t1.a.20
  store i64 12345, ptr %_inl1_t2.a.21
  %l.22 = load i64, ptr %_inl1_t1.a.20
  %l.23 = load i64, ptr %_inl1_t2.a.21
  %i.24 = add i64 %l.22, %l.23
  store i64 %i.24, ptr %_inl1_t3.a.25
  store i64 2147483648, ptr %_inl1_t4.a.26
  %l.27 = load i64, ptr %_inl1_t3.a.25
  %l.28 = load i64, ptr %_inl1_t4.a.26
  %i.29 = srem i64 %l.27, %l.28
  store i64 %i.29, ptr %_inl1_t5.a.30
  br label %_inl1_ret
_inl1_ret:
  %l.31 = load i64, ptr %_inl1_t5.a.30
  store i64 %l.31, ptr %seed.a.6
  store i64 100000, ptr %t6.a.32
  %l.33 = load i64, ptr %seed.a.6
  %l.34 = load i64, ptr %t6.a.32
  %i.35 = srem i64 %l.33, %l.34
  store i64 %i.35, ptr %t7.a.36
  %l.37 = load i64, ptr %t7.a.36
  store i64 %l.37, ptr %ea.38
  call void @__mn_list_push(ptr %t0.a.1, ptr %ea.38)
  %ul.39 = load {ptr, i64, i64, i64, i64}, ptr %t0.a.1
  store {ptr, i64, i64, i64, i64} %ul.39, ptr %arr.a.3
  store i64 1, ptr %t8.a.40
  %l.41 = load i64, ptr %i.a.9
  %l.42 = load i64, ptr %t8.a.40
  %i.43 = add i64 %l.41, %l.42
  store i64 %i.43, ptr %t9.a.44
  %l.45 = load i64, ptr %t9.a.44
  store i64 %l.45, ptr %i.a.9
  br label %while_header0
while_exit2:
  store i64 0, ptr %t10.a.46
  store i64 9999, ptr %t11.a.47
  %l.48 = load {ptr, i64, i64, i64, i64}, ptr %arr.a.3
  %l.49 = load i64, ptr %t10.a.46
  %l.50 = load i64, ptr %t11.a.47
  call void @qsort({ptr, i64, i64, i64, i64} %l.48, i64 %l.49, i64 %l.50)
  store i1 0, ptr %t12.a.51
  store i64 0, ptr %t13.a.52
  %l.53 = load i64, ptr %t13.a.52
  store i64 %l.53, ptr %checksum.a.54
  store i64 0, ptr %t14.a.55
  %l.56 = load i64, ptr %t14.a.55
  store i64 %l.56, ptr %k.a.57
  br label %while_header3
while_header3:
  store i64 10, ptr %t15.a.58
  %l.59 = load i64, ptr %k.a.57
  %l.60 = load i64, ptr %t15.a.58
  %i.61 = icmp slt i64 %l.59, %l.60
  store i1 %i.61, ptr %t16.a.62
  %l.63 = load i1, ptr %t16.a.62
  br i1 %l.63, label %while_body4, label %while_exit5
while_body4:
  %l.64 = load {ptr, i64, i64, i64, i64}, ptr %arr.a.3
  %l.65 = load i64, ptr %k.a.57
  store {ptr, i64, i64, i64, i64} %l.64, ptr %lp.66
  %rt.67 = call ptr @__mn_list_get(ptr %lp.66, i64 %l.65)
  store ptr %rt.67, ptr %t17.a.68
  %l.69 = load i64, ptr %checksum.a.54
  %l.70 = load ptr, ptr %t17.a.68
  %p2i.71 = ptrtoint ptr %l.70 to i64
  %i.72 = add i64 %l.69, %p2i.71
  store i64 %i.72, ptr %t18.a.73
  %l.74 = load i64, ptr %t18.a.73
  store i64 %l.74, ptr %checksum.a.54
  store i64 1, ptr %t19.a.75
  %l.76 = load i64, ptr %k.a.57
  %l.77 = load i64, ptr %t19.a.75
  %i.78 = add i64 %l.76, %l.77
  store i64 %i.78, ptr %t20.a.79
  %l.80 = load i64, ptr %t20.a.79
  store i64 %l.80, ptr %k.a.57
  br label %while_header3
while_exit5:
  %sp.81 = getelementptr inbounds [11 x i8], ptr @.str.0, i64 0, i64 0
  %s.82 = insertvalue {ptr, i64} undef, ptr %sp.81, 0
  %s.83 = insertvalue {ptr, i64} %s.82, i64 11, 1
  store {ptr, i64} %s.83, ptr %t21.a.84
  %l.85 = load i64, ptr %checksum.a.54
  %rt.86 = call {ptr, i64} @__mn_str_from_int(i64 %l.85)
  store {ptr, i64} %rt.86, ptr %str_track.87
  store {ptr, i64} %rt.86, ptr %t22.a.88
  %l.89 = load {ptr, i64}, ptr %t21.a.84
  %l.90 = load {ptr, i64}, ptr %t22.a.88
  %rt.91 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.89, {ptr, i64} %l.90)
  store {ptr, i64} %rt.91, ptr %str_track.92
  store {ptr, i64} %rt.91, ptr %t23.a.93
  %l.94 = load {ptr, i64}, ptr %t23.a.93
  call void @__mn_str_println({ptr, i64} %l.94)
  store i1 0, ptr %t24.a.95
  %drop.s.96 = load {ptr, i64}, ptr %str_track.87
  %drop.p.97 = extractvalue {ptr, i64} %drop.s.96, 0
  %drop.null.98 = icmp eq ptr %drop.p.97, null
  br i1 %drop.null.98, label %drop.skip.99, label %drop.check.99
drop.check.99:
  call void @__mn_str_free({ptr, i64} %drop.s.96)
  br label %drop.skip.99
drop.skip.99:
  %drop.s.100 = load {ptr, i64}, ptr %str_track.92
  %drop.p.101 = extractvalue {ptr, i64} %drop.s.100, 0
  %drop.null.102 = icmp eq ptr %drop.p.101, null
  br i1 %drop.null.102, label %drop.skip.103, label %drop.check.103
drop.check.103:
  call void @__mn_str_free({ptr, i64} %drop.s.100)
  br label %drop.skip.103
drop.skip.103:
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
