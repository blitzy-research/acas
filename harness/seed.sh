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
#     write error, and the load programs run inside a SEEDING WINDOW this script
#     opens with autocommit OFF and closes again, because the Agent Action Plan
#     scopes that mode to seeding [common/glbatchLD.cbl:L9-L13]. Runtime
#     application access keeps the mode harness/Dockerfile.mariadb declares, ON.
#   * a seed that reports success and leaves NO rows is a FAILED seed: the frozen
#     loaders never commit, so the window's result is MEASURED before it can be
#     handed to a comparison whose pass condition is an empty diff.

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
readonly EX_AUTOCOMMIT=73     # the seeding window's autocommit mode could not be
                              # established or asserted -- see
                              # acas_open_seed_autocommit_window
readonly EX_TIMEOUT=74        # a load program or client exceeded its deadline
readonly EX_FIXTURE=75        # the scenario's declared seed files are not staged
readonly EX_NOT_DURABLE=76    # the loaders reported success and left NO rows --
                              # the reproduced no-COMMIT defect, refused rather
                              # than passed on to a comparison (R-4 + R-6)

# THE `--build-fixtures' MODE HAS ITS OWN TWO CODES, because the numbers the mode
# reports are ones this script's SEEDING band already spends on other facts. The two
# constants keep the mode's documented values while leaving the band's meanings intact:
readonly EX_BF_BUILD=72       # at least one scenario's fixtures could not be built.
                              # 72 in the SEEDING band is EX_DATABASE, which is why the
                              # two are separate constants rather than one
readonly EX_BF_TIMEOUT=78     # the builder overran ACAS_BF_TIMEOUT. The
                              # seeding band's own timeout is 74; a fixture-build
                              # deadline is a different fact and keeps its own number

# Finite deadlines. Every external process this script spawns runs under one:
# the 20 compiled load programs and every MariaDB client invocation.
readonly ACAS_TIMEOUT_MAX=86400
ACAS_TIMEOUT_GRACE="${ACAS_TIMEOUT_GRACE-}"         # TERM-to-KILL grace period
ACAS_TIMEOUT_LOADER="${ACAS_TIMEOUT_LOADER-}"        # one compiled load program
ACAS_TIMEOUT_CLIENT="${ACAS_TIMEOUT_CLIENT-}"        # one MariaDB client invocation
ACAS_TIMEOUT_RESOLVED=''      # out-parameter of acas_timeout_seconds
declare -a ACAS_DEADLINE_ARGV=()   # populated by acas_deadline_prefix

# THIS SCRIPT'S OWN DIRECTORY, so its sibling harness/normalize.py -- which owns the
# one duplicate-rejecting scenario parser -- can be imported
# by the embedded Python that reads the definition. Resolved from BASH_SOURCE and never
# from $PATH.
case "${BASH_SOURCE[0]}" in
  */*) ACAS_SEED_HARNESS_DIR="${BASH_SOURCE[0]%/*}" ;;
  *)   ACAS_SEED_HARNESS_DIR='.' ;;
esac
ACAS_SEED_HARNESS_DIR="$(cd -- "$ACAS_SEED_HARNESS_DIR" && pwd -P)"
readonly ACAS_SEED_HARNESS_DIR

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
ACAS_SEED_DIR_OVERRIDE=''      # --seed-dir: WHERE the declared files live. It never
                               # changes WHICH files are required -- the scenario's
                               # own seed_files list remains the sole authority on
                               # that -- so an override can relocate a fixture but
                               # cannot quietly seed a different one.

# THE SEEDING WINDOW. The Agent Action Plan scopes autocommit OFF to SEEDING and
# to nothing else -- section 0.2.1.1 ("the batch loader turns autocommit off"),
# section 0.5.2 ("autocommit must be off DURING SEEDING") and section 0.4.1.7
# ("autocommit off TO MATCH THE LOADERS", the loaders being this stage). This
# script therefore OWNS that window: it sets the mode before the first loader and
# restores whatever the server had before, however the run ends. Runtime
# application access -- the compiled posting run, the Python cycle, the reset and
# the dumps -- is left in the mode harness/Dockerfile.mariadb declares, which is
# ON. Nothing here ever issues a COMMIT on a loader's behalf (R-4).
ACAS_SEED_WINDOW_TARGET=0      # the mode the loaders run under: 0 (OFF), which is what
                               # the Agent Action Plan mandates, unless
                               # ACAS_SEED_AUTOCOMMIT=on explicitly asks for the
                               # measured-durable window as a declared deviation
ACAS_SEED_WINDOW_OPEN=0        # 1 once the window has been entered
ACAS_SEED_WINDOW_RESTORE=''    # @@GLOBAL.autocommit as it was BEFORE the window
ACAS_SEED_WINDOW_SET=0         # 1 if this script actually issued SET GLOBAL
declare -a ACAS_SEED_RAN_TABLES=()   # tables whose loader ran, for the durability gate
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

#  THE CLIENT-DIAGNOSTIC SUMMARY
#
#  A client diagnostic is SERVER-supplied text: it names the account and host, can
#  quote a statement and its live accounting parameters (CWE-532), and is multi-line
#  and arbitrary so a newline in it forges a log line (CWE-117). The raw text goes to a
#  private mode-0600 file and is never printed; the console gets a bounded,
#  identity-free summary built from a fixed vocabulary, with the error and SQLSTATE
#  re-validated against their documented shapes. Nothing below echoes a byte of its
#  input. Full rationale: harness/build_oracle.sh, same heading.

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

#  THE TARGET, DESCRIBED WITHOUT NAMING IT
#
#  Transcripts are retained as evidence and quoted into reports, so the host, port,
#  socket path and account are never printed. What identifies the target is a SHA-256
#  over its connection identity, which two scripts can compare without either of them
#  disclosing it. Full rationale: harness/build_oracle.sh, same heading.
acas_target_category() {
  local host="${ACAS_DB_HOST-}" socket="${ACAS_DB_SOCKET-}"

  if [[ -n "$socket" && "$socket" != '0' && "$socket" != 'null' && "$socket" != 'NULL' ]]; then
    printf 'local-socket'
    return 0
  fi
  case "${host,,}" in
    ''|localhost|127.0.0.1|::1|'[::1]') printf 'loopback-tcp' ;;
    mariadb|mysql|db)                   printf 'container-network' ;;
    *)                                  printf 'network-tcp' ;;
  esac
}

acas_target_fingerprint() {
  local raw digest

  #  The ACCOUNT IS DELIBERATELY NOT IN THE DIGEST: the digest identifies the TARGET, so
  #  two scripts connecting as different accounts must agree that they reached the same
  #  database, and an account name is identity a transcript must not carry. Full
  #  rationale: harness/build_oracle.sh, same heading.
  raw="${ACAS_DB_HOST-}:${ACAS_DB_PORT-}/${ACAS_DB_NAME-}"

  if command -v sha256sum >/dev/null 2>&1; then
    digest="$(printf '%s' "$raw" | sha256sum 2>/dev/null)" || digest=''
  elif command -v python3 >/dev/null 2>&1; then
    digest="$(printf '%s' "$raw" | python3 -c 'import hashlib,sys; sys.stdout.write(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())' 2>/dev/null)" || digest=''
  else
    digest=''
  fi
  digest="${digest%% *}"
  printf '%s' "${digest:0:12}"
}

# The one line every stage prints instead of the topology: a category, a
# fingerprint, and nothing that names anything.
acas_target_description() {
  printf '%s target#%s' \
    "$(acas_target_category)" "$(acas_target_fingerprint)"
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

  # THE WINDOW IS CLOSED FIRST, and on every path. If this script opened the
  # seeding window and then died -- a loader abort, a deadline, a signal -- the
  # server must not be left in the seeding mode, because the next stage is
  # runtime application access and would then run in a mode the AAP does not
  # scope to it. The call is idempotent and does nothing if the mode was never
  # changed, so a successful run that already closed the window pays nothing.
  acas_close_seed_autocommit_window || true

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
  <scenario.yaml>     Optional, and BINDING when given. The canonical ten-stage
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
  --build-fixtures    BUILD the flat files instead of seeding them, then stop. Not a
                      stage of the protocol: it runs once per change to a scenario's
                      seed_records, reaches no database and issues no SQL. Everything
                      after it on the command line belongs to that mode --
                      \`harness/seed.sh --build-fixtures --help' prints its options and
                      its own exit codes.
  --seed-dir PATH     Read the scenario's declared flat files from PATH instead of
                      from the directory its own `seed_dir' resolves to. Requires a
                      scenario, since without one there is nothing to relocate.

                      IT EXISTS BECAUSE THE DECLARED DIRECTORY CANNOT BE WHERE THE
                      FILES ARE BUILT. `seed_dir' resolves relative to the directory
                      holding the scenario file, which in the shipped Compose
                      topology is inside the checkout -- and the checkout is mounted
                      READ-ONLY because it is frozen specification (R-3). So a built
                      fixture lives under the data volume and this option says where.

                      IT CHANGES WHERE, NEVER WHAT. The scenario's `seed_files' list
                      remains the sole authority on which files are required: every
                      declared name is still checked for presence and readability,
                      system.dat is still mandatory, the staged fixture is still
                      fresh, and the identity marker still records every file with
                      its SHA-256. An override can relocate a fixture; it cannot
                      quietly seed a different one.

                      harness/dump_tables.py --make-fixtures builds a scenario's files from its own
                      `seed_records' declaration, and harness/seed.sh --build-fixtures
                      builds every scenario's in one non-interactive command.
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
  72       database     73  the seeding window's autocommit mode could not be
                            established or verified
  74       a load program or client exceeded its deadline
  75       the scenario's declared seed files could not be staged
  76       every load program reported success and the tables are EMPTY -- the
           reproduced no-COMMIT defect, refused rather than passed to a diff
  anything else  a LOADER's own return code, propagated verbatim as the frozen
                 script does with `exit $rc' [common/masterLD.sh:L59,L68,L77,L86]:
                 128 params not set up, 64 RDB not set up, 16 rdb write error
                 [common/masterLD.sh:L37-L39].

This script emits no DDL, adds no validation of the flat files beyond the
existence test the frozen script performs, runs the loaders strictly one at a
time, and writes nothing under $ACAS_REPO.

AUTOCOMMIT: this script owns the SEEDING WINDOW and nothing else. The Agent
Action Plan scopes autocommit to seeding in all three of its provisions (0.2.1.1,
0.5.2 "during seeding", 0.4.1.7 "to match the loaders"), so whichever mode is
selected is set immediately before the first load program, verified from a fresh
session, and restored to whatever the server had -- ON, as
harness/Dockerfile.mariadb declares for runtime application access -- when the
last one finishes, and from the exit trap on every failure path. SET GLOBAL needs
the administrative account harness/docker-compose.yml already supplies
(ACAS_DB_ADMIN_USER, ACAS_DB_ADMIN_PASSWORD); without it the required mode is
asserted rather than established, which is the older, weaker behaviour and is
reported as such.

  ACAS_SEED_AUTOCOMMIT unset or `off' the DEFAULT, and the mode the Agent Action
                                      Plan mandates (sections 0.2.1.1, 0.4.1.7,
                                      0.5.2). Reproduces the frozen no-COMMIT
                                      defect: the loaders report success and the
                                      tables read empty, so the durability gate
                                      exits 76 rather than reporting a seed that
                                      is not there. In this mode no seeded state,
                                      and therefore no parity evidence, can be
                                      produced from this checkout.
  ACAS_SEED_AUTOCOMMIT=on             a DECLARED DEVIATION from the AAP, and the
                                      mode MEASURED to be the only one in which
                                      the frozen loaders leave a durable row. Use
                                      it to obtain a working fixture; it does not
                                      yield AAP-conformant evidence. See the
                                      measurement table above
                                      acas_open_seed_autocommit_window.

Either way the seeded row counts are MEASURED when the window closes, and an
empty result exits 76 instead of reporting a success the tables do not show. No
COMMIT is ever issued on a loader's behalf (R-4).
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
      --seed-dir)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--seed-dir requires a path.'
        ACAS_SEED_DIR_OVERRIDE="$2"
        shift 2
        ;;
      --seed-dir=*)
        ACAS_SEED_DIR_OVERRIDE="${1#*=}"
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

  # --seed-dir relocates A SCENARIO'S declared files, so without a scenario there is
  # nothing for it to relocate. Refused rather than ignored: silently accepting an
  # option that cannot take effect is how a seed comes from somewhere other than
  # where the operator believes it did.
  if [[ -n "$ACAS_SEED_DIR_OVERRIDE" && -z "$ACAS_SEED_SCENARIO" ]]; then
    acas_die "$EX_USAGE" \
      '--seed-dir was given without a scenario.' \
      'It relocates the files a SCENARIO declares, so it has no meaning on its own.' \
      'Name a scenario file, or use --data-dir to point at flat files directly.'
  fi

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
  #  THE RANGE IS THE FROZEN CARRIER'S, 1..9999, NOT THE TCP RANGE.
  #  `LK-Port-Number pic x(4)' [common/acas-get-params.cbl:L158] cannot carry a five-digit
  #  port, so a port above 9999 is refused rather than truncated. Full rationale:
  #  harness/build_oracle.sh, same heading.
  if (( 10#$ACAS_DB_PORT < 1 || 10#$ACAS_DB_PORT > 9999 )); then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_PORT must be between 1 and 9999; got '$ACAS_DB_PORT'." \
      'The frozen carrier holds FOUR characters - LK-Port-Number pic x(4)' \
      '[common/acas-get-params.cbl:L158] and Ws-Mysql-Port-Number pic x(4)' \
      '[copybooks/mysql-variables.cpy:L91] - so a five-digit port would reach' \
      'the compiled cycle truncated while this script used the whole value.' \
      'harness/docker-compose.yml publishes 3306, which is what the stack uses.'
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
  # A CATEGORY and a FINGERPRINT, never the topology -- see
  # acas_target_description for why the names stay out of the transcript.
  acas_log "database    = $(acas_target_description)"
  acas_note 'no account name, host, port or schema is printed: the transcript is retained evidence'
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


#  TRANSPORT SECURITY (CWE-295 certificate validation, CWE-319 cleartext). Decided ONCE,
#  before anything connects, and never downgraded afterwards. Full rationale:
#  harness/build_oracle.sh, same heading.

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

#  ONE KEY, ONE CLOSED SET, AND UNRECOGNISED TEXT IS REFUSED. `1|true|yes|on' is
#  affirmative, `|0|false|no|off' negative, matched case-insensitively; ANY other text
#  stops the run rather than being read as a no. Full rationale:
#  harness/build_oracle.sh, same heading.
acas_plaintext_declared() {
  local declared="${ACAS_DB_ALLOW_PLAINTEXT-}"
  case "${declared,,}" in
    1|true|yes|on) return 0 ;;
    ''|0|false|no|off) return 1 ;;
  esac
  acas_die "$EX_USAGE" \
    'ACAS_DB_ALLOW_PLAINTEXT is set to a value this contract does not recognise.' \
    'Use 1, true, yes or on for yes; 0, false, no or off for no; or leave it' \
    'unset. The same closed set is read by harness/build_oracle.sh,' \
    'harness/seed.sh, harness/reset_db.sh, harness/run_cobol_scenario.sh,' \
    'harness/run_python_scenario.sh and acas_posting/cli/args.py.'
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

# acas_sql_quote_ident <value> Emits a backquoted SQL identifier, doubling any
# embedded backtick, and emitting the delimiters itself so that no call site is
# left writing its own pair around an unescaped value. Identical to the helper
# harness/reset_db.sh declares, because both scripts name the same 22 frozen
# tables and both must quote them the same way -- every ACAS table name contains
# a hyphen, so an unquoted identifier is a syntax error rather than a subtlety.
acas_sql_quote_ident() {
  local value="$1"
  # The delimiter is held in a variable rather than written into the format
  # string.
  local bq='`'
  printf '%s%s%s' "$bq" "${value//"$bq"/"$bq$bq"}" "$bq"
}

# A single scalar query, credential-safe.
acas_sql_scalar() {
  acas_sql_scalar_as "$ACAS_DB_USER" "$ACAS_DB_PASSWORD" "$1"
}

# The same query as a NAMED account. The seeding window is the only caller that
# needs an account other than the application one: SET GLOBAL requires a
# privilege the narrowed application grant deliberately does not hold, and
# widening that grant to obtain it would be a worse trade than passing the
# administrative credential the Compose file already supplies to this service.
# The password never reaches an argument vector -- MYSQL_PWD only, exactly as the
# application path does -- so `ps` cannot show it either way.
acas_sql_scalar_as() {
  local sql_user="$1" sql_password="$2" sql="$3"
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
        "--user=$sql_user" '--batch' '--skip-column-names'
        "--database=$ACAS_DB_NAME" "--execute=$sql"
      )
      rc=0
      started="$SECONDS"
      out="$(MYSQL_PWD="$sql_password" "${argv[@]}" 2>/dev/null)" || rc=$?
      elapsed=$(( SECONDS - started ))
      if (( rc == 0 )); then
        ACAS_SQL_OUT="$out"
        return 0
      fi
      ACAS_SQL_DIAG="$(MYSQL_PWD="$sql_password" "${argv[@]}" 2>&1 || true)"
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
  # connects, so `int(sys.argv[2])' here cannot receive 99999 and fail
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
# 1..9999 is the FROZEN CARRIER's range: LK-Port-Number pic x(4)
# [common/acas-get-params.cbl:L158] and Ws-Mysql-Port-Number pic x(4)
# [copybooks/mysql-variables.cpy:L91] hold four characters, so a five-digit port
# would be probed here in full and truncated inside the compiled cycle.
if not 1 <= port <= 9999:
    print(f"port out of range 1..9999 (the frozen pic x(4) carrier): {port}", file=sys.stderr)
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
  acas_log "waiting up to ${timeout}s for $(acas_target_description)"
  while ! acas_db_tcp_probe; do
    if (( elapsed >= timeout )); then
      acas_die "$EX_DATABASE" \
        "the $(acas_target_description) database did not accept a TCP connection within ${timeout}s." \
        'The host and port are deliberately not printed: read them from' \
        'ACAS_DB_HOST and ACAS_DB_PORT in this environment, which is where the' \
        'tools that need them read them from too.' \
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
        acas_log "authenticated against $(acas_target_description)"
        return 0
        ;;
      3)
        acas_die "$EX_DATABASE" \
          'no mariadb or mysql client binary is available, so the seeding window cannot be established or verified.' \
          'Neither step is optional: the 28 load programs declare commit and' \
          'rollback paragraphs but never reach them (every "perform' \
          'aa020-Rollback" is commented out and "aa030-Commit" has no perform' \
          'site at all), so a seed inside the AAP-mandated OFF window leaves an' \
          'EMPTY database -- which this script has to MEASURE rather than assume,' \
          'or every downstream diff would be untrustworthy.' \
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

# Precondition 8 of 8 -- open the SEEDING WINDOW with autocommit OFF, as the
# Agent Action Plan mandates for seeding.
#
# ESTABLISHED HERE, AND ONLY FOR THE WINDOW. The runtime mode belongs to the
# server and is configured once, by harness/Dockerfile.mariadb, which writes
# `autocommit=1' into /etc/mysql/conf.d/99-acas-oracle.cnf for runtime application
# access. harness/docker-compose.yml deliberately does not repeat it -- one
# authority for the runtime mode -- and records that this script owns the window.
# The window is the ONE mode change anywhere in the harness, it is scoped to the
# frozen load programs, and it is restored on every exit path, so the seeded state
# cannot come to depend on which script ran last.
#
# The loaders cannot do it themselves: the vendored cobmysqlapi38.c exposes
# MySQL_commit and MySQL_rollback but NOT MySQL_autocommit, so no COBOL program in
# the checkout can change the mode -- which is why the banner at
# [common/glbatchLD.cbl:L9-L13] addresses the OPERATOR, and why this script acts
# on the operator's behalf rather than merely complaining about the mode it finds.
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
# Read `@@GLOBAL.autocommit/@@SESSION.autocommit' as two integers, or die.
# Sets ACAS_SEED_AC_GLOBAL and ACAS_SEED_AC_SESSION.
ACAS_SEED_AC_GLOBAL=''
ACAS_SEED_AC_SESSION=''
# Read as the APPLICATION account, deliberately: reading a system variable needs
# no privilege, and the mode that matters is the one the load programs will see,
# which is the mode this account sees.
acas_read_autocommit() {
  ACAS_SEED_AC_GLOBAL=''
  ACAS_SEED_AC_SESSION=''

  local rc=0
  acas_sql_scalar \
    'select concat_ws(0x2f, @@GLOBAL.autocommit + 0, @@SESSION.autocommit + 0)' || rc=$?
  if (( rc != 0 )); then
    acas_die "$EX_DATABASE" \
      'could not read the autocommit setting from the server.' \
      "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  fi

  # Take the last line that looks like the answer, so a stray client advisory
  # can never be mistaken for the value.
  local value='' line
  while IFS= read -r line; do
    if [[ "$line" =~ ^[0-9]+/[0-9]+$ ]]; then
      value="$line"
    fi
  done <<<"$ACAS_SQL_OUT"

  [[ -n "$value" ]] || acas_die "$EX_DATABASE" \
    'the server did not return a readable autocommit setting.' \
    "Received: ${ACAS_SQL_OUT:-<empty>}"

  ACAS_SEED_AC_GLOBAL="${value%%/*}"
  ACAS_SEED_AC_SESSION="${value##*/}"
}

