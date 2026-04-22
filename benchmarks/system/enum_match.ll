; ModuleID = 'enum_match'
source_filename = "enum_match"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"checksum = ", align 8

declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal noundef i64 @area({i64, i64, i64} %s) nounwind willreturn {
pre_entry:
  %s.addr = alloca {i64, i64, i64}, align 8
  %tag0.a.2 = alloca i64, align 8
  store i64 0, ptr %tag0.a.2
  %match_result17.a.4 = alloca i64, align 8
  store i64 0, ptr %match_result17.a.4
  %r1.a.8 = alloca i64, align 8
  store i64 0, ptr %r1.a.8
  %t2.a.12 = alloca i64, align 8
  store i64 0, ptr %t2.a.12
  %t3.a.13 = alloca i64, align 8
  store i64 0, ptr %t3.a.13
  %t4.a.17 = alloca i64, align 8
  store i64 0, ptr %t4.a.17
  %side5.a.21 = alloca i64, align 8
  store i64 0, ptr %side5.a.21
  %t6.a.25 = alloca i64, align 8
  store i64 0, ptr %t6.a.25
  %base7.a.29 = alloca i64, align 8
  store i64 0, ptr %base7.a.29
  %height8.a.32 = alloca i64, align 8
  store i64 0, ptr %height8.a.32
  %t9.a.36 = alloca i64, align 8
  store i64 0, ptr %t9.a.36
  %t10.a.37 = alloca i64, align 8
  store i64 0, ptr %t10.a.37
  %t11.a.41 = alloca i64, align 8
  store i64 0, ptr %t11.a.41
  %t12.a.43 = alloca i64, align 8
  store i64 0, ptr %t12.a.43
  %len13.a.47 = alloca i64, align 8
  store i64 0, ptr %len13.a.47
  %w14.a.51 = alloca i64, align 8
  store i64 0, ptr %w14.a.51
  %h15.a.54 = alloca i64, align 8
  store i64 0, ptr %h15.a.54
  %t16.a.58 = alloca i64, align 8
  store i64 0, ptr %t16.a.58
  store {i64, i64, i64} %s, ptr %s.addr
  br label %entry
entry:
  %l.0 = load {i64, i64, i64}, ptr %s.addr
  %et.1 = extractvalue {i64, i64, i64} %l.0, 0
  store i64 %et.1, ptr %tag0.a.2
  %l.3 = load i64, ptr %tag0.a.2
  switch i64 %l.3, label %match_merge0 [
    i64 0, label %match_arm1
    i64 1, label %match_arm2
    i64 2, label %match_arm3
    i64 3, label %match_arm4
    i64 4, label %match_arm5
    i64 5, label %match_arm6
  ]
match_merge0:
  store i64 0, ptr %match_result17.a.4
  %l.5 = load i64, ptr %match_result17.a.4
  ret i64 %l.5
match_arm1:
  %l.6 = load {i64, i64, i64}, ptr %s.addr
  %pr.7 = extractvalue {i64, i64, i64} %l.6, 1
  store i64 %pr.7, ptr %r1.a.8
  %l.9 = load i64, ptr %r1.a.8
  %l.10 = load i64, ptr %r1.a.8
  %i.11 = mul nsw i64 %l.9, %l.10
  store i64 %i.11, ptr %t2.a.12
  store i64 3, ptr %t3.a.13
  %l.14 = load i64, ptr %t2.a.12
  %l.15 = load i64, ptr %t3.a.13
  %i.16 = mul nsw i64 %l.14, %l.15
  store i64 %i.16, ptr %t4.a.17
  %l.18 = load i64, ptr %t4.a.17
  ret i64 %l.18
match_arm2:
  %l.19 = load {i64, i64, i64}, ptr %s.addr
  %pr.20 = extractvalue {i64, i64, i64} %l.19, 1
  store i64 %pr.20, ptr %side5.a.21
  %l.22 = load i64, ptr %side5.a.21
  %l.23 = load i64, ptr %side5.a.21
  %i.24 = mul nsw i64 %l.22, %l.23
  store i64 %i.24, ptr %t6.a.25
  %l.26 = load i64, ptr %t6.a.25
  ret i64 %l.26
match_arm3:
  %l.27 = load {i64, i64, i64}, ptr %s.addr
  %pr.28 = extractvalue {i64, i64, i64} %l.27, 1
  store i64 %pr.28, ptr %base7.a.29
  %l.30 = load {i64, i64, i64}, ptr %s.addr
  %pr.31 = extractvalue {i64, i64, i64} %l.30, 2
  store i64 %pr.31, ptr %height8.a.32
  %l.33 = load i64, ptr %base7.a.29
  %l.34 = load i64, ptr %height8.a.32
  %i.35 = mul nsw i64 %l.33, %l.34
  store i64 %i.35, ptr %t9.a.36
  store i64 2, ptr %t10.a.37
  %l.38 = load i64, ptr %t9.a.36
  %l.39 = load i64, ptr %t10.a.37
  %i.40 = sdiv i64 %l.38, %l.39
  store i64 %i.40, ptr %t11.a.41
  %l.42 = load i64, ptr %t11.a.41
  ret i64 %l.42
match_arm4:
  store i64 0, ptr %t12.a.43
  %l.44 = load i64, ptr %t12.a.43
  ret i64 %l.44
match_arm5:
  %l.45 = load {i64, i64, i64}, ptr %s.addr
  %pr.46 = extractvalue {i64, i64, i64} %l.45, 1
  store i64 %pr.46, ptr %len13.a.47
  %l.48 = load i64, ptr %len13.a.47
  ret i64 %l.48
match_arm6:
  %l.49 = load {i64, i64, i64}, ptr %s.addr
  %pr.50 = extractvalue {i64, i64, i64} %l.49, 1
  store i64 %pr.50, ptr %w14.a.51
  %l.52 = load {i64, i64, i64}, ptr %s.addr
  %pr.53 = extractvalue {i64, i64, i64} %l.52, 2
  store i64 %pr.53, ptr %h15.a.54
  %l.55 = load i64, ptr %w14.a.51
  %l.56 = load i64, ptr %h15.a.54
  %i.57 = mul nsw i64 %l.55, %l.56
  store i64 %i.57, ptr %t16.a.58
  %l.59 = load i64, ptr %t16.a.58
  ret i64 %l.59
}

