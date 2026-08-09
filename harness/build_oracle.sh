#!/usr/bin/env bash
# harness/build_oracle.sh -- build the compiled-COBOL comparison ORACLE.
#
# Five steps, one exit code each (run `--help' for the options, the environment
# and the codes): unpack the vendored JC preSQL archive, compile the bridge's C
# interface object cobmysqlapi.o with the build rule recovered from that archive,
# install `presql2' on PATH, then run common/comp-common.sh and comp-all.sh
# UNMODIFIED. No cobc flag is changed, because default compiler arithmetic is
# what the migration's truncation and rounding behaviour depends on.
#
# Two invariants the code below rests on:
#   * $ACAS_REPO is READ and never written. presql2 truncates its output file
#     before it validates its parameters, so running it inside the checkout would
#     zero the 28 generated common/*MT.cbl bridges -- the authoritative
#     record-layout to table mapping. The tree is copied to $ACAS_BUILD instead.
#   * every frozen compile script ends in a bare, unconditional `exit 0'
#     ([common/comp-common.sh:L59], [comp-all.sh:L45]), so its status is not a
#     success signal and neither `set -e' nor `pipefail' can see a failed
#     compile. acas_scan_build_log and acas_assert_artifacts decide instead.
#     These are frozen defects: worked around here, never fixed (R-4).
#
# Locator notation: [path:Lnn] names a checkout file. [<archive>:member:Lnn]
# names a member of a vendored archive that is unpacked inside the container.

set -Eeuo pipefail

# A conservative IFS: word splitting on newlines and tabs only, so a path
# containing a space can never be split apart.
IFS=$'\n\t'

# Unmatched globs must expand to nothing rather than to the pattern text, so
# the artifact assertions report "no sources found" instead of a literal
# "*.cbl".
shopt -s nullglob

# 0077 by default: nothing this script writes is world- or group-readable.
umask 077

# ---------------------------------------------------------------------------
#  DROP THE ADMINISTRATIVE CREDENTIAL BEFORE ANYTHING IS SPAWNED
#
#  `harness/docker-compose.yml` puts ACAS_DB_ADMIN_USER / ACAS_DB_ADMIN_PASSWORD in
#  the `gnucobol` service environment because protocol stages 1 and 5 -- and only
#  those two, both `harness/reset_db.sh` -- drop and re-apply the frozen schema and
#  so need DDL rights. A service-wide variable is inherited by every descendant,
#  which put the database SUPERUSER password into the environment of the GnuCOBOL
#  compiler, the preSQL translator, every bridge and menu binary, the migrated
#  Python cycle and pytest itself.
#
#  THIS SCRIPT NEVER USES THAT PAIR -- it holds no reference to either name and
#  invokes neither reset_db.sh nor seed.sh -- so it removes them from its own
#  environment here, before the first child exists. Least privilege by
#  construction rather than by convention: a compile or a cycle run cannot reach
#  the credential even by accident, because it is not there to reach.
#
#  Application access is unaffected: ACAS_DB_USER / ACAS_DB_PASSWORD remain, and
#  that account holds SELECT, INSERT, UPDATE and DELETE on the one schema.
# ---------------------------------------------------------------------------
unset ACAS_DB_ADMIN_USER ACAS_DB_ADMIN_PASSWORD

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
readonly EX_TIMEOUT=78          # an external command exceeded its finite deadline
readonly EX_ARCHIVE=79          # vendored archive failed its digest or member audit

# The frozen recipe's hard-coded paths.
readonly ACAS_FROZEN_MYSQL_PREFIX='/usr/local/mysql'

readonly ACAS_REQUIRED_COBC_VERSION='3.2'

readonly ACAS_PRESQL2_SHA256_EXPECTED='638db9530d2fe008fbb46cf8600b9406f6f780c9fc59d0e0c94e868b4d615475'
readonly ACAS_PRESQL2_ARCHIVE_ROOT='presql2-package'

# =============================================================================
# THE FOUR MEMBER DIGESTS -- SO THAT A REUSED PACKAGE IS AS PROVABLE AS AN UNPACKED
# ONE
#
# WHAT THIS CLOSES. Step 1 verified the vendored archive's digest and then audited
# it member by member -- but ONLY on the branch that unpacks it. The other branch
# reuses an already-unpacked directory, and that branch is the DEFAULT: the image
# unpacks to /opt/presql2-package at build time, so an ordinary run never reached the
# digest check at all. `ACAS_PRESQL2_PACKAGE=DIR' then let any directory take its
# place. Between them, the two decided WHAT THE ORACLE IS -- step 2 compiles
# `cobmysqlapi38.c' from that directory and links the result into every bridge, and
# step 3 compiles `presql2.cbl' into the translator that generates every bridge's
# SQL -- with nothing verifying either file.
#
# So the four members every later step depends on carry their own pinned digests, and
# they are verified on BOTH branches. These are properties of the pinned archive
# above rather than independent choices: extract it and hash the members and you get
# exactly these. Replacing the archive means updating five constants, not one, and
# that is the point -- each one names a file whose content decides what gets built.
# =============================================================================
readonly ACAS_PRESQL2_MEMBER_DIGESTS=(
  'cobmysqlapi38.c:7c6055d90c96ae472ca9439eb94825743913d7f9d43fb79a15ef677f2fab01be'
  'cobmysqlapi38.sh:33dbc2558870ee3c672006fffc217505a59f2e331b5130035af988d03d39f6d6'
  'presql2.cbl:c42791cf4d9be038959280c4c8151e4eda268a3daf003e625d003f277263e986'
  'presql2.sh:976d2ed231eb5a57a7ac2363e5b57ce842355db9acf685da1cc4461dd615ba17'
)

# The provenance sidecar a pre-built cobmysqlapi.o must carry to be reused. A
# compiled object's digest is NOT reproducible -- it depends on the compiler, its
# flags and the host -- so it cannot be pinned, and pinning it would be a fiction.
# What CAN be established is the digest of the source it was compiled from, and
# whatever builds the object records it here. An object without this record is not
# reused: step 2 compiles its own from the source it has just verified, which is
# always available, so refusing costs one gcc invocation and buys a provable chain
# from the pinned archive to every linked bridge.
readonly ACAS_COBMYSQLAPI_PROVENANCE_SUFFIX='.source-sha256'

# Finite deadlines -- every external command this script spawns runs under one.
readonly ACAS_TIMEOUT_MAX=86400     # 24h -- an upper bound on any single budget
ACAS_TIMEOUT_GRACE="${ACAS_TIMEOUT_GRACE-}"               # resolved by acas_resolve_deadlines
ACAS_TIMEOUT_UNPACK="${ACAS_TIMEOUT_UNPACK-}"              # step 1: audit + extract the vendored zip
ACAS_TIMEOUT_COMPILE="${ACAS_TIMEOUT_COMPILE-}"             # a single gcc / cobc invocation
ACAS_TIMEOUT_BUILD="${ACAS_TIMEOUT_BUILD-}"               # a delegated frozen build script
ACAS_TIMEOUT_PROBE="${ACAS_TIMEOUT_PROBE-}"               # one database client probe attempt
ACAS_TIMEOUT_RESOLVED=''            # out-parameter of acas_timeout_seconds
declare -a ACAS_DEADLINE_ARGV=()    # populated by acas_deadline_prefix

# [comp-all.sh:L15-L32] cd's through exactly these six directories in this
# order.
readonly -a ACAS_COMPILE_DIRS=(common general irs purchase sales stock)

readonly -a ACAS_INSCOPE_LOADERS=(
  analLD dfltLD finalLD glbatchLD glpostingLD irsdfltLD irsfinalLD
  irsnominalLD irspostingLD nominalLD otm3LD otm5LD plinvoiceLD purchLD
  salesLD slinvoiceLD slpostingLD sys4LD systemLD valueLD
)

# The in-scope posting programs, per ledger, plus the Date Entry program each
# runner uses to pin the clock.
readonly -a ACAS_GENERAL_MODULES=(gl000 gl051 gl070 gl071 gl072 gl080)
readonly -a ACAS_SALES_MODULES=(sl000 sl055 sl060 sl100)
readonly -a ACAS_PURCHASE_MODULES=(pl000 pl055 pl060 pl100)
readonly -a ACAS_IRS_MODULES=(irs000 irs030)

# THE PINNED IDENTITY OF THE VENDORED preSQL ARCHIVE (CWE-494 download of code
# without integrity check) presql2-latest.zip is not a passive data file.

declare -a ACAS_BUILD_TLS_VARIANTS=()
declare -a ACAS_PARAM_FILES=()      # credential files to shred on exit
declare -a ACAS_SCRATCH_DIRS=()     # scratch trees to remove on exit
declare -a ACAS_WARN_SUMMARY=()     # non-fatal findings, replayed at the end
ACAS_START_STEP=1                   # --from N
ACAS_ONLY_STEP=0                    # --only N (0 = run the whole sequence)
ACAS_REFRESH_TREE=1                 # refresh $ACAS_BUILD before step 1
ACAS_RUN_PREFLIGHT_LINK=1           # reproduce the vendored worked example

# ---------------------------------------------------------------------------
#  THE FROZEN BUILD IS THE DEFAULT
#
#  Applying the whole source-transform block unconditionally would build EVERY oracle
#  from 41 modified frozen files and leave no invocation able to produce an unmodified
#  one. Disclosing the transforms in the attestation is necessary but not
#  sufficient: rule R-6 makes the COMPILED PROGRAM the
#  specification, and rule R-4 requires its defects to be reproduced rather than
#  repaired. A build that repairs IF scope, connection lifetime and stale reply status
#  in the oracle has repaired the specification, so an empty diff against it is not
#  evidence of parity with the frozen system - it is evidence of parity with a patched
#  one.
#
#  0 = FROZEN. Not one byte of the build copy differs from the checkout, and the
#      attestation records `oracle-source-is-frozen yes`. This is the ONLY mode whose
#      output `harness/reset_db.sh` will accept as evidence -- it reads this attestation
#      before stage 1 drops a table.
#  1 = TRANSFORMED. The catalogued transforms are applied. Must be asked for
#      explicitly, by `--transformed-oracle` or ACAS_ORACLE_ALLOW_TRANSFORMS=1, and the
#      resulting oracle is a diagnostic tool rather than a specification.
#
#  Defaulting to frozen is what makes the difference visible: see §8.7 of
#  README-python-migration.md for what a frozen build actually does on this checkout,
#  which is measured rather than predicted.
# ---------------------------------------------------------------------------
ACAS_ALLOW_SOURCE_TRANSFORMS=0

#: The transforms ACTUALLY applied by this build. Empty in the default frozen mode. The
#: catalogue below (ACAS_SOURCE_TRANSFORMS) is what WOULD be applied in transformed
#: mode; this is what was. The attestation and the measured register check both read
#: THIS array, so a frozen build cannot report itself transformed or the reverse.
declare -a ACAS_SOURCE_TRANSFORMS_APPLIED=()
ACAS_LOG_DIR=''                     # $ACAS_OUT/build, created in preflight
ACAS_PRESQL2_DIR=''                 # resolved unpacked package directory
ACAS_COBMYSQLAPI_SRC=''             # resolved cobmysqlapi.o to distribute
ACAS_DB_PROBE_DIAG=''               # last client diagnostic from the auth probe

# Reporting. Stage banners are numbered so the log reads as the deterministic
# staged orchestration the plan requires (R-6): explicit, ordered, individually
# reported, individually asserted.
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

# ---------------------------------------------------------------------------
#  THE CLIENT-DIAGNOSTIC SUMMARY
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
  local raw="${1-$ACAS_DB_PROBE_DIAG}" category='' code='' lines=0 bytes=0 digest=''

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

# Join the remaining arguments into an alternation for grep -E.
acas_join_re() {
  local IFS='|'
  printf '%s' "$*"
}

# ---------------------------------------------------------------------------
#  THE TARGET, DESCRIBED WITHOUT NAMING IT
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
#  different one, while the value itself discloses no name. The full values remain
#  in the environment, where the tools that need them read them.
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

# acas_assert_outside_repo <label> <path> Nothing this script writes may land
# inside $ACAS_REPO.
# Join the remaining arguments with single spaces for human-readable output.
acas_join_words() {
  local IFS=' '
  printf '%s' "$*"
}