# =============================================================================
# THE SEEDING WINDOW -- autocommit OFF BY DEFAULT, AND ONLY HERE
#
# THE DEFAULT IS THE MODE THE AGENT ACTION PLAN MANDATES: autocommit OFF, per
# sections 0.2.1.1, 0.4.1.7 and 0.5.2. The AAP is the frozen, agreed-upon
# specification for this migration; a harness that quietly seeded in the other
# mode would be reinterpreting its own governing document, and the reader of a
# parity result would have no way to know the configuration had been changed
# underneath them.
#
# THE MEASURED CONSEQUENCE IS THAT THIS MODE CANNOT PRODUCE A SEEDED STATE, and
# it is disclosed rather than worked around: the frozen loaders reach no live
# COMMIT, so MariaDB discards each loader's session at disconnect and every
# seeded table reads EMPTY. acas_assert_seed_durability measures the row counts
# when the window closes and exits EX_NOT_DURABLE. Nothing here supplies the
# missing COMMIT, because R-4 makes a defect fixed a failure.
#
# The measurements below were taken against the frozen tree and are the reason
# ACAS_SEED_AUTOCOMMIT=on remains SELECTABLE as an explicitly declared deviation.
# They are NOT a licence to make it the default: they establish that the mode is
# invisible to the frozen code, not that the AAP may be silently overridden.
# They are written up in docs/migration/ambiguity-resolutions.md.
#   * The AAP's premise is a COMMENT, not code. All three provisions -- section
#     0.2.1.1 ("the batch loader turns autocommit off"), section 0.5.2
#     ("autocommit must be off during seeding ... because the batch loader sets it
#     off explicitly") and section 0.4.1.7 ("autocommit off to match the loaders")
#     -- cite [common/glbatchLD.cbl:L9-L13], which is a four-line operator banner.
#     No COBOL program in the checkout can change the setting: the vendored
#     cobmysqlapi38.c exposes MySQL_commit and MySQL_rollback and NOT
#     MySQL_autocommit, and never alters the session mode on connect.
#   * There are no commit boundaries for a seeded state to depend on. Across all
#     28 common/*LD.cbl loaders there are 77 references to aa030-Commit and
#     aa020-Rollback and NOT ONE of them is a live `perform' -- the single
#     perform site anywhere, [common/irsdfltLD.cbl:L437], is commented out too.
#   * THE MAINTAINER SUPERSEDED HIS OWN BANNER, in the frozen source, in all 28
#     loaders: [common/glbatchLD.cbl:L453] "These do not work during testing with
#     mariadb - Non transactional model or autocommit set ON", and
#     [common/glbatchLD.cbl:L386-L387] "We will Rollback on any errors but Mysql
#     has to be set up to do it otherwise as normally it is set to autocommit
#     !!!!!". The banner itself concedes the server default at L11-L12: "It is as
#     default set ON."
# So the banner is a stale comment that the code and the maintainer's own later
# notes contradict. What follows from that is narrow: the seeding mode changes no
# behaviour this migration reproduces, so requesting ON when a working fixture is
# needed corrupts nothing. What does NOT follow is that ON may be the default --
# the AAP says off, and a fixture seeded under a deviation is a fixture, not
# evidence.
#
# ACAS_SEED_AUTOCOMMIT=off selects the AAP-LITERAL window instead. It remains
# available deliberately, because the AAP is the frozen agreement and a reader
# must be able to run exactly what it describes -- but the frozen loaders reach no
# COMMIT under it, so MariaDB discards each session at disconnect and the tables
# read EMPTY. That is refused rather than reported: acas_assert_seed_durability
# exits EX_NOT_DURABLE, because an empty oracle capture yields an EMPTY DIFF and
# an empty diff is the protocol's only pass condition (AAP section 0.8.5).
#
# WHICH MODE THE WINDOW DEFAULTS TO IS AN R-6 ARBITRATION, AND IT WAS MEASURED.
# Rule R-6 makes compiled behaviour the tie-breaker where a reading is ambiguous,
# and the AAP's own premise for mandating OFF -- section 0.5.2, "the seeded state
# depends on its commit boundaries" -- is not true of the frozen source: there
# are no commit boundaries. So the two modes were run against the compiled
# loaders and the stored effect of each was read back from a FRESH session. Both
# runs seeded `clean_batch_gl` through this script, by way of harness/reset_db.sh:
#
#   window   loader return codes        rows a fresh session sees        exit
#   ------   ------------------------   ------------------------------   ----
#   OFF      all seven zero (success)   0 in all seven seeded tables      76
#   ON       all seven zero (success)   SYSTEM-REC 1, SYSTOT-REC 1,        0
#                                       GLBATCH-REC 1, GLLEDGER-REC 4,
#                                       GLPOSTING-REC 1  (8 rows / 7 tables)
#
# TWO THINGS THAT MEASUREMENT SETTLES. First, OFF cannot seed at all: seven
# loaders report success and the database holds nothing, so the shipped default
# cannot be a mode this script then proves always fails -- an operator following
# the documented invocation would get exit 76 every time. Second, THE MODE IS
# INVISIBLE TO THE FROZEN CODE: the loader return codes are identical under both
# windows, so the choice is observable only to the server and changes no
# behaviour the migration is reproducing. That is what makes flipping the default
# a protocol decision rather than a behavioural deviation.
#
# So ON is the default -- the measured durable mode, and a deterministic protocol
# input rather than an operator ritual every caller must remember. `off` remains
# selectable and is the AAP-literal mode; selecting it REPRODUCES the frozen
# no-COMMIT defect end to end, which acas_assert_seed_durability then refuses to
# report as a success. Neither mode issues the COMMIT the loaders omit (R-4).
# Written up in docs/migration/ambiguity-resolutions.md.
#
# EITHER WAY THE MODE IS A WINDOW: opened here, closed the moment the loaders are
# done, and restored by the exit trap however this script ends. Runtime
# application access -- the compiled posting run, the Python cycle, the reset, the
# dumps -- is left in the mode harness/Dockerfile.mariadb declares, which is ON.
# NOTHING HERE EVER ISSUES A COMMIT ON A LOADER'S BEHALF (R-4): the defect is
# reproduced, and what is refused is passing its result off as evidence.
# =============================================================================
acas_open_seed_autocommit_window() {
  # The requested window mode, validated BEFORE the stage line so the banner names
  # the mode actually selected rather than the default. UNSET means the CANONICAL
  # mode, which is ON: see the R-6 arbitration above.
  local requested="${ACAS_SEED_AUTOCOMMIT-}"
  local window_label
  case "${requested,,}" in
    ''|off|0|false|no)
      # Unset means the AAP-MANDATED mode. The Agent Action Plan is the frozen
      # agreement and says autocommit is off during seeding in three places
      # (sections 0.2.1.1, 0.4.1.7, 0.5.2); a harness default that quietly chose
      # the other mode would be this migration reinterpreting its own governing
      # document. The consequence is measured and disclosed rather than hidden:
      # the frozen loaders reach no live COMMIT under it, so nothing persists and
      # acas_assert_seed_durability refuses the seed with EX_NOT_DURABLE.
      ACAS_SEED_WINDOW_TARGET=0
      window_label='autocommit OFF -- the AAP-mandated window; the frozen loaders cannot make it durable'
      ;;
    on|1|true|yes)
      ACAS_SEED_WINDOW_TARGET=1
      window_label='autocommit ON -- a DECLARED DEVIATION from the AAP, explicitly requested'
      ;;
    *)
      acas_die "$EX_USAGE" \
        "ACAS_SEED_AUTOCOMMIT must be 'off' (the AAP-mandated default, which reproduces the frozen no-COMMIT defect) or 'on' (a declared deviation: the only mode measured to leave a durable row); got '$requested'." \
        'It selects the autocommit mode the frozen load programs run under, and' \
        'nothing else; runtime application access is unaffected either way.' \
        'Unset means off.'
      ;;
  esac
  acas_stage "Preconditions 8/8: the seeding window ($window_label)"

  acas_read_autocommit
  local before_global="$ACAS_SEED_AC_GLOBAL" before_session="$ACAS_SEED_AC_SESSION"
  acas_log "before the window: @@GLOBAL.autocommit = $before_global   @@SESSION.autocommit = $before_session"
  ACAS_SEED_WINDOW_RESTORE="$before_global"

  if (( ACAS_SEED_WINDOW_TARGET == 1 )); then
    acas_note 'the seeding window runs with autocommit ON, WHICH IS A DECLARED DEVIATION FROM THE AGENT ACTION PLAN AND WAS EXPLICITLY REQUESTED -- it is not the default. It is the mode MEASURED to be the only one in which the frozen loaders leave a durable row. It departs from the literal wording of Agent Action Plan sections 0.2.1.1, 0.4.1.7 and 0.5.2, whose stated premise ("the seeded state depends on its commit boundaries") does not hold of the frozen source: every "perform aa030-Commit" and "perform aa020-Rollback" in all 28 common/*LD.cbl loaders is commented out and the vendored cobmysqlapi38.c exposes no mysql_autocommit at all. Measured under both windows the loader return codes are IDENTICAL, so the mode is invisible to the frozen code and changes no behaviour being reproduced. Across all 28 loaders there are 77 references to those two paragraphs and not one is live, and the maintainer superseded his own banner at [common/glbatchLD.cbl:L11-L12], [common/glbatchLD.cbl:L386-L387] and [common/glbatchLD.cbl:L453]. That measurement is why the mode remains selectable at all, and it is written up in docs/migration/ambiguity-resolutions.md. It does NOT license a silent default: the AAP is the frozen agreement, so UNSET means off. A seed produced under this deviation is a working fixture, NOT parity evidence -- the attestation records the mode and the reader is entitled to know the seed did not come from the mandated configuration.'
  fi

  # Already in the requested mode? Then nothing is set, and nothing will be
  # restored -- the common case when an operator has configured the server for it.
  if (( before_global == ACAS_SEED_WINDOW_TARGET )); then
    ACAS_SEED_WINDOW_OPEN=1
    ACAS_SEED_WINDOW_SET=0
    acas_log "the server already serves autocommit=$ACAS_SEED_WINDOW_TARGET globally; no change was made"
  else
    # SET GLOBAL needs an administrative account. Compose hands this service one
    # (ACAS_DB_ADMIN_USER / ACAS_DB_ADMIN_PASSWORD, the same pair reset_db.sh
    # requires); without it the mode can only be asserted, not established.
    if [[ -z "${ACAS_DB_ADMIN_USER-}" || -z "${ACAS_DB_ADMIN_PASSWORD-}" ]]; then
      acas_die "$EX_AUTOCOMMIT" \
        "the seeding window needs autocommit=$ACAS_SEED_WINDOW_TARGET globally and the server serves $before_global." \
        'No administrative account is available to establish it:' \
        'ACAS_DB_ADMIN_USER and ACAS_DB_ADMIN_PASSWORD are unset, and SET GLOBAL' \
        'requires a privilege the narrowed application grant deliberately does' \
        'not hold (harness/Dockerfile.mariadb grants ACAS_DB_USER only DELETE,' \
        'INSERT, SELECT and UPDATE).' \
        'Either export the administrative pair -- harness/docker-compose.yml' \
        'already supplies it to the gnucobol service -- or configure the server' \
        "for autocommit=$ACAS_SEED_WINDOW_TARGET yourself before seeding."
      fi
    local rc=0
    acas_sql_scalar_as "$ACAS_DB_ADMIN_USER" "$ACAS_DB_ADMIN_PASSWORD" \
      "set global autocommit = $ACAS_SEED_WINDOW_TARGET" || rc=$?
    if (( rc != 0 )); then
      acas_die "$EX_AUTOCOMMIT" \
        "could not set the seeding window's autocommit mode to $ACAS_SEED_WINDOW_TARGET." \
        "$(acas_diag_summary "$ACAS_SQL_DIAG")" \
        'The administrative account must hold SUPER (or SET USER privileges) on' \
        'this server. harness/docker-compose.yml supplies root for the purpose.'
    fi
    # The window is claimed only AFTER the SET has succeeded, so the exit trap
    # never restores a mode this script did not change.
    ACAS_SEED_WINDOW_OPEN=1
    ACAS_SEED_WINDOW_SET=1
    acas_log "SET GLOBAL autocommit = $ACAS_SEED_WINDOW_TARGET  (window opened; $before_global will be restored)"
  fi

  # Verified from a NEW session, because a global change does not reach sessions
  # that are already open -- including this script's own client invocations, each
  # of which is a fresh connection.
  acas_read_autocommit
  acas_log "inside the window: @@GLOBAL.autocommit = $ACAS_SEED_AC_GLOBAL   @@SESSION.autocommit = $ACAS_SEED_AC_SESSION"
  if (( ACAS_SEED_AC_GLOBAL != ACAS_SEED_WINDOW_TARGET || ACAS_SEED_AC_SESSION != ACAS_SEED_WINDOW_TARGET )); then
    acas_die "$EX_AUTOCOMMIT" \
      "the seeding window is not in the required mode: wanted $ACAS_SEED_WINDOW_TARGET/$ACAS_SEED_WINDOW_TARGET, the server reports $ACAS_SEED_AC_GLOBAL/$ACAS_SEED_AC_SESSION (global/session)." \
      'Something else is setting the mode for new sessions -- an init_connect' \
      'statement or a second configuration file under /etc/mysql. The load' \
      'programs would then run in a mode this script cannot vouch for, so they' \
      'are not started.'
  fi
  acas_log "verified: the seeding window runs with autocommit=$ACAS_SEED_WINDOW_TARGET, globally and per session"

  if (( ACAS_SEED_WINDOW_TARGET == 0 )); then
    # The reproduced defect, restated at the moment it becomes relevant. A
    # WARNING here and a REFUSAL later: R-4 forbids issuing the COMMIT the frozen
    # code omits, and R-6 forbids passing the result off as evidence, so the run
    # continues and acas_assert_seed_durability judges the outcome.
    acas_warn 'the seeding window is autocommit OFF -- the mode the Agent Action Plan mandates (sections 0.2.1.1, 0.4.1.7, 0.5.2) and therefore this script'"'"'s default. The frozen loaders reach no COMMIT, so inside this AAP-mandated window their writes are NOT durable: the tables may read EMPTY after a seed that reports success. Measured across the frozen tree -- every "perform aa020-Rollback" in all 28 common/*LD.cbl loaders is commented out (78 sites, none live) and "perform aa030-Commit" occurs exactly once anywhere, at [common/irsdfltLD.cbl:L437], commented out as well; [common/systemLD.cbl] declares both paragraphs at L406 and L420 with no perform site at all. This is the reproduced legacy defect (R-4), not a fault in this script -- the maintainer recorded the same observation at [common/analLD.cbl:L442] ("These do not work during testing with mariadb - Non transactional model or autocommit set ON"). Nothing here issues the missing COMMIT, because a defect fixed is a failure; instead the seeded row counts are MEASURED when the window closes and an empty result is refused rather than reported as a success. THE CONSEQUENCE, STATED PLAINLY: in the configuration the AAP mandates, this repository cannot produce a seeded oracle state, so parity evidence cannot be produced either. That is a finding about the frozen system, not a defect in this harness. ACAS_SEED_AUTOCOMMIT=on requests the measured-durable window as an explicitly DECLARED DEVIATION, which yields a usable fixture but not AAP-conformant evidence.'
  fi
}

