; ModuleID = '36_crypto'
source_filename = "36_crypto"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"hello world", align 8
@.str.1 = private constant [8 x i8] c"Mapanare", align 8
@.str.2 = private constant [2 x i8] c"AB", align 8

declare {ptr, i64} @__mn_sha256_str({ptr, i64}) nounwind willreturn
declare {ptr, i64} @__mn_hex_encode_str({ptr, i64}) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare {ptr, i64} @__mn_base64_encode_str({ptr, i64}) nounwind willreturn
declare {ptr, i64} @__mn_base64_decode_str({ptr, i64}) nounwind willreturn
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t0.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t0.a.3
  %str_track.6 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.6
  %t1.a.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.7
  %str_track.10 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.10
  %t2.a.11 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.11
  %t3.a.13 = alloca i1, align 8
  store i1 0, ptr %t3.a.13
  %t4.a.17 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.17
  %str_track.20 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.20
  %t5.a.21 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.21
  %t6.a.23 = alloca i1, align 8
  store i1 0, ptr %t6.a.23
  %str_track.26 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.26
  %t7.a.27 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t7.a.27
  %t8.a.29 = alloca i1, align 8
  store i1 0, ptr %t8.a.29
  %t9.a.33 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t9.a.33
  %str_track.36 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.36
  %t10.a.37 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.37
  %t11.a.39 = alloca i1, align 8
  store i1 0, ptr %t11.a.39
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [11 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 11, 1
  store {ptr, i64} %s.2, ptr %t0.a.3
  %l.4 = load {ptr, i64}, ptr %t0.a.3
  %rt.5 = call {ptr, i64} @__mn_sha256_str({ptr, i64} %l.4)
  store {ptr, i64} %rt.5, ptr %str_track.6
  store {ptr, i64} %rt.5, ptr %t1.a.7
  %l.8 = load {ptr, i64}, ptr %t1.a.7
  %rt.9 = call {ptr, i64} @__mn_hex_encode_str({ptr, i64} %l.8)
  store {ptr, i64} %rt.9, ptr %str_track.10
  store {ptr, i64} %rt.9, ptr %t2.a.11
  %l.12 = load {ptr, i64}, ptr %t2.a.11
  call void @__mn_str_println({ptr, i64} %l.12)
  store i1 0, ptr %t3.a.13
  %sp.14 = getelementptr inbounds [8 x i8], ptr @.str.1, i64 0, i64 0
  %s.15 = insertvalue {ptr, i64} undef, ptr %sp.14, 0
  %s.16 = insertvalue {ptr, i64} %s.15, i64 8, 1
  store {ptr, i64} %s.16, ptr %t4.a.17
  %l.18 = load {ptr, i64}, ptr %t4.a.17
  %rt.19 = call {ptr, i64} @__mn_base64_encode_str({ptr, i64} %l.18)
  store {ptr, i64} %rt.19, ptr %str_track.20
  store {ptr, i64} %rt.19, ptr %t5.a.21
  %l.22 = load {ptr, i64}, ptr %t5.a.21
  call void @__mn_str_println({ptr, i64} %l.22)
  store i1 0, ptr %t6.a.23
  %l.24 = load {ptr, i64}, ptr %t5.a.21
  %rt.25 = call {ptr, i64} @__mn_base64_decode_str({ptr, i64} %l.24)
  store {ptr, i64} %rt.25, ptr %str_track.26
  store {ptr, i64} %rt.25, ptr %t7.a.27
  %l.28 = load {ptr, i64}, ptr %t7.a.27
  call void @__mn_str_println({ptr, i64} %l.28)
  store i1 0, ptr %t8.a.29
  %sp.30 = getelementptr inbounds [2 x i8], ptr @.str.2, i64 0, i64 0
  %s.31 = insertvalue {ptr, i64} undef, ptr %sp.30, 0
  %s.32 = insertvalue {ptr, i64} %s.31, i64 2, 1
  store {ptr, i64} %s.32, ptr %t9.a.33
  %l.34 = load {ptr, i64}, ptr %t9.a.33
  %rt.35 = call {ptr, i64} @__mn_hex_encode_str({ptr, i64} %l.34)
  store {ptr, i64} %rt.35, ptr %str_track.36
  store {ptr, i64} %rt.35, ptr %t10.a.37
  %l.38 = load {ptr, i64}, ptr %t10.a.37
  call void @__mn_str_println({ptr, i64} %l.38)
  store i1 0, ptr %t11.a.39
  %drop.s.40 = load {ptr, i64}, ptr %str_track.6
  %drop.p.41 = extractvalue {ptr, i64} %drop.s.40, 0
  %drop.null.42 = icmp eq ptr %drop.p.41, null
  br i1 %drop.null.42, label %drop.skip.43, label %drop.check.43
drop.check.43:
  call void @__mn_str_free({ptr, i64} %drop.s.40)
  br label %drop.skip.43
drop.skip.43:
  %drop.s.44 = load {ptr, i64}, ptr %str_track.10
  %drop.p.45 = extractvalue {ptr, i64} %drop.s.44, 0
  %drop.null.46 = icmp eq ptr %drop.p.45, null
  br i1 %drop.null.46, label %drop.skip.47, label %drop.check.47
drop.check.47:
  call void @__mn_str_free({ptr, i64} %drop.s.44)
  br label %drop.skip.47
drop.skip.47:
  %drop.s.48 = load {ptr, i64}, ptr %str_track.20
  %drop.p.49 = extractvalue {ptr, i64} %drop.s.48, 0
  %drop.null.50 = icmp eq ptr %drop.p.49, null
  br i1 %drop.null.50, label %drop.skip.51, label %drop.check.51
drop.check.51:
  call void @__mn_str_free({ptr, i64} %drop.s.48)
  br label %drop.skip.51
drop.skip.51:
  %drop.s.52 = load {ptr, i64}, ptr %str_track.26
  %drop.p.53 = extractvalue {ptr, i64} %drop.s.52, 0
  %drop.null.54 = icmp eq ptr %drop.p.53, null
  br i1 %drop.null.54, label %drop.skip.55, label %drop.check.55
drop.check.55:
  call void @__mn_str_free({ptr, i64} %drop.s.52)
  br label %drop.skip.55
drop.skip.55:
  %drop.s.56 = load {ptr, i64}, ptr %str_track.36
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
!0 = !{!"4.34.0"}
