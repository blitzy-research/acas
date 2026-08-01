#!/usr/bin/env bash
# harness/run_cobol_scenario.sh
# Drive the COMPILED ACAS Cobol posting cycle for one scenario, with the same
# logical inputs the menus supply.
#
# This is stage 2 of the eight-stage parity protocol:
#
#     seed -> run(COBOL) -> dump -> normalize -> reset -> run(Python) -> dump -> diff
#
# and it is the ORACLE side of that diff. Its output is not "a result" to be
# judged; it IS the behavioural specification. Nothing in this script decides
# whether the Cobol did the right thing -- harness/diff_states.py does that.
# This script drives, observes, asserts its own PRECONDITIONS, and records.
#
# Run it with the canonical invocation documented at
# [harness/docker-compose.yml:L346-L357], which passes the scenario file as a
# bare POSITIONAL argument, so that form is accepted here alongside the named
# options.
#
# -----------------------------------------------------------------------------
# WHY THIS SCRIPT DRIVES THE MENU EXECUTABLES AND NOT THE POSTING PROGRAMS
# None of the twelve in-scope programs is a main program. Every one is a CALLed
# sub-program whose PROCEDURE DIVISION USING list is made of GROUP ITEMS, in
# exactly three distinct linkage shapes:
#   Shape 1  General Ledger, 4 params: `using ws-calling-data,
#      system-record, to-day, file-defs' [general/gl070.cbl:L245-L248],
#      [general/gl000.cbl:L162-L165] -- gl000 gl051 gl070 gl071 gl072 gl080
#   Shape 2  Sales / Purchase, 5 params: `using ws-calling-data,
#      System-Record, system-record-4, to-day, file-defs'
#      [sales/sl060.cbl:L395-L399] -- sl055 sl060 sl100 pl055 pl060 pl100

#   Shape 3  IRS, 3 params, NO to-day and NO calling-data block, irs030
#      only: `using IRS-System-Params, WS-System-Record, File-Defs'
#      [irs/irs030.cbl:L552-L554]
# `cobcrun' can pass only string arguments; it cannot construct a SYSTEM-REC
# group item, a File-Defs block or a WS-Calling-Data block, and the posting
# programs are compiled `-m' as dynamically loadable modules rather than `-x'
# executables. So no shell can invoke them directly. The four MENU executables
# -- general, sales, purchase, irs, built with `cobc -x' -- are what construct
# those blocks and CALL the sub-programs. Driving them is not a convenience; it
# is the only faithful method. Writing a NEW Cobol driver was rejected: it
# would add Cobol source to a repository whose Cobol is frozen (R-1, R-4, and
# the frozen-artifact guarantee) and there is no sanctioned place to put it.

# THE RULES THAT BIND THIS FILE
# There is NO user rules document for this project: `review_rules' reports that
# no user rules were provided. The six binding rules R-1..R-6 come from the
# Agent Action Plan itself. Where they are silent, this script is held to
# enterprise-standard shell practice. Nothing has been invented to fill a gap.
#   R-1  NO COBOL AT RUNTIME -- and this file is the sanctioned exception.
#        Compiled Cobol is confined to harness/ and invoked only as an
#        OUT-OF-PROCESS utility. This script never references acas_posting, is
#        never invoked from inside it, and harness/ has no __init__.py.
#   R-2  ZERO BINARY FLOATING POINT. No arithmetic on any monetary value here;
#        the only numbers this script computes with are counts, timeouts, row
#        counts and exit codes.

#   R-3  NO NEW VALIDATIONS, NO SCHEMA CHANGE, STRICTLY SEQUENTIAL. No DDL is
#        emitted, nothing is written under $ACAS_REPO, and exactly one scenario
#        runs at a time -- no `&', no `xargs -P', no job control. Every check
#        here is a HARNESS-ENVIRONMENT precondition, never an added validation
#        of what the Cobol computed.
#   R-4  LEGACY ANOMALIES REPRODUCED, NEVER FIXED. "A defect reproduced is
#        correct; a defect fixed is a failure." The sharpest obligation is the
#        THREE DIVERGENT ABORT GATES -- General `= 5', Sales `not = zero'
#        TWICE, and Purchase's gate COMMENTED OUT ENTIRELY -- each quoted with
#        its locator at its own plan function below. They are never harmonised.
#        The menus implement them; this script must not compensate, so it never
#        adds a gate to Purchase, never removes one from Sales, never turns a

#        gate into a warning, and never treats "gl071 did not run" as an error.
#        It OBSERVES which branch was taken and reports it. Sales runs sl830
#        first and Purchase does not run pl830: preserved too. And this script
#        never ends with an unconditional `exit 0'. The frozen build scripts do
#        -- [comp-all.sh:L45], [common/comp-common.sh:L59] -- and they are NOT
#        fixed; their shape is simply not adopted.
#   R-5  FULL TRACEABILITY. Every keystroke, screen anchor, gate and
#        precondition below carries a [<path>:<locator>] citation to the frozen
#        source it reproduces, and every deliberate deviation is annotated as a
#        deviation with its reason.

#   R-6  COMPILED BEHAVIOUR IS THE TIE-BREAKER, AND THE RUN MUST BE
#        REPRODUCIBLE. Two runs of one scenario under the same pinned clock
#        must produce byte-identical dumps. Therefore: the run date is PINNED
#        through the menus' own Date Entry option; this script never reads the
#        host clock; and NOTHING carrying a wall-clock time, hostname, pid, run
#        id, elapsed time or absolute path is ever written under
#        $ACAS_OUT/<scenario>/. The pty transcript goes deliberately OUTSIDE
#        the compared tree, to $ACAS_OUT/run-logs/<scenario>/, because
#        [general/gl000.cbl:L194] accepts the host TIME and
#        [general/gl000.cbl:L177] the host DATE, and the time is DISPLAYED at
#        0373 -- so the transcript necessarily contains a host clock reading
#        and can never be allowed into a compared dump.

# DOCUMENTED DEVIATIONS FROM THE PRODUCTION CALL PATH  (R-5)
#   D-1  Keystrokes on a pty instead of a human operator -- the only way to
#        supply the menus' logical inputs, per the linkage shapes above.
#   D-2  The run happens in $ACAS_DATA with $ACAS_BUILD on the library path,
#        not in the maintainer's ~/ACAS against ~/bin, because the checkout is
#        mounted read-only and the build is a container-local copy. That makes
#        the frozen-artifact guarantee structural rather than a matter of care.
#        This script never cd's into $ACAS_REPO.
#   D-3  ACAS_BIN points at a fixed directory whose contents do not change
#        between runs. Reason: determinism (R-6) of the CBL_CHECK_FILE_EXIST
#        branch at [general/general.cbl:L489-L503], which otherwise displays
#        "No BackUp Script in Bin" on one run and not the next.

#   D-4  Accepts whose only effect is to pause for acknowledgement get a bare
#        Return. AAP 0.3.4 drops such prompts on the Python side; on the Cobol
#        side they still need a keystroke, so they get the most neutral one.
#        Accepts that GATE A DATABASE WRITE are NOT treated this way -- they
#        are genuine scenario inputs, and there are three of them.
#   D-5  COB_EXIT_WAIT is forced to `off', because GnuCobol otherwise waits for
#        a keypress when a screen-section program ends, which would hang the
#        harness after the menu exits. This suppresses a pause, not a write, so
#        it is the same class of deviation as D-4.

# THE GATING INPUTS -- accepts that change table state, so the scenario pins
# them. Each is quoted in full at its own plan function below.
#   G-1  irs030 end-of-job "Can I clear the Ledgers Posting file? [Y]"
#        [irs/irs030.cbl:L1715-L1727]. "Y" performs acas008-Open-Output, which
#        the handler turns into a DELETE-ALL of PSIRSPOST-REC
#        [common/acas008.cbl:L313-L318] (key irs_clear_postings).
#   G-2  gl080's unconditional pre-run gate [general/gl080.cbl:L295-L302]:
#        Escape or "A"/"a" means `goback', so gl080 writes NOTHING (key
#        gl080_proceed).
#   G-3  sl100 [sales/sl100.cbl:L310-L318] and pl100
#        [purchase/pl100.cbl:L302-L311] each ask an unconditional YES/NO whose
#        WORDING DIVERGES; NO posts nothing (key payment_post_confirm).

set -Eeuo pipefail
IFS=$'\n\t'
shopt -s nullglob
umask 077

# EXIT CODES
# Chosen not to collide with the load-program codes harness/seed.sh already
# reserves (16 / 64 / 128) and continuous with seed.sh's own 70..73 block so an
# operator reading either log sees one scheme.
readonly EX_OK=0
readonly EX_USAGE=70
readonly EX_PRECONDITION=71
readonly EX_DATABASE=72
readonly EX_AUTOCOMMIT=73  # autocommit is not on -- the frozen COBOL never commits
readonly EX_ORACLE=74      # a compiled artifact is missing -> build_oracle.sh
readonly EX_SCENARIO=75    # the scenario file is missing or malformed
readonly EX_DRIVE=76       # the pty driver timed out, spun, or hit a refusal
readonly EX_ASSERT=77      # a post-run assertion failed
readonly EX_TIMEOUT=78     # an external command exceeded its finite deadline
readonly EX_CAPACITY=79    # the fh-logger budget cannot be met -> refuse to run


# =============================================================================
# FINITE DEADLINES
#
# No external command may run without an upper bound. The pty driver already
# enforces a PER-PROMPT timeout inside itself, and that is not the same guarantee:
# a driver that keeps making prompt-by-prompt progress, or one that blocks in a
# syscall before its select loop is even reached, never trips it and runs forever.
# ACAS_TIMEOUT_DRIVE therefore bounds the WHOLE driver process, in addition to
# --timeout bounding each prompt within it.
#
# Declared as "${VAR-}" rather than as a bare default so an operator-supplied
# value SURVIVES to be validated. Writing ACAS_TIMEOUT_X='' here would discard the
# environment silently, which makes every documented tunable inert and -- worse --
# means an invalid budget is never rejected.
# =============================================================================
readonly ACAS_TIMEOUT_MAX=86400          # 24h, an upper bound on any one budget
ACAS_TIMEOUT_GRACE="${ACAS_TIMEOUT_GRACE-}"    # seconds between TERM and KILL
ACAS_TIMEOUT_CLIENT="${ACAS_TIMEOUT_CLIENT-}"  # one database client invocation
ACAS_TIMEOUT_DRIVE="${ACAS_TIMEOUT_DRIVE-}"    # the whole pty driver process
ACAS_TIMEOUT_ROTATE="${ACAS_TIMEOUT_ROTATE-}"  # one fh-logger rotation move
ACAS_TIMEOUT_RESOLVED=''                 # out-parameter of acas_timeout_seconds

# Free space reserved for the frozen file-handler log. Declared with the same
# "${VAR-}" form as the deadlines so that an operator-supplied value survives:
# a bare VAR='' would wipe the environment and make the knob inert, which is
# exactly the defect that made every documented ACAS_TIMEOUT_* non-functional
# in all three sibling scripts until it was found by testing through the
# environment rather than by sourcing.
ACAS_FH_LOG_BUDGET_MB="${ACAS_FH_LOG_BUDGET_MB-}"
readonly ACAS_RUN_FH_BUDGET_DEFAULT_MB=1024
ACAS_RUN_FH_BUDGET_MB=0                  # frozen by acas_resolve_deadlines
declare -a ACAS_DEADLINE_ARGV=()         # the resolved `timeout ...' prefix

# ENVIRONMENT CONTRACT
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

# The one schema the frozen dump defines. [mysql/ACASDB.sql:L3] records
# "Host: localhost    Database: ACASDB", and the file carries 33 CREATE TABLE
# statements with zero CREATE DATABASE and zero USE -- so there is exactly one
# database this cycle can legitimately be driven against.
readonly ACAS_RUN_REQUIRED_SCHEMA='ACASDB'

# The pty geometry. Pinned to EXACTLY 24x80 rather than "at least", because a
# larger terminal changes how many report lines a screen holds -- ws-21-lines
# and ws-22-lines at [general/gl070.cbl:L254] are derived from `accept ... from
# lines' -- and that would change the keystroke count between hosts (R-6).
# 24x80 is the MINIMUM the menu will tolerate. Below it the menu refuses to run:
# [general/general.cbl:L374-L383] displays SY010 for too few lines and SY013 for
# too few columns and then `goback's, producing an empty run that looks exactly
# like a clean pass. That is the single highest-value precondition in this file.
readonly ACAS_RUN_ROWS=24
readonly ACAS_RUN_COLS=80

# The seven operation names. These MUST stay identical to the set the
# Python-side scenario runner is to accept, so the two runners are trivially
# comparable; that parity is asserted by the validation checklist.
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

# operation:subsystem:menu-key:paragraph:locator
# The menu key is NOT guessed. Each menu accepts one character and resolves it
# to a paragraph by ordinal: `letters-upper' is "ABC..Z"
# [general/general.cbl:L271], `a-entry' occurs 26 times
# [general/general.cbl:L273], a SEARCH sets z to the matching subscript
# [general/general.cbl:L603-L608], and `go to load01 load02 ... depending on z'
# dispatches [general/general.cbl:L699-L704]. So the Nth letter selects loadNN.
# Each key below follows from that rule and from the menu's own display block,
# and agrees with the paragraph the AAP names.

#   general  "(H)  Transaction Posting"      at 1044  -> H is 8th  -> load08
#   general  "(I)  End Of Cycle Processing"  at 1144  -> I is 9th  -> load09
#   sales    "(G)  Sales Transactions Post"  at 1604  -> G is 7th  -> load07
#   sales    "(K)  Payment Post"             at 2004  -> K is 11th -> load11
#   purchase "(H)  Purchase Transactions Post" at 1704 -> H is 8th -> load08
#   purchase "(L)  Payment Post"             at 2104  -> L is 12th -> load12
# Note in particular that Sales invoice posting is load07 and NOT load08:
# [sales/sales.cbl:L770] load08 is sl080, a different and out-of-scope program.
readonly -a ACAS_RUN_OPERATION_MAP=(
  'gl_post_cycle:general:H:load08:general/general.cbl:L805-L815'
  'gl_end_of_cycle:general:I:load09:general/general.cbl:L817-L821'
  'sl_invoice_post:sales:G:load07:sales/sales.cbl:L756-L768'
  'sl_cash_post:sales:K:load11:sales/sales.cbl:L792-L796'
  'pl_order_post:purchase:H:load08:purchase/purchase.cbl:L752-L762'
  'pl_payment_post:purchase:L:load12:purchase/purchase.cbl:L786-L790'
  'irs_post:irs:4:irs030-dispatch:irs/irs030.cbl:L666-L672'
)

# The in-scope `-m' modules each subsystem's menu must be able to load, taken
# verbatim from the arrays harness/build_oracle.sh publishes so the two files
# cannot disagree about what "built" means.
readonly -a ACAS_RUN_GENERAL_MODULES=(gl000 gl051 gl070 gl071 gl072 gl080)
readonly -a ACAS_RUN_SALES_MODULES=(sl000 sl055 sl060 sl100)
readonly -a ACAS_RUN_PURCHASE_MODULES=(pl000 pl055 pl060 pl100)
readonly -a ACAS_RUN_IRS_MODULES=(irs000 irs030)

# The subsystem directories build_oracle.sh compiles, in its own order. Used to
# rebuild the COB_LIBRARY_PATH contract it publishes.
readonly -a ACAS_RUN_LIBRARY_DIRS=(common general irs purchase sales stock)

# Screen refusals and interactive diversions. If ANY of these reaches the
# transcript the run is void, so the driver aborts the moment it sees one
# rather than continuing to a dump that would silently compare nothing.
#   SY010 / SY013  the 24x80 refusal          [general/general.cbl:L374-L383]
#   SYS002/SY102/SY104
#                  system.dat could not be opened, so the menu CALLed sys002
#                  interactively [general/general.cbl:L385-L396]. sys002 is a
#                  full interactive parameter-entry program, so its banner on
#                  the transcript means the menu never reached a posting run.
#   SY007          a program argument the menu refuses, then `stop run'
#                  [copybooks/Proc-Get-Env-Set-Files.cob:L75], `stop run' at
#                  [copybooks/Proc-Get-Env-Set-Files.cob:L82]

#   SY009          ACAS_LEDGERS or ACAS_BIN begins with a space, then a
#                  `stop run' [copybooks/Proc-Get-Env-Set-Files.cob:L20-L28]
#   Invalid Date   the date-entry reject loop. All four date programs word it
#                  the same way at the end of the message -- GL009
#                  [general/gl000.cbl:L148], SL005, PL005, IR005 -- so the
#                  shared suffix is a single reliable detector.
# FIELD SEPARATOR IS '|', NOT ':'. A colon cannot be used here: a locator is
# itself path:Lnnn, and a reason may legitimately contain a colon too, so a
# colon-split silently truncates the reason and glues its tail onto the
# front of the locator. '|' appears in no screen code, no reason and no path.
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

