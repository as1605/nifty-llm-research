#!/usr/bin/env bash
set -euo pipefail

# Change to repo root (directory of this script)
cd "$(dirname "$0")"

# Optional: activate venv if present
if [[ -d "env" ]]; then
  # shellcheck disable=SC1091
  source env/bin/activate || true
fi

# Ensure python can import from project root
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

# Logs directory
LOG_DIR="data/logs"
mkdir -p "$LOG_DIR"

# Configurable parameters
INDEX="NIFTY SMALLCAP 250"
FILTER_TOP_N=${FILTER_TOP_N:-50}
BASKET_SIZE_K=${BASKET_SIZE_K:-10}
WORKERS=${WORKERS:-10}
PARALLEL=${PARALLEL:-1}    # 1=true, 0=false
FORCE_NSE=${FORCE_NSE:-0}  # 1 to refetch list from NSE
FORCE_LLM=${FORCE_LLM:-0}  # 1 to force LLM analysis
QUIET_REBALANCE=${QUIET_REBALANCE:-1}
LIVE_REBALANCE=${LIVE_REBALANCE:-1}  # Default to LIVE ordering
MIN_ORDER_VALUE=${MIN_ORDER_VALUE:-1000}

# Run ID for log naming
RUN_ID=$(date +"%Y%m%d_%H%M%S")
INDEX_SAFE=${INDEX// /_}

# Log files
ANALYZE1_LOG="$LOG_DIR/${RUN_ID}_${INDEX_SAFE}_analyze_pass1.log"
ANALYZE2_LOG="$LOG_DIR/${RUN_ID}_${INDEX_SAFE}_analyze_pass2.log"
GENERATE_LOG="$LOG_DIR/${RUN_ID}_${INDEX_SAFE}_generate_portfolio.log"
REBALANCE_LOG="$LOG_DIR/${RUN_ID}_${INDEX_SAFE}_rebalance.log"

parallel_flag=()
if [[ "$PARALLEL" == "1" ]]; then
  parallel_flag+=(--parallel -w "$WORKERS")
fi

force_nse_flag=()
if [[ "$FORCE_NSE" == "1" ]]; then
  force_nse_flag+=(--force-nse)
fi

force_llm_flag=()
if [[ "$FORCE_LLM" == "1" ]]; then
  force_llm_flag+=(--force-llm)
fi

quiet_flag=()
if [[ "$QUIET_REBALANCE" == "1" ]]; then
  quiet_flag+=(--quiet)
fi

live_flag=(--dry-run)
if [[ "$LIVE_REBALANCE" == "1" ]]; then
  live_flag=(--live)
fi

# 1st analysis pass
echo "[1/6] Running stock analysis for: $INDEX (1st pass)" >&2
python3 scripts/analyze_stocks.py -i "$INDEX" "${parallel_flag[@]}" "${force_nse_flag[@]}" "${force_llm_flag[@]}" 2>&1 | tee "$ANALYZE1_LOG"

# 2nd analysis pass
echo "[2/6] Running stock analysis for: $INDEX (2nd pass)" >&2
python3 scripts/analyze_stocks.py -i "$INDEX" "${parallel_flag[@]}" "${force_nse_flag[@]}" "${force_llm_flag[@]}" 2>&1 | tee "$ANALYZE2_LOG"

# Generate portfolio
echo "[3/6] Generating portfolio for: $INDEX (N=${FILTER_TOP_N}, K=${BASKET_SIZE_K})" >&2
python3 scripts/generate_portfolio.py -i "$INDEX" -n "$FILTER_TOP_N" -k "$BASKET_SIZE_K" 2>&1 | tee "$GENERATE_LOG"

# Find the latest basket JSON for this index
echo "Locating latest generated basket..." >&2
LATEST_JSON=$(find docs/baskets -maxdepth 1 -type f -name "$(printf '%s__*.json' "$INDEX")" -print0 | xargs -0 ls -t | head -n 1 || true)
if [[ -z "${LATEST_JSON}" ]]; then
  echo "Error: Could not locate latest basket JSON for index '$INDEX'" >&2
  exit 1
fi

echo "Latest basket: ${LATEST_JSON}" >&2

# Commit docs and push
echo "[4/6] Committing docs and pushing to git..." >&2
# Add JSON, MD and index updates
git add docs/baskets/*.json docs/baskets/*.md docs/index.md || true
if ! git diff --cached --quiet; then
  git commit -m "Auto-update: ${INDEX} portfolio $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  git push
else
  echo "No documentation changes to commit." >&2
fi

# Rebalance portfolio
echo "[5/6] Rebalancing portfolio (mode: ${live_flag[*]} | quiet: ${QUIET_REBALANCE})" >&2
python3 scripts/rebalance_portfolio.py "$LATEST_JSON" "${live_flag[@]}" "${quiet_flag[@]}" --min-order-value "$MIN_ORDER_VALUE" 2>&1 | tee "$REBALANCE_LOG"

echo "[6/6] Completed end-to-end flow." >&2
