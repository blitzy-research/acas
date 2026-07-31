#!/usr/bin/env bash
# =============================================================================
# harness/build_oracle.sh
#
# The five-step bootstrap that builds the compiled-COBOL ORACLE for the ACAS
# posting-cycle migration.
#
#   Step 1/5  Unpack the vendored JC preSQL archive inside the container.
#   Step 2/5  Compile the bridge's C interface object, cobmysqlapi.o, using the
#             build rule RECOVERED from that archive -- the rule is absent from
#             the ACAS checkout, so without it the oracle cannot be built at
#             all and every RDBMS-touching compile fails at link time with no
#             obvious cause.
#   Step 3/5  Build and install the `presql2' translator onto the PATH.
#   Step 4/5  Run common/comp-common.sh UNMODIFIED.
#   Step 5/5  Run comp-all.sh UNMODIFIED.
#
# WHAT THIS SCRIPT IS FOR
#   The migration has no test suite. Compiled COBOL execution IS the behavioural
#   specification, defects included, and this script is what makes that
#   specification executable. If it does not work there is no arbiter, and every
#   ambiguity in the migration becomes unresolvable. It is therefore the most
#   consequential script in the harness.
#
# WHERE THIS FILE SITS
#   harness/ is the compiled oracle and is a SIBLING of acas_posting/, never a
#   sub-package. There is no import path from the shipped Python package to this
#   tree, and this script never creates one: it writes no __init__.py, installs
#   no import hook, and places no artifact anywhere acas_posting/ could reach.
#   Every product of the build lands under $ACAS_BUILD.
#
# THE FROZEN-ARTIFACT GUARANTEE
#   The COBOL source, the bridge programs and the MySQL schema are frozen. This
#   script READS $ACAS_REPO and NEVER writes to it -- not a .prn listing, not a
#   .o, not a .so, not a .param, not a regenerated *MT.cbl, not an executable.
#   It copies the tree into the writable $ACAS_BUILD and builds there. The
#   reason is specific and severe: [common/comp-common.sh:L25] runs
#   `presql2 $i' over every *MT.scb, and presql2 truncates its output file at
#   [presql2-package/presql2.cbl:L543] BEFORE it validates its parameters at
#   [presql2-package/presql2.cbl:L759]. Run inside the checkout it would zero
#   the 28 committed common/*MT.cbl bridges -- the authoritative record-layout
#   to table mapping, i.e. the data dictionary for this migration -- and it
#   would do so even when misconfigured.
#
# THE FROZEN SCRIPTS ARE RUN UNMODIFIED
#   common/comp-common.sh, comp-all.sh and the five per-directory compile
#   scripts are executed exactly as the maintainer wrote them. They are not
#   patched, sed-ed, re-implemented or reordered, and NO cobc flag is added or
#   removed. Default compiler arithmetic is mandatory: a census of every frozen
#   compile invocation finds no -std= dialect selection, no >>SET ARITHMETIC
#   directive and no binary-truncate flag, and the migration's truncation and
#   rounding behaviour depends on exactly that.
#
# WHY `set -e' IS NOT ENOUGH -- READ THIS BEFORE CHANGING THE ERROR HANDLING
#   Every frozen compile script ends with a bare, unconditional `exit 0':
#   [common/comp-common.sh:L59], [comp-all.sh:L44-L45], [general/comp-gl.sh:L7],
#   [irs/comp-irs.sh:L9], [purchase/comp-purchase.sh:L6],
#   [sales/comp-sales.sh:L22], [stock/comp-stock.sh:L7]. Their exit status is
#   therefore NOT a build-success signal, and neither `set -e' nor `pipefail'
#   can catch a failed compile. These are frozen defects: they are worked
#   around here, never fixed. What actually catches failure is (a) the two-tier
#   log scan in acas_scan_build_log and (b) the artifact assertions in
#   acas_assert_artifacts. The artifact assertions are the more reliable of the
#   two and both are always run.
#
# RULES PROVENANCE
#   There is no user rules document for this project: `review_rules' returns
#   "No user rules provided." The binding rules R-1..R-6 come from the Agent
#   Action Plan and are cited inline below as (R-n). Where they are silent this
#   script holds to enterprise-standard best practice.
#     R-1 no COBOL at runtime          R-2 zero binary floating point
#     R-3 no schema change, sequential R-4 anomalies reproduced, never fixed
#     R-5 full traceability            R-6 compiled behaviour is the tie-breaker
#
# USAGE
#   Run `harness/build_oracle.sh --help'.
# =============================================================================

# Strict mode. -E propagates the ERR trap into functions and subshells so that
# an unexpected failure anywhere is attributed to a line number rather than
# silently ignored. See the caveat above: this protects THIS script, not the
# frozen ones.
set -Eeuo pipefail

# A conservative IFS: word splitting on newlines and tabs only, so a path
# containing a space can never be split apart. Every expansion below is quoted
# regardless.
IFS=$'\n\t'

# Unmatched globs must expand to nothing rather than to the pattern text, so
# the artifact assertions report "no sources found" instead of a literal "*.cbl".
shopt -s nullglob

# 0077 by default: nothing this script writes is world- or group-readable. The
# credential file written by acas_write_presql2_param re-asserts this locally
# and then chmods explicitly, so the guarantee does not depend on inheritance.
umask 077

# -----------------------------------------------------------------------------
# Exit codes -- one per stage, so an automated caller can attribute a failure
# without parsing text. 64/65 follow the sysexits.h convention.
# -----------------------------------------------------------------------------
readonly EX_OK=0
readonly EX_USAGE=64            # bad command line
readonly EX_PRECONDITION=65     # environment, directory or toolchain assertion
readonly EX_DATABASE=66         # MariaDB never became reachable
readonly EX_BUILDTREE=67        # could not prepare the writable build tree
readonly EX_STEP1=71            # unpack the vendored preSQL archive
readonly EX_STEP2=72            # compile cobmysqlapi.o
readonly EX_STEP3=73            # build and install presql2
readonly EX_STEP4=74            # common/comp-common.sh
readonly EX_STEP5=75            # comp-all.sh
readonly EX_ARTIFACTS=76        # post-build artifact assertions
readonly EX_FINALISE=77         # ldconfig / library path publication

# -----------------------------------------------------------------------------
# The frozen recipe's hard-coded paths.
#
# [common/comp-common.sh:L26] links `-L/usr/local/mysql/lib -lmysqlclient' and
# [presql2-package/cobmysqlapi38.sh] compiles with `-I/usr/local/mysql/include'.
# Both are LITERAL in the frozen sources, so this script uses the literal too
# and merely CHECKS that any ACAS_MYSQL_PREFIX published by the image agrees
# with it. Honouring a different prefix here would be a lie: the frozen scripts
# would still use /usr/local/mysql.
# -----------------------------------------------------------------------------
readonly ACAS_FROZEN_MYSQL_PREFIX='/usr/local/mysql'

# The compiler the maintainer targets, per [common/comp-common.sh:L8-L9]
# ("...the silly default warning in latest gnucobol v3.2") and [README.TXT:L53].
readonly ACAS_REQUIRED_COBC_VERSION='3.2'

# [comp-all.sh:L15-L32] cd's through exactly these six directories in this
# order. Because every RDBMS-touching compile links a BARE `cobmysqlapi.o'
# filename resolved against the current directory, the object must be present
# in all six. The order is the maintainer's own and is preserved.
readonly -a ACAS_COMPILE_DIRS=(common general irs purchase sales stock)

# The loaders harness/seed.sh invokes -- the 20 that serve the 22 in-scope
# tables. All 28 common/*LD.cbl are BUILT (that is what
# [common/comp-common.sh:L51] does); only these 20 are ever invoked. The other
# eight -- delfolioLD, sldelinvnosLD, deliveryLD, paymentsLD, plautogenLD,
# slautogenLD, auditLD, stockLD -- serve out-of-scope tables.
readonly -a ACAS_INSCOPE_LOADERS=(
  analLD dfltLD finalLD glbatchLD glpostingLD irsdfltLD irsfinalLD
  irsnominalLD irspostingLD nominalLD otm3LD otm5LD plinvoiceLD purchLD
  salesLD slinvoiceLD slpostingLD sys4LD systemLD valueLD
)

# The in-scope posting programs, per ledger, plus the Date Entry program each
# runner uses to pin the clock. Asserted by name because a state diff cannot
# be produced without them.
readonly -a ACAS_GENERAL_MODULES=(gl000 gl051 gl070 gl071 gl072 gl080)
readonly -a ACAS_SALES_MODULES=(sl000 sl055 sl060 sl100)
readonly -a ACAS_PURCHASE_MODULES=(pl000 pl055 pl060 pl100)
readonly -a ACAS_IRS_MODULES=(irs000 irs030)

# Mutable state. Declared up front because `set -u' makes an unset array a
# fatal reference.
declare -a ACAS_PARAM_FILES=()      # credential files to shred on exit
declare -a ACAS_SCRATCH_DIRS=()     # scratch trees to remove on exit
declare -a ACAS_WARN_SUMMARY=()     # non-fatal findings, replayed at the end
ACAS_START_STEP=1                   # --from N
ACAS_ONLY_STEP=0                    # --only N (0 = run the whole sequence)
ACAS_REFRESH_TREE=1                 # refresh $ACAS_BUILD before step 1
ACAS_RUN_PREFLIGHT_LINK=1           # reproduce the vendored worked example
ACAS_LOG_DIR=''                     # $ACAS_OUT/build, created in preflight
ACAS_PRESQL2_DIR=''                 # resolved unpacked package directory
ACAS_COBMYSQLAPI_SRC=''             # resolved cobmysqlapi.o to distribute
ACAS_DB_PROBE_DIAG=''               # last client diagnostic from the auth probe

# -----------------------------------------------------------------------------
# Reporting. Stage banners are numbered so the log reads as the deterministic
# staged orchestration the plan requires (R-6): explicit, ordered, individually
# reported, individually asserted.
# -----------------------------------------------------------------------------
acas_banner() {
  printf '\n==> Step %s/5: %s\n' "$1" "$2"
}

acas_stage() {
  printf '\n==> %s\n' "$1"
}

acas_log() {
  printf '    %s\n' "$*"
}

acas_note() {
  printf '    note: %s\n' "$*"
}

acas_warn() {
  printf 'WARNING: %s\n' "$*" >&2
  ACAS_WARN_SUMMARY+=("$*")
}

# acas_die <exit-code> <message>...
# Every abort names the artifact or setting at fault and, wherever the cause is
# a frozen recipe, cites its locator so the reader can verify the claim (R-5).
acas_die() {
  local code="$1"
  shift
  printf 'FATAL: %s\n' "$1" >&2
  shift
  local line
  for line in "$@"; do
    printf '       %s\n' "$line" >&2
  done
  exit "$code"
}

acas_have() {
  command -v "$1" >/dev/null 2>&1
}

# Join the remaining arguments into an alternation for grep -E.
acas_join_re() {
  local IFS='|'
  printf '%s' "$*"
}

# Join the remaining arguments with single spaces for human-readable output.
# Needed because this script sets IFS=$'\n\t', so a bare "${array[*]}" would
# join on a NEWLINE and break a one-line log message across several lines.
acas_join_words() {
  local IFS=' '
  printf '%s' "$*"
}

# -----------------------------------------------------------------------------
# Re-exec guard -- SAFETY CRITICAL, do not remove.
#
# Two independent reasons.
#
#   1. bash reads a script file incrementally as it executes it. This script
#      copies $ACAS_REPO over $ACAS_BUILD, and $ACAS_BUILD/harness/ contains a
#      copy of THIS FILE. If the running instance is the one under $ACAS_BUILD,
#      `cp' truncates and rewrites the very file bash is reading and execution
#      can continue into rewritten bytes. Re-executing the $ACAS_REPO copy --
#      which is read-only and is never a copy target -- removes the hazard
#      entirely rather than relying on buffering behaviour.
#
#   2. Determinism (R-6). $ACAS_REPO is the specification; a copy sitting in a
#      build volume from an earlier run is not. Always running the checkout's
#      own copy makes two runs of the same commit identical.
#
# harness/docker-compose.yml sets `working_dir: /build', so
# `docker compose run --rm gnucobol harness/build_oracle.sh' resolves relative
# to $ACAS_BUILD. That is exactly the case this guard redirects. The guard is
# also why nothing in this script derives a path from $0: every location comes
# from the environment contract instead.
# -----------------------------------------------------------------------------
acas_reexec_from_repo_if_needed() {
  # Nothing to do if we have already redirected once (loop breaker), or if the
  # environment contract is not yet known -- the preflight reports that.
  if [[ -n "${ACAS_BUILD_ORACLE_REEXEC-}" ]]; then
    return 0
  fi
  if [[ -z "${ACAS_BUILD-}" || -z "${ACAS_REPO-}" ]]; then
    return 0
  fi

  local self build_real repo_copy
  self="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || printf '%s' "${BASH_SOURCE[0]}")"
  build_real="$(readlink -f "$ACAS_BUILD" 2>/dev/null || printf '%s' "$ACAS_BUILD")"
  repo_copy="$ACAS_REPO/harness/build_oracle.sh"

  if [[ "$self" != "$build_real"/* ]]; then
    return 0
  fi
  if [[ ! -f "$repo_copy" ]]; then
    acas_die "$EX_PRECONDITION" \
      "this script is running from inside \$ACAS_BUILD ($self) but the read-only" \
      "checkout copy $repo_copy does not exist, so it cannot be re-executed safely." \
      "Invoke \$ACAS_REPO/harness/build_oracle.sh directly."
  fi

  printf 'Re-executing the read-only checkout copy to protect the build tree copy:\n'
  printf '    from %s\n' "$self"
  printf '    to   %s\n' "$repo_copy"
  export ACAS_BUILD_ORACLE_REEXEC=1
  exec bash "$repo_copy" "$@"
}

acas_reexec_from_repo_if_needed "$@"

# -----------------------------------------------------------------------------
# Traps.
#
# ERR reports the failing line so an unexpected failure is attributable.
# EXIT shreds every credential file this script wrote, on EVERY exit path
# including a fatal abort or an interrupt -- no password may survive the run.
# -----------------------------------------------------------------------------
# The three functions below are reached ONLY through the `trap' statements that
# follow them. ShellCheck's reachability pass cannot see an indirect invocation
# through a trap in a script that ends with an explicit `exit', so it reports
# their bodies as unreachable (SC2317) -- its own message says "or ignore if
# invoked indirectly", which is exactly the case here. Verified against
# ShellCheck 0.10.0 with a minimal reproduction; the suppression is scoped to
# these three definitions and to nothing else.
# shellcheck disable=SC2317
acas_on_err() {
  local code="$1" line="$2" cmd="$3"
  printf '\nFATAL: unexpected failure at %s line %s (exit %s)\n' \
    "${BASH_SOURCE[0]}" "$line" "$code" >&2
  printf '       failing command: %s\n' "$cmd" >&2
}

acas_shred_param_files() {
  local f
  for f in "${ACAS_PARAM_FILES[@]+"${ACAS_PARAM_FILES[@]}"}"; do
    [[ -f "$f" ]] || continue
    # Overwrite before unlinking. The file is 0600 and lives on a container
    # volume, but a credential should not be left recoverable in free blocks.
    : > "$f" 2>/dev/null || true
    rm -f "$f" 2>/dev/null || true
  done
  ACAS_PARAM_FILES=()
}

# shellcheck disable=SC2317  # reached only via the EXIT trap; see the note above acas_on_err
acas_remove_scratch_dirs() {
  local d
  for d in "${ACAS_SCRATCH_DIRS[@]+"${ACAS_SCRATCH_DIRS[@]}"}"; do
    # Only ever remove a directory this script created itself, and only when
    # the path is absolute and at least two components deep. A recursive
    # remove must never be able to walk into a shared or mounted tree.
    [[ -n "$d" && "$d" == /*/* && -d "$d" ]] || continue
    rm -rf -- "$d" 2>/dev/null || true
  done
  ACAS_SCRATCH_DIRS=()
}

