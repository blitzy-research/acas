#!/usr/bin/env bash
# harness/run_parity.sh -- drive the whole parity protocol for ONE scenario, in
# order, stopping at the first stage that fails. Run `--help' for the options,
# the stage list and the exit codes.
#
# WHY THIS SCRIPT EXISTS. The protocol was ten commands an operator typed in
# order, and nothing enforced either the order or the outcome. Run them against a
# checkout with no seed fixtures and no compiled oracle and every one of them
# "works": the seed exits 75, the compiled run exits 74, the Python run exits 69,
# and the dump, normalise and comparison stages then exit 0 apiece and print
# "identical - 3 table(s) compared, no difference". An EMPTY DIFF IS THE ONLY PASS
# CONDITION the protocol has (AAP section 0.8.5), so the harness reported the
# migration exact having compared two empty captures. Three of the ten stages had
# already failed and no stage looked at what the stage before it had done.
#
# Two defences were added for that, in different places, and they are
# complementary rather than redundant:
#   * the CAPTURE now carries what its run stage claimed, and
#     harness/diff_states.py refuses a pair that does not attest success or that
#     is empty on both sides -- so a hand-driven run still fails closed;
#   * THIS SCRIPT makes the ordering itself mechanical, so the refusal is never
#     reached: a non-zero stage stops the run at that stage, with the stage named.
#
# It is a DRIVER and nothing else. It contains no accounting logic, no SQL, no
# table names and no accounting knowledge. It reads only the scenario basename
# and its ordered operation names: the basename selects the isolated staged-data
# directory, and a multi-menu scenario requires one compiled process per declared
# operation. Every accounting input remains in the scenario file, every stage is
# one of the committed scripts or tools, and every verdict decision is "did that
# exit zero". Restating a table, answer or expected value here would create a
# second source of truth and is forbidden.
#
# Strictly sequential (R-3): no stage is backgrounded, no two stages overlap, and
# exactly one scenario runs at a time.

set -Eeuo pipefail

# Word splitting on newlines and tabs only, so a path containing a space can never
# be split apart. Every expansion below is quoted regardless.
IFS=$'\n\t'

# An unmatched glob expands to nothing rather than to the pattern text.
shopt -s nullglob

# Nothing this script writes is group- or world-readable, matching the four
# sibling scripts.
umask 077

readonly EX_OK=0
readonly EX_USAGE=70          # bad command line
readonly EX_PRECONDITION=71   # environment or scenario assertion
# THERE IS NO "A STAGE FAILED" CODE, DELIBERATELY. The exit status of a failed run
# is the failing stage's OWN status, passed through verbatim. A driver that
# flattened every failure into one code would throw away the thing an operator
# needs: seed.sh's 75 (no fixtures) and 76 (the seed left no rows),
# run_cobol_scenario.sh's 74 (no compiled oracle), run_python_scenario.sh's 69 (a
# behavioural difference) and diff_states.py's 1 (a real difference) each call for
# a different next step, and only 1 and 2 belong to the comparison at all.

ACAS_PARITY_SCENARIO_FILE=''   # the positional argument
ACAS_PARITY_SCENARIO=''        # its basename without the extension
ACAS_PARITY_RUNTIME_DATA=''    # staged COBOL files for this scenario only
ACAS_PARITY_FROM=1             # --from N
ACAS_PARITY_TO=10              # --to N
ACAS_PARITY_DRY_RUN=0          # --dry-run
ACAS_PARITY_KEEP_GOING=0       # --keep-going, which is NOT the default
ACAS_PARITY_SEED_DIR=''        # --seed-dir, forwarded to the two reset stages
ACAS_PARITY_STAGE_INDEX=0      # the stage being run, for the traps
ACAS_PARITY_STAGE_NAME=''
declare -a ACAS_PARITY_SUMMARY=()
declare -a ACAS_PARITY_OPERATIONS=()

