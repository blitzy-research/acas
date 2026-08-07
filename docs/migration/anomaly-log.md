# ACAS Posting Cycle — Anomaly Log

This is the register of legacy defects that the Python 3.12 migration of the ACAS posting cycle
**reproduces on purpose**. Its governing rule inverts ordinary engineering judgement: a defect
reproduced is a success, and a defect fixed is a failure. Every entry below therefore records a
behaviour that is *wrong* by any normal standard and *right* by the only standard that applies
here — what the compiled COBOL does. If, while reading, you find yourself wanting to note that
something "should be corrected", stop: that instinct is precisely the failure mode this document
exists to prevent. The place to act on it is nowhere; the place to record it is here.

The register covers the twelve in-scope posting programs of the General, Sales, Purchase and IRS
sub systems, the handlers and bridges they reach, and the frozen copybooks, schema and build
scripts that surround them. Twenty-two entries are canonical (`A-1` … `A-22`); a further **eighteen**
are candidates discovered while writing the migration (`A-NEW-1` … `A-NEW-18`), and **six more** are
candidates that were discovered inside a single program module and are named after it
(`A-PL060-A` … `A-PL060-C`, `A-PL100-A` … `A-PL100-C`). All **twenty-four** candidates are kept in §15, a
separate section, so that the canonical numbering is never disturbed.

**The release this register describes.** `README.TXT` records the state as v3.3 pre-final, dated
2025-09-21 `[README.TXT:L36-L38]`, and eleven of the twelve in-scope programs carry their own version
in a `prog-name` literal — **seven at 3.3.00 and four at 3.3.01**. The four at 3.3.01 are exactly the
four Sales and Purchase posting programs across which A-1, A-10 and A-17 are drawn:
`[sales/sl060.cbl:L191]`, `[sales/sl100.cbl:L135]`, `[purchase/pl060.cbl:L139]` and
`[purchase/pl100.cbl:L125]`. The five General programs and the two extract programs are at 3.3.00, for
example `[general/gl080.cbl:L181]` — `77  prog-name           pic x(15)  value "gl080 (3.3.00)"`.
`irs030` is the exception and declares no such literal, noting instead at `[irs/irs030.cbl:L36]` that
the version is in working storage. Every locator below was read at that release.

---

## 1. Rules provenance

**There is no user rules document for this project, and there is no such file anywhere in the
checkout.** That is a fact about the repository, checkable at any time: no rules document exists under
any path, and the Agent Action Plan records the same absence in its own §0.7.1.

Do not go looking for a rules file. There is none. Stated plainly, as the absence requires: this
project has no rules document, and **enterprise-standard best practice therefore applies wherever
the Agent Action Plan is silent**. Nothing has been invented to fill the gap, and the absence is
not treated as permission to lower the bar.

The six binding rules of this engagement — **R-1 … R-6** — nevertheless exist. They live in the
**Agent Action Plan itself, §0.7.2**, as a labelled rules block inside the user's requirements, and
their exact wording is retrievable via **`review_prompt`**, *not* via `review_rules`.
Quoting AAP §0.7.1: *"downstream execution agents that need the exact wording must read it there."*

The reason both facts are recorded rather than one of them quietly dropped is AAP §0.7.4 **C-5**. Its
resolution is quoted here verbatim, picked up from the point at which it names the temptation —
ignoring the requirement-embedded rules block:

> *"because it arrived in the requirements rather than in a rules document would discard six binding constraints on a technicality. Equally, claiming a rules document exists when it does not would send downstream agents to an empty source. Recording both facts is the only resolution that misleads no one."*

---

## 2. The rules that govern this document

Sections 2.1 to 2.6 restate each governing rule and say how this document honours it. Rule text is
quoted verbatim where the Agent Action Plan requires it; nothing is paraphrased into a weaker form.

### 2.1 R-4 — Legacy anomalies reproduced, never fixed ★ primary owner of this document

> *"Defects present in the compiled behavior are part of the specification. A defect reproduced is a success; a defect fixed is a failure."*

The user statement AAP §0.8.2 preserves verbatim, and which is the origin of that rule:

> *"There is no test suite: compiled COBOL execution is the behavioral specification, defects included. A defect reproduced is correct; a defect fixed is a failure."*

R-4 prevails over ordinary engineering instinct — AAP §0.7.4 **C-3** says *"without exception"* —
and gives the reason:

> *"Any 'improvement' destroys that property and cannot be detected as a regression by any downstream consumer, because there is no correct answer other than what the old system produced."*

C-3 then says where engineering quality actually lives on this engagement. It is expressed
*"through the anomaly log, the anomaly-locking tests, and a comment at each reproduction site citing the COBOL locator — rather than through correction."* This document is the first of those
three. The second is the `tests/arithmetic/` and `tests/scenarios/` tiers mapped in §11. The third
is the per-site comment carried in each reproducing module, which cites the same locator this
register cites, so that a reader who arrives from either direction lands on the same frozen line.

### 2.2 R-1 — No COBOL at runtime

> *"The Python implementation must not execute, embed, or shell out to the COBOL programs. COBOL is the specification for the migration, not a runtime dependency of the result. The shipped artifact must run on a host with no COBOL compiler and no COBOL runtime present."*

Nothing in this document instructs or implies that the shipped package invokes COBOL. Where the
oracle is mentioned it is located in `harness/` and characterised as **out of process**. AAP §0.7.4
**C-1** states the arrangement:

> *"compiled COBOL is confined to `harness/`, invoked only as an out-of-process comparison and seeding utility by the test suites, and never appears on any import path or code path of `acas_posting/`."*

Two structural proofs, each verified in this checkout rather than assumed, and one argument that is
explicitly withdrawn:

- `pyproject.toml` publishes an explicit **allow-list** of shipped packages — `[tool.setuptools]`
  `packages` names only the seven `acas_posting*` packages plus the `acas_posting.data_dictionary`
  data directory — together with `include-package-data = false`. `harness` is on neither list, so
  it is excluded by construction rather than by an exclusion pattern that could be widened. Belt
  and braces: `harness` also appears in pytest's `norecursedirs` and `harness/*` in the coverage
  `omit` list.
- A search of `harness/*.py` for `import acas_posting` or `from acas_posting` returns **zero** hits, so
  the dependency does not run in the other direction either. This is the import-direction half of the
  proof and it is measured, not asserted.
- ⚠️ **What is deliberately NOT offered as a proof: the absence of `harness/__init__.py`.** An earlier
  revision of this section argued that because the directory has no `__init__.py` "there is no import
  path into it at all". That argument is invalid — PEP 420 makes a directory without `__init__.py` an
  implicit namespace package, so `import harness.diff_states` would resolve perfectly well from a
  process whose working directory is the repository root. The isolation is real, but it rests on the
  packaging allow-list and the measured import direction above, not on a missing marker file.
- The entire `tests/arithmetic/` tier needs **no Docker, no MariaDB and no GnuCOBOL**. It imports
  only `acas_posting.cobol`, `acas_posting.records`, `acas_posting.dictionary` and the standard
  library, and it passes on a bare host.

### 2.3 R-2 — Zero binary floating point

> *"No accounting value may pass through a binary floating-point type at any point — not in computation, not in storage, not in transport."*

R-2 governs entries **A-8**, **A-10** and **A-11** directly, because each is a *precision* defect
whose reproduction depends on modelling the exact storage class of the receiving field rather than
approximating it. Supporting facts, all verified against the frozen schema:

- `mysql/ACASDB.sql` contains **zero** `FLOAT`, `DOUBLE` or `REAL` columns.
- Its numeric census is **167 `DECIMAL`, 151 `INT`, 116 `TINYINT`, 23 `MEDIUMINT`, 22 `SMALLINT`
  and 3 `BIGINT`**.
- Its character census is **238 `char(` columns and zero `varchar(`**, which is why padding is
  observable in a table dump at all and therefore why A-12 matters.

AAP §0.5.1 records the dependency consequence:

> *"No `pandas` and no `numpy` — both compute in binary floating point by default, which is prohibited outright for accounting computation. This exclusion is absolute, including for the harness dump comparison, which uses ordered row sequences rather than dataframes."*

### 2.4 R-3 — No new validations, fields or schema changes; no concurrency

> *"The migration may not add validation logic, add fields, or alter the database schema, and must not introduce concurrent execution."*

R-3 is the reason this document may exist at all, so the resolution is quoted rather than
summarised. AAP §0.7.4 **C-2**:

> *"R-3 constrains the database, not the repository. Describing a schema in a committed artifact is orthogonal to altering it."*

Two consequences follow. First, this file is Markdown in the repository: it adds no table, no
column, no index and no DDL statement, and it introduces no migration tool. Second, the thirteen
frozen-script and frozen-file defects in §13 are **recorded, never fixed** — the harness works
around them, and the frozen files keep their defects.

### 2.5 R-5 — Full traceability

> *"Every program must map to a module, every paragraph to a function, and every field to a data-dictionary entry, and the mapping must be recorded as a document rather than left implicit in the code."*

Here R-5 obliges every entry to name the **reproducing Python module** that carries the defect
forward, and to cross-reference [`traceability.md`](traceability.md) rather than duplicate its
program-to-module, paragraph-to-function and field-to-dictionary tables. Field-level traceability
for the anomalies is already mechanised: the generated dictionary
`data_dictionary/acas_posting_dictionary.json` carries an `anomaly_refs` list on each affected
field entry, so the question "which fields does A-11 touch?" is answered by the artifact and not by
this prose. §10 quotes those counts where they are load-bearing.

### 2.6 R-6 — Compiled behavior is the tie-breaker

> *"Where a semantic question is ambiguous, the compiled program's observed behavior decides it, and each such resolution must be documented rather than settled silently."*

An anomaly can have a *shape* that is settled by reading the frozen source and a *stored value* that
is not. Where a stored value is still unmeasured the entry says
**`PENDING — AWAITING ORACLE EXECUTION`** and points at the matching `Q-` entry in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md). Where the value has since been watched on the
compiled oracle the entry says **`REPRODUCED — VALUE MEASURED`** and the companion `Q-` entry carries the
observation in full. No stored value is guessed anywhere in this document, and no `Q-` identifier is
invented: the ones cited are the identifiers already emitted by
`acas_posting/dictionary/generate.py` into the dictionary's `ambiguity_refs` lists, or already
carried by the sibling modules and tests.

**Measuring a value does not close the anomaly.** Five entries have been measured against the compiled
oracle — **A-2**, **A-11**, **A-14**, **A-15** and **A-17** — and all five remain in this log. Four of
them remain because the defect remains: knowing that an out-of-record subscript stores past the record
(A-2), that a narrowed sign becomes an absolute value (A-11), that the compiled tie order is input order
so the sequential read is right only by accident (A-14), or that an unexplained move wraps at 32767 and
reaches an unsigned column as a magnitude (A-17), tells you what the column holds and changes nothing
about whether the column is wrong. R-4 forbids repairing any of them. The fifth, **A-15**, is the one
case where measurement *dissolved* the uncertainty rather than pricing it — the compiled layout turned
out to be unambiguous and the maintainer's contradictory note simply false — and it stays because the
false note is still in the frozen copybook, where the next reader will hit it. §17's self-audit carries
the current status tally; it is not repeated here, because a count written in prose decays the first
time an entry is promoted.

---

## 3. The honesty mandate

AAP §0.4.5, verbatim:

> *"The traceability, anomaly and ambiguity documents are byproducts of writing the program modules and would be fabrications if written separately."*

Three commitments follow, and all three are kept literally.

**No empty diff is claimed that was not observed, and no experiment is claimed
that was not performed.** AAP §0.6.9 records the limitations of the original
authoring host. QA remediation later supplied the writable Compose harness,
completed the strict build, and observed the **eight** mandated parity journeys
on 2026-08-04. A ninth scenario, `end_of_cycle_gl`, was added afterwards to reach
`gl080`, and on **2026-08-07 all nine** journeys were observed with empty diffs.

⚠️ **AND EVERY ONE OF THOSE DIFFS IS AGAINST THE DISCLOSED-TRANSFORMED DIAGNOSTIC
ORACLE, NOT THE FROZEN ONE.** It has to be said here rather than only in the evidence
register, because a reader arriving at an anomaly's `REPRODUCED` status through this
sentence would otherwise take it for frozen parity. The frozen sources do not compile
from this checkout — `copybooks/ACAS-SQLstate-error-list.cob` is absent and 22 of the
28 generated `common/*MT.cbl` bridges `COPY` it — so the build those journeys ran
against carried 41 transformed paths, 40 of them repairs to executable logic. What the
empty diffs establish is that the two implementations agree; what they cannot establish
is that either reproduces the frozen specification. Every anomaly whose status rests on
one of those runs is therefore **reproduced against the diagnostic oracle**, and
[`scenario-diff-evidence.md`](scenario-diff-evidence.md) §0 states the position in
full, verdict by verdict.
Both dates are stated rather than the later one silently replacing the earlier,
because an entry that cites 2026-08-04 evidence was resolved against an
eight-journey sweep and saying otherwise would backdate a run that had not
happened. Only entries carrying an explicit compiled-evidence update rely on
those runs; all other stored-value questions retain their pending or partial
status.

**AND EVERY MEASURED CLAIM CITES DURABLE REPOSITORY STATE, NOT A SESSION LOG.** This matters enough to
state as its own commitment, because it was not always true here. Where an entry reports something the
oracle showed, the evidence it cites is
[`scenario-diff-evidence.md`](scenario-diff-evidence.md) — which carries the per-scenario manifest
SHA-256 digests, the affected-table lists, the row counts and the artifact layout, all committed to
this repository — and, where relevant, the assertion-owning test that re-establishes the same fact on
demand. Console logs written to a temporary directory during a remediation session are **not** cited as
evidence: they do not survive the session, a later reader cannot open them, and a claim whose only
support has evaporated is indistinguishable from an unsupported one. Where a value was measured but no
durable artifact retains it, this register says so in those words and labels the value an **unverified
report** or a **provisional assumption** rather than a finding.

**Every locator in this document was verified by direct reading of the frozen source.** That is the
other evidential claim made. Where the received brief and the Agent Action Plan disagreed with the
frozen file, the frozen file won and §8 records the correction. Where an entry's stored effect
depends on a conversion nobody has yet measured, the entry is marked pending rather than completed
with a plausible number.

---

## 4. The freeze

AAP §0.8.1, verbatim:

> *"Any diff touching `common/*.cbl`, `common/*.scb`, `copybooks/*.cob`, `general/*.cbl`, `sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl` or `mysql/ACASDB.sql` is a defect in the migration, regardless of how harmless it appears."*

Not reformatted, not commented, not "modernised", not moved. **Reading is the only permitted
interaction.** The same holds for the maintainer's own record. Per AAP §0.2.1.4, `README.TXT`,
`README`, `README.SVN`, `README.nightly`, `Changelog` and `ACAS-Manuals/`

> *"are not edited — they document the COBOL system and its version history, and modifying them would misrepresent the maintainer's record."*

They are cross-referenced throughout and never edited.

Every anomaly in this register is consequently a *description*, never a patch. Where a defect
plainly wants fixing, the fix belongs nowhere: the COBOL keeps it, and the Python reproduces it.

---

## 5. Identifier convention

Anomaly identifiers are **externally imposed and must not be renumbered**:

- Canonical entries are `A-1` … `A-22`, in the order the Agent Action Plan §0.6.7 register
  established them.
- Candidates found while writing the migration are `A-NEW-1`, `A-NEW-2`, … and live in §15.

This is not a stylistic choice. The sibling test tiers and the reproducing modules cite these
identifiers directly, in assertion messages and module-level registers, and the generated data
dictionary carries them in per-field `anomaly_refs` lists. Renumbering would break the sibling
suite silently — the worst possible failure mode for a document whose entire purpose is that a
future "fix" fails loudly.

New candidates are only ever *appended*. `A-NEW-13` in §15 is appended for exactly that reason: it
adds a verified finding without moving any existing identifier.

---

## 6. How to read an entry

Each canonical entry in §10 carries six things, always in the same order:

| Field | Meaning |
| --- | --- |
| **id** | `A-1` … `A-22`. Never renumbered. A dagger (†) marks a test-locked entry. |
| **description** | What the defect is, and why it is a defect rather than an idiom. |
| **locator(s)** | One or more `[path:locator]` citations into the frozen source, all verified. |
| **reproducing module** | The Python module that carries the defect forward, per R-5. |
| **test-locked** | Yes plus the named locking test, or No plus the reason none applies. |
| **status** | `REPRODUCED` when the behaviour is fully determined by the frozen source; `PENDING — AWAITING ORACLE EXECUTION` plus a `Q-` cross-reference when the stored value is not yet measured; `REPRODUCED — VALUE MEASURED` when it has since been watched — **five** entries carry that today, A-2, A-11, A-14, A-15 and A-17, and **none** is still pending. That third value is the one to read carefully: it means the defect is still reproduced and still not repaired, and only the value it produces became known. A promoted entry keeps its `Q-` cross-reference, because the measurement lives there. An anomaly never moves to a status that implies it was fixed, because R-4 does not permit fixing one. |

"Test-locked" means a test asserts the defective behaviour, **so that a future well-meaning "fix"
fails the suite** rather than passing unnoticed. Fifteen of the twenty-two are locked; §11 maps
each to its owning test file.

---

## 7. Locator convention

Every claim about the existing system carries an inline `[<path>:<locator>]` citation, following
AAP §0.1, *"so that downstream execution agents can verify each statement against the source rather than trusting this document."* Paths are repository-root relative. `L<n>` is a single line;
`L<n>-L<m>` is an inclusive span. A citation with no line number refers to the file as a whole.

Two conventions worth stating because they recur:

- A locator points at the **defect site**, not at the paragraph containing it. Where the effect of
  the defect appears on a different line, both are cited and labelled.
- Where a defect exists in several sibling programs, every site is cited. The point of A-1, A-9,
  A-17 and A-NEW-10 is precisely that the siblings differ, and a single citation would hide that.

---

## 8. Corrected locators

⚠️ **Several locators in the Agent Action Plan are wrong, and this document uses the verified
values.** A citation that does not resolve defeats the entire convention in §7, so each correction
is listed here rather than applied silently.

| Claim | AAP locator | Verified locator | What is actually at the AAP locator |
| --- | --- | --- | --- |
| A-1 missing period | `sales/sl060.cbl:L1172-L1178` (span only) | **`sales/sl060.cbl:L1176`** | the span is right; the defect line was never named |
| A-13 non-numeric skip | `general/gl072.cbl:L289-L290` | **`general/gl072.cbl:L291-L292`** | L289 is `go to end-run.`, part of the at-end phrase |
| A-13 `we-error` skip | `general/gl072.cbl:L303-L304` | **`general/gl072.cbl:L306-L307`**, plus a second site at **L348-L349** | L303-L304 are blank-comment and `if post-ledger` lines |
| A-14 sequential read | `general/gl072.cbl:L410-L412` | **`general/gl072.cbl:L408`**, guard L407, key move L405 | L410-L411 is the *post-read* `if read-ledger not = "R"` guard |
| A-21 qualified reference | `general/gl070.cbl:L510` | **`general/gl070.cbl:L497`, `L521`, `L525`** | L510 is an ordinary unqualified `move post-cr to pre-ac.` |
| A-11 signed source block | `copybooks/wssl.cob:L46-L52` | **`copybooks/wssl.cob:L45-L53`** for the nine `binary-long`, plus **L43-L44** for two `binary-short` | L46-L52 is seven of the nine, omitting `Sales-Limit` and `Sales-Create-Date` |
| A-11 unsigned host block | `common/salesMT.cbl:L305-L312` | **`common/salesMT.cbl:L304-L312`**, plus **L302-L303** | L305-L312 is eight of the nine, omitting `HV-SALES-LIMIT` |
| A-15 length contradiction | `copybooks/wsbatch.cob` (file only) | **`copybooks/wsbatch.cob:L7-L9`** | no line was given |
| A-19 destructive subtract | not cited | **`irs/irs030.cbl:L1564`** | the AAP cites the computes but not the subtract that consumes them |
| A-20 misnamed spares | `copybooks/wssys4.cob` (file only) | **`copybooks/wssys4.cob:L29-L30`**, group at L20 | no line was given |
| A-11 second instance | not cited | **`copybooks/wsbatch.cob:L36-L39`** to **`common/glbatchMT.cbl:L287-L290`** to **`mysql/ACASDB.sql:L86-L89`** | the AAP records only the Sales instance |
| `sign is leading`, second field | `copybooks/irswspost.cob:L19` | **`copybooks/irswspost.cob:L18`** | L19 is the closing `*>` comment line |
| A-3 quarter notions | "two" | **at least four**, at `general/gl080.cbl:L328` with `L345`, `L355-L357`, `L358-L360` and `L361-L363` | the AAP undercounts |
| A-12 width drift | one instance | **two**, the second at `copybooks/slwsoi.cob:L32` to `common/otm3MT.cbl:L310` to `mysql/ACASDB.sql:L905` | the AAP records only the ledger-name instance |

