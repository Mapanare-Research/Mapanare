; ModuleID = '17_option'
source_filename = "17_option"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [4 x i8] c"none", align 8
@.str.1 = private constant [4 x i8] c"none", align 8

declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal {i1, i64} @find_positive(i64 %x) {
pre_entry:
  %x.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i1, align 8
  store i1 0, ptr %t1.a.4
  %t3.a.9 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t3.a.9
  %t5.a.11 = alloca i64, align 8
  store i64 0, ptr %t5.a.11
  %t7.a.15 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t7.a.15
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
  %l.6 = load i64, ptr %x.addr
  %ws.7 = insertvalue {i1, i64} undef, i1 1, 0
  %ws.8 = insertvalue {i1, i64} %ws.7, i64 %l.6, 1
  store {i1, i64} %ws.8, ptr %t3.a.9
  %l.10 = load {i1, i64}, ptr %t3.a.9
  ret {i1, i64} %l.10
if_else1:
  br label %if_merge2
if_merge2:
  store i64 0, ptr %t5.a.11
  %l.12 = load i64, ptr %t5.a.11
  %ws.13 = insertvalue {i1, i64} undef, i1 1, 0
  %ws.14 = insertvalue {i1, i64} %ws.13, i64 %l.12, 1
  store {i1, i64} %ws.14, ptr %t7.a.15
  %l.16 = load {i1, i64}, ptr %t7.a.15
  ret {i1, i64} %l.16
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.3 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t1.a.3
  %a.a.5 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %a.a.5
  %tag2.a.9 = alloca i64, align 8
  store i64 0, ptr %tag2.a.9
  %t9.a.11 = alloca i64, align 8
  store i64 0, ptr %t9.a.11
  %t11.a.15 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %t11.a.15
  %b.a.17 = alloca {i1, i64}, align 8
  store {i1, i64} zeroinitializer, ptr %b.a.17
  %tag12.a.21 = alloca i64, align 8
  store i64 0, ptr %tag12.a.21
  %v3.a.25 = alloca i64, align 8
  store i64 0, ptr %v3.a.25
  %str_track.28 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.28
  %t4.a.29 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.29
  %t5.a.31 = alloca i1, align 8
  store i1 0, ptr %t5.a.31
  %t6.a.35 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.35
  %t7.a.37 = alloca i1, align 8
  store i1 0, ptr %t7.a.37
  %v13.a.44 = alloca i64, align 8
  store i64 0, ptr %v13.a.44
  %str_track.47 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.47
  %t14.a.48 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t14.a.48
  %t15.a.50 = alloca i1, align 8
  store i1 0, ptr %t15.a.50
  %t16.a.54 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t16.a.54
  %t17.a.56 = alloca i1, align 8
  store i1 0, ptr %t17.a.56
  br label %entry
entry:
  store i64 42, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %c.2 = call {i1, i64} @find_positive(i64 %l.1)
  store {i1, i64} %c.2, ptr %t1.a.3
  %l.4 = load {i1, i64}, ptr %t1.a.3
  store {i1, i64} %l.4, ptr %a.a.5
  %l.6 = load {i1, i64}, ptr %a.a.5
  %et.7 = extractvalue {i1, i64} %l.6, 0
  %etz.8 = zext i1 %et.7 to i64
  store i64 %etz.8, ptr %tag2.a.9
  %l.10 = load i64, ptr %tag2.a.9
  switch i64 %l.10, label %match_arm2 [
    i64 1, label %match_arm1
  ]
match_merge0:
  store i64 7, ptr %t9.a.11
  %l.12 = load i64, ptr %t9.a.11
  %ws.13 = insertvalue {i1, i64} undef, i1 1, 0
  %ws.14 = insertvalue {i1, i64} %ws.13, i64 %l.12, 1
  store {i1, i64} %ws.14, ptr %t11.a.15
  %l.16 = load {i1, i64}, ptr %t11.a.15
  store {i1, i64} %l.16, ptr %b.a.17
  %l.18 = load {i1, i64}, ptr %b.a.17
  %et.19 = extractvalue {i1, i64} %l.18, 0
  %etz.20 = zext i1 %et.19 to i64
  store i64 %etz.20, ptr %tag12.a.21
  %l.22 = load i64, ptr %tag12.a.21
  switch i64 %l.22, label %match_arm5 [
    i64 1, label %match_arm4
  ]
match_arm1:
  %l.23 = load {i1, i64}, ptr %a.a.5
  %sm.24 = extractvalue {i1, i64} %l.23, 1
  store i64 %sm.24, ptr %v3.a.25
  %l.26 = load i64, ptr %v3.a.25
  %rt.27 = call {ptr, i64} @__mn_str_from_int(i64 %l.26)
  store {ptr, i64} %rt.27, ptr %str_track.28
  store {ptr, i64} %rt.27, ptr %t4.a.29
  %l.30 = load {ptr, i64}, ptr %t4.a.29
  call void @__mn_str_println({ptr, i64} %l.30)
  store i1 0, ptr %t5.a.31
  br label %match_merge0
match_arm2:
  %sp.32 = getelementptr inbounds [4 x i8], ptr @.str.0, i64 0, i64 0
  %s.33 = insertvalue {ptr, i64} undef, ptr %sp.32, 0
  %s.34 = insertvalue {ptr, i64} %s.33, i64 4, 1
  store {ptr, i64} %s.34, ptr %t6.a.35
  %l.36 = load {ptr, i64}, ptr %t6.a.35
  call void @__mn_str_println({ptr, i64} %l.36)
  store i1 0, ptr %t7.a.37
  br label %match_merge0
match_merge3:
  %drop.s.38 = load {ptr, i64}, ptr %str_track.28
  %drop.p.39 = extractvalue {ptr, i64} %drop.s.38, 0
  %drop.null.40 = icmp eq ptr %drop.p.39, null
  br i1 %drop.null.40, label %drop.skip.41, label %drop.check.41
match_arm4:
  %l.42 = load {i1, i64}, ptr %b.a.17
  %sm.43 = extractvalue {i1, i64} %l.42, 1
  store i64 %sm.43, ptr %v13.a.44
  %l.45 = load i64, ptr %v13.a.44
  %rt.46 = call {ptr, i64} @__mn_str_from_int(i64 %l.45)
  store {ptr, i64} %rt.46, ptr %str_track.47
  store {ptr, i64} %rt.46, ptr %t14.a.48
  %l.49 = load {ptr, i64}, ptr %t14.a.48
  call void @__mn_str_println({ptr, i64} %l.49)
  store i1 0, ptr %t15.a.50
  br label %match_merge3
match_arm5:
  %sp.51 = getelementptr inbounds [4 x i8], ptr @.str.1, i64 0, i64 0
  %s.52 = insertvalue {ptr, i64} undef, ptr %sp.51, 0
  %s.53 = insertvalue {ptr, i64} %s.52, i64 4, 1
  store {ptr, i64} %s.53, ptr %t16.a.54
  %l.55 = load {ptr, i64}, ptr %t16.a.54
  call void @__mn_str_println({ptr, i64} %l.55)
  store i1 0, ptr %t17.a.56
  br label %match_merge3
drop.check.41:
  call void @__mn_str_free({ptr, i64} %drop.s.38)
  br label %drop.skip.41
drop.skip.41:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.32.0"}
