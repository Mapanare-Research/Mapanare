; ModuleID = '64_closure_typed'
source_filename = "64_closure_typed"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
declare void @__mn_str_println({ptr, i64})
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal i64 @lambda0(ptr %__env_ptr, i64 %x) nounwind willreturn {
pre_entry:
  %__env_ptr.addr = alloca ptr, align 8
  %x.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  store ptr %__env_ptr, ptr %__env_ptr.addr
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  store i64 2, ptr %t0.a.0
  %l.1 = load i64, ptr %x.addr
  %l.2 = load i64, ptr %t0.a.0
  %i.3 = mul nsw i64 %l.1, %l.2
  store i64 %i.3, ptr %t1.a.4
  %l.5 = load i64, ptr %t1.a.4
  ret i64 %l.5
}

define internal i64 @lambda2(ptr %__env_ptr, i64 %x) nounwind willreturn {
pre_entry:
  %__env_ptr.addr = alloca ptr, align 8
  %x.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  store ptr %__env_ptr, ptr %__env_ptr.addr
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  store i64 0, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %l.2 = load i64, ptr %x.addr
  %i.3 = sub nsw i64 %l.1, %l.2
  store i64 %i.3, ptr %t1.a.4
  %l.5 = load i64, ptr %t1.a.4
  ret i64 %l.5
}

define internal void @lambda4(ptr %__env_ptr, ptr %a, ptr %b) nounwind willreturn {
pre_entry:
  %__env_ptr.addr = alloca ptr, align 8
  %a.addr = alloca ptr, align 8
  %b.addr = alloca ptr, align 8
  %t0.a.5 = alloca i64, align 8
  store i64 0, ptr %t0.a.5
  store ptr %__env_ptr, ptr %__env_ptr.addr
  store ptr %a, ptr %a.addr
  store ptr %b, ptr %b.addr
  br label %entry
entry:
  %l.0 = load ptr, ptr %a.addr
  %l.1 = load ptr, ptr %b.addr
  %p2i.2 = ptrtoint ptr %l.0 to i64
  %p2i.3 = ptrtoint ptr %l.1 to i64
  %i.4 = add nsw i64 %p2i.2, %p2i.3
  store i64 %i.4, ptr %t0.a.5
  %l.6 = load i64, ptr %t0.a.5
  ret void
}