Three further corrections apply to §13 rather than to the register, and are stated there in place:
the live `cobc` line list of `common/comp-common.sh` (§13.5), the live compile-line count of
`sales/comp-sales.sh` (§13.6), and the existence of a `presql2.param` template inside the vendored
archive (§13.12).

---

## 9. The register — index

Twenty-two canonical entries. A dagger (†) marks a test-locked entry; §11 names the owning test.

| id | One-line summary | Sub system | Test-locked | Status |
| --- | --- | --- | --- | --- |
| A-1 † | A missing terminating period nests a second conditional, so the General Ledger posting close never runs in pure-GL mode | Sales | yes | REPRODUCED |
| A-2 † | A quarter-array subscript is computed by a `ROUNDED` divide and used with no bounds check | General | yes | REPRODUCED — VALUE MEASURED |
| A-3 † | Four disagreeing notions of "current quarter" coexist in one program | General | yes | REPRODUCED |
| A-4 † | Half-posted double entry: the debit is rewritten before the credit account is looked up | IRS | yes | REPRODUCED |
| A-5 † | Lost update on the two VAT control accounts, from pre-loop snapshots rewritten at end of job | IRS | yes | REPRODUCED |
| A-6 † | A published facade verb that can never succeed, rejected unconditionally at handler entry | IRS | yes | REPRODUCED |
| A-7 † | Guarded date-component derivation leaves columns at zero beside intact date text | IRS bridge | yes | REPRODUCED |
| A-8 † | Double truncation of the moving average: pence lost, then the remainder lost | Sales and Purchase | yes | REPRODUCED |
| A-9 † | The credit-note average path never increments its activity counter | Sales and Purchase | yes | REPRODUCED |
| A-10 † | Mutually inconsistent guards on one moving-average idiom | Sales and Purchase | yes | REPRODUCED |
| A-11 † | A signed value narrows to an unsigned host variable and column, losing its sign before any SQL runs | Sales, General, and nine more tables | yes | REPRODUCED — VALUE MEASURED, `Q-3` |
| A-12 | Character-width drift across copybook, host variable and column, and the bridge trims | General and Sales | no | REPRODUCED |
| A-13 † | Two entirely silent skips, with no message, counter or trace | General | yes | REPRODUCED |
| A-14 † | The nominal account is located by sequential read, so correctness depends on upstream sort order | General | yes | REPRODUCED — VALUE MEASURED |
| A-15 | The batch record's declared length contradicts the sum of its fields | General | no | REPRODUCED — VALUE MEASURED, comment stale, `Q-4` |
| A-16 | The date module leaves its output field unchanged on a bad date | Shared | no | REPRODUCED |
| A-17 | An unexplained move carrying the maintainer's own `*> Why ?`, in all four Sales and Purchase posting programs | Sales and Purchase | no | REPRODUCED — effect measured, `Q-A17-POSTINGS-EFFECT` |
| A-18 | Two percentage fields are not carried into the IRS posting record | Sales and Purchase | no | REPRODUCED |
| A-19 † | Superseded commented-out VAT computes remain beside the live ones | IRS | yes | REPRODUCED |
| A-20 | Two spare fields carry the Sales prefix inside the Purchase group | General | no | REPRODUCED |
| A-21 † | Field-name collisions across three posting copybooks force qualified references, in two spellings | General | yes | REPRODUCED |
| A-22 | A wrapper section named after the interface copybook, with its exit label named after the called program | General | no | REPRODUCED |

Fifteen entries are test-locked: **A-1, A-2, A-3, A-4, A-5, A-6, A-7, A-8, A-9, A-10, A-11, A-13,
A-14, A-19, A-21**. They are locked **so that a future well-meaning "fix" fails the suite**. The
seven that are not locked are recorded rather than asserted because their observable is a comment, a
name, or a report line that never reaches a table, so no state diff and no arithmetic assertion can
see them; §11 explains that boundary once rather than seven times.

---

## 10. The register — entries

### A-1 † — the missing terminating period that swallows the General Ledger posting close

**Description.** In `sl060`'s `ca000-BL-Close` section the `perform SPL-Posting-Close` statement has
no terminating period, so the `if IRS-Both-Used or G-L` that follows it becomes **nested inside**
the preceding `if IRS-Used OR IRS-Both-Used` instead of being a sibling sentence. The consequence is
exact and one-directional: in pure-GL mode — `G-L` true, `IRS-Used` and `IRS-Both-Used` both false —
the outer condition is false, so the nested inner condition is never evaluated and
`GL-Posting-Close` never executes. The General Ledger posting file is left unclosed on the one
configuration where it is the only posting file in play.

**Locators.** The defect site is `[sales/sl060.cbl:L1176]` — `perform SPL-Posting-Close` with the
maintainer's trailing comment `*>  close irs-post-file` and **no period** — inside the span
`[sales/sl060.cbl:L1172-L1178]`, with the swallowed effect at
`[sales/sl060.cbl:L1177-L1178]`. The three sibling programs all **have** the period at the
equivalent statement: `[purchase/pl060.cbl:L1031]`, `[sales/sl100.cbl:L694]` and
`[purchase/pl100.cbl:L675]`. That three-to-one split is what makes this an accident rather than an
idiom, and it is why the entry is worded as a defect at all. See also A-NEW-10, which records a
copy-paste artefact in the same four-line neighbourhood and is the most plausible mechanism by which
the period was lost.

**Reproducing module.** `acas_posting/programs/sl060_invoice_posting.py`, where the second
conditional is written as a **nested** conditional and is deliberately **not** normalised against
its three siblings.

**Test-locked.** Yes. **Primary lock:**
`tests/arithmetic/test_shipped_close_and_rejection_paths.py::test_a1_the_posting_close_follows_the_nested_predicate`,
which drives the SHIPPED `ca000-BL-Close` with a recording stand-in in the module's `facade` slot and
asserts the whole two-field truth table of `IRS-Instead` × `Level-1`. Its companion
`test_a1_the_nested_and_sibling_readings_differ_on_exactly_one_row` establishes that the table
discriminates: the nested reading and the sibling reading disagree on **pure-GL mode alone**, so a
test exercising only the IRS states would pass against both and prove nothing. Verified by
construction — adding the missing period was tried, and the truth table failed on exactly that one
row.

⚠️ **The lock moved here, and the reason is worth stating (finding MJ-07).** An earlier revision named
`tests/scenarios/test_clean_batch_post_sl.py::test_a1_missing_period_gl_posting_close_not_executed` as
the primary lock, on the ground that it "demands that `GLPOSTING-REC` show the unclosed-file state on
both sides". **There is no such state.** `GL-Posting-Close` is a pure lifecycle call: it writes
nothing, mutates no record area, and closing a file leaves no row behind. Adding the missing period
therefore produces an identical dump and that test passes either way — measured, not reasoned. A
state comparison could never have owned this defect.

**State witnesses.** `tests/scenarios/test_clean_batch_post_sl.py::test_a1_missing_period_gl_posting_close_not_executed`
and its **paired control**
`tests/scenarios/test_clean_batch_post_pl.py::test_a1_control_pl060_terminating_period_is_present`
remain valuable and remain in the register — just as witnesses rather than locks. What they establish
is that two independent implementations agree on `GLPOSTING-REC` on the one route where A-1 is
reachable, and on the sibling route where the period is present; that is real parity evidence about
the surrounding posting path, and it is what makes the three-to-one split reviewable against compiled
behaviour rather than against an argument. **Contextual coverage only:**
`tests/arithmetic/test_irs_vat_from_net.py` and
`tests/scenarios/test_clean_batch_post_pl.py`'s header prose mention `A-1` without asserting it. The
distinction between lock, witness and mention is kept because a reader who follows a mention to a
test and finds no assertion has been misdirected.

**Status.** REPRODUCED. Determined entirely by the frozen source; no measurement is required to know
which branch runs.

### A-2 † — an unbounded quarter subscript from a `ROUNDED` divide

**Description.** `gl080` computes the quarter-array subscript `a` with a rounding divide and then
uses it to index the nominal-ledger quarter array with no bounds check of any kind. `a` is declared
`pic 99`, so it can hold 0 to 99, while the array it indexes has four elements. An out-of-range
accounting period therefore silently indexes past the array rather than raising anything.

**Locators.** The divide is `[general/gl080.cbl:L328]` — `divide scycle by period giving a rounded.`
— and the unchecked subscript use is `[general/gl080.cbl:L345]` — `move ledger-balance to
ledger-q (a).` The declaration is `[general/gl080.cbl:L183]`. This is one of the five `ROUNDED`
sites listed in §12, and the only one whose result is used as a subscript. A-NEW-6 records that the
same divide is reachable with `period = 0`.

**Reproducing module.** `acas_posting/programs/gl080_end_of_cycle.py`, which leaves the subscript
unbounded per R-3 as well as R-4 — adding a range check would be adding a validation.

**Test-locked.** Yes — `tests/arithmetic/test_gl080_cycle_divide_rounded.py`.

**Status.** **REPRODUCED — VALUE MEASURED.** The divide itself was always fully determined. The
*behaviour* of an out-of-range subscript is a property of the compiled program rather than of the Python
code, and it has now been watched: `move 999.99 to ledger-q (13)` on the 126-byte `GLLEDGER` record stores
its six packed bytes at 1-based offsets **125 to 130** — two inside the trailing `filler pic x(50)`, **four
past the end of the record** — leaves `Q1` through `Q4` and `Ledger-Last` unchanged, emits no diagnostic and
exits 0. Occurrence 14 lands at 131 to 136, so the addressing is linear and does not wrap.

**The consequence for a state diff is what makes the measurement worth having: an overrunning store moves no
column of any of the 22 compared tables**, so a run that overruns and a run that does not are
indistinguishable in a dump. The subscript is left unbounded (R-3, R-4) and the one remaining divergence is
declared at the site rather than guarded away: Python RAISES where COBOL overwrites, because Python has no
adjacent storage to write into. The measurement lives in
`[acas_posting/cobol/move.py UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE]` and is asserted by
`tests/arithmetic/test_gl080_cycle_divide_rounded.py`. Question `Q-QUARTER-SUBSCRIPT`, carried in the numeric
band as `Q-19`, has the full record in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md).

### A-3 † — four disagreeing notions of "current quarter" in one program

**Description.** `gl080` maintains the idea of "which quarter are we in" in four different and
mutually independent ways within thirty-five lines, and nothing reconciles them:

1. the computed subscript `a`, derived by the `ROUNDED` divide of A-2 and used to select the array
   slot the balance is written into;
2. an independent rotating counter `current-quarter`, incremented after the ledger walk and reset
   to 1 when it reaches 5;
3. a third rotation, on `scycle` rather than on a quarter counter, applied when the period length
   is 3 and the cycle number has passed 12;
4. a fourth conjunctive reset of the same `scycle`, applied when the period length is 13 and the
   cycle number has passed 52.

Notions 3 and 4 rotate a *different variable* from notion 2 on a *different trigger*, and notion 1
is recomputed from `scycle` on the next run — so a change to `scycle` by notion 3 or 4 feeds back
into notion 1 but never into notion 2.

**Locators.** `[general/gl080.cbl:L345-L357]` carries notions 1 and 2 — the subscript use at L345
and the rotation at L355-L357. Notion 3 is `[general/gl080.cbl:L358-L360]` — `if period = 3 / and
scycle > 12 / move 1 to scycle.` Notion 4 is `[general/gl080.cbl:L361-L363]`, whose conjunctive
condition occupies L361-L362 and whose `move 1 to scycle.` is at L363. The Agent Action Plan says
"two"; the frozen file has at least these four, and §8 records the undercount.

**Reproducing module.** `acas_posting/programs/gl080_end_of_cycle.py`, which keeps all four as four.

**Test-locked.** Yes — `tests/arithmetic/test_gl080_cycle_divide_rounded.py`.

**Status.** REPRODUCED.

### A-4 † — half-posted double entry on a missing credit account

**Description.** In `irs030`'s `Ledger-Postings-Add` section the debit side of a posting is
**rewritten to the nominal ledger before the credit account is even looked up**. If the credit
account does not exist, the section abandons the transaction and returns to the input loop — leaving
a posted debit with no balancing credit, and no posting record written either. The double entry is
half-applied and the run continues.

There are two distinct dispositions here, and only the second is destructive:

- a missing **debit** account is a *clean* skip. The lookup fails before anything is written, a
  message is displayed, and control returns to the input loop with no database effect.
- a missing **credit** account is a *partial write*. The debit has already been rewritten.

**Locators.** The span is `[irs/irs030.cbl:L1635-L1652]`. The debit accumulation is at L1635-L1637
and the debit rewrite at **L1641**; the credit key move is at L1645 and the credit lookup at
**L1647**; the failure exit is at **L1652**. The clean debit-side skip is
`[irs/irs030.cbl:L1627-L1634]`, carrying message identifier **IR032**; the destructive credit-side
path is `[irs/irs030.cbl:L1645-L1652]`, carrying message identifier **IR033**. The two paths are
textually near-identical and differ only in what has already happened by the time they are reached
— which is exactly why the defect survived.

**Reproducing module.** `acas_posting/programs/irs030_posting.py`, which performs the debit rewrite
before the credit lookup in the same order, and reproduces both dispositions separately rather than
collapsing them into one rejection path.

**Test-locked.** Yes. **Primary lock:**
`tests/scenarios/test_clean_batch_post_irs.py::test_a4_half_posted_double_entry_reproduced`, whose
whole subject is this defect: it seeds a posting whose credit account is missing and asserts that
both sides show the committed debit in `IRSNL-REC` **and** the absent `IRSPOSTING-REC` row, failing
in the direction that looks like a fix as loudly as in the other. That end state is the only
observable a half-posted double entry has, which is why the lock cannot live in the arithmetic tier.
**Contextual coverage only:** `tests/arithmetic/test_move_truncation.py` cites A-4 in its section
headings without asserting the disposition.

**Status.** REPRODUCED. Both the ordering and the resulting partial state are fully determined by
the frozen source.

### A-5 † — lost update on the two VAT control accounts

**Description.** `irs030` reads the input-tax and output-tax control accounts into two working
snapshots **before** its posting loop begins, accumulates VAT into those snapshots during the loop,
and rewrites both snapshots to the nominal ledger at end of job. Any rewrite of those same two
accounts performed *inside* the loop — which happens whenever a posting's debit or credit account
happens to be one of them — is therefore overwritten by the stale-plus-VAT snapshot at end of job.
This is a textbook lost update, and it is silent.

**Locators.** The snapshots are taken at `[irs/irs030.cbl:L1602]` and `[irs/irs030.cbl:L1612]`, from
the two default account codes `def-acs (31)` at `[irs/irs030.cbl:L1594]` and `def-acs (32)` at
`[irs/irs030.cbl:L1604]`. They are rewritten at `[irs/irs030.cbl:L1704-L1705]` and
`[irs/irs030.cbl:L1707-L1708]`, unconditionally, at end of job. The in-loop rewrites that they
discard are at `[irs/irs030.cbl:L1641]` and `[irs/irs030.cbl:L1657]`.

**Reproducing module.** `acas_posting/programs/irs030_posting.py`.

**Test-locked.** Yes — `tests/scenarios/test_clean_batch_post_irs.py::test_a5_lost_update_on_vat_control_accounts_reproduced`,
the file AAP §0.4.1.7 names, whose end-state assertion is the only observable that can see a lost
update. No arithmetic-tier test can: the defect is in *ordering across a loop boundary*, not in a
computation.

**Status.** REPRODUCED.

### A-6 † — a published facade verb that can never succeed

**Description.** `acas008`, the handler for the Sales-and-Purchase-to-IRS transfer file, rejects four
of its published verbs unconditionally at entry, before any access-type or file-mode logic runs,
because the underlying file is sequential: **read-indexed, re-write, start and delete**. The IRS
facade nevertheless publishes `acas008-Rewrite` as a callable verb, so any caller invoking it always
fails with the same status pair, every time, for every record.

**Locators.** The guard is `[common/acas008.cbl:L299-L307]`: an `evaluate File-Function` with
`when 4` (read-indexed), `when 7` (re-write), `when 9` (start) and `when 8` (delete) falling into a
common branch. That branch sets **`WE-Error = 988`** at `[common/acas008.cbl:L304]`, carrying the
maintainer's own comment `*> Action type wrong for file type (seq)   988`, then **`FS-Reply = 99`**
at `[common/acas008.cbl:L305]`, then `go to aa999-main-exit` at `[common/acas008.cbl:L306]`. The
published verb is `[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163]`. Those two numbers are not
decoration: "return the same status pair" is unimplementable without them, and the Agent Action Plan
omits them.

Two related facts about the same handler, recorded here so they are not mistaken for separate
defects. It declares its own logging identity as the IRS sub system —
`[common/acas008.cbl:L293-L294]`, system 1, file 15 — even though its callers are Sales and
Purchase. And `Open-Output` on it means *delete every row*; see A-NEW-8, which records that the
sibling handler `acas007` does **not** do the same.

**Reproducing module.** `acas_posting/dal/acas008_spl_posting.py`, which reproduces the guard in
`aa010_main` and returns the same pair rather than performing an update. The refused set and its pair
are data-driven, from `HANDLER_REJECTED_FUNCTIONS` in `acas_posting/dal/cursor_state.py`, keyed by
table and then by `File-Function`.

**Test-locked.** **Yes**, in two halves, because the anomaly has two observables and no single tier
can see both. This entry previously said *no*, on the reasoning that the verb's failure is a status
pair returned to a caller rather than a table state and so no scenario diff can see it. The first
half of that is true and the conclusion did not follow: a status pair is not observable from a table
dump, but it *is* observable from a call.

The **behaviour lock** is at the arithmetic tier, which calls the handler directly: seven tests in
`tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` drive the refused verbs and assert
the measured pair — `WE-Error 988` with `FS-Reply 99` — per verb, per published facade alias, for the
whole refused set, before any connection is attempted, and against the supported functions as a
control. The **state-level lock** is at the scenario tier, where the pair is invisible:
`tests/scenarios/test_clean_batch_post_irs.py::test_a6_rewrite_verb_can_never_succeed` asserts the only
outcome an always-failing verb can produce, NO CHANGE, on both sides — so a migrated rewrite that
quietly succeeded would surface as surviving or altered rows on one side alone. That is a weaker
guarantee than the behaviour lock rather than a substitute for it, and §11 classifies the two
relationships separately for exactly that reason. The reproducing module carries the two numbers at
the guard site.

*The mechanism half* — `tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` §20. It
INVOKES each of the four refused functions through **both** published alias sets, asserts
`WE-Error 988` with `FS-Reply 99` on every one, asserts the record is unchanged by the call, asserts
the `File-Function` the facade set before dispatching, and sabotages the handler's connection opener
to prove the guard returns **before** any database work is attempted. It also asserts the ABSENCE of
the three aliases the IRS copybook does not declare, and includes a control proving the four
supported functions and `DELETE_ALL` are *not* refused — so the test cannot pass by refusing
everything.

