#!/usr/bin/env bash
# harness/seed.sh -- stage 1 of the parity protocol: load the Cobol flat files
# into ACASDB through the frozen common/*LD.cbl loader programs, so that both
# cycles start from identical state. Run `--help' for the options, the loader
# list and the exit codes.
#
# WHY IT REPRODUCES common/masterLD.sh RATHER THAN INVOKING IT. Two reasons, the
# second decisive: its author marks it untested ([common/masterLD.sh:L4-L5]), and
# it cannot execute at all -- all 24 loader lines [common/masterLD.sh:L93-L116]
# are `if [ -e X.dat ];  then YLD fi' with no `;' or newline before `fi', so
# `bash -n' rejects the file. The frozen file is NOT repaired, sed-ed, copied or
# sourced (R-3, R-4); its per-file CONTRACT is reproduced here in valid shell.
#
# Two invariants that decide whether a seed is comparable:
#   * loader ORDER is the frozen order, and the system block runs systemLD then
#     sys4LD, finalLD, dfltLD -- a later loader reads what an earlier one wrote.
#   * loader exit codes above 63 ABORT the load rather than being logged, with
#     distinct codes for unset RDBMS parameters, an unset database flag and a
#     write error, and autocommit must be OFF because the batch loader turns it
#     off explicitly [common/glbatchLD.cbl:L9-L13].

set -Eeuo pipefail

# Word splitting on newlines and tabs only, so a path containing a space can
# never be split apart. Every expansion below is quoted regardless.
IFS=$'\n\t'

# An unmatched glob expands to nothing rather than to the pattern text.
shopt -s nullglob

# Nothing this script writes is group- or world-readable.
umask 077

readonly EX_OK=0
readonly EX_USAGE=70          # bad command line
readonly EX_PRECONDITION=71   # environment, directory or loader assertion
readonly EX_DATABASE=72       # MariaDB unreachable, or credentials rejected
readonly EX_AUTOCOMMIT=73     # autocommit is not OFF -- see acas_assert_autocommit
readonly EX_TIMEOUT=74        # a load program or client exceeded its deadline
readonly EX_FIXTURE=75        # the scenario's declared seed files are not staged

# Finite deadlines. Every external process this script spawns runs under one:
# the 20 compiled load programs and every MariaDB client invocation.
readonly ACAS_TIMEOUT_MAX=86400
ACAS_TIMEOUT_GRACE="${ACAS_TIMEOUT_GRACE-}"         # TERM-to-KILL grace period
ACAS_TIMEOUT_LOADER="${ACAS_TIMEOUT_LOADER-}"        # one compiled load program
ACAS_TIMEOUT_CLIENT="${ACAS_TIMEOUT_CLIENT-}"        # one MariaDB client invocation
ACAS_TIMEOUT_RESOLVED=''      # out-parameter of acas_timeout_seconds
declare -a ACAS_DEADLINE_ARGV=()   # populated by acas_deadline_prefix

# THE SYSTEM-FILE BLOCK -- [common/masterLD.sh:L50-L88] Frozen order, and the
# reason for it, [common/masterLD.sh:L47-L48] verbatim.
readonly -a ACAS_SEED_SYSTEM_BLOCK=(
  'systemLD:gt63:L52,L56:SYSTEM-REC'
  'sys4LD:gt63:L61,L65:SYSTOT-REC'
  'finalLD:gt63:L70,L74:SYSFINAL-REC'
  'dfltLD:ne0:L79,L83:SYSDEFLT-REC'
)

# The one flat file the whole system block is guarded on,
# [common/masterLD.sh:L51].
readonly ACAS_SEED_SYSTEM_FLAT_FILE='system.dat'

readonly ACAS_SEED_SYSTEM_ABORT_MSG='Problem with data in system.dat - Aborting'

# The two frozen return-code tests, quoted for the diagnostics so a reader can
# match a message straight back to the frozen line.
readonly ACAS_SEED_TEST_TEXT_GT63="if [ \$rc -gt 63 ]"
readonly ACAS_SEED_TEST_TEXT_NE0="if [ \$rc != 0 ]"

# THE 16 IN-SCOPE MAPPINGS -- [common/masterLD.sh:L93-L116] FROZEN ORDER
# PRESERVED.
readonly -a ACAS_SEED_MAPPINGS=(
  'analysis.dat:analLD:L93:ANALYSIS-REC'
  'batch.dat:glbatchLD:L94:GLBATCH-REC'
  'invoice.dat:slinvoiceLD:L98:SAINVOICE-REC + SAINV-LINES-REC'
  'irsacnts.dat:irsnominalLD:L99:IRSNL-REC'
  'irsdflt.dat:irsdfltLD:L100:IRSDFLT-REC'
  'irsfinal.dat:irsfinalLD:L101:IRSFINAL-REC'
  'irspost.dat:irspostingLD:L102:IRSPOSTING-REC'
  'ledger.dat:nominalLD:L103:GLLEDGER-REC'
  'openitm3.dat:otm3LD:L104:SAITM3-REC'
  'openitm5.dat:otm5LD:L105:PUITM5-REC'
  'pinvoice.dat:plinvoiceLD:L107:PUINVOICE-REC + PUINV-LINES-REC'
  'posting.dat:glpostingLD:L109:GLPOSTING-REC'
  'postings2irs.dat:slpostingLD:L110:PSIRSPOST-REC'
  'purchled.dat:purchLD:L111:PULEDGER-REC'
  'salesled.dat:salesLD:L112:SALEDGER-REC'
  'value.dat:valueLD:L116:VALUEANAL-REC'
)

readonly -a ACAS_SEED_OUT_OF_SCOPE=(
  'delfolio.dat:delfolioLD:L95:PUDELINV-REC'
  'delinvno.dat:sldelinvnosLD:L96:SADELINV-REC'
  'delivery.dat:deliveryLD:L97:DELIVERY-REC'
  'pay.dat:paymentsLD:L106:PLPAY-REC + PLPAY-RECrg01'
  'plautogen.dat:plautogenLD:L108:PUAUTOGEN-REC + PUAUTOGEN-LINES-REC'
  'slautogen.dat:slautogenLD:L113:SAAUTOGEN-REC + SAAUTOGEN-LINES-REC'
  'staudit.dat:auditLD:L114:STOCKAUDIT-REC'
  'stockctl.dat:stockLD:L115:STOCK-REC'
)

# The interactive tail this script does NOT reproduce,
# [common/masterLD.sh:L119].
readonly ACAS_SEED_SYSOUT_LOG='SYS-DISPLAY.log'
readonly ACAS_SEED_COMPLETE_MSG='All loads complete but check SYS-DISPLAY.log'

readonly -a ACAS_SEED_LOADER_PATHS=(
  /usr/local/lib/gnucobol
  /usr/local/lib
  /usr/local/mysql/lib
  /usr/lib
)

# The environment contract, identical in shape to the one
# harness/build_oracle.sh asserts, so a container configured for one stage is
# configured for both.
readonly -a ACAS_SEED_REQUIRED_ENV_NONEMPTY=(
  ACAS_REPO ACAS_BUILD ACAS_DATA ACAS_OUT
  ACAS_DB_HOST ACAS_DB_PORT ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD
  ACAS_LEDGERS ACAS_BIN
)
readonly -a ACAS_SEED_REQUIRED_ENV_DECLARED=(
  ACAS_DB_SOCKET
)

ACAS_SEED_DATA_DIR=''          # --data-dir, defaults to $ACAS_DATA
ACAS_SEED_SCENARIO=''          # optional positional scenario file
ACAS_SEED_DRY_RUN=0            # --dry-run
ACAS_SEED_LOG=''               # $ACAS_OUT/seed/seed.log
ACAS_SEED_JOBSTATUS=0          # JOBSTATUS, tracked as [common/masterLD.sh:L50]
ACAS_SEED_RAN=0                # loaders actually executed
ACAS_SQL_OUT=''                # last successful scalar query result
ACAS_SQL_DIAG=''               # last client diagnostic, for error messages
# The size of the append-only loader log BEFORE the first loader ran, so the
# completion report can bound itself to what THIS run appended (deviation D6).
# Empty until `acas_seed_note_sysout_baseline' has run.
ACAS_SEED_SYSOUT_BASELINE=''
ACAS_SEED_FIXTURE_DIR=''       # scenario fixture staged by acas_stage_scenario_seed
declare -a ACAS_SEED_ONLY=()         # --only, validated loader names
declare -a ACAS_SEED_SUMMARY=()      # the final table, one row per loader
declare -a ACAS_SEED_WARN_SUMMARY=() # non-fatal findings, replayed at the end
declare -a ACAS_SEED_TLS_VARIANTS=()

# Stage banners are numbered so the log reads as the deterministic staged
# orchestration the plan prescribes (R-6): explicit, ordered, individually
# reported, individually asserted.

# Append to the run log if it is open yet. Silent before acas_open_log runs, so
# early usage errors still print without needing a log.
acas_tee() {
  if [[ -n "$ACAS_SEED_LOG" ]]; then
    printf '%s\n' "$*" >>"$ACAS_SEED_LOG" 2>/dev/null || true
  fi
}

acas_stage() {
  printf '\n==> %s\n' "$1"
  acas_tee ""
  acas_tee "==> $1"
}

acas_log() {
  printf '    %s\n' "$*"
  acas_tee "    $*"
}

acas_note() {
  printf '    note: %s\n' "$*"
  acas_tee "    note: $*"
}

acas_warn() {
  printf 'WARNING: %s\n' "$*" >&2
  acas_tee "WARNING: $*"
  ACAS_SEED_WARN_SUMMARY+=("$*")
}

acas_die() {
  local code="$1"
  shift
  printf 'FATAL: %s\n' "$1" >&2
  acas_tee "FATAL: $1"
  shift
  local line
  for line in "$@"; do
    printf '       %s\n' "$line" >&2
    acas_tee "       $line"
  done
  exit "$code"
}

acas_have() {
  command -v "$1" >/dev/null 2>&1
}

# ---------------------------------------------------------------------------
#  THE CLIENT-DIAGNOSTIC SUMMARY  (OBS-008)
#
#  A database client's diagnostic is text the SERVER supplied, captured here with
#  `2>&1`, and it is NOT safe to replay:
#
#    * it routinely names the account and the host -- "Access denied for user
#      'acas'@'db.internal'" -- and on a statement failure it can quote the
#      statement and its parameters, which are live accounting values (CWE-532);
#    * it is multi-line and arbitrary, so a newline inside it forges a further
#      line in whatever log collects this script's output (CWE-117);
#    * these scripts run under Compose, where standard output and standard error
#      are collected as container logs and kept.
#
#  So the RAW text is persisted to a private mode-0600 file and never printed,
#  and the console gets a bounded, identity-free summary: a token from a fixed
#  vocabulary, the client's own numeric error and SQLSTATE when it printed them,
#  the size, and the artifact's path and SHA-256. This is the same
#  console/artifact split `harness/diff_states.py` and `harness/normalize.py`
#  apply to their own detail, with the same reasoning and the same vocabulary.
#
#  NOTHING BELOW ECHOES A BYTE OF ITS INPUT. The category comes from a `case`
#  over fixed globs; the error and SQLSTATE are re-validated against their
#  documented shapes and replaced by `unknown` when they do not match, so a
#  server that returned `28000\nERROR: forged` cannot get that through.
# ---------------------------------------------------------------------------

#: Where the raw text of the most recent diagnostic was kept, or empty when none
#: was produced or it could not be persisted.
ACAS_DIAG_ARTIFACT=''

# acas_diag_category <raw>
# Classify a client diagnostic. Echoes ONE token and never any input byte.
acas_diag_category() {
  local raw="$1"

  if [[ -z "${raw//[[:space:]]/}" ]]; then
    printf 'no-diagnostic'
    return 0
  fi
  case "$raw" in
    *'Access denied'*)                          printf 'access-denied' ;;
    *'Unknown database'*)                       printf 'unknown-database' ;;
    *'Unknown MySQL server host'*)              printf 'host-unresolvable' ;;
    *'is not allowed to connect'*)              printf 'host-not-permitted' ;;
    *"Can't connect"*|*'Connection refused'*)   printf 'connect-refused' ;;
    *'did not answer within'*|*'timed out'*|*'Timeout'*|*'timeout expired'*)
                                                printf 'timeout' ;;
    *'Lost connection'*|*'gone away'*)          printf 'connection-lost' ;;
    *'Lock wait timeout'*)                      printf 'lock-wait-timeout' ;;
    *'Deadlock found'*)                         printf 'deadlock' ;;
    *'Duplicate entry'*)                        printf 'duplicate-key' ;;
    *"doesn't exist"*|*'Unknown table'*)        printf 'table-missing' ;;
    *'Unknown column'*)                         printf 'column-missing' ;;
    *'error in your SQL syntax'*)               printf 'syntax-error' ;;
    *'command denied'*|*'insufficient privileges'*)
                                                printf 'grant-missing' ;;
    *'SSL'*|*'TLS'*)                            printf 'tls-refused' ;;
    *'read-only'*)                              printf 'server-read-only' ;;
    *)                                          printf 'unclassified' ;;
  esac
}

