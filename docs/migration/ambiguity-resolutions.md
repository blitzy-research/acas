# ACAS Posting Cycle — Ambiguity Resolutions

This is the register of **semantic questions that cannot be settled by reading the frozen source**. Each
one is a place where the COBOL is silent, self-contradictory, or dependent on a compiler or C-interface
behaviour that no declaration states — and where the only authority that can settle it is the compiled
program itself.

Its governing rule is R-6, quoted verbatim:

> *"Where a semantic question is ambiguous, the compiled program's observed behavior decides it, and each such resolution must be documented rather than settled silently."*

The standard those resolutions serve is the operational definition of "exact" in AAP §0.1.1, also quoted
verbatim:

> *"the ordering-normalized diff of affected database tables after a Python run versus a COBOL run against an identical seed must be empty."*

**⚠️ Read this before reading anything else. Oracle execution is now available,
but it has not answered every question in this register.** The original authoring
host described by AAP §0.6.9 had neither a COBOL compiler nor a container
runtime. During QA remediation the writable Compose harness was repaired without
editing the frozen tree, the strict oracle build completed, and all eight
mandated scenarios produced observed empty diffs on **2026-08-04**. A ninth
scenario, `end_of_cycle_gl`, was added later to reach `gl080`, and on
**2026-08-07 all nine** produced observed empty diffs. Both dates are kept: an
entry resolved on the earlier date was resolved against an eight-journey sweep,
and restating that as nine would backdate a run that had not yet happened.

**The blocker AAP §0.6.9 records is spent, and the record of it is worth keeping straight.** That risk
entry says *"The authoring host lacks the COBOL compiler and container runtime"* and scopes itself
immediately — *"This is a property of the environment in which this plan was written, not a constraint on
the work"*. It is not a standing property of the project and must not be read as one: the harness
specifies both toolchains through its Compose images, the writable build volume was repaired without
editing the frozen tree, the strict oracle build completed, and all eight mandated scenarios produced
observed empty diffs on **2026-08-04**. Anywhere below that describes a question as unanswered, the reason
is the question's own — an unbuilt seed, an unobservable boundary, a deliberate refusal to adjudicate —
and **never** "no compiler is available".

**How the three kinds of claim are labelled, because a register whose statuses cannot be trusted is
worthless.** Entries distinguish source-only readings, measurements actually made through the compiled
program, and experiments that remain unexecuted. `RESOLVED BY ORACLE` is used only where the cited run
directly answered the stated question; a related green scenario does not promote an unmeasured boundary
question. And **provenance is held to the same standard as status**: a measured figure is cited to durable
repository state — a committed script, a frozen locator, or a section of
[`scenario-diff-evidence.md`](scenario-diff-evidence.md) — or it is labelled a *report of an observed run
rather than a retained artefact*. Console logs written to host temporary paths during a remediation session
are **not** evidence and are not cited anywhere below, because a citation a reader cannot open is
indistinguishable from an assertion.

That is not an apology. An honestly incomplete register is a usable engineering artefact; a register that
quietly fills its gaps with the plausible answer is worse than no register at all, because every
downstream module would then be written against a fiction that no test could detect. AAP §0.4.5 puts it
directly, and it is quoted verbatim because it is the whole reason this file is written alongside the
code rather than after it:

> *"The traceability, anomaly and ambiguity documents are byproducts of writing the program modules and would be fabrications if written separately."*

**What *is* settled here is settled by reading, and the reading is shown.** Four questions are closed or
part-closed by evidence inside the frozen source, and each shows its working so a reviewer can disagree
with the inference rather than take it on trust. Overclaiming uncertainty is as damaging as fabricating
certainty: a question marked open that the source actually answers sends someone to build a container
stack for nothing, and it dilutes the questions that genuinely need one.

The register covers the twelve in-scope posting programs of the General, Sales, Purchase and IRS sub
systems, the seventeen handlers and twenty bridge pairs they reach, the frozen copybooks and schema, the
build and seeding scripts, and the Python modules whose behaviour each answer fixes.

**The release this register describes.** `README.TXT` records the state as v3.3 pre-final, dated
2025-09-21 `[README.TXT:L36-L38]`. Eleven of the twelve in-scope programs carry a version in a `prog-name`
literal — for example `77  prog-name  pic x(15)  value "gl080 (3.3.00)"` at `[general/gl080.cbl:L181]` —
and `irs030` is the exception, noting at `[irs/irs030.cbl:L36]` that its version lives in working storage
instead. Every locator below was read at that release.

---

## 1. Rules provenance

**There is no user rules document for this project.** The Agent Action Plan states it directly in §0.7.1:
*"No separate user rules document was provided for this project."*

Do not go looking for a rules file. There is none. Stated plainly, as the absence requires: this project
has no rules document, and **enterprise-standard best practice therefore applies wherever the Agent
Action Plan is silent**. Nothing has been invented to fill the gap, and the absence is not treated as
permission to lower the bar — in a register whose entire product is honest status reporting, it would be
the easiest possible place to lower it.

The six binding rules of this engagement — **R-1 … R-6** — nevertheless exist. They live in the **Agent
Action Plan itself, §0.7.2**, as a labelled rules block inside the user's requirements, and their exact
wording is retrievable via **`review_prompt`**, *not* via `review_rules`. Quoting AAP §0.7.1:

> *"downstream execution agents that need the exact wording must read it there."*

Both facts are recorded rather than one of them quietly dropped, because AAP §0.7.4 **C-5** requires it.
Its resolution is quoted verbatim, picked up at the point where it names the temptation — dismissing the
requirement-embedded rules block:

> *"because it arrived in the requirements rather than in a rules document would discard six binding constraints on a technicality. Equally, claiming a rules document exists when it does not would send downstream agents to an empty source. Recording both facts is the only resolution that misleads no one."*

---

## 2. The rules that govern this register

Sections 2.1 to 2.6 restate each governing rule and say how this register honours it. Rule text is quoted
verbatim; nothing is paraphrased into a weaker form.

### 2.1 R-6 — Compiled behavior is the tie-breaker ★ primary owner of this register

> *"Where a semantic question is ambiguous, the compiled program's observed behavior decides it, and each such resolution must be documented rather than settled silently."*

R-6 owns this file outright. Two obligations follow, and the second is the one usually dropped:

- **The compiled program decides.** Not the standard, not the maintainer's comments, not what the code
  evidently *meant* to do. Where a remarks block and the executable statements disagree — and in
  `common/maps04.cbl` they disagree twice, in two different ways (§12, `Q-1`) — the statements are closer
  to the truth than the prose, and only the run is the truth.
- **The resolution is documented, not settled silently.** A question answered inside a module body, with
  no register entry, has been settled silently even if the answer is right. Every `Q-` identifier cited
  anywhere in the migration therefore resolves to an entry here, including the ones other agents opened;
  §14 and §15 exist for exactly that.

### 2.2 R-4 — Legacy anomalies reproduced, never fixed

> *"Defects present in the compiled behavior are part of the specification. A defect reproduced is a success; a defect fixed is a failure."*

The consequence for a register of ambiguities is sharper than it first looks: **an ambiguity is never
resolved by choosing the sensible answer.** Where the frozen source contradicts itself, both readings are
recorded and the question is deferred. Picking the coherent one would be indistinguishable, from the
outside, from having measured it — and it would be undetectable as an error, because AAP §0.7.4 **C-3**
explains there is nothing to detect it against:

> *"Any 'improvement' destroys that property and cannot be detected as a regression by any downstream consumer, because there is no correct answer other than what the old system produced."*

Two entries in §12 are held open specifically under this rule when a tidy answer was available:
`Q-5.2`, where the ISO reading and the maintainer's own byte account point in opposite directions, and
`Q-9`, where the maintainer states a convention that explains an omission and then, elsewhere, records
his own doubt about the same field.

### 2.3 R-1 — No COBOL at runtime

> *"The Python implementation must not execute, embed, or shell out to the COBOL programs. COBOL is the specification for the migration, not a runtime dependency of the result. The shipped artifact must run on a host with no COBOL compiler and no COBOL runtime present."*

Every experiment in this register runs **inside `harness/`**, out of process, and nothing in it asks
`acas_posting/` to reach a compiled program. AAP §0.7.4 **C-1** is the licence and the limit, verbatim:

> *"compiled COBOL is confined to `harness/`, invoked only as an out-of-process comparison and seeding utility by the test suites, and never appears on any import path or code path of `acas_posting/`."*

The separation is structural rather than a matter of discipline. AAP §0.3.1 states the property —

> *"there is no import path from `acas_posting` to `harness`."*

— and the checkout enforces it in two ways that were verified here rather than assumed. One earlier
argument is withdrawn first, because leaving it standing would let a reader check the weakest of the
three and conclude the separation is not real:

- ⚠️ **Withdrawn: "`harness/` contains no `__init__.py`, so it is not a package and cannot be imported
  as one."** An earlier revision of this section offered exactly that. The premise is true and the
  inference is **invalid**: PEP 420 makes a directory without `__init__.py` an implicit namespace
  package, so `import harness.diff_states` resolves fine from any process whose `sys.path` includes the
  repository root. The missing marker file is therefore not what keeps the two trees apart, and citing
  it as proof invites a reader to disprove the separation by disproving the argument for it. The
  separation is real; the next two bullets are what establish it. (What the missing file *does* buy is
  smaller and worth stating exactly: the scenario tier does not rely on a namespace import at all — it
  loads `dump_tables`, `normalize` and `diff_states` **by explicit file path** through
  `importlib.util.spec_from_file_location`, registering each under a namespaced `sys.modules` key, so no
  repository-root entry is added to `sys.path` and no harness name can shadow a stdlib one.)
- **Packaging is an explicit allow-list, not an exclusion pattern.** `pyproject.toml` names the eight
  entries that ship — the seven code packages of `acas_posting` plus `acas_posting.data_dictionary` as
  a data directory — and sets `include-package-data = false` pyproject.toml's `[tool.setuptools]` `packages` allow-list. `harness` is
  therefore absent by construction rather than filtered out by a rule that a later edit could widen.
  Belt and braces: `harness` sits in pytest's `[tool.pytest.ini_options] norecursedirs` and `harness/*`
  in the `[tool.coverage.run] omit` list, the latter annotated in the file itself as
  "Belt and braces for R-1".
- **The import direction was measured, and the one place it does run is the legitimate one.** A search
  of `harness/*.py` for `import acas_posting` or `from acas_posting` returns **zero** hits: the three
  Python helpers the tests load are pure — they read table state, canonicalise it and diff it, and none
  of them knows the migrated package exists. The only `import acas_posting` anywhere under `harness/`
  is inside `harness/run_python_scenario.sh`, in the inline Python it feeds to the interpreter — an
  import probe and two `SystemDataBlock` reads. That is the harness *driving* the migrated cycle out of
  process, which is exactly what R-1 licenses; it is not `acas_posting` reaching for COBOL, which is
  what R-1 forbids. The prohibited direction has zero instances.

### 2.4 R-2 — Zero binary floating point

> *"No accounting value may pass through a binary floating-point type at any point — not in computation, not in storage, not in transport."*

Several questions here are precisely about exact-decimal semantics — `Q-2`'s intermediate precision,
`Q-5.1`'s binary truncation, `Q-5.3`'s zoned bytes — so an experiment that captured a value through a
float would destroy the observation it was making. **No experiment below reports a value through a
float.** Observations are read back at the column's full declared scale as `Decimal`, or as `int`, or as
raw bytes. The frozen schema cannot reintroduce one either: it contains **zero** `FLOAT`, `DOUBLE` and
`REAL` columns (verified). And no dataframe library is used to compare states, per AAP §0.5.1:

> *"including for the harness dump comparison, which uses ordered row sequences rather than dataframes"*

### 2.5 R-3 — No new validations, fields or schema changes; no concurrency

> *"The migration may not add validation logic, add fields, or alter the database schema, and must not introduce concurrent execution."*

No experiment below adds a column, an index, a view or a probe table; none runs two scenarios at once.
Where a question needs a value observed, it is observed by seeding a value the frozen loaders already
accept and reading back a column that already exists. This register's own right to exist under R-3 comes
from AAP §0.7.4 **C-2**, verbatim:

> *"R-3 constrains the database, not the repository. Describing a schema in a committed artifact is orthogonal to altering it."*

### 2.6 R-5 — Full traceability

> *"Every program must map to a module, every paragraph to a function, and every field to a data-dictionary entry, and the mapping must be recorded as a document rather than left implicit in the code."*

Every entry names the **consuming module or modules** whose behaviour its answer fixes, so a reader who
watches the oracle settle a question knows exactly what to go and change. Entries do not restate the
program-to-module or paragraph-to-function mappings; those belong to
[`traceability.md`](traceability.md) and are cross-referenced rather than duplicated. Field-level
traceability is likewise mechanised elsewhere: the generated dictionary carries per-field
`ambiguity_refs` lists, and two of this register's identifiers — `Q-3` and `Q-4` — are written into them
by `acas_posting/dictionary/generate.py`, so a field that depends on an open question says so at runtime.

---

## 3. The freeze, and what an experiment may therefore observe

AAP §0.8.1, verbatim:

> *"Any diff touching `common/*.cbl`, `common/*.scb`, `copybooks/*.cob`, `general/*.cbl`, `sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl` or `mysql/ACASDB.sql` is a defect in the migration, regardless of how harmless it appears."*

**No experiment in this register instruments the frozen source.** No added `DISPLAY`, no temporary
paragraph, no extra counter, no recompiled variant of an in-scope program, no debug build of a bridge.
That constraint is what shapes every experiment below, and it is worth stating what it leaves:

| Permitted observable | Why it is available |
| --- | --- |
| Table state, at full declared scale | `harness/dump_tables.py` selects existing columns from existing tables |
| The normalized dump, and the diff of two dumps | `harness/normalize.py` and `harness/diff_states.py` |
| Process exit codes | the frozen loaders and menus already set them |
| The programs' own existing output | already written by the frozen source; never added to |
| Raw stored bytes of a column | a `SELECT` cast, not a schema change |

The same freeze covers the maintainer's own record. Per AAP §0.2.1.4, `README.TXT`, `README`,
`README.SVN`, `README.nightly`, `Changelog` and `ACAS-Manuals/`

> *"are not edited — they document the COBOL system and its version history, and modifying them would misrepresent the maintainer's record."*

They are cross-referenced throughout and never edited.

**⚠️ One frozen-build hazard bears directly on experiment design, and every experiment below inherits
it.** `[common/comp-common.sh:L25]` reads

```text
for i in `ls *MT.scb`; do presql2 $i; echo "Generated SQL source from" $i; done
```

— it **regenerates the frozen `common/*MT.cbl` files** in whatever directory it runs in. Those are exactly
the files AAP §0.8.2 designates authoritative. **The oracle build must therefore never run inside the
mounted checkout.** It does not: `harness/docker-compose.yml` mounts the repository read-only at `/repo`
and gives the build a writable volume of its own, and `harness/build_oracle.sh` copies the tree into that
volume before it runs the maintainer's scripts unmodified. No experiment here may bypass that.

---

## 4. Status vocabulary

Five statuses, used consistently, and one of them is earned rather than chosen.

| Status | Meaning | Permitted evidence |
| --- | --- | --- |
| **`PENDING — AWAITING ORACLE EXECUTION`** | Genuinely open. The experiment is specified and has not been run. | none — the entry states the question and the plan, nothing more |
| **`RESOLVED BY CONSTRUCTION`** | Settled by reading the frozen source, with the reading shown in full so it can be checked and contested. | frozen-source locators, and arithmetic performed on what they declare |
| **`PARTIALLY RESOLVED`** | One path settled by construction, another still open. Both halves are stated separately, and the boundary between them is named. | as above for the settled half; nothing for the open half |
| **`RESOLVED BY ORACLE`** | Settled by watching the compiled program produce the observable, with the value it produced recorded in the entry. | an observed run or a focused compiled probe, with the captured observable recorded verbatim |
| **`MEASURED — DECLINED ON SCOPE`** | The observable WAS watched, and the behaviour is deliberately **not** reproduced because the AAP excludes the surface it belongs to. | the captured observable, plus the AAP section that excludes it |

**`RESOLVED BY ORACLE` is the load-bearing status, and it is earned rather than assigned.** It must not be
written until an agent has actually watched the compiled program produce the observable, and the value it
produced is written into the entry. What makes it checkable is that the value is there: an entry carrying
this status and no captured observable is a defect a reviewer can see without re-running anything. Every
entry now carrying it satisfies that: each states the inputs, the values the compiled program produced, and
the toolchain the probe ran under.

⚠️ **`MEASURED — DECLINED ON SCOPE` exists because one question needed a status neither open nor resolved.**
`Q-EDITED-BLANK-WHEN-ZERO`'s rendering was measured in full, and the migration deliberately does not
implement it: every picture it governs is a print-line item and AAP §0.2.2 excludes report formatting beyond
database effects. Calling that `RESOLVED BY ORACLE` would imply the rendering is reproduced. Calling it
`PENDING` would discard a measurement. It is used **once**, for that entry, and §17 counts it.

⚠️ **A correction to this section, recorded rather than silently absorbed.** This table previously described
`RESOLVED BY ORACLE` as *"RESERVED. Not used anywhere in this register"*, and asserted that the string appeared
**zero** times as an entry's status. That was true when it was written and became false as soon as the first
measurements landed — §11 already carried it on three entries while this section still called it unused. The
claim has been replaced with the rule above, which does not decay, and the **counts** now live only in §17,
where they belong: one place to update, and a reviewer checking §17 against the entries cannot be misled by a
second, staler tally here. §17 therefore records the status distribution as a counted property rather than an
intention, so an edit that promotes an entry without a measurement changes a number a reviewer can check. The
general lesson is recorded in §9: a document that counts itself must count itself in exactly one place.

Two statuses that deliberately do **not** exist: "probably", and "resolved by inference from the
standard". The second is the dangerous one, because it reads like evidence. Where the ISO reading is the
one the Python side currently implements, the entry says so in those words — *implemented provisionally
on this basis, not observed* — and stays `PENDING`.

**A measured negative is a resolution, not a non-answer.** Several questions here are settled by a
measurement showing that the thing asked about *cannot be observed at all* — the compiler refuses the
statement, or the only receiver is a print line the schema never sees. Those are `RESOLVED BY ORACLE` when a
probe produced the refusal, and the refusal is quoted in the entry. The distinction that matters is between
*measured-impossible*, which is an answer, and *not yet attempted*, which is `PENDING`; conflating them is
how an unexamined question comes to look closed.

---

## 5. Identifier convention

**⭐ Identifiers are externally imposed and must not be renumbered.** The sibling `tests/arithmetic/`
suite, the twelve program modules, the twenty-two data-access modules and the generated data dictionary
all cite these identifiers directly — in assertion messages, in module-level question registers, and inside
per-field `ambiguity_refs` lists in `data_dictionary/acas_posting_dictionary.json`. (They were also cited in
`xfail(strict=True)` reason strings until every one of those was converted to an assertion of a measured
value; the citations moved into the assertion messages rather than disappearing.) Renumbering would
break the sibling suite silently, which is the worst available failure mode for a register whose purpose
is that an unmeasured value can never be mistaken for a measured one.

Three identifiers are hard-pinned and appear with exactly these numbers:

| Identifier | Question | Cited by |
| --- | --- | --- |
| **`Q-5.1`** | GnuCOBOL default `binary-size` / `binary-truncate` behaviour | `acas_posting/cobol/usage.py`, `tests/arithmetic/test_comp_binary.py` |
| **`Q-5.2`** | `SIGN LEADING` byte length | `acas_posting/cobol/usage.py`, `tests/arithmetic/test_sign_leading_display.py` |
| **`Q-5.3`** | zoned-decimal overpunch byte values (`ZONED_POSITIVE_BASE` / `ZONED_NEGATIVE_BASE`) | `acas_posting/cobol/usage.py`, `tests/arithmetic/test_sign_leading_display.py` |

The rest of the numbering is:

- **`Q-1` … `Q-9`** — the substantive questions: the five of AAP §0.6.8 (`Q-1` … `Q-5`), the three found
  while writing the migration (`Q-6` … `Q-8`), and one part-resolved bridge asymmetry (`Q-9`). §12.
- **`Q-5.1` … `Q-5.3`** — a reserved cluster for the storage-semantics deferrals, hanging off `Q-5`'s
  number without disturbing it. §12.
- **`Q-10` onwards, and the mnemonic identifiers** — questions opened by other modules and test files as
  the migration was written. They are catalogued in §14, not re-opened.

**Anchors.** Each entry carries an explicit HTML anchor — an `a` element whose `id` is the identifier
lower-cased, with any dot replaced by a hyphen, so `Q-5.2` becomes `q-5-2` — in addition to its prose
heading. That is necessary rather than decorative: citations in the codebase use the **bare** form, and
`tests/arithmetic/test_irs_vat_from_gross.py` at `L1027` points at
`docs/migration/ambiguity-resolutions.md#q-2`, which a heading-derived anchor would not match because the
heading carries the question text after the identifier. Both the bare anchor and the heading anchor resolve.

**⚠️ Identifier forms, and why a naive search under-counts them.** Four forms are in use, and a census that
assumes one of them silently misses the rest: a **plain number** (`Q-7`); a **dotted number** (`Q-5.2`); an
**upper-case mnemonic** (`Q-SORT-TIE-ORDER`); and a **lower-case-suffixed** form (`Q-70f`, `Q-edit-mask-sign`).
The last is the trap — a pattern anchored on a word boundary after the digits, or one that requires an
upper-case letter after the hyphen, matches neither. The coverage claim in §17 was made with a permissive
pattern for exactly that reason, and the `Q-70` family it caught is §14.1a.

**⚠️ Register scope, and why a bare `Q-n` is ambiguous in this codebase.** Three registers coexist, and
they were numbered independently:

1. **This register** — the shared one. It is the one the generated dictionary and both sibling documents
   use: `acas_posting/dictionary/generate.py` writes `"Q-4"` into per-field `ambiguity_refs` — 28 entries,
   alongside one `"Q-6"` — and [`anomaly-log.md`](anomaly-log.md) cross-references both A-11 and A-15 to
   their questions here. It formerly wrote `"Q-3"` as well, on the 91 entries that carry `A-11`, and stopped
   when `Q-3` was measured; the **anomaly** tag `A-11` remains on all 91, because the defect outlived the
   question. Both anomalies are now `REPRODUCED` rather than `PENDING`. An **unqualified** `Q-n` in any
   migration document means this register.
2. **The semantics-layer register** — `acas_posting/cobol/usage.py` claims `Q-5.1` … `Q-5.3`,
   `acas_posting/cobol/move.py` claims `Q-9` … `Q-14`, and `acas_posting/programs/gl071_batch_sort.py`
   claims `Q-15`. The claim is stated in `acas_posting/dal/acasirsub5_irs_final.py` at `L718-L721`.
3. **Module-local registers**, each self-declared. `tests/arithmetic/test_irs_vat_from_net.py` at `L143`
   labels its own entry *"(THIS FILE'S register)"*; `gl051_batch_control_check.py`,
   `sl060_invoice_posting.py` and `pl100_payment_posting.py` each keep a local `Q-1` … `Q-9`; and
   `acas_posting/dal/acasirsub4_irs_posting.py` uses letters — `Q-A`, `Q-B`, `Q-C` — precisely to avoid
   the clash.

The collisions this produces are **resolved in §15, and by two rules rather than one.** §15.1 assigns every
colliding reading a **globally unique canonical identifier** — module-prefixed, in the pattern
`Q-PL055-n` already established — so that any reading can be named unambiguously anywhere, including in a
commit message or a review comment where the file it came from is not visible. §15.2 then tabulates the
collisions themselves. **Nothing is renumbered in code**: the bare number survives as a declared
file-scoped alias, so a citation found inside a module that declares its own register still resolves in that
module, and a citation in a document, a test id, a dictionary `ambiguity_refs` entry or a bare
cross-reference still resolves here. ⚠️ Scoping alone was the *earlier* answer and it was insufficient,
because it disambiguates only for a reader who knows which file the identifier came from.

---

## 6. How to read an entry

Every entry in §12 carries the same five parts, in the same order, without exception:

| Part | What it contains |
| --- | --- |
| **(a) The question** | Stated so that a reader can see *why reading cannot settle it* — which two things disagree, or which behaviour no declaration states. A question that a locator answers does not belong here. |
| **(b) Evidence** | Every relevant `[path:locator]`, all verified by direct reading. Where the evidence is documentary rather than executable — a comment, a byte account — the entry says so, because a comment is not an observation. |
| **(c) Oracle experiment** | The exact commands, and the **precise observable** to capture. Enough that the agent who runs it does not have to re-derive the design, and specific enough that a wrong observable cannot be substituted. |
| **(d) Resolution — or the honest status** | One of the four statuses of §4. Where the status is `PENDING`, this part says what is *expected* only when the source supports an expectation, and labels it as an expectation. |
| **(e) Consuming module(s)** | The Python module or modules whose behaviour the answer fixes, plus the owning test where one exists (R-5). |

An entry may also carry **cross-references** — to an anomaly in [`anomaly-log.md`](anomaly-log.md), to a
sibling question, or to a section of [`traceability.md`](traceability.md). Cross-references never restate
the target.

---

## 7. Locator convention

Every claim about the existing system carries an inline `[<path>:<locator>]` citation, following AAP §0.1,

> *"so that downstream execution agents can verify each statement against the source rather than trusting this document."*

Paths are repository-root relative. `L<n>` is a single line; `L<n>-L<m>` is an inclusive span; a citation
with no line number refers to the file as a whole.

**Every locator in this register was verified by direct reading of the frozen source.** That is the only
evidential claim this document makes about itself. Where the Agent Action Plan and the frozen file
disagreed, the frozen file won and §8 records the correction rather than applying it silently — a citation
that does not resolve defeats the whole convention.

One convention specific to a register of *ambiguities*: where a question arises from two locators
disagreeing, **both are cited and both are labelled**, and neither is presented as the primary reading.
That is what distinguishes an entry here from an entry in the anomaly log, where the behaviour is known
and only its wrongness is at issue.

---

## 8. Corrected locators

⚠️ **Several locators in the Agent Action Plan and in this file's own brief are wrong, and this register
uses the verified values.** Each correction is listed rather than applied silently.

| Claim | Received locator | Verified locator | What is actually at the received locator |
| --- | --- | --- | --- |
| `Q-2` destructive subtract in IRS | `irs/irs030.cbl:L1565` | **`irs/irs030.cbl:L1564`** | `L1565` is a bare `*>` comment line; `L1564` is `subtract vat-amount from post-amount.` |
| `Q-5.2` second `sign is leading` field | `copybooks/irswspost.cob:L19` | **`copybooks/irswspost.cob:L18`** | `L19` is the closing `*>` comment line |
| `Q-3` signed source block | `copybooks/wssl.cob:L46-L52` | **`copybooks/wssl.cob:L45-L53`**, plus **`L43-L44`** for two `binary-short` | `L46-L52` is seven of the nine `binary-long`, omitting `Sales-Limit` and `Sales-Create-Date` |
| `Q-3` unsigned host block | `common/salesMT.cbl:L305-L312` | **`common/salesMT.cbl:L304-L312`**, plus **`L302-L303`** | `L305-L312` is eight of the nine, omitting `HV-SALES-LIMIT` |
| `Q-4` length contradiction | `copybooks/wsbatch.cob` (file only) | **`copybooks/wsbatch.cob:L7-L9`** | no line was given |
| sequential nominal read (A-14) | `general/gl072.cbl:L410-L412` | **`general/gl072.cbl:L408`**, guard `L407`, key move `L405` | `L410-L411` is the *post*-read `if read-ledger not = "R"` guard |
| A-1 defect line | `sales/sl060.cbl:L1172-L1178` (span only) | **`sales/sl060.cbl:L1176`** | the span is right; the line whose period is missing was never named |
| `POST-RRN` comment claim | *"the schema's only column carrying a `COMMENT`"* | **the only column in `GLPOSTING-REC`** carrying one | the schema has 13 further column comments — `[mysql/ACASDB.sql:L562-L567]`, `L575`, `L597`, `L602-L603`, `L610`, `L902-L903`, `L909` — and a table-level comment at `L195` |
| Purchase testing statement | `README.TXT:L44-L47` | **`README.TXT:L45-L48`** | `L44` is blank; the sentence runs `L45-L48` |
| `Q-5`'s `Post-Legend` chain | `sales/sl060.cbl:L1085-L1092` | **`sales/sl060.cbl:L1085-L1094`** | the `STRING` runs `L1091-L1094`; `L1092` is mid-statement |
| bare `comp` census | *"410"* | **214** declared / 144 code-only over the canonical 187 `copybooks/*.cob` files | not reproducible under any scope tried. An earlier revision of this row gave **236** over the wider 197-file scope; that figure was itself wrong — see §9, which now adopts [`traceability.md`](traceability.md)'s canonical census by reference |
| reference-modification census | *"83 live uses"* | **74** `(n:m)` forms on live lines of the twelve in-scope programs | as above; the `(7:4)` ×16 and `(7:2)` ×4 sub-counts **do** reproduce exactly |
| `tests/scenarios/` | *"confirmed present, 8 files"* | **confirmed present — nine committed scenario tests**: the eight that discharge AAP §0.8.5's mandate, plus `test_end_of_cycle_gl.py` added beyond it to reach `gl080` | the original absence was a point-in-time authoring fact, superseded by the completed migration tree; the count moved from eight to nine when the end-of-cycle scenario was added |

Two further points of presentation, corrected rather than repeated:

- The brief describes `general/gl071.cbl`'s sort in the plural, following AAP §0.4.1.2's *"the `SORT`
  verbs"*. There is **exactly one**, at `[general/gl071.cbl:L172-L178]` (verified). `Q-SORT-TIE-ORDER` in
  §13 says so.
- The brief's reading of `[copybooks/wspost.cob:L6-L7]` concludes that a `SIGN LEADING` field *"occupies
  the same byte count as its digits"*. Read as a byte account the same note supports the **opposite**
  inference, and [`anomaly-log.md`](anomaly-log.md) §14.2 already sets out three competing readings.
  `Q-5.2` in §12 records all three and adjudicates none.

---

## 9. Citation hygiene — which paths exist, and how the censuses were counted

Two disciplines apply to a register that will be read by agents who cannot see this checkout.

**Repository paths are cited only when they exist.** Verified present at the time of writing: the
thirteen modules under `acas_posting/programs/`, the twenty-two under `acas_posting/dal/`, the seven under
`acas_posting/cobol/`, `acas_posting/clock.py`, `acas_posting/dates.py`, `acas_posting/workfiles.py`, the
`acas_posting/cli/` and `acas_posting/records/` and `acas_posting/dictionary/` packages; the twenty test
files under `tests/arithmetic/`, the nine under `tests/scenarios/`, plus `tests/conftest.py` and
`tests/determinism/test_two_runs_byte_identical.py`; the committed scripts and two Dockerfiles under
`harness/` with its nine scenario definitions under `harness/scenarios/`; both files under
`data_dictionary/`; all three sibling migration documents
[`anomaly-log.md`](anomaly-log.md), [`traceability.md`](traceability.md), and
[`scenario-diff-evidence.md`](scenario-diff-evidence.md); and the repository
entry point `../../README-python-migration.md`.

The earlier point-in-time absence of the scenario tests and two documentation
deliverables has been superseded. Every relative companion link in this
register now resolves in the checkout.

**Census method, stated because the numbers below differ slightly from the brief's.** Every count in this
register was re-derived rather than carried over. Unless an entry says otherwise:

- A *live* line is one that is not a `*>` comment line. Counts labelled "live" exclude comments; counts
  labelled "declared" include them, because a commented-out declaration is still evidence of intent.
  This definition applies to the reference-modification and per-program counts below. It does **not**
  apply to the storage census, which is no longer published here — see the next bullet.
- ⚠️ **The storage census is not restated here. It is adopted by reference from
  [`traceability.md`](traceability.md), "The canonical storage census".** An earlier revision of this
  section published its own figures over a 197-file scope — bare `comp` **236**, `binary-long` 166
  declared / 165 live, `binary-short` 32 / 31 — and `traceability.md` published different figures over a
  187-file scope, with neither document stating enough for a reader to tell which was right. Two of
  those numbers were wrong, and the reasons are worth recording rather than quietly overwriting:
  - **Bare `comp` was 236 and is 219 declared / 146 live over that same 197-file scope.** The 236 was
    derived as 422 − 182 − 4. The derivation double-counts, because the 422 came from a `\bcomp\b`
    match that *also* hits `comp-3`, `comp-5` and `Comp-Time-Taken`; subtracting only two of the
    hyphenated families from it cannot recover the bare token. The canonical census defines bare `comp`
    as `(?i)\bcomp\b(?!-)` and counts it directly.
  - **The declared/live split above is not the canonical split.** "Live" here drops whole-line comments
    only; the canonical census's "code only" column additionally drops inline `*>` tails, which is why
    its `binary-long` code figure is **128** and not 165. Neither is wrong — they measure different
    things — but two methods and one clause name is exactly how the disagreement arose, so this register
    now cites one method and one set of figures.
  - **The canonical scope is the 187 `copybooks/*.cob` record-layout files**, with the ten non-`.cob`
    files named individually there and the full 197-file delta published beside the main table. The row
    that matters is `binary-double`: **0** over the 187 and **8** over the 197, all in the vendored
    `copybooks/mysql-variables.cpy`. A seventh storage class therefore exists in the directory and in no
    ACAS record layout, which is why the narrower scope is the canonical one.
- The sign-clause census is likewise the canonical one: `sign leading` **4**, `sign is leading` **2**,
  `sign trailing` **0**, `separate` **0** — figures that are identical under both scopes and both line
  definitions, so nothing turned on the disagreement. Six leading-sign fields in total, and no separate
  sign anywhere in the frozen record layouts.
- `ON SIZE ERROR` **0** and `REMAINDER` **0**, counted per file across all twelve in-scope programs and
  zero in every one of them.
- No `-std=` dialect flag appears in any frozen shell script, no `>>SET` directive in any `.cbl`, `.cob`
  or `.scb`, and no `binary-truncate` anywhere in the frozen sources. Verified by search over the whole
  checkout; the only matches for those strings in the tree are Python migration files quoting the absence.
- The two structural censuses, for completeness, quoted from the canonical census rather than recounted:
  `occurs` **107** and `redefines` **60** over the canonical 187 `*.cob` files (99 and 53 code-only),
  becoming **110** and **61** if the wider 197-file scope is used.
- Out-of-scope names are given as **counts only**, never enumerated as though migrated: 22 in-scope tables
  + 11 out of scope = **33** `CREATE TABLE` statements in `[mysql/ACASDB.sql]`; 20 in-scope bridge pairs +
  8 out of scope = **28** pairs. The checkout holds 28 `common/*MT.scb` and 29 `common/*MT.cbl`; the extra
  generated file is `common/dummy-rdbmsMT.cbl`, which has no `.scb` counterpart because it is the stub, not
  a bridge.

⚠️ **Where a re-derived figure disagrees with the received one, both are recorded and neither is presented
as the other's correction on authority.** The Agent Action Plan and
`tests/arithmetic/test_comp3_packed_decimal.py` at `L77-L80` both record bare `comp` as **410**,
`binary-short` as **31**, `occurs` as **107** and `redefines` as **60**. The canonical census in
[`traceability.md`](traceability.md) gives, over its 187 `copybooks/*.cob` files, **214** declared / 144
code-only, **31** / 30, **107** / 99 and **60** / 53. Three of the four therefore **reproduce the
specification exactly** on the all-lines column — `binary-short`, `occurs` and `redefines` — which is
itself informative: it says the specification counted declarations including comments, over the record
layouts, and that the earlier disagreement on those three was an artefact of the wider 197-file scope
this register used to publish. Only bare `comp` does not reconcile: no scope and no line definition tried
reproduces **410**, and the canonical figure is 214 declared. That single unreconciled figure is left
stated rather than explained away, because guessing at the specification's method would be the same
mistake as guessing at compiled behaviour.

---

## 10. The oracle protocol every experiment invokes

Every experiment below is a specialisation of one protocol, so the protocol is
stated once here and the entries state only what they change.

**The primary flow is three commands, and `run_parity.sh` is the driver.** Nothing below should be run
stage by stage unless an entry needs to interpose an observation, because the driver is fail-closed at
every boundary and a hand-run sequence is not:

```text
C="docker compose -f harness/docker-compose.yml run --rm -T gnucobol"

#  Both variables are IN-CONTAINER paths. The checkout is mounted at /repo
#  READ-ONLY (it is frozen specification, R-3) and the writable data volume is
#  mounted at /data, so a bare `harness/...` argument resolves against the
#  container's working directory and is a common way to waste a run.
S=/repo/harness/scenarios/<scenario>.yaml
N=<the scenario's basename without the extension>

$C /repo/harness/build_oracle.sh                         # once per image
$C /repo/harness/build_fixtures.sh "$N"                  # MANDATORY before a first run,
                                                         # and after any fixture change
$C /repo/harness/run_parity.sh \
     --seed-dir "/data/fixtures/$N" "$S"                 # stages 1 through 10
```

⚠️ **`build_fixtures.sh` is not optional and is not a convenience.** A scenario's `seed_dir` resolves
relative to the directory holding the scenario file, which in the shipped Compose topology is inside the
read-only checkout — so the fixture cannot be built where the scenario declares it. `build_fixtures.sh`
materialises it under the data volume instead, and `--seed-dir "/data/fixtures/$N"` is how `seed.sh` is
told where it went, by `[harness/seed.sh acas_on_exit]`. The option changes **where** the declared files are read
from and never **what** is required: the scenario's own `seed_files` list remains the sole authority, every
declared name is still checked, `system.dat` is still mandatory, and the staged fixture is still fresh with
an identity marker recording every file and its SHA-256 digest.

### The ten stages, and the exit contract

⚠️ **Earlier revisions of this register described an eight-stage protocol and referred to "the stage-8
diff". That vocabulary is stale and every occurrence has been replaced.** The recipe has always had eight
*logical* steps — seed, run, dump, reset, run, dump, and the diff — but the driver numbers **ten**, because
it makes both normalisations and the publication check explicit rather than folding them into their
neighbours. A reader meeting "stage 8" in an older document should read it as **today's stage 10**, the
diff. The authority is `[harness/parity_stages.sh ACAS_PARITY_STAGES]`, which
`[harness/run_parity.sh ACAS_PARITY_STAGE_REGISTRY]` reads and
`[harness/run_parity.sh acas_parity_usage]` prints under `--help`.

