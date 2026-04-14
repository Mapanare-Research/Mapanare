; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/matmul_naive_stripped.bc'
source_filename = "matmul_naive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"checksum = ", align 8

declare { ptr, i64, i64, i64, i64 } @__mn_list_new(i64)

declare void @__mn_list_push(ptr, ptr)

declare ptr @__mn_list_get(ptr, i64)

declare { ptr, i64 } @__mn_str_from_int(i64)

declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 })

declare void @__mn_str_println({ ptr, i64 })

declare void @__mn_str_free({ ptr, i64 })

declare void @free(ptr)

declare void @__mn_list_free(ptr)

declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %t2.a.3 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.0.gep93 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 0
  store ptr null, ptr %.fca.0.gep93, align 8
  %.fca.1.gep94 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 1
  store i64 0, ptr %.fca.1.gep94, align 8
  %.fca.2.gep95 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 2
  store i64 0, ptr %.fca.2.gep95, align 8
  %.fca.3.gep96 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 3
  store i64 0, ptr %.fca.3.gep96, align 8
  %.fca.4.gep97 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 4
  store i64 0, ptr %.fca.4.gep97, align 8
  %a.a.5 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.0.gep83 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 0
  store ptr null, ptr %.fca.0.gep83, align 8
  %.fca.1.gep84 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 1
  store i64 0, ptr %.fca.1.gep84, align 8
  %.fca.2.gep85 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 2
  store i64 0, ptr %.fca.2.gep85, align 8
  %.fca.3.gep86 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 3
  store i64 0, ptr %.fca.3.gep86, align 8
  %.fca.4.gep87 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 4
  store i64 0, ptr %.fca.4.gep87, align 8
  %t3.a.7 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.0.gep68 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 0
  store ptr null, ptr %.fca.0.gep68, align 8
  %.fca.1.gep69 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 1
  store i64 0, ptr %.fca.1.gep69, align 8
  %.fca.2.gep70 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 2
  store i64 0, ptr %.fca.2.gep70, align 8
  %.fca.3.gep71 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 3
  store i64 0, ptr %.fca.3.gep71, align 8
  %.fca.4.gep72 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 4
  store i64 0, ptr %.fca.4.gep72, align 8
  %b.a.9 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.0.gep58 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 0
  store ptr null, ptr %.fca.0.gep58, align 8
  %.fca.1.gep59 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 1
  store i64 0, ptr %.fca.1.gep59, align 8
  %.fca.2.gep60 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 2
  store i64 0, ptr %.fca.2.gep60, align 8
  %.fca.3.gep61 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 3
  store i64 0, ptr %.fca.3.gep61, align 8
  %.fca.4.gep62 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 4
  store i64 0, ptr %.fca.4.gep62, align 8
  %t4.a.11 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.0.gep43 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 0
  store ptr null, ptr %.fca.0.gep43, align 8
  %.fca.1.gep44 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 1
  store i64 0, ptr %.fca.1.gep44, align 8
  %.fca.2.gep45 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 2
  store i64 0, ptr %.fca.2.gep45, align 8
  %.fca.3.gep46 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 3
  store i64 0, ptr %.fca.3.gep46, align 8
  %.fca.4.gep47 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 4
  store i64 0, ptr %.fca.4.gep47, align 8
  %c.a.13 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 0
  store ptr null, ptr %.fca.0.gep, align 8
  %.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 1
  store i64 0, ptr %.fca.1.gep, align 8
  %.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 2
  store i64 0, ptr %.fca.2.gep, align 8
  %.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 3
  store i64 0, ptr %.fca.3.gep, align 8
  %.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 4
  store i64 0, ptr %.fca.4.gep, align 8
  %ea.38 = alloca i64, align 8
  %ea.56 = alloca i64, align 8
  %ea.60 = alloca i64, align 8
  %lp.82 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.88 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.100 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.111 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.186 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.199 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.230 = alloca { ptr, i64, i64, i64, i64 }, align 8
  br label %entry