# acas_diag_code <raw>
# Echo `<error>/<sqlstate>` from a `ERROR 1045 (28000)` prefix, each re-validated
# against its documented shape and replaced by `unknown` when it does not match.
acas_diag_code() {
  local raw="$1" code='' state=''

  code="$(printf '%s\n' "$raw" \
    | sed -n 's/.*ERROR \([0-9][0-9]*\).*/\1/p' | head -n 1)"
  state="$(printf '%s\n' "$raw" \
    | sed -n 's/.*ERROR [0-9][0-9]* (\([0-9A-Za-z][0-9A-Za-z]*\)).*/\1/p' \
    | head -n 1)"
  [[ "$code" =~ ^[0-9]{1,5}$ ]] || code='unknown'
  # SQLSTATE is five alphanumeric characters by definition
  # [copybooks/wsfnctn.cob:L51]; anything else is not one.
  [[ "$state" =~ ^[0-9A-Za-z]{5}$ ]] || state='unknown'
  printf '%s/%s' "$code" "$state"
}

# acas_diag_sha256 <path>
# Self-contained on purpose: this runs on abort paths, so it must not depend on
# any deadline or digest machinery having been initialised. Echoes nothing on
# failure.
acas_diag_sha256() {
  local path="$1" digest=''

  if command -v sha256sum >/dev/null 2>&1; then
    digest="$(sha256sum -- "$path" 2>/dev/null)" || return 0
    printf '%s' "${digest%% *}"
    return 0
  fi
  command -v python3 >/dev/null 2>&1 || return 0
  python3 - "$path" 2>/dev/null <<'PY' || return 0
import hashlib
import sys

digest = hashlib.sha256()
with open(sys.argv[1], 'rb') as handle:
    for block in iter(lambda: handle.read(1 << 16), b''):
        digest.update(block)
sys.stdout.write(digest.hexdigest())
PY
}

# acas_diag_persist <raw>
# Write the raw text to a private mode-0600 file and set ACAS_DIAG_ARTIFACT.
# Leaves it EMPTY when nothing could be written; never aborts, because this runs
# on paths that are already reporting a failure.
acas_diag_persist() {
  local raw="$1" dir='' path=''

  ACAS_DIAG_ARTIFACT=''
  dir="$(mktemp -d "${TMPDIR:-/tmp}/acas-diag-XXXXXXXX" 2>/dev/null)" || return 0
  # `mktemp -d` creates 0700; the file is narrowed to 0600 explicitly because
  # this script's `umask 077` governs creation but is not a guarantee a reader
  # can check.
  path="$dir/client-diagnostic.txt"
  printf '%s\n' "$raw" >"$path" 2>/dev/null || return 0
  chmod 600 -- "$path" 2>/dev/null || true
  ACAS_DIAG_ARTIFACT="$path"
}

# acas_diag_summary [raw]
# Echo the bounded, identity-free summary. Defaults to the script's own
# last-diagnostic variable so a call site reads as one word.
acas_diag_summary() {
  local raw="${1-$ACAS_SQL_DIAG}" category='' code='' lines=0 bytes=0 digest=''

  category="$(acas_diag_category "$raw")"
  if [[ "$category" == 'no-diagnostic' ]]; then
    printf 'client diagnostic: none was produced'
    return 0
  fi
  code="$(acas_diag_code "$raw")"
  lines="$(printf '%s\n' "$raw" | wc -l | tr -d '[:space:]')"
  bytes="$(printf '%s' "$raw" | wc -c | tr -d '[:space:]')"
  acas_diag_persist "$raw"
  if [[ -n "$ACAS_DIAG_ARTIFACT" ]]; then
    digest="$(acas_diag_sha256 "$ACAS_DIAG_ARTIFACT")"
    printf 'client diagnostic: %s (error %s, %s line(s), %s byte(s)); the raw text is in %s (mode 0600%s)' \
      "$category" "$code" "$lines" "$bytes" "$ACAS_DIAG_ARTIFACT" \
      "${digest:+, sha256=$digest}"
    return 0
  fi
  printf 'client diagnostic: %s (error %s, %s line(s), %s byte(s)); the raw text could NOT be persisted, so it is not available -- it is deliberately NOT printed here' \
    "$category" "$code" "$lines" "$bytes"
}

# Join the remaining arguments with single spaces. Needed because IFS is
# $'\n\t', so a bare "${array[*]}" would join on a NEWLINE and break a one-line
# message across several lines.
acas_join_words() {
  local IFS=' '
  printf '%s' "$*"
}


