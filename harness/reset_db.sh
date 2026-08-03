#!/usr/bin/env bash
# harness/reset_db.sh
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
# [harness/docker-compose.yml:L346-L357]:
#
#     C="docker compose -f harness/docker-compose.yml run --rm -T gnucobol"
#     S=harness/scenarios/clean_batch_gl.yaml
#     ...
#     $C harness/reset_db.sh            "$S"
#
# -----------------------------------------------------------------------------
# THE ONE DESIGN FACT THAT SHAPES THIS ENTIRE SCRIPT: THE DROP IS IN THE FROZEN
# FILE
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
#      MARIADB_DATABASE=ACASDB [harness/Dockerfile.mariadb:L427]; this script
#      resets the database's CONTENTS, never its existence. Forgetting
#      --database is the single most likely way to get a confusing failure.
#
#   2. IT MANAGES ITS OWN SESSION STATE. [mysql/ACASDB.sql:L13-L22] sets
#      character set, NAMES, TIME_ZONE, UNIQUE_CHECKS, FOREIGN_KEY_CHECKS,
#      SQL_MODE and SQL_NOTES, and the tail restores every one; this script
#      therefore adds none of its own.

#   3. ITS 66 `ALTER TABLE` HITS ARE COMMENTS, NOT STATEMENTS. Every one sits
#      inside a `/*!40000 ... DISABLE|ENABLE KEYS */` version guard, first at
#      [mysql/ACASDB.sql:L45]; a bare ALTER TABLE occurs zero times. So a naive
#      `grep -c 'ALTER TABLE'` is NOT an integrity anchor -- precondition 2
#      anchors on the sha256 of the whole file instead.

# THE CHARSET CAVEAT IS FROZEN STATE AND IS NOT FIXED (R-4)
# [mysql/ACASDB.sql:L9-L11], verbatim:
#     --  THERE IS NOT ANY DATA RECORDS PRESENT HERE --
#     --   YOU MAY NEED TO CHANGE the defined Character set in all tables
#     --   TO MATCH ANY OF YOUR REQUIREMENTS IF THEY DIFFER
# The dump sets `SET NAMES utf8mb4` at [mysql/ACASDB.sql:L16] while all 33
# tables declare `DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci`. The
# maintainer flagged the inconsistency himself and it is part of the
# specification: "A defect reproduced is correct; a defect fixed is a failure."
# So the file reaches the client BYTE-FOR-BYTE -- no sed, awk, tr or iconv on
# the way in, no edited copy under harness/, no --default-character-set
# override -- and stage 2 asserts all 33 tables came back utf8mb3_general_ci.

# AUTOCOMMIT IS ASSERTED, NEVER SET (R-3, R-4)
# [common/glbatchLD.cbl:L9-L12], verbatim:
#     *>  This modules uses commit and rollback so *
#     *>  you MUST ensure that autocommit is OFF   *
#     *>   in the rdb settings. It is as default   *
#     *>   set ON.                                 *
#
# That banner is not unique to the batch loader -- it appears across the
# `common/*LD.cbl` family. But the shipped loaders never carry the intention
# out: every `perform aa020-Rollback` is commented out with `*>` (e.g.
# [common/glbatchLD.cbl:L386], [common/nominalLD.cbl:L428],
# [common/slpostingLD.cbl:L405]) and `aa030-Commit` has ZERO perform sites in
# any of the 28 loaders, so this census returns nothing:
#     grep -n '^ *perform.*\(aa020\|aa030\|Commit\|Rollback\)' common/*LD.cbl
# The maintainer records the consequence inline at [common/analLD.cbl:L442]:
# "These do not work during testing with mariadb - Non transactional model or
# autocommit set ON."
#
# The same holds on the posting side: the twenty in-scope bridges, the in-scope
# handlers and every bridge close path contain zero COMMIT / ROLLBACK / START
# TRANSACTION, and the vendored `cobmysqlapi38.c` exposes `MySQL_commit` without
# ever calling it -- and does not expose `MySQL_autocommit` at all, so no COBOL
# program in the checkout can set the mode itself.
#
# The Agent Action Plan nonetheless mandates autocommit OFF -- section 0.2.1.1
# (the seeding contract), section 0.4.1.7 (on harness/Dockerfile.mariadb:
# "autocommit off to match the loaders") and section 0.5.2 -- and the AAP is the
# frozen source of truth this migration aligns to. So the database this script
# hands to the comparison is served with autocommit OFF, and the durability
# consequence is REPORTED rather than engineered away: MariaDB discards each
# COBOL session at disconnect, so the re-seed and any COBOL posting run leave no
# durable rows. That is the frozen code's defect, and R-4 makes it the
# specification -- "a defect reproduced is correct; a defect fixed is a failure".
#
# The setting has exactly ONE authority: harness/Dockerfile.mariadb, which
# writes `autocommit=0` into /etc/mysql/conf.d/99-acas-oracle.cnf. This script
# reads it and REFUSES to reset when it is on. It never issues
# `SET autocommit`, not even for the duration of the DDL: doing so would create
# a second authority and make the reset depend on which script ran last. It is
# asserted BEFORE the apply and again AFTER it, because the frozen file changes
# session variables and the claim that it left this one alone has to be proved
# rather than assumed.
#
# The loaders' unreachable commit/rollback is preserved as a reproduced legacy
# defect (R-4), not repaired: this script neither enables transactional seeding
# the frozen code cannot drive, nor issues the COMMIT the loaders omit.
#
# DDL is durable regardless -- InnoDB commits CREATE TABLE and DROP TABLE
# implicitly -- and stage 3 proves it empirically by reconnecting in a FRESH
# session and re-counting the tables, rather than taking the manual's word
# for it.
#
# -----------------------------------------------------------------------------
# WHERE THIS FILE SITS, AND WHAT IT NEVER TOUCHES
# harness/ is the compiled oracle and is a SIBLING of acas_posting/, never a
# sub-package. This script imports nothing from acas_posting, creates no
# harness/__init__.py, and reaches compiled COBOL only indirectly and
# out-of-process, through harness/seed.sh -- the sanctioned use under R-1.
# $ACAS_REPO is mounted READ-ONLY (`../:/repo:ro`) and only ever READ, because
# any diff touching the frozen tree "is a defect in the migration, regardless
# of how harmless it appears": the run log goes to $ACAS_OUT/reset/ and the
# sequential lock to $ACAS_OUT. Nothing under $ACAS_OUT/<scenario>/ is written
# here, so the determinism suite -- which requires two Python runs under one
# pinned clock to dump byte-identically -- cannot see this script's own
# wall-clock reading in that log.

# STRICTLY SEQUENTIAL (R-3): no `&`, no `xargs -P`, no job control, and a plain
# lock file that refuses a second concurrent reset of the shared database.
# DETERMINISTIC AND IDEMPOTENT (R-6): running it twice leaves the database in
# exactly the same state both times -- the frozen file's `DROP TABLE IF EXISTS`
# makes that natural, and stage 2 asserts it.
# RULES PROVENANCE. There is no user rules document for this project; the
# binding rules -- R-1 no COBOL at runtime, R-2 zero binary floating point,
# R-3 no schema change and sequential, R-4 anomalies reproduced never fixed,
# R-5 full traceability, R-6 compiled behaviour decides -- come from the plan.

# Strict mode. -E propagates the ERR trap into functions and subshells so an
# unexpected failure is attributed to a line number instead of vanishing.
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

# Exit codes.
# CHOSEN NOT TO COLLIDE WITH ANY CODE THIS SCRIPT MIGHT PROPAGATE. The delegated
# seed uses 70..73 for its own failures [harness/seed.sh] and propagates a
# loader's 128, 64 or 16 [common/masterLD.sh:L37-L39]; harness/build_oracle.sh
# uses 64..67 and 71..77. This script therefore keeps to the 80..88 band, so the
# rule for an automated caller is unambiguous:
#     0              clean reset, and a clean re-seed
#     80..88         THIS SCRIPT failed one of its own stages
#     anything else  harness/seed.sh's own status, propagated verbatim
readonly EX_OK=0
readonly EX_USAGE=80          # bad command line
readonly EX_PRECONDITION=81   # environment, output directory or seed.sh assertion
readonly EX_DATABASE=82       # MariaDB unreachable, or credentials rejected
readonly EX_AUTOCOMMIT=83     # autocommit is not OFF -- see acas_assert_autocommit
readonly EX_PRIVILEGE=84      # the account cannot perform the drop and re-apply
readonly EX_FROZEN=85         # mysql/ACASDB.sql has been MODIFIED -- see §invariants
readonly EX_APPLY=86          # the client rejected part of the frozen schema
readonly EX_VERIFY=87         # the post-apply state is not what the schema defines
readonly EX_CONCURRENT=88     # another reset holds the sequential lock
readonly EX_TIMEOUT=89        # a client or the delegated seed exceeded its deadline
readonly EX_TARGET=90         # the target is not a proven harness-owned disposable database
readonly EX_FIXTURE=91        # the re-seed did not reuse the scenario's staged fixture