# The ten stages, in the one order that makes the verdict mean anything. Each row
# is `<number>:<label>', and the body of each is a case arm in acas_parity_run_stage
# -- the two are kept side by side deliberately, so a stage cannot be listed here
# and quietly not implemented.
readonly -a ACAS_PARITY_STAGES=(
  '1:reset the schema and seed the scenario'
  '2:run the compiled COBOL cycle'
  '3:dump the COBOL state'
  '4:normalise the COBOL dump'
  '5:reset the schema and re-seed the SAME scenario'
  '6:run the migrated Python cycle'
  '7:dump the Python state'
  '8:normalise the Python dump'
  '9:verify both captures are published'
  '10:diff the two normalised trees -- an EMPTY diff is the pass'
)

acas_parity_log() {
  printf '    %s\n' "$*"
}

# IFS is newline and tab, so "${array[*]}" would join a command's words with
# NEWLINES and print a command nobody could copy. Joined with single spaces
# explicitly, for display only -- every real invocation uses "${array[@]}".
acas_parity_join() {
  local out='' word
  for word in "$@"; do
    if [[ -z "$out" ]]; then
      out="$word"
    else
      out="$out $word"
    fi
  done
  printf '%s' "$out"
}

acas_parity_note() {
  printf '    note: %s\n' "$*"
}

acas_parity_stage_banner() {
  printf '\n========================================================================\n'
  printf '==> stage %s/10: %s\n' "$1" "$2"
  printf '========================================================================\n'
}

acas_parity_die() {
  local status="$1"
  shift
  printf '\nFATAL: %s\n' "$1" >&2
  shift || true
  local line
  for line in "$@"; do
    printf '       %s\n' "$line" >&2
  done
  exit "$status"
}

# shellcheck disable=SC2317  # reached only through the ERR trap installed below.
acas_parity_on_err() {
  local status="$1" line="$2" cmd="$3"
  printf '\nFATAL: unexpected failure at %s line %s (status %s).\n' \
    "${BASH_SOURCE[0]}" "$line" "$status" >&2
  printf '       failing command: %s\n' "$cmd" >&2
  if (( ACAS_PARITY_STAGE_INDEX > 0 )); then
    printf '       while driving stage %s/10: %s\n' \
      "$ACAS_PARITY_STAGE_INDEX" "$ACAS_PARITY_STAGE_NAME" >&2
  fi
}
trap 'acas_parity_on_err "$?" "$LINENO" "$BASH_COMMAND"' ERR