# The menu anchors. All three letter-menus share one prompt, written by a single
# `display' of a 44-character literal at 0601, so it always reaches the pty
# contiguously: [general/general.cbl:L568], [sales/sales.cbl:L537],
# [purchase/purchase.cbl:L531]. The IRS menu is a SCREEN SECTION rather than a
# display/accept pair, so its anchor comes from the screen item at
# [irs/irs.cbl:L440-L441].
readonly ACAS_RUN_MENU_ANCHOR='Select one of the following by letter'
readonly ACAS_RUN_IRS_MENU_ANCHOR='Select the required function'
readonly ACAS_RUN_IRS_OPTION_ANCHOR='Enter Run Option'

# The 22 in-scope tables, used only to validate a scenario's affected-table list
# against the same vocabulary harness/dump_tables.py uses. Nothing here issues
# DDL and nothing here inspects the schema for its own sake (R-3).
readonly -a ACAS_RUN_INSCOPE_TABLES=(
  ANALYSIS-REC GLBATCH-REC GLLEDGER-REC GLPOSTING-REC
  IRSDFLT-REC IRSFINAL-REC IRSNL-REC IRSPOSTING-REC
  PSIRSPOST-REC PUINV-LINES-REC PUINVOICE-REC PUITM5-REC PULEDGER-REC
  SAINV-LINES-REC SAINVOICE-REC SAITM3-REC SALEDGER-REC
  SYSDEFLT-REC SYSFINAL-REC SYSTEM-REC SYSTOT-REC VALUEANAL-REC
)

# The two autogen tables. Never seeded -- harness/seed.sh deliberately does not
# invoke slautogenLD -- and asserted untouched after any Sales run, because the
# Sales menu runs sl830 first [sales/sales.cbl:L759-L760] whereas the Python
# Sales invoice CLI entry point dispatches only sl055 -> sl060. See THE sl830
# ASYMMETRY below.
readonly -a ACAS_RUN_AUTOGEN_TABLES=(SAAUTOGEN-REC SAAUTOGEN-LINES-REC)

# THE sl830 ASYMMETRY -- the Cobol side runs a program the Python side does not
# [sales/sales.cbl:L756-L768] load07 calls sl830 BEFORE sl055, and sl830 is
# explicitly out of scope: AAP 0.2.2 excludes the sales autogen series
# sl800..sl830, and AAP 0.4.1.1 has the Sales invoice CLI entry point dispatch
# only sl055 -> sl060. Because this script must drive the menu, sl830 WILL
# execute on the oracle side. Two facts make that safe, and both are asserted
# rather than assumed:

#   1. sl830 is a genuine no-op when autogen is not in use. Its first act after
#      initialising is [sales/sl830.cbl:L270-L272]:
#          if       SL-Autogen not = "Y"    *> SL Autogen not in use
#                   goback.
#      The field is [copybooks/wssystem.cob:L274] `05 SL-Autogen pic x value
#      space', column SL-AUTOGEN in SYSTEM-REC. So with SL-AUTOGEN not "Y" it
#      returns before touching anything.

#   2. If SL-AUTOGEN *were* "Y" the whole Sales invoice path would become
#      NON-DETERMINISTIC and this harness could not be trusted, because
#      [sales/sl830.cbl:L298] does
#          accept   WS-Temp-Run-Date from DATE YYYYMMDD.
#      and feeds that HOST CLOCK reading into the arithmetic that decides
#      which autogen invoices to create. That is a direct R-6 violation, and
#      it is why SL-AUTOGEN is a hard precondition for every Sales operation
#      here rather than a hopeful assumption.

# The residual asymmetry -- the oracle runs one more program than the Python
# does, even though that program returns immediately -- is settled by this
# script's own post-run assertion that the two autogen tables are untouched,
# which is what R-6 requires of an ambiguity, and recorded for the ambiguity
# register the migration documentation set is to carry.

# THE FILE-SYSTEM-USED SILENT-PASS TRAP
# [general/general.cbl:L385-L396] forces the Cobol path for the SYSTEM PARAMETER
# FILE only -- `move "00" to FA-RDBMS-Flat-Statuses. *> Force Cobol proc.' What
# decides whether the LEDGER and POSTING files reach the RDB is a different
# field, File-System-Used [copybooks/wssystem.cob:L111-L112], read out of
# system.dat, column FILE-SYSTEM-USED in SYSTEM-REC. The menu's own exit path
# only rewrites the RDB copies `if File-System-Used NOT = zero'
# [general/general.cbl:L656-L692].
# So if FILE-SYSTEM-USED is zero the entire run writes Cobol flat files only,
# every in-scope table is untouched, the state diff is empty, and the harness
# reports a clean pass having compared nothing. That is the worst possible
# failure mode for an oracle, so it is a hard precondition.

# THE MENU-EXIT SIDE EFFECT, AND WHY THE COMPARISON IS BOUNDED BY THE SCENARIO
# Leaving a letter-menu with "X" is not inert. [general/general.cbl:L656-L692]
# reopens the system files and rewrites key 1 (SYSTEM-REC), key 2 (the default
# record, SYSDEFLT-REC) and key 4 (WS-System-Record-4, SYSTOT-REC), closes, and
# then repeats the identical three rewrites against the Cobol flat file. The
# Python CLI has no menu and does none of this. THE FOUR MENUS DO NOT AGREE ON
# WHICH KEYS THEY REWRITE, and the difference changes which tables a run
# touches; the per-subsystem key list, with each menu's own locator, is stated
# once at acas_plan_menu_exit and reported in the plan from there. Nothing is
# harmonised: the divergence is the specification (R-4).

# The resolution is NOT to avoid the exit path -- killing the process instead
# would leave a different and non-deterministic state -- and NOT an ignore-list
# in the diff tool. It is to exit cleanly with "X" and let each scenario's
# affected-table list bound the comparison, which AAP 0.4.1.7 already mandates
# and harness/dump_tables.py already implements through its `affected_tables'
# key. This script therefore requires that key and validates it.
# SYSTOT-REC deserves a note: it is genuinely in scope for the period-end
# totals scenario, because AAP 0.6.4 names nine period-total write sites as
# "the sole writers of the totals record". So the overlap between "written by
# the menu exit" and "written by the cycle" is real, belongs in the migration
# documentation set's ambiguity register, and must never be papered over.

# Mutable state. Declared up front because `set -u' makes an unset array or
# scalar a fatal reference.
ACAS_RUN_SCENARIO=''            # scenario NAME
ACAS_RUN_SCENARIO_FILE=''       # scenario YAML path
ACAS_RUN_SUBSYSTEM=''           # --subsystem, or derived from --operation
ACAS_RUN_OPERATION=''           # --operation
ACAS_RUN_TIMEOUT=120            # per-prompt timeout, seconds
ACAS_RUN_LOG=''                 # $ACAS_OUT/run-logs/<scenario>/cobol.log
# Whether the transcript file actually EXISTS and is writable yet, as distinct
# from merely having been requested on the command line. --log sets the path
# during argument parsing, long before the directory is created, so a non-empty
# ACAS_RUN_LOG must never on its own be taken as permission to append: doing so
# makes every diagnostic emitted between parsing and acas_open_log fail its
# redirection, and a failed redirection is reported by the shell itself against
# the stderr in force at that moment, which no 2>/dev/null on the command can
# suppress after the fact. acas_open_log sets this to 1 only once the file is
# successfully created.
ACAS_RUN_LOG_OPEN=0
ACAS_RUN_LOCK=''                # the sequential-run lock, removed by the EXIT trap
ACAS_RUN_PLAN_FILE=''           # the resolved keystroke plan, beside the log
ACAS_RUN_RESULT_FILE=''         # the driver's machine-readable outcome record
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
ACAS_RUN_IRS_CLEAR=''           # G-1: irs030's clear-transfer-file answer
ACAS_RUN_GL080_PROCEED=''       # G-2: gl080's pre-run gate answer
ACAS_RUN_PAYMENT_CONFIRM=''     # G-3: sl100 / pl100 YES/NO
ACAS_SQL_OUT=''                 # last successful scalar query result
ACAS_SQL_DIAG=''                # last client diagnostic, for error messages
declare -a ACAS_RUN_TABLES=()          # the scenario's affected-table list
declare -a ACAS_RUN_SUMMARY=()         # the closing summary table
declare -a ACAS_RUN_WARN_SUMMARY=()    # non-fatal findings, replayed at the end
# The client transports this target has earned, most secure first. Decided ONCE
# by acas_assert_transport_policy, before anything connects, and consumed
# read-only by acas_sql_scalar -- see the TRANSPORT SECURITY section.
declare -a ACAS_RUN_TLS_VARIANTS=()
# The schema name, validated and SQL-escaped once, for the one information_schema
# query this script issues -- see SAFE SQL COMPOSITION.
ACAS_RUN_SCHEMA_LITERAL=''
# The sequential run lock. The PATH and the OWNERSHIP FLAG are separate for the
# same reason ACAS_RUN_LOG_OPEN is separate from ACAS_RUN_LOG: knowing the name of
# a lock is not permission to delete it. Only the process that successfully created
# it sets the flag, so the EXIT trap can never remove a live run's lock.
ACAS_RUN_LOCK=''
ACAS_RUN_LOCK_HELD=0

# REPORTING
# Stage banners are numbered so the log reads as the deterministic staged
# orchestration the plan prescribes (R-6). Everything printed goes to standard
# output and, once the log is open, to $ACAS_OUT/run-logs/<scenario>/cobol.log.
# NOTHING is written under $ACAS_OUT/<scenario>/, because a compared dump must
# be byte-identical between runs and this log necessarily contains the host time
# the menu displays at [general/general.cbl:L556-L557].

# Append to the run log if it is open yet. Silent before acas_open_log runs, so
# early usage errors still print without needing a log.
acas_tee() {
  if (( ACAS_RUN_LOG_OPEN )); then
    # 2>/dev/null is deliberately FIRST. Redirections are applied left to right,
    # so silencing stderr before opening the append target is what actually
    # suppresses a redirection failure; the reverse order lets the shell's own
    # diagnostic escape to the terminal.
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

# acas_die <exit-code> <headline> [detail-line]...
# Every abort names the artifact or setting at fault and, wherever the cause is
# frozen behaviour, cites its locator so the claim is traceable to it (R-5).
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

# Record one row of the closing summary table.
# acas_summary_row <label> <value>
acas_summary_row() {
  ACAS_RUN_SUMMARY+=("$(printf '%-22s %s' "$1" "$2")")
}

# -----------------------------------------------------------------------------
# SANITISING A VALUE BEFORE IT REACHES THE TRANSCRIPT  (CWE-117 log injection,
# CWE-532 sensitive information in a log)
#
# The environment block was reported straight into the transcript:
#
#     acas_log "database   = $ACAS_DB_NAME on $ACAS_DB_HOST:$ACAS_DB_PORT as $ACAS_DB_USER"
#
# Every one of those is caller-supplied. A value carrying a newline forges an
# arbitrary transcript line -- including a plausible "PASS" or "==> Stage" banner --
# and a value carrying ESC or a C1 control writes a terminal escape sequence into
# a file an operator is told to `cat'. The transcript is EVIDENCE: it is the
# artifact docs/migration/scenario-diff-evidence.md points at, so a forgeable
# line is a forgeable finding.
#
# NEUTRALISED, NOT REJECTED. These values are already width-checked against the
# frozen host-variable limits [copybooks/wsfnctn.cob:L56-L62] and a legitimate
# one contains no control character at all, so rendering it safely loses nothing
# real while an outright refusal would turn a cosmetic mistake into an abort.
# CR, LF, TAB, ESC, every other C0 control and the C1 range are replaced by a
# visible marker, and the field is capped so one value cannot flood the file.
#
# `LC_ALL=C tr' operates on BYTES, which is what is wanted: a multi-byte
# character cannot smuggle a C1 control past a byte-wise class.
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# SAFE SQL COMPOSITION  (CWE-89)
#
# This script issues exactly ONE query that embeds a caller-supplied value:
#
#     where table_schema = '$ACAS_DB_NAME'      <-- the defect, as it was
#
# ACAS_DB_NAME arrives from the environment, so an apostrophe in it terminated
# the literal and the remainder of the value was parsed as SQL. Two independent
# controls replace it, in this order, both applied BEFORE any SQL is composed:
#
#   1. The name must be a plain SQL identifier and must be one of the schemas
#      this harness is allowed to look at. That is a WHITELIST, which is the only
#      control that actually bounds what the value can be.
#   2. Whatever survives step 1 is escaped for a string literal anyway, so a
#      future call site cannot reintroduce the defect by forgetting step 1.
#
# Identifier quoting goes through acas_sql_quote_ident, declared with the SQL
# COMPOSITION SAFETY block below. Every SQL identifier this script names is a
# frozen constant from the in-scope table list, so none comes from the caller;
# the helper exists because every identifier in this schema is HYPHENATED and so
# has to be backquoted, and one helper that emits its own delimiters is safer
# than a backquote pair hand-written at each site.
# -----------------------------------------------------------------------------
readonly ACAS_RUN_SCHEMA_NAME_PATTERN='^[A-Za-z_][A-Za-z0-9_$]*$'
readonly -a ACAS_RUN_DEFAULT_ALLOWED_SCHEMAS=(
  'ACASDB'
)

# Escape a value for use inside a single-quoted SQL literal and RETURN IT WITH
# ITS QUOTES, so a call site cannot use the result and forget to quote it.
# Backslash first, then the apostrophe: doing it the other way round would
# re-escape the backslashes this function just added.
acas_sql_quote_literal() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\'/\\\'}"
  printf "'%s'" "$value"
}

# Split a comma- or space-separated list into one item per line. A LOCAL IFS is
# used rather than `tr', because the global IFS is deliberately $'\n\t' and so
# splitting on a comma or a space is not otherwise available here.
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

# Validate ACAS_DB_NAME and compute ACAS_RUN_SCHEMA_LITERAL once. Called from
# acas_assert_environment, before anything connects.
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

# -----------------------------------------------------------------------------
# SAFE FILE CREATION  (CWE-59 symlink following, CWE-367 TOCTOU, CWE-732
# over-permissive files)
#
# `: >"$path"' FOLLOWS a symlink and TRUNCATES its target, and creates at
# whatever the umask allows. The three files this script creates -- the
# transcript, the plan and the driver's outcome record -- live under $ACAS_OUT,
# which the Compose recipe makes a bind mount shared between the `gnucobol' and
# `mariadb' services. So anything able to place `run-logs/<scenario>/cobol.log'
# there first chooses which file gets truncated, and then reads the pty
# transcript of a whole posting run.
#
# THE PATTERN, in four steps, each load-bearing, identical to the one
# harness/reset_db.sh and harness/seed.sh use (deliberately duplicated rather than
# sourced: the three scripts are independent entry points and none may fail
# because another is absent):
#
#   1. REFUSE a symlink outright. Bash has no O_NOFOLLOW, so this is an explicit
#      `-L' test. On its own it would be a TOCTOU window, which is why step 3
#      exists.
#   2. REMOVE an existing regular file, so step 3's exclusive create is not
#      defeated by our own previous run. These files are truncated at the start
#      of every run by contract, so removing one is exactly the old behaviour.
#   3. CREATE under `set -C' (noclobber), which is O_EXCL: if anything -- a
#      symlink, a regular file, a directory -- appears at the name between step 1
#      and here, the create FAILS instead of following or truncating.
#   4. chmod 600, so the content is private regardless of the inherited umask.
#      `umask 077' is set at the top of this script, which makes step 4 belt and
#      braces rather than the only control.
#
# The embedded pty driver reopens two of these files later, and it does so with
# O_NOFOLLOW -- see WRITING THE EVIDENCE inside acas_drive -- because the window
# between this create and that reopen is exactly what step 3 cannot cover.
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
# DEADLINE HELPERS
# =============================================================================

# acas_timeout_seconds <variable-name> <default>
# Validates the named variable and publishes the result in ACAS_TIMEOUT_RESOLVED.
#
# THE RESULT IS AN OUT-PARAMETER, NOT STDOUT, AND THAT IS LOAD-BEARING. If this
# printed instead, callers would write `x="$(acas_timeout_seconds ...)"' -- a
# command substitution, in which acas_die's `exit' terminates only the subshell.
# Every rejected budget would then be accepted as the EMPTY STRING, and an empty
# budget in `(( elapsed >= budget ))' is treated as zero, so every non-zero status
# would look like a timeout while no deadline was actually applied.
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

  # The fh-logger budget is resolved HERE, with the deadlines, because it is the
  # same kind of value -- a number arriving from the environment that silently
  # becomes meaningless if it is malformed. Validating it this early means a typo
  # is a usage error before any scenario file is parsed or any socket is opened.
  # The free-space CHECK it feeds cannot happen here, because $ACAS_DATA is not
  # known to exist yet; that is acas_assert_fh_log_capacity, called as soon as it
  # is. Syntax first, enforcement when the facts are available.
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

# -----------------------------------------------------------------------------
# Free space for the frozen file-handler log, asserted BEFORE the database is
# contacted and long before the menu is spawned.
#
# The ordering is the whole point of the check. Logging cannot be switched off --
# [copybooks/Test-Data-Flags.cob] hardcodes `SW-Testing value 1' and that file is
# frozen (R-4) -- and the log has been measured growing 473 MB in about three
# minutes. If the volume fills part-way through a posting cycle, the database is
# left half-posted: some batches cleared, some not. That state is not a failure
# this protocol can diff its way out of, because the diff would show real
# differences produced by an unrelated cause, and the run that produced it would
# report a write error rather than a capacity problem.
#
# So the refusal happens while refusing is still free.
# -----------------------------------------------------------------------------
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