# -----------------------------------------------------------------------------
# WHAT MAKES A DATABASE SAFE TO DESTROY.
#
# This script streams 33 `DROP TABLE IF EXISTS` + 33 `CREATE TABLE` pairs at
# whatever server the environment names. That is irreversible, it is the entire
# purpose of the script, and it must therefore be aimed at a database that has
# been PROVEN disposable rather than one that merely answered a connection.
#
# "The credentials worked" is not proof of anything except that the credentials
# worked. A correct-looking ACAS_DB_HOST/ACAS_DB_NAME pair pointing at a
# developer's or a colleague's MariaDB is indistinguishable, at the protocol
# level, from the harness's own throwaway container.
#
# So four independent facts must line up, and every one of them is checked before
# a single DDL statement is sent:
#
#   1. The schema name is EXACTLY the one the frozen dump defines. The frozen
#      mysql/ACASDB.sql is the only schema this script can apply, so any other
#      name is by definition not this harness's database.
#   2. The host is one the harness itself provisions.
#   3. The server carries the harness's own disposability sentinel -- a marker
#      schema created by harness/Dockerfile.mariadb, which exists nowhere except
#      in an image this harness built. A production or shared server cannot have
#      it by accident.
#   4. The target schema contains nothing but the 33 tables the frozen dump
#      defines. An extra table means somebody else's data is in there.
#
# Any deviation requires an explicit acknowledgement that NAMES THE EXACT TARGET,
# so a stale blanket "yes" left in an environment cannot authorise the
# destruction of a different database later.
#
# None of this is a business validation and none of it touches the migrated code:
# the harness is oracle apparatus (AAP 0.7 C-1/C-2), and R-3's prohibition is on
# schema evolution, which this adds none of.
# -----------------------------------------------------------------------------
readonly ACAS_RESET_REQUIRED_SCHEMA='ACASDB'
readonly ACAS_RESET_SENTINEL_SCHEMA='acas_harness_disposable'
readonly ACAS_RESET_SENTINEL_TABLE='disposability_marker'
readonly -a ACAS_RESET_CANONICAL_HOSTS=(mariadb 127.0.0.1 localhost ::1)

# The scenario-fixture marker harness/seed.sh writes when it stages a scenario's
# declared seed files. THIS STRING MUST MATCH ACAS_FIXTURE_MARKER in
# [harness/seed.sh] exactly -- the two scripts communicate through this filename
# and nothing else, so a divergence would make every reset silently report an
# unbound re-seed.
readonly ACAS_RESET_FIXTURE_MARKER='.acas-scenario-fixture'

# -----------------------------------------------------------------------------
# Finite deadlines. Every external process runs under one: each MariaDB client
# invocation, the schema apply, and the delegated harness/seed.sh.
# -----------------------------------------------------------------------------
readonly ACAS_TIMEOUT_MAX=86400
ACAS_TIMEOUT_GRACE="${ACAS_TIMEOUT_GRACE-}"         # TERM-to-KILL grace period
ACAS_TIMEOUT_CLIENT="${ACAS_TIMEOUT_CLIENT-}"        # one MariaDB client invocation
ACAS_TIMEOUT_APPLY="${ACAS_TIMEOUT_APPLY-}"         # streaming the frozen schema
ACAS_TIMEOUT_SEED="${ACAS_TIMEOUT_SEED-}"          # the delegated harness/seed.sh
ACAS_TIMEOUT_RESOLVED=''      # out-parameter of acas_timeout_seconds
declare -a ACAS_DEADLINE_ARGV=()   # populated by acas_deadline_prefix

# THE FROZEN ARTIFACT

# The one file this script applies, relative to the read-only checkout.
readonly ACAS_RESET_SCHEMA_RELPATH='mysql/ACASDB.sql'

# Byte-for-byte digest of `mysql/ACASDB.sql` as committed: 1459 lines,
# 51008 bytes. The SAME value harness/Dockerfile.mariadb pins as
# ARG ACASDB_SCHEMA_SHA256, deliberately, so the image build and this script
# check one baseline rather than two.
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
# Entry shape: <table>:<columns>:<primary key>
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
# so a reader can re-add the 22 + 11 = 33 rather than trust it, and so the
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
# Every one of the 22 IN-SCOPE tables carries PRIMARY and nothing else. That is
# exactly why harness/dump_tables.py can order by the primary key with no
# tie-breaking logic and still get a deterministic dump, and why no seeding or
# reset ordering is dictated by referential integrity -- so the frozen order is
# kept everywhere. Re-asserting it after every reset keeps it honest.
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

# GATE 3a -- schema names this script will destroy. `ACASDB` is the name the
# frozen dump was produced from [mysql/ACASDB.sql:L1] and the name
# harness/docker-compose.yml creates. Extend with a comma- or space-separated
# ACAS_DB_ALLOWED_SCHEMAS when a deployment names its throwaway schema
# something else.
readonly -a ACAS_RESET_DEFAULT_ALLOWED_SCHEMAS=(
  'ACASDB'
)

# GATE 3b -- hosts a disposable database is expected to live on: the loopback
# forms, and the two service names the Compose recipe and the setup contract
# use. Extend with ACAS_DB_DISPOSABLE_HOSTS.
#
# A HOSTNAME IS NOT A SECURITY BOUNDARY and this list does not pretend
# otherwise -- `localhost` inside a container with a tunnel out is not
# disposable. It is a TRIPWIRE against the overwhelmingly common accident: an
# environment left pointing at a shared or production server. Gates 1 and 2
# are what actually authorise the operation.
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
# into SQL at all. Deliberately narrower than MySQL permits: every schema this
# harness will ever address is an ASCII identifier, so anything carrying a
# quote, a backslash, a semicolon, whitespace or a comment introducer is
# refused rather than escaped. Escaping is applied too (see
# acas_sql_quote_literal), but a shape check that cannot be talked out of is
# the stronger of the two controls.
readonly ACAS_RESET_SCHEMA_NAME_PATTERN='^[A-Za-z_][A-Za-z0-9_$]*$'

# -----------------------------------------------------------------------------
# Mutable state. Declared up front because `set -u` makes an unset reference
# fatal.
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
ACAS_RESET_CONSENT_ARG=''        # --consent=, overrides ACAS_RESET_CONSENT
ACAS_RESET_CONSENT_EXPECTED=''   # the token the target requires, once resolved
ACAS_RESET_TARGET_AUTHORISED=0   # 1 once all three destructive gates passed
ACAS_RESET_SCHEMA_LITERAL=''     # the schema as a safe SQL literal, incl. quotes
ACAS_RESET_ACKNOWLEDGE=''        # --acknowledge-destructive: the named target
ACAS_RESET_ACK_USED=0            # 1 once an acknowledgement has been honoured
declare -a ACAS_RESET_GATE_PROBLEMS=()  # destructive-gate failures, reported together
declare -a ACAS_RESET_TLS_VARIANTS=()   # permitted client transports, most secure first
ACAS_SQL_OUT=''                  # last successful query result
ACAS_SQL_DIAG=''                 # last client diagnostic, for error messages
ACAS_SQL_CLIENT=''               # resolved client binary: mariadb or mysql
declare -a ACAS_SQL_ARGV=()      # bounded client argv, published by acas_build_sql_argv
ACAS_SQL_TLS_FLAG=''             # resolved TLS flag: '' or --skip-ssl
declare -a ACAS_RESET_SUMMARY=()      # the closing checklist
declare -a ACAS_RESET_WARN_SUMMARY=() # non-fatal findings, replayed at the end

# REPORTING
# Stage banners are numbered so the log reads as the deterministic staged
# orchestration the plan prescribes (R-6): explicit, ordered, individually
# reported, individually asserted.
# Everything printed here goes to standard output AND, once the log directory
# exists, to $ACAS_OUT/reset/reset.log. Nothing is written under
# $ACAS_OUT/<scenario>/, because the determinism test requires byte-identical
# scenario dumps and a clock reading in a compared file would break it.

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
# frozen behaviour, cites its locator so the reader can check the claim (R-5).
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

# =============================================================================
# FINITE DEADLINES
# =============================================================================

# acas_timeout_seconds <env-var-name> <default>
# Publishes the validated budget in ACAS_TIMEOUT_RESOLVED rather than on stdout:
# a caller writing `x="$(acas_timeout_seconds ...)"' would run this in a command
# substitution, where acas_die's `exit' terminates only that subshell, the
# message and status are both swallowed, and the run continues with an empty
# budget -- which is to say with no deadline at all.
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

# acas_deadline_prefix <budget>
# The single place that knows the flag spelling. `timeout' becomes the parent of
# exactly the process it is given, so only that one child is ever signalled.
acas_deadline_prefix() {
  ACAS_DEADLINE_ARGV=(
    timeout
    "--kill-after=$ACAS_TIMEOUT_GRACE"
    --signal=TERM
    "$1"
  )
}

