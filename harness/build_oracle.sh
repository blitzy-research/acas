#!/usr/bin/env bash
# harness/build_oracle.sh
# The five-step bootstrap that builds the compiled-COBOL ORACLE for the ACAS
# posting-cycle migration: (1) unpack the vendored JC preSQL archive inside the
# container, (2) compile the bridge's C interface object cobmysqlapi.o with the
# build rule RECOVERED from that archive, (3) build and install the `presql2'
# translator onto the PATH, (4) run common/comp-common.sh UNMODIFIED, (5) run
# comp-all.sh UNMODIFIED. For the options, the environment and the exit codes,
# run `--help'.
# NOTATION. Backticked locators -- `presql2.cbl:L543', `cobmysqlapi38.sh' --
# name members of the vendored `presql2-latest.zip' unpacked in the container,
# never checkout paths; bracketed [path:Lnn] locators are checkout paths.

# WHAT THIS SCRIPT IS FOR
# The migration has no test suite. Compiled COBOL execution IS the behavioural
# specification, defects included, and this script is what makes that
# specification executable. If it does not work there is no arbiter, and every
# ambiguity in the migration becomes unresolvable.
# WHERE THIS FILE SITS
# harness/ is the compiled oracle and is a SIBLING of acas_posting/, never a
# sub-package. There is no import path from the shipped Python package to this
# tree, and this script never creates one: it writes no __init__.py, installs
# no import hook, and puts no artifact where acas_posting/ can reach it (R-1).
# Every product of the build lands under $ACAS_BUILD.

# THE FROZEN-ARTIFACT GUARANTEE
# The COBOL source, the bridge programs and the MySQL schema are frozen. This
# script READS $ACAS_REPO and NEVER writes to it -- not a .prn listing, not a
# .o, not a .so, not a .param, not a regenerated *MT.cbl, not an executable.
# It copies the tree into the writable $ACAS_BUILD and builds there. The reason
# is specific and severe: [common/comp-common.sh:L25] runs `presql2 $i' over
# every *MT.scb, and presql2 truncates its output with OPEN OUTPUT OUTPUT-FILE
# at `presql2.cbl:L543' BEFORE it validates parameters at `presql2.cbl:L759'.
# Run inside the checkout it would zero the 28 GENERATED common/*MT.cbl bridges
# -- the authoritative record-layout to table mapping, i.e. the data dictionary
# for this migration -- and it would do so even when merely misconfigured.

# THE FROZEN SCRIPTS ARE RUN UNMODIFIED
# common/comp-common.sh, comp-all.sh and the five per-directory scripts that
# comp-all.sh invokes [comp-all.sh:L15-L32] are executed exactly as written:
# not patched, sed-ed, re-implemented or reordered, and NO cobc flag changed.
# Default compiler arithmetic is mandatory: a census of every frozen compile
# invocation finds no -std= dialect selection, no >>SET ARITHMETIC directive
# and no binary-truncate flag, and the migration's truncation and rounding
# behaviour depends on exactly that.

# WHY `set -e' IS NOT ENOUGH -- READ THIS BEFORE CHANGING THE ERROR HANDLING
# Every frozen compile script ends with a bare, unconditional `exit 0':
# [common/comp-common.sh:L59], [comp-all.sh:L45], [general/comp-gl.sh:L7],
# [irs/comp-irs.sh:L9], [purchase/comp-purchase.sh:L6],
# [sales/comp-sales.sh:L22], [stock/comp-stock.sh:L7] -- in each case the last
# line of the file. Their exit status is therefore NOT a build-success signal,
# and neither `set -e' nor `pipefail' can catch a failed compile. These are
# frozen defects: worked around here, never fixed (R-4). What actually catches
# failure is (a) the two-tier log scan in acas_scan_build_log and (b) the
# artifact assertions in acas_assert_artifacts, which inspect the products
# rather than the prose and are the more reliable of the two. Both always run.

# RULES PROVENANCE
# There is no user rules document for this project: `review_rules' returns
# "No user rules provided." The binding rules R-1..R-6 come from the Agent
# Action Plan and are cited inline below as (R-n). Where they are silent this
# script holds to enterprise-standard best practice.
#   R-1 no COBOL at runtime          R-2 zero binary floating point
#   R-3 no schema change, sequential R-4 anomalies reproduced, never fixed
#   R-5 full traceability            R-6 compiled behaviour is the tie-breaker

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

# Exit codes -- one per stage, so an automated caller can attribute a failure
# without parsing text. 64/65 follow the sysexits.h convention.
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
# [common/comp-common.sh:L26] links `-L/usr/local/mysql/lib -lmysqlclient' and
# `cobmysqlapi38.sh' compiles with `-I/usr/local/mysql/include'.
# Both are LITERAL in the frozen sources, so this script uses the literal too
# and merely CHECKS that any ACAS_MYSQL_PREFIX published by the image agrees
# with it. Honouring a different prefix here would be a lie: the frozen scripts
# would still use /usr/local/mysql.
readonly ACAS_FROZEN_MYSQL_PREFIX='/usr/local/mysql'

# The compiler the maintainer targets, per [common/comp-common.sh:L8-L9]
# ("...the silly default warning in latest gnucobol v3.2") and [README.TXT:L53].
readonly ACAS_REQUIRED_COBC_VERSION='3.2'

# -----------------------------------------------------------------------------
# The vendored preSQL archive -- IDENTITY PIN.
#
# Step 1 unpacks $ACAS_REPO/presql2-latest.zip and steps 2 and 3 then compile C
# and COBOL out of it and INSTALL the result to /usr/local/bin. The archive is
# therefore executable input to a privileged step, and its identity decides what
# the oracle is. Two consequences, both mandatory:
#
#   1. The digest is pinned. The oracle is the behavioural specification for the
#      whole migration (R-6), so "whatever zip happens to be on disk" cannot be
#      allowed to redefine it. This value is the SHA-256 of the archive as
#      committed to this repository, measured with sha256sum; the archive holds
#      61 members under a single `presql2-package/' root.
#
#   2. Extraction is audited member by member -- see acas_extract_audited_zip.
#      An archive is an untrusted directory listing: a member named `../x' or
#      `/etc/x', or a symlink member pointing outside the scratch tree, writes
#      wherever the archive says rather than where this script says. `unzip -o'
#      and zipfile.extractall() are both unsuitable and neither is used.
#
# The same value is declared in harness/Dockerfile.gnucobol, which unpacks the
# same archive at image build time (ARG PRESQL2_SHA256); THE TWO MUST AGREE, and
# a disagreement between them is itself a finding.
#
# A maintainer replacing the archive sets ACAS_PRESQL2_SHA256 to the new digest.
# That is a deliberate, logged act: the override is announced as a warning, it
# is replayed in the closing summary, and the recorded expectation still appears
# in the log, so the evidence trail never silently loses the pin.
# -----------------------------------------------------------------------------
readonly ACAS_PRESQL2_SHA256_EXPECTED='638db9530d2fe008fbb46cf8600b9406f6f780c9fc59d0e0c94e868b4d615475'
readonly ACAS_PRESQL2_ARCHIVE_ROOT='presql2-package'

# -----------------------------------------------------------------------------
# Finite deadlines -- every external command this script spawns runs under one.
#
# The frozen build recipe can block indefinitely and does so for reasons that
# are entirely ordinary: `cobc' resolving a copybook over a stalled mount, the
# MariaDB client waiting on a TCP connection that is neither accepted nor
# refused, [common/comp-common.sh] itself reaching a prompt. An unbounded wait
# in a harness is worse than a failure, because a hung run yields no verdict at
# all -- and a protocol that cannot terminate cannot produce the empty-diff
# evidence the plan requires (R-6, AAP 0.8.5).
#
# Budgets are per-command wall-clock seconds, overridable by environment for a
# slower host, validated as integers >= 1, and reported in the failure message
# together with the variable that raises them. The grace period is the interval
# between the TERM that asks the child to stop and the KILL that makes it.
#
# Only the exact spawned child is signalled: `timeout' becomes the parent of
# that one process. Nothing here inspects a process table or matches on a
# command name, so no unrelated process on the host can be caught.
# -----------------------------------------------------------------------------
readonly ACAS_TIMEOUT_MAX=86400     # 24h -- an upper bound on any single budget
ACAS_TIMEOUT_GRACE="${ACAS_TIMEOUT_GRACE-}"               # resolved by acas_resolve_deadlines
ACAS_TIMEOUT_UNPACK="${ACAS_TIMEOUT_UNPACK-}"              # step 1: audit + extract the vendored zip
ACAS_TIMEOUT_COMPILE="${ACAS_TIMEOUT_COMPILE-}"             # a single gcc / cobc invocation
ACAS_TIMEOUT_BUILD="${ACAS_TIMEOUT_BUILD-}"               # a delegated frozen build script
ACAS_TIMEOUT_PROBE="${ACAS_TIMEOUT_PROBE-}"               # one database client probe attempt
ACAS_TIMEOUT_RESOLVED=''            # out-parameter of acas_timeout_seconds
declare -a ACAS_DEADLINE_ARGV=()    # populated by acas_deadline_prefix

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