# acas_deadline_prefix <budget-seconds>
# Publishes the command prefix in ACAS_DEADLINE_ARGV. TERM first so a child can
# clean up, KILL after the grace period so one that ignores TERM still dies.
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

# acas_is_timeout_status <rc> <elapsed> <budget>
# True when a status plausibly means "the deadline expired".
#
# GNU coreutils reports 124 on expiry and 137 when the KILL was needed. The uutils
# reimplementation -- which is what is on some hosts, including this container --
# reports 125 where GNU reports 124, and GNU uses 125 for "timeout itself failed".
# The status alone is therefore ambiguous, so elapsed time disambiguates: a command
# that consumed its entire budget and then failed timed out, whatever it reported.
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

# acas_assert_not_timed_out <rc> <elapsed> <budget> <budget-var> <label>...
# Dies with EX_TIMEOUT when the status means the deadline expired. Names both the
# stage and the variable, so an under-provisioned budget is distinguishable from a
# genuinely stuck command.
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


# =============================================================================
# PATH CONTAINMENT
#
# Every write target is judged by its CANONICAL path, never by the string the
# operator typed. A textual prefix test -- `[[ "$p" == "$root"/* ]]' -- is
# satisfied by none of the ways a path actually escapes:
#   * `$root/../<same-basename>/x'   resolves back inside, but does not match
#   * a symlink whose target is inside resolves inside, but does not match
#   * a relative path matches nothing at all, yet lands wherever the cwd is
# So each check resolves both sides with readlink -f first. For a target that
# does not exist yet, the nearest EXISTING ancestor is resolved instead, because
# readlink -f on a missing leaf cannot follow a symlink that is not there.
#
# Containment is rejected in BOTH directions: the target must not sit inside the
# protected root, and the protected root must not sit inside the target -- the
# second because a write target that CONTAINS the checkout would have the frozen
# tree deleted underneath it by any cleanup that treats the target as its own.
# =============================================================================

# acas_canonical_path <path>
# Prints the canonical form of <path>, resolving through the nearest existing
# ancestor when the leaf does not exist yet. Never fails; falls back to the input.
acas_canonical_path() {
  local path="$1" probe parent tail=''

  # An empty or relative path is anchored first, so the answer does not depend on
  # the caller's working directory.
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

# acas_path_contains <root> <path>
# True when <path> IS <root> or lies beneath it, or when <root> lies beneath
# <path>. Both arguments must already be canonical.
acas_path_contains() {
  local root="${1%/}" path="${2%/}"
  [[ -n "$root" && -n "$path" ]] || return 1
  [[ "$path" == "$root" || "$path" == "$root"/* || "$root" == "$path"/* ]]
}

# acas_assert_outside_repo <label> <path>
# Refuses a write target that resolves into the frozen checkout, in either
# direction. The checkout is REFERENCE-only: "any diff touching ... is a defect
# in the migration, regardless of how harmless it appears" (AAP 0.8.1).
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
# The generic form, for roots other than the checkout -- principally the compared
# trees, whose contents are diffed byte for byte between the two cycles.
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

# =============================================================================
# TRAPS
# There is no credential FILE to shred: the password reaches the client through
# MYSQL_PWD only (see acas_sql_scalar), so it never appears in argv, never in
# `ps', and never on disk. `set -x' is never enabled anywhere in this script for
# the same reason, and no credential is ever passed to the driver or written to
# the plan, the transcript or the log.
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
# Release the sequential run lock, but only if THIS process took it, so an early
# failure can never delete a lock belonging to a live run. Reached only through
# the EXIT trap, so it must be safe to call when no lock is held.
# shellcheck disable=SC2317  # reached only through the EXIT trap installed below,
# which shellcheck cannot follow; the body is live and is exercised by the
# concurrency validation case.
acas_release_lock() {
  if (( ACAS_RUN_LOCK_HELD )) && [[ -n "$ACAS_RUN_LOCK" ]]; then
    rm -f -- "$ACAS_RUN_LOCK" 2>/dev/null || true
    ACAS_RUN_LOCK_HELD=0
  fi
}

# shellcheck disable=SC2317  # reached only through the EXIT trap installed below,
# which shellcheck cannot follow; the body is live and is exercised by every
# non-zero exit path.
acas_on_exit() {
  local status="$1"
  # FIRST, unconditionally, and before the status is even examined: a lock that
  # outlives its owner wedges every later invocation, and acas_take_lock's stale
  # reclaim exists to recover from the cases this cannot cover -- not to excuse
  # skipping it. Releasing here rather than from a lock-specific trap also means
  # there is exactly ONE EXIT trap in this script, so installing the lock can no
  # longer overwrite the reporting trap (which is what the previous
  # `trap "rm -f ...; acas_on_exit" EXIT' inside acas_take_lock did).
  acas_release_lock
  if (( status == 0 )); then
    return 0
  fi
  if (( ACAS_RUN_DRIVEN )); then
    printf '\nharness/run_cobol_scenario.sh exiting with status %s AFTER the compiled cycle\n' \
      "$status" >&2
    printf 'was driven, so the database may hold a PARTIAL result. Run harness/reset_db.sh\n' >&2
    printf 'and harness/seed.sh before drawing any conclusion from a state diff.\n' >&2
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


# USAGE
acas_usage() {
  # The delimiter is USAGE_EOF and not USAGE, because the text below uses
  # "USAGE" as a section heading on a line of its own and that would end the
  # here-document early -- silently truncating the help and leaving the rest to
  # be parsed as shell.
  cat <<'USAGE_EOF'
harness/run_cobol_scenario.sh -- drive the COMPILED ACAS Cobol posting cycle.

Stage 2 of the eight-stage parity protocol:
    seed -> run(COBOL) -> dump -> normalize -> reset -> run(Python) -> dump -> diff

This is the ORACLE side. It drives the four compiled MENU executables over a
pty, because every in-scope posting program is a CALLed sub-program with
group-item linkage and therefore cannot be invoked from a shell at all.

USAGE
    harness/run_cobol_scenario.sh [OPTIONS] [<scenario-file>]

OPTIONS
    --scenario NAME        Scenario name. Defaults to the scenario file's
                          basename without its extension.
    --scenario-file PATH   Scenario definition. Same as the positional form,
                          which exists for the canonical invocation at
                          [harness/docker-compose.yml:L346-L357].
    --subsystem NAME       One of: general sales purchase irs.
                          Optional -- it is derived from --operation, and is
                          cross-checked when both are given.
    --operation NAME       One of the seven operations, identical to the set
                          harness/run_python_scenario.sh accepts:
                              gl_post_cycle      general, load08 via "H"
                              gl_end_of_cycle    general, load09 via "I"
                              sl_invoice_post    sales,    load07 via "G"
                              sl_cash_post       sales,    load11 via "K"
                              pl_order_post      purchase, load08 via "H"
                              pl_payment_post    purchase, load12 via "L"
                              irs_post           irs,      option "4" then "66"
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
                          $ACAS_OUT/run-logs/<scenario>/fh-logger.<op>.txt.NNN --
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
    payment_post_confirm   G-3. "YES" or "NO". Default "YES".

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
    73  autocommit is off -- the frozen COBOL never reaches a COMMIT, so its
        writes would be discarded at session close
    74  a compiled artifact is missing -- run harness/build_oracle.sh
    75  the scenario file is missing or malformed
    76  the driver timed out, spun, or saw a screen refusal
    77  a post-run assertion failed
    78  a bounded command overran its deadline. Distinct from 76: 76 is the
        driver's own verdict about a screen, 78 means a deadline expired and
        the command was killed, so no verdict was reached at all.
    79  insufficient free space for the frozen fh-logger. Nothing was run and
        the database was not contacted.

This script never exits 0 unconditionally. The frozen build scripts do --
[comp-all.sh:L45] and [common/comp-common.sh:L59] -- and they are NOT fixed;
their shape is simply not adopted here.
USAGE_EOF
}

# ARGUMENT PARSING
# Both `--opt value' and `--opt=value' forms are accepted, `--' terminates the
# options, and a bare word is the scenario file. That matches harness/seed.sh so
# an operator does not have to remember which stage wants which form.
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
        ACAS_RUN_SUBSYSTEM="$2"
        shift 2
        ;;
      --subsystem=*)
        ACAS_RUN_SUBSYSTEM="${1#*=}"
        shift
        ;;
      --operation)
        [[ $# -ge 2 ]] || acas_die "$EX_USAGE" '--operation requires a name.'
        ACAS_RUN_OPERATION="$2"
        shift 2
        ;;
      --operation=*)
        ACAS_RUN_OPERATION="${1#*=}"
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
        # Retained so an existing invocation that asks for the default keeps working.
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

# SCENARIO FILE
# Read with pure shell rather than a YAML parser. Three reasons:
#   1. This stage needs a handful of SCALAR keys plus one flat LIST, and the
#      scenario files are written to that shape.
#   2. `yq' is not installed in the harness image and adding it would be a new
#      dependency for a job that does not need one.
#   3. harness/dump_tables.py already validates `affected_tables' properly with
#      PyYAML, so a second full parser here would duplicate a contract rather
#      than enforce it. This reader deliberately FAILS LOUDLY on anything it
#      does not understand instead of guessing.

# Accepted at top level only: `key: value' (optional quotes), `key:' followed
# by `  - ITEM' lines, and the inline flow form `key: [A, B, C]'. A `#' starts
# a comment except inside quotes.

# acas_scenario_scalar <key>
# Prints the value, or nothing if the key is absent.
# `_' and `-' are interchangeable in a key name, in BOTH directions, because the
# key is normalised on both sides of the comparison rather than by trying two
# spellings of the requested name. Asking for `affected-tables' therefore finds
# `affected_tables' in the file and vice versa, which is the same tolerance
# harness/dump_tables.py extends to that key.
# An explicitly empty value must be QUOTED -- `irs_instead: ""' -- because a
# bare `key:' is a block-list header in this dialect and in YAML proper is null.
# Use acas_scenario_has_key to distinguish "absent" from "present and empty";
# the difference is load-bearing for the three-state IRS fan-out switch, where
# empty means GL only [copybooks/wssystem.cob:L179-L181].
acas_scenario_scalar() {
  local key="$1"
  [[ -n "$ACAS_RUN_SCENARIO_FILE" ]] || return 0
  awk -v want="$key" '
    # Strip a trailing comment that is not inside quotes.
    function decomment(s,   i, c, q, out) {
      q = ""
      out = ""
      for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (q != "") {
          if (c == q) { q = "" }
          out = out c
          continue
        }
        if (c == "\"" || c == "'\''") { q = c; out = out c; continue }
        if (c == "#") { break }
        out = out c
      }
      return out
    }
    function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t\r]+$/, "", s); return s }
    function norm(s) { gsub(/-/, "_", s); return s }
    function unquote(s) {
      if (length(s) >= 2) {
        if (substr(s, 1, 1) == "\"" && substr(s, length(s), 1) == "\"") {
          return substr(s, 2, length(s) - 2)
        }
        if (substr(s, 1, 1) == "'\''" && substr(s, length(s), 1) == "'\''") {
          return substr(s, 2, length(s) - 2)
        }
      }
      return s
    }
    BEGIN { target = norm(want) }
    # Top level only: no leading whitespace before the key.
    /^[A-Za-z_][A-Za-z0-9_-]*[ \t]*:/ {
      line = decomment($0)
      name = line
      sub(/[ \t]*:.*$/, "", name)
      if (norm(trim(name)) != target) { next }
      value = line
      sub(/^[^:]*:[ \t]*/, "", value)
      value = trim(value)
      if (value == "") { next }          # a list header, not a scalar
      print unquote(value)
      exit
    }
  ' "$ACAS_RUN_SCENARIO_FILE"
}

# acas_scenario_has_key <key>
# True when the key appears at top level at all, whatever its value. Needed
# because an empty value is meaningful for irs_instead and must not be confused
# with the key having been forgotten.
acas_scenario_has_key() {
  local key="$1"
  [[ -n "$ACAS_RUN_SCENARIO_FILE" ]] || return 1
  awk -v want="$key" '
    function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t\r]+$/, "", s); return s }
    function norm(s) { gsub(/-/, "_", s); return s }
    BEGIN { target = norm(want); found = 0 }
    /^[A-Za-z_][A-Za-z0-9_-]*[ \t]*:/ {
      name = $0
      sub(/[ \t]*:.*$/, "", name)
      if (norm(trim(name)) == target) { found = 1; exit }
    }
    END { exit (found ? 0 : 1) }
  ' "$ACAS_RUN_SCENARIO_FILE"
}

# acas_scenario_list <key>
# Prints one item per line for a block list or an inline flow list.
acas_scenario_list() {
  local key="$1"
  [[ -n "$ACAS_RUN_SCENARIO_FILE" ]] || return 0
  awk -v want="$key" '
    function decomment(s,   i, c, q, out) {
      q = ""
      out = ""
      for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (q != "") {
          if (c == q) { q = "" }
          out = out c
          continue
        }
        if (c == "\"" || c == "'\''") { q = c; out = out c; continue }
        if (c == "#") { break }
        out = out c
      }
      return out
    }
    function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t\r]+$/, "", s); return s }
    function norm(s) { gsub(/-/, "_", s); return s }
    function unquote(s) {
      if (length(s) >= 2) {
        if (substr(s, 1, 1) == "\"" && substr(s, length(s), 1) == "\"") {
          return substr(s, 2, length(s) - 2)
        }
        if (substr(s, 1, 1) == "'\''" && substr(s, length(s), 1) == "'\''") {
          return substr(s, 2, length(s) - 2)
        }
      }
      return s
    }
    BEGIN { inlist = 0; target = norm(want) }
    {
      line = decomment($0)
      # A new top-level key ends any list we were collecting.
      if (line ~ /^[A-Za-z_][A-Za-z0-9_-]*[ \t]*:/) {
        name = line
        sub(/[ \t]*:.*$/, "", name)
        value = line
        sub(/^[^:]*:[ \t]*/, "", value)
        value = trim(value)
        if (norm(trim(name)) == target) {
          if (value == "") { inlist = 1; next }
          # Inline flow list.
          if (substr(value, 1, 1) == "[") {
            gsub(/^\[/, "", value)
            gsub(/\][ \t]*$/, "", value)
            n = split(value, parts, ",")
            for (i = 1; i <= n; i++) {
              item = unquote(trim(parts[i]))
              if (item != "") { print item }
            }
            exit
          }
          # A single scalar where a list was expected: emit it as a one-item
          # list rather than silently dropping it.
          print unquote(value)
          exit
        }
        if (inlist) { exit }
        next
      }
      if (!inlist) { next }
      item = trim(line)
      if (item == "") { next }
      if (substr(item, 1, 1) != "-") { exit }
      sub(/^-[ \t]*/, "", item)
      item = unquote(trim(item))
      if (item != "") { print item }
    }
  ' "$ACAS_RUN_SCENARIO_FILE"
}

# acas_scenario_default <key> <fallback>
acas_scenario_default() {
  local value
  value="$(acas_scenario_scalar "$1")"
  if [[ -n "$value" ]]; then
    printf '%s' "$value"
  else
    printf '%s' "$2"
  fi
}


