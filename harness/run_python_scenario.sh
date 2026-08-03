#!/usr/bin/env bash
# harness/run_python_scenario.sh
# Drive the MIGRATED PYTHON posting cycle for one scenario, with inputs
# identical to the ones the compiled oracle was given.
#
# This is stage 6 of the eight-stage parity protocol. The eight stages, named by
# the JOB each performs rather than by the script that performs it:
#
#     1 seed        2 run(COBOL)   3 dump(cobol)   4 normalise
#     5 reset       6 run(PYTHON)  7 dump(python)  8 diff        <-- 6 is here
#
# Naming the stages by job is deliberate. A static check for stage-discipline
# violations looks for an INVOCATION of another stage's script from this file,
# and if this comment spelled those filenames the check could not tell a
# citation from a call. So it does not spell them, and there are none to spell:
# this file runs exactly two external programs -- the Python interpreter, and
# the interpreter again for the dump of stage 7.
#
# Agent Action Plan section 0.4.1.7 gives this file one line:
#
#     harness/run_python_scenario.sh | CREATE | acas_posting/cli/* |
#     "Drives the Python cycle with the IDENTICAL inputs"
#
# and section 0.3.2 says why the staging is rigid: "deterministic orchestration
# with explicit validation stages outperforms unconstrained execution", which
# "justifies the rigid stage ordering baked into the harness scripts -- seed,
# run, dump, normalize, reset, run, dump, diff -- rather than an ad-hoc
# comparison". Section 0.8.5 states the acceptance condition the pair of runners
# exists to serve: seed identically, run the compiled cycle, dump, reset, run
# the Python cycle, dump again -- "and the diff MUST be empty".
#
# NOTHING HERE JUDGES THE ACCOUNTING. This file invokes, observes and records.
# Whether the two cycles agree is decided by stage 8, from the two dumps.
#
# -----------------------------------------------------------------------------
# THE RULES THAT BIND THIS FILE
# There is NO user rules document for this project: `review_rules' reports, in
# full, "No user rules provided." The six binding rules R-1..R-6 come from the
# Agent Action Plan itself, section 0.7.2. Where they are silent this script is
# held to enterprise-standard shell practice, and nothing has been invented to
# fill a gap.
#
#   R-1  NO COBOL AT RUNTIME -- and this is the ONE file in this tree that has
#        no sanctioned exception. It compiles nothing, translates nothing and
#        runs no compiled artifact; it sets no `COB_'-prefixed environment
#        variable, allocates no pseudo-terminal, requires no screen geometry and
#        needs no terminal type, because the migrated cycle is headless. It
#        reaches the migrated command line as a SUBPROCESS and never as an
#        import: Agent Action Plan section 0.4.3 permits this tree "standard
#        library, PyYAML, driver" and forbids it the package's internals, so the
#        only Python import of the package anywhere below is the bare
#        availability probe of the package ROOT, which reaches no internals.
#        The mechanised proof of R-1 is that this script completes on a host
#        with no COBOL compiler and no COBOL runtime present.
#
#        ON THE FROZEN-SOURCE CITATIONS BELOW. Rule R-5 requires every
#        non-obvious decision to carry a [<path>:<locator>] citation, and the
#        specification being reproduced is COBOL, so those paths name COBOL
#        files. Every such path in this file is a CITATION and never an operand
#        of a command: it appears in a comment, or in the operation map from
#        which a log line is composed, or inside the text of a diagnostic or of
#        the help. None of them is ever executed, opened, compiled, translated or
#        passed to anything. That is the same convention every other file in this
#        tree follows -- the oracle-side runner carries about a hundred and thirty
#        of them outside comments and the capture tool about ten -- so the check
#        that matters is not "does the text appear" but "is any of it a command",
#        and none of it is. The one file this script names as an operand is the
#        capture tool, which is Python.
#
#   R-2  ZERO BINARY FLOATING POINT. This script performs no arithmetic on any
#        accounting value. The only numbers it computes with are row counts,
#        table counts, line counts, deadlines and exit statuses, all integers,
#        all in the shell's own integer arithmetic. It imports no data-frame or
#        array library, runs no arbitrary-precision calculator and never formats
#        a value as a floating-point number. A scenario key carrying a real
#        number is REFUSED rather than rounded.
#
#   R-3  NO NEW VALIDATIONS, NO SCHEMA CHANGE, STRICTLY SEQUENTIAL.
#        No data-definition statement of any kind is issued: every statement
#        this script sends is a SELECT, and the only tables it names come from
#        the scenario's own affected-table list plus the four autogen tables it
#        asserts are untouched. It does not seed and it does not reset -- those
#        are stages 1 and 5, and calling them from here would destroy the stage
#        ordering that R-6 depends on. Execution is strictly sequential: one
#        scenario at a time behind a run lock, and the scenario's operations one
#        after another in the order the scenario declares. There is no
#        concurrency option; the option parser's catch-all refuses any option it
#        does not know, which is how a request for concurrency is refused.
#        No business validation is added. In particular the run date is NOT
#        pre-validated, no batch is checked for existence and no account number
#        is verified. Every check below is a HARNESS precondition about the
#        harness's own environment, never an opinion about what the cycle
#        computed.
#
#   R-4  LEGACY ANOMALIES REPRODUCED, NEVER FIXED. "There is no test suite:
#        compiled COBOL execution is the behavioral specification, defects
#        included. A defect reproduced is correct; a defect fixed is a failure."
#        The sharpest obligation here is the THREE DIVERGENT ABORT GATES, and
#        the discipline is that this script does not implement any of them:
#          General   `if ws-term-code = 5 / go to display-menu'
#                    [general/general.cbl:L810-L811], inside `load08.'
#                    [general/general.cbl:L805-L815]
#          Sales     `if ws-term-code not = zero', TWICE
#                    [sales/sales.cbl:L761-L762] and [sales/sales.cbl:L765-L766],
#                    inside `load07.' [sales/sales.cbl:L756-L768]
#          Purchase  NONE -- the pl830 call AND the gate are both commented out
#                    [purchase/purchase.cbl:L755-L758], inside `load08.'
#                    [purchase/purchase.cbl:L752-L762]
#          IRS       NONE, and no dispatch wrapper at all
#                    [irs/irs.cbl:L666-L672]
#        Those gates live inside the migrated modules, which reproduce them. So
#        this script ADDS NO GATE AND REMOVES NONE, and it never decides from an
#        exit status whether to skip a later operation. It runs every operation
#        the scenario lists, in order, unconditionally. If a scenario must not
#        run a later operation, the scenario simply does not list it.
#        A CONSEQUENCE: A NON-ZERO EXIT STATUS IS FREQUENTLY THE SPECIFICATION.
#        `exit_status_for' in the migrated argument layer is the identity, so a
#        term code surfaces unchanged. Three of the twelve in-scope programs set
#        one: `move 5 to ws-term-code' [general/gl070.cbl:L289] and `move 8 to
#        WS-Term-Code' [sales/sl055.cbl:L344], [purchase/pl055.cbl:L286]. Agent
#        Action Plan section 0.6.5 says why the state capture still happens:
#        for a run-aborting rejection "the database effect is therefore THE
#        ABSENCE of everything the later phases would have written". Absence is
#        evidence. So the order is ALWAYS CAPTURE, THEN DECIDE THE STATUS.
#        And this script never ends with an unconditional success exit. The
#        frozen build scripts do -- [comp-all.sh:L45], [common/comp-common.sh:L59]
#        -- and they are NOT fixed; their shape is simply not adopted.
#
#   R-5  FULL TRACEABILITY. Every non-obvious decision below carries a
#        [<path>:<locator>] citation to the frozen source it reproduces, and
#        every deliberate deviation is annotated AS a deviation with its reason.
#        The deviations are D-1..D-8 below and the omissions are O-1..O-3.
#
#   R-6  COMPILED BEHAVIOUR IS THE TIE-BREAKER, AND THE RUN MUST BE
#        REPRODUCIBLE. "Two runs of the same scenario under the same pinned
#        clock produce byte-identical dumps." Therefore: this script NEVER READS
#        THE HOST CLOCK -- there is no call to any clock utility anywhere in it
#        -- and the run date comes from the scenario and is passed explicitly.
#        Nothing carrying a wall-clock reading, a host name, a process id, a run
#        id, an elapsed time or an absolute path is ever written under
#        $ACAS_OUT/<scenario>/. Human-facing progress text goes to
#        $ACAS_OUT/run-logs/<scenario>/python.log, which is outside every
#        compared tree by construction, and so do both seed fingerprints and the
#        run lock. The lock is the only place a process id is written, and it is
#        two directory levels away from any tree stage 8 compares.
#
# -----------------------------------------------------------------------------
# THE SEVEN OPERATIONS -- one migrated command-line module each, and the menu
# paragraph each mirrors. This set is IDENTICAL to the one the oracle-side
# runner accepts, so the two runners are trivially comparable.
#
#   gl_post_cycle    acas_posting.cli.gl_post_cycle
#                    [general/general.cbl:L805-L815]   load08, menu letter H
#   gl_end_of_cycle  acas_posting.cli.gl_end_of_cycle
#                    [general/general.cbl:L817-L821]   load09, menu letter I
#   sl_invoice_post  acas_posting.cli.sl_invoice_post
#                    [sales/sales.cbl:L756-L768]       load07, menu letter G
#   sl_cash_post     acas_posting.cli.sl_cash_post
#                    [sales/sales.cbl:L792-L796]       load11, menu letter K
#   pl_order_post    acas_posting.cli.pl_order_post
#                    [purchase/purchase.cbl:L752-L762] load08, menu letter H
#   pl_payment_post  acas_posting.cli.pl_payment_post
#                    [purchase/purchase.cbl:L786-L790] load12, menu letter L
#   irs_post         acas_posting.cli.irs_post
#                    [irs/irs.cbl:L666-L672]           menu option "4"
#
# SALES INVOICE POSTING IS load07 AND NOT load08. The label carries the
# maintainer's own comment on the label line -- `load07.  *> Sales trans
# posting' [sales/sales.cbl:L756] -- and `load08.' [sales/sales.cbl:L770]
# dispatches sl080, Payment Input, which Agent Action Plan section 0.2.2 places
# out of scope. The menu letter agrees: "(G) Sales Transactions Post"
# [sales/sales.cbl:L545] is the seventh letter.
#
# THE THREE LINKAGE SHAPES -- why there are three argument sets and not one.
# Agent Action Plan section 0.8.1: the entry points "must bind the actual
# linkage parameters, and there are THREE DISTINCT SHAPES, not one".
#   Shape 1  General Ledger, 4 parameters: `using ws-calling-data,
#            system-record, to-day, file-defs' [general/gl070.cbl:L245-L248],
#            dispatched by `load00.' [general/general.cbl:L711-L721].
#   Shape 2  Sales / Purchase, 5 parameters: `using ws-calling-data,
#            System-Record, WS-System-Record-4, to-day, file-defs'
#            [sales/sl060.cbl:L395-L399], dispatched by `load000.'
#            [sales/sales.cbl:L698-L712], [purchase/purchase.cbl:L691-L704].
#   Shape 3  IRS, 3 parameters, with NO calling-data block and NO to-day:
#            `using IRS-System-Params, WS-System-Record, File-Defs'
#            [irs/irs030.cbl:L552-L554].
# Shape 3 still takes a run date on the command line, and that is not a
# contradiction: its second parameter is the ordinary ACAS system record, which
# carries `Run-Date binary-long' [copybooks/wssystem.cob:L67]. "No to-day" never
# meant "no clock".
#
# -----------------------------------------------------------------------------
# DOCUMENTED DEVIATIONS  (R-5)
#
#   D-1  COMMAND-LINE OPTIONS INSTEAD OF KEYSTROKES. Where the oracle-side
#        runner must type into a screen, this runner passes an option. That is
#        Agent Action Plan section 0.3.4 applied: an accept that GATES A
#        DATABASE WRITE becomes "an explicit CLI parameter with the COBOL
#        default preserved". The five such accepts, and the option each became,
#        are tabulated at acas_py_operation_argv.
#
#   D-2  THE IRS FAN-OUT SWITCH IS PASSED AS THE RAW CHARACTER, NOT AS A TOKEN.
#        `05 IRS-Instead pic x.' with `88 IRS-Used value "Y".' and
#        `88 IRS-Both-Used value "B".' [copybooks/wssystem.cob:L179-L181] gives
#        the field exactly two condition names, so its three states are the
#        space the record declares, "Y" and "B". The migrated option takes ONE
#        CHARACTER and its own help says there is "no third value and in
#        particular no 'N'". So a scenario's empty or blank value is passed as a
#        single SPACE and never as a letter standing for "off": passing a letter
#        would be accepted unvalidated and would store that letter in the column
#        where the compiled cycle stores a space, which is a real difference
#        that stage 8 would report and no one would be able to explain. Y and B
#        are passed through unchanged. No fourth state is invented.
#
#   D-3  THE TWO RUNNERS TAKE THE SAME LOGICAL RUN DATE IN POSSIBLY DIFFERENT
#        LEXICAL FORMS. `Date-Form' with `88 Date-UK value 1' / `88 Date-USA
#        value 2' / `88 Date-Intl value 3' [copybooks/wssystem.cob:L128-L131]
#        decides which prompt the compiled date-entry program shows, and
#        therefore the digit order the oracle-side runner must type. The
#        migrated argument layer fixes its own accepted form at DD/MM/CCYY
#        unconditionally. So the date TEXT this script passes is the scenario's
#        `run_date_text' exactly as written, and the digits are NEVER reordered
#        to match the date form: reordering them would corrupt the pinned date.
#        The form is still passed on, because it is a field of the system record
#        and a run must pin it.
#
#   D-4  THE MENU-EXIT REWRITE HAS NO PYTHON COUNTERPART, AND THE COMPARISON IS
#        BOUNDED RATHER THAN PATCHED. Leaving a letter-menu with "X" is not
#        inert: `overrewrite.' [general/general.cbl:L656] rewrites the system
#        record, the defaults record and the totals record to the relational
#        database and then to the COBOL file, and falls through `overclose.'
#        [general/general.cbl:L693] to `goback' [general/general.cbl:L694]. The
#        Sales and Purchase menus do the same, and their dispatch helper reaches
#        it on every call. The migrated cycle has no menu and does none of it.
#        The resolution, already decided, is that the comparison is bounded by
#        the scenario's own affected-table list, which is why the state capture
#        of stage 7 is always given that list and never asked for everything.
#        It is NOT resolved with an ignore-list in the diff stage, which is
#        required to have no ignore-list, no tolerance list and no "known
#        difference" allowance. The overlap is recorded honestly: the totals
#        record IS genuinely in scope for the period-end-totals scenario,
#        because Agent Action Plan section 0.6.4 names nine period-total write
#        sites as the sole writers of it. That overlap belongs in the migration
#        documentation set's ambiguity register.
#
#   D-5  ONE PROGRAM RUNS ON THE ORACLE SIDE AND NEVER ON THIS ONE.
#        `move "sl830" to WS-Called.   *> In case autogen is use'
#        [sales/sales.cbl:L759] dispatches sl830 BEFORE sl055, corroborated by
#        the maintainer's own changelog line [sales/sales.cbl:L121]. The sales
#        autogen series is explicitly out of scope (Agent Action Plan section
#        0.2.2) and the migrated Sales invoice entry point dispatches only
#        sl055 then sl060. Because the oracle-side runner drives the MENU,
#        sl830 will execute there. The resolution is assertion, not
#        compensation: the four autogen tables are never seeded, they are never
#        on any affected-table list, and this script asserts after the run that
#        all four still hold zero rows. Purchase has no such asymmetry, because
#        its equivalent call and gate are both commented out
#        [purchase/purchase.cbl:L755-L758] -- another divergence preserved
#        rather than harmonised. Recorded for the ambiguity register.
#
#   D-6  THE STATE CAPTURE OF STAGE 7 IS PERFORMED HERE AS WELL AS BY THE
#        CANONICAL RECIPE. The committed Compose file's recipe runs stage 7 as
#        its own command, and Agent Action Plan section 0.4.1.7 requires this
#        file to take the capture too. Both are honoured: the capture is
#        idempotent -- it re-reads the same rows and rewrites the same files --
#        so a recipe that also runs stage 7 separately gets an identical tree.
#        `--no-dump' opts out for debugging. The normalise and diff stages are
#        NEVER run from here: folding them in would destroy the explicit
#        staging section 0.3.2 requires.
#
#   D-7  A DRY RUN CONTACTS NO DATABASE AND WRITES NOTHING. The oracle-side
#        runner's dry run does connect, because its preconditions are about a
#        compiled artifact and a seeded parameter file. This one deliberately
#        does not: the whole value of `--dry-run' here is to prove, before any
#        database or output area exists, that every option the scenario requires
#        is one the migrated module actually publishes. It still resolves the
#        scenario, probes the interpreter and the package, reads every module's
#        own help text and resolves every option against it.
#
#   D-8  A FAILED POST-RUN ASSERTION IS RECORDED AND THE CAPTURE IS STILL
#        TAKEN. The oracle-side runner aborts on one, which is right for a stage
#        that produces no capture. Here the capture IS the evidence, and R-4
#        requires it be taken even when the run aborted, so assertions are
#        recorded during the post-run phase and the status they imply is applied
#        only at the very end.
#
# OMISSIONS RECORDED SO A READER DOES NOT CONCLUDE SOMETHING WAS LOST  (R-5)
#
#   O-1  Accepts whose only effect is to pause for acknowledgement are dropped
#        entirely and have no option, exactly as Agent Action Plan section 0.3.4
#        directs. The clearest case is the pair immediately after the IRS
#        end-of-job clear question: `display "Note counts and any messages"' and
#        the accept under it [irs/irs030.cbl:L1725-L1726]. Their only effect is
#        to block a terminal, so there is nothing here to represent them.
#
#   O-2  Every precondition the compiled menus impose on a TERMINAL is absent
#        here, because the migrated cycle is headless. The oracle side must
#        provide a real 24x80 screen or the menu refuses to start -- it displays
#        SY010 for too few lines and SY013 for too few columns and then `goback's
#        [general/general.cbl:L374-L383] -- and must have a readable system
#        parameter file or the menu diverts into an interactive setup program
#        [general/general.cbl:L385-L396]. Neither applies to a headless command
#        line, so neither is checked, and no compiled binary, no flat data file
#        and no terminal type is required.
#
#   O-3  The compiled cycle's file-handler log has no counterpart here. Its
#        switch is frozen on and cannot be turned off, so the oracle side has to
#        reserve space for it and rotate it. The migrated cycle writes no such
#        log, so this script neither reserves space nor rotates anything.
#
# -----------------------------------------------------------------------------
# ENVIRONMENT
# The `ACAS_*' contract is the same one every other file in this tree publishes,
# so a container configured for one stage is configured for this one.
#
#   ACAS_REPO         the checkout, mounted READ-ONLY. Nothing is ever written
#                     inside it, and this script never makes it the working
#                     directory. Asserted after the run.
#   ACAS_OUT          the output area: run logs, fingerprints, the lock, and the
#                     <scenario>/python/ capture tree.
#   ACAS_DATA         declared for symmetry with the other stages; the migrated
#                     cycle needs no flat file, so it may legitimately be empty.
#   ACAS_DB_HOST      the server. `mariadb' inside the harness network.
#   ACAS_DB_PORT      3306 in the harness network.
#   ACAS_DB_NAME      must be exactly ACASDB.
#   ACAS_DB_USER      }  the credential. Width-limited, because the frozen
#   ACAS_DB_PASSWORD  }  host-variable group is `DB-Schema pic x(12)', `DB-UName
#   ACAS_DB_SOCKET    }  pic x(12)', `DB-UPass pic x(12)', `DB-Host pic x(32)',
#                     }  `DB-Socket pic x(64)', `DB-Port pic x(5)'
#                     }  [copybooks/wsfnctn.cob:L56-L62], and a longer value is
#                     }  silently shortened by the MOVE into it -- so the two
#                     }  sides of the comparison would connect as different
#                     }  accounts. Declared but may be EMPTY: the harness
#                     }  connects over TCP.
#
# HOW THE CREDENTIAL REACHES THE PYTHON SIDE. Not through a command-line option:
# the migrated entry points publish none, and none may be added. The migrated
# data-access layer takes its connection from the `RDB-Data' group
# [copybooks/wsfnctn.cob:L56-L62], and the adapter that fills that group from
# the environment reads exactly these names. So this script's job is to VERIFY
# and EXPORT them and let the child inherit them:
#
#   harness variable    migrated field   frozen declaration
#   ACAS_DB_HOST        RDBMS-Host       [copybooks/wssystem.cob:L143]
#   ACAS_DB_USER        RDBMS-User       [copybooks/wssystem.cob:L138]
#   ACAS_DB_PASSWORD    RDBMS-Passwd     [copybooks/wssystem.cob:L139]
#   ACAS_DB_NAME        RDBMS-DB-Name    [copybooks/wssystem.cob:L137]
#   ACAS_DB_PORT        RDBMS-Port       [copybooks/wssystem.cob:L142]
#   ACAS_DB_SOCKET      RDBMS-Socket     [copybooks/wssystem.cob:L144]
#
# The transport declarations ACAS_DB_TLS_CA, ACAS_DB_TLS_CERT, ACAS_DB_TLS_KEY
# and ACAS_DB_ALLOW_PLAINTEXT are passed through untouched, never invented here,
# and this script's own read-only queries obey the same fail-closed policy the
# migrated side does: a certificate authority means verified encryption, a
# loopback address or a socket needs no declaration, any other target with
# neither an authority nor an explicit declaration is REFUSED before anything
# connects.
#
# NO CREDENTIAL VALUE IS EVER PRINTED, LOGGED OR PLACED IN A COMMAND LINE. The
# password reaches nothing but the child's inherited environment. Execution
# tracing is never switched on anywhere in this file, for the same reason.
#
# THE DETERMINISM AND FREEZE BELT, applied to every interpreter invocation:
#   PYTHONPATH               $ACAS_REPO, so the package is imported from the
#                            read-only checkout. Nothing is installed into it.
#   PYTHONDONTWRITEBYTECODE  set, because importing from the checkout would
#                            otherwise try to create cache directories inside it
#                            and those would show up as a change to a frozen
#                            tree. Agent Action Plan section 0.8.1 treats ANY
#                            diff to the checkout as a defect "regardless of how
#                            harmless it appears". The read-only mount is the
#                            belt; this is the braces.
#   PYTHONSAFEPATH           set, so the current directory is NOT put at the
#                            front of the import path. Without it a directory
#                            holding a package of the same name would be imported
#                            ahead of the checkout, and this stage would read that
#                            package's options while reporting the checkout's
#                            path -- which would defeat the option-resolution
#                            check that is the whole reason this file exists.
#   PYTHONHASHSEED           0, so set and dictionary iteration cannot vary.
#   LC_ALL / LANG            C.UTF-8, so text handling cannot vary by locale.
#   TZ                       UTC, consistent with the session preamble of the
#                            frozen schema dump, which pins the time zone to
#                            +00:00.
# Warnings are deliberately NOT turned into errors: that would be a new
# validation, which R-3 forbids.
# The working directory is moved to a writable place OUTSIDE the checkout before
# anything is invoked, so no relative output path can land in a frozen tree.
#
# -----------------------------------------------------------------------------
# EXIT STATUS -- THREE CATEGORIES THAT ARE NEVER CONFLATED
#
#     0        SUCCESS. Every operation ran and behaved as the scenario says the
#              specification behaves -- INCLUDING a reproduced abort whose
#              disposition the scenario declared. The capture was taken.
#
#     69       BEHAVIOURAL DIFFERENCE. The run happened and an observed
#              disposition contradicts the scenario's declared one. THE CAPTURE
#              IS STILL TAKEN, so stage 8 can corroborate. Deliberately just
#              BELOW the fault block, so the whole vocabulary reads: 0 means the
#              two sides agreed on every disposition, 69 means they did not, and
#              70 or above means the comparison could not be performed at all.
#
#     70..79   HARNESS FAULT. The comparison could not be performed. The numbers
#              are the oracle-side runner's numbers, so an operator reads one
#              vocabulary across both runners:
#     70       usage error -- including an unknown operation, an unknown option,
#              and a command line this script itself built wrongly, which the
#              argument layer of a migrated module reports as status 2.
#     71       a precondition failed -- environment, interpreter, package,
#              driver, a required option the module does not publish, or the two
#              sides did not start from the same seed.
#     72       the database is unreachable or the schema is absent.
#     75       the scenario file is missing, malformed or incomplete.
#     77       a post-run assertion failed, or the capture of stage 7 did not
#              produce what was asked of it.
#     78       a bounded command overran its deadline, so no verdict was reached.
#
#     73, 74, 76 and 79 are DELIBERATELY UNUSED here, and their meanings are not
#     reassigned. 73 is the oracle side's autocommit refusal: on this side the
#     session policy belongs to the migrated data-access layer, which applies
#     per-statement autocommit as the compiled cycle does, so this script only
#     OBSERVES and reports the server's setting and never overrides or refuses
#     on it. 74 names a missing compiled artifact, 76 a screen driver and 79 the
#     frozen file-handler log's space reservation -- three failure modes that
#     cannot arise on a side with no COBOL in it (R-1).
# -----------------------------------------------------------------------------

