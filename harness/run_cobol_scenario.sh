#!/usr/bin/env bash
# harness/run_cobol_scenario.sh -- stage 2 of the parity protocol: drive the
# COMPILED Cobol posting cycle for one scenario with the same logical inputs the
# menus supply. Run `--help' for the options and the exit codes.
#
# Its output is not a result to be judged; it IS the behavioural specification.
# Nothing here decides whether the Cobol did the right thing --
# harness/diff_states.py does that. This script drives, asserts its own
# preconditions, observes and records.
#
# WHY IT DRIVES THE MENU EXECUTABLES RATHER THAN THE POSTING PROGRAMS. None of
# the twelve in-scope programs is a main program: each is a CALLed sub-program
# whose PROCEDURE DIVISION USING list is made of GROUP ITEMS, in three linkage
# shapes -- General Ledger 4 parameters [general/gl070.cbl:L245-L248], Sales and
# Purchase 5 [sales/sl060.cbl:L395-L399], IRS 3 with no run date and no
# calling-data block [irs/irs030.cbl:L552-L554]. `cobcrun' can pass only string
# arguments, and the posting programs are compiled `-m' as loadable modules
# rather than `-x' executables, so no shell can invoke them directly. The four
# menu executables are what construct those blocks and CALL the sub-programs.
# Writing a new Cobol driver was rejected: the Cobol tree is frozen (R-1, R-4).
#
# Exactly one scenario runs at a time -- no `&', no `xargs -P' (R-3) -- and
# nothing is ever written under $ACAS_REPO.

set -Eeuo pipefail
IFS=$'\n\t'
shopt -s nullglob
umask 077

#  DROP THE ADMINISTRATIVE CREDENTIAL BEFORE ANYTHING IS SPAWNED
#
#  harness/docker-compose.yml supplies the administrative pair to the stages that need
#  it, and a spawned child inherits the whole environment. This script unsets it before
#  it spawns anything, so no compiler, menu or tool ever sees it. Full rationale:
#  harness/build_oracle.sh, same heading.
unset ACAS_DB_ADMIN_USER ACAS_DB_ADMIN_PASSWORD

readonly EX_OK=0
readonly EX_USAGE=70
readonly EX_PRECONDITION=71
readonly EX_DATABASE=72
readonly EX_AUTOCOMMIT=73  # autocommit is not ON -- i.e. the seeding window
                           # harness/seed.sh owns is still open
readonly EX_ORACLE=74      # a compiled artifact is missing -> build_oracle.sh
readonly EX_SCENARIO=75    # the scenario file is missing or malformed
readonly EX_DRIVE=76       # the pty driver timed out, spun, or hit a refusal
readonly EX_ASSERT=77      # a post-run assertion failed
readonly EX_TIMEOUT=78     # an external command exceeded its finite deadline
readonly EX_CAPACITY=79    # the fh-logger budget cannot be met -> refuse to run
readonly EX_TARGET=90      # the target is not a proven harness-owned disposable database


# No external command may run without an upper bound. The pty driver already
# enforces a PER-PROMPT timeout inside itself, and that is not the same
# guarantee.
readonly ACAS_TIMEOUT_MAX=86400          # 24h, an upper bound on any one budget
ACAS_TIMEOUT_GRACE="${ACAS_TIMEOUT_GRACE-}"    # seconds between TERM and KILL
ACAS_TIMEOUT_CLIENT="${ACAS_TIMEOUT_CLIENT-}"  # one database client invocation
ACAS_TIMEOUT_DRIVE="${ACAS_TIMEOUT_DRIVE-}"    # the whole pty driver process
ACAS_TIMEOUT_ROTATE="${ACAS_TIMEOUT_ROTATE-}"  # one fh-logger rotation move
ACAS_TIMEOUT_RESOLVED=''                 # out-parameter of acas_timeout_seconds

# Free space reserved for the frozen file-handler log. Declared with the same
# "${VAR-}" form as the deadlines so that an operator-supplied value survives.
ACAS_FH_LOG_BUDGET_MB="${ACAS_FH_LOG_BUDGET_MB-}"
readonly ACAS_RUN_FH_BUDGET_DEFAULT_MB=1024
ACAS_RUN_FH_BUDGET_MB=0                  # frozen by acas_resolve_deadlines
declare -a ACAS_DEADLINE_ARGV=()         # the resolved `timeout ...' prefix

# Identical wording to harness/seed.sh so the two stages cannot drift.
# ACAS_DB_SOCKET is DECLARED but may be empty: the harness connects over TCP.
readonly -a ACAS_RUN_REQUIRED_ENV_NONEMPTY=(
  ACAS_REPO ACAS_BUILD ACAS_DATA ACAS_OUT
  ACAS_DB_HOST ACAS_DB_PORT ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD
  ACAS_LEDGERS ACAS_BIN
)
readonly -a ACAS_RUN_REQUIRED_ENV_DECLARED=(
  ACAS_DB_SOCKET
)

readonly ACAS_RUN_REQUIRED_SCHEMA='ACASDB'

# ---------------------------------------------------------------------------
#  WHAT PROVES THIS TARGET IS THROWAWAY.
#
#  Driving the compiled posting cycle POSTS. It rewrites nominal balances, stamps
#  batches cleared, writes posting rows and -- when a scenario answers the IRS
#  end-of-job question with `Y' -- performs acas008-Open-Output, which DELETES EVERY
#  ROW of PSIRSPOST-REC [common/acas008.cbl:L313-L319]. Until now the only thing
#  standing between that and somebody's real ledger was the schema NAME being
#  `ACASDB', and the frozen dump gives every ACAS installation in existence exactly
#  that name [mysql/ACASDB.sql]. A name shared with every real installation is not a
#  distinction, so this script could be pointed at a production ACAS database and
#  would post into it without a word.
#
#  The proof is the one harness/reset_db.sh already relies on and is deliberately
#  IDENTICAL to it, down to the variable and the marker text: a SERVER SETTING that
#  harness/Dockerfile.mariadb writes into the server's own configuration. A stock
#  MariaDB leaves `report_host' empty and this server is nobody's replica, so the
#  setting has no other effect and can be read back with one query. It cannot be
#  faked by a client, cannot be set per session, and is absent from every server the
#  harness did not build.
#
#  NOT a table and NOT a schema object: rule R-3 admits no added DDL, so a gate that
#  needed one would make the violation load-bearing.
#
#  The escape hatch is deliberately target-SCOPED. An acknowledgement names the exact
#  `user@host:port/schema' it authorises, so one left in an environment cannot later
#  authorise a different database -- the failure mode a bare
#  ACAS_..._ACKNOWLEDGE=1 would have. On a PROTOCOL-BOUND run the acknowledgement is
#  refused outright -- see acas_assert_no_evidence_bypass -- because evidence
#  production may not be aimed by hand.
# ---------------------------------------------------------------------------
readonly ACAS_RUN_DISPOSABLE_MARKER='ACAS-harness-disposable-oracle'
readonly ACAS_RUN_DISPOSABLE_VARIABLE='report_host'


readonly ACAS_RUN_ROWS=24
readonly ACAS_RUN_COLS=80

# The seven operation names. These MUST stay identical to the set the
# Python-side scenario runner is to accept, so the two runners are trivially
# comparable.
readonly -a ACAS_RUN_OPERATIONS=(
  gl_post_cycle
  gl_end_of_cycle
  sl_invoice_post
  sl_cash_post
  pl_order_post
  pl_payment_post
  irs_post
)

readonly -a ACAS_RUN_SUBSYSTEMS=(general sales purchase irs)

# operation:subsystem:menu-key:paragraph:locator The menu key is NOT guessed.
# Each menu accepts one character and resolves it to a paragraph by ordinal.

readonly -a ACAS_RUN_OPERATION_MAP=(
  'gl_post_cycle:general:H:load08:general/general.cbl:L805-L815'
  'gl_end_of_cycle:general:I:load09:general/general.cbl:L817-L821'
  'sl_invoice_post:sales:G:load07:sales/sales.cbl:L756-L768'
  'sl_cash_post:sales:K:load11:sales/sales.cbl:L792-L796'
  'pl_order_post:purchase:H:load08:purchase/purchase.cbl:L752-L762'
  'pl_payment_post:purchase:L:load12:purchase/purchase.cbl:L786-L790'
  'irs_post:irs:4:irs030-dispatch:irs/irs.cbl:L666-L672'
)

# The in-scope `-m' modules each subsystem's menu must be able to load, taken
# verbatim from the arrays harness/build_oracle.sh publishes so the two files
# cannot disagree about what "built" means.
readonly -a ACAS_RUN_GENERAL_MODULES=(gl000 gl051 gl070 gl071 gl072 gl080)
readonly -a ACAS_RUN_SALES_MODULES=(sl000 sl055 sl060 sl100)
readonly -a ACAS_RUN_PURCHASE_MODULES=(pl000 pl055 pl060 pl100)
readonly -a ACAS_RUN_IRS_MODULES=(irs000 irs030)

readonly -a ACAS_RUN_LIBRARY_DIRS=(common general irs purchase sales stock)

# Screen refusals and interactive diversions.

# SY009 ACAS_LEDGERS or ACAS_BIN begins with a space, then a `stop run'
# [copybooks/Proc-Get-Env-Set-Files.cob:L20-L28] Invalid Date the date-entry
# reject loop.
readonly -a ACAS_RUN_FORBIDDEN=(
  'SY010|the menu refused to run: fewer than 24 lines|general/general.cbl:L374-L383'
  'SY013|the menu refused to run: fewer than 80 columns|general/general.cbl:L374-L383'
  'SYS002|the menu diverted into the interactive sys002 setup program|general/general.cbl:L385-L396'
  'SY102|sys002 could not read the system parameter file|general/general.cbl:L385-L396'
  'SY104|sys002 is waiting for an operator to fix the system parameter file|general/general.cbl:L385-L396'
  'SY007|the menu refused a program argument and stopped|copybooks/Proc-Get-Env-Set-Files.cob:L37'
  'SY009|ACAS_LEDGERS or ACAS_BIN begins with a space|copybooks/Proc-Get-Env-Set-Files.cob:L20-L28'
  'Invalid Date|the pinned run date was rejected by maps04|general/gl000.cbl:L261-L265'
)

readonly ACAS_RUN_MENU_ANCHOR='Select one of the following by letter'
readonly ACAS_RUN_IRS_MENU_ANCHOR='Select the required function'
readonly ACAS_RUN_IRS_OPTION_ANCHOR='Enter Run Option'

# The 22 in-scope tables, used only to validate a scenario's affected-table
# list against the same vocabulary harness/dump_tables.py uses.
readonly -a ACAS_RUN_INSCOPE_TABLES=(
  ANALYSIS-REC GLBATCH-REC GLLEDGER-REC GLPOSTING-REC
  IRSDFLT-REC IRSFINAL-REC IRSNL-REC IRSPOSTING-REC
  PSIRSPOST-REC PUINV-LINES-REC PUINVOICE-REC PUITM5-REC PULEDGER-REC
  SAINV-LINES-REC SAINVOICE-REC SAITM3-REC SALEDGER-REC
  SYSDEFLT-REC SYSFINAL-REC SYSTEM-REC SYSTOT-REC VALUEANAL-REC
)

readonly -a ACAS_RUN_AUTOGEN_TABLES=(SAAUTOGEN-REC SAAUTOGEN-LINES-REC)

# THE sl830 ASYMMETRY -- the Cobol side runs a program the Python side does not
# [sales/sales.cbl:L756-L768] load07 calls sl830 BEFORE sl055, and sl830 is
# explicitly out of scope.



# The residual asymmetry -- the oracle runs one more program than the Python
# does, even though that program returns immediately -- is settled by this
# script's own post-run assertion that the two autogen tables are untouched.


# Leaving a letter-menu with "X" is not inert.

# The resolution is NOT to avoid the exit path -- killing the process instead
# would leave a different and non-deterministic state -- and NOT an ignore-list
# in the diff tool.

# The ONE scenario parser, shared with harness/run_python_scenario.sh.
# Resolved from THIS script's own location rather than from ACAS_REPO, so the reader
# that ships beside this runner is the reader it uses -- a pair that cannot be
# mismatched by an environment variable. The `case' is not decoration: invoked by a
# bare name from its own directory, BASH_SOURCE holds no slash at all and stripping
# a trailing component would yield this script's own name as the directory.
case "${BASH_SOURCE[0]}" in
  */*) ACAS_RUN_SELF_DIR="${BASH_SOURCE[0]%/*}" ;;
  *)   ACAS_RUN_SELF_DIR='.' ;;
esac
readonly ACAS_RUN_SELF_DIR
# The shared scenario reader and the shared stage registry are BOTH modes of
# harness/normalize.py: they were files of their own,
# which the Agent Action Plan section 0.3.1 harness inventory does not name.
readonly ACAS_RUN_SCENARIO_READER="$ACAS_RUN_SELF_DIR/normalize.py"

# THE CANONICAL STAGE REGISTRY. The parity protocol's ten
# stages are defined in `PARITY_STAGES' in harness/normalize.py and nowhere else, and
# `--print-stage-shell' publishes them as the sourceable fragment eval'd below -- the same
# variable names, the same readonly protection, the same re-source guard and the same
# three `acas_parity_stage_*' helpers this script has always called. So this script's
# statement of where it sits in the protocol cannot drift from the protocol actually
# driven. Duplicating the list here as prose would let it go stale; putting it in a shell
# file of its own would add a path the Agent Action Plan section 0.3.1 harness inventory
# does not name.
readonly ACAS_RUN_STAGE_REGISTRY="$ACAS_RUN_SELF_DIR/normalize.py"
if [[ ! -r "$ACAS_RUN_STAGE_REGISTRY" ]]; then
  printf '%s: the canonical stage registry is missing: %s\n' \
    "$0" "$ACAS_RUN_STAGE_REGISTRY" >&2
  printf '  The parity protocol'"'"'s stages are defined there and nowhere else.\n' >&2
  exit 71
fi
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s: python3 is not on PATH, so the canonical stage registry cannot be\n' \
    "$0" >&2
  printf '  read. Every stage this script performs already needs it.\n' >&2
  exit 71
fi
if ! ACAS_RUN_STAGE_SHELL="$(python3 "$ACAS_RUN_STAGE_REGISTRY" --print-stage-shell)"
then
  printf '%s: the canonical stage registry could not be read from %s\n' \
    "$0" "$ACAS_RUN_STAGE_REGISTRY" >&2
  exit 71
fi
eval "$ACAS_RUN_STAGE_SHELL"
unset ACAS_RUN_STAGE_SHELL

ACAS_RUN_SCENARIO=''            # scenario NAME
ACAS_RUN_SCENARIO_FILE=''       # scenario YAML path
ACAS_RUN_SUBSYSTEM=''           # the subsystem of the operation being driven
# What --subsystem asked for, kept separate from the resolved value. The resolved
# one changes per operation; the request is a constraint on every one of them, so it
# must survive being resolved.
ACAS_RUN_SUBSYSTEM_REQUESTED=''
ACAS_RUN_OPERATION=''           # the operation currently being driven
# The sentinel that means "declared, but never driven". Deliberately NOT zero: zero
# is a real term code, and a slot left at zero would attest a clean disposition for
# an operation that never ran. It is outside the two-digit range of
# WS-Term-Code [copybooks/wscall.cob:L10], so it can never collide with one.
readonly ACAS_RUN_OP_NOT_RUN='not-run'
# THE ORDERED OPERATION LIST. This runner drives EVERY operation the
# scenario declares, in the declared order, in ONE invocation -- see
# acas_resolve_operations for why one-per-invocation could not attest the run.
declare -a ACAS_RUN_OPS=()
# Its observed disposition, one entry per ACAS_RUN_OPS entry, same index. This is
# the operation's own term code, NOT this script's exit status.
declare -a ACAS_RUN_OP_STATUS=()
# Which of ACAS_RUN_OPS is being driven right now, 0-based; -1 before the first.
ACAS_RUN_OP_INDEX=-1
ACAS_RUN_TIMEOUT=120            # per-prompt timeout, seconds
ACAS_RUN_LOG=''                 # $ACAS_OUT/run-logs/<scenario>/cobol.log
# Whether the transcript file actually EXISTS and is writable yet, as distinct
# from merely having been requested on the command line.
ACAS_RUN_LOG_OPEN=0
ACAS_RUN_LOCK=''                # the sequential-run lock, removed by the EXIT trap
ACAS_RUN_PLAN_FILE=''           # the resolved keystroke plan, beside the log
ACAS_RUN_RESULT_FILE=''         # the driver's machine-readable outcome record
ACAS_RUN_FINGERPRINT=''         # cobol.seed-fingerprint -- read by the Python side
ACAS_RUN_POST_FINGERPRINT=''    # cobol.post-fingerprint -- the same record, after the drive
ACAS_RUN_STATUS_FILE=''         # cobol.run-status -- read by harness/dump_tables.py
# cobol.operation-status -- ONE record per declared operation, carrying that
# operation's own observed disposition. Separate from the run-status record because
# WRAPPER HEALTH and PER-OPERATION DISPOSITION are different facts.
ACAS_RUN_OP_STATUS_FILE=''
# One identity for one attempt, bound through every stage. Supplied by the
# protocol via --run-id or ACAS_PARITY_RUN_ID; derived locally when a
# hand invocation supplies neither -- and its presence is what marks this run as a
# protocol stage rather than a hand invocation (acas_assert_no_evidence_bypass).
ACAS_RUN_RUN_ID="${ACAS_PARITY_RUN_ID:-}"
# The staged fixture marker digest this run was seeded from, read from the record
# harness/reset_db.sh publishes. The EXACT seed identity.
ACAS_RUN_SEED_IDENTITY=''
# This script's own directory, so its siblings -- harness/dump_tables.py --table-digest, the
# single canonical state-digest producer both sides invoke -- are found relative to
# this file rather than through $PATH or a guessed checkout layout. Resolved once,
# here, because $0 is not reliable after a `cd'.
ACAS_RUN_HARNESS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# The status a SIGNAL handler decided on, and the pty driver's pid while it runs.
# Both exist because of the same problem: bash runs the EXIT trap when this shell is
# terminated by a signal, but `$?' at that moment is the status of the last command
# that COMPLETED -- routinely zero -- so the run-status record claimed success for a
# run that was killed. The handler records the real status here and the writer
# prefers it. See acas_on_signal.
ACAS_RUN_SIGNAL_STATUS=0
ACAS_RUN_DRIVER_PID=0
ACAS_RUN_DRY_RUN=0              # --dry-run
ACAS_RUN_ROTATE_FH_LOG=1        # rotation is the DEFAULT; --no-rotate-fh-log opts out
ACAS_RUN_FH_ROTATED=''          # where fh-logger.txt was moved to, if it was
ACAS_RUN_MENU_KEY=''            # the resolved single-character menu selection
ACAS_RUN_PARAGRAPH=''           # the menu paragraph that key dispatches to
ACAS_RUN_PARAGRAPH_LOCATOR=''   # its [<path>:<locator>]
ACAS_RUN_EXECUTABLE=''          # $ACAS_BUILD/<subsystem>/<subsystem>
ACAS_RUN_DRIVEN=0               # 1 once the menu has actually been spawned
ACAS_RUN_DATE_TEXT=''           # the pinned date, as typed
ACAS_RUN_DATE_FORM=''           # 1 UK, 2 USA, 3 International
ACAS_RUN_RUN_DATE=''            # the expected binary Run-Date
ACAS_RUN_IRS_INSTEAD=''         # the pinned three-state fan-out switch
ACAS_RUN_OBSERVED_STATUS=0       # term code observed from the driven menu path
ACAS_RUN_IRS_CLEAR=''           # G-1: irs030's clear-transfer-file answer
ACAS_RUN_GL080_PROCEED=''       # G-2: gl080's pre-run gate answer
ACAS_RUN_PAYMENT_CONFIRM=''     # G-3: sl100 / pl100 YES/NO
ACAS_RUN_DISK_CHANGE=''         # gl080 disk-change option, 0 or 9
ACAS_RUN_ARCHIVE_PATH=''        # gl080 archive path override, or empty
ACAS_SQL_OUT=''                 # last successful scalar query result
ACAS_SQL_DIAG=''                # last client diagnostic, for error messages
declare -a ACAS_RUN_TABLES=()          # the scenario's affected-table list
# The fingerprint list -- the affected tables, plus the menu-persisted parameter row on
# the fallback path where a scenario has not declared it. See
# acas_resolve_fingerprint_tables for why SYSTEM-REC is dumped AND fingerprinted on
# every scenario.
declare -a ACAS_RUN_FINGERPRINT_TABLES=()
readonly ACAS_RUN_PARAMETER_TABLE='SYSTEM-REC'
declare -a ACAS_RUN_SUMMARY=()         # the closing summary table
declare -a ACAS_RUN_WARN_SUMMARY=()    # non-fatal findings, replayed at the end
declare -a ACAS_RUN_TLS_VARIANTS=()
ACAS_RUN_SCHEMA_LITERAL=''
# The sequential run lock. The PATH and the OWNERSHIP FLAG are separate for the
# same reason ACAS_RUN_LOG_OPEN is separate from ACAS_RUN_LOG.
ACAS_RUN_LOCK=''
ACAS_RUN_LOCK_HELD=0

# Stage banners are numbered so the log reads as the deterministic staged
# orchestration the plan prescribes (R-6).

# Append to the run log if it is open yet. Silent before acas_open_log runs, so
# early usage errors still print without needing a log.
acas_tee() {
  if (( ACAS_RUN_LOG_OPEN )); then
    # 2>/dev/null is deliberately FIRST. Redirections are applied left to
    # right, so silencing stderr before opening the append target is what
    # actually suppresses a redirection failure.
    printf '%s\n' "$*" 2>/dev/null >>"$ACAS_RUN_LOG" || true
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
  ACAS_RUN_WARN_SUMMARY+=("$*")
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

# EVERY ONCE-PER-RUN GATE ASKS THE WHOLE LIST, NOT THE SELECTION
#
# Three kinds of check in this script run exactly ONCE, before the first drive:
# the pinned-value gates in acas_resolve_pinned_values, the database
# preconditions in acas_assert_database, and the fh-logger rotation. At that
# point ACAS_RUN_OPERATION holds the FIRST operation of the list, because
# acas_resolve_operations deliberately leaves it selected so that nothing between
# resolution and the drive loop sees an incoherent operation/subsystem pair.
#
# So a once-per-run check keyed on ACAS_RUN_OPERATION asks about operation 1 and
# silently says nothing about operations 2..n. period_end_totals declares
# sl_invoice_post, sl_cash_post, pl_order_post, pl_payment_post -- and the two
# cash routes are the ones that need an answer to a prompt with no default. The
# measured consequence was a run that drove operation 1 cleanly and then hung on
# sl100's YES/NO prompt until the reactive budget ran out, exit 76.
#
# These three predicates are the fix, and they are deliberately pure: none of
# them touches ACAS_RUN_OPERATION or ACAS_RUN_SUBSYSTEM, so a gate can ask about
# any operation without disturbing the selected one.

# acas_ops_include <operation>
# True when <operation> appears anywhere in the resolved ordered list.
acas_ops_include() {
  local wanted="$1" op
  (( ${#ACAS_RUN_OPS[@]} > 0 )) || return 1
  for op in "${ACAS_RUN_OPS[@]}"; do
    [[ "$op" == "$wanted" ]] && return 0
  done
  return 1
}

# acas_op_subsystem <operation>
# Echo the menu that dispatches <operation>, read from the same frozen map
# acas_select_operation reads. Returns non-zero for an unmapped name rather than
# echoing a guess.
acas_op_subsystem() {
  local wanted="$1" entry rest
  for entry in "${ACAS_RUN_OPERATION_MAP[@]}"; do
    if [[ "${entry%%:*}" == "$wanted" ]]; then
      rest="${entry#*:}"
      printf '%s\n' "${rest%%:*}"
      return 0
    fi
  done
  return 1
}

# acas_ops_use_subsystem <subsystem>
# True when ANY declared operation is dispatched by <subsystem>'s menu.
acas_ops_use_subsystem() {
  local wanted="$1" op mapped
  (( ${#ACAS_RUN_OPS[@]} > 0 )) || return 1
  for op in "${ACAS_RUN_OPS[@]}"; do
    mapped="$(acas_op_subsystem "$op")" || continue
    [[ "$mapped" == "$wanted" ]] && return 0
  done
  return 1
}

acas_summary_row() {
  ACAS_RUN_SUMMARY+=("$(printf '%-22s %s' "$1" "$2")")
}

readonly ACAS_RUN_LOG_FIELD_MAX=120

acas_sanitise_field() {
  local value="$1"
  # Replace every C0 control (including CR, LF and TAB) and DEL with `?'.
  value="$(printf '%s' "$value" | LC_ALL=C tr '\000-\037\177' '?')"
  # Drop the C1 range, which a UTF-8 terminal can still act on.
  value="$(printf '%s' "$value" | LC_ALL=C tr -d '\200-\237')"
  if (( ${#value} > ACAS_RUN_LOG_FIELD_MAX )); then
    value="${value:0:ACAS_RUN_LOG_FIELD_MAX}...<truncated>"
  fi
  printf '%s' "$value"
}

# This script issues exactly ONE query that embeds a caller-supplied value.
readonly ACAS_RUN_SCHEMA_NAME_PATTERN='^[A-Za-z_][A-Za-z0-9_$]*$'
readonly -a ACAS_RUN_DEFAULT_ALLOWED_SCHEMAS=(
  'ACASDB'
)

# Escape a value for use inside a single-quoted SQL literal and RETURN IT WITH
# ITS QUOTES, so a call site cannot use the result and forget to quote it.
acas_sql_quote_literal() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\'/\\\'}"
  printf "'%s'" "$value"
}

# Split a comma- or space-separated list into one item per line.
acas_split_list() {
  local raw="${1-}"
  local item
  local IFS=', '
  # shellcheck disable=SC2086  # word splitting on IFS is the whole point here
  for item in $raw; do
    [[ -n "$item" ]] && printf '%s\n' "$item"
  done
  return 0
}

acas_assert_schema_name() {
  if [[ ! "$ACAS_DB_NAME" =~ $ACAS_RUN_SCHEMA_NAME_PATTERN ]]; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_NAME is not a plain SQL identifier: '$(acas_sanitise_field "$ACAS_DB_NAME")'" \
      'It is embedded in an information_schema query, so it must match' \
      "$ACAS_RUN_SCHEMA_NAME_PATTERN -- a letter or underscore followed by letters," \
      'digits, underscores or dollar signs. The frozen schema is named ACASDB.'
  fi

  local -a allowed=("${ACAS_RUN_DEFAULT_ALLOWED_SCHEMAS[@]}")
  local -a extra=()
  mapfile -t extra < <(acas_split_list "${ACAS_DB_ALLOWED_SCHEMAS-}")
  if (( ${#extra[@]} )); then
    allowed+=("${extra[@]}")
  fi
  if ! acas_in_list "$ACAS_DB_NAME" "${allowed[@]}"; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_NAME names a schema this harness is not configured to inspect: $ACAS_DB_NAME" \
      "Permitted: $(acas_join_words "${allowed[@]}"). If another schema really" \
      'holds the frozen ACAS tables, add it to ACAS_DB_ALLOWED_SCHEMAS -- an' \
      'explicit, auditable declaration rather than an implicit default.'
  fi

  ACAS_RUN_SCHEMA_LITERAL="$(acas_sql_quote_literal "$ACAS_DB_NAME")"
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

# =============================================================================
#  THE RUN ID -- ONE IDENTITY FOR ONE ATTEMPT
#
#  Writing every artifact of the parity protocol to a CANONICAL path and nothing else --
#  run-logs/<scenario>/<side>.log, <side>.run-status, <side>.seed-fingerprint -- would have
#  two attempts at one scenario write to the same names, and a driver offering --from/--to
#  would make that reachable on purpose:
#  stages 1..5 of one attempt and stages 6..10 of another produce a verdict over
#  artifacts that were never part of the same run, and nothing in the evidence says
#  so. Resuming a protocol part-way is not offered at all, and
#  the run-scoped paths below are why doing it by hand cannot go unnoticed either.
#
#  So one identity is bound through every stage. It arrives from the driver
#  (--run-id, or ACAS_PARITY_RUN_ID), which is how all ten stages come to agree; when
#  neither is given -- a hand invocation -- one is derived locally so that the field
#  is never empty and never guessed at by a reader.
#
#  It is deliberately NOT derived from the clock. Rule R-6 makes the run
#  reproducible, and wall-clock readings are kept out of retained
#  evidence; a timestamped identity would put one back into every record. The kernel
#  UUID source is used when it is readable, and the process id plus one shell random
#  otherwise -- neither of which says when the run happened.
# =============================================================================
acas_derive_run_id() {
  local uuid=''
  if [[ -r /proc/sys/kernel/random/uuid ]]; then
    read -r uuid < /proc/sys/kernel/random/uuid 2>/dev/null || uuid=''
    uuid="${uuid//-/}"
  fi
  if [[ -n "$uuid" ]]; then
    printf 'local-%s' "${uuid:0:16}"
  else
    printf 'local-%s-%s' "$$" "$RANDOM"
  fi
}

acas_assert_run_id() {
  #  THE VARIABLE, NOT THE PROCESS ID. Writing `$$ACAS_RUN_RUN_ID` here would have bash
  #  expand `$$` -- this shell's PID -- followed by the LITERAL text `ACAS_RUN_RUN_ID`, so
  #  the regex would be matched against something like `4127ACAS_RUN_RUN_ID`, which is
  #  always inside the closed alphabet: the check would ALWAYS PASS and the supplied run
  #  id would never be validated at all. The id becomes
  #  part of a file name and is published in every evidence record, so CR, LF, tab or
  #  path content in it could forge an evidence line or steer a staging path
  #  (CWE-20, CWE-22, CWE-73, CWE-117).
  [[ "${ACAS_RUN_RUN_ID-}" =~ ^[A-Za-z0-9._-]{1,64}$ ]] || acas_die "$EX_USAGE" \
    "the run id must be 1 to 64 characters of letters, digits, dot, underscore or hyphen." \
    "  got: $(acas_sanitise_field "$ACAS_RUN_RUN_ID")" \
    'It becomes part of a file name and is published in every evidence record, so it' \
    'has to be a plain identifier.'

  #  AND IT MUST NAME SOMETHING. `.` and `..` are inside the alphabet above and are
  #  directory references rather than identifiers; neither can traverse -- the closed
  #  set admits no `/` -- but neither is a name an evidence record can be attributed
  #  to, and `..` as a file-name component reads as a mistake wherever it appears.
  case "$ACAS_RUN_RUN_ID" in
    .|..)
      acas_die "$EX_USAGE" \
        "the run id must be an identifier, not a directory reference: '$ACAS_RUN_RUN_ID'." \
        'It is published in every evidence record and must identify one attempt.'
      ;;
  esac
}

# EVERY EVIDENCE LEAF IS PUBLISHED BY RENAME, NEVER BY REDIRECTION
#
# acas_create_private_file above closes the CREATE race: it refuses a symlink and
# creates under `set -C', which is O_EXCL. It does not close the WRITE race, and the
# write is where the evidence actually appears. Every artifact this script publishes
# -- the run-status record, the per-operation dispositions, the seed fingerprint --
# must NOT be written with a plain `>' redirection into a path checked for a symlink
# EARLIER. Between the check and the write, the name can be replaced;
# `>' follows a symlink and truncates whatever it points at (CWE-59), and a reader
# arriving mid-write sees a TRUNCATED record, which for an attestation file means a
# capture is either unattested or attested by half a record.
#
# So content is written into a private temporary file in the SAME DIRECTORY -- same
# filesystem, so the rename cannot fail with EXDEV -- and then renamed over the
# target. `mv' is rename(2): the target either holds the whole previous content or
# the whole new content, never a mixture, and renaming ONTO a symlink replaces the
# LINK rather than writing through it.
#
# Reads content from STDIN, so the caller composes the record in one place:
#     { printf ...; printf ...; } | acas_publish_atomic "$target" 'the run status'
#
# NEVER dies. Every caller is either the EXIT trap or a final-report step, where an
# abort would replace a real verdict with a plumbing failure; it warns and returns
# non-zero so the caller can say plainly that the artifact is missing -- and a
# missing attestation is read downstream as UNATTESTED, which is the safe direction.
acas_publish_atomic() {
  local target="$1" what="${2:-an evidence artifact}"
  local dir base tmp

  if [[ -z "$target" ]]; then
    printf 'WARNING: %s has no resolved path, so it was not published.\n' "$what" >&2
    return 1
  fi

  dir="${target%/*}"
  [[ "$dir" != "$target" ]] || dir='.'
  base="${target##*/}"
  tmp="$dir/.$base.tmp.$$"

  if [[ ! -d "$dir" ]]; then
    printf 'WARNING: the directory for %s does not exist: %s\n' "$what" "$dir" >&2
    return 1
  fi

  # A leftover temporary from a killed run is removed by name; it is ours, it is
  # inside a 0700 directory, and it is not the target.
  [[ -e "$tmp" || -L "$tmp" ]] && rm -f -- "$tmp" 2>/dev/null

  # O_EXCL: refuses an existing name, including a symlink, rather than following it.
  if ! (set -C; : >"$tmp") 2>/dev/null; then
    printf 'WARNING: could not create a private temporary for %s at %s\n' "$what" "$tmp" >&2
    return 1
  fi
  chmod 600 -- "$tmp" 2>/dev/null || true

  if ! cat >"$tmp" 2>/dev/null; then
    printf 'WARNING: could not write %s into %s\n' "$what" "$tmp" >&2
    rm -f -- "$tmp" 2>/dev/null || true
    return 1
  fi

  if ! mv -f -- "$tmp" "$target" 2>/dev/null; then
    printf 'WARNING: could not publish %s to %s\n' "$what" "$target" >&2
    rm -f -- "$tmp" 2>/dev/null || true
    return 1
  fi
  return 0
}