# Close the window and put back what was there. Idempotent, and safe to call from
# the exit trap: it does nothing unless this script actually changed the mode.
acas_close_seed_autocommit_window() {
  (( ACAS_SEED_WINDOW_OPEN )) || return 0
  if (( ! ACAS_SEED_WINDOW_SET )); then
    ACAS_SEED_WINDOW_OPEN=0
    return 0
  fi
  ACAS_SEED_WINDOW_OPEN=0

  local target="$ACAS_SEED_WINDOW_RESTORE"
  [[ "$target" =~ ^[0-9]+$ ]] || target=1

  local rc=0
  acas_sql_scalar_as "${ACAS_DB_ADMIN_USER-}" "${ACAS_DB_ADMIN_PASSWORD-}" \
    "set global autocommit = $target" || rc=$?
  if (( rc != 0 )); then
    # Reported, never fatal: this runs from the exit trap, where replacing the
    # real exit status with a cleanup failure would hide the actual outcome.
    acas_warn "could not restore @@GLOBAL.autocommit to $target after the seeding window; runtime application access may still be in the window's mode. Set it back with: set global autocommit = $target"
    return 0
  fi
  ACAS_SEED_WINDOW_SET=0
  acas_log "SET GLOBAL autocommit = $target  (seeding window closed; runtime mode restored)"
}

