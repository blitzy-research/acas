#!/usr/bin/env bash
# =============================================================================
# harness/seed.sh
#
# Seed the frozen ACASDB schema from the ACAS Cobol flat files by running the
# compiled `common/*LD.cbl' load programs, in the maintainer's own order, and
# CHECKING their return codes.
#
# This is stage 1 of the eight-stage parity protocol, and it is also stage 5's
# tail by way of harness/reset_db.sh:
#
#     seed -> run(COBOL) -> dump -> normalize -> reset -> run(Python) -> dump -> diff
#
# Both sides of that diff must start from IDENTICAL seeded state or the diff
# means nothing, so this script is deterministic and repeatable by design
# (R-6). Run it with the canonical invocation documented at
# [harness/docker-compose.yml:L263-L274].
#
# -----------------------------------------------------------------------------
# WHY THIS SCRIPT REPRODUCES common/masterLD.sh RATHER THAN INVOKING IT
# -----------------------------------------------------------------------------
# Two independent reasons. The second is decisive.
#
#   1. THE AUTHOR MARKS IT UNTESTED. [common/masterLD.sh:L4-L5] is, verbatim:
#          #   THIS SCRIPT HAS NOT YET BEEN TESTED
#          #   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#      [Changelog:L21-L22] corroborates it independently: "Revised scripts
#      masterUNL.sh, masterRES.sh & masterLD and so far only tested masterUNL."
#
#   2. IT CANNOT EXECUTE AT ALL. All 24 of its loader lines
#      [common/masterLD.sh:L93-L116] are written
#          if [ -e X.dat ];  then YLD fi
#      with no `;' or newline before `fi', so the `then' list is never
#      terminated and the file is not valid shell:
#          $ bash -n common/masterLD.sh
#          common/masterLD.sh: line 124: syntax error: unexpected end of file
#      Verified against this checkout; the exit status is 2.
#
# THE FROZEN FILE IS NOT FIXED (R-3, R-4). common/masterLD.sh is never
# executed, never sourced, never copied-and-repaired, never sed-ed, and the
# missing semicolons are never added. "A defect reproduced is correct; a defect
# fixed is a failure." Its CONTRACT is reproduced here instead, in valid shell,
# and the frozen file stays exactly as the maintainer left it.
#
# -----------------------------------------------------------------------------
# THE SEVEN DELIBERATE DEVIATIONS FROM THE FROZEN SCRIPT
# -----------------------------------------------------------------------------
# Every deviation is enumerated, cited and justified, so none of them is
# accidental and a reviewer can audit each one (R-5).
#
#   D1  VALID SHELL. The 24 loader lines are reproduced as working `if'
#       statements. Reason: reason 2 above. The frozen text is quoted verbatim
#       beside each mapping so the reproduction is checkable line by line.
#       [common/masterLD.sh:L93-L116]
#
#   D2  $ACAS_DATA INSTEAD OF ~/ACAS. The frozen script does `cd ~/ACAS'
#       [common/masterLD.sh:L45] because it "MUST be run from the ACAS data
#       directory containing all of the Cobol Data files"
#       [common/masterLD.sh:L27-L28]. A home-relative path has no meaning in a
#       container, so the harness data volume is used instead
#       ($ACAS_DATA = /data per [harness/docker-compose.yml]), overridable with
#       --data-dir. The `cd' itself is preserved.
#
#   D3  ACAS ENVIRONMENT VARIABLES ARE USED. [common/masterLD.sh:L30-L31] says
#       "IT DOES NOT - NOT make use of the system param file or ACAS
#       environment variables." That was true of the pre-RDB loaders; it is no
#       longer true of the compiled ones. Every one of the 28 `common/*LD.cbl'
#       programs copies [copybooks/Proc-Get-Env-Set-Files.cob] (verified: 28 of
#       28) and its `zz020-Set-the-Paths' paragraph PREFIXES EVERY FILE NAME
#       with ACAS_LEDGERS + the OS delimiter
#       [copybooks/Proc-Get-Env-Set-Files.cob:L125-L136]. So ACAS_LEDGERS --
#       not the working directory -- is what actually decides where a loader
#       looks for system.dat. This script therefore asserts and exports
#       ACAS_LEDGERS to match the data directory, and puts $ACAS_BUILD/common
#       on PATH so the loaders built by harness/build_oracle.sh are found.
#
#   D4  THE RETURN CODES ARE TRAPPED FOR EVERY LOADER. [common/masterLD.sh:
#       L41-L42] is the author's own admission that they are not:
#       "MUST GET round to trapping these param errors (>63) / but it is a lot
#       of typing :)". He traps them for the four system loaders only
#       [common/masterLD.sh:L56,L65,L74,L83] and for none of the 24 mappings.
#       This script traps all of them. That changes nothing about how a loader
#       behaves; it is the harness doing the checking the author says he never
#       got round to.
#
#   D5  16 IS FATAL BY DEFAULT. 16 means "error writing data to rdb"
#       [common/masterLD.sh:L39], [common/glbatchLD.cbl:L445]. It is not > 63,
#       so the frozen threshold would let the seed continue with a PARTIALLY
#       loaded table -- and a partial seed silently poisons every subsequent
#       state diff, which is the one failure this harness exists to prevent.
#       Set ACAS_SEED_STRICT=0 to restore the frozen >63-only tolerance
#       exactly. The `dfltLD' asymmetry in D7 is frozen behaviour and is NOT
#       governed by this switch.
#
#   D6  NO INTERACTIVE PAGER. [common/masterLD.sh:L119-L123] runs
#       `less SYS-DISPLAY.log', which would block the harness for ever, and
#       falls off the end with no explicit exit when the log is absent. The
#       completion message is kept, the log is written to standard output with
#       `cat', and the script always exits with a meaningful status. This
#       follows the plan's rule for interactive statements: a prompt that
#       merely pauses for acknowledgement is dropped, because its only effect
#       is to block a terminal, and a diagnostic with no database effect
#       becomes a log record.
#
#   D7  IN-SCOPE LOADERS ONLY. The frozen script runs all 24 mappings. Eight of
#       them load tables the posting cycle never touches, so they are NEVER
#       invoked here: delfolioLD, sldelinvnosLD, deliveryLD, paymentsLD,
#       plautogenLD, slautogenLD, auditLD and stockLD. If one of their flat
#       files is present the skip is LOGGED, naming the out-of-scope table, so
#       it is visible rather than silent.
#
# NOT a deviation, and preserved exactly: the `dfltLD' return-code test is
# `!= 0' [common/masterLD.sh:L83] while the other three system loaders use
# `-gt 63' [common/masterLD.sh:L56,L65,L74]. That asymmetry is in the frozen
# source. It is reproduced, not harmonised (R-4).
#
# One transcription note, for anyone diffing this file against a summary of the
# frozen script: all FOUR system-block abort messages are byte-identical --
# "Problem with data in system.dat - Aborting". Verified with `cat -A' on
# [common/masterLD.sh:L58,L67,L76,L85]. The frozen file is the arbiter (R-6).
#
# -----------------------------------------------------------------------------
# WHERE THIS FILE SITS
# -----------------------------------------------------------------------------
# harness/ is the compiled oracle and is a SIBLING of acas_posting/, never a
# sub-package. This script imports nothing from acas_posting, creates no
# harness/__init__.py, and invokes the compiled loaders only as external
# processes. That is the sanctioned use of compiled COBOL under R-1: it is
# confined to harness/ and used as a comparison and SEEDING utility.
#
# THE FROZEN-ARTIFACT GUARANTEE
#   This script READS $ACAS_REPO and never writes to it. The flat files live in
#   the data directory, the loaders live under $ACAS_BUILD, and the logs live
#   under $ACAS_OUT/seed.
#
# NO SCHEMA CHANGE, NO ADDED VALIDATION, STRICTLY SEQUENTIAL (R-3)
#   No DDL is emitted -- no CREATE, no ALTER, no index, no migration tool. The
#   only SQL issued is the read-only autocommit assertion below. The flat files
#   are tested for EXISTENCE and nothing else, exactly as the frozen script
#   tests them: no row counts, no header checks, no charset checks, no
#   referential checks. The loaders run one at a time, in the frozen order,
#   never in parallel: no `&', no `xargs -P', no job control.
#
# RULES PROVENANCE
#   There is no user rules document for this project: `review_rules' returns
#   "No user rules provided." The binding rules R-1..R-6 come from the Agent
#   Action Plan and are cited inline as (R-n). Where they are silent this
#   script holds to enterprise-standard best practice.
#     R-1 no COBOL at runtime          R-2 zero binary floating point
#     R-3 no schema change, sequential R-4 anomalies reproduced, never fixed
#     R-5 full traceability            R-6 compiled behaviour is the tie-breaker
#
# USAGE
#   Run `harness/seed.sh --help'.
# =============================================================================