*The state half* — `tests/scenarios/test_clean_batch_post_irs.py`'s `test_a6_rewrite_verb_can_never_succeed`.
It compares the transfer table's PRE-run digest against its POST-run digest, per side, so the claim
is "this cycle changed nothing", not merely "the two cycles agree". That comparison is only possible
because the end-of-job clear is a measured no-op on this fixture (see the key-bound note under
A-NEW-8); had the table been emptied, an unchanged-table claim would have held for any behaviour.

Neither half claims the other's ground, and the earlier "No" in this slot understated the register:
the status pair *is* assertable, in the tier that can call the handler directly. Seven assertions make
it so —

- one per refused verb, calling `aa010_main` with `File-Function` 4, 7, 9 and 8 in turn and requiring
  `WE-Error 988` with `FS-Reply 99`;
- one per refused verb again, this time through the PUBLISHED entity-named facade verb, so that what a
  caller observes is asserted rather than inferred from the handler, and requiring the record to come
  back field for field as it went in;
- one on the membership of the refused set itself, which is data and could otherwise drift without any
  code changing, plus the four `when`-line locators this register cites;
- one on the dual-alias publication, requiring the entity-named `SPL-Posting-Rewrite` and the
  handler-named `acas008-Rewrite` to carry the same `File-Function` and the same handler, since a hole
  in the aliasing would fall exactly where this anomaly lives;
- one that CALLS the handler-named `acas008-Rewrite` and requires the identical refusal, and asserts
  the ABSENCE of `acas008-Read-Indexed`, `-Start` and `-Delete`, which the IRS copybook does not
  declare;
- one that sabotages the handler's own connection opener and requires the refusal to arrive anyway, so
  "no database is reached" is proved rather than asserted in prose;
- and one CONTROL, requiring the four supported functions and `DELETE_ALL` to be absent from the
  refusal table, so that the six above cannot be satisfied by a handler that refused everything.

No connection is opened by any of them, because the guard returns before any code that would want
one — which is part of the finding rather than a convenience.

`tests/scenarios/test_clean_batch_post_irs.py` continues to assert the STATE consequence, and the two
are complementary rather than redundant: the state assertion alone would pass for a handler that
silently did nothing, raised, or returned a different failure pair.

**Status.** REPRODUCED, with both status values **MEASURED on the compiled handler** rather than read
from the source. A COBOL driver compiled against the frozen copybooks called the compiled `acas008`
with its own linkage in its own order `[common/acas008.cbl:L278-L284]`, logging off and
`File-System-Used` set to the RDB mode. GnuCOBOL 3.2 answered:

| verb | `File-Function` | `WE-Error` | `FS-Reply` |
| --- | --- | --- | --- |
| read-indexed | 4 | 988 | 99 |
| re-write | 7 | 988 | 99 |
| delete | 8 | 988 | 99 |
| start | 9 | 988 | 99 |

And it answered the contrast, which is what makes the pair meaningful rather than generic:
`read-next` (2) is not named by the `evaluate`, and the same call passed the guard and went on into
the handler's real work. So 988/99 is *this guard's* answer, not what `acas008` says whenever
anything goes wrong.

### A-7 † — guarded date-component derivation, and the partially-derived row

**Description.** The internal IRS posting table carries three columns — `POST4-DAY`, `POST4-MONTH`
and `POST4-YEAR` — that have **no counterpart in any copybook**. They exist only because the bridge
derives them from the posting date's text by reference modification, each behind its own `numeric`
guard. The guards have **no `else`**, and they are **three independent statements rather than one**,
so a *partial* derivation is reachable: day and year set while month stays at zero, for instance,
alongside a fully intact raw date text in the neighbouring column. The row is internally
inconsistent and nothing detects it.

The reason a failed guard yields **zero and never SQL `NULL`** is that the host-variable group is
initialised before the load, so an unset numeric host variable is zero by the time the statement is
built. That is also why every column in the frozen schema can be declared `NOT NULL`.

**Locators.** The three guards are `[common/irspostingMT.cbl:L982-L983]`,
`[common/irspostingMT.cbl:L984-L985]` and `[common/irspostingMT.cbl:L986-L987]`, testing
`Post-Date (1:2)`, `Post-Date (4:2)` and `Post-Date (7:2)` respectively — collectively
`[common/irspostingMT.cbl:L982-L987]`. The unconditional raw-text store that survives a failed guard
is `[common/irspostingMT.cbl:L969]`, and the group initialisation is
`[common/irspostingMT.cbl:L966]`. The maintainer's own note on the derivation sits immediately above
at `[common/irspostingMT.cbl:L978-L980]`.

This is the entry that proves the Agent Action Plan's central sourcing decision — that the bridge
and not the copybook is the authoritative data dictionary. A migration driven from the copybooks
alone would have omitted three columns of a posting table outright. The generated dictionary records
all three as `BRIDGE_DERIVED` entries with their guard text and source span attached.

**Reproducing module.** `acas_posting/dal/acasirsub4_irs_posting.py`.

**Test-locked.** Yes. **Primary lock:** `tests/arithmetic/test_irs_date_component_derivation.py`,
which owns the guarded derivation itself. **Second lock, at the other end:**
`tests/scenarios/test_clean_batch_post_irs.py::test_a7_partial_date_component_derivation_is_dumped_as_stored`,
which asserts that the internally inconsistent row — zero components beside a stored raw date text —
survives the dump and normalisation unchanged on both sides.

**Status.** REPRODUCED.

### A-8 † — double truncation of the moving average

**Description.** `sl060` maintains a customer's moving average invoice value with an idiom that
loses precision **twice**, because of the field widths involved rather than because of any explicit
rounding:

1. the accumulator has **zero decimal places** while the value added into it carries two, so pence
   are discarded on every accumulation; then
2. the subsequent divide stores into an integer average field, so the remainder is discarded as
   well.

An implementation that carried two decimals through either step would diverge from the compiled
program on very nearly every invoice, which is why this is the highest-value entry in the register
for arithmetic parity.

**Locators.** The accumulator is `[sales/sl060.cbl:L206]` — `03 work-2 pic s9(14) comp-3.`, with no
`V` and therefore no decimal positions — while the value added into it, `work-goods`, is
`[sales/sl060.cbl:L218]` — `pic s9(7)v99 comp-3`. Truncation one is the add at
`[sales/sl060.cbl:L826]`; truncation two is the divide at `[sales/sl060.cbl:L827]`, whose receiving
field `Sales-Average` is declared `binary-long` at `[copybooks/wssl.cob:L49]` and is therefore an
integer. The Purchase mirror is `[purchase/pl060.cbl:L200]` with the same shape.

⚠️ The *double* truncation is specific to `sl060` and `pl060`. The cash and payment programs have
**no `work-2` at all** — `[sales/sl100.cbl:L181]` and `[purchase/pl100.cbl:L174]` declare only
`work-1 pic s9(7)v99 comp-3`, and their payment-days accumulator and operand are both `binary-long`
at `[sales/sl100.cbl:L182-L183]` and `[purchase/pl100.cbl:L175-L176]`. Their average therefore
truncates once, on the divide, not twice.

**Reproducing module.** `acas_posting/programs/sl060_invoice_posting.py` and
`acas_posting/programs/pl060_order_posting.py`, both of which model the accumulator's zero scale and
the average field's integer storage class exactly rather than carrying a common decimal through.

**Test-locked.** Yes — `tests/arithmetic/test_compute_truncate_unrounded.py` is the primary lock,
with `tests/arithmetic/test_comp3_packed_decimal.py` covering the first truncation and
`tests/arithmetic/test_comp_binary.py` the second.

**Status.** REPRODUCED.

### A-9 † — the credit-note average that never increments its counter

**Description.** `sl060` has two near-identical sections that maintain the same moving average, one
for invoices and one for credit notes. The invoice section increments the activity counter before
dividing by it. The credit-note section **never increments it at all**, and additionally guards the
whole computation on the accumulator being non-zero — so the first credit note for a customer, whose
accumulator is still zero, is silently dropped from the average entirely.

The guard is a **third instance of the same missing-period class as A-1**, and this is the detail
that makes the entry reproducible rather than merely describable: the `if work-2 not = zero` and the
two statements after it form a **single COBOL sentence**, because the only terminating period in the
three lines is at the end of the last one. The condition therefore governs *both* the add and the
divide. In the invoice section the two equivalent statements are each their own sentence and neither
is guarded.

**Locators.** The credit-note section is `[sales/sl060.cbl:L835-L843]`: the two-condition entry
guard at L835-L836, the else-zero at L838-L839, then the single sentence L841-L843 — `if work-2 not
= zero` at L841, `add work-goods to work-2` at L842, and `divide sales-activety into work-2 giving
sales-average.` at L843, whose period is the only one in the group. The contrasting invoice section
is `[sales/sl060.cbl:L816-L827]`, with its counter increment at `[sales/sl060.cbl:L825]` and its two
unguarded sentences at `[sales/sl060.cbl:L826]` and `[sales/sl060.cbl:L827]`. The Purchase mirror is
`[purchase/pl060.cbl:L755-L766]`, which likewise never increments `purch-activety`.

**Reproducing module.** `acas_posting/programs/sl060_invoice_posting.py` and
`acas_posting/programs/pl060_order_posting.py`. The missing increment is left missing.

**Test-locked.** Yes — `tests/arithmetic/test_compute_truncate_unrounded.py`.

**Status.** REPRODUCED.

### A-10 † — mutually inconsistent guards on one moving-average idiom

**Description.** The same moving-average idiom appears in four of the in-scope programs, and no two
instances agree on how it is guarded or on whether the counter is incremented. The divergences are
real and change results. What does **not** diverge — and this is the precision obligation set out in
full in §14.1 — is the direction of the divide.

The genuine divergences, verified site by site:

| Site | Guard shape | Counter increment |
| --- | --- | --- |
| `sl060` invoice section | two conditions plus an `else` that zeroes the accumulator | yes, before the divide |
| `sl060` credit-note section | the same two conditions, plus a second inner guard on the accumulator that makes the add and divide one conditional sentence | **no** |
| `sl100` cash section | one condition, with the accumulator pre-zeroed by an unconditional move rather than by an `else` | yes, before the divide |
| `pl060` and `pl100` | the Purchase mirrors of the two `sl060` sections and of `sl100` respectively | as their Sales counterparts |

**Locators.** The three Sales guards are `[sales/sl060.cbl:L819]`, `[sales/sl060.cbl:L835]` and
`[sales/sl100.cbl:L506]`; the Purchase mirrors are `[purchase/pl060.cbl:L743]`,
`[purchase/pl060.cbl:L758]` and `[purchase/pl100.cbl:L497]`. The `sl100` pre-zeroing move is
`[sales/sl100.cbl:L504]` and its increment `[sales/sl100.cbl:L510]`; the `pl100` equivalents are
`[purchase/pl100.cbl:L495]` and `[purchase/pl100.cbl:L501]`.

⚠️ **The divide direction is a lexical difference only.** `divide X into Y giving Z` and `divide Y
by X giving Z` compute the **same quotient**. `[sales/sl060.cbl:L827]` uses the `into` form and
`[sales/sl100.cbl:L511]` the `by` form, and they differ in spelling, not in arithmetic. Normalising
the three instances into one helper would be the single easiest way to fail this migration — but the
reason is the guard and the counter, never the operand order. §14.1 carries the supporting census.

**Reproducing module.** `acas_posting/programs/sl060_invoice_posting.py`,
`acas_posting/programs/sl100_cash_posting.py`,
`acas_posting/programs/pl060_order_posting.py` and
`acas_posting/programs/pl100_payment_posting.py` — four separate reproductions, deliberately not
factored into one.

**Test-locked.** Yes — `tests/arithmetic/test_compute_truncate_unrounded.py`, the primary R-4 site.

**Status.** REPRODUCED.

### A-11 † — a signed value narrowed to an unsigned host variable and column

**Description.** For a whole block of statistics and date fields the copybook declares a **signed**
binary item, the bridge declares an **unsigned** host variable, and the schema declares an
**unsigned** column. The sign is therefore lost **at the bridge, before any SQL executes** — not at
the database, and not by any rejection the caller can observe. A negative value computed in COBOL is
converted on the way into the host variable and the database never sees the original.

The narrowing is **specific, not systemic**, and that is the operative fact for the migration: the
monetary fields keep their sign at all three layers, so the correction cannot be applied
field-uniformly and must be driven from the dictionary field by field.

**Locators.** The Sales instance, proven in order and one-for-one:

- nine consecutive **signed** `binary-long` items at `[copybooks/wssl.cob:L45-L53]` — `Sales-Limit`
  at L45 through `Sales-Create-Date` at L53, with `Sales-Average` at L49;
- nine **unsigned** `PIC 9(10) COMP` host variables at `[common/salesMT.cbl:L304-L312]`;
- nine `int(8) unsigned NOT NULL` columns, of which `SALES-AVERAGE` is `[mysql/ACASDB.sql:L969]`.

⚠️ There are **eleven narrowings in that bridge, not nine**: `Sales-Late-Min` and `Sales-Late-Max`
are `binary-short` at `[copybooks/wssl.cob:L43-L44]` and become unsigned `PIC 9(05) COMP` at
`[common/salesMT.cbl:L302-L303]`.

⚠️ A **second instance the Agent Action Plan does not record** sits in the General Ledger batch
record: `Entered`, `Proofed`, `Posted` and `Stored` are `binary-long` at
`[copybooks/wsbatch.cob:L36-L39]`, become `PIC 9(10) COMP` at `[common/glbatchMT.cbl:L287-L290]`, and
land in `int(8) unsigned` columns at `[mysql/ACASDB.sql:L86-L89]`.

The contrast that proves specificity: `Sales-Current` and `Sales-Last` are signed `comp-3` at
`[copybooks/wssl.cob:L54-L55]`, stay signed as `PIC S9(08)V9(02) COMP` at
`[common/salesMT.cbl:L313-L314]`, and land in signed `decimal(10,2)` columns.

**Footprint.** The generated dictionary is the authoritative index here, and it makes the scale of
the drift visible in a way the Agent Action Plan's two examples do not:
`data_dictionary/acas_posting_dictionary.json` carries `anomaly_refs` containing `A-11` on **91
field entries across eleven in-scope tables** — `SYSTEM-REC` 41, `PULEDGER-REC` 12, `SALEDGER-REC`
11, `PUINVOICE-REC` 5, `SAINVOICE-REC` 5, `GLBATCH-REC` 4, `PUITM5-REC` 4, `SAITM3-REC` 4,
`VALUEANAL-REC` 3, `PUINV-LINES-REC` 1 and `SAINV-LINES-REC` 1.

⚠️ Those 91 entries **no longer** carry `Q-3` in `ambiguity_refs`, and the change is load-bearing rather
than cosmetic: the question is answered, so the tag was dropped, while the 91 `A-11` references stayed
exactly as they were. The count of one going to zero while the count of the other holds at 91 is what
demonstrates that answering the question did not repair the anomaly.

**Reproducing module.** `acas_posting/dal/acas012_sales.py` and
`acas_posting/dal/acas007_gl_batch.py`, which reproduce the bridge's conversion rather than writing
the computed value and letting the database complain. `acas_posting/dal/acas012_sales.py` additionally
asserts at import time that every field it treats as narrowed carries `A-11` **and** the measurement
note, and that none of them still carries `Q-3`, so the prose above and the artifact cannot drift apart
in either direction: a missing `A-11` would hide a live defect, a missing note would report a measured
value as unmeasured, and a re-appearing `Q-3` would report a settled question as open.

**Test-locked.** Yes — `tests/arithmetic/test_comp_binary.py` for the storage class and
`tests/arithmetic/test_pic_field_descriptors.py` for the per-field descriptors, with
`tests/arithmetic/test_compute_truncate_unrounded.py` and
`tests/arithmetic/test_control_total_comparison.py` carrying it as context.

**Status.** **REPRODUCED — VALUE MEASURED.** Both halves are now settled, and they are settled
separately because they are different claims.

The *shape* was always settled: the sign is lost at the bridge, before any SQL runs, and not at the
database. **That is the anomaly, it is reproduced, and it is not repaired** — R-4. Nothing below
changes it.

The *value stored* for a negative input has now been watched. A probe wrote a negative `Sales-Average`
through the COMPILED `acas012` handler and the COMPILED `salesMT` bridge — so through `cobmysqlapi` and
real SQL against real MariaDB, which is what the question actually asked about. `Q-3` in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md) carries the measurement in full; the result is that
the conversion takes the **absolute value** and then bounds it by the receiving field's declared digit
count, in that order. `-1` into `pic 9(10) comp` stores `0000000001`; `-2147483648` stores `2147483648`;
`-123456` into `pic 9(4) comp` stores `3456`. The two's-complement reinterpretation and the
store-zero readings are both refuted, and the ORDER is settled by an overflowing negative:
`-1` into `binary-char unsigned` stores `1`, not `255`.

Two consequences are visible in the tree rather than only here. `acas_posting/dictionary/generate.py` no
longer emits `Q-3` alongside `A-11`, because the question it pointed to is answered, and the regenerated
artifact carries **0** `Q-3` references where it carried 91 — with all 91 `A-11` references intact, which is
the property that matters: dropping the question did not drop the anomaly. And
`acas_posting/dal/acas012_sales.py`'s import-time guard was INVERTED: it now requires the measurement note
and REFUSES any entry that still publishes `Q-3`, so the artifact cannot silently regress to the open state.

⚠️ **Measuring it did not repair it, and that is why this entry stays.** Every one of those statistics
still arrives at the database with its debit-versus-credit sense destroyed. What the measurement settled
is *what the column holds*, not *whether the defect is present* — and rule R-4 forbids fixing the latter.

The Purchase-side variant is carried as `Q-PURCH-AVERAGE-SIGN`, and it is a separate identifier for a
separate field set rather than a duplicate of this one.

### A-12 — character-width drift, and the bridge that trims

**Description.** A character field is declared narrower in the copybook than in the host variable and
the column. The *value* is not corrupted, but the **padding differs**, and padding is directly
visible in a table dump. Worse, the bridge does not simply widen: it **trims trailing spaces** when
it builds the SQL statement text, so the compiled program stores char columns *trimmed* while a
Python data-access layer writing the padded record field would store them *padded* — two states that
compare unequal byte for byte while representing the same COBOL value.

**This is the empirical reason `harness/normalize.py` has a trailing-space job**, and that reasoning
appears nowhere in the Agent Action Plan. Without it, a reviewer would read the normaliser's first
job as defensive tidying rather than as the reproduction of a specific bridge behaviour.

**Locators.** The ledger-name instance: `Ledger-Name pic x(24)` at `[copybooks/wsledger.cob:L27]`
becomes `HV-LEDGER-NAME PIC X(32)` at `[common/nominalMT.cbl:L299]` and `LEDGER-NAME char(32)` at
`[mysql/ACASDB.sql:L127]`. The trim is `[common/nominalMT.cbl:L1065-L1067]`, which builds the
statement fragment with `FUNCTION TRIM (HV-LEDGER-NAME,TRAILING)`. The behaviour is pervasive rather
than incidental: there are **23** `FUNCTION TRIM` sites in `common/nominalMT.cbl` and **29** in
`common/glpostingMT.cbl`.

⚠️ A **second instance the Agent Action Plan does not record**, recovered from the generated
dictionary and then verified in the frozen source: `OI-Description pic x(25)` at
`[copybooks/slwsoi.cob:L32]` becomes `HV-OI3-DESCRIPTION PIC X(32)` at `[common/otm3MT.cbl:L310]` and
`OI3-DESCRIPTION char(32)` at `[mysql/ACASDB.sql:L905]` — a 25 to 32 drift rather than 24 to 32. The
dictionary carries exactly two `A-12` entries, `GLLEDGER-REC.LEDGER-NAME` and
`SAITM3-REC.OI3-DESCRIPTION`, which is how the second one came to light.