entry:                                            ; preds = %pre_entry
  %ln.2 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  %ln.2.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 0
  %ln.2.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 0
  store ptr %ln.2.fca.0.extract, ptr %ln.2.fca.0.gep, align 8
  %ln.2.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 1
  %ln.2.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 1
  store i64 %ln.2.fca.1.extract, ptr %ln.2.fca.1.gep, align 8
  %ln.2.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 2
  %ln.2.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 2
  store i64 %ln.2.fca.2.extract, ptr %ln.2.fca.2.gep, align 8
  %ln.2.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 3
  %ln.2.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 3
  store i64 %ln.2.fca.3.extract, ptr %ln.2.fca.3.gep, align 8
  %ln.2.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 4
  %ln.2.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 4
  store i64 %ln.2.fca.4.extract, ptr %ln.2.fca.4.gep, align 8
  %l.4.fca.0.gep98 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 0
  %l.4.fca.0.load = load ptr, ptr %l.4.fca.0.gep98, align 8
  %l.4.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %l.4.fca.0.load, 0
  %l.4.fca.1.gep99 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 1
  %l.4.fca.1.load = load i64, ptr %l.4.fca.1.gep99, align 8
  %l.4.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.4.fca.0.insert, i64 %l.4.fca.1.load, 1
  %l.4.fca.2.gep100 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 2
  %l.4.fca.2.load = load i64, ptr %l.4.fca.2.gep100, align 8
  %l.4.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.4.fca.1.insert, i64 %l.4.fca.2.load, 2
  %l.4.fca.3.gep101 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 3
  %l.4.fca.3.load = load i64, ptr %l.4.fca.3.gep101, align 8
  %l.4.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.4.fca.2.insert, i64 %l.4.fca.3.load, 3
  %l.4.fca.4.gep102 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 4
  %l.4.fca.4.load = load i64, ptr %l.4.fca.4.gep102, align 8
  %l.4.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.4.fca.3.insert, i64 %l.4.fca.4.load, 4
  %l.4.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.4.fca.4.insert, 0
  %l.4.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 0
  store ptr %l.4.fca.0.extract, ptr %l.4.fca.0.gep, align 8
  %l.4.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.4.fca.4.insert, 1
  %l.4.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 1
  store i64 %l.4.fca.1.extract, ptr %l.4.fca.1.gep, align 8
  %l.4.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.4.fca.4.insert, 2
  %l.4.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 2
  store i64 %l.4.fca.2.extract, ptr %l.4.fca.2.gep, align 8
  %l.4.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.4.fca.4.insert, 3
  %l.4.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 3
  store i64 %l.4.fca.3.extract, ptr %l.4.fca.3.gep, align 8
  %l.4.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.4.fca.4.insert, 4
  %l.4.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 4
  store i64 %l.4.fca.4.extract, ptr %l.4.fca.4.gep, align 8
  %ln.6 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  %ln.6.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 0
  %ln.6.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 0
  store ptr %ln.6.fca.0.extract, ptr %ln.6.fca.0.gep, align 8
  %ln.6.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 1
  %ln.6.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 1
  store i64 %ln.6.fca.1.extract, ptr %ln.6.fca.1.gep, align 8
  %ln.6.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 2
  %ln.6.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 2
  store i64 %ln.6.fca.2.extract, ptr %ln.6.fca.2.gep, align 8
  %ln.6.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 3
  %ln.6.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 3
  store i64 %ln.6.fca.3.extract, ptr %ln.6.fca.3.gep, align 8
  %ln.6.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 4
  %ln.6.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 4
  store i64 %ln.6.fca.4.extract, ptr %ln.6.fca.4.gep, align 8
  %l.8.fca.0.gep73 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 0
  %l.8.fca.0.load = load ptr, ptr %l.8.fca.0.gep73, align 8
  %l.8.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %l.8.fca.0.load, 0
  %l.8.fca.1.gep74 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 1
  %l.8.fca.1.load = load i64, ptr %l.8.fca.1.gep74, align 8
  %l.8.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.8.fca.0.insert, i64 %l.8.fca.1.load, 1
  %l.8.fca.2.gep75 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 2
  %l.8.fca.2.load = load i64, ptr %l.8.fca.2.gep75, align 8
  %l.8.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.8.fca.1.insert, i64 %l.8.fca.2.load, 2
  %l.8.fca.3.gep76 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 3
  %l.8.fca.3.load = load i64, ptr %l.8.fca.3.gep76, align 8
  %l.8.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.8.fca.2.insert, i64 %l.8.fca.3.load, 3
  %l.8.fca.4.gep77 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 4
  %l.8.fca.4.load = load i64, ptr %l.8.fca.4.gep77, align 8
  %l.8.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.8.fca.3.insert, i64 %l.8.fca.4.load, 4
  %l.8.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.8.fca.4.insert, 0
  %l.8.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 0
  store ptr %l.8.fca.0.extract, ptr %l.8.fca.0.gep, align 8
  %l.8.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.8.fca.4.insert, 1
  %l.8.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 1
  store i64 %l.8.fca.1.extract, ptr %l.8.fca.1.gep, align 8
  %l.8.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.8.fca.4.insert, 2
  %l.8.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 2
  store i64 %l.8.fca.2.extract, ptr %l.8.fca.2.gep, align 8
  %l.8.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.8.fca.4.insert, 3
  %l.8.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 3
  store i64 %l.8.fca.3.extract, ptr %l.8.fca.3.gep, align 8
  %l.8.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.8.fca.4.insert, 4
  %l.8.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 4
  store i64 %l.8.fca.4.extract, ptr %l.8.fca.4.gep, align 8
  %ln.10 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  %ln.10.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 0
  %ln.10.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 0
  store ptr %ln.10.fca.0.extract, ptr %ln.10.fca.0.gep, align 8
  %ln.10.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 1
  %ln.10.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 1
  store i64 %ln.10.fca.1.extract, ptr %ln.10.fca.1.gep, align 8
  %ln.10.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 2
  %ln.10.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 2
  store i64 %ln.10.fca.2.extract, ptr %ln.10.fca.2.gep, align 8
  %ln.10.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 3
  %ln.10.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 3
  store i64 %ln.10.fca.3.extract, ptr %ln.10.fca.3.gep, align 8
  %ln.10.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 4
  %ln.10.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 4
  store i64 %ln.10.fca.4.extract, ptr %ln.10.fca.4.gep, align 8
  %l.12.fca.0.gep48 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 0
  %l.12.fca.0.load = load ptr, ptr %l.12.fca.0.gep48, align 8
  %l.12.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %l.12.fca.0.load, 0
  %l.12.fca.1.gep49 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 1
  %l.12.fca.1.load = load i64, ptr %l.12.fca.1.gep49, align 8
  %l.12.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.12.fca.0.insert, i64 %l.12.fca.1.load, 1
  %l.12.fca.2.gep50 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 2
  %l.12.fca.2.load = load i64, ptr %l.12.fca.2.gep50, align 8
  %l.12.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.12.fca.1.insert, i64 %l.12.fca.2.load, 2
  %l.12.fca.3.gep51 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 3
  %l.12.fca.3.load = load i64, ptr %l.12.fca.3.gep51, align 8
  %l.12.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.12.fca.2.insert, i64 %l.12.fca.3.load, 3
  %l.12.fca.4.gep52 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 4
  %l.12.fca.4.load = load i64, ptr %l.12.fca.4.gep52, align 8
  %l.12.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.12.fca.3.insert, i64 %l.12.fca.4.load, 4
  %l.12.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.12.fca.4.insert, 0
  %l.12.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 0
  store ptr %l.12.fca.0.extract, ptr %l.12.fca.0.gep, align 8
  %l.12.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.12.fca.4.insert, 1
  %l.12.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 1
  store i64 %l.12.fca.1.extract, ptr %l.12.fca.1.gep, align 8
  %l.12.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.12.fca.4.insert, 2
  %l.12.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 2
  store i64 %l.12.fca.2.extract, ptr %l.12.fca.2.gep, align 8
  %l.12.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.12.fca.4.insert, 3
  %l.12.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 3
  store i64 %l.12.fca.3.extract, ptr %l.12.fca.3.gep, align 8
  %l.12.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.12.fca.4.insert, 4
  %l.12.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 4
  store i64 %l.12.fca.4.extract, ptr %l.12.fca.4.gep, align 8
  br label %while_header0

