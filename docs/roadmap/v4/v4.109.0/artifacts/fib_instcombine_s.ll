; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/fib_stripped.bc'
source_filename = "fib_recursive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [10 x i8] c"fib(35) = ", align 8

declare { ptr, i64 } @__mn_str_from_int(i64)

declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 })

declare void @__mn_str_println({ ptr, i64 })

declare void @__mn_str_free({ ptr, i64 })

declare void @free(ptr)

declare void @__mn_intern_destroy()

define internal i64 @fib(i64 %n) {
pre_entry:
  %n.addr = alloca i64, align 8
  store i64 %n, ptr %n.addr, align 8
  br label %entry

entry:                                            ; preds = %pre_entry
  %l.1 = load i64, ptr %n.addr, align 8
  %i.3 = icmp slt i64 %l.1, 2
  br i1 %i.3, label %if_then0, label %if_else1

if_then0:                                         ; preds = %entry
  %l.6 = load i64, ptr %n.addr, align 8
  ret i64 %l.6

if_else1:                                         ; preds = %entry
  br label %if_merge2

if_merge2:                                        ; preds = %if_else1
  %l.8 = load i64, ptr %n.addr, align 8
  %i.10 = add i64 %l.8, -1
  %c.13 = call i64 @fib(i64 %i.10)
  %i.18 = add i64 %l.8, -2
  %c.21 = call i64 @fib(i64 %i.18)
  %i.25 = add i64 %c.13, %c.21
  ret i64 %i.25
}

