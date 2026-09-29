#!/bin/zsh
# Relay test harness. Fakes the Herdr pane (tests/herdr-stub) and claude (sleep processes). It never
# calls the real herdr and never touches ~/maax. Usage: tests/run.sh [path-to-relay-script]
cd ${0:A:h}/.. || exit 1
SUT=${1:-$PWD/relay.candidate}
STUB=$PWD/tests/herdr-stub
PROD=~/maax/fleet/relay
prod_sum=$(shasum $PROD 2>/dev/null)
pass=0; fail=0; total=0; ORIGPATH=$PATH; typeset -a realcalled wdirs
typeset -a fakepids

t() { print -r -- "--- $1"; }
ok() { total=$((total+1)); if eval "$2"; then pass=$((pass+1)); print "  ok   $1"; else fail=$((fail+1)); print "  FAIL $1"; fi; }

setup() { # setup <mode> [screen kind]
  W=$(mktemp -d); export SCEN=$W/scen; mkdir -p $SCEN $W/handoffs
  print -r -- $1 > $SCEN/mode
  bash -c 'sleep 300 >/dev/null 2>&1 & echo $!; disown' > $SCEN/pid
  [[ $1 == deaf ]] && { kill $(cat $SCEN/pid); bash -c 'trap "" TERM; while :; do sleep 1; done' >/dev/null 2>&1 & echo $! > $SCEN/pid; disown; }
  fakepids+=($(cat $SCEN/pid))
  printf '❯ \n' > $SCEN/screen.txt; printf '\033[2m❯ \033[0m\033[2mTry "fix bug"\033[0m\n' > $SCEN/screen.ansi
  cp $SCEN/screen.txt $SCEN/screen.clean.txt; cp $SCEN/screen.ansi $SCEN/screen.clean.ansi
  HF=$W/handoffs/20260929-0800-test.md
  { print '# HANDOFF'; print '```'; print '▶ PASTE THIS TO START THE NEXT SESSION'; print 'next: do the thing'; print '```'; for i in {1..20}; do print "line $i of state"; done } > $HF
  export HERDR_PANE_ID=w1:p1 RELAY_HERDR=$STUB RELAY_LOG=$W/relay.log RELAY_KICKOFF_FILE=$W/kick \
    RELAY_HANDOFF_DIR=$W/handoffs RELAY_ABORT_MARK=$W/abort RELAY_LOCK=$W/lock RELAY_TIME_SCALE=0.002 \
    RELAY_NO_DETACH=1 RELAY_LAUNCH_CMD='claude-stub' RELAY_MAX_INPUT_TRIES=3
  unset RELAY_DRY_RUN RELAY_AGENT_RE
  mkdir -p $W/bin; print '#!/bin/sh\ntouch '$W'/REAL-HERDR-CALLED' > $W/bin/herdr; chmod +x $W/bin/herdr; export PATH=$W/bin:$ORIGPATH
  realcalled+=($W); wdirs+=($W)
}
run() { $SUT "$@" >$W/out 2>&1; rc=$?; }
sent() { [[ -f $SCEN/sent.log ]] && { grep -c -- "$1" $SCEN/sent.log || true; } || echo 0; }
logs() { cat $W/relay.log 2>/dev/null; }

t "T1 clean /exit relaunches and verifies the new pid"
setup clean; run $HF
ok "exit 0" '[[ $rc == 0 ]]'; ok "log OK with new pid" 'logs | grep -q "OK relayed w1:p1 (old pid $(cat $SCEN/pid), new pid"'
ok "kickoff names the handoff" 'grep -q "Resume $HF and delete it" $W/kick'; ok "no forced exit" '! logs | grep -q forced'
ok "no bare number key sent" '[[ $(sent "SEND-TEXT 1") == 0 ]]'

