; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/fib.bc'
source_filename = "fib_recursive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [10 x i8] c"fib(35) = ", align 8

; Function Attrs: nounwind willreturn
declare { ptr, i64 } @__mn_str_from_int(i64) #0

; Function Attrs: nounwind willreturn
declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 }) #0

declare void @__mn_str_println({ ptr, i64 })

; Function Attrs: nounwind willreturn
declare void @__mn_str_free({ ptr, i64 }) #0

; Function Attrs: nounwind willreturn
declare void @free(ptr) #0

declare void @__mn_intern_destroy()

; Function Attrs: nounwind willreturn
define internal i64 @fib(i64 %n) #0 {
pre_entry:
  %n.addr = alloca i64, align 8
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0, align 8
  %t1.a.4 = alloca i1, align 8
  store i1 false, ptr %t1.a.4, align 1
  %t3.a.7 = alloca i64, align 8
  store i64 0, ptr %t3.a.7, align 8
  %t4.a.11 = alloca i64, align 8
  store i64 0, ptr %t4.a.11, align 8
  %t5.a.14 = alloca i64, align 8
  store i64 0, ptr %t5.a.14, align 8
  %t6.a.15 = alloca i64, align 8
  store i64 0, ptr %t6.a.15, align 8
  %t7.a.19 = alloca i64, align 8
  store i64 0, ptr %t7.a.19, align 8
  %t8.a.22 = alloca i64, align 8
  store i64 0, ptr %t8.a.22, align 8
  %t9.a.26 = alloca i64, align 8
  store i64 0, ptr %t9.a.26, align 8
  store i64 %n, ptr %n.addr, align 8
  store i64 1, ptr %t0.a.0, align 8
  %i.3 = icmp sle i64 %n, 1
  store i1 %i.3, ptr %t1.a.4, align 1
  br i1 %i.3, label %if_then0, label %if_else1

if_then0:                                         ; preds = %pre_entry
  ret i64 %n

if_else1:                                         ; preds = %pre_entry
  store i64 1, ptr %t3.a.7, align 8
  %i.10 = sub nsw i64 %n, 1
  store i64 %i.10, ptr %t4.a.11, align 8
  %c.13 = call i64 @fib(i64 %i.10)
  store i64 %c.13, ptr %t5.a.14, align 8
  store i64 2, ptr %t6.a.15, align 8
  %i.18 = sub nsw i64 %n, 2
  store i64 %i.18, ptr %t7.a.19, align 8
  %c.21 = call i64 @fib(i64 %i.18)
  store i64 %c.21, ptr %t8.a.22, align 8
  %i.25 = add nsw i64 %c.13, %c.21
  store i64 %i.25, ptr %t9.a.26, align 8
  ret i64 %i.25
}

; Function Attrs: nounwind willreturn
define i64 @main() #0 {
pre_entry:
  %t0.a.0 = alloca i64, align 8
  store i64 0, ptr %t0.a.0, align 8
  %t1.a.3 = alloca i64, align 8
  store i64 0, ptr %t1.a.3, align 8
  %t2.a.7 = alloca { ptr, i64 }, align 8
  store { ptr, i64 } zeroinitializer, ptr %t2.a.7, align 8
  %str_track.10 = alloca { ptr, i64 }, align 8
  store { ptr, i64 } zeroinitializer, ptr %str_track.10, align 8
  %t3.a.11 = alloca { ptr, i64 }, align 8
  store { ptr, i64 } zeroinitializer, ptr %t3.a.11, align 8
  %str_track.15 = alloca { ptr, i64 }, align 8
  store { ptr, i64 } zeroinitializer, ptr %str_track.15, align 8
  %t4.a.16 = alloca { ptr, i64 }, align 8
  store { ptr, i64 } zeroinitializer, ptr %t4.a.16, align 8
  %t5.a.18 = alloca i1, align 8
  store i1 false, ptr %t5.a.18, align 1
  store i64 35, ptr %t0.a.0, align 8
  %c.2 = call i64 @fib(i64 35)
  store i64 %c.2, ptr %t1.a.3, align 8
  store { ptr, i64 } { ptr @.str.0, i64 10 }, ptr %t2.a.7, align 8
  %rt.9 = call { ptr, i64 } @__mn_str_from_int(i64 %c.2)
  store { ptr, i64 } %rt.9, ptr %str_track.10, align 8
  store { ptr, i64 } %rt.9, ptr %t3.a.11, align 8
  %rt.14 = call { ptr, i64 } @__mn_str_concat({ ptr, i64 } { ptr @.str.0, i64 10 }, { ptr, i64 } %rt.9)
  store { ptr, i64 } %rt.14, ptr %str_track.15, align 8
  store { ptr, i64 } %rt.14, ptr %t4.a.16, align 8
  call void @__mn_str_println({ ptr, i64 } %rt.14)
  store i1 false, ptr %t5.a.18, align 1
  %drop.p.20 = extractvalue { ptr, i64 } %rt.9, 0
  %drop.null.21 = icmp eq ptr %drop.p.20, null
  br i1 %drop.null.21, label %drop.skip.22, label %drop.check.22

drop.check.22:                                    ; preds = %pre_entry
  call void @__mn_str_free({ ptr, i64 } %rt.9)
  br label %drop.skip.22

drop.skip.22:                                     ; preds = %drop.check.22, %pre_entry
  %drop.p.24 = extractvalue { ptr, i64 } %rt.14, 0
  %drop.null.25 = icmp eq ptr %drop.p.24, null
  br i1 %drop.null.25, label %drop.skip.26, label %drop.check.26

drop.check.26:                                    ; preds = %drop.skip.22
  call void @__mn_str_free({ ptr, i64 } %rt.14)
  br label %drop.skip.26

drop.skip.26:                                     ; preds = %drop.check.26, %drop.skip.22
  call void @__mn_intern_destroy()
  ret i64 0
}

attributes #0 = { nounwind willreturn }

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
