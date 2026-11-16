#!/usr/bin/env bash
# Check a Vercel deployment against the slice spec's targets (§8). Needs `vercel login`.
# Usage: scripts/check_deployment.sh <deployment-url>
set -u
export MSYS_NO_PATHCONV=1  # Git Bash would otherwise rewrite /api/... into a Windows path
url=$1
vc() { npx.cmd --yes vercel@65.16.0 curl "$1" --deployment "$url" -- -s "${@:2}" 2>/dev/null; }
body='{"district_id":"107_jodhpur","business_model":"kusum_a","layout":{"preset_id":"elevated_fixed_3m"},"rotation":[{"season":"kharif","crop_id":"bajra"},{"season":"rabi","crop_id":"wheat"}]}'
sweep() { vc /api/sweep -o /dev/null -w '%{http_code} %{time_total}\n' -X POST -H 'Content-Type: application/json' --data "$body"; }
fail=0
check() { if [ "$2" = 1 ]; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }

h=$(vc /api/health)
check "health: $h" "$(echo "$h" | grep -q '"weather_packs":785' && echo 1)"
t=$(vc /model/107_jodhpur -H 'Accept: text/html')
check "deep link loads the page" "$(echo "$t" | grep -q 'AgriPV Lab' && echo 1)"
read -r code first <<< "$(sweep)"
check "first sweep: HTTP $code, ${first}s (limit 8 s)" "$(awk -v c="$code" -v t="$first" 'BEGIN{print (c==200 && t<=8)}')"
warm=$(for _ in $(seq 20); do sweep; done)
p95=$(echo "$warm" | awk '{print $2}' | sort -n | sed -n 19p)
check "warm sweeps: p95 ${p95}s (limit 1.5 s), all HTTP 200" \
  "$(echo "$warm" | awk -v p="$p95" '$1!=200{bad=1} END{print (!bad && p<=1.5)}')"
exit $fail
