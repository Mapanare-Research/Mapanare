#!/usr/bin/env bash
# v4.105.0 — run valgrind on mnc-stage1 compiling each golden test.
# For each test:
#   valgrind --leak-check=full --error-exitcode=99 ./mnc-stage1 <test>.mn -o /tmp/<test>.ll
# Classify: CLEAN (no errors), WARNINGS (leaks only), ERRORS (invalid read/write/uninit).
# Writes artifacts/valgrind-summary.tsv and per-test logs to /tmp/v4_105_valgrind/.

set -u
ROOT=${MAPANARE_ROOT:-$(pwd)}
STAGE1=$ROOT/mapanare/self/mnc-stage1
OUTDIR=${VG_OUTDIR:-/tmp/v4_105_valgrind}
TSV=$OUTDIR/valgrind-summary.tsv

rm -rf $OUTDIR
mkdir -p $OUTDIR

if [ ! -x "$STAGE1" ]; then
  echo "error: $STAGE1 not found or not executable" >&2
  exit 2
fi

echo -e "test\trc\texit_code\tdefinitely_lost\tindirectly_lost\tpossibly_lost\tstill_reachable\terror_types\tclass" > $TSV

count_total=0
count_clean=0
count_warnings=0
count_errors=0

for mn in $ROOT/tests/golden/*.mn; do
  t=$(basename $mn .mn)
  count_total=$((count_total+1))
  LOG=$OUTDIR/${t}.log

  # --error-exitcode=99: exit with 99 if valgrind finds errors (not leaks)
  # --errors-for-leak-kinds=none: leaks don't set the error exit code
  # --track-origins=yes: trace uninit origins
  # --show-leak-kinds=all: definitely/indirect/possibly/reachable
  timeout 120 valgrind \
      --error-exitcode=99 \
      --errors-for-leak-kinds=none \
      --leak-check=full \
      --show-leak-kinds=all \
      --track-origins=yes \
      --num-callers=20 \
      $STAGE1 $mn -o $OUTDIR/${t}.ll \
      > $OUTDIR/${t}.stdout 2> $LOG
  rc=$?

  # compiler exit code (distinct from valgrind's exit code if errors found)
  # with --error-exitcode=99, rc is the valgrind error code OR the compiler exit
  if [ $rc -eq 124 ]; then
    echo -e "$t\t$rc\tTIMEOUT\t-\t-\t-\t-\tTIMEOUT\tTIMEOUT" >> $TSV
    count_errors=$((count_errors+1))
    continue
  fi

  # Extract memory summary
  dl=$(grep -E "definitely lost:" $LOG | tail -1 | awk '{print $4}' | tr -d ',')
  il=$(grep -E "indirectly lost:" $LOG | tail -1 | awk '{print $4}' | tr -d ',')
  pl=$(grep -E "possibly lost:" $LOG | tail -1 | awk '{print $4}' | tr -d ',')
  sr=$(grep -E "still reachable:" $LOG | tail -1 | awk '{print $4}' | tr -d ',')
  : ${dl:=0}; : ${il:=0}; : ${pl:=0}; : ${sr:=0}

  # Enumerate distinct error kinds (Invalid read/write, Conditional jump on uninit, etc.)
  err_types=$(grep -oE "(Invalid read of size [0-9]+|Invalid write of size [0-9]+|Use of uninitialised value of size [0-9]+|Conditional jump or move depends on uninitialised value|Mismatched free/delete|Invalid free/delete|Syscall param.*uninitialised)" $LOG | sort -u | tr '\n' '|' | sed 's/|$//')
  : ${err_types:=none}

  # Number of ERROR SUMMARY errors
  nerr=$(grep "ERROR SUMMARY:" $LOG | tail -1 | awk '{print $4}')
  : ${nerr:=0}

  if [ "$nerr" = "0" ] && [ "$dl" = "0" ] && [ "$il" = "0" ]; then
    cls=CLEAN
    count_clean=$((count_clean+1))
  elif [ "$nerr" = "0" ]; then
    # non-zero leaks but no errors
    cls=WARNINGS_ONLY
    count_warnings=$((count_warnings+1))
  else
    cls=ERRORS
    count_errors=$((count_errors+1))
  fi

  # compiler exit code (not rc, which may be 99 from valgrind)
  cexit=$(grep -E "\[CRASH\] Signal" $OUTDIR/${t}.stdout 2>/dev/null | head -1 | awk '{print $3}')
  : ${cexit:=$rc}

  echo -e "$t\t$rc\t$cexit\t$dl\t$il\t$pl\t$sr\t$err_types\t$cls" >> $TSV
done

echo
echo "=== Valgrind summary ==="
echo "Total: $count_total  CLEAN: $count_clean  WARNINGS_ONLY: $count_warnings  ERRORS: $count_errors"
echo "TSV:  $TSV"
echo "Logs: $OUTDIR/*.log"

exit 0