set -Eeuo pipefail
# A newline-and-tab field separator, so an unquoted expansion cannot be split on
# a space. Every deliberate word split below is done with an explicit local IFS.
IFS=$'\n\t'
# `set -e' alone is NOT enough and is not relied on. A failure inside a command
# substitution, or on the left of a pipe, is not necessarily fatal, and a
# function called in a condition has `errexit' suspended for its whole body. So
# every consequential command below is checked EXPLICITLY, with its status
# captured into a variable, and no status is ever discarded.
#
# AND THE STATUS IS CAPTURED WITH `cmd || rc=$?', NEVER WITH
# `if ! cmd; then rc=$?; fi'. The second form looks equivalent and is not: the
# `!' has already inverted the status by the time the branch body runs, so `$?'
# there is ZERO for every failure, however the command failed. Written that way,
# every diagnostic below would report "status 0" and every status-dependent
# decision -- was this a deadline expiring, a bad command line, or a term code
# the frozen program set? -- would take the wrong branch. It is called out here
# because the wrong form is the one that reads naturally.

# =============================================================================
# EXIT STATUS VOCABULARY.  See the header for what each category means and why
# 73, 74, 76 and 79 are left unassigned.
# =============================================================================
readonly EX_OK=0
readonly EX_BEHAVIOUR=69      # a disposition contradicted the scenario
readonly EX_USAGE=70          # bad command line, here or one this script built
readonly EX_PRECONDITION=71   # environment, interpreter, package or option
readonly EX_DATABASE=72       # unreachable server, or the schema is not there
readonly EX_SCENARIO=75       # the scenario file is missing or incomplete
readonly EX_ASSERT=77         # a post-run assertion or the capture failed
readonly EX_TIMEOUT=78        # a bounded command overran its deadline

# =============================================================================
# DEADLINES.  Every external command runs under one, because a hang is worse
# than a failure: it looks like progress. Declared as "${VAR-}" rather than with
# a bare default so that an operator-supplied value SURVIVES to be validated --
# writing VAR='' here would discard the environment silently, which makes every
# documented knob inert and, worse, means a malformed budget is never rejected.
# =============================================================================
readonly ACAS_TIMEOUT_MAX=86400                # 24h, a ceiling on any one budget
ACAS_TIMEOUT_GRACE="${ACAS_TIMEOUT_GRACE-}"    # seconds between TERM and KILL
ACAS_TIMEOUT_CLIENT="${ACAS_TIMEOUT_CLIENT-}"  # one read-only database query
ACAS_TIMEOUT_HELP="${ACAS_TIMEOUT_HELP-}"      # one module's own help text
ACAS_TIMEOUT_OPERATION="${ACAS_TIMEOUT_OPERATION-}"  # one migrated operation
ACAS_TIMEOUT_CAPTURE="${ACAS_TIMEOUT_CAPTURE-}"      # the stage-7 capture
ACAS_TIMEOUT_RESOLVED=''                       # out-parameter of the resolver
declare -a ACAS_DEADLINE_ARGV=()               # the resolved deadline prefix

# =============================================================================
# ENVIRONMENT CONTRACT
#
# The oracle-side runner additionally requires the build tree and the two
# variables the compiled menus read for their own paths. Those are DELIBERATELY
# NOT required here (R-1): requiring a compiled build tree, or a variable whose
# only reader is a compiled menu, would import a COBOL precondition into the one
# file in this tree that must run on a host with no COBOL on it at all.
# =============================================================================
readonly -a ACAS_PY_REQUIRED_ENV_NONEMPTY=(
  ACAS_REPO ACAS_OUT
  ACAS_DB_HOST ACAS_DB_PORT ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD
)
# May legitimately be empty, but must be DECLARED: the harness connects over
# TCP, and the migrated cycle reads no flat file.
readonly -a ACAS_PY_REQUIRED_ENV_DECLARED=(
  ACAS_DB_SOCKET ACAS_DATA
)

# The one schema the frozen dump defines: it carries thirty-three table
# definitions, no database creation and no schema switch, so there is exactly
# one database this cycle can legitimately be driven against.
readonly ACAS_PY_REQUIRED_SCHEMA='ACASDB'
readonly ACAS_PY_REQUIRED_TABLES=33

# The interpreter series the project pins. A different series would compile the
# same source to different decimal behaviour in principle and to a different
# package set in practice, and the two sides of a comparison must be run by the
# interpreter the migration was built for.
readonly ACAS_PY_REQUIRED_MAJOR=3
readonly ACAS_PY_REQUIRED_MINOR=12

# The seven operation names, in the order an operator reads them. Identical to
# the set the oracle-side runner accepts.
readonly -a ACAS_PY_OPERATIONS=(
  gl_post_cycle
  gl_end_of_cycle
  sl_invoice_post
  sl_cash_post
  pl_order_post
  pl_payment_post
  irs_post
)

readonly -a ACAS_PY_SUBSYSTEMS=(general sales purchase irs)

# operation | subsystem | module | menu paragraph | locator
#
# THE FIELD SEPARATOR IS '|' AND NOT ':'. A locator is itself path:Lnnn, so a
# colon-split would cut a field short and glue its tail onto the front of the
# locator. '|' appears in no operation name, no module path and no locator.
readonly -a ACAS_PY_OPERATION_MAP=(
  'gl_post_cycle|general|acas_posting.cli.gl_post_cycle|load08|general/general.cbl:L805-L815'
  'gl_end_of_cycle|general|acas_posting.cli.gl_end_of_cycle|load09|general/general.cbl:L817-L821'
  'sl_invoice_post|sales|acas_posting.cli.sl_invoice_post|load07|sales/sales.cbl:L756-L768'
  'sl_cash_post|sales|acas_posting.cli.sl_cash_post|load11|sales/sales.cbl:L792-L796'
  'pl_order_post|purchase|acas_posting.cli.pl_order_post|load08|purchase/purchase.cbl:L752-L762'
  'pl_payment_post|purchase|acas_posting.cli.pl_payment_post|load12|purchase/purchase.cbl:L786-L790'
  'irs_post|irs|acas_posting.cli.irs_post|main-loop option 4|irs/irs.cbl:L666-L672'
)

# The 22 in-scope tables, used ONLY to check a scenario's affected-table list
# against the same vocabulary the capture stage uses. Nothing here inspects the
# schema for its own sake and nothing here alters it (R-3).
readonly -a ACAS_PY_INSCOPE_TABLES=(
  ANALYSIS-REC GLBATCH-REC GLLEDGER-REC GLPOSTING-REC
  IRSDFLT-REC IRSFINAL-REC IRSNL-REC IRSPOSTING-REC
  PSIRSPOST-REC PUINV-LINES-REC PUINVOICE-REC PUITM5-REC PULEDGER-REC
  SAINV-LINES-REC SAINVOICE-REC SAITM3-REC SALEDGER-REC
  SYSDEFLT-REC SYSFINAL-REC SYSTEM-REC SYSTOT-REC VALUEANAL-REC
)

# The four autogen tables. Never seeded -- the seed stage lists their loaders
# among the ones it never invokes -- and asserted untouched after every run,
# which is what makes deviation D-5 safe to live with rather than merely stated
# in prose. All four rather than the Sales pair the oracle side checks: the
# migrated cycle dispatches neither autogen program, so on this side all four
# must be empty, and counting four rows costs nothing.
readonly -a ACAS_PY_AUTOGEN_TABLES=(
  SAAUTOGEN-REC SAAUTOGEN-LINES-REC PUAUTOGEN-REC PUAUTOGEN-LINES-REC
)

# The IRS transfer table, named once. The end-of-job answer decides whether
# every one of its rows is removed [irs/irs030.cbl:L1723], because for that
# handler an open-for-output is not a file open but a mass delete:
# `if fn-Open and fn-output and not FS-Cobol-Files-Used / set fn-delete-all to
# true' [common/acas008.cbl:L309-L319], reinforced at [common/acas008.cbl:L571-L574].
readonly ACAS_PY_IRS_TRANSFER_TABLE='PSIRSPOST-REC'

# The name the capture stage writes LAST, recording the run identity and the
# table list it completed. It is expected in the capture tree and is not a table
# dump, so the per-table assertion below accounts for it explicitly.
readonly ACAS_PY_MANIFEST='_manifest.json'

# The side of the comparison this runner produces. The capture stage records the
# side in the PATH and never inside a file.
readonly ACAS_PY_SIDE='python'

# How wide a caller-supplied value may be rendered into the run log.
readonly ACAS_PY_LOG_FIELD_MAX=120
# How many lines of a migrated operation's own output are echoed to the console.
# The whole of it always reaches the run log; the console gets a bounded tail so
# that a long report cannot bury the summary.
readonly ACAS_PY_CONSOLE_TAIL=25

# =============================================================================
# MUTABLE STATE.  Declared up front because `set -u' makes an unset scalar or
# array a fatal reference.
# =============================================================================
ACAS_PY_SCENARIO=''             # scenario NAME
ACAS_PY_SCENARIO_FILE=''        # scenario definition path
ACAS_PY_OUT_DIR=''              # --out-dir, defaults to $ACAS_OUT
ACAS_PY_LOG=''                  # $ACAS_OUT/run-logs/<scenario>/python.log
# Whether the run log EXISTS and is writable yet, as distinct from merely having
# been named on the command line. `--log' sets the path during argument parsing,
# long before the directory exists, so a non-empty path must never on its own be
# taken as permission to append: doing so makes every diagnostic between parsing
# and opening fail its redirection, and a failed redirection is reported by the
# shell itself against whatever stderr was in force, which no suppression on the
# command can undo after the fact.
ACAS_PY_LOG_OPEN=0
ACAS_PY_WORKDIR=''              # the writable working directory, outside the checkout
ACAS_PY_DRY_RUN=0               # --dry-run
ACAS_PY_DUMP=1                  # --no-dump clears this
ACAS_PY_RAN=0                   # 1 once a migrated operation has been invoked
ACAS_PY_LOCK=''                 # the sequential-run lock
ACAS_PY_LOCK_HELD=0             # only the taker may release it
ACAS_PY_PYTHON=''               # the resolved interpreter, an absolute path
ACAS_PY_BEHAVIOURAL=0           # count of contradicted dispositions
ACAS_PY_ASSERT_FAILURES=0       # count of failed post-run assertions

# The pinned values a scenario must supply, resolved once.
ACAS_PY_RUN_DATE_TEXT=''        # `to-day pic x(10)', exactly as the scenario writes it
ACAS_PY_RUN_DATE_BINARY=''      # the expected `Run-Date' [copybooks/wssystem.cob:L67]
ACAS_PY_DATE_FORM=''            # 1 UK, 2 USA, 3 International
ACAS_PY_IRS_INSTEAD=''          # the three-state fan-out switch, as a raw character
ACAS_PY_IRS_INSTEAD_SHOWN=''    # how to render it in a log line without losing a space
ACAS_PY_IRS_CLEAR=''            # the IRS end-of-job clear answer, Y or N
ACAS_PY_GL080_PROCEED=''        # the end-of-cycle pre-run gate answer, Y or A
ACAS_PY_DISK_CHANGE=''          # the end-of-cycle disk-change option, 0 or 9
ACAS_PY_ARCHIVE_PATH=''         # the end-of-cycle archive path override, or empty
ACAS_PY_PAYMENT_CONFIRM=''      # the payment run-confirm answer, YES or NO
ACAS_PY_CALLER=''               # WS-Caller override, or empty for the route default

declare -a ACAS_PY_TABLES=()          # the scenario's affected-table list, in order
declare -a ACAS_PY_REQUESTED_OPS=()   # --operation, repeated
declare -a ACAS_PY_RUN_OPS=()         # what will actually be run, in order
declare -a ACAS_PY_EXPECTED=()        # the declared status per operation, or empty
declare -a ACAS_PY_OBSERVED=()        # the status each operation actually left
declare -a ACAS_PY_SUMMARY=()         # the closing summary table
declare -a ACAS_PY_WARN_SUMMARY=()    # non-fatal findings, replayed at the end
declare -a ACAS_PY_ARGV=()            # out-parameter of the argv builder
ACAS_PY_CAPTURE_DIR=''                # <out-dir>/<scenario>/python
ACAS_PY_FINGERPRINT=''                # this side's seed fingerprint file
# The bytecode cache directories that existed inside the checkout BEFORE this run
# invoked anything. Recorded so that the freeze check can report what THIS RUN
# created rather than what happened to be lying there: a cache directory left by
# something else is a fact worth stating, but it is not this run's doing and
# failing on it would bury a real finding under a stale one.
ACAS_PY_PYCACHE_BEFORE=''

# The scenario document, read ONCE with a real YAML parser and held here.
#   ACAS_PY_YAML_PRESENT[key]  the key appeared at top level, whatever its value
#   ACAS_PY_YAML_SCALAR[key]   its scalar value, rendered as text
#   ACAS_PY_YAML_LIST[key]     its list items, one per line, in file order
#   ACAS_PY_YAML_GROUP[key]    the key carried a nested block this stage does
#                              not read -- recorded so that a key the runner
#                              DOES read can never arrive as a block and be
#                              mistaken for an empty value
# `_' and `-' are interchangeable in a key name because every key is normalised
# to `_' on both sides of the lookup, which is the same tolerance the capture
# stage and the oracle-side runner extend.
declare -A ACAS_PY_YAML_PRESENT=()
declare -A ACAS_PY_YAML_SCALAR=()
declare -A ACAS_PY_YAML_LIST=()
declare -A ACAS_PY_YAML_GROUP=()

# The keys THIS runner reads out of a scenario document. A scenario legitimately
# carries more than these -- a nested `clock:', `system:' or `seed:' block that
# documents the seeded state, and the `seed_dir:'/`seed_files:' pair that
# harness/seed.sh reads -- and a block under a key this runner never reads is
# left alone, exactly as the oracle-side reader leaves it. A block under a key it
# DOES read is refused, because that value would read as empty and change the run
# without saying so: for the fan-out switch [copybooks/wssystem.cob:L179-L181], or
# for the affected-table list that BOUNDS the comparison, silence is the most
# expensive failure available here.
readonly ACAS_PY_SCENARIO_KEYS=(
  scenario
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
  expected_status
)

# Each module's own help text, read at most once per module, so that resolving
# twenty options costs seven interpreter starts rather than twenty.
declare -A ACAS_PY_HELP_CACHE=()

# The last read-only query's output, and the stage label the error trap reports.
ACAS_PY_SQL_OUT=''
ACAS_PY_CURRENT_STAGE=''

# =============================================================================
# REPORTING
#
# Everything printed goes to standard output and, once the log is open, to
# $ACAS_OUT/run-logs/<scenario>/python.log. NOTHING is written under
# $ACAS_OUT/<scenario>/, because a compared capture must be byte-identical
# between two runs and this log carries an elapsed time and an absolute path
# (R-6).
# =============================================================================

# Append to the run log if it is open. Silent before it is opened, so an early
# usage error still prints without needing a log.
acas_py_tee() {
  if (( ACAS_PY_LOG_OPEN )); then
    # The stderr suppression comes FIRST on purpose. Redirections are applied
    # left to right, so silencing stderr before opening the append target is
    # what actually suppresses a redirection failure; the other order lets the
    # shell's own diagnostic escape to the terminal. And a failure is not
    # swallowed: the log is marked closed, so the operator sees output stop
    # reaching it rather than seeing nothing at all.
    if ! printf '%s\n' "$*" 2>/dev/null >>"$ACAS_PY_LOG"; then
      ACAS_PY_LOG_OPEN=0
      printf 'WARNING: the run log could not be appended to and is now closed.\n' >&2
    fi
  fi
}

# Stage banners are numbered so the log reads as the deterministic staged
# orchestration the plan prescribes (R-6).
acas_py_stage() {
  printf '\n==> %s\n' "$1"
  acas_py_tee ""
  acas_py_tee "==> $1"
}

acas_py_log() {
  printf '    %s\n' "$*"
  acas_py_tee "    $*"
}

acas_py_note() {
  printf '    note: %s\n' "$*"
  acas_py_tee "    note: $*"
}

acas_py_warn() {
  printf 'WARNING: %s\n' "$*" >&2
  acas_py_tee "WARNING: $*"
  ACAS_PY_WARN_SUMMARY+=("$*")
}

# acas_py_die <exit-code> <headline> [detail-line]...
# Every abort names the setting or artifact at fault and, where the cause is
# frozen behaviour, cites its locator so the claim is traceable (R-5).
acas_py_die() {
  local code="$1"
  shift
  printf 'FATAL: %s\n' "$1" >&2
  acas_py_tee "FATAL: $1"
  shift
  local line
  for line in "$@"; do
    printf '       %s\n' "$line" >&2
    acas_py_tee "       $line"
  done
  exit "$code"
}

acas_py_have() {
  command -v "$1" >/dev/null 2>&1
}

# Join the remaining arguments with single spaces. Needed because IFS is
# $'\n\t', so a bare "${array[*]}" would join on a NEWLINE and break a one-line
# message across several lines.
acas_py_join_words() {
  local IFS=' '
  printf '%s' "$*"
}

# Join the remaining arguments with commas, for the capture stage's table list.
acas_py_join_commas() {
  local IFS=','
  printf '%s' "$*"
}

