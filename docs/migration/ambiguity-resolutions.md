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

**⚠️ Read this before reading anything else. No oracle run has been observed.** AAP §0.6.9 records that
the authoring host has neither a COBOL compiler nor a container runtime, and that is still true of the
host on which this register was written. Every question below therefore carries its **experiment**, fully
specified and ready to run, and the status **`PENDING — AWAITING ORACLE EXECUTION`** rather than an
answer. The status `RESOLVED BY ORACLE` exists in the vocabulary and is **deliberately unused**: it is
reserved for the agent who actually watches a run. Nothing here describes an experiment as performed, and
nothing here states a measured value that was not measured.

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

**There is no user rules document for this project.** The `review_rules` facility was called while this
register was written, including a full-document read with an explicit range, and every call returned
exactly:

```text
No user rules provided.
```

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

— and the checkout enforces it: `harness/` contains **no `__init__.py`** (verified), so it is not a
package and cannot be imported as one, and `pyproject.toml` excludes `harness*` from the distribution.

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

Four statuses, used consistently, and one of them is reserved.

| Status | Meaning | Permitted evidence |
| --- | --- | --- |
| **`PENDING — AWAITING ORACLE EXECUTION`** | Genuinely open. The experiment is specified and has not been run. | none — the entry states the question and the plan, nothing more |
| **`RESOLVED BY CONSTRUCTION`** | Settled by reading the frozen source, with the reading shown in full so it can be checked and contested. | frozen-source locators, and arithmetic performed on what they declare |
| **`PARTIALLY RESOLVED`** | One path settled by construction, another still open. Both halves are stated separately, and the boundary between them is named. | as above for the settled half; nothing for the open half |
| **`RESOLVED BY ORACLE`** | **RESERVED. Not used anywhere in this register.** | an observed run, with the captured observable recorded |

**The reserved status is the load-bearing one.** It must not be written until an agent has actually
watched the compiled program produce the observable, and the value it produced is recorded in the entry.
The string `RESOLVED BY ORACLE` occurs **five** times in this file, all of them talking *about* the status
rather than assigning it: once in the opening box, twice in this section, once in §11's statement about the
index column, and once in §17's audit row. It appears **zero** times as an entry's status. §17 records that as
a counted property rather than an intention, so a future edit that promotes an entry without a measurement
changes a number a reviewer can check.

Two statuses that deliberately do **not** exist: "probably", and "resolved by inference from the
standard". The second is the dangerous one, because it reads like evidence. Where the ISO reading is the
one the Python side currently implements, the entry says so in those words — *implemented provisionally
on this basis, not observed* — and stays `PENDING`.

---

## 5. Identifier convention

**⭐ Identifiers are externally imposed and must not be renumbered.** The sibling `tests/arithmetic/`
suite, the twelve program modules, the twenty-two data-access modules and the generated data dictionary
all cite these identifiers directly — including inside `xfail(strict=True)` reason strings, and inside
per-field `ambiguity_refs` lists in `data_dictionary/acas_posting_dictionary.json`. Renumbering would
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
   use: `acas_posting/dictionary/generate.py` writes `"Q-3"` and `"Q-4"` into per-field `ambiguity_refs`,
   and [`anomaly-log.md`](anomaly-log.md) carries the statuses `PENDING — Q-3` for A-11 and
   `PENDING — Q-4` for A-15. An **unqualified** `Q-n` in any migration document means this register.
2. **The semantics-layer register** — `acas_posting/cobol/usage.py` claims `Q-5.1` … `Q-5.3`,
   `acas_posting/cobol/move.py` claims `Q-9` … `Q-14`, and `acas_posting/programs/gl071_batch_sort.py`
   claims `Q-15`. The claim is stated in `acas_posting/dal/acasirsub5_irs_final.py` at `L718-L721`.
3. **Module-local registers**, each self-declared. `tests/arithmetic/test_irs_vat_from_net.py` at `L143`
   labels its own entry *"(THIS FILE'S register)"*; `gl051_batch_control_check.py`,
   `sl060_invoice_posting.py` and `pl100_payment_posting.py` each keep a local `Q-1` … `Q-9`; and
   `acas_posting/dal/acasirsub4_irs_posting.py` uses letters — `Q-A`, `Q-B`, `Q-C` — precisely to avoid
   the clash.

The collisions this produces are **tabulated in §15 and resolved by scoping, never by renumbering**. A
citation found inside a module that declares its own register resolves in that module; a citation in a
document, a test id, a dictionary `ambiguity_refs` entry, or a bare cross-reference resolves here.

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
| bare `comp` census | *"410"* | **236** in `copybooks/` | not reproducible under any scope tried; see §9's method note |
| reference-modification census | *"83 live uses"* | **74** `(n:m)` forms on live lines of the twelve in-scope programs | as above; the `(7:4)` ×16 and `(7:2)` ×4 sub-counts **do** reproduce exactly |
| `tests/scenarios/` | *"confirmed present, 8 files"* | **absent** — the directory holds no `.py` files | cited by AAP section instead, per §9 |

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
`acas_posting/cli/` and `acas_posting/records/` and `acas_posting/dictionary/` packages; the fourteen test
files under `tests/arithmetic/`, plus `tests/conftest.py` and
`tests/determinism/test_two_runs_byte_identical.py`; the nine scripts and two Dockerfiles under
`harness/` with its eight scenario definitions under `harness/scenarios/`; both files under
`data_dictionary/`; and the two sibling documents [`anomaly-log.md`](anomaly-log.md) and
[`traceability.md`](traceability.md).

**Absent, and therefore cited by Agent Action Plan section rather than asserted as files:** the eight
scenario test files of `tests/scenarios/` (AAP §0.4.1.7 — the directory exists and holds no `.py` file),
[`scenario-diff-evidence.md`](scenario-diff-evidence.md) (AAP §0.2.1.3), and `README-python-migration.md`
(AAP §0.2.1.4). Where this register says a scenario test "will" own something, that is a statement about
the plan, not about the checkout. The sibling documents adopt the same discipline —
[`traceability.md`](traceability.md) marks `scenario-diff-evidence.md` **absent** in its own companion
table — and this register follows it rather than inventing a different one.

**Census method, stated because the numbers below differ slightly from the brief's.** Every count in this
register was re-derived rather than carried over. Unless an entry says otherwise:

- A *live* line is one that is not a `*>` comment line. Counts labelled "live" exclude comments; counts
  labelled "declared" include them, because a commented-out declaration is still evidence of intent.
- The usage census is over `copybooks/` only, the directory that holds the record layouts: `comp-3`
  **182**; `binary-long` **166** declared, 165 live; `binary-short` **32** declared, 31 live;
  `binary-char` **84**; bare `comp` **236** — the token `comp` matches 422 times, of which 182 are the
  `comp-3` spelling and 4 the `comp-5` spelling.
- The sign-clause census is also over `copybooks/`: `sign leading` **4**, `sign is leading` **2**,
  `sign trailing` **0**, `separate` **0**. Six leading-sign fields in total, and no separate sign anywhere
  in the frozen record layouts.
- `ON SIZE ERROR` **0** and `REMAINDER` **0**, counted per file across all twelve in-scope programs and
  zero in every one of them.
- No `-std=` dialect flag appears in any frozen shell script, no `>>SET` directive in any `.cbl`, `.cob`
  or `.scb`, and no `binary-truncate` anywhere in the frozen sources. Verified by search over the whole
  checkout; the only matches for those strings in the tree are Python migration files quoting the absence.
- The two structural censuses over `copybooks/`, for completeness: `occurs` **110** and `redefines` **61**.
- Out-of-scope names are given as **counts only**, never enumerated as though migrated: 22 in-scope tables
  + 11 out of scope = **33** `CREATE TABLE` statements in `[mysql/ACASDB.sql]`; 20 in-scope bridge pairs +
  8 out of scope = **28** pairs. The checkout holds 28 `common/*MT.scb` and 29 `common/*MT.cbl`; the extra
  generated file is `common/dummy-rdbmsMT.cbl`, which has no `.scb` counterpart because it is the stub, not
  a bridge.

