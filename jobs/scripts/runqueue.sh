#!/bin/bash
# Restart-proof submit runner (Andrew 11/11: run in chunks so a session restart loses at most one application).
# Queue: data/submit_queue.txt, one application id per line. Each run takes up to CHUNK ids from the top,
# submits them one at a time (90 s apart), and removes each id as soon as it finishes. Re-run to continue;
# a restart mid-application leaves that id at the top, and `jobbot recover` never re-clicks submit.
# Usage: scripts/runqueue.sh [CHUNK]      (default 5; 0 = drain the whole queue)
cd "$(dirname "$0")/.." || exit 1
Q=data/submit_queue.txt
CHUNK=${1:-5}
LOCK=data/runqueue.lock
exec 9>"$LOCK"; flock -n 9 || { echo "runqueue already running"; exit 0; }
python3 -m jobbot recover >/dev/null 2>&1
rm -f data/waiting_for_code.txt  # a crashed run can leave a stale marker
n=0
while [ -s "$Q" ]; do
  id=$(head -1 "$Q" | tr -dc '0-9')
  [ -z "$id" ] && { sed -i '1d' "$Q"; continue; }
  rm -f data/verification_code.txt
  echo "START $id $(date -u +%H:%M:%S)" >> data/logs/batch.log
  timeout 1200 python3 -m jobbot submit "$id" --headless --wait-human 480 > "data/logs/submit_$id.json" 2> "data/logs/submit_$id.err"
  echo "END $id $(python3 -c "import json;r=json.load(open('data/logs/submit_$id.json'))[0];print(r['outcome'], '|', '; '.join(r.get('reasons',[]))[:300], r.get('error','')[:150])" 2>&1)" >> data/logs/batch.log
  sed -i "0,/^$id\$/{/^$id\$/d}" "$Q"
  n=$((n+1))
  [ "$CHUNK" -gt 0 ] && [ "$n" -ge "$CHUNK" ] && break
  sleep 90
done
[ -s "$Q" ] && echo "CHUNK DONE ($(wc -l < "$Q") left)" >> data/logs/batch.log || echo "QUEUE EMPTY" >> data/logs/batch.log
