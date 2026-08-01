#!/usr/bin/env bash
# =============================================================================
# harness/reset_db.sh
#
# Drop the ACASDB schema, re-apply the frozen `mysql/ACASDB.sql` VERBATIM, and
# re-seed by delegating to harness/seed.sh.
#
# This is STAGE 5 of the eight-stage parity protocol:
#
#     seed -> run(COBOL) -> dump -> normalize -> RESET -> run(Python) -> dump -> diff
#                                                 ^^^^^
#
# and it is the stage the whole comparison rests on. The acceptance condition
# the harness exists to satisfy is an EMPTY diff between the two dumps, so both
# cycles must start from byte-for-byte the same seeded state. If this reset is
# not exact, the Python side starts from a different premise than the COBOL side
# did and a non-empty diff proves nothing at all. The plan's conclusion that "a
# non-empty diff is always a real behavioral difference and never an artefact of
# the comparison" is true only because this script is exact.
#
# The canonical invocation is documented with the rest of the cycle at
# [harness/docker-compose.yml:L263-L274]:
#
#     C="docker compose -f harness/docker-compose.yml run --rm -T gnucobol"
#     S=harness/scenarios/clean_batch_gl.yaml
#     ...
#     $C harness/reset_db.sh            "$S"
#
# -----------------------------------------------------------------------------
# THE ONE DESIGN FACT THAT SHAPES THIS ENTIRE SCRIPT: THE DROP IS IN THE FROZEN
# FILE
# -----------------------------------------------------------------------------
# R-3 forbids schema evolution of any kind -- "No new tables, columns, indexes,
# constraints, views, triggers or DDL statements. No migration tooling." A
# script whose job is "drop and re-create 33 tables" would seem to need DDL of
# its own. It does not, because the frozen dump already carries it: verified on
# this checkout, `mysql/ACASDB.sql` contains 33 `DROP TABLE IF EXISTS`
# statements, one immediately before each of its 33 `CREATE TABLE` statements,
# the first at [mysql/ACASDB.sql:L28]:
#
#     DROP TABLE IF EXISTS `ANALYSIS-REC`;
#
# RE-APPLYING THE FROZEN FILE *IS* THE DROP-AND-RECREATE. So this script emits
# ZERO DDL. There is no hand-written DROP TABLE list, no DROP DATABASE /
# CREATE DATABASE pair, no TRUNCATE loop, no DELETE FROM loop and no generated
# DDL anywhere below. The file is streamed to the client and its own statements
# do the work. Every SQL statement this script issues itself is a read-only
# SELECT (the readiness probe, the autocommit assertion, the privilege
# assertion and the post-apply verification).
#
# -----------------------------------------------------------------------------
# THREE MORE PROPERTIES OF THE FROZEN FILE THAT THE IMPLEMENTATION DEPENDS ON
# -----------------------------------------------------------------------------
#   1. IT CONTAINS NO `CREATE DATABASE` AND NO `USE`. Verified: zero of each.
#      The database must therefore already exist AND be named on the client
#      command line. The vendor MariaDB entrypoint creates it once from
#      MARIADB_DATABASE=ACASDB [harness/Dockerfile.mariadb:L288]; this script
#      resets the database's CONTENTS, never its existence. Forgetting
#      --database is the single most likely way to get a confusing failure.
#
#   2. IT MANAGES ITS OWN SESSION STATE. [mysql/ACASDB.sql:L13-L22] sets
#      character set, NAMES, TIME_ZONE, UNIQUE_CHECKS, FOREIGN_KEY_CHECKS,
#      SQL_MODE and SQL_NOTES, and the tail restores every one of them. This
#      script therefore adds NONE of its own -- no SET FOREIGN_KEY_CHECKS, no
#      SET UNIQUE_CHECKS, no SET SQL_MODE, no SET NAMES, no SET TIME_ZONE.
#      Adding any would be a statement the frozen artifact did not contain and
#      would change which session state is in force.
#
#   3. ITS 66 `ALTER TABLE` HITS ARE COMMENTS, NOT STATEMENTS. Every one sits
#      inside a mysqldump version guard,
#      `/*!40000 ALTER TABLE `X` DISABLE KEYS */` [mysql/ACASDB.sql:L45], in
#      the (empty) per-table data section. There are ZERO real
#      schema-evolution ALTER TABLE statements, which is why the invariant
#      check below anti-anchors on `^[^/]*ALTER TABLE` instead of counting the
#      naive pattern.
#
# -----------------------------------------------------------------------------
# THE CHARSET CAVEAT IS FROZEN STATE AND IS NOT FIXED (R-4)
# -----------------------------------------------------------------------------
# [mysql/ACASDB.sql:L9-L11], verbatim:
#
#     --  THERE IS NOT ANY DATA RECORDS PRESENT HERE --
#     --   YOU MAY NEED TO CHANGE the defined Character set in all tables
#     --   TO MATCH ANY OF YOUR REQUIREMENTS IF THEY DIFFER
#
# The dump sets `SET NAMES utf8mb4` at [mysql/ACASDB.sql:L16] while all 33
# tables declare `DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci`. The
# maintainer flagged the inconsistency himself and it is part of the
# specification. "A defect reproduced is correct; a defect fixed is a failure."
# So the file reaches the client BYTE-FOR-BYTE:
#
#     NO sed, awk, tr or iconv on the way in.
#     NO edited local copy of the schema inside harness/.
#     NO --default-character-set override contradicting the file's own SET NAMES.
#
# and the post-apply verification asserts all 33 tables came back
# `utf8mb3_general_ci`, so a transformation on the way in is caught rather than
# assumed absent.
#
# -----------------------------------------------------------------------------
# AUTOCOMMIT IS ASSERTED, NEVER SET (R-3, R-4)
# -----------------------------------------------------------------------------
# [common/glbatchLD.cbl:L9-L13], verbatim:
#
#     *>  This modules uses commit and rollback so *
#     *>  you MUST ensure that autocommit is OFF   *
#     *>   in the rdb settings. It is as default   *
#     *>   set ON.                                 *
#
# That banner is not unique to the batch loader -- the whole `common/*LD.cbl`
# family depends on it, and the maintainer records the consequence inline at
# [common/analLD.cbl:L442]: "These do not work during testing with mariadb -
# Non transactional model or autocommit set ON."
#
# The setting has exactly ONE authority: harness/Dockerfile.mariadb, which
# writes `autocommit=0` into /etc/mysql/conf.d/99-acas-oracle.cnf
# [harness/Dockerfile.mariadb:L231-L258]. This script reads it and REFUSES to
# reset when it is on. It never issues `SET autocommit`, not even for the
# duration of the DDL: doing so would create a second authority and corrupt the
# loaders' commit boundaries. It is asserted BEFORE the apply and again AFTER
# it, because the frozen file changes session variables and the claim that it
# left this one alone has to be proved rather than assumed.
#
# DDL under autocommit=0 is still durable -- InnoDB commits CREATE TABLE and
# DROP TABLE implicitly, as [harness/Dockerfile.mariadb:L227-L229] records --
# and stage 3 proves it empirically by reconnecting in a FRESH session and
# re-counting the tables, rather than taking the manual's word for it.
#
# -----------------------------------------------------------------------------
# WHERE THIS FILE SITS, AND WHAT IT NEVER TOUCHES
# -----------------------------------------------------------------------------
# harness/ is the compiled oracle and is a SIBLING of acas_posting/, never a
# sub-package. This script imports nothing from acas_posting, creates no
# harness/__init__.py, and reaches compiled COBOL only indirectly and
# out-of-process, through harness/seed.sh -- the sanctioned use under R-1, which
# confines COBOL to harness/ as a comparison and SEEDING utility.
#
# $ACAS_REPO is mounted READ-ONLY (`../:/repo:ro`). This script only ever READS
# $ACAS_REPO/mysql/ACASDB.sql. Any diff touching the frozen tree "is a defect in
# the migration, regardless of how harmless it appears", so nothing is written
# there: the run log goes to $ACAS_OUT/reset/ and the sequential lock to
# $ACAS_OUT.
#
# STRICTLY SEQUENTIAL (R-3): no `&`, no `xargs -P`, no job control, and a plain
# lock file that refuses a second concurrent reset of the shared database.
#
# DETERMINISTIC AND IDEMPOTENT (R-6): running it twice leaves the database in
# exactly the same state both times -- the frozen file's `DROP TABLE IF EXISTS`
# makes that natural, and the verification stage proves it. The only wall-clock
# reading in the script is in the run log under $ACAS_OUT/reset/, which is never
# part of a comparison; nothing under $ACAS_OUT/<scenario>/ is written here, so
# tests/determinism/test_two_runs_byte_identical.py cannot see it.
#
# RULES PROVENANCE
#   There is no user rules document for this project: `review_rules` returns
#   "No user rules provided." The binding rules R-1..R-6 come from the Agent
#   Action Plan and are cited inline as (R-n). Where they are silent this script
#   holds to enterprise-standard best practice.
#     R-1 no COBOL at runtime          R-2 zero binary floating point
#     R-3 no schema change, sequential R-4 anomalies reproduced, never fixed
#     R-5 full traceability            R-6 compiled behaviour is the tie-breaker
#
# USAGE
#   Run `harness/reset_db.sh --help`.
# =============================================================================