# Strict mode. -E propagates the ERR trap into functions and subshells so an
# unexpected failure is attributed to a line number instead of being ignored.
#
# READ THIS BEFORE CHANGING THE ERROR HANDLING: `set -e' is NOT sufficient here
# and must not be relied on to police the loaders. A loader's non-zero status is
# DATA -- 128, 64 and 16 each mean something specific -- and this script has to
# CLASSIFY it, not merely propagate it. Every loader is therefore invoked with
# errexit suspended for exactly the length of the call, its status captured, and
# the classification applied by acas_classify_rc. See acas_invoke_loader.
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
# DELIBERATELY CHOSEN NOT TO COLLIDE WITH A LOADER RETURN CODE. The loaders
# return 128, 64 and 16 [common/masterLD.sh:L37-L39], so this script's own
# failures use the 70-79 band and nothing else. The rule for an automated
# caller is therefore unambiguous:
#
#     0        clean seed
#     70..73   THIS SCRIPT failed a precondition of its own
#     anything else  a LOADER's own return code, propagated verbatim exactly as
#                    the frozen script propagates it with `exit $rc'
#                    [common/masterLD.sh:L59,L68,L77,L86]
# -----------------------------------------------------------------------------
readonly EX_OK=0
readonly EX_USAGE=70          # bad command line
readonly EX_PRECONDITION=71   # environment, directory or loader assertion
readonly EX_DATABASE=72       # MariaDB unreachable, or credentials rejected
readonly EX_AUTOCOMMIT=73     # autocommit is not off -- see acas_assert_autocommit

# -----------------------------------------------------------------------------
# THE SYSTEM-FILE BLOCK -- [common/masterLD.sh:L50-L88]
#
# Frozen order, and the reason for it, [common/masterLD.sh:L47-L48] verbatim:
# "First, process the five different records in the system file that are used to
# create five RDBMS tables holding only one record each."
#
# Each entry: <loader>:<frozen test>:<locator>:<target table>
# The frozen test is `gt63' or `ne0' and is transcribed from the frozen line
# named in the locator. dfltLD's `ne0' is the asymmetry preserved under R-4.
# -----------------------------------------------------------------------------
readonly -a ACAS_SEED_SYSTEM_BLOCK=(
  'systemLD:gt63:L52,L56:SYSTEM-REC'
  'sys4LD:gt63:L61,L65:SYSTOT-REC'
  'finalLD:gt63:L70,L74:SYSFINAL-REC'
  'dfltLD:ne0:L79,L83:SYSDEFLT-REC'
)

# The one flat file the whole system block is guarded on, [common/masterLD.sh:L51].
readonly ACAS_SEED_SYSTEM_FLAT_FILE='system.dat'

# The abort message the maintainer prints on a system-block failure, byte-exact
# from [common/masterLD.sh:L58,L67,L76,L85].
readonly ACAS_SEED_SYSTEM_ABORT_MSG='Problem with data in system.dat - Aborting'

# The two frozen return-code tests, quoted for the diagnostics so a reader can
# match a message straight back to the frozen line. Written with double quotes
# and an escaped dollar so the text is literal while remaining lint-clean.
readonly ACAS_SEED_TEST_TEXT_GT63="if [ \$rc -gt 63 ]"
readonly ACAS_SEED_TEST_TEXT_NE0="if [ \$rc != 0 ]"

# -----------------------------------------------------------------------------
# THE 16 IN-SCOPE MAPPINGS -- [common/masterLD.sh:L93-L116]
#
# FROZEN ORDER PRESERVED. The frozen list is alphabetical by flat-file name and
# is NOT reordered here to "seed parents before children": the frozen schema
# contains exactly one FOREIGN KEY, on the out-of-scope PLPAY-RECrg01, so
# nothing requires reordering, and reordering would move the loaders' commit
# boundaries and therefore change the seeded state.
#
# Each entry: <flat file>:<loader>:<frozen locator>:<target table(s)>
# All 16 use the `gt63' test -- the threshold the author names at
# [common/masterLD.sh:L41] but never wrote for these lines (D4).
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# THE 8 OUT-OF-SCOPE MAPPINGS -- NEVER INVOKED (D7)
#
# Same triple shape, plus the out-of-scope table each loader writes. The table
# names were read from the bridge each loader feeds -- the `TABLE=' directive in
# common/<bridge>MT.scb -- not guessed. Together they are exactly the 11
# out-of-scope tables of the 33 in the frozen schema.
# -----------------------------------------------------------------------------
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

# The interactive tail this script does NOT reproduce, [common/masterLD.sh:L119].
readonly ACAS_SEED_SYSOUT_LOG='SYS-DISPLAY.log'
readonly ACAS_SEED_COMPLETE_MSG='All loads complete but check SYS-DISPLAY.log'

# The four runtime loader paths, in the order the repository declares them.
# [etc/ld.so.conf.d/gnucobol.conf]
readonly -a ACAS_SEED_LOADER_PATHS=(
  /usr/local/lib/gnucobol
  /usr/local/lib
  /usr/local/mysql/lib
  /usr/lib
)