# STAGE 1 -- resolve the scenario, the operation and the subsystem
acas_resolve_scenario() {
  ACAS_RUN_CURRENT_STAGE='resolving the scenario'
  acas_stage 'Stage 1/8: scenario, operation and subsystem'

  if [[ -n "$ACAS_RUN_SCENARIO_FILE" ]]; then
    [[ -f "$ACAS_RUN_SCENARIO_FILE" ]] || acas_die "$EX_SCENARIO" \
      "scenario file not found: $ACAS_RUN_SCENARIO_FILE" \
      'The eight scenario definitions live under harness/scenarios/.'
    [[ -r "$ACAS_RUN_SCENARIO_FILE" ]] || acas_die "$EX_SCENARIO" \
      "scenario file is not readable: $ACAS_RUN_SCENARIO_FILE"
  fi

  # The scenario NAME. Explicit option first, then the file's own key, then the
  # file's basename -- which is how harness/docker-compose.yml's canonical
  # invocation identifies a scenario, since it passes only the path.
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

  # The operation, then the subsystem it implies.
  if [[ -z "$ACAS_RUN_OPERATION" ]]; then
    ACAS_RUN_OPERATION="$(acas_scenario_scalar operation)"
  fi
  [[ -n "$ACAS_RUN_OPERATION" ]] || acas_die "$EX_USAGE" \
    'no operation was named.' \
    'Give --operation, or an operation: key in the scenario file.' \
    "The seven operations are: $(acas_join_words "${ACAS_RUN_OPERATIONS[@]}")."
  acas_in_list "$ACAS_RUN_OPERATION" "${ACAS_RUN_OPERATIONS[@]}" || acas_die "$EX_USAGE" \
    "unknown operation '$ACAS_RUN_OPERATION'." \
    "The seven operations are: $(acas_join_words "${ACAS_RUN_OPERATIONS[@]}")." \
    'This set is identical to the one harness/run_python_scenario.sh accepts, so' \
    'the two runners stay trivially comparable.'

  local entry name mapped_subsystem
  # A colon separator IS safe for this array, unlike ACAS_RUN_FORBIDDEN, and the
  # difference is worth stating so the two conventions do not look arbitrary:
  # here only the LAST field (the locator, path:Lnnn) can contain a colon, and it
  # is extracted with ${rest#*:} -- a leftmost strip that keeps the remainder
  # whole. The first four fields are colon-free identifiers. ACAS_RUN_FORBIDDEN
  # instead has a colon in a MIDDLE field, which no left-to-right strip can
  # survive, hence '|' there.
  for entry in "${ACAS_RUN_OPERATION_MAP[@]}"; do
    name="${entry%%:*}"
    if [[ "$name" == "$ACAS_RUN_OPERATION" ]]; then
      local rest="${entry#*:}"
      mapped_subsystem="${rest%%:*}"
      rest="${rest#*:}"
      ACAS_RUN_MENU_KEY="${rest%%:*}"
      rest="${rest#*:}"
      ACAS_RUN_PARAGRAPH="${rest%%:*}"
      ACAS_RUN_PARAGRAPH_LOCATOR="${rest#*:}"
      break
    fi
  done
  [[ -n "${mapped_subsystem:-}" ]] || acas_die "$EX_USAGE" \
    "internal: operation '$ACAS_RUN_OPERATION' has no menu mapping."

  # A scenario file may name the subsystem too. Every source must agree: a
  # silent override is exactly how a run ends up driving the wrong menu.
  local scenario_subsystem
  scenario_subsystem="$(acas_scenario_scalar subsystem)"
  if [[ -n "$scenario_subsystem" && "$scenario_subsystem" != "$mapped_subsystem" ]]; then
    acas_die "$EX_SCENARIO" \
      "the scenario file's subsystem does not match its operation." \
      "operation '$ACAS_RUN_OPERATION' is dispatched by the $mapped_subsystem menu," \
      "but the file says subsystem '$scenario_subsystem'."
  fi
  if [[ -n "$ACAS_RUN_SUBSYSTEM" && "$ACAS_RUN_SUBSYSTEM" != "$mapped_subsystem" ]]; then
    acas_die "$EX_USAGE" \
      "--subsystem does not match --operation." \
      "operation '$ACAS_RUN_OPERATION' is dispatched by the $mapped_subsystem menu," \
      "but --subsystem said '$ACAS_RUN_SUBSYSTEM'."
  fi
  ACAS_RUN_SUBSYSTEM="$mapped_subsystem"
  acas_in_list "$ACAS_RUN_SUBSYSTEM" "${ACAS_RUN_SUBSYSTEMS[@]}" || acas_die "$EX_USAGE" \
    "internal: unknown subsystem '$ACAS_RUN_SUBSYSTEM'."

  # AAP 0.6.4: "Sales and Purchase batches balance by construction, so the
  # control-total mismatch scenario is General-Ledger-specific -- there is no
  # meaningful way to construct an unbalanced sales batch." So this scenario is
  # refused anywhere but General rather than being run to a meaningless result.
  if [[ "$ACAS_RUN_SCENARIO" == *control_total_mismatch* && "$ACAS_RUN_SUBSYSTEM" != 'general' ]]; then
    acas_die "$EX_USAGE" \
      "the control_total_mismatch scenario is General-Ledger-specific." \
      "It was requested for subsystem '$ACAS_RUN_SUBSYSTEM'." \
      'Sales and Purchase batches balance by construction, so an unbalanced batch' \
      'cannot meaningfully be built for them; the control-total gate that this' \
      'scenario exercises lives in the General Ledger batch proof at' \
      '[general/gl051.cbl:L1109-L1118].'
  fi

  acas_log "scenario   = $ACAS_RUN_SCENARIO"
  if [[ -n "$ACAS_RUN_SCENARIO_FILE" ]]; then
    acas_log "definition = $ACAS_RUN_SCENARIO_FILE"
  else
    acas_note 'no scenario file given; every pinned value must come from an option'
  fi
  acas_log "operation  = $ACAS_RUN_OPERATION"
  acas_log "subsystem  = $ACAS_RUN_SUBSYSTEM"
  if [[ "$ACAS_RUN_SUBSYSTEM" == 'irs' ]]; then
    acas_log "menu path  = option '$ACAS_RUN_MENU_KEY' then run option '66'  [$ACAS_RUN_PARAGRAPH_LOCATOR]"
  else
    acas_log "menu path  = letter '$ACAS_RUN_MENU_KEY' -> $ACAS_RUN_PARAGRAPH  [$ACAS_RUN_PARAGRAPH_LOCATOR]"
  fi
}

