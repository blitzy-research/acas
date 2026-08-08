#!/usr/bin/env bash
# harness/reset_db.sh -- stage 5 of the parity protocol: drop the schema,
# re-apply the frozen mysql/ACASDB.sql VERBATIM, and re-seed through
# harness/seed.sh. Run `--help' for the options, the gates and the exit codes.
#
#     seed -> run(COBOL) -> dump -> normalise -> RE-SEED -> run(Python) -> dump
#     -> normalise -> verify published -> diff
#
# Both cycles must start from byte-for-byte the same seeded state, because the
# acceptance condition is an EMPTY diff between the two dumps. An inexact reset
# would leave the Python side starting from a different premise, and then a
# non-empty diff would prove nothing.
#
# This script emits ZERO DDL of its own (R-3). It does not need any: the frozen
# dump already carries 33 `DROP TABLE IF EXISTS` statements, one before each of
# its 33 `CREATE TABLE` statements [mysql/ACASDB.sql:L28], so re-applying the
# frozen file IS the drop-and-recreate. Every statement this script issues
# itself is a read-only SELECT: the readiness probe, the autocommit assertion,
# the privilege assertion and the post-apply verification.
#
# It is DESTRUCTIVE, so it refuses to run until its gates are satisfied -- a
# consent token, an acknowledged target, and a target that is not the frozen
# checkout. Those gates are the reason the script is long; do not weaken them.

set -Eeuo pipefail

# Word splitting on newlines and tabs only, so a path containing a space can
# never be split apart. Every expansion below is quoted regardless.
IFS=$'\n\t'

# An unmatched glob expands to nothing rather than to the pattern text.
shopt -s nullglob

# Nothing this script writes is group- or world-readable.
umask 077

# Exit codes. CHOSEN NOT TO COLLIDE WITH ANY CODE THIS SCRIPT MIGHT PROPAGATE.
readonly EX_OK=0
readonly EX_USAGE=80          # bad command line
readonly EX_PRECONDITION=81   # environment, output directory or seed.sh assertion
readonly EX_DATABASE=82       # MariaDB unreachable, or credentials rejected
readonly EX_AUTOCOMMIT=83     # autocommit is not ON -- see acas_assert_autocommit. A
                              # reset is RUNTIME APPLICATION ACCESS and not seeding, so
                              # it requires the mode harness/Dockerfile.mariadb
                              # declares; the Agent Action Plan scopes autocommit-OFF
                              # to the seeding window, which harness/seed.sh owns.
                              # (The inverted wording this comment used to carry was
                              # the whole of QA issue 9 in this file: the code died
                              # when autocommit was ON while the text said the
                              # opposite. The --help exit-code table already agreed
                              # with the code; only this line did not.)
readonly EX_PRIVILEGE=84      # the account cannot perform the drop and re-apply
readonly EX_FROZEN=85         # mysql/ACASDB.sql has been MODIFIED -- see §invariants
readonly EX_APPLY=86          # the client rejected part of the frozen schema
readonly EX_VERIFY=87         # the post-apply state is not what the schema defines
readonly EX_CONCURRENT=88     # another reset holds the sequential lock
readonly EX_TIMEOUT=89        # a client or the delegated seed exceeded its deadline
readonly EX_TARGET=90         # the target is not a proven harness-owned disposable database
readonly EX_FIXTURE=91        # the re-seed did not reuse the scenario's staged fixture
#  EVIDENCE UNAVAILABLE (finding SEC-02, moved here by finding M-06). Distinct from
#  every difference status on purpose: a difference is a finding ABOUT the migration,
#  whereas this means nothing was compared at all because the oracle cannot arbitrate.
#  Conflating the two is how a missing specification gets reported as a passing one --
#  or as a failing one, which is no better. It is checked BEFORE this script drops a
#  single table, so a refusal leaves the database untouched.
readonly EX_EVIDENCE_UNAVAILABLE=77

# This script streams 33 `DROP TABLE IF EXISTS` + 33 `CREATE TABLE` pairs at
# whatever server the environment names.
readonly ACAS_RESET_REQUIRED_SCHEMA='ACASDB'
# THE DISPOSABILITY MARKER IS A SERVER SETTING, NOT A SCHEMA (finding F-43).
# It used to be `acas_harness_disposable.disposability_marker', a table created by
# harness/Dockerfile.mariadb with CREATE DATABASE, CREATE TABLE and INSERT -- and
# this script REQUIRED it, which made that DDL load-bearing. Rule R-3 admits no
# added DDL of any kind, so the proof is now `report_host', a MariaDB variable
# settable only from a configuration file inside the image. Same property, no
# schema: a stock MariaDB leaves it EMPTY, so the marker can only be seen on a
# server started from the harness image, and this server is nobody's replica so the
# variable has no other effect.
#
# MEASURED (rule R-6): `version_comment' was the first choice and mariadbd 10.11.7
# REFUSES IT in an option file -- "unknown variable 'version_comment=...'" -- and
# will not start, so that marker could never be read at all. `report_host' was
# accepted on the same probe. The image now proves its own option file startable at
# BUILD time, so this variable and that file cannot drift apart again.
readonly ACAS_RESET_DISPOSABLE_MARKER='ACAS-harness-disposable-oracle'
readonly ACAS_RESET_DISPOSABLE_VARIABLE='report_host'
readonly -a ACAS_RESET_CANONICAL_HOSTS=(mariadb 127.0.0.1 localhost ::1)

# The scenario-fixture marker harness/seed.sh writes when it stages a
# scenario's declared seed files.
readonly ACAS_RESET_FIXTURE_MARKER='.acas-scenario-fixture'

readonly ACAS_TIMEOUT_MAX=86400
ACAS_TIMEOUT_GRACE="${ACAS_TIMEOUT_GRACE-}"         # TERM-to-KILL grace period
ACAS_TIMEOUT_CLIENT="${ACAS_TIMEOUT_CLIENT-}"        # one MariaDB client invocation
ACAS_TIMEOUT_APPLY="${ACAS_TIMEOUT_APPLY-}"         # streaming the frozen schema
ACAS_TIMEOUT_SEED="${ACAS_TIMEOUT_SEED-}"          # the delegated harness/seed.sh
ACAS_TIMEOUT_RESOLVED=''      # out-parameter of acas_timeout_seconds
declare -a ACAS_DEADLINE_ARGV=()   # populated by acas_deadline_prefix


# The one file this script applies, relative to the read-only checkout.
readonly ACAS_RESET_SCHEMA_RELPATH='mysql/ACASDB.sql'

# Byte-for-byte digest of `mysql/ACASDB.sql` as committed: 1459 lines, 51008
# bytes.
readonly ACAS_RESET_SCHEMA_SHA256='094e588226f650672c3781d1737d7bf8be30be048ce6a788df81800a19326ed0'

readonly ACAS_RESET_EXPECT_TABLES=33

# The 22 IN-SCOPE tables, each with the column count and single-column primary
# key the frozen schema declares.
readonly -a ACAS_RESET_INSCOPE=(
  'ANALYSIS-REC:4:PA-CODE'
  'GLBATCH-REC:21:BATCH-KEY'
  'GLLEDGER-REC:11:LEDGER-KEY'
  'GLPOSTING-REC:14:POST-RRN'
  'IRSDFLT-REC:4:DEF-REC-KEY'
  'IRSFINAL-REC:3:IRS-FINAL-ACC-REC-KEY'
  'IRSNL-REC:15:KEY-1'
  'IRSPOSTING-REC:13:KEY-4'
  'PSIRSPOST-REC:10:IRS-POST-KEY'
  'PUINV-LINES-REC:14:IL-LINE-KEY'
  'PUINVOICE-REC:30:PINVOICE-KEY'
  'PUITM5-REC:29:OI5-KEY'
  'PULEDGER-REC:29:PURCH-KEY'
  'SAINV-LINES-REC:14:IL-LINE-KEY'
  'SAINVOICE-REC:31:SINVOICE-KEY'
  'SAITM3-REC:28:OI3-KEY'
  'SALEDGER-REC:37:SALES-KEY'
  'SYSDEFLT-REC:4:DEF-REC-KEY'
  'SYSFINAL-REC:2:FINAL-ACC-REC-KEY'
  'SYSTEM-REC:169:SYSTEM-REC-KEY'
  'SYSTOT-REC:21:LEDGER-TOTALS-REC-KEY'
  'VALUEANAL-REC:10:VA-CODE'
)

# The 11 OUT-OF-SCOPE tables, recreated by the apply and never compared.
readonly -a ACAS_RESET_OUT_OF_SCOPE=(
  'DELIVERY-REC'
  'PLPAY-REC'
  'PLPAY-RECrg01'
  'PUAUTOGEN-LINES-REC'
  'PUAUTOGEN-REC'
  'PUDELINV-REC'
  'SAAUTOGEN-LINES-REC'
  'SAAUTOGEN-REC'
  'SADELINV-REC'
  'STOCK-REC'
  'STOCKAUDIT-REC'
)

# The frozen collation every one of the 33 tables declares. Asserted after the
# apply.
readonly ACAS_RESET_COLLATION='utf8mb3_general_ci'

# The only tables in the whole schema carrying a NON-PRIMARY index, both out of
# scope.
readonly -a ACAS_RESET_SECONDARY_INDEX_ALLOWED=(
  'STOCK-REC'
  'PLPAY-RECrg01'
)

# The six privileges the frozen file's own statements require of the applying
# account.
readonly -a ACAS_RESET_REQUIRED_PRIVILEGES=(
  'DROP'
  'CREATE'
  'LOCK TABLES'
  'ALTER'
  'INSERT'
  'SELECT'
)

# The script this one delegates re-seeding to, resolved beside this file so the
# reset works from any working directory -- the `gnucobol` service runs with
# working_dir /build [harness/docker-compose.yml].
readonly ACAS_RESET_SEED_SCRIPT='seed.sh'

# The environment contract, identical in shape to the one harness/seed.sh and
# harness/build_oracle.sh assert, so a container configured for one stage is
# configured for all three.
readonly -a ACAS_RESET_REQUIRED_ENV_NONEMPTY=(
  ACAS_REPO ACAS_OUT
  ACAS_DB_HOST ACAS_DB_PORT ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD
)
readonly -a ACAS_RESET_REQUIRED_ENV_DECLARED=(
  ACAS_DB_SOCKET
)

# Variables this script does not use itself but harness/seed.sh requires, so a
# named cause instead of at the delegation boundary.
readonly -a ACAS_RESET_SEED_ENV_NONEMPTY=(
  ACAS_BUILD ACAS_DATA ACAS_LEDGERS ACAS_BIN
)

# =============================================================================
# THE DESTRUCTIVE-TARGET POLICY  (CWE-20 missing validation of a destructive
# operation, CWE-89 SQL construction from an unvalidated identifier)
#
# WHAT THIS SCRIPT DOES, stated plainly: it streams a file containing 33
# `DROP TABLE IF EXISTS` statements at whatever server the environment names,
# using whatever account the environment names, and then re-seeds. Every
# accounting table in the target schema is destroyed. There is no undo, and by
# design there is no transaction around it -- autocommit is asserted ON, because
# the frozen COBOL never reaches a COMMIT, and a DDL statement commits implicitly
# regardless.
#
# WHAT WAS MISSING. Three things, and together they are the whole finding:
#
#   1. NO CONSENT. `ACAS_DB_*` is an ambient environment contract, set once in
#      a shell or a Compose file and inherited by every later command. Nothing
#      distinguished "reset my disposable harness database" from "run this in
#      the wrong terminal". A destructive default is the wrong default.
#   2. NO TARGET IDENTITY CHECK. Any host and any schema name were accepted.
#      Point the environment at a real server and the script does exactly what
#      it is told.
#   3. NO PRIVILEGE SEPARATION. The applying account fell back SILENTLY to the
#      application account:
#          ACAS_RESET_DB_USER="${ACAS_DB_ADMIN_USER:-$ACAS_DB_USER}"
#      which the MariaDB vendor entrypoint grants ALL on the schema. That
#      fallback meant the account the migrated Python cycle authenticates with
#      day to day was also the account that dropped every table.
#      GATE 1 removed the fallback, which fixed WHICH ACCOUNT THIS SCRIPT USES.
#      It did not, and could not, fix WHAT THE APPLICATION ACCOUNT MAY DO: the
#      vendor grant stood on its own, so a leak of the runtime credential
#      remained a destructive capability no matter what this script chose. That
#      second half is closed elsewhere, by the least-privilege init script in
#      harness/Dockerfile.mariadb, which narrows the account to SELECT, INSERT,
#      UPDATE and DELETE at container start and refuses to finish initialisation
#      if the narrowing did not take. Both halves are needed; neither alone is
#      sufficient, and recording the distinction is the point of this note.
#
# THE THREE GATES, all asserted in acas_assert_environment BEFORE the first
# connection is opened, and re-asserted immediately before the apply:
#
#   GATE 1  A DISTINCT ADMIN ACCOUNT. ACAS_DB_ADMIN_USER must be set and must
#           differ from ACAS_DB_USER. No fallback. The application account can
#           then be granted only what the Python cycle needs.
#   GATE 2  EXPLICIT, TARGET-SCOPED CONSENT. ACAS_RESET_CONSENT (or --consent=)
#           must equal EXACTLY
#               DESTROY <schema>@<host>:<port>
#           for the target actually resolved. A boolean flag would not do:
#           `--yes` inherited from a shell history is worth nothing, whereas a
#           token naming the schema, host and port cannot be aimed at a
#           different database by accident. Comparison is exact and
#           case-sensitive.
#   GATE 3  A DISPOSABLE TARGET. The schema must appear in the allow-list
#           below, and the host must be a disposable host. Both lists are
#           extendable by environment, because a deployment may legitimately
#           name its throwaway database something else -- but extending them
#           is an explicit, reviewable act.
#
# WHY NONE OF THIS CHANGES BEHAVIOUR THAT IS COMPARED (R-3, R-4, R-6). Every
# gate either lets the run proceed exactly as before or ABORTS it before the
# first connection. There is no third outcome: no gate rewrites a statement,
# alters the applied file, changes the seed, or touches the loader exit-code
# contract. This script still emits ZERO DDL of its own -- the 33 drops live
# inside the frozen mysql/ACASDB.sql and are applied verbatim.
# =============================================================================

readonly -a ACAS_RESET_DEFAULT_ALLOWED_SCHEMAS=(
  'ACASDB'
)

# GATE 3b -- hosts a disposable database is expected to live on.
readonly -a ACAS_RESET_DEFAULT_DISPOSABLE_HOSTS=(
  'localhost'
  'localhost.localdomain'
  '127.0.0.1'
  '::1'
  'mariadb'
  'acas-mariadb'
)

# GATE 2 -- the consent token's fixed prefix. The remainder is derived from the
# resolved target, so the whole token is `DESTROY <schema>@<host>:<port>`.
readonly ACAS_RESET_CONSENT_PREFIX='DESTROY'

# SEC-02 -- the shape a schema name must have before it may be interpolated
# into SQL at all. Deliberately narrower than MySQL permits.
readonly ACAS_RESET_SCHEMA_NAME_PATTERN='^[A-Za-z_][A-Za-z0-9_$]*$'

# Mutable state. Declared up front because `set -u` makes an unset reference
# fatal.
ACAS_RESET_SCHEMA=''             # absolute path to the frozen schema
ACAS_RESET_SCHEMA_ONLY=0         # --schema-only: apply the schema, skip the seed
ACAS_RESET_DATA_DIR=''           # --data-dir, forwarded verbatim to seed.sh
ACAS_RESET_SEED_DIR=''           # --seed-dir, forwarded verbatim to seed.sh. It says
                                 # WHERE the scenario's declared flat files live, never
                                 # WHICH are required -- see harness/seed.sh --help.
                                 # DEFAULTED when a scenario is named and the option is
                                 # not -- see acas_resolve_fixture_root.
ACAS_RESET_DRY_RUN=0             # --dry-run
ACAS_RESET_SCENARIO=''           # optional positional scenario file
ACAS_RESET_HARNESS=''            # this script's own directory, resolved in acas_main
#  Set by --accept-transformed-oracle. 0 refuses a transformed oracle outright; 1
#  proceeds for DIAGNOSIS, and the run is then not a parity claim.
ACAS_RESET_ACCEPT_TRANSFORMED_ORACLE=0
#  Raised once a transformed oracle has been accepted, so every later report can say so
#  regardless of what any comparison finds.
ACAS_RESET_ORACLE_IS_DIAGNOSTIC=0
ACAS_RESET_LOG=''                # $ACAS_OUT/reset/reset.log
ACAS_RESET_LOCK=''               # $ACAS_OUT/.reset_db.lock, held for the run
ACAS_RESET_LOCK_HELD=0           # 1 once this process owns the lock
ACAS_RESET_APPLIED=0             # 1 once the frozen schema has been applied
ACAS_RESET_VERIFIED=0            # 1 once every post-apply assertion passed
ACAS_RESET_SEED_RC=''            # seed.sh's exit status, or '' if not run
ACAS_RESET_STAGE='startup'       # the stage a trap reports against
ACAS_RESET_SEED=''               # absolute path to harness/seed.sh
declare -a ACAS_RESET_SEED_ARGV=()   # out-parameter of acas_compose_seed_argv

# acas_compose_seed_argv -- the ONE place the delegated seed command is built.
#
# WHY IT IS A FUNCTION AND NOT TWO COPIES. The command is needed twice, once to RUN and
# once to PRINT in the dry-run plan, and while it was written out twice the two drifted:
# --seed-dir was forwarded by the runner and omitted by the plan, so the plan quietly
# described a different command from the one that would execute. A plan that misreports
# the command is worse than no plan, and it is the same class of defect as a --help text
# that disagrees with behaviour. Composing it once makes the two AGREE BY CONSTRUCTION
# rather than by remembering to edit both.
acas_compose_seed_argv() {
  ACAS_RESET_SEED_ARGV=("$ACAS_RESET_SEED")
  if [[ -n "$ACAS_RESET_DATA_DIR" ]]; then
    ACAS_RESET_SEED_ARGV+=("--data-dir" "$ACAS_RESET_DATA_DIR")
  fi
  # It has to be reachable from HERE and not only from seed.sh directly, because the
  # ten-stage protocol reaches the seed through this script -- stages 1 and 5 are both
  # `reset_db.sh <scenario>' -- so a fixture that could only be
  # named on seed.sh's own command line would be unusable from the protocol it was built
  # for.
  if [[ -n "$ACAS_RESET_SEED_DIR" ]]; then
    ACAS_RESET_SEED_ARGV+=("--seed-dir" "$ACAS_RESET_SEED_DIR")
  fi
  if [[ -n "$ACAS_RESET_SCENARIO" ]]; then
    ACAS_RESET_SEED_ARGV+=("$ACAS_RESET_SCENARIO")
  fi
}
ACAS_RESET_DB_USER=''            # account used for the drop and re-apply
ACAS_RESET_DB_PASSWORD=''        # its password -- never printed, never in argv
ACAS_RESET_CONSENT_ARG=''        # --consent=, overrides ACAS_RESET_CONSENT
ACAS_RESET_CONSENT_EXPECTED=''   # the token the target requires, once resolved
ACAS_RESET_TARGET_AUTHORISED=0   # 1 once all three destructive gates passed
ACAS_RESET_SCHEMA_LITERAL=''     # the schema as a safe SQL literal, incl. quotes
ACAS_RESET_ACKNOWLEDGE=''        # --acknowledge-destructive: the named target
ACAS_RESET_ACK_USED=0            # 1 once an acknowledgement has been honoured
ACAS_RESET_FIXTURE_DIGEST=''     # sha256 of the staged fixture marker (F-22)
# The parity attempt this reset belongs to, so the two reset stages of ONE attempt can
# be required to have seeded identical bytes while a LATER attempt is free to seed
# something else (F-22, F-37). Empty for a hand invocation, which is not part of an
# attempt and therefore binds nothing.
ACAS_RESET_RUN_ID="${ACAS_PARITY_RUN_ID:-}"
declare -a ACAS_RESET_GATE_PROBLEMS=()  # destructive-gate failures, reported together
declare -a ACAS_RESET_TLS_VARIANTS=()   # permitted client transports, most secure first
ACAS_SQL_OUT=''                  # last successful query result
ACAS_SQL_DIAG=''                 # last client diagnostic, for error messages
ACAS_SQL_CLIENT=''               # resolved client binary: mariadb or mysql
declare -a ACAS_SQL_ARGV=()      # bounded client argv, published by acas_build_sql_argv
ACAS_SQL_TLS_FLAG=''             # resolved TLS flag: '' or --skip-ssl
declare -a ACAS_RESET_SUMMARY=()      # the closing checklist
declare -a ACAS_RESET_WARN_SUMMARY=() # non-fatal findings, replayed at the end

# Stage banners are numbered so the log reads as the deterministic staged
# orchestration the plan prescribes (R-6): explicit, ordered, individually
# reported, individually asserted.

# Append to the run log if it is open yet. Silent before acas_open_log runs, so
# early usage errors still print without needing a log.
acas_tee() {
  if [[ -n "$ACAS_RESET_LOG" ]]; then
    printf '%s\n' "$*" >>"$ACAS_RESET_LOG" 2>/dev/null || true
  fi
}