**Reproducing module.** `acas_posting/dal/acas005_gl_nominal.py` for the write side, and
`harness/normalize.py` for the comparison side. The normaliser's job removes **trailing** ASCII
spaces only, never leading ones, because a COBOL alphanumeric `MOVE` is left-justified with right
padding and a leading space is therefore content.

**Test-locked.** No, not as an assertion of the defect itself. It is covered indirectly by
`tests/arithmetic/test_pic_field_descriptors.py`, which asserts the descriptor widths, and by
`tests/arithmetic/test_ledger_balance_accumulation.py`, which carries it as context. The trim's
effect is only observable in a table dump, so the scenario tier is where it is actually exercised.

**Status.** REPRODUCED.

### A-13 † — two entirely silent skips

**Description.** `gl072` discards records on two conditions and says nothing whatsoever about either
one: no message, no counter, no log line, no trace. A batch whose number is not numeric is skipped,
and a record for which the handler returned a specific error is skipped. Both simply loop.

The obligation here is unusual and worth stating explicitly: the Python reproduction must be
**equally silent**. Adding a warning would be adding behaviour, which R-3 forbids and R-4 makes a
failure — and it would also be observable in a log a reviewer might diff.

**Locators.** ⚠️ The corrected sites are `[general/gl072.cbl:L291-L292]` — `if post-batch not
numeric` at L291 and `go to loop.` at L292 — and `[general/gl072.cbl:L306-L307]` — `if we-error
equal 999` at L306 and `go to loop.` at L307. The Agent Action Plan's L289-L290 and L303-L304 do not
resolve to these statements; §8 records the correction.

⭐ There is a **second `we-error = 999` site the Agent Action Plan omits**, at
`[general/gl072.cbl:L348-L349]`, inside the headings paragraph: `if we-error equal 999` then `go to
headings-end.` Its disposition differs from the loop sites — it abandons the *headings* rather than
the *record* — so it is a third silent path, not a duplicate of the second.

**Reproducing module.** `acas_posting/programs/gl072_transaction_update.py`.

**Test-locked.** Yes, and **once per path**, because the two skips are two dispositions rather than
one. **Primary locks:** skip (a), the non-numeric batch number, is owned by
`tests/scenarios/test_mixed_accepted_rejected_batch.py::test_a13_non_numeric_batch_number_skipped_silently`;
skip (b), `we-error = 999`, by
`tests/scenarios/test_mixed_accepted_rejected_batch.py::test_a13_we_error_999_record_skipped_silently`.
The same file's
`test_skipped_postings_do_not_perturb_sequential_nominal_cursor` locks the A-13 / A-14 interaction —
that a silent skip must not move the sequential cursor A-14 depends on. **Supporting lock:**
`tests/arithmetic/test_move_truncation.py` owns the *class condition* the first skip tests, asserting
that `is_numeric_class` never raises whatever the item holds, which is the primitive the skip is built
on rather than the skip itself. **Contextual coverage only:**
`tests/arithmetic/test_ledger_balance_accumulation.py` and
`tests/arithmetic/test_irs_date_component_derivation.py`.

**Status.** REPRODUCED.

**Compiled reachability update (2026-08-04).** The two record-skip sites are
real, but the loader path available to the mandated RDBMS scenarios cannot
reach them with independently keyed postings. `bb000-HV-Load` never moves
`WS-Post-rrn` into `HV-POST-RRN`, so non-fetch writes use the initialised key
zero. `gl070` then skips that posting earlier at
`[general/gl070.cbl:L490-L493]`. The `mixed_accepted_rejected` journey was
therefore re-derived as two batches plus one posting and explicitly proves an
unchanged result; fabricating six addressable posting rows would test a state
the compiled loader cannot create. The arithmetic lock on the silent
disposition remains valid, while
[`scenario-diff-evidence.md`](scenario-diff-evidence.md) records why the
scenario does not pretend the sites are reachable.

### A-14 † — the nominal account located by sequential read

**Description.** `gl072` finds the nominal-ledger account for each posting with a **sequential**
read-next rather than an indexed read by key. It lands on the correct account only because `gl071`
has already emitted the transaction stream in nominal-key order. Perturb the sort — change its
stability, change its key composition, change the tie-break — and the program **silently posts to
the wrong account**. No error, no diagnostic, wrong balances.

This is the entry that turns a sorting detail into a correctness requirement, and it is why the
migration's sort primitive guarantees stability rather than merely being convenient.

**Locators.** ⚠️ The read is `[general/gl072.cbl:L408]` — `perform GL-Nominal-Read-Next.` with the
maintainer's comment `*> read  ledger-file  record.` The key move that precedes it is
`[general/gl072.cbl:L405]` and the guard on the read is `[general/gl072.cbl:L407]`. The
`if read-ledger not = "R"` at `[general/gl072.cbl:L410-L411]` comes **after** the read and is a
different test with a different consequence — it zeroes the running totals — so it must not be
mistaken for the read guard. The Agent Action Plan's L410-L412 points at that post-read block rather
than at the read; §8 records the correction.

**Reproducing module.** `acas_posting/programs/gl072_transaction_update.py` for the sequential read,
and `acas_posting/cobol/sortverb.py` for the stability guarantee the read depends on. The sort
module's own header cites `[general/gl072.cbl:L408]` and the L407-L408 pair, so the two ends of the
dependency name each other.

**Test-locked.** Yes — `tests/arithmetic/test_ledger_balance_accumulation.py`. The generated
dictionary additionally carries `A-14` on **28 work-record field entries** — the
`post-trans-record` fields that `gl071` sorts and `gl072` walks — which is the field-level record of
which layout the ordering dependency runs through.

**Status.** **REPRODUCED — VALUE MEASURED.** The read itself was always reproduced. What the compiled
sort does with a **tie** on the sort key was the separate question, and it has been watched: fed five records
through `gl071`'s four-key tuple with three of them sharing the whole tuple, the compiled `SORT` returned the
three tied records **in input order**. The sort is STABLE.

That is the answer this anomaly needed rather than merely an answer, because the sequential read is only
correct if the upstream order is deterministic: an unstable sort would hand `gl072` tied postings in an
arbitrary sequence, which leaves the final balance alone but changes `POST-RRN` assignment and therefore the
compared rows. `[acas_posting/cobol/sortverb.py]` guarantees stability, so the migrated side matches.
Question `Q-SORT-TIE-ORDER` in [`ambiguity-resolutions.md`](ambiguity-resolutions.md) carries the inputs and
the observed output.

### A-15 — the batch record's declared length contradicts the sum of its fields

**Description.** The batch record copybook carries three consecutive header comments recording two
different declared lengths and the maintainer's own inability to reconcile them, complete with
**two question marks**. It matters because if the declared length rather than the field sum governs
the record actually read, the trailing fields are misaligned.

**Locators.** `[copybooks/wsbatch.cob:L7-L9]`, verbatim in shape:

- L7 — `*> 96 bytes 26/03/09`
- L8 — `*> 98 bytes 20/12/11 (no, dont understand as I count 96)`
- L9 — `*>   but function length (Batch-record) says 98?`

The Agent Action Plan cites the file without a line; §8 records the correction. §14.2 sets this
entry against its two siblings in `copybooks/wspost.cob`, which look superficially identical and are
**not** of equal standing — one is explained and one is arithmetically resolved. Conflating the three
would either overstate or understate the uncertainty, and both are damaging.

**Reproducing module.** `acas_posting/records/gl_batch.py`, which records the contradiction rather
than resolving it, and comments the fields a length misalignment would move.

**Test-locked.** Carried as context by `tests/arithmetic/test_pic_field_descriptors.py`,
`tests/arithmetic/test_comp3_packed_decimal.py` and
`tests/arithmetic/test_control_total_comparison.py`, which assert the `Q-4` reference rather than a
layout. The measurement below did not change what those tests assert, because the layout they were
already built on is the one the measurement confirmed.

**Status.** **REPRODUCED — and the contradiction turns out to be a stale comment, not a live
ambiguity.**

Measured on the compiled oracle, 2026-08-07, GnuCOBOL 3.2.0, by `copy`-ing the frozen copybooks
into a probe and asking the compiler for its own layout:

| observable | measured |
| --- | --- |
| `FUNCTION LENGTH(WS-Batch-Record)` — the WS copy | **96** |
| `FUNCTION LENGTH(Batch-Record)` — the `fdbatch.cob` copy | **96** |
| sum of the ten members' own `FUNCTION LENGTH` values | **96** |
| padding implied by the difference | **none** |
| first byte of `Description` | **53** — exactly where the field sum puts it |
| `Description` read back at 53 for 24 bytes | intact, undisplaced |
| bytes 92–96 | `54321` = `Batch-Start`, so the record ends where the field sum says |

Member widths, for the record: `WS-Batch-Key` 6, `Items` 2, `Batch-Status` 1, `Cleared-Status` 1,
`Bcycle` 2, `Dates` 16 (four `binary-long` at 4 each, stored little-endian), `Amounts` 24 (four
`comp-3` at 6 each for eleven digits plus a sign nibble), `Description` 24, `posting-data` 15,
`Batch-Start` 5.

**So the L9 claim — *"but function length (Batch-record) says 98?"* — is false under this
compiler.** `FUNCTION LENGTH` and the field sum give the same 96, which means there was never a
choice between them to make, and the two-byte displacement the question was about does not occur.
Whatever compiler produced a 98 in 2011 is not the compiler this migration's oracle uses.
`acas_posting/records/gl_batch.py` builds its layout from the declared pictures — the field sum —
and that decision is now **measured correct** rather than assumed.

**Why this entry survives its own resolution.** The contradictory comment is still sitting in
`copybooks/wsbatch.cob:L7-L9` and in `copybooks/fdbatch.cob:L6-L8`, unchanged and unchangeable under
the freeze, where the next person to read either file will hit it and reach for the same question.
Recording that it is *answered and answered false* is the only thing that stops the question being
re-opened. See **`Q-4`** in [`ambiguity-resolutions.md`](ambiguity-resolutions.md) for the probe and
the full byte attribution; the dictionary continues to emit `Q-4` on **28 field entries**, which is
correct — the identifier now points at a resolved entry rather than an open one.

⚠️ **One probe hazard worth passing on**, because it produced a wrong answer before it produced the
right one. The first run located `Description` by scanning for its fill character `D`, having filled
`Actual-Vat` with `444444444.44` — whose packed bytes are `0x44`, which *is* ASCII `D`. The scan
found the amount, at byte 47, and would have been read as a six-byte displacement. `Q-4`'s own
experiment design had said to choose amounts whose packed representation cannot alias a text
character; ignoring that advice manufactured a false finding. The confirming run used
`555555555.55` and an `ABCDEFGH…` description, and located byte 53 unambiguously.

### A-16 — the date module returns its output field unchanged on a bad date

**Description.** `maps04` validates a ten-character UK date and converts it to a binary day number.
On **any** rejection it falls straight through to its exit **without touching its output field**, so
the caller sees whatever was in that field beforehand. Its own remarks nevertheless document that
errors return zero. Both statements are true only because the one caller that has been traced
**pre-zeroes** the field immediately before the call. The documented contract is therefore an
accident of caller discipline, not a property of the module.

**Locators.** The six-part reject test is `[common/maps04.cbl:L140-L146]`, ending in `go to
Main-Exit.` at L146 with the output field `A-Bin` never assigned. The second rejection, on a
calendar-invalid date, is `[common/maps04.cbl:L153-L154]`, with the same untouched exit. The
documented claim is `[common/maps04.cbl:L163]` — `*>  Date errors returned as A-Bin equal zero *`.
The caller's pre-zero is `[copybooks/Proc-ACAS-Mapser-RDB.cob:L78]` — `move zero to u-bin.` —
immediately before the call at L79 and the unconditional `move u-bin to run-date.` at L80. The clock
read that supplies the date is L72 of the same copybook.

⚠️ **THE CLOCK-READ CENSUS, CORRECTED.** That read is **not** the only one in the call chain, and an
earlier revision of this register said it was. The accurate statement, measured over the frozen tree
rather than carried over from the Agent Action Plan's phrasing:

- **All twelve in-scope posting programs contain ZERO clock reads.** `function current-date` appears in
  none of `gl051`, `gl070`, `gl071`, `gl072`, `gl080`, `sl055`, `sl060`, `sl100`, `pl055`, `pl060`,
  `pl100` or `irs030`; every one receives both date observables through linkage. **That zero is the
  entire basis of the controlled-clock design**, and it is what the Plan's conclusion rests on.
- **The posting cycle's call chain holds FIVE `function current-date` reads, not one**: the date-service
  copybook at `[copybooks/Proc-ACAS-Mapser-RDB.cob:L72]` and one in each menu shell —
  `[general/general.cbl:L371]`, `[sales/sales.cbl:L323]`, `[purchase/purchase.cbl:L318]`,
  `[irs/irs.cbl:L480]` — with a sixth in `[common/ACAS.cbl:L353]`. Counting `accept … from date` and
  `accept … from time` as well, the census over those six files is **fourteen** ambient reads;
  `tests/determinism/test_two_runs_byte_identical.py` publishes it site by site.
- **Beyond that chain the frozen tree holds further reads**, all in programs no scenario reaches:
  `[common/ACAS-Sysout.cbl:L107]`, `[common/fhlogger.cbl:L219]`, `[common/auditLD2.cbl:L192]` and L389,
  `[common/makesqltable-free.cbl:L81]` and L320, `[common/makesqltable-original.cbl:L78]` and L303, and
  `[stock/stock.cbl:L302]`.

Nothing about **this** anomaly changes: the pre-zero at L78 and the store at L80 are the caller
discipline the documented contract depends on, whichever read supplied the date.

A-NEW-2 records a **second, independent** contradiction in the same remarks block, which is why the
block as a whole is treated as unreliable rather than merely imprecise.

**Reproducing module.** `acas_posting/dates.py`, which reproduces the untouched-output behaviour
rather than zeroing, and `acas_posting/clock.py`, which reproduces the caller's pre-zero and the
unconditional store that follows it. Both modules cite these exact lines at the reproduction site.

**Test-locked.** No. The behaviour is only observable through a caller, and the two in-scope callers
pre-zero, so there is no arithmetic-tier assertion that can distinguish "returned zero" from "left
the pre-zeroed value alone". That indistinguishability is itself the finding.

**Status.** REPRODUCED. Whether **every** in-scope caller pre-zeroes has not been proven for all
callers; that residue is carried in [`ambiguity-resolutions.md`](ambiguity-resolutions.md) as the
date-contract question.

### A-17 — an unexplained move carrying the maintainer's own `*> Why ?`

**Description.** All four Sales and Purchase posting programs perform the same move of a relative
record number into a postings counter, each annotated by the maintainer with an inline `*> Why ?`.
The move is preserved exactly, in all four programs, because the author of the code does not know why
it is there and therefore neither can this migration.

**Locators.** `[sales/sl060.cbl:L1173]`, `[purchase/pl060.cbl:L1028]`, `[sales/sl100.cbl:L691]` and
`[purchase/pl100.cbl:L672]` — four sites, identical statement, identical comment. Note that each sits
on the line immediately after the wrong-program comment recorded as A-NEW-10, and immediately before
the batch close, which is the same three-line neighbourhood that carries A-1.

**Reproducing module.** All four Sales and Purchase program modules:
`acas_posting/programs/sl060_invoice_posting.py`,
`acas_posting/programs/sl100_cash_posting.py`,
`acas_posting/programs/pl060_order_posting.py` and
`acas_posting/programs/pl100_payment_posting.py`.

**Test-locked.** Not as an arithmetic-tier assertion. The move's effect is only observable once the
source counter has advanced past the receiving field's range, which no in-scope scenario reaches; the
measurement below was taken with a probe rather than a run, and is recorded rather than asserted.

**Status.** **REPRODUCED — and the effect is now measured, in both of the database columns it
reaches.**

The statement moves a five-digit source into a two-byte receiver:

| | declaration | locator | measured width |
| --- | --- | --- | --- |
| source | `Rrn pic 9(5) comp` | `[copybooks/wsfnctn.cob:L24]` | 4 bytes |
| receiver | `Postings binary-short` | `[copybooks/wssystem.cob:L184]` | 2 bytes |

`[copybooks/wssystem.cob:L184]` annotates the receiver `*> 9(4) comp`, and **both halves of that
annotation are wrong**: `binary-short` is signed, and its range is not the four digits the comment
implies.

It is database-visible **twice**, which is why it is worth measuring at all rather than merely
preserving. `Postings` is a `SYSTEM-REC` column in its own right; and
`[sales/sl060.cbl:L1037]` reads `add postings 1 giving Batch-start`, which writes
`GLBATCH-REC.BATCH-START`, declared `pic 9(5)` **unsigned** at `[copybooks/wsbatch.cob:L54]`.

Measured on the compiled oracle, 2026-08-07, GnuCOBOL 3.2.0:

| `Rrn` | → `Postings` | → `Batch-Start` | |
| --- | --- | --- | --- |
| `1` | `+00001` | `00002` | |
| `9999` | `+09999` | `10000` | |
| `10000` | `+10000` | `10001` | **not** truncated to four digits |
| `12345` | `+12345` | `12346` | **not** truncated to four digits |
| `32767` | `+32767` | `32768` | the last value that survives |
| `32768` | `-32768` | `32767` | signed 16-bit wrap, silent |
| `65535` | `-00001` | `00000` | the database column becomes **zero** |
| `99999` | `-31073` | `31072` | `99999 mod 65536 = 34463`; `34463 − 65536 = −31073` |

and `move -1 to Postings` yields `-00001`, confirming the receiver is signed.

Four things follow, and the third and fourth are the ones that matter:

1. `binary-short` is **signed**, contradicting its own comment.
2. There is **no decimal truncation at the implied picture**. The full signed binary range governs,
   not the four digits — so this compiler is not applying `binary-truncate` to this storage class.
   That is also the answer to the `binary-short` half of `Q-5.1`.
3. Past `32767` the store **wraps as a signed 16-bit integer, silently**, with no diagnostic and no
   trace.
4. The negative then reaches the **unsigned** `pic 9(5)` `Batch-Start` as its **absolute value** —
   the same magnitude-only rule `Q-3` measured at the bridge boundary, occurring here at a plain
   COBOL store with no bridge involved. So one move nobody can explain can drive a `GLBATCH-REC`
   column to `00000`, or to a wrapped magnitude bearing no relation to the record count, and nothing
   anywhere reports it.

**This is latent rather than scenario-reachable** — it needs more than 32767 postings in a single
run, which no mandated scenario produces — so no scenario diff will ever show it. That is precisely
why it is written down. The move is preserved unchanged at all four sites, because R-4 forbids
repairing it and because the author of the code still does not know why it is there. See
`Q-A17-POSTINGS-EFFECT` in [`ambiguity-resolutions.md`](ambiguity-resolutions.md).

### A-18 — two percentage fields not carried into the IRS posting record

**Description.** When a Sales or Purchase posting fans out to the IRS transfer file, the debit and
credit **account numbers** are carried across but their two accompanying **percentage** fields are
not. The reason is structural rather than accidental — the transfer record has no fields for them —
but the maintainer flagged the omission as a concern in three separate inline comments and then
wrote the record anyway.

**Locators.** The fan-out block is `[sales/sl060.cbl:L1122-L1142]`. The debit account is moved at
`[sales/sl060.cbl:L1132]` and the credit account at `[sales/sl060.cbl:L1134]`, with no equivalent
move of `DR-PC` or `CR-PC` anywhere in the block. The maintainer's flags are
`[sales/sl060.cbl:L1123-L1124]` — *"The postings for GL NEEDS TO BE CHECKED if it is used etc"* and
*"and usage of DR-PC and CR-PC"* — then `[sales/sl060.cbl:L1133]` — *"Missing usage of DR-PC for GL
MUST be checked in GL ????"* — and `[sales/sl060.cbl:L1135]`, the same for `CR-PC`. The record is
nonetheless written at `[sales/sl060.cbl:L1142]`.