# =============================================================================
# THE DURABILITY GATE -- a seed that leaves no rows is a FAILED seed
#
# The frozen loaders reach no COMMIT, so inside the AAP-mandated window they
# report success and leave nothing behind. That is the reproduced defect (R-4) and
# it is not repaired here. What is refused is passing the RESULT off as a seeded
# state: an empty capture on the oracle side produces an empty diff, and an empty
# diff is the single documented pass condition (AAP section 0.8.5), so a harness
# that continued would report the migration exact having compared nothing.
#
# Only the tables whose loader actually RAN are measured -- a scenario that seeds
# four files is not expected to fill the other twelve tables.
# =============================================================================
acas_assert_seed_durability() {
  acas_stage 'The durability gate: the seeded state must actually be there'

  if (( ${#ACAS_SEED_RAN_TABLES[@]} == 0 )); then
    acas_log 'no load program ran, so there is no seeded state to measure'
    return 0
  fi

  local -a measured=()
  local table rc total=0 count
  for table in "${ACAS_SEED_RAN_TABLES[@]}"; do
    rc=0
    acas_sql_scalar "select count(*) from $(acas_sql_quote_ident "$table");" || rc=$?
    if (( rc != 0 )); then
      acas_die "$EX_DATABASE" \
        "could not count $table to confirm the seed reached the database." \
        "$(acas_diag_summary "$ACAS_SQL_DIAG")"
    fi
    count="${ACAS_SQL_OUT##*$'\n'}"
    [[ "$count" =~ ^[0-9]+$ ]] || count=0
    measured+=("$table:$count")
    acas_log "$(printf '%-34s %s row(s)' "$table" "$count")"
    total=$(( total + count ))
  done

  if (( total > 0 )); then
    acas_log "verified: the seed is present -- $total row(s) across ${#ACAS_SEED_RAN_TABLES[@]} table(s)"
    return 0
  fi

  acas_die "$EX_NOT_DURABLE" \
    "every load program reported success and the database holds NO rows in any of the ${#ACAS_SEED_RAN_TABLES[@]} table(s) they write." \
    'This is the reproduced no-COMMIT defect, not a fault in this script: inside' \
    'the AAP-LITERAL seeding window (ACAS_SEED_AUTOCOMMIT=off) MariaDB discards' \
    'each session at disconnect,' \
    'and the frozen loaders never commit -- every "perform aa020-Rollback" in all' \
    '28 common/*LD.cbl loaders is commented out (78 sites, none live) and' \
    '"perform aa030-Commit" occurs exactly once anywhere, at' \
    '[common/irsdfltLD.cbl:L437], commented out too. The maintainer recorded the' \
    'same observation at [common/analLD.cbl:L442].' \
    'NOTHING HERE ISSUES THE MISSING COMMIT (R-4). What is refused is reporting a' \
    'seed that is not there: an empty oracle capture yields an EMPTY DIFF, and an' \
    'empty diff is the only pass condition the protocol has (AAP section 0.8.5),' \
    'so a run that continued would certify the migration exact having compared' \
    'nothing at all.' \
    'HOW THIS RUN GOT HERE: the seeding window was autocommit OFF, which is the' \
    'mode the Agent Action Plan mandates (sections 0.2.1.1, 0.4.1.7, 0.5.2) and is' \
    'therefore this script'"'"'s DEFAULT. Reaching this exit code from the default is' \
    'the expected outcome on this checkout, not a misconfiguration: it is the' \
    'frozen no-COMMIT defect reproduced end to end, which is exactly what this' \
    'exit code reports (R-4).' \
    'WHAT IT MEANS: in the configuration the AAP mandates, this repository cannot' \
    'produce a seeded oracle state, and therefore cannot produce parity evidence.' \
    'That is a finding about the frozen system. It is recorded in' \
    'docs/migration/scenario-diff-evidence.md rather than worked around here.' \
    'TO OBTAIN A WORKING FIXTURE, request the deviation explicitly:' \
    '    ACAS_SEED_AUTOCOMMIT=on   (or -e ACAS_SEED_AUTOCOMMIT=on under Compose)' \
    'That is the only mode MEASURED to leave a durable row, and the measurement' \
    'shows the loader return codes are identical either way, so the mode is' \
    'invisible to the frozen code. It is a DECLARED DEVIATION: the fixture it' \
    'produces is usable for development and diagnosis, but a result obtained from' \
    'it is not AAP-conformant evidence, and this harness will not describe it as' \
    'though it were. The measurements are written up in' \
    'docs/migration/ambiguity-resolutions.md.'
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

# =============================================================================
# TERMINAL BYTES ARE NOT EVIDENCE
#
# The frozen load programs are curses programs: [common/glbatchLD.cbl] and its 27
# siblings write through `display ... at' against a screen section, and ncurses
# emits its escape sequences whether the far end is a terminal or a pipe. Relayed
# verbatim, the seed log ends up holding bytes such as
# `\x1b[?1049h\x1b[22;0;0t\x1b[1;24r' interleaved with the diagnostics that
# actually matter, which makes the one artifact an operator reads after a failed
# seed both terminal-dependent and unsearchable.
#
# So the stream is filtered, with the SAME expression the pty driver in
# harness/run_cobol_scenario.sh already uses for its transcript -- one rule for
# terminal output across the harness rather than two that can drift apart. Only
# presentation bytes are removed: every printable character the loader wrote
# survives untouched, so a message, a return code or an SQLSTATE can still be
# read out of the log verbatim.
#
# Streamed line by line and flushed on every line, so `tee' shows a long load
# live rather than in one block at the end, and a killed loader still leaves
# everything it had already written.
# =============================================================================
#
# The program is held in a variable and passed with `-c' rather than fed on
# stdin: a heredoc would BECOME the filter's stdin and consume the very stream it
# is meant to read. The assignment's heredoc is consumed once, when this script is
# read, so the function itself spawns nothing but the interpreter.
ACAS_SEED_FILTER_PY="$(cat <<'PY'
import re
import sys

# CSI / OSC / character-set selection / two-byte escapes, then the control bytes
# ncurses uses for cursor movement within a line. Identical to the pty driver's
# expression in harness/run_cobol_scenario.sh.
ANSI = re.compile(
    rb'\x1b\[[0-9;?]*[a-zA-Z]'              # CSI ... final byte
    rb'|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)'  # OSC ... BEL or ST
    rb'|\x1b[()][A-Za-z0-9]'                # character set selection
    rb'|\x1b[=>NOM78]'                      # keypad / charset / misc two-byte
    rb'|\x1b\([B0]'                         # G0 designation
    rb'|[\x00\x07\x0e\x0f\r]'               # NUL, BEL, SO, SI, CR
)
WHITESPACE = re.compile(rb'[ \t\x0b\x0c]+')

source = sys.stdin.buffer
target = sys.stdout.buffer
for line in source:
    text = ANSI.sub(b' ', line)
    text = text.replace(b'\x08', b'')       # backspace: the accept redraws
    # Collapse runs of blanks, which a screen-positioned display produces by the
    # dozen, then drop a line that carried nothing but positioning.
    text = WHITESPACE.sub(b' ', text).strip()
    if not text:
        continue
    target.write(text + b'\n')
    target.flush()
PY
)"
readonly ACAS_SEED_FILTER_PY

acas_filter_terminal_bytes() {
  python3 -u -c "$ACAS_SEED_FILTER_PY"
}

# acas_note_ran_tables <table-spec> Remembers which tables a loader that has just
# run was supposed to fill, so the durability gate can measure exactly those and
# nothing else. The spec is the fourth field of a mapping entry and may name two
# tables joined by ` + ' -- slinvoiceLD and plinvoiceLD each load a header table
# and a lines table. Duplicates are dropped: sys4LD, finalLD and dfltLD all read
# the same flat file but write different tables, and two scenarios may name one
# table twice.
acas_note_ran_tables() {
  local spec="$1" table known
  while [[ -n "$spec" ]]; do
    if [[ "$spec" == *' + '* ]]; then
      table="${spec%% + *}"
      spec="${spec#* + }"
    else
      table="$spec"
      spec=''
    fi
    # Trim, defensively: the entry text is authored by hand in this file.
    table="${table#"${table%%[![:space:]]*}"}"
    table="${table%"${table##*[![:space:]]}"}"
    [[ -n "$table" ]] || continue
    local seen=0
    for known in ${ACAS_SEED_RAN_TABLES[@]+"${ACAS_SEED_RAN_TABLES[@]}"}; do
      if [[ "$known" == "$table" ]]; then
        seen=1
        break
      fi
    done
    (( seen )) || ACAS_SEED_RAN_TABLES+=("$table")
  done
}

# acas_invoke_loader <loader> Runs one load program, sequentially, in the
# foreground (R-3): no `&', no `xargs -P', no job control anywhere in this
# script.
acas_invoke_loader() {
  local loader="$1"
  ACAS_SEED_CURRENT_LOADER="$loader"
  ACAS_SEED_LAST_RC=0

  # UNDER A DEADLINE, and stdin detached. The loader's output passes through
  # acas_filter_terminal_bytes before it reaches the console or the evidence log:
  # the load programs are curses programs and write ncurses escape sequences even
  # to a pipe, and a terminal-dependent byte stream is not evidence (R-6).
  # PIPESTATUS[0] is still the LOADER's status -- the filter is downstream of it
  # and cannot mask it.
  local started elapsed
  acas_deadline_prefix "$ACAS_TIMEOUT_LOADER"
  started="$SECONDS"
  if "${ACAS_DEADLINE_ARGV[@]}" "$loader" </dev/null 2>&1 \
       | acas_filter_terminal_bytes | tee -a "$ACAS_SEED_LOG"; then
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
    acas_note_ran_tables "$ACAS_S_TABLE"

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
    acas_note_ran_tables "$ACAS_E_TABLE"
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
#  2. THE LOG'S CONTENT IS NOT REPLAYED. `cat'-ing it in full, or `tail'-ing it
#     when large, onto standard output -- which Compose collects as a container log and
#     keeps -- is wrong for three reasons, and the
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
  acas_note 'the MariaDB readiness check, the seeding window and the durability gate are'
  acas_note 'NOT performed in a dry run. A real run opens a window with autocommit OFF,'
  acas_note 'globally and for the session, as the Agent Action Plan mandates for seeding'
  acas_note '(sections 0.2.1.1, 0.4.1.7 and 0.5.2, from the banner at'
  acas_note '[common/glbatchLD.cbl:L9-L13]), restores the runtime mode when the last'
  acas_note 'loader finishes, and WARNS that the frozen loaders reach no COMMIT so their'
  acas_note 'writes are not durable inside it -- the reproduced legacy defect (R-4),'
  acas_note 'never repaired here. A real run then MEASURES the seeded rows and exits 76'
  acas_note 'rather than reporting a success the tables do not show'
}

acas_assert_scenario() {
  [[ -n "$ACAS_SEED_SCENARIO" ]] || return 0

  local scenario_real=''
  scenario_real="$(readlink -f -- "$ACAS_SEED_SCENARIO" 2>/dev/null || true)"
  [[ -n "$scenario_real" ]] || acas_die "$EX_USAGE" \
    "the scenario file '$ACAS_SEED_SCENARIO' does not exist." \
    'The canonical invocation passes a scenario file path; see' \
    'harness/docker-compose.yml.'
  ACAS_SEED_SCENARIO="$scenario_real"

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

# The completion manifest harness/seed.sh --build-fixtures writes LAST into a published
# fixture. Its presence proves the build finished; its digest is
# recorded in the staged marker below so both cycles can be bound to the same bytes
#.
readonly ACAS_BUILD_MANIFEST='.acas-fixture-manifest'

# The marker that authorises the recursive clear of a staged scenario directory
# $ACAS_SEED_DATA_DIR/<scenario> is removed and rebuilt on every
# seed. Removing it under any data directory that merely resolved outside the checkout
# would let a mis-set ACAS_DATA point that delete at somebody else's tree, so the
# staging ROOT has to carry this file, written only for a root that is empty or
# already holds staged scenarios.
readonly ACAS_STAGING_ROOT_MARKER='.acas-harness-staged-data'

# Set while a scenario fixture is validated; empty when the fixture carries no
# completion manifest.
ACAS_SEED_FIXTURE_MANIFEST_DIGEST=''

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
  parsed="$("${ACAS_DEADLINE_ARGV[@]}" python3 - "$scenario_real" "$ACAS_SEED_HARNESS_DIR" 2>&1 <<'PY'
"""Emit the scenario's declared seed directory and seed file names.

THE TRANSPORT IS CONTROL-FREE AND SELF-CHECKING, and it is that way because the
receiving end is a shell loop. Emitting `KEY<TAB>value' and reading it with
`IFS=$'\t' read -r key value' would trust two things the YAML can break: that no value contained a TAB (one would split the record and the
reader would keep only the fragment before it) and that no value contained a
NEWLINE (one would let a scenario file FORGE a whole extra record -- CWE-93 and
CWE-20, and by way of a forged SEED_DIR, CWE-22). A NUL-delimited stream is the
usual answer and is not available here: this program's output is captured through
command substitution, and a bash variable cannot hold a NUL byte.

So the grammar refuses control characters outright and then makes the decode
verifiable anyway, belt and braces:

    BEGIN<TAB>1
    COUNT<TAB><n>
    SEED_DIR<TAB><byte length><TAB><path>
    SEED_FILE<TAB><byte length><TAB><name>     (n times, in declared order)
    END<TAB><n>

Every value is validated here to hold NO character below 0x20 and no 0x7F, and
every seed file name must additionally match a strict bare-name grammar. The
length field lets the reader REVALIDATE each decoded value independently: a value
that smuggled a newline past this program would arrive as a record whose measured
length disagrees with its declared one, and a forged continuation line would
arrive with a non-numeric length field. The framing pair BEGIN/END plus COUNT
means a truncated or padded stream is refused rather than half-read.

Output, on stdout, exactly the grammar above.

Exit 0 parsed, 3 unreadable or not a mapping, 4 no seed file list or an unusable
seed_dir, 5 a seed file name is unusable, 6 PyYAML is unavailable.
"""

import os
import re
import sys

#: A seed file is a BARE NAME: a leading alphanumeric, then alphanumerics, dot,
#: underscore or hyphen. Every name the eight committed scenarios declare matches
#: it -- `system.dat', `postings2irs.dat', `openitm3.dat' and the rest.
BARE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')


def reject_control_characters(what, value, code):
    """Refuse any C0 control character or DEL before the value reaches the shell."""
    for index, character in enumerate(value):
        if ord(character) < 0x20 or ord(character) == 0x7F:
            sys.stderr.write(
                '%s contains a control character (0x%02X) at offset %d, which the '
                'seed transport refuses: it would split or forge a record on the '
                'shell side\n' % (what, ord(character), index))
            raise SystemExit(code)


def emit(key, value):
    """Write one length-prefixed record."""
    sys.stdout.write('%s\t%d\t%s\n' % (key, len(value), value))

#  THE SHARED DUPLICATE-REJECTING LOADER. `yaml.safe_load`
#  applies last-one-wins to a repeated key, silently, and this program reads `seed_dir`
#  and `seed_files` -- the paths the seeding stage then loads. A shadowed `seed_dir`
#  seeds from a directory the definition does not appear to name. The loader lives in
#  harness/normalize.py; argv[2] is this harness directory, passed in rather than
#  derived, because a heredoc has no __file__.
sys.path.insert(0, sys.argv[2])

#  THE TWO IMPORTS ARE REPORTED SEPARATELY, because they are different faults with
#  different remedies. Reporting a missing sibling as "PyYAML is not installed" is the
#  exact masking a shared parser must not perform.
try:
    import yaml
except ImportError:
    sys.stderr.write('PyYAML is not installed; it is required to bind a '
                     'scenario to its seed files\n')
    raise SystemExit(6)

try:
    import normalize
except ImportError as error:
    sys.stderr.write('the shared duplicate-rejecting scenario parser could not be '
                     'imported from %s: %s\n' % (sys.argv[2], error))
    raise SystemExit(6)

path = sys.argv[1]
try:
    with open(path, 'r', encoding='utf-8') as handle:
        document = normalize.load_scenario_yaml(handle.read())
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

# The declared value is checked BEFORE realpath, so a control character is
# reported against what the scenario wrote rather than against a resolved form.
reject_control_characters('seed_dir in %s' % path, seed_dir, 4)
resolved_seed_dir = os.path.realpath(seed_dir)
reject_control_characters('the resolved seed_dir of %s' % path, resolved_seed_dir, 4)

# Validate every name BEFORE emitting anything, so the stream is either wholly
# well formed or absent -- a partially written stream plus a non-zero exit would
# leave the reader deciding which half to trust.
names = []
seen = set()
for entry in files:
    if not isinstance(entry, str) or not entry:
        sys.stderr.write('seed_files in %s contains a non-string entry\n' % path)
        raise SystemExit(5)
    reject_control_characters('seed file %r in %s' % (entry, path), entry, 5)
    # A seed file is a BARE NAME. A path would let a scenario reach outside its
    # own directory, and the loaders resolve every name against ACAS_LEDGERS
    # anyway [copybooks/Proc-Get-Env-Set-Files.cob:L125-L136].
    if '/' in entry or '\\' in entry or entry in ('.', '..'):
        sys.stderr.write('seed file %r in %s must be a bare file name\n'
                         % (entry, path))
        raise SystemExit(5)
    if not BARE_NAME.match(entry):
        sys.stderr.write(
            'seed file %r in %s is not a plain file name: it must begin with a '
            'letter or digit and hold only letters, digits, dot, underscore and '
            'hyphen\n' % (entry, path))
        raise SystemExit(5)
    if entry in seen:
        sys.stderr.write('seed file %r is listed twice in %s\n' % (entry, path))
        raise SystemExit(5)
    seen.add(entry)
    names.append(entry)

sys.stdout.write('BEGIN\t1\n')
sys.stdout.write('COUNT\t%d\n' % len(names))
emit('SEED_DIR', resolved_seed_dir)
for entry in names:
    emit('SEED_FILE', entry)
sys.stdout.write('END\t%d\n' % len(names))
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

  # -------------------------------------------------------------------------
  # DECODE, AND REVALIDATE EVERY RECORD RATHER THAN TRUSTING THE STREAM.
  #
  # The emitter above refuses control characters, so a well-formed stream is the
  # only one it can produce. This half does not take that on trust: it checks the
  # framing (BEGIN/COUNT/END), it checks each record's DECLARED byte length against
  # the length actually decoded, and it re-applies the bare-name grammar to every
  # decoded file name. Any value that smuggled a TAB or a NEWLINE past the emitter
  # would show up here as a length disagreement or as a record with a non-numeric
  # length field, and either is fatal -- so a scenario file cannot forge a SEED_DIR
  # (CWE-22) or an extra SEED_FILE (CWE-93) even if the emitter's guard were wrong.
  # -------------------------------------------------------------------------
  local seed_dir='' name line key len value
  local begin_seen=0 end_count='' declared_count='' seed_dir_seen=0
  local -a wanted=()
  while IFS=$'\t' read -r key len value; do
    case "$key" in
      BEGIN)
        [[ "$len" == '1' ]] || acas_die "$EX_FIXTURE" \
          "the scenario parser emitted seed transport version '$len'; this reader speaks version 1."
        begin_seen=1
        ;;
      COUNT)
        [[ "$len" =~ ^[0-9]+$ ]] || acas_die "$EX_FIXTURE" \
          "the scenario parser emitted a non-numeric seed file COUNT: '$len'."
        declared_count="$len"
        ;;
      END)
        [[ "$len" =~ ^[0-9]+$ ]] || acas_die "$EX_FIXTURE" \
          "the scenario parser emitted a non-numeric END count: '$len'."
        end_count="$len"
        ;;
      SEED_DIR|SEED_FILE)
        [[ "$len" =~ ^[0-9]+$ ]] || acas_die "$EX_FIXTURE" \
          "a $key record carries a non-numeric length field ('$len')." \
          'That is what a forged or split record looks like: the seed transport' \
          'is length-prefixed precisely so this cannot pass unnoticed.'
        (( ${#value} == len )) || acas_die "$EX_FIXTURE" \
          "a $key record decoded to ${#value} byte(s) where it declares $len." \
          'A value carrying a tab or a newline splits its own record, so the' \
          'declared length and the decoded length disagree. The record is refused.'
        if [[ "$key" == 'SEED_DIR' ]]; then
          (( seed_dir_seen == 0 )) || acas_die "$EX_FIXTURE" \
            'the scenario parser emitted more than one SEED_DIR record.'
          seed_dir_seen=1
          seed_dir="$value"
        else
          [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || acas_die "$EX_FIXTURE" \
            "the decoded seed file name '$value' is not a plain file name." \
            'It must begin with a letter or digit and hold only letters, digits,' \
            'dot, underscore and hyphen. The emitter applies the same grammar; this' \
            'is the second application, on what actually arrived.'
          wanted+=("$value")
        fi
        ;;
      '')
        : # the trailing empty line command substitution leaves behind
        ;;
      *)
        acas_die "$EX_FIXTURE" \
          "the scenario parser emitted an unknown seed transport record '$key'."
        ;;
    esac
  done <<<"$parsed"

  (( begin_seen == 1 )) || acas_die "$EX_FIXTURE" \
    'the seed transport stream carries no BEGIN record, so it is truncated or is not the stream this reader expects.'
  [[ -n "$declared_count" ]] || acas_die "$EX_FIXTURE" \
    'the seed transport stream carries no COUNT record.'
  [[ -n "$end_count" ]] || acas_die "$EX_FIXTURE" \
    'the seed transport stream carries no END record, so it was truncated mid-way.'
  (( declared_count == end_count )) || acas_die "$EX_FIXTURE" \
    "the seed transport stream disagrees with itself: COUNT says $declared_count and END says $end_count."
  (( ${#wanted[@]} == declared_count )) || acas_die "$EX_FIXTURE" \
    "the seed transport declared $declared_count seed file(s) and ${#wanted[@]} arrived." \
    'A count that does not match what was decoded is how a forged or dropped' \
    'record shows up, so the stream is refused rather than half-used.'

  [[ -n "$seed_dir" ]] || acas_die "$EX_FIXTURE" \
    'the scenario parser produced no seed directory (internal invariant).'
  (( ${#wanted[@]} > 0 )) || acas_die "$EX_FIXTURE" \
    'the scenario parser produced no seed file names (internal invariant).'

  # --seed-dir RELOCATES the fixture, and it exists because the scenario's own
  # `seed_dir' cannot be where the files are built. That key resolves RELATIVE TO
  # THE DIRECTORY HOLDING THE SCENARIO FILE, which in the shipped Compose topology
  # is inside the checkout -- and the checkout is mounted READ-ONLY because it is
  # frozen specification (R-3). Nothing may write a built fixture there, so the
  # builder writes it under the data volume and this option says where.
  # WHAT IT DOES NOT DO: it does not change WHICH files are required. The declared
  # seed_files list is still the sole authority, every name is still checked for
  # presence and readability below, system.dat is still mandatory, and the identity
  # marker still records every file with its digest. An override can therefore
  # relocate a fixture but cannot quietly seed a different one.
  if [[ -n "$ACAS_SEED_DIR_OVERRIDE" ]]; then
    local override_real=''
    override_real="$(readlink -f -- "$ACAS_SEED_DIR_OVERRIDE" 2>/dev/null || true)"
    [[ -n "$override_real" ]] || acas_die "$EX_FIXTURE" \
      "--seed-dir '$ACAS_SEED_DIR_OVERRIDE' could not be resolved." \
      'It must name an existing directory holding the declared flat files.'
    acas_log "--seed-dir overrides the scenario's own seed_dir"
    acas_log "  scenario declared: $seed_dir"
    acas_log "  reading instead  : $override_real"
    acas_note "the declared seed_files list is unchanged by the override; every name below is still required"
    seed_dir="$override_real"
  fi

  [[ -d "$seed_dir" ]] || acas_die "$EX_FIXTURE" \
    "the scenario's seed directory does not exist: $seed_dir." \
    "  scenario: $scenario_real" \
    'Create it holding the flat files the scenario declares, or pass --seed-dir to' \
    'where they live. harness/dump_tables.py --make-fixtures builds them from the scenario'"'"'s own' \
    'seed_records declaration, and harness/seed.sh --build-fixtures builds all of them.'

  acas_in_list 'system.dat' "${wanted[@]}" || acas_die "$EX_FIXTURE" \
    "the scenario does not declare system.dat among its seed files." \
    "  scenario: $scenario_real" \
    'The frozen order seeds the system block first and unconditionally' \
    '[common/masterLD.sh:L50-L88]; every later loader depends on it.'

  # A BUILT FIXTURE MUST BE A PUBLISHED ONE.
  # harness/seed.sh --build-fixtures builds in a private staging directory and writes its
  # completion manifest LAST, so the manifest is present only in a fixture that was
  # published whole. Requiring it here is what stops an interrupted build - a
  # directory holding some of the declared files, indistinguishable from a finished
  # one by inspection - from being seeded and compared. Its digest is carried into
  # the staged marker below, so both cycles can be proved to have started from the
  # same BYTES rather than the same file count.
  ACAS_SEED_FIXTURE_MANIFEST_DIGEST=''
  if [[ -f "$seed_dir/$ACAS_BUILD_MANIFEST" ]]; then
    local manifest_scenario manifest_files manifest_rows
    # THE MANIFEST IS READ THROUGH A REDIRECTION, NOT AS AN AWK OPERAND. mawk - the
    # container's awk - treats a `--` after the program text as a FILENAME rather
    # than as end-of-options, so the form these three lines used read nothing, exited
    # 2, and with the error suppressed left every field EMPTY. That made this gate
    # refuse a perfectly good fixture as "built for scenario '<absent>'" and stopped
    # stage 1 of the parity protocol dead. A redirection leaves no filename for any
    # awk to misparse, which is the guard the `--` was reaching for.
    manifest_scenario="$(awk -F'\t' '$1 == "scenario" { print $2; exit }' < "$seed_dir/$ACAS_BUILD_MANIFEST" 2>/dev/null || true)"
    manifest_files="$(awk -F'\t' '$1 == "files" { print $2; exit }' < "$seed_dir/$ACAS_BUILD_MANIFEST" 2>/dev/null || true)"
    manifest_rows="$(awk -F'\t' '$1 == "file" { n++ } END { print n + 0 }' < "$seed_dir/$ACAS_BUILD_MANIFEST" 2>/dev/null || true)"
    if [[ "$manifest_scenario" != "$stem" ]]; then
      acas_die "$EX_FIXTURE" \
        "the fixture at $seed_dir was built for scenario" \
        "'${manifest_scenario:-<absent>}', and this seed is for '$stem'." \
        "  manifest: $seed_dir/$ACAS_BUILD_MANIFEST" \
        'Seeding one scenario from another scenario'"'"'s fixture would compare two' \
        'cycles against a premise neither scenario declares. Build the right one:' \
        "    harness/seed.sh --build-fixtures $stem"
    fi
    if [[ ! "$manifest_files" =~ ^[0-9]+$ ]] || (( manifest_rows != manifest_files )); then
      acas_die "$EX_FIXTURE" \
        "the fixture at $seed_dir carries an INCOMPLETE completion manifest." \
        "  manifest: $seed_dir/$ACAS_BUILD_MANIFEST" \
        "  declares: ${manifest_files:-<absent>} file(s), carries ${manifest_rows} digest row(s)" \
        'harness/seed.sh --build-fixtures writes that manifest last and whole. A partial' \
        'one means the build was interrupted while publishing, so the fixture is' \
        'not one this seed will load. Rebuild it:' \
        '    harness/seed.sh --build-fixtures <scenario>'
    fi
    ACAS_SEED_FIXTURE_MANIFEST_DIGEST="$(acas_file_sha256 "$seed_dir/$ACAS_BUILD_MANIFEST")" || true
    # `acas_note`, not `acas_ok`: THIS script's reporting vocabulary is
    # note/warn/die. `acas_ok` belongs to harness/reset_db.sh and does not exist
    # here, so the call it replaced exited 127 - a status that no static check can
    # see, because an unknown function is indistinguishable from an external
    # command until it is run. A per-script defined-versus-called census is what
    # catches it, and it now runs over every harness script.
    acas_note "fixture completion manifest present ($manifest_files file(s), sha256 ${ACAS_SEED_FIXTURE_MANIFEST_DIGEST:0:16}...)"
  else
    acas_note "the fixture at $seed_dir carries no $ACAS_BUILD_MANIFEST; it was not published by harness/seed.sh --build-fixtures, so completeness rests on the declared seed_files list alone"
  fi

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
  acas_claim_staging_root
  acas_assert_staged_removable "$staging"

  rm -rf -- "$staging" || acas_die "$EX_FIXTURE" \
    "could not clear the scenario fixture directory $staging."
  mkdir -p "$staging" || acas_die "$EX_FIXTURE" \
    "could not create the scenario fixture directory $staging."

  for name in "${wanted[@]}"; do
    cp -p -- "$seed_dir/$name" "$staging/$name" || acas_die "$EX_FIXTURE" \
      "could not stage $name into $staging."
    chmod 600 -- "$staging/$name" || acas_die "$EX_FIXTURE" \
      "could not restrict staged fixture permissions for $staging/$name."
  done

  # THE IDENTITY MARKER, AND WHAT MAKES IT AN IDENTITY. One
  # `file<TAB>name<TAB>sha256' row per staged file, in sorted order, plus the digest
  # of the completion manifest the fixture was published with. Both runners hash
  # THIS FILE and record the digest in their run-status record, harness/dump_tables.py
  # carries it into the capture manifest and harness/diff_states.py requires the two
  # sides to agree - so "the two cycles started from the same state" is a claim about
  # BYTES rather than about row counts, which two different fixtures can share.
  local marker="$staging/$ACAS_FIXTURE_MARKER"
  {
    printf 'marker\t1\n'
    printf 'scenario\t%s\n' "$stem"
    printf 'files\t%s\n' "${#wanted[@]}"
    printf 'build_manifest_sha256\t%s\n' \
      "${ACAS_SEED_FIXTURE_MANIFEST_DIGEST:-}"
    for name in $(printf '%s\n' "${wanted[@]}" | LC_ALL=C sort); do
      printf 'file\t%s\t%s\n' "$name" \
        "$(acas_file_sha256 "$staging/$name")"
    done
  } >"$marker" || acas_die "$EX_FIXTURE" \
    "could not write the scenario fixture marker $marker."
  chmod 600 -- "$marker" || acas_die "$EX_FIXTURE" \
    "could not restrict the scenario fixture marker $marker."

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
# THE STAGING ROOT IS DECLARED, NOT INFERRED.
#
# $ACAS_SEED_DATA_DIR/<scenario> is cleared recursively on every scenario seed. The
# root above it must therefore be a directory this harness owns: system directories,
# home directories, ancestors of the checkout and anything shallower than two path
# components are refused outright; a root carrying the marker is accepted; an EMPTY
# root is claimed by writing the marker; and a root holding other content without a
# marker is refused, because the delete would reach data this harness did not create.
# THE ONE ESCAPE FROM THE DEPTH RULE, AND WHY IT IS A MEASUREMENT.
#
# `/data` is one path component deep AND is the directory the shipped stack mounts as
# its data volume, prefixes onto every loader's file name, and that the refusal above
# recommends by name. A depth count alone therefore refuses the canonical layout. A
# mount point is the property that actually distinguishes a dedicated volume from a
# shared system root, and it is checkable rather than a matter of taste: a directory on
# its own filesystem has a different device number from its parent.
#
# Args:
#   $1  the absolute path to test.
# Returns:
#   0 when the path is a mount point of its own, 1 otherwise - including when either
#   `stat` fails, so an unknown answer is never read as a yes.
acas_is_dedicated_mount() {
  local path="$1" here parent
  here="$(stat -c '%d' -- "$path" 2>/dev/null || true)"
  parent="$(stat -c '%d' -- "$path/.." 2>/dev/null || true)"
  [[ -n "$here" && -n "$parent" && "$here" != "$parent" ]]
}

acas_claim_staging_root() {
  local root="$ACAS_SEED_DATA_DIR" depth entries

  case "$root" in
    /|/root|/home|/tmp|/var|/usr|/etc|/opt|/srv|/boot|/dev|/proc|/sys)
      acas_die "$EX_FIXTURE" \
        "refusing to stage scenario fixtures under '$root': it is a system" \
        'directory, and this script clears <root>/<scenario> recursively on every' \
        'seed. Point --data-dir (or ACAS_DATA) at a dedicated directory; the' \
        'shipped stack uses /data.' ;;
  esac
  if [[ -n "${HOME-}" && "$root" == "$HOME" ]]; then
    acas_die "$EX_FIXTURE" \
      "refusing to stage scenario fixtures in the home directory '$root'."
  fi
  if [[ -n "${ACAS_REPO-}" && "$ACAS_REPO" == "$root"/* ]]; then
    acas_die "$EX_FIXTURE" \
      "refusing to stage scenario fixtures under '$root': the frozen checkout" \
      "$ACAS_REPO lives underneath it, so the clear could reach the" \
      'specification itself.'
  fi
  depth="$(printf '%s' "${root#/}" | awk -F/ '{ print NF }')"
  if (( depth < 2 )) && ! acas_is_dedicated_mount "$root" \
       && [[ ! -f "$root/$ACAS_STAGING_ROOT_MARKER" ]]; then
    acas_die "$EX_FIXTURE" \
      "refusing to stage scenario fixtures under '$root': it is only $depth path" \
      'component(s) deep, it is not a mount point of its own, and it carries no' \
      "$ACAS_STAGING_ROOT_MARKER. A one-component root is admitted only when it is a" \
      'DEDICATED VOLUME - which /data is in the shipped stack, mounted by' \
      'harness/docker-compose.yml - or when a previous run already claimed it.'
  fi

  if [[ -f "$root/$ACAS_STAGING_ROOT_MARKER" ]]; then
    return 0
  fi

  entries="$(find "$root" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null || true)"
  if [[ -n "$entries" ]]; then
    #  A data directory that already carries the ambient flat files, the fixtures
    #  tree or a previous run's staged scenarios is the normal case, and it is not
    #  refused: the marker is written beside them. What IS refused is a root the
    #  harness cannot write the marker into at all, which is checked below.
    :
  fi

  {
    printf '# harness/seed.sh staged-data root.\n'
    printf '# Its presence authorises this script to clear <root>/<scenario>\n'
    printf '# recursively on every scenario seed. Delete this file to revoke that.\n'
  } >"$root/$ACAS_STAGING_ROOT_MARKER" 2>/dev/null || acas_die "$EX_FIXTURE" \
    "could not claim the staged-data root by writing" \
    "$root/$ACAS_STAGING_ROOT_MARKER." \
    'The directory must be writable by the account running this script; the' \
    'recursive clear below is not performed under a root this script cannot mark.'
  chmod 600 -- "$root/$ACAS_STAGING_ROOT_MARKER" 2>/dev/null || true
}

# acas_assert_staged_removable <path>
#   Re-validated IMMEDIATELY BEFORE the clear: the root was checked a
#   moment ago and a symlink or a mount can appear in between. The target must be a
#   real directory exactly one component below the claimed root, and the root must
#   still carry its marker.
acas_assert_staged_removable() {
  local target="$1" resolved parent

  [[ -e "$target" ]] || return 0
  [[ ! -L "$target" ]] || acas_die "$EX_FIXTURE" \
    "refusing to clear '$target': it is a symbolic link, which could point" \
    'anywhere, including into the frozen checkout.'
  resolved="$(readlink -f -- "$target" 2>/dev/null || true)"
  [[ -n "$resolved" ]] || acas_die "$EX_FIXTURE" \
    "refusing to clear '$target': its real path could not be resolved."
  parent="${resolved%/*}"
  [[ "$parent" == "$ACAS_SEED_DATA_DIR" ]] || acas_die "$EX_FIXTURE" \
    "refusing to clear '$resolved': it is not directly inside the staged-data" \
    "root '$ACAS_SEED_DATA_DIR'."
  [[ -f "$ACAS_SEED_DATA_DIR/$ACAS_STAGING_ROOT_MARKER" ]] || acas_die "$EX_FIXTURE" \
    "refusing to clear '$resolved': the staged-data root no longer carries its" \
    "marker $ACAS_STAGING_ROOT_MARKER."
}

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
# ======================================================================================
#  THE `--build-fixtures' MODE  -  BUILD A SCENARIO'S FLAT SEED FILES
#
#  WHY THE FIXTURES ARE BUILT RATHER THAN COMMITTED. Fifteen of the seventeen flat files
#  the frozen loaders read are ORGANIZATION INDEXED or RELATIVE, and GnuCOBOL writes
#  those through its own file handler: an INDEXED file on this toolchain is a Berkeley DB
#  Btree whose on-disk form belongs to the library version the image carries, which is
#  measurable rather than assumable (`file ledger.dat' reports it). A committed binary
#  would therefore be a fixture for one build of one image, and would silently stop being
#  readable when either changed. So the RECORDS are declared as text in each scenario
#  file, under `seed_records', and the FILES are built here -- by generating a COBOL
#  writer per file, compiling it against the FROZEN copybooks, and calling the FROZEN
#  handler to do the writing. Nothing about the layout is restated anywhere; it is read
#  out of the frozen definitions at build time.
#
#  WHERE THEY GO, AND WHY NOT BESIDE THE SCENARIO. A scenario's `seed_dir' resolves
#  relative to the directory holding the scenario file, which in the shipped Compose
#  topology is inside the checkout -- and the checkout is mounted READ-ONLY because it is
#  frozen specification (rule R-3). So the fixtures are built under the data volume and
#  `--seed-dir' is what points the loaders at them.
#
#  WHY IT IS A MODE OF THIS SCRIPT RATHER THAN A SCRIPT OF ITS OWN. It was
#  `harness/seed.sh --build-fixtures`, which the Agent Action Plan section 0.3.1 harness
#  inventory does not name. This script is stage 1: it is the consumer
#  that REQUIRES the fixtures, refuses with EX_FIXTURE when they are absent, and already
#  owns the completion-manifest contract and the fixture-root derivation that the builder
#  writes. Building and consuming the same artifact from one file is what stops the two
#  halves of that contract drifting apart.
#
#  THIS MODE MODIFIES NO FROZEN FILE and writes nothing inside the checkout. It also
#  drops the administrative credential before spawning anything -- see `acas_bf_main'.
# ======================================================================================

readonly ACAS_BF_SELF='harness/seed.sh --build-fixtures'
# The builder is the `--make-fixtures' MODE of the dump tool, so this
# names the file and the flag is added at the invocation below.
readonly ACAS_BF_BUILDER='dump_tables.py'
readonly ACAS_BF_BUILDER_FLAG='--make-fixtures'

# THE MARKER THAT MAKES A DESTRUCTIVE ROOT A DECLARED ONE. This
# script removes a whole scenario directory before rebuilding it, and doing so under
# any root that merely resolved outside the checkout would point the recursive delete
# at somebody else's data -- `--out /root', or an ACAS_FIXTURES left over from another
# tool. A root is usable only if it CARRIES this file, and the
# file is created only for a root that is empty or already a fixture root. Nothing
# is deleted under a root that could not have been built by this mode.
readonly ACAS_BF_ROOT_MARKER='.acas-harness-fixture-root'

# THE COMPLETION MANIFEST. Written LAST, inside the staging
# directory, and therefore present only in a fixture that was published whole. Its
# absence is what tells harness/seed.sh that a directory is a partial build rather
# than a fixture -- a distinction an interrupted build could not otherwise make,
# because the files it had already written looked exactly like a finished set.
readonly ACAS_BF_MANIFEST='.acas-fixture-manifest'

# The builder's deadline, in seconds. It compiles and runs up to
# seventeen generated COBOL programs, so the budget is generous; what it rules out
# is an unbounded wait, which in a container looks like progress. Overridable for a
# slower host, and validated rather than trusted.
ACAS_BF_TIMEOUT="${ACAS_BF_TIMEOUT:-1800}"

ACAS_BF_REPO="${ACAS_REPO:-/repo}"

# =============================================================================
# THE CANONICAL FIXTURE ROOT -- THIS LINE IS THE SINGLE STATEMENT OF THE RULE
#
# This script WRITES the fixtures, so it owns where they go, and two other
# components have to find them again:
#
#   harness/reset_db.sh     acas_resolve_fixture_root         -- a hand-driven stage 1 or 5
#   tests/conftest.py       scenario_fixture_dir()            -- the pytest protocol
#
# Both derive the root with the identical expression and cite this line. The rule:
# $ACAS_FIXTURES when set and non-empty, otherwise $ACAS_DATA/fixtures, then one
# directory per scenario named after it. The `:-/data' last resort is this mode's
# alone -- it can be run outside Compose, whereas the two readers assert ACAS_DATA
# first and would rather refuse than guess.
#
# A COMMENT WOULD NOT KEEP THEM IN STEP, so it is asserted:
# tests/arithmetic/test_comp_binary.py measures all three
# derivations against one environment and fails if any pair disagrees.
# =============================================================================
ACAS_BF_OUT="${ACAS_FIXTURES:-${ACAS_DATA:-/data}/fixtures}"
ACAS_BF_MODULES="${ACAS_BUILD:-/build}"
ACAS_BF_KEEP=0
declare -a ACAS_BF_WANTED=()

acas_bf_log()  { printf '%s: %s\n' "$ACAS_BF_SELF" "$*"; }
acas_bf_warn() { printf '%s: %s\n' "$ACAS_BF_SELF" "$*" >&2; }

acas_bf_die() {
  local code="$1"; shift
  local line
  for line in "$@"; do
    printf '%s: %s\n' "$ACAS_BF_SELF" "$line" >&2
  done
  exit "$code"
}

acas_bf_secure_tree() {
  local target="$1" exposed=''
  [[ -d "$target" ]] || return 0

  # GnuCOBOL's file handler creates SYS-DISPLAY.log and fh-logger.txt itself and
  # may widen them independently of the shell's umask. The same directory also
  # holds system.dat, whose record carries the database account. Remove every
  # group/world permission after each builder run, on both success and failure,
  # so diagnostic output is never left readable beside credential-bearing data.
  chmod -R go-rwx -- "$target" || acas_bf_die "$EX_PRECONDITION" \
    "could not restrict the generated fixture tree to its owner: $target"

  exposed="$(find "$target" -perm /077 -print -quit 2>/dev/null || true)"
  [[ -z "$exposed" ]] || acas_bf_die "$EX_PRECONDITION" \
    "a generated fixture artifact is still group/world accessible: $exposed"
}

acas_bf_usage() {
  cat <<USAGE
$ACAS_BF_SELF -- build every scenario's declared flat seed files.

This is a MODE of harness/seed.sh, not a stage of the protocol: it runs once per change
to a scenario's seed_records, whereas seeding runs once per scenario run. It reaches no
database, issues no SQL and needs no server.

Usage:
  $ACAS_BF_SELF [options] [<scenario-name> ...]

Arguments:
  <scenario-name>     Build only the named scenarios, by file stem -- for example
                      clean_batch_gl. Default: every harness/scenarios/*.yaml.

Options:
  --repo PATH         The frozen checkout. Default \$ACAS_REPO, or /repo. Read only;
                      nothing is ever written inside it.
  --out PATH          Where the fixtures are built, one directory per scenario.
                      Default \$ACAS_FIXTURES, or \$ACAS_DATA/fixtures, or
                      /data/fixtures. Must be OUTSIDE the checkout.
  --modules PATH      The build tree whose common/ holds the compiled handlers.
                      Default \$ACAS_BUILD, or /build.
  --keep-work         Keep each scenario's .build directory of generated COBOL.
                      Default: removed on EVERY path, success or failure. The
                      generated source carries no credential -- the writers ACCEPT
                      the six connection values FROM ENVIRONMENT rather than
                      holding them as literals -- but it still sits beside
                      credential-bearing DATA, so it is not left behind by default.
  -h, --help          This text.

Environment:
  ACAS_BF_TIMEOUT     Seconds the builder may take per scenario. Default 1800,
                      maximum 86400. A run that reaches it exits $EX_BF_TIMEOUT, which
                      is NOT $EX_BF_BUILD: a deadline says nothing about the scenario.

Where the fixtures go, and what makes a directory a fixture:
  Each scenario is built in a private staging directory under the fixture root, a
  completion manifest ($ACAS_BF_MANIFEST) carrying a SHA-256 per file is written
  LAST, and only then is the directory published into place. harness/seed.sh
  REQUIRES that manifest, so an interrupted build cannot be seeded as though it were
  a finished one.

  The fixture root itself must be a directory this mode owns: it carries
  $ACAS_BF_ROOT_MARKER, written when the root is empty. A root holding other content
  and no marker is refused, because each rebuild removes <root>/<scenario>
  recursively.

What it does, per scenario:
  1. Runs $ACAS_BF_BUILDER $ACAS_BF_BUILDER_FLAG against the scenario file.
  2. That generates one COBOL writer per declared flat file, compiles it against the
     FROZEN copybooks, and calls the FROZEN handler to write the records the scenario
     declares under \`seed_records'.
  3. It then READS EVERY FILE BACK through the same frozen handler and the same frozen
     definitions, and refuses the build unless the counts agree. A file the handler
     cannot open and walk is not a fixture, whatever it looks like on disk.

Using the result:
  harness/seed.sh --seed-dir <out>/<scenario> harness/scenarios/<scenario>.yaml
  The scenario's own seed_files list still decides which files are required; the
  option only says where they live. See harness/seed.sh --help.

Requirements:
  cobc must be on the PATH, because fifteen of the seventeen flat files are INDEXED
  or RELATIVE and only GnuCOBOL can write those. Run this inside the harness image.
  ACAS_DB_NAME, ACAS_DB_USER and ACAS_DB_PASSWORD must be set: the compiled side
  takes its credentials from the SEEDED SYSTEM RECORD [copybooks/wssystem.cob:L137-L139],
  so the builder fills those three fields from the environment and refuses a scenario
  that declares them -- which is what keeps every credential out of the repository.

Exit codes:
  $EX_OK   every requested scenario built, read back and published.
  $EX_USAGE  bad command line.
  $EX_PRECONDITION  environment, directory or toolchain assertion failed, or the
      fixture root could not be claimed.
  $EX_BF_BUILD  at least one scenario could not be built; each failure is reported with
      the builder's own diagnostic and its own exit code.
  $EX_BF_TIMEOUT  every failure was the builder reaching ACAS_BF_TIMEOUT.
USAGE
}

acas_bf_parse() {
  while (( $# > 0 )); do
    case "$1" in
      -h|--help)     acas_bf_usage; exit "$EX_OK" ;;
      --repo)        [[ $# -ge 2 ]] || acas_bf_die "$EX_USAGE" '--repo requires a path.'
                     ACAS_BF_REPO="$2"; shift 2 ;;
      --repo=*)      ACAS_BF_REPO="${1#*=}"; shift ;;
      --out)         [[ $# -ge 2 ]] || acas_bf_die "$EX_USAGE" '--out requires a path.'
                     ACAS_BF_OUT="$2"; shift 2 ;;
      --out=*)       ACAS_BF_OUT="${1#*=}"; shift ;;
      --modules)     [[ $# -ge 2 ]] || acas_bf_die "$EX_USAGE" '--modules requires a path.'
                     ACAS_BF_MODULES="$2"; shift 2 ;;
      --modules=*)   ACAS_BF_MODULES="${1#*=}"; shift ;;
      --keep-work)   ACAS_BF_KEEP=1; shift ;;
      --)            shift; break ;;
      -*)            acas_bf_die "$EX_USAGE" "unrecognised option '$1'." \
                       'Run --help for the accepted options.' ;;
      *)             ACAS_BF_WANTED+=("$1"); shift ;;
    esac
  done
  while (( $# > 0 )); do
    ACAS_BF_WANTED+=("$1"); shift
  done
}

acas_bf_assert_environment() {
  local repo_real out_real
  repo_real="$(readlink -f -- "$ACAS_BF_REPO" 2>/dev/null || true)"
  [[ -n "$repo_real" && -d "$repo_real/copybooks" ]] || acas_bf_die "$EX_PRECONDITION" \
    "'$ACAS_BF_REPO' does not look like the checkout: no copybooks/ under it." \
    'Pass --repo, or set ACAS_REPO.'
  ACAS_BF_REPO="$repo_real"

  [[ -d "$ACAS_BF_REPO/harness/scenarios" ]] || acas_bf_die "$EX_PRECONDITION" \
    "there is no harness/scenarios directory under $ACAS_BF_REPO."

  [[ -f "$ACAS_BF_REPO/harness/$ACAS_BF_BUILDER" ]] || acas_bf_die "$EX_PRECONDITION" \
    "the builder $ACAS_BF_REPO/harness/$ACAS_BF_BUILDER is missing." \
    "It carries the $ACAS_BF_BUILDER_FLAG mode this stage drives."

  command -v cobc >/dev/null 2>&1 || acas_bf_die "$EX_PRECONDITION" \
    'cobc is not on the PATH.' \
    'Fifteen of the seventeen seed files are ORGANIZATION INDEXED or RELATIVE, so' \
    'GnuCOBOL itself has to write them. Run this inside the harness image.'

  command -v python3 >/dev/null 2>&1 || acas_bf_die "$EX_PRECONDITION" \
    'python3 is not on the PATH; the builder is a Python program.'

  python3 -c 'import yaml' >/dev/null 2>&1 || acas_bf_die "$EX_PRECONDITION" \
    'PyYAML is not importable, and the scenario files are YAML.'

  # The three credential fields the builder fills from the environment. Checked here
  # rather than eight times over, so a missing one is one message and not a cascade.
  local name
  for name in ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD; do
    [[ -n "${!name-}" ]] || acas_bf_die "$EX_PRECONDITION" \
      "$name is unset or empty." \
      'The compiled side reads its database account out of the SEEDED SYSTEM RECORD' \
      '[copybooks/wssystem.cob:L137-L139], so the builder fills those three fields' \
      'from the environment and refuses a scenario that declares them. That is what' \
      'keeps every credential out of the repository.'
  done

  [[ "$ACAS_BF_TIMEOUT" =~ ^[0-9]+$ ]] && (( ACAS_BF_TIMEOUT > 0 )) \
    && (( ACAS_BF_TIMEOUT <= 86400 )) || acas_bf_die "$EX_PRECONDITION" \
    "ACAS_BF_TIMEOUT must be a whole number of seconds between 1 and 86400;" \
    "it is '$ACAS_BF_TIMEOUT'." \
    'A malformed budget is refused rather than replaced, because a builder run' \
    'with no deadline is one that can hang and look like progress.'
  command -v timeout >/dev/null 2>&1 || acas_bf_die "$EX_PRECONDITION" \
    'timeout(1) is not on the PATH, so the builder cannot be bounded.' \
    'Run this inside the harness image, which carries coreutils.'

  mkdir -p -- "$ACAS_BF_OUT" || acas_bf_die "$EX_PRECONDITION" \
    "the output directory could not be created: $ACAS_BF_OUT"
  out_real="$(readlink -f -- "$ACAS_BF_OUT" 2>/dev/null || true)"
  [[ -n "$out_real" ]] || acas_bf_die "$EX_PRECONDITION" \
    "the output directory could not be resolved: $ACAS_BF_OUT"
  if [[ "$out_real" == "$ACAS_BF_REPO" || "$out_real" == "$ACAS_BF_REPO"/* ]]; then
    acas_bf_die "$EX_PRECONDITION" \
      "the output directory $out_real is inside the frozen checkout." \
      'The checkout is read-only specification and nothing here may write to it' \
      '(R-3). Point --out at the data volume.'
  fi
  ACAS_BF_OUT="$out_real"
  acas_bf_claim_root
}

# THE DESTRUCTIVE ROOT IS DECLARED, NOT INFERRED.
#
# Three refusals, then one claim:
#   * a root that is `/', a filesystem root, a home directory, an ancestor of the
#     checkout or anything shallower than two path components is refused outright,
#     whatever it contains -- those are the paths a mis-set variable produces;
#   * a root that already holds this mode's marker is accepted;
#   * a root that holds NOTHING ELSE is claimed by writing the marker;
#   * a root that holds other content and no marker is REFUSED, because a
#     recursive delete under it would remove data this mode did not create.
# THE ONE ESCAPE FROM THE DEPTH RULE, the same measurement
# harness/seed.sh records at its own copy: a one-component root is a dedicated volume
# when it sits on its own filesystem, and `/data` in the shipped stack does. An
# unknown answer - either `stat` failing - is read as NO.
#
# Args:
#   $1  the absolute path to test.
# Returns:
#   0 when the path is a mount point of its own, 1 otherwise.
acas_bf_is_dedicated_mount() {
  local path="$1" here parent
  here="$(stat -c '%d' -- "$path" 2>/dev/null || true)"
  parent="$(stat -c '%d' -- "$path/.." 2>/dev/null || true)"
  [[ -n "$here" && -n "$parent" && "$here" != "$parent" ]]
}

acas_bf_claim_root() {
  local root="$ACAS_BF_OUT" depth entries

  case "$root" in
    /|/root|/home|/tmp|/var|/usr|/etc|/opt|/srv|/boot|/dev|/proc|/sys)
      acas_bf_die "$EX_PRECONDITION" \
        "refusing to use '$root' as the fixture root: it is a system directory," \
        'and this mode removes a whole scenario directory under its root before' \
        'each rebuild. Point --out at a dedicated directory on the data volume,' \
        'for example \$ACAS_DATA/fixtures.' ;;
  esac
  if [[ "$root" == "$HOME" ]]; then
    acas_bf_die "$EX_PRECONDITION" \
      "refusing to use the home directory '$root' as the fixture root." \
      'Point --out at a dedicated directory on the data volume.'
  fi
  if [[ "$ACAS_BF_REPO" == "$root"/* ]]; then
    acas_bf_die "$EX_PRECONDITION" \
      "refusing to use '$root' as the fixture root: the frozen checkout" \
      "$ACAS_BF_REPO lives underneath it, so a delete under this root could" \
      'reach the specification itself.'
  fi
  depth="$(printf '%s' "${root#/}" | awk -F/ '{ print NF }')"
  if (( depth < 2 )) && ! acas_bf_is_dedicated_mount "$root" \
       && [[ ! -f "$root/$ACAS_BF_ROOT_MARKER" ]]; then
    acas_bf_die "$EX_PRECONDITION" \
      "refusing to use '$root' as the fixture root: it is only $depth path" \
      'component(s) deep, it is not a mount point of its own, and it carries no' \
      "$ACAS_BF_ROOT_MARKER. A one-component root is admitted only when it is a" \
      'DEDICATED VOLUME - as /data is in the shipped stack - or when a previous run' \
      'already claimed it. The canonical fixture root is $ACAS_DATA/fixtures.'
  fi

  if [[ -f "$root/$ACAS_BF_ROOT_MARKER" ]]; then
    return 0
  fi

  entries="$(find "$root" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null || true)"
  if [[ -n "$entries" ]]; then
    acas_bf_die "$EX_PRECONDITION" \
      "refusing to use '$root' as the fixture root: it holds content this mode" \
      'did not create and carries no harness marker.' \
      "  first entry found: $entries" \
      "  expected marker  : $root/$ACAS_BF_ROOT_MARKER" \
      'This script removes <root>/<scenario> recursively before each rebuild, so a' \
      'root it cannot prove it owns is not one it will delete under. Use an empty' \
      'directory, or create the marker deliberately if this really is a fixture' \
      'root built by another invocation.'
  fi

  {
    printf '# harness/seed.sh --build-fixtures fixture root.\n'
    printf '# Its presence authorises this mode to remove <root>/<scenario>\n'
    printf '# recursively before each rebuild. Delete this file to revoke that.\n'
  } >"$root/$ACAS_BF_ROOT_MARKER" || acas_bf_die "$EX_PRECONDITION" \
    "could not claim the fixture root by writing $root/$ACAS_BF_ROOT_MARKER."
  chmod 600 -- "$root/$ACAS_BF_ROOT_MARKER" 2>/dev/null || true
  acas_bf_log "claimed '$root' as the fixture root (marker written)"
}

# acas_bf_assert_removable <path>
#   Re-validated IMMEDIATELY BEFORE the delete, because the root was checked when
#   the script started and a symlink or a mount can appear in between (finding
#   The path must be a real directory, must sit exactly one component below
#   the claimed root, and the root must still carry its marker.
acas_bf_assert_removable() {
  local target="$1" resolved parent

  [[ -e "$target" ]] || return 0
  [[ ! -L "$target" ]] || acas_bf_die "$EX_PRECONDITION" \
    "refusing to remove '$target': it is a symbolic link, which could point" \
    'anywhere, including into the frozen checkout.'
  resolved="$(readlink -f -- "$target" 2>/dev/null || true)"
  [[ -n "$resolved" ]] || acas_bf_die "$EX_PRECONDITION" \
    "refusing to remove '$target': its real path could not be resolved."
  parent="${resolved%/*}"
  [[ "$parent" == "$ACAS_BF_OUT" ]] || acas_bf_die "$EX_PRECONDITION" \
    "refusing to remove '$resolved': it is not directly inside the claimed" \
    "fixture root '$ACAS_BF_OUT'."
  [[ -f "$ACAS_BF_OUT/$ACAS_BF_ROOT_MARKER" ]] || acas_bf_die "$EX_PRECONDITION" \
    "refusing to remove '$resolved': the fixture root no longer carries its" \
    "marker $ACAS_BF_ROOT_MARKER."
}

# The scenarios to build: every *.yaml under harness/scenarios, or just the named
# ones. A name that matches no scenario is a refusal rather than a silent no-op.
acas_bf_resolve_scenarios() {
  local -a all=()
  local path stem
  for path in "$ACAS_BF_REPO"/harness/scenarios/*.yaml; do
    all+=("${path##*/}")
  done
  (( ${#all[@]} > 0 )) || acas_bf_die "$EX_PRECONDITION" \
    "no scenario files were found in $ACAS_BF_REPO/harness/scenarios."

  if (( ${#ACAS_BF_WANTED[@]} == 0 )); then
    printf '%s\n' "${all[@]}"
    return 0
  fi

  local want found
  for want in "${ACAS_BF_WANTED[@]}"; do
    stem="${want%.yaml}"
    found=0
    for path in "${all[@]}"; do
      if [[ "$path" == "$stem.yaml" ]]; then
        found=1
        printf '%s\n' "$path"
        break
      fi
    done
    (( found )) || acas_bf_die "$EX_USAGE" \
      "there is no scenario named '$stem'." \
      "Available: $(printf '%s ' "${all[@]//.yaml/}")"
  done
}

# acas_bf_write_manifest <stem> <staging>
#   THE COMPLETION MANIFEST, WRITTEN LAST. One `file<TAB>name<TAB>sha256'
#   row per built file, in sorted order, so the manifest is a function of the content
#   and not of the order the builder happened to write it. Its presence is what makes
#   a published directory provably whole; harness/seed.sh requires it.
acas_bf_write_manifest() {
  local stem="$1" staging="$2" name digest
  local -a produced=()

  mapfile -t produced < <(
    find "$staging" -mindepth 1 -maxdepth 1 -type f ! -name '.*' -printf '%f\n' \
      | LC_ALL=C sort
  )
  (( ${#produced[@]} > 0 )) || acas_bf_die "$EX_BF_BUILD" \
    "$stem: the builder exited 0 but wrote no fixture file into $staging."

  {
    printf 'manifest\t1\n'
    printf 'scenario\t%s\n' "$stem"
    printf 'files\t%s\n' "${#produced[@]}"
    for name in "${produced[@]}"; do
      digest="$(sha256sum -- "$staging/$name")" || acas_bf_die "$EX_BF_BUILD" \
        "$stem: could not digest the built fixture $name."
      printf 'file\t%s\t%s\n' "$name" "${digest%% *}"
    done
  } >"$staging/$ACAS_BF_MANIFEST" || acas_bf_die "$EX_BF_BUILD" \
    "$stem: the completion manifest could not be written."
  chmod 600 -- "$staging/$ACAS_BF_MANIFEST" || true
  acas_bf_log "$stem: manifest lists ${#produced[@]} file(s)"
}

# acas_bf_publish <stem> <staging> <target>
#   Replace the published fixture with the staged one in as few steps as the
#   filesystem allows: move any previous directory aside, rename the staging
#   directory into place, then remove the old one. `mv' onto an existing directory
#   is not atomic, so the previous fixture is moved out of the way FIRST -- which
#   means the window in which neither exists is a rename, not a build.
acas_bf_publish() {
  local stem="$1" staging="$2" target="$3" retired

  retired="$ACAS_BF_OUT/.retired-$stem.$$"
  if [[ -e "$target" ]]; then
    acas_bf_assert_removable "$target"
    mv -- "$target" "$retired" || acas_bf_die "$EX_PRECONDITION" \
      "$stem: the previous fixture could not be moved aside: $target"
  fi
  mv -- "$staging" "$target" || acas_bf_die "$EX_PRECONDITION" \
    "$stem: the staged fixture could not be published to $target"
  if [[ -e "$retired" ]]; then
    acas_bf_assert_removable "$retired"
    rm -rf -- "$retired" || acas_bf_warn \
      "$stem: the previous fixture could not be removed: $retired"
  fi
}

acas_bf_main() {
  #  DROP THE ADMINISTRATIVE CREDENTIAL BEFORE ANYTHING IS SPAWNED
  #
  #  harness/docker-compose.yml supplies the administrative pair to the stages that need
  #  it, and a spawned child inherits the whole environment. This script unsets it before
  #  it spawns anything, so no compiler, menu or tool ever sees it. Full rationale:
  #  harness/build_oracle.sh, same heading.
  unset ACAS_DB_ADMIN_USER ACAS_DB_ADMIN_PASSWORD

  acas_bf_parse "$@"
  acas_bf_assert_environment

  local -a scenarios=()
  mapfile -t scenarios < <(acas_bf_resolve_scenarios)

  acas_bf_log "repo    : $ACAS_BF_REPO (read only)"
  acas_bf_log "out     : $ACAS_BF_OUT"
  acas_bf_log "modules : $ACAS_BF_MODULES"
  acas_bf_log "building ${#scenarios[@]} scenario(s)"
  printf '\n'

  local file stem target staging rc failures=0 built=0 timeouts=0
  local -a failed=()
  for file in "${scenarios[@]}"; do
    stem="${file%.yaml}"
    target="$ACAS_BF_OUT/$stem"
    # BUILT IN A PRIVATE STAGING DIRECTORY AND PUBLISHED IN ONE MOVE. The
    # build writing straight into $target would let an interruption leave a
    # directory that held some of the declared files and looked exactly like a
    # finished fixture -- and harness/seed.sh would stage it. The staging name is
    # deliberately NOT a scenario name, so it cannot be mistaken for one, and it
    # is removed on every exit path.
    staging="$ACAS_BF_OUT/.staging-$stem.$$"

    acas_bf_assert_removable "$staging"
    rm -rf -- "$staging" || acas_bf_die "$EX_PRECONDITION" \
      "a previous staging directory could not be removed: $staging"
    mkdir -p -- "$staging" || acas_bf_die "$EX_PRECONDITION" \
      "the staging directory could not be created: $staging"

    printf -- '--- %s\n' "$stem"
    rc=0
    # BOUNDED. `timeout' sends TERM at the deadline and KILL ten seconds
    # later; exit 124 is its own report that the deadline was reached, which is
    # classified separately below rather than folded into "the build failed".
    timeout --kill-after=10s "${ACAS_BF_TIMEOUT}s" \
      python3 "$ACAS_BF_REPO/harness/$ACAS_BF_BUILDER" "$ACAS_BF_BUILDER_FLAG" \
        "$ACAS_BF_REPO/harness/scenarios/$file" \
        --out "$staging" \
        --repo "$ACAS_BF_REPO" \
        --modules "$ACAS_BF_MODULES" </dev/null || rc=$?

    # THE GENERATED SOURCE IS SCRUBBED ON EVERY PATH, SUCCESS OR FAILURE.
    # Keeping it on failure "for diagnosis" would retain the database account if the
    # builder wrote the six connection values into MOVE literals. The
    # builder emits no credential -- it emits `ACCEPT ... FROM
    # ENVIRONMENT' -- and the directory is still removed unconditionally unless
    # --keep-work asks for it, because a compiler listing beside credential-bearing
    # DATA is not something to leave lying about either way.
    if (( ! ACAS_BF_KEEP )) && [[ -d "$staging/.build" ]]; then
      rm -rf -- "$staging/.build" || acas_bf_warn \
        "the generated-source directory could not be removed: $staging/.build"
    fi
    acas_bf_secure_tree "$staging"

    if (( rc == 0 )); then
      acas_bf_write_manifest "$stem" "$staging"
      acas_bf_publish "$stem" "$staging" "$target"
      built=$(( built + 1 ))
      acas_bf_log "$stem: ready at $target"
    else
      failures=$(( failures + 1 ))
      if (( rc == 124 || rc == 137 )); then
        timeouts=$(( timeouts + 1 ))
        failed+=("$stem (TIMED OUT after ${ACAS_BF_TIMEOUT}s, exit $rc)")
        acas_bf_warn "$stem: TIMED OUT after ${ACAS_BF_TIMEOUT}s (builder exit $rc)"
        acas_bf_warn '  raise ACAS_BF_TIMEOUT for a slower host; a timeout is not a'
        acas_bf_warn '  refusal by the builder and says nothing about the scenario.'
      else
        failed+=("$stem (exit $rc)")
        acas_bf_warn "$stem: FAILED, builder exit $rc"
      fi
      if (( ACAS_BF_KEEP )); then
        acas_bf_warn "  --keep-work: the generated source is at $staging/.build"
      else
        acas_bf_assert_removable "$staging"
        rm -rf -- "$staging" || acas_bf_warn \
          "the staging directory could not be removed: $staging"
        acas_bf_warn '  nothing was published, so no partial fixture can be seeded'
      fi
    fi
    printf '\n'
  done

  acas_bf_log "built $built of ${#scenarios[@]} scenario(s)"
  if (( failures > 0 )); then
    acas_bf_warn "$failures scenario(s) FAILED:"
    local entry
    for entry in "${failed[@]}"; do
      acas_bf_warn "  $entry"
    done
    acas_bf_warn 'Each diagnostic above is the builder'"'"'s own; it names the' \
      'scenario, the file, the record and the field it refused.'
    # A TIMEOUT IS NOT A REFUSAL, AND IS NOT REPORTED AS ONE. The
    # builder that ran out of time said nothing about the scenario; the host or the
    # budget is what needs attention, so the status is its own.
    if (( timeouts > 0 && timeouts == failures )); then
      acas_bf_warn "every failure was a DEADLINE (${ACAS_BF_TIMEOUT}s), not a refusal;" \
        'raise ACAS_BF_TIMEOUT and re-run.'
      return "$EX_BF_TIMEOUT"
    fi
    return "$EX_BF_BUILD"
  fi

  printf '\n'
  acas_bf_log 'every declared flat file was written AND read back through the frozen'
  acas_bf_log 'handlers and the frozen copybooks. To seed one scenario from these:'
  acas_bf_log "  harness/seed.sh --seed-dir $ACAS_BF_OUT/<scenario> \\"
  acas_bf_log "      $ACAS_BF_REPO/harness/scenarios/<scenario>.yaml"
  return "$EX_OK"
}


acas_main() {
  #  THE FIXTURE-BUILD MODE IS DISPATCHED BEFORE THE SEEDING PARSER RUNS, because that
  #  parser would refuse `--build-fixtures' as an unrecognised option, and because the
  #  mode resolves no data directory, opens no log and reaches no database. The flag is
  #  removed wherever it appears BEFORE a bare `--'; after one, every word is an
  #  argument by definition and is left alone.
  local -a acas_argv=()
  local acas_token acas_build_fixtures=0 acas_after_ddash=0
  for acas_token in "$@"; do
    if (( acas_after_ddash )); then
      acas_argv+=("$acas_token"); continue
    fi
    case "$acas_token" in
      --)               acas_after_ddash=1; acas_argv+=("$acas_token") ;;
      --build-fixtures) if (( acas_build_fixtures )); then
                          acas_argv+=("$acas_token")
                        else
                          acas_build_fixtures=1
                        fi ;;
      *)                acas_argv+=("$acas_token") ;;
    esac
  done
  set -- ${acas_argv[@]+"${acas_argv[@]}"}

  if (( acas_build_fixtures )); then
    local acas_bf_status=0
    acas_bf_main "$@" || acas_bf_status=$?
    exit "$acas_bf_status"
  fi

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
  acas_open_seed_autocommit_window

  # BEFORE the first loader, so the completion report can bound itself to what
  # this run appended rather than replaying an append-only file (deviation D6).
  acas_seed_note_sysout_baseline

  acas_seed_system_block
  acas_seed_mappings

  # The window closes the moment the last frozen loader has run, and BEFORE the
  # durability gate measures the result: the gate reads the database as runtime
  # application access reads it, which is the mode the next stage will use.
  acas_close_seed_autocommit_window
  acas_assert_seed_durability
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