# The environment contract, identical in shape to the one
# harness/build_oracle.sh asserts, so a container configured for one stage is
# configured for both. ACAS_DB_SOCKET may legitimately be EMPTY -- Compose sets
# it so on purpose because the harness connects over TCP -- but it must be
# DECLARED.
readonly -a ACAS_SEED_REQUIRED_ENV_NONEMPTY=(
  ACAS_REPO ACAS_BUILD ACAS_DATA ACAS_OUT
  ACAS_DB_HOST ACAS_DB_PORT ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD
  ACAS_LEDGERS ACAS_BIN
)
readonly -a ACAS_SEED_REQUIRED_ENV_DECLARED=(
  ACAS_DB_SOCKET
)

# -----------------------------------------------------------------------------
# Mutable state. Declared up front because `set -u' makes an unset array a
# fatal reference.
# -----------------------------------------------------------------------------
ACAS_SEED_DATA_DIR=''          # --data-dir, defaults to $ACAS_DATA
ACAS_SEED_SCENARIO=''          # optional positional scenario file
ACAS_SEED_DRY_RUN=0            # --dry-run
ACAS_SEED_LOG=''               # $ACAS_OUT/seed/seed.log
ACAS_SEED_JOBSTATUS=0          # JOBSTATUS, tracked as [common/masterLD.sh:L50]
ACAS_SEED_RAN=0                # loaders actually executed
ACAS_SQL_OUT=''                # last successful scalar query result
ACAS_SQL_DIAG=''               # last client diagnostic, for error messages
declare -a ACAS_SEED_ONLY=()         # --only, validated loader names
declare -a ACAS_SEED_SUMMARY=()      # the final table, one row per loader
declare -a ACAS_SEED_WARN_SUMMARY=() # non-fatal findings, replayed at the end

# =============================================================================
# REPORTING
#
# Stage banners are numbered so the log reads as the deterministic staged
# orchestration the plan prescribes (R-6): explicit, ordered, individually
# reported, individually asserted.
#
# Everything printed here goes to standard output AND, once the log directory
# exists, to $ACAS_OUT/seed/seed.log. Nothing is written under
# $ACAS_OUT/<scenario>/, because the determinism test requires byte-identical
# scenario dumps and a clock reading in a compared file would break it.
# =============================================================================

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

# Split a `<flat file>:<loader>:<locator>:<table>' entry into four globals.
# Done with parameter expansion rather than `read -r -d' because the final field
# may itself contain spaces (e.g. "SAINVOICE-REC + SAINV-LINES-REC") and must
# survive intact.
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

# Split a `<loader>:<test>:<locator>:<table>' system-block entry. Same shape,
# different first field, kept separate so neither reader has to guess.
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

# Record one row of the closing summary table.
# acas_summary_row <loader> <flat file> <present> <rc> <decision>
acas_summary_row() {
  ACAS_SEED_SUMMARY+=("$(printf '%-14s %-17s %-8s %-5s %s' "$1" "$2" "$3" "$4" "$5")")
}

# Membership test over an array passed by name, so the arrays stay readonly.
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
# `ps', and never on disk. That is a stronger guarantee than a
# --defaults-extra-file plus a cleanup trap, and it is why no temporary file is
# created anywhere in this script. `set -x' is never enabled, for the same
# reason.
# =============================================================================
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
  # The partial-seed warning is only true once a loader has actually run. A
  # precondition failure leaves the database exactly as it was, and saying
  # otherwise would send the operator to reset_db.sh for no reason.
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

# =============================================================================
# USAGE
# =============================================================================
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
  <scenario.yaml>     Optional. The scenario being seeded, accepted so that the
                      canonical eight-stage invocation documented at
                      [harness/docker-compose.yml:L263-L274] works verbatim.
                      It is checked for readability and reported for
                      traceability; it is NOT parsed. A scenario's inputs reach
                      the loaders through the flat files it places in the data
                      directory -- in particular Run-Date
                      [copybooks/wssystem.cob:L67] and the three-state IRS
                      fan-out switch [copybooks/wssystem.cob:L179-L181] arrive
                      through system.dat, which the scenario owns.

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
  ACAS_SEED_STRICT=0        Restore the frozen >63-only tolerance, so return
                            code 16 ("error writing data to rdb",
                            [common/masterLD.sh:L39]) no longer aborts the seed.
                            Default 1: 16 IS fatal, because a partial seed
                            silently poisons every subsequent state diff (D5).
                            The frozen dfltLD `!= 0' test
                            [common/masterLD.sh:L83] applies either way.
  ACAS_DB_WAIT_TIMEOUT=N    Seconds to wait for MariaDB (default 180).
  ACAS_DB_AUTH_GRACE=N      Seconds to tolerate "Access denied" before failing
                            fast, capped at ACAS_DB_WAIT_TIMEOUT (default 15).

Exit codes:
  0        clean seed
  70       usage        71  precondition
  72       database     73  autocommit is not off
  anything else  a LOADER's own return code, propagated verbatim as the frozen
                 script does with `exit $rc' [common/masterLD.sh:L59,L68,L77,L86]:
                 128 params not set up, 64 RDB not set up, 16 rdb write error
                 [common/masterLD.sh:L37-L39].

This script emits no DDL, adds no validation of the flat files beyond the
existence test the frozen script performs, runs the loaders strictly one at a
time, writes nothing under $ACAS_REPO, and never sets autocommit.
USAGE
}


# =============================================================================
# ARGUMENTS
# =============================================================================

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

# Validate one --only name. Deliberately NOT a value-returning helper:
# `acas_die' calls `exit', and inside a command substitution that would
# terminate only the subshell, leaving the caller running with an empty value.
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
        # The optional scenario positional. Accepted for compatibility with the
        # canonical invocation at [harness/docker-compose.yml:L263-L274].
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

  # Note the test is on `only_given', NOT on `only_raw' being non-empty: an
  # explicit `--only ""' names nothing at all and must be rejected as a usage
  # error rather than silently degrading into "seed every loader".
  if (( only_given )); then
    local name
    local -a only_allowed=()
    # Split a comma-separated list without disturbing the global IFS, which is
    # deliberately $'\n\t' (see the strict-mode block), so unquoted word
    # splitting on spaces is not available here.
    #
    # `printf "%s\n"' -- NOT `printf "%s"' -- terminates the final field, and
    # the `|| [[ -n "$name" ]]' guard admits it even if the terminator were
    # ever lost. Both are required: `read' returns non-zero on an unterminated
    # final field, and with neither safeguard the loop body is skipped and the
    # last name in the list is SILENTLY DROPPED. Do not "simplify" either away.
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

# =============================================================================
# PRECONDITIONS
#
# This script ASSERTS its environment; it never installs one and never creates a
# database object. Asserting here means a misconfigured container fails in
# seconds with a named cause, instead of a loader returning a bare 128 whose
# real reason -- a data directory the loader was never told about -- is invisible.
# =============================================================================