# acas_is_timeout_status <rc> <elapsed> <budget>
# 124 is GNU coreutils on expiry, 137 the KILL escalation. uutils coreutils
# returns 125 where GNU returns 124, while GNU's 125 means timeout itself failed
# -- so 125 is decided by elapsed wall clock rather than by status alone.
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

# acas_assert_not_timed_out <rc> <elapsed> <budget> <budget-var> <label>
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

# =============================================================================
# THE FROZEN-ARTIFACT CONTAINMENT GUARD
#
# acas_assert_outside_repo <label> <path>
#
# Canonical, not textual, and in BOTH directions. A string prefix test misses a
# symlink whose target is inside the checkout, a path that does not exist yet
# (judged instead by its nearest existing ancestor, which is what mkdir would
# create under), and a write root that CONTAINS the checkout -- equally
# unacceptable, since writing through it reaches the frozen files too.
# =============================================================================
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

# =============================================================================
# SQL IDENTIFIER AND LITERAL SAFETY
#
# Every statement in this script is built by string composition -- the MariaDB
# CLI has no bind parameters -- so the two values that reach SQL from the
# environment are gated here rather than trusted at each of the eleven sites
# that use them.
#
# acas_assert_sql_identifier <label> <value>
#   The character class is deliberately narrower than MariaDB permits: letters,
#   digits and underscore only, and at most 12 characters, which is already the
#   ceiling the COBOL `RDB-Data' pic x(12) field imposes
#   [copybooks/wsfnctn.cob:L56-L62]. Nothing legitimate in this harness needs
#   more, and a value that cannot contain a quote, a backslash, a semicolon, a
#   comment introducer or whitespace cannot alter the shape of a statement.
#
# acas_sql_quote <value>
#   Emits the value as a SQL string literal WITH its enclosing quotes, doubling
#   any embedded single quote. Used so no call site concatenates a bare value
#   between hand-written quotes -- the pattern that made the schema name able to
#   terminate a literal and append its own SQL.
# =============================================================================
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
# block that explains it, is the implementation. It escapes the BACKSLASH as
# well as the apostrophe, which matters because MariaDB treats a backslash as an
# escape character in a string literal unless NO_BACKSLASH_ESCAPES is set. Two
# separate escapers would be two places for that to be got wrong.
acas_sql_quote() {
  acas_sql_quote_literal "${1-}"
}

# acas_assert_table_name <label> <value>
# The table-name counterpart of acas_assert_sql_identifier. A SEPARATE validator
# rather than a loosened one, because the two accept different alphabets for
# different reasons and merging them would weaken the stricter of the pair:
#   - a schema/user name comes from the environment and is bounded by the COBOL
#     pic x(12) field, so it is restricted to [A-Za-z0-9_];
#   - a table name comes from the frozen schema, which uses HYPHENS throughout
#     (GLLEDGER-REC, SAINV-LINES-REC) and reaches 19 characters
#     (PUAUTOGEN-LINES-REC), so [A-Za-z0-9_-] up to 64 is the accurate rule.
# Notably absent from both: the backtick, which is the character that would
# escape a quoted identifier.
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