# STAGE 2 -- the pinned values the scenario must supply
# Every one of these changes what the run writes, so none of them may be left to
# a default that happens to be whatever the database currently holds (R-6).
acas_resolve_pinned_values() {
  ACAS_RUN_CURRENT_STAGE='resolving the pinned scenario values'
  acas_stage 'Stage 4/8: pinned run date, date form and switches'

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
  # this script waits for is chosen from date_form: a mismatch would otherwise
  # surface only as an unexplained timeout.
  if [[ "$ACAS_RUN_DATE_FORM" == '3' && ! "$ACAS_RUN_DATE_TEXT" =~ ^[0-9]{4}/ ]]; then
    acas_die "$EX_SCENARIO" \
      "date_form 3 expects yyyy/mm/dd but run_date_text is '$ACAS_RUN_DATE_TEXT'."
  fi
  if [[ "$ACAS_RUN_DATE_FORM" != '3' && "$ACAS_RUN_DATE_TEXT" =~ ^[0-9]{4}/ ]]; then
    acas_die "$EX_SCENARIO" \
      "date_form $ACAS_RUN_DATE_FORM expects a two-digit leading field but run_date_text is '$ACAS_RUN_DATE_TEXT'."
  fi

  # The three-state IRS fan-out switch. AAP 0.6.4: "leaving it at a default would
  # make the affected-table list ambiguous", so it must be pinned EXPLICITLY --
  # which means the key has to be present even when its value is the empty
  # string that selects GL only.
  if acas_scenario_has_key irs_instead; then
    ACAS_RUN_IRS_INSTEAD="$(acas_scenario_scalar irs_instead)"
    # IRS-Instead is `pic x' [copybooks/wssystem.cob:L179], and a pic x holds a
    # SPACE for the General-Ledger-only state -- Cobol has no empty string for a
    # single-character alphanumeric field, and neither condition name matches, so
    # the state is literally a space. A scenario author writing `irs_instead: " "'
    # is therefore being MORE faithful to the frozen record than one writing "",
    # and both spellings must be accepted. Spaces are stripped here so the two
    # converge on the same internal form, which is exactly what the seeded-column
    # comparison already does to the value it reads back out of SYSTEM-REC. Do NOT
    # "tighten" this into rejecting one spelling: that turns a correct scenario
    # into a fatal error, and the two are indistinguishable once seeded.
    ACAS_RUN_IRS_INSTEAD="${ACAS_RUN_IRS_INSTEAD// /}"
  elif [[ -n "$ACAS_RUN_SCENARIO_FILE" ]]; then
    acas_die "$EX_SCENARIO" \
      'the scenario does not pin the IRS fan-out switch.' \
      'Add an irs_instead: key. It is three-state at [copybooks/wssystem.cob:L179-L181]:' \
      '    ""  General Ledger only  (a pic x holding a space; " " is accepted too)' \
      '    "Y" IRS instead of the General Ledger  (88 IRS-Used)' \
      '    "B" IRS as well as the General Ledger  (88 IRS-Both-Used)' \
      'It is tested at three sites in each of the four Sales and Purchase posting' \
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

  # G-1 -- irs030's clear-transfer-file answer. A genuine input: "Y" deletes
  # every row of PSIRSPOST-REC.
  if [[ "$ACAS_RUN_OPERATION" == 'irs_post' ]]; then
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

  # G-2 -- gl080's unconditional pre-run gate. "A" (or Escape) means gl080
  # writes nothing at all, so this too is a genuine input.
  if [[ "$ACAS_RUN_OPERATION" == 'gl_end_of_cycle' ]]; then
    ACAS_RUN_GL080_PROCEED="$(acas_scenario_default gl080_proceed 'Y')"
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
  fi

  # G-3 -- sl100 / pl100 YES/NO before posting.
  if [[ "$ACAS_RUN_OPERATION" == 'sl_cash_post' || "$ACAS_RUN_OPERATION" == 'pl_payment_post' ]]; then
    ACAS_RUN_PAYMENT_CONFIRM="$(acas_scenario_default payment_post_confirm 'YES')"
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

  # The affected-table list. This is what BOUNDS the comparison, which is how
  # the menu-exit rewrite at [general/general.cbl:L656-L692] is kept from
  # producing a spurious diff without resorting to an ignore-list.
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
        'It is required, not optional: leaving the menu with "X" rewrites SYSTEM-REC' \
        'and SYSTOT-REC, plus SYSDEFLT-REC in the General menu only' \
        '[general/general.cbl:L656-L692] vs [sales/sales.cbl:L628-L657], which the' \
        'Python side never does, so the comparison MUST be bounded by an explicit' \
        'per-scenario list rather than by an ignore-list in diff_states.py.'
    fi
    acas_note 'no affected-table list available; post-run table assertions will be skipped'
  else
    local table
    for table in "${tables[@]}"; do
      acas_in_list "$table" "${ACAS_RUN_INSCOPE_TABLES[@]}" || acas_die "$EX_SCENARIO" \
        "affected_tables names '$table', which is not one of the 22 in-scope tables." \
        "The in-scope tables are: $(acas_join_words "${ACAS_RUN_INSCOPE_TABLES[@]}")."
      # Written as an `if' and not as `acas_in_list ... && acas_die', because
      # under `set -e' a trailing `&&' whose left side FAILS makes the whole
      # compound non-zero and aborts the script on the success path.
      if (( ${#ACAS_RUN_TABLES[@]} > 0 )) && acas_in_list "$table" "${ACAS_RUN_TABLES[@]}"; then
        acas_die "$EX_SCENARIO" "affected_tables names '$table' more than once."
      fi
      ACAS_RUN_TABLES+=("$table")
    done
  fi

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

  # G-1 consistency: if irs030 may clear the transfer file, the scenario must be
  # comparing that table, or the clear is invisible to the diff.
  if [[ "$ACAS_RUN_OPERATION" == 'irs_post' && ${#ACAS_RUN_TABLES[@]} -gt 0 ]]; then
    acas_in_list 'PSIRSPOST-REC' "${ACAS_RUN_TABLES[@]}" || acas_die "$EX_SCENARIO" \
      'an irs_post scenario must list PSIRSPOST-REC in affected_tables.' \
      "irs_clear_postings is '$ACAS_RUN_IRS_CLEAR', and that answer changes the" \
      'contents of PSIRSPOST-REC [common/acas008.cbl:L313-L318]. Leaving the table' \
      'out of the comparison would make a genuine, pinned input invisible to the diff.'
  fi
}


# STAGE 3 -- the environment contract
acas_assert_environment() {
  ACAS_RUN_CURRENT_STAGE='asserting the environment contract'
  acas_stage 'Stage 2/8: environment'

  local name
  for name in "${ACAS_RUN_REQUIRED_ENV_NONEMPTY[@]}"; do
    if [[ -z "${!name:-}" ]]; then
      acas_die "$EX_PRECONDITION" \
        "$name is unset or empty." \
        'The harness environment is published by harness/docker-compose.yml; see the' \
        'canonical invocation at [harness/docker-compose.yml:L346-L357].'
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

  # The Cobol host-variable widths are hard limits, not conventions:
  # DB-Schema x(12), DB-UName x(12), DB-UPass x(12), DB-Host x(32),
  # DB-Socket x(64), DB-Port x(5)   [copybooks/wsfnctn.cob:L56-L62]
  # A longer value is silently truncated by the MOVE into the host variable, so
  # the Cobol would connect with different credentials than this script checks.
  acas_assert_width ACAS_DB_NAME 12
  acas_assert_width ACAS_DB_USER 12
  acas_assert_width ACAS_DB_PASSWORD 12
  acas_assert_width ACAS_DB_HOST 32
  acas_assert_width ACAS_DB_PORT 5
  if [[ -n "${ACAS_DB_SOCKET:-}" ]]; then
    acas_assert_width ACAS_DB_SOCKET 64
  fi
  # THE RANGE, not merely the character class. A numeric-only test admitted 0 and
  # 99999, both of which reached the python TCP probe and the client as an
  # out-of-range port and failed with a cause naming neither the variable nor the
  # value. Asserted here, once, before anything connects.
  #
  # This checks the harness environment variable, NOT the Cobol field: `DB-Port'
  # is `pic x(5)' CHARACTER data [copybooks/wsfnctn.cob:L56-L62] and its value
  # semantics are untouched -- port 65535 is five characters and fits, which is
  # exactly why the frozen field is five wide and why acas_assert_width above
  # remains the width check.
  [[ "$ACAS_DB_PORT" =~ ^[0-9]+$ ]] || acas_die "$EX_PRECONDITION" \
    "ACAS_DB_PORT must be numeric; got '$(acas_sanitise_field "$ACAS_DB_PORT")'."
  if (( 10#$ACAS_DB_PORT < 1 || 10#$ACAS_DB_PORT > 65535 )); then
    acas_die "$EX_PRECONDITION" \
      "ACAS_DB_PORT must be between 1 and 65535; got '$ACAS_DB_PORT'." \
      'A value outside the range reaches the TCP probe and the client as an' \
      'out-of-range port, which fails with a cause that names neither the' \
      'variable nor the value.'
  fi
  # Canonicalised so the port this script reports, probes and hands the client is
  # one value rather than several spellings of it. `10#' forces base-10 so a
  # leading zero is stripped rather than read as octal. Done AFTER the x(5) width
  # check, so a six-character value is still rejected on width as before.
  ACAS_DB_PORT="$(( 10#$ACAS_DB_PORT ))"

  # The schema name is embedded in an information_schema query, so it is
  # validated and escaped here rather than at the query site.
  acas_assert_schema_name

  # Decided HERE, before the readiness probe, and not lazily on first use -- see
  # acas_assert_transport_policy for why the ordering matters.
  acas_assert_transport_policy

  # The schema name is composed into SQL text and passed to the client, so it is
  # restricted to a plain identifier here -- refused rather than escaped -- before
  # anything can build a statement from it.
  acas_assert_sql_identifier 'ACAS_DB_NAME' "$ACAS_DB_NAME"
  acas_assert_sql_identifier 'ACAS_DB_USER' "$ACAS_DB_USER"

  # And it must be THE schema. The frozen mysql/ACASDB.sql contains 33 CREATE
  # TABLE statements, zero CREATE DATABASE and zero USE [mysql/ACASDB.sql], so it
  # defines exactly one database and this cycle has exactly one place to run.
  # Driving the compiled menus at a differently-named schema would either fail
  # obscurely inside COBOL or -- worse -- succeed against something else and
  # produce a state diff that looks like evidence.
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

  # [copybooks/Proc-Get-Env-Set-Files.cob:L20-L28] tests only character 1 of each
  # of these, so a value that BEGINS with a space is treated as absent and the
  # menu displays SY009, waits for a keystroke, and stops. That is a hang, and it
  # is invisible from outside, so it is checked here rather than discovered later.
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
  # there: it never cd's into it and never names it as a write target.
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
  # [general/general.cbl:L489-L503]. Its absence is NOT fatal to the Cobol, but a
  # directory whose contents change between runs would change the displayed
  # branch and therefore the transcript, so it must at least exist (D-3).
  if [[ ! -d "$ACAS_BIN" ]]; then
    mkdir -p "$ACAS_BIN" 2>/dev/null || acas_die "$EX_PRECONDITION" \
      "ACAS_BIN is not a directory and could not be created: $ACAS_BIN"
    acas_note "created ACAS_BIN so the backup-script probe takes the same branch every run"
  fi

  # python3 drives the pty. It is the ONLY option available: `expect' and `socat'
  # are not installed in the harness image, and `script -q -c' can feed a pty but
  # cannot match a prompt and then answer it, which is exactly what is required
  # here -- see WHY EVERY PROMPT IS MATCHED BEFORE IT IS ANSWERED below.
  acas_have python3 || acas_die "$EX_PRECONDITION" \
    'python3 is not on PATH.' \
    'It drives the pty, using only the standard library (pty, termios, fcntl,' \
    'struct, select, signal, os, re). harness/Dockerfile.gnucobol provides it.'

  # EVERY interpolated value below is caller-supplied, so every one goes through
  # acas_sanitise_field first: the transcript is the evidence artifact
  # docs/migration/scenario-diff-evidence.md points at, and a value carrying a
  # newline could otherwise forge a line in it. See SANITISING A VALUE BEFORE IT
  # REACHES THE TRANSCRIPT. The VALUES ARE UNCHANGED -- only their rendering is.
  acas_log "ACAS_REPO  = $(acas_sanitise_field "$ACAS_REPO") (read-only; never written, never entered)"
  acas_log "ACAS_BUILD = $(acas_sanitise_field "$ACAS_BUILD")"
  acas_log "ACAS_DATA  = $(acas_sanitise_field "$ACAS_DATA") (working directory for the run)"
  acas_log "ACAS_OUT   = $(acas_sanitise_field "$ACAS_OUT")"
  acas_log "ACAS_BIN   = $(acas_sanitise_field "$ACAS_BIN")"
  acas_log "database   = $(acas_sanitise_field "$ACAS_DB_NAME") on $(acas_sanitise_field "$ACAS_DB_HOST"):$ACAS_DB_PORT as $(acas_sanitise_field "$ACAS_DB_USER")"
  acas_note 'the database password is never logged, never placed in argv and never written to disk'
}

# acas_assert_width <env-var-name> <max>
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

# STAGE 4 -- open the transcript
# Deliberately under $ACAS_OUT/run-logs/<scenario>/ and NOT under
# $ACAS_OUT/<scenario>/. The determinism test compares scenario dumps byte for
# byte, and this transcript necessarily contains a host clock reading: the menu
# displays the host time at [general/general.cbl:L556-L557] and
# [general/gl000.cbl:L194] accepts it from TIME and displays it at 0373. A file
# containing that can never be allowed into a compared tree (R-6).
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

  # Refuse a --log that would land anywhere its contents could be mistaken for
  # evidence, or could perturb the evidence. This is a guard against an operator,
  # not against this script's own default.
  #
  # Judged on the CANONICAL path, and BEFORE mkdir -p: the previous form compared
  # the raw string against one root, which let `$ACAS_OUT/../<out>/<scenario>/x',
  # a symlink into the tree, and any relative path straight through -- and by the
  # time a later check could notice, mkdir -p had already created directories
  # inside the compared tree.
  #
  # The transcript must be excluded from comparison because it records the host
  # time the menu displays [general/general.cbl:L556-L557], which differs between
  # two runs by construction and would make every diff non-empty (R-6).
  local compared="$ACAS_OUT/$ACAS_RUN_SCENARIO"
  local suggest="$ACAS_OUT/run-logs/$ACAS_RUN_SCENARIO/cobol.log"

  acas_assert_outside_repo '--log' "$ACAS_RUN_LOG"

  # The scenario tree itself, plus each raw and normalized side beneath it. The
  # sides are named explicitly rather than relying on the parent check alone, so
  # that a future layout change which moves them out from under <scenario> does
  # not silently drop the guard.
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

  # A symlinked leaf is refused outright rather than followed. The checks above
  # already resolve it, so this only adds a clearer diagnostic -- and it prevents
  # the confusing case of a transcript that appears at one path and lands at
  # another, which makes an evidence trail unreadable.
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

  # Re-checked after creation: mkdir -p follows symlinks along the way, so the
  # path that now exists is the one to judge, not the one that was requested.
  acas_assert_outside_repo 'the transcript directory' "$dir"
  acas_assert_outside_tree 'the transcript directory' "$dir" "$compared" \
    "Use a path outside it; the default is $suggest"

  # ACAS_RUN_LOG_OPEN IS SET ONLY AFTER THE CREATE SUCCEEDS, and that ordering is
  # load-bearing rather than tidy. acas_tee appends whenever the flag is set and
  # acas_die reports through acas_tee, so raising the flag before the path was
  # proven safe would write the refusal message itself through the very symlink it
  # was refusing. Until then every diagnostic goes to the terminal only -- which
  # is also why the flag exists separately from the path (see its declaration).
  acas_create_private_file "$ACAS_RUN_LOG" 'the transcript'
  ACAS_RUN_LOG_OPEN=1

  # The plan and the outcome record get the same treatment. The outcome record in
  # particular is reopened by the embedded pty driver, which uses O_NOFOLLOW for
  # the same reason this create refuses a link.
  local plan="$dir/cobol.plan"
  local result="$dir/cobol.result"
  acas_create_private_file "$plan" 'the keystroke plan'
  acas_create_private_file "$result" "the driver's outcome record"
  ACAS_RUN_PLAN_FILE="$plan"
  ACAS_RUN_RESULT_FILE="$result"

  # No timestamp in this header, by design. The prohibition on reading the host
  # clock is absolute in this script (R-6) and a header line is not worth an
  # exception; the scenario and operation identify the run unambiguously.
  acas_tee "harness/run_cobol_scenario.sh -- scenario $ACAS_RUN_SCENARIO, operation $ACAS_RUN_OPERATION"
  acas_stage 'Stage 3/8: transcript'
  acas_log "transcript = $ACAS_RUN_LOG"
  acas_log "plan       = $ACAS_RUN_PLAN_FILE"
  acas_log "outcome    = $ACAS_RUN_RESULT_FILE"
  acas_note 'all three are OUTSIDE the compared tree, so they cannot perturb a state diff'
}

# STAGE 5 -- the compiled oracle
acas_assert_oracle() {
  ACAS_RUN_CURRENT_STAGE='asserting the compiled oracle'
  acas_stage 'Stage 5/8: compiled artifacts'

  # The four menu executables, each built with `cobc -x' by the maintainer's own
  # per-directory script. Only the one this operation needs is required to be
  # runnable, but all four are reported so a partial build is obvious.
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

  ACAS_RUN_EXECUTABLE="$ACAS_BUILD/$ACAS_RUN_SUBSYSTEM/$ACAS_RUN_SUBSYSTEM"
  if [[ ! -x "$ACAS_RUN_EXECUTABLE" ]]; then
    acas_die "$EX_ORACLE" \
      "the $ACAS_RUN_SUBSYSTEM menu executable is missing or not executable." \
      "expected: $ACAS_RUN_EXECUTABLE" \
      'Run harness/build_oracle.sh first. It performs the five-step bootstrap,' \
      'including the build rule for cobmysqlapi.o that the repository itself does' \
      'not contain -- every bridge, handler and loader links that object at' \
      '[common/comp-common.sh:L26] and following, yet no rule anywhere in the' \
      'checkout builds it, so a naive build fails at link time with no obvious cause.' \
      'Note also that the frozen build scripts end with an unconditional exit 0' \
      '-- [comp-all.sh:L45], [common/comp-common.sh:L59] -- so their exit status is' \
      'NOT a success signal and the artifacts must be checked by name, as here.'
  fi
  if (( missing )); then
    acas_warn "not every menu executable is built; only $ACAS_RUN_SUBSYSTEM is needed for this operation"
  fi

  # The `-m' modules this subsystem's menu will dynamically load. Names come from
  # the arrays harness/build_oracle.sh publishes, so the two files cannot
  # disagree about what "built" means.
  local -a modules=()
  case "$ACAS_RUN_SUBSYSTEM" in
    general)  modules=("${ACAS_RUN_GENERAL_MODULES[@]}") ;;
    sales)    modules=("${ACAS_RUN_SALES_MODULES[@]}") ;;
    purchase) modules=("${ACAS_RUN_PURCHASE_MODULES[@]}") ;;
    irs)      modules=("${ACAS_RUN_IRS_MODULES[@]}") ;;
  esac
  # Sales additionally loads sl830 before sl055 [sales/sales.cbl:L759-L760].
  # It is OUT OF SCOPE and a no-op when autogen is unused, but the menu calls it
  # unconditionally, so a missing module would abort the run inside load07.
  if [[ "$ACAS_RUN_SUBSYSTEM" == 'sales' ]]; then
    modules+=(sl830)
  fi

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

  # COB_LIBRARY_PATH must name every build directory or the menu cannot load its
  # sub-programs. This reproduces the value harness/build_oracle.sh publishes as
  # "this script's output contract to the runner scripts" rather than inventing
  # one, and it PREPENDS rather than replaces so an operator's own additions
  # survive.
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

  # GnuCobol must have a REAL indexed-file backend. system.dat is opened as a
  # Cobol INDEXED file -- [general/general.cbl:L385-L396] forces that path with
  # `move "00" to FA-RDBMS-Flat-Statuses. *> Force Cobol proc.' -- so without a
  # backend the open fails, the menu CALLs sys002 interactively, and the harness
  # hangs with no diagnostic at all.
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

# acas_module_present <name>
# A `-m' module is a shared object named after the program. GnuCobol accepts
# either the plain name or the platform suffix, so both are tried, across every
# build directory on the library path.
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


# DATABASE ACCESS
# The password reaches the client through MYSQL_PWD ONLY. It is never an argv
# element, so it never appears in `ps'; it is never written to a defaults file,
# so there is nothing to shred on exit; and it is never echoed, logged or teed.
# Identical to harness/seed.sh, deliberately.
# Every query below is a SELECT. This stage emits no DDL and no DML of any kind
# (R-3): the only thing that writes during this stage is the compiled Cobol.
# =============================================================================
# -----------------------------------------------------------------------------
# TRANSPORT SECURITY (CWE-295 improper certificate validation, CWE-319 cleartext
# transmission). The variant search used to be, unconditionally:
#
#     for variant in '' '--skip-ssl'; do          <-- the defect, as it was
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
#     none, so --skip-ssl is REQUIRED there. Removing that path would break every
#     local probe while protecting nothing.
#   * A NON-LOCAL target must present a certificate chaining to $ACAS_DB_TLS_CA
#     and matching its hostname. That is what --ssl-verify-server-cert adds;
#     without a CA it verifies nothing, so the CA is required rather than optional.
#   * Plaintext to a non-local target is permitted ONLY when
#     ACAS_DB_ALLOW_PLAINTEXT explicitly declares the network isolated. The
#     accepted values are a CLOSED set, so a typo fails closed.
#   * Anything else is REFUSED before the first connection.
#
# NOTHING ELSE CHANGES: the same two binaries are probed in the same order, the
# same four return codes are reported, and the composed argv is otherwise
# identical -- still every query a SELECT, still no --force, still no DDL and no
# DML from this script (R-3).
# -----------------------------------------------------------------------------

# True when the target is reachable without leaving the machine: a unix socket,
# an empty host, a loopback name, or a numeric loopback address. RESOLVES NOTHING
# about whether the server is trustworthy (R-6) -- it answers only "could this
# traffic be observed on a network".
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

# True when ACAS_DB_ALLOW_PLAINTEXT explicitly declares the network isolated.
# A CLOSED set of accepted spellings, so `ture' or `TRUE ' fails closed.
acas_plaintext_declared() {
  case "${ACAS_DB_ALLOW_PLAINTEXT:-}" in
    1|true|yes|on) return 0 ;;
  esac
  return 1
}

# Decide, ONCE and BEFORE ANYTHING CONNECTS, which client transports this target
# has earned. Populates ACAS_RUN_TLS_VARIANTS, most secure first, or aborts.
#
# Called from acas_assert_environment (stage 2 of 8), and NOT lazily from the
# query path: a policy that is only evaluated when a connection is first attempted
# arrives AFTER the TCP reachability probe in stage 6, so the operator would be
# told "cannot reach <host>:<port>" when the truth is "this script refuses to talk
# to it that way".
acas_assert_transport_policy() {
  local ca="${ACAS_DB_TLS_CA:-}"
  ACAS_RUN_TLS_VARIANTS=()

  if [[ -n "$ca" ]]; then
    [[ -r "$ca" ]] || acas_die "$EX_PRECONDITION" \
      "ACAS_DB_TLS_CA names a file that cannot be read: $(acas_sanitise_field "$ca")" \
      'It must be the PEM bundle the server certificate chains to.'
    # --ssl-verify-server-cert is what makes the CA meaningful: without it the
    # client encrypts but accepts any certificate, which is CWE-295 with extra
    # steps.
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

# =============================================================================
# SQL COMPOSITION SAFETY
#
# Every value that reaches SQL text does so through one of these, never by being
# interpolated between hand-written quotes. Both quoters EMIT THEIR OWN
# DELIMITERS, which is the point: a call site cannot end up writing `'$(...)''
# and re-opening the hole the helper exists to close.
#
# Two validators rather than one loosened validator, because the two alphabets
# differ for different reasons and merging them would weaken the stricter:
#   * a schema or user name comes from the environment and is bounded by the
#     COBOL RDB-Data pic x(12) field [copybooks/wsfnctn.cob:L56-L62];
#   * a table name comes from the frozen schema, which uses hyphens throughout
#     (GLLEDGER-REC) and reaches 19 characters (PUAUTOGEN-LINES-REC).
# The backtick is absent from both -- it is the character that would escape a
# quoted identifier.
# =============================================================================

# acas_assert_sql_identifier <label> <value>
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

# acas_assert_table_name <label> <value>
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

# acas_sql_quote <value>  -> 'value', escaped, WITH its own delimiters.
# ONE implementation, two published names: acas_sql_quote_literal, declared with
# the SAFE SQL COMPOSITION block above, is the implementation. Two separate
# escapers would be two places for the escaping to be got wrong.
acas_sql_quote() {
  acas_sql_quote_literal "${1-}"
}

# acas_sql_quote_ident <value>  -> `value` with embedded backticks doubled
acas_sql_quote_ident() {
  local value="$1"
  # The delimiter travels in a variable rather than inside the printf format: a
  # backtick in a single-quoted format is literal and would be correct, but it
  # reads as an attempted command substitution to both static analysis and humans.
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
  # Asserted rather than assumed, because an empty list would otherwise fall
  # straight through the loop and report a bare "the query failed" with no
  # diagnostic at all -- the least informative failure this script could produce.
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
        # A variant may carry two words (--ssl-ca=... --ssl-verify-server-cert),
        # so it is split deliberately here -- each flag must be its own argv
        # element.
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
  # connects, so `int(sys.argv[2])' here can no longer receive 99999 and fail with
  # an OverflowError that names neither the variable nor the value. The range is
  # re-checked in the probe itself because a defence that only exists at one entry
  # point is one refactor away from not existing.
  #
  # Bounded even though create_connection carries its own timeout: that timeout
  # covers the CONNECT, not the getaddrinfo() before it. A lookup against an
  # unreachable resolver blocks in libc, where no Python-level timeout reaches.
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

# acas_system_column <column>
# Read one column of the single SYSTEM-REC row. Used only for PRECONDITIONS and
# for POST-RUN OBSERVATION -- never to validate what the Cobol computed (R-3).
acas_system_column() {
  local column="$1" rc=0
  # The column name reaches SQL as a quoted identifier. Callers pass fixed names,
  # so this is defence in depth: it makes the composition correct by construction.
  acas_assert_table_name 'a SYSTEM-REC column name' "$column"
  acas_sql_scalar "select $(acas_sql_quote_ident "$column") from $(acas_sql_quote_ident 'SYSTEM-REC') limit 1;" || rc=$?
  if (( rc != 0 )); then
    return "$rc"
  fi
  printf '%s' "$ACAS_SQL_OUT"
}

# STAGE 6 -- the database
acas_assert_database() {
  ACAS_RUN_CURRENT_STAGE='asserting the database'
  acas_stage 'Stage 6/8: database, schema and the two silent-pass traps'

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
         "client diagnostic: $ACAS_SQL_DIAG" ;;
  esac

  # The frozen schema must be present. 33 CREATE TABLE statements, no ALTER and
  # no CREATE INDEX [mysql/ACASDB.sql]. Nothing here alters it (R-3).
  rc=0
  # ACAS_RUN_SCHEMA_LITERAL, not "'$ACAS_DB_NAME'": the name has been checked
  # against the allow-list and escaped for a string literal by
  # acas_assert_schema_name, and the literal ALREADY CARRIES ITS QUOTES.
  acas_sql_scalar "select count(*) from information_schema.tables where table_schema = ${ACAS_RUN_SCHEMA_LITERAL};" || rc=$?
  (( rc == 0 )) || acas_die "$EX_DATABASE" \
    'could not count the tables in the schema.' \
    "client diagnostic: $ACAS_SQL_DIAG"
  local table_count="$ACAS_SQL_OUT"
  acas_log "tables present = $table_count"
  if [[ "$table_count" == '0' ]]; then
    acas_die "$EX_DATABASE" \
      "the schema $ACAS_DB_NAME holds no tables." \
      'Apply mysql/ACASDB.sql verbatim -- harness/Dockerfile.mariadb does this -- and' \
      'then seed with harness/seed.sh. The schema is FROZEN: it is applied as it' \
      'stands and never migrated.'
  fi

  # Autocommit must be ON, because the frozen COBOL never commits.
  #
  # The loader banner at [common/glbatchLD.cbl:L9-L13] asks for OFF, but the
  # shipped code never carries that out: every `perform aa020-Rollback' is
  # commented out and `aa030-Commit' has zero perform sites in any of the 28
  # loaders, so this census returns nothing --
  #     grep -n '^ *perform.*\(aa020\|aa030\|Commit\|Rollback\)' common/*LD.cbl
  # and the posting path is the same: zero COMMIT / ROLLBACK / START TRANSACTION
  # in the twenty in-scope bridges, in the in-scope handlers and on every bridge
  # close path, with the vendored `cobmysqlapi38.c' exposing MySQL_commit
  # without ever calling it.
  #
  # With autocommit off, MariaDB opens an implicit transaction on the first DML
  # statement of a session and discards it at disconnect, so this posting run
  # would write NOTHING while the Python run -- which commits -- keeps its rows.
  # The diff would then report a harness artefact on every row.
  #
  # ASSERTED, NEVER SET: the setting has exactly one authority,
  # harness/Dockerfile.mariadb.
  rc=0
  acas_sql_scalar 'select concat_ws(0x2f, @@GLOBAL.autocommit + 0, @@SESSION.autocommit + 0);' || rc=$?
  (( rc == 0 )) || acas_die "$EX_DATABASE" \
    'could not read the autocommit settings.' \
    "client diagnostic: $ACAS_SQL_DIAG"
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
      "autocommit must be on; the server reports $autocommit (global/session)." \
      'The frozen COBOL never reaches a COMMIT: in the load programs the commit' \
      'and rollback paragraphs are unreachable, and the bridges have none --' \
      'so with autocommit off every row this posting run writes is discarded at' \
      'session close, while the Python run commits and keeps its own. The state' \
      'diff would then report a harness artefact on every row.' \
      'harness/Dockerfile.mariadb sets autocommit on for exactly this reason and' \
      'is the single authority; this script only asserts it.'
  fi

  # There must BE a system record. Without it the menu cannot start, and an empty
  # result would otherwise make every column check below vacuously pass.
  rc=0
  acas_sql_scalar "select count(*) from $(acas_sql_quote_ident 'SYSTEM-REC');" || rc=$?
  (( rc == 0 )) || acas_die "$EX_DATABASE" \
    'could not count SYSTEM-REC.' \
    "client diagnostic: $ACAS_SQL_DIAG"
  if [[ "$ACAS_SQL_OUT" == '0' ]]; then
    acas_die "$EX_PRECONDITION" \
      'SYSTEM-REC is empty: the database has not been seeded.' \
      'Run harness/seed.sh for this scenario first. It is stage 1 of the eight-stage' \
      'protocol and this is stage 2; running out of order compares nothing.' \
      'Note that the checkout ships no *.dat files, so the scenario seed data has to' \
      'be authored -- see the per-file contract at [common/masterLD.sh:L44-L115],' \
      'which harness/seed.sh reproduces rather than invokes.'
  fi

  # TRAP 1 -- FILE-SYSTEM-USED. The silent pass.
  local file_system_used
  file_system_used="$(acas_system_column 'FILE-SYSTEM-USED')" || acas_die "$EX_DATABASE" \
    'could not read SYSTEM-REC.FILE-SYSTEM-USED.' \
    "client diagnostic: $ACAS_SQL_DIAG"
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
    "client diagnostic: $ACAS_SQL_DIAG"
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
    "client diagnostic: $ACAS_SQL_DIAG"
  acas_log "DATE-FORM = $seeded_date_form (scenario says $ACAS_RUN_DATE_FORM)"
  # [general/gl000.cbl:L205] coerces an out-of-range value to 1 before choosing a
  # prompt, so the effective form -- not the stored one -- is what must match.
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
  # NOT write it: seeding is harness/seed.sh's job, and writing it here would be
  # this stage mutating the state it is about to be compared on.
  local seeded_irs
  seeded_irs="$(acas_system_column 'IRS-INSTEAD')" || acas_die "$EX_DATABASE" \
    'could not read SYSTEM-REC.IRS-INSTEAD.' \
    "client diagnostic: $ACAS_SQL_DIAG"
  # The column is char(1); a space and an empty string are the same state.
  local seeded_irs_trimmed="${seeded_irs// /}"
  acas_log "IRS-INSTEAD = '$seeded_irs_trimmed' (scenario pins '$ACAS_RUN_IRS_INSTEAD')"
  if [[ "$seeded_irs_trimmed" != "$ACAS_RUN_IRS_INSTEAD" ]]; then
    acas_die "$EX_PRECONDITION" \
      "the seeded IRS-INSTEAD ('$seeded_irs_trimmed') does not match the scenario ('$ACAS_RUN_IRS_INSTEAD')." \
      'The switch is three-state at [copybooks/wssystem.cob:L179-L181] and is tested' \
      'at three sites in each of the four Sales and Purchase posting programs, so it' \
      'decides WHICH TABLES the run touches. AAP 0.6.4: leaving it at a default' \
      '"would make the affected-table list ambiguous".' \
      'This script does not write it -- seed it with harness/seed.sh, because a run' \
      'that adjusted the state it is about to measure would not be an oracle.'
  fi

  # TRAP 2 -- SL-AUTOGEN. The determinism landmine. Sales operations only.
  if [[ "$ACAS_RUN_SUBSYSTEM" == 'sales' ]]; then
    local sl_autogen
    sl_autogen="$(acas_system_column 'SL-AUTOGEN')" || acas_die "$EX_DATABASE" \
      'could not read SYSTEM-REC.SL-AUTOGEN.' \
      "client diagnostic: $ACAS_SQL_DIAG"
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
  local flag_column='' flag_locator=''
  case "$ACAS_RUN_OPERATION" in
    sl_cash_post)    flag_column='S-FLAG-P'; flag_locator='sales/sl100.cbl:L296-L301' ;;
    pl_payment_post) flag_column='P-FLAG-P'; flag_locator='purchase/pl100.cbl:L288-L293' ;;
  esac
  if [[ -n "$flag_column" ]]; then
    local flag
    flag="$(acas_system_column "$flag_column")" || acas_die "$EX_DATABASE" \
      "could not read SYSTEM-REC.$flag_column." \
      "client diagnostic: $ACAS_SQL_DIAG"
    acas_log "$flag_column = $flag"
    if [[ "$flag" != '2' ]]; then
      acas_die "$EX_PRECONDITION" \
        "SYSTEM-REC.$flag_column is '$flag', so the posting program would exit without posting." \
        "[$flag_locator] tests the proof flag and, when it is not 2, displays a" \
        '"Payments Not Proofed" message, waits for a keystroke and go to menu-exit.' \
        'The run would therefore appear to succeed while writing nothing. Seed the' \
        'flag as 2, which is the state the proof step leaves behind.'
    fi
  fi

  # The Cobol reads its OWN credentials out of system.dat, not out of this
  # environment: SYSTEM-REC carries RDBMS-DB-NAME, RDBMS-USER, RDBMS-PASSWD,
  # RDBMS-PORT, RDBMS-HOST and RDBMS-SOCKET. If those disagree with ACAS_DB_*,
  # this script would check one database while the Cobol wrote to another.
  # Only the NON-SECRET fields are compared, and the password is never read,
  # never printed and never compared.
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
  acas_stage 'Stage 7/8: data directory'

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
# process working directory, which for this harness is $ACAS_DATA.
#
# Measured growth: 473 MB in roughly three minutes. That makes it an operational
# hazard rather than a curiosity, and the hazard has a specific shape -- a volume
# that fills DURING the run leaves the database half-posted and reports something
# unrelated as the cause.
# =============================================================================

# The rotated log is labelled and kept, never overwritten. Deterministic given the
# directory's contents, and it lives under run-logs/ which is never compared, so
# no naming choice here can perturb a state diff.
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

  # Capacity was asserted much earlier, by acas_assert_fh_log_capacity, so that a
  # volume with no room refuses before the database is contacted at all. By the
  # time rotation runs, the only remaining question is where the existing log goes.

  if [[ ! -f "$fh_log" ]]; then
    return 0
  fi

  if (( ! ACAS_RUN_ROTATE_FH_LOG )); then
    acas_warn "--no-rotate-fh-log: fh-logger.txt keeps growing from its current $fh_bytes bytes, and this run appends to it"
    return 0
  fi

  # The destination is under run-logs/<scenario>/, which is OUTSIDE every compared
  # tree, so a multi-hundred-megabyte log can never enter a dump or a diff. It is
  # also where the transcript already lives, so all of a run's evidence is together.
  local dest_dir="$ACAS_OUT/run-logs/$ACAS_RUN_SCENARIO"
  acas_assert_outside_repo 'the fh-logger rotation directory' "$dest_dir"
  acas_assert_outside_tree 'the fh-logger rotation directory' "$dest_dir" \
    "$ACAS_OUT/$ACAS_RUN_SCENARIO" \
    'The rotated log would be compared byte for byte between the two cycles, and it' \
    'records host timings, so every diff would be non-empty (R-6).'

  mkdir -p "$dest_dir" 2>/dev/null || acas_die "$EX_PRECONDITION" \
    "could not create the fh-logger rotation directory: $dest_dir"

  local rotated
  rotated="$(acas_fh_rotation_target "$dest_dir" "fh-logger.${ACAS_RUN_OPERATION}.txt")"

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

acas_plan_forbidden() {
  local entry code reason locator
  for entry in "${ACAS_RUN_FORBIDDEN[@]}"; do
    # Split on '|' -- see the note on ACAS_RUN_FORBIDDEN for why not ':'.
    IFS='|' read -r code reason locator <<<"$entry"
    acas_plan_add 0 "forbid-$code" forbid "$code" '' 0 "$reason [$locator]"
  done
}

# The date-entry step. All four menus force Date Entry on the first pass, so no
# keystroke selects it:
#     general  [general/general.cbl:L268] menu-reply pic x value "A"
#              [general/general.cbl:L506-L507] if menu-reply = "A" go to load01
#     sales    [sales/sales.cbl:L219], [sales/sales.cbl:L475-L476]
#     purchase [purchase/purchase.cbl:L215], [purchase/purchase.cbl:L469-L470]
#     irs      [irs/irs.cbl:L338] Menu-Reply pic x value "1"
#              *> Force Run Date updating at SOJ.
#              [irs/irs.cbl:L626-L630]
# Sending "A" or "1" first would therefore be a keystroke too many, and it
# would land in the date field.

# The prompt is chosen from DATE-FORM, so waiting for the specific variant also
# pins the seeded form and the typed digit order together:
#     [general/gl000.cbl:L230-L237] "Enter todays date as dd/mm/yyyy -
#                                   [          ]" ... mm/dd/yyyy ... yyyy/mm/dd
#     [irs/irs000.cbl:L222-L228]    "Enter today's date as ..."  -- with an
#                                   apostrophe, so only the tail is matched.
# The accept is ten characters wide with no AUTO
# [general/gl000.cbl:L238-L239], so it needs an explicit Return.
acas_plan_date_entry() {
  local order
  case "$ACAS_RUN_DATE_FORM" in
    1) order='dd/mm/yyyy' ;;
    2) order='mm/dd/yyyy' ;;
    3) order='yyyy/mm/dd' ;;
  esac
  # Each subsystem has its OWN date-entry program, and the citation must name the
  # one that actually runs. All four display the same three prompts and accept
  # u-date, but at different lines, and irs000 additionally spells the literal
  # with an apostrophe ("today's"), which is why the match anchor below is only
  # the shared tail "date as <order>".
  local locator
  case "$ACAS_RUN_SUBSYSTEM" in
    general)  locator='general/gl000.cbl:L230-L239'  ;;  # prompts L230/233/236, accept L239
    sales)    locator='sales/sl000.cbl:L226-L235'    ;;  # prompts L226/229/232, accept L235
    purchase) locator='purchase/pl000.cbl:L236-L245' ;;  # prompts L236/239/242, accept L245
    irs)      locator='irs/irs000.cbl:L222-L231'     ;;  # accept L231, at column 0848
  esac
  acas_plan_add 1 'date-entry' expect "date as $order" "${ACAS_RUN_DATE_TEXT}\\r" 1 \
    "pinned run date, typed in the order DATE-FORM $ACAS_RUN_DATE_FORM selects [$locator]"
}

