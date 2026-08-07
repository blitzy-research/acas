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
ACAS_PARITY_SEED_DIR=''        # --seed-dir, forwarded to the two reset stages.
                               # Left empty by the parser and DEFAULTED to the
                               # canonical fixture root -- see
                               # acas_parity_resolve_fixture_root
ACAS_PARITY_SEED_DIR_STATED=0  # 1 if --seed-dir was given on the command line
ACAS_PARITY_STAGE_INDEX=0      # the stage being run, for the traps
ACAS_PARITY_STAGE_NAME=''
declare -a ACAS_PARITY_SUMMARY=()
declare -a ACAS_PARITY_OPERATIONS=()
# ⭐ ONE IDENTITY FOR ALL TEN STAGES (finding F-37). Every stage that publishes an
# artifact records it, so a verdict assembled from artifacts of two different
# attempts can be detected rather than believed. It is exported as well as passed,
# because the reset and seed stages reach the runners through `env'.
ACAS_PARITY_RUN_ID="${ACAS_PARITY_RUN_ID:-}"
# The loop variable acas_parity_argv uses to expand the operation list. Declared
# here rather than `local' because acas_parity_argv publishes into a global array and
# a `local' in a builder that is called from several places is easy to lose.
ACAS_PARITY_OP_ARG=''
# Non-zero once a stage has reported a behavioural difference. The protocol continues
# past one so the capture and the diff still happen, but no verdict may call the two
# states identical afterwards (F-14, F-17).
ACAS_PARITY_BEHAVIOURAL=0