# acas_timeout_seconds <env-var-name> <default> Publishes the validated budget
# in ACAS_TIMEOUT_RESOLVED.
acas_timeout_seconds() {
  local name="$1" default="$2" value
  ACAS_TIMEOUT_RESOLVED=''
  value="${!name-}"
  [[ -n "$value" ]] || value="$default"

  if [[ ! "$value" =~ ^[0-9]+$ ]]; then
    acas_die "$EX_USAGE" \
      "$name must be a whole number of seconds; got '$value'."
  fi
  # 10# forces base 10: a zero-padded 08 would otherwise be an invalid octal.
  value=$(( 10#$value ))
  if (( value < 1 )); then
    acas_die "$EX_USAGE" \
      "$name must be at least 1 second; got '$value'." \
      'A zero budget means "block forever", the condition deadlines exist to' \
      'rule out. There is deliberately no way to disable them.'
  fi
  if (( value > ACAS_TIMEOUT_MAX )); then
    acas_die "$EX_USAGE" \
      "$name must not exceed $ACAS_TIMEOUT_MAX seconds; got '$value'."
  fi
  ACAS_TIMEOUT_RESOLVED="$value"
}

# Resolve every budget once, before any external process is spawned.
acas_resolve_deadlines() {
  acas_have timeout || acas_die "$EX_PRECONDITION" \
    'timeout is not on the PATH.' \
    'It is part of coreutils and every external process this script spawns' \
    'runs under it. harness/Dockerfile.gnucobol provides it.'

  acas_timeout_seconds ACAS_TIMEOUT_GRACE 15
  ACAS_TIMEOUT_GRACE="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_LOADER 600
  ACAS_TIMEOUT_LOADER="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_CLIENT 30
  ACAS_TIMEOUT_CLIENT="$ACAS_TIMEOUT_RESOLVED"
  readonly ACAS_TIMEOUT_GRACE ACAS_TIMEOUT_LOADER ACAS_TIMEOUT_CLIENT

  local budget
  for budget in "$ACAS_TIMEOUT_GRACE" "$ACAS_TIMEOUT_LOADER" "$ACAS_TIMEOUT_CLIENT"; do
    [[ "$budget" =~ ^[1-9][0-9]*$ ]] || acas_die "$EX_PRECONDITION" \
      'a deadline budget resolved empty or non-positive (internal invariant).'
  done
}

acas_deadline_prefix() {
  ACAS_DEADLINE_ARGV=(
    timeout
    "--kill-after=$ACAS_TIMEOUT_GRACE"
    --signal=TERM
    "$1"
  )
}

# acas_is_timeout_status <rc> <elapsed> <budget> True when <rc> means "the
# deadline expired" rather than "it ran and failed".
acas_is_timeout_status() {
  local rc="$1" elapsed="$2" budget="$3"
  if (( rc == 124 || rc == 137 )); then
    return 0
  fi
  if (( rc != 0 && elapsed >= budget )); then
    return 0
  fi
  return 1
}

acas_assert_not_timed_out() {
  local rc="$1" elapsed="$2" budget="$3" budget_var="$4" label="$5"
  if ! acas_is_timeout_status "$rc" "$elapsed" "$budget"; then
    return 0
  fi
  acas_die "$EX_TIMEOUT" \
    "$label exceeded its ${budget}s deadline and was terminated." \
    "Raise $budget_var if this host is slower than the budget assumes." \
    'A load program that blocks is usually waiting on a terminal: the frozen' \
    'family prompts, and this harness is headless by design.' \
    "The child was sent TERM at the deadline and KILL ${ACAS_TIMEOUT_GRACE}s later."
}

# acas_assert_outside_repo <label> <path> Nothing this script writes may land
# inside $ACAS_REPO.
acas_assert_outside_repo() {
  local label="$1" path="$2"
  local repo_real target probe

  repo_real="$(readlink -f -- "$ACAS_REPO" 2>/dev/null || printf '%s' "$ACAS_REPO")"

  # Resolve the nearest existing ancestor so a not-yet-created target is still
  # judged by where it would actually be created.
  probe="$path"
  while [[ -n "$probe" && ! -e "$probe" ]]; do
    local parent="${probe%/*}"
    [[ "$parent" != "$probe" ]] || parent=''
    probe="$parent"
  done
  [[ -n "$probe" ]] || probe='/'
  target="$(readlink -f -- "$probe" 2>/dev/null || printf '%s' "$probe")"

  if [[ "$target" == "$repo_real" || "$target" == "$repo_real"/* ]]; then
    acas_die "$EX_PRECONDITION" \
      "$label resolves inside the frozen checkout." \
      "  $label: $path" \
      "  resolves to: $target" \
      "  ACAS_REPO:   $repo_real" \
      'Nothing may ever be written into the checkout. Point it at a volume' \
      'outside ACAS_REPO -- /data or /out in the Compose stack.'
  fi
  if [[ "$repo_real" == "$target"/* ]]; then
    acas_die "$EX_PRECONDITION" \
      "$label CONTAINS the frozen checkout." \
      "  $label: $path" \
      "  resolves to: $target" \
      "  ACAS_REPO:   $repo_real" \
      'Writing through a root that contains the checkout can reach the frozen' \
      'files. Point it at a directory disjoint from ACAS_REPO.'
  fi
}

# Split a `<flat file>:<loader>:<locator>:<table>' entry into four globals.
# Done with parameter expansion rather than `read -r -d' because the final
# field may itself contain spaces.
ACAS_E_FLAT=''
ACAS_E_LOADER=''
ACAS_E_LOCATOR=''
ACAS_E_TABLE=''
acas_split_entry() {
  local entry="$1"
  ACAS_E_FLAT="${entry%%:*}"
  entry="${entry#*:}"
  ACAS_E_LOADER="${entry%%:*}"
  entry="${entry#*:}"
  ACAS_E_LOCATOR="${entry%%:*}"
  ACAS_E_TABLE="${entry#*:}"
}

ACAS_S_LOADER=''
ACAS_S_TEST=''
ACAS_S_LOCATOR=''
ACAS_S_TABLE=''
acas_split_system_entry() {
  local entry="$1"
  ACAS_S_LOADER="${entry%%:*}"
  entry="${entry#*:}"
  ACAS_S_TEST="${entry%%:*}"
  entry="${entry#*:}"
  ACAS_S_LOCATOR="${entry%%:*}"
  ACAS_S_TABLE="${entry#*:}"
}

acas_summary_row() {
  ACAS_SEED_SUMMARY+=("$(printf '%-14s %-17s %-8s %-5s %s' "$1" "$2" "$3" "$4" "$5")")
}

# Membership test over an array passed by name, so the arrays stay readonly.
acas_in_list() {
  local needle="$1"
  shift
  local element
  for element in "$@"; do
    if [[ "$element" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

# Create a file that cannot be hijacked: a symlink or non-regular path is refused
# rather than followed, and the file is created under `set -C' (O_EXCL) so it can
# neither be pre-created by another user nor widened between create and chmod.
acas_create_private_file() {
  local path="$1" what="$2"

  if [[ -L "$path" ]]; then
    acas_die "$EX_PRECONDITION" \
      "$what is a SYMLINK: $path" \
      'It is refused rather than followed. Writing through it would truncate' \
      'whatever it points at, and would then expose this run to whoever placed' \
      'it. Remove the link and run again.'
  fi
  if [[ -e "$path" ]] && [[ ! -f "$path" ]]; then
    acas_die "$EX_PRECONDITION" \
      "$what exists and is not a regular file: $path" \
      'Refusing to write to a directory, device or socket.'
  fi
  rm -f -- "$path" 2>/dev/null || true

  # noclobber => O_EXCL. A subshell so the option change cannot leak into the
  # rest of the script.
  if ! (set -C; : >"$path") 2>/dev/null; then
    acas_die "$EX_PRECONDITION" \
      "could not create $what at $path." \
      'Either the directory is not writable, or something created the name in' \
      'the instant between the symlink check and the exclusive create -- which' \
      'is exactly the race the exclusive create exists to lose safely.'
  fi
  chmod 600 -- "$path" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "could not restrict $what to mode 600: $path"
}

# TRAPS There is no credential FILE to shred.
ACAS_SEED_CURRENT_LOADER=''

# shellcheck disable=SC2317  # reached only through the ERR trap installed below,
# which shellcheck cannot follow; the body is live and is exercised by the
# negative validation cases.
acas_on_err() {
  local status="$1" line="$2" cmd="$3"
  printf '\nFATAL: unexpected failure at %s line %s (status %s).\n' \
    "${BASH_SOURCE[0]}" "$line" "$status" >&2
  printf '       failing command: %s\n' "$cmd" >&2
  if [[ -n "$ACAS_SEED_CURRENT_LOADER" ]]; then
    printf '       while seeding with loader: %s\n' "$ACAS_SEED_CURRENT_LOADER" >&2
  fi
  acas_tee "FATAL: unexpected failure at line $line (status $status): $cmd"
}
trap 'acas_on_err "$?" "$LINENO" "$BASH_COMMAND"' ERR

# shellcheck disable=SC2317  # reached only through the EXIT trap installed below.
acas_on_exit() {
  local status="$1"
  if (( status == 0 )); then
    return 0
  fi
  # The partial-seed warning is only true once a loader has actually run.
  if (( ACAS_SEED_RAN > 0 )); then
    printf '\nharness/seed.sh exiting with status %s after running %s load program(s).\n' \
      "$status" "$ACAS_SEED_RAN" >&2
    printf 'The database may be PARTIALLY seeded: run harness/reset_db.sh before drawing\n' >&2
    printf 'any conclusion from a state diff.\n' >&2
  else
    printf '\nharness/seed.sh exiting with status %s. No load program ran, so the database\n' \
      "$status" >&2
    printf 'is untouched.\n' >&2
  fi
  acas_tee "harness/seed.sh exiting with status $status after $ACAS_SEED_RAN load program(s)"
}
trap 'acas_on_exit "$?"' EXIT

acas_usage() {
  cat <<'USAGE'
harness/seed.sh -- seed the frozen ACASDB schema from the ACAS Cobol flat files.

Reproduces the flat-file-to-loader contract of common/masterLD.sh
[common/masterLD.sh:L44-L115] and its exit-code semantics. It NEVER executes
that script: its author marks it untested [common/masterLD.sh:L4-L5] and it is
not valid shell -- `bash -n' rejects it at line 124 because its 24 loader lines
[common/masterLD.sh:L93-L116] omit the `;' before `fi'. The frozen file is not
fixed (R-3, R-4).

Usage:
  harness/seed.sh [options] [<scenario.yaml>]

Arguments:
  <scenario.yaml>     Optional, and BINDING when given. The canonical eight-stage
                      invocation documented in harness/docker-compose.yml
                      works verbatim. The scenario's declared
                      `seed_files' (with optional `seed_dir', defaulting to a
                      directory beside the scenario named after it) are staged
                      into a FRESH scenario-owned fixture directory under the
                      data directory, an identity marker naming the files and
                      their SHA-256 digests is written, and the load programs
                      then read that fixture and nothing else.

                      Binding rather than merely logged, because a scenario that
                      is only recorded would let the seed come from whatever flat
                      files happened to be in the data directory -- and the
                      resulting dump would then be attributed to a scenario it
                      was never derived from. system.dat must be among the
                      declared files: the frozen order seeds the system block
                      first and unconditionally [common/masterLD.sh:L50-L88], and
                      it is what carries Run-Date
                      [copybooks/wssystem.cob:L67] and the three-state IRS
                      fan-out switch [copybooks/wssystem.cob:L179-L181].

                      harness/reset_db.sh asserts the same marker after its
                      re-seed, which is how stage 5 of the parity protocol
                      demonstrably re-seeds from the fixture stage 1 used.

                      With no scenario given, the ambient data directory is
                      seeded exactly as before -- there is no scenario to bind.

Options:
  --data-dir PATH     Directory holding the Cobol flat files. Default $ACAS_DATA.
                      The frozen script hard-codes `cd ~/ACAS'
                      [common/masterLD.sh:L45,L27-L28]; this is deviation D2.
  --only LIST         Comma-separated loader names to run, for debugging. Each
                      must be one of the 20 in-scope loaders. The 8 out-of-scope
                      loaders are rejected by name.
  --dry-run           Print the plan -- every flat file, its loader, and the
                      decision -- and exit without running anything or touching
                      the database.
  -h, --help          Print this help and exit 0.

Required environment (harness/docker-compose.yml supplies all of it):
  ACAS_REPO           read-only checkout            (mounted ../:/repo:ro)
  ACAS_BUILD          build tree from build_oracle.sh (volume /build)
  ACAS_DATA           writable ledger/data area     (volume /data)
  ACAS_OUT            writable output area          (volume /out)
  ACAS_LEDGERS        the path every loader prefixes onto every file name
                      [copybooks/Proc-Get-Env-Set-Files.cob:L125-L136].
                      MUST be non-blank or every loader waits on an ACCEPT
                      [copybooks/Proc-Get-Env-Set-Files.cob:L20-L28].
  ACAS_BIN            MUST be non-blank, for the same reason.
  ACAS_DB_HOST        MariaDB host
  ACAS_DB_PORT        MariaDB port
  ACAS_DB_NAME        target schema
  ACAS_DB_USER        MariaDB user      (max 12 chars, [copybooks/wsfnctn.cob:L56-L62])
  ACAS_DB_PASSWORD    MariaDB password  (max 12 chars; never echoed, never logged)
  ACAS_DB_SOCKET      may be EMPTY (TCP), but must be declared

Optional environment:
  ACAS_SEED_STRICT=1        OPT IN to aborting on the first loader return code
                            the frozen test tolerates -- 1 through 63, of which
                            16 is "error writing data to rdb"
                            [common/masterLD.sh:L39]. Useful while bisecting a
                            seed; nothing in the harness sets it.
                            UNSET, WHICH IS THE DEFAULT: the frozen `-gt 63'
                            tolerance [common/masterLD.sh:L41] applies, the code
                            is logged and warned about, and seeding runs to the
                            end of the frozen sequence. The seed still never
                            reaches a diff unnoticed -- the post-seed gate in
                            `acas_main' exits with the worst code seen (D5).
                            The frozen dfltLD `!= 0' test
                            [common/masterLD.sh:L83] applies either way.
  ACAS_DB_WAIT_TIMEOUT=N    Seconds to wait for MariaDB (default 180).
  ACAS_DB_AUTH_GRACE=N      Seconds to tolerate "Access denied" before failing
                            fast, capped at ACAS_DB_WAIT_TIMEOUT (default 15).
  ACAS_DB_TLS_CA=PATH       PEM bundle the server certificate chains to.
                            REQUIRED for a NON-LOCAL ACAS_DB_HOST: the client is
                            then given --ssl-ca and --ssl-verify-server-cert, so
                            both the chain and the hostname are checked. A
                            loopback host or a unix socket needs none.
  ACAS_DB_ALLOW_PLAINTEXT=1 Declare a NON-LOCAL network isolated and permit
                            plaintext to it. Accepted spellings are exactly
                            1, true, yes, on -- anything else fails closed. Use
                            only for a private harness network; the seeding
                            credential is then unprotected.

Finite deadlines. Every external process this script spawns runs under one and
there is deliberately no way to disable them. Each is a whole number of seconds,
at least 1 and at most 86400; the child is sent TERM at the deadline and KILL
ACAS_TIMEOUT_GRACE seconds later, and only ever that one child:
  ACAS_TIMEOUT_LOADER=N     One compiled load program (default 600). A loader
                            that reaches a prompt would otherwise wait on a
                            terminal for ever; its stdin is also detached.
  ACAS_TIMEOUT_CLIENT=N     One MariaDB client invocation, the TCP probe, one
                            digest read (default 30).
  ACAS_TIMEOUT_GRACE=N      TERM-to-KILL grace period (default 15).

Exit codes:
  0        clean seed
  70       usage        71  precondition
  72       database     73  autocommit is not on
  74       a load program or client exceeded its deadline
  75       the scenario's declared seed files could not be staged
  anything else  a LOADER's own return code, propagated verbatim as the frozen
                 script does with `exit $rc' [common/masterLD.sh:L59,L68,L77,L86]:
                 128 params not set up, 64 RDB not set up, 16 rdb write error
                 [common/masterLD.sh:L37-L39].

This script emits no DDL, adds no validation of the flat files beyond the
existence test the frozen script performs, runs the loaders strictly one at a
time, writes nothing under $ACAS_REPO, and never sets autocommit.
USAGE
}



# Every loader this script is allowed to invoke, for validating --only. Built
# from the two in-scope tables so the list cannot drift away from them.
acas_inscope_loader_names() {
  local entry
  for entry in "${ACAS_SEED_SYSTEM_BLOCK[@]}"; do
    acas_split_system_entry "$entry"
    printf '%s\n' "$ACAS_S_LOADER"
  done
  for entry in "${ACAS_SEED_MAPPINGS[@]}"; do
    acas_split_entry "$entry"
    printf '%s\n' "$ACAS_E_LOADER"
  done
}

acas_out_of_scope_loader_names() {
  local entry
  for entry in "${ACAS_SEED_OUT_OF_SCOPE[@]}"; do
    acas_split_entry "$entry"
    printf '%s\n' "$ACAS_E_LOADER"
  done
}

# Validate one --only name. Deliberately NOT a value-returning helper.
acas_assert_only_name() {
  local name="$1"
  local -a allowed=() forbidden=()
  mapfile -t allowed < <(acas_inscope_loader_names)
  mapfile -t forbidden < <(acas_out_of_scope_loader_names)

  if acas_in_list "$name" "${allowed[@]}"; then
    return 0
  fi
  if acas_in_list "$name" "${forbidden[@]}"; then
    acas_die "$EX_USAGE" \
      "--only names '$name', which is one of the 8 OUT-OF-SCOPE loaders." \
      'It loads a table the posting cycle never touches, so this harness never' \
      'invokes it under any circumstances (deviation D7). The out-of-scope' \
      "loaders are: $(acas_join_words "${forbidden[@]}")."
  fi
  acas_die "$EX_USAGE" \
    "--only names '$name', which is not an ACAS load program this script knows." \
    "The 20 in-scope loaders are: $(acas_join_words "${allowed[@]}")."
}

acas_parse_args() {
  local only_raw='' only_given=0
  while (( $# > 0 )); do
    case "$1" in
      -h|--help)
        acas_usage
        exit "$EX_OK"
        ;;
      --data-dir)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--data-dir requires a path.'
        ACAS_SEED_DATA_DIR="$2"
        shift 2
        ;;
      --data-dir=*)
        ACAS_SEED_DATA_DIR="${1#*=}"
        shift
        ;;
      --only)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--only requires a comma-separated loader list.'
        only_raw="$2"
        only_given=1
        shift 2
        ;;
      --only=*)
        only_raw="${1#*=}"
        only_given=1
        shift
        ;;
      --dry-run)
        ACAS_SEED_DRY_RUN=1
        shift
        ;;
      --)
        shift
        break
        ;;
      -*)
        acas_die "$EX_USAGE" "unrecognised option '$1'." \
          'Run --help for the accepted options.'
        ;;
      *)
        if [[ -n "$ACAS_SEED_SCENARIO" ]]; then
          acas_die "$EX_USAGE" \
            "at most one scenario file may be given; got '$ACAS_SEED_SCENARIO' and '$1'."
        fi
        ACAS_SEED_SCENARIO="$1"
        shift
        ;;
    esac
  done

  # Anything after `--' is the scenario, at most one.
  while (( $# > 0 )); do
    if [[ -n "$ACAS_SEED_SCENARIO" ]]; then
      acas_die "$EX_USAGE" "unexpected trailing arguments: $(acas_join_words "$@")"
    fi
    ACAS_SEED_SCENARIO="$1"
    shift
  done

  # Note the test is on `only_given', NOT on `only_raw' being non-empty.
  if (( only_given )); then
    local name
    local -a only_allowed=()
    # Split a comma-separated list without disturbing the global IFS, which is
    # deliberately $'\n\t' (see the strict-mode block), so unquoted word
    # splitting on spaces is not available here.
    while IFS= read -r name || [[ -n "$name" ]]; do
      [[ -n "$name" ]] || continue
      acas_assert_only_name "$name"
      ACAS_SEED_ONLY+=("$name")
    done < <(printf '%s\n' "$only_raw" | tr ',' '\n')
    if (( ${#ACAS_SEED_ONLY[@]} == 0 )); then
      mapfile -t only_allowed < <(acas_inscope_loader_names)
      acas_die "$EX_USAGE" \
        '--only was given an empty list; name at least one load program.' \
        "The 20 in-scope loaders are: $(acas_join_words "${only_allowed[@]}")."
    fi
  fi
}

# Is this loader selected? With no --only every loader is selected.
acas_loader_selected() {
  if (( ${#ACAS_SEED_ONLY[@]} == 0 )); then
    return 0
  fi
  acas_in_list "$1" "${ACAS_SEED_ONLY[@]}"
}

# This script ASSERTS its environment; it never installs one and never creates
# a database object.

acas_assert_environment() {
  acas_stage 'Preconditions 1/8: environment contract'

  local name missing=0
  for name in "${ACAS_SEED_REQUIRED_ENV_NONEMPTY[@]}"; do
    if [[ -z "${!name-}" ]]; then
      printf 'FATAL: required environment variable %s is unset or empty.\n' "$name" >&2
      missing=1
    fi
  done
  for name in "${ACAS_SEED_REQUIRED_ENV_DECLARED[@]}"; do
    # `-v' tests declaration, not content.
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

  # THE RANGE, not merely the character class.
  if [[ ! "$ACAS_DB_PORT" =~ ^[0-9]+$ ]]; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_PORT must be numeric; got '$ACAS_DB_PORT'."
  fi
  if (( 10#$ACAS_DB_PORT < 1 || 10#$ACAS_DB_PORT > 65535 )); then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_PORT must be between 1 and 65535; got '$ACAS_DB_PORT'." \
      'A value outside the range reaches the TCP probe and the client as an' \
      'out-of-range port, which fails with a cause that names neither the' \
      'variable nor the value.'
  fi
  # Canonicalised so the port this script reports, probes and passes to the
  # client is one value rather than three spellings of it.
  ACAS_DB_PORT="$(( 10#$ACAS_DB_PORT ))"

  # only the FIRST CHARACTER -- so a value that merely BEGINS with a space
  # triggers the interactive block just as an empty one does.
  for name in ACAS_LEDGERS ACAS_BIN; do
    if [[ "${!name-}" == ' '* ]]; then
      acas_die "$EX_PRECONDITION" \
        "$name begins with a space, which the COBOL treats as blank." \
        'zz010-Get-Env-Set-Files tests only the first character' \
        '("if ACAS_LEDGERS (1:1) = spaces or ACAS_BIN (1:1) = spaces"), then' \
        'displays SY009 "Environment variables not yet set up : ABORTING",' \
        'SY008 "Note message & Hit return" and WAITS ON AN ACCEPT.' \
        'Every one of the 28 load programs copies that paragraph, so the seed' \
        'would hang with no diagnostic.' \
        '[copybooks/Proc-Get-Env-Set-Files.cob:L20-L28]' \
        '[common/glbatchLD.cbl:L188-L189]'
    fi
  done

  # The COBOL reads its connection details into fixed-width fields.
  local value
  for name in ACAS_DB_USER ACAS_DB_PASSWORD ACAS_DB_NAME; do
    value="${!name-}"
    if (( ${#value} > 12 )); then
      acas_die "$EX_PRECONDITION" \
        "$name is ${#value} characters long; the RDB-Data field is pic x(12)." \
        'A longer value is silently truncated into DB-UName / DB-UPass /' \
        'DB-Schema and the COBOL side then fails to authenticate.' \
        '[copybooks/wsfnctn.cob:L56-L62]'
    fi
  done

  # Decided HERE, before the readiness probe, and not lazily on first use --
  # see acas_assert_transport_policy for why the ordering matters.
  acas_assert_transport_policy

  acas_log "ACAS_REPO   = $ACAS_REPO (read-only checkout; the specification)"
  acas_log "ACAS_BUILD  = $ACAS_BUILD (the loaders built by harness/build_oracle.sh)"
  acas_log "ACAS_DATA   = $ACAS_DATA"
  acas_log "ACAS_OUT    = $ACAS_OUT"
  acas_log "ACAS_BIN    = $ACAS_BIN"
  acas_log "database    = ${ACAS_DB_USER}@${ACAS_DB_HOST}:${ACAS_DB_PORT}/${ACAS_DB_NAME}"
  acas_note 'the password is never printed, never logged and never passed in argv'
}

# Precondition 2 of 8 -- the data directory, and the frozen `cd' (D2).
acas_assert_data_dir() {
  acas_stage 'Preconditions 2/8: the ACAS data directory'

  [[ -n "$ACAS_SEED_DATA_DIR" ]] || ACAS_SEED_DATA_DIR="$ACAS_DATA"

  # An absolute path is REQUIRED, not merely tidy.
  [[ "$ACAS_SEED_DATA_DIR" == /* ]] || acas_die "$EX_PRECONDITION" \
    "the data directory must be an absolute path; got '$ACAS_SEED_DATA_DIR'." \
    'The loaders prefix every file name with ACAS_LEDGERS and the OS delimiter,' \
    'so a relative path is resolved against the working directory twice.' \
    '[copybooks/Proc-Get-Env-Set-Files.cob:L125-L136]'

  # A path containing a space is silently TRUNCATED at the first space, because
  # the STRING statement takes ACAS_LEDGERS `delimited by space'.
  case "$ACAS_SEED_DATA_DIR" in
    *' '*)
      acas_die "$EX_PRECONDITION" \
        "the data directory path contains a space: '$ACAS_SEED_DATA_DIR'." \
        'zz020-Set-the-Paths concatenates ACAS_LEDGERS "delimited by space", so' \
        'the path is truncated at the first space and every file name is wrong.' \
        '[copybooks/Proc-Get-Env-Set-Files.cob:L131,L142]'
      ;;
  esac

  [[ -d "$ACAS_SEED_DATA_DIR" ]] || acas_die "$EX_PRECONDITION" \
    "the data directory ($ACAS_SEED_DATA_DIR) is not a directory." \
    'It must hold the ACAS Cobol flat files the load programs read.' \
    '[common/masterLD.sh:L27-L28]'

  # Writable because the loaders append their own diagnostics to
  # SYS-DISPLAY.log [copybooks/Test-Data-Flags.cob:L10] hardcodes `SW-Testing
  # pic 9 value 1' and cannot be switched off, so the log grows on every DAL.
  [[ -w "$ACAS_SEED_DATA_DIR" ]] || acas_die "$EX_PRECONDITION" \
    "the data directory ($ACAS_SEED_DATA_DIR) is not writable." \
    'The load programs write SYS-DISPLAY.log there, and the frozen file-handler' \
    'logger cannot be disabled [copybooks/Test-Data-Flags.cob:L10].'

  # THE FROZEN-ARTIFACT GUARANTEE. The data directory must not be inside the
  # checkout.
  acas_assert_outside_repo 'the data directory' "$ACAS_SEED_DATA_DIR"

  local data_real
  data_real="$(readlink -f "$ACAS_SEED_DATA_DIR" 2>/dev/null || printf '%s' "$ACAS_SEED_DATA_DIR")"

  local ledgers_real
  ledgers_real="$(readlink -f "${ACAS_LEDGERS}" 2>/dev/null || printf '%s' "${ACAS_LEDGERS}")"
  if [[ "$ledgers_real" != "$data_real" ]]; then
    acas_warn "ACAS_LEDGERS ($ACAS_LEDGERS) differs from the data directory ($ACAS_SEED_DATA_DIR); exporting the data directory instead, so the loaders read the files this script checked."
  fi
  export ACAS_LEDGERS="$ACAS_SEED_DATA_DIR"

  # Reproduce [common/masterLD.sh:L45] `cd ~/ACAS' with the harness data
  # directory (D2).
  cd "$ACAS_SEED_DATA_DIR" || acas_die "$EX_PRECONDITION" \
    "could not change directory to $ACAS_SEED_DATA_DIR."
  acas_log "working directory = $PWD  (reproduces [common/masterLD.sh:L45])"
  acas_log "ACAS_LEDGERS      = $ACAS_LEDGERS  (the path the loaders prefix onto every file name)"
}


acas_open_log() {
  local dir="$ACAS_OUT/seed"
  # Canonical containment BEFORE mkdir: the guard must decide where a directory
  # would be created, not discover afterwards that it was created in the
  # checkout.
  acas_assert_outside_repo 'ACAS_OUT' "$ACAS_OUT"
  acas_assert_outside_repo 'the seed log directory' "$dir"
  mkdir -p "$dir" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "could not create the seed log directory $dir." \
    'ACAS_OUT must be a writable volume.'
  chmod 700 -- "$dir" 2>/dev/null || true

  acas_assert_outside_repo 'the seed log directory' "$dir"

  # THE GLOBAL IS ASSIGNED LAST, and that ordering is the whole point.
  local candidate="$dir/seed.log"
  acas_create_private_file "$candidate" 'the seed log'
  ACAS_SEED_LOG="$candidate"
  {
    printf 'harness/seed.sh run log\n'
    printf 'started (UTC): %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'this file lives under the ACAS_OUT seed directory and is never compared\n'
    printf -- '----------------------------------------------------------------\n'
  } >>"$ACAS_SEED_LOG"
}

# Precondition 4 of 8 -- system.dat. Its own stage, because its absence is the
# single most consequential and least obvious failure in the whole harness.
acas_assert_system_dat() {
  acas_stage "Preconditions 4/8: $ACAS_SEED_SYSTEM_FLAT_FILE"

  if [[ -e "$ACAS_SEED_SYSTEM_FLAT_FILE" ]]; then
    acas_log "found $ACAS_SEED_SYSTEM_FLAT_FILE in $PWD"
    acas_note 'the scenario owns its content; two settings in SYSTEM-REC are diff-visible'
    acas_note 'and must be pinned by the scenario, not by this script: Run-Date'
    acas_note '[copybooks/wssystem.cob:L67] and the three-state IRS fan-out switch'
    acas_note '[copybooks/wssystem.cob:L179-L181] (space = GL only, "Y" = IRS instead,'
    acas_note '"B" = IRS as well as). Leaving the switch at a default would make the'
    acas_note 'affected-table list of a scenario ambiguous.'
    # A zero accounting cycle is the second interactive trap. Enforced by the
    # scenario definitions, not here, because this script does not parse the
    # flat files.
    acas_note 'the scenario must also seed a NON-ZERO accounting cycle:'
    acas_note '[general/general.cbl:L462-L463] diverts a zero cycle to an interactive path.'
    return 0
  fi

  acas_die "$EX_PRECONDITION" \
    "$ACAS_SEED_SYSTEM_FLAT_FILE is not present in $PWD." \
    'This is fatal for two independent reasons, and the second one hangs the' \
    'harness with no diagnostic at all.' \
    '' \
    '  1. Every load program opens the system file FIRST to read the RDBMS' \
    '     connection parameters, and returns 128 -- "params are not set up" --' \
    '     when it cannot. So without it NOTHING can be seeded.' \
    '     [common/glbatchLD.cbl:L215-L224] [common/glbatchLD.cbl:L233]' \
    '     [common/masterLD.sh:L37]' \
    '' \
    '  2. It is also the COBOL indexed file the menus force open before' \
    '     anything else: [general/general.cbl:L385-L396] does' \
    '     move "00" to FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.  and, if' \
    '     that open fails, CALLs sys002 -- which is INTERACTIVE. A subsequent' \
    '     harness/run_cobol_scenario.sh would then block for ever on a terminal' \
    '     read instead of failing, and the run would look hung rather than' \
    '     broken.' \
    '' \
    "Seed $ACAS_SEED_SYSTEM_FLAT_FILE into $PWD from the scenario definition" \
    'before invoking this script.'
}

# Precondition 5 of 8 -- the compiled loaders.
acas_assert_loaders() {
  acas_stage 'Preconditions 5/8: the compiled load programs'

  local loader_dir="$ACAS_BUILD/common"
  [[ -d "$loader_dir" ]] || acas_die "$EX_PRECONDITION" \
    "$loader_dir does not exist, so the compiled load programs cannot be found." \
    'Run harness/build_oracle.sh first: it copies the checkout into ACAS_BUILD' \
    'and compiles the loaders there.'
  export PATH="$loader_dir:$PATH"
  acas_log "load programs   = $loader_dir (prepended to PATH)"

  # COB_LIBRARY_PATH must resolve the bridge modules each loader CALLs -- a
  # loader is an executable, but glbatchMT and friends are dynamically loadable
  # modules.
  if [[ -z "${COB_LIBRARY_PATH-}" ]]; then
    export COB_LIBRARY_PATH="$loader_dir"
    acas_note "COB_LIBRARY_PATH was unset; set to $loader_dir so the *MT bridge modules resolve"
  elif [[ ":${COB_LIBRARY_PATH}:" != *":${loader_dir}:"* ]]; then
    export COB_LIBRARY_PATH="$loader_dir:$COB_LIBRARY_PATH"
    acas_note "prepended $loader_dir to COB_LIBRARY_PATH so the *MT bridge modules resolve"
  fi
  acas_log "COB_LIBRARY_PATH = $COB_LIBRARY_PATH"

  local -a wanted=() missing=()
  mapfile -t wanted < <(acas_inscope_loader_names)
  local name resolved
  for name in "${wanted[@]}"; do
    resolved="$(command -v "$name" 2>/dev/null || true)"
    if [[ -z "$resolved" || ! -x "$resolved" || ! -s "$resolved" ]]; then
      missing+=("$name")
    fi
  done
  if (( ${#missing[@]} )); then
    acas_die "$EX_PRECONDITION" \
      "${#missing[@]} of ${#wanted[@]} in-scope load programs are missing or not executable." \
      "Missing: $(acas_join_words "${missing[@]}")" \
      'Every one of them should have been built by harness/build_oracle.sh from' \
      'common/<name>.cbl via [common/comp-common.sh:L51], and build_oracle.sh' \
      'asserts exactly these 20 by name as "required by harness/seed.sh".' \
      'A missing loader therefore means the oracle build did not complete: run' \
      'harness/build_oracle.sh and check the build logs under ACAS_OUT.'
  fi
  acas_log "verified: all ${#wanted[@]} in-scope load programs are present and executable"

  # The 8 out-of-scope loaders are NOT asserted -- they may legitimately be
  # absent, and their presence changes nothing, because this script never
  # invokes them (D7).
  local -a forbidden=()
  mapfile -t forbidden < <(acas_out_of_scope_loader_names)
  acas_note "never invoked, whatever their flat files: $(acas_join_words "${forbidden[@]}")"
}

# Precondition 6 of 8 -- the runtime library paths.
acas_assert_library_paths() {
  acas_stage 'Preconditions 6/8: runtime library paths'

  # The loaders link libcob and libmysqlclient, and the repository declares its
  # own loader path order in [etc/ld.so.conf.d/gnucobol.conf].
  local dir added=0
  for dir in "${ACAS_SEED_LOADER_PATHS[@]}"; do
    [[ -d "$dir" ]] || continue
    if [[ -z "${LD_LIBRARY_PATH-}" ]]; then
      export LD_LIBRARY_PATH="$dir"
      added=1
    elif [[ ":${LD_LIBRARY_PATH}:" != *":${dir}:"* ]]; then
      export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${dir}"
      added=1
    fi
  done
  if (( added )); then
    acas_note 'LD_LIBRARY_PATH completed from [etc/ld.so.conf.d/gnucobol.conf], in that order'
  fi
  acas_log "LD_LIBRARY_PATH = ${LD_LIBRARY_PATH-<unset>}"

  # Not fatal on its own -- the library may be resolved through the ldconfig
  # cache instead -- but worth naming, because an unresolved libmysqlclient
  # presents as a loader that dies before it can return one of the documented.
  if [[ ! -e /usr/local/mysql/lib/libmysqlclient.so ]]; then
    acas_warn 'libmysqlclient.so was not found under /usr/local/mysql/lib, the prefix every frozen compile line hard-codes [common/comp-common.sh:L26]; a loader that cannot resolve it will fail before it can return 128, 64 or 16.'
  fi
}


# TRANSPORT SECURITY (CWE-295 certificate validation, CWE-319 cleartext).
# The transport is decided ONCE, before anything connects, and never downgraded
# silently. A local target may use plaintext; a non-local target needs either a
# CA bundle in ACAS_DB_TLS_CA, whose certificate and hostname are then verified,
# or an explicit ACAS_DB_ALLOW_PLAINTEXT declaration -- otherwise the run aborts
# with a named cause, because the probe authenticates with a real credential.

# True when the target is reachable without leaving the machine: a unix socket,
# an empty host, a loopback name, or a numeric loopback address.
acas_target_is_local() {
  [[ -n "${ACAS_DB_SOCKET-}" ]] && return 0
  [[ -z "$ACAS_DB_HOST" ]] && return 0
  local host="${ACAS_DB_HOST#[}"
  host="${host%]}"
  case "$host" in
    localhost|localhost.localdomain|::1) return 0 ;;
    127.*) return 0 ;;
  esac
  return 1
}

acas_plaintext_declared() {
  case "${ACAS_DB_ALLOW_PLAINTEXT-}" in
    1|true|yes|on) return 0 ;;
  esac
  return 1
}

# Decide, ONCE and BEFORE ANYTHING CONNECTS, which client transports this
# target has earned. Populates ACAS_SEED_TLS_VARIANTS, most secure first, or
# aborts.
acas_assert_transport_policy() {
  local ca="${ACAS_DB_TLS_CA-}"
  ACAS_SEED_TLS_VARIANTS=()

  if [[ -n "$ca" ]]; then
    [[ -r "$ca" ]] || acas_die "$EX_PRECONDITION" \
      "ACAS_DB_TLS_CA names a file that cannot be read: $ca" \
      'It must be the PEM bundle the server certificate chains to.'
    ACAS_SEED_TLS_VARIANTS+=("--ssl-ca=$ca --ssl-verify-server-cert")
  fi

  if acas_target_is_local; then
    ACAS_SEED_TLS_VARIANTS+=('--skip-ssl')
    acas_note 'transport: local target, so plaintext is permitted'
    return 0
  fi

  if acas_plaintext_declared; then
    acas_warn 'ACAS_DB_ALLOW_PLAINTEXT permits plaintext to a NON-LOCAL server; the seeding credential and every answer are unprotected'
    ACAS_SEED_TLS_VARIANTS+=('--skip-ssl')
    return 0
  fi

  if [[ -z "$ca" ]]; then
    acas_die "$EX_PRECONDITION" \
      "the target ${ACAS_DB_HOST}:${ACAS_DB_PORT} is not local and no verified TLS is configured." \
      'This script authenticates with the credential the 28 load programs use' \
      'and reads the server autocommit setting, so the connection must be' \
      'protected. Either set ACAS_DB_TLS_CA to the PEM bundle the server' \
      'certificate chains to, or -- if this really is an isolated harness network' \
      'such as the private Compose network [harness/docker-compose.yml] --' \
      'declare it with ACAS_DB_ALLOW_PLAINTEXT=1.' \
      'It is NOT downgraded silently: that was the defect.'
  fi

  acas_note 'transport: verified TLS required (CA supplied, certificate and hostname checked)'
  return 0
}

# A single scalar query, credential-safe.
acas_sql_scalar() {
  local sql="$1"
  ACAS_SQL_OUT=''
  ACAS_SQL_DIAG=''

  local client variant flag out rc started elapsed

  # Every client invocation carries ACAS_TIMEOUT_CLIENT.
  local -a deadline=()
  acas_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  deadline=("${ACAS_DEADLINE_ARGV[@]}")

  # Unreachable unless acas_assert_transport_policy was skipped or changed: it
  # either records at least one permitted variant or aborts with a named cause.
  if (( ${#ACAS_SEED_TLS_VARIANTS[@]} == 0 )); then
    acas_die "$EX_PRECONDITION" \
      'no permitted client transport for this target.' \
      'acas_assert_transport_policy must run before any query; see the' \
      'TRANSPORT SECURITY section.'
  fi
  for client in mariadb mysql; do
    acas_have "$client" || continue
    for variant in "${ACAS_SEED_TLS_VARIANTS[@]}"; do
      local -a argv=("${deadline[@]}" "$client" '--protocol=TCP')
      if [[ -n "$variant" ]]; then
        # A variant may carry two words (--ssl-ca=...
        # --ssl-verify-server-cert), so it is split deliberately here -- each
        # flag must be its own argv element.
        for flag in $variant; do
          argv+=("$flag")
        done
      fi
      argv+=(
        "--host=$ACAS_DB_HOST" "--port=$ACAS_DB_PORT"
        "--user=$ACAS_DB_USER" '--batch' '--skip-column-names'
        "--database=$ACAS_DB_NAME" "--execute=$sql"
      )
      rc=0
      started="$SECONDS"
      out="$(MYSQL_PWD="$ACAS_DB_PASSWORD" "${argv[@]}" 2>/dev/null)" || rc=$?
      elapsed=$(( SECONDS - started ))
      if (( rc == 0 )); then
        ACAS_SQL_OUT="$out"
        return 0
      fi
      ACAS_SQL_DIAG="$(MYSQL_PWD="$ACAS_DB_PASSWORD" "${argv[@]}" 2>&1 || true)"
      if acas_is_timeout_status "$rc" "$elapsed" "$ACAS_TIMEOUT_CLIENT"; then
        ACAS_SQL_DIAG="$client did not answer within ${ACAS_TIMEOUT_CLIENT}s and was terminated (raise ACAS_TIMEOUT_CLIENT). $ACAS_SQL_DIAG"
      fi
    done
    if [[ "$ACAS_SQL_DIAG" == *'Access denied'* ]]; then
      return 2
    fi
    return 1
  done
  return 3
}

acas_db_tcp_probe() {
  # The port range is asserted in acas_assert_environment, before anything
  # connects, so `int(sys.argv[2])' here can no longer receive 99999 and fail
  # with an OverflowError that names neither the variable nor the value.
  acas_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  "${ACAS_DEADLINE_ARGV[@]}" python3 - "$ACAS_DB_HOST" "$ACAS_DB_PORT" <<'PY'
import socket
import sys

host = sys.argv[1]
try:
    port = int(sys.argv[2])
except ValueError:
    print(f"port is not an integer: {sys.argv[2]!r}", file=sys.stderr)
    sys.exit(2)
if not 1 <= port <= 65535:
    print(f"port out of range 1..65535: {port}", file=sys.stderr)
    sys.exit(2)
try:
    with socket.create_connection((host, port), timeout=5):
        pass
except OSError:
    sys.exit(1)
sys.exit(0)
PY
}

# Precondition 7 of 8 -- MariaDB readiness.
acas_wait_for_database() {
  acas_stage 'Preconditions 7/8: MariaDB readiness'

  local timeout="${ACAS_DB_WAIT_TIMEOUT:-180}"
  [[ "$timeout" =~ ^[0-9]+$ ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_DB_WAIT_TIMEOUT must be numeric; got '$timeout'."
  local auth_grace="${ACAS_DB_AUTH_GRACE:-15}"
  [[ "$auth_grace" =~ ^[0-9]+$ ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_DB_AUTH_GRACE must be numeric; got '$auth_grace'."
  (( auth_grace > timeout )) && auth_grace="$timeout"

  local interval=3 elapsed=0
  acas_log "waiting up to ${timeout}s for ${ACAS_DB_HOST}:${ACAS_DB_PORT}"
  while ! acas_db_tcp_probe; do
    if (( elapsed >= timeout )); then
      acas_die "$EX_DATABASE" \
        "MariaDB at ${ACAS_DB_HOST}:${ACAS_DB_PORT} did not accept a TCP connection within ${timeout}s." \
        'The load programs connect through the bridge C interface, so nothing can' \
        'be seeded without it. Start the service' \
        '(docker compose -f harness/docker-compose.yml up -d mariadb), wait for' \
        'its healthcheck, or raise ACAS_DB_WAIT_TIMEOUT.'
    fi
    sleep "$interval"
    elapsed=$(( elapsed + interval ))
  done
  acas_log "TCP reachable after ${elapsed}s"

  # An open port is not readiness.
  local rc=0 denied_for=0
  elapsed=0
  while true; do
    rc=0
    acas_sql_scalar 'select 1' || rc=$?
    case "$rc" in
      0)
        acas_log "authenticated as ${ACAS_DB_USER} against ${ACAS_DB_NAME}"
        return 0
        ;;
      3)
        acas_die "$EX_DATABASE" \
          'no mariadb or mysql client binary is available, so the autocommit setting cannot be verified.' \
          'That verification is not optional: the 28 load programs declare' \
          'commit and rollback paragraphs but never reach them (every' \
          '"perform aa020-Rollback" is commented out and "aa030-Commit" has no' \
          'perform site at all), so seeding with autocommit OFF would leave an' \
          'EMPTY database and every downstream diff would be untrustworthy.' \
          'harness/Dockerfile.gnucobol installs mariadb-client for exactly this;' \
          'run inside the gnucobol service image.'
        ;;
      2)
        if (( denied_for >= auth_grace )); then
          acas_die "$EX_DATABASE" \
            "MariaDB at ${ACAS_DB_HOST}:${ACAS_DB_PORT} REJECTED the credentials for user '${ACAS_DB_USER}'." \
            'The server is alive, so this is a credential or grant problem, not a' \
            'readiness problem, and waiting longer will not fix it.' \
            'Both services in harness/docker-compose.yml interpolate the same two' \
            'variables for the application account, so a mismatch usually means' \
            'the database volume was created with a different password: recreate' \
            'it with "docker compose ... down -v", or correct ACAS_DB_USER and' \
            'ACAS_DB_PASSWORD.' \
            "$(acas_diag_summary "$ACAS_SQL_DIAG")"
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
            "$(acas_diag_summary "$ACAS_SQL_DIAG")"
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

# Precondition 8 of 8 -- autocommit MUST be OFF, as the Agent Action Plan
# mandates for the seeding window.
#
# ASSERTED, NEVER SET. The setting belongs to the server and is configured once,
# by harness/Dockerfile.mariadb, which writes `autocommit=0' into
# /etc/mysql/conf.d/99-acas-oracle.cnf. harness/docker-compose.yml deliberately
# does not repeat it -- one authority only -- and records that this script
# asserts it. Issuing `SET autocommit' here would create a second authority and
# make the seeded state depend on which script ran last. It is also impossible
# for the loaders themselves to do: the vendored cobmysqlapi38.c exposes
# MySQL_commit and MySQL_rollback but NOT MySQL_autocommit, so no COBOL program
# in the checkout can change the mode.
#
# WHY OFF -- THE AAP REQUIRES IT
# ------------------------------
# Three provisions mandate it, all deriving from the same banner: section 0.2.1.1
# ("the batch loader turns autocommit off"), section 0.4.1.7 (on
# harness/Dockerfile.mariadb: "autocommit off to match the loaders") and section
# 0.5.2 ("autocommit must be **off** during seeding, because the batch loader
# sets it off explicitly, and the seeded state depends on its commit
# boundaries").
#
# [common/glbatchLD.cbl:L9-L13] verbatim:
#     *>  This modules uses commit and rollback so *
#     *>  you MUST ensure that autocommit is OFF   *
#     *>   in the rdb settings. It is as default   *
#     *>   set ON.                                 *
#
# Verified across the frozen tree: that banner is in EVERY ONE of the 28
# common/*LD.cbl programs, not just the batch loader -- e.g.
# [common/analLD.cbl:L11], [common/finalLD.cbl:L10], [common/dfltLD.cbl:L10],
# [common/systemLD.cbl:L9], [common/sys4LD.cbl:L10].
#
# But the shipped loaders never carry that intention out. Each declares a
# `aa020-Rollback' paragraph calling "MySQL_rollback" and a `aa030-Commit'
# paragraph calling "MySQL_commit", and BOTH are unreachable in the frozen
# source: every `perform aa020-Rollback' is commented out with `*>' --
# [common/glbatchLD.cbl:L386], [common/glbatchLD.cbl:L428],
# [common/nominalLD.cbl:L386], [common/nominalLD.cbl:L428],
# [common/nominalLD.cbl:L473], [common/slpostingLD.cbl:L363],
# [common/slpostingLD.cbl:L405], [common/slpostingLD.cbl:L450] -- and
# `aa030-Commit' has ZERO perform sites of any kind in any of the 28 loaders.
# The census that proves it returns no matches:
#     grep -n '^ *perform.*\(aa020\|aa030\|Commit\|Rollback\)' common/*LD.cbl
#
# The maintainer's own inline notes, sitting directly above those dead
# paragraphs, describe the same conclusion: [common/analLD.cbl:L377] "otherwise
# as normally it is set to autocommit !!!!!", [common/glbatchLD.cbl:L453] and
# [common/analLD.cbl:L442] "These do not work during testing with mariadb - Non
# transactional model or autocommit set ON", and [common/finalLD.cbl:L361]
# "which can be ignored unless you thought autocommit was set up."
#
# CONSEQUENCE, PRESERVED NOT REPAIRED (R-4): with autocommit OFF, MariaDB opens
# an implicit transaction on a loader's first INSERT and discards it when the
# loader disconnects, because no reachable COMMIT exists. The seed is therefore
# NOT durable under the mandated mode -- a defect of the frozen code, which R-4
# makes the specification rather than a bug to fix: "A defect reproduced is
# correct; a defect fixed is a failure."
#
# This script consequently WARNS about that consequence and proceeds. It does not
# issue the COMMIT the loaders omit, does not enable transactional seeding the
# frozen code cannot drive, and does not override the AAP by demanding a more
# convenient mode. The warning exists so that an empty table set after a
# successful-looking seed is recognised as the reproduced defect rather than
# mistaken for a harness fault.
#
# The `+ 0' coercion is required, not cosmetic: autocommit is a boolean system
# variable and renders as ON/OFF in a string context, not as 1/0.
acas_assert_autocommit() {
  acas_stage 'Preconditions 8/8: autocommit must be OFF (AAP-mandated)'

  local rc=0
  acas_sql_scalar 'select concat_ws(0x2f, @@GLOBAL.autocommit + 0, @@SESSION.autocommit + 0)' || rc=$?
  if (( rc != 0 )); then
    acas_die "$EX_DATABASE" \
      'could not read the autocommit setting from the server.' \
      "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  fi

  # Take the last line that looks like the answer, so a stray client advisory
  # can never be mistaken for the value.
  local value=''
  local line
  while IFS= read -r line; do
    if [[ "$line" =~ ^[0-9]+/[0-9]+$ ]]; then
      value="$line"
    fi
  done <<<"$ACAS_SQL_OUT"

  [[ -n "$value" ]] || acas_die "$EX_DATABASE" \
    'the server did not return a readable autocommit setting.' \
    "Received: ${ACAS_SQL_OUT:-<empty>}"

  local global="${value%%/*}" session="${value##*/}"
  acas_log "@@GLOBAL.autocommit = $global   @@SESSION.autocommit = $session"

  if (( global != 0 || session != 0 )); then
    acas_die "$EX_AUTOCOMMIT" \
      "autocommit is ON (global=$global, session=$session); seeding is REFUSED." \
      'The Agent Action Plan mandates autocommit OFF for the seeding window in' \
      'three places -- section 0.2.1.1 (the seeding contract), section 0.4.1.7' \
      '(harness/Dockerfile.mariadb: "autocommit off to match the loaders") and' \
      'section 0.5.2 -- all deriving it from the banner carried by all 28' \
      'common/*LD.cbl loaders at [common/glbatchLD.cbl:L9-L13]: "you MUST ensure' \
      'that autocommit is OFF in the rdb settings".' \
      'Seeding under ON would produce durable rows the mandated mode does not,' \
      'so the seeded state would depend on the server rather than on the frozen' \
      'contract, and the oracle would no longer be the thing the AAP specifies.' \
      'This script deliberately does NOT set the mode: it has exactly one' \
      'authority, harness/Dockerfile.mariadb, which writes autocommit=0 into' \
      '/etc/mysql/conf.d/99-acas-oracle.cnf. Start the harness MariaDB service' \
      'built from that Dockerfile, or set autocommit=0 in the server' \
      'configuration and restart it.'
  fi
  acas_log 'verified: autocommit is OFF, globally and for this session (AAP-mandated)'

  # The reproduced defect, restated at the moment it becomes relevant. This is a
  # WARNING and not a refusal: R-4 requires the frozen behaviour, and refusing
  # here would be refusing the specification.
  acas_warn 'the frozen loaders reach no COMMIT, so under this AAP-mandated mode their writes are NOT durable: the tables may read EMPTY after a seed that reports success. Measured across the frozen tree -- every "perform aa020-Rollback" in all 28 common/*LD.cbl loaders is commented out (78 sites, none live) and "perform aa030-Commit" occurs exactly once anywhere, at [common/irsdfltLD.cbl:L437], commented out as well; [common/systemLD.cbl] declares both paragraphs at L406 and L420 with no perform site at all. This is the reproduced legacy defect (R-4), not a fault in this script -- the maintainer recorded the same observation at [common/analLD.cbl:L442] ("These do not work during testing with mariadb - Non transactional model or autocommit set ON"). Nothing here issues the missing COMMIT, because a defect fixed is a failure.'
}


# THE DOCUMENTED RETURN CODES -- [common/masterLD.sh:L37-L39] verbatim.
ACAS_SEED_LAST_RC=0
ACAS_SEED_WORST_RC=0

acas_rc_meaning() {
  case "$1" in
    0)
      printf 'success'
      ;;
    16)
      printf 'error writing data to the RDB [common/masterLD.sh:L39] [common/glbatchLD.cbl:L445]'
      ;;
    64)
      printf 'RDB not set up -- RDBMS-DB-Name is spaces, or the system record says Cobol files only [common/masterLD.sh:L38] [common/glbatchLD.cbl:L290]'
      ;;
    128)
      printf 'params not set up -- the loader could not open or read the system file [common/masterLD.sh:L37] [common/glbatchLD.cbl:L223,L233]'
      ;;
    *)
      printf 'UNDOCUMENTED load-program return code -- not one of 16, 64 or 128 [common/masterLD.sh:L37-L39]'
      ;;
  esac
}