# The three letter-menus. One character, and NO Return: the accept carries AUTO
#     [general/general.cbl:L591-L593] accept menu-reply at 0644 with ... auto UPPER
# so a single keystroke terminates it. A trailing Return would be consumed by
# whatever screen came next.
acas_plan_menu_select() {
  acas_plan_add 1 'menu-select' expect "$ACAS_RUN_MENU_ANCHOR" "$ACAS_RUN_MENU_KEY" 1 \
    "select '$ACAS_RUN_MENU_KEY' -> $ACAS_RUN_PARAGRAPH [$ACAS_RUN_PARAGRAPH_LOCATOR]"
}

# Leaving a letter-menu. "X" is tested before the ordinal search
#     [general/general.cbl:L595-L596], [sales/sales.cbl:L572],
#     [purchase/purchase.cbl:L566]
# and the exit path REWRITES system records twice -- once through the RDB and
# once through the Cobol flat file. That is left to happen: killing the menu
# instead would leave a different and non-deterministic state. The comparison
# is bounded by the scenario's affected-table list instead.

# THE EXIT SIDE EFFECT IS NOT THE SAME IN ALL FOUR MENUS, and the difference
# decides which extra tables a run touches, so it is stated per subsystem
# rather than generalised from General. Each menu's own paragraph:
#   general   keys 1, 2 AND 4 -> SYSTEM-REC, SYSDEFLT-REC, SYSTOT-REC
#             [general/general.cbl:L656-L692], and every rewrite is then
#             REPEATED against the flat file [general/general.cbl:L674-L691]
#   sales     keys 1 and 4 ONLY -> SYSTEM-REC, SYSTOT-REC. There is NO key 2
#             and therefore NO SYSDEFLT-REC write [sales/sales.cbl:L628-L657]
#   purchase  keys 1 and 4 ONLY, as Sales [purchase/purchase.cbl:L621-L651]
#   irs       key 1 ONLY -> SYSTEM-REC [irs/irs.cbl:L755-L775]

# The RDB half of each block is guarded by `if File-System-Used NOT = zero',
# which is why a zero FILE-SYSTEM-USED is asserted as a silent-pass trap: with
# it zero the RDB is never written and a diff would be empty for the wrong
# reason.
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

# Prompts that merely pause for acknowledgement (D-4). Each is conditional -- it
# fires only if the program actually reaches that error path -- so each is a
# react rule rather than an expect step, and none may change control flow.
acas_plan_ack() {
  local step="$1" pattern="$2" limit="$3" citation="$4"
  acas_plan_add 2 "$step" react "$pattern" '\r' "$limit" "$citation"
}


# gl_post_cycle -- general, letter "H", load08
# THE GENERAL GATE. [general/general.cbl:L805-L815], `*>' rule lines elided:
#     load08.
#         move     "gl070" to ws-called.
#         perform  load00.
#         if       ws-term-code = 5
#                  go to display-menu.
#         move     "gl071" to ws-called.
#         perform  load00.
#         move     "gl072" to ws-called.
#         go       to load00.
# The predicate is `ws-term-code = 5' [general/general.cbl:L810-L811].

# The code is raised inside gl070 on finding a batch left open
# [general/gl070.cbl:L287-L290]: `if a = 1 / perform gl060a / move 5 to
# ws-term-code / go to main-exit.' When it fires, gl071 and gl072 NEVER RUN AT
# ALL and the database shows none of their effects. This script neither
# implements that gate nor compensates for it: it answers whatever prompts
# appear and records which program banners were seen, so the branch taken is
# derived from the record.
# The gate path is NOT quiet, and this is the detail most likely to hang a
# harness: `perform gl060a' runs a full Batch Status Report, which paginates.
#     [general/gl070.cbl:L416]       "Enter <N> for next screen or <X> to
#                                     exit :- [ ]"
#     [general/gl070.cbl:L421-L424]  accept ws-reply, then the "X" or "x" test

#                                    and `go to end-report'
#     [general/gl070.cbl:L438-L439]  "Type return to exit." and a second accept
# Both prompts are answered. "X" leaves the report immediately, which is the
# minimum interaction that reaches end-report and closes the batch file --
# paging with "N" would produce a different number of keystrokes per scenario
# and is not needed, since the report has no database effect.
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
  acas_plan_add 2 'gl060a-page' react 'for next screen or' 'X' 12 \
    'gl060a report paging, reached ONLY when the GL gate fires [general/gl070.cbl:L416-L421]'
  acas_plan_ack 'gl060a-exit' 'Type return to exit.' 4 \
    'gl060a end-of-report acknowledgement [general/gl070.cbl:L435-L439]'

  # The gate-not-fired path: gl071 then gl072. Neither program has an accept --
  # gl071's only display is its sort banner and gl072 has none at all -- so these
  # are pure observations with nothing sent.
  acas_plan_add 2 'gl071-sort' react 'Sorting.......Please wait' '' 2 \
    'gl071 sort banner; its output ordering is what gl072 depends on [general/gl071.cbl:L170]'
  acas_plan_add 2 'gl072-phase4' react 'Phase - 4. Transaction Update' '' 2 \
    'gl072 posting banner [general/gl072.cbl:L274]'

  acas_plan_menu_exit
}