while_header0:                                    ; preds = %while_body1, %entry
  %idx.a.16.0 = phi i64 [ 0, %entry ], [ %i.65, %while_body1 ]
  %i.19 = icmp slt i64 %idx.a.16.0, 4096
  br i1 %i.19, label %while_body1, label %while_exit2

while_body1:                                      ; preds = %while_header0
  %i.25 = mul i64 %idx.a.16.0, 3
  %i.30 = add i64 %i.25, 7
  %i.35 = srem i64 %i.30, 100
  store i64 %i.35, ptr %ea.38, align 8
  call void @__mn_list_push(ptr %t2.a.3, ptr %ea.38)
  %ul.39.fca.0.gep103 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 0
  %ul.39.fca.0.load = load ptr, ptr %ul.39.fca.0.gep103, align 8
  %ul.39.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %ul.39.fca.0.load, 0
  %ul.39.fca.1.gep104 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 1
  %ul.39.fca.1.load = load i64, ptr %ul.39.fca.1.gep104, align 8
  %ul.39.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.39.fca.0.insert, i64 %ul.39.fca.1.load, 1
  %ul.39.fca.2.gep105 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 2
  %ul.39.fca.2.load = load i64, ptr %ul.39.fca.2.gep105, align 8
  %ul.39.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.39.fca.1.insert, i64 %ul.39.fca.2.load, 2
  %ul.39.fca.3.gep106 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 3
  %ul.39.fca.3.load = load i64, ptr %ul.39.fca.3.gep106, align 8
  %ul.39.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.39.fca.2.insert, i64 %ul.39.fca.3.load, 3
  %ul.39.fca.4.gep107 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i32 0, i32 4
  %ul.39.fca.4.load = load i64, ptr %ul.39.fca.4.gep107, align 8
  %ul.39.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.39.fca.3.insert, i64 %ul.39.fca.4.load, 4
  %ul.39.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.39.fca.4.insert, 0
  %ul.39.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 0
  store ptr %ul.39.fca.0.extract, ptr %ul.39.fca.0.gep, align 8
  %ul.39.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.39.fca.4.insert, 1
  %ul.39.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 1
  store i64 %ul.39.fca.1.extract, ptr %ul.39.fca.1.gep, align 8
  %ul.39.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.39.fca.4.insert, 2
  %ul.39.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 2
  store i64 %ul.39.fca.2.extract, ptr %ul.39.fca.2.gep, align 8
  %ul.39.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.39.fca.4.insert, 3
  %ul.39.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 3
  store i64 %ul.39.fca.3.extract, ptr %ul.39.fca.3.gep, align 8
  %ul.39.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.39.fca.4.insert, 4
  %ul.39.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 4
  store i64 %ul.39.fca.4.extract, ptr %ul.39.fca.4.gep, align 8
  %i.43 = mul i64 %idx.a.16.0, 5
  %i.48 = add i64 %i.43, 13
  %i.53 = srem i64 %i.48, 100
  store i64 %i.53, ptr %ea.56, align 8
  call void @__mn_list_push(ptr %t3.a.7, ptr %ea.56)
  %ul.57.fca.0.gep78 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 0
  %ul.57.fca.0.load = load ptr, ptr %ul.57.fca.0.gep78, align 8
  %ul.57.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %ul.57.fca.0.load, 0
  %ul.57.fca.1.gep79 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 1
  %ul.57.fca.1.load = load i64, ptr %ul.57.fca.1.gep79, align 8
  %ul.57.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.57.fca.0.insert, i64 %ul.57.fca.1.load, 1
  %ul.57.fca.2.gep80 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 2
  %ul.57.fca.2.load = load i64, ptr %ul.57.fca.2.gep80, align 8
  %ul.57.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.57.fca.1.insert, i64 %ul.57.fca.2.load, 2
  %ul.57.fca.3.gep81 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 3
  %ul.57.fca.3.load = load i64, ptr %ul.57.fca.3.gep81, align 8
  %ul.57.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.57.fca.2.insert, i64 %ul.57.fca.3.load, 3
  %ul.57.fca.4.gep82 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i32 0, i32 4
  %ul.57.fca.4.load = load i64, ptr %ul.57.fca.4.gep82, align 8
  %ul.57.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.57.fca.3.insert, i64 %ul.57.fca.4.load, 4
  %ul.57.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.57.fca.4.insert, 0
  %ul.57.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 0
  store ptr %ul.57.fca.0.extract, ptr %ul.57.fca.0.gep, align 8
  %ul.57.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.57.fca.4.insert, 1
  %ul.57.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 1
  store i64 %ul.57.fca.1.extract, ptr %ul.57.fca.1.gep, align 8
  %ul.57.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.57.fca.4.insert, 2
  %ul.57.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 2
  store i64 %ul.57.fca.2.extract, ptr %ul.57.fca.2.gep, align 8
  %ul.57.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.57.fca.4.insert, 3
  %ul.57.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 3
  store i64 %ul.57.fca.3.extract, ptr %ul.57.fca.3.gep, align 8
  %ul.57.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.57.fca.4.insert, 4
  %ul.57.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 4
  store i64 %ul.57.fca.4.extract, ptr %ul.57.fca.4.gep, align 8
  store i64 0, ptr %ea.60, align 8
  call void @__mn_list_push(ptr %t4.a.11, ptr %ea.60)
  %ul.61.fca.0.gep53 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 0
  %ul.61.fca.0.load = load ptr, ptr %ul.61.fca.0.gep53, align 8
  %ul.61.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %ul.61.fca.0.load, 0
  %ul.61.fca.1.gep54 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 1
  %ul.61.fca.1.load = load i64, ptr %ul.61.fca.1.gep54, align 8
  %ul.61.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.61.fca.0.insert, i64 %ul.61.fca.1.load, 1
  %ul.61.fca.2.gep55 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 2
  %ul.61.fca.2.load = load i64, ptr %ul.61.fca.2.gep55, align 8
  %ul.61.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.61.fca.1.insert, i64 %ul.61.fca.2.load, 2
  %ul.61.fca.3.gep56 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 3
  %ul.61.fca.3.load = load i64, ptr %ul.61.fca.3.gep56, align 8
  %ul.61.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.61.fca.2.insert, i64 %ul.61.fca.3.load, 3
  %ul.61.fca.4.gep57 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i32 0, i32 4
  %ul.61.fca.4.load = load i64, ptr %ul.61.fca.4.gep57, align 8
  %ul.61.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %ul.61.fca.3.insert, i64 %ul.61.fca.4.load, 4
  %ul.61.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.61.fca.4.insert, 0
  %ul.61.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 0
  store ptr %ul.61.fca.0.extract, ptr %ul.61.fca.0.gep, align 8
  %ul.61.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.61.fca.4.insert, 1
  %ul.61.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 1
  store i64 %ul.61.fca.1.extract, ptr %ul.61.fca.1.gep, align 8
  %ul.61.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.61.fca.4.insert, 2
  %ul.61.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 2
  store i64 %ul.61.fca.2.extract, ptr %ul.61.fca.2.gep, align 8
  %ul.61.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.61.fca.4.insert, 3
  %ul.61.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 3
  store i64 %ul.61.fca.3.extract, ptr %ul.61.fca.3.gep, align 8
  %ul.61.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %ul.61.fca.4.insert, 4
  %ul.61.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 4
  store i64 %ul.61.fca.4.extract, ptr %ul.61.fca.4.gep, align 8
  %i.65 = add i64 %idx.a.16.0, 1
  br label %while_header0