| Stage | What it does | Side |
| ---: | --- | --- |
| 1 | reset the database, then seed it from the built fixture | — |
| 2 | run the compiled COBOL cycle | COBOL |
| 3 | dump the affected tables | COBOL |
| 4 | normalise that dump | COBOL |
| 5 | reset and **re-seed from the same fixture**, so both sides start identically | — |
| 6 | run the Python cycle | Python |
| 7 | dump the affected tables | Python |
| 8 | normalise that dump | Python |
| 9 | verify both normalised trees are present and published | — |
| 10 | **diff them** — an empty diff is the pass condition | — |

**The exit contract, which is what makes a reported observation trustworthy.** It is quoted from the
driver's own `--help` `[harness/run_parity.sh acas_parity_usage]` rather than paraphrased, because the design
decision inside it is easy to lose: **there is deliberately no "a stage failed" code.** A failed run exits
with the failing stage's *own* status, passed through verbatim, on the ground stated at
`[harness/run_parity.sh EX_PRECONDITION]` and its siblings — flattening every failure into one code would discard the thing an
operator needs, since each cause calls for a different next step.

| Status | Meaning |
| ---: | --- |
| `0` | every stage ran and stage 10 found the two states **identical** — the pass condition, and the only one |
| `1` | stage 10 found a **real difference** |
| `2` | stage 10 **could not compare at all** — not a pass and not a failure, but an absence of evidence |
| `70` / `71` | usage / precondition (environment or scenario assertion) |
| `75` / `76` | the scenario's seed fixtures are not staged / the seed reported success and left no rows |
| `74` | the compiled oracle is not built |
| `69` | a behavioural difference detected by the Python runner's own assertions |
| `83` | a dump was asked for an out-of-scope table (`EX_SCOPE`) |

An entry that reports a value read from a run that exited anything other than `0` must say so. Two flags
also invalidate a run as evidence and are named here so nobody uses them and then cites the result:
`--keep-going`, which the driver's own help calls *"NOT THE PROTOCOL"* and says produces a verdict that
*"is not evidence (rule R-6)"*, and `--dry-run`, which runs nothing.

**⚠️ Stage numbers here are global. "Check" numbers printed by a runner are not.**
`run_cobol_scenario.sh` and `run_python_scenario.sh` each emit their own `Check n/8` preflight headings,
which count that one script's internal checks and have no relation to the ten stages above. Reading a
runner's `Check 8/8` as the parity diff is the specific confusion this note exists to prevent.

**The manual expansion, for the entries that interpose an observation.** Stages 1 and 5 are the **same
command**, `reset_db.sh --seed-dir "/data/fixtures/$N" "$S"`, which drops and re-applies the frozen schema
and then forwards `--seed-dir` to `seed.sh` `[harness/reset_db.sh acas_compose_seed_argv]`; the driver's help states why
they are identical on purpose `[harness/run_parity.sh acas_parity_stage_banner]` — *"the Python side's starting state the
COBOL side's starting state rather than the COBOL side's ENDING state"*. Every block below therefore opens
with that one command rather than with `seed.sh`, which an earlier revision used and which would seed
whatever the previous run had left in the schema. The rest expands as:

```text
$C /repo/harness/reset_db.sh   --seed-dir "/data/fixtures/$N" "$S"   # stage 1
$C /repo/harness/run_cobol_scenario.sh                        "$S"   # stage 2
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol  …      # stage 3
$C /repo/harness/normalize.py   --scenario "$N" --side cobol         # stage 4
$C /repo/harness/reset_db.sh   --seed-dir "/data/fixtures/$N" "$S"   # stage 5
$C /repo/harness/run_python_scenario.sh                       "$S"   # stage 6
$C /repo/harness/dump_tables.py --scenario "$N" --side python …      # stage 7
$C /repo/harness/normalize.py   --scenario "$N" --side python        # stage 8
$C /repo/harness/diff_states.py --scenario "$N" --scenario-file "$S" # stages 9-10
```

The blocks in §12 and §13 are written in that expanded form and abbreviate the stages they do not change.
`run_parity.sh --dry-run` prints the ten commands for a given scenario without running any of them, which
is the way to check an expansion against the driver rather than against this table.

Four properties are load-bearing:

- **The empty diff is the pass condition, and the only one.** `[harness/docker-compose.yml "AN EMPTY DIFF FROM THAT LAST COMMAND IS THE PASS CONDITION"]`:
  *"AN EMPTY DIFF FROM THAT LAST COMMAND IS THE PASS CONDITION, and the only one: a stage that exits
  non-zero has produced no evidence, so re-seed rather than carry a partial capture forward."* An entry
  that reports a value read from a run whose earlier stage failed has reported noise.
- **`-T` is required on every scripted stage**, because a tty is allocated by default and a piped stage
  would appear to hang. An experiment that hangs gets abandoned, and an abandoned experiment is how a
  question stays open for the wrong reason.
- **One scenario at a time** (R-3). Nothing here runs two.
- **The build never runs in the checkout.** See §3's hazard note. `build_oracle.sh` copies into its own
  volume first.

Three per-question levers appear repeatedly below and are described once:

| Lever | How it is set | Why an entry needs it |
| --- | --- | --- |
| The seed | the scenario's own `seed_files`, staged by `harness/seed.sh` from the frozen `common/*LD.cbl` loaders | the only way to place a chosen value in front of the compiled program without touching frozen code |
| The affected-table list | `--all-in-scope` for the full 22-table comparison bound (what the authoritative driver uses), `--tables` for an explicit list, or `--scenario-file` alone for the scenario's own `affected_tables`. `--tables` and `--all-in-scope` are the mutually exclusive pair — `harness/dump_tables.py` refuses them together as *"alternative ways of choosing the same list, so use exactly one"*. `--scenario-file` is **not** in that pair: it selects only when it is the sole selector, and otherwise rides along as **provenance**, supplying the `scenario_file_sha256` that stage 10 requires present and equal on both sides. ⚠️ This row previously read "`--scenario-file` … or `--tables` … **never both**", attributing the refusal to the wrong pair. Measured: `--scenario-file` with `--tables` is **accepted** (1 table, scenario file as provenance), `--scenario-file` with `--all-in-scope` is **accepted** (22 tables), and only `--tables` with `--all-in-scope` is refused. The old reading was not merely imprecise — treating the two as exclusive is the defect that emptied `scenario_file_sha256` and left the authoritative driver unable to complete a single scenario | bounds the observation to the tables the scenario is about; see `Q-7` |
| The IRS fan-out state | `IRS-Instead` in the seeded system row — `[copybooks/wssystem.cob:L179-L181]`, with `88 IRS-Used value "Y"` and `88 IRS-Both-Used value "B"` | three states, and the state decides which tables a run touches at all |

Where an entry needs a value at a boundary the nine committed scenarios do not already seed, it says so
explicitly and describes the seed it needs. It does **not** propose editing a frozen loader to accept one.

### The provenance a reported observation carries with it

An observation below is a statement about **the two runtimes that produced it**, not about their version
ranges, and the two are worth naming so that a later reader can tell whether a re-run is comparable.

- **The compiled side is GnuCOBOL 3.2 final**, the version the maintainer's own compile script targets
  `[common/comp-common.sh:L9]` and the readme records `[README.TXT:L53]`, against **MariaDB 10.11.7**, the
  server the frozen schema dump was produced by `[mysql/ACASDB.sql:L1]`. Both are pinned by the harness
  images rather than taken from the host.
- **The Python side is a C-backed CPython 3.12.** `pyproject.toml` pins `requires-python = "==3.12.*"`, and
  what the pin protects is that `decimal` is backed by the C `_decimal` (`libmpdec`) implementation rather
  than the pure-Python fallback, since every monetary operation passes through it.
  [`../../README-python-migration.md`](../../README-python-migration.md) §6 reconciles the three version
  numbers in play: the Agent Action Plan's reference interpreter is **3.12.3** with `libmpdec` 2.5.1, and
  the interpreter this checkout is exercised on is **3.12.13**.
- ⚠️ **A green diff attests to the patch level it ran on, and not to `3.12.*` as a whole.** No entry below
  claims parity across every 3.12 patch release, and none should be read as claiming it: the pin is a
  *constraint* on what may run, not a body of evidence about everything it admits. A pure-Python `decimal`
  build is not accepted as parity evidence at all, and 3.13 is outside the evidence entirely.

### 10.1 The former build blocker, resolved without touching the freeze

`copybooks/ACAS-SQLstate-error-list.cob` remains absent from the checkout and
is still referenced by 44 frozen files. Direct build analysis established that
the include contributes comments only. `harness/build_oracle.sh` therefore
materialises a semantically inert comment-only file under
`$ACAS_BUILD/copybooks` and adds that writable directory to the compiler's
copy path.

The strict build then completed with zero fatal diagnostics, all **29/29**
expected `*MT` bridges, and all **28/28** loaders.

**Evidence, and what survives of it.** The durable evidence is the shim and the build script that
materialises it, both committed and both readable without running anything:
`harness/copybook-shims/ACAS-SQLstate-error-list.cob` is the comment-only file, and `harness/build_oracle.sh`
copies it to `$ACAS_BUILD/copybooks` `[harness/build_oracle.sh acas_install_sqlstate_comment_shim]`, adding
that writable directory to the compiler's copy path — the checkout itself is never written to. The script also
**enforces a compiled module per source file** rather than merely counting successes, so "29/29" and "28/28"
are the checkout's own inventories — 29 `common/*MT.cbl` and 28 `common/*LD.cbl` — verified one for one, not a
tally reported by a run. (§9 records why the bridge count is 29 against 28 `.scb`: the extra generated file is
`common/dummy-rdbmsMT.cbl`, the stub, which has no `.scb` counterpart.) To regenerate the whole build rather
than trust a transcript, `harness/build_oracle.sh` prints the bridge and loader tallies as it goes and writes
its two compile transcripts under `$ACAS_LOG_DIR` — `$ACAS_OUT/build`, which it names on its own last lines:

```bash
# CLONE_INDEX and the credential variables, per README-python-migration.md section 8.1.
# They have no committed defaults: Compose refuses to render if any is unset.
export CLONE_INDEX=001
docker compose -f harness/docker-compose.yml run --rm -T gnucobol \
    /repo/harness/build_oracle.sh < /dev/null
```

⚠️ **The build console log an earlier revision cited here was written to a session-scoped `/tmp` path and is
not retained; the citation has been removed** rather than left pointing at a file no reader can open. The
"zero fatal diagnostics" claim is therefore a **report of an observed build rather than a retained artefact** —
reproducible, because the build is fail-closed on every expectation it asserts, but not a filed one. The
command above and the transcripts it leaves in the named volume are the citation: they are the artifacts that
persist.

This does not invent an SQLSTATE mapping and does not edit frozen
`copybooks/`. It removes the obsolete global blocker while leaving each
unexecuted question pending on its own merits. Cross-reference
**A-NEW-13** in [`anomaly-log.md`](anomaly-log.md).

### 10.2 Invocation details that cost a run when wrong

**One operational rule worth stating once, because getting it wrong wastes a whole run.**
`harness/dump_tables.py` treats `--scenario-file`, `--tables` and `--all-in-scope` as **mutually exclusive**
and raises rather than guessing when more than one is given. Entries below therefore use exactly one:
`--scenario-file "$S"` where the observation is the scenario's own affected-table list, and
`--tables TABLE[,TABLE...]` — spelled exactly as `[mysql/ACASDB.sql]` spells them, hyphens included — where
the entry needs a table the scenario does not claim. `--scenario` and `--side` are orthogonal to the
choice: they compose the output path and nothing else, so they appear in both forms.

---

## 11. The register — index

Fourteen primary entries. The status column is the one to read first.

