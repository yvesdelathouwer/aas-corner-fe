#!/bin/bash
# Checkpointed runner: ONE load step per run_aster call; the database is saved after every
# converged step (wd/<job>/base.ok), so a reclaimed/restarted container resumes at the last step.
R=$(cd "$(dirname "$0")" && pwd); JD=$R/jobs; RES=$R/results
export PATH=$HOME/mm/envs/aster/bin:$PATH; RA=$(command -v run_aster)
push(){ (cd $R && git add results && git commit -qm "$1" && git fetch -q origin main && git rebase -q origin/main && git push -q origin HEAD:main) >/dev/null 2>&1 || true; }
for J in ${JOBS:-g150_TV g40_TV g75_TV}; do
  W=$R/wd/$J; mkdir -p $W; C=$RES/$J.curve; touch $C; ln -sf $C $JD/$J.curve
  MESH=$(grep "F mmed" $JD/$J.export | awk '{print $3}'); NSEG=$(ls $JD/${J}_s*.comm | wc -l)
  fails=0
  while :; do
    grep -q "^STOP" $C && break
    K=$(cat $W/next 2>/dev/null || echo 0); [ $K -ge $NSEG ] && break
    S=$(printf "%s/%s_s%02d.comm" $JD $J $K)
    rm -rf $W/run $W/base; mkdir -p $W/run
    { head -4 $JD/$J.export; echo "F comm $S D 1"; echo "F mmed $MESH D 20"; echo "F mess $W/run/mess R 6"
      if [ $K -eq 0 ]; then echo "R base $W/base R 0"; else cp -r $W/base.ok $W/base; echo "R base $W/base DC 0"; fi; } > $W/run/job.export
    n0=$(grep -c ^CURVE $C); T0=$(date +%s)
    echo "$(date -u +%FT%TZ) RUN $J seg $K" >> $RES/camp.progress
    $RA -w $W/run $W/run/job.export > $W/run/log 2>&1; rc=$?
    n1=$(grep -c ^CURVE $C)
    echo "$(date -u +%FT%TZ) END $J seg $K rc=$rc $(( $(date +%s)-T0 ))s last=$(tail -1 $C)" >> $RES/camp.progress
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
echo "$(date -u +%FT%TZ) QUEUE DONE" >> $RES/camp.progress; push "queue done"