# Precondition 1 of 7.
acas_assert_environment() {
  acas_stage 'Preconditions 1/7: environment contract'

  local name missing=0
  for name in "${ACAS_SEED_REQUIRED_ENV_NONEMPTY[@]}"; do
    if [[ -z "${!name-}" ]]; then
      printf 'FATAL: required environment variable %s is unset or empty.\n' "$name" >&2
      missing=1
    fi
  done
  for name in "${ACAS_SEED_REQUIRED_ENV_DECLARED[@]}"; do
    # `-v' tests declaration, not content. An empty ACAS_DB_SOCKET is valid and
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

  # ACAS_LEDGERS and ACAS_BIN are tested by the COBOL as `(1:1) = spaces' --
  # only the FIRST CHARACTER -- so a value that merely BEGINS with a space
  # triggers the interactive block just as an empty one does. Reproduce that
  # sensitivity exactly rather than approximating it with a non-empty test.
  # [copybooks/Proc-Get-Env-Set-Files.cob:L20-L28]
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
        '[common/glbatchLD.cbl:L188-L189] [harness/docker-compose.yml:L296-L299]'
    fi
  done

  # The COBOL reads its connection details into fixed-width fields. A longer
  # value is silently TRUNCATED, after which the COBOL side fails to
  # authenticate while the Python side succeeds -- a divergence with nothing to
  # do with posting logic. The password's LENGTH is checked; its VALUE is never
  # printed. [copybooks/wsfnctn.cob:L56-L62] [harness/docker-compose.yml:L222-L237]
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

  acas_log "ACAS_REPO   = $ACAS_REPO (read-only checkout; the specification)"
  acas_log "ACAS_BUILD  = $ACAS_BUILD (the loaders built by harness/build_oracle.sh)"
  acas_log "ACAS_DATA   = $ACAS_DATA"
  acas_log "ACAS_OUT    = $ACAS_OUT"
  acas_log "ACAS_BIN    = $ACAS_BIN"
  acas_log "database    = ${ACAS_DB_USER}@${ACAS_DB_HOST}:${ACAS_DB_PORT}/${ACAS_DB_NAME}"
  acas_note 'the password is never printed, never logged and never passed in argv'
}