# acas_timeout_seconds <variable-name> <default> Validates the named variable
# and publishes the result in ACAS_TIMEOUT_RESOLVED.
acas_timeout_seconds() {
  local name="$1" default="$2" value
  ACAS_TIMEOUT_RESOLVED=''
  value="${!name-}"
  [[ -n "$value" ]] || value="$default"

  if [[ ! "$value" =~ ^[0-9]+$ ]]; then
    acas_die "$EX_USAGE" \
      "$name must be a whole number of seconds; got '$value'."
  fi
  # Base 10 explicitly: a value such as 08 is a plain number here, not octal.
  value=$(( 10#$value ))
  if (( value < 1 )); then
    acas_die "$EX_USAGE" \
      "$name must be at least 1 second; got '$value'." \
      'A zero or negative budget would mean no deadline at all.'
  fi
  if (( value > ACAS_TIMEOUT_MAX )); then
    acas_die "$EX_USAGE" \
      "$name must be at most $ACAS_TIMEOUT_MAX seconds; got '$value'."
  fi
  ACAS_TIMEOUT_RESOLVED="$value"
}

acas_resolve_deadlines() {
  acas_have timeout || acas_die "$EX_PRECONDITION" \
    'timeout is not on the PATH.' \
    'It is part of coreutils and every external process this script spawns runs' \
    'under it. harness/Dockerfile.gnucobol provides it.'

  acas_timeout_seconds ACAS_TIMEOUT_GRACE 15
  ACAS_TIMEOUT_GRACE="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_CLIENT 30
  ACAS_TIMEOUT_CLIENT="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_DRIVE 3600
  ACAS_TIMEOUT_DRIVE="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_ROTATE 300
  ACAS_TIMEOUT_ROTATE="$ACAS_TIMEOUT_RESOLVED"
  readonly ACAS_TIMEOUT_GRACE ACAS_TIMEOUT_CLIENT ACAS_TIMEOUT_DRIVE ACAS_TIMEOUT_ROTATE

  # The fh-logger budget is resolved HERE, with the deadlines, because it is
  # the same kind of value -- a number arriving from the environment that
  # silently becomes meaningless if it is malformed.
  local budget="${ACAS_FH_LOG_BUDGET_MB-}"
  [[ -n "$budget" ]] || budget="$ACAS_RUN_FH_BUDGET_DEFAULT_MB"
  if [[ ! "$budget" =~ ^[0-9]+$ ]]; then
    acas_die "$EX_USAGE" \
      "ACAS_FH_LOG_BUDGET_MB must be a whole number of megabytes; got '$budget'." \
      'Leave it unset to take the default of' \
      "$ACAS_RUN_FH_BUDGET_DEFAULT_MB MiB."
  fi
  budget=$(( 10#$budget ))
  if (( budget < 1 )); then
    acas_die "$EX_USAGE" \
      "ACAS_FH_LOG_BUDGET_MB must be at least 1 MiB; got '$budget'." \
      'A zero budget would assert that the frozen file-handler log needs no space at' \
      'all, and [copybooks/Test-Data-Flags.cob] makes that impossible: SW-Testing is' \
      'frozen on, so the log is always written.'
  fi
  ACAS_RUN_FH_BUDGET_MB="$budget"
  readonly ACAS_RUN_FH_BUDGET_MB
}

# Free space for the frozen file-handler log, asserted BEFORE the database is
# contacted and long before the menu is spawned.
acas_assert_fh_log_capacity() {
  local avail_mb=''

  if ! acas_have df; then
    acas_warn "df is not available, so the ${ACAS_RUN_FH_BUDGET_MB} MiB fh-logger budget is UNVERIFIED for this run"
    return 0
  fi

  # POSIX output, 1 MiB blocks, field 4 of the data row.
  avail_mb="$(df -P -B1048576 -- "$ACAS_DATA" 2>/dev/null | awk 'NR==2 { print $4 }')"

  if [[ -z "$avail_mb" || ! "$avail_mb" =~ ^[0-9]+$ ]]; then
    acas_warn "could not determine free space on $ACAS_DATA; the ${ACAS_RUN_FH_BUDGET_MB} MiB fh-logger budget is UNVERIFIED for this run"
    return 0
  fi

  acas_log "free space on the data volume = ${avail_mb} MiB (fh-logger budget ${ACAS_RUN_FH_BUDGET_MB} MiB)"

  if (( avail_mb < ACAS_RUN_FH_BUDGET_MB )); then
    acas_die "$EX_CAPACITY" \
      "only ${avail_mb} MiB is free on the data volume; this run reserves ${ACAS_RUN_FH_BUDGET_MB} MiB." \
      "  data volume: $ACAS_DATA" \
      'File-handler logging cannot be switched off: SW-Testing is frozen on at' \
      '[copybooks/Test-Data-Flags.cob] and that file is not modified (R-4). The log' \
      'has been measured growing 473 MB in about three minutes.' \
      'This is refused NOW -- before the database is contacted and before the menu is' \
      'spawned -- because a volume that fills mid-cycle leaves the database half-posted' \
      'and reports a write error rather than the capacity problem that caused it.' \
      'Free some space, archive the rotated logs under the run-logs directory in the' \
      'output area, or lower the reservation with ACAS_FH_LOG_BUDGET_MB if you know' \
      'this run is short.'
  fi
}

# acas_deadline_prefix <budget-seconds> Publishes the command prefix in
# ACAS_DEADLINE_ARGV.
acas_deadline_prefix() {
  local budget="$1"
  [[ "$budget" =~ ^[1-9][0-9]*$ ]] || acas_die "$EX_PRECONDITION" \
    "acas_deadline_prefix was given a non-positive budget: '$budget'." \
    'Deadlines are resolved by acas_resolve_deadlines before anything spawns.'
  ACAS_DEADLINE_ARGV=(
    timeout
    "--kill-after=$ACAS_TIMEOUT_GRACE"
    --signal=TERM
    "$budget"
  )
}

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
  local rc="$1" elapsed="$2" budget="$3" budget_var="$4"
  shift 4
  if ! acas_is_timeout_status "$rc" "$elapsed" "$budget"; then
    return 0
  fi
  acas_die "$EX_TIMEOUT" \
    "$* exceeded its ${budget}s deadline (status $rc after ${elapsed}s)." \
    "Raise $budget_var if the work legitimately takes longer; investigate the" \
    'command if it does not. It was sent TERM and then KILL after' \
    "${ACAS_TIMEOUT_GRACE}s, so nothing is still running."
}


# Every write target is judged by its CANONICAL path, never by the string the
# operator typed.

# acas_canonical_path <path> Prints the canonical form of <path>, resolving
# through the nearest existing ancestor when the leaf does not exist yet.
acas_canonical_path() {
  local path="$1" probe parent tail=''

  # An empty or relative path is anchored first, so the answer does not depend
  # on the caller's working directory.
  if [[ -z "$path" ]]; then
    printf '%s' ''
    return 0
  fi
  if [[ "$path" != /* ]]; then
    path="$PWD/$path"
  fi

  probe="$path"
  while [[ -n "$probe" && ! -e "$probe" ]]; do
    tail="${probe##*/}/$tail"
    parent="${probe%/*}"
    if [[ "$parent" == "$probe" ]]; then
      parent=''
    fi
    probe="$parent"
  done
  [[ -n "$probe" ]] || probe='/'

  local resolved
  resolved="$(readlink -f -- "$probe" 2>/dev/null || printf '%s' "$probe")"
  if [[ -n "$tail" ]]; then
    # Strip the trailing slash the accumulation above leaves behind.
    tail="${tail%/}"
    resolved="${resolved%/}/$tail"
  fi
  printf '%s' "$resolved"
}

acas_path_contains() {
  local root="${1%/}" path="${2%/}"
  [[ -n "$root" && -n "$path" ]] || return 1
  [[ "$path" == "$root" || "$path" == "$root"/* || "$root" == "$path"/* ]]
}

# acas_assert_outside_repo <label> <path> Refuses a write target that resolves
# into the frozen checkout, in either direction. The checkout is
# REFERENCE-only.
acas_assert_outside_repo() {
  local label="$1" path="$2"
  local repo_real target
  repo_real="$(acas_canonical_path "$ACAS_REPO")"
  target="$(acas_canonical_path "$path")"

  if acas_path_contains "$repo_real" "$target"; then
    acas_die "$EX_PRECONDITION" \
      "$label resolves inside the frozen checkout." \
      "  requested : $path" \
      "  resolves  : $target" \
      "  checkout  : $repo_real" \
      'The checkout is read-only specification. Point it at the writable output' \
      'area named by ACAS_OUT instead.'
  fi
}

# acas_assert_outside_tree <label> <path> <protected-root> <why>...
acas_assert_outside_tree() {
  local label="$1" path="$2" root="$3"
  shift 3
  local root_real target
  root_real="$(acas_canonical_path "$root")"
  target="$(acas_canonical_path "$path")"

  if acas_path_contains "$root_real" "$target"; then
    acas_die "$EX_USAGE" \
      "$label resolves inside $root_real" \
      "  requested : $path" \
      "  resolves  : $target" \
      "$@"
  fi
}

# TRAPS There is no credential FILE to shred.
ACAS_RUN_CURRENT_STAGE=''

# shellcheck disable=SC2317  # reached only through the ERR trap installed below,
# which shellcheck cannot follow; the body is live and is exercised by the
# negative validation cases.
acas_on_err() {
  local status="$1" line="$2" cmd="$3"
  printf '\nFATAL: unexpected failure at %s line %s (status %s).\n' \
    "${BASH_SOURCE[0]}" "$line" "$status" >&2
  printf '       failing command: %s\n' "$cmd" >&2
  if [[ -n "$ACAS_RUN_CURRENT_STAGE" ]]; then
    printf '       while: %s\n' "$ACAS_RUN_CURRENT_STAGE" >&2
  fi
  acas_tee "FATAL: unexpected failure at line $line (status $status): $cmd"
}
trap 'acas_on_err "$?" "$LINENO" "$BASH_COMMAND"' ERR

# shellcheck disable=SC2317  # reached only through the EXIT trap installed below.
# shellcheck disable=SC2317  # reached only through the EXIT trap installed below,
# Release the sequential run lock, but only if THIS process took it, so an
# early failure can never delete a lock belonging to a live run.
acas_release_lock() {
  if (( ACAS_RUN_LOCK_HELD )) && [[ -n "$ACAS_RUN_LOCK" ]]; then
    rm -f -- "$ACAS_RUN_LOCK" 2>/dev/null || true
    ACAS_RUN_LOCK_HELD=0
  fi
}

# THE PER-SIDE RUN-STATUS RECORD, written from the EXIT trap.
#
# [harness/dump_tables.py] records an ATTESTATION in the dump manifest and
# [harness/diff_states.py] refuses to compare two captures unless both sides
# attest that their run actually succeeded. That closes the silent pass in which
# the run stage failed, the capture stage found the tables empty, and the diff
# then reported "identical" -- a clean pass over two empty directories. The
# attestation has to come from the side that KNOWS the status, which is this
# script, and it has to be written on EVERY path, which is why it lives in the
# EXIT trap rather than at the end of acas_main.
#
# FORMAT -- a four-field TSV, one field per line, in the order dump_tables.py
# declares:
#     scenario<TAB><name>
#     side<TAB>cobol
#     status<TAB><this script's exit status>
#     seed_fingerprint_sha256<TAB><digest, or empty if none was recorded>
# The digest is a POINTER to the fingerprint, not a substitute for it: the
# cross-check compares the fingerprints themselves, and this lets a capture be
# tied to the starting state it was taken from.
#
# It must not raise and must not change the exit status. It runs from the EXIT
# trap, where a failure of its own would replace the real diagnosis with a
# confusing one, so every step is best-effort and reported rather than fatal.
# shellcheck disable=SC2317  # reached only through the EXIT trap installed below,
# which shellcheck cannot follow; the body is live and runs on every exit path.
# WRAPPER HEALTH AND PER-OPERATION DISPOSITION ARE DIFFERENT FACTS
#
# This script's exit status answers "did the harness do its job?" -- it drove the
# menu, the prompts appeared where the plan said they would, the post-run assertions
# held. It does NOT answer "what did the compiled cycle decide?", and it never can,
# because a term-code-5 abort is CORRECT compiled behaviour
# [general/gl070.cbl:L287-L290] and the harness that observed it did its job
# perfectly. Conflating the two is how a scenario whose whole subject is a rejection
# came to be asserted through a wrapper exit code.
#
# Before this, the only machine-readable statement of an operation's disposition was
# an `OPERATION_STATUS' line inside the pty TRANSCRIPT -- a file that also contains
# every screen the menu drew, so reading it means pattern-matching a log. That line
# is KEPT, because tests/conftest.py parses it and because a reader of the
# transcript should be able to see the disposition in place. This artifact is the
# structured statement of the same facts:
#
#   scenario   <TAB> <name>
#   side       <TAB> cobol
#   operations <TAB> <count>
#   operation  <TAB> <index, 1-based> <TAB> <name> <TAB> <observed status>
#   ...one `operation' record per DECLARED operation, in declared order...
#
# An operation that was declared but never driven carries the sentinel
# `not-run' rather than a number. That distinction is the whole point: zero is a
# real term code, so a slot defaulting to zero would attest a clean disposition for
# an operation that never happened.
acas_publish_operation_status() {
  [[ -n "$ACAS_RUN_OP_STATUS_FILE" ]] || return 0

  # A dry run drives nothing, so it has no disposition to publish and must not
  # appear to have one. The record is left as the empty file stage 3 created:
  # zero `operation' records for a non-zero declared count is self-evidently not a
  # complete run, which is exactly what a reader should conclude.
  if (( ACAS_RUN_DRY_RUN )); then
    acas_note '--dry-run drove nothing, so the per-operation status record stays empty'
    return 0
  fi

  local index rendered
  {
    printf 'scenario\t%s\n' "$ACAS_RUN_SCENARIO"
    printf 'side\tcobol\n'
    printf 'run_id\t%s\n' "$ACAS_RUN_RUN_ID"
    printf 'operations\t%s\n' "${#ACAS_RUN_OPS[@]}"
    for index in "${!ACAS_RUN_OPS[@]}"; do
      rendered="${ACAS_RUN_OP_STATUS[$index]-$ACAS_RUN_OP_NOT_RUN}"
      printf 'operation\t%s\t%s\t%s\n' \
        "$(( index + 1 ))" "${ACAS_RUN_OPS[$index]}" "$rendered"
    done
  } | acas_publish_atomic "$ACAS_RUN_OP_STATUS_FILE" 'the per-operation status record' \
    || return 0

  acas_log 'per-operation dispositions (the operations own status, NOT this script exit code):'
  for index in "${!ACAS_RUN_OPS[@]}"; do
    acas_log "$(printf '  %d. %-16s status %s' \
      "$(( index + 1 ))" "${ACAS_RUN_OPS[$index]}" "${ACAS_RUN_OP_STATUS[$index]-$ACAS_RUN_OP_NOT_RUN}")"
  done
  return 0
}

acas_write_run_status() {
  local status="$1"

  # A DRY RUN ATTESTS NOTHING, AND WRITES NOTHING -- INCLUDING NOT DELETING.
  # `--dry-run' validates every precondition and prints the plan without spawning the
  # menu, then exits 0, and a bare status 0 is exactly what
  # [harness/dump_tables.py] reads as "the run succeeded". So no record is written
  # here, which is the whole of what this branch has to do.
  #
  # DELETING ANY EXISTING RECORD HERE WOULD BE DEFENSIBLE AS FAR AS IT GOES: a real
  # record from a previous run of the same scenario survives, and would go on attesting
  # whatever capture is taken next. But `rm' is a WRITE, and it destroys the most
  # expensive artifact in the tree -- the evidence that a completed run produced. A mode
  # that promises to touch nothing cannot keep a hidden exception, and that exception
  # would be the worst one available.
  #
  # So the hazard is REPORTED instead. That is the honest half of the trade: it
  # leaves the operator's own artifact alone and tells them exactly what taking a
  # capture now would attest. [harness/run_python_scenario.sh] does the same, for the
  # same reason -- one model of `--dry-run' across the harness, not two.
  #
  # The path is resolved here rather than taken on trust, for the case where a dry
  # run failed before stage 3 named it.
  if (( ACAS_RUN_DRY_RUN )); then
    local dry_target="$ACAS_RUN_STATUS_FILE"
    if [[ -z "$dry_target" && -n "$ACAS_RUN_SCENARIO" && -n "${ACAS_OUT-}" ]]; then
      dry_target="$ACAS_OUT/run-logs/$ACAS_RUN_SCENARIO/cobol.run-status"
    fi
    printf 'note: --dry-run drove nothing, so no run-status record is written and\n' >&2
    printf '      nothing on disk was created, changed or removed.\n' >&2
    if [[ -n "$dry_target" && -f "$dry_target" && ! -L "$dry_target" ]]; then
      printf 'WARNING: a run-status record from an EARLIER run of this scenario is still\n' >&2
      printf '         present, and it has been left exactly as it was:\n' >&2
      printf '           %s\n' "$dry_target" >&2
      printf '         A capture taken by hand now would carry THAT run attestation, not\n' >&2
      printf '         this dry run. Re-run without --dry-run, or remove the record\n' >&2
      printf '         yourself, before taking one.\n' >&2
    fi
    return 0
  fi

  [[ -n "$ACAS_RUN_STATUS_FILE" ]] || return 0
  [[ -f "$ACAS_RUN_STATUS_FILE" && ! -L "$ACAS_RUN_STATUS_FILE" ]] || return 0

  # A signal handler's decision outranks `$?'. See acas_on_signal for why: bash runs
  # the EXIT trap after a fatal signal with `$?' holding the status of the last
  # command that completed, which is usually zero, so trusting it here would attest
  # a killed run as a successful one.
  if (( ACAS_RUN_SIGNAL_STATUS != 0 )); then
    status="$ACAS_RUN_SIGNAL_STATUS"
  fi

  local digest=''
  if [[ -f "$ACAS_RUN_FINGERPRINT" && ! -L "$ACAS_RUN_FINGERPRINT" ]]; then
    digest="$(sha256sum -- "$ACAS_RUN_FINGERPRINT" 2>/dev/null | cut -d' ' -f1)" || digest=''
  fi

  # `status' is retained under its original name because every existing reader
  # requires it, and it is now stated for what it always was: WRAPPER HEALTH. It is
  # published beside `wrapper_status', an explicit alias, and beside the ordered
  # per-operation dispositions -- so a reader can no longer take one for the other
  # without saying so.
  local index rendered
  {
    printf 'scenario\t%s\n' "$ACAS_RUN_SCENARIO"
    printf 'side\tcobol\n'
    printf 'run_id\t%s\n' "$ACAS_RUN_RUN_ID"
    printf 'status\t%s\n' "$status"
    printf 'wrapper_status\t%s\n' "$status"
    printf 'seed_fingerprint_sha256\t%s\n' "$digest"
    printf 'seed_marker_sha256\t%s\n' "$ACAS_RUN_SEED_IDENTITY"
    printf 'operations\t%s\n' "${#ACAS_RUN_OPS[@]}"
    for index in "${!ACAS_RUN_OPS[@]}"; do
      rendered="${ACAS_RUN_OP_STATUS[$index]-$ACAS_RUN_OP_NOT_RUN}"
      printf 'operation_status\t%s\t%s\t%s\n' \
        "$(( index + 1 ))" "${ACAS_RUN_OPS[$index]}" "$rendered"
    done
  } | acas_publish_atomic "$ACAS_RUN_STATUS_FILE" 'the run-status record' || {
    printf 'WARNING: the run-status record at %s was not published; the capture stage\n' \
      "$ACAS_RUN_STATUS_FILE" >&2
    printf '         will treat this run as unattested, which is the safe direction.\n' >&2
    return 0
  }
  return 0
}

# shellcheck disable=SC2317  # reached only through the EXIT trap installed below,
# which shellcheck cannot follow; the body is live and is exercised by every
# non-zero exit path.
acas_on_exit() {
  local status="$1"
  # FIRST, unconditionally, and before the status is even examined.
  acas_release_lock
  # SECOND, also unconditionally: the run-status record must exist for a success
  # and for every failure, because its whole purpose is to let a later stage
  # distinguish the two.
  acas_write_run_status "$status"
  if (( status == 0 )); then
    return 0
  fi
  if (( ACAS_RUN_DRIVEN )); then
    printf '\nharness/run_cobol_scenario.sh exiting with status %s AFTER the compiled cycle\n' \
      "$status" >&2
    printf 'was driven, so the database may hold a PARTIAL result. Run harness/reset_db.sh\n' >&2
    printf 'and harness/seed.sh before drawing any conclusion from a state diff.\n' >&2
    if (( ACAS_RUN_OP_INDEX >= 0 && ${#ACAS_RUN_OPS[@]} > 1 )); then
      printf 'It was driving operation %s of %s (%s) when it stopped, so operations\n' \
        "$(( ACAS_RUN_OP_INDEX + 1 ))" "${#ACAS_RUN_OPS[@]}" "$ACAS_RUN_OPERATION" >&2
      printf 'before it had already completed and their effects are in the database too.\n' >&2
    fi
    if (( ACAS_RUN_LOG_OPEN )); then
      printf 'The pty transcript is at: %s\n' "$ACAS_RUN_LOG" >&2
    fi
  else
    printf '\nharness/run_cobol_scenario.sh exiting with status %s. The compiled cycle was\n' \
      "$status" >&2
    printf 'never started, so the database is untouched.\n' >&2
  fi
  acas_tee "harness/run_cobol_scenario.sh exiting with status $status (driven=$ACAS_RUN_DRIVEN)"
}
trap 'acas_on_exit "$?"' EXIT

# SIGNALS -- AND WHY THE DEFAULT DISPOSITION WAS NOT GOOD ENOUGH.
#
# With no handler installed, a SIGTERM terminates this shell and bash still runs the
# EXIT trap on the way out -- but `$?' at that moment is the status of the last
# command that COMPLETED, which during a long drive is routinely ZERO. The
# run-status record therefore said `status 0' for a run somebody had killed, and
# [harness/dump_tables.py] read that as a successful run and attested a capture of a
# database the cycle had only partly written. That is the identical silent pass the
# attestation exists to close, arriving through the one door nobody watches. The
# handler records the real status, and acas_write_run_status prefers it.
#
# IT ALSO STOPS THE DRIVER, which the default disposition did not. On the
# wall-clock-deadline path `timeout' signals the whole process group, so the pty
# driver and the compiled menu both get TERM and the driver's own handler flushes the
# transcript. On a MANUAL kill of this script only this pid is signalled, so the
# driver, the menu it spawned, and every write that menu still had to make were left
# running -- while this script's EXIT trap released the sequential run lock, so the
# next run could start against a database an orphan was still writing to. Signalling
# the driver here makes the two interruption paths behave the same: the driver
# flushes its evidence, the menu goes with it, and the lock is released only once
# nothing is still writing.
#
# 128+signum is the status a shell reports for a signalled child, so a caller sees
# the same encoding it would have seen without a handler.
# shellcheck disable=SC2317  # reached only through the signal traps installed below.
acas_on_signal() {
  local status="$1" name="$2"
  ACAS_RUN_SIGNAL_STATUS="$status"
  printf '\nharness/run_cobol_scenario.sh received %s; stopping.\n' "$name" >&2
  if (( ACAS_RUN_DRIVER_PID > 0 )) && kill -0 "$ACAS_RUN_DRIVER_PID" 2>/dev/null; then
    printf 'Signalling the pty driver (pid %s) so it flushes its transcript and the\n' \
      "$ACAS_RUN_DRIVER_PID" >&2
    printf 'compiled menu stops with it.\n' >&2
    kill -TERM "$ACAS_RUN_DRIVER_PID" 2>/dev/null || true
    # Bounded, because a handler must not become the hang it is cleaning up after.
    # The driver's own deadline wrapper escalates to KILL, so nothing survives this
    # indefinitely even if the wait gives up first.
    local waited=0
    while kill -0 "$ACAS_RUN_DRIVER_PID" 2>/dev/null && (( waited < 10 )); do
      sleep 1
      waited=$(( waited + 1 ))
    done
    if kill -0 "$ACAS_RUN_DRIVER_PID" 2>/dev/null; then
      printf 'The driver has not stopped after %ss; its own deadline wrapper will KILL it.\n' \
        "$waited" >&2
    fi
  fi
  exit "$status"
}
trap 'acas_on_signal 130 SIGINT' INT
trap 'acas_on_signal 143 SIGTERM' TERM
trap 'acas_on_signal 129 SIGHUP' HUP


acas_usage() {
  # The delimiter is USAGE_EOF and not USAGE, because the text below uses
  # "USAGE" as a section heading on a line of its own and that would end the
  # here-document early -- silently truncating the help and leaving the rest to.
  cat <<'USAGE_EOF'
harness/run_cobol_scenario.sh -- drive the COMPILED ACAS Cobol posting cycle.

Stage 2 of the TEN-stage parity protocol (README section 8 drives it by hand,
tests/conftest.py composes it):
    reset+seed -> run(COBOL) -> dump -> normalise -> reset+re-seed ->
    run(Python) -> dump -> normalise -> verify published -> diff
The canonical stage list is harness/normalize.py; print it with
`harness/normalize.py --print-stages'. The AAP's eight logical stages
(section 0.3.2) become those ten by making both normalisations and the
publication check explicit.
STAGE IS NOT CHECK. The numbered `Check n/8' headings this script prints below
are its OWN preflight checks, eight of them, and they are NOT protocol stages.
They are spelled `Check' rather than `Stage' or `Step' precisely so the two
countings cannot be confused: `Check 8/8' is the keystroke plan, not the parity
diff, which is protocol stage 10 and belongs to harness/diff_states.py.

This is the ORACLE side. It drives the four compiled MENU executables over a
pty, because every in-scope posting program is a CALLed sub-program with
group-item linkage and therefore cannot be invoked from a shell at all.

USAGE
    harness/run_cobol_scenario.sh [OPTIONS] [<scenario-file>]

OPTIONS
    --scenario NAME        Scenario name. Defaults to the scenario file's
                          basename without its extension.
    --scenario-file PATH   Scenario definition. Same as the positional form,
                          which exists for the canonical invocation in
                          harness/docker-compose.yml.
    --subsystem NAME       One of: general sales purchase irs.
                          Optional -- it is derived from each operation, and is
                          cross-checked against EVERY operation to be driven. A
                          scenario spanning two menus cannot be constrained with
                          it at all.
    --operation NAME       REPEATABLE, and driven in the order given. One of the
                          seven operations of the posting cycle, named as
                          acas_posting/cli/ names them:
                              gl_post_cycle      general, load08 via "H"
                              gl_end_of_cycle    general, load09 via "I"
                              sl_invoice_post    sales,    load07 via "G"
                              sl_cash_post       sales,    load11 via "K"
                              pl_order_post      purchase, load08 via "H"
                              pl_payment_post    purchase, load12 via "L"
                              irs_post           irs,      option "4" then "66"
                          When it is not given, the operations come from the
                          scenario file's ordered `operations:' list, or failing
                          that from its singular `operation:' key -- the same
                          precedence harness/run_python_scenario.sh applies, so
                          both sides of the comparison resolve one list from one
                          file. EVERY declared operation is driven, in order, in
                          this single invocation, and each one's own observed
                          disposition is published to
                          <run-logs>/<scenario>/cobol.operation-status. That
                          record, and NOT this script's exit status, is what says
                          what the compiled cycle decided: the exit status is
                          wrapper health.
    --timeout SECONDS      Per-PROMPT timeout. Default 120. Must be > 0 and
                          finite: every interaction in this script is a hang
                          risk, and a hang is worse than a failure because it
                          looks like progress. This bounds ONE screen; the whole
                          driver is bounded separately by ACAS_TIMEOUT_DRIVE,
                          because "this screen never arrived" and "the driver as
                          a whole never finished" are different failures.
    --log PATH             Transcript destination. Default
                          $ACAS_OUT/run-logs/<scenario>/cobol.log, which is
                          deliberately OUTSIDE the compared tree.
                          The path is CANONICALISED (symlinks resolved, relative
                          paths anchored at the cwd) and then refused if it, or
                          any parent it would create, lands inside the frozen
                          checkout ACAS_REPO or inside any tree this protocol
                          compares -- <scenario>, /cobol, /python, /cobol.norm,
                          /python.norm. A symlinked leaf is refused outright, and
                          containment is re-checked AFTER mkdir -p, because mkdir
                          follows symlinks along the way. A transcript written
                          into a compared tree would be diffed as though it were
                          posted data and would corrupt the parity evidence.
    --rotate-fh-log        Move fh-logger.txt aside BEFORE the run. This is the
                          DEFAULT; the flag is accepted for compatibility. The log
                          is MOVED, never truncated, to
                          $ACAS_OUT/run-logs/<scenario>/fh-logger.pre-run.txt.NNN --
                          outside every compared tree, numbered so nothing is ever
                          overwritten. The logging switch itself is frozen on at
                          [copybooks/Test-Data-Flags.cob] `SW-Testing value 1'
                          and is never "fixed" (R-4).
    --no-rotate-fh-log     Append to the existing fh-logger.txt instead. Use only
                          when one continuous log across several runs is wanted:
                          the log has been measured growing 473 MB in about three
                          minutes, and a volume that fills MID-RUN leaves the
                          database half-posted with no diagnostic naming the cause.
    --dry-run              Resolve and print the keystroke plan, run every
                          precondition, and stop without spawning a menu.
    -h, --help             This text.

SCENARIO KEYS THIS STAGE READS
    run_date_text          The pinned date, exactly as typed, e.g. 21/09/2025.
    run_date_binary        The expected SYSTEM-REC.RUN-DAT after Date Entry.
    date_form              1 UK dd/mm/yyyy, 2 USA mm/dd/yyyy, 3 yyyy/mm/dd.
    irs_instead            The three-state fan-out switch: "" or " " for General
                           Ledger only, "Y" for IRS instead, "B" for IRS as well.
                           IRS-Instead is a pic x, so the GL-only state is a
                           space; both spellings of it are accepted. The key must
                           be PRESENT even so -- a default would leave the
                           affected-table list ambiguous.
    subsystem, operation   Defaults for the matching options.
    affected_tables        The table list that BOUNDS the comparison. Required,
                          and the same key harness/dump_tables.py reads.
    irs_clear_postings     G-1. "Y" or "N". Required for irs_post.
    gl080_proceed          G-2. "Y" proceeds, "A" aborts. Default "Y".
    disk_change_option     REQUIRED for gl_end_of_cycle. The GL084 answer
                           [general/gl080.cbl:L545-L549]. Only "0" is accepted:
                           this leg cannot drive "9" provably, because `a' is
                           `pic 99' [general/gl080.cbl:L183] and because 9 exits
                           the section before the accept that would consume the
                           Return. Refused rather than guessed at.
    archive_path_override  REFUSED by this leg. The frozen prompt is an UPDATE
                           accept [general/gl080.cbl:L555] whose replace-versus-
                           insert behaviour is unmeasured and, while the prompt
                           is unreachable in every fixture, unmeasurable. Omit
                           the key to take the frozen default of no override.
    payment_post_confirm   G-3. "YES" or "NO". Required for sl_cash_post and
                          pl_payment_post: neither program's prompt has a default
                          (both blank the reply field and re-ask on a blank), so
                          the scenario must state the answer.

ENVIRONMENT
    ACAS_DB_NAME           MUST be exactly "ACASDB". This stage drives a
                          DESTRUCTIVE posting cycle against whatever schema it is
                          pointed at, and the schema name is the only thing
                          distinguishing the harness database from a real one.
                          Every other schema name is refused before the database
                          is contacted at all.
    ACAS_DB_NAME/_USER     Additionally required to be plain SQL identifiers, so
                          neither can carry a quote, a backquote or a semicolon
                          into a composed statement.
    ACAS_TIMEOUT_CLIENT    Seconds allowed for one mysql client invocation.
                          Default 30.
    ACAS_TIMEOUT_DRIVE     Seconds allowed for the WHOLE pty driver process.
                          Default 3600. Complements --timeout, which bounds one
                          prompt: a driver that answers every screen promptly and
                          still never returns is only caught here.
    ACAS_TIMEOUT_ROTATE    Seconds allowed for the fh-logger rotation move.
                          Default 300. The log reaches hundreds of megabytes, so
                          the move is not instantaneous and a stalled filesystem
                          must not hang the run before it starts.
    ACAS_TIMEOUT_GRACE     Seconds between TERM and KILL for any command that
                          overruns its deadline. Default 15. Only the exact child
                          this script spawned is ever signalled.
                          Every ACAS_TIMEOUT_* value must be a whole number of
                          seconds from 1 to 86400, read base-ten so a leading zero
                          is not octal; leave it unset or empty to take the
                          default. A malformed value is a usage error, never a
                          silently dropped deadline.
    ACAS_FH_LOG_BUDGET_MB  Free space required on the filesystem holding
                          $ACAS_DATA before the run starts. Default 1024. The
                          frozen logging switch cannot be turned off and the log
                          has been measured growing 473 MB in about three
                          minutes, so capacity is checked BEFORE the database is
                          touched -- a volume that fills mid-cycle leaves a
                          half-posted database, which is the one failure this
                          protocol cannot diff its way out of.
OPTIONAL ENVIRONMENT
    ACAS_DB_ALLOWED_SCHEMAS   Comma- or space-separated extra schema names this
                          stage may inspect. ACAS_DB_NAME is embedded in an
                          information_schema query, so it must be a plain SQL
                          identifier AND appear on this allow-list; ACASDB is
                          permitted by default. An explicit declaration is
                          preferred to an implicit default because it is
                          auditable.
    ACAS_DB_TLS_CA=PATH   PEM bundle the server certificate chains to. When set,
                          the readiness and schema queries connect with
                          --ssl-ca AND --ssl-verify-server-cert, so both the
                          certificate and the hostname are checked; encrypting
                          without verifying accepts any certificate and is not
                          verification at all.
    ACAS_DB_ALLOW_PLAINTEXT=1
                          Declare that the target really is an isolated harness
                          network -- the private Compose network
                          [harness/docker-compose.yml] -- and permit plaintext
                          to it. Only 1, y, yes, true and on count; anything
                          else is a typo and is treated as "not declared".
                          A loopback host (127.0.0.1, ::1, localhost) or a
                          non-empty ACAS_DB_SOCKET needs neither, because those
                          never leave the machine. Any OTHER host with no CA and
                          no declaration is REFUSED before anything connects:
                          the credential here is the one the Cobol itself uses.

EXIT CODES
    0   the cycle was driven and every assertion passed
    70  usage error -- including a malformed ACAS_TIMEOUT_* budget
    71  a precondition failed
    72  the database is unreachable or the schema is absent
    73  autocommit is off -- the seeding window is still open, and the frozen
        COBOL never reaches a COMMIT, so this run's writes would be discarded at
        session close and the capture would be empty
    74  a compiled artifact is missing -- run harness/build_oracle.sh
    75  the scenario file is missing, unreadable, does not parse as a YAML
        mapping, or is incomplete. The parse check is deliberately separate from
        the value extraction, so a malformed document is reported as a malformed
        document rather than as "no operation was named" -- which points at the
        command line when the fault is in the file. [harness/seed.sh] and
        [harness/run_python_scenario.sh] report the same fault the same way.
    76  the driver timed out, spun, or saw a screen refusal
    77  a post-run assertion failed
    78  a bounded command overran its deadline. Distinct from 76: 76 is the
        driver's own verdict about a screen, 78 means a deadline expired and
        the command was killed, so no verdict was reached at all. The pty
        driver preserves its evidence on this path: it flushes the transcript
        and its outcome record from a signal handler before it goes, and the
        record then carries an `interrupted' line saying why, so the screen the
        cycle had reached is still readable afterwards.
    79  insufficient free space for the frozen fh-logger. Nothing was run and
        the database was not contacted.
    90  the target is not a proven harness-owned disposable database. Driving
        this cycle POSTS, and the schema NAME proves nothing -- the frozen
        mysql/ACASDB.sql gives every ACAS installation the name ACASDB -- so the
        server must declare itself disposable through @@report_host, or the exact
        target must be named in ACAS_RUN_ACKNOWLEDGE_DESTRUCTIVE. Same number and
        same meaning in [harness/reset_db.sh] and
        [harness/run_python_scenario.sh].

ARTIFACTS, all under $ACAS_OUT/run-logs/<scenario>/ and all mode 0600, none of
them inside any tree the diff stage compares:
    cobol.log               the pty transcript, escape sequences stripped
    cobol.plan              the resolved keystroke plan
    cobol.result            the driver's machine-readable outcome record
    cobol.seed-fingerprint  one <table><TAB><row count><TAB><sha256> line per
                            table the scenario names, in its declared order --
                            which includes SYSTEM-REC, the parameter row the menu
                            exit persists on every route. That row is dumped like
                            any other, with its two credential cells withheld by
                            [harness/dump_tables.py], and fingerprinted here as
                            well because a digest compares even those. Recorded
                            immediately before the drive. The digest is
                            taken over the canonical dump by
                            [harness/dump_tables.py --table-digest], the SAME producer the
                            Python side invokes, and it is what makes the record
                            mean anything: two seeds differing in one balance
                            have identical row counts.
                            [harness/run_python_scenario.sh] compares its own
                            record with this file and refuses to proceed if they
                            differ, so the two cycles cannot silently be handed
                            different starting states. Any fingerprint left by an
                            earlier run is removed at the start of this one, so
                            "absent" always means "this run did not get that
                            far".
    cobol.post-fingerprint  the same record, taken immediately AFTER the drive.
                            The pair answers a question no table diff can: did
                            this run change anything? Two runs that did nothing
                            agree perfectly, so without it a no-op could satisfy
                            a parity or a determinism claim.
    cobol.run-status        scenario, side, this script's exit status and the
                            digest of the fingerprint. Written from the EXIT
                            trap, so it exists for every termination path.
                            [harness/dump_tables.py] records it as an
                            attestation in the dump manifest and
                            [harness/diff_states.py] refuses to compare two
                            captures unless both sides attest success -- which
                            is what stops a failed run from being reported as
                            an empty, and therefore "identical", diff.

This script never exits 0 unconditionally. The frozen build scripts do --
[comp-all.sh:L45] and [common/comp-common.sh:L59] -- and they are NOT fixed;
their shape is simply not adopted here.
USAGE_EOF
}

acas_parse_args() {
  local positional=''
  while (( $# > 0 )); do
    case "$1" in
      -h|--help)
        acas_usage
        exit "$EX_OK"
        ;;
      --scenario)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--scenario requires a name.'
        ACAS_RUN_SCENARIO="$2"
        shift 2
        ;;
      --scenario=*)
        ACAS_RUN_SCENARIO="${1#*=}"
        shift
        ;;
      --scenario-file)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--scenario-file requires a path.'
        ACAS_RUN_SCENARIO_FILE="$2"
        shift 2
        ;;
      --scenario-file=*)
        ACAS_RUN_SCENARIO_FILE="${1#*=}"
        shift
        ;;
      --subsystem)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--subsystem requires a name.'
        ACAS_RUN_SUBSYSTEM_REQUESTED="$2"
        shift 2
        ;;
      --subsystem=*)
        ACAS_RUN_SUBSYSTEM_REQUESTED="${1#*=}"
        shift
        ;;
      # REPEATABLE, and in the order given. It matches
      # harness/run_python_scenario.sh's own --operation exactly, so a caller can
      # drive both sides of the comparison with the same argument list.
      --operation)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--operation requires a name.'
        ACAS_RUN_OPS+=("$2")
        shift 2
        ;;
      --operation=*)
        ACAS_RUN_OPS+=("${1#*=}")
        shift
        ;;
      --run-id)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--run-id requires an identifier.'
        ACAS_RUN_RUN_ID="$2"
        shift 2
        ;;
      --run-id=*)
        ACAS_RUN_RUN_ID="${1#*=}"
        shift
        ;;
      --timeout)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--timeout requires a number of seconds.'
        ACAS_RUN_TIMEOUT="$2"
        shift 2
        ;;
      --timeout=*)
        ACAS_RUN_TIMEOUT="${1#*=}"
        shift
        ;;
      --log)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--log requires a path.'
        ACAS_RUN_LOG="$2"
        shift 2
        ;;
      --log=*)
        ACAS_RUN_LOG="${1#*=}"
        shift
        ;;
      --rotate-fh-log)
        # Retained so an existing invocation that asks for the default keeps
        # working.
        ACAS_RUN_ROTATE_FH_LOG=1
        shift
        ;;
      --no-rotate-fh-log)
        ACAS_RUN_ROTATE_FH_LOG=0
        shift
        ;;
      --dry-run)
        ACAS_RUN_DRY_RUN=1
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
        if [[ -n "$positional" ]]; then
          acas_die "$EX_USAGE" \
            "at most one scenario file may be given; got '$positional' and '$1'."
        fi
        positional="$1"
        shift
        ;;
    esac
  done

  # Anything after `--' is the scenario file, at most one.
  while (( $# > 0 )); do
    if [[ -n "$positional" ]]; then
      acas_die "$EX_USAGE" "unexpected trailing arguments: $(acas_join_words "$@")"
    fi
    positional="$1"
    shift
  done

  if [[ -n "$positional" ]]; then
    if [[ -n "$ACAS_RUN_SCENARIO_FILE" && "$ACAS_RUN_SCENARIO_FILE" != "$positional" ]]; then
      acas_die "$EX_USAGE" \
        'the scenario file was given twice with different values.' \
        "--scenario-file said '$ACAS_RUN_SCENARIO_FILE', the positional said '$positional'."
    fi
    ACAS_RUN_SCENARIO_FILE="$positional"
  fi

  [[ "$ACAS_RUN_TIMEOUT" =~ ^[0-9]+$ ]] || acas_die "$EX_USAGE" \
    "--timeout must be a whole number of seconds; got '$ACAS_RUN_TIMEOUT'."
  (( ACAS_RUN_TIMEOUT > 0 )) || acas_die "$EX_USAGE" \
    '--timeout must be greater than zero.' \
    'Every interaction with the menus is a hang risk, so a timeout of zero -- meaning' \
    'no timeout at all -- is refused: a hang looks like progress and is worse than a' \
    'failure.'
}

# =============================================================================
# THE SCENARIO DOCUMENT -- READ BY THE SAME PARSER THE PYTHON RUNNER USES
#
# ONE PARSER, NOT TWO
#
# Three hand-written `awk' programs would do this: recognise a top-level `key:' line with
# no leading whitespace, strip an unquoted trailing comment, unquote a value and collect a
# block or flow list. Careful, well-commented and wrong for the job, because the job is
# not "read a
# few scalars". The job is: RECEIVE EXACTLY WHAT THE OTHER SIDE OF THE COMPARISON
# RECEIVED. harness/run_python_scenario.sh read the same file with PyYAML. Two
# readers over one document, on a protocol whose entire premise is that both legs
# are handed identical inputs, is a correctness defect and not a matter of taste:
#
#   * an anchor and an alias (`&batch' / `*batch') are values to a parser and
#     literal text to a line matcher;
#   * a merge key (`<<:') expands to real keys for one side and to nothing for the
#     other;
#   * a flow mapping (`{a: 1}') is a block for one and a scalar for the other;
#   * a block scalar (`description: |') is one value for one side and a stream of
#     unrecognised lines for the other;
#   * a key written twice is a hard error to the parser and last-one-wins to awk;
#   * a tab-indented list is a parse failure to one and invisible to the other.
#
# In every one of those cases the protocol would still have produced a verdict, and
# the verdict would have been about two different scenarios. Worse, PyYAML was
# treated as OPTIONAL here -- a missing parser "degraded" to the awk reader -- so
# the divergence was reachable by having one package uninstalled.
#
# So the parser lives in harness/normalize.py --scenario-stream, both runners invoke it, and it
# is a HARD REQUIREMENT: status 3 (no PyYAML) is a refusal, not a degradation.
# The accessor names below are unchanged, so every call site reads exactly as it
# did; only what is underneath them changed.
#
# The stream is TAB-delimited, one record per line, in document order:
#     K <TAB> key                 present at top level, whatever its value
#     S <TAB> key <TAB> value     a scalar
#     L <TAB> key <TAB> value     one list item, in file order
#     G <TAB> key                 a nested block, RECORDED and not read
# =============================================================================

# `_' and `-' are interchangeable in a key name: every key is normalised to `_' on
# both sides of the lookup, which is the same tolerance the Python runner and the
# capture stage extend.
declare -A ACAS_RUN_YAML_PRESENT=()
declare -A ACAS_RUN_YAML_SCALAR=()
declare -A ACAS_RUN_YAML_LIST=()
declare -A ACAS_RUN_YAML_GROUP=()

# The keys THIS runner reads. A scenario legitimately carries more -- the nested
# `clock:', `system:' and `seed:' blocks that document the seeded state, and the
# `seed_dir:'/`seed_files:' pair harness/seed.sh reads -- and a block under a key
# this runner never reads is left alone, exactly as the Python runner leaves it. A
# block under a key it DOES read is refused, because that value would read as empty
# and change the run without saying so: for the fan-out switch
# [copybooks/wssystem.cob:L179-L181], or for the affected-table list that BOUNDS
# the comparison, silence is the most expensive failure available here.
readonly ACAS_RUN_SCENARIO_KEYS=(
  scenario
  name
  subsystem
  operation
  operations
  run_date_text
  run_date_binary
  date_form
  irs_instead
  irs_clear_postings
  payment_post_confirm
  gl080_proceed
  disk_change_option
  archive_path_override
  ws_caller
  affected_tables
  expected_table_effect
  expected_status
)

# Emit the stream for one file. Stdin is detached: the reader takes a path and must
# never be able to wait on a terminal.
acas_scenario_stream() {
  [[ -f "$ACAS_RUN_SCENARIO_READER" ]] || {
    printf 'the shared scenario reader is missing: %s\n' "$ACAS_RUN_SCENARIO_READER" >&2
    printf 'It is harness/normalize.py --scenario-stream and it ships beside this\n' >&2
    printf 'script; both runners read every scenario through it so that one document\n' >&2
    printf 'cannot mean two things.\n' >&2
    return 4
  }
  acas_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  "${ACAS_DEADLINE_ARGV[@]}" python3 "$ACAS_RUN_SCENARIO_READER" \
    --scenario-stream "$1" < /dev/null
}

# Read the document into the four arrays. Any failure is FATAL: this stage takes
# the operation, the subsystem, the pinned clock, every answer and the
# affected-table list from that document, so a document it could not read is a run
# with no inputs.
acas_read_scenario() {
  local file="$1" rc=0 stream='' started elapsed
  started="$SECONDS"
  stream="$(acas_scenario_stream "$file")" || rc=$?
  elapsed=$(( SECONDS - started ))
  acas_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_CLIENT" \
    ACAS_TIMEOUT_CLIENT 'reading the scenario file'

  case "$rc" in
    0) : ;;
    3)
      acas_die "$EX_SCENARIO" \
        'PyYAML is not importable by this interpreter, so the scenario cannot be read.' \
        'This is a REFUSAL and not a degradation. Falling back to a hand-written' \
        'reader when the parser is missing would let the two legs' \
        'of the comparison read one document by two different rules, decided by' \
        'which packages happened to be installed. A verdict reached that way is about' \
        'two different scenarios.' \
        '  install it the way every other environment in this project installs it:' \
        '    pip install --require-hashes -r requirements.txt' \
        '  which pins PyYAML 6.0.3 and verifies every artifact against a recorded' \
        '  hash. Do NOT install the one package unpinned or unhashed: the parser is' \
        '  what decides how BOTH legs of the comparison read a scenario, so an' \
        '  unverified build of it is an unverified premise for every verdict below.' \
        '  Or run this stage inside the harness image, which installs from that same' \
        '  hash-verified lock at build time and already carries it.'
      ;;
    4)
      acas_die "$EX_SCENARIO" \
        "the scenario file could not be read: $file" \
        'The reader printed the reason above.'
      ;;
    5)
      acas_die "$EX_SCENARIO" \
        "the scenario file is not a usable YAML document: $file" \
        'The reader printed the reason above. It requires a mapping at top level' \
        'whose values are scalars, flat lists of scalars, or nested blocks it records' \
        'without reading. A real number is refused outright: no scenario value is a' \
        'real number and rule R-2 forbids binary floating point from entering the' \
        'comparison by accident.' \
        'The scenario definitions live under harness/scenarios/.'
      ;;
    *)
      acas_die "$EX_SCENARIO" \
        "the shared scenario reader exited $rc, which is not one of its documented statuses." \
        "  file: $file" \
        '  documented: 0 read, 3 no PyYAML, 4 unreadable, 5 not a usable document.'
      ;;
  esac

  local kind key value
  while IFS=$'\t' read -r kind key value; do
    case "$kind" in
      '') continue ;;
      K)  ACAS_RUN_YAML_PRESENT["$key"]=1 ;;
      G)  ACAS_RUN_YAML_GROUP["$key"]=1 ;;
      S)  ACAS_RUN_YAML_SCALAR["$key"]="$value" ;;
      L)
        if [[ -n "${ACAS_RUN_YAML_LIST[$key]+set}" ]]; then
          ACAS_RUN_YAML_LIST["$key"]="${ACAS_RUN_YAML_LIST[$key]}"$'\n'"$value"
        else
          ACAS_RUN_YAML_LIST["$key"]="$value"
        fi
        ;;
      *)
        acas_die "$EX_SCENARIO" \
          "the scenario reader emitted an unrecognised record kind '$(acas_sanitise_field "$kind")'."
        ;;
    esac
  done <<< "$stream"

  acas_assert_scenario_shape
  acas_log 'scenario read by harness/normalize.py --scenario-stream -- the same parser the Python runner uses'
}

# Refused HERE, in the main shell, where a refusal can still stop the run: the
# accessors are called inside command substitutions, where an exit would end only
# the subshell and the run would carry on with an empty value -- exactly the
# silence this check exists to prevent.
acas_assert_scenario_shape() {
  (( ${#ACAS_RUN_YAML_GROUP[@]} > 0 )) || return 0
  local key
  for key in "${!ACAS_RUN_YAML_GROUP[@]}"; do
    if acas_in_list "$key" "${ACAS_RUN_SCENARIO_KEYS[@]}"; then
      acas_die "$EX_SCENARIO" \
        "the scenario declares '$(acas_sanitise_field "$key")' as a nested block, and this runner reads that key." \
        '  A key this runner reads must carry a scalar, or a flat list of scalars, so' \
        '  that what the author wrote is what the run receives. As a block it would' \
        '  read as empty and change the run without saying so.' \
        '  State the value at top level; a block under a key this runner does not' \
        '  read -- clock, system, seed -- is perfectly fine and is left alone.'
    fi
  done
}

# True when the key appeared at top level at all, whatever its value. Needed
# because an EMPTY value is meaningful for the fan-out switch and must never be
# confused with the key having been forgotten [copybooks/wssystem.cob:L179-L181].
acas_scenario_has_key() {
  [[ -n "${ACAS_RUN_YAML_PRESENT[${1//-/_}]+set}" ]]
}

# The scalar value, or nothing when the key is absent or carries a list.
acas_scenario_scalar() {
  local key="${1//-/_}"
  if [[ -n "${ACAS_RUN_YAML_SCALAR[$key]+set}" ]]; then
    printf '%s' "${ACAS_RUN_YAML_SCALAR[$key]}"
  fi
}

# The list items, one per line, in file order. A single scalar where a list was
# expected is emitted as a one-item list rather than silently dropped -- the same
# tolerance the Python runner extends, so one scenario file serves both.
acas_scenario_list() {
  local key="${1//-/_}"
  if [[ -n "${ACAS_RUN_YAML_LIST[$key]+set}" ]]; then
    printf '%s\n' "${ACAS_RUN_YAML_LIST[$key]}"
    return 0
  fi
  if [[ -n "${ACAS_RUN_YAML_SCALAR[$key]+set}" && -n "${ACAS_RUN_YAML_SCALAR[$key]}" ]]; then
    printf '%s\n' "${ACAS_RUN_YAML_SCALAR[$key]}"
  fi
}

# The scalar value, or the fallback when it is absent or empty.
acas_scenario_default() {
  local value
  value="$(acas_scenario_scalar "$1")"
  if [[ -n "$value" ]]; then
    printf '%s' "$value"
  else
    printf '%s' "$2"
  fi
}


# STAGE 1 -- resolve the scenario, the operation and the subsystem.
#
# The document is read by harness/normalize.py --scenario-stream (see THE SCENARIO DOCUMENT
# above), so there is no separate "is this really YAML?" check any more: a document
# that does not parse produces no values at all and acas_read_scenario refuses it
# with the SAME exit code harness/seed.sh and harness/run_python_scenario.sh use for
# the same fault, so one malformed scenario produces one diagnosis wherever the
# protocol first touches it.
acas_resolve_scenario() {
  ACAS_RUN_CURRENT_STAGE='resolving the scenario'
  acas_stage 'Check 1/8: scenario, operation and subsystem'

  if [[ -n "$ACAS_RUN_SCENARIO_FILE" ]]; then
    [[ -f "$ACAS_RUN_SCENARIO_FILE" ]] || acas_die "$EX_SCENARIO" \
      "scenario file not found: $ACAS_RUN_SCENARIO_FILE" \
      'Pass the path of a scenario definition file.'
    [[ -r "$ACAS_RUN_SCENARIO_FILE" ]] || acas_die "$EX_SCENARIO" \
      "scenario file is not readable: $ACAS_RUN_SCENARIO_FILE"
    acas_read_scenario "$ACAS_RUN_SCENARIO_FILE"
  fi

  if [[ -z "$ACAS_RUN_SCENARIO" ]]; then
    ACAS_RUN_SCENARIO="$(acas_scenario_scalar scenario)"
  fi
  if [[ -z "$ACAS_RUN_SCENARIO" && -n "$ACAS_RUN_SCENARIO_FILE" ]]; then
    ACAS_RUN_SCENARIO="${ACAS_RUN_SCENARIO_FILE##*/}"
    ACAS_RUN_SCENARIO="${ACAS_RUN_SCENARIO%.*}"
  fi
  [[ -n "$ACAS_RUN_SCENARIO" ]] || acas_die "$EX_USAGE" \
    'no scenario was named.' \
    'Give --scenario NAME, or a scenario file whose name or scenario: key supplies it.'
  [[ "$ACAS_RUN_SCENARIO" =~ ^[A-Za-z0-9_-]+$ ]] || acas_die "$EX_USAGE" \
    "the scenario name must be a plain identifier; got '$ACAS_RUN_SCENARIO'." \
    'It becomes a directory name under ACAS_OUT, so it may hold only letters,' \
    'digits, underscore and hyphen.'

  #  Before the id is DERIVED, because a derived id means a hand invocation and a
  #  supplied one means a protocol stage, and the two are permitted different options.
  acas_assert_no_evidence_bypass

  [[ -n "$ACAS_RUN_RUN_ID" ]] || ACAS_RUN_RUN_ID="$(acas_derive_run_id)"
  acas_assert_run_id

  acas_resolve_operations
  acas_assert_operations_supported_by_both_sides

  acas_log "scenario   = $ACAS_RUN_SCENARIO"
  if [[ -n "$ACAS_RUN_SCENARIO_FILE" ]]; then
    acas_log "definition = $ACAS_RUN_SCENARIO_FILE"
  else
    acas_note 'no scenario file given; every pinned value must come from an option'
  fi
  acas_log "operations = $(acas_join_words "${ACAS_RUN_OPS[@]}")  (driven in this order, one at a time)"

  local index op
  for index in "${!ACAS_RUN_OPS[@]}"; do
    op="${ACAS_RUN_OPS[$index]}"
    acas_select_operation "$op"
    acas_log "$(printf '  %d. %-16s %-9s menu %-6s %s  [%s]' \
      "$(( index + 1 ))" "$op" "$ACAS_RUN_SUBSYSTEM" \
      "'$ACAS_RUN_MENU_KEY'" "$ACAS_RUN_PARAGRAPH" "$ACAS_RUN_PARAGRAPH_LOCATOR")"
  done
  # Leave the FIRST operation selected, so anything between here and the drive loop
  # that reads ACAS_RUN_OPERATION or ACAS_RUN_SUBSYSTEM sees a coherent pair.
  acas_select_operation "${ACAS_RUN_OPS[0]}"
}

# EVERY DECLARED OPERATION, IN THE DECLARED ORDER, IN ONE INVOCATION
#
# Reading the SINGULAR `operation:' key and nothing else would let a scenario declaring
# four ordered operations -- period_end_totals does, and it is the scenario whose whole
# subject is that all nine period-total write sites fire -- be driven only one operation
# per invocation. The protocol works
# around that by invoking this script four times and then COPYING the first
# invocation's seed fingerprint and run-status record over the last one's, because
# only one record could exist per side. The consequence was precise and bad:
# operations 2, 3 and 4 had NO ATTESTED DISPOSITION AT ALL. Their term codes were
# never recorded, so nothing downstream could tell a clean run of four operations
# from a clean run of one followed by three that aborted.
#
# The ordering is not presentation. period_end_totals' own definition states why:
# operation 3 conditions state that operation 4 reads [purchase/pl060.cbl:L373-L375],
# operations 1 and 3 establish the ledger rows that 2 and 4 rewrite, and anomaly
# A-17's write [sales/sl060.cbl:L1173] is read back as a batch start in a LATER
# operation [purchase/pl100.cbl:L564]. Reordering the list changes what that read
# returns.
#
# Precedence is identical to harness/run_python_scenario.sh's, so the two sides
# cannot resolve different lists from one file: repeated --operation first, then the
# file's ordered `operations:' list, then its singular `operation:' key.
# EVERY DECLARED OPERATION MUST BE DRIVEABLE BY BOTH SIDES, CHECKED BEFORE STAGE 2 DRIVES ONE
#
# A parity verdict is only worth something if the two sides did the same work. The
# scenario's `operations:' list is the statement of that work, and each runner keeps
# its own map from an operation name to what it drives -- a compiled menu key on one
# side, a `python -m' module on the other. Nothing previously compared the two maps
# against the list, and the driver that came to do it is gone, so the
# check lives HERE -- in the first stage that drives an operation, and therefore the
# last moment before any state is produced. A hand-driven stage 2 is protected exactly
# as a composed one is, which a check in a separate driver could not promise.
#
# THE FAILURE IT PREVENTS IS SILENT AND EXPENSIVE. An operation present in one
# map and absent from the other makes the scenario undriveable on one side, and without
# this check it surfaces late: nine stages run, several minutes and two full seeds
# spent, and then stage 10 reports a table difference that is not a behavioural
# finding at all but a difference in how much work each side did. Read at face value
# it accuses the migration of a defect it does not have.
#
# THE MAPS ARE READ, NOT RESTATED. Both are `readonly -a' arrays in their own
# scripts, so this check greps the declarations out of the shipped files rather than
# holding a third copy that could drift from either. A third list would be one more
# thing to keep in step, which is the defect this check exists to catch.
# =============================================================================
acas_operation_names() {
  # $1 the script, $2 the array name, $3 the field separator of its rows.
  local script="$1" array="$2" sep="$3"
  sed -n "/^readonly -a ${array}=(/,/^)/p" -- "$script" \
    | sed -e '1d' -e '$d' \
    | sed -e "s/^[[:space:]]*'//" -e "s/'[[:space:]]*$//" \
    | awk -v FS="$sep" 'NF { print $1 }'
}

acas_assert_operations_supported_by_both_sides() {
  local cobol_script="$ACAS_RUN_HARNESS_DIR/run_cobol_scenario.sh"
  local python_script="$ACAS_RUN_HARNESS_DIR/run_python_scenario.sh"

  local -a cobol_ops=() python_ops=()
  mapfile -t cobol_ops < <(acas_operation_names \
    "$cobol_script" 'ACAS_RUN_OPERATION_MAP' ':')
  mapfile -t python_ops < <(acas_operation_names \
    "$python_script" 'ACAS_PY_OPERATION_MAP' '|')

  (( ${#cobol_ops[@]} > 0 )) || acas_die "$EX_PRECONDITION" \
    "could not read the operation map out of $cobol_script." \
    'It is a `readonly -a ACAS_RUN_OPERATION_MAP=(...)'"'"' block; this check reads' \
    'the shipped file rather than holding a third copy of the list.'
  (( ${#python_ops[@]} > 0 )) || acas_die "$EX_PRECONDITION" \
    "could not read the operation map out of $python_script." \
    'It is a `readonly -a ACAS_PY_OPERATION_MAP=(...)'"'"' block.'

  local operation found_cobol found_python name
  local -a unsupported=()
  for operation in "${ACAS_RUN_OPS[@]}"; do
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
    local -a refusal_lines=()
    for name in "${unsupported[@]}"; do
      refusal_lines+=("  $name")
    done
    acas_die "$EX_PRECONDITION" \
      "this scenario declares ${#unsupported[@]} operation(s) that the two sides do not both support." \
      "${refusal_lines[@]}" \
      'A parity verdict means the two sides did the SAME work, so an operation only' \
      'one side can drive makes the comparison meaningless -- and it would surface' \
      'as a table difference at stage 10, after two full seeds, looking exactly like' \
      'a behavioural defect in the migration. Refused here instead.' \
      "  compiled side drives: $(printf '%s ' "${cobol_ops[@]}")" \
      "  migrated side drives: $(printf '%s ' "${python_ops[@]}")"
  fi

  acas_log \
    "operations    = ${ACAS_RUN_OPS[*]}  (all ${#ACAS_RUN_OPS[@]} driveable by both sides)"
}


acas_resolve_operations() {
  local candidate

  if (( ${#ACAS_RUN_OPS[@]} == 0 )); then
    while IFS= read -r candidate; do
      [[ -n "$candidate" ]] && ACAS_RUN_OPS+=("$candidate")
    done < <(acas_scenario_list operations)
  fi
  if (( ${#ACAS_RUN_OPS[@]} == 0 )); then
    candidate="$(acas_scenario_scalar operation)"
    [[ -n "$candidate" ]] && ACAS_RUN_OPS+=("$candidate")
  fi
  (( ${#ACAS_RUN_OPS[@]} > 0 )) || acas_die "$EX_USAGE" \
    'no operation was named.' \
    'Give --operation (repeatable), or an operations: list in the scenario file,' \
    'or its singular operation: key.' \
    "The seven operations are: $(acas_join_words "${ACAS_RUN_OPERATIONS[@]}")."

  local op index seen_subsystem=''
  for index in "${!ACAS_RUN_OPS[@]}"; do
    op="${ACAS_RUN_OPS[$index]}"
    acas_in_list "$op" "${ACAS_RUN_OPERATIONS[@]}" || acas_die "$EX_USAGE" \
      "unknown operation '$(acas_sanitise_field "$op")' at position $(( index + 1 ))." \
      "The seven operations are: $(acas_join_words "${ACAS_RUN_OPERATIONS[@]}")." \
      'The set is identical to the seven entry points under acas_posting/cli/, so' \
      'the two sides of the comparison stay trivially comparable.'
    # Resolves the menu mapping and refuses an operation whose subsystem
    # contradicts --subsystem or the scenario's own subsystem: key.
    acas_select_operation "$op"
    seen_subsystem="$ACAS_RUN_SUBSYSTEM"

    if [[ "$ACAS_RUN_SCENARIO" == *control_total_mismatch* && "$seen_subsystem" != 'general' ]]; then
      acas_die "$EX_USAGE" \
        'the control_total_mismatch scenario is General-Ledger-specific.' \
        "Operation '$op' is dispatched by the $seen_subsystem menu." \
        'Sales and Purchase batches balance by construction, so an unbalanced batch' \
        'cannot meaningfully be built for them; the control-total gate that this' \
        'scenario exercises lives in the General Ledger batch proof at' \
        '[general/gl051.cbl:L1109-L1118].'
    fi
  done

  # One status slot per operation, pre-set to the sentinel that means "this
  # operation was never driven". It is NOT zero: zero is a real term code and would
  # attest a clean disposition for an operation that never ran.
  ACAS_RUN_OP_STATUS=()
  for index in "${!ACAS_RUN_OPS[@]}"; do
    ACAS_RUN_OP_STATUS+=("$ACAS_RUN_OP_NOT_RUN")
  done
}

# acas_select_operation <name>
# Make <name> the operation being driven: resolve its subsystem, menu letter and
# dispatch paragraph from the frozen map, and refuse any disagreement with
# --subsystem or with the scenario's own subsystem: key. Called once per operation
# during resolution and again immediately before each drive, so that every
# subsystem-dependent value -- the executable, the menu geometry, the plan builder
# -- is the one belonging to the operation about to run.
acas_select_operation() {
  local wanted="$1" entry name rest mapped_subsystem=''

  for entry in "${ACAS_RUN_OPERATION_MAP[@]}"; do
    name="${entry%%:*}"
    if [[ "$name" == "$wanted" ]]; then
      rest="${entry#*:}"
      mapped_subsystem="${rest%%:*}"
      rest="${rest#*:}"
      ACAS_RUN_MENU_KEY="${rest%%:*}"
      rest="${rest#*:}"
      ACAS_RUN_PARAGRAPH="${rest%%:*}"
      ACAS_RUN_PARAGRAPH_LOCATOR="${rest#*:}"
      break
    fi
  done
  [[ -n "$mapped_subsystem" ]] || acas_die "$EX_USAGE" \
    "internal: operation '$(acas_sanitise_field "$wanted")' has no menu mapping."

  # A scenario file may name the subsystem too. Every source must agree: a silent
  # override is exactly how a run ends up driving the wrong menu. An EMPTY
  # subsystem: key means "the file does not say", which is what period_end_totals
  # carries because it spans two menus -- so no single name could be true for all
  # four of its operations.
  local scenario_subsystem
  scenario_subsystem="$(acas_scenario_scalar subsystem)"
  if [[ -n "$scenario_subsystem" && "$scenario_subsystem" != "$mapped_subsystem" ]]; then
    acas_die "$EX_SCENARIO" \
      "the scenario file's subsystem does not match one of its operations." \
      "operation '$wanted' is dispatched by the $mapped_subsystem menu," \
      "but the file says subsystem '$(acas_sanitise_field "$scenario_subsystem")'." \
      'A file that spans two menus must leave subsystem: empty; naming either one' \
      'would make the operations of the other fail here rather than behaviourally.'
  fi
  if [[ -n "$ACAS_RUN_SUBSYSTEM_REQUESTED" && "$ACAS_RUN_SUBSYSTEM_REQUESTED" != "$mapped_subsystem" ]]; then
    acas_die "$EX_USAGE" \
      '--subsystem does not match one of the operations to be driven.' \
      "operation '$wanted' is dispatched by the $mapped_subsystem menu," \
      "but --subsystem said '$(acas_sanitise_field "$ACAS_RUN_SUBSYSTEM_REQUESTED")'." \
      'A scenario spanning two menus cannot be constrained with --subsystem at all.'
  fi

  ACAS_RUN_OPERATION="$wanted"
  ACAS_RUN_SUBSYSTEM="$mapped_subsystem"
  acas_in_list "$ACAS_RUN_SUBSYSTEM" "${ACAS_RUN_SUBSYSTEMS[@]}" || acas_die "$EX_USAGE" \
    "internal: unknown subsystem '$ACAS_RUN_SUBSYSTEM'."

  # The executable follows the subsystem, ALWAYS, and is set here so it cannot
  # drift from it. Assigning it once in acas_assert_oracle, which runs before the drive
  # loop, would have a scenario spanning two menus drive every operation with the FIRST
  # operation's menu. MEASURED: period_end_totals'
  # operation 3 is pl_order_post, and such a run launches /build/sales/sales and sends
  # the purchase menu letter "H" -- which on the Sales menu is (H) Payment Input,
  # so the run landed in SL080's interactive data-entry screen and never came back.
  # No diagnostic said the wrong program had been started; the only symptom was a
  # timeout at a screen the plan does not answer.
  acas_resolve_executable
}

# acas_resolve_executable
# $ACAS_BUILD/<subsystem>/<subsystem>, the `cobc -x' menu the maintainer's own
# per-directory script builds. Left EMPTY while ACAS_BUILD is still unset, because
# acas_resolve_scenario runs before acas_assert_environment and a half-formed path
# would be worse than no path: acas_assert_oracle re-derives it once the
# environment contract has been asserted, and the drive loop re-derives it again
# for every operation.
acas_resolve_executable() {
  if [[ -n "${ACAS_BUILD:-}" ]]; then
    ACAS_RUN_EXECUTABLE="$ACAS_BUILD/$ACAS_RUN_SUBSYSTEM/$ACAS_RUN_SUBSYSTEM"
  else
    ACAS_RUN_EXECUTABLE=''
  fi
}

# STAGE 2 -- the pinned values the scenario must supply Every one of these
# changes what the run writes, so none of them may be left to a default that
# happens to be whatever the database currently holds (R-6).
acas_resolve_pinned_values() {
  ACAS_RUN_CURRENT_STAGE='resolving the pinned scenario values'
  acas_stage 'Check 4/8: pinned run date, date form and switches'

  ACAS_RUN_DATE_TEXT="$(acas_scenario_scalar run_date_text)"
  [[ -n "$ACAS_RUN_DATE_TEXT" ]] || acas_die "$EX_SCENARIO" \
    'the scenario does not pin a run date.' \
    'Add a run_date_text: key, e.g. "21/09/2025".' \
    'The run date is not allowed to come from the host clock: two runs of one' \
    'scenario must produce byte-identical dumps (R-6), and the whole cycle takes' \
    'its date through linkage from the menu [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80].'
  [[ "$ACAS_RUN_DATE_TEXT" =~ ^[0-9]{2}/[0-9]{2}/[0-9]{4}$ || "$ACAS_RUN_DATE_TEXT" =~ ^[0-9]{4}/[0-9]{2}/[0-9]{2}$ ]] \
    || acas_die "$EX_SCENARIO" \
      "run_date_text must be ten characters in one of the three forms maps04 accepts; got '$ACAS_RUN_DATE_TEXT'." \
      'The field is u-date pic x(10) and the accept is ten characters wide at' \
      '[general/gl000.cbl:L238-L239]; the accepted separators and the six-part' \
      'reject test are at [common/maps04.cbl:L140-L146].'

  ACAS_RUN_RUN_DATE="$(acas_scenario_scalar run_date_binary)"
  [[ -n "$ACAS_RUN_RUN_DATE" ]] || acas_die "$EX_SCENARIO" \
    'the scenario does not pin the expected binary run date.' \
    'Add a run_date_binary: key -- the value SYSTEM-REC.RUN-DAT must hold after' \
    'Date Entry.' \
    'Without it a SILENTLY REJECTED date would leave the previous value in place' \
    'and every downstream comparison would run against the wrong date. maps04' \
    'returns its output field UNCHANGED on a bad date [common/maps04.cbl:L146],' \
    'so the only reliable check is to assert the value afterwards.'
  [[ "$ACAS_RUN_RUN_DATE" =~ ^[0-9]+$ ]] || acas_die "$EX_SCENARIO" \
    "run_date_binary must be a whole number; got '$ACAS_RUN_RUN_DATE'." \
    'It is Run-Date binary-long [copybooks/wssystem.cob:L67], column RUN-DAT.'

  # DATE-FORM selects which of three prompts the date program displays, and
  # therefore which digit order must be typed. Never assume UK order.
  ACAS_RUN_DATE_FORM="$(acas_scenario_default date_form 1)"
  case "$ACAS_RUN_DATE_FORM" in
    1|2|3) : ;;
    *)
      acas_die "$EX_SCENARIO" \
        "date_form must be 1, 2 or 3; got '$ACAS_RUN_DATE_FORM'." \
        '1 = UK dd/mm/yyyy, 2 = USA mm/dd/yyyy, 3 = International yyyy/mm/dd,' \
        'per the condition names at [copybooks/wssystem.cob:L128-L131]. The value' \
        'selects the prompt at [general/gl000.cbl:L230-L237].'
      ;;
  esac
  # Cross-check the typed order against the declared form, because the prompt
  # this script waits for is chosen from date_form.
  if [[ "$ACAS_RUN_DATE_FORM" == '3' && ! "$ACAS_RUN_DATE_TEXT" =~ ^[0-9]{4}/ ]]; then
    acas_die "$EX_SCENARIO" \
      "date_form 3 expects yyyy/mm/dd but run_date_text is '$ACAS_RUN_DATE_TEXT'."
  fi
  if [[ "$ACAS_RUN_DATE_FORM" != '3' && "$ACAS_RUN_DATE_TEXT" =~ ^[0-9]{4}/ ]]; then
    acas_die "$EX_SCENARIO" \
      "date_form $ACAS_RUN_DATE_FORM expects a two-digit leading field but run_date_text is '$ACAS_RUN_DATE_TEXT'."
  fi

  # The three-state IRS fan-out switch.
  if acas_scenario_has_key irs_instead; then
    ACAS_RUN_IRS_INSTEAD="$(acas_scenario_scalar irs_instead)"
    # IRS-Instead is `pic x' [copybooks/wssystem.cob:L179], and a pic x holds a
    # SPACE for the General-Ledger-only state -- Cobol has no empty string for
    # a single-character alphanumeric field, and neither condition name.
    ACAS_RUN_IRS_INSTEAD="${ACAS_RUN_IRS_INSTEAD// /}"
  elif [[ -n "$ACAS_RUN_SCENARIO_FILE" ]]; then
    acas_die "$EX_SCENARIO" \
      'the scenario does not pin the IRS fan-out switch.' \
      'Add an irs_instead: key. It is three-state at [copybooks/wssystem.cob:L179-L181]:' \
      '    ""  General Ledger only  (a pic x holding a space; " " is accepted too)' \
      '    "Y" IRS instead of the General Ledger  (88 IRS-Used)' \
      '    "B" IRS as well as the General Ledger  (88 IRS-Both-Used)' \
      'It is tested at 27 sites across the four Sales and Purchase posting' \
      'programs, e.g. [sales/sl060.cbl:L1039], [sales/sl060.cbl:L1126] and' \
      '[sales/sl060.cbl:L1175], so it decides WHICH TABLES the run touches. Use' \
      'irs_instead: "" or irs_instead: " " to select General Ledger only -- the' \
      'key must be PRESENT either way, because a default would leave the' \
      'affected-table list ambiguous.'
  fi
  case "$ACAS_RUN_IRS_INSTEAD" in
    ''|'Y'|'B') : ;;
    *)
      acas_die "$EX_SCENARIO" \
        "irs_instead must be \"\" (or \" \"), \"Y\" or \"B\"; got '$ACAS_RUN_IRS_INSTEAD'." \
        'IRS-Instead is a pic x whose only condition names are "Y" (IRS-Used) and' \
        '"B" (IRS-Both-Used); any other content means General Ledger only.' \
        'See [copybooks/wssystem.cob:L179-L181].'
      ;;
  esac

  if acas_ops_include 'irs_post'; then
    ACAS_RUN_IRS_CLEAR="$(acas_scenario_scalar irs_clear_postings)"
    [[ -n "$ACAS_RUN_IRS_CLEAR" ]] || acas_die "$EX_SCENARIO" \
      'the scenario does not answer irs030 end-of-job question.' \
      'Add an irs_clear_postings: key with "Y" or "N".' \
      'Despite the "[Y]" hint an EMPTY reply is NOT accepted --' \
      '[irs/irs030.cbl:L1718-L1719] loops until Y or N -- so leaving it unset would' \
      'spin forever. And the answer changes table state: "Y" performs' \
      'acas008-Open-Output, which the handler turns into a DELETE-ALL of' \
      'PSIRSPOST-REC [common/acas008.cbl:L313-L318], [common/acas008.cbl:L568-L574].'
    ACAS_RUN_IRS_CLEAR="${ACAS_RUN_IRS_CLEAR^^}"
    case "$ACAS_RUN_IRS_CLEAR" in
      Y|N) : ;;
      *)
        acas_die "$EX_SCENARIO" \
          "irs_clear_postings must be Y or N; got '$ACAS_RUN_IRS_CLEAR'." \
          'The accept is with ... UPPER at [irs/irs030.cbl:L1717] and the test at' \
          'L1718 admits nothing else.'
        ;;
    esac
  fi

  if acas_ops_include 'gl_end_of_cycle'; then
    # REQUIRED, not defaulted -- symmetrically with the migrated leg.
    #
    # This leg types a keystroke rather than passing an option, so it cannot launder
    # an omission into "consent explicitly stated" the way the migrated leg could.
    # The reason it must still require the key is the OTHER half of the same rule: the
    # scenario is the single statement of what both legs were driven with. If one leg
    # accepted silence and supplied 'Y' while the other refused it, the scenario would
    # no longer say what the run did -- and the answer decides whether gl080 writes
    # anything at all [general/gl080.cbl:L295-L302]. Costs nothing: the only scenario
    # selecting this operation declares it.
    ACAS_RUN_GL080_PROCEED="$(acas_scenario_scalar gl080_proceed)"
    [[ -n "$ACAS_RUN_GL080_PROCEED" ]] || acas_die "$EX_SCENARIO" \
      'the scenario selects gl_end_of_cycle but does not declare gl080_proceed.' \
      'It is the pre-run backup gate [general/gl080.cbl:L295-L302]: "A" or Escape' \
      'means goback and gl080 writes nothing; anything else proceeds. Not defaulted' \
      'here because the migrated leg does not default it either -- the scenario is' \
      'the single statement of what BOTH legs were driven with, and a value this' \
      'harness invented would make that statement untrue.' \
      'Add to the scenario:  gl080_proceed: "Y"   (or "A" to abort before any write)'
    ACAS_RUN_GL080_PROCEED="${ACAS_RUN_GL080_PROCEED^^}"
    case "$ACAS_RUN_GL080_PROCEED" in
      Y|A) : ;;
      *)
        acas_die "$EX_SCENARIO" \
          "gl080_proceed must be Y (proceed) or A (abort); got '$ACAS_RUN_GL080_PROCEED'." \
          'The gate is [general/gl080.cbl:L295-L302]: GL085/GL086/GL087 then' \
          'accept keyed-reply at 1065 with update auto, and Escape or "A"/"a"' \
          'means goback -- gl080 writes nothing. Any other keystroke proceeds,' \
          'and the Cobol default immediately before the accept is `move space to' \
          'keyed-reply`, so "Y" here is sent as a bare Return to reproduce that' \
          'default exactly rather than to type a letter the program never tests.'
        ;;
    esac

    # -------------------------------------------------------------------------
    #  THIS LEG NOW READS THE DISK-CHANGE ANSWER INSTEAD OF ASSUMING IT.
    #
    #  `disk_change_option' and `archive_path_override' were both on this script's
    #  KNOWN-KEY list and neither was ever READ. The GL084 plan step hard-coded `0'.
    #  So a scenario declaring 9 was accepted here, honoured by the migrated leg as
    #  --disk-change-option 9, and contradicted by this leg typing 0 -- two legs
    #  driven with different logical inputs, and a diff between them measuring the
    #  disagreement rather than the accounting (R-6).
    #
    #  REQUIRED rather than defaulted, matching the migrated leg: the answer
    #  decides whether the archiving walk, every batch stamp, every posting delete,
    #  the ledger-quarter rollover and the cycle increment happen at all
    #  [general/gl080.cbl:L406-L409], [general/gl080.cbl:L324-L326].
    # -------------------------------------------------------------------------
    ACAS_RUN_DISK_CHANGE="$(acas_scenario_scalar disk_change_option)"
    [[ -n "$ACAS_RUN_DISK_CHANGE" ]] || acas_die "$EX_SCENARIO" \
      'the scenario selects gl_end_of_cycle but does not declare disk_change_option.' \
      'It is the GL084 answer [general/gl080.cbl:L545-L549]. Not defaulted here,' \
      'because the migrated leg does not default it either: a value this harness' \
      'invented would be driven into one leg as a decision nobody made, and the' \
      'two legs must be given the SAME logical inputs or the diff means nothing.' \
      'Add to the scenario:  disk_change_option: "0"'
    case "$ACAS_RUN_DISK_CHANGE" in
      0) : ;;
      9)
        # ---------------------------------------------------------------------
        #  REFUSED, NOT SILENTLY DOWNGRADED -- the second branch of the same rule
        #  ("reject unsupported keys and keep the ambiguity open") applied
        #  deliberately rather than as a shortcut.
        #
        #  THE KEYSTROKE SEMANTICS ARE NOW MEASURED; THE JOURNEY IS STILL NOT,
        #  AND THE REFUSAL RESTS ON THE SECOND. Both halves that were open when
        #  this refusal was written have been answered (2026-08-08), by a
        #  standalone probe carrying the frozen declaration
        #  `77 a pic 99 value zero' [general/gl080.cbl:L183] and the frozen
        #  statement `accept a at 1369' [general/gl080.cbl:L545], compiled by this
        #  image's own cobc 3.2.0 and driven over a real 24x80 pty:
        #
        #  1. A single keystroke 9 stores 09, NOT 90 -- the runtime right-justifies
        #     the numeric field on termination even though the screen renders 90
        #     while it is being typed -- so `if a = 9' [general/gl080.cbl:L546]
        #     DOES fire and 9 does abort.
        #  2. The Return IS consumed by the accept that took the digit, so nothing
        #     stays buffered for a following prompt.
        #
        #  What remains unreachable is the SECTION, not the semantics:
        #  `disk-change' is reached only from `gl080b', which runs only when
        #  SYSTEM-REC.Arch = "Y" [general/gl080.cbl:L315],
        #  [copybooks/wssystem.cob:L164-L165], and no fixture seeds that. Reaching
        #  it would mean this harness inventing seed state (R-3), so there is no
        #  compiled JOURNEY to capture and compare.
        #
        #  So it is still refused HERE, where the divergence would be introduced.
        #  Refusing costs nothing real: no scenario declares 9, and the protocol
        #  stops at this stage rather than producing a verdict from a run only one
        #  leg could make. Recorded, with the measurement, as
        #  Q-GL084-ACCEPT-SEMANTICS in docs/migration/ambiguity-resolutions.md.
        # ---------------------------------------------------------------------
        acas_die "$EX_SCENARIO" \
          'disk_change_option: "9" cannot be driven through this leg provably, so it is refused.' \
          'The migrated leg implements 9 and this one would have to type it at' \
          '[general/gl080.cbl:L545]. The KEYSTROKE SEMANTICS are measured' \
          '(2026-08-08, a standalone cobc 3.2.0 probe over a real pty): a single 9' \
          'stores 09 rather than 90, so `if a = 9` [general/gl080.cbl:L546] fires,' \
          'and the Return is consumed rather than left buffered.' \
          'What is still missing is a compiled JOURNEY to compare against: the' \
          'prompt is reached only when SYSTEM-REC.Arch = "Y"' \
          '[general/gl080.cbl:L315] and no fixture seeds that, and seeding one' \
          'would be this harness inventing state (R-3).' \
          'A capture the oracle cannot match is not evidence, so it is refused' \
          'rather than driven on one leg only (R-6).' \
          'Use disk_change_option: "0". The measurement is recorded under' \
          'Q-GL084-ACCEPT-SEMANTICS' \
          'in docs/migration/ambiguity-resolutions.md.'
        ;;
      *)
        acas_die "$EX_SCENARIO" \
          "disk_change_option must be 0 or 9; got '$ACAS_RUN_DISK_CHANGE'." \
          'Anything that is neither is sent straight back to the prompt by' \
          '[general/gl080.cbl:L548-L549], so no other value can leave the loop.'
        ;;
    esac

    #  The archive path override, refused for the same reason and on the same terms.
    #  [general/gl080.cbl:L555] is `accept file-2 ... with update' -- an UPDATE field
    #  pre-loaded with the path the program just built at
    #  [general/gl080.cbl:L530-L537]. Whether typed text REPLACES that content or is
    #  INSERTED into it was measured on 2026-08-08 and is NEITHER: it OVERWRITES IN
    #  PLACE from position 1, leaving the tail, and a bare Return leaves the field
    #  unchanged. The migrated leg now reproduces exactly that. The refusal stands
    #  on the same ground as the option above -- the section is unreachable in every
    #  fixture, so there is no compiled journey to compare a capture against.
    ACAS_RUN_ARCHIVE_PATH="$(acas_scenario_scalar archive_path_override)"
    [[ -z "$ACAS_RUN_ARCHIVE_PATH" ]] || acas_die "$EX_SCENARIO" \
      'archive_path_override cannot be driven through this leg provably, so it is refused.' \
      'The frozen prompt is `accept file-2 ... with update` at' \
      '[general/gl080.cbl:L555]: an UPDATE field already holding the path built at' \
      '[general/gl080.cbl:L530-L537]. Its edit semantics are MEASURED (2026-08-08):' \
      'typed text OVERWRITES IN PLACE from position 1 and leaves the tail, and a' \
      'bare Return leaves the field unchanged. The migrated leg reproduces that.' \
      'What is still missing is a compiled JOURNEY: the prompt is unreachable in' \
      'every fixture (it needs SYSTEM-REC.Arch = "Y" [general/gl080.cbl:L315]), so' \
      'a capture here would have nothing to be compared with.' \
      'Remove the key to take the frozen default, which is no override. The' \
      'measurement is recorded under' \
      'Q-GL084-ACCEPT-SEMANTICS in docs/migration/ambiguity-resolutions.md.'
  fi

  # G-3 -- sl100 / pl100 YES/NO before posting. REQUIRED, exactly as G-1 is, and
  # for the same reason: the frozen prompt has NO default, so a default here would
  # be this harness inventing the answer rather than reproducing one. Both
  # programs blank the reply field immediately before the accept
  # [sales/sl100.cbl:L313], [purchase/pl100.cbl:L305] - so the `update` phrase
  # pre-fills spaces - and both re-ask on a blank [sales/sl100.cbl:L318-L319],
  # [purchase/pl100.cbl:L310-L311]. The Python leg demands the answer too: the
  # --ok-to-post/--no-ok-to-post pair on both routes is argparse-required, and
  # neither programs/sl100_cash_posting.run nor
  # programs/pl100_payment_posting.run carries a default for it. Both legs of the
  # comparison therefore take the answer from the scenario and neither invents it.
  if acas_ops_include 'sl_cash_post' || acas_ops_include 'pl_payment_post'; then
    ACAS_RUN_PAYMENT_CONFIRM="$(acas_scenario_scalar payment_post_confirm)"
    [[ -n "$ACAS_RUN_PAYMENT_CONFIRM" ]] || acas_die "$EX_SCENARIO" \
      'the scenario does not answer the payment-posting confirmation.' \
      'Add a payment_post_confirm: key with "YES" or "NO".' \
      'An EMPTY reply is NOT accepted by either program -- wx-reply is blanked at' \
      '[sales/sl100.cbl:L313] and [purchase/pl100.cbl:L305] and a blank re-asks at' \
      '[sales/sl100.cbl:L318-L319] and [purchase/pl100.cbl:L310-L311] -- so there' \
      'is no default to fall back on, and the answer decides whether anything is' \
      'posted at all: NO transfers to menu-exit before the first file is opened.' \
      'The Python leg requires the same answer as --ok-to-post/--no-ok-to-post.'
    ACAS_RUN_PAYMENT_CONFIRM="${ACAS_RUN_PAYMENT_CONFIRM^^}"
    case "$ACAS_RUN_PAYMENT_CONFIRM" in
      YES|NO) : ;;
      *)
        acas_die "$EX_SCENARIO" \
          "payment_post_confirm must be YES or NO; got '$ACAS_RUN_PAYMENT_CONFIRM'." \
          'Both programs loop on anything else -- [sales/sl100.cbl:L316-L318] and' \
          '[purchase/pl100.cbl:L309-L311] -- and NO means go to menu-exit, so' \
          'nothing is posted. The prompt WORDING differs between the two programs' \
          'and that divergence is preserved, not harmonised (R-4).'
        ;;
    esac
  fi

  local -a tables=()
  mapfile -t tables < <(acas_scenario_list affected_tables)
  if (( ${#tables[@]} == 0 )); then
    mapfile -t tables < <(acas_scenario_list affected-tables)
  fi
  if (( ${#tables[@]} == 0 )); then
    if [[ -n "$ACAS_RUN_SCENARIO_FILE" ]]; then
      acas_die "$EX_SCENARIO" \
        'the scenario does not list its affected tables.' \
        'Add an affected_tables: key -- the same key harness/dump_tables.py reads.' \
        'It is required, not optional: it is the DECLARED EFFECT this script asserts' \
        'against after the run. The comparison itself is bounded by all 22 in-scope' \
        'tables, because leaving the menu with "X" rewrites SYSTEM-REC and SYSTOT-REC,' \
        'plus SYSDEFLT-REC in the General menu only [general/general.cbl:L656-L672]' \
        'vs [sales/sales.cbl:L628-L657], and the Python side REPRODUCES that in' \
        'acas_posting/cli/args.py::overrewrite -- so those rows are comparable and' \
        'must not be bounded away. Neither list is an ignore-list; diff_states.py' \
        'has none.'
    fi
    acas_note 'no affected-table list available; post-run table assertions will be skipped'
  else
    local table
    for table in "${tables[@]}"; do
      acas_in_list "$table" "${ACAS_RUN_INSCOPE_TABLES[@]}" || acas_die "$EX_SCENARIO" \
        "affected_tables names '$table', which is not one of the 22 in-scope tables." \
        "The in-scope tables are: $(acas_join_words "${ACAS_RUN_INSCOPE_TABLES[@]}")."
      # Written as an `if' and not as `acas_in_list ...
      if (( ${#ACAS_RUN_TABLES[@]} > 0 )) && acas_in_list "$table" "${ACAS_RUN_TABLES[@]}"; then
        acas_die "$EX_SCENARIO" "affected_tables names '$table' more than once."
      fi
      ACAS_RUN_TABLES+=("$table")
    done
  fi
  acas_resolve_fingerprint_tables

  acas_log "run date   = $ACAS_RUN_DATE_TEXT  (date_form $ACAS_RUN_DATE_FORM)"
  acas_log "expected SYSTEM-REC.RUN-DAT = $ACAS_RUN_RUN_DATE"
  case "$ACAS_RUN_IRS_INSTEAD" in
    '')  acas_log 'IRS fan-out = "" -- General Ledger only' ;;
    'Y') acas_log 'IRS fan-out = "Y" -- IRS instead of the General Ledger  (88 IRS-Used)' ;;
    'B') acas_log 'IRS fan-out = "B" -- IRS as well as the General Ledger  (88 IRS-Both-Used)' ;;
  esac
  [[ -z "$ACAS_RUN_IRS_CLEAR" ]] || \
    acas_log "G-1 irs030 clear postings file = $ACAS_RUN_IRS_CLEAR"
  [[ -z "$ACAS_RUN_GL080_PROCEED" ]] || \
    acas_log "G-2 gl080 pre-run gate        = $ACAS_RUN_GL080_PROCEED"
  [[ -z "$ACAS_RUN_PAYMENT_CONFIRM" ]] || \
    acas_log "G-3 payment post confirmation = $ACAS_RUN_PAYMENT_CONFIRM"
  if (( ${#ACAS_RUN_TABLES[@]} > 0 )); then
    acas_log "affected tables ($((${#ACAS_RUN_TABLES[@]}))) = $(acas_join_words "${ACAS_RUN_TABLES[@]}")"
  fi

  if acas_ops_include 'irs_post' && (( ${#ACAS_RUN_TABLES[@]} > 0 )); then
    acas_in_list 'PSIRSPOST-REC' "${ACAS_RUN_TABLES[@]}" || acas_die "$EX_SCENARIO" \
      'an irs_post scenario must list PSIRSPOST-REC in affected_tables.' \
      "irs_clear_postings is '$ACAS_RUN_IRS_CLEAR', and that answer changes the" \
      'contents of PSIRSPOST-REC [common/acas008.cbl:L313-L318]. Leaving the table' \
      'out of the comparison would make a genuine, pinned input invisible to the diff.'
  fi
}



# =============================================================================
# SYSTEM-REC IS DECLARED, DUMPED AND FINGERPRINTED ON EVERY SCENARIO.
#
# The menu exit persists it. `overrewrite' rewrites key 1 on all four subsystems --
# [general/general.cbl:L656-L672], [sales/sales.cbl:L628-L641],
# [purchase/purchase.cbl:L621-L634], [irs/irs.cbl:L759-L774] -- and the migrated
# command line reproduces that paragraph rather than skipping it
# [acas_posting/cli/args.py]. So SYSTEM-REC is written by BOTH cycles on every route,
# and a difference in what they write is a real behavioural difference. Leaving it
# outside every bound is what let a system-state regression produce an empty diff.
#
# It is therefore on every scenario's affected-table list and in every capture. The one
# problem a dump does have is solved where it arises rather than by dropping the table:
#
#   1. THE ROW CARRIES TWO CREDENTIALS. `RDBMS-PASSWD char(12)' [mysql/ACASDB.sql] is a
#      SYSTEM-REC column [copybooks/wssystem.cob:L139], and so is `PASS-WORD'. A dump is
#      `SELECT *' and a capture is committed evidence, so harness/dump_tables.py
#      withholds exactly those two cells -- `REDACTED_COLUMNS' applied inside
#      `render_value', keyed by (table, column), identical on both sides and therefore
#      incapable of producing a difference of its own. The other 167 columns are compared
#      by value. Bounding the whole table out instead would have taken those 167 with it,
#      and a bound drawn that way cannot reveal a difference in what it excludes.
#
#   2. THE EFFECT CLAIM IS NOT, IN FACT, COUPLED TO FIELDS NO SCENARIO REASONS ABOUT.
#      `expected_table_effect: unchanged' is the whole assertion of the empty-batch and
#      rejection scenarios -- that the journey touched NOTHING -- and SYSTEM-REC's content
#      does depend on what the route DID: the run-date stamp, the IRS allocator, the
#      one-shot latches, and `Date-Form', which the frozen date sections write back
#      [copybooks/wssystem.cob:L127]. So the objection was MEASURED rather than argued:
#      the row's digest HOLDS on all four scenarios declaring `unchanged' and MOVES on
#      every one declaring `changed'. That was measured over the eight committed
#      scenarios, which is all four `unchanged' ones; it was also measured on a ninth,
#      end_of_cycle_gl, which declared `changed' and moved the row by construction, its
#      Phase 5 advancing the cycle and rotating the quarter counter -- that scenario has
#      since been removed and the observation is recorded here
#      because it is what established the `changed' half of the claim. Declaring the row
#      falsifies no effect claim, and reason 1 is handled by redaction not exclusion.
#
# The fingerprint is kept ANYWAY, because it gives what a dump cannot: the seed
# cross-check proves both sides STARTED from the same 169-column row, the pre/post pair
# proves whether each side CHANGED it, and tests/conftest.py compares the two sides'
# post-run digests -- a second, independent parity check over every column INCLUDING the
# two the capture withholds, with nothing to leak, because a sha256 of the canonical dump
# is not the dump. A scenario that declares the row gets it fingerprinted in its declared
# position; one that does not gets it appended after the declared order, so the two sides'
# records stay byte-comparable either way.
# =============================================================================
acas_resolve_fingerprint_tables() {
  ACAS_RUN_FINGERPRINT_TABLES=()
  if (( ${#ACAS_RUN_TABLES[@]} == 0 )); then
    return 0
  fi
  ACAS_RUN_FINGERPRINT_TABLES=("${ACAS_RUN_TABLES[@]}")
  if ! acas_in_list "$ACAS_RUN_PARAMETER_TABLE" "${ACAS_RUN_FINGERPRINT_TABLES[@]}"; then
    ACAS_RUN_FINGERPRINT_TABLES+=("$ACAS_RUN_PARAMETER_TABLE")
  fi
  acas_log "fingerprinted tables ($((${#ACAS_RUN_FINGERPRINT_TABLES[@]}))) = $(acas_join_words "${ACAS_RUN_FINGERPRINT_TABLES[@]}")"
}

# STAGE 3 -- the environment contract.
acas_assert_environment() {
  ACAS_RUN_CURRENT_STAGE='asserting the environment contract'
  acas_stage 'Check 2/8: environment'

  local name
  for name in "${ACAS_RUN_REQUIRED_ENV_NONEMPTY[@]}"; do
    if [[ -z "${!name:-}" ]]; then
      acas_die "$EX_PRECONDITION" \
        "$name is unset or empty." \
        'The harness environment is published by harness/docker-compose.yml,' \
        'which also documents the canonical invocation.'
    fi
  done
  for name in "${ACAS_RUN_REQUIRED_ENV_DECLARED[@]}"; do
    if ! declare -p "$name" >/dev/null 2>&1 && [[ -z "${!name+x}" ]]; then
      acas_die "$EX_PRECONDITION" \
        "$name is not declared." \
        'It may legitimately be EMPTY -- the harness connects over TCP -- but it must' \
        'be declared, because the Cobol side reads a socket path out of the RDB-Data' \
        'block at [copybooks/wsfnctn.cob:L56-L62].'
    fi
  done

  # The Cobol host-variable widths are hard limits, not conventions.
  acas_assert_width ACAS_DB_NAME 12
  acas_assert_width ACAS_DB_USER 12
  acas_assert_width ACAS_DB_PASSWORD 12
  acas_assert_width ACAS_DB_HOST 32
  acas_assert_width ACAS_DB_PORT 5
  if [[ -n "${ACAS_DB_SOCKET:-}" ]]; then
    acas_assert_width ACAS_DB_SOCKET 64
  fi
  # THE RANGE, not merely the character class.
  [[ "$ACAS_DB_PORT" =~ ^[0-9]+$ ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_DB_PORT must be numeric; got '$(acas_sanitise_field "$ACAS_DB_PORT")'."
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
  # Canonicalised so the port this script reports, probes and hands the client
  # is one value rather than several spellings of it.
  ACAS_DB_PORT="$(( 10#$ACAS_DB_PORT ))"

  # The schema name is embedded in an information_schema query, so it is
  # validated and escaped here rather than at the query site.
  acas_assert_schema_name

  # Decided HERE, before the readiness probe, and not lazily on first use --
  # see acas_assert_transport_policy for why the ordering matters.
  acas_assert_transport_policy

  # The schema name is composed into SQL text and passed to the client, so it
  # is restricted to a plain identifier here -- refused rather than escaped --
  # before anything can build a statement from it.
  acas_assert_sql_identifier 'ACAS_DB_NAME' "$ACAS_DB_NAME"
  acas_assert_sql_identifier 'ACAS_DB_USER' "$ACAS_DB_USER"

  # And it must be THE schema.
  if [[ "$ACAS_DB_NAME" != "$ACAS_RUN_REQUIRED_SCHEMA" ]]; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_NAME is '$ACAS_DB_NAME', not '$ACAS_RUN_REQUIRED_SCHEMA'." \
      'The frozen mysql/ACASDB.sql defines exactly one database and the compiled' \
      'cycle is driven against it. A different name means either the schema is' \
      'not there, or this run would post into a database that is not the one the' \
      'parity protocol compares -- and the resulting diff would be evidence of' \
      'nothing (R-6).' \
      'harness/docker-compose.yml and harness/Dockerfile.mariadb both supply' \
      "ACAS_DB_NAME=$ACAS_RUN_REQUIRED_SCHEMA."
  fi

  # [copybooks/Proc-Get-Env-Set-Files.cob:L20-L28] tests only character 1 of
  # each of these, so a value that BEGINS with a space is treated as absent and
  # the menu displays SY009, waits for a keystroke, and stops.
  for name in ACAS_LEDGERS ACAS_BIN; do
    if [[ "${!name}" == ' '* ]]; then
      acas_die "$EX_PRECONDITION" \
        "$name begins with a space." \
        '[copybooks/Proc-Get-Env-Set-Files.cob:L20-L28] tests only the first character,' \
        'so the menu would treat it as unset, display SY009 and SY008, wait for a' \
        'keystroke and stop run -- which from outside looks like a hung harness.'
    fi
  done

  # $ACAS_REPO is the read-only checkout. The frozen-artifact guarantee is
  # structural -- the mount is :ro -- but this script also simply never goes
  # there.
  [[ -d "$ACAS_REPO" ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_REPO is not a directory: $ACAS_REPO"
  [[ -d "$ACAS_BUILD" ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_BUILD is not a directory: $ACAS_BUILD" \
    'harness/build_oracle.sh creates it as a container-local cp -a copy of the' \
    'checkout, so that compiling can never touch the frozen tree.'
  [[ "$ACAS_BUILD" != "$ACAS_REPO" ]] || acas_die "$EX_PRECONDITION" \
    'ACAS_BUILD must not be the same directory as ACAS_REPO.' \
    'Building or running inside the checkout would risk a diff to a frozen file,' \
    'which AAP 0.8.1 treats as a defect "regardless of how harmless it appears".'
  [[ -d "$ACAS_DATA" ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_DATA is not a directory: $ACAS_DATA" \
    'It is the working directory for the run and it holds system.dat and the flat files.'
  [[ -w "$ACAS_DATA" ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_DATA is not writable: $ACAS_DATA" \
    'The run happens there, and the file handler writes fh-logger.txt into the' \
    'process working directory [common/fhlogger.cbl:L111].'

  mkdir -p "$ACAS_OUT" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "cannot create ACAS_OUT: $ACAS_OUT"
  [[ -w "$ACAS_OUT" ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_OUT is not writable: $ACAS_OUT"

  # ACAS_BIN is the target of the CBL_CHECK_FILE_EXIST probe at
  # [general/general.cbl:L489-L503].
  if [[ ! -d "$ACAS_BIN" ]]; then
    mkdir -p "$ACAS_BIN" 2>/dev/null || acas_die "$EX_PRECONDITION" \
      "ACAS_BIN is not a directory and could not be created: $ACAS_BIN"
    acas_note "created ACAS_BIN so the backup-script probe takes the same branch every run"
  fi

  # python3 drives the pty. It is the ONLY option available.
  acas_have python3 || acas_die "$EX_PRECONDITION" \
    'python3 is not on PATH.' \
    'It drives the pty, using only the standard library (pty, termios, fcntl,' \
    'struct, select, signal, os, re). harness/Dockerfile.gnucobol provides it.'

  acas_log "ACAS_REPO  = $(acas_sanitise_field "$ACAS_REPO") (read-only; never written, never entered)"
  acas_log "ACAS_BUILD = $(acas_sanitise_field "$ACAS_BUILD")"
  acas_log "ACAS_DATA  = $(acas_sanitise_field "$ACAS_DATA") (working directory for the run)"
  acas_log "ACAS_OUT   = $(acas_sanitise_field "$ACAS_OUT")"
  acas_log "ACAS_BIN   = $(acas_sanitise_field "$ACAS_BIN")"
  # A CATEGORY and a FINGERPRINT, never the topology. This transcript is
  # retained evidence and is replayed to a container log, so the schema, host, port
  # and ACCOUNT NAME are deliberately absent from it. The fingerprint is the same
  # value harness/seed.sh, harness/reset_db.sh and harness/build_oracle.sh print for
  # one target, so two transcripts of one protocol run are still comparable.
  acas_log "database   = $(acas_target_description)"
  acas_note 'no account name, host, port or schema is printed: the transcript is retained evidence'
  acas_note 'the database password is never logged, never placed in argv and never written to disk'
}

acas_assert_width() {
  local name="$1" max="$2" value
  value="${!name:-}"
  if (( ${#value} > max )); then
    acas_die "$EX_PRECONDITION" \
      "$name is ${#value} characters; the Cobol host variable holds at most $max." \
      'The RDB-Data block is DB-Schema x(12), DB-UName x(12), DB-UPass x(12),' \
      'DB-Host x(32), DB-Socket x(64), DB-Port x(5) at' \
      '[copybooks/wsfnctn.cob:L56-L62]. A longer value is silently truncated by the' \
      'MOVE, so the Cobol would connect with a different credential than this' \
      'script just verified.'
  fi
}

# STAGE 4 -- open the transcript Deliberately under
# $ACAS_OUT/run-logs/<scenario>/ and NOT under $ACAS_OUT/<scenario>/.
acas_open_log() {
  ACAS_RUN_CURRENT_STAGE='opening the transcript'
  local dir
  if [[ -z "$ACAS_RUN_LOG" ]]; then
    dir="$ACAS_OUT/run-logs/$ACAS_RUN_SCENARIO"
    ACAS_RUN_LOG="$dir/cobol.log"
  else
    dir="${ACAS_RUN_LOG%/*}"
    if [[ "$dir" == "$ACAS_RUN_LOG" ]]; then
      dir='.'
    fi
  fi

  local compared="$ACAS_OUT/$ACAS_RUN_SCENARIO"
  local suggest="$ACAS_OUT/run-logs/$ACAS_RUN_SCENARIO/cobol.log"

  acas_assert_outside_repo '--log' "$ACAS_RUN_LOG"

  # The scenario tree itself, plus each raw and normalized side beneath it.
  local root
  for root in \
    "$compared" \
    "$compared/cobol" "$compared/python" \
    "$compared/cobol.norm" "$compared/python.norm"; do
    acas_assert_outside_tree '--log' "$ACAS_RUN_LOG" "$root" \
      'Everything under that tree is compared byte for byte between the COBOL and' \
      'Python cycles. This transcript records the host time the menu displays' \
      '[general/general.cbl:L556-L557], so including it would make every diff' \
      'non-empty and destroy the evidence the protocol depends on (R-6).' \
      "Use a path outside it; the default is $suggest"
  done

  # A symlinked leaf is refused outright rather than followed.
  if [[ -L "$ACAS_RUN_LOG" ]]; then
    acas_die "$EX_USAGE" \
      "--log is a symbolic link: $ACAS_RUN_LOG" \
      "  it points at: $(readlink -f -- "$ACAS_RUN_LOG" 2>/dev/null || printf '<unresolvable>')" \
      'The transcript is written to a real path so the evidence trail names where' \
      'the bytes actually are. Give the destination directly.'
  fi

  mkdir -p "$dir" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "cannot create the transcript directory: $dir"
  chmod 700 -- "$dir" 2>/dev/null || true

  acas_assert_outside_repo 'the transcript directory' "$dir"
  acas_assert_outside_tree 'the transcript directory' "$dir" "$compared" \
    "Use a path outside it; the default is $suggest"

  # ACAS_RUN_LOG_OPEN IS SET ONLY AFTER THE CREATE SUCCEEDS, and that ordering
  # is load-bearing rather than tidy.
  acas_create_private_file "$ACAS_RUN_LOG" 'the transcript'
  ACAS_RUN_LOG_OPEN=1

  local plan="$dir/cobol.plan"
  local result="$dir/cobol.result"
  acas_create_private_file "$plan" 'the keystroke plan'
  acas_create_private_file "$result" "the driver's outcome record"
  ACAS_RUN_PLAN_FILE="$plan"
  ACAS_RUN_RESULT_FILE="$result"

  # THE STALE-FINGERPRINT WINDOW, CLOSED HERE AND NOT LATER.
  # cobol.seed-fingerprint is written by acas_record_seed_fingerprint, immediately
  # before the drive; [harness/run_python_scenario.sh] reads it and REFUSES to
  # compare if the two sides started from different STATES -- rows and values both,
  # since each line carries a digest of the canonical dump. If this run dies
  # before that stage -- a missing artifact, a database refusal -- a fingerprint
  # left over from an EARLIER parity run would still be sitting at that name, and
  # the Python side would compare against a starting state that has nothing to do
  # with this attempt. So the name is emptied at the first moment the run-logs
  # directory is known good, which makes "absent" mean "this run did not get that
  # far" and never "some previous run's state". The post-run record is emptied with
  # it, for the same reason and in the same loop.
  ACAS_RUN_FINGERPRINT="$dir/cobol.seed-fingerprint"
  ACAS_RUN_POST_FINGERPRINT="$dir/cobol.post-fingerprint"
  local stale
  for stale in "$ACAS_RUN_FINGERPRINT" "$ACAS_RUN_POST_FINGERPRINT"; do
    if [[ -e "$stale" || -L "$stale" ]]; then
      rm -f -- "$stale" 2>/dev/null || acas_die "$EX_PRECONDITION" \
        "a previous state fingerprint could not be removed: $stale" \
        'Leaving it in place would let the Python side cross-check this run against' \
        "another run's starting state."
      acas_note "removed the state fingerprint left by an earlier run at $stale"
    fi
  done

  # The per-side run-status record. Written by the EXIT trap, so it exists for
  # EVERY termination path and carries this run's real status.
  ACAS_RUN_STATUS_FILE="$dir/cobol.run-status"
  acas_create_private_file "$ACAS_RUN_STATUS_FILE" "the run-status record"

  # INVALIDATED AT STARTUP, NOT MERELY WRITTEN AT THE END. Created
  # empty here, which is a record with NO `operation' line in it, so a reader that
  # requires one operation record per declared operation cannot mistake a previous
  # run's dispositions for this run's. The real content is published by
  # acas_publish_operation_status after the last operation has been driven.
  ACAS_RUN_OP_STATUS_FILE="$dir/cobol.operation-status"
  acas_create_private_file "$ACAS_RUN_OP_STATUS_FILE" 'the per-operation status record'

  # No timestamp in this header, by design.
  acas_tee "harness/run_cobol_scenario.sh -- scenario $ACAS_RUN_SCENARIO, operations $(acas_join_words "${ACAS_RUN_OPS[@]}")"
  acas_stage 'Check 3/8: transcript'
  acas_log "transcript = $ACAS_RUN_LOG"
  acas_log "plan       = $ACAS_RUN_PLAN_FILE"
  acas_log "outcome    = $ACAS_RUN_RESULT_FILE"
  acas_log "run id     = $ACAS_RUN_RUN_ID"
  acas_log "run status = $ACAS_RUN_STATUS_FILE (WRAPPER health)"
  acas_log "op status  = $ACAS_RUN_OP_STATUS_FILE (each operation's OWN disposition)"
  acas_log "fingerprint= $ACAS_RUN_FINGERPRINT (written just before the drive)"
  acas_log "post-print = $ACAS_RUN_POST_FINGERPRINT (written just after it)"
  acas_note 'all five are OUTSIDE the compared tree, so they cannot perturb a state diff'
  acas_note 'their SHA-256 fingerprints come at the END of the run, not here: all but the'
  acas_note 'transcript are still empty at this point and the transcript is still being'
  acas_note 'appended to, so a digest taken now would identify nothing an operator could'
  acas_note 'later check (rule R-6)'
}

# =============================================================================
# THE STATE FINGERPRINTS -- the oracle half of a cross-check that had none
#
# [harness/run_python_scenario.sh] records the state of every table its scenario
# names and compares its record with this side's. That cross-check was once
# unreachable, because nothing wrote this side's file: every Python run reported
# "seed cross-check: unverified", and the guarantee it exists to give -- that the
# two cycles were handed the same starting state -- was never actually checked.
# The consequence is the expensive one: a re-seed that quietly loaded a different
# fixture produces a diff full of real differences with no indication that the
# seed, not the cycle, was the cause.
#
# A ROW COUNT WAS NOT ENOUGH, AND THAT IS WHY THIS RECORD CARRIES A DIGEST.
# Two seeds that differ in one balance, one status byte or one date have
# IDENTICAL row counts. The counts-only form therefore certified a starting state
# it had not established, and an empty diff taken after it meant nothing. Each
# line now carries three fields:
#
#     <table><TAB><row count><TAB><sha256 of the canonical dump>
#
# in the scenario's declared order, with a single hyphen in BOTH value fields for
# a table that cannot be read -- a hyphen and never a zero, because "could not be
# read" is a different fact from "is empty" and the far side must tell them apart.
# The format is a contract: the far side compares with `cmp -s', byte for byte,
# not field by field.
#
# AND BOTH SIDES COMPUTE IT WITH THE SAME PROGRAM. [harness/dump_tables.py --table-digest]
# takes the digest over the canonical dump text [harness/dump_tables.py] itself
# writes, through its published `serialise_dump'. Two independently produced
# digests are comparable only if one implementation produced them: a digest taken
# by the mysql client here and by the driver there would differ on formatting
# alone and would report a starting-state disagreement on every run. Invoking
# that one producer from both sides is the only design that works, and it reaches
# no COBOL (R-1) -- it is a Python program, run out of process, exactly as the
# dump stage is.
#
# Row counts and digests only. No monetary value goes near this file, and it
# lives under run-logs/, outside every compared tree, so it can never be diffed
# as though it were posted data (R-2, R-6).
#
# WHY THIS SIDE DOES NOT ITSELF COMPARE. In protocol order the compiled run is
# first and the Python run second, so at this moment there is nothing to compare
# against: any python.seed-fingerprint present belongs to a previous parity run
# and a different seeding. Keeping ONE authority for the comparison -- the side
# that runs second -- is what stops a leftover file from manufacturing a failure.
# What this side owes the protocol is an honest record of its own state, and that
# is what it writes: one before the drive, and one after it.
# THE EXACT SEED IDENTITY, READ AND CARRIED
#
# "Seed fingerprint" on this side is a list of TABLE ROW COUNTS, and that is not an
# identity: two seedings with the same shape and different values compare equal, so the
# two legs of a parity run could start from different money and the protocol would
# report that their starting states matched. harness/seed.sh already stages a marker
# carrying a SHA-256 per seeded file, and harness/reset_db.sh publishes that marker's
# own digest to <ACAS_OUT>/run-logs/<scenario>/seed-identity. This reads it, and
# records it in the run-status record, where harness/dump_tables.py requires it and
# harness/diff_states.py requires the two sides to agree.
#
# ABSENCE IS NOT FATAL HERE, and that is deliberate rather than lax: a run driven by
# hand, without the reset stage, legitimately has no seed identity, and refusing it
# would make the runner unusable for exactly the debugging it is most needed for. The
# refusal belongs downstream, where the CAPTURE is required to carry one before it can
# support a verdict -- fail-closed at the point the claim is made rather than at the
# point the work is done.
#
# A run id that does NOT match is a different matter: it means the seed on disk was
# staged by another attempt, so the identity would be a lie about this one. That is
# discarded rather than recorded.
acas_read_seed_identity() {
  local path="$ACAS_OUT/run-logs/$ACAS_RUN_SCENARIO/seed-identity"
  local key value recorded_run='' recorded_digest='' recorded_scenario=''

  ACAS_RUN_SEED_IDENTITY=''
  [[ -f "$path" && ! -L "$path" ]] || {
    acas_note "no seed identity at $path; this capture will be reported as carrying no exact seed identity"
    return 0
  }
  while IFS=$'\t' read -r key value; do
    case "$key" in
      scenario)              recorded_scenario="$value" ;;
      run_id)                recorded_run="$value" ;;
      fixture_marker_sha256) recorded_digest="$value" ;;
    esac
  done <"$path"

  if [[ "$recorded_scenario" != "$ACAS_RUN_SCENARIO" ]]; then
    acas_warn "the seed identity at $path names scenario '$recorded_scenario', not '$ACAS_RUN_SCENARIO'; it is discarded."
    return 0
  fi
  if [[ -n "$ACAS_RUN_RUN_ID" && -n "$recorded_run" && "$recorded_run" != "$ACAS_RUN_RUN_ID" ]]; then
    acas_warn "the seed identity at $path was staged by attempt '$recorded_run', not '$ACAS_RUN_RUN_ID'; it is discarded." \
      'Recording it would make this capture claim a seed it was not given.'
    return 0
  fi
  [[ "$recorded_digest" =~ ^[0-9a-f]{64}$ ]] || {
    acas_warn "the seed identity at $path carries no SHA-256; it is discarded."
    return 0
  }

  ACAS_RUN_SEED_IDENTITY="$recorded_digest"
  acas_log "seed identity = ${ACAS_RUN_SEED_IDENTITY:0:16}... (the staged fixture marker digest)"
  return 0
}

acas_write_state_fingerprint() {
  local target="$1" label="$2"

  if (( ${#ACAS_RUN_FINGERPRINT_TABLES[@]} == 0 )); then
    acas_warn "no affected-table list, so no $label is recorded and the Python side will report the cross-check as unverified"
    return 0
  fi

  acas_create_private_file "$target" "the $label"

  # The digest producer is a sibling of this script, so it is found relative to
  # this file rather than through $PATH or a guessed checkout layout.
  local producer="$ACAS_RUN_HARNESS_DIR/dump_tables.py"
  [[ -f "$producer" ]] || acas_die "$EX_PRECONDITION" \
    "the canonical state-digest producer is missing: $producer" \
    'Both sides must compute their fingerprints with the same program, or the two' \
    'records cannot be compared. It is a sibling of this script.'

  acas_have python3 || acas_die "$EX_PRECONDITION" \
    'python3 is not on PATH, so no state fingerprint can be taken.' \
    'harness/dump_tables.py --table-digest is the single canonical digest producer' \
    'for both' \
    'sides of the comparison. It reaches no COBOL (R-1).'

  local out rc=0
  acas_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  out="$("${ACAS_DEADLINE_ARGV[@]}" python3 "$producer" --table-digest \
    -- "${ACAS_RUN_FINGERPRINT_TABLES[@]}" 2>&1)" || rc=$?
  # Exit 1 means at least one table could not be read; the record is still
  # complete, still ordered and still comparable, so it is written and the
  # unreadable tables are reported. Anything else is fatal: an empty or partial
  # record would certify a starting state nobody established.
  if (( rc != 0 && rc != 1 )); then
    acas_die "$EX_DATABASE" \
      "the $label could not be taken (status $rc)." \
      "$(acas_diag_summary "$out")" \
      'A comparison whose starting state cannot be established is not a' \
      'comparison, so this is refused rather than recorded as unknown.'
  fi

  # Only the well-formed record lines are kept: the producer writes its per-table
  # diagnoses to stderr, which was merged above so an operator sees them, and a
  # diagnosis inside the record would be compared as though it were state.
  local lines=''
  local line
  while IFS= read -r line; do
    [[ "$line" =~ ^[A-Za-z0-9_-]+$'\t'([0-9]+|-)$'\t'([0-9a-f]{64}|-)$ ]] || continue
    lines+="$line"$'\n'
  done <<<"$out"

  [[ -n "$lines" ]] || acas_die "$EX_DATABASE" \
    "the $label came back empty." \
    "$(acas_diag_summary "$out")" \
    'One line per affected table is the contract.'

  printf '%s' "$lines" >"$target" || acas_die "$EX_PRECONDITION" \
    "the $label could not be written: $target"
  acas_log "$label = $target"
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    acas_log "  $(printf '%-22s %-8s %s' \
      "${line%%$'\t'*}" \
      "$(printf '%s' "$line" | cut -f2)" \
      "$(printf '%s' "$line" | cut -f3)")"
  done <<<"$lines"
  if (( rc == 1 )); then
    acas_warn "at least one table could not be digested for the $label; its line carries the hyphen markers and the reason is above"
  fi
  return 0
}

acas_record_seed_fingerprint() {
  ACAS_RUN_CURRENT_STAGE='recording the pre-run state fingerprint'
  acas_stage 'Check 8a/8: the pre-run state fingerprint'

  # The EXACT identity first, then the per-table digests. The digests remain
  # because they are the cross-check the two runners exchange; the identity is what
  # actually binds the two legs to the same seeded BYTES rather than to the same shape.
  acas_read_seed_identity
  acas_write_state_fingerprint "$ACAS_RUN_FINGERPRINT" 'seed fingerprint'
  acas_note 'the Python side compares its own record with this file and refuses to proceed if they differ; this side records and does not compare, because in protocol order it runs first'
}

acas_record_post_fingerprint() {
  ACAS_RUN_CURRENT_STAGE='recording the post-run state fingerprint'
  acas_stage 'Check 8c/8: the post-run state fingerprint'
  acas_write_state_fingerprint "$ACAS_RUN_POST_FINGERPRINT" 'post-run fingerprint'
  acas_note 'the pre-run and post-run records together answer a question no table diff can: did this run CHANGE anything? Two runs that did nothing at all agree perfectly, so without this a no-op could satisfy a parity or a determinism claim'
}

# STAGE 5 -- the compiled oracle.
acas_assert_oracle() {
  ACAS_RUN_CURRENT_STAGE='asserting the compiled oracle'
  acas_stage 'Check 5/8: compiled artifacts'

  # The four menu executables, each built with `cobc -x' by the maintainer's
  # own per-directory script.
  local -a menus=(
    'general:general/comp-gl.sh:L3'
    'sales:sales/comp-sales.sh:L9'
    'purchase:purchase/comp-purchase.sh:L3'
    'irs:irs/comp-irs.sh:L3'
  )
  local entry subsystem locator path present missing=0
  for entry in "${menus[@]}"; do
    subsystem="${entry%%:*}"
    locator="${entry#*:}"
    path="$ACAS_BUILD/$subsystem/$subsystem"
    if [[ -x "$path" ]]; then
      present='present'
    elif [[ -e "$path" ]]; then
      present='NOT EXECUTABLE'
      missing=1
    else
      present='MISSING'
      missing=1
    fi
    acas_log "$(printf '%-9s %-14s %s' "$subsystem" "$present" "[$locator]")"
  done

  # EVERY SUBSYSTEM THE OPERATION LIST REACHES, NOT JUST ONE. A scenario
  # may span two menus -- period_end_totals spans Sales and Purchase -- and this run
  # drives all of its operations, so a menu missing for operation 3 must be a
  # refusal HERE, before anything is written, and not a failure discovered after
  # operations 1 and 2 have already posted.
  local -a needed_subsystems=()
  local op
  for op in "${ACAS_RUN_OPS[@]}"; do
    acas_select_operation "$op"
    if ! acas_in_list "$ACAS_RUN_SUBSYSTEM" "${needed_subsystems[@]}"; then
      needed_subsystems+=("$ACAS_RUN_SUBSYSTEM")
    fi
  done
  acas_select_operation "${ACAS_RUN_OPS[0]}"

  local needed candidate
  for needed in "${needed_subsystems[@]}"; do
    candidate="$ACAS_BUILD/$needed/$needed"
    if [[ ! -x "$candidate" ]]; then
      acas_die "$EX_ORACLE" \
        "the $needed menu executable is missing or not executable." \
        "expected: $candidate" \
        "It is required because this run drives: $(acas_join_words "${ACAS_RUN_OPS[@]}")." \
        'Run harness/build_oracle.sh first. It performs the five-step bootstrap,' \
        'including the build rule for cobmysqlapi.o that the repository itself does' \
        'not contain -- every bridge, handler and loader links that object at' \
        '[common/comp-common.sh:L26] and following, yet no rule anywhere in the' \
        'checkout builds it, so a naive build fails at link time with no obvious cause.' \
        'Note also that the frozen build scripts end with an unconditional exit 0' \
        '-- [comp-all.sh:L45], [common/comp-common.sh:L59] -- so their exit status is' \
        'NOT a success signal and the artifacts must be checked by name, as here.'
    fi
  done
  # Re-derived rather than assigned, so there is exactly ONE expression anywhere
  # in this script that turns a subsystem into an executable path. This call makes
  # the value correct for the operation selected right now; the drive loop calls
  # acas_select_operation, and so this, again for each operation in turn.
  acas_resolve_executable
  if (( missing )); then
    acas_warn "not every menu executable is built; this run needs $(acas_join_words "${needed_subsystems[@]}")"
  fi

  # The `-m' modules the menus of EVERY needed subsystem will dynamically load.
  local -a modules=()
  for needed in "${needed_subsystems[@]}"; do
    case "$needed" in
      general)  modules+=("${ACAS_RUN_GENERAL_MODULES[@]}") ;;
      sales)    modules+=("${ACAS_RUN_SALES_MODULES[@]}") ;;
      purchase) modules+=("${ACAS_RUN_PURCHASE_MODULES[@]}") ;;
      irs)      modules+=("${ACAS_RUN_IRS_MODULES[@]}") ;;
    esac
    # Sales additionally loads sl830 before sl055 [sales/sales.cbl:L759-L760].
    if [[ "$needed" == 'sales' ]]; then
      modules+=(sl830)
    fi
  done

  local -a absent=()
  local module
  for module in "${modules[@]}"; do
    if ! acas_module_present "$module"; then
      absent+=("$module")
    fi
  done
  if (( ${#absent[@]} > 0 )); then
    acas_die "$EX_ORACLE" \
      "compiled modules are missing: $(acas_join_words "${absent[@]}")" \
      "searched: $(acas_join_words "${ACAS_RUN_LIBRARY_DIRS[@]/#/$ACAS_BUILD/}")" \
      'These are the dynamically loadable sub-programs the menu CALLs. Run' \
      'harness/build_oracle.sh.' \
      'If build_oracle.sh reported success but a module is still absent, check' \
      'whether copybooks/ACAS-SQLstate-error-list.cob is present: it is referenced' \
      'by the generated bridges and, when it is missing from the archive, those' \
      'bridges cannot compile. It must be supplied by the maintainer and must NOT' \
      'be fabricated -- it carries the SQLSTATE to FS-Reply mapping that DEFINES' \
      'the oracle rejection behaviour this harness exists to reproduce.'
  fi
  acas_log "modules    = $(acas_join_words "${modules[@]}") -- all present"

  # COB_LIBRARY_PATH must name every build directory or the menu cannot load
  # its sub-programs.
  local dir want=''
  for dir in "${ACAS_RUN_LIBRARY_DIRS[@]}"; do
    if [[ -d "$ACAS_BUILD/$dir" ]]; then
      if [[ -z "$want" ]]; then
        want="$ACAS_BUILD/$dir"
      else
        want="$want:$ACAS_BUILD/$dir"
      fi
    fi
  done
  [[ -n "$want" ]] || acas_die "$EX_ORACLE" \
    "no build subdirectories found under $ACAS_BUILD." \
    'Run harness/build_oracle.sh.'
  if [[ -n "${COB_LIBRARY_PATH:-}" && "$COB_LIBRARY_PATH" != "$want"* ]]; then
    COB_LIBRARY_PATH="$want:$COB_LIBRARY_PATH"
  else
    COB_LIBRARY_PATH="$want"
  fi
  export COB_LIBRARY_PATH
  acas_log "COB_LIBRARY_PATH = $COB_LIBRARY_PATH"

  local info=''
  if acas_have cobc; then
    info="$(cobc --info 2>/dev/null | grep -i 'indexed file handler' || true)"
    if [[ -z "$info" ]]; then
      acas_warn 'cobc --info did not report an indexed file handler line; cannot verify the ISAM backend'
    else
      acas_log "cobc: $(printf '%s' "$info" | sed -e 's/^[ \t]*//')"
      if printf '%s' "$info" | grep -qiE 'disabled|not available|none'; then
        acas_die "$EX_PRECONDITION" \
          'GnuCobol has no indexed-file (ISAM) backend.' \
          "cobc --info reports: $info" \
          'system.dat is opened as a Cobol INDEXED file, because' \
          '[general/general.cbl:L385-L396] forces the Cobol path for the system' \
          'parameter file. With no backend the open fails, the menu CALLs sys002' \
          'INTERACTIVELY, and this harness hangs with no diagnostic. Rebuild the' \
          'image: harness/Dockerfile.gnucobol installs a GnuCobol with BDB.'
      fi
    fi
  else
    acas_note 'cobc is not on PATH; skipping the ISAM backend check (only the runtime is needed to drive the oracle)'
  fi
}

acas_module_present() {
  local module="$1" dir
  for dir in "${ACAS_RUN_LIBRARY_DIRS[@]}"; do
    if [[ -f "$ACAS_BUILD/$dir/$module.so" ]] \
      || [[ -f "$ACAS_BUILD/$dir/$module" ]] \
      || [[ -f "$ACAS_BUILD/$dir/$module.dylib" ]]; then
      return 0
    fi
  done
  return 1
}


# The password reaches the client through MYSQL_PWD ONLY.

#  TRANSPORT SECURITY (CWE-295 certificate validation, CWE-319 cleartext). Decided ONCE,
#  before anything connects, and never downgraded afterwards. Full rationale:
#  harness/build_oracle.sh, same heading.

# True when the target is reachable without leaving the machine: a unix socket,
# an empty host, a loopback name, or a numeric loopback address.
acas_target_is_local() {
  [[ -n "${ACAS_DB_SOCKET:-}" ]] && return 0
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
# target has earned. Populates ACAS_RUN_TLS_VARIANTS, most secure first, or
# aborts.
acas_assert_transport_policy() {
  local ca="${ACAS_DB_TLS_CA:-}"
  ACAS_RUN_TLS_VARIANTS=()

  if [[ -n "$ca" ]]; then
    [[ -r "$ca" ]] || acas_die "$EX_PRECONDITION" \
      "ACAS_DB_TLS_CA names a file that cannot be read: $(acas_sanitise_field "$ca")" \
      'It must be the PEM bundle the server certificate chains to.'
    ACAS_RUN_TLS_VARIANTS+=("--ssl-ca=$ca --ssl-verify-server-cert")
  fi

  if acas_target_is_local; then
    ACAS_RUN_TLS_VARIANTS+=('--skip-ssl')
    acas_note 'transport: local target, so plaintext is permitted'
    return 0
  fi

  if acas_plaintext_declared; then
    acas_warn 'ACAS_DB_ALLOW_PLAINTEXT permits plaintext to a NON-LOCAL server; the harness credential and every answer are unprotected'
    ACAS_RUN_TLS_VARIANTS+=('--skip-ssl')
    return 0
  fi

  if [[ -z "$ca" ]]; then
    acas_die "$EX_PRECONDITION" \
      "the target $(acas_sanitise_field "$ACAS_DB_HOST"):${ACAS_DB_PORT} is not local and no verified TLS is configured." \
      'This script authenticates with the harness credential and reads the schema' \
      'and the SYSTEM-REC row, so the connection must be protected. Either set' \
      'ACAS_DB_TLS_CA to the PEM bundle the server certificate chains to, or -- if' \
      'this really is an isolated harness network such as the private Compose' \
      'network [harness/docker-compose.yml] -- declare it with' \
      'ACAS_DB_ALLOW_PLAINTEXT=1.' \
      'It is NOT downgraded silently: that was the defect.'
  fi

  acas_note 'transport: verified TLS required (CA supplied, certificate and hostname checked)'
  return 0
}

# Every value that reaches SQL text does so through one of these, never by
# being interpolated between hand-written quotes.

acas_assert_sql_identifier() {
  local label="$1" value="$2"
  if [[ ! "$value" =~ ^[A-Za-z0-9_]{1,12}$ ]]; then
    acas_die "$EX_PRECONDITION" \
      "$label is not a plain SQL identifier: '$value'." \
      'It is composed into SQL text, so it is restricted to letters, digits and' \
      'underscore, at most 12 characters -- already the ceiling the COBOL' \
      'RDB-Data pic x(12) field imposes [copybooks/wsfnctn.cob:L56-L62].' \
      'A value carrying a quote, backslash, semicolon or whitespace is refused' \
      'rather than escaped, because nothing here has a legitimate use for one.'
  fi
}

acas_assert_table_name() {
  local label="$1" value="$2"
  if [[ ! "$value" =~ ^[A-Za-z0-9_-]{1,64}$ ]]; then
    acas_die "$EX_PRECONDITION" \
      "$label is not a plain SQL table name: '$value'." \
      'It is composed into SQL text as a quoted identifier, so it is restricted' \
      'to letters, digits, underscore and hyphen -- the alphabet the frozen' \
      'mysql/ACASDB.sql actually uses. A backtick in particular is refused' \
      'rather than escaped.'
  fi
}

# ONE PUBLIC SPELLING FOR EACH JOB, and no alias. A value literal is quoted by
# acas_sql_quote_literal, declared with the SAFE SQL COMPOSITION block above, and
# an identifier by acas_sql_quote_ident below. A second published name for the
# literal quoter is deliberately NOT published here: nothing would call it, ShellCheck
# reports such a name as unreachable (SC2317), and a spelling that exists but is never
# used is a place a later edit can quote a value the other way round unnoticed.

# acas_sql_quote_ident <value> -> `value` with embedded backticks doubled.
acas_sql_quote_ident() {
  local value="$1"
  # The delimiter travels in a variable rather than inside the printf format.
  local bq='`'
  printf '%s%s%s' "$bq" "${value//"$bq"/"$bq$bq"}" "$bq"
}

acas_sql_scalar() {
  local sql="$1"
  ACAS_SQL_OUT=''
  ACAS_SQL_DIAG=''

  local client variant flag out rc
  # Unreachable unless acas_assert_transport_policy was skipped or changed: it
  # either records at least one permitted variant or aborts with a named cause.
  if (( ${#ACAS_RUN_TLS_VARIANTS[@]} == 0 )); then
    acas_die "$EX_PRECONDITION" \
      'no permitted client transport for this target.' \
      'acas_assert_transport_policy must run before any query; see the' \
      'TRANSPORT SECURITY section.'
  fi
  for client in mariadb mysql; do
    acas_have "$client" || continue
    for variant in "${ACAS_RUN_TLS_VARIANTS[@]}"; do
      # Every attempt is bounded: a client that neither connects nor is refused
      # would otherwise block this probe indefinitely.
      acas_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
      local -a argv=("${ACAS_DEADLINE_ARGV[@]}" "$client" '--protocol=TCP')
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
      out="$(MYSQL_PWD="$ACAS_DB_PASSWORD" "${argv[@]}" 2>/dev/null)" || rc=$?
      if (( rc == 0 )); then
        ACAS_SQL_OUT="$out"
        return 0
      fi
      ACAS_SQL_DIAG="$(MYSQL_PWD="$ACAS_DB_PASSWORD" "${argv[@]}" 2>&1 || true)"
    done
    if [[ "$ACAS_SQL_DIAG" == *'Access denied'* ]]; then
      return 2
    fi
    return 1
  done
  return 3
}

# TCP reachability without a client binary and without a credential.
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

# acas_system_column <column> Read one column of the single SYSTEM-REC row.
acas_system_column() {
  local column="$1" rc=0
  acas_assert_table_name 'a SYSTEM-REC column name' "$column"
  acas_sql_scalar "select $(acas_sql_quote_ident "$column") from $(acas_sql_quote_ident 'SYSTEM-REC') limit 1;" || rc=$?
  if (( rc != 0 )); then
    return "$rc"
  fi
  printf '%s' "$ACAS_SQL_OUT"
}

# THE DESTRUCTIVE-TARGET GATE. See the DISPOSABLE vocabulary above for
# why the schema name alone proved nothing.
#
# Called from acas_assert_database AFTER connectivity, because the proof is a query.
# It runs BEFORE the autocommit check, the silent-pass traps and every drive stage,
# so nothing has posted by the time this either passes or refuses.
acas_run_target_label() {
  printf '%s@%s:%s/%s' \
    "${ACAS_DB_USER:-<unset>}" \
    "${ACAS_DB_HOST:-<unset>}" \
    "${ACAS_DB_PORT:-<unset>}" \
    "${ACAS_DB_NAME:-<unset>}"
}

acas_run_target_acknowledged() {
  local supplied="${ACAS_RUN_ACKNOWLEDGE_DESTRUCTIVE-}"
  [[ -n "$supplied" ]] || return 1
  [[ "$supplied" == "$(acas_run_target_label)" ]]
}

# A PROTOCOL-BOUND RUN REFUSES THE ACKNOWLEDGEMENT
#
# The acknowledgement above lets this runner post into a server that does not declare
# itself a harness-owned disposable target. That is legitimate when someone is driving
# the compiled cycle against a database of their own, and wrong when the run is stage 2
# of the parity protocol: the state this stage produces is one half of a verdict, so a
# server nobody proved was throwaway makes that verdict a statement about an unknown
# database.
#
# The two cases are told apart by the RUN ID. ACAS_PARITY_RUN_ID (or --run-id) is what
# binds ten separate invocations into one protocol run, so its presence IS the evidence
# path -- and on that path the acknowledgement is refused rather than honoured. Without
# it this stays the hand-drivable tool it is.
#
# A refusal in a ten-stage driver script would scrub the variable only for the stages that
# script drove itself and therefore protect nothing in a hand-driven run. Checked HERE it
# travels with the stage, and it is checked BEFORE the
# run id is derived, before a connection is opened and before a keystroke is planned.
acas_assert_no_evidence_bypass() {
  #  Unbound means the hand-drivable tool, so nothing is refused.
  [[ -n "$ACAS_RUN_RUN_ID" ]] || return 0
  [[ -n "${ACAS_RUN_ACKNOWLEDGE_DESTRUCTIVE-}" ]] || return 0

  acas_die "$EX_PRECONDITION" \
    'ACAS_RUN_ACKNOWLEDGE_DESTRUCTIVE is set on a protocol-bound run.' \
    "This run carries ACAS_PARITY_RUN_ID='$ACAS_RUN_RUN_ID', so it is stage 2 of the" \
    'parity protocol and the state it produces will be compared against the Python' \
    'cycle. The acknowledgement waives the requirement that the target declare itself' \
    'a harness-owned disposable server, and a verdict drawn from a database that' \
    'cannot prove that is a statement about an unknown state.' \
    'Unset it and re-run against the harness target. To drive the compiled cycle at' \
    'another server deliberately, invoke this script WITHOUT a bound run id: the' \
    'acknowledgement is honoured then, and no protocol artifact claims the result.'
}

acas_assert_disposable_target() {
  local acknowledged=0
  if acas_run_target_acknowledged; then
    acknowledged=1
  fi

  # An acknowledgement that is SET but names a different target is refused outright
  # rather than treated as absent: it means the operator believes they authorised
  # this run, and letting the marker decide instead would be answering a question
  # they did not ask.
  if (( ! acknowledged )) && [[ -n "${ACAS_RUN_ACKNOWLEDGE_DESTRUCTIVE-}" ]]; then
    acas_die "$EX_TARGET" \
      'ACAS_RUN_ACKNOWLEDGE_DESTRUCTIVE names a different target than this run.' \
      "  this run: $(acas_run_target_label)" \
      'The acknowledgement is matched against the exact target so that one left in' \
      'an environment cannot later authorise a different database. Correct it or' \
      'unset it.'
  fi

  local marker='' rc=0
  acas_sql_scalar "select @@${ACAS_RUN_DISPOSABLE_VARIABLE};" || rc=$?
  if (( rc == 0 )); then
    marker="$ACAS_SQL_OUT"
  fi

  if (( rc != 0 )) || [[ "$marker" != "$ACAS_RUN_DISPOSABLE_MARKER"* ]]; then
    if (( ! acknowledged )); then
      acas_die "$EX_TARGET" \
        'this server does not declare itself a harness-owned disposable target.' \
        "  variable: @@${ACAS_RUN_DISPOSABLE_VARIABLE}" \
        "  expected: ${ACAS_RUN_DISPOSABLE_MARKER}..." \
        "  found:    ${marker:-<query failed>}" \
        '' \
        'This script DRIVES THE COMPILED POSTING CYCLE. It rewrites nominal' \
        'balances, stamps batches cleared and, for a scenario that answers the IRS' \
        'end-of-job question with Y, ISSUES A DELETE against PSIRSPOST-REC' \
        '[common/acas008.cbl:L313-L319] -- bounded by the bridge' \
        '[common/slpostingMT.cbl:L850-L891]. The schema name proves nothing: the frozen' \
        'mysql/ACASDB.sql gives every ACAS installation that same name.' \
        '' \
        'That declaration is written into the server configuration by' \
        'harness/Dockerfile.mariadb, so its ABSENCE means this is not the' \
        "harness's throwaway server. Start the harness service instead:" \
        '    docker compose -f harness/docker-compose.yml up -d mariadb' \
        'If this IS a disposable target that predates the marker, rebuild the' \
        'image rather than acknowledging past the gate:' \
        '    docker compose -f harness/docker-compose.yml build mariadb' \
        '' \
        'If the target really is disposable, say so explicitly and name it exactly:' \
        "    ACAS_RUN_ACKNOWLEDGE_DESTRUCTIVE='$(acas_run_target_label)'" \
        'A protocol-bound run refuses that variable: evidence production may not' \
        'be aimed by hand.'
    fi
    acas_warn 'acknowledged: this server does not declare itself a harness-owned disposable target.'
    acas_log 'disposability = acknowledged, NOT PROVEN'
  else
    acas_log "disposability declared by the server: @@${ACAS_RUN_DISPOSABLE_VARIABLE} = ${ACAS_RUN_DISPOSABLE_MARKER}"
  fi
}

# STAGE 6 -- the database.
acas_assert_database() {
  ACAS_RUN_CURRENT_STAGE='asserting the database'
  acas_stage 'Check 6/8: database, schema and the two silent-pass traps'

  acas_db_tcp_probe || acas_die "$EX_DATABASE" \
    "cannot reach $ACAS_DB_HOST:$ACAS_DB_PORT." \
    'Bring the MariaDB service up first -- harness/docker-compose.yml defines it at' \
    'the version the frozen schema was produced by [mysql/ACASDB.sql:L1].'

  local rc=0
  acas_sql_scalar 'select 1;' || rc=$?
  case "$rc" in
    0) : ;;
    2) acas_die "$EX_DATABASE" \
         "the database refused the credentials for user '$ACAS_DB_USER'." \
         'The password is not shown here and is never logged.' ;;
    3) acas_die "$EX_DATABASE" \
         'no mariadb or mysql client is on PATH.' \
         'harness/Dockerfile.gnucobol installs the client libraries under the prefix' \
         'the frozen compile scripts expect.' ;;
    *) acas_die "$EX_DATABASE" \
         "the database rejected a trivial query on $ACAS_DB_NAME." \
         "$(acas_diag_summary "$ACAS_SQL_DIAG")" ;;
  esac

  # BEFORE anything else this stage learns about the target, and long
  # before any drive stage posts into it.
  acas_assert_disposable_target

  # The frozen schema must be present. 33 CREATE TABLE statements, no ALTER and
  # no CREATE INDEX [mysql/ACASDB.sql]. Nothing here alters it (R-3).
  rc=0
  acas_sql_scalar "select count(*) from information_schema.tables where table_schema = ${ACAS_RUN_SCHEMA_LITERAL};" || rc=$?
  (( rc == 0 )) || acas_die "$EX_DATABASE" \
    'could not count the tables in the schema.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  local table_count="$ACAS_SQL_OUT"
  acas_log "tables present = $table_count"
  if [[ "$table_count" == '0' ]]; then
    acas_die "$EX_DATABASE" \
      "the schema $ACAS_DB_NAME holds no tables." \
      'Apply mysql/ACASDB.sql verbatim -- harness/Dockerfile.mariadb does this -- and' \
      'then seed with harness/seed.sh. The schema is FROZEN: it is applied as it' \
      'stands and never migrated.'
  fi

  # Autocommit must be ON here, and the reason is a scoping one rather than a
  # preference. The Agent Action Plan mandates OFF for SEEDING and says so in all
  # three of its provisions -- section 0.2.1.1 ("the batch loader turns autocommit
  # off"), section 0.5.2 ("autocommit must be off DURING SEEDING") and section
  # 0.4.1.7 on harness/Dockerfile.mariadb ("autocommit off TO MATCH THE LOADERS",
  # the loaders being the seeding stage) -- all deriving it from the banner carried
  # by all 28 common/*LD.cbl loaders at [common/glbatchLD.cbl:L9-L13]: "you MUST
  # ensure that autocommit is OFF in the rdb settings".
  #
  # A POSTING RUN IS NOT SEEDING. It is runtime application access, which the AAP
  # never scopes OFF, so it runs in the mode harness/Dockerfile.mariadb declares
  # for runtime access. harness/seed.sh owns the OFF window, opens it around the
  # frozen load programs and restores this mode when it closes.
  #
  # The banner addresses the OPERATOR because no COBOL program can act on it: the
  # vendored `cobmysqlapi38.c' exposes MySQL_commit and MySQL_rollback but NOT
  # MySQL_autocommit. Only the server's setting can establish the mode, which is
  # why this script ASSERTS and NEVER SETS it -- the runtime authority is
  # harness/Dockerfile.mariadb and the window authority is harness/seed.sh.
  #
  # CONSEQUENCE, PRESERVED NOT REPAIRED (R-4): the frozen code reaches no COMMIT.
  # Every `perform aa020-Rollback' in all 28 loaders is commented out (78 sites,
  # none live) and `perform aa030-Commit' occurs exactly once anywhere, at
  # [common/irsdfltLD.cbl:L437], commented out as well; [common/systemLD.cbl]
  # declares both paragraphs at L406 and L420 with no perform site at all. The
  # posting path is the same -- zero COMMIT / ROLLBACK / START TRANSACTION in the
  # twenty in-scope bridges, in the in-scope handlers and on every bridge close
  # path.
  #
  # Under the runtime mode each statement the bridges issue lands on its own,
  # which is exactly the per-statement model the bridges were written for -- what
  # is absent is any transaction BOUNDARY, so a run that fails part-way through a
  # double entry leaves the completed half in place instead of rolling it back.
  # That is the frozen code's own defect and R-4 makes it the specification --
  # "a defect reproduced is correct; a defect fixed is a failure" -- so this script
  # warns about it below and proceeds, issuing neither the missing COMMIT nor the
  # missing ROLLBACK. Were this run driven inside the seeding window instead, the
  # implicit transaction MariaDB opens on its first DML statement would be
  # discarded at disconnect and the capture would be empty, which is why the mode
  # is asserted rather than assumed.
  rc=0
  acas_sql_scalar 'select concat_ws(0x2f, @@GLOBAL.autocommit + 0, @@SESSION.autocommit + 0);' || rc=$?
  (( rc == 0 )) || acas_die "$EX_DATABASE" \
    'could not read the autocommit settings.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  local autocommit=''
  local line
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ ^[0-9]+/[0-9]+$ ]]; then
      autocommit="$line"
    fi
  done < <(printf '%s\n' "$ACAS_SQL_OUT")
  [[ -n "$autocommit" ]] || acas_die "$EX_DATABASE" \
    'could not parse the autocommit settings.' \
    "client returned: $ACAS_SQL_OUT"
  acas_log "autocommit (global/session) = $autocommit"
  if [[ "$autocommit" != '1/1' ]]; then
    acas_die "$EX_AUTOCOMMIT" \
      "autocommit must be ON for the compiled cycle; the server reports $autocommit (global/session)." \
      'A posting run is RUNTIME APPLICATION ACCESS, not seeding. The Agent Action' \
      'Plan scopes its autocommit-OFF requirement to seeding in all three of its' \
      'provisions -- section 0.2.1.1 ("the batch loader turns autocommit off"),' \
      'section 0.5.2 ("autocommit must be off DURING SEEDING") and section 0.4.1.7' \
      'on harness/Dockerfile.mariadb ("autocommit off TO MATCH THE LOADERS", the' \
      'loaders being the seeding stage) -- all from the banner carried by all 28' \
      'common/*LD.cbl loaders at [common/glbatchLD.cbl:L9-L13]. harness/seed.sh' \
      'owns that window and restores this mode when it closes.' \
      'Driving the compiled cycle with autocommit OFF would be worse than' \
      'unsanctioned: the frozen code reaches no COMMIT, so every posting it made' \
      'would be discarded at session close, the capture would be EMPTY, and an' \
      'empty diff is the only pass condition the protocol has -- the run would' \
      'certify' \
      'the migration exact having posted nothing.' \
      'Finding the mode OFF means the seeding window is still open: a seed' \
      'interrupted before its exit trap ran, or a server configured for the' \
      'seeding mode server-wide. harness/Dockerfile.mariadb declares autocommit=1' \
      'in /etc/mysql/conf.d/99-acas-oracle.cnf for runtime access; this script only' \
      'asserts it. Start the harness MariaDB service built from that Dockerfile,' \
      'or restore the runtime mode with: set global autocommit = 1'
  fi

  # The reproduced defect, restated where it bites. A WARNING, not a refusal:
  # R-4 requires the frozen behaviour, so refusing would be refusing the
  # specification. Under the runtime mode asserted above the statements the
  # bridges issue do land, one per statement, exactly as the bridges' own
  # per-statement model expects -- what remains absent is any transaction
  # BOUNDARY, so a half-posted double entry stays half-posted rather than rolling
  # back, which is the frozen behaviour the anomaly log records.
  acas_warn 'the frozen COBOL reaches no COMMIT and no ROLLBACK: in all 28 common/*LD.cbl loaders every "perform aa020-Rollback" is commented out (78 sites, none live) and "perform aa030-Commit" occurs exactly once anywhere, at [common/irsdfltLD.cbl:L437], commented out too, while the twenty in-scope bridges, the in-scope handlers and every bridge close path contain zero COMMIT/ROLLBACK/START TRANSACTION. The maintainer recorded the same observation at [common/analLD.cbl:L442] ("These do not work during testing with mariadb - Non transactional model or autocommit set ON"), and [common/glbatchLD.cbl:L386] notes the server is "as normally ... set to autocommit". So this run has NO transaction boundaries: a failure part-way through a double entry leaves the completed half in place. That is the reproduced legacy defect (R-4); nothing here issues the missing COMMIT or the missing ROLLBACK, because a defect fixed is a failure.'

  # There must BE a system record. Without it the menu cannot start, and an
  # empty result would otherwise make every column check below vacuously pass.
  rc=0
  acas_sql_scalar "select count(*) from $(acas_sql_quote_ident 'SYSTEM-REC');" || rc=$?
  (( rc == 0 )) || acas_die "$EX_DATABASE" \
    'could not count SYSTEM-REC.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  if [[ "$ACAS_SQL_OUT" == '0' ]]; then
    acas_die "$EX_PRECONDITION" \
      'SYSTEM-REC is empty: the database has not been seeded.' \
      'Run harness/seed.sh for this scenario first. It is part of stage 1 of the' \
      'ten-stage protocol and this is stage 2; running out of order compares' \
      'nothing.' \
      'Note that the checkout ships no *.dat files, so the scenario seed data has to' \
      'be authored -- see the per-file contract at [common/masterLD.sh:L44-L115],' \
      'which harness/seed.sh reproduces rather than invokes.'
  fi

  local file_system_used
  file_system_used="$(acas_system_column 'FILE-SYSTEM-USED')" || acas_die "$EX_DATABASE" \
    'could not read SYSTEM-REC.FILE-SYSTEM-USED.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  acas_log "FILE-SYSTEM-USED = $file_system_used"
  if [[ "$file_system_used" == '0' ]]; then
    acas_die "$EX_PRECONDITION" \
      'SYSTEM-REC.FILE-SYSTEM-USED is zero, so this run would write NO tables at all.' \
      'The field is File-System-Used at [copybooks/wssystem.cob:L111-L112]. Note that' \
      '[general/general.cbl:L385-L396] forces the Cobol path for the SYSTEM PARAMETER' \
      'FILE only; what decides whether the LEDGER and POSTING files reach the RDB is' \
      'this field, and the menu exit only rewrites the RDB copies `if' \
      'File-System-Used NOT = zero` [general/general.cbl:L656-L692].' \
      'With it zero the whole run writes Cobol flat files, every in-scope table is' \
      'untouched, the state diff comes back EMPTY and the harness reports a clean' \
      'pass having compared nothing. That is the worst failure mode an oracle has,' \
      'so it is refused here rather than discovered later.'
  fi

  # A non-zero accounting cycle, or the menu diverts to interactive setup.
  local cyclea
  cyclea="$(acas_system_column 'CYCLEA')" || acas_die "$EX_DATABASE" \
    'could not read SYSTEM-REC.CYCLEA.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  acas_log "CYCLEA = $cyclea"
  if [[ -z "$cyclea" || "$cyclea" == '0' ]]; then
    acas_die "$EX_PRECONDITION" \
      'SYSTEM-REC.CYCLEA is zero, so the menu would divert into interactive setup.' \
      '[general/general.cbl:L462-L463] is, verbatim:' \
      '    if       scycle = zero' \
      '             go to call-system-setup.' \
      'That path waits for an operator, so the harness would hang rather than fail.' \
      'The accounting cycle is also the filter both passes over the batch file use' \
      '[general/gl070.cbl:L309-L310] and [general/gl070.cbl:L452-L453], so it must be' \
      'pinned by the scenario seed in any case.'
  fi

  # DATE-FORM must match what the scenario says, because the prompt this script
  # waits for is chosen from it.
  local seeded_date_form
  seeded_date_form="$(acas_system_column 'DATE-FORM')" || acas_die "$EX_DATABASE" \
    'could not read SYSTEM-REC.DATE-FORM.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  acas_log "DATE-FORM = $seeded_date_form (scenario says $ACAS_RUN_DATE_FORM)"
  # [general/gl000.cbl:L205] coerces an out-of-range value to 1 before choosing
  # a prompt, so the effective form -- not the stored one -- is what must
  # match.
  local effective_form="$seeded_date_form"
  if [[ ! "$effective_form" =~ ^[123]$ ]]; then
    effective_form=1
    acas_note "DATE-FORM $seeded_date_form is out of range; gl000 coerces it to 1 at [general/gl000.cbl:L205]"
  fi
  if [[ "$effective_form" != "$ACAS_RUN_DATE_FORM" ]]; then
    acas_die "$EX_PRECONDITION" \
      "the seeded DATE-FORM ($effective_form) does not match the scenario's date_form ($ACAS_RUN_DATE_FORM)." \
      'DATE-FORM selects which of three prompts the date program displays' \
      '[general/gl000.cbl:L230-L237] and therefore which digit order must be typed.' \
      'A mismatch would make this script wait for a prompt that never appears, so it' \
      'is caught here instead of surfacing as an unexplained timeout.'
  fi

  # The IRS fan-out switch must already hold the pinned value. This script does
  # NOT write it.
  local seeded_irs
  seeded_irs="$(acas_system_column 'IRS-INSTEAD')" || acas_die "$EX_DATABASE" \
    'could not read SYSTEM-REC.IRS-INSTEAD.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  # The column is char(1); a space and an empty string are the same state.
  local seeded_irs_trimmed="${seeded_irs// /}"
  acas_log "IRS-INSTEAD = '$seeded_irs_trimmed' (scenario pins '$ACAS_RUN_IRS_INSTEAD')"
  if [[ "$seeded_irs_trimmed" != "$ACAS_RUN_IRS_INSTEAD" ]]; then
    acas_die "$EX_PRECONDITION" \
      "the seeded IRS-INSTEAD ('$seeded_irs_trimmed') does not match the scenario ('$ACAS_RUN_IRS_INSTEAD')." \
      'The switch is three-state at [copybooks/wssystem.cob:L179-L181] and is tested' \
      'at 27 sites across the four Sales and Purchase posting programs, so it' \
      'decides WHICH TABLES the run touches. AAP 0.6.4: leaving it at a default' \
      '"would make the affected-table list ambiguous".' \
      'This script does not write it -- seed it with harness/seed.sh, because a run' \
      'that adjusted the state it is about to measure would not be an oracle.'
  fi

  if acas_ops_use_subsystem 'sales'; then
    local sl_autogen
    sl_autogen="$(acas_system_column 'SL-AUTOGEN')" || acas_die "$EX_DATABASE" \
      'could not read SYSTEM-REC.SL-AUTOGEN.' \
      "$(acas_diag_summary "$ACAS_SQL_DIAG")"
    local sl_autogen_trimmed="${sl_autogen// /}"
    acas_log "SL-AUTOGEN = '$sl_autogen_trimmed'"
    if [[ "${sl_autogen_trimmed^^}" == 'Y' ]]; then
      acas_die "$EX_PRECONDITION" \
        'SL-AUTOGEN is "Y", which makes the Sales invoice path NON-DETERMINISTIC.' \
        'The Sales menu calls sl830 before sl055 [sales/sales.cbl:L759-L760]. sl830' \
        'returns immediately when autogen is unused -- [sales/sl830.cbl:L270-L272] is' \
        'if SL-Autogen not = "Y" goback. -- but when it IS "Y" it reaches' \
        '[sales/sl830.cbl:L298]:' \
        '    accept   WS-Temp-Run-Date from DATE YYYYMMDD.' \
        'and feeds that HOST CLOCK reading into the arithmetic that decides which' \
        'autogen invoices to create. Two runs of the same scenario would then differ,' \
        'which is a direct R-6 violation and makes the oracle untrustworthy.' \
        'Seed SL-AUTOGEN as space for every Sales scenario. The autogen tables are' \
        'out of scope and harness/seed.sh deliberately never invokes slautogenLD.'
    fi
    acas_note 'sl830 will run and return immediately; the autogen tables are asserted untouched afterwards'
  fi

  # The payment proof flag. sl100 and pl100 post NOTHING unless it is 2.
  #
  # Checked for EVERY declared cash route, because this function runs ONCE and
  # the selected operation is still the FIRST of the list (see acas_ops_include).
  # period_end_totals declares sl_cash_post second and pl_payment_post fourth, so
  # keying this on the selection skipped BOTH -- and an unproofed flag is exactly
  # the silent pass this check exists to catch: the program displays "Payments Not
  # Proofed", waits for a keystroke and goes to menu-exit, so the run looks clean
  # and writes nothing.
  local flag_entry flag_rest flag_column flag_locator flag
  for flag_entry in \
      'sl_cash_post:S-FLAG-P:sales/sl100.cbl:L296-L301' \
      'pl_payment_post:P-FLAG-P:purchase/pl100.cbl:L288-L293'; do
    acas_ops_include "${flag_entry%%:*}" || continue
    flag_rest="${flag_entry#*:}"
    flag_column="${flag_rest%%:*}"
    flag_locator="${flag_rest#*:}"
    flag="$(acas_system_column "$flag_column")" || acas_die "$EX_DATABASE" \
      "could not read SYSTEM-REC.$flag_column." \
      "$(acas_diag_summary "$ACAS_SQL_DIAG")"
    acas_log "$flag_column = $flag"
    if [[ "$flag" != '2' ]]; then
      acas_die "$EX_PRECONDITION" \
        "SYSTEM-REC.$flag_column is '$flag', so the posting program would exit without posting." \
        "[$flag_locator] tests the proof flag and, when it is not 2, displays a" \
        '"Payments Not Proofed" message, waits for a keystroke and go to menu-exit.' \
        'The run would therefore appear to succeed while writing nothing. Seed the' \
        'flag as 2, which is the state the proof step leaves behind.'
    fi
  done

  # The Cobol reads its OWN credentials out of system.dat, not out of this
  # environment: SYSTEM-REC carries RDBMS-DB-NAME, RDBMS-USER, RDBMS-PASSWD,
  # RDBMS-PORT, RDBMS-HOST and RDBMS-SOCKET.
  local pair column env_value seeded_value
  for pair in "RDBMS-DB-NAME:$ACAS_DB_NAME" "RDBMS-USER:$ACAS_DB_USER" "RDBMS-HOST:$ACAS_DB_HOST"; do
    column="${pair%%:*}"
    env_value="${pair#*:}"
    seeded_value="$(acas_system_column "$column")" || continue
    seeded_value="${seeded_value%"${seeded_value##*[![:space:]]}"}"
    if [[ -n "$seeded_value" && "$seeded_value" != "$env_value" ]]; then
      acas_warn "SYSTEM-REC.$column is '$seeded_value' but the harness environment says '$env_value'; the Cobol connects using the seeded value"
    fi
  done
}


# STAGE 7 -- the data directory: system.dat and the file-handler log
acas_assert_data_dir() {
  ACAS_RUN_CURRENT_STAGE='asserting the data directory'
  acas_stage 'Check 7/8: data directory'

  # system.dat MUST exist, and must not be empty. Paragraph `Open-System'
  # [general/general.cbl:L385-L396] forces the Cobol path, opens key 1, and on
  # `fs-reply not = zero' does `move "sys002" to ws-called / call ws-called
  # using ws-calling-data file-defs / perform System-Open'
  # [general/general.cbl:L391-L396]. So a failed open CALLs sys002
  # INTERACTIVELY, and sys002 is an interactive parameter-entry program: its
  # banner is [common/sys002.cbl:L288] "SYS002 (3.3.02)", and the read failure
  # it reports is [common/sys002.cbl:L604] "SY102 Read Err 1 = " followed by
  # [common/sys002.cbl:L606] "SY104 Fix and Press Enter", displayed at 2401
  # [common/sys002.cbl:L1316] -- after which it waits. Under a pty that is a
  # hang; fed from a pipe it is worse, because the accept returns end-of-file
  # immediately and the program SPINS. Both are refused before a menu spawns.
  local system_dat="$ACAS_DATA/system.dat"
  if [[ ! -f "$system_dat" ]]; then
    acas_die "$EX_PRECONDITION" \
      "system.dat is missing: $system_dat" \
      'The menu opens the system parameter file as a Cobol INDEXED file --' \
      '[general/general.cbl:L385-L396] forces that with `move "00" to' \
      'FA-RDBMS-Flat-Statuses. *> Force Cobol proc.` -- and when the open fails it' \
      'CALLs sys002 INTERACTIVELY, so this harness would hang with no diagnostic.' \
      'Create it before running: sys002 is the program that does so, and it only' \
      'completes on a genuine interactive terminal. Never cobcrun sys002 -- it is a' \
      'CALLed sub-program and segfaults without its linkage records.'
  fi
  if [[ ! -s "$system_dat" ]]; then
    acas_die "$EX_PRECONDITION" \
      "system.dat exists but is EMPTY: $system_dat" \
      'An empty file opens and then fails on the first read, which is the same trap' \
      'as a missing file: [general/general.cbl:L385-L396] CALLs sys002 interactively.' \
      'Verified empirically -- an empty system.dat produces "SYS002 ... System' \
      'Parameters / SY102 Read Err 1 = 23 / SY104 Fix and Press Enter" and then waits.'
  fi
  [[ -r "$system_dat" ]] || acas_die "$EX_PRECONDITION" \
    "system.dat is not readable: $system_dat"
  acas_log "system.dat = present, $(wc -c <"$system_dat" | tr -d ' ') bytes"

  # The file handler logs unconditionally. [copybooks/Test-Data-Flags.cob] declares
  # `03 SW-Testing pic 9 value 1.` as a literal, and that copybook is FROZEN, so
  # logging cannot be switched off without editing a frozen file -- which is
  # forbidden. The log is written to the process working directory, because
  # [common/fhlogger.cbl:L111] assigns it a RELATIVE name:
  #     select Log-File assign "fh-logger.txt"
  # It grows fast -- measured at 473 MB in about three minutes -- so it is rotated
  # at the SCENARIO BOUNDARY by default, and the capacity to do the run at all is
  # checked before the database is touched.
  #
  # Rotation is the default rather than an opt-in because the failure it prevents is
  # not cosmetic: an unbounded log fills the volume, and a volume that fills
  # MID-RUN leaves the database half-posted with no diagnostic pointing at the real
  # cause. Opting out (--no-rotate-fh-log) is still supported for the case where an
  # operator wants one continuous log across several runs.
  #
  # It is never truncated, and the frozen switch is never "fixed" (R-4): the log is
  # MOVED, so every byte the file handler wrote is still readable afterwards.
  acas_rotate_fh_log
  acas_note 'file-handler logging cannot be disabled: [copybooks/Test-Data-Flags.cob] hardcodes SW-Testing value 1 and is frozen'

  # It is written into the working directory, so that directory has to be
  # writable -- already asserted -- and the run has to happen there.
  acas_log "working directory for the run = $ACAS_DATA"
  acas_note 'the run never enters ACAS_REPO, so no frozen file can be touched (AAP 0.8.1)'
}

# THE KEYSTROKE PLAN
# WHY EVERY PROMPT IS MATCHED BEFORE IT IS ANSWERED
# A stream of newlines fed blindly at a menu does not fail; it SUCCEEDS at
# something else. One keystroke landing a field early selects a different menu
# letter, the run posts a different ledger or nothing at all, and the harness
# reports a clean pass. So every keystroke below is emitted only after the
# exact screen text that asks for it has been seen, and every wait has a
# timeout.

# PLAN FORMAT -- seven TAB-separated fields per record:
#     PHASE  STEP_ID  MODE  PATTERN  SEND  LIMIT  CITATION
#   PHASE   0 global, 1 strict prefix, 2 reactive body, 3 strict suffix
#   MODE    forbid    a pattern that voids the run the moment it appears
#           expect    PHASE 1 or 3: must appear, in order, or the run fails
#           react     PHASE 2: answered whenever it appears, up to LIMIT times
#           terminal  PHASE 2: ends the reactive phase when it appears
#   PATTERN a literal substring, matched against the transcript after the ANSI
#           escapes are stripped and runs of whitespace collapsed
#   SEND    keystrokes; \r is Return, \e is Escape, empty sends nothing
#   LIMIT   how many times a react rule may fire before the run is called stuck

# PHASE 2 is REACTIVE and not a fixed sequence, and that is deliberate: the
# three menus branch, and the branch they take is the specification. On a
# General posting cycle the gate at [general/general.cbl:L810-L811] decides
# whether gl071 and gl072 run at all, and this script must not presume either
# outcome. It answers whatever prompts appear, records which anchors were seen,
# and lets the gate outcome be DERIVED from that record (R-3, R-4).

# acas_plan_add <phase> <step-id> <mode> <pattern> <send> <limit> <citation>
# =============================================================================
# THE FILE-HANDLER LOG
#
# [copybooks/Test-Data-Flags.cob] declares `03 SW-Testing pic 9 value 1.' as a
# LITERAL, and that copybook is frozen, so file-handler logging cannot be turned
# off without editing a frozen file. [common/fhlogger.cbl:L111] assigns the log a
# RELATIVE name -- `select Log-File assign "fh-logger.txt"' -- so it lands in the
# process working directory, which for this harness is $ACAS_DATA. Measured
# growth: 473 MB in roughly three minutes.

# The rotated log is labelled and kept, never overwritten.
acas_fh_rotation_target() {
  local dir="$1" base="$2" n=1 candidate
  candidate="$dir/$base.001"
  while [[ -e "$candidate" ]]; do
    n=$(( n + 1 ))
    if (( n > 999 )); then
      # Refusing beats silently overwriting the oldest evidence.
      acas_die "$EX_CAPACITY" \
        "there are already 999 rotated copies of fh-logger.txt in $dir." \
        'Nothing is overwritten automatically, so this is a refusal rather than a' \
        'silent loss. Archive or delete some of them, or pass --no-rotate-fh-log.'
    fi
    candidate="$(printf '%s/%s.%03d' "$dir" "$base" "$n")"
  done
  printf '%s' "$candidate"
}

acas_rotate_fh_log() {
  local fh_log="$ACAS_DATA/fh-logger.txt"
  local fh_bytes=0

  if [[ -f "$fh_log" ]]; then
    fh_bytes="$(wc -c <"$fh_log" | tr -d ' ')"
    acas_log "fh-logger.txt = $fh_bytes bytes before the run"
  else
    acas_log 'fh-logger.txt = absent; the file handler will create it during the run'
  fi

  # Capacity was asserted much earlier, by acas_assert_fh_log_capacity, so that
  # a volume with no room refuses before the database is contacted at all.

  if [[ ! -f "$fh_log" ]]; then
    return 0
  fi

  if (( ! ACAS_RUN_ROTATE_FH_LOG )); then
    acas_warn "--no-rotate-fh-log: fh-logger.txt keeps growing from its current $fh_bytes bytes, and this run appends to it"
    return 0
  fi

  # The destination is under run-logs/<scenario>/, which is OUTSIDE every
  # compared tree, so a multi-hundred-megabyte log can never enter a dump or a
  # diff.
  local dest_dir="$ACAS_OUT/run-logs/$ACAS_RUN_SCENARIO"
  acas_assert_outside_repo 'the fh-logger rotation directory' "$dest_dir"
  acas_assert_outside_tree 'the fh-logger rotation directory' "$dest_dir" \
    "$ACAS_OUT/$ACAS_RUN_SCENARIO" \
    'The rotated log would be compared byte for byte between the two cycles, and it' \
    'records host timings, so every diff would be non-empty (R-6).'

  mkdir -p "$dest_dir" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "could not create the fh-logger rotation directory: $dest_dir"

  local rotated
  # Named after the RUN, not after an operation. The rotation happens exactly
  # once, before the first drive, so for a four-operation scenario a name taken
  # from the selected operation would claim a per-operation rotation that does
  # not happen -- and would attribute the PREVIOUS run's log to this run's first
  # operation.
  rotated="$(acas_fh_rotation_target "$dest_dir" 'fh-logger.pre-run.txt')"

  # Bounded: this can be a cross-device copy of a very large file.
  acas_deadline_prefix "$ACAS_TIMEOUT_ROTATE"
  local rc=0 started elapsed
  started="$SECONDS"
  "${ACAS_DEADLINE_ARGV[@]}" mv -f -- "$fh_log" "$rotated" 2>/dev/null || rc=$?
  elapsed=$(( SECONDS - started ))
  acas_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_ROTATE" \
    'ACAS_TIMEOUT_ROTATE' "rotating fh-logger.txt ($fh_bytes bytes)"

  if (( rc != 0 )); then
    acas_die "$EX_PRECONDITION" \
      "could not rotate $fh_log to $rotated (status $rc)." \
      'The log is MOVED rather than truncated, so nothing the file handler wrote is' \
      'discarded. Pass --no-rotate-fh-log to append to the existing log instead.'
  fi

  ACAS_RUN_FH_ROTATED="$rotated"
  acas_log "rotated $fh_bytes bytes to $rotated"
  acas_note 'the rotated log is kept, not overwritten, and lives outside every compared tree'
}

acas_plan_add() {
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" "$6" "$7" \
    >>"$ACAS_RUN_PLAN_FILE"
}

# ---------------------------------------------------------------------------
#  TRUSTED PLAN CONTROLS AND UNTRUSTED SCENARIO DATA ARE NOT THE SAME
#  THING, AND THEY SHARED ONE ESCAPE NAMESPACE.
#
#  A plan row's `send' field is TRUSTED PLAN TEXT. The pty driver's `decode_send'
#  expands `\r', `\n', `\e', `\t' and `\\' ANYWHERE in it, which is exactly right for
#  the terminator this script appends to a keystroke -- and exactly wrong for the
#  scenario-supplied value the terminator is appended TO. Both arrived in the same
#  string, so a backslash in a scenario value was read as the start of a control
#  sequence rather than as a backslash: `run_date_text: 01\r02\r2025' would have been
#  typed at the compiled program as three separate ENTER-terminated fields.
#
#  THE PARITY CONSEQUENCE IS THE POINT, not the injection. The migrated leg receives
#  scenario values as ARGV -- no escape layer, no expansion, the bytes as written. So
#  a value the oracle leg re-interpreted and the migrated leg took literally makes
#  the two legs receive DIFFERENT LOGICAL INPUTS, and a diff drawn across that pair
#  measures the escape layer rather than the accounting (R-6).
#
#  This function is the boundary. Every backslash in untrusted text is doubled, so
#  `decode_send' emits precisely one literal backslash for it and the data reaches
#  the program BYTE FOR BYTE as the scenario wrote it -- while the `\r' this script
#  appends outside the call still means ENTER.
#
#  Ordering is not incidental: the backslash must be doubled FIRST or a doubling pass
#  would re-escape its own output. `${var//\\/\\\\}' is a single simultaneous
#  substitution, so it cannot.
#
#  Currently every value reaching a send field is also pattern-validated to a closed
#  set that contains no backslash, so this is not a live injection today. It is
#  applied anyway, at the boundary, because the validation and the send site are
#  hundreds of lines apart: the next scenario key routed into a keystroke, or one
#  relaxation of one pattern, would otherwise reintroduce the divergence silently.
#  A test asserts that no send field interpolates a variable without coming through
#  here.
# ---------------------------------------------------------------------------
acas_plan_escape_data() {
  local raw="$1"
  printf '%s' "${raw//\\/\\\\}"
}

acas_plan_forbidden() {
  local entry code reason locator
  for entry in "${ACAS_RUN_FORBIDDEN[@]}"; do
    # Split on '|' -- see the note on ACAS_RUN_FORBIDDEN for why not ':'.
    IFS='|' read -r code reason locator <<<"$entry"
    acas_plan_add 0 "forbid-$code" forbid "$code" '' 0 "$reason [$locator]"
  done
}

# The date-entry step. All four menus force Date Entry on the first pass, so no
# keystroke selects it.

acas_plan_date_entry() {
  local order
  case "$ACAS_RUN_DATE_FORM" in
    1) order='dd/mm/yyyy' ;;
    2) order='mm/dd/yyyy' ;;
    3) order='yyyy/mm/dd' ;;
  esac
  # Each subsystem has its OWN date-entry program, and the citation must name
  # the one that actually runs.
  local locator
  case "$ACAS_RUN_SUBSYSTEM" in
    general)  locator='general/gl000.cbl:L230-L239'  ;;  # prompts L230/233/236, accept L239
    sales)    locator='sales/sl000.cbl:L226-L235'    ;;  # prompts L226/229/232, accept L235
    purchase) locator='purchase/pl000.cbl:L236-L245' ;;  # prompts L236/239/242, accept L245
    irs)      locator='irs/irs000.cbl:L222-L231'     ;;  # accept L231, at column 0848
  esac
  acas_plan_add 1 'date-entry' expect "date as $order" "$(acas_plan_escape_data "$ACAS_RUN_DATE_TEXT")\\r" 1 \
    "pinned run date, typed in the order DATE-FORM $ACAS_RUN_DATE_FORM selects [$locator]"
}

# The three letter-menus. One character, and NO Return: the accept carries AUTO
# [general/general.cbl:L591-L593] accept menu-reply at 0644 with ...
acas_plan_menu_select() {
  acas_plan_add 1 'menu-select' expect "$ACAS_RUN_MENU_ANCHOR" "$ACAS_RUN_MENU_KEY" 1 \
    "select '$ACAS_RUN_MENU_KEY' -> $ACAS_RUN_PARAGRAPH [$ACAS_RUN_PARAGRAPH_LOCATOR]"
}


# THE EXIT SIDE EFFECT IS NOT THE SAME IN ALL FOUR MENUS, and the difference
# decides which extra tables a run touches, so it is stated per subsystem
# rather than generalised from General.

# The RDB half of each block is guarded by `if File-System-Used NOT = zero',
# which is why a zero FILE-SYSTEM-USED is asserted as a silent-pass trap.
acas_plan_menu_exit() {
  local keys locator
  case "$ACAS_RUN_SUBSYSTEM" in
    general)  keys='keys 1, 2 and 4 (SYSTEM-REC, SYSDEFLT-REC, SYSTOT-REC)'
              locator='general/general.cbl:L656-L692' ;;
    sales)    keys='keys 1 and 4 only (SYSTEM-REC, SYSTOT-REC; no SYSDEFLT-REC)'
              locator='sales/sales.cbl:L628-L657' ;;
    purchase) keys='keys 1 and 4 only (SYSTEM-REC, SYSTOT-REC; no SYSDEFLT-REC)'
              locator='purchase/purchase.cbl:L621-L651' ;;
    *)        keys='key 1 only (SYSTEM-REC)'
              locator='irs/irs.cbl:L755-L775' ;;
  esac
  acas_plan_add 2 'menu-exit' terminal "$ACAS_RUN_MENU_ANCHOR" 'X' 1 \
    "leave the menu cleanly; the exit path rewrites $keys [$locator]"
}

# Prompts that merely pause for acknowledgement (D-4).
acas_plan_ack() {
  local step="$1" pattern="$2" limit="$3" citation="$4"
  acas_plan_add 2 "$step" react "$pattern" '\r' "$limit" "$citation"
}



# The code is raised inside gl070 on finding a batch left open
# [general/gl070.cbl:L287-L290]. The diagnostic report has two separate ACCEPTs:
# its page choice at L421 does NOT carry AUTO, so selecting X requires Return;
# the end-report acknowledgement at L439 then requires a second Return.
acas_plan_gl_post_cycle() {
  acas_plan_date_entry
  acas_plan_menu_select

  # gl070's own banners. Recorded, never required: Phase 2 is not reached when
  # the gate fires.
  acas_plan_add 2 'gl070-phase1' react 'Phase - 1. Batch Check' '' 4 \
    'gl070 Phase 1 banner [general/gl070.cbl:L284]'
  acas_plan_add 2 'gl070-phase2' react 'Phase - 2. Transaction Pre-process' '' 4 \
    'gl070 Phase 2 banner [general/gl070.cbl:L292]'

  # The gate-fired path: gl060a's paginated Batch Status Report.
  acas_plan_add 2 'gl060a-page' react 'for next screen or' 'X\r' 12 \
    'gl060a report paging, reached ONLY when the GL gate fires [general/gl070.cbl:L416-L421]'
  acas_plan_ack 'gl060a-exit' 'Type return to exit.' 4 \
    'gl060a end-of-report acknowledgement [general/gl070.cbl:L435-L439]'

  acas_plan_add 2 'gl071-sort' react 'Sorting.......Please wait' '' 2 \
    'gl071 sort banner; its output ordering is what gl072 depends on [general/gl071.cbl:L170]'
  acas_plan_add 2 'gl072-phase4' react 'Phase - 4. Transaction Update' '' 2 \
    'gl072 posting banner [general/gl072.cbl:L274]'

  acas_plan_menu_exit
}

# gl_end_of_cycle -- general, letter "I", load09 -> gl080
# [general/general.cbl:L817-L821] G-2. gl080 opens with an UNCONDITIONAL gate
# [general/gl080.cbl:L295-L302].
acas_plan_gl_end_of_cycle() {
  acas_plan_date_entry
  acas_plan_menu_select

  local send citation
  if [[ "$ACAS_RUN_GL080_PROCEED" == 'A' ]]; then
    send='A'
    citation='G-2: ABORT gl080 -- goback, nothing written [general/gl080.cbl:L295-L302]'
  else
    send='\r'
    citation='G-2: proceed with gl080; Return leaves keyed-reply at the space the program itself moved in [general/gl080.cbl:L295-L302]'
  fi
  acas_plan_add 2 'gl080-gate' react 'GL087' "$send" 2 "$citation"

  acas_plan_add 2 'gl080-unproofed' react 'GL088' '\r' 2 \
    'gl080 found unproofed or unposted batches and will end after this [general/gl080.cbl:L308-L313]'
  acas_plan_ack 'gl080-note' 'GL012' 3 \
    'gl080 note-and-return acknowledgement [general/gl080.cbl:L310]'

  # ---------------------------------------------------------------------------
  #  THE DECLARED ANSWER, NOT A HARD-CODED ONE.
  #
  #  GL084 is a genuine choice -- "<0> to signify change made or <9> to abort this
  #  run" -- so typing `0' whatever the scenario said would drive a choice the
  #  scenario did not declare. The value is the scenario's, and the binding gate above
  #  has already refused every value this leg cannot drive provably, so it is `0' here.
  #
  #  Escaped at the boundary even though the gate has narrowed it to a single
  #  digit: the escaping belongs to the send site, not to whatever validation happens
  #  to precede it today.
  #
  #  REACHABILITY, STATED PLAINLY: `disk-change' runs only from `gl080b', which runs
  #  only when SYSTEM-REC.Arch = "Y" [general/gl080.cbl:L315],
  #  [copybooks/wssystem.cob:L164-L165]. No fixture seeds that, so this rule and the
  #  path rule below have never fired in any run. They are `react' rules, which fire
  #  only if the screen appears, so an unreachable prompt costs nothing -- but the
  #  step is written correctly rather than left as a hard-coded placeholder, and its
  #  untested status is recorded in docs/migration/ambiguity-resolutions.md.
  # ---------------------------------------------------------------------------
  acas_plan_add 2 'gl080-archive' react 'GL084' \
    "$(acas_plan_escape_data "$ACAS_RUN_DISK_CHANGE")\\r" 3 \
    "gl080 disk-change option; scenario declares $ACAS_RUN_DISK_CHANGE [general/gl080.cbl:L539-L549]"

  #  THE PROMPT THIS PLAN HAD NO STEP FOR AT ALL.
  #
  #  Answering GL084 with 0 falls through to a SECOND prompt the plan never
  #  mentioned: `accept file-2 ... with update' [general/gl080.cbl:L555], an update
  #  field pre-loaded with the archive path built at
  #  [general/gl080.cbl:L530-L537]. A bare Return accepts that built path unchanged,
  #  which is the frozen default and the only behaviour this leg supports -- the
  #  binding gate refuses archive_path_override precisely because overriding an
  #  update field cannot be driven provably.
  #
  #  Without this step the run would answer GL084 and then sit at an unanswered
  #  accept until the phase deadline, reported as a pty timeout rather than as the
  #  missing plan step it actually was. A leading space would send the program back
  #  to the option prompt [general/gl080.cbl:L556-L557], so a bare Return is also
  #  the only answer that makes progress.
  acas_plan_add 2 'gl080-archive-path' react 'Current path/name is' '\r' 3 \
    'gl080 archive-path update accept; bare Return keeps the built path, which is the frozen default [general/gl080.cbl:L553-L557]'

  acas_plan_add 2 'gl080-phase1' react 'Phase - 1. Batch Check' '' 3 \
    'gl080 Phase 1 banner [general/gl080.cbl:L306]'
  acas_plan_add 2 'gl080-phase2' react 'Phase - 2. Transaction Archiving' '' 3 \
    'gl080 Phase 2 banner [general/gl080.cbl:L316]'
  acas_plan_add 2 'gl080-phase3' react 'Phase - 3. Transaction Deletion' '' 3 \
    'gl080 Phase 3 banner; note it EXECUTES after Phase 4 [general/gl080.cbl:L319]'
  acas_plan_add 2 'gl080-phase5' react 'Phase - 5. End of Period Processing' '' 3 \
    'gl080 Phase 5 banner [general/gl080.cbl:L336]'

  acas_plan_menu_exit
}

# sl_invoice_post -- sales, letter "G", load07.


# The predicate is `ws-term-code not = zero' and it appears TWICE
# [sales/sales.cbl:L761-L762], [sales/sales.cbl:L765-L766].

# The error acknowledgements in sl055 and sl060 are guarded by `if WS-Caller
# not = "xl150"' and the Sales menu sets `move "sales" to ws-caller'
# [sales/sales.cbl:L481], so they DO fire on this path and must be answered.
acas_plan_sl_invoice_post() {
  acas_plan_date_entry
  acas_plan_menu_select

  acas_plan_add 2 'sl830-banner' react 'Autogen Posting' '' 2 \
    'sl830 runs first and is OUT OF SCOPE; it returns at once while SL-Autogen is not "Y" [sales/sl830.cbl:L270-L272]'
  acas_plan_add 2 'sl055-banner' react 'Invoice Post Extract' '' 2 \
    'sl055 banner [sales/sl055.cbl:L352]'
  acas_plan_add 2 'sl060-banner' react 'Invoice Posting & Report' '' 2 \
    'sl060 banner [sales/sl060.cbl:L419]'

  acas_plan_add 2 'sl-note-error' react 'SL002' '' 6 \
    'companion diagnostic only; the specific error anchor sends the acknowledgement so a repeated unchanged SL002 screen cannot consume an extra key [sales/sales.cbl:L481]'
  acas_plan_ack 'sl-continue' 'SL003' 6 \
    'sl060 hit-return-to-continue [sales/sl060.cbl:L262]'
  acas_plan_ack 'sl055-no-anal' 'SL125' 3 \
    'sl055 analysis file absent [sales/sl055.cbl:L256]'
  acas_plan_ack 'sl055-unprinted' 'SL122' 3 \
    'sl055 unprinted invoices exist [sales/sl055.cbl:L253]'
  acas_plan_ack 'sl055-emergency' 'SL123' 3 \
    'sl055 emergency analysis records created [sales/sl055.cbl:L254]'
  acas_plan_ack 'sl055-update' 'SL126' 3 \
    'sl055 you-will-need-to-update-this [sales/sl055.cbl:L257]'
  acas_plan_ack 'sl055-oi2-write' 'SL121' 3 \
    'sl055 open-item-2 write error [sales/sl055.cbl:L252]'
  acas_plan_ack 'sl060-otm3-write' 'SL130' 6 \
    'sl060 open-item-3 write error; match this changing anchor because curses may not redraw the identical SL002 companion prompt [sales/sl060.cbl:L590-L601]'
  acas_plan_ack 'sl060-zero-value' 'SL131' 3 \
    'sl060 zero-value CR swop [sales/sl060.cbl:L265]'
  acas_plan_ack 'sl060-batch-write' 'SL132' 3 \
    'sl060 batch-file write error [sales/sl060.cbl:L266]'

  acas_plan_menu_exit
}

# sl_cash_post -- sales, letter "K", load11 -> sl100
# [sales/sales.cbl:L792-L796] G-3. sl100 asks an UNCONDITIONAL YES/NO
# [sales/sl100.cbl:L310-L318].
acas_plan_sl_cash_post() {
  acas_plan_date_entry
  acas_plan_menu_select

  acas_plan_add 2 'sl100-confirm' react 'OK to Post Payment Transactions' \
    "$(acas_plan_escape_data "$ACAS_RUN_PAYMENT_CONFIRM")\\r" 3 \
    "G-3: sl100 posting confirmation = $ACAS_RUN_PAYMENT_CONFIRM [sales/sl100.cbl:L310-L318]"
  acas_plan_ack 'sl100-not-proofed' 'SL137' 2 \
    'sl100 payments-not-proofed; Stage 6 asserts S-FLAG-P = 2 so this should not fire [sales/sl100.cbl:L296-L301]'
  acas_plan_ack 'sl100-note-error' 'SL002' 6 \
    'sl100 error acknowledgement [sales/sl100.cbl:L211]'
  acas_plan_ack 'sl100-batch-write' 'SL132' 3 \
    'sl100 batch-file write error [sales/sl100.cbl:L214]'

  acas_plan_menu_exit
}


# BOTH the pl830 call AND the gate are COMMENTED OUT [purchase/purchase.cbl:
# L755-L758]. Purchase has NO ABORT GATE AT ALL.
acas_plan_pl_order_post() {
  acas_plan_date_entry
  acas_plan_menu_select

  acas_plan_add 2 'pl055-banner' react 'Invoice Post Extract' '' 2 \
    'pl055 banner [purchase/pl055.cbl:L294]'
  acas_plan_add 2 'pl060-banner' react 'Purchase Orders Posting Report' '' 2 \
    'pl060 banner; reached UNCONDITIONALLY -- Purchase has no gate [purchase/purchase.cbl:L755-L758]'

  acas_plan_ack 'pl-note-error' 'PL002' 6 \
    'pl060 error acknowledgement [purchase/pl060.cbl:L250]'
  acas_plan_ack 'pl-continue' 'PL003' 6 \
    'pl055/pl060 hit-return-to-continue [purchase/pl055.cbl:L217]'
  acas_plan_ack 'pl055-note-details' 'PL006' 4 \
    'pl055 note-details-and-hit-return [purchase/pl055.cbl:L218]'
  acas_plan_ack 'pl060-oi5-write' 'PL130' 3 \
    'pl060 open-item-5 write error [purchase/pl060.cbl:L253]'
  acas_plan_ack 'pl060-zero-value' 'PL131' 3 \
    'pl060 zero-value CR swop [purchase/pl060.cbl:L254]'
  acas_plan_ack 'pl060-batch-write' 'PL132' 3 \
    'pl060 batch-file write error [purchase/pl060.cbl:L255]'
  acas_plan_ack 'pl060-missing-recs' 'PL133' 3 \
    'pl060 records missing in the purchase file [purchase/pl060.cbl:L256]'

  acas_plan_menu_exit
}

# pl_payment_post -- purchase, letter "L", load12 -> pl100
# [purchase/purchase.cbl:L786-L790] G-3 again, but the prompt text DIVERGES
# from sl100's and is matched separately.
acas_plan_pl_payment_post() {
  acas_plan_date_entry
  acas_plan_menu_select

  acas_plan_add 2 'pl100-confirm' react 'OK to post payment transactions' \
    "$(acas_plan_escape_data "$ACAS_RUN_PAYMENT_CONFIRM")\\r" 3 \
    "G-3: pl100 posting confirmation = $ACAS_RUN_PAYMENT_CONFIRM; note the wording differs from sl100 [purchase/pl100.cbl:L302-L311]"
  acas_plan_ack 'pl100-not-proofed' 'PL137' 2 \
    'pl100 payments-not-proofed; Stage 6 asserts P-FLAG-P = 2 so this should not fire [purchase/pl100.cbl:L288-L293]'
  acas_plan_ack 'pl100-note-error' 'PL002' 6 \
    'pl100 error acknowledgement [purchase/pl100.cbl:L204]'
  acas_plan_ack 'pl100-batch-write' 'PL132' 3 \
    'pl100 batch-file write error [purchase/pl100.cbl:L207]'

  acas_plan_menu_exit
}



# G-1 is answered here. [irs/irs030.cbl:L1715-L1727] is paragraph EOJ-q1:
# display "Can I clear the Ledgers Posting file? [Y]" at 1401 ...
acas_plan_irs_post() {
  acas_plan_date_entry

  acas_plan_add 1 'irs-menu-select' expect "$ACAS_RUN_IRS_MENU_ANCHOR" '4' 1 \
    'IRS menu option 4 -> irs030, three-parameter linkage, no to-day [irs/irs.cbl:L666-L672]'
  acas_plan_add 1 'irs030-option' expect "$ACAS_RUN_IRS_OPTION_ANCHOR" '66\r' 1 \
    'irs030 run option 66, "Add PL or SL Postings from file" [irs/irs030.cbl:L599-L601]'

  acas_plan_add 2 'irs030-updating' react 'Updating Nominal Ledger' '' 2 \
    'Ledger-Postings-Add is running [irs/irs030.cbl:L1616]'
  acas_plan_add 2 'irs030-complete' react 'Processing Complete on' '' 2 \
    'Ledger-Postings-Add finished [irs/irs030.cbl:L1713-L1714]'

  # G-1. LIMIT 2 rather than 1: one legitimate appearance, and one more to
  # catch a rejected answer as a failure rather than as a hang.
  acas_plan_add 2 'irs030-clear' react 'Can I clear the Ledgers Posting' \
    "$(acas_plan_escape_data "$ACAS_RUN_IRS_CLEAR")\\r" 2 \
    "G-1: clear the transfer file = $ACAS_RUN_IRS_CLEAR; \"Y\" issues the bridge's bounded delete against PSIRSPOST-REC [irs/irs030.cbl:L1715-L1724]"
  acas_plan_ack 'irs030-note-counts' 'Note counts and any messages' 2 \
    'pure acknowledgement, no database effect [irs/irs030.cbl:L1725-L1726]'

  acas_plan_add 2 'irs030-no-postings' react 'IR031' '' 2 \
    'no ledger posting file found; irs030 aborts the section with no accept [irs/irs030.cbl:L1579-L1581]'
  acas_plan_ack 'irs030-vat-missing' 'IR035' 4 \
    'VAT account missing, one acknowledgement per account [irs/irs030.cbl:L1447-L1458]'
  acas_plan_ack 'irs030-irsub1-31' 'IR03A' 3 \
    'IRSUB1-31 returned an error [irs/irs030.cbl:L1596-L1600]'
  acas_plan_ack 'irs030-irsub1-32' 'IR03B' 3 \
    'IRSUB1-32 returned an error [irs/irs030.cbl:L1606-L1610]'
  acas_plan_ack 'irs030-invalid-debit' 'IR032' 6 \
    'debit account missing after the indexed read; acknowledge the diagnostic before irs030 rejects the whole posting [irs/irs030.cbl:L1627-L1634]'
  acas_plan_ack 'irs030-invalid-credit' 'IR033' 6 \
    'credit account missing after the debit rewrite; acknowledge the diagnostic before irs030 preserves the reproduced half-post and continues [irs/irs030.cbl:L1645-L1652]'
  acas_plan_ack 'irs030-posting-write' 'IR914' 3 \
    'IRS posting-table write error; acknowledge the diagnostic before irs030 leaves through EOJ [irs/irs030.cbl:L1673-L1678]'
  acas_plan_ack 'irs030-nominal-err' 'IR912' 3 \
    'irsnominalMT error; irs030 acknowledges and gobacks [irs/irs030.cbl:L1437-L1443]'
  acas_plan_ack 'irs030-sy008' 'SY008' 4 \
    'note-message-and-hit-return [irs/irs030.cbl:L392]'

  # Back at irs030's own run-option menu: leave it with Return.
  acas_plan_add 2 'irs030-exit' terminal "$ACAS_RUN_IRS_OPTION_ANCHOR" '\r' 1 \
    'Return exits irs030 to the System Menu; Main-Loop pre-zeroes w [irs/irs030.cbl:L571-L572], [irs/irs030.cbl:L587-L589]'

  # And then leave the IRS menu itself. "X" or Escape both work
  # [irs/irs.cbl:L751-L753].
  acas_plan_add 3 'irs-menu-exit' expect "$ACAS_RUN_IRS_MENU_ANCHOR" 'X' 1 \
    'leave the IRS menu [irs/irs.cbl:L751-L753]'
}

# Build the plan for the resolved operation.
acas_build_plan() {
  ACAS_RUN_CURRENT_STAGE='building the keystroke plan'
  acas_stage 'Check 8/8: keystroke plan'

  # The plan file was already created safely at Step 3 (acas_open_transcript),
  # but this is Step 8 -- five of this script's own preflight steps later -- so
  # this line EMPTIES it before the builders append to it.  Step numbers here are
  # local to this script; the protocol's ten stages are in harness/normalize.py.
  acas_create_private_file "$ACAS_RUN_PLAN_FILE" 'the keystroke plan'
  acas_plan_forbidden

  case "$ACAS_RUN_OPERATION" in
    gl_post_cycle)   acas_plan_gl_post_cycle ;;
    gl_end_of_cycle) acas_plan_gl_end_of_cycle ;;
    sl_invoice_post) acas_plan_sl_invoice_post ;;
    sl_cash_post)    acas_plan_sl_cash_post ;;
    pl_order_post)   acas_plan_pl_order_post ;;
    pl_payment_post) acas_plan_pl_payment_post ;;
    irs_post)        acas_plan_irs_post ;;
    *) acas_die "$EX_USAGE" "internal: no plan builder for '$ACAS_RUN_OPERATION'." ;;
  esac

  local total
  total="$(grep -c '' "$ACAS_RUN_PLAN_FILE" || true)"
  acas_log "plan records = $total (written to $ACAS_RUN_PLAN_FILE)"
  acas_print_plan
}

# Render the plan for a human.
ACAS_SPLIT=()
acas_split_tabs() {
  local rest="$1"
  ACAS_SPLIT=()
  while true; do
    ACAS_SPLIT+=("${rest%%$'\t'*}")
    case "$rest" in
      *$'\t'*) rest="${rest#*$'\t'}" ;;
      *)       break ;;
    esac
  done
}

acas_print_plan() {
  local line phase step mode pattern send limit citation label
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -n "$line" ]] || continue
    acas_split_tabs "$line"
    phase="${ACAS_SPLIT[0]-}"
    step="${ACAS_SPLIT[1]-}"
    mode="${ACAS_SPLIT[2]-}"
    pattern="${ACAS_SPLIT[3]-}"
    send="${ACAS_SPLIT[4]-}"
    limit="${ACAS_SPLIT[5]-}"
    citation="${ACAS_SPLIT[6]-}"
    [[ -n "$phase" ]] || continue
    case "$send" in
      '')     label='(nothing sent)' ;;
      '\r')   label='<Return>' ;;
      *)      label="${send//\\r/<Return>}"
              label="${label//\\e/<Escape>}"
              ;;
    esac
    case "$mode" in
      forbid)
        acas_log "$(printf 'FORBID   %-24s on %-34s %s' "$step" "\"$pattern\"" "$citation")"
        ;;
      expect)
        acas_log "$(printf 'EXPECT   %-24s on %-34s send %-14s %s' "$step" "\"$pattern\"" "$label" "$citation")"
        ;;
      react)
        acas_log "$(printf 'REACT    %-24s on %-34s send %-14s x%-3s %s' "$step" "\"$pattern\"" "$label" "$limit" "$citation")"
        ;;
      terminal)
        acas_log "$(printf 'TERMINAL %-24s on %-34s send %-14s %s' "$step" "\"$pattern\"" "$label" "$citation")"
        ;;
    esac
  done <"$ACAS_RUN_PLAN_FILE"
}


# A REAL pty of exactly 24x80 is mandatory, for two independent reasons. *
# Smaller than 24x80 the menu REFUSES.

# `pty.fork' is used rather than `script -q -c' because the driver has to MATCH
# a prompt and then answer it, and `script' can only feed a fixed stream.

# Exit codes, mapped to EX_DRIVE by the caller with a specific message.
acas_drive() {
  ACAS_RUN_CURRENT_STAGE='driving the compiled menu over a pty'
  acas_stage "Driving: $ACAS_RUN_SUBSYSTEM menu, operation $ACAS_RUN_OPERATION"

  # THE EXECUTABLE AND THE OPERATION MUST AGREE, CHECKED HERE
  #
  # Asserted at the drive rather than trusted, because the failure it catches is
  # silent: a menu letter is a single character and every menu accepts one, so
  # sending the purchase letter to the sales menu selects a DIFFERENT, valid
  # option and the run proceeds into a program the plan was not written for.
  # MEASURED before this check existed: "H" -- pl_order_post's letter -- reached
  # the Sales menu's (H) Payment Input and sat in SL080's data-entry screen until
  # the reactive budget expired. The only evidence was a timeout.
  [[ -n "$ACAS_RUN_EXECUTABLE" ]] || acas_die "$EX_ORACLE" \
    "internal: no menu executable is resolved for operation '$ACAS_RUN_OPERATION'."
  [[ "$ACAS_RUN_EXECUTABLE" == */"$ACAS_RUN_SUBSYSTEM"/"$ACAS_RUN_SUBSYSTEM" ]] || \
    acas_die "$EX_ORACLE" \
      "internal: the resolved executable does not belong to this operation's menu." \
      "operation  = $ACAS_RUN_OPERATION ($ACAS_RUN_SUBSYSTEM menu)" \
      "executable = $ACAS_RUN_EXECUTABLE" \
      'A menu letter is one character and every menu accepts one, so driving the' \
      'wrong menu selects a different valid option instead of failing.'
  [[ -x "$ACAS_RUN_EXECUTABLE" ]] || acas_die "$EX_ORACLE" \
    "the $ACAS_RUN_SUBSYSTEM menu executable is missing or not executable." \
    "expected: $ACAS_RUN_EXECUTABLE" \
    'Run harness/build_oracle.sh first.'

  acas_log "executable = $ACAS_RUN_EXECUTABLE"
  acas_log "geometry   = ${ACAS_RUN_ROWS}x${ACAS_RUN_COLS} (pinned, not 'at least')"
  acas_log "per-prompt timeout = ${ACAS_RUN_TIMEOUT}s"

  # [general/general.cbl:L369-L370] and [general/gl000.cbl:L172-L173] -- but
  # they are exported here as well so the runtime sees them from the first
  # screen.
  export COB_SCREEN_EXCEPTIONS='Y'
  export COB_SCREEN_ESC='Y'
  export TERM="${TERM:-xterm}"
  # D-5. Without this GnuCobol waits for a keypress when a screen program ends,
  # which would hang the harness after the menu exits.
  export COB_EXIT_WAIT='off'
  export LINES="$ACAS_RUN_ROWS"
  export COLUMNS="$ACAS_RUN_COLS"
  export COB_COPY_DIR="${COB_COPY_DIR:-$ACAS_BUILD/copybooks}"
  export COBCPY="${COBCPY:-$ACAS_BUILD/copybooks}"
  # [etc/ld.so.conf.d/gnucobol.conf] is exactly four lines; they are reproduced
  # here so libcob and libmysqlclient resolve without depending on ldconfig
  # having been run in the image.
  local ld='/usr/local/lib/gnucobol:/usr/local/lib:/usr/local/mysql/lib:/usr/lib'
  if [[ -n "${LD_LIBRARY_PATH:-}" ]]; then
    export LD_LIBRARY_PATH="$ld:$LD_LIBRARY_PATH"
  else
    export LD_LIBRARY_PATH="$ld"
  fi

  if (( ACAS_RUN_DRY_RUN )); then
    acas_note '--dry-run: the plan above is complete and every precondition passed; no menu was spawned'
    return 0
  fi

  # From here on the database may change, so the exit trap must say so.
  ACAS_RUN_DRIVEN=1

  local rc=0
  # The menu is invoked with NO ARGUMENTS, deliberately.
  # [copybooks/Proc-Get-Env-Set-Files.cob:L37] zz020-Get-Program-Args accepts
  # only a blank first argument, or "NONE", "NULL" or "ACAS_LEDGERS=".
  acas_deadline_prefix "$ACAS_TIMEOUT_DRIVE"
  local drive_started="$SECONDS"
  set +e
  # STARTED IN THE BACKGROUND AND WAITED FOR, RATHER THAN RUN IN THE FOREGROUND.
  # Nothing about the drive itself changes -- the deadline wrapper, the arguments and
  # the here-document are identical, and `wait' yields exactly the status the
  # foreground form did. What changes is that the pid is KNOWN while the drive is in
  # progress, which is what lets acas_on_signal stop the driver when this script is
  # killed instead of leaving it, and the compiled menu it spawned, running against
  # the database after the run lock has been released. It also means the driver gets
  # its TERM on the manual-kill path, so its own handler flushes the transcript there
  # too and the evidence guarantee is not limited to the wall-clock-deadline path.
  "${ACAS_DEADLINE_ARGV[@]}" python3 - \
    "$ACAS_RUN_PLAN_FILE" \
    "$ACAS_RUN_LOG" \
    "$ACAS_RUN_RESULT_FILE" \
    "$ACAS_RUN_EXECUTABLE" \
    "$ACAS_DATA" \
    "$ACAS_RUN_ROWS" \
    "$ACAS_RUN_COLS" \
    "$ACAS_RUN_TIMEOUT" \
    <<'PY' &
import atexit
import fcntl
import os
import pty
import re
import select
import signal
import struct
import sys
import termios
import time

(plan_path, log_path, result_path, executable, workdir,
 rows_s, cols_s, timeout_s) = sys.argv[1:9]

ROWS = int(rows_s)
COLS = int(cols_s)
# The ONLY binary float in this whole script, and it is deliberately not an R-2
# concern: R-2 forbids binary floating point for ACCOUNTING values -- money and
# quantities -- and this is a timeout in seconds, used solely with
# time.monotonic() to bound a wait. It never touches a monetary or quantity
# field, never reaches the database, and never reaches an artifact: elapsed time
# is deliberately not printed anywhere, because a duration is exactly the kind of
# non-reproducible byte R-6 keeps out of a compared tree. No accounting
# arithmetic of any kind is performed in this file.
STEP_TIMEOUT = float(timeout_s)
# The reactive phase is given a larger budget than one prompt, because a posting
# run legitimately spends a long time between screens. It is still FINITE: an
# unbounded wait is the hang this driver exists to prevent.
REACTIVE_TIMEOUT = STEP_TIMEOUT * 8

# Strip the escape sequences ncurses interleaves with the text, plus the bare
# carriage returns it uses to rewind within a line.
ANSI = re.compile(
    rb'\x1b\[[0-9;?]*[a-zA-Z]'   # CSI ... final byte
    rb'|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)'  # OSC ... BEL or ST
    rb'|\x1b[()][A-Za-z0-9]'     # character set selection
    rb'|\x1b[=>NOM78]'           # keypad / charset / misc two-byte
    rb'|\x1b\([B0]'              # G0 designation
    rb'|[\x00\x07\x0e\x0f\r]'    # NUL, BEL, SO, SI, CR
)
WHITESPACE = re.compile(rb'[ \t\x0b\x0c]+')


def clean(raw):
    """Escape-stripped, whitespace-collapsed text for matching."""
    text = ANSI.sub(b' ', raw)
    text = text.replace(b'\x08', b'')      # backspace: the accept redraws
    text = WHITESPACE.sub(b' ', text)
    return text


def decode_send(spec):
    r"""Expand the plan's \r and \e escapes. Deliberately NOT a general
    unicode_escape decode, which would also transform sequences that are meant
    to reach the program literally.

    THE INPUT CONTRACT. This expands escapes ANYWHERE in `spec', which is
    correct only because a plan `send' field is TRUSTED PLAN TEXT. Untrusted
    scenario-supplied text must reach a send field through
    `acas_plan_escape_data', which doubles every backslash so that exactly one
    literal backslash is emitted here. That keeps the bytes typed at the compiled
    program identical to the bytes the migrated leg receives as argv, where there
    is no escape layer at all -- and a diff between two legs that were given
    different logical inputs would measure this function rather than the
    accounting (R-6). Do not add an escape to this table without checking every
    send site: a new one silently changes the meaning of data already flowing
    through."""
    out = []
    i = 0
    while i < len(spec):
        ch = spec[i]
        if ch == '\\' and i + 1 < len(spec):
            nxt = spec[i + 1]
            if nxt == 'r':
                out.append('\r')
                i += 2
                continue
            if nxt == 'n':
                out.append('\n')
                i += 2
                continue
            if nxt == 'e':
                out.append('\x1b')
                i += 2
                continue
            if nxt == 't':
                out.append('\t')
                i += 2
                continue
            if nxt == '\\':
                out.append('\\')
                i += 2
                continue
        out.append(ch)
        i += 1
    return ''.join(out).encode('utf-8', 'replace')


class Rule(object):
    __slots__ = ('phase', 'step', 'mode', 'pattern', 'send', 'limit',
                 'citation', 'fires')

    def __init__(self, phase, step, mode, pattern, send, limit, citation):
        self.phase = int(phase)
        self.step = step
        self.mode = mode
        self.pattern = pattern.encode('utf-8', 'replace')
        self.send = decode_send(send)
        try:
            self.limit = int(limit)
        except ValueError:
            self.limit = 1
        self.citation = citation
        self.fires = 0


rules = []
with open(plan_path, 'r', encoding='utf-8') as handle:
    for raw_line in handle:
        line = raw_line.rstrip('\n')
        if not line:
            continue
        fields = line.split('\t')
        if len(fields) != 7:
            sys.stderr.write(
                'driver: malformed plan record (%d fields, expected 7): %r\n'
                % (len(fields), line))
            sys.exit(15)
        rules.append(Rule(*fields))

forbidden = [r for r in rules if r.mode == 'forbid']
prefix = [r for r in rules if r.phase == 1]
reactive = [r for r in rules if r.phase == 2]
suffix = [r for r in rules if r.phase == 3]
terminals = [r for r in reactive if r.mode == 'terminal']

if not prefix:
    sys.stderr.write('driver: the plan has no strict prefix steps.\n')
    sys.exit(15)
if not terminals:
    sys.stderr.write('driver: the plan has no terminal rule for the reactive phase.\n')
    sys.exit(15)

# --- spawn -------------------------------------------------------------------
try:
    os.chdir(workdir)
except OSError as exc:
    sys.stderr.write('driver: cannot enter the data directory %s: %s\n'
                     % (workdir, exc))
    sys.exit(15)

pid, master = pty.fork()
if pid == 0:
    # Child. pty.fork has already made the slave its controlling terminal and
    # its fds 0, 1 and 2, so the heredoc this program was read from is gone.
    # NO ARGUMENTS: see zz020-Get-Program-Args.
    try:
        os.execv(executable, [os.path.basename(executable)])
    except OSError:
        os._exit(126)

# Parent. Set the REAL window size; the environment variables alone are what
# make a pipe pass the geometry gate, which is precisely the trap being avoided.
try:
    fcntl.ioctl(master, termios.TIOCSWINSZ,
                struct.pack('HHHH', ROWS, COLS, 0, 0))
except OSError as exc:
    sys.stderr.write('driver: could not set the pty window size: %s\n' % exc)

raw = bytearray()
matches = []          # (step, kind) in the order they were seen
offset = 0            # search position in the cleaned stream
child_status = None
failure = None        # (code, headline, detail...)
interrupted = None    # why the drive ended early, if it did

# --- the evidence writer, installed BEFORE the first byte is read ------------
# WRITING THE EVIDENCE, WITHOUT FOLLOWING A LINK  (CWE-59, CWE-367)
#
# acas_create_private_file already created both of these as regular files at mode
# 0600 and refused a symlink at each name -- but that was moments ago, before the
# whole posting cycle was driven. `open(path, 'a')` and `open(path, 'w')` both
# FOLLOW a symlink, and 'w' TRUNCATES what it finds, so anything able to replace
# either name during the drive would redirect this write and read the pty
# transcript of an entire accounting run. O_NOFOLLOW closes that window at the
# only moment it is actually open.
#
# O_CREAT is deliberately absent: both files MUST already exist, because the shell
# created them. If one has vanished, that is a fact worth reporting rather than
# papering over with a fresh file.
#
# WHY THIS IS A FUNCTION, REGISTERED EARLY, RATHER THAN A BLOCK AT THE END.
# Writing the evidence in straight-line code AFTER the read loop would write it only when
# the loop finished, and the loop does not finish on the one path where the transcript
# matters most: the outer wall-clock deadline sends this process SIGTERM, the default
# disposition kills it, and the run then reports
# "the driver exceeded its deadline" while leaving cobol.log with no trace of the
# child's output and cobol.result at zero bytes -- so the operator was told a
# screen never arrived and given nothing whatever to see WHICH screen the cycle
# had reached. Every byte needed to answer that is already in `raw'; only the
# write was missing.
#
# Three arrival paths are covered, and they are three because no one of them
# covers the others:
#   * atexit           -- normal return, sys.exit(), and an unhandled exception
#   * SIGTERM/INT/HUP  -- the outer deadline, a Ctrl-C, a lost terminal. None of
#                         these runs atexit on its own: the default disposition
#                         terminates the process outright
#   * an explicit call at the end of the happy path, so the ordinary run does not
#                         depend on interpreter shutdown ordering at all
# The function is idempotent through `_evidence_written', so the belt and the
# braces cannot double-append the transcript.
#
# It must not raise. It runs from a signal handler and from interpreter shutdown,
# and an exception raised there would replace a partial-evidence problem with a
# confusing traceback and a different exit status.
_NOFOLLOW = getattr(os, 'O_NOFOLLOW', 0)
_evidence_written = False


def _reopen(path, append):
    """Reopen a file the shell already created, refusing to follow a symlink."""
    flags = os.O_WRONLY | _NOFOLLOW | (os.O_APPEND if append else os.O_TRUNC)
    return os.fdopen(os.open(path, flags), 'w', encoding='utf-8')


def write_evidence():
    """Write the transcript and the outcome record. Idempotent; never raises."""
    global _evidence_written
    if _evidence_written:
        return
    _evidence_written = True
    try:
        transcript = clean(bytes(raw)).decode('utf-8', 'replace')
        with _reopen(log_path, True) as handle:
            handle.write('\n==> pty transcript (escape sequences stripped)\n')
            handle.write(transcript)
            if not transcript.endswith('\n'):
                handle.write('\n')
            if interrupted is not None:
                handle.write('==> TRANSCRIPT IS PARTIAL: %s\n' % interrupted)
            handle.write('==> end of transcript\n')
    except (OSError, ValueError) as exc:
        sys.stderr.write('driver: could not write the transcript to %s: %s\n'
                         % (log_path, exc))
    try:
        with _reopen(result_path, False) as handle:
            handle.write('child_exit\t%s\n'
                         % ('' if child_status is None else child_status))
            handle.write('raw_bytes\t%d\n' % len(raw))
            if interrupted is not None:
                handle.write('interrupted\t%s\n' % interrupted)
            for step, kind in matches:
                handle.write('matched\t%s\t%s\n' % (step, kind))
            if failure is not None:
                handle.write('failed\t%s\t%s\n' % (failure[0], failure[1]))
                for detail in failure[2:]:
                    handle.write('detail\t%s\n' % detail)
    except (OSError, ValueError) as exc:
        sys.stderr.write('driver: could not write the outcome record to %s: %s\n'
                         % (result_path, exc))


atexit.register(write_evidence)

_SIGNAL_NAMES = {
    signal.SIGTERM: 'SIGTERM',
    signal.SIGINT: 'SIGINT',
    signal.SIGHUP: 'SIGHUP',
}


def _on_signal(signum, _frame):
    """Preserve the evidence, stop the child, and leave.

    `os._exit' rather than `sys.exit': this runs in a signal handler, so the
    fewer interpreter mechanisms involved the better, and the evidence has
    already been written by the line above it. 128+signum is the conventional
    encoding a shell would report for a signalled child; the outer `timeout'
    substitutes its own 124 on the deadline path, which is what
    acas_assert_not_timed_out keys on.
    """
    global interrupted
    interrupted = 'the driver received %s -- the transcript below stops where the ' \
                  'signal arrived, and the run did NOT complete' \
                  % _SIGNAL_NAMES.get(signum, str(signum))
    # Best effort, and deliberately only ever this one pid: leaving the compiled
    # menu attached to a pty nobody is reading would hold the run lock's promise
    # of sequential execution open long after this process is gone.
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    write_evidence()
    os._exit(128 + signum)


for _signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    try:
        signal.signal(_signum, _on_signal)
    except (OSError, ValueError):
        # A disposition that cannot be installed is not worth failing the drive
        # for; the atexit path still covers the ordinary exits.
        sys.stderr.write('driver: could not install a handler for %s\n'
                         % _SIGNAL_NAMES.get(_signum, str(_signum)))


def reap(block=False):
    """Collect the child's status without ever touching another process."""
    global child_status
    if child_status is not None:
        return child_status
    try:
        waited, status = os.waitpid(pid, 0 if block else os.WNOHANG)
    except ChildProcessError:
        child_status = 0
        return child_status
    except OSError:
        return None
    if waited == pid:
        if os.WIFEXITED(status):
            child_status = os.WEXITSTATUS(status)
        elif os.WIFSIGNALED(status):
            child_status = 128 + os.WTERMSIG(status)
        else:
            child_status = status
    return child_status


def pump(budget):
    """Read whatever is available for up to `budget` seconds. Returns True if
    any new bytes arrived."""
    grew = False
    deadline = time.monotonic() + budget
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return grew
        try:
            ready, _, _ = select.select([master], [], [], min(remaining, 0.25))
        except (OSError, ValueError):
            return grew
        if not ready:
            if grew:
                # Give the screen a moment to settle, then stop: a partial
                # redraw must not be matched mid-write.
                return grew
            continue
        try:
            chunk = os.read(master, 65536)
        except OSError:
            # The slave closed: the program has exited.
            reap(block=True)
            return grew
        if not chunk:
            reap(block=True)
            return grew
        raw.extend(chunk)
        grew = True


def send(rule):
    if not rule.send:
        return True
    try:
        os.write(master, rule.send)
    except OSError as exc:
        sys.stderr.write('driver: could not write to the pty for step %s: %s\n'
                         % (rule.step, exc))
        return False
    return True


def check_forbidden(text):
    for rule in forbidden:
        if rule.pattern in text:
            return rule
    return None


def find_first(candidates, text, start):
    """The EARLIEST match at or after `start`, so the stream order of the
    screens is preserved rather than the order the rules happen to be listed."""
    best = None
    best_at = None
    for rule in candidates:
        at = text.find(rule.pattern, start)
        if at < 0:
            continue
        if best_at is None or at < best_at:
            best = rule
            best_at = at
    return best, best_at


def run_strict(steps, label):
    """Each step must appear, in order, within STEP_TIMEOUT."""
    global offset, failure
    for rule in steps:
        deadline = time.monotonic() + STEP_TIMEOUT
        while True:
            text = clean(bytes(raw))
            bad = check_forbidden(text)
            if bad is not None:
                failure = (11, 'the menu refused to run or diverted: %s'
                           % bad.pattern.decode('utf-8', 'replace'),
                           bad.citation)
                return False
            at = text.find(rule.pattern, offset)
            if at >= 0:
                offset = at + len(rule.pattern)
                matches.append((rule.step, label))
                if not send(rule):
                    failure = (15, 'could not send the keystrokes for step %s'
                               % rule.step, rule.citation)
                    return False
                break
            if reap() is not None:
                failure = (13, 'the menu exited before step %s was reached'
                           % rule.step, rule.citation)
                return False
            if time.monotonic() >= deadline:
                failure = (10, 'timed out waiting for step %s: expected the screen '
                           'to show %r' % (rule.step,
                                           rule.pattern.decode('utf-8', 'replace')),
                           rule.citation)
                return False
            pump(0.5)
    return True


def run_reactive():
    """Answer whatever appears, up to each rule's limit, until a terminal rule
    matches. This phase is intentionally NOT a fixed sequence: the menus branch,
    and which branch they take is the behaviour under observation."""
    global offset, failure
    deadline = time.monotonic() + REACTIVE_TIMEOUT
    while True:
        text = clean(bytes(raw))
        bad = check_forbidden(text)
        if bad is not None:
            failure = (11, 'the run was voided by %s'
                       % bad.pattern.decode('utf-8', 'replace'), bad.citation)
            return False

        rule, at = find_first(reactive, text, offset)
        if rule is not None:
            offset = at + len(rule.pattern)
            rule.fires += 1
            matches.append((rule.step, rule.mode))
            if rule.fires > rule.limit:
                # The program is asking the same thing over and over: an answer
                # it will not accept, or a paging loop with no end. This is the
                # spin, caught as a failure rather than left as a hang.
                failure = (12, 'step %s appeared %d times, more than its limit of %d: '
                           'the program is stuck on %r'
                           % (rule.step, rule.fires, rule.limit,
                              rule.pattern.decode('utf-8', 'replace')),
                           rule.citation)
                return False
            if not send(rule):
                failure = (15, 'could not send the keystrokes for step %s'
                           % rule.step, rule.citation)
                return False
            if rule.mode == 'terminal':
                return True
            deadline = time.monotonic() + REACTIVE_TIMEOUT
            continue

        if reap() is not None:
            # The menu exited on its own. For the IRS path that is the normal
            # end, because the suffix step may already have been consumed.
            return True
        if time.monotonic() >= deadline:
            failure = (14, 'the reactive phase never reached its terminal screen; '
                       'last matched step was %s'
                       % (matches[-1][0] if matches else '(none)'),
                       'expected one of: %s'
                       % ', '.join(r.pattern.decode('utf-8', 'replace')
                                   for r in terminals))
            return False
        pump(1.0)


ok = run_strict(prefix, 'prefix')
if ok:
    ok = run_reactive()
if ok and suffix:
    ok = run_strict(suffix, 'suffix')

# --- shut the child down cleanly --------------------------------------------
# Only ever the pid this driver itself forked. No pkill, no killall, no pattern
# match against the process table.
if reap() is None:
    settle = time.monotonic() + min(STEP_TIMEOUT, 15.0)
    while reap() is None and time.monotonic() < settle:
        pump(0.5)
if reap() is None:
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    settle = time.monotonic() + 5.0
    while reap() is None and time.monotonic() < settle:
        pump(0.25)
if reap() is None:
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    reap(block=True)

try:
    os.close(master)
except OSError:
    pass

# --- write the evidence ------------------------------------------------------
# The writer, its O_NOFOLLOW discipline and the three arrival paths that reach it
# are all defined next to the state they serialise, immediately after the pty was
# forked -- see the block headed "the evidence writer, installed BEFORE the first
# byte is read". Calling it explicitly here keeps the ordinary run independent of
# interpreter-shutdown ordering; the call is idempotent, so the atexit
# registration and the signal handlers remain the safety net they are meant to be
# rather than a second writer.
write_evidence()

if failure is not None:
    sys.stderr.write('driver: %s\n' % failure[1])
    for detail in failure[2:]:
        sys.stderr.write('driver:   %s\n' % detail)
    sys.exit(failure[0])
sys.exit(0)
PY
  ACAS_RUN_DRIVER_PID=$!
  wait "$ACAS_RUN_DRIVER_PID"
  rc=$?
  ACAS_RUN_DRIVER_PID=0
  set -e

  # A deadline expiry is separated from every driver-defined status BEFORE the
  # caller classifies it.
  local drive_elapsed=$(( SECONDS - drive_started ))
  if acas_is_timeout_status "$rc" "$drive_elapsed" "$ACAS_TIMEOUT_DRIVE"; then
    # The deadline is the ONE failure path on which the driver is killed rather
    # than returning, so it is also the one on which the operator most needs to be
    # told that the evidence survived. The driver's signal handler flushes both
    # artifacts before it goes; this reports them, and quotes the last screen it
    # managed to read, because "which screen did the cycle reach" is the only
    # question a drive timeout ever raises.
    acas_report_partial_drive_evidence
  fi
  acas_assert_not_timed_out "$rc" "$drive_elapsed" "$ACAS_TIMEOUT_DRIVE" \
    'ACAS_TIMEOUT_DRIVE' 'driving the compiled menu'

  return "$rc"
}

# Announce what the interrupted driver left behind. Read-only, and deliberately
# tolerant: it runs immediately before a die, so a missing or unreadable artifact
# must not replace the timeout diagnosis with a different failure.
acas_report_partial_drive_evidence() {
  local reason='' bytes='' matched=0 line kind rest
  if [[ -r "$ACAS_RUN_RESULT_FILE" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      kind="${line%%$'\t'*}"
      rest="${line#*$'\t'}"
      case "$kind" in
        interrupted) reason="$rest" ;;
        raw_bytes)   bytes="$rest" ;;
        matched)     matched=$(( matched + 1 )) ;;
      esac
    done <"$ACAS_RUN_RESULT_FILE"
  fi
  if [[ -n "$reason" ]]; then
    acas_log "the driver recorded why it stopped: $reason"
  fi
  if [[ -n "$bytes" ]]; then
    acas_log "partial evidence preserved: ${bytes} byte(s) read from the pty, ${matched} plan step(s) matched"
  else
    acas_warn "the driver left no outcome record at $ACAS_RUN_RESULT_FILE, so how far the cycle got cannot be established from this run"
    return 0
  fi
  acas_log "  transcript      = $ACAS_RUN_LOG"
  acas_log "  outcome record  = $ACAS_RUN_RESULT_FILE"
  # The last few non-blank lines OF THE TRANSCRIPT identify the screen the cycle
  # was sitting on. Bounded, because this is a pointer into the evidence and not a
  # second copy of it.
  #
  # THE TRANSCRIPT REGION IS EXTRACTED, NOT THE FILE'S TAIL. cobol.log is the
  # whole run log: this script's own lines go into it through acas_tee, and the
  # driver APPENDS the pty transcript to the same file. Reading the tail therefore
  # quotes whatever this function has just finished logging -- the excerpt ends up
  # echoing itself, and the one thing the operator wanted, the child's last screen,
  # is nowhere in it. So the region between the driver's own two markers is
  # extracted instead, and the LAST such region, because --no-rotate-fh-log and a
  # re-run against the same log can leave earlier ones above it.
  if [[ -r "$ACAS_RUN_LOG" ]]; then
    local -a tailed=()
    while IFS= read -r line; do
      [[ -n "${line// /}" ]] || continue
      tailed+=("$line")
    done < <(awk '
      /^==> pty transcript/ { collecting = 1; count = 0; delete buffer; next }
      /^==> end of transcript/ { collecting = 0; next }
      /^==> TRANSCRIPT IS PARTIAL/ { next }
      collecting { buffer[++count] = $0 }
      END { start = count - 5; if (start < 1) start = 1
            for (i = start; i <= count; i++) print buffer[i] }
    ' "$ACAS_RUN_LOG" 2>/dev/null || true)
    if (( ${#tailed[@]} > 0 )); then
      acas_log 'the last screen text the driver read before it was stopped:'
      for line in "${tailed[@]}"; do
        acas_log "  | $line"
      done
    else
      acas_note 'the transcript holds no screen text, so the child produced no output at all before it was stopped'
    fi
  fi
}


acas_report_drive_failure() {
  local rc="$1"
  local -a details=()
  local line kind rest

  # WHICH operation failed, when there is more than one. Without this a four-operation
  # scenario reported "the drive failed" and left the reader to work out from the
  # transcript which of the four menus it had been in.
  if (( ACAS_RUN_OP_INDEX >= 0 && ${#ACAS_RUN_OPS[@]} > 1 )); then
    details+=("failed during operation $(( ACAS_RUN_OP_INDEX + 1 )) of ${#ACAS_RUN_OPS[@]}: $ACAS_RUN_OPERATION ($ACAS_RUN_SUBSYSTEM menu)")
    if (( ACAS_RUN_OP_INDEX > 0 )); then
      details+=("        operations 1..$ACAS_RUN_OP_INDEX had already been driven, so the database holds their effects")
    fi
  fi

  # The driver already wrote its own diagnosis; replay it so the transcript and
  # the console agree.
  if [[ -f "$ACAS_RUN_RESULT_FILE" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      kind="${line%%$'\t'*}"
      rest="${line#*$'\t'}"
      case "$kind" in
        failed) details+=("driver: ${rest#*$'\t'}") ;;
        detail) details+=("        $rest") ;;
      esac
    done <"$ACAS_RUN_RESULT_FILE"
  fi

  case "$rc" in
    10)
      acas_die "$EX_DRIVE" \
        'a prompt this script was waiting for never appeared.' \
        "${details[@]}" \
        'The full transcript, with the escape sequences stripped, is at:' \
        "  $ACAS_RUN_LOG" \
        'A timeout here is the DESIGNED outcome for a screen that did not arrive.' \
        'Blind-feeding newlines instead would have selected some other menu option' \
        'and reported a clean pass, which is why every keystroke is matched first.'
      ;;
    11)
      acas_die "$EX_DRIVE" \
        'the menu refused to run, or diverted into an interactive setup program.' \
        "${details[@]}" \
        'The refusals this script watches for are SY010 and SY013 (the 24x80 gate at' \
        '[general/general.cbl:L374-L383]), SYS002 with SY102 and SY104 (the sys002' \
        'diversion at [general/general.cbl:L385-L396]), SY007 and SY009 (the argument' \
        'and environment checks at [copybooks/Proc-Get-Env-Set-Files.cob]), and' \
        '"Invalid Date" (the date reject loop at [general/gl000.cbl:L261-L265]).' \
        "transcript: $ACAS_RUN_LOG"
      ;;
    12)
      acas_die "$EX_DRIVE" \
        'the compiled program is stuck asking the same question.' \
        "${details[@]}" \
        'The commonest cause is an answer the program will not accept. irs030 end-of-job' \
        'question is the clearest example: despite its "[Y]" hint,' \
        '[irs/irs030.cbl:L1718-L1719] loops until the reply is exactly Y or N, so an' \
        'empty or mistyped answer spins forever. This is reported as a failure rather' \
        'than left to hang, because a hang looks like progress.' \
        "transcript: $ACAS_RUN_LOG"
      ;;
    13)
      acas_die "$EX_DRIVE" \
        'the menu exited before the run reached the posting step.' \
        "${details[@]}" \
        'Check the transcript for a refusal or an error screen. Note that' \
        '[general/general.cbl:L374-L383] ends its refusals with goback, so an early,' \
        'clean-looking exit is itself evidence.' \
        "transcript: $ACAS_RUN_LOG"
      ;;
    14)
      acas_die "$EX_DRIVE" \
        'the run never returned to the screen that ends the operation.' \
        "${details[@]}" \
        'Either the cycle is still working and the reactive budget was too small --' \
        'raise --timeout -- or a prompt appeared that the plan does not answer. The' \
        'transcript shows which screen was last recognised.' \
        "transcript: $ACAS_RUN_LOG"
      ;;
    15)
      acas_die "$EX_DRIVE" \
        'the pty driver failed internally.' \
        "${details[@]}" \
        "transcript: $ACAS_RUN_LOG"
      ;;
    126|127)
      acas_die "$EX_ORACLE" \
        "the menu executable could not be run: $ACAS_RUN_EXECUTABLE" \
        'Check that it is executable and that its shared libraries resolve --' \
        'LD_LIBRARY_PATH is set from [etc/ld.so.conf.d/gnucobol.conf], and libcob plus' \
        'libmysqlclient must both be findable. Run harness/build_oracle.sh.'
      ;;
    *)
      acas_die "$EX_DRIVE" \
        "the pty driver exited with status $rc." \
        "${details[@]}" \
        "transcript: $ACAS_RUN_LOG"
      ;;
  esac
}