# acas_invoke_loader <loader> Runs one load program, sequentially, in the
# foreground (R-3): no `&', no `xargs -P', no job control anywhere in this
# script.
acas_invoke_loader() {
  local loader="$1"
  ACAS_SEED_CURRENT_LOADER="$loader"
  ACAS_SEED_LAST_RC=0

  # UNDER A DEADLINE, and stdin detached.
  local started elapsed
  acas_deadline_prefix "$ACAS_TIMEOUT_LOADER"
  started="$SECONDS"
  if "${ACAS_DEADLINE_ARGV[@]}" "$loader" </dev/null 2>&1 | tee -a "$ACAS_SEED_LOG"; then
    ACAS_SEED_LAST_RC=0
  else
    ACAS_SEED_LAST_RC=${PIPESTATUS[0]}
  fi
  elapsed=$(( SECONDS - started ))

  # A timeout is fatal, unlike an ordinary non-zero return code.
  acas_assert_not_timed_out "$ACAS_SEED_LAST_RC" "$elapsed" "$ACAS_TIMEOUT_LOADER" \
    ACAS_TIMEOUT_LOADER "the load program $loader"

  ACAS_SEED_CURRENT_LOADER=''
  ACAS_SEED_RAN=$(( ACAS_SEED_RAN + 1 ))
  if (( ACAS_SEED_LAST_RC > ACAS_SEED_WORST_RC )); then
    ACAS_SEED_WORST_RC="$ACAS_SEED_LAST_RC"
  fi
  return 0
}