while_exit2:                                      ; preds = %while_header0
  br label %while_header3

while_header3:                                    ; preds = %while_exit8, %while_exit2
  %i.a.70.0 = phi i64 [ 0, %while_exit2 ], [ %i.168, %while_exit8 ]
  %i.73 = icmp slt i64 %i.a.70.0, 64
  br i1 %i.73, label %while_body4, label %while_exit5

while_body4:                                      ; preds = %while_header3
  br label %while_header6

while_exit5:                                      ; preds = %while_header3
  %l.80.fca.0.gep18 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 0
  %l.80.fca.0.load = load ptr, ptr %l.80.fca.0.gep18, align 8
  %l.80.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %l.80.fca.0.load, 0
  %l.80.fca.1.gep19 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 1
  %l.80.fca.1.load = load i64, ptr %l.80.fca.1.gep19, align 8
  %l.80.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.80.fca.0.insert, i64 %l.80.fca.1.load, 1
  %l.80.fca.2.gep20 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 2
  %l.80.fca.2.load = load i64, ptr %l.80.fca.2.gep20, align 8
  %l.80.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.80.fca.1.insert, i64 %l.80.fca.2.load, 2
  %l.80.fca.3.gep21 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 3
  %l.80.fca.3.load = load i64, ptr %l.80.fca.3.gep21, align 8
  %l.80.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.80.fca.2.insert, i64 %l.80.fca.3.load, 3
  %l.80.fca.4.gep22 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 4
  %l.80.fca.4.load = load i64, ptr %l.80.fca.4.gep22, align 8
  %l.80.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.80.fca.3.insert, i64 %l.80.fca.4.load, 4
  %l.80.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.80.fca.4.insert, 0
  %l.80.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i32 0, i32 0
  store ptr %l.80.fca.0.extract, ptr %l.80.fca.0.gep, align 8
  %l.80.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.80.fca.4.insert, 1
  %l.80.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i32 0, i32 1
  store i64 %l.80.fca.1.extract, ptr %l.80.fca.1.gep, align 8
  %l.80.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.80.fca.4.insert, 2
  %l.80.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i32 0, i32 2
  store i64 %l.80.fca.2.extract, ptr %l.80.fca.2.gep, align 8
  %l.80.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.80.fca.4.insert, 3
  %l.80.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i32 0, i32 3
  store i64 %l.80.fca.3.extract, ptr %l.80.fca.3.gep, align 8
  %l.80.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.80.fca.4.insert, 4
  %l.80.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i32 0, i32 4
  store i64 %l.80.fca.4.extract, ptr %l.80.fca.4.gep, align 8
  %rt.83 = call ptr @__mn_list_get(ptr %lp.82, i64 0)
  %l.86.fca.0.gep23 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 0
  %l.86.fca.0.load = load ptr, ptr %l.86.fca.0.gep23, align 8
  %l.86.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %l.86.fca.0.load, 0
  %l.86.fca.1.gep24 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 1
  %l.86.fca.1.load = load i64, ptr %l.86.fca.1.gep24, align 8
  %l.86.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.86.fca.0.insert, i64 %l.86.fca.1.load, 1
  %l.86.fca.2.gep25 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 2
  %l.86.fca.2.load = load i64, ptr %l.86.fca.2.gep25, align 8
  %l.86.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.86.fca.1.insert, i64 %l.86.fca.2.load, 2
  %l.86.fca.3.gep26 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 3
  %l.86.fca.3.load = load i64, ptr %l.86.fca.3.gep26, align 8
  %l.86.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.86.fca.2.insert, i64 %l.86.fca.3.load, 3
  %l.86.fca.4.gep27 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 4
  %l.86.fca.4.load = load i64, ptr %l.86.fca.4.gep27, align 8
  %l.86.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.86.fca.3.insert, i64 %l.86.fca.4.load, 4
  %l.86.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.86.fca.4.insert, 0
  %l.86.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i32 0, i32 0
  store ptr %l.86.fca.0.extract, ptr %l.86.fca.0.gep, align 8
  %l.86.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.86.fca.4.insert, 1
  %l.86.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i32 0, i32 1
  store i64 %l.86.fca.1.extract, ptr %l.86.fca.1.gep, align 8
  %l.86.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.86.fca.4.insert, 2
  %l.86.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i32 0, i32 2
  store i64 %l.86.fca.2.extract, ptr %l.86.fca.2.gep, align 8
  %l.86.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.86.fca.4.insert, 3
  %l.86.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i32 0, i32 3
  store i64 %l.86.fca.3.extract, ptr %l.86.fca.3.gep, align 8
  %l.86.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.86.fca.4.insert, 4
  %l.86.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i32 0, i32 4
  store i64 %l.86.fca.4.extract, ptr %l.86.fca.4.gep, align 8
  %rt.89 = call ptr @__mn_list_get(ptr %lp.88, i64 63)
  %p2i.93 = ptrtoint ptr %rt.83 to i64
  %p2i.94 = ptrtoint ptr %rt.89 to i64
  %i.95 = add i64 %p2i.93, %p2i.94
  %l.98.fca.0.gep28 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 0
  %l.98.fca.0.load = load ptr, ptr %l.98.fca.0.gep28, align 8
  %l.98.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %l.98.fca.0.load, 0
  %l.98.fca.1.gep29 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 1
  %l.98.fca.1.load = load i64, ptr %l.98.fca.1.gep29, align 8
  %l.98.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.98.fca.0.insert, i64 %l.98.fca.1.load, 1
  %l.98.fca.2.gep30 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 2
  %l.98.fca.2.load = load i64, ptr %l.98.fca.2.gep30, align 8
  %l.98.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.98.fca.1.insert, i64 %l.98.fca.2.load, 2
  %l.98.fca.3.gep31 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 3
  %l.98.fca.3.load = load i64, ptr %l.98.fca.3.gep31, align 8
  %l.98.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.98.fca.2.insert, i64 %l.98.fca.3.load, 3
  %l.98.fca.4.gep32 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 4
  %l.98.fca.4.load = load i64, ptr %l.98.fca.4.gep32, align 8
  %l.98.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.98.fca.3.insert, i64 %l.98.fca.4.load, 4
  %l.98.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.98.fca.4.insert, 0
  %l.98.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i32 0, i32 0
  store ptr %l.98.fca.0.extract, ptr %l.98.fca.0.gep, align 8
  %l.98.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.98.fca.4.insert, 1
  %l.98.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i32 0, i32 1
  store i64 %l.98.fca.1.extract, ptr %l.98.fca.1.gep, align 8
  %l.98.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.98.fca.4.insert, 2
  %l.98.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i32 0, i32 2
  store i64 %l.98.fca.2.extract, ptr %l.98.fca.2.gep, align 8
  %l.98.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.98.fca.4.insert, 3
  %l.98.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i32 0, i32 3
  store i64 %l.98.fca.3.extract, ptr %l.98.fca.3.gep, align 8
  %l.98.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.98.fca.4.insert, 4
  %l.98.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i32 0, i32 4
  store i64 %l.98.fca.4.extract, ptr %l.98.fca.4.gep, align 8
  %rt.101 = call ptr @__mn_list_get(ptr %lp.100, i64 4032)
  %p2i.105 = ptrtoint ptr %rt.101 to i64
  %i.106 = add i64 %i.95, %p2i.105
  %l.109.fca.0.gep33 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 0
  %l.109.fca.0.load = load ptr, ptr %l.109.fca.0.gep33, align 8
  %l.109.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %l.109.fca.0.load, 0
  %l.109.fca.1.gep34 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 1
  %l.109.fca.1.load = load i64, ptr %l.109.fca.1.gep34, align 8
  %l.109.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.109.fca.0.insert, i64 %l.109.fca.1.load, 1
  %l.109.fca.2.gep35 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 2
  %l.109.fca.2.load = load i64, ptr %l.109.fca.2.gep35, align 8
  %l.109.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.109.fca.1.insert, i64 %l.109.fca.2.load, 2
  %l.109.fca.3.gep36 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 3
  %l.109.fca.3.load = load i64, ptr %l.109.fca.3.gep36, align 8
  %l.109.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.109.fca.2.insert, i64 %l.109.fca.3.load, 3
  %l.109.fca.4.gep37 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 4
  %l.109.fca.4.load = load i64, ptr %l.109.fca.4.gep37, align 8
  %l.109.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.109.fca.3.insert, i64 %l.109.fca.4.load, 4
  %l.109.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.109.fca.4.insert, 0
  %l.109.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i32 0, i32 0
  store ptr %l.109.fca.0.extract, ptr %l.109.fca.0.gep, align 8
  %l.109.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.109.fca.4.insert, 1
  %l.109.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i32 0, i32 1
  store i64 %l.109.fca.1.extract, ptr %l.109.fca.1.gep, align 8
  %l.109.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.109.fca.4.insert, 2
  %l.109.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i32 0, i32 2
  store i64 %l.109.fca.2.extract, ptr %l.109.fca.2.gep, align 8
  %l.109.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.109.fca.4.insert, 3
  %l.109.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i32 0, i32 3
  store i64 %l.109.fca.3.extract, ptr %l.109.fca.3.gep, align 8
  %l.109.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.109.fca.4.insert, 4
  %l.109.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i32 0, i32 4
  store i64 %l.109.fca.4.extract, ptr %l.109.fca.4.gep, align 8
  %rt.112 = call ptr @__mn_list_get(ptr %lp.111, i64 4095)
  %p2i.116 = ptrtoint ptr %rt.112 to i64
  %i.117 = add i64 %i.106, %p2i.116
  %sp.119 = getelementptr inbounds [11 x i8], ptr @.str.0, i64 0, i64 0
  %s.120 = insertvalue { ptr, i64 } undef, ptr %sp.119, 0
  %s.121 = insertvalue { ptr, i64 } %s.120, i64 11, 1
  %s.121.fca.0.extract = extractvalue { ptr, i64 } %s.121, 0
  %s.121.fca.1.extract = extractvalue { ptr, i64 } %s.121, 1
  %rt.124 = call { ptr, i64 } @__mn_str_from_int(i64 %i.117)
  %rt.124.fca.0.extract7 = extractvalue { ptr, i64 } %rt.124, 0
  %rt.124.fca.1.extract8 = extractvalue { ptr, i64 } %rt.124, 1
  %rt.124.fca.0.extract = extractvalue { ptr, i64 } %rt.124, 0
  %rt.124.fca.1.extract = extractvalue { ptr, i64 } %rt.124, 1
  %l.127.fca.0.insert = insertvalue { ptr, i64 } poison, ptr %s.121.fca.0.extract, 0
  %l.127.fca.1.insert = insertvalue { ptr, i64 } %l.127.fca.0.insert, i64 %s.121.fca.1.extract, 1
  %l.128.fca.0.insert = insertvalue { ptr, i64 } poison, ptr %rt.124.fca.0.extract, 0
  %l.128.fca.1.insert = insertvalue { ptr, i64 } %l.128.fca.0.insert, i64 %rt.124.fca.1.extract, 1
  %rt.129 = call { ptr, i64 } @__mn_str_concat({ ptr, i64 } %l.127.fca.1.insert, { ptr, i64 } %l.128.fca.1.insert)
  %rt.129.fca.0.extract5 = extractvalue { ptr, i64 } %rt.129, 0
  %rt.129.fca.1.extract6 = extractvalue { ptr, i64 } %rt.129, 1
  %rt.129.fca.0.extract = extractvalue { ptr, i64 } %rt.129, 0
  %rt.129.fca.1.extract = extractvalue { ptr, i64 } %rt.129, 1
  %l.132.fca.0.insert = insertvalue { ptr, i64 } poison, ptr %rt.129.fca.0.extract, 0
  %l.132.fca.1.insert = insertvalue { ptr, i64 } %l.132.fca.0.insert, i64 %rt.129.fca.1.extract, 1
  call void @__mn_str_println({ ptr, i64 } %l.132.fca.1.insert)
  %drop.s.134.fca.0.insert = insertvalue { ptr, i64 } poison, ptr %rt.124.fca.0.extract7, 0
  %drop.s.134.fca.1.insert = insertvalue { ptr, i64 } %drop.s.134.fca.0.insert, i64 %rt.124.fca.1.extract8, 1
  %drop.p.135 = extractvalue { ptr, i64 } %drop.s.134.fca.1.insert, 0
  %drop.null.136 = icmp eq ptr %drop.p.135, null
  br i1 %drop.null.136, label %drop.skip.137, label %drop.check.137