# acas_timeout_seconds <env-var-name> <default> Resolve one budget from the
# environment, validating it as a positive integer no larger than
# ACAS_TIMEOUT_MAX.
acas_timeout_seconds() {
  local name="$1" default="$2" value
  ACAS_TIMEOUT_RESOLVED=''
  value="${!name-}"
  [[ -n "$value" ]] || value="$default"

  if [[ ! "$value" =~ ^[0-9]+$ ]]; then
    acas_die "$EX_USAGE" \
      "$name must be a whole number of seconds; got '$value'." \
      'Budgets are wall-clock seconds. Raise the value for a slower host;' \
      'there is deliberately no way to disable the deadline.'
  fi

  # 10# forces base 10: a zero-padded value such as 08 would otherwise be read
  # as an invalid octal literal and abort with an arithmetic syntax error.
  value=$(( 10#$value ))

  if (( value < 1 )); then
    acas_die "$EX_USAGE" \
      "$name must be at least 1 second; got '$value'." \
      'A zero or negative budget would mean "block forever", which is exactly' \
      'the condition every deadline in this script exists to rule out.'
  fi
  if (( value > ACAS_TIMEOUT_MAX )); then
    acas_die "$EX_USAGE" \
      "$name must not exceed $ACAS_TIMEOUT_MAX seconds; got '$value'." \
      'A budget beyond 24 hours is indistinguishable from no budget at all.'
  fi

  ACAS_TIMEOUT_RESOLVED="$value"
}

# Resolve every budget once, before any external command is spawned, so that a
# malformed value is reported as a usage error at startup rather than hours
# into a build.
acas_resolve_deadlines() {
  acas_have timeout || acas_die "$EX_PRECONDITION" \
    'timeout is not on the PATH.' \
    'It is part of coreutils and every external command this script spawns' \
    'runs under it. harness/Dockerfile.gnucobol provides it.'

  # No command substitution anywhere here -- see acas_timeout_seconds.
  acas_timeout_seconds ACAS_TIMEOUT_GRACE 15
  ACAS_TIMEOUT_GRACE="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_UNPACK 300
  ACAS_TIMEOUT_UNPACK="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_COMPILE 600
  ACAS_TIMEOUT_COMPILE="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_BUILD 3600
  ACAS_TIMEOUT_BUILD="$ACAS_TIMEOUT_RESOLVED"
  acas_timeout_seconds ACAS_TIMEOUT_PROBE 30
  ACAS_TIMEOUT_PROBE="$ACAS_TIMEOUT_RESOLVED"

  readonly ACAS_TIMEOUT_GRACE ACAS_TIMEOUT_UNPACK ACAS_TIMEOUT_COMPILE
  readonly ACAS_TIMEOUT_BUILD ACAS_TIMEOUT_PROBE

  # Belt and braces: nothing downstream may run with an unresolved budget, and
  # a missing one would degrade to "no deadline" -- the defect, not a fallback.
  local budget
  for budget in "$ACAS_TIMEOUT_GRACE" "$ACAS_TIMEOUT_UNPACK" "$ACAS_TIMEOUT_COMPILE" \
                "$ACAS_TIMEOUT_BUILD" "$ACAS_TIMEOUT_PROBE"; do
    [[ "$budget" =~ ^[1-9][0-9]*$ ]] || acas_die "$EX_PRECONDITION" \
      'a deadline budget resolved empty or non-positive.' \
      'This is an internal invariant failure, not a configuration error.'
  done

  acas_log "deadlines (s): unpack=$ACAS_TIMEOUT_UNPACK compile=$ACAS_TIMEOUT_COMPILE build=$ACAS_TIMEOUT_BUILD probe=$ACAS_TIMEOUT_PROBE grace=$ACAS_TIMEOUT_GRACE"

  acas_verify_deadline_escalation
}

# Measure whether the `timeout' on this PATH really bounds a child that refuses
# to stop, and report it when it does not.
acas_verify_deadline_escalation() {
  local probe_budget=1 probe_grace=1 sleep_for=4 allowance_ms=3200
  local started_us ended_us elapsed_ms rc=0 raw

  raw="${EPOCHREALTIME-}"
  if [[ -z "$raw" ]]; then
    acas_note 'EPOCHREALTIME is unavailable; the deadline escalation self-test is skipped'
    return 0
  fi

  # EPOCHREALTIME is seconds.microseconds; removing the separator yields whole
  # microseconds as an integer. The comma form is accepted because the
  # separator follows LC_NUMERIC.
  raw="${raw/,/.}"
  started_us="${raw/./}"

  timeout "--kill-after=$probe_grace" --signal=TERM "$probe_budget" \
    bash -c 'trap "" TERM; sleep '"$sleep_for" >/dev/null 2>&1 </dev/null || rc=$?

  raw="${EPOCHREALTIME}"
  raw="${raw/,/.}"
  ended_us="${raw/./}"
  elapsed_ms=$(( (ended_us - started_us) / 1000 ))

  if (( elapsed_ms <= allowance_ms )); then
    acas_log "deadline escalation verified: a TERM-ignoring child was stopped in ${elapsed_ms}ms"
    return 0
  fi

  acas_warn \
    "the timeout on this PATH does not enforce --kill-after promptly (${elapsed_ms}ms for a ${probe_budget}s+${probe_grace}s deadline)." \
    'Deadlines still fire and every command is still bounded on TERM, but a' \
    'child that IGNORES TERM can hold a stage past its budget. GNU coreutils' \
    'behaves correctly; the Rust reimplementation (uutils) waits for orphaned' \
    'descendants before returning. harness/Dockerfile.gnucobol provides GNU' \
    'coreutils, so this affects ad-hoc runs on a developer host only.'
  return 0
}

# acas_deadline_prefix <budget> Populate ACAS_DEADLINE_ARGV with the invocation
# words that impose <budget> on whatever command words are appended to them.
acas_deadline_prefix() {
  ACAS_DEADLINE_ARGV=(
    timeout
    "--kill-after=$ACAS_TIMEOUT_GRACE"
    --signal=TERM
    "$1"
  )
}

# acas_is_timeout_status <rc> <elapsed> <budget> True when <rc> means "the
# deadline expired" rather than "the command ran and failed". Measured
# behaviour of the two implementations in play.
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

# acas_assert_not_timed_out <rc> <elapsed> <budget> <budget-var> <label> <code>
# Abort with EX_TIMEOUT when the deadline expired, naming the stage, the budget
# it exceeded and the variable that raises it.
acas_assert_not_timed_out() {
  local rc="$1" elapsed="$2" budget="$3" budget_var="$4" label="$5" code="$6"

  if ! acas_is_timeout_status "$rc" "$elapsed" "$budget"; then
    return 0
  fi

  # The stage code is reported alongside EX_TIMEOUT rather than instead of it.
  acas_die "$EX_TIMEOUT" \
    "$label exceeded its ${budget}s deadline (stage exit code would have been $code)." \
    "Raise $budget_var if this host is simply slower than the budget assumes;" \
    'investigate the command itself if it is genuinely stuck. The child was' \
    "sent TERM at the deadline and KILL ${ACAS_TIMEOUT_GRACE}s later."
}

# acas_run_deadline <budget> <budget-var> <label> <code> <workdir|-> -- cmd...
acas_run_deadline() {
  local budget="$1" budget_var="$2" label="$3" code="$4" workdir="$5"
  shift 5
  [[ ${1:-} != '--' ]] || shift

  if [[ "$workdir" != '-' && ! -d "$workdir" ]]; then
    acas_die "$code" \
      "$label cannot run: its working directory $workdir does not exist."
  fi

  acas_deadline_prefix "$budget"

  # STDIN IS CLOSED FOR EVERY DELEGATED CHILD
  #
  # This script is run non-interactively -- from harness/docker-compose.yml, from a
  # `docker compose run -T', from tests/conftest.py -- and it delegates to programs
  # that WILL read stdin if it is a terminal or a pipe that never closes. presql2
  # prompts on a parameter it cannot resolve; cobc reads a program from stdin when
  # given `-' ; a mariadb client with no --execute reads statements from stdin
  # forever. Any of those turns a build into a hang whose only visible symptom is
  # the deadline firing minutes later with a timeout classification that says
  # nothing about the real cause.
  #
  # `< /dev/null' makes every one of them see immediate EOF, so a program that
  # wanted input fails fast and says what it wanted. The deadlines stay exactly as
  # they were: they remain the fallback for a child that genuinely spins without
  # reading anything.
  local started rc=0 elapsed
  started="$SECONDS"
  if [[ "$workdir" == '-' ]]; then
    "${ACAS_DEADLINE_ARGV[@]}" "$@" < /dev/null || rc=$?
  else
    # `exec' so the subshell process BECOMES timeout.
    ( cd "$workdir" && exec "${ACAS_DEADLINE_ARGV[@]}" "$@" ) < /dev/null || rc=$?
  fi
  elapsed=$(( SECONDS - started ))

  acas_assert_not_timed_out "$rc" "$elapsed" "$budget" "$budget_var" "$label" "$code"
  return "$rc"
}

# See the ACAS_PRESQL2_SHA256_EXPECTED declaration for why an archive that
# feeds a compile-and-install step is treated as untrusted input with a pinned
# identity.

# acas_file_sha256 <path> sha256sum when present, python3 hashlib otherwise.
acas_file_sha256() {
  local path="$1" digest=''

  acas_deadline_prefix "$ACAS_TIMEOUT_PROBE"

  if acas_have sha256sum; then
    digest="$("${ACAS_DEADLINE_ARGV[@]}" sha256sum -- "$path" < /dev/null)" || return 1
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

# acas_assert_archive_digest <path> Refuse to unpack an archive whose identity
# is not the pinned one, unless the maintainer has explicitly named a
# replacement digest.
acas_assert_archive_digest() {
  local path="$1" expected="$ACAS_PRESQL2_SHA256_EXPECTED" actual=''
  local override="${ACAS_PRESQL2_SHA256-}"

  if [[ -n "$override" ]]; then
    if [[ ! "$override" =~ ^[0-9a-fA-F]{64}$ ]]; then
      acas_die "$EX_ARCHIVE" \
        'ACAS_PRESQL2_SHA256 must be a 64-character hex SHA-256 digest.' \
        "Got: $override"
    fi
    # Compared lower-case so the pin is insensitive to how it was pasted.
    override="${override,,}"
    if [[ "$override" != "$expected" ]]; then
      acas_warn \
        'ACAS_PRESQL2_SHA256 overrides the pinned preSQL archive digest.' \
        "  pinned in this script: $expected" \
        "  accepted for this run: $override" \
        'The oracle built by this run is therefore NOT the one this checkout' \
        'pins. Update ACAS_PRESQL2_SHA256_EXPECTED when replacing the archive.'
    fi
    expected="$override"
  fi

  actual="$(acas_file_sha256 "$path")" || acas_die "$EX_ARCHIVE" \
    "could not compute the SHA-256 digest of $path."
  actual="${actual,,}"

  if [[ "$actual" != "$expected" ]]; then
    acas_die "$EX_ARCHIVE" \
      "$path does not match its pinned SHA-256 digest." \
      "  expected: $expected" \
      "  measured: $actual" \
      'Steps 2 and 3 compile C and COBOL out of this archive and install the' \
      'result, so an unexpected archive silently redefines the oracle -- and' \
      'the oracle is the behavioural specification for the whole migration.' \
      'Restore the committed archive, or set ACAS_PRESQL2_SHA256 to the digest' \
      'of the replacement to accept it deliberately -- and update' \
      'ACAS_PRESQL2_SHA256_EXPECTED here and PRESQL2_SHA256 in' \
      'harness/Dockerfile.gnucobol, which unpacks the same archive and must' \
      'agree.'
  fi
  acas_log "archive digest verified: sha256 $actual"
}

# acas_pinned_member_digest <member-name> Echo the digest ACAS_PRESQL2_MEMBER_DIGESTS
# pins for one member of the vendored archive. Fails when the member is not pinned,
# so a caller can never silently compare against an empty expectation.
acas_pinned_member_digest() {
  local wanted="$1" entry
  for entry in "${ACAS_PRESQL2_MEMBER_DIGESTS[@]}"; do
    if [[ "${entry%%:*}" == "$wanted" ]]; then
      printf '%s' "${entry#*:}"
      return 0
    fi
  done
  return 1
}

# -----------------------------------------------------------------------------
# PROVENANCE FOR A REUSED BUILD PRODUCT
#
# Steps 2 and 3 each prefer an artifact something else already built -- the object at
# ACAS_COBMYSQLAPI_OBJ, and whatever `presql2' the PATH resolves. Both are reused
# because rebuilding them costs time the parity runs do not need to spend, and in the
# shipped image both were built by harness/Dockerfile.gnucobol from the same pinned
# archive this script verifies.
#
# What could not be checked is WHICH source they came from. A compiled artifact's own
# digest is not reproducible -- it moves with the compiler, its flags, its libraries
# and the host -- so pinning it would be a fiction that failed on every machine but
# one. What IS stable is the digest of the SOURCE it was compiled from, so whatever
# builds one of these artifacts records that digest in a sidecar beside it, and these
# two helpers write and read it. An artifact with no sidecar, or with one naming a
# different source, is not trusted: the caller rebuilds from the source step 1 has
# just verified.
# -----------------------------------------------------------------------------

# acas_record_artifact_provenance <artifact> <source-digest> Best effort by design:
# the sidecar is an optimisation for the NEXT run, and failing to write it must never
# fail a build that has otherwise succeeded (the artifact directory may be read-only,
# and frequently is).
acas_record_artifact_provenance() {
  local artifact="$1" digest="$2"
  local sidecar="${artifact}${ACAS_COBMYSQLAPI_PROVENANCE_SUFFIX}"

  if printf '%s\n' "$digest" > "$sidecar" 2>/dev/null; then
    acas_log "recorded provenance: $sidecar -> $digest"
    return 0
  fi
  acas_note "provenance for $artifact could not be recorded at $sidecar (not writable); the next run will rebuild rather than reuse"
  return 0
}

# acas_artifact_provenance_holds <artifact> <expected-source-digest> <source-name>
# <what>  0 when <artifact> carries a sidecar naming <expected-source-digest>. Warns
# and returns 1 otherwise -- never dies, because every caller has a working
# alternative: build its own from the verified source.
acas_artifact_provenance_holds() {
  local artifact="$1" expected="$2" source_name="$3" what="$4"
  local sidecar="${artifact}${ACAS_COBMYSQLAPI_PROVENANCE_SUFFIX}"
  local recorded=''

  if [[ ! -f "$sidecar" ]]; then
    acas_warn \
      "$artifact carries no provenance record, so it will NOT be reused." \
      "  expected a sidecar at: $sidecar" \
      "  naming the sha256 of:  $source_name" \
      "$what, so it decides what the oracle IS -- and an artifact whose source" \
      'cannot be named cannot be shown to be the one this checkout pins. Rebuilding' \
      'it from the source step 1 has just verified costs one compile and makes the' \
      'chain from the pinned archive to the built oracle provable end to end.'
    return 1
  fi

  # First whitespace-delimited token, so a `sha256sum'-style line works too.
  read -r recorded _ < "$sidecar" || recorded=''
  recorded="${recorded,,}"

  if [[ "$recorded" != "${expected,,}" ]]; then
    acas_warn \
      "$artifact was built from a different $source_name, so it will NOT be reused." \
      "  its sidecar names: ${recorded:-<empty>}" \
      "  this checkout pins: $expected" \
      'Rebuilding from the verified source rather than trusting the mismatch.'
    return 1
  fi

  acas_log "provenance verified: $artifact was built from $source_name sha256 $recorded"
  return 0
}

# acas_extract_audited_zip <archive> <destination> <expected-root> Extract
# every member of <archive> beneath <destination>, having first audited the
# WHOLE member list.
acas_extract_audited_zip() {
  local archive="$1" destination="$2" root="$3" rc=0

  acas_run_deadline "$ACAS_TIMEOUT_UNPACK" ACAS_TIMEOUT_UNPACK \
    "auditing and extracting $archive" "$EX_ARCHIVE" - \
    -- python3 - "$archive" "$destination" "$root" <<'PY' || rc=$?
"""Audit every member of a zip archive, then extract the audited members.

Rejections, each of which is a way an archive can write outside the tree it was
told to occupy or can smuggle something other than a file into it:

  * an absolute member name, or one carrying a Windows drive letter
  * any ``..`` path segment, at any depth
  * a backslash, which some producers emit as a separator and which would be a
    literal character in a POSIX name
  * any root other than the single expected one
  * any member that is not a regular file or a directory -- symlink, fifo,
    socket, device
  * a duplicate member name, which decides by extraction ORDER which content
    wins and is therefore never legitimate
  * a member name that does not resolve back inside the destination

Exit codes: 0 audited and extracted, 3 the audit rejected the archive,
4 the archive could not be read, 5 extraction failed after a clean audit.
"""

import os
import stat
import sys
import zipfile

archive_path, destination, expected_root = sys.argv[1], sys.argv[2], sys.argv[3]

# Windows created a member: the mode bits in external_attr are meaningless, so
# such a member is treated as a plain file and given an explicit mode below.
CREATE_SYSTEM_UNIX = 3


def member_mode(info):
    """Return the POSIX mode a member declares, or None when it declares none."""
    if info.create_system != CREATE_SYSTEM_UNIX:
        return None
    mode = info.external_attr >> 16
    return mode if mode else None


def reject(name, reason):
    sys.stderr.write('rejected member %r: %s\n' % (name, reason))


try:
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()

        problems = 0
        seen = set()
        planned = []

        for info in infos:
            name = info.filename

            if not name or name in ('.', '..'):
                reject(name, 'empty or dot-only member name')
                problems += 1
                continue
            if name.startswith('/') or name.startswith('\\'):
                reject(name, 'absolute member name')
                problems += 1
                continue
            if '\\' in name:
                reject(name, 'backslash in member name')
                problems += 1
                continue
            if len(name) > 1 and name[1] == ':':
                reject(name, 'drive-letter member name')
                problems += 1
                continue

            parts = [part for part in name.split('/') if part not in ('', '.')]
            if any(part == '..' for part in parts):
                reject(name, 'parent-directory traversal segment')
                problems += 1
                continue
            if not parts:
                reject(name, 'member name has no usable path segments')
                problems += 1
                continue
            if parts[0] != expected_root:
                reject(name, 'unexpected root %r (expected %r)'
                       % (parts[0], expected_root))
                problems += 1
                continue

            mode = member_mode(info)
            if mode is not None:
                kind = stat.S_IFMT(mode)
                if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                    reject(name, 'member type 0o%o is neither a regular file '
                                 'nor a directory' % kind)
                    problems += 1
                    continue

            key = '/'.join(parts)
            if key in seen:
                reject(name, 'duplicate member name; extraction order would '
                             'decide which content wins')
                problems += 1
                continue
            seen.add(key)

            target = os.path.realpath(os.path.join(destination, *parts))
            root = os.path.realpath(destination)
            if target != root and not target.startswith(root + os.sep):
                reject(name, 'resolves to %s, outside %s' % (target, root))
                problems += 1
                continue

            planned.append((info, parts, target, mode))

        if problems:
            sys.stderr.write(
                '%d of %d member(s) rejected; nothing was extracted\n'
                % (problems, len(infos)))
            raise SystemExit(3)

        # A package with no regular-file members has nothing to contribute to
        # steps 2 and 3. Caught here, where the archive is the subject, rather
        # than three assertions later as a puzzling "cobmysqlapi38.c is missing".
        if not any(not info.is_dir() for info, _parts, _target, _mode in planned):
            sys.stderr.write('archive contains no file members to extract\n')
            raise SystemExit(3)
except SystemExit:
    raise
except (OSError, zipfile.BadZipFile, RuntimeError) as error:
    sys.stderr.write('cannot read %s: %s\n' % (archive_path, error))
    raise SystemExit(4)

# Audit passed. Extract the audited members ONE AT A TIME, by the resolved path
# this program computed -- never by the name the archive supplied -- and with an
# explicit mode. Modes are owner-only, matching this script's umask 077: the
# execute bit is carried across where the member declared one, because a
# vendored build script that arrives non-executable is a change to the package.
try:
    with zipfile.ZipFile(archive_path) as archive:
        directories = 0
        files = 0
        for info, parts, target, mode in planned:
            if info.is_dir() or (mode is not None and stat.S_ISDIR(mode)):
                os.makedirs(target, mode=0o700, exist_ok=True)
                os.chmod(target, 0o700)
                directories += 1
                continue

            parent = os.path.dirname(target)
            if parent:
                os.makedirs(parent, mode=0o700, exist_ok=True)

            with archive.open(info) as source:
                # 'xb' so a member can never overwrite something already there:
                # the duplicate-name audit above makes that impossible within
                # the archive, and this makes it impossible against a stale
                # tree as well.
                with open(target, 'xb') as sink:
                    while True:
                        block = source.read(1 << 16)
                        if not block:
                            break
                        sink.write(block)

            executable = mode is not None and (mode & 0o111)
            os.chmod(target, 0o700 if executable else 0o600)
            files += 1
except (OSError, zipfile.BadZipFile, RuntimeError) as error:
    sys.stderr.write('extraction failed after a clean audit: %s\n' % error)
    raise SystemExit(5)

sys.stdout.write('audited %d member(s): %d directory(ies), %d file(s)\n'
                 % (len(planned), directories, files))
PY

  case "$rc" in
    0) : ;;
    3) acas_die "$EX_ARCHIVE" \
         "$archive failed its member audit; see the rejected-member lines above." \
         'A member that is absolute, traverses upwards, is a symlink or other' \
         'non-regular entry, or sits under an unexpected root would write' \
         'outside the scratch tree. Nothing was extracted.' ;;
    4) acas_die "$EX_ARCHIVE" \
         "$archive could not be read as a zip archive." \
         'Restore the committed copy from this checkout.' ;;
    5) acas_die "$EX_ARCHIVE" \
         "extraction of $archive failed after its member audit passed." \
         "Check free space and permissions on $destination." ;;
    *) acas_die "$EX_ARCHIVE" \
         "the member audit of $archive exited with status $rc." ;;
  esac
}

# Re-exec guard -- SAFETY CRITICAL, do not remove. 1. bash reads a script file
# incrementally as it executes it.
acas_reexec_from_repo_if_needed() {
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
  # THE ONE DELIBERATE EXCEPTION to the finite-deadline rule, and it is not a
  # gap.
  exec bash "$repo_copy" "$@"
}

acas_reexec_from_repo_if_needed "$@"

# shellcheck disable=SC2317
# Traps. ERR reports the failing line so an unexpected failure is attributable.
acas_on_err() {
  local code="$1" line="$2" cmd="$3"
  printf '\nFATAL: unexpected failure at %s line %s (exit %s)\n' \
    "${BASH_SOURCE[0]}" "$line" "$code" >&2
  printf '       failing command: %s\n' "$cmd" >&2
}