acas_matched() {
  [[ -f "$ACAS_RUN_RESULT_FILE" ]] || return 1
  grep -q -F "$(printf 'matched\t%s\t' "$1")" "$ACAS_RUN_RESULT_FILE"
}

# These check that THE HARNESS did what it set out to do. They never judge the
# accounting.
acas_assert_after_run() {
  ACAS_RUN_CURRENT_STAGE='post-run assertions'
  acas_stage 'Post-run assertions'

  local failures=0
  ACAS_RUN_OBSERVED_STATUS=0

  # 1. The clock actually got pinned.
  local actual
  if actual="$(acas_system_column 'RUN-DAT')"; then
    if [[ "$actual" == "$ACAS_RUN_RUN_DATE" ]]; then
      acas_log "PASS  SYSTEM-REC.RUN-DAT = $actual, as pinned"
    else
      failures=$((failures + 1))
      acas_warn "FAIL  SYSTEM-REC.RUN-DAT is $actual but the scenario pinned $ACAS_RUN_RUN_DATE"
      if [[ "$actual" == '0' ]]; then
        acas_log '      A zero here is information, not noise: maps04 returns its output field'
        acas_log '      unchanged when it rejects a date [common/maps04.cbl:L146] and the caller'
        acas_log '      pre-zeroes it [copybooks/Proc-ACAS-Mapser-RDB.cob:L78], so zero means the'
        acas_log '      date was rejected. That is anomaly A-16, reproduced, not masked.'
      fi
    fi
  else
    failures=$((failures + 1))
    acas_warn 'FAIL  could not read SYSTEM-REC.RUN-DAT after the run'
  fi

  local irs_after
  if irs_after="$(acas_system_column 'IRS-INSTEAD')"; then
    # BOTH SIDES OF THE COMPARISON ARE STRIPPED, not just the one read back.
    # `IRS-INSTEAD' is `pic x' and its General-Ledger-only value is a single SPACE.
    # The column is CHAR(1) and MariaDB strips a trailing space from a CHAR on read,
    # so the value comes back EMPTY; stripping only that side and comparing it with
    # the scenario's unstripped `" "' reported "FAIL SYSTEM-REC.IRS-INSTEAD changed
    # from ' ' to ''" on every General Ledger run, for a switch nothing had touched.
    # Stage 6 already compares the SEEDED value this way -- it derives
    # seeded_irs_trimmed and compares trimmed against trimmed -- so this is the
    # post-run half of a rule the pre-run half was already following.
    irs_after="${irs_after// /}"
    local irs_pinned="${ACAS_RUN_IRS_INSTEAD// /}"
    if [[ "$irs_after" == "$irs_pinned" ]]; then
      acas_log "PASS  SYSTEM-REC.IRS-INSTEAD = '$irs_after', unchanged"
    else
      failures=$((failures + 1))
      acas_warn "FAIL  SYSTEM-REC.IRS-INSTEAD changed from '$ACAS_RUN_IRS_INSTEAD' to '$irs_after' during the run"
    fi
  else
    failures=$((failures + 1))
    acas_warn 'FAIL  could not read SYSTEM-REC.IRS-INSTEAD after the run'
  fi

  # 3. THE TWO ONE-SHOT POSTING LATCHES, OBSERVED AND EMITTED RATHER THAN JUDGED.
  # `S-Flag-P' [copybooks/wssystem.cob:L226] and `P-Flag-P'
  # [copybooks/wssystem.cob:L206] are the gates sl100 and pl100 clear once they have
  # posted -- `move zero to S-Flag-P.' [sales/sl100.cbl:L474] and `move zero to
  # P-Flag-P.' [purchase/pl100.cbl:L465] -- and the menu's key-1 `System-Rewrite'
  # [general/general.cbl:L656-L663] is their only writer to the store.
  #
  # WHY THIS IS EMITTED HERE RATHER THAN LEFT TO A TEST'S OWN QUERY. The dump of
  # `SYSTEM-REC' is a comparison artifact, written under the diff tree and read by the
  # diff stage; a test that wants ONE latch value as a number, attributable to ONE side
  # of ONE operation, would otherwise have to query the LIVE database
  # after the fact -- long after the protocol's own reset-and-reseed had replaced the
  # state this run left, and after any other scenario sharing the same database had
  # run. Reading it HERE, in the seconds after the operation, and printing it into
  # this run's captured stream makes it EVIDENCE OF THIS RUN: immutable, attributable
  # to one side, and impossible to confuse with a later run's state. It is an
  # OBSERVATION and deliberately not an assertion, because what a cleared latch means
  # is scenario-specific and belongs to the scenario's own test.
  local latch latch_value
  for latch in 'S-FLAG-P' 'P-FLAG-P'; do
    if latch_value="$(acas_system_column "$latch")"; then
      acas_log "ONE-SHOT-LATCH $latch = $latch_value"
    else
      failures=$((failures + 1))
      acas_warn "FAIL  could not read SYSTEM-REC.$latch after the run"
    fi
  done

  if [[ "$ACAS_RUN_SUBSYSTEM" == 'sales' ]]; then
    local table rc rows
    for table in "${ACAS_RUN_AUTOGEN_TABLES[@]}"; do
      rc=0
      acas_assert_table_name 'an autogen table name' "$table"
      acas_sql_scalar "select count(*) from $(acas_sql_quote_ident "$table");" || rc=$?
      if (( rc != 0 )); then
        acas_note "$table could not be counted; it is out of scope and may not exist in this schema"
        continue
      fi
      rows="$ACAS_SQL_OUT"
      if [[ "$rows" == '0' ]]; then
        acas_log "PASS  $table holds 0 rows -- sl830 was a no-op, as [sales/sl830.cbl:L270-L272] requires"
      else
        failures=$((failures + 1))
        acas_warn "FAIL  $table holds $rows rows; sl830 was NOT a no-op, so autogen is in use and the run is not comparable"
      fi
    done
  fi

  # 4. Report which branch each divergent gate took. This is OBSERVATION, and
  # it is deliberately not an assertion. (The latch report above is the same kind of
  # record: observed, emitted, and judged only by the scenario that cares.)
  case "$ACAS_RUN_OPERATION" in
    gl_post_cycle)
      local gl071_ran='no' gl072_ran='no' gate='did NOT fire'
      acas_matched 'gl071-sort' && gl071_ran='yes'
      acas_matched 'gl072-phase4' && gl072_ran='yes'
      if acas_matched 'gl060a-page' || acas_matched 'gl060a-exit'; then
        gate='FIRED'
        # The report is reached only through gl070's `a = 1` branch, whose next
        # statement moves 5 to ws-term-code [general/gl070.cbl:L287-L290].
        ACAS_RUN_OBSERVED_STATUS=5
      fi
      acas_log "GL gate (ws-term-code = 5) $gate  [general/general.cbl:L805-L815]"
      acas_log "  gl071 sort banner seen  : $gl071_ran"
      acas_log "  gl072 Phase 4 seen      : $gl072_ran"
      if [[ "$gate" == 'FIRED' ]]; then
        acas_log '  The gate fired, so gl071 and gl072 never ran and the database shows none of'
        acas_log '  their effects. The terminate code is raised on finding an open batch at'
        acas_log '  [general/gl070.cbl:L287-L290]. This is correct behaviour, not an error.'
      fi
      acas_summary_row 'GL gate' "$gate (gl071=$gl071_ran, gl072=$gl072_ran)"
      ;;
    sl_invoice_post)
      local sl055_ran='no' sl060_ran='no'
      acas_matched 'sl055-banner' && sl055_ran='yes'
      acas_matched 'sl060-banner' && sl060_ran='yes'
      acas_log "Sales gate (ws-term-code not = zero, twice)  [sales/sales.cbl:L756-L768]"
      acas_log "  sl055 banner seen : $sl055_ran"
      acas_log "  sl060 banner seen : $sl060_ran"
      acas_summary_row 'Sales gate' "sl055=$sl055_ran, sl060=$sl060_ran"
      ;;
    pl_order_post)
      local pl055_ran='no' pl060_ran='no'
      acas_matched 'pl055-banner' && pl055_ran='yes'
      acas_matched 'pl060-banner' && pl060_ran='yes'
      acas_log 'Purchase has NO abort gate: the pl830 call and the gate are BOTH commented out'
      acas_log '  at [purchase/purchase.cbl:L755-L758], so pl060 follows pl055 unconditionally.'
      acas_log "  pl055 banner seen : $pl055_ran"
      acas_log "  pl060 banner seen : $pl060_ran"
      acas_log '  No gate is added here, in any form. The divergence from Sales is the'
      acas_log '  specification (R-4).'
      acas_summary_row 'Purchase gate' "none by design (pl055=$pl055_ran, pl060=$pl060_ran)"
      ;;
    irs_post)
      local cleared='not asked'
      if acas_matched 'irs030-clear'; then
        cleared="answered $ACAS_RUN_IRS_CLEAR"
      fi
      acas_log "irs030 end-of-job clear question: $cleared  [irs/irs030.cbl:L1715-L1727]"
      if acas_matched 'irs030-no-postings'; then
        acas_warn 'irs030 reported IR031: no ledger posting file found, so the section aborted [irs/irs030.cbl:L1579-L1581]'
      fi
      local rc2=0
      acas_sql_scalar "select count(*) from $(acas_sql_quote_ident 'PSIRSPOST-REC');" || rc2=$?
      if (( rc2 == 0 )); then
        local transfer_rows="$ACAS_SQL_OUT"
        acas_log "PSIRSPOST-REC now holds $transfer_rows rows"
        if [[ "$ACAS_RUN_IRS_CLEAR" == 'Y' && "$cleared" != 'not asked' ]]; then
          local eligible_rc=0
          acas_sql_scalar \
            "select count(*) from $(acas_sql_quote_ident 'PSIRSPOST-REC') where $(acas_sql_quote_ident 'IRS-POST-KEY') < '9999999999';" \
            || eligible_rc=$?
          if (( eligible_rc != 0 )); then
            failures=$((failures + 1))
            acas_warn 'FAIL  the rows eligible for the frozen IRS transfer cleanup could not be counted'
          elif [[ "$ACAS_SQL_OUT" != '0' ]]; then
            failures=$((failures + 1))
            acas_warn "FAIL  the clear answer was Y but $ACAS_SQL_OUT PSIRSPOST-REC row(s) below key 9999999999 survived the frozen delete predicate [common/slpostingMT.cbl:L849-L891]"
          else
            acas_log "PASS  the frozen clear predicate removed every PSIRSPOST-REC row below key 9999999999; $transfer_rows higher-key row(s) remain by the compiled bridge's measured threshold [common/slpostingMT.cbl:L849-L891]"
          fi
        fi
      fi
      acas_summary_row 'irs030 clear postings' "$cleared"
      ;;
    gl_end_of_cycle)
      local proceeded='no'
      acas_matched 'gl080-gate' && proceeded='yes'
      acas_log "gl080 pre-run gate answered: $proceeded (scenario said $ACAS_RUN_GL080_PROCEED)  [general/gl080.cbl:L295-L302]"
      if acas_matched 'gl080-unproofed'; then
        acas_warn 'gl080 reported GL088: unproofed or unposted batches present, so it ended early [general/gl080.cbl:L308-L313]'
      fi
      acas_summary_row 'gl080 gate' "answered=$proceeded, scenario=$ACAS_RUN_GL080_PROCEED"
      ;;
    sl_cash_post|pl_payment_post)
      local confirmed='no'
      acas_matched 'sl100-confirm' && confirmed='yes'
      acas_matched 'pl100-confirm' && confirmed='yes'
      acas_log "payment posting confirmation answered: $confirmed ($ACAS_RUN_PAYMENT_CONFIRM)"
      acas_summary_row 'payment confirmation' "answered=$confirmed, value=$ACAS_RUN_PAYMENT_CONFIRM"
      ;;
  esac

  # Machine-readable behavioural evidence for tests/conftest.py. This is the
  # operation's observed term code, not this harness script's own exit status:
  # the script exits zero only after the drive and all self-checks complete.
  acas_log "$(printf 'OPERATION_STATUS\t%s\t%s' \
    "$ACAS_RUN_OPERATION" "$ACAS_RUN_OBSERVED_STATUS")"

  # 5. Row counts for the scenario's own tables.
  if (( ${#ACAS_RUN_TABLES[@]} > 0 )); then
    acas_log 'row counts for the affected tables (reported, not judged):'
    local table rc3
    for table in "${ACAS_RUN_TABLES[@]}"; do
      rc3=0
      acas_assert_table_name 'an affected table name' "$table"
      acas_sql_scalar "select count(*) from $(acas_sql_quote_ident "$table");" || rc3=$?
      if (( rc3 == 0 )); then
        acas_log "$(printf '  %-18s %s' "$table" "$ACAS_SQL_OUT")"
      else
        acas_log "$(printf '  %-18s (could not be counted)' "$table")"
      fi
    done
  fi

  # 6. The file-handler log, which cannot be switched off.
  local fh_log="$ACAS_DATA/fh-logger.txt"
  if [[ -f "$fh_log" ]]; then
    local fh_bytes
    fh_bytes="$(wc -c <"$fh_log" | tr -d ' ')"
    acas_log "fh-logger.txt = $fh_bytes bytes after the run"
    if (( fh_bytes > 104857600 )); then
      if (( ACAS_RUN_ROTATE_FH_LOG )); then
        acas_note "this run alone wrote $fh_bytes bytes of file-handler log; it will be rotated at the start of the next run"
      else
        acas_warn "fh-logger.txt has grown to $fh_bytes bytes and --no-rotate-fh-log was given, so the next run appends to it again"
      fi
    fi
  fi
  if [[ -n "$ACAS_RUN_FH_ROTATED" ]]; then
    acas_log "previous fh-logger.txt was preserved at $ACAS_RUN_FH_ROTATED"
  fi

  if (( failures > 0 )); then
    acas_die "$EX_ASSERT" \
      "$failures post-run assertion(s) failed." \
      'Each is listed above with its locator. None of them is an opinion about the' \
      'accounting: they check that the harness pinned what it said it pinned and that' \
      'the run is comparable at all.' \
      "transcript: $ACAS_RUN_LOG"
  fi
  acas_log 'all post-run assertions passed'
}

# acas_run_summarise_digest <label> <path>
# Add one `<label>  <digest>` row naming a file's SHA-256, or a row saying plainly
# why there is none. NEVER aborts and never alters the exit status: a digest is
# provenance for a verdict already reached, so failing to take one must not
# change the verdict.
#
# Only for artifacts that are FINAL when the row is added. A summary row is
# replayed through acas_log at the end of the report, and acas_log appends to the
# transcript -- so this helper cannot be used for the transcript itself. That one
# is emitted by acas_run_fingerprint_transcript, after the last append.
acas_run_summarise_digest() {
  local label="$1" path="$2" digest=''

  if [[ -z "$path" ]]; then
    acas_summary_row "$label" 'none -- no such artifact for this run'
    return 0
  fi
  if [[ ! -f "$path" ]]; then
    acas_summary_row "$label" 'none -- the artifact was not written'
    return 0
  fi
  digest="$(acas_diag_sha256 "$path")"
  if [[ -z "$digest" ]]; then
    acas_summary_row "$label" 'none -- no digest utility was available'
    return 0
  fi
  acas_summary_row "$label" "$digest"
}

# acas_run_fingerprint_transcript
# Print the pty transcript's own SHA-256 to the console.
#
# THIS CANNOT BE A SUMMARY ROW, and the reason is worth stating because it is the
# defect this replaces: summary rows are replayed through acas_log at the end of
# acas_run_report, acas_log tees into the transcript, and so a digest of the
# transcript taken alongside the other rows would be stale by exactly the bytes of
# the report that prints it. A file cannot contain its own digest.
#
# It is therefore emitted with a bare printf -- console only, no tee -- from the
# first point at which nothing further will be appended. On the success path,
# which is the only path that reaches the closing report, acas_on_exit returns
# before its own acas_tee, so the file really is final. The `%-22s' width matches
# acas_summary_row and the four-space indent matches acas_log, so the line lands
# in the same column as the rows above it.
#
# Like acas_run_summarise_digest it NEVER aborts: provenance for a verdict already
# reached must not be able to change that verdict.
acas_run_fingerprint_transcript() {
  local digest=''

  # The two "none" cases are reported apart, exactly as acas_run_summarise_digest
  # reports them, because they mean different things to a reader: an empty path is
  # a run that never had a transcript (--dry-run before the pty is opened), while a
  # named path that is absent means the create failed.
  if [[ -z "$ACAS_RUN_LOG" ]]; then
    printf '    %-22s %s\n' 'transcript sha256' 'none -- no such artifact for this run'
    return 0
  fi
  if [[ ! -f "$ACAS_RUN_LOG" ]]; then
    printf '    %-22s %s\n' 'transcript sha256' 'none -- the artifact was not written'
    return 0
  fi
  digest="$(acas_diag_sha256 "$ACAS_RUN_LOG")"
  if [[ -z "$digest" ]]; then
    printf '    %-22s %s\n' 'transcript sha256' 'none -- no digest utility was available'
    return 0
  fi
  printf '    %-22s %s\n' 'transcript sha256' "$digest"
}

# CLOSING REPORT
acas_run_report() {
  acas_stage 'Summary'

  acas_summary_row 'scenario' "$ACAS_RUN_SCENARIO"
  acas_summary_row 'operations' "$(acas_join_words "${ACAS_RUN_OPS[@]}")"
  local sindex srendered summary_ops=''
  for sindex in "${!ACAS_RUN_OPS[@]}"; do
    srendered="${ACAS_RUN_OP_STATUS[$sindex]-$ACAS_RUN_OP_NOT_RUN}"
    summary_ops+="${summary_ops:+, }${ACAS_RUN_OPS[$sindex]}=$srendered"
  done
  acas_summary_row 'observed statuses' "$summary_ops"
  acas_summary_row 'subsystem' "$ACAS_RUN_SUBSYSTEM (of the last operation driven)"
  if [[ "$ACAS_RUN_SUBSYSTEM" == 'irs' ]]; then
    acas_summary_row 'menu path' "option $ACAS_RUN_MENU_KEY then run option 66"
  else
    acas_summary_row 'menu path' "letter $ACAS_RUN_MENU_KEY -> $ACAS_RUN_PARAGRAPH"
  fi
  acas_summary_row 'pinned run date' "$ACAS_RUN_DATE_TEXT (form $ACAS_RUN_DATE_FORM, binary $ACAS_RUN_RUN_DATE)"
  case "$ACAS_RUN_IRS_INSTEAD" in
    '')  acas_summary_row 'IRS fan-out' '"" General Ledger only' ;;
    'Y') acas_summary_row 'IRS fan-out' '"Y" IRS instead of the GL' ;;
    'B') acas_summary_row 'IRS fan-out' '"B" IRS as well as the GL' ;;
  esac
  if (( ${#ACAS_RUN_TABLES[@]} > 0 )); then
    acas_summary_row 'affected tables' "$(acas_join_words "${ACAS_RUN_TABLES[@]}")"
  fi

  local prompts=0 line
  if [[ -f "$ACAS_RUN_RESULT_FILE" ]]; then
    prompts="$(grep -c $'^matched\t' "$ACAS_RUN_RESULT_FILE" || true)"
  fi
  acas_summary_row 'screens recognised' "$prompts"
  if (( ACAS_RUN_DRY_RUN )); then
    acas_summary_row 'mode' 'dry run -- no menu was spawned'
  else
    acas_summary_row 'transcript' "$ACAS_RUN_LOG"
  fi

  #  EVERY ARTIFACT THIS RUN CALLS EVIDENCE IS BOUND TO ITS BYTES
  #
  #  The rows above name a path, and a path is not evidence: a reader cannot tell
  #  whether the file they open is the file this run wrote, and
  #  docs/migration/scenario-diff-evidence.md cites these artifacts by name. A
  #  SHA-256 closes that gap. Rule R-6 is why that matters rather than being a
  #  nicety: the verdict of a scenario rests on the claim that one particular
  #  compiled run produced one particular state, and every link in that chain has
  #  to be checkable by someone who was not here when it ran.
  #
  #  WHICH ARTIFACT IS FINAL DECIDES WHERE ITS DIGEST GOES. The plan is written
  #  once, by acas_build_plan; the outcome record only while the cycle is being
  #  driven. Both are settled by now, so both are summary rows -- and because the
  #  rows are replayed through acas_log, the transcript ends up carrying their
  #  fingerprints as well as the console. The TRANSCRIPT itself is deliberately
  #  NOT a row: that same replay appends to it, so a digest taken here would be
  #  stale by exactly the bytes of this report. It is emitted after the last
  #  append instead, by acas_run_fingerprint_transcript.
  acas_run_summarise_digest 'plan sha256' "$ACAS_RUN_PLAN_FILE"
  acas_run_summarise_digest 'outcome sha256' "$ACAS_RUN_RESULT_FILE"

  for line in "${ACAS_RUN_SUMMARY[@]}"; do
    acas_log "$line"
  done

  if (( ${#ACAS_RUN_WARN_SUMMARY[@]} > 0 )); then
    acas_stage "Warnings (${#ACAS_RUN_WARN_SUMMARY[@]})"
    for line in "${ACAS_RUN_WARN_SUMMARY[@]}"; do
      acas_log "- $line"
    done
    acas_note 'a warning is a finding to record, not a failure; nothing above was repaired'
  fi

  # Last, because this is the first point at which nothing further is appended to
  # the transcript. Everything below writes to the console only.
  acas_run_fingerprint_transcript

  if (( ACAS_RUN_DRY_RUN )); then
    printf '\nDry run complete. Every precondition passed and the keystroke plan resolved.\n'
    printf 'Re-run without --dry-run to drive the compiled cycle.\n'
  else
    printf '\nThe compiled cycle ran for scenario %s.\n' "$ACAS_RUN_SCENARIO"

    # The next-step commands CARRY BOTH SELECTION-RELATED OPTIONS, because the two
    # do different jobs and each capture needs both. --all-in-scope is the BOUND,
    # all 22 in-scope tables. --scenario-file is the PROVENANCE: its sha256 becomes
    # scenario_file_sha256, one of the three fields harness/diff_states.py requires
    # PRESENT AND EQUAL on both sides before it compares a row, so a capture taken
    # without it is refused at the diff stage -- "the provenance field
    # 'scenario_file_sha256' is empty on both sides" -- and the whole cycle has to be
    # driven again. An operator copies these lines, so they must be the protocol.
    printf '\nNext steps -- each capture bounded by all 22 in-scope tables:\n'
    printf '  harness/dump_tables.py --scenario %s --side cobol --all-in-scope --scenario-file %s\n' \
      "$ACAS_RUN_SCENARIO" "$ACAS_RUN_SCENARIO_FILE"
    printf '  harness/normalize.py   --scenario %s --side cobol\n' "$ACAS_RUN_SCENARIO"
    printf '  harness/reset_db.sh %s\n' "$ACAS_RUN_SCENARIO_FILE"
    printf '  harness/run_python_scenario.sh --scenario %s\n' "$ACAS_RUN_SCENARIO"
    printf '  harness/dump_tables.py --scenario %s --side python --all-in-scope --scenario-file %s\n' \
      "$ACAS_RUN_SCENARIO" "$ACAS_RUN_SCENARIO_FILE"
    printf '  harness/normalize.py   --scenario %s --side python\n' "$ACAS_RUN_SCENARIO"
    printf '  harness/diff_states.py --scenario %s --all-in-scope --scenario-file %s\n' \
      "$ACAS_RUN_SCENARIO" "$ACAS_RUN_SCENARIO_FILE"
    printf 'The empty diff from that last command is the pass condition (AAP 0.8.5).\n'
  fi
}

acas_take_lock() {
  ACAS_RUN_LOCK="$ACAS_OUT/run-logs/.run_cobol_scenario.lock"

  acas_assert_outside_repo 'the sequential run lock' "$ACAS_RUN_LOCK"

  mkdir -p "${ACAS_RUN_LOCK%/*}" 2>/dev/null || true

  local holder=''
  if [[ -e "$ACAS_RUN_LOCK" ]]; then
    holder="$(cat -- "$ACAS_RUN_LOCK" 2>/dev/null || true)"
    if [[ "$holder" =~ ^[0-9]+$ ]] && kill -0 "$holder" 2>/dev/null; then
      acas_die "$EX_PRECONDITION" \
        "another harness/run_cobol_scenario.sh (pid $holder) is already driving the oracle." \
        "lock file: $ACAS_RUN_LOCK" \
        'Execution must be strictly sequential (R-3): the database is shared, and two' \
        'scenarios running at once would each invalidate the other. Wait for it to' \
        'finish.'
    fi
    acas_warn "reclaiming a stale run lock left by pid ${holder:-<unreadable>} at $ACAS_RUN_LOCK"
    rm -f -- "$ACAS_RUN_LOCK" 2>/dev/null || true
  fi

  if ! (set -C; printf '%s\n' "$$" >"$ACAS_RUN_LOCK") 2>/dev/null; then
    acas_die "$EX_PRECONDITION" \
      "could not take the run lock $ACAS_RUN_LOCK." \
      'Either another run took it in the last instant, or the ACAS_OUT directory' \
      'is not writable.'
  fi
  ACAS_RUN_LOCK_HELD=1
}

acas_main() {
  acas_parse_args "$@"

  # FIRST, before anything can spawn an external command: resolve and freeze
  # every deadline.
  acas_resolve_deadlines

  acas_resolve_scenario
  acas_assert_environment
  acas_open_log

  # As soon as $ACAS_DATA is known good and the transcript is open, and while a
  # refusal is still free.
  acas_assert_fh_log_capacity

  acas_take_lock
  acas_resolve_pinned_values
  acas_assert_oracle
  acas_assert_database
  acas_assert_data_dir

  # LAST before the first drive, so the counts it records are the state the compiled
  # cycle is actually handed, with nothing between them.
  acas_record_seed_fingerprint

  # ONE PASS PER DECLARED OPERATION, IN ORDER
  #
  # Each iteration selects the operation, builds ITS keystroke plan for ITS menu,
  # drives it, runs the post-run assertions, and records the operation's OWN
  # observed disposition in ACAS_RUN_OP_STATUS at this index. The loop is strictly
  # sequential -- no concurrency anywhere, matching the single-threaded COBOL (R-3)
  # -- and it stops at the first WRAPPER fault, because a wrapper fault means the
  # harness cannot vouch for what it just did. A BEHAVIOURAL disposition is not a
  # wrapper fault and does not stop the loop: the term-code-5 abort chain
  # [general/gl070.cbl:L287-L290] is correct compiled behaviour, and the operations
  # after it must still be driven so that the state the Python side is compared
  # against is the state the whole declared sequence produces.
  local index op rc=0
  for index in "${!ACAS_RUN_OPS[@]}"; do
    op="${ACAS_RUN_OPS[$index]}"
    ACAS_RUN_OP_INDEX="$index"
    acas_select_operation "$op"

    if (( ${#ACAS_RUN_OPS[@]} > 1 )); then
      acas_stage "$(printf 'Operation %d of %d: %s (%s menu)' \
        "$(( index + 1 ))" "${#ACAS_RUN_OPS[@]}" "$op" "$ACAS_RUN_SUBSYSTEM")"
    fi

    acas_build_plan

    rc=0
    acas_drive || rc=$?
    if (( rc != 0 )); then
      # Terminal: acas_report_drive_failure dies.
      acas_report_drive_failure "$rc"
    fi

    if (( ACAS_RUN_DRY_RUN )); then
      # A dry run prints the plan for every operation and drives none of them, so
      # there is nothing to assert and no disposition to record.
      continue
    fi

    acas_assert_after_run
    ACAS_RUN_OP_STATUS["$index"]="$ACAS_RUN_OBSERVED_STATUS"
  done
  ACAS_RUN_OP_INDEX=-1

  # Published BEFORE the report, and before the EXIT trap writes the run-status
  # record, so that both carry the same per-operation dispositions.
  acas_publish_operation_status


  # IMMEDIATELY AFTER THE DRIVE AND ITS PER-OPERATION ASSERTIONS, and before the
  # report: the pre-run and post-run records together are the only evidence that this
  # run CHANGED anything, and a table diff cannot supply it - two runs that did
  # nothing at all agree perfectly. `acas_assert_after_run` is NOT repeated here: the
  # multi-operation loop above takes it once per operation, which is where the
  # disposition of each belongs.
  acas_record_post_fingerprint

  acas_run_report

  # Explicitly the success code, reached only after every operation was driven and
  # every assertion passed. It is WRAPPER HEALTH and nothing else: what each
  # operation actually did is in the operation-status artifact.
  exit "$EX_OK"
}

acas_main "$@"