# acas_abort_on_rc <rc> <loader> <flat file> <test kind> <locator> <scope>
# Applies the FROZEN test, and by default nothing else.
acas_abort_on_rc() {
  local rc="$1" loader="$2" flat="$3" kind="$4" locator="$5" scope="$6"
  local meaning
  meaning="$(acas_rc_meaning "$rc")"

  if (( rc == 0 )); then
    acas_log "$loader -> return code 0"
    acas_summary_row "$loader" "$flat" 'yes' "$rc" 'ran'
    return 0
  fi

  # Does the FROZEN test abort on this code?
  local frozen_aborts=0
  case "$kind" in
    gt63)
      if (( rc > 63 )); then
        frozen_aborts=1
      fi
      ;;
    ne0)
      frozen_aborts=1
      ;;
    *)
      acas_die "$EX_PRECONDITION" \
        "internal error: unknown return-code test kind '$kind' for $loader."
      ;;
  esac

  if (( frozen_aborts )); then
    acas_summary_row "$loader" "$flat" 'yes' "$rc" 'ABORTED'
    if [[ "$scope" == 'system' ]]; then
      printf '%s\n' "$ACAS_SEED_SYSTEM_ABORT_MSG"
      acas_tee "$ACAS_SEED_SYSTEM_ABORT_MSG"
      printf 'FATAL: %s returned %s: %s\n' "$loader" "$rc" "$meaning" >&2
      acas_tee "FATAL: $loader returned $rc: $meaning"
      local test_text="$ACAS_SEED_TEST_TEXT_GT63"
      if [[ "$kind" == 'ne0' ]]; then
        test_text="$ACAS_SEED_TEST_TEXT_NE0"
      fi
      printf '       frozen test: %s at [common/masterLD.sh:%s]\n' \
        "$test_text" "$locator" >&2
      acas_seed_report
      exit "$rc"
    fi
    printf 'FATAL: %s returned %s: %s\n' "$loader" "$rc" "$meaning" >&2
    acas_tee "FATAL: $loader returned $rc: $meaning"
    printf '       Seeding is abandoned. The frozen script never tested this line\n' >&2
    printf '       [common/masterLD.sh:%s]; its author records the omission at\n' "$locator" >&2
    printf '       [common/masterLD.sh:L41-L42] -- "MUST GET round to trapping these\n' >&2
    printf '       param errors (>63) / but it is a lot of typing :)" -- so this\n' >&2
    printf '       harness does the trapping instead (deviation D4).\n' >&2
    printf '       Run harness/reset_db.sh before drawing any conclusion from a diff.\n' >&2
    acas_seed_report
    exit "$rc"
  fi

  # The frozen test TOLERATES this code, and so does this script by default:
  # the seed contract is reproduced, not tightened (R-3, R-6).
  if [[ "${ACAS_SEED_STRICT:-0}" != '1' ]]; then
    acas_summary_row "$loader" "$flat" 'yes' "$rc" 'ran (tolerated)'
    acas_warn "$loader returned $rc: $meaning. The frozen >63-only tolerance applies [common/masterLD.sh:L41], so seeding continues -- the seeded state may be PARTIAL and any state diff taken from it is untrustworthy. harness/seed.sh exits $rc at the end rather than aborting here (deviation D5)."
    return 0
  fi

  # ACAS_SEED_STRICT=1 -- an explicit OPT-IN to failing fast on a code the
  # frozen test tolerates. Nothing in the harness sets it.
  acas_summary_row "$loader" "$flat" 'yes' "$rc" 'ABORTED (opt-in strict)'
  printf 'FATAL: %s returned %s: %s\n' "$loader" "$rc" "$meaning" >&2
  acas_tee "FATAL: $loader returned $rc: $meaning"
  printf '       The frozen threshold TOLERATES this code, because it is not greater\n' >&2
  printf '       than 63 [common/masterLD.sh:L41], and so does this script by default.\n' >&2
  printf '       You exported ACAS_SEED_STRICT=1, which opts in to aborting here\n' >&2
  printf '       instead of at the end of the frozen sequence (deviation D5).\n' >&2
  printf '       Unset ACAS_SEED_STRICT to reproduce the frozen contract; the post-seed\n' >&2
  printf '       gate in acas_main still exits with this code, so nothing hands a\n' >&2
  printf '       partial seed to a diff either way.\n' >&2
  printf '       Run harness/reset_db.sh before re-seeding.\n' >&2
  acas_seed_report
  exit "$rc"
}