# acas_sql_quote_ident <value>
# Emits a backquoted SQL identifier, doubling any embedded backtick, and -- like
# acas_sql_quote -- emits the delimiters itself so that no call site is left
# writing its own pair around an unescaped value. The frozen table names REQUIRE
# quoting: every one contains a hyphen, which is an operator in unquoted SQL.
acas_sql_quote_ident() {
  local value="$1"
  # The delimiter is held in a variable rather than written into the format
  # string: a backtick inside a single-quoted printf format is literal and would
  # be correct, but it reads as an attempted command substitution to both static
  # analysis and to humans. This spelling is unambiguous to both.
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

# Split a comma- or space-separated list into words, one per line. Used for the
# two environment-extendable allow-lists, so both separators work and empty
# entries are dropped.
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

# -----------------------------------------------------------------------------
# SAFE SQL COMPOSITION  (CWE-89)
#
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

# Return $1 as a single-quoted SQL literal, safely escaped. Backslash first,
# then the quote, so an escaped backslash is not re-escaped.
acas_sql_quote_literal() {
  local value="${1-}"
  value="${value//\\/\\\\}"
  value="${value//\'/\'\'}"
  printf "'%s'" "$value"
}

# Identifier quoting goes through acas_sql_quote_ident, declared above with
# acas_assert_table_name. Every SQL identifier this script names is a frozen
# constant -- from ACAS_RESET_SECONDARY_INDEX_ALLOWED or the in-scope table list
# -- so none comes from the caller and there is nothing for the helper to
# sanitise; it exists because every identifier in this schema is HYPHENATED and
# therefore has to be backquoted, and one helper that emits its own delimiters
# is safer than a backquote pair hand-written at each site.

# -----------------------------------------------------------------------------
# SAFE FILE CREATION  (CWE-59 symlink following, CWE-367 TOCTOU, CWE-732
# over-permissive files)
#
# `: >"$path"` and `printf ... >"$path"` both FOLLOW a symlink and TRUNCATE its
# target, and both create at whatever the umask allows -- 0644 in practice. Every
# file this script creates lives under $ACAS_OUT, which the Compose recipe makes
# a bind mount shared between the `gnucobol` and `mariadb` services
# [harness/docker-compose.yml:L689]. So an attacker able to create the name
# first chooses which file gets truncated, and then reads what is written in its
# place.
#
# THE PATTERN, in four steps, and each one is load-bearing:
#
#   1. REFUSE a symlink outright. Bash has no O_NOFOLLOW, so this is an explicit
#      `-L` test. On its own it would be a TOCTOU window, which is why step 3
#      exists.
#   2. REMOVE an existing regular file, so step 3's exclusive create is not
#      defeated by our own previous run.
#   3. CREATE under `set -C` (noclobber), which is O_EXCL: if anything -- a
#      symlink, a regular file, a directory -- appears at the name between step 1
#      and here, the create FAILS instead of following or truncating. This is
#      what closes the race that step 1 alone leaves open.
#   4. chmod 600, so the content is private regardless of the inherited umask.
#      `umask 077` is also set in acas_main, which makes step 4 belt and braces
#      rather than the only control.
#
# Not `mktemp`: these are named files the operator is told to read, so the name
# is part of the contract. Not `flock`: it is not guaranteed present, and a lock
# that silently degrades to no lock is worse than none -- the same reasoning
# acas_take_lock records.
# -----------------------------------------------------------------------------
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
# TRAPS
# There is no credential FILE to shred: the password reaches the client
# through MYSQL_PWD only (see acas_sql_argv), so it never appears in argv,
# never in `ps`, and never on disk. That is a stronger guarantee than a
# --defaults-extra-file plus a cleanup trap, and it is why this script
# creates no temporary credential file. `set -x` is never enabled either.
# The EXIT trap releases the sequential lock and -- the important part --
# tells the operator whether the database was left mid-reset. A reset that
# failed AFTER the apply and BEFORE the seed leaves 33 empty tables, which
# is a perfectly valid schema and a completely invalid premise for a diff.
# Saying so is the difference between a diff that is known-meaningless and
# one that is silently wrong.

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

# USAGE
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
                      canonical invocation documented at
                      [harness/docker-compose.yml:L357-L399] --
                      `harness/reset_db.sh "$S"` -- works as written.
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
    3. The server carries acas_harness_disposable.disposability_marker, which is
       created by harness/Dockerfile.mariadb and therefore exists ONLY in an
       image this harness built. Proof by PRESENCE of a marker, not by absence of
       production data: an empty staging database and an empty production
       database are indistinguishable, so a heuristic would fail OPEN. This fails
       CLOSED.
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
  82       database        83  autocommit is not on
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


# ARGUMENTS
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
        # Deliberately REQUIRES a value rather than acting as a bare switch: the
        # acknowledgement has to name the exact target it authorises, or it would
        # be a blanket "destroy whatever is configured" that outlives the
        # invocation it was reasoned about. See acas_assert_disposable_static.
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
        # The optional scenario positional, forwarded verbatim to seed.sh so the
        # canonical invocation at [harness/docker-compose.yml:L346-L357] works
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

# PRECONDITIONS
# This script ASSERTS its environment; it never installs one, never creates a
# database object and never changes a server setting. Asserting here means a
# misconfigured container fails in seconds with a named cause, instead of the
# client failing part-way through the frozen file and leaving a half-applied
# schema that silently poisons every subsequent diff.

# Precondition 1 of 9.
acas_assert_environment() {
  acas_stage 'Preconditions 1/9: environment contract'

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

  # A numeric test alone let 99999 through to the TCP probe's bare
  # `int(sys.argv[2])` and to --port=, where the client's own truncation or the
  # kernel's rejection produced a connection failure with no useful cause. The
  # RANGE is asserted here, once, before anything connects.
  #
  # NOTE ON WIDTH: this checks the harness environment variable, NOT the COBOL
  # field. `DB-Port` is `pic x(5)` CHARACTER data
  # [copybooks/wsfnctn.cob:L56-L62] and its value semantics are untouched --
  # port 65535 is five characters and fits, which is exactly why the frozen
  # field is five wide.
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
  # CANONICALISED, and this matters beyond tidiness: the consent token embeds
  # the port verbatim, so `03306` and `3306` would demand two different tokens
  # for one target. `10#` forces base-10 so a leading zero is stripped rather
  # than read as octal.
  ACAS_DB_PORT="$(( 10#$ACAS_DB_PORT ))"

  # The COBOL reads its connection details into fixed-width fields. A longer
  # value is silently TRUNCATED, after which the COBOL side fails to
  # authenticate while the Python side succeeds -- a divergence with nothing to
  # do with posting logic. The password's LENGTH is checked; its VALUE is never
  # printed. [copybooks/wsfnctn.cob:L56-L62]
  # The limit applies to the APPLICATION account and the schema name, which do
  # enter the COBOL `RDB-Data` block. It deliberately does NOT apply to an
  # ACAS_DB_ADMIN_* override, which is a harness-only credential -- the same
  # reasoning [harness/docker-compose.yml:L512-L527] applies to
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

  # GATE 1, GATE 2 and GATE 3. Asserted here so that a misdirected invocation
  # fails before the TCP probe, let alone the apply.
  acas_authorise_destructive_target

  # The transport policy, for the same reason and at the same point: a refusal
  # must be reported before the readiness probe spends its timeout on a host
  # this script was never going to talk to.
  acas_assert_transport_policy

  [[ -d "$ACAS_REPO" ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_REPO is not a directory: $ACAS_REPO." \
    'It must be the checkout holding the frozen COBOL, bridges and schema.'

  acas_log "ACAS_REPO   = $ACAS_REPO (read-only checkout; the specification)"
  acas_log "ACAS_OUT    = $ACAS_OUT"
  acas_log "database    = ${ACAS_RESET_DB_USER}@${ACAS_DB_HOST}:${ACAS_DB_PORT}/${ACAS_DB_NAME}"
  acas_log "the drop and re-apply run as the ADMIN account ${ACAS_RESET_DB_USER}, not as ${ACAS_DB_USER}"
  if (( ACAS_RESET_SCHEMA_ONLY )); then
    acas_note '--schema-only: harness/seed.sh will NOT be run, so its variables are not required'
  fi
  acas_note 'the password is never printed, never logged and never passed in argv'
}

# -----------------------------------------------------------------------------
# THE THREE DESTRUCTIVE GATES. See THE DESTRUCTIVE-TARGET POLICY above for why
# each one exists. Nothing in this function connects, reads or writes.
#
# EVERY problem is collected and reported TOGETHER rather than one per run, so
# an operator configuring the harness for the first time learns all three
# requirements at once instead of discovering them in three failed attempts.
#
# UNDER --dry-run the problems are WARNINGS and the run continues to print the
# plan. That is deliberate and it is not a hole: a dry run opens no connection
# and executes nothing, and it is the documented way to be TOLD the exact
# consent token this target needs. A real run is strict -- ACAS_RESET_DRY_RUN is
# set only by the flag, is never read from the environment, and the flag exits
# before acas_take_lock.
# -----------------------------------------------------------------------------
acas_gate_problem() {
  ACAS_RESET_GATE_PROBLEMS+=("$@")
  ACAS_RESET_GATE_PROBLEMS+=('')
}

acas_authorise_destructive_target() {
  ACAS_RESET_GATE_PROBLEMS=()

  # ---- SEC-02: the schema name must be a plain identifier before it is ever
  # interpolated into SQL, and the safely-quoted literal is computed once here
  # so all twelve query sites share one derivation. FATAL even under --dry-run,
  # because the plan printout itself names the schema.
  if [[ ! "$ACAS_DB_NAME" =~ $ACAS_RESET_SCHEMA_NAME_PATTERN ]]; then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_NAME is not a plain SQL identifier: '${ACAS_DB_NAME}'." \
      'This script interpolates the schema name into twelve information_schema' \
      'queries. A name carrying a quote, backslash, semicolon, whitespace or a' \
      'comment introducer is REFUSED rather than escaped, because no schema' \
      'this harness addresses needs one.'
  fi
  ACAS_RESET_SCHEMA_LITERAL="$(acas_sql_quote_literal "$ACAS_DB_NAME")"

  # ---- GATE 1: a distinct admin account, with no fallback.
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

  # Resolved even when gate 1 failed, so the plan printout and the log line have
  # something truthful to name. A failed gate aborts before any connection, so
  # this value is never used to authenticate in that case.
  ACAS_RESET_DB_USER="${ACAS_DB_ADMIN_USER:-<unset:ACAS_DB_ADMIN_USER>}"
  ACAS_RESET_DB_PASSWORD="${ACAS_DB_ADMIN_PASSWORD-}"

  # ---- GATE 3: a disposable target. Reported before the consent token so an
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

  # ---- GATE 2: explicit, target-scoped consent.
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
      # A dry run connects to nothing and executes nothing, so it reports the
      # requirements instead of refusing. This is the documented way to be told
      # the exact consent token a target needs.
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
  acas_ok "destructive target authorised: ${ACAS_DB_NAME}@${ACAS_DB_HOST}:${ACAS_DB_PORT} as ${ACAS_RESET_DB_USER}"
  acas_check 'PASS' 'destructive-target gates: distinct admin account, target-scoped consent, disposable schema and host'
}

# Open the run log. Its directory is $ACAS_OUT/reset, deliberately NOT
# $ACAS_OUT/<scenario>/: the determinism test compares scenario dumps byte for
# byte, so the one wall-clock reading in this script must live somewhere the
# comparison can never see.
#
# CREATED SAFELY (CWE-59 symlink following, CWE-367 TOCTOU, CWE-732
# over-permissive). The truncation used to be a bare
#
#     : >"$ACAS_RESET_LOG"
#
# which FOLLOWS a symlink and truncates whatever it points at, at whatever mode
# the umask happens to allow. $ACAS_OUT is a bind mount shared between two
# Compose services [harness/docker-compose.yml:L689], so anything able to place
# `reset/reset.log` there first could choose the victim -- and then read a log
# that names the schema, the host, the admin account and every client
# diagnostic. See acas_create_private_file for the replacement pattern; the
# LOG'S CONTENT is unchanged.
acas_open_log() {
  local dir="$ACAS_OUT/reset"

  # Canonicalise BEFORE creating anything. A prefix test on the raw strings would
  # be satisfied by `$ACAS_REPO/../repo-name', by a symlink into the checkout, or
  # by a relative path -- and the first thing this function does is mkdir -p,
  # which would have already materialised directories inside the frozen tree by
  # the time a later check noticed. Both directions are rejected: the target must
  # not sit inside the checkout, and the checkout must not sit inside the target.
  acas_assert_outside_repo 'ACAS_OUT' "$ACAS_OUT"
  acas_assert_outside_repo 'the reset log directory' "$dir"

  mkdir -p "$dir" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "could not create the reset log directory $dir." \
    'ACAS_OUT must be a writable volume.'
  chmod 700 -- "$dir" 2>/dev/null || true

  # Re-checked after creation: mkdir -p resolves symlinks along the way, so the
  # path that now exists is the one to judge, not the one that was requested.
  acas_assert_outside_repo 'the reset log directory' "$dir"

  # THE GLOBAL IS ASSIGNED LAST, and that ordering is the whole point. acas_tee
  # appends to $ACAS_RESET_LOG whenever it is non-empty, and acas_die reports
  # through acas_tee -- so setting the global BEFORE the path was proven safe
  # meant the refusal message itself was written through the very symlink it was
  # refusing. Proven by probe, not reasoned about: the victim file grew by five
  # lines of diagnostic. Until the create succeeds, ACAS_RESET_LOG stays empty
  # and every diagnostic goes to the terminal only.
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

# -----------------------------------------------------------------------------
# Precondition 5 of 9 -- THE SEQUENTIAL LOCK (R-3)
#
# "Execution strictly sequential -- no parallel scenario runs against the shared
# database." Two resets racing on one database would interleave 33 drops with 33
# creates and leave a state neither caller asked for, so a second one is refused
# rather than queued.
#
# Taken AFTER preconditions 1..3, which are pure reads, so a misconfigured
# invocation can never block a correct one; and BEFORE preconditions 5..7,
# which open connections to the shared database.
# A PLAIN LOCK FILE, created with `set -C` (noclobber) so the test and the
# create are one atomic operation. Deliberately not `flock`, which is not
# guaranteed present and would silently degrade to no lock. The owning pid
# is written, and a stale lock is reclaimed: a killed run must not wedge.
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
# Precondition 3 of 9 -- THE FROZEN ARTIFACT.
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

  # 2..9. The structural invariants, each asserted independently against the
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

# Precondition 4 of 9 -- the script this one delegates re-seeding to.
acas_assert_seed_script() {
  acas_stage 'Preconditions 4/9: harness/seed.sh'

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
    'harness/scenarios/clean_batch_gl.yaml [harness/docker-compose.yml:L346-L357].'
  [[ -f "$ACAS_RESET_SCENARIO" && -r "$ACAS_RESET_SCENARIO" ]] || acas_die "$EX_USAGE" \
    "the scenario '$ACAS_RESET_SCENARIO' is not a readable file."
}


# DATABASE ACCESS
# CREDENTIAL HYGIENE. The password reaches the client through MYSQL_PWD and
# nowhere else: never on the command line (where `ps` would expose it to
# every process on the host), never in a --defaults-extra-file (which would
# have to be created, chmod-ed and shredded, and would survive a SIGKILL),
# never in the run log, and never in a diagnostic. `set -x` stays off.
# THE CLIENT IS RESOLVED ONCE, THEN PINNED. Two dimensions vary between
# environments: the binary may be `mariadb` or `mysql`, and a modern client
# talking to a server without TLS needs --skip-ssl. Both are probed ONCE with a
# read-only `select 1` and then pinned for the rest of the run.
#
# TRANSPORT SECURITY (CWE-295 improper certificate validation, CWE-319
# cleartext transmission). The variant search used to be, unconditionally:
#
#     for tls in '' '--skip-ssl'; do          <-- the defect, as it was
#
# so a server that merely declined TLS -- or a middlebox that stripped the
# STARTTLS-equivalent -- caused a SILENT downgrade to plaintext on the second
# iteration, carrying the admin password (well, its handshake) and every
# information_schema answer in clear. Worse, the first iteration passed no
# --ssl-verify-server-cert either, so even the TLS attempt validated nothing:
# any certificate, from anyone, was accepted.
#
# THE POLICY, enforced by acas_permitted_tls_variants and FAIL-CLOSED:
#
#   * A LOCAL target -- a unix socket, or a loopback host -- may use plaintext.
#     Nothing leaves the machine, and it is the configuration the setup contract
#     actually uses: the host client is 11.8 and this server has no TLS, so
#     --skip-ssl is REQUIRED there. Removing that path would break every local
#     probe while protecting nothing.
#   * A NON-LOCAL target must present a certificate chaining to
#     $ACAS_DB_TLS_CA and matching its hostname. That is what
#     --ssl-verify-server-cert adds; without a CA it verifies nothing, so the CA
#     is required rather than optional.
#   * Plaintext to a non-local target is permitted ONLY when
#     ACAS_DB_ALLOW_PLAINTEXT explicitly declares the network isolated. The
#     accepted values are a CLOSED set, so a typo fails closed.
#   * Anything else is REFUSED before the first connection.
#
# NOTHING ELSE CHANGES: the same two binaries are probed in the same order, the
# pinning is still one-shot for the same correctness reason, and the composed
# argv is otherwise identical.
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

# True when the target is reachable without leaving the machine: a unix socket,
# an empty host, a loopback name, or a numeric loopback address. RESOLVES
# NOTHING about whether the server is trustworthy (R-6) -- it answers only
# "could this traffic be observed on a network".
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

# True when ACAS_DB_ALLOW_PLAINTEXT explicitly declares the network isolated.
# A CLOSED set of accepted spellings, so `ture` or `TRUE ` fails closed.
acas_plaintext_declared() {
  case "${ACAS_DB_ALLOW_PLAINTEXT-}" in
    1|true|yes|on) return 0 ;;
  esac
  return 1
}

# Decide, ONCE and BEFORE ANYTHING CONNECTS, which client transports this target
# has earned. Populates ACAS_RESET_TLS_VARIANTS, most secure first, or aborts.
#
# Called from acas_assert_environment alongside the destructive gates, and NOT
# lazily from the query path: a policy that is only evaluated when a connection
# is first attempted arrives AFTER the TCP readiness probe, which can spend its
# whole timeout on an unreachable host before the refusal is ever reported. The
# operator would then be told "the server did not answer" when the truth is
# "this script refuses to talk to it that way".
acas_assert_transport_policy() {
  local ca="${ACAS_DB_TLS_CA-}"
  ACAS_RESET_TLS_VARIANTS=()

  if [[ -n "$ca" ]]; then
    [[ -r "$ca" ]] || acas_die "$EX_PRECONDITION" \
      "ACAS_DB_TLS_CA names a file that cannot be read: $ca" \
      'It must be the PEM bundle the server certificate chains to.'
    # --ssl-verify-server-cert is what makes the CA meaningful: without it the
    # client encrypts but accepts any certificate, which is CWE-295 with extra
    # steps.
    ACAS_RESET_TLS_VARIANTS+=("--ssl-ca=$ca --ssl-verify-server-cert")
  fi

  if acas_target_is_local; then
    # Loopback or socket: plaintext is permitted, and on the setup contract's
    # host client it is REQUIRED -- client 11.8 enforces TLS and this server has
    # none, so --skip-ssl is the only combination that works locally.
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
# acas_sql_argv <client> <tls-flag> [budget-seconds]
#
# The single funnel every client invocation in this script goes through, which is
# why the deadline is prepended HERE: one edit bounds all of them, and a future
# call site cannot forget to add one.
#
# The budget is a parameter rather than a constant because a scalar
# information_schema query and streaming 33 DROP/CREATE pairs are not the same
# kind of wait. It defaults to ACAS_TIMEOUT_CLIENT; acas_apply_schema overrides
# it with ACAS_TIMEOUT_APPLY.
acas_sql_argv() {
  local client="$1" tls="$2" budget="${3:-$ACAS_TIMEOUT_CLIENT}"

  # An empty budget would silently mean "no deadline at all", which is the exact
  # defect this bounding exists to remove, so it is a hard error rather than a
  # fallback. (This is the command-substitution hazard documented on
  # acas_timeout_seconds, reached from the other direction.)
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

# acas_build_sql_argv <client> <tls-flag> [budget-seconds]
# Publishes the client argv through ACAS_SQL_ARGV.
#
# This wrapper exists for one reason, and it is a real trap rather than a
# stylistic one: acas_sql_argv is consumed through `mapfile < <(...)', a process
# SUBSHELL, so an acas_die inside it prints its message and exits only that
# subshell. The caller carries on with a SHORT OR EMPTY array -- which, since the
# deadline lives at the front of that array, means carrying on with no deadline
# at all: precisely the defect this bounding removes.
#
# So the verdict is reached HERE, in the caller's own shell, by checking that the
# generator produced a plausible argv. A correct one is always at least the four
# deadline words plus the client, the protocol and the five connection flags.
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

  # Not pinned yet: probe both binaries and every PERMITTED TLS variant, pinning
  # the first combination that works. The variant list is computed by policy
  # (see TRANSPORT SECURITY above) rather than being the unconditional
  # `'' '--skip-ssl'` pair it used to be, so a plaintext downgrade can only
  # happen where it has been permitted.
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
      # Through acas_build_sql_argv, never `mapfile < <(acas_sql_argv ...)':
      # the generator's acas_die would exit only the subshell and leave this
      # loop running an UNBOUNDED client. See that function's own comment.
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
      "$(acas_diag_summary "$ACAS_SQL_DIAG")"
  fi
}

# TCP reachability, using python3 so no client binary and no credential is
# needed. python3 is guaranteed present by harness/Dockerfile.gnucobol.
# Bounded even though create_connection carries its own timeout: that timeout
# covers the CONNECT, not the getaddrinfo() that precedes it. A name lookup
# against an unreachable resolver blocks in libc, where no Python-level timeout
# reaches, so the deadline has to sit outside the interpreter.
acas_db_tcp_probe() {
  # The port range is asserted in acas_assert_environment, before anything
  # connects, so `int(sys.argv[2])` here can no longer receive 99999 and fail
  # with an OverflowError that names neither the variable nor the value. The
  # range is re-checked in the probe itself because this function is also
  # reached from the readiness loop, and a defence that only exists at one
  # entry point is one refactor away from not existing.
  #
  # An EXTERNAL deadline as well as the socket timeout below: create_connection's
  # timeout covers the connect but NOT the getaddrinfo() that precedes it, so a
  # host name served by an unresponsive resolver would block with the socket
  # timeout never reached.
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
# Precondition 8 of 9 -- autocommit MUST be OFF, as the Agent Action Plan
# mandates (sections 0.2.1.1, 0.4.1.7 and 0.5.2, all from the loader banner at
# [common/glbatchLD.cbl:L9-L13]).
#
# ASSERTED, NEVER SET. See the header for the frozen-source proof: the loaders'
# commit/rollback paragraphs are unreachable and the bridges never commit at all,
# so under this mandated mode every COBOL write is discarded at session close.
# That consequence is reported, not repaired (R-4). The setting belongs to the
# server and has exactly one authority, harness/Dockerfile.mariadb, which writes
# `autocommit=0` into /etc/mysql/conf.d/99-acas-oracle.cnf. Issuing
# `SET autocommit` here -- even "just for the DDL" -- would create a second
# authority and change behaviour, which R-3 and R-4 both forbid.
#
# Read TWICE: once here, before anything is applied, and again after the apply,
# because the frozen file changes six session variables [mysql/ACASDB.sql:L13-L22]
# and the claim that it left this one alone is re-asserted, not assumed.
# The `+ 0` coercion is required, not cosmetic: autocommit is a boolean system
# variable and renders as ON/OFF in a string context, so a bare select can hand
# back "ON" where a caller expects 1.
ACAS_RESET_AUTOCOMMIT_SQL='select concat_ws(0x2f, @@GLOBAL.autocommit + 0, @@SESSION.autocommit + 0)'

# acas_read_autocommit -> echoes "<global>/<session>" into ACAS_SQL_OUT
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
      'The Agent Action Plan mandates autocommit OFF in three places -- section' \
      '0.2.1.1 (the seeding contract), section 0.4.1.7 (on' \
      'harness/Dockerfile.mariadb: "autocommit off to match the loaders") and' \
      'section 0.5.2 -- all deriving it from the banner carried by all 28' \
      'common/*LD.cbl loaders at [common/glbatchLD.cbl:L9-L13]: "you MUST ensure' \
      'that autocommit is OFF in the rdb settings".' \
      'Resetting under ON would hand the comparison a database served in a mode' \
      'the AAP does not sanction, so the oracle would no longer be the thing the' \
      'AAP specifies.' \
      'This script deliberately does NOT set the mode: it has exactly one' \
      'authority, harness/Dockerfile.mariadb, which writes autocommit=0 into' \
      '/etc/mysql/conf.d/99-acas-oracle.cnf. Start the harness MariaDB service' \
      'built from that Dockerfile, or set autocommit=0 in the server' \
      'configuration and restart it.'
  fi
  acas_ok "autocommit is OFF, globally and for this session ($when) -- AAP-mandated"
}

# -----------------------------------------------------------------------------
# Precondition 9 of 9 -- the privileges the FROZEN FILE'S OWN statements need.
#
# Checked by name, up front, so a missing grant is reported as a missing grant
# instead of surfacing as the client dying part-way through the file and leaving
# a half-applied schema.
# Both privilege scopes must be consulted, because an administrative account can
# legitimately be provisioned either way. A schema-scoped grant -- what GATE 1's
# own message tells an operator to create, "DROP, CREATE, ALTER, LOCK TABLES,
# INSERT and SELECT on this schema and nothing else" -- appears in
# information_schema.SCHEMA_PRIVILEGES; a global grant, which the `root` account
# Compose names has, appears only in information_schema.USER_PRIVILEGES. Reading
# one and not the other would declare one of those two accounts unprivileged.
# This reads the privileges of the CONNECTED account, which GATE 1 has already
# forced to be the admin account and never the application one. The application
# account holds only SELECT, INSERT, UPDATE and DELETE -- narrowed at container
# start by harness/Dockerfile.mariadb -- so it could not pass this check, which
# is the intended outcome rather than a limitation.
# The grantee string is built from current_user() with char(39) and char(64)
# rather than literal quote and at-sign characters, so the SQL survives being
# carried through the shell without any quoting subtlety.
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

  acas_ok "all $(acas_join_words "${ACAS_RESET_REQUIRED_PRIVILEGES[@]}") held by ${ACAS_RESET_DB_USER}"
}


# STAGE 1 -- APPLY THE FROZEN SCHEMA, VERBATIM
# This one command is the entire drop-and-recreate. The frozen file's own 33
# `DROP TABLE IF EXISTS` statements drop, its 33 `CREATE TABLE` statements
# recreate, and this script contributes NO DDL (R-3).
# The file is streamed on standard input with NO transformation whatsoever:
# no sed, awk, tr or iconv; no edited copy under harness/; no
# --default-character-set override contradicting the file's own
# `SET NAMES utf8mb4` [mysql/ACASDB.sql:L16]; and no wrapper statements,
# because the file manages its own session state [mysql/ACASDB.sql:L13-L22]
# and restores all of it at the tail, so the charset caveat at
# [mysql/ACASDB.sql:L9-L11] survives untouched (R-4). --database is passed
# because the dump has no `USE`; --force is NOT.

# Classify whatever the client wrote while applying the frozen schema.
# A clean apply is USUALLY silent, but not always, and the difference
# matters. A modern MariaDB client can emit an advisory of its own on
# stderr -- for instance the `--ssl-verify-server-cert` warning its string
# table carries for a passwordless login. Such a line says nothing about
# the schema, so promoting it to a WARNING would train an operator to
# ignore warnings, which is worse than useless in a harness whose entire
# value is that an anomaly gets noticed. It is reported as a NOTE and
# explained, and the WARNING channel is reserved for output that might
# actually mean the frozen schema was applied imperfectly. Nothing is
# discarded either way: every line the client produced is printed.
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

# =============================================================================
# THE DISPOSABILITY GATE -- the guard that stands between this script and
# somebody else's database. See the ACAS_RESET_REQUIRED_SCHEMA declaration for
# why "the credentials worked" is not evidence of anything.
#
# Split in two because the two halves can be checked at different times and the
# earlier one is free:
#
#   acas_assert_disposable_static  -- pure string checks, run BEFORE any network
#                                     contact, so a misaimed invocation is
#                                     refused without touching a server at all.
#   acas_assert_disposable_server  -- server-side proof, run after readiness and
#                                     BEFORE the privilege check and the apply.
#
# Deviations are permitted, but only with an acknowledgement that NAMES THE EXACT
# TARGET. That is the difference between a considered override and a blanket
# "yes" left in an environment: the latter would silently authorise the
# destruction of whatever database the environment happened to name next week.
# =============================================================================

# The acknowledgement must equal `user@host:port/schema' for THIS invocation.
#
# Every expansion is defaulted because this is also called from acas_parse_args
# to build a usage message, which runs BEFORE acas_assert_environment binds
# ACAS_RESET_DB_USER and before the required variables have been proven present.
# Under `set -u' an undefaulted expansion there would abort with a bare
# "unbound variable" instead of the usage error the caller needs to read.
acas_reset_target_label() {
  local user="${ACAS_RESET_DB_USER:-${ACAS_DB_ADMIN_USER:-${ACAS_DB_USER:-<unset>}}}"
  printf '%s@%s:%s/%s' \
    "$user" \
    "${ACAS_DB_HOST:-<unset>}" \
    "${ACAS_DB_PORT:-<unset>}" \
    "${ACAS_DB_NAME:-<unset>}"
}

# acas_target_acknowledged
# True when the caller has explicitly acknowledged destroying THIS target.
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

# acas_refuse_target <headline> <detail>...
# One refusal path, so every deviation reports the same way and names the same
# escape hatch with the same exact string the caller must supply.
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

  # Gate the two values that reach SQL text before either is composed into a
  # statement -- including by the proofs immediately below.
  acas_assert_sql_identifier 'ACAS_DB_NAME' "$ACAS_DB_NAME"

  local acknowledged=0
  if acas_target_acknowledged; then
    acknowledged=1
  fi

  # 1. THE SCHEMA NAME. The frozen mysql/ACASDB.sql is the only schema this
  #    script can apply and it defines exactly one database. A different name is
  #    therefore, by definition, not this harness's database.
  if [[ "$ACAS_DB_NAME" != "$ACAS_RESET_REQUIRED_SCHEMA" ]]; then
    if (( ! acknowledged )); then
      acas_refuse_target \
        "ACAS_DB_NAME is '$ACAS_DB_NAME', not '$ACAS_RESET_REQUIRED_SCHEMA'." \
        "The frozen $ACAS_RESET_SCHEMA_RELPATH defines exactly one database, and" \
        "this script can only apply that file. A schema named anything else is" \
        'not the database this harness owns.'
    fi
    acas_warn "acknowledged: resetting '$ACAS_DB_NAME' rather than $ACAS_RESET_REQUIRED_SCHEMA."
  fi

  # 2. THE HOST. One the harness itself provisions: the Compose service name, or
  #    a loopback address reaching a locally published container.
  if ! acas_in_list "$ACAS_DB_HOST" "${ACAS_RESET_CANONICAL_HOSTS[@]}"; then
    if (( ! acknowledged )); then
      acas_refuse_target \
        "ACAS_DB_HOST is '$ACAS_DB_HOST', which is not a host this harness provisions." \
        "Canonical hosts: $(acas_join_words "${ACAS_RESET_CANONICAL_HOSTS[@]}")." \
        'The first is the harness/docker-compose.yml service name; the others' \
        'reach a container published on this machine. A remote host is exactly' \
        'the case that must not be destroyed by accident.'
    fi
    acas_warn "acknowledged: resetting on the non-canonical host '$ACAS_DB_HOST'."
  fi

  if (( acknowledged )); then
    ACAS_RESET_ACK_USED=1
    acas_note "the destructive acknowledgement names this exact target: $(acas_reset_target_label)"
  fi

  acas_log "target schema  = $ACAS_DB_NAME (required: $ACAS_RESET_REQUIRED_SCHEMA)"
  acas_log "target host    = $ACAS_DB_HOST"
  acas_check 'PASS' 'target identity accepted before any database contact'
}

acas_assert_disposable_server() {
  acas_stage 'Preconditions 7/9: server-side proof of disposability'

  local acknowledged=0
  if acas_target_acknowledged; then
    acknowledged=1
  fi

  # 3. THE SENTINEL. A marker schema created by harness/Dockerfile.mariadb, which
  #    exists nowhere except in an image this harness built. A shared or
  #    production server cannot carry it by accident -- that is the whole point
  #    of proving disposability by presence of something rather than by absence
  #    of something.
  # NOTE: acas_sql_value publishes through ACAS_SQL_OUT (it reduces the scalar
  # in place); there is no separate ACAS_SQL_VALUE.
  local sentinel_rows='' rc=0
  acas_sql_value "select count(*) from information_schema.TABLES where TABLE_SCHEMA = $(acas_sql_quote "$ACAS_RESET_SENTINEL_SCHEMA") and TABLE_NAME = $(acas_sql_quote "$ACAS_RESET_SENTINEL_TABLE")" \
    || rc=$?
  if (( rc == 0 )); then
    sentinel_rows="$ACAS_SQL_OUT"
  fi

  if (( rc != 0 )) || [[ "$sentinel_rows" != '1' ]]; then
    if (( ! acknowledged )); then
      acas_refuse_target \
        "this server does not carry the harness disposability sentinel." \
        "  expected: ${ACAS_RESET_SENTINEL_SCHEMA}.${ACAS_RESET_SENTINEL_TABLE}" \
        "  found:    ${sentinel_rows:-<query failed>}" \
        'That sentinel is created by harness/Dockerfile.mariadb and exists only' \
        'in an image this harness built, so its ABSENCE means this is not the' \
        'harness'"'"'s throwaway server. Start the harness service instead:' \
        '    docker compose -f harness/docker-compose.yml up -d mariadb'
    fi
    acas_warn 'acknowledged: the harness disposability sentinel is absent from this server.'
  else
    acas_ok "disposability sentinel present: ${ACAS_RESET_SENTINEL_SCHEMA}.${ACAS_RESET_SENTINEL_TABLE}"
  fi

  # The server family, recorded rather than enforced: the schema dump names
  # 10.11.7 as its producer [mysql/ACASDB.sql:L1,L5], and a different family is
  # a parity risk worth reporting but not by itself evidence of the wrong server.
  local version=''
  if acas_sql_value 'select @@version'; then
    version="$ACAS_SQL_OUT"
    acas_log "server version = $version  (schema produced by 10.11.7-MariaDB [mysql/ACASDB.sql:L1])"
    case "$version" in
      10.11.*) : ;;
      *) acas_warn "the server reports $version; the frozen schema was produced by 10.11.7-MariaDB [mysql/ACASDB.sql:L1]. Parity evidence from a different family is not comparable." ;;
    esac
  fi

  # 4. NOTHING BUT THE FROZEN TABLES. An extra table means somebody else's data
  #    shares this schema, and the frozen file's own DROP statements would not
  #    remove it -- but a caller who believes this schema is theirs would be
  #    wrong. Checked BEFORE the drop, so the answer still describes the state
  #    the caller thinks they are resetting.
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
        "$ACAS_DB_NAME holds ${#unexpected[@]} table(s) the frozen schema does not define." \
        "  unexpected: $(acas_join_words "${unexpected[@]}")" \
        'The frozen dump defines 33 tables and drops exactly those. A table' \
        'outside that set means this schema is shared with something else, and' \
        'that something else is about to lose the schema around it.'
    fi
    acas_warn "acknowledged: $ACAS_DB_NAME holds ${#unexpected[@]} table(s) outside the frozen 33."
  else
    acas_ok "no table outside the frozen ${ACAS_RESET_EXPECT_TABLES} is present"
  fi

  acas_check 'PASS' 'server-side disposability proof accepted'
}

