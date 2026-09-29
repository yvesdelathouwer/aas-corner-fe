#!/bin/bash
# Line B of the campaign (2026-09-29): same stepper, plus a time budget — a new step is not started when the
# last step's duration (x1.15) does not fit in what remains of BUDGET seconds, so no partial step is wasted at
# the end of an Actions window. Checkpointed runner: ONE load step per run_aster call; the database is saved after every
# converged step (wd/<job>/base.ok), so a reclaimed/restarted container resumes at the last step.
R=$(cd "$(dirname "$0")" && pwd); JD=$R/jobs; RES=$R/results
export PATH=$HOME/mm/envs/aster/bin:$PATH; RA=$(command -v run_aster)
BR=${BRANCH:-main}
T_START=$(date +%s); BUDGET=${BUDGET:-19800}; LAST=${LASTSTEP:-0}
push(){ (cd $R && git add results && git commit -qm "$1" && for i in 1 2 3; do git fetch -q origin $BR && git rebase -q origin/$BR; git push -q origin HEAD:$BR && break; sleep 5; done) >/dev/null 2>&1 || true; }
for J in ${JOBS:-g150_TV g40_TV g75_TV}; do
  W=$R/wd/$J; mkdir -p $W; C=$RES/$J.curve; touch $C; ln -sf $C $JD/$J.curve
  MESH=$(grep "F mmed" $JD/$J.export | awk '{print $3}'); NSEG=$(ls $JD/${J}_s*.comm | wc -l)
  fails=0
  while :; do
    grep -q "^STOP" $C && break
    K=$(cat $W/next 2>/dev/null || echo 0); [ $K -ge $NSEG ] && break
    EL=$(( $(date +%s) - T_START )); if [ $LAST -gt 0 ] && [ $(( EL + LAST*115/100 )) -gt $BUDGET ]; then echo "$(date -u +%FT%TZ) SKIP $J seg $K: ${LAST}s step does not fit in the remaining $(( BUDGET - EL ))s" >> $RES/$J.progress; push "$J: window budget reached before seg $K"; break; fi
    S=$(printf "%s/%s_s%02d.comm" $JD $J $K)
    rm -rf $W/run $W/base; mkdir -p $W/run
    { head -4 $JD/$J.export; echo "F comm $S D 1"; echo "F mmed $MESH D 20"; echo "F mess $W/run/mess R 6"
      if [ $K -eq 0 ]; then echo "R base $W/base R 0"; else cp -r $W/base.ok $W/base; echo "R base $W/base DC 0"; fi; } > $W/run/job.export
    n0=$(grep -c ^CURVE $C); T0=$(date +%s)
    echo "$(date -u +%FT%TZ) RUN $J seg $K" >> $RES/$J.progress
    $RA -w $W/run $W/run/job.export > $W/run/log 2>&1; rc=$?
    n1=$(grep -c ^CURVE $C); LAST=$(( $(date +%s)-T0 ))
    echo "$(date -u +%FT%TZ) END $J seg $K rc=$rc $(( $(date +%s)-T0 ))s last=$(tail -1 $C)" >> $RES/$J.progress
    if [ $n1 -gt $n0 ] && ls $W/base/glob.* >/dev/null 2>&1; then
      rm -rf $W/base.ok; mv $W/base $W/base.ok; echo $((K+1)) > $W/next; fails=0
      push "$J: $(tail -1 $C)"
    elif grep -q "^STOP" $C; then push "$J: $(tail -1 $C)"; break
    else
      fails=$((fails+1)); cp $W/run/log $RES/$J.fail$K.$fails.log
      [ $fails -ge 3 ] && { echo "STOP runner-failed seg $K" >> $C; push "$J failed seg $K"; break; }
    fi
  done
done
echo "$(date -u +%FT%TZ) QUEUE DONE ${JOBS}" >> $RES/queue.progress; push "queue done"