⚠️ **Where a re-derived figure disagrees with the received one, both are recorded and neither is presented
as the other's correction on authority.** The Agent Action Plan and
`tests/arithmetic/test_comp3_packed_decimal.py` at `L77-L80` both record bare `comp` as **410**,
`binary-short` as **31**, `occurs` as **107** and `redefines` as **60**. Counting live `copybooks/`
declarations gives **236**, **31**, **110** and **61**. Three of the four differ by a handful and are
plainly a matter of comment-line inclusion or of which directories were counted; the `comp` figure differs
by enough that the two counts cannot be reconciled by that explanation, and no scope tried here reproduces
410. The figures used in this register are the ones above, with the method stated, precisely so that a
reader who prefers the specification's numbers can see exactly what was counted and disagree on the
evidence.

---

## 10. The oracle protocol every experiment invokes

Every experiment below is a specialisation of one protocol, so the protocol is stated once here and the
entries state only what they change. It is the eight-stage sequence documented in the harness itself, at
`[harness/docker-compose.yml:L29-L45]`, reproduced here as the commands an agent actually types:

```text
C="docker compose -f harness/docker-compose.yml run --rm -T gnucobol"
S=<scenario file>   N=<its basename without the extension>

$C /repo/harness/build_oracle.sh                                          # once per image
$C /repo/harness/seed.sh                   "$S"                           # stage 1
$C /repo/harness/run_cobol_scenario.sh     "$S"                           # stage 2
$C /repo/harness/dump_tables.py  --scenario "$N" --side cobol \
                                 --scenario-file "$S"                     # stage 3
$C /repo/harness/normalize.py    --scenario "$N" --side cobol             # stage 4
$C /repo/harness/reset_db.sh               "$S"                           # stage 5
$C /repo/harness/run_python_scenario.sh    "$S"                           # stage 6
$C /repo/harness/dump_tables.py  --scenario "$N" --side python \
                                 --scenario-file "$S"                     # stage 7
$C /repo/harness/normalize.py    --scenario "$N" --side python
$C /repo/harness/diff_states.py  --scenario "$N" --scenario-file "$S"     # stage 8
```

Four properties of that sequence are load-bearing for this register, and the harness states them itself:

- **The empty diff is the pass condition, and the only one.** `[harness/docker-compose.yml:L42-L44]`:
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
| The affected-table list | `--scenario-file` for the scenario's own `affected_tables`, or `--tables` for an explicit list — **never both**, since `harness/dump_tables.py` rejects the combination as *"alternative ways of choosing the same list, so use exactly one"* | bounds the observation to the tables the scenario is about; see `Q-7` |
| The IRS fan-out state | `IRS-Instead` in the seeded system row — `[copybooks/wssystem.cob:L179-L181]`, with `88 IRS-Used value "Y"` and `88 IRS-Both-Used value "B"` | three states, and the state decides which tables a run touches at all |

Where an entry needs a value at a boundary the eight scenarios do not already seed, it says so explicitly
and describes the seed it needs. It does **not** propose editing a frozen loader to accept one.

### 10.1 ⛔ A blocking precondition: the oracle cannot be built today

Every experiment in this register is specified against a protocol that **currently cannot complete**, and
that is the honest reason the statuses read as they do rather than a matter of nobody having got round to it.

`copybooks/ACAS-SQLstate-error-list.cob` is **absent from the checkout** yet named by a `COPY` statement in
**44** frozen files — 22 of the 28 generated `common/*MT.cbl` bridges and the same 22 `common/*MT.scb`
sources (verified by search; the 29th `*MT.cbl`, `common/dummy-rdbmsMT.cbl`, has no `.scb` and does not
reference it). Those bridges therefore **cannot compile**, the handlers that `CALL` them cannot reach a
table, and `harness/build_oracle.sh` cannot complete — which is why it detects the absence by name and
explains it rather than failing obscurely. Everything else in the tree compiles: all twelve in-scope posting
programs, all seventeen handlers, all twenty in-scope loaders and the menu shells.

**⛔ It must not be fabricated.** The reason is specific to this register's subject rather than general
caution: the copybook carries the **SQLSTATE-to-`FS-Reply` mapping**, which is what *defines* the oracle's
rejection behaviour — and rejection behaviour, in both dimensions, disposition **and** database effect, is
precisely what this migration must reproduce. An invented mapping would make the oracle wrong in the one
dimension nobody could later detect, and it would breach both R-3 and R-4. It must be supplied by the
maintainer.

Two consequences for how this register is read:

- **`PENDING — AWAITING ORACLE EXECUTION` here means blocked, not deferred.** The experiments are written
  out in full so that the moment the copybook is supplied they can be run without redesign.
- **Where another agent reports a measurement taken before or outside that blockage, this register records
  the report and attributes it, and still does not promote a status** — see `Q-OTM5-NARROW` in §14 and its
  cross-reference from `Q-3`. Recording someone else's measurement as though this register had observed it
  would be the same failure as inventing one.

Cross-reference: **A-NEW-13** in [`anomaly-log.md`](anomaly-log.md), and
[`traceability.md`](traceability.md), which records the same absence as a finding rather than an omission.

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

Twelve primary entries. The status column is the one to read first.