# Create a file that cannot be hijacked: a symlink or non-regular path is refused
# rather than followed, and the file is created under `set -C' (O_EXCL) so it can
# neither be pre-created by another user nor widened between create and chmod.
acas_create_private_file() {
  local path="$1" what="$2" code="${3:-$EX_PRECONDITION}"

  if [[ -L "$path" ]]; then
    acas_die "$code" \
      "$what is a SYMLINK: $path" \
      'It is refused rather than followed. Writing through it would truncate' \
      'whatever it points at, and would then expose this file to whoever placed' \
      'the link. Remove it and run again.'
  fi
  if [[ -e "$path" ]] && [[ ! -f "$path" ]]; then
    acas_die "$code" \
      "$what exists and is not a regular file: $path" \
      'Refusing to write to a directory, device or socket.'
  fi
  rm -f -- "$path" 2>/dev/null || true

  # noclobber => O_EXCL. A subshell so the option change cannot leak into the
  # rest of the script.
  if ! (set -C; : >"$path") 2>/dev/null; then
    acas_die "$code" \
      "could not create $what at $path." \
      'Either the directory is not writable, or something created the name in' \
      'the instant between the symlink check and the exclusive create -- which' \
      'is exactly the race the exclusive create exists to lose safely.'
  fi
  chmod 600 -- "$path" 2>/dev/null || acas_die "$code" \
    "could not restrict $what to mode 600: $path"
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
    # the path is absolute and at least two components deep.
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
     directory.  [presql2-latest.zip:presql2-package/cobmysqlapi38.sh] [common/comp-common.sh:L26]
  3  Build and install the `presql2' translator onto the PATH.
     [presql2-latest.zip:presql2-package/presql2.sh]
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
                      vendored worked example [presql2-latest.zip:presql2-package/ACAS/comp-stockMT.sh].
  --transformed-oracle
                      Apply the catalogued source transformations to the BUILD COPY
                      before compiling. NOT the default, and not a mode whose output
                      may be used as parity evidence: it repairs IF scope, connection
                      lifetime and stale reply status in the frozen programs, which
                      rule R-4 requires be reproduced rather than repaired. The
                      attestation then records `oracle-source-is-frozen no' and
                      harness/reset_db.sh REFUSES the resulting oracle, exit 77. Use it to
                      diagnose the cycle, never to make a claim about it.
                      ACAS_ORACLE_ALLOW_TRANSFORMS=1 has the same effect.
  --frozen-oracle     State the default explicitly: transform nothing.
  -h, --help          Print this help and exit 0.

Required environment (harness/docker-compose.yml supplies all of it):
  ACAS_REPO           read-only checkout            (mounted ../:/repo:ro)
  ACAS_BUILD          writable build tree           (volume  /build)
  ACAS_DATA           writable ledger/data area     (volume  /data)
  ACAS_OUT            writable output area          (volume  /out)
  ACAS_DB_HOST        MariaDB host
  ACAS_DB_PORT        MariaDB port
  ACAS_DB_NAME        target schema (the .scb BASE= directive names it too);
                      AT MOST 12 CHARACTERS -- DB-Schema is pic x(12)
  ACAS_DB_USER        MariaDB user; AT MOST 12 CHARACTERS -- DB-UName is
                      pic x(12)
  ACAS_DB_PASSWORD    MariaDB password (never echoed, never logged); AT MOST
                      12 CHARACTERS -- DB-UPass is pic x(12). A longer value
                      is silently truncated to its first 12 characters, so it
                      is refused here rather than surfacing later as
                      "credentials rejected" [copybooks/wsfnctn.cob:L56-L62]
  ACAS_DB_SOCKET      unix socket path; may legitimately be EMPTY, in which
                      case DBSOCKET=NULL is written, the only spelling the C
                      shim maps to "no socket"
                      [presql2-latest.zip:presql2-package/cobmysqlapi38.c:L513-L525]

Optional environment:
  ACAS_BUILD_STRICT=1        promote compiler warnings to fatal
  ACAS_DB_WAIT_TIMEOUT=N     seconds to wait for MariaDB (default 180)
  ACAS_DB_AUTH_GRACE=N       seconds to tolerate "Access denied" before failing
                             fast, capped at ACAS_DB_WAIT_TIMEOUT (default 15).
                             Rejected credentials are a configuration error,
                             not a readiness state, so they are NOT retried for
                             the full timeout
  ACAS_PRESQL2_PACKAGE=DIR   reuse an already-unpacked preSQL package. DIR is
                             not taken on trust: the four members later steps
                             compile -- cobmysqlapi38.c, cobmysqlapi38.sh,
                             presql2.cbl, presql2.sh -- are hashed and must match
                             the digests pinned in this script, whichever branch
                             step 1 takes
  ACAS_COBMYSQLAPI_OBJ=FILE  reuse an already-compiled cobmysqlapi.o. Reused only
                             when FILE.source-sha256 names the pinned
                             cobmysqlapi38.c digest. Without that record the
                             object is rebuilt from the verified source rather
                             than trusted -- one gcc invocation
  ACAS_PRESQL2_DBNAME=NAME   schema presql2 connects to (default
                             information_schema; see acas_write_presql2_param)
  ACAS_MYSQL_PREFIX=DIR      checked for agreement with the frozen literal
                             /usr/local/mysql; it cannot override it
  ACAS_PRESQL2_SHA256=HEX    accept a REPLACEMENT presql2-latest.zip whose
                             SHA-256 is HEX instead of the digest pinned in this
                             script. Announced as a warning and replayed in the
                             closing summary: the archive decides what the
                             oracle is, so redefining it is never silent. It
                             admits the archive's IDENTITY only -- the four
                             member digests are still enforced, so a genuine
                             replacement means updating
                             ACAS_PRESQL2_MEMBER_DIGESTS as well. That is
                             deliberate: this variable cannot become a way to
                             feed unpinned C or COBOL into the oracle

Finite deadlines. Every external command that compiles, extracts, copies in
bulk, installs, or talks to the database runs under one, and there is
deliberately no way to disable them. Each is a whole number of wall-clock
seconds, at least 1 and at most 86400; the command is sent TERM at the deadline
and KILL ACAS_TIMEOUT_GRACE seconds later, and only ever that one child:
  ACAS_TIMEOUT_UNPACK=N      audit and extract the vendored zip (default 300)
  ACAS_TIMEOUT_COMPILE=N     one gcc or cobc invocation (default 600)
  ACAS_TIMEOUT_BUILD=N       one delegated frozen build script -- comp-common.sh
                             or comp-all.sh -- and the build-tree clear and copy
                             (default 3600)
  ACAS_TIMEOUT_PROBE=N       one database client probe, one cobc interrogation,
                             one install, one digest read, ldconfig (default 30)
  ACAS_TIMEOUT_GRACE=N       TERM-to-KILL grace period (default 15)
The only external invocation deliberately NOT wrapped is the re-exec of this
script's own checkout copy: `exec' replaces this process, and the replacement
imposes these same deadlines. Fast metadata operations (mkdir, readlink, stat)
are not wrapped either; they cannot block on anything the wrapped commands do
not already cover.

Transport security (the probes this script issues authenticate with the same
account presql2 uses, so a non-local connection is NOT downgraded silently):
  ACAS_DB_TLS_CA=PATH        PEM bundle the server certificate chains to. When
                             set, every probe connects with --ssl-ca and
                             --ssl-verify-server-cert, so the certificate AND
                             the hostname are checked. Without the verify flag
                             a client encrypts but accepts any certificate,
                             which is not verification at all
  ACAS_DB_ALLOW_PLAINTEXT=1  declare that the target really is an isolated
                             harness network -- the private Compose network
                             [harness/docker-compose.yml] -- and permit
                             plaintext to it. Only the exact values 1, y, yes,
                             true and on count; anything else is a typo and is
                             treated as "not declared"
  A loopback host (127.0.0.1, ::1, localhost) or a non-empty ACAS_DB_SOCKET
  needs neither: those never leave the machine. Any OTHER host with no CA and
  no explicit declaration is REFUSED before a single connection is attempted.

Vendored-archive integrity (the archive is compiled and executed by steps 2
and 3, so an unverified archive means an unverified oracle):
  ACAS_PRESQL2_SHA256=HEX    override the pinned SHA-256 of
                             presql2-latest.zip, for the one legitimate case
                             where the maintainer has published a NEW vendored
                             package. Must be 64 lowercase hex digits.
                             harness/Dockerfile.gnucobol unpacks the same
                             archive and its declared digest must agree
  The pinned archive digest stays authoritative regardless of which branch step
  1 takes. Whether the archive is unpacked here or an already-unpacked directory
  is reused via ACAS_PRESQL2_PACKAGE, the four members steps 2 and 3 compile are
  hashed against ACAS_PRESQL2_MEMBER_DIGESTS. A build product reused instead of
  rebuilt -- the object at ACAS_COBMYSQLAPI_OBJ, or a `presql2' already on the
  PATH -- must carry a NAME.source-sha256 sidecar naming the pinned digest of
  the source it came from; a compiled artifact's own digest moves with the
  compiler and the host, so the source digest is the only honest thing to pin.
  An artifact that cannot name its source is rebuilt from the source step 1 has
  just verified, never trusted.

Exit codes:
  0 success   64 usage   65 precondition   66 database   67 build tree
  71-75 steps 1-5   76 artifact assertions   77 finalisation
  78 an external command exceeded its deadline
  79 presql2-latest.zip failed its digest check or its member audit

Code 67 in particular means the writable build tree could not be prepared, and
the commonest reason is the provenance guard that stands in front of the
recursive clear. That clear is admitted for an EMPTY tree, for a tree holding
DIRECTORIES ONLY at every depth -- which is what the /build volume of the
shipped Compose topology hands over, and which contains no data by construction
-- and for a tree this script has already marked as its own. A tree that holds
holds FILES is refused, and the refusal names the first few of them; clear it,
point ACAS_BUILD elsewhere, pass --no-refresh to build in place, or create the
marker by hand to say you meant it.

This script NEVER writes to $ACAS_REPO, never modifies a frozen compile script,
never adds or removes a cobc flag, and never exits 0 unconditionally.
USAGE
}

# Validate in place and die on failure. Deliberately NOT a value-returning
# helper.
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

  #  The environment route, read BEFORE the command line so an explicit
  #  `--frozen-oracle` still wins over an inherited variable. Only the exact string
  #  `1` enables it: a truthy-looking value such as `false` or `no` must not quietly
  #  turn on a mode whose output cannot be used as evidence.
  if [[ "${ACAS_ORACLE_ALLOW_TRANSFORMS-}" == '1' ]]; then
    ACAS_ALLOW_SOURCE_TRANSFORMS=1
  fi

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
      --transformed-oracle)
        ACAS_ALLOW_SOURCE_TRANSFORMS=1
        shift
        ;;
      --frozen-oracle)
        ACAS_ALLOW_SOURCE_TRANSFORMS=0
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

# This script ASSERTS its toolchain; it never installs one.

# The full environment contract. ACAS_DB_SOCKET is deliberately in the
# "declared" list rather than the "non-empty" list.
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
      'The C shim converts it with atoi() at [presql2-latest.zip:presql2-package/cobmysqlapi38.c:L511],' \
      'so a non-numeric value silently becomes port 0.'
  fi
  # THE RANGE, not merely the character class -- and here the consequence is
  # worse than a failed connection.
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

  # Every card written into presql2.param is copied with strncpy(..., 32) at
  # `cobmysqlapi38.c:L138,L145,L152,L159,L166,L173' into a 32-byte COBOL pic
  # x(32) field.
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
        '[presql2-latest.zip:presql2-package/cobmysqlapi38.c:L114-L176]'
    fi
  done

  # THE 32-CHARACTER CEILING ABOVE IS NOT THE TIGHTEST ONE, and the difference
  # matters. `strncpy(..., 32)' is the width of the C shim's own parameter card;
  # the COBOL side that ultimately authenticates does not use a 32-byte field for
  # the schema, the user or the password. `RDB-Data' declares
  #     DB-Schema pic x(12)   DB-UName pic x(12)   DB-UPass pic x(12)
  #     DB-Host   pic x(32)   DB-Socket pic x(64)  DB-Port  pic x(5)
  # [copybooks/wsfnctn.cob:L56-L62], and every bridge STRINGs those fields
  # `delimited by space' into the null-terminated C arguments it hands to the shim
  # [common/glbatchMT.cbl:L402-L425]. A 20-character password therefore arrives at
  # the server as its first 12 characters, silently -- the field cannot hold more,
  # so there is nothing to warn about at the point of truncation.
  #
  # WHY THIS BELONGS IN *THIS* SCRIPT AND NOT ONLY IN THE LATER ONES. This is the
  # first stage of the protocol, and it accepts exactly the credentials every
  # later stage uses: [harness/seed.sh], [harness/reset_db.sh],
  # [harness/run_cobol_scenario.sh] and [harness/run_python_scenario.sh] all refuse
  # a value wider than 12 for these three names. Accepting one here and refusing it
  # three stages later wastes a full build and reports the fault far from its
  # cause. Worse, without this check an over-long credential reaches the readiness
  # probe, whose refusal is `EX_DATABASE' with the words "credentials rejected" --
  # true of the server's answer but a misdiagnosis of the cause, which is a width
  # breach in the harness's own configuration and not a grant problem at all.
  #
  # ACAS_DB_HOST, ACAS_DB_SOCKET and ACAS_DB_PORT are deliberately NOT in this
  # list: their fields are wider than 12, and the 32-character check above already
  # covers the narrower of each pair.
  for name in ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD; do
    value="${!name-}"
    if (( ${#value} > 12 )); then
      acas_die "$EX_PRECONDITION" \
        "$name is ${#value} characters long; the RDB-Data field is pic x(12)." \
        'A longer value is silently truncated into DB-Schema / DB-UName /' \
        'DB-UPass and the COBOL side then fails to authenticate -- which the' \
        'readiness probe would report as "credentials rejected", naming the' \
        'symptom rather than this width breach.' \
        '[copybooks/wsfnctn.cob:L56-L62]' \
        '[common/glbatchMT.cbl:L402-L425]'
    fi
  done

  # Canonicalised AFTER the 32-character width check above, so an over-long
  # value is still rejected on width exactly as before.
  ACAS_DB_PORT="$(( 10#$ACAS_DB_PORT ))"

  # Decided HERE, before anything connects, and not lazily on first use -- see
  # acas_assert_transport_policy for why the ordering matters.
  acas_assert_transport_policy

  acas_log "ACAS_REPO  = $ACAS_REPO (read-only checkout; the specification)"
  acas_log "ACAS_BUILD = $ACAS_BUILD (writable build tree; every artifact lands here)"
  acas_log "ACAS_DATA  = $ACAS_DATA"
  acas_log "ACAS_OUT   = $ACAS_OUT"
  # A CATEGORY and a FINGERPRINT, never the topology. See
  # acas_target_description: the transcript of a build is retained evidence, and a
  # topology triple in it is a map of the deployment plus half a credential.
  acas_log "database   = $(acas_target_description)"
  if [[ -n "${ACAS_DB_SOCKET-}" ]]; then
    # The PRESENCE of a socket is what changes behaviour downstream (it makes the
    # target local, which acas_target_category already reports); the PATH does not.
    acas_log 'unix socket = present (the path is not printed; DBSOCKET takes it from the environment)'
  else
    acas_log 'unix socket = (empty; DBSOCKET=NULL will be written -- TCP only)'
  fi
  acas_note 'no account name, host, port or schema is printed: the transcript is retained evidence'
  acas_note 'the password is never printed, never logged and never passed in argv'
}

# THE BUILD TREE'S OWN MARKER.  Written by acas_prepare_build_tree
# immediately after a successful copy, and required by
# acas_assert_clearable_build_tree before any recursive clear of a directory that
# HOLDS DATA - that is, one containing a non-directory entry at any depth. A tree
# that is empty, or that holds only directories and therefore no data at all, is
# cleared without it. The marker is the one control that distinguishes "this is a
# build tree this harness made" from "this is a directory that merely satisfies
# every structural test", and it is what makes a mis-set ACAS_BUILD pointed at
# someone's populated volume fail closed instead of clearing it.
readonly ACAS_BUILD_MARKER='.acas-build-oracle-tree'

# Guard a path before it is used as the target of a recursive operation. A
# mis-set ACAS_BUILD is the one configuration error that could destroy something
# irreplaceable, so the checks are deliberately paranoid.
acas_assert_safe_build_path() {
  local path="$1"
  local repo_real path_real
  path_real="$(readlink -f "$path" 2>/dev/null || printf '%s' "$path")"
  repo_real="$(readlink -f "$ACAS_REPO" 2>/dev/null || printf '%s' "$ACAS_REPO")"

  # THE RAW VALUE, not only the resolved one. `readlink -f' canonicalises
  # a relative path against the CURRENT directory, so `ACAS_BUILD=build' arrives
  # here as an absolute $path_real and satisfied this test - while the recursive
  # clear in acas_prepare_build_tree targets the UNRESOLVED "$ACAS_BUILD". The
  # guard would then have judged $PWD/build at assertion time and the delete would
  # have hit whatever $PWD/build meant at deletion time. Requiring the value itself
  # to be absolute is what makes "the path I checked" and "the path I delete" the
  # same path, which is the whole point of re-asserting before the delete.
  [[ "$path" == /* ]] || acas_die "$EX_BUILDTREE" \
    "ACAS_BUILD must be an absolute path; got '$path'." \
    'A relative value is resolved against the current directory, which is not' \
    'necessarily the same directory when the recursive clear runs.'
  [[ "$path_real" == /* ]] || acas_die "$EX_BUILDTREE" \
    "ACAS_BUILD must be an absolute path; got '$path'."
  [[ "$path_real" != '/' ]] || acas_die "$EX_BUILDTREE" \
    'ACAS_BUILD must not be the filesystem root.'
  # A one-component path is normally refused, because clearing something like
  # /usr or /home would be catastrophic. The Compose stack, however, hands this
  # script exactly such a path on purpose: harness/docker-compose.yml mounts the
  # named volume `acas_build' at /build and both that file and
  # harness/Dockerfile.gnucobol export ACAS_BUILD=/build. This function's own
  # caller assumes it too -- acas_prepare_build_tree deletes only the CHILDREN
  # of $ACAS_BUILD precisely "because the directory is a mount point in the
  # Compose stack". Refusing /build outright therefore made the script
  # unrunnable in the only topology it ships with (exit 67 at the first
  # precondition), so a top-level path is accepted under two conditions that
  # together make it as safe as a deeper one:
  #   1. it is a DEDICATED MOUNT POINT -- its device differs from its parent's,
  #      i.e. a volume was mounted there, so clearing it cannot reach the image
  #      filesystem; and
  #   2. it is not one of the distribution's own top-level directories.
  # Every other guard in this function still applies unchanged.
  # CWE-73.  THE OTHER DECLARED MOUNTS ARE REFUSED BY IDENTITY, FIRST.
  # WITHOUT this check the top-level exception below accepts ANY dedicated mount point
  # that is not a distribution directory, and harness/docker-compose.yml mounts THREE such volumes on this
  # service - `acas_build:/build', `acas_data:/data' and `acas_out:/out'
  # [harness/docker-compose.yml "/repo is READ-ONLY"] - all four paths being
  # exported as environment variables side by side, under that file's
  # "ENVIRONMENT -- the canonical ACAS_* contract" heading. So a single mistyped or
  # copy-pasted assignment, `ACAS_BUILD=$ACAS_DATA', passed every guard and then
  # had its children recursively deleted: the seeded fixtures, or the evidence a
  # completed comparison had just written.
  #
  # Compared by RESOLVED PATH and in BOTH DIRECTIONS, never by string or by
  # component count: a symlink, a trailing slash or a `/data/../data' spelling all
  # collapse under readlink, and containment either way is as destructive as
  # equality. Skipped when a variable is unset so this function stays usable
  # before `acas_assert_environment' has run.
  local sibling sibling_real
  for sibling in ACAS_DATA ACAS_OUT; do
    [[ -n "${!sibling-}" ]] || continue
    sibling_real="$(readlink -f "${!sibling}" 2>/dev/null || printf '%s' "${!sibling}")"
    [[ "$path_real" != "$sibling_real" ]] || acas_die "$EX_BUILDTREE" \
      "ACAS_BUILD ($path_real) is the same directory as $sibling." \
      'This script recursively clears ACAS_BUILD. ACAS_DATA holds the seeded' \
      'fixtures and ACAS_OUT holds the comparison evidence; neither is ever a' \
      'build target. Point ACAS_BUILD at its own volume -- /build in the shipped' \
      'Compose topology.'
    [[ "$path_real" != "$sibling_real"/* ]] || acas_die "$EX_BUILDTREE" \
      "ACAS_BUILD ($path_real) is inside $sibling ($sibling_real)." \
      'Clearing it would delete part of the fixtures or the evidence.'
    [[ "$sibling_real" != "$path_real"/* ]] || acas_die "$EX_BUILDTREE" \
      "$sibling ($sibling_real) is inside ACAS_BUILD ($path_real)." \
      'Clearing the build tree would delete the fixtures or the evidence.'
  done

  if [[ "$path_real" != /*/* ]]; then
    local forbidden
    for forbidden in /bin /boot /dev /etc /home /lib /lib32 /lib64 /libx32 \
                     /media /mnt /opt /proc /root /run /sbin /srv /sys /tmp \
                     /usr /var; do
      [[ "$path_real" != "$forbidden" ]] || acas_die "$EX_BUILDTREE" \
        "ACAS_BUILD ($path_real) is a distribution top-level directory." \
        'This script clears it, and such a directory is never a safe target.'
    done

    local path_dev parent_dev
    path_dev="$(stat -c '%d' "$path_real" 2>/dev/null || printf 'x')"
    parent_dev="$(stat -c '%d' "$(dirname "$path_real")" 2>/dev/null || printf 'y')"
    [[ "$path_dev" != "$parent_dev" ]] || acas_die "$EX_BUILDTREE" \
      "ACAS_BUILD ($path_real) is one component deep and is NOT a mount point." \
      'This script clears it, so a top-level directory is only acceptable when a' \
      'dedicated volume is mounted there, as harness/docker-compose.yml does for' \
      '/build. Either mount a volume at that path or use a deeper one.'

    # A DEDICATED MOUNT POINT IS NOT ENOUGH ON ITS OWN, which is the
    # other half of the finding. Being a mount point says only that a volume is
    # there; it says nothing about WHOSE. A top-level path is therefore accepted
    # only when it is the one THE TOPOLOGY ITSELF DECLARES as the build tree, so
    # the exception cannot be reached by pointing ACAS_BUILD at some other
    # volume-backed top-level directory that happens not to be on the
    # distribution list.
    local declared_real
    declared_real="$(readlink -f "${ACAS_BUILD-}" 2>/dev/null || printf '%s' "${ACAS_BUILD-}")"
    [[ "$path_real" == "$declared_real" ]] || acas_die "$EX_BUILDTREE" \
      "$path_real is one component deep and is not the declared ACAS_BUILD." \
      'The top-level exception exists for exactly one path, the build volume the' \
      'Compose topology mounts at /build. A recursive clear of any other' \
      'volume-backed top-level directory is refused however that volume got there.'
    acas_log "accepted top-level ACAS_BUILD ($path_real): dedicated mount point, and the declared build tree"
  fi
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

# THE GATE THAT STANDS IMMEDIATELY BEFORE THE RECURSIVE CLEAR, and the
# only one that asks WHOSE directory this is rather than what shape it has.
#
# acas_assert_safe_build_path establishes that the path is absolute, is not the
# root, is not a distribution directory, is not ACAS_DATA or ACAS_OUT or the
# checkout in either direction, and - if it is one component deep - is a dedicated
# mount point AND the path the topology declares. Every one of those is a check on
# the path's SHAPE and PROVENANCE. None of them can tell a fresh build volume from
# a populated volume that satisfies the same description, and the finding was
# precisely that a recursive delete must not proceed on a directory this harness
# cannot show it created.
#
# So the clear is admitted in exactly three states, and in no others:
#   * the directory is EMPTY - nothing whatever below it; or
#   * the directory holds DIRECTORIES ONLY, at every depth, and therefore not one
#     byte of anybody's data. This is what the Compose stack actually hands over,
#     because [harness/Dockerfile.gnucobol] creates /build AND /build/bin in the
#     image layer so that $ACAS_BIN resolves, and Docker seeds a fresh named
#     volume from that layer. See the paragraph below; or
#   * it carries $ACAS_BUILD_MARKER, which only acas_prepare_build_tree writes,
#     and only after a copy of the frozen checkout has succeeded.
# Anything else is refused with an exit code and an instruction, never cleared.
#
# WHY "DIRECTORIES ONLY" IS ADMITTED, AND WHY IT DOES NOT WEAKEN THE RULE.
# The rule this guard enforces is that no DATA is destroyed in a tree whose
# provenance the harness cannot establish. A directory with no non-directory
# entry at any depth contains no data by construction: removing it destroys
# nothing that any process wrote and nothing that any operator can miss. The
# earlier form of this guard tested only "is the directory empty", which is a
# proxy for that property, and the proxy was WRONG for the one topology this
# harness ships: the image layer contains the empty directory `bin', so the
# volume Compose hands over is never empty and a first run on a genuinely fresh
# stack was refused - the failure the QA finding recorded, and one whose message
# then told the operator to "point ACAS_BUILD at an empty volume -- /build in the
# shipped Compose topology" when /build WAS that volume. Testing the property
# itself rather than the proxy admits the shipped topology and still refuses, for
# example, a volume holding a single stray file. The refusal threshold is one
# regular file, one symlink, one device node, one socket, one FIFO - anything a
# process could have written.
#
# The test is deliberately `! -type d' rather than `-type f': a symlink is not a
# directory and must count, because `rm -rf' would remove it, and because a
# symlink pointing outside the tree is exactly the kind of thing whose presence
# means "somebody set this up on purpose". An unreadable subdirectory makes
# `find' report a non-zero status, which is treated as "not provably data-free"
# rather than as "no entries found", so a permissions problem also fails closed.
#
# THE MARKER IS NOT SECURITY, IT IS PROVENANCE. A caller who genuinely wants a
# populated directory cleared can create the marker by hand, and that is the point:
# it converts an accident into a deliberate act. Nothing here defends against a
# hostile operator, who could delete the tree without this script.
acas_assert_clearable_build_tree() {
  local path="$1"
  local path_real
  path_real="$(readlink -f "$path" 2>/dev/null || printf '%s' "$path")"

  # Never reached with a path the shape guard has not already accepted; asserted
  # rather than assumed, because this function is the last thing between a
  # configuration mistake and an irreversible delete.
  acas_assert_safe_build_path "$path_real"

  [[ -d "$path_real" ]] || acas_die "$EX_BUILDTREE" \
    "ACAS_BUILD ($path_real) is not a directory."

  if [[ -f "$path_real/$ACAS_BUILD_MARKER" ]]; then
    acas_log "build tree recognised by its marker ($ACAS_BUILD_MARKER); clear permitted"
    return 0
  fi

  # `find -mindepth 1 -maxdepth 1` rather than a glob, so that dot files count and
  # an unreadable directory reports as non-empty rather than as empty.
  local entries
  entries="$(find "$path_real" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null || printf 'x')"
  if [[ -z "$entries" ]]; then
    acas_log "build tree is empty; clear permitted"
    return 0
  fi

  # The provably-data-free case. `find' is run WITHOUT -quit here so that its exit
  # status is meaningful: a traversal error - an unreadable subdirectory, a path
  # that vanished mid-walk - yields a non-zero status, and a non-zero status is
  # treated as "NOT provably data-free" rather than as "no entries found", so a
  # permissions problem fails closed. The assignment sits in the `if' CONDITION,
  # which is the errexit-safe way to read a pipeline's status here: `set +e' /
  # `set -e' around it would briefly disarm the ERR trap installed for the whole
  # script. Output is bounded with `head -c' because a wildly mis-set ACAS_BUILD
  # could be pointed at something enormous and only the fact of a file matters.
  local nondir='' data_free=0
  if nondir="$(find "$path_real" -mindepth 1 ! -type d -print 2>/dev/null | head -c 4096)"; then
    if [[ -z "$nondir" ]]; then
      data_free=1
    fi
  fi
  if (( data_free )); then
    local dirs
    dirs="$(find "$path_real" -mindepth 1 -type d 2>/dev/null | wc -l)"
    acas_log "build tree holds directories only (${dirs} of them) and no file at any depth: it is provably data-free; clear permitted"
    return 0
  fi

  acas_die "$EX_BUILDTREE" \
    "ACAS_BUILD ($path_real) holds files and carries no $ACAS_BUILD_MARKER marker." \
    'This script is about to delete every child of that directory, and it will' \
    'not do so to a directory it cannot show it created. An empty tree, or a tree' \
    'of empty directories such as the /build volume the shipped Compose topology' \
    'hands over, is cleared without ceremony; a tree that already holds files is' \
    'not. Either point ACAS_BUILD at a fresh volume, or pass --no-refresh to' \
    'build in place without clearing, or, if you really do mean to clear this' \
    "tree, create the marker file yourself: touch $path_real/$ACAS_BUILD_MARKER" \
    "$(acas_build_tree_occupants "$path_real")"
}

# The occupant summary the refusal above quotes. It exists so that the operator
# is told WHAT stopped the clear rather than only that something did: with a
# stray file the answer is usually obvious once named, and with a populated
# volume the first few paths identify whose volume it is. Bounded to five paths
# because the message is a diagnostic, not a listing, and because a mis-set
# ACAS_BUILD may be pointed at something very large.
acas_build_tree_occupants() {
  local path_real="$1"
  # Named `occupants' rather than the obvious `found': `found' is already used as
  # a scalar counter by four artifact-census helpers further down, and shellcheck
  # reports SC2178/SC2128 across the whole file when one name is an array in one
  # function and a counter in another. The warning is a false positive -- both are
  # `local' -- but the script is kept shellcheck-clean, so the name gives way.
  #
  # THE `|| true' IS LOAD-BEARING, not defensive noise. `head -5' closes its input
  # after the fifth line, so `sort' takes SIGPIPE and the pipeline exits 141 under
  # `pipefail'. With the script's `set -E' and its ERR trap that surfaced as
  # "unexpected failure ... failing command: head -5" printed ABOVE the refusal it
  # was helping to write - alarming, and about nothing. Testing the pipeline's
  # status makes the truncation what it is: the intended end of a bounded read.
  local -a occupants=()
  local line
  while IFS= read -r line; do
    occupants+=( "$line" )
  done < <(find "$path_real" -mindepth 1 ! -type d -print 2>/dev/null | LC_ALL=C sort | head -5 || true)
  if (( ${#occupants[@]} == 0 )); then
    printf '%s' 'the tree could not be traversed to name its occupants (a permissions problem is the usual cause).'
    return 0
  fi
  printf 'first file(s) found: %s' "${occupants[0]}"
  local i
  for (( i = 1; i < ${#occupants[@]}; i++ )); do
    printf ', %s' "${occupants[$i]}"
  done
}

# THE ONE PLACE A BUILD-TREE SCRATCH DIRECTORY IS REMOVED.
#
# Four steps each keep a scratch directory inside the build tree and clear it
# before use - the unpacked preSQL package, the two compile working directories
# and the link proof. Each did its own bare `rm -rf -- "$ACAS_BUILD/.acas-..."'.
# Those were already far safer than the tree clear, because the target is a fixed
# dot-named CHILD rather than the directory itself, so even a wildly mis-set
# ACAS_BUILD could only lose a directory of that exact name. The finding's
# instruction was nonetheless to "recheck before deletion", and four ad-hoc
# recursive removes are four places a future edit can get wrong, so they are
# funnelled through here and each one now re-asserts the shape guard first.
#
# The name is required to be a SINGLE component beginning with `.acas-', which is
# what makes traversal impossible: `..', `/', an absolute path and an empty name
# are all refused rather than joined.
acas_remove_build_scratch() {
  local name="$1"

  [[ "$name" == .acas-* ]] || acas_die "$EX_BUILDTREE" \
    "refusing to remove build scratch '$name': the name must begin with .acas-."
  [[ "$name" != */* && "$name" != *..* ]] || acas_die "$EX_BUILDTREE" \
    "refusing to remove build scratch '$name': it must be a single path component."

  # Re-assert immediately before the delete, never only at resolution time.
  acas_assert_safe_build_path "$ACAS_BUILD"

  local target="$ACAS_BUILD/$name"
  [[ ! -e "$target" ]] || rm -rf -- "$target" || acas_die "$EX_BUILDTREE" \
    "could not remove the scratch directory $target."
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
  # cannot be written even by accident.
  local probe="$ACAS_REPO/.acas-build-oracle-write-probe"
  if : > "$probe" 2>/dev/null; then
    rm -f "$probe" 2>/dev/null || true
    acas_die "$EX_PRECONDITION" \
      "ACAS_REPO ($ACAS_REPO) is WRITABLE; it must be mounted read-only." \
      'A writable checkout is the one configuration error that can silently' \
      'destroy the specification: [common/comp-common.sh:L25] regenerates every' \
      'common/*MT.cbl with presql2, and presql2 truncates its output at' \
      '[presql2-latest.zip:presql2-package/presql2.cbl:L543] BEFORE validating its parameters at' \
      '[presql2-latest.zip:presql2-package/presql2.cbl:L759]. Mount it "../:/repo:ro" as' \
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

  # Build logs live under $ACAS_OUT/build/.
  ACAS_LOG_DIR="$ACAS_OUT/build"
  mkdir -p "$ACAS_LOG_DIR"
  # 0700, for the same reason harness/reset_db.sh, seed.sh and
  # run_cobol_scenario.sh all narrow their own output directories.
  chmod 700 -- "$ACAS_LOG_DIR" 2>/dev/null || true
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

  # cobc MUST be 3.2 -- the compiler the maintainer targets. A different
  # release is a different oracle, and the oracle is the specification.
  local -a deadline=()
  acas_deadline_prefix "$ACAS_TIMEOUT_PROBE"
  deadline=("${ACAS_DEADLINE_ARGV[@]}")

  local cobc_line
  cobc_line="$("${deadline[@]}" cobc --version < /dev/null 2>&1 | head -n 1)"
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

  local cobc_info isam_line
  cobc_info="$("${deadline[@]}" cobc --info 2>&1 || true)"
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

  [[ -e "$ACAS_FROZEN_MYSQL_PREFIX/lib/libmysqlclient.so" ]] \
    || acas_die "$EX_PRECONDITION" \
      "$ACAS_FROZEN_MYSQL_PREFIX/lib/libmysqlclient.so is absent." \
      'Every frozen compile line linking -lmysqlclient would fail.' \
      '[common/comp-common.sh:L26]'
  [[ -f "$ACAS_FROZEN_MYSQL_PREFIX/include/mysql.h" ]] \
    || acas_die "$EX_PRECONDITION" \
      "$ACAS_FROZEN_MYSQL_PREFIX/include/mysql.h is absent." \
      'cobmysqlapi38.c includes <mysql.h> and the recovered rule compiles with' \
      '-I/usr/local/mysql/include. [presql2-latest.zip:presql2-package/cobmysqlapi38.sh]'
  acas_log "MySQL client prefix: $ACAS_FROZEN_MYSQL_PREFIX (lib + headers present)"

  # ACAS_MYSQL_PREFIX is published by the image for documentation. It cannot
  # override the frozen literal, so disagreement is reported rather than
  # obeyed.
  if [[ -n "${ACAS_MYSQL_PREFIX-}" && "${ACAS_MYSQL_PREFIX}" != "$ACAS_FROZEN_MYSQL_PREFIX" ]]; then
    acas_warn \
      "ACAS_MYSQL_PREFIX=${ACAS_MYSQL_PREFIX} disagrees with the frozen literal ${ACAS_FROZEN_MYSQL_PREFIX}; the frozen scripts hard-code the literal, so it is used regardless."
  fi
}

acas_assert_loader_configuration() {
  acas_stage 'Preconditions 4/5: shared-library loader paths'

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
# target has earned. Populates ACAS_BUILD_TLS_VARIANTS, most secure first, or
# aborts.
acas_assert_transport_policy() {
  local ca="${ACAS_DB_TLS_CA-}"
  ACAS_BUILD_TLS_VARIANTS=()

  if [[ -n "$ca" ]]; then
    [[ -r "$ca" ]] || acas_die "$EX_PRECONDITION" \
      "ACAS_DB_TLS_CA names a file that cannot be read: $ca" \
      'It must be the PEM bundle the server certificate chains to.'
    ACAS_BUILD_TLS_VARIANTS+=("--ssl-ca=$ca --ssl-verify-server-cert")
  fi

  if acas_target_is_local; then
    ACAS_BUILD_TLS_VARIANTS+=('--skip-ssl')
    acas_note 'transport: local target, so plaintext is permitted'
    return 0
  fi

  if acas_plaintext_declared; then
    acas_warn 'ACAS_DB_ALLOW_PLAINTEXT permits plaintext to a NON-LOCAL server; the build credential is unprotected'
    ACAS_BUILD_TLS_VARIANTS+=('--skip-ssl')
    return 0
  fi

  if [[ -z "$ca" ]]; then
    acas_die "$EX_PRECONDITION" \
      "the target ($(acas_target_description)) is not local and no verified TLS is configured." \
      'The credentialed probe authenticates with the same account presql2 uses, so' \
      'the connection must be protected. Either set ACAS_DB_TLS_CA to the PEM' \
      'bundle the server certificate chains to, or -- if this really is an isolated' \
      'harness network such as the private Compose network' \
      '[harness/docker-compose.yml] -- declare it with ACAS_DB_ALLOW_PLAINTEXT=1.' \
      'It is NOT downgraded silently: that was the defect.'
  fi

  acas_note 'transport: verified TLS required (CA supplied, certificate and hostname checked)'
  return 0
}

# TCP reachability, using python3 because it is guaranteed present by the
# toolchain assertion and needs no client binary or credentials.
acas_db_tcp_probe() {
  # The port range is asserted in acas_assert_environment, before anything
  # connects, so `int(sys.argv[2])' here cannot receive 99999 and fail
  # with an OverflowError that names neither the variable nor the value.
  acas_deadline_prefix "$ACAS_TIMEOUT_PROBE"
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

# A genuinely credentialed probe -- this is what presql2 will actually need.

# The password goes through MYSQL_PWD rather than argv so it never appears in
# the process list.
acas_db_credentialed_probe() {
  ACAS_DB_PROBE_DIAG=''
  local dbname="${ACAS_PRESQL2_DBNAME:-information_schema}"
  local client out rc started elapsed

  # EVERY client invocation below runs under ACAS_TIMEOUT_PROBE.
  local -a deadline=()
  acas_deadline_prefix "$ACAS_TIMEOUT_PROBE"
  deadline=("${ACAS_DEADLINE_ARGV[@]}")

  # Unreachable unless acas_assert_transport_policy was skipped or changed: it
  # either records at least one permitted variant or aborts with a named cause.
  if (( ${#ACAS_BUILD_TLS_VARIANTS[@]} == 0 )); then
    acas_die "$EX_PRECONDITION" \
      'no permitted client transport for this target.' \
      'acas_assert_transport_policy must run before any probe; see TRANSPORT' \
      'SECURITY.'
  fi

  # Layer 1: a real SQL client executing a real statement.
  for client in mariadb mysql; do
    if acas_have "$client"; then
      local variant flag
      for variant in "${ACAS_BUILD_TLS_VARIANTS[@]}"; do
        local -a argv=("${deadline[@]}" "$client" '--protocol=TCP')
        if [[ -n "$variant" ]]; then
          # A variant may carry two words (--ssl-ca=...
          # --ssl-verify-server-cert), so it is split deliberately -- each flag
          # must be its own argv element.
          for flag in $variant; do
            argv+=("$flag")
          done
        fi
        argv+=(
          "--host=$ACAS_DB_HOST" "--port=$ACAS_DB_PORT"
          "--user=$ACAS_DB_USER" '--batch' '--skip-column-names'
          "--database=$dbname" '--execute=select 1'
        )
        out=''
        rc=0
        started="$SECONDS"
        out="$(MYSQL_PWD="$ACAS_DB_PASSWORD" "${argv[@]}" < /dev/null 2>&1)" || rc=$?
        elapsed=$(( SECONDS - started ))
        if (( rc == 0 )); then
          return 0
        fi
        if acas_is_timeout_status "$rc" "$elapsed" "$ACAS_TIMEOUT_PROBE"; then
          out="$client did not answer within ${ACAS_TIMEOUT_PROBE}s and was terminated (raise ACAS_TIMEOUT_PROBE). ${out}"
        fi
        ACAS_DB_PROBE_DIAG="$out"
      done
      # Every SSL variant of a real client failed.
      if [[ "$ACAS_DB_PROBE_DIAG" == *'Access denied'* ]]; then
        return 2
      fi
      return 1
    fi
  done

  # Layer 2: no SQL client, so use an admin client -- `status', never `ping',
  # for the reason given above.
  for client in mariadb-admin mysqladmin; do
    if acas_have "$client"; then
      local variant flag
      for variant in "${ACAS_BUILD_TLS_VARIANTS[@]}"; do
        local -a argv=("${deadline[@]}" "$client" '--protocol=TCP')
        if [[ -n "$variant" ]]; then
          for flag in $variant; do
            argv+=("$flag")
          done
        fi
        argv+=(
          "--host=$ACAS_DB_HOST" "--port=$ACAS_DB_PORT"
          "--user=$ACAS_DB_USER" 'status'
        )
        out=''
        rc=0
        started="$SECONDS"
        out="$(MYSQL_PWD="$ACAS_DB_PASSWORD" "${argv[@]}" < /dev/null 2>&1)" || rc=$?
        elapsed=$(( SECONDS - started ))
        if (( rc == 0 )); then
          return 0
        fi
        if acas_is_timeout_status "$rc" "$elapsed" "$ACAS_TIMEOUT_PROBE"; then
          out="$client did not answer within ${ACAS_TIMEOUT_PROBE}s and was terminated (raise ACAS_TIMEOUT_PROBE). ${out}"
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
  # connection. `presql2.cbl:L784' performs MYSQL-1000-OPEN, which reaches
  # MySQL_real_connect at `cobmysqlapi38.c:L500-L531'.
  local timeout="${ACAS_DB_WAIT_TIMEOUT:-180}"
  if [[ ! "$timeout" =~ ^[0-9]+$ ]]; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_WAIT_TIMEOUT must be numeric; got '$timeout'."
  fi

  local interval=3 elapsed=0
  acas_log "waiting up to ${timeout}s for $(acas_target_description) to accept connections"
  while ! acas_db_tcp_probe; do
    if (( elapsed >= timeout )); then
      acas_die "$EX_DATABASE" \
        "the $(acas_target_description) database did not accept a TCP connection within ${timeout}s." \
        'The host and port are deliberately not printed: read them from' \
        'ACAS_DB_HOST and ACAS_DB_PORT in this environment.' \
        'Step 4 cannot run without it: [common/comp-common.sh:L25] invokes presql2,' \
        'which opens a live connection at [presql2-latest.zip:presql2-package/presql2.cbl:L784].' \
        'Start the service (docker compose -f harness/docker-compose.yml up -d mariadb)' \
        'and wait for its healthcheck, or raise ACAS_DB_WAIT_TIMEOUT.'
    fi
    sleep "$interval"
    elapsed=$(( elapsed + interval ))
  done
  acas_log "TCP reachable after ${elapsed}s"

  # Authentication gate. An open port is not readiness.
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
          acas_log "authenticated against $(acas_target_description), probe schema ${ACAS_PRESQL2_DBNAME:-information_schema} -- server is ready"
        else
          acas_log "authenticated against $(acas_target_description) after a further ${elapsed}s"
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
            "the $(acas_target_description) database REJECTED the credentials it was given." \
            "The server is alive and accepting connections, so this is a credential" \
            "or grant problem, not a readiness problem -- waiting longer will not fix it." \
            "presql2 authenticates with exactly these values via read_params" \
            '[presql2-latest.zip:presql2-package/cobmysqlapi38.c:L114-L176], so step 4 would fail on every' \
            "one of the 28 bridges in [common/comp-common.sh:L25]." \
            "Check ACAS_DB_USER and ACAS_DB_PASSWORD in this environment -- neither is" \
            "printed here -- and that the account is granted access to" \
            "${ACAS_PRESQL2_DBNAME:-information_schema} and to the target schema." \
            "$(acas_diag_summary "$ACAS_DB_PROBE_DIAG")"
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
            'read_params [presql2-latest.zip:presql2-package/cobmysqlapi38.c:L114-L176], so step 4' \
            'would fail. Check that the server has finished initialising.' \
            "$(acas_diag_summary "$ACAS_DB_PROBE_DIAG")"
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

# BUILD TREE -- DEVIATION 1 of 6: the compile runs in $ACAS_BUILD, not where
# the frozen scripts live. Not a preference but a hard requirement.

# The WHOLE checkout is copied, and that is the safe choice.

# =============================================================================
# THE SOURCE-TRANSFORMATION REGISTER
#
# NINE SHIMS BELOW EDIT THE BUILD COPY OF FROZEN SOURCES, and this register is what
# makes that a DISCLOSED fact rather than a hidden one. An attestation describing only
# the two identity substitutions -- a replacement preSQL archive and a redirected
# cobmysqlapi.o -- would publish `overrides-used no' for a build whose compiled COBOL
# differs from the checkout in nine places. An empty diff drawn
# against such a build compares Python to a PATCHED oracle, and calling that "the
# frozen behavioural specification" is the one claim this project must never make.
#
# WHY THE SHIMS EXIST AT ALL, stated once so the disclosure is readable rather than
# alarming. Every one of them is a CONNECTIVITY or SCOPE repair without which the
# compiled cycle cannot reach MySQL, and none of them alters an accounting
# computation, a posting order, a control total or a rejection path. Six restore the
# IF scope that a stray period closed early; three propagate or retain a database
# connection the frozen code drops; one supplies an archive member the frozen bridges
# COPY and the checkout does not contain. Each one's reason is recorded beside its
# path below, and the frozen checkout itself is never written.
#
# WHAT IS PUBLISHED. For every registered path the attestation carries the FROZEN
# checkout digest and the BUILD COPY digest, so a reader can verify the difference
# independently and diff the two trees themselves. `oracle-source-is-frozen' states
# the conclusion in one word.
#
# WHY A DECLARED LIST *AND* A MEASURED CHECK. The list is what the attestation
# publishes; the measurement is what stops the list going stale. On any build that
# refreshes the tree, the sources are digested immediately before the shim block and
# immediately after it, and the set of paths that changed must EQUAL this register. A
# tenth shim added without a register entry therefore fails the build instead of
# compiling silently into the oracle.
#
# Format: <repo-relative path>|<reason>
readonly -a ACAS_SOURCE_TRANSFORMS=(
  'copybooks/ACAS-SQLstate-error-list.cob|supplies the comment-only archive member the 22 frozen *MT bridges COPY from their Remarks paragraphs and the checkout does not contain'
  'common/glbatchLD.cbl|restores the IF scope of both flat-file open-error branches, which a period on the first MOVE closed early'
  'common/glpostingLD.cbl|restores the IF scope of both flat-file open-error branches'
  'common/irsnominalLD.cbl|restores the IF scope of both flat-file open-error branches'
  'common/irspostingLD.cbl|restores the IF scope of both flat-file open-error branches'
  'common/nominalLD.cbl|restores the IF scope of both flat-file open-error branches'
  'common/otm5LD.cbl|restores the IF scope of both flat-file open-error branches'
  'common/dfltLD.cbl|propagates the six RDBMS credential fields of SYSTEM-REC into File-Access before the bridge call, which this loader reads and never copies'
  'common/finalLD.cbl|propagates the six RDBMS credential fields of SYSTEM-REC into File-Access before the bridge call'
  'common/sys4LD.cbl|propagates the six RDBMS credential fields of SYSTEM-REC into File-Access before the bridge call'
  'copybooks/mysql-procedures.cpy|retains the process connection across Mysql-1980-Close so one handler closing does not invalidate another handler still-open bridge state'
  'copybooks/mysql-procedures-2.cpy|retains the process connection across Mysql-1980-Close'
  'general/general.cbl|retains the declared RDB mode in the system record the menu rewrites on exit, so a run cannot silently fall back to indexed files'
  'sales/sales.cbl|retains the declared RDB mode in the system record the menu rewrites on exit'
  'purchase/purchase.cbl|retains the declared RDB mode in the system record the menu rewrites on exit'
  'irs/irs030.cbl|retains the shared connection until the end-of-job transfer cleanup, which the frozen EOJ closes first'
  # The 25 numbered file handlers, each carrying BOTH handler shims: the connection
  # refresh and the reply-pair reset. `acas000.cbl` takes only the second, because it
  # is the five-way dispatcher and copies no credentials of its own.
  'common/acas000.cbl|resets the FS-Reply/We-Error pair before each dispatch, so a caller cannot read the previous call reply'
  'common/acas004.cbl|refreshes the six DB-Data fields from the current caller on every RDBMS dispatch, which the frozen one-time guard leaves blank for a second caller, and resets the reply pair before each dispatch'
  'common/acas005.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas006.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas007.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas008.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas010.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas011.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas012.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas013.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas014.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas015.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas016.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas017.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas019.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas022.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas023.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas026.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas029.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas030.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acas032.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acasirsub1.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acasirsub3.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acasirsub4.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
  'common/acasirsub5.cbl|refreshes DB-Data per caller and resets the reply pair before each dispatch'
)

#: The source extensions the frozen build consumes, and therefore the ones the
#: completeness measurement covers.
readonly -a ACAS_SOURCE_TRANSFORM_EXTENSIONS=('*.cbl' '*.cob' '*.cpy' '*.scb')

#: The directories those sources live in. `copybooks` first because the shim that
#: CREATES a file writes there.
readonly -a ACAS_SOURCE_TRANSFORM_DIRS=(copybooks common general sales purchase irs stock)

# acas_in_list <needle> <haystack>...  0 when the first argument equals a later one.
acas_in_list() {
  local needle="$1"
  shift
  local candidate
  for candidate in "$@"; do
    [[ "$candidate" == "$needle" ]] && return 0
  done
  return 1
}

# acas_source_digest_listing  A sorted `<digest>  <relpath>` listing of every build-tree
# source. Written to stdout; an unreadable file is listed as UNREADABLE so it cannot
# vanish from the comparison.
acas_source_digest_listing() {
  local dir pattern
  {
    for dir in "${ACAS_SOURCE_TRANSFORM_DIRS[@]}"; do
      for pattern in "${ACAS_SOURCE_TRANSFORM_EXTENSIONS[@]}"; do
        find "$ACAS_BUILD/$dir" -maxdepth 1 -type f -name "$pattern" -print 2>/dev/null
      done
    done
  } | LC_ALL=C sort | while IFS= read -r path; do
    if [[ -r "$path" ]]; then
      printf '%s  %s\n' "$(sha256sum "$path" | cut -d' ' -f1)" "${path#"$ACAS_BUILD/"}"
    else
      printf 'UNREADABLE  %s\n' "${path#"$ACAS_BUILD/"}"
    fi
  done
}

# acas_assert_transform_register_complete <before-listing> <after-listing>
#
# The measurement that keeps ACAS_SOURCE_TRANSFORMS honest. Only meaningful on a
# refreshed tree: the shims are idempotent, so on a --no-refresh build over an already
# prepared tree nothing changes and there is nothing to compare.
acas_assert_transform_register_complete() {
  local before="$1" after="$2"
  local -a measured=() registered=() unregistered=() unmeasured=()
  local entry path

  mapfile -t measured < <(
    LC_ALL=C comm -3 <(LC_ALL=C sort "$before") <(LC_ALL=C sort "$after") \
      | awk '{ print $NF }' | LC_ALL=C sort -u
  )
  # The APPLIED register, not the catalogue: in frozen mode nothing was applied, so
  # `measured` must also be empty and any difference is an undisclosed patch.
  for entry in "${ACAS_SOURCE_TRANSFORMS_APPLIED[@]}"; do
    registered+=("${entry%%|*}")
  done

  for path in "${measured[@]}"; do
    [[ -n "$path" ]] || continue
    acas_in_list "$path" "${registered[@]}" || unregistered+=("$path")
  done
  for path in "${registered[@]}"; do
    acas_in_list "$path" "${measured[@]}" || unmeasured+=("$path")
  done

  if (( ${#unregistered[@]} )); then
    acas_die "$EX_BUILDTREE" \
      "build-copy sources changed that this build did not declare it would change:" \
      "  $(printf '%s ' "${unregistered[@]}")" \
      'Every source transformation must be REGISTERED, because the attestation' \
      'publishes the register and a transformation missing from it is an undisclosed' \
      'behavioural patch in the oracle. Add the path and its' \
      'reason to ACAS_SOURCE_TRANSFORMS.' \
      'IF THIS IS A FROZEN BUILD the register is empty by design and ANY change is' \
      'unregistered: something modified the build copy outside the shim block, and a' \
      'frozen oracle is exactly what that destroys.'
  fi
  if (( ${#unmeasured[@]} )); then
    acas_die "$EX_BUILDTREE" \
      "this build declared source transformations it did not make:" \
      "  $(printf '%s ' "${unmeasured[@]}")" \
      'A register entry with no transformation behind it overstates what was patched,' \
      'which is as misleading as omitting one. Remove the stale entry, or fix the shim.'
  fi
  if (( ${#registered[@]} == 0 )); then
    acas_log 'verified by MEASUREMENT: zero source transformations; the build copy is byte-for-byte the frozen checkout'
  else
    acas_log "verified: ${#registered[@]} declared source transformation(s), and no others were made"
  fi
}

# =============================================================================
# THE SQLSTATE COMPATIBILITY INCLUDE IS GENERATED HERE, INTO THE BUILD COPY ONLY
#
# 22 frozen `common/*MT.cbl` bridges and their 22 `.scb` sources
# `copy "ACAS-SQLstate-error-list.cob"' from inside their Identification Division
# REMARKS paragraph -- for example [common/glpostingMT.cbl:L160], which sits between
# `identification division.' at L9 and `environment division.' at L201, a region in
# which only comments are legal. The member is absent from the checkout and from
# presql2-latest.zip alike, so no bridge compiles without something at that name and
# the default frozen build fails with exit 74 (README section 8.7).
#
# IT IS NOT A REPOSITORY FILE, AND MUST NOT BECOME ONE (rules R-3,
# R-4 and AAP section 0.8.1). Committing it as
# `harness/copybook-shims/ACAS-SQLstate-error-list.cob' would add a file the Agent Action
# Plan's harness inventory does not name, so the text is EMITTED here, at build time,
# straight into the writable build copy under $ACAS_BUILD. Two properties follow, and
# both are the point rather than a side effect:
#
#   * The frozen tree is untouched. Writing the member into `copybooks/' would be a
#     fabricated frozen source -- forbidden even if an authentic copy were obtained,
#     because AAP section 0.8.1 makes any diff touching `copybooks/*.cob' a defect.
#   * There is no second place for the text to drift to. A committed shim is a file a
#     reader can mistake for archive material; a generated one carries its own
#     disclosure into the build log every time it is produced.
#
# WHAT IT MAY CONTAIN: blank lines and `*>' comments, and nothing else. That is what
# makes it behaviour-neutral -- measured, not assumed: the generated C is
# byte-identical with this include, with a zero-byte member, and with different
# comment text. The emitted file is re-read and CHECKED against that grammar below,
# so a future edit to the heredoc that introduced executable text fails the build
# rather than silently patching the specification.
# =============================================================================
acas_install_sqlstate_comment_shim() {
  local target="$ACAS_BUILD/copybooks/ACAS-SQLstate-error-list.cob"

  #  GENERATED, not copied. Every line is a comment or blank, and the terminating
  #  newline matters: GnuCOBOL otherwise emits a missing-newline warning once per
  #  bridge that includes it.
  if ! cat > "$target" <<'SQLSTATE_SHIM_EOF'
      *> Compatibility include for the missing ACAS SQLSTATE remarks list.
      *>
      *> GENERATED by harness/build_oracle.sh into the writable build copy only.
      *> It is NOT part of the frozen checkout and is not a repository file: the
      *> archive member this name refers to is absent from the checkout and from
      *> presql2-latest.zip alike, and writing it into copybooks/ would be a
      *> fabricated frozen source (rules R-3 and R-4, Agent Action Plan 0.8.1).
      *>
      *> Every frozen COPY site expands this file inside the Identification
      *> Division's Remarks paragraph, before any Data Division begins.  The
      *> executable SQLSTATE handling remains in mysql-procedures.cpy; this
      *> include therefore contains comments only and changes no COBOL behavior.
      *>
SQLSTATE_SHIM_EOF
  then
    acas_die "$EX_BUILDTREE" \
      "could not write the SQLSTATE remarks shim into $target." \
      'The 22 frozen *MT bridges COPY this absent archive member from their' \
      'Identification Division Remarks paragraphs, so no bridge compiles without it.'
  fi

  # Fail closed if the generated include ever acquires executable text. Its safety
  # rests on being semantically inert: blank lines and *> comments are the entire
  # allowed grammar. Checked on the MATERIALISED file, so the guarantee covers what
  # the compiler will actually read.
  if grep -Ev '^[[:space:]]*(\*>.*)?$' "$target" | grep -q .; then
    acas_die "$EX_BUILDTREE" \
      "$target contains text other than blank lines and COBOL comments." \
      'The compatibility include must remain comment-only because its COPY sites' \
      'are documentation gaps, not missing executable SQLSTATE logic. Correct the' \
      'heredoc in acas_install_sqlstate_comment_shim.'
  fi

  chmod 0644 -- "$target" || acas_die "$EX_BUILDTREE" \
    "could not set the SQLSTATE remarks shim mode on $target."

  #  DISCLOSED EVERY TIME IT IS PRODUCED, because this is the transformation that
  #  makes an otherwise unbuildable specification compile, and a reader of the build
  #  log must be able to see that it happened without going looking for it.
  acas_log 'GENERATED the comment-only SQLSTATE remarks include into the build copy:'
  acas_log "  $target"
  acas_log '  The archive member of that name is ABSENT from the frozen checkout and from'
  acas_log '  presql2-latest.zip; 22 frozen common/*MT bridges COPY it from their REMARKS'
  acas_log '  paragraph, so without it no bridge compiles (exit 74). It is comments only,'
  acas_log '  verified by re-reading it, and it is written ONLY under $ACAS_BUILD -- the'
  acas_log '  frozen copybooks/ tree is never written to, because a fabricated frozen'
  acas_log '  source would breach rules R-3 and R-4 whatever it contained.'
  acas_log '  It is REGISTERED as a source transformation, so the provenance attestation'
  acas_log '  records this build as TRANSFORMED and no verdict from it is a parity claim.'
}

acas_install_loader_open_scope_shims() {
  local common_dir="$ACAS_BUILD/common"

  # Six in-scope loaders put a period on the first MOVE inside each of their two
  # flat-file-open error branches. In COBOL the period ends the IF sentence, so
  # the diagnostic, CLOSE and GOBACK that follow run unconditionally even after a
  # successful OPEN. The frozen sources remain untouched; this build-copy
  # transformation restores the branch scope the surrounding source states and
  # is required before those loaders can seed any relational comparison.
  if ! python3 - "$common_dir" <<'PY'
from pathlib import Path
import sys

common = Path(sys.argv[1])
loaders = (
    "glbatchLD.cbl",
    "glpostingLD.cbl",
    "irsnominalLD.cbl",
    "irspostingLD.cbl",
    "nominalLD.cbl",
    "otm5LD.cbl",
)
conditions = ("FS-Reply = 35", "FS-Reply not = zero")

for name in loaders:
    path = common / name
    if not path.is_file():
        raise SystemExit(f"missing in-scope loader in build tree: {path}")
    text = path.read_text(encoding="utf-8")
    for condition in conditions:
        broken = (
            f"     if       {condition}\n"
            "              move Prog-Name to SO-Print.\n"
        )
        scoped = (
            f"     if       {condition}\n"
            "              move Prog-Name to SO-Print\n"
        )
        broken_count = text.count(broken)
        scoped_count = text.count(scoped)
        if broken_count == 1 and scoped_count == 0:
            text = text.replace(broken, scoped, 1)
        elif broken_count == 0 and scoped_count == 1:
            # --no-refresh may revisit an already prepared build tree.
            continue
        else:
            raise SystemExit(
                f"{path}: expected exactly one original or transformed "
                f"open-error scope for {condition!r}; found "
                f"original={broken_count}, transformed={scoped_count}"
            )
    path.write_text(text, encoding="utf-8")
PY
  then
    acas_die "$EX_BUILDTREE" \
      'could not install the six loader open-error scope shims in the build copy.' \
      'The frozen loader sources were not modified; inspect the diagnostic above.'
  fi
  acas_log 'installed build-copy open-error scope shims for 6 in-scope loaders'
}

acas_install_system_secondary_loader_credential_shims() {
  local -a targets=(
    "$ACAS_BUILD/common/dfltLD.cbl"
    "$ACAS_BUILD/common/finalLD.cbl"
    "$ACAS_BUILD/common/sys4LD.cbl"
  )

  # These three loaders read the credential-bearing SYSTEM-REC at relative key
  # 1 into WS-System-Record, but unlike systemLD they never copy its six RDBMS
  # fields into File-Access.DB-Data before calling their bridge directly. The
  # bridge therefore attempts a local socket with blank credentials and the
  # loader returns zero after loading nothing.
  if ! python3 - "${targets[@]}" <<'PY'
from pathlib import Path
import sys

marker = "*>  Harness build copy: propagate SYSTEM-REC credentials to DB-Data.\n"


def credential_block(prefix: str) -> str:
    return (
        marker
        + f"     move     {prefix}RDBMS-DB-Name to DB-Schema.\n"
        + f"     move     {prefix}RDBMS-User    to DB-UName.\n"
        + f"     move     {prefix}RDBMS-Passwd  to DB-UPass.\n"
        + f"     move     {prefix}RDBMS-Port    to DB-Port.\n"
        + f"     move     {prefix}RDBMS-Host    to DB-Host.\n"
        + f"     move     {prefix}RDBMS-Socket  to DB-Socket.\n"
    )

for argument in sys.argv[1:]:
    path = Path(argument)
    text = path.read_text(encoding="utf-8")
    # sys4LD explicitly copies the FD record into WS-System-Record after reading
    # relative key 1; dfltLD and finalLD leave the credential-bearing record in
    # the FD's unprefixed System-Record.
    desired = credential_block("WS-" if path.name == "sys4LD.cbl" else "")
    legacy_ws = credential_block("WS-")
    if marker in text:
        if text.count(desired) == 1:
            continue
        if desired != legacy_ws and text.count(legacy_ws) == 1:
            path.write_text(text.replace(legacy_ws, desired, 1), encoding="utf-8")
            continue
        if text.count(desired) != 1:
            raise SystemExit(f"{path}: secondary-loader credential shim is malformed")
    label = " aa010-Proc-Override.\n"
    lines = text.splitlines(keepends=True)
    positions = [i for i, line in enumerate(lines) if line == label]
    if len(positions) != 1:
        raise SystemExit(
            f"{path}: expected one aa010-Proc-Override label; "
            f"found {len(positions)}"
        )
    lines.insert(positions[0] + 1, "*>\n" + desired)
    path.write_text("".join(lines), encoding="utf-8")
PY
  then
    acas_die "$EX_BUILDTREE" \
      'could not install the secondary system-loader credential shims.' \
      'The frozen loader sources were not modified; inspect the diagnostic above.'
  fi
  acas_log 'installed build-copy credential propagation in dfltLD, finalLD and sys4LD'
}

acas_install_handler_connection_refresh_shims() {
  local common_dir="$ACAS_BUILD/common"

  # Every dynamic file-handler module keeps its record-size sentinels in
  # WORKING-STORAGE. The frozen source also puts the DB credential copy inside
  # that one-time guard. When a later posting program calls the same loaded
  # module with its own fresh File-Access block, the sentinel is already set and
  # the new block stays blank; mysql_real_connect then falls back to a local
  # socket and the compiled cycle stops. Keep the one-time size check, but refresh
  # the six connection fields from the current caller on every RDBMS dispatch.
  # Only the writable build copy is transformed.
  if ! python3 - "$common_dir" <<'PY'
from pathlib import Path
import sys

common = Path(sys.argv[1])
generic_names = (
    "acas004.cbl",
    "acas005.cbl",
    "acas006.cbl",
    "acas007.cbl",
    "acas008.cbl",
    "acas010.cbl",
    "acas011.cbl",
    "acas012.cbl",
    "acas013.cbl",
    "acas014.cbl",
    "acas015.cbl",
    "acas016.cbl",
    "acas017.cbl",
    "acas019.cbl",
    "acas022.cbl",
    "acas023.cbl",
    "acas026.cbl",
    "acas029.cbl",
    "acas030.cbl",
    "acas032.cbl",
    "acasirsub1.cbl",
    "acasirsub3.cbl",
    "acasirsub4.cbl",
    "acasirsub5.cbl",
)
marker = "*>  Harness build copy: refresh DB-Data for this caller.\n"
guarded_moves = (
    "              move     RDBMS-DB-Name to DB-Schema\n"
    "              move     RDBMS-User    to DB-UName\n"
    "              move     RDBMS-Passwd  to DB-UPass\n"
    "              move     RDBMS-Port    to DB-Port\n"
    "              move     RDBMS-Host    to DB-Host\n"
    "              move     RDBMS-Socket  to DB-Socket\n"
)
refresh_moves = guarded_moves[:-1] + ".\n"

for name in generic_names:
    path = common / name
    if not path.is_file():
        raise SystemExit(f"missing handler in build tree: {path}")
    text = path.read_text(encoding="utf-8")
    if marker in text:
        if text.count(marker) != 1:
            raise SystemExit(f"{path}: connection refresh marker is not unique")
        incomplete = marker + guarded_moves
        complete = marker + refresh_moves
        if text.count(incomplete) == 1 and text.count(complete) == 0:
            path.write_text(text.replace(incomplete, complete, 1),
                            encoding="utf-8")
            continue
        if text.count(incomplete) == 0 and text.count(complete) == 1:
            continue
        raise SystemExit(f"{path}: connection refresh block is malformed")
    original = guarded_moves + "     end-if.\n"
    if text.count(original) != 1:
        raise SystemExit(
            f"{path}: expected one guarded connection-copy block; "
            f"found {text.count(original)}"
        )
    path.write_text(text.replace(original, original + marker + refresh_moves, 1),
                    encoding="utf-8")

system_path = common / "acas000.cbl"
system_text = system_path.read_text(encoding="utf-8")
system_marker = "*>  Harness build copy: refresh qualified DB-Data for this caller.\n"
guarded_system_moves = (
    "              move     RDBMS-DB-Name in System-Record  to DB-Schema\n"
    "              move     RDBMS-User    in System-Record  to DB-UName\n"
    "              move     RDBMS-Passwd  in System-Record  to DB-UPass\n"
    "              move     RDBMS-Port    in System-Record  to DB-Port\n"
    "              move     RDBMS-Host    in System-Record  to DB-Host\n"
    "              move     RDBMS-Socket  in System-Record  to DB-Socket\n"
)
legacy_refresh_system_moves = guarded_system_moves[:-1] + ".\n"
refresh_system_moves = (
    "     if       File-Key-No = 1\n"
    "        and   RDBMS-Host in System-Record not = spaces\n"
    + guarded_system_moves
    + "     end-if.\n"
)
if system_marker in system_text:
    if system_text.count(system_marker) != 1:
        raise SystemExit(f"{system_path}: qualified refresh marker is not unique")
    incomplete = system_marker + guarded_system_moves
    complete = system_marker + refresh_system_moves
    legacy_complete = system_marker + legacy_refresh_system_moves
    if system_text.count(legacy_complete) == 1 and system_text.count(complete) == 0:
        system_path.write_text(
            system_text.replace(legacy_complete, complete, 1), encoding="utf-8"
        )
    elif system_text.count(incomplete) == 1 and system_text.count(complete) == 0:
        system_path.write_text(
            system_text.replace(incomplete, complete, 1), encoding="utf-8"
        )
    elif not (
        system_text.count(incomplete) == 0 and system_text.count(complete) == 1
    ):
        raise SystemExit(
            f"{system_path}: qualified connection refresh block is malformed"
        )
else:
    original = guarded_system_moves + "     end-if.\n"
    if system_text.count(original) != 1:
        raise SystemExit(
            f"{system_path}: expected one guarded qualified connection-copy block; "
            f"found {system_text.count(original)}"
        )
    system_path.write_text(
        system_text.replace(
            original, original + system_marker + refresh_system_moves, 1
        ),
        encoding="utf-8",
    )
PY
  then
    acas_die "$EX_BUILDTREE" \
      'could not install the handler connection-refresh shims in the build copy.' \
      'The frozen handler sources were not modified; inspect the diagnostic above.'
  fi
  acas_log 'installed build-copy connection refresh shims for 25 handlers'
}

acas_install_handler_status_reset_shims() {
  local common_dir="$ACAS_BUILD/common"

  # File-Access is caller-owned, while each dynamically loaded handler keeps
  # process state. A reply left by one operation otherwise becomes the starting
  # reply of the next operation or even the next program. Clear only the reply
  # pair at the dispatch boundary; File-Function, Access-Type and key selection
  # remain exactly as the caller supplied them.
  if ! python3 - "$common_dir" <<'PY'
from pathlib import Path
import sys

common = Path(sys.argv[1])
names = (
    "acas000.cbl",
    "acas004.cbl",
    "acas005.cbl",
    "acas006.cbl",
    "acas007.cbl",
    "acas008.cbl",
    "acas010.cbl",
    "acas011.cbl",
    "acas012.cbl",
    "acas013.cbl",
    "acas014.cbl",
    "acas015.cbl",
    "acas016.cbl",
    "acas017.cbl",
    "acas019.cbl",
    "acas022.cbl",
    "acas023.cbl",
    "acas026.cbl",
    "acas029.cbl",
    "acas030.cbl",
    "acas032.cbl",
    "acasirsub1.cbl",
    "acasirsub3.cbl",
    "acasirsub4.cbl",
    "acasirsub5.cbl",
)
marker = "*>  Harness build copy: clear the caller reply pair at dispatch.\n"
insertion = marker + "     move     zero to FS-Reply WE-Error.\n"

for name in names:
    path = common / name
    text = path.read_text(encoding="utf-8")
    if marker in text:
        if text.count(marker) != 1 or text.count(insertion) != 1:
            raise SystemExit(f"{path}: status-reset shim is malformed")
        continue
    label = " aa010-main.\n"
    if text.count(label) != 1:
        raise SystemExit(
            f"{path}: expected one aa010-main dispatch label; "
            f"found {text.count(label)}"
        )
    path.write_text(text.replace(label, label + insertion, 1), encoding="utf-8")
PY
  then
    acas_die "$EX_BUILDTREE" \
      'could not install the handler status-reset shims in the build copy.' \
      'The frozen handler sources were not modified; inspect the diagnostic above.'
  fi
  acas_log 'installed build-copy reply-pair resets for 25 handler dispatches'
}

acas_install_process_connection_ownership_shims() {
  local -a targets=(
    "$ACAS_BUILD/copybooks/mysql-procedures.cpy"
    "$ACAS_BUILD/copybooks/mysql-procedures-2.cpy"
  )

  # cobmysqlapi38.c owns exactly one file-scope MYSQL object for the whole
  # process. The generated bridges nevertheless treat each logical file open as
  # independently owned and every logical close calls mysql_close on that same
  # object. A multi-handler posting program therefore closes another handler's
  # live session, and a second close invokes mysql_close on an already-closed
  # object. Keep the process connection alive until process exit instead. The
  # operating system then releases the socket exactly once; no COMMIT or
  # ROLLBACK is introduced, and every SQL statement remains the frozen one.
  if ! python3 - "${targets[@]}" <<'PY'
from pathlib import Path
import sys

marker = "*>  Harness build copy: the vendored API owns one process connection.\n"
original = (
    " Mysql-1980-Close.\n"
    '     call "MySQL_close".\n'
)
replacement = (
    " Mysql-1980-Close.\n"
    + marker
    + "     continue.\n"
)

for argument in sys.argv[1:]:
    path = Path(argument)
    text = path.read_text(encoding="utf-8")
    if text.count(replacement) == 1 and text.count(original) == 0:
        continue
    if text.count(original) != 1 or text.count(replacement) != 0:
        raise SystemExit(
            f"{path}: expected one original or transformed MySQL close paragraph; "
            f"original={text.count(original)}, transformed={text.count(replacement)}"
        )
    path.write_text(text.replace(original, replacement, 1), encoding="utf-8")
PY
  then
    acas_die "$EX_BUILDTREE" \
      'could not install the process-connection ownership shims in the build copy.' \
      'The frozen MySQL procedure copybooks were not modified; inspect the diagnostic above.'
  fi
  acas_log 'installed build-copy process-connection ownership shims in both MySQL procedure copybooks'
}

acas_install_menu_rdb_mode_restore_shims() {
  local -a targets=(
    "$ACAS_BUILD/general/general.cbl"
    "$ACAS_BUILD/sales/sales.cbl"
    "$ACAS_BUILD/purchase/purchase.cbl"
  )

  # Every menu's overrewrite paragraph first mirrors the system records to the
  # RDBMS, then zeroes File-System-Used so it can mirror the same records to
  # system.dat. The frozen paragraph never restores the saved RDBMS mode. Date
  # Entry therefore leaves the next posting program in indexed-file mode even
  # though the scenario and database row both declare FILE-SYSTEM-USED = 1.
  # The maintainer's own commented block already names Arg-Number as the save
  # slot. Use that slot in the BUILD COPY so the pty-driven menu can pin the date
  # without silently switching the accounting run away from MariaDB.
  if ! python3 - "${targets[@]}" <<'PY'
from pathlib import Path
import sys

save_marker = "*>  Harness build copy: preserve RDB mode across the flat-file mirror.\n"
legacy_save_block = save_marker + "     move     File-System-Used to Arg-Number.\n"
save_block = (
    save_marker
    + "     if       File-System-Used = 1\n"
    + "              move File-System-Used to Arg-Number\n"
    + "     else\n"
    + "      if      Arg-Number = 1\n"
    + "              move Arg-Number to File-System-Used\n"
    + "      end-if\n"
    + "     end-if.\n"
)
restore_marker = "*>  Harness build copy: restore RDB mode for the next menu dispatch.\n"
restore_block = (
    restore_marker
    + "     move     Arg-Number to File-System-Used.\n"
    + "     if       File-System-Used not = zero\n"
    + '              move "66" to FA-RDBMS-Flat-Statuses\n'
    + "     end-if.\n"
)
flat_record_marker = (
    "*>  Harness build copy: retain the declared RDB mode in system.dat record 1.\n"
)
flat_record_block = (
    flat_record_marker
    + "*>  FA-RDBMS-Flat-Statuses = \"00\" still selects acas000's flat-file leg.\n"
    + "     move     Arg-Number to File-System-Used.\n"
)

for argument in sys.argv[1:]:
    path = Path(argument)
    text = path.read_text(encoding="utf-8")

    if save_marker not in text:
        label = " overrewrite."
        positions = [i for i, line in enumerate(text.splitlines(keepends=True))
                     if line.startswith(label)]
        if len(positions) != 1:
            raise SystemExit(
                f"{path}: expected one overrewrite label; found {len(positions)}"
            )
        lines = text.splitlines(keepends=True)
        lines.insert(positions[0] + 1, save_block)
        text = "".join(lines)
    elif text.count(legacy_save_block) == 1 and text.count(save_block) == 0:
        text = text.replace(legacy_save_block, save_block, 1)
    elif text.count(save_block) != 1:
        raise SystemExit(f"{path}: RDB-mode save shim is malformed")

    if flat_record_marker not in text:
        section_start = text.find(" overrewrite.")
        section_end = text.find("\n overclose.", section_start)
        if section_start < 0 or section_end < 0:
            raise SystemExit(f"{path}: could not bound the overrewrite paragraph")
        section = text[section_start:section_end]
        lines = section.splitlines(keepends=True)
        positions = [
            i
            for i, line in enumerate(lines)
            if "move     System-Record to WS-Temp-System-Rec" in line
        ]
        if len(positions) != 2:
            raise SystemExit(
                f"{path}: expected the RDB and flat System-Record save sites; "
                f"found {len(positions)}"
            )
        lines.insert(positions[-1], flat_record_block)
        text = text[:section_start] + "".join(lines) + text[section_end:]
    elif text.count(flat_record_block) != 1:
        raise SystemExit(f"{path}: flat system-record RDB-mode shim is malformed")

    if restore_marker not in text:
        terminator = "*>\n overclose.\n"
        if text.count(terminator) != 1:
            raise SystemExit(
                f"{path}: expected one overclose terminator; "
                f"found {text.count(terminator)}"
            )
        text = text.replace(terminator, restore_block + "*>\n overclose.\n", 1)
    elif text.count(restore_block) != 1:
        raise SystemExit(f"{path}: RDB-mode restore shim is malformed")

    path.write_text(text, encoding="utf-8")
PY
  then
    acas_die "$EX_BUILDTREE" \
      'could not install the menu RDB-mode restore shims in the build copy.' \
      'The frozen menu sources were not modified; inspect the diagnostic above.'
  fi
  acas_log 'installed build-copy RDB-mode restoration in the General, Sales and Purchase menus, including their system.dat mirrors'
}

acas_install_irs_default_connection_ownership_shim() {
  local target="$ACAS_BUILD/common/acasirsub3.cbl"

  # acasirsub3 synthesises OPEN -> READ -> CLOSE inside one read-next call.
  # The vendored C API owns one process connection pointer, so that CLOSE also
  # disconnects acasirsub1, which irs030 deliberately keeps open around the
  # defaults lookup. Keep the synthesized connection alive; the normal IRS close
  # path closes the process connection after the posting loop.
  if ! python3 - "$target" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
original = (
    "              set     fn-Close to true\n"
    "              perform ba020-Call-DAL\n"
    " *>             perform Ca-Process-Logs                  *> temp only during testing\n"
)
replacement = (
    "*>  Harness build copy: retain the shared connection after the defaults read.\n"
    "*>            set     fn-Close to true\n"
    "*>            perform ba020-Call-DAL\n"
    " *>             perform Ca-Process-Logs                  *> temp only during testing\n"
)
if text.count(replacement) == 1 and text.count(original) == 0:
    raise SystemExit(0)
if text.count(original) != 1 or text.count(replacement) != 0:
    raise SystemExit(
        f"{path}: expected one original or transformed synthesized close; "
        f"original={text.count(original)}, transformed={text.count(replacement)}"
    )
path.write_text(text.replace(original, replacement, 1), encoding="utf-8")
PY
  then
    acas_die "$EX_BUILDTREE" \
      'could not install the acasirsub3 connection-ownership shim in the build copy.' \
      'The frozen handler source was not modified; inspect the diagnostic above.'
  fi
  acas_log 'installed build-copy acasirsub3 shared-connection ownership shim'
}

acas_install_irs_eoj_connection_ownership_shim() {
  local target="$ACAS_BUILD/irs/irs030.cbl"

  # The vendored C API exposes one process-wide MYSQL object, although irs030
  # treats acasirsub4 and acas008 as independently owned files. At EOJ the
  # frozen source closes BOTH handlers and then immediately asks acas008 to
  # delete every transfer row. Either close disconnects the one shared MYSQL
  # object, so the delete receives "Server has gone away". Retain the shared
  # connection across those two logical closes; the existing acas008-Close
  # immediately after the delete remains the final process-connection close.
  if ! python3 - "$target" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
original = (
    "     perform  acasirsub4-Close.\n"
    "     perform  acas008-Close.\n"
)
replacement = (
    "*>  Harness build copy: retain the shared connection until transfer cleanup.\n"
    "*>   perform  acasirsub4-Close.\n"
    "*>   perform  acas008-Close.\n"
)
if text.count(replacement) == 1 and text.count(original) == 0:
    raise SystemExit(0)
if text.count(original) != 1 or text.count(replacement) != 0:
    raise SystemExit(
        f"{path}: expected one original or transformed EOJ close pair; "
        f"original={text.count(original)}, transformed={text.count(replacement)}"
    )
path.write_text(text.replace(original, replacement, 1), encoding="utf-8")
PY
  then
    acas_die "$EX_BUILDTREE" \
      'could not install the irs030 EOJ connection-ownership shim in the build copy.' \
      'The frozen IRS source was not modified; inspect the diagnostic above.'
  fi
  acas_log 'installed build-copy irs030 EOJ shared-connection ownership shim'
}

acas_prepare_build_tree() {
  acas_stage 'Build tree: copy the frozen checkout into the writable tree'

  # Re-assert the safety guards immediately before anything destructive.
  acas_assert_safe_build_path "$ACAS_BUILD"

  if (( ACAS_REFRESH_TREE )); then
    # AND THE PROVENANCE GATE, re-evaluated here rather than earlier, so
    # that a value or a directory that changed between the preconditions and this
    # moment is caught. It re-runs the shape guard itself, so the two cannot drift
    # apart, and it refuses a non-empty directory that this harness cannot show it
    # created. Nothing between this line and the `find` can alter $ACAS_BUILD.
    acas_assert_clearable_build_tree "$ACAS_BUILD"

    acas_log "clearing $ACAS_BUILD"
    # Delete only the CHILDREN of $ACAS_BUILD, never $ACAS_BUILD itself: the
    # directory is a mount point in the Compose stack and removing it would
    # break the container.
    acas_run_deadline "$ACAS_TIMEOUT_BUILD" ACAS_TIMEOUT_BUILD \
      "clearing $ACAS_BUILD" "$EX_BUILDTREE" - \
      -- find "$ACAS_BUILD" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + \
      || acas_die "$EX_BUILDTREE" "could not clear $ACAS_BUILD."

    # CLAIM THE TREE BEFORE THE COPY, NOT AFTER IT.
    #
    # The marker means "this harness owns this directory and a later run may clear
    # it". It used to be written only once the copy had SUCCEEDED, on the reasoning
    # that a marker on a tree that was never a build tree would licence clearing
    # someone's data. That reasoning is sound about a directory this run did not
    # clear -- and this run has just cleared it, under
    # `acas_assert_clearable_build_tree', so ownership is already established at
    # this point and the copy cannot change who owns it.
    #
    # WRITING IT AFTERWARDS MADE A FAILED COPY UNRECOVERABLE IN PLACE, measured:
    # a copy that stopped part-way left $ACAS_BUILD POPULATED and UNMARKED, so the
    # next run refused to clear it and exited 67 -- a second failure with a
    # different cause, which the operator could only escape with a
    # `docker volume rm' or by creating the marker by hand. The marker now goes
    # down immediately after the clear, so a retry recognises its own tree and
    # clears it again. A tree this harness cleared is a tree it may clear.
    if : > "$ACAS_BUILD/$ACAS_BUILD_MARKER" 2>/dev/null; then
      acas_log "marked $ACAS_BUILD as this harness's build tree ($ACAS_BUILD_MARKER)"
    else
      acas_warn "could not write $ACAS_BUILD/$ACAS_BUILD_MARKER;" \
        'a later run will refuse to clear this tree and will need --no-refresh.'
    fi

    # THE COPY NAMES WHAT IT COPIES. It is an ALLOW LIST of the frozen build's
    # inputs, and that is a correctness measure rather than a speed one.
    #
    # WHAT A DENY LIST COST, MEASURED TWICE. This copy used to enumerate
    # `$ACAS_REPO/*' and skip a fixed list of scratch names. Two failures followed,
    # and both were the same defect:
    #
    #   * `cp: cannot access '/repo/./.pytest_cache': Permission denied' -- pytest
    #     creates it mode 0700 owned by whoever ran the tests, this service runs as
    #     an unprivileged account (harness/Dockerfile.gnucobol `USER') and `/repo'
    #     is read-only, so the documented order "run the tests, then build the
    #     oracle" ended in exit 67. `.pytest_cache' was then added to the deny list.
    #   * `cp: cannot access '/repo/tmp/qa-.../evidence': Permission denied' -- a QA
    #     run had left a root-owned tree under `tmp/', which `.gitignore' ignores, so
    #     `git status' was EMPTY and the build failed anyway. Exit 67 again.
    #
    # A deny list can only ever name the trees somebody has already been bitten by,
    # while the failure mode is "any unreadable path anywhere in the checkout" -- and
    # every one of those paths is, by construction, something the frozen build does
    # not need. So the selection is inverted: the copy takes the inputs the frozen
    # compile scripts actually read and NOTHING else, and arbitrary ignored or
    # runtime state in the checkout becomes unreachable rather than newly hazardous.
    #
    # WHY THIS LIST IS THE WHOLE LIST, from the frozen scripts themselves:
    #   comp-all.sh   `cd's through the six compile directories in order and runs
    #                 each one's own comp-*.sh [comp-all.sh:L15-L32].
    #   copybooks/    every compile resolves copybooks through `-I ../copybooks'
    #                 [common/comp-common.sh:L21-L57], and COBCPY/COB_COPY_DIR are
    #                 set to `../copybooks' [comp-all.sh:L9-L10].
    #   the six dirs  common general irs purchase sales stock -- ACAS_COMPILE_DIRS,
    #                 which is what comp-all.sh walks.
    # Nothing else in the checkout is read from the BUILD COPY. The vendored preSQL
    # archive, `etc/ld.so.conf.d/gnucobol.conf', `mysql/ACASDB.sql' and the frozen
    # digests are all read from $ACAS_REPO directly, so copying them would be dead
    # weight rather than a requirement -- and the structural assertions below plus
    # the per-step compile assertions fail loudly if that ever stops being true.
    #
    # Absence is FATAL rather than silently tolerated: a missing input means the
    # mount is wrong, and a build that proceeded would compile a partial
    # specification.
    local -a wanted=(comp-all.sh copybooks "${ACAS_COMPILE_DIRS[@]}")
    local -a sources=()
    local entry name missing=''
    for name in "${wanted[@]}"; do
      entry="$ACAS_REPO/$name"
      if [[ -e "$entry" ]]; then
        sources+=("$entry")
      else
        missing+=" $name"
      fi
    done
    [[ -z "$missing" ]] || acas_die "$EX_BUILDTREE" \
      "the read-only checkout is missing frozen build input(s):${missing}." \
      'The checkout IS the specification, so a build that continued would compile' \
      'a partial one. Check that $ACAS_REPO is the repository root and that the' \
      'bind mount in harness/docker-compose.yml resolves to it.'

    #  What was NOT taken, recorded rather than left to be inferred: a reader of this
    #  log can see that the omission was a decision. Names only, never contents, so
    #  an unreadable directory is named without being entered.
    local -a untaken=()
    local keep candidate
    for entry in "$ACAS_REPO"/* "$ACAS_REPO"/.[!.]*; do
      [[ -e "$entry" ]] || continue
      name="${entry##*/}"
      keep=''
      for candidate in "${wanted[@]}"; do
        [[ "$name" == "$candidate" ]] && { keep=1; break; }
      done
      [[ -n "$keep" ]] || untaken+=("$name")
    done
    (( ${#untaken[@]} == 0 )) || acas_log \
      "not copied (${#untaken[@]} top-level entries; no frozen compile reads any of them from the build copy): ${untaken[*]}"

    acas_log "copying $ACAS_REPO into $ACAS_BUILD (${#sources[@]} named frozen build inputs, layout preserved)"
    acas_run_deadline "$ACAS_TIMEOUT_BUILD" ACAS_TIMEOUT_BUILD \
      "copying $ACAS_REPO into $ACAS_BUILD" "$EX_BUILDTREE" - \
      -- cp -a "${sources[@]}" "$ACAS_BUILD/" \
      || acas_die "$EX_BUILDTREE" \
        "copying $ACAS_REPO into $ACAS_BUILD failed." \
        'The build must run in a copy: [common/comp-common.sh:L25] regenerates' \
        'every common/*MT.cbl, and those files are the frozen data dictionary.' \
        'Only the named frozen inputs above are copied, so a permission failure' \
        'here names a path INSIDE comp-all.sh, copybooks/ or one of the six compile' \
        'directories -- a specification source this account cannot read, which is a' \
        'broken checkout rather than stray workspace state. $ACAS_BUILD carries its' \
        'marker, so re-running after fixing the path clears and re-copies in place.'
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

  if [[ -n "${ACAS_BIN-}" && "$ACAS_BIN" == "$ACAS_BUILD"/* ]]; then
    mkdir -p "$ACAS_BIN"
    acas_log "restored ACAS_BIN=$ACAS_BIN"
  fi

  # comp-all.sh is frozen and re-exports COBCPY=../copybooks, so an additional
  # environment include path cannot reach this missing archive member. Install
  # the comment-only shim into the BUILD COPY instead. This runs for refresh and
  # --no-refresh alike and never writes under $ACAS_REPO/copybooks.
  #  DIGEST THE SOURCES ON EITHER SIDE OF THE SHIM BLOCK, so the register above is
  #  MEASURED rather than trusted. Only on a refreshed tree: the shims are idempotent
  #  and a --no-refresh build over an already prepared tree changes nothing, so there
  #  would be nothing to compare and the check would pass vacuously.
  local before_listing='' after_listing=''
  if (( ACAS_REFRESH_TREE )); then
    before_listing="$ACAS_BUILD/.acas-sources-before-shims"
    after_listing="$ACAS_BUILD/.acas-sources-after-shims"
    acas_source_digest_listing > "$before_listing" || acas_die "$EX_BUILDTREE" \
      "could not digest the build-tree sources into $before_listing."
  fi

  #  THE TRANSFORMS ARE APPLIED ONLY WHEN ASKED FOR. In the default
  #  frozen mode the applied register stays EMPTY, so the attestation reports
  #  `oracle-source-is-frozen yes` because nothing was changed - not because the check
  #  was skipped. Both facts are then measured on either side of this block.
  if (( ACAS_ALLOW_SOURCE_TRANSFORMS )); then
    acas_warn "BUILDING A TRANSFORMED ORACLE BECAUSE IT WAS EXPLICITLY REQUESTED. ${#ACAS_SOURCE_TRANSFORMS[@]} catalogued source transformation(s) will be applied to the build copy. The result is a DIAGNOSTIC oracle: harness/reset_db.sh refuses it as evidence, because rule R-4 requires the frozen defects be reproduced rather than repaired and these repairs change the specification the migration is measured against."
    acas_install_sqlstate_comment_shim
    acas_install_loader_open_scope_shims
    acas_install_system_secondary_loader_credential_shims
    acas_install_handler_connection_refresh_shims
    acas_install_handler_status_reset_shims
    acas_install_process_connection_ownership_shims
    acas_install_menu_rdb_mode_restore_shims
    acas_install_irs_default_connection_ownership_shim
    acas_install_irs_eoj_connection_ownership_shim
    ACAS_SOURCE_TRANSFORMS_APPLIED=("${ACAS_SOURCE_TRANSFORMS[@]}")
  else
    ACAS_SOURCE_TRANSFORMS_APPLIED=()
    acas_log 'frozen oracle: no source transformation applied; the build copy is byte-for-byte the checkout'
  fi

  if (( ACAS_REFRESH_TREE )); then
    acas_source_digest_listing > "$after_listing" || acas_die "$EX_BUILDTREE" \
      "could not digest the build-tree sources into $after_listing."
    acas_assert_transform_register_complete "$before_listing" "$after_listing"
  fi

  acas_check_copybook_closure
}

# COPY-closure advisory. A precise, zero-false-positive check that every
# copybook the frozen build needs can be resolved. It exists because there is a
# real source-level gap.

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

         THE AAP FORBIDS WRITING IT INTO THE REPOSITORY, AND NAMES THE RULES.
         §0.8.1 places copybooks/*.cob among the frozen artifacts and states
         that a diff touching them is a defect in the migration "regardless of
         how harmless it appears". §0.2.2 lists copybooks/ under "Frozen
         artifacts -- zero modifications of any kind". R-3 forbids adding
         validation logic, and a SQLSTATE-to-FS-Reply table is validation logic.
         R-4 makes a repaired defect a failure rather than an improvement. A
         synthesised member breaches all four at once, so the absence is
         reported and left in place deliberately -- it is not an oversight, and
         it is not something this script will paper over.

         OPERATOR REMEDIATION -- THE ONLY ROUTE TO A FROZEN ORACLE:
           1. Obtain the authentic copybooks/ACAS-SQLstate-error-list.cob from
              the ACAS maintainer. Measured: it is in no tracked file of this
              repository, nowhere in the working tree, and in none of the three
              vendored archives -- presql2-latest.zip and
              mysql-connector-c-6.1.11-src.tar.gz contain no member matching
              "sqlstate" at all, and the only two in
              mariadb-connector-c-3.3.4-src.zip are the unrelated C API man
              pages man/mysql_sqlstate.3 and man/mysql_stmt_sqlstate.3. Do not
              try to reconstruct it from the *MT.scb sources: they COPY it, they
              do not contain it.
           2. Place it at copybooks/ACAS-SQLstate-error-list.cob in the
              checkout, byte-for-byte as received, with no reformatting.
           3. Re-run this script with NO transform flag and with
              ACAS_ACCEPT_TRANSFORMED_ORACLE unset:
                harness/build_oracle.sh
              A frozen build then reports "verified: every COPY target of every
              source the frozen scripts compile resolves", and the attestation
              records "oracle-source-is-frozen yes" with "source-transforms 0".
           4. From that point reset_db.sh needs no --accept-transformed-oracle,
              and the eight scenario protocols yield the ordering-normalised
              empty diffs that AAP §0.8.5 accepts as parity evidence.
         Until step 1 is done by the maintainer, every verdict this harness can
         produce carries NO PARITY CLAIM, and that is the honest ceiling of the
         evidence -- not a defect in the Python implementation, which passes its
         own suites in full.

         THEREFORE, ON THIS CHECKOUT, THE FROZEN ORACLE IS UNAVAILABLE. That is
         a measurement, not a prediction: a default (frozen, zero-transformation)
         build of this repository fails with exit 74 and 22 compile errors, one
         per affected bridge. No attestation is written, and reset_db.sh
         reports exit 77 EVIDENCE UNAVAILABLE -- before it drops a single
         table -- rather than any verdict.

         WHAT THE SHIM DOES, MEASURED RATHER THAN ASSUMED. Only an explicitly
         requested --transformed-oracle build GENERATES the comment-only
         compatibility include, and only into the writable build copy at
         $ACAS_BUILD/copybooks -- it is not a repository file and the frozen
         copybooks/ tree is never written to. Its CONTENT provably does not matter: compiling
         glpostingMT.cbl to C (cobc -C) with the comment-only shim, with a
         zero-byte member, and with arbitrary different comment text yields a
         BYTE-IDENTICAL translation in all three cases. Only the COPY resolving
         matters. That follows from where the COPY sits -- line 160 of
         glpostingMT.cbl, between `identification division.' (L9) and
         `environment division.' (L201), a region in which only comments are
         legal -- so the absent member cannot have carried data or procedure
         code, and the executable SQLSTATE handling is in the frozen PROCEDURE
         DIVISION already (`move WS-MYSQL-SqlState to SQL-State', 8 sites).

         SO THIS ONE TRANSFORM IS BEHAVIOUR-NEUTRAL, AND IT IS NOT THE REASON A
         TRANSFORMED ORACLE CANNOT BE EVIDENCE. The other 40 entries in
         ACAS_SOURCE_TRANSFORMS are: they restore IF scope in flat-file
         open-error branches, propagate RDBMS credentials, retain connections
         across calls, and reset stale reply pairs -- all of them changes to
         EXECUTABLE logic in the handlers. A build carrying those has repaired
         the specification, which is why reset_db.sh refuses to set up a
         comparison against it, and why no verdict drawn from one is a parity
         claim.
         --------------------------------------------------------------------
EXPLAIN
}


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

    acas_assert_archive_digest "$archive"

    # A scratch directory INSIDE the writable build tree, removed on exit. The
    # archive itself is never touched: it is read out of the read-only
    # checkout.
    local scratch="$ACAS_BUILD/.acas-presql2"
    acas_remove_build_scratch '.acas-presql2'
    mkdir -p "$scratch"
    ACAS_SCRATCH_DIRS+=("$scratch")

    # EXTRACTED UNDER A MEMBER POLICY, NOT WITH `unzip -o' OR `extractall'.
    # Identity was asserted above; this is the member-by-member audit that must
    # follow it.
    acas_extract_audited_zip "$archive" "$scratch" "$ACAS_PRESQL2_ARCHIVE_ROOT"

    [[ -d "$scratch/$ACAS_PRESQL2_ARCHIVE_ROOT" ]] || acas_die "$EX_STEP1" \
      "$ACAS_PRESQL2_ARCHIVE_ROOT/ was not found inside $archive." \
      'The archive layout is not as expected.'
    ACAS_PRESQL2_DIR="$scratch/$ACAS_PRESQL2_ARCHIVE_ROOT"
    acas_log "unpacked to $ACAS_PRESQL2_DIR"
  fi

  # -------------------------------------------------------------------------
  # THE FOUR MEMBERS EVERY LATER STEP DEPENDS ON, PRESENT *AND* VERIFIED.
  #
  # Present was never enough. Step 2 compiles `cobmysqlapi38.c' and links the object
  # into every bridge, handler and loader; step 3 compiles `presql2.cbl' into the
  # translator that generates every bridge's SQL. Those two files decide what the
  # oracle IS, and the oracle is the specification this whole migration is measured
  # against -- so a run that reused a directory nothing had verified could not say
  # what it had measured against.
  #
  # Verified on BOTH branches deliberately: the reuse branch above is the DEFAULT in
  # the shipped image, so a check that ran only after an unpack would almost never
  # run. See the ACAS_PRESQL2_MEMBER_DIGESTS declaration.
  # -------------------------------------------------------------------------
  local entry required expected actual
  for entry in "${ACAS_PRESQL2_MEMBER_DIGESTS[@]}"; do
    required="${entry%%:*}"
    expected="${entry#*:}"
    [[ -f "$ACAS_PRESQL2_DIR/$required" ]] || acas_die "$EX_STEP1" \
      "$ACAS_PRESQL2_DIR/$required is missing." \
      'Steps 2 and 3 are built from these four files.'
    actual="$(acas_file_sha256 "$ACAS_PRESQL2_DIR/$required")" || acas_die "$EX_STEP1" \
      "could not hash $ACAS_PRESQL2_DIR/$required."
    if [[ "$actual" != "$expected" ]]; then
      acas_die "$EX_ARCHIVE" \
        "$ACAS_PRESQL2_DIR/$required is not the member the pinned archive carries." \
        "  expected: $expected" \
        "  measured: $actual" \
        'This file is compiled into the oracle -- cobmysqlapi38.c becomes the object' \
        'linked into every bridge, presql2.cbl becomes the translator that generates' \
        'every bridge'"'"'s SQL -- so the oracle would not be the system the checkout' \
        'describes, and every parity verdict drawn from it would be measured against' \
        'something else.' \
        'If the archive was deliberately replaced, update both' \
        'ACAS_PRESQL2_SHA256_EXPECTED and ACAS_PRESQL2_MEMBER_DIGESTS.'
    fi
    acas_log "verified: $required sha256 $actual"
  done
  acas_log 'verified: all four members match the digests the pinned archive carries'

  # Two coexisting version strings. BOTH are true and NEITHER is resolved: the
  # package README records one, the translator's own WORKING-STORAGE another.
  acas_note 'preSQL package version per [presql2-latest.zip:presql2-package/README.SVN:L22]: 1.14f'
  acas_note 'translator version per [presql2-latest.zip:presql2-package/presql2.cbl:L302]: " 2.22 "'
}

# STEP 2/5 -- the RECOVERED build rule for the bridge's C interface object
# `find .

# The rule was recovered from the vendored package.
acas_step2_build_cobmysqlapi() {
  acas_banner 2 'compile cobmysqlapi.o with the recovered build rule'

  # The digest step 1 pinned and verified for the C source this object must come
  # from. Every reuse decision below is measured against it.
  local c_digest
  c_digest="$(acas_pinned_member_digest 'cobmysqlapi38.c')" || acas_die "$EX_STEP2" \
    'cobmysqlapi38.c is not pinned in ACAS_PRESQL2_MEMBER_DIGESTS.' \
    'That array is what makes a reused object provable; do not remove entries from it.'

  local published="${ACAS_COBMYSQLAPI_OBJ:-/usr/local/lib/acas/cobmysqlapi.o}"
  if [[ -s "$published" ]] \
     && acas_artifact_provenance_holds "$published" "$c_digest" 'cobmysqlapi38.c' \
          'The object is linked into every bridge, handler and loader'; then
    ACAS_COBMYSQLAPI_SRC="$published"
    #  Say WHOSE object it is, not just that one was found. Crediting
    #  harness/Dockerfile.gnucobol for an object that arrived by a redirected
    #  ACAS_COBMYSQLAPI_OBJ would misstate provenance in the build log, and the
    #  attestation this run publishes has to agree with what the log claims.
    if [[ "$published" == "$ACAS_CANONICAL_COBMYSQLAPI_OBJ" ]]; then
      acas_log "reusing the object harness/Dockerfile.gnucobol built from the vendored source: $published"
    else
      acas_log "reusing an OPERATOR-SUPPLIED object of unestablished origin: $published"
      acas_log "  (ACAS_COBMYSQLAPI_OBJ points away from $ACAS_CANONICAL_COBMYSQLAPI_OBJ;"
      acas_log '   this build will be attested as unable to produce evidence)'
    fi
  else
    [[ -n "$ACAS_PRESQL2_DIR" && -f "$ACAS_PRESQL2_DIR/cobmysqlapi38.c" ]] \
      || acas_die "$EX_STEP2" \
        'the unpacked preSQL package is not available, so cobmysqlapi38.c cannot be compiled.' \
        'Run step 1 first (omit --from/--only, or use --from 1).'

    local workdir="$ACAS_BUILD/.acas-cobmysqlapi"
    acas_remove_build_scratch '.acas-cobmysqlapi'
    mkdir -p "$workdir"
    ACAS_SCRATCH_DIRS+=("$workdir")
    cp -p "$ACAS_PRESQL2_DIR/cobmysqlapi38.c" "$workdir/cobmysqlapi38.c"

    acas_log 'running the recovered rule verbatim [presql2-latest.zip:presql2-package/cobmysqlapi38.sh]:'
    acas_log '  gcc -I/usr/local/mysql/include -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC'
    acas_run_deadline "$ACAS_TIMEOUT_COMPILE" ACAS_TIMEOUT_COMPILE \
      'compiling cobmysqlapi38.c' "$EX_STEP2" "$workdir" \
      -- gcc -I/usr/local/mysql/include -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC \
      || acas_die "$EX_STEP2" \
      'compiling cobmysqlapi38.c failed.' \
      'This is the recovered rule from [presql2-latest.zip:presql2-package/cobmysqlapi38.sh]; it needs' \
      "$ACAS_FROZEN_MYSQL_PREFIX/include/mysql.h and a working C compiler." \
      'Without the object, every bridge, handler and loader fails at link time' \
      'with nothing more informative than "cobmysqlapi.o: No such file or directory".'

    [[ -s "$workdir/cobmysqlapi.o" ]] || acas_die "$EX_STEP2" \
      "gcc reported success but $workdir/cobmysqlapi.o is missing or empty." \
      '[presql2-latest.zip:presql2-package/cobmysqlapi38.sh]'
    ACAS_COBMYSQLAPI_SRC="$workdir/cobmysqlapi.o"
    acas_log "built $ACAS_COBMYSQLAPI_SRC ($(wc -c < "$ACAS_COBMYSQLAPI_SRC") bytes)"
    acas_record_artifact_provenance "$ACAS_COBMYSQLAPI_SRC" "$c_digest"
  fi

  # SIX copies, one per compile directory.
  local dir target
  for dir in "${ACAS_COMPILE_DIRS[@]}"; do
    target="$ACAS_BUILD/$dir/cobmysqlapi.o"
    acas_run_deadline "$ACAS_TIMEOUT_PROBE" ACAS_TIMEOUT_PROBE \
      "placing cobmysqlapi.o in $dir" "$EX_STEP2" - \
      -- install -m 0644 "$ACAS_COBMYSQLAPI_SRC" "$target" \
      || acas_die "$EX_STEP2" \
      "could not place cobmysqlapi.o in $ACAS_BUILD/$dir."
    [[ -s "$target" ]] || acas_die "$EX_STEP2" "$target is missing or empty."
  done
  acas_log "placed cobmysqlapi.o in all ${#ACAS_COMPILE_DIRS[@]} compile directories: $(acas_join_words "${ACAS_COMPILE_DIRS[@]}")"
}

acas_step3_build_presql2() {
  acas_banner 3 'build and install the presql2 translator'

  # The translator rewrites every common/*MT.scb into the common/*MT.cbl that is
  # actually compiled, which means it AUTHORS the SQL every bridge issues. A reused
  # one is therefore held to the same standard as the object in step 2: it is trusted
  # only when it can name the presql2.cbl it was built from.
  local cbl_digest
  cbl_digest="$(acas_pinned_member_digest 'presql2.cbl')" || acas_die "$EX_STEP3" \
    'presql2.cbl is not pinned in ACAS_PRESQL2_MEMBER_DIGESTS.' \
    'That array is what makes a reused translator provable; do not remove entries from it.'

  local existing=''
  acas_have presql2 && existing="$(command -v presql2)"

  if [[ -n "$existing" ]] \
     && acas_artifact_provenance_holds "$existing" "$cbl_digest" 'presql2.cbl' \
          'The translator generates the SQL inside every bridge'; then
    acas_log "presql2 is already on the PATH: $existing"
  else
    [[ -n "$ACAS_PRESQL2_DIR" && -f "$ACAS_PRESQL2_DIR/presql2.cbl" ]] \
      || acas_die "$EX_STEP3" \
        'presql2 cannot be trusted or is absent, and the unpacked package is unavailable.' \
        'Run step 1 first (omit --from/--only, or use --from 1).'
    [[ -n "$ACAS_COBMYSQLAPI_SRC" && -s "$ACAS_COBMYSQLAPI_SRC" ]] \
      || acas_die "$EX_STEP3" \
        'cobmysqlapi.o is unavailable, and [presql2-latest.zip:presql2-package/presql2.sh] links it.' \
        'Run step 2 first.'

    local workdir="$ACAS_BUILD/.acas-presql2-build"
    acas_remove_build_scratch '.acas-presql2-build'
    mkdir -p "$workdir"
    ACAS_SCRATCH_DIRS+=("$workdir")

    cp -p "$ACAS_PRESQL2_DIR/presql2.cbl" "$workdir/"
    local cpy
    for cpy in MYSQL-VARIABLES.CPY MYSQL-PROCEDURES.CPY \
               mysql-variables.cpy mysql-procedures.cpy; do
      [[ -f "$ACAS_PRESQL2_DIR/$cpy" ]] && cp -p "$ACAS_PRESQL2_DIR/$cpy" "$workdir/"
    done
    cp -p "$ACAS_COBMYSQLAPI_SRC" "$workdir/cobmysqlapi.o"

    acas_log 'running the vendored rule verbatim [presql2-latest.zip:presql2-package/presql2.sh]:'
    acas_log '  cobc -x presql2.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz'
    # `env' carries the two copybook variables.
    acas_run_deadline "$ACAS_TIMEOUT_COMPILE" ACAS_TIMEOUT_COMPILE \
      'building presql2' "$EX_STEP3" "$workdir" \
      -- env "COBCPY=$workdir" "COB_COPY_DIR=$workdir" \
         cobc -x presql2.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz \
      || acas_die "$EX_STEP3" \
      'building presql2 failed.' \
      '[common/comp-common.sh:L25] cannot translate any *MT.scb without it.'

    [[ -s "$workdir/presql2" ]] || acas_die "$EX_STEP3" \
      "cobc reported success but $workdir/presql2 was not produced." \
      '[presql2-latest.zip:presql2-package/presql2.sh]'
    # Installing into /usr/local/bin is preferred, because the frozen
    # [common/comp-common.sh:L25] invokes `presql2' by name. It is NOT required: the
    # runtime account is deliberately unprivileged, and a rebuild triggered by a
    # missing provenance record must not need root that the build never needed
    # before. Prepending the freshly built copy to PATH resolves the same name for
    # every child process, which is all the frozen script asks of it.
    if acas_run_deadline "$ACAS_TIMEOUT_PROBE" ACAS_TIMEOUT_PROBE \
         'installing presql2' "$EX_STEP3" - \
         -- install -m 0755 "$workdir/presql2" /usr/local/bin/presql2; then
      acas_log 'installed /usr/local/bin/presql2'
      acas_record_artifact_provenance /usr/local/bin/presql2 "$cbl_digest"
    else
      PATH="$workdir:$PATH"
      export PATH
      acas_warn \
        'could not install presql2 into /usr/local/bin (root is required there).' \
        "Using the copy just built instead: $workdir/presql2" \
        'It is first on PATH, so [common/comp-common.sh:L25] resolves this one by' \
        'name for the rest of this run.'
      acas_record_artifact_provenance "$workdir/presql2" "$cbl_digest"
    fi

    # bldcopy2 is built for completeness.
    if [[ -f "$ACAS_PRESQL2_DIR/bldcopy2.cbl" ]] && ! acas_have bldcopy2; then
      cp -p "$ACAS_PRESQL2_DIR/bldcopy2.cbl" "$workdir/"
      acas_log 'running the vendored rule verbatim [presql2-latest.zip:presql2-package/bldcopy2.sh]:'
      acas_log '  cobc -x bldcopy2.cbl cobmysqlapi.o -L /usr/local/mysql/lib -lmysqlclient'
      # The deadline is imposed with acas_deadline_prefix rather than with
      # acas_run_deadline because THIS site must stay non-fatal.
      local bldcopy_rc=0 bldcopy_started bldcopy_elapsed
      acas_deadline_prefix "$ACAS_TIMEOUT_COMPILE"
      bldcopy_started="$SECONDS"
      (
        cd "$workdir" \
          && exec "${ACAS_DEADLINE_ARGV[@]}" \
               env "COBCPY=$workdir" "COB_COPY_DIR=$workdir" \
               cobc -x bldcopy2.cbl cobmysqlapi.o -L /usr/local/mysql/lib -lmysqlclient
      ) < /dev/null || bldcopy_rc=$?
      bldcopy_elapsed=$(( SECONDS - bldcopy_started ))
      if acas_is_timeout_status "$bldcopy_rc" "$bldcopy_elapsed" "$ACAS_TIMEOUT_COMPILE"; then
        acas_warn \
          "building bldcopy2 exceeded its ${ACAS_TIMEOUT_COMPILE}s deadline and was terminated." \
          'No frozen ACAS script invokes bldcopy2, so the oracle build continues.'
      fi
      if (( bldcopy_rc == 0 )) && [[ -s "$workdir/bldcopy2" ]]; then
        acas_run_deadline "$ACAS_TIMEOUT_PROBE" ACAS_TIMEOUT_PROBE \
            'installing bldcopy2' "$EX_STEP3" - \
            -- install -m 0755 "$workdir/bldcopy2" /usr/local/bin/bldcopy2 \
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
  # prtschema2 is NOT built.
  acas_note 'prtschema2 is deliberately not built: the archive ships no prtschema2.cbl and no frozen ACAS script uses it'

  if (( ACAS_RUN_PREFLIGHT_LINK )); then
    acas_preflight_link_proof
  else
    acas_note 'step-3 toolchain link proof skipped at the operator'"'"'s request'
  fi
}

acas_preflight_link_proof() {
  local example="$ACAS_PRESQL2_DIR/ACAS"
  if [[ -z "$ACAS_PRESQL2_DIR" || ! -f "$example/stockMT.COB" ]]; then
    acas_note 'the vendored worked example is unavailable, so the link proof is skipped'
    return 0
  fi

  local proof="$ACAS_BUILD/.acas-link-proof"
  acas_remove_build_scratch '.acas-link-proof'
  mkdir -p "$proof"
  ACAS_SCRATCH_DIRS+=("$proof")
  cp -a "$example/." "$proof/"
  cp -p "$ACAS_COBMYSQLAPI_SRC" "$proof/cobmysqlapi.o"

  acas_log 'proving the toolchain with [presql2-latest.zip:presql2-package/ACAS/comp-stockMT.sh]:'
  acas_log '  cobc -m stockMT.COB cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz'
  acas_run_deadline "$ACAS_TIMEOUT_COMPILE" ACAS_TIMEOUT_COMPILE \
    'the vendored worked example (stockMT)' "$EX_STEP3" "$proof" \
    -- env "COBCPY=$proof" "COB_COPY_DIR=$proof" \
       cobc -m stockMT.COB cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz \
    || acas_die "$EX_STEP3" \
    'the vendored worked example failed to compile.' \
    'The COBOL-to-MySQL toolchain is incomplete, so every frozen bridge compile' \
    'would fail the same way. Check cobmysqlapi.o, mysql.h and libmysqlclient.so.' \
    '[presql2-latest.zip:presql2-package/ACAS/comp-stockMT.sh]'

  [[ -s "$proof/stockMT.so" ]] || acas_die "$EX_STEP3" \
    'cobc reported success but stockMT.so was not produced.' \
    '[presql2-latest.zip:presql2-package/ACAS/comp-stockMT.sh]'

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


# presql2.cbl reads it at `presql2.cbl:L759-L773' and states the requirement in
# its own prologue at :L55 ("This filename MUST be presql2.param").

# DEVIATION 3 of 6 -- WHY DBNAME IS information_schema, NOT $ACAS_DB_NAME.

# DEVIATION 4 of 6 -- an EMPTY ACAS_DB_SOCKET is written as the literal
# DBSOCKET=NULL rather than as an empty value.
acas_write_presql2_param() {
  local dir="$1"
  local prog="${2:-presql2}"
  local target="$dir/$prog.param"

  [[ -d "$dir" ]] || acas_die "$EX_STEP4" \
    "$dir does not exist, so $prog.param cannot be written there."

  local dbname="${ACAS_PRESQL2_DBNAME:-information_schema}"

  local socket="${ACAS_DB_SOCKET-}"
  if [[ -z "$socket" ]]; then
    socket='NULL'
  fi

  # CREATED EMPTY, EXCLUSIVELY, AND CHMOD'ED 0600 BEFORE THE PASSWORD IS
  # WRITTEN.
  acas_create_private_file "$target" "the $prog parameter file" "$EX_STEP4"
  ACAS_PARAM_FILES+=("$target")

  # Appended, not redirected: the file already exists at 0600 and `>>' will not
  # widen it. `>' here would create a fresh inode at the umask's mode.
  {
    printf 'DBHOST=%s\n'   "$ACAS_DB_HOST"
    printf 'DBUSER=%s\n'   "$ACAS_DB_USER"
    printf 'DBPASSWD=%s\n' "$ACAS_DB_PASSWORD"
    printf 'DBNAME=%s\n'   "$dbname"
    printf 'DBPORT=%s\n'   "$ACAS_DB_PORT"
    printf 'DBSOCKET=%s\n' "$socket"
  } >> "$target" || acas_die "$EX_STEP4" "could not write $target."

  acas_log "wrote $target (0600, six cards in the order read_params requires)"
  # The CARD NAMES and their PRESENCE are what a reader has to be able to check --
  # read_params is positional, so a missing or reordered card is the failure mode.
  # The VALUES are the deployment's identity and are not printed: the file
  # itself is 0600 and is shredded by the EXIT trap, and the values come from the
  # environment, where anyone entitled to them already has them.
  acas_log '  cards: DBHOST DBUSER DBPASSWD DBNAME DBPORT DBSOCKET (all six, in that order)'
  acas_log "  target: $(acas_target_description)"
  acas_log "  DBNAME card: ${dbname} (the presql2 probe schema -- see DEVIATION 3 of 6)"
  acas_log "  DBSOCKET card: $( [[ "$socket" == 'NULL' ]] && printf 'NULL (TCP only)' || printf 'a socket path (not printed)' )"
  acas_note 'no host, account name or socket path is printed: the transcript is retained evidence'
  acas_note 'it is shredded and unlinked by the EXIT trap, on every exit path'
}

# LOG SCANNING -- the workaround for the unconditional `exit 0' Every frozen
# compile script ends `exit 0' unconditionally (see the header), so their exit
# status carries no information.

# the artifact produced: the frozen scripts pass -D_FORTIFY_SOURCE=1
# ([general/comp-gl.sh:L2] and its siblings) on a toolchain that already
# defines it. FATAL -- always fails the build.

# `No such file or directory' is matched WITHOUT a colon anchor, because a
# missing cobmysqlapi.o produces.

# indicate a missing artifact -- `undefined reference', `cannot find -l' -- are
# classified FATAL above, which is what makes the default safe.

# With copybooks/ACAS-SQLstate-error-list.cob absent, that is exactly what
# analMT, auditMT and glpostingMT do. A semantic error, by contrast, DOES reach
# the listing.
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
         [presql2-latest.zip:presql2-package/cobmysqlapi38.sh]. Re-run step 2 (--from 2) and do
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
         [presql2-latest.zip:presql2-package/cobmysqlapi38.c:L127] and exits 5 when it is absent;
         it then prefix-validates six cards in the fixed order DBHOST=, DBUSER=,
         DBPASSWD=, DBNAME=, DBPORT=, DBSOCKET= and exits 6 on any mismatch
         [presql2-latest.zip:presql2-package/cobmysqlapi38.c:L134-L172]. The file is written by
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

# STEP 4/5 -- run common/comp-common.sh UNMODIFIED What it does, in its own
# order, so the expected output is known.

# L54 *UNL.cbl L57 *RES.cbl L59 exit 0 (unconditional) A frozen anomaly worth
# knowing and NOT fixing (R-4).

acas_step4_comp_common() {
  acas_banner 4 'run common/comp-common.sh UNMODIFIED'

  local common_dir="$ACAS_BUILD/common"
  [[ -f "$common_dir/comp-common.sh" ]] || acas_die "$EX_STEP4" \
    "$common_dir/comp-common.sh is absent; prepare the build tree first."
  [[ -s "$common_dir/cobmysqlapi.o" ]] || acas_die "$EX_STEP4" \
    "$common_dir/cobmysqlapi.o is absent or empty." \
    '[common/comp-common.sh:L26] links it as a bare filename resolved against' \
    'the current directory, so it must be present here before the script runs.' \
    'Run step 2 (--from 2). [presql2-latest.zip:presql2-package/cobmysqlapi38.sh]'

  acas_write_presql2_param "$common_dir" presql2

  # No-follow, exclusive, 0600 -- the same treatment presql2.param gets.
  local log="$ACAS_LOG_DIR/comp-common.log"
  acas_create_private_file "$log" 'the comp-common.sh build log' "$EX_STEP4"

  # DEVIATION 5 of 6 -- COBCPY and COB_COPY_DIR are set for this invocation
  # only.
  acas_log "running: bash ./comp-common.sh   (cwd $common_dir)"
  acas_log "COBCPY=$ACAS_BUILD/copybooks (absolute; cf. [comp-all.sh:L9-L10])"
  acas_log "deadline: ${ACAS_TIMEOUT_BUILD}s (raise ACAS_TIMEOUT_BUILD on a slower host)"

  # The deadline is imposed with acas_deadline_prefix rather than with
  # acas_run_deadline because this output must reach the log through `tee' and
  # acas_run_deadline cannot be piped.
  local rc=0 started elapsed
  acas_deadline_prefix "$ACAS_TIMEOUT_BUILD"
  started="$SECONDS"
  # `< /dev/null' -- see acas_run_deadline for why every delegated child gets it
  #. It matters most HERE: this frozen script invokes presql2 28 times
  # [common/comp-common.sh:L25] and presql2 prompts for a parameter it cannot
  # resolve, so an inherited stdin turns the longest step in the build into a hang.
  (
    cd "$common_dir" \
      && exec "${ACAS_DEADLINE_ARGV[@]}" \
           env "COBCPY=$ACAS_BUILD/copybooks" \
               "COB_COPY_DIR=$ACAS_BUILD/copybooks" \
               bash ./comp-common.sh
  ) < /dev/null 2>&1 | tee -a "$log" || rc=$?
  elapsed=$(( SECONDS - started ))

  # `pipefail' is set, so rc is the subshell's status whenever tee succeeded.
  acas_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_BUILD" \
    ACAS_TIMEOUT_BUILD 'comp-common.sh' "$EX_STEP4"

  # rc is reported, never trusted: [common/comp-common.sh:L59] is a bare exit
  # 0.
  acas_log "comp-common.sh returned $rc (informational only -- L59 is an unconditional exit 0)"

  acas_scan_build_log "$log" 'comp-common.sh' "$EX_STEP4"
  acas_shred_param_files
}

# STEP 5/5 -- run comp-all.sh UNMODIFIED [comp-all.sh:L9-L10] exports
# COBCPY=../copybooks and COB_COPY_DIR=../copybooks -- relative, and correct
# because every compile runs with its own directory as the cwd.

# So expect that stage TWICE in a full run: do not deduplicate it, and do not
# drop step 4 as redundant.
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

  acas_write_presql2_param "$ACAS_BUILD/common" presql2

  # Same treatment as the comp-common.sh log above.
  local log="$ACAS_LOG_DIR/comp-all.log"
  acas_create_private_file "$log" 'the comp-all.sh build log' "$EX_STEP5"

  acas_log "running: bash ./comp-all.sh   (cwd $ACAS_BUILD)"
  acas_note 'comp-all.sh ends by cd-ing into stock/ and never returns to the top,'
  acas_note 'so it is run in a subshell and this script'"'"'s own cwd is unaffected'
  acas_log "deadline: ${ACAS_TIMEOUT_BUILD}s (raise ACAS_TIMEOUT_BUILD on a slower host)"

  # Same shape as step 4: piped to tee, so the deadline prefix is applied here
  # and the verdict is reached in this shell.
  local rc=0 started elapsed
  acas_deadline_prefix "$ACAS_TIMEOUT_BUILD"
  started="$SECONDS"
  # `< /dev/null' -- see acas_run_deadline. comp-all.sh compiles every
  # application directory, so a single cobc that decides to read stdin would stall
  # the whole step.
  (
    cd "$ACAS_BUILD" && exec "${ACAS_DEADLINE_ARGV[@]}" bash ./comp-all.sh
  ) < /dev/null 2>&1 | tee -a "$log" || rc=$?
  elapsed=$(( SECONDS - started ))

  acas_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_BUILD" \
    ACAS_TIMEOUT_BUILD 'comp-all.sh' "$EX_STEP5"

  acas_log "comp-all.sh returned $rc (informational only -- L45 is an unconditional exit 0)"

  acas_scan_build_log "$log" 'comp-all.sh' "$EX_STEP5"
  acas_shred_param_files
}

# More reliable than any text scan: they inspect the products of the build
# rather than the prose about it.
declare -a ACAS_MISSING_ARTIFACTS=()

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

  # common/ : bridges, handlers, date modules, loaders
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

  # The four ledger subsystems: every in-scope program must exist as a `-m'
  # module the menu can load, and each menu itself as a `-x' executable.
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

acas_finalise() {
  acas_stage 'Post-build: loader cache and module search path'

  if acas_have ldconfig; then
    # Under a deadline like everything else.
    acas_deadline_prefix "$ACAS_TIMEOUT_PROBE"
    if "${ACAS_DEADLINE_ARGV[@]}" ldconfig < /dev/null 2>/dev/null; then
      acas_log 'refreshed the shared-library cache (ldconfig)'
    else
      acas_warn 'ldconfig failed (root privileges are usually required); the compiled modules may not resolve libmysqlclient at run time.'
    fi
  fi

  # COB_LIBRARY_PATH must cover all six build directories so that the compiled
  # modules resolve when harness/run_cobol_scenario.sh drives a menu.
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

# =============================================================================
# THE PROVENANCE ATTESTATION
#
# WHAT DEFINES THE BEHAVIOURAL ORACLE MUST BE A REVIEWED SOURCE CHANGE, NEVER
# AMBIENT CONFIGURATION. Two of this script's own options can substitute the
# bytes the oracle is built from:
#
#   ACAS_PRESQL2_SHA256=HEX  accepts a REPLACEMENT presql2-latest.zip whose digest
#                            is not the pinned ACAS_PRESQL2_SHA256_EXPECTED, and
#                            the preSQL translator is what turns every *MT.scb into
#                            the *MT.cbl bridge that is actually compiled.
#   ACAS_COBMYSQLAPI_OBJ=F   reuses an ALREADY-COMPILED cobmysqlapi.o instead of
#                            building it from the source vendored in that package.
#                            Every bridge, handler and loader links it, and the
#                            package also ships two SUPERSEDED variants that must
#                            not be used (old-apis/cobmysqlapi.005.c and
#                            old-apis/cobmysqlapi3.c), so a renamed old API or an
#                            arbitrary prebuilt object could silently define the
#                            supposed specification.
#
# Both remain available, because a build is a thing one debugs. What they must not
# do is silently produce EVIDENCE. So every full build publishes what it was
# actually built from, and `harness/reset_db.sh` reads that file and refuses to set up
# the comparison when an override was used or when the compiled modules no
# longer match the ones the attestation covers.
#
# WRITTEN ONLY AFTER A FULL FIVE-STEP SEQUENCE, from acas_main -- a partial or
# --only run leaves no attestation at all, which is the honest outcome: a
# half-built tree has no provenance to state.
#
# The format is deliberately flat TAB-separated text rather than JSON: it is read
# by a shell script with `while IFS=', so it needs no parser and cannot fail on a
# quoting subtlety at the exact moment it is meant to be establishing trust.
# =============================================================================
# VERSION 2 ADDS THE SOURCE-TRANSFORMATION DISCLOSURE. A version 1
# attestation described only the two IDENTITY substitutions and said nothing about the
# nine shims that edit the build copy of frozen sources, so `overrides-used no' read as
# "this is the unmodified oracle" for a build that was not. Version 2 publishes the
# register: a count, a set digest, one record per transformed path carrying its FROZEN
# and BUILD digests, and `oracle-source-is-frozen' stating the conclusion outright.
# harness/reset_db.sh understands version 2 and refuses version 1, deliberately: an
# attestation that cannot state whether the sources were transformed is not evidence
# about the frozen specification.
readonly ACAS_ATTESTATION_VERSION='2'
readonly ACAS_ATTESTATION_BASENAME='oracle-attestation.txt'

#  THE CANONICAL cobmysqlapi.o PATH, and why merely being SET is not an override.
#  `harness/Dockerfile.gnucobol' exports ACAS_COBMYSQLAPI_OBJ=/usr/local/lib/acas/
#  cobmysqlapi.o [harness/Dockerfile.gnucobol:L990] and builds the object THERE,
#  from the vendored source, with the recovered rule verbatim: `gcc
#  -I/usr/local/mysql/include -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC'
#  [harness/Dockerfile.gnucobol:L478] then `install -m 0644' to that path
#  [harness/Dockerfile.gnucobol:L479].
#  That is reviewed provenance -- AAP section 0.5.2 recovered exactly this rule from
#  the vendored package -- so the variable pointing THERE is the NORMAL case and
#  step 2 simply reuses the object rather than recompiling it. What must be flagged
#  is the variable pointing SOMEWHERE ELSE: an object of unknown origin, which is
#  the route by which a build of one of the two SUPERSEDED C sources the archive
#  also ships -- presql2-package/old-apis/cobmysqlapi.005.c and .../cobmysqlapi3.c,
#  alongside the current presql2-package/cobmysqlapi38.c that is the one actually
#  used -- would reach the link line without anyone noticing. The image probes for
#  the first of those two so that old-apis/ is known to exist and be left unused
#  [harness/Dockerfile.gnucobol:L457-L458].
readonly ACAS_CANONICAL_COBMYSQLAPI_OBJ='/usr/local/lib/acas/cobmysqlapi.o'

# The digest of the compiled module set, computed the same way here and in
# reset_db.sh: every *.so under the six build directories, sorted by path, each
# hashed, and the whole listing hashed again. This is what BINDS the attestation to
# the artifacts -- replacing a single .so after the build invalidates it.
#
# WHAT IT IS NOT: evidence of a reproducible build. Three consecutive clean builds
# of this tree were measured and produced three different set digests, because cobc
# embeds build-varying material in the C it generates. The value therefore proves
# only that the modules on disk NOW are the ones this attestation was written about
# -- which is exactly what the consumer needs, since it is about to execute them --
# and it must never be quoted as showing that two builds agree.
acas_module_set_digest() {
  local dir
  {
    for dir in "${ACAS_COMPILE_DIRS[@]}"; do
      find "$ACAS_BUILD/$dir" -maxdepth 1 -type f -name '*.so' -print 2>/dev/null
    done
  } | LC_ALL=C sort | while IFS= read -r module; do
    sha256sum "$module" 2>/dev/null || printf 'UNREADABLE  %s\n' "$module"
  done | sha256sum | cut -d' ' -f1
}

acas_module_set_count() {
  local dir total=0 n
  for dir in "${ACAS_COMPILE_DIRS[@]}"; do
    n="$(find "$ACAS_BUILD/$dir" -maxdepth 1 -type f -name '*.so' 2>/dev/null | wc -l)"
    total=$(( total + n ))
  done
  printf '%s' "$total"
}

acas_file_digest() {
  local path="$1"
  if [[ -f "$path" ]]; then
    sha256sum "$path" | cut -d' ' -f1
  else
    printf 'ABSENT'
  fi
}

# acas_source_transform_records  One TAB-separated record per registered transformation.
#
#   source-transform<TAB><relpath><TAB><frozen digest><TAB><build digest><TAB><reason>
#
# The FROZEN digest is taken from $ACAS_REPO, which this script never writes, so a
# reader can recompute both sides independently and diff the two files. `ABSENT` on the
# frozen side is the correct and expected value for the one shim that CREATES a file
# the checkout does not contain.
acas_source_transform_records() {
  local entry path reason
  for entry in "${ACAS_SOURCE_TRANSFORMS_APPLIED[@]}"; do
    path="${entry%%|*}"
    reason="${entry#*|}"
    printf 'source-transform\t%s\t%s\t%s\t%s\n' \
      "$path" \
      "$(acas_file_digest "$ACAS_REPO/$path")" \
      "$(acas_file_digest "$ACAS_BUILD/$path")" \
      "$reason"
  done
}

# The digest OVER the transformation records, so one changed shim changes one value a
# consumer can compare. Computed from the records themselves rather than from the
# register text, so editing a reason without changing a source is visible too.
acas_source_transform_set_digest() {
  acas_source_transform_records | sha256sum | cut -d' ' -f1
}

acas_publish_attestation() {
  acas_stage 'Post-build: the provenance attestation'

  local target="$ACAS_BUILD/$ACAS_ATTESTATION_BASENAME"
  local archive="$ACAS_REPO/presql2-latest.zip"

  # WAS EITHER IDENTITY OVERRIDDEN? Recorded as a fact, not as a judgement -- the
  # refusal belongs to the consumer, so that this script stays usable for debugging.
  local digest_override='no' object_redirected='no'
  [[ -n "${ACAS_PRESQL2_SHA256-}" ]] && digest_override='yes'
  if [[ -n "${ACAS_COBMYSQLAPI_OBJ-}" &&
        "${ACAS_COBMYSQLAPI_OBJ}" != "$ACAS_CANONICAL_COBMYSQLAPI_OBJ" ]]; then
    object_redirected='yes'
  fi

  #  WHERE THE OBJECT ACTUALLY CAME FROM, recorded as a fact rather than a verdict.
  #  Only two values are legitimate: the image built it from the vendored source, or
  #  step 2 compiled it from the vendored source during this run.
  local object_provenance='unknown'
  case "${ACAS_COBMYSQLAPI_SRC-}" in
    "$ACAS_CANONICAL_COBMYSQLAPI_OBJ")
      object_provenance='image-built-from-vendored-source' ;;
    "$ACAS_BUILD/.acas-cobmysqlapi/cobmysqlapi.o")
      object_provenance='compiled-from-vendored-source-this-run' ;;
    '') object_provenance='unresolved' ;;
    *)  object_provenance='operator-supplied' ;;
  esac

  #  THE ARCHIVE MUST MATCH ITS PIN, checked independently of the override variable
  #  so that a substituted archive is caught even when nobody set anything. This is
  #  belt-and-braces: step 1 already asserts it, but the attestation must be able to
  #  stand alone as evidence without the reader having to trust that step 1 ran.
  local archive_matches_pin='no'
  [[ "$(acas_file_digest "$archive")" == "$ACAS_PRESQL2_SHA256_EXPECTED" ]] &&
    archive_matches_pin='yes'

  local overrides='no'
  if [[ "$digest_override" == 'yes' || "$object_redirected" == 'yes' ||
        "$archive_matches_pin" == 'no' ||
        "$object_provenance" == 'operator-supplied' ||
        "$object_provenance" == 'unresolved' ]]; then
    overrides='yes'
  fi

  local cobc_version cc_version
  cobc_version="$(cobc --version 2>/dev/null | head -1)"
  cc_version="$(cc --version 2>/dev/null | head -1)"
  [[ -n "$cobc_version" ]] || cobc_version='UNKNOWN'
  [[ -n "$cc_version" ]] || cc_version='UNKNOWN'

  #  THE TOOLCHAIN BY DIGEST AS WELL AS BY VERSION STRING. A version string is what
  #  a compiler chooses to say about itself; the digest is what it IS. Two builds can
  #  both report `cobc (GnuCOBOL) 3.2.0' from different binaries, so recording only
  #  the string would leave the attestation unable to distinguish them. These are
  #  recorded, not re-verified at parity time: stage 2 executes the already-compiled
  #  modules and never invokes a compiler, so the value that BINDS the run is
  #  module-set-sha256 above. The digests are here so the evidence can be audited
  #  after the fact -- which is the whole point of an attestation.
  local cobc_path cc_path
  cobc_path="$(command -v cobc 2>/dev/null || true)"
  cc_path="$(command -v cc 2>/dev/null || true)"

  local module_digest module_count
  module_digest="$(acas_module_set_digest)"
  module_count="$(acas_module_set_count)"

  #  WHETHER THE COMPILED ORACLE IS THE FROZEN SOURCE, answered from the register
  #  rather than asserted. `no' whenever any transformation is declared, which today
  #  is always -- the nine shims are what let the compiled cycle reach MySQL at all.
  #  The value exists so that a tree in which they became unnecessary would say `yes'
  #  and be believed, and so that no consumer has to infer the answer from a count.
  local source_is_frozen='yes' transform_digest
  (( ${#ACAS_SOURCE_TRANSFORMS_APPLIED[@]} == 0 )) || source_is_frozen='no'
  transform_digest="$(acas_source_transform_set_digest)"

  #  THE PREVIOUS RUN'S ATTESTATION IS REMOVED BEFORE THIS ONE IS WRITTEN, and that is
  #  not tidiness -- it is what makes `--no-refresh' work at all. This function ends by
  #  `chmod 0444', and `harness/Dockerfile.gnucobol' runs the container as a NON-ROOT
  #  user [harness/Dockerfile.gnucobol USER ${ACAS_UID}:${ACAS_GID}], so a read-only
  #  file cannot be truncated by the redirection below. `--no-refresh' deliberately
  #  PRESERVES the build tree, so the file is still there from the previous build and
  #  the redirection failed with "Permission denied" -- exit 77, in precisely the use
  #  case the option exists for. Worse than the error: steps 1 to 5 had already
  #  recompiled every module, so the surviving attestation then described a module set
  #  that no longer existed and `harness/reset_db.sh' refused the oracle on its
  #  module-set digest, with the documented in-place rebuild unable to recover it.
  #  Only THIS function's own artifact is removed, only after a full five-step
  #  sequence has succeeded, and the write below is still asserted -- so a genuine
  #  failure (a full volume, a read-only mount) is still fatal rather than silent.
  if [[ -e "$target" ]]; then
    chmod u+w "$target" 2>/dev/null || true
    rm -f "$target" 2>/dev/null || true
  fi

  {
    printf 'attestation-version	%s
' "$ACAS_ATTESTATION_VERSION"
    printf 'built-at-utc	%s
' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'presql2-archive	%s
' "$archive"
    printf 'presql2-sha256	%s
' "$(acas_file_digest "$archive")"
    printf 'presql2-pinned-sha256	%s
' "$ACAS_PRESQL2_SHA256_EXPECTED"
    printf 'presql2-digest-override	%s
' "$digest_override"
    printf 'cobmysqlapi-object	%s
' "${ACAS_COBMYSQLAPI_SRC:-UNKNOWN}"
    printf 'cobmysqlapi-sha256	%s
' "$(acas_file_digest "${ACAS_COBMYSQLAPI_SRC-}")"
    printf 'cobmysqlapi-redirected	%s
' "$object_redirected"
    printf 'cobmysqlapi-provenance	%s
' "$object_provenance"
    printf 'presql2-matches-pin	%s
' "$archive_matches_pin"
    printf 'cobc-version	%s
' "$cobc_version"
    printf 'cobc-path	%s
' "${cobc_path:-UNKNOWN}"
    printf 'cobc-sha256	%s
' "$(acas_file_digest "$cobc_path")"
    printf 'cc-version	%s
' "$cc_version"
    printf 'cc-path	%s
' "${cc_path:-UNKNOWN}"
    printf 'cc-sha256	%s
' "$(acas_file_digest "$cc_path")"
    printf 'module-count	%s
' "$module_count"
    printf 'module-set-sha256	%s
' "$module_digest"
    printf 'overrides-used	%s
' "$overrides"
    #  THE SOURCE-TRANSFORMATION DISCLOSURE. Published
    #  UNCONDITIONALLY, so an attestation can never be silent about it: a reader who
    #  finds no `source-transform' record knows there were none, rather than not
    #  knowing whether the producer looked.
    printf 'oracle-source-is-frozen	%s
' "$source_is_frozen"
    printf 'source-transforms	%s
' "${#ACAS_SOURCE_TRANSFORMS_APPLIED[@]}"
    printf 'source-transform-set-sha256	%s
' "$transform_digest"
    acas_source_transform_records
  } > "$target" || acas_die "$EX_FINALISE" \
    "the provenance attestation could not be written to $target." \
    'Without it harness/reset_db.sh will refuse to set up the comparison,' \
    'because an oracle that cannot say what it was built from cannot arbitrate.'

  chmod 0444 "$target" 2>/dev/null || true

  acas_log "attestation:  $target"
  acas_log "  presql2 archive     $(acas_file_digest "$archive")"
  acas_log "  pinned digest       $ACAS_PRESQL2_SHA256_EXPECTED"
  acas_log "  cobmysqlapi.o       $(acas_file_digest "${ACAS_COBMYSQLAPI_SRC-}")"
  acas_log "  toolchain           $cobc_version / $cc_version"
  acas_log "  modules             $module_count (*.so), set digest $module_digest"
  acas_log "  frozen sources      $source_is_frozen"
  acas_log "  source transforms   ${#ACAS_SOURCE_TRANSFORMS_APPLIED[@]}, set digest $transform_digest"
  if [[ "$source_is_frozen" != 'yes' ]]; then
    acas_warn "THIS ORACLE WAS COMPILED FROM TRANSFORMED SOURCES, and the attestation now says so. ${#ACAS_SOURCE_TRANSFORMS_APPLIED[@]} build-copy file(s) differ from the frozen checkout; every one is listed in $target as a source-transform record carrying its frozen and build digests and the reason for it. They are connectivity and IF-scope repairs without which the compiled cycle cannot reach MySQL, and none alters an accounting computation, a posting order, a control total or a rejection path -- but a parity verdict produced against this build is a verdict against a DISCLOSED-TRANSFORMED oracle and must never be described as one against the unmodified frozen specification. The frozen checkout itself is untouched: diff $ACAS_REPO against $ACAS_BUILD to see every difference."
  fi
  if [[ "$overrides" == 'yes' ]]; then
    acas_warn "THIS ORACLE CANNOT PRODUCE EVIDENCE: its identity was not established from the reviewed sources alone (presql2-digest-override=$digest_override, presql2-matches-pin=$archive_matches_pin, cobmysqlapi-redirected=$object_redirected, cobmysqlapi-provenance=$object_provenance). The attestation records that and harness/reset_db.sh will refuse to set up a comparison against this build. Rebuild without ACAS_PRESQL2_SHA256, and without pointing ACAS_COBMYSQLAPI_OBJ anywhere other than $ACAS_CANONICAL_COBMYSQLAPI_OBJ. To replace either legitimately, make it a REVIEWED SOURCE CHANGE -- update the vendored archive and ACAS_PRESQL2_SHA256_EXPECTED together in the same commit."
  else
    acas_log "  provenance          $object_provenance"
    acas_log '  overrides           none -- this oracle may produce evidence'
  fi
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

# MAIN Strictly sequential (R-3). No step is backgrounded, no step is
# parallelised, and the order is the one the plan prescribes.
acas_main() {
  acas_parse_args "$@"

  # Before ANY external command is spawned: a malformed budget must be a
  # startup usage error, never something discovered hours into a build.
  acas_resolve_deadlines

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

  # The assertions and the summary run only after a full sequence.
  if (( ACAS_ONLY_STEP == 0 && ACAS_START_STEP == 1 )); then
    acas_assert_artifacts
    acas_finalise
    acas_publish_attestation
    acas_print_summary
  else
    acas_stage 'Partial run: artifact assertions and finalisation skipped'
    acas_note 'run without --from/--only to build the whole oracle and verify it'
  fi

  exit "$EX_OK"
}

acas_main "$@"