The structural confirmation is `[copybooks/wspost-irs.cob:L13-L25]`: the transfer record declares
`WS-IRS-Post-DR` and `WS-IRS-Post-CR` but **no percentage field for either**, so there is nowhere for
the two values to go. Note also `[sales/sl060.cbl:L1138-L1139]`, a multi-receiver move that stores
the literal 31 or 32 into the VAT account-definition field **and into a percentage field**, carrying
the maintainer's `*> IS IT ???`.

**Reproducing module.** `acas_posting/programs/sl060_invoice_posting.py`.

**Test-locked.** No. The two values are dropped, so there is no column in which to observe them; the
absence is the behaviour.

**Status.** REPRODUCED. Whether the literal stored into the percentage field at L1138-L1139 is
observable downstream, and in which column, is carried as `Q-VAT-PC-31` in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md).

### A-19 † — superseded commented-out VAT computes beside the live ones

**Description.** `irs030` computes VAT two ways, from net and from gross, and each live compute sits
immediately below a commented-out predecessor that references a **differently named rate field**.
The pair is preserved as-is: the live line is reproduced and the dead line is recorded, because the
name change between them is the only evidence of which rate field is actually in force.

Both live computes are `ROUNDED`, and they are two of only five `ROUNDED` sites in the whole in-scope
cycle (§12). The from-gross path is additionally **destructive**: the line immediately after it
subtracts the computed VAT out of the posting amount, so the amount the caller passed in is not the
amount that continues.

**Locators.** From net: the superseded line is `[irs/irs030.cbl:L1550]` and the live compute is
`[irs/irs030.cbl:L1551]`. From gross: the superseded line is `[irs/irs030.cbl:L1561]` and the live
compute spans `[irs/irs030.cbl:L1562-L1563]`, followed by the destructive
`[irs/irs030.cbl:L1564]` — `subtract vat-amount from post-amount.`

⭐ The maintainer's flagged-but-unacted concern sits directly above the from-net compute at
`[irs/irs030.cbl:L1547-L1548]`: *"Calculate vat from net  - THIS MAY NEED A TEST FOR ONLY NON ZERO
VAT RATES"* and *"before compute but look like comes to zero ?"*. It is recorded because it is a
change the maintainer considered and did not make — and under R-4 the not-making is the
specification.

**Reproducing module.** `acas_posting/programs/irs030_posting.py`.

**Test-locked.** Yes — `tests/arithmetic/test_compute_rounded_half_up.py` for the rounding mode,
`tests/arithmetic/test_irs_vat_from_net.py` for the from-net path and its post-condition that the
posting amount is unchanged, and `tests/arithmetic/test_irs_vat_from_gross.py` for the destructive
subtract at L1564.

**Status.** REPRODUCED. The exact intermediate precision of the compound from-gross expression under
the compiler's default arithmetic was carried as a question in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md), alongside `Q-ROUNDED-OVERFLOW-ORDER`, and
**both have since been measured**: `Q-2` is **`RESOLVED BY ORACLE`** (2026-08-07) — extended precision
throughout, quantized once at the store — and `Q-ROUNDED-OVERFLOW-ORDER` is **`RESOLVED BY ORACLE`**
on the same date. Measuring the precision did not change this anomaly's standing: it is REPRODUCED
either way, because knowing what the compiler does is not the same as the behaviour being correct
(R-4).

### A-20 — two spare fields carrying the Sales prefix inside the Purchase group

**Description.** The period-totals record has a Sales group and a Purchase group, each ending in two
spare money fields. The Purchase group's two spares are named with the **Sales** prefix. The names
are wrong; the layout is not. Renaming them would be a change to a field name that the generated
dictionary, the record module and the schema column names all agree on, so the misnaming is carried
through to the Python attribute names deliberately.

**Locators.** `[copybooks/wssys4.cob:L29-L30]` declares `sl4-spare3` and `sl4-spare4` inside
`Purchase-Ledger-Data`, whose group header is `[copybooks/wssys4.cob:L20]`. The contrast is the
legitimate Sales pair `sl4-spare1` and `sl4-spare2` at `[copybooks/wssys4.cob:L18-L19]`, inside
`Sales-Ledger-Data` at `[copybooks/wssys4.cob:L9]`. The Agent Action Plan cites the file without a
line; §8 records the correction. The generated dictionary carries exactly two `A-20` entries,
`SYSTOT-REC.SL4-SPARE3` and `SYSTOT-REC.SL4-SPARE4`.

**Reproducing module.** `acas_posting/records/system_record_4.py`, which keeps both names and marks
each at its declaration site.

**Test-locked.** No, not as a behaviour — a name is not an observable in a table dump beyond the
column name itself, which already matches. It is carried by
`tests/arithmetic/test_pic_field_descriptors.py` and
`tests/arithmetic/test_comp3_packed_decimal.py` as a descriptor-level fact.

**Status.** REPRODUCED.

### A-21 † — field-name collisions forcing qualified references, in two spellings

**Description.** Three posting-related copybooks are in scope in the same program at the same time
and they declare colliding leaf names, so several references must be **qualified** to compile at all.
The program qualifies them in **both** COBOL spellings — `in` and `of` — for the same purpose and
within a few lines of each other. Neither spelling is wrong; the inconsistency is the finding, and it
is preserved because a paragraph-to-function traceability reader comparing the two files needs to see
the same shape on both sides.

**Locators.** ⚠️ The verified sites in `gl070` are `[general/gl070.cbl:L497]` — `move post-code in
WS-Posting-Record   to  pre-code.`, the **`in`** form — and `[general/gl070.cbl:L521]` — `if vat-ac
of WS-Posting-Record = zero` — and `[general/gl070.cbl:L525]` — `move vat-ac of WS-Posting-Record  to
pre-ac.`, both the **`of`** form. The Agent Action Plan's `L510` is **wrong**: that line is an
ordinary unqualified `move post-cr to pre-ac.` §8 records the correction.

⭐ The collision source is `[copybooks/wspost.cob:L12-L15]`: `01 WS-Posting-Record.` at L12 contains
the group `WS-Post-Key.` at L14, whose first leaf is an **unqualified item named `Batch`** at L15 —
`05 Batch pic 9(5).` — while `copybooks/wsbatch.cob` carries its own batch fields in the same
program.

⭐ **A-21 also extends to `gl080`**, at `[general/gl080.cbl:L467]` (the `in` form),
`[general/gl080.cbl:L497]` and `[general/gl080.cbl:L501]` (both the `of` form) — the same mixed
spelling, in the archive-write path rather than the pre-process path.

**Reproducing module.** `acas_posting/programs/gl070_transaction_pre_process.py` and
`acas_posting/programs/gl080_end_of_cycle.py`. In Python the qualification disappears into the
receiving object, so the sites are marked by comment rather than by syntax — which is exactly why the
locators above have to be right.

**Test-locked.** Yes — `tests/arithmetic/test_double_entry_explosion.py`, which exercises the
three-leg explosion these qualified references drive.

**Status.** REPRODUCED.

### A-22 — a wrapper section named after the interface copybook, exiting under the callee's name

**Description.** The thin wrapper section around the date module is named after the **interface
copybook** while its exit label is named after the **called program**. The two names differ by one
digit and refer to different things, which is a live trap for anyone using paragraph names to
navigate. It is preserved, and named in the traceability mapping, so that a reader following the
paragraph-to-function correspondence is not left wondering which name was dropped.

**Locators.** `[general/gl070.cbl:L603-L609]`: `maps03 section.` at L603, `call "maps04" using
maps03-ws.` at L606, and `maps04-exit.` at L608.

⭐ **Two occurrences, not one.** The same pairing appears in `gl051` at
`[general/gl051.cbl:L1273]` — `maps03 section.` — with the call at `[general/gl051.cbl:L1276]` and
the exit at `[general/gl051.cbl:L1278]`.

**Reproducing module.** `acas_posting/programs/gl070_transaction_pre_process.py` and
`acas_posting/programs/gl051_batch_control_check.py`. The naming is carried into
[`traceability.md`](traceability.md)'s paragraph-to-function table rather than smoothed away.

**Test-locked.** No. A section name has no runtime observable. It is cited by
`tests/arithmetic/test_irs_vat_from_net.py` as traceability context.

**Status.** REPRODUCED.

---

## 11. The anomaly to locking-test ownership map

**Fifteen** of the twenty-two entries carry a **behaviour lock** — a test that asserts the defect
itself, **so that a future well-meaning "fix" fails the suite** instead of passing unnoticed. Three more
carry a weaker guarantee and four carry none; the reconciled census is at the end of this section, and
it distinguishes four relationships that an earlier revision of this table blurred into one.

This is the ownership map. The "primary lock" column is the test that owns the assertion; the "also
cites" column was recovered by reading every test file in this checkout, so that a reader chasing an
identifier finds every file that mentions it rather than only the owner. All TWENTY files under
`tests/arithmetic/` are present in the repository and pass on a bare host, with no Docker, no MariaDB
and no GnuCOBOL: the fourteen AAP §0.4.1.7 names, plus the shared-storage and dispatch-boundary file,
the deployment-contract file, and the four that drive the shipped modules directly — the gl080
end-of-cycle file, the gl072 silent-skip file, the CLI-seam file and the shipped-close/rejection file
that holds A-1's and the IR032 path's call sequences. (Fifteen is the number of
ANOMALIES carrying a behaviour lock, not the number of files: several files lock more than one, and
several of the nineteen lock none because they are structural rather than arithmetic.)

⚠️ **This table listed fourteen rows for fifteen files at one revision, and stated fifteen and then
sixteen and then eighteen as the directory grew.** `test_shared_storage_and_dispatch_boundaries.py`
was named in the prose below the table, as **A-6**'s lock, but had no row of its own — so a reader
scanning the table for the file would not have found it, and the stated count of files agreed with
the number of rows rather than with the tree. Every file now has a row in the second table of this
section, and the count is **twenty** because the directory holds twenty — nineteen until
`test_shipped_close_and_rejection_paths.py` was added for findings MJ-07 and MJ-11.
`test_documented_inventory_counts_match_the_tree` reads the tree, and it is what caught this revision
rather than a reader noticing.

- **PRIMARY LOCK** — the test that owns the assertion of *this defect*. Break the defect and this test
  goes red. There is exactly one per entry, except where an entry has two independent dispositions, in
  which case there is one per disposition.
- **SUPPORTING LOCK** — a test that asserts a *primitive the defect is built on* rather than the defect.
  Useful, and it would catch some regressions, but it is not where the defect lives.
- **RECORD LOCK** — a test that asserts the anomaly reference is still carried on the field descriptor,
  so the *record* cannot be quietly deleted. It does not assert a behaviour and must not be read as
  though it did.
- **CONTEXTUAL CITATION** — a file that merely mentions the identifier, usually for traceability. **Not
  a lock at all**, and previously the most misleading kind of entry in this table: a reader who followed
  a mention to an arithmetic test and found no assertion had been sent to the wrong file.

**The arithmetic tier — twenty files**, all present, all passing on a bare host with no Docker, no
MariaDB and no GnuCOBOL. The table immediately below carries a row for the fifteen that own an anomaly
relationship; the second table in this section carries a row for **every** file, which is the one to
read for completeness. (Twenty, not the fourteen AAP §0.4.1.7 names: the shared-storage,
deployment-contract, two shipped-module, CLI-seam and shipped-close/rejection files were added during
QA remediation.)

| Test file | Primary lock | Supporting lock | Contextual citation |
| --- | --- | --- | --- |
| `tests/arithmetic/test_pic_field_descriptors.py` | A-11 | **record locks** for A-12, A-15, A-20 — `assert "A-12" in descriptor.anomaly_refs()` and its two equivalents | A-7 |
| `tests/arithmetic/test_comp3_packed_decimal.py` | A-8, first truncation | — | A-11, A-15, A-20 |
| `tests/arithmetic/test_comp_binary.py` | A-8, second truncation, and A-11 | — | — |
| `tests/arithmetic/test_sign_leading_display.py` | the two `sign leading` spellings; the primary R-6 site | — | — |
| `tests/arithmetic/test_move_truncation.py` | — | A-13, via `is_numeric_class` never raising | A-4 |
| `tests/arithmetic/test_compute_truncate_unrounded.py` | **A-8, A-9, A-10** — the primary R-4 site | — | A-11 |
| `tests/arithmetic/test_compute_rounded_half_up.py` | the five `ROUNDED` sites, the three adjacency pairs, and A-19 | — | — |
| `tests/arithmetic/test_irs_vat_from_net.py` | the post-amount-unchanged post-condition, and A-19 | — | A-1, A-22 |
| `tests/arithmetic/test_irs_vat_from_gross.py` | the destructive `[irs/irs030.cbl:L1564]` | — | A-19 |
| `tests/arithmetic/test_gl080_cycle_divide_rounded.py` | **A-2, A-3** | — | A-11 |
| `tests/arithmetic/test_double_entry_explosion.py` | A-21 | — | — |
| `tests/arithmetic/test_control_total_comparison.py` | the three batch dispositions | A-15, as context | A-11 |
| `tests/arithmetic/test_ledger_balance_accumulation.py` | **A-14**, the sequential read | — | A-12, A-13 |
| `tests/arithmetic/test_irs_date_component_derivation.py` | **A-7**, the guarded derivation | — | A-13 |
| `tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` | the shared storage and dispatch boundaries | — | — |

**The scenario tier — eight files, all present in this checkout and read to build the rows below.**
Four entries have their primary lock here rather than in the arithmetic tier, because their only
observable is end state, and A-6 has its state-level lock here for the same reason:

| Entry | Primary lock | Why it cannot be an arithmetic assertion |
| --- | --- | --- |
| `tests/arithmetic/test_pic_field_descriptors.py` | A-11, A-12, A-15, A-20 | A-7 |
| `tests/arithmetic/test_comp3_packed_decimal.py` | A-8, first truncation | A-11, A-15, A-20 |
| `tests/arithmetic/test_comp_binary.py` | A-8, second truncation, and A-11 | — |
| `tests/arithmetic/test_sign_leading_display.py` | the two `sign leading` spellings; the primary R-6 site | — |
| `tests/arithmetic/test_move_truncation.py` | A-13 | A-4 |
| `tests/arithmetic/test_compute_truncate_unrounded.py` | **A-8, A-9, A-10** — the primary R-4 site | A-11 |
| `tests/arithmetic/test_compute_rounded_half_up.py` | the five `ROUNDED` sites, the three adjacency pairs, and A-19 | — |
| `tests/arithmetic/test_irs_vat_from_net.py` | the post-amount-unchanged post-condition, and A-19 | A-1, A-22 |
| `tests/arithmetic/test_irs_vat_from_gross.py` | the destructive `[irs/irs030.cbl:L1564]` | A-19 |
| `tests/arithmetic/test_gl080_cycle_divide_rounded.py` | **A-2, A-3** | A-11 |
| `tests/arithmetic/test_double_entry_explosion.py` | A-21 | — |
| `tests/arithmetic/test_control_total_comparison.py` | the three batch dispositions, and A-15 as context | A-11 |
| `tests/arithmetic/test_ledger_balance_accumulation.py` | **A-14** | A-12, A-13 |
| `tests/arithmetic/test_irs_date_component_derivation.py` | **A-7** | A-13 |
| `tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` | **A-6** at §20 — the mechanism half: all four refused functions invoked through both alias sets — and **N-KEY** at §19 | A-2, A-3, A-11, A-13 |
| `tests/arithmetic/test_gl080_shipped_end_of_cycle.py` | **A-2, A-3** in the SHIPPED module rather than a transcription | A-11 |
| `tests/arithmetic/test_gl072_shipped_silent_skips.py` | **A-13** reachability: both silent skips driven, each with a positive witness | A-14 |
| `tests/arithmetic/test_cli_seams_and_failure_paths.py` | the entry-point seams the scenario tier cannot reach without the stack | — |
| `tests/arithmetic/test_shipped_close_and_rejection_paths.py` | **A-1** — the nested posting close, over the full `IRS-Instead` × `Level-1` truth table in the SHIPPED paragraph — and the **IR032 clean rejection**, the sibling path of A-4 | A-4 |
| `tests/arithmetic/test_deployment_contract_boundaries.py` | the deployment, manifest and register-consistency contracts; no anomaly of its own | — |

Three entries in the dagger set are locked outside the arithmetic tier as well, because their
observable is end state rather than a computed value:

- **A-5** is locked by the IRS scenario test named in AAP §0.4.1.7, whose empty-diff assertion is the
  only observable that can see a lost update. A lost update is an ordering fault across a loop
  boundary, not an arithmetic one, so no arithmetic-tier assertion can distinguish it.
- **A-4** is additionally exercised end-to-end by the scenario tier named in the same section, because
  a half-posted double entry shows up as table state: the debit is written and nothing balances it.
- **A-1** is **not**, and the distinction matters (finding MJ-07). A file left unclosed shows up in **no**
  table — `GL-Posting-Close` writes nothing — so the scenario tier is A-1's **state witness** and its
  **primary lock** is `tests/arithmetic/test_shipped_close_and_rejection_paths.py`, which drives the
  shipped paragraph and asserts the verb sequence. An earlier revision of this bullet paired A-1 with
  A-4 as though both were observable in state; they are not, and A-1's own entry records the correction.
- **A-6**'s state half lives in the IRS scenario file, which compares the transfer table's pre-run
  digest against its post-run digest per side. The mechanism half is in the arithmetic tier above,
  where the handler can be called directly; neither half claims the other's ground.

**A-6** was in this list and no longer is. It is locked in BOTH tiers now — at the handler by
`tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` §20, which calls the migrated
`acas008` once per refused verb and requires the measured `WE-Error 988` / `FS-Reply 99` pair, and at
the state level by `tests/scenarios/test_clean_batch_post_irs.py`'s
`test_a6_rewrite_verb_can_never_succeed`. The ground it was listed on — that its observable is "a
status pair returned to a caller" rather than a table state — was a true premise with a false
conclusion: a status pair cannot be seen from a dump, but it is exactly what a direct call to the
data-access layer can assert.

**AND THE SAME MAP FROM THE OTHER DIRECTION, for the five entries whose observable is END STATE
rather than a computed value.** An earlier revision of this section named a test for three of them
that does not assert them, so each row below was re-verified by opening the test:

| Entry | Primary lock | Why the observable is a state |
| --- | --- | --- |
| **A-1** | `test_clean_batch_post_sl.py::test_a1_missing_period_gl_posting_close_not_executed`, with `test_clean_batch_post_pl.py::test_a1_control_pl060_terminating_period_is_present` as its paired control | an unclosed posting file is a table state, and it is observable only in pure-GL mode |
| **A-4** | `test_clean_batch_post_irs.py::test_a4_half_posted_double_entry_reproduced` | a committed debit with no balancing credit and no posting row is a state, not a computation |
| **A-5** | `test_clean_batch_post_irs.py::test_a5_lost_update_on_vat_control_accounts_reproduced` | a lost update is an ordering fault across a loop boundary |
| **A-6** — state-level lock IN ADDITION to its behaviour lock | `test_clean_batch_post_irs.py::test_a6_rewrite_verb_can_never_succeed` | the status pair is invisible to a dump, so at this tier the test asserts the only outcome the guard can leave, NO CHANGE on both sides |
| **A-13** | `test_mixed_accepted_rejected_batch.py::test_a13_non_numeric_batch_number_skipped_silently` for skip (a) and `::test_a13_we_error_999_record_skipped_silently` for skip (b), with `::test_skipped_postings_do_not_perturb_sequential_nominal_cursor` locking the A-13 / A-14 interaction | a *silent* skip has no observable except the row that is absent and the cursor that did not move |

