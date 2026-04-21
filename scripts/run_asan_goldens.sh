#!/usr/bin/env bash
# v4.105.0 Phase 2: run ASan-instrumented mnc-stage1 against 64 goldens.
# Leaks disabled (documented in Phase 1 valgrind report as intentional).
# Record: CLEAN, ASAN_ERROR (with error type), or CRASH_NO_ASAN (compiler exits nonzero but ASan is silent).
set -u
ROOT=${MAPANARE_ROOT:-$(pwd)}
STAGE1=$ROOT/mapanare/self/mnc-stage1-asan
OUTDIR=${ASAN_OUTDIR:-/tmp/v4_105_asan}
TSV=$OUTDIR/asan-summary.tsv

rm -rf $OUTDIR
mkdir -p $OUTDIR

export ASAN_OPTIONS=detect_leaks=0:abort_on_error=0:halt_on_error=1:symbolize=1

echo -e "test\texit\tasan_error_kind\tfirst_frame\tclass" > $TSV

count_total=0 count_clean=0 count_err=0 count_crashnoasan=0

for mn in $ROOT/tests/golden/*.mn; do
  t=$(basename $mn .mn)
  count_total=$((count_total+1))
  OUT=$OUTDIR/${t}.out
  ERR=$OUTDIR/${t}.err

  timeout 60 $STAGE1 $mn > $OUT 2> $ERR
  rc=$?

  # ASan reports go to stderr. Look for the sanitizer banner.
  kind=$(grep -oE "==(ERROR|WARNING): AddressSanitizer: [a-z0-9\-]+" $ERR 2>/dev/null | head -1 | awk -F': ' '{print $NF}')
  frame=$(grep -m1 -E "#0 0x[0-9a-f]+ in [a-zA-Z_]" $ERR 2>/dev/null | awk '{for(i=1;i<=NF;i++) if ($i=="in") {print $(i+1); break}}')
  : ${kind:=none}; : ${frame:=-}

  if [ -n "$kind" ] && [ "$kind" != "none" ]; then
    cls=ASAN_ERROR
    count_err=$((count_err+1))
  elif [ $rc -ne 0 ]; then
    cls=CRASH_NO_ASAN
    count_crashnoasan=$((count_crashnoasan+1))
  else
    cls=CLEAN
    count_clean=$((count_clean+1))
  fi

  echo -e "$t\t$rc\t$kind\t$frame\t$cls" >> $TSV
done

echo
echo "=== ASan golden summary ==="
echo "Total: $count_total  CLEAN: $count_clean  ASAN_ERROR: $count_err  CRASH_NO_ASAN: $count_crashnoasan"
echo "TSV:  $TSV"