# -----------------------------------------------------------------------------
# THE PINNED IDENTITY OF THE VENDORED preSQL ARCHIVE  (CWE-494 download of code
# without integrity check)
#
# presql2-latest.zip is not a passive data file. Step 1 unpacks it and steps 2
# and 3 then COMPILE AND EXECUTE what came out: cobmysqlapi38.c becomes the
# object every bridge, handler and loader links, and presql2.cbl becomes the
# translator that rewrites every *MT.scb. Whoever controls the bytes of this
# archive controls the whole oracle -- and therefore controls the values every
# scenario diff is measured against. An oracle built from a substituted archive
# would still produce a confident, empty diff.
#
# The archive lives in the read-only checkout, so this pin is not defending
# against a network fetch; it is defending against the checkout not being the
# checkout this harness was written for -- a bind mount pointed elsewhere, a
# tampered clone, or simply a different revision of the vendored package
# arriving silently. The digest is asserted BEFORE a single byte is extracted.
#
# The value is the SHA-256 of the archive as committed. It is also declared in
# harness/Dockerfile.gnucobol, which unpacks the same archive at image build
# time; THE TWO MUST AGREE, and a mismatch between them is itself a finding.
#
# ACAS_PRESQL2_SHA256 may override it, for the one legitimate case: the
# maintainer publishing a new vendored package. That is an explicit, auditable
# act -- not a silent default.
#
# The pin itself is ACAS_PRESQL2_SHA256_EXPECTED, declared once above with
# ACAS_PRESQL2_ARCHIVE_ROOT: one declaration, so the pin cannot be updated in
# one place and left stale in another.
# -----------------------------------------------------------------------------

# Mutable state. Declared up front because `set -u' makes an unset array a
# fatal reference.
# The client transports this target has earned, most secure first. Decided ONCE
# by acas_assert_transport_policy, before anything connects, and consumed
# read-only by acas_db_credentialed_probe -- see TRANSPORT SECURITY.
declare -a ACAS_BUILD_TLS_VARIANTS=()
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

# acas_die <exit-code> <message>...
# Every abort names the artifact or setting at fault and, wherever the cause is
# a frozen recipe, cites its locator so the claim is traceable to it (R-5).
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

# =============================================================================
# FINITE DEADLINES
#
# One definition of what "run this with a deadline" means, used by every call
# site that spawns an external process. Nothing in this script may block
# forever: see the rationale beside the ACAS_TIMEOUT_* declarations above.
# =============================================================================