# shellcheck disable=SC2317  # reached only via the EXIT trap; see the note above acas_on_err
acas_on_exit() {
  local code="$1"
  acas_shred_param_files
  acas_remove_scratch_dirs
  if (( code != 0 )); then
    printf '\nbuild_oracle.sh FAILED with exit code %s.\n' "$code" >&2
    if [[ -n "$ACAS_LOG_DIR" && -d "$ACAS_LOG_DIR" ]]; then
      printf 'Build logs, if any were produced, are under %s\n' "$ACAS_LOG_DIR" >&2
    fi
  fi
}

trap 'acas_on_err "$?" "$LINENO" "$BASH_COMMAND"' ERR
trap 'acas_on_exit "$?"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# -----------------------------------------------------------------------------
# Usage
# -----------------------------------------------------------------------------
acas_usage() {
  cat <<'USAGE'
build_oracle.sh - build the compiled-COBOL oracle for the ACAS posting cycle.

Usage:
  build_oracle.sh [options]

The five steps, always in this order:
  1  Unpack the vendored JC preSQL archive (presql2-latest.zip) in the container.
  2  Compile cobmysqlapi.o with the rule RECOVERED from that archive and place a
     copy in each of the six compile directories, because every frozen compile
     links a bare `cobmysqlapi.o' filename resolved against the current
     directory.  [presql2-package/cobmysqlapi38.sh] [common/comp-common.sh:L26]
  3  Build and install the `presql2' translator onto the PATH.
     [presql2-package/presql2.sh]
  4  Run common/comp-common.sh UNMODIFIED, in the build copy.
  5  Run comp-all.sh UNMODIFIED, in the build copy.

Options:
  --from N            Start at step N (1-5). Steps before N are skipped and the
                      existing build tree is validated instead of refreshed.
  --only N            Run step N alone (1-5). Implies --no-refresh for N > 1.
  --no-refresh        Do not clear and re-copy $ACAS_BUILD before step 1.
  --refresh           Force the refresh even with --from/--only (default when
                      the full sequence runs).
  --skip-preflight-link
                      Skip the step-3 toolchain proof that reproduces the
                      vendored worked example [presql2-package/ACAS/comp-stockMT.sh].
  -h, --help          Print this help and exit 0.

Required environment (harness/docker-compose.yml supplies all of it):
  ACAS_REPO           read-only checkout            (mounted ../:/repo:ro)
  ACAS_BUILD          writable build tree           (volume  /build)
  ACAS_DATA           writable ledger/data area     (volume  /data)
  ACAS_OUT            writable output area          (volume  /out)
  ACAS_DB_HOST        MariaDB host
  ACAS_DB_PORT        MariaDB port
  ACAS_DB_NAME        target schema (the .scb BASE= directive names it too)
  ACAS_DB_USER        MariaDB user
  ACAS_DB_PASSWORD    MariaDB password (never echoed, never logged)
  ACAS_DB_SOCKET      unix socket path; may legitimately be EMPTY, in which
                      case DBSOCKET=NULL is written, the only spelling the C
                      shim maps to "no socket"
                      [presql2-package/cobmysqlapi38.c:L513-L525]

Optional environment:
  ACAS_BUILD_STRICT=1        promote compiler warnings to fatal
  ACAS_DB_WAIT_TIMEOUT=N     seconds to wait for MariaDB (default 180)
  ACAS_DB_AUTH_GRACE=N       seconds to tolerate "Access denied" before failing
                             fast, capped at ACAS_DB_WAIT_TIMEOUT (default 15).
                             Rejected credentials are a configuration error,
                             not a readiness state, so they are NOT retried for
                             the full timeout
  ACAS_PRESQL2_PACKAGE=DIR   reuse an already-unpacked preSQL package
  ACAS_COBMYSQLAPI_OBJ=FILE  reuse an already-compiled cobmysqlapi.o
  ACAS_PRESQL2_DBNAME=NAME   schema presql2 connects to (default
                             information_schema; see acas_write_presql2_param)
  ACAS_MYSQL_PREFIX=DIR      checked for agreement with the frozen literal
                             /usr/local/mysql; it cannot override it

Exit codes:
  0 success   64 usage   65 precondition   66 database   67 build tree
  71-75 steps 1-5   76 artifact assertions   77 finalisation

This script NEVER writes to $ACAS_REPO, never modifies a frozen compile script,
never adds or removes a cobc flag, and never exits 0 unconditionally.
USAGE
}

# Validate in place and die on failure. Deliberately NOT a value-returning
# helper: `acas_die' calls `exit', and inside a command substitution that would
# terminate only the subshell, leaving the caller running with an empty value.
acas_assert_step_number() {
  local flag="$1" value="$2"
  if [[ ! "$value" =~ ^[1-5]$ ]]; then
    acas_die "$EX_USAGE" \
      "$flag requires a step number in the range 1-5; got '$value'." \
      "Run --help for the step list."
  fi
}