# Precondition 2 of 7 -- the data directory, and the frozen `cd' (D2).
acas_assert_data_dir() {
  acas_stage 'Preconditions 2/7: the ACAS data directory'

  [[ -n "$ACAS_SEED_DATA_DIR" ]] || ACAS_SEED_DATA_DIR="$ACAS_DATA"

  # An absolute path is REQUIRED, not merely tidy. zz020-Set-the-Paths builds
  # every file name as ACAS_LEDGERS + OS-Delimiter + name, and OS-Delimiter
  # defaults to "/" (`77 OS-Delimiter pic x value "/"',
  # [common/glbatchLD.cbl:L141]). A relative ACAS_LEDGERS would be joined onto
  # the working directory -- which this script sets to the data directory --
  # producing <data>/<data>/system.dat.
  # [copybooks/Proc-Get-Env-Set-Files.cob:L125-L136]
  [[ "$ACAS_SEED_DATA_DIR" == /* ]] || acas_die "$EX_PRECONDITION" \
    "the data directory must be an absolute path; got '$ACAS_SEED_DATA_DIR'." \
    'The loaders prefix every file name with ACAS_LEDGERS and the OS delimiter,' \
    'so a relative path is resolved against the working directory twice.' \
    '[copybooks/Proc-Get-Env-Set-Files.cob:L125-L136]'

  # A path containing a space is silently TRUNCATED at the first space, because
  # the STRING statement takes ACAS_LEDGERS `delimited by space'.
  # [copybooks/Proc-Get-Env-Set-Files.cob:L131,L142]
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

  # Writable because the loaders append their own diagnostics to SYS-DISPLAY.log
  # in this directory, and because the file-handler logger writes here too --
  # [copybooks/Test-Data-Flags.cob:L10] hardcodes `SW-Testing pic 9 value 1' and
  # cannot be switched off, so the log grows on every DAL call.
  [[ -w "$ACAS_SEED_DATA_DIR" ]] || acas_die "$EX_PRECONDITION" \
    "the data directory ($ACAS_SEED_DATA_DIR) is not writable." \
    'The load programs write SYS-DISPLAY.log there, and the frozen file-handler' \
    'logger cannot be disabled [copybooks/Test-Data-Flags.cob:L10].'

  # THE FROZEN-ARTIFACT GUARANTEE. The data directory must not be inside the
  # checkout: seeding writes SYS-DISPLAY.log and the handler log, and a diff
  # touching a frozen path is a defect in the migration however harmless it
  # looks.
  local data_real repo_real
  data_real="$(readlink -f "$ACAS_SEED_DATA_DIR" 2>/dev/null || printf '%s' "$ACAS_SEED_DATA_DIR")"
  repo_real="$(readlink -f "$ACAS_REPO" 2>/dev/null || printf '%s' "$ACAS_REPO")"
  if [[ "$data_real" == "$repo_real" || "$data_real" == "$repo_real"/* ]]; then
    acas_die "$EX_PRECONDITION" \
      "the data directory ($data_real) is inside ACAS_REPO ($repo_real)." \
      'Seeding writes SYS-DISPLAY.log and the file-handler log into the data' \
      'directory, and nothing may ever be written into the frozen checkout.' \
      'Point --data-dir at the /data volume instead.'
  fi

  # D3: ACAS_LEDGERS -- not the working directory -- is what the loaders
  # actually resolve file names against, so it must agree with the directory
  # this script tested for `-e system.dat'. Exporting it is what makes
  # --data-dir mean anything at all.
  local ledgers_real
  ledgers_real="$(readlink -f "${ACAS_LEDGERS}" 2>/dev/null || printf '%s' "${ACAS_LEDGERS}")"
  if [[ "$ledgers_real" != "$data_real" ]]; then
    acas_warn "ACAS_LEDGERS ($ACAS_LEDGERS) differs from the data directory ($ACAS_SEED_DATA_DIR); exporting the data directory instead, so the loaders read the files this script checked."
  fi
  export ACAS_LEDGERS="$ACAS_SEED_DATA_DIR"

  # Reproduce [common/masterLD.sh:L45] `cd ~/ACAS' with the harness data
  # directory (D2). Preserved because it is the frozen contract and because the
  # loaders write SYS-DISPLAY.log relative to the working directory.
  cd "$ACAS_SEED_DATA_DIR" || acas_die "$EX_PRECONDITION" \
    "could not change directory to $ACAS_SEED_DATA_DIR."
  acas_log "working directory = $PWD  (reproduces [common/masterLD.sh:L45])"
  acas_log "ACAS_LEDGERS      = $ACAS_LEDGERS  (the path the loaders prefix onto every file name)"
}


# Open the run log. Fixed file name, truncated at the start of every run, so the
# set of files this script produces is deterministic and two runs leave the tree
# in the same shape. It lives under $ACAS_OUT/seed and NEVER under
# $ACAS_OUT/<scenario>/, which the determinism test compares byte for byte.
acas_open_log() {
  local dir="$ACAS_OUT/seed"
  mkdir -p "$dir" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "could not create the seed log directory $dir." \
    'ACAS_OUT must be a writable volume.'
  ACAS_SEED_LOG="$dir/seed.log"
  : >"$ACAS_SEED_LOG" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "could not write the seed log $ACAS_SEED_LOG."
  # The ONE wall-clock reading in this script. Permitted here because
  # $ACAS_OUT/seed/ is never part of a comparison; it is deliberately kept out
  # of standard output and out of every path the dump tree reaches, so
  # tests/determinism cannot see it.
  {
    printf 'harness/seed.sh run log\n'
    printf 'started (UTC): %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'this file lives under the ACAS_OUT seed directory and is never compared\n'
    printf -- '----------------------------------------------------------------\n'
  } >>"$ACAS_SEED_LOG"
}

# Precondition 3 of 7 -- system.dat. Its own stage, because its absence is the
# single most consequential and least obvious failure in the whole harness.
acas_assert_system_dat() {
  acas_stage "Preconditions 3/7: $ACAS_SEED_SYSTEM_FLAT_FILE"

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
    # flat files (R-3: no added validation) -- but recorded so the operator
    # recognises the symptom. [general/general.cbl:L462-L463] is
    # `if scycle = zero  go to call-system-setup.'
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
    '     broken. [harness/docker-compose.yml:L288-L292]' \
    '' \
    "Seed $ACAS_SEED_SYSTEM_FLAT_FILE into $PWD from the scenario definition" \
    'before invoking this script.'
}

# Precondition 4 of 7 -- the compiled loaders.
acas_assert_loaders() {
  acas_stage 'Preconditions 4/7: the compiled load programs'

  # harness/build_oracle.sh builds all 28 *LD.cbl as executables
  # [common/comp-common.sh:L51] and asserts these 20 by name in
  # $ACAS_BUILD/common. Putting that directory on PATH is part of D3: the frozen
  # script assumes the loaders are already installed on the operator's PATH,
  # which is not true of a container built from harness/Dockerfile.gnucobol.
  local loader_dir="$ACAS_BUILD/common"
  [[ -d "$loader_dir" ]] || acas_die "$EX_PRECONDITION" \
    "$loader_dir does not exist, so the compiled load programs cannot be found." \
    'Run harness/build_oracle.sh first: it copies the checkout into ACAS_BUILD' \
    'and compiles the loaders there.'
  export PATH="$loader_dir:$PATH"
  acas_log "load programs   = $loader_dir (prepended to PATH)"

  # COB_LIBRARY_PATH must resolve the bridge modules each loader CALLs -- a
  # loader is an executable, but glbatchMT and friends are dynamically loadable
  # modules. build_oracle.sh publishes the same value; this re-asserts it so the
  # script also works when invoked outside Compose.
  if [[ -z "${COB_LIBRARY_PATH-}" ]]; then
    export COB_LIBRARY_PATH="$loader_dir"
    acas_note "COB_LIBRARY_PATH was unset; set to $loader_dir so the *MT bridge modules resolve"
  elif [[ ":${COB_LIBRARY_PATH}:" != *":${loader_dir}:"* ]]; then
    export COB_LIBRARY_PATH="$loader_dir:$COB_LIBRARY_PATH"
    acas_note "prepended $loader_dir to COB_LIBRARY_PATH so the *MT bridge modules resolve"
  fi
  acas_log "COB_LIBRARY_PATH = $COB_LIBRARY_PATH"

  # The 20 in-scope loaders, asserted by name and by executability BEFORE
  # anything is seeded. A missing one means build_oracle.sh did not complete,
  # and saying so here is far better than a bare "command not found" halfway
  # through a partial seed.
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

# Precondition 5 of 7 -- the runtime library paths.
acas_assert_library_paths() {
  acas_stage 'Preconditions 5/7: runtime library paths'

  # The loaders link libcob and libmysqlclient, and the repository declares its
  # own loader path order in [etc/ld.so.conf.d/gnucobol.conf]. That file is
  # normally installed into the image and covered by ldconfig; LD_LIBRARY_PATH
  # is set here as well so the loaders resolve even when the cache has not been
  # refreshed (ldconfig needs privileges this script does not assume).
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
  # presents as a loader that dies before it can return one of the documented
  # codes. [common/comp-common.sh:L26] links -L/usr/local/mysql/lib.
  if [[ ! -e /usr/local/mysql/lib/libmysqlclient.so ]]; then
    acas_warn 'libmysqlclient.so was not found under /usr/local/mysql/lib, the prefix every frozen compile line hard-codes [common/comp-common.sh:L26]; a loader that cannot resolve it will fail before it can return 128, 64 or 16.'
  fi
}

# =============================================================================
# DATABASE PRECONDITIONS
# =============================================================================

# A single scalar query, credential-safe.
#
# The password reaches the client through MYSQL_PWD, so it never appears in
# argv and never in `ps'. No --defaults-extra-file is written, so there is no
# credential on disk to leak and none to clean up.
#
# Both a TLS-enforcing client (which needs --skip-ssl against a server with no
# TLS) and a permissive one are tolerated. Standard error is discarded while
# capturing the VALUE, because a permissive client emits a TLS advisory there
# that would otherwise be parsed as data; on failure the attempt is repeated
# with standard error merged so the diagnostic is never lost.
#
# Returns: 0 with the value in ACAS_SQL_OUT; 1 the query failed (diagnostic in
# ACAS_SQL_DIAG); 2 credentials rejected; 3 no client binary available.
acas_sql_scalar() {
  local sql="$1"
  ACAS_SQL_OUT=''
  ACAS_SQL_DIAG=''

  local client variant out rc
  for client in mariadb mysql; do
    acas_have "$client" || continue
    for variant in '' '--skip-ssl'; do
      local -a argv=("$client" '--protocol=TCP')
      if [[ -n "$variant" ]]; then
        argv+=("$variant")
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

# Precondition 6 of 7 -- MariaDB readiness.
acas_wait_for_database() {
  acas_stage 'Preconditions 6/7: MariaDB readiness'

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

  # An open port is not readiness. The loaders authenticate with exactly these
  # credentials, so a wrong user or password must be caught here rather than
  # surfacing as a return code of 64 whose stated meaning ("RDB not set up")
  # would send the operator looking in the wrong place.
  #
  # Two failure shapes, deliberately treated differently: a transient failure is
  # retried for the full timeout, because the port routinely opens before the
  # server will talk; "Access denied" is a configuration error, not a readiness
  # state, so it is retried only for a short grace window -- no amount of
  # waiting fixes a wrong password.
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
          'That verification is not optional: every one of the 28 load programs' \
          'uses commit and rollback and requires autocommit to be OFF' \
          '[common/glbatchLD.cbl:L9-L13]. Seeding with autocommit on would' \
          'produce state the loaders never intended and every downstream diff' \
          'would be untrustworthy.' \
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

# Precondition 7 of 7 -- autocommit MUST be OFF.
#
# ASSERTED, NEVER SET. The setting belongs to the server and is configured once,
# by harness/Dockerfile.mariadb, which writes `autocommit=0' into
# /etc/mysql/conf.d/99-acas-oracle.cnf. harness/docker-compose.yml deliberately
# does not repeat it -- one authority only -- and records that this script
# asserts it. Issuing `SET autocommit' here would both create a second
# authority and corrupt the loaders' commit boundaries (R-4).
#
# [common/glbatchLD.cbl:L9-L13] verbatim:
#     *>  This modules uses commit and rollback so *
#     *>  you MUST ensure that autocommit is OFF   *
#     *>   in the rdb settings. It is as default   *
#     *>   set ON.                                 *
#
# Beyond the plan, and verified across the frozen tree: that comment is in EVERY
# ONE of the 28 common/*LD.cbl programs, not just the batch loader -- e.g.
# [common/analLD.cbl:L11], [common/finalLD.cbl:L10], [common/dfltLD.cbl:L10],
# [common/systemLD.cbl:L9], [common/sys4LD.cbl:L10]. The maintainer's inline
# notes record the consequence: [common/analLD.cbl:L377] "otherwise as normally
# it is set to autocommit !!!!!", [common/analLD.cbl:L442] "These do not work
# during testing with mariadb - Non transactional model or autocommit set ON",
# and [common/finalLD.cbl:L361] "which can be ignored unless you thought
# autocommit was set up."
#
# The `+ 0' coercion is required, not cosmetic: autocommit is a boolean system
# variable and renders as ON/OFF in a string context, so a bare select can hand
# back "ON" where a caller expects 1.
acas_assert_autocommit() {
  acas_stage 'Preconditions 7/7: autocommit must be OFF'

  local rc=0
  acas_sql_scalar 'select concat_ws(0x2f, @@GLOBAL.autocommit + 0, @@SESSION.autocommit + 0)' || rc=$?
  if (( rc != 0 )); then
    acas_die "$EX_DATABASE" \
      'could not read the autocommit setting from the server.' \
      "Client said: ${ACAS_SQL_DIAG:-<no diagnostic>}"
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
      'Every one of the 28 ACAS load programs uses commit and rollback and' \
      'states the requirement in its own header, [common/glbatchLD.cbl:L9-L13]:' \
      '"This modules uses commit and rollback so you MUST ensure that autocommit' \
      'is OFF in the rdb settings. It is as default set ON."' \
      'With autocommit on, the loaders commit at boundaries they never chose,' \
      'their rollbacks silently do nothing [common/analLD.cbl:L442], and the' \
      'seeded state is not the state the loaders intended -- which makes every' \
      'subsequent COBOL-versus-Python state diff untrustworthy.' \
      'This script deliberately does NOT fix it: the setting has exactly one' \
      'authority, harness/Dockerfile.mariadb, which writes autocommit=0 into' \
      '/etc/mysql/conf.d/99-acas-oracle.cnf. Start the harness MariaDB service' \
      'built from that Dockerfile, or set autocommit=0 in the server' \
      'configuration and restart it.'
  fi
  acas_log 'verified: autocommit is off, globally and for this session'
}


# =============================================================================
# LOADER INVOCATION AND RETURN-CODE CLASSIFICATION
#
# THE DOCUMENTED RETURN CODES -- [common/masterLD.sh:L37-L39] verbatim:
#     # If params are not set up, they will exit with 128
#     # if  RDB not set up will exit with 64
#     #   if error writing data to rdb with 16
#
# Each one was verified in the loader source rather than taken on trust. In
# common/glbatchLD.cbl:
#     L223  move 128 to return-code  + L224 goback.   `open input System-File' failed
#     L233  move 128 to return-code  + L234 goback.   read of record 1 failed, "Not set up ?"
#     L290  move  64 to Return-Code  + L291 goback.   RDBMS-DB-Name = spaces, or Cobol files only
#     L445  move  16 to return-code                   *> rdb problem?
# with a bare `goback' -- return code 0 -- at L248, L253, L258, L317, L330, L345
# and L516.
#
# A consequence worth knowing when reading a failure: BOTH 128 sites are the
# loader failing to open or read the system file, which it resolves through
# ACAS_LEDGERS. So a 128 usually means the loader was pointed at the wrong
# directory, not that the data is bad -- which is why this script asserts
# system.dat and ACAS_LEDGERS before it starts.
# =============================================================================
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

# acas_invoke_loader <loader>
#
# Runs exactly one load program, sequentially, in the foreground (R-3): no `&',
# no `xargs -P', no job control anywhere in this script.
#
# WHY THE LOADER RUNS AS AN `if' CONDITION -- DO NOT "SIMPLIFY" THIS AWAY.
#
# A loader's non-zero status is DATA that this script has to classify, not an
# error to propagate: 128, 64 and 16 each mean something specific and each leads
# to a different message. Under plain `set -e' the script would die on the
# loader's own documented failure path before it could say why.
#
# `set +e' ALONE IS NOT SUFFICIENT, and this is the trap that catches people.
# Suspending errexit does NOT suspend the ERR trap -- measured on this bash: with
# `set +e' active, a failing pipeline still fires `trap ... ERR' and the handler
# reports a spurious "unexpected failure" on top of the real, classified
# diagnostic. Bash exempts a command from BOTH errexit and the ERR trap when it
# is "part of the test following the if or elif reserved words", so running the
# loader as an `if' condition is what makes a documented loader failure an
# ordinary, quiet result. It also needs no trap juggling and no `set +e', so
# there is no window in which the script's own errors would go unnoticed.
#
# The loader's combined output is passed through unaltered to standard output and
# copied into the run log; PIPESTATUS[0] rather than $? is read, because the
# status wanted is the loader's, not tee's. The result is left in
# ACAS_SEED_LAST_RC and the function itself always succeeds, so no caller has to
# reason about errexit.
acas_invoke_loader() {
  local loader="$1"
  ACAS_SEED_CURRENT_LOADER="$loader"
  ACAS_SEED_LAST_RC=0

  if "$loader" 2>&1 | tee -a "$ACAS_SEED_LOG"; then
    ACAS_SEED_LAST_RC=0
  else
    ACAS_SEED_LAST_RC=${PIPESTATUS[0]}
  fi

  ACAS_SEED_CURRENT_LOADER=''
  ACAS_SEED_RAN=$(( ACAS_SEED_RAN + 1 ))
  if (( ACAS_SEED_LAST_RC > ACAS_SEED_WORST_RC )); then
    ACAS_SEED_WORST_RC="$ACAS_SEED_LAST_RC"
  fi
  return 0
}

# acas_abort_on_rc <rc> <loader> <flat file> <test kind> <locator> <scope>
#
# Applies the frozen test first, then the D5 strict deviation.
#
#   test kind `gt63'  -- `if [ $rc -gt 63 ]', the test the frozen script writes
#                        for systemLD, sys4LD and finalLD
#                        [common/masterLD.sh:L56,L65,L74] and the threshold it
#                        names for everything else [common/masterLD.sh:L41].
#   test kind `ne0'   -- `if [ $rc != 0 ]', the STRICTER test the frozen script
#                        writes for dfltLD ALONE [common/masterLD.sh:L83].
#
# THE ASYMMETRY BETWEEN THOSE TWO TESTS IS IN THE FROZEN SOURCE AND IS
# REPRODUCED, NOT HARMONISED (R-4). A return code of 1 from dfltLD aborts the
# seed; the same code from systemLD does not. That is what the maintainer wrote,
# so that is what happens here, and ACAS_SEED_STRICT does not change it.
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
      # The maintainer's own message text, byte-exact from
      # [common/masterLD.sh:L58,L67,L76,L85], followed by `exit $rc' exactly as
      # [common/masterLD.sh:L59,L68,L77,L86].
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

  # The frozen test tolerates this code. Deviation D5: by default this harness
  # does not, because a partially loaded table silently poisons every subsequent
  # state diff and the diff is the only arbiter the migration has.
  if [[ "${ACAS_SEED_STRICT:-1}" == '0' ]]; then
    acas_summary_row "$loader" "$flat" 'yes' "$rc" 'ran (tolerated)'
    acas_warn "$loader returned $rc: $meaning. ACAS_SEED_STRICT=0, so the frozen >63-only tolerance applies [common/masterLD.sh:L41] and seeding continues -- the seeded state may be PARTIAL and any state diff taken from it is untrustworthy."
    return 0
  fi

  acas_summary_row "$loader" "$flat" 'yes' "$rc" 'ABORTED (strict)'
  printf 'FATAL: %s returned %s: %s\n' "$loader" "$rc" "$meaning" >&2
  acas_tee "FATAL: $loader returned $rc: $meaning"
  printf '       The frozen threshold would tolerate this code, because it is not\n' >&2
  printf '       greater than 63 [common/masterLD.sh:L41]. This harness treats it as\n' >&2
  printf '       fatal anyway (deviation D5): a partially loaded table cannot be\n' >&2
  printf '       distinguished from a behavioural difference once the states are\n' >&2
  printf '       diffed, so every conclusion drawn from this seed would be unsound.\n' >&2
  printf '       Export ACAS_SEED_STRICT=0 to restore the frozen tolerance exactly.\n' >&2
  printf '       Run harness/reset_db.sh before re-seeding.\n' >&2
  acas_seed_report
  exit "$rc"
}

# =============================================================================
# STAGE 1 -- THE SYSTEM-FILE BLOCK  [common/masterLD.sh:L50-L88]
#
# Frozen verbatim, in shape and in order:
#
#     JOBSTATUS=0
#     if [ -e system.dat ]; then
#         systemLD          ; rc=$? ; JOBSTATUS=$rc ; if [ $rc -gt 63 ] ...
#         sys4LD            ; rc=$? ; JOBSTATUS=$rc ; if [ $rc -gt 63 ] ...
#         finalLD           ; rc=$? ; JOBSTATUS=$rc ; if [ $rc -gt 63 ] ...
#         dfltLD            ; rc=$? ; JOBSTATUS=$rc ; if [ $rc != 0 ]  ...
#     fi
#
# and the reason the four run together, [common/masterLD.sh:L47-L48] verbatim:
# "First, process the five different records in the system file that are used to
# create five RDBMS tables holding only one record each."
# =============================================================================
acas_seed_system_block() {
  acas_stage 'Stage 1/2: the system file  [common/masterLD.sh:L50-L88]'

  # JOBSTATUS=0  [common/masterLD.sh:L50]
  ACAS_SEED_JOBSTATUS=0

  # if [ -e system.dat ]; then  [common/masterLD.sh:L51]
  # Existence, and nothing else. The frozen script performs no other check on a
  # flat file and neither does this one (R-3: no added validation).
  if [[ ! -e "$ACAS_SEED_SYSTEM_FLAT_FILE" ]]; then
    # Unreachable in practice, because acas_assert_system_dat already refused to
    # continue. Kept because the frozen guard is part of the contract being
    # reproduced, and because --data-dir could in principle be changed between
    # the assertion and here by a future edit.
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
    # [common/masterLD.sh:L54-L55,L63-L64,L72-L73,L81-L82]. So JOBSTATUS holds
    # the LAST loader's code, not the worst one; ACAS_SEED_WORST_RC is tracked
    # separately for the closing report, because the frozen variable on its own
    # would hide an earlier tolerated failure.
    ACAS_SEED_JOBSTATUS="$ACAS_SEED_LAST_RC"

    acas_abort_on_rc "$ACAS_SEED_LAST_RC" "$ACAS_S_LOADER" \
      "$ACAS_SEED_SYSTEM_FLAT_FILE" "$ACAS_S_TEST" "$ACAS_S_LOCATOR" 'system'
  done
}

# =============================================================================
# STAGE 2 -- THE FLAT-FILE MAPPINGS  [common/masterLD.sh:L93-L116]
#
# [common/masterLD.sh:L90-L91] verbatim: "Now for all the ACAS data files
# checking if each one exists before running the load program (for each)."
#
# The 16 in-scope mappings run in the frozen order. The 8 out-of-scope mappings
# are reported and never invoked (D7).
# =============================================================================
acas_seed_mappings() {
  acas_stage 'Stage 2/2: the flat-file mappings  [common/masterLD.sh:L93-L116]'

  local entry
  for entry in "${ACAS_SEED_MAPPINGS[@]}"; do
    acas_split_entry "$entry"

    # The frozen line, reproduced in valid shell (D1). The frozen text is, for
    # example, `if [ -e analysis.dat ];  then analLD fi' at
    # [common/masterLD.sh:L93] -- note the missing `;' before `fi', which is why
    # the frozen file cannot run and why it is not repaired.
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

# The 8 out-of-scope mappings. Never invoked; a present flat file is reported as
# a DELIBERATE skip, naming the table, so it is visible rather than silently
# ignored. Those tables are 8 of the 11 the frozen schema carries that the
# posting cycle never touches: STOCK-REC, STOCKAUDIT-REC, DELIVERY-REC,
# PUDELINV-REC, SADELINV-REC, SAAUTOGEN-REC, SAAUTOGEN-LINES-REC,
# PUAUTOGEN-REC, PUAUTOGEN-LINES-REC, PLPAY-REC and PLPAY-RECrg01.
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


# =============================================================================
# COMPLETION
# =============================================================================

# The frozen tail, [common/masterLD.sh:L119-L123] verbatim:
#
#     if [ -e SYS-DISPLAY.log ]; then
#        echo "All loads complete but check SYS-DISPLAY.log"
#        less SYS-DISPLAY.log
#        exit 0
#     fi
#
# Deviation D6, on two counts. `less' is an interactive pager and would block the
# harness for ever, so the log is written to standard output with `cat' instead:
# a prompt whose only effect is to pause a terminal is dropped, and a diagnostic
# with no database effect becomes a log record. And the frozen block exits 0 only
# when the log exists, falling off the end of the file with no explicit exit at
# all when it does not -- so this script always exits explicitly, and never
# unconditionally with 0.
#
# The log is NOT truncated between runs. The frozen loaders append to it and
# nothing in the frozen path clears it, so clearing it here would be a change to
# the seed path rather than a reproduction of it (R-4). It lives in the data
# directory, is never dumped and is never compared, so its growth cannot affect
# determinism.
acas_report_sysout_log() {
  if [[ ! -e "$ACAS_SEED_SYSOUT_LOG" ]]; then
    acas_log "no $ACAS_SEED_SYSOUT_LOG was produced in $PWD"
    return 0
  fi

  # The maintainer's own completion message, byte-exact from
  # [common/masterLD.sh:L120].
  printf '%s\n' "$ACAS_SEED_COMPLETE_MSG"
  acas_tee "$ACAS_SEED_COMPLETE_MSG"

  local bytes=0
  bytes="$(wc -c <"$ACAS_SEED_SYSOUT_LOG" 2>/dev/null | tr -d '[:space:]')"
  [[ "$bytes" =~ ^[0-9]+$ ]] || bytes=0
  acas_log "$ACAS_SEED_SYSOUT_LOG is ${bytes} byte(s), at $PWD/$ACAS_SEED_SYSOUT_LOG"
  acas_note 'the loaders APPEND to it, so it spans previous runs as well as this one'

  # 65536 bytes of diagnostics is already more than an operator will read in a
  # terminal; beyond that the tail is shown and the full file left in place.
  if (( bytes <= 65536 )); then
    printf -- '--- %s ---\n' "$ACAS_SEED_SYSOUT_LOG"
    cat -- "$ACAS_SEED_SYSOUT_LOG"
    printf -- '--- end of %s ---\n' "$ACAS_SEED_SYSOUT_LOG"
  else
    printf -- '--- last 200 lines of %s ---\n' "$ACAS_SEED_SYSOUT_LOG"
    tail -n 200 -- "$ACAS_SEED_SYSOUT_LOG"
    printf -- '--- end of tail; the whole file is at %s ---\n' "$PWD/$ACAS_SEED_SYSOUT_LOG"
  fi
}

# The closing report: the summary table, JOBSTATUS, and every non-fatal finding.
# Called on the success path and on every abort path, so a failed seed is just as
# fully accounted for as a clean one.
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
  # JOBSTATUS as the frozen script maintains it: the return code of the LAST
  # loader invoked. [common/masterLD.sh:L50,L55,L64,L73,L82]
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

# =============================================================================
# DRY RUN
# =============================================================================
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
  acas_log "strict mode  : ACAS_SEED_STRICT=${ACAS_SEED_STRICT:-1} (1 = return code 16 is fatal, deviation D5)"
  acas_note 'the MariaDB readiness and autocommit assertions are NOT performed in a'
  acas_note 'dry run; a real run refuses to seed unless autocommit is off, globally'
  acas_note 'and for the session [common/glbatchLD.cbl:L9-L13]'
}

# =============================================================================
# THE OPTIONAL SCENARIO POSITIONAL
#
# Accepted so the canonical eight-stage invocation at
# [harness/docker-compose.yml:L263-L274] works verbatim -- that file documents
# `harness/seed.sh "$S"' with S=harness/scenarios/<name>.yaml, alongside
# `harness/reset_db.sh "$S"'.
#
# It is NOT parsed. Two reasons, both deliberate. First, R-3 forbids adding
# validation the frozen script does not perform, and interpreting a scenario's
# declared contents against the flat files would be exactly that. Second, a
# scenario's inputs reach the loaders through the flat files it places in the
# data directory -- including the two SYSTEM-REC settings that are visible in
# every dump, Run-Date [copybooks/wssystem.cob:L67] and the three-state IRS
# fan-out switch [copybooks/wssystem.cob:L179-L181] -- so the scenario owns them
# through system.dat and this script has nothing to add.
# =============================================================================
acas_assert_scenario() {
  [[ -n "$ACAS_SEED_SCENARIO" ]] || return 0

  [[ -e "$ACAS_SEED_SCENARIO" ]] || acas_die "$EX_USAGE" \
    "the scenario file '$ACAS_SEED_SCENARIO' does not exist." \
    'The canonical invocation passes a path such as' \
    'harness/scenarios/clean_batch_gl.yaml [harness/docker-compose.yml:L263-L274].'
  [[ -f "$ACAS_SEED_SCENARIO" && -r "$ACAS_SEED_SCENARIO" ]] || acas_die "$EX_USAGE" \
    "the scenario '$ACAS_SEED_SCENARIO' is not a readable file."
}

# =============================================================================
# MAIN
#
# Strictly sequential (R-3). No stage is backgrounded and none is parallelised.
# Nothing here writes to $ACAS_REPO.
# =============================================================================
acas_main() {
  acas_parse_args "$@"

  printf 'harness/seed.sh -- seeding the frozen ACASDB schema from the ACAS Cobol flat files\n'
  printf 'reproducing the contract of common/masterLD.sh [common/masterLD.sh:L44-L115];\n'
  printf 'that script is NEVER executed -- its author marks it untested\n'
  printf '[common/masterLD.sh:L4-L5] and it is not valid shell (bash -n rejects it at\n'
  printf 'line 124). It is frozen and is not fixed.\n'

  acas_assert_environment
  acas_open_log
  acas_assert_scenario
  if [[ -n "$ACAS_SEED_SCENARIO" ]]; then
    acas_log "scenario = $ACAS_SEED_SCENARIO (recorded for traceability; not parsed)"
  fi
  acas_assert_data_dir
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

  acas_seed_system_block
  acas_seed_mappings
  acas_report_out_of_scope

  acas_stage 'Completion  [common/masterLD.sh:L119-L123]'
  acas_report_sysout_log
  acas_seed_report

  # Exit 0 ONLY on a genuinely clean seed. The frozen script exits 0
  # unconditionally when SYS-DISPLAY.log exists [common/masterLD.sh:L122] and
  # falls off the end with an accidental status when it does not; neither is
  # reproduced. If ACAS_SEED_STRICT=0 let a non-zero code through, the seed is
  # still not clean, so that code is reported here rather than hidden.
  if (( ACAS_SEED_WORST_RC != 0 )); then
    printf '\nharness/seed.sh completed with a non-zero load-program return code (%s).\n' \
      "$ACAS_SEED_WORST_RC" >&2
    printf 'The seeded state may be PARTIAL. Run harness/reset_db.sh before taking a diff.\n' >&2
    exit "$ACAS_SEED_WORST_RC"
  fi

  printf '\nharness/seed.sh completed: %s load program(s) ran, all returning 0.\n' "$ACAS_SEED_RAN"
  printf 'Next: harness/run_cobol_scenario.sh, then harness/dump_tables.py.\n'
  exit "$EX_OK"
}

acas_main "$@"