# Strict mode. -E propagates the ERR trap into functions and subshells so an
# unexpected failure is attributed to a line number instead of vanishing.
#
# `set -e` is deliberately NOT relied on to police the two operations whose
# status is DATA rather than an accident: the schema apply (whose failure must
# produce a named diagnostic and the client's own output) and the delegated
# seed (whose exit code carries meaning -- 70..73 from seed.sh itself, or a
# loader's 128/64/16). Both are invoked with errexit suspended for exactly the
# length of the call and their status captured and classified.
set -Eeuo pipefail

# Word splitting on newlines and tabs only, so a path containing a space can
# never be split apart. Every expansion below is quoted regardless. Note the
# consequence: "${array[*]}" would join on a NEWLINE, so acas_join_words exists
# for one-line messages.
IFS=$'\n\t'

# An unmatched glob expands to nothing rather than to the pattern text.
shopt -s nullglob

# Nothing this script writes is group- or world-readable. No credential is ever
# written to a file at all (see acas_sql_scalar), so this is defence in depth
# rather than the primary protection.
umask 077

# -----------------------------------------------------------------------------
# Exit codes.
#
# CHOSEN NOT TO COLLIDE WITH ANY CODE THIS SCRIPT MIGHT PROPAGATE. The delegated
# seed uses 70..73 for its own failures [harness/seed.sh] and propagates a
# loader's 128, 64 or 16 [common/masterLD.sh:L37-L39]; harness/build_oracle.sh
# uses 64..67 and 71..77. This script therefore keeps to the 80..88 band, so the
# rule for an automated caller is unambiguous:
#
#     0              clean reset, and a clean re-seed
#     80..88         THIS SCRIPT failed one of its own stages
#     anything else  harness/seed.sh's own status, propagated verbatim
# -----------------------------------------------------------------------------
readonly EX_OK=0
readonly EX_USAGE=80          # bad command line
readonly EX_PRECONDITION=81   # environment, output directory or seed.sh assertion
readonly EX_DATABASE=82       # MariaDB unreachable, or credentials rejected
readonly EX_AUTOCOMMIT=83     # autocommit is not off -- see acas_assert_autocommit
readonly EX_PRIVILEGE=84      # the account cannot perform the drop and re-apply
readonly EX_FROZEN=85         # mysql/ACASDB.sql has been MODIFIED -- see §invariants
readonly EX_APPLY=86          # the client rejected part of the frozen schema
readonly EX_VERIFY=87         # the post-apply state is not what the schema defines
readonly EX_CONCURRENT=88     # another reset holds the sequential lock

# =============================================================================
# THE FROZEN ARTIFACT
# =============================================================================

# The one file this script applies, relative to the read-only checkout.
readonly ACAS_RESET_SCHEMA_RELPATH='mysql/ACASDB.sql'

# Byte-for-byte digest of `mysql/ACASDB.sql` as committed: 1459 lines,
# 51008 bytes. The SAME value harness/Dockerfile.mariadb pins as
# ARG ACASDB_SCHEMA_SHA256, deliberately, so the image build and this script
# check one baseline rather than two.
#
# This pin CANNOT go stale: the file is frozen, so the check fails precisely --
# and only -- when someone commits the violation the plan forbids. It makes the
# "applied byte-for-byte" claim machine-checked rather than merely asserted.
readonly ACAS_RESET_SCHEMA_SHA256='094e588226f650672c3781d1737d7bf8be30be048ce6a788df81800a19326ed0'

# The 33 tables the frozen schema defines: 22 in scope for the posting cycle,
# 11 out of scope. 22 + 11 = 33. The reset recreates ALL 33 -- it applies the
# whole file and nothing but the whole file -- but only the 22 are ever
# compared, so only they carry a shape expectation below.
readonly ACAS_RESET_EXPECT_TABLES=33

# The 22 IN-SCOPE tables, each with the column count and single-column primary
# key the frozen schema declares. Read out of `mysql/ACASDB.sql` itself and
# cross-checked against the plan's own census, not transcribed by eye.
#
# Entry shape: <table>:<columns>:<primary key>
#
# The verification stage asserts every one of these, because a reset that
# produced the right NUMBER of tables with the wrong SHAPE would poison every
# downstream diff just as thoroughly.
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

# The 11 OUT-OF-SCOPE tables, recreated by the apply and never compared. Named
# so a reader can confirm the arithmetic rather than trust it, and so the
# secondary-index assertion can explain why STOCK-REC is exempt.
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
# apply: a `utf8mb4_*` reading would mean the file was transformed on the way in
# and the charset caveat at [mysql/ACASDB.sql:L9-L11] had been "fixed" (R-4).
readonly ACAS_RESET_COLLATION='utf8mb3_general_ci'

# The only tables in the whole schema carrying a NON-PRIMARY index, both out of
# scope: three secondary `KEY`s on STOCK-REC, and the one `UNIQUE KEY` that
# belongs to PLPAY-RECrg01 -- which also owns the schema's only composite primary
# key and its only FOREIGN KEY.
#
# Every one of the 22 IN-SCOPE tables carries PRIMARY and nothing else. That is
# exactly why harness/dump_tables.py can order by the primary key with no
# tie-breaking logic and still get a deterministic dump, and why no seeding or
# reset ordering is dictated by referential integrity -- so the frozen order is
# kept everywhere. Verifying it after every reset keeps that guarantee honest.
readonly -a ACAS_RESET_SECONDARY_INDEX_ALLOWED=(
  'STOCK-REC'
  'PLPAY-RECrg01'
)

# The six privileges the frozen file's own statements require of the applying
# account: DROP and CREATE for the 33 drop/create pairs, LOCK TABLES and INSERT
# for the 33 `LOCK TABLES ... WRITE` data sections, ALTER for the version-guarded
# DISABLE/ENABLE KEYS comments should the server honour them, and SELECT for the
# verification queries.
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
# configured for all three. ACAS_DB_SOCKET may legitimately be EMPTY -- Compose
# sets it so on purpose because the harness connects over TCP -- but it must be
# DECLARED, because an undeclared one means the caller never supplied the
# contract at all.
readonly -a ACAS_RESET_REQUIRED_ENV_NONEMPTY=(
  ACAS_REPO ACAS_OUT
  ACAS_DB_HOST ACAS_DB_PORT ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD
)
readonly -a ACAS_RESET_REQUIRED_ENV_DECLARED=(
  ACAS_DB_SOCKET
)

# Variables this script does not use itself but harness/seed.sh requires, so a
# --schema-only run does not demand them while a full reset fails early with a
# named cause instead of at the delegation boundary.
readonly -a ACAS_RESET_SEED_ENV_NONEMPTY=(
  ACAS_BUILD ACAS_DATA ACAS_LEDGERS ACAS_BIN
)