define i64 @main() {
pre_entry:
  %t2.a.7 = alloca { ptr, i64 }, align 8
  store ptr null, ptr %t2.a.7, align 8
  %t2.a.7.repack1 = getelementptr inbounds { ptr, i64 }, ptr %t2.a.7, i64 0, i32 1
  store i64 0, ptr %t2.a.7.repack1, align 8
  %str_track.10 = alloca { ptr, i64 }, align 8
  store ptr null, ptr %str_track.10, align 8
  %str_track.10.repack2 = getelementptr inbounds { ptr, i64 }, ptr %str_track.10, i64 0, i32 1
  store i64 0, ptr %str_track.10.repack2, align 8
  %t3.a.11 = alloca { ptr, i64 }, align 8
  store ptr null, ptr %t3.a.11, align 8
  %t3.a.11.repack3 = getelementptr inbounds { ptr, i64 }, ptr %t3.a.11, i64 0, i32 1
  store i64 0, ptr %t3.a.11.repack3, align 8
  %str_track.15 = alloca { ptr, i64 }, align 8
  store ptr null, ptr %str_track.15, align 8
  %str_track.15.repack4 = getelementptr inbounds { ptr, i64 }, ptr %str_track.15, i64 0, i32 1
  store i64 0, ptr %str_track.15.repack4, align 8
  br label %entry

entry:                                            ; preds = %pre_entry
  %c.2 = call i64 @fib(i64 35)
  store ptr @.str.0, ptr %t2.a.7, align 8
  %t2.a.7.repack6 = getelementptr inbounds { ptr, i64 }, ptr %t2.a.7, i64 0, i32 1
  store i64 10, ptr %t2.a.7.repack6, align 8
  %rt.9 = call { ptr, i64 } @__mn_str_from_int(i64 %c.2)
  %rt.9.elt = extractvalue { ptr, i64 } %rt.9, 0
  store ptr %rt.9.elt, ptr %str_track.10, align 8
  %str_track.10.repack7 = getelementptr inbounds { ptr, i64 }, ptr %str_track.10, i64 0, i32 1
  %rt.9.elt8 = extractvalue { ptr, i64 } %rt.9, 1
  store i64 %rt.9.elt8, ptr %str_track.10.repack7, align 8
  %rt.9.elt9 = extractvalue { ptr, i64 } %rt.9, 0
  store ptr %rt.9.elt9, ptr %t3.a.11, align 8
  %t3.a.11.repack10 = getelementptr inbounds { ptr, i64 }, ptr %t3.a.11, i64 0, i32 1
  %rt.9.elt11 = extractvalue { ptr, i64 } %rt.9, 1
  store i64 %rt.9.elt11, ptr %t3.a.11.repack10, align 8
  %l.12.unpack = load ptr, ptr %t2.a.7, align 8
  %0 = insertvalue { ptr, i64 } poison, ptr %l.12.unpack, 0
  %l.12.elt12 = getelementptr inbounds { ptr, i64 }, ptr %t2.a.7, i64 0, i32 1
  %l.12.unpack13 = load i64, ptr %l.12.elt12, align 8
  %l.1214 = insertvalue { ptr, i64 } %0, i64 %l.12.unpack13, 1
  %l.13.unpack = load ptr, ptr %t3.a.11, align 8
  %1 = insertvalue { ptr, i64 } poison, ptr %l.13.unpack, 0
  %l.13.elt15 = getelementptr inbounds { ptr, i64 }, ptr %t3.a.11, i64 0, i32 1
  %l.13.unpack16 = load i64, ptr %l.13.elt15, align 8
  %l.1317 = insertvalue { ptr, i64 } %1, i64 %l.13.unpack16, 1
  %rt.14 = call { ptr, i64 } @__mn_str_concat({ ptr, i64 } %l.1214, { ptr, i64 } %l.1317)
  %rt.14.elt = extractvalue { ptr, i64 } %rt.14, 0
  store ptr %rt.14.elt, ptr %str_track.15, align 8
  %str_track.15.repack18 = getelementptr inbounds { ptr, i64 }, ptr %str_track.15, i64 0, i32 1
  %rt.14.elt19 = extractvalue { ptr, i64 } %rt.14, 1
  store i64 %rt.14.elt19, ptr %str_track.15.repack18, align 8
  call void @__mn_str_println({ ptr, i64 } %rt.14)
  %drop.s.19.unpack = load ptr, ptr %str_track.10, align 8
  %drop.null.21 = icmp eq ptr %drop.s.19.unpack, null
  br i1 %drop.null.21, label %drop.skip.22, label %drop.check.22

drop.check.22:                                    ; preds = %entry
  %2 = insertvalue { ptr, i64 } poison, ptr %drop.s.19.unpack, 0
  %drop.s.19.elt26 = getelementptr inbounds { ptr, i64 }, ptr %str_track.10, i64 0, i32 1
  %drop.s.19.unpack27 = load i64, ptr %drop.s.19.elt26, align 8
  %drop.s.1928 = insertvalue { ptr, i64 } %2, i64 %drop.s.19.unpack27, 1
  call void @__mn_str_free({ ptr, i64 } %drop.s.1928)
  br label %drop.skip.22

drop.skip.22:                                     ; preds = %drop.check.22, %entry
  %drop.s.23.unpack = load ptr, ptr %str_track.15, align 8
  %drop.null.25 = icmp eq ptr %drop.s.23.unpack, null
  br i1 %drop.null.25, label %drop.skip.26, label %drop.check.26

drop.check.26:                                    ; preds = %drop.skip.22
  %3 = insertvalue { ptr, i64 } poison, ptr %drop.s.23.unpack, 0
  %drop.s.23.elt29 = getelementptr inbounds { ptr, i64 }, ptr %str_track.15, i64 0, i32 1
  %drop.s.23.unpack30 = load i64, ptr %drop.s.23.elt29, align 8
  %drop.s.2331 = insertvalue { ptr, i64 } %3, i64 %drop.s.23.unpack30, 1
  call void @__mn_str_free({ ptr, i64 } %drop.s.2331)
  br label %drop.skip.26

drop.skip.26:                                     ; preds = %drop.check.26, %drop.skip.22
  call void @__mn_intern_destroy()
  ret i64 0
}

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