while_header6:                                    ; preds = %while_exit11, %while_body4
  %j.a.78.0 = phi i64 [ 0, %while_body4 ], [ %i.235, %while_exit11 ]
  %i.156 = icmp slt i64 %j.a.78.0, 64
  br i1 %i.156, label %while_body7, label %while_exit8

while_body7:                                      ; preds = %while_header6
  br label %while_header9

while_exit8:                                      ; preds = %while_header6
  %i.168 = add i64 %i.a.70.0, 1
  br label %while_header3

while_header9:                                    ; preds = %while_body10, %while_body7
  %sum.a.161.0 = phi i64 [ 0, %while_body7 ], [ %i.210, %while_body10 ]
  %k.a.164.0 = phi i64 [ 0, %while_body7 ], [ %i.216, %while_body10 ]
  %i.173 = icmp slt i64 %k.a.164.0, 64
  br i1 %i.173, label %while_body10, label %while_exit11

while_body10:                                     ; preds = %while_header9
  %i.178 = mul i64 %i.a.70.0, 64
  %i.182 = add i64 %i.178, %k.a.164.0
  %l.184.fca.0.gep88 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 0
  %l.184.fca.0.load = load ptr, ptr %l.184.fca.0.gep88, align 8
  %l.184.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %l.184.fca.0.load, 0
  %l.184.fca.1.gep89 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 1
  %l.184.fca.1.load = load i64, ptr %l.184.fca.1.gep89, align 8
  %l.184.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.184.fca.0.insert, i64 %l.184.fca.1.load, 1
  %l.184.fca.2.gep90 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 2
  %l.184.fca.2.load = load i64, ptr %l.184.fca.2.gep90, align 8
  %l.184.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.184.fca.1.insert, i64 %l.184.fca.2.load, 2
  %l.184.fca.3.gep91 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 3
  %l.184.fca.3.load = load i64, ptr %l.184.fca.3.gep91, align 8
  %l.184.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.184.fca.2.insert, i64 %l.184.fca.3.load, 3
  %l.184.fca.4.gep92 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 4
  %l.184.fca.4.load = load i64, ptr %l.184.fca.4.gep92, align 8
  %l.184.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.184.fca.3.insert, i64 %l.184.fca.4.load, 4
  %l.184.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.184.fca.4.insert, 0
  %l.184.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i32 0, i32 0
  store ptr %l.184.fca.0.extract, ptr %l.184.fca.0.gep, align 8
  %l.184.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.184.fca.4.insert, 1
  %l.184.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i32 0, i32 1
  store i64 %l.184.fca.1.extract, ptr %l.184.fca.1.gep, align 8
  %l.184.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.184.fca.4.insert, 2
  %l.184.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i32 0, i32 2
  store i64 %l.184.fca.2.extract, ptr %l.184.fca.2.gep, align 8
  %l.184.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.184.fca.4.insert, 3
  %l.184.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i32 0, i32 3
  store i64 %l.184.fca.3.extract, ptr %l.184.fca.3.gep, align 8
  %l.184.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.184.fca.4.insert, 4
  %l.184.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i32 0, i32 4
  store i64 %l.184.fca.4.extract, ptr %l.184.fca.4.gep, align 8
  %rt.187 = call ptr @__mn_list_get(ptr %lp.186, i64 %i.182)
  %i.191 = mul i64 %k.a.164.0, 64
  %i.195 = add i64 %i.191, %j.a.78.0
  %l.197.fca.0.gep63 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 0
  %l.197.fca.0.load = load ptr, ptr %l.197.fca.0.gep63, align 8
  %l.197.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %l.197.fca.0.load, 0
  %l.197.fca.1.gep64 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 1
  %l.197.fca.1.load = load i64, ptr %l.197.fca.1.gep64, align 8
  %l.197.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.197.fca.0.insert, i64 %l.197.fca.1.load, 1
  %l.197.fca.2.gep65 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 2
  %l.197.fca.2.load = load i64, ptr %l.197.fca.2.gep65, align 8
  %l.197.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.197.fca.1.insert, i64 %l.197.fca.2.load, 2
  %l.197.fca.3.gep66 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 3
  %l.197.fca.3.load = load i64, ptr %l.197.fca.3.gep66, align 8
  %l.197.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.197.fca.2.insert, i64 %l.197.fca.3.load, 3
  %l.197.fca.4.gep67 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 4
  %l.197.fca.4.load = load i64, ptr %l.197.fca.4.gep67, align 8
  %l.197.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.197.fca.3.insert, i64 %l.197.fca.4.load, 4
  %l.197.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.197.fca.4.insert, 0
  %l.197.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i32 0, i32 0
  store ptr %l.197.fca.0.extract, ptr %l.197.fca.0.gep, align 8
  %l.197.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.197.fca.4.insert, 1
  %l.197.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i32 0, i32 1
  store i64 %l.197.fca.1.extract, ptr %l.197.fca.1.gep, align 8
  %l.197.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.197.fca.4.insert, 2
  %l.197.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i32 0, i32 2
  store i64 %l.197.fca.2.extract, ptr %l.197.fca.2.gep, align 8
  %l.197.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.197.fca.4.insert, 3
  %l.197.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i32 0, i32 3
  store i64 %l.197.fca.3.extract, ptr %l.197.fca.3.gep, align 8
  %l.197.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.197.fca.4.insert, 4
  %l.197.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i32 0, i32 4
  store i64 %l.197.fca.4.extract, ptr %l.197.fca.4.gep, align 8
  %rt.200 = call ptr @__mn_list_get(ptr %lp.199, i64 %i.195)
  %p2i.204 = ptrtoint ptr %rt.187 to i64
  %p2i.205 = ptrtoint ptr %rt.200 to i64
  %i.206 = mul i64 %p2i.204, %p2i.205
  %i.210 = add i64 %sum.a.161.0, %i.206
  %i.216 = add i64 %k.a.164.0, 1
  br label %while_header9