acas_parity_usage() {
  cat <<'USAGE'
harness/run_parity.sh <scenario.yaml> [options]

Drives the ten stages of the parity protocol for one scenario, in order, and
ABORTS AT THE FIRST NON-ZERO STAGE. The exit status of a failed run is that
stage's own status, so the diagnosis is not flattened away.

  stage  1  harness/reset_db.sh            <scenario>     schema + seed
  stage  2  harness/run_cobol_scenario.sh  <scenario>     the compiled cycle
  stage  3  harness/dump_tables.py         --side cobol
  stage  4  harness/normalize.py           --side cobol
  stage  5  harness/reset_db.sh            <scenario>     schema + re-seed
  stage  6  harness/run_python_scenario.sh <scenario>     the migrated cycle
  stage  7  harness/dump_tables.py         --side python
  stage  8  harness/normalize.py           --side python
  stage  9  both normalised trees are present and published
  stage 10  harness/diff_states.py         --scenario-file <scenario>

AN EMPTY DIFF FROM STAGE 10 IS THE PASS CONDITION, and the only one (Agent
Action Plan section 0.8.5). Stage 1 and stage 5 are the same command on purpose:
the two cycles must start from the same seed, and the second reset is what makes
the Python side's starting state the COBOL side's starting state rather than the
COBOL side's ENDING state.

Options:
  --from N        start at stage N (default 1). For resuming after a fix.
  --to N          stop after stage N (default 10).
  --seed-dir PATH  where the scenario's declared flat files live, forwarded to BOTH
                  reset stages and through them to harness/seed.sh. It says WHERE,
                  never WHICH: the scenario's seed_files list stays the authority.
                  Needed because a scenario's seed_dir resolves relative to the
                  scenario file, which sits in the READ-ONLY checkout, so a built
                  fixture cannot live there. Build them with
                  harness/build_fixtures.sh, which writes one directory per scenario.
  --keep-going    run the remaining stages after a failure instead of stopping.
                  NOT THE PROTOCOL: it exists for diagnosing a broken harness,
                  and the run's exit status is then the FIRST failing stage's.
                  A verdict produced this way is not evidence (rule R-6).
  --dry-run       print the ten commands and exit without running any of them.
  -h, --help      this text.

Environment: the same contract the five scripts assert -- ACAS_REPO, ACAS_BUILD,
ACAS_DATA, ACAS_OUT, ACAS_DB_* and, for the reset, ACAS_DB_ADMIN_* and
ACAS_RESET_CONSENT. harness/docker-compose.yml supplies all of them; this script
adds none of its own and sets none of them.

Exit codes:
  0        every stage ran and stage 10 found the two states IDENTICAL
  70       usage        71  precondition (environment or scenario)
  <other>  the exit status of the first stage that failed, verbatim. The common
           ones: 75 the scenario's seed fixtures are not staged, 76 the seed
           reported success and left no rows, 74 the compiled oracle is not
           built, 69 a behavioural difference in the Python run, 1 stage 10
           found a real difference, 2 stage 10 could not compare at all.

This script writes nothing itself: every artifact is written by the stage that
produced it, under $ACAS_OUT. It creates no file under $ACAS_REPO, which
harness/docker-compose.yml mounts read-only.
USAGE
}

