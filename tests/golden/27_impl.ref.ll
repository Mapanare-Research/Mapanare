; ModuleID = '27_impl'
source_filename = "27_impl"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.fmt.0 = private constant [6 x i8] c"%lld\0A\00", align 2

declare i32 @printf(ptr, ...)

define internal i64 @Counter_get(ptr %self) {
pre_entry:
  %self.addr = alloca ptr, align 8
  %t0.a.1 = alloca ptr, align 8
  store ptr null, ptr %t0.a.1
  store ptr %self, ptr %self.addr
  br label %entry
entry:
  %l.0 = load ptr, ptr %self.addr
  store ptr %l.0, ptr %t0.a.1
  %l.2 = load ptr, ptr %t0.a.1
  %p2i.3 = ptrtoint ptr %l.2 to i64
  ret i64 %p2i.3
}

define internal i64 @Counter_add(ptr %self, i64 %n) {
pre_entry:
  %self.addr = alloca ptr, align 8
  %n.addr = alloca i64, align 8
  %t0.a.1 = alloca ptr, align 8
  store ptr null, ptr %t0.a.1
  %t1.a.6 = alloca i64, align 8
  store i64 0, ptr %t1.a.6
  store ptr %self, ptr %self.addr
  store i64 %n, ptr %n.addr
  br label %entry
entry:
  %l.0 = load ptr, ptr %self.addr
  store ptr %l.0, ptr %t0.a.1
  %l.2 = load ptr, ptr %t0.a.1
  %l.3 = load i64, ptr %n.addr
  %p2i.4 = ptrtoint ptr %l.2 to i64
  %i.5 = add nsw i64 %p2i.4, %l.3
  store i64 %i.5, ptr %t1.a.6
  %l.7 = load i64, ptr %t1.a.6
  ret i64 %l.7
}

define i64 @main() {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0
  %t1.a.3 = alloca {i64}, align 8
  store {i64} zeroinitializer, ptr %t1.a.3
  %rc.5 = alloca {i64}, align 8
  %t3.a.8 = alloca i64, align 8
  store i64 0, ptr %t3.a.8
  %t4.a.12 = alloca i1, align 8
  store i1 0, ptr %t4.a.12
  %t5.a.13 = alloca i64, align 8
  store i64 0, ptr %t5.a.13
  %rc.16 = alloca {i64}, align 8
  %t7.a.19 = alloca i64, align 8
  store i64 0, ptr %t7.a.19
  %t8.a.23 = alloca i1, align 8
  store i1 0, ptr %t8.a.23
  br label %entry
entry:
  store i64 42, ptr %t0.a.0
  %l.1 = load i64, ptr %t0.a.0
  %si.2 = insertvalue {i64} undef, i64 %l.1, 0
  store {i64} %si.2, ptr %t1.a.3
  %l.4 = load {i64}, ptr %t1.a.3
  store {i64} %l.4, ptr %rc.5
  %rv.6 = load ptr, ptr %rc.5
  %c.7 = call i64 @Counter_get(ptr %rv.6)
  store i64 %c.7, ptr %t3.a.8
  %l.9 = load i64, ptr %t3.a.8
  %fp.10 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.11 = call i32 (ptr, ...) @printf(ptr %fp.10, i64 %l.9)
  store i1 0, ptr %t4.a.12
  store i64 8, ptr %t5.a.13
  %l.14 = load {i64}, ptr %t1.a.3
  %l.15 = load i64, ptr %t5.a.13
  store {i64} %l.14, ptr %rc.16
  %rv.17 = load ptr, ptr %rc.16
  %c.18 = call i64 @Counter_add(ptr %rv.17, i64 %l.15)
  store i64 %c.18, ptr %t7.a.19
  %l.20 = load i64, ptr %t7.a.19
  %fp.21 = getelementptr inbounds [6 x i8], ptr @.fmt.0, i64 0, i64 0
  %pf.22 = call i32 (ptr, ...) @printf(ptr %fp.21, i64 %l.20)
  store i1 0, ptr %t8.a.23
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"3.14.0"}