define internal void @make_shape(ptr noalias sret({i64, i64, i64}) %__sret__, i64 noundef %i) nounwind willreturn {
pre_entry:
  %i.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  %t2.a.5 = alloca i64, align 8
  store i64 0, ptr %t2.a.5
  %t3.a.9 = alloca i1, align 8
  store i1 0, ptr %t3.a.9
  %t4.a.11 = alloca i64, align 8
  store i64 0, ptr %t4.a.11
  %t5.a.15 = alloca i64, align 8
  store i64 0, ptr %t5.a.15
  %t6.a.16 = alloca i64, align 8
  store i64 0, ptr %t6.a.16
  %t7.a.20 = alloca i64, align 8
  store i64 0, ptr %t7.a.20
  %t9.a.25 = alloca {i64, i64, i64}, align 8
  store {i64, i64, i64} zeroinitializer, ptr %t9.a.25
  %t11.a.27 = alloca i64, align 8
  store i64 0, ptr %t11.a.27
  %t12.a.31 = alloca i1, align 8
  store i1 0, ptr %t12.a.31
  %t13.a.33 = alloca i64, align 8
  store i64 0, ptr %t13.a.33
  %t14.a.37 = alloca i64, align 8
  store i64 0, ptr %t14.a.37
  %t15.a.38 = alloca i64, align 8
  store i64 0, ptr %t15.a.38
  %t16.a.42 = alloca i64, align 8
  store i64 0, ptr %t16.a.42
  %t18.a.47 = alloca {i64, i64, i64}, align 8
  store {i64, i64, i64} zeroinitializer, ptr %t18.a.47
  %t20.a.49 = alloca i64, align 8
  store i64 0, ptr %t20.a.49
  %t21.a.53 = alloca i1, align 8
  store i1 0, ptr %t21.a.53
  %t22.a.55 = alloca i64, align 8
  store i64 0, ptr %t22.a.55
  %t23.a.59 = alloca i64, align 8
  store i64 0, ptr %t23.a.59
  %t24.a.60 = alloca i64, align 8
  store i64 0, ptr %t24.a.60
  %t25.a.64 = alloca i64, align 8
  store i64 0, ptr %t25.a.64
  %t26.a.65 = alloca i64, align 8
  store i64 0, ptr %t26.a.65
  %t27.a.69 = alloca i64, align 8
  store i64 0, ptr %t27.a.69
  %t28.a.70 = alloca i64, align 8
  store i64 0, ptr %t28.a.70
  %t29.a.74 = alloca i64, align 8
  store i64 0, ptr %t29.a.74
  %t31.a.80 = alloca {i64, i64, i64}, align 8
  store {i64, i64, i64} zeroinitializer, ptr %t31.a.80
  %t33.a.82 = alloca i64, align 8
  store i64 0, ptr %t33.a.82
  %t34.a.86 = alloca i1, align 8
  store i1 0, ptr %t34.a.86
  %t35.a.91 = alloca {i64, i64, i64}, align 8
  store {i64, i64, i64} zeroinitializer, ptr %t35.a.91
  %t37.a.93 = alloca i64, align 8
  store i64 0, ptr %t37.a.93
  %t38.a.97 = alloca i1, align 8
  store i1 0, ptr %t38.a.97
  %t39.a.99 = alloca i64, align 8
  store i64 0, ptr %t39.a.99
  %t40.a.103 = alloca i64, align 8
  store i64 0, ptr %t40.a.103
  %t41.a.104 = alloca i64, align 8
  store i64 0, ptr %t41.a.104
  %t42.a.108 = alloca i64, align 8
  store i64 0, ptr %t42.a.108
  %t44.a.113 = alloca {i64, i64, i64}, align 8
  store {i64, i64, i64} zeroinitializer, ptr %t44.a.113
  %t46.a.115 = alloca i64, align 8
  store i64 0, ptr %t46.a.115
  %t47.a.119 = alloca i64, align 8
  store i64 0, ptr %t47.a.119
  %t48.a.120 = alloca i64, align 8
  store i64 0, ptr %t48.a.120
  %t49.a.124 = alloca i64, align 8
  store i64 0, ptr %t49.a.124
  %t50.a.125 = alloca i64, align 8
  store i64 0, ptr %t50.a.125
  %t51.a.129 = alloca i64, align 8
  store i64 0, ptr %t51.a.129
  %t52.a.130 = alloca i64, align 8
  store i64 0, ptr %t52.a.130
  %t53.a.134 = alloca i64, align 8
  store i64 0, ptr %t53.a.134
  %t55.a.140 = alloca {i64, i64, i64}, align 8
  store {i64, i64, i64} zeroinitializer, ptr %t55.a.140
  store i64 %i, ptr %i.addr
  br label %entry
entry:
  store i64 6, ptr %t0.a.0
  %l.1 = load i64, ptr %i.addr
  %l.2 = load i64, ptr %t0.a.0
  %i.3 = srem i64 %l.1, %l.2
  store i64 %i.3, ptr %t1.a.4
  store i64 0, ptr %t2.a.5
  %l.6 = load i64, ptr %t1.a.4
  %l.7 = load i64, ptr %t2.a.5
  %i.8 = icmp eq i64 %l.6, %l.7
  store i1 %i.8, ptr %t3.a.9
  %l.10 = load i1, ptr %t3.a.9
  br i1 %l.10, label %if_then0, label %if_else1
if_then0:
  store i64 50, ptr %t4.a.11
  %l.12 = load i64, ptr %i.addr
  %l.13 = load i64, ptr %t4.a.11
  %i.14 = srem i64 %l.12, %l.13
  store i64 %i.14, ptr %t5.a.15
  store i64 1, ptr %t6.a.16
  %l.17 = load i64, ptr %t5.a.15
  %l.18 = load i64, ptr %t6.a.16
  %i.19 = add nsw i64 %l.17, %l.18
  store i64 %i.19, ptr %t7.a.20
  %l.21 = load i64, ptr %t7.a.20
  %ei.22 = insertvalue {i64, i64, i64} undef, i64 0, 0
  %ei.23 = insertvalue {i64, i64, i64} %ei.22, i64 %l.21, 1
  %ei.24 = insertvalue {i64, i64, i64} %ei.23, i64 0, 2
  store {i64, i64, i64} %ei.24, ptr %t9.a.25
  %l.26 = load {i64, i64, i64}, ptr %t9.a.25
  store {i64, i64, i64} %l.26, ptr %__sret__
  ret void
if_else1:
  br label %if_merge2
if_merge2:
  store i64 1, ptr %t11.a.27
  %l.28 = load i64, ptr %t1.a.4
  %l.29 = load i64, ptr %t11.a.27
  %i.30 = icmp eq i64 %l.28, %l.29
  store i1 %i.30, ptr %t12.a.31
  %l.32 = load i1, ptr %t12.a.31
  br i1 %l.32, label %if_then3, label %if_else4
if_then3:
  store i64 30, ptr %t13.a.33
  %l.34 = load i64, ptr %i.addr
  %l.35 = load i64, ptr %t13.a.33
  %i.36 = srem i64 %l.34, %l.35
  store i64 %i.36, ptr %t14.a.37
  store i64 1, ptr %t15.a.38
  %l.39 = load i64, ptr %t14.a.37
  %l.40 = load i64, ptr %t15.a.38
  %i.41 = add nsw i64 %l.39, %l.40
  store i64 %i.41, ptr %t16.a.42
  %l.43 = load i64, ptr %t16.a.42
  %ei.44 = insertvalue {i64, i64, i64} undef, i64 1, 0
  %ei.45 = insertvalue {i64, i64, i64} %ei.44, i64 %l.43, 1
  %ei.46 = insertvalue {i64, i64, i64} %ei.45, i64 0, 2
  store {i64, i64, i64} %ei.46, ptr %t18.a.47
  %l.48 = load {i64, i64, i64}, ptr %t18.a.47
  store {i64, i64, i64} %l.48, ptr %__sret__
  ret void
if_else4:
  br label %if_merge5
if_merge5:
  store i64 2, ptr %t20.a.49
  %l.50 = load i64, ptr %t1.a.4
  %l.51 = load i64, ptr %t20.a.49
  %i.52 = icmp eq i64 %l.50, %l.51
  store i1 %i.52, ptr %t21.a.53
  %l.54 = load i1, ptr %t21.a.53
  br i1 %l.54, label %if_then6, label %if_else7
if_then6:
  store i64 20, ptr %t22.a.55
  %l.56 = load i64, ptr %i.addr
  %l.57 = load i64, ptr %t22.a.55
  %i.58 = srem i64 %l.56, %l.57
  store i64 %i.58, ptr %t23.a.59
  store i64 1, ptr %t24.a.60
  %l.61 = load i64, ptr %t23.a.59
  %l.62 = load i64, ptr %t24.a.60
  %i.63 = add nsw i64 %l.61, %l.62
  store i64 %i.63, ptr %t25.a.64
  store i64 40, ptr %t26.a.65
  %l.66 = load i64, ptr %i.addr
  %l.67 = load i64, ptr %t26.a.65
  %i.68 = srem i64 %l.66, %l.67
  store i64 %i.68, ptr %t27.a.69
  store i64 1, ptr %t28.a.70
  %l.71 = load i64, ptr %t27.a.69
  %l.72 = load i64, ptr %t28.a.70
  %i.73 = add nsw i64 %l.71, %l.72
  store i64 %i.73, ptr %t29.a.74
  %l.75 = load i64, ptr %t25.a.64
  %l.76 = load i64, ptr %t29.a.74
  %ei.77 = insertvalue {i64, i64, i64} undef, i64 2, 0
  %ei.78 = insertvalue {i64, i64, i64} %ei.77, i64 %l.75, 1
  %ei.79 = insertvalue {i64, i64, i64} %ei.78, i64 %l.76, 2
  store {i64, i64, i64} %ei.79, ptr %t31.a.80
  %l.81 = load {i64, i64, i64}, ptr %t31.a.80
  store {i64, i64, i64} %l.81, ptr %__sret__
  ret void
if_else7:
  br label %if_merge8
if_merge8:
  store i64 3, ptr %t33.a.82
  %l.83 = load i64, ptr %t1.a.4
  %l.84 = load i64, ptr %t33.a.82
  %i.85 = icmp eq i64 %l.83, %l.84
  store i1 %i.85, ptr %t34.a.86
  %l.87 = load i1, ptr %t34.a.86
  br i1 %l.87, label %if_then9, label %if_else10
if_then9:
  %ei.88 = insertvalue {i64, i64, i64} undef, i64 3, 0
  %ei.89 = insertvalue {i64, i64, i64} %ei.88, i64 0, 1
  %ei.90 = insertvalue {i64, i64, i64} %ei.89, i64 0, 2
  store {i64, i64, i64} %ei.90, ptr %t35.a.91
  %l.92 = load {i64, i64, i64}, ptr %t35.a.91
  store {i64, i64, i64} %l.92, ptr %__sret__
  ret void
if_else10:
  br label %if_merge11
if_merge11:
  store i64 4, ptr %t37.a.93
  %l.94 = load i64, ptr %t1.a.4
  %l.95 = load i64, ptr %t37.a.93
  %i.96 = icmp eq i64 %l.94, %l.95
  store i1 %i.96, ptr %t38.a.97
  %l.98 = load i1, ptr %t38.a.97
  br i1 %l.98, label %if_then12, label %if_else13
if_then12:
  store i64 100, ptr %t39.a.99
  %l.100 = load i64, ptr %i.addr
  %l.101 = load i64, ptr %t39.a.99
  %i.102 = srem i64 %l.100, %l.101
  store i64 %i.102, ptr %t40.a.103
  store i64 1, ptr %t41.a.104
  %l.105 = load i64, ptr %t40.a.103
  %l.106 = load i64, ptr %t41.a.104
  %i.107 = add nsw i64 %l.105, %l.106
  store i64 %i.107, ptr %t42.a.108
  %l.109 = load i64, ptr %t42.a.108
  %ei.110 = insertvalue {i64, i64, i64} undef, i64 4, 0
  %ei.111 = insertvalue {i64, i64, i64} %ei.110, i64 %l.109, 1
  %ei.112 = insertvalue {i64, i64, i64} %ei.111, i64 0, 2
  store {i64, i64, i64} %ei.112, ptr %t44.a.113
  %l.114 = load {i64, i64, i64}, ptr %t44.a.113
  store {i64, i64, i64} %l.114, ptr %__sret__
  ret void
if_else13:
  br label %if_merge14
if_merge14:
  store i64 25, ptr %t46.a.115
  %l.116 = load i64, ptr %i.addr
  %l.117 = load i64, ptr %t46.a.115
  %i.118 = srem i64 %l.116, %l.117
  store i64 %i.118, ptr %t47.a.119
  store i64 1, ptr %t48.a.120
  %l.121 = load i64, ptr %t47.a.119
  %l.122 = load i64, ptr %t48.a.120
  %i.123 = add nsw i64 %l.121, %l.122
  store i64 %i.123, ptr %t49.a.124
  store i64 35, ptr %t50.a.125
  %l.126 = load i64, ptr %i.addr
  %l.127 = load i64, ptr %t50.a.125
  %i.128 = srem i64 %l.126, %l.127
  store i64 %i.128, ptr %t51.a.129
  store i64 1, ptr %t52.a.130
  %l.131 = load i64, ptr %t51.a.129
  %l.132 = load i64, ptr %t52.a.130
  %i.133 = add nsw i64 %l.131, %l.132
  store i64 %i.133, ptr %t53.a.134
  %l.135 = load i64, ptr %t49.a.124
  %l.136 = load i64, ptr %t53.a.134
  %ei.137 = insertvalue {i64, i64, i64} undef, i64 5, 0
  %ei.138 = insertvalue {i64, i64, i64} %ei.137, i64 %l.135, 1
  %ei.139 = insertvalue {i64, i64, i64} %ei.138, i64 %l.136, 2
  store {i64, i64, i64} %ei.139, ptr %t55.a.140
  %l.141 = load {i64, i64, i64}, ptr %t55.a.140
  store {i64, i64, i64} %l.141, ptr %__sret__
  ret void
}