| id | Question | Status | Consuming module(s) |
| --- | --- | --- | --- |
| [`Q-1`](#q-1) | Does `maps04` leave its output field untouched on a rejected date, and does every in-scope caller pre-zero it? | `PENDING — AWAITING ORACLE EXECUTION` | `acas_posting/dates.py`, `acas_posting/clock.py` |
| [`Q-2`](#q-2) | What intermediate precision the default compiler applies at the five `ROUNDED` sites, and to the compound VAT expression | `PENDING — AWAITING ORACLE EXECUTION` | `acas_posting/cobol/arithmetic.py` |
| [`Q-3`](#q-3) | What a negative binary value *becomes* once the bridge narrows it into an unsigned host variable and an unsigned column | `PENDING — AWAITING ORACLE EXECUTION` | `acas_posting/dal/acas012_sales.py`, `acas_posting/dal/acas007_gl_batch.py` |
| [`Q-4`](#q-4) | Which of the batch record's two declared lengths governs the record actually read | `PENDING — AWAITING ORACLE EXECUTION` | `acas_posting/records/gl_batch.py` |
| [`Q-5`](#q-5) | What observable effect the unexplained `move RRN to postings` has, in each of the four Sales and Purchase posting programs | `PENDING — AWAITING ORACLE EXECUTION` | `sl060_invoice_posting.py`, `sl100_cash_posting.py`, `pl060_order_posting.py`, `pl100_payment_posting.py` |
| [`Q-5.1`](#q-5-1) | The default `binary-size` and `binary-truncate` policy governing every `COMP` and `BINARY-*` field | `PENDING — AWAITING ORACLE EXECUTION` | `acas_posting/cobol/usage.py` |
| [`Q-5.2`](#q-5-2) | The byte length of a `SIGN LEADING` display item — three readings, none adjudicated | `PENDING — AWAITING ORACLE EXECUTION` | `acas_posting/cobol/usage.py` |
| [`Q-5.3`](#q-5-3) | The concrete zoned-decimal overpunch byte values, for both signs and for zero | `PENDING — AWAITING ORACLE EXECUTION` | `acas_posting/cobol/usage.py` |
| [`Q-6`](#q-6) | Whether `sl830`, which the Sales menu dispatches before `sl055` and the Python route does not, is observably a no-op | `PENDING — AWAITING ORACLE EXECUTION` | `harness/run_cobol_scenario.sh`, `harness/run_python_scenario.sh` |
| [`Q-7`](#q-7) | What the menu shells' unconditional `overrewrite` writes on exit, which the Python CLI has no counterpart for | `PENDING — AWAITING ORACLE EXECUTION` | `harness/dump_tables.py`, `harness/diff_states.py` |
| [`Q-8`](#q-8) | Whether `Post-Date (7:2)` holds a **year** or a **century** — settled on the Sales path, open elsewhere | **`PARTIALLY RESOLVED`** | `acas_posting/dal/acasirsub4_irs_posting.py`, `acas_posting/dal/acas006_gl_posting.py`, `harness/normalize.py` |
| [`Q-9`](#q-9) | Whether `HV-POST-RRN` being declared and fetched but never loaded is the maintainer's stated convention or the field he doubted | **`PARTIALLY RESOLVED`** | `acas_posting/dal/acas006_gl_posting.py`, `acas_posting/dal/cursor_state.py` |

`RESOLVED BY ORACLE` appears nowhere in that column, and `RESOLVED BY CONSTRUCTION` appears nowhere as a
whole-entry status — the two part-resolved entries carry their settled halves inside the entry, where the
reading can be shown, rather than in a column that cannot hold one.

**§13** carries the deferrals handed up from the arithmetic tier: **six** entries of its own, mostly under
mnemonic identifiers, plus a companion answer key that a run supplies, plus **three** questions cited by
scope because the semantics layer already owns them. **§14** catalogues every remaining `Q-` identifier the
repository cites — **82** distinct identifiers are cited across the migration trees, and **every one of them
resolves to an entry or a catalogue row in this file**, so no citation anywhere dangles (§17 states that as a
counted property, with the census scope defined so the figure is reproducible). **§15** tabulates the
identifier collisions between the three coexisting registers.
**§16** records three scope declinations that are decisions rather than ambiguities, and **§17** is a counted
self-audit of this file.

---

## 12. The register — entries

<a id="q-1"></a>

### `Q-1` — the date module's reject contract

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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
$C /repo/harness/seed.sh                  "$S"
$C /repo/harness/run_cobol_scenario.sh    "$S"
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

**(d) Resolution.** None. The status stands. What the source *does* support, stated as an expectation
rather than a finding: the two `go to Main-Exit.` transfers leave `A-Bin` untouched, so any caller that
does not pre-zero should be observed carrying its prior value forward. That expectation is exactly what the
experiment tests, and the second half of it — *which* callers pre-zero — the source does not answer at all.

**(e) Consuming modules.** `acas_posting/dates.py`, which reimplements `maps04` including its reject
behaviour, and `acas_posting/clock.py`, which pins the two date observables at the CLI boundary and
therefore decides what a caller's field holds before the call.

<a id="q-2"></a>

### `Q-2` — default arithmetic precision

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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
$C /repo/harness/seed.sh                  "$S"
$C /repo/harness/run_cobol_scenario.sh    "$S"
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

**(d) Resolution.** None. **What the semantics layer carries, reported rather than adopted:**
`acas_posting/cobol/arithmetic.py` at `L96` records both halves of `Q-2` as measured against GnuCOBOL 3.2.0 —
*evaluate at extended precision, then quantize **once**, at the store* — and
`tests/arithmetic/test_compute_rounded_half_up.py` asserts the **rejected** alternative, the reduced-precision
per-sub-expression penny, as a strict expected failure so that a later change to quantize sub-expressions
turns the suite red. That is a report by another agent, recorded here per §10.1's rule and **not** promoted:
this register has observed nothing, and the same test states in its own words that the oracle cannot be
rebuilt in this checkout.

Note the boundary of this question precisely, because several sibling tests depend on where it stops: `Q-2` reaches only expressions whose intermediate needs **more
digits than the receiver declares**. `tests/arithmetic/test_irs_vat_from_net.py` records the semantics
layer's working assumption and states plainly that no assertion in that file would change if the answer
moved, because its figures never approach the limit. The compound gross expression is the exception, and
`tests/arithmetic/test_irs_vat_from_gross.py` marks the affected proposition `xfail(strict=True)` against
`Q-2` rather than asserting it.

**(e) Consuming module.** `acas_posting/cobol/arithmetic.py`, which owns every store's truncation
direction and the extended-precision intermediate. Test-owned at the parity tier by
`tests/arithmetic/test_irs_vat_from_gross.py`, with `tests/arithmetic/test_compute_rounded_half_up.py`
and `tests/arithmetic/test_compute_truncate_unrounded.py` recording the same identifier where their own
figures touch it.

<a id="q-3"></a>

### `Q-3` — a negative binary value through an unsigned host variable into an unsigned column

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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

Cross-reference: **A-11** in [`anomaly-log.md`](anomaly-log.md), whose status there is `PENDING — Q-3`.

**(c) Oracle experiment.** Under the §10 protocol, seeding a customer whose statistics computation drives a
**negative** value into one of the narrowed fields, and a batch whose date fields do the same:

```text
$C /repo/harness/seed.sh                  "$S"
$C /repo/harness/run_cobol_scenario.sh    "$S"
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

**(d) Resolution.** None. **The provisional implementation, named so the oracle confirms or replaces a
concrete value:** the Python side currently stores the **absolute value**, taken in
`acas_posting/cobol/usage.py`'s `_wrap_into_bits`, and `tests/arithmetic/test_comp_binary.py` asserts that
choice as *provisional* rather than as fact. That is the same answer `Q-OTM5-NARROW` (§14.4) reports as
measured at the `MOVE`, one link earlier in the chain — which is corroboration, not arbitration.

The status stands, and it must: `tests/arithmetic/test_comp_binary.py` holds the
value consequence open rather than asserting it, and `tests/arithmetic/test_pic_field_descriptors.py` and
`tests/arithmetic/test_gl080_cycle_divide_rounded.py` assert only that the affected descriptors *carry the
`Q-3` reference*, which is a statement about traceability rather than about the value. That arrangement is
what stops a plausible number entering the codebase: until the artifact drops the tag, the tests that would
assert a value report an expected failure.

**(e) Consuming modules.** `acas_posting/dal/acas012_sales.py` for the Sales instance and
`acas_posting/dal/acas007_gl_batch.py` for the batch instance. Test-owned by
`tests/arithmetic/test_comp_binary.py`.

<a id="q-4"></a>

### `Q-4` — the batch record's length contradiction

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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

Cross-reference: **A-15** in [`anomaly-log.md`](anomaly-log.md), whose status there is `PENDING — Q-4`.
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
$C /repo/harness/seed.sh                  "$S"
$C /repo/harness/run_cobol_scenario.sh    "$S"
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

**(d) Resolution.** None, and deliberately none: this is the entry where choosing the coherent answer would
be most tempting and least detectable. `acas_posting/records/gl_batch.py` builds the layout from the
declared pictures — the field sum — and says at its own site that the choice is `Q-4`'s to make, so the
assumption is visible in the code rather than buried in it.

**(e) Consuming module.** `acas_posting/records/gl_batch.py`. Read at the parity tier by
`tests/arithmetic/test_control_total_comparison.py` and `tests/arithmetic/test_comp3_packed_decimal.py`,
which assert the reference rather than the layout.

<a id="q-5"></a>

### `Q-5` — the unexplained move

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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

Cross-reference: **A-17** in [`anomaly-log.md`](anomaly-log.md), whose status there is
`PENDING — Q-A17-POSTINGS-EFFECT` — the mnemonic identifier `acas_posting/programs/pl060_order_posting.py`
opened for the same question's *value* half. See §15 for how the two identifiers relate.

**(c) Oracle experiment.** Under the §10 protocol, run **each of the four programs** with the IRS fan-out
pinned to **each of its three states**, because the guard tests `IRS-Both-Used OR G-L` and the state decides
whether the move executes at all:

```text
# For each of the three IRS-Instead states, and each of the four programs:
$C /repo/harness/seed.sh                  "$S"      # $S pins IRS-Instead in the system row
$C /repo/harness/run_cobol_scenario.sh    "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables GLPOSTING-REC,PSIRSPOST-REC,GLBATCH-REC,SYSTEM-REC
$C /repo/harness/normalize.py  --scenario "$N" --side cobol
```

The three states are `IRS-Instead = "Y"` (`IRS-Used`), `"B"` (`IRS-Both-Used`) and any third value, which
is neither — `[copybooks/wssystem.cob:L179-L181]`. Then run the Python side with the equivalent move
present and again with it absent, and diff:

```text
$C /repo/harness/run_python_scenario.sh   "$S"
$C /repo/harness/diff_states.py --scenario "$N" --scenario-file "$S"
```

**The observable is every column of the posting record, plus any column `postings` can reach.** The
decisive question is whether `postings` is *stored anywhere* — if the diff is empty with the move present
and also empty with it absent, the statement is observably inert and that is a real result. If either diff
is non-empty, record which column moved. Note that `RRN` may exceed `postings`' picture, in which case the
stored value is a truncation rather than a copy; that value half is
`Q-A17-POSTINGS-EFFECT` (§14) and is measured by the same run.

**(d) Resolution.** None. The status stands. The move is reproduced in all four program modules exactly as
written, including the wrong-program comment carried forward as a comment, because R-4 requires the artefact
and not a tidied version of it. Nothing is normalised across the four, and in particular the `sl060`
missing period is **not** repaired to match its three siblings.

**(e) Consuming modules.** All four Sales and Purchase posting program modules:
`acas_posting/programs/sl060_invoice_posting.py`, `acas_posting/programs/sl100_cash_posting.py`,
`acas_posting/programs/pl060_order_posting.py` and `acas_posting/programs/pl100_payment_posting.py`.

---

### The `Q-5.x` storage-semantics cluster

Three questions about how a value is *represented* rather than how it is computed. They share a cluster
number because they share an owner — `acas_posting/cobol/usage.py` — and because all three are settled by
the same class of observation: write a known value through the bridge and look at what arrives.

⚠️ **All three carry a provisional implementation, and none carries a measurement.** `usage.py` labels each
of them "RESOLVED" at its own site. That label means *settled for implementation purposes from the
documented default or from the ISO reading* — it does not mean observed, and the module does not claim it
does. **Under R-6 only an observed run promotes a status**, so this register keeps all three
`PENDING — AWAITING ORACLE EXECUTION` and states the provisional choice explicitly, with its basis, so that
the oracle can confirm or overturn a named value rather than an implication. Recording the two facts
together — what the code does, and that nobody has watched the compiler agree — is the only presentation
that misleads neither a reader of this register nor a reader of that module.

<a id="q-5-1"></a>

#### `Q-5.1` — GnuCOBOL default `binary-size` and `binary-truncate`

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

**(a) The question.** With no dialect selected, the compiler's **defaults** govern two separate things for
every `COMP`, `BINARY-CHAR`, `BINARY-SHORT` and `BINARY-LONG` field: how many **bytes** the item occupies
(`binary-size`), and whether a store is reduced to the item's **declared digit count** or to its **byte
capacity** (`binary-truncate`). Neither is stated anywhere in the repository, and the two are independent —
a field can be eight bytes wide and still refuse an eighteenth digit.

**(b) Evidence.** The absence, counted in §9: no `-std=`, no `>>SET ARITHMETIC`, no `binary-truncate`
anywhere in the frozen sources. The compiler is GnuCOBOL **3.2 final** — `[common/comp-common.sh:L9]`,
`[README.TXT:L53]`.

The exposure, from the `copybooks/` census of §9: `binary-long` **166** declared, `binary-char` **84**,
`binary-short` **32**, and bare `comp` **236**. The two questions therefore reach several hundred fields,
including `Run-Date` itself at `[copybooks/wssystem.cob:L67]` and the whole of the narrowed block that
`Q-3` is about.

**The provisional implementation, named so it can be overturned.** `acas_posting/cobol/usage.py` carries
`DEFAULT_BINARY_SIZE_THRESHOLDS` as `(2 digits → 1 byte, 4 → 2, 9 → 4, 18 → 8)` and `BINARY_TRUNCATE = True`,
the module's own comment noting that setting the flag false would make a `COMP` store reduce into its byte
capacity instead of its digit count. That is the documented GnuCOBOL default, transcribed; it is **not** a
measurement.

**(c) Oracle experiment.** Under the §10 protocol, seeding values **at and beyond each declared digit
count** for one field of each width:

```text
$C /repo/harness/seed.sh                  "$S"
$C /repo/harness/run_cobol_scenario.sh    "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables SALEDGER-REC,GLBATCH-REC,SYSTEM-REC
```

For each width, three seeds: the largest value the declared digits admit, that value plus one, and the
largest value the byte capacity admits. A `binary-long` declared as eight digits accepts `99999999`; the
byte capacity accepts `2147483647`. **The observable is which of the two ceilings the stored column
respects** — a store that survives `999999999` has truncated to capacity, and one that wraps or clips at
`99999999` has truncated to digits. Read as `int`, never through a float (R-2). Repeat at `binary-short`
and `binary-char` widths, because the policy may not be uniform across them.

**(d) Resolution.** None. The provisional values above are what the Python side computes today; the
experiment exists to confirm or replace them.

**(e) Consuming module.** `acas_posting/cobol/usage.py`. Test-owned by
`tests/arithmetic/test_comp_binary.py`, which records the absence census in its own header and marks the
propositions that depend on the answer rather than asserting them.

<a id="q-5-2"></a>

#### `Q-5.2` — the byte length of a `SIGN LEADING` display item

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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
$C /repo/harness/seed.sh                  "$S"
$C /repo/harness/run_cobol_scenario.sh    "$S"
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

**(d) Resolution.** None, and it must stay none: `tests/arithmetic/test_sign_leading_display.py` refuses to
assert either width as fact and holds the question open with a strict expected failure, so that whichever
way the oracle settles it the suite reacts rather than silently agreeing. Note that the byte account of
`Q-4`'s Sibling 2 does **not** depend on this answer — neither money field carries a `sign leading` clause in
the *current* declaration, and the ten bytes each occupies is corroborated by Reading C.

**(e) Consuming module.** `acas_posting/cobol/usage.py`. Test-owned by
`tests/arithmetic/test_sign_leading_display.py`;
`tests/arithmetic/test_irs_date_component_derivation.py` cross-references it and deliberately checks sign
*position* and *spelling* only, never `byte_length`.

<a id="q-5-3"></a>

#### `Q-5.3` — the overpunch and packed-decimal byte values

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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

**(d) Resolution.** None. The provisional tables above are what the Python side uses today, and they are
named here so the oracle confirms or replaces a concrete value rather than an implication.

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

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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

**(c) Oracle experiment.** Under the §10 protocol, run the Sales invoice-posting scenario on both sides with
the autogen switch off, and bound the observation by the autogen tables:

```text
$C /repo/harness/seed.sh                  harness/scenarios/clean_batch_sl.yaml
$C /repo/harness/run_cobol_scenario.sh    harness/scenarios/clean_batch_sl.yaml
$C /repo/harness/dump_tables.py --scenario clean_batch_sl --side cobol \
       --tables SAAUTOGEN-REC,SAAUTOGEN-LINES-REC,PUAUTOGEN-REC,PUAUTOGEN-LINES-REC
```

**The observable is that all four autogen tables are still empty after the COBOL run**, and empty again
after the Python run. The four tables are never seeded, never appear on any scenario's affected-table list,
and are named here **only** as tables asserted to remain empty — they are out of scope and nothing in the
migration writes them. Then run the scenario end to end and confirm the stage-8 diff is empty, which is the
statement that `sl830`'s presence on one side changed nothing anywhere.

Repeat once with the autogen switch **on**, not to compare the two sides — `sl830` has no Python
counterpart, so that comparison is meaningless — but to establish that the switch is what gates the
program, and therefore that the scenarios' setting of it off is load-bearing rather than incidental.

**(d) Resolution.** None. **The expectation, labelled as an expectation:** `[sales/sl830.cbl:L269-L270]`
returns immediately with the switch off, so the four autogen tables should be observed unchanged and the
diff should be empty. ⚠️ **That "no-op" claim must be verified against the oracle (R-6), not assumed.** It is
a reading of one guard at the top of one section, and a program that returns early can still have done
something before it — opened a file, written a log row, advanced a counter in the system record. Until the
run says otherwise, the status is `PENDING`.

**(e) Consuming modules.** `harness/run_cobol_scenario.sh` and `harness/run_python_scenario.sh` (AAP
§0.4.1.7), which are the two halves of the route difference and the two places an assertion about the
autogen tables belongs.

<a id="q-7"></a>

#### `Q-7` — the menu shells' exit-path rewrite

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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

**The Python CLI does none of this.** It has no menu, so it has no exit path to hang the paragraph off.

**(c) Oracle experiment.** Under the §10 protocol, with the observation bounded by the scenario's own
affected-table list rather than by everything:

```text
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol --scenario-file "$S"
```

`harness/dump_tables.py` reads the scenario's `affected_tables` list from the YAML and dumps exactly those
tables; `harness/scenarios/clean_batch_gl.yaml` declares its list at `L585`. Run the full eight stages for
each of the four clean-batch scenarios, then **also** dump the three system tables outside the affected list,
as a separate observation, and compare them against the seed:

```text
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables SYSTEM-REC,SYSDEFLT-REC,SYSTOT-REC
```

**The observable is which columns of those three tables differ from the seeded values after a COBOL run that
the Python run cannot reproduce.** That is the size of the problem, stated as a column list rather than as a
worry.

**(d) Resolution.** None. **The proposed resolution, and the reason it is proposed rather than adopted:**
bound the comparison by the scenario's affected-table list, which is what `harness/dump_tables.py` already
does when invoked with the scenario file. A row the scenario does not claim to be about is not evidence
about the scenario. That is sound as far as it goes, and it is the mechanism in place — but it is a
*containment*, not an answer, and the answer is the column list the experiment produces.

⛔ **It must never be resolved with an ignore-list inside `harness/diff_states.py`.** That module is required
to have none, and it says so itself: `[harness/diff_states.py:L2441]` records *"no ignore-list"* as a
property of the comparison, and `[harness/diff_states.py:L1632]` names an ignore-list as **forbidden by rule
R-4**. The distinction matters and is not pedantic: choosing which tables a scenario is *about* is scoping,
declared in the scenario and reviewable there; teaching the differ to overlook a difference it found is
suppression, invisible at the point of use, and it would silently swallow a real regression in the same
column later.

⚠️ **An honest overlap, stated plainly rather than buried.** `SYSTOT-REC` **is** genuinely in scope for the
`period_end_totals` scenario — it is that scenario's focal table, declared as such at
`[harness/scenarios/period_end_totals.yaml:L592]`, because the nine period-total write sites are its sole
writers. So for one of the eight scenarios the containment above does **not** apply: the table the menu
rewrites on exit is the table the scenario exists to compare. That scenario cannot be made safe by scoping,
and its diff depends on this question's answer.

**(e) Consuming modules.** `harness/dump_tables.py` and `harness/diff_states.py` (AAP §0.4.1.7). Related but
distinct, and catalogued in §14: `Q-CLI-OVERREWRITE` and `Q-CLI-OVERREWRITE-SECOND-LEG`, which ask whether
the Python CLI should reproduce the paragraph at all.

<a id="q-8"></a>

#### `Q-8` — `Post-Date (7:2)`: a year, or a century?

**Status: `PARTIALLY RESOLVED`.** The Sales path is settled **by construction**; any caller that truncates
instead is open.

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
$C /repo/harness/seed.sh                  "$S"
$C /repo/harness/run_cobol_scenario.sh    "$S"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol \
                               --tables IRSPOSTING-REC,GLPOSTING-REC,PSIRSPOST-REC
```

**The observable is the stored `POST4-YEAR` column against the stored `POST4-DAT` text, per caller.**
`POST4-YEAR = 25` with `POST4-DAT = "21/09/25"` is the composing route; `POST4-YEAR = 20` with
`POST4-DAT = "21/09/20"` is the truncating route. Record the pair for every caller, not a single
representative one — the whole question is whether the callers agree.

**(d) Resolution.** Part-settled. The **Sales** path holds the year, by construction, from
`[sales/sl060.cbl:L1071-L1072]`. Whether **every** in-scope caller uses the composing route rather than a
truncating move is **open** and must be arbitrated by the oracle.

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

**Status: `PARTIALLY RESOLVED`.** The convention that explains the omission is stated by the maintainer;
the doubt that unsettles it is stated by the same maintainer, about the same field. **Both are recorded and
neither is chosen.**

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
$C /repo/harness/seed.sh                  harness/scenarios/clean_batch_gl.yaml
$C /repo/harness/run_cobol_scenario.sh    harness/scenarios/clean_batch_gl.yaml
$C /repo/harness/dump_tables.py --scenario clean_batch_gl --side cobol --tables GLPOSTING-REC
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

**(d) Resolution.** Part-settled, and the parts must be kept apart. **Settled:** the omission is consistent
with a stated, bridge-wide convention, cited twice, and the field's own history describes it as a
data-access-layer surrogate. **Open:** whether that convention is what the compiled bridge actually does with
the key, given that the same file warns the key of reference may be wrong. Neither reading is adopted.

**(e) Consuming modules.** `acas_posting/dal/acas006_gl_posting.py`, which owns the SQL for
`GLPOSTING-REC` and therefore decides what `POST-RRN` is written from, and
`acas_posting/dal/cursor_state.py`, which owns the `START` / `READ NEXT` emulation and therefore decides
which key the walk follows.

---

## 13. Deferrals handed up from the arithmetic tier

The parity tier reached a class of question it cannot answer and would not be honest to guess: **what the
compiled program produces where the language leaves the result undefined, or where the only observable is
one the migration does not have.** Each one is recorded here with the same five parts, in a more compact
form because the experiments share a shape.

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

<a id="q-sort-tie-order"></a>

### `Q-SORT-TIE-ORDER` — where the compiled sort places two records with an identical key tuple

**Status: `PENDING — AWAITING ORACLE EXECUTION`.** ⭐ This is the highest-consequence deferral in the
register.

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
$C /repo/harness/seed.sh                  harness/scenarios/clean_batch_gl.yaml
$C /repo/harness/run_cobol_scenario.sh    harness/scenarios/clean_batch_gl.yaml
$C /repo/harness/dump_tables.py --scenario clean_batch_gl --side cobol --tables GLPOSTING-REC,GLLEDGER-REC
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

**(d) Resolution.** None. `tests/arithmetic/test_ledger_balance_accumulation.py` carries the question text in
its own `OPEN_QUESTIONS` mapping and asserts the propositions that do **not** depend on the answer, marking
the one that does.

**(e) Consuming modules.** `acas_posting/cobol/sortverb.py`, which guarantees stability, and
`acas_posting/programs/gl071_batch_sort.py`, which invokes it on the identical four-key tuple. Test-owned by
`tests/arithmetic/test_ledger_balance_accumulation.py`.

<a id="q-gl080-divide-by-zero"></a>

### `Q-GL080-DIVIDE-BY-ZERO` — what the compiled program does when the cycle divide has a zero divisor

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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
*abort* and *zero*. It is recorded here **attributed and unpromoted**, for the same three reasons this
register does not promote `Q-OTM5-NARROW` (§14.4): the measurement belongs to the tier that took it and its
provenance must stay visible; **this register observed no run**, so adopting it would breach the honesty
mandate of §2 and R-6 alike; and §10.1 records that the oracle cannot presently be built at all, so no run is
available to this register to confirm it against. The status below therefore stays `PENDING`, and if the
oracle run confirms the arithmetic tier's measurement then this entry closes by citing it rather than by
restating it.

**(c) Oracle experiment.** Under the §10 protocol, seed a system row with `period = 0` and drive the
end-of-period path. ⚠️ Note the §16 declination: **no mandated scenario drives `gl080`**, so this experiment
needs a scenario of its own, and building one is part of the experiment rather than a precondition of it.

```text
$C /repo/harness/seed.sh                  "$S"      # $S seeds period = 0
$C /repo/harness/run_cobol_scenario.sh    "$S"
echo "exit=$?"
$C /repo/harness/dump_tables.py --scenario "$N" --side cobol --tables GLLEDGER-REC,SYSTEM-REC
```

**Two observables, and the first is the process exit code**, because "abort" is one of the three candidate
answers and a table dump cannot show it. Then the stored `LEDGER-Q1` … `LEDGER-Q4` columns, which reveal
which subscript the divide's result selected — that is `Q-QUARTER-SUBSCRIPT`'s subject, measured by the
same run.

**(d) Resolution.** None. No guard is added on the Python side; the divide is reproduced as written.

**(e) Consuming modules.** `acas_posting/cobol/arithmetic.py` and
`acas_posting/programs/gl080_end_of_cycle.py`. Test-owned by
`tests/arithmetic/test_gl080_cycle_divide_rounded.py`.

<a id="q-quarter-subscript"></a>

### `Q-QUARTER-SUBSCRIPT` — what the compiled program writes when the quarter subscript is out of range

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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

**(d) Resolution.** None. The subscript is left unbounded (R-3, R-4) and the divergence — that Python raises
where COBOL overwrites — is declared at the site rather than smoothed away by a guard.

**(e) Consuming module.** `acas_posting/programs/gl080_end_of_cycle.py`. Test-owned by
`tests/arithmetic/test_gl080_cycle_divide_rounded.py`.

<a id="q-rounded-overflow-order"></a>

### `Q-ROUNDED-OVERFLOW-ORDER` — whether a `ROUNDED` store rounds before or after it overflows

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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

**(d) Resolution.** None. **The provisional order, named:** the semantics layer **rounds first and then
discards**, so `99.5` stored into a `pic 99` receiver holds `0`. The alternative order would hold `99`, and
`tests/arithmetic/test_compute_rounded_half_up.py` asserts *that* as a strict expected failure — so whichever
way the oracle settles it, the suite reacts rather than silently agreeing.

**(e) Consuming module.** `acas_posting/cobol/arithmetic.py`. Test-owned by
`tests/arithmetic/test_compute_rounded_half_up.py`.

<a id="q-edited-blank-when-zero"></a>

### `Q-EDITED-BLANK-WHEN-ZERO` — the characters an edited picture renders

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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

**(d) Resolution.** None for the rendering. One value *is* fixed and is asserted unconditionally rather than
deferred: the `z(7)9` rendering of **zero** — seven suppressed positions then the always-printing final `9`
— because it is the case that reaches a real column and the assertion is itself the lock.

**(e) Consuming modules.** `acas_posting/cobol/move.py` and
`acas_posting/programs/sl060_invoice_posting.py`. Test-owned by
`tests/arithmetic/test_move_truncation.py` and `tests/arithmetic/test_ledger_balance_accumulation.py`.

<a id="q-70f"></a>

### `Q-70f` — the on-the-wire sign of a negated zero

**Status: `PENDING — AWAITING ORACLE EXECUTION`.**

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

**(d) Resolution.** None.

**(e) Consuming modules.** `acas_posting/cobol/arithmetic.py` and `acas_posting/cobol/usage.py`.
Test-owned by `tests/arithmetic/test_double_entry_explosion.py`, which marks it `xfail(strict=True)` — so
if the oracle confirms the negative overpunch the test XPASSes and forces the resolution to be recorded here.

<a id="q-string-pointer-and-refmod"></a>

### The three that are handed **down**, not up — questions the semantics layer already owns

Three deferrals in the brief for this file are owned by `acas_posting/cobol/move.py`'s register (§5), and
are **cited here by scope rather than re-issued**, because re-numbering them would strand fourteen
citations. Each is recorded with what its owner measured, so a reader of this register is not sent looking:

| Identifier and owner | Question | What the owner records |
| --- | --- | --- |
| **`Q-9` (`cobol/move`)** — ⚠️ *not* this register's `Q-9`; see §15 | `MOVE SPACE` into a numeric receiver | **INEXPRESSIBLE** — measured as a GnuCOBOL 3.2 compile error, so the statement cannot exist in the compiled system and there is no representation to reproduce |
| **`Q-10` (`cobol/move`)** | a reference-modification range past the end of the item | **UNREPRODUCIBLE** — a literal out-of-range range does not compile, and a computed one reads **adjacent storage**, which a Python `str` does not have |
| **`Q-11` (`cobol/move`)** | a `STRING` pointer beyond the receiver | measured as a **silent no-op**: nothing is written **and** the pointer does not advance |

`Q-11`'s live site in the frozen source is worth naming, because it is the one the maintainer himself
flagged. `[general/gl080.cbl:L530]` is `move space to Arg-Test.` carrying the inline comment
`*> this lot looks wrong !!!!!`, and it introduces a five-source `STRING` at
`[general/gl080.cbl:L531-L536]` whose result is then moved into the **shorter** `file-2` at
`[general/gl080.cbl:L537]` — the truncation on that final move being the maintainer's concern. That is
**A-NEW-9**. It sits in the archive-path construction, which produces no database effect, so it is recorded
rather than locked, and `Q-22` (§14) owns what path the statement actually builds.

⚠️ Each of the three is marked `xfail(strict=True)` by `tests/arithmetic/test_move_truncation.py` against
the **naive** reading — what an engineer would guess before consulting the compiler. Because the strictness
is on, the day a naive reading starts holding, the test **XPASSes and the suite goes red**. That is the
R-4/R-6 lock working, and it is why these three are recorded as measured by their owner while this register
still refuses to promote any status of its own without a run.

---

## 14. The wider register — identifiers opened elsewhere in the migration

The migration was written by many hands, and modules opened questions at the sites where they hit them. Every
`Q-` identifier cited anywhere in the repository is catalogued below so that **no citation dangles**, which
is R-5 applied to this register itself. Entries here are **not re-opened and not re-numbered**: each records
the question its owner named, the owner, and the state the owner reports. Where an owner reports a
measurement, that is recorded as *their* report — this register has observed none (§10.1).

### 14.1 The numeric band `Q-10` … `Q-25`

| id | Question | Owner | State as its owner reports it |
| --- | --- | --- | --- |
| `Q-10` | a reference-modification range not wholly inside its item | `acas_posting/cobol/move.py` | UNREPRODUCIBLE — a literal range does not compile, a computed one reads adjacent storage |
| `Q-11` | a `STRING` pointer beyond the receiver | `acas_posting/cobol/move.py` | measured as a silent no-op; the pointer does not advance |
| `Q-14` | an edited picture outside the Z-then-9 shape | `acas_posting/cobol/move.py` | UNOBSERVABLE — every other edited picture in the frozen sources receives into a print line |
| `Q-15` | whether `gl071`'s `SYSTEM-REC` parameter is ever tested; it is imported for the parameter's declaration and never read | `acas_posting/programs/gl071_batch_sort.py` at `L24-L26` | marked at the site |
| `Q-16` | what a `tinyint(2) unsigned` column holds, and what a predicate comparing it against the **quoted** three-digit string `"000"` actually compares — `HV-IRS-FINAL-ACC-REC-KEY` is `PIC 9(03) COMP` written into a two-digit column | `acas_posting/dal/acasirsub5_irs_final.py` | transport-level; both renderings reproduced as written, nothing normalised |
| `Q-17` | what the table holds, and what a read returns, when fewer than 26 rows exist — the bridge tolerates a short table by design | `acas_posting/dal/acasirsub5_irs_final.py` | measured behaviour of the compiled system, not inferred; note the state after **any** write is dense, all 26 rows, blanks stored as spaces |
| `Q-18` | whether `move 1 to File-Key-No` at `[general/gl080.cbl:L288]` has any observable effect, given the facade's own dispatch paragraphs pin the same value before every call | `acas_posting/programs/gl080_end_of_cycle.py` | reproduced regardless |
| `Q-19` | what the compiled program writes when the quarter subscript is out of range | `acas_posting/programs/gl080_end_of_cycle.py` | the divergence is declared, no guard added — see §13's `Q-QUARTER-SUBSCRIPT`, which is the same site from the subscript's side |
| `Q-20` | whether `GL-Posting-Open-Output` at `[general/gl080.cbl:L673]` **truncates** `GLPOSTING-REC`, as `Open-Output` does on the transfer-file handler | `acas_posting/programs/gl080_end_of_cycle.py` | open; `Q-23` says the statement is unreachable in the frozen source, which does not settle what it would do |
| `Q-21` | whether this program's system-record mutations are persisted at all — `gl080` performs **no** `System-*` facade verb, so it depends entirely on what the caller does with the by-reference parameter | `acas_posting/programs/gl080_end_of_cycle.py` | all reproduced in memory; none written to a table from there |
| `Q-22` | what path the `disk-change` `STRING` actually builds — the maintainer's own `*> this lot looks wrong !!!!!` at `[general/gl080.cbl:L530]` | `acas_posting/programs/gl080_end_of_cycle.py` | measured against the package's record defaults as `"archives archive.dat"`, a space where a separator belongs; reproduced exactly as written |
| `Q-23` | whether `compress-post` aborts the run in the COBOL-files configuration | `acas_posting/programs/gl080_end_of_cycle.py` | the two record lengths measure 103 and 101, so `stop run` at `[general/gl080.cbl:L649]` fires; computed from the descriptors, never from a literal |
| `Q-24` | the facade argument list and the per-handler record operand for the IRS calling convention — five operands in the copybook's own order | `acas_posting/programs/irs030_posting.py` at `L1217-L1229` | marked at the site |
| `Q-25` | which callers of the bridge put a two-digit **year** in `Post-Date (7:2)` and which put a **century** | `tests/arithmetic/test_irs_date_component_derivation.py` at `L128-L135`, declared *"OWNED HERE"* | the Sales path closed by construction; open for any other caller — **the same question as this register's `Q-8`**, see §15 |

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

Opened by `acas_posting/cli/args.py` and the six entry points, at the boundary where a menu paragraph becomes
a command line. Several are **settled by their owner**, and the settled ones are recorded as such because a
reader following a citation needs to know it is closed.

| id | Question | State as its owner reports it |
| --- | --- | --- |
| `Q-CLI-SYSREC-LOAD` | whether loading and persisting the system record belongs to the route at all, given no in-scope posting program performs system-record I/O | SETTLED, and settled the other way from an earlier reading: the route is the menu's counterpart, so the route loads and persists |
| `Q-CLI-SYSREC-PINS` | whether the CLI's pins should be re-applied over the loaded row | OPEN — forced for the six connection fields; for `Run-Date`, `Date-Form` and `IRS-Instead` it means the CLI wins, so a scenario must seed those three to agree with the options it passes |
| `Q-CLI-SYSREC-RUNDATE` | that the row's `RUN-DATE` is written once at record-creation time by the out-of-scope `common/sys002.cbl`, and no menu ever writes it | OPEN |
| `Q-CLI-RUNDATE-VS-ROW` | that the frozen menus derive the text date from the row they just read and never write `RUN-DATE` back, so a scenario must pin `--run-date` to the seeded value for the two cycles to be comparable at all | STILL OPEN |
| `Q-CLI-EXITSTATUS` | what process status the frozen system produces | SETTLED by establishing that **there is no oracle observable**: `RETURN-CODE` is read and never written anywhere in the menus or the twelve programs, and each menu ends with a bare `goback` |
| `Q-CLI-OVERREWRITE` | whether the Python route has any counterpart to the menu's exit-time rewrite | SETTLED at three of the entry points by reproducing the paragraph; OPEN at `pl_payment_post` — this register's `Q-7` asks the complementary question, what the rewrite *writes* |
| `Q-CLI-OVERREWRITE-QUIT` | whether a single-operation process has a counterpart to the menu's quit-time rewrite | SETTLED by reproducing the paragraph: the quit key is the only exit `display-menu.` has, so one operation per process means one persist per process |
| `Q-CLI-OVERREWRITE-SECOND-LEG` | the omitted COBOL half zeroes `File-System-Used` and never restores it, which under a literal reading puts a second dispatch on the indexed leg | STILL OPEN — measure which leg the oracle's second dispatch takes |
| `Q-CLI-TERMCODE-1-7` | the reachability of the 1..7 termination-code band | OPEN |
| `Q-CLI-OKTOPOST` | what CLI default preserves a prompt that has **no** defaultable answer | RESOLVED: none does, so the switch is required with no default; an earlier draft answered `True`, which would have invented the one answer that silently enables every database write on the route |
| `Q-CLI-CLEARFILE` | whether the `[Y]` in the IRS end-of-job prompt makes `Y` the effective default | RESOLVED by reading rather than by the prompt's appearance: the accept at `[irs/irs030.cbl:L1717]` carries no `WITH UPDATE`, so the literal stays in the prompt text and a bare Enter **re-prompts** rather than clearing |
| `Q-CLI-IRS-RUNDATE` | whether `irs030` reads the run-date field the IRS menu prepares before every option | STILL OPEN, and deliberately so — nothing provisional executes at the site |
| `Q-CLI-GL080-DEFAULTS` | the observed **database effect** of each of `gl080`'s three promoted interactive parameters | OPEN — in particular that `--disk-change-option 9` leaves `GLPOSTING-REC`, `GLBATCH-REC` and `GLLEDGER-REC` exactly as the seed left them. See §16 |

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

| id | Question | Locator |
| --- | --- | --- |
| `Q-A` | the width inflations, as `9(5)` sources travel through `9(08)` host variables | `L507` |
| `Q-B` | the money path at the column's precision limit | `L522` |
| `Q-C` | the key predicate: the key metadata declares `"STR"`, and the coercion its owner reports as **numeric**, measured on MariaDB 10.11.7 | `L535` |

### 14.4 The remaining mnemonic identifiers

| id | Question | Owner |
| --- | --- | --- |
| `Q-A17-POSTINGS-EFFECT` | the stored value of `postings` once `RRN` has advanced past its picture — the **value** half of this register's `Q-5`, and the identifier **A-17** carries in [`anomaly-log.md`](anomaly-log.md) | `acas_posting/programs/pl060_order_posting.py` |
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

§5 establishes that three registers coexist and were numbered independently. This section tabulates every
collision, so that a reader following a citation lands in the right place. **Nothing is renumbered** — the
citations are load-bearing, and moving a number to tidy a table would break a suite silently, which is the
failure mode this whole register exists to prevent.

**The scoping rule.** An **unqualified** `Q-n` means *this* register. A citation found inside a module or
test that declares a register of its own resolves *within that file*. Where ambiguity is possible, the
qualified form — `Q-9 (cobol/move)` — is used.

| Number | This register's reading | Other readings, with the citing file |
| --- | --- | --- |
| `Q-1` | the date module's reject contract | *"THIS FILE'S register"* in `tests/arithmetic/test_irs_vat_from_net.py` at `L143` — an unsized-overflow question; `acas_posting/programs/gl051_batch_control_check.py` — whether persisting `Batch-Status` is the caller's job, which that module reports **resolved from the source**; `acas_posting/programs/sl060_invoice_posting.py` — which `oi-type` values reach the loop; `acas_posting/programs/pl100_payment_posting.py` — a status pair and row state |
| `Q-2` | default arithmetic precision | the same question, and the **shared** reading, in `acas_posting/cobol/arithmetic.py` at `L96` and in five arithmetic tests. `gl051_batch_control_check.py` and `sl060_invoice_posting.py` also keep local `Q-2` entries on other subjects |
| `Q-3` | the signed-to-unsigned stored value | the same question in the dictionary's `ambiguity_refs`, in `acas012_sales.py`, `acas007_gl_batch.py`, `records/sales_ledger.py` and four arithmetic tests — **the shared reading**. `gl051_batch_control_check.py` and `sl060_invoice_posting.py` keep unrelated local `Q-3` entries |
| `Q-4` | the batch record's length contradiction | the same question in the dictionary's `ambiguity_refs`, in `records/gl_batch.py`, `acas007_gl_batch.py` and three arithmetic tests — **the shared reading**. `sl060_invoice_posting.py` and `pl100_payment_posting.py` keep unrelated local `Q-4` entries |
| `Q-5` | the unexplained move | its **value** half is `Q-A17-POSTINGS-EFFECT` (§14.4), which is the identifier **A-17** carries |
| `Q-9` | `HV-POST-RRN` declared and fetched but never loaded | ⚠️ **the sharpest collision.** `acas_posting/cobol/move.py` and `tests/arithmetic/test_move_truncation.py` publish a `Q-9` meaning *`MOVE SPACE` into a numeric receiver*; `gl051_batch_control_check.py` publishes a local `Q-9` meaning *A-15's record-length contradiction*, which is **this register's `Q-4`**; and `sl060_invoice_posting.py` publishes a third. Resolved by scoping only — see §13's handed-down table for the `cobol/move` reading |
| `Q-8` | `Post-Date (7:2)`: year or century | **the same question** as `Q-25` (§14.1), which `tests/arithmetic/test_irs_date_component_derivation.py` declares *"OWNED HERE"*. The two are **aliases**, not rivals: `Q-8` is the register entry and `Q-25` is the owning test's identifier for the same subject, with the same split — Sales closed by construction, other callers open. Both are kept so that neither a document citation nor a test citation dangles |
| `Q-6` | the `sl830` asymmetry | `acas_posting/programs/sl060_invoice_posting.py` keeps a local `Q-6`; `acas_posting/cli/sl_cash_post.py` records that its program module carries the ok-to-post question as *its own* `Q-6` |
| `Q-7` | the menu-shell exit-path rewrite | ⚠️ **the collision this register could not absorb.** `tests/arithmetic/test_gl080_cycle_divide_rounded.py` and `tests/arithmetic/test_compute_truncate_unrounded.py` both publish a `Q-7` meaning *the zero divisor*, carried on `acas_posting.cobol.arithmetic.SizeErrorNoStore`. §12's `Q-7` is externally mandated to the menu-shell rewrite and the arithmetic tier's citations are equally fixed, so **neither could yield the number**: the zero-divisor question is filed in §13 under the mnemonic `Q-GL080-DIVIDE-BY-ZERO`, which is an **alias** for the arithmetic tier's `Q-7` and not a new question. `Q-CLI-OVERREWRITE` and `Q-CLI-OVERREWRITE-SECOND-LEG` (§14.2) are this entry's neighbours at the CLI boundary |

**Why the collisions were not simply prevented.** Because the register was being written at the same time as
the modules that cite it, and there was no shared allocation point until this file existed. One module solved
it properly by construction — `acas_posting/dal/acasirsub4_irs_posting.py` chose **letters** (§14.3) — which
is the pattern to follow for any question opened from now on: either take the next free number **in this
register**, or use a mnemonic that cannot collide.

---

## 16. Scope declinations, recorded honestly

Three items below are **not ambiguities in the frozen source**. They are decisions this migration took about
what to exercise and what to trust, and they are recorded here rather than left implicit because each one
would otherwise be read as coverage that does not exist. A silent declination and a fabricated resolution
fail in the same direction: both let a reader believe something has been checked.

### 16.1 `gl080` is driven by **no scenario at all**

**The declination.** The end-of-period path is not exercised by any of the eight mandated scenarios. Their
declared operations are `gl_post_cycle` for four of them — `clean_batch_gl`, `control_total_mismatch`,
`empty_batch` and `mixed_accepted_rejected` — `sl_invoice_post` for two, `pl_order_post` for one and
`irs_post` for one. **`gl_end_of_cycle`, which is the route that dispatches `gl080`, is the operation of
none of them** (verified by reading the eight definitions). And `system.period` is seeded as `1` in **all
eight**, which is inert for this purpose: with a period of one the cycle-to-period divide has nothing to
decide.

**The rationale, and its limit.** The eight scenarios are the set AAP §0.8.5 mandates — clean batch per
ledger, mixed accepted-and-rejected, period-end totals, control-total mismatch, empty batch — and none of
those five is an end-of-period run. So the declination follows the mandate rather than contradicting it. Its
limit is worth stating plainly: **three of this register's questions live in `gl080`** —
`Q-GL080-DIVIDE-BY-ZERO`, `Q-QUARTER-SUBSCRIPT`, and `Q-2`'s fifth `ROUNDED` site at
`[general/gl080.cbl:L328]` — plus five of §14.1's (`Q-18` … `Q-23`). Every one of them therefore needs a
scenario that does not exist yet, and **building it is part of those experiments** rather than a precondition
somebody else has met.

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
question — which is what every `PENDING` status in §12 and §13 is doing.

---

## 17. Self-audit

Counted properties of this file, stated so that a reviewer can check them mechanically rather than take the
document's word for its own discipline. Each was verified at the time of writing.

| Property | Value |
| --- | --- |
| Primary entries in §12 | **12** — `Q-1` … `Q-5`, `Q-5.1` … `Q-5.3`, `Q-6` … `Q-9` |
| Entries in §13 | **6** of its own, plus one companion answer key, plus **3** cited by scope |
| Statuses in §12 | **10** × `PENDING — AWAITING ORACLE EXECUTION`, **2** × `PARTIALLY RESOLVED` (`Q-8`, `Q-9`) |
| Statuses in §13 | **6** × `PENDING — AWAITING ORACLE EXECUTION` |
| `RESOLVED BY ORACLE` used as a status | **0.** The string occurs **5** times — the opening box, twice in §4, §11's index statement and this row — every one of them talking *about* the status, none assigning it |
| `RESOLVED BY CONSTRUCTION` used as a whole-entry status | **0.** The two part-resolved entries carry their settled halves inside the entry, where the reading can be shown |
| Entries carrying all five template parts | **all of them.** Every §12 entry has (a) question, (b) evidence, (c) oracle experiment, (d) resolution-or-status and (e) consuming module(s) |
| Explicit anchors | **19** — one for each of the **18** entries (`q-1` … `q-9`, `q-5-1` … `q-5-3`, and one per §13 entry), plus one on §13's closing scoping table, so a bare `#q-n` citation resolves |
| `Q-` identifiers cited by the project | **82**, and **every one of them appears in this file** — §12, §13, §14 or §15. Census scope, stated so the figure is reproducible: the tracked text files of `acas_posting/`, `tests/`, `harness/`, `docs/`, `data_dictionary/` and the two manifests, under a pattern permissive enough to catch all four identifier forms of §5, excluding the family labels `Q-5.x` / `Q-70` / `Q-CLI` and the metasyntactic placeholder `Q-nn` that `acas_posting/programs/gl080_end_of_cycle.py` uses for *"`AMBIGUITY Q-nn` at the site that raises it"* |
| Identifiers this file uses **as register identifiers** | **86** — the 82 above plus exactly four that are register-only and each declared as such: `Q-12`, `Q-13` and `Q-70c`, documented as **unassigned** rather than missing, and `Q-GL080-DIVIDE-BY-ZERO`, the one **coined name** for an existing question (§13, §15) |
| Tokens outside the census, and why | **12** — `Q-TAX`, `Q-TAXES`, `Q-FICA-TAX`, `Q-CO-FUTA-LIAB`, `Q-ENDED`, `Q-Year`, `Q-mmdd` and five case variants are COBOL **data-item names** in the Payroll sub system, which AAP §0.2.2 excludes in its entirety. They are not register identifiers and are deliberately not catalogued. ⚠️ The seven forms are spelled out in the row above so the exclusion is checkable, which is why a naive `Q-` pattern over this file returns **93** tokens rather than 86: those seven are the **only** `Q-`-prefixed tokens anywhere in this file that are not register identifiers, and the family labels `Q-5.x` / `Q-70` / `Q-CLI` and the placeholder `Q-nn` are named for the same reason |
| Experiments described as having been run | **0** |
| Measured values claimed as this register's own observations | **0** |
| Experiments that instrument the frozen source | **0.** §3 lists the five permitted observables; none of them requires a change to a frozen file |
| Experiments that add a column, an index, a view or a probe table | **0** (R-3) |
| Experiments that report a value through a binary float | **0** (R-2) |
| Experiments that build inside the mounted checkout | **0.** §3's hazard note and §10's protocol both forbid it |
| Locators verified by direct reading of the frozen source | **all of them.** §8 lists the thirteen corrections that verification produced |
| Identifiers renumbered | **0.** §15 resolves every collision by scoping |
| Identifiers newly opened here | **0 questions.** Two were drafted under new mnemonics and both were then traced to identifiers the project already had: one became `Q-70f` when `gl070`'s own question family was found (§14.1a), and one — the zero divisor — is the arithmetic tier's `Q-7`, which §12's mandated `Q-7` prevents this register from using, so it keeps the mnemonic `Q-GL080-DIVIDE-BY-ZERO` as a declared **alias** (§15). **One name is coined; no question is.** |
| Third-party measurements recorded but **not** promoted to a resolution | **3** — `Q-OTM5-NARROW`'s magnitude finding (§14.4), the arithmetic tier's zero-divisor measurement (§13), and the provisional constants named in `Q-2`, `Q-3`, `Q-5.1`–`Q-5.3` and `Q-ROUNDED-OVERFLOW-ORDER`. Each is attributed to the tier that took it; none changes a status in this register |

Two properties that are deliberately **not** claimed, because claiming them would be the failure this file
exists to prevent:

- **That the questions are answered.** They are not. §10.1 explains why they cannot be yet.
- **That the expectations recorded under some `PENDING` entries are findings.** Where an entry says what the
  source *supports*, it labels that an expectation and says which half of it the source does not reach.

---

## 18. Companion documents

This register is one of four migration documents and deliberately does not duplicate the others. All four
are companion deliverables of the same single execution phase, per AAP §0.4.5 and §0.4.1.7.

| Document | What it carries | Why it is not here |
| --- | --- | --- |
| [`anomaly-log.md`](anomaly-log.md) | the twenty-two canonical reproduced defects, plus appended candidates, each with its locators and its reproducing module | R-4's register. This file carries the **questions**; that one carries the **known** wrong behaviours. Where a defect's stored value is unmeasured, its status there is `PENDING` plus a `Q-` cross-reference into here |
| [`traceability.md`](traceability.md) | program to module, paragraph to function, field to dictionary entry, with the `GO TO` class annotated at each transfer site | R-5's mapping tables. This file names a consuming module per entry and stops there |
| [`scenario-diff-evidence.md`](scenario-diff-evidence.md) | the empty-diff evidence, per mandated scenario | evidence of parity, which is a **measurement**. **Absent from the checkout at the time of writing** (AAP §0.2.1.3), and it cannot honestly exist before §10.1's blocker is cleared |

Further reading inside the repository, none of it modified by this work: `README-python-migration.md`
(AAP §0.2.1.4) for how to build the oracle, seed a scenario, run both cycles and diff them; and the
maintainer's own `README.TXT` and `Changelog` for the COBOL system's history — read throughout this register
and, per §3, never edited.