# gl_end_of_cycle -- general, letter "I", load09 -> gl080
#     [general/general.cbl:L817-L821]
# G-2. gl080 opens with an UNCONDITIONAL gate [general/gl080.cbl:L295-L302]:
#     display  GL085 ... GL086 ... GL087
#     move     space to keyed-reply.
#     accept   keyed-reply at 1065 with update auto.
#     if       cob-crt-status = cob-scr-esc
#         or   keyed-reply = "A" or "a"
#              goback.
# "A" or Escape means gl080 writes NOTHING, so the answer is a genuine input.
# Proceeding is a bare Return: the Cobol default immediately before the accept
# is `move space to keyed-reply' and Return on an AUTO field leaves it there.
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

  # GL088 -- unproofed or unposted batches present. A second gate, conditional:
  # it acknowledges and then `go to main-end' [general/gl080.cbl:L308-L313].
  acas_plan_add 2 'gl080-unproofed' react 'GL088' '\r' 2 \
    'gl080 found unproofed or unposted batches and will end after this [general/gl080.cbl:L308-L313]'
  acas_plan_ack 'gl080-note' 'GL012' 3 \
    'gl080 note-and-return acknowledgement [general/gl080.cbl:L310]'

  # GL084 sits deeper in the archive path and is a genuine choice: "<0> to
  # signify change made or <9> to abort this run". "0" continues, which is the
  # answer that lets the run complete; aborting here is not a scenario input the
  # AAP defines, so the continuing branch is taken and recorded.
  acas_plan_add 2 'gl080-archive' react 'GL084' '0\r' 3 \
    'gl080 archive-path question; 0 = change made, continue [general/gl080.cbl:L539-L545]'

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

# sl_invoice_post -- sales, letter "G", load07

# THE SALES GATE. [sales/sales.cbl:L756-L768], with its `*>' rule lines elided:
#     load07.             *> Sales trans posting
#         move     "sl830" to WS-Called.   *> In case autogen is use
#         perform  load00.
#         if       ws-term-code not = zero
#                  go to display-menu.
#         move     "sl055" to ws-called.
#         perform  load000.
#         if       ws-term-code not = zero
#                  go to display-menu.
#         move     "sl060" to ws-called.
#         go       to load000.

# The predicate is `ws-term-code not = zero' and it appears TWICE
# [sales/sales.cbl:L761-L762], [sales/sales.cbl:L765-L766]. That differs from
# General's `= 5' and from Purchase's absence, and the divergence is the
# specification: it is never harmonised (R-4).
# sl830 runs FIRST and is out of scope -- see THE sl830 ASYMMETRY above.
# load07 dispatches sl830 through load00, the FOUR-parameter shape
# [sales/sales.cbl:L677], and sl055 and sl060 through load000, the FIVE-
# parameter shape [sales/sales.cbl:L698]. Both are the menu's own behaviour,
# noted so a reader comparing the two files is not surprised.

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

  acas_plan_ack 'sl-note-error' 'SL002' 6 \
    'sl055/sl060 error acknowledgement; fires because ws-caller is "sales" [sales/sales.cbl:L481]'
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
  acas_plan_ack 'sl060-zero-value' 'SL131' 3 \
    'sl060 zero-value CR swop [sales/sl060.cbl:L265]'
  acas_plan_ack 'sl060-batch-write' 'SL132' 3 \
    'sl060 batch-file write error [sales/sl060.cbl:L266]'

  acas_plan_menu_exit
}

# sl_cash_post -- sales, letter "K", load11 -> sl100
#     [sales/sales.cbl:L792-L796]
# G-3. sl100 asks an UNCONDITIONAL YES/NO [sales/sl100.cbl:L310-L318]:
#     display  "OK to Post Payment Transactions (YES/NO) ? [   ]"  at 1212 ...
#     accept   wx-reply at 1256 with foreground-color 6 update.
#     move     function upper-case (wx-reply) to wx-reply.
#     if       wx-reply = "NO"   go to menu-exit.
#     if       wx-reply not = "YES"  go to acpt-xrply.
# NO posts nothing; anything that is neither loops. The wording differs from
# pl100's and that divergence is preserved -- the pattern here is deliberately
# specific to this program's capital "Post".
acas_plan_sl_cash_post() {
  acas_plan_date_entry
  acas_plan_menu_select

  acas_plan_add 2 'sl100-confirm' react 'OK to Post Payment Transactions' \
    "${ACAS_RUN_PAYMENT_CONFIRM}\\r" 3 \
    "G-3: sl100 posting confirmation = $ACAS_RUN_PAYMENT_CONFIRM [sales/sl100.cbl:L310-L318]"
  acas_plan_ack 'sl100-not-proofed' 'SL137' 2 \
    'sl100 payments-not-proofed; Stage 6 asserts S-FLAG-P = 2 so this should not fire [sales/sl100.cbl:L296-L301]'
  acas_plan_ack 'sl100-note-error' 'SL002' 6 \
    'sl100 error acknowledgement [sales/sl100.cbl:L211]'
  acas_plan_ack 'sl100-batch-write' 'SL132' 3 \
    'sl100 batch-file write error [sales/sl100.cbl:L214]'

  acas_plan_menu_exit
}

# pl_order_post -- purchase, letter "H", load08
# THE PURCHASE NON-GATE. [purchase/purchase.cbl:L752-L762], with its `*>' rule
# lines elided:
#     load08.
#     *>    move     "pl830" to WS-Called.   *> In case autogen is use
#     *>    perform  load000.
#     *>    if       ws-term-code not = zero
#     *>             go to display-menu.
#         move     "pl055" to ws-called.
#         perform  load000.
#         move     "pl060" to ws-called.
#         go       to load000.

# BOTH the pl830 call AND the gate are COMMENTED OUT [purchase/purchase.cbl:
# L755-L758]. Purchase has NO ABORT GATE AT ALL: pl055 is followed by pl060
# unconditionally, whatever ws-term-code holds. This is the sharpest R-4
# obligation in this file. No gate is added here in any form; it is not
# "aligned with Sales"; and it is not turned into a warning, because a warning
# that changed what this script did next would change behaviour and one that
# did not would be noise. The absence is simply recorded, and the validation
# suite asserts that pl060 still runs where Sales would have stopped -- which
# is what locks the divergence in place against a future correction.
# Purchase also does NOT run pl830, unlike Sales. That divergence is preserved
# too: no autogen program is expected, and none is answered for.
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
#     [purchase/purchase.cbl:L786-L790]
# G-3 again, but the prompt text DIVERGES from sl100's and is matched separately.
# [purchase/pl100.cbl:L302-L311]:
#     display  "OK to post payment transactions (YES/NO) ? <   > enter {CR}" ...
# Lowercase "post", ANGLE brackets, and a trailing "enter {CR}", where
# [sales/sl100.cbl:L310] has a capital "Post" and SQUARE brackets. Normalising
# the two into one pattern would erase a real difference between the programs, so
# each keeps its own (R-4).
acas_plan_pl_payment_post() {
  acas_plan_date_entry
  acas_plan_menu_select

  acas_plan_add 2 'pl100-confirm' react 'OK to post payment transactions' \
    "${ACAS_RUN_PAYMENT_CONFIRM}\\r" 3 \
    "G-3: pl100 posting confirmation = $ACAS_RUN_PAYMENT_CONFIRM; note the wording differs from sl100 [purchase/pl100.cbl:L302-L311]"
  acas_plan_ack 'pl100-not-proofed' 'PL137' 2 \
    'pl100 payments-not-proofed; Stage 6 asserts P-FLAG-P = 2 so this should not fire [purchase/pl100.cbl:L288-L293]'
  acas_plan_ack 'pl100-note-error' 'PL002' 6 \
    'pl100 error acknowledgement [purchase/pl100.cbl:L204]'
  acas_plan_ack 'pl100-batch-write' 'PL132' 3 \
    'pl100 batch-file write error [purchase/pl100.cbl:L207]'

  acas_plan_menu_exit
}

# irs_post -- irs, option "4", then irs030's OWN run option "66"
# The IRS menu is a SCREEN SECTION, not a display/accept pair
# [irs/irs.cbl:L640-L643], and its replies are DIGITS or function keys rather
# than letters. The in-scope dispatch is [irs/irs.cbl:L666-L672]:
#     if       Menu-Reply = "4"
#           or Cob-Crt-Status = Cob-Scr-F4
#              call   "irs030" using IRS-System-Params
#                                    WS-System-Record
#                                    file-defs
#              end-call
#              go to main-loop.
# Three parameters, and NEITHER a calling-data block NOR to-day -- Shape 3.

# The IRS menu derives its text date from the binary one
# [irs/irs.cbl:L632-L634] `move run-date to u-bin / perform maps04 / move
# u-date to to-day', so pinning Run-Date through Date Entry is sufficient here
# too. irs030 then presents its OWN run-option menu
# [irs/irs030.cbl:L570-L582]; the in-scope option is 66, displayed as "(<66>
# Add PL or SL Postings from file)" at [irs/irs030.cbl:L579] and dispatched at
# [irs/irs030.cbl:L601]. The accept is `w pic 99' [irs/irs030.cbl:L232] with
# UPDATE and no AUTO [irs/irs030.cbl:L582], so it needs a Return.
# Exiting irs030 is a bare Return: `Main-Loop.' begins `move zero to w'
# [irs/irs030.cbl:L571-L572], the screen offers "(<Return> to exit to System
# Menu)" [irs/irs030.cbl:L580], and `if w = zero / perform acasirsub1-Close /
# go to Main-Exit' [irs/irs030.cbl:L588-L590] then fires.

# G-1 is answered here. [irs/irs030.cbl:L1715-L1727] is paragraph EOJ-q1:
#         display  "Can I clear the Ledgers Posting file? [Y]" at 1401 ...
#         accept   WS-Reply at 1440 with foreground-color 6 UPPER.
#         if       WS-Reply not = "Y" and not = "N"
#                  go to EOJ-q1.
#         if       WS-Reply = "Y"
#                  perform acas008-Open-Output    *> a acas008-Delete-All
#                  perform acas008-Close.
# An empty reply is NOT accepted despite the "[Y]" hint, so the scenario's
# answer is mandatory. The following "Note counts and any messages" accept is a
# pure acknowledgement and gets a Return (D-4). The LIMIT on the EOJ-q1 rule
# turns a mis-keyed answer into a loud failure instead of an endless loop.
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

  # G-1. LIMIT 2 rather than 1: one legitimate appearance, and one more to catch a
  # rejected answer as a failure rather than as a hang.
  acas_plan_add 2 'irs030-clear' react 'Can I clear the Ledgers Posting' \
    "$ACAS_RUN_IRS_CLEAR" 2 \
    "G-1: clear the transfer file = $ACAS_RUN_IRS_CLEAR; \"Y\" deletes every row of PSIRSPOST-REC [irs/irs030.cbl:L1715-L1724]"
  acas_plan_ack 'irs030-note-counts' 'Note counts and any messages' 2 \
    'pure acknowledgement, no database effect [irs/irs030.cbl:L1725-L1726]'

  # Conditional error paths inside irs030. IR031 has NO accept -- it displays and
  # transfers control [irs/irs030.cbl:L1579-L1581] -- so it is observed with
  # nothing sent, which is exactly the "diagnostic with no database effect"
  # class AAP 0.3.4 turns into a log line.
  acas_plan_add 2 'irs030-no-postings' react 'IR031' '' 2 \
    'no ledger posting file found; irs030 aborts the section with no accept [irs/irs030.cbl:L1579-L1581]'
  acas_plan_ack 'irs030-vat-missing' 'IR035' 4 \
    'VAT account missing, one acknowledgement per account [irs/irs030.cbl:L1447-L1458]'
  acas_plan_ack 'irs030-irsub1-31' 'IR03A' 3 \
    'IRSUB1-31 returned an error [irs/irs030.cbl:L1596-L1600]'
  acas_plan_ack 'irs030-irsub1-32' 'IR03B' 3 \
    'IRSUB1-32 returned an error [irs/irs030.cbl:L1606-L1610]'
  acas_plan_ack 'irs030-nominal-err' 'IR912' 3 \
    'irsnominalMT error; irs030 acknowledges and gobacks [irs/irs030.cbl:L1437-L1443]'
  acas_plan_ack 'irs030-sy008' 'SY008' 4 \
    'note-message-and-hit-return [irs/irs030.cbl:L392]'

  # Back at irs030's own run-option menu: leave it with Return.
  acas_plan_add 2 'irs030-exit' terminal "$ACAS_RUN_IRS_OPTION_ANCHOR" '\r' 1 \
    'Return exits irs030 to the System Menu; Main-Loop pre-zeroes w [irs/irs030.cbl:L571-L572], [irs/irs030.cbl:L587-L589]'

  # And then leave the IRS menu itself. "X" or Escape both work
  # [irs/irs.cbl:L751-L753]; "X" is sent because it is the option the screen
  # actually offers at [irs/irs.cbl:L455].
  acas_plan_add 3 'irs-menu-exit' expect "$ACAS_RUN_IRS_MENU_ANCHOR" 'X' 1 \
    'leave the IRS menu [irs/irs.cbl:L751-L753]'
}