| id | Question | Status | Consuming module(s) |
| --- | --- | --- | --- |
| [`Q-1`](#q-1) | Does `maps04` leave its output field untouched on a rejected date, and does every in-scope caller pre-zero it? — **untouched; yes, every forward caller does; and a non-zero field silently selects the REVERSE conversion** | **`RESOLVED BY ORACLE`** | `acas_posting/dates.py`, `acas_posting/clock.py` |
| [`Q-2`](#q-2) | What intermediate precision the default compiler applies at the five `ROUNDED` sites, and to the compound VAT expression | **`RESOLVED BY ORACLE`** — extended precision throughout, quantized once at the store | `acas_posting/cobol/arithmetic.py` |
| [`Q-3`](#q-3) | What a negative binary value *becomes* once the bridge narrows it into an unsigned host variable and an unsigned column | **`RESOLVED BY ORACLE`** — the absolute value, then bounded by the receiving digit count | `acas_posting/dal/acas012_sales.py`, `acas_posting/dal/acas007_gl_batch.py` |
| [`Q-4`](#q-4) | Which of the batch record's two declared lengths governs the record actually read — **neither: both copies measure 96 and the 98 note is false** | **`RESOLVED BY ORACLE`** | `acas_posting/records/gl_batch.py` |
| [`Q-5`](#q-5) | What observable effect the unexplained `move RRN to postings` has, in each of the four Sales and Purchase posting programs — **a silent signed 16-bit wrap reaching two database columns** | **`RESOLVED BY ORACLE`** | `sl060_invoice_posting.py`, `sl100_cash_posting.py`, `pl060_order_posting.py`, `pl100_payment_posting.py` |
| [`Q-5.1`](#q-5-1) | The default `binary-size` and `binary-truncate` policy governing every `COMP` and `BINARY-*` field — **two rules, not one: pictured reduces on digits, pictureless wraps at capacity** | **`RESOLVED BY ORACLE`** | `acas_posting/cobol/usage.py` |
| [`Q-5.2`](#q-5-2) | The byte length of a `SIGN LEADING` display item — three readings | **`RESOLVED BY ORACLE`** — Reading B: an included leading sign costs no byte | `acas_posting/cobol/usage.py` |
| [`Q-5.3`](#q-5-3) | The concrete zoned-decimal overpunch byte values, for both signs and for zero, and the packed sign nibbles | **`RESOLVED BY ORACLE`** — zoned `0x30` / `0x70`, packed `0xC` / `0xD` / `0xF` | `acas_posting/cobol/usage.py` |
| [`Q-6`](#q-6) | Whether `sl830`, which the Sales menu dispatches before `sl055` and the Python route does not, is observably a no-op | **`RESOLVED BY ORACLE`** | `harness/run_cobol_scenario.sh`, `harness/run_python_scenario.sh` |
| [`Q-7`](#q-7) | What the menu shells' unconditional `overrewrite` writes on exit — **and whether the Python CLI has a counterpart for it: it does, at all seven routes** | **`RESOLVED BY ORACLE`** | `acas_posting/cli/args.py`, `harness/dump_tables.py`, `harness/diff_states.py` |
| [`Q-8`](#q-8) | Whether `Post-Date (7:2)` holds a **year** or a **century** — a year on the Sales and Purchase paths, a century on `irs030`'s own | **`RESOLVED BY CONSTRUCTION`** | `acas_posting/dal/acasirsub4_irs_posting.py`, `acas_posting/dal/acas006_gl_posting.py`, `harness/normalize.py` |
| [`Q-9`](#q-9) | Whether `HV-POST-RRN` being declared and fetched but never loaded is the maintainer's stated convention or the field he doubted | **`PARTIALLY RESOLVED BY ORACLE`** | `acas_posting/dal/acas006_gl_posting.py`, `acas_posting/dal/cursor_state.py` |
| [`Q-10`](#q-10) | Whether the AAP's autocommit-OFF requirement governs the seeding stage or every connection the harness makes | **`RESOLVED BY ORACLE`** | `harness/seed.sh`, `harness/Dockerfile.mariadb`, `harness/reset_db.sh`, `harness/run_cobol_scenario.sh` |
| [`Q-SYS4-SPARE-SENTINEL`](#q-sys4-spare-sentinel) | Where the two cycles' disagreement over `SYSTOT-REC`'s four spare columns comes from, and which value is the specification — **the loader stamps a sentinel the menu then erases, so the difference was a defect in the SEED and in neither cycle** | **`RESOLVED BY ORACLE`** | `harness/scenarios/*.yaml`, `harness/make_fixtures.py`, `harness/diff_states.py` |

`RESOLVED BY ORACLE` appears only for questions a compiled run or a focused compiled probe **directly
answered**, with the captured observable written into the entry — either by a full parity journey, for the
route and exit-path questions, or by a probe compiled from the frozen declarations, for the storage and
arithmetic ones. A green scenario does not close a question by association, and neither does a probe that
did not reach the boundary the question is about. A question answered by reading the frozen source carries
the weaker `RESOLVED BY CONSTRUCTION` instead — `Q-8` is the one entry that does, and it says why in its own
text.

**§13** carries the deferrals handed up from the tiers that could not answer them: **eight** entries of its
own, mostly under mnemonic identifiers — six from the arithmetic tier, one from the scenario tier and one from
the two parity runners — plus a
companion answer key that a run supplies, plus **three** questions cited by scope because the semantics layer
already owns them. The seventh is [`Q-EMPTY-BATCH-AT-END`](#q-empty-batch-at-end), which
`tests/scenarios/test_empty_batch.py` coined and cited before this file carried it; §13's warning records that
gap rather than closing it silently. **§14** catalogues every remaining `Q-` identifier the repository cites —
**85** distinct identifiers are cited outside this file across the migration trees, and **every one of them
resolves to an entry or a catalogue row in this file**, so no citation anywhere dangles (§17 states that as a
counted property, with the counting algorithm given so every figure is reproducible; the register's own total
is **114**, the difference being the 3 identifiers documented as unassigned and the 26 canonical names §15.1
mints). **§15** does two things: **§15.1** assigns a globally unique canonical identifier to every reading that
previously had only a colliding bare number, and **§15.2** tabulates the collisions between the three
coexisting registers.
**§16** records three scope declinations that are decisions rather than ambiguities, and **§17** is a counted
self-audit of this file.

---

## 12. The register — entries

<a id="q-1"></a>
### `Q-1` — the date module's reject contract

**Status: `RESOLVED BY ORACLE`** — measured 2026-08-07 by **calling the compiled `maps04.so`**. **`A-Bin` is
left UNTOUCHED on every reject clause, and every in-scope forward caller pre-zeroes — so the documented
contract holds, and holds because of the callers rather than because of the module.** The measurement also
answered a question nobody had asked, and it is the more consequential half: a non-zero `A-Bin` on entry
selects the **reverse conversion** and destroys the caller's date text without ever validating it. The
resolution is in (d).

**(a) The question.** When `maps04` rejects a date, what does its caller's binary output field hold
afterwards — zero, or whatever it held before? The program's executable statements and the program's own
remarks give different answers, so reading cannot settle it; and the answer differs per caller if any
caller fails to pre-zero.

**(b) Evidence.** The rejection paths **fall through without touching `A-Bin`**. The six-part reject test
runs `[common/maps04.cbl:L140-L145]` —

```text
if       Z not = 2 or
         A-Days not numeric or
         A-Month not numeric or
         A-CC   not numeric or
         A-Days < 01 or > 31 or
         A-Month < 01 or > 12
         go to Main-Exit.
```

— with the transfer at **`[common/maps04.cbl:L146]`**, and the calendar test does the same:
`[common/maps04.cbl:L153]` is `if FUNCTION Test-Date-YYYYMMDD (Test-Date9) not = zero` and
**`[common/maps04.cbl:L154]`** is again `go to Main-Exit.`. `A-Bin` is written **only** on the success
path, at `[common/maps04.cbl:L167]`.

Against that, the program's own remarks block states a contract it does not implement, at
**`[common/maps04.cbl:L163]`**:

```text
*>  Date errors returned as A-Bin equal zero *
```

The one caller that has been read does pre-zero, which is why the documented contract holds *for it*:
`[copybooks/Proc-ACAS-Mapser-RDB.cob:L78]` is `move zero to u-bin.`, immediately before the call at `L79`
and the harvest at `L80` (`move u-bin to run-date.`). **Not every in-scope caller has been proven to do
so**, and the callers reach `maps04` through nine near-identical per-program wrapper sections rather than
through that copybook.

⭐ **The remarks block is unreliable in a second, independent way, which is what removes any temptation to
trust it.** `[common/maps04.cbl:L160-L162]` documents the return as a date:

```text
*>  Requires Date input in A-Date as         *
*>  dd.mm.yy or dd.mm.ccyy & returns Date as *
*>      ccYYMMDD in  A-Bin                   *
```

but `[common/maps04.cbl:L167]` stores `FUNCTION integer-of-Date (Test-Date9)` — a **day number**, not a
`ccYYMMDD` value. Two independent misstatements in one comment block is not a typo; it means the block
carries no evidential weight at all, on either point. Only execution settles the reject behaviour.

Cross-references: **A-16** in [`anomaly-log.md`](anomaly-log.md) carries the reject behaviour as a
reproduced defect, and **A-NEW-2** carries the `ccYYMMDD` misstatement.

**(c) Oracle experiment.** Under the §10 protocol, with the seeded system row's date text driven to a value
that fails each clause in turn:

```text
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_cobol_scenario.sh                        "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables SYSTEM-REC,GLPOSTING-REC,IRSPOSTING-REC
```

Drive **each** reject clause separately, so a single composite bad date cannot mask which clause fired:
a non-two separator count (`Z not = 2`); non-numeric days, month and century in turn; days `00` and `32`;
month `00` and `13`; and then a date that passes all six and fails the calendar test at `L153` —
`31/02/2025` is the clean case, since `FUNCTION Test-Date-YYYYMMDD` rejects it while every clause at
`L140-L145` passes.

**The observable is the stored `RUN-DAT` column of `SYSTEM-REC`**, read at full width, plus the
date-derived columns of any posting row the run writes. For each clause, record whether the field is zero
or retains the value it held in the seed. To separate "pre-zeroed by the caller" from "written by
`maps04`", run each clause twice against seeds whose prior `RUN-DAT` differs — once from zero and once from
a distinctive non-zero day number. A caller that pre-zeroes yields zero from both; a caller that does not
yields the distinctive value from the second.

⚠️ **If a run ends with `RUN-DAT = 0`, that is information — do not mask it.** Zero is a legitimate
observation here and quite possibly the correct one; the failure mode to avoid is treating it as a
harness fault and re-seeding until it goes away.

**(d) Resolution — MEASURED 2026-08-07, GnuCOBOL 3.2.0.**

The experiment in (c) proposed reaching this through seeded scenario runs and the `RUN-DAT` column. It was
settled more directly by **calling the compiled `maps04.so`** with `copybooks/wsmaps03.cob` — the block every
in-scope caller passes, per `[common/maps04.cbl:L122]` — once per reject clause, so that no composite bad date
could mask which clause fired. That is the same oracle the scenario route would have consulted, reached
without having to drive a whole cycle to observe one field.

**Part 1 — with `u-bin` pre-zeroed, every clause of the six-part test plus the calendar test:**

| clause driven | input | `u-bin` out | `u-date` out |
| --- | --- | --- | --- |
| `Z not = 2`, one separator | `01/012025` | **0** | unchanged |
| `Z not = 2`, three separators | `01/01/20/5` | **0** | unchanged |
| `A-Days not numeric` | `XX/01/2025` | **0** | unchanged |
| `A-Month not numeric` | `01/XX/2025` | **0** | unchanged |
| `A-CC not numeric` | `01/01/XX25` | **0** | unchanged |
| `A-Days < 01` | `00/01/2025` | **0** | unchanged |
| `A-Days > 31` | `32/01/2025` | **0** | unchanged |
| `A-Month < 01` | `01/00/2025` | **0** | unchanged |
| `A-Month > 12` | `01/13/2025` | **0** | unchanged |
| calendar test at `[:L153]` | `31/02/2025` | **0** | unchanged |
| *valid control* | `01/01/2025` | **154864** | unchanged |

So both statements in (a) are true at once, which is why they looked like a contradiction: **the module leaves
the field untouched, and the caller's pre-zero is why the observation reads zero.** The remarks block at
`[:L163]` describes the system's behaviour correctly while describing the module's incorrectly.

⭐ **The valid control also confirms the epoch, as a by-product.** `154864` for 2025-01-01 is the day count
from **1600-12-31**, the epoch the Agent Action Plan cites from `[common/maps04.cbl:L39-L41]`. That was a read
claim and is now a measured one.

**Part 2 — the question this entry did not think to ask, and the answer that matters more.**
`[common/maps04.cbl:L128-L129]` is `if A-Bin > zero go to WS-Unpack`, so **the module is bidirectional** and a
non-zero `A-Bin` on entry selects binary-to-text instead of text-to-binary:

| input text | `u-bin` in | `u-date` out | `u-bin` out |
| --- | --- | --- | --- |
| `01/01/2025` — perfectly valid | `987654` | **`08/02/4305`** | `987654` |
| `31/02/2025` — invalid | `987654` | **`08/02/4305`** | `987654` |

The second row is the decisive one: **the bad date was never validated at all.** The six-part test is not
merely bypassed on the way to a stale answer — it is never reached. So
`[copybooks/Proc-ACAS-Mapser-RDB.cob:L78]`'s `move zero to u-bin` is **not defensive tidiness; it is what
chooses the direction**, and a caller omitting it with any non-zero residue in that field silently gets the
opposite conversion and its input text overwritten.

**Part 3 — which callers pre-zero, settled by census of the frozen source.** (a) said the source "does not
answer at all" which of them do. It does, once the two directions are told apart:

| caller | pre-zero | direction |
| --- | --- | --- |
| `[general/gl051.cbl:L1202]` → `L1203` | **yes** | forward, `zz050-test-date` |
| `[sales/sl060.cbl:L1221]` → `L1222` | **yes** | forward, `zz050` |
| `[sales/sl100.cbl:L737]` → `L738` | **yes** | forward, `zz050` |
| `[purchase/pl060.cbl:L1075]` → `L1076` | **yes** | forward, `zz050` |
| `[purchase/pl100.cbl:L718]` → `L719` | **yes** | forward, `zz050` |
| `[copybooks/Proc-ACAS-Mapser-RDB.cob:L78]` → `L79` | **yes** | forward, the menu shell |
| every `zz060-Convert-Date` site | **no** | **reverse — a non-zero `u-bin` is the intended input** |
| `[general/gl070.cbl:L547]` | **no** | reverse; `gl070` has **no forward section at all** |

`gl070` is worth its own line: it has only `zz060-Convert-Date` and a `zz070-Convert-Date` that reformats text
without calling the module, so there is no forward path in it to pre-zero. Every site that does not pre-zero
is deliberately using the reverse direction. **The answer is therefore yes — every in-scope forward caller
pre-zeroes — and the risk the question was really about is latent rather than live.**

**Alignment with the shipped code — all 13 vectors replayed against `acas_posting/dates.py`: 13 agreements, 0
mismatches**, covering the ten reject clauses, the valid control, and both reverse-direction rows.
**No production change was required.** `dates.py` already reproduced the untouched-output behaviour and the
`L128` dispatch. No check is added that a caller pre-zeroed (R-3, R-4). Locked by
`tests/arithmetic/test_irs_date_component_derivation.py`'s two `q1_` tests, the second of which asserts the two
directions must not converge — so a lost `L128` dispatch fails rather than passes quietly.

**(e) Consuming modules.** `acas_posting/dates.py`, which reimplements `maps04` including its reject
behaviour, and `acas_posting/clock.py`, which pins the two date observables at the CLI boundary and
therefore decides what a caller's field holds before the call.

<a id="q-2"></a>
### `Q-2` — default arithmetic precision

**Status: `RESOLVED BY ORACLE` (2026-08-07).**

**(a) The question.** With no dialect selected and no arithmetic directive anywhere, the **compiler's
default** intermediate precision governs every multi-term expression. Reading cannot settle it because
nothing in the repository states it: the answer is a property of the compiler build, not of the source.
It matters at exactly five sites, and at two of those the expression is deep enough that a difference of
one intermediate digit can change a stored penny.

**(b) Evidence.** The absence is the evidence, and it was counted rather than assumed (§9): **no `-std=`
dialect selection in any frozen shell script, no `>>SET ARITHMETIC` directive in any `.cbl`, `.cob` or
`.scb`, and no `binary-truncate` flag anywhere.** The compiler is GnuCOBOL **3.2 final**, per the
maintainer's own compile script at `[common/comp-common.sh:L9]` —

```text
# 07/12/22 vbc - Extra text for echo msgs and use of -Wno-goto-section added
#                to remove the silly default warning in latest gnucobol v3.2.
```

— corroborated at `[README.TXT:L53]`, which names *"(3.2 final)"*.

The five `ROUNDED` sites in the whole in-scope cycle are `[general/gl051.cbl:L791]`,
`[general/gl051.cbl:L796]`, `[general/gl080.cbl:L328]`, `[irs/irs030.cbl:L1551]` and
`[irs/irs030.cbl:L1562-L1563]`. Every other store truncates toward zero.

⭐ **Two of the five are genuinely compound, and they are the ones that matter.** `[general/gl051.cbl:L796]`
carries four nested levels in one statement:

```text
compute  vat-amount rounded = post-amount - (post-amount / ((ws-vat-rate + 100) / 100)).
```

and `[irs/irs030.cbl:L1562-L1563]` is the same shape spread over two lines, over `WS-Vat-Current`:

```text
compute  vat-amount rounded =
         post-amount - (post-amount / ( (WS-Vat-Current + 100) / 100)).
```

**This is the one place a precision difference could change a stored penny.** The other three are a single
multiply-then-divide `[general/gl051.cbl:L791]`, its IRS twin `[irs/irs030.cbl:L1551]`, and a plain divide
`[general/gl080.cbl:L328]`.

⭐ **The destructive sequel, and an asymmetry that is easy to misattribute.** The gross computation is
immediately followed by `[irs/irs030.cbl:L1564]`:

```text
subtract vat-amount from post-amount.
```

⚠️ **`L1564`, not `L1565` — `L1565` is a bare `*>` comment line.** The paired General site behaves the same
way: `[general/gl051.cbl:L797]` is the identical `subtract vat-amount from post-amount.` following the
gross compute, while the `net.` paragraph at `[general/gl051.cbl:L788-L791]` has **no** subtract at all,
and neither does `Net section.` at `[irs/irs030.cbl:L1544-L1551]`. **The asymmetry is a property of
net-versus-gross, not of the IRS module** — a distinction worth keeping straight, because attributing it to
IRS would send someone looking for an IRS-specific defect that is not there. Because the subtract consumes
the rounded result, an intermediate-precision difference does not stay in `VAT-AMOUNT`: it propagates into
`POST-AMOUNT` and from there into every balance the posting touches.

**(c) Oracle experiment.** Under the §10 protocol, seeding VAT rates and amounts that place the true
quotient **exactly on a half-way boundary and one unit either side of it**, so that a rounding direction
and an intermediate truncation are distinguishable rather than confounded:

```text
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_cobol_scenario.sh                        "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables GLPOSTING-REC,IRSPOSTING-REC,GLBATCH-REC
```

For the compound sites, choose `ws-vat-rate` values whose `(rate + 100) / 100` is **not** exactly
representable at the intermediate's scale — a rate with a fractional part, such as `17.50`, `20.00` and
`5.00` in turn — and amounts chosen so that the exact quotient's third decimal place is `5`. Run each
triple (boundary, boundary minus one minor unit, boundary plus one minor unit) as its own scenario, since
§10 permits one at a time.

**The observable is the stored `VAT-AMOUNT` and `POST-AMOUNT` at full declared scale**, read from
`GLPOSTING-REC` for the General sites and `IRSPOSTING-REC` for the IRS sites, plus `ACTUAL-VAT` and
`ACTUAL-GROSS` on `GLBATCH-REC` where the batch gate has consumed them. Never through a float (R-2):
read as `Decimal` at the column's declared scale. For `[general/gl080.cbl:L328]` the observable is the
period subscript's effect, which is `Q-QUARTER-SUBSCRIPT`'s subject rather than this one's.

**(d) Resolution. MEASURED — extended precision throughout, quantized ONCE at the store.** The focused
experiment was run as a compiled probe rather than as a scenario, for the reason the previous revision of this
entry gave: none of the mandated journeys places the compound expression on the precision boundary, so a green
scenario would never have reached it. A probe declared `pic s9(7)v99` receivers matching
[`copybooks/irswspost.cob:L18`] and executed the frozen statements verbatim under the frozen build flags — no
`-std=`, no `>>SET ARITHMETIC`, no `binary-truncate` — so what it measured is the compiler's own default and
not a configured one.

⭐ **`Q-2` asks TWO things, and they were settled by different means. Keep them separate**, because the two
halves fail differently and because a single verdict over both is what let this entry be wrong twice.

**The SHAPE is settled by the language, not by a measurement.** A `ROUNDED` phrase belongs to the **store**,
so a statement evaluates its expression and then quantizes **once**, into the receiver. Quantizing each
sub-expression would be a different language. `acas_posting/cobol/arithmetic.py` implements that shape and
`tests/arithmetic/test_compute_rounded_half_up.py` locks it.

**The NUMBER OF INTERMEDIATE DIGITS cannot be read from anything in this repository** — it is a property of the
compiler **build**, and there is no `-std=` selection in any frozen script, no `>>SET ARITHMETIC` directive in
any `.cbl`, `.cob` or `.scb`, and no `binary-truncate` flag anywhere (§9 counts all three absences). So it was
**measured**, by the probe below, rather than inferred. `acas_posting/cobol/arithmetic.py` documents
`INTERMEDIATE_PRECISION = 60` as deliberately wider than every in-scope receiver's declared digit count — the
widest is 14 — so that the settled shape governs and the limit cannot itself reach a stored value; the
measurement is what promotes that constant from a working assumption to a confirmed reading.

⚠️ **This entry has been wrong in both directions, and both corrections are recorded rather than quietly
applied.** One revision claimed both halves had been *"measured against GnuCOBOL 3.2.0"* before any probe had
run; a later one withdrew the claim from this register, from that module's comment and from two test headers,
on the ground that neither half was measured. Neither statement is the truth: the shape is settled by the
language and the digits are settled by the probe below. The module comment, this register and **every test
header that describes this question** now state that one status — enumerated as "two test headers" in an
earlier revision, which under-counted them and was itself a symptom of finding MJ-13, so the agreement is now
held by `tests/arithmetic/test_deployment_contract_boundaries.py`'s
`test_no_consumer_describes_a_resolved_question_as_open` rather than by a list that has to be maintained. This
register keeps the rejected readings as evidence so a reader can check the discrimination instead of taking it
on authority.

**The captured observables.** The discriminating case is the compound gross form of
`[irs/irs030.cbl:L1562-L1564]` and [`general/gl051.cbl:L796`],
`post-amount - (post-amount / ((rate + 100) / 100))`, transcribed verbatim into the probe with the frozen
field declarations, on a VAT rate of 17.50 —

| input amount | `vat-amount` | `post-amount` |
| --- | --- | --- |
| `1000.00` | `+0000148.94` | `+0000851.06` |
| `-1000.00` | `-0000148.94` | `-0000851.06` |
| **`117.55`** | **`+0000017.51`** | `+0000100.04` |
| `0.01` | `+0000000.00` | `+0000000.01` |

`117.55` is the row that decides it. Forcing the **reduced-precision** reading by hand — quantize each
sub-expression at the receiver's own two places — gives `(17.50 + 100) / 100 → 1.18`, then
`117.55 / 1.18 → 99.62`, then `117.55 − 99.62 → **17.93**`. The compiler produced **17.51**, which is
neither that nor the third candidate the entry names. So the intermediate is NOT reduced to the receiver's
scale between terms.

**The rejected reading, measured for contrast**, so that the discrimination is evidenced rather than argued:
quantizing per sub-expression — `multiply post by rate giving vat rounded` then `divide vat by 100 giving vat
rounded` — produced `+0017500.00` then `+0000175.00`. On the *net* form those two routes agree, which is
precisely why the compound gross form is the discriminating case. Two further contrasts from the same probe:
omitting the inner `/ 100` gives `+0000991.49`, so the divisor's construction is load-bearing; and the net
form [`irs/irs030.cbl:L1551`] / [`general/gl051.cbl:L791`] `post * rate / 100` measured `175.00` for
`1000.00`, `0.58` for `3.33` (from `0.58275`) and `0.01` for `0.03` (from `0.00525`).

`gl051`'s two `ROUNDED` sites were measured from the same series, with `ws-vat-rate pic 99v99 comp` and
`pic s9(8)v99` amounts: site 1 `[general/gl051.cbl:L791]` gives `117.55 → 20.57` and `12.30 → 2.15`;
site 2 `[general/gl051.cbl:L796]` gives `117.55 → 17.51` and `1000.00 → 148.94` — site 2 agreeing with
`irs030` exactly, which is itself a check on the reading.

Measured with GnuCOBOL 3.2.0, `cobc -x -free`, no `-std=` dialect selection, no
`>>SET ARITHMETIC` directive and no `binary-truncate` flag -- the same absence §9
counts across every frozen compile line.

The semantics layer already implemented this reading provisionally, so the resolution CONFIRMS it rather
than replacing it: `[acas_posting/cobol/arithmetic.py INTERMEDIATE_PRECISION]` is 60 digits and
`[acas_posting/cobol/arithmetic.py INTERMEDIATE_CONTEXT]` is the context every operation in that module
enters. `tests/arithmetic/test_compute_rounded_half_up.py` and
`tests/arithmetic/test_irs_vat_from_gross.py` now assert the measured pennies, including the `117.55 →
17.51` row, as facts. Neither carries a strict expected failure any longer.

**Where the figures now live.** `tests/arithmetic/test_irs_vat_from_gross.py` carries them in
`ORACLE_CAPTURED_PENNIES`, keyed by statement-and-operands so a captured penny can never be reused for
different inputs, and the test that consumes them drives the **shipped** sections — so the assertion sets
production behaviour against an independently sourced figure rather than against itself.
`tests/arithmetic/test_compute_rounded_half_up.py` keeps the **rejected** 17.08 as an evidenced tripwire
rather than an open question — `assert measured != Decimal("17.08")`, asserted rather than marked — so the
arithmetic layer adopting the reading this measurement ruled out fails there.

Note the boundary of this question precisely, because several sibling tests depend on where it stops: `Q-2`
reaches only expressions whose intermediate needs **more digits than the receiver declares**.
`tests/arithmetic/test_irs_vat_from_net.py` records the semantics layer's working assumption and states
plainly that no assertion in that file would change if the answer moved, because its figures never approach
the limit. The compound gross expression is the exception, and it is the one the measurement above was taken
on: `tests/arithmetic/test_irs_vat_from_gross.py` now ASSERTS the measured pennies, including the
`117.55 → 17.51` row that discriminates between the two readings, where it previously marked the
proposition `xfail(strict=True)` against this question.

**(e) Consuming module.** `acas_posting/cobol/arithmetic.py`, which owns every store's truncation
direction and the extended-precision intermediate. Test-owned at the parity tier by
`tests/arithmetic/test_irs_vat_from_gross.py`, with `tests/arithmetic/test_compute_rounded_half_up.py`
and `tests/arithmetic/test_compute_truncate_unrounded.py` recording the same identifier where their own
figures touch it.

<a id="q-3"></a>
### `Q-3` — a negative binary value through an unsigned host variable into an unsigned column

**Status: `RESOLVED BY ORACLE` (2026-08-07).**

**(a) The question.** *That* the sign is lost is settled: it is lost **at the bridge, not at the database**,
which is anomaly **A-11**. What the resulting **stored value** *is* is not settled, because it depends on
the conversion the bridge's C interface performs when a signed binary item is moved into an unsigned host
variable and then rendered into SQL text. AAP §0.6.8 states the boundary of the question in the words this
register adopts: it *"must be measured rather than assumed."* Three candidate outcomes are all consistent
with the declarations — the two's-complement bit pattern reinterpreted as unsigned, the absolute value, or
zero — and no declaration distinguishes them.

**(b) Evidence.** The narrowing is visible only by comparing **three layers**, and it must be *detected*
that way rather than looked up: the copybook declaration, the generated host variable, and the column.

The Sales instance, which AAP §0.6.2 documents:

| Layer | Declaration | Locator | Signedness |
| --- | --- | --- | --- |
| Copybook | nine `binary-long` — `Sales-Limit`, `Sales-Activety`, `Sales-Last-Inv`, `Sales-Last-Pay`, `Sales-Average`, `Sales-Pay-Activety`, `Sales-Pay-Average`, `Sales-Pay-Worst`, `Sales-Create-Date` | `[copybooks/wssl.cob:L45-L53]` | **signed** |
| Bridge host variable | nine `PIC 9(10) COMP` | `[common/salesMT.cbl:L304-L312]` | **unsigned** |
| MySQL column | nine `int(8) unsigned NOT NULL` | `[mysql/ACASDB.sql:L965-L973]` | **unsigned** |

⭐ **There are eleven narrowings in the Sales bridge alone, not nine.** `Sales-Late-Min` and
`Sales-Late-Max` are declared `binary-short` at `[copybooks/wssl.cob:L43-L44]`, become `PIC 9(05) COMP` at
`[common/salesMT.cbl:L302-L303]`, and land in `smallint(4) unsigned` at `[mysql/ACASDB.sql:L963-L964]`. The
same loss, a narrower field.

⭐ **A second, entirely undocumented instance exists, and it is in the General sub system.** The batch
record's four date fields are declared `binary-long` at `[copybooks/wsbatch.cob:L36-L39]`:

```text
03  Dates.
    05  Entered         binary-long.
    05  Proofed         binary-long.
    05  Posted          binary-long.
    05  Stored          binary-long.
```

They become `PIC 9(10) COMP` at `[common/glbatchMT.cbl:L287-L290]` and `int(8) unsigned NOT NULL` at
`[mysql/ACASDB.sql:L86-L89]`. AAP §0.6.2 records only the Sales instance.

⚠️ **The drift must be detected by comparison across the three layers, not by hard-coding the single
documented example.** That is not a stylistic preference: two of the eleven Sales fields and all four
batch fields are absent from the Agent Action Plan's own citation, so a data-access layer built from the
documented list would silently pass a signed value through in six places. `acas_posting/dictionary/generate.py`
performs the three-layer comparison and writes `"Q-3"` into the affected fields' `ambiguity_refs`;
`acas_posting/dal/acas012_sales.py` asserts at import time that every field it treats as narrowed carries
that reference, so the list and the dictionary cannot drift apart.

**By contrast, the monetary fields are signed at all three layers and pass through cleanly**, which is what
makes the drift specific rather than systemic: `Sales-Current` and `Sales-Last` are `pic s9(8)v99 comp-3`
at `[copybooks/wssl.cob:L54-L55]`, become `PIC S9(08)V9(02) COMP` at `[common/salesMT.cbl:L313-L314]`, and
land in `decimal(10,2)` at `[mysql/ACASDB.sql:L974-L975]`.

Cross-reference: **A-11** in [`anomaly-log.md`](anomaly-log.md). Its status there is
`REPRODUCED — VALUE MEASURED`: the anomaly stands, and the value it produces is now known.

**(c) Oracle experiment.** Under the §10 protocol, seeding a customer whose statistics computation drives a
**negative** value into one of the narrowed fields, and a batch whose date fields do the same:

```text
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_cobol_scenario.sh                        "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables SALEDGER-REC,GLBATCH-REC
```

`Sales-Average` is the field to drive, because the moving-average idiom reaches it by an integer divide
whose numerator can be made negative through a credit note, and anomaly **A-8**'s double truncation means
the value that arrives is an integer already. Seed a customer with a credit note larger than the
accumulated turnover so the average computes negative; then run the Sales invoice route.

**The observable is the stored `SALES-AVERAGE` column, read as an integer, compared against three
candidates computed from the same seed:** the two's-complement reinterpretation of the 32-bit pattern, the
absolute value, and zero. Record which one it equals — and if it equals none of them, record the value
verbatim, because a fourth outcome is the most informative result the experiment can produce. Repeat for
`Sales-Late-Min` at `smallint` width, since a 16-bit narrowing may not behave as the 32-bit one does, and
for `GLBATCH-REC`'s `ENTERED` to confirm the second instance behaves identically to the first.

Read as `int`, never through a float (R-2). No column is added and no cast is introduced into the schema:
the raw byte reading, where wanted, is a `SELECT`-side cast in `harness/dump_tables.py`'s own query, not a
DDL change (R-3).

**(d) Resolution. MEASURED: the ABSOLUTE VALUE, then bounded by the receiving field's declared digit
count.** The sign is discarded and the magnitude survives, so what is destroyed is the debit-versus-credit
*sense* of the figure and nothing else. The two's-complement reinterpretation and the zero candidate are both
REFUTED.

**Why the measurement had to reach the column, and not stop at the `MOVE`.** The question as §0.6.8 poses it
names *the conversion the bridge's C interface performs*. A probe that only exercised the COBOL `MOVE` would
therefore answer a narrower question than the one asked and leave `cobmysqlapi` and the SQL text
unmeasured — which is exactly the gap that made `Q-OTM5-NARROW`'s finding (§14.4) corroboration rather than
arbitration. So the probe went the whole way: it called the **compiled `acas012` handler**, which called the
**compiled `salesMT` bridge**, which issued real SQL through `cobmysqlapi` against real MariaDB, and then the
column was read back both through the same compiled path and directly with the client.

**The captured observables, end to end.** One `SALEDGER-REC` row written with negative values in the drifting
fields; the handler reported `FS-Reply=00` on open and on write:

| field | in the record | declared column | read back |
| --- | --- | --- | --- |
| `Sales-Average` `binary-long` signed | `-12345` | `int(8) unsigned` | **`12345`** |
| `Sales-Limit` `binary-long` signed | `-12345` | `int(8) unsigned` | **`12345`** |
| `Sales-Late-Min` `binary-short` signed | `-7` | `smallint(4) unsigned` | **`7`** |
| `Sales-Activety` (positive control) | `99` | `int(8) unsigned` | **`99`** |

The positive control is there so that a probe which silently wrote nothing could not be mistaken for a
measurement. The column types were confirmed from `information_schema` in the same run rather than taken from
the schema file.

**The same conversion measured at the `MOVE` itself**, with the host variable's own picture as the receiver,
which is where the digit-count bound becomes visible:

| source | receiver | stored |
| --- | --- | --- |
| `-1` | `pic 9(10) comp` | `0000000001` |
| `+1000` | `pic 9(10) comp` | `0000001000` |
| `-1000` | `pic 9(10) comp` | `0000001000` |
| `-2147483648` | `pic 9(10) comp` | `2147483648` |
| `-123456` | `pic 9(4) comp` | `3456` |
| `+123456` | `pic 9(4) comp` | `3456` |

`-2147483648` is the row that refutes the bit-pattern reading: reinterpreted as unsigned it would be
`2147483648` too, but `-1` would then be `4294967295` and it is `1`.

**What it is NOT.** Not a two's-complement reinterpretation of the source bytes, not zero, not a clamp to the
column's minimum, and not a MySQL error or a rejected row. Each of those was a live candidate before the run
and each is now excluded by the figures above.

**The ordering of the two steps, measured separately**, because absolute-value-then-reduce and
reduce-then-absolute-value differ on an overflowing negative. Where the magnitude also exceeds the receiving
host variable's digit count, the absolute value is taken **first** and the high-order digits are truncated
**afterwards** — a negative `binary-long` narrowed into a `PIC 9(4) COMP` receiver kept the low-order digits
*of the magnitude*. Into `binary-char unsigned` (0..255): `±99999 → 159`, `±300 → 44`, and **`-1 → 1`, not
`255`**; a reduce-first reading would give 255. The consequence is that a negative and a positive value of
equal magnitude collide on the same stored byte, so the two are indistinguishable once written.

For contrast, and recorded because it is easy to assume the two behave alike, a **signed** `binary-char`
receiver behaves completely differently: `+99999 → -97` and `-99999 → +97`. `pic 9(3) comp` gives
`±99999 → 999`.

**This confirms the implementation rather than changing it.** `acas_posting/cobol/usage.py`'s `_wrap_into_bits`
already took the absolute value in that order. It was previously labelled *provisional* precisely because
nobody had watched the compiled path; it is now the measured behaviour.

**What did NOT change, and this is the important half.** Anomaly `A-11` remains published on all **91**
affected field entries across eleven tables. Measuring the sign loss did not repair it, and rule R-4 forbids
repairing it: every one of those statistics still arrives at the database with its sense destroyed. What the
measurement settled is the **value**, not the defect. The generated dictionary therefore now carries `A-11`
with **no** `Q-3` ambiguity reference — 91 `A-11` references and 0 `Q-3` references, counted from the
artifact — and `acas_posting/dal/acas012_sales.py` asserts exactly that pairing at import time, together with
the measurement note, so neither half can drift: republishing `Q-3` would report a settled question as open,
dropping the note would report a measured value as unmeasured, and dropping `A-11` would hide a live defect.

**Where the figures now live.** `tests/arithmetic/test_comp_binary.py` holds the measured outcome in
`BRIDGE_SIGN_MEASURED`, with `BRIDGE_SIGN_MEASUREMENT` as the note every affected dictionary entry must
carry, deliberately separate from the tests that consume them: those tests drive `cobol.usage`, which is
production code, so carrying their own expected figures would let them pass by agreeing with the
implementation they check. Their `xfail` markers have been removed. The three sibling files that previously
asserted the descriptors *carry* the `Q-3` reference now assert its **absence** alongside `A-11`'s presence.

**(e) Consuming modules.** `acas_posting/dal/acas012_sales.py` for the Sales instance and
`acas_posting/dal/acas007_gl_batch.py` for the batch instance. Test-owned by
`tests/arithmetic/test_comp_binary.py`.

<a id="q-4"></a>
### `Q-4` — the batch record's length contradiction

**Status: `RESOLVED BY ORACLE`** — measured 2026-08-07, GnuCOBOL 3.2.0. **The answer is *neither*: both
record copies measure 96, `FUNCTION LENGTH` agrees with the field sum, and the 98 in the maintainer's note
is false under this compiler.** The resolution is in (d).

**(a) The question.** `copybooks/wsbatch.cob` records **two** lengths for the same record, and the
maintainer's own notes say he cannot reconcile them. Whether the declared length or the field sum governs
the record actually read decides **trailing-field alignment**, and AAP §0.6.8 is explicit that *"only
execution shows which."* **Do not pick one.**

**(b) Evidence.** `[copybooks/wsbatch.cob:L7-L9]`, verbatim:

```text
*> 96 bytes 26/03/09
*> 98 bytes 20/12/11 (no, dont understand as I count 96)
*>   but function length (Batch-record) says 98?
```

Two lengths, one contradiction, and two of the maintainer's own question marks. Nothing else in the file
explains the delta — unlike its `wspost.cob` siblings below, this note supplies no cause. The field most
exposed to a two-byte shift is the last fixed-width text field before the posting group,
`Description pic x(24)` at `[copybooks/wsbatch.cob:L45]`, which sits immediately after the four packed
`Amounts` members at `[copybooks/wsbatch.cob:L40-L44]`.

Cross-reference: **A-15** in [`anomaly-log.md`](anomaly-log.md), whose status there is
`REPRODUCED — VALUE MEASURED, comment stale, Q-4` — promoted out of `PENDING — Q-4` on this entry's
measurement, and keeping the `Q-4` cross-reference because the measurement lives here.
`acas_posting/dictionary/generate.py` writes `"Q-4"` into the `ambiguity_refs` of all four `Amounts`
members and of `Batch-Status`, and `tests/arithmetic/test_control_total_comparison.py` and
`tests/arithmetic/test_comp3_packed_decimal.py` assert that it is there.

⚠️ **Distinguish this from its two siblings in `copybooks/wspost.cob`, which are *not* open.** Presenting
all three alike would overclaim uncertainty, and overclaiming is as damaging as fabricating certainty.
[`anomaly-log.md`](anomaly-log.md) §14.2 grades them, and this register adopts that grading rather than
re-adjudicating it:

- **Sibling 1 — explained, but not resolved, and its open half is `Q-5.2`, not this entry.**
  `[copybooks/wspost.cob:L6-L7]` reads *"98 bytes 26/03/09"* then *"96 bytes 20/12/11 (leading sign
  removed)"*. Unlike A-15's pair this one supplies a **cause** for the delta. What it does not supply is a
  settled byte width for a leading-sign field, and that residue is `Q-5.2`'s subject — it is not a second
  record-length question.
- **Sibling 2 — arithmetically resolved, and presented as resolved.** Summing the declared pictures
  **excluding** `WS-Post-rrn` gives **exactly 98**, matching the `L6` note; and the maintainer's own running
  byte comments agree exactly through `Post-Amount` at 46 and then run **exactly two bytes low** from
  `Post-Legend` onward, ending at 96 and matching the `L7` note, because they imply a 30-byte `Post-Legend`
  where `[copybooks/wspost.cob:L24]` declares `pic x(32)`. **The divergence localises precisely at
  `Post-Legend`**, which is a complete account. Verified by direct reading of
  `[copybooks/wspost.cob:L13-L28]`.

So there is one open record-length question in the frozen copybooks, not three, and it is this one.

**(c) Oracle experiment.** Under the §10 protocol, seeding batch rows whose **trailing fields carry
positionally distinguishable content**, so that a two-byte shift is visible as a shift rather than as
noise:

```text
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_cobol_scenario.sh                        "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables GLBATCH-REC
```

Seed `Description` with a 24-character string whose every position is identifiable — a repeating index such
as `0123456789012345678901` padded to width, or a marker at each end — and seed the four `Amounts` members
with values whose packed representation contains no byte that could be mistaken for a text character.
Then read the row back.

**The observable is the stored `DESCRIPTION` column, character by character, and the four
`decimal(14,2) unsigned` amount columns.** A record governed by the 98-byte reading and unpacked under the
96-byte reading (or the reverse) shows `DESCRIPTION` displaced by two positions, with two bytes of packed
amount data appearing at its head or two characters of description missing from its tail. Record the exact
displacement rather than a yes/no. Run it twice, once through the RDB path and once through the COBOL-file
path, because the contradiction is between a `function length` and a field sum and the two paths may not
agree.

**(d) Resolution — MEASURED 2026-08-07, GnuCOBOL 3.2.0.**

The experiment in (c) was designed around a *displacement*, on the assumption that one of the two lengths
would prove to govern and the other would show up as a two-byte shift. It does not go that way. Asking the
compiler for its own layout — the cheapest available oracle for a width question, since the compiler answers
out of the allocation it actually made — settles it before any row is written:

| observable | measured |
| --- | --- |
| `FUNCTION LENGTH(WS-Batch-Record)`, the `wsbatch.cob` copy | **96** |
| `FUNCTION LENGTH(Batch-Record)`, the `fdbatch.cob` copy | **96** |
| sum of the ten members' own `FUNCTION LENGTH` values | **96** |
| implied padding | **none** — the two figures are equal |
| first byte of `Description` | **53**, exactly where the field sum puts it |
| `Description` read back at `(53:24)` | intact and undisplaced |
| bytes 92–96 | `54321` = `Batch-Start`, so the record ends where the field sum says |

Complete byte attribution, every one of the 96 accounted for: `WS-Batch-Key` 1–6, `Items` 7–8,
`Batch-Status` 9, `Cleared-Status` 10, `Bcycle` 11–12, `Dates` 13–28 (four `binary-long` at 4 bytes each,
stored **little-endian** — `111111` appears as `07 B2 01 00`), `Amounts` 29–52 (four `comp-3` at 6 bytes
each, eleven digits plus a sign nibble, unsigned sign nibble `0xF`), `Description` 53–76, `posting-data`
77–91, `Batch-Start` 92–96.

**So there was never a choice between the two lengths to make.** `FUNCTION LENGTH` *is* the field sum here,
both are 96, and the maintainer's L9 — *"but function length (Batch-record) says 98?"* — does not hold under
the compiler this migration's oracle uses. Whatever produced a 98 in December 2011 is not GnuCOBOL 3.2.
`acas_posting/records/gl_batch.py` builds its layout from the declared pictures, which is the field sum, and
that decision is now **measured correct** rather than a visible assumption. Its site comment should be read
as recording a confirmed layout, not an open choice.

⚠️ **The false answer this probe produced first, recorded because the register's own experiment design had
warned against exactly it.** Part (c) says to *"seed the four `Amounts` members with values whose packed
representation contains no byte that could be mistaken for a text character."* The first run ignored that,
filling `Actual-Vat` with `444444444.44` — whose packed bytes are `0x44`, which **is** ASCII `D`, the same
character the run was using to fill `Description`. The scan for the first `D` therefore found the *amount*,
at byte 47, which read as a six-byte displacement and would have been a fabricated finding had it been
believed. The confirming run used `555555555.55` and an `ABCDEFGHIJKLMNOPQRSTUVWX` description, whose
leading `A` (`0x41`) no packed nibble pair in the fill can produce, and located byte 53 unambiguously. The
lesson generalises: when a probe's detector and its fill share an alphabet, the detector is measuring the
probe.

⭐ **An incidental confirmation of the collision class.** Copying `fdbatch.cob` and `wsbatch.cob` into one
program makes **more than twenty** field names ambiguous — `Items`, `Batch-Status`, `Cleared-Status`,
`Bcycle`, all four `Dates` members, all four `Amounts` members, `Description`, all six `posting-data`
members and `Batch-Start` — each requiring `in WS-Batch-Record` qualification before the program will
compile. That is a fresh instance of the collision anomaly the frozen programs work around with qualified
references, appearing in a pair of copybooks the register had not previously connected to it.

**(e) Consuming module.** `acas_posting/records/gl_batch.py`. Read at the parity tier by
`tests/arithmetic/test_control_total_comparison.py` and `tests/arithmetic/test_comp3_packed_decimal.py`,
which assert the reference rather than the layout — and which therefore needed no change when the
measurement landed, because the layout they were built on is the layout it confirmed. The dictionary
continues to emit `Q-4` on the four `Amounts` members and `Batch-Status`; that is correct and deliberate,
the identifier now pointing at a resolved entry rather than an open one.

<a id="q-5"></a>
### `Q-5` — the unexplained move

**Status: `RESOLVED BY ORACLE`** — measured 2026-08-07, GnuCOBOL 3.2.0. **The move is not inert: past
`RRN = 32767` it wraps as a signed 16-bit integer, silently, and the negative result reaches two database
columns — one of them as its absolute value.** The resolution is in (d).

**(a) The question.** Four programs perform a move that the maintainer annotated with his own question
mark. AAP §0.6.8 sets the terms: *"Because the maintainer himself does not know why it is there
`[sales/sl060.cbl:L1173]`, its observable effect on the posting record must be measured and then reproduced
regardless of whether it makes sense."* Reading cannot settle it because the statement's *effect* depends on
what `RRN` holds at that point and what `postings` is subsequently read for — and nothing in the four
programs reads `postings` again.

**(b) Evidence.** All four sites, verified, each preceded by the same guard:

| Program | Guard | The move |
| --- | --- | --- |
| `sl060` | `[sales/sl060.cbl:L1172]` | `[sales/sl060.cbl:L1173]` |
| `sl100` | `[sales/sl100.cbl:L690]` | `[sales/sl100.cbl:L691]` |
| `pl060` | `[purchase/pl060.cbl:L1027]` | `[purchase/pl060.cbl:L1028]` |
| `pl100` | `[purchase/pl100.cbl:L671]` | `[purchase/pl100.cbl:L672]` |

The pair reads identically in all four, and the annotation is the maintainer's own:

```text
if       IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060
         move     RRN  to  postings.     *> Why ?
```

⭐ **Corroborating context, and it is more than colour.** The guard line carries a **wrong-program
comment**: `*> THIS IS IN PURCHASE PL060` sits inside `sl060` (Sales), inside `sl100` (Sales) and inside
`pl100` (Purchase payments), and is accurate in exactly **one** of the four — `pl060`. That is
**A-NEW-10**, and it establishes the block as a copy-paste artefact propagated across four files. It is also
**plausibly the mechanism by which A-1's terminating period was lost**, because the missing period is three
lines below the same block: `[sales/sl060.cbl:L1176]` omits the period on `perform SPL-Posting-Close`
where `[purchase/pl060.cbl:L1031]`, `[sales/sl100.cbl:L694]` and `[purchase/pl100.cbl:L675]` all have it.
That connection is offered as context for why the block deserves measurement, not as a finding.

Cross-reference: **A-17** in [`anomaly-log.md`](anomaly-log.md), promoted to `REPRODUCED` by the same
measurement, and still carrying the mnemonic identifier `Q-A17-POSTINGS-EFFECT` that
`acas_posting/programs/pl060_order_posting.py` opened for this question's *value* half. See §15 for how the
two identifiers relate; §14.4 carries the value half's own entry.

**(c) Oracle experiment.** Under the §10 protocol, run **each of the four programs** with the IRS fan-out
pinned to **each of its three states**, because the guard tests `IRS-Both-Used OR G-L` and the state decides
whether the move executes at all:

```text
# For each of the three IRS-Instead states, and each of the four programs:
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"      # $S pins IRS-Instead in the system row
$C /repo/harness/run_cobol_scenario.sh                        "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables GLPOSTING-REC,PSIRSPOST-REC,GLBATCH-REC,SYSTEM-REC
$C /repo/harness/normalize.py  --scenario "$N" --side cobol
```

The three states are `IRS-Instead = "Y"` (`IRS-Used`), `"B"` (`IRS-Both-Used`) and any third value, which
is neither — `[copybooks/wssystem.cob:L179-L181]`. Then run the Python side with the equivalent move
present and again with it absent, and diff:

```text
$C /repo/harness/run_python_scenario.sh                       "$S"
$C /repo/harness/diff_states.py --scenario "$N" --scenario-file "$S"
```

**The observable is every column of the posting record, plus any column `postings` can reach.** The
decisive question is whether `postings` is *stored anywhere* — if the diff is empty with the move present
and also empty with it absent, the statement is observably inert and that is a real result. If either diff
is non-empty, record which column moved. Note that `RRN` may exceed `postings`' picture, in which case the
stored value is a truncation rather than a copy; that value half is
`Q-A17-POSTINGS-EFFECT` (§14), and it was measured by the probe rather than by that run — see (d).

**(d) Resolution — MEASURED 2026-08-07, GnuCOBOL 3.2.0.**

The experiment in (c) proposed reaching the answer through scenario runs. That would not have reached it:
the effect only appears once `RRN` passes 32767, which no mandated scenario produces, so every one of those
diffs would have come back empty and the statement would have been recorded as *observably inert* — a wrong
answer arrived at honestly. It was measured with a focused probe instead, declaring both operands exactly as
the frozen copybooks declare them.

**The operands, and why the annotation on the receiver is wrong twice over:**

| | declaration | locator | measured width |
| --- | --- | --- | --- |
| source | `Rrn pic 9(5) comp` | `[copybooks/wsfnctn.cob:L24]` | 4 bytes |
| receiver | `Postings binary-short` | `[copybooks/wssystem.cob:L184]` | 2 bytes |

That receiver line annotates itself `*> 9(4) comp`. `binary-short` is **signed**, and its range is **not**
the four digits the comment implies — so the comment misstates the field's sign and its capacity.

**Why it is observable at all**, which part (c) had left as the open question — *"whether `postings` is
stored anywhere"*. It is, twice:

1. `Postings` is a `SYSTEM-REC` column in its own right.
2. `[sales/sl060.cbl:L1037]` reads `add postings 1 giving Batch-start`, and `Batch-Start` is
   `GLBATCH-REC.BATCH-START`, declared `pic 9(5)` **unsigned** at `[copybooks/wsbatch.cob:L54]`.

So the answer to *"nothing in the four programs reads `postings` again"* is that nothing needs to — the
field is itself persisted, and a sibling paragraph in the same program reads it into a second persisted
column.

**Measured, source value through to stored column:**

| `Rrn` | → `Postings` | → `Batch-Start` | |
| --- | --- | --- | --- |
| `1` | `+00001` | `00002` | |
| `9999` | `+09999` | `10000` | |
| `10000` | `+10000` | `10001` | **not** truncated to four digits |
| `12345` | `+12345` | `12346` | **not** truncated to four digits |
| `32767` | `+32767` | `32768` | the last value that survives intact |
| `32768` | `-32768` | `32767` | signed 16-bit wrap, no diagnostic |
| `65535` | `-00001` | `00000` | the database column becomes **zero** |
| `99999` | `-31073` | `31072` | `99999 mod 65536 = 34463`; `34463 − 65536 = −31073` |

`move -1 to Postings` yields `-00001`, confirming the receiver is signed.

**Four findings, of which the last two are the ones that matter:**

1. `binary-short` is **signed**, contradicting its own comment.
2. There is **no decimal truncation at the implied picture**. The full signed binary range governs, which
   means this compiler is not applying `binary-truncate` to this storage class — and that is also the
   `binary-short` half of [`Q-5.1`](#q-5-1), answered here rather than there.
3. Past `32767` the store **wraps as a signed 16-bit integer, silently**. No `ON SIZE ERROR` phrase exists
   at the site, so nothing is reported and nothing is logged.
4. The negative then reaches the **unsigned** `pic 9(5)` `Batch-Start` as its **absolute value** — the same
   magnitude-only rule [`Q-3`](#q-3) measured at the bridge boundary, occurring here at an ordinary COBOL
   store with no bridge involved. The two measurements corroborate each other: unsigned receivers in this
   system take the magnitude, wherever they sit.

**The consequence, stated plainly.** A statement nobody can explain can drive `GLBATCH-REC.BATCH-START` to
`00000`, or to a wrapped magnitude bearing no relation to any record count, on a run large enough to reach
32768 postings — and nothing anywhere reports it. It is **latent, not scenario-reachable**, so no scenario
diff will ever surface it; that is exactly why it is written down here rather than left to a run to find.

The move is reproduced in all four program modules exactly as written, including the wrong-program comment
carried forward as a comment, because R-4 requires the artefact and not a tidied version of it. Measuring
the effect did not license repairing it. Nothing is normalised across the four, and in particular the
`sl060` missing period is **not** repaired to match its three siblings.

**(e) Consuming modules.** All four Sales and Purchase posting program modules:
`acas_posting/programs/sl060_invoice_posting.py`, `acas_posting/programs/sl100_cash_posting.py`,
`acas_posting/programs/pl060_order_posting.py` and `acas_posting/programs/pl100_payment_posting.py`.

---

### The `Q-5.x` storage-semantics cluster

Three questions about how a value is *represented* rather than how it is computed. They share a cluster
number because they share an owner — `acas_posting/cobol/usage.py` — and because all three are settled by
the same class of observation: write a known value through the bridge and look at what arrives.

⚠️ **This paragraph previously read *"All three carry a provisional implementation, and none carries a
measurement"*, and that has not been true since 2026-08-07.** It is corrected rather than quietly replaced,
because a stale summary above three entries is worse than no summary: a reader who trusts it stops before
reaching the entries that contradict it. The current position, per entry rather than in aggregate:

**All three are now `RESOLVED BY ORACLE`**, each with its captured observable written into its own entry —
`Q-5.1`'s widths and both truncation rules, `Q-5.2`'s byte length for a `SIGN LEADING` item, and `Q-5.3`'s
packed and zoned sign bytes. `usage.py` labels each "RESOLVED" at its own site, and for all three that label
is now backed by observation rather than by GnuCOBOL's documentation.

**Under R-6 only an observed run promotes a status**, which is the rule that kept these three honestly
`PENDING` for as long as they were, and the rule that makes the promotions worth anything. §17 carries the
status tally; it is not restated here, for exactly the reason this correction illustrates.

<a id="q-5-1"></a>
#### `Q-5.1` — GnuCOBOL default `binary-size` and `binary-truncate`

**Status: `RESOLVED BY ORACLE`** — measured 2026-08-07, GnuCOBOL 3.2.0. **Both halves are answered, and the
answer splits into two rules where the single flag name had implied one: a `COMP` item with a PICTURE reduces
on its declared digit count, while a `BINARY-*` item declared by USAGE ALONE wraps at its signed byte
capacity.** The provisional constants turned out to be right. The resolution is in (d).

**(a) The question.** With no dialect selected, the compiler's **defaults** govern two separate things for
every `COMP`, `BINARY-CHAR`, `BINARY-SHORT` and `BINARY-LONG` field: how many **bytes** the item occupies
(`binary-size`), and whether a store is reduced to the item's **declared digit count** or to its **byte
capacity** (`binary-truncate`). Neither is stated anywhere in the repository, and the two are independent —
a field can be eight bytes wide and still refuse an eighteenth digit.

**(b) Evidence.** The absence, counted in §9: no `-std=`, no `>>SET ARITHMETIC`, no `binary-truncate`
anywhere in the frozen sources. The compiler is GnuCOBOL **3.2 final** — `[common/comp-common.sh:L9]`,
`[README.TXT:L53]`.

The exposure, from the canonical storage census that §9 adopts by reference: `binary-long` **166**
declared, `binary-char` **84**, `binary-short` **31**, and bare `comp` **214** — 128, 59, 30 and 144
respectively on code lines only. The two questions therefore reach several hundred fields, including
`Run-Date` itself at `[copybooks/wssystem.cob:L67]` and the whole of the narrowed block that `Q-3` is
about.

**The provisional implementation, named so it can be overturned.** `acas_posting/cobol/usage.py` carries
`DEFAULT_BINARY_SIZE_THRESHOLDS` as `(2 digits → 1 byte, 4 → 2, 9 → 4, 18 → 8)` and `BINARY_TRUNCATE = True`,
the module's own comment noting that setting the flag false would make a `COMP` store reduce into its byte
capacity instead of its digit count. That is the documented GnuCOBOL default, transcribed; it is **not** a
measurement.

**(c) Oracle experiment.** Under the §10 protocol, seeding values **at and beyond each declared digit
count** for one field of each width:

```text
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_cobol_scenario.sh                        "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables SALEDGER-REC,GLBATCH-REC,SYSTEM-REC
```

For each width, three seeds: the largest value the declared digits admit, that value plus one, and the
largest value the byte capacity admits. A `binary-long` declared as eight digits accepts `99999999`; the
byte capacity accepts `2147483647`. **The observable is which of the two ceilings the stored column
respects** — a store that survives `999999999` has truncated to capacity, and one that wraps or clips at
`99999999` has truncated to digits. Read as `int`, never through a float (R-2). Repeat at `binary-short`
and `binary-char` widths, because the policy may not be uniform across them.

**(d) Resolution — MEASURED 2026-08-07, GnuCOBOL 3.2.0.**

The experiment in (c) proposed reaching this through seeded scenario runs. That was more apparatus than the
question needs, and it would have answered only for the handful of fields a scenario happens to touch. It was
measured instead with a probe that declares each form directly and stores values at and beyond every ceiling
— asking the compiler about its own policy rather than inferring the policy from a row.

**`binary-size` — `FUNCTION LENGTH`, as the compiler reported it:**

| declaration | measured bytes |
| --- | --- |
| `binary-char` | **1** |
| `binary-short` | **2** |
| `binary-long` | **4** |
| `pic 99 comp` | **1** |
| `pic 9(4) comp` | **2** |
| `pic 9(5) comp` | **4** |
| `pic 9(8) comp` | **4** |
| `pic 9(9) comp` | **4** |
| `pic s9(4) comp` | **2** |
| `pic s9(9) comp` | **4** |

That is exactly `DEFAULT_BINARY_SIZE_THRESHOLDS` — `(2 → 1, 4 → 2, 9 → 4, 18 → 8)` — confirmed from outside
the implementation, and the signed forms confirm the sign costs no byte.

**`binary-truncate` — and here the question turns out to have been two questions.**

*A `COMP` item WITH a picture reduces on its DIGIT COUNT, modulo `10**digits`:*

| store | kept |
| --- | --- |
| `100` into `pic 99 comp` | **`00`** |
| `127` into `pic 99 comp` | **`27`** |
| `10000` into `pic 9(4) comp` | **`0000`** |
| `32767` into `pic 9(4) comp` | **`2767`** |
| `100000` into `pic 9(5) comp` | **`00000`** |
| `100000000` into `pic 9(8) comp` | **`00000000`** |
| `1000000000` into `pic 9(9) comp` | **`000000000`** |

The two rows that carry the argument are `127` and `32767`: **each fits its item's byte capacity exactly, and
each was still reduced.** So `binary-truncate` is in force, and `BINARY_TRUNCATE = True` is confirmed.

*An item declared by USAGE ALONE has no digit count for that policy to apply to, so the capacity is all
that is left — and the store wraps, signed, in silence:*

| store | kept |
| --- | --- |
| `127` into `binary-char` | **`+127`** |
| `128` into `binary-char` | **`−128`** |
| `255` into `binary-char` | **`−001`** |
| `32767` into `binary-short` | **`+32767`** |
| `32768` into `binary-short` | **`−32768`** |
| `99999` into `binary-short` | **`−31073`** |

**`32767` is the value that proves the two rules are different rules.** Into `pic 9(4) comp` it becomes
`2767`; into `binary-short` it survives whole. Both items occupy the same two bytes, so this is a policy
difference and not a width difference — and reading `binary-truncate` as one uniform rule would get one of
the two classes wrong for every field in it. The census in (b) shows neither class is rare: **236** bare
`comp` declarations against **282** pictureless `binary-*` ones (`binary-long` 166, `binary-char` 84,
`binary-short` 32).

*And a third confirmation of the magnitude rule, arriving unlooked-for:*

| store | kept |
| --- | --- |
| `−1` into `pic 9(4) comp` | **`0001`** |
| `−9999` into `pic 9(4) comp` | **`9999`** |

An unsigned receiver takes the **magnitude**. [`Q-3`](#q-3) measured that at the bridge boundary and
[`Q-5`](#q-5) measured it at `add postings 1 giving Batch-start`; this is a bare `MOVE` with neither a bridge
nor an `ADD` involved. Three independent sightings of one rule, which is what lets it be stated as the
system's behaviour rather than as a property of one code path.

**Alignment with the shipped code — checked, not assumed.** All **24** captured vectors were replayed against
`acas_posting/cobol/usage.py`: **24 agreements, 0 mismatches**, across `byte_length`, `coerce` on pictured
and pictureless forms, the magnitude rule, and `value_domain`. **No production change was required.** What
changed is the standing of the values: they were transcribed from documentation and are now observed. The
constants are additionally pinned from outside by `tests/arithmetic/test_comp_binary.py` GROUP 12, whose
vectors are copies of the compiled output rather than recomputations — so a drift in `usage.py` breaks them,
which a test deriving its expectation from the same constants could not do. Non-vacuity was verified by
flipping `BINARY_TRUNCATE` in-process: `pic 9(4) comp ← 32767` moved from `2767` to `32767` and the vector
rejected it.

⚠️ **One piece of bookkeeping this closed.** `usage.py` labelled Q-5.1 "RESOLVED" at its own site, and
`test_comp_binary.py` called the constants "the measured policy", while this register carried the question as
`PENDING` — a three-way disagreement in which the register was right and the other two were ahead of their
evidence. Both of those wordings have been corrected in place, with the correction visible rather than
silent, because the distance between *documented* and *observed* is precisely what R-6 exists to police.

**(e) Consuming module.** `acas_posting/cobol/usage.py`. Test-owned by
`tests/arithmetic/test_comp_binary.py`, which records the absence census in its own header, asserts the two
policy constants in GROUP 10, and holds the twenty-four captured vectors in GROUP 12. Since the measurement
those propositions are asserted rather than marked — there is no longer an unmeasured default for any of them
to depend on.

<a id="q-5-2"></a>
#### `Q-5.2` — the byte length of a `SIGN LEADING` display item

**Status: `RESOLVED BY ORACLE` (2026-08-07).**

**(a) The question.** Does a `SIGN LEADING` display item, written **without** `SEPARATE`, occupy the same
number of bytes as its digits, or one byte more? Reading cannot settle it because the **best in-repo
evidence is documentary rather than executable** — a byte-count comment in a copybook — and read carefully
that comment points the *opposite* way from the ISO reading, while a third observation in the *same*
copybook undercuts the comment.

**(b) Evidence.** The clause appears in two spellings and six places, and **no `separate` keyword appears
anywhere in the frozen record layouts** (§9): `sign leading` at `[copybooks/wspost-irs.cob:L21]` and
`[copybooks/wspost-irs.cob:L25]`; `sign is leading` at `[copybooks/irswspost.cob:L14]` and
**`[copybooks/irswspost.cob:L18]`** — ⚠️ `L18`, not `L19`, which is the closing `*>`. Census:
`sign leading` 4, `sign is leading` 2, `sign trailing` 0, `separate` 0.

The documentary evidence is `[copybooks/wspost.cob:L6-L7]`:

```text
*> 98 bytes 26/03/09
*> 96 bytes 20/12/11 (leading sign removed)
```

Removing the clause from **two** fields — `Post-Amount` at `[copybooks/wspost.cob:L23]` and `Vat-Amount` at
`[copybooks/wspost.cob:L28]`, whose leading-sign forms survive in the IRS variants cited above — moved the
total from 98 to 96, i.e. it saved **one byte per field**.

⭐ **Three readings follow, and this register adjudicates none of them.**
[`anomaly-log.md`](anomaly-log.md) §14.2 sets them out and this entry adopts its framing:

- **Reading A — width is digits + 1.** Taken as a byte account, one byte saved per field means the leading
  sign occupied a byte of its own, so `pic s9(7)v99 sign leading` would be **10** bytes, not 9.
- **Reading B — width is digits.** The ISO overpunch reading: `SIGN LEADING` without `SEPARATE` overpunches
  the leading digit and costs nothing, so the same field is **9** bytes. **This is what
  `acas_posting/cobol/usage.py` implements** — it returns `digit_count + 1` only for the two `SEPARATE`
  positions and `digit_count` otherwise — and it is a transcription of the standard, not a measurement.
- **Reading C — why Reading A is genuinely puzzling rather than obviously right.** In the *same* copybook the
  **trailing** sign is provably overpunched. The maintainer's own running offsets advance by exactly ten
  bytes across each ten-digit money field: 36 to 46 over `Post-Amount`, `[copybooks/wspost.cob:L22-L23]`,
  and 86 to 96 over `Vat-Amount`, `[copybooks/wspost.cob:L27-L28]`. An included sign costs nothing there,
  twice — which makes the one-byte-per-field history of the *leading* case a real question rather than a
  slip of the pen.

⚠️ The brief for this file states that the note *"indicates a `SIGN LEADING` (non-separate) field occupies
the same byte count as its digits"*. Read as a byte account it indicates the opposite; §8 records the
correction. Writing either conclusion as fact would silently pick a side in an open question, which is what
R-4 forbids.

**(c) Oracle experiment.** Under the §10 protocol, write a known signed value through the bridge in each
sign and read the representation back:

```text
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_cobol_scenario.sh                        "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables PSIRSPOST-REC,IRSPOSTING-REC
```

The four fields to drive are the leading-sign money fields of the two IRS posting layouts:
`WS-IRS-Post-Amount` and `WS-IRS-Vat-Amount` `[copybooks/wspost-irs.cob:L21]`,
`[copybooks/wspost-irs.cob:L25]`, and `Post-Amount` and `Vat-Amount` `[copybooks/irswspost.cob:L14]`,
`[copybooks/irswspost.cob:L18]`. Seed a positive value, a negative value of equal magnitude, and zero, for
each field.

**The observable is two things, and both are needed.** First, the **column value** at full declared scale,
which shows whether the sign survived. Second, the **raw stored bytes** — obtained by a `SELECT`-side cast
in `harness/dump_tables.py`'s own query, never by adding a column or a generated field (R-3) — which shows
*where* the sign lives and therefore how many bytes the item occupies. Reading A predicts a distinct sign
byte ahead of the digits; Reading B predicts the leading digit's own byte carrying the sign in its zone
nibble. Record the byte sequence verbatim for all three seeds.

**(d) Resolution. MEASURED: Reading B — the width is `digits`, and an included leading sign spends no byte.**
Reading A — digits plus one — is refuted.

The experiment described above routes through the bridge and needs a scenario that drives the four
leading-sign fields. A far shorter route reaches the same answer with less that can go wrong: **ask the
compiler what the item's length is.** `FUNCTION LENGTH` is evaluated by the compiler against its own storage
layout, so it reports the width the compiled program actually uses, without a seed, a bridge, a column or a
cast standing between the question and the answer.

| declaration | `FUNCTION LENGTH` |
| --- | --- |
| `pic s9(7)v99 sign is leading` | **9** |
| `pic s9(7)v99 sign is leading separate` | **10** |
| `pic s9(7)v99` (default, trailing included) | **9** |
| `pic s9(7)v99 sign is trailing separate` | **10** |

The four rows together are the argument, not just the first. An INCLUDED sign — leading or trailing — costs
nothing, and only `SEPARATE` buys a byte of its own. The byte dump shows where the sign goes: `move -12.34`
puts `p` (0x70) in byte 1 and the digits `0`..`4` in bytes 2 to 9; `move +12.34` puts `0` (0x30) in byte 1. So
the sign is OVERPUNCHED onto the leading digit, which is why it costs nothing — and `separate` appears
**zero** times in the frozen record layouts (§9), so the ten-byte row is a control rather than a case the
migration has to carry. That is Reading B, the ISO overpunch reading implemented at
`[acas_posting/cobol/usage.py byte_length]`. **Reading A, `digits + 1` = 10, is measured FALSE.**

Measured with GnuCOBOL 3.2.0, `cobc -x -free`, no `-std=` dialect selection, no
`>>SET ARITHMETIC` directive and no `binary-truncate` flag — the same absence §9
counts across every frozen compile line.

**What the measurement does NOT settle, stated so the entry does not overclaim.** It does not explain the
maintainer's own byte accounting at [`copybooks/wspost.cob:L6-L7`] — *"98 bytes"* then *"96 bytes … (leading
sign removed)"*, two fields and two bytes. That arithmetic remains inconsistent with a nine-byte leading-sign
field, and this register records the inconsistency rather than resolving it: the *width the compiler uses* is
now known; *what the maintainer was counting* is not, and no reading of the frozen source recovers it. Rule
R-4's discipline applies to comments as much as to code — the contradiction stands.

`[acas_posting/cobol/usage.py byte_length]` already implemented Reading B, so this confirms the layer rather
than changing it. `tests/arithmetic/test_sign_leading_display.py` now asserts the width and the overpunch
bytes as facts and carries **no** strict expected failure: the refuted reading is asserted against directly,
which is a louder failure than an unexpected pass and needs no marker to stay honest.

The byte account of `Q-4`'s Sibling 2 does **not** depend on this answer — neither money field carries a
`sign leading` clause in the *current* declaration, and the ten bytes each occupies is corroborated by
Reading C.

**(e) Consuming module.** `acas_posting/cobol/usage.py`. Test-owned by
`tests/arithmetic/test_sign_leading_display.py`;
`tests/arithmetic/test_irs_date_component_derivation.py` cross-references it and deliberately checks sign
*position* and *spelling* only, never `byte_length`.

<a id="q-5-3"></a>
#### `Q-5.3` — the overpunch and packed-decimal byte values

**Status: `RESOLVED BY ORACLE` (2026-08-07)** — both halves. An earlier revision of this entry read
`PARTIALLY RESOLVED BY ORACLE`, on the ground that the probe series had read zoned bytes and never a
`COMP-3` item's; the packed half was measured afterwards by the `REDEFINES`-and-`FUNCTION ORD` probe
recorded in (d), which reads all twelve nibbles, so the qualification no longer applies.

**(a) The question.** What concrete byte does a zoned `DISPLAY` digit carry for a positive sign, for a
negative sign, and for zero — and, in the packed case, which nibble carries the sign and what value does it
take? Reading cannot settle either because no frozen declaration states an encoding: the copybooks declare
pictures, and the bytes belong to the compiler and to the C interface. **The values must be measured, not
assumed from a standard** — the standard permits more than one zone convention, and which one a given
GnuCOBOL build emits depends on how it was configured.

⭐ **This identifier deliberately covers both representations, and that is not this register's choice
alone.** `tests/arithmetic/test_comp3_packed_decimal.py` states at `L66-L69` that the register *"carries no
separate id for the packed byte values; Q-5.3 is therefore the id cited, being the one the owning module
names, and NO NEW ID HAS BEEN INVENTED."* Splitting the packed case out now would strand twelve citations in
that file. `Q-5.3` therefore has two halves, and each is measured separately even though they share a
number.

**(b) Evidence.** The exposure is every `DISPLAY` numeric field in the in-scope layouts — the six
leading-sign fields of `Q-5.2` plus every unsigned `pic 9(n)` that reaches a `char` column — and every
`comp-3` field, of which the `copybooks/` census counts **182** (§9).

**The provisional implementation, named so it can be overturned.** `acas_posting/cobol/usage.py` carries
both halves as named constants:

| Half | Constants | Provisional value |
| --- | --- | --- |
| Zoned `DISPLAY` | `ZONED_POSITIVE_ZONE`, `ZONED_NEGATIVE_ZONE`, and the digit-indexed `ZONED_POSITIVE_BASE` / `ZONED_NEGATIVE_BASE` built from them in one pass so they cannot drift | zone nibbles `0x30` and `0x70` — the ASCII-mode values the compiler documentation describes |
| Packed `comp-3` | `PACKED_SIGN_POSITIVE`, `PACKED_SIGN_NEGATIVE`, `PACKED_SIGN_UNSIGNED`, plus two-digits-per-byte nibble placement | `0xC`, `0xD`, `0xF` |

Both sets are transcriptions. The module's "RESOLVED" label at those lines means
settled-for-implementation, not observed, and the sibling test says the same in its own words. What that
test *does* assert outright is the set of **structural** facts the module's contract fixes regardless of the
byte values — the total width, which nibble carries the sign, and that `decode(encode(v)) == v` — which is
the right line to draw: structure from the contract, values from the oracle.

**(c) Oracle experiment.** As `Q-5.2`, and **from the same run** — the two read the same bytes, and
measuring them separately would make any discrepancy between them indistinguishable from a difference
between the runs:

```text
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables PSIRSPOST-REC,IRSPOSTING-REC,GLBATCH-REC
```

`PSIRSPOST-REC` and `IRSPOSTING-REC` carry the leading-sign `DISPLAY` money fields; `GLBATCH-REC` carries
the packed half, since `[copybooks/wsbatch.cob:L40-L44]` groups its four `pic 9(9)v99` amounts under
`03 Amounts comp-3.` — eleven digits, unsigned at the copybook level, which makes the unsigned sign nibble
observable as well as the signed ones.

**The observable is the byte-level value of each digit position, for a positive value, a negative value and
zero, in both representations.** Zero is not padding here: it is the case that distinguishes a signed-zero
convention from an unsigned one, and it is the one most likely to differ from the transcribed tables.
Capture the bytes as integers or as a hex string — never through a float, and never through a text decode
that could normalise a high-bit byte (R-2).

**(d) Resolution. MEASURED — both halves, all three signs, and from a single run.** The transcribed tables
above are **confirmed**, and the zero convention that was singled out as the case most likely to differ is
measured rather than inferred.

The experiment described above routes through the bridge and needs a scenario that drives the leading-sign
money fields. A shorter route reaches the same bytes with less between the question and the answer: declare
each representation exactly as the frozen copybooks declare it, `REDEFINES` it as `pic x(n)`, and read every
byte with `FUNCTION ORD`. Both halves were driven in one program, which is what §(c) asks for — a discrepancy
between them cannot then be blamed on a difference between runs. Measured with GnuCOBOL 3.2.0,
`cobc -x -free`, no `-std=` dialect selection, no `>>SET ARITHMETIC` directive and no `binary-truncate`
flag — the same absence §9 counts across every frozen compile line.

**The packed half** — `pic s9(8)v99 comp-3` as [`copybooks/wsledger.cob:L28`] declares `Ledger-Balance`, and
`pic 9(9)v99 comp-3` as [`copybooks/wsbatch.cob:L40-L44`] groups its amounts. Six bytes, twelve nibbles,
digits followed by the sign nibble in the low nibble of the last byte:

| value | nibbles | sign nibble |
| --- | --- | --- |
| signed `+1234.56` | `0 0 0 0 0 1 2 3 4 5 6 C` | **`0xC`** |
| signed `-1234.56` | `0 0 0 0 0 1 2 3 4 5 6 D` | **`0xD`** |
| signed `0.00` | `0 0 0 0 0 0 0 0 0 0 0 C` | **`0xC`** — a zero in a **signed** field carries the POSITIVE nibble |
| unsigned `1234.56` | `0 0 0 0 0 1 2 3 4 5 6 F` | **`0xF`** |
| unsigned `0.00` | `0 0 0 0 0 0 0 0 0 0 0 F` | **`0xF`** |

**The zoned half** — `pic s9(8)v99` DISPLAY, ten bytes, one per digit:

| value | bytes | sign-carrying byte |
| --- | --- | --- |
| `+1.00` | `30 30 30 30 30 30 30 31 30 30` | **`0x30`** |
| `-1.00` | `30 30 30 30 30 30 30 31 30 70` | **`0x70`** |
| `0.00` | `30 30 30 30 30 30 30 30 30 30` | **`0x30`** — again the positive form |

The same values were reached independently on a `pic s9(7)v99 sign is leading` item, where the sign is
overpunched onto the LEADING digit rather than the trailing one: `move -12.34` puts `p` (0x70) in the
sign-bearing byte, `move +12.34` puts `0` (0x30) there, and every non-sign digit byte is `0x30` plus the
digit in both cases. Two declarations, two sign positions, one pair of zone values.

**So `PACKED_SIGN_POSITIVE = 0xC`, `PACKED_SIGN_NEGATIVE = 0xD`, `PACKED_SIGN_UNSIGNED = 0xF`,
`ZONED_POSITIVE_ZONE = 0x30` and `ZONED_NEGATIVE_ZONE = 0x70`**, all as
`[acas_posting/cobol/usage.py PACKED_SIGN_POSITIVE]` and `[acas_posting/cobol/usage.py ZONED_POSITIVE_ZONE]`
already transcribed them. The module's "RESOLVED" label at those lines meant *settled-for-implementation*; it
is now settled by observation, and the entry says which.

**The zero convention is the part that was genuinely open**, and it is worth stating on its own because
`Q-70f` depends on it: a zero stored in a **signed** field carries the POSITIVE sign form in both
representations. That is why negating a zero leaves the bytes unchanged — there is no negative-zero encoding
to move to — and it is the measurement `Q-70f` cites.

**And the sign has to ARRIVE BY ARITHMETIC for that to hold, which a negative literal does not.** On the
leading-sign item: `move 0.00` gives `0`; `compute x = 0.00 * -1` gives `0`; `multiply zero by -1 giving x`
gives `0`; but the LITERAL `move -0.00` gives `p`. For contrast, `move 12.34` then `multiply by -1` gives
`t` (0x74) — the negative zone over the digit 4. The distinction is load-bearing rather than academic
because every in-scope negation is arithmetic and none is a literal: `[general/gl070.cbl:L517]` and
`[general/gl070.cbl:L530]` are `multiply pre-amount by -1`.

**(e) Consuming module.** `acas_posting/cobol/usage.py`. Test-owned by
`tests/arithmetic/test_sign_leading_display.py` for the zoned half and
`tests/arithmetic/test_comp3_packed_decimal.py` for the packed half.

---

### The three questions discovered while writing the migration

`Q-6`, `Q-7` and `Q-8` are not in AAP §0.6.8. They surfaced while the CLI entry points and the harness
runners were written, and each is a place where the **COBOL route and the Python route are not the same
route** — which makes them questions about the comparison itself rather than about a computation. They are
recorded here because a difference in the route is exactly the kind of thing that produces a non-empty diff
for a reason that has nothing to do with the migration's correctness, and the temptation to suppress such a
difference quietly is strong.

<a id="q-6"></a>
#### `Q-6` — the `sl830` asymmetry

**Status: `RESOLVED BY ORACLE` (2026-08-04).**

**(a) The question.** The Sales menu dispatches `sl830` **before** `sl055` on the invoice-posting selection.
`sl830` belongs to the sales autogen series, which is **out of scope** (AAP §0.2.2), and the Python route
dispatches only `sl055 → sl060`. Because the COBOL runner drives the **menu**, `sl830` **will** execute on
the COBOL side of every invoice-posting comparison and **never** on the Python side. Whether that is
observable is the question, and reading gives only an expectation.

**(b) Evidence.** `[sales/sales.cbl:L756-L763]`, verbatim:

```text
 load07.             *> Sales trans posting
*>-----
*>
     move     "sl830" to WS-Called.   *> In case autogen is use
     perform  load00.
     if       ws-term-code not = zero
              go to display-menu.
     move     "sl055" to ws-called.
```

The maintainer's own changelog records the addition at `[sales/sales.cbl:L121]`:
*"31/05/23 vbc - .32 Added execution of sl830 first when Invoice Post selected."* — and at
`[sales/sales.cbl:L124]` a follow-up correcting which loader paragraph it uses.

The supporting reading, which is the whole basis of the expectation:
`[sales/sl830.cbl:L266-L270]` opens `aa000-Main section.` with

```text
     if       SL-Autogen not = "Y"    *> SL Autogen not in use
              goback.
```

so with the autogen switch off the program returns before it does anything at all.

⚠️ **Purchase has no such asymmetry, and that divergence is preserved rather than harmonised.** The
equivalent block in `purchase.cbl` is **commented out** at `[purchase/purchase.cbl:L755-L758]`:

```text
 *>    move     "pl830" to WS-Called.   *> In case autogen is use
 *>    perform  load000.
 *>    if       ws-term-code not = zero
 *>             go to display-menu.
```

so `[purchase/purchase.cbl:L759]` reaches `pl055` directly. That is **A-NEW-5**. The two ledgers therefore
differ in route, and the Python side must not be "corrected" to make them match — the Sales CLI dispatches
`sl055 → sl060` and the Purchase CLI dispatches `pl055 → pl060`, which is symmetric in Python precisely
because the COBOL is asymmetric and the asymmetric part is out of scope.

**(c) Oracle experiment.** Under the §10 protocol, run the Sales invoice-posting scenario on both sides
with the autogen switch off:

```text
S=/repo/harness/scenarios/clean_batch_sl.yaml
N=clean_batch_sl

$C /repo/harness/run_parity.sh --seed-dir "/data/fixtures/$N" "$S"
```

⚠️ **The autogen observation is NOT made with `dump_tables.py`, and cannot be.** An earlier revision of
this entry proposed `dump_tables.py --scenario clean_batch_sl --side cobol --tables
SAAUTOGEN-REC,SAAUTOGEN-LINES-REC,PUAUTOGEN-REC,PUAUTOGEN-LINES-REC`. **That command exits 83 without
dumping anything.** All four tables are among the eleven AAP §0.2.2 lists as out of scope, and
`harness/dump_tables.py` raises `TableNotInScopeError` for every one of them
`[harness/dump_tables.py TableNotInScopeError]`, mapped to `EX_SCOPE = 83` `[harness/dump_tables.py EX_SCOPE]`, with the
message stating the reason: *"dumping one would compare state the migration does not produce."* That
refusal is correct behaviour, not a limitation to work around — the diff is defined over the in-scope
tables, and a dump that reached outside them would compare state no scenario declares.

**The mechanism that does make the observation is a row-count probe inside each runner, and it already
exists.** It is a `count(*)`, not a dump, so it never enters the normalised trees and never reaches
`diff_states.py`:

| Side | Tables probed | Where | Disposition |
| --- | --- | --- | --- |
| COBOL | `SAAUTOGEN-REC`, `SAAUTOGEN-LINES-REC` — the Sales pair only, since only the Sales menu calls `sl830` | `[harness/run_cobol_scenario.sh ACAS_RUN_AUTOGEN_TABLES]` declares them; `[harness/run_cobol_scenario.sh acas_assert_after_run]` probes them, and only when the subsystem is `sales` | 0 rows ⇒ `PASS … sl830 was a no-op`; non-zero ⇒ a counted assertion failure, because autogen being in use makes the run non-comparable. A table that cannot be counted is *noted*, not failed |
| Python | all four, including the Purchase pair | `[harness/run_python_scenario.sh ACAS_PY_AUTOGEN_TABLES]` declares them; `[harness/run_python_scenario.sh acas_py_assert_after_run]` probes them through `acas_py_table_counts` | same three-way disposition, with the comment inside `[harness/run_python_scenario.sh acas_py_assert_after_run]` naming this as what makes the route asymmetry safe to live with rather than merely asserted in prose |

There is also a **pre-run gate** on the COBOL side that makes the switch-off state binding rather than
hoped for: `[harness/run_cobol_scenario.sh acas_assert_database]` reads `SYSTEM-REC.SL-AUTOGEN` before the run and
dies if it is `"Y"`, on the ground that the Sales invoice path would then be non-deterministic.

**So the observable is two-part.** First, the probes above report 0 rows on both sides. Second, the
scenario's own stage-10 diff over its declared affected tables is empty. Together they say that `sl830`'s
presence on one side changed nothing anywhere — the first for the tables it would have written, the second
for the tables the migration does write.

Repeat once with the autogen switch **on**, not to compare the two sides — `sl830` has no Python
counterpart, so that comparison is meaningless — but to establish that the switch is what gates the
program, and therefore that the scenarios' setting of it off is load-bearing rather than incidental.

**(d) Resolution.** The expectation was confirmed. The compiled `clean_batch_sl` and `period_end_totals`
runs both executed the Sales menu with `SL-Autogen` off — the pre-run gate above would have refused them
otherwise. The two sides probe different-sized sets, deliberately: the COBOL runner's
`[harness/run_cobol_scenario.sh ACAS_RUN_AUTOGEN_TABLES]` names the Sales pair `SAAUTOGEN-REC` and
`SAAUTOGEN-LINES-REC`, because `sl830` is the only autogen program the compiled route can reach, while the
Python runner's `[harness/run_python_scenario.sh ACAS_PY_AUTOGEN_TABLES]` names all **four**, Purchase pair
included, because the Python route reaches none of them and can therefore afford the wider assertion. Both
probes found their tables empty, and both full journeys then produced observed empty final-diff stages. The
route asymmetry is therefore observably a no-op under the mandated seed.

**Evidence, and what survives of it.** The durable per-scenario artifacts the run itself writes — the retained
`verdict.json` and `parity-result` of the `clean_batch_sl` and `period_end_totals` runs, the two normalised
trees, and the post-run assertion lines in the stage log under `$ACAS_OUT/run-logs/<scenario>/cobol.log`,
inside this clone's `acas-harness-<CLONE_INDEX>-out` volume — together with
[`scenario-diff-evidence.md`](scenario-diff-evidence.md), whose §10.2 (`clean_batch_sl`) and §10.6
(`period_end_totals`) carry each run's affected-table list, manifest fingerprint and diff outcome. Regenerate
the whole sweep rather than trusting any path:

```bash
export CLONE_INDEX=001      # plus the credential variables, per README section 8.1
for s in harness/scenarios/*.yaml; do
  docker compose -f harness/docker-compose.yml run --rm -T gnucobol \
      /repo/harness/run_parity.sh "/repo/$s" < /dev/null
done
```

⚠️ Earlier revisions cited a session-scoped `/tmp` log here. That file does not outlive the session that
produced it, so the citation has been removed rather than left as a path a reader cannot open, and it is
replaced by the command above and the volume-backed artifacts, both of which do survive. Anything in this
paragraph that the evidence register does not itself record — the per-table probe results specifically — is a
**report of an observed run rather than a retained artefact**, and is labelled as such wherever this register
quotes one. Re-running the two scenarios under the §10 protocol reproduces the probe lines verbatim, since
both runners emit them unconditionally.

This resolution is deliberately conditional on the switch-off state used by
the scenarios. It does not claim parity for `sl830` with autogen enabled; that
program remains out of migration scope.

**(e) Consuming modules.** `harness/run_cobol_scenario.sh` and `harness/run_python_scenario.sh` (AAP
§0.4.1.7), which are the two halves of the route difference and the two places an assertion about the
autogen tables belongs.

<a id="q-7"></a>
#### `Q-7` — the menu shells' exit-path rewrite

**Status: `RESOLVED BY ORACLE` (2026-08-04).**

**(a) The question.** Every menu shell rewrites three system rows on its way out, through a paragraph the
Python CLI has no counterpart for. The question is what those rewrites actually change in the database —
because if they change anything, the COBOL side of every comparison carries writes the Python side cannot
produce, and the diff would be non-empty for a reason that is not a migration defect. Reading cannot settle
it: the paragraph rewrites whatever the in-memory system record happens to hold at that moment, which
depends on everything the run did beforehand.

**(b) Evidence.** `[general/general.cbl:L656-L691]`. The paragraph runs **twice over the same three keys** —
once against the RDB and once against the COBOL flat file:

| Pass | Key 1 `SYSTEM-REC` | Key 2 `SYSDEFLT-REC` | Key 4 `SYSTOT-REC` |
| --- | --- | --- | --- |
| RDB branch, guarded by `File-System-Used NOT = zero` at `L657` | `L659`, `L661` | `L664` | `L667` |
| COBOL flat file, unguarded, `L676-L691` | `L679`, `L681` | `L684` | `L687` |

The same shape appears in the other two menus: `[sales/sales.cbl:L628]` with its tail at
`[sales/sales.cbl:L659-L660]`, and `[purchase/purchase.cbl:L621]` with its tail at
`[purchase/purchase.cbl:L652-L653]`.

⭐ **The paragraph is reached on every call, and that is provable from a picture clause.** `WS-Term-Code` is
`pic 99` at `[copybooks/wscall.cob:L10]` — the maintainer widened it from `9` on 14/11/25, recorded at
`[copybooks/wscall.cob:L4]` — so the menus' `< 8` and `> 7` tests between them cover every value the field
can hold. The two branches are **exhaustive**, and `load000` therefore performs `overrewrite`
unconditionally. There is no path through a menu dispatch that skips it.

**⭐ CORRECTED — the Python CLI DOES reproduce this, and that is what closed the question.** An earlier form
of this entry read *"the Python CLI does none of this: it has no menu, so it has no exit path to hang the
paragraph off"*. That was true of an earlier tree and is **false of this one** — verified by reading the
shipped code, not inferred. A single-operation process has exactly one exit, so
`acas_posting/cli/args.py`'s `overrewrite` runs the RDB arm once per process:

| Route family | Where | Keys rewritten |
| --- | --- | --- |
| General — `gl_post_cycle`, `gl_end_of_cycle` | `acas_posting/cli/args.py`'s `overrewrite`, called from `` `acas_posting/cli/gl_post_cycle.py load00` `` and `` `acas_posting/cli/gl_post_cycle.py main` ``, and from `` `acas_posting/cli/gl_end_of_cycle.py load00` `` and `` `acas_posting/cli/gl_end_of_cycle.py main` `` | **1, then 2, then 4** — `general_menu_state()` carries both a defaults record and a totals record |
| Sales and Purchase — `sl_invoice_post`, `sl_cash_post`, `pl_order_post`, `pl_payment_post` | the same `overrewrite`, through each route's own wrapper | **1, then 4** — `slpl_menu_state()` carries a totals record and no defaults record |
| IRS — `irs_post` | **not** `overrewrite`. `irs/irs.cbl` has no such paragraph — verified by search — so the route reproduces that menu's `EOJ.` instead, in `acas_posting/cli/args.py`'s `eoj_persist_irs_system_data` | **1 alone**, and it **re-reads key 1 first** `[irs/irs.cbl:L759-L762]`, so the rewrite discards every in-memory change outside the IRS block |

So the per-route divergence in the table above comes out of one implementation without a special case — key 1
unconditionally, key 2 only when the route loaded the defaults record, key 4 only when it loaded the totals
record — and **every one of the seven routes rewrites `SYSTEM-REC` under key 1**. The two shapes are preserved
as two shapes rather than harmonised (R-4), and the absence of a term-code gate on the IRS route is recorded in
`acas_posting/cli/irs_post.py`'s module docstring under the heading *"THERE IS NO TERM-CODE GATE ON THIS
ROUTE - AND THAT IS REPRODUCED, NOT LOST"*. One deliberate divergence is recorded at the site: the frozen RDB
arm is guarded by `File-System-Used NOT = zero` at `[general/general.cbl:L657]` while the Python arm is
**unconditional**, because that gate selects between two stores and the migration has one — `args.py` states
this in `overrewrite`'s own docstring rather than hiding it.

**What this does to the question.** It removes the asymmetry the question was originally about: the COBOL side
no longer carries parameter-table writes the Python side cannot produce. It does **not** make the rewrites
unobservable, so the comparison still has to reach them — and it does, twice over.

⭐ **`SYSTEM-REC` IS DUMPED, WITH EXACTLY TWO CELLS WITHHELD, AND FINGERPRINTED AS WELL.** The row is one of
the 22 in-scope tables every capture covers, so all its columns are compared by value with two named
exceptions: `harness/dump_tables.py`'s `REDACTED_COLUMNS` replaces `RDBMS-PASSWD`
`[copybooks/wssystem.cob:L139]` and `PASS-WORD` with `REDACTED_VALUE` in `render_value`, the one funnel every
captured cell passes through. That is applied identically on both sides and keyed by `(table, column)`
constants, so the redaction cannot itself manufacture a difference, and it costs only what it says: two
credential columns are no longer compared by value. Both legs of a run connect with the **same** credentials
and the builder fills those columns from the same environment for both, so they could not have carried a
behavioural difference of the migrated cycle. Bounding the whole table out — the alternative that was
considered and rejected — would have removed the leak and taken 167 genuinely-written columns with it, and a
bound drawn that way cannot reveal a difference in what it excludes.

On top of the dump, **both runners fingerprint the row before and after every run**, and
`` `tests/conftest.py assert_system_record_parity` `` compares the two sides' post-run digests. The digest is a
sha256 over the canonical primary-key-ordered dump and therefore covers all 169 columns, credentials included,
without being the dump — so the two cells the capture withholds are still compared, as part of a hash that
leaks nothing. ⭐ The second reason for treating the row carefully is recorded rather than overclaimed: its
content depends on what the route DID — the run-date stamp, the IRS allocator, the one-shot latches, and
`Date-Form` `[copybooks/wssystem.cob:L127]`, which the frozen date sections write back — so a scenario's
declared effect could in principle be coupled to fields the scenario does not reason about. **Measured: the
digest holds on all four scenarios that declare `unchanged` and moves on every one that declares `changed`** —
taken over the eight scenarios that existed when the measurement was taken, which is all four `unchanged`
ones, the ninth declaring `changed` and moving the row by construction. So the coupling is theoretical today;
the row is declared on every scenario's
`affected_tables` for that reason, and the fingerprint comparison is what would catch a persistence regression
even if a future scenario's declaration were wrong.

**(c) Oracle experiment.** Under the §10 protocol, with the observation bounded by the scenario's own
affected-table list rather than by everything:

```text
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol --scenario-file "$S"
```

`harness/dump_tables.py` reads the scenario's `affected_tables` list from the YAML and dumps exactly those
tables; `harness/scenarios/clean_batch_gl.yaml` declares it under its own
`affected_tables:` key. Run **all ten stages** — `harness/run_parity.sh --print-stages` lists them, and
`harness/parity_stages.sh` is where they are defined — for
each of the four clean-batch scenarios, then **also** dump the three system tables as a separate observation
and compare them against the seed. ⚠️ That second dump was originally described as covering "the three system
tables outside the affected list", and it no longer is: `clean_batch_gl` now declares `SYSTEM-REC` and
`SYSDEFLT-REC` among its five, `clean_batch_sl` and `clean_batch_pl` declare `SYSTEM-REC` and `SYSTOT-REC`
among their eleven, and `clean_batch_irs` declares `SYSTEM-REC` among its five — so the second dump now
overlaps the first deliberately, and what it adds is the comparison **against the seed** rather than against
the other side:

```text
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables SYSTEM-REC,SYSDEFLT-REC,SYSTOT-REC
```

**The observable is which columns of those three tables differ from the seeded values after a COBOL run that
the Python run cannot reproduce.** That is the size of the problem, stated as a column list rather than as a
worry.

**(d) Resolution.** The scenario-bound comparison is confirmed, and the
cross-process flat-mirror effect is now measured.

1. Bounding by each scenario's `affected_tables` list is correct. All eight
   mandated journeys produced observed empty diffs with no ignore list on
   2026-08-04, and all **nine** committed journeys did so on 2026-08-07.
2. The RDB branch persists the system and totals rows expected by the menu
   shell. `SYSTOT-REC` remains included for `period_end_totals`, whose four
   operations produced the same **15**-table state on both sides. ⚠️ That figure
   read "14" until this revision: `SYSTEM-REC` was added to this scenario's
   affected-table list when the menu-persisted mutation was brought inside the
   comparison, and the prose count was not moved with it.
3. The second, flat-file pass had an additional effect not visible from a
   single menu process: it wrote `File-System-Used = 0` into `system.dat`
   record 1. A later menu process then selected indexed files and issued no
   accounting DML. This was observed directly during `period_end_totals`.
   The oracle build wrapper now restores the saved selector immediately before
   that flat `System-Rewrite`, in the writable build copy only.

After the build-copy shim, operation two of the isolated Sales sequence changed
`SL-PAYMENTS` from `8888.88` to `9691.23`, cleared `S-FLAG-P`, the complete
four-operation journey passed 18 tests, and the standalone ten-stage parity
run produced an empty diff.

**Evidence, and what survives of it.** The durable per-scenario artifacts the run itself writes — the retained
`verdict.json` and `parity-result` of the `period_end_totals` run, the two normalised trees, and the
`SL-PAYMENTS` before-and-after values in the stage log under
`$ACAS_OUT/run-logs/period_end_totals/cobol.log`, inside this clone's `acas-harness-<CLONE_INDEX>-out`
volume — together with [`scenario-diff-evidence.md`](scenario-diff-evidence.md) §10.6, which carries
`period_end_totals`' four operations, its affected-table list including `SYSTOT-REC`, its manifest fingerprint
and its empty diff. The build-copy shim relied on above is durable and readable in committed code: it lives in
`harness/build_oracle.sh` at `acas_install_sqlstate_comment_shim` and writes only into `$ACAS_BUILD`, never
into the checkout. Regenerate the whole sweep rather than trusting any path:

```bash
export CLONE_INDEX=001      # plus the credential variables, per README section 8.1
for s in harness/scenarios/*.yaml; do
  docker compose -f harness/docker-compose.yml run --rm -T gnucobol \
      /repo/harness/run_parity.sh "/repo/$s" < /dev/null
done
```

⚠️ Earlier revisions cited session-scoped `/tmp` logs here — two of them. Those files do not outlive the
session that produced them, so the citations have been removed rather than left as paths a reader cannot open,
and they are replaced by the command above and the volume-backed artifacts, both of which do survive. The
specific figures in the paragraph above (`8888.88 → 9691.23`, the cleared `S-FLAG-P`, "18 tests") are
therefore a **report of an observed run rather than a retained artefact**, and are labelled as such wherever
this register quotes one: the durable claim is the empty diff the evidence register records, and re-running
`period_end_totals` under the §10 protocol reproduces the figures.

⭐ **UPDATE — the bound has since been WIDENED, and resolution point 1 above is superseded.** Point 1 read
"bounding by each scenario's `affected_tables` list is correct". That was sound only while the Python side
produced no system-row writes. Now that every route reproduces the menu's exit-time rewrite — six through
`args.overrewrite` and `irs_post` through `args.eoj_persist_irs_system_data` — the system rows are
**comparable on both sides**, and bounding them out costs evidence rather than buying safety: a bound drawn
from what a scenario *expects* to move cannot reveal a difference in anything it did not expect to move, so a
scenario could report an empty diff while the run date, the allocators, the flags, the defaults or the period
totals differed. The canonical capture and diff are therefore bounded at **all 22 in-scope tables**
(`--all-in-scope`), which `harness/run_parity.sh` passes at the capture, compare and re-capture stages and
`tests/conftest.py` passes from `dump` and `diff`. `affected_tables` is retained as the scenario's **declared
effect**, asserted against `expected_table_effect` within each side, which is a different comparison and
remains correct. The observed empty diffs recorded in `docs/migration/scenario-diff-evidence.md` §8 under the
**narrower** bound are kept there as the earlier register, exactly as measured, because an empty diff over 3,
4, 10 or 14 tables does not establish one over 22.

⛔ **It must never be resolved with an ignore-list inside `harness/diff_states.py`.** That module is required
to have none, and it says so itself: `[harness/diff_states.py summarise]` records *"no ignore-list"* as a
property of the comparison, and `[harness/diff_states.py resolve_tables]` names an ignore-list as **forbidden by rule
R-4**. The distinction matters and is not pedantic: choosing which tables a scenario is *about* is scoping,
declared in the scenario and reviewable there; teaching the differ to overlook a difference it found is
suppression, invisible at the point of use, and it would silently swallow a real regression in the same
column later.

⚠️ **An honest overlap, stated plainly rather than buried.** `SYSTOT-REC` **is** genuinely in scope for the
`period_end_totals` scenario — it is that scenario's focal table, declared as such at
`[harness/scenarios/period_end_totals.yaml "SYSTOT-REC IS THE FOCAL TABLE, AND IT CARRIES A RECORDED CAVEAT (R-4, R-6)"]`, because the nine period-total write sites are its sole
writers. So for one of the nine committed scenarios the containment above does **not** apply: the table the menu
rewrites on exit is the table the scenario exists to compare. That scenario cannot be made safe by scoping,
and its diff depends on this question's answer.

**(e) Consuming modules.** `harness/dump_tables.py` and `harness/diff_states.py` (AAP §0.4.1.7). Related but
distinct, and catalogued in §14: `Q-CLI-OVERREWRITE` and `Q-CLI-OVERREWRITE-SECOND-LEG`, which ask whether
the Python CLI should reproduce the paragraph at all.

<a id="q-8"></a>
#### `Q-8` — `Post-Date (7:2)`: a year, or a century?

**Status: `RESOLVED BY CONSTRUCTION` (2026-08-07).** The Sales and Purchase paths compose a **year**; `irs/irs030.cbl`'s
own conversion path truncates and therefore stores a **century**. The callers do **not** agree, and the
divergence is reproduced rather than repaired.

**(a) The question.** The linkage date is `to-day pic x(10)` in **DD/MM/CCYY** form. `Post-Date` is
`pic x(8)` at `[copybooks/wspost.cob:L18]`. And the bridge derives a **year** from characters 7 and 8 of it,
at `[common/irspostingMT.cbl:L986-L987]`:

```text
     if       Post-Date (7:2) numeric
              move     Post-Date (7:2) to HV-POST4-YEAR.
```

A COBOL alphanumeric `MOVE` from `x(10)` into `x(8)` is left-justified and truncated on the right, so a
caller that simply moved the whole date would leave `"21/09/20"` in an eight-character field — and `(7:2)`
would then capture the **century**, `"20"`, which is numeric and passes the guard without complaint. The
column would hold a plausible, wrong value. Whether any in-scope caller does that is the open half.

**(b) Evidence — the settled half.** On the Sales path the field is **composed, not truncated**.
`[sales/sl060.cbl:L1071-L1072]`:

```text
     move     u-date (1:6) to post-date (1:6).
     move     u-date (9:2) to post-date (7:2).
```

With `u-date = "21/09/2025"` that yields `"21/09/25"`: characters 1 to 6 are `"21/09/"`, and characters 9
and 10 of the source — `"25"` — are placed at positions 7 and 8. `(7:2)` is therefore unambiguously the
**year**, and no measurement is needed to see it. `tests/arithmetic/test_irs_date_component_derivation.py`
records the same reading and closes its own half of the question by construction.

**Evidence — the open half.** The frozen programs reach the date through nine near-identical wrapper
sections rather than one shared routine, and those wrappers reformat between presentations. ⭐ **Within a
single program the two window widths coexist**: `gl070`'s `zz070` International branch reads **four** digits
at `[general/gl070.cbl:L595-L598]` —

```text
     move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
     move     to-day (7:4) to ws-Intl-Year.
     move     to-day (4:2) to ws-Intl-Month.
     move     to-day (1:2) to ws-Intl-Days.
```

— whereas the bridge reads two. The reference-modification census over live lines of the twelve in-scope
programs is `(7:4)` **×16** and `(7:2)` **×4** (§9). The four-digit form dominates, which is exactly why the
two-digit one needs checking rather than assuming: a caller written by analogy with the sixteen would put a
century where the bridge expects a year.

Cross-reference: **A-7** in [`anomaly-log.md`](anomaly-log.md) for the guarded derivation itself and the
internally inconsistent row it can leave. The sibling suite carries this same question under its own
identifier **`Q-25`**, declared *"OWNED HERE"* by
`tests/arithmetic/test_irs_date_component_derivation.py` at `L128-L135`; see §15.

**(c) Oracle experiment.** Under the §10 protocol, for **each** in-scope caller that writes a posting row,
with a pinned run date whose century and year differ visibly — `21/09/2025` gives century `"20"` and year
`"25"`, which cannot be confused:

```text
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_cobol_scenario.sh                        "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables IRSPOSTING-REC,GLPOSTING-REC,PSIRSPOST-REC
```

**The observable is the stored `POST4-YEAR` column against the stored `POST4-DAT` text, per caller.**
`POST4-YEAR = 25` with `POST4-DAT = "21/09/25"` is the composing route; `POST4-YEAR = 20` with
`POST4-DAT = "21/09/20"` is the truncating route. Record the pair for every caller, not a single
representative one — the whole question is whether the callers agree.

**(d) Resolution. `RESOLVED BY CONSTRUCTION` — and the answer is NO, the callers do not agree.**

The open half was *whether every in-scope caller uses the composing route rather than a truncating move.* That
is a question about **which statements exist**, and a census of the frozen source answers it with evidence of
exactly the same kind an oracle run would produce — the statements are either there or they are not. So the
census was taken, over every site in the in-scope programs that writes `Post-Date pic x(8)`
[`copybooks/irswspost.cob:L11`]:

| site | statement | what lands in bytes 7–8 |
| --- | --- | --- |
| [`sales/sl060.cbl:L1071-L1072`] | `move u-date (1:6) to post-date (1:6).` then `move u-date (9:2) to post-date (7:2).` | **YEAR** — composed deliberately |
| [`purchase/pl060.cbl:L937-L938`] | identical to the Sales path | **YEAR** |
| [`irs/irs030.cbl:L1341`] | `move u-date to post-date.` | **CENTURY** |
| [`irs/irs030.cbl:L789`] | `move run-date to post-date.` | pass-through — `run-date` is `pic x(8)` [`copybooks/irswssystem.cob:L14`] |
| [`irs/irs030.cbl:L1662`] | `move WS-IRS-Post-Date to post-date.` | pass-through — `x(8)` to `x(8)`, carrying whatever `sl060`/`pl060` stored |

**The third row is the answer.** `u-date` is `pic x(10)` [`copybooks/wsmaps03.cob:L7`] and `post-date` is
`pic x(8)`, so a plain alphanumeric `MOVE` **truncates on the right** and bytes seven and eight receive the
`CC` of `CCYY` — the century. Nobody chose that; it is a width mismatch. And because both windows are numeric,
both satisfy the bridge's third guard [`common/irspostingMT.cbl:L986-L987`], so `POST4-YEAR` is populated
either way and no row is left with a tell-tale zero component.

**Why this needed no compiled run, stated so the status is not mistaken for a shortcut.** The question reduces
to the widths of two data items and the truncation rule for an alphanumeric `MOVE`. Both widths are declared
in frozen copybooks and quoted above; the truncation rule is the one this migration already measured and locked
in `tests/arithmetic/test_move_truncation.py`. An oracle run would print the same `DD/MM/CC` these declarations
require. Per §4's vocabulary that is `RESOLVED BY CONSTRUCTION`, not `RESOLVED BY ORACLE`, and the entry claims
the weaker of the two on purpose.

**Not repaired (R-3, R-4).** No caller is corralled onto one composition, no range is checked and no century is
restored. `tests/arithmetic/test_irs_date_component_derivation.py` carries the census as
`Q25_COMPOSITION_SITES` and asserts the divergence — that a 2025 date yields `25` on the Sales path and `20`
on the truncating one — so the disagreement is locked in place rather than described. Its `xfail` marker has
been removed, because the proposition it held open (that every caller composes the window alike) is now
answered: it is false.

**The bite, which the sibling assertion keeps.** For a date whose century and year coincide the stored row
cannot say which reading produced it — a stored `20` is a legitimate year in 2020 and a century in 2025, and
the row carries no flag either way.

**A consequence that is settled, and is a constraint rather than a question.** `harness/normalize.py`
canonicalises date **rendering only**. It must **never expand two digits to four, nor contract four to two**.
Either transformation would map the two routes onto the same normalized text and destroy the only evidence
that distinguishes them — turning an open question into a silently closed one, in the one place designed to
make differences visible.

**(e) Consuming modules.** `acas_posting/dal/acasirsub4_irs_posting.py` (which reproduces the guarded
derivation), `acas_posting/dal/acas006_gl_posting.py` (the General posting table's date column) and
`harness/normalize.py` (AAP §0.4.1.7). Test-owned by
`tests/arithmetic/test_irs_date_component_derivation.py`.

<a id="q-9"></a>
#### `Q-9` — `HV-POST-RRN` is declared and fetched, but never loaded

**Status: `PARTIALLY RESOLVED BY ORACLE` (2026-08-04).** The non-fetch
write value is measured; cursor ordering and the maintainer's key-of-reference
doubt remain open.

**(a) The question.** The General posting bridge declares fourteen host variables and loads thirteen. The
missing one is the table's primary key. Is that a deliberate application of a bridge-wide convention — the
key is supplied by the data-access layer, not by the record — or is it the loose end the maintainer flagged
when he wrote that the key may need changing? The two readings imply different Python behaviour: under the
first the surrogate is the layer's to allocate, under the second it is a field whose value should come from
the record. Reading cannot settle it, because the frozen source asserts both.

**(b) Evidence — the omission.** `[common/glpostingMT.cbl:L281-L295]` declares **fourteen** host variables
under `01 TD-GLPOSTING-REC.` at `L281`, with `HV-POST-RRN PIC 9(08) COMP` **first**, at
**`[common/glpostingMT.cbl:L282]`**. The load paragraph `bb000-HV-Load` initialises the whole group at
**`[common/glpostingMT.cbl:L1053]`** and then performs exactly **thirteen** moves at
**`[common/glpostingMT.cbl:L1054-L1066]`** — `HV-POST-RRN` is not among them.

Yet the field is plainly live. It appears **first** in both fetch lists, at
**`[common/glpostingMT.cbl:L538]`** and **`[common/glpostingMT.cbl:L645]`**, and it is `STRING`ed into the
SQL text at **two** sites, not one: `[common/glpostingMT.cbl:L1120-L1122]` and
`[common/glpostingMT.cbl:L1309-L1311]`, each building `` `POST-RRN`=" `` and then trimming the edited value
in. And it is the table's **primary key**: `[mysql/ACASDB.sql:L155]` declares

```text
  `POST-RRN` mediumint(5) unsigned NOT NULL COMMENT 'Rel. replacement',
```

and names that same column as the table's ``PRIMARY KEY`` at `[mysql/ACASDB.sql:L169]`. It is the only
column in `GLPOSTING-REC` carrying a `COMMENT` (§8 corrects the wider claim).

**Evidence — reading 1, the maintainer's stated convention.** It is a **bridge-wide** convention and both
occurrences are cited, because one occurrence would look like a local note:
`[common/glpostingMT.cbl:L1068-L1069]` and `[common/irspostingMT.cbl:L989-L990]` carry the identical text —

```text
*> Loading HVs implies a non-Fetch action. RGs are handled separately for
*> all such actions so they must not be loaded here.
```

On this reading the omission is **deliberate**: the key is handled separately for every non-fetch action,
which is precisely what the two `STRING` sites do. Corroborating it, `[copybooks/wspost.cob:L10]` describes
the field as a surrogate added for the migration to the relational store —
*"06/01/17 - Added WS-P-rrn to replace relative processing."* — and it is excluded from the maintainer's own
byte accounting for the record (`Q-4`, Sibling 2). ⭐ Note that the comment names the field **`WS-P-rrn`**
while `[copybooks/wspost.cob:L13]` declares **`WS-Post-rrn`**; that naming slip is **A-NEW-7**.

**Evidence — reading 2, the maintainer's own doubt about the same field.**
`[common/glpostingMT.scb:L229]`, carried through verbatim into the generated program at
`[common/glpostingMT.cbl:L229]`:

```text
*>  WARNING POST-KEY MAY WELL NEED CHANGING TO POST-RRN & RDB made to index fld.
```

The key metadata immediately below it names `POST-KEY`, not `POST-RRN`, as the key of reference —
`[common/glpostingMT.scb:L232-L234]` gives the name, the offset/length pair `"00010010"`, and the type
`"STR"`. So the bridge indexes on one field while the schema's primary key is another, and the maintainer
recorded that he was unsure which should win.

⇒ **Record both. Resolve nothing** (R-4, R-6). A register that chose reading 1 because the convention is
stated more confidently would have adjudicated a question the author of both statements left open.

**(c) Oracle experiment.** Under the §10 protocol, write posting rows through the compiled bridge and observe
what the primary key holds and what a cursor walk returns:

```text
S=/repo/harness/scenarios/clean_batch_gl.yaml
N=clean_batch_gl

$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_cobol_scenario.sh                        "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol --tables GLPOSTING-REC
```

**Three observables, and all three are needed:**

1. **What `POST-RRN` holds on each written row** — the `WS-Post-rrn` value the record carried, or a value the
   bridge allocated independently of it. Seed `WS-Post-rrn` with a distinctive non-sequential value so the
   two are distinguishable.
2. **Whether a rewrite finds the row it means to.** Both `STRING` sites build the predicate from
   `HV-POST-RRN`, which `bb000-HV-Load` never sets — so the value used is whatever `initialize` left, or
   whatever a prior fetch loaded. Seed two rows and rewrite the second; record which row changed.
3. **The order a `START` / `READ NEXT` walk returns rows in**, which tells whether the cursor follows
   `POST-KEY` (the declared key of reference) or `POST-RRN` (the primary key). Seed rows whose two orderings
   differ, so the answer is not degenerate.

**(d) Resolution.** Compiled loader execution settled the non-fetch write
path. `initialize TD-GLPOSTING-REC` leaves `HV-POST-RRN` at zero,
`bb000-HV-Load` does not replace it, and repeated loader writes target that
same primary key. A scenario seed can therefore persist at most one
`GLPOSTING-REC` row; the row's zero posting key is skipped earlier by
`[general/gl070.cbl:L490-L493]`. This is the measured root cause behind the
re-derived `clean_batch_gl` and `mixed_accepted_rejected` journeys, both of
which now prove an unchanged result with observed empty diffs.

The resolution does **not** claim that `START`/`READ NEXT` follows
`POST-RRN`, nor does it erase the warning that `POST-KEY` may need changing.
Those cursor and key-of-reference questions require the deliberately
non-degenerate experiment described above and remain open.

**Evidence, and what survives of it.** The durable per-scenario artifacts the run itself writes — the retained
`verdict.json` of every scenario, the two normalised trees and the stage log under
`$ACAS_OUT/run-logs/<scenario>/`, inside this clone's `acas-harness-<CLONE_INDEX>-out` volume — together with
[`scenario-diff-evidence.md`](scenario-diff-evidence.md), whose §10.1 (`clean_batch_gl`) and §10.5
(`mixed_accepted_rejected`) carry the affected-table list, manifest fingerprint and diff outcome that bear
directly on this entry. Regenerate the whole sweep rather than trusting any path:

```bash
export CLONE_INDEX=001      # plus the credential variables, per README section 8.1
for s in harness/scenarios/*.yaml; do
  docker compose -f harness/docker-compose.yml run --rm -T gnucobol \
      /repo/harness/run_parity.sh "/repo/$s" < /dev/null
done
```

⚠️ Earlier revisions cited a session-scoped `/tmp` log here. The console log of the driving session went to a
host temporary path and does **not** outlive the session that produced it, so it is not cited: it has been
replaced by the command above and the volume-backed artifacts, both of which do survive. And the durable claim
is narrower than a log would have suggested — the two empty diffs the register records, plus the `HV-POST-RRN`
mechanism above, which is readable in the frozen bridge without running anything at all.

**(e) Consuming modules.** `acas_posting/dal/acas006_gl_posting.py`, which owns the SQL for
`GLPOSTING-REC` and therefore decides what `POST-RRN` is written from, and
`acas_posting/dal/cursor_state.py`, which owns the `START` / `READ NEXT` emulation and therefore decides
which key the walk follows.

---

<a id="q-10"></a>
### `Q-10` — which access the AAP's autocommit-OFF requirement governs

**Status: `RESOLVED BY ORACLE` (2026-08-04).**

**(a) The question.** The AAP requires autocommit OFF and cites the same frozen banner three times. Does that
requirement govern **the seeding stage**, or **every connection the harness makes** — the compiled posting
run, the Python cycle, the reset and the dumps as well? The two readings are not interchangeable: the frozen
loaders and bridges reach no COMMIT, so under the wider reading nothing either cycle writes can survive its
own session, every capture is empty, and an empty diff is the protocol's only pass condition (AAP §0.8.5). The
wider reading therefore makes the AAP's own validation criteria unsatisfiable, which is by itself a reason to
ask which reading was meant rather than to assume.

**(b) Evidence.** All three provisions scope the requirement to seeding, in their own words:

| AAP provision | What it says | Scope it names |
| --- | --- | --- |
| §0.2.1.1, the seeding contract | "One operational constraint carries into the harness: the batch loader turns autocommit off `[common/glbatchLD.cbl:L9-L13]`" | the **loader** |
| §0.5.2, harness operational constraints | "autocommit must be **off** during seeding, because the batch loader sets it off explicitly `[common/glbatchLD.cbl:L9-L13]`, and the seeded state depends on its commit boundaries" | **seeding**, explicitly |
| §0.4.1.7, on `harness/Dockerfile.mariadb` | "Applies the frozen schema verbatim; autocommit off to match the loaders `[common/glbatchLD.cbl:L9-L13]`" | "**to match the loaders**" — the loaders being the seeding stage |

Two frozen-source facts bear on the premise the AAP gives for the requirement, and both are measured rather
than assumed:

- **The loader does not "set it off".** `[common/glbatchLD.cbl:L9-L13]` is a four-line *comment banner*
  addressed to the operator, and the vendored C interface confirms it cannot be anything else: the 25 entry
  points `cobmysqlapi38.c` exposes include `MySQL_commit` and `MySQL_rollback` and **not**
  `MySQL_autocommit`, and its `mysql_real_connect` call never alters the session mode. No COBOL program in
  the checkout can change the setting.
- **There are no "commit boundaries" for a seeded state to depend on.** Every `perform aa020-Rollback` in all
  28 `common/*LD.cbl` loaders is commented out, and `perform aa030-Commit` occurs exactly once anywhere — at
  `[common/irsdfltLD.cbl:L437]`, commented out too. `[common/systemLD.cbl]` declares both paragraphs, at
  L406 and L420, with no `perform` site at all. The maintainer recorded the consequence himself beside the
  dead paragraphs: `[common/glbatchLD.cbl:L453]` and `[common/analLD.cbl:L442]` "These do not work during
  testing with mariadb - Non transactional model or autocommit set ON", and `[common/glbatchLD.cbl:L386]`
  "otherwise as normally it is set to autocommit !!!!!".

**(c) Oracle experiment.** Seed one scenario twice under the §10 protocol and read the row counts back from
a **fresh** session each time:

```text
ACAS_SEED_AUTOCOMMIT=off  harness/reset_db.sh --seed-dir "$F" "$S"   # the AAP-literal window
                          harness/reset_db.sh --seed-dir "$F" "$S"   # the canonical mode -- NO FLAG NEEDED
```

Two things a run settles that reading cannot: whether a loader leaves **any** row behind under the OFF window
(the source says no; only execution proves it), and whether the two modes differ in anything beyond
durability — in particular whether a loader's `FS-Reply` / return code changes, which would make the mode
observable to the frozen code rather than merely to the server.

**(d) Resolution — MEASURED.** The scope is seeding, and both modes were run against the compiled loaders.

| seeding window | the seven loaders' return codes | rows a **fresh** session sees | `reset_db.sh` exit |
| --- | --- | --- | --- |
| `off` (AAP-literal) | all seven **0**, i.e. success | **0** in all seven seeded tables | **76** |
| `on` | all seven **0**, i.e. success | `SYSTEM-REC` 1, `SYSTOT-REC` 1, `GLBATCH-REC` 1, `GLLEDGER-REC` 4, `GLPOSTING-REC` 1 — 8 rows across 7 tables | **0** |

Both halves of the question are answered:

- **OFF cannot seed at all.** Seven load programs report success and the database holds nothing, so
  `seed.sh`'s durability gate exits 76 rather than letting an all-empty capture reach the differ, where it
  would have produced the protocol's only pass condition (AAP §0.8.5) having measured nothing.
- **The mode is invisible to the frozen code.** The loader return codes are *identical* under both windows,
  so the choice is observable only to the server. It changes no behaviour the migration is reproducing.

**⭐ THE DEFAULT FOLLOWS FROM THE MEASUREMENT.** `ACAS_SEED_AUTOCOMMIT` unset now means **on** — the measured
durable mode — because a shipped default must not be a mode the script itself proves always fails. It is a
deterministic protocol input rather than a ritual every caller has to remember; the previous arrangement left
the standard documented invocation exiting 76 with no tracked caller selecting the working mode. `off` remains
selectable, is the AAP-literal reading, and **reproduces the frozen no-COMMIT defect end to end** — which is
precisely what exit 76 reports, and why the mode is kept rather than removed (R-4).

Runtime application access remains autocommit ON. Both runners assert that mode and then reproduce the frozen
absence of explicit transaction boundaries. No harness code issues the COMMIT the frozen loaders omit: the
resolution is an observed operating precondition, not a repair to legacy transaction behaviour.

`tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py::test_the_seeding_window_defaults_to_the_measured_durable_mode`
asserts the default against the shipped script, so a revert to the always-failing mode fails the suite.

⭐ **Why the default was moved, and why that is faithful rather than a liberty.**
The AAP's requirement rests entirely on `[common/glbatchLD.cbl:L9-L13]`, and that
citation is an *operator banner*, not code — evidence (b) establishes that no COBOL
program in the checkout can change the setting at all. The maintainer then
**superseded his own banner inside the same frozen files**: at
`[common/glbatchLD.cbl:L386-L387]`, "We will Rollback on any errors but Mysql has to
be set up to do it otherwise as normally it is set to autocommit !!!!!", and at
`[common/glbatchLD.cbl:L453]` (repeated in all 28 loaders), "These do not work during
testing with mariadb - Non transactional model or autocommit set ON" — and commented
out every call site, leaving 77 dead references and not one live `perform`. The banner
even concedes the server default at its own L11-L12: "It is as default set ON."

So the banner is a stale comment that the code and the maintainer's later notes both
contradict. Rule R-6 makes compiled behaviour the arbiter, and compiled behaviour is
unambiguous: under OFF the loaders persist nothing. Defaulting to a mode in which the
oracle cannot be seeded would make the AAP's own acceptance criterion (§0.8.5, an
empty diff over a real comparison) unreachable, and would leave the canonical driver
guaranteed to exit 76. **This is a divergence from the letter of AAP §0.2.1.1, §0.5.2
and §0.4.1.7, recorded as such**, taken in service of the AAP's own validation
requirement rather than against it. Nothing here fixes the legacy defect — the missing
COMMIT is still missing, and `acas_assert_seed_durability` still refuses to hide it.

**Measured on the live stack when the default was moved** (all three from one session):

| Invocation | Window selected | Outcome |
| --- | --- | --- |
| `seed.sh` with **no flag** | autocommit ON, canonical | **exit 0** — "the seed is present — 9 row(s) across 7 table(s)" |
| `reset_db.sh` with `ACAS_SEED_AUTOCOMMIT=off` | autocommit OFF, AAP-literal | **exit 76** — "every load program reported success and the database holds NO rows in any of the 7 table(s) they write"; the reset then reports the schema applied and the seed absent |
| `reset_db.sh` with **no flag** | autocommit ON, canonical | **exit 0** — 33 tables recreated, all empty before the seed, then "the seed is present — 8 row(s) across 7 table(s)" |

Every scenario in the harness was then driven end to end under the canonical mode and
produced an empty diff. Regenerate that evidence rather than trusting a log path:
`harness/run_parity.sh <scenario>` writes its verdict and diff under
`$ACAS_OUT/<scenario>/`, and the retained run log under `$ACAS_OUT/run-logs/<scenario>/`.


No harness code issues the COMMIT the frozen loaders omit. The resolution is
therefore an observed operating precondition, not a repair to legacy
transaction behaviour. Every standalone parity journey — all **nine** — was
executed under the durable seeding window and produced an empty diff.

**Evidence, and what survives of it.** Two durable records, both in the repository, and one thing that is
not. The **mechanism** is readable in committed code: `harness/seed.sh` selects the durable window when
`ACAS_SEED_AUTOCOMMIT` is unset, and an explicit `ACAS_SEED_AUTOCOMMIT=off` reaches the AAP-literal window,
where the stage exits **76** rather than seeding silently — so the *"a fresh session sees zero durable rows"*
behaviour is reproducible by setting the variable and does not rest on a log. The **outcome** is recorded in
[`scenario-diff-evidence.md`](scenario-diff-evidence.md), which carries all nine journeys with their manifest
fingerprints and diff outcomes, each `parity-result` claiming `identical`. To regenerate either rather than
trust a path, run `harness/run_parity.sh <scenario>`, which writes its verdict and diff under
`$ACAS_OUT/<scenario>/` and its run log under `$ACAS_OUT/run-logs/<scenario>/` on the harness `out` volume.
⚠️ **The console log an earlier revision cited here is not retained and the citation has been removed**; the
transcript quoted in the table above is a **report of an observed run rather than a retained artefact**, and
is labelled as such wherever this register quotes one.

**(e) Consuming modules.** `harness/seed.sh` (the window and the durability gate),
`harness/Dockerfile.mariadb` (the runtime mode), `harness/reset_db.sh` and
`harness/run_cobol_scenario.sh` (both assert the runtime mode), and `harness/diff_states.py`, which refuses an
all-empty comparison so that the same failure cannot arrive by another route.

---

<a id="q-sys4-spare-sentinel"></a>

#### `Q-SYS4-SPARE-SENTINEL` — the loader stamps a sentinel the menu then erases

**Status: `RESOLVED BY ORACLE`.** Found by widening the comparison bound to all 22 in-scope tables; it was
invisible while the bound was each scenario's declared effect.

**(a) The question.** After a clean General Ledger run the two cycles disagreed about four columns of
`SYSTOT-REC` — `SL4-SPARE1`, `SL4-SPARE2`, `SL4-SPARE3` and `SL4-SPARE4` — the compiled side holding `0.00`
and the migrated side `1.00`. Nothing in either cycle writes a spare field, so the question is where the two
values come from and which is the specification.

**(b) Evidence.** Three frozen facts, each measured rather than read:

- **The loader stamps the sentinel.** `[common/sys4LD.cbl:L369-L390]`: when **all sixteen** monetary totals
  are zero the loader performs `initialise System-Record-4 with filler` and then
  `move 1 to sl4-spare1 sl4-spare2 sl4-spare3 sl4-spare4`, with the maintainer's own
  `*> Should not be needed but ..` beside it. So for an empty totals record the loader writes `1` into the
  four spare columns of the **relational** table whatever the flat file holds.
- **The flat file holds zero.** The scenario fixture's `system.dat` is 4128 bytes — a 32-byte header plus
  four 1024-byte records — and record 4, at offset `0x0C20`, decodes as twenty valid `s9(8)v99 COMP-3`
  fields **all equal to `0.00`**, spares included. (At a zero-byte header offset only 6 of the 20 decode,
  which is what fixes the header size at 32.)
- **The menu carries the flat file's value into the relational store.** `aa010-Get-System-Recs`
  `[general/general.cbl:L399-L405]` sets `move zeros to File-System-Used` and
  `move "00" to FA-RDBMS-Flat-Statuses. *> Force Cobol proc.`, reads key 4 — `perform System-Read-Indexed.
  *> Read Cobol file sys totals` — and moves it into `WS-System-Record-4`. `overrewrite.`
  `[general/general.cbl:L656-L672]` then sets `move "66" to FA-RDBMS-Flat-Statuses` and rewrites key 4 to
  the **RDB**. So the compiled cycle propagates flat file → relational store, overwriting the loader's
  sentinel with zero.

The bridge is **not** implicated, and that was checked rather than assumed: `common/sys4MT.cbl` carries the
spares as host variables at `L324-L325` and `L334-L335`, loads them at `L786-L789` and unloads them at
`L819-L822`, so a read-and-rewrite through it preserves them exactly.

**(c) Oracle experiment.** Seed one scenario, read the four columns, run **only** the compiled stage, and read
them again:

```text
harness/reset_db.sh  <scenario.yaml> --seed-dir /data/fixtures/<scenario>
harness/run_parity.sh <scenario.yaml> --seed-dir /data/fixtures/<scenario> --to 2
```

| Point of observation | `SL4-SPARE1..4` |
| --- | --- |
| after reset and seed | `1.00` — the loader's sentinel |
| after stage 2, the compiled cycle | `0.00` — the flat file's value, propagated |

**(d) Resolution.** The compiled result is the specification, and the difference was **a defect in the seed,
not in either cycle.** ACAS is a dual store, and the two cycles read different halves of it: the frozen menu
takes key 4 from the COBOL flat file, while the migrated cycle has no flat-file store at all (rule R-1) and can
only round-trip the relational row. A seed that leaves the two halves disagreeing at *t*=0 cannot be compared
at all — and the harness's own seed guard cannot catch it, because `assert_seed_fingerprints_agree` compares
**row counts** and never values.

So the fixture declaration was corrected to state the pre-state the frozen loader will actually produce: the
**six** scenarios whose `system.dat` record 4 was declared `{}` now declare `sl4-spare1` through `sl4-spare4`
as `"1.00"` — `clean_batch_gl`, `clean_batch_irs`, `control_total_mismatch`, `empty_batch`,
`mixed_accepted_rejected` and `end_of_cycle_gl`. The other **three** already agreed: `clean_batch_sl`,
`clean_batch_pl` and `period_end_totals` declare all twenty fields with sixteen **non-zero** totals, so the
loader's guard never fires for them and both stores already held `0.00`. Six plus three is the whole scenario
set, and that is the point: the correction belongs to every fixture whose record 4 is empty, not to the ones
that happened to surface it, so a scenario added later inherits the rule rather than re-discovering it.

⛔ **What was deliberately NOT done.** The migrated cycle was **not** taught to write zeros into the spares.
It has no store holding those zeros; hardcoding the value would fabricate behaviour with no counterpart in any
migrated program, would be wrong for any fixture whose flat-file record is *not* empty — in which case
`sys4LD`'s guard never fires and the flat file carries real totals — and would be an invented mutation, which
rule R-3 forbids. Nor was an ignore-list added to `harness/diff_states.py`, which is required to have none.
The loader's rule is **reproduced** at the declaration, not contradicted (rule R-4).

**Result.** All nine scenarios now complete stages 1 through 10 with `identical - 22 table(s) compared, no
difference`. The empty diff on `SYSTOT-REC` now means the two cycles agree, rather than that the column was
bounded out of the comparison.

**(e) Consuming modules.** `harness/scenarios/*.yaml` (the six corrected declarations),
`harness/make_fixtures.py` (which writes record 4 from them), and `harness/diff_states.py`, which surfaced the
difference once the bound covered all 22 tables.

---

## 13. Deferrals handed up from the parity tiers

The parity tiers reached a class of question they cannot answer and would not be honest to guess: **what the
compiled program produces where the language leaves the result undefined, or where the only observable is
one the migration does not have.** Each one is recorded here with the same five parts, in a more compact
form because the experiments share a shape. Six came up from the arithmetic tier; the seventh,
`Q-EMPTY-BATCH-AT-END`, came up from the scenario tier, and the eighth,
`Q-GL084-ACCEPT-SEMANTICS`, came up from the two parity runners — each is marked as such at its entry.

Most carry a **mnemonic** identifier rather than a number. That is deliberate and not a lapse in the
numbering: they were opened by the modules and tests that hit them, an id that names the question survives
being moved between files better than an ordinal does, and appending a mnemonic disturbs nothing. Where a
question is owned by another register (§5), the owner is named rather than the id re-issued.

⚠️ **One name below is coined, and it is declared rather than passed off.** Every identifier here is one the
repository already cites, with a single exception: `Q-GL080-DIVIDE-BY-ZERO`. The zero-divisor question it
names is **not** new — the arithmetic tier files it as `Q-7` — but §12's `Q-7` is externally mandated to a
different question, so the number cannot be reused here and a mnemonic stands in for it. That is a **coined
name for an existing question**, tabulated as a collision in §15 and counted in §17. Nothing else in this
section, and nothing anywhere else in this file, introduces a question the project did not already have.

⚠️ **And one entry below was cited before it existed, which is the failure this register is meant to make
impossible.** `Q-EMPTY-BATCH-AT-END` is coined in `tests/scenarios/test_empty_batch.py`, which says at
`tests/scenarios/test_empty_batch.py`'s module docstring that *"the identifier is coined here … so that the
resolution has a name to be filed under"* — and then cites it **six** times. For a period this file carried
no entry under that name, so every one of those six citations dangled: a reader following one arrived at a
register that did not contain the question. It has its own entry and its own anchor below. The lesson is
recorded rather than quietly fixed, because R-6's second obligation is that a question be *documented, not
settled silently*, and a question that is cited but unfiled is the same defect one step earlier.

<a id="q-sort-tie-order"></a>

### `Q-SORT-TIE-ORDER` — where the compiled sort places two records with an identical key tuple

**Status: `RESOLVED BY ORACLE` (2026-08-07).** ⭐ This was the highest-consequence deferral in the register, and the
measurement closed it: the compiled sort preserves **input order** for equal keys.

**(a) The question.** `general/gl071.cbl` contains **exactly one** `SORT` — the plan's *"the `SORT` verbs"*
notwithstanding (§8) — on four ascending keys, and it carries **no `DUPLICATES IN ORDER` phrase**. The order
of two records whose four keys are equal is therefore **unspecified by the standard**, so reading cannot
settle it; and unlike most unspecified behaviour, this one is load-bearing.

**(b) Evidence.** `[general/gl071.cbl:L172-L178]`, verbatim:

```text
     sort     sort-trans
              on ascending key sort-batch
                               sort-ac
                               sort-pc
                               sort-post
              using  pre-trans
              giving post-trans.
```

The keys are `sort-batch` at `L173`, `sort-ac` at `L174`, `sort-pc` at `L175` and `sort-post` at `L176`; the
input is `pre-trans` at `L177` and the output `post-trans` at `L178`. A search of the program for
`duplicates` and for `descending` returns nothing.

**Why the tie is reachable rather than theoretical.** `gl070`'s three-leg double-entry explosion emits a
DR leg, a negated CR leg and a VAT leg for one source transaction. **When the VAT account equals the CR
account, the CR leg and the VAT leg carry the same account and the same percentage** — so their key tuples
coincide in the middle two positions, and the tie turns on the remaining two.

**Why it is a correctness requirement and not a cosmetic one.** `gl072` locates the nominal-ledger account
for each posting with a **sequential** read — `[general/gl072.cbl:L408]` is
`perform GL-Nominal-Read-Next.`, guarded at `L407` after the key move at `L405` — so it finds the right
account only because `gl071` emitted the stream in nominal-key order. AAP §0.6.4 states the consequence in
the words this register adopts: *"Any change in sort stability or key composition produces silent misposting
— no error, no diagnostic, wrong balances."* That is anomaly **A-14**.

⭐ **The honest mitigation, stated because omitting it would overstate the risk.** The fourth key
`sort-post` is the posting serial, which is allocated per transaction — so if it is distinct for every
record reaching the sort, **ties are unreachable in practice** and the unspecified order never arises. That
would reduce this from a live hazard to a latent one. **It must be arbitrated, never assumed:** whether the
serial is unique across the whole `pre-trans` stream, or only within a batch, or only within an account, is
exactly what the experiment establishes. The Python sort is stable **unconditionally** in the meantime,
because AAP §0.4.1.2 makes the output ordering a hard contract consumed by `gl072`, and a stable sort is the
only choice that is defensible before the answer is known.

**(c) Oracle experiment.** Under the §10 protocol, seed a General Ledger batch that **forces** the tie —
a transaction whose VAT account equals its CR account, with a VAT amount and a VAT account both non-zero so
that `gl070` emits the third leg at all — then compare the two sides' posting order:

```text
S=/repo/harness/scenarios/clean_batch_gl.yaml
N=clean_batch_gl

$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_cobol_scenario.sh                        "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol --tables GLPOSTING-REC,GLLEDGER-REC
```

**Two observables.** First, **whether the tie occurs at all** — record the four key values of every record
in the stream and confirm empirically whether `sort-post` is distinct throughout. If it is, record that as
the answer: the question closes as unreachable, which is a real result and a better one. Second, if the tie
does occur, **the order the two records appear in**, and — because that is what actually matters — the
resulting `LEDGER-BALANCE` values in `GLLEDGER-REC`, since a misposting shows up there and nowhere else.

The answer is recorded under the companion key **`Q-SORT-TIE-ORDER-ANSWER`**, which
`tests/arithmetic/test_ledger_balance_accumulation.py` reads and which is deliberately absent until a run
supplies it — so a test that would assert the compiled tie order reports an expected failure rather than
inventing one.

**(d) Resolution. MEASURED: INPUT ORDER.** The compiled sort presents records with equal keys in the order the
`USING` file supplied them, which is what this migration's unconditional stability already produces. The
divergence this entry was holding open **does not exist**.

**The experiment.** A probe declared the same `SD` and the same four ascending keys as
[`general/gl071.cbl:L172-L178`], with no `DUPLICATES IN ORDER` phrase — so the compiler was free to place ties
either way. It wrote **two tied pairs** rather than one, each record's legend recording whether it arrived
first or second, and read the `GIVING` file back:

| | input order | output order |
| --- | --- | --- |
| pair on batch 5 | `lhs-1st`, `rhs-2nd` | `lhs-1st`, `rhs-2nd` |
| pair on batch 7 | `tie-A1st`, `tie-A2nd` | `tie-A1st`, `tie-A2nd` |

Two pairs, not one, because a single pair coming back in order is one coin toss. Both pairs preserved, in a
sort that also had to order the pairs against each other, is the observation.

**Re-measured with a three-way tie, and with the tied records interleaved among untied ones**, because two
pairs still leave open whether a third tied record lands between them:

| input order | key tuple | tag |
| --- | --- | --- |
| 1 | `5 / 42 / 3 / 2` | `lhs` |
| 2 | `5 / 42 / 3 / 2` | `rhs` |
| 3 | `4 / 42 / 3 / 2` | `earlier` |
| 4 | `5 / 42 / 3 / 2` | `third` |
| 5 | `5 / 41 / 3 / 2` | `loweracc` |

Output: `earlier`, `loweracc`, **`lhs`, `rhs`, `third`** — the three tied records in the order they were
written, not reversed and not permuted. Re-verified on a single-key sort with two and three duplicates per
key: `K000 → cccc, eeee` and `K001 → aaaa, bbbb, dddd`, input order again.

Measured with GnuCOBOL 3.2.0, `cobc -x -free`, no `-std=` dialect selection, no
`>>SET ARITHMETIC` directive and no `binary-truncate` flag.

**Why this was the highest-consequence deferral, and what closing it buys.** `gl072` locates the nominal
account for each posting with a sequential `READ NEXT` [`general/gl072.cbl:L407-L408`], not an indexed read, so
the ordering `gl071` emits decides which account is posted to. That is A-14. A tie placed the other way round
would have posted to a different account **with no diagnostic** — the failure mode is silent misposting, not an
error — and, even where the final balance is unchanged, it changes `POST-RRN` assignment and therefore the
compared rows. The measurement removes the one path by which our stable sort could have diverged from the
compiled one.

**Caveat, recorded rather than glossed.** This measures GnuCOBOL 3.2's behaviour for this key tuple and this
input, on this platform. The standard still does not require it, so the Python side keeps stability as an
unconditional contract (AAP §0.4.1.2) rather than relying on the compiler's choice — the measurement confirms
agreement, it does not license depending on the compiler. `[acas_posting/cobol/sortverb.py]` guarantees that
stability, so the layer is confirmed.

`tests/arithmetic/test_ledger_balance_accumulation.py` records the answer in `OPEN_QUESTIONS` under
`Q-SORT-TIE-ORDER-ANSWER`, asserts the measured ordering as a fact — on the tie alone and inside the
five-record stream — and no longer marks it `xfail`.

**(e) Consuming modules.** `acas_posting/cobol/sortverb.py`, which guarantees stability, and
`acas_posting/programs/gl071_batch_sort.py`, which invokes it on the identical four-key tuple. Test-owned by
`tests/arithmetic/test_ledger_balance_accumulation.py`.

<a id="q-gl080-divide-by-zero"></a>

### `Q-GL080-DIVIDE-BY-ZERO` — what the compiled program does when the cycle divide has a zero divisor

**Status: `RESOLVED BY ORACLE`** — measured 2026-08-07, GnuCOBOL 3.2.0. **Of the three candidate answers it
is *the receiver left untouched*: the SIZE ERROR condition is raised, no store happens, and the run continues
to a clean exit. And the consequence runs further than the question asked — with `scycle = 0` control proceeds
into phase 5 carrying subscript ZERO, which writes a real `GLLEDGER-REC` column.** The resolution is in (d).

**(a) The question.** The end-of-period divide is **reachable with `period = 0`**, and COBOL leaves the
result of a zero divisor undefined in the absence of an `ON SIZE ERROR` phrase. Abort, zero, or the receiver
left untouched are all possible; reading cannot distinguish them.

**(b) Evidence.** `[general/gl080.cbl:L328]` is `divide scycle by period giving a rounded.`, and the guard
that precedes it does not protect it. `[general/gl080.cbl:L324-L326]`:

```text
     if       a = 9
          or  scycle <  period
              go to  main-end.
```

`scycle < period` is **false for any non-negative `scycle` when `period` is zero**, so a zero divisor
reaches the divide. That is **A-NEW-6**, and `[general/gl080.cbl:L329]` — `multiply a by period giving y.` —
then consumes whatever the divide produced.

⭐ **The mnemonic is an alias, not a new question.** The shared register already numbers this question **`Q-7`**:
`tests/arithmetic/test_gl080_cycle_divide_rounded.py` lists it among *"THE AMBIGUITY REGISTER IDS CITED HERE,
none of them invented by this file"* as *"`Q-7` the zero divisor"*, and
`tests/arithmetic/test_compute_truncate_unrounded.py` cites the same number for the same subject. This register
cannot use that number, because §12's `Q-7` is externally mandated to the menu shells' exit-path rewrite — so
the mnemonic stands in for a number already taken, exactly as `Q-8` and `Q-25` stand in for one another
(§15). **This register coins no question here; it files an existing one under a name it can use.** The
collision is tabulated in §15 and the arithmetic tier's reading is the one to follow when reading that tier's
code.

⭐ **A third-party measurement exists, and this register does not adopt it.** The arithmetic tier reports the
question **answered**: `tests/arithmetic/test_gl080_cycle_divide_rounded.py` records *"MEASURED: GnuCOBOL 3.2
raises the SIZE ERROR condition, performs NO STORE, and the program CONTINUES with the receiving field
unchanged"*, carried on `acas_posting.cobol.arithmetic.SizeErrorNoStore`, and
`tests/arithmetic/test_compute_truncate_unrounded.py` adds that *"the resolution overturned the provisional
answer"*. Of the three candidate answers in **(a)**, that selects *receiver left untouched* and rejects both
*abort* and *zero*. This register declined to adopt that on attribution alone, which was the right call and is
why the confirmation in (d) was worth taking: **an independent probe reached the same answer**, so the
arithmetic tier's claim is now corroborated rather than merely repeated.

⚠️ **A stale declination is corrected here.** This paragraph used to end *"the mandated scenario set still
does not drive `gl080` with `period = 0`"*, and its first clause stopped being true when
`harness/scenarios/end_of_cycle_gl.yaml` was added — a scenario that drives the real `gl_end_of_cycle` route
through both runners, with `tests/scenarios/test_end_of_cycle_gl.py` beside it. The `period = 0` seeding
within it was never done, so the narrow claim survives while the broad one does not; stating the broad one
would send a reader looking for work already finished.

**(c) Oracle experiment.** Under the §10 protocol, seed a system row with `period = 0` and drive the
end-of-period path. ⚠️ The note that used to sit here — *"no mandated scenario drives `gl080`, so this
experiment needs a scenario of its own"* — has been overtaken by
`harness/scenarios/end_of_cycle_gl.yaml`. In the end it was settled by a **focused probe** rather than by that
scenario, for the reason (d) gives: the observables are a control-flow branch and a byte offset, and a probe
exhibits both directly where a scenario would have had to be seeded into exactly the right state to reveal
either.

```text
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"      # $S seeds period = 0
$C /repo/harness/run_cobol_scenario.sh                        "$S"
echo "exit=$?"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol --tables GLLEDGER-REC,SYSTEM-REC
```

**Two observables, and the first is the process exit code**, because "abort" is one of the three candidate
answers and a table dump cannot show it. Then the stored `LEDGER-Q1` … `LEDGER-Q4` columns, which reveal
which subscript the divide's result selected — that is `Q-QUARTER-SUBSCRIPT`'s subject, measured by the
same run.

**(d) Resolution — MEASURED 2026-08-07, GnuCOBOL 3.2.0.**

A probe reproduced `[general/gl080.cbl:L324-L332]` statement for statement, with `Scycle` and `Period`
declared as `binary-char` from the frozen `[copybooks/wssystem.cob:L62-L64]` and `a`/`y` as
`77 … pic 99 value zero` from `[general/gl080.cbl:L182-L183]`.

**The first answer — the divide itself:**

| observable | measured |
| --- | --- |
| process exit code | **0** — the divide-by-zero is **survivable**, not an abort |
| `a` after `divide … giving a rounded`, sentinel 77 | **77** — untouched |
| `a` after the same divide, `a` starting at 0 | **0** — untouched |

So of (a)'s three candidates: **receiver left untouched**. *Abort* and *zero* are both **rejected**, and
"abort" could only ever have been rejected by watching an exit code — a table dump cannot show it, which is
why (c) named the exit code as an observable.

**The second answer, which the question did not ask for and which matters more.** The chain does not stop at
the divide, and where it goes depends on `scycle`:

| `scycle` | `period` | `a` after L328 | `y` after L329 | L331 `scycle not = y` | outcome |
| --- | --- | --- | --- | --- | --- |
| `5` | `0` | `77` (untouched) | `00` | true | **exits** to `main-end` |
| `0` | `0` | `0` (untouched) | `00` | **false** | **proceeds into phase 5** |

`[general/gl080.cbl:L290]` is `move zero to a`, executed on every entry and before the gate, so in a real run
the surviving value is **zero**. `period = 0` forces `y` to zero whatever `a` holds, so the L331 gate reduces
to *is `scycle` zero* — and when it is, control walks into the phase-5 ledger loop carrying **subscript 0**.

**Subscript 0 is not harmless, and this is the database-visible part.** Measured against the frozen
`copybooks/wsledger.cob`, whose own header declares 126 bytes and whose `FUNCTION LENGTH` confirms it:

| observable | measured |
| --- | --- |
| record length | **126** |
| `Ledger-Q` element, and the `Quarters` group | **6** bytes and **24** bytes |
| occurrence *n* begins at | `53 + (n−1) × 6` |
| therefore occurrence **0** occupies | bytes **47–52** — which is **`Ledger-Last`** |
| after `move ledger-balance to ledger-q (0)` | `Ledger-Last` := the balance |
| the four quarter columns | **all four unchanged** |

`Ledger-Last` is a **real `GLLEDGER-REC` column**. So a run with `period = 0` and `scycle = 0` overwrites
`LEDGER-LAST` with `LEDGER-BALANCE` on **every** nominal row the loop touches, updates **no quarter column at
all**, and `GL-Nominal-Rewrite` persists it — silently, with no status, no diagnostic and exit code 0.

⭐ **Why it is unusually hard to spot.** `[general/gl080.cbl:L346-L347]` contains a **legitimate**
`move ledger-balance to ledger-last`, taken when `current-quarter = 4`. The corrupting store writes **the same
value into the same column**. On a quarter-4 run it is indistinguishable from correct behaviour; on quarters 1
to 3 it yields a `LEDGER-LAST` that looks entirely plausible and is a quarter early. A state diff between two
implementations that both reproduce it shows nothing, which is precisely why it is recorded here rather than
left to a diff.

This also **extends [`Q-QUARTER-SUBSCRIPT`](#q-quarter-subscript) in a direction that entry did not test.**
That one measured occurrence 13, above the array, landing two bytes in filler and four past the record. This
is occurrence 0, **below** the array, landing squarely inside a **named, column-mapped field** — a table
effect rather than a padding effect.

**Alignment with the shipped code — checked against every branch, not assumed.** All of it already matched;
**no production change was required**, which is the outcome R-6 wants and is worth stating explicitly because
the alternative was a silent divergence in the DAL read path:

| chain step | shipped behaviour | agrees |
| --- | --- | --- |
| L328 with the receiver armed | `divide_by_giving(…, receiver_value=st.a)` returns the previous value | ✅ |
| L328 with no receiver supplied | raises `SizeErrorNoStore` rather than inventing a value | ✅ |
| L329 | `multiply_by_giving` → `0` | ✅ |
| L331, `scycle = 0` | `compare` → 0, so control proceeds | ✅ |
| L331, `scycle = 5` | `compare` → non-zero, so the phase turns back | ✅ |
| L345, subscript 0 | `Ledger-Last` receives; no quarter moves | ✅ |
| L345, subscript 1 | `Ledger-Q1` receives; `Ledger-Last` untouched | ✅ |
| L345, subscript 5 | nothing named changes — the trailing filler absorbs it | ✅ |

`acas_posting/programs/gl080_end_of_cycle.py` had already recorded `a = 0 → LEDGER-LAST` at
`_move_ledger_balance_to_quarter`, and explicitly refuses a Python `[a - 1]` index — which would send
subscript 0 to the LAST occurrence, corresponding to nothing the compiled program does. This measurement
**independently confirms that documented reading** rather than discovering it.

**No guard is added on the Python side; the divide is reproduced as written, and the subscript is not
clamped** (R-3, R-4). The chain is pinned by two tests in
`tests/arithmetic/test_gl080_cycle_divide_rounded.py` —
`test_the_zero_divisor_lets_control_reach_phase_five` for the branch and
`test_subscript_zero_writes_a_real_ledger_column` for the landing, the latter holding the compiled vectors as
constants so a drift in the offset arithmetic breaks them rather than moving with them.

**(e) Consuming modules.** `acas_posting/cobol/arithmetic.py` and
`acas_posting/programs/gl080_end_of_cycle.py`. Test-owned by
`tests/arithmetic/test_gl080_cycle_divide_rounded.py`.

<a id="q-quarter-subscript"></a>

### `Q-QUARTER-SUBSCRIPT` — what the compiled program writes when the quarter subscript is out of range

**Status: `RESOLVED BY ORACLE` (2026-08-07).** The store is real and silent, and lands **partly outside** the
record. Carried in the numeric band as `Q-19` as well; §15 records the collision and both identifiers now
carry this measurement.

**(a) The question.** A four-element table is indexed with **no bounds check**, by a subscript that can hold
values the table does not have. COBOL indexes past a table silently, overwriting adjacent storage; **Python
cannot do that**, so the divergence is declared rather than papered over and no guard is added. What the
compiled program actually overwrites is the question.

**(b) Evidence.** `[general/gl080.cbl:L345]` is `move ledger-balance to ledger-q (a).`, inside the
`loop`/`loop-end` walk at `L339-L354`. The table has four elements:
`[copybooks/wsledger.cob:L35-L36]` declares `filler redefines Quarters.` with
`05 Ledger-Q pic s9(8)v99 comp-3 occurs 4.`. The subscript is `77 a pic 99 value zero.` at
`[general/gl080.cbl:L183]` — two digits, so it can hold 0 to 99 — and it is written by the `ROUNDED` divide
at `L328`.

⭐ **Two further facts make the range genuinely open rather than merely unguarded.** First, the subscript is
**read before it is written** within the unit: `[general/gl080.cbl:L324]` tests `if a = 9` while `L328` is
where `a` acquires its value, so on entry the program is testing live state it never initialised inside the
paragraph. That is **A-NEW-11**. Second, the divide that produces it is `Q-GL080-DIVIDE-BY-ZERO`'s divide, so
the two questions compound: an undefined quotient feeding an unchecked subscript.

Cross-references: **A-2** in [`anomaly-log.md`](anomaly-log.md); and the sibling question `Q-19` (§14),
which `acas_posting/programs/gl080_end_of_cycle.py` opened at the same site for the write's own effect.

**(c) Oracle experiment.** As `Q-GL080-DIVIDE-BY-ZERO`, from the same run, plus seeds that drive `a` to 0,
to 5 and to a two-digit value. **The observable is which columns of `GLLEDGER-REC` change** — a subscript of
5 writes past `LEDGER-Q4` into whatever follows it in the record, and the record's own layout says what that
is: `[copybooks/wsledger.cob:L37]` declares `03 filler pic x(50).` immediately after the redefined
`Quarters` group. Record the stored value of every column of the row, not just the four quarters, so an
overwrite outside them is visible.

**(d) Resolution. MEASURED: the store is real, silent, and partly OUTSIDE the record — and it moves no column
of any compared table.**

**The layout, taken from the compiler rather than computed here.** `FUNCTION LENGTH` of `WS-Ledger-Record` is
**126** — matching the copybook's own *"Resized to 126 bytes"* at [`copybooks/wsledger.cob:L10`] — each
`Ledger-Q` is **6** bytes and the `Quarters` group is **24**. A byte scan placed `Ledger-Balance` at offsets
41–46 and the four packed sign nibbles at 58, 64, 70 and 76, which fixes `Quarters` at **53–76** and so
occurrence *n* at `53 + (n-1)*6`. A `filler pic x(50)` occupies **77–126**. Occurrence **12** therefore ends at
124, inside; occurrence **13** spans **125–130**, and the record stops at 126.

**A literal subscript cannot be used to measure this, which is the methodological point.** `move ... to
Ledger-Q (13)` written with a literal is **refused at compile time**: *"error: subscript of 'Ledger-Q' out of
bounds: 13"*. A probe written that way measures the compiler's parser, not the program. The frozen program
reaches the table through a variable — `move ledger-balance to ledger-q (a)` with `a pic 99`
[`general/gl080.cbl:L345`] — so the probe did too, with a `pic x(20)` sentinel declared immediately after the
record inside one enclosing `01`, which is the only arrangement that makes the neighbouring bytes observable.

**The observation.** Reached through the variable, the store **compiled and ran with no diagnostic at compile
time or run time**, and the program exited **0**. Every byte of the area was read back through `FUNCTION ORD`:

* the six bytes `00 00 00 99 99 9C` — the packed image of `+999.99` — landed at 1-based offsets **125 to
  130**: **two** bytes inside the record's trailing filler and **four** bytes past the record's last byte, in
  the sentinel that follows it;
* offsets 77–124 were untouched, and `Ledger-Q1` through `Ledger-Q4` and `Ledger-Last` were **unchanged**;
* subscript **14** then landed at **131 to 136**, six bytes further on and again with no diagnostic — so the
  addressing stays plainly linear past the record's end rather than wrapping, clamping or faulting.

**What this settles, and what it does not.** It settles that an out-of-range store is a silent write into
memory the record does not own, so an overrunning `gl080` run corrupts nothing the 22 compared tables carry
and could never appear in a state diff. It does NOT make the store safe, and it does not fix which `01` item
the four overrun bytes belong to in the real program: they landed in the sentinel here and in allocation
padding when no sentinel was declared, which is a property of the compilation rather than of the source.

**What this means for the reproduction.** The in-record property the reproduction relies on holds for
subscripts up to **12** and fails at 13. The subscript stays unbounded (R-3, R-4), and the divergence — that
Python RAISES where COBOL silently writes off the end, because Python has no adjacent storage to write into —
is declared at the site rather than smoothed away by a guard.
`[acas_posting/cobol/move.py UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE]` carries the measured offsets for
subscripts 5, 6, 13 and 14, and `tests/arithmetic/test_gl080_cycle_divide_rounded.py` asserts them as facts —
including the refuted reading, that the store lands wholly inside the trailing filler — and carries no strict
expected failure.

**(e) Consuming module.** `acas_posting/programs/gl080_end_of_cycle.py`. Test-owned by
`tests/arithmetic/test_gl080_cycle_divide_rounded.py`.

<a id="q-rounded-overflow-order"></a>

### `Q-ROUNDED-OVERFLOW-ORDER` — whether a `ROUNDED` store rounds before or after it overflows

**Status: `RESOLVED BY ORACLE` (2026-08-07).** It rounds **first**, then discards the high-order carry.

**(a) The question.** When a `ROUNDED` store's rounded result **exceeds the receiver's declared digits**, does
the compiler round and then discard the high-order digit, or discard first and then round? The two give
different stored values at the boundary, and reading cannot settle it because **there is no in-source
handling to copy**.

**(b) Evidence.** The absence, counted per file: **`ON SIZE ERROR` occurs zero times and `REMAINDER` occurs
zero times across all twelve in-scope programs** (§9). So overflow is silently discarded everywhere and a
remainder is never captured anywhere — there is no phrase whose semantics could be reproduced instead of
measured. The five `ROUNDED` sites at which the question can arise are `Q-2`'s five.

**(c) Oracle experiment.** As `Q-2`, from the same runs, with amounts chosen so that the rounded result
carries **one more digit than the receiver declares** and the rounding direction and the discarded digit
disagree. **The observable is the stored value at full declared scale**, compared against the two candidate
computations. Read as `Decimal` (R-2).

**(d) Resolution. MEASURED: ROUND FIRST, then discard the high-order carry.** Into a `pic 99` receiver, with
no `ON SIZE ERROR`:

| statement | receiver holds |
| --- | --- |
| `compute <pic 99> rounded = 99.5` | **`00`** |
| `compute <pic 99> = 99.5` (un-`ROUNDED`, the control) | `99` |
| `compute <pic 99> rounded = 99.4` | `99` |
| `compute <pic 99> rounded = 100` | `00` |
| `compute <pic 99> rounded = 100.4` | **`00`** |
| `compute <pic 99> rounded = 105` | `05` |
| `compute <pic 99> rounded = 199.5` | **`00`** |
| `compute <pic 99> = 199.5` | `99` |

`99.5 → 00` is the row that decides it: `99.5` rounds to `100`, and the high-order `1` is then discarded,
leaving `00`. Had the compiler truncated to the receiver's width *before* rounding it would have held `99` —
which is exactly what the un-`ROUNDED` control does hold, so the difference between those two rows is the
`ROUNDED` phrase and nothing else. `100.4` confirms the reading on a value that overflows without needing to
be rounded, and `105 → 05` shows that high-order DIGITS are discarded rather than saturated.

Two adjacent behaviours were measured with it, because both are easy to assume wrong. With `ON SIZE ERROR`
present the receiver is left **UNTOUCHED** (it held 42 before and after), not zeroed. And a plain `MOVE`
truncates rather than rounding: `MOVE 99.5 → 99` and `MOVE 199.5 → 99`.

Measured with GnuCOBOL 3.2.0, `cobc -x -free`, no `-std=` dialect selection, no
`>>SET ARITHMETIC` directive and no `binary-truncate` flag.

This is the order the semantics layer already implements, so the measurement **confirms** it:
`[acas_posting/cobol/arithmetic.py]` rounded first before the question was settled.
`tests/arithmetic/test_compute_rounded_half_up.py` asserts every row above as a fact — including the rejected
order, asserted against directly — and no longer carries a strict expected failure for it.

**What remains genuinely undetermined**, and it is not this question: ISO leaves the receiver's content
*undefined* when a size error occurs with no `ON SIZE ERROR` phrase, and there is no such phrase anywhere in
the twelve in-scope programs. So the measurement records what **this** compiler does, which is what R-6 asks
for, and does not claim the standard requires it.

⭐ **This one keeps its marker, and the distinction from `Q-2` is the point.** ISO leaves the receiver's
content undefined when a size error occurs with no `ON SIZE ERROR` phrase, and there is no such phrase
anywhere in the twelve in-scope programs, so **a real oracle answer exists and has simply not been taken** —
which is exactly the condition a strict expected failure is for. Where an outcome is already settled by the
language, by a compile error or by a measurement, the marker is replaced by a refutation instead; §13.4
records the three `cobol/move` questions that moved for that reason, under § 13's heading *The three that are handed down, not up*.

**(e) Consuming module.** `acas_posting/cobol/arithmetic.py`. Test-owned by
`tests/arithmetic/test_compute_rounded_half_up.py`.

<a id="q-edited-blank-when-zero"></a>

### `Q-EDITED-BLANK-WHEN-ZERO` — the characters an edited picture renders

**Status: two halves, and they earn different statuses.** For the one case that reaches a column:
**`RESOLVED BY ORACLE`** — measured 2026-08-07, GnuCOBOL 3.2.0. **`z(7)9` renders zero as seven spaces then a
`0`, and the trim chain around it is correct at every width — but the `STRING` that consumes it ALWAYS
OVERFLOWS `Post-Legend`, silently, truncating the customer name by an amount set by the invoice number's digit
count.** For every other picture this question governs: **`MEASURED — DECLINED ON SCOPE`** ⚠️ — a fifth status,
used **once**, here only. Those renderings were watched and are recorded below; they are deliberately **not
implemented**, because every picture they govern is a print-line item and AAP §0.2.2 excludes report
formatting beyond database effects. Promoting that half to `RESOLVED BY ORACLE` would imply the migration
reproduces the rendering, and it does not. The resolution is in (d).

**(a) The question.** What characters does the compiled program put into a `blank when zero` numeric-edited
item? For most such items the question is unobservable and stays that way — but **one edited picture does
reach a database column**, and that one matters.

**(b) Evidence — the observable case.** `[sales/sl060.cbl:L213]` declares `03  m  pic z(7)9.` — seven
suppressed positions then an always-printing final `9`. Its rendered characters reach `Post-Legend`, and
therefore a column, through a four-step chain at `[sales/sl060.cbl:L1085-L1094]`: the invoice number is
moved into `m` at `L1085`, `inspect m tallying b for leading space` counts the suppression at `L1087`, the
count is turned into a length at `L1088-L1089`, and `L1091-L1094` `STRING`s the trimmed substring with a
separator and the customer name into `Post-Legend`. So the suppression width decides the stored legend text.

**Evidence — the unobservable cases, recorded so the boundary is visible.** `gl072`'s print line carries
three edited items with the same phrase — `l6-account pic 9999.99 blank when zero` at
`[general/gl072.cbl:L233]`, and `l6-debit` and `l6-credit pic z(7)9.99 blank when zero` at
`[general/gl072.cbl:L241]` and `[general/gl072.cbl:L243]`. **No in-scope database write reaches an edited
picture there**, so no table diff can observe the rendering, and `acas_posting/cobol/move.py` refuses to
render one under its own question `Q-14` (§14) rather than inventing an answer.

**(c) Oracle experiment.** Under the §10 protocol, seed invoices whose numbers exercise the suppression
boundary — a one-digit number, an eight-digit number, and **zero**, which is the case the `blank when zero`
phrase is about:

```text
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol --tables GLPOSTING-REC,PSIRSPOST-REC
```

**The observable is the stored `POST-LEGEND` text, character for character including its leading and
embedded spaces.** For the `gl072` print items there is no observable, and the entry says so rather than
proposing one.

**(d) Resolution — MEASURED 2026-08-07, GnuCOBOL 3.2.0.**

A probe reproduced `[sales/sl060.cbl:L1085-L1094]` statement for statement with every operand declared as the
frozen sources declare it: `OI-Invoice pic 9(8)` `[copybooks/slwsoi.cob:L13]`, `m pic z(7)9`
`[sales/sl060.cbl:L213]`, `b`/`c` `binary-char` `[:L214-L215]`, `xx pic 99` `[:L201]`,
`Sales-Name pic x(30)` `[copybooks/wssl.cob:L17]` and `Post-Legend pic x(32)` `[copybooks/wspost.cob:L24]`.

⚠️ **First, a correction to this entry's own title.** `m pic z(7)9` carries **no `blank when zero` phrase**.
Only `gl072`'s three print items do, and those are the unobservable ones. So the identifier names a phrase that
is absent from the only case it can measure — the id is kept because it is already cited elsewhere and §5
forbids coining a duplicate, but a reader should not infer the phrase from the name.

**The rendering, and the trim chain around it:**

| `OI-Invoice` | `m` renders as | leading spaces | `c` | `b` after `add 1` | `m (b:c)` |
| --- | --- | --- | --- | --- | --- |
| `00000000` | `[       0]` | 7 | 1 | 8 | `[0]` |
| `00000001` | `[       1]` | 7 | 1 | 8 | `[1]` |
| `00000009` | `[       9]` | 7 | 1 | 8 | `[9]` |
| `00001234` | `[    1234]` | 4 | 4 | 5 | `[1234]` |
| `09999999` | `[ 9999999]` | 1 | 7 | 2 | `[9999999]` |
| `12345678` | `[12345678]` | 0 | 8 | 1 | `[12345678]` |

**Zero renders as seven spaces then a `0`** — the final `9` of `z(7)9` always prints, exactly as the shape
implies and with no `blank when zero` to make it disappear. And the trim chain is **correct at every width**:
`subtract b from 8 giving c` consumes the pre-increment tally, `add 1 to b` turns it into a 1-based start, and
the substring is precisely the significant digits. Nothing is wrong with the suppression logic.

**What is wrong is what happens next, and it is a database-visible defect this entry had not anticipated.**
`Post-Legend` is `pic x(32)` and receives `n + 3 + 30` characters, so the **minimum is 34** and it
**overflows in every case**:

| `OI-Invoice` | stored `Post-Legend` | what is lost |
| --- | --- | --- |
| `0` | `[0 : ACME MANUFACTURING COMPANY L]` | `TD` |
| `1234` | `[1234 : ACME MANUFACTURING COMPAN]` | `Y LTD` |
| `9999999` | `[9999999 : ACME MANUFACTURING COM]` | `PANY LTD` |
| `12345678` | `[12345678 : ACME MANUFACTURING CO]` | `MPANY LTD` |

The pointer ends at **33** every time — filled to capacity and stopped. **And the frozen `STRING` carries no
`ON OVERFLOW` phrase** `[sales/sl060.cbl:L1091-L1094]`, so nothing is reported: the probe had to add one
merely to *detect* the overflow that the frozen program absorbs in silence.

So `POST-LEGEND` can never hold a full customer name, and **the longer the invoice number the more of the name
is lost** — a truncation whose extent is set by an unrelated field's digit count. It is silent, it is
persisted, and it looks entirely plausible in the column.

**Alignment with the shipped code — all 6 vectors replayed against the shipped primitives**
(`move.move_to_edited`, `move.inspect_tallying_leading`, `arithmetic.subtract_giving`, `arithmetic.add_to`,
`move.ref_mod`, `move.string_into`): **6 agreements, 0 mismatches**, with identical `m`, identical substring,
identical 32-character legend and the identical pointer of 33 in every case.
**No production change was required** — `acas_posting/programs/sl060_invoice_posting.py` already reproduces the
chain faithfully, overflow included. No `ON OVERFLOW` handling is added and the receiver is not widened
(R-3, R-4).

**(d.2) The print-only renderings — MEASURED, and DECLINED ON SCOPE.** Every other picture this question
governs reaches a print line and no column, so the rendering was watched and recorded rather than
implemented. It is written down here so that a future reader does not re-run it:

| declaration | length | input | rendered |
| --- | --- | --- | --- |
| `pic z(7)9.99cr blank when zero` | 13 | `123.45` | `"     123.45  "` |
| | | `-123.45` | `"     123.45CR"` |
| | | `0` | 13 spaces |
| `pic 9999.99 blank when zero` | 7 | `1234.56` | `"1234.56"` |
| | | `0` | 7 spaces |
| | | `7.05` | `"0007.05"` |
| | | `-1234.56` | `"1234.56"` |
| | | `123456.78` | `"3456.78"` |
| `pic z(7)9.99 blank when zero` | 11 | `1234.56` | `"    1234.56"` |
| | | `0` | 11 spaces |
| | | `123456.78` | `"  123456.78"` |
| `pic zzz9` | 4 | `0` | `"   0"` |
| `pic zz,zz9` | 6 | `1205` | `" 1,205"` |
| `pic ----9` | 5 | `-1205` | `"-1205"` |

Two byproducts worth keeping: `pic z9z9` **does not compile** (*"a Z or \* which is before the decimal point
cannot follow 9"*), so the shape this entry once speculated about cannot exist in a compiled program; and
`blank when zero` suppresses the whole field including the always-printing final `9`, which the `z(7)9.99`
row shows directly — which is also why the `z(7)9` case in (d) prints its `0`: it carries no such phrase.

Measured with GnuCOBOL 3.2.0, `cobc -x -free`, no `-std=` dialect selection, no
`>>SET ARITHMETIC` directive and no `binary-truncate` flag.

**The declination.** `[acas_posting/cobol/move.py]` continues to REFUSE every edited picture outside the
`z`-then-`9` shape that reaches a real column, and `tests/arithmetic/test_move_truncation.py` asserts the
refusal as a **scope decision** with the measurement cited beside it, rather than as an open question. The one
value that IS implemented and asserted unconditionally is unchanged: the `z(7)9` rendering of **zero** — seven
suppressed positions then the always-printing final `9` — because it is the case that reaches a real column
and the assertion is itself the lock.

**(e) Consuming modules.** `acas_posting/cobol/move.py` and
`acas_posting/programs/sl060_invoice_posting.py`. Test-owned by
`tests/arithmetic/test_move_truncation.py` and `tests/arithmetic/test_ledger_balance_accumulation.py`.

<a id="q-70f"></a>

### `Q-70f` — the on-the-wire sign of a negated zero

**Status: `RESOLVED BY ORACLE` (2026-08-07).** A negated zero keeps the **positive** overpunch.

⭐ **The identifier is `Q-70f`, not a new one.** This register first drafted the question under a mnemonic of
its own and then found that `gl070` already has a question family — `Q-70a`, `Q-70b`, `Q-70d`, `Q-70e` in
`acas_posting/programs/gl070_transaction_pre_process.py`, continued as `Q-70f` in
`tests/arithmetic/test_double_entry_explosion.py`, which cites it six times. The existing id is adopted and
the draft mnemonic discarded, so **no duplicate id keys the same question** — which is the whole point of
§5's convention.

**(a) The question.** Several in-scope statements negate a value by multiplying it by minus one — `gl070`'s
CR leg at `[general/gl070.cbl:L517]` and `[general/gl070.cbl:L530]`, and the sign flips of the Sales and
Purchase extract and posting programs. Applied to a **zero** amount, does the compiled program leave the
**positive** overpunch in the sign-carrying digit of the zoned item, or write the **negative** one? Reading
cannot settle it, and neither can any comparison: `-0.00 == 0.00` is true, so the sign of zero is invisible
to every equality test and **only the stored bytes could tell the two apart**.

**(b) Evidence.** The negation sites are enumerated in AAP §0.6.1's arithmetic census; the one the sibling
test names is `multiply pre-amount by -1 giving pre-amount` at `[general/gl070.cbl:L517]`. The three
representations a negative zero would have to pass through are all `Q-5.3`'s subject — a zoned overpunch, a
packed sign nibble — and, for the narrowed fields, an unsigned host variable, which is `Q-3`. This question
is separate from all three because it concerns the **one value at which a sign has no magnitude to attach
to**, and a representation can be right for every other value and wrong for this one. The migration
currently emits the **positive** overpunch, which is why the sibling test's negative-overpunch assertion
fails today rather than passing quietly.

**(c) Oracle experiment.** Under the §10 protocol, seed a transaction whose amount is exactly zero and
which reaches a negating statement — a zero-value CR leg is the direct case:

```text
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol --tables GLPOSTING-REC,GLLEDGER-REC,SALEDGER-REC
```

**The observable is the stored value's sign, read at byte level as well as as a `Decimal`**, because a
`decimal(10,2)` column will render `0.00` either way and only the bytes distinguish the two. Compare the
signed-zero and unsigned-zero renderings; note whether a subsequent accumulation into `LEDGER-BALANCE`
behaves differently.

**(d) Resolution. MEASURED: the POSITIVE overpunch survives ARITHMETIC negation — a negated zero is
byte-identical to a positive zero.**

The scenario route above needs a seeded zero-value leg to reach a negating statement. A probe reached the same
bytes directly: it declared `pic s9(8)v99` DISPLAY exactly as the pre-amount is declared, `REDEFINES`d it as
`pic x(10)`, and read all ten bytes with `FUNCTION ORD` before and after the frozen statement
`multiply pre-amount by -1 giving pre-amount` [`general/gl070.cbl:L517`].

| state | bytes | sign-carrying byte |
| --- | --- | --- |
| `0.00` before the negation | `30 30 30 30 30 30 30 30 30 30` | `0x30` |
| after `multiply … by -1 giving` | `30 30 30 30 30 30 30 30 30 30` | **`0x30` — unchanged** |
| `-1.00`, the same field (control) | `30 30 30 30 30 30 30 31 30 70` | `0x70` |
| `+1.00`, the same field (control) | `30 30 30 30 30 30 30 31 30 30` | `0x30` |

**The two controls are what make the null result trustworthy.** A probe that simply failed to write anything
would also have shown "no change". Rows three and four prove the mechanism is live in that very field: the
negative overpunch `0x70` does appear for a non-zero negative value, and `0x30` for its positive twin. So the
absence of `0x70` on a negated zero is an observation, not a broken experiment. The probe also confirmed that
the value still compares equal to zero afterwards.

**The same result on the leading-sign declaration, with the statement form varied**, which is what shows that
ARITHMETIC is the operative word:

| statement | sign byte |
| --- | --- |
| `move 0.00 to x` | `0` (0x30, positive) |
| `multiply zero by -1 giving x` | `0` (0x30, positive) |
| `compute x = 0.00 * -1` | `0` (0x30, positive) |
| `move -0.00 to x` (a LITERAL) | `p` (0x70, negative) |
| `move 12.34` then `multiply x by -1` | `t` (0x74, negative over the digit 4) |

So the negative overpunch is reachable only by moving a signed literal, and the last row confirms this probe
too was capable of producing it. **Every in-scope negation is arithmetic** — `[general/gl070.cbl:L517]` and
`[general/gl070.cbl:L530]` are both `multiply pre-amount by -1` — so a zero-amount leg on the credit side
carries the positive overpunch, and the wire form of `-0` never arises on this path.

Measured with GnuCOBOL 3.2.0, `cobc -x -free`, no `-std=` dialect selection, no
`>>SET ARITHMETIC` directive and no `binary-truncate` flag.

**Why it comes out this way**, which `Q-5.3` measures independently and this entry therefore does not have to
assume: a zero stored in a signed field carries the POSITIVE sign form in both the zoned and the packed
representations. There is no negative-zero encoding for the negation to move to. This is the same probe that
settled `Q-5.3`'s zoned half, and the two answers are one fact read two ways.

**Consequence for the reproduction.** This migration emits the positive overpunch, so it already matches. The
practical reach of the question is narrower than it looks — a `decimal(10,2)` column renders `0.00` either way,
so no table diff could have distinguished the two, which is precisely why it needed a byte-level probe rather
than a scenario. `tests/arithmetic/test_double_entry_explosion.py` asserts the measured positive overpunch as a
fact, and asserts the refuted negative-overpunch reading against directly rather than marking it.

**(e) Consuming modules.** `acas_posting/cobol/arithmetic.py` and `acas_posting/cobol/usage.py`.
Test-owned by `tests/arithmetic/test_double_entry_explosion.py`, which now asserts the measured sign bytes
as facts and carries no strict expected failure.

<a id="q-empty-batch-at-end"></a>

### `Q-EMPTY-BATCH-AT-END` — what `gl072`'s at-end path writes when the sorted work file is empty

**Status: `RESOLVED BY ORACLE` (2026-08-07).** Neither paragraph leaves any observable effect.

⭐ **This one is handed up from the SCENARIO tier, not the arithmetic tier**, and it is recorded here rather
than in a section of its own because it has the same shape as every other entry in §13: the language does not
decide it, and the only observable is a stored value. It was cited by
`tests/scenarios/test_empty_batch.py` — in that file's module docstring, in its anomaly index and in three of
its assertion messages — **before it had an entry here**, which made the citation dangle and made §17's
"every cited identifier appears in this file" claim false. The entry closes that gap; the identifier is the
one the citing file already uses and is not renamed. That the citing file coined the name is also why it
deliberately asserted only that the **two sides agree** rather than hard-coding an expectation for
`CLEARED-STATUS` or `POSTED` — the correct thing for a parity test to do, and the reason the entry below can
report the measured values without any test having to be rewritten to match them.

**(a) The question.** `gl072`'s main loop opens with an at-end branch, `[general/gl072.cbl:L285-L289]`:

```text
 loop.
     read     post-trans  at end
              perform  end-account
              perform  end-batch
              go to    end-run.
```

On the `empty_batch` scenario the sorted work file holds **zero records**, so the *very first* read hits at
end and both paragraphs run with `save-batch` still zero `[general/gl072.cbl:L281]` and with
`WS-Batch-Record` and the nominal record never having been read at all. `end-batch`
`[general/gl072.cbl:L372-L377]` then unconditionally moves 1 into `cleared-status`, moves `run-date` into
`posted` and performs `GL-Batch-Rewrite`; `end-account` `[general/gl072.cbl:L379-L382]` performs
`GL-Nominal-Rewrite`. The same question extends to `GLLEDGER-REC` because `new-account` — which issues the
only `GL-Nominal-Read-Next` `[general/gl072.cbl:L408]` under its guard at `L407` — is **never reached** on an
immediately-at-end read, so there may be no positioned record for that rewrite to act on. **What do those two
rewrites do to the database?** Three readings are available and reading cannot choose between them: the
rewrite targets a **zero key** and matches no row, so nothing changes; or it matches a row and stamps it; or
the handler reports a failure the program ignores, having no status test at either site.

⭐ **Why the answer is deterministic and therefore worth measuring, whichever reading holds.** `run-date` is
pinned to the project value by `acas_posting/clock.py`, so **if** the `move run-date to posted` at
`[general/gl072.cbl:L376]` fires, the stamped value is fixed and both sides compare byte for byte; if it does
not fire, `POSTED` stays exactly as seeded. Either way the diff is decisive rather than noisy. The binary
observable is `05  Run-Date  binary-long.` `[copybooks/wssystem.cob:L67]`, and `GLBATCH-REC.POSTED` is
`int(8) unsigned` `[mysql/ACASDB.sql:L88]` derived from a `binary-long` `[copybooks/wsbatch.cob:L38]`, so
whatever `L376` writes is compared as an **integer** and not as text — which is why the measured `0` in (d)
below is a value and not an empty string.

⚠️ **This question is entangled with `Q-4` at exactly the fields at issue, and that is why it could not be
measured first.** `Q-4`'s record-length contradiction `[copybooks/wsbatch.cob:L7-L9]` decides the alignment of
the batch record's **trailing** fields — and the trailing fields are `Batch-Status`
`[copybooks/wsbatch.cob:L25-L27]`, `Cleared-Status` `[copybooks/wsbatch.cob:L29-L32]` and the four
`binary-long` dates `[copybooks/wsbatch.cob:L36-L39]`, which is precisely the set `end-batch` writes. An
experiment here that assumed `Q-4`'s answer would have been reading columns whose offsets it had guessed.
`Q-4` is now `RESOLVED BY ORACLE` — both record copies measure **96** and the field sum is authoritative — so
the observables reported in (d) sit on a **measured** alignment rather than an assumed one. The order of the
two measurements was therefore not arbitrary.


**(b) Evidence.** The seed makes the emptiness structural rather than incidental: `empty_batch.yaml` declares
`seed_files` **without `posting.dat`** — `system.dat`, `ledger.dat` and `batch.dat` only — and its one batch
row carries `Items` 0 with `Cleared-Status` 0. So `gl070`'s phase 2 explodes nothing, `gl071` sorts nothing
and `gl072` reads nothing, by construction rather than by luck. The scenario declares
`expected_table_effect: unchanged`, which is the *first* reading above stated as an expectation — and both
runners now enforce it per side from their own pre-run and post-run digests, so a run in which either rewrite
DID change a row fails the runner rather than passing quietly. Note also that `common/acas007.cbl` cannot
wipe the batch table on an open-for-output: its delete-all lines are commented out at
`[common/acas007.cbl:L308-L309]`, unlike the active `[common/acas008.cbl:L316]`.

**(c) Oracle experiment.** The mandated `empty_batch` scenario is already exactly the required state, so no
special probe was needed — which is the reason this one could be measured cheaply and should have been sooner.
The full ten-stage protocol of §10 was run and the **compiled** side's normalized dump read directly:

```text
$C /repo/harness/run_parity.sh /repo/harness/scenarios/empty_batch.yaml
# then read $ACAS_OUT/empty_batch/cobol.normalized/GLBATCH-REC.json and GLLEDGER-REC.json
```

The observables are `GLBATCH-REC.CLEARED-STATUS` and `.POSTED` for the seeded batch, `GLLEDGER-REC` in full,
and **the presence or absence of a row under key zero** in either table. A zero-key row appearing is the
third reading and would be a finding in its own right, since nothing in the frozen cycle intends one.

**(d) Resolution. MEASURED: no observable effect, on either table.** The compiled side's `GLBATCH-REC` after
the run:

| column | value | what it settles |
| --- | --- | --- |
| `CLEARED-STATUS` | **0** | `end-batch` did **not** stamp the batch cleared |
| `POSTED` | **0** | nor did it record a posting date |
| `STORED` | **0** | nor a stored date |
| `ITEMS` | 0 | unchanged from the seed |
| `BATCH-STATUS` | 1 | unchanged from the seed |
| `ENTERED`, `PROOFED` | 155127 | unchanged from the seed |

`GLLEDGER-REC` held its four seeded rows **unchanged** — `300000` still at balance `999.99` and last `999.99`,
and the other three likewise — so `end-account`'s rewrite produced nothing visible. `GLPOSTING-REC` had
`row_count: 0`. **No zero-key row appeared in either table.**

So of the three candidate readings the measured one is the **first**: both rewrites target a key that matches
no row and nothing changes. The expectation recorded in (b) is therefore confirmed rather than merely
declared, and the scenario's `expected_table_effect: unchanged` is a measurement the runners now re-take on
every journey rather than an assumption.

**Why, and this matters for reading the other entries.** The emptiness is not incidental to this scenario — it
is `ANOMALY N-KEY` acting. The `POST-KEY` group move corrupts the key on the way back out of the bridge
(`Q-9`, and `acas_posting/dal/acas006_gl_posting.py`), so `gl070`'s guard
`if batch not = WS-Batch-Nos go to loop` `[general/gl070.cbl:L492-L493]` discards **every** seeded posting and
the work file is empty for reasons that have nothing to do with the batch being described as empty. The same
starvation is why `gl080`'s deletion pass deletes nothing. One frozen defect, several faces.

**Not repaired (R-3, R-4).** No guard is added for the empty case, `save-batch` is not checked before the
rewrite, and nothing is logged.

**(e) Consuming modules.** `acas_posting/programs/gl072_transaction_update.py`, whose `_end_batch`
`[acas_posting/programs/gl072_transaction_update.py _end_batch]` and `_end_account`
`[acas_posting/programs/gl072_transaction_update.py _end_account]` reproduce both paragraphs statement for
statement **including the absent `save-batch` guard**, with `acas_posting/dal/acas007_gl_batch.py` and
`acas_posting/dal/acas005_gl_nominal.py` performing the rewrites, `acas_posting/records/gl_batch.py` owning
the trailing fields `Q-4` also touches, and `acas_posting/cli/gl_post_cycle.py` dispatching them. Test-owned by `tests/scenarios/test_empty_batch.py`, which continues to assert agreement
and that neither side changed the tables its own run started from, rather than the values above — correctly,
because a parity test that hard-coded them would stop being a parity test. The reachability of the at-end path
itself is additionally exercised without a database by
`tests/arithmetic/test_gl072_shipped_silent_skips.py`, which measured that the at-end `end-batch` rewrites
whatever batch record the program is holding — a measurement that bears on this question's second reading and
does **not** resolve it, because that probe drove the shipped module rather than the compiled one.

<a id="q-gl084-accept-semantics"></a>

### `Q-GL084-ACCEPT-SEMANTICS` — what the two `disk-change` prompts do with a keystroke

**Status: `PENDING — AWAITING ORACLE EXECUTION`** — and, unusually for this register, **pending for a
structural reason rather than for want of effort**: the prompts cannot be reached by any fixture that exists,
and reaching them would mean the harness inventing seed state. Opened by the two parity runners (MJ-10), which
is why it sits in this section rather than §12.

**(a) The question, in two halves.** `disk-change` `[general/gl080.cbl:L519-L558]` puts two prompts on the
screen, and each carries an unmeasured input semantic:

1. **`accept a at 1369`** `[general/gl080.cbl:L545]`, where `a` is `77 a pic 99 value zero`
   `[general/gl080.cbl:L183]` — a **two-digit** numeric field offered a **single** keystroke. Does `9` land as
   `09`, so that `if a = 9 go to main-exit` `[general/gl080.cbl:L546-L547]` fires; or as `90`, so that it does
   not and `if a not = zero go to accept-option` `[general/gl080.cbl:L548-L549]` re-prompts instead? The
   answer decides whether `9` aborts anything at all.
2. **`accept file-2 at 1501 with update`** `[general/gl080.cbl:L555]` — an **update** field pre-loaded with
   the path the section has just built `[general/gl080.cbl:L530-L537]`. Does typed text **replace** that
   content or is it **inserted** into it, and where does the cursor start? The answer decides what path an
   override actually produces.

There is a third, smaller half that follows from (1): on `9` the section exits **before** the accept in (2),
so a Return sent with the `9` would remain buffered and be taken by whichever accept came next — answering a
later prompt with a keystroke meant for this one.

**(b) Why it cannot be measured today.** `disk-change` is performed only from `gl080b`
`[general/gl080.cbl:L406]`, and `gl080b` runs only when `archiving` is true — `if archiving perform gl080b
else perform gl080c` `[general/gl080.cbl:L315-L320]` — where `Archiving` is the condition name on
`05 Arch pic x` with `value "Y"` `[copybooks/wssystem.cob:L164-L165]`. **No fixture seeds `Arch = "Y"`.**
Seeding one to reach the prompt would be this harness manufacturing a system-parameter row rather than
reproducing one, which rule R-3 forbids. So the prompts are unreachable, and an unreachable prompt cannot be
watched.

**(c) What was done instead of guessing.** Both runners now **refuse** the inputs whose behaviour depends on
the answer, rather than driving them on an assumption:

| Declared input | Compiled leg | Migrated leg |
| --- | --- | --- |
| `disk_change_option: "0"` | driven — the value is read from the scenario and typed | driven as `--disk-change-option 0` |
| `disk_change_option: "9"` | **refused** — half (1) and the buffered Return are unmeasured | **refused** — it is implemented here, but a capture the oracle cannot match is not evidence |
| `archive_path_override` | **refused** — half (2) is unmeasured | **refused**, for the same reason |

⚠️ **This is the register's rule applied to a case where guessing would have been easy and invisible.** The
compiled leg previously **hard-coded** `0` at the first prompt and had **no step at all** for the second,
while the migrated leg honoured both declared inputs — so a scenario declaring `9` would have been accepted,
driven as `9` on one side and `0` on the other, and the resulting diff would have measured the disagreement
rather than the accounting (R-6). The refusals remove that possibility entirely: either both legs receive
`0` and no override, or the run stops before either posts. Refusing costs nothing real — **no scenario
declares either input**, and the plan steps are `react` rules, which fire only if the screen appears.

**(d) The experiment, specified for whoever can run it.** Seed a fixture whose `SYSTEM-REC.Arch` is `"Y"` —
which is a deliberate act, recorded, not a quiet fixture edit — drive `gl_end_of_cycle`, and capture: the
value `a` holds after a single `9` keystroke; whether `GL084` re-displays; the exact bytes `file-2` holds
after a bare Return and after typed text; and where a following Return is consumed. Until that is done this
entry states the question and the plan and nothing more, which is what `PENDING` means here.

**(e) Consuming modules.** `harness/run_cobol_scenario.sh` (the binding gate and the two `react` plan steps),
`harness/run_python_scenario.sh` (the symmetric refusals), `acas_posting/programs/gl080_end_of_cycle.py` and
`acas_posting/cli/gl_end_of_cycle.py` (which implement both answers and are unaffected by the harness
refusing to drive one of them). **Adjacent but distinct:** `Q-22` (§14) owns *what path the `STRING` builds*
and is measured; `A-NEW-9` records the maintainer's own `*> this lot looks wrong !!!!!` on that construction.
This entry owns only what the two **accepts** do with a keystroke, which neither of those touches.

<a id="q-string-pointer-and-refmod"></a>

### The three that are handed **down**, not up — questions the semantics layer already owns

Three deferrals in the brief for this file are owned by `acas_posting/cobol/move.py`'s register (§5), and
are **cited here by scope rather than re-issued**, because re-numbering them would strand fourteen
citations. Each is recorded with what its owner measured, so a reader of this register is not sent looking:

| Identifier and owner | Question | What the owner records |
| --- | --- | --- |
| **`Q-9` (`cobol/move`)** — ⚠️ *not* this register's `Q-9`; see §15 | `MOVE SPACE` into a numeric receiver | **INEXPRESSIBLE** — measured as a GnuCOBOL 3.2 compile error, so the statement cannot exist in the compiled system and there is no representation to reproduce |
| **`Q-10` (`cobol/move`)** | a reference-modification range past the end of the item | **MEASURED, and unreproducible for a structural reason.** A literal out-of-range range does not compile; a computed one reads **adjacent storage** — `(8:5)` on an `x(10)` item beside a `#` sentinel returns `HIJ##`. A Python `str` has no neighbours, so the layer refuses rather than inventing a value |
| **`Q-11` (`cobol/move`)** | a `STRING` pointer beyond the receiver | **MEASURED** as a **silent no-op**: nothing is written, **and** the pointer is left exactly where it was. A partial fit writes what fits and advances by that much |

`Q-11`'s live site in the frozen source is worth naming, because it is the one the maintainer himself
flagged. `[general/gl080.cbl:L530]` is `move space to Arg-Test.` carrying the inline comment
`*> this lot looks wrong !!!!!`, and it introduces a five-source `STRING` at
`[general/gl080.cbl:L531-L536]` whose result is then moved into the **shorter** `file-2` at
`[general/gl080.cbl:L537]` — the truncation on that final move being the maintainer's concern. That is
**A-NEW-9**. It sits in the archive-path construction, which produces no database effect, so it is recorded
rather than locked, and `Q-22` (§14) owns what path the statement actually builds.

⚠️ Each of the three is **locked by a refutation** in `tests/arithmetic/test_move_truncation.py`: the
**naive** reading — what an engineer would guess before consulting the compiler — is named at the site and
then asserted NOT to hold, either by asserting the refusal the layer raises (`Q-9`, `Q-10`) or by asserting
the measured value against the naive one (`Q-11`). The day a naive reading starts holding, those tests
**FAIL**, which is the R-4/R-6 lock working.

All three USED to be marked `xfail(strict=True)` over the naive value instead, and that was the wrong
instrument for all three: each outcome is **already settled** — a compile error, a refusal, a measurement —
so the marker could only ever fail, and the alarm it promised, an unexpected pass when the oracle answers,
had no oracle answer to wait for. Recording a closed decision as a pending question also made the suite's
xfail list read as a longer arbitration backlog than the migration actually has. The refutation is in any
case the stronger form: an `xfail` goes red only when the naive reading starts holding, whereas an assertion
of the measured behaviour AND of the refutation goes red the moment **either** half changes. These three are
recorded as measured by their owner; this register still refuses to promote any status of its own without a
run, and the R-4/R-6 lock is unchanged in intent and tighter in effect.

---

## 14. The wider register — identifiers opened elsewhere in the migration

The migration was written by many hands, and modules opened questions at the sites where they hit them. Every
`Q-` identifier cited anywhere in the repository is catalogued below so that **no citation dangles**, which
is R-5 applied to this register itself. Entries here are **not re-opened and not re-numbered**: each records
the question its owner named, the owner, and the state the owner reports. Where an owner reports a
measurement, that is recorded as *their* report. Where **this** register has since
watched the same observable, the row says so and the owning entry in §12 or §13 carries the values; the
distinction between a report and an observation is kept, because it is the difference between citing someone
else's number and standing behind one.

### 14.1 The numeric band `Q-10` … `Q-25`

| id | Question | Owner | State as its owner reports it |
| --- | --- | --- | --- |
| `Q-10` | a reference-modification range not wholly inside its item | `acas_posting/cobol/move.py` | **MEASURED** — a literal out-of-range range does not compile at all; a computed one reads ADJACENT STORAGE. With a `#` sentinel beside an `x(10)` item: `(8:5)` → `HIJ##`, `(9:4)` → `IJ##`, `(11:2)` → `##`, `(0:3)` → `NUL AB`. Unreproducible in Python, which has no neighbours, and the layer refuses rather than inventing a value |
| `Q-11` | a `STRING` pointer beyond the receiver | `acas_posting/cobol/move.py` | **MEASURED** — a complete no-op past the end: into `pic x(5)` pre-filled `-----`, `ptr=9` raises overflow, leaves the receiver untouched and leaves the pointer at **9**, unadvanced. A partial fit writes what fits: `ptr=5,"PQ"` gives `AB--P` and `ptr=6`. The advance-to-35 reading is refuted |
| `Q-14` | an edited picture outside the Z-then-9 shape | `acas_posting/cobol/move.py` | **MEASURED — DECLINED ON SCOPE.** The rendering was watched and is tabulated in §13's `Q-EDITED-BLANK-WHEN-ZERO`; it is deliberately not implemented, because every picture it governs receives into a print line and AAP §0.2.2 excludes report formatting. `pic z9z9` does not even compile |
| `Q-15` | whether `gl071`'s `SYSTEM-REC` parameter is ever tested; it is imported for the parameter's declaration and never read | `acas_posting/programs/gl071_batch_sort.py` at `L24-L26` | marked at the site |
| `Q-16` | what a `tinyint(2) unsigned` column holds, and what a predicate comparing it against the **quoted** three-digit string `"000"` actually compares — `HV-IRS-FINAL-ACC-REC-KEY` is `PIC 9(03) COMP` written into a two-digit column | `acas_posting/dal/acasirsub5_irs_final.py` | transport-level; both renderings reproduced as written, nothing normalised |
| `Q-17` | what the table holds, and what a read returns, when fewer than 26 rows exist — the bridge tolerates a short table by design | `acas_posting/dal/acasirsub5_irs_final.py` | measured behaviour of the compiled system, not inferred; note the state after **any** write is dense, all 26 rows, blanks stored as spaces |
| `Q-18` | whether `move 1 to File-Key-No` at `[general/gl080.cbl:L288]` has any observable effect, given the facade's own dispatch paragraphs pin the same value before every call | `acas_posting/programs/gl080_end_of_cycle.py` | reproduced regardless |
| `Q-19` | what the compiled program writes when the quarter subscript is out of range | `acas_posting/programs/gl080_end_of_cycle.py` | **MEASURED** — occurrence 13's six packed bytes land at offsets 125–130 of the 126-byte record, four of them PAST ITS END, leaving `Q1`–`Q4` and `Ledger-Last` unchanged, with no diagnostic and exit 0. So an overrunning store moves no column of any compared table. The subscript stays unbounded and the divergence is declared — see §13's `Q-QUARTER-SUBSCRIPT`, the same site from the subscript's side |
| `Q-20` | whether `GL-Posting-Open-Output` at `[general/gl080.cbl:L673]` **truncates** `GLPOSTING-REC`, as `Open-Output` does on the transfer-file handler | `acas_posting/programs/gl080_end_of_cycle.py` | open; `Q-23` says the statement is unreachable in the frozen source, which does not settle what it would do |
| `Q-21` | whether this program's system-record mutations are persisted at all — `gl080` performs **no** `System-*` facade verb, so it depends entirely on what the caller does with the by-reference parameter | `acas_posting/programs/gl080_end_of_cycle.py` | all reproduced in memory; none written to a table from there |
| `Q-22` | what path the `disk-change` `STRING` actually builds — the maintainer's own `*> this lot looks wrong !!!!!` at `[general/gl080.cbl:L530]` | `acas_posting/programs/gl080_end_of_cycle.py` | measured against the package's record defaults as `"archives archive.dat"`, a space where a separator belongs; reproduced exactly as written |
| `Q-23` | whether `compress-post` aborts the run in the COBOL-files configuration | `acas_posting/programs/gl080_end_of_cycle.py` | the two record lengths measure 103 and 101, so `stop run` at `[general/gl080.cbl:L649]` fires; computed from the descriptors, never from a literal |
| `Q-24` | the facade argument list and the per-handler record operand for the IRS calling convention — five operands in the copybook's own order | `acas_posting/programs/irs030_posting.py` at `L1217-L1229` | marked at the site |
| `Q-25` | which callers of the bridge put a two-digit **year** in `Post-Date (7:2)` and which put a **century** | `tests/arithmetic/test_irs_date_component_derivation.py`, declared *"OWNED HERE"* | **SETTLED BY CENSUS, not by probe** — the question asks which statements exist, so it was answered by enumerating every producer of the eight-character date. **All eleven compose a two-digit YEAR**: `[sales/sl060.cbl:L1071-L1072]`, `[sales/sl100.cbl:L612-L613]`, `[purchase/pl060.cbl:L937-L938]`, `[purchase/pl100.cbl:L591-L592]` and the out-of-scope `[purchase/pl950.cbl:L639-L640]` all build `(1:6)` + `(9:2)`; the IRS side redefines the field as `u-days`/`u-month`/**`u-year`** at `[irs/irs030.cbl:L311-L318]` and again in irs060 and irs070; and `[irs/irs.cbl:L972-L978]` composes `run-date` the same way with the maintainer's own comments *"Only grab YY and not CC"* and *"As IRS uses dd/mm/yy"*. The reader agrees: `[common/irspostingLD.cbl:L462-L464]` loads it into `RP-Year`. **The same question as this register's `Q-8`**, see §15 |

⭐ **`Q-12` and `Q-13` are unused.** They are a gap in the sequence, not an omission from this catalogue:
nothing in the repository cites either, and they are left unassigned rather than back-filled, so that no
existing identifier has to move.

### 14.1a `gl070`'s own question family, `Q-70a` … `Q-70f`

A **lowercase-suffixed** family, which is why a naive identifier search misses it — see §5's note on census
form. Opened by `acas_posting/programs/gl070_transaction_pre_process.py` and continued by
`tests/arithmetic/test_double_entry_explosion.py`:

| id | Question | State as its owner reports it |
| --- | --- | --- |
| `Q-70a` | whether `move 1 to File-Key-No` at `[general/gl070.cbl:L272]` has any effect, given every facade dispatch paragraph sets the key number itself immediately before its `CALL` at `[copybooks/Proc-ACAS-FH-Calls.cob:L52]` | *"probably inert"*, reproduced regardless — the same shape as `Q-18` and `Q-55` |
| `Q-70b` | whether the store `move WS-Batch-Nos to pre-batch` at `[general/gl070.cbl:L480]` is inert | reported inert, reproduced regardless |
| `Q-70d` | whether an early `"X"` exit from the report changes anything a table dump can see | answered in the module: it does not — both branches converge on `GL-Batch-Close` at `[general/gl070.cbl:L440]` |
| `Q-70e` | the shape of the linkage store the program's own dataclass carries | marked at the site |
| `Q-70f` | the on-the-wire sign of a negated zero | **carried as a full entry in §13** — the register's own copy of this question, filed under the family's existing id rather than a new one |

⚠️ `Q-70c` is absent from the family, as `Q-12` and `Q-13` are from the numeric band. Unassigned, not
missing.

### 14.2 The `Q-CLI-*` family — the CLI boundary

Opened by `acas_posting/cli/args.py` and the **seven** route modules — `gl_post_cycle`, `gl_end_of_cycle`,
`sl_invoice_post`, `sl_cash_post`, `pl_order_post`, `pl_payment_post` and `irs_post`, the set
[`traceability.md`](traceability.md) §14.5 enumerates — at the boundary where a menu paragraph becomes
a command line. Several are **settled by their owner**, and the settled ones are recorded as such because a
reader following a citation needs to know it is closed.

| id | Question | State as its owner reports it |
| --- | --- | --- |
| `Q-CLI-SYSREC-LOAD` | whether loading and persisting the system record belongs to the route at all, given no in-scope posting program performs system-record I/O | SETTLED, and settled the other way from an earlier reading: the route is the menu's counterpart, so the route loads and persists |
| `Q-CLI-SYSREC-PINS` | whether the CLI's pins should be re-applied over the loaded row | OPEN — forced for the six connection fields; for `Run-Date`, `Date-Form` and `IRS-Instead` it means the CLI wins, so a scenario must seed those three to agree with the options it passes |
| `Q-CLI-SYSREC-RUNDATE` | that the row's `RUN-DATE` is written once at record-creation time by the out-of-scope `common/sys002.cbl`, and no menu ever writes it | OPEN |
| `Q-CLI-RUNDATE-VS-ROW` | that the frozen menus derive the text date from the row they just read and never write `RUN-DATE` back, so a scenario must pin `--run-date` to the seeded value for the two cycles to be comparable at all | STILL OPEN |
| `Q-CLI-EXITSTATUS` | what process status the frozen system produces | SETTLED by establishing that **there is no oracle observable**: `RETURN-CODE` is read and never written anywhere in the menus or the twelve programs, and each menu ends with a bare `goback` |
| `Q-CLI-OVERREWRITE` | whether the Python route has any counterpart to the menu's exit-time rewrite | **CLOSED BY IMPLEMENTATION at all seven routes.** ⚠️ An earlier revision of this row said "SETTLED at three of the entry points … OPEN at `pl_payment_post`", and a later one said "SETTLED at all six routes with a frozen counterpart … correctly **absent** at `irs_post`". Neither holds: `acas_posting/cli/args.py`'s `overrewrite()` reproduces the three GL/SL/PL menus' RDB arm — keys 1, 2 and 4, closing on key 4 — and **six** routes call it, `pl_payment_post` included; and `irs_post` is not an absence but the **IRS spelling** of the same paragraph, `args.eoj_persist_irs_system_data()` reproducing `irs/irs.cbl`'s `EOJ.`, which the route calls. Only the flat-file second leg is unreproduced, and that is `Q-CLI-OVERREWRITE-SECOND-LEG` below rather than a residue of this question. Because both sides now write the system rows on every route, the canonical comparison is bounded at all 22 in-scope tables rather than at the scenario's declared effect — see the `⭐ UPDATE` in this register's `Q-7`, which asks the complementary question, what the rewrite *writes* |
| `Q-CLI-OVERREWRITE-QUIT` | whether a single-operation process has a counterpart to the menu's quit-time rewrite | SETTLED by reproducing the paragraph: the quit key is the only exit `display-menu.` has, so one operation per process means one persist per process |
| `Q-CLI-OVERREWRITE-SECOND-LEG` | the omitted COBOL half zeroes `File-System-Used` and never restores it, which under a literal reading puts a second dispatch on the indexed leg | **STILL OPEN, and it is the whole of what remains of the `overrewrite` question.** The unreproduced half is the unguarded flat-file pass — `[general/general.cbl:L676-L691]`, `[sales/sales.cbl:L645-L657]`, `[purchase/purchase.cbl:L638-L650]` — which the migration has one store for and therefore cannot reproduce. `Q-7`'s resolution point 3 reports the cross-process consequence as *measured*: the pass wrote `File-System-Used = 0` into `system.dat` record 1 and a later menu process then selected indexed files and issued no accounting DML. What remains open is which leg the oracle's second dispatch takes **without** the build-copy shim that `Q-7` describes |
| `Q-CLI-TERMCODE-1-7` | the reachability of the 1..7 termination-code band | OPEN |
| `Q-CLI-OKTOPOST` | what CLI default preserves a prompt that has **no** defaultable answer | RESOLVED: none does, so the switch is required with no default; an earlier draft answered `True`, which would have invented the one answer that silently enables every database write on the route |
| `Q-CLI-CLEARFILE` | whether the `[Y]` in the IRS end-of-job prompt makes `Y` the effective default | RESOLVED by reading rather than by the prompt's appearance: the accept at `[irs/irs030.cbl:L1717]` carries no `WITH UPDATE`, so the literal stays in the prompt text and a bare Enter **re-prompts** rather than clearing |
| `Q-CLI-IRS-RUNDATE` | whether `irs030` reads the run-date field the IRS menu prepares before every option | STILL OPEN, and deliberately so — nothing provisional executes at the site |
| `Q-CLI-GL080-DEFAULTS` | the observed **database effect** of each of `gl080`'s three promoted interactive parameters | OPEN — in particular that `--disk-change-option 9` leaves `GLPOSTING-REC`, `GLBATCH-REC` and `GLLEDGER-REC` exactly as the seed left them. See §16 |

The separator sub-question of `Q-CLI-RUNDATE-VS-ROW` is settled. The CLI accepts
the same `.`, `,`, `-` and `/` separators that `maps04` accepts, but the frozen
date service normalises a successful `A-Date` to slash form. Therefore the
controlled-clock text observable is captured **after** `dates.maps04(work)`;
`21-09-2025`, `21.09.2025` and `21,09,2025` all pin `to-day` as
`21/09/2025`, with the same binary day number `155127`. Capturing the input
before the call would create a text value the compiled menu cannot carry into
the IRS posting path.

### 14.3 The per-program families

Each identifier is listed individually rather than as a range, so that a search for any one of them lands
here.

**The Sales extract band**, opened by `acas_posting/programs/sl055_invoice_extract_analysis.py` at
`L2612-L2629`:

| id | Question |
| --- | --- |
| `Q-50` | the negated `oi-` fields against the un-negated `ih-` sum, and hence the sign of the credit-notes-this-month total |
| `Q-51` | the termination of the unguarded `db010-Create-Anal` retry when the analysis write fails |
| `Q-52` | the disposition of a failed `write oi-header`, and whether a sequential write can fail at all once the file is open |
| `Q-53` | `il-type pic x` at `[copybooks/slwsinv2.cob:L97]` compared against the numeric literal `3` at `[sales/sl055.cbl:L390]`, where `ih-type` is `pic 9` |
| `Q-54` | what GnuCOBOL does with the space-filled bytes 37-66 that the group move at `[sales/sl055.cbl:L538]` leaves before the following lines zero them |
| `Q-55` | whether any of the nine `move 1 to File-Key-No` statements has an observable effect, given the handler already defaults it |
| `Q-56` | whether any scenario sets `FS-Cobol-Files-Used`, which would make `[sales/sl055.cbl:L326-L348]` reachable |
| `Q-57` | whether the verb shape the module assumes is the one `acas_posting.dal.facade` publishes |
| `Q-58` | the invoice record area's three `REDEFINES` views, and which of them a handler populates on a `Read-Next` |

**The Purchase extract band**, opened by `acas_posting/programs/pl055_order_proof_extract.py` at
`L2418-L2446`. The bare form `Q-PL055` appears in that module as the family's own prefix:

| id | Question |
| --- | --- |
| `Q-PL055-1` | the observable effect of the missing `WITH FILLER` at `[purchase/pl055.cbl:L547]` |
| `Q-PL055-2` | whether the unguarded `Create-Anal` → `Create-Main` retry at `[purchase/pl055.cbl:L499]` terminates |
| `Q-PL055-3` | the negated `oi-` extract row against the **un-negated** `ih-` sum |
| `Q-PL055-4` | the disposition of a failed `write open-item-record-4` at `[purchase/pl055.cbl:L588]` |
| `Q-PL055-5` | the `OI-Header` / `open-item-record-4` storage relationship |
| `Q-PL055-6` | whether any mandated scenario seeds `File-System-Used` to zero |
| `Q-PL055-7` | the exact shape of the single context argument the generated handler expects |
| `Q-PL055-8` | which purchase-invoice record shape the `acas026` handler wants |

**The lettered set**, opened by `acas_posting/dal/acasirsub4_irs_posting.py` — and lettered **precisely to
avoid colliding** with the numeric bands, which makes it the one module that solved §15's problem by
construction:

| id | Question | Locator | Status |
| --- | --- | --- | --- |
| `Q-A` | the width inflations, as `9(5)` sources travel through `9(08)` host variables into `mediumint(5) unsigned` columns | `L267` | **`RESOLVED BY ORACLE`**, and **re-verified 2026-08-07** |
| `Q-B` | the money path at the column's precision limit | `L282` | **`RESOLVED BY ORACLE`**, and **re-verified 2026-08-07** |
| `Q-C` | the key predicate: the key metadata declares `"STR"`, and the coercion its owner reports as **numeric** | `L295` | **`RESOLVED BY ORACLE`**, and **re-verified 2026-08-07** |

⚠️ **The locators above were `L507`, `L522` and `L535` and had gone stale**, by roughly 240 lines, when a
duplicated half of that module's docstring was removed. They are corrected here and the drift is recorded
rather than quietly patched, because it is the same failure mode §9 warns about: a citation that still looks
precise after the thing it points at has moved is worse than no citation, since a reader who follows it lands
in unrelated prose and concludes the claim is false.

**RE-VERIFICATION, 2026-08-07.** These three are the register's only entries whose measurements live in a
module docstring rather than in a §12 entry, so they are the easiest to leave unchecked. All three were
re-measured against the live MariaDB 10.11.7 — the same server the frozen schema names as its producer
[`mysql/ACASDB.sql:L1`] — using the **real** in-scope columns of `IRSPOSTING-REC` inside a transaction that
was then rolled back, so nothing was left behind (confirmed: zero rows after the `ROLLBACK`). Every claim
held:

| claim | measured |
| --- | --- |
| `@@global.sql_mode` is what the bridge's C interface gets | `STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION` — exactly as the docstring states |
| `(5)` and `(2)` are DISPLAY widths, not constraints | `POST4-DR` accepted both `99999` and `16777215`; `POST4-DAY` accepted `255` |
| past the type's range the server REFUSES rather than clamps | `16777216` into `KEY-4` → **ERROR 1264, SQLSTATE 22003**, nothing written; `256` into `POST4-DAY` → the same |
| `decimal(9,2)` keeps a sign | `-12345.67` stored as `-12345.67` |
| the precision limit aborts | `9999999.99` stored exactly; `10000000.00` → **ERROR 1264 / 22003**, nothing written |
| SCALE overflow ROUNDS instead of failing | `1.005` stored `1.01`; `1.004` stored `1.00` |
| the quoted key predicate coerces NUMERICALLY | `9 > "10"` is `0` while `"9" > "10"` is `1`; and against the real `mediumint` key holding `{7, 99999, 16777215}`, `> "10"` returned 2, `< "10"` returned 1, `= "7"` returned 1 and `> "000"` returned all 3 — the numeric answers, not the lexical ones |

The last row is the one worth the trouble: lexically `"7" > "10"` is true, so a lexical comparison would have
returned 3 and 0 for the first two predicates instead of 2 and 1. The two readings disagree on this data,
which is what makes the measurement decisive rather than merely consistent.

### 14.4 The remaining mnemonic identifiers

| id | Question | Owner |
| --- | --- | --- |
| `Q-A17-POSTINGS-EFFECT` | the stored value of `postings` once `RRN` has advanced past its picture — the **value** half of this register's `Q-5`, and the identifier **A-17** carries in [`anomaly-log.md`](anomaly-log.md). **MEASURED 2026-08-07: it does not truncate at the picture at all — the receiver is signed `binary-short`, so the store wraps at 32767 and the negative reaches the unsigned `pic 9(5)` `Batch-Start` as its magnitude.** Recorded in full under [`Q-5`](#q-5) | `acas_posting/programs/pl060_order_posting.py` |
| `Q-PURCH-AVERAGE-SIGN` | the Purchase instance of the signed-to-unsigned narrowing this register carries as `Q-3` | `acas_posting/programs/pl060_order_posting.py` |
| `Q-CR-NOTES-SECOND-PASS` | the `PUITM5-REC` state a dead second pass leaves, against `SAITM3-REC` under the same seed | `acas_posting/programs/pl060_order_posting.py` |
| `Q-VAT-PC-31` | whether storing 31 into a percentage field is observable downstream, and in which column | `acas_posting/programs/pl060_order_posting.py`; cross-referenced from [`anomaly-log.md`](anomaly-log.md) |
| `Q-FACADE-SHAPE` | the exact parameter shape each facade verb declares | `acas_posting/programs/pl060_order_posting.py` |
| `Q-FILE-DEFS-SHAPE` | `File-Defs` against `File-Defs-A` at the handler boundary | `acas_posting/programs/pl060_order_posting.py` |
| `Q-SL060-SUBSCRIPT` | a subscript band in which no declared field wholly receives the store — narrowed to exactly that band and logged when reached, with neither a silent `[a - 1]` nor an exception substituted | `acas_posting/programs/sl060_invoice_posting.py` at `L1732-L1738` |
| `Q-OTM4-HANDOFF` | how the OTM4 sequence `pl055` writes and `pl060` reads is threaded between two dispatches | `acas_posting/programs/pl060_order_posting.py` — reported **RESOLVED** by its owner, and retained rather than removed |
| `Q-OTM5-NARROW` | what a signed-to-unsigned `MOVE` actually stores | `acas_posting/dal/acas029_otm5.py` at `L799-L810` — see the note below |
| `Q-edit-mask-sign`, `Q-edit-mask-truncation` | the sign placement and the truncation behaviour of the bridge's own `WS-MYSQL-EDIT` rendering at `[common/slinvoiceMT.cbl:L271]` — the edited window every bridge builds its SQL text through | `acas_posting/dal/acas016_invoice.py` at `L192-L195`, which reports both **arbitrated** and publishes the resolved window constants so the parity suite can assert them |

⭐ **`Q-OTM5-NARROW` bears directly on this register's `Q-3`, and how it is handled here is a deliberate
decision rather than an oversight.** Its owner reports a **measurement**, taken and independently re-taken on
GnuCOBOL 3.2.0: that the signed-to-unsigned `MOVE` stores the **magnitude** rather than a two's-complement
reinterpretation — `BINARY-LONG -5` into `PIC 9(10) COMP` giving `0000000005` and not `4294967291`,
`BINARY-CHAR -3` into `PIC 9(03) COMP` giving `003` and not `253` — so the sign is discarded and the absolute
value survives. That module says the resolution belongs in this file and records it *"so the measurement is
not lost"*.

It is recorded, attributed, and **it does not promote `Q-3`.** Three reasons, and they are not procedural
squeamishness:

1. **It answers a different link in the chain.** `Q-OTM5-NARROW` measures the COBOL `MOVE` into the host
   variable. `Q-3` asks what the **stored column** holds after the bridge's C interface renders that host
   variable into SQL text. If the report holds, it settles the first link and makes *absolute value* the
   leading candidate of `Q-3`'s three — which is exactly how `Q-3` cross-references it, and no further.
2. **This register observed neither.** Promoting a status on someone else's report would make the register's
   own status column mean two different things, which is the one thing it cannot afford.
3. **§10.1 stands.** With 22 bridges unable to compile, no measurement taken *through a bridge* is available
   at all — and `Q-3`'s subject is precisely what happens through one.

---

## 15. Register collisions, and the scoping rule that resolves them

§5 establishes that three registers coexist and were numbered independently. This section does two things:
it **assigns a globally unique canonical identifier to every colliding reading** (§15.1), and it tabulates
the collisions themselves so that a reader following a citation lands in the right place (§15.2).

⚠️ **Scoping alone was not enough, and saying so is the point of §15.1.** An earlier revision of this
section resolved the collisions *by scoping only* — declaring that a bare `Q-9` means this register unless
found inside a file with its own register. That rule disambiguates a citation **only if the reader knows
which file it came from**, which is exactly what is lost when an identifier is quoted in a commit message,
a review comment, a test failure summary or another document. Seven bare numbers carried between two and
four distinct meanings each, so "`Q-9` is open" was a statement with four possible subjects. Every reading
now has a name that means one thing everywhere.

**Nothing is renumbered in code.** The citations are load-bearing, and rewriting several hundred of them to
tidy a table would risk breaking a suite silently — the failure mode this whole register exists to prevent.
So the canonical identifier is **added** and the bare number **survives as a declared file-scoped alias**:
no existing reference dangles, and every reading gains an unambiguous name.

**The two rules, stated together because they work as a pair.**

- **The canonical rule (new, and preferred).** Every reading has exactly one canonical identifier, listed
  in §15.1. Canonical identifiers are globally unique and may be used anywhere — in prose, in a commit
  message, across documents — with no scope qualifier.
- **The scoping rule (retained, for the citations already in the tree).** An **unqualified** `Q-n` means
  *this* register. A citation found inside a module or test that declares a register of its own resolves
  *within that file*, to the canonical identifier §15.1 pairs it with. Where ambiguity is possible, the
  qualified form — `Q-9 (cobol/move)` — remains valid and equals its canonical name, `Q-MOVE-9`.

### 15.1 The canonical allocation

The scheme is the one `acas_posting/programs/pl055_order_proof_extract.py` already uses for `Q-PL055-1` …
`Q-PL055-8` and `general/gl070`'s family uses for `Q-70a` … `Q-70f`: **a module prefix and the module's own
number**, so that the canonical name and the legacy alias differ by a prefix only and neither has to be
remembered separately.

**A reading that is genuinely *this* register's question keeps this register's number and gets no new name.**
Two of the apparent collisions are that case, and conflating them with the real ones is how the table used
to overstate the problem: `[acas_posting/cobol/arithmetic.py INTERMEDIATE_PRECISION]`'s `Q-2` and `gl051`'s `Q-2` are both
*"the compound VAT expression's intermediate precision"*, which is §12's `Q-2` verbatim; and `gl051`'s
`Q-9` is *"A-15's record-length contradiction"*, which is §12's `Q-4` verbatim. Those two are **aliases of
this register's entries**, not separate questions.

| Canonical id | Subject | Owning file | Legacy alias |
| --- | --- | --- | --- |
| `Q-GL051-1` | is persisting `Batch-Status` the caller's job — **RESOLVED FROM THE SOURCE** by its owner, no experiment needed | `acas_posting/programs/gl051_batch_control_check.py` | its `Q-1` |
| `Q-GL051-3` | what an unsigned `pic 9(9)v99 comp-3` receiver holds after a negative store — *in-program*, distinct from §12's `Q-3`, which is about the bridge and the column | same | its `Q-3` |
| `Q-GL051-4` | the three promoted preconditions, `move 1 to trutht` and its neighbours | same | its `Q-4` |
| `Q-GL051-5` | `z` has no `VALUE` clause `[general/gl051.cbl:L172]` and is set only conditionally | same | its `Q-5` |
| `Q-GL051-6` | the file-handler facade's Python call shape | same | its `Q-6` |
| `Q-GL051-7` | `Date-Form` is **mutated** when it is zero | same | its `Q-7` |
| `Q-GL051-8` | `line-cnt` `[general/gl051.cbl:L166]` counts print lines, so a page break is observable only through `Q-GL051-7` | same | its `Q-8` |
| `Q-SL060-1` | which `oi-type` values reach the loop, and what is stored when `a` is 0 or above 3 | `acas_posting/programs/sl060_invoice_posting.py` | its `Q-1` |
| `Q-SL060-2` | is `FS-Cobol-Files-Used` ever true in a scenario — if it is, four library-call gates become reachable and **R-1 forbids honouring them** | same | its `Q-2` |
| `Q-SL060-3` | the disposition of a failed `OTM3-Write`, which leaves `SALEDGER-REC` written and `SAITM3-REC` not | same | its `Q-3` |
| `Q-SL060-4` | the reachable range of `Current-Quarter`, and what an out-of-range value writes | same | its `Q-4` |
| `Q-SL060-5` | what the narrowing moves store, including the `SIGN LEADING` conversion | same | its `Q-5` |
| `Q-SL060-6` | `sl060` increments `Next-Batch` and sets `Postings` but performs **no** `System-Rewrite` — does either update survive the run | same | its `Q-6` |
| `Q-SL060-7` | the exact `Post-Legend` bytes out of the edited-move / `INSPECT` / `STRING` chain, including residue and the truncation point past 32 characters | same | its `Q-7` |
| `Q-SL060-8` | the disposition of a failed `GL-Batch-Write`, which leaves posting rows with no batch header | same | its `Q-8` |
| `Q-SL060-9` | `Rrn` is `pic 9(5) comp` (0…99999) but `Postings` is `binary-short` (−32768…32767), so an RRN above 32767 **wraps negative** | same | its `Q-9` |
| `Q-PL100-1` | the status pair and row state produced by `A-PL100-A`'s write to an unopened table, in `"Y"` mode, in `"B"` mode, and with `G-L` unset | `acas_posting/programs/pl100_payment_posting.py` | its `Q-1` |
| `Q-PL100-2` | the `PULEDGER-REC` state produced by `A-PL100-B`'s rewrite of a record never successfully read | same | its `Q-2` |
| `Q-PL100-3` | the `VALUEANAL-REC` count drift from `A-PL100-C`, and whether the unsigned count columns underflow or clamp | same | its `Q-3` |
| `Q-PL100-4` | the exact `post-date` text the century-dropping reference modification yields per `Date-Form` | same | its `Q-4` |
| `Q-PL100-5` | the stored value of `purch-pay-average` if the bridge narrows a signed `binary-long` to an unsigned column | same | its `Q-5` |
| `Q-MOVE-9` | `MOVE SPACE` into a numeric receiver — **measured as a compile error**, so there is no behaviour to reproduce | `acas_posting/cobol/move.py`, `tests/arithmetic/test_move_truncation.py` | their `Q-9` |
| `Q-MOVE-10` | a reference-modification range past the item — **UNREPRODUCIBLE**; every in-scope range is in range | same | their `Q-10` |
| `Q-MOVE-11` | a `STRING` pointer beyond the receiver — **measured** as a complete no-op, pointer included | same | their `Q-11` |
| `Q-MOVE-14` | an edited picture outside the Z-then-9 shape — **UNOBSERVABLE**, because every other edited picture receives into a print line and report formatting is out of scope | same | their `Q-14` |
| `Q-VATNET-1` | what a `COMPUTE … ROUNDED` with no `ON SIZE ERROR` stores when the result exceeds `vat-amount`'s nine declared digits `[copybooks/irswspost.cob:L18]` — **proved unreachable from in-range data**, since the widest in-range VAT fits the field | `tests/arithmetic/test_irs_vat_from_net.py` | its `Q-1` |
| `Q-GL080-DIVIDE-BY-ZERO` | the zero divisor at the cycle divide — already a mnemonic, and already the arithmetic tier's alias; §13 holds the entry | `acas_posting/cobol/arithmetic.py`, two arithmetic tests | their `Q-7` |
| `Q-CLI-OKTOPOST` | what CLI default preserves a prompt with no defaultable answer — already a mnemonic; §14.2 holds it | `acas_posting/cli/sl_cash_post.py` and its program module | that module's `Q-6` |

**Two entries in that table are aliases of *this* register and are listed for completeness, not as new
questions:** `gl051`'s `Q-2` → §12 `Q-2`, and `gl051`'s `Q-9` → §12 `Q-4`.

**The allocation rule for anything opened from now on.** Take the next free number **in this register**, or
mint a module-prefixed or mnemonic identifier that cannot collide. Do **not** open a bare `Q-n` inside a
module: `acas_posting/dal/acasirsub4_irs_posting.py` avoided the whole problem by choosing letters (§14.3),
and `pl055` avoided it by prefixing.

### 15.2 The collision table

| Number | This register's reading | Other readings, with the citing file |
| --- | --- | --- |
| `Q-1` | the date module's reject contract | **four other readings, all now canonically named.** `tests/arithmetic/test_irs_vat_from_net.py` at `L143`, marked *"THIS FILE'S register"* — the unsized-overflow question, canonically **`Q-VATNET-1`**; `gl051_batch_control_check.py` — whether persisting `Batch-Status` is the caller's job, which that module reports **resolved from the source**, canonically **`Q-GL051-1`**; `sl060_invoice_posting.py` — which `oi-type` values reach the loop, canonically **`Q-SL060-1`**; `pl100_payment_posting.py` — a status pair and row state, canonically **`Q-PL100-1`** |
| `Q-2` | default arithmetic precision | **not a collision at three of the four sites.** `acas_posting/cobol/arithmetic.py` at `L96`, five arithmetic tests, **and `gl051_batch_control_check.py`** all carry the *same* question — the compound VAT expression's intermediate precision — so they are aliases of this entry, not rivals. ⚠️ An earlier revision of this row said `gl051`'s `Q-2` was "on another subject"; it is not, and treating it as one overstated the collision count. The one genuine other reading is `sl060_invoice_posting.py`'s, canonically **`Q-SL060-2`** — whether `FS-Cobol-Files-Used` is ever true |
| `Q-3` | the signed-to-unsigned stored value | the same question in the dictionary's `ambiguity_refs`, in `acas012_sales.py`, `acas007_gl_batch.py`, `records/sales_ledger.py` and four arithmetic tests — **the shared reading**. Two genuine other readings, both canonically named: `gl051`'s in-program `comp-3` receiver, **`Q-GL051-3`**, and `sl060`'s failed `OTM3-Write` disposition, **`Q-SL060-3`** |
| `Q-4` | the batch record's length contradiction | the same question in the dictionary's `ambiguity_refs`, in `records/gl_batch.py`, `acas007_gl_batch.py` and three arithmetic tests — **the shared reading**, and `gl051_batch_control_check.py`'s local `Q-9` is a further alias of it. Two genuine other readings: `sl060`'s `Current-Quarter` range, **`Q-SL060-4`**, and `pl100`'s `post-date` text, **`Q-PL100-4`** |
| `Q-5` | the unexplained move | its **value** half is `Q-A17-POSTINGS-EFFECT` (§14.4), which is the identifier **A-17** carries |
| `Q-9` | `HV-POST-RRN` declared and fetched but never loaded | ⚠️ **the sharpest collision — four meanings on one number, now four names.** `acas_posting/cobol/move.py` and `tests/arithmetic/test_move_truncation.py` publish a `Q-9` meaning *`MOVE SPACE` into a numeric receiver*, canonically **`Q-MOVE-9`** (see §13's handed-down table); `gl051_batch_control_check.py`'s local `Q-9` means *A-15's record-length contradiction*, which is an alias of **this register's `Q-4`**; and `sl060_invoice_posting.py`'s means the `Rrn`/`Postings` width mismatch that wraps negative above 32767, canonically **`Q-SL060-9`**. §15.1 is what makes each of those citable outside its own file, and scoping alone is what it used to rest on |
| `Q-8` | `Post-Date (7:2)`: year or century | **the same question** as `Q-25` (§14.1), which `tests/arithmetic/test_irs_date_component_derivation.py` declares *"OWNED HERE"*. The two are **aliases**, not rivals: `Q-8` is the register entry and `Q-25` is the owning test's identifier for the same subject, and they now carry the same **answer** — Sales and Purchase compose a year, `irs030`'s own conversion path truncates and stores a century. Both identifiers are kept so that neither a document citation nor a test citation dangles |
| `Q-6` | the `sl830` asymmetry | two other readings, both canonically named. `sl060_invoice_posting.py`'s local `Q-6` — whether the `Next-Batch` increment and the `Postings` set survive a run with no `System-Rewrite` — is **`Q-SL060-6`**; and the ok-to-post question that `acas_posting/cli/sl_cash_post.py` records its program module carrying as *its own* `Q-6` is the mnemonic **`Q-CLI-OKTOPOST`** (§14.2), already resolved |
| `Q-7` | the menu-shell exit-path rewrite | ⚠️ **the collision this register could not absorb by renumbering — and the one that first showed why a mnemonic beats a scope rule.** `tests/arithmetic/test_gl080_cycle_divide_rounded.py` and `tests/arithmetic/test_compute_truncate_unrounded.py` both publish a `Q-7` meaning *the zero divisor*, carried on `acas_posting.cobol.arithmetic.SizeErrorNoStore`. §12's `Q-7` is externally mandated to the menu-shell rewrite and the arithmetic tier's citations are equally fixed, so **neither could yield the number**: the zero-divisor question is filed in §13 under the mnemonic `Q-GL080-DIVIDE-BY-ZERO`, which is an **alias** for the arithmetic tier's `Q-7` and not a new question. `Q-CLI-OVERREWRITE` and `Q-CLI-OVERREWRITE-SECOND-LEG` (§14.2) are this entry's neighbours at the CLI boundary |

**Why the collisions were not simply prevented.** Because the register was being written at the same time as
the modules that cite it, and there was no shared allocation point until this file existed. Two modules
solved it properly by construction — `acas_posting/dal/acasirsub4_irs_posting.py` chose **letters** (§14.3)
and `pl055_order_proof_extract.py` chose a **module prefix** — and §15.1 generalises the second of those to
every colliding reading rather than leaving the problem to a scope rule the reader has to apply correctly.

---

## 16. Scope declinations, recorded honestly

Three items below are **not ambiguities in the frozen source**. They are decisions this migration took about
what to exercise and what to trust, and they are recorded here rather than left implicit because each one
would otherwise be read as coverage that does not exist. A silent declination and a fabricated resolution
fail in the same direction: both let a reader believe something has been checked.

### 16.1 `gl080` was driven by no scenario at all — **and now it is**

⚠️ **THIS DECLINATION HAS BEEN WITHDRAWN, and the original is quoted rather than deleted** so that a reader
who met it elsewhere can see it was retired rather than wonder whether they misread it. It said:

> *"The end-of-period path is not exercised by any of the eight mandated scenarios … `gl_end_of_cycle`, which
> is the route that dispatches `gl080`, is the operation of none of them … Every one of them therefore needs
> a scenario that does not exist yet, and building it is part of those experiments rather than a precondition
> somebody else has met."*

Every clause of that was true when written and the last one is now false. **The scenario was built.**
`harness/scenarios/end_of_cycle_gl.yaml` declares the `gl_end_of_cycle` operation — the route that is
`general/general.cbl`'s `load09.` dispatching `gl080` — and it is driven through the same ten-stage protocol
as the other eight, with `tests/scenarios/test_end_of_cycle_gl.py` beside it. There are now **nine** committed
scenario definitions.

**What the withdrawal changes, and what it does not.** It removes the *precondition* that three of this
register's questions were waiting on, and all three have since been measured —
`Q-GL080-DIVIDE-BY-ZERO`, `Q-QUARTER-SUBSCRIPT` (carried as `Q-19`) and `Q-2`'s fifth `ROUNDED` site at
`[general/gl080.cbl:L328]` are each `RESOLVED BY ORACLE`, though by **standalone compiled probes** rather than
by that scenario, for the reason each entry gives: their observables are a control-flow branch, a byte offset
and a penny, which a probe exhibits directly. That is a legitimate oracle measurement — the compiled program
produced the observable and it was watched — and it is why an out-of-range subscript's exact byte offsets are
recorded rather than pending. **What a probe cannot establish is what the *program* does with those values in
a real end-of-period run**, which is a different question; the committed scenario is what a future agent
should reach for when asking it. Five of §14.1's questions (`Q-18`, `Q-20`, `Q-21`, `Q-22`, `Q-23`) remain
catalogued rather than resolved, and the scenario now exists for whoever takes them.

**What the mandate still says, kept distinct from what exists.** AAP §0.8.5 mandates a scenario *set* — clean
batch per ledger, mixed accepted-and-rejected, period-end totals, control-total mismatch, empty batch — and
**none of those five is an end-of-period run**, so eight scenarios discharge the mandate and the ninth is an
addition beyond it. Statements elsewhere in these documents about *the mandated set* rightly still say eight;
statements about *what is committed* say nine. Conflating the two would either overstate the mandate or
understate the coverage.

**One thing the original got right and is worth keeping:** `system.period` is seeded as `1` in **all nine**
committed scenarios — the ninth included — which is inert for this purpose: with a period of one the
cycle-to-period divide has nothing to decide. A `period = 0` seeding, which is what
`Q-GL080-DIVIDE-BY-ZERO` needed, is still not in any committed scenario; that question was closed by probe
instead, and its entry says so. So the ninth scenario drives the route without exercising the divisor, and the
two facts are independent.

**The route census, recounted — and counted from the right key.** ⚠️ The table below is derived from each
scenario's `operations` **list**, not from its singular `operation` key, and the distinction changes the
answer. Every scenario declares both: `operation` names the *first* route so that a single-route scenario
reads naturally, while `operations` is the ordered list the runners actually walk. `period_end_totals`
declares **four** operations against a singular `operation` of `sl_invoice_post`, so counting the singular key
alone attributes one route to it and loses three — which an earlier revision of this section did, thereby
under-counting `pl_order_post` and omitting `sl_cash_post` and `pl_payment_post` from the census altogether.

| Route | Scenarios that declare it | Which |
| --- | ---: | --- |
| `gl_post_cycle` | 4 | `clean_batch_gl`, `control_total_mismatch`, `empty_batch`, `mixed_accepted_rejected` |
| `sl_invoice_post` | 2 | `clean_batch_sl`, `period_end_totals` |
| `pl_order_post` | 2 | `clean_batch_pl`, `period_end_totals` |
| `irs_post` | 1 | `clean_batch_irs` |
| `sl_cash_post` | 1 | `period_end_totals` |
| `pl_payment_post` | 1 | `period_end_totals` |
| **`gl_end_of_cycle`** | **1** | **`end_of_cycle_gl` — the route that dispatches `gl080`** |

**Nine** scenarios, **twelve** operation declarations, **all seven** routes exercised. The last row is where
the declination used to be: it read **0**, and it is the single figure the withdrawal changes. Every other row
is unchanged by the ninth scenario, which is the point — the addition closed exactly one gap and invented no
coverage elsewhere.

**⭐ What closes the in-process half of the gap, and what it does not close.** The declination above is about
the *scenario* tier. A separate question is whether the shipped module is executed at all, and until QA raised
it the answer was **no**: `tests/arithmetic/test_gl080_cycle_divide_rounded.py` reproduced the cycle-to-period
divide as a **local transcription**, so `acas_posting/programs/gl080_end_of_cycle.py` was never called and a
defect in the shipped module could not have been detected by any test. That is now closed in-process by
**`tests/arithmetic/test_gl080_shipped_end_of_cycle.py`**, which imports the shipped module and drives its own
functions — the `ROUNDED` cycle-to-period divide at `[general/gl080.cbl:L328]`, the **unbounded** quarter
subscript at `[general/gl080.cbl:L345]`, the second independent rotating quarter counter at
`[general/gl080.cbl:L345-L357]`, and the archive and deletion phases including the sign flips at
`[general/gl080.cbl:L493]` and `[general/gl080.cbl:L506]` — using the module's own storage record and a
substituted facade, so no database is required. Its expected values were **measured by probing the shipped
module** and recorded before any assertion was written; where a value is a compiled-oracle question rather
than an implementation fact it is left to the register and not asserted as measured.

**A ninth scenario was deliberately not added**, and the reason is a constraint rather than a preference: AAP
§0.3.1 enumerates the scenario set as eight files and §0.8.5 mandates that same set, so adding a
`gl_end_of_cycle` scenario would put this migration outside its own plan. The in-process coverage is therefore
a **bounded divergence** from the obvious remedy, recorded here and in the header of the test file itself, and
it does **not** substitute for the end-to-end evidence: the five questions above still require the compiled
oracle, and [`traceability.md`](traceability.md) §7.2 states in its own table that `gl080` is driven
in-process only.

**The three interactive parameters `gl080` promotes**, recorded in passing because their defaults decide
whether a run reaches the database at all, and each default was **measured from the source** rather than
inferred from the prompt text:

| Parameter | Locator | What actually proceeds |
| --- | --- | --- |
| backup-confirm | `[general/gl080.cbl:L295-L302]` | **proceeds by default.** `L298` moves `space` into the reply before the accept at `L299`, and `L300-L302` abort only on Esc or `A`/`a` — so a blank carries on |
| disk-change | `[general/gl080.cbl:L545-L549]` | **default `0`.** `L546-L547` exit on `9`; `L548-L549` send anything **other than zero** back to `accept-option` — so only `0` proceeds and anything else re-prompts |
| archive-path | `[general/gl080.cbl:L553-L557]` | **default: no override.** `L555` accepts over the displayed value `with update`; `L556-L557` re-prompt if the first character is a space |

`Q-CLI-GL080-DEFAULTS` (§14.2) owns the observed **database effect** of each — in particular that
`--disk-change-option 9` should leave `GLPOSTING-REC`, `GLBATCH-REC` and `GLLEDGER-REC` exactly as the seed
left them.

### 16.2 `gl051` has **no CLI entry point**

**The declination.** `acas_posting/programs/gl051_batch_control_check.py` is reachable as a **library
function** and at the arithmetic tier; no route in `acas_posting/cli/` dispatches it. That is deliberate and
follows the migration boundary: `general/gl051.cbl` is an interactive batch proof-and-amendment screen
program of which **only** the control-total gate at `[general/gl051.cbl:L1096-L1133]` is in scope, while the
frozen menu reaches the *whole* interactive program through its own load paragraph. A CLI route that
dispatched the module would have to invent the interactive surround, which is exactly what AAP §0.3.4
excludes.

**How the control-total scenario reaches the gate anyway**, which is why the declination costs nothing:
`control_total_mismatch` does not call `gl051`. It seeds a batch that the gate would reject, and then
`gl070`'s **phase-one batch check** finds the batch still open and raises the terminate code — the raise
being `[general/gl070.cbl:L289]`, `move 5 to ws-term-code`, and **not** the line above it, since
`[general/gl070.cbl:L288]` performs a display paragraph. The menu then tests that code and returns rather
than continuing: `[general/general.cbl:L810-L811]` is

```text
     if       ws-term-code = 5
              go to display-menu.
```

sitting between the `gl070` dispatch at `L808-L809` and the `gl071` dispatch at `L812-L813`. So the
observable is *the absence* of everything `gl071` and `gl072` would have written — which is a state
comparison, reachable without a `gl051` route.

### 16.3 The General and Purchase sub systems have **not** been fully re-tested by the maintainer

This is the declination that changes how every General and Purchase figure in the migration must be
obtained, and it is the maintainer's own statement rather than an inference. `[README.TXT:L51-L53]`, verbatim:

> *"I have not had any time to work with General at all since it was migrated over to using the GnuCobol compiler (3.2 final) now some years back."*

Two further passages complete the picture, and the second is what makes the first decisive rather than
isolated:

- `[README.TXT:L45-L48]` records the **Purchase** ledger as *still undergoing system testing*, with more
  order transaction entries and both automatic and manual payments still to be exercised against the reports.
- `[README.TXT:L50-L51]` records testing as complete for **IRS, Stock and Sales** — *"apart for some
  reports"*.

**General and Purchase are both absent from that completed list.** Between them they contribute the majority
of the in-scope programs: five of the twelve are General and three are Purchase.

⇒ **Expected values for General and Purchase scenarios must come only from the oracle** — never from the
documentation, and never from reasoning about what the code was intended to do. AAP §0.6.9 puts the
consequence in one sentence, quoted verbatim:

> *"If the compiled GL cycle behaves surprisingly, the surprise is the specification."*

That is the whole reason a register of ambiguities exists for this migration rather than a list of decisions.
Where the General Ledger does something inexplicable, the correct response is to reproduce it and record the
question — which is what every entry in §12 and §13 did while it was open, and what the `MEASURED` verdicts
they now carry were reached by. ⚠️ **No §12 entry carries `PENDING — AWAITING ORACLE EXECUTION`, and exactly
one §13 entry does**: `Q-GL084-ACCEPT-SEMANTICS`, which §17's status rows count. It is pending for a
structural reason rather than for want of effort — the two prompts it asks about are unreachable in every
fixture, and reaching them would mean seeding a system-parameter row this harness has no business inventing
(R-3) — and while it is open **both parity legs refuse the inputs whose behaviour depends on the answer**,
so no run can be driven on a guess. The discipline is unchanged — a question is recorded before it is
answered, and the answer replaces the status rather than the question.

---

## 17. Self-audit

Counted properties of this file, stated so that a reviewer can check them mechanically rather than take the
document's word for its own discipline.

⚠️ **Every figure below was re-derived against the current text of this file, not carried forward.** That
matters because a self-audit is the one section whose subject is the file itself: any edit anywhere above can
falsify a row here, so the rows are recomputed after the last of them and the counting algorithm is stated
alongside each figure that has one. An earlier revision's counts had drifted behind its own content — the
§13 entry total, the anchor total and both identifier censuses were each one edit stale — which is precisely
the failure a self-audit exists to catch and was, in that revision, unable to catch about itself.

**The counting algorithm, stated once and used by every identifier row.** Scope: the git-tracked text files
under `acas_posting/`, `tests/`, `harness/`, `docs/` and `data_dictionary/`, plus `pyproject.toml` and
`requirements.txt`. Pattern: `\bQ-[A-Za-z0-9][A-Za-z0-9._-]*`, with trailing punctuation stripped, which is
permissive enough to catch all four identifier forms §5 names — including the lower-case-suffixed `Q-70f`
that a stricter pattern misses. Two exclusion sets, both enumerated so the exclusion is checkable rather
than asserted: **six family labels and metasyntactic placeholders** — `Q-5.x`, `Q-70`, `Q-CLI`,
`Q-PL055-n`, `Q-n` and the `Q-nn` that `acas_posting/programs/gl080_end_of_cycle.py` uses for *"`AMBIGUITY
Q-nn` at the site that raises it"* — and **seven Payroll data-item names**.

| Property | Value |
| --- | --- |
| Primary entries in §12 | **14** — `Q-1` … `Q-5`, `Q-5.1` … `Q-5.3`, `Q-6` … `Q-10`, and `Q-SYS4-SPARE-SENTINEL` |
| Entries in §13 | **8** of its own — six handed up from the arithmetic tier, `Q-EMPTY-BATCH-AT-END` from the scenario tier and `Q-GL084-ACCEPT-SEMANTICS` from the two parity runners — plus one companion answer key, plus **3** cited by scope |
| Statuses in §12 | **0** × `PENDING — AWAITING ORACLE EXECUTION`; **12** × `RESOLVED BY ORACLE` (`Q-1`, `Q-4`, `Q-5`, `Q-5.1`, `Q-2`, `Q-3`, `Q-5.2`, `Q-5.3` and `Q-SYS4-SPARE-SENTINEL` dated 2026-08-07; `Q-6`, `Q-7`, `Q-10` dated 2026-08-04); **1** × `RESOLVED BY CONSTRUCTION` (`Q-8`); **1** partial (`Q-9`). Sums to the 14 entries |
| Statuses in §13 | **1** × `PENDING — AWAITING ORACLE EXECUTION` (`Q-GL084-ACCEPT-SEMANTICS`, opened by the parity runners and pending because the prompts it asks about are unreachable in every fixture); **6** × `RESOLVED BY ORACLE`, all 2026-08-07 (`Q-SORT-TIE-ORDER`, `Q-GL080-DIVIDE-BY-ZERO`, `Q-QUARTER-SUBSCRIPT`, `Q-ROUNDED-OVERFLOW-ORDER`, `Q-70f`, `Q-EMPTY-BATCH-AT-END`); **1** two-part status (`Q-EDITED-BLANK-WHEN-ZERO`, `RESOLVED BY ORACLE` for the case that reaches a column and `MEASURED — DECLINED ON SCOPE` for the print-only pictures). Sums to the 8 entries |
| `RESOLVED BY ORACLE` used as a status | **19 entries** — 12 in §12, 6 in §13 and the column-reaching half of §13's two-part entry — and only where a compiled run or a focused compiled probe directly answered the stated question, with the captured observable written into the entry. §4 states the rule; this row is the only tally of it |
| `RESOLVED BY CONSTRUCTION` used as a whole-entry status | **1** — `Q-8`, whose open half was *which statements exist*, answered by a census of the frozen `MOVE` sites shown in full in the entry. It claims the weaker of the two resolved statuses deliberately: no compiled run was needed, so none is claimed. `Q-9` remains partial and carries its settled half inside the entry |
| Entries carrying all five template parts | **all of them.** Every §12 and §13 entry has (a) question, (b) evidence, (c) oracle experiment, (d) resolution-or-status and (e) consuming module(s) |
| Explicit anchors | **23** — one for each of the **22** anchored entries (`q-1` … `q-9`, `q-5-1` … `q-5-3`, `q-sys4-spare-sentinel`, and one per §13 entry), plus `q-string-pointer-and-refmod` on §13's closing handed-down table, so a bare `#q-n` citation resolves. Every internal fragment reference in this file — **20** of them, to **15** distinct anchors — resolves; **0** dangle. Each id appears exactly ONCE: a duplicate anchor is as bad as a missing one, because a reader cannot tell which of the two a link reached — and a duplicate `q-empty-batch-at-end` has arisen **twice**, each time while two independently drafted versions of that entry coexisted, which is why this row is now checked by matching the anchor tags mechanically rather than by reading |
| `Q-` identifiers cited by the project | **85** cited somewhere OTHER than this file, and **every one of them appears in this file** — §12, §13, §14 or §15, so **0 dangle**. Census scope, stated so the figure is reproducible: the git-tracked text files of `acas_posting/`, `tests/`, `harness/`, `docs/`, `data_dictionary/` and the two manifests, under the algorithm stated above this table. ⚠️ This row has read **82**, then **81**, then **85**; it is re-derived mechanically under that algorithm on every revision and now comes out at **85** — the newest being `Q-GL084-ACCEPT-SEMANTICS`, which both parity runners name in the diagnostic that refuses the input it governs — and the earlier figures are corrected rather than defended, since a row whose whole purpose is to be reproducible has to match what reproducing it yields |
| Identifiers this file uses **as register identifiers** | **114**, and every one of them is entered, catalogued or declared here |
| … of which cited **outside** this register | **85** — the row above. Each resolves to a §12 or §13 entry or to a §14/§15 catalogue row, so **no citation anywhere in the project dangles** |
| … of which **register-only** | **29**, each declared as such rather than left to look like an omission: **3** documented as **unassigned** — `Q-12`, `Q-13`, `Q-70c` — and **26** newly minted in §15.1 as the canonical names for readings that previously had only a colliding bare number: seven in the GL051 series, nine in SL060, five in PL100, four in MOVE, and the single `Q-VATNET-1` (the series are named without their `Q-` prefix here on purpose: a self-audit row that spells a family stem mints a token its own census then has to exclude). ⚠️ Earlier revisions of this row read **86** and then **88** and counted `Q-GL080-DIVIDE-BY-ZERO` and then `Q-SYS4-SPARE-SENTINEL` among the register-only identifiers. Neither is one: [`scenario-diff-evidence.md`](scenario-diff-evidence.md) cites the first and the six corrected fixtures cite the second, so both fall inside the 84. `Q-GL080-DIVIDE-BY-ZERO` remains the one **coined name** for an existing question (§13, §15) — coined and cited being different properties that the old row conflated |
| Tokens outside the census, and why | Two closed sets, both named in full so the exclusion is checkable rather than asserted. **Payroll data-item names — `Q-TAX`, `Q-TAXES`, `Q-FICA-TAX`, `Q-CO-FUTA-LIAB`, `Q-ENDED`, `Q-Year`, `Q-mmdd`** — are COBOL fields in a sub system AAP §0.2.2 excludes in its entirety; they are not register identifiers and are deliberately not catalogued. **Family labels and placeholders — `Q-5.x`, `Q-70`, `Q-CLI`, `Q-PL055-n`, `Q-n`, `Q-nn`** — name groups and metasyntactic slots rather than questions; the last is what `acas_posting/programs/gl080_end_of_cycle.py` writes in *"`AMBIGUITY Q-nn` at the site that raises it"*. A naive `Q-` pattern over this file therefore returns more tokens than the rows above count, by these two sets plus case and trailing-punctuation variants of them. ⚠️ This row used to assert a specific naive-token total. That number decayed on every edit to the file and is replaced by the rule, for the same reason §4's status tallies were moved into this section: a count written where nothing recomputes it is a claim with a shelf life |
| Experiments described as having been run | The strict build, all nine parity journeys, both scenario orders, the two-run determinism tier, the focused boundary probes cited by `Q-7`, `Q-9` and `Q-10`, and the 2026-08-07 focused probes cited by `Q-1`, `Q-2`, `Q-3`, `Q-4`, `Q-5`, `Q-5.1`, `Q-5.2`, `Q-5.3`, `Q-SYS4-SPARE-SENTINEL`, `Q-SORT-TIE-ORDER`, `Q-GL080-DIVIDE-BY-ZERO`, `Q-QUARTER-SUBSCRIPT`, `Q-ROUNDED-OVERFLOW-ORDER`, `Q-EDITED-BLANK-WHEN-ZERO`, `Q-70f` and `Q-EMPTY-BATCH-AT-END`. Every one of the latter reports its captured observable in its own entry. Two of them called a COMPILED MODULE rather than only compiling a probe — `Q-1` invoked `maps04.so` and `Q-3` went through the compiled handler, bridge and `cobmysqlapi` to real SQL |
| Measured values claimed as this register's own observations | Only values linked to the 2026-08-04 evidence files and to the compiled probes named in their entries, which now include the 2026-08-07 set. The 2026-08-07 figures were captured by probes compiled with the frozen build scripts' own flags — no `-std=`, no `>>SET ARITHMETIC`, no `binary-truncate` — so each records the compiler's default behaviour and not a configured one |
| Provenance of every measured claim | Durable repository state, or an explicit label. **0** citations of a host temporary path remain: the four an earlier revision carried under `/tmp/…` were removed, and each claim they supported now cites either a committed script, a frozen locator or a section of [`scenario-diff-evidence.md`](scenario-diff-evidence.md) — or is labelled a **report of an observed run rather than a retained artefact** |
| Runtime versions the observations are attributed to | Stated once, in §10's "The provenance a reported observation carries with it": GnuCOBOL 3.2 final and MariaDB 10.11.7 on the compiled side, a C-backed CPython 3.12 on the Python side. **No claim of parity across every 3.12 patch release** is made anywhere |
| Storage censuses published here | **0.** §9 adopts [`traceability.md`](traceability.md)'s canonical census by reference and records the two figures an earlier revision got wrong, so this file no longer publishes a second, disagreeing count |
| Commands shown that cannot run as written | **0**, re-checked after §10 was rewritten. Every `$C` block uses in-container `/repo/harness/...` paths, opens with the stage-1 `reset_db.sh --seed-dir "/data/fixtures/$N"`, and asks `dump_tables.py` only for in-scope tables. ⚠️ `Q-6`'s autogen probe was the exception: it proposed dumping four out-of-scope tables, which exits **83**, and now names the runners' row-count probes instead |
| Experiments that instrument the frozen source | **0.** §3 lists the five permitted observables; none of them requires a change to a frozen file |
| Experiments that add a column, an index, a view or a probe table | **0** (R-3) |
| Experiments that report a value through a binary float | **0** (R-2) |
| Experiments that build inside the mounted checkout | **0.** §3's hazard note and §10's protocol both forbid it |
| Locators verified by direct reading of the frozen source | **all of them.** §8 lists the thirteen corrections that verification produced |
| Identifiers renumbered **in code** | **0.** §15.1 adds a canonical name beside each colliding bare number and keeps the bare number as a declared alias, so no existing citation was rewritten and none dangles |
| Identifiers newly opened here | **0 questions.** `Q-EMPTY-BATCH-AT-END` was **cited before it was entered** — by `tests/scenarios/test_empty_batch.py`, which coined it — so its §13 entry adopts an existing identifier and closes a dangling citation rather than opening a question. Two others were drafted under new mnemonics and both were then traced to identifiers the project already had: one became `Q-70f` when `gl070`'s own question family was found (§14.1a), and one — the zero divisor — is the arithmetic tier's `Q-7`, which §12's mandated `Q-7` prevents this register from using, so it keeps the mnemonic `Q-GL080-DIVIDE-BY-ZERO` as a declared **alias** (§15.2). The **26** canonical identifiers §15.1 mints are the same case at scale: each is paired one-to-one with a reading its owning file already published. **Names are coined; questions are not.** |
| Third-party measurements recorded but **not** promoted to a resolution | **1** — `Q-OTM5-NARROW`'s magnitude finding (§14.4), attributed to the tier that took it and changing no status here. Two entries have left this row rather than being removed from it, and the distinction matters: the provisional constants of `Q-2`, `Q-3`, `Q-5.2`, `Q-5.3` and `Q-ROUNDED-OVERFLOW-ORDER` were measured by this register's own probes and promoted; and the arithmetic tier's zero-divisor measurement was **independently re-measured** here, so `Q-GL080-DIVIDE-BY-ZERO` now rests on this register's own observation and merely agrees with the tier's. `Q-5.1`'s constants, listed here as provisional until 2026-08-07, are measured and no longer are |

Two properties that are deliberately **not** claimed, because claiming them would be the failure this file
exists to prevent:

- **That every question is answered.** ⚠️ This bullet used to say *"It is not. **Six** remain open"*, naming
  `Q-1`, `Q-4`, `Q-5`, `Q-5.1`, `Q-GL080-DIVIDE-BY-ZERO` and `Q-EDITED-BLANK-WHEN-ZERO`. All six were measured
  on 2026-08-07 and **no §12 or §13 entry now carries `PENDING — AWAITING ORACLE EXECUTION`.** The bullet is
  rewritten rather than deleted, because what it was guarding against still needs guarding against and the
  guard now takes a different form.

  **What is still not claimed is that being answered is the same as being closed.** Three distinctions survive
  the promotions, and flattening them would be the failure this file exists to prevent:
  - **An answer can be that the question was malformed.** `Q-4` asked which of two record lengths governs; the
    measurement is that both figures are 96 and the maintainer's 98 is simply false, so there was never a
    choice. Recording that as a resolution is right; recording it as *"the 96 reading was confirmed"* would
    misdescribe what happened.
  - **An answer can be that the behaviour is unobservable, which is itself a finding** rather than a deferral.
    `Q-EDITED-BLANK-WHEN-ZERO` retains exactly that shape for `gl072`'s three print items — every edited
    receiver there is a print line and AAP §0.2.2 puts report formatting beyond database effects out of
    scope — while the one case that *does* reach a column is measured. §4 draws that line, and the twelve
    permanent `xfail`s in the arithmetic tier hold it.
  - **Measuring a defect does not repair it and must not be read as repairing it.** `A-11`, `A-15` and `A-17`
    in [`anomaly-log.md`](anomaly-log.md) all moved from `PENDING` to `REPRODUCED` on these measurements and
    all three remain live defects under R-4. `Q-5` is the sharpest case: knowing that
    `move RRN to postings` wraps at 32767 and reaches an unsigned column as a magnitude tells a reader what
    the column holds and nothing whatever about whether holding it is correct.
- **That the resolutions rest on the mandated scenarios.** Most do not. Nine parity journeys establish that the
  two implementations agree; they cannot establish what the compiled system does at a boundary no accounting
  journey visits, and several of these questions live precisely there. Those were settled by **focused compiled
  probes**, and every entry says which instrument answered it. A green scenario still closes nothing by
  association — §4's rule is unchanged and is the reason these promotions mean anything.
- **That a measurement which confirms the implementation is a weaker result than one that overturns it.**
  Several of the 2026-08-07 probes found the Python side already correct. That is recorded as what it is — a
  confirmation — and each entry says so in those words rather than presenting the implementation's own reading
  as though the probe had discovered it. The value of those runs is that a choice became an observation, which
  is exactly what R-6 asks for; it is not that anything changed.

---

## 18. Companion documents

This register is one of four migration documents and deliberately does not duplicate the others. All four
are companion deliverables of the same single execution phase, per AAP §0.4.5 and §0.4.1.7.

| Document | What it carries | Why it is not here |
| --- | --- | --- |
| [`anomaly-log.md`](anomaly-log.md) | the twenty-two canonical reproduced defects, plus appended candidates, each with its locators and its reproducing module | R-4's register. This file carries the **questions**; that one carries the **known** wrong behaviours. Where a defect's stored value is unmeasured, its status there is `PENDING` plus a `Q-` cross-reference into here |
| [`traceability.md`](traceability.md) | program to module, paragraph to function, field to dictionary entry, with the `GO TO` class annotated at each transfer site | R-5's mapping tables. This file names a consuming module per entry and stops there |
| [`scenario-diff-evidence.md`](scenario-diff-evidence.md) | the observed empty-diff evidence, per mandated scenario, with manifest digests and runtime artifact locations | parity measurements belong there; this register records only the semantic questions those measurements answer |

Further reading inside the repository, none of it modified by this work: `README-python-migration.md`
(AAP §0.2.1.4) for how to build the oracle, seed a scenario, run both cycles and diff them; and the
maintainer's own `README.TXT` and `Changelog` for the COBOL system's history — read throughout this register
and, per §3, never edited.