while_exit11:                                     ; preds = %while_header9
  %i.221 = mul i64 %i.a.70.0, 64
  %i.225 = add i64 %i.221, %j.a.78.0
  %l.227.fca.0.gep38 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 0
  %l.227.fca.0.load = load ptr, ptr %l.227.fca.0.gep38, align 8
  %l.227.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %l.227.fca.0.load, 0
  %l.227.fca.1.gep39 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 1
  %l.227.fca.1.load = load i64, ptr %l.227.fca.1.gep39, align 8
  %l.227.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.227.fca.0.insert, i64 %l.227.fca.1.load, 1
  %l.227.fca.2.gep40 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 2
  %l.227.fca.2.load = load i64, ptr %l.227.fca.2.gep40, align 8
  %l.227.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.227.fca.1.insert, i64 %l.227.fca.2.load, 2
  %l.227.fca.3.gep41 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 3
  %l.227.fca.3.load = load i64, ptr %l.227.fca.3.gep41, align 8
  %l.227.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.227.fca.2.insert, i64 %l.227.fca.3.load, 3
  %l.227.fca.4.gep42 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 4
  %l.227.fca.4.load = load i64, ptr %l.227.fca.4.gep42, align 8
  %l.227.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.227.fca.3.insert, i64 %l.227.fca.4.load, 4
  %l.227.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.227.fca.4.insert, 0
  %l.227.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i32 0, i32 0
  store ptr %l.227.fca.0.extract, ptr %l.227.fca.0.gep, align 8
  %l.227.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.227.fca.4.insert, 1
  %l.227.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i32 0, i32 1
  store i64 %l.227.fca.1.extract, ptr %l.227.fca.1.gep, align 8
  %l.227.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.227.fca.4.insert, 2
  %l.227.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i32 0, i32 2
  store i64 %l.227.fca.2.extract, ptr %l.227.fca.2.gep, align 8
  %l.227.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.227.fca.4.insert, 3
  %l.227.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i32 0, i32 3
  store i64 %l.227.fca.3.extract, ptr %l.227.fca.3.gep, align 8
  %l.227.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %l.227.fca.4.insert, 4
  %l.227.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i32 0, i32 4
  store i64 %l.227.fca.4.extract, ptr %l.227.fca.4.gep, align 8
  %rt.231 = call ptr @__mn_list_get(ptr %lp.230, i64 %i.225)
  store i64 %sum.a.161.0, ptr %rt.231, align 8
  %i.235 = add i64 %j.a.78.0, 1
  br label %while_header6

