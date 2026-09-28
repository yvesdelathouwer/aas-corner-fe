#!/bin/bash
# AAS corner FE campaign runner — GitHub edition.
# One job at a time, one-step checkpoint segments, resume from BASE_PREC, and after EVERY
# completed load step the curve files are committed and pushed, so a reclaimed VM can never
# lose a finished step.  Re-running this script resumes everything.
R=$(cd "$(dirname "$0")" && pwd); J_DIR=$R/jobs; WD=$R/wd; RES=$R/results
RA=${RA:-$(command -v run_aster || echo $HOME/mm/envs/aster/bin/run_aster)}
mkdir -p $WD $RES; cd $J_DIR
# bind the job files to wherever this repository was cloned (done once, idempotent)
grep -l __ROOT__ $J_DIR/*.comm $J_DIR/*.export $R/genjob.py 2>/dev/null | xargs -r sed -i "s#__ROOT__#$J_DIR#g"
finished(){ grep -q "^STOP peak" $RES/$1.curve 2>/dev/null; }
push(){ (cd $R && git add results && git -c user.name=aas-fe -c user.email=aas-fe@adit.org.il commit -qm "$1" 2>/dev/null && git push -q origin HEAD 2>/dev/null) || true; }
for J in ${JOBS:-v8c75_TV v8c50_TV v8c100_V v8c100_TV v8c75_TV2}; do
  finished $J && continue
  [ -f $RES/$J.done ] && continue
  mkdir -p $WD/$J
  # the comm files write the curve next to themselves: point them at results/
  for attempt in 1 2 3 4 5 6 7 8; do
    finished $J && break
    sed -i '/^STOP solver/d' $RES/$J.curve 2>/dev/null
    ln -sf $RES/$J.curve $J_DIR/$J.curve
    if [ -d $WD/$J/BASE_PREC ] && ls $WD/$J/BASE_PREC/glob.* >/dev/null 2>&1; then
      find $WD/$J -maxdepth 1 -type f -delete 2>/dev/null; rm -rf $WD/$J/REPE_OUT
      cp -f $WD/$J/BASE_PREC/* $WD/$J/
      sed -n '1,4p' $J.export > $J.resume.export
      grep "F comm" $J.export | grep -v "_s00.comm" >> $J.resume.export
      grep -E "F mmed|F mess" $J.export >> $J.resume.export
      EXP=$J.resume.export; MODE=resume
    else
      rm -f $RES/$J.curve; EXP=$J.export; MODE=fresh
    fi
    echo "$(date -u +%FT%TZ) RUN $J ($MODE, attempt $attempt)" >> $RES/camp.progress
    T0=$(date +%s)
    # watcher: push every time the curve grows
    ( last=0; while sleep 60; do n=$(wc -l < $RES/$J.curve 2>/dev/null || echo 0); [ "$n" != "$last" ] && { last=$n; push "$J: $(tail -1 $RES/$J.curve)"; }; done ) & W=$!
    $RA -w $WD/$J $EXP > $RES/$J.$(date -u +%H%M%S).$MODE.log 2>&1; rc=$?
    kill $W 2>/dev/null
    EL=$(( $(date +%s) - T0 ))
    echo "$(date -u +%FT%TZ) END $J rc=$rc ${EL}s last=$(tail -1 $RES/$J.curve 2>/dev/null)" >> $RES/camp.progress
    push "$J: END rc=$rc $(tail -1 $RES/$J.curve 2>/dev/null)"
    if [ "$MODE" = resume ] && [ $rc -ne 0 ] && [ $EL -lt 60 ]; then mv $WD/$J/BASE_PREC $WD/$J/BASE_PREC.bad.$(date +%s); fi
    [ $rc -eq 0 ] && break
  done
  finished $J && rm -rf $WD/$J
  touch $RES/$J.done; push "$J done"
done
echo "$(date -u +%FT%TZ) CAMPAIGN DONE" >> $RES/camp.progress; push "campaign done"