**A-7** is locked at both ends: the arithmetic tier owns the derivation, and
`test_clean_batch_post_irs.py::test_a7_partial_date_component_derivation_is_dumped_as_stored` owns the
dumped row. The candidate `A-NEW-1` is likewise locked, by
`test_clean_batch_post_pl.py::test_a_new_1_second_apportionment_pass_never_runs`.

**Why the seven non-dagger entries are as they are**, stated once here rather than seven times in the
register. Three of them are **record locks** rather than nothing: `test_pic_field_descriptors.py`
asserts `"A-12" in descriptor.anomaly_refs()` and the equivalents for A-15 and A-20, so the *record*
cannot be quietly deleted even though no behaviour is pinned. The remaining four carry no lock of any
kind, because the observable is a **name or comment with no runtime effect** (A-22), a **value that is
dropped or is only visible in a table dump** (A-17, A-18), or a **behaviour visible only through a
caller that has not been proven for every caller** (A-16). Each of the seven is nonetheless carried at
its reproduction site by a comment citing the same locator this register cites, which is the third of
C-3's three places where engineering quality lives.

**THE CENSUS, RECONCILED, because an earlier revision of this section contradicted the register's own
per-entry `Test-locked` fields.** Four relationships exist and they are not interchangeable:

| Relationship | Entries | Count |
| --- | --- | ---: |
| **Behaviour lock** — a test asserts the defect itself, so breaking it turns the suite red. These are exactly the dagger (†) entries, in the index and in the entry headings alike. | A-1, A-2, A-3, A-4, A-5, A-6, A-7, A-8, A-9, A-10, A-11, A-13, A-14, A-19, A-21 | **15** |
| **Record lock only** — a test asserts that the anomaly reference is still carried on the field descriptor, so the *record* cannot be quietly deleted, without asserting a behaviour. `test_pic_field_descriptors.py` does this with `assert "A-12" in descriptor.anomaly_refs()` and the equivalents for A-15 and A-20. | A-12, A-15, A-20 | **3** |
| **No lock of any kind** | A-16, A-17, A-18, A-22 | **4** |

15 + 3 + 4 = **22**, with no entry counted twice.

⚠️ **This census read `14 + 1 + 3 + 4` at one revision, with A-6 in a `state-level lock only` row of its
own.** That was true of a tree in which the only A-6 assertion was the scenario tier's no-change claim.
It is not true of this one: `tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` now calls
the migrated `acas008` directly and asserts the measured `WE-Error 988` / `FS-Reply 99` pair seven ways,
which is a behaviour lock by this section's own definition — so A-6 carries the dagger and sits in the
first row. Its scenario-tier no-change assertion is a SECOND lock on an already-locked entry, listed
above with A-7's and A-13's extra locks rather than counted again here. A-7 additionally carries a
second lock in the scenario tier and A-13 a second and third; those too are extra locks on
already-locked entries and are not added to the census.

---

## 12. The five `ROUNDED` sites

COBOL truncates toward zero on store unless `ROUNDED` is written. Across the entire in-scope posting
cycle there are exactly **five** live `ROUNDED` sites, verified by enumerating every arithmetic
statement in the twelve in-scope programs and discarding commented-out lines:

| Site | Statement | Anchors |
| --- | --- | --- |
| `[general/gl051.cbl:L791]` | VAT from net, in the batch proof path | — |
| `[general/gl051.cbl:L796]` | VAT from gross, in the batch proof path | — |
| `[general/gl080.cbl:L328]` | the cycle-to-period divide whose result is a subscript | **A-2**, and A-NEW-6 |
| `[irs/irs030.cbl:L1551]` | VAT from net, in the IRS posting path | **A-19** |
| `[irs/irs030.cbl:L1562-L1563]` | VAT from gross, in the IRS posting path | **A-19**, and the destructive L1564 |

**Every other store truncates.** Truncation is therefore the default path in
`acas_posting/cobol/arithmetic.py` and rounding is the annotated exception, which is the correct way
round: getting it backwards would corrupt essentially every posted figure while leaving these five
sites correct.

---

## 13. Frozen-script and frozen-file defects

Thirteen further defects live in frozen files — build scripts, load scripts, the schema dump and the
vendored translator package. They are recorded here under **R-3** and **R-4**: the harness **works
around them rather than correcting them**, and the frozen files keep their defects. Every one was
verified directly in this checkout, and three corrections to the received brief are stated in place.

**13.1 — `comp-all.sh` swallows its own build failures.** The script ends with an echo and then a
bare `exit 0`, so a failed compile is invisible to the exit status: `[comp-all.sh:L44]` — `echo "We
Are all done but check for any error or warning messages"` — then `[comp-all.sh:L45]` — `exit 0`. The
file is 45 lines. The harness therefore cannot use the script's exit status as a build verdict and
must inspect the compile output itself.

**13.2 — the same unconditional `exit 0` appears in every compile script.** It is
`[common/comp-common.sh:L59]`, a second site the Agent Action Plan does not mention, and it is also
the last line of every per-directory script: `general/comp-gl.sh` (7 lines), `irs/comp-irs.sh` (9),
`purchase/comp-purchase.sh` (6), `sales/comp-sales.sh` (22) and `stock/comp-stock.sh` (7).

**13.3 — `common/masterLD.sh` is syntactically unrunnable, and could not be invoked even if it were.**
Three independent reasons, in ascending order of finality:

1. All **24** loader lines are written `if [ -e X.dat ]; then YLD fi`, omitting the mandatory `;` or
   newline before `fi` — `[common/masterLD.sh:L93-L116]`, twenty-four lines, all of that shape.
   `bash -n common/masterLD.sh` fails with `line 124: syntax error: unexpected end of file`, and the
   file is 123 lines.
2. Its own header says so: `[common/masterLD.sh:L4-L5]` reads `#   THIS SCRIPT HAS NOT YET BEEN
   TESTED` under a rule of carets. The `Changelog` corroborates it verbatim at
   `[Changelog:L21-L22]`: *"Revised scripts masterUNL.sh, masterRES.sh & / masterLD and so far only
   tested masterUNL."*
3. ⭐ It ends with an **interactive pager** — `[common/masterLD.sh:L119-L123]` closes with `less
   SYS-DISPLAY.log`, which would block a test run forever even if the syntax were repaired.

Two facts about its contract survive and are reproduced by `harness/seed.sh`. The loaders' exit
semantics are documented at `[common/masterLD.sh:L37-L39]` — 128 for parameters unset, 64 for the
RDB flag unset, 16 for a write error — with the maintainer's note at `[common/masterLD.sh:L41]` that
anything above 63 should abort. And there is a **strict-versus-lenient asymmetry** among the four
system-file loaders: three are checked with `-gt 63` at `[common/masterLD.sh:L56]`,
`[common/masterLD.sh:L65]` and `[common/masterLD.sh:L74]`, while the fourth — `dfltLD`, invoked at
`[common/masterLD.sh:L79]` — is checked with `!= 0` at `[common/masterLD.sh:L83]`.

**13.4 — `-Wno-goto-section` is a phantom flag.** A repository-wide search finds it in exactly three
places, all of them **changelog comments**: `[common/comp-common.sh:L8]`,
`[common/comp-common2.sh:L8]` and `[common/comp-common-no-rdbms-diags.sh:L9]`. It appears in **no
actual `cobc` invocation anywhere**.

⚠️ Correction to the received brief: the flag does **not** appear in `README.TXT` either.
`[README.TXT:L204-L207]` narrates the compiler warning about inter-section `GO TO` in prose, and
`[README.TXT:L208-L210]` claims *"an extra element is added to the compile commands in the scripts
for both with and without rdbms"* — a documentation-versus-code contradiction in its own right, and
recorded as such. The practical consequence for the migration is unchanged: inter-section `GO TO` is
a deliberate, pervasive idiom of this codebase, which is why the four-class taxonomy in AAP §0.4.2 is
the right approach.

**13.5 — `common/comp-common.sh` claims a dump flag it does not use.**
`[common/comp-common.sh:L11]` records *"Added to all comps  -fdump=all"*, yet **no live line in that
file carries `-fdump` at all**; the only occurrence of the string in the file is that comment.

⚠️ Correction to the received brief: the live `cobc` invocations in that file are at **L18, L21, L23,
L26, L29, L32, L34, L36, L40, L41, L42, L45, L51, L54 and L57** — fifteen lines. The brief's list
omits L18 (the `accept_numeric.c` compile) and L54 (the `*UNL.cbl` loop). Separately, the
per-directory scripts that *do* carry a dump flag carry `-fdump=ws`, not `-fdump=all`:
`[general/comp-gl.sh:L2]`, `L3`, `L5` and `[irs/comp-irs.sh:L2]`, `L3`, `L4`, `L6`.

**13.6 — `sales/comp-sales.sh` is the odd one out, and must not be harmonised.** Its header records
the divergence: `[sales/comp-sales.sh:L2]` — *"Removed all references to accept_numeric -- too many
problems."* — and the `accept_numeric` variants are commented out at L5, L11, L13 and L20.

⚠️ Correction to the received brief: the file has **three** live `cobc` lines, not one —
`[sales/comp-sales.sh:L7]` (the `sl*.cbl` loop), `[sales/comp-sales.sh:L9]` (`cobc -x sales.cbl`) and
`[sales/comp-sales.sh:L18]` (`cobc -m sales.cbl`). L7 is the only one that compiles the `sl*`
programs. The finding stands and is in fact stronger: **none** of the three carries `-fdump` or
`-fmissing-statement`, whereas the General and IRS scripts carry both. The Sales programs are
therefore compiled with a different flag set from their siblings, and the harness reproduces that
rather than levelling it.

**13.7 — the bridge trims trailing spaces.** See **A-12**. Recorded again here because it is the
empirical origin of `harness/normalize.py`'s first job, and because a reviewer who meets the
normaliser before the anomaly would otherwise read that job as defensive tidying.

**13.8 — a binary day-number column declared with a display width of one.**
`[mysql/ACASDB.sql:L1270]` declares `BL-END-CYCLE-DAT int(1) unsigned NOT NULL`. The parenthesised
number is a MySQL display-width hint and does not constrain the stored range, so a full day number
stores correctly — but the declaration reads as though it could not, and the schema is frozen, so it
stays.

**13.9 — the schema dump sets one character set and its tables declare another.**
`[mysql/ACASDB.sql:L16]` issues `SET NAMES utf8mb4` while **all 33** tables are created
`DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci`. The maintainer's own caveat sits in the header
at `[mysql/ACASDB.sql:L9-L11]`, warning that the defined character set may need changing to match a
given installation. The harness applies the file verbatim and changes neither.

**13.10 — the vendored translator disagrees with itself about its own version.** The package readme
says one thing — `presql2-latest.zip` at `presql2-package/README.SVN:L22`, *"presql release
(currently 1.14f)"* — and the program self-identifies as another, `presql2-package/presql2.cbl:L302`
declaring `ws-Prog-Version pic x(6) value " 2.22 "`. The harness pins the vendored archive rather
than a version string, so the disagreement is recorded and not resolved.