drop.check.137:                                   ; preds = %while_exit5
  call void @__mn_str_free({ ptr, i64 } %drop.s.134.fca.1.insert)
  br label %drop.skip.137

drop.skip.137:                                    ; preds = %drop.check.137, %while_exit5
  %drop.s.138.fca.0.insert = insertvalue { ptr, i64 } poison, ptr %rt.129.fca.0.extract5, 0
  %drop.s.138.fca.1.insert = insertvalue { ptr, i64 } %drop.s.138.fca.0.insert, i64 %rt.129.fca.1.extract6, 1
  %drop.p.139 = extractvalue { ptr, i64 } %drop.s.138.fca.1.insert, 0
  %drop.null.140 = icmp eq ptr %drop.p.139, null
  br i1 %drop.null.140, label %drop.skip.141, label %drop.check.141

drop.check.141:                                   ; preds = %drop.skip.137
  call void @__mn_str_free({ ptr, i64 } %drop.s.138.fca.1.insert)
  br label %drop.skip.141

drop.skip.141:                                    ; preds = %drop.check.141, %drop.skip.137
  %drop.lv.142.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 0
  %drop.lv.142.fca.0.load = load ptr, ptr %drop.lv.142.fca.0.gep, align 8
  %drop.lv.142.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %drop.lv.142.fca.0.load, 0
  %drop.lv.142.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 1
  %drop.lv.142.fca.1.load = load i64, ptr %drop.lv.142.fca.1.gep, align 8
  %drop.lv.142.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.142.fca.0.insert, i64 %drop.lv.142.fca.1.load, 1
  %drop.lv.142.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 2
  %drop.lv.142.fca.2.load = load i64, ptr %drop.lv.142.fca.2.gep, align 8
  %drop.lv.142.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.142.fca.1.insert, i64 %drop.lv.142.fca.2.load, 2
  %drop.lv.142.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 3
  %drop.lv.142.fca.3.load = load i64, ptr %drop.lv.142.fca.3.gep, align 8
  %drop.lv.142.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.142.fca.2.insert, i64 %drop.lv.142.fca.3.load, 3
  %drop.lv.142.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i32 0, i32 4
  %drop.lv.142.fca.4.load = load i64, ptr %drop.lv.142.fca.4.gep, align 8
  %drop.lv.142.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.142.fca.3.insert, i64 %drop.lv.142.fca.4.load, 4
  %drop.lp.143 = extractvalue { ptr, i64, i64, i64, i64 } %drop.lv.142.fca.4.insert, 0
  %drop.lnull.144 = icmp eq ptr %drop.lp.143, null
  br i1 %drop.lnull.144, label %drop.lskip.145, label %drop.lcheck.145