acas_seed_system_block() {
  acas_stage 'Stage 1/2: the system file  [common/masterLD.sh:L50-L88]'

  ACAS_SEED_JOBSTATUS=0

  # if [ -e system.dat ]; then [common/masterLD.sh:L51] Existence, and nothing
  # else.
  if [[ ! -e "$ACAS_SEED_SYSTEM_FLAT_FILE" ]]; then
    # Unreachable in practice, because acas_assert_system_dat already refused
    # to continue.
    acas_warn "$ACAS_SEED_SYSTEM_FLAT_FILE is absent; the whole system-file block is skipped, as [common/masterLD.sh:L51] would skip it."
    local entry
    for entry in "${ACAS_SEED_SYSTEM_BLOCK[@]}"; do
      acas_split_system_entry "$entry"
      acas_summary_row "$ACAS_S_LOADER" "$ACAS_SEED_SYSTEM_FLAT_FILE" 'no' '-' 'skipped-absent'
    done
    return 0
  fi

  local entry
  for entry in "${ACAS_SEED_SYSTEM_BLOCK[@]}"; do
    acas_split_system_entry "$entry"

    if ! acas_loader_selected "$ACAS_S_LOADER"; then
      acas_log "$ACAS_S_LOADER -> not selected by --only; skipped"
      acas_summary_row "$ACAS_S_LOADER" "$ACAS_SEED_SYSTEM_FLAT_FILE" 'yes' '-' 'skipped-only'
      continue
    fi

    acas_log "$ACAS_S_LOADER  <- $ACAS_SEED_SYSTEM_FLAT_FILE  -> $ACAS_S_TABLE  [common/masterLD.sh:$ACAS_S_LOCATOR]"
    acas_invoke_loader "$ACAS_S_LOADER"

    # rc=$? ; JOBSTATUS=$rc -- assigned after EVERY loader, including a
    # successful one, exactly as the frozen script does at
    # [common/masterLD.sh:L54-L55,L63-L64,L72-L73,L81-L82].
    ACAS_SEED_JOBSTATUS="$ACAS_SEED_LAST_RC"

    acas_abort_on_rc "$ACAS_SEED_LAST_RC" "$ACAS_S_LOADER" \
      "$ACAS_SEED_SYSTEM_FLAT_FILE" "$ACAS_S_TEST" "$ACAS_S_LOCATOR" 'system'
  done
}