acas_parity_parse_args() {
  while (( $# )); do
    case "$1" in
      -h|--help)
        acas_parity_usage
        exit "$EX_OK"
        ;;
      --from)
        [[ $# -ge 2 ]] || acas_parity_die "$EX_USAGE" '--from requires a stage number.'
        ACAS_PARITY_FROM="$2"
        shift 2
        ;;
      --to)
        [[ $# -ge 2 ]] || acas_parity_die "$EX_USAGE" '--to requires a stage number.'
        ACAS_PARITY_TO="$2"
        shift 2
        ;;
      --seed-dir)
        [[ $# -ge 2 ]] || acas_parity_die "$EX_USAGE" '--seed-dir requires a path.'
        ACAS_PARITY_SEED_DIR="$2"
        [[ -n "$ACAS_PARITY_SEED_DIR" ]] || acas_parity_die "$EX_USAGE" \
          '--seed-dir was given an empty path.' \
          'If the scenario'"'"'s own seed_dir is wanted, omit the flag.'
        shift 2
        ;;
      --seed-dir=*)
        ACAS_PARITY_SEED_DIR="${1#*=}"
        [[ -n "$ACAS_PARITY_SEED_DIR" ]] || acas_parity_die "$EX_USAGE" \
          '--seed-dir was given an empty path.' \
          'If the scenario'"'"'s own seed_dir is wanted, omit the flag.'
        shift
        ;;
      --keep-going)
        ACAS_PARITY_KEEP_GOING=1
        shift
        ;;
      --dry-run)
        ACAS_PARITY_DRY_RUN=1
        shift
        ;;
      --)
        shift
        break
        ;;
      -*)
        acas_parity_die "$EX_USAGE" "unrecognised option '$1'." \
          'Run with --help for the options and the ten stages.'
        ;;
      *)
        [[ -z "$ACAS_PARITY_SCENARIO_FILE" ]] || acas_parity_die "$EX_USAGE" \
          'exactly one scenario file may be given.' \
          'One scenario runs at a time (R-3); drive a second one with a second' \
          'invocation, after this one has finished.'
        ACAS_PARITY_SCENARIO_FILE="$1"
        shift
        ;;
    esac
  done

  if (( $# )); then
    [[ -z "$ACAS_PARITY_SCENARIO_FILE" ]] || acas_parity_die "$EX_USAGE" \
      'exactly one scenario file may be given.'
    ACAS_PARITY_SCENARIO_FILE="$1"
    shift
  fi

  [[ -n "$ACAS_PARITY_SCENARIO_FILE" ]] || acas_parity_die "$EX_USAGE" \
    'no scenario file was given.' \
    'Usage: harness/run_parity.sh <scenario.yaml>. The eight committed' \
    'scenarios are in harness/scenarios/.'

  local bound
  for bound in "$ACAS_PARITY_FROM" "$ACAS_PARITY_TO"; do
    [[ "$bound" =~ ^[0-9]+$ ]] || acas_parity_die "$EX_USAGE" \
      "--from and --to take a stage number between 1 and 10; got '$bound'."
    (( bound >= 1 && bound <= 10 )) || acas_parity_die "$EX_USAGE" \
      "--from and --to take a stage number between 1 and 10; got '$bound'."
  done
  (( ACAS_PARITY_FROM <= ACAS_PARITY_TO )) || acas_parity_die "$EX_USAGE" \
    "--from ($ACAS_PARITY_FROM) is after --to ($ACAS_PARITY_TO)."
}

acas_parity_assert_environment() {
  local name missing=0
  for name in ACAS_REPO ACAS_DATA ACAS_OUT; do
    if [[ -z "${!name-}" ]]; then
      printf 'FATAL: required environment variable %s is unset or empty.\n' "$name" >&2
      missing=1
    fi
  done
  (( missing == 0 )) || acas_parity_die "$EX_PRECONDITION" \
    'the environment contract is incomplete.' \
    'harness/docker-compose.yml supplies every variable the stages need;' \
    'outside Compose, export them yourself before invoking this script.' \
    'This script asserts only the two it uses itself -- each stage asserts its' \
    'own contract, and duplicating those assertions here would create a second' \
    'place for them to drift.'

  [[ -f "$ACAS_PARITY_SCENARIO_FILE" ]] || acas_parity_die "$EX_PRECONDITION" \
    "the scenario file does not exist: $ACAS_PARITY_SCENARIO_FILE"
  [[ -r "$ACAS_PARITY_SCENARIO_FILE" ]] || acas_parity_die "$EX_PRECONDITION" \
    "the scenario file is not readable: $ACAS_PARITY_SCENARIO_FILE"

  # The scenario NAME is the file's basename without its extension, which is the
  # same derivation every other stage makes. It is not read from inside the file:
  # two derivations of one name is one too many.
  local base="${ACAS_PARITY_SCENARIO_FILE##*/}"
  ACAS_PARITY_SCENARIO="${base%.*}"
  [[ "$ACAS_PARITY_SCENARIO" =~ ^[A-Za-z0-9_-]+$ ]] || acas_parity_die \
    "$EX_PRECONDITION" \
    "the scenario name must be a plain identifier; got '$ACAS_PARITY_SCENARIO'." \
    'It becomes a directory name under ACAS_OUT, so it may hold only letters,' \
    'digits, underscore and hyphen.'

  # reset_db.sh stages each built fixture below `$ACAS_DATA/<scenario>`. The
  # Python test protocol supplies that isolated directory to both run stages;
  # this standalone driver must do the same for both ACAS_DATA and ACAS_LEDGERS
  # or the compiled menu searches the data-volume root for system.dat while
  # reset staged it one directory below.
  ACAS_PARITY_RUNTIME_DATA="${ACAS_DATA%/}/$ACAS_PARITY_SCENARIO"

  local operation_lines
  operation_lines="$(
    "$ACAS_PARITY_PYTHON" - "$ACAS_PARITY_SCENARIO_FILE" <<'PY'
import sys
from pathlib import Path

import yaml

path = Path(sys.argv[1])
definition = yaml.safe_load(path.read_text(encoding="utf-8"))
if not isinstance(definition, dict):
    raise SystemExit(f"{path}: scenario definition is not a YAML mapping")

operations = definition.get("operations")
if operations is None:
    operations = [definition.get("operation")]
if not isinstance(operations, list) or not operations:
    raise SystemExit(f"{path}: scenario declares no operation")
for operation in operations:
    if not isinstance(operation, str) or not operation:
        raise SystemExit(f"{path}: operation names must be non-empty strings")
    print(operation)
PY
  )" || acas_parity_die "$EX_PRECONDITION" \
    "the scenario operation list could not be read from $ACAS_PARITY_SCENARIO_FILE"
  mapfile -t ACAS_PARITY_OPERATIONS <<< "$operation_lines"
  (( ${#ACAS_PARITY_OPERATIONS[@]} > 0 )) || acas_parity_die \
    "$EX_PRECONDITION" \
    "the scenario declares no operations: $ACAS_PARITY_SCENARIO_FILE"

  local script
  for script in reset_db.sh run_cobol_scenario.sh run_python_scenario.sh \
                dump_tables.py normalize.py diff_states.py; do
    [[ -f "$ACAS_PARITY_HARNESS/$script" ]] || acas_parity_die "$EX_PRECONDITION" \
      "$ACAS_PARITY_HARNESS/$script is missing, so the protocol cannot be driven." \
      'This script drives the committed harness and contains no copy of any' \
      'stage it invokes.'
  done
}

# acas_parity_argv <stage-number> Publishes the stage's command in
# ACAS_PARITY_ARGV. One case arm per row of ACAS_PARITY_STAGES, in the same order.
declare -a ACAS_PARITY_ARGV=()
acas_parity_argv() {
  local stage="$1"
  local S="$ACAS_PARITY_SCENARIO_FILE" N="$ACAS_PARITY_SCENARIO"
  local H="$ACAS_PARITY_HARNESS"
  case "$stage" in
    1|5)
      # reset_db.sh applies the frozen schema and then delegates the seed to
      # seed.sh, so one command covers "reset" and "seed". Stage 5 is the same
      # command as stage 1 by design.
      ACAS_PARITY_ARGV=("$H/reset_db.sh")
      # Forwarded to BOTH reset stages from ONE place, so stage 1 and stage 5 cannot
      # diverge -- they are the same command by design, and the two cycles must start
      # from the SAME seed or the diff compares nothing.
      if [[ -n "$ACAS_PARITY_SEED_DIR" ]]; then
        ACAS_PARITY_ARGV+=("--seed-dir" "$ACAS_PARITY_SEED_DIR")
      fi
      ACAS_PARITY_ARGV+=("$S")
      ;;
    2) ACAS_PARITY_ARGV=(
         'env' "ACAS_DATA=$ACAS_PARITY_RUNTIME_DATA"
         "ACAS_LEDGERS=$ACAS_PARITY_RUNTIME_DATA"
         "$H/run_cobol_scenario.sh" '--operation' "${ACAS_PARITY_OPERATIONS[0]}" "$S"
       ) ;;
    3) ACAS_PARITY_ARGV=(
         "$ACAS_PARITY_PYTHON" "$H/dump_tables.py"
         '--scenario' "$N" '--side' 'cobol' '--scenario-file' "$S"
       ) ;;
    4) ACAS_PARITY_ARGV=(
         "$ACAS_PARITY_PYTHON" "$H/normalize.py"
         '--scenario' "$N" '--side' 'cobol'
       ) ;;
    6) ACAS_PARITY_ARGV=(
         'env' "ACAS_DATA=$ACAS_PARITY_RUNTIME_DATA"
         "ACAS_LEDGERS=$ACAS_PARITY_RUNTIME_DATA"
         "$H/run_python_scenario.sh" "$S"
       ) ;;
    7) ACAS_PARITY_ARGV=(
         "$ACAS_PARITY_PYTHON" "$H/dump_tables.py"
         '--scenario' "$N" '--side' 'python' '--scenario-file' "$S"
       ) ;;
    8) ACAS_PARITY_ARGV=(
         "$ACAS_PARITY_PYTHON" "$H/normalize.py"
         '--scenario' "$N" '--side' 'python'
       ) ;;
    9) ACAS_PARITY_ARGV=() ;;   # an in-script check; see acas_parity_run_stage
    10) ACAS_PARITY_ARGV=(
         "$ACAS_PARITY_PYTHON" "$H/diff_states.py"
         '--scenario' "$N" '--scenario-file' "$S"
       ) ;;
    *)
      acas_parity_die "$EX_USAGE" "there is no stage $stage."
      ;;
  esac
}