acas_apply_schema() {
  # LAST LINE OF DEFENCE. Both halves of the disposability gate have already run
  # as preconditions; this re-assertion costs nothing and makes it structurally
  # impossible for a future edit to reorder a stage and reach the 33 DROP/CREATE
  # pairs without them.
  [[ "$ACAS_DB_NAME" == "$ACAS_RESET_REQUIRED_SCHEMA" ]] || acas_target_acknowledged \
    || acas_refuse_target \
      "reached the apply with ACAS_DB_NAME='$ACAS_DB_NAME' and no acknowledgement." \
      'This is unreachable unless a stage was reordered; refusing regardless.'

  acas_stage "Stage 1/4: apply $ACAS_RESET_SCHEMA_RELPATH verbatim to ${ACAS_DB_NAME}"

  # THE LAST GATE, re-asserted at the point of no return. The three destructive
  # gates already passed in acas_assert_environment, before any connection; this
  # re-check costs nothing and means that no future edit can introduce a path
  # into the destructive stage that bypasses them. It also proves, to a reader
  # arriving at this function alone, that the drop cannot happen unauthorised.
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

  # ACAS_TIMEOUT_APPLY, not ACAS_TIMEOUT_CLIENT: this invocation streams 33 DROP
  # plus 33 CREATE statements, which is a different order of wait from a scalar
  # information_schema query.
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
  # failure below, and it is separated here rather than left to the caller because
  # the two demand opposite responses: an under-provisioned ACAS_TIMEOUT_APPLY is
  # fixed by raising the budget, whereas a rejected statement means the frozen
  # file or the server is wrong. Reporting a timeout as "the client REJECTED part
  # of the schema" would send the operator looking for a defect that is not there.
  #
  # The schema is partially applied either way, so the flag is set first and the
  # timeout message carries the same warning the apply failure does.
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

# STAGE 2 -- VERIFY THE RESET STATE
# Eight checks, all read-only, all cheap, and every one of them protects every
# downstream diff. They are mandatory rather than optional for a specific reason:
# the maintainer records that he has not worked with the General Ledger since the
# GnuCOBOL migration, and the plan's instruction is that "if the compiled GL cycle
# behaves surprisingly, the surprise is the specification". An inexact reset would
# make that surprise indistinguishable from a migration bug.
# Every hyphenated identifier is backtick-quoted, because every identifier in this
# schema is hyphenated.

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
# One client invocation carrying 33 `select '<name>', count(*) from `<name>``
# statements: read-only, deterministic, and it attributes a non-empty table by
# name. COUNT(*) rather than information_schema.TABLE_ROWS, which is only an
# estimate for InnoDB and would make this check meaningless.
acas_verify_all_empty() {
  local -a tables=()
  mapfile -t tables < <(acas_expected_table_names)

  # Each name reaches SQL in TWO syntactic positions -- a string literal and a
  # quoted identifier -- so each is composed through the primitive for its own
  # position rather than by hand. These names come from the script's own readonly
  # arrays, not from input, so this is defence in depth: it makes the composition
  # correct by construction, so a future edit that sources the list from
  # elsewhere cannot silently open an injection point.
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
# This is the check that would catch the schema having been transformed on its
# way to the client: a `utf8mb4_*` reading would mean someone "fixed" the charset
# caveat at [mysql/ACASDB.sql:L9-L11], which R-4 forbids.
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

# Check 5 of 8 -- the SHAPE of all 22 in-scope tables: column count and primary
# key, plus the LEDGER-NAME width that the dump normaliser depends on.
# The right NUMBER of tables with the wrong SHAPE would poison a diff just as
# thoroughly as a missing table, and it would be far harder to notice.
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

  # The width drift the dump normaliser exists to canonicalise:
  # [copybooks/wsledger.cob] declares Ledger-Name pic x(24), the bridge widens it
  # to PIC X(32) [common/nominalMT.cbl:L299], and the column is char(32)
  # [mysql/ACASDB.sql:L127]. The value is not corrupted but the PADDING differs,
  # and padding is visible in a dump -- so this width is load-bearing evidence
  # and is asserted explicitly rather than left implicit in the column count.
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
# It holds because each bridge load paragraph initialises its host-variable group
# before a write, so an unset field becomes zero or space rather than SQL NULL.
# That is why the Python data-access layer must DEFAULT rather than omit, and why
# a nullable column appearing here would signal the schema had drifted.
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

# Check 7 of 8 -- no binary floating-point column anywhere (R-2).
# The structural half of "zero binary floating point in accounting computation":
# an accounting value cannot traverse a float if no float column exists. Asserted
# on the SERVER as well as in the file, because the file check cannot see a column
# someone altered by hand.
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
  #    variables and restores them at the tail [mysql/ACASDB.sql:L13-L22]; this
  #    re-asserts that it left autocommit alone rather than assuming it.
  acas_assert_autocommit 'after the apply'
  acas_check 'PASS' 'autocommit still 0/0 after the apply'

  ACAS_RESET_VERIFIED=1
}

# STAGE 3 -- DURABILITY IN A FRESH SESSION
#
# Durability is the one property the whole comparison rests on, and under the
# AAP-mandated `autocommit=0` it holds for the SCHEMA but not for COBOL DATA.
# The two cases must not be conflated:
#   * DDL is durable either way -- InnoDB commits CREATE TABLE and DROP TABLE
#     implicitly, regardless of the autocommit mode -- so the schema apply this
#     stage verifies survives a fresh session, and this script never needs to
#     change the mode for it. That is what makes the check below meaningful at
#     all under the mandated mode.
#   * DML from the frozen COBOL is NOT durable, because the loaders and bridges
#     reach no COMMIT. Any subsequent re-seed or COBOL posting run therefore
#     leaves nothing behind. That consequence is reported by the autocommit
#     assertion and by harness/seed.sh, and is preserved as the frozen code's own
#     defect (R-4) rather than repaired here.
#
# The schema property is not trusted; it is PROVED. A brand-new client process,
# hence a brand-new server session, re-counts the tables. If the apply had
# somehow landed inside an uncommitted transaction, the fresh session would see
# the OLD tables and this check would fail -- which is exactly the empirical
# verification the plan asks for.
# =============================================================================
acas_verify_durability() {
  acas_stage 'Stage 3/4: durability -- re-count in a FRESH session'

  # acas_sql_scalar spawns a new client process per call, so this is genuinely a
  # new connection and a new session, not a reuse of the one that applied the
  # schema.
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


# STAGE 4 -- RE-SEED
# Delegated to harness/seed.sh, which reproduces the flat-file-to-loader
# contract of [common/masterLD.sh:L44-L115] and its exit-code semantics by
# driving the maintainer's own compiled `common/*LD.cbl` programs.
# WHY DELEGATE. Duplicating the seed would create a second definition of the
# seeded state -- the one thing both sides of the parity diff must agree on
# absolutely. Why seed.sh reproduces the frozen script's CONTRACT rather than
# executing it is settled there, and is not re-litigated here.
# The compiled loaders run OUT OF PROCESS and confined to harness/ -- the
# sanctioned use of compiled COBOL under R-1. ITS STATUS IS PROPAGATED
# VERBATIM, so a caller can still tell seed.sh's own failures from a load
# program's 128, 64 or 16 [common/masterLD.sh:L37-L39]; ours are 80..88.
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
  # must be classified, not merely propagated by `set -e'.
  #
  # Bounded by ACAS_TIMEOUT_SEED. seed.sh bounds each individual loader itself,
  # but this bounds the WHOLE delegated stage: a run that makes progress forever
  # -- each loader finishing inside its own budget while the sequence never ends
  # -- would otherwise hang the reset indefinitely.
  acas_deadline_prefix "$ACAS_TIMEOUT_SEED"
  local rc=0 started elapsed
  started="$SECONDS"
  "${ACAS_DEADLINE_ARGV[@]}" "${argv[@]}" || rc=$?
  elapsed=$(( SECONDS - started ))
  ACAS_RESET_SEED_RC="$rc"

  # Checked BEFORE the classification below, because "never finished" is not one
  # of the frozen load-program return codes and must not be reported as one.
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

# The other half of the scenario-binding fix. harness/seed.sh stages the scenario's
# declared seed files into a scenario-owned fixture directory and leaves a marker
# behind [harness/seed.sh, ACAS_FIXTURE_MARKER]. Reset asserts that marker here.
#
# Why this is a correctness check and not bookkeeping: stage 5 exists so the
# Python cycle starts from BYTE-FOR-BYTE the state the COBOL cycle started from.
# If the re-seed drew from a different set of files than the original seed did,
# that premise is false, every downstream table difference is unattributable, and
# the empty diff the protocol treats as proof would be proof of nothing. A
# scenario named on the command line but not actually reflected in the seed is
# exactly the failure this catches.
acas_assert_reseed_used_fixture() {
  # No scenario named means no fixture was staged, and the seed came from the
  # ambient data directory for both cycles. Symmetric, so nothing to prove.
  [[ -n "$ACAS_RESET_SCENARIO" ]] || return 0

  local stem marker
  stem="${ACAS_RESET_SCENARIO##*/}"
  stem="${stem%.*}"

  local base="${ACAS_RESET_DATA_DIR:-${ACAS_DATA:-}}"
  if [[ -z "$base" ]]; then
    acas_warn "cannot locate the scenario fixture: neither --data-dir nor ACAS_DATA is set, so the marker for '$stem' cannot be confirmed"
    acas_check 'WARN' "scenario fixture for '$stem' unconfirmed (no data directory known)"
    return 0
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

  # The marker records the file set and a SHA-256 per file, with no clock, pid or
  # uuid in it, so it is directly comparable between the two seeds of one run.
  local files
  files="$(awk -F'\t' '$1 == "files" { print $2 }' -- "$marker" 2>/dev/null || true)"
  acas_ok "re-seed used the '$stem' scenario fixture (${files:-?} declared file(s))"
  acas_check 'PASS' "re-seed bound to scenario '$stem' (${files:-?} file(s))"
  acas_log "fixture marker = $marker"
}

# REPORTING THE OUTCOME
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
  # NOT satisfy the gate -- and evidence produced from it has to carry that fact
  # with it rather than look identical to evidence from a canonical target.
  acas_log "target                : $(acas_reset_target_label)"
  if (( ACAS_RESET_ACK_USED )); then
    acas_log "disposability         : OVERRIDDEN by an explicit acknowledgement"
    printf '\nNOTE: this reset proceeded under --acknowledge-destructive, so one or more\n'
    printf '      disposability proofs did not hold. See the findings above.\n'
  else
    acas_log 'disposability         : proved (canonical target, sentinel present)'
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

# DRY RUN
# Prints exactly what a real run would do and touches nothing: no statement is
# issued, no lock is taken, no table is dropped. The frozen-artifact invariants
# ARE checked, because they are pure reads of the checkout and they are the whole
# point of looking before leaping.
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
  acas_note 'in a dry run; a real run refuses to reset unless autocommit is OFF, globally'
  acas_note 'and for the session, as the Agent Action Plan mandates (sections 0.2.1.1,'
  acas_note '0.4.1.7 and 0.5.2, from [common/glbatchLD.cbl:L9-L13]). Under that mode the'
  acas_note 'frozen COBOL, which reaches no COMMIT, leaves no durable rows -- reported'
  acas_note 'as the reproduced legacy defect (R-4), never repaired here'
}

# MAIN
# Strictly sequential (R-3). No stage is backgrounded and none is parallelised.
# Nothing here writes to $ACAS_REPO.
# The order is deliberate and is the whole discipline of the script: assert
# everything that can be asserted BEFORE 33 tables are dropped, so a run that
# cannot finish has not started.
acas_main() {
  acas_parse_args "$@"

  # FIRST, before anything can spawn an external command: resolve and freeze
  # every deadline. It validates each budget and makes them readonly, which is
  # the invariant acas_sql_argv and acas_build_sql_argv rely on.
  acas_resolve_deadlines

  printf 'harness/reset_db.sh -- stage 5 of the eight-stage parity protocol\n'
  printf '  seed -> run(COBOL) -> dump -> normalize -> RESET -> run(Python) -> dump -> diff\n'
  printf 'Drops and re-applies the FROZEN mysql/ACASDB.sql verbatim, then re-seeds, so the\n'
  printf 'Python cycle starts from byte-for-byte the state the COBOL cycle started from.\n'
  printf 'The drop lives in the frozen file itself, so this script emits no DDL (R-3).\n'

  acas_assert_environment
  acas_open_log

  # The static half of the disposability gate runs HERE: after acas_open_log so
  # that a refusal is recorded in the reset log as evidence, but before anything
  # in this script has contacted a server. A misaimed invocation is therefore
  # refused without a single packet leaving the machine.
  acas_assert_disposable_static

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

  # The server-side half of the gate runs as early as it possibly can: the first
  # thing after readiness, and BEFORE acas_assert_privileges and acas_apply_schema.
  # Ordering is the whole point -- a privilege check that succeeds tells you the
  # account CAN destroy this schema, which is the opposite of permission to.
  acas_assert_disposable_server

  # The banner is raised HERE rather than inside acas_assert_autocommit, because
  # that function is deliberately dual-use: it runs once as this precondition and
  # once as check 8 of 8 after the apply, where a "Preconditions 8/9" banner
  # would be actively misleading. Raising it at the call site keeps the
  # precondition numbering complete AND makes the ERR/EXIT traps name the
  # autocommit gate -- not MariaDB readiness -- as the failing stage.
  acas_stage 'Preconditions 8/9: autocommit is OFF (AAP-mandated; the frozen COBOL never commits)'
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
