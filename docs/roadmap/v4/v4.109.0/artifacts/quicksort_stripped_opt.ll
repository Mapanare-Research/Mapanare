; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/quicksort_stripped.bc'
source_filename = "quicksort"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"checksum = ", align 8

declare ptr @__mn_list_get(ptr, i64) local_unnamed_addr

declare { ptr, i64, i64, i64, i64 } @__mn_list_new(i64) local_unnamed_addr

declare void @__mn_list_push(ptr, ptr) local_unnamed_addr

declare { ptr, i64 } @__mn_str_from_int(i64) local_unnamed_addr

declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 }) local_unnamed_addr

declare void @__mn_str_println({ ptr, i64 }) local_unnamed_addr

declare void @__mn_str_free({ ptr, i64 }) local_unnamed_addr

declare void @__mn_intern_destroy() local_unnamed_addr

define internal fastcc void @qsort({ ptr, i64, i64, i64, i64 } %arr, i64 %lo, i64 %hi) unnamed_addr {
pre_entry:
  %lp.2.i = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.17.i = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.28.i = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.34.i = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.41.i = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.46.i = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.51.i = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.57.i = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.64.i = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.69.i = alloca { ptr, i64, i64, i64, i64 }, align 8
  %i.2 = icmp slt i64 %lo, %hi
  br i1 %i.2, label %while_body1.lr.ph.i, label %if_merge2

while_body1.lr.ph.i:                              ; preds = %pre_entry
  call void @llvm.lifetime.start.p0(i64 40, ptr nonnull %lp.2.i)
  call void @llvm.lifetime.start.p0(i64 40, ptr nonnull %lp.17.i)
  call void @llvm.lifetime.start.p0(i64 40, ptr nonnull %lp.28.i)
  call void @llvm.lifetime.start.p0(i64 40, ptr nonnull %lp.34.i)
  call void @llvm.lifetime.start.p0(i64 40, ptr nonnull %lp.41.i)
  call void @llvm.lifetime.start.p0(i64 40, ptr nonnull %lp.46.i)
  call void @llvm.lifetime.start.p0(i64 40, ptr nonnull %lp.51.i)
  call void @llvm.lifetime.start.p0(i64 40, ptr nonnull %lp.57.i)
  call void @llvm.lifetime.start.p0(i64 40, ptr nonnull %lp.64.i)
  call void @llvm.lifetime.start.p0(i64 40, ptr nonnull %lp.69.i)
  %arr.fca.0.extract.i = extractvalue { ptr, i64, i64, i64, i64 } %arr, 0
  %arr.fca.1.extract.i = extractvalue { ptr, i64, i64, i64, i64 } %arr, 1
  %arr.fca.2.extract.i = extractvalue { ptr, i64, i64, i64, i64 } %arr, 2
  %arr.fca.3.extract.i = extractvalue { ptr, i64, i64, i64, i64 } %arr, 3
  %arr.fca.4.extract.i = extractvalue { ptr, i64, i64, i64, i64 } %arr, 4
  store ptr %arr.fca.0.extract.i, ptr %lp.2.i, align 8
  %l.0.fca.1.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.2.i, i64 0, i32 1
  store i64 %arr.fca.1.extract.i, ptr %l.0.fca.1.gep.i, align 8
  %l.0.fca.2.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.2.i, i64 0, i32 2
  store i64 %arr.fca.2.extract.i, ptr %l.0.fca.2.gep.i, align 8
  %l.0.fca.3.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.2.i, i64 0, i32 3
  store i64 %arr.fca.3.extract.i, ptr %l.0.fca.3.gep.i, align 8
  %l.0.fca.4.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.2.i, i64 0, i32 4
  store i64 %arr.fca.4.extract.i, ptr %l.0.fca.4.gep.i, align 8
  %rt.3.i = call ptr @__mn_list_get(ptr nonnull %lp.2.i, i64 %hi)
  %el.4.i = load i64, ptr %rt.3.i, align 8
  %l.15.fca.1.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.17.i, i64 0, i32 1
  %l.15.fca.2.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.17.i, i64 0, i32 2
  %l.15.fca.3.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.17.i, i64 0, i32 3
  %l.15.fca.4.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.17.i, i64 0, i32 4
  %l.49.fca.1.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.51.i, i64 0, i32 1
  %l.49.fca.2.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.51.i, i64 0, i32 2
  %l.49.fca.3.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.51.i, i64 0, i32 3
  %l.49.fca.4.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.51.i, i64 0, i32 4
  %l.55.fca.1.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.57.i, i64 0, i32 1
  %l.55.fca.2.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.57.i, i64 0, i32 2
  %l.55.fca.3.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.57.i, i64 0, i32 3
  %l.55.fca.4.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.57.i, i64 0, i32 4
  %l.61.fca.1.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.64.i, i64 0, i32 1
  %l.61.fca.2.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.64.i, i64 0, i32 2
  %l.61.fca.3.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.64.i, i64 0, i32 3
  %l.61.fca.4.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.64.i, i64 0, i32 4
  %l.66.fca.1.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.69.i, i64 0, i32 1
  %l.66.fca.2.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.69.i, i64 0, i32 2
  %l.66.fca.3.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.69.i, i64 0, i32 3
  %l.66.fca.4.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.69.i, i64 0, i32 4
  br label %while_body1.i

while_body1.i:                                    ; preds = %if_merge5.i, %while_body1.lr.ph.i
  %j.a.9.0102.i = phi i64 [ %lo, %while_body1.lr.ph.i ], [ %i.80.i, %if_merge5.i ]
  %i.a.7.0101.i = phi i64 [ %lo, %while_body1.lr.ph.i ], [ %i.a.7.1.i, %if_merge5.i ]
  store ptr %arr.fca.0.extract.i, ptr %lp.17.i, align 8
  store i64 %arr.fca.1.extract.i, ptr %l.15.fca.1.gep.i, align 8
  store i64 %arr.fca.2.extract.i, ptr %l.15.fca.2.gep.i, align 8
  store i64 %arr.fca.3.extract.i, ptr %l.15.fca.3.gep.i, align 8
  store i64 %arr.fca.4.extract.i, ptr %l.15.fca.4.gep.i, align 8
  %rt.18.i = call ptr @__mn_list_get(ptr nonnull %lp.17.i, i64 %j.a.9.0102.i)
  %el.19.i = load i64, ptr %rt.18.i, align 8
  %i.23.i = icmp slt i64 %el.19.i, %el.4.i
  br i1 %i.23.i, label %if_then3.i, label %if_merge5.i

if_then3.i:                                       ; preds = %while_body1.i
  store ptr %arr.fca.0.extract.i, ptr %lp.51.i, align 8
  store i64 %arr.fca.1.extract.i, ptr %l.49.fca.1.gep.i, align 8
  store i64 %arr.fca.2.extract.i, ptr %l.49.fca.2.gep.i, align 8
  store i64 %arr.fca.3.extract.i, ptr %l.49.fca.3.gep.i, align 8
  store i64 %arr.fca.4.extract.i, ptr %l.49.fca.4.gep.i, align 8
  %rt.52.i = call ptr @__mn_list_get(ptr nonnull %lp.51.i, i64 %i.a.7.0101.i)
  %el.53.i = load i64, ptr %rt.52.i, align 8
  store ptr %arr.fca.0.extract.i, ptr %lp.57.i, align 8
  store i64 %arr.fca.1.extract.i, ptr %l.55.fca.1.gep.i, align 8
  store i64 %arr.fca.2.extract.i, ptr %l.55.fca.2.gep.i, align 8
  store i64 %arr.fca.3.extract.i, ptr %l.55.fca.3.gep.i, align 8
  store i64 %arr.fca.4.extract.i, ptr %l.55.fca.4.gep.i, align 8
  %rt.58.i = call ptr @__mn_list_get(ptr nonnull %lp.57.i, i64 %j.a.9.0102.i)
  %el.59.i = load i64, ptr %rt.58.i, align 8
  store ptr %arr.fca.0.extract.i, ptr %lp.64.i, align 8
  store i64 %arr.fca.1.extract.i, ptr %l.61.fca.1.gep.i, align 8
  store i64 %arr.fca.2.extract.i, ptr %l.61.fca.2.gep.i, align 8
  store i64 %arr.fca.3.extract.i, ptr %l.61.fca.3.gep.i, align 8
  store i64 %arr.fca.4.extract.i, ptr %l.61.fca.4.gep.i, align 8
  %rt.65.i = call ptr @__mn_list_get(ptr nonnull %lp.64.i, i64 %i.a.7.0101.i)
  store i64 %el.59.i, ptr %rt.65.i, align 8
  store ptr %arr.fca.0.extract.i, ptr %lp.69.i, align 8
  store i64 %arr.fca.1.extract.i, ptr %l.66.fca.1.gep.i, align 8
  store i64 %arr.fca.2.extract.i, ptr %l.66.fca.2.gep.i, align 8
  store i64 %arr.fca.3.extract.i, ptr %l.66.fca.3.gep.i, align 8
  store i64 %arr.fca.4.extract.i, ptr %l.66.fca.4.gep.i, align 8
  %rt.70.i = call ptr @__mn_list_get(ptr nonnull %lp.69.i, i64 %j.a.9.0102.i)
  store i64 %el.53.i, ptr %rt.70.i, align 8
  %i.74.i = add i64 %i.a.7.0101.i, 1
  br label %if_merge5.i

if_merge5.i:                                      ; preds = %if_then3.i, %while_body1.i
  %i.a.7.1.i = phi i64 [ %i.74.i, %if_then3.i ], [ %i.a.7.0101.i, %while_body1.i ]
  %i.80.i = add i64 %j.a.9.0102.i, 1
  %exitcond.not.i = icmp eq i64 %i.80.i, %hi
  br i1 %exitcond.not.i, label %partition.exit, label %while_body1.i

partition.exit:                                   ; preds = %if_merge5.i
  store ptr %arr.fca.0.extract.i, ptr %lp.28.i, align 8
  %l.26.fca.1.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.28.i, i64 0, i32 1
  store i64 %arr.fca.1.extract.i, ptr %l.26.fca.1.gep.i, align 8
  %l.26.fca.2.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.28.i, i64 0, i32 2
  store i64 %arr.fca.2.extract.i, ptr %l.26.fca.2.gep.i, align 8
  %l.26.fca.3.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.28.i, i64 0, i32 3
  store i64 %arr.fca.3.extract.i, ptr %l.26.fca.3.gep.i, align 8
  %l.26.fca.4.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.28.i, i64 0, i32 4
  store i64 %arr.fca.4.extract.i, ptr %l.26.fca.4.gep.i, align 8
  %rt.29.i = call ptr @__mn_list_get(ptr nonnull %lp.28.i, i64 %i.a.7.1.i)
  %el.30.i = load i64, ptr %rt.29.i, align 8
  store ptr %arr.fca.0.extract.i, ptr %lp.34.i, align 8
  %l.32.fca.1.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.34.i, i64 0, i32 1
  store i64 %arr.fca.1.extract.i, ptr %l.32.fca.1.gep.i, align 8
  %l.32.fca.2.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.34.i, i64 0, i32 2
  store i64 %arr.fca.2.extract.i, ptr %l.32.fca.2.gep.i, align 8
  %l.32.fca.3.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.34.i, i64 0, i32 3
  store i64 %arr.fca.3.extract.i, ptr %l.32.fca.3.gep.i, align 8
  %l.32.fca.4.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.34.i, i64 0, i32 4
  store i64 %arr.fca.4.extract.i, ptr %l.32.fca.4.gep.i, align 8
  %rt.35.i = call ptr @__mn_list_get(ptr nonnull %lp.34.i, i64 %hi)
  %el.36.i = load i64, ptr %rt.35.i, align 8
  store ptr %arr.fca.0.extract.i, ptr %lp.41.i, align 8
  %l.38.fca.1.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.41.i, i64 0, i32 1
  store i64 %arr.fca.1.extract.i, ptr %l.38.fca.1.gep.i, align 8
  %l.38.fca.2.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.41.i, i64 0, i32 2
  store i64 %arr.fca.2.extract.i, ptr %l.38.fca.2.gep.i, align 8
  %l.38.fca.3.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.41.i, i64 0, i32 3
  store i64 %arr.fca.3.extract.i, ptr %l.38.fca.3.gep.i, align 8
  %l.38.fca.4.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.41.i, i64 0, i32 4
  store i64 %arr.fca.4.extract.i, ptr %l.38.fca.4.gep.i, align 8
  %rt.42.i = call ptr @__mn_list_get(ptr nonnull %lp.41.i, i64 %i.a.7.1.i)
  store i64 %el.36.i, ptr %rt.42.i, align 8
  store ptr %arr.fca.0.extract.i, ptr %lp.46.i, align 8
  %l.43.fca.1.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.46.i, i64 0, i32 1
  store i64 %arr.fca.1.extract.i, ptr %l.43.fca.1.gep.i, align 8
  %l.43.fca.2.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.46.i, i64 0, i32 2
  store i64 %arr.fca.2.extract.i, ptr %l.43.fca.2.gep.i, align 8
  %l.43.fca.3.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.46.i, i64 0, i32 3
  store i64 %arr.fca.3.extract.i, ptr %l.43.fca.3.gep.i, align 8
  %l.43.fca.4.gep.i = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.46.i, i64 0, i32 4
  store i64 %arr.fca.4.extract.i, ptr %l.43.fca.4.gep.i, align 8
  %rt.47.i = call ptr @__mn_list_get(ptr nonnull %lp.46.i, i64 %hi)
  store i64 %el.30.i, ptr %rt.47.i, align 8
  call void @llvm.lifetime.end.p0(i64 40, ptr nonnull %lp.2.i)
  call void @llvm.lifetime.end.p0(i64 40, ptr nonnull %lp.17.i)
  call void @llvm.lifetime.end.p0(i64 40, ptr nonnull %lp.28.i)
  call void @llvm.lifetime.end.p0(i64 40, ptr nonnull %lp.34.i)
  call void @llvm.lifetime.end.p0(i64 40, ptr nonnull %lp.41.i)
  call void @llvm.lifetime.end.p0(i64 40, ptr nonnull %lp.46.i)
  call void @llvm.lifetime.end.p0(i64 40, ptr nonnull %lp.51.i)
  call void @llvm.lifetime.end.p0(i64 40, ptr nonnull %lp.57.i)
  call void @llvm.lifetime.end.p0(i64 40, ptr nonnull %lp.64.i)
  call void @llvm.lifetime.end.p0(i64 40, ptr nonnull %lp.69.i)
  %i.13 = add i64 %i.a.7.1.i, -1
  call fastcc void @qsort({ ptr, i64, i64, i64, i64 } %arr, i64 %lo, i64 %i.13)
  %i.22 = add i64 %i.a.7.1.i, 1
  call fastcc void @qsort({ ptr, i64, i64, i64, i64 } %arr, i64 %i.22, i64 %hi)
  br label %if_merge2

if_merge2:                                        ; preds = %pre_entry, %partition.exit
  ret void
}