define i64 @main() nounwind willreturn {
pre_entry:
  %t1.a.2 = alloca {ptr, ptr}, align 8
  store {ptr, ptr} zeroinitializer, ptr %t1.a.2
  %t3.a.5 = alloca {ptr, ptr}, align 8
  store {ptr, ptr} zeroinitializer, ptr %t3.a.5
  %t5.a.8 = alloca {ptr, ptr}, align 8
  store {ptr, ptr} zeroinitializer, ptr %t5.a.8
  %t6.a.9 = alloca i64, align 8
  store i64 0, ptr %t6.a.9
  %_inl1_t0.a.15 = alloca i64, align 8
  store i64 0, ptr %_inl1_t0.a.15
  %str_track.18 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.18
  %t8.a.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t8.a.19
  %t9.a.21 = alloca i1, align 8
  store i1 0, ptr %t9.a.21
  %t10.a.22 = alloca i64, align 8
  store i64 0, ptr %t10.a.22
  %_inl2_t0.a.28 = alloca i64, align 8
  store i64 0, ptr %_inl2_t0.a.28
  %str_track.31 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.31
  %t12.a.32 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t12.a.32
  %t13.a.34 = alloca i1, align 8
  store i1 0, ptr %t13.a.34
  %t14.a.35 = alloca i64, align 8
  store i64 0, ptr %t14.a.35
  %t15.a.41 = alloca i64, align 8
  store i64 0, ptr %t15.a.41
  %str_track.44 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.44
  %t16.a.45 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t16.a.45
  %t17.a.47 = alloca i1, align 8
  store i1 0, ptr %t17.a.47
  %t18.a.48 = alloca i64, align 8
  store i64 0, ptr %t18.a.48
  %t19.a.49 = alloca i64, align 8
  store i64 0, ptr %t19.a.49
  %_inl3_t0.a.56 = alloca i64, align 8
  store i64 0, ptr %_inl3_t0.a.56
  %str_track.59 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.59
  %t21.a.60 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t21.a.60
  %t22.a.62 = alloca i1, align 8
  store i1 0, ptr %t22.a.62
  br label %entry
entry:
  %cc.0 = insertvalue {ptr, ptr} undef, ptr @lambda0, 0
  %cc.1 = insertvalue {ptr, ptr} %cc.0, ptr null, 1
  store {ptr, ptr} %cc.1, ptr %t1.a.2
  %cc.3 = insertvalue {ptr, ptr} undef, ptr @lambda2, 0
  %cc.4 = insertvalue {ptr, ptr} %cc.3, ptr null, 1
  store {ptr, ptr} %cc.4, ptr %t3.a.5
  %cc.6 = insertvalue {ptr, ptr} undef, ptr @lambda4, 0
  %cc.7 = insertvalue {ptr, ptr} %cc.6, ptr null, 1
  store {ptr, ptr} %cc.7, ptr %t5.a.8
  store i64 5, ptr %t6.a.9
  br label %_inl1_entry
_inl1_entry:
  %l.10 = load {ptr, ptr}, ptr %t1.a.2
  %l.11 = load i64, ptr %t6.a.9
  %cfn.12 = extractvalue {ptr, ptr} %l.10, 0
  %cen.13 = extractvalue {ptr, ptr} %l.10, 1
  %ccr.14 = call i64 %cfn.12(ptr %cen.13, i64 %l.11)
  store i64 %ccr.14, ptr %_inl1_t0.a.15
  br label %_inl1_ret
_inl1_ret:
  %l.16 = load i64, ptr %_inl1_t0.a.15
  %rt.17 = call {ptr, i64} @__mn_str_from_int(i64 %l.16)
  store {ptr, i64} %rt.17, ptr %str_track.18
  store {ptr, i64} %rt.17, ptr %t8.a.19
  %l.20 = load {ptr, i64}, ptr %t8.a.19
  call void @__mn_str_println({ptr, i64} %l.20)
  store i1 0, ptr %t9.a.21
  store i64 3, ptr %t10.a.22
  br label %_inl2_entry
_inl2_entry:
  %l.23 = load {ptr, ptr}, ptr %t3.a.5
  %l.24 = load i64, ptr %t10.a.22
  %cfn.25 = extractvalue {ptr, ptr} %l.23, 0
  %cen.26 = extractvalue {ptr, ptr} %l.23, 1
  %ccr.27 = call i64 %cfn.25(ptr %cen.26, i64 %l.24)
  store i64 %ccr.27, ptr %_inl2_t0.a.28
  br label %_inl2_ret
_inl2_ret:
  %l.29 = load i64, ptr %_inl2_t0.a.28
  %rt.30 = call {ptr, i64} @__mn_str_from_int(i64 %l.29)
  store {ptr, i64} %rt.30, ptr %str_track.31
  store {ptr, i64} %rt.30, ptr %t12.a.32
  %l.33 = load {ptr, i64}, ptr %t12.a.32
  call void @__mn_str_println({ptr, i64} %l.33)
  store i1 0, ptr %t13.a.34
  store i64 10, ptr %t14.a.35
  %l.36 = load {ptr, ptr}, ptr %t1.a.2
  %l.37 = load i64, ptr %t14.a.35
  %cfn.38 = extractvalue {ptr, ptr} %l.36, 0
  %cen.39 = extractvalue {ptr, ptr} %l.36, 1
  %ccr.40 = call i64 %cfn.38(ptr %cen.39, i64 %l.37)
  store i64 %ccr.40, ptr %t15.a.41
  %l.42 = load i64, ptr %t15.a.41
  %rt.43 = call {ptr, i64} @__mn_str_from_int(i64 %l.42)
  store {ptr, i64} %rt.43, ptr %str_track.44
  store {ptr, i64} %rt.43, ptr %t16.a.45
  %l.46 = load {ptr, i64}, ptr %t16.a.45
  call void @__mn_str_println({ptr, i64} %l.46)
  store i1 0, ptr %t17.a.47
  store i64 7, ptr %t18.a.48
  store i64 8, ptr %t19.a.49
  br label %_inl3_entry
_inl3_entry:
  %l.50 = load {ptr, ptr}, ptr %t5.a.8
  %l.51 = load i64, ptr %t18.a.48
  %l.52 = load i64, ptr %t19.a.49
  %cfn.53 = extractvalue {ptr, ptr} %l.50, 0
  %cen.54 = extractvalue {ptr, ptr} %l.50, 1
  %ccr.55 = call i64 %cfn.53(ptr %cen.54, i64 %l.51, i64 %l.52)
  store i64 %ccr.55, ptr %_inl3_t0.a.56
  br label %_inl3_ret
_inl3_ret:
  %l.57 = load i64, ptr %_inl3_t0.a.56
  %rt.58 = call {ptr, i64} @__mn_str_from_int(i64 %l.57)
  store {ptr, i64} %rt.58, ptr %str_track.59
  store {ptr, i64} %rt.58, ptr %t21.a.60
  %l.61 = load {ptr, i64}, ptr %t21.a.60
  call void @__mn_str_println({ptr, i64} %l.61)
  store i1 0, ptr %t22.a.62
  %drop.s.63 = load {ptr, i64}, ptr %str_track.18
  %drop.p.64 = extractvalue {ptr, i64} %drop.s.63, 0
  %drop.null.65 = icmp eq ptr %drop.p.64, null
  br i1 %drop.null.65, label %drop.skip.66, label %drop.check.66
drop.check.66:
  call void @__mn_str_free({ptr, i64} %drop.s.63)
  br label %drop.skip.66
drop.skip.66:
  %drop.s.67 = load {ptr, i64}, ptr %str_track.31
  %drop.p.68 = extractvalue {ptr, i64} %drop.s.67, 0
  %drop.null.69 = icmp eq ptr %drop.p.68, null
  br i1 %drop.null.69, label %drop.skip.70, label %drop.check.70
drop.check.70:
  call void @__mn_str_free({ptr, i64} %drop.s.67)
  br label %drop.skip.70
drop.skip.70:
  %drop.s.71 = load {ptr, i64}, ptr %str_track.44
  %drop.p.72 = extractvalue {ptr, i64} %drop.s.71, 0
  %drop.null.73 = icmp eq ptr %drop.p.72, null
  br i1 %drop.null.73, label %drop.skip.74, label %drop.check.74
drop.check.74:
  call void @__mn_str_free({ptr, i64} %drop.s.71)
  br label %drop.skip.74
drop.skip.74:
  %drop.s.75 = load {ptr, i64}, ptr %str_track.59
  %drop.p.76 = extractvalue {ptr, i64} %drop.s.75, 0
  %drop.null.77 = icmp eq ptr %drop.p.76, null
  br i1 %drop.null.77, label %drop.skip.78, label %drop.check.78
drop.check.78:
  call void @__mn_str_free({ptr, i64} %drop.s.75)
  br label %drop.skip.78
drop.skip.78:
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