# STAGE 2 -- THE FLAT-FILE MAPPINGS [common/masterLD.sh:L93-L116]
# [common/masterLD.sh:L90-L91] verbatim.
acas_seed_mappings() {
  acas_stage 'Stage 2/2: the flat-file mappings  [common/masterLD.sh:L93-L116]'

  local entry
  for entry in "${ACAS_SEED_MAPPINGS[@]}"; do
    acas_split_entry "$entry"

    # The frozen line, reproduced in valid shell (D1).
    if [[ ! -e "$ACAS_E_FLAT" ]]; then
      acas_log "$ACAS_E_FLAT absent -> $ACAS_E_LOADER not run  [common/masterLD.sh:$ACAS_E_LOCATOR]"
      acas_summary_row "$ACAS_E_LOADER" "$ACAS_E_FLAT" 'no' '-' 'skipped-absent'
      continue
    fi

    if ! acas_loader_selected "$ACAS_E_LOADER"; then
      acas_log "$ACAS_E_LOADER -> not selected by --only; skipped"
      acas_summary_row "$ACAS_E_LOADER" "$ACAS_E_FLAT" 'yes' '-' 'skipped-only'
      continue
    fi

    acas_log "$ACAS_E_LOADER  <- $ACAS_E_FLAT  -> $ACAS_E_TABLE  [common/masterLD.sh:$ACAS_E_LOCATOR]"
    acas_invoke_loader "$ACAS_E_LOADER"
    ACAS_SEED_JOBSTATUS="$ACAS_SEED_LAST_RC"
    acas_abort_on_rc "$ACAS_SEED_LAST_RC" "$ACAS_E_LOADER" "$ACAS_E_FLAT" \
      'gt63' "$ACAS_E_LOCATOR" 'mapping'
  done
}

acas_report_out_of_scope() {
  acas_stage 'Out-of-scope mappings: never invoked (deviation D7)'

  local entry present=0
  for entry in "${ACAS_SEED_OUT_OF_SCOPE[@]}"; do
    acas_split_entry "$entry"
    if [[ -e "$ACAS_E_FLAT" ]]; then
      present=$(( present + 1 ))
      acas_log "$ACAS_E_FLAT IS PRESENT and is DELIBERATELY SKIPPED: $ACAS_E_LOADER loads $ACAS_E_TABLE, which the posting cycle never touches  [common/masterLD.sh:$ACAS_E_LOCATOR]"
      acas_summary_row "$ACAS_E_LOADER" "$ACAS_E_FLAT" 'yes' '-' 'skipped-out-of-scope'
    else
      acas_summary_row "$ACAS_E_LOADER" "$ACAS_E_FLAT" 'no' '-' 'skipped-out-of-scope'
    fi
  done

  if (( present == 0 )); then
    acas_log 'none of the 8 out-of-scope flat files is present; nothing to skip'
  else
    acas_note "$present out-of-scope flat file(s) present and skipped by design; their tables are not part of the 22 the parity diff covers"
  fi
}



# The frozen tail, [common/masterLD.sh:L119-L123] verbatim:
#     if [ -e SYS-DISPLAY.log ]; then
#        echo "All loads complete but check SYS-DISPLAY.log"
#        less SYS-DISPLAY.log
#        exit 0
#     fi
# Deviation D6, on three counts.
#
#  1. `less' is an interactive pager and would block the harness for ever, so the
#     prompt is dropped: a pause whose only effect is to block a terminal has no
#     database effect and is not reproduced.
#
#  2. THE LOG'S CONTENT IS NOT REPLAYED (OBS-008). It used to be `cat'-ed in
#     full, or `tail'-ed when large, onto standard output -- which Compose
#     collects as a container log and keeps. Three reasons that is wrong, and the
#     first alone settles it:
#       * THE FILE IS APPEND-ONLY AND SPANS EVERY PREVIOUS RUN. The frozen
#         loaders append and nothing in the frozen path clears it, so replaying
#         it publishes other runs' diagnostics as though they were this run's.
#         That is not a current-run summary, and it is not evidence of anything.
#       * Its content is loader output about live accounting data: it names the
#         flat files, the tables and the rows a load rejected (CWE-532).
#       * It is arbitrary multi-line text, so a line inside it can be read as a
#         line of this script's own output (CWE-117).
#     What replaces it is a bounded CURRENT-RUN summary: how many bytes THIS run
#     appended, the file's total size, its path and its SHA-256. The file itself
#     is untouched and stays exactly where the frozen loaders put it, so an
#     operator who wants the detail opens it -- and the digest proves the file
#     they open is the one this run wrote to.
#
#  3. The frozen block exits 0 only when the log exists, falling off the end of
#     the file otherwise, so this script always exits explicitly and never
#     unconditionally with 0.

# The log is NOT truncated between runs: the frozen loaders append to it and
# nothing in the frozen path clears it, so clearing it here would change the
# seed path rather than reproduce it (R-4). It lives in the data directory, is
# never dumped and is never compared, so its growth cannot affect determinism.
# acas_seed_note_sysout_baseline
# Record the append-only log's size before any loader runs. Called from
# `acas_main' immediately before the first load program, and deliberately not
# earlier: the working directory is re-pointed at a staged scenario fixture
# during setup, and the size that matters is the one in the directory the loaders
# will actually write in.
acas_seed_note_sysout_baseline() {
  local bytes=''

  if [[ ! -e "$ACAS_SEED_SYSOUT_LOG" ]]; then
    ACAS_SEED_SYSOUT_BASELINE=0
    return 0
  fi
  bytes="$(wc -c <"$ACAS_SEED_SYSOUT_LOG" 2>/dev/null | tr -d '[:space:]')"
  if [[ "$bytes" =~ ^[0-9]+$ ]]; then
    ACAS_SEED_SYSOUT_BASELINE="$bytes"
  else
    ACAS_SEED_SYSOUT_BASELINE=''
  fi
}

acas_report_sysout_log() {
  if [[ ! -e "$ACAS_SEED_SYSOUT_LOG" ]]; then
    acas_log "no $ACAS_SEED_SYSOUT_LOG was produced in $PWD"
    return 0
  fi

  printf '%s\n' "$ACAS_SEED_COMPLETE_MSG"
  acas_tee "$ACAS_SEED_COMPLETE_MSG"

  local bytes=0 appended=0 digest=''
  bytes="$(wc -c <"$ACAS_SEED_SYSOUT_LOG" 2>/dev/null | tr -d '[:space:]')"
  [[ "$bytes" =~ ^[0-9]+$ ]] || bytes=0

  # THE CURRENT-RUN BOUND. `acas_seed_note_sysout_baseline' recorded the size
  # before the first loader ran, so the difference is exactly what THIS run
  # appended -- which is the only part of an append-only file that this run can
  # honestly report on.
  if [[ "$ACAS_SEED_SYSOUT_BASELINE" =~ ^[0-9]+$ ]] \
     && (( bytes >= ACAS_SEED_SYSOUT_BASELINE )); then
    appended=$(( bytes - ACAS_SEED_SYSOUT_BASELINE ))
    acas_log "$ACAS_SEED_SYSOUT_LOG grew by ${appended} byte(s) during this run, to ${bytes} byte(s) in total"
  else
    acas_log "$ACAS_SEED_SYSOUT_LOG is ${bytes} byte(s) in total; this run's share of it could not be determined"
  fi
  acas_log "it is at $PWD/$ACAS_SEED_SYSOUT_LOG"
  digest="$(acas_diag_sha256 "$ACAS_SEED_SYSOUT_LOG")"
  if [[ -n "$digest" ]]; then
    acas_log "sha256 = $digest"
  fi
  acas_note 'the loaders APPEND to it, so it spans previous runs as well as this one'
  acas_note 'its CONTENT is not replayed here: it is loader output about the rows a load'
  acas_note 'rejected, it spans runs this one cannot speak for, and standard output is a'
  acas_note 'collected container log. Open the file above for the detail (deviation D6).'
}