# THE CAPTURE AND THE COMPARISON ARE BOUNDED BY ALL 22 IN-SCOPE TABLES, not by the
# scenario's declared affected_tables. Stages 3 and 7 pass --all-in-scope and stage 10
# passes it too, keeping --scenario-file only for the declared-effect gate that refuses
# an all-empty comparison. Both cycles perform the menu's own `overrewrite.'
# [general/general.cbl:L656-L672] - SYSTEM-REC key 1, SYSDEFLT-REC key 2, SYSTOT-REC
# key 4, reproduced by acas_posting/cli/args.py::overrewrite - so a capture bounded by
# what a scenario EXPECTS to move could have reported an EMPTY DIFF while the run date,
# the allocators, the flags, the defaults or the period totals differed. An empty diff
# is the single pass condition (AAP section 0.8.5), so its scope has to be everything
# the cycle can persist.
# THE STAGE REGISTRY IS NOT DEFINED HERE (finding F-16). It lives in
# harness/parity_stages.sh, which this script and both runners and the reset script all
# source, and which `--print-stages' publishes for the composed recipes and the test
# suite. It was defined here once, and independently restated in five other places that
# had drifted to saying EIGHT stages and NINE -- describing a protocol that did not match
# the one being driven. One definition, six readers.
#
# The body of each row is a case arm in acas_parity_run_stage; the registry and the arms
# are kept in the same order deliberately, and acas_parity_assert_stages below refuses to
# run if the two ever disagree, so a stage cannot be listed and quietly not implemented.
ACAS_PARITY_SELF_DIR=''
case "${BASH_SOURCE[0]}" in
  */*) ACAS_PARITY_SELF_DIR="${BASH_SOURCE[0]%/*}" ;;
  *)   ACAS_PARITY_SELF_DIR='.' ;;
esac
readonly ACAS_PARITY_SELF_DIR
readonly ACAS_PARITY_STAGE_REGISTRY="$ACAS_PARITY_SELF_DIR/parity_stages.sh"
if [[ ! -r "$ACAS_PARITY_STAGE_REGISTRY" ]]; then
  printf 'harness/run_parity.sh: the canonical stage registry is missing: %s\n' \
    "$ACAS_PARITY_STAGE_REGISTRY" >&2
  printf '  The protocol'"'"'s ten stages are defined there and nowhere else, so this\n' >&2
  printf '  driver cannot invent them. Restore the file from the repository.\n' >&2
  exit 71
fi
# shellcheck source=harness/parity_stages.sh
. "$ACAS_PARITY_STAGE_REGISTRY"

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

# A finding that does not stop the protocol but must not be lost in the transcript.
# Every line goes to stderr, so a caller capturing stdout for the summary still sees it.
acas_parity_warn() {
  local line
  printf 'WARNING: %s\n' "$1" >&2
  shift
  for line in "$@"; do
    printf '         %s\n' "$line" >&2
  done
}

acas_parity_stage_banner() {
  printf '\n========================================================================\n'
  # Phrased by the canonical registry so the count in the banner cannot drift from the
  # number of stages actually driven (finding F-16).
  printf '==> %s\n' "$(acas_parity_stage_headline "$1")"
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
                  DEFAULTED, and rarely needed: omitted, it resolves to the CANONICAL
                  FIXTURE ROOT -- $ACAS_FIXTURES if set, otherwise $ACAS_DATA/fixtures
                  -- plus the scenario name, which is exactly where
                  harness/build_fixtures.sh writes. Pass it only to run a scenario
                  against a fixture built somewhere else.
                  A default is necessary rather than convenient: a scenario's own
                  seed_dir resolves relative to the scenario file, which sits in the
                  READ-ONLY checkout, so it can never be where a built fixture lives.
                  Without the default every invocation had to supply the path and an
                  omission failed ten stages in.
  --keep-going    run the remaining stages after a failure instead of stopping.
                  NOT THE PROTOCOL: it exists for diagnosing a broken harness,
                  and the run's exit status is then the FIRST failing stage's.
                  A verdict produced this way is not evidence (rule R-6).
  --dry-run       print the ten commands and exit without running any of them.
  --print-stages  print the canonical stage registry as `<number><TAB><label>' rows,
                  one per line, and exit. This is the machine-readable form the
                  composed recipes and tests/conftest.py consume, so that no consumer
                  restates the stage names. harness/parity_stages.sh defines them.
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
      --print-stages)
        # THE PUBLICATION POINT for the canonical registry (finding F-16). The
        # composed recipes and tests/conftest.py read the protocol's stage names from
        # here rather than restating them, so there is one entry point to know and no
        # second copy to drift. One `<number><TAB><label>' row per line.
        acas_parity_stage_registry
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
        ACAS_PARITY_SEED_DIR_STATED=1
        ACAS_PARITY_SEED_DIR="$2"
        [[ -n "$ACAS_PARITY_SEED_DIR" ]] || acas_parity_die "$EX_USAGE" \
          '--seed-dir was given an empty path.' \
          'If the scenario'"'"'s own seed_dir is wanted, omit the flag.'
        shift 2
        ;;
      --seed-dir=*)
        ACAS_PARITY_SEED_DIR_STATED=1
        ACAS_PARITY_SEED_DIR="${1#*=}"
        [[ -n "$ACAS_PARITY_SEED_DIR" ]] || acas_parity_die "$EX_USAGE" \
          '--seed-dir was given an empty path.' \
          'If the scenario'"'"'s own seed_dir is wanted, omit the flag.'
        shift
        ;;
      --run-id)
        [[ $# -ge 2 ]] || acas_parity_die "$EX_USAGE" '--run-id requires an identifier.'
        ACAS_PARITY_RUN_ID="$2"
        shift 2
        ;;
      --run-id=*)
        ACAS_PARITY_RUN_ID="${1#*=}"
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

  # ---------------------------------------------------------------------------
  #  THE CANONICAL DESTRUCTIVE TARGET, PINNED -- AND EVERY BYPASS REFUSED.
  #
  #  Stages 1 and 5 DROP AND RE-APPLY EVERY TABLE in the target schema. This is
  #  the EVIDENCE driver, so it may only ever aim at the harness's own throwaway
  #  database, and it must not be possible to widen that aim by leaving something
  #  in the environment.
  #
  #  `harness/reset_db.sh` is also a general administrative tool, and as such it
  #  offers documented escape hatches: ACAS_DB_ALLOWED_SCHEMAS extends the
  #  disposable-SCHEMA allow-list [harness/reset_db.sh:L1380-L1388],
  #  ACAS_DB_DISPOSABLE_HOSTS extends the disposable-HOST allow-list [:L1393-L1404],
  #  and ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE / ACAS_RESET_ACKNOWLEDGE assert a target
  #  is disposable without proof [:L2196-L2205]. That last one is the sharpest: it
  #  short-circuits BOTH the static disposability check [:L2230] AND the SERVER-SIDE
  #  sentinel proof [:L2271], so with it set the reset will drop a database that
  #  carries no `acas_harness_disposable.disposability_marker' at all.
  #
  #  Those hatches are legitimate for the administrative tool and WRONG for
  #  evidence production, which is exactly the separation this gate enforces: the
  #  tool keeps them, the evidence path refuses them. Refused rather than silently
  #  unset, because an operator who set one deliberately must be told the evidence
  #  driver will not honour it rather than left believing it applied.
  # ---------------------------------------------------------------------------
  local -a bypasses=(
    ACAS_DB_ALLOWED_SCHEMAS
    ACAS_DB_DISPOSABLE_HOSTS
    ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE
    ACAS_RESET_ACKNOWLEDGE
  )
  local present=''
  for name in "${bypasses[@]}"; do
    [[ -n "${!name-}" ]] && present+="${present:+, }$name"
  done
  [[ -z "$present" ]] || acas_parity_die "$EX_PRECONDITION" \
    "a destructive-target bypass is set in the environment: $present." \
    'Stages 1 and 5 drop and re-apply every table in the target schema, so this' \
    'driver aims only at the harness'"'"'s own throwaway database and will not' \
    'honour a widened allow-list or an unproven acknowledgement.' \
    'ACAS_DB_ALLOWED_SCHEMAS and ACAS_DB_DISPOSABLE_HOSTS extend' \
    'harness/reset_db.sh'"'"'s allow-lists; ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE and' \
    'ACAS_RESET_ACKNOWLEDGE bypass the static disposability check AND the' \
    'server-side sentinel proof, so with one set the reset would drop a database' \
    'that cannot prove it is disposable.' \
    'Unset it and re-run. If you genuinely need to reset a different target, use' \
    'harness/reset_db.sh directly -- it is the general administrative tool and it' \
    'keeps those options deliberately. Evidence production does not.'

  #  THE TARGET ITSELF, pinned to what harness/docker-compose.yml supplies. The
  #  schema is exact; the host set is reset_db.sh'"'"'s own CANONICAL list
  #  [harness/reset_db.sh:L65], which is strictly tighter than its EXTENSIBLE
  #  disposable-host list [harness/reset_db.sh:L245-L252].
  local -r canonical_schema='ACASDB'
  local -a canonical_hosts=(mariadb 127.0.0.1 localhost ::1)
  [[ "${ACAS_DB_NAME-}" == "$canonical_schema" ]] || acas_parity_die "$EX_PRECONDITION" \
    "the target schema is '${ACAS_DB_NAME-<unset>}', and this driver only produces evidence against '$canonical_schema'." \
    'harness/docker-compose.yml sets ACAS_DB_NAME: ACASDB, and stages 1 and 5' \
    'drop and re-apply every table in whatever schema is named.' \
    'Use harness/reset_db.sh directly for any other schema.'

  local host_ok=0 candidate
  for candidate in "${canonical_hosts[@]}"; do
    [[ "${ACAS_DB_HOST-}" == "$candidate" ]] && host_ok=1
  done
  (( host_ok )) || acas_parity_die "$EX_PRECONDITION" \
    "the target host is '${ACAS_DB_HOST-<unset>}', which is not one of the canonical harness hosts: ${canonical_hosts[*]}." \
    'harness/docker-compose.yml sets ACAS_DB_HOST: mariadb, the Compose service' \
    'name on the internal network. A hostname is not a security boundary, but' \
    'aiming the evidence driver'"'"'s drop-and-re-apply at a host the harness does' \
    'not own is an accident worth refusing.' \
    'Use harness/reset_db.sh directly if the target really is elsewhere.'

  #  THE FROZEN PORT CARRIER, four characters: `LK-Port-Number pic x(4)'
  #  [common/acas-get-params.cbl:L158] and `01 Ws-Mysql-Port-Number pic x(4)'
  #  [copybooks/mysql-variables.cpy:L91]. A wider value would reach the compiled
  #  cycle TRUNCATED while this driver probed the untruncated one, so the two sides
  #  would not be talking to the same server.
  if [[ -n "${ACAS_DB_PORT-}" ]]; then
    [[ "$ACAS_DB_PORT" =~ ^[0-9]{1,4}$ ]] && (( ACAS_DB_PORT >= 1 && ACAS_DB_PORT <= 9999 )) \
      || acas_parity_die "$EX_PRECONDITION" \
        "ACAS_DB_PORT is '$ACAS_DB_PORT'; the frozen carrier is FOUR characters, so it must be 1..9999." \
        'The value travels through `LK-Port-Number pic x(4)`' \
        '[common/acas-get-params.cbl:L158] and `01 Ws-Mysql-Port-Number pic x(4)`' \
        '[copybooks/mysql-variables.cpy:L91], which every bridge STRINGs DB-Port' \
        'into [common/glpostingMT.cbl:L410-L413]. A five-digit port would reach the' \
        'compiled cycle truncated -- 13306 as 1330 -- while this driver probed' \
        '13306, so the two sides would not share a server.'
  fi

  #  THE CONSENT TOKEN, checked here so a wrong one fails before any stage runs.
  #  reset_db.sh derives the same expectation [harness/reset_db.sh:L1406]; naming it
  #  up front means an operator is not told to type a token only after stage 1 has
  #  already been attempted.
  local expected_consent="DESTROY ${ACAS_DB_NAME}@${ACAS_DB_HOST}:${ACAS_DB_PORT-}"
  if [[ -n "${ACAS_RESET_CONSENT-}" && "${ACAS_RESET_CONSENT}" != "$expected_consent" ]]; then
    acas_parity_die "$EX_PRECONDITION" \
      'ACAS_RESET_CONSENT does not name this target.' \
      "  expected: $expected_consent" \
      "  supplied: ${ACAS_RESET_CONSENT}" \
      'The token embeds the target so it cannot be left in an environment and' \
      'later authorise a different database. harness/docker-compose.yml sets the' \
      'matching token for the Compose target.'
  fi

  # ---------------------------------------------------------------------------
  #  THE SEED MODE, VALIDATED HERE SO STAGE 1 CANNOT FAIL FOR A REASON THE
  #  OPERATOR COULD HAVE BEEN TOLD ABOUT UP FRONT.
  #
  #  The canonical durable mode is autocommit ON, and it needs no flag: unset
  #  means on, harness/seed.sh defaults to it and harness/docker-compose.yml
  #  declares it. It is the ONLY mode in which the frozen loaders leave a durable
  #  row -- across all 28 common/*LD.cbl loaders there are 77 references to
  #  `perform aa030-Commit' and `perform aa020-Rollback' and not one is live, and
  #  the vendored cobmysqlapi38.c never calls mysql_autocommit. That diverges from
  #  the letter of the Agent Action Plan (sections 0.2.1.1, 0.4.1.7, 0.5.2), whose
  #  premise is the operator banner at [common/glbatchLD.cbl:L9-L13] -- superseded
  #  by the maintainer himself in the same frozen files at
  #  [common/glbatchLD.cbl:L386-L387] and [common/glbatchLD.cbl:L453]. Arbitrated
  #  under R-6; see docs/migration/ambiguity-resolutions.md.
  #
  #  A CLOSED SPELLING SET, and unrecognised text is REFUSED rather than guessed --
  #  the same discipline the transport flag uses, because a value silently read as
  #  its opposite is worse than a rejected one.
  # ---------------------------------------------------------------------------
  local seed_mode="${ACAS_SEED_AUTOCOMMIT-}"
  case "${seed_mode,,}" in
    ''|on|1|true|yes)
      : # the canonical durable mode
      ;;
    off|0|false|no)
      acas_parity_note 'ACAS_SEED_AUTOCOMMIT=off selects the AAP-LITERAL seeding window, in which the frozen loaders reach no live COMMIT and therefore persist NOTHING. Stage 1 will refuse it with exit 76 rather than hand an all-empty capture to the differ, because an empty capture yields an EMPTY DIFF and an empty diff is this protocol'"'"'s only pass condition. Unset the variable, or set it to on, to run the canonical durable mode. The arbitration is recorded in docs/migration/ambiguity-resolutions.md.'
      ;;
    *)
      acas_parity_die "$EX_USAGE" \
        "ACAS_SEED_AUTOCOMMIT does not recognise '${seed_mode}'." \
        'It takes on (or 1/true/yes), off (or 0/false/no), or nothing at all.' \
        'Unset means on, which is the canonical durable seeding mode. An' \
        'unrecognised value is refused rather than guessed at, because reading it' \
        'as its opposite would silently change whether this run can produce' \
        'evidence.'
      ;;
  esac

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

  acas_parity_assert_operations_supported_by_both_sides
  acas_parity_resolve_fixture_root
  acas_parity_assert_seed_files
}

# =============================================================================
# EVERY DECLARED OPERATION MUST BE DRIVEABLE BY BOTH SIDES, CHECKED BEFORE STAGE 1
#
# A parity verdict is only worth something if the two sides did the same work. The
# scenario's `operations:' list is the statement of that work, and each runner keeps
# its own map from an operation name to what it drives -- a compiled menu key on one
# side, a `python -m' module on the other. Nothing previously compared the two maps
# against the list.
#
# ⭐ THE FAILURE IT PREVENTS IS SILENT AND EXPENSIVE. An operation present in one
# map and absent from the other makes the scenario undriveable on one side, and the
# way that used to surface was: nine stages run, several minutes and two full seeds
# spent, and then stage 10 reports a table difference that is not a behavioural
# finding at all but a difference in how much work each side did. Read at face value
# it accuses the migration of a defect it does not have.
#
# THE MAPS ARE READ, NOT RESTATED. Both are `readonly -a' arrays in their own
# scripts, so this check greps the declarations out of the shipped files rather than
# holding a third copy that could drift from either. A third list would be one more
# thing to keep in step, which is the defect this check exists to catch.
# =============================================================================
acas_parity_operation_names() {
  # $1 the script, $2 the array name, $3 the field separator of its rows.
  local script="$1" array="$2" sep="$3"
  sed -n "/^readonly -a ${array}=(/,/^)/p" -- "$script" \
    | sed -e '1d' -e '$d' \
    | sed -e "s/^[[:space:]]*'//" -e "s/'[[:space:]]*$//" \
    | awk -v FS="$sep" 'NF { print $1 }'
}

acas_parity_assert_operations_supported_by_both_sides() {
  local cobol_script="$ACAS_PARITY_HARNESS/run_cobol_scenario.sh"
  local python_script="$ACAS_PARITY_HARNESS/run_python_scenario.sh"

  local -a cobol_ops=() python_ops=()
  mapfile -t cobol_ops < <(acas_parity_operation_names \
    "$cobol_script" 'ACAS_RUN_OPERATION_MAP' ':')
  mapfile -t python_ops < <(acas_parity_operation_names \
    "$python_script" 'ACAS_PY_OPERATION_MAP' '|')

  (( ${#cobol_ops[@]} > 0 )) || acas_parity_die "$EX_PRECONDITION" \
    "could not read the operation map out of $cobol_script." \
    'It is a `readonly -a ACAS_RUN_OPERATION_MAP=(...)'"'"' block; this check reads' \
    'the shipped file rather than holding a third copy of the list.'
  (( ${#python_ops[@]} > 0 )) || acas_parity_die "$EX_PRECONDITION" \
    "could not read the operation map out of $python_script." \
    'It is a `readonly -a ACAS_PY_OPERATION_MAP=(...)'"'"' block.'

  local operation found_cobol found_python name
  local -a unsupported=()
  for operation in "${ACAS_PARITY_OPERATIONS[@]}"; do
    found_cobol=0
    found_python=0
    for name in "${cobol_ops[@]}"; do
      [[ "$name" == "$operation" ]] && { found_cobol=1; break; }
    done
    for name in "${python_ops[@]}"; do
      [[ "$name" == "$operation" ]] && { found_python=1; break; }
    done
    if (( found_cobol == 0 && found_python == 0 )); then
      unsupported+=("$operation: neither runner drives it")
    elif (( found_cobol == 0 )); then
      unsupported+=("$operation: the migrated runner drives it, the compiled runner does not")
    elif (( found_python == 0 )); then
      unsupported+=("$operation: the compiled runner drives it, the migrated runner does not")
    fi
  done

  if (( ${#unsupported[@]} > 0 )); then
    local -a lines=()
    for name in "${unsupported[@]}"; do
      lines+=("  $name")
    done
    acas_parity_die "$EX_PRECONDITION" \
      "this scenario declares ${#unsupported[@]} operation(s) that the two sides do not both support." \
      "${lines[@]}" \
      'A parity verdict means the two sides did the SAME work, so an operation only' \
      'one side can drive makes the comparison meaningless -- and it would surface' \
      'as a table difference at stage 10, after two full seeds, looking exactly like' \
      'a behavioural defect in the migration. Refused here instead.' \
      "  compiled side drives: $(printf '%s ' "${cobol_ops[@]}")" \
      "  migrated side drives: $(printf '%s ' "${python_ops[@]}")"
  fi

  acas_parity_log \
    "operations    = ${ACAS_PARITY_OPERATIONS[*]}  (all ${#ACAS_PARITY_OPERATIONS[@]} driveable by both sides)"
}

# =============================================================================
# THE CANONICAL FIXTURE ROOT -- ONE RULE, STATED ONCE, DERIVED IDENTICALLY
#
# A built fixture cannot live where a scenario's own `seed_dir' points: that key
# resolves relative to the scenario FILE, which sits in the checkout, and the
# checkout is mounted read-only because it is frozen specification (R-3). So the
# runtime location is a separate thing that has to be agreed on, and THREE
# components have to agree on it:
#
#   harness/build_fixtures.sh   WRITES it  -- and OWNS the rule; its `ACAS_BF_OUT'
#                                             default is the single statement of it
#   harness/run_parity.sh       READS it   -- here
#   tests/conftest.py           READS it   -- scenario_fixture_dir()
#
# The rule: `$ACAS_FIXTURES' when set and non-empty, otherwise `$ACAS_DATA/fixtures',
# and then `/<scenario>'. ACAS_DATA is already asserted non-empty above, so the
# builder's extra `:-/data' fallback cannot be reached from inside this protocol.
# tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py asserts that the
# three derivations agree, which is what keeps them from drifting apart -- a comment
# alone would not.
#
# WHY IT IS A DEFAULT AND NOT A REQUIREMENT: an omitted --seed-dir used to leave
# seed.sh resolving the scenario's own relative seed_dir inside the read-only
# checkout, which fails -- but it fails in stage 1, AFTER the schema has already been
# dropped and re-applied. The default removes a way to compose the protocol wrongly.
# =============================================================================
acas_parity_resolve_fixture_root() {
  if (( ACAS_PARITY_SEED_DIR_STATED )); then
    acas_parity_log "--seed-dir was stated: $ACAS_PARITY_SEED_DIR"
    return 0
  fi

  local root="${ACAS_FIXTURES:-}"
  [[ -n "$root" ]] || root="${ACAS_DATA%/}/fixtures"
  ACAS_PARITY_SEED_DIR="${root%/}/$ACAS_PARITY_SCENARIO"
  acas_parity_log "fixture root (canonical, --seed-dir not stated): $ACAS_PARITY_SEED_DIR"
}

# =============================================================================
# EVERY DECLARED SEED FILE IS CHECKED BEFORE STAGE 1 OPENS A CONNECTION
#
# harness/seed.sh already refuses a missing declared file (75). This is not a
# duplicate of that check -- it is the same check moved EARLIER, and the difference
# is what the operator is left with. seed.sh runs inside stage 1, AFTER
# harness/reset_db.sh has dropped and re-applied the whole frozen schema, so a
# fixture that was never built costs a wiped database before anything says so. Here
# the run refuses before stage 1 starts and the database is untouched.
#
# It reads the scenario through the SAME hardened, length-prefixed transport
# harness/seed.sh uses, and for the same reason: the values come from a data file and
# reach a shell loop. See the emitter's own docstring in harness/seed.sh.
# =============================================================================
acas_parity_assert_seed_files() {
  local parsed rc=0
  parsed="$("$ACAS_PARITY_PYTHON" - "$ACAS_PARITY_SCENARIO_FILE" <<'SEEDLIST'
"""Emit the scenario's declared seed file names, control-free and length-prefixed.

The grammar is harness/seed.sh's, minus the SEED_DIR record this caller does not
need -- it has already resolved the runtime location itself:

    BEGIN<TAB>1
    COUNT<TAB><n>
    SEED_FILE<TAB><byte length><TAB><name>     (n times, in declared order)
    END<TAB><n>

Exit 0 parsed, 3 unreadable or not a mapping, 4 no seed file list, 5 an unusable
seed file name.
"""

import re
import sys

import yaml

BARE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')

path = sys.argv[1]
try:
    with open(path, 'r', encoding='utf-8') as handle:
        document = yaml.safe_load(handle)
except (OSError, yaml.YAMLError) as error:
    sys.stderr.write('cannot parse %s: %s\n' % (path, error))
    raise SystemExit(3)
if not isinstance(document, dict):
    sys.stderr.write('%s is not a YAML mapping\n' % path)
    raise SystemExit(3)

files = document.get('seed_files', document.get('seed-files'))
if not isinstance(files, (list, tuple)) or not files:
    sys.stderr.write('%s declares no seed_files list\n' % path)
    raise SystemExit(4)

names = []
for entry in files:
    if not isinstance(entry, str) or not BARE_NAME.match(entry):
        sys.stderr.write('seed file %r in %s is not a plain file name\n'
                         % (entry, path))
        raise SystemExit(5)
    names.append(entry)

sys.stdout.write('BEGIN\t1\n')
sys.stdout.write('COUNT\t%d\n' % len(names))
for entry in names:
    sys.stdout.write('SEED_FILE\t%d\t%s\n' % (len(entry), entry))
sys.stdout.write('END\t%d\n' % len(names))
SEEDLIST
  )" || rc=$?
  if (( rc != 0 )); then
    acas_parity_die "$EX_PRECONDITION" \
      "the scenario's seed_files list could not be read from $ACAS_PARITY_SCENARIO_FILE." \
      "  reported: ${parsed:-<no output>}"
  fi

  local key len value begin_seen=0 declared='' ending=''
  local -a wanted=()
  while IFS=$'\t' read -r key len value; do
    case "$key" in
      BEGIN)
        [[ "$len" == '1' ]] || acas_parity_die "$EX_PRECONDITION" \
          "seed transport version '$len' is not the version this reader speaks."
        begin_seen=1
        ;;
      COUNT) declared="$len" ;;
      END)   ending="$len" ;;
      SEED_FILE)
        [[ "$len" =~ ^[0-9]+$ ]] || acas_parity_die "$EX_PRECONDITION" \
          "a SEED_FILE record carries a non-numeric length field ('$len')."
        (( ${#value} == len )) || acas_parity_die "$EX_PRECONDITION" \
          "a SEED_FILE record decoded to ${#value} byte(s) where it declares $len."
        [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || acas_parity_die \
          "$EX_PRECONDITION" \
          "the decoded seed file name '$value' is not a plain file name."
        wanted+=("$value")
        ;;
      '') : ;;
      *)
        acas_parity_die "$EX_PRECONDITION" "unknown seed transport record '$key'."
        ;;
    esac
  done <<<"$parsed"

  (( begin_seen == 1 )) || acas_parity_die "$EX_PRECONDITION" \
    'the seed transport stream carries no BEGIN record.'
  [[ "$declared" =~ ^[0-9]+$ && "$ending" =~ ^[0-9]+$ ]] || acas_parity_die \
    "$EX_PRECONDITION" 'the seed transport stream carries no numeric COUNT and END.'
  (( declared == ending && ${#wanted[@]} == declared )) || acas_parity_die \
    "$EX_PRECONDITION" \
    "the seed transport disagrees with itself: COUNT $declared, END $ending, ${#wanted[@]} decoded."

  [[ -d "$ACAS_PARITY_SEED_DIR" ]] || acas_parity_die "$EX_PRECONDITION" \
    "the scenario's fixture directory does not exist: $ACAS_PARITY_SEED_DIR" \
    "Build it first: harness/build_fixtures.sh $ACAS_PARITY_SCENARIO" \
    'Checked HERE rather than in stage 1 so that a missing fixture does not cost' \
    'a dropped and re-applied schema before anything reports it.'

  local name absent=0
  for name in "${wanted[@]}"; do
    if [[ ! -f "$ACAS_PARITY_SEED_DIR/$name" || ! -r "$ACAS_PARITY_SEED_DIR/$name" ]]; then
      printf 'FATAL: declared seed file is missing or unreadable: %s\n' \
        "$ACAS_PARITY_SEED_DIR/$name" >&2
      absent=1
    fi
  done
  (( absent == 0 )) || acas_parity_die "$EX_PRECONDITION" \
    "the scenario declares seed files that are not in $ACAS_PARITY_SEED_DIR." \
    "Rebuild the fixture: harness/build_fixtures.sh $ACAS_PARITY_SCENARIO" \
    'A missing file would leave its table empty and the resulting dump would' \
    'still look like a successful seed.'

  acas_parity_log "seed fixture verified: ${#wanted[@]} declared file(s) present in $ACAS_PARITY_SEED_DIR"
}

# acas_parity_argv <stage-number> Publishes the stage's command in
# ACAS_PARITY_ARGV. One case arm per row of ACAS_PARITY_STAGES, in the same order.
declare -a ACAS_PARITY_ARGV=()
# =============================================================================
# THE ORACLE PROVENANCE GATE -- required before the compiled cycle runs
#
# Stage 2 runs the compiled COBOL, and its output is THE SPECIFICATION every other
# stage is measured against (rule R-6). So this driver must know what that oracle
# was built from, and it must refuse an oracle whose identity was decided by
# ambient configuration rather than by a reviewed source change.
#
# `harness/build_oracle.sh` publishes $ACAS_BUILD/oracle-attestation.txt after a
# FULL five-step sequence, recording the vendored preSQL archive digest against its
# pinned expectation, the cobmysqlapi.o digest and whether it was prebuilt, the
# compiler versions, and a digest over the compiled module set. Two of its options
# can substitute the bytes the oracle is built from -- ACAS_PRESQL2_SHA256 accepts a
# replacement archive, and ACAS_COBMYSQLAPI_OBJ reuses an already-compiled object --
# and the package ships two SUPERSEDED API sources that must not be used, so a
# renamed old API could otherwise define the specification unnoticed. The build
# records that as a fact; refusing it is this gate's job, which keeps the build
# script debuggable and the evidence path strict.
#
# FOUR THINGS ARE CHECKED, and the fourth is the one that makes the other three
# worth having:
#   1. the attestation EXISTS -- a partial or --only build leaves none;
#   2. it is the version this driver understands;
#   3. `overrides-used' is `no';
#   4. the module-set digest still matches the modules ON DISK, recomputed here the
#      same way the build computed it. Without this an attestation would only
#      describe some build, not the artifacts stage 2 is about to execute.
# =============================================================================
readonly ACAS_PARITY_ATTESTATION_BASENAME='oracle-attestation.txt'
readonly ACAS_PARITY_ATTESTATION_VERSION='1'
readonly -a ACAS_PARITY_ORACLE_DIRS=(common general irs purchase sales stock)

#  IDENTICAL to acas_module_set_digest in harness/build_oracle.sh, deliberately:
#  every *.so under the six build directories, sorted by path, each hashed, and the
#  whole listing hashed again. If the two ever drift the gate fails closed, which is
#  the safe direction.
acas_parity_module_set_digest() {
  local dir
  {
    for dir in "${ACAS_PARITY_ORACLE_DIRS[@]}"; do
      find "$ACAS_BUILD/$dir" -maxdepth 1 -type f -name '*.so' -print 2>/dev/null
    done
  } | LC_ALL=C sort | while IFS= read -r module; do
    sha256sum "$module" 2>/dev/null || printf 'UNREADABLE  %s\n' "$module"
  done | sha256sum | cut -d' ' -f1
}

acas_parity_assert_oracle_attestation() {
  [[ -n "${ACAS_BUILD-}" ]] || acas_parity_die "$EX_PRECONDITION" \
    'ACAS_BUILD is unset, so the oracle build tree cannot be located and its' \
    'provenance cannot be verified.' \
    'harness/docker-compose.yml sets ACAS_BUILD: /build.'

  local attestation="$ACAS_BUILD/$ACAS_PARITY_ATTESTATION_BASENAME"
  [[ -f "$attestation" ]] || acas_parity_die "$EX_PRECONDITION" \
    "the oracle carries no provenance attestation: $attestation is absent." \
    'Stage 2 runs the compiled COBOL and its output IS the specification, so this' \
    'driver will not accept whatever modules happen to be lying in the build tree.' \
    'harness/build_oracle.sh writes the attestation after a FULL five-step run, so' \
    'an absent file means the oracle was never built, or was built with --only or' \
    '--from and is therefore only partly this repository'"'"'s.' \
    'Build it: harness/build_oracle.sh'

  local version='' overrides='' recorded_digest='' recorded_count=''
  local presql_actual='' presql_pinned='' digest_override='' matches_pin=''
  local redirected='' provenance='' cobc_version='' key value
  while IFS=$'\t' read -r key value; do
    case "$key" in
      attestation-version)     version="$value" ;;
      overrides-used)          overrides="$value" ;;
      module-set-sha256)       recorded_digest="$value" ;;
      module-count)            recorded_count="$value" ;;
      presql2-sha256)          presql_actual="$value" ;;
      presql2-pinned-sha256)   presql_pinned="$value" ;;
      presql2-digest-override) digest_override="$value" ;;
      presql2-matches-pin)     matches_pin="$value" ;;
      cobmysqlapi-redirected)  redirected="$value" ;;
      cobmysqlapi-provenance)  provenance="$value" ;;
      cobc-version)            cobc_version="$value" ;;
    esac
  done < "$attestation"

  [[ "$version" == "$ACAS_PARITY_ATTESTATION_VERSION" ]] || acas_parity_die "$EX_PRECONDITION" \
    "the attestation at $attestation declares version '${version:-<none>}'; this driver understands version $ACAS_PARITY_ATTESTATION_VERSION." \
    'A format this driver cannot read is refused rather than partly believed.' \
    'Rebuild the oracle with the matching harness/build_oracle.sh.'

  if [[ "$overrides" != 'no' ]]; then
    acas_parity_die "$EX_PRECONDITION" \
      'THIS ORACLE'"'"'S IDENTITY WAS NOT ESTABLISHED FROM THE REVIEWED SOURCES ALONE,' \
      'so it cannot produce evidence.' \
      "  attestation             $attestation" \
      "  overrides-used          ${overrides:-<unrecorded>}" \
      "  presql2-digest-override ${digest_override:-<unrecorded>}" \
      "  presql2-matches-pin     ${matches_pin:-<unrecorded>}" \
      "  cobmysqlapi-redirected  ${redirected:-<unrecorded>}" \
      "  cobmysqlapi-provenance  ${provenance:-<unrecorded>}" \
      "  presql2 archive digest  ${presql_actual:-<unrecorded>}" \
      "  pinned digest           ${presql_pinned:-<unrecorded>}" \
      'ACAS_PRESQL2_SHA256 accepts a replacement preSQL archive, and the translator' \
      'in it is what turns every *MT.scb into the *MT.cbl bridge that is actually' \
      'compiled. Pointing ACAS_COBMYSQLAPI_OBJ away from the image-built object' \
      'substitutes the C interface that every bridge, handler and loader links, and' \
      'the vendored package also ships two SUPERSEDED variants of that source which' \
      'must not be used. Any of these lets ambient configuration decide what the' \
      'behavioural specification IS.' \
      'Note that ACAS_COBMYSQLAPI_OBJ pointing at the image'"'"'s own object is NOT an' \
      'override -- harness/Dockerfile.gnucobol builds it there from the vendored' \
      'source with the recovered rule, and reusing it is the normal case.' \
      'Rebuild without them: harness/build_oracle.sh' \
      'To replace either legitimately, make it a REVIEWED SOURCE CHANGE -- update the' \
      'vendored archive and ACAS_PRESQL2_SHA256_EXPECTED together -- rather than' \
      'setting a variable at run time.'
  fi

  #  THE ARCHIVE DIGEST MUST EQUAL ITS PIN, re-derived here from the two values the
  #  attestation records rather than taken from the producer's own verdict. A
  #  producer that computed `overrides-used' wrongly cannot smuggle a substituted
  #  archive past this, because the mismatch is visible in the record itself.
  if [[ -z "$presql_actual" || -z "$presql_pinned" || "$presql_actual" != "$presql_pinned" ]]; then
    acas_parity_die "$EX_PRECONDITION" \
      'THE preSQL ARCHIVE DOES NOT MATCH ITS PIN, so the translator that generated' \
      'every *MT.cbl bridge is not the reviewed one.' \
      "  attestation        $attestation" \
      "  archive digest     ${presql_actual:-<unrecorded>}" \
      "  pinned digest      ${presql_pinned:-<unrecorded>}" \
      'Rebuild the oracle from the vendored archive: harness/build_oracle.sh' \
      'If the archive was updated deliberately, update ACAS_PRESQL2_SHA256_EXPECTED' \
      'in harness/build_oracle.sh in the same commit.'
  fi

  #  THE C INTERFACE MUST HAVE COME FROM THE VENDORED SOURCE. Exactly two answers
  #  are legitimate: the image built it (harness/Dockerfile.gnucobol:L478-L479), or
  #  step 2 compiled it during this build. Anything else -- including an unresolved
  #  path -- means the object every bridge links is of unestablished origin.
  case "$provenance" in
    image-built-from-vendored-source|compiled-from-vendored-source-this-run) : ;;
    *)
      acas_parity_die "$EX_PRECONDITION" \
        'THE cobmysqlapi.o C INTERFACE IS OF UNESTABLISHED ORIGIN, so the object that' \
        'every bridge, handler and loader links cannot be traced to the vendored source.' \
        "  attestation        $attestation" \
        "  provenance         ${provenance:-<unrecorded>}" \
        "  redirected         ${redirected:-<unrecorded>}" \
        'Legitimate values are image-built-from-vendored-source and' \
        'compiled-from-vendored-source-this-run.' \
        'Rebuild the oracle: harness/build_oracle.sh'
      ;;
  esac

  #  THE ATTESTATION MUST DESCRIBE THE MODULES STAGE 2 WILL ACTUALLY EXECUTE.
  local measured
  measured="$(acas_parity_module_set_digest)"
  [[ "$measured" == "$recorded_digest" ]] || acas_parity_die "$EX_PRECONDITION" \
    'THE COMPILED MODULES DO NOT MATCH THE ATTESTATION, so its provenance does not' \
    'describe the oracle this run would execute.' \
    "  attestation        $attestation" \
    "  recorded digest    ${recorded_digest:-<unrecorded>}  (${recorded_count:-?} module(s))" \
    "  measured digest    $measured" \
    'Every *.so under the six build directories is hashed, sorted by path, and the' \
    'listing hashed again, so a single replaced, added or removed module changes' \
    'this value. Rebuild the oracle: harness/build_oracle.sh'

  acas_parity_log "oracle provenance verified: $attestation"
  acas_parity_note "no identity override; cobmysqlapi.o ${provenance}; preSQL archive matches its pin; ${recorded_count:-?} module(s), set digest $measured; toolchain ${cobc_version:-unknown}"
}

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
    # ⭐ EVERY DECLARED OPERATION, IN ONE INVOCATION (finding F-12)
    #
    # This used to pass ONLY the first operation, and acas_parity_run_cobol_sequence
    # made up the difference by invoking the runner once per operation and then
    # copying operation one's seed fingerprint and run-status record back over the
    # last one's -- because only one record could exist per side. Operations 2..n
    # therefore had NO attested disposition at all.
    #
    # harness/run_cobol_scenario.sh now drives the whole ordered list itself and
    # publishes one disposition per operation, so this is an ordinary stage again and
    # the copy-back is gone.
    2) ACAS_PARITY_ARGV=(
         'env' "ACAS_DATA=$ACAS_PARITY_RUNTIME_DATA"
         "ACAS_LEDGERS=$ACAS_PARITY_RUNTIME_DATA"
         "$H/run_cobol_scenario.sh" '--run-id' "$ACAS_PARITY_RUN_ID"
       )
       for ACAS_PARITY_OP_ARG in "${ACAS_PARITY_OPERATIONS[@]}"; do
         ACAS_PARITY_ARGV+=('--operation' "$ACAS_PARITY_OP_ARG")
       done
       ACAS_PARITY_ARGV+=("$S")
       ;;
    3) ACAS_PARITY_ARGV=(
         "$ACAS_PARITY_PYTHON" "$H/dump_tables.py"
         '--scenario' "$N" '--side' 'cobol' '--all-in-scope'
       ) ;;
    4) ACAS_PARITY_ARGV=(
         "$ACAS_PARITY_PYTHON" "$H/normalize.py"
         '--scenario' "$N" '--side' 'cobol'
       ) ;;
    6) ACAS_PARITY_ARGV=(
         'env' "ACAS_DATA=$ACAS_PARITY_RUNTIME_DATA"
         "ACAS_LEDGERS=$ACAS_PARITY_RUNTIME_DATA"
         "$H/run_python_scenario.sh" '--run-id' "$ACAS_PARITY_RUN_ID" "$S"
       ) ;;
    7) ACAS_PARITY_ARGV=(
         "$ACAS_PARITY_PYTHON" "$H/dump_tables.py"
         '--scenario' "$N" '--side' 'python' '--all-in-scope'
       ) ;;
    8) ACAS_PARITY_ARGV=(
         "$ACAS_PARITY_PYTHON" "$H/normalize.py"
         '--scenario' "$N" '--side' 'python'
       ) ;;
    9) ACAS_PARITY_ARGV=() ;;   # an in-script check; see acas_parity_run_stage
    10) ACAS_PARITY_ARGV=(
         "$ACAS_PARITY_PYTHON" "$H/diff_states.py"
         '--scenario' "$N" '--all-in-scope' '--scenario-file' "$S"
       ) ;;
    *)
      acas_parity_die "$EX_USAGE" "there is no stage $stage."
      ;;
  esac
}

# ⭐ THE ORACLE-SIDE SEQUENCE WORKAROUND IS GONE (finding F-12)
#
# acas_parity_run_cobol_sequence used to live here. It invoked
# harness/run_cobol_scenario.sh once per declared operation -- because that script
# read only the singular `operation:' key -- and then copied operation ONE's
# cobol.seed-fingerprint and cobol.run-status back over whatever the LAST invocation
# had left, because the two names are canonical and only one record could exist per
# side.
#
# The consequence was that operations 2..n had no attested disposition at all: their
# statuses were never recorded anywhere a later stage could read, so nothing
# downstream could tell a clean run of four operations from a clean run of one
# followed by three that aborted. And the record that WAS published described
# operation one while the database held the effects of all four.
#
# The runner now takes a repeatable --operation, drives the whole declared list in
# order in ONE invocation, and publishes cobol.operation-status with one record per
# operation. Stage 2 is therefore an ordinary stage built by acas_parity_argv, and
# there is nothing left here to work around.

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

# ⭐ A BEHAVIOURAL DISPOSITION IS NOT A STAGE FAILURE (findings F-14, F-17)
#
# Every non-zero status used to stop the protocol, which sounds right and is wrong for
# exactly one status. harness/run_python_scenario.sh exits EX_BEHAVIOUR=69 when an
# operation's observed status CONTRADICTS the one the scenario declared -- and that is
# the single most valuable thing this protocol can report. The run happened, the
# database holds its effects, and the state capture is exactly what would show WHERE
# the two cycles diverged.
#
# Stopping at stage 6 threw all of that away: no capture, no normalisation, no diff,
# and a summary saying the protocol could not be run. A real behavioural difference
# was therefore indistinguishable from a broken container, and
# tests/conftest.py compounded it by listing 69 among the wrapper-fault codes.
#
# So a behavioural status lets the protocol CONTINUE to the dump, and is remembered:
# the verdict at the end cannot be "identical" when an operation contradicted its
# declared disposition, whatever the diff says. Everything else -- usage, precondition,
# database, oracle, drive, assert, timeout -- still stops the run, because a stage that
# could not verify its own preconditions has not measured behaviour at all.
#
# Stage 2 is deliberately NOT in this table. harness/run_cobol_scenario.sh publishes
# each operation's disposition in cobol.operation-status and exits ZERO when it drove
# them all successfully, so a non-zero status from that side is always a wrapper fault.
acas_parity_is_behavioural() {
  local stage="$1" rc="$2"
  [[ "$stage" == '6' ]] && (( rc == 69 ))
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
  fi
  acas_parity_argv "$stage"
  acas_parity_log "command: $(acas_parity_join "${ACAS_PARITY_ARGV[@]}")"
  # `set +e' around exactly one command, so a non-zero status is a value to report
  # rather than an unexpected failure for the ERR trap.
  set +e
  "${ACAS_PARITY_ARGV[@]}"
  rc=$?
  set -e

  if (( rc == 0 )); then
    acas_parity_log "stage $stage: exit 0"
    ACAS_PARITY_SUMMARY+=("$(printf '%-3s %-58s %s' "$stage" "$label" 'ok')")
  else
    acas_parity_log "stage $stage: exit $rc"
    ACAS_PARITY_SUMMARY+=("$(printf '%-3s %-58s exit %s' "$stage" "$label" "$rc")")
  fi
  return "$rc"
}

# The verdict manifest harness/diff_states.py publishes at stage 10, and the result
# artifact this driver retains beside it.
readonly ACAS_PARITY_VERDICT_FILE='verdict.json'
readonly ACAS_PARITY_RESULT_FILE='parity-result'
# The last stage. A parity claim requires it to have run, so it is named rather than
# spelled 10 at each use.
readonly ACAS_PARITY_VERDICT_STAGE=10

# THE VERDICT GATE (finding F-15).
#
# Before this, the summary printed "the two states are IDENTICAL" whenever no stage had
# failed -- including `--from 1 --to 4', which never reaches the comparison at all, and
# `--from 10 --to 10' resumed over artifacts from an earlier attempt. Four stages
# completing successfully is not a parity claim; it is four stages completing. The claim
# now requires the ONE artifact that can carry it: a verdict manifest, published by
# harness/diff_states.py at stage 10, recording outcome `identical' AND carrying THIS
# run's id.
#
# Sets ACAS_PARITY_VERDICT_STATE to exactly one of:
#   identical    stage 10 ran in this attempt and found no difference
#   different    stage 10 ran in this attempt and found one
#   incomplete   stage 10 was outside the requested range, so nothing compared
#   missing      stage 10 was in range but published no manifest
#   foreign      a manifest is there, but it belongs to a different run id
#   unreadable   a manifest is there and could not be parsed
# and ACAS_PARITY_VERDICT_DETAIL to a sentence naming why.
ACAS_PARITY_VERDICT_STATE=''
ACAS_PARITY_VERDICT_DETAIL=''
ACAS_PARITY_VERDICT_PATH=''

acas_parity_read_verdict() {
  ACAS_PARITY_VERDICT_STATE='missing'
  ACAS_PARITY_VERDICT_DETAIL=''
  ACAS_PARITY_VERDICT_PATH="$ACAS_OUT/$ACAS_PARITY_SCENARIO/$ACAS_PARITY_VERDICT_FILE"

  if (( ACAS_PARITY_TO < ACAS_PARITY_VERDICT_STAGE \
     || ACAS_PARITY_FROM > ACAS_PARITY_VERDICT_STAGE )); then
    ACAS_PARITY_VERDICT_STATE='incomplete'
    ACAS_PARITY_VERDICT_DETAIL="stage $ACAS_PARITY_VERDICT_STAGE was outside the requested range ($ACAS_PARITY_FROM through $ACAS_PARITY_TO), so nothing was compared"
    return 0
  fi

  if [[ ! -f "$ACAS_PARITY_VERDICT_PATH" ]]; then
    ACAS_PARITY_VERDICT_DETAIL="no $ACAS_PARITY_VERDICT_FILE was published at $ACAS_PARITY_VERDICT_PATH"
    return 0
  fi

  # Read with python3 rather than a grep: the manifest is JSON, and a claim this
  # important must not rest on a pattern that a differently formatted file could
  # satisfy by accident. Three fields on one line, tab separated.
  local parsed=''
  parsed="$("$ACAS_PARITY_PYTHON" - "$ACAS_PARITY_VERDICT_PATH" <<'ACAS_VERDICT_READER' 2>/dev/null
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        data = json.load(handle)
except (OSError, ValueError):
    raise SystemExit(3)
if not isinstance(data, dict):
    raise SystemExit(3)
outcome = data.get("outcome")
run_id = data.get("run_id")
tables = data.get("tables_compared")
if not isinstance(outcome, str) or not outcome:
    raise SystemExit(3)
print(
    "\t".join(
        (
            outcome,
            run_id if isinstance(run_id, str) else "",
            str(tables) if isinstance(tables, int) else "",
        )
    )
)
ACAS_VERDICT_READER
)" || {
    ACAS_PARITY_VERDICT_STATE='unreadable'
    ACAS_PARITY_VERDICT_DETAIL="$ACAS_PARITY_VERDICT_PATH could not be read as a verdict manifest"
    return 0
  }

  local outcome run_id tables
  IFS=$'\t' read -r outcome run_id tables <<< "$parsed"

  if [[ "$run_id" != "$ACAS_PARITY_RUN_ID" ]]; then
    ACAS_PARITY_VERDICT_STATE='foreign'
    ACAS_PARITY_VERDICT_DETAIL="the manifest at $ACAS_PARITY_VERDICT_PATH records run id '${run_id:-<none>}', not this run's '$ACAS_PARITY_RUN_ID'"
    return 0
  fi

  case "$outcome" in
    identical)
      ACAS_PARITY_VERDICT_STATE='identical'
      ACAS_PARITY_VERDICT_DETAIL="${tables:-0} table(s) compared, no difference"
      ;;
    different)
      ACAS_PARITY_VERDICT_STATE='different'
      ACAS_PARITY_VERDICT_DETAIL="${tables:-0} table(s) compared, at least one differs"
      ;;
    *)
      ACAS_PARITY_VERDICT_STATE='unreadable'
      ACAS_PARITY_VERDICT_DETAIL="the manifest records outcome '$outcome', which is neither 'identical' nor 'different'"
      ;;
  esac
  return 0
}

# THE RETAINED RESULT (finding F-35). The summary above is prose on a terminal; this is
# the machine-readable record of what this driver concluded, published where the
# scenario's other evidence lives so tests/conftest.py and the migration's diff evidence
# read a claim rather than scrape a transcript. Published on EVERY outcome, pass or not.
#
# Written to a staging name in the same directory and renamed, so a reader never sees a
# half-written record, and 0600 like every other artifact this protocol publishes.
acas_parity_publish_result() {
  local claim="$1" first_failure="$2"
  local directory="$ACAS_OUT/$ACAS_PARITY_SCENARIO"
  local target="$directory/$ACAS_PARITY_RESULT_FILE"
  local staging="$directory/.$ACAS_PARITY_RESULT_FILE.tmp.$$"

  mkdir -p "$directory" 2>/dev/null || {
    acas_parity_warn \
      "could not create $directory, so no $ACAS_PARITY_RESULT_FILE was published." \
      'The verdict printed above still stands; nothing downstream can read it.'
    return 0
  }

  {
    printf 'scenario\t%s\n' "$ACAS_PARITY_SCENARIO"
    printf 'run_id\t%s\n' "$ACAS_PARITY_RUN_ID"
    printf 'claim\t%s\n' "$claim"
    printf 'stages_requested\t%s\t%s\n' "$ACAS_PARITY_FROM" "$ACAS_PARITY_TO"
    printf 'first_failing_stage_status\t%s\n' "$first_failure"
    printf 'behavioural_status\t%s\n' "$ACAS_PARITY_BEHAVIOURAL"
    printf 'verdict_state\t%s\n' "$ACAS_PARITY_VERDICT_STATE"
    printf 'verdict_manifest\t%s\n' "$ACAS_PARITY_VERDICT_PATH"
    printf 'keep_going\t%s\n' "$ACAS_PARITY_KEEP_GOING"
  } > "$staging" 2>/dev/null || {
    rm -f -- "$staging" 2>/dev/null || true
    acas_parity_warn \
      "could not write $target, so no machine-readable result was published." \
      'The verdict printed above still stands.'
    return 0
  }
  chmod 600 "$staging" 2>/dev/null || true
  mv -f -- "$staging" "$target" 2>/dev/null || {
    rm -f -- "$staging" 2>/dev/null || true
    acas_parity_warn "could not publish $target."
    return 0
  }
  acas_parity_log "result        = $target (claim: $claim)"
  return 0
}

# THE RESUME GUARD (finding F-37).
#
# `--from N' exists so a fixed cause can be re-tried without repeating the stages that
# already succeeded. What it must NOT do is let stages from two different attempts be
# assembled into one verdict: the earlier attempt's COBOL capture beside this attempt's
# Python capture is a comparison of two different runs, and it can produce an empty diff
# that means nothing. Every stage that publishes an artifact records the run id
# (findings F-34, F-37), so a resume can be CHECKED rather than trusted.
#
# The rule: resuming past stage 1 requires that every artifact this run will build on
# carries THIS run's id. In practice that means the caller passes the same --run-id it
# used for the earlier stages. Absent that, the run is refused rather than silently
# mixing attempts -- and the refusal says exactly which id to pass.
acas_parity_assert_resume() {
  (( ACAS_PARITY_FROM > 1 )) || return 0

  local logs="$ACAS_OUT/run-logs/$ACAS_PARITY_SCENARIO"
  local -a mismatched=()
  local -a checked=()
  local artifact recorded name

  for artifact in \
    "$logs/seed-identity" \
    "$logs/cobol.run-status" \
    "$logs/python.run-status"
  do
    [[ -f "$artifact" ]] || continue
    name="${artifact##*/}"
    checked+=("$name")
    recorded=''
    # The second field of the `run_id' row. A tab-separated record, so cut on tab.
    recorded="$(awk -F'\t' '$1 == "run_id" { print $2; exit }' "$artifact" 2>/dev/null)" \
      || recorded=''
    if [[ "$recorded" != "$ACAS_PARITY_RUN_ID" ]]; then
      mismatched+=("$name records '${recorded:-<none>}'")
    fi
  done

  if (( ${#mismatched[@]} == 0 )); then
    if (( ${#checked[@]} > 0 )); then
      acas_parity_log \
        "resume check  = ${#checked[@]} prior artifact(s) all carry run id $ACAS_PARITY_RUN_ID"
    else
      acas_parity_note \
        "--from $ACAS_PARITY_FROM: no prior artifact was found under $logs, so there is nothing to mix with"
    fi
    return 0
  fi

  acas_parity_die "$EX_PRECONDITION" \
    "--from $ACAS_PARITY_FROM resumes a protocol whose earlier stages belong to a DIFFERENT attempt." \
    "  this run's id: $ACAS_PARITY_RUN_ID" \
    "  ${mismatched[*]}" \
    'Assembling stages from two attempts is not a comparison of one run: the earlier' \
    'attempt started from different seeded bytes and may have driven different' \
    'operations, so a diff between them -- empty or not -- says nothing about parity.' \
    'Either re-run the whole protocol without --from, or pass --run-id with the id the' \
    'earlier stages recorded so every artifact in this verdict belongs to one attempt.'
}

# THE REGISTRY AND THE IMPLEMENTATION MUST AGREE (finding F-16). The stage table is
# sourced from harness/parity_stages.sh and each row's body is a case arm in
# acas_parity_argv or acas_parity_run_stage. A row with no arm would be reported `ok'
# having done nothing, which is the worst possible failure for a protocol whose verdict
# depends on every stage having run. So the driver proves the correspondence before it
# drives anything: every stage number in the registry must build a command or be one of
# the two in-script checks.
acas_parity_assert_stages() {
  local entry stage
  local -a unimplemented=()
  for entry in "${ACAS_PARITY_STAGES[@]}"; do
    stage="${entry%%:*}"
    # Stage 9 is an in-script check and publishes no command; every other stage must.
    if [[ "$stage" == '9' ]]; then
      continue
    fi
    ACAS_PARITY_ARGV=()
    acas_parity_argv "$stage"
    if (( ${#ACAS_PARITY_ARGV[@]} == 0 )); then
      unimplemented+=("$stage")
    fi
  done
  ACAS_PARITY_ARGV=()
  (( ${#unimplemented[@]} == 0 )) || acas_parity_die "$EX_PRECONDITION" \
    "the stage registry lists ${#unimplemented[@]} stage(s) this driver does not implement: ${unimplemented[*]}." \
    'harness/parity_stages.sh is the canonical registry and acas_parity_argv is where' \
    'each row is driven; a listed stage with no command would be reported `ok'"'"' having' \
    'done nothing, and the verdict depends on every stage having actually run.'
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
  # THE PARITY CLAIM RESTS ON THE STAGE-10 MANIFEST, NOT ON "no stage failed"
  # (finding F-15). Read it before anything is printed, so the prose and the retained
  # result artifact below say the same thing.
  acas_parity_read_verdict
  acas_parity_log "verdict state = $ACAS_PARITY_VERDICT_STATE ($ACAS_PARITY_VERDICT_DETAIL)"

  local claim='no-claim'
  if (( first_failure == 0 && ACAS_PARITY_BEHAVIOURAL != 0 )); then
    claim='behavioural-difference'
    printf '\n    VERDICT: NO PARITY CLAIM. Every stage completed, but stage 6 reported a\n'
    printf '             BEHAVIOURAL difference (exit %s): an operation observed status\n' \
      "$ACAS_PARITY_BEHAVIOURAL"
    printf '             contradicted the one the scenario declared. The capture and the\n'
    printf '             diff were still taken -- deliberately, so they can show where --\n'
    printf '             but a contradicted disposition is a difference whatever the diff\n'
    printf '             says, so this is not the pass condition.\n'
  elif (( first_failure != 0 )); then
    claim='stage-failed'
    printf '\n    VERDICT: NO PARITY CLAIM. The run stopped at the first failing stage,\n'
    printf '             so no later stage rendered a verdict on evidence an earlier one\n'
    printf '             never produced.\n'
  else
    case "$ACAS_PARITY_VERDICT_STATE" in
      identical)
        claim='identical'
        printf '\n    VERDICT: the two states are IDENTICAL -- an empty diff, which is the\n'
        printf '             pass condition and the only one (AAP section 0.8.5).\n'
        printf '             Evidence: %s\n' "$ACAS_PARITY_VERDICT_PATH"
        printf '             (%s; run id %s)\n' \
          "$ACAS_PARITY_VERDICT_DETAIL" "$ACAS_PARITY_RUN_ID"
        ;;
      different)
        # Reachable when --keep-going carried the run past stage 10's non-zero exit.
        claim='different'
        printf '\n    VERDICT: the two states DIFFER. Stage %s compared them and found a\n' \
          "$ACAS_PARITY_VERDICT_STAGE"
        printf '             real behavioural difference: %s.\n' "$ACAS_PARITY_VERDICT_DETAIL"
        printf '             Interrogate the compiled oracle and record the resolution in\n'
        printf '             the migration'"'"'s ambiguity register (AAP section 0.6.6).\n'
        ;;
      incomplete)
        claim='incomplete'
        printf '\n    VERDICT: INCOMPLETE -- no parity claim. %s.\n' \
          "$ACAS_PARITY_VERDICT_DETAIL"
        printf '             The stages that ran did so successfully, which is NOT the same\n'
        printf '             as the two states being identical: only stage %s compares them,\n' \
          "$ACAS_PARITY_VERDICT_STAGE"
        printf '             and an empty diff from it is the one pass condition (AAP 0.8.5).\n'
        printf '             Run the full protocol to obtain a verdict.\n'
        ;;
      foreign)
        claim='foreign-verdict'
        printf '\n    VERDICT: NO PARITY CLAIM. %s.\n' "$ACAS_PARITY_VERDICT_DETAIL"
        printf '             A manifest from an earlier attempt cannot speak for this one:\n'
        printf '             it was built from different seeded bytes and possibly a\n'
        printf '             different operation list (finding F-37).\n'
        ;;
      *)
        claim='no-verdict'
        printf '\n    VERDICT: NO PARITY CLAIM. Every stage reported success, but %s.\n' \
          "$ACAS_PARITY_VERDICT_DETAIL"
        printf '             The pass condition is an empty diff RECORDED BY STAGE %s, not\n' \
          "$ACAS_PARITY_VERDICT_STAGE"
        printf '             the absence of a failure: with no manifest there is nothing to\n'
        printf '             cite as evidence, so no claim is made (rule R-6).\n'
        ;;
    esac
  fi

  acas_parity_publish_result "$claim" "$first_failure"
}

acas_parity_main() {
  # ACAS_REPO is asserted before it is used to locate the harness, so a missing
  # variable is reported as itself rather than as a missing script.
  ACAS_PARITY_HARNESS="${ACAS_REPO:-}/harness"
  ACAS_PARITY_PYTHON="${ACAS_PARITY_PYTHON:-python3}"

  acas_parity_parse_args "$@"
  acas_parity_assert_environment
  ACAS_PARITY_HARNESS="$ACAS_REPO/harness"

  # ⭐ ONE IDENTITY, RESOLVED ONCE AND BOUND TO EVERY STAGE (finding F-37). Not
  # derived from the clock: R-6 makes the run reproducible and F-41 keeps wall-clock
  # readings out of retained evidence, so a timestamped identity would put one back
  # into every record this run publishes.
  if [[ -z "$ACAS_PARITY_RUN_ID" ]]; then
    local uuid=''
    if [[ -r /proc/sys/kernel/random/uuid ]]; then
      read -r uuid < /proc/sys/kernel/random/uuid 2>/dev/null || uuid=''
      uuid="${uuid//-/}"
    fi
    if [[ -n "$uuid" ]]; then
      ACAS_PARITY_RUN_ID="parity-${uuid:0:16}"
    else
      ACAS_PARITY_RUN_ID="parity-$$-$RANDOM"
    fi
  fi
  [[ "$ACAS_PARITY_RUN_ID" =~ ^[A-Za-z0-9._-]{1,64}$ ]] || acas_parity_die "$EX_USAGE" \
    'the run id must be 1 to 64 characters of letters, digits, dot, underscore or hyphen.' \
    "  got: $ACAS_PARITY_RUN_ID"
  export ACAS_PARITY_RUN_ID

  printf 'harness/run_parity.sh -- the ten-stage parity protocol, in order, stopping at\n'
  printf 'the first failure. An EMPTY DIFF FROM STAGE 10 IS THE PASS CONDITION, and the\n'
  printf 'only one (Agent Action Plan section 0.8.5).\n\n'
  acas_parity_log "scenario file = $ACAS_PARITY_SCENARIO_FILE"
  acas_parity_log "scenario      = $ACAS_PARITY_SCENARIO"
  acas_parity_log "stages        = $ACAS_PARITY_FROM through $ACAS_PARITY_TO"
  acas_parity_log "run id        = $ACAS_PARITY_RUN_ID (bound to every stage that publishes an artifact)"
  acas_parity_log "python        = $ACAS_PARITY_PYTHON"
  acas_parity_log "ACAS_OUT      = $ACAS_OUT"
  if (( ACAS_PARITY_KEEP_GOING )); then
    acas_parity_note '--keep-going: a failure will NOT stop the run, and the verdict is not evidence (R-6)'
  fi

  #  THE ORACLE PROVENANCE GATE, BEFORE ANY STAGE RUNS -- and only when stage 2 is
  #  actually in range. A `--from 3' run compares captures that already exist and
  #  executes no compiled module, so demanding an attestation from it would refuse a
  #  legitimate re-diff for no gain. When stage 2 IS in range, the gate is
  #  unconditional: the compiled cycle is the specification, so this driver will not
  #  run it without knowing what it was built from.
  if (( ACAS_PARITY_FROM <= 2 && ACAS_PARITY_TO >= 2 )) && (( ! ACAS_PARITY_DRY_RUN )); then
    acas_parity_assert_oracle_attestation
  elif (( ACAS_PARITY_DRY_RUN )); then
    acas_parity_note 'dry run: the oracle provenance gate is reported, not applied'
  else
    acas_parity_note "stage 2 is out of range ($ACAS_PARITY_FROM..$ACAS_PARITY_TO), so no compiled module is executed and the oracle provenance gate does not apply"
  fi

  # Both checked BEFORE any stage runs: a registry row with no implementation, or a
  # resume that would mix two attempts, must stop the run rather than be discovered
  # from a verdict that has already been printed (findings F-16, F-37).
  acas_parity_assert_stages
  if (( ! ACAS_PARITY_DRY_RUN )); then
    acas_parity_assert_resume
  fi

  local entry stage label rc first_failure=0
  for entry in "${ACAS_PARITY_STAGES[@]}"; do
    stage="${entry%%:*}"
    label="${entry#*:}"
    if (( stage < ACAS_PARITY_FROM || stage > ACAS_PARITY_TO )); then
      continue
    fi

    if (( ACAS_PARITY_DRY_RUN )); then
      # Stage 2 needs no special case any more: it is one command carrying the whole
      # ordered operation list, exactly as acas_parity_argv builds it (F-12).
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

    # A behavioural difference is RECORDED and the protocol continues, so that the
    # capture, the normalisation and the diff all still happen and can say WHERE the
    # two cycles diverged (F-14, F-17).
    if acas_parity_is_behavioural "$stage" "$rc"; then
      ACAS_PARITY_BEHAVIOURAL="$rc"
      acas_parity_warn \
        "stage $stage reported a BEHAVIOURAL difference (exit $rc): an operation's observed status contradicted the scenario's declared one." \
        'The protocol CONTINUES so that the capture and the diff can show where the two' \
        'cycles diverged. It is remembered: the verdict cannot be "identical" after this,' \
        'whatever the diff says.'
      ACAS_PARITY_SUMMARY+=("$(printf '%-3s %-58s %s' "$stage" "$label" "exit $rc (BEHAVIOURAL -- continuing)")")
      continue
    fi

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