# Stage 2 may span more than one menu process. `period_end_totals` is the one
# committed example: Sales invoice, Sales cash, Purchase order and Purchase
# payment run in that exact order against one seeded state. Each ordinary runner
# invocation owns one menu process, so drive the declared sequence without a
# reset between operations and preserve operation one's seed fingerprint and
# successful run-status attestation for the later dump. This mirrors
# tests/conftest.py::run_cobol_sequence.
acas_parity_run_cobol_sequence() {
  local run_logs="$ACAS_OUT/run-logs/$ACAS_PARITY_SCENARIO"
  local fingerprint="$run_logs/cobol.seed-fingerprint"
  local status_file="$run_logs/cobol.run-status"
  local saved_fingerprint saved_status
  saved_fingerprint="$(mktemp)"
  saved_status="$(mktemp)"
  local preserved=0 index=0 operation rc=0 log_path
  local -a command=()

  for operation in "${ACAS_PARITY_OPERATIONS[@]}"; do
    index=$((index + 1))
    command=(
      'env' "ACAS_DATA=$ACAS_PARITY_RUNTIME_DATA"
      "ACAS_LEDGERS=$ACAS_PARITY_RUNTIME_DATA"
      "$ACAS_PARITY_HARNESS/run_cobol_scenario.sh"
      '--operation' "$operation"
    )
    if (( index > 1 )); then
      log_path="$run_logs/cobol.$index-$operation.log"
      command+=('--log' "$log_path")
    fi
    command+=("$ACAS_PARITY_SCENARIO_FILE")

    acas_parity_log \
      "operation $index/${#ACAS_PARITY_OPERATIONS[@]}: $(acas_parity_join "${command[@]}")"
    "${command[@]}"
    rc=$?

    if (( index == 1 && rc == 0 )); then
      [[ -f "$fingerprint" && -f "$status_file" ]] || {
        rm -f "$saved_fingerprint" "$saved_status"
        acas_parity_die "$EX_PRECONDITION" \
          'the first oracle operation completed without publishing its seed fingerprint and run-status attestation.'
      }
      cp -- "$fingerprint" "$saved_fingerprint"
      cp -- "$status_file" "$saved_status"
      preserved=1
    fi
    (( rc == 0 )) || break
  done

  if (( preserved )); then
    cp -- "$saved_fingerprint" "$fingerprint"
    cp -- "$saved_status" "$status_file"
    chmod 600 "$fingerprint" "$status_file"
  fi
  rm -f "$saved_fingerprint" "$saved_status"
  return "$rc"
}