# -----------------------------------------------------------------------------
# Mutable state. Declared up front because `set -u` makes an unset reference
# fatal.
# -----------------------------------------------------------------------------
ACAS_RESET_SCHEMA=''             # absolute path to the frozen schema
ACAS_RESET_SCHEMA_ONLY=0         # --schema-only: apply the schema, skip the seed
ACAS_RESET_DATA_DIR=''           # --data-dir, forwarded verbatim to seed.sh
ACAS_RESET_DRY_RUN=0             # --dry-run
ACAS_RESET_SCENARIO=''           # optional positional scenario file
ACAS_RESET_LOG=''                # $ACAS_OUT/reset/reset.log
ACAS_RESET_LOCK=''               # $ACAS_OUT/.reset_db.lock, held for the run
ACAS_RESET_LOCK_HELD=0           # 1 once this process owns the lock
ACAS_RESET_APPLIED=0             # 1 once the frozen schema has been applied
ACAS_RESET_VERIFIED=0            # 1 once every post-apply assertion passed
ACAS_RESET_SEED_RC=''            # seed.sh's exit status, or '' if not run
ACAS_RESET_STAGE='startup'       # the stage a trap reports against
ACAS_RESET_SEED=''               # absolute path to harness/seed.sh
ACAS_RESET_DB_USER=''            # account used for the drop and re-apply
ACAS_RESET_DB_PASSWORD=''        # its password -- never printed, never in argv
ACAS_SQL_OUT=''                  # last successful query result
ACAS_SQL_DIAG=''                 # last client diagnostic, for error messages
ACAS_SQL_CLIENT=''               # resolved client binary: mariadb or mysql
ACAS_SQL_TLS_FLAG=''             # resolved TLS flag: '' or --skip-ssl
declare -a ACAS_RESET_SUMMARY=()      # the closing checklist
declare -a ACAS_RESET_WARN_SUMMARY=() # non-fatal findings, replayed at the end

# =============================================================================
# REPORTING
#
# Stage banners are numbered so the log reads as the deterministic staged
# orchestration the plan prescribes (R-6): explicit, ordered, individually
# reported, individually asserted.
#
# Everything printed here goes to standard output AND, once the log directory
# exists, to $ACAS_OUT/reset/reset.log. Nothing is written under
# $ACAS_OUT/<scenario>/, because the determinism test requires byte-identical
# scenario dumps and a clock reading in a compared file would break it.
# =============================================================================

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

# acas_die <exit-code> <headline> [detail-line]...
# Every abort names the artifact or setting at fault and, wherever the cause is
# frozen behaviour, cites its locator so the reader can verify the claim (R-5).
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

# Join the remaining arguments with single spaces. Needed because IFS is
# $'\n\t', so a bare "${array[*]}" would join on a NEWLINE and break a one-line
# message across several lines.
acas_join_words() {
  local IFS=' '
  printf '%s' "$*"
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

# Record one line of the closing checklist.
# acas_check <verdict> <detail...>
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
# message never reads "missing    :" with nothing after the colon.
# acas_list_or_none <element>...
acas_list_or_none() {
  if (( $# == 0 )); then
    printf 'none'
    return 0
  fi
  acas_join_words "$@"
}

# Membership test over elements passed by value, so the arrays stay readonly.
# acas_in_list <needle> <element>...
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

# =============================================================================
# TRAPS
#
# There is no credential FILE to shred: the password reaches the client through
# MYSQL_PWD only (see acas_sql_scalar), so it never appears in argv, never in
# `ps`, and never on disk. That is a stronger guarantee than a
# --defaults-extra-file plus a cleanup trap, and it is why this script creates no
# temporary credential file anywhere. `set -x` is never enabled, for the same
# reason.
#
# The EXIT trap releases the sequential lock and -- this is the important part --
# tells the operator whether the database was left mid-reset. A reset that failed
# AFTER the apply and BEFORE the seed leaves 33 empty tables, which is a
# perfectly valid schema and a completely invalid premise for a diff. Saying so
# is the difference between a diff that is known-meaningless and one that is
# silently wrong.
# =============================================================================

# Release the lock this process created, and only that one.
# shellcheck disable=SC2317  # reached only through the EXIT trap installed below,
# which shellcheck cannot follow; the body is live and is exercised by the
# concurrency validation case.
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
    # The seed "did not complete" covers both never having run and having run and
    # failed: in either case the database holds the empty schema and no seed data,
    # which is the fact the operator needs, so both take the specific message.
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

# =============================================================================
# USAGE
# =============================================================================
acas_usage() {
  cat <<'USAGE'
harness/reset_db.sh -- drop, re-apply the frozen ACASDB schema verbatim, re-seed.

Stage 5 of the eight-stage parity protocol:

    seed -> run(COBOL) -> dump -> normalize -> RESET -> run(Python) -> dump -> diff

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
     autocommit still off, and durability in a fresh session.
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
                      canonical invocation documented at
                      [harness/docker-compose.yml:L263-L274] --
                      `harness/reset_db.sh "$S"` -- works as written. It is
                      recorded for traceability and is NOT parsed here.

Options:
  --schema-only       Apply the frozen schema and STOP: 33 empty tables, no seed
                      data. Useful for a bare database, but note that the full
                      stage-5 contract is schema PLUS seed -- a dump taken after
                      --schema-only is NOT comparable with one taken after the
                      COBOL cycle.
  --data-dir PATH     Directory holding the Cobol flat files, forwarded verbatim
                      to harness/seed.sh. Default $ACAS_DATA.
  --dry-run           Print the plan -- the file to be applied, its asserted
                      invariants, the verification queries and the seed command
                      -- and exit without executing anything or touching the
                      database.
  -h, --help          Print this help and exit 0.

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

Optional environment:
  ACAS_DB_ADMIN_USER      Account used for the drop and re-apply. Defaults to
  ACAS_DB_ADMIN_PASSWORD  ACAS_DB_USER / ACAS_DB_PASSWORD, which Compose grants
                          ALL PRIVILEGES on the target schema, so an override is
                          normally unnecessary. Provided because
                          [harness/docker-compose.yml:L385-L396] contemplates the
                          root account being used for exactly this operation. The
                          12-character limit does NOT apply to an override: it is
                          a harness credential and never enters the COBOL
                          `RDB-Data` block.
  ACAS_DB_WAIT_TIMEOUT=N  Seconds to wait for MariaDB (default 180).
  ACAS_DB_AUTH_GRACE=N    Seconds to tolerate "Access denied" before failing
                          fast, capped at ACAS_DB_WAIT_TIMEOUT (default 15).

Exit codes:
  0        clean reset and clean re-seed
  80       usage           81  precondition
  82       database        83  autocommit is not off
  84       privilege      85  mysql/ACASDB.sql has been MODIFIED
  86       schema apply   87  post-apply verification
  88       another reset holds the sequential lock
  anything else  harness/seed.sh's own status, propagated verbatim: 70..73 for
                 its own failures, or a load program's 128 / 64 / 16
                 [common/masterLD.sh:L37-L39].

This script emits no DDL, writes nothing under $ACAS_REPO, never sets
autocommit, never passes --force to the client, and runs strictly sequentially.
USAGE
}


# =============================================================================
# ARGUMENTS
# =============================================================================
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
        # the --data-dir=* form below rejects it: an empty value almost always
        # means an unset variable was interpolated, and silently falling back to
        # $ACAS_DATA would seed from a directory the operator did not choose --
        # which is precisely how a state diff becomes meaningless. Both spellings
        # of the flag therefore behave identically.
        [[ -n "$ACAS_RESET_DATA_DIR" ]] || acas_die "$EX_USAGE" \
          '--data-dir was given an empty path.' \
          'If the default is wanted, omit the flag; harness/seed.sh then uses' \
          'the ACAS_DATA volume [harness/seed.sh:L830].'
        shift 2
        ;;
      --data-dir=*)
        ACAS_RESET_DATA_DIR="${1#*=}"
        [[ -n "$ACAS_RESET_DATA_DIR" ]] || acas_die "$EX_USAGE" \
          '--data-dir was given an empty path.' \
          'If the default is wanted, omit the flag; harness/seed.sh then uses' \
          'the ACAS_DATA volume [harness/seed.sh:L830].'
        shift
        ;;
      --dry-run)
        ACAS_RESET_DRY_RUN=1
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
        # The optional scenario positional, forwarded verbatim to seed.sh so the
        # canonical invocation at [harness/docker-compose.yml:L263-L274] works
        # as written.
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

  # --schema-only skips the seed, so a data directory would be inert. Rejecting
  # the combination is better than silently ignoring an argument the caller
  # clearly meant to have an effect.
  if (( ACAS_RESET_SCHEMA_ONLY )) && [[ -n "$ACAS_RESET_DATA_DIR" ]]; then
    acas_die "$EX_USAGE" \
      '--schema-only and --data-dir cannot be combined.' \
      '--data-dir is forwarded to harness/seed.sh, which --schema-only does not' \
      'run, so the value would have no effect.'
  fi
}