# The closing report: the summary table, JOBSTATUS, and every non-fatal
# finding.
ACAS_SEED_REPORTED=0
acas_seed_report() {
  if (( ACAS_SEED_REPORTED )); then
    return 0
  fi
  ACAS_SEED_REPORTED=1

  acas_stage 'Summary'
  local header
  header="$(printf '%-14s %-17s %-8s %-5s %s' 'LOADER' 'FLAT FILE' 'PRESENT' 'RC' 'DECISION')"
  printf '    %s\n' "$header"
  acas_tee "    $header"
  printf '    %s\n' '-------------- ----------------- -------- ----- ------------------------'
  acas_tee "    -------------- ----------------- -------- ----- ------------------------"
  local row
  for row in "${ACAS_SEED_SUMMARY[@]}"; do
    printf '    %s\n' "$row"
    acas_tee "    $row"
  done

  acas_log ''
  acas_log "load programs run          : $ACAS_SEED_RAN"
  acas_log "JOBSTATUS (last loader rc) : $ACAS_SEED_JOBSTATUS   [common/masterLD.sh:L50,L55,L64,L73,L82]"
  acas_log "worst return code seen     : $ACAS_SEED_WORST_RC"
  if [[ -n "$ACAS_SEED_SCENARIO" ]]; then
    acas_log "scenario                   : $ACAS_SEED_SCENARIO"
  fi
  acas_log "run log                    : ${ACAS_SEED_LOG:-<not opened>}"

  if (( ${#ACAS_SEED_WARN_SUMMARY[@]} )); then
    printf '\n--- %s non-fatal finding(s) reported during this run ---\n' \
      "${#ACAS_SEED_WARN_SUMMARY[@]}"
    local entry
    for entry in "${ACAS_SEED_WARN_SUMMARY[@]}"; do
      printf '    %s\n' "$entry"
      acas_tee "    finding: $entry"
    done
    printf -- '--- end of non-fatal findings ---\n'
  fi
}

acas_print_plan() {
  acas_stage 'Dry run: the plan, in the frozen order'
  acas_note 'nothing is executed and no database statement is issued'

  local header
  header="$(printf '%-6s %-17s %-14s %-6s %s' 'ORDER' 'FLAT FILE' 'LOADER' 'FROZEN' 'DECISION / TARGET')"
  printf '    %s\n' "$header"
  acas_tee "    $header"

  local n=0 entry decision
  for entry in "${ACAS_SEED_SYSTEM_BLOCK[@]}"; do
    acas_split_system_entry "$entry"
    n=$(( n + 1 ))
    if [[ ! -e "$ACAS_SEED_SYSTEM_FLAT_FILE" ]]; then
      decision='skip: system.dat absent'
    elif ! acas_loader_selected "$ACAS_S_LOADER"; then
      decision='skip: not selected by --only'
    elif [[ "$ACAS_S_TEST" == 'ne0' ]]; then
      decision="run, frozen test ${ACAS_SEED_TEST_TEXT_NE0}  -> $ACAS_S_TABLE"
    else
      decision="run, frozen test ${ACAS_SEED_TEST_TEXT_GT63} -> $ACAS_S_TABLE"
    fi
    printf '    %-6s %-17s %-14s %-6s %s\n' \
      "$n" "$ACAS_SEED_SYSTEM_FLAT_FILE" "$ACAS_S_LOADER" "$ACAS_S_LOCATOR" "$decision"
  done

  for entry in "${ACAS_SEED_MAPPINGS[@]}"; do
    acas_split_entry "$entry"
    n=$(( n + 1 ))
    if [[ ! -e "$ACAS_E_FLAT" ]]; then
      decision='skip: flat file absent'
    elif ! acas_loader_selected "$ACAS_E_LOADER"; then
      decision='skip: not selected by --only'
    else
      decision="run, frozen test ${ACAS_SEED_TEST_TEXT_GT63} -> $ACAS_E_TABLE"
    fi
    printf '    %-6s %-17s %-14s %-6s %s\n' \
      "$n" "$ACAS_E_FLAT" "$ACAS_E_LOADER" "$ACAS_E_LOCATOR" "$decision"
  done

  for entry in "${ACAS_SEED_OUT_OF_SCOPE[@]}"; do
    acas_split_entry "$entry"
    if [[ -e "$ACAS_E_FLAT" ]]; then
      decision="NEVER invoked (out of scope: $ACAS_E_TABLE) -- flat file IS present"
    else
      decision="NEVER invoked (out of scope: $ACAS_E_TABLE)"
    fi
    printf '    %-6s %-17s %-14s %-6s %s\n' \
      '-' "$ACAS_E_FLAT" "$ACAS_E_LOADER" "$ACAS_E_LOCATOR" "$decision"
  done

  acas_log ''
  acas_log "return codes : frozen -- \`-gt 63' [common/masterLD.sh:L41]; dfltLD \`!= 0' [L83]"
  acas_log "strict opt-in: ACAS_SEED_STRICT=${ACAS_SEED_STRICT:-<unset>}; unset = frozen"
  acas_log "             : tolerance plus the post-seed gate, 1 = fail fast (D5)"
  acas_note 'the MariaDB readiness and autocommit assertions are NOT performed in a'
  acas_note 'dry run; a real run refuses to seed unless autocommit is OFF, globally'
  acas_note 'and for the session, as the Agent Action Plan mandates for the seeding'
  acas_note 'window (sections 0.2.1.1, 0.4.1.7 and 0.5.2, from the banner at'
  acas_note '[common/glbatchLD.cbl:L9-L13]). A real run then WARNS that the frozen'
  acas_note 'loaders reach no COMMIT, so their writes are not durable under that'
  acas_note 'mode -- the reproduced legacy defect (R-4), never repaired here'
}

acas_assert_scenario() {
  [[ -n "$ACAS_SEED_SCENARIO" ]] || return 0

  [[ -e "$ACAS_SEED_SCENARIO" ]] || acas_die "$EX_USAGE" \
    "the scenario file '$ACAS_SEED_SCENARIO' does not exist." \
    'The canonical invocation passes a scenario file path; see' \
    'harness/docker-compose.yml.'
  [[ -f "$ACAS_SEED_SCENARIO" && -r "$ACAS_SEED_SCENARIO" ]] || acas_die "$EX_USAGE" \
    "the scenario '$ACAS_SEED_SCENARIO' is not a readable file."
}

# THE SCENARIO FIXTURE -- what makes a named scenario mean something A scenario
# file that is merely READ and logged is a trace, not a binding.
readonly ACAS_FIXTURE_MARKER='.acas-scenario-fixture'

acas_stage_scenario_seed() {
  [[ -n "$ACAS_SEED_SCENARIO" ]] || return 0

  acas_stage 'Preconditions 3/8: stage the scenario'"'"'s declared seed files'

  local scenario_real stem
  scenario_real="$(readlink -f -- "$ACAS_SEED_SCENARIO" 2>/dev/null \
    || printf '%s' "$ACAS_SEED_SCENARIO")"
  stem="${ACAS_SEED_SCENARIO##*/}"
  stem="${stem%.*}"
  if [[ ! "$stem" =~ ^[A-Za-z0-9_-]+$ ]]; then
    acas_die "$EX_USAGE" \
      "the scenario name '$stem' is not a plain identifier." \
      'It names a directory and appears in an identity marker, so it is' \
      'restricted to letters, digits, underscore and hyphen.'
  fi

  # Parse with python3 + PyYAML. The scenario path arrives as argv and is never
  # interpolated into the program text. Exit codes are the program's own.
  local parsed rc=0
  acas_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  parsed="$("${ACAS_DEADLINE_ARGV[@]}" python3 - "$scenario_real" 2>&1 <<'PY'
"""Emit the scenario's declared seed directory and seed file names.

Output, on stdout, one field per line:
    SEED_DIR<TAB><path or empty>
    SEED_FILE<TAB><name>          (repeated, in the order declared)

Exit 0 parsed, 3 unreadable or not a mapping, 4 no seed file list,
5 a seed file name is unusable, 6 PyYAML is unavailable.
"""

import os
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write('PyYAML is not installed; it is required to bind a '
                     'scenario to its seed files\n')
    raise SystemExit(6)

path = sys.argv[1]
try:
    with open(path, 'r', encoding='utf-8') as handle:
        document = yaml.safe_load(handle)
except (OSError, yaml.YAMLError) as error:
    sys.stderr.write('cannot parse %s: %s\n' % (path, error))
    raise SystemExit(3)

if not isinstance(document, dict):
    sys.stderr.write('%s does not contain a YAML mapping at the top level\n' % path)
    raise SystemExit(3)


def field(*names):
    for name in names:
        if name in document:
            return document[name]
    return None


files = field('seed_files', 'seed-files')
if files is None:
    sys.stderr.write(
        '%s declares no seed_files. A scenario must state which flat files it '
        'seeds from, or the dump it produces cannot be attributed to it.\n' % path)
    raise SystemExit(4)
if isinstance(files, str) or not isinstance(files, (list, tuple)):
    sys.stderr.write('seed_files in %s must be a list of file names\n' % path)
    raise SystemExit(4)
if not files:
    sys.stderr.write('seed_files in %s is empty\n' % path)
    raise SystemExit(4)

seed_dir = field('seed_dir', 'seed-dir')
if seed_dir is None:
    # Default: a directory beside the scenario file, named after it.
    stem = os.path.splitext(os.path.basename(path))[0]
    seed_dir = os.path.join(os.path.dirname(path), stem)
elif not isinstance(seed_dir, str):
    sys.stderr.write('seed_dir in %s must be a string\n' % path)
    raise SystemExit(4)
elif not os.path.isabs(seed_dir):
    seed_dir = os.path.join(os.path.dirname(path), seed_dir)

sys.stdout.write('SEED_DIR\t%s\n' % os.path.realpath(seed_dir))

seen = set()
for entry in files:
    if not isinstance(entry, str) or not entry:
        sys.stderr.write('seed_files in %s contains a non-string entry\n' % path)
        raise SystemExit(5)
    # A seed file is a BARE NAME. A path would let a scenario reach outside its
    # own directory, and the loaders resolve every name against ACAS_LEDGERS
    # anyway [copybooks/Proc-Get-Env-Set-Files.cob:L125-L136].
    if '/' in entry or '\\' in entry or entry in ('.', '..'):
        sys.stderr.write('seed file %r in %s must be a bare file name\n'
                         % (entry, path))
        raise SystemExit(5)
    if entry in seen:
        sys.stderr.write('seed file %r is listed twice in %s\n' % (entry, path))
        raise SystemExit(5)
    seen.add(entry)
    sys.stdout.write('SEED_FILE\t%s\n' % entry)
PY
  )" || rc=$?

  if (( rc != 0 )); then
    local hint='the scenario could not be bound to its seed files.'
    case "$rc" in
      3) hint='the scenario file could not be parsed as a YAML mapping.' ;;
      4) hint='the scenario declares no usable seed_files list.' ;;
      5) hint='the scenario declares an unusable seed file name.' ;;
      6) hint='PyYAML is not installed, so the scenario cannot be parsed.' ;;
    esac
    acas_die "$EX_FIXTURE" \
      "$hint" \
      "  scenario: $scenario_real" \
      "  reported: ${parsed:-<no output>}" \
      'A named scenario must state which flat files it seeds from. Without that,' \
      'the seed comes from whatever happens to be in the data directory and the' \
      'resulting dump cannot honestly be attributed to this scenario.' \
      'Run without a scenario argument to seed from the ambient data directory.'
  fi

  local seed_dir='' line name
  local -a wanted=()
  while IFS=$'\t' read -r key value; do
    case "$key" in
      SEED_DIR)  seed_dir="$value" ;;
      SEED_FILE) wanted+=("$value") ;;
    esac
  done <<<"$parsed"

  [[ -n "$seed_dir" ]] || acas_die "$EX_FIXTURE" \
    'the scenario parser produced no seed directory (internal invariant).'
  (( ${#wanted[@]} > 0 )) || acas_die "$EX_FIXTURE" \
    'the scenario parser produced no seed file names (internal invariant).'

  [[ -d "$seed_dir" ]] || acas_die "$EX_FIXTURE" \
    "the scenario's seed directory does not exist: $seed_dir." \
    "  scenario: $scenario_real" \
    'Create it holding the flat files the scenario declares, or set seed_dir in' \
    'the scenario to where they live.'

  acas_in_list 'system.dat' "${wanted[@]}" || acas_die "$EX_FIXTURE" \
    "the scenario does not declare system.dat among its seed files." \
    "  scenario: $scenario_real" \
    'The frozen order seeds the system block first and unconditionally' \
    '[common/masterLD.sh:L50-L88]; every later loader depends on it.'

  local absent=0
  for name in "${wanted[@]}"; do
    if [[ ! -f "$seed_dir/$name" || ! -r "$seed_dir/$name" ]]; then
      printf 'FATAL: declared seed file is missing or unreadable: %s\n' \
        "$seed_dir/$name" >&2
      absent=1
    fi
  done
  if (( absent )); then
    acas_die "$EX_FIXTURE" \
      "the scenario declares seed files that are not present in $seed_dir." \
      "  scenario: $scenario_real" \
      'Every declared file must exist before the load programs run: a missing' \
      'one would leave its table empty and the dump would still look like a' \
      'successful seed.'
  fi

  # A FRESH scenario-owned directory. Fresh matters: a flat file left by
  # another scenario would be read by the loaders and attributed to this one.
  local staging="$ACAS_SEED_DATA_DIR/$stem"
  acas_assert_outside_repo "the scenario fixture directory" "$staging"

  rm -rf -- "$staging" || acas_die "$EX_FIXTURE" \
    "could not clear the scenario fixture directory $staging."
  mkdir -p "$staging" || acas_die "$EX_FIXTURE" \
    "could not create the scenario fixture directory $staging."

  for name in "${wanted[@]}"; do
    cp -p -- "$seed_dir/$name" "$staging/$name" || acas_die "$EX_FIXTURE" \
      "could not stage $name into $staging."
  done

  local marker="$staging/$ACAS_FIXTURE_MARKER"
  {
    printf 'scenario\t%s\n' "$stem"
    printf 'files\t%s\n' "${#wanted[@]}"
    for name in $(printf '%s\n' "${wanted[@]}" | LC_ALL=C sort); do
      printf 'file\t%s\t%s\n' "$name" \
        "$(acas_file_sha256 "$staging/$name")"
    done
  } >"$marker" || acas_die "$EX_FIXTURE" \
    "could not write the scenario fixture marker $marker."

  # From here on the loaders read the staged fixture and nothing else.
  ACAS_SEED_DATA_DIR="$staging"
  ACAS_SEED_FIXTURE_DIR="$staging"

  acas_log "scenario fixture staged: ${#wanted[@]} file(s) from $seed_dir"
  acas_log "fixture directory = $staging  (the loaders read ONLY this)"
  acas_log "identity marker   = $stem/$ACAS_FIXTURE_MARKER"
  for line in "${wanted[@]}"; do
    acas_log "  staged: $line"
  done
}

# python3 is already required, so the marker can never silently lose its
# digests.
acas_file_sha256() {
  local path="$1" digest=''
  acas_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  if acas_have sha256sum; then
    digest="$("${ACAS_DEADLINE_ARGV[@]}" sha256sum -- "$path")" || return 1
    printf '%s' "${digest%% *}"
    return 0
  fi
  "${ACAS_DEADLINE_ARGV[@]}" python3 - "$path" <<'PY' || return 1
import hashlib
import sys

digest = hashlib.sha256()
with open(sys.argv[1], 'rb') as handle:
    for block in iter(lambda: handle.read(1 << 16), b''):
        digest.update(block)
sys.stdout.write(digest.hexdigest())
PY
}

# MAIN Strictly sequential (R-3). No stage is backgrounded and none is
# parallelised. Nothing here writes to $ACAS_REPO.
acas_main() {
  acas_parse_args "$@"

  printf 'harness/seed.sh -- seeding the frozen ACASDB schema from the ACAS Cobol flat files\n'
  printf 'reproducing the contract of common/masterLD.sh [common/masterLD.sh:L44-L115];\n'
  printf 'that script is NEVER executed -- its author marks it untested\n'
  printf '[common/masterLD.sh:L4-L5] and it is not valid shell (bash -n rejects it at\n'
  printf 'line 124). It is frozen and is not fixed.\n'

  # Before ANY external process is spawned: a malformed budget must be a
  # startup usage error rather than something discovered mid-seed.
  acas_resolve_deadlines

  acas_assert_environment
  acas_open_log
  acas_assert_scenario
  if [[ -n "$ACAS_SEED_SCENARIO" ]]; then
    acas_log "scenario = $ACAS_SEED_SCENARIO (BINDING: its declared seed files become the seed)"
  fi
  acas_assert_data_dir
  # After acas_assert_data_dir, which resolves and validates the data root, and
  # BEFORE acas_assert_system_dat, which tests for system.dat in whatever
  # directory the loaders will actually read.
  acas_stage_scenario_seed
  if [[ -n "$ACAS_SEED_FIXTURE_DIR" ]]; then
    export ACAS_LEDGERS="$ACAS_SEED_DATA_DIR"
    cd "$ACAS_SEED_DATA_DIR" || acas_die "$EX_FIXTURE" \
      "could not change directory to the scenario fixture $ACAS_SEED_DATA_DIR."
    acas_log "working directory = $PWD  (the staged scenario fixture)"
    acas_log "ACAS_LEDGERS      = $ACAS_LEDGERS  (re-pointed at the fixture)"
  fi
  acas_assert_system_dat
  acas_assert_loaders
  acas_assert_library_paths

  if (( ACAS_SEED_DRY_RUN )); then
    acas_print_plan
    printf '\nharness/seed.sh dry run complete: nothing was executed.\n'
    exit "$EX_OK"
  fi

  acas_wait_for_database
  acas_assert_autocommit

  # BEFORE the first loader, so the completion report can bound itself to what
  # this run appended rather than replaying an append-only file (deviation D6).
  acas_seed_note_sysout_baseline

  acas_seed_system_block
  acas_seed_mappings
  acas_report_out_of_scope

  acas_stage 'Completion  [common/masterLD.sh:L119-L123]'
  acas_report_sysout_log
  acas_seed_report

  # This is the ONE place this script is stricter than the frozen one about a
  # return code the frozen test tolerates, and it deliberately sits HERE rather
  # than inside `acas_abort_on_rc'.
  if (( ACAS_SEED_WORST_RC != 0 )); then
    printf '\nharness/seed.sh completed with a non-zero load-program return code (%s).\n' \
      "$ACAS_SEED_WORST_RC" >&2
    printf 'No loader hit the frozen abort test, so the frozen contract did not stop the\n' >&2
    printf 'run and seeding continued to the end of the sequence\n' >&2
    printf '[common/masterLD.sh:L41,L56-L58]. The seeded state may therefore be PARTIAL,\n' >&2
    printf 'so this harness refuses to pass it to a state diff (deviation D5). Run\n' >&2
    printf 'harness/reset_db.sh before taking a diff.\n' >&2
    exit "$ACAS_SEED_WORST_RC"
  fi

  printf '\nharness/seed.sh completed: %s load program(s) ran, all returning 0.\n' "$ACAS_SEED_RAN"
  printf 'Next: harness/run_cobol_scenario.sh, then harness/dump_tables.py.\n'
  exit "$EX_OK"
}

acas_main "$@"