# Stage 9 is the one stage with no command of its own: it asserts that stages 4
# and 8 actually published something for stage 10 to read. Without it, a
# `--from 10' resume against a half-finished run reaches the comparison stage and
# is refused there with a message about trees rather than about stages.
acas_parity_assert_published() {
  local side dir manifest missing=0
  for side in cobol python; do
    dir="$ACAS_OUT/$ACAS_PARITY_SCENARIO/$side.normalized"
    manifest="$dir/_manifest.json"
    if [[ -d "$dir" && -f "$manifest" ]]; then
      acas_parity_log "$(printf '%-8s %s' "$side" "$manifest")"
    else
      acas_parity_log "$(printf '%-8s MISSING  %s' "$side" "$dir")"
      missing=1
    fi
  done
  if (( missing )); then
    acas_parity_die "$EX_PRECONDITION" \
      'one or both normalised trees were never published, so there is nothing to compare.' \
      'harness/normalize.py writes _manifest.json LAST, so its absence means' \
      'that stage did not finish for that side. Re-run from the stage that' \
      'produced it -- --from 3 for the COBOL side, --from 7 for the Python side.'
  fi
  acas_parity_log 'both sides are published; the comparison has two complete trees to read'
}

# acas_parity_run_stage <number> <label> Runs one stage and returns its status.
acas_parity_run_stage() {
  local stage="$1" label="$2" rc=0
  ACAS_PARITY_STAGE_INDEX="$stage"
  ACAS_PARITY_STAGE_NAME="$label"

  acas_parity_stage_banner "$stage" "$label"

  if [[ "$stage" == '9' ]]; then
    acas_parity_log 'checking that both normalised trees were published'
    acas_parity_assert_published
    ACAS_PARITY_SUMMARY+=("$(printf '%-3s %-58s %s' "$stage" "$label" 'ok')")
    return 0
  fi

  # `set +e' around exactly one command, so a non-zero status is a value to
  # report rather than an unexpected failure for the ERR trap.
  if [[ "$stage" == '2' ]]; then
    acas_parity_log "staged data: $ACAS_PARITY_RUNTIME_DATA"
    acas_parity_log \
      "declared operations: $(acas_parity_join "${ACAS_PARITY_OPERATIONS[@]}")"
    set +e
    acas_parity_run_cobol_sequence
    rc=$?
    set -e
  else
    acas_parity_argv "$stage"
    acas_parity_log "command: $(acas_parity_join "${ACAS_PARITY_ARGV[@]}")"
    set +e
    "${ACAS_PARITY_ARGV[@]}"
    rc=$?
    set -e
  fi

  if (( rc == 0 )); then
    acas_parity_log "stage $stage: exit 0"
    ACAS_PARITY_SUMMARY+=("$(printf '%-3s %-58s %s' "$stage" "$label" 'ok')")
  else
    acas_parity_log "stage $stage: exit $rc"
    ACAS_PARITY_SUMMARY+=("$(printf '%-3s %-58s exit %s' "$stage" "$label" "$rc")")
  fi
  return "$rc"
}