define i64 @main() nounwind willreturn {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %total.a.2 = alloca i64, align 8
  store i64 0, ptr %total.a.2
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3
  %i.a.5 = alloca i64, align 8
  store i64 0, ptr %i.a.5
  %t2.a.6 = alloca i64, align 8
  store i64 0, ptr %t2.a.6
  %t3.a.10 = alloca i1, align 8
  store i1 0, ptr %t3.a.10
  %sret.13 = alloca {i64, i64, i64}, align 8
  %t4.a.15 = alloca {i64, i64, i64}, align 8
  store {i64, i64, i64} zeroinitializer, ptr %t4.a.15
  %t5.a.18 = alloca i64, align 8
  store i64 0, ptr %t5.a.18
  %t6.a.22 = alloca i64, align 8
  store i64 0, ptr %t6.a.22
  %t7.a.24 = alloca i64, align 8
  store i64 0, ptr %t7.a.24
  %t8.a.28 = alloca i64, align 8
  store i64 0, ptr %t8.a.28
  %t9.a.33 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t9.a.33
  %str_track.36 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.36
  %t10.a.37 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.37
  %str_track.41 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.41
  %t11.a.42 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t11.a.42
  %t12.a.44 = alloca i1, align 8
  store i1 0, ptr %t12.a.44
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  store i64 %l.1, ptr %total.a.2
  store i64 0, ptr %t1.a.3
  %l.4 = load i64, ptr %t1.a.3
  store i64 %l.4, ptr %i.a.5
  br label %while_header0
while_header0:
  store i64 100000, ptr %t2.a.6
  %l.7 = load i64, ptr %i.a.5
  %l.8 = load i64, ptr %t2.a.6
  %i.9 = icmp slt i64 %l.7, %l.8
  store i1 %i.9, ptr %t3.a.10
  %l.11 = load i1, ptr %t3.a.10
  br i1 %l.11, label %while_body1, label %while_exit2
while_body1:
  %l.12 = load i64, ptr %i.a.5
  store {i64, i64, i64} zeroinitializer, ptr %sret.13
  call void @make_shape(ptr sret({i64, i64, i64}) %sret.13, i64 %l.12)
  %c.14 = load {i64, i64, i64}, ptr %sret.13
  store {i64, i64, i64} %c.14, ptr %t4.a.15
  %l.16 = load {i64, i64, i64}, ptr %t4.a.15
  %c.17 = call i64 @area({i64, i64, i64} %l.16)
  store i64 %c.17, ptr %t5.a.18
  %l.19 = load i64, ptr %total.a.2
  %l.20 = load i64, ptr %t5.a.18
  %i.21 = add nsw i64 %l.19, %l.20
  store i64 %i.21, ptr %t6.a.22
  %l.23 = load i64, ptr %t6.a.22
  store i64 %l.23, ptr %total.a.2
  store i64 1, ptr %t7.a.24
  %l.25 = load i64, ptr %i.a.5
  %l.26 = load i64, ptr %t7.a.24
  %i.27 = add nsw i64 %l.25, %l.26
  store i64 %i.27, ptr %t8.a.28
  %l.29 = load i64, ptr %t8.a.28
  store i64 %l.29, ptr %i.a.5
  br label %while_header0
while_exit2:
  %sp.30 = getelementptr inbounds [11 x i8], ptr @.str.0, i64 0, i64 0
  %s.31 = insertvalue {ptr, i64} undef, ptr %sp.30, 0
  %s.32 = insertvalue {ptr, i64} %s.31, i64 11, 1
  store {ptr, i64} %s.32, ptr %t9.a.33
  %l.34 = load i64, ptr %total.a.2
  %rt.35 = call {ptr, i64} @__mn_str_from_int(i64 %l.34)
  store {ptr, i64} %rt.35, ptr %str_track.36
  store {ptr, i64} %rt.35, ptr %t10.a.37
  %l.38 = load {ptr, i64}, ptr %t9.a.33
  %l.39 = load {ptr, i64}, ptr %t10.a.37
  %rt.40 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.38, {ptr, i64} %l.39)
  store {ptr, i64} %rt.40, ptr %str_track.41
  store {ptr, i64} %rt.40, ptr %t11.a.42
  %l.43 = load {ptr, i64}, ptr %t11.a.42
  call void @__mn_str_println({ptr, i64} %l.43)
  store i1 0, ptr %t12.a.44
  %drop.s.45 = load {ptr, i64}, ptr %str_track.36
  %drop.p.46 = extractvalue {ptr, i64} %drop.s.45, 0
  %drop.null.47 = icmp eq ptr %drop.p.46, null
  br i1 %drop.null.47, label %drop.skip.48, label %drop.check.48
drop.check.48:
  call void @__mn_str_free({ptr, i64} %drop.s.45)
  br label %drop.skip.48
drop.skip.48:
  %drop.s.49 = load {ptr, i64}, ptr %str_track.41
  %drop.p.50 = extractvalue {ptr, i64} %drop.s.49, 0
  %drop.null.51 = icmp eq ptr %drop.p.50, null
  br i1 %drop.null.51, label %drop.skip.52, label %drop.check.52
drop.check.52:
  call void @__mn_str_free({ptr, i64} %drop.s.49)
  br label %drop.skip.52
drop.skip.52:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"5.1.2"}