**13.11 — the bridge's C interface object has no build rule in the checkout.** `find . -name
'cobmysqlapi*'` returns **nothing**, yet the object is linked by nine live compile lines:
`[common/comp-common.sh:L26]`, `L32`, `L34`, `L36`, `L40`, `L41`, `L42`, `L45` and `L51`. Following
the compile scripts alone, the oracle cannot be built at all, and the failure appears at link time
with no obvious cause.

The rule was recovered from inside the vendored archive: `presql2-package/cobmysqlapi38.sh` is a
single line, `gcc -I/usr/local/mysql/include -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC`. The
superseded variants `presql2-package/old-apis/cobmysqlapi.005.c` and
`presql2-package/old-apis/cobmysqlapi3.c` must **not** be used. See AAP §0.5.2 and §0.8.7.

**13.12 — the translator needs a parameter file that is not present as a loose file.**
⚠️ Correction to the received brief, in the direction of accuracy rather than of severity: `find .
-name "*.param"` over the checkout returns **empty**, but the vendored archive **does** ship a
template at `presql2-package/presql2.param`. The defect is therefore not that the file does not
exist anywhere — it is that the checkout as delivered cannot run `presql2` until the archive is
unpacked and the template is populated for the target database.

The consequences are unforgiving. `presql2-package/cobmysqlapi38.c` exits **5** at its L130 when the
file is absent, and exits **6** at L136, L143, L150, L157, L164 and L171 when any of its six
prefixed cards fails to match — the six being `DBHOST=`, `DBUSER=`, `DBPASSWD=`, `DBNAME=`,
`DBPORT=` and `DBSOCKET=`. The shipped template's *values* are credential-shaped and are deliberately
not reproduced anywhere in this document or in the repository; only the card prefixes are named. The
harness supplies its own values from an environment file that is excluded from version control.

**13.13 — the build regenerates the frozen bridge sources, so it must never run in the checkout.**
`[common/comp-common.sh:L25]` is `for i in $(ls *MT.scb); do presql2 $i; ...`, which rewrites every
`common/*MT.cbl` from its `.scb`. Those generated programs are the artifacts AAP §0.8.2 designates
authoritative, and §4 above freezes them. Running the maintainer's build inside a writable copy of
the checkout would therefore overwrite the migration's own specification. The harness builds in a
separate volume with the checkout mounted read-only, which is a workaround for a frozen-script
defect and not a preference.

---

## 14. Precision obligations

This document's entire value is accuracy. Each of the following is a place where the obvious phrasing
would be **wrong**, so the correct phrasing is set out explicitly and the reasoning kept with it.

### 14.1 The divide direction in A-10 is lexical, not arithmetical

`divide X into Y giving Z` and `divide Y by X giving Z` compute the **same quotient**.
`[sales/sl060.cbl:L827]` uses the first form and `[sales/sl100.cbl:L511]` the second, and they differ
**lexically, not arithmetically**. Describing A-10 as an inverted divide would be a false statement
about the arithmetic and would send an implementer looking for a sign or reciprocal error that is not
there.

The genuine divergences in A-10 are the **guard shape** and the **counter increment**, as tabulated
in the entry.

Supporting census, over the twelve in-scope programs, counting live statements only: there are
exactly **17 `DIVIDE`** statements — **13** of the `BY … GIVING` form and **4** of the
`INTO … GIVING` form. The four `INTO` sites are `[sales/sl060.cbl:L827]`,
`[sales/sl060.cbl:L843]`, `[purchase/pl060.cbl:L751]` and `[purchase/pl060.cbl:L766]` — that is, both
moving-average sections of `sl060` and both of `pl060`, and nothing else. The 13 `BY` sites are
`[general/gl051.cbl:L604]`, `L607`, `L1035`, `L1037`, `L1044`; `[general/gl072.cbl:L386]` and `L413`;
`[general/gl080.cbl:L328]`; `[sales/sl100.cbl:L511]`; `[purchase/pl100.cbl:L502]`; and
`[irs/irs030.cbl:L1074]`, `L1077`, `L1333`.

### 14.2 A-15 and its two siblings are not of equal standing

There are **three** distinct declared-length findings in the frozen copybooks — one in
`copybooks/wsbatch.cob`, and two different readings of the same pair of lines in
`copybooks/wspost.cob` — and they are **not of equal standing**. Treating them alike would either
overstate the open questions or understate them, and **overclaiming uncertainty is as damaging as
fabricating certainty**.

**A-15 proper — unexplained in the source, and MEASURED against the compiler.**
`[copybooks/wsbatch.cob:L7-L9]`: two lengths, one contradiction, and two of the maintainer's own
question marks. Nothing in the file explains the delta, which is why it was carried as `Q-4` in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md) rather than argued out on the page. `Q-4` is
now **`RESOLVED BY ORACLE`** (2026-08-07) and the answer is **neither** reading taken as a contest:
both record copies measure **96**, `FUNCTION LENGTH` agrees with the field sum, and the 98 in the
maintainer's note is **false** under GnuCOBOL 3.2.0 — which is why this register carries A-15 as
`REPRODUCED — VALUE MEASURED`. Measuring it did not repair it and must not: the contradictory
comments stay in the frozen copybook (R-4).

**Sibling 1 — explained, but not resolved.** `[copybooks/wspost.cob:L6-L7]` records *"98 bytes
26/03/09"* and then *"96 bytes 20/12/11 (leading sign removed)"*. Unlike A-15's pair, this one
supplies a **cause** for the delta. What it does **not** supply is a settled byte width, and the
difference matters enough to spell out — because the obvious inference here is wrong, in a specific
direction.

Read as a byte account, dropping the clause from **two** fields saved **two** bytes, so the leading
sign occupied **one byte of its own**: width equals **digits + 1**, not digits. Writing "the same byte
count as its digits" would be the opposite of what the note evidences, and would silently pick a side
in an open question. The sibling test states the disagreement in three readings and this register
adopts its framing rather than adjudicating it:

- **Reading A**, from `[copybooks/wspost.cob:L6-L7]` as above — width is **digits + 1**, so 10 bytes
  for `pic s9(7)v99 sign leading`.
- **Reading B**, the ISO overpunch reading — `SIGN LEADING` written without `SEPARATE` overpunches
  the leading digit and costs no byte, so width is **digits**, 9 bytes. This is what
  `acas_posting/cobol/usage.py` implements, at the lines that name the question.
- **Reading C**, which is why Reading A is genuinely puzzling rather than obviously right: in the
  **same copybook** the *trailing* sign is provably overpunched. The maintainer's own running offsets
  advance by exactly ten bytes across each ten-digit money field — 36 to 46 over `Post-Amount`,
  `[copybooks/wspost.cob:L22-L23]`, and 86 to 96 over `Vat-Amount`,
  `[copybooks/wspost.cob:L27-L28]`. An included sign costs nothing there, twice, which makes the
  one-byte-per-field history of the *leading* case a real question rather than a typo.

`tests/arithmetic/test_sign_leading_display.py` held the question open with a strict expected failure until
the width was measured. It has since been measured — `function length` of a `pic s9(7)v99 sign is leading`
item is **9**, the same as its digit count, and the sign is overpunched onto the leading digit as `0x70` for
negative and `0x30` for positive — so that file now asserts the width and the overpunch bytes as facts.
Sibling 1 is consequently **explained AND resolved**: the maintainer named the cause and question
**`Q-5.2`**, which owns the width, carries the measurement.

The two fields are `Post-Amount` at `[copybooks/wspost.cob:L23]` and `Vat-Amount` at
`[copybooks/wspost.cob:L28]`, whose `sign leading` forms survive in the IRS variants at
`[copybooks/wspost-irs.cob:L21]`, `[copybooks/wspost-irs.cob:L25]`,
`[copybooks/irswspost.cob:L14]` and `[copybooks/irswspost.cob:L18]`.

**Sibling 2 — arithmetically RESOLVED, and presented as resolved.** Also in
`copybooks/wspost.cob`. Summing the declared pictures **excluding** `WS-Post-rrn` gives **exactly
98**, matching the L6 note:

| Field | Locator | Bytes | Running total | Maintainer's inline comment |
| --- | --- | --- | --- | --- |
| `Batch pic 9(5)` | `[copybooks/wspost.cob:L15]` | 5 | 5 | — |
| `Post-Number pic 9(5)` | `[copybooks/wspost.cob:L16]` | 5 | 10 | — |
| `Post-Code pic xx` | `[copybooks/wspost.cob:L17]` | 2 | 12 | 12 — agrees |
| `Post-Date pic x(8)` | `[copybooks/wspost.cob:L18]` | 8 | 20 | 20 — agrees |
| `Post-DR pic 9(6)` | `[copybooks/wspost.cob:L19]` | 6 | 26 | 26 — agrees |
| `DR-PC pic 99` | `[copybooks/wspost.cob:L20]` | 2 | 28 | — |
| `Post-CR pic 9(6)` | `[copybooks/wspost.cob:L21]` | 6 | 34 | 34 — agrees |
| `CR-PC pic 99` | `[copybooks/wspost.cob:L22]` | 2 | 36 | 36 — agrees |
| `Post-Amount pic s9(8)v99` | `[copybooks/wspost.cob:L23]` | 10 | 46 | 46 — agrees |
| `Post-Legend pic x(32)` | `[copybooks/wspost.cob:L24]` | 32 | 78 | 76 — **2 low** |
| `Vat-AC pic 9(6)` | `[copybooks/wspost.cob:L25]` | 6 | 84 | 82 — 2 low |
| `Vat-PC pic 99` | `[copybooks/wspost.cob:L26]` | 2 | 86 | — |
| `Post-Vat-Side pic xx` | `[copybooks/wspost.cob:L27]` | 2 | 88 | 86 — 2 low |
| `Vat-Amount pic s9(8)v99` | `[copybooks/wspost.cob:L28]` | 10 | 98 | 96 — 2 low |

The inline comments agree exactly through `Post-Amount` and then run **exactly 2 bytes low** for
every field from `Post-Legend` onward, ending at 96 and matching the L7 note. **The divergence
localises precisely at `Post-Legend`: the comments imply 30 bytes where `x(32)` is declared.** That
is a complete account, so this sibling is **resolved** and is not carried as an open question. It is
worth stating explicitly because the two notes at L6-L7 look, at a glance, exactly like A-15's
unexplained pair.

Note that this account does **not** depend on `Q-5.2`. Neither money field carries a `sign leading`
clause in the current declaration, and the ten bytes assigned to each of them above is corroborated
by the maintainer's own comment deltas — Reading C in Sibling 1: 36 to 46, and 86 to 96. Sibling 2 is
therefore resolvable while Sibling 1 stays open, which is exactly why the two must be presented
separately rather than merged.

### 14.3 Harmless versus fatal missing periods

Missing terminating periods appear in the frozen source in both harmless and fatal forms, and the
contrast is what stops a future reader "fixing" either one. Listing them without the contrast would
make A-1 look arbitrary.

**Harmless.** `[common/glpostingMT.cbl:L1060]` — `move CR-PC to HV-CR-PC` — omits its terminating
period where every sibling `move` in the same load paragraph has one. The paragraph is a
straight-line sequence of unconditional statements, so L1060 and `[common/glpostingMT.cbl:L1061]`
simply form one sentence and both moves execute in order. The behaviour is identical to the
period-bearing form. It is recorded, not repaired.

**Fatal.** `[sales/sl060.cbl:L1176]` omits its period **fatally**, because the statement that follows
is an `if`. The missing period changes conditional nesting, and a whole close is lost in one
configuration. This is **A-1**.

**Fatal, second form.** `[sales/sl060.cbl:L841-L843]` is a single sentence whose leading `if` governs
two statements, where the sibling section's equivalent statements are two unguarded sentences. This
is **A-9**, and it is the same class as A-1 acting on a guard rather than on a close.

The rule the contrast yields, and the reason all three are in this register: a missing period is
harmless **only** where the next statement is unconditional. Where the next statement is a
conditional, or where the statement itself is inside a conditional, the period is load-bearing and
its absence changes control flow.

### 14.4 Out-of-scope names are given as counts only

The frozen schema and the bridge set both contain material this migration does not touch, and naming
it risks presenting an out-of-scope table or bridge as though it were migrated. Counts only,
therefore, and they reconcile exactly:

- **22** in-scope tables plus **11** out-of-scope tables equals the **33** `CREATE TABLE` statements
  in `mysql/ACASDB.sql`.
- **20** in-scope bridge pairs plus **8** out-of-scope bridge pairs equals the **28** `common/*MT.scb`
  sources in the checkout.

Both figures are also recorded machine-readably in the generated dictionary's `coverage` block —
`schema_tables_total` 33, `in_scope_tables` 22, `out_of_scope_tables` 11, `in_scope_bridges` 20,
`out_of_scope_bridges` 8 — so the arithmetic can be checked without reading this file. No
out-of-scope table or bridge is named anywhere in this document.

### 14.5 The schema contains no DDL evolution, and the raw text does not say so

For completeness, because a naive grep of the frozen schema is misleading: `mysql/ACASDB.sql` contains
**zero** `CREATE INDEX` statements and **zero** schema-altering statements, but the string
`ALTER TABLE` does occur 66 times. Every one of those occurrences is a MySQL version-guarded dump
wrapper of the form `/*!40000 ALTER TABLE ... DISABLE KEYS */` or its `ENABLE KEYS` partner, paired
one-to-one around each table's data section. They alter nothing about the schema. Recording this
prevents the opposite error to the one §14.4 guards against — reading a dump artefact as evidence
that the schema does evolve.

---

## 15. Candidates beyond the canonical register

⚠️ **This section is separate from §10 on purpose.** These are **candidates discovered during
planning and implementation, additional to the AAP §0.6.7 register of twenty-two.** They are not
canonical entries, they do not renumber anything, and they use their own `A-NEW-<n>` identifiers —
several of which are already cited by the reproducing modules, so the numbering here is fixed by the
same argument as §5. All were verified by direct reading of the frozen source.

**A-NEW-1 — dead code after an unconditional transfer.** In `pl060`'s end-of-loop paragraph the
`perform OTM5-Start` at `[purchase/pl060.cbl:L819]` is followed by an **unconditional** `go to
main-end.` at `[purchase/pl060.cbl:L820]`, which makes the `go to read-loop.` at
`[purchase/pl060.cbl:L821]` unreachable. The second pass over the open-item file that L821 was
evidently meant to start therefore never happens. The span is
`[purchase/pl060.cbl:L809-L823]`. Already named `A-NEW-1` by
`acas_posting/programs/pl060_order_posting.py` — and this is the **one** number on which that module
and this register agree about the defect as well as the digit, which is why it is the one candidate
number §15.1 does not reassign. It is additionally locked by
`tests/scenarios/test_clean_batch_post_pl.py::test_a_new_1_second_apportionment_pass_never_runs`. The end state the dead second pass would have left is
carried as `Q-CR-NOTES-SECOND-PASS`.

**A-NEW-2 — a second, independent contradiction in the `maps04` remarks block.**
`[common/maps04.cbl:L160-L162]` documents the module as returning a date in `ccYYMMDD` form in its
output field, yet `[common/maps04.cbl:L167]` stores `FUNCTION integer-of-Date`, which is a **day
number**. Together with **A-16**, whose contradiction sits three lines further down in the same block
at `[common/maps04.cbl:L163]`, this makes the block unreliable in two distinct ways rather than
merely imprecise — which is why the date contract is arbitrated against the compiled program instead
of read off the comments. Strengthens the date-contract question in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md).

**A-NEW-3 — a handler left open, and a comment asserting the opposite.** `irs030`'s posting section
never closes `acasirsub1`, the IRS nominal-ledger handler, when it returns. The commented-out close
at `[irs/irs030.cbl:L1710]` carries the maintainer's `*> Closed at EOJ` assertion, which is not what
happens. ⚠️ The live closes are **two, not three** — `[irs/irs030.cbl:L1711]` for `acasirsub4` and
`[irs/irs030.cbl:L1712]` for `acas008` — correcting the received brief.

**A-NEW-4 — VAT silently discarded for any account-and-side pair outside the four handled.**
`[irs/irs030.cbl:L1682-L1699]` accumulates a posting's VAT into one of two control-account snapshots
by a four-deep `if`/`else` chain, keyed on the **pair** of the VAT account definition and the posting's
VAT side: 31 with CR at L1687, 31 with DR at L1691, 32 with CR at L1695, 32 with DR at L1699. There is
**no final `else` and no diagnostic**, and control then falls to `go to Input-Loop.` at
`[irs/irs030.cbl:L1700]`. Any other pair — an account code outside `{31, 32}`, or one of those two
codes with a side that is neither `DR` nor `CR` — loses its VAT with no trace. The zero gate that
precedes the chain is `[irs/irs030.cbl:L1682-L1683]`.

⚠️ The condition must be stated as the **pair**, not as the account code alone: account 31 with an
unexpected side falls through just as an unknown account does, and describing the gap as "an unknown
VAT account" would miss half of it.

**A-NEW-5 — Purchase has no abort gate at all.** This is the sharpest R-4 obligation in the menu
layer, because the three sub systems diverge three ways on the same guard:

| Sub system | Locator | Gate | Predicate |
| --- | --- | --- | --- |
| General | `[general/general.cbl:L805-L815]` | once, at L810-L811 | `ws-term-code = 5` |
| Sales | `[sales/sales.cbl:L756-L768]` | **twice**, at L761-L762 and L765-L766 | `ws-term-code not = zero` |
| Purchase | `[purchase/purchase.cbl:L752-L762]` | **none** | — |

In Purchase, both the autogen call and the term-code gate are **entirely commented out** at
`[purchase/purchase.cbl:L755-L758]`, so `pl055` runs at L759-L760 and `pl060` at L761-L762 with
nothing between them. ⭐ Even the dead code diverges: the commented-out Purchase line at
`[purchase/purchase.cbl:L756]` reads `perform load000` where the live Sales line at
`[sales/sales.cbl:L760]` reads `perform load00`. The migration's Purchase entry point therefore has
**no** gate, its Sales entry point has **two**, and its General entry point has **one** with a
different predicate — three shapes, preserved as three.

⚠️ **Reproducing module:** the three shapes live in the three CLI entry points —
`acas_posting/cli/pl_order_post.py` has no gate, `acas_posting/cli/sl_invoice_post.py` has two and
`acas_posting/cli/gl_post_cycle.py` has one with the `= 5` predicate. An earlier revision of this entry
claimed it was "already named `A-NEW-5` by `acas_posting/programs/pl100_payment_posting.py`". **That was
false.** That module's local `A-NEW-5` was a different defect entirely — a mutually exclusive `IF/ELSE`
in its `bl-open` — and it now carries the globally unique name `A-PL100-A`. See §15.1.

**A-NEW-6 — the `gl080` divide-by-zero is reachable.** The guard that protects the cycle-to-period
divide is `[general/gl080.cbl:L324-L326]` — `if a = 9 or scycle < period go to main-end.` The second
disjunct, `scycle < period`, is **false** for any non-negative `scycle` when `period` is zero, so
control reaches the divide at `[general/gl080.cbl:L328]` with a zero divisor. The guard reads as
though it protects the divide and does not. Cross-referenced to the division-by-zero question in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md); the resulting behaviour is a property of the
compiled program and is not guessed here.

⚠️ **Reproducing module:** `acas_posting/programs/gl080_end_of_cycle.py`, which leaves the guard exactly
as written. An earlier revision claimed this was "already named `A-NEW-6` by
`acas_posting/programs/pl100_payment_posting.py`". **That was false** — that module's local `A-NEW-6`
was "no supplier is ever created", and it now carries the globally unique name `A-PL100-B`. See §15.1.

**A-NEW-7 — a comment naming a field that does not exist.** `[copybooks/wspost.cob:L10]` records
*"Added WS-P-rrn to replace relative processing"*, but the field declared at
`[copybooks/wspost.cob:L13]` is `WS-Post-rrn`. The maintainer's own change note cites a name that
appears nowhere in the copybook. Same class as **A-22** — a name that misdirects a reader navigating
by name — and, like A-22, preserved.

⚠️ `acas_posting/records/gl_posting.py` carries the note at the field it belongs to. An earlier revision
claimed this was "already named `A-NEW-7` by `acas_posting/programs/pl100_payment_posting.py`"; **that
was false** — that module's local `A-NEW-7` was the deduction reversal gated on `t-deduct` alone, and it
now carries the globally unique name `A-PL100-C`. See §15.1.

**A-NEW-8 — `acas007` and `acas008` disagree about whether `Open-Output` truncates.** The two
handlers carry the same special-case block, and one of them has two of its lines commented out:

- `[common/acas007.cbl:L305-L312]` has the same shape as its sibling, **but `set fn-delete-all to
  true` at L308 and `move zero to access-type` at L309 are commented out**. Opening the General
  Ledger batch table for output therefore does **not** truncate `GLBATCH-REC`.
- `[common/acas008.cbl:L313-L319]` **does** substitute a delete-all and therefore **does** truncate
  the transfer table — and only in RDB mode, the extra condition at `[common/acas008.cbl:L315]` being
  `and not FS-Cobol-Files-Used`.

There is additionally a **second, unguarded** delete-all substitution in the same handler at
`[common/acas008.cbl:L571-L574]`, which sets the flag on any open-output regardless of mode. Both
handlers are preserved exactly, and **never harmonised** — the asymmetry is what decides whether an
`Open-Output` in a scenario empties a table or leaves it alone, which is directly diff-visible.

**A-NEW-9 — a five-source `STRING` the maintainer flagged as wrong.**
`[general/gl080.cbl:L530]` carries `move space to Arg-Test.` with the inline comment `*> this lot
looks wrong !!!!!`, introducing a `STRING` statement at `[general/gl080.cbl:L531-L536]` that
concatenates five sources into `Arg-Test` and is then moved into the shorter `file-2` at
`[general/gl080.cbl:L537]`. The truncation on that final move is the maintainer's concern. It sits in
the archive-path construction, which produces no database effect, so it is recorded rather than
locked.

**A-NEW-10 — a wrong-program comment in all four Sales and Purchase posting programs.**
`[sales/sl060.cbl:L1172]` reads `if IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060` — inside
`sl060`, which is Sales. The identical comment appears at `[purchase/pl060.cbl:L1027]`,
`[sales/sl100.cbl:L690]` and `[purchase/pl100.cbl:L671]`, and is accurate in **exactly one** of the
four.

This is documentation-grade corroboration for **A-1**, not merely a curiosity. The comment is a
copy-paste artefact, it sits on the line immediately before **A-17**'s unexplained move and three
lines before **A-1**'s missing period, and it is plausibly the very mechanism by which that period was
lost: the block was copied between programs and one character did not survive the copy. It is
recorded because it makes A-1 comprehensible rather than arbitrary — which §14.3 requires — and it is
preserved because it is a comment in a frozen file.

**A-NEW-11 — live state read before it is written.** `[general/gl080.cbl:L182-L183]` declare
`77 y pic 99 value zero.` and `77 a pic 99 value zero.` The subscript `a` is **read** at
`[general/gl080.cbl:L324]` — `if a = 9` — before it is **written** at `[general/gl080.cbl:L328]`. The
`value zero` clause initialises it once at program load, so on a second entry to the section within
the same run it carries the previous value rather than zero. The test at L324 is therefore reading
state the unit never initialises for itself. Left exactly as it is.

**A-NEW-12 — a transposed name, and a condition name declared but never tested.**
`[general/gl051.cbl:L175]` declares `03 trutht pic 9.`, a transposition of "truth", carrying
`88 falset value zero.` at `[general/gl051.cbl:L176]` and `88 truet value 1.` at
`[general/gl051.cbl:L177]`. **`falset` is declared and never tested anywhere in the program** — its
declaration is its only occurrence — while `truet` is tested twice, at `[general/gl051.cbl:L507]` and
at `[general/gl051.cbl:L1101]`, the latter being the `if not truet` inside the control-total gate that
is in scope for this migration. The negative condition name is therefore dead, and the program
expresses its negative case as `not` of the positive one.

**A-NEW-13 — a comment-only copybook absent from the frozen archive.**
`copybooks/ACAS-SQLstate-error-list.cob` is absent from the checkout yet is
named by a `COPY` statement in 44 frozen files, most of them `common/*MT.cbl`
bridges. The initial consequence was direct: 22 of 28 required `*MT` bridge
builds failed.

**Compiled resolution, observed 2026-08-04.** The include is semantically
inert. `harness/build_oracle.sh` now materialises a comment-only compatibility
file at `$ACAS_BUILD/copybooks/ACAS-SQLstate-error-list.cob` and adds that
writable build directory to the compiler's copy path. It does not create or
edit anything under frozen `copybooks/`. A strict rebuild completed with zero
fatal diagnostics and produced all 29 expected `*MT` bridge artifacts and all
28 loader programs.

**Durable evidence, in the repository rather than in a session log.** The shim itself is committed at
`harness/copybook-shims/ACAS-SQLstate-error-list.cob` and is comments only, so a reader can confirm by
inspection that no data item or statement was supplied;
`[harness/build_oracle.sh acas_install_sqlstate_comment_shim]` is the copy that places it in the
disposable build tree, and `[harness/build_oracle.sh acas_explain_missing_sqlstate_copybook]` is where
the script detects the absence and explains it. The build result — 29/29 bridges, 28/28 loaders, all
twelve in-scope programs and all seventeen handlers — is recorded in
[`scenario-diff-evidence.md`](scenario-diff-evidence.md) §3, alongside the manifest digests of the runs
that build produced.

**And stated as how to regenerate it**, because a committed digest and a reproducible command are the
two durable forms of the same claim. `harness/build_oracle.sh` prints the bridge and loader tallies as
it goes and writes its two compile transcripts under `$ACAS_LOG_DIR` — `$ACAS_OUT/build`, which it names
on its own last lines — so the counts above come back from:

```bash
# CLONE_INDEX and the credential variables, per README-python-migration.md section 8.1.
# They have no committed defaults: Compose refuses to render if any is unset.
export CLONE_INDEX=001
docker compose -f harness/docker-compose.yml run --rm -T gnucobol \
    /repo/harness/build_oracle.sh < /dev/null
```

⚠️ The console log of the remediation build itself was captured to a session-scoped file under `/tmp`,
which does **not** survive the session, and it is deliberately not cited here as though a reader could
open it: a citation a reader cannot open is not evidence. The committed shim, the §3 digests, and the
command above with the transcripts it leaves in the named volume are the citation, because those are
the artifacts that persist.

The resolution is intentionally narrower than “invent the missing copybook”:
only comments are supplied, only in the disposable build tree, and the
compiler proves that no data item or executable statement was missing. This
candidate at the time of that note remained `A-NEW-13` so that `A-NEW-1` through `A-NEW-12`, already
cited by reproducing modules, keep their numbers.

**A-NEW-14 — `GLPOSTING-REC` non-fetch writes collapse onto one primary
key.** `[common/glpostingMT.cbl:L1053-L1066]` initialises the host-variable
record and loads thirteen fields, but does not load `HV-POST-RRN`. The SQL
builder nevertheless uses that field as the relational primary key. Compiled
loader measurement confirmed the consequence: every non-fetch write targets
the same key, so a seed can persist at most one posting row. That row's key is
zero and is then skipped by `[general/gl070.cbl:L490-L493]`.

This is the measured value half of `Q-9` in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md). It forced the
`mixed_accepted_rejected` and `clean_batch_gl` scenarios to be re-derived from
reachable store state. Both now declare `expected_table_effect: unchanged`
and both produce an observed empty diff. The bridge and schema are frozen;
the migration reproduces the collapse rather than allocating a replacement
key.

**A-NEW-15 — the menu's flat mirror persists RDB mode as zero for the next
process.** Each menu's `overrewrite` first saves the declared RDB mode, then
sets the flat selector before rewriting the COBOL system file. In the frozen
source that flat rewrite stores `File-System-Used = 0` into `system.dat`
record 1. The next menu process begins by forcing the flat leg and reading that
record, so it silently runs its entire accounting operation against indexed
files even though MariaDB still holds `FILE-SYSTEM-USED = 1`.

This was observed directly in the four-operation `period_end_totals` journey:
operation one changed MariaDB; operations two through four displayed success
but issued no accounting DML. The build wrapper now inserts a build-copy-only
move of the saved mode immediately before the flat `System-Rewrite` in
General, Sales, and Purchase. After the shim, the isolated Sales measurement
changed `SL-PAYMENTS` from `8888.88` to `9691.23` and cleared `S-FLAG-P`,
then the full journey passed 18/18 tests and an empty parity diff. No frozen
menu source was edited.

**A-NEW-16 — one process-global MySQL handle makes local CLOSE calls destroy
unrelated IRS facades.** The vendored `cobmysqlapi38.c` owns one file-scope
`MYSQL sql, *mysql=&sql;`. `acasirsub3` and the `irs030` end-of-job path issue
local closes as though each facade owned a separate connection. Compiled
measurement showed that a preceding default-record read therefore made the
later `acasirsub1` indexed read report a false key-not-found, and the end-of-job
closes could kill the transfer delete-all.

The Python DAL now scopes process-owned connections explicitly, and the oracle
build copy suppresses only the destructive local closes. The `irs030`
reproduction, including the preceding `acasirsub3` read, is runtime verified by driving the IRS
scenario end to end — `harness/run_parity.sh harness/scenarios/clean_batch_irs.yaml`, whose retained
`verdict.json` records `identical` over the four IRS tables and whose
`<ACAS_OUT>/run-logs/clean_batch_irs/cobol.log` carries the facade call sequence — and by
`tests/scenarios/test_clean_batch_post_irs.py`, which asserts the reproduction against the compared
state. ⚠️ An earlier revision cited a session-scoped `/tmp` log that does not outlive its session; the
retained artifacts, the scenario and the test are cited instead because all three persist and all
three re-run on demand. The frozen ownership defect is
preserved as the specification; the shims make the compiled comparison
executable without pretending the API supplies per-facade handles.

**Evidential status, stated exactly.** The false key-not-found and the killed delete-all were
**observed** during the remediation session, but the only record of that observation was a console log
in a temporary directory and it has not survived — so the measurement is carried here as an
**unverified report** rather than as a finding, and nothing in the migration depends on it being taken
on trust. What *is* durable, and what a reader can check now: the shim's effect is visible in
`harness/build_oracle.sh`, the reproduction is exercised on every run of
`tests/scenarios/test_clean_batch_post_irs.py` — whose `clean_batch_irs` journey drives `acasirsub3`
before `acasirsub1` precisely so the handle sharing is on the path — and that journey's observed empty
diff, with its manifest digests, is recorded in
[`scenario-diff-evidence.md`](scenario-diff-evidence.md) §10.4.

**A-NEW-17 — Purchase linkage reinterprets storage instead of converting the
numeric value.** `acas022` passes `binary-char` and `binary-long` storage by
reference, while `purchMT` receives it as `PIC 99 COMP` and
`PIC 9(8) COMP` `[common/purchMT.cbl:L344-L355]`. Compiled probes measured
the byte reinterpretation directly. For example, caller `112233` becomes a
bridge value outside the frozen `mediumint(6) unsigned` sort-code range, and
the loader reports the database range error while returning zero.

The scenarios do not correct that linkage. `clean_batch_pl` and
`period_end_totals` pin `Purch-SortCode` to `"0"`, the reachable value that
survives the frozen boundary. The full Purchase and period-total journeys then
produce observed empty diffs. The measured conversion table and its consumers
are recorded in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md).

**A-NEW-18, working alias `N-KEY` — the `POST-KEY` group move corrupts the key on
the way back out of the bridge, and the General Ledger posting cycle therefore
cannot post a seeded posting row at all.** Not "does not, here" — **cannot**, for a
frozen-code reason, on either side. This entry is promoted from a derivation that
previously lived only inside two scenario definitions and one test section; it is
recorded here because it is a defect of the frozen system, it governs what four
scenarios can observe, and a defect that is only derived in passing is a defect
nobody can cite. **The alias `N-KEY` is retained** because
`harness/scenarios/mixed_accepted_rejected.yaml`,
`harness/scenarios/end_of_cycle_gl.yaml`,
`tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py`,
`tests/scenarios/test_mixed_accepted_rejected_batch.py` and
`acas_posting/dal/acas006_gl_posting.py` already cite that name, and §5's rule is
that identifiers are never renumbered.

**The chain, each link measured on GnuCOBOL 3.2 against MariaDB 10.11.7:**

1. `WS-Post-Key` is a **group** of two `pic 9(5)` items
   `[copybooks/wspost.cob:L14-L16]`, while `HV-POST-KEY` is `PIC 9(18) COMP`
   `[common/glpostingMT.cbl:L283]`. Because the sending operand is a group,
   `move WS-Post-Key to HV-POST-KEY` `[common/glpostingMT.cbl:L1054]` is a **byte
   move, not a numeric conversion**. Proved on the oracle by moving the
   non-numeric group `"ABCDE00001"` into it without a diagnostic.
2. Batch `00001` with Post-Number `00001` gives the ten bytes `"0000100001"`. The
   first **eight**, `"00001000"`, read as a big-endian integer are
   `3472328296244457520` — **nineteen** digits, which the eighteen-digit picture
   truncates to `472328296244457520`. That is exactly what the column holds,
   measured by `SELECT` after a compiled seed.
3. Reading back, SQL sets `HV-POST-KEY` **numerically**, so its eight bytes are now
   `0x06 0x8E 0x0C 0x15 0x3B 0x04 0x30 0x30`. The leading `3` was truncated away in
   step 2 and **cannot be recovered**. `move HV-POST-KEY to WS-Post-Key`
   `[common/glpostingMT.cbl:L1085]` copies those bytes straight back, so `Batch`
   now holds five control characters and `IF Batch IS NUMERIC` is **false**.
   Measured directly on the oracle compiler; `Batch` compares as **75261**.
4. `gl070`'s own guard therefore fires — `if batch not = WS-Batch-Nos go to loop`
   `[general/gl070.cbl:L492-L493]` — and **no work record is written**. Measured:
   `pretrans.tmp` and `postrans.tmp` are both **zero bytes** after the run.
5. `gl072` opens post-trans, reads, and takes `AT END` on the **first** read
   `[general/gl072.cbl:L286-L289]`, so it performs `end-account` and `end-batch`
   against a working-storage batch record that was never populated. Both rewrites
   address a key no row has, so neither changes anything. Measured: every
   `GLBATCH-REC`, `GLLEDGER-REC` and `GLPOSTING-REC` row is byte-identical to the
   seed.

**One frozen defect with three faces, which is why it is one entry and not three.**
First, it starves `gl070` → `gl071` → `gl072`: the cycle runs to completion, exits
zero, and posts nothing. Second, it is why **`gl080`'s deletion phase deletes
nothing**, measured independently by the `end_of_cycle_gl` scenario. Third, it makes
**A-13's two silent skips unreachable by any seed** — the non-numeric value genuinely
exists, but `gl070` discards the row one layer above, before `gl072` can ever see it.
That third face corrected an earlier claim in this project's own records which named
the right corruption and the wrong program.

**Reproduced, not repaired (R-4).** `acas_posting/dal/acas006_gl_posting.py`
reproduces the round trip, including `_split_post_key`, which was added after
measurement established that the compiled unload is a **raw byte copy** rather than
the arithmetic `int(hv_post_key) % 10**10` the module first used. **Locked** by
`tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` §19, which derives
why no seed reaches either skip, and §22, which pins the byte-level round trip.
The consequence — that no batch is stamped — is asserted against the declared seed
by `tests/scenarios/test_mixed_accepted_rejected_batch.py`.

⚠️ **What this entry does not claim.** It does not claim the migration is unable to
post; it claims the *frozen system* cannot post a **seeded** posting row, because a
seeded row's key makes the round trip that corrupts it. A posting row created within
a run does not travel that path. The distinction matters because an empty diff over
these scenarios proves the two implementations reach the same **absence** by the same
route — it does not prove that anything posted, and the scenario files say so
themselves.

---

### 15.1 The six program-scoped candidates, and the old-to-new identifier map

⚠️ **A candidate number used to mean two different defects depending on which file you were reading,
and that is now fixed.** Two program modules had each opened a candidate register of their own and
numbered it `A-NEW-<n>` from 1, at the same time as this register was numbering its own candidates from
1. There was no shared allocation point, so six numbers collided: `A-NEW-2`, `A-NEW-3` and `A-NEW-4`
meant one thing here and another in `pl060_order_posting.py`; `A-NEW-5`, `A-NEW-6` and `A-NEW-7` meant
one thing here and another in `pl100_payment_posting.py`. `A-NEW-1` was the single exception — both
sides had independently given that number to the *same* defect.

**How it is resolved: globally unique names, allocated to the module-local readings.** This register
keeps its numbers, because they are cited by the scenario definitions, the scenario tests and the
sibling documents, and moving a cited number to tidy a table breaks a suite silently — the failure mode
§5 exists to prevent. The six module-local candidates instead take names that cannot collide with
anything, formed from the program that owns them. That is the pattern this register already recommends
and that `acas_posting/dal/acasirsub4_irs_posting.py` adopted by choosing letters. **The six are
registered here, so none of them is "UNREGISTERED" any longer.**

| New identifier | Old, file-local identifier | Owning module | Locators | The defect |
| --- | --- | --- | --- | --- |
| **`A-PL060-A`** | `A-NEW-2` in `pl060_order_posting.py` only | `acas_posting/programs/pl060_order_posting.py`, `_init01__end_loop_end` | `[purchase/pl060.cbl:L630-L635]` | The `write` sits in the `else` arm only, so `PL133` is moved into `print-record` and never written in `FS-Cobol-Files-Used` mode. Mirrors `[sales/sl060.cbl:L702-L707]`. |
| **`A-PL060-B`** | `A-NEW-3` in `pl060_order_posting.py` only | same module, `_init01__loop` | `[purchase/pl060.cbl:L450]`, `[purchase/pl060.cbl:L467-L468]` | `a` is set from `oi-type` with no range check and then subscripts `total-group occurs 3`. Same class as **A-2**. |
| **`A-PL060-C`** | `A-NEW-4` in `pl060_order_posting.py` only | same module, `_add_to_pturnover_q` | `[purchase/pl060.cbl:L484]`, `[purchase/pl060.cbl:L490]`, `[purchase/pl060.cbl:L497]` | `current-quarter` subscripts `pturnover-q occurs 4` unchecked, exactly as `[general/gl080.cbl:L345]` does for **A-2**. |
| **`A-PL100-A`** | `A-NEW-5` in `pl100_payment_posting.py` only | `acas_posting/programs/pl100_payment_posting.py`, `_bl_open` | `[purchase/pl100.cbl:L566-L570]` | A mutually exclusive `IF … ELSE` where every sibling uses two independent `IF`s, `irs-used` tested without `IRS-Both-Used`, and no open-output fallback — so the program writes to unopened tables in **both** IRS modes. Control: `[purchase/pl060.cbl:L907-L920]`. |
| **`A-PL100-B`** | `A-NEW-6` in `pl100_payment_posting.py` only | same module, `_init01__cust_update` | `[purchase/pl100.cbl:L356-L361]`, `[purchase/pl100.cbl:L405]` | No supplier is ever created — the program contains no `Purch-Write` at all — yet `Purch-Rewrite` is issued unconditionally. |
| **`A-PL100-C`** | `A-NEW-7` in `pl100_payment_posting.py` only | same module, `_init01__main_end` | `[purchase/pl100.cbl:L449]` | The whole deduction reversal is gated on `t-deduct` alone, so `n-deduct` can drift permanently. |

**The compatibility map, in one line per rename, so that no existing reference dangles:**

```text
pl060_order_posting.py    A-NEW-2 -> A-PL060-A    A-NEW-3 -> A-PL060-B    A-NEW-4 -> A-PL060-C
pl100_payment_posting.py  A-NEW-5 -> A-PL100-A    A-NEW-6 -> A-PL100-B    A-NEW-7 -> A-PL100-C
pl060_order_posting.py    A-NEW-1 -> A-NEW-1      (unchanged: same defect as this register's A-NEW-1)
```

**What was updated with them.** Every occurrence in the two owning modules, and the one *external* file
that had cited a module-local meaning: `harness/scenarios/period_end_totals.yaml`, whose four
references to `A-NEW-5` meant `[purchase/pl100.cbl:L566-L570]` and which additionally asserted "It is
entry A-NEW-5 of docs/migration/anomaly-log.md" — a statement that was false and is now correct under
the new name. Every other external citation in `tests/`, `harness/scenarios/` and the sibling documents
was checked one identifier at a time and uses **this register's** meaning, so nothing else needed
changing and nothing dangles. Each owning module also carries the map at the head of its own anomaly
footer, so a grep for an old number lands on an explanation rather than on nothing.

**The rule from here.** Any candidate opened from now on either takes the next free number **in this
register** or uses a name that cannot collide — a program-scoped letter, as above, or a mnemonic. A bare
`A-NEW-<n>` allocated inside a single module is no longer an acceptable identifier.

---

## 16. Self-audit

Recorded so that a reviewer can confirm what was and was not established, rather than inferring it.

**What was verified.** Every `[path:locator]` citation in this document was resolved by reading the
frozen file at that line in this checkout. Every census figure — the five `ROUNDED` sites, the 17
`DIVIDE` statements split 13 to 4, the 23 and 29 `FUNCTION TRIM` sites, the 33 tables, the 28 bridge
sources, the numeric and character column censuses, the 24 malformed loader lines, the nine
`cobmysqlapi.o` link sites, the 44 `COPY` references to the missing copybook — was produced by
enumeration over the frozen files, not recalled. The `bash -n` failure on `common/masterLD.sh` was
observed. All twenty `tests/arithmetic/` files were read to build §11's map, including the
shared-storage, dispatch-boundary and cross-file-reference coverage added during QA remediation. The infrastructure-free
tier was run independently of the Compose stack. The per-field `anomaly_refs` and
`ambiguity_refs` counts quoted for A-7, A-11, A-12, A-14, A-15 and A-20 were read out of the committed
`data_dictionary/acas_posting_dictionary.json`.

**What compiled execution established.** On 2026-08-04 the strict oracle build completed with all
29 expected `*MT` bridges and 28 loaders. All eight mandated journeys then completed the ten-stage
protocol with observed empty diffs, and the scenario tier passed 93 tests in both declared and
reverse file order. On **2026-08-07**, after `end_of_cycle_gl` was added, **all nine** journeys
completed the same ten stages with observed empty diffs, and the scenario tier — **107** tests as
selected by `pytest -m scenario`, the growth being the ninth file's eleven plus the seed-relative
tests added to the eight — passed in the containerised run. The measurements added to A-13 and
A-NEW-13 through A-NEW-17 are therefore runtime findings, not source-reading predictions.
**[`scenario-diff-evidence.md`](scenario-diff-evidence.md) is the authority for which run produced
which verdict**, and it carries the manifest digests; this document deliberately does not restate
them, so that there is one place a reader has to trust and one place an edit has to change.

**What remains open, and what closed since.** Compiled execution of the mandated *scenarios* never
answered every `Q-` question, and was never going to: a scenario exercises the paths the scenario
reaches, and several of these questions live at boundaries no accounting journey visits. Those were
closed instead by **focused compiled probes** — small programs that `copy` the frozen copybooks and
ask the compiler or the database one question — which is a different instrument from a green
scenario and is labelled as such wherever it was used.

Every entry in *this* register that once read `PENDING — AWAITING ORACLE EXECUTION` has now been
measured that way: **A-11** (a narrowed sign becomes the absolute value, bounded afterwards by the
receiving digit count), **A-15** (both record copies measure 96 and the maintainer's 98 is false), and
**A-17** (the receiver is signed, does not truncate at its picture, wraps at 32767, and reaches an
unsigned column as a magnitude). Two further entries were promoted the same way without ever having
read `PENDING`, because their *shape* was never in doubt and only their stored effect was watched:
**A-2** (an out-of-record subscript stores past the record and moves no column) and **A-14** (the
compiled tie order is input order, so the sequential read is right by upstream sort and not by
lookup). All five entries remain, for the reasons §2.6 gives.

`Q-` questions that remain open are open in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md), which is where their status is authoritative;
§17 there carries the tally. No value anywhere is promoted merely because a related journey
passed — the rule that produced the honest `PENDING`s in the first place is the rule that made these
promotions worth something.

**⚠️ Two of those measurements have no durable artifact, and are labelled accordingly in place.** The
strict-build console output behind `A-NEW-13` and the handle-sharing probe behind `A-NEW-16` were
written to a temporary directory during a remediation session and have not survived, so the first cites
the committed shim and the build script instead and the second is carried as an **unverified report**.
No session log is cited anywhere in this register as though a reader could open it.

**What was corrected.** Fourteen locators from the Agent Action Plan and three claims from the
received brief did not survive verification. They are listed in §8 and, for the build scripts, in
place at §13.4, §13.5, §13.6 and §13.12. In every case the frozen file decided.

**Register integrity.** Twenty-two canonical entries, `A-1` through `A-22`, none missing and none
renumbered. **Fifteen** marked test-locked — A-1, A-2, A-3, A-4, A-5, **A-6**, A-7, A-8, A-9, A-10,
A-11, A-13, A-14, A-19, A-21 — each naming a real test from §11, and every one of those names was
verified by OPENING the test rather than by trusting the field. Three earlier attributions did not
survive that verification and were corrected: A-1 named an arithmetic test that only mentions it, A-4
named an arithmetic test that only cites it, and A-13 named one file where the two skips are in fact
locked by two separate scenario tests. §11 additionally separates a **record lock** from a behaviour
lock, because conflating them was what let the false attributions stand. ⚠️ This count read "Fourteen"
and omitted **A-6** until this revision, while A-6's own summary row already carried the dagger and §11
already counted fifteen: the register disagreed with itself in three places at once. A-6 became locked
when `tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` §20 began driving the migrated
`acas008` once per refused verb and requiring the measured `WE-Error 988` / `FS-Reply 99` pair; the
summary row and §11 were moved then and the heading dagger and this list were not. **Twenty-four
candidates** live in §15: **eighteen** as `A-NEW-1` through `A-NEW-18`, where `A-NEW-18` carries the
working alias `N-KEY` under which the scenario files, the arithmetic tier and the data-access module
already cite it, plus the **six** program-scoped ones registered in §15.1 with their old-to-new map.
Thirteen frozen-script and frozen-file defects in §13 are recorded; executable compatibility changes
live only in the writable build tree or in the migration harness.

**The freeze held.** Creating this document modified no frozen file. `common/*.cbl`, `common/*.scb`,
`copybooks/*.cob`, `general/*.cbl`, `sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl`,
`mysql/ACASDB.sql`, the compile and load scripts, `README.TXT`, `README`, `README.SVN`,
`README.nightly`, `Changelog` and `ACAS-Manuals/` are all byte-identical to the state in which they
were read.

---

## 17. Companion documents

This register is one of four migration documents and deliberately does not duplicate the others.
All four are companion deliverables of the same single execution phase, per AAP §0.4.5 and §0.4.1.7.

| Document | What it carries | Why it is not here |
| --- | --- | --- |
| [`traceability.md`](traceability.md) | program to module, paragraph to function, field to dictionary entry, with the `GO TO` class annotated at each transfer site | R-5's mapping tables; this register names a reproducing module per entry and stops there |
| [`ambiguity-resolutions.md`](ambiguity-resolutions.md) | each `Q-` question, the oracle experiment, and the resolution adopted | R-6's arbitration record; this register cross-references a `Q-` identifier rather than pre-empting its answer |
| [`scenario-diff-evidence.md`](scenario-diff-evidence.md) | the empty-diff evidence, per mandated scenario | evidence of parity, which is a measurement; this register is a specification of what parity must include |

Further reading inside the repository, none of it modified by this work: `README-python-migration.md`
for how to build the oracle, seed a scenario, run both cycles and diff them; and the maintainer's own
`README.TXT` and `Changelog` for the COBOL system's history — including, at
`[README.TXT:L50-L53]`, the statement that gives this register much of its urgency: all testing is
complete for the IRS, Stock and Sales sub systems apart from some reports, while General has not been
worked on at all since the migration to the GnuCobol 3.2 compiler. The General Ledger contributes the
majority of the in-scope programs. Expected values for its scenarios must therefore come **only**
from the oracle, never from the documentation and never from reasoning about intent. Where the
compiled General Ledger behaves surprisingly, the surprise is the specification.
