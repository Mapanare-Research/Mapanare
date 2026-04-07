; ModuleID = '28_traits'
source_filename = "28_traits"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 2

declare i32 @printf(ptr, ...)

define internal i64 @Vec2_magnitude(ptr %self) {
pre_entry:
  %self.addr = alloca ptr, align 8
  %t0.a.1 = alloca ptr, align 8
  store ptr null, ptr %t0.a.1
  %t1.a.3 = alloca ptr, align 8
  store ptr null, ptr %t1.a.3
  %t2.a.9 = alloca i64, align 8
  store i64 0, ptr %t2.a.9
  store ptr %self, ptr %self.addr
  br label %entry
entry:
  %l.0 = load ptr, ptr %self.addr
  store ptr %l.0, ptr %t0.a.1
  %l.2 = load ptr, ptr %self.addr
  store ptr %l.2, ptr %t1.a.3
  %l.4 = load ptr, ptr %t0.a.1
  %l.5 = load ptr, ptr %t1.a.3
  %p2i.6 = ptrtoint ptr %l.4 to i64
  %p2i.7 = ptrtoint ptr %l.5 to i64
  %i.8 = add nsw i64 %p2i.6, %p2i.7
  store i64 %i.8, ptr %t2.a.9
  %l.10 = load i64, ptr %t2.a.9
  ret i64 %l.10
}

define internal i64 @double__Int(i64 %x) {
pre_entry:
  %x.addr = alloca i64, align 8
  store i64 %x, ptr %x.addr
  br label %entry
entry:
  %l.0 = load i64, ptr %x.addr
  ret i64 %l.0
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1
  %t2.a.6 = alloca {i64, i64}, align 8
  store {i64, i64} zeroinitializer, ptr %t2.a.6
  %rc.8 = alloca {i64, i64}, align 8
  %t4.a.11 = alloca i64, align 8
  store i64 0, ptr %t4.a.11
  %t5.a.15 = alloca i1, align 8
  store i1 0, ptr %t5.a.15
  %t6.a.16 = alloca i64, align 8
  store i64 0, ptr %t6.a.16
  %t7.a.19 = alloca i64, align 8
  store i64 0, ptr %t7.a.19
  %t8.a.23 = alloca i1, align 8
  store i1 0, ptr %t8.a.23
  br label %entry
entry:
  store i64 3, ptr %t0.a.0
  store i64 7, ptr %t1.a.1
  %l.2 = load i64, ptr %t0.a.0
  %si.3 = insertvalue {i64, i64} undef, i64 %l.2, 0
  %l.4 = load i64, ptr %t1.a.1
  %si.5 = insertvalue {i64, i64} %si.3, i64 %l.4, 1
  store {i64, i64} %si.5, ptr %t2.a.6
  %l.7 = load {i64, i64}, ptr %t2.a.6
  store {i64, i64} %l.7, ptr %rc.8
  %rv.9 = load ptr, ptr %rc.8
  %c.10 = call i64 @Vec2_magnitude(ptr %rv.9)
  store i64 %c.10, ptr %t4.a.11
  %l.12 = load i64, ptr %t4.a.11
  %fp.13 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.14 = call i32 (ptr, ...) @printf(ptr %fp.13, i64 %l.12)
  store i1 0, ptr %t5.a.15
  store i64 21, ptr %t6.a.16
  %l.17 = load i64, ptr %t6.a.16
  %c.18 = call i64 @double__Int(i64 %l.17)
  store i64 %c.18, ptr %t7.a.19
  %l.20 = load i64, ptr %t7.a.19
  %fp.21 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.22 = call i32 (ptr, ...) @printf(ptr %fp.21, i64 %l.20)
  store i1 0, ptr %t8.a.23
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.9.0"}