acas_parity_report() {
  local first_failure="$1"
  printf '\n========================================================================\n'
  printf '==> harness/run_parity.sh summary -- scenario %s\n' "$ACAS_PARITY_SCENARIO"
  printf '========================================================================\n'
  local row
  for row in ${ACAS_PARITY_SUMMARY[@]+"${ACAS_PARITY_SUMMARY[@]}"}; do
    printf '    %s\n' "$row"
  done
  if (( first_failure == 0 )); then
    printf '\n    VERDICT: the two states are IDENTICAL -- an empty diff, which is the\n'
    printf '             pass condition and the only one (AAP section 0.8.5).\n'
  else
    printf '\n    VERDICT: NO PARITY CLAIM. The run stopped at the first failing stage,\n'
    printf '             so no later stage rendered a verdict on evidence an earlier one\n'
    printf '             never produced.\n'
  fi
}

acas_parity_main() {
  # ACAS_REPO is asserted before it is used to locate the harness, so a missing
  # variable is reported as itself rather than as a missing script.
  ACAS_PARITY_HARNESS="${ACAS_REPO:-}/harness"
  ACAS_PARITY_PYTHON="${ACAS_PARITY_PYTHON:-python3}"

  acas_parity_parse_args "$@"
  acas_parity_assert_environment
  ACAS_PARITY_HARNESS="$ACAS_REPO/harness"

  printf 'harness/run_parity.sh -- the ten-stage parity protocol, in order, stopping at\n'
  printf 'the first failure. An EMPTY DIFF FROM STAGE 10 IS THE PASS CONDITION, and the\n'
  printf 'only one (Agent Action Plan section 0.8.5).\n\n'
  acas_parity_log "scenario file = $ACAS_PARITY_SCENARIO_FILE"
  acas_parity_log "scenario      = $ACAS_PARITY_SCENARIO"
  acas_parity_log "stages        = $ACAS_PARITY_FROM through $ACAS_PARITY_TO"
  acas_parity_log "python        = $ACAS_PARITY_PYTHON"
  acas_parity_log "ACAS_OUT      = $ACAS_OUT"
  if (( ACAS_PARITY_KEEP_GOING )); then
    acas_parity_note '--keep-going: a failure will NOT stop the run, and the verdict is not evidence (R-6)'
  fi

  local entry stage label rc first_failure=0
  for entry in "${ACAS_PARITY_STAGES[@]}"; do
    stage="${entry%%:*}"
    label="${entry#*:}"
    if (( stage < ACAS_PARITY_FROM || stage > ACAS_PARITY_TO )); then
      continue
    fi

    if (( ACAS_PARITY_DRY_RUN )); then
      if [[ "$stage" == '2' ]]; then
        local operation
        for operation in "${ACAS_PARITY_OPERATIONS[@]}"; do
          printf 'stage %-3s env ACAS_DATA=%s ACAS_LEDGERS=%s %s/run_cobol_scenario.sh --operation %s %s\n' \
            "$stage" "$ACAS_PARITY_RUNTIME_DATA" "$ACAS_PARITY_RUNTIME_DATA" "$ACAS_PARITY_HARNESS" \
            "$operation" "$ACAS_PARITY_SCENARIO_FILE"
        done
        continue
      fi
      acas_parity_argv "$stage"
      if (( ${#ACAS_PARITY_ARGV[@]} == 0 )); then
        printf 'stage %-3s %-58s (an in-script check, no command)\n' "$stage" "$label"
      else
        printf 'stage %-3s %s\n' "$stage" \
          "$(acas_parity_join "${ACAS_PARITY_ARGV[@]}")"
      fi
      continue
    fi

    rc=0
    acas_parity_run_stage "$stage" "$label" || rc=$?
    if (( rc != 0 )); then
      if (( first_failure == 0 )); then
        first_failure="$rc"
      fi
      if (( ! ACAS_PARITY_KEEP_GOING )); then
        acas_parity_report "$first_failure"
        printf '\nharness/run_parity.sh: stage %s/10 (%s) exited %s, so the run stops here.\n' \
          "$stage" "$label" "$rc" >&2
        printf 'The remaining stages are NOT run: a later stage would otherwise render a\n' >&2
        printf 'verdict on evidence this stage never produced, and an empty diff is the\n' >&2
        printf 'pass condition. Fix the cause, then resume with --from %s.\n' "$stage" >&2
        exit "$rc"
      fi
    fi
  done

  if (( ACAS_PARITY_DRY_RUN )); then
    printf '\nharness/run_parity.sh dry run complete: nothing was executed.\n'
    exit "$EX_OK"
  fi

  acas_parity_report "$first_failure"
  if (( first_failure != 0 )); then
    printf '\nharness/run_parity.sh: --keep-going was given and stage(s) failed; exiting with\n' >&2
    printf 'the FIRST failing stage status (%s).\n' "$first_failure" >&2
    exit "$first_failure"
  fi

  printf '\nharness/run_parity.sh completed: stages %s through %s, all exit 0.\n' \
    "$ACAS_PARITY_FROM" "$ACAS_PARITY_TO"
  exit "$EX_OK"
}

acas_parity_main "$@"