# Build the plan for the resolved operation.
acas_build_plan() {
  ACAS_RUN_CURRENT_STAGE='building the keystroke plan'
  acas_stage 'Stage 8/8: keystroke plan'

  # The plan file was already created safely at stage 3 (acas_open_transcript),
  # but stage 8 runs five stages later and this line EMPTIES it before the
  # builders append to it. A bare `: >' here would have undone the whole point
  # of that create: anything able to unlink the name in the interval could have
  # left a symlink behind, and the redirect would then have truncated whatever
  # it pointed at. Re-creating through the same primitive keeps the no-follow
  # refusal, the exclusive create and mode 0600 for the SECOND write as well as
  # the first, which is what closes the window rather than merely narrowing it.
  # The directory is 0700 (see acas_open_transcript), so this is defence in
  # depth over that, not a substitute for it -- that chmod is best-effort and
  # silently does nothing if the directory was not ours to change.
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

# Render the plan for a human. Sent keystrokes are shown with Return and Escape
# spelled out, because a bare control character in a log is unreadable and,
# worse, indistinguishable from no keystroke at all.
# Split $1 on TAB into ACAS_SPLIT, PRESERVING EMPTY FIELDS. `IFS=$'\t' read -r
# a b c d' cannot read this plan file, and the reason is a bash rule rather
# than a style preference: TAB is an IFS *whitespace* character, so a run of
# tabs is a SINGLE delimiter and leading and trailing ones are stripped. For
# "a<TAB>b<TAB><TAB>d" that read yields (a, b, d, "") while awk -F'\t' and
# python's str.split('\t') both yield (a, b, "", d). A react step that sends
# nothing writes two adjacent tabs, so under IFS-read the limit would print in
# the "send" column. The plan FILE and the python driver are unaffected -- the
# driver splits with str.split('\t') -- so the format is left unchanged.
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


# THE PTY DRIVER
# A REAL pty of exactly 24x80 is mandatory, for two independent reasons.
#   * Smaller than 24x80 the menu REFUSES: [general/general.cbl:L374-L383]
#     displays SY010 when `ws-env-lines < 24' and SY013 when `ws-Env-Columns <
#     80', then `goback'.
#   * Under a PIPE the gate does not save us. GnuCobol answers `accept ... from
#     lines' out of the LINES and COLUMNS variables, so the geometry test
#     passes with no terminal at all -- and then the first real `accept' reads
#     end-of-file, returns immediately, and the program SPINS, redrawing one
#     screen without limit. A hang looks like progress, which is the failure
#     mode this driver exists to make impossible.

# `pty.fork' is used rather than `script -q -c' because the driver has to MATCH
# a prompt and then answer it, and `script' can only feed a fixed stream.
# `expect' and `socat' would both do and neither is installed in the harness
# image, so the standard library is the only dependency-free option.
# ON THE CLOCK (R-6): the driver's timeouts use time.monotonic(), a relative
# interval timer. It cannot influence any value the Cobol computes, it never
# reaches the transcript, and no elapsed time is printed anywhere.
# ON MATCHING: ncurses interleaves cursor-positioning escapes with text, so the
# raw stream is unmatchable. The driver strips the escapes, collapses runs of
# whitespace and searches from an ADVANCING OFFSET, so a screen redrawn ten
# times matches once per redraw. Every pattern is a substring of a SINGLE Cobol
# `display' of a single literal, so no pattern can split across two writes.

# Exit codes, mapped to EX_DRIVE by the caller with a specific message:
#   0  every strict step matched and the reactive phase terminated cleanly
#   10 a strict step timed out          13 the menu exited before a strict step
#   11 a forbidden pattern appeared     14 the reactive phase never terminated
#   12 a react rule exceeded its limit  15 an internal driver error
acas_drive() {
  ACAS_RUN_CURRENT_STAGE='driving the compiled menu over a pty'
  acas_stage "Driving: $ACAS_RUN_SUBSYSTEM menu, operation $ACAS_RUN_OPERATION"
  acas_log "executable = $ACAS_RUN_EXECUTABLE"
  acas_log "geometry   = ${ACAS_RUN_ROWS}x${ACAS_RUN_COLS} (pinned, not 'at least')"
  acas_log "per-prompt timeout = ${ACAS_RUN_TIMEOUT}s"

  # The curses environment. The programs set the first two themselves --
  # [general/general.cbl:L369-L370] and [general/gl000.cbl:L172-L173] -- but they
  # are exported here as well so the runtime sees them from the first screen.
  # TERM must be a real terminfo entry: [common/comp-common.sh:L18] compiles
  # accept_numeric.c against ncursesw, so the runtime needs a working terminal
  # description.
  export COB_SCREEN_EXCEPTIONS='Y'
  export COB_SCREEN_ESC='Y'
  export TERM="${TERM:-xterm}"
  # D-5. Without this GnuCobol waits for a keypress when a screen program ends,
  # which would hang the harness after the menu exits. It suppresses a pause, not
  # a write.
  export COB_EXIT_WAIT='off'
  # Belt and braces with the pty winsize: GnuCobol consults these for
  # `accept ... from lines / columns', and the ioctl below sets the real thing.
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
  # [copybooks/Proc-Get-Env-Set-Files.cob:L37] zz020-Get-Program-Args accepts only
  # a blank first argument, or "NONE", "NULL" or "ACAS_LEDGERS="; anything else
  # displays SY007, waits for a keystroke and `stop run'. That is another hang, so
  # the safe argument list is the empty one.
  # An OVERALL bound on the driver, distinct from the per-prompt --timeout the
  # driver enforces internally. The two catch different failures: --timeout catches
  # "this screen never arrived", while this catches "the driver as a whole never
  # finished" -- a plan that keeps making prompt-by-prompt progress without ever
  # terminating, or a process blocked before its select loop is reached. Without
  # this, the only such failures the harness can survive are the ones the driver
  # happens to model.
  acas_deadline_prefix "$ACAS_TIMEOUT_DRIVE"
  local drive_started="$SECONDS"
  set +e
  "${ACAS_DEADLINE_ARGV[@]}" python3 - \
    "$ACAS_RUN_PLAN_FILE" \
    "$ACAS_RUN_LOG" \
    "$ACAS_RUN_RESULT_FILE" \
    "$ACAS_RUN_EXECUTABLE" \
    "$ACAS_DATA" \
    "$ACAS_RUN_ROWS" \
    "$ACAS_RUN_COLS" \
    "$ACAS_RUN_TIMEOUT" \
    <<'PY'
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
    to reach the program literally."""
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
# WRITING THE EVIDENCE, WITHOUT FOLLOWING A LINK  (CWE-59, CWE-367)
#
# acas_create_private_file already created both of these as regular files at mode
# 0600 and refused a symlink at each name -- but that was minutes ago, before the
# whole posting cycle was driven. `open(path, 'a')` and `open(path, 'w')` both
# FOLLOW a symlink, and 'w' TRUNCATES what it finds, so anything able to replace
# either name during the drive would redirect this write and read the pty
# transcript of an entire accounting run. O_NOFOLLOW closes that window at the
# only moment it is actually open.
#
# O_CREAT is deliberately absent: both files MUST already exist, because the shell
# created them. If one has vanished, that is a fact worth failing on rather than
# papering over with a fresh file.
_NOFOLLOW = getattr(os, 'O_NOFOLLOW', 0)


def _reopen(path, append):
    """Reopen a file the shell already created, refusing to follow a symlink."""
    flags = os.O_WRONLY | _NOFOLLOW | (os.O_APPEND if append else os.O_TRUNC)
    return os.fdopen(os.open(path, flags), 'w', encoding='utf-8')


transcript = clean(bytes(raw)).decode('utf-8', 'replace')
with _reopen(log_path, True) as handle:
    handle.write('\n==> pty transcript (escape sequences stripped)\n')
    handle.write(transcript)
    if not transcript.endswith('\n'):
        handle.write('\n')
    handle.write('==> end of transcript\n')

with _reopen(result_path, False) as handle:
    handle.write('child_exit\t%s\n' % ('' if child_status is None else child_status))
    handle.write('raw_bytes\t%d\n' % len(raw))
    for step, kind in matches:
        handle.write('matched\t%s\t%s\n' % (step, kind))
    if failure is not None:
        handle.write('failed\t%s\t%s\n' % (failure[0], failure[1]))
        for detail in failure[2:]:
            handle.write('detail\t%s\n' % detail)

if failure is not None:
    sys.stderr.write('driver: %s\n' % failure[1])
    for detail in failure[2:]:
        sys.stderr.write('driver:   %s\n' % detail)
    sys.exit(failure[0])
sys.exit(0)
PY
  rc=$?
  set -e

  # A deadline expiry is separated from every driver-defined status BEFORE the
  # caller classifies it. The driver's own codes (10 prompt never appeared, 11
  # refusal, 12 spinning, ...) each name a specific diagnosis, and reporting
  # "never finished" as one of them would send an operator after a defect that is
  # not there. ACAS_RUN_DRIVEN is already 1, so the exit trap still warns that the
  # database may hold a partial result.
  local drive_elapsed=$(( SECONDS - drive_started ))
  acas_assert_not_timed_out "$rc" "$drive_elapsed" "$ACAS_TIMEOUT_DRIVE" \
    'ACAS_TIMEOUT_DRIVE' 'driving the compiled menu'

  return "$rc"
}


# TRANSLATING A DRIVER FAILURE INTO SOMETHING ACTIONABLE
acas_report_drive_failure() {
  local rc="$1"
  local -a details=()
  local line kind rest

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

# acas_matched <step-id>
# Did the driver record a match for this step?
acas_matched() {
  [[ -f "$ACAS_RUN_RESULT_FILE" ]] || return 1
  grep -q -F "$(printf 'matched\t%s\t' "$1")" "$ACAS_RUN_RESULT_FILE"
}

# POST-RUN ASSERTIONS
# These check that THE HARNESS did what it set out to do. They never judge the
# accounting: no balance is recomputed, no total is checked, no posting is
# validated. harness/diff_states.py is the only thing entitled to an opinion
# about the numbers, and it forms that opinion by comparison rather than by rule.
acas_assert_after_run() {
  ACAS_RUN_CURRENT_STAGE='post-run assertions'
  acas_stage 'Post-run assertions'

  local failures=0

  # 1. The clock actually got pinned. maps04 leaves its output field UNCHANGED on
  #    a bad date [common/maps04.cbl:L146], and the caller pre-zeroes it
  #    [copybooks/Proc-ACAS-Mapser-RDB.cob:L78] -- anomaly 16 -- so a rejected date
  #    shows up either as the OLD value or as zero. Neither is detectable without
  #    reading the column back, which is why the scenario has to state the value
  #    it expects.
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
        acas_log '      date was rejected. That is anomaly 16, reproduced, not masked.'
      fi
    fi
  else
    failures=$((failures + 1))
    acas_warn 'FAIL  could not read SYSTEM-REC.RUN-DAT after the run'
  fi

  # 2. The IRS fan-out switch still holds the pinned value. Nothing in the cycle
  #    should change it; if it did, the affected-table list for this scenario no
  #    longer describes what the run touched.
  local irs_after
  if irs_after="$(acas_system_column 'IRS-INSTEAD')"; then
    irs_after="${irs_after// /}"
    if [[ "$irs_after" == "$ACAS_RUN_IRS_INSTEAD" ]]; then
      acas_log "PASS  SYSTEM-REC.IRS-INSTEAD = '$irs_after', unchanged"
    else
      failures=$((failures + 1))
      acas_warn "FAIL  SYSTEM-REC.IRS-INSTEAD changed from '$ACAS_RUN_IRS_INSTEAD' to '$irs_after' during the run"
    fi
  else
    failures=$((failures + 1))
    acas_warn 'FAIL  could not read SYSTEM-REC.IRS-INSTEAD after the run'
  fi

  # 3. Sales only: the two autogen tables must be untouched, which is what makes
  #    the sl830 asymmetry safe to live with rather than merely asserted in prose.
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

  # 4. Report which branch each divergent gate took. This is OBSERVATION, and it
  #    is deliberately not an assertion: presuming an outcome is exactly how a
  #    gate gets "helpfully" harmonised.
  case "$ACAS_RUN_OPERATION" in
    gl_post_cycle)
      local gl071_ran='no' gl072_ran='no' gate='did NOT fire'
      acas_matched 'gl071-sort' && gl071_ran='yes'
      acas_matched 'gl072-phase4' && gl072_ran='yes'
      if acas_matched 'gl060a-page' || acas_matched 'gl060a-exit'; then
        gate='FIRED'
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
        acas_log "PSIRSPOST-REC now holds $ACAS_SQL_OUT rows"
        if [[ "$ACAS_RUN_IRS_CLEAR" == 'Y' && "$ACAS_SQL_OUT" != '0' && "$cleared" != 'not asked' ]]; then
          failures=$((failures + 1))
          acas_warn "FAIL  the clear answer was Y but PSIRSPOST-REC still holds $ACAS_SQL_OUT rows; acas008 Open-Output should have performed a delete-all [common/acas008.cbl:L313-L318]"
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

  # 5. Row counts for the scenario's own tables. Reported, never judged: the
  #    comparison belongs to harness/diff_states.py, and a count here is only a
  #    breadcrumb for an operator reading the log.
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

  # 6. The file-handler log, which cannot be switched off. Reported so the growth
  #    this run caused is on the record next to the run that caused it.
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

# CLOSING REPORT
acas_run_report() {
  acas_stage 'Summary'

  acas_summary_row 'scenario' "$ACAS_RUN_SCENARIO"
  acas_summary_row 'operation' "$ACAS_RUN_OPERATION"
  acas_summary_row 'subsystem' "$ACAS_RUN_SUBSYSTEM"
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

  if (( ACAS_RUN_DRY_RUN )); then
    printf '\nDry run complete. Every precondition passed and the keystroke plan resolved.\n'
    printf 'Re-run without --dry-run to drive the compiled cycle.\n'
  else
    printf '\nThe compiled cycle ran for scenario %s.\n' "$ACAS_RUN_SCENARIO"

    # The next-step commands CARRY THE SELECTOR. Every one of them passes
    # --scenario-file, because the comparison is only evidence if it is bounded by
    # the same affected-table list the scenario declares:
    #
    #   * dump_tables.py and diff_states.py both REFUSE an unbounded run now, so a
    #     command printed without the selector would simply fail -- and worse, the
    #     obvious "fix" for that failure is --all-in-scope / --all-tables, which
    #     silently widens the comparison and turns a bounded proof into a survey.
    #   * an unbounded diff compares whatever happens to be in the two trees. If a
    #     table is missing from BOTH sides it is not compared, is not reported, and
    #     the run passes -- a false empty diff, which is the one outcome the
    #     protocol must never produce (R-6).
    #
    # Printed with the resolved scenario-file path rather than the bare name so the
    # commands can be pasted and run as they stand.
    printf '\nNext steps -- each one bounded by the scenario'"'"'s affected_tables list:\n'
    printf '  harness/dump_tables.py --scenario %s --side cobol --scenario-file %s\n' \
      "$ACAS_RUN_SCENARIO" "$ACAS_RUN_SCENARIO_FILE"
    printf '  harness/normalize.py   --scenario %s --side cobol\n' "$ACAS_RUN_SCENARIO"
    printf '  harness/reset_db.sh %s\n' "$ACAS_RUN_SCENARIO_FILE"
    printf '  harness/run_python_scenario.sh --scenario %s\n' "$ACAS_RUN_SCENARIO"
    printf '  harness/dump_tables.py --scenario %s --side python --scenario-file %s\n' \
      "$ACAS_RUN_SCENARIO" "$ACAS_RUN_SCENARIO_FILE"
    printf '  harness/normalize.py   --scenario %s --side python\n' "$ACAS_RUN_SCENARIO"
    printf '  harness/diff_states.py --scenario %s --scenario-file %s\n' \
      "$ACAS_RUN_SCENARIO" "$ACAS_RUN_SCENARIO_FILE"
    printf 'The empty diff from that last command is the pass condition (AAP 0.8.5).\n'
  fi
}

# MAIN
# Strictly sequential, one scenario at a time (R-3). There is no `&' anywhere in
# this script, no `xargs -P', and no job control: the menus already serialise the
# CALLs, and the database is shared, so two concurrent scenarios would corrupt
# each other's state and neither result would mean anything.
# A lock is taken so that a second invocation cannot start against the same
# database while this one is driving. It is advisory and it is released on exit.
# =============================================================================
# THE LOCK RECORDS ITS OWNER AND A STALE ONE IS RECLAIMED  (CWE-400 uncontrolled
# resource consumption). It used to be an EMPTY file:
#
#     if ! ( set -o noclobber; : >"$lock" ) 2>/dev/null; then     <-- the defect
#
# which is atomic, and that part was right -- but it recorded NOTHING. A container
# killed mid-run, an OOM kill, a `docker compose down' during a drive, or any exit
# path that outran the trap left a file that no later invocation could distinguish
# from a live run. The harness then refused EVERY subsequent scenario, for ever,
# and the only remedy was an operator reading the diagnostic and deleting the file
# by hand. A lock that can be permanently wedged by an abnormal exit is a denial of
# service against the harness itself.
#
# The owning pid is now written into the lock, so a later invocation can ask
# whether that process still exists:
#
#   * A LIVE holder is refused, and the diagnostic names its pid.
#   * A STALE holder -- gone, or an unreadable/garbage lock body -- is reclaimed
#     with a warning, so the harness recovers by itself.
#   * The create is still `set -C` (noclobber = O_EXCL) AFTER the reclaim, so if
#     two invocations race between the staleness check and the create, exactly one
#     wins and the loser is refused rather than both proceeding.
#
# Deliberately NOT `flock': it is not guaranteed present in the harness image, and
# a lock that silently degrades to no lock is worse than none -- the same
# reasoning harness/reset_db.sh records for the identical pattern.
#
# The lock is released only by the process that took it: ACAS_RUN_LOCK_HELD gates
# the removal, so an early failure cannot delete a lock belonging to someone else.
#
# NO SECOND EXIT TRAP IS INSTALLED HERE, and that matters for two reasons beyond
# tidiness. A trap body must never carry data: the form this replaced --
#   trap "rm -f '$lock'; acas_on_exit \"\$?\"" EXIT
# -- interpolated an operator-supplied path into the trap string, so a single
# quote in $ACAS_OUT closed the literal and the remainder ran as shell code at
# exit (CWE-78). It also passed RM's status to acas_on_exit rather than the
# script's, so the "the database may hold a PARTIAL result" warning could never
# appear. The single trap installed at the top of this script is statically
# quoted, captures the status first, and reaches the lock through
# acas_release_lock -- which is gated on ACAS_RUN_LOCK_HELD, so a refused
# acquisition can never delete the live holder's lock.
acas_take_lock() {
  ACAS_RUN_LOCK="$ACAS_OUT/run-logs/.run_cobol_scenario.lock"

  # The lock is a write target this script also DELETES, so it is canonicalised
  # and refused if it resolves into the frozen checkout.
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

  # noclobber makes the create fail if another process won the race between the
  # staleness check above and here.
  if ! (set -C; printf '%s\n' "$$" >"$ACAS_RUN_LOCK") 2>/dev/null; then
    acas_die "$EX_PRECONDITION" \
      "could not take the run lock $ACAS_RUN_LOCK." \
      'Either another run took it in the last instant, or the ACAS_OUT directory' \
      'is not writable.'
  fi
  ACAS_RUN_LOCK_HELD=1
}

acas_main() {
  # THE ORDER OF THESE SIX CALLS IS CONSTRAINED, AND THE STAGE NUMBERS FOLLOW IT
  # RATHER THAN LEADING IT. Do not reorder to make the names read alphabetically
  # or to group the "resolve" steps together:
  #   * acas_assert_environment must precede acas_open_log, because the default
  #     transcript path is derived from $ACAS_OUT and that variable is not known
  #     to be set or sane until the environment has been asserted.
  #   * acas_open_log must precede acas_resolve_pinned_values, so that the pinned
  #     date, date form and fan-out switch -- the values a later state diff is
  #     most sensitive to (R-6) -- are recorded in the transcript rather than
  #     only on the terminal.
  #   * acas_take_lock must precede everything that touches the database, to keep
  #     execution strictly sequential (R-3).
  acas_parse_args "$@"

  # FIRST, before anything can spawn an external command: resolve and freeze every
  # deadline. It validates each budget and makes them readonly, which is the
  # invariant acas_deadline_prefix relies on.
  acas_resolve_deadlines

  acas_resolve_scenario
  acas_assert_environment
  acas_open_log

  # As soon as $ACAS_DATA is known good and the transcript is open, and while a
  # refusal is still free: the frozen file-handler log cannot be switched off, so
  # a volume without room for it must stop the run BEFORE the database is
  # contacted. Placed after acas_open_log only so the refusal is recorded in the
  # transcript rather than only on the terminal.
  acas_assert_fh_log_capacity

  acas_take_lock
  acas_resolve_pinned_values
  acas_assert_oracle
  acas_assert_database
  acas_assert_data_dir
  acas_build_plan

  local rc=0
  acas_drive || rc=$?
  if (( rc != 0 )); then
    acas_report_drive_failure "$rc"
  fi

  if (( ACAS_RUN_DRY_RUN )); then
    acas_run_report
    exit "$EX_OK"
  fi

  acas_assert_after_run
  acas_run_report

  # Explicitly the success code, reached only after every assertion passed. Note
  # that this is NOT an unconditional `exit 0' bolted to the end of the file: the
  # frozen build scripts do that -- [comp-all.sh:L45] and
  # [common/comp-common.sh:L59] -- which is why their exit status carries no
  # information. Those files are not fixed (R-4); their shape is simply not
  # copied here.
  exit "$EX_OK"
}

acas_main "$@"