drop.lcheck.145:                                  ; preds = %drop.skip.141
  call void @__mn_list_free(ptr %a.a.5)
  br label %drop.lskip.145

drop.lskip.145:                                   ; preds = %drop.lcheck.145, %drop.skip.141
  %drop.lv.146.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 0
  %drop.lv.146.fca.0.load = load ptr, ptr %drop.lv.146.fca.0.gep, align 8
  %drop.lv.146.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %drop.lv.146.fca.0.load, 0
  %drop.lv.146.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 1
  %drop.lv.146.fca.1.load = load i64, ptr %drop.lv.146.fca.1.gep, align 8
  %drop.lv.146.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.146.fca.0.insert, i64 %drop.lv.146.fca.1.load, 1
  %drop.lv.146.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 2
  %drop.lv.146.fca.2.load = load i64, ptr %drop.lv.146.fca.2.gep, align 8
  %drop.lv.146.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.146.fca.1.insert, i64 %drop.lv.146.fca.2.load, 2
  %drop.lv.146.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 3
  %drop.lv.146.fca.3.load = load i64, ptr %drop.lv.146.fca.3.gep, align 8
  %drop.lv.146.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.146.fca.2.insert, i64 %drop.lv.146.fca.3.load, 3
  %drop.lv.146.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i32 0, i32 4
  %drop.lv.146.fca.4.load = load i64, ptr %drop.lv.146.fca.4.gep, align 8
  %drop.lv.146.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.146.fca.3.insert, i64 %drop.lv.146.fca.4.load, 4
  %drop.lp.147 = extractvalue { ptr, i64, i64, i64, i64 } %drop.lv.146.fca.4.insert, 0
  %drop.lnull.148 = icmp eq ptr %drop.lp.147, null
  br i1 %drop.lnull.148, label %drop.lskip.149, label %drop.lcheck.149

drop.lcheck.149:                                  ; preds = %drop.lskip.145
  call void @__mn_list_free(ptr %b.a.9)
  br label %drop.lskip.149

drop.lskip.149:                                   ; preds = %drop.lcheck.149, %drop.lskip.145
  %drop.lv.150.fca.0.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 0
  %drop.lv.150.fca.0.load = load ptr, ptr %drop.lv.150.fca.0.gep, align 8
  %drop.lv.150.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %drop.lv.150.fca.0.load, 0
  %drop.lv.150.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 1
  %drop.lv.150.fca.1.load = load i64, ptr %drop.lv.150.fca.1.gep, align 8
  %drop.lv.150.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.150.fca.0.insert, i64 %drop.lv.150.fca.1.load, 1
  %drop.lv.150.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 2
  %drop.lv.150.fca.2.load = load i64, ptr %drop.lv.150.fca.2.gep, align 8
  %drop.lv.150.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.150.fca.1.insert, i64 %drop.lv.150.fca.2.load, 2
  %drop.lv.150.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 3
  %drop.lv.150.fca.3.load = load i64, ptr %drop.lv.150.fca.3.gep, align 8
  %drop.lv.150.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.150.fca.2.insert, i64 %drop.lv.150.fca.3.load, 3
  %drop.lv.150.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i32 0, i32 4
  %drop.lv.150.fca.4.load = load i64, ptr %drop.lv.150.fca.4.gep, align 8
  %drop.lv.150.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %drop.lv.150.fca.3.insert, i64 %drop.lv.150.fca.4.load, 4
  %drop.lp.151 = extractvalue { ptr, i64, i64, i64, i64 } %drop.lv.150.fca.4.insert, 0
  %drop.lnull.152 = icmp eq ptr %drop.lp.151, null
  br i1 %drop.lnull.152, label %drop.lskip.153, label %drop.lcheck.153

drop.lcheck.153:                                  ; preds = %drop.lskip.149
  call void @__mn_list_free(ptr %c.a.13)
  br label %drop.lskip.153

drop.lskip.153:                                   ; preds = %drop.lcheck.153, %drop.lskip.149
  call void @__mn_intern_destroy()
  ret i64 0
}

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