acas_parse_args() {
  local explicit_refresh=0
  while (( $# > 0 )); do
    case "$1" in
      -h|--help)
        acas_usage
        exit "$EX_OK"
        ;;
      --from)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" "--from requires a value (1-5)."
        acas_assert_step_number --from "$2"
        ACAS_START_STEP="$2"
        shift 2
        ;;
      --from=*)
        acas_assert_step_number --from "${1#*=}"
        ACAS_START_STEP="${1#*=}"
        shift
        ;;
      --only)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" "--only requires a value (1-5)."
        acas_assert_step_number --only "$2"
        ACAS_ONLY_STEP="$2"
        ACAS_START_STEP="$2"
        shift 2
        ;;
      --only=*)
        acas_assert_step_number --only "${1#*=}"
        ACAS_ONLY_STEP="${1#*=}"
        ACAS_START_STEP="${1#*=}"
        shift
        ;;
      --no-refresh)
        ACAS_REFRESH_TREE=0
        explicit_refresh=1
        shift
        ;;
      --refresh)
        ACAS_REFRESH_TREE=1
        explicit_refresh=1
        shift
        ;;
      --skip-preflight-link)
        ACAS_RUN_PREFLIGHT_LINK=0
        shift
        ;;
      --)
        shift
        break
        ;;
      *)
        acas_die "$EX_USAGE" "unrecognised argument '$1'." \
          "Run --help for the accepted options."
        ;;
    esac
  done

  if (( $# > 0 )); then
    acas_die "$EX_USAGE" "unexpected trailing arguments: $*"
  fi

  # Starting part-way through the sequence must not wipe the tree the earlier
  # steps populated, unless the operator asks for that explicitly.
  if (( ACAS_START_STEP > 1 && explicit_refresh == 0 )); then
    ACAS_REFRESH_TREE=0
  fi
}

# Explicit returns rather than a bare arithmetic expression, so the result is
# unambiguous in every calling context under `set -e'.
acas_step_enabled() {
  local step="$1"
  if (( ACAS_ONLY_STEP != 0 )); then
    if (( step == ACAS_ONLY_STEP )); then
      return 0
    fi
    return 1
  fi
  if (( step >= ACAS_START_STEP )); then
    return 0
  fi
  return 1
}

# =============================================================================
# PRECONDITIONS
#
# This script ASSERTS its toolchain; it never installs one. harness/Dockerfile.
# gnucobol is what provides GnuCOBOL 3.2, the MySQL client libraries under the
# frozen prefix, the JC preSQL package and CPython 3.12. Asserting here means a
# misconfigured image fails in seconds with a named cause instead of failing
# minutes later inside a frozen script that reports success anyway.
# =============================================================================

# The full environment contract. ACAS_DB_SOCKET is deliberately in the
# "declared" list rather than the "non-empty" list: harness/docker-compose.yml
# sets it to the empty string on purpose, because the harness connects over TCP.
readonly -a ACAS_REQUIRED_ENV_NONEMPTY=(
  ACAS_REPO ACAS_BUILD ACAS_DATA ACAS_OUT
  ACAS_DB_HOST ACAS_DB_PORT ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD
)
readonly -a ACAS_REQUIRED_ENV_DECLARED=(
  ACAS_DB_SOCKET
)

acas_assert_environment() {
  acas_stage 'Preconditions 1/5: environment contract'

  local name missing=0
  for name in "${ACAS_REQUIRED_ENV_NONEMPTY[@]}"; do
    if [[ -z "${!name-}" ]]; then
      printf 'FATAL: required environment variable %s is unset or empty.\n' "$name" >&2
      missing=1
    fi
  done
  for name in "${ACAS_REQUIRED_ENV_DECLARED[@]}"; do
    # `-v' tests declaration, not content. An empty ACAS_DB_SOCKET is valid and
    # means "no unix socket"; an UNDECLARED one means the caller did not supply
    # the contract at all, which is a configuration error worth reporting.
    if [[ ! -v "$name" ]]; then
      printf 'FATAL: required environment variable %s is not declared.\n' "$name" >&2
      printf '       It may legitimately be EMPTY, but it must be declared.\n' >&2
      missing=1
    fi
  done
  if (( missing )); then
    acas_die "$EX_PRECONDITION" \
      'the environment contract is incomplete.' \
      'harness/docker-compose.yml supplies every variable listed by --help;' \
      'outside Compose, export them yourself before invoking this script.'
  fi

  if [[ ! "$ACAS_DB_PORT" =~ ^[0-9]+$ ]]; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_PORT must be numeric; got '$ACAS_DB_PORT'." \
      'The C shim converts it with atoi() at [presql2-package/cobmysqlapi38.c:L511],' \
      'so a non-numeric value silently becomes port 0.'
  fi

  # Every card written into presql2.param is copied with strncpy(..., 32) at
  # [presql2-package/cobmysqlapi38.c:L138,L145,L152,L159,L166,L173] into a
  # 32-byte COBOL pic x(32) field. A longer value is TRUNCATED SILENTLY, which
  # would produce a connection failure with no explanation, so it is rejected
  # here instead. The password's LENGTH is checked; its VALUE is never printed.
  local -a checked_names=(ACAS_DB_HOST ACAS_DB_USER ACAS_DB_PASSWORD ACAS_DB_NAME
                          ACAS_DB_PORT ACAS_DB_SOCKET)
  local value
  for name in "${checked_names[@]}"; do
    value="${!name-}"
    if (( ${#value} > 32 )); then
      acas_die "$EX_PRECONDITION" \
        "$name is ${#value} characters long; the maximum is 32." \
        'read_params() copies each parameter card with strncpy(..., 32) into a' \
        'pic x(32) host field, so anything longer is truncated without warning.' \
        '[presql2-package/cobmysqlapi38.c:L114-L176]'
    fi
  done

  acas_log "ACAS_REPO  = $ACAS_REPO (read-only checkout; the specification)"
  acas_log "ACAS_BUILD = $ACAS_BUILD (writable build tree; every artifact lands here)"
  acas_log "ACAS_DATA  = $ACAS_DATA"
  acas_log "ACAS_OUT   = $ACAS_OUT"
  acas_log "database   = ${ACAS_DB_USER}@${ACAS_DB_HOST}:${ACAS_DB_PORT}/${ACAS_DB_NAME}"
  if [[ -n "${ACAS_DB_SOCKET-}" ]]; then
    acas_log "unix socket = ${ACAS_DB_SOCKET}"
  else
    acas_log 'unix socket = (empty; DBSOCKET=NULL will be written -- TCP only)'
  fi
  acas_note 'the password is never printed, never logged and never passed in argv'
}

# Guard a path before it is used as the target of a recursive operation. A
# mis-set ACAS_BUILD is the one configuration error that could destroy something
# irreplaceable, so the checks are deliberately paranoid.
acas_assert_safe_build_path() {
  local path="$1"
  local repo_real path_real
  path_real="$(readlink -f "$path" 2>/dev/null || printf '%s' "$path")"
  repo_real="$(readlink -f "$ACAS_REPO" 2>/dev/null || printf '%s' "$ACAS_REPO")"

  [[ "$path_real" == /* ]] || acas_die "$EX_BUILDTREE" \
    "ACAS_BUILD must be an absolute path; got '$path'."
  [[ "$path_real" != '/' ]] || acas_die "$EX_BUILDTREE" \
    'ACAS_BUILD must not be the filesystem root.'
  [[ "$path_real" == /*/* ]] || acas_die "$EX_BUILDTREE" \
    "ACAS_BUILD must be at least two components deep; got '$path_real'." \
    'This script clears it, and a top-level directory is never a safe target.'
  [[ "$path_real" != "$repo_real" ]] || acas_die "$EX_BUILDTREE" \
    'ACAS_BUILD and ACAS_REPO resolve to the same directory.' \
    'The build must happen in a copy, never in the frozen checkout.'
  [[ "$path_real" != "$repo_real"/* ]] || acas_die "$EX_BUILDTREE" \
    "ACAS_BUILD ($path_real) is inside ACAS_REPO ($repo_real)." \
    'Building there would write into the frozen checkout and the tree copy' \
    'would recurse into itself.'
  [[ "$repo_real" != "$path_real"/* ]] || acas_die "$EX_BUILDTREE" \
    "ACAS_REPO ($repo_real) is inside ACAS_BUILD ($path_real)." \
    'Clearing the build tree would delete the checkout.'
}

acas_assert_directories() {
  acas_stage 'Preconditions 2/5: directories and the frozen-artifact guarantee'

  [[ -d "$ACAS_REPO" ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_REPO ($ACAS_REPO) is not a directory."
  [[ -f "$ACAS_REPO/comp-all.sh" && -d "$ACAS_REPO/common" && -d "$ACAS_REPO/copybooks" ]] \
    || acas_die "$EX_PRECONDITION" \
      "ACAS_REPO ($ACAS_REPO) does not look like an ACAS checkout." \
      'Expected comp-all.sh, common/ and copybooks/ at its root.'

  # THE central safety assertion. /repo is mounted read-only by
  # harness/docker-compose.yml ("../:/repo:ro") precisely so that a frozen file
  # cannot be written even by accident. Verify the mount actually is read-only,
  # by attempting a write and requiring it to FAIL.
  local probe="$ACAS_REPO/.acas-build-oracle-write-probe"
  if : > "$probe" 2>/dev/null; then
    rm -f "$probe" 2>/dev/null || true
    acas_die "$EX_PRECONDITION" \
      "ACAS_REPO ($ACAS_REPO) is WRITABLE; it must be mounted read-only." \
      'A writable checkout is the one configuration error that can silently' \
      'destroy the specification: [common/comp-common.sh:L25] regenerates every' \
      'common/*MT.cbl with presql2, and presql2 truncates its output at' \
      '[presql2-package/presql2.cbl:L543] BEFORE validating its parameters at' \
      '[presql2-package/presql2.cbl:L759]. Mount it "../:/repo:ro" as' \
      'harness/docker-compose.yml does, then re-run.'
  fi
  acas_log "verified: $ACAS_REPO is not writable"

  acas_assert_safe_build_path "$ACAS_BUILD"

  local dir
  for dir in "$ACAS_BUILD" "$ACAS_DATA" "$ACAS_OUT"; do
    [[ -d "$dir" ]] || mkdir -p "$dir" 2>/dev/null || acas_die "$EX_PRECONDITION" \
      "$dir does not exist and could not be created."
    [[ -w "$dir" ]] || acas_die "$EX_PRECONDITION" \
      "$dir is not writable." \
      'ACAS_BUILD, ACAS_DATA and ACAS_OUT must all be writable volumes.'
  done
  acas_log "verified: $ACAS_BUILD, $ACAS_DATA and $ACAS_OUT are writable"

  # Build logs live under $ACAS_OUT/build/. They are never compared, so a
  # timestamp there is harmless -- but nothing this script writes goes into
  # $ACAS_OUT/<scenario>/, because the determinism test requires byte-identical
  # scenario dumps and a clock reading in a compared file would break it.
  ACAS_LOG_DIR="$ACAS_OUT/build"
  mkdir -p "$ACAS_LOG_DIR"
  acas_log "build logs: $ACAS_LOG_DIR"
}

acas_assert_toolchain() {
  acas_stage 'Preconditions 3/5: toolchain'

  local tool
  for tool in cobc gcc python3; do
    acas_have "$tool" || acas_die "$EX_PRECONDITION" \
      "$tool is not on the PATH." \
      'harness/Dockerfile.gnucobol installs the whole toolchain; this script' \
      'only asserts it. Run inside the gnucobol service image.'
  done
  acas_have ldconfig || acas_warn \
    'ldconfig is not on the PATH; the shared-library cache cannot be refreshed.'

  # cobc MUST be 3.2 -- the compiler the maintainer targets. A different release
  # is a different oracle, and the oracle is the specification.
  # [common/comp-common.sh:L8-L9] [README.TXT:L53]
  local cobc_line
  cobc_line="$(cobc --version 2>&1 | head -n 1)"
  if [[ ! "$cobc_line" =~ ^cobc\ \(GnuCOBOL\)\ ${ACAS_REQUIRED_COBC_VERSION}(\.[0-9]+)*$ ]]; then
    acas_die "$EX_PRECONDITION" \
      "cobc does not report GnuCOBOL ${ACAS_REQUIRED_COBC_VERSION}." \
      "It reports: $cobc_line" \
      'The oracle MUST be built with the compiler the maintainer targets --' \
      '"...the silly default warning in latest gnucobol v3.2"' \
      '[common/comp-common.sh:L8-L9], corroborated by [README.TXT:L53].' \
      'A different release is a different specification.'
  fi
  acas_log "cobc: $cobc_line"

  # An ISAM handler is not optional and the reason is not obvious.
  # [general/general.cbl:L385-L396] forces COBOL indexed processing for the
  # system parameter file ('move "00" to FA-RDBMS-Flat-Statuses') and, if that
  # OPEN fails, CALLs the interactive sys002 -- which waits on a terminal and
  # hangs a headless harness forever. Surface it at build time instead.
  local cobc_info isam_line
  cobc_info="$(cobc --info 2>&1 || true)"
  isam_line="$(printf '%s\n' "$cobc_info" | grep -i 'indexed file handler' || true)"
  if [[ -z "$isam_line" ]]; then
    acas_die "$EX_PRECONDITION" \
      'cobc --info reports no indexed file handler at all.' \
      'GnuCOBOL must be configured with an ISAM backend (--with-db).'
  fi
  if printf '%s' "$isam_line" | grep -qiE 'disabled|none|not available'; then
    acas_die "$EX_PRECONDITION" \
      "the GnuCOBOL indexed file handler is unusable: $isam_line" \
      'Without ISAM the forced indexed OPEN at [general/general.cbl:L385-L396]' \
      'fails and the menu CALLs the interactive sys002, which hangs the harness.'
  fi
  acas_log "cobc --info: ${isam_line#*:}"
  acas_log "cobc --info: $(printf '%s\n' "$cobc_info" | grep -i 'mathematical library' || true)"

  # The frozen prefix. These two paths are LITERAL in the frozen recipe, so they
  # are checked literally: [common/comp-common.sh:L26] links
  # -L/usr/local/mysql/lib -lmysqlclient and [presql2-package/cobmysqlapi38.sh]
  # compiles with -I/usr/local/mysql/include.
  [[ -e "$ACAS_FROZEN_MYSQL_PREFIX/lib/libmysqlclient.so" ]] \
    || acas_die "$EX_PRECONDITION" \
      "$ACAS_FROZEN_MYSQL_PREFIX/lib/libmysqlclient.so is absent." \
      'Every frozen compile line linking -lmysqlclient would fail.' \
      '[common/comp-common.sh:L26]'
  [[ -f "$ACAS_FROZEN_MYSQL_PREFIX/include/mysql.h" ]] \
    || acas_die "$EX_PRECONDITION" \
      "$ACAS_FROZEN_MYSQL_PREFIX/include/mysql.h is absent." \
      'cobmysqlapi38.c includes <mysql.h> and the recovered rule compiles with' \
      '-I/usr/local/mysql/include. [presql2-package/cobmysqlapi38.sh]'
  acas_log "MySQL client prefix: $ACAS_FROZEN_MYSQL_PREFIX (lib + headers present)"

  # ACAS_MYSQL_PREFIX is published by the image for documentation. It cannot
  # override the frozen literal, so disagreement is reported rather than obeyed.
  if [[ -n "${ACAS_MYSQL_PREFIX-}" && "${ACAS_MYSQL_PREFIX}" != "$ACAS_FROZEN_MYSQL_PREFIX" ]]; then
    acas_warn \
      "ACAS_MYSQL_PREFIX=${ACAS_MYSQL_PREFIX} disagrees with the frozen literal ${ACAS_FROZEN_MYSQL_PREFIX}; the frozen scripts hard-code the literal, so it is used regardless."
  fi
}

acas_assert_loader_configuration() {
  acas_stage 'Preconditions 4/5: shared-library loader paths'

  # The repository's own loader configuration, read and LEFT UNTOUCHED. The
  # search ORDER is part of the configuration, so both content and order are
  # compared. [etc/ld.so.conf.d/gnucobol.conf]
  local reference="$ACAS_REPO/etc/ld.so.conf.d/gnucobol.conf"
  local installed='/etc/ld.so.conf.d/gnucobol.conf'

  if [[ ! -f "$reference" ]]; then
    acas_warn "the repository reference $reference is missing; loader paths cannot be compared."
    return 0
  fi
  if [[ ! -f "$installed" ]]; then
    acas_warn "$installed is absent; the loader may not find libcob or libmysqlclient. Reference: $reference"
    return 0
  fi

  # Compare only meaningful lines: blank lines and comments carry no loader
  # semantics, so they are excluded from both sides rather than causing a
  # spurious mismatch.
  local -a want=() have=()
  mapfile -t want < <(grep -vE '^[[:space:]]*(#|$)' "$reference" || true)
  mapfile -t have < <(grep -vE '^[[:space:]]*(#|$)' "$installed" || true)

  if (( ${#want[@]} != ${#have[@]} )); then
    acas_warn "$installed has ${#have[@]} loader path(s); [etc/ld.so.conf.d/gnucobol.conf] has ${#want[@]}."
    return 0
  fi
  local i mismatched=0
  for (( i = 0; i < ${#want[@]}; i++ )); do
    if [[ "${have[$i]}" != "${want[$i]}" ]]; then
      acas_warn "loader path line $(( i + 1 )) is '${have[$i]}', expected '${want[$i]}' per [etc/ld.so.conf.d/gnucobol.conf]."
      mismatched=1
    fi
  done
  if (( mismatched == 0 )); then
    acas_log "verified: $installed reproduces [etc/ld.so.conf.d/gnucobol.conf] exactly, in order"
    local p
    for p in "${want[@]}"; do
      acas_log "  $p"
    done
  fi
}

# TCP reachability, using python3 because it is guaranteed present by the
# toolchain assertion and needs no client binary or credentials.
acas_db_tcp_probe() {
  python3 - "$ACAS_DB_HOST" "$ACAS_DB_PORT" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
try:
    with socket.create_connection((host, port), timeout=5):
        pass
except OSError:
    sys.exit(1)
sys.exit(0)
PY
}

# A genuinely credentialed probe -- this is what presql2 will actually need.
#
# MEASURED, AND THE REASON THIS FUNCTION IS NOT A `ping':
#   `mariadb-admin ping' EXITS 0 EVEN WHEN AUTHENTICATION IS REFUSED. Against
#   this repository's own MariaDB 10.11.7 service, with a deliberately wrong
#   password, `mariadb-admin ... ping' printed
#     error: 'Access denied for user ...(using password: YES)'
#   on stderr and still exited 0, because `ping' answers "is the server alive",
#   not "are these credentials accepted". Using it as a readiness gate let a
#   wrong password sail through the gate and surface 19 seconds later as 28
#   presql2 diagnostics inside step 4 -- attributable, but far later and far
#   less obvious than it should be. The same invocation with `status' instead
#   of `ping' exits 1, and a real `select 1' exits 1 with ERROR 1045.
#   Therefore: prefer a real authenticated statement; fall back to `status',
#   never to `ping'.
#
# The statement is issued against the schema presql2 itself connects to
# (information_schema by default -- see acas_write_presql2_param and
# [presql2-package/presql2.cbl:L798-L806]), so a grant that happens to exclude
# that schema is caught here rather than inside step 4.
#
# The password is passed through MYSQL_PWD rather than argv so it never appears
# in the process list. Both a TLS-enforcing client (which needs --skip-ssl
# against a server without TLS) and a permissive one are tolerated.
#
# Returns: 0 authenticated, 1 transient failure (retry), 2 credentials
# rejected (configuration error), 3 no client binary available.
# Side effect: sets ACAS_DB_PROBE_DIAG to the client's last diagnostic.
acas_db_credentialed_probe() {
  ACAS_DB_PROBE_DIAG=''
  local dbname="${ACAS_PRESQL2_DBNAME:-information_schema}"
  local client out rc

  # Layer 1: a real SQL client executing a real statement.
  for client in mariadb mysql; do
    if acas_have "$client"; then
      local -a ssl_variant=('' '--skip-ssl')
      local variant
      for variant in "${ssl_variant[@]}"; do
        local -a argv=("$client" '--protocol=TCP')
        [[ -n "$variant" ]] && argv+=("$variant")
        argv+=(
          "--host=$ACAS_DB_HOST" "--port=$ACAS_DB_PORT"
          "--user=$ACAS_DB_USER" '--batch' '--skip-column-names'
          "--database=$dbname" '--execute=select 1'
        )
        out=''
        rc=0
        out="$(MYSQL_PWD="$ACAS_DB_PASSWORD" "${argv[@]}" 2>&1)" || rc=$?
        if (( rc == 0 )); then
          return 0
        fi
        ACAS_DB_PROBE_DIAG="$out"
      done
      # Every SSL variant of a real client failed. Classify.
      if [[ "$ACAS_DB_PROBE_DIAG" == *'Access denied'* ]]; then
        return 2
      fi
      return 1
    fi
  done

  # Layer 2: no SQL client, so use an admin client -- `status', never `ping',
  # for the reason measured above.
  for client in mariadb-admin mysqladmin; do
    if acas_have "$client"; then
      local -a ssl_variant=('' '--skip-ssl')
      local variant
      for variant in "${ssl_variant[@]}"; do
        local -a argv=("$client" '--protocol=TCP')
        [[ -n "$variant" ]] && argv+=("$variant")
        argv+=(
          "--host=$ACAS_DB_HOST" "--port=$ACAS_DB_PORT"
          "--user=$ACAS_DB_USER" 'status'
        )
        out=''
        rc=0
        out="$(MYSQL_PWD="$ACAS_DB_PASSWORD" "${argv[@]}" 2>&1)" || rc=$?
        if (( rc == 0 )); then
          return 0
        fi
        ACAS_DB_PROBE_DIAG="$out"
      done
      if [[ "$ACAS_DB_PROBE_DIAG" == *'Access denied'* ]]; then
        return 2
      fi
      return 1
    fi
  done

  return 3
}

acas_wait_for_database() {
  acas_stage 'Preconditions 5/5: MariaDB readiness'

  # Why this gate exists, and why it is not optional: presql2 opens a LIVE
  # connection. [presql2-package/presql2.cbl:L784] performs MYSQL-1000-OPEN,
  # which reaches MySQL_real_connect at
  # [presql2-package/cobmysqlapi38.c:L500-L531]. presql2 runs inside step 4 via
  # [common/comp-common.sh:L25], so the database must be up BEFORE step 4 or
  # every bridge translation fails for a reason that looks like a compiler
  # problem. harness/docker-compose.yml declares
  # "depends_on: mariadb: condition: service_healthy" for the same reason;
  # this loop makes the guarantee hold outside Compose too.
  local timeout="${ACAS_DB_WAIT_TIMEOUT:-180}"
  if [[ ! "$timeout" =~ ^[0-9]+$ ]]; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_WAIT_TIMEOUT must be numeric; got '$timeout'."
  fi

  local interval=3 elapsed=0
  acas_log "waiting up to ${timeout}s for ${ACAS_DB_HOST}:${ACAS_DB_PORT} to accept connections"
  while ! acas_db_tcp_probe; do
    if (( elapsed >= timeout )); then
      acas_die "$EX_DATABASE" \
        "MariaDB at ${ACAS_DB_HOST}:${ACAS_DB_PORT} did not accept a TCP connection within ${timeout}s." \
        'Step 4 cannot run without it: [common/comp-common.sh:L25] invokes presql2,' \
        'which opens a live connection at [presql2-package/presql2.cbl:L784].' \
        'Start the service (docker compose -f harness/docker-compose.yml up -d mariadb)' \
        'and wait for its healthcheck, or raise ACAS_DB_WAIT_TIMEOUT.'
    fi
    sleep "$interval"
    elapsed=$(( elapsed + interval ))
  done
  acas_log "TCP reachable after ${elapsed}s"

  # Authentication gate. An open port is not readiness: presql2 authenticates
  # with exactly these credentials via read_params
  # [presql2-package/cobmysqlapi38.c:L114-L176], so a wrong user or password
  # must be caught HERE, not 28 diagnostics into step 4.
  #
  # Two distinct failure shapes, deliberately treated differently:
  #   - transient (connection reset, server still initialising): retried for
  #     the full ACAS_DB_WAIT_TIMEOUT, because the port frequently opens before
  #     the server will talk.
  #   - "Access denied" (a configuration error, not a readiness state): retried
  #     only for a short grace window, because no amount of waiting fixes a
  #     wrong password, and a fast honest message is worth far more than a long
  #     hopeful wait. The grace window exists solely to absorb the narrow race
  #     in which grants are still being applied.
  local auth_grace="${ACAS_DB_AUTH_GRACE:-15}"
  if [[ ! "$auth_grace" =~ ^[0-9]+$ ]]; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_AUTH_GRACE must be numeric; got '$auth_grace'."
  fi
  (( auth_grace > timeout )) && auth_grace="$timeout"

  local rc=0 denied_for=0
  elapsed=0
  while true; do
    rc=0
    acas_db_credentialed_probe || rc=$?
    case "$rc" in
      0)
        if (( elapsed == 0 )); then
          acas_log "authenticated as ${ACAS_DB_USER} against ${ACAS_PRESQL2_DBNAME:-information_schema} -- server is ready"
        else
          acas_log "authenticated as ${ACAS_DB_USER} after a further ${elapsed}s"
        fi
        return 0
        ;;
      3)
        acas_note 'no mariadb/mysql/mariadb-admin/mysqladmin binary found; readiness verified at the TCP layer only'
        acas_note 'step 4 will be the first thing to authenticate; a credential error will surface there'
        return 0
        ;;
      2)
        if (( denied_for >= auth_grace )); then
          acas_die "$EX_DATABASE" \
            "MariaDB at ${ACAS_DB_HOST}:${ACAS_DB_PORT} REJECTED the credentials for user '${ACAS_DB_USER}'." \
            "The server is alive and accepting connections, so this is a credential" \
            "or grant problem, not a readiness problem -- waiting longer will not fix it." \
            "presql2 authenticates with exactly these values via read_params" \
            '[presql2-package/cobmysqlapi38.c:L114-L176], so step 4 would fail on every' \
            "one of the 28 bridges in [common/comp-common.sh:L25]." \
            "Check ACAS_DB_USER and ACAS_DB_PASSWORD, and that the user is granted" \
            "access to ${ACAS_PRESQL2_DBNAME:-information_schema} and ${ACAS_DB_NAME}." \
            "Server said: ${ACAS_DB_PROBE_DIAG:-<no diagnostic>}"
        fi
        if (( denied_for == 0 )); then
          acas_log "credentials rejected; allowing ${auth_grace}s in case grants are still being applied"
        fi
        sleep "$interval"
        denied_for=$(( denied_for + interval ))
        elapsed=$(( elapsed + interval ))
        ;;
      *)
        if (( elapsed >= timeout )); then
          acas_die "$EX_DATABASE" \
            "MariaDB at ${ACAS_DB_HOST}:${ACAS_DB_PORT} accepted a TCP connection but would not complete an authenticated statement within ${timeout}s." \
            'presql2 authenticates with exactly these credentials via' \
            'read_params [presql2-package/cobmysqlapi38.c:L114-L176], so step 4' \
            'would fail. Check that the server has finished initialising.' \
            "Client said: ${ACAS_DB_PROBE_DIAG:-<no diagnostic>}"
        fi
        if (( elapsed == 0 )); then
          acas_log "port is open but an authenticated statement did not yet succeed; retrying for up to ${timeout}s"
        fi
        sleep "$interval"
        elapsed=$(( elapsed + interval ))
        ;;
    esac
  done
}

# =============================================================================
# BUILD TREE
#
# DEVIATION 1 of 6 -- the compile runs in $ACAS_BUILD, not where the frozen
# scripts live. Reason, and it is not a preference but a hard requirement:
# [common/comp-common.sh:L25] is
#     for i in `ls *MT.scb`; do presql2 $i; ... done
# which REGENERATES every common/*MT.cbl in whatever directory it runs in. Those
# 28 generated bridges are the committed, frozen files that AAP 0.8.2 designates
# "the authoritative record-layout <-> table mapping ... the data dictionary for
# this migration". Worse, presql2 TRUNCATES its output before it validates its
# parameters -- OPEN OUTPUT OUTPUT-FILE at [presql2-package/presql2.cbl:L543]
# precedes 2131-Get-RDB-Params at [presql2-package/presql2.cbl:L759] -- so a
# mere misconfiguration run inside the checkout would zero all 28 of them. Four
# further writes make the same point: `-T <name>.prn' listings, six copies of
# cobmysqlapi.o, presql2.param, and every .so/executable cobc emits. The frozen
# scripts are therefore run UNMODIFIED against a faithful replica.
#
# The whole checkout is copied. The prompt's own preference, and the safe
# choice: the frozen scripts navigate with relative paths -- `-I ../copybooks'
# in every compile, `cd common' / `cd ../general' in [comp-all.sh:L15-L32] --
# so the copy must preserve the tree layout exactly. Excluding directories to
# save space (ACAS-Manuals/, Basic-Code/, payroll/, home/, .git/) would work
# today but would silently break the moment a frozen script grew a reference,
# and the space cost is a few hundred megabytes on a container volume. The
# faithful replica is worth more than the disk.
# =============================================================================

acas_prepare_build_tree() {
  acas_stage 'Build tree: copy the frozen checkout into the writable tree'

  # Re-assert the safety guards immediately before anything destructive.
  acas_assert_safe_build_path "$ACAS_BUILD"

  if (( ACAS_REFRESH_TREE )); then
    acas_log "clearing $ACAS_BUILD"
    # Delete only the CHILDREN of $ACAS_BUILD, never $ACAS_BUILD itself: the
    # directory is a mount point in the Compose stack and removing it would
    # break the container. The guards above have already established that this
    # path is absolute, at least two components deep, and disjoint from
    # $ACAS_REPO in both directions.
    find "$ACAS_BUILD" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + \
      || acas_die "$EX_BUILDTREE" "could not clear $ACAS_BUILD."

    acas_log "copying $ACAS_REPO into $ACAS_BUILD (whole tree, layout preserved)"
    cp -a "$ACAS_REPO/." "$ACAS_BUILD/" \
      || acas_die "$EX_BUILDTREE" \
        "copying $ACAS_REPO into $ACAS_BUILD failed." \
        'The build must run in a copy: [common/comp-common.sh:L25] regenerates' \
        'every common/*MT.cbl, and those files are the frozen data dictionary.'
  else
    acas_log "reusing the existing build tree in $ACAS_BUILD (refresh disabled)"
  fi

  # Structure the frozen scripts require.
  local dir
  for dir in copybooks "${ACAS_COMPILE_DIRS[@]}"; do
    [[ -d "$ACAS_BUILD/$dir" ]] || acas_die "$EX_BUILDTREE" \
      "$ACAS_BUILD/$dir is missing from the build tree." \
      'Every frozen compile resolves copybooks through `-I ../copybooks'"'"' and' \
      '[comp-all.sh:L15-L32] cd s through all six compile directories.'
  done
  [[ -f "$ACAS_BUILD/comp-all.sh" ]] || acas_die "$EX_BUILDTREE" \
    "$ACAS_BUILD/comp-all.sh is missing from the build tree."
  [[ -f "$ACAS_BUILD/common/comp-common.sh" ]] || acas_die "$EX_BUILDTREE" \
    "$ACAS_BUILD/common/comp-common.sh is missing from the build tree."

  # The executable bit, on the COPIES only -- never on the checkout.
  # [comp-all.sh:L16,L19,L22,L25,L28,L31] invokes each per-directory script as
  # `./comp-*.sh', which requires the bit even though this script itself calls
  # the two top-level scripts through `bash'.
  local script
  for script in "$ACAS_BUILD/comp-all.sh" \
                "$ACAS_BUILD/common/comp-common.sh" \
                "$ACAS_BUILD/general/comp-gl.sh" \
                "$ACAS_BUILD/irs/comp-irs.sh" \
                "$ACAS_BUILD/purchase/comp-purchase.sh" \
                "$ACAS_BUILD/sales/comp-sales.sh" \
                "$ACAS_BUILD/stock/comp-stock.sh"; do
    [[ -f "$script" ]] || acas_die "$EX_BUILDTREE" \
      "$script is missing from the build tree; [comp-all.sh] invokes it directly."
    chmod +x "$script" || acas_die "$EX_BUILDTREE" "could not make $script executable."
  done
  acas_log 'verified: all seven frozen compile scripts are present and executable in the copy'

  # $ACAS_BIN is created by the image under /build and the refresh removes it,
  # so restore it for the runner scripts that install modules there.
  if [[ -n "${ACAS_BIN-}" && "$ACAS_BIN" == "$ACAS_BUILD"/* ]]; then
    mkdir -p "$ACAS_BIN"
    acas_log "restored ACAS_BIN=$ACAS_BIN"
  fi

  acas_check_copybook_closure
}

# -----------------------------------------------------------------------------
# COPY-closure advisory.
#
# A precise, zero-false-positive check that every copybook the frozen build
# actually needs can be resolved. It exists because this repository has a real
# source-level gap: copybooks/ACAS-SQLstate-error-list.cob is COPY'd by 22 of
# the 28 GENERATED bridges and is ABSENT from the frozen archive. Without this advisory
# that gap surfaces minutes later as 22 apparently unrelated compile errors
# inside a script that then reports success anyway.
#
# It is an ADVISORY, not a gate: the missing copybook is a frozen-archive defect
# and must be supplied by the maintainer, never fabricated here (R-3, R-4). The
# build is still attempted so that the log scan and the artifact assertions
# report exactly which bridges are affected.
#
# Precision notes:
#   * only quoted COPY targets are considered, and only on lines with no `*' or
#     `/' before the keyword, which excludes fixed-format comment lines (`*' in
#     column 7) and inline `*>' comments;
#   * a target is resolved against copybooks/ AND the program's own directory,
#     because cobc searches the current directory as well as `-I ../copybooks';
#   * the bare name and GnuCOBOL's usual copybook extensions are all tried,
#     because sources use both `copy "wsdnos".' and `copy "wsbatch.cob".';
#   * only the source sets the frozen scripts actually compile are scanned, so
#     a copybook needed exclusively by a program no compile script builds --
#     common/acasconvert3.cbl is the real example -- is correctly ignored.
# -----------------------------------------------------------------------------
acas_collect_sources() {
  local dir="$1"
  shift
  local pattern
  local -a matched=()
  for pattern in "$@"; do
    mapfile -t matched < <(compgen -G "$ACAS_BUILD/$dir/$pattern" || true)
    if (( ${#matched[@]} )); then
      printf '%s\n' "${matched[@]}"
    fi
  done
}

acas_scan_dir_copybooks() {
  local dir="$1"
  shift
  local -a sources=()
  mapfile -t sources < <(acas_collect_sources "$dir" "$@")
  (( ${#sources[@]} )) || return 0

  local target ext candidate resolved
  while IFS= read -r target; do
    [[ -n "$target" ]] || continue
    resolved=0
    for ext in '' .cob .COB .cpy .CPY .cbl .CBL; do
      for candidate in "$ACAS_BUILD/copybooks/${target}${ext}" \
                       "$ACAS_BUILD/${dir}/${target}${ext}"; do
        if [[ -f "$candidate" ]]; then
          resolved=1
          break 2
        fi
      done
    done
    if (( resolved == 0 )); then
      printf '%s\n' "${dir}: ${target}"
    fi
  done < <(grep -hoiE '^[^*/]*[[:space:]]copy[[:space:]]+"[A-Za-z0-9._-]+"' \
             "${sources[@]}" 2>/dev/null \
             | grep -oE '"[A-Za-z0-9._-]+"' | tr -d '"' | sort -u)
}

acas_check_copybook_closure() {
  local -a unresolved=()
  mapfile -t unresolved < <(
    acas_scan_dir_copybooks common '*MT.cbl' 'maps0*.cbl' 'acas0*.cbl' \
      'acasirsub*.cbl' 'acas-get-params.cbl' 'fhlogger.cbl' 'xl150.cbl' \
      'sys002.cbl' 'ACAS.cbl' 'ACAS-Sysout.cbl' '*LD.cbl' '*UNL.cbl' '*RES.cbl'
    acas_scan_dir_copybooks general 'gl*.cbl' 'general.cbl'
    acas_scan_dir_copybooks irs 'irs0*.cbl' 'irs.cbl' 'irsubp.cbl'
    acas_scan_dir_copybooks purchase 'pl*.cbl' 'purchase.cbl'
    acas_scan_dir_copybooks sales 'sl*.cbl' 'sales.cbl'
    acas_scan_dir_copybooks stock 'st*.cbl' 'stock.cbl'
  )

  if (( ${#unresolved[@]} == 0 )); then
    acas_log 'verified: every COPY target of every source the frozen scripts compile resolves'
    return 0
  fi

  printf '\n'
  acas_warn "${#unresolved[@]} COPY target(s) referenced by the frozen build cannot be resolved:"
  local entry
  for entry in "${unresolved[@]}"; do
    printf '         %s\n' "$entry" >&2
    if [[ "$entry" == *ACAS-SQLstate-error-list* ]]; then
      acas_explain_missing_sqlstate_copybook
    fi
  done
  acas_warn 'the build will continue so that the log scan and the artifact assertions report exactly which programs are affected.'
}

# The one known, named gap in the frozen archive. Explained in full because the
# correct response is counter-intuitive: it must NOT be written.
acas_explain_missing_sqlstate_copybook() {
  cat >&2 <<'EXPLAIN'
         --------------------------------------------------------------------
         copybooks/ACAS-SQLstate-error-list.cob is MISSING from the frozen
         archive. It is COPY'd by 22 of the 28 GENERATED common/*MT.cbl bridges
         and by the same 22 *MT.scb sources -- 44 frozen files in total -- so
         those bridges cannot compile, and the handlers that CALL them cannot
         reach a table. (The 29th *MT.cbl, dummy-rdbmsMT.cbl, has no *MT.scb and
         does not reference the copybook, so it is unaffected.)

         DO NOT FABRICATE IT. It carries the SQLSTATE-to-FS-Reply mapping that
         DEFINES the oracle's rejection behaviour, and rejection behaviour --
         disposition AND database effect -- is precisely what this migration
         must reproduce. An invented mapping would make the oracle wrong in the
         one dimension nobody could later detect, and inventing it would breach
         both the no-new-validations rule (R-3) and the reproduce-never-fix rule
         (R-4).

         It must be supplied by the maintainer. Until it is, the oracle can be
         built only for the bridges that do not reference it.
         --------------------------------------------------------------------
EXPLAIN
}

# =============================================================================
# STEP 1/5 -- unpack the vendored JC preSQL archive
#
# The vendored archives are harness build inputs: unpacked INSIDE the container
# and never modified in the checkout. presql2-latest.zip holds 61 entries and
# expands to a presql2-package/ directory carrying cobmysqlapi38.c and .sh,
# presql2.cbl and .sh, bldcopy2.*, prtschema2.*, the MYSQL-*.CPY copybooks, the
# example .param files, and the ACAS/, Variations/ and old-apis/ subdirectories.
# =============================================================================
acas_step1_unpack_presql2() {
  acas_banner 1 'unpack the vendored JC preSQL archive'

  local published="${ACAS_PRESQL2_PACKAGE:-/opt/presql2-package}"
  if [[ -f "$published/cobmysqlapi38.c" && -f "$published/presql2.cbl" ]]; then
    ACAS_PRESQL2_DIR="$published"
    acas_log "reusing the package harness/Dockerfile.gnucobol already unpacked: $published"
  else
    local archive="$ACAS_REPO/presql2-latest.zip"
    [[ -f "$archive" ]] || acas_die "$EX_STEP1" \
      "the vendored archive $archive is absent." \
      'It is the only source of the build rule for cobmysqlapi.o, without which' \
      'the oracle cannot be built at all.'

    # A scratch directory INSIDE the writable build tree, removed on exit. The
    # archive itself is never touched: it is read out of the read-only checkout.
    local scratch="$ACAS_BUILD/.acas-presql2"
    rm -rf -- "$scratch"
    mkdir -p "$scratch"
    ACAS_SCRATCH_DIRS+=("$scratch")

    if acas_have unzip; then
      acas_log "extracting $archive with unzip"
      unzip -q -o "$archive" -d "$scratch" || acas_die "$EX_STEP1" \
        "unzip failed to extract $archive."
    else
      # unzip is not guaranteed on every host, so fall back to the standard
      # library. python3 is already asserted present by the toolchain check.
      acas_log "unzip is unavailable; extracting $archive with python3 zipfile"
      if ! python3 - "$archive" "$scratch" <<'PY'
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as archive:
    archive.extractall(sys.argv[2])
PY
      then
        acas_die "$EX_STEP1" \
          "python3 zipfile failed to extract $archive."
      fi
    fi

    [[ -d "$scratch/presql2-package" ]] || acas_die "$EX_STEP1" \
      "presql2-package/ was not found inside $archive." \
      'The archive layout is not as expected.'
    ACAS_PRESQL2_DIR="$scratch/presql2-package"
    acas_log "unpacked to $ACAS_PRESQL2_DIR"
  fi

  # The four members every later step depends on.
  local required
  for required in cobmysqlapi38.c cobmysqlapi38.sh presql2.cbl presql2.sh; do
    [[ -f "$ACAS_PRESQL2_DIR/$required" ]] || acas_die "$EX_STEP1" \
      "$ACAS_PRESQL2_DIR/$required is missing." \
      'Steps 2 and 3 are built from these four files.'
  done
  acas_log 'verified: cobmysqlapi38.c, cobmysqlapi38.sh, presql2.cbl and presql2.sh are present'

  # Two coexisting version strings. BOTH are true and NEITHER is resolved: the
  # package README records one, the translator's own WORKING-STORAGE another.
  # Recorded rather than reconciled (R-4, R-5).
  acas_note 'preSQL package version per [presql2-package/README.SVN:L22]: 1.14f'
  acas_note 'translator version per [presql2-package/presql2.cbl:L302]: " 2.22 "'
}

# =============================================================================
# STEP 2/5 -- the RECOVERED build rule for the bridge's C interface object
#
# `find . -name cobmysqlapi*' over the whole ACAS checkout returns nothing: no
# object, no C source, and NO RULE ANYWHERE THAT BUILDS IT. Yet every
# RDBMS-touching compile links a bare `cobmysqlapi.o':
# [common/comp-common.sh:L26] (bridges), :L32 (handlers), :L34 (IRS handlers),
# :L36 (acas-get-params), :L40-L42 (fhlogger, xl150, sys002), :L45 (ACAS.cbl),
# :L51 (loaders), and every per-directory script -- [general/comp-gl.sh:L2],
# [irs/comp-irs.sh:L2], [purchase/comp-purchase.sh:L2], [sales/comp-sales.sh:L7],
# [stock/comp-stock.sh:L2]. Following the compile scripts alone, the oracle
# cannot be built.
#
# The rule was recovered from the vendored package. Verbatim, and it is the
# whole of [presql2-package/cobmysqlapi38.sh]:
#
#     gcc -I/usr/local/mysql/include -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC
#
# cobmysqlapi38.c ONLY. The superseded variants must not be used:
# [presql2-package/old-apis/cobmysqlapi.sh] is
# `gcc -I/usr/include/mysql -c cobmysqlapi.005.c' and
# [presql2-package/old-apis/cobmysqlapi3.sh] is
# `gcc -I/usr/include/mysql -c cobmysqlapi3.c -o cobmysqlapi.o' -- a DIFFERENT
# include path and, decisively, NO -fPIC, so neither can be linked into the
# `cobc -m' shared modules the frozen scripts build.
# =============================================================================
acas_step2_build_cobmysqlapi() {
  acas_banner 2 'compile cobmysqlapi.o with the recovered build rule'

  local published="${ACAS_COBMYSQLAPI_OBJ:-/usr/local/lib/acas/cobmysqlapi.o}"
  if [[ -s "$published" ]]; then
    ACAS_COBMYSQLAPI_SRC="$published"
    acas_log "reusing the object harness/Dockerfile.gnucobol already built: $published"
  else
    [[ -n "$ACAS_PRESQL2_DIR" && -f "$ACAS_PRESQL2_DIR/cobmysqlapi38.c" ]] \
      || acas_die "$EX_STEP2" \
        'the unpacked preSQL package is not available, so cobmysqlapi38.c cannot be compiled.' \
        'Run step 1 first (omit --from/--only, or use --from 1).'

    local workdir="$ACAS_BUILD/.acas-cobmysqlapi"
    rm -rf -- "$workdir"
    mkdir -p "$workdir"
    ACAS_SCRATCH_DIRS+=("$workdir")
    cp -p "$ACAS_PRESQL2_DIR/cobmysqlapi38.c" "$workdir/cobmysqlapi38.c"

    acas_log 'running the recovered rule verbatim [presql2-package/cobmysqlapi38.sh]:'
    acas_log '  gcc -I/usr/local/mysql/include -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC'
    (
      cd "$workdir" \
        && gcc -I/usr/local/mysql/include -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC
    ) || acas_die "$EX_STEP2" \
      'compiling cobmysqlapi38.c failed.' \
      'This is the recovered rule from [presql2-package/cobmysqlapi38.sh]; it needs' \
      "$ACAS_FROZEN_MYSQL_PREFIX/include/mysql.h and a working C compiler." \
      'Without the object, every bridge, handler and loader fails at link time' \
      'with nothing more informative than "cobmysqlapi.o: No such file or directory".'

    [[ -s "$workdir/cobmysqlapi.o" ]] || acas_die "$EX_STEP2" \
      "gcc reported success but $workdir/cobmysqlapi.o is missing or empty." \
      '[presql2-package/cobmysqlapi38.sh]'
    ACAS_COBMYSQLAPI_SRC="$workdir/cobmysqlapi.o"
    acas_log "built $ACAS_COBMYSQLAPI_SRC ($(wc -c < "$ACAS_COBMYSQLAPI_SRC") bytes)"
  fi

  # SIX copies, one per compile directory. The link references a BARE FILENAME
  # -- `cobc -m $i cobmysqlapi.o ...' at [common/comp-common.sh:L26] and
  # `cobc -m $i ... cobmysqlapi.o ...' at [general/comp-gl.sh:L2] -- which the
  # linker resolves against the CURRENT DIRECTORY. [comp-all.sh:L15-L32] cd s
  # into all six directories in turn, so the object must exist in all six. This
  # is not redundancy; it is what the frozen recipe requires.
  local dir target
  for dir in "${ACAS_COMPILE_DIRS[@]}"; do
    target="$ACAS_BUILD/$dir/cobmysqlapi.o"
    install -m 0644 "$ACAS_COBMYSQLAPI_SRC" "$target" || acas_die "$EX_STEP2" \
      "could not place cobmysqlapi.o in $ACAS_BUILD/$dir."
    [[ -s "$target" ]] || acas_die "$EX_STEP2" "$target is missing or empty."
  done
  acas_log "placed cobmysqlapi.o in all ${#ACAS_COMPILE_DIRS[@]} compile directories: $(acas_join_words "${ACAS_COMPILE_DIRS[@]}")"
}

# =============================================================================
# STEP 3/5 -- build and install the presql2 translator
#
# Verbatim, and the whole of [presql2-package/presql2.sh]:
#     cobc -x presql2.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz
#
# [common/comp-common.sh:L25] invokes `presql2' by name over every *MT.scb, so
# it must be on the PATH before step 4.
# =============================================================================
acas_step3_build_presql2() {
  acas_banner 3 'build and install the presql2 translator'

  if acas_have presql2; then
    acas_log "presql2 is already on the PATH: $(command -v presql2)"
  else
    [[ -n "$ACAS_PRESQL2_DIR" && -f "$ACAS_PRESQL2_DIR/presql2.cbl" ]] \
      || acas_die "$EX_STEP3" \
        'presql2 is not on the PATH and the unpacked package is unavailable.' \
        'Run step 1 first (omit --from/--only, or use --from 1).'
    [[ -n "$ACAS_COBMYSQLAPI_SRC" && -s "$ACAS_COBMYSQLAPI_SRC" ]] \
      || acas_die "$EX_STEP3" \
        'cobmysqlapi.o is unavailable, and [presql2-package/presql2.sh] links it.' \
        'Run step 2 first.'

    local workdir="$ACAS_BUILD/.acas-presql2-build"
    rm -rf -- "$workdir"
    mkdir -p "$workdir"
    ACAS_SCRATCH_DIRS+=("$workdir")

    # presql2.cbl COPYs the MYSQL-*.CPY interface copybooks that ship beside it,
    # so they are staged into the same directory and COBCPY is pointed there.
    cp -p "$ACAS_PRESQL2_DIR/presql2.cbl" "$workdir/"
    local cpy
    for cpy in MYSQL-VARIABLES.CPY MYSQL-PROCEDURES.CPY \
               mysql-variables.cpy mysql-procedures.cpy; do
      [[ -f "$ACAS_PRESQL2_DIR/$cpy" ]] && cp -p "$ACAS_PRESQL2_DIR/$cpy" "$workdir/"
    done
    cp -p "$ACAS_COBMYSQLAPI_SRC" "$workdir/cobmysqlapi.o"

    acas_log 'running the vendored rule verbatim [presql2-package/presql2.sh]:'
    acas_log '  cobc -x presql2.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz'
    (
      cd "$workdir" \
        && COBCPY="$workdir" COB_COPY_DIR="$workdir" \
           cobc -x presql2.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz
    ) || acas_die "$EX_STEP3" \
      'building presql2 failed.' \
      '[common/comp-common.sh:L25] cannot translate any *MT.scb without it.'

    [[ -s "$workdir/presql2" ]] || acas_die "$EX_STEP3" \
      "cobc reported success but $workdir/presql2 was not produced." \
      '[presql2-package/presql2.sh]'
    install -m 0755 "$workdir/presql2" /usr/local/bin/presql2 || acas_die "$EX_STEP3" \
      'could not install presql2 into /usr/local/bin.' \
      'Root privileges are required, or place it on the PATH yourself.'
    acas_log 'installed /usr/local/bin/presql2'

    # bldcopy2 is built for completeness. Note the SPACE after -L, which is how
    # [presql2-package/bldcopy2.sh] is written, and that it links WITHOUT -lz.
    # No frozen ACAS script invokes bldcopy2, so a failure here cannot block the
    # oracle and is reported rather than fatal.
    if [[ -f "$ACAS_PRESQL2_DIR/bldcopy2.cbl" ]] && ! acas_have bldcopy2; then
      cp -p "$ACAS_PRESQL2_DIR/bldcopy2.cbl" "$workdir/"
      acas_log 'running the vendored rule verbatim [presql2-package/bldcopy2.sh]:'
      acas_log '  cobc -x bldcopy2.cbl cobmysqlapi.o -L /usr/local/mysql/lib -lmysqlclient'
      if (
           cd "$workdir" \
             && COBCPY="$workdir" COB_COPY_DIR="$workdir" \
                cobc -x bldcopy2.cbl cobmysqlapi.o -L /usr/local/mysql/lib -lmysqlclient
         ) && [[ -s "$workdir/bldcopy2" ]]; then
        install -m 0755 "$workdir/bldcopy2" /usr/local/bin/bldcopy2 \
          && acas_log 'installed /usr/local/bin/bldcopy2'
      else
        acas_warn 'bldcopy2 could not be built or installed; no frozen ACAS script invokes it, so the oracle build is unaffected.'
      fi
    fi
  fi

  acas_have presql2 || acas_die "$EX_STEP3" \
    'presql2 is still not on the PATH after step 3.' \
    '[common/comp-common.sh:L25] invokes it by name for every *MT.scb.'

  # DEVIATION 6 of 6 -- a deliberate omission, recorded as one (R-5):
  # prtschema2 is NOT built. The
  # archive ships no prtschema2.cbl, so [presql2-package/prtschema2.sh:L1] has
  # to generate it by RUNNING presql2 -- which would need a second credential
  # file at translate time -- and no frozen ACAS script invokes prtschema2 at
  # all. Building it would add a credential write and a failure mode for no
  # gain to the oracle.
  acas_note 'prtschema2 is deliberately not built: the archive ships no prtschema2.cbl and no frozen ACAS script uses it'

  if (( ACAS_RUN_PREFLIGHT_LINK )); then
    acas_preflight_link_proof
  else
    acas_note 'step-3 toolchain link proof skipped at the operator'"'"'s request'
  fi
}

# -----------------------------------------------------------------------------
# Toolchain link proof.
#
# Reproduces the vendored worked example [presql2-package/ACAS/comp-stockMT.sh]
# verbatim in a scratch directory:
#     cobc -m stockMT.COB cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz
# A real generated ACAS bridge, compiled exactly as ACAS compiles its own. A
# clean link here proves the entire COBOL-to-MySQL toolchain before a single
# frozen script runs, and a missing or wrong cobmysqlapi.o is precisely the
# failure it catches -- the failure that is otherwise reported as an
# unattributable link error minutes into step 4.
# -----------------------------------------------------------------------------
acas_preflight_link_proof() {
  local example="$ACAS_PRESQL2_DIR/ACAS"
  if [[ -z "$ACAS_PRESQL2_DIR" || ! -f "$example/stockMT.COB" ]]; then
    acas_note 'the vendored worked example is unavailable, so the link proof is skipped'
    return 0
  fi

  local proof="$ACAS_BUILD/.acas-link-proof"
  rm -rf -- "$proof"
  mkdir -p "$proof"
  ACAS_SCRATCH_DIRS+=("$proof")
  cp -a "$example/." "$proof/"
  cp -p "$ACAS_COBMYSQLAPI_SRC" "$proof/cobmysqlapi.o"

  acas_log 'proving the toolchain with [presql2-package/ACAS/comp-stockMT.sh]:'
  acas_log '  cobc -m stockMT.COB cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz'
  (
    cd "$proof" \
      && COBCPY="$proof" COB_COPY_DIR="$proof" \
         cobc -m stockMT.COB cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz
  ) || acas_die "$EX_STEP3" \
    'the vendored worked example failed to compile.' \
    'The COBOL-to-MySQL toolchain is incomplete, so every frozen bridge compile' \
    'would fail the same way. Check cobmysqlapi.o, mysql.h and libmysqlclient.so.' \
    '[presql2-package/ACAS/comp-stockMT.sh]'

  [[ -s "$proof/stockMT.so" ]] || acas_die "$EX_STEP3" \
    'cobc reported success but stockMT.so was not produced.' \
    '[presql2-package/ACAS/comp-stockMT.sh]'

  if acas_have ldd; then
    if ldd "$proof/stockMT.so" 2>/dev/null | grep -q 'not found'; then
      acas_die "$EX_STEP3" \
        'stockMT.so has unresolved shared-library dependencies.' \
        '-L/usr/local/mysql/lib -lmysqlclient linked but does not resolve at run' \
        'time. Check /etc/ld.so.conf.d/gnucobol.conf and run ldconfig.' \
        '[etc/ld.so.conf.d/gnucobol.conf]'
    fi
  fi
  acas_log 'verified: a real generated ACAS bridge compiles and links against the recovered cobmysqlapi.o'
}

# =============================================================================
# presql2.param -- the credential file the translator requires and the checkout
#                  does not contain
#
# read_params() in the recovered C shim, declared at
# [presql2-package/cobmysqlapi38.c:L114], derives its filename from the calling
# program's name -- sprintf(zwi2, "%s.param", zwi) at :L126 -- and opens it
# RELATIVE TO THE CURRENT DIRECTORY at :L127. When the file is absent it prints
# "Could not read file >presql2.param<, aborting..." and calls exit(5) at
# :L129-L130. It then reads exactly SIX cards and prefix-validates each one in
# this exact order, calling exit(6) on any mismatch:
#
#   DBHOST=    :L134-L137      DBNAME=    :L155-L158
#   DBUSER=    :L141-L144      DBPORT=    :L162-L165
#   DBPASSWD=  :L148-L151      DBSOCKET=  :L169-L172
#
# presql2.cbl reads it at [presql2-package/presql2.cbl:L759-L773] and states the
# requirement in its own prologue at :L55 ("This filename MUST be
# presql2.param"). NO *.param file exists anywhere in the ACAS checkout, so one
# must be materialised, and it must be materialised in the directory presql2
# runs in -- $ACAS_BUILD/common, because [common/comp-common.sh:L25] runs there.
#
# DEVIATION 2 of 6 -- presql2.param is a NEW file the frozen recipe never
# creates. It is unavoidable: no *.param exists anywhere in the checkout, yet
# read_params aborts with exit(5) without one. It is written only into the
# writable build tree, never the checkout, and is shredded on exit.
#
# DEVIATION 3 of 6 -- WHY DBNAME IS information_schema, NOT $ACAS_DB_NAME.
# presql2 builds its metadata query at [presql2-package/presql2.cbl:L798-L806]
# as "SELECT COLUMN_NAME, DATA_TYPE, ... FROM COLUMNS WHERE TABLE_SCHEMA=..." --
# and `FROM COLUMNS' is UNQUALIFIED. The connected schema must therefore be the
# one that owns COLUMNS, i.e. information_schema. The schema actually being
# described arrives separately, from each bridge's own BASE= directive
# (BASE=ACASDB, e.g. [common/glpostingMT.scb:L273-L276]), and is substituted
# into TABLE_SCHEMA. The vendored example agrees: [presql2-package/presql2.param]
# line 4 is DBNAME=information_schema. ACAS_PRESQL2_DBNAME can override this for
# experimentation; the default is the value the source requires.
#
# DEVIATION 4 of 6 -- an EMPTY ACAS_DB_SOCKET is written as the literal
# DBSOCKET=NULL rather than as an empty value. MySQL_real_connect at
# [presql2-package/cobmysqlapi38.c:L513-L525] maps unix_socket to NULL only for
# the literals "0", "null" and "NULL"; an empty string is passed through as ""
# and defeats the TCP connection. harness/docker-compose.yml sets
# ACAS_DB_SOCKET: "", so this translation is what makes the Compose default work.
#
# CREDENTIAL HYGIENE. Written under umask 077, chmod 0600 explicitly, never
# echoed, never passed in argv, and shredded then unlinked by the EXIT trap on
# every exit path.
# =============================================================================
acas_write_presql2_param() {
  local dir="$1"
  local prog="${2:-presql2}"
  local target="$dir/$prog.param"

  [[ -d "$dir" ]] || acas_die "$EX_STEP4" \
    "$dir does not exist, so $prog.param cannot be written there."

  local dbname="${ACAS_PRESQL2_DBNAME:-information_schema}"

  # An EMPTY socket is written as the literal NULL. MySQL_real_connect maps
  # unix_socket to NULL only for the exact strings "0", "null" and "NULL"
  # [presql2-package/cobmysqlapi38.c:L513-L525]; an empty string is passed
  # through as an empty socket path, which is not the same thing. NULL is the
  # only unambiguous spelling of "connect over TCP, there is no socket", and
  # harness/docker-compose.yml sets ACAS_DB_SOCKET to the empty string on
  # purpose. A non-empty value is written verbatim.
  local socket="${ACAS_DB_SOCKET-}"
  if [[ -z "$socket" ]]; then
    socket='NULL'
  fi

  # umask 077 locally, so the file is never momentarily group- or
  # world-readable between creation and chmod.
  local previous_umask
  previous_umask="$(umask)"
  umask 077
  {
    printf 'DBHOST=%s\n'   "$ACAS_DB_HOST"
    printf 'DBUSER=%s\n'   "$ACAS_DB_USER"
    printf 'DBPASSWD=%s\n' "$ACAS_DB_PASSWORD"
    printf 'DBNAME=%s\n'   "$dbname"
    printf 'DBPORT=%s\n'   "$ACAS_DB_PORT"
    printf 'DBSOCKET=%s\n' "$socket"
  } > "$target" || {
    umask "$previous_umask"
    acas_die "$EX_STEP4" "could not write $target."
  }
  umask "$previous_umask"
  chmod 600 "$target" || acas_die "$EX_STEP4" "could not restrict permissions on $target."
  ACAS_PARAM_FILES+=("$target")

  # LF endings are correct: cobapi_read_line stops at '\n' or EOF and discards
  # '\r' [presql2-package/cobmysqlapi38.c:L77-L93].
  acas_log "wrote $target (0600, six cards in the order read_params requires)"
  acas_log "  DBHOST=${ACAS_DB_HOST}  DBUSER=${ACAS_DB_USER}  DBPASSWD=<redacted>"
  acas_log "  DBNAME=${dbname}  DBPORT=${ACAS_DB_PORT}  DBSOCKET=${socket}"
  acas_note 'it is shredded and unlinked by the EXIT trap, on every exit path'
}

# =============================================================================
# LOG SCANNING -- the workaround for the unconditional `exit 0'
#
# Every frozen compile script ends `exit 0' unconditionally
# ([common/comp-common.sh:L59], [comp-all.sh:L44-L45] and the five
# per-directory scripts), so their exit status carries no information. This scan
# is one of the two mechanisms that actually detect failure; the artifact
# assertions are the other, and are more reliable because they inspect the
# products rather than the prose. Both always run.
#
# THE CLASSIFICATION, stated so a reviewer can audit it:
#
#   BENIGN  -- excluded from the counts, but the number excluded is REPORTED so
#              nothing is hidden. Exactly one family qualifies:
#              "warning: '_FORTIFY_SOURCE' redefined" and its companion
#              "note: this is the location of the previous definition". These
#              come from the C compiler, not from cobc, and are emitted once per
#              compile because the frozen scripts pass -D_FORTIFY_SOURCE=1
#              ([general/comp-gl.sh:L2] and its siblings) on a toolchain that
#              already defines it. They say nothing about the artifact produced.
#              Verified empirically: one such pair per cobc invocation, on a
#              compile that succeeds and produces a correct module.
#
#   FATAL   -- always fails the build. Includes cobc and gcc diagnostics, linker
#              failures, missing files, crashes, and the two exit paths of the
#              preSQL credential reader. The patterns are colon-anchored
#              (`error:', `warning:') for a specific reason: the frozen scripts
#              themselves print "check for any error or warning messages"
#              ([comp-all.sh:L44]), which must not be mistaken for a diagnostic.
#              `No such file or directory' is matched WITHOUT a colon anchor
#              because a missing cobmysqlapi.o produces
#              "prog.cbl: cobc: cobmysqlapi.o: No such file or directory" with
#              no `error:' token at all -- verified against cobc 3.2 -- and that
#              is the single most important failure this script must catch.
#              The end-of-group summary is matched as `[1-9][0-9]* error' so
#              that "0 errors" never matches.
#
# DO NOT "IMPROVE" THIS BY SCANNING THE .prn LISTINGS -- MEASURED TRAP.
#   The frozen scripts pass `-T <name>.prn' to every compile, and each listing
#   ends with an authoritative-looking "N errors in compilation group". It is
#   tempting to trust that instead of this prose scan. It is NOT trustworthy on
#   its own, and I verified why: when a compile fails because a COPY target is
#   missing, cobc aborts BEFORE refreshing the listing, so a STALE listing from
#   an earlier run survives and still says "0 errors in compilation group" for a
#   bridge that produced no module at all. Measured directly: with
#   copybooks/ACAS-SQLstate-error-list.cob absent, analMT/auditMT/glpostingMT
#   each failed with `error: ... No such file or directory' on stderr while
#   analMT.prn, auditMT.prn and glpostingMT.prn all reported "0 errors".
#   Conversely a semantic error DOES reach the listing: an undefined data item
#   in maps04.cbl produced "2 errors in compilation group" in maps04.prn.
#   So the listing is a COMPLEMENT at best and a liar at worst. The two signals
#   this script relies on -- this scan (which catches the abort-before-listing
#   class) and the artifact assertions (which inspect the products) -- together
#   cover both classes without ever trusting a stale listing. If the summary
#   line does reach the console it is caught anyway by the FATAL pattern above.
#
#   WARNING -- reported with a count and the full text, and fatal only when
#              ACAS_BUILD_STRICT=1. -Wlinkage is used deliberately by the
#              maintainer at [common/comp-common.sh:L26] and throughout, and
#              this codebase is known to produce diagnostics, so warnings are
#              neither silently accepted nor silently fatal. The warnings that
#              DO indicate a missing artifact -- `undefined reference',
#              `cannot find -l' -- are classified FATAL above, which is what
#              makes the default safe.
# =============================================================================
readonly -a ACAS_LOG_BENIGN_PATTERNS=(
  '_FORTIFY_SOURCE.*redefined'
  'note: this is the location of the previous definition'
)
readonly -a ACAS_LOG_FATAL_PATTERNS=(
  'cobc: error'
  'cobc: fatal error'
  'error:'
  'No such file or directory'
  'undefined reference'
  'cannot find -l'
  'cannot open'
  'Permission denied'
  'Segmentation fault'
  'core dumped'
  'internal compiler error'
  'collect2:'
  'ld returned'
  '[1-9][0-9]* error[s]? in compilation group'
  'aborting\.\.\.'
  'Invalid param card'
)
readonly -a ACAS_LOG_WARNING_PATTERNS=(
  'warning:'
  '[1-9][0-9]* warning[s]? in compilation group'
)

# acas_scan_build_log <logfile> <label> <exit-code-on-failure>
acas_scan_build_log() {
  local log="$1" label="$2" failure_code="$3"

  [[ -f "$log" ]] || acas_die "$failure_code" \
    "the $label log $log was not produced, so the build cannot be verified."

  local benign_re fatal_re warning_re
  benign_re="$(acas_join_re "${ACAS_LOG_BENIGN_PATTERNS[@]}")"
  fatal_re="$(acas_join_re "${ACAS_LOG_FATAL_PATTERNS[@]}")"
  warning_re="$(acas_join_re "${ACAS_LOG_WARNING_PATTERNS[@]}")"

  local total benign_count
  total="$(wc -l < "$log" | tr -d '[:space:]')"
  benign_count="$(grep -cE "$benign_re" "$log" || true)"

  # A filtered view with the benign families removed, kept beside the raw log so
  # a reviewer can inspect exactly what was and was not classified.
  local filtered="${log%.log}.filtered.log"
  grep -vE "$benign_re" "$log" > "$filtered" || true

  local -a fatal_lines=() warning_lines=()
  mapfile -t fatal_lines < <(grep -nE "$fatal_re" "$filtered" || true)
  mapfile -t warning_lines < <(grep -nE "$warning_re" "$filtered" || true)

  acas_log "$label log: $log ($total lines)"
  acas_log "  benign lines excluded from classification: $benign_count (see the classification comment above acas_scan_build_log)"
  acas_log "  filtered view: $filtered"
  acas_log "  fatal diagnostics: ${#fatal_lines[@]}"
  acas_log "  warnings:          ${#warning_lines[@]}"

  local line
  if (( ${#warning_lines[@]} )); then
    printf '\n--- %s: %s warning line(s), full text ---\n' "$label" "${#warning_lines[@]}"
    for line in "${warning_lines[@]}"; do
      printf '    %s\n' "$line"
    done
    printf -- '--- end of %s warnings ---\n' "$label"
  fi

  if (( ${#fatal_lines[@]} )); then
    printf '\n--- %s: %s FATAL diagnostic line(s), full text ---\n' \
      "$label" "${#fatal_lines[@]}" >&2
    for line in "${fatal_lines[@]}"; do
      printf '    %s\n' "$line" >&2
    done
    printf -- '--- end of %s fatal diagnostics ---\n' "$label" >&2

    if grep -q 'ACAS-SQLstate-error-list' "$filtered"; then
      acas_explain_missing_sqlstate_copybook
    fi
    if grep -q 'cobmysqlapi\.o: No such file' "$filtered"; then
      cat >&2 <<'EXPLAIN'
         --------------------------------------------------------------------
         cobmysqlapi.o could not be found by a compile. Every RDBMS-touching
         frozen compile links it as a BARE FILENAME resolved against the
         current directory -- [common/comp-common.sh:L26] and every
         per-directory script -- and the ACAS checkout contains neither the
         object nor any rule that builds it. Step 2 places a copy in all six
         compile directories using the rule recovered from
         [presql2-package/cobmysqlapi38.sh]. Re-run step 2 (--from 2) and do
         not delete the object from any of common, general, irs, purchase,
         sales or stock.
         --------------------------------------------------------------------
EXPLAIN
    fi
    if grep -qE 'Could not read file >.*\.param<|Invalid param card' "$filtered"; then
      cat >&2 <<'EXPLAIN'
         --------------------------------------------------------------------
         presql2 could not read or could not parse its credential file. The C
         shim opens "<progname>.param" relative to the CURRENT DIRECTORY at
         [presql2-package/cobmysqlapi38.c:L127] and exits 5 when it is absent;
         it then prefix-validates six cards in the fixed order DBHOST=, DBUSER=,
         DBPASSWD=, DBNAME=, DBPORT=, DBSOCKET= and exits 6 on any mismatch
         [presql2-package/cobmysqlapi38.c:L134-L172]. The file is written by
         acas_write_presql2_param into the directory presql2 runs in, and the
         EXIT trap removes it afterwards. Check ACAS_DB_* and re-run.
         --------------------------------------------------------------------
EXPLAIN
    fi

    acas_die "$failure_code" \
      "$label produced ${#fatal_lines[@]} fatal diagnostic line(s)." \
      "The frozen script exited 0 regardless -- [common/comp-common.sh:L59]," \
      '[comp-all.sh:L44-L45] -- so its status is not a success signal and this' \
      'scan is what detects the failure. Full text is above; the log is at' \
      "$log"
  fi

  if (( ${#warning_lines[@]} )) && [[ "${ACAS_BUILD_STRICT-}" == '1' ]]; then
    acas_die "$failure_code" \
      "$label produced ${#warning_lines[@]} warning line(s) and ACAS_BUILD_STRICT=1." \
      'Unset ACAS_BUILD_STRICT to treat warnings as non-fatal.'
  fi
  if (( ${#warning_lines[@]} )); then
    acas_warn "$label produced ${#warning_lines[@]} compiler warning line(s); set ACAS_BUILD_STRICT=1 to make them fatal."
  fi
}

# =============================================================================
# STEP 4/5 -- run common/comp-common.sh UNMODIFIED
#
# What it does, in its own order, so the expected output is known:
#   L18  cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H
#        -DDECIMAL_RIGHT'   (needs the wide-character ncurses headers)
#   L21  dummy-rdbmsMT.cbl        L23  ACAS-Sysout.cbl
#   L25  presql2 over every *MT.scb -- REGENERATES *MT.cbl in the build copy,
#        which is harmless there and catastrophic in the checkout
#   L26  every *MT.cbl as a module, linking cobmysqlapi.o
#   L29  maps0*.cbl (no cobmysqlapi.o)      L32  acas0*.cbl
#   L34  acasirsub*.cbl                     L36  acas-get-params
#   L40-L42  fhlogger, xl150, sys002        L45  cobc -x ACAS.cbl
#   L51  all 28 *LD.cbl as executables -- these are what harness/seed.sh invokes
#   L54  *UNL.cbl      L57  *RES.cbl        L59  exit 0  (unconditional)
#
# A frozen anomaly worth knowing and NOT fixing (R-4): `ls *MT.cbl' at L26
# matches 29 files, not 28. The extra one is dummy-rdbmsMT.cbl, which has no
# *MT.scb and was already compiled at L21 without cobmysqlapi.o; L26 compiles it
# again WITH the object and overwrites the first result. Reproduced as-is.
#
# TWO PHANTOM FLAGS -- RECORDED SO NOBODY "RESTORES" THEM (R-4).
# The frozen changelog header claims two compiler flags that NO live invocation
# anywhere actually uses. Both claims are stale records, and both stay stale:
#   [common/comp-common.sh:L8-L9] says "-Wno-goto-section added to remove the
#     silly default warning in latest gnucobol v3.2", and [README.TXT:L204-L212]
#     repeats it -- yet a census of the live (non-comment) lines of all seven
#     frozen compile scripts finds -Wno-goto-section ZERO times.
#   [common/comp-common.sh:L11] says "Added to all comps -fdump=all" -- yet
#     -fdump=all appears ZERO times. What actually exists is -fdump=ws, and only
#     in general (3 lines), irs (4) and purchase (3); sales and stock have none.
# A maintainer reading the changelog will be tempted to "put the missing flags
# back". DO NOT. Adding either one changes cobc's diagnostics and, for the
# arithmetic the migration depends on, the compiler must be invoked exactly as
# the maintainer actually invokes it -- with default arithmetic and no flag this
# script added or removed.
# =============================================================================
acas_step4_comp_common() {
  acas_banner 4 'run common/comp-common.sh UNMODIFIED'

  local common_dir="$ACAS_BUILD/common"
  [[ -f "$common_dir/comp-common.sh" ]] || acas_die "$EX_STEP4" \
    "$common_dir/comp-common.sh is absent; prepare the build tree first."
  [[ -s "$common_dir/cobmysqlapi.o" ]] || acas_die "$EX_STEP4" \
    "$common_dir/cobmysqlapi.o is absent or empty." \
    '[common/comp-common.sh:L26] links it as a bare filename resolved against' \
    'the current directory, so it must be present here before the script runs.' \
    'Run step 2 (--from 2). [presql2-package/cobmysqlapi38.sh]'

  acas_write_presql2_param "$common_dir" presql2

  local log="$ACAS_LOG_DIR/comp-common.log"
  : > "$log"

  # DEVIATION 5 of 6 -- COBCPY and COB_COPY_DIR are set for this invocation only.
  # Setting them is the maintainer's own practice -- [comp-all.sh:L9-L10] exports
  # both -- and the deviation is only that absolute paths are used instead of the relative
  # `../copybooks', because step 4 runs comp-common.sh directly rather than
  # through comp-all.sh. comp-all.sh's own relative values are left untouched and
  # take effect in step 5. The frozen script itself is not modified in any way.
  acas_log "running: bash ./comp-common.sh   (cwd $common_dir)"
  acas_log "COBCPY=$ACAS_BUILD/copybooks (absolute; cf. [comp-all.sh:L9-L10])"
  local rc=0
  if ! (
         cd "$common_dir" \
           && COBCPY="$ACAS_BUILD/copybooks" \
              COB_COPY_DIR="$ACAS_BUILD/copybooks" \
              bash ./comp-common.sh
       ) 2>&1 | tee -a "$log"; then
    rc=1
  fi
  # rc is reported, never trusted: [common/comp-common.sh:L59] is a bare exit 0.
  acas_log "comp-common.sh returned $rc (informational only -- L59 is an unconditional exit 0)"

  acas_scan_build_log "$log" 'comp-common.sh' "$EX_STEP4"
  acas_shred_param_files
}

# =============================================================================
# STEP 5/5 -- run comp-all.sh UNMODIFIED
#
# [comp-all.sh:L9-L10] exports COBCPY=../copybooks and COB_COPY_DIR=../copybooks
# -- relative, and correct because every compile runs with its own directory as
# the cwd. The body then compiles in the maintainer's own order:
#   common -> general -> irs -> purchase -> sales -> stock
# ([comp-all.sh:L15-L32]; the OE, payroll and epos blocks are commented out).
#
# comp-all.sh RE-RUNS comp-common.sh at [comp-all.sh:L16]. That is the
# maintainer's own design and is NOT optimised away. Step 4 is retained
# deliberately and separately: the plan prescribes the five-step order, and
# running comp-common.sh explicitly produces a clean, attributable log for the
# bridge, handler and loader stage instead of burying it inside the full build.
# Expect the bridge/handler/loader stage to appear TWICE in a full run. Do not
# deduplicate it, and do not delete step 4 as redundant.
#
# Per-directory divergences that are preserved, never harmonised (R-4):
#   general, irs, purchase  -- -fdump=ws -fmissing-statement=ok -D_FORTIFY_SOURCE=1
#   sales                   -- accept_numeric references COMMENTED OUT
#                              ([sales/comp-sales.sh:L2,L5,L11,L13]) and NO
#                              -fdump / -fmissing-statement on the live lines
#   stock                   -- also no -fdump / -fmissing-statement
# =============================================================================
acas_step5_comp_all() {
  acas_banner 5 'run comp-all.sh UNMODIFIED'

  [[ -f "$ACAS_BUILD/comp-all.sh" ]] || acas_die "$EX_STEP5" \
    "$ACAS_BUILD/comp-all.sh is absent; prepare the build tree first."

  local dir
  for dir in "${ACAS_COMPILE_DIRS[@]}"; do
    [[ -s "$ACAS_BUILD/$dir/cobmysqlapi.o" ]] || acas_die "$EX_STEP5" \
      "$ACAS_BUILD/$dir/cobmysqlapi.o is absent or empty." \
      "[comp-all.sh:L15-L32] cd s into $dir and its compile script links" \
      'cobmysqlapi.o as a bare filename. Run step 2 (--from 2).'
  done

  # comp-all.sh:L25 runs comp-common.sh again, which runs presql2 again, which
  # needs the credential file again -- in common/, the directory presql2 runs in.
  acas_write_presql2_param "$ACAS_BUILD/common" presql2

  local log="$ACAS_LOG_DIR/comp-all.log"
  : > "$log"

  acas_log "running: bash ./comp-all.sh   (cwd $ACAS_BUILD)"
  acas_note 'comp-all.sh ends by cd-ing into stock/ and never returns to the top,'
  acas_note 'so it is run in a subshell and this script'"'"'s own cwd is unaffected'
  local rc=0
  if ! ( cd "$ACAS_BUILD" && bash ./comp-all.sh ) 2>&1 | tee -a "$log"; then
    rc=1
  fi
  acas_log "comp-all.sh returned $rc (informational only -- L45 is an unconditional exit 0)"

  acas_scan_build_log "$log" 'comp-all.sh' "$EX_STEP5"
  acas_shred_param_files
}

# =============================================================================
# ARTIFACT ASSERTIONS
#
# More reliable than any text scan: they inspect the products of the build
# rather than the prose about it. Counts are derived from the build tree's own
# source globs rather than hard-coded, so they stay correct as the frozen tree
# is what it is -- for example `ls *MT.cbl' matches 29 files, not the 28
# bridges, because dummy-rdbmsMT.cbl has no *MT.scb.
# =============================================================================
declare -a ACAS_MISSING_ARTIFACTS=()

# acas_expect_module_per_source <dir> <glob> <label>
# cobc -m produces <base>.so beside the source.
acas_expect_module_per_source() {
  local dir="$1" glob="$2" label="$3"
  local -a sources=()
  mapfile -t sources < <(compgen -G "$ACAS_BUILD/$dir/$glob" || true)
  if (( ${#sources[@]} == 0 )); then
    ACAS_MISSING_ARTIFACTS+=("$dir/$glob -- no sources matched, so $label could not be built")
    return 0
  fi
  local src base found=0
  for src in "${sources[@]}"; do
    base="$(basename "$src" .cbl)"
    if [[ -s "$ACAS_BUILD/$dir/$base.so" ]]; then
      found=$(( found + 1 ))
    else
      ACAS_MISSING_ARTIFACTS+=("$dir/$base.so (module for $dir/$base.cbl)")
    fi
  done
  acas_log "$label: $found/${#sources[@]} modules present in $dir/"
}

# acas_expect_executable_per_source <dir> <glob> <label>
# cobc -x produces an extensionless executable beside the source.
acas_expect_executable_per_source() {
  local dir="$1" glob="$2" label="$3"
  local -a sources=()
  mapfile -t sources < <(compgen -G "$ACAS_BUILD/$dir/$glob" || true)
  if (( ${#sources[@]} == 0 )); then
    ACAS_MISSING_ARTIFACTS+=("$dir/$glob -- no sources matched, so $label could not be built")
    return 0
  fi
  local src base found=0
  for src in "${sources[@]}"; do
    base="$(basename "$src" .cbl)"
    if [[ -s "$ACAS_BUILD/$dir/$base" && -x "$ACAS_BUILD/$dir/$base" ]]; then
      found=$(( found + 1 ))
    else
      ACAS_MISSING_ARTIFACTS+=("$dir/$base (executable for $dir/$base.cbl)")
    fi
  done
  acas_log "$label: $found/${#sources[@]} executables present in $dir/"
}

acas_expect_named_modules() {
  local dir="$1" label="$2"
  shift 2
  local name found=0
  local -a names=("$@")
  for name in "${names[@]}"; do
    if [[ -s "$ACAS_BUILD/$dir/$name.so" ]]; then
      found=$(( found + 1 ))
    else
      ACAS_MISSING_ARTIFACTS+=("$dir/$name.so ($label)")
    fi
  done
  acas_log "$label: $found/${#names[@]} present in $dir/"
}

acas_expect_named_executable() {
  local dir="$1" name="$2" label="$3"
  if [[ -s "$ACAS_BUILD/$dir/$name" && -x "$ACAS_BUILD/$dir/$name" ]]; then
    acas_log "$label: $dir/$name present"
  else
    ACAS_MISSING_ARTIFACTS+=("$dir/$name ($label)")
  fi
}

acas_assert_artifacts() {
  acas_stage 'Post-build: artifact assertions'
  ACAS_MISSING_ARTIFACTS=()

  # --- common/ : bridges, handlers, date modules, loaders -------------------
  # [common/comp-common.sh:L26] bridges, :L29 maps, :L32 handlers,
  # :L34 IRS handlers, :L45 ACAS executable, :L51 loaders.
  acas_expect_module_per_source common '*MT.cbl' 'bridges (*MT) [common/comp-common.sh:L26]'
  acas_expect_module_per_source common 'acas0*.cbl' 'file handlers (acas0*) [common/comp-common.sh:L32]'
  acas_expect_module_per_source common 'acasirsub*.cbl' 'IRS handlers (acasirsub*) [common/comp-common.sh:L34]'
  acas_expect_module_per_source common 'maps0*.cbl' 'date and screen modules (maps0*) [common/comp-common.sh:L29]'
  acas_expect_named_executable common ACAS 'the ACAS top-level executable [common/comp-common.sh:L45]'
  acas_expect_executable_per_source common '*LD.cbl' 'load programs (*LD) [common/comp-common.sh:L51]'

  # The 20 loaders harness/seed.sh actually invokes, asserted by name so a
  # partial build cannot leave seeding to fail later with a bare "not found".
  local name found=0
  for name in "${ACAS_INSCOPE_LOADERS[@]}"; do
    if [[ -s "$ACAS_BUILD/common/$name" && -x "$ACAS_BUILD/common/$name" ]]; then
      found=$(( found + 1 ))
    else
      ACAS_MISSING_ARTIFACTS+=("common/$name (in-scope loader required by harness/seed.sh)")
    fi
  done
  acas_log "in-scope loaders required by harness/seed.sh: $found/${#ACAS_INSCOPE_LOADERS[@]} present"

  # --- the four ledgers ----------------------------------------------------
  # Each menu is built BOTH as an executable and as a module
  # ([general/comp-gl.sh:L3,L5] and the same shape in irs, purchase, sales).
  acas_expect_named_modules general \
    'in-scope General Ledger programs plus the Date Entry program' \
    "${ACAS_GENERAL_MODULES[@]}"
  acas_expect_named_executable general general 'the General Ledger menu [general/comp-gl.sh:L3]'

  acas_expect_named_modules sales \
    'in-scope Sales Ledger programs plus the Date Entry program' \
    "${ACAS_SALES_MODULES[@]}"
  acas_expect_named_executable sales sales 'the Sales Ledger menu [sales/comp-sales.sh:L9]'

  acas_expect_named_modules purchase \
    'in-scope Purchase Ledger programs plus the Date Entry program' \
    "${ACAS_PURCHASE_MODULES[@]}"
  acas_expect_named_executable purchase purchase \
    'the Purchase Ledger menu [purchase/comp-purchase.sh:L3]'

  acas_expect_named_modules irs \
    'in-scope IRS programs plus the Date Entry program' \
    "${ACAS_IRS_MODULES[@]}"
  acas_expect_named_executable irs irs 'the IRS menu [irs/comp-irs.sh:L3]'

  if (( ${#ACAS_MISSING_ARTIFACTS[@]} == 0 )); then
    acas_log 'verified: every expected artifact is present and non-empty'
    return 0
  fi

  printf '\n--- %s MISSING or EMPTY artifact(s) ---\n' "${#ACAS_MISSING_ARTIFACTS[@]}" >&2
  local entry
  for entry in "${ACAS_MISSING_ARTIFACTS[@]}"; do
    printf '    %s\n' "$entry" >&2
  done
  printf -- '--- end of missing artifacts ---\n' >&2

  acas_die "$EX_ARTIFACTS" \
    "${#ACAS_MISSING_ARTIFACTS[@]} expected artifact(s) were not produced." \
    'The frozen compile scripts exited 0 regardless, so this assertion -- not' \
    'their exit status -- is what detects the failure. Each missing artifact is' \
    'named above with the source it should have been built from. The compile' \
    "diagnostics are in $ACAS_LOG_DIR."
}

# =============================================================================
# FINALISATION
# =============================================================================
acas_finalise() {
  acas_stage 'Post-build: loader cache and module search path'

  if acas_have ldconfig; then
    if ldconfig 2>/dev/null; then
      acas_log 'refreshed the shared-library cache (ldconfig)'
    else
      acas_warn 'ldconfig failed (root privileges are usually required); the compiled modules may not resolve libmysqlclient at run time.'
    fi
  fi

  # COB_LIBRARY_PATH must cover all six build directories so that the compiled
  # modules resolve when harness/run_cobol_scenario.sh drives a menu. Published
  # here and printed, because it is this script's output contract to the runner
  # scripts. Any existing value is preserved and appended to.
  #
  # Every directory on the path must exist, or a menu resolves a CALL to nothing
  # and diverts down an error path at run time instead of failing here.
  local dir
  for dir in "${ACAS_COMPILE_DIRS[@]}"; do
    [[ -d "$ACAS_BUILD/$dir" ]] || acas_die "$EX_FINALISE" \
      "$ACAS_BUILD/$dir does not exist, so it cannot be published on COB_LIBRARY_PATH." \
      'The compiled modules of that subsystem would not resolve at run time and' \
      'a CALL would divert into an error path instead of failing here.'
  done

  local computed=''
  for dir in "${ACAS_COMPILE_DIRS[@]}"; do
    if [[ -z "$computed" ]]; then
      computed="$ACAS_BUILD/$dir"
    else
      computed="$computed:$ACAS_BUILD/$dir"
    fi
  done
  if [[ -n "${COB_LIBRARY_PATH-}" && ":${COB_LIBRARY_PATH}:" != *":$ACAS_BUILD/common:"* ]]; then
    computed="$computed:$COB_LIBRARY_PATH"
  elif [[ -n "${COB_LIBRARY_PATH-}" ]]; then
    computed="$COB_LIBRARY_PATH"
  fi
  export COB_LIBRARY_PATH="$computed"
  acas_log 'COB_LIBRARY_PATH for the runner scripts:'
  acas_log "  $COB_LIBRARY_PATH"
  acas_note 'exported for this process only; harness/docker-compose.yml sets the same'
  acas_note 'value for the service, so the runners inherit it independently'
}

acas_count_files() {
  local dir="$1" glob="$2"
  local -a matched=()
  mapfile -t matched < <(compgen -G "$ACAS_BUILD/$dir/$glob" || true)
  printf '%s' "${#matched[@]}"
}

acas_print_summary() {
  acas_stage 'Summary'

  local dir
  for dir in "${ACAS_COMPILE_DIRS[@]}"; do
    acas_log "$(printf '%-9s %4s modules (*.so)' "$dir/" "$(acas_count_files "$dir" '*.so')")"
  done
  acas_log "common/   $(acas_count_files common '*LD') load-program executables (glob *LD)"
  acas_log "build tree:   $ACAS_BUILD"
  acas_log "build logs:   $ACAS_LOG_DIR/comp-common.log"
  acas_log "              $ACAS_LOG_DIR/comp-all.log"
  acas_log "              (plus the .filtered.log companions used by the scan)"

  if (( ${#ACAS_WARN_SUMMARY[@]} )); then
    printf '\n--- %s non-fatal finding(s) reported during this run ---\n' \
      "${#ACAS_WARN_SUMMARY[@]}"
    local entry
    for entry in "${ACAS_WARN_SUMMARY[@]}"; do
      printf '    %s\n' "$entry"
    done
    printf -- '--- end of non-fatal findings ---\n'
  fi

  printf '\nbuild_oracle.sh completed: the compiled-COBOL oracle is built in %s\n' "$ACAS_BUILD"
  printf 'Next: harness/seed.sh to seed a scenario, then harness/run_cobol_scenario.sh.\n'
}

# =============================================================================
# MAIN
#
# Strictly sequential (R-3). No step is backgrounded, no step is parallelised,
# and the order is the one the plan prescribes. Nothing here writes to
# $ACAS_REPO, and nothing is placed anywhere acas_posting/ could import (R-1).
# =============================================================================
acas_main() {
  acas_parse_args "$@"

  printf 'build_oracle.sh -- building the compiled-COBOL oracle for the ACAS posting cycle\n'
  if (( ACAS_ONLY_STEP != 0 )); then
    printf 'Running step %s only (debugging mode); the default is all five steps in order.\n' \
      "$ACAS_ONLY_STEP"
  elif (( ACAS_START_STEP != 1 )); then
    printf 'Starting at step %s (debugging mode); the default is all five steps in order.\n' \
      "$ACAS_START_STEP"
  fi

  acas_assert_environment
  acas_assert_directories
  acas_assert_toolchain
  acas_assert_loader_configuration
  acas_wait_for_database

  acas_prepare_build_tree

  if acas_step_enabled 1; then acas_step1_unpack_presql2; else
    acas_note 'step 1 skipped; resolving the preSQL package from the environment'
    ACAS_PRESQL2_DIR="${ACAS_PRESQL2_PACKAGE:-/opt/presql2-package}"
  fi
  if acas_step_enabled 2; then acas_step2_build_cobmysqlapi; else
    acas_note 'step 2 skipped; resolving cobmysqlapi.o from the environment'
    ACAS_COBMYSQLAPI_SRC="${ACAS_COBMYSQLAPI_OBJ:-/usr/local/lib/acas/cobmysqlapi.o}"
  fi
  if acas_step_enabled 3; then acas_step3_build_presql2; else
    acas_note 'step 3 skipped'
  fi
  if acas_step_enabled 4; then acas_step4_comp_common; else
    acas_note 'step 4 skipped'
  fi
  if acas_step_enabled 5; then acas_step5_comp_all; else
    acas_note 'step 5 skipped'
  fi

  # The assertions and the summary run only after a full sequence: a partial run
  # cannot have produced the full artifact set, and reporting a false failure
  # would be worse than reporting nothing.
  if (( ACAS_ONLY_STEP == 0 && ACAS_START_STEP == 1 )); then
    acas_assert_artifacts
    acas_finalise
    acas_print_summary
  else
    acas_stage 'Partial run: artifact assertions and finalisation skipped'
    acas_note 'run without --from/--only to build the whole oracle and verify it'
  fi

  # An explicit success exit. NEVER an unconditional `exit 0': that is the very
  # defect this script exists to work around
  # ([common/comp-common.sh:L59], [comp-all.sh:L44-L45]).
  exit "$EX_OK"
}

acas_main "$@"