t "T2 exit dialog: choose option 1 by number, no force"
setup dialog_num; run $HF
ok "sent number 1" '[[ $(sent "SEND-TEXT 1") == 1 ]]'; ok "logged the dialog choice" 'logs | grep -q "exit dialog: chose 1"'
ok "no TERM forced exit" '! logs | grep -q forced'; ok "OK logged" 'logs | grep -q "^.* | OK relayed"'

t "T3 dialog ignores the number: TERM fallback still relays"
setup dialog; run $HF
ok "WARN stalled logged with pane text" 'logs | grep -q "WARN /exit stalled; pane showed:.*Exit and stop tasks"'
ok "forced exit logged" 'logs | grep -q "forced exit of pid $(cat $SCEN/pid)"'; ok "OK logged" 'logs | grep -q "| OK relayed"'

t "T4 claude ignores TERM: KILL backstop"
setup deaf; run $HF
ok "forced exit via KILL" 'logs | grep -q "forced exit"'; ok "OK logged" 'logs | grep -q "| OK relayed"'

t "T5 dim placeholder in the input box is not typed text"
setup clean; run $HF
ok "no WAIT logged" '! logs | grep -q "WAIT input"'

t "T6 typed text holds, then relays when cleared"
setup clean; printf '❯ half a message\n' > $SCEN/screen.ansi; echo 1 > $SCEN/clear_after; run $HF
ok "WAIT logged" 'logs | grep -q "WAIT input box not empty, holding: half a message"'; ok "OK after hold" 'logs | grep -q "| OK relayed"'

t "T7 input never clears: ABORT 2, marker, never /exit"
setup clean; printf '❯ half a message\n' > $SCEN/screen.ansi; run $HF
ok "exit 2" '[[ $rc == 2 ]]'; ok "ABORT logged" 'logs | grep -q "ABORT input box still not empty"'
ok "/exit never sent" '[[ $(sent "/exit") == 0 ]]'; ok "abort marker written" '[[ -s $W/abort ]]'

t "T8 in-session agents running: hold, abort 4, never /exit"
setup clean; printf '❯ \n2 local agents running\n' > $SCEN/screen.txt; run $HF
ok "exit 4" '[[ $rc == 4 ]]'; ok "WAIT agents logged" 'logs | grep -q "WAIT in-session agents running"'
ok "/exit never sent" '[[ $(sent "/exit") == 0 ]]'; ok "marker written" '[[ -s $W/abort ]]'

t "T9 agents finish: relay proceeds"
setup clean; printf '❯ \n2 local agents running\n' > $SCEN/screen.txt; echo 1 > $SCEN/clear_after; run $HF
ok "held then OK" 'logs | grep -q "WAIT in-session agents" && logs | grep -q "| OK relayed"'

t "T10 handoff integrity"
setup clean; run $W/handoffs/missing.md
ok "missing: exit 1, /exit never sent" '[[ $rc == 1 && $(sent "/exit") == 0 ]] && logs | grep -q "ABORT no handoff"'
setup clean; print tiny > $HF; run $HF
ok "tiny: exit 1, /exit never sent" '[[ $rc == 1 && $(sent "/exit") == 0 ]] && logs | grep -q "too small"'
setup clean; { for i in {1..40}; do print "filler line $i"; done } > $HF; run $HF
ok "no kickoff block: exit 1, /exit never sent" '[[ $rc == 1 && $(sent "/exit") == 0 ]] && logs | grep -q "no .PASTE THIS TO START"'
setup clean; cp $HF $W/handoffs/20260929-0900-newer.md; touch -t 209912312359 $W/handoffs/20260929-0900-newer.md; run $HF
ok "not newest: exit 1, /exit never sent, ABORT logged" '[[ $rc == 1 && $(sent "/exit") == 0 ]] && logs | grep -q "ABORT handoff is not the newest"'
ok "not newest: abort marker written" '[[ -s $W/abort ]]'
setup clean; cp $HF $W/handoffs/20260929-0900-newer.md; touch -t 209912312359 $W/handoffs/20260929-0900-newer.md; RELAY_ALLOW_STALE=1 run $HF
ok "RELAY_ALLOW_STALE=1: WARN but relays" 'logs | grep -q "WARN handoff is not the newest" && logs | grep -q "| OK relayed"'