# acas_timeout_seconds <env-var-name> <default>
# Resolve one budget from the environment, validating it as a positive integer
# no larger than ACAS_TIMEOUT_MAX. An unparsable or zero budget is a usage
# error and not a reason to fall back to "wait forever": a caller who asks for
# no deadline has asked for the defect this section exists to prevent.
#
# The resolved value is published in ACAS_TIMEOUT_RESOLVED rather than written to
# stdout, and the reason is the same hazard documented for acas_run_deadline: a
# caller writing `x="$(acas_timeout_seconds ...)"' would run this function in a
# command substitution, where acas_die's `exit' terminates only that subshell.
# The assignment would then swallow both the message and the status and the run
# would continue with an empty budget -- which is to say, with no deadline at
# all, silently. Returning through a variable keeps the abort real.
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
# malformed value is reported as a usage error at startup rather than hours into
# a build. Also asserts the one tool the whole mechanism depends on.
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

  # Belt and braces: nothing downstream may run with an unresolved budget, and a
  # missing one would degrade to "no deadline" -- the defect, not a fallback.
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
#
# The deadline itself -- TERM at the budget -- works everywhere and is what every
# real command in this script needs: gcc, cobc, python3, ldconfig and the MariaDB
# clients all terminate on TERM. The ESCALATION path matters for the two
# delegated frozen build scripts, whose own children (cobc) are what would
# actually be wedged.
#
# Measured difference between the two implementations in circulation:
#
#   GNU coreutils    -- sends TERM at the deadline, KILL after --kill-after, and
#                       returns as soon as its direct child is reaped. Correct.
#   uutils coreutils -- verified against 0.2.2: it reports 137 correctly but does
#                       not RETURN until the child's orphaned descendants have
#                       also exited, so a wedged grandchild can hold the run past
#                       the deadline.
#
# harness/Dockerfile.gnucobol is Ubuntu-based and provides GNU coreutils, so the
# documented execution environment is the correct one. A developer running this
# on a host with the Rust reimplementation gets a warning instead of a silent
# weakening -- which is the whole point of a harness. Non-fatal: refusing to
# build would be a worse outcome than reporting the exposure, and the warning is
# replayed in the closing summary so it cannot be scrolled past.
acas_verify_deadline_escalation() {
  local probe_budget=1 probe_grace=1 sleep_for=4 allowance_ms=3200
  local started_us ended_us elapsed_ms rc=0 raw

  raw="${EPOCHREALTIME-}"
  if [[ -z "$raw" ]]; then
    acas_note 'EPOCHREALTIME is unavailable; the deadline escalation self-test is skipped'
    return 0
  fi

  # EPOCHREALTIME is seconds.microseconds; removing the separator yields whole
  # microseconds as an integer. The comma form is accepted because the separator
  # follows LC_NUMERIC.
  raw="${raw/,/.}"
  started_us="${raw/./}"

  # stdio is detached so nothing about this probe can be confused with a build
  # diagnostic, and so an orphaned `sleep' holds no descriptor of ours.
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

# acas_deadline_prefix <budget>
# Populate ACAS_DEADLINE_ARGV with the invocation words that impose <budget> on
# whatever command words are appended to them. The single place in this script
# that knows the flag spelling, so a call site that must pipe its output (and
# therefore cannot delegate to acas_run_deadline) still gets identical
# semantics: TERM at the deadline, KILL after the grace period.
#
# `timeout' becomes the parent of exactly the process it is given. Only that one
# child is ever signalled -- this script never matches on a process name and
# never signals a process group, so no unrelated process can be caught.
acas_deadline_prefix() {
  ACAS_DEADLINE_ARGV=(
    timeout
    "--kill-after=$ACAS_TIMEOUT_GRACE"
    --signal=TERM
    "$1"
  )
}

# acas_is_timeout_status <rc> <elapsed> <budget>
# True when <rc> means "the deadline expired" rather than "the command ran and
# failed". Measured behaviour of the two implementations in play:
#
#   GNU coreutils   : 124 when the deadline expires; 125 means timeout ITSELF
#                     failed, which is not a deadline expiry.
#   uutils coreutils: 125 where GNU returns 124 (verified against 0.2.2).
#
# Because 125 is ambiguous across the two, status alone cannot decide it. The
# elapsed wall clock does: a command that consumed its whole budget and then
# failed timed out, whichever implementation reported it. 137 (128+9) is the
# escalation path -- the child ignored TERM and --kill-after sent KILL.
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
# it exceeded and the variable that raises it. Returns without comment for any
# other status: an ordinary failure is the CALLER's to report, because only the
# caller knows which stage exit code applies.
acas_assert_not_timed_out() {
  local rc="$1" elapsed="$2" budget="$3" budget_var="$4" label="$5" code="$6"

  if ! acas_is_timeout_status "$rc" "$elapsed" "$budget"; then
    return 0
  fi

  # The stage code is reported alongside EX_TIMEOUT rather than instead of it:
  # a caller distinguishing "the build failed" from "the build never finished"
  # needs the latter to be its own status, and a reader needs to know which
  # stage stalled.
  acas_die "$EX_TIMEOUT" \
    "$label exceeded its ${budget}s deadline (stage exit code would have been $code)." \
    "Raise $budget_var if this host is simply slower than the budget assumes;" \
    'investigate the command itself if it is genuinely stuck. The child was' \
    "sent TERM at the deadline and KILL ${ACAS_TIMEOUT_GRACE}s later."
}

# acas_run_deadline <budget> <budget-var> <label> <code> <workdir|-> -- cmd...
# Run one external command under its deadline and return the command's own exit
# status, having already aborted if the deadline expired.
#
# The optional working directory is handled here rather than by the caller
# wrapping the call in `( cd x && ... )'. That matters: acas_die inside a
# subshell would exit only the subshell, the caller's own `|| acas_die' would
# then fire, and the run would be attributed to the stage code instead of to
# EX_TIMEOUT. Here the cd is confined to a subshell but the VERDICT is reached
# in the function's own shell, so the abort is real.
acas_run_deadline() {
  local budget="$1" budget_var="$2" label="$3" code="$4" workdir="$5"
  shift 5
  [[ ${1:-} != '--' ]] || shift

  if [[ "$workdir" != '-' && ! -d "$workdir" ]]; then
    acas_die "$code" \
      "$label cannot run: its working directory $workdir does not exist."
  fi

  acas_deadline_prefix "$budget"

  local started rc=0 elapsed
  started="$SECONDS"
  if [[ "$workdir" == '-' ]]; then
    "${ACAS_DEADLINE_ARGV[@]}" "$@" || rc=$?
  else
    # `exec' so the subshell process BECOMES timeout: no extra shell survives to
    # be left behind when the deadline fires.
    ( cd "$workdir" && exec "${ACAS_DEADLINE_ARGV[@]}" "$@" ) || rc=$?
  fi
  elapsed=$(( SECONDS - started ))

  acas_assert_not_timed_out "$rc" "$elapsed" "$budget" "$budget_var" "$label" "$code"
  return "$rc"
}

# =============================================================================
# VENDORED ARCHIVE AUDIT
#
# See the ACAS_PRESQL2_SHA256_EXPECTED declaration for why an archive that feeds
# a compile-and-install step is treated as untrusted input with a pinned
# identity.
# =============================================================================

# acas_file_sha256 <path>
# sha256sum when present, python3 hashlib otherwise. python3 is already a hard
# requirement of this script (acas_assert_toolchain), so the fallback adds no
# new dependency and the digest check can never be skipped for want of a tool.
acas_file_sha256() {
  local path="$1" digest=''

  # Under a deadline like every other external command: the archive is read from
  # $ACAS_REPO, which is a bind mount in the Compose stack.
  acas_deadline_prefix "$ACAS_TIMEOUT_PROBE"

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

# acas_assert_archive_digest <path>
# Refuse to unpack an archive whose identity is not the pinned one, unless the
# maintainer has explicitly named a replacement digest. The override is a
# warning and is replayed in the closing summary, so a run that redefined the
# oracle's provenance cannot be mistaken for a run that did not.
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

# acas_extract_audited_zip <archive> <destination> <expected-root>
# Extract every member of <archive> beneath <destination>, having first audited
# the WHOLE member list. Nothing is written until every member has passed, so a
# rejected archive leaves no partial tree behind.
#
# Replaces `unzip -o' and zipfile.extractall(), neither of which is safe here:
# both honour the member names the archive supplies, so a member named `../x' or
# `/etc/x' escapes the destination, and a symlink member followed by a write
# through it escapes just as effectively. Python 3.12's extractall() sanitises
# absolute paths and `..', but it still MATERIALISES symlink members verbatim
# and reports nothing about what it changed -- neither acceptable for input to a
# privileged compile-and-install step.
#
# The audit and the extraction both live in python3 because zip member metadata
# (the type bits in external_attr, the create_system field) is not reachable
# from the shell. The archive path, destination and expected root arrive as argv
# and are never interpolated into the program text.
acas_extract_audited_zip() {
  local archive="$1" destination="$2" root="$3" rc=0

  # The heredoc is attached to the function call, so it is the stdin `python3 -'
  # reads through acas_run_deadline and on through timeout. Failure statuses are
  # the ones the program below documents.
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

# -----------------------------------------------------------------------------
# Re-exec guard -- SAFETY CRITICAL, do not remove.
#   1. bash reads a script file incrementally as it executes it. This script
#      copies $ACAS_REPO over $ACAS_BUILD, and $ACAS_BUILD/harness/ holds a
#      copy of THIS FILE. If the running instance is the one under
#      $ACAS_BUILD, `cp' truncates and rewrites the very file bash is reading
#      and execution can continue into rewritten bytes. Re-executing the
#      $ACAS_REPO copy -- read-only, never a copy target -- removes it.
#   2. Determinism (R-6). $ACAS_REPO is the specification; a copy left in a
#      build volume by an earlier run is not.
# harness/docker-compose.yml sets `working_dir: /build', so a plain
# `docker compose run ... harness/build_oracle.sh' resolves to $ACAS_BUILD --
# exactly the case this guard redirects. It is also why nothing here uses $0.
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
  # THE ONE DELIBERATE EXCEPTION to the finite-deadline rule, and it is not a
  # gap. `exec' REPLACES this process with the checkout's copy of this same
  # script, which then imposes its own per-command deadlines. Wrapping it in
  # `timeout' would instead bound the ENTIRE build to a single budget and leave
  # a supervisor process in the chain for the whole run. The re-exec itself
  # cannot block: it is a kernel execve of a local file whose existence was
  # asserted immediately above.
  exec bash "$repo_copy" "$@"
}

acas_reexec_from_repo_if_needed "$@"

# Traps.
# ERR reports the failing line so an unexpected failure is attributable.
# EXIT shreds every credential file this script wrote, on EVERY exit path
# including a fatal abort or an interrupt -- no password may survive the run.
# The three functions below are reached ONLY through the `trap' statements that
# follow them. ShellCheck's reachability pass cannot see an indirect invocation
# through a trap in a script that ends with an explicit `exit', so it reports
# their bodies as unreachable (SC2317) -- its own message says "or ignore if
# invoked indirectly", which is exactly the case here (SC2317 is ShellCheck
# 0.10.0's reachability diagnostic). The suppression is scoped to these three
# definitions and to nothing else.
# shellcheck disable=SC2317
acas_on_err() {
  local code="$1" line="$2" cmd="$3"
  printf '\nFATAL: unexpected failure at %s line %s (exit %s)\n' \
    "${BASH_SOURCE[0]}" "$line" "$code" >&2
  printf '       failing command: %s\n' "$cmd" >&2
}

# -----------------------------------------------------------------------------
# SAFE FILE CREATION  (CWE-59 symlink following, CWE-367 TOCTOU, CWE-732
# over-permissive files)
#
# presql2.param was written with a plain `> "$target"' and chmod'ed 0600
# afterwards. Both halves of that are wrong for a file that holds a database
# password in cleartext:
#
#   * `> "$target"' FOLLOWS a symlink and TRUNCATES its target. The file is
#     written into the build tree, which the Compose recipe makes a named volume;
#     anything able to place `presql2.param' there first chooses which file gets
#     overwritten AND then reads the password that lands in its place.
#   * chmod AFTER the write is too late. Between the create and the chmod the
#     file exists at whatever the umask allows -- the local `umask 077' narrowed
#     that window but did not close it, because a mode is a property of the
#     inode, not of the write.
#
# THE PATTERN, in four steps, each load-bearing, identical to the one
# harness/reset_db.sh, harness/seed.sh and harness/run_cobol_scenario.sh use
# (deliberately duplicated rather than sourced: the four scripts are independent
# entry points and none may fail because another is absent):
#
#   1. REFUSE a symlink outright. Bash has no O_NOFOLLOW, so this is an explicit
#      `-L' test. On its own it would be a TOCTOU window, which is why step 3
#      exists.
#   2. REMOVE an existing regular file, so step 3's exclusive create is not
#      defeated by our own previous run -- or by a param file the EXIT trap of an
#      earlier, killed run never got to shred.
#   3. CREATE under `set -C' (noclobber), which is O_EXCL: if anything appears at
#      the name between step 1 and here, the create FAILS rather than following
#      or truncating it.
#   4. chmod 600 on the EMPTY file, BEFORE any content is written, so the
#      password never exists on disk at a wider mode even momentarily.
# -----------------------------------------------------------------------------
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

# Usage
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
  ACAS_PRESQL2_SHA256=HEX    accept a REPLACEMENT presql2-latest.zip whose
                             SHA-256 is HEX instead of the digest pinned in this
                             script. Announced as a warning and replayed in the
                             closing summary: the archive decides what the
                             oracle is, so redefining it is never silent

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

Exit codes:
  0 success   64 usage   65 precondition   66 database   67 build tree
  71-75 steps 1-5   76 artifact assertions   77 finalisation
  78 an external command exceeded its deadline
  79 presql2-latest.zip failed its digest check or its member audit

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

# PRECONDITIONS
# This script ASSERTS its toolchain; it never installs one. harness/Dockerfile.
# gnucobol is what provides GnuCOBOL 3.2, the MySQL client libraries under the
# frozen prefix, the JC preSQL package and CPython 3.12. Asserting here means a
# misconfigured image fails in seconds with a named cause instead of failing
# minutes later inside a frozen script that reports success anyway.

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
  # THE RANGE, not merely the character class -- and here the consequence is
  # worse than a failed connection. atoi() has no error return
  # [presql2-package/cobmysqlapi38.c:L511], so a value outside the port range is
  # converted to whatever the platform's int truncation produces and handed
  # straight to mysql_real_connect. The build would then either fail with a cause
  # naming neither the variable nor the value, or -- worse -- succeed against a
  # DIFFERENT port than the operator specified.
  if (( 10#$ACAS_DB_PORT < 1 || 10#$ACAS_DB_PORT > 65535 )); then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_PORT must be between 1 and 65535; got '$ACAS_DB_PORT'." \
      'It is written verbatim into presql2.param and converted with atoi(), which' \
      'has no error return [presql2-package/cobmysqlapi38.c:L511], so an' \
      'out-of-range value becomes an arbitrary port rather than an error.'
  fi

  # Every card written into presql2.param is copied with strncpy(..., 32) at
  # `cobmysqlapi38.c:L138,L145,L152,L159,L166,L173' into a
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

  # Canonicalised AFTER the 32-character width check above, so an over-long value
  # is still rejected on width exactly as before. `10#' forces base-10 so a
  # leading zero is stripped rather than read as octal -- which matters here
  # because the value is written verbatim into presql2.param and then read by
  # atoi(), whose own base-10 interpretation would disagree with the shell's.
  ACAS_DB_PORT="$(( 10#$ACAS_DB_PORT ))"

  # Decided HERE, before anything connects, and not lazily on first use -- see
  # acas_assert_transport_policy for why the ordering matters.
  acas_assert_transport_policy

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
  # cannot be written even by accident. Assert the mount actually is read-only,
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
  # 0700, for the same reason harness/reset_db.sh, seed.sh and
  # run_cobol_scenario.sh all narrow their own output directories: the build
  # logs below are created no-follow, and a private directory means nothing can
  # unlink one of those names and leave a symlink in its place between the
  # create and the compiler's append. Best-effort by design -- if the directory
  # was not ours to change the create still refuses a link on its own, so this
  # is defence in depth and never the only guard.
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

  # cobc MUST be 3.2 -- the compiler the maintainer targets. A different release
  # is a different oracle, and the oracle is the specification.
  # [common/comp-common.sh:L8-L9] [README.TXT:L53]
  # Even an interrogation runs under a deadline. `cobc --version' loads the
  # runtime library, so a wedged NFS mount under COB_LIBRARY_PATH stalls it just
  # as readily as a real compile, and a preflight check that never returns is
  # the worst place of all to lose a run.
  local -a deadline=()
  acas_deadline_prefix "$ACAS_TIMEOUT_PROBE"
  deadline=("${ACAS_DEADLINE_ARGV[@]}")

  local cobc_line
  cobc_line="$("${deadline[@]}" cobc --version 2>&1 | head -n 1)"
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

  # The frozen prefix. These two paths are LITERAL in the frozen recipe, so they
  # are checked literally: [common/comp-common.sh:L26] links
  # -L/usr/local/mysql/lib -lmysqlclient and archive member
  # `cobmysqlapi38.sh' compiles with -I/usr/local/mysql/include.
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

# -----------------------------------------------------------------------------
# TRANSPORT SECURITY (CWE-295 improper certificate validation, CWE-319 cleartext
# transmission). Both credentialed probes searched, unconditionally:
#
#     local -a ssl_variant=('' '--skip-ssl')      <-- the defect, as it was
#
# so a server that merely declined TLS -- or a middlebox that stripped it --
# caused a SILENT downgrade to plaintext on the second iteration. Worse, the
# first iteration passed no --ssl-verify-server-cert either, so even the TLS
# attempt validated nothing: any certificate, from anyone, was accepted.
#
# THE POLICY, enforced by acas_assert_transport_policy and FAIL-CLOSED:
#
#   * A LOCAL target -- a unix socket, an empty host, or a loopback host -- may
#     use plaintext. Nothing leaves the machine, and it is the configuration the
#     harness actually uses: a current client enforces TLS while this server has
#     none, so --skip-ssl is REQUIRED there.
#   * A NON-LOCAL target must present a certificate chaining to $ACAS_DB_TLS_CA
#     and matching its hostname. That is what --ssl-verify-server-cert adds;
#     without a CA it verifies nothing, so the CA is required rather than optional.
#   * Plaintext to a non-local target is permitted ONLY when
#     ACAS_DB_ALLOW_PLAINTEXT explicitly declares the network isolated. The
#     accepted values are a CLOSED set, so a typo fails closed.
#   * Anything else is REFUSED before the first connection.
#
# A NOTE ON SCOPE, so this is not mistaken for more than it is: presql2 itself
# connects through the vendored C shim, which calls mysql_real_connect with no
# TLS options at all [presql2-package/cobmysqlapi38.c] -- that is FROZEN source
# and is not modified (R-3). This policy governs the probes THIS SCRIPT issues.
# For a non-local server the honest conclusion is therefore that the isolated
# network has to be declared explicitly, which is exactly what
# ACAS_DB_ALLOW_PLAINTEXT records -- as a deliberate, auditable statement instead
# of a silent fallback.
# -----------------------------------------------------------------------------

# True when the target is reachable without leaving the machine: a unix socket,
# an empty host, a loopback name, or a numeric loopback address. RESOLVES NOTHING
# about whether the server is trustworthy (R-6) -- it answers only "could this
# traffic be observed on a network".
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
# A CLOSED set of accepted spellings, so `ture' or `TRUE ' fails closed.
acas_plaintext_declared() {
  case "${ACAS_DB_ALLOW_PLAINTEXT-}" in
    1|true|yes|on) return 0 ;;
  esac
  return 1
}

# Decide, ONCE and BEFORE ANYTHING CONNECTS, which client transports this target
# has earned. Populates ACAS_BUILD_TLS_VARIANTS, most secure first, or aborts.
#
# Called from acas_assert_environment, and NOT lazily from the probe: a policy
# that is only evaluated when a connection is first attempted arrives AFTER the
# readiness wait, which can spend its whole timeout on an unreachable host before
# the refusal is ever reported. The operator would then be told "MariaDB never
# became reachable" when the truth is "this script refuses to talk to it that way".
acas_assert_transport_policy() {
  local ca="${ACAS_DB_TLS_CA-}"
  ACAS_BUILD_TLS_VARIANTS=()

  if [[ -n "$ca" ]]; then
    [[ -r "$ca" ]] || acas_die "$EX_PRECONDITION" \
      "ACAS_DB_TLS_CA names a file that cannot be read: $ca" \
      'It must be the PEM bundle the server certificate chains to.'
    # --ssl-verify-server-cert is what makes the CA meaningful: without it the
    # client encrypts but accepts any certificate, which is CWE-295 with extra
    # steps.
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
      "the target ${ACAS_DB_HOST}:${ACAS_DB_PORT} is not local and no verified TLS is configured." \
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
  # connects, so `int(sys.argv[2])' here can no longer receive 99999 and fail with
  # an OverflowError that names neither the variable nor the value. The range is
  # re-checked in the probe itself because a defence that only exists at one entry
  # point is one refactor away from not existing.
  #
  # An EXTERNAL deadline as well as the socket timeout below, because the two
  # bound different things: create_connection's timeout covers the connect, but
  # NOT the getaddrinfo() that precedes it. A host name served by an
  # unresponsive resolver would block in name resolution with the socket timeout
  # never reached.
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

# A genuinely credentialed probe -- this is what presql2 will actually need.
# WHY THIS IS NOT A `ping': `mariadb-admin ping' ANSWERS "IS THE SERVER ALIVE",
# NOT "ARE THESE CREDENTIALS ACCEPTED", so it exits 0 even when authentication
# is refused -- it prints `error: 'Access denied for user ...'' on stderr and
# still succeeds -- a refusal only comes from a server that is up. Used as a
# readiness gate it would let a wrong password through, to resurface much later
# as one presql2 diagnostic per bridge inside step 4. `status' and a real
# `select 1' both exit 1 instead. Therefore: prefer a real authenticated
# statement; fall back to `status', never to `ping'.
# The statement runs against the schema presql2 itself connects to
# (information_schema by default -- see acas_write_presql2_param and
# `presql2.cbl:L798-L806'), so a grant excluding it is caught here, not later.

# The password goes through MYSQL_PWD rather than argv so it never appears in
# the process list. Both a TLS-enforcing client (which needs --skip-ssl against
# a server without TLS) and a permissive one are tolerated.
# Returns: 0 authenticated, 1 transient failure (retry), 2 credentials rejected
# (a configuration error), 3 no client binary available.
# Side effect: sets ACAS_DB_PROBE_DIAG to the client's last diagnostic.
acas_db_credentialed_probe() {
  ACAS_DB_PROBE_DIAG=''
  local dbname="${ACAS_PRESQL2_DBNAME:-information_schema}"
  local client out rc started elapsed

  # EVERY client invocation below runs under ACAS_TIMEOUT_PROBE. A client that
  # neither connects nor is refused -- a dropped packet filter is the usual
  # cause -- would otherwise block this probe, and with it the readiness gate,
  # indefinitely. A probe that exceeds its own deadline is reported as the
  # transient failure it is (return 1) rather than as a fatal error: the caller,
  # acas_wait_for_database, owns the OVERALL bound and retries until
  # ACAS_DB_WAIT_TIMEOUT is spent.
  local -a deadline=()
  acas_deadline_prefix "$ACAS_TIMEOUT_PROBE"
  deadline=("${ACAS_DEADLINE_ARGV[@]}")

  # Unreachable unless acas_assert_transport_policy was skipped or changed: it
  # either records at least one permitted variant or aborts with a named cause.
  # Asserted rather than assumed, because an empty list would otherwise fall
  # straight through both layers and return 3 -- "no client binary available" --
  # which would send the operator looking for a missing package.
  if (( ${#ACAS_BUILD_TLS_VARIANTS[@]} == 0 )); then
    acas_die "$EX_PRECONDITION" \
      'no permitted client transport for this target.' \
      'acas_assert_transport_policy must run before any probe; see TRANSPORT' \
      'SECURITY.'
  fi

  # Layer 1: a real SQL client executing a real statement.
  for client in mariadb mysql; do
    if acas_have "$client"; then
      # The PERMITTED variants, decided by policy before anything connected -- not
      # the unconditional ('' '--skip-ssl') pair this used to be. Every variant
      # runs under the probe deadline resolved above.
      local variant flag
      for variant in "${ACAS_BUILD_TLS_VARIANTS[@]}"; do
        local -a argv=("${deadline[@]}" "$client" '--protocol=TCP')
        if [[ -n "$variant" ]]; then
          # A variant may carry two words (--ssl-ca=... --ssl-verify-server-cert),
          # so it is split deliberately -- each flag must be its own argv element.
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
        out="$(MYSQL_PWD="$ACAS_DB_PASSWORD" "${argv[@]}" 2>&1)" || rc=$?
        elapsed=$(( SECONDS - started ))
        if (( rc == 0 )); then
          return 0
        fi
        if acas_is_timeout_status "$rc" "$elapsed" "$ACAS_TIMEOUT_PROBE"; then
          out="$client did not answer within ${ACAS_TIMEOUT_PROBE}s and was terminated (raise ACAS_TIMEOUT_PROBE). ${out}"
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
        out="$(MYSQL_PWD="$ACAS_DB_PASSWORD" "${argv[@]}" 2>&1)" || rc=$?
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
  # MySQL_real_connect at `cobmysqlapi38.c:L500-L531'. presql2 runs inside
  # step 4 via [common/comp-common.sh:L25], so it must be up BEFORE step 4 or
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
  # `cobmysqlapi38.c:L114-L176', so a wrong user or password must be caught
  # HERE, not one diagnostic per bridge into step 4.
  # Two failure shapes, deliberately treated differently:
  #   - transient (connection reset, server still initialising): retried for
  #     the full ACAS_DB_WAIT_TIMEOUT, because the port often opens before the
  #     server will talk.
  #   - "Access denied" (a configuration error, not a readiness state): retried
  #     only for a short grace window, because no wait fixes a wrong password.
  #     The window exists solely to absorb the narrow race in which
  #     grants are still being applied.
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

# BUILD TREE -- DEVIATION 1 of 6: the compile runs in $ACAS_BUILD, not where
# the frozen scripts live. Not a preference but a hard requirement:
# [common/comp-common.sh:L25] is
#     for i in `ls *MT.scb`; do presql2 $i; ... done
# which REGENERATES every common/*MT.cbl in whatever directory it runs in.
# Those 28, one per *MT.scb, are the committed, frozen files AAP 0.8.2 calls
# "the authoritative record-layout <-> table mapping ... the data dictionary
# for this migration". Worse, presql2 TRUNCATES its output before validating
# parameters -- `presql2.cbl:L543' precedes `presql2.cbl:L759' -- so a mere
# misconfiguration inside the checkout would zero all 28. Four further writes
# make the point too: .prn listings, six copies of cobmysqlapi.o,
# presql2.param, and every .so or executable cobc emits.

# The WHOLE checkout is copied, and that is the safe choice: the frozen
# scripts navigate with relative paths -- `-I ../copybooks' in every compile,
# `cd common' / `cd ../general' [comp-all.sh:L15-L32] -- so the copy must
# preserve the tree layout exactly. Excluding directories to save space
# (ACAS-Manuals/, Basic-Code/, payroll/, home/, .git/) works against the
# frozen scripts as they stand but would break silently the moment one grew a
# reference, and the cost is a few hundred megabytes on a container volume.
# The faithful replica is worth more than the disk.

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
    #
    # Both bulk operations run under ACAS_TIMEOUT_BUILD. $ACAS_BUILD is a mount
    # point in the Compose stack, so a wedged volume would otherwise stall the
    # clear or the copy indefinitely -- before a single stage banner is printed.
    acas_run_deadline "$ACAS_TIMEOUT_BUILD" ACAS_TIMEOUT_BUILD \
      "clearing $ACAS_BUILD" "$EX_BUILDTREE" - \
      -- find "$ACAS_BUILD" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + \
      || acas_die "$EX_BUILDTREE" "could not clear $ACAS_BUILD."

    acas_log "copying $ACAS_REPO into $ACAS_BUILD (whole tree, layout preserved)"
    acas_run_deadline "$ACAS_TIMEOUT_BUILD" ACAS_TIMEOUT_BUILD \
      "copying $ACAS_REPO into $ACAS_BUILD" "$EX_BUILDTREE" - \
      -- cp -a "$ACAS_REPO/." "$ACAS_BUILD/" \
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

# COPY-closure advisory.
# A precise, zero-false-positive check that every copybook the frozen build
# needs can be resolved. It exists because there is a real source-level gap:
# copybooks/ACAS-SQLstate-error-list.cob is COPY'd by 22 of the 28 GENERATED
# bridges and is ABSENT from the frozen archive. Without this advisory that
# gap surfaces minutes later as 22 apparently unrelated compile errors inside
# a script that then reports success anyway.
# It is an ADVISORY, not a gate: the missing copybook is a frozen-archive
# defect and must be supplied by the maintainer, never fabricated (R-3, R-4).
# The build is still attempted so that the log scan and the artifact assertions
# report exactly which bridges are affected.

# Precision notes:
#   * only quoted COPY targets count, and only on lines with no `*' or `/'
#     before the keyword, which excludes fixed-format comment lines (`*' in
#     column 7) and inline `*>' comments;
#   * a target resolves against copybooks/ AND the program's own directory,
#     because cobc searches the current directory as well as `-I ../copybooks';
#   * the bare name and GnuCOBOL's usual copybook extensions are all tried,
#     because sources use both `copy "wsdnos".' and `copy "wsbatch.cob".';
#   * only the source sets the frozen scripts actually compile are scanned,
#     so a copybook needed solely by a program no compile script builds --
#     common/acasconvert3.cbl is the real example -- is correctly ignored.
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

# STEP 1/5 -- unpack the vendored JC preSQL archive
# The vendored archives are harness build inputs: unpacked INSIDE the container
# and never modified in the checkout. presql2-latest.zip holds 61 entries and
# expands to a presql2-package/ directory carrying cobmysqlapi38.c and .sh,
# presql2.cbl and .sh, bldcopy2.*, prtschema2.*, the MYSQL-*.CPY copybooks, the
# example .param files, and the ACAS/, Variations/ and old-apis/ subdirectories.
# =============================================================================
# The digest of this archive is asserted BEFORE a single byte is extracted, by
# acas_assert_archive_digest -- defined once in VENDORED ARCHIVE AUDIT above,
# alongside acas_file_sha256 and acas_extract_audited_zip, so that the pin, the
# digest computation and the member audit cannot drift apart. sha256sum is
# preferred there and python3's hashlib is the fallback, so the check cannot be
# skipped merely because coreutils is minimal: a digest check that quietly does
# nothing is worse than none, because it reports confidence it does not have.

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
    # archive itself is never touched: it is read out of the read-only checkout.
    local scratch="$ACAS_BUILD/.acas-presql2"
    rm -rf -- "$scratch"
    mkdir -p "$scratch"
    ACAS_SCRATCH_DIRS+=("$scratch")

    # EXTRACTED UNDER A MEMBER POLICY, NOT WITH `unzip -o' OR `extractall'.
    #
    # Identity was asserted above; this is the member-by-member audit that must
    # follow it. Both of the calls this replaces trusted every member name in
    # the archive. A zip entry may legitimately be named `../../etc/whatever' or
    # `/etc/whatever', may be a symlink whose target is followed on the NEXT
    # extraction, and may be a device or fifo entry -- and `unzip -o'
    # additionally OVERWRITES without asking. Because steps 2 and 3 then compile
    # C and COBOL out of what came out and install the result to
    # /usr/local/bin, a traversal here is not merely a stray file: it is
    # arbitrary content placed anywhere this process can write, in a tree whose
    # products define the oracle -- and the oracle is the behavioural
    # specification for the whole migration. The digest assertion above makes
    # this defence redundant for the committed archive; it is kept because
    # ACAS_PRESQL2_SHA256 can legitimately point the digest at a NEW package,
    # and the member policy is what makes that override safe rather than merely
    # explicit.
    #
    # `unzip' is not used at all -- it has no portable way to refuse a hostile
    # member -- and neither is zipfile.extractall(), which still materialises
    # symlink members verbatim. acas_extract_audited_zip judges every name
    # before a single byte is written, so a rejected archive leaves no partial
    # tree behind, and it runs under a finite deadline.
    acas_extract_audited_zip "$archive" "$scratch" "$ACAS_PRESQL2_ARCHIVE_ROOT"

    [[ -d "$scratch/$ACAS_PRESQL2_ARCHIVE_ROOT" ]] || acas_die "$EX_STEP1" \
      "$ACAS_PRESQL2_ARCHIVE_ROOT/ was not found inside $archive." \
      'The archive layout is not as expected.'
    ACAS_PRESQL2_DIR="$scratch/$ACAS_PRESQL2_ARCHIVE_ROOT"
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

# STEP 2/5 -- the RECOVERED build rule for the bridge's C interface object
# `find . -name cobmysqlapi*' over the whole ACAS checkout returns nothing: no
# object, no C source, and NO RULE ANYWHERE THAT BUILDS IT. Yet every
# RDBMS-touching compile links a bare `cobmysqlapi.o':
# [common/comp-common.sh:L26] (bridges), :L32 (handlers), :L34 (IRS handlers),
# :L36 (acas-get-params), :L40-L42 (fhlogger, xl150, sys002), :L45 (ACAS.cbl),
# :L51 (loaders), and every per-directory script -- [general/comp-gl.sh:L2],
# [irs/comp-irs.sh:L2], [purchase/comp-purchase.sh:L2],
# [sales/comp-sales.sh:L7], [stock/comp-stock.sh:L2]. Following the compile
# scripts alone, the oracle cannot be built at all.

# The rule was recovered from the vendored package. Verbatim, and the whole of
# archive member `cobmysqlapi38.sh':
#     gcc -I/usr/local/mysql/include -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC
# cobmysqlapi38.c ONLY. The superseded variants must not be used:
# `old-apis/cobmysqlapi.sh' is `gcc -I/usr/include/mysql -c cobmysqlapi.005.c'
# and `old-apis/cobmysqlapi3.sh' is
# `gcc -I/usr/include/mysql -c cobmysqlapi3.c -o cobmysqlapi.o' -- a DIFFERENT
# include path and, decisively, NO -fPIC, so neither can be linked into the
# `cobc -m' shared modules the frozen scripts build.
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
    acas_run_deadline "$ACAS_TIMEOUT_COMPILE" ACAS_TIMEOUT_COMPILE \
      'compiling cobmysqlapi38.c' "$EX_STEP2" "$workdir" \
      -- gcc -I/usr/local/mysql/include -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC \
      || acas_die "$EX_STEP2" \
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
  # $ACAS_BUILD is a mount point in the Compose stack, so even a small write into
  # it is bounded: a wedged volume must fail this stage, not stall it.
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

# STEP 3/5 -- build and install the presql2 translator
# Verbatim, and the whole of archive member `presql2.sh':
#     cobc -x presql2.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz
# [common/comp-common.sh:L25] invokes `presql2' by name over every *MT.scb, so
# it must be on the PATH before step 4.
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
    # `env' carries the two copybook variables: it EXECS cobc, so the process
    # timeout supervises is cobc itself and nothing extra survives a deadline.
    acas_run_deadline "$ACAS_TIMEOUT_COMPILE" ACAS_TIMEOUT_COMPILE \
      'building presql2' "$EX_STEP3" "$workdir" \
      -- env "COBCPY=$workdir" "COB_COPY_DIR=$workdir" \
         cobc -x presql2.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz \
      || acas_die "$EX_STEP3" \
      'building presql2 failed.' \
      '[common/comp-common.sh:L25] cannot translate any *MT.scb without it.'

    [[ -s "$workdir/presql2" ]] || acas_die "$EX_STEP3" \
      "cobc reported success but $workdir/presql2 was not produced." \
      '[presql2-package/presql2.sh]'
    acas_run_deadline "$ACAS_TIMEOUT_PROBE" ACAS_TIMEOUT_PROBE \
      'installing presql2' "$EX_STEP3" - \
      -- install -m 0755 "$workdir/presql2" /usr/local/bin/presql2 \
      || acas_die "$EX_STEP3" \
      'could not install presql2 into /usr/local/bin.' \
      'Root privileges are required, or place it on the PATH yourself.'
    acas_log 'installed /usr/local/bin/presql2'

    # bldcopy2 is built for completeness. Note the SPACE after -L, which is how
    # archive member `bldcopy2.sh' is written, and that it links WITHOUT -lz.
    # No frozen ACAS script invokes bldcopy2, so a failure here cannot block the
    # oracle and is reported rather than fatal.
    if [[ -f "$ACAS_PRESQL2_DIR/bldcopy2.cbl" ]] && ! acas_have bldcopy2; then
      cp -p "$ACAS_PRESQL2_DIR/bldcopy2.cbl" "$workdir/"
      acas_log 'running the vendored rule verbatim [presql2-package/bldcopy2.sh]:'
      acas_log '  cobc -x bldcopy2.cbl cobmysqlapi.o -L /usr/local/mysql/lib -lmysqlclient'
      # The deadline is imposed with acas_deadline_prefix rather than with
      # acas_run_deadline because THIS site must stay non-fatal: a stuck
      # bldcopy2 build is killed at the deadline and downgraded to a warning,
      # so it can neither hang the harness nor block an oracle that does not
      # depend on it. Every other compile in this script is fatal on timeout.
      local bldcopy_rc=0 bldcopy_started bldcopy_elapsed
      acas_deadline_prefix "$ACAS_TIMEOUT_COMPILE"
      bldcopy_started="$SECONDS"
      (
        cd "$workdir" \
          && exec "${ACAS_DEADLINE_ARGV[@]}" \
               env "COBCPY=$workdir" "COB_COPY_DIR=$workdir" \
               cobc -x bldcopy2.cbl cobmysqlapi.o -L /usr/local/mysql/lib -lmysqlclient
      ) || bldcopy_rc=$?
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
  # prtschema2 is NOT built. The archive ships no prtschema2.cbl, so its own
  # rule `prtschema2.sh:L1' has to generate it by RUNNING presql2 -- which
  # would need a second credential
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

# Toolchain link proof.
# Reproduces the vendored worked example `ACAS/comp-stockMT.sh'
# verbatim in a scratch directory:
#     cobc -m stockMT.COB cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz
# A real generated ACAS bridge, compiled exactly as ACAS compiles its own. A
# clean link here exercises the entire COBOL-to-MySQL toolchain before a single
# frozen script runs, and a missing or wrong cobmysqlapi.o is precisely the
# failure it catches -- the failure that is otherwise reported as an
# unattributable link error minutes into step 4.
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
  acas_run_deadline "$ACAS_TIMEOUT_COMPILE" ACAS_TIMEOUT_COMPILE \
    'the vendored worked example (stockMT)' "$EX_STEP3" "$proof" \
    -- env "COBCPY=$proof" "COB_COPY_DIR=$proof" \
       cobc -m stockMT.COB cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz \
    || acas_die "$EX_STEP3" \
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

# presql2.param -- the credential file the translator requires and the checkout
#                  does not contain
# read_params() in the recovered C shim, declared at `cobmysqlapi38.c:L114',
# derives its filename from the calling program's name -- sprintf(zwi2,
# "%s.param", zwi) at :L126 -- and opens it RELATIVE TO THE CURRENT DIRECTORY
# at :L127. When the file is absent it prints "Could not read file
# >presql2.param<, aborting..." and calls exit(5) at :L129-L130. It then reads
# exactly SIX cards and prefix-validates each in this order, exit(6) on any
# mismatch:
#   DBHOST=    :L134-L137      DBNAME=    :L155-L158
#   DBUSER=    :L141-L144      DBPORT=    :L162-L165
#   DBPASSWD=  :L148-L151      DBSOCKET=  :L169-L172

# presql2.cbl reads it at `presql2.cbl:L759-L773' and states the requirement in
# its own prologue at :L55 ("This filename MUST be presql2.param"). NO *.param
# file exists anywhere in the ACAS checkout, so one must be materialised, and
# in the directory presql2 runs in -- $ACAS_BUILD/common, because
# [common/comp-common.sh:L25] runs there. DEVIATION 2 of 6 -- presql2.param is
# a NEW file the frozen recipe never creates. Unavoidable: no *.param exists
# anywhere in the checkout, yet read_params aborts with exit(5) without one. It
# is written only into the writable build tree, never the checkout, and is
# shredded on exit.

# DEVIATION 3 of 6 -- WHY DBNAME IS information_schema, NOT $ACAS_DB_NAME.
# presql2 builds its metadata query at `presql2.cbl:L798-L806' as "SELECT
# COLUMN_NAME, DATA_TYPE, ... FROM COLUMNS WHERE TABLE_SCHEMA=..." -- and `FROM
# COLUMNS' is UNQUALIFIED. The connected schema must therefore be the one that
# owns COLUMNS, i.e. information_schema, and presql2 queries it LIVE. The
# schema actually being described arrives separately, from each bridge's own
# BASE= directive (BASE=ACASDB, e.g. [common/glpostingMT.scb:L273-L276]), and
# is substituted into TABLE_SCHEMA. The vendored example agrees:
# `presql2.param' line 4 is DBNAME=information_schema. ACAS_PRESQL2_DBNAME can
# override this for experimentation; the default is the value the source
# requires.

# DEVIATION 4 of 6 -- an EMPTY ACAS_DB_SOCKET is written as the literal
# DBSOCKET=NULL rather than as an empty value. MySQL_real_connect at
# `cobmysqlapi38.c:L513-L525' maps unix_socket to NULL only for the literals
# "0", "null" and "NULL"; an empty string is passed through as "" and defeats
# the TCP connection. harness/docker-compose.yml sets ACAS_DB_SOCKET: "", so
# this translation is what makes the Compose default work. CREDENTIAL HYGIENE.
# Written under umask 077, chmod 0600 explicitly, never echoed, never passed in
# argv, and shredded then unlinked by the EXIT trap on every exit path. Every
# value is a PLACEHOLDER supplied from the environment; no real credential is
# committed anywhere in this tree.
acas_write_presql2_param() {
  local dir="$1"
  local prog="${2:-presql2}"
  local target="$dir/$prog.param"

  [[ -d "$dir" ]] || acas_die "$EX_STEP4" \
    "$dir does not exist, so $prog.param cannot be written there."

  local dbname="${ACAS_PRESQL2_DBNAME:-information_schema}"

  # An EMPTY socket is written as the literal NULL. MySQL_real_connect maps
  # unix_socket to NULL only for the exact strings "0", "null" and "NULL"
  # `cobmysqlapi38.c:L513-L525'; an empty string is passed
  # through as an empty socket path, which is not the same thing. NULL is the
  # only unambiguous spelling of "connect over TCP, there is no socket", and
  # harness/docker-compose.yml sets ACAS_DB_SOCKET to the empty string on
  # purpose. A non-empty value is written verbatim.
  local socket="${ACAS_DB_SOCKET-}"
  if [[ -z "$socket" ]]; then
    socket='NULL'
  fi

  # CREATED EMPTY, EXCLUSIVELY, AND CHMOD'ED 0600 BEFORE THE PASSWORD IS WRITTEN.
  #
  # This replaces `> "$target"' followed by a chmod. Two things were wrong with
  # that and only one of them was the mode: `>' also FOLLOWS a symlink and
  # TRUNCATES its target, so anything able to create `presql2.param' in the build
  # tree first both chose the victim and then read the password. The local
  # `umask 077' narrowed the mode window but could not close it -- a mode is a
  # property of the inode, not of the write -- and it did nothing at all about the
  # symlink. See SAFE FILE CREATION for the four steps.
  #
  # THE FILE IS REGISTERED FOR SHREDDING IMMEDIATELY AFTER THE CREATE AND BEFORE
  # THE CONTENT IS WRITTEN. If the write fails half way, the EXIT trap must still
  # find the file and shred it; registering afterwards would leave a partially
  # written credential on disk on exactly the path where something went wrong.
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

  # LF endings are correct: cobapi_read_line stops at '\n' or EOF and discards
  # '\r' `cobmysqlapi38.c:L77-L93'.
  acas_log "wrote $target (0600, six cards in the order read_params requires)"
  acas_log "  DBHOST=${ACAS_DB_HOST}  DBUSER=${ACAS_DB_USER}  DBPASSWD=<redacted>"
  acas_log "  DBNAME=${dbname}  DBPORT=${ACAS_DB_PORT}  DBSOCKET=${socket}"
  acas_note 'it is shredded and unlinked by the EXIT trap, on every exit path'
}

# LOG SCANNING -- the workaround for the unconditional `exit 0'
# Every frozen compile script ends `exit 0' unconditionally (see the header),
# so their exit status carries no information. This scan is one of the two
# mechanisms that actually detect failure; the artifact assertions are the
# other, and are more reliable because they inspect the products rather than
# the prose. Both always run.
# THE CLASSIFICATION, stated so a reviewer can audit it:
#   BENIGN  -- excluded from the counts, but the number excluded is REPORTED so
#              nothing is hidden. Exactly one family qualifies: "warning:
#              '_FORTIFY_SOURCE' redefined" and its companion "note: this is
#              the location of the previous definition", one pair per compile.
#              They come from the C compiler, not cobc, and say nothing about

#              the artifact produced: the frozen scripts pass
#              -D_FORTIFY_SOURCE=1 ([general/comp-gl.sh:L2] and its siblings)
#              on a toolchain that already defines it.
#   FATAL   -- always fails the build: cobc and gcc diagnostics, linker
#              failures, missing files, crashes, and the two exit paths of the
#              preSQL credential reader. The patterns are colon-anchored
#              (`error:', `warning:') for a specific reason: the frozen scripts
#              themselves print "check for any error or warning messages"
#              ([comp-all.sh:L44]), which must not be read as a diagnostic. The
#              end-of-group summary is matched as `[1-9][0-9]* error' so that
#              "0 errors" never matches.

#              `No such file or directory' is matched WITHOUT a colon anchor,
#              because a missing cobmysqlapi.o produces "prog.cbl: cobc:
#              cobmysqlapi.o: No such file or directory" with no `error:' token
#              at all -- and that is the single most important failure this
#              script must catch.
#   WARNING -- reported with a count and the full text, and fatal only when
#              ACAS_BUILD_STRICT=1. -Wlinkage is used deliberately by the
#              maintainer at [common/comp-common.sh:L26] and throughout, and
#              this codebase does produce diagnostics, so warnings are neither
#              silently accepted nor silently fatal. The warnings that DO

#              indicate a missing artifact -- `undefined reference', `cannot
#              find -l' -- are classified FATAL above, which is what makes the
#              default safe.
# DO NOT "IMPROVE" THIS BY SCANNING THE .prn LISTINGS -- IT IS A TRAP.
#   The frozen scripts pass `-T <name>.prn' to every compile, and each listing
#   ends with an authoritative-looking "N errors in compilation group". That is
#   not trustworthy on its own: when a compile fails because a COPY target is
#   missing, cobc aborts BEFORE refreshing the listing, so a STALE listing from
#   an earlier run survives and still claims "0 errors" for a bridge that
#   produced no module at all.

#   With copybooks/ACAS-SQLstate-error-list.cob absent, that is exactly what
#   analMT, auditMT and glpostingMT do. A semantic error, by contrast, DOES
#   reach the listing. So the listing is a COMPLEMENT at best and misleading at
#   worst. The two signals this script relies on -- this scan, which catches
#   the abort-before-listing class, and the artifact assertions, which inspect
#   the products -- cover both classes without ever trusting a listing. If the
#   summary line does reach the console it is caught anyway by FATAL above.
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

# STEP 4/5 -- run common/comp-common.sh UNMODIFIED
# What it does, in its own order, so the expected output is known:
#   L18  cobc -m accept_numeric.c -lncursesw -A '-DHAVE_NCURSESW_NCURSES_H
#        -DDECIMAL_RIGHT'   (needs the wide-character ncurses headers)
#   L21  dummy-rdbmsMT.cbl        L23  ACAS-Sysout.cbl
#   L25  presql2 over every *MT.scb -- REGENERATES *MT.cbl in the build copy,
#        harmless there and catastrophic in the checkout
#   L26  every *MT.cbl as a module, linking cobmysqlapi.o
#   L29  maps0*.cbl (no cobmysqlapi.o)      L32  acas0*.cbl
#   L34  acasirsub*.cbl                     L36  acas-get-params
#   L40-L42  fhlogger, xl150, sys002        L45  cobc -x ACAS.cbl
#   L51  all 28 *LD.cbl as executables -- what harness/seed.sh invokes

#   L54  *UNL.cbl      L57  *RES.cbl        L59  exit 0  (unconditional)
# A frozen anomaly worth knowing and NOT fixing (R-4): `ls *MT.cbl' at L26
# matches 29 files, not 28. The extra one is dummy-rdbmsMT.cbl, which has no
# *MT.scb and was already compiled at L21 without cobmysqlapi.o; L26 compiles
# it again WITH the object and overwrites the first result. Reproduced as-is.
# TWO PHANTOM FLAGS -- RECORDED SO NOBODY "RESTORES" THEM (R-4). The frozen
# changelog header claims two compiler flags that no live invocation uses.
# [common/comp-common.sh:L8-L9] says "-Wno-goto-section added to remove the
# silly default warning in latest gnucobol v3.2" and [README.TXT:L204-L212]
# repeats it, yet across the live (non-comment) lines of all seven frozen
# compile scripts -Wno-goto-section occurs zero times.

# [common/comp-common.sh:L11] says "Added to all comps -fdump=all", yet
# -fdump=all occurs zero times: what exists is -fdump=ws, in general (3 lines),
# irs (4) and purchase (3) only, with sales and stock carrying none.
# A maintainer reading that changelog will be tempted to put the missing flags
# back. DO NOT. Adding either changes cobc's diagnostics and, for the
# arithmetic the migration depends on, the compiler must be invoked exactly as
# the maintainer actually invokes it -- default arithmetic, and no flag this
# script added or removed.
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

  # No-follow, exclusive, 0600 -- the same treatment presql2.param gets. A build
  # log holds no credential, but a bare `: >' here would still let anything that
  # could plant a symlink at this predictable name truncate the file it pointed
  # at, which is the whole of CWE-59/CWE-367 and is not excused by the payload
  # being uninteresting.
  local log="$ACAS_LOG_DIR/comp-common.log"
  acas_create_private_file "$log" 'the comp-common.sh build log' "$EX_STEP4"

  # DEVIATION 5 of 6 -- COBCPY and COB_COPY_DIR are set for this invocation only.
  # Setting them is the maintainer's own practice -- [comp-all.sh:L9-L10] exports
  # both -- and the deviation is only that absolute paths are used instead of the relative
  # `../copybooks', because step 4 runs comp-common.sh directly rather than
  # through comp-all.sh. comp-all.sh's own relative values are left untouched and
  # take effect in step 5. The frozen script itself is not modified in any way.
  acas_log "running: bash ./comp-common.sh   (cwd $common_dir)"
  acas_log "COBCPY=$ACAS_BUILD/copybooks (absolute; cf. [comp-all.sh:L9-L10])"
  acas_log "deadline: ${ACAS_TIMEOUT_BUILD}s (raise ACAS_TIMEOUT_BUILD on a slower host)"

  # The deadline is imposed with acas_deadline_prefix rather than with
  # acas_run_deadline because this output must reach the log through `tee' and
  # acas_run_deadline cannot be piped: the verdict has to be reached in THIS
  # shell for acas_die to abort the script rather than a subshell.
  #
  # `timeout' supervises the `bash ./comp-common.sh' process exactly. A frozen
  # script that stalls -- on a copybook over a wedged mount, or on a prompt --
  # is sent TERM at the deadline and KILL after the grace period.
  local rc=0 started elapsed
  acas_deadline_prefix "$ACAS_TIMEOUT_BUILD"
  started="$SECONDS"
  (
    cd "$common_dir" \
      && exec "${ACAS_DEADLINE_ARGV[@]}" \
           env "COBCPY=$ACAS_BUILD/copybooks" \
               "COB_COPY_DIR=$ACAS_BUILD/copybooks" \
               bash ./comp-common.sh
  ) 2>&1 | tee -a "$log" || rc=$?
  elapsed=$(( SECONDS - started ))

  # `pipefail' is set, so rc is the subshell's status whenever tee succeeded.
  # A TIMEOUT is fatal even though an ordinary nonzero rc is not: the frozen
  # script's bare `exit 0' means its own status carries no information, but
  # "never finished" is not a status the frozen script can fake.
  acas_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_BUILD" \
    ACAS_TIMEOUT_BUILD 'comp-common.sh' "$EX_STEP4"

  # rc is reported, never trusted: [common/comp-common.sh:L59] is a bare exit 0.
  acas_log "comp-common.sh returned $rc (informational only -- L59 is an unconditional exit 0)"

  acas_scan_build_log "$log" 'comp-common.sh' "$EX_STEP4"
  acas_shred_param_files
}

# STEP 5/5 -- run comp-all.sh UNMODIFIED
# [comp-all.sh:L9-L10] exports COBCPY=../copybooks and
# COB_COPY_DIR=../copybooks -- relative, and correct because every compile runs
# with its own directory as the cwd. The body then compiles in the maintainer's
# own order:
#   common -> general -> irs -> purchase -> sales -> stock
# ([comp-all.sh:L15-L32]; the OE, payroll and epos blocks are commented out).
# comp-all.sh RE-RUNS comp-common.sh at [comp-all.sh:L16]. That is the
# maintainer's own design and is NOT optimised away. Step 4 is retained
# deliberately and separately: the plan prescribes the five-step order, and
# running comp-common.sh explicitly gives a clean, attributable log for the
# bridge/handler/loader stage instead of burying it in the full build.

# So expect that stage TWICE in a full run: do not deduplicate it, and do not
# drop step 4 as redundant.
# Per-directory divergences that are preserved, never harmonised (R-4):
#   general, irs, purchase  -- -fdump=ws -fmissing-statement=ok
#                              -D_FORTIFY_SOURCE=1
#   sales                   -- accept_numeric references COMMENTED OUT
#                              ([sales/comp-sales.sh:L2,L5,L11,L13]) and NO
#                              -fdump / -fmissing-statement on live lines
#   stock                   -- also no -fdump / -fmissing-statement
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

  # Same treatment as the comp-common.sh log above.
  local log="$ACAS_LOG_DIR/comp-all.log"
  acas_create_private_file "$log" 'the comp-all.sh build log' "$EX_STEP5"

  acas_log "running: bash ./comp-all.sh   (cwd $ACAS_BUILD)"
  acas_note 'comp-all.sh ends by cd-ing into stock/ and never returns to the top,'
  acas_note 'so it is run in a subshell and this script'"'"'s own cwd is unaffected'
  acas_log "deadline: ${ACAS_TIMEOUT_BUILD}s (raise ACAS_TIMEOUT_BUILD on a slower host)"

  # Same shape as step 4: piped to tee, so the deadline prefix is applied here
  # and the verdict is reached in this shell. comp-all.sh compiles six
  # directories, so it is the longest-running command in the script and the one
  # most in need of a bound.
  local rc=0 started elapsed
  acas_deadline_prefix "$ACAS_TIMEOUT_BUILD"
  started="$SECONDS"
  (
    cd "$ACAS_BUILD" && exec "${ACAS_DEADLINE_ARGV[@]}" bash ./comp-all.sh
  ) 2>&1 | tee -a "$log" || rc=$?
  elapsed=$(( SECONDS - started ))

  acas_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_BUILD" \
    ACAS_TIMEOUT_BUILD 'comp-all.sh' "$EX_STEP5"

  acas_log "comp-all.sh returned $rc (informational only -- L45 is an unconditional exit 0)"

  acas_scan_build_log "$log" 'comp-all.sh' "$EX_STEP5"
  acas_shred_param_files
}

# ARTIFACT ASSERTIONS
# More reliable than any text scan: they inspect the products of the build
# rather than the prose about it. Counts are derived from the build tree's own
# source globs rather than hard-coded, so they stay correct as the frozen tree
# is what it is -- for example `ls *MT.cbl' matches 29 files, not the 28
# bridges, because dummy-rdbmsMT.cbl has no *MT.scb.
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

# FINALISATION
acas_finalise() {
  acas_stage 'Post-build: loader cache and module search path'

  if acas_have ldconfig; then
    # Under a deadline like everything else: ldconfig walks every directory in
    # /etc/ld.so.conf.d, and one of those pointing at an unresponsive mount is
    # enough to stall the final stage of an otherwise successful build.
    acas_deadline_prefix "$ACAS_TIMEOUT_PROBE"
    if "${ACAS_DEADLINE_ARGV[@]}" ldconfig 2>/dev/null; then
      acas_log 'refreshed the shared-library cache (ldconfig)'
    else
      acas_warn 'ldconfig failed (root privileges are usually required); the compiled modules may not resolve libmysqlclient at run time.'
    fi
  fi

  # COB_LIBRARY_PATH must cover all six build directories so that the compiled
  # modules resolve when harness/run_cobol_scenario.sh drives a menu. Published
  # here and printed, because it is this script's output contract to the runner
  # scripts. Any existing value is preserved and appended to.
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

# MAIN
# Strictly sequential (R-3). No step is backgrounded, no step is parallelised,
# and the order is the one the plan prescribes. Nothing here writes to
# $ACAS_REPO, and nothing is placed anywhere acas_posting/ could import (R-1).
acas_main() {
  acas_parse_args "$@"

  # Before ANY external command is spawned: a malformed budget must be a startup
  # usage error, never something discovered hours into a build.
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