# =============================================================================
# PRECONDITIONS
#
# This script ASSERTS its environment; it never installs one, never creates a
# database object and never changes a server setting. Asserting here means a
# misconfigured container fails in seconds with a named cause, instead of the
# client failing part-way through the frozen file and leaving a half-applied
# schema that silently poisons every subsequent diff.
# =============================================================================

# Precondition 1 of 7.
acas_assert_environment() {
  acas_stage 'Preconditions 1/7: environment contract'

  local name missing=0
  local -a required=("${ACAS_RESET_REQUIRED_ENV_NONEMPTY[@]}")

  # The seed-only variables are required for a full reset and irrelevant to
  # --schema-only. Asserting them up front means a full reset that cannot seed
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
    # means "no unix socket"; an UNDECLARED one means the caller never supplied
    # the contract at all.
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
      "ACAS_DB_PORT must be numeric; got '$ACAS_DB_PORT'."
  fi

  # The COBOL reads its connection details into fixed-width fields. A longer
  # value is silently TRUNCATED, after which the COBOL side fails to
  # authenticate while the Python side succeeds -- a divergence with nothing to
  # do with posting logic. The password's LENGTH is checked; its VALUE is never
  # printed. [copybooks/wsfnctn.cob:L56-L62]
  #
  # The limit applies to the APPLICATION account and the schema name, which do
  # enter the COBOL `RDB-Data` block. It deliberately does NOT apply to an
  # ACAS_DB_ADMIN_* override, which is a harness-only credential -- the same
  # reasoning [harness/docker-compose.yml:L385-L396] applies to
  # MARIADB_ROOT_PASSWORD.
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

  # The account that performs the drop and re-apply. Defaults to the application
  # account, which Compose grants ALL PRIVILEGES on the target schema.
  ACAS_RESET_DB_USER="${ACAS_DB_ADMIN_USER:-$ACAS_DB_USER}"
  ACAS_RESET_DB_PASSWORD="${ACAS_DB_ADMIN_PASSWORD-$ACAS_DB_PASSWORD}"

  [[ -d "$ACAS_REPO" ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_REPO is not a directory: $ACAS_REPO." \
    'It must be the checkout holding the frozen COBOL, bridges and schema.'

  acas_log "ACAS_REPO   = $ACAS_REPO (read-only checkout; the specification)"
  acas_log "ACAS_OUT    = $ACAS_OUT"
  acas_log "database    = ${ACAS_RESET_DB_USER}@${ACAS_DB_HOST}:${ACAS_DB_PORT}/${ACAS_DB_NAME}"
  if [[ "$ACAS_RESET_DB_USER" != "$ACAS_DB_USER" ]]; then
    acas_log "admin override active: the drop and re-apply run as ${ACAS_RESET_DB_USER}"
  fi
  if (( ACAS_RESET_SCHEMA_ONLY )); then
    acas_note '--schema-only: harness/seed.sh will NOT be run, so its variables are not required'
  fi
  acas_note 'the password is never printed, never logged and never passed in argv'
}

# Open the run log. Its directory is $ACAS_OUT/reset, deliberately NOT
# $ACAS_OUT/<scenario>/: the determinism test compares scenario dumps byte for
# byte, so the one wall-clock reading in this script must live somewhere the
# comparison can never see.
acas_open_log() {
  local dir="$ACAS_OUT/reset"
  mkdir -p "$dir" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "could not create the reset log directory $dir." \
    'ACAS_OUT must be a writable volume.'
  ACAS_RESET_LOG="$dir/reset.log"
  : >"$ACAS_RESET_LOG" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "could not write the reset log $ACAS_RESET_LOG."
  {
    printf 'harness/reset_db.sh run log\n'
    printf 'started (UTC): %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'this file lives under the ACAS_OUT reset directory and is never compared\n'
    printf -- '----------------------------------------------------------------\n'
  } >>"$ACAS_RESET_LOG"
}

# -----------------------------------------------------------------------------
# Precondition 4 of 7 -- THE SEQUENTIAL LOCK (R-3)
#
# "Execution strictly sequential -- no parallel scenario runs against the shared
# database." Two resets racing on one database would interleave 33 drops with 33
# creates and leave a state neither caller asked for, so a second one is refused
# rather than queued.
#
# Taken AFTER preconditions 1..3, which are pure reads, so a misconfigured
# invocation can never block a correct one; and BEFORE preconditions 5..7, which
# open connections to the shared database.
#
# A PLAIN LOCK FILE, created with `set -C` (noclobber) so the test and the create
# are one atomic operation. Deliberately not `flock`: it is not guaranteed
# present, and a lock that silently degrades to no lock is worse than none. The
# owning pid is written so a stale lock can be identified, and a lock whose owner
# is gone is reclaimed -- a container killed mid-reset must not wedge the harness
# for ever.
# -----------------------------------------------------------------------------
acas_take_lock() {
  acas_stage 'Preconditions 4/7: the sequential reset lock'
  ACAS_RESET_LOCK="$ACAS_OUT/.reset_db.lock"

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

  # noclobber makes the create fail if another process won the race between the
  # check above and here.
  if ! (set -C; printf '%s\n' "$$" >"$ACAS_RESET_LOCK") 2>/dev/null; then
    acas_die "$EX_CONCURRENT" \
      "could not take the reset lock $ACAS_RESET_LOCK." \
      'Either another reset took it in the last instant, or the ACAS_OUT' \
      'directory is not writable.'
  fi
  ACAS_RESET_LOCK_HELD=1
}

# -----------------------------------------------------------------------------
# Precondition 2 of 7 -- THE FROZEN ARTIFACT.
#
# Asserted BEFORE anything is applied, because this is the cheapest possible
# place to catch a modified frozen file and the most expensive place to miss one:
# the plan is unambiguous that "any diff touching ... mysql/ACASDB.sql is a
# defect in the migration, regardless of how harmless it appears", and a schema
# that has quietly grown an index or lost a table would make every downstream
# parity result meaningless while still looking like a clean run.
#
# Every check is a READ. Nothing here transforms, copies or repairs the file
# (R-4) -- see the header on the charset caveat.
#
# On the ALTER TABLE pattern: a naive `grep -c 'ALTER TABLE'` reports 66 on this
# dump, yet there is not one real ALTER TABLE in it -- every hit sits inside a
# mysqldump version guard, `/*!40000 ALTER TABLE `X` DISABLE KEYS */`
# [mysql/ACASDB.sql:L45]. `^[^/]*ALTER TABLE` matches only an occurrence with no
# `/` before it on the line, so the 66 guarded hits are excluded while a
# genuinely added statement -- at column 1 or indented -- is caught. The same
# pattern is used by the image build tripwire [harness/Dockerfile.mariadb], so
# both agree by construction.
#
# On the float test: it matches the bare TOKENS `float`, `double` and `real`
# anywhere in the file rather than only in column position. That is the stronger
# assertion -- the frozen schema contains zero occurrences of all three words, in
# DDL and in comments alike -- and it supports R-2 structurally: an accounting
# value can never traverse a binary floating-point column because no such column
# exists. `decimal` is unaffected, containing none of the three as a whole word.
# -----------------------------------------------------------------------------

# acas_assert_grep_count <expected> <grep-flags> <pattern> <description>
# `|| true` is required: grep exits 1 when the count is 0, which under `set -e`
# would abort before the comparison this function exists to make.
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
  acas_stage "Preconditions 2/7: the frozen schema, $ACAS_RESET_SCHEMA_RELPATH"

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
  #    "verbatim" a machine-checked claim rather than a comment.
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

  # 2..9. The structural invariants, each independently verified against the
  #       committed schema. A digest mismatch alone would say only "something
  #       changed"; these name WHICH rule was violated.
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

# Precondition 3 of 7 -- the script this one delegates re-seeding to.
acas_assert_seed_script() {
  acas_stage 'Preconditions 3/7: harness/seed.sh'

  # Resolved beside THIS file, not relative to the working directory: the
  # `gnucobol` service runs with working_dir /build, and the reset must work from
  # anywhere.
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

# The optional scenario positional. Checked for readability here so a typo fails
# before 33 tables are dropped, rather than after; NOT parsed, because R-3
# forbids adding validation the frozen tooling does not perform, and because a
# scenario's inputs reach the loaders through the flat files it places in the data
# directory rather than through this script.
acas_assert_scenario() {
  [[ -n "$ACAS_RESET_SCENARIO" ]] || return 0

  [[ -e "$ACAS_RESET_SCENARIO" ]] || acas_die "$EX_USAGE" \
    "the scenario file '$ACAS_RESET_SCENARIO' does not exist." \
    'The canonical invocation passes a path such as' \
    'harness/scenarios/clean_batch_gl.yaml [harness/docker-compose.yml:L263-L274].'
  [[ -f "$ACAS_RESET_SCENARIO" && -r "$ACAS_RESET_SCENARIO" ]] || acas_die "$EX_USAGE" \
    "the scenario '$ACAS_RESET_SCENARIO' is not a readable file."
}


# =============================================================================
# DATABASE ACCESS
#
# CREDENTIAL HYGIENE. The password reaches the client through MYSQL_PWD and
# nowhere else: never on the command line (where it would be visible in `ps` to
# every process on the host), never in a --defaults-extra-file (which would have
# to be created, chmod-ed and shredded, and would survive a SIGKILL), never in
# the run log, and never in a diagnostic. `set -x` is never enabled.
#
# THE CLIENT IS RESOLVED ONCE, THEN PINNED. Two dimensions vary between
# environments: the binary may be `mariadb` or `mysql`, and a modern client
# talking to a server without TLS needs --skip-ssl. Both are probed ONCE with a
# read-only `select 1` and then pinned for the rest of the run.
#
# That pinning is a correctness requirement, not an optimisation. The schema
# apply streams 33 DROP/CREATE pairs; retrying it under a different client
# variant after a mid-file failure could re-run part of the file against a
# half-applied schema. Probing first means the apply is attempted exactly once,
# with a combination already known to work.
#
# --database IS ALWAYS PASSED. The frozen dump contains zero `USE` statements, so
# without it every statement would fail with "No database selected".
#
# --batch AND NEVER --force. --force makes the client continue past SQL errors,
# which would leave a half-applied schema and report success. Every failure must
# be loud.
# =============================================================================

# Build the client argv for a read-only query. The password is NOT in it.
acas_sql_argv() {
  local client="$1" tls="$2"
  printf '%s\n' "$client" '--protocol=TCP'
  if [[ -n "$tls" ]]; then
    printf '%s\n' "$tls"
  fi
  printf '%s\n' \
    "--host=$ACAS_DB_HOST" \
    "--port=$ACAS_DB_PORT" \
    "--user=$ACAS_RESET_DB_USER" \
    '--batch' \
    '--skip-column-names' \
    "--database=$ACAS_DB_NAME"
}

# Run one read-only statement (or several, separated by `;`) and capture the
# result in ACAS_SQL_OUT, one row per line with tab-separated columns.
#
# Return codes, chosen so the readiness loop can tell a transient failure from a
# permanent one:
#     0  success
#     1  the client ran and failed for some other reason
#     2  the server rejected the credentials
#     3  no client binary is available at all
acas_sql_scalar() {
  local sql="$1"
  ACAS_SQL_OUT=''
  ACAS_SQL_DIAG=''

  local -a argv=()
  local out rc=0

  # Already pinned: one attempt, no retry, no variant search.
  if [[ -n "$ACAS_SQL_CLIENT" ]]; then
    mapfile -t argv < <(acas_sql_argv "$ACAS_SQL_CLIENT" "$ACAS_SQL_TLS_FLAG")
    argv+=("--execute=$sql")
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

  # Not pinned yet: probe both binaries and both TLS variants, pinning the first
  # combination that works.
  local client tls
  local saw_client=0
  for client in mariadb mysql; do
    acas_have "$client" || continue
    saw_client=1
    for tls in '' '--skip-ssl'; do
      mapfile -t argv < <(acas_sql_argv "$client" "$tls")
      argv+=("--execute=$sql")
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
    # A rejected credential is the same answer from either binary, so there is
    # nothing to gain by trying the second one.
    if [[ "$ACAS_SQL_DIAG" == *'Access denied'* ]]; then
      return 2
    fi
    return 1
  done
  (( saw_client )) || return 3
  return 1
}

# One scalar value from a single-column, single-row query. Takes the LAST line
# that is not empty, so a stray client advisory can never be mistaken for the
# answer.
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
      "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"
  fi
}

# TCP reachability, using python3 so no client binary and no credential is
# needed. python3 is guaranteed present by harness/Dockerfile.gnucobol.
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

# Precondition 5 of 7 -- MariaDB readiness.
acas_wait_for_database() {
  acas_stage 'Preconditions 5/7: MariaDB readiness'

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
  #
  # Two failure shapes, deliberately treated differently: a transient failure is
  # retried for the full timeout, because the port routinely opens before the
  # server will talk; "Access denied" is a configuration error, not a readiness
  # state, so it is retried only for a short grace window -- no amount of waiting
  # fixes a wrong password.
  local rc=0 denied_for=0
  elapsed=0
  while true; do
    rc=0
    acas_sql_scalar 'select 1' || rc=$?
    case "$rc" in
      0)
        acas_log "authenticated as ${ACAS_RESET_DB_USER} against ${ACAS_DB_NAME}"
        acas_log "client pinned : ${ACAS_SQL_CLIENT} ${ACAS_SQL_TLS_FLAG:-(TLS negotiated normally)}"
        return 0
        ;;
      3)
        acas_die "$EX_DATABASE" \
          'no mariadb or mysql client binary is available, so the frozen schema cannot be applied.' \
          'The schema must be streamed to a client UNMODIFIED -- that is the whole' \
          'of the drop-and-recreate, because the frozen file carries its own 33' \
          'DROP TABLE IF EXISTS statements -- and the autocommit setting must be' \
          'read before anything is touched [common/glbatchLD.cbl:L9-L13].' \
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
            "Server said: ${ACAS_SQL_DIAG:-<no diagnostic>}"
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
            "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"
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
# Precondition 6 of 7 -- autocommit MUST be OFF.
#
# ASSERTED, NEVER SET. See the header. The setting belongs to the server and has
# exactly one authority, harness/Dockerfile.mariadb, which writes `autocommit=0`
# into /etc/mysql/conf.d/99-acas-oracle.cnf [harness/Dockerfile.mariadb:L231-L258].
# Issuing `SET autocommit` here -- even "just for the DDL" -- would create a
# second authority and change behaviour, which R-3 and R-4 both forbid.
#
# Read TWICE: once here, before anything is applied, and again after the apply,
# because the frozen file changes six session variables [mysql/ACASDB.sql:L13-L22]
# and the claim that it left this one alone must be proved rather than assumed.
#
# The `+ 0` coercion is required, not cosmetic: autocommit is a boolean system
# variable and renders as ON/OFF in a string context, so a bare select can hand
# back "ON" where a caller expects 1.
# -----------------------------------------------------------------------------
ACAS_RESET_AUTOCOMMIT_SQL='select concat_ws(0x2f, @@GLOBAL.autocommit + 0, @@SESSION.autocommit + 0)'

# acas_read_autocommit -> echoes "<global>/<session>" into ACAS_SQL_OUT
acas_read_autocommit() {
  local rc=0
  acas_sql_scalar "$ACAS_RESET_AUTOCOMMIT_SQL" || rc=$?
  if (( rc != 0 )); then
    acas_die "$EX_DATABASE" \
      'could not read the autocommit setting from the server.' \
      "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"
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

# acas_assert_autocommit <when>
acas_assert_autocommit() {
  local when="$1"

  acas_read_autocommit
  local value="$ACAS_SQL_OUT"
  local global="${value%%/*}" session="${value##*/}"
  acas_log "@@GLOBAL.autocommit = $global   @@SESSION.autocommit = $session   ($when)"

  if (( global != 0 || session != 0 )); then
    acas_die "$EX_AUTOCOMMIT" \
      "autocommit is ON (global=$global, session=$session) $when; the reset is REFUSED." \
      'Every one of the 28 ACAS load programs uses commit and rollback and states' \
      'the requirement in its own header, [common/glbatchLD.cbl:L9-L13]:' \
      '"This modules uses commit and rollback so you MUST ensure that autocommit' \
      'is OFF in the rdb settings. It is as default set ON."' \
      'With autocommit on, the re-seed commits at boundaries the loaders never' \
      'chose, their rollbacks silently do nothing [common/analLD.cbl:L442], and' \
      'the state the Python cycle starts from is not the state the COBOL cycle' \
      'started from -- which makes the whole comparison worthless.' \
      'This script deliberately does NOT fix it: the setting has exactly one' \
      'authority, harness/Dockerfile.mariadb, which writes autocommit=0 into' \
      '/etc/mysql/conf.d/99-acas-oracle.cnf. Start the harness MariaDB service' \
      'built from that Dockerfile, or set autocommit=0 in the server' \
      'configuration and restart it.'
  fi
  acas_ok "autocommit is off, globally and for this session ($when)"
}

# -----------------------------------------------------------------------------
# Precondition 7 of 7 -- the privileges the FROZEN FILE'S OWN statements need.
#
# Checked by name, up front, so a missing grant is reported as a missing grant
# instead of surfacing as the client dying part-way through the file and leaving
# a half-applied schema.
#
# Both privilege scopes must be consulted. A schema-scoped grant
# (`GRANT ALL ON `ACASDB`.*`, which is what Compose's application account has)
# appears in information_schema.SCHEMA_PRIVILEGES; a global grant, which a
# superuser has, appears only in information_schema.USER_PRIVILEGES. Reading one
# and not the other would declare a superuser unprivileged.
#
# The grantee string is built from current_user() with char(39) and char(64)
# rather than literal quote and at-sign characters, so the SQL survives being
# carried through the shell without any quoting subtlety.
# -----------------------------------------------------------------------------
acas_assert_privileges() {
  acas_stage 'Preconditions 7/7: privileges for the drop and re-apply'

  local grantee_expr
  grantee_expr="concat(char(39), substring_index(current_user(), char(64), 1), char(39), char(64), char(39), substring_index(current_user(), char(64), -1), char(39))"

  local sql
  sql="select group_concat(distinct p order by p separator ',') from ("
  sql+=" select PRIVILEGE_TYPE as p from information_schema.USER_PRIVILEGES"
  sql+=" where GRANTEE = ${grantee_expr}"
  sql+=" union all"
  sql+=" select PRIVILEGE_TYPE as p from information_schema.SCHEMA_PRIVILEGES"
  sql+=" where TABLE_SCHEMA = '${ACAS_DB_NAME}' and GRANTEE = ${grantee_expr}"
  sql+=" ) as g"

  local rc=0
  acas_sql_value "$sql" || rc=$?
  if (( rc != 0 )); then
    acas_die "$EX_PRIVILEGE" \
      'could not read the privileges of the connected account.' \
      "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"
  fi

  local granted="${ACAS_SQL_OUT}"
  if [[ -z "$granted" || "$granted" == 'NULL' ]]; then
    acas_die "$EX_PRIVILEGE" \
      "the account '${ACAS_RESET_DB_USER}' holds no recorded privileges on ${ACAS_DB_NAME}." \
      'Applying the frozen schema needs DROP, CREATE, LOCK TABLES, ALTER, INSERT' \
      'and SELECT. Compose grants the application account ALL PRIVILEGES on the' \
      'target schema; if this account was created by hand, grant them.'
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

  acas_ok "all $(acas_join_words "${ACAS_RESET_REQUIRED_PRIVILEGES[@]}") held by ${ACAS_RESET_DB_USER}"
}


# =============================================================================
# STAGE 1 -- APPLY THE FROZEN SCHEMA, VERBATIM
#
# This one command is the entire drop-and-recreate. The frozen file's own 33
# `DROP TABLE IF EXISTS` statements drop, its 33 `CREATE TABLE` statements
# recreate, and this script contributes NO DDL (R-3).
#
# The file is streamed on standard input with no transformation whatsoever:
#   * no sed, awk, tr or iconv;
#   * no edited copy under harness/;
#   * no --default-character-set override contradicting the file's own
#     `SET NAMES utf8mb4` [mysql/ACASDB.sql:L16];
#   * no wrapper statements of any kind -- the file manages its own session state
#     [mysql/ACASDB.sql:L13-L22] and restores all of it at the tail.
# so the charset caveat at [mysql/ACASDB.sql:L9-L11] survives untouched (R-4).
#
# --database is passed explicitly because the dump has no `USE`. --force is NOT
# passed: it would continue past a SQL error, leaving a half-applied schema and
# reporting success, which is the one failure mode this stage must never have.
# =============================================================================
# -----------------------------------------------------------------------------
# Classify whatever the client wrote while applying the frozen schema.
#
# A clean apply is USUALLY silent, but not always, and the difference matters. A
# modern MariaDB client emits a TLS advisory of its own on stderr when it relaxes
# --ssl-verify-server-cert against a server with no configured TLS -- verified
# with client 15.2 (from MariaDB 11.8.3) against this 10.11.7 server:
#
#     WARNING: option --ssl-verify-server-cert is disabled, ...
#
# That line says nothing about the schema and appears on every run in such an
# environment. Promoting it to a WARNING would train an operator to ignore
# warnings, which is worse than useless in a harness whose entire value is that
# an anomaly gets noticed. So it is reported as a NOTE, explained, and the WARNING
# channel is reserved for output that might actually mean the frozen schema was
# applied imperfectly.
#
# Nothing is discarded either way: every line the client produced is printed.
# -----------------------------------------------------------------------------
acas_report_client_output() {
  local out="$1"
  [[ -n "$out" ]] || return 0

  local line advisories=0 other=0
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    # The client's own TLS advisory: about the CONNECTION, never about the schema.
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

acas_apply_schema() {
  acas_stage "Stage 1/4: apply $ACAS_RESET_SCHEMA_RELPATH verbatim to ${ACAS_DB_NAME}"

  acas_note 'the frozen file supplies its own DROP TABLE IF EXISTS statements, so this'
  acas_note 'stage emits no DDL of its own and drops nothing by hand (R-3)'

  local -a argv=()
  mapfile -t argv < <(acas_sql_argv "$ACAS_SQL_CLIENT" "$ACAS_SQL_TLS_FLAG")

  # Errexit is suspended for exactly the length of this call so the failure can
  # be reported with the client's own words instead of a bare line number.
  local out rc=0
  out="$(MYSQL_PWD="$ACAS_RESET_DB_PASSWORD" "${argv[@]}" <"$ACAS_RESET_SCHEMA" 2>&1)" || rc=$?

  if (( rc != 0 )); then
    # The apply is attempted exactly ONCE. Retrying it -- with another client, or
    # another TLS variant -- would re-run part of the file against a half-applied
    # schema, which is why the client was pinned during the readiness probe.
    ACAS_RESET_APPLIED=1   # partially, which is worse than not at all: say so
    acas_die "$EX_APPLY" \
      "the client REJECTED part of $ACAS_RESET_SCHEMA_RELPATH (status $rc); the schema is PARTIALLY applied." \
      'No retry is attempted: re-running the file against a half-applied schema' \
      'would compound the damage. Fix the cause and run this script again.' \
      '--force is deliberately not used, so nothing was skipped silently.' \
      "Client said: ${out:-<no output>}"
  fi

  ACAS_RESET_APPLIED=1

  # Anything the client said is surfaced rather than swallowed -- this is the only
  # chance to notice a server-side warning about the frozen schema.
  acas_report_client_output "$out"

  acas_ok "applied verbatim: 33 DROP TABLE IF EXISTS + 33 CREATE TABLE, from the frozen file"
  acas_check 'PASS' "frozen schema applied verbatim ($ACAS_RESET_SCHEMA_RELPATH)"
}

# =============================================================================
# STAGE 2 -- VERIFY THE RESET STATE
#
# Eight checks, all read-only, all cheap, and every one of them protects every
# downstream diff. They are mandatory rather than optional for a specific reason:
# the maintainer records that he has not worked with the General Ledger since the
# GnuCOBOL migration, and the plan's instruction is that "if the compiled GL cycle
# behaves surprisingly, the surprise is the specification". An inexact reset would
# make that surprise indistinguishable from a migration bug.
#
# Every hyphenated identifier is backtick-quoted, because every identifier in this
# schema is hyphenated.
# =============================================================================

# All 33 expected table names: the 22 in scope plus the 11 out of scope.
acas_expected_table_names() {
  acas_inscope_table_names
  local name
  for name in "${ACAS_RESET_OUT_OF_SCOPE[@]}"; do
    printf '%s\n' "$name"
  done
}

# Check 1 of 8 -- the 33 tables exist, and they are exactly the expected 33.
# Counting alone would pass if a table had been renamed, so the NAME SET is
# compared in both directions.
acas_verify_table_set() {
  acas_sql_value_or_die \
    "select count(*) from information_schema.TABLES where TABLE_SCHEMA = '${ACAS_DB_NAME}'" \
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
    "select TABLE_NAME from information_schema.TABLES where TABLE_SCHEMA = '${ACAS_DB_NAME}' order by TABLE_NAME" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not list the tables after the apply.' \
    "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"

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
#
# One client invocation carrying 33 `select '<name>', count(*) from `<name>``
# statements: read-only, deterministic, and it attributes a non-empty table by
# name. COUNT(*) rather than information_schema.TABLE_ROWS, which is only an
# estimate for InnoDB and would make this check meaningless.
acas_verify_all_empty() {
  local -a tables=()
  mapfile -t tables < <(acas_expected_table_names)

  local sql='' name
  for name in "${tables[@]}"; do
    sql+="select '${name}', count(*) from \`${name}\`;"
  done

  local rc=0
  acas_sql_scalar "$sql" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not count the rows of the recreated tables.' \
    "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"

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
    "select distinct TABLE_NAME, INDEX_NAME from information_schema.STATISTICS where TABLE_SCHEMA = '${ACAS_DB_NAME}' and INDEX_NAME <> 'PRIMARY' order by TABLE_NAME, INDEX_NAME" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not list the indexes after the apply.' \
    "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"

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
#
# This is the check that would catch the schema having been transformed on its
# way to the client: a `utf8mb4_*` reading would mean someone "fixed" the charset
# caveat at [mysql/ACASDB.sql:L9-L11], which R-4 forbids.
acas_verify_collation() {
  local rc=0
  acas_sql_scalar \
    "select TABLE_NAME, TABLE_COLLATION from information_schema.TABLES where TABLE_SCHEMA = '${ACAS_DB_NAME}' and TABLE_COLLATION <> '${ACAS_RESET_COLLATION}' order by TABLE_NAME" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not read the table collations after the apply.' \
    "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"

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

# Check 5 of 8 -- the SHAPE of all 22 in-scope tables: column count and primary
# key, plus the LEDGER-NAME width that the dump normaliser depends on.
#
# The right NUMBER of tables with the wrong SHAPE would poison a diff just as
# thoroughly as a missing table, and it would be far harder to notice.
acas_verify_shapes() {
  local rc=0
  acas_sql_scalar \
    "select TABLE_NAME, count(*) from information_schema.COLUMNS where TABLE_SCHEMA = '${ACAS_DB_NAME}' group by TABLE_NAME order by TABLE_NAME" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not read the column counts after the apply.' \
    "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"

  local -A columns_of=()
  local table value
  while IFS=$'\t' read -r table value; do
    [[ -n "$table" ]] || continue
    columns_of["$table"]="$value"
  done <<<"$ACAS_SQL_OUT"

  rc=0
  acas_sql_scalar \
    "select TABLE_NAME, group_concat(COLUMN_NAME order by SEQ_IN_INDEX separator ',') from information_schema.STATISTICS where TABLE_SCHEMA = '${ACAS_DB_NAME}' and INDEX_NAME = 'PRIMARY' group by TABLE_NAME order by TABLE_NAME" || rc=$?
  (( rc == 0 )) || acas_die "$EX_VERIFY" \
    'could not read the primary keys after the apply.' \
    "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"

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

  # The width drift the dump normaliser exists to canonicalise:
  # [copybooks/wsledger.cob] declares Ledger-Name pic x(24), the bridge widens it
  # to PIC X(32) [common/nominalMT.cbl:L299], and the column is char(32)
  # [mysql/ACASDB.sql:L127]. The value is not corrupted but the PADDING differs,
  # and padding is visible in a dump -- so this width is load-bearing evidence
  # and is asserted explicitly rather than left implicit in the column count.
  acas_sql_value_or_die \
    "select COLUMN_TYPE from information_schema.COLUMNS where TABLE_SCHEMA = '${ACAS_DB_NAME}' and TABLE_NAME = 'GLLEDGER-REC' and COLUMN_NAME = 'LEDGER-NAME'" \
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
#
# It holds because each bridge load paragraph initialises its host-variable group
# before a write, so an unset field becomes zero or space rather than SQL NULL.
# That is why the Python data-access layer must DEFAULT rather than omit, and why
# a nullable column appearing here would signal the schema had drifted.
acas_verify_not_null() {
  acas_sql_value_or_die \
    "select count(*) from information_schema.COLUMNS where TABLE_SCHEMA = '${ACAS_DB_NAME}' and IS_NULLABLE = 'YES'" \
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

# Check 7 of 8 -- no binary floating-point column anywhere (R-2).
#
# The structural half of "zero binary floating point in accounting computation":
# an accounting value cannot traverse a float if no float column exists. Asserted
# on the SERVER as well as in the file, because the file check cannot see a column
# someone altered by hand.
acas_verify_no_float() {
  acas_sql_value_or_die \
    "select count(*) from information_schema.COLUMNS where TABLE_SCHEMA = '${ACAS_DB_NAME}' and DATA_TYPE in ('float', 'double', 'real')" \
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
  #    variables and restores them at the tail [mysql/ACASDB.sql:L13-L22]; this
  #    proves it left autocommit alone rather than assuming it.
  acas_assert_autocommit 'after the apply'
  acas_check 'PASS' 'autocommit still 0/0 after the apply'

  ACAS_RESET_VERIFIED=1
}

# =============================================================================
# STAGE 3 -- DURABILITY IN A FRESH SESSION
#
# With autocommit off, every DML statement needs an explicit COMMIT. DDL does
# not: InnoDB commits CREATE TABLE and DROP TABLE implicitly, which
# [harness/Dockerfile.mariadb:L227-L229] records and which is why this script does
# not -- and must not -- turn autocommit on for the apply.
#
# That is a documented property, not an observation, so it is PROVED here rather
# than trusted: a brand-new client process, hence a brand-new server session,
# re-counts the tables. If the apply had somehow landed inside an uncommitted
# transaction, the fresh session would see the OLD tables and this check would
# fail -- which is exactly the empirical verification the plan asks for.
# =============================================================================
acas_verify_durability() {
  acas_stage 'Stage 3/4: durability -- re-count in a FRESH session'

  # acas_sql_scalar spawns a new client process per call, so this is genuinely a
  # new connection and a new session, not a reuse of the one that applied the
  # schema.
  acas_sql_value_or_die \
    "select count(*) from information_schema.TABLES where TABLE_SCHEMA = '${ACAS_DB_NAME}'" \
    'the table count in a fresh session'

  if [[ "$ACAS_SQL_OUT" != "$ACAS_RESET_EXPECT_TABLES" ]]; then
    acas_die "$EX_VERIFY" \
      "a fresh session sees $ACAS_SQL_OUT tables, not $ACAS_RESET_EXPECT_TABLES." \
      'The apply was therefore not durable, so nothing downstream can rely on it.' \
      'Note what is NOT the fix: turning autocommit on for the DDL would change' \
      'behaviour and is forbidden (R-3, R-4). InnoDB commits CREATE TABLE and' \
      'DROP TABLE implicitly, so a failure here points at the server' \
      'configuration, not at this script.'
  fi

  acas_ok "a fresh session sees all $ACAS_RESET_EXPECT_TABLES tables -- the DDL committed implicitly, as expected under autocommit=0"
  acas_check 'PASS' 'schema durable in a fresh session'
}


# =============================================================================
# STAGE 4 -- RE-SEED
#
# Delegated to harness/seed.sh, which reproduces the flat-file-to-loader contract
# of [common/masterLD.sh:L44-L115] and its exit-code semantics by driving the
# maintainer's own compiled `common/*LD.cbl` programs.
#
# WHY DELEGATE RATHER THAN SEED HERE. Seeding is a solved problem in this harness
# and duplicating it would create a second definition of the seeded state -- the
# one thing both sides of the parity diff must agree on absolutely. The decision
# that seed.sh reproduces the frozen script's CONTRACT rather than executing the
# frozen script is made and justified there (its author marks it untested, and it
# is not valid shell), and is deliberately not re-litigated here.
#
# The compiled loaders run as EXTERNAL PROCESSES, out of process and confined to
# harness/ -- the sanctioned use of compiled COBOL under R-1. Nothing here imports
# from acas_posting.
#
# ITS STATUS IS PROPAGATED VERBATIM. seed.sh distinguishes its own failures
# (70..73) from a load program's return code (128 params not set up, 64 RDB not
# set up, 16 rdb write error [common/masterLD.sh:L37-L39]), and that distinction
# is worth more to a caller than a flattened "reset failed". This script's own
# codes occupy 80..88 precisely so the two can never be confused.
# =============================================================================
acas_reseed() {
  if (( ACAS_RESET_SCHEMA_ONLY )); then
    acas_stage 'Stage 4/4: re-seed -- SKIPPED by --schema-only'
    acas_note 'the database now holds 33 EMPTY tables'
    acas_warn '--schema-only leaves an UNSEEDED database: the full stage-5 contract is schema PLUS seed, so a dump taken now is not comparable with one taken after the COBOL cycle'
    return 0
  fi

  acas_stage "Stage 4/4: re-seed via $ACAS_RESET_SEED_SCRIPT"

  local -a argv=("$ACAS_RESET_SEED")
  if [[ -n "$ACAS_RESET_DATA_DIR" ]]; then
    argv+=("--data-dir" "$ACAS_RESET_DATA_DIR")
  fi
  if [[ -n "$ACAS_RESET_SCENARIO" ]]; then
    argv+=("$ACAS_RESET_SCENARIO")
  fi

  acas_log "running: $(acas_join_words "${argv[@]}")"
  acas_note 'it drives the compiled load programs as external processes only (R-1)'

  # Errexit suspended for exactly the length of the call: the status is DATA and
  # must be classified, not merely propagated by `set -e`.
  local rc=0
  "${argv[@]}" || rc=$?
  ACAS_RESET_SEED_RC="$rc"

  if (( rc != 0 )); then
    acas_check 'FAIL' "re-seed failed, $ACAS_RESET_SEED_SCRIPT exited $rc"
    acas_seed_report
    acas_die "$rc" \
      "$ACAS_RESET_SEED_SCRIPT exited $rc; the reset is NOT complete." \
      'The frozen schema was applied and verified, so the database holds the 33' \
      'empty tables and NO seed data. That is a valid schema and an invalid' \
      'premise for a state diff.' \
      'DO NOT take a diff from this state. seed.sh reports 70 usage, 71' \
      'precondition, 72 database, 73 autocommit for its own failures, and' \
      'otherwise propagates a load program return code: 128 params not set up,' \
      '64 RDB not set up, 16 rdb write error [common/masterLD.sh:L37-L39].' \
      'Its own diagnostics are above, and its log is in the seed subdirectory' \
      'of the ACAS_OUT area.'
  fi

  acas_ok "$ACAS_RESET_SEED_SCRIPT completed cleanly"
  acas_check 'PASS' 're-seeded via harness/seed.sh (exit 0)'
}

# =============================================================================
# REPORTING THE OUTCOME
# =============================================================================
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
    acas_log "scenario              : $ACAS_RESET_SCENARIO (forwarded verbatim; not parsed here)"
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

# =============================================================================
# DRY RUN
#
# Prints exactly what a real run would do and touches nothing: no statement is
# issued, no lock is taken, no table is dropped. The frozen-artifact invariants
# ARE checked, because they are pure reads of the checkout and they are the whole
# point of looking before leaping.
# =============================================================================
acas_print_plan() {
  acas_stage 'Dry run: the plan'
  acas_note 'nothing is executed, no database statement is issued and no table is dropped'

  acas_log ''
  acas_log "1. apply, verbatim : $ACAS_RESET_SCHEMA"
  acas_log "   to database     : ${ACAS_DB_NAME} (named explicitly -- the file has no USE statement)"
  acas_log "   as              : ${ACAS_RESET_DB_USER}@${ACAS_DB_HOST}:${ACAS_DB_PORT}"
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
    local -a argv=("$ACAS_RESET_SEED")
    if [[ -n "$ACAS_RESET_DATA_DIR" ]]; then
      argv+=("--data-dir" "$ACAS_RESET_DATA_DIR")
    fi
    if [[ -n "$ACAS_RESET_SCENARIO" ]]; then
      argv+=("$ACAS_RESET_SCENARIO")
    fi
    acas_log "4. re-seed        : $(acas_join_words "${argv[@]}")"
    acas_log '   its status is propagated verbatim (70..73 its own, else a loader rc)'
  fi

  acas_log ''
  acas_note 'the MariaDB readiness, autocommit and privilege assertions are NOT performed'
  acas_note 'in a dry run; a real run refuses to reset unless autocommit is off, globally'
  acas_note 'and for the session [common/glbatchLD.cbl:L9-L13]'
}

# =============================================================================
# MAIN
#
# Strictly sequential (R-3). No stage is backgrounded and none is parallelised.
# Nothing here writes to $ACAS_REPO.
#
# The order is deliberate and is the whole discipline of the script: assert
# everything that can be asserted BEFORE 33 tables are dropped, so a run that
# cannot finish has not started.
# =============================================================================
acas_main() {
  acas_parse_args "$@"

  printf 'harness/reset_db.sh -- stage 5 of the eight-stage parity protocol\n'
  printf '  seed -> run(COBOL) -> dump -> normalize -> RESET -> run(Python) -> dump -> diff\n'
  printf 'Drops and re-applies the FROZEN mysql/ACASDB.sql verbatim, then re-seeds, so the\n'
  printf 'Python cycle starts from byte-for-byte the state the COBOL cycle started from.\n'
  printf 'The drop lives in the frozen file itself, so this script emits no DDL (R-3).\n'

  acas_assert_environment
  acas_open_log
  acas_assert_scenario
  if [[ -n "$ACAS_RESET_SCENARIO" ]]; then
    acas_log "scenario = $ACAS_RESET_SCENARIO (forwarded verbatim to $ACAS_RESET_SEED_SCRIPT)"
  fi
  acas_assert_frozen_schema
  acas_assert_seed_script

  if (( ACAS_RESET_DRY_RUN )); then
    acas_print_plan
    printf '\nharness/reset_db.sh dry run complete: nothing was executed.\n'
    exit "$EX_OK"
  fi

  # The lock is taken only for a real run, and only after every cheap assertion
  # has passed, so a misconfigured invocation never blocks a correct one.
  acas_take_lock

  acas_wait_for_database

  # The banner is raised HERE rather than inside acas_assert_autocommit, because
  # that function is deliberately dual-use: it runs once as this precondition and
  # once as check 8 of 8 after the apply, where a "Preconditions 6/7" banner
  # would be actively misleading. Raising it at the call site keeps the
  # precondition numbering complete AND makes the ERR/EXIT traps name the
  # autocommit gate -- not MariaDB readiness -- as the failing stage.
  acas_stage 'Preconditions 6/7: autocommit is off [common/glbatchLD.cbl:L9-L13]'
  acas_assert_autocommit 'before the apply'

  acas_assert_privileges

  acas_apply_schema
  acas_verify_reset_state
  acas_verify_durability
  acas_reseed

  acas_seed_report

  # Exit 0 ONLY on a genuinely clean reset AND a clean re-seed. Never
  # unconditionally: the frozen build scripts end with a bare `exit 0`
  # [comp-all.sh:L45], [common/comp-common.sh:L59] that reports success however
  # the work went, and that defect is worked around here rather than copied.
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
    exit "$EX_OK"
  fi

  printf '\nharness/reset_db.sh completed: frozen schema re-applied verbatim, %s tables\n' \
    "$ACAS_RESET_EXPECT_TABLES"
  printf 'verified, and re-seeded. Both cycles now start from identical state.\n'
  printf 'Next: harness/run_python_scenario.sh, then harness/dump_tables.py.\n'
  exit "$EX_OK"
}

acas_main "$@"