# Announce a stage AND record it, so a trap can name the stage that failed.
acas_stage() {
  ACAS_RESET_STAGE="$1"
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

acas_ok() {
  printf '    ok: %s\n' "$*"
  acas_tee "    ok: $*"
}

acas_warn() {
  printf 'WARNING: %s\n' "$*" >&2
  acas_tee "WARNING: $*"
  ACAS_RESET_WARN_SUMMARY+=("$*")
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

# acas_file_sha256 <path>
#   The digest of one file, printed bare, for a value this script PUBLISHES rather
#   than merely reports: the staged fixture marker's digest is what binds both
#   cycles to the same seeded bytes (finding F-22). Unlike acas_diag_sha256 this one
#   FAILS when it cannot produce a digest, because a missing digest here would
#   silently remove the binding rather than degrade a diagnostic.
# ⭐ EVERY EVIDENCE LEAF IS PUBLISHED BY RENAME, NEVER BY REDIRECTION (finding F-26)
#
# acas_create_private_file above closes the CREATE race: it refuses a symlink and
# creates under `set -C', which is O_EXCL. It does not close the WRITE race, and the
# write is where the evidence actually appears. Every artifact this script publishes
# -- the run-status record, the per-operation dispositions, the seed fingerprint --
# used to be written with a plain `>' redirection into a path that had been checked
# for a symlink EARLIER. Between the check and the write, the name can be replaced;
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


acas_file_sha256() {
  local path="$1" digest=''

  if command -v sha256sum >/dev/null 2>&1; then
    digest="$(sha256sum -- "$path")" || return 1
    printf '%s' "${digest%% *}"
    return 0
  fi
  command -v python3 >/dev/null 2>&1 || return 1
  python3 - "$path" <<'DIGEST'
import hashlib
import sys

digest = hashlib.sha256()
with open(sys.argv[1], 'rb') as handle:
    for block in iter(lambda: handle.read(1 << 16), b''):
        digest.update(block)
sys.stdout.write(digest.hexdigest())
DIGEST
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
# in ACAS_TIMEOUT_RESOLVED rather than on stdout.
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
      'A zero budget means "block forever". There is deliberately no way to' \
      'disable a deadline in this script.'
  fi
  if (( value > ACAS_TIMEOUT_MAX )); then
    acas_die "$EX_USAGE" \
      "$name must not exceed $ACAS_TIMEOUT_MAX seconds; got '$value'."
  fi
  ACAS_TIMEOUT_RESOLVED="$value"
}

acas_resolve_deadlines() {
  acas_have timeout || acas_die "$EX_PRECONDITION" \
    'timeout is not on the PATH.' \
    'It is part of coreutils and every external process this script spawns' \
    'runs under it. harness/Dockerfile.gnucobol provides it.'

  acas_timeout_seconds ACAS_TIMEOUT_GRACE 15
  ACAS_TIMEOUT_GRACE="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_CLIENT 30
  ACAS_TIMEOUT_CLIENT="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_APPLY 300
  ACAS_TIMEOUT_APPLY="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_SEED 3600
  ACAS_TIMEOUT_SEED="$ACAS_TIMEOUT_RESOLVED"
  readonly ACAS_TIMEOUT_GRACE ACAS_TIMEOUT_CLIENT ACAS_TIMEOUT_APPLY ACAS_TIMEOUT_SEED

  local budget
  for budget in "$ACAS_TIMEOUT_GRACE" "$ACAS_TIMEOUT_CLIENT" "$ACAS_TIMEOUT_APPLY" \
                "$ACAS_TIMEOUT_SEED"; do
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

# acas_assert_not_timed_out <rc> <elapsed> <budget> <budget-var> <label>.
acas_assert_not_timed_out() {
  local rc="$1" elapsed="$2" budget="$3" budget_var="$4" label="$5"
  if ! acas_is_timeout_status "$rc" "$elapsed" "$budget"; then
    return 0
  fi
  acas_die "$EX_TIMEOUT" \
    "$label exceeded its ${budget}s deadline and was terminated." \
    "Raise $budget_var if this host is slower than the budget assumes." \
    "The child was sent TERM at the deadline and KILL ${ACAS_TIMEOUT_GRACE}s later."
}

# acas_assert_outside_repo <label> <path> Canonical, not textual, and in BOTH
# directions.
acas_assert_outside_repo() {
  local label="$1" path="$2"
  local repo_real target probe

  repo_real="$(readlink -f -- "$ACAS_REPO" 2>/dev/null || printf '%s' "$ACAS_REPO")"

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

# Every statement in this script is built by string composition -- the MariaDB
# CLI has no bind parameters -- so the two values that reach SQL from the
# environment are gated here rather than trusted at each of the eleven sites.
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

# ONE implementation, two published names. acas_sql_quote is the name most call
# sites use; acas_sql_quote_literal, declared below with the SQL-COMPOSITION
# block that explains it, is the implementation.
acas_sql_quote() {
  acas_sql_quote_literal "${1-}"
}

# acas_assert_table_name <label> <value> The table-name counterpart of
# acas_assert_sql_identifier.
acas_assert_table_name() {
  local label="$1" value="$2"
  if [[ ! "$value" =~ ^[A-Za-z0-9_-]{1,64}$ ]]; then
    acas_die "$EX_PRECONDITION" \
      "$label is not a plain SQL table name: '$value'." \
      'It is composed into SQL text as a quoted identifier, so it is restricted' \
      'to letters, digits, underscore and hyphen -- the alphabet the frozen' \
      "$ACAS_RESET_SCHEMA_RELPATH actually uses. A backtick in particular is" \
      'refused rather than escaped.'
  fi
}

# acas_sql_quote_ident <value> Emits a backquoted SQL identifier, doubling any
# embedded backtick, and -- like acas_sql_quote -- emits the delimiters itself
# so that no call site is left writing its own pair around an unescaped value.
acas_sql_quote_ident() {
  local value="$1"
  # The delimiter is held in a variable rather than written into the format
  # string.
  local bq='`'
  printf '%s%s%s' "$bq" "${value//"$bq"/"$bq$bq"}" "$bq"
}

# Split a `<table>:<columns>:<primary key>` in-scope entry into three globals.
# Parameter expansion rather than `read -r -d`, so a field is never re-split.
ACAS_T_TABLE=''
ACAS_T_COLUMNS=''
ACAS_T_PK=''
acas_split_table_entry() {
  local entry="$1"
  ACAS_T_TABLE="${entry%%:*}"
  entry="${entry#*:}"
  ACAS_T_COLUMNS="${entry%%:*}"
  ACAS_T_PK="${entry#*:}"
}

acas_check() {
  local verdict="$1"
  shift
  ACAS_RESET_SUMMARY+=("$(printf '%-6s %s' "$verdict" "$(acas_join_words "$@")")")
}

# The 22 in-scope table names, for membership tests.
acas_inscope_table_names() {
  local entry
  for entry in "${ACAS_RESET_INSCOPE[@]}"; do
    acas_split_table_entry "$entry"
    printf '%s\n' "$ACAS_T_TABLE"
  done
}

# Render a list for a diagnostic, or the word "none" when it is empty, so a
# message never reads "missing :" with nothing after the colon.
acas_list_or_none() {
  if (( $# == 0 )); then
    printf 'none'
    return 0
  fi
  acas_join_words "$@"
}

# ---------------------------------------------------------------------------
#  THE TARGET, DESCRIBED WITHOUT NAMING IT (finding F-39)
#
#  This script's transcripts are retained evidence: they are read by operators,
#  attached to reports and, on the Python side, replayed to a container log. A line
#  reading `acas@mariadb:3306/ACASDB` puts the deployment's topology and the database
#  ACCOUNT NAME into all of that, which is half of a credential and a map of the
#  network for anybody who reads it (CWE-532). Nothing downstream needs the names:
#  what a reader needs is WHICH KIND of target this was, and whether two runs used
#  the SAME one.
#
#  So the transcript carries a CATEGORY and a stable FINGERPRINT. The category is
#  derived from the host alone and is the same vocabulary
#  `acas_posting/dal/connection.py` uses. The fingerprint is the first twelve hex
#  digits of a SHA-256 over `host:port/schema` - never the password and never the
#  account name, neither of which is in the digest at all - so two runs against one
#  target print the same value and a run against a different target prints a
#  different one, while the value itself discloses no name. The full values remain in the environment, where the tools that
#  need them read them.
# ---------------------------------------------------------------------------
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

  # The ACCOUNT IS DELIBERATELY NOT IN THE DIGEST. Two reasons, both load-bearing.
  # The digest identifies the TARGET, so harness/seed.sh (which connects as the
  # application account) and harness/reset_db.sh (which connects as the admin
  # account) print the SAME fingerprint for the same database -- which is exactly
  # what makes two transcripts comparable. And an account name that is never an
  # input can never be recovered from the output, not even by a reader who can
  # enumerate candidate names.
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

# Membership test over elements passed by value, so the arrays stay readonly.
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

# This script builds twelve read-only information_schema queries by
# interpolating $ACAS_DB_NAME into SQL text. Every one of them went in raw:
#
#     where TABLE_SCHEMA = '${ACAS_DB_NAME}'      <-- the defect, as it was
#
# A schema name containing an apostrophe closes the literal, and because the
# client is invoked with --execute and the frozen dump is streamed on stdin,
# the remainder is executed as SQL by whichever account is connected -- and
# until GATE 1 that could be the application account, which the vendor grant
# gave ALL on the schema. Today GATE 1 forces an administrative account here,
# so the blast radius is bounded by that account rather than by the runtime
# one, and the runtime one no longer holds DDL in any case. `--force` is
# deliberately absent, which limits the radius further but does not remove it,
# which is why the two controls below are applied regardless.
#
# TWO CONTROLS, applied together:
#
#   * SHAPE. acas_assert_schema_name refuses anything that is not a plain
#     ASCII identifier, once, at precondition time. A name that cannot contain
#     a quote cannot break out of one.
#   * ESCAPING. acas_sql_quote_literal doubles backslashes and apostrophes and
#     returns the value WITH its surrounding quotes, so a call site cannot
#     accidentally omit them. Belt and braces: the shape check already makes
#     escaping a no-op for every accepted name, and that is the point -- if the
#     shape check is ever loosened, the call sites stay safe.
#
# The composed SQL is otherwise IDENTICAL, character for character, to what the
# twelve queries sent before, so every verification result is unchanged.
# -----------------------------------------------------------------------------

acas_sql_quote_literal() {
  local value="${1-}"
  value="${value//\\/\\\\}"
  value="${value//\'/\'\'}"
  printf "'%s'" "$value"
}

# Identifier quoting goes through acas_sql_quote_ident, declared above with
# acas_assert_table_name.

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

# shellcheck disable=SC2317  # reached only through the EXIT trap installed below,
# Release the lock this process created, and only that one. which shellcheck
# cannot follow; the body is live and is exercised by the concurrency
# validation case.
acas_release_lock() {
  if (( ACAS_RESET_LOCK_HELD )) && [[ -n "$ACAS_RESET_LOCK" ]]; then
    rm -f -- "$ACAS_RESET_LOCK" 2>/dev/null || true
    ACAS_RESET_LOCK_HELD=0
  fi
}

# shellcheck disable=SC2317  # reached only through the ERR trap installed below,
# which shellcheck cannot follow; the body is live and is exercised by the
# negative validation cases.
acas_on_err() {
  local status="$1" line="$2" cmd="$3"
  printf '\nFATAL: unexpected failure at %s line %s (status %s).\n' \
    "${BASH_SOURCE[0]}" "$line" "$status" >&2
  printf '       failing stage  : %s\n' "$ACAS_RESET_STAGE" >&2
  printf '       failing command: %s\n' "$cmd" >&2
  acas_tee "FATAL: unexpected failure at line $line (status $status) during stage '$ACAS_RESET_STAGE': $cmd"
}
trap 'acas_on_err "$?" "$LINENO" "$BASH_COMMAND"' ERR

# shellcheck disable=SC2317  # reached only through the EXIT trap installed below.
acas_on_exit() {
  local status="$1"
  acas_release_lock
  if (( status == 0 )); then
    return 0
  fi
  printf '\nharness/reset_db.sh exiting with status %s during stage: %s\n' \
    "$status" "$ACAS_RESET_STAGE" >&2
  if (( ACAS_RESET_APPLIED )); then
    # The seed "did not complete" covers both never having run and having run
    # and failed.
    if (( ! ACAS_RESET_SCHEMA_ONLY )) && [[ "$ACAS_RESET_SEED_RC" != '0' ]]; then
      printf 'The frozen schema WAS applied but the re-seed did not complete, so the\n' >&2
      printf 'database now holds the %s empty tables and NO seed data. That is a valid\n' \
        "$ACAS_RESET_EXPECT_TABLES" >&2
      printf 'schema and an invalid premise for a state diff: re-run this script, and do\n' >&2
      printf 'not compare dumps taken from this state.\n' >&2
    else
      printf 'The frozen schema WAS applied. Re-run this script before taking any diff.\n' >&2
    fi
  else
    printf 'The frozen schema was NOT applied, so the database is untouched by this run.\n' >&2
  fi
  acas_tee "harness/reset_db.sh exiting with status $status during stage '$ACAS_RESET_STAGE'"
}
trap 'acas_on_exit "$?"' EXIT

acas_usage() {
  cat <<'USAGE'
harness/reset_db.sh -- drop, re-apply the frozen ACASDB schema verbatim, re-seed.

Stages 1 and 5 of the TEN-stage parity protocol. The canonical stage list is
harness/normalize.py; print it with `harness/normalize.py --print-stages'.

    seed -> run(COBOL) -> dump -> normalise -> RE-SEED -> run(Python) -> dump
    -> normalise -> verify published -> diff

Both cycles must start from byte-for-byte the same seeded state, or the diff they
produce means nothing. This script restores that state:

  1. Applies $ACAS_REPO/mysql/ACASDB.sql VERBATIM to $ACAS_DB_NAME. The frozen
     file carries its own 33 `DROP TABLE IF EXISTS` statements
     [mysql/ACASDB.sql:L28], so re-applying it IS the drop-and-recreate and this
     script emits no DDL of its own (R-3). It is streamed unfiltered: no sed, no
     awk, no iconv, no local copy, no --default-character-set override, so the
     charset caveat at [mysql/ACASDB.sql:L9-L11] is preserved, not "fixed" (R-4).
  2. Verifies the result -- 33 tables, all empty, the frozen collation, the
     declared shape of all 22 in-scope tables, no nullable column, no floating
     point column, no secondary index where the dump relies on there being none,
     autocommit still on, and durability in a fresh session.
  3. Re-seeds by delegating to harness/seed.sh, which drives the maintainer's own
     compiled load programs and reproduces the contract of
     [common/masterLD.sh:L44-L115].

It never drops the database itself: `DROP DATABASE` / `CREATE DATABASE` appear
nowhere in the frozen file and would destroy the grants Compose established. The
database is created once by the MariaDB entrypoint; this resets its CONTENTS.

Usage:
  harness/reset_db.sh [options] [<scenario.yaml>]

Arguments:
  <scenario.yaml>     Optional. Forwarded VERBATIM to harness/seed.sh, so the
                      canonical invocation documented in
                      harness/docker-compose.yml -- `harness/reset_db.sh "$S"`
                      -- works as written.
                      BINDING when given: harness/seed.sh stages the scenario's
                      declared seed_files into a scenario-owned fixture and seeds
                      from exactly those, and after the re-seed this script
                      ASSERTS the fixture marker. So a scenario named here is
                      provably the one the database was re-seeded from. Naming a
                      scenario whose seed files are missing FAILS (91) rather
                      than silently re-seeding from something else: stage 5
                      exists so the Python cycle starts from byte-for-byte the
                      state the COBOL cycle started from, and a re-seed drawn
                      from a different file set makes every downstream table
                      difference unattributable.

THIS SCRIPT IS DESTRUCTIVE, so three gates must be satisfied before it opens a
single connection. All three are asserted up front; --dry-run REPORTS them
instead of enforcing them, and is the way to be told the exact consent token a
target needs.

  GATE 1  A DISTINCT ADMIN ACCOUNT. ACAS_DB_ADMIN_USER and
          ACAS_DB_ADMIN_PASSWORD must name an account that is NOT ACAS_DB_USER.
          There is no fallback: the application account the migrated cycle
          authenticates with must not also carry DROP on every table.
  GATE 2  TARGET-SCOPED CONSENT. ACAS_RESET_CONSENT, or --consent=, must equal
          exactly `DESTROY <schema>@<host>:<port>` for the resolved target. A
          bare --yes would authorise nothing in particular; this cannot be
          aimed at another database by accident.
  GATE 3  A DISPOSABLE TARGET. The schema must be in the allow-list (ACASDB by
          default, extend with ACAS_DB_ALLOWED_SCHEMAS) and the host must be a
          disposable host (the loopback forms plus `mariadb` and
          `acas-mariadb`, extend with ACAS_DB_DISPOSABLE_HOSTS).

The connection must also be protected unless it is local: set ACAS_DB_TLS_CA to
the PEM bundle the server certificate chains to, or declare an isolated network
with ACAS_DB_ALLOW_PLAINTEXT=1. A loopback host or a unix socket may always use
plaintext. Nothing is downgraded silently.

Options:
  --consent TOKEN     Satisfy GATE 2 without setting ACAS_RESET_CONSENT.
                      `--consent=TOKEN` is the same option. Run --dry-run to be
                      told the exact token this target requires.
  --schema-only       Apply the frozen schema and STOP: 33 empty tables, no seed
                      data. Useful for a bare database, but note that the full
                      stage-5 contract is schema PLUS seed -- a dump taken after
                      --schema-only is NOT comparable with one taken after the
                      COBOL cycle.
  --data-dir PATH     Directory holding the Cobol flat files, forwarded verbatim
                      to harness/seed.sh. Default $ACAS_DATA.
  --seed-dir PATH     Where the scenario's declared flat files live, forwarded
                      verbatim to harness/seed.sh. It says WHERE, never WHICH: the
                      scenario's own seed_files list remains the sole authority on
                      what is required.
                      DEFAULTED, and rarely needed: with a scenario named and this
                      option omitted, it resolves to the CANONICAL FIXTURE ROOT --
                      $ACAS_FIXTURES if set, otherwise $ACAS_DATA/fixtures -- plus the
                      scenario name, which is exactly where harness/seed.sh --build-fixtures
                      writes. Pass it only for a fixture built somewhere else.
                      A default is necessary rather than convenient: a scenario's own
                      seed_dir resolves relative to the scenario file, which sits in
                      the READ-ONLY checkout, so a built fixture can never live there,
                      and an omission used to fail only AFTER all 33 tables had been
                      dropped and re-applied.
                      Reachable from here and not only from seed.sh because the
                      ten-stage protocol seeds through this script -- stages 1
                      and 5 are both reset_db.sh <scenario>.
  --dry-run           Print the plan -- the file to be applied, its asserted
                      invariants, the verification queries and the seed command
                      -- and exit without executing anything or touching the
                      database.
  --acknowledge-destructive USER@HOST:PORT/SCHEMA
                      Proceed even though a disposability proof does not hold.
                      REQUIRES the exact target it authorises, and is matched
                      against this invocation's own target, so it cannot be left
                      in an environment and later authorise a different database.
                      A run that uses it says so in its report.
  -h, --help          Print this help and exit 0.

Disposability -- what this script demands before it destroys anything:
  It drops and re-applies all 33 tables, so it first requires POSITIVE PROOF that
  the target is a harness-owned throwaway. Four independent facts, the first two
  checked before any network contact at all:
    1. ACAS_DB_NAME is exactly ACASDB -- the only schema the frozen dump defines.
    2. ACAS_DB_HOST is one this harness provisions: mariadb, 127.0.0.1,
       localhost or ::1.
    3. The server reports report_host beginning ACAS-harness-disposable-oracle,
       which harness/Dockerfile.mariadb declares in a configuration file inside
       the image and which therefore exists ONLY on a server started from an image
       this harness built. It is a SERVER SETTING and not a schema: no CREATE
       DATABASE, CREATE TABLE or INSERT is issued anywhere for it (rule R-3, and
       finding F-43, which is why the earlier marker TABLE is gone). Proof by
       PRESENCE of a marker, not by absence of production data: an empty staging
       database and an empty production database are indistinguishable, so a
       heuristic would fail OPEN. This fails CLOSED.
    4. ACASDB holds no table outside the frozen 33 -- an extra table means the
       schema is shared with something that is about to lose the schema around it.
  Any of these failing REFUSES the run (90) unless --acknowledge-destructive (or
  ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE) names this exact target.

Finite deadlines -- no external command may hang indefinitely:
  ACAS_TIMEOUT_CLIENT=N   Seconds for one database client invocation (default 30).
  ACAS_TIMEOUT_APPLY=N    Seconds to stream the 33 DROP/CREATE pairs (default 300).
  ACAS_TIMEOUT_SEED=N     Seconds for the whole delegated re-seed (default 3600).
  ACAS_TIMEOUT_GRACE=N    Seconds between TERM and KILL (default 15).
  Each must be a positive integer of at most 86400. On expiry the run fails 89
  and names both the stage and the variable that bounded it, so an
  under-provisioned budget is distinguishable from a genuinely stuck server.

Required environment (harness/docker-compose.yml supplies all of it):
  ACAS_REPO           read-only checkout            (mounted ../:/repo:ro)
  ACAS_OUT            writable output area          (volume /out)
  ACAS_DB_HOST        MariaDB host
  ACAS_DB_PORT        MariaDB port
  ACAS_DB_NAME        target schema -- passed EXPLICITLY to the client, because
                      the frozen dump contains no `USE` statement at all
  ACAS_DB_USER        MariaDB user      (max 12 chars, [copybooks/wsfnctn.cob:L56-L62])
  ACAS_DB_PASSWORD    MariaDB password  (max 12 chars; never echoed, never logged)
  ACAS_DB_SOCKET      may be EMPTY (TCP), but must be declared

Also required for the re-seed, and asserted up front unless --schema-only:
  ACAS_BUILD          build tree from harness/build_oracle.sh (volume /build)
  ACAS_DATA           writable ledger/data area     (volume /data)
  ACAS_LEDGERS        the path every loader prefixes onto every file name
  ACAS_BIN            must be non-blank for the same reason

Also required -- GATE 1, privilege separation, with NO fallback:
  ACAS_DB_ADMIN_USER      The account that performs the drop and re-apply. It
  ACAS_DB_ADMIN_PASSWORD  MUST be set and MUST differ from ACAS_DB_USER; naming
                          the application account is refused. There is
                          deliberately no default -- an earlier revision fell
                          back to ACAS_DB_USER, and this text described that
                          fallback as making an override "normally unnecessary",
                          which was wrong twice over: GATE 1 has no fallback to
                          be optional about, and the application account no
                          longer holds the privileges the apply needs. It is
                          narrowed to SELECT, INSERT, UPDATE and DELETE by the
                          least-privilege init script in
                          harness/Dockerfile.mariadb, so it cannot DROP or CREATE
                          at all. Compose supplies `root` here, which holds them
                          globally. The 12-character limit does NOT apply: this
                          is a harness credential and never enters the COBOL
                          `RDB-Data` block.
  ACAS_DB_WAIT_TIMEOUT=N  Seconds to wait for MariaDB (default 180).
  ACAS_DB_AUTH_GRACE=N    Seconds to tolerate "Access denied" before failing
                          fast, capped at ACAS_DB_WAIT_TIMEOUT (default 15).

Exit codes:
  0        clean reset and clean re-seed
  80       usage           81  precondition
  82       database        83  autocommit is not on (the runtime mode)
  84       privilege      85  mysql/ACASDB.sql has been MODIFIED
  86       schema apply   87  post-apply verification
  88       another reset holds the sequential lock
  89       an external command exceeded its finite deadline
  90       the target could not be proved a harness-owned disposable database
  91       the re-seed did not use the named scenario's staged fixture
  anything else  harness/seed.sh's own status, propagated verbatim: 70..75 for
                 its own failures, or a load program's 128 / 64 / 16
                 [common/masterLD.sh:L37-L39].

This script emits no DDL, writes nothing under $ACAS_REPO -- every write target is
canonicalised and refused if it resolves into the checkout, in either direction --
never sets autocommit, never passes --force to the client, composes every schema
value into SQL through a validating quoter rather than by interpolation, bounds
every external command with a finite deadline, and runs strictly sequentially.
USAGE
}


acas_parse_args() {
  while (( $# > 0 )); do
    case "$1" in
      -h|--help)
        acas_usage
        exit "$EX_OK"
        ;;
      --schema-only)
        ACAS_RESET_SCHEMA_ONLY=1
        shift
        ;;
      --data-dir)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--data-dir requires a path.'
        ACAS_RESET_DATA_DIR="$2"
        # Rejected rather than treated as "not given", and for the same reason
        # the --data-dir=* form below rejects it.
        [[ -n "$ACAS_RESET_DATA_DIR" ]] || acas_die "$EX_USAGE" \
          '--data-dir was given an empty path.' \
          'If the default is wanted, omit the flag; harness/seed.sh then uses' \
          'the ACAS_DATA volume instead.'
        shift 2
        ;;
      --data-dir=*)
        ACAS_RESET_DATA_DIR="${1#*=}"
        [[ -n "$ACAS_RESET_DATA_DIR" ]] || acas_die "$EX_USAGE" \
          '--data-dir was given an empty path.' \
          'If the default is wanted, omit the flag; harness/seed.sh then uses' \
          'the ACAS_DATA volume instead.'
        shift
        ;;
      --accept-transformed-oracle)
        #  ⭐ ACKNOWLEDGE A TRANSFORMED ORACLE FOR DIAGNOSIS ONLY. Without it a build
        #  whose attestation says `oracle-source-is-frozen no' is refused outright with
        #  EX_EVIDENCE_UNAVAILABLE, because rule R-6 makes the COMPILED PROGRAM the
        #  specification and rule R-4 requires its defects reproduced rather than
        #  repaired -- so an empty diff against a repaired oracle would claim the
        #  migrated cycle matches a PATCHED system.
        ACAS_RESET_ACCEPT_TRANSFORMED_ORACLE=1
        shift ;;
      --seed-dir)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--seed-dir requires a path.'
        ACAS_RESET_SEED_DIR="$2"
        [[ -n "$ACAS_RESET_SEED_DIR" ]] || acas_die "$EX_USAGE" \
          '--seed-dir was given an empty path.' \
          'If the scenario'"'"'s own seed_dir is wanted, omit the flag.'
        shift 2
        ;;
      --seed-dir=*)
        ACAS_RESET_SEED_DIR="${1#*=}"
        [[ -n "$ACAS_RESET_SEED_DIR" ]] || acas_die "$EX_USAGE" \
          '--seed-dir was given an empty path.' \
          'If the scenario'"'"'s own seed_dir is wanted, omit the flag.'
        shift
        ;;
      --consent)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" \
          '--consent requires the target-scoped token.' \
          'Run --dry-run to be told the exact token this target needs.'
        ACAS_RESET_CONSENT_ARG="$2"
        shift 2
        ;;
      --consent=*)
        # Deliberately accepted even when EMPTY here, so that
        # acas_authorise_destructive_target reports the one message that names
        # the exact token required, rather than a usage error that does not.
        ACAS_RESET_CONSENT_ARG="${1#*=}"
        shift
        ;;
      --dry-run)
        ACAS_RESET_DRY_RUN=1
        shift
        ;;
      --acknowledge-destructive)
        # Deliberately REQUIRES a value rather than acting as a bare switch.
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" \
          '--acknowledge-destructive requires the exact target it authorises.' \
          "Expected form: user@host:port/schema" \
          "For this invocation that is: $(acas_reset_target_label)"
        ACAS_RESET_ACKNOWLEDGE="$2"
        [[ -n "$ACAS_RESET_ACKNOWLEDGE" ]] || acas_die "$EX_USAGE" \
          '--acknowledge-destructive was given an empty target.' \
          'An empty acknowledgement cannot name a target, so it authorises' \
          'nothing; omit the flag instead.'
        shift 2
        ;;
      --acknowledge-destructive=*)
        ACAS_RESET_ACKNOWLEDGE="${1#*=}"
        [[ -n "$ACAS_RESET_ACKNOWLEDGE" ]] || acas_die "$EX_USAGE" \
          '--acknowledge-destructive was given an empty target.' \
          'An empty acknowledgement cannot name a target, so it authorises' \
          'nothing; omit the flag instead.'
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
        # The optional scenario positional, forwarded verbatim to seed.sh so
        # the canonical invocation at harness/docker-compose.yml works as
        # written.
        if [[ -n "$ACAS_RESET_SCENARIO" ]]; then
          acas_die "$EX_USAGE" \
            "at most one scenario file may be given; got '$ACAS_RESET_SCENARIO' and '$1'."
        fi
        ACAS_RESET_SCENARIO="$1"
        shift
        ;;
    esac
  done

  # Anything after `--` is the scenario, at most one.
  while (( $# > 0 )); do
    if [[ -n "$ACAS_RESET_SCENARIO" ]]; then
      acas_die "$EX_USAGE" "unexpected trailing arguments: $(acas_join_words "$@")"
    fi
    ACAS_RESET_SCENARIO="$1"
    shift
  done

  # the combination is better than silently ignoring an argument the caller
  # clearly meant to have an effect.
  if (( ACAS_RESET_SCHEMA_ONLY )) && [[ -n "$ACAS_RESET_DATA_DIR" ]]; then
    acas_die "$EX_USAGE" \
      '--schema-only and --data-dir cannot be combined.' \
      '--data-dir is forwarded to harness/seed.sh, which --schema-only does not' \
      'run, so the value would have no effect.'
  fi
}

# This script ASSERTS its environment; it never installs one, never creates a
# database object and never changes a server setting.

acas_assert_environment() {
  acas_stage 'Preconditions 1/9: environment contract'

  local name missing=0
  local -a required=("${ACAS_RESET_REQUIRED_ENV_NONEMPTY[@]}")

  # The seed-only variables are required for a full reset and irrelevant to
  # fails BEFORE it drops 33 tables, rather than after.
  if (( ! ACAS_RESET_SCHEMA_ONLY )); then
    required+=("${ACAS_RESET_SEED_ENV_NONEMPTY[@]}")
  fi

  for name in "${required[@]}"; do
    if [[ -z "${!name-}" ]]; then
      printf 'FATAL: required environment variable %s is unset or empty.\n' "$name" >&2
      missing=1
    fi
  done
  for name in "${ACAS_RESET_REQUIRED_ENV_DECLARED[@]}"; do
    # `-v` tests declaration, not content. An empty ACAS_DB_SOCKET is valid and
    # means "no unix socket".
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

  # A numeric test alone let 99999 through to the TCP probe's bare
  # `int(sys.argv[2])` and to --port=, where the client's own truncation or the
  # kernel's rejection produced a connection failure with no useful cause.
  if [[ ! "$ACAS_DB_PORT" =~ ^[0-9]+$ ]]; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_PORT must be numeric; got '$ACAS_DB_PORT'."
  fi
  # THE RANGE IS THE FROZEN CARRIER'S, 1..9999, NOT THE TCP RANGE.
  # `LK-Port-Number pic x(4)' [common/acas-get-params.cbl:L158] and
  # `01 Ws-Mysql-Port-Number pic x(4)' [copybooks/mysql-variables.cpy:L91] are
  # FOUR characters, and every bridge STRINGs DB-Port into the second of them
  # [common/glpostingMT.cbl:L410-L413]. So a five-digit port reaches the compiled
  # cycle TRUNCATED - 13306 becomes 1330 - while this script would probe and drive
  # the untruncated one, and the two sides of the comparison would be talking to
  # different servers. Refused here rather than truncated silently.
  if (( 10#$ACAS_DB_PORT < 1 || 10#$ACAS_DB_PORT > 9999 )); then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_PORT must be between 1 and 9999; got '$ACAS_DB_PORT'." \
      'The frozen carrier holds FOUR characters - LK-Port-Number pic x(4)' \
      '[common/acas-get-params.cbl:L158] and Ws-Mysql-Port-Number pic x(4)' \
      '[copybooks/mysql-variables.cpy:L91] - so a five-digit port would reach' \
      'the compiled cycle truncated while this script used the whole value.' \
      'harness/docker-compose.yml publishes 3306, which is what the stack uses.'
  fi
  # CANONICALISED, and this matters beyond tidiness: the consent token embeds
  # the port verbatim, so `03306` and `3306` would demand two different tokens
  # for one target.
  ACAS_DB_PORT="$(( 10#$ACAS_DB_PORT ))"

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

  # GATE 1, GATE 2 and GATE 3. Asserted here so that a misdirected invocation
  # fails before the TCP probe, let alone the apply.
  acas_authorise_destructive_target

  # The transport policy, for the same reason and at the same point.
  acas_assert_transport_policy

  [[ -d "$ACAS_REPO" ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_REPO is not a directory: $ACAS_REPO." \
    'It must be the checkout holding the frozen COBOL, bridges and schema.'

  acas_log "ACAS_REPO   = $ACAS_REPO (read-only checkout; the specification)"
  acas_log "ACAS_OUT    = $ACAS_OUT"
  # A CATEGORY and a FINGERPRINT, never the topology (F-39). What a reader of
  # this transcript needs from the next line is which KIND of target was reset and
  # whether it was the same one another transcript reset -- not its name.
  acas_log "database    = $(acas_target_description)"
  # The ROLE distinction is the whole point of the line, and the role is what is
  # printed: the two account NAMES add nothing a reader can act on.
  acas_log 'the drop and re-apply run as the ADMIN account, deliberately NOT as the application account'
  acas_note 'no account name, host, port or schema is printed: the transcript is retained evidence'
  if (( ACAS_RESET_SCHEMA_ONLY )); then
    acas_note '--schema-only: harness/seed.sh will NOT be run, so its variables are not required'
  fi
  acas_note 'the password is never printed, never logged and never passed in argv'
}

# THE THREE DESTRUCTIVE GATES. See THE DESTRUCTIVE-TARGET POLICY above for why
# each one exists. Nothing in this function connects, reads or writes.
acas_gate_problem() {
  ACAS_RESET_GATE_PROBLEMS+=("$@")
  ACAS_RESET_GATE_PROBLEMS+=('')
}

acas_authorise_destructive_target() {
  ACAS_RESET_GATE_PROBLEMS=()

  # interpolated into SQL, and the safely-quoted literal is computed once here
  # so all twelve query sites share one derivation.
  if [[ ! "$ACAS_DB_NAME" =~ $ACAS_RESET_SCHEMA_NAME_PATTERN ]]; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_NAME is not a plain SQL identifier: '${ACAS_DB_NAME}'." \
      'This script interpolates the schema name into twelve information_schema' \
      'queries. A name carrying a quote, backslash, semicolon, whitespace or a' \
      'comment introducer is REFUSED rather than escaped, because no schema' \
      'this harness addresses needs one.'
  fi
  ACAS_RESET_SCHEMA_LITERAL="$(acas_sql_quote_literal "$ACAS_DB_NAME")"

  if [[ -z "${ACAS_DB_ADMIN_USER-}" ]]; then
    acas_gate_problem \
      'GATE 1 (privilege separation): ACAS_DB_ADMIN_USER is not set, and there' \
      'is deliberately no fallback. This script drops every table in the target' \
      "schema. It used to fall back to the application account (${ACAS_DB_USER})," \
      'which would mean the account the migrated cycle authenticates with every' \
      'day performing the drop. Set ACAS_DB_ADMIN_USER and' \
      'ACAS_DB_ADMIN_PASSWORD to a separate account holding DROP, CREATE,' \
      'ALTER, LOCK TABLES, INSERT and SELECT on this schema and nothing else.' \
      'Note that removing this fallback addressed which account this SCRIPT' \
      'uses, not what the application account is ABLE to do: the MariaDB vendor' \
      'entrypoint grants it ALL on the schema, so it carried DROP regardless of' \
      'anything decided here. That capability is removed separately, by the' \
      'least-privilege init script in harness/Dockerfile.mariadb, which reduces' \
      'the account to SELECT, INSERT, UPDATE and DELETE at container start.'
  elif [[ "$ACAS_DB_ADMIN_USER" == "$ACAS_DB_USER" ]]; then
    acas_gate_problem \
      "GATE 1 (privilege separation): ACAS_DB_ADMIN_USER and ACAS_DB_USER are" \
      "the same account ('${ACAS_DB_USER}'). The separation is the point:" \
      'naming the application account as the admin account restores exactly the' \
      'coupling this gate exists to break.'
  elif [[ -z "${ACAS_DB_ADMIN_PASSWORD-}" ]]; then
    acas_gate_problem \
      'GATE 1 (privilege separation): ACAS_DB_ADMIN_PASSWORD is unset or empty.' \
      'It is required whenever ACAS_DB_ADMIN_USER is set. It is never printed,' \
      'never logged and never passed in argv -- the client receives it through' \
      'MYSQL_PWD only.'
  fi

  # Resolved even when gate 1 failed, so the plan printout and the log line
  # have something truthful to name.
  ACAS_RESET_DB_USER="${ACAS_DB_ADMIN_USER:-<unset:ACAS_DB_ADMIN_USER>}"
  ACAS_RESET_DB_PASSWORD="${ACAS_DB_ADMIN_PASSWORD-}"

  # operator who has aimed at the wrong server is told THAT, rather than being
  # told to type a consent string naming it.
  local -a allowed_schemas=("${ACAS_RESET_DEFAULT_ALLOWED_SCHEMAS[@]}")
  local -a extra=()
  mapfile -t extra < <(acas_split_list "${ACAS_DB_ALLOWED_SCHEMAS-}")
  (( ${#extra[@]} )) && allowed_schemas+=("${extra[@]}")
  if ! acas_in_list "$ACAS_DB_NAME" "${allowed_schemas[@]}"; then
    acas_gate_problem \
      "GATE 3 (disposable target): the schema '${ACAS_DB_NAME}' is not in the" \
      "disposable-schema allow-list. Allowed: $(acas_join_words "${allowed_schemas[@]}")." \
      'Every table in the named schema would be dropped. If this schema really' \
      'is disposable, add it to ACAS_DB_ALLOWED_SCHEMAS -- an explicit,' \
      'reviewable act -- rather than removing the check.'
  fi

  local -a disposable_hosts=("${ACAS_RESET_DEFAULT_DISPOSABLE_HOSTS[@]}")
  extra=()
  mapfile -t extra < <(acas_split_list "${ACAS_DB_DISPOSABLE_HOSTS-}")
  (( ${#extra[@]} )) && disposable_hosts+=("${extra[@]}")
  if ! acas_in_list "$ACAS_DB_HOST" "${disposable_hosts[@]}"; then
    acas_gate_problem \
      "GATE 3 (disposable target): the host '${ACAS_DB_HOST}' is not in the" \
      "disposable-host allow-list. Allowed: $(acas_join_words "${disposable_hosts[@]}")." \
      'A hostname is not a security boundary and this list does not pretend to' \
      'be one -- gates 1 and 2 authorise the operation. It is a tripwire against' \
      'the common accident of an environment left pointing at a shared server.' \
      'Extend it with ACAS_DB_DISPOSABLE_HOSTS if the target really is' \
      'disposable.'
  fi

  ACAS_RESET_CONSENT_EXPECTED="${ACAS_RESET_CONSENT_PREFIX} ${ACAS_DB_NAME}@${ACAS_DB_HOST}:${ACAS_DB_PORT}"
  local supplied="${ACAS_RESET_CONSENT_ARG:-${ACAS_RESET_CONSENT-}}"
  if [[ -z "$supplied" ]]; then
    acas_gate_problem \
      'GATE 2 (consent): this run would DESTROY every table in the target' \
      'schema, and no consent was given. Set ACAS_RESET_CONSENT, or pass' \
      '--consent=, to EXACTLY:' \
      "    ${ACAS_RESET_CONSENT_EXPECTED}" \
      'The token names the schema, host and port on purpose: a bare --yes' \
      'inherited from a shell or a Compose file authorises nothing in' \
      'particular, whereas this one cannot be aimed at another database by' \
      'accident.'
  elif [[ "$supplied" != "$ACAS_RESET_CONSENT_EXPECTED" ]]; then
    acas_gate_problem \
      'GATE 2 (consent): the token does not match this target.' \
      "    expected: ${ACAS_RESET_CONSENT_EXPECTED}" \
      "    supplied: ${supplied}" \
      'The comparison is exact and case-sensitive. A mismatch almost always' \
      'means the environment now names a DIFFERENT database from the one the' \
      'token was written for -- which is precisely the accident this gate' \
      'exists to catch. Re-read the expected token above before retyping it.'
  fi

  if (( ${#ACAS_RESET_GATE_PROBLEMS[@]} )); then
    if (( ACAS_RESET_DRY_RUN )); then
      acas_warn 'the destructive-target gates would REFUSE this run; --dry-run reports them instead'
      local line
      for line in "${ACAS_RESET_GATE_PROBLEMS[@]}"; do
        printf '  %s\n' "$line"
      done
      acas_check 'WARN' 'destructive-target gates not satisfied (reported, not enforced, under --dry-run)'
      return 0
    fi
    acas_die "$EX_PRECONDITION" \
      'this run is REFUSED: it would destroy every table in the target schema' \
      'and the destructive-target gates are not satisfied.' \
      '' \
      "${ACAS_RESET_GATE_PROBLEMS[@]}" \
      'Run with --dry-run to see the full plan, and the exact consent token this' \
      'target requires, without executing anything.'
  fi

  ACAS_RESET_TARGET_AUTHORISED=1
  acas_ok "destructive target authorised: $(acas_target_description) as the admin account"
  acas_check 'PASS' 'destructive-target gates: distinct admin account, target-scoped consent, disposable schema and host'
}

# Open the run log. Its directory is $ACAS_OUT/reset, deliberately NOT
# $ACAS_OUT/<scenario>/.
acas_open_log() {
  local dir="$ACAS_OUT/reset"

  acas_assert_outside_repo 'ACAS_OUT' "$ACAS_OUT"
  acas_assert_outside_repo 'the reset log directory' "$dir"

  mkdir -p "$dir" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "could not create the reset log directory $dir." \
    'ACAS_OUT must be a writable volume.'
  chmod 700 -- "$dir" 2>/dev/null || true

  acas_assert_outside_repo 'the reset log directory' "$dir"

  local candidate="$dir/reset.log"
  acas_create_private_file "$candidate" 'the reset log'
  ACAS_RESET_LOG="$candidate"
  {
    printf 'harness/reset_db.sh run log\n'
    printf 'started (UTC): %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'this file lives under the ACAS_OUT reset directory and is never compared\n'
    printf -- '----------------------------------------------------------------\n'
  } >>"$ACAS_RESET_LOG"
}

# Precondition 5 of 9 -- THE SEQUENTIAL LOCK (R-3) "Execution strictly
# sequential -- no parallel scenario runs against the shared database." Two
# resets racing on one database would interleave 33 drops with 33 creates and.
acas_take_lock() {
  acas_stage 'Preconditions 5/9: the sequential reset lock'
  ACAS_RESET_LOCK="$ACAS_OUT/.reset_db.lock"

  # The lock is a write target like any other, and it is one this script also
  # DELETES (both on reclaim and on release), so a path resolving into the
  # checkout would mean removing a frozen file.
  acas_assert_outside_repo 'the reset lock' "$ACAS_RESET_LOCK"

  local holder=''
  if [[ -e "$ACAS_RESET_LOCK" ]]; then
    holder="$(cat -- "$ACAS_RESET_LOCK" 2>/dev/null || true)"
    if [[ "$holder" =~ ^[0-9]+$ ]] && kill -0 "$holder" 2>/dev/null; then
      acas_die "$EX_CONCURRENT" \
        "another harness/reset_db.sh (pid $holder) is already resetting ${ACAS_DB_NAME}." \
        'Resets are strictly sequential (R-3): two of them racing on the shared' \
        'database would interleave the 33 drop/create pairs and leave a state' \
        'neither caller asked for. Wait for it to finish.' \
        "Lock file: $ACAS_RESET_LOCK"
    fi
    acas_warn "reclaiming a stale reset lock left by pid ${holder:-<unreadable>} at $ACAS_RESET_LOCK"
    rm -f -- "$ACAS_RESET_LOCK" 2>/dev/null || true
  fi

  if ! (set -C; printf '%s\n' "$$" >"$ACAS_RESET_LOCK") 2>/dev/null; then
    acas_die "$EX_CONCURRENT" \
      "could not take the reset lock $ACAS_RESET_LOCK." \
      'Either another reset took it in the last instant, or the ACAS_OUT' \
      'directory is not writable.'
  fi
  ACAS_RESET_LOCK_HELD=1
}

# Precondition 3 of 9 -- THE FROZEN ARTIFACT.

# acas_assert_grep_count <expected> <grep-flags> <pattern> <description> `||
# true` is required.
acas_assert_grep_count() {
  local expected="$1" flags="$2" pattern="$3" description="$4"
  local actual
  actual="$(grep "$flags" -- "$pattern" "$ACAS_RESET_SCHEMA" || true)"
  if [[ "$actual" != "$expected" ]]; then
    acas_die "$EX_FROZEN" \
      "$ACAS_RESET_SCHEMA_RELPATH HAS BEEN MODIFIED: expected $expected $description, found $actual." \
      'The schema is FROZEN. Any diff touching mysql/ACASDB.sql is a defect in' \
      'the migration, regardless of how harmless it appears, and no schema' \
      'evolution of any kind is permitted -- no new tables, columns, indexes,' \
      'constraints, views, triggers or DDL statements (R-3).' \
      'Revert the file; do not re-pin this check and do not apply a modified' \
      'schema, because every parity result taken against it would be worthless.'
  fi
  acas_ok "$expected $description"
}

acas_assert_frozen_schema() {
  acas_stage "Preconditions 3/9: the frozen schema, $ACAS_RESET_SCHEMA_RELPATH"

  ACAS_RESET_SCHEMA="$ACAS_REPO/$ACAS_RESET_SCHEMA_RELPATH"

  [[ -e "$ACAS_RESET_SCHEMA" ]] || acas_die "$EX_PRECONDITION" \
    "the frozen schema $ACAS_RESET_SCHEMA does not exist." \
    'ACAS_REPO must point at the checkout; Compose mounts it read-only as /repo.'
  [[ -f "$ACAS_RESET_SCHEMA" && -r "$ACAS_RESET_SCHEMA" ]] || acas_die "$EX_PRECONDITION" \
    "the frozen schema $ACAS_RESET_SCHEMA is not a readable file."
  [[ -s "$ACAS_RESET_SCHEMA" ]] || acas_die "$EX_FROZEN" \
    "the frozen schema $ACAS_RESET_SCHEMA is empty."

  acas_log "applying: $ACAS_RESET_SCHEMA"

  # 1. Byte-for-byte identity. The strongest check, and the one that makes
  # "verbatim" a machine-checked claim rather than a comment.
  acas_have sha256sum || acas_die "$EX_PRECONDITION" \
    'sha256sum is not available, so the frozen schema cannot be verified byte-for-byte.' \
    'It is part of coreutils and is present in both harness images.'
  local actual_sha
  actual_sha="$(sha256sum -- "$ACAS_RESET_SCHEMA")"
  actual_sha="${actual_sha%% *}"
  if [[ "$actual_sha" != "$ACAS_RESET_SCHEMA_SHA256" ]]; then
    acas_die "$EX_FROZEN" \
      "$ACAS_RESET_SCHEMA_RELPATH is NOT byte-identical to the frozen baseline." \
      "expected sha256 $ACAS_RESET_SCHEMA_SHA256" \
      "actual   sha256 $actual_sha" \
      'The schema is frozen: any diff touching it is a defect in the migration,' \
      'regardless of how harmless it appears. Revert it, do not re-pin.' \
      'harness/Dockerfile.mariadb pins the same digest, so the image build will' \
      'reject it too.'
  fi
  acas_ok "byte-identical to the frozen baseline (sha256 ${ACAS_RESET_SCHEMA_SHA256:0:16}...)"

  # 2..9. The structural invariants, each asserted independently against the
  # committed schema. A digest mismatch alone would say only "something
  # changed"; these name WHICH rule was violated.
  acas_assert_grep_count "$ACAS_RESET_EXPECT_TABLES" -c '^CREATE TABLE ' \
    'CREATE TABLE statements (22 in scope + 11 out of scope)'
  acas_assert_grep_count "$ACAS_RESET_EXPECT_TABLES" -c '^DROP TABLE IF EXISTS ' \
    'DROP TABLE IF EXISTS statements -- THE DROP LIVES IN THE FROZEN FILE, which is why this script emits no DDL'
  acas_assert_grep_count 0 -cE '^[^/]*ALTER TABLE' \
    'real ALTER TABLE statements (the 66 naive hits are all mysqldump version-guarded comments)'
  acas_assert_grep_count 0 -ciE 'CREATE (INDEX|VIEW|TRIGGER|PROCEDURE|FUNCTION|DATABASE)' \
    'added DDL statements -- no index, view, trigger, routine or database creation'
  acas_assert_grep_count 0 -ciE '^[[:space:]]*USE[[:space:]]' \
    'USE statements -- which is why the database name is passed EXPLICITLY to the client'
  acas_assert_grep_count 0 -ciE '^[^-]*INSERT INTO' \
    'INSERT INTO statements -- the dump carries no rows, as it says itself at [mysql/ACASDB.sql:L9]'
  acas_assert_grep_count "$ACAS_RESET_EXPECT_TABLES" -c \
    'DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci' \
    'tables still declaring utf8mb3_general_ci -- the charset caveat at [mysql/ACASDB.sql:L9-L11] is NOT fixed (R-4)'
  acas_assert_grep_count 0 -ciwE 'float|double|real' \
    'FLOAT / DOUBLE / REAL tokens -- an accounting value can never traverse a binary float (R-2)'

  acas_note 'every check above is a READ; the file is never transformed, copied or repaired'
}

# Precondition 4 of 9 -- the script this one delegates re-seeding to.
acas_assert_seed_script() {
  acas_stage 'Preconditions 4/9: harness/seed.sh'

  local here
  here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
  ACAS_RESET_SEED="$here/$ACAS_RESET_SEED_SCRIPT"

  if (( ACAS_RESET_SCHEMA_ONLY )); then
    acas_note "--schema-only: $ACAS_RESET_SEED_SCRIPT will not be run, so it is not required"
    acas_check 'SKIP' 're-seed skipped by --schema-only'
    return 0
  fi

  [[ -e "$ACAS_RESET_SEED" ]] || acas_die "$EX_PRECONDITION" \
    "the seeding script $ACAS_RESET_SEED does not exist." \
    'Stage 5 is a drop, a re-apply AND a re-seed: without the seed the database' \
    'would hold 33 empty tables, which is a valid schema and an invalid premise' \
    'for a state diff. Use --schema-only if an empty database is what you want.'
  [[ -f "$ACAS_RESET_SEED" && -r "$ACAS_RESET_SEED" ]] || acas_die "$EX_PRECONDITION" \
    "the seeding script $ACAS_RESET_SEED is not a readable file."
  [[ -x "$ACAS_RESET_SEED" ]] || acas_die "$EX_PRECONDITION" \
    "the seeding script $ACAS_RESET_SEED is not executable." \
    'Restore its mode with: chmod +x harness/seed.sh'

  acas_ok "$ACAS_RESET_SEED is present and executable"
  acas_note 'it reproduces the loader contract of [common/masterLD.sh:L44-L115] and'
  acas_note 'invokes the compiled load programs as external processes only -- the'
  acas_note 'sanctioned use of compiled COBOL under R-1'
}

# compiler versions, and a digest over the compiled module set. Two of its options
# can substitute the bytes the oracle is built from -- ACAS_PRESQL2_SHA256 accepts a
# replacement archive, and ACAS_COBMYSQLAPI_OBJ reuses an already-compiled object --
# and the package ships two SUPERSEDED API sources that must not be used, so a
# renamed old API could otherwise define the specification unnoticed. The build
# records that as a fact; refusing it is this gate's job, which keeps the build
# script debuggable and the evidence path strict.
#
# FIVE THINGS ARE CHECKED, and the fourth is the one that makes the first three
# worth having:
#   1. the attestation EXISTS -- a partial or --only build leaves none;
#   2. it is the version this script understands;
#   3. `overrides-used' is `no';
#   4. the module-set digest still matches the modules ON DISK, recomputed here the
#      same way the build computed it. Without this an attestation would only
#      describe some build, not the artifacts stage 2 is about to execute;
#   5. the SOURCE-TRANSFORMATION DISCLOSURE is present and is REPORTED with the run.
#
# ⭐ ON THE FIFTH (finding CR-01). harness/build_oracle.sh edits the BUILD COPY of
# frozen sources in a declared set of places -- connectivity and IF-scope repairs
# without which the compiled cycle cannot reach MySQL at all. A version 1 attestation
# said nothing about them, so `overrides-used no' read as "this is the unmodified
# oracle" for a build that was not, and an empty diff drawn against it was presented as
# parity with the frozen behavioural specification. Version 2 publishes
# `oracle-source-is-frozen', a transform count, a set digest and one record per
# transformed path with its frozen and build digests.
#
# THIS SCRIPT DOES NOT REFUSE A TRANSFORMED ORACLE, and that is a deliberate choice
# rather than an omission: refusing would leave the project with NO oracle and
# therefore no evidence of any kind, since the transformations are what make the
# compiled cycle reach the database. What it does instead is refuse to be QUIET about
# it -- the count and the set digest are logged before stage 1 and again in the closing
# summary, so every verdict this script produces carries the disclosure beside it and
# no reader can mistake it for a verdict against the untouched checkout.
# =============================================================================
readonly ACAS_RESET_ATTESTATION_BASENAME='oracle-attestation.txt'
readonly ACAS_RESET_ATTESTATION_VERSION='2'

# Populated by acas_assert_oracle_attestation and reported in the summary.
ACAS_RESET_SOURCE_IS_FROZEN=''
ACAS_RESET_SOURCE_TRANSFORMS=''
ACAS_RESET_TRANSFORM_DIGEST=''
readonly -a ACAS_RESET_ORACLE_DIRS=(common general irs purchase sales stock)

#  IDENTICAL to acas_module_set_digest in harness/build_oracle.sh, deliberately:
#  every *.so under the six build directories, sorted by path, each hashed, and the
#  whole listing hashed again. If the two ever drift the gate fails closed, which is
#  the safe direction.
acas_reset_module_set_digest() {
  local dir
  {
    for dir in "${ACAS_RESET_ORACLE_DIRS[@]}"; do
      find "$ACAS_BUILD/$dir" -maxdepth 1 -type f -name '*.so' -print 2>/dev/null
    done
  } | LC_ALL=C sort | while IFS= read -r module; do
    sha256sum "$module" 2>/dev/null || printf 'UNREADABLE  %s\n' "$module"
  done | sha256sum | cut -d' ' -f1
}

acas_assert_oracle_attestation() {
  [[ -n "${ACAS_BUILD-}" ]] || acas_die "$EX_PRECONDITION" \
    'ACAS_BUILD is unset, so the oracle build tree cannot be located and its' \
    'provenance cannot be verified.' \
    'harness/docker-compose.yml sets ACAS_BUILD: /build.'

  local attestation="$ACAS_BUILD/$ACAS_RESET_ATTESTATION_BASENAME"
  #  AN ABSENT ATTESTATION IS EVIDENCE UNAVAILABLE, NOT A BEHAVIOURAL DIFFERENCE.
  #  build_oracle.sh writes it as the LAST act of a full run, so its absence means no
  #  oracle was produced -- and on this checkout that is the MEASURED outcome of the
  #  default frozen build, not a hypothetical: a zero-transformation build of the
  #  frozen sources fails with exit 74 because 22 of the frozen common/*MT.cbl
  #  bridges `copy "ACAS-SQLstate-error-list.cob"' and that member is absent from the
  #  checkout and from presql2-latest.zip alike. See README-python-migration.md
  #  section 8.7. Reporting that as EX_PRECONDITION would file it alongside "you
  #  forgot to build", when what it actually means is that the specification cannot
  #  presently be compiled and NOTHING WAS COMPARED.
  [[ -f "$attestation" ]] || acas_die "$EX_EVIDENCE_UNAVAILABLE" \
    "ORACLE UNAVAILABLE: no provenance attestation exists, so no compiled specification was produced." \
    "  attestation        $attestation (absent)" \
    'THIS IS NOT A BEHAVIOURAL DIFFERENCE. Nothing was compared, so nothing is' \
    'known about whether the Python cycle agrees with the frozen COBOL.' \
    'Stage 2 runs the compiled COBOL and its output IS the specification, so this' \
    'script will not set up a comparison against whatever modules happen to be lying' \
    'in the build tree.' \
    'build_oracle.sh writes the attestation as the last act of a FULL five-step run,' \
    'so an absent file means the oracle was never built, was built with --only or' \
    '--from and is therefore only partly this repository'"'"'s, or FAILED TO BUILD.' \
    'ON THIS CHECKOUT THE DEFAULT FROZEN BUILD FAILS, and that is measured rather' \
    'than predicted: 22 frozen common/*MT.cbl bridges copy ACAS-SQLstate-error-list.cob,' \
    'which exists in neither the checkout nor presql2-latest.zip. The member carries' \
    'the SQLSTATE-to-FS-Reply mapping that DEFINES the oracle'"'"'s rejection behaviour,' \
    'and rejection behaviour is precisely what this migration must reproduce, so it' \
    'cannot be fabricated (R-3, R-4) and must be supplied by the maintainer.' \
    'Build it: harness/build_oracle.sh   (see README-python-migration.md section 8.7)'

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
      oracle-source-is-frozen) ACAS_RESET_SOURCE_IS_FROZEN="$value" ;;
      source-transforms)       ACAS_RESET_SOURCE_TRANSFORMS="$value" ;;
      source-transform-set-sha256) ACAS_RESET_TRANSFORM_DIGEST="$value" ;;
    esac
  done < "$attestation"

  [[ "$version" == "$ACAS_RESET_ATTESTATION_VERSION" ]] || acas_die "$EX_PRECONDITION" \
    "the attestation at $attestation declares version '${version:-<none>}'; this script understands version $ACAS_RESET_ATTESTATION_VERSION." \
    'A format this script cannot read is refused rather than partly believed.' \
    'Rebuild the oracle with the matching harness/build_oracle.sh.'

  if [[ "$overrides" != 'no' ]]; then
    acas_die "$EX_PRECONDITION" \
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
    acas_die "$EX_PRECONDITION" \
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
      acas_die "$EX_PRECONDITION" \
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
  measured="$(acas_reset_module_set_digest)"
  [[ "$measured" == "$recorded_digest" ]] || acas_die "$EX_PRECONDITION" \
    'THE COMPILED MODULES DO NOT MATCH THE ATTESTATION, so its provenance does not' \
    'describe the oracle this run would execute.' \
    "  attestation        $attestation" \
    "  recorded digest    ${recorded_digest:-<unrecorded>}  (${recorded_count:-?} module(s))" \
    "  measured digest    $measured" \
    'Every *.so under the six build directories is hashed, sorted by path, and the' \
    'listing hashed again, so a single replaced, added or removed module changes' \
    'this value. Rebuild the oracle: harness/build_oracle.sh'

  #  THE DISCLOSURE MUST BE PRESENT. An attestation of the right version that omits it
  #  is a producer that did not look, and silence about whether the sources were
  #  transformed is exactly the condition finding CR-01 names.
  case "$ACAS_RESET_SOURCE_IS_FROZEN" in
    yes|no) : ;;
    *)
      acas_die "$EX_PRECONDITION" \
        'THE ATTESTATION DOES NOT STATE WHETHER THE ORACLE WAS COMPILED FROM THE FROZEN' \
        'SOURCES, so it cannot support a claim about the frozen behavioural specification.' \
        "  attestation              $attestation" \
        "  oracle-source-is-frozen  ${ACAS_RESET_SOURCE_IS_FROZEN:-<unrecorded>}" \
        'Rebuild the oracle: harness/build_oracle.sh'
      ;;
  esac

  acas_log "oracle provenance verified: $attestation"
  acas_note "no identity override; cobmysqlapi.o ${provenance}; preSQL archive matches its pin; ${recorded_count:-?} module(s), set digest $measured; toolchain ${cobc_version:-unknown}"

  if [[ "$ACAS_RESET_SOURCE_IS_FROZEN" == 'yes' ]]; then
    acas_log 'oracle sources: the frozen checkout, with no build-copy transformation'
    return 0
  fi

  #  ⭐ A TRANSFORMED ORACLE IS REFUSED, NOT WARNED ABOUT (finding SEC-02)
  #
  #  This used to be a warning, and a warning was not enough. Rule R-6 makes the
  #  COMPILED PROGRAM the behavioural specification and rule R-4 requires its defects to
  #  be REPRODUCED rather than repaired. The catalogued transforms repair IF scope,
  #  connection lifetime and stale reply status in the frozen programs - so a build that
  #  applies them has repaired the specification, and an empty diff against it says the
  #  migrated cycle matches a PATCHED system. That is not the claim this protocol
  #  exists to make, and publishing it as though it were is the evidence-integrity
  #  defect itself.
  #
  #  Refusing is reported as EVIDENCE UNAVAILABLE, with its own exit status, because it
  #  must never be confused with a behavioural difference: a difference is a finding
  #  about the migration, and this is the absence of anything to find it against.
  if (( ! ACAS_RESET_ACCEPT_TRANSFORMED_ORACLE )); then
    acas_die "$EX_EVIDENCE_UNAVAILABLE" \
      'EVIDENCE UNAVAILABLE: THE ORACLE WAS COMPILED FROM TRANSFORMED SOURCES.' \
      "  attestation              $attestation" \
      "  oracle-source-is-frozen  no" \
      "  transformed files        ${ACAS_RESET_SOURCE_TRANSFORMS:-?}" \
      "  transform-set digest     ${ACAS_RESET_TRANSFORM_DIGEST:-<unrecorded>}" \
      '' \
      'THIS IS NOT A BEHAVIOURAL DIFFERENCE. Nothing was compared. The compiled' \
      'program IS the behavioural specification (rule R-6) and its defects must be' \
      'reproduced rather than repaired (rule R-4), so an oracle whose sources were' \
      'repaired cannot arbitrate anything: an empty diff against it would say the' \
      'migrated cycle matches a PATCHED system, which is not the claim this protocol' \
      'makes.' \
      '' \
      'Every transformed path is listed in the attestation with its frozen and build' \
      'digests and the reason for it, and the frozen checkout itself is untouched.' \
      '' \
      'To obtain evidence, build a frozen oracle - which is now the DEFAULT:' \
      '    harness/build_oracle.sh' \
      'See README-python-migration.md section 8.7 for what that does on this' \
      'checkout, which is measured rather than predicted.' \
      '' \
      'To drive the cycle against this oracle for DIAGNOSIS, acknowledge it:' \
      '    harness/reset_db.sh --accept-transformed-oracle ...' \
      'The run then proceeds and every verdict it prints is marked NO PARITY CLAIM.'
  fi

  ACAS_RESET_ORACLE_IS_DIAGNOSTIC=1
  acas_warn "PROCEEDING AGAINST A TRANSFORMED ORACLE BECAUSE --accept-transformed-oracle WAS GIVEN. ${ACAS_RESET_SOURCE_TRANSFORMS:-?} build-copy file(s) differ from the frozen checkout (transform-set digest ${ACAS_RESET_TRANSFORM_DIGEST:-<unrecorded>}), each listed in $attestation with its frozen and build digests and its reason. NO VERDICT FROM THIS RUN IS A PARITY CLAIM, and the summary will say so however the comparison turns out: the oracle is a diagnostic build, not the frozen specification."
}


# =============================================================================
# ⭐ AN EVIDENCE RUN REFUSES EVERY DESTRUCTIVE-TARGET BYPASS (findings MJ-18, M-06)
#
# This script is TWO things, and the difference decides which options it may honour.
# As stages 1 and 5 of the parity protocol it drops and re-applies every table in the
# schema a verdict will be drawn from. As the general administrative reset it is also
# the tool an operator uses on a throwaway database of their own, and for that it
# offers documented escape hatches: ACAS_DB_ALLOWED_SCHEMAS extends the disposable-
# SCHEMA allow-list, ACAS_DB_DISPOSABLE_HOSTS extends the disposable-HOST allow-list,
# and ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE / --acknowledge-destructive assert a target is
# disposable without proof -- that last one short-circuiting BOTH the static check and
# the server-side sentinel, so with it set this script will drop a database that
# carries no disposability declaration at all.
#
# Those hatches are legitimate for administration and WRONG for evidence: a verdict
# drawn from a database nobody proved was throwaway is a verdict about an unknown
# state. So the two roles are separated by the RUN ITSELF rather than by a wrapper.
# ACAS_PARITY_RUN_ID is what makes ten separate invocations one protocol run -- bound by
# tests/conftest.py's `bound_run_id` for the composed protocol, exported by the operator
# for a hand-driven one (README-python-migration.md section 8) -- and on any run
# carrying it every hatch is REFUSED. Unbound, the hatches remain, because then this is
# the administrative tool and not a protocol stage.
#
# WHY THIS IS STRONGER THAN WHAT IT REPLACES. The refusal used to live in the deleted
# harness/run_parity.sh, which could only guard the stages IT drove: a hand-driven
# stage 1 honoured every hatch. Here the guard travels with the stage, so a
# hand-driven protocol run is scoped exactly as a composed one is.
#
# REFUSED, NOT SILENTLY UNSET. An operator who set one deliberately is told the
# evidence path will not honour it, rather than left believing it applied.
# =============================================================================
readonly -a ACAS_RESET_EVIDENCE_BYPASSES=(
  ACAS_DB_ALLOWED_SCHEMAS
  ACAS_DB_DISPOSABLE_HOSTS
  ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE
  ACAS_RESET_ACKNOWLEDGE
)

acas_assert_no_evidence_bypass() {
  #  UNBOUND MEANS ADMINISTRATIVE USE, so nothing is refused.
  [[ -n "$ACAS_RESET_RUN_ID" ]] || return 0

  local name present=''
  for name in "${ACAS_RESET_EVIDENCE_BYPASSES[@]}"; do
    if [[ -n "${!name-}" ]]; then
      present+="${present:+, }$name"
    fi
  done
  [[ -z "$present" ]] || acas_die "$EX_PRECONDITION" \
    "a destructive-target bypass is set on a protocol-bound run: $present." \
    "This run carries ACAS_PARITY_RUN_ID='$ACAS_RESET_RUN_ID', so it is stage 1 or" \
    'stage 5 of the parity protocol and the state it creates will be compared. It' \
    'therefore aims only at a target that PROVES it is disposable, and will not' \
    'honour a widened allow-list or an unproven acknowledgement.' \
    'ACAS_DB_ALLOWED_SCHEMAS and ACAS_DB_DISPOSABLE_HOSTS extend the two' \
    'disposability allow-lists; ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE and' \
    '--acknowledge-destructive bypass the static check AND the server-side sentinel' \
    'proof, so with one set this script would drop a database that cannot prove it is' \
    'disposable and a verdict would be drawn from whatever it contained.' \
    'Unset it and re-run. To reset a different target deliberately, invoke this' \
    'script WITHOUT a bound run id -- it is the general administrative tool and it' \
    'keeps those options on purpose. Evidence production does not.'

  acas_note "protocol-bound run ($ACAS_RESET_RUN_ID): every destructive-target bypass is refused, so the target must prove it is disposable"
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
acas_assert_seed_files() {
  local parsed rc=0
  parsed="$(python3 - "$ACAS_RESET_SCENARIO" "$ACAS_RESET_HARNESS" <<'SEEDLIST'
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

#  THE SHARED DUPLICATE-REJECTING LOADER (finding MJ-17): a shadowed `seed_files`
#  key would stage a fixture the definition does not appear to declare. argv[2] is
#  the harness directory, passed in because a heredoc has no __file__.
sys.path.insert(0, sys.argv[2])

import normalize
import yaml

BARE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')

path = sys.argv[1]
try:
    with open(path, 'r', encoding='utf-8') as handle:
        document = normalize.load_scenario_yaml(handle.read())
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
    acas_die "$EX_PRECONDITION" \
      "the scenario's seed_files list could not be read from $ACAS_RESET_SCENARIO." \
      "  reported: ${parsed:-<no output>}"
  fi

  local key len value begin_seen=0 declared='' ending=''
  local -a wanted=()
  while IFS=$'\t' read -r key len value; do
    case "$key" in
      BEGIN)
        [[ "$len" == '1' ]] || acas_die "$EX_PRECONDITION" \
          "seed transport version '$len' is not the version this reader speaks."
        begin_seen=1
        ;;
      COUNT) declared="$len" ;;
      END)   ending="$len" ;;
      SEED_FILE)
        [[ "$len" =~ ^[0-9]+$ ]] || acas_die "$EX_PRECONDITION" \
          "a SEED_FILE record carries a non-numeric length field ('$len')."
        (( ${#value} == len )) || acas_die "$EX_PRECONDITION" \
          "a SEED_FILE record decoded to ${#value} byte(s) where it declares $len."
        [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || acas_die \
          "$EX_PRECONDITION" \
          "the decoded seed file name '$value' is not a plain file name."
        wanted+=("$value")
        ;;
      '') : ;;
      *)
        acas_die "$EX_PRECONDITION" "unknown seed transport record '$key'."
        ;;
    esac
  done <<<"$parsed"

  (( begin_seen == 1 )) || acas_die "$EX_PRECONDITION" \
    'the seed transport stream carries no BEGIN record.'
  [[ "$declared" =~ ^[0-9]+$ && "$ending" =~ ^[0-9]+$ ]] || acas_die \
    "$EX_PRECONDITION" 'the seed transport stream carries no numeric COUNT and END.'
  (( declared == ending && ${#wanted[@]} == declared )) || acas_die \
    "$EX_PRECONDITION" \
    "the seed transport disagrees with itself: COUNT $declared, END $ending, ${#wanted[@]} decoded."

  [[ -d "$ACAS_RESET_SEED_DIR" ]] || acas_die "$EX_PRECONDITION" \
    "the scenario's fixture directory does not exist: $ACAS_RESET_SEED_DIR" \
    "Build it first: harness/seed.sh --build-fixtures $ACAS_RESET_SCENARIO" \
    'Checked HERE rather than in stage 1 so that a missing fixture does not cost' \
    'a dropped and re-applied schema before anything reports it.'

  local name absent=0
  for name in "${wanted[@]}"; do
    if [[ ! -f "$ACAS_RESET_SEED_DIR/$name" || ! -r "$ACAS_RESET_SEED_DIR/$name" ]]; then
      printf 'FATAL: declared seed file is missing or unreadable: %s\n' \
        "$ACAS_RESET_SEED_DIR/$name" >&2
      absent=1
    fi
  done
  (( absent == 0 )) || acas_die "$EX_PRECONDITION" \
    "the scenario declares seed files that are not in $ACAS_RESET_SEED_DIR." \
    "Rebuild the fixture: harness/seed.sh --build-fixtures $ACAS_RESET_SCENARIO" \
    'A missing file would leave its table empty and the resulting dump would' \
    'still look like a successful seed.'

  acas_log "seed fixture verified: ${#wanted[@]} declared file(s) present in $ACAS_RESET_SEED_DIR"
}


# The optional scenario positional. Checked for readability here so a typo
# fails before 33 tables are dropped, rather than after.
acas_assert_scenario() {
  [[ -n "$ACAS_RESET_SCENARIO" ]] || return 0

  local scenario_real=''
  scenario_real="$(readlink -f -- "$ACAS_RESET_SCENARIO" 2>/dev/null || true)"
  [[ -n "$scenario_real" ]] || acas_die "$EX_USAGE" \
    "the scenario file '$ACAS_RESET_SCENARIO' does not exist." \
    'The canonical invocation passes a scenario file path; see' \
    'harness/docker-compose.yml.'
  ACAS_RESET_SCENARIO="$scenario_real"

  [[ -e "$ACAS_RESET_SCENARIO" ]] || acas_die "$EX_USAGE" \
    "the scenario file '$ACAS_RESET_SCENARIO' does not exist." \
    'The canonical invocation passes a scenario file path; see' \
    'harness/docker-compose.yml.'
  [[ -f "$ACAS_RESET_SCENARIO" && -r "$ACAS_RESET_SCENARIO" ]] || acas_die "$EX_USAGE" \
    "the scenario '$ACAS_RESET_SCENARIO' is not a readable file."

  acas_resolve_fixture_root
}

# -----------------------------------------------------------------------------
# THE CANONICAL FIXTURE ROOT, DEFAULTED RATHER THAN DEMANDED
#
# A scenario's own `seed_dir' resolves relative to the scenario FILE, which sits in
# the checkout, and the checkout is mounted read-only because it is frozen
# specification (R-3). So a built fixture can never live where the scenario points,
# and an omitted --seed-dir used to leave harness/seed.sh resolving a path inside the
# read-only tree -- AFTER this script had already dropped and re-applied all 33
# tables. Defaulting removes that way of composing the protocol wrongly.
#
# ONE RULE, THREE DERIVATIONS. harness/seed.sh --build-fixtures WRITES the fixtures and owns
# the rule -- its `ACAS_BF_OUT' default is the single statement of it. This script
# derives it identically for the shell side, and
# tests/conftest.py's scenario_fixture_dir() for the pytest side;
# tests/arithmetic/test_comp_binary.py asserts that the
# three agree, because a comment would not keep them in step.
#
# ONLY WITH A SCENARIO. Without one this script re-seeds from the ambient data
# directory and there is no scenario name to append, so nothing is defaulted.
acas_resolve_fixture_root() {
  [[ -z "$ACAS_RESET_SEED_DIR" ]] || return 0
  [[ -n "$ACAS_RESET_SCENARIO" ]] || return 0

  local stem="${ACAS_RESET_SCENARIO##*/}"
  stem="${stem%.*}"
  [[ "$stem" =~ ^[A-Za-z0-9_-]+$ ]] || acas_die "$EX_USAGE" \
    "the scenario name '$stem' is not a plain identifier." \
    'It names the fixture directory, so it may hold only letters, digits,' \
    'underscore and hyphen.'

  local root="${ACAS_FIXTURES:-}"
  [[ -n "$root" ]] || root="${ACAS_DATA:-/data}"/fixtures
  ACAS_RESET_SEED_DIR="${root%/}/$stem"
  acas_note "fixture root (canonical, --seed-dir not stated): $ACAS_RESET_SEED_DIR"
}


# CREDENTIAL HYGIENE. The password reaches the client through MYSQL_PWD and
# nowhere else.

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

# ONE KEY, ONE CLOSED SET, AND UNRECOGNISED TEXT IS REFUSED.
# `1|true|yes|on' is affirmative and `|0|false|no|off' is negative, matched
# case-insensitively; the identical set lives in
# acas_posting/cli/args.py as AFFIRMATIVE_SPELLINGS / NEGATIVE_SPELLINGS
# and is read there by read_declared_flag, so one exported value cannot mean two
# different things to the two halves of the harness. Anything else STOPS the run
# rather than resolving to either answer: the value governs whether a credential
# and every posted figure may cross a network in the clear, and only the operator
# who typed it knows what was meant. The message never echoes the value.
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
# target has earned. Populates ACAS_RESET_TLS_VARIANTS, most secure first, or
# aborts.
acas_assert_transport_policy() {
  local ca="${ACAS_DB_TLS_CA-}"
  ACAS_RESET_TLS_VARIANTS=()

  if [[ -n "$ca" ]]; then
    [[ -r "$ca" ]] || acas_die "$EX_PRECONDITION" \
      "ACAS_DB_TLS_CA names a file that cannot be read: $ca" \
      'It must be the PEM bundle the server certificate chains to.'
    ACAS_RESET_TLS_VARIANTS+=("--ssl-ca=$ca --ssl-verify-server-cert")
  fi

  if acas_target_is_local; then
    ACAS_RESET_TLS_VARIANTS+=('--skip-ssl')
    acas_note 'transport: local target, so plaintext is permitted'
    return 0
  fi

  if acas_plaintext_declared; then
    acas_warn 'ACAS_DB_ALLOW_PLAINTEXT permits plaintext to a NON-LOCAL server; the admin credential and every answer are unprotected'
    ACAS_RESET_TLS_VARIANTS+=('--skip-ssl')
    return 0
  fi

  if [[ -z "$ca" ]]; then
    acas_die "$EX_PRECONDITION" \
      "the target ${ACAS_DB_HOST}:${ACAS_DB_PORT} is not local and no verified TLS is configured." \
      'This script authenticates as an account holding DROP on every table and' \
      'then reads the whole schema, so the connection must be protected.' \
      'Either set ACAS_DB_TLS_CA to the PEM bundle the server certificate' \
      'chains to, or -- if this really is an isolated harness network such as the' \
      'private Compose network [harness/docker-compose.yml] -- declare it with' \
      'ACAS_DB_ALLOW_PLAINTEXT=1.' \
      'It is NOT downgraded silently: that was the defect.'
  fi

  acas_note 'transport: verified TLS required (CA supplied, certificate and hostname checked)'
  return 0
}

# Build the client argv for a read-only query. The password is NOT in it.
acas_sql_argv() {
  local client="$1" tls="$2" budget="${3:-$ACAS_TIMEOUT_CLIENT}"

  # An empty budget would silently mean "no deadline at all", which is the
  # exact defect this bounding exists to remove, so it is a hard error rather
  # than a fallback.
  [[ "$budget" =~ ^[1-9][0-9]*$ ]] || acas_die "$EX_PRECONDITION" \
    "acas_sql_argv was given a non-positive deadline: '$budget'." \
    'Deadlines are resolved by acas_resolve_deadlines before any client runs.'

  acas_deadline_prefix "$budget"
  printf '%s\n' "${ACAS_DEADLINE_ARGV[@]}"
  printf '%s\n' "$client" '--protocol=TCP'
  if [[ -n "$tls" ]]; then
    # `tls` may carry two words (--ssl-ca=... --ssl-verify-server-cert), so it
    # is split deliberately here -- each flag must be its own argv element.
    local flag
    for flag in $tls; do
      printf '%s\n' "$flag"
    done
  fi
  printf '%s\n' \
    "--host=$ACAS_DB_HOST" \
    "--port=$ACAS_DB_PORT" \
    "--user=$ACAS_RESET_DB_USER" \
    '--batch' \
    '--skip-column-names' \
    "--database=$ACAS_DB_NAME"
}

# acas_build_sql_argv <client> <tls-flag> [budget-seconds] Publishes the client
# argv through ACAS_SQL_ARGV.
acas_build_sql_argv() {
  local client="$1" tls="$2" budget="${3:-$ACAS_TIMEOUT_CLIENT}"
  ACAS_SQL_ARGV=()
  mapfile -t ACAS_SQL_ARGV < <(acas_sql_argv "$client" "$tls" "$budget")

  if (( ${#ACAS_SQL_ARGV[@]} < 10 )) || [[ "${ACAS_SQL_ARGV[0]}" != 'timeout' ]]; then
    acas_die "$EX_PRECONDITION" \
      'the database client argv could not be composed.' \
      "Got ${#ACAS_SQL_ARGV[@]} word(s); a bounded invocation needs at least 10," \
      "the first of which must be 'timeout'." \
      'This means acas_sql_argv rejected its arguments (its diagnostic is above),' \
      'and continuing would run the client with NO deadline.'
  fi
}

# Run one read-only statement (or several, separated by `;`) and capture the
# result in ACAS_SQL_OUT, one row per line with tab-separated columns.
acas_sql_scalar() {
  local sql="$1"
  ACAS_SQL_OUT=''
  ACAS_SQL_DIAG=''

  local -a argv=()
  local out rc=0

  # Already pinned: one attempt, no retry, no variant search.
  if [[ -n "$ACAS_SQL_CLIENT" ]]; then
    acas_build_sql_argv "$ACAS_SQL_CLIENT" "$ACAS_SQL_TLS_FLAG"
    argv=("${ACAS_SQL_ARGV[@]}" "--execute=$sql")
    out="$(MYSQL_PWD="$ACAS_RESET_DB_PASSWORD" "${argv[@]}" 2>/dev/null)" || rc=$?
    if (( rc == 0 )); then
      ACAS_SQL_OUT="$out"
      return 0
    fi
    ACAS_SQL_DIAG="$(MYSQL_PWD="$ACAS_RESET_DB_PASSWORD" "${argv[@]}" 2>&1 || true)"
    if [[ "$ACAS_SQL_DIAG" == *'Access denied'* ]]; then
      return 2
    fi
    return 1
  fi

  # Not pinned yet: probe both binaries and every PERMITTED TLS variant,
  # pinning the first combination that works.
  local client tls
  local saw_client=0
  if (( ${#ACAS_RESET_TLS_VARIANTS[@]} == 0 )); then
    acas_die "$EX_PRECONDITION" \
      'no permitted client transport for this target.' \
      'Unreachable unless acas_assert_transport_policy was skipped or changed:' \
      'it either records at least one variant or aborts with a named cause.'
  fi
  for client in mariadb mysql; do
    acas_have "$client" || continue
    saw_client=1
    for tls in "${ACAS_RESET_TLS_VARIANTS[@]}"; do
      # Through acas_build_sql_argv, never `mapfile < <(acas_sql_argv ...)'.
      acas_build_sql_argv "$client" "$tls"
      argv=("${ACAS_SQL_ARGV[@]}" "--execute=$sql")
      rc=0
      out="$(MYSQL_PWD="$ACAS_RESET_DB_PASSWORD" "${argv[@]}" 2>/dev/null)" || rc=$?
      if (( rc == 0 )); then
        ACAS_SQL_CLIENT="$client"
        ACAS_SQL_TLS_FLAG="$tls"
        ACAS_SQL_OUT="$out"
        return 0
      fi
      ACAS_SQL_DIAG="$(MYSQL_PWD="$ACAS_RESET_DB_PASSWORD" "${argv[@]}" 2>&1 || true)"
    done
    if [[ "$ACAS_SQL_DIAG" == *'Access denied'* ]]; then
      return 2
    fi
    return 1
  done
  (( saw_client )) || return 3
  return 1
}

# One scalar value from a single-column, single-row query.
acas_sql_value() {
  local sql="$1"
  local rc=0
  acas_sql_scalar "$sql" || rc=$?
  if (( rc != 0 )); then
    return "$rc"
  fi
  local line value=''
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    value="$line"
  done <<<"$ACAS_SQL_OUT"
  ACAS_SQL_OUT="$value"
  return 0
}

# A read-only query whose failure is never expected. Any failure here means the
# database moved under us mid-run, so it aborts rather than degrading.
acas_sql_value_or_die() {
  local sql="$1" what="$2"
  local rc=0
  acas_sql_value "$sql" || rc=$?
  if (( rc != 0 )); then
    acas_die "$EX_VERIFY" \
      "could not read $what from the server." \
      "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  fi
}

# TCP reachability, using python3 so no client binary and no credential is
# needed. python3 is guaranteed present by harness/Dockerfile.gnucobol.
acas_db_tcp_probe() {
  # The port range is asserted in acas_assert_environment, before anything
  # connects, so `int(sys.argv[2])` here can no longer receive 99999 and fail
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

# Precondition 6 of 9 -- MariaDB readiness.
acas_wait_for_database() {
  acas_stage 'Preconditions 6/9: MariaDB readiness'

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
        'The host and port are deliberately not printed (F-39): read them from' \
        'ACAS_DB_HOST and ACAS_DB_PORT in this environment, which is where this' \
        'script reads them from too.' \
        'Nothing can be reset without it. Start the service' \
        '(docker compose -f harness/docker-compose.yml up -d mariadb), wait for' \
        'its healthcheck, or raise ACAS_DB_WAIT_TIMEOUT.'
    fi
    sleep "$interval"
    elapsed=$(( elapsed + interval ))
  done
  acas_log "TCP reachable after ${elapsed}s"

  # An open port is not readiness, and this is also where the client binary and
  # TLS variant get pinned for the whole run -- including the apply, which must
  # not have to discover them mid-file.
  local rc=0 denied_for=0
  elapsed=0
  while true; do
    rc=0
    acas_sql_scalar 'select 1' || rc=$?
    case "$rc" in
      0)
        acas_log "authenticated as the admin account against $(acas_target_description)"
        acas_log "client pinned : ${ACAS_SQL_CLIENT} ${ACAS_SQL_TLS_FLAG:-(TLS negotiated normally)}"
        return 0
        ;;
      3)
        acas_die "$EX_DATABASE" \
          'no mariadb or mysql client binary is available, so the frozen schema cannot be applied.' \
          'The schema must be streamed to a client UNMODIFIED -- that is the whole' \
          'of the drop-and-recreate, because the frozen file carries its own 33' \
          'DROP TABLE IF EXISTS statements -- and the autocommit setting must be' \
          'read before anything is touched, because the frozen COBOL never' \
          'reaches a COMMIT and only writes durable rows when it is ON.' \
          'harness/Dockerfile.gnucobol installs mariadb-client for exactly this;' \
          'run inside the gnucobol service image.'
        ;;
      2)
        if (( denied_for >= auth_grace )); then
          acas_die "$EX_DATABASE" \
            "MariaDB at ${ACAS_DB_HOST}:${ACAS_DB_PORT} REJECTED the credentials for user '${ACAS_RESET_DB_USER}'." \
            'The server is alive, so this is a credential or grant problem, not a' \
            'readiness problem, and waiting longer will not fix it.' \
            'Both services in harness/docker-compose.yml interpolate the same two' \
            'variables for the application account, so a mismatch usually means' \
            'the database volume was created with a different password: recreate' \
            'it with "docker compose ... down -v", or correct the credentials.' \
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
            "The target database ${ACAS_DB_NAME} must already exist: the frozen dump" \
            'contains no CREATE DATABASE statement, and this script never creates' \
            'one -- the MariaDB entrypoint does, once, from MARIADB_DATABASE.' \
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

# -----------------------------------------------------------------------------
# Precondition 8 of 9 -- autocommit MUST be ON, because a reset is RUNTIME
# APPLICATION ACCESS. The Agent Action Plan scopes its autocommit-OFF requirement
# to SEEDING and to nothing else: section 0.2.1.1 ("the batch loader turns
# autocommit off"), section 0.5.2 ("autocommit must be off DURING SEEDING") and
# section 0.4.1.7 ("autocommit off TO MATCH THE LOADERS" -- the loaders being the
# seeding stage), all from the loader banner at [common/glbatchLD.cbl:L9-L13].
# harness/seed.sh owns that window, sets it around the frozen load programs, and
# restores this runtime mode when it closes. WHICH mode the window runs is that
# script's own R-6 arbitration and was measured: ON by default, because it is the
# only mode in which the frozen loaders leave a durable row, with the AAP-literal
# OFF selectable through ACAS_SEED_AUTOCOMMIT=off. Nothing here depends on the
# choice -- this precondition is about the mode OUTSIDE the window.
#
# ASSERTED, NEVER SET. See the header for the frozen-source proof: the loaders'
# commit/rollback paragraphs are unreachable and the bridges never commit at all,
# so under the AAP-literal OFF window every COBOL write is discarded at session
# close. That consequence is reported, not repaired (R-4). Finding the mode OFF
# here means a seeding window is still open -- a seed interrupted before its exit
# trap ran, or a server configured for autocommit off server-wide -- and the
# database would then be one neither cycle can write to. The runtime setting
# belongs to the server, whose authority is harness/Dockerfile.mariadb; issuing
# `SET autocommit` here -- even "just for the DDL" -- would create a second
# authority for it and change behaviour, which R-3 and R-4 both forbid.
#
# Read TWICE: once here, before anything is applied, and again after the apply,
# because the frozen file changes six session variables [mysql/ACASDB.sql:L13-L22]
# and the claim that it left this one alone is re-asserted, not assumed.
# The `+ 0` coercion is required, not cosmetic: autocommit is a boolean system
# variable and renders as ON/OFF in a string context, so a bare select can hand
# back "ON" where a caller expects 1.
ACAS_RESET_AUTOCOMMIT_SQL='select concat_ws(0x2f, @@GLOBAL.autocommit + 0, @@SESSION.autocommit + 0)'

# acas_read_autocommit -> echoes "<global>/<session>" into ACAS_SQL_OUT.
acas_read_autocommit() {
  local rc=0
  acas_sql_scalar "$ACAS_RESET_AUTOCOMMIT_SQL" || rc=$?
  if (( rc != 0 )); then
    acas_die "$EX_DATABASE" \
      'could not read the autocommit setting from the server.' \
      "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  fi

  local value='' line
  while IFS= read -r line; do
    if [[ "$line" =~ ^[0-9]+/[0-9]+$ ]]; then
      value="$line"
    fi
  done <<<"$ACAS_SQL_OUT"

  [[ -n "$value" ]] || acas_die "$EX_DATABASE" \
    'the server did not return a readable autocommit setting.' \
    "Received: ${ACAS_SQL_OUT:-<empty>}"
  ACAS_SQL_OUT="$value"
}

acas_assert_autocommit() {
  local when="$1"

  acas_read_autocommit
  local value="$ACAS_SQL_OUT"
  local global="${value%%/*}" session="${value##*/}"
  acas_log "@@GLOBAL.autocommit = $global   @@SESSION.autocommit = $session   ($when)"

  if (( global != 1 || session != 1 )); then
    acas_die "$EX_AUTOCOMMIT" \
      "autocommit is OFF (global=$global, session=$session) $when; the reset is REFUSED." \
      'A reset is RUNTIME APPLICATION ACCESS, not seeding, and the Agent Action' \
      'Plan scopes its autocommit-OFF requirement to seeding in all three of its' \
      'provisions -- section 0.2.1.1 ("the batch loader turns autocommit off"),' \
      'section 0.5.2 ("autocommit must be off DURING SEEDING") and section 0.4.1.7' \
      'on harness/Dockerfile.mariadb ("autocommit off TO MATCH THE LOADERS", the' \
      'loaders being the seeding stage). harness/seed.sh owns that window and' \
      'restores this mode when it closes, whichever mode the window ran.' \
      'Finding the mode OFF here means either that the server is configured for' \
      'autocommit off server-wide -- which leaves the frozen COBOL unable to' \
      'persist a single row, since it never reaches a COMMIT -- or that a seed was' \
      'interrupted before its exit trap could restore the mode. Either way the' \
      'state this script would hand the comparison is not a state either cycle can' \
      'write to, so the drop is refused.' \
      'This script deliberately does NOT set the mode: harness/Dockerfile.mariadb' \
      'declares autocommit=1 in /etc/mysql/conf.d/99-acas-oracle.cnf for runtime' \
      'access, and harness/seed.sh is the only place the mode is ever changed.' \
      'Start the harness MariaDB service built from that Dockerfile, or restore' \
      'the runtime mode with: set global autocommit = 1'
  fi
  acas_ok "autocommit is ON, globally and for this session ($when) -- the runtime mode; the seeding window, whatever mode it runs, belongs to harness/seed.sh"
}

# Precondition 9 of 9 -- the privileges the FROZEN FILE'S OWN statements need.
acas_assert_privileges() {
  acas_stage 'Preconditions 9/9: privileges for the drop and re-apply'

  local grantee_expr
  grantee_expr="concat(char(39), substring_index(current_user(), char(64), 1), char(39), char(64), char(39), substring_index(current_user(), char(64), -1), char(39))"

  local sql
  sql="select group_concat(distinct p order by p separator ',') from ("
  sql+=" select PRIVILEGE_TYPE as p from information_schema.USER_PRIVILEGES"
  sql+=" where GRANTEE = ${grantee_expr}"
  sql+=" union all"
  sql+=" select PRIVILEGE_TYPE as p from information_schema.SCHEMA_PRIVILEGES"
  sql+=" where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL} and GRANTEE = ${grantee_expr}"
  sql+=" ) as g"

  local rc=0
  acas_sql_value "$sql" || rc=$?
  if (( rc != 0 )); then
    acas_die "$EX_PRIVILEGE" \
      'could not read the privileges of the connected account.' \
      "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  fi

  local granted="${ACAS_SQL_OUT}"
  if [[ -z "$granted" || "$granted" == 'NULL' ]]; then
    acas_die "$EX_PRIVILEGE" \
      "the account '${ACAS_RESET_DB_USER}' holds no recorded privileges on ${ACAS_DB_NAME}." \
      'Applying the frozen schema needs DROP, CREATE, LOCK TABLES, ALTER, INSERT' \
      'and SELECT. Compose names root here, which holds them globally. If this' \
      'account was created by hand, grant it those on this schema. Note that the' \
      'APPLICATION account is not a usable substitute: it is deliberately' \
      'narrowed to SELECT, INSERT, UPDATE and DELETE by the least-privilege init' \
      'script in harness/Dockerfile.mariadb, and GATE 1 refuses it by name.'
  fi

  # Split the comma-separated list without disturbing the global IFS, which is
  # deliberately $'\n\t'.
  local -a held=()
  local name
  while IFS= read -r name || [[ -n "$name" ]]; do
    [[ -n "$name" ]] || continue
    held+=("$name")
  done < <(printf '%s\n' "$granted" | tr ',' '\n')

  local -a absent=()
  local needed
  for needed in "${ACAS_RESET_REQUIRED_PRIVILEGES[@]}"; do
    if ! acas_in_list "$needed" "${held[@]}"; then
      absent+=("$needed")
    fi
  done

  if (( ${#absent[@]} )); then
    acas_die "$EX_PRIVILEGE" \
      "the account '${ACAS_RESET_DB_USER}' is MISSING the privilege(s): $(acas_join_words "${absent[@]}")." \
      "Applying $ACAS_RESET_SCHEMA_RELPATH needs all of:" \
      "  $(acas_join_words "${ACAS_RESET_REQUIRED_PRIVILEGES[@]}")" \
      'DROP and CREATE for its 33 drop/create pairs, LOCK TABLES and INSERT for' \
      'its 33 "LOCK TABLES ... WRITE" data sections, ALTER for the' \
      'version-guarded DISABLE/ENABLE KEYS directives, SELECT for the' \
      'verification queries.' \
      "Held: ${granted}" \
      'Reported here rather than letting the client fail part-way through the' \
      'file, which would leave a half-applied schema and poison every diff.'
  fi

  acas_ok "all $(acas_join_words "${ACAS_RESET_REQUIRED_PRIVILEGES[@]}") held by the admin account"
}


# This one command is the entire drop-and-recreate.

# Classify whatever the client wrote while applying the frozen schema. A clean
# apply is USUALLY silent, but not always, and the difference matters.
acas_report_client_output() {
  local out="$1"
  [[ -n "$out" ]] || return 0

  local line advisories=0 other=0
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    # The client's own TLS advisory: about the CONNECTION, never about the
    # schema.
    if [[ "$line" == *'ssl-verify-server-cert'* ]]; then
      advisories=$(( advisories + 1 ))
      acas_note "client TLS advisory (about the connection, not the schema): $line"
      continue
    fi
    other=$(( other + 1 ))
    acas_warn "the client emitted output while applying the frozen schema: $line"
  done <<<"$out"

  if (( advisories && ! other )); then
    acas_note 'the client said nothing about the schema itself'
  fi
}

# THE DISPOSABILITY GATE -- the guard that stands between this script and
# somebody else's database.

# The acknowledgement must equal `user@host:port/schema' for THIS invocation.
# THE ONE PLACE THE TARGET IS STILL NAMED, AND WHY (finding F-39)
#
# Everything a run RETAINS as evidence prints acas_target_description instead of a
# topology triple. This function is the exception, and it is deliberate: the
# destructive acknowledgement is matched against this EXACT string
# (see acas_target_acknowledged), so a refusal that would not print it would be a
# refusal an operator cannot satisfy without reading this source -- a safety gate
# nobody can pass is a safety gate that gets bypassed another way. Its two callers
# are therefore both TERMINAL: the usage error for a malformed
# --acknowledge-destructive, and acas_refuse_target. Neither runs on a successful
# reset, so no retained transcript of a completed run contains this string.
#
# Anything that logs on the success path must call acas_target_description.
acas_reset_target_label() {
  local user="${ACAS_RESET_DB_USER:-${ACAS_DB_ADMIN_USER:-${ACAS_DB_USER:-<unset>}}}"
  printf '%s@%s:%s/%s' \
    "$user" \
    "${ACAS_DB_HOST:-<unset>}" \
    "${ACAS_DB_PORT:-<unset>}" \
    "${ACAS_DB_NAME:-<unset>}"
}

acas_target_acknowledged() {
  # The flag wins over the environment, so a deliberate command line is never
  # silently overridden by something left in the shell.
  local supplied="${ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE-}"
  if [[ -n "${ACAS_RESET_ACKNOWLEDGE-}" ]]; then
    supplied="$ACAS_RESET_ACKNOWLEDGE"
  fi
  [[ -n "$supplied" ]] || return 1
  [[ "$supplied" == "$(acas_reset_target_label)" ]]
}

acas_refuse_target() {
  local headline="$1"
  shift
  acas_die "$EX_TARGET" \
    "$headline" \
    "$@" \
    '' \
    'This script streams 33 DROP TABLE + 33 CREATE TABLE pairs. It will not do' \
    'that to a database it cannot prove is a harness-owned throwaway.' \
    '' \
    'If this target really is disposable, say so explicitly and name it exactly:' \
    "    ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE='$(acas_reset_target_label)'" \
    "  or: --acknowledge-destructive '$(acas_reset_target_label)'" \
    'The acknowledgement is matched against this exact target, so it cannot be' \
    'left in an environment and later authorise a different database.'
}

acas_assert_disposable_static() {
  acas_stage 'Preconditions 2/9: the target is a harness-owned disposable database'

  acas_assert_sql_identifier 'ACAS_DB_NAME' "$ACAS_DB_NAME"

  local acknowledged=0
  if acas_target_acknowledged; then
    acknowledged=1
  fi

  if [[ "$ACAS_DB_NAME" != "$ACAS_RESET_REQUIRED_SCHEMA" ]]; then
    if (( ! acknowledged )); then
      acas_refuse_target \
        "ACAS_DB_NAME does not name '$ACAS_RESET_REQUIRED_SCHEMA'; the configured" \
        "value is not printed (F-39) -- it is $(acas_target_description)." \
        "The frozen $ACAS_RESET_SCHEMA_RELPATH defines exactly one database, and" \
        "this script can only apply that file. A schema named anything else is" \
        'not the database this harness owns.'
    fi
    acas_warn "acknowledged: resetting $(acas_target_description) rather than $ACAS_RESET_REQUIRED_SCHEMA."
  fi

  if ! acas_in_list "$ACAS_DB_HOST" "${ACAS_RESET_CANONICAL_HOSTS[@]}"; then
    if (( ! acknowledged )); then
      acas_refuse_target \
        "ACAS_DB_HOST is not a host this harness provisions; the configured value" \
        "is not printed (F-39) -- the target is $(acas_target_description)." \
        "Canonical hosts: $(acas_join_words "${ACAS_RESET_CANONICAL_HOSTS[@]}")." \
        'The first is the harness/docker-compose.yml service name; the others' \
        'reach a container published on this machine. A remote host is exactly' \
        'the case that must not be destroyed by accident.'
    fi
    acas_warn "acknowledged: resetting on a non-canonical host: $(acas_target_description)."
  fi

  if (( acknowledged )); then
    ACAS_RESET_ACK_USED=1
    acas_note "the destructive acknowledgement names this exact target: $(acas_target_description)"
  fi

  acas_log "target         = $(acas_target_description)"
  acas_log "required schema= $ACAS_RESET_REQUIRED_SCHEMA (a constant of this script, not of the deployment)"
  acas_log "schema matches = $( [[ "$ACAS_DB_NAME" == "$ACAS_RESET_REQUIRED_SCHEMA" ]] && printf 'yes' || printf 'no (acknowledged)' )"
  acas_log "host canonical = $( acas_in_list "$ACAS_DB_HOST" "${ACAS_RESET_CANONICAL_HOSTS[@]}" && printf 'yes' || printf 'no (acknowledged)' )"
  acas_check 'PASS' 'target identity accepted before any database contact'
}

acas_assert_disposable_server() {
  acas_stage 'Preconditions 7/9: server-side proof of disposability'

  local acknowledged=0
  if acas_target_acknowledged; then
    acknowledged=1
  fi

  # 3. THE DISPOSABILITY MARKER. A SERVER SETTING declared by
  # harness/Dockerfile.mariadb, readable back with one query, and present on no
  # server this harness did not build. NOT a table and NOT a schema: rule R-3
  # admits no added DDL, and a reset gate that required some made the violation
  # load-bearing (finding F-43).
  local marker='' rc=0
  acas_sql_value "select @@${ACAS_RESET_DISPOSABLE_VARIABLE}" || rc=$?
  if (( rc == 0 )); then
    marker="$ACAS_SQL_OUT"
  fi

  if (( rc != 0 )) || [[ "$marker" != "$ACAS_RESET_DISPOSABLE_MARKER"* ]]; then
    if (( ! acknowledged )); then
      acas_refuse_target \
        "this server does not declare itself a harness-owned disposable target." \
        "  variable: @@${ACAS_RESET_DISPOSABLE_VARIABLE}" \
        "  expected: ${ACAS_RESET_DISPOSABLE_MARKER}..." \
        "  found:    ${marker:-<query failed>}" \
        'That declaration is written into the server configuration by' \
        'harness/Dockerfile.mariadb and exists only on a server started from an' \
        'image this harness built, so its ABSENCE means this is not the' \
        'harness'"'"'s throwaway server. Start the harness service instead:' \
        '    docker compose -f harness/docker-compose.yml up -d mariadb' \
        'If this IS a disposable target that predates the marker, rebuild the' \
        'image rather than acknowledging past the gate:' \
        '    docker compose -f harness/docker-compose.yml build mariadb'
    fi
    acas_warn 'acknowledged: this server does not declare itself a harness-owned disposable target.'
  else
    acas_ok "disposability declared by the server: @@${ACAS_RESET_DISPOSABLE_VARIABLE} = ${ACAS_RESET_DISPOSABLE_MARKER}"
  fi

  # The server family, recorded rather than enforced.
  local version=''
  if acas_sql_value 'select @@version'; then
    version="$ACAS_SQL_OUT"
    acas_log "server version = $version  (schema produced by 10.11.7-MariaDB [mysql/ACASDB.sql:L1])"
    case "$version" in
      10.11.*) : ;;
      *) acas_warn "the server reports $version; the frozen schema was produced by 10.11.7-MariaDB [mysql/ACASDB.sql:L1]. Parity evidence from a different family is not comparable." ;;
    esac
  fi

  # 4. NOTHING BUT THE FROZEN TABLES.
  local -a expected=()
  mapfile -t expected < <(acas_expected_table_names)

  local -a unexpected=()
  local name
  if acas_sql_scalar "select TABLE_NAME from information_schema.TABLES where TABLE_SCHEMA = $(acas_sql_quote "$ACAS_DB_NAME") order by TABLE_NAME"; then
    while IFS= read -r name; do
      [[ -n "$name" ]] || continue
      acas_in_list "$name" "${expected[@]}" || unexpected+=("$name")
    done <<<"$ACAS_SQL_OUT"
  fi

  if (( ${#unexpected[@]} )); then
    if (( ! acknowledged )); then
      acas_refuse_target \
        "the target holds ${#unexpected[@]} table(s) the frozen schema does not define." \
        "  unexpected: $(acas_join_words "${unexpected[@]}")" \
        'The frozen dump defines 33 tables and drops exactly those. A table' \
        'outside that set means this schema is shared with something else, and' \
        'that something else is about to lose the schema around it.'
    fi
    acas_warn "acknowledged: the target holds ${#unexpected[@]} table(s) outside the frozen 33."
  else
    acas_ok "no table outside the frozen ${ACAS_RESET_EXPECT_TABLES} is present"
  fi

  acas_check 'PASS' 'server-side disposability proof accepted'
}

acas_apply_schema() {
  [[ "$ACAS_DB_NAME" == "$ACAS_RESET_REQUIRED_SCHEMA" ]] || acas_target_acknowledged \
    || acas_refuse_target \
      "reached the apply with ACAS_DB_NAME='$ACAS_DB_NAME' and no acknowledgement." \
      'This is unreachable unless a stage was reordered; refusing regardless.'

  acas_stage "Stage 1/4: apply $ACAS_RESET_SCHEMA_RELPATH verbatim to ${ACAS_DB_NAME}"

  # THE LAST GATE, re-asserted at the point of no return. The three destructive
  # gates already passed in acas_assert_environment, before any connection.
  if (( ! ACAS_RESET_TARGET_AUTHORISED )); then
    acas_die "$EX_PRECONDITION" \
      'REFUSED: the destructive-target gates were never satisfied, yet the apply' \
      'stage was reached. This branch is unreachable by any current path -- see' \
      'THE DESTRUCTIVE-TARGET POLICY near the top of this file -- so reaching it' \
      'means a code path now skips acas_authorise_destructive_target. Nothing has' \
      'been dropped.'
  fi

  acas_note 'the frozen file supplies its own DROP TABLE IF EXISTS statements, so this'
  acas_note 'stage emits no DDL of its own and drops nothing by hand (R-3)'

  local -a argv=()
  acas_build_sql_argv "$ACAS_SQL_CLIENT" "$ACAS_SQL_TLS_FLAG" "$ACAS_TIMEOUT_APPLY"
  argv=("${ACAS_SQL_ARGV[@]}")

  # Errexit is suspended for exactly the length of this call so the failure can
  # be reported with the client's own words instead of a bare line number.
  local out rc=0 started elapsed
  started="$SECONDS"
  out="$(MYSQL_PWD="$ACAS_RESET_DB_PASSWORD" "${argv[@]}" <"$ACAS_RESET_SCHEMA" 2>&1)" || rc=$?
  elapsed=$(( SECONDS - started ))

  # A deadline expiry is separated from a rejected statement BEFORE the generic
  # failure below, and it is separated here rather than left to the caller
  # because the two demand opposite responses.
  if acas_is_timeout_status "$rc" "$elapsed" "$ACAS_TIMEOUT_APPLY"; then
    ACAS_RESET_APPLIED=1
    acas_die "$EX_TIMEOUT" \
      "applying $ACAS_RESET_SCHEMA_RELPATH exceeded its ${ACAS_TIMEOUT_APPLY}s deadline (status $rc after ${elapsed}s)." \
      'The schema is PARTIALLY applied: the client was killed part-way through' \
      'the 33 DROP/CREATE pairs, so the database now holds neither the previous' \
      'state nor a complete schema. DO NOT dump or diff from it -- run this' \
      'script again to completion first.' \
      'Raise ACAS_TIMEOUT_APPLY if the server is simply slow; investigate the' \
      'server if it is not. This is NOT a rejected statement -- no statement was' \
      'refused, the client ran out of time.' \
      "Client said: ${out:-<no output>}"
  fi

  if (( rc != 0 )); then
    # The apply is attempted exactly ONCE.
    ACAS_RESET_APPLIED=1   # partially, which is worse than not at all: say so
    acas_die "$EX_APPLY" \
      "the client REJECTED part of $ACAS_RESET_SCHEMA_RELPATH (status $rc); the schema is PARTIALLY applied." \
      'No retry is attempted: re-running the file against a half-applied schema' \
      'would compound the damage. Fix the cause and run this script again.' \
      '--force is deliberately not used, so nothing was skipped silently.' \
      "Client said: ${out:-<no output>}"
  fi

  ACAS_RESET_APPLIED=1

  # Anything the client said is surfaced rather than swallowed -- this is the
  # only chance to notice a server-side warning about the frozen schema.
  acas_report_client_output "$out"

  acas_ok "applied verbatim: 33 DROP TABLE IF EXISTS + 33 CREATE TABLE, from the frozen file"
  acas_check 'PASS' "frozen schema applied verbatim ($ACAS_RESET_SCHEMA_RELPATH)"
}

# Eight checks, all read-only, all cheap, and every one of them protects every
# downstream diff. They are mandatory rather than optional for a specific
# reason.

# All 33 expected table names: the 22 in scope plus the 11 out of scope.
acas_expected_table_names() {
  acas_inscope_table_names
  local name
  for name in "${ACAS_RESET_OUT_OF_SCOPE[@]}"; do
    printf '%s\n' "$name"
  done
}

# Check 1 of 8 -- the 33 tables exist, and they are exactly the expected 33.
acas_verify_table_set() {
  acas_sql_value_or_die \
    "select count(*) from information_schema.TABLES where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL}" \
    'the table count'
  local count="$ACAS_SQL_OUT"

  if [[ "$count" != "$ACAS_RESET_EXPECT_TABLES" ]]; then
    acas_die "$EX_VERIFY" \
      "expected $ACAS_RESET_EXPECT_TABLES tables in ${ACAS_DB_NAME} after the apply, found $count." \
      'The frozen file defines exactly 33; if fewer came back, the apply did not' \
      'complete, and if more did, something outside the frozen schema created' \
      'them. Either way no diff taken from this state can be trusted.'
  fi

  local rc=0
  acas_sql_scalar \
    "select TABLE_NAME from information_schema.TABLES where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL} order by TABLE_NAME" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not list the tables after the apply.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"

  local -a present=() expected=() unexpected=() missing=()
  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    present+=("$line")
  done <<<"$ACAS_SQL_OUT"
  mapfile -t expected < <(acas_expected_table_names)

  local name
  for name in "${present[@]}"; do
    acas_in_list "$name" "${expected[@]}" || unexpected+=("$name")
  done
  for name in "${expected[@]}"; do
    acas_in_list "$name" "${present[@]}" || missing+=("$name")
  done

  if (( ${#unexpected[@]} || ${#missing[@]} )); then
    acas_die "$EX_VERIFY" \
      "the tables in ${ACAS_DB_NAME} are not the 33 the frozen schema defines." \
      "missing    : $(acas_list_or_none "${missing[@]}")" \
      "unexpected : $(acas_list_or_none "${unexpected[@]}")" \
      'The reset must leave exactly the frozen set: 22 in-scope tables plus 11' \
      'out-of-scope ones.'
  fi

  acas_ok "$count tables present, exactly the frozen set (22 in scope + 11 out of scope)"
  acas_check 'PASS' "$count tables recreated"
}

# Check 2 of 8 -- every table is EMPTY, before the seed puts anything in it.
acas_verify_all_empty() {
  local -a tables=()
  mapfile -t tables < <(acas_expected_table_names)

  # Each name reaches SQL in TWO syntactic positions -- a string literal and a
  # quoted identifier -- so each is composed through the primitive for its own
  # position rather than by hand.
  local sql='' name
  for name in "${tables[@]}"; do
    acas_assert_table_name 'a frozen table name' "$name"
    sql+="select $(acas_sql_quote "$name"), count(*) from $(acas_sql_quote_ident "$name");"
  done

  local rc=0
  acas_sql_scalar "$sql" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not count the rows of the recreated tables.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"

  local -a populated=()
  local table rows seen=0
  while IFS=$'\t' read -r table rows; do
    [[ -n "$table" ]] || continue
    seen=$(( seen + 1 ))
    if [[ "$rows" != '0' ]]; then
      populated+=("$table=$rows")
    fi
  done <<<"$ACAS_SQL_OUT"

  if (( seen != ACAS_RESET_EXPECT_TABLES )); then
    acas_die "$EX_VERIFY" \
      "expected a row count for each of the $ACAS_RESET_EXPECT_TABLES tables, got $seen." \
      "Received: ${ACAS_SQL_OUT:-<empty>}"
  fi

  if (( ${#populated[@]} )); then
    acas_die "$EX_VERIFY" \
      "the frozen schema was applied but $(( ${#populated[@]} )) table(s) are NOT empty." \
      "non-empty: $(acas_join_words "${populated[@]}")" \
      'Each CREATE TABLE is preceded by its own DROP TABLE IF EXISTS' \
      '[mysql/ACASDB.sql:L28], so a surviving row means the drop did not take' \
      'effect -- and the re-seed would then add to old data instead of replacing' \
      'it, which is precisely the silent corruption stage 5 exists to prevent.'
  fi

  acas_ok "all $seen tables are empty"
  acas_check 'PASS' "all $seen tables empty before the seed"
}

# Check 3 of 8 -- no secondary index on any of the 22 in-scope tables.
acas_verify_no_secondary_indexes() {
  local rc=0
  acas_sql_scalar \
    "select distinct TABLE_NAME, INDEX_NAME from information_schema.STATISTICS where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL} and INDEX_NAME <> 'PRIMARY' order by TABLE_NAME, INDEX_NAME" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not list the indexes after the apply.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"

  local -a offenders=() allowed_seen=()
  local table index
  while IFS=$'\t' read -r table index; do
    [[ -n "$table" ]] || continue
    if acas_in_list "$table" "${ACAS_RESET_SECONDARY_INDEX_ALLOWED[@]}"; then
      allowed_seen+=("$table.$index")
      continue
    fi
    offenders+=("$table.$index")
  done <<<"$ACAS_SQL_OUT"

  if (( ${#offenders[@]} )); then
    acas_die "$EX_VERIFY" \
      "an index outside the frozen schema exists: $(acas_join_words "${offenders[@]}")." \
      'The frozen schema contains ZERO CREATE INDEX statements and R-3 forbids' \
      'adding one. The 22 in-scope tables carry PRIMARY and nothing else, which' \
      'is what lets harness/dump_tables.py order by the primary key alone and' \
      'still produce a deterministic dump.' \
      "The only permitted non-primary indexes belong to $(acas_join_words "${ACAS_RESET_SECONDARY_INDEX_ALLOWED[@]}"), both out of scope."
  fi

  acas_ok "no secondary index on any of the 22 in-scope tables (out of scope, as frozen: $(acas_join_words "${allowed_seen[@]}"))"
  acas_check 'PASS' 'no secondary index on the 22 in-scope tables'
}

# Check 4 of 8 -- the frozen collation survived the apply.
acas_verify_collation() {
  local rc=0
  acas_sql_scalar \
    "select TABLE_NAME, TABLE_COLLATION from information_schema.TABLES where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL} and TABLE_COLLATION <> $(acas_sql_quote_literal "$ACAS_RESET_COLLATION") order by TABLE_NAME" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not read the table collations after the apply.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"

  local -a wrong=()
  local table collation
  while IFS=$'\t' read -r table collation; do
    [[ -n "$table" ]] || continue
    wrong+=("$table=$collation")
  done <<<"$ACAS_SQL_OUT"

  if (( ${#wrong[@]} )); then
    acas_die "$EX_VERIFY" \
      "$(( ${#wrong[@]} )) table(s) did not come back as ${ACAS_RESET_COLLATION}." \
      "$(acas_join_words "${wrong[@]}")" \
      'All 33 tables in the frozen dump declare' \
      '"DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci" while its header sets' \
      'SET NAMES utf8mb4 [mysql/ACASDB.sql:L16]. That inconsistency is frozen' \
      'state, flagged by the maintainer himself at [mysql/ACASDB.sql:L9-L11], and' \
      'it must NOT be harmonised (R-4). A utf8mb4 reading here means the file was' \
      'transformed on its way in -- by a sed, an iconv, an edited copy or a' \
      '--default-character-set override. Apply it byte-for-byte instead.'
  fi

  acas_ok "all 33 tables came back ${ACAS_RESET_COLLATION}; the charset caveat is preserved, not fixed"
  acas_check 'PASS' "collation ${ACAS_RESET_COLLATION} intact on all 33 tables"
}

# Check 5 of 8 -- the SHAPE of all 22 in-scope tables.
acas_verify_shapes() {
  local rc=0
  acas_sql_scalar \
    "select TABLE_NAME, count(*) from information_schema.COLUMNS where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL} group by TABLE_NAME order by TABLE_NAME" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not read the column counts after the apply.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"

  local -A columns_of=()
  local table value
  while IFS=$'\t' read -r table value; do
    [[ -n "$table" ]] || continue
    columns_of["$table"]="$value"
  done <<<"$ACAS_SQL_OUT"

  rc=0
  acas_sql_scalar \
    "select TABLE_NAME, group_concat(COLUMN_NAME order by SEQ_IN_INDEX separator ',') from information_schema.STATISTICS where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL} and INDEX_NAME = 'PRIMARY' group by TABLE_NAME order by TABLE_NAME" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not read the primary keys after the apply.' \
    "$(acas_diag_summary "$ACAS_SQL_DIAG")"

  local -A pk_of=()
  while IFS=$'\t' read -r table value; do
    [[ -n "$table" ]] || continue
    pk_of["$table"]="$value"
  done <<<"$ACAS_SQL_OUT"

  local -a faults=()
  local entry
  for entry in "${ACAS_RESET_INSCOPE[@]}"; do
    acas_split_table_entry "$entry"
    if [[ "${columns_of[$ACAS_T_TABLE]-}" != "$ACAS_T_COLUMNS" ]]; then
      faults+=("$ACAS_T_TABLE: expected $ACAS_T_COLUMNS columns, found ${columns_of[$ACAS_T_TABLE]-<absent>}")
    fi
    if [[ "${pk_of[$ACAS_T_TABLE]-}" != "$ACAS_T_PK" ]]; then
      faults+=("$ACAS_T_TABLE: expected primary key ($ACAS_T_PK), found (${pk_of[$ACAS_T_TABLE]-<absent>})")
    fi
  done

  # The width drift the dump normaliser exists to canonicalise.
  acas_sql_value_or_die \
    "select COLUMN_TYPE from information_schema.COLUMNS where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL} and TABLE_NAME = 'GLLEDGER-REC' and COLUMN_NAME = 'LEDGER-NAME'" \
    'the LEDGER-NAME column type'
  if [[ "$ACAS_SQL_OUT" != 'char(32)' ]]; then
    faults+=("GLLEDGER-REC.LEDGER-NAME: expected char(32), found ${ACAS_SQL_OUT:-<absent>}")
  fi

  if (( ${#faults[@]} )); then
    local fault
    printf 'FATAL: the recreated tables do not match the shape the frozen schema declares.\n' >&2
    for fault in "${faults[@]}"; do
      printf '       %s\n' "$fault" >&2
      acas_tee "       $fault"
    done
    acas_die "$EX_VERIFY" \
      "$(( ${#faults[@]} )) shape fault(s) after applying $ACAS_RESET_SCHEMA_RELPATH." \
      'Every count and key above is read out of the frozen schema itself. A' \
      'mismatch means the file was modified or the apply did not complete.'
  fi

  acas_ok "all 22 in-scope tables match their frozen column count and primary key"
  acas_ok 'GLLEDGER-REC.LEDGER-NAME is char(32) -- the 24-to-32 width drift the dump normaliser canonicalises'
  acas_check 'PASS' 'all 22 in-scope table shapes match the frozen schema'
}

# Check 6 of 8 -- every column is NOT NULL.
acas_verify_not_null() {
  acas_sql_value_or_die \
    "select count(*) from information_schema.COLUMNS where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL} and IS_NULLABLE = 'YES'" \
    'the nullable column count'
  if [[ "$ACAS_SQL_OUT" != '0' ]]; then
    acas_die "$EX_VERIFY" \
      "$ACAS_SQL_OUT column(s) are nullable; the frozen schema declares every column NOT NULL." \
      'Each bridge load paragraph initialises its host-variable group before a' \
      'write, so an unset field becomes zero or space rather than SQL NULL. A' \
      'nullable column means the schema has drifted from the frozen definition.'
  fi
  acas_ok 'every column is NOT NULL, as the frozen schema declares'
  acas_check 'PASS' 'zero nullable columns'
}

# Check 7 of 8 -- no binary floating-point column anywhere (R-2). The
# structural half of "zero binary floating point in accounting computation".
acas_verify_no_float() {
  acas_sql_value_or_die \
    "select count(*) from information_schema.COLUMNS where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL} and DATA_TYPE in ('float', 'double', 'real')" \
    'the floating-point column count'
  if [[ "$ACAS_SQL_OUT" != '0' ]]; then
    acas_die "$EX_VERIFY" \
      "$ACAS_SQL_OUT column(s) use a binary floating-point type." \
      'R-2 is absolute: no accounting value may pass through binary floating' \
      'point, in computation, in storage or in transport. The frozen schema' \
      'contains zero FLOAT, DOUBLE or REAL columns -- its numeric types are' \
      'DECIMAL and the integer family -- so a float here is a schema change.'
  fi
  acas_ok 'zero FLOAT / DOUBLE / REAL columns -- accounting values cannot traverse a float (R-2)'
  acas_check 'PASS' 'zero binary floating-point columns'
}

acas_verify_reset_state() {
  acas_stage 'Stage 2/4: verify the reset state (8 checks)'

  acas_verify_table_set              # 1
  acas_verify_all_empty              # 2
  acas_verify_no_secondary_indexes   # 3
  acas_verify_collation              # 4
  acas_verify_shapes                 # 5
  acas_verify_not_null               # 6
  acas_verify_no_float               # 7

  # 8. Autocommit again, AFTER the apply. The frozen file changes six session
  # variables and restores them at the tail [mysql/ACASDB.sql:L13-L22].
  acas_assert_autocommit 'after the apply'
  acas_check 'PASS' 'autocommit still 1/1 after the apply'

  ACAS_RESET_VERIFIED=1
}

# STAGE 3 -- DURABILITY IN A FRESH SESSION
#
# Durability is the one property the whole comparison rests on. Two cases must not
# be conflated:
#   * DDL is durable in either autocommit mode -- InnoDB commits CREATE TABLE and
#     DROP TABLE implicitly -- so the schema apply this stage verifies survives a
#     fresh session, and this script never needs to change the mode for it.
#   * DML from the frozen COBOL is NOT durable INSIDE THE SEEDING WINDOW, because
#     the loaders and bridges reach no COMMIT. A re-seed run inside that window
#     therefore leaves nothing behind, which is why harness/seed.sh measures the
#     seeded row counts when the window closes and fails rather than reporting a
#     success the tables do not show. The defect itself is preserved as the frozen
#     code's own (R-4) and is never repaired by issuing the missing COMMIT.
#
# The schema property is not trusted; it is PROVED. A brand-new client process,
# hence a brand-new server session, re-counts the tables. If the apply had
# somehow landed inside an uncommitted transaction, the fresh session would see
# the OLD tables and this check would fail -- which is exactly the empirical
# verification the plan asks for.
# =============================================================================
acas_verify_durability() {
  acas_stage 'Stage 3/4: durability -- re-count in a FRESH session'

  acas_sql_value_or_die \
    "select count(*) from information_schema.TABLES where TABLE_SCHEMA = ${ACAS_RESET_SCHEMA_LITERAL}" \
    'the table count in a fresh session'

  if [[ "$ACAS_SQL_OUT" != "$ACAS_RESET_EXPECT_TABLES" ]]; then
    acas_die "$EX_VERIFY" \
      "a fresh session sees $ACAS_SQL_OUT tables, not $ACAS_RESET_EXPECT_TABLES." \
      'The apply was therefore not durable, so nothing downstream can rely on it.' \
      'Note what is NOT the fix: changing the autocommit mode from this script' \
      'would create a second authority and is forbidden (R-3, R-4). InnoDB' \
      'commits CREATE TABLE and DROP TABLE implicitly in either mode, so a' \
      'failure here points at the server configuration, not at this script.'
  fi

  acas_ok "a fresh session sees all $ACAS_RESET_EXPECT_TABLES tables -- the DDL committed implicitly, as expected"
  acas_check 'PASS' 'schema durable in a fresh session'
}


# Delegated to harness/seed.sh, which reproduces the flat-file-to-loader
# contract of [common/masterLD.sh:L44-L115] and its exit-code semantics by
# driving the maintainer's own compiled `common/*LD.cbl` programs.
acas_reseed() {
  if (( ACAS_RESET_SCHEMA_ONLY )); then
    acas_stage 'Stage 4/4: re-seed -- SKIPPED by --schema-only'
    acas_note 'the database now holds 33 EMPTY tables'
    acas_warn '--schema-only leaves an UNSEEDED database: the full stage-5 contract is schema PLUS seed, so a dump taken now is not comparable with one taken after the COBOL cycle'
    return 0
  fi

  acas_stage "Stage 4/4: re-seed via $ACAS_RESET_SEED_SCRIPT"

  acas_compose_seed_argv
  local -a argv=("${ACAS_RESET_SEED_ARGV[@]}")

  acas_log "running: $(acas_join_words "${argv[@]}")"
  acas_note 'it drives the compiled load programs as external processes only (R-1)'

  acas_deadline_prefix "$ACAS_TIMEOUT_SEED"
  local rc=0 started elapsed
  started="$SECONDS"
  "${ACAS_DEADLINE_ARGV[@]}" "${argv[@]}" || rc=$?
  elapsed=$(( SECONDS - started ))
  ACAS_RESET_SEED_RC="$rc"

  # Checked BEFORE the classification below, because "never finished" is not
  # one of the frozen load-program return codes and must not be reported as
  # one.
  acas_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_SEED" \
    'ACAS_TIMEOUT_SEED' "the re-seed via $ACAS_RESET_SEED_SCRIPT"

  if (( rc != 0 )); then
    acas_check 'FAIL' "re-seed failed, $ACAS_RESET_SEED_SCRIPT exited $rc"
    acas_seed_report
    acas_die "$rc" \
      "$ACAS_RESET_SEED_SCRIPT exited $rc; the reset is NOT complete." \
      'The frozen schema was applied and verified, so the database holds the 33' \
      'empty tables and NO seed data. That is a valid schema and an invalid' \
      'premise for a state diff.' \
      'DO NOT take a diff from this state. seed.sh reports 70 usage, 71' \
      'precondition, 72 database, 73 autocommit, 74 timeout, 75 scenario fixture' \
      'for its own failures, and' \
      'otherwise propagates a load program return code: 128 params not set up,' \
      '64 RDB not set up, 16 rdb write error [common/masterLD.sh:L37-L39].' \
      'Its own diagnostics are above, and its log is in the seed subdirectory' \
      'of the ACAS_OUT area.'
  fi

  acas_ok "$ACAS_RESET_SEED_SCRIPT completed cleanly"
  acas_check 'PASS' 're-seeded via harness/seed.sh (exit 0)'

  acas_assert_reseed_used_fixture
}

# The other half of the scenario-binding fix. harness/seed.sh stages the
# scenario's declared seed files into a scenario-owned fixture directory and
# leaves a marker behind [harness/seed.sh, ACAS_FIXTURE_MARKER].
acas_assert_reseed_used_fixture() {
  [[ -n "$ACAS_RESET_SCENARIO" ]] || return 0

  local stem marker
  stem="${ACAS_RESET_SCENARIO##*/}"
  stem="${stem%.*}"

  # ⭐ NO DATA DIRECTORY IS A REFUSAL, NOT A WARNING (finding F-46). This used to
  # warn and return SUCCESS, so a reset that could not prove which fixture the
  # re-seed drew from reported itself as bound to the scenario anyway -- and the two
  # cycles could then start from different premises with nothing saying so. A
  # scenario reset that cannot locate the fixture has not done what it claims.
  local base="${ACAS_RESET_DATA_DIR:-${ACAS_DATA:-}}"
  if [[ -z "$base" ]]; then
    acas_die "$EX_FIXTURE" \
      "cannot locate the scenario fixture for '$stem': neither --data-dir nor" \
      'ACAS_DATA is set, so the marker harness/seed.sh leaves cannot be read and' \
      'this reset cannot prove WHICH seed the two cycles are about to compare' \
      'from. Pass --data-dir, or set ACAS_DATA -- harness/docker-compose.yml sets' \
      'it to /data for the gnucobol service.'
  fi

  marker="$base/$stem/$ACAS_RESET_FIXTURE_MARKER"
  if [[ ! -f "$marker" ]]; then
    acas_die "$EX_FIXTURE" \
      "the re-seed did not leave a scenario fixture for '$stem'." \
      "  expected marker: $marker" \
      "harness/seed.sh writes that marker when it stages a scenario's declared" \
      'seed_files. Its absence means the re-seed did NOT draw from the scenario,' \
      'so the Python cycle would start from a different premise than the COBOL' \
      'cycle did and the resulting diff would be meaningless.' \
      'Check that the scenario file declares seed_files (or seed_dir) and that' \
      'those files exist.'
  fi

  # ⭐ THE MARKER'S EXACT SHAPE IS VALIDATED, NOT ITS EXISTENCE (finding F-22). A
  # file count alone cannot tell two fixtures apart: two scenarios with the same
  # number of files, or one fixture rebuilt from different records, produce the same
  # count and a different seeded state. The marker carries a `file<TAB>name<TAB>sha256'
  # row per staged file [harness/seed.sh], so this reads the whole of it, requires the
  # scenario name to match, requires the row count to equal the declared count, and
  # requires every digest to be a full SHA-256. Its own digest is then published as
  # ACAS_RESET_FIXTURE_DIGEST, which is what both runners bind into their run-status
  # records so the two sides can be proved to have started from the SAME BYTES.
  local recorded_scenario recorded_count row_count bad_digests
  # READ THROUGH A REDIRECTION, NOT AS AN AWK OPERAND -- see the note at the
  # matching gate in harness/seed.sh. mawk reads `--` as a filename, so the
  # `awk '...' -- "$file"` form these four lines used returned NOTHING and the gate
  # silently saw an empty marker.
  recorded_scenario="$(awk -F'\t' '$1 == "scenario" { print $2; exit }' < "$marker" 2>/dev/null || true)"
  recorded_count="$(awk -F'\t' '$1 == "files" { print $2; exit }' < "$marker" 2>/dev/null || true)"
  row_count="$(awk -F'\t' '$1 == "file" { n++ } END { print n + 0 }' < "$marker" 2>/dev/null || true)"
  bad_digests="$(awk -F'\t' '$1 == "file" && $3 !~ /^[0-9a-f]{64}$/ { print $2 }' < "$marker" 2>/dev/null || true)"

  if [[ "$recorded_scenario" != "$stem" ]]; then
    acas_die "$EX_FIXTURE" \
      "the fixture marker at $marker names scenario '${recorded_scenario:-<absent>}'," \
      "and this reset is for '$stem'. It belongs to a different scenario, so it" \
      'proves nothing about this one.'
  fi
  if [[ ! "$recorded_count" =~ ^[0-9]+$ ]] || (( recorded_count == 0 )); then
    acas_die "$EX_FIXTURE" \
      "the fixture marker at $marker records a file count of" \
      "'${recorded_count:-<absent>}', which is not a positive whole number." \
      'A fixture of no files cannot seed anything, and an unreadable count cannot' \
      'be checked against the rows below it.'
  fi
  if (( row_count != recorded_count )); then
    acas_die "$EX_FIXTURE" \
      "the fixture marker at $marker records $recorded_count file(s) but carries" \
      "$row_count digest row(s). The marker is incomplete or was written by an" \
      'interrupted stage, so the seed it describes cannot be identified.'
  fi
  if [[ -n "$bad_digests" ]]; then
    acas_die "$EX_FIXTURE" \
      "the fixture marker at $marker carries a row whose digest is not a" \
      'SHA-256:' "  $bad_digests" \
      'Every staged file must be identified by its full content digest; a row' \
      'without one cannot bind the two sides to the same bytes.'
  fi

  ACAS_RESET_FIXTURE_DIGEST="$(acas_file_sha256 "$marker")"
  acas_ok "re-seed used the '$stem' scenario fixture ($recorded_count declared file(s), every digest present)"
  acas_check 'PASS' "re-seed bound to scenario '$stem' ($recorded_count file(s), marker sha256 ${ACAS_RESET_FIXTURE_DIGEST:0:16}...)"
  acas_log "fixture marker = $marker"
  acas_log "fixture marker sha256 = ${ACAS_RESET_FIXTURE_DIGEST:-<unavailable>}"

  acas_publish_seed_identity "$stem" "$recorded_count"
}

# ⭐ THE EXACT SEED IDENTITY, PUBLISHED WHERE BOTH RUNNERS CAN BIND IT (finding F-22)
#
# The two runners each recorded a "seed fingerprint" that was a list of TABLE ROW
# COUNTS, and harness/diff_states.py compared those. Row counts are not an identity:
# two seedings with the same shape and DIFFERENT VALUES compare equal, so the two legs
# of a parity run could start from different money and the protocol would say the
# starting states matched. The one artifact that IS an identity already exists --
# harness/seed.sh stages a marker carrying a SHA-256 per seeded file -- and until now
# nothing bound it to anything.
#
# So this publishes the marker's own digest, once, where both runners read it:
#     <ACAS_OUT>/run-logs/<scenario>/seed-identity
# and each runner records it in its run-status record, and
# harness/dump_tables.py requires it, and harness/diff_states.py requires the two
# sides to carry the SAME one before it compares a single row.
#
# THE SECOND RESET OF ONE ATTEMPT MUST SEED THE SAME BYTES. Stage 1 seeds for the
# COBOL leg and stage 5 seeds for the Python leg, and the entire claim of the protocol
# is that both legs started from byte-for-byte the same state. So a second reset
# carrying the SAME run id and a DIFFERENT digest is refused here, where the refusal
# still costs nothing -- rather than discovered at the diff, where it would look like
# an accounting difference. A reset with a DIFFERENT run id is a different attempt and
# replaces the record freely.
acas_publish_seed_identity() {
  local stem="$1" files="$2"
  local dir="$ACAS_OUT/run-logs/$stem"
  local target="$dir/seed-identity"

  [[ -n "$ACAS_RESET_FIXTURE_DIGEST" ]] || return 0

  mkdir -p -- "$dir" 2>/dev/null || {
    acas_warn "the seed identity could not be published: $dir is not creatable." \
      'The capture stage will report the run as unattested, which is the safe direction.'
    return 0
  }
  chmod 700 -- "$dir" 2>/dev/null || true

  if [[ -f "$target" && ! -L "$target" && -n "$ACAS_RESET_RUN_ID" ]]; then
    local prior_run='' prior_digest='' key value
    while IFS=$'\t' read -r key value; do
      case "$key" in
        run_id)                prior_run="$value" ;;
        fixture_marker_sha256) prior_digest="$value" ;;
      esac
    done <"$target"
    if [[ "$prior_run" == "$ACAS_RESET_RUN_ID" && -n "$prior_digest" \
          && "$prior_digest" != "$ACAS_RESET_FIXTURE_DIGEST" ]]; then
      acas_die "$EX_FIXTURE" \
        'this attempt has already seeded a DIFFERENT fixture for this scenario.' \
        "  attempt        : $ACAS_RESET_RUN_ID" \
        "  already seeded : $prior_digest" \
        "  seeding now    : $ACAS_RESET_FIXTURE_DIGEST" \
        'The two legs of a parity run must start from byte-for-byte the same state --' \
        'that is the whole claim the empty diff is evidence for. Two different fixtures' \
        'within one attempt cannot support it, and the difference would surface at the' \
        'diff looking exactly like an accounting difference.' \
        'Rebuild the fixture once, then run the protocol from stage 1.'
    fi
  fi

  {
    printf 'scenario\t%s\n' "$stem"
    printf 'run_id\t%s\n' "$ACAS_RESET_RUN_ID"
    printf 'fixture_marker_sha256\t%s\n' "$ACAS_RESET_FIXTURE_DIGEST"
    printf 'files\t%s\n' "$files"
  } | acas_publish_atomic "$target" 'the seed identity' || {
    acas_warn 'the seed identity could not be published; the capture stage will report the run as unattested.'
    return 0
  }
  acas_log "seed identity  = $target"
  return 0
}

ACAS_RESET_REPORTED=0

acas_seed_report() {
  if (( ACAS_RESET_REPORTED )); then
    return 0
  fi
  ACAS_RESET_REPORTED=1

  acas_stage 'Summary'
  local row
  for row in "${ACAS_RESET_SUMMARY[@]}"; do
    printf '    %s\n' "$row"
    acas_tee "    $row"
  done

  acas_log ''
  acas_log "schema applied        : $( (( ACAS_RESET_APPLIED )) && printf 'yes' || printf 'no' )"
  acas_log "state verified        : $( (( ACAS_RESET_VERIFIED )) && printf 'yes' || printf 'no' )"
  acas_log "re-seed exit code     : ${ACAS_RESET_SEED_RC:-<not run>}"
  if [[ -n "$ACAS_RESET_SCENARIO" ]]; then
    acas_log "scenario              : $ACAS_RESET_SCENARIO (BINDING on the re-seed; fixture asserted)"
  fi

  # Recorded in the report, not merely in a warning, because a reset that
  # proceeded past the disposability gate on an operator's acknowledgement did
  # NOT satisfy the gate -- and evidence produced from it has to carry that.
  acas_log "target                : $(acas_target_description)"
  if (( ACAS_RESET_ACK_USED )); then
    acas_log "disposability         : OVERRIDDEN by an explicit acknowledgement"
    printf '\nNOTE: this reset proceeded under --acknowledge-destructive, so one or more\n'
    printf '      disposability proofs did not hold. See the findings above.\n'
  else
    acas_log 'disposability         : proved (canonical target, server marker present, consent token matched)'
  fi

  acas_log "run log               : ${ACAS_RESET_LOG:-<not opened>}"

  if (( ${#ACAS_RESET_WARN_SUMMARY[@]} )); then
    printf '\n--- %s non-fatal finding(s) reported during this run ---\n' \
      "${#ACAS_RESET_WARN_SUMMARY[@]}"
    local entry
    for entry in "${ACAS_RESET_WARN_SUMMARY[@]}"; do
      printf '    %s\n' "$entry"
      acas_tee "    finding: $entry"
    done
    printf -- '--- end of non-fatal findings ---\n'
  fi
}

# DRY RUN Prints exactly what a real run would do and touches nothing: no
# statement is issued, no lock is taken, no table is dropped.
acas_print_plan() {
  acas_stage 'Dry run: the plan'
  acas_note 'nothing is executed, no database statement is issued and no table is dropped'

  acas_log ''
  acas_log "1. apply, verbatim : $ACAS_RESET_SCHEMA"
  acas_log "   to database     : $(acas_target_description) (named explicitly on the client"
  acas_log '                     command line -- the frozen file has no USE statement)'
  acas_log '   as              : the ADMIN account, not the application account'
  acas_log "   client          : ${ACAS_SQL_CLIENT:-resolved at run time (mariadb, else mysql)}"
  acas_log '   how             : streamed on stdin, unfiltered -- no sed, no awk, no iconv,'
  acas_log '                     no local copy, no --default-character-set override, no --force'
  acas_log "   what does the dropping: the frozen file's own 33 DROP TABLE IF EXISTS statements"
  acas_log '                     [mysql/ACASDB.sql:L28]; this script emits no DDL (R-3)'

  acas_log ''
  acas_log '2. verify (8 read-only checks):'
  acas_log "   a. exactly $ACAS_RESET_EXPECT_TABLES tables, and exactly the frozen set"
  acas_log '   b. every table empty, by COUNT(*) -- not by the InnoDB row estimate'
  acas_log '   c. no secondary index on any of the 22 in-scope tables'
  acas_log "   d. all 33 tables still ${ACAS_RESET_COLLATION} (R-4: the charset caveat is not fixed)"
  acas_log '   e. all 22 in-scope column counts and primary keys, plus LEDGER-NAME char(32)'
  acas_log '   f. zero nullable columns'
  acas_log '   g. zero FLOAT / DOUBLE / REAL columns (R-2)'
  acas_log '   h. autocommit still 0/0 after the apply'

  acas_log ''
  acas_log '3. durability: re-count the tables in a FRESH session'

  acas_log ''
  if (( ACAS_RESET_SCHEMA_ONLY )); then
    acas_log '4. re-seed        : SKIPPED (--schema-only) -- the database would be left EMPTY'
    acas_log '   NOTE           : the full stage-5 contract is schema PLUS seed'
  else
    acas_compose_seed_argv
    acas_log "4. re-seed        : $(acas_join_words "${ACAS_RESET_SEED_ARGV[@]}")"
    acas_log '   its status is propagated verbatim (70..73 its own, else a loader rc)'
  fi

  acas_log ''
  acas_note 'the MariaDB readiness, autocommit and privilege assertions are NOT performed'
  acas_note 'in a dry run; a real run refuses to reset unless autocommit is ON, globally'
  acas_note 'and for the session -- the runtime mode, since a reset is runtime application'
  acas_note 'access and the Agent Action Plan scopes its OFF requirement to seeding'
  acas_note '(sections 0.2.1.1, 0.4.1.7 and 0.5.2, from [common/glbatchLD.cbl:L9-L13]).'
  acas_note 'harness/seed.sh owns that window. Inside it the frozen COBOL, which reaches'
  acas_note 'no COMMIT, leaves no durable rows -- reported as the reproduced legacy defect'
  acas_note '(R-4), never repaired, and measured by seed.sh rather than assumed'
}

# MAIN Strictly sequential (R-3). No stage is backgrounded and none is
# parallelised. Nothing here writes to $ACAS_REPO.
# ⭐ A DIAGNOSTIC RESET SAYS SO, ON EVERY EXIT PATH THAT SUCCEEDS. The gate above may
# be waived with --accept-transformed-oracle, and a run made under that waiver has set
# up a comparison against a REPAIRED specification. That is legitimate for diagnosis and
# is not a parity claim, so it is stated here rather than left in the operator's memory:
# every later stage reads this script's output to know what state it created.
acas_reset_disclose_diagnostic_oracle() {
  (( ACAS_RESET_ORACLE_IS_DIAGNOSTIC )) || return 0
  printf '\n'
  printf 'NO PARITY CLAIM: this reset was made with --accept-transformed-oracle, so the\n'
  printf 'compiled oracle was built from TRANSFORMED sources (%s file(s), transform-set\n' \
    "${ACAS_RESET_SOURCE_TRANSFORMS:-?}"
  printf 'digest %s). Rule R-6 makes the compiled program the behavioural\n' \
    "${ACAS_RESET_TRANSFORM_DIGEST:-<unrecorded>}"
  printf 'specification and rule R-4 requires its defects reproduced rather than repaired,\n'
  printf 'so an empty diff drawn against this oracle would say the migrated cycle matches\n'
  printf 'a PATCHED system. Use these captures for DIAGNOSIS only.\n'
}

acas_main() {
  acas_parse_args "$@"

  # FIRST, before anything can spawn an external command: resolve and freeze
  # every deadline.
  acas_resolve_deadlines

  printf 'harness/reset_db.sh -- stages 1 and 5 of the ten-stage parity protocol\n'
  printf '  seed -> run(COBOL) -> dump -> normalise -> RE-SEED -> run(Python) -> dump\n'
  printf '  -> normalise -> verify published -> diff\n'
  printf 'Drops and re-applies the FROZEN mysql/ACASDB.sql verbatim, then re-seeds, so the\n'
  printf 'Python cycle starts from byte-for-byte the state the COBOL cycle started from.\n'
  printf 'The drop lives in the frozen file itself, so this script emits no DDL (R-3).\n'

  acas_assert_environment
  acas_open_log

  #  THIS SCRIPT'S OWN DIRECTORY, so the seed-file pre-flight below can reach the
  #  shared scenario parser without a $PATH search or a guessed checkout layout.
  ACAS_RESET_HARNESS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
  readonly ACAS_RESET_HARNESS

  #  ⭐ THE ORACLE-PROVENANCE GATE RUNS BEFORE A SINGLE TABLE IS DROPPED (finding
  #  M-06 moved it here from the deleted driver; finding SEC-02 is why it exists).
  #  This script is stages 1 and 5: it destroys the database in order to set up a
  #  comparison. If the compiled specification cannot arbitrate that comparison there
  #  is nothing to set up, so the refusal belongs HERE, before the destruction --
  #  which is also what lets docs/migration/scenario-diff-evidence.md record the
  #  measured behaviour as "refused before stage 1, so no database was touched".
  acas_assert_oracle_attestation

  #  ⭐ AND SO DOES THE BYPASS REFUSAL, for the same reason: it decides WHICH TARGET
  #  this run is permitted to destroy, so it has to be settled before the two
  #  disposability checks it would otherwise be able to waive.
  acas_assert_no_evidence_bypass

  acas_assert_disposable_static

  acas_assert_scenario
  if [[ -n "$ACAS_RESET_SCENARIO" ]]; then
    acas_log "scenario = $ACAS_RESET_SCENARIO (forwarded verbatim to $ACAS_RESET_SEED_SCRIPT)"
  fi
  acas_assert_frozen_schema
  acas_assert_seed_script
  #  AFTER the fixture root has been resolved by acas_assert_scenario, and STILL before
  #  the drop: a fixture that was never built costs a wiped database if it is only
  #  discovered inside the re-seed.
  acas_assert_seed_files

  if (( ACAS_RESET_DRY_RUN )); then
    acas_print_plan
    printf '\nharness/reset_db.sh dry run complete: nothing was executed.\n'
    exit "$EX_OK"
  fi

  # The lock is taken only for a real run, and only after every cheap assertion
  # has passed, so a misconfigured invocation never blocks a correct one.
  acas_take_lock

  acas_wait_for_database

  acas_assert_disposable_server

  # The banner is raised HERE rather than inside acas_assert_autocommit, because
  # that function is deliberately dual-use: it runs once as this precondition and
  # once as check 8 of 8 after the apply, where a "Preconditions 8/9" banner
  # would be actively misleading. Raising it at the call site keeps the
  # precondition numbering complete AND makes the ERR/EXIT traps name the
  # autocommit gate -- not MariaDB readiness -- as the failing stage.
  acas_stage 'Preconditions 8/9: autocommit is ON (the runtime mode; the seeding window belongs to harness/seed.sh)'
  acas_assert_autocommit 'before the apply'

  acas_assert_privileges

  acas_apply_schema
  acas_verify_reset_state
  acas_verify_durability
  acas_reseed

  acas_seed_report

  # Exit 0 ONLY on a genuinely clean reset AND a clean re-seed.
  if (( ! ACAS_RESET_APPLIED || ! ACAS_RESET_VERIFIED )); then
    acas_die "$EX_VERIFY" \
      'the reset did not complete: the schema was not applied and verified.' \
      'This branch should be unreachable -- reaching it means a stage returned' \
      'without asserting. Do not take a diff from this state.'
  fi

  if (( ACAS_RESET_SCHEMA_ONLY )); then
    printf '\nharness/reset_db.sh completed: the frozen schema is applied and verified,\n'
    printf '%s empty tables, and the re-seed was SKIPPED by --schema-only.\n' \
      "$ACAS_RESET_EXPECT_TABLES"
    printf 'This state is NOT comparable with a dump taken after the COBOL cycle: run\n'
    printf 'without --schema-only for the full stage-5 contract.\n'
    acas_reset_disclose_diagnostic_oracle
    exit "$EX_OK"
  fi

  printf '\nharness/reset_db.sh completed: frozen schema re-applied verbatim, %s tables\n' \
    "$ACAS_RESET_EXPECT_TABLES"
  printf 'verified, and re-seeded. Both cycles now start from identical state.\n'
  printf 'Next: run the Python cycle, then harness/dump_tables.py.\n'
  acas_reset_disclose_diagnostic_oracle
  exit "$EX_OK"
}

acas_main "$@"