# Membership test over an array passed by expansion, so the arrays stay readonly.
# acas_py_in_list <needle> <element>...
acas_py_in_list() {
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
acas_py_summary_row() {
  ACAS_PY_SUMMARY+=("$(printf '%-24s %s' "$1" "$2")")
}

# -----------------------------------------------------------------------------
# NEUTRALISING A VALUE BEFORE IT REACHES THE RUN LOG
# (CWE-117 log injection, CWE-532 sensitive information in a log)
#
# Environment values, scenario values and table names are all caller-supplied. A
# value carrying a newline forges an arbitrary log line -- including a plausible
# "PASS" or "==> Stage" banner -- and one carrying an escape or another control
# writes a terminal escape sequence into a file an operator is told to read. The
# run log is EVIDENCE: it is what the migration's scenario-diff evidence document
# points at, so a forgeable line is a forgeable finding.
#
# NEUTRALISED, NOT REJECTED. These values are already width-checked against the
# frozen host-variable limits [copybooks/wsfnctn.cob:L56-L62] and a legitimate
# one contains no control character at all, so rendering it safely loses nothing
# real, while an outright refusal would turn a cosmetic mistake into an abort.
# `LC_ALL=C tr' works on BYTES, which is what is wanted: a multi-byte character
# cannot smuggle a control past a byte-wise class.
# -----------------------------------------------------------------------------
acas_py_sanitise_field() {
  local value="$1"
  value="$(printf '%s' "$value" | LC_ALL=C tr '\000-\037\177' '?')"
  value="$(printf '%s' "$value" | LC_ALL=C tr -d '\200-\237')"
  if (( ${#value} > ACAS_PY_LOG_FIELD_MAX )); then
    value="${value:0:ACAS_PY_LOG_FIELD_MAX}...<clipped>"
  fi
  printf '%s' "$value"
}

# Render a value that may be a single space, so a log line cannot lose it. Used
# for the fan-out switch, whose General-Ledger-only state IS a space (D-2).
acas_py_render_char() {
  local value="$1"
  case "$value" in
    '')  printf '<empty>' ;;
    ' ') printf '<space>' ;;
    *)   printf '%s' "$(acas_py_sanitise_field "$value")" ;;
  esac
}

# =============================================================================
# PATH SAFETY
#
# Every path this script writes to is canonicalised and then refused if it lands
# inside the frozen checkout, or inside a tree stage 8 compares. Canonicalisation
# happens BEFORE the working directory is moved, so a relative path given on the
# command line keeps the meaning the operator intended.
# =============================================================================

# Resolve symlinks and anchor a relative path, for a path that may not exist yet.
acas_py_canonical_path() {
  local path="$1" probe parent tail=''

  if [[ -z "$path" ]]; then
    printf '%s' ''
    return 0
  fi
  if [[ "$path" != /* ]]; then
    path="$PWD/$path"
  fi

  # Walk up to the deepest component that exists, resolve that, then re-attach
  # the part that does not exist yet.
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
  if ! resolved="$(readlink -f -- "$probe" 2>/dev/null)"; then
    resolved="$probe"
  fi
  if [[ -n "$tail" ]]; then
    tail="${tail%/}"
    resolved="${resolved%/}/$tail"
  fi
  printf '%s' "$resolved"
}

# True when <path> IS <root>, lies beneath it, or contains it. Both arguments
# must already be canonical. Containment is tested in BOTH directions because a
# parent of a protected tree is just as unsafe a write target as a child of it.
acas_py_path_contains() {
  local root="${1%/}" path="${2%/}"
  [[ -n "$root" && -n "$path" ]] || return 1
  [[ "$path" == "$root" || "$path" == "$root"/* || "$root" == "$path"/* ]]
}

# acas_py_assert_outside_repo <label> <path>
# The checkout is REFERENCE-only: "any diff touching ... is a defect in the
# migration, regardless of how harmless it appears" (Agent Action Plan 0.8.1).
acas_py_assert_outside_repo() {
  local label="$1" path="$2" repo_real target
  repo_real="$(acas_py_canonical_path "${ACAS_REPO:-}")"
  target="$(acas_py_canonical_path "$path")"

  if [[ -n "$repo_real" ]] && acas_py_path_contains "$repo_real" "$target"; then
    acas_py_die "$EX_PRECONDITION" \
      "$label resolves inside the frozen checkout." \
      "  requested : $(acas_py_sanitise_field "$path")" \
      "  resolves  : $(acas_py_sanitise_field "$target")" \
      "  checkout  : $(acas_py_sanitise_field "$repo_real")" \
      'The checkout is read-only specification. Point it at the writable output' \
      'area named by ACAS_OUT instead.'
  fi
}

# acas_py_assert_outside_tree <label> <path> <protected-root> <why>...
# For the compared trees, whose contents stage 8 diffs byte for byte. A run log
# or a fingerprint written into one of them would be diffed as though it were
# posted data and would corrupt the parity evidence (R-6).
acas_py_assert_outside_tree() {
  local label="$1" path="$2" root="$3"
  shift 3
  local root_real target
  root_real="$(acas_py_canonical_path "$root")"
  target="$(acas_py_canonical_path "$path")"

  if acas_py_path_contains "$root_real" "$target"; then
    acas_py_die "$EX_USAGE" \
      "$label resolves inside $(acas_py_sanitise_field "$root_real")" \
      "  requested : $(acas_py_sanitise_field "$path")" \
      "  resolves  : $(acas_py_sanitise_field "$target")" \
      "$@"
  fi
}

# =============================================================================
# DEADLINES
# =============================================================================

# acas_py_timeout_seconds <env-var-name> <default>
# Validates one budget and publishes it in ACAS_TIMEOUT_RESOLVED.
acas_py_timeout_seconds() {
  local name="$1" default="$2" value
  ACAS_TIMEOUT_RESOLVED=''
  value="${!name-}"
  [[ -n "$value" ]] || value="$default"

  if [[ ! "$value" =~ ^[0-9]+$ ]]; then
    acas_py_die "$EX_USAGE" \
      "$name must be a whole number of seconds; got '$(acas_py_sanitise_field "$value")'." \
      'Leave it unset or empty to take the default.'
  fi
  # Base ten explicitly, so a value such as 08 is a plain number and not octal.
  value=$(( 10#$value ))
  if (( value < 1 )); then
    acas_py_die "$EX_USAGE" \
      "$name must be at least 1 second; got '$value'." \
      'A zero or negative budget would mean no deadline at all, and every external' \
      'command this script runs is a hang risk.'
  fi
  if (( value > ACAS_TIMEOUT_MAX )); then
    acas_py_die "$EX_USAGE" \
      "$name must be at most $ACAS_TIMEOUT_MAX seconds; got '$value'."
  fi
  ACAS_TIMEOUT_RESOLVED="$value"
}

# Resolve and FREEZE every budget, before anything can spawn a child.
acas_py_resolve_deadlines() {
  acas_py_have timeout || acas_py_die "$EX_PRECONDITION" \
    'timeout is not on the PATH.' \
    'It is part of coreutils, and every external process this script spawns runs' \
    'under it so that no stage of the protocol can hang.'

  acas_py_timeout_seconds ACAS_TIMEOUT_GRACE 15
  ACAS_TIMEOUT_GRACE="$ACAS_TIMEOUT_RESOLVED"
  acas_py_timeout_seconds ACAS_TIMEOUT_CLIENT 60
  ACAS_TIMEOUT_CLIENT="$ACAS_TIMEOUT_RESOLVED"
  acas_py_timeout_seconds ACAS_TIMEOUT_HELP 120
  ACAS_TIMEOUT_HELP="$ACAS_TIMEOUT_RESOLVED"
  acas_py_timeout_seconds ACAS_TIMEOUT_OPERATION 3600
  ACAS_TIMEOUT_OPERATION="$ACAS_TIMEOUT_RESOLVED"
  acas_py_timeout_seconds ACAS_TIMEOUT_CAPTURE 1800
  ACAS_TIMEOUT_CAPTURE="$ACAS_TIMEOUT_RESOLVED"
  readonly ACAS_TIMEOUT_GRACE ACAS_TIMEOUT_CLIENT ACAS_TIMEOUT_HELP
  readonly ACAS_TIMEOUT_OPERATION ACAS_TIMEOUT_CAPTURE
}

# acas_py_deadline_prefix <budget-seconds>
# Publishes the command prefix in ACAS_DEADLINE_ARGV. TERM first so a child can
# clean up, KILL after the grace period so one that ignores TERM still dies.
acas_py_deadline_prefix() {
  local budget="$1"
  [[ "$budget" =~ ^[1-9][0-9]*$ ]] || acas_py_die "$EX_PRECONDITION" \
    "a deadline prefix was requested with a non-positive budget: '$budget'." \
    'Budgets are resolved and frozen before anything spawns.'
  ACAS_DEADLINE_ARGV=(
    timeout
    "--kill-after=$ACAS_TIMEOUT_GRACE"
    --signal=TERM
    "$budget"
  )
}

# acas_py_is_timeout_status <rc> <elapsed> <budget>
# True when a status plausibly means "the deadline expired".
#
# GNU coreutils reports 124 on expiry and 137 when the KILL was needed. The Rust
# reimplementation that ships on some hosts reports 125 where GNU reports 124,
# and GNU uses 125 for "the deadline wrapper itself failed". The status alone is
# therefore ambiguous, so the elapsed count disambiguates: a command that
# consumed its entire budget and then failed timed out, whatever it reported.
# The elapsed count comes from the shell's own seconds counter and never from a
# clock utility, and it is only ever written to the run log (R-6).
acas_py_is_timeout_status() {
  local rc="$1" elapsed="$2" budget="$3"
  if (( rc == 124 || rc == 137 )); then
    return 0
  fi
  if (( rc != 0 && elapsed >= budget )); then
    return 0
  fi
  return 1
}

# acas_py_assert_not_timed_out <rc> <elapsed> <budget> <budget-var> <label>...
acas_py_assert_not_timed_out() {
  local rc="$1" elapsed="$2" budget="$3" budget_var="$4"
  shift 4
  if ! acas_py_is_timeout_status "$rc" "$elapsed" "$budget"; then
    return 0
  fi
  acas_py_die "$EX_TIMEOUT" \
    "$* exceeded its ${budget}s deadline (status $rc after ${elapsed}s)." \
    "Raise $budget_var if the work legitimately takes longer; investigate the" \
    'command if it does not. It was sent TERM and then KILL after' \
    "${ACAS_TIMEOUT_GRACE}s, so nothing is still running."
}

# =============================================================================
# TRAPS
#
# There is no credential file to shred and no credential in any command line:
# the password reaches nothing but the child's inherited environment. Execution
# tracing is never enabled anywhere in this script for the same reason.
# =============================================================================

# shellcheck disable=SC2317  # reached only through the ERR trap installed below,
# which shellcheck cannot follow; the body is live and is exercised by the
# negative validation cases.
acas_py_on_err() {
  local status="$1" line="$2" cmd="$3"
  printf '\nFATAL: unexpected failure at %s line %s (status %s).\n' \
    "${BASH_SOURCE[0]}" "$line" "$status" >&2
  printf '       failing command: %s\n' "$cmd" >&2
  if [[ -n "$ACAS_PY_CURRENT_STAGE" ]]; then
    printf '       while: %s\n' "$ACAS_PY_CURRENT_STAGE" >&2
  fi
  acas_py_tee "FATAL: unexpected failure at line $line (status $status): $cmd"
}
trap 'acas_py_on_err "$?" "$LINENO" "$BASH_COMMAND"' ERR

# shellcheck disable=SC2317  # reached only through the EXIT trap installed
# below, which shellcheck cannot follow; the body is live and is exercised by
# the concurrency validation case.
# Release the sequential run lock, but only if THIS process took it, so an early
# failure can never delete a lock belonging to a live run.
acas_py_release_lock() {
  if (( ACAS_PY_LOCK_HELD )) && [[ -n "$ACAS_PY_LOCK" ]]; then
    if ! rm -f -- "$ACAS_PY_LOCK" 2>/dev/null; then
      printf 'WARNING: the run lock could not be removed: %s\n' "$ACAS_PY_LOCK" >&2
    fi
    ACAS_PY_LOCK_HELD=0
  fi
}

# shellcheck disable=SC2317  # reached only through the EXIT trap installed
# below; the body is live and is exercised by every non-zero exit path.
acas_py_on_exit() {
  local status="$1"
  # FIRST, unconditionally, and before the status is examined: a lock that
  # outlives its owner wedges every later invocation.
  acas_py_release_lock
  if (( status == 0 )); then
    return 0
  fi
  if (( ACAS_PY_RAN )); then
    printf '\nharness/run_python_scenario.sh exiting with status %s AFTER at least one\n' \
      "$status" >&2
    printf 'operation was invoked, so the database may hold a PARTIAL result. Re-run the\n' >&2
    printf 'reset and seed stages before drawing any conclusion from a state diff.\n' >&2
  else
    printf '\nharness/run_python_scenario.sh exiting with status %s. No operation was\n' \
      "$status" >&2
    printf 'invoked, so the database is untouched.\n' >&2
  fi
  if (( ACAS_PY_LOG_OPEN )); then
    printf 'The run log is at: %s\n' "$ACAS_PY_LOG" >&2
  fi
  acas_py_tee "harness/run_python_scenario.sh exiting with status $status (ran=$ACAS_PY_RAN)"
}
trap 'acas_py_on_exit "$?"' EXIT

# =============================================================================
# USAGE
# =============================================================================
acas_py_usage() {
  # The delimiter is USAGE_EOF and not USAGE, because the text below uses
  # "USAGE" as a section heading on a line of its own, which would end the
  # here-document early -- silently shortening the help and leaving the rest to
  # be parsed as shell.
  cat <<'USAGE_EOF'
harness/run_python_scenario.sh -- drive the MIGRATED PYTHON posting cycle.

Stage 6 of the eight-stage parity protocol:
    seed -> run(COBOL) -> dump -> normalise -> reset -> run(PYTHON) -> dump -> diff

This is the MIGRATED side. It runs the headless command-line entry points of the
acas_posting package as subprocesses, with the same logical inputs the compiled
menus were given, and then takes the state capture of stage 7. It contains no
COBOL of any kind and runs on a host with no COBOL compiler and no COBOL runtime
present.

USAGE
    harness/run_python_scenario.sh [OPTIONS] [<scenario-file>]

    The bare positional form is the canonical invocation the committed Compose
    recipe uses, which passes only the scenario file.

OPTIONS
    --scenario NAME        Scenario name. Defaults to the scenario file's own
                          `scenario:' key, then to its basename without the
                          extension. It becomes a directory name under the
                          output area, so it may hold only letters, digits,
                          underscore and hyphen.
    --scenario-file PATH   Scenario definition. Same as the positional form.
                          Defaults to <ACAS_REPO>/harness/scenarios/<NAME>.yaml
                          when only --scenario was given.
    --operation NAME       One of the seven operations below. May be REPEATED,
                          and the repetitions run in the order given. Omit it to
                          take the scenario's own ordered list, from its
                          `operations:' key or its singular `operation:' key.
    --out-dir DIR          Root of the capture tree, <DIR>/<scenario>/python/.
                          Defaults to $ACAS_OUT.
    --log PATH             Run-log destination. Default
                          $ACAS_OUT/run-logs/<scenario>/python.log, which is
                          deliberately OUTSIDE every compared tree. The path is
                          canonicalised and then refused if it, or any parent it
                          would create, lands inside the frozen checkout or
                          inside a tree the diff stage compares.
    --no-dump              Run the operations but skip the stage-7 capture. For
                          debugging only: without a capture there is nothing for
                          the diff stage to compare.
    --dry-run              Resolve the scenario, probe the interpreter and the
                          package, read each module's own help text, resolve
                          every option the scenario requires against it, print
                          the exact command line of every command that would
                          run -- and stop. Contacts no database and writes
                          nothing at all.
    -h, --help             This text.

    There is no option that would run anything at the same time as anything
    else, and none that would force past a refusal. Execution is strictly
    sequential and every refusal is a real precondition, so the option parser
    refuses any option it does not recognise rather than accepting one it would
    then ignore.

THE SEVEN OPERATIONS
    Identical to the set the oracle-side runner accepts, so the two runners are
    trivially comparable. Each names the migrated module it invokes and the menu
    paragraph that module reproduces.

    gl_post_cycle     acas_posting.cli.gl_post_cycle
                      load08  [general/general.cbl:L805-L815]
    gl_end_of_cycle   acas_posting.cli.gl_end_of_cycle
                      load09  [general/general.cbl:L817-L821]
    sl_invoice_post   acas_posting.cli.sl_invoice_post
                      load07  [sales/sales.cbl:L756-L768]
    sl_cash_post      acas_posting.cli.sl_cash_post
                      load11  [sales/sales.cbl:L792-L796]
    pl_order_post     acas_posting.cli.pl_order_post
                      load08  [purchase/purchase.cbl:L752-L762]
    pl_payment_post   acas_posting.cli.pl_payment_post
                      load12  [purchase/purchase.cbl:L786-L790]
    irs_post          acas_posting.cli.irs_post
                      main-loop option "4"  [irs/irs.cbl:L666-L672]

SCENARIO KEYS THIS STAGE READS
    Read with a real YAML parser. `_' and `-' are interchangeable in every key
    name. An explicitly empty value must be QUOTED, because a bare `key:' is a
    null in YAML and cannot be told from a forgotten value.

    run_date_text          The pinned run date, exactly as written, e.g.
                           21/09/2025. Passed through unchanged: the digits are
                           never reordered to match date_form.
    run_date_binary        The `Run-Date' the system record must hold after the
                           run [copybooks/wssystem.cob:L67]. Observed, and
                           reported against, after the run.
    date_form              1 UK, 2 USA, 3 International
                           [copybooks/wssystem.cob:L128-L131]. Default 1.
    irs_instead            The three-state fan-out switch
                           [copybooks/wssystem.cob:L179-L181]: "" or " " for
                           General Ledger only, "Y" for IRS instead of the
                           General Ledger, "B" for IRS as well as it. The key
                           must be PRESENT even for the blank state, because a
                           default would leave the affected-table list
                           ambiguous. Passed on as the RAW character.
    operations             The ordered list of operations to run. A singular
                           `operation:' scalar is accepted as a one-item list.
    affected_tables        The table list that BOUNDS the comparison. Required.
                           Every name must be one of the 22 in-scope tables, and
                           no name may appear twice.
    irs_clear_postings     "Y" or "N". REQUIRED for irs_post, and there is no
                           default because the frozen program has none. "Y"
                           removes every row of the IRS transfer table
                           [irs/irs030.cbl:L1723], so an irs_post scenario must
                           also list PSIRSPOST-REC in affected_tables.
    gl080_proceed          "Y" proceeds, "A" aborts before any write of any kind
                           [general/gl080.cbl:L295-L302]. Default "Y", which is
                           the frozen program's own default.
    disk_change_option     "0" proceeds, "9" aborts the archiving walk and the
                           whole of end-of-period processing
                           [general/gl080.cbl:L545]. Default "0". No other value
                           can leave the frozen program's input loop.
    archive_path_override  Optional override of the archive path
                           [general/gl080.cbl:L530-L537]. Omit it for the frozen
                           default, which is no override.
    payment_post_confirm   "YES" or "NO". REQUIRED for sl_cash_post and
                           pl_payment_post: neither program's prompt has a
                           default, both blank the reply field and re-ask on a
                           blank [sales/sl100.cbl:L310-L319],
                           [purchase/pl100.cbl:L302-L311].
    ws_caller              Optional override of `WS-Caller pic x(8)'
                           [copybooks/wscall.cob:L8]. Omit it to take each
                           route's own default, which is the literal the
                           corresponding menu moves.
    expected_status        Optional. The process status each operation is
                           declared to end with, either one value for all of
                           them or a list positionally matching `operations'. A
                           contradiction is reported as a behavioural difference
                           and the capture is still taken.

ENVIRONMENT
    ACAS_REPO             The checkout, mounted read-only. Never written to and
                          never made the working directory; asserted untouched
                          after the run.
    ACAS_OUT              The output area. Holds run-logs/<scenario>/ and the
                          <scenario>/python/ capture tree.
    ACAS_DATA             Declared for symmetry with the other stages. May be
                          empty: the migrated cycle reads no flat file.
    ACAS_DB_HOST          The server; `mariadb' inside the harness network.
    ACAS_DB_PORT          The port; 3306 inside the harness network.
    ACAS_DB_NAME          MUST be exactly ACASDB. This stage drives a
                          DESTRUCTIVE posting cycle against whatever schema it
                          is pointed at, and the schema name is the only thing
                          distinguishing the harness database from a real one.
    ACAS_DB_USER          The credential. Both are width-limited to twelve
    ACAS_DB_PASSWORD      characters, because the frozen host-variable group is
                          `DB-UName pic x(12)' and `DB-UPass pic x(12)'
                          [copybooks/wsfnctn.cob:L56-L62] and a longer value is
                          silently shortened by the MOVE into it -- so the two
                          sides of the comparison would connect as different
                          accounts. Neither is ever printed, logged or placed in
                          a command line.
    ACAS_DB_SOCKET        A socket path, or empty for TCP. Must be DECLARED.
    PYTHON                The interpreter, default python3. It must be a 3.12
                          series interpreter, which is what the project pins.

OPTIONAL ENVIRONMENT
    ACAS_DB_TLS_CA        A certificate-authority bundle the server's
                          certificate chains to. When set, this stage's own
                          read-only queries verify BOTH the certificate and the
                          host name, because encrypting without verifying
                          accepts any certificate and is not verification at
                          all. Passed through to the migrated side unchanged.
    ACAS_DB_TLS_CERT      A client certificate and its key, for a server that
    ACAS_DB_TLS_KEY       requires one. Passed through unchanged.
    ACAS_DB_ALLOW_PLAINTEXT
                          Declare that the target really is the isolated harness
                          network and that an unprotected connection to it is
                          intended. Only 1, true, yes and on count; anything
                          else is a typo and is read as "not declared". A
                          loopback host or a non-empty socket path needs no
                          declaration. Any OTHER target with neither a
                          certificate authority nor this declaration is REFUSED
                          before anything connects: the credential here is the
                          one the compiled cycle itself uses.
    ACAS_DB_CONNECT_TIMEOUT, ACAS_DB_READ_TIMEOUT, ACAS_DB_WRITE_TIMEOUT
                          The driver's own socket deadlines, honoured by this
                          stage's queries and by the capture of stage 7.
    ACAS_TIMEOUT_GRACE    Seconds between TERM and KILL for a command that
                          overruns its deadline. Default 15.
    ACAS_TIMEOUT_CLIENT   Seconds for one read-only query. Default 60.
    ACAS_TIMEOUT_HELP     Seconds for one module's help text. Default 120.
    ACAS_TIMEOUT_OPERATION
                          Seconds for one migrated operation. Default 3600.
    ACAS_TIMEOUT_CAPTURE  Seconds for the stage-7 capture. Default 1800.
                          Every budget must be a whole number of seconds from 1
                          to 86400, read base ten so a leading zero is not
                          octal. Leave one unset or empty to take its default. A
                          malformed value is a usage error, never a silently
                          dropped deadline.

EXIT STATUS
    0   every operation ran and behaved as the scenario declares, INCLUDING a
        reproduced abort whose status the scenario declared. The capture was
        taken.
    69  a behavioural difference: an observed status contradicts the scenario's
        declared one. THE CAPTURE WAS STILL TAKEN, so the diff stage can
        corroborate. Deliberately below the fault block: 0 means every
        disposition agreed, 69 means one did not, 70 or above means the
        comparison could not be performed at all.
    70  usage error -- an unknown option, an unknown operation, or a command
        line this script built wrongly, which a migrated module's argument layer
        reports as status 2.
    71  a precondition failed -- environment, interpreter, package, driver, an
        option a module does not publish, or seed fingerprints that disagree.
    72  the database is unreachable, or the schema is not there.
    75  the scenario file is missing, malformed or incomplete.
    77  a post-run assertion failed, or the capture did not produce what was
        asked of it.
    78  a bounded command overran its deadline, so no verdict was reached.

    73, 74, 76 and 79 belong to the oracle-side runner and are deliberately
    unused here; their meanings are not reassigned. See the header.

    A non-zero status FROM A MIGRATED OPERATION is frequently the specification
    rather than a fault: the term-code mapping is the identity, and three of the
    twelve in-scope programs set one -- `move 5 to ws-term-code'
    [general/gl070.cbl:L289] and `move 8 to WS-Term-Code'
    [sales/sl055.cbl:L344], [purchase/pl055.cbl:L286]. Such a status is recorded
    verbatim and interpreted only against the scenario's declaration.

This script never exits with a success status unconditionally. The frozen build
scripts do -- [comp-all.sh:L45] and [common/comp-common.sh:L59] -- and they are
NOT fixed; their shape is simply not adopted here.
USAGE_EOF
}

# =============================================================================
# ARGUMENT PARSING
#
# Both `--opt value' and `--opt=value' are accepted, `--' terminates the
# options, and a bare word is the scenario file -- the same shapes every other
# stage in this tree accepts, so an operator does not have to remember which
# stage wants which form.
# =============================================================================
acas_py_parse_args() {
  local positional=''
  while (( $# > 0 )); do
    case "$1" in
      -h|--help)
        acas_py_usage
        exit "$EX_OK"
        ;;
      --scenario)
        [[ $# -ge 2 ]] || acas_py_die "$EX_USAGE" '--scenario requires a name.'
        ACAS_PY_SCENARIO="$2"
        shift 2
        ;;
      --scenario=*)
        ACAS_PY_SCENARIO="${1#*=}"
        shift
        ;;
      --scenario-file)
        [[ $# -ge 2 ]] || acas_py_die "$EX_USAGE" '--scenario-file requires a path.'
        ACAS_PY_SCENARIO_FILE="$2"
        shift 2
        ;;
      --scenario-file=*)
        ACAS_PY_SCENARIO_FILE="${1#*=}"
        shift
        ;;
      --operation)
        [[ $# -ge 2 ]] || acas_py_die "$EX_USAGE" '--operation requires a name.'
        ACAS_PY_REQUESTED_OPS+=("$2")
        shift 2
        ;;
      --operation=*)
        ACAS_PY_REQUESTED_OPS+=("${1#*=}")
        shift
        ;;
      --out-dir)
        [[ $# -ge 2 ]] || acas_py_die "$EX_USAGE" '--out-dir requires a path.'
        ACAS_PY_OUT_DIR="$2"
        shift 2
        ;;
      --out-dir=*)
        ACAS_PY_OUT_DIR="${1#*=}"
        shift
        ;;
      --log)
        [[ $# -ge 2 ]] || acas_py_die "$EX_USAGE" '--log requires a path.'
        ACAS_PY_LOG="$2"
        shift 2
        ;;
      --log=*)
        ACAS_PY_LOG="${1#*=}"
        shift
        ;;
      --no-dump)
        ACAS_PY_DUMP=0
        shift
        ;;
      --dry-run)
        ACAS_PY_DRY_RUN=1
        shift
        ;;
      --)
        shift
        break
        ;;
      -*)
        acas_py_die "$EX_USAGE" \
          "unrecognised option '$(acas_py_sanitise_field "$1")'." \
          'Run --help for the accepted options. Nothing is silently ignored: an' \
          'option this script does not know might have been meant to change what the' \
          'run does, and accepting it would be the same defect as dropping one.'
        ;;
      *)
        if [[ -n "$positional" ]]; then
          acas_py_die "$EX_USAGE" \
            "at most one scenario file may be given; got '$(acas_py_sanitise_field "$positional")' and '$(acas_py_sanitise_field "$1")'."
        fi
        positional="$1"
        shift
        ;;
    esac
  done

  # Anything after `--' is the scenario file, at most one.
  while (( $# > 0 )); do
    if [[ -n "$positional" ]]; then
      acas_py_die "$EX_USAGE" \
        "unexpected trailing arguments: $(acas_py_sanitise_field "$(acas_py_join_words "$@")")"
    fi
    positional="$1"
    shift
  done

  if [[ -n "$positional" ]]; then
    if [[ -n "$ACAS_PY_SCENARIO_FILE" && "$ACAS_PY_SCENARIO_FILE" != "$positional" ]]; then
      acas_py_die "$EX_USAGE" \
        'the scenario file was given twice with different values.' \
        "--scenario-file said '$(acas_py_sanitise_field "$ACAS_PY_SCENARIO_FILE")'," \
        "the positional said '$(acas_py_sanitise_field "$positional")'."
    fi
    ACAS_PY_SCENARIO_FILE="$positional"
  fi
}

# =============================================================================
# THE INTERPRETER
#
# Resolved to an ABSOLUTE path before the working directory moves, so a relative
# `PYTHON' cannot stop resolving half way through the run, and so the summary
# names the interpreter that actually ran rather than a name that might mean
# something else by then.
# =============================================================================
acas_py_resolve_interpreter() {
  ACAS_PY_CURRENT_STAGE='resolving the interpreter'
  local requested="${PYTHON:-python3}" resolved=''

  if ! resolved="$(command -v -- "$requested" 2>/dev/null)"; then
    acas_py_die "$EX_PRECONDITION" \
      "the interpreter '$(acas_py_sanitise_field "$requested")' is not on the PATH." \
      'Set PYTHON to the 3.12 interpreter this project pins. Every Python command' \
      'this script runs -- each migrated operation, each help text, each read-only' \
      'query and the stage-7 capture -- uses that one interpreter, so there is never' \
      'a second one in play.'
  fi
  if [[ "$resolved" != /* ]]; then
    resolved="$(acas_py_canonical_path "$resolved")"
  fi
  [[ -x "$resolved" ]] || acas_py_die "$EX_PRECONDITION" \
    "the interpreter is not executable: $(acas_py_sanitise_field "$resolved")"
  ACAS_PY_PYTHON="$resolved"

  # The series, asserted before anything else runs under it. The project pins a
  # single series and the two sides of a comparison must be produced by the
  # interpreter the migration was built for.
  local rc=0 reported=''
  acas_py_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  reported="$("${ACAS_DEADLINE_ARGV[@]}" "$ACAS_PY_PYTHON" -c \
      'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)" || rc=$?
  if (( rc != 0 )); then
    acas_py_die "$EX_PRECONDITION" \
      "the interpreter could not report its version (status $rc)." \
      "  interpreter: $(acas_py_sanitise_field "$ACAS_PY_PYTHON")"
  fi
  if [[ "$reported" != "${ACAS_PY_REQUIRED_MAJOR}.${ACAS_PY_REQUIRED_MINOR}" ]]; then
    acas_py_die "$EX_PRECONDITION" \
      "the interpreter is Python $(acas_py_sanitise_field "$reported"), not ${ACAS_PY_REQUIRED_MAJOR}.${ACAS_PY_REQUIRED_MINOR}." \
      "  interpreter: $(acas_py_sanitise_field "$ACAS_PY_PYTHON")" \
      'The project declares a single interpreter series. Point PYTHON at it -- a' \
      'virtual environment created from it will do -- rather than running this stage' \
      'under whatever happens to be first on the PATH.'
  fi
}

# =============================================================================
# THE SCENARIO DOCUMENT
#
# Read ONCE, with PyYAML -- the one third-party import this tree permits itself
# besides the database driver. Not with a hand-rolled parser: the affected-table
# list is what BOUNDS the comparison, so mis-reading it silently is the most
# expensive mistake available here, and a real parser is the only way to be sure
# that a quoted empty value, an inline list and a block list all mean what their
# author meant.
#
# The reader below imports PyYAML and NOTHING from the migrated package: this
# tree is not on the package's import path and must not put itself there.
#
# The stream it emits is one record per line, tab-separated:
#     K <TAB> key                 the key is present, whatever its value
#     S <TAB> key <TAB> value     a scalar, rendered as text
#     L <TAB> key <TAB> value     one list item, in file order
#     G <TAB> key                 the key carried a nested block, which this
#                                 stage records rather than reads
# A value carrying a tab, a newline or any other control character is FOLDED to
# spaces rather than smuggled through the separator, and a real number is refused
# outright because no scenario value is a real number and R-2 forbids one from
# entering by accident.
#
# A nested block -- a mapping, or a list whose items are themselves mappings --
# is recorded as present and NOT read: a scenario documents the seeded state in
# `clock:', `system:' and `seed:' blocks that this runner has no use for, and the
# oracle-side reader ignores them in the same way, which is what lets one scenario
# file serve both runners. Nothing is lost by that: the caller then refuses a
# block that appears under a key this runner actually reads
# (ACAS_PY_SCENARIO_KEYS), so tolerance never becomes a silent mis-read.
# =============================================================================
acas_py_yaml_stream() {
  acas_py_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  "${ACAS_DEADLINE_ARGV[@]}" "$ACAS_PY_PYTHON" - "$1" <<'PY'
import pathlib
import sys

try:
    import yaml
except ModuleNotFoundError as exc:
    sys.stderr.write(
        "PyYAML is not importable by this interpreter (%s). It is the one "
        "third-party import the harness tree permits itself besides the "
        "database driver, and the scenario definitions are YAML.\n" % exc
    )
    raise SystemExit(3)

path = pathlib.Path(sys.argv[1])
try:
    text = path.read_text(encoding="utf-8")
except OSError as exc:
    sys.stderr.write("the scenario file could not be read: %s\n" % exc)
    raise SystemExit(4)

try:
    document = yaml.safe_load(text)
except yaml.YAMLError as exc:
    sys.stderr.write("the scenario file is not valid YAML: %s\n" % exc)
    raise SystemExit(5)

if document is None:
    document = {}
if not isinstance(document, dict):
    sys.stderr.write(
        "the scenario file must be a mapping at top level; got %s\n"
        % type(document).__name__
    )
    raise SystemExit(5)


def render(key, value):
    """Render one scalar as text, refusing anything that cannot travel."""
    if value is None:
        text = ""
    elif isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, int):
        text = str(value)
    elif isinstance(value, str):
        text = value
    elif isinstance(value, float):
        sys.stderr.write(
            "key %r carries a real number, which is refused: no scenario value "
            "is a real number, and rule R-2 forbids binary floating point from "
            "entering the comparison by accident. Quote it if it is text.\n"
            % key
        )
        raise SystemExit(5)
    else:
        sys.stderr.write(
            "key %r carries an unsupported %s value; this stage reads scalars "
            "and flat lists of scalars, and records a nested block without "
            "reading it. A date written unquoted becomes a date object here, so "
            "quote it to keep it text.\n" % (key, type(value).__name__)
        )
        raise SystemExit(5)
    if any(ord(character) < 32 or ord(character) == 127 for character in text):
        #  A CONTROL CHARACTER IS FOLDED, NOT REFUSED - and the distinction is the
        #  reader's own protocol rather than a relaxation of it. The stream this
        #  reader emits is TAB-delimited and newline-terminated, so a value
        #  carrying either would forge a record boundary; replacing each control
        #  character with ONE SPACE keeps that property absolutely, because no
        #  emitted byte is a control character afterwards.
        #
        #  It is folded rather than refused because a scenario legitimately
        #  carries a multi-line documentation block: `description: |` in
        #  harness/scenarios/clean_batch_gl.yaml is a YAML literal scalar of
        #  several hundred lines, and no key this runner consumes is documentation.
        #  Refusing it would have made a documented scenario unreadable.
        #
        #  ONLY a value that actually holds a control character is touched, so
        #  every value that travels arrives byte for byte - `irs_instead: ' '`, the
        #  single SPACE that selects General-Ledger-only posting
        #  [copybooks/wssystem.cob:L179-L181], included. Folding whitespace
        #  generally would have emptied it and silently changed the fan-out.
        text = "".join(
            " " if (ord(character) < 32 or ord(character) == 127) else character
            for character in text
        )
    return text


def is_block(value):
    """True for a nested structure: a mapping, a sequence or a set."""
    return isinstance(value, (dict, list, tuple, set, frozenset))


emitted = {}
out = []
blocks = []
for key in document:
    if not isinstance(key, str):
        sys.stderr.write(
            "every top-level key must be text; got a %s\n" % type(key).__name__
        )
        raise SystemExit(5)
    normalised = key.replace("-", "_")
    if normalised in emitted:
        sys.stderr.write(
            "keys %r and %r are the same key: '-' and '_' are "
            "interchangeable, so one of them must go.\n"
            % (emitted[normalised], key)
        )
        raise SystemExit(5)
    emitted[normalised] = key
    out.append("K\t%s" % normalised)
    value = document[key]
    if isinstance(value, (list, tuple)):
        #  A LIST IS EMITTED ONLY WHEN EVERY ITEM IS A SCALAR. A part-read list is
        #  worse than an unread one: the affected-table list BOUNDS the comparison
        #  and the operation list ORDERS the run, so half of either would look like
        #  a complete answer. So a list holding a nested item is recorded whole and
        #  read not at all.
        if any(is_block(item) for item in value):
            out.append("G\t%s" % normalised)
            blocks.append((key, "list whose items are themselves blocks"))
            continue
        for item in value:
            out.append("L\t%s\t%s" % (normalised, render(key, item)))
    elif is_block(value):
        #  A NESTED BLOCK IS RECORDED, NOT READ. A scenario file documents the
        #  state it seeds in `clock:', `system:' and `seed:' blocks, and states the
        #  values this runner reads as top-level scalars beside them; the
        #  oracle-side reader passes over a nested block in exactly the same way,
        #  which is what lets ONE scenario file drive both runners. The caller
        #  refuses a block that appears under a key this runner does read, so this
        #  tolerance cannot turn into a silent mis-read.
        out.append("G\t%s" % normalised)
        blocks.append((key, "%s block" % type(value).__name__))
    else:
        out.append("S\t%s\t%s" % (normalised, render(key, value)))

sys.stdout.write("".join(line + "\n" for line in out))
for key, shape in blocks:
    sys.stderr.write(
        "note: key %r is a %s. It is recorded as present and its members are "
        "not read: this stage reads scalars and flat lists of scalars, and no "
        "key this runner reads is declared as a block.\n" % (key, shape)
    )
PY
}

# Read the document into the three associative arrays.
acas_py_read_scenario() {
  local file="$1" rc=0 stream='' started elapsed
  started="$SECONDS"
  stream="$(acas_py_yaml_stream "$file")" || rc=$?
  elapsed=$(( SECONDS - started ))
  acas_py_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_CLIENT" \
    'ACAS_TIMEOUT_CLIENT' 'reading the scenario file'
  if (( rc != 0 )); then
    acas_py_die "$EX_SCENARIO" \
      "the scenario file could not be read (status $rc)." \
      "  file: $(acas_py_sanitise_field "$file")" \
      'The reader printed the reason above. The eight scenario definitions live' \
      'under harness/scenarios/.'
  fi

  local kind key value
  while IFS=$'\t' read -r kind key value; do
    case "$kind" in
      '') continue ;;
      K)  ACAS_PY_YAML_PRESENT["$key"]=1 ;;
      G)  ACAS_PY_YAML_GROUP["$key"]=1 ;;
      S)  ACAS_PY_YAML_SCALAR["$key"]="$value" ;;
      L)
        if [[ -n "${ACAS_PY_YAML_LIST[$key]+set}" ]]; then
          ACAS_PY_YAML_LIST["$key"]="${ACAS_PY_YAML_LIST[$key]}"$'\n'"$value"
        else
          ACAS_PY_YAML_LIST["$key"]="$value"
        fi
        ;;
      *)
        acas_py_die "$EX_SCENARIO" \
          "the scenario reader emitted an unrecognised record kind '$(acas_py_sanitise_field "$kind")'."
        ;;
    esac
  done <<< "$stream"

  acas_py_assert_scenario_shape
}

# A nested block under a key this runner READS is refused here, in the main shell,
# where a refusal can still stop the run -- the scalar and list accessors are
# called inside command substitutions, where an exit would end only the subshell
# and the run would carry on with an empty value, which is exactly the silence
# this check exists to prevent. A block under any other key is left alone: the
# oracle-side reader ignores a nested block too, and that shared tolerance is what
# lets one scenario file drive both runners.
acas_py_assert_scenario_shape() {
  (( ${#ACAS_PY_YAML_GROUP[@]} > 0 )) || return 0
  local key
  for key in "${!ACAS_PY_YAML_GROUP[@]}"; do
    if acas_py_in_list "$key" "${ACAS_PY_SCENARIO_KEYS[@]}"; then
      acas_py_die "$EX_SCENARIO" \
        "the scenario declares '$(acas_py_sanitise_field "$key")' as a nested block, and this runner reads that key." \
        '  A key this runner reads must carry a scalar, or a flat list of scalars,' \
        '  so that what the author wrote is what the run receives. As a block it' \
        '  would read as empty and change the run without saying so -- for the' \
        '  fan-out switch [copybooks/wssystem.cob:L179-L181] that decides which' \
        '  ledgers a posting reaches, or for the affected-table list that bounds' \
        '  the comparison, that silence is the most expensive failure available.' \
        '  State the value at top level; a block under a key this runner does not' \
        '  read -- clock, system, seed -- is perfectly fine and is left alone.'
    fi
  done
}

# True when the key appeared at top level at all, whatever its value. Needed
# because an empty value is MEANINGFUL for the fan-out switch and must never be
# confused with the key having been forgotten
# [copybooks/wssystem.cob:L179-L181].
acas_py_scenario_has_key() {
  [[ -n "${ACAS_PY_YAML_PRESENT[${1//-/_}]+set}" ]]
}

# The scalar value, or nothing when the key is absent or is a list.
acas_py_scenario_scalar() {
  local key="${1//-/_}"
  if [[ -n "${ACAS_PY_YAML_SCALAR[$key]+set}" ]]; then
    printf '%s' "${ACAS_PY_YAML_SCALAR[$key]}"
  fi
}

# The scalar value, or the fallback when it is absent or empty.
acas_py_scenario_default() {
  local value
  value="$(acas_py_scenario_scalar "$1")"
  if [[ -n "$value" ]]; then
    printf '%s' "$value"
  else
    printf '%s' "$2"
  fi
}

# The list items, one per line. A single scalar where a list was expected is
# emitted as a one-item list rather than silently dropped -- the same tolerance
# the oracle-side runner extends, so one scenario file serves both.
acas_py_scenario_list() {
  local key="${1//-/_}"
  if [[ -n "${ACAS_PY_YAML_LIST[$key]+set}" ]]; then
    printf '%s\n' "${ACAS_PY_YAML_LIST[$key]}"
    return 0
  fi
  if [[ -n "${ACAS_PY_YAML_SCALAR[$key]+set}" && -n "${ACAS_PY_YAML_SCALAR[$key]}" ]]; then
    printf '%s\n' "${ACAS_PY_YAML_SCALAR[$key]}"
  fi
}

# =============================================================================
# THE ENVIRONMENT
# =============================================================================

# acas_py_assert_width <env-var-name> <max>
acas_py_assert_width() {
  local name="$1" max="$2" value
  value="${!name:-}"
  if (( ${#value} > max )); then
    acas_py_die "$EX_PRECONDITION" \
      "$name is ${#value} characters; the frozen host variable holds at most $max." \
      'The connection group is DB-Schema x(12), DB-UName x(12), DB-UPass x(12),' \
      'DB-Host x(32), DB-Socket x(64), DB-Port x(5)' \
      '[copybooks/wsfnctn.cob:L56-L62]. A longer value is silently shortened by the' \
      'MOVE into it, so the compiled side would connect as a different account than' \
      'this side -- and two captures taken as different accounts are not comparable.' \
      'The offending VALUE is deliberately not echoed; only its length and its limit.'
  fi
}

acas_py_assert_environment() {
  ACAS_PY_CURRENT_STAGE='asserting the environment contract'
  acas_py_stage 'Stage 1/8: environment'

  local name
  for name in "${ACAS_PY_REQUIRED_ENV_NONEMPTY[@]}"; do
    if [[ -z "${!name:-}" ]]; then
      acas_py_die "$EX_PRECONDITION" \
        "$name is unset or empty." \
        'The harness environment is published by the committed Compose file, which' \
        'also carries the canonical one-command-per-stage recipe.'
    fi
  done
  for name in "${ACAS_PY_REQUIRED_ENV_DECLARED[@]}"; do
    if [[ -z "${!name+set}" ]]; then
      acas_py_die "$EX_PRECONDITION" \
        "$name is not declared." \
        'It may legitimately be EMPTY -- the harness connects over TCP, and the' \
        'migrated cycle reads no flat file -- but it must be DECLARED, because the' \
        'compiled side reads a socket path out of the connection group at' \
        '[copybooks/wsfnctn.cob:L56-L62] and the two sides must agree about what is' \
        'configured and what is merely absent.'
    fi
  done
  acas_py_note 'the compiled build tree and the two menu path variables are deliberately NOT required here: they are COBOL-only preconditions (R-1)'

  acas_py_assert_width ACAS_DB_NAME 12
  acas_py_assert_width ACAS_DB_USER 12
  acas_py_assert_width ACAS_DB_PASSWORD 12
  acas_py_assert_width ACAS_DB_HOST 32
  acas_py_assert_width ACAS_DB_PORT 5
  if [[ -n "${ACAS_DB_SOCKET:-}" ]]; then
    acas_py_assert_width ACAS_DB_SOCKET 64
  fi

  # THE RANGE, not merely the character class. A numeric-only test admits 0 and
  # 99999, both of which reach the driver as an out-of-range port and fail with a
  # cause naming neither the variable nor the value.
  [[ "$ACAS_DB_PORT" =~ ^[0-9]+$ ]] || acas_py_die "$EX_PRECONDITION" \
    "ACAS_DB_PORT must be numeric; got '$(acas_py_sanitise_field "$ACAS_DB_PORT")'."
  if (( 10#$ACAS_DB_PORT < 1 || 10#$ACAS_DB_PORT > 65535 )); then
    acas_py_die "$EX_PRECONDITION" \
      "ACAS_DB_PORT must be between 1 and 65535; got '$ACAS_DB_PORT'."
  fi
  # Canonicalised so that the port this script reports and the port the driver
  # receives are one value rather than several spellings of it. Base ten, so a
  # leading zero is stripped rather than read as octal. Done AFTER the width
  # check, so a six-character value is still refused on width: the frozen field
  # is `DB-Port pic x(5)' CHARACTER data, and 65535 is five characters.
  ACAS_DB_PORT="$(( 10#$ACAS_DB_PORT ))"
  export ACAS_DB_PORT

  # And it must be THE schema. The frozen dump defines exactly one database, so
  # this cycle has exactly one place to run. Driving it at a differently named
  # schema would either fail obscurely or -- far worse -- succeed against
  # something else and produce a state diff that looks like evidence.
  if [[ "$ACAS_DB_NAME" != "$ACAS_PY_REQUIRED_SCHEMA" ]]; then
    acas_py_die "$EX_PRECONDITION" \
      "ACAS_DB_NAME is '$(acas_py_sanitise_field "$ACAS_DB_NAME")', not '$ACAS_PY_REQUIRED_SCHEMA'." \
      'This stage drives a DESTRUCTIVE posting cycle against whatever schema it is' \
      'pointed at, and the schema name is the only thing distinguishing the harness' \
      'database from a real one. The frozen schema defines exactly one database and' \
      'the committed Compose file supplies its name.'
  fi

  # The five the migrated side reads for its connection, plus the transport
  # declarations, are EXPORTED rather than merely checked, so the child inherits
  # exactly what was verified here. No option is added to carry any of them: the
  # migrated entry points publish none and must not gain one.
  export ACAS_DB_HOST ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD
  export ACAS_DB_SOCKET="${ACAS_DB_SOCKET:-}"

  [[ -d "$ACAS_REPO" ]] || acas_py_die "$EX_PRECONDITION" \
    "ACAS_REPO is not a directory: $(acas_py_sanitise_field "$ACAS_REPO")"
  export ACAS_REPO

  # The output area. Created here rather than lazily, so a run refused for an
  # unwritable output area is refused before anything else is attempted. Not in a
  # dry run, which writes nothing at all (D-7).
  if (( ! ACAS_PY_DRY_RUN )); then
    if ! mkdir -p -- "$ACAS_OUT" 2>/dev/null; then
      acas_py_die "$EX_PRECONDITION" \
        "cannot create ACAS_OUT: $(acas_py_sanitise_field "$ACAS_OUT")"
    fi
    [[ -w "$ACAS_OUT" ]] || acas_py_die "$EX_PRECONDITION" \
      "ACAS_OUT is not writable: $(acas_py_sanitise_field "$ACAS_OUT")"
  fi
  export ACAS_OUT

  # The capture root. Canonicalised HERE, while the working directory is still
  # the operator's, because a relative path must keep the meaning they intended.
  [[ -n "$ACAS_PY_OUT_DIR" ]] || ACAS_PY_OUT_DIR="$ACAS_OUT"
  ACAS_PY_OUT_DIR="$(acas_py_canonical_path "$ACAS_PY_OUT_DIR")"
  acas_py_assert_outside_repo 'the capture root' "$ACAS_PY_OUT_DIR"

  # The scenario file, likewise canonicalised before anything moves.
  if [[ -n "$ACAS_PY_SCENARIO_FILE" ]]; then
    ACAS_PY_SCENARIO_FILE="$(acas_py_canonical_path "$ACAS_PY_SCENARIO_FILE")"
  fi
  if [[ -n "$ACAS_PY_LOG" ]]; then
    ACAS_PY_LOG="$(acas_py_canonical_path "$ACAS_PY_LOG")"
  fi

  # THE DETERMINISM AND FREEZE BELT. Set once, here, so every child inherits it.
  # The package is imported from the read-only checkout and nothing is installed
  # into it; bytecode writing is off so importing cannot try to create cache
  # directories inside a frozen tree; the hash seed, the locale and the time zone
  # are pinned so that two runs cannot differ for a reason that has nothing to do
  # with the accounting (R-6). Warnings are deliberately NOT promoted to errors:
  # that would be a new validation (R-3).
  export PYTHONPATH="$ACAS_REPO"
  export PYTHONDONTWRITEBYTECODE=1
  # THE PACKAGE COMES FROM $ACAS_REPO AND NEVER FROM THE CURRENT DIRECTORY.
  # Without this, running a module puts the current directory at the FRONT of the
  # import path, ahead of PYTHONPATH -- so a directory that happens to hold a
  # package of the same name would be imported instead, and this stage would read
  # ITS options and run ITS code while reporting the checkout's path. That is not
  # hypothetical: it was found by pointing this stage at a stub package and
  # watching it read the real one's help text from the directory it was launched
  # in. A real run also moves the working directory away from the checkout, but a
  # dry run deliberately writes nothing and so moves nowhere, which left exactly
  # one path in which the most important check in this file could be answered by
  # the wrong module. This closes it for every invocation, dry or not.
  export PYTHONSAFEPATH=1
  export PYTHONHASHSEED=0
  export LC_ALL='C.UTF-8'
  export LANG='C.UTF-8'
  export TZ='UTC'

  acas_py_log "ACAS_REPO   = $(acas_py_sanitise_field "$ACAS_REPO") (read-only; never written, never entered)"
  acas_py_log "ACAS_OUT    = $(acas_py_sanitise_field "$ACAS_OUT")"
  acas_py_log "ACAS_DATA   = $(acas_py_sanitise_field "${ACAS_DATA:-}") (declared for symmetry; unused by the migrated cycle)"
  acas_py_log "capture at  = $(acas_py_sanitise_field "$ACAS_PY_OUT_DIR")/<scenario>/$ACAS_PY_SIDE"
  acas_py_log "database    = $(acas_py_sanitise_field "$ACAS_DB_NAME") on $(acas_py_sanitise_field "$ACAS_DB_HOST"):$ACAS_DB_PORT as $(acas_py_sanitise_field "$ACAS_DB_USER")"
  acas_py_log "interpreter = $(acas_py_sanitise_field "$ACAS_PY_PYTHON")"
  acas_py_note 'the database password is never logged, never placed in a command line and never written to disk'

  # The census that the freeze check compares against, taken NOW -- after the
  # bytecode setting is in force and before this script has imported the migrated
  # package for the first time.
  ACAS_PY_PYCACHE_BEFORE="$(acas_py_pycache_census)"
  if [[ -n "$ACAS_PY_PYCACHE_BEFORE" ]]; then
    acas_py_note 'bytecode cache directories already exist inside the checkout; they predate this run and are listed in the post-run check'
  fi
}

# The bytecode cache directories under the migrated package in the checkout, one
# per line and sorted, so two censuses can be compared as text.
acas_py_pycache_census() {
  local listing=''
  if [[ ! -d "$ACAS_REPO/acas_posting" ]]; then
    return 0
  fi
  if ! listing="$(find "$ACAS_REPO/acas_posting" -type d -name '__pycache__' -print 2>/dev/null | LC_ALL=C sort)"; then
    return 0
  fi
  printf '%s' "$listing"
}

# =============================================================================
# THE SCENARIO, THE OPERATIONS AND THE SUBSYSTEM
# =============================================================================
acas_py_resolve_scenario() {
  ACAS_PY_CURRENT_STAGE='resolving the scenario'
  acas_py_stage 'Stage 2/8: scenario, definition and operations'

  # The definition path. When only a name was given, it comes from the one place
  # the eight definitions live.
  if [[ -z "$ACAS_PY_SCENARIO_FILE" && -n "$ACAS_PY_SCENARIO" ]]; then
    ACAS_PY_SCENARIO_FILE="$(acas_py_canonical_path "$ACAS_REPO/harness/scenarios/$ACAS_PY_SCENARIO.yaml")"
  fi
  [[ -n "$ACAS_PY_SCENARIO_FILE" ]] || acas_py_die "$EX_USAGE" \
    'no scenario was named.' \
    'Give a scenario file -- as the bare positional argument the canonical recipe' \
    'uses, or with --scenario-file -- or give --scenario NAME and let the path be' \
    'derived from it.'
  [[ -f "$ACAS_PY_SCENARIO_FILE" ]] || acas_py_die "$EX_SCENARIO" \
    "scenario file not found: $(acas_py_sanitise_field "$ACAS_PY_SCENARIO_FILE")" \
    'The eight scenario definitions live under harness/scenarios/ and are named' \
    'clean_batch_gl, clean_batch_sl, clean_batch_pl, clean_batch_irs,' \
    'mixed_accepted_rejected, period_end_totals, control_total_mismatch and' \
    'empty_batch.'
  [[ -r "$ACAS_PY_SCENARIO_FILE" ]] || acas_py_die "$EX_SCENARIO" \
    "scenario file is not readable: $(acas_py_sanitise_field "$ACAS_PY_SCENARIO_FILE")"

  acas_py_read_scenario "$ACAS_PY_SCENARIO_FILE"

  # The scenario NAME: the option first, then the file's own key, then the file's
  # basename -- which is how the canonical recipe identifies a scenario, since it
  # passes only the path.
  if [[ -z "$ACAS_PY_SCENARIO" ]]; then
    ACAS_PY_SCENARIO="$(acas_py_scenario_scalar scenario)"
  fi
  if [[ -z "$ACAS_PY_SCENARIO" ]]; then
    ACAS_PY_SCENARIO="${ACAS_PY_SCENARIO_FILE##*/}"
    ACAS_PY_SCENARIO="${ACAS_PY_SCENARIO%.*}"
  fi
  [[ -n "$ACAS_PY_SCENARIO" ]] || acas_py_die "$EX_USAGE" \
    'no scenario name could be resolved.'
  [[ "$ACAS_PY_SCENARIO" =~ ^[A-Za-z0-9_-]+$ ]] || acas_py_die "$EX_USAGE" \
    "the scenario name must be a plain identifier; got '$(acas_py_sanitise_field "$ACAS_PY_SCENARIO")'." \
    'It becomes a directory name under the output area, so it may hold only' \
    'letters, digits, underscore and hyphen.'

  # The operations. Repeated options first, then the file's ordered list, then
  # its singular key. Order is the whole point: the operations of a scenario run
  # in the sequence the scenario declares, one after another (R-3).
  local -a wanted=()
  local candidate
  if (( ${#ACAS_PY_REQUESTED_OPS[@]} > 0 )); then
    wanted=("${ACAS_PY_REQUESTED_OPS[@]}")
  else
    while IFS= read -r candidate; do
      [[ -n "$candidate" ]] || continue
      wanted+=("$candidate")
    done < <(acas_py_scenario_list operations)
    if (( ${#wanted[@]} == 0 )); then
      candidate="$(acas_py_scenario_scalar operation)"
      [[ -z "$candidate" ]] || wanted+=("$candidate")
    fi
  fi
  (( ${#wanted[@]} > 0 )) || acas_py_die "$EX_USAGE" \
    'no operation was named.' \
    'Give --operation, or an operations: list in the scenario file, or its' \
    'singular operation: key.' \
    "The seven operations are: $(acas_py_join_words "${ACAS_PY_OPERATIONS[@]}")."

  local operation
  for operation in "${wanted[@]}"; do
    acas_py_in_list "$operation" "${ACAS_PY_OPERATIONS[@]}" || acas_py_die "$EX_USAGE" \
      "unknown operation '$(acas_py_sanitise_field "$operation")'." \
      "The seven operations are: $(acas_py_join_words "${ACAS_PY_OPERATIONS[@]}")." \
      'This set is identical to the one the oracle-side runner accepts, so the two' \
      'runners stay trivially comparable.'
  done
  ACAS_PY_RUN_OPS=("${wanted[@]}")

  # Agent Action Plan section 0.6.4: "Sales and Purchase batches balance by
  # construction, so the control-total mismatch scenario is
  # General-Ledger-specific -- there is no meaningful way to construct an
  # unbalanced sales batch." So the combination is refused rather than run to a
  # meaningless result. Matched on the same terms the oracle-side runner uses, so
  # one scenario file cannot be accepted by one runner and refused by the other.
  if [[ "$ACAS_PY_SCENARIO" == *control_total_mismatch* ]]; then
    for operation in "${ACAS_PY_RUN_OPS[@]}"; do
      local subsystem
      subsystem="$(acas_py_operation_field "$operation" 2)"
      if [[ "$subsystem" != 'general' ]]; then
        acas_py_die "$EX_USAGE" \
          'the control_total_mismatch scenario is General-Ledger-specific.' \
          "It was requested with operation '$operation', which the $subsystem route runs." \
          'Sales and Purchase batches balance by construction, so an unbalanced batch' \
          'cannot meaningfully be built for them; the control-total gate this scenario' \
          'exercises lives in the General Ledger batch proof at' \
          '[general/gl051.cbl:L1109-L1118].'
      fi
    done
  fi

  acas_py_log "scenario   = $ACAS_PY_SCENARIO"
  acas_py_log "definition = $(acas_py_sanitise_field "$ACAS_PY_SCENARIO_FILE")"
  acas_py_log "operations = $(acas_py_join_words "${ACAS_PY_RUN_OPS[@]}")"
  local mapped
  for operation in "${ACAS_PY_RUN_OPS[@]}"; do
    # The subsystem the operation belongs to, checked against the closed set of
    # four rather than merely read out of the map: a map entry with a mistyped
    # subsystem would otherwise pass silently and then mis-apply the
    # General-Ledger-only refusal above.
    mapped="$(acas_py_operation_field "$operation" 2)"
    acas_py_in_list "$mapped" "${ACAS_PY_SUBSYSTEMS[@]}" || acas_py_die "$EX_USAGE" \
      "operation '$operation' maps to subsystem '$(acas_py_sanitise_field "$mapped")', which is not one of the four." \
      "The four subsystems are: $(acas_py_join_words "${ACAS_PY_SUBSYSTEMS[@]}")."
    acas_py_log "$(printf '  %-16s %-8s %-34s %s [%s]' \
      "$operation" \
      "$mapped" \
      "$(acas_py_operation_field "$operation" 3)" \
      "$(acas_py_operation_field "$operation" 4)" \
      "$(acas_py_operation_field "$operation" 5)")"
  done
}

# acas_py_operation_field <operation> <1..5>
# Field 1 is the operation, 2 the subsystem, 3 the migrated module, 4 the menu
# paragraph, 5 its locator. Split on '|' -- see the map's own note on why not
# a colon.
acas_py_operation_field() {
  local operation="$1" want="$2" entry rest index
  for entry in "${ACAS_PY_OPERATION_MAP[@]}"; do
    if [[ "${entry%%|*}" != "$operation" ]]; then
      continue
    fi
    rest="$entry"
    for (( index = 1; index < want; index++ )); do
      rest="${rest#*|}"
    done
    printf '%s' "${rest%%|*}"
    return 0
  done
  acas_py_die "$EX_USAGE" \
    "operation '$(acas_py_sanitise_field "$operation")' has no entry in the operation map."
}

# =============================================================================
# THE RUN LOG, THE WORKING DIRECTORY AND THE RUN LOCK
#
# All three live under $ACAS_OUT/run-logs/, deliberately OUTSIDE $ACAS_OUT/<scenario>/.
# The determinism test compares scenario captures byte for byte, and this log
# necessarily carries an absolute path and an elapsed count, so a file containing
# it can never be allowed into a compared tree (R-6).
# =============================================================================
acas_py_run_logs_dir() {
  printf '%s' "$ACAS_OUT/run-logs/$ACAS_PY_SCENARIO"
}

acas_py_open_log() {
  ACAS_PY_CURRENT_STAGE='opening the run log'
  local dir
  if [[ -z "$ACAS_PY_LOG" ]]; then
    dir="$(acas_py_run_logs_dir)"
    ACAS_PY_LOG="$dir/python.log"
  else
    dir="${ACAS_PY_LOG%/*}"
  fi

  # A symlinked leaf is refused outright, and containment is re-checked AFTER the
  # directory is created, because creating a directory follows any symlink along
  # the way.
  [[ ! -L "$ACAS_PY_LOG" ]] || acas_py_die "$EX_USAGE" \
    "the run log is a symbolic link: $(acas_py_sanitise_field "$ACAS_PY_LOG")" \
    'A symlinked destination can point anywhere, including into a compared tree or' \
    'into the frozen checkout, so it is refused rather than followed.'
  acas_py_assert_outside_repo 'the run log' "$ACAS_PY_LOG"
  acas_py_assert_outside_tree 'the run log' "$ACAS_PY_LOG" \
    "$ACAS_PY_OUT_DIR/$ACAS_PY_SCENARIO" \
    'That tree is what the diff stage compares byte for byte. A run log written' \
    'into it would be diffed as though it were posted data and would corrupt the' \
    'parity evidence (R-6). The default location is under run-logs/ for exactly' \
    'this reason.'

  if (( ACAS_PY_DRY_RUN )); then
    acas_py_note "a dry run writes nothing, so no run log is opened (it would have been $ACAS_PY_LOG)"
    return 0
  fi

  if ! mkdir -p -- "$dir" 2>/dev/null; then
    acas_py_die "$EX_PRECONDITION" \
      "cannot create the run-log directory: $(acas_py_sanitise_field "$dir")"
  fi
  acas_py_assert_outside_repo 'the run-log directory, after creation' "$dir"
  acas_py_assert_outside_tree 'the run-log directory, after creation' "$dir" \
    "$ACAS_PY_OUT_DIR/$ACAS_PY_SCENARIO" \
    'Re-checked after creation because creating a directory follows a symlink along' \
    'the way, so the path that existed a moment ago is not necessarily the path' \
    'that exists now.'

  if ! : >>"$ACAS_PY_LOG" 2>/dev/null; then
    acas_py_die "$EX_PRECONDITION" \
      "cannot append to the run log: $(acas_py_sanitise_field "$ACAS_PY_LOG")"
  fi
  ACAS_PY_LOG_OPEN=1
  acas_py_tee ""
  acas_py_tee "==> harness/run_python_scenario.sh -- stage 6, scenario $ACAS_PY_SCENARIO"
  acas_py_log "run log = $ACAS_PY_LOG"
}

# Move to a writable directory OUTSIDE the checkout, so that no relative output
# path any child might build can land in a frozen tree. Under run-logs/ rather
# than at the top of the output area, so that even a stray relative write lands
# outside every tree the diff stage compares.
acas_py_enter_workdir() {
  ACAS_PY_CURRENT_STAGE='entering the working directory'
  if (( ACAS_PY_DRY_RUN )); then
    return 0
  fi
  ACAS_PY_WORKDIR="$(acas_py_run_logs_dir)"
  acas_py_assert_outside_repo 'the working directory' "$ACAS_PY_WORKDIR"
  if ! mkdir -p -- "$ACAS_PY_WORKDIR" 2>/dev/null; then
    acas_py_die "$EX_PRECONDITION" \
      "cannot create the working directory: $(acas_py_sanitise_field "$ACAS_PY_WORKDIR")"
  fi
  if ! cd -- "$ACAS_PY_WORKDIR"; then
    acas_py_die "$EX_PRECONDITION" \
      "cannot enter the working directory: $(acas_py_sanitise_field "$ACAS_PY_WORKDIR")"
  fi
  acas_py_log "working directory = $ACAS_PY_WORKDIR (outside the checkout, outside every compared tree)"
}

# -----------------------------------------------------------------------------
# THE SEQUENTIAL RUN LOCK  (R-3)
#
# The database is shared, so two scenarios running at the same time would each
# invalidate the other. The lock records the OWNING PROCESS so that a later
# invocation can ask whether that process still exists: a live holder is refused
# and its identity named, a stale holder -- gone, or an unreadable body -- is
# reclaimed with a warning so the harness recovers by itself, and the create is
# still done with the shell's no-clobber flag AFTER the reclaim, so if two
# invocations race between the staleness check and the create then exactly one
# wins and the loser is refused rather than both proceeding.
#
# An EMPTY lock file would be atomic and still wrong: a container killed mid-run
# would leave a file no later invocation could tell from a live run, and the
# harness would refuse every subsequent scenario for ever.
#
# Deliberately not a kernel advisory lock: one is not guaranteed present in the
# harness image, and a lock that silently degrades to no lock is worse than none.
#
# This is the ONLY place a process id is written, and it is two directory levels
# away from any tree the diff stage compares, so it cannot reach a capture (R-6).
# No second exit trap is installed: the single statically-quoted trap at the top
# of this file reaches the lock through the release helper, which is gated on
# ownership, so a refused acquisition can never delete the live holder's lock.
# -----------------------------------------------------------------------------
acas_py_take_lock() {
  ACAS_PY_CURRENT_STAGE='taking the sequential run lock'
  if (( ACAS_PY_DRY_RUN )); then
    acas_py_note 'a dry run invokes no operation, so it takes no run lock'
    return 0
  fi

  ACAS_PY_LOCK="$ACAS_OUT/run-logs/.run_python_scenario.lock"
  acas_py_assert_outside_repo 'the sequential run lock' "$ACAS_PY_LOCK"

  if ! mkdir -p -- "${ACAS_PY_LOCK%/*}" 2>/dev/null; then
    acas_py_die "$EX_PRECONDITION" \
      "cannot create the lock directory: $(acas_py_sanitise_field "${ACAS_PY_LOCK%/*}")"
  fi

  local holder=''
  if [[ -e "$ACAS_PY_LOCK" ]]; then
    if ! holder="$(cat -- "$ACAS_PY_LOCK" 2>/dev/null)"; then
      holder=''
    fi
    if [[ "$holder" =~ ^[0-9]+$ ]] && kill -0 "$holder" 2>/dev/null; then
      acas_py_die "$EX_PRECONDITION" \
        "another harness/run_python_scenario.sh (process $holder) is already running." \
        "lock file: $ACAS_PY_LOCK" \
        'Execution must be strictly sequential (R-3): the database is shared, and two' \
        'scenarios running at once would each invalidate the other. Wait for it to' \
        'finish.'
    fi
    acas_py_warn "reclaiming a stale run lock left by process ${holder:-<unreadable>} at $ACAS_PY_LOCK"
    if ! rm -f -- "$ACAS_PY_LOCK" 2>/dev/null; then
      acas_py_die "$EX_PRECONDITION" \
        "a stale run lock could not be removed: $(acas_py_sanitise_field "$ACAS_PY_LOCK")"
    fi
  fi

  if ! (set -C; printf '%s\n' "$$" >"$ACAS_PY_LOCK") 2>/dev/null; then
    acas_py_die "$EX_PRECONDITION" \
      "could not take the run lock $(acas_py_sanitise_field "$ACAS_PY_LOCK")." \
      'Either another run took it in the last instant, or the output area is not' \
      'writable.'
  fi
  ACAS_PY_LOCK_HELD=1
}

# =============================================================================
# THE PINNED VALUES
#
# Every one of these changes what the run writes, so none of them may be left to
# a default that happens to be whatever the database currently holds (R-6).
# =============================================================================
acas_py_resolve_pinned_values() {
  ACAS_PY_CURRENT_STAGE='resolving the pinned scenario values'
  acas_py_stage 'Stage 3/8: the pinned run date, date form, switches and tables'

  # THE RUN DATE, exactly as the scenario writes it. Passed through unchanged
  # (D-3): the migrated argument layer accepts one canonical form, so the digits
  # are never reordered to match the date form. This script does NOT validate the
  # date against the calendar, because the frozen date module's rejection is
  # itself specified behaviour -- it leaves its output field untouched
  # [common/maps04.cbl:L146] and the caller pre-zeroes it
  # [copybooks/Proc-ACAS-Mapser-RDB.cob:L78] -- so a rejected date must reach the
  # migrated cycle and produce a zero run date there, not be refused here (R-3).
  ACAS_PY_RUN_DATE_TEXT="$(acas_py_scenario_scalar run_date_text)"
  [[ -n "$ACAS_PY_RUN_DATE_TEXT" ]] || acas_py_die "$EX_SCENARIO" \
    'the scenario does not pin a run date.' \
    'Add a run_date_text: key, e.g. "21/09/2025". There is deliberately no default:' \
    'a run date is never taken from the host clock, so that two runs of one' \
    'scenario are byte-identical (R-6).'
  if (( ${#ACAS_PY_RUN_DATE_TEXT} != 10 )); then
    acas_py_die "$EX_SCENARIO" \
      "run_date_text must be ten characters, the width of to-day pic x(10); got '$(acas_py_sanitise_field "$ACAS_PY_RUN_DATE_TEXT")'." \
      'The text date is one of the two observables the controlled clock pins' \
      '[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80].'
  fi

  # The other observable. Not enforced before the run -- that would be a new
  # validation -- but reported against afterwards, because a rejected date shows
  # up either as zero or as the previous value and neither is visible without
  # reading the column back.
  ACAS_PY_RUN_DATE_BINARY="$(acas_py_scenario_scalar run_date_binary)"
  [[ -n "$ACAS_PY_RUN_DATE_BINARY" ]] || acas_py_die "$EX_SCENARIO" \
    'the scenario does not pin the expected binary run date.' \
    'Add a run_date_binary: key -- the value Run-Date binary-long' \
    '[copybooks/wssystem.cob:L67] must hold after the run.'
  [[ "$ACAS_PY_RUN_DATE_BINARY" =~ ^[0-9]+$ ]] || acas_py_die "$EX_SCENARIO" \
    "run_date_binary must be a whole number; got '$(acas_py_sanitise_field "$ACAS_PY_RUN_DATE_BINARY")'."

  # THE DATE FORM [copybooks/wssystem.cob:L128-L131].
  ACAS_PY_DATE_FORM="$(acas_py_scenario_default date_form 1)"
  case "$ACAS_PY_DATE_FORM" in
    1|2|3) ;;
    *)
      acas_py_die "$EX_SCENARIO" \
        "date_form must be 1, 2 or 3; got '$(acas_py_sanitise_field "$ACAS_PY_DATE_FORM")'." \
        'The three condition names are 88 Date-UK value 1, 88 Date-USA value 2 and' \
        '88 Date-Intl value 3 [copybooks/wssystem.cob:L128-L131]. The migrated option' \
        'accepts the whole one-digit domain, because the frozen menu coerces an' \
        'out-of-range value rather than refusing it -- but a SCENARIO must pin one of' \
        'the three real forms, or the two runners are not pinning the same thing.'
      ;;
  esac

  # THE IRS FAN-OUT SWITCH. Three states, and the key must be PRESENT even for
  # the blank one: its state changes WHICH TABLES a run touches, so a default
  # would leave the affected-table list ambiguous (Agent Action Plan 0.6.4).
  # See deviation D-2 for why the blank state is passed as a literal space.
  if acas_py_scenario_has_key irs_instead; then
    ACAS_PY_IRS_INSTEAD="$(acas_py_scenario_scalar irs_instead)"
  else
    acas_py_die "$EX_SCENARIO" \
      'the scenario does not pin the IRS fan-out switch.' \
      'Add an irs_instead: key. The field is three-state at' \
      '[copybooks/wssystem.cob:L179-L181]: 05 IRS-Instead pic x, with' \
      '88 IRS-Used value "Y" and 88 IRS-Both-Used value "B".' \
      'Write irs_instead: "" or irs_instead: " " for General Ledger only -- the' \
      'declared value of the field is a space -- "Y" for IRS instead of the General' \
      'Ledger, or "B" for IRS as well as it. The key is required even for the blank' \
      'state, because its value decides which tables the run touches and therefore' \
      'what the affected-table list has to say.'
  fi
  case "$ACAS_PY_IRS_INSTEAD" in
    ''|' ')
      # D-2: the GL-only state is the space the record declares. It is passed as
      # a single space and never as a letter standing for "off": the migrated
      # option does not validate the character, so a letter would be stored in
      # the column where the compiled cycle stores a space.
      ACAS_PY_IRS_INSTEAD=' '
      ;;
    Y|B) ;;
    *)
      acas_py_die "$EX_SCENARIO" \
        "irs_instead must be \"\" (or \" \"), \"Y\" or \"B\"; got '$(acas_py_sanitise_field "$ACAS_PY_IRS_INSTEAD")'." \
        'The field has exactly two condition names [copybooks/wssystem.cob:L179-L181],' \
        'so it has exactly three states and there is no fourth to invent.'
      ;;
  esac
  ACAS_PY_IRS_INSTEAD_SHOWN="$(acas_py_render_char "$ACAS_PY_IRS_INSTEAD")"

  acas_py_resolve_gating_answers
  acas_py_resolve_tables

  acas_py_log "run date   = $(acas_py_sanitise_field "$ACAS_PY_RUN_DATE_TEXT")  (date_form $ACAS_PY_DATE_FORM, expected Run-Date $ACAS_PY_RUN_DATE_BINARY)"
  acas_py_note 'the date text is passed through unchanged; its digits are never reordered to match date_form (D-3)'
  case "$ACAS_PY_IRS_INSTEAD" in
    ' ') acas_py_log 'IRS fan-out = <space>  General Ledger only' ;;
    'Y') acas_py_log 'IRS fan-out = "Y"      IRS instead of the General Ledger' ;;
    'B') acas_py_log 'IRS fan-out = "B"      IRS as well as the General Ledger' ;;
  esac
}

# -----------------------------------------------------------------------------
# THE GATING ANSWERS
#
# Agent Action Plan section 0.3.4 splits the frozen program's interactive
# statements three ways. A display with no database effect becomes a log record;
# an accept whose only effect is to pause for acknowledgement is dropped
# entirely (O-1); and an accept that GATES A DATABASE WRITE becomes an explicit
# command-line parameter with the frozen default preserved. Five accepts are in
# the third class, and each is resolved here so that the harness and the module
# can never silently drift apart about what the answer was:
#
#   1  the end-of-cycle backup pre-flight [general/gl080.cbl:L295-L302].
#      Only Escape or A/a aborts, and the blank the field is pre-set to at L298
#      PROCEEDS, so the frozen default is to proceed. Aborting returns before any
#      write of any kind, leaving the database completely untouched.
#   2  the end-of-cycle disk-change option [general/gl080.cbl:L545]. Only 0
#      proceeds and only 9 aborts; the frozen program's own message reads
#      "Enter <0> to signify change made or <9> to abort this run"
#      [general/gl080.cbl:L252], and anything else is sent straight back to the
#      prompt [general/gl080.cbl:L548-L549], so those two are the only values the
#      program can proceed on. 9 is read twice more, to skip the whole archiving
#      walk and the whole of end-of-period processing, so it suppresses every
#      batch stamp, every posting delete, the ledger-quarter rollover and the
#      cycle increment. The frozen default is 0.
#   3  the end-of-cycle archive path [general/gl080.cbl:L530-L537], accepted
#      with update at L555 so the field is presented already holding the computed
#      path -- which makes "no override" the frozen default. A value whose first
#      character is a space returns the paragraph to its option prompt, from
#      which its exit is unreachable, so the run unit ends having performed no
#      archive, no posting delete, no batch stamp and no period rollover.
#   4  the sales payment run-confirm [sales/sl100.cbl:L310-L319] and
#   5  the purchase one [purchase/pl100.cbl:L302-L311]. The wording diverges and
#      the divergence is preserved. NEITHER HAS A DEFAULT: both move spaces into
#      the reply field and re-ask on a blank, so only the affirmative literal
#      proceeds and only the negative one declines. The scenario must therefore
#      state the answer, and this script refuses to guess.
#
#   and, in its own class because it is destructive, the IRS end-of-job clear
#   question [irs/irs030.cbl:L1715-L1727]. See below.
# -----------------------------------------------------------------------------
acas_py_resolve_gating_answers() {
  local operation needs_payment=0 needs_irs=0 needs_gl080=0

  for operation in "${ACAS_PY_RUN_OPS[@]}"; do
    case "$operation" in
      sl_cash_post|pl_payment_post) needs_payment=1 ;;
      irs_post)                     needs_irs=1 ;;
      gl_end_of_cycle)              needs_gl080=1 ;;
    esac
  done

  # THE IRS END-OF-JOB CLEAR ANSWER. Destructive, so it is pinned explicitly and
  # passed explicitly -- never left to the module's own default, so that the
  # harness default and the module default cannot silently drift.
  #
  # `if WS-Reply = "Y" / perform acas008-Open-Output' [irs/irs030.cbl:L1720-L1723]
  # and for that handler an open-for-output is a mass delete of every row of the
  # IRS transfer table [common/acas008.cbl:L309-L319].
  #
  # AND NOTE, because it is counter-intuitive: despite the "[Y]" in the prompt
  # text at [irs/irs030.cbl:L1716], AN EMPTY REPLY DOES NOT ANSWER Y. The test at
  # [irs/irs030.cbl:L1718-L1719] sends anything that is neither Y nor N straight
  # back to the prompt, for ever. The "[Y]" is display text only. That is why the
  # answer is a required scenario key here and not an assumed one.
  if (( needs_irs )); then
    ACAS_PY_IRS_CLEAR="$(acas_py_scenario_scalar irs_clear_postings)"
    [[ -n "$ACAS_PY_IRS_CLEAR" ]] || acas_py_die "$EX_SCENARIO" \
      'an irs_post scenario must pin the end-of-job clear answer.' \
      'Add an irs_clear_postings: key with "Y" or "N".' \
      'ONE ANSWER IS DESTRUCTIVE: "Y" performs acas008-Open-Output' \
      '[irs/irs030.cbl:L1723], which for that handler is a mass delete of every row' \
      "of $ACAS_PY_IRS_TRANSFER_TABLE [common/acas008.cbl:L309-L319]." \
      'There is no default because the frozen program has none: the prompt shows' \
      '"[Y]" but an empty reply re-asks for ever [irs/irs030.cbl:L1718-L1719].'
    case "$ACAS_PY_IRS_CLEAR" in
      Y|N) ;;
      *)
        acas_py_die "$EX_SCENARIO" \
          "irs_clear_postings must be Y or N; got '$(acas_py_sanitise_field "$ACAS_PY_IRS_CLEAR")'." \
          'Those are the only two replies the frozen program accepts' \
          '[irs/irs030.cbl:L1718-L1719].'
        ;;
    esac
  fi

  # THE PAYMENT RUN-CONFIRM. Required, for the reason above: neither frozen
  # program has a default.
  if (( needs_payment )); then
    ACAS_PY_PAYMENT_CONFIRM="$(acas_py_scenario_scalar payment_post_confirm)"
    [[ -n "$ACAS_PY_PAYMENT_CONFIRM" ]] || acas_py_die "$EX_SCENARIO" \
      'a payment-posting scenario must pin the run-confirm answer.' \
      'Add a payment_post_confirm: key with "YES" or "NO".' \
      'It gates EVERY database write the program makes: the first file is opened' \
      'only after the test, so declining reaches the exit having opened nothing and' \
      'written nothing. Neither program has a default -- both move spaces into the' \
      'reply field and re-ask on a blank [sales/sl100.cbl:L310-L319],' \
      '[purchase/pl100.cbl:L302-L311] -- so the scenario has to say.'
    case "$ACAS_PY_PAYMENT_CONFIRM" in
      YES|NO) ;;
      *)
        acas_py_die "$EX_SCENARIO" \
          "payment_post_confirm must be YES or NO; got '$(acas_py_sanitise_field "$ACAS_PY_PAYMENT_CONFIRM")'."
        ;;
    esac
  fi

  # THE END-OF-CYCLE ANSWERS. These three DO have frozen defaults, so they are
  # defaulted to those and never to something convenient.
  if (( needs_gl080 )); then
    ACAS_PY_GL080_PROCEED="$(acas_py_scenario_default gl080_proceed 'Y')"
    case "$ACAS_PY_GL080_PROCEED" in
      Y|A) ;;
      *)
        acas_py_die "$EX_SCENARIO" \
          "gl080_proceed must be Y (proceed) or A (abort); got '$(acas_py_sanitise_field "$ACAS_PY_GL080_PROCEED")'." \
          'In the frozen source only Escape and A/a abort; every other reply, including' \
          'the blank the field is pre-set to, proceeds [general/gl080.cbl:L295-L302].' \
          'So Y is the frozen default and is what this key defaults to.'
        ;;
    esac
    ACAS_PY_DISK_CHANGE="$(acas_py_scenario_default disk_change_option '0')"
    case "$ACAS_PY_DISK_CHANGE" in
      0|9) ;;
      *)
        acas_py_die "$EX_SCENARIO" \
          "disk_change_option must be 0 (proceed) or 9 (abort); got '$(acas_py_sanitise_field "$ACAS_PY_DISK_CHANGE")'." \
          'No other value can leave the frozen input loop: anything that is neither 0' \
          'nor 9 is sent back to the prompt [general/gl080.cbl:L548-L549]. The default' \
          'is 0, the value that proceeds -- NOT 9, which would suppress every batch' \
          'stamp, every posting delete, the ledger-quarter rollover and the cycle' \
          'increment [general/gl080.cbl:L324-L326], [general/gl080.cbl:L408-L409].'
        ;;
    esac
    # Absent means "no override", which is the frozen default: the accept is an
    # update field already holding the computed path [general/gl080.cbl:L555].
    ACAS_PY_ARCHIVE_PATH="$(acas_py_scenario_scalar archive_path_override)"
  fi

  # An optional override of the calling identity. Omitted, each route takes its
  # own default, which is the literal the corresponding menu moves:
  # [general/general.cbl:L512], [sales/sales.cbl:L481],
  # [purchase/purchase.cbl:L475]. Overriding it is offered because the field is a
  # genuine linkage parameter [copybooks/wscall.cob:L8], not because anything in
  # the migrated cycle needs it changed.
  ACAS_PY_CALLER="$(acas_py_scenario_scalar ws_caller)"
}

# -----------------------------------------------------------------------------
# THE AFFECTED-TABLE LIST -- what BOUNDS the comparison (D-4)
# -----------------------------------------------------------------------------
acas_py_resolve_tables() {
  local -a tables=()
  local table seen=''

  while IFS= read -r table; do
    [[ -n "$table" ]] || continue
    tables+=("$table")
  done < <(acas_py_scenario_list affected_tables)

  (( ${#tables[@]} > 0 )) || acas_py_die "$EX_SCENARIO" \
    'the scenario does not declare an affected-table list.' \
    'Add an affected_tables: key -- the same key the capture stage reads. It is' \
    'required, not optional: the comparison is evidence only if it is bounded by' \
    'the tables the scenario declares (Agent Action Plan 0.8.5), and it is also' \
    'what keeps the menu-exit rewrite of the system, defaults and totals records' \
    'out of the comparison for a scenario that does not affect them -- see' \
    'deviation D-4 and [general/general.cbl:L656].'

  for table in "${tables[@]}"; do
    acas_py_in_list "$table" "${ACAS_PY_INSCOPE_TABLES[@]}" || acas_py_die "$EX_SCENARIO" \
      "affected_tables names '$(acas_py_sanitise_field "$table")', which is not one of the 22 in-scope tables." \
      "The in-scope set is: $(acas_py_join_words "${ACAS_PY_INSCOPE_TABLES[@]}")." \
      'Names are spelled exactly as the frozen schema spells them, hyphens included.'
    if [[ "$seen" == *"|$table|"* ]]; then
      acas_py_die "$EX_SCENARIO" \
        "affected_tables names '$table' more than once." \
        'The capture stage would write the same file twice and the diff stage would' \
        'compare it twice, which proves nothing and hides a typo.'
    fi
    seen="$seen|$table|"
  done
  ACAS_PY_TABLES=("${tables[@]}")

  # An IRS run must declare the transfer table, because the end-of-job answer
  # changes whether it still holds any rows [irs/irs030.cbl:L1720-L1724]. Leaving
  # it out of the list would hide the single most visible effect of the run.
  local operation
  for operation in "${ACAS_PY_RUN_OPS[@]}"; do
    if [[ "$operation" == 'irs_post' ]]; then
      acas_py_in_list "$ACAS_PY_IRS_TRANSFER_TABLE" "${ACAS_PY_TABLES[@]}" \
        || acas_py_die "$EX_SCENARIO" \
        "an irs_post scenario must list $ACAS_PY_IRS_TRANSFER_TABLE in affected_tables." \
        "The end-of-job answer is '$ACAS_PY_IRS_CLEAR', and that answer decides whether" \
        'every row of that table is removed [irs/irs030.cbl:L1720-L1724] through the' \
        'handler mass delete at [common/acas008.cbl:L309-L319]. A comparison that does' \
        'not include it cannot see the run at all.'
    fi
  done

  acas_py_log "affected tables ($((${#ACAS_PY_TABLES[@]}))): $(acas_py_join_words "${ACAS_PY_TABLES[@]}")"
  acas_py_note 'the comparison is bounded by this list and by nothing else; the diff stage has no ignore-list, no tolerance list and no known-difference allowance (D-4)'
}

# =============================================================================
# THE PACKAGE AND THE DRIVER
#
# The package import below is the BARE ROOT ONLY. That is a legitimate
# availability probe and not a breach of the layering rule: the package root is
# deliberately not a convenience-import hub, so importing it reaches no internal
# module of the migrated cycle. Everything else this script needs from the
# migrated side it reaches as a SUBPROCESS, which is what Agent Action Plan
# section 0.4.3 requires of this tree.
#
# This script imports no data-frame library and no array library, and computes
# with nothing but integers (R-2).
# =============================================================================

# acas_py_probe_import <label> <statement> <advice-line>...
acas_py_probe_import() {
  local label="$1" statement="$2"
  shift 2
  local rc=0 started elapsed
  started="$SECONDS"
  acas_py_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  "${ACAS_DEADLINE_ARGV[@]}" "$ACAS_PY_PYTHON" -c "$statement" >/dev/null 2>&1 || rc=$?
  elapsed=$(( SECONDS - started ))
  acas_py_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_CLIENT" \
    'ACAS_TIMEOUT_CLIENT' "probing $label"
  if (( rc != 0 )); then
    acas_py_die "$EX_PRECONDITION" \
      "$label is not available to this interpreter (status $rc)." \
      "  interpreter: $(acas_py_sanitise_field "$ACAS_PY_PYTHON")" \
      "  PYTHONPATH : $(acas_py_sanitise_field "${PYTHONPATH:-}")" \
      "$@"
  fi
  acas_py_log "PASS  $label is available"
}

acas_py_assert_package() {
  ACAS_PY_CURRENT_STAGE='asserting the package and the driver'
  acas_py_stage 'Stage 4/8: interpreter, package and driver'

  acas_py_log "interpreter = $(acas_py_sanitise_field "$ACAS_PY_PYTHON") (Python ${ACAS_PY_REQUIRED_MAJOR}.${ACAS_PY_REQUIRED_MINOR})"

  acas_py_probe_import 'the acas_posting package' 'import acas_posting' \
    'The package is imported from the read-only checkout through PYTHONPATH; nothing' \
    'is installed into the checkout. Only the package ROOT is imported here, which' \
    'reaches no internal module -- every entry point below is run as a subprocess.'

  acas_py_probe_import 'the pinned database driver' 'import mysql.connector' \
    'It is what the capture stage of the protocol uses, so proving it here proves' \
    'the capture will be able to run. Install the pinned version listed in the' \
    'project requirements.'

  acas_py_probe_import 'the YAML reader' 'import yaml' \
    'It reads the scenario definitions. Install the pinned version listed in the' \
    'project requirements.'

  acas_py_note 'no data-frame library and no array library is imported anywhere in this stage; every number it computes with is an integer (R-2)'
}

# =============================================================================
# RESOLVING EVERY OPTION AGAINST THE MODULE THAT MUST PUBLISH IT
#
# THIS IS THE MOST IMPORTANT MECHANISM IN THIS FILE. The exact spelling of every
# promoted parameter belongs to the module that publishes it, and a spelling
# guessed here would either be refused by that module's argument layer -- which
# this script reports as a usage fault -- or, far worse, be quietly dropped and
# change what the run does. Dropping the fan-out switch makes the affected-table
# list ambiguous; dropping the IRS clear answer changes whether the transfer
# table still has any rows in it.
#
# So NO OPTION IS EVER PASSED WITHOUT FIRST BEING FOUND IN THE MODULE'S OWN HELP
# TEXT, and an option that is missing is a REFUSAL and never a fallback. Each
# module's help text is read at most once and cached, so resolving twenty options
# costs seven interpreter starts.
# =============================================================================

# acas_py_module_help <module>
# Read and cache one module's own help text.
acas_py_module_help() {
  local module="$1"
  if [[ -n "${ACAS_PY_HELP_CACHE[$module]+set}" ]]; then
    return 0
  fi
  local rc=0 text='' started elapsed
  started="$SECONDS"
  acas_py_deadline_prefix "$ACAS_TIMEOUT_HELP"
  text="$("${ACAS_DEADLINE_ARGV[@]}" "$ACAS_PY_PYTHON" -m "$module" --help 2>&1)" || rc=$?
  elapsed=$(( SECONDS - started ))
  acas_py_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_HELP" \
    'ACAS_TIMEOUT_HELP' "reading the help text of $module"
  if (( rc != 0 )); then
    acas_py_die "$EX_PRECONDITION" \
      "the module $(acas_py_sanitise_field "$module") could not report its own options (status $rc)." \
      'Every migrated entry point must be runnable as a module and must answer' \
      '--help, because that is how this stage proves an option exists before passing' \
      'it. The output it did produce, if any, is in the run log.' \
      "  interpreter: $(acas_py_sanitise_field "$ACAS_PY_PYTHON")" \
      "  PYTHONPATH : $(acas_py_sanitise_field "${PYTHONPATH:-}")"
  fi
  ACAS_PY_HELP_CACHE["$module"]="$text"
}

# acas_py_module_publishes <module> <flag>
# True when the module's help text names that option. Matched with word-ish
# boundaries rather than as a bare substring, so that one option cannot be
# mistaken for a longer one that merely contains it.
acas_py_module_publishes() {
  local module="$1" flag="$2"
  acas_py_module_help "$module"
  # `-' is last in each bracket expression so it is a literal and not a range.
  [[ "${ACAS_PY_HELP_CACHE[$module]}" =~ (^|[^[:alnum:]_-])"$flag"([^[:alnum:]_-]|$) ]]
}

# acas_py_require_flag <module> <flag> <why>...
# Refuse, loudly and immediately, if the module does not publish the option the
# scenario requires. Never falls back and never drops it.
acas_py_require_flag() {
  local module="$1" flag="$2"
  shift 2
  if acas_py_module_publishes "$module" "$flag"; then
    return 0
  fi
  acas_py_die "$EX_PRECONDITION" \
    "the module $(acas_py_sanitise_field "$module") does not publish the option $(acas_py_sanitise_field "$flag")." \
    "$@" \
    'This is refused rather than worked around. Passing the option anyway would be' \
    'reported by that module as a bad command line; dropping it would silently' \
    'change what the run does, which is the one failure this check exists to' \
    'prevent. Re-read the module and this stage against each other: one of them is' \
    'out of date.'
}

# acas_py_refuse_flag <module> <flag> <why>...
# The mirror image: refuse if the module publishes an option this route must
# NEVER be given. The IRS route is argument-poor on purpose, and its poverty is
# part of the specification [irs/irs030.cbl:L552-L554], so an option appearing
# there would mean the migrated side had grown a parameter the frozen linkage
# shape does not have.
acas_py_refuse_flag() {
  local module="$1" flag="$2"
  shift 2
  if ! acas_py_module_publishes "$module" "$flag"; then
    return 0
  fi
  acas_py_warn "the module $module unexpectedly publishes $flag; $*"
}

# =============================================================================
# THE OPTION SPELLINGS, NAMED ONCE
#
# Every one is checked against the publishing module's own help text before it is
# used, so a spelling that drifts is caught as a refusal rather than becoming a
# dropped input. Naming them once means a drift is corrected in one place.
# =============================================================================
readonly ACAS_PY_FLAG_RUN_DATE='--run-date'
readonly ACAS_PY_FLAG_DATE_FORM='--date-form'
readonly ACAS_PY_FLAG_IRS_INSTEAD='--irs-instead'
readonly ACAS_PY_FLAG_WS_CALLER='--ws-caller'
readonly ACAS_PY_FLAG_RUN_CONFIRMED='--run-confirmed'
readonly ACAS_PY_FLAG_NO_RUN_CONFIRMED='--no-run-confirmed'
readonly ACAS_PY_FLAG_DISK_CHANGE='--disk-change-option'
readonly ACAS_PY_FLAG_ARCHIVE_PATH='--archive-path-override'
readonly ACAS_PY_FLAG_OK_TO_POST='--ok-to-post'
readonly ACAS_PY_FLAG_NO_OK_TO_POST='--no-ok-to-post'
readonly ACAS_PY_FLAG_CLEAR_POSTING='--clear-posting-file'
readonly ACAS_PY_FLAG_NO_CLEAR_POSTING='--no-clear-posting-file'

# -----------------------------------------------------------------------------
# acas_py_operation_argv <operation>
# Publishes the option list for one operation in ACAS_PY_ARGV.
#
# THE MATRIX IS PER ROUTE AND THERE IS NO UNIVERSAL COMMAND LINE, because the
# three frozen linkage shapes are not one shape. The General Ledger and the
# Sales/Purchase routes carry a calling-data block, a system record and a run
# date; the IRS route carries neither a calling-data block nor a run date
# [irs/irs030.cbl:L552-L554] and its module therefore publishes neither the
# calling-data options nor the fan-out switch. Handing it one would be a bad
# command line, which is a fault of this script and is reported as one.
#
#   operation         always                       route-specific
#   gl_post_cycle     run date, date form,         none
#                     fan-out switch
#   gl_end_of_cycle   the same                     backup pre-flight,
#                                                  disk-change option,
#                                                  archive-path override
#   sl_invoice_post   the same                     none
#   sl_cash_post      the same                     run-confirm
#   pl_order_post     the same                     none -- the frozen
#                                                  confirmation is commented out
#                                                  at [purchase/pl060.cbl:L362-L371]
#   pl_payment_post   the same                     run-confirm
#   irs_post          run date ONLY                clear-posting-file
#
# The run date is required on EVERY route including the IRS one, and that is not
# a contradiction of "no to-day": the IRS route's second parameter is the
# ordinary system record, which carries Run-Date [copybooks/wssystem.cob:L67].
# -----------------------------------------------------------------------------
acas_py_operation_argv() {
  local operation="$1" module
  module="$(acas_py_operation_field "$operation" 3)"
  ACAS_PY_ARGV=()

  # The run date. Required everywhere, and passed through unchanged (D-3).
  acas_py_require_flag "$module" "$ACAS_PY_FLAG_RUN_DATE" \
    'Every route takes a run date, because every route is given a system record and' \
    'that record carries Run-Date [copybooks/wssystem.cob:L67]. A run date is never' \
    'taken from the host clock (R-6).'
  ACAS_PY_ARGV+=("$ACAS_PY_FLAG_RUN_DATE" "$ACAS_PY_RUN_DATE_TEXT")

  if [[ "$operation" == 'irs_post' ]]; then
    # The IRS route is argument-poor on purpose. These two checks are not
    # decoration: if the module ever grew either option it would mean the
    # migrated side had acquired a parameter the frozen three-parameter linkage
    # shape does not have, and the two sides would no longer be given the same
    # inputs.
    acas_py_refuse_flag "$module" "$ACAS_PY_FLAG_IRS_INSTEAD" \
      'the frozen IRS linkage shape carries no fan-out switch [irs/irs030.cbl:L552-L554], so nothing is passed for it here'
    acas_py_refuse_flag "$module" "$ACAS_PY_FLAG_WS_CALLER" \
      'the frozen IRS linkage shape carries no calling-data block [irs/irs030.cbl:L552-L554], so nothing is passed for it here'

    # The destructive answer, always passed explicitly so that the harness and
    # the module cannot drift about what it was.
    local clear_flag
    if [[ "$ACAS_PY_IRS_CLEAR" == 'Y' ]]; then
      clear_flag="$ACAS_PY_FLAG_CLEAR_POSTING"
    else
      clear_flag="$ACAS_PY_FLAG_NO_CLEAR_POSTING"
    fi
    acas_py_require_flag "$module" "$clear_flag" \
      'It is the end-of-job question at [irs/irs030.cbl:L1715-L1727], and one of its' \
      "two answers removes every row of $ACAS_PY_IRS_TRANSFER_TABLE through the handler" \
      'mass delete at [common/acas008.cbl:L309-L319]. It is a genuine scenario input' \
      'and is never left to a default.'
    ACAS_PY_ARGV+=("$clear_flag")
    return 0
  fi

  # The six routes that carry a system record with a date form and a fan-out
  # switch in it.
  acas_py_require_flag "$module" "$ACAS_PY_FLAG_DATE_FORM" \
    'The date form is a field of the system record [copybooks/wssystem.cob:L128-L131]' \
    'and a run must pin it, because it decides how the compiled side reads a date.'
  ACAS_PY_ARGV+=("$ACAS_PY_FLAG_DATE_FORM" "$ACAS_PY_DATE_FORM")

  acas_py_require_flag "$module" "$ACAS_PY_FLAG_IRS_INSTEAD" \
    'The fan-out switch decides WHICH TABLES the run touches' \
    '[copybooks/wssystem.cob:L179-L181], so leaving it unpinned would make the' \
    'affected-table list ambiguous. It is passed as the raw character the field' \
    'holds, never as a token standing for a state (D-2).'
  ACAS_PY_ARGV+=("$ACAS_PY_FLAG_IRS_INSTEAD" "$ACAS_PY_IRS_INSTEAD")

  if [[ -n "$ACAS_PY_CALLER" ]]; then
    acas_py_require_flag "$module" "$ACAS_PY_FLAG_WS_CALLER" \
      'The scenario overrides the calling identity WS-Caller pic x(8)' \
      '[copybooks/wscall.cob:L8], so the option has to exist to carry it. Remove the' \
      'ws_caller key from the scenario to take each route default instead.'
    ACAS_PY_ARGV+=("$ACAS_PY_FLAG_WS_CALLER" "$ACAS_PY_CALLER")
  fi

  case "$operation" in
    gl_end_of_cycle)
      local confirm_flag
      if [[ "$ACAS_PY_GL080_PROCEED" == 'Y' ]]; then
        confirm_flag="$ACAS_PY_FLAG_RUN_CONFIRMED"
      else
        confirm_flag="$ACAS_PY_FLAG_NO_RUN_CONFIRMED"
      fi
      acas_py_require_flag "$module" "$confirm_flag" \
        'It is the pre-run backup gate at [general/gl080.cbl:L295-L302]. Declining' \
        'returns before any write of any kind, so the answer changes whether the run' \
        'has any database effect at all.'
      ACAS_PY_ARGV+=("$confirm_flag")

      acas_py_require_flag "$module" "$ACAS_PY_FLAG_DISK_CHANGE" \
        'It is the disk-change option at [general/gl080.cbl:L545]. 9 suppresses the' \
        'archiving walk and the whole of end-of-period processing' \
        '[general/gl080.cbl:L324-L326], [general/gl080.cbl:L408-L409], so the answer' \
        'changes what the run writes.'
      ACAS_PY_ARGV+=("$ACAS_PY_FLAG_DISK_CHANGE" "$ACAS_PY_DISK_CHANGE")

      if [[ -n "$ACAS_PY_ARCHIVE_PATH" ]]; then
        acas_py_require_flag "$module" "$ACAS_PY_FLAG_ARCHIVE_PATH" \
          'The scenario overrides the archive path of' \
          '[general/gl080.cbl:L530-L537], so the option has to exist to carry it.' \
          'Remove the archive_path_override key to take the frozen default, which is' \
          'no override.'
        ACAS_PY_ARGV+=("$ACAS_PY_FLAG_ARCHIVE_PATH" "$ACAS_PY_ARCHIVE_PATH")
      fi
      ;;
    sl_cash_post|pl_payment_post)
      local post_flag
      if [[ "$ACAS_PY_PAYMENT_CONFIRM" == 'YES' ]]; then
        post_flag="$ACAS_PY_FLAG_OK_TO_POST"
      else
        post_flag="$ACAS_PY_FLAG_NO_OK_TO_POST"
      fi
      acas_py_require_flag "$module" "$post_flag" \
        'It is the run-confirm at [sales/sl100.cbl:L310-L319] and' \
        '[purchase/pl100.cbl:L302-L311], whose wording diverges between the two and' \
        'whose divergence is preserved. It gates every database write the program' \
        'makes, and neither program has a default, so the answer is a genuine' \
        'scenario input.'
      ACAS_PY_ARGV+=("$post_flag")
      ;;
    gl_post_cycle|sl_invoice_post)
      # No promoted parameter. Recorded rather than left silent, so a reader
      # comparing the routes does not conclude one was forgotten.
      :
      ;;
    pl_order_post)
      # Deliberately none: the Purchase orders-posting program's own confirmation
      # is commented out in the frozen source [purchase/pl060.cbl:L362-L371], so
      # there is no prompt to promote. The divergence from the Sales route is
      # preserved, not harmonised (R-4).
      :
      ;;
  esac
}

# =============================================================================
# THE DATABASE -- READ-ONLY, ALWAYS
#
# Every statement this script sends is a SELECT. No data-definition statement of
# any kind is issued, no session variable is set, and nothing is seeded or reset
# here: those are stages 1 and 5 (R-3).
#
# The transport policy is fail-closed and is the same one the migrated side and
# the capture stage apply: a named certificate authority means encryption with
# BOTH the certificate and the host name verified, because encrypting without
# verifying accepts any certificate and is not verification at all; a loopback
# address or a socket path needs no declaration, never leaving the machine; and
# any other target with neither an authority nor an explicit declaration is
# REFUSED before anything connects, because the credential here is the one the
# compiled cycle itself uses.
#
# The driver rather than a client binary, deliberately: it is exactly what the
# capture stage uses, so proving a connection here proves the capture can be
# taken -- and it keeps this stage runnable on a host that has an interpreter and
# nothing else, which is what R-1 is ultimately about.
# =============================================================================
acas_py_db() {
  # acas_py_db <mode> [table...]     mode is `probe' or `counts'
  acas_py_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  "${ACAS_DEADLINE_ARGV[@]}" "$ACAS_PY_PYTHON" - "$@" <<'PY'
import os
import re
import sys

try:
    import mysql.connector as driver
except ModuleNotFoundError as exc:
    sys.stderr.write("the pinned database driver is not importable: %s\n" % exc)
    raise SystemExit(3)

MODE = sys.argv[1]
TABLES = sys.argv[2:]
AFFIRMATIVE = frozenset({"1", "true", "yes", "on"})
LOOPBACK = frozenset({"", "localhost", "localhost.localdomain", "127.0.0.1", "::1"})
IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def whole_seconds(name, default):
    text = (os.environ.get(name) or "").strip()
    if not text:
        return default
    if not text.isdigit() or int(text) < 1:
        sys.stderr.write(
            "%s must be a whole number of seconds of at least 1; got %r\n"
            % (name, text)
        )
        raise SystemExit(2)
    return int(text)


host = (os.environ.get("ACAS_DB_HOST") or "").strip()
socket_path = (os.environ.get("ACAS_DB_SOCKET") or "").strip()
tls_ca = (os.environ.get("ACAS_DB_TLS_CA") or "").strip()
tls_cert = (os.environ.get("ACAS_DB_TLS_CERT") or "").strip()
tls_key = (os.environ.get("ACAS_DB_TLS_KEY") or "").strip()
declared = (
    (os.environ.get("ACAS_DB_ALLOW_PLAINTEXT") or "").strip().lower() in AFFIRMATIVE
)
is_local = bool(socket_path) or host.strip("[]").lower() in LOOPBACK

kwargs = {
    "host": host,
    "port": int((os.environ.get("ACAS_DB_PORT") or "0").strip() or 0),
    "database": (os.environ.get("ACAS_DB_NAME") or "").strip(),
    "user": (os.environ.get("ACAS_DB_USER") or "").strip(),
    "password": os.environ.get("ACAS_DB_PASSWORD") or "",
    # Pin the conversion rather than leaning on a default: an exact-decimal
    # column must arrive as an exact decimal and every integer width as an
    # integer (R-2). Nothing here formats a value as a real number.
    "raw": False,
    "use_unicode": True,
    "connect_timeout": whole_seconds("ACAS_DB_CONNECT_TIMEOUT", 10),
    "read_timeout": whole_seconds("ACAS_DB_READ_TIMEOUT", 300),
    "write_timeout": whole_seconds("ACAS_DB_WRITE_TIMEOUT", 60),
}
if socket_path:
    kwargs["unix_socket"] = socket_path

if tls_ca:
    kwargs.update(
        {
            "ssl_ca": tls_ca,
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_disabled": False,
        }
    )
    if tls_cert:
        kwargs["ssl_cert"] = tls_cert
    if tls_key:
        kwargs["ssl_key"] = tls_key
elif not (is_local or declared):
    sys.stderr.write(
        "the target is neither a loopback address nor a socket, no certificate "
        "authority is named in ACAS_DB_TLS_CA, and ACAS_DB_ALLOW_PLAINTEXT does "
        "not declare the network isolated. Refused before connecting: the "
        "credential used here is the one the compiled cycle itself uses. Set "
        "ACAS_DB_TLS_CA to encrypt and verify, or declare the harness network "
        "with ACAS_DB_ALLOW_PLAINTEXT=1.\n"
    )
    raise SystemExit(6)

try:
    connection = driver.connect(**kwargs)
except Exception as exc:  # driver-specific, reported without echoing the server
    errno = getattr(exc, "errno", "unknown")
    sqlstate = getattr(exc, "sqlstate", "unknown")
    sys.stderr.write(
        "could not connect to the ACAS database (errno %s, sqlstate %s). The "
        "host, port, schema, account and the driver's own text are "
        "deliberately not echoed: they identify the server and who reaches it, "
        "and driver text is arbitrary server-supplied content.\n"
        % (errno, sqlstate)
    )
    raise SystemExit(7)

status = 0
try:
    cursor = connection.cursor()
    try:
        if MODE == "probe":
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = %s",
                ((os.environ.get("ACAS_DB_NAME") or "").strip(),),
            )
            row = cursor.fetchone()
            sys.stdout.write("tables\t%d\n" % int(row[0] if row else 0))
            cursor.execute("SELECT @@autocommit")
            row = cursor.fetchone()
            sys.stdout.write("autocommit\t%s\n" % ("" if row is None else row[0]))
        elif MODE == "system":
            # The two observables the controlled clock pins, read back so that a
            # date the frozen module rejected is VISIBLE. It leaves its output
            # field untouched on a rejection [common/maps04.cbl:L146] and the
            # caller pre-zeroes it [copybooks/Proc-ACAS-Mapser-RDB.cob:L78], so a
            # rejected date shows up either as zero or as the previous value and
            # neither can be seen without reading the column.
            for column in TABLES:
                if not IDENTIFIER.match(column):
                    sys.stderr.write("%r is not a plain column name\n" % column)
                    status = 2
                    break
                quoted = "`%s`" % column.replace("`", "``")
                try:
                    cursor.execute(
                        "SELECT %s FROM `SYSTEM-REC` LIMIT 1" % quoted
                    )
                    row = cursor.fetchone()
                except Exception as exc:
                    errno = getattr(exc, "errno", "unknown")
                    sys.stdout.write("%s\t-\n" % column)
                    sys.stderr.write(
                        "%s could not be read (errno %s)\n" % (column, errno)
                    )
                    continue
                if row is None:
                    sys.stdout.write("%s\t-\n" % column)
                else:
                    sys.stdout.write("%s\t%s\n" % (column, row[0]))
        elif MODE == "counts":
            for table in TABLES:
                if not IDENTIFIER.match(table):
                    sys.stderr.write(
                        "%r is not a plain table name; it is composed into a "
                        "quoted identifier, so a name carrying a quote, a "
                        "backquote or whitespace is refused rather than "
                        "escaped.\n" % table
                    )
                    status = 2
                    break
                quoted = "`%s`" % table.replace("`", "``")
                try:
                    cursor.execute("SELECT COUNT(*) FROM %s" % quoted)
                    row = cursor.fetchone()
                    sys.stdout.write(
                        "%s\t%d\n" % (table, int(row[0] if row else 0))
                    )
                except Exception as exc:  # a table that is not there
                    errno = getattr(exc, "errno", "unknown")
                    sys.stdout.write("%s\t-\n" % table)
                    sys.stderr.write(
                        "%s could not be counted (errno %s)\n" % (table, errno)
                    )
        else:
            sys.stderr.write("unknown mode %r\n" % MODE)
            status = 2
    finally:
        cursor.close()
finally:
    # A read-only session: rolling back writes nothing and releases the
    # read-only transaction the server opens when autocommit is off. No session
    # variable is set anywhere above, so the server is read exactly as it was
    # configured (R-3).
    connection.rollback()
    connection.close()

raise SystemExit(status)
PY
}

acas_py_assert_database() {
  ACAS_PY_CURRENT_STAGE='asserting the database'
  acas_py_stage 'Stage 5/8: database, schema and session'

  local rc=0 out='' started elapsed
  started="$SECONDS"
  out="$(acas_py_db probe)" || rc=$?
  elapsed=$(( SECONDS - started ))
  acas_py_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_CLIENT" \
    'ACAS_TIMEOUT_CLIENT' 'probing the database'
  if (( rc != 0 )); then
    acas_py_die "$EX_DATABASE" \
      "the database could not be read (status $rc)." \
      "  server : $(acas_py_sanitise_field "$ACAS_DB_HOST"):$ACAS_DB_PORT" \
      "  schema : $(acas_py_sanitise_field "$ACAS_DB_NAME")" \
      "  account: $(acas_py_sanitise_field "$ACAS_DB_USER")" \
      'The reason the driver gave is above; the password is not part of it. Start the' \
      'harness database service, or apply the frozen schema to it, before this stage.'
  fi

  local key value table_count='' autocommit=''
  while IFS=$'\t' read -r key value; do
    case "$key" in
      tables)     table_count="$value" ;;
      autocommit) autocommit="$value" ;;
    esac
  done <<< "$out"

  [[ "$table_count" =~ ^[0-9]+$ ]] || acas_py_die "$EX_DATABASE" \
    "the schema table count could not be read; got '$(acas_py_sanitise_field "$table_count")'."
  acas_py_log "schema $ACAS_DB_NAME holds $table_count tables (the frozen schema defines $ACAS_PY_REQUIRED_TABLES)"
  if (( 10#$table_count != ACAS_PY_REQUIRED_TABLES )); then
    acas_py_die "$EX_DATABASE" \
      "schema $ACAS_DB_NAME holds $table_count tables, not $ACAS_PY_REQUIRED_TABLES." \
      'The frozen schema is applied verbatim by the reset stage and defines exactly' \
      'that many. A different count means either the schema was never applied, or' \
      'something has altered it -- and either way a comparison against the compiled' \
      'oracle would be evidence of nothing. Nothing is repaired here: this stage' \
      'issues no data-definition statement at all (R-3).'
  fi

  # OBSERVED AND REPORTED, NEVER SET. The session policy of the migrated run
  # belongs to the migrated data-access layer, which applies per-statement
  # autocommit as the compiled cycle does. Overriding the server here would
  # change the run rather than measure it, so the value is put on the record next
  # to the run it applied to and nothing else is done with it. This is also why
  # the oracle side's autocommit refusal status is deliberately not reused here.
  acas_py_log "server autocommit = $(acas_py_render_char "$autocommit")  (observed, never set)"
  acas_py_summary_row 'server autocommit' "$(acas_py_render_char "$autocommit")"
}

# acas_py_table_counts <table>...
# Publishes "<table><TAB><count>" lines, in the order asked, in ACAS_PY_SQL_OUT.
# A table that cannot be counted yields a hyphen rather than aborting, because a
# table's absence is a fact to report and not this stage's business to repair.
acas_py_table_counts() {
  local rc=0 started elapsed
  ACAS_PY_SQL_OUT=''
  started="$SECONDS"
  ACAS_PY_SQL_OUT="$(acas_py_db counts "$@")" || rc=$?
  elapsed=$(( SECONDS - started ))
  acas_py_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_CLIENT" \
    'ACAS_TIMEOUT_CLIENT' 'counting rows'
  return "$rc"
}

# =============================================================================
# THE SEED FINGERPRINT
#
# The two sides of a comparison must START from the same state, and nothing else
# in the protocol proves it. Without this check, a re-seed that quietly loaded a
# different fixture produces a diff full of real differences with no indication
# that the cause was the seed rather than the cycle -- which is a false failure
# that costs a day to find. So each side records the row count of every table the
# scenario names, in the order the scenario names them, and this side refuses to
# proceed if the other side recorded something different.
#
# Row counts only, all integers (R-2). BOTH fingerprints live under run-logs/ and
# never under a compared tree, so neither can reach a capture (R-6).
# =============================================================================
acas_py_seed_fingerprint() {
  ACAS_PY_CURRENT_STAGE='recording the seed fingerprint'
  acas_py_stage 'Stage 6a/8: the pre-run seed fingerprint'

  local dir
  dir="$(acas_py_run_logs_dir)"
  ACAS_PY_FINGERPRINT="$dir/python.seed-fingerprint"
  acas_py_assert_outside_tree 'the seed fingerprint' "$ACAS_PY_FINGERPRINT" \
    "$ACAS_PY_OUT_DIR/$ACAS_PY_SCENARIO" \
    'A fingerprint written into a compared tree would be diffed as though it were' \
    'posted data (R-6).'

  local rc=0
  acas_py_table_counts "${ACAS_PY_TABLES[@]}" || rc=$?
  if (( rc != 0 )); then
    acas_py_die "$EX_DATABASE" \
      "the affected tables could not be counted before the run (status $rc)." \
      'The reason is above. A comparison whose starting state cannot be established' \
      'is not a comparison.'
  fi

  if ! printf '%s\n' "$ACAS_PY_SQL_OUT" >"$ACAS_PY_FINGERPRINT" 2>/dev/null; then
    acas_py_die "$EX_PRECONDITION" \
      "the seed fingerprint could not be written: $(acas_py_sanitise_field "$ACAS_PY_FINGERPRINT")"
  fi
  acas_py_log "seed fingerprint = $ACAS_PY_FINGERPRINT"
  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    acas_py_log "  $(printf '%-22s %s' "${line%%$'\t'*}" "${line##*$'\t'}")"
  done <<< "$ACAS_PY_SQL_OUT"

  # THE CROSS-CHECK. The oracle-side fingerprint is written by whatever recorded
  # the compiled run's starting state; when it is absent that is said plainly and
  # the run continues, because a missing cross-check is a weaker guarantee and not
  # a fault.
  local other="$dir/cobol.seed-fingerprint"
  if [[ ! -f "$other" ]]; then
    acas_py_note "no oracle-side seed fingerprint at $other, so the two starting states are UNVERIFIED for this run"
    acas_py_summary_row 'seed cross-check' 'unverified -- no oracle-side fingerprint'
    return 0
  fi
  if cmp -s -- "$ACAS_PY_FINGERPRINT" "$other"; then
    acas_py_log 'PASS  both sides started from the same row counts'
    acas_py_summary_row 'seed cross-check' 'matched'
    return 0
  fi
  acas_py_log 'this side:'
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    acas_py_log "  $line"
  done <"$ACAS_PY_FINGERPRINT"
  acas_py_log 'oracle side:'
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    acas_py_log "  $line"
  done <"$other"
  acas_py_die "$EX_PRECONDITION" \
    'the two sides did not start from the same seed, so a comparison would be meaningless.' \
    "  this side  : $ACAS_PY_FINGERPRINT" \
    "  oracle side: $other" \
    'Both fingerprints are printed above. This is a HARNESS FAULT and deliberately' \
    'not a behavioural difference: the cycles were never given the same starting' \
    'state, so nothing about their behaviour has been measured. Re-run the reset and' \
    'seed stages and then both run stages, in the protocol order.'
}

# =============================================================================
# THE DECLARED STATUSES
#
# Optional. Either one value for every operation, or a list matching the
# operations positionally. A status that contradicts its declaration is reported
# as a behavioural difference -- and the capture is still taken, so the diff stage
# can corroborate (R-4).
# =============================================================================
acas_py_resolve_expected() {
  local -a declared=()
  local item index
  while IFS= read -r item; do
    [[ -n "$item" ]] || continue
    declared+=("$item")
  done < <(acas_py_scenario_list expected_status)

  ACAS_PY_EXPECTED=()
  if (( ${#declared[@]} == 0 )); then
    for (( index = 0; index < ${#ACAS_PY_RUN_OPS[@]}; index++ )); do
      ACAS_PY_EXPECTED+=('')
    done
    acas_py_note 'the scenario declares no expected status, so every status is recorded and none is judged'
    return 0
  fi
  if (( ${#declared[@]} == 1 && ${#ACAS_PY_RUN_OPS[@]} > 1 )); then
    for (( index = 0; index < ${#ACAS_PY_RUN_OPS[@]}; index++ )); do
      ACAS_PY_EXPECTED+=("${declared[0]}")
    done
  elif (( ${#declared[@]} == ${#ACAS_PY_RUN_OPS[@]} )); then
    ACAS_PY_EXPECTED=("${declared[@]}")
  else
    acas_py_die "$EX_SCENARIO" \
      "expected_status declares ${#declared[@]} values for ${#ACAS_PY_RUN_OPS[@]} operations." \
      'Give one value for all of them, or exactly one per operation in the same' \
      'order. A partial list would silently pair a declaration with the wrong' \
      'operation.'
  fi
  for item in "${ACAS_PY_EXPECTED[@]}"; do
    [[ "$item" =~ ^[0-9]+$ ]] || acas_py_die "$EX_SCENARIO" \
      "expected_status values must be whole process statuses; got '$(acas_py_sanitise_field "$item")'." \
      'The term-code mapping is the identity, so 0 means the operation completed and' \
      'a non-zero value is the term code the frozen program set -- 5 for the General' \
      'Ledger open-batch abort [general/gl070.cbl:L289], 8 for the missing-extract' \
      'abort [sales/sl055.cbl:L344], [purchase/pl055.cbl:L286].'
  done
}

# =============================================================================
# RUNNING THE OPERATIONS
# =============================================================================

# Render an argument list so that the line printed is the line an operator could
# paste back. Nothing here carries a credential: the migrated entry points take
# none, so there is nothing to hide from this rendering.
#
# Single quotes rather than the shell's own quoting operator, and for a reason
# that matters to this file specifically: that operator renders a lone space as a
# backslash and a space, which is correct but reads as a trailing nothing -- and
# the one argument this stage passes that IS a lone space is the fan-out switch's
# General-Ledger-only state (D-2). An option whose value is invisible in the
# printed plan would defeat the whole point of printing it.
acas_py_quote_argv() {
  local out='' word
  for word in "$@"; do
    if [[ -n "$word" && "$word" != *[!A-Za-z0-9_./:=@%+,-]* ]]; then
      out+="${out:+ }$word"
    else
      # An embedded single quote is closed, escaped and reopened, which is the
      # only form that is safe inside single quotes.
      out+="${out:+ }'${word//\'/\'\\\'\'}'"
    fi
  done
  printf '%s' "$out"
}

# How many lines the run log holds. `awk' rather than a line-count utility so the
# answer arrives with no leading whitespace to strip.
acas_py_log_line_count() {
  if (( ACAS_PY_LOG_OPEN )) && [[ -f "$ACAS_PY_LOG" ]]; then
    awk 'END { print NR }' "$ACAS_PY_LOG"
  else
    printf '0'
  fi
}

# -----------------------------------------------------------------------------
# acas_py_run_operations
#
# STRICTLY SEQUENTIAL, and every operation the scenario lists is run, in order,
# UNCONDITIONALLY. There is no halt rule and there is no gate: the three abort
# gates diverge between the ledgers and they live inside the migrated modules,
# which reproduce them. An operator at the frozen menu returns to the menu after
# every option and then selects the next one, so a scenario that must not run a
# later operation simply does not list it (R-4).
#
# A non-zero status is RECORDED, not judged. It is interpreted only against the
# scenario's declaration, and even a contradiction does not stop the remaining
# work: the capture that follows is the evidence, and for a run-aborting
# rejection the evidence IS the absence of what the later phases would have
# written (Agent Action Plan 0.6.5).
# -----------------------------------------------------------------------------
acas_py_run_operations() {
  ACAS_PY_CURRENT_STAGE='running the migrated operations'
  acas_py_stage 'Stage 6b/8: the migrated cycle'

  local index operation module rc started elapsed before after declared
  ACAS_PY_OBSERVED=()

  for (( index = 0; index < ${#ACAS_PY_RUN_OPS[@]}; index++ )); do
    operation="${ACAS_PY_RUN_OPS[index]}"
    module="$(acas_py_operation_field "$operation" 3)"
    declared="${ACAS_PY_EXPECTED[index]}"
    acas_py_operation_argv "$operation"

    acas_py_log ""
    acas_py_log "operation $((index + 1))/${#ACAS_PY_RUN_OPS[@]}: $operation  ->  $module  [$(acas_py_operation_field "$operation" 5)]"
    acas_py_log "  $(acas_py_quote_argv "$ACAS_PY_PYTHON" -m "$module" "${ACAS_PY_ARGV[@]}")"

    before="$(acas_py_log_line_count)"
    rc=0
    started="$SECONDS"
    ACAS_PY_RAN=1
    acas_py_deadline_prefix "$ACAS_TIMEOUT_OPERATION"
    if (( ACAS_PY_LOG_OPEN )); then
      "${ACAS_DEADLINE_ARGV[@]}" "$ACAS_PY_PYTHON" -m "$module" \
          "${ACAS_PY_ARGV[@]}" >>"$ACAS_PY_LOG" 2>&1 || rc=$?
    else
      "${ACAS_DEADLINE_ARGV[@]}" "$ACAS_PY_PYTHON" -m "$module" \
          "${ACAS_PY_ARGV[@]}" || rc=$?
    fi
    elapsed=$(( SECONDS - started ))
    acas_py_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_OPERATION" \
      'ACAS_TIMEOUT_OPERATION' "the $operation operation"

    # Replay a bounded tail of what the operation wrote, so an operator sees the
    # end of it without the whole of a long report burying the summary. All of it
    # is in the run log either way.
    after="$(acas_py_log_line_count)"
    if (( ACAS_PY_LOG_OPEN )) && (( after > before )); then
      if ! sed -n "$(( before + 1 )),${after}p" -- "$ACAS_PY_LOG" \
          | tail -n "$ACAS_PY_CONSOLE_TAIL"; then
        acas_py_warn "the tail of the $operation output could not be replayed to the console; all of it is in the run log"
      fi
    fi

    ACAS_PY_OBSERVED+=("$rc")
    acas_py_log "  status = $rc (after ${elapsed}s)"

    # A bad command line is THIS SCRIPT'S fault and is never a behavioural
    # difference. The migrated argument layer reports one as status 2, which is
    # distinguishable from every term code the frozen programs set -- those are 5
    # and 8 [general/gl070.cbl:L289], [sales/sl055.cbl:L344],
    # [purchase/pl055.cbl:L286] -- and from a clean completion.
    if (( rc == 2 )); then
      acas_py_die "$EX_USAGE" \
        "the $operation module refused the command line this stage built for it." \
        "  $(acas_py_quote_argv "$ACAS_PY_PYTHON" -m "$module" "${ACAS_PY_ARGV[@]}")" \
        'Status 2 from an argument layer means a bad command line, so this is a fault' \
        'of the harness and not a behavioural difference. Every option above was' \
        'checked against that module own help text before it was used, so a refusal' \
        'here means the option exists but its VALUE was refused. The reason is in the' \
        'run log.'
    fi

    if [[ -z "$declared" ]]; then
      acas_py_log '  no status was declared for this operation, so it is recorded and not judged'
      continue
    fi
    if (( rc == 10#$declared )); then
      acas_py_log "  PASS  the declared status was $declared"
      continue
    fi
    ACAS_PY_BEHAVIOURAL=$(( ACAS_PY_BEHAVIOURAL + 1 ))
    acas_py_warn "$operation ended with status $rc but the scenario declared $declared"
    acas_py_log '  This is a BEHAVIOURAL DIFFERENCE, not a harness fault: the operation ran.'
    acas_py_log '  The capture is still taken, so the diff stage can corroborate -- for a'
    acas_py_log '  run-aborting rejection the database effect IS the absence of everything the'
    acas_py_log '  later phases would have written (Agent Action Plan 0.6.5).'
    acas_py_log '  The remaining operations still run: no gate is added and none removed (R-4).'
  done
}

# =============================================================================
# POST-RUN ASSERTIONS -- READ-ONLY, AND RECORDED RATHER THAN FATAL (D-8)
#
# Each one is a HARNESS self-check: that the run pinned what it said it pinned,
# and that the run is comparable at all. None of them is an opinion about the
# accounting -- that belongs to the diff stage.
# =============================================================================
acas_py_assert_after_run() {
  ACAS_PY_CURRENT_STAGE='post-run assertions'
  acas_py_stage 'Stage 6c/8: post-run assertions'

  local rc=0 line key value

  # 1. THE PINNED CLOCK ACTUALLY LANDED. Read back rather than assumed, because
  #    the frozen date module leaves its output field untouched when it rejects a
  #    date [common/maps04.cbl:L146] and the caller pre-zeroes it
  #    [copybooks/Proc-ACAS-Mapser-RDB.cob:L78], so a rejection shows up either as
  #    zero or as the previous value.
  ACAS_PY_SQL_OUT=''
  acas_py_deadline_prefix "$ACAS_TIMEOUT_CLIENT"
  ACAS_PY_SQL_OUT="$(acas_py_db system 'RUN-DAT' 'IRS-INSTEAD')" || rc=$?
  if (( rc != 0 )); then
    ACAS_PY_ASSERT_FAILURES=$(( ACAS_PY_ASSERT_FAILURES + 1 ))
    acas_py_warn "FAIL  the pinned system-record columns could not be read after the run (status $rc)"
  else
    local run_dat='' irs_after=''
    while IFS=$'\t' read -r key value; do
      case "$key" in
        RUN-DAT)     run_dat="$value" ;;
        IRS-INSTEAD) irs_after="$value" ;;
      esac
    done <<< "$ACAS_PY_SQL_OUT"

    if [[ "$run_dat" == "$ACAS_PY_RUN_DATE_BINARY" ]]; then
      acas_py_log "PASS  the system record holds Run-Date $run_dat, as pinned"
    elif [[ "$run_dat" == '-' ]]; then
      acas_py_note 'the system record holds no row, so the pinned run date cannot be read back; the seed did not load it'
    else
      ACAS_PY_ASSERT_FAILURES=$(( ACAS_PY_ASSERT_FAILURES + 1 ))
      acas_py_warn "FAIL  the system record holds Run-Date $(acas_py_render_char "$run_dat") but the scenario pinned $ACAS_PY_RUN_DATE_BINARY"
      if [[ "$run_dat" == '0' ]]; then
        acas_py_log '      A zero here is information and not noise: the frozen date module returns'
        acas_py_log '      its output field unchanged when it rejects a date [common/maps04.cbl:L146]'
        acas_py_log '      and the caller pre-zeroes it'
        acas_py_log '      [copybooks/Proc-ACAS-Mapser-RDB.cob:L78], so zero means the date was'
        acas_py_log '      rejected. That anomaly is reproduced, not masked (R-4).'
      fi
    fi

    # The fan-out switch must still hold what was pinned. Nothing in the cycle
    # should change it, and if it did then the affected-table list no longer
    # describes what the run touched.
    local trimmed="${irs_after%% }"
    if [[ "$irs_after" == '-' ]]; then
      acas_py_note 'the system record holds no row, so the fan-out switch cannot be read back'
    elif [[ "${trimmed:-" "}" == "${ACAS_PY_IRS_INSTEAD%% }" || "$irs_after" == "$ACAS_PY_IRS_INSTEAD" ]]; then
      acas_py_log "PASS  the fan-out switch still holds $ACAS_PY_IRS_INSTEAD_SHOWN"
    else
      ACAS_PY_ASSERT_FAILURES=$(( ACAS_PY_ASSERT_FAILURES + 1 ))
      acas_py_warn "FAIL  the fan-out switch changed from $ACAS_PY_IRS_INSTEAD_SHOWN to $(acas_py_render_char "$irs_after") during the run"
    fi
  fi

  # 2. THE FOUR AUTOGEN TABLES ARE UNTOUCHED. This is what makes deviation D-5
  #    -- the oracle side running one program this side does not
  #    [sales/sales.cbl:L759] -- safe to live with rather than merely asserted in
  #    prose. It also covers the Purchase pair, whose equivalent call and gate are
  #    both commented out [purchase/purchase.cbl:L755-L758], so on this side all
  #    four must be empty. A table that cannot be counted is noted and not failed:
  #    it is out of scope and its absence is not this stage's business to repair.
  rc=0
  acas_py_table_counts "${ACAS_PY_AUTOGEN_TABLES[@]}" || rc=$?
  if (( rc != 0 )); then
    acas_py_note "the autogen tables could not all be counted (status $rc); each result is reported below"
  fi
  while IFS=$'\t' read -r key value; do
    [[ -n "$key" ]] || continue
    case "$value" in
      0)
        acas_py_log "PASS  $key holds 0 rows -- neither autogen program ran on this side"
        ;;
      -)
        acas_py_note "$key could not be counted; it is out of scope and may not be present"
        ;;
      *)
        ACAS_PY_ASSERT_FAILURES=$(( ACAS_PY_ASSERT_FAILURES + 1 ))
        acas_py_warn "FAIL  $key holds $value rows; the autogen tables are never seeded and the migrated cycle never writes them, so this run is not comparable"
        ;;
    esac
  done <<< "$ACAS_PY_SQL_OUT"

  # 3. ROW COUNTS FOR THE SCENARIO'S OWN TABLES. Reported, never judged: the
  #    comparison belongs to the diff stage, and a count here is a breadcrumb for
  #    an operator reading the log.
  rc=0
  acas_py_table_counts "${ACAS_PY_TABLES[@]}" || rc=$?
  if (( rc != 0 )); then
    acas_py_note "not every affected table could be counted after the run (status $rc)"
  fi
  acas_py_log 'row counts for the affected tables after the run (reported, not judged):'
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    acas_py_log "  $(printf '%-22s %s' "${line%%$'\t'*}" "${line##*$'\t'}")"
  done <<< "$ACAS_PY_SQL_OUT"

  # 4. THE FROZEN CHECKOUT IS UNTOUCHED. The read-only mount is the belt and the
  #    bytecode-writing setting is the braces; this is the proof. Agent Action Plan
  #    section 0.8.1 treats ANY diff to the checkout as a defect "regardless of how
  #    harmless it appears", and an import that created a cache directory inside it
  #    would be exactly that.
  acas_py_assert_repo_untouched
}

acas_py_assert_repo_untouched() {
  if [[ ! -d "$ACAS_REPO/acas_posting" ]]; then
    acas_py_note 'the migrated package directory is not in the checkout, so there is nothing to check for cache directories'
    return 0
  fi

  local after entry
  after="$(acas_py_pycache_census)"

  if [[ "$after" == "$ACAS_PY_PYCACHE_BEFORE" ]]; then
    if [[ -z "$after" ]]; then
      acas_py_log 'PASS  no bytecode cache directory exists under the migrated package in the checkout'
    else
      acas_py_log 'PASS  this run created no bytecode cache directory inside the checkout'
      acas_py_note 'these already existed before this run started and are not its doing:'
      while IFS= read -r entry; do
        [[ -n "$entry" ]] || continue
        acas_py_log "  $(acas_py_sanitise_field "$entry")"
      done <<< "$ACAS_PY_PYCACHE_BEFORE"
      acas_py_log '      They are worth removing all the same. Bytecode writing is switched off for'
      acas_py_log '      every interpreter this stage runs and the checkout is mounted read-only, so'
      acas_py_log '      whatever created them ran outside this stage.'
    fi
    return 0
  fi

  ACAS_PY_ASSERT_FAILURES=$(( ACAS_PY_ASSERT_FAILURES + 1 ))
  acas_py_warn 'FAIL  this run created a bytecode cache directory inside the frozen checkout'
  while IFS= read -r entry; do
    [[ -n "$entry" ]] || continue
    if [[ "$ACAS_PY_PYCACHE_BEFORE" == *"$entry"* ]]; then
      continue
    fi
    acas_py_log "  new: $(acas_py_sanitise_field "$entry")"
  done <<< "$after"
  acas_py_log '      Bytecode writing is switched off for every interpreter this stage runs and'
  acas_py_log '      the checkout is meant to be mounted read-only, so this should be impossible.'
  acas_py_log '      Remove it: a change to the checkout is a defect in the migration regardless'
  acas_py_log '      of how harmless it appears (Agent Action Plan 0.8.1). Then find out which'
  acas_py_log '      invocation created it, because something is reaching the checkout writably.'
}

# =============================================================================
# STAGE 7 -- THE STATE CAPTURE
#
# One file per table, bounded by the scenario's own affected-table list and by
# nothing else (D-4). The capture tool is asked for the list explicitly rather
# than being pointed at the scenario file, so the bounding is visible in the
# command line this stage prints and in the run log it writes -- which is what
# makes a dry run useful evidence rather than a rehearsal of something invisible.
#
# The normalise and diff stages are NOT run from here. They are stages the caller
# sequences, and folding them in would destroy the explicit staging the plan
# requires (D-6).
# =============================================================================
acas_py_capture_command() {
  printf '%s\0' \
    "$ACAS_PY_PYTHON" \
    "$ACAS_REPO/harness/dump_tables.py" \
    '--scenario' "$ACAS_PY_SCENARIO" \
    '--side' "$ACAS_PY_SIDE" \
    '--tables' "$(acas_py_join_commas "${ACAS_PY_TABLES[@]}")" \
    '--out-dir' "$ACAS_PY_OUT_DIR"
}

acas_py_capture() {
  ACAS_PY_CURRENT_STAGE='taking the state capture'
  acas_py_stage 'Stage 7/8: the state capture'

  ACAS_PY_CAPTURE_DIR="$ACAS_PY_OUT_DIR/$ACAS_PY_SCENARIO/$ACAS_PY_SIDE"

  if (( ! ACAS_PY_DUMP )); then
    acas_py_warn 'the state capture was skipped because --no-dump was given, so there is nothing for the diff stage to compare'
    acas_py_summary_row 'state capture' 'SKIPPED -- --no-dump'
    return 0
  fi

  local tool="$ACAS_REPO/harness/dump_tables.py"
  [[ -f "$tool" ]] || acas_py_die "$EX_PRECONDITION" \
    "the capture tool is not in the checkout: $(acas_py_sanitise_field "$tool")" \
    'It is the stage that reads the affected tables and writes one file per table.' \
    'Without it there is nothing for the diff stage to compare.'

  local -a argv=()
  local word
  while IFS= read -r -d '' word; do
    argv+=("$word")
  done < <(acas_py_capture_command)

  acas_py_log "  $(acas_py_quote_argv "${argv[@]}")"

  local rc=0 started elapsed before after
  before="$(acas_py_log_line_count)"
  started="$SECONDS"
  acas_py_deadline_prefix "$ACAS_TIMEOUT_CAPTURE"
  if (( ACAS_PY_LOG_OPEN )); then
    "${ACAS_DEADLINE_ARGV[@]}" "${argv[@]}" >>"$ACAS_PY_LOG" 2>&1 || rc=$?
  else
    "${ACAS_DEADLINE_ARGV[@]}" "${argv[@]}" || rc=$?
  fi
  elapsed=$(( SECONDS - started ))
  acas_py_assert_not_timed_out "$rc" "$elapsed" "$ACAS_TIMEOUT_CAPTURE" \
    'ACAS_TIMEOUT_CAPTURE' 'the state capture'

  after="$(acas_py_log_line_count)"
  if (( ACAS_PY_LOG_OPEN )) && (( after > before )); then
    if ! sed -n "$(( before + 1 )),${after}p" -- "$ACAS_PY_LOG" \
        | tail -n "$ACAS_PY_CONSOLE_TAIL"; then
      acas_py_warn 'the tail of the capture output could not be replayed to the console; all of it is in the run log'
    fi
  fi

  if (( rc != 0 )); then
    acas_py_die "$EX_ASSERT" \
      "the state capture failed (status $rc)." \
      "  capture tree: $(acas_py_sanitise_field "$ACAS_PY_CAPTURE_DIR")" \
      'Its own reason is in the run log. Without a capture this scenario has produced' \
      'no evidence at all, so this is a failure even when every operation behaved' \
      'exactly as the scenario declared.'
  fi

  # One file per requested table, and the completeness record beside them.
  local table missing=0
  for table in "${ACAS_PY_TABLES[@]}"; do
    if [[ -f "$ACAS_PY_CAPTURE_DIR/$table.json" ]]; then
      acas_py_log "PASS  $table.json"
    else
      missing=$(( missing + 1 ))
      acas_py_warn "FAIL  $table.json is missing from the capture tree"
    fi
  done
  if (( missing > 0 )); then
    ACAS_PY_ASSERT_FAILURES=$(( ACAS_PY_ASSERT_FAILURES + missing ))
  fi
  if [[ -f "$ACAS_PY_CAPTURE_DIR/$ACAS_PY_MANIFEST" ]]; then
    acas_py_log "PASS  $ACAS_PY_MANIFEST -- the completeness record, written last"
  else
    ACAS_PY_ASSERT_FAILURES=$(( ACAS_PY_ASSERT_FAILURES + 1 ))
    acas_py_warn "FAIL  $ACAS_PY_MANIFEST is missing, so the capture cannot be shown to be complete"
  fi

  # Anything else in the tree is REPORTED, because the next stages take their
  # table list from the completeness record and would ignore it -- but a leftover
  # from a scenario with a different table list is worth an operator's attention.
  local entry name
  while IFS= read -r entry; do
    [[ -n "$entry" ]] || continue
    name="${entry##*/}"
    if [[ "$name" == "$ACAS_PY_MANIFEST" ]]; then
      continue
    fi
    if acas_py_in_list "${name%.json}" "${ACAS_PY_TABLES[@]}"; then
      continue
    fi
    acas_py_note "the capture tree also holds $name, which this scenario did not ask for; the next stages take their table list from $ACAS_PY_MANIFEST and will ignore it"
  done < <(find "$ACAS_PY_CAPTURE_DIR" -maxdepth 1 -type f -name '*.json' -print 2>/dev/null)

  acas_py_summary_row 'state capture' "$ACAS_PY_CAPTURE_DIR"
}

# =============================================================================
# THE DRY-RUN PLAN
#
# Prints the exact command line of every command that would run, having already
# resolved every option against the module that must publish it. Nothing is
# contacted and nothing is written (D-7). This is the cheapest possible guard
# against the one failure this file exists to prevent -- an option quietly
# dropped -- so it resolves every option for real rather than describing them.
# =============================================================================
acas_py_print_plan() {
  ACAS_PY_CURRENT_STAGE='printing the plan'
  acas_py_stage 'Dry run: the resolved plan'

  local index operation module
  for (( index = 0; index < ${#ACAS_PY_RUN_OPS[@]}; index++ )); do
    operation="${ACAS_PY_RUN_OPS[index]}"
    module="$(acas_py_operation_field "$operation" 3)"
    acas_py_operation_argv "$operation"
    acas_py_log ""
    acas_py_log "operation $((index + 1))/${#ACAS_PY_RUN_OPS[@]}: $operation  ->  $module"
    acas_py_log "  paragraph : $(acas_py_operation_field "$operation" 4)  [$(acas_py_operation_field "$operation" 5)]"
    acas_py_log "  subsystem : $(acas_py_operation_field "$operation" 2)"
    if [[ -n "${ACAS_PY_EXPECTED[index]}" ]]; then
      acas_py_log "  declared  : status ${ACAS_PY_EXPECTED[index]}"
    else
      acas_py_log '  declared  : nothing -- the status will be recorded and not judged'
    fi
    acas_py_log "  $(acas_py_quote_argv "$ACAS_PY_PYTHON" -m "$module" "${ACAS_PY_ARGV[@]}")"
  done

  acas_py_log ""
  if (( ACAS_PY_DUMP )); then
    local -a argv=()
    local word
    while IFS= read -r -d '' word; do
      argv+=("$word")
    done < <(acas_py_capture_command)
    acas_py_log 'then the state capture of stage 7:'
    acas_py_log "  $(acas_py_quote_argv "${argv[@]}")"
  else
    acas_py_log 'the state capture of stage 7 would be skipped: --no-dump was given'
  fi
  acas_py_log ''
  acas_py_log 'and nothing else. The normalise stage and the diff stage are sequenced by the'
  acas_py_log 'caller and are never run from here (D-6).'
  acas_py_note 'every option above was found in the publishing module own help text before it was placed in a command line; an option a module does not publish is a refusal here and never a fallback'
}

# =============================================================================
# THE CLOSING REPORT
# =============================================================================
acas_py_report() {
  ACAS_PY_CURRENT_STAGE='reporting'
  acas_py_stage 'Summary'

  acas_py_summary_row 'scenario' "$ACAS_PY_SCENARIO"
  acas_py_summary_row 'definition' "$(acas_py_sanitise_field "$ACAS_PY_SCENARIO_FILE")"
  acas_py_summary_row 'operations' "$(acas_py_join_words "${ACAS_PY_RUN_OPS[@]}")"
  acas_py_summary_row 'pinned run date' "$(acas_py_sanitise_field "$ACAS_PY_RUN_DATE_TEXT") (form $ACAS_PY_DATE_FORM, Run-Date $ACAS_PY_RUN_DATE_BINARY)"
  case "$ACAS_PY_IRS_INSTEAD" in
    ' ') acas_py_summary_row 'IRS fan-out' '<space> -- General Ledger only' ;;
    'Y') acas_py_summary_row 'IRS fan-out' '"Y" -- IRS instead of the General Ledger' ;;
    'B') acas_py_summary_row 'IRS fan-out' '"B" -- IRS as well as the General Ledger' ;;
  esac
  if [[ -n "$ACAS_PY_IRS_CLEAR" ]]; then
    acas_py_summary_row 'IRS clear postings' "$ACAS_PY_IRS_CLEAR"
  fi
  if [[ -n "$ACAS_PY_PAYMENT_CONFIRM" ]]; then
    acas_py_summary_row 'payment run-confirm' "$ACAS_PY_PAYMENT_CONFIRM"
  fi
  if [[ -n "$ACAS_PY_GL080_PROCEED" ]]; then
    acas_py_summary_row 'end-of-cycle gate' "$ACAS_PY_GL080_PROCEED (disk-change $ACAS_PY_DISK_CHANGE)"
  fi
  acas_py_summary_row 'affected tables' "$(acas_py_join_words "${ACAS_PY_TABLES[@]}")"
  acas_py_summary_row 'interpreter' "$(acas_py_sanitise_field "$ACAS_PY_PYTHON")"
  if (( ACAS_PY_DRY_RUN )); then
    acas_py_summary_row 'mode' 'dry run -- nothing was contacted and nothing written'
  else
    acas_py_summary_row 'run log' "$ACAS_PY_LOG"
  fi

  local index operation
  if (( ${#ACAS_PY_OBSERVED[@]} > 0 )); then
    acas_py_log 'observed status per operation:'
    for (( index = 0; index < ${#ACAS_PY_OBSERVED[@]}; index++ )); do
      operation="${ACAS_PY_RUN_OPS[index]}"
      if [[ -n "${ACAS_PY_EXPECTED[index]}" ]]; then
        acas_py_log "$(printf '  %-18s observed %-4s declared %s' \
          "$operation" "${ACAS_PY_OBSERVED[index]}" "${ACAS_PY_EXPECTED[index]}")"
      else
        acas_py_log "$(printf '  %-18s observed %-4s declared -' \
          "$operation" "${ACAS_PY_OBSERVED[index]}")"
      fi
    done
  fi

  acas_py_log ''
  local row
  for row in "${ACAS_PY_SUMMARY[@]}"; do
    acas_py_log "$row"
  done

  if (( ${#ACAS_PY_WARN_SUMMARY[@]} > 0 )); then
    acas_py_log ''
    acas_py_log "findings that did not stop the run (${#ACAS_PY_WARN_SUMMARY[@]}):"
    for row in "${ACAS_PY_WARN_SUMMARY[@]}"; do
      acas_py_log "  - $(acas_py_sanitise_field "$row")"
    done
  fi

  acas_py_log ''
  if (( ACAS_PY_ASSERT_FAILURES > 0 )); then
    acas_py_log "VERDICT: $ACAS_PY_ASSERT_FAILURES post-run assertion(s) failed -- a HARNESS FAULT."
    acas_py_log '  Each is listed above with its reason. None of them is an opinion about the'
    acas_py_log '  accounting: they check that this stage pinned what it said it pinned and that'
    acas_py_log '  the run is comparable at all.'
  elif (( ACAS_PY_BEHAVIOURAL > 0 )); then
    acas_py_log "VERDICT: $ACAS_PY_BEHAVIOURAL observed status/statuses contradict the scenario -- a BEHAVIOURAL DIFFERENCE."
    acas_py_log '  The run happened and the capture was taken, so the diff stage can corroborate.'
  elif (( ACAS_PY_DRY_RUN )); then
    acas_py_log 'VERDICT: the plan resolved completely. Nothing was run.'
  else
    # HOW MANY DECLARATIONS THERE WERE TO MEET IS PART OF THE VERDICT. Reporting
    # "every operation behaved as the scenario declares" when the scenario
    # declared nothing would overstate what has been established: a status that
    # was recorded and not judged is evidence for the diff stage to weigh, not a
    # verdict this stage is entitled to reach.
    local declarations=0
    for row in "${ACAS_PY_EXPECTED[@]}"; do
      [[ -z "$row" ]] || declarations=$(( declarations + 1 ))
    done
    if (( declarations == 0 )); then
      acas_py_log 'VERDICT: every operation ran and the capture was taken. The scenario declared'
      acas_py_log '  no status, so none was judged -- every observed status is on the record above'
      acas_py_log '  for the diff stage to be read against.'
    elif (( declarations == ${#ACAS_PY_OBSERVED[@]} )); then
      acas_py_log 'VERDICT: every operation behaved as the scenario declares, and the capture was taken.'
    else
      acas_py_log "VERDICT: the capture was taken. $declarations of ${#ACAS_PY_OBSERVED[@]} operation(s) carried a declared"
      acas_py_log '  status and every one of those was met; the rest were recorded and not judged.'
    fi
    acas_py_log '  The EMPTY DIFF from the diff stage is still the only pass condition for the'
    acas_py_log '  scenario as a whole; this stage having succeeded is a precondition of it.'
  fi
  if (( ! ACAS_PY_DRY_RUN )); then
    acas_py_log ''
    acas_py_log 'Next in the protocol: the normalise stage for this side, then the diff stage.'
  fi
}

# =============================================================================
# MAIN
#
# THE ORDER OF THESE CALLS IS CONSTRAINED. Do not reorder them to group the
# resolvers together or to make the names read better:
#   * the deadlines are resolved FIRST, before anything can spawn a child, because
#     every spawn goes through the prefix they publish;
#   * the interpreter is resolved before the scenario, because the scenario is
#     read with it;
#   * the environment is asserted before the scenario, because the definition path
#     is derived from the checkout when only a name was given, and because every
#     command-line path is canonicalised there while the working directory is
#     still the operator's;
#   * the run log is opened after the scenario is resolved, because its default
#     path carries the scenario name;
#   * the working directory moves before anything is spawned, so no relative
#     output path a child might build can land in a frozen tree;
#   * the lock is taken before anything touches the database, to keep execution
#     strictly sequential (R-3);
#   * every option is resolved against its publishing module BEFORE the database
#     is contacted, so the cheapest failure is also the earliest one;
#   * the capture follows the operations unconditionally, because for a
#     run-aborting rejection the absence of later writes IS the evidence (R-4).
# =============================================================================
acas_py_main() {
  acas_py_parse_args "$@"
  acas_py_resolve_deadlines
  acas_py_resolve_interpreter
  acas_py_assert_environment
  acas_py_resolve_scenario
  acas_py_open_log
  acas_py_resolve_pinned_values
  acas_py_resolve_expected
  acas_py_take_lock
  acas_py_enter_workdir
  acas_py_assert_package

  # Resolve every option the scenario will cause this stage to pass, against the
  # module that must publish it. Done here, before the database is contacted, so
  # that a spelling drift is caught in a second and without a server.
  ACAS_PY_CURRENT_STAGE='resolving the option matrix'
  acas_py_stage 'Stage 4b/8: resolving every option against its module'
  local operation
  for operation in "${ACAS_PY_RUN_OPS[@]}"; do
    acas_py_operation_argv "$operation"
    acas_py_log "PASS  $operation: every option it needs is published by $(acas_py_operation_field "$operation" 3)"
  done

  if (( ACAS_PY_DRY_RUN )); then
    acas_py_print_plan
    acas_py_report
    # Explicitly the success code, and reached only because every option resolved.
    exit "$EX_OK"
  fi

  acas_py_assert_database
  acas_py_seed_fingerprint
  acas_py_run_operations
  acas_py_assert_after_run
  acas_py_capture
  acas_py_report

  # THE STATUS IS DECIDED HERE AND NOWHERE ELSE, and the three categories are
  # never conflated. A harness fault outranks a behavioural difference, because a
  # stage that could not verify its own preconditions has not measured behaviour
  # at all. And none of these is an unconditional success exit: the frozen build
  # scripts end that way -- [comp-all.sh:L45], [common/comp-common.sh:L59] -- which
  # is why their status carries no information. They are not fixed (R-4); their
  # shape is simply not copied.
  if (( ACAS_PY_ASSERT_FAILURES > 0 )); then
    exit "$EX_ASSERT"
  fi
  if (( ACAS_PY_BEHAVIOURAL > 0 )); then
    exit "$EX_BEHAVIOUR"
  fi
  exit "$EX_OK"
}

acas_py_main "$@"