t "T11 dry-run changes nothing"
setup clean; run --dry-run $HF
ok "exit 0" '[[ $rc == 0 ]]'; ok "prints plan" 'grep -q "DRY: checks passed" $W/out'
ok "no sends" '[[ ! -f $SCEN/sent.log ]]'; ok "no real log, no kickoff file, no lock" '[[ ! -f $W/relay.log && ! -f $W/kick && ! -d $W/lock ]]'
ok "fake claude still alive" 'kill -0 $(cat $SCEN/pid)'
setup clean; printf '❯ half a message\n' > $SCEN/screen.ansi; run --dry-run $HF
ok "dry-run reports it would hold, exit 0" '[[ $rc == 0 ]] && grep -q "would hold" $W/out'

t "T12 new claude never appears: ABORT 6 not a false OK"
setup nolaunch; run $HF
ok "exit 6" '[[ $rc == 6 ]]'; ok "no OK line" '! logs | grep -q "| OK relayed"'; ok "marker written" '[[ -s $W/abort ]]'

t "T13 lock"
setup clean; mkdir $W/lock; print $$ > $W/lock/pid; run $HF
ok "live lock: exit 5, /exit never sent" '[[ $rc == 5 && $(sent "/exit") == 0 ]]'
setup clean; mkdir $W/lock; print 999999 > $W/lock/pid; run $HF
ok "stale lock: relays" 'logs | grep -q "| OK relayed"'; ok "lock released" '[[ ! -d $W/lock ]]'

t "T14 pane never idle / no claude process"
setup clean; echo 1 > $SCEN/wait_rc; run $HF
ok "never idle: exit 1, /exit never sent" '[[ $rc == 1 && $(sent "/exit") == 0 ]] && logs | grep -q "ABORT pane never went idle"'
setup clean; touch $SCEN/no_claude; run $HF
ok "no claude in pane: exit 3, /exit never sent" '[[ $rc == 3 && $(sent "/exit") == 0 ]]'

t "T16 agent regex vs real pane captures (9/29 calibration)"
RE=$(grep -m1 '^AGENT_RE=' relay.candidate | sed "s/^AGENT_RE=\${RELAY_AGENT_RE:-'//; s/'}\$//")
ok "running agent row matches" 'grep -Eq -- "$RE" tests/fixtures/pane-agent-running.txt'
ok "finished agent (transcript Agent( line still visible) does not match" '! grep -Eq -- "$RE" tests/fixtures/pane-agent-finished.txt'
ok "footer alone (2 shells / for agents) does not match" '! printf "  bypass permissions on · 2 shells · ← for agents\n  ⏺ main\n" | grep -Eq -- "$RE"'
setup clean; cp tests/fixtures/pane-agent-running.txt $SCEN/screen.txt; run $HF
ok "real running capture holds, abort 4, /exit never sent" '[[ $rc == 4 && $(sent "/exit") == 0 ]]'
setup clean; cp tests/fixtures/pane-agent-finished.txt $SCEN/screen.txt; run $HF
ok "real finished capture relays" 'logs | grep -q "| OK relayed"'

t "T15 isolation: the harness never touched production"
ok "~/maax/fleet/relay unchanged" '[[ "$(shasum $PROD 2>/dev/null)" == "$prod_sum" ]]'
ok "no test ever reached a real herdr on PATH" '! ls ${^realcalled}/REAL-HERDR-CALLED >/dev/null 2>&1'

for p in $fakepids; do kill -KILL $p 2>/dev/null; done
for d in $wdirs; do for f in $d/scen/pid(N) $d/scen/newpid(N); do kill -KILL $(cat $f) 2>/dev/null; done; command rm -r $d; done
print; print "tests: $pass/$total passed"; (( fail == 0 ))