define noundef i64 @main() local_unnamed_addr {
pre_entry:
  %t0.a.1 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t0.a.1, i64 0, i32 1
  %.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t0.a.1, i64 0, i32 2
  %.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t0.a.1, i64 0, i32 3
  %.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t0.a.1, i64 0, i32 4
  %ea.38 = alloca i64, align 8
  %lp.66 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %ln.0 = tail call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  %ln.0.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.0, 0
  store ptr %ln.0.fca.0.extract, ptr %t0.a.1, align 8
  %ln.0.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.0, 1
  store i64 %ln.0.fca.1.extract, ptr %.fca.1.gep, align 8
  %ln.0.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.0, 2
  store i64 %ln.0.fca.2.extract, ptr %.fca.2.gep, align 8
  %ln.0.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.0, 3
  store i64 %ln.0.fca.3.extract, ptr %.fca.3.gep, align 8
  %ln.0.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.0, 4
  store i64 %ln.0.fca.4.extract, ptr %.fca.4.gep, align 8
  br label %_inl1_entry

_inl1_entry:                                      ; preds = %pre_entry, %_inl1_entry
  %i.a.9.022 = phi i64 [ 0, %pre_entry ], [ %i.43, %_inl1_entry ]
  %seed.a.6.021 = phi i32 [ 42, %pre_entry ], [ %i.29, %_inl1_entry ]
  %i.19 = mul i32 %seed.a.6.021, 1103515245
  %i.24 = add i32 %i.19, 12345
  %i.29 = and i32 %i.24, 2147483647
  %i.3519 = urem i32 %i.29, 100000
  %i.35.zext = zext nneg i32 %i.3519 to i64
  store i64 %i.35.zext, ptr %ea.38, align 8
  call void @__mn_list_push(ptr nonnull %t0.a.1, ptr nonnull %ea.38)
  %i.43 = add nuw nsw i64 %i.a.9.022, 1
  %exitcond.not = icmp eq i64 %i.43, 10000
  br i1 %exitcond.not, label %while_exit2, label %_inl1_entry

while_exit2:                                      ; preds = %_inl1_entry
  %ul.39.fca.1.load.le = load i64, ptr %.fca.1.gep, align 8
  %ul.39.fca.2.load.le = load i64, ptr %.fca.2.gep, align 8
  %ul.39.fca.3.load.le = load i64, ptr %.fca.3.gep, align 8
  %ul.39.fca.4.load.le = load i64, ptr %.fca.4.gep, align 8
  %arr.a.3.sroa.0.0.le = load ptr, ptr %t0.a.1, align 8
  %l.48.fca.0.insert = insertvalue { ptr, i64, i64, i64, i64 } poison, ptr %arr.a.3.sroa.0.0.le, 0
  %l.48.fca.1.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.48.fca.0.insert, i64 %ul.39.fca.1.load.le, 1
  %l.48.fca.2.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.48.fca.1.insert, i64 %ul.39.fca.2.load.le, 2
  %l.48.fca.3.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.48.fca.2.insert, i64 %ul.39.fca.3.load.le, 3
  %l.48.fca.4.insert = insertvalue { ptr, i64, i64, i64, i64 } %l.48.fca.3.insert, i64 %ul.39.fca.4.load.le, 4
  call fastcc void @qsort({ ptr, i64, i64, i64, i64 } %l.48.fca.4.insert, i64 0, i64 9999)
  %l.64.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.66, i64 0, i32 1
  %l.64.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.66, i64 0, i32 2
  %l.64.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.66, i64 0, i32 3
  %l.64.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.66, i64 0, i32 4
  store ptr %arr.a.3.sroa.0.0.le, ptr %lp.66, align 8
  store i64 %ul.39.fca.1.load.le, ptr %l.64.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load.le, ptr %l.64.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load.le, ptr %l.64.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load.le, ptr %l.64.fca.4.gep, align 8
  %rt.67 = call ptr @__mn_list_get(ptr nonnull %lp.66, i64 0)
  %p2i.71 = ptrtoint ptr %rt.67 to i64
  store ptr %arr.a.3.sroa.0.0.le, ptr %lp.66, align 8
  store i64 %ul.39.fca.1.load.le, ptr %l.64.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load.le, ptr %l.64.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load.le, ptr %l.64.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load.le, ptr %l.64.fca.4.gep, align 8
  %rt.67.1 = call ptr @__mn_list_get(ptr nonnull %lp.66, i64 1)
  %p2i.71.1 = ptrtoint ptr %rt.67.1 to i64
  %i.72.1 = add i64 %p2i.71, %p2i.71.1
  store ptr %arr.a.3.sroa.0.0.le, ptr %lp.66, align 8
  store i64 %ul.39.fca.1.load.le, ptr %l.64.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load.le, ptr %l.64.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load.le, ptr %l.64.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load.le, ptr %l.64.fca.4.gep, align 8
  %rt.67.2 = call ptr @__mn_list_get(ptr nonnull %lp.66, i64 2)
  %p2i.71.2 = ptrtoint ptr %rt.67.2 to i64
  %i.72.2 = add i64 %i.72.1, %p2i.71.2
  store ptr %arr.a.3.sroa.0.0.le, ptr %lp.66, align 8
  store i64 %ul.39.fca.1.load.le, ptr %l.64.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load.le, ptr %l.64.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load.le, ptr %l.64.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load.le, ptr %l.64.fca.4.gep, align 8
  %rt.67.3 = call ptr @__mn_list_get(ptr nonnull %lp.66, i64 3)
  %p2i.71.3 = ptrtoint ptr %rt.67.3 to i64
  %i.72.3 = add i64 %i.72.2, %p2i.71.3
  store ptr %arr.a.3.sroa.0.0.le, ptr %lp.66, align 8
  store i64 %ul.39.fca.1.load.le, ptr %l.64.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load.le, ptr %l.64.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load.le, ptr %l.64.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load.le, ptr %l.64.fca.4.gep, align 8
  %rt.67.4 = call ptr @__mn_list_get(ptr nonnull %lp.66, i64 4)
  %p2i.71.4 = ptrtoint ptr %rt.67.4 to i64
  %i.72.4 = add i64 %i.72.3, %p2i.71.4
  store ptr %arr.a.3.sroa.0.0.le, ptr %lp.66, align 8
  store i64 %ul.39.fca.1.load.le, ptr %l.64.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load.le, ptr %l.64.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load.le, ptr %l.64.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load.le, ptr %l.64.fca.4.gep, align 8
  %rt.67.5 = call ptr @__mn_list_get(ptr nonnull %lp.66, i64 5)
  %p2i.71.5 = ptrtoint ptr %rt.67.5 to i64
  %i.72.5 = add i64 %i.72.4, %p2i.71.5
  store ptr %arr.a.3.sroa.0.0.le, ptr %lp.66, align 8
  store i64 %ul.39.fca.1.load.le, ptr %l.64.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load.le, ptr %l.64.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load.le, ptr %l.64.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load.le, ptr %l.64.fca.4.gep, align 8
  %rt.67.6 = call ptr @__mn_list_get(ptr nonnull %lp.66, i64 6)
  %p2i.71.6 = ptrtoint ptr %rt.67.6 to i64
  %i.72.6 = add i64 %i.72.5, %p2i.71.6
  store ptr %arr.a.3.sroa.0.0.le, ptr %lp.66, align 8
  store i64 %ul.39.fca.1.load.le, ptr %l.64.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load.le, ptr %l.64.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load.le, ptr %l.64.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load.le, ptr %l.64.fca.4.gep, align 8
  %rt.67.7 = call ptr @__mn_list_get(ptr nonnull %lp.66, i64 7)
  %p2i.71.7 = ptrtoint ptr %rt.67.7 to i64
  %i.72.7 = add i64 %i.72.6, %p2i.71.7
  store ptr %arr.a.3.sroa.0.0.le, ptr %lp.66, align 8
  store i64 %ul.39.fca.1.load.le, ptr %l.64.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load.le, ptr %l.64.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load.le, ptr %l.64.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load.le, ptr %l.64.fca.4.gep, align 8
  %rt.67.8 = call ptr @__mn_list_get(ptr nonnull %lp.66, i64 8)
  %p2i.71.8 = ptrtoint ptr %rt.67.8 to i64
  %i.72.8 = add i64 %i.72.7, %p2i.71.8
  store ptr %arr.a.3.sroa.0.0.le, ptr %lp.66, align 8
  store i64 %ul.39.fca.1.load.le, ptr %l.64.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load.le, ptr %l.64.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load.le, ptr %l.64.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load.le, ptr %l.64.fca.4.gep, align 8
  %rt.67.9 = call ptr @__mn_list_get(ptr nonnull %lp.66, i64 9)
  %p2i.71.9 = ptrtoint ptr %rt.67.9 to i64
  %i.72.9 = add i64 %i.72.8, %p2i.71.9
  %rt.86 = call { ptr, i64 } @__mn_str_from_int(i64 %i.72.9)
  %rt.86.fca.0.extract3 = extractvalue { ptr, i64 } %rt.86, 0
  %rt.91 = call { ptr, i64 } @__mn_str_concat({ ptr, i64 } { ptr @.str.0, i64 11 }, { ptr, i64 } %rt.86)
  %rt.91.fca.0.extract1 = extractvalue { ptr, i64 } %rt.91, 0
  call void @__mn_str_println({ ptr, i64 } %rt.91)
  %drop.null.98 = icmp eq ptr %rt.86.fca.0.extract3, null
  br i1 %drop.null.98, label %drop.skip.99, label %drop.check.99

drop.check.99:                                    ; preds = %while_exit2
  call void @__mn_str_free({ ptr, i64 } %rt.86)
  br label %drop.skip.99

drop.skip.99:                                     ; preds = %drop.check.99, %while_exit2
  %drop.null.102 = icmp eq ptr %rt.91.fca.0.extract1, null
  br i1 %drop.null.102, label %drop.skip.103, label %drop.check.103

drop.check.103:                                   ; preds = %drop.skip.99
  call void @__mn_str_free({ ptr, i64 } %rt.91)
  br label %drop.skip.103

drop.skip.103:                                    ; preds = %drop.check.103, %drop.skip.99
  call void @__mn_intern_destroy()
  ret i64 0
}

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.start.p0(i64 immarg, ptr nocapture) #0

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.end.p0(i64 immarg, ptr nocapture) #0

attributes #0 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
