# ACAS Posting Cycle — Traceability

This is the mapping document for the Python 3.12 migration of the ACAS posting cycle. It exists
because the migration's governing traceability rule requires the correspondence between the frozen
COBOL and the Python that replaces it to be **written down** rather than left for a reader to
reconstruct from the code. It carries three tables and nothing that belongs in a sibling document:

| Table | Mapping | Section |
| --- | --- | --- |
| **Table 1** | program → module, one-to-one for all twelve in-scope programs | [§7](#7-table-1--program--module) |
| **Table 2** | paragraph → function, with the `GO TO` class annotated at every transfer site | [§9](#9-table-2--paragraph--function) |
| **Table 3** | field → data-dictionary entry, derived from the authoritative triple | [§10](#10-table-3--field--dictionary-entry) |

Everything else here exists to make those three tables usable: the corrected locators the tables
rely on (§6), the phase labels a maintainer will otherwise misread (§8), the omissions that are
deliberate rather than lost (§11), the facade whose two naming conventions differ in *behaviour* and
not only in name (§12), the module arithmetic of the data-access layer (§13), the three linkage
shapes and the seven command-line routes that bind them (§14), the three divergent abort gates
(§15), and the five rejection classes (§16).

**The release this document describes.** `README.TXT` records the state as v3.3 pre-final, dated
2025-09-21 `[README.TXT:L36-L38]`. Eleven of the twelve in-scope programs carry a version in a
`prog-name` literal — for example `[general/gl080.cbl:L181]` — and `irs030` declares none, noting at
`[irs/irs030.cbl:L36]` that its version lives in working storage. Every locator below was read at
that release.

---

## 1. Rules provenance

**There is no user rules document for this project.** The Agent Action Plan states it directly in §0.7.1:
*"No separate user rules document was provided for this project."* Do not go looking for a rules file:
there is none, **enterprise-standard best practice applies wherever the Agent Action Plan is silent**,
and nothing has been invented to fill the gap.

The six binding rules — **R-1 … R-6** — nevertheless exist, in the **Agent Action Plan itself, §0.7.2**,
as a labelled rules block inside the user's requirements, retrievable via **`review_prompt`** and not
via `review_rules`. Recording both facts rather than dropping one is AAP §0.7.4 **C-5**'s resolution;
[`ambiguity-resolutions.md`](ambiguity-resolutions.md) §1 quotes it in full and is where the
arbitration reasoning lives.

---

## 2. The rules that govern this document

### 2.1 R-5 — Full traceability primary owner of this document

Quoted verbatim:

> *"Every program must map to a module, every paragraph to a function, and every field to a data-dictionary entry, and the mapping must be recorded as a document rather than left implicit in the code."*

Three clauses, three tables, one document. §7 is the program-to-module clause, §9 the
paragraph-to-function clause, §10 the field-to-dictionary clause, and this file is the "recorded as
a document" clause.

The rule collides with the licence to restructure `GO TO`, because restructuring tends to dissolve
paragraph boundaries. AAP §0.7.4 **C-4** resolves that collision, and its resolution is the design
principle Table 2 is built on. Quoted verbatim:

> *"every paragraph retains a named function even where its `GO TO` becomes a `continue`, a `break` or a `return`"*

> *"Keeping the function boundary fixed at the paragraph boundary and varying only the transfer mechanism satisfies both, and has the side benefit that the equivalence argument is reviewable one site at a time."*

That is exactly what the sibling modules do, and it is verifiable without reading this document:
every module under `acas_posting/programs/` exposes precisely **one** public symbol, `run`, and one
private function per paragraph. `acas_posting/programs/gl072_transaction_update.py`, for instance,
declares fifteen top-level functions of which `run` is the only public one, and the other fourteen
are `_gl072_main`, `_loop`, `_headings`, `_headings_end`, `_end_batch`, `_end_account`,
`_new_account`, `_end_run`, `_gl072_main_main_exit`, `_get_batch`, `_get_batch_main_exit`,
`_zz070_convert_date`, `_zz070_exit` and one record-image helper — one per paragraph of
`general/gl072.cbl`, plus the helper.

### 2.2 R-1 — No COBOL at runtime

> *"The Python implementation must not execute, embed, or shell out to the COBOL programs. COBOL is the specification for the migration, not a runtime dependency of the result. The shipped artifact must run on a host with no COBOL compiler and no COBOL runtime present."*

Nothing in this document may imply the shipped package invokes COBOL, and nothing does. Every
COBOL locator below is cited **as specification**. AAP §0.7.4 **C-1** states the confinement:

> *"compiled COBOL is confined to `harness/`, invoked only as an out-of-process comparison and seeding utility by the test suites, and never appears on any import path or code path of `acas_posting/`."*

and AAP §0.3.1 states the structural consequence: *"there is no import path from `acas_posting` to
`harness`."* Two proofs of that were verified in this checkout rather than assumed, and one earlier
argument is withdrawn:

- `pyproject.toml` declares packaging as `[tool.setuptools.packages.find]` with
  `include = ["acas_posting*"]` — resolving to exactly the seven code packages — against an explicit
  `exclude = ["harness*", "tests*", "docs*", "data_dictionary*"]`, and `include-package-data = false`.
  `harness` is excluded BY NAME rather than by setuptools' automatic behaviour, and the generated
  dictionary stays the top-level sibling AAP §0.3.1 fixes it as. Belt and braces:
  `harness` is in pytest's `[tool.pytest.ini_options] norecursedirs` and `harness/*` in the coverage
  `[tool.coverage.run] omit` list.
- A search of `harness/*.py` for `import acas_posting` or `from acas_posting` returns **zero** hits,
  so the dependency does not run in the other direction either. Measured, not asserted.
- **ONE ARGUMENT IS DELIBERATELY NOT MADE: the absence of `harness/__init__.py` proves nothing.**
  It looks like the obvious first proof and it is invalid — PEP 420 makes a directory without
  `__init__.py` an implicit namespace package, so `import harness.diff_states` would resolve
  from a process rooted at the repository. The isolation is real and the two proofs above
  establish it; the missing marker file does not.

### 2.3 R-2 — Zero binary floating point

> *"No accounting value may pass through a binary floating-point type at any point — not in computation, not in storage, not in transport."*

R-2 governs the shape of Table 3: **every** field entry carries digits, scale, signedness and usage,
at all three layers, because those four properties are what determine whether a value can be
represented exactly. §10.6 gives the storage-class census; §10.4 gives the numeric census of the
frozen schema, whose relevant fact is that it contains **zero** `FLOAT`, `DOUBLE` or `REAL` columns,
so the transport layer cannot reintroduce a float even by accident. AAP §0.5.1 makes the exclusion
of the two obvious offenders absolute: `pandas` and `numpy` are barred outright, *including* from the
harness comparison, precisely because both compute in binary floating point by default.

### 2.4 R-3 — No new validations, fields or schema changes; no concurrency

> *"The migration may not add validation logic, add fields, or alter the database schema, and must not introduce concurrent execution."*

A document that describes a schema in this much detail needs a licence, and AAP §0.7.4 **C-2** is
it:

> *"R-3 constrains the database, not the repository. Describing a schema in a committed artifact is orthogonal to altering it."*

Nothing here proposes a column, an index, a constraint or a DDL statement. §10.4 records what the
frozen schema *is*, including the two single-instance features a reader would otherwise assume away.

### 2.5 R-4 — Legacy anomalies reproduced, never fixed

> *"Defects present in the compiled behavior are part of the specification. A defect reproduced is a success; a defect fixed is a failure."*

Here R-4 forbids *tidying the mapping*. Where the frozen source uses one label six times, Table 2
records six functions. Where three sibling programs agree and a fourth does not, §15 and §16 record
the divergence rather than the consensus. Where a wrapper section is named after one thing and its
exit label after another, §11 records both names. Anomalies are cross-referenced by identifier into
[`anomaly-log.md`](anomaly-log.md) rather than restated, so that the register stays the single place
each defect is described.

### 2.6 R-6 — Compiled behavior is the tie-breaker

> *"Where a semantic question is ambiguous, the compiled program's observed behavior decides it, and each such resolution must be documented rather than settled silently."*

Where a Class-4 equivalence argument, a stored value or a record length is not settled by reading,
this document says so and cross-references a `Q-` identifier in `ambiguity-resolutions.md` rather
than picking an answer. **No claim below is a report of an observed oracle run.** Everything here was
established by reading the frozen source and the sibling Python modules in this checkout.

---

## 3. The honesty mandate

AAP §0.4.5, verbatim:

> *"The traceability, anomaly and ambiguity documents are byproducts of writing the program modules and would be fabrications if written separately."*

Accordingly:

- Every COBOL locator below was verified by reading the cited file at the cited line in this
  checkout. §6 lists the places where doing so contradicted the Agent Action Plan.
- Every Python name below was read out of the sibling module, not invented. Where the sibling names
  a function, Table 2 gives that name; nothing is predicted.
- Where a file named in the plan does **not** exist in this checkout, this document cites the **plan
  section** that names it and says plainly that it is a companion deliverable rather than an
  observed file. §17.2 lists every such case.

## 4. The freeze

AAP §0.8.1, verbatim:

> *"Any diff touching `common/*.cbl`, `common/*.scb`, `copybooks/*.cob`, `general/*.cbl`, `sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl` or `mysql/ACASDB.sql` is a defect in the migration, regardless of how harmless it appears."*

Reading only. Additionally, per AAP §0.2.1.4, the maintainer's `README.TXT`, `README`, `README.SVN`,
`README.nightly`, `Changelog` and `ACAS-Manuals/` are **never** edited; this document
cross-references them instead.

## 5. Citation convention

Every claim about the existing system carries an inline `[<path>:<locator>]` citation, following AAP
§0.1, *"so that downstream execution agents can verify each statement against the source rather than
trusting this document."* Paths are repository-root relative. `L<n>` is a single line; `L<n>-L<m>` is
an inclusive span; `§<n>` before a line number means "the section whose header is at line n". A
citation with no line number refers to the file as a whole.

Two conventions recur and are stated once:

- A section span is given to its **last executable line**, not to the blank comment that follows it.
  `batch-print` is `[general/gl051.cbl:L999-L1166]` because `main-exit.   exit section.` is at L1166,
  even though the next section header is at L1169.
- Where the Agent Action Plan and the source disagree, the source wins and the disagreement is
  listed in §6. A citation that does not resolve is worse than no citation, because it teaches the
  reader to stop checking.

---

## 6. Corrected locators

**The Agent Action Plan contains numerous citation errors, and this document uses verified values
throughout.** Each correction this document relies on is listed here rather than applied silently.
Every "verified" cell was read at that line in this checkout.

| # | Claim | AAP locator | Verified | What is actually at the AAP locator |
| --- | --- | --- | --- | --- |
| C-01 | Phase-1 banner | `general/gl070.cbl:L283` | **`general/gl070.cbl:L284`** | L283 is `move zero to a.` |
| C-02 | Phase-2 banner | `general/gl070.cbl:L291` | **`general/gl070.cbl:L292`** | L291 is a blank comment |
| C-03 | Phase-4 banner | `general/gl072.cbl:L277` | **`general/gl072.cbl:L274`** | L277 is `perform GL-Nominal-Open.` |
| C-04 | Phase-5 banner | `general/gl080.cbl:L330` | **`general/gl080.cbl:L336`** | L330 is a blank comment |
| C-05 | SL/PL linkage shape | "the four-parameter SL/PL linkage shape", §0.4.1.1 | **five parameters**, e.g. `[sales/sl060.cbl:L395-L399]` | §0.1.1 and all six programs give five; the third is spelled `system-record-4` |
| C-06 | Sales invoice-post dispatch | `sales/sales.cbl` `load08.` | **`sales/sales.cbl:L756-L768`, `load07.`** | `load08.` at L770 dispatches `sl080`, which §0.2.2 places out of scope |
| C-07 | GL post-cycle dispatch | `general/general.cbl:L806-L816` and `L800-L814` | **`general/general.cbl:L805-L815`** | both spans straddle the paragraph boundary at L805 |
| C-08 | `gl080` dispatch | `general/general.cbl:L711-L723` | **`general/general.cbl:L817-L821`** | L711 is `load00.`, the shared 4-parameter call paragraph |
| C-09 | `end-batch` gate | `general/gl051.cbl:L1096-L1133` | **`general/gl051.cbl:L1096-L1134`** | the paragraph's last statement, `go to main-exit.`, is at L1134 |
| C-10 | `Ledger-Postings-Add` | `irs/irs030.cbl:L1569-L1733` | **`irs/irs030.cbl:L1569-L1730`** | the section ends `exit section.` at L1730; L1732 is the facade `copy` |
| C-11 | Phase-1 cycle filter | `general/gl070.cbl:L309-L310` | **`general/gl070.cbl:L312-L313`** | L309-L310 is the at-end test `if fs-reply = 10 go to end-run` |
| C-12 | Open-batch detection | `general/gl070.cbl:L312-L313` | **`general/gl070.cbl:L314-L315`** | L312-L313 is the cycle filter |
| C-13 | Phase-2 status filter | `general/gl070.cbl:L455-L459` | **`general/gl070.cbl:L460-L463`** | L455 is the at-end `go to end-run`; L456-L459 spans a comment |
| C-14 | Sequential nominal read | `general/gl072.cbl:L410-L412` | **`general/gl072.cbl:L408`**, guard L407, key move L405 | L410-L411 is the *post-read* `if read-ledger not = "R"` guard |
| C-15 | Non-numeric batch skip | `general/gl072.cbl:L289-L290` | **`general/gl072.cbl:L291-L292`** | L289 is `go to end-run.`, part of the at-end phrase |
| C-16 | `we-error = 999` skip | `general/gl072.cbl:L303-L304` | **`general/gl072.cbl:L306-L307`**, plus a second site at **L348-L349** | L303-L304 are a blank comment and `if post-ledger` |
| C-17 | Batch stamping | `general/gl072.cbl:L373-L377` | **`general/gl072.cbl:L375-L377`** | L373-L374 are the paragraph's underline comment and a blank |
| C-18 | `gl072` stub block | `general/gl072.cbl:L134-L153` | **`general/gl072.cbl:L135-L155`** | L134 is a blank comment; the block's last entry is at L155 |
| C-19 | IRS derived columns | `mysql/ACASDB.sql` L277-L279 (implied) | **`mysql/ACASDB.sql:L278-L280`** | L277 is `POST4-DAT`, the raw date text |
| C-20 | Second `sign is leading` | `copybooks/irswspost.cob:L19` | **`copybooks/irswspost.cob:L18`** | L19 is the file's closing `*>` |
| C-21 | Calling-data block | `copybooks/wscall.cob:L6-L13` | **`copybooks/wscall.cob:L7-L14`** for the seven leaves, group at L6 | the span omits `WS-CD-Args` at L14 |
| C-22 | `File-Access` block | `copybooks/wsfnctn.cob:L23-L38` | **`copybooks/wsfnctn.cob:L22-L41`** | `FS-Action` is at L41, outside the span; L22 is the `01` |
| C-23 | `Logging-Data` block | `copybooks/wsfnctn.cob:L44-L56` | **`copybooks/wsfnctn.cob:L44-L55`** | L56 is `03 RDB-Data.`, the next group |
| C-24 | `RDB-Data` block | `copybooks/wsfnctn.cob:L57-L64` | **`copybooks/wsfnctn.cob:L56-L62`** | the six leaves end at L62; L64 is a comment |
| C-25 | Work-file names | `copybooks/wsnames.cob:L14-L17` | **`copybooks/wsnames.cob:L15-L16`** | L14 is `02 file-defs-a.`; L17 is the first `copy` |
| C-26 | `acas000` dispatch arity | "four-way", §0.3.1 and §0.4.1.5 | **five-way**, `[common/acas000.cbl:L574-L600]` | key 5 aliases `systemMT` at L596; the range check at L335 admits 1 thru 5 |
| C-27 | `PERFORM … THRU` | "seven times", spelled `THRU` | **nine live sites**, in two spellings; **four** inside the migrated surface | `gl072`'s two are spelled `through`, so a `THRU` search misses them — see §9.5 |
| C-28 | `main-exit.` in `sl060` | two occurrences | **six**: L763, L789, L813, L829, L845, L973 | the plan names only the two in the two `-Comp` sections |
| C-29 | IRS fan-out test sites | "three sites in each of the four" | **seven, seven, seven and six** — 27 in total | see §16.6; `pl100` also tests a *weaker* predicate at L566 |
| C-30 | Schema column `COMMENT` | "the schema's **only** `COMMENT`" | **fifteen**: L155, L562-L567, L575, L597, L602, L603, L610, L902, L903, L909 | `POST-RRN` at L155 is the *first*, not the only |
| C-31 | Field-name collision | `general/gl070.cbl:L510` | **`general/gl070.cbl:L497`, `L521`, `L525`** | L510 is an ordinary unqualified `move post-cr to pre-ac.` |
| C-32 | Class-1 share of `GO TO` sites | "the most common class **by a wide margin**", §0.4.2 | most common, but by **83 sites to 69** | the full census is in §9.1: C1 83, C3 69, C2 38, C4 16, total 206. C1 leads C3 by 20%, so this document publishes the counts and drops the adjective |

Corrections C-14, C-15, C-16, C-20 and C-31 were reached independently here and match
[`anomaly-log.md` §8](anomaly-log.md) exactly; the two documents were verified against the source
separately and agree.

---

## 7. Table 1 — program → module

One COBOL program, one Python module, twelve times, with no merging and no splitting. Line counts
were taken with `wc -l` in this checkout and total **10,495**.

| COBOL program | Lines | Python module | Migration boundary |
| --- | --- | --- | --- |
| `general/gl051.cbl` | 1282 | `acas_posting/programs/gl051_batch_control_check.py` | **PARTIAL** — the control-total gate: `batch-print` §999, spanning `[general/gl051.cbl:L999-L1166]`, of which `end-batch` L1096-L1134 is the gate; plus the **seven arithmetic fragments AAP §0.4.1.2 names by locator**, all in `gl050c` §496 and none of them reachable from the gate — `net.` L788 (`ROUNDED` L791), `gross.` L793 (`ROUNDED` L796 then the destructive un-`ROUNDED` `subtract` L797), `accept-date.` L582 (the scaling divides L604, L607), `accept-amount.` L650 (the scaling multiplies L654, L657) and `get-description.` L799 (the fifth multiply L803) |
| `general/gl070.cbl` | 612 | `acas_posting/programs/gl070_transaction_pre_process.py` | Whole posting path — Phase 1 (`gl071a` §300) and Phase 2 (`gl071b` §444 with `gl071b-pre-process` §477) |
| `general/gl071.cbl` | 182 | `acas_posting/programs/gl071_batch_sort.py` | Whole program. A pure sort: **zero `GO TO`**, **zero `MOVE`**, **zero arithmetic verbs**, **no sections at all**, and the only in-scope program that copies **no** facade copybook and touches **no** table |
| `general/gl072.cbl` | 498 | `acas_posting/programs/gl072_transaction_update.py` | Whole program — Phase 4 |
| `general/gl080.cbl` | 750 | `acas_posting/programs/gl080_end_of_cycle.py` | Whole program — archiving, deletion, posting contraction and end-of-period |
| `sales/sl055.cbl` | 732 | `acas_posting/programs/sl055_invoice_extract_analysis.py` | Whole program |
| `sales/sl060.cbl` | 1301 | `acas_posting/programs/sl060_invoice_posting.py` | Whole program, including the IRS fan-out |
| `sales/sl100.cbl` | 817 | `acas_posting/programs/sl100_cash_posting.py` | Whole program |
| `purchase/pl055.cbl` | 635 | `acas_posting/programs/pl055_order_proof_extract.py` | Whole program |
| `purchase/pl060.cbl` | 1155 | `acas_posting/programs/pl060_order_posting.py` | Whole program, including the IRS fan-out |
| `purchase/pl100.cbl` | 798 | `acas_posting/programs/pl100_payment_posting.py` | Whole program |
| `irs/irs030.cbl` | 1733 | `acas_posting/programs/irs030_posting.py` | **PARTIAL** — `Ledger-Postings-Add` §1569, spanning `[irs/irs030.cbl:L1569-L1730]`; plus `Net` §1544 and `Gross` §1556, whose two `ROUNDED` VAT computes (L1551, L1562-L1563) the posting path consumes |

`acas_posting/programs/` is closed at exactly **13** files — the twelve above plus `__init__.py` —
verified by listing the directory. Every one of the twelve exposes exactly one **callable** entry
point, `run`, whose positional parameters preserve the COBOL `PROCEDURE DIVISION USING` order
exactly; §14 gives the three shapes.

**"One callable entry point" is not "one exported symbol", and one module proves the difference.**
`acas_posting/programs/gl080_end_of_cycle.py`'s `__all__` declares
`__all__ = ("DiskChangeOptionNotAcceptable", "run")` — two names, because the module also publishes
the exception type it raises when the disk-change option is neither of the two values the frozen
input loop accepts (`general/gl080.cbl:L548-L549`). Its class is at
`[acas_posting/programs/gl080_end_of_cycle.py DiskChangeOptionNotAcceptable]`, and it is raised in place of the frozen
paragraph's interactive re-prompt, which has no headless equivalent — the re-prompt's effect is that
nothing below `general/gl080.cbl:L406` runs at all, and refusing is the only disposition that keeps
the database effect inside the set the frozen program can produce. It is exported so that a caller
reaching `run` directly can distinguish that refusal from any other `ValueError`; **no committed
caller catches it today**, because `acas_posting/cli/gl_end_of_cycle.py` restricts
`--disk-change-option` to `{0, 9}` and an out-of-range command line therefore fails at argparse
first. Every other one of the twelve declares `__all__ = ("run",)`, verified by reading all thirteen
files. The distinction is recorded rather than smoothed away because "precisely one public symbol"
is the tempting summary and a reader can check it in one grep and find it false.

### 7.1 The two partial boundaries are narrow, and both files are dominated by out-of-scope code

Quoting AAP §0.8.7: *"an agent working from the file rather than from the stated boundary would
migrate several hundred lines that must not be migrated."* The boundaries are therefore stated as
line spans, not as prose.

**`gl051` — 1282 lines, of which 172 are in scope.** Out of scope, and named here so the boundary is
unmistakable: `gl051-Main` §359, `proof-all` §474, `gl050c` §496, `batch-amendment` §825 and
`gl050d` §961. The in-scope span is `batch-print` §999 through L1166 plus the three paragraphs at
L788, L793 and L799 that sit *inside* the out-of-scope `gl050c` section but are reached by the gate.

**`gl051` has no command-line entry point.** It is the one in-scope program that no menu
paragraph dispatches as part of a posting run — the General menu's posting routes are `load08.` and
`load09.` `[general/general.cbl:L805-L815]`, `[general/general.cbl:L817-L821]`, and neither names
`gl051`. Its module is consequently a library function, exercised at the arithmetic tier by the
control-total parity test named in AAP §0.4.1.7, and §7.2 of `anomaly-log.md` records the same
boundary from the anomaly side.

**`irs030` — 1733 lines, of which 187 are in scope.** Out of scope: `Init-Main` §557,
`Input-Headings` §1239, `Date-Validate` §1285, `Initialise-Main` §1402, `Show-Default` §1504 and
`file-init` §1518.

Two distinct facts about `irs030`'s tail must both be recorded, because conflating them produces a
citation that does not resolve:

- The **section** ends at **L1730** — `main99-exit.` at L1729, `exit     section.` at L1730.
- The **file** is exactly **1733** lines, and L1732 is `copy "Proc-ZZ100-ACAS-IRS-Calls.cob".`

A third fact makes the boundary sharper still: `Input-Loop` is declared **twice** in `irs030` — at
`[irs/irs030.cbl:L797]` inside the out-of-scope `Init-Main`, and at `[irs/irs030.cbl:L1619]` inside
the in-scope `Ledger-Postings-Add`. COBOL resolves an unqualified paragraph reference within the
containing section first, so the four `go to Input-Loop` statements at L1634, L1652, L1683 and L1700
all target **L1619**. The Python function is `_input_loop`, private to
`acas_posting/programs/irs030_posting.py`, and the out-of-scope twin has no counterpart at all.

### 7.2 Which test drives each module, and at which tier

R-5 asks that every program map to a module. A map alone does not show the module was ever
**executed**, so this table records where each one is driven, measured in this checkout rather
than predicted — by scanning `tests/` for imports of `acas_posting.programs.*` and by reading the
`Modules exercised` line of each scenario in
[`scenario-diff-evidence.md`](scenario-diff-evidence.md) §10.

Two tiers, and the distinction is load-bearing because only one of them runs everywhere:

- **Arithmetic tier — in-process, and runs on a bare host.** The test imports the shipped module
  and calls its own functions. Needs only `data_dictionary/acas_posting_dictionary.json`.
- **Scenario tier — out-of-process through the real CLI, and SKIPS without the Compose stack.**
  The runner drives `python -m acas_posting`, so the module executes as it does in production.

| Python module | Driven in-process by | Driven out-of-process by | Both tiers? |
| --- | --- | --- | --- |
| `gl051_batch_control_check.py` | `tests/arithmetic/test_control_total_comparison.py` — drives `_end_batch` | **no scenario at all** | in-process only |
| `gl070_transaction_pre_process.py` | — | `clean_batch_gl`, `mixed_accepted_rejected` | scenario only |
| `gl071_batch_sort.py` | — | `clean_batch_gl`, `mixed_accepted_rejected` | scenario only |
| `gl072_transaction_update.py` | `tests/arithmetic/test_ledger_balance_accumulation.py` — drives both silent-skip branches and, in `test_the_empty_work_file_still_performs_end_account_then_end_batch`, the EMPTY work file's at-end path, where `end-account` and `end-batch` run unconditionally on zero keys | `clean_batch_gl`, `mixed_accepted_rejected` | **both** |
| `gl080_end_of_cycle.py` | `tests/arithmetic/test_gl080_cycle_divide_rounded.py` — drives the `ROUNDED` divide, the unbounded subscript, the rotating counter, and the archive and deletion phases | **no scenario at all** | in-process only |
| `sl055_invoice_extract_analysis.py` | — | `clean_batch_sl`, `period_end_totals` | scenario only |
| `sl060_invoice_posting.py` | `tests/arithmetic/test_compute_truncate_unrounded.py` — drives `_ba000_sales_comp` and `_ba000_credit_comp`; `tests/arithmetic/test_double_entry_explosion.py` — drives `_ca000_bl_close` over the full `IRS-Instead` × `Level-1` truth table, which is A-1's primary lock | `clean_batch_sl`, `period_end_totals` | **both** |
| `sl100_cash_posting.py` | `tests/arithmetic/test_compute_truncate_unrounded.py` — drives `_compute_sales_pay` | `period_end_totals` | **both** |
| `pl055_order_proof_extract.py` | — | `clean_batch_pl`, `period_end_totals` | scenario only |
| `pl060_order_posting.py` | `tests/arithmetic/test_compute_truncate_unrounded.py` — drives `_purch_comp` and `_credit_comp` | `clean_batch_pl`, `period_end_totals` | **both** |
| `pl100_payment_posting.py` | `tests/arithmetic/test_compute_truncate_unrounded.py` — drives `_init01__compute_purch_pay` | `period_end_totals` | **both** |
| `irs030_posting.py` | `tests/arithmetic/test_irs_vat_from_net.py`, `tests/arithmetic/test_irs_vat_from_gross.py` — drive `Net` and `Gross`; `tests/arithmetic/test_double_entry_explosion.py` — drives `_input_loop` for the IR032 clean rejection and its A-4 counterpart | `clean_batch_irs` | **both** |

**Two modules are driven by no scenario, and the reason differs in each case.**

`gl051_batch_control_check.py` has no command-line entry point at all — §7.1 records why: neither
`load08.` nor `load09.` names `gl051`, so it is a library function. Its gate is therefore reachable
only in-process, which is what `test_control_total_comparison.py` does.

`gl080_end_of_cycle.py` **does** have a route — `acas_posting/cli/gl_end_of_cycle.py`, the
`gl_end_of_cycle` operation — but **no scenario declares that operation**, so nothing drives it
end-to-end. AAP §0.3.1 and §0.8.5 fix the scenario set at exactly eight and none of the eight is an
end-of-cycle journey, so a ninth was **not** added; the gap is closed at the arithmetic tier
instead, in-process against the shipped module. This is recorded as a bounded divergence in the
header of `tests/arithmetic/test_gl080_cycle_divide_rounded.py` and in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md) §16.1.

**Four modules are driven only by the stack-bound tier**, and the honest consequence is stated
rather than glossed: on a host without the Compose stack, `gl070`, `gl071`, `sl055` and `pl055` are
**imported** — transitively, because `tests/arithmetic/test_control_total_comparison.py` imports
the seven `acas_posting/cli/` route modules, and importing all seven pulls in eleven of the twelve
program modules — but **none of their own functions is called**. Import proves the module parses and
that its own imports resolve; it does not exercise its logic. What closes that gap is the scenario
tier, and the evidence for it is the per-scenario empty diff in
[`scenario-diff-evidence.md`](scenario-diff-evidence.md) §10, not this table — and that diff is
against the **disclosed-transformed diagnostic** oracle rather than the frozen one, because the frozen
sources do not compile from this checkout. So the gap is closed to the extent that the two
implementations are shown to agree, and no further; §0 of that document states the position.

### 7.3 The coverage-tooling evidence, produced rather than promised

AAP §0.5.1 pins `pytest-cov` as *"evidence that every traced module is actually exercised — a
traceability support, not a quality gate"*. A pinned tool with no published command evidences
nothing, so the command, its destinations and its measured output are all recorded. The command is
in [`README-python-migration.md`](../../README-python-migration.md) §12.4 and is
`python -m pytest -m arithmetic --cov --cov-report=term-missing:skip-covered`; `[tool.coverage.run]`
fixes `source = ["acas_posting"]` with `branch = true`, omitting `harness/*` and `tests/*` for R-1,
and `[tool.coverage.html]`/`[tool.coverage.xml]` fix the two report destinations. All three
artifacts — `.coverage`, `coverage.xml`, `htmlcov/` — are gitignored, so producing the evidence adds
no tracked file and does not disturb the inventory AAP §0.4.1 fixes.

Measured on this checkout, CPython 3.12.13:

| Quantity | Value |
| --- | --- |
| Tests run by the command | **1,219 passed**, 114 deselected (the stack-bound tiers) |
| `acas_posting` modules measured | **89 of 89** |
| Modules with **zero** coverage | **0** |
| Modules at 100 % | 18 |
| Statements covered | 15,293 of 31,865 |
| Branches covered | 1,529 of 6,874 |
| Overall, branch-inclusive | **43.4 %** |

**Every figure here is re-measured against the tree as it stands rather than carried forward**, because
two of them are sensitive to its shape: merging the six extra arithmetic groups into the fourteen
planned files changes the deselection arithmetic, and keeping the connection-parameter reader inside
`cli/args.py` rather than in a module of its own changes the module count. A figure whose whole
purpose is to be reproducible has to match what reproducing it yields.

**There is no `fail_under` and no `--cov` in `addopts`,** deliberately: a coverage number never
decides whether this migration is correct, and an ordinary `pytest` run must not require the plugin.

**No module is at zero, and the generator is covered by being run.** `dictionary/generate.py` used to
be the single zero-coverage module because the arithmetic tier reads the committed artifact rather
than rebuilding it; the merged deployment-contract group now reads the generator to close the
traceability census, which brings it to **24 %**. Its real exercise is still the run:
`python -m coverage run -m acas_posting.dictionary.generate --check` reports **90 %** of its 1,707
statements, with the `--check` itself exiting **0** — the committed dictionary is byte-reproducible
from the frozen sources. Every module in the package is now reached by the infrastructure-free tier,
which is precisely the R-5 claim being evidenced; §7.2's caveat about the four modules that are only
**imported** by that tier stands unchanged and is not softened by a coverage percentage.

---

---

## 8. The five phase labels, and their non-sequential execution

AAP §0.6.4 requires this be recorded *"in the module docstrings so a maintainer is not misled"*, and
it is recorded here for the same reason. All five banners were read at the lines given; four of the
Agent Action Plan's locators for them are wrong (§6, C-01 to C-04).

| Banner text | Locator | Program | Executes |
| --- | --- | --- | --- |
| `"Phase - 1.  Batch Check"` | `[general/gl070.cbl:L284]` | `gl070` | first |
| `"Phase - 2.  Transaction Pre-process"` | `[general/gl070.cbl:L292]` | `gl070` | second |
| *(no banner — `gl071` displays only `"Sorting.......Please wait"`)* | `[general/gl071.cbl:L170]` | `gl071` | third |
| `"Phase - 4.  Transaction Update"` | `[general/gl072.cbl:L274]` | `gl072` | fourth |
| `"Phase - 3.  Transaction Deletion"` | `[general/gl080.cbl:L319]` | `gl080` | fifth |
| `"Phase - 5.  End of Period Processing"` | `[general/gl080.cbl:L336]` | `gl080` | last |

⇒ **Transaction deletion is labelled Phase 3 but executes after Phase 4**, because `gl080` is reached
through a *different* menu route (`load09.`) that runs after the `load08.` route has already run
`gl070`, `gl071` and `gl072`.

`gl080` additionally carries three banners the plan does not mention, and they collide with `gl070`'s
and `gl072`'s numbering — **three** collisions, not the two sometimes claimed:

| `gl080` banner | Locator | Collides with |
| --- | --- | --- |
| `"Phase - 1.  Batch Check"` | `[general/gl080.cbl:L306]` | `gl070` L284 — the text is **character-for-character identical** |
| `"Phase - 2.  Transaction Archiving"` | `[general/gl080.cbl:L316]` | `gl070` L292 — same number, different text |
| `"Phase - 4.  Posting Contraction "` | `[general/gl080.cbl:L637]` | `gl072` L274 — same number, different text |

Two further facts about `gl080`'s own banners, both load-bearing for a reader tracing execution:

- L316 and L319 are the **two arms of one `if archiving`** at `[general/gl080.cbl:L315]`, so Phase 2
  and Phase 3 are mutually exclusive within a single run — never both.
- The Phase-5 banner at L336 appears **earlier in the file** than the Phase-4 banner at L637, because
  L637 sits inside `compress-post` §628, which is performed from `[general/gl080.cbl:L322]`. Source
  order and execution order disagree, and within `gl080` alone the banners fire in numeric order.

---

## 9. Table 2 — paragraph → function

### 9.1 The four-class `GO TO` taxonomy

Every `GO TO` in the in-scope programs falls into exactly one of four classes. The census below was
taken over all twelve files and leaves no residue.

**Notation.** In the per-program inventories of §9.3 the class is written in the shortest form that
still resolves: **C1**, **C2**, **C3** and **C4** mean Class 1, Class 2, Class 3 and Class 4 of this
table, and nothing else. A site is written as the line number of the `GO TO` itself, then its class,
then its target — `L310 **C2** → end-run` reads *"the `GO TO` at line 310 is a Class 2 forward
terminator whose target is the `end-run` label."* Where several `GO TO` statements in one paragraph
share both a class and a target they are listed as one comma-separated run, so the number of
annotations is smaller than the number of sites.

| Class | COBOL shape | Python | Why it is safe, or what makes it risky |
| --- | --- | --- | --- |
| **1** loop-back | targets an earlier iteration label in the same paragraph group — `loop`, `read-loop`, `da010-read-loop`, `ba010-read-loop`, `input-loop`, `main-loop`, `loop1`, `loop2` | `continue` inside `while True:` | The most common class, and unconditionally safe: a backward transfer to the head of a read loop skips no code that would otherwise execute |
| **2** forward terminator | targets a label that ends the iteration and then continues with post-loop work — `end-run`, `end-report`, `main-end`, `end-loop`, `input-end`, `pack-end`, `loop1-end`, `loop2-end`, `headings-end`, `loop-end`, `da040-close-files`, `EOJ` | `break` **plus** faithful placement of the post-loop block | The transformation is `break` **and the work**, never `break` alone. AAP §0.6.3: *"Mis-splitting here would silently drop end-of-run processing."* §9.4 walks the strongest instance in full |
| **3** section or paragraph exit | targets the trailing exit label — `main-exit`, `main-ex`, `main99-exit`, `menu-exit`, `csp-exit`, `zz050-exit`, `zz060-Exit`, `zz070-Exit`, `db999-main-exit`, `dc999-main-exit`, `dd999-main-ex`, `Main-Exit` | `return` | Unconditionally safe: a forward transfer to a section's trailing exit label cannot skip code that would otherwise run |
| **4** sibling re-dispatch | targets a peer paragraph that performs work and then itself transfers control — `da030-skip-invoice`, `next-1`, `file-error`, `ba000-Main-Rewrite`, `main-rewrite`, `Get-Default`, `Open-Error-Continued`, `header-analysis`, `Create-Anal`, `Chk-Ans` | a named call followed by an **explicit** `continue` or `return` | **The only class requiring per-site proof.** Which control statement follows the call depends on where the target's *own* transfer goes, so each site is argued individually |

**The distribution, counted rather than asserted.** Summing the annotations in §9.3 over all twelve
programs gives **206 `GO TO` sites**, carried by 123 annotations:

| Class | Sites | Share | Annotations |
| --- | --- | --- | --- |
| **C1** loop-back | 83 | 40% | 42 |
| **C3** section or paragraph exit | 69 | 33% | 38 |
| **C2** forward terminator | 38 | 18% | 32 |
| **C4** sibling re-dispatch | 16 | 8% | 11 |
| **total** | **206** | 100% | **123** |

Two consequences worth drawing out, because both bear on how much of this migration is mechanical.
First, **C1 and C3 together are 74% of all sites**, and both are unconditionally safe, so roughly
three-quarters of the control-flow transformation needs no argument beyond its class. AAP §0.6.3 puts
the same point as *"Class 1 (loop-back) and Class 3 (exit) together account for the large majority of
sites and are unconditionally safe"* — the census confirms it and supplies the number. Separately,
AAP §0.4.2 calls C1 the most common class *"by a wide margin"*; it is indeed the most common, but the
measured margin over C3 is 83 to 69, so this document reports the counts and drops the adjective.
Second, **C4 is 8% of sites — 16 in total** — which is what makes the per-site proof obligation
tractable rather than theoretical. §9.4 works one of the sixteen through in full and every other is
annotated in place.

### 9.2 How a paragraph name becomes a function name

The rule is mechanical, so traceability is checkable rather than trusted:

1. Lower-case the COBOL label and replace `-` with `_`.
2. Prefix a single `_`, because paragraph functions are private to their module; only `run` is public.
3. Where the same label is declared in more than one section of the same program, prefix the
   **section** name so the two remain distinct functions — for example `sl060`'s six `main-exit.`
   labels become `_ba000_cr_swop__main_exit`, `_ba000_new_heading__main_exit`,
   `_ba000_headings__main_exit`, `_ba000_sales_comp__main_exit`, `_ba000_credit_comp__main_exit` and
   `_ba000_apportion__main_exit`. This is R-4 applied to names: six labels, six functions, no merging.
4. A trailing exit label whose only statement is `exit section.` or `goback.` may be realised as the
   enclosing function's `return` rather than as a separate function. Where a module does that, this
   document says so in the program's table rather than claiming a function that does not exist.

### 9.3 Per-program paragraph inventories

Each table below lists every section and paragraph of the program's `PROCEDURE DIVISION` in source
order, the Python function that carries it, and the `GO TO` sites inside it with the class applied.
"—" in the `GO TO` column means the paragraph contains none.

#### `general/gl051.cbl` → `gl051_batch_control_check.py` (in-scope portion)

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `batch-print` §  | `[general/gl051.cbl:L999]` | `_batch_print` | — |
| `loop.` | `L1005` | `_loop` | L1010 **C2** → `end-batch`; L1013, L1030, L1065 **C1** → `loop` |
| `get-a-batch.` | `L1067` | `_get_a_batch` | — |
| `headings.` | `L1074` | `_headings` | — |
| `end-batch.` | `L1096` | `_end_batch` | L1100, L1103, L1134 **C3** → `main-exit` |
| `get-description.` | `L1136` | `_batch_print_get_description` | — |
| `main-exit.   exit section.` | `L1166` | `_batch_print_main_exit` | — |

The five paragraph fragments below are the arithmetic AAP §0.4.1.2 names for this module. Every one of
them sits in `gl050c` §496, which §7.1 puts outside the boundary, and a census of every `perform`
between L999 and L1166 confirms **none is reachable from the gate** — so each function is present and
**has no caller inside the module**. They are reproduced anyway because the plan names them by
locator, and because §0.6.1's five-`ROUNDED`-site census counts L791 and L796: shipping three of five
would falsify both the census and R-2.

| COBOL paragraph | Locator | Python function | Statements carried |
| --- | --- | --- | --- |
| `net.` | `L788` | `_net` | **`ROUNDED` site 1 of 5** — `compute vat-amount rounded = post-amount * ws-vat-rate / 100.` L791 |
| `gross.` | `L793` | `_gross` | **`ROUNDED` site 2 of 5** L796, then the un-`ROUNDED` destructive `subtract vat-amount from post-amount.` L797 |
| `accept-date.` | `L582` | `_accept_date_scale_out` | the two scaling `divide … giving acc-ok` at L604 and L607, with the `array-pc` moves L605, L608. The `if convention = "DR"` block is the **last statement of `accept-date.`**, not the first of `get-account.` L610, even though L615 consumes it |
| `accept-amount.` | `L650` | `_accept_amount_scale_in` | the two scaling `multiply account-in by 100` at L654 and L657, with the `dr-pc`/`cr-pc` moves L655, L658 |
| `get-description.` | `L799` | `_gl050c_get_description_scale` | the fifth scaling multiply, `multiply account-in by 100 giving WS-Ledger-Nos.` L803. The `gl050c` twin of the in-scope L1136 paragraph — see §9.6 — and the only one of the two that scales |

`acc-ok` `[general/gl051.cbl:L233]` and `account-in` `[general/gl051.cbl:L178]` are **two fields
with one picture**, `pic 9(4)v99`, and the divides store into `acc-ok`. `move acc-ok to account-in.`
`[general/gl051.cbl:L615]` carries the value across in a later paragraph — and in between, the
out-of-scope `accept-account.` `[general/gl051.cbl:L464-L472]` may overwrite it, because `acc-ok`
**redefines** `ws-account-work` `[general/gl051.cbl:L229-L233]` and the `accept … update` at
`[general/gl051.cbl:L470]` writes that group's two fields. The divide therefore PRE-FILLS the field the
operator is shown. `_WorkingStorage` declares both `acc_ok` and `account_in`, because collapsing them
would fuse three frozen statements into two.

The gate itself, in the order the frozen source performs it: `if z = 99` L1099-L1100 → exit;
`if not truet` L1101-L1103 → status 0 and exit; the report moves L1105-L1108; **`add actual-vat to
actual-gross.` L1109**; the page-break test L1111-L1112 and three writes L1113-L1115; **the equality
test L1117-L1121**; then the three status banners L1123-L1133 and the exit at L1134. VAT enters the
actual gross *before* the comparison, and reversing those two steps would reject every batch carrying
VAT. `truet` is a condition name, not a field: `[copybooks/wsledger.cob]` is not its home —
`[general/gl051.cbl:L175]` declares `03  trutht              pic 9.` and `[general/gl051.cbl:L177]`
declares `88  truet                            value 1.`, so the predicate lives in
`acas_posting/cobol/condition_names.py`.

#### `general/gl070.cbl` → `gl070_transaction_pre_process.py`

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `init01` § | `L251` | `_init01` | — |
| `menu-input.` | `L274` | `_init01_menu_input` | — |
| `menu-input2.` | `L281` | `_init01_menu_input2` | L290 **C3** → `main-exit` (the abort; L289 sets `ws-term-code` to 5) |
| `main-exit.` | `L295` | `_init01_main_exit` | — (`goback.` L298) |
| `gl071a` § | `L300` | `_gl071a` | — |
| `loop.` | `L305` | `_gl071a_loop` | L310 **C2** → `end-run`; L313, L316 **C1** → `loop` |
| `end-run.` | `L318` | `_gl071a_end_run` | — |
| `main-exit.   exit section.` | `L323` | `_gl071a_main_exit` | — |
| `gl060a` § | `L325` | `_gl060a` | — |
| `loop.` | `L344` | `_gl060a_loop` | L349 **C2** → `end-report`; L352 **C1** → `loop`; L366, L371, L376 **C4** → `next-1` |
| `next-1.` | `L382` | `_gl060a_next_1` | L414 **C1** → `loop` |
| `screen-option.` | `L418` | `_gl060a_screen_option` | L424 **C2** → `end-report`; L427 **C1** → `loop` |
| `screen-clear.` | `L429` | `_gl060a_screen_clear` | — |
| `end-report.` | `L435` | `_gl060a_end_report` | — |
| `main-exit.   exit section.` | `L442` | `_gl060a_main_exit` | — |
| `gl071b` § | `L444` | `_gl071b` | — |
| `loop.` | `L450` | `_gl071b_loop` | L455 **C2** → `end-run`; L458, L463, L467 **C1** → `loop` |
| `end-run.` | `L469` | `_gl071b_end_run` | — |
| `main-exit.   exit section.` | `L475` | `_gl071b_main_exit` | — |
| `gl071b-pre-process` § | `L477` | `_gl071b_pre_process` | — |
| `loop.` | `L483` | `_gl071b_pre_process_loop` | L488 **C3** → `main-exit`; L491, L493, L523, L533 **C1** → `loop` |
| `main-exit.   exit section.` | `L535` | `_gl071b_pre_process_main_exit` | — |
| `zz060-Convert-Date` § | `L538` | `_zz060_convert_date`, delegating to `dates.zz060_convert_date` | L550, L556, L561 **C3** → `zz060-Exit` (L570), realised as the helper's `return` |
| `zz070-Convert-Date` § | `L573` | `_zz070_convert_date`, delegating to `dates.zz070_convert_date` | L586, L591 **C3** → `zz070-Exit` (L600), realised as the helper's `return` |
| `maps03` § | `L603` | `_maps03`, delegating to `dates.maps04` | — (exit label `maps04-exit.` L608; see §11.4) |

`gl070` has **four distinct `loop.` labels** — L305, L344, L450 and L483 — and **twelve**
`go to loop` statements between them. A count of "six" is reachable only by ignoring the second
occurrence in each paragraph and the whole of `gl060a`. Each label is a separate Python function, so
each `continue` is unambiguous; conflating them would fuse four loops into one.

The three-leg double-entry explosion, for the record, because it is the arithmetic the sort order
later depends on: the DR leg is L501-L508 with the `write` at L508; the CR leg is L510-L519 with
**`multiply pre-amount by -1 giving pre-amount` at L517** and the `write` at L519; the VAT leg is
guarded at L521-L523 and runs L525-L532 with a second **`multiply … by -1` at L530** and the `write`
at L532. `[general/gl070.cbl:L497]`, `[general/gl070.cbl:L521]` and `[general/gl070.cbl:L525]` are
the three qualified references that A-21 is about (§6, C-31).

#### `general/gl071.cbl` → `gl071_batch_sort.py`

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `main.` | `[general/gl071.cbl:L167]` | `_main` | — |
| `main-exit.` | `L180` | `_main_exit` | — (`goback.` L181) |

**`gl071` contributes two rows, and that is the point.** It declares **no sections at all**, two
paragraphs, and its entire body is one screen display at L170 — dropped per §11.1 — and one `SORT` at
**L172-L178**, `on ascending key sort-batch sort-ac sort-pc sort-post using pre-trans giving
post-trans`. It contains **zero `GO TO`**, **zero `MOVE`** and **zero arithmetic verbs**; the three
`compute` matches a naive grep finds are the word "Computers" in the copyright header at L15, L19 and
L57. It copies only `envdiv.cob` L85, `wscall.cob` L155, `wssystem.cob` L156 and `wsnames.cob` L157 —
**no facade copybook**, so it is the one in-scope program that reaches no table.

The four sort keys are a hard contract, not an implementation detail: `gl072` locates each posting's
nominal account with a **sequential** read at `[general/gl072.cbl:L408]` rather than an indexed one,
so it finds the right account only because this sort has already ordered the stream. The Python
equivalent is `acas_posting/cobol/sortverb.py`'s `sort_records`, whose stability is guaranteed and
whose ordering `is_sorted` can assert; `acas_posting/workfiles.py` supplies `sort_using_giving` and
the `GeneralLedgerWorkFiles` pair that stand in for `pretrans.tmp`
`[copybooks/wsnames.cob:L15]` and `postrans.tmp` `[copybooks/wsnames.cob:L16]`. Cross-reference
**A-14**.

One property of that `SORT` is **not** settled by reading it: `[general/gl071.cbl:L172-L178]`
declares no `with duplicates in order` phrase, so the compiled tie order for two records carrying an
identical `(sort-batch, sort-ac, sort-pc, sort-post)` is whatever GnuCOBOL 3.2 chooses. The Python
sort is stable unconditionally, which may or may not agree. Under R-6 that was a question for the
oracle rather than something to settle here, and the oracle has **answered** it:
**`Q-SORT-TIE-ORDER`** in `ambiguity-resolutions.md` is **`RESOLVED BY ORACLE`** (2026-08-07) — the
compiled sort **preserves input order** for equal keys, which is exactly what an unconditionally
stable sort produces, so the two implementations agree. The measured ordering is asserted as a fact
under the companion key **`Q-SORT-TIE-ORDER-ANSWER`**; it is recorded here rather than settled here,
because the register remains the single place a resolution is declared.

#### `general/gl072.cbl` → `gl072_transaction_update.py`

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `gl072-Main` § | `[general/gl072.cbl:L268]` | `_gl072_main` | — |
| `loop.` | `L283` | `_loop` | L289 **C2** → `end-run`; L292, L307, L341 **C1** → `loop` |
| `headings.` | `L343` | `_headings` | L349 **C2** → `headings-end` |
| `headings-end.` | `L369` | `_headings_end` | — |
| `end-batch.` | `L372` | `_end_batch` | — |
| `end-account.` | `L379` | `_end_account` | — |
| `new-account.` | `L402` | `_new_account` | — |
| `end-run.` | `L437` | `_end_run` | — |
| `main-exit.` | `L445` | `_gl072_main_main_exit` | — (`goback.` L446) |
| `get-batch` § | `L448` | `_get_batch` | — |
| `main-exit.   exit.` | `L464` | `_get_batch_main_exit` | — |
| `zz070-Convert-Date` § | `L467` | `_zz070_convert_date` | L480, L485 **C3** → `zz070-Exit` |
| `zz070-Exit.` | `L494` | `_zz070_exit` | — |

**`headings-end.` at L369 is an empty label** — there is no statement between it and `end-batch.`
at L372. It exists solely as the terminus of `perform headings through headings-end` (§9.5). The
Python module keeps `_headings_end` as a real function anyway, because C-4 fixes the function boundary
at the paragraph boundary; deleting it would make the `through` transformation unverifiable.

**`end-account` is performed before `end-batch`, while being declared after it.** The at-end phrase
does `perform end-account` L287 then `perform end-batch` L288 then `go to end-run` L289; the
batch-change phrase does the same pair at L297-L298. Yet `end-batch.` is declared at L372 and
`end-account.` at L379. Source order and call order disagree, and inverting the calls would stamp a
batch cleared — `move 1 to cleared-status` L375, `move run-date to posted` L376,
`perform GL-Batch-Rewrite` L377 — with its final account still unclosed.

#### `general/gl080.cbl` → `gl080_end_of_cycle.py`

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `gl080-Main` § | `[general/gl080.cbl:L275]` | `_gl080_main` | L313, L326, L332 **C2** → `main-end` |
| `loop.` | `L339` | `_gl080_main_loop` | L344 **C2** → `loop-end`; L349 **C1** → `loop` |
| `loop-end.` | `L351` | `_gl080_main_loop_end` | — |
| `main-end.` | `L365` | `_main_end` | — (`goback.` L366) |
| `gl080a` § | `L368` | `_gl080a` | — |
| `loop.` | `L374` | `_gl080a_loop` | L379 **C2** → `end-run`; L382, L388 **C1** → `loop` |
| `end-run.` | `L390` | `_gl080a_end_run` | — |
| `main-exit.   exit section.` | `L395` | `_gl080a_main_exit` | — |
| `gl080b` § | `L398` | `_gl080b` | L409 **C3** → `main-exit` |
| `loop.` | `L417` | `_gl080b_loop` | L422 **C2** → `end-run`; L425, L434 **C1** → `loop` |
| `end-run.` | `L436` | `_gl080b_end_run` | — |
| `main-exit.   exit section.` | `L442` | `_gl080b_main_exit` | — |
| `arc-process` § | `L445` | `_arc_process` | — |
| `loop.` | `L452` | `_arc_process_loop` | L457 **C3** → `main-exit`; L461 **C1** → `loop`; L499 **C2** → `by-pass` |
| `by-pass.` | `L510` | `_arc_process_by_pass` | L514 **C1** → `loop` |
| `main-exit.   exit section.` | `L516` | `_arc_process_main_exit` | — |
| `disk-change` § | `L519` | `_disk_change` | — |
| `accept-option.` | `L542` | `_disk_change_accept_option` | L547 **C3** → `main-exit`; L549, L557 **C1** → `accept-option` (an interactive retry; see §11.5) |
| `main-exit.   exit section.` | `L559` | `_disk_change_main_exit` | — |
| `gl080c` § | `L562` | `_gl080c` | — |
| `loop.` | `L572` | `_gl080c_loop` | L577 **C2** → `end-run`; L580, L590 **C1** → `loop` |
| `end-run.` | `L592` | `_gl080c_end_run` | — |
| `main-exit.   exit section.` | `L597` | `_gl080c_main_exit` | — |
| `del-process` § | `L600` | `_del_process` | — |
| `loop.` | `L609` | `_del_process_loop` | L614 **C3** → `main-exit`; L618, L623 **C1** → `loop` |
| `main-exit.   exit section.` | `L625` | `_del_process_main_exit` | — |
| `compress-post` § | `L628` | `_compress_post` | L634 **C3** → `main-exit` |
| `Test-Work-File-Size-1.` | `L639` | `_compress_post_test_work_file_size_1` | — |
| `loop1.` | `L654` | `_compress_post_loop1` | L659 **C2** → `loop1-end`; L661, L664 **C4** → `file-error`; L665 **C1** → `loop1` |
| `loop1-end.` | `L667` | `_compress_post_loop1_end` | — |
| `loop2.` | `L675` | `_compress_post_loop2` | L679 **C2** → `loop2-end`; L681, L685 **C4** → `file-error`; L686 **C1** → `loop2` |
| `file-error.` | `L688` | `_compress_post_file_error` | — |
| `loop2-end.` | `L699` | `_compress_post_loop2_end` | — |
| `main-exit.` | `L705` | `_compress_post_main_exit` | — |
| `Evaluate-Message` § | `L710` | `_evaluate_message` | — (exit `Eval-Msg-Exit.   exit section.` L716 → `_eval_msg_exit`) |
| `zz070-Convert-Date` § | `L719` | `_zz070_convert_date` | L732, L737 **C3** → `zz070-Exit` |
| `zz070-Exit.` | `L746` | `_zz070_exit` | — |

`gl080` is where the end-of-period arithmetic lives, and two sites are cited because Table 2 has to
locate them: the `ROUNDED` cycle divide `divide scycle by period giving a rounded.` at
`[general/gl080.cbl:L328]` and the multiply that immediately checks it,
`multiply a by period giving y.` at `[general/gl080.cbl:L329]`; then the **unbounded** subscript
`move ledger-balance to ledger-q (a).` at `[general/gl080.cbl:L345]`. The array it indexes has
exactly four elements — `Ledger-Q … occurs 4` at `[copybooks/wsledger.cob:L35-L36]`, surfacing as the
four columns `LEDGER-Q1` … `LEDGER-Q4` at `[mysql/ACASDB.sql:L130-L133]` — which is the precise blast
radius of **A-2**. `[general/gl080.cbl:L355-L357]`, `[general/gl080.cbl:L358-L360]` and
`[general/gl080.cbl:L361-L363]` are the three further rotating counters of **A-3**.

#### `sales/sl055.cbl` → `sl055_invoice_extract_analysis.py`

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `da000-mainline` § | `[sales/sl055.cbl:L305]` | `_da000_mainline` | — |
| `da010-Read-Loop.` | `L364` | `_da010_read_loop` | L368 **C2** → `da040-Close-Files` |
| `da020-Header-Analysis.` | `L426` | `_da020_header_analysis` | L428, L442, L470 **C1** → `da010-Read-Loop`; L431, L436 **C4** → `da030-Skip-Invoice` |
| `da030-Skip-Invoice.` | `L472` | `_da030_skip_invoice` | L478 **C2** → `da040-Close-Files`; L479 **C1** → `da010-Read-Loop` |
| `da040-Close-Files.` | `L481` | `_da040_close_files` | — |
| `da999-Menu-Exit.` | `L520` | `_da999_menu_exit` | — (`goback.` L521) |
| `db000-Create` § | `L527` | `_db000_create` | — |
| `DB000-Create-Main.` | `L530` | `_db000_create_main` | L536 **C4** → `db010-Create-Anal`; L543, L554, L566, L572 **C3** → `db999-Main-Exit` |
| `db010-Create-Anal.` | `L574` | `_db010_create_anal` | L585 **C4** → `db000-Create-Main` |
| `db999-Main-Exit.` | `L587` | `_db999_main_exit` | — |
| `dc000-Store-Specials` § | `L590` | `_dc000_store_specials` | L615 **C3** → `dc999-Main-Exit` |
| `dc999-Main-Exit.` | `L623` | `_dc999_main_exit` | — |
| `dd000-Extract` § | `L626` | `_dd000_extract` | L633 **C3** → `dd999-Main-Ex` |
| `dd999-Main-Ex.` | `L691` | `_dd999_main_ex` | — |
| `zz070-Convert-Date` § | `L694` | `_zz070_convert_date` | L707, L712 **C3** → `zz070-Exit` |
| `zz070-Exit.` | `L721` | `_zz070_exit` | — |
| `a01-Eval-Status` § | `L724` | `_a01_eval_status` | — (exit `a01-exit.   exit section.` L729 → `_a01_exit`) |

The section at L590 is **`dc000-Store-Specials`**, not merely the exit label the plan's inventory
names; the AAP §0.4.2 entry lists only `dc999-Main-Exit` L623 and so hides the section header.
`sl055` carries **only** `zz070-Convert-Date` of the four shared date sections — no `zz050`, no
`zz060`, no wrapper — and it sets `ws-term-code` to 8 at `[sales/sl055.cbl:L344]`.

#### `sales/sl060.cbl` → `sl060_invoice_posting.py`

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `aa000-Main-Process` § | `[sales/sl060.cbl:L402]` | `_aa000_main_process` | — |
| `aa020-Read-Loop.` | `L483` | `_aa020_read_loop` | L485 **C2** → `aa030-Main-End`; L610 **C1** → `aa020-Read-Loop` |
| `aa030-Main-End.` | `L612` | `_aa030_main_end` | — |
| `aa040-End-Loop.` | `L661` | `_aa040_end_loop` | L664 **C2** → `aa050-End-Loop-End`; L669, L674 **C1** → `aa040-End-Loop` |
| `aa050-End-Loop-End.` | `L676` | `_aa050_end_loop_end` | — |
| `aa999-Exit-Prog.` | `L722` | `_aa999_exit_prog` | — |
| `ba000-Cr-Swop` § | `L725` | `_ba000_cr_swop` | — |
| `main-exit.` | `L763` | `_ba000_cr_swop__main_exit` | — |
| `ba000-New-Heading` § | `L766` | `_ba000_new_heading` | — |
| `main-exit.` | `L789` | `_ba000_new_heading__main_exit` | — |
| `ba000-Headings` § | `L792` | `_ba000_headings` | — |
| `main-exit.` | `L813` | `_ba000_headings__main_exit` | — |
| `ba000-Sales-Comp` § | `L816` | `_ba000_sales_comp` | — |
| `main-exit.` | `L829` | `_ba000_sales_comp__main_exit` | — |
| `ba000-Credit-Comp` § | `L832` | `_ba000_credit_comp` | — |
| `main-exit.` | `L845` | `_ba000_credit_comp__main_exit` | — |
| `ba000-CR-Notes` § | `L848` | `_ba000_cr_notes` | L858 **C2** → `ba020-end-loop` |
| `ba010-read-loop.` | `L864` | `_ba010_read_loop` | L869, L876 **C2** → `ba020-end-loop`; L873, L878, L893 **C1** → `ba010-read-loop` |
| `ba020-end-loop.` | `L895` | `_ba020_end_loop` | L900, L907 **C2** → `ba030-main-end`; L908 **C1** → `ba010-read-loop` |
| `ba030-main-end.` | `L910` | `_ba030_main_end` | — |
| `ba040-main-exit.` | `L915` | `_ba040_main_exit` | — |
| `ba000-Apportion` § | `L918` | `_ba000_apportion` | L928 **C4** → `ba000-Main-Rewrite` |
| `ba000-Main-Rewrite.` | `L960` | `_ba000_main_rewrite` | — (`exit section.` L963) |
| `ba000-Clear-Invoice-Deduct.` | `L965` | `_ba000_clear_invoice_deduct` | — |
| `ba000-cid-exit.` | `L971` | `_ba000_cid_exit` | — |
| `main-exit.` | `L973` | `_ba000_apportion__main_exit` | — |
| `ba000-Analise-Deductions` § | `L976` | `_ba000_analise_deductions` | — |
| `ba999-main-exit.` | `L1004` | `_ba999_main_exit` | — |
| `ca000-BL-Open` § | `L1007` | `_ca000_bl_open` | — |
| `ca997-main-exit.` | `L1055` | `_ca997_main_exit` | — |
| `ca000-BL-Write` § | `L1058` | `_ca000_bl_write` | — |
| `ca998-main-exit.` | `L1155` | `_ca998_main_exit` | — |
| `ca000-BL-Close` § | `L1158` | `_ca000_bl_close` | — |
| `ca999-main-exit.` | `L1180` | `_ca999_main_exit` | — (`exit section.` L1181) |
| `zz040-Evaluate-Message` § | `L1183` | `_zz040_evaluate_message` | — (exit `Eval-Msg-Exit.   exit section.` L1189 → `_eval_msg_exit`) |
| `zz050-Validate-Date` § | `L1192` | `_zz050_validate_date` | L1205, L1210 **C1** → `zz050-test-date` |
| `zz050-test-date.` | `L1219` | `_zz050_test_date` | — |
| `zz050-exit.` | `L1224` | `_zz050_exit` | — |
| `zz060-Convert-Date` § | `L1227` | `_zz060_convert_date` | L1239, L1245, L1250 **C3** → `zz060-Exit` |
| `zz060-Exit.` | `L1259` | `_zz060_exit` | — |
| `zz070-Convert-Date` § | `L1262` | `_zz070_convert_date` | L1275, L1280 **C3** → `zz070-Exit` |
| `zz070-Exit.` | `L1289` | `_zz070_exit` | — |
| `maps04` § | `L1292` | `_maps04` | — |
| `maps04-exit.` | `L1297` | `_maps04_exit` | — |

**`main-exit.` is declared six times in `sl060`** — L763, L789, L813, L829, L845 and L973 — not the
two the Agent Action Plan names (§6, C-28). Six labels, six functions, disambiguated by section
prefix per §9.2 rule 3. `sl060`'s wrapper section is named **`maps04`** at L1292, matching its exit
label `maps04-exit.` at L1297; the naming inconsistency of §11.4 is a General-ledger phenomenon and
does not occur here.

`ca000-BL-Close` is where **A-1** lives: `perform SPL-Posting-Close` at
`[sales/sl060.cbl:L1176]` has **no terminating period**, so the `if IRS-Both-Used or G-L` at L1177
nests inside the `if IRS-Used OR IRS-Both-Used` at L1175 and `perform GL-Posting-Close.` at L1178
never runs in pure-General-ledger mode. The three siblings all carry the period —
`[purchase/pl060.cbl:L1031]`, `[sales/sl100.cbl:L694]`, `[purchase/pl100.cbl:L675]` — which is what
makes it an accident rather than an idiom. The unexplained `move RRN to postings.  *> Why ?` of
**A-17** is at `[sales/sl060.cbl:L1173]`, with siblings at `[purchase/pl060.cbl:L1028]`,
`[sales/sl100.cbl:L691]` and `[purchase/pl100.cbl:L672]`.

#### `sales/sl100.cbl` → `sl100_cash_posting.py`

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `init01` § | `[sales/sl100.cbl:L279]` | `_init01` | L300 **C3** → `menu-exit` |
| `menu-return.` | `L303` | `_menu_return` | — |
| `acpt-xrply.` | `L310` | `_acpt_xrply` | L317 **C3** → `menu-exit`; L319 **C1** → `acpt-xrply` |
| `loop.` | `L331` | `_loop` | L334 **C2** → `main-end`; L339, L348, L352, L355 **C1** → `loop` |
| `cust-update.` | `L357` | `_cust_update` | L433 **C1** → `loop` |
| `main-end.` | `L435` | `_main_end` | — |
| `menu-exit.` | `L476` | `_menu_exit` | — |
| `headings.` | `L479` | `_headings` | — |
| `compute-sales-pay.` | `L497` | `_compute_sales_pay` | L501 **C3** → `csp-exit` |
| `csp-exit.` | `L516` | `_csp_exit` | — (bare `exit.` L517) |
| `analise-deductions` § | `L519` | `_analise_deductions` | L526, L540 **C3** → `main-exit` (L548) |
| `BL-Open` § | `L550` | `_bl_open` | — (exit L595) |
| `BL-Write` § | `L598` | `_bl_write` | — (exit L676) |
| `BL-Close` § | `L679` | `_bl_close` | — (`main-exit.   exit section.` L698) |
| `Eval-Status` § | `L700` | `_eval_status` | — (exit L706) |
| `zz050-Validate-Date` § | `L708` | `_zz050_validate_date` | L721, L726 **C1** → `zz050-test-date` |
| `zz050-test-date.` | `L735` | `_zz050_test_date` | — |
| `zz050-exit.` | `L740` | `_zz050_exit` | — |
| `zz060-Convert-Date` § | `L743` | `_zz060_convert_date` | L755, L761, L766 **C3** → `zz060-Exit` |
| `zz060-Exit.` | `L775` | `_zz060_exit` | — |
| `zz070-Convert-Date` § | `L778` | `_zz070_convert_date` | L791, L796 **C3** → `zz070-Exit` |
| `zz070-Exit.` | `L805` | `_zz070_exit` | — |
| `maps04` § | `L808` | `_maps04` (with `_date_wrapper` binding it) | — |
| `maps04-exit.` | `L813` | `_maps04_exit` | — |

`[sales/sl100.cbl:L516-L517]` is `csp-exit.` followed by a **bare `exit.`**, not `exit section.`
That is the proof that `compute-sales-pay` is a **paragraph of `init01`** rather than a section of its
own, which in turn is why `perform compute-sales-pay thru csp-exit` at L344 is legal (§9.5).

#### `purchase/pl055.cbl` → `pl055_order_proof_extract.py`

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `mainline` § | `[purchase/pl055.cbl:L246]` | `_mainline` | — |
| `read-loop.` | `L306` | `_read_loop` | L309 **C2** → `close-files`; L312 **C4** → `header-analysis`; L315, L341, L347, L360 **C1** → `read-loop` |
| `header-analysis.` | `L362` | `_header_analysis` | L366, L372, L398 **C1** → `read-loop` |
| `close-files.` | `L400` | `_close_files` | — |
| `menu-exit.` | `L434` | `_menu_exit` | — |
| `create` § | `L441` | `_create` | — |
| `Create-Main.` | `L444` | `_create__create_main` | L450 **C4** → `Create-Anal`; L457, L468, L480, L486 **C3** → `main-exit` |
| `Create-Anal.` | `L488` | `_create__create_anal` | L499 **C4** → `create-Main` |
| `main-exit.` | `L501` | `_create__main_exit` | — |
| `store-specials` § | `L503` | `_store_specials` | L528 **C3** → `main-exit` |
| `main-exit.` | `L536` | `_store_specials__main_exit` | — |
| `extract` § | `L538` | `_extract` | L545 **C3** → `main-exit` |
| `main-exit.` | `L597` | `_extract__main_exit` | — |
| `zz070-Convert-Date` § | `L599` | `_zz070_convert_date` | L612, L617 **C3** → `zz070-Exit` |
| `zz070-Exit.` | `L626` | `_zz070_exit` | — |
| `a01-Eval-Status` § | `L629` | `_a01_eval_status` | — |

Like `sl055`, `pl055` carries **only** `zz070-Convert-Date` of the four date sections, and it sets
`ws-term-code` to 8 at `[purchase/pl055.cbl:L286]`.

#### `purchase/pl060.cbl` → `pl060_order_posting.py`

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `init01` § | `[purchase/pl060.cbl:L347]` | `_init01` | — |
| `acpt-xrply.` | `L362` | `_init01__acpt_xrply` | — |
| `loop.` | `L424` | `_init01__loop` | L426 **C2** → `main-end`; L543 **C1** → `loop` |
| `main-end.` | `L545` | `_init01__main_end` | — |
| `end-loop.` | `L585` | `_init01__end_loop` | L590 **C2** → `end-loop-end`; L595, L600 **C1** → `end-loop` |
| `end-loop-end.` | `L602` | `_init01__end_loop_end` | — |
| `exit-prog.` | `L650` | `_init01__exit_prog` | — |
| `cr-swop` § | `L653` | `_cr_swop` | — (exit L688 → `_cr_swop__main_exit`) |
| `new-heading` § | `L691` | `_new_heading` | — (exit L714 → `_new_heading__main_exit`) |
| `headings` § | `L717` | `_headings` | — (exit L738 → `_headings__main_exit`) |
| `purch-comp` § | `L740` | `_purch_comp` | — (exit L753 → `_purch_comp__main_exit`) |
| `credit-comp` § | `L755` | `_credit_comp` | — (exit L768 → `_credit_comp__main_exit`) |
| `cr-notes` § | `L770` | `_cr_notes` | L780 **C2** → `end-loop` |
| `read-loop.` | `L786` | `_cr_notes__read_loop` | L791, L798 **C2** → `end-loop`; L795, L800, L807 **C1** → `read-loop` |
| `end-loop.` | `L809` | `_cr_notes__end_loop` | L814, L820 **C2** → `main-end`; L821 **C1** → `read-loop` |
| `main-end.` | `L823` | `_cr_notes__main_end` | — (exit L828 → `_cr_notes__main_exit`) |
| `apportion` § | `L831` | `_apportion` | L839 **C4** → `main-rewrite`; L842 **C3** → `main-exit` (L875) |
| `main-rewrite.` | `L867` | `_apportion__main_rewrite` | — |
| `BL-Open` § | `L877` | `_bl_open` | — (exit L923 → `_bl_open__main_exit`) |
| `BL-Write` § | `L926` | `_bl_write` | — (exit L1010 → `_bl_write__main_exit`) |
| `BL-Close` § | `L1013` | `_bl_close` | — (`main-exit.   exit section.` L1035) |
| `Evaluate-Message` § | `L1037` | `_evaluate_message` | — (exit `Eval-Msg-Exit.` L1043 → `_evaluate_message__eval_msg_exit`) |
| `zz050-Validate-Date` § | `L1046` | `_zz050_validate_date` | L1059, L1064 **C1** → `zz050-test-date` |
| `zz050-test-date.` | `L1073` | `_zz050_validate_date__zz050_test_date` | — |
| `zz050-exit.` | `L1078` | `_zz050_validate_date__zz050_exit` | — |
| `zz060-Convert-Date` § | `L1081` | `_zz060_convert_date` | L1093, L1099, L1104 **C3** → `zz060-Exit` |
| `zz060-Exit.` | `L1113` | `_zz060_convert_date__zz060_exit` | — |
| `zz070-Convert-Date` § | `L1116` | `_zz070_convert_date` | L1129, L1134 **C3** → `zz070-Exit` |
| `zz070-Exit.` | `L1143` | `_zz070_convert_date__zz070_exit` | — |
| `maps04` § | `L1146` | `_maps04` | — |
| `maps04-exit.` | `L1151` | `_maps04__maps04_exit` | — |

#### `purchase/pl100.cbl` → `pl100_payment_posting.py`

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `init01` § | `[purchase/pl100.cbl:L272]` | `_init01` | L293 **C3** → `menu-exit` |
| `menu-return.` | `L296` | `_init01__menu_return` | — |
| `acpt-xrply.` | `L302` | `_init01__acpt_xrply` | L309 **C3** → `menu-exit`; L311 **C1** → `acpt-xrply` |
| `loop.` | `L323` | `_init01__loop` | L326 **C2** → `main-end`; L331, L340, L344, L347 **C1** → `loop` |
| `cust-update.` | `L349` | `_init01__cust_update` | L425 **C1** → `loop` |
| `main-end.` | `L427` | `_init01__main_end` | — |
| `menu-exit.` | `L467` | `_init01__menu_exit` | — |
| `headings.` | `L470` | `_init01__headings` | — |
| `compute-purch-pay.` | `L488` | `_init01__compute_purch_pay` | L492 **C3** → `csp-exit` |
| `csp-exit.` | `L507` | `_init01__csp_exit` | — |
| `analise-deductions` § | `L510` | `_analise_deductions` | L517, L531 **C3** → `main-exit` (L539) |
| `bl-open` § | `L541` | `_bl_open` | — (exit L574 → `_bl_open__main_exit`) |
| `bl-write` § | `L577` | `_bl_write` | — (exit L657 → `_bl_write__main_exit`) |
| `bl-close` § | `L660` | `_bl_close` | — (`main-exit.   exit section.` L679) |
| `Eval-Status` § | `L681` | `_eval_status` | — (exit L687 → `_eval_status__main_exit`) |
| `zz050-Validate-Date` § | `L689` | `_zz050_validate_date` | L702, L707 **C1** → `zz050-test-date` |
| `zz050-test-date.` | `L716` | `_zz050_test_date` | — |
| `zz050-exit.` | `L721` | `_zz050_exit` | — |
| `zz060-Convert-Date` § | `L724` | `_zz060_convert_date` | L736, L742, L747 **C3** → `zz060-Exit` |
| `zz060-Exit.` | `L756` | `_zz060_exit` | — |
| `zz070-Convert-Date` § | `L759` | `_zz070_convert_date` | L772, L777 **C3** → `zz070-Exit` |
| `zz070-Exit.` | `L786` | `_zz070_exit` | — |
| `maps04` § | `L789` | `_maps04` (with `_maps04_wrapper`) | — |
| `maps04-exit.` | `L794` | `_maps04_exit` | — |

#### `irs/irs030.cbl` → `irs030_posting.py` (in-scope portion)

| COBOL paragraph | Locator | Python function | `GO TO` sites and class |
| --- | --- | --- | --- |
| `Net` § | `[irs/irs030.cbl:L1544]` | `_net_section` | — |
| `Main-Exita.` | `L1553` | `_net_main_exita` | — (bare `exit.` L1554) |
| `Gross` § | `L1556` | `_gross_section` | — |
| `Main-Exitb.` | `L1566` | `_gross_main_exitb` | — (bare `exit.` L1567) |
| `Ledger-Postings-Add` § | `L1569` | `_ledger_postings_add` | L1581, L1601, L1611 **C3** → `main99-exit` — **all three bypass `EOJ`** |
| `Input-Loop.` | `L1619` | `_input_loop` | L1622 **C2** → `EOJ`; L1634, L1652, L1683, L1700 **C1** → `Input-Loop`; L1678 **C2** → `EOJ` |
| `EOJ.` | `L1702` | `_eoj` | — |
| `EOJ-q1.` | `L1715` | `_eoj_q1` | L1719 **C1** → `EOJ-q1` (an interactive retry; see §11.5) |
| `main99-exit.` | `L1729` | `_main99_exit` | — (`exit     section.` L1730) |

`Net` and `Gross` end with a **bare `exit.`** at L1554 and L1567, not `exit section.`, even though
both are declared as sections. The two exits are kept as `_net_main_exita` and `_gross_main_exitb`
because C-4 fixes the boundary at the paragraph, and their names differ only in a trailing letter —
preserved, not normalised.

### 9.4 The Class-4 equivalence argument, worked in full

Class 4 is the only class where the transformation is not determined by the class alone, so one site
is walked end to end and every other Class-4 site is annotated by analogy to it. The chosen site is
the strongest in the in-scope set because its target's own transfer is a `goback`.

**The site.** `copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob` contains five `go to Open-Error-Continued`
statements, at `L324`, `L331`, `L338`, `L345` and `L352` — one in each of the five per-handler error
checks.

**What the target does.** `Open-Error-Continued.` at `[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355]`
is not a label: it performs real work. It displays `Fs-reply` (L356-L357), `WE-Error` (L358-L359),
`SQL-Err` (L360), `SQL-Msg` (L361) and `SY008` (L362), accepts an acknowledgement (L363), and then
**`goback.` at L364**. A `goback` in a `COPY`-included section returns from the *containing program*,
so control never comes back to the caller's next statement.

**The equivalence argument.** Three facts fix the transformation:

1. The transfer is unconditional once reached, so no branch is lost.
2. The target's own exit is a program return, so nothing after the `go to` in the source paragraph is
   reachable. A Python `return` inside the check function would be *insufficient* — it would resume
   the caller.
3. The five displays have no database effect and the accept only blocks a terminal, so §11.1 and
   §11.5 apply to them: the displays become log records and the accept is dropped. **The control
   transfer is preserved; only the pause is removed.**

**Therefore** the Python equivalent is: call the handler's close function, then raise the shared
abort. `acas_posting/dal/facade.py` implements exactly that — the five checks are
`acas000_check_4_errors` (L5504), `acas008_check_4_errors` (L5521), `irsub1_check_4_errors` (L5538),
`irsub3_check_4_errors` (L5554) and `irsub5_check_4_errors` (L5570), and each ends by delegating to
`open_error_continued` (L5598), whose return type is annotated **`NoReturn`**. The type annotation
*is* the equivalence proof, checkable by a tool rather than by a reader: a function that cannot
return cannot be mistaken for one that resumes its caller.

**Annotating the other Class-4 sites by analogy.** Each site is classified by where its target's own
transfer goes:

| Target's own exit | Python after the call | Sites |
| --- | --- | --- |
| back to the loop head | `continue` | `next-1` `[general/gl070.cbl:L366]`, `L371`, `L376` — `next-1.` L382 falls through to `screen-option.` L418, whose `go to loop` at L427 re-enters the loop; `da030-Skip-Invoice` `[sales/sl055.cbl:L431]`, `L436` — its own L470/L479 return to `da010-Read-Loop`; `header-analysis` `[purchase/pl055.cbl:L312]` — its own L360/L366/L372/L398 return to `read-loop` |
| the section's exit label | `return` | `Create-Anal` `[purchase/pl055.cbl:L450]` and `create-Main` `[purchase/pl055.cbl:L499]` — a mutual pair whose members both reach `main-exit.` L501; `db010-Create-Anal` `[sales/sl055.cbl:L536]` and `db000-Create-Main` `[sales/sl055.cbl:L585]` — the Sales twin of the same pair |
| the section's exit label, via `exit section.` | `return` | `ba000-Main-Rewrite` `[sales/sl060.cbl:L928]` — the target at L960 ends `exit section.` L963; `main-rewrite` `[purchase/pl060.cbl:L839]` — the Purchase twin at L867 |
| a shared error paragraph that then re-enters the loop | call, then `continue` | `file-error` `[general/gl080.cbl:L661]`, `L664`, `L681`, `L685` — the target at L688 is reached from both `loop1` and `loop2` |
| a program return | raise the shared abort | the five `Open-Error-Continued` sites above |

Two of those rows are **mutually re-dispatching pairs** — `Create-Main` ⇄ `Create-Anal` in `pl055`
and `DB000-Create-Main` ⇄ `db010-Create-Anal` in `sl055` — where each paragraph can transfer to the
other. Mutual recursion is *not* a faithful rendering, because COBOL's transfer does not stack a
return address. The sibling modules keep the two as separate functions, `_create__create_main` /
`_create__create_anal` and `_db000_create_main` / `_db010_create_anal`, and drive the alternation from
the enclosing section function, so no frame accumulates. Where the *number of alternations* a given
input produces cannot be settled by reading, it is a question for the oracle rather than for this
document, and is cross-referenced as a `Q-` entry in `ambiguity-resolutions.md` (§18) rather than
asserted here.

### 9.5 `PERFORM … THROUGH` and `PERFORM … THRU` — individually hand-verified

**The construct appears in two spellings, and a search for `THRU` alone misses `gl072` entirely.**
AAP §0.6.3 requires each site be hand-verified with no pattern-matching shortcut; that is why the
count is given three ways, with the arithmetic shown.

| # | Site | Spelling | Range performed | Inside a migration boundary? |
| --- | --- | --- | --- | --- |
| 1 | `[general/gl051.cbl:L504]` | `through` | `help-outline` L764 → `h-o-data` L782 | **No** — the site is in `gl050c` §496, out of scope |
| 2 | `[general/gl051.cbl:L955]` | `through` | `help-outline` L764 → `h-o-data` L782 | **No** — the site is in `batch-amendment` §825, out of scope |
| 3 | `[general/gl072.cbl:L300]` | `through` | `headings` L343 → `headings-end` L369 | **Yes** |
| 4 | `[general/gl072.cbl:L304]` | `through` | `headings` L343 → `headings-end` L369 | **Yes** |
| 5 | `[sales/sl100.cbl:L344]` | `thru` | `compute-sales-pay` L497 → `csp-exit` L516 | **Yes** |
| 6 | `[purchase/pl100.cbl:L336]` | `thru` | `compute-purch-pay` L488 → `csp-exit` L507 | **Yes** |
| 7 | `[irs/irs030.cbl:L813]` | `thru` | `End-Batch` L1170 → `Batch-Close` L1213 | **No** — the site is in `Init-Main` §557, out of scope |
| 8 | `[irs/irs030.cbl:L831]` | `thru` | `End-Batch` L1170 → `Batch-Close` L1213 | **No** — as above |
| 9 | `[irs/irs030.cbl:L832]` | `thru` | `Get-Default` L607 → `Set-Up` L778 | **No** — as above |

**Nine** live sites across the twelve files. Three further `thru` matches in `irs030` — at L1059,
L1305 and L1306 — are comments and are not statements. **Four** sites fall inside a migration
boundary, and they are #3 to #6. **Zero** fall inside either partial program's boundary, because
`gl051`'s two sit outside `batch-print` and `irs030`'s three sit inside the out-of-scope `Init-Main`.

The transformation of #3 and #4 is worth stating because the range terminates on an empty label: the
Python is a call to `_headings` followed by a call to `_headings_end`, with `_headings_end`'s body
empty. The `go to headings-end` at `[general/gl072.cbl:L349]` — Class 2 — is the reason the range
exists at all: it lets `headings` abandon its own body on `we-error = 999` while the `perform` still
completes normally. Collapsing the range to a single call to `_headings` would silently change what
that Class-2 transfer means.

The transformation of #5 and #6 is a call to `_compute_sales_pay` / `_init01__compute_purch_pay`
followed by a call to `_csp_exit` / `_init01__csp_exit`; the `go to csp-exit` at
`[sales/sl100.cbl:L501]` and `[purchase/pl100.cbl:L492]` — Class 3 — becomes a `return` from the
first of the pair.

### 9.6 Duplicate and variant labels that remain distinct functions

R-4 forbids tidying these. Each row is a name the frozen source uses more than once, or uses in a
form that differs from its siblings, and in every case the Python keeps them apart.

| Program or copybook | The names | Verified locators |
| --- | --- | --- |
| `sales/sl060.cbl` | `main-exit.` **six times** | L763, L789, L813, L829, L845, L973 |
| `general/gl051.cbl` | `get-description.` **twice**, in different sections | L799 (`gl050c`), L1136 (`batch-print`) |
| `irs/irs030.cbl` | `Input-Loop.` **twice**, one in scope and one not | L797 (`Init-Main`), L1619 (`Ledger-Postings-Add`) |
| `irs/irs030.cbl` | `Main-Exit.` **three times**, plus two single-letter variants | L1230, L1281, L1397, and `Main-Exita.` L1553 / `Main-Exitb.` L1566 |
| `common/acas008.cbl` | two **differently named** exits, referenced in **three** casings | declared `aa999-main-exit.` L496 and `aa-main-exit.` L501; referenced as `aa999-main-exit`, `aa999-Main-Exit` (L389, L408) and `AA-Main-Exit` (L318, L326) |
| `copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob` | `ReWrite` with a capital W | `acasirsub3-ReWrite.` L250, `acasirsub5-ReWrite.` L314, against `acas008-Rewrite.` L163 |
| the four Sales and Purchase posting programs | the closing exit label differs | `sl060` `ca999-main-exit.` L1180 with `exit section.` on its **own line** L1181, against a **single-line** `main-exit.   exit section.` at `pl060` L1035, `sl100` L698 and `pl100` L679 |
| `sales/sl100.cbl` | a **bare** `exit.` | L517, proving `compute-sales-pay` is a paragraph, not a section |
| `irs/irs030.cbl` | two **bare** `exit.` statements closing declared sections | L1554, L1567 |

### 9.7 The four shared date sections, and the one place consolidation is safe

Four sections — `zz050-Validate-Date`, `zz060-Convert-Date`, `zz070-Convert-Date` and the wrapper
around the date module — recur near-identically across the in-scope programs. AAP §0.6.3 permits
consolidating them, on the specific ground that their bodies are textually equivalent, and
`acas_posting/dates.py` is where they land: it publishes `zz050_validate_date`, `zz050_test_date`,
`zz060_convert_date`, `zz070_convert_date`, `maps03`, `maps04`, `ws_unpack`, `test_date_yyyymmdd`,
`integer_of_date`, `date_of_integer`, the three `date_form_is_*` predicates, and one program-specific
variant, `zz050_validate_date_gl051`.

Traceability is preserved on both sides of that consolidation:

- **Each program keeps its own named function** for each date section it declares — the per-program
  tables above give them — and that function delegates to the consolidated body. The section name is
  therefore still resolvable from either direction.
- **The distribution is not uniform, and the tables record the actual distribution.** `sl055` and
  `pl055` declare only `zz070-Convert-Date`; `gl070`, `gl072` and `gl080` declare no `zz050` at all;
  `gl051`, `gl070`, `gl072`, `gl080`, `sl055` and `pl055` declare no `maps04` wrapper under that
  name. Only `sl060`, `sl100`, `pl060` and `pl100` declare all four.
- **`gl051` is the exception that required a variant.** Its `zz050-Validate-Date` §1169 differs
  enough from the others that `dates.py` publishes `zz050_validate_date_gl051` separately rather than
  forcing one body to serve both. That is consolidation stopping exactly where equivalence stops. Note
  that `gl051`'s own module imports **neither** that variant nor `zz070_convert_date`, because its
  `zz050` is performed only from `gl050c` §496 and its `zz070` only from `gl050d` §961 — both out of
  scope per §7.1 — so the in-scope portion reaches only `maps03` and `zz060_convert_date`. The variant
  remains published for the carriers that do reach it.
- **`maps03` and `maps04` are the same wrapper under two names.** `gl051` §1273 and `gl070` §603
  perform one named `maps03`; `sl060` §1292, `sl100` §808, `pl060` §1146 and `pl100` §789 perform one
  named `maps04`. `dates.py` publishes both names over one body, which is the §12 dual-alias principle
  applied to the date layer rather than to the facade.
- **Trailing exit labels of the consolidated sections** are realised as the helper's `return` in some
  modules and as a separate function in others — `gl072` keeps `_zz070_exit`, `gl070` does not. The
  per-program tables state which, per §9.2 rule 4, so no reader is sent looking for a function that
  is not there.

The specification the consolidated body reproduces is `common/maps04.cbl`: the six-part reject test at
`[common/maps04.cbl:L140-L146]`, the calendar validity test at `[common/maps04.cbl:L153-L154]`, and
the ordinal conversion `move FUNCTION integer-of-Date (Test-Date9) to A-Bin.` at
`[common/maps04.cbl:L167]`. Neither reject path writes the output field, which contradicts the
maintainer's own remark at `[common/maps04.cbl:L163]` that errors return zero; the contract holds only
because the known caller pre-zeroes at `[copybooks/Proc-ACAS-Mapser-RDB.cob:L78]`. Cross-reference
**A-16**.

---

## 10. Table 3 — field → dictionary entry

### 10.1 The authority

The preserved user statement of AAP §0.8.2 heads this table because it decides where every field's
metadata comes from. Quoted verbatim:

> *"The maintainer's one-way COBOL-to-MySQL bridge defines the authoritative record-layout ↔ table mapping — it is the data dictionary for this migration."*

The ordering that follows from it is a directive, not a preference. AAP §0.8.1, under **"Data
dictionary first"**: *"This ordering is a directive, not a preference — it is what prevents fields
being transcribed by eye."* And AAP §0.3.3 states the payoff: *"Field metadata is therefore derived,
not transcribed, which eliminates an entire class of transcription error across several hundred
fields."*

**The mapping is enumerated in full, entry by entry, in Appendix A of this document** — all **1067**
of them, every dictionary key with its copybook or program-source field, its bridge host variable, its
SQL column, its one-sided state, its drift and derivation, its A- and Q- references, and a locator for
each of the three layers. R-5 requires that *every* field map to a dictionary entry and that the
mapping be *recorded as a document*; counts and worked examples do not discharge "every", so the
enumeration is here rather than described.

**And it is still not transcription by eye, which is the constraint that makes refusing to enumerate
at all so tempting.** That refusal would reason that reproducing several hundred rows in Markdown is
exactly the hand-copying AAP §0.8.1 forbids. It is sound about hand-copying and wrong about the
conclusion: **Appendix A is rendered mechanically from
`data_dictionary/acas_posting_dictionary.json`**, which is itself generated from the frozen copybooks,
the frozen bridges and the frozen schema by `acas_posting/dictionary/generate.py`. Nobody read a
picture clause and typed it into a table. The authority remains the generated artifact — the appendix is
a *rendering* of it, and the artifact stays the thing a program reads — so the property AAP §0.3.3
promises still holds: "field metadata is therefore derived, not transcribed."

**How to check the appendix against its source, without trusting either.** `python -m
acas_posting.dictionary.generate --check` re-derives the JSON from the frozen sources and reports
agreement without writing; the appendix's own row counts and its per-table column counts are then
checkable against that artifact's `coverage` block. If the two ever disagree, the artifact is right and
the appendix is stale.

This section remains the *specification* of what the enumeration contains: what an entry holds, how
many there are, what the source layers are, and how to resolve a field to its entry.

- **The artifact:** `data_dictionary/acas_posting_dictionary.json`, generated and committed.
- **Its schema:** `data_dictionary/acas_posting_dictionary.schema.json`, which validates it.
- **The generator:** `acas_posting/dictionary/generate.py`, which parses the copybooks, the bridges
  and `mysql/ACASDB.sql` and reconciles them. Running it with `--check` re-derives the artifact and
  reports agreement without writing.
- **The runtime accessor:** `acas_posting/dictionary/loader.py`, which publishes `get_entry`,
  `find_entry`, `entries_for_table`, `entries_for_copybook_record`, `entries_for_copybook_file`,
  `copybook_field_for`, `host_variable_for`, `column_for`, `drift_for` and `derivation_for`, so a
  record field cites its entry at run time rather than in a comment.
- **The typed model:** `acas_posting/dictionary/model.py`, which publishes `CopybookField`,
  `BridgeHostVariable`, `MysqlColumn`, `Presence`, `Drift`, `Derivation`, `DictionaryEntry`, and the
  enumerations `Usage`, `SignPosition`, `CobolPythonStorage`, `SqlBaseType` and `DerivationKind`.

Both JSON artifacts exist in this checkout and are additionally planned at these paths by AAP
§0.4.1.6. The record modules are not optional consumers of them: `acas_posting/records/gl_posting.py`,
for example, imports `FieldDescriptor` from `acas_posting.cobol.field` and `loader` from
`acas_posting.dictionary`, and builds its descriptors from the artifact during a normal import.
`pyproject.toml` does **not** ship the dictionary as package data — `include-package-data = false`
and `data_dictionary*` is in the discovery exclusion list — so the artifact is read from the
committed repository sibling, the single entry in `DATA_DICTIONARY_SEARCH_PATH`. A record module
therefore imports only inside a checkout that carries it.

**The run-time half of that claim is now a measured count rather than a description, and it was
one attribute short when it was only a description.** `loader.trace_record` resolves an attribute to
its entry by trying a fixed sequence of routes — field metadata, a class constant, the class's and
then the module's named descriptor maps, position within `FIELDS`, and group membership — so "every
record field cites its entry at run time" holds exactly as far as that sequence reaches. Run across
every record dataclass the package defines, it reaches **976 of 976 attributes**. It previously
reached 975: `SystemDataBlock.filler_81` fell off the end of the sequence, because two ordinary facts
about that record combine badly.

- **The positional route was unavailable.** It requires `FIELDS` and the dataclass fields to be the
  same length, and `SYSTEM-REC` has **46** descriptors against **45** fields — because
  `Scycle REDEFINES Cyclea` `[copybooks/wssystem.cob:L62-L63]` is one storage location with two COBOL
  names, correctly modelled as one field plus a `scycle` property. The record is right; the count
  mismatch is a consequence of it being right.
- **No name route could match.** The descriptor's COBOL name is the bare `FILLER`
  `[copybooks/wssystem.cob:L81]`, and `FILLER` is not unique in that copybook, so the Python
  attribute has to carry the line number to be a distinct name — after which `filler_81` equals no
  form of `FILLER`.

The field now states its key outright, which is the loader's **first** route, and takes it from the
module's own key index rather than as a literal so that a wrong name or line fails at import with a
`KeyError` naming the pair. The entry it reaches is `System-Record.FILLER#81`, row 300 of Appendix A.
`tests/arithmetic/test_pic_field_descriptors.py` holds both halves: that **zero** attributes are
unrouted, and that this particular one routes by stated key to that particular entry — the second
assertion being there because the count alone would go green again if the attribute were deleted
rather than routed, and deleting a `FILLER` the frozen record declares would be a change to the
layout rather than a fix.

### 10.2 What one entry contains — the authoritative triple, plus what the triple implies

Every entry is keyed `TABLE-NAME.COLUMN-NAME` and carries four views of one field, so that a reader
starting from any layer arrives at the same entry.

| Member | Contents |
| --- | --- |
| `key`, `table`, `bridge`, `handler`, `entity_facade` | the entry's identity and its position in the entity-to-table spine of AAP §0.2.1.1 |
| `presence`, `one_sided` | which of the four layers declare this field, and whether any of them does not |
| `copybook` | file, `path:line` locator, name, level, picture, usage, `usage_declared_at`, `usage_inherited_from`, signed, `sign_position`, `sign_clause_text`, digits, `integer_digits`, scale, `character_length`, `redefines`, `occurs`, `is_filler`, `is_group`, `parent_group`, `condition_names` |
| `program_source` | the same shape, for the work-file records declared in a program rather than a copybook |
| `bridge_host_variable` | file, locator, `hv_group_name`, `hv_group_suffix`, name, picture, usage, signed, digits, scale, `character_length`, `loaded_from_record` with its `load_source`, `unloaded_to_record` with its `unload_source`, and `group_initialised_before_load` |
| `column` | file, locator, name, `sql_type`, `base_type`, `display_width`, scale, `unsigned` |
| `drift`, `derivation`, `cobol_python_storage` | where the three layers disagree; how a bridge-only column is computed; and which Python storage class carries the value |
| `notes`, `anomaly_refs`, `ambiguity_refs` | prose, plus the `A-` and `Q-` identifiers that connect the entry to [`anomaly-log.md`](anomaly-log.md) and to `ambiguity-resolutions.md` |

**R-2 is satisfied structurally by that shape, and the claim is machine-checkable rather than
rhetorical.** Digits, scale, signedness and usage are present at *every* layer of *every* entry,
which is the only way to decide whether a value is exactly representable. Checked over the artifact
in this checkout: of the 1067 entries, the 1007 that declare a `copybook` layer, the 513 that declare
a `bridge_host_variable` layer and the 46 that declare a `program_source` layer **all four properties
are present in every case, with zero omissions**; all 513 `column` members carry `sql_type`, `scale`
and `unsigned`; and the number of columns whose `base_type` is `float`, `double` or `real` is **zero**.
A reader can reproduce that count from `data_dictionary/acas_posting_dictionary.json` without
consulting this document. Three worked entries, read from the same artifact:

| Entry | Copybook | Bridge host variable | Column | Refs |
| --- | --- | --- | --- | --- |
| `GLLEDGER-REC.LEDGER-NAME` | `Ledger-Name x(24)`, ALPHANUMERIC, length 24 `[copybooks/wsledger.cob:L27]` | `HV-LEDGER-NAME X(32)` `[common/nominalMT.cbl:L299]` | `char(32)` `[mysql/ACASDB.sql:L127]` | A-12 |
| `SALEDGER-REC.SALES-AVERAGE` | `Sales-Average`, BINARY-LONG, **signed** `[copybooks/wssl.cob:L49]` | `HV-SALES-AVERAGE 9(10) COMP`, **unsigned** `[common/salesMT.cbl:L308]` | `int(8) unsigned` `[mysql/ACASDB.sql:L969]` | A-11 |
| `IRSPOSTING-REC.POST4-DAY` | **absent** — `in_copybook: false`, `one_sided: true` | `HV-POST4-DAY 9(03) COMP` `[common/irspostingMT.cbl:L177]` | `tinyint(2) unsigned` `[mysql/ACASDB.sql:L278]` | A-7 |

### 10.3 The coverage arithmetic

`acas_posting/dictionary/generate.py --check` reports, in this checkout, that the committed artifact
is **unchanged** and that it holds **1067 entries covering 513 columns, 513 host variables, 1007
copybook fields and 46 program-source work-file fields across 22 tables and 20 bridges**. The
artifact's own `coverage` block carries the same figures, and each was reproduced here by parsing the
frozen sources independently:

| Quantity | Value | How it decomposes |
| --- | --- | --- |
| Tables in `mysql/ACASDB.sql` | **33** | **22 in scope + 11 out of scope** |
| Bridges in `common/` | **28** | **20 in scope + 8 out of scope** |
| Columns of the 22 in-scope tables | **513** | see the per-table list in §10.4 |
| Host variables covered | **513** | one per in-scope column |
| Copybook fields covered | **1007** | ENTRIES carrying a copybook view; includes groups, redefines and filler, which have no column |
| Distinct physical copybook declarations covered | **1001** | the DECLARATION population of the 63-file closure, every one of which has at least one entry citing it. Smaller than the row above because an `OCCURS` declaration bound by several columns yields one entry per occurrence and all of them cite the one physical line — publishing both is what makes a missing declaration visible rather than masked, and the generator refuses to emit a document in which any parsed declaration is uncited |
| Program-source work-file fields | **46** | the `pre-trans` / `post-trans` records, declared in `gl070` and `gl071` rather than in a copybook |
| Entries | **1067** | 513 column-anchored plus 554 with no column; every one of the 1067 is enumerated in Appendix A, §A.1 and §A.2 respectively |

`mysql/ACASDB.sql` is **1459** lines. It contains **33** `CREATE TABLE` statements and **33**
`DROP TABLE IF EXISTS` statements — so re-applying the file *is* the drop-and-recreate — together with
**zero** `CREATE DATABASE`, **zero** `USE` (the database name must therefore be supplied on the client
command line) and **zero** `INSERT INTO`. The 22 in-scope tables carry 513 columns, **all** of them
`NOT NULL`, **all 22** with a single-column primary key, and **zero** secondary indexes anywhere.
There are **zero `TIMESTAMP`** columns.

### 10.4 The frozen schema, stated as it is

Three claims about this file are commonly repeated in a form that is wrong. Each is corrected here
so a reader does not have to discover the correction by grepping.

1. **The `ALTER TABLE` hits are all `mysqldump` comments.** A raw search finds **66** of them, which
   invites the conclusion that the schema evolves. It does not: every one is inside a
   `/*!40000 … DISABLE KEYS */` or `/*!40000 … ENABLE KEYS */` conditional-execution comment. Filtering
   comment lines out leaves **zero**. Together with **zero `CREATE INDEX`**, the file contains no
   schema-evolution statement at all — which is what makes the R-3 freeze checkable rather than
   aspirational.
2. **"No column-level `DEFAULT`" is false.** Exactly one exists:
   `` `PASS-WORD` char(4) NOT NULL DEFAULT '' `` at `[mysql/ACASDB.sql:L1219]`, in the in-scope
   `SYSTEM-REC`.
3. **"Zero `AUTO_INCREMENT`" needs qualifying.** The file's only one is
   `` `AUDIT-ID` int(6) unsigned NOT NULL AUTO_INCREMENT `` at `[mysql/ACASDB.sql:L1107]`, in
   `STOCKAUDIT-REC` — an **out-of-scope** table. Zero for the in-scope 22; one for the file. It is one
   more concrete reason the eleven out-of-scope tables must never be dumped: an auto-increment column
   is the one thing in this schema whose value is not a function of the input.

A fourth correction belongs with them, because it is the kind of claim a reader will act on:

4. **`POST-RRN`'s comment is the first, not the only one.** `mysql/ACASDB.sql` carries **fifteen**
   column-level `COMMENT` clauses, at L155, L562, L563, L564, L565, L566, L567, L575, L597, L602,
   L603, L610, L902, L903 and L909. `` `POST-RRN` mediumint(5) unsigned NOT NULL COMMENT 'Rel.
   replacement' `` at `[mysql/ACASDB.sql:L155]` is the first and the most informative — it is the
   schema's record of the same "replace relative processing" change the copybook notes at
   `[copybooks/wspost.cob:L10]` — but a document that called it the only one would be wrong.

**The 22 in-scope tables.** Every locator below was read in this checkout.

| Table | `CREATE` | Columns | Column span | Primary key | PK line |
| --- | --- | --- | --- | --- | --- |
| `ANALYSIS-REC` | L31 | 4 | L32-L35 | `PA-CODE` | L36 |
| `GLBATCH-REC` | L80 | 21 | L81-L101 | `BATCH-KEY` | L102 |
| `GLLEDGER-REC` | L122 | 11 | L123-L133 | `LEDGER-KEY` | L134 |
| `GLPOSTING-REC` | L154 | 14 | L155-L168 | `POST-RRN` | L169 |
| `IRSDFLT-REC` | L189 | 4 | L190-L193 | `DEF-REC-KEY` | L194 |
| `IRSFINAL-REC` | L214 | 3 | L215-L217 | `IRS-FINAL-ACC-REC-KEY` | L218 |
| `IRSNL-REC` | L238 | 15 | L239-L253 | `KEY-1` | L254 |
| `IRSPOSTING-REC` | L274 | 13 | L275-L287 | `KEY-4` | L288 |
| `PSIRSPOST-REC` | L366 | 10 | L367-L376 | `IRS-POST-KEY` | L377 |
| `PUINV-LINES-REC` | L510 | 14 | L511-L524 | `IL-LINE-KEY` | L525 |
| `PUINVOICE-REC` | L545 | 30 | L546-L575 | `PINVOICE-KEY` | L576 |
| `PUITM5-REC` | L596 | 29 | L597-L625 | `OI5-KEY` | L626 |
| `PULEDGER-REC` | L646 | 29 | L647-L675 | `PURCH-KEY` | L676 |
| `SAINV-LINES-REC` | L809 | 14 | L810-L823 | `IL-LINE-KEY` | L824 |
| `SAINVOICE-REC` | L844 | 31 | L845-L875 | `SINVOICE-KEY` | L876 |
| `SAITM3-REC` | L896 | 28 | L897-L924 | `OI3-KEY` | L925 |
| `SALEDGER-REC` | L945 | 37 | L946-L982 | `SALES-KEY` | L983 |
| `SYSDEFLT-REC` | L1138 | 4 | L1139-L1142 | `DEF-REC-KEY` | L1143 |
| `SYSFINAL-REC` | L1163 | 2 | L1164-L1165 | `FINAL-ACC-REC-KEY` | L1166 |
| `SYSTEM-REC` | L1186 | 169 | L1187-L1355 | `SYSTEM-REC-KEY` | L1356 |
| `SYSTOT-REC` | L1376 | 21 | L1377-L1397 | `LEDGER-TOTALS-REC-KEY` | L1398 |
| `VALUEANAL-REC` | L1418 | 10 | L1419-L1428 | `VA-CODE` | L1429 |
| **total** | | **513** | | | |

**Primary-key names are not globally unique**, so a dictionary keyed on the column name alone would
collide. `DEF-REC-KEY` is the primary key of both `IRSDFLT-REC` (L194) and `SYSDEFLT-REC` (L1143);
`IL-LINE-KEY` is the primary key of both `PUINV-LINES-REC` (L525) and `SAINV-LINES-REC` (L824). This
is why every entry key in the artifact is `TABLE.COLUMN` and never `COLUMN`.

The eleven out-of-scope tables are given as a **count and a name list only**, never as mapped fields:
`DELIVERY-REC`, `PLPAY-REC`, `PLPAY-RECrg01`, `PUAUTOGEN-LINES-REC`, `PUAUTOGEN-REC`, `PUDELINV-REC`,
`SAAUTOGEN-LINES-REC`, `SAAUTOGEN-REC`, `SADELINV-REC`, `STOCK-REC`, `STOCKAUDIT-REC`. 22 + 11 = 33.
Likewise the eight out-of-scope bridges, per AAP §0.2.2: `auditMT`, `deliveryMT`, `delfolioMT`,
`sldelinvnosMT`, `stockMT`, `paymentsMT`, `plautogenMT`, `slautogenMT`. 20 + 8 = 28.

**The numeric census, which is R-2's evidence.** There are **zero** `FLOAT`, `DOUBLE` and `REAL`
columns in the whole file, and **zero** `varchar(` against **238** `char(`, so both the numeric and the
character transport are fixed-width and exact.

| Base type | Whole file (720 columns) | In-scope 22 (513 columns) |
| --- | --- | --- |
| `char` | 238 | 177 |
| `decimal` | 167 | 128 |
| `int` | 151 | 65 |
| `tinyint` | 116 | 99 |
| `mediumint` | 23 | 21 |
| `smallint` | 22 | 20 |
| `bigint` | 3 | 3 |

**The decimal scale is not uniformly 2**, so a normaliser that assumed two places would corrupt the
comparison. Whole-file census: 68 × `decimal(9,2)`, 57 × `(10,2)`, 17 × `(4,2)`, 12 × `(5,2)`,
4 × `(14,2)`, 2 × `(2,0)`, 2 × `(14,4)`, and five singletons — `(5,0)`, `(6,2)`, `(10,4)`, `(11,2)`
and `(11,4)`. Restricted to the in-scope 22 the shape narrows usefully: 55 × `(10,2)`, 44 × `(9,2)`,
15 × `(4,2)`, 8 × `(5,2)`, 4 × `(14,2)`, 1 × `(5,0)`, 1 × `(6,2)` — **two distinct scales only, 0 and
2**, and eleven distinct precisions.

### 10.5 The proof that the bridge is authoritative

The authority statement of §10.1 is not a stylistic preference; it is forced by the sources, which
disagree in **three different directions**. All three are worked below, because a migration that
assumed any single direction would be wrong about the other two.

#### 10.5.1 Expansion — the IRS posting table gains three columns that no copybook declares

| Layer | Declaration | Count |
| --- | --- | --- |
| Copybook | `01  Posting-Record.` `[copybooks/irswspost.cob:L8]`, leaves at **L9-L18** | **10** |
| Bridge | `01  TD-IRSPOSTING-REC.` `[common/irspostingMT.cbl:L173]`, host variables at **L174-L186** | **13** |
| Schema | `CREATE TABLE ``IRSPOSTING-REC``` `[mysql/ACASDB.sql:L274]`, columns at **L275-L287** | **13** |

**10 → 13 → 13.** The ten copybook leaves are `Post-Key 9(5)` L9, `Post-Code xx` L10,
`Post-Date x(8)` L11, `Post-DR 9(5)` L12, `Post-CR 9(5)` L13,
`Post-Amount s9(7)v99 sign is leading` **L14**, `Post-Legend x(32)` L15, `Vat-AC-Def 99` L16,
`Post-Vat-Side xx` L17 and `Vat-Amount s9(7)v99 sign is leading` **L18**. The three extra host
variables are `HV-POST4-DAY` **L177**, `HV-POST4-MONTH` **L178** and `HV-POST4-YEAR` **L179**, each
`PIC 9(03) COMP`, surfacing as `POST4-DAY`, `POST4-MONTH` and `POST4-YEAR`, each
`tinyint(2) unsigned NOT NULL`, at **`[mysql/ACASDB.sql:L278-L280]`**.

**The three derived columns sit at ordinals 4, 5 and 6 — interleaved, not appended.** A reader who
assumed new columns are appended would mis-map `POST4-DR` onto `Post-Amount` and every column after
it. The correct correspondence is: ordinals 1-3 to copybook leaves 1-3, ordinals 4-6 to nothing,
ordinals 7-13 to copybook leaves 4-10.

**How the three are derived, and what happens when the derivation fails.** The load paragraph begins
`initialize TD-IRSPOSTING-REC.` at `[common/irspostingMT.cbl:L966]`, stores the raw date text
**unconditionally** at `[common/irspostingMT.cbl:L969]`, and then applies a guarded reference
modification at `[common/irspostingMT.cbl:L982-L987]` — three `if … numeric` tests over
`Post-Date (1:2)`, `Post-Date (4:2)` and `Post-Date (7:2)`, each gating one move. The maintainer's own
comment sits immediately above at `[common/irspostingMT.cbl:L978-L980]` and explains both the date and
the doubt: the columns were added after new ones were created on 31/12/16, and although they *should*
all be numeric because a date is present, the guard is there just in case.

⇒ **When a guard fails the component stays at zero — never `NULL` — while the raw date text is still
stored.** That is why every column in the schema can be declared `NOT NULL`, and why the Python layer
must *default* rather than *omit*. The row that results is internally inconsistent, and it is
reproduced rather than repaired. Cross-reference **A-7**;
`acas_posting/dal/acasirsub4_irs_posting.py` is the reproducing module, and the dictionary entry
records the rule in its `derivation` member with `kind: BRIDGE_DERIVED`, the expression, the guard and
the guard-failure behaviour.

Quoting AAP §0.1.1: *"A migration driven from the copybooks alone would silently omit three columns of
a posting table."*

A usage conversion rides along and must not be lost: `Post-Amount` and `Vat-Amount` are `DISPLAY` with
a **leading sign** in the copybook, become `PIC S9(07)V9(02) COMP` — binary — in the bridge, and land
as `decimal(9,2)` in the schema. Three storage classes for one value, and the sign travels in a
different place in each.

#### 10.5.2 Collapse — the General Ledger posting record loses a field boundary

| Layer | Declaration | Count |
| --- | --- | --- |
| Copybook | `01  WS-Posting-Record.` `[copybooks/wspost.cob:L12]`, leaves at **L13-L28** | **15** |
| Bridge | `01  TD-GLPOSTING-REC.` `[common/glpostingMT.cbl:L281]`, host variables at **L282-L295** | **14** |
| Schema | `CREATE TABLE ``GLPOSTING-REC``` `[mysql/ACASDB.sql:L154]`, columns at **L155-L168** | **14** |

**15 → 14 → 14**, the opposite direction from §10.5.1. The group `WS-Post-Key.` at
`[copybooks/wspost.cob:L14]` holds two five-digit leaves — `Batch` L15 and `Post-Number` L16 — and the
bridge collapses both into a **single** host variable, `HV-POST-KEY PIC 9(18) COMP` at
`[common/glpostingMT.cbl:L283]`, which becomes one column, `POST-KEY bigint(10) unsigned` at
`[mysql/ACASDB.sql:L156]`. A migration that mapped leaf-for-column would produce fifteen columns for a
fourteen-column table.

Two further facts about this triple:

- **`HV-POST-RRN` is declared but never loaded.** It is the first host variable, at
  `[common/glpostingMT.cbl:L282]`, yet the load paragraph — `initialize TD-GLPOSTING-REC.` at
  `[common/glpostingMT.cbl:L1053]`, then thirteen moves at L1054-L1066 — does not touch it. The
  maintainer's rule for why is stated in the source at `[common/glpostingMT.cbl:L1068-L1069]` and
  again, word for word, at `[common/irspostingMT.cbl:L989-L990]`: loading host variables implies a
  non-Fetch action, and record-generated values are handled separately for all such actions, so they
  must not be loaded there. Citing **both** occurrences matters, because one would read as a
  peculiarity of one bridge and two establish it as a convention.
- **The copybook's own byte accounting excludes `WS-Post-rrn`.** The trailing comments run
  `*> 12` at L17 through `*> 96` at L28, and 12 is reached by `WS-Post-Key` (10 bytes) plus
  `Post-Code` (2) — so the five bytes of `WS-Post-rrn` at L13 are outside the count. That is
  consistent with `[copybooks/wspost.cob:L10]` describing it as a later addition "to replace relative
  processing", and with the schema recording the same idea as `POST-RRN`'s `COMMENT 'Rel.
  replacement'` at `[mysql/ACASDB.sql:L155]`. The header's own history at L6-L7 records the record
  going from 98 bytes to 96 when a leading sign was removed.

#### 10.5.3 Drift — width, signedness and name change while the value survives

| Field | Copybook | Bridge | Column | Ref |
| --- | --- | --- | --- | --- |
| Ledger name | `x(24)` `[copybooks/wsledger.cob:L27]` | `X(32)` `[common/nominalMT.cbl:L299]` | `char(32)` `[mysql/ACASDB.sql:L127]` | **A-12** |
| Ledger balance | `s9(8)v99 comp-3` `[copybooks/wsledger.cob:L28]` | `S9(08)V9(02) COMP` `[common/nominalMT.cbl:L300]` | `decimal(10,2)` `[mysql/ACASDB.sql:L128]` | — |
| Sales average | `binary-long`, **signed** `[copybooks/wssl.cob:L49]` | `9(10) COMP`, **unsigned** `[common/salesMT.cbl:L308]` | `int(8) unsigned` `[mysql/ACASDB.sql:L969]` | **A-11** |

- **Width drift** changes padding, not value — and padding is visible in a table dump, which is why
  the harness normaliser canonicalises fixed-character trailing spaces rather than comparing raw
  bytes.
- **Usage drift** changes representation, not value: packed decimal to binary to SQL decimal, with
  digits and scale identical at all three layers. It is nonetheless recorded per field, because the
  Python storage class has to match the layer it is talking to.
- **Signedness drift changes the value**, and it does so **at the bridge, before any SQL runs**. Nine
  signed `binary-long` fields at `[copybooks/wssl.cob:L45-L53]` and two signed `binary-short` fields
  at `[copybooks/wssl.cob:L43-L44]` become eleven unsigned host variables at
  `[common/salesMT.cbl:L302-L312]`. What is actually stored when the value is negative cannot be read
  out of the source — it depends on the conversion the bridge's C interface performs — so it was
  measured instead: **`Q-3` is `RESOLVED BY ORACLE`**, the absolute value being stored and then bounded
  by the receiving digit count, and each entry carries that measurement in its notes.
  `acas_posting/dal/acas012_sales.py` asserts at L357-L370 that all **eleven** columns it narrows
  carry `A-11` in the dictionary, raising at import time if any does not — so the anomaly cannot be
  lost by omission.
- **Name drift** accompanies the others and would defeat a mapping built on name equality:
  `Post-Date` → `HV-POST-DAT` `[common/glpostingMT.cbl:L285]`, `Post-Date` → `HV-POST4-DAT`
  `[common/irspostingMT.cbl:L176]`, `Sales-Create-Date` → `HV-SALES-CREATE-DAT`
  `[common/salesMT.cbl:L312]`, `Post-Key` → `HV-KEY-4` `[common/irspostingMT.cbl:L174]`,
  `Vat-Amount` → `HV-VAT-AMOUNT4` `[common/irspostingMT.cbl:L186]`.

The same collapse-and-drift pattern recurs in the transfer-file record: `wspost-irs.cob` declares
eleven leaves under `01 WS-IRS-Posting-Record.` `[copybooks/wspost-irs.cob:L13]`, with the group
`WS-IRS-Post-Key.` at L14 holding `WS-IRS-Batch` L15 and `WS-IRS-Post-Number` L16, and
`PSIRSPOST-REC` has **ten** columns at `[mysql/ACASDB.sql:L367-L376]` — the group collapsed into
`IRS-POST-KEY bigint(11)`.

### 10.6 The six storage classes, and the census that shows the set is closed

Six numeric storage classes appear in the in-scope record layouts, and the set is closed — which
matters, because R-2 is only enforceable if no seventh class can appear unnoticed.

| # | Class | Python storage | Example |
| --- | --- | --- | --- |
| 1 | `DISPLAY` (zoned decimal, the default) | `Decimal` or `int` per the descriptor | `Post-DR pic 9(5)` `[copybooks/irswspost.cob:L12]` |
| 2 | `COMP` in a picture-declared range | `int` | `Sales-Discount pic 99v99 comp` `[copybooks/wssl.cob:L42]` |
| 3 | `COMP-3` (packed decimal) | `Decimal` | `Ledger-Balance pic s9(8)v99 comp-3` `[copybooks/wsledger.cob:L28]` |
| 4 | `DISPLAY` with a **leading sign** | `Decimal`, sign position modelled | `[copybooks/wspost-irs.cob:L21]`, `[copybooks/irswspost.cob:L14]` |
| 5 | `BINARY-CHAR` / `BINARY-SHORT` / `BINARY-LONG` | `int` — never `Decimal`, never `float` | `Run-Date binary-long` `[copybooks/wssystem.cob:L67]` |
| 6 | group and `REDEFINES` views over the above | the descriptor of the redefining leaf | `Ledger-Q … occurs 4` `[copybooks/wsledger.cob:L35-L36]` |

Class 5 is why the Sales and Purchase statistics fields are Python `int` rather than `Decimal`: their
truncation on divide is *integer* truncation, which is exactly what makes the moving-average defect of
**A-8** reproducible. Getting that one wrong would silently improve the arithmetic.

### The canonical storage census

**THIS IS THE PROJECT'S ONE CANONICAL CENSUS OF THE FROZEN RECORD LAYOUTS, and it is canonical
because two documents used to publish different figures without either stating enough for a reader to
tell which was right.** The scope and the algorithm are therefore given in full, before the numbers.

**The file set: the 187 `copybooks/*.cob` files.** `copybooks/` holds **197** files in total — 187
`*.cob`, 8 `*.cpy`, 1 `*.ws` and 1 `*.pl`. The ten non-`.cob` files are the vendored MySQL, curses and
file-status helpers (`mysql-variables.cpy`, `mysql-procedures.cpy`, `mysql-procedures-2.cpy`,
`MySQL-SQLCA.cpy`, `screenio.cpy`, `FileStat-Msgs.cpy`, `FileStat-Msgs-2.cpy`, `selprint-2.cpy`) plus a
Perl script and a worksheet (`an-accept.pl`, `an-accept.ws`). **None of them is an ACAS record layout**,
which is why the canonical scope is the 187 and not the 197. The 197-file delta is published below
rather than hidden, so a reader who counts differently can reconcile instead of disagreeing.

**The algorithm, stated so the numbers are reproducible.** One regex per clause, applied twice:

- **All lines** — every line of every file, matched case-insensitively. This column includes the
  maintainer's inline annotations, which is why it exceeds the other: many `binary-long` declarations
  carry a `*> 9(8) comp.` note.
- **Code only** — the same regex after dropping (a) every whole-line comment, meaning a line whose
  first non-blank characters are `*>` or whose column 7 is `*`, and (b) any inline `*>` tail from the
  remaining lines.
- **Bare `comp`** means the regex `(?i)\bcomp\b(?!-)` — the token standing alone. This is the one
  definition that has to be spelled out, because `\bcomp\b` on its own also matches `comp-3`,
  `comp-5` and `Comp-Time-Taken`, and subtracting the hyphenated forms from that looser total is how a
  sibling document arrived at a figure this census does not reproduce.

| Clause | All lines | Code only |
| --- | ---: | ---: |
| `comp-3` | 182 | 177 |
| `comp` (bare) | 214 | 144 |
| `binary-long` | 166 | 128 |
| `binary-char` | 84 | 59 |
| `binary-short` | 31 | 30 |
| `occurs` | 107 | 99 |
| `redefines` | 60 | 53 |
| `sign leading` | 4 | 4 |
| `sign is leading` | 2 | 2 |

And **zero** occurrences over the 187, in code or in comment, of every clause that would introduce a
seventh storage class: `comp-1`, `comp-2`, `comp-5`, `binary-double`, `sign trailing`, `sign separate`,
`justified`, blank-when-zero, `PIC A`, and `P` scaling. Zero code-line trailing `V` as well.

**The 197-file delta, in full, so that a wider count is a reconciliation and not a contradiction.**
Widening the scope to every file under `copybooks/` changes exactly six figures, and every one of the
additions comes from the single vendored file `copybooks/mysql-variables.cpy`:

| Clause | 187 `*.cob` | 197 all files | Where the difference comes from |
| --- | ---: | ---: | --- |
| `comp` (bare) | 214 / 144 | **219 / 146** | five more declarations in the vendored MySQL helpers |
| `binary-short` | 31 / 30 | **32 / 31** | one more |
| `occurs` | 107 / 99 | **110 / 102** | three more |
| `redefines` | 60 / 53 | **61 / 54** | one more |
| `comp-5` | 0 / 0 | **4 / 0** | `copybooks/mysql-variables.cpy`, comments only |
| `binary-double` | 0 / 0 | **8 / 8** | `copybooks/mysql-variables.cpy` |

**The `binary-double` row is the one that matters**, and it is the reason the narrower scope is the
right one: a seventh storage class *does* appear once `copybooks/` is read whole, but it appears only in
a vendored MySQL helper that no in-scope record layout uses and no migrated program reaches. The
six-class model of the table above is correct for the ACAS record layouts and would be wrong if stated
over the wider set without this note.

**Where a sibling figure disagrees.** `[docs/migration/ambiguity-resolutions.md]` previously published
bare `comp` as **236** over the 197-file scope, derived as 422 − 182 − 4. That derivation
double-counts: the 422 came from the looser `\bcomp\b`, which matches hyphenated forms this census
excludes by construction. The correct figure for that scope is **219 / 146**, as the delta table above
gives. That document now adopts this census by reference rather than publishing a second one.

**One clause, two spellings, six fields, three files.** `sign leading` appears at
`[copybooks/fdpost-irs.cob:L20]`, `[copybooks/fdpost-irs.cob:L24]`, `[copybooks/wspost-irs.cob:L21]`
and `[copybooks/wspost-irs.cob:L25]`; `sign is leading` appears at `[copybooks/irswspost.cob:L14]`
and `[copybooks/irswspost.cob:L18]`. A parser matching only one spelling would silently treat two
signed fields of the internal IRS posting record as unsigned. `acas_posting/cobol/usage.py` handles
both, and `acas_posting/cobol/picture.py` parses the clause into the `SignPosition` the dictionary
records.

The **width in bytes** of a leading-sign `DISPLAY` item was a second question, carried as
**`Q-5.2`**. Two readings existed: the maintainer's own byte accounting at
`[copybooks/wspost.cob:L6-L7]` — 98 bytes, then 96 "(leading sign removed)" across two fields, so one
byte each — implies digits + 1; the ISO overpunch reading implies digits. Under R-6 the compiled
program decided, and it has: **`Q-5.2`** is **`RESOLVED BY ORACLE`** (2026-08-07) on **Reading B —
the width is `digits`**, an included leading sign spending no byte, which is what
`[acas_posting/cobol/usage.py byte_length]` implements. Reading A, `digits + 1`, is measured **false**.
The descriptor continues to record which reading is in force, now as a confirmed reading rather than a
provisional one.

### 10.7 What is deliberately **not** a column-anchored entry

1007 copybook-view entries exist against 513 columns, so roughly half of the copybook surface
has no column. Those fields are still entries — the artifact marks them `one_sided: true`, **and all
554 of them are enumerated in §A.2 of Appendix A**, grouped by the file that declares them. This
section gives the *reasons* the group exists, so that a reader meeting one of those rows understands
why it has no column instead of reading the blank as an omission:

- **Group items.** `01 WS-Posting-Record.` `[copybooks/wspost.cob:L12]` and `03 WS-Post-Key.` L14 are
  addressable in COBOL but are not columns. The artifact's `is_group` and `parent_group` members carry
  the containment so the tree is still navigable.
- **`REDEFINES` views.** `Ledger-Q … occurs 4` `[copybooks/wsledger.cob:L35-L36]` is a second view of
  the four `Quarters` fields, which are themselves the four `LEDGER-Q` columns. Only one view can be
  a column; both are entries.
- **`FILLER`.** `[copybooks/wsledger.cob:L26]` (`pic x(5)`) and `[copybooks/wsledger.cob:L37]`
  (`pic x(50)`) reach the record but not the table. `is_filler` marks them.
- **Fields the bridge does not load.** `WS-Post-rrn` `[copybooks/wspost.cob:L13]` maps to a column
  that the load paragraph never writes, per §10.5.2.
- **An unqualified leaf named `Batch`.** `[copybooks/wspost.cob:L15]` declares
  `05  Batch       pic 9(5).` inside `WS-Post-Key`, and the name collides across the three posting
  copybooks, which is why `gl070` has to write `post-code in WS-Posting-Record` at
  `[general/gl070.cbl:L497]` and `vat-ac of WS-Posting-Record` at `[general/gl070.cbl:L521]` and
  `[general/gl070.cbl:L525]`. The dictionary keys on `TABLE.COLUMN`, so the collision cannot reach it;
  cross-reference **A-21**.
- **Work-file fields.** The 46 `program_source` fields come from the `pre-trans` / `post-trans`
  records declared inside `gl070` and `gl071` rather than in any copybook. They are transient scratch
  records — `pretrans.tmp` `[copybooks/wsnames.cob:L15]` and `postrans.tmp`
  `[copybooks/wsnames.cob:L16]`, both annotated `*> gl071` by the maintainer — so nothing about them
  reaches the database and nothing about them appears in a table dump. `acas_posting/workfiles.py`
  models them as ordered sequences with the same layout and the same ordering guarantees.

### 10.8 Cursor and key metadata — the fourth thing the bridge is authoritative about

The `.scb` sources carry key metadata that appears in no copybook and in no `CREATE TABLE`, and it is
the specification for `acas_posting/dal/cursor_state.py`. Using `glpostingMT` as the worked example:

| Declaration | Locator | What it fixes |
| --- | --- | --- |
| `01  Table-Of-Keynames.` | `[common/glpostingMT.scb:L231]` | the key table itself |
| `"POST-KEY"` padded to `x(30)` | `L232` | the key's name in the relational store |
| `"00010010"`, annotated `*> offset/length in ws rec` | `L233` | offset 0001, length 0010 — the key's position in the working-storage record |
| `"STR"`, annotated `*> key is string` | `L234` | the key's comparison type |
| `keyOfReference occurs 1 indexed by KOR-x1` | `L237` | **`occurs 1`** — one key of reference, independently corroborating the schema's single-column primary key |
| `01  DAL-Data.` | `L247` | the cursor block |
| `MOST-Relation pic xxx`, annotated `*> valid are >=, <=, <, >, =` | `L248` | a **five-value** relation for `START` |
| `Most-Cursor-Set pic 9 value zero` with `88 Cursor-Not-Active value zero` / `88 Cursor-Active value 1` | `L249-L251` | a **two-state latch** |
| `/MYSQL VAR\` · `BASE=ACASDB` · `TABLE=GLPOSTING-REC,HV` · `/MYSQL-END\` | `L273-L276` | the table directive the preSQL translator consumes — the single place a record group is bound to a table name |

The constraint that shapes the whole emulation is stated in the source, at
`[common/glpostingMT.scb:L243-L245]`: the `START` condition cannot be compounded and must use a key of
reference within the record, *"(These are COBOL rules...)"*. A two-state latch plus a five-value
relation over a single key of reference is therefore the entire cursor model, which is why
`cursor_state.py` publishes `MostRelation`, `CursorSlot`, `KeyOfReference`, `CursorState`,
`SequentialReadStart`, `start`, `read_next`, `read_indexed`, `keys_for`, `key_of_reference` and
`reset`, and nothing more general.

The maintainer's own warning at `[common/glpostingMT.scb:L229]` — that `POST-KEY` may well need
changing to `POST-RRN` with the relational store made to index it — is preserved as a comment in the
same place and acted on nowhere: the schema's primary key is `POST-RRN` `[mysql/ACASDB.sql:L169]`
while the key of reference is `POST-KEY`, and that divergence is part of the specification.

The two vocabularies the cursor model runs on are declared in one copybook, and
`acas_posting/dal/status.py` and `acas_posting/cobol/condition_names.py` publish them between them:
`File-Function pic 99` at `[copybooks/wsfnctn.cob:L88]` with **fifteen** `88`-levels at L89-L105
(`fn-open` 1, `fn-close` 2, `fn-read-next` 3, `fn-read-indexed` 4, `fn-write` 5, `fn-Delete-All` 6,
`fn-re-write` 7, `fn-delete` 8, `fn-start` 9, `fn-Read-Next-Raw` 13, `fn-Write-Raw` 15,
`fn-Read-By-Name` 31, `fn-Read-By-Batch` 32, `fn-Read-By-Cust` 33, `fn-Read-Next-Header` 34), and
`Access-Type pic 9` at `[copybooks/wsfnctn.cob:L107]` with **nine** at L108-L116 (`fn-input` 1,
`fn-i-o` 2, `fn-output` 3, `fn-extend` 4, then the five relation codes `fn-equal-to` 5,
`fn-less-than` 6, `fn-greater-than` 7, `fn-not-less-than` 8, `fn-not-greater-than` 9). The status
block they report through is `01 File-Access.` at `[copybooks/wsfnctn.cob:L22]`, whose four
load-bearing members are `We-Error pic 999` L23, `Rrn pic 9(5) comp` L24, `Fs-Reply pic 99` L25 and
`FS-Action pic x(22)` **L41**, with `03 Logging-Data.` nested at L44-L55 and `03 RDB-Data.` nested at
L56-L62 supplying the six connection fields `DB-Schema`, `DB-UName`, `DB-UPass`, `DB-Host`,
`DB-Socket` and `DB-Port`.

---

## 10a. Three files the plan covers by wildcard, and the artifact boundary

Traceability cuts both ways: a reader must be able to account for every file in the tree, not only
find a module for every program. Three delivered files are reached by the AAP's **trailing wildcards**
rather than by a per-file table, so they are named here rather than left to be discovered. There is
no fourth: the connection-parameter reader is SECTION 0 of `acas_posting/cli/args.py` rather than a
module of its own, because the six `RDBMS-*` fields it fills are part of the system-record binding
§0.4.1.1 gives that module, and `acas_posting/cli/` therefore holds exactly the nine files §0.3.1
names.

Four harness files went the same way, into the listed file whose job each already shared, so that
`harness/` holds only paths §0.3.1 names. `harness/scenario_yaml.py`'s duplicate-rejecting loader and
`harness/scenario_stream.py`'s flat record stream are now `load_scenario_yaml` and the
`--scenario-stream` mode of `harness/normalize.py`; `harness/parity_stages.sh`
is `PARITY_STAGES` in that same file, published to shell through `--print-stage-shell` and to
everything else through `--print-stages`; and `harness/table_digest.py` is the
`--table-digest` mode of `harness/dump_tables.py`, which is where it always took its
digest from — it existed only to load that module by path and hash what `serialise_dump` returned. No
definition changed in any of the four: the loader's three parse budgets, the stream's four exit
statuses, the ten stage rows and the digest's three exit statuses are the values they were, and the
scenario stream is byte-identical for all eight definitions.

`harness/build_fixtures.sh` and `harness/make_fixtures.py` left the same way, as the
`--build-fixtures` mode of `harness/seed.sh` and the `--make-fixtures` mode of
`harness/dump_tables.py`. **`harness/run_parity.sh` is absent differently, and is not a mode of
anything**: its ten-stage orchestration is already implemented in
`tests/conftest.py::run_scenario_parity`, and the four gates it alone owned moved to the stage that
owns the state each protects — the oracle-provenance gate (exit 77) and the seed-file pre-flight into
`harness/reset_db.sh`, before it drops a table; the cross-side operations check into
`harness/run_cobol_scenario.sh`, before it drives an operation; and the destructive-target bypass
refusal into each of the three, conditioned on a bound `ACAS_PARITY_RUN_ID`. That last placement is
stronger than the driver's was, because a **hand-driven** stage is now guarded exactly as a composed
one is. Four options were deliberately not carried forward — `--from`/`--to`, `--dry-run`,
`--keep-going` and the `parity-result` summary file — and README §11.1 records what replaces each.

| File | The wildcard that covers it | What it is for | Ships in the wheel? |
|---|---|---|---|
| `harness/seed.sh --build-fixtures` | §0.2.1.2 *"Oracle harness: `harness/*`"* | Compiles a per-file COBOL writer and calls the frozen handler, because most seeded files are `ORGANIZATION INDEXED` and their on-disk form belongs to the image's library version — measurable, not assumable | No |
| `harness/dump_tables.py --make-fixtures` | §0.2.1.2 *"Oracle harness: `harness/*`"* | Generates that writer from each scenario's `seed_records`, so **no record layout is restated by hand** | No |

**Measured boundary.** Building the wheel and listing its entries shows only `acas_posting/` and its
`dist-info`: no `harness/`, no `tests/`, no `.cbl`/`.cob`/`.scb`, no `.sql`. That is R-1 enforced
structurally rather than by convention — there is no import path from the shipped package to the
oracle. **No JSON appears in the wheel either:** `data_dictionary*` is named in the packaging exclusion
list, so the generated dictionary stays the top-level sibling AAP §0.3.1 fixes it as, and
`acas_posting/dictionary/loader.py` resolves that one committed path rather than choosing between two
copies. With `include-package-data = false` and discovery constrained to `acas_posting*`, no stray file
in the checkout can reach the distribution.

## 11. Deliberate omissions, recorded **as** omissions

AAP §0.1.1 and §0.4.3 require these be visible rather than accidental, *"so that a reader comparing
the two files does not conclude something was lost"*. Each subsection names what is dropped, why, and
what — if anything — survives in its place.

### 11.1 Screen output with no database effect → a log record

Every `DISPLAY … AT` whose effect stops at the terminal becomes a log record at a severity matching
the original's intent. AAP §0.3.4 fixes two constraints on the replacement: it *"must not alter
control flow and must not appear in any table dump."*

The rule is applied uniformly, so the individual sites are not enumerated; three that a reader will
look for are `[general/gl070.cbl:L284]` and `[general/gl070.cbl:L292]` (the phase banners of §8),
`[general/gl071.cbl:L170]` (`"Sorting.......Please wait"`, the whole of `gl071`'s output), and the
five diagnostic displays of `Open-Error-Continued` at
`[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L356-L362]`. In the last case the *control transfer* that
follows them is preserved — see §9.4 — and only the presentation is replaced.

### 11.2 The `call "SYSTEM" using Print-Report` spool-out path

This statement hands a report file to the operating system, so it has no database effect and is not
reproduced. It occurs at **six** sites inside the twelve in-scope programs, and all six are omitted:

| Site | Program | Containing paragraph |
| --- | --- | --- |
| `[general/gl051.cbl:L991]` | `gl051` | `gl050d`'s `main-exit.` L985 — **doubly omitted**, since `gl050d` is itself outside the boundary of §7.1 |
| `[general/gl072.cbl:L443]` | `gl072` | `end-run.` L437 |
| `[sales/sl060.cbl:L710]` | `sl060` | `aa050-End-Loop-End.` L676 |
| `[sales/sl100.cbl:L454]` | `sl100` | `main-end.` L435 |
| `[purchase/pl060.cbl:L638]` | `pl060` | `init01`'s `end-loop-end.` L602 |
| `[purchase/pl100.cbl:L446]` | `pl100` | `main-end.` L427 |

`gl070`, `gl071`, `gl080`, `sl055`, `pl055` and `irs030` contain none. Note the spelling divergence,
preserved as an observation rather than normalised: `[sales/sl100.cbl:L454]` writes `print-report` in
lower case where the other five write `Print-Report`.

### 11.3 The unused facade stub blocks, which map to nothing

**Four** of the twelve programs declare a block of one-byte stubs whose only purpose is to satisfy the
linker: the facade copybook references every entity's record, so a program that uses only some of
them must still declare the rest. Quoting AAP §0.4.3: *"Python has no equivalent need, so the block
maps to nothing."*

| Program | Block | Span | Live stubs | Commented out — i.e. actually in use |
| --- | --- | --- | --- | --- |
| `gl051` | `01  Dummies-4-Unused-ACAS-FH-Calls.` `[general/gl051.cbl:L136]`, annotated `*> Call blk at zz080-ACAS-Calls` | L136-L156 | 16 | **four**: `Default-Record` L137, `WS-Ledger-Record` L140, `WS-Posting-Record` L141, `WS-Batch-Record` L142 |
| `gl072` | `01  Dummies-4-Unused-ACAS-FH-Calls.` `[general/gl072.cbl:L135]`, annotated `*> Call blk at zz080-ACAS-Calls` | L135-L155 | 17 | **three**: `Default-Record` L136, `WS-Ledger-Record` L139, `WS-Batch-Record` L141 |
| `gl080` | `01  Dummies-4-Unused-ACAS-FH-Calls.` `[general/gl080.cbl:L194]`, same annotation | L194-L214 | 16 | **four**: `Default-Record` L195, `WS-Ledger-Record` L198, `WS-Posting-Record` L199, `WS-Batch-Record` L200 |
| `irs030` | `01  Dummies-For-Unused-FH-Calls.` `[irs/irs030.cbl:L291]`, annotated `*> IRS call blk at zz100-ACAS-IRS-Calls` | L291-L296 | **one** | **four**: `WS-IRSNL-Record` L292, `WS-IRS-Default-Record` L293, `Posting-Record` L294, `WS-IRS-Posting-Record` L295 |

The commented-out entries are the informative ones: a stub is commented out **because the record is
in use**, which the maintainer instructs at `[general/gl072.cbl:L133]` and `[general/gl080.cbl:L192]`
with `*> REMARK OUT ANY IN USE`. Read that way the blocks are a handler manifest per program, and they
agree with the facade verbs each program actually performs. `Proc-ZZ100-ACAS-IRS-Calls.cob` points at
its own block in its header at `[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L5-L6]`.

### 11.4 The preserved naming inconsistency in the date wrapper

`[general/gl070.cbl:L603]` declares the section `maps03` — named after the *interface copybook* — while
`[general/gl070.cbl:L608]` names its exit label `maps04-exit`, after the *called program*. The same
pairing recurs at `[general/gl051.cbl:L1273]` and `[general/gl051.cbl:L1278]`. Both are preserved as
evidence rather than smoothed away; cross-reference **A-22**.

The inconsistency is **General-ledger-only**, which is what makes it an accident rather than a
convention: `sl060` §1292, `sl100` §808, `pl060` §1146 and `pl100` §789 all name the section `maps04`,
matching their exit labels at L1297, L813, L1151 and L794 respectively. `gl072`, `gl080`, `sl055` and
`pl055` declare no wrapper section under either name.

### 11.5 Prompts that merely pause for acknowledgement

An `ACCEPT` whose only effect is to block a terminal is dropped entirely — AAP §0.3.4: *"their only
effect is to block a terminal"*. Two rules govern the two shapes it takes:

- **A bare acknowledgement is removed.** `[irs/irs030.cbl:L1725-L1726]` displays
  `"Note counts and any messages"` and accepts a reply after the transfer-file decision has already
  been taken; both lines are dropped.
- **Where the prompt sits inside an error path that then transfers control, the control transfer is
  preserved and only the pause is removed.** The three IRS abort paths do exactly this:
  `[irs/irs030.cbl:L1600]`, `[irs/irs030.cbl:L1610]` and `[irs/irs030.cbl:L1677]` each accept a reply
  and then `go to`; the `go to` survives as a `return` or a `break`, the accept does not. The same
  applies to `[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L363]`, whose accept precedes the `goback.` at
  L364, and to the `accept-option.` retry loop at `[general/gl080.cbl:L542-L558]`.

**The one prompt that is *not* dropped** is the one that gates a database write. `EOJ-q1.` at
`[irs/irs030.cbl:L1715]` asks whether the Ledger Posting file may be cleared; answering `"Y"` performs
`acas008-Open-Output` at `[irs/irs030.cbl:L1723]`, which — per §16.5 — deletes every row. Its answer
therefore changes table state and is a genuine input, so it becomes an explicit parameter:
`acas_posting/programs/irs030_posting.py`'s `run` takes `clear_posting_file` as a keyword-only
argument, and `acas_posting/cli/irs_post.py` binds it. The `go to EOJ-q1` retry at
`[irs/irs030.cbl:L1719]` dissolves along with the prompt, because a parameter cannot be invalid.

### 11.6 `IRSFINAL-REC` is deliberately untouched by `irs030`

The frozen source says so twice over. `[irs/irs030.cbl:L296]` declares
`03  Final-Record          pic x.    *> Table/File not used in this program.` — and it is the **only
live entry** in that program's stub block, per §11.3. Independently, the in-scope section performs
`acasirsub1` (read-indexed four times, rewrite four times), `acasirsub3` once via the bare dispatch
paragraph at `[irs/irs030.cbl:L1586]` after setting `file-function` to 3 at L1585, `acasirsub4` three
times (open L1617, write L1673, close L1711) and `acas008` five times (open-input L1578, read-next
L1620, close L1712, open-output L1723, close L1724) — and **never `acasirsub5`**. Two further
`acasirsub1` verbs are commented out in the frozen source and are therefore not performed either:
`acasirsub1-Open` at `[irs/irs030.cbl:L1590]`, whose comment records that the file is opened in
`Initialise-Main`, and `acasirsub1-Close` at `[irs/irs030.cbl:L1710]`.

`acas_posting/dal/acasirsub5_irs_final.py` exists — it is one of the seventeen handler modules of §13
— but nothing in the migrated `irs030` path calls it.

### 11.7 Representation-only declarations

Group items, `REDEFINES` views and `FILLER` are recorded in the dictionary but have no column, and
`WS-Post-rrn` has a column the bridge never loads. §10.7 covers all four cases with locators; they are
listed there rather than duplicated here.

---

## 12. The dual-alias facade: a **behavioural** difference, not merely naming

`acas_posting/dal/facade.py` publishes **both** verb vocabularies over one implementation: the
**entity-named** set from `copybooks/Proc-ACAS-FH-Calls.cob` and the **handler-named** set from
`copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob`. A reader following either COBOL convention therefore finds
a correspondingly named Python function, while the logic exists once.

That much is a naming accommodation. The reason it is more than that is that the two conventions
**behave differently on error**, and the evidence is unanswerable.

### 12.1 The General / Sales / Purchase convention has no error handling at all

`copybooks/Proc-ACAS-FH-Calls.cob` is **1449** lines. A case-insensitive search for the string
`error` across the whole file returns **zero** hits. The word does not appear anywhere in it — not in
a paragraph name, not in a message identifier, not in a comment. Its callers test `fs-reply` and
`we-error` **inline**, at their own call sites.

Its structure, for the record:

| Fact | Value |
| --- | --- |
| Section | `zz080-ACAS-Processes` `[copybooks/Proc-ACAS-FH-Calls.cob:L3]` |
| Paragraph labels | **256** |
| of which handler-dispatch paragraphs | **21** — `acas000` L20, `acas004` L27, `acas005` L35, `acas006` L43, `acas007` L51, `acas008` L59, `acas010` L67, `acas011` L75, `acas012` L82, `acas013` L90, `acas014` L99, `acas015` L108, `acas016` L116, `acas017` L124, `acas019` L132, `acas022` L140, `acas023` L148, `acas026` L156, `acas029` L164, `acas030` L172, `acas032` L180 |
| of which entity-verb paragraphs | **235** (256 − 21) |
| Dispatch pattern | `acas007.` `[copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]` — set the key number, then `call` with five arguments |
| Facade pattern | `GL-Batch-Read-Indexed.` `[copybooks/Proc-ACAS-FH-Calls.cob:L465-L468]` — three statements: clear `Access-Type`, `set` the function code, `perform` the dispatch |

### 12.2 The IRS convention wraps every handler call in a per-handler error check

`copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob` is **367** lines, section `zz100-ACAS-IRS-Calls` at L2, with
**55** paragraph labels. It defines exactly **five** error checks, each with its own message
identifier:

| Check paragraph | Locator | Message | Displayed at | Handler closed |
| --- | --- | --- | --- | --- |
| `acas000-Check-4-Errors.` | `L320` | **IR911** | `L322` | `acas000-Close` L323 |
| `acas008-Check-4-Errors.` | `L327` | **IR916** | `L329` | `acas008-Close` L330 |
| `irsub1-Check-4-Errors.` | `L334` | **IR912** | `L336` | `acasirsub1-Close` L337 |
| `irsub3-Check-4-Errors.` | `L341` | **IR913** | `L343` | `acasirsub3-Close` L344 |
| `irsub5-Check-4-Errors.` | `L348` | **IR915** | `L350` | `acasirsub5-Close` L351 |

Each tests `if fs-reply not = zero`, displays its message, performs its handler's `-Close`, and then
`go to Open-Error-Continued` — the Class-4 site walked in §9.4, whose target ends in `goback.` at
`[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364]`, a hard return from the program.

There are **twelve** `perform *-Check-4-Errors` call sites, at L96, L101, L134, L140, L146, L173,
L179, L185, L227, L233, L291 and L297.

### 12.3 The `IR914` gap proves `acasirsub4` has no error check, and it is triple-sourced

The copybook dispatches **six** handlers but defines **five** checks. The missing one is
`acasirsub4`, and three independent sources say so:

1. **The maintainer's own header list omits IR914.**
   `[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L11]` reads
   `*>  Uses messages:  IR911, IR912, IR913, IR915, IR916. (Was IR011 - 16.` — five identifiers, with
   IR914 absent from a sequence that is otherwise contiguous.
2. **There are five check paragraphs and none for `acasirsub4`.** The six dispatch paragraphs are
   `acas000` L22, `acas008` L34, `acasirsub1` L45, `acasirsub3` L57, **`acasirsub4` L69** and
   `acasirsub5` L81; the five checks are those in §12.2.
3. **`irs030` declares IR914 itself and uses it inline.**
   `[irs/irs030.cbl:L396]` declares
   `03 IR914 pic x(51) value "IR914 Error on irspostingMT processing, FS-Reply = "`, and
   `[irs/irs030.cbl:L1675]` displays it — immediately after `perform acasirsub4-Write.` at
   `[irs/irs030.cbl:L1673]`. The caller does inline what the copybook does for the other five.

**Five error checks for six dispatched handlers.** Quoting AAP §0.6.5: *"The Python facade must
therefore behave differently depending on which alias set the caller used, which is a behavioral
difference and not merely a naming one."*

`acas_posting/dal/facade.py` reproduces exactly that shape: five check functions —
`acas000_check_4_errors` (L5504), `acas008_check_4_errors` (L5521), `irsub1_check_4_errors` (L5538),
`irsub3_check_4_errors` (L5554), `irsub5_check_4_errors` (L5570) — and **no** `acasirsub4` check,
plus `open_error_continued` (L5598) annotated `-> NoReturn`. The module publishes 284 public functions
in total, with 292 names in `__all__`, spanning both vocabularies over one implementation.

### 12.4 Which convention each program uses

| Convention | Programs | `copy` locator |
| --- | --- | --- |
| entity-named, `Proc-ACAS-FH-Calls.cob` | **ten** | `gl051` L1281, `gl070` L611, `gl072` L497, `gl080` L749, `sl055` L731, `sl060` L1300, `sl100` L816, `pl055` L634, `pl060` L1154, `pl100` L797 |
| handler-named, `Proc-ZZ100-ACAS-IRS-Calls.cob` | **one** | `irs030` L1732 |
| **neither** | **one** | `gl071` copies only `envdiv.cob` L85, `wscall.cob` L155, `wssystem.cob` L156 and `wsnames.cob` L157 |

Ten plus one plus one is twelve. `gl071` is the outlier because it reaches no table at all (§9.3).

Two naming oddities inside the IRS convention are preserved rather than normalised:
`acas008-Rewrite.` is published at `[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163]` even though the
handler rejects that verb unconditionally (§16.5, **A-6**); and `ReWrite` appears with a capital W at
`[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L250]` and `[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L314]`
against `Rewrite` at L163.

---

## 13. The data-access layer: 17 files, 20 pairs, 22 modules

The three numbers are different and all three matter, so the document states each separately rather
than collapsing them into "twenty modules".

| Count | What it counts |
| --- | --- |
| **17** | handler-named modules under `acas_posting/dal/` — one per in-scope COBOL handler |
| **20** | handler-and-bridge pairs those 17 modules cover |
| **22** | total modules in `acas_posting/dal/` — the 17 plus five infrastructure files |

**The arithmetic, shown.** `Proc-ACAS-FH-Calls.cob` declares **21** handler-dispatch paragraphs
(§12.1). Thirteen are in scope — `acas000`, `acas005`, `acas006`, `acas007`, `acas008`, `acas012`,
`acas013`, `acas015`, `acas016`, `acas019`, `acas022`, `acas026`, `acas029` — and **eight** are not:
`acas004`, `acas010`, `acas011`, `acas014`, `acas017`, `acas023`, `acas030`, `acas032`. The four IRS
handlers `acasirsub1`, `acasirsub3`, `acasirsub4` and `acasirsub5` appear **only** in the IRS
copybook, never in the entity one.

> **13 + 4 = 17** in-scope handlers → **17** handler modules.
> **16 × 1 + 1 × 4 = 20** bridges, because `acas000` fronts four of them.
> **20 + 8 = 28** bridges in `common/` altogether.
> **17 + 5 = 22** modules in `acas_posting/dal/`.

The seventeen: `acas000_system`, `acas005_gl_nominal`, `acas006_gl_posting`, `acas007_gl_batch`,
`acas008_spl_posting`, `acas012_sales`, `acas013_value`, `acas015_analysis`, `acas016_invoice`,
`acas019_otm3`, `acas022_purch`, `acas026_pinvoice`, `acas029_otm5`, `acasirsub1_irs_nominal`,
`acasirsub3_irs_dflt`, `acasirsub4_irs_posting`, `acasirsub5_irs_final`. The five infrastructure
files: `__init__.py`, `connection.py`, `status.py`, `cursor_state.py`, `facade.py`. The directory was
listed in this checkout and contains exactly those 22.

**`acas000` is a five-way dispatcher, not a four-way one.** `[common/acas000.cbl:L574]` opens
`evaluate File-Key-No` with `when 1` → `systemMT` L576, `when 2` → `dfltMT` L581, `when 3` →
`finalMT` L586, `when 4` → `sys4MT` L591, and **`when 5` → `systemMT` again** at
`[common/acas000.cbl:L596]`, annotated `*> support for PY may be`. The range check agrees:
`[common/acas000.cbl:L335]` reads `if File-Key-No < 1 or > 5     *> Chg 14/10/25 to support PY`, and
the version history records the change at `[common/acas000.cbl:L161]` as 3.3.01 pre-support for
Payroll. The module's own documentation was **not** updated —
`[common/acas000.cbl:L185]` still reads `998* = File-Key-No Out Of Range not 1, 2 or 3 or 4.` — so the
error text describes a four-way dispatcher that no longer exists. Key 5 is an alias of key 1, which is
why 20 bridges rather than 21 are reached; the alias is reproduced, and the stale message text with
it.

**The four IRS entities have no entity-convention name at all.** They are reachable only through
handler-named aliases, because `Proc-ACAS-FH-Calls.cob` declares no facade for them — its own header
says as much at `[copybooks/Proc-ACAS-FH-Calls.cob:L11-L12]`: the IRS file handlers and data-access
layers are not in that copybook, although the IRS posting file is, since Sales, Purchase and Stock all
write it. That asymmetry is the reason the Python facade must publish both sets rather than one with
a translation table.

For completeness, the FS-Reply and WE-Error vocabularies the seventeen report through are documented
in the handler itself: `[common/acas000.cbl:L178-L182]` gives `Fs-Reply` 0, 10, 21 and 99, and
`[common/acas000.cbl:L184-L190]` gives `WE-Error` 999, 998, 997, 996, 995, 994 and 990.
`acas_posting/dal/status.py` publishes them as `FsReply`, `WeError`, `FileFunction`, `AccessType`,
`SqlState`, `SqlStateMapping`, `LockRetryRung` and `DbErrorStatus`.

---

## 14. The three linkage shapes, and the seven routes that bind them

None of the twelve is a main program. Every one is a `CALL`ed sub-program with a fixed parameter list,
and there are exactly **three** distinct shapes — not one. `acas_posting/cli/args.py` publishes them as
three dataclasses, `GlLinkage`, `SlPlLinkage` and `IrsLinkage`, and every `run` keeps the COBOL order
positionally.

### 14.1 General Ledger — four parameters

`using ws-calling-data / system-record / to-day / file-defs`

| Program | Locator |
| --- | --- |
| `gl051` | `[general/gl051.cbl:L353-L356]` |
| `gl070` | `[general/gl070.cbl:L245-L248]` |
| `gl071` | `[general/gl071.cbl:L161-L164]` |
| `gl072` | `[general/gl072.cbl:L262-L265]` |
| `gl080` | `[general/gl080.cbl:L269-L272]` |

Python: `run(ws_calling_data, system_record, to_day, file_defs, *, …)`.

### 14.2 Sales and Purchase — **five** parameters, not four

`using ws-calling-data / system-record / system-record-4 / to-day / file-defs`

| Program | Locator |
| --- | --- |
| `sl055` | `[sales/sl055.cbl:L271-L275]` |
| `sl060` | `[sales/sl060.cbl:L395-L399]` |
| `sl100` | `[sales/sl100.cbl:L272-L276]` |
| `pl055` | `[purchase/pl055.cbl:L239-L243]` |
| `pl060` | `[purchase/pl060.cbl:L340-L344]` |
| `pl100` | `[purchase/pl100.cbl:L265-L269]` |

**AAP citation error (§6, C-05):** §0.4.1.1 calls this *"the four-parameter SL/PL linkage shape"*. It
is **five**. §0.1.1 of the same plan gives five, and so do all six programs. The source spelling of the
third parameter is **`system-record-4`**, in lower case with a hyphenated digit, not the plan's
paraphrase `WS-System-Record-4`.

The menus corroborate the arity independently, because they maintain **two** call paragraphs and pick
between them: `load00.` issues the four-parameter call —
`[sales/sales.cbl:L681-L685]`, `[purchase/purchase.cbl:L670]`, `[general/general.cbl:L711]` — and
`load000.` issues the five-parameter one, passing `WS-System-Record-4` as the third argument:
`[sales/sales.cbl:L702-L706]`, `[purchase/purchase.cbl:L695-L699]`, `[general/general.cbl:L727]`. Every
in-scope Sales and Purchase program is dispatched through `load000.`

Python: `run(ws_calling_data, system_record, system_record_4, to_day, file_defs, *, …)`.

### 14.3 IRS — three parameters, and materially different

`using IRS-System-Params / WS-System-Record / File-Defs` at `[irs/irs030.cbl:L552-L554]`.

**No calling-data block and no `to-day`.** That is corroborated three ways: `irs030` contains no
`copy "wscall.cob"`; a search of the file for `ws-calling-data`, `wscall` or `to-day` returns **zero**
hits; and it consequently sets no `WS-Term-Code` (§15.2).

The shape is an **IRS-wide idiom**, not a peculiarity of `irs030`: `irs010`
`[irs/irs010.cbl:L435-L437]`, `irs020` `[irs/irs020.cbl:L599-L601]` and `irs040`
`[irs/irs040.cbl:L290-L292]` all take the identical three parameters. The menu itself is the
exception — `[irs/irs.cbl:L470]` is `procedure division.` with **no** `USING`, because `irs.cbl` is a
**main** program rather than a called one.

**"No run date" never meant "no clock".** Parameter 2 still carries `Run-Date binary-long` at
`[copybooks/wssystem.cob:L67]`, so the IRS route pins one date observable rather than two.
`acas_posting/clock.py` publishes `PinnedRunDate`, `pin_from_calendar_date`, `pin_from_to_day`,
`pin_from_run_date` and `verify_pin`, which covers both cases from a single injected value. The read
the clock module reproduces is the date service's, and it produces exactly the two observables:
`move function current-date to wse-date-block.`
`[copybooks/Proc-ACAS-Mapser-RDB.cob:L72]`, then `move u-date to to-day.`
`[copybooks/Proc-ACAS-Mapser-RDB.cob:L77]` and `move u-bin to run-date.`
`[copybooks/Proc-ACAS-Mapser-RDB.cob:L80]`, with the pre-zeroing of §9.7 in between at L78.

**THE CLOCK-READ CENSUS — that copybook read is not the only one.** Calling it "the one clock read in
the whole call chain", following the Agent Action Plan's phrasing at §0.1.1, gets the *conclusion*
exactly right and the arithmetic wrong; nothing in the design changes either way. Measured over the
frozen tree:

- **Zero clock reads in all twelve in-scope posting programs.** `function current-date` appears in none
  of `gl051`, `gl070`, `gl071`, `gl072`, `gl080`, `sl055`, `sl060`, `sl100`, `pl055`, `pl060`, `pl100`
  or `irs030`; each receives the date purely through linkage. **That zero, not any count of reads
  elsewhere, is what makes pinning two observables at the CLI boundary sufficient.**
- **Six `function current-date` reads in the cycle's own call chain**, all in out-of-scope code: the
  shared date-service copybook `[copybooks/Proc-ACAS-Mapser-RDB.cob:L72]`, one in each of the four menu
  shells — `[general/general.cbl:L371]`, `[sales/sales.cbl:L323]`, `[purchase/purchase.cbl:L318]`,
  `[irs/irs.cbl:L480]` — and one in the system selector `[common/ACAS.cbl:L353]`. Counting
  `accept … from date` and `accept … from time` as well, the census over those six files is
  **fourteen** ambient reads; `tests/determinism/test_two_runs_byte_identical.py` publishes it site by
  site.
- **Further reads exist outside that chain**, in programs no scenario reaches:
  `[common/ACAS-Sysout.cbl:L107]`, `[common/fhlogger.cbl:L219]`, `[common/auditLD2.cbl:L192]` and L389,
  `[common/makesqltable-free.cbl:L81]` and L320, `[common/makesqltable-original.cbl:L78]` and L303, and
  `[stock/stock.cbl:L302]`. They are named so that a reader who greps and finds them does not conclude
  the census was wrong.

The same corrected census is carried by
[`anomaly-log.md`](anomaly-log.md) at A-16 and by the CLI modules' own clock-contract sections, so the
four places a reader might land all agree.

Python: `run(irs_system_params, ws_system_record, file_defs, *, clear_posting_file, …)` — the extra
keyword-only argument being the gated prompt of §11.5.

### 14.4 The `WS-Calling-Data` block the first two shapes pass

`[copybooks/wscall.cob:L6]` declares `01  WS-Calling-Data.` with seven leaves:

| Field | Picture | Locator |
| --- | --- | --- |
| `WS-Called` | `x(8)` | `L7` |
| `WS-Caller` | `x(8)` | `L8` |
| `WS-Del-Link` | `x(8)` | `L9` |
| `WS-Term-Code` | **`99`** | `L10` |
| `WS-Process-Func` | `9` | `L12` |
| `WS-Sub-Function` | `9` | `L13` |
| `WS-CD-Args` | `x(13)` | `L14` |

`WS-Term-Code` is **`pic 99`**, not `pic 9` — the maintainer's own change note at
`[copybooks/wscall.cob:L4]` records `Chg WS-Term-Code from 9 to 99.` That is what makes the menus'
`< 8` and `> 7` tests exhaustive and mutually exclusive over the whole domain 00-99, with no value
falling through both. The block was designed for unattended invocation —
`[copybooks/wscall.cob:L1-L3]` describes `WS-CD-Args` as carrying extra information for a `cron` call
by time — so binding it to command-line arguments is a faithful use rather than an invention.

### 14.5 The seven routes

`acas_posting/__main__.py` is the router, and its `_ROUTES` table carries the same COBOL locators this
document cites. The invocation form is `python -m acas_posting SUBSYSTEM OPERATION`, and each route
remains directly runnable as `python -m acas_posting.cli.<module>`.

| Subsystem | Operation | Python module | COBOL menu paragraph | Locator |
| --- | --- | --- | --- | --- |
| `general` | `post-cycle` | `acas_posting.cli.gl_post_cycle` | `load08.` | `[general/general.cbl:L805-L815]` |
| `general` | `end-of-cycle` | `acas_posting.cli.gl_end_of_cycle` | `load09.` | `[general/general.cbl:L817-L821]` |
| `sales` | `invoice-post` | `acas_posting.cli.sl_invoice_post` | **`load07.`** | `[sales/sales.cbl:L756-L768]` |
| `sales` | `cash-post` | `acas_posting.cli.sl_cash_post` | `load11.` | `[sales/sales.cbl:L792-L796]` |
| `purchase` | `order-post` | `acas_posting.cli.pl_order_post` | `load08.` | `[purchase/purchase.cbl:L752-L762]` |
| `purchase` | `payment-post` | `acas_posting.cli.pl_payment_post` | `load12.` | `[purchase/purchase.cbl:L786-L790]` |
| `irs` | `post` | `acas_posting.cli.irs_post` | `Main-Loop.` option `"4"` | `[irs/irs.cbl:L666-L672]` |

**AAP citation error (§6, C-06): Sales invoice posting is `load07.`, not `load08.`** Three
independent confirmations: the maintainer's own inline comment on the label —
`[sales/sales.cbl:L756]` reads `load07.             *> Sales trans posting`; the menu letter —
`"(G)  Sales Transactions Post"` at `[sales/sales.cbl:L545]` is the **seventh** option, with `(A)` at
L539; and what `load08.` actually does — `[sales/sales.cbl:L770-L774]` dispatches `sl080`, Payment
Input, which AAP §0.2.2 places out of scope. For contrast, Purchase's `load08` **is** correct, because
`"(H)  Purchase Transactions Post"` at `[purchase/purchase.cbl:L540]` is the eighth option with `(A)`
at L533.

**AAP citation errors (§6, C-07 and C-08)** for the two General routes: the plan cites both
`L806-L816` and `L800-L814` for the post-cycle, and `L711-L723` for the `gl080` dispatch. The verified
spans are **L805-L815** and **L817-L821**; `L711` is `load00.`, the shared four-parameter call
paragraph.

`acas_posting/cli/` holds **nine** files: `__init__.py`, the seven route modules above, and `args.py`
— exactly the set the AAP's target tree of §0.3.1 names. `acas_posting/__main__.py` records that
`args.py` is deliberately a library the routes use rather than a route itself; its SECTION 0 carries
the connection-parameter reader, which in a tenth module of its own would be a path the plan's
per-file tables do not name.

---

## 15. The three abort gates diverge — recorded, never harmonised (R-4)

The four menus gate the phases of a posting run differently, and one of them does not gate at all. R-4
forbids reconciling them.

### 15.1 The four routes, side by side

| Sub system | Locator | Predicate | Gates | Effect |
| --- | --- | --- | --- | --- |
| **General** | `[general/general.cbl:L805-L815]` | `ws-term-code = 5` at **L810-L811** | **one**, after `gl070` only | Quoting AAP §0.6.4: *"The effect is that `gl071` and `gl072` never run at all."* |
| **Sales** | `[sales/sales.cbl:L756-L768]` | `ws-term-code not = zero` | **two** — L761-L762 after `sl830`, L765-L766 after `sl055` | a different predicate, and one more gate |
| **Purchase** | `[purchase/purchase.cbl:L752-L762]` | — | **none** | see §15.3 |
| **IRS** | `[irs/irs.cbl:L666-L672]` | — | none | the `CALL` is inline in the menu's `evaluate`; no dispatch wrapper at all |

The General chain is four links long and crosses three programs: `[general/gl070.cbl:L314-L315]`
detects an open batch and sets the flag; `[general/gl070.cbl:L289]` moves **5** into `ws-term-code`;
`[general/gl070.cbl:L290]` exits; and `[general/general.cbl:L810-L811]` tests the code and returns to
the menu. The Python CLI reproduces it as a **hard** gate between phases, not a warning.

### 15.2 Only three in-scope programs ever set `WS-Term-Code`

| Program | Value | Locator |
| --- | --- | --- |
| `gl070` | **5** | `[general/gl070.cbl:L289]` |
| `sl055` | **8** | `[sales/sl055.cbl:L344]` |
| `pl055` | **8** | `[purchase/pl055.cbl:L286]` |

`gl051`, `gl071`, `gl072`, `gl080`, `sl060`, `sl100`, `pl060`, `pl100` and `irs030` set none — `irs030`
cannot, having no calling-data block at all (§14.3).

⇒ **Exit 5 and exit 8 are frequently the correct, specified outcome, not failures.** Quoting AAP
§0.6.5 on a run-aborting rejection: *"The database effect is therefore the absence of everything the
later phases would have written."* **Absence is evidence.** A scenario whose expected result is an
aborted run is verified by the later phases having written nothing, and a harness that treated a
non-zero exit as a failure would reject a correct run.

### 15.3 Purchase has no abort gate, because the lines are commented out

`[purchase/purchase.cbl:L755-L758]` — **four consecutive commented-out lines** — are the `pl830`
autogen call *and* the gate that would follow it:

```text
 *>    move     "pl830" to WS-Called.   *> In case autogen is use
 *>    perform  load000.
 *>    if       ws-term-code not = zero
 *>             go to display-menu.
```

What remains live is `move "pl055" to ws-called.` L759, `perform load000.` L760,
`move "pl060" to ws-called.` L761 and `go to load000.` L762. **`pl060` runs whatever `pl055`
returned.** This is the sharpest R-4 obligation in the tree: reproducing it means `pl_order_post`
must *not* gate, even though its Sales twin does, and even though `pl055` demonstrably can set
`ws-term-code` to 8 (§15.2). `acas_posting/__main__.py`'s route summary records the same divergence
against the same locator.

**Three further Purchase-against-Sales divergences appear within those few lines**, and all three
are preserved:

1. `pl830` is commented out entirely, where `sl830` is live at `[sales/sales.cbl:L759-L760]`.
2. The commented-out Purchase line uses `perform load000` where the live Sales line uses
   `perform load00` — **even the dead code diverges**, and by the very arity §14.2 is about.
3. The serious-error tail of the shared five-parameter paragraph differs:
   `[purchase/purchase.cbl:L703-L704]` is `if ws-term-code > 7 / go to overrewrite.` where
   `[sales/sales.cbl:L710-L712]` is `if ws-term-code > 7 / perform overrewrite / goback.` One returns
   to the menu by falling into a paragraph; the other performs it and leaves the program.

---

## 16. The five rejection classes — same disposition **and** same database effect

AAP §0.8.1 requires rejection behaviour be preserved in both dimensions, because *"a single generic
rejection path would fail this directive"*. Five classes exist, and they differ precisely in the second
dimension.

### 16.1 Clean rejection — no database effect, and entirely silent

`gl072` skips a posting whose batch number is non-numeric at `[general/gl072.cbl:L291-L292]`, and skips
a record whose handler returned a specific error at `[general/gl072.cbl:L306-L307]` and again inside
`headings` at `[general/gl072.cbl:L348-L349]`.

Both are **entirely silent** — no message, no counter, no trace, no accumulator touched. **Adding a
warning would be an added behavior**, which R-3 forbids as surely as adding a validation would.
Cross-reference **A-13**.

### 16.2 Run-aborting rejection — the effect is an absence

A control-total mismatch at `[general/gl051.cbl:L1117-L1121]` leaves the batch status 0, which
`gl070`'s Phase-1 walk detects at `[general/gl070.cbl:L314-L315]`, which raises code 5 at
`[general/gl070.cbl:L289]`, which the menu tests at `[general/general.cbl:L810-L811]`. The database
effect is *the absence* of everything `gl071` and `gl072` would have written — see §15.2.

### 16.3 Partial database effect — two defects in the IRS path

Both are reproduced exactly, in `acas_posting/programs/irs030_posting.py`.

**The half-posted double entry.** The debit is accumulated at `[irs/irs030.cbl:L1635-L1637]` and
**rewritten at `[irs/irs030.cbl:L1641]`** — *before* the credit account is even looked up at
`[irs/irs030.cbl:L1647]`. When that lookup fails, `[irs/irs030.cbl:L1648-L1652]` displays `IR033`,
accepts, and returns to the loop at L1652. The result is a posted debit with no balancing credit and no
posting record at all, because the posting-record build at L1661-L1671 is never reached.
Cross-reference **A-4**. Note the asymmetry: the *debit* miss at `[irs/irs030.cbl:L1630-L1634]` is
clean, because nothing has been written yet when it is detected.

**The lost update on the two VAT control accounts.** The two accounts are read into snapshots before
the loop — `move WS-IRSNL-Record to nl31-record.` at `[irs/irs030.cbl:L1602]` and
`move WS-IRSNL-Record to nl32-record.` at `[irs/irs030.cbl:L1612]`, each after a read-indexed on
`def-acs (31)` L1594 and `def-acs (32)` L1604 — and rewritten **from those snapshots** at end of job:
`[irs/irs030.cbl:L1704-L1705]` and `[irs/irs030.cbl:L1707-L1708]`. Any in-loop rewrite of the same two
accounts is therefore overwritten. Cross-reference **A-5**.

### 16.4 File-abandoning rejection — the partial state is committed, not rolled back

`perform acasirsub4-Write.` at `[irs/irs030.cbl:L1673]` is tested at
`[irs/irs030.cbl:L1674-L1678]`: on failure it displays `IR914` L1675 and `WE-Error` L1676, accepts
L1677, and **`go to EOJ.` at L1678** — a Class-2 forward terminator.

`EOJ.` at `[irs/irs030.cbl:L1702]` then runs in full: both snapshot rewrites (L1704-L1705,
L1707-L1708) and **two** closes — `perform acasirsub4-Close.` **L1711** and `perform acas008-Close.`
**L1712**. **Two live closes, not three:** `perform acasirsub1-Close.` at L1710 is commented out,
its comment recording that the file is closed at end of job elsewhere. Dropping the post-loop block
would silently lose all of this, which is why §9.1's Class 2 is `break` **plus** the work.

**Three abort paths bypass `EOJ` entirely**, because `main99-exit.` at L1729 sits *after* `EOJ-q1.`
at L1715 in source order, so a jump to it skips both:

| Path | Detected at | Message | Exit |
| --- | --- | --- | --- |
| transfer file will not open | `[irs/irs030.cbl:L1578-L1579]` | **IR031** L1580 | `go to main99-exit.` **L1581** |
| VAT control account 31 not found | `[irs/irs030.cbl:L1596-L1597]` | **IR03A** L1598 | `go to main99-exit.` **L1601** |
| VAT control account 32 not found | `[irs/irs030.cbl:L1606-L1607]` | **IR03B** L1608 | `go to main99-exit.` **L1611** |

Each leaves the two nominal accounts un-rewritten and the transfer file uncleared — a *fourth* distinct
database outcome from the same section.

### 16.5 A permanently failing facade verb

`[common/acas008.cbl:L299-L307]` rejects four of the handler's published verbs unconditionally, at
entry, before any file or table is touched:

```text
     evaluate File-Function
              when  4   *> fn-read-indexed
              when  7   *> fn-re-write
              when  9   *> fn-start
              when  8   *> fn-delete
                       move 988 to WE-Error
                       move 99 to fs-reply
                       go   to aa999-main-exit
     end-evaluate.
```

The returned pair is **`WE-Error = 988`** at `[common/acas008.cbl:L304]` and **`FS-Reply = 99`** at
`[common/acas008.cbl:L305]`, with the comment at L304 giving the reason: the action type is wrong for a
sequential file. The rewrite verb is nonetheless **published** by the facade at
`[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163]`, so any caller invoking it always fails.
`acas_posting/dal/acas008_spl_posting.py` reproduces the guard and returns the same pair rather than
performing an update. Cross-reference **A-6**.

Two related behaviours of the same handler are reproduced with it:

- **Opening for output means deleting every row.** `[common/acas008.cbl:L313-L319]` converts an
  open-output into `fn-delete-all` — `set fn-delete-all to true` at L316 — and
  `[common/acas008.cbl:L571-L574]`, inside `ba015-Test-Ends.` L566, forces the same substitution again.
  This is how the transfer-file clear of §11.5 is implemented.
- **The handler labels itself as the IRS sub system**, not as Sales or Purchase:
  `move 1 to WS-Log-System.` at `[common/acas008.cbl:L293]`, whose inline comment gives the encoding
  `1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock`, and `move 15 to WS-Log-File-No.` at
  `[common/acas008.cbl:L294]`. It matters only if logging is later compared, and it is recorded so that
  it is not mistaken for a bug when it is.

### 16.6 One asymmetry that decides which tables a run touches

The IRS fan-out is a single character with two condition names: `IRS-Instead pic x.` at
`[copybooks/wssystem.cob:L179]`, `88  IRS-Used  value "Y".` at `[copybooks/wssystem.cob:L180]` and
`88  IRS-Both-Used  value "B".` at `[copybooks/wssystem.cob:L181]` — a **three-state** switch, since
neither name holds when the field is space.

**AAP citation error (§6, C-29):** the plan says it is tested at "three sites in each of the four
Sales and Purchase posting programs". The verified counts are **seven, seven, seven and six** —
**27** sites:

| Program | Sites |
| --- | --- |
| `sl060` | L1039, L1046, L1126, L1144, L1172, L1175, L1177 |
| `sl100` | L578, L585, L647, L665, L690, L693, L695 |
| `pl060` | L907, L914, L982, L999, L1027, L1030, L1032 |
| `pl100` | L566, L629, L646, L671, L674, L676 |

`sl055` and `pl055` test it nowhere.

**`pl100` tests a weaker predicate than its Sales twin at the corresponding site.**
`[purchase/pl100.cbl:L566]` is `if irs-used` alone, where `[sales/sl100.cbl:L578]` is
`if irs-used OR IRS-Both-Used`; both carry the same trailing comment,
`*> will open as o/p if not exist`. So in `IRS-Both-Used` mode the Sales program opens the transfer
file and the Purchase program does not. That is a divergence in *which tables a run touches*, and it is
preserved rather than harmonised. A further preserved oddity: all four programs carry the identical
misplaced comment `*> THIS IS IN PURCHASE PL060` at `[sales/sl060.cbl:L1172]`,
`[sales/sl100.cbl:L690]`, `[purchase/pl060.cbl:L1027]` and `[purchase/pl100.cbl:L671]`.

Because the switch decides the affected-table list, every scenario definition must pin it explicitly;
leaving it at a default would make the list ambiguous.

Finally, the **nine** period-total write sites — the sole writers of `SYSTOT-REC`, which is what makes
the period-end scenario verifiable by inspecting one table — were verified individually:

| Site | Field |
| --- | --- |
| `[sales/sl055.cbl:L675]` | `sl-invoices-this-month` |
| `[sales/sl055.cbl:L677]` | `sl-credit-notes-this-month` |
| `[sales/sl060.cbl:L641]` | `sl-credit-deductions` |
| `[sales/sl060.cbl:L700]` | `sl-cn-unappl-this-month` |
| `[sales/sl100.cbl:L404]` | `sl-payments` |
| `[purchase/pl055.cbl:L582]` | `pl-invoices-this-month` |
| `[purchase/pl055.cbl:L584]` | `pl-credit-notes-this-month` |
| `[purchase/pl060.cbl:L628]` | `pl-cn-unappl-this-month` |
| `[purchase/pl100.cbl:L396]` | `pl-payments` |

---

## 17. Self-audit

### 17.1 Coverage

| R-5 clause | Where | Complete? |
| --- | --- | --- |
| every program maps to a module | §7 | **Yes** — all twelve, one-to-one, with verified line counts and both partial boundaries given as line spans |
| every paragraph maps to a function | §9.3 | **Yes** — every section and paragraph of every in-scope `PROCEDURE DIVISION`, in source order, with the Python name read from the sibling module rather than predicted |
| the `GO TO` class is annotated at every transfer site | §9.1, §9.3 | **Yes** — **206 sites**, each placed in the paragraph that contains it and carrying its class; the four-class census is published in §9.1 and the `C1`…`C4` shorthand is defined there |
| each Class-4 site carries an equivalence argument | §9.4 | **Yes** — **16** C4 sites, one walked in full and every other classified by where its target's own transfer goes |
| the `PERFORM … THRU` sites are individually hand-verified | §9.5 | **Yes** — nine live sites in two spellings, listed one per row, with the in-boundary subset identified |
| every field maps to a data-dictionary entry | §10 **and Appendix A** | **Yes — and now enumerated rather than counted, declaration by declaration.** Appendix A lists **all 1067 entries**, one row each: 513 that reach a column, grouped by their 22 tables and ordered by schema column ordinal, and 554 that declare no column, grouped by their 66 declaring files. The enumeration is closed over the DECLARATION MULTISET rather than over a total: `copybooks/plwsoi5C.cob` carries seven rows for its seven declarations rather than one. Every row carries the copybook or program-source field, the bridge host variable, the SQL column, the one-sided flag, drift, derivation, storage class, A-/Q- references and a locator per layer. Rendered mechanically from `data_dictionary/acas_posting_dictionary.json`, so it is derived and not transcribed; §10.7 still accounts for the one-sided remainder in prose |
| the mapping is recorded as a document | this file | **Yes** |

### 17.2 Companion and test paths, verified against the tree

Each item below was read in the completed checkout, and every count was taken
from the tree rather than carried forward:

| Item | Status in this checkout |
| --- | --- |
| `tests/arithmetic/` | **present — fourteen test files, exactly the AAP §0.4.1.7 set**. The shared-storage, dispatch-boundary, tier-import, deployment-contract and cross-file-reference coverage, and the four groups that drive shipped program and CLI modules in-process, are **merged into the planned file that owns the subject** rather than each holding a file of its own — `test_comp_binary.py`, `test_pic_field_descriptors.py`, `test_gl080_cycle_divide_rounded.py`, `test_ledger_balance_accumulation.py`, `test_control_total_comparison.py` and `test_double_entry_explosion.py` respectively. The collected test-name multiset is identical either way, so the coverage is unchanged; A-1's nested posting close and the IR032 clean rejection, both call sequences no table dump can observe, are locked in `test_double_entry_explosion.py`. §7.2 records which module each group drives |
| `tests/scenarios/` | **present — eight scenario tests**, exactly the eight that discharge AAP §0.8.5's mandate |
| `tests/determinism/test_two_runs_byte_identical.py` | **present** |
| `harness/scenarios/` | **present — 8 YAML definitions**, exactly the mandated set, `period_end_totals.yaml` among them |
| `docs/migration/ambiguity-resolutions.md` | **present** |
| `docs/migration/scenario-diff-evidence.md` | **present** |
| `README-python-migration.md` | **present at repository root** |

**BOTH ROWS READ "EIGHT", AND A NINTH IS THE PLAUSIBLE MISREADING.** A ninth scenario —
`harness/scenarios/end_of_cycle_gl.yaml`, with `tests/scenarios/test_end_of_cycle_gl.py`
beside it — would drive `gl_end_of_cycle` and therefore `gl080`, which no other scenario
reaches. Neither file is committed, because AAP §0.3.1 and §0.4.1.7 name eight scenario
definitions and eight scenario tests and this tree is held to that inventory.
The count in a hand-maintained inventory decays the moment the tree moves, which is
exactly the failure this subsection exists to catch, and it caught itself late in both
directions. **What the removal costs, stated here because a count alone hides it:**
`gl080` has no table-state comparison behind it. Anomalies A-2 and A-3 remain locked by
`tests/arithmetic/test_gl080_cycle_divide_rounded.py`, and the three questions that once
waited on an end-of-period scenario were resolved by standalone compiled probes — see
[`ambiguity-resolutions.md`](ambiguity-resolutions.md) §16.1, which also records the
removed definition's design so it can be rebuilt rather than re-derived.

Everything else this document cites was read in this checkout: the twelve programs, the four menus, the
handlers and bridges named, the copybooks named, `mysql/ACASDB.sql`, the thirteen files of
`acas_posting/programs/`, the twenty-two of `acas_posting/dal/`, the nine of `acas_posting/cli/`, the
eight of `acas_posting/cobol/`, the twenty-eight of `acas_posting/records/`, the four of
`acas_posting/dictionary/`, both `data_dictionary/*.json`, `acas_posting/clock.py`,
`acas_posting/dates.py`, `acas_posting/workfiles.py`, `acas_posting/__main__.py`, `pyproject.toml`, and
[`anomaly-log.md`](anomaly-log.md).

### 17.4 The whole tracked inventory, counted from the tree

**The migration's tracked file set is EXACTLY the inventory AAP §0.3.1 and §0.4.1
name — 141 paths, with nothing missing and nothing extra.** Seventeen further paths beyond
that inventory are each folded into a planned file rather than standing on their own, which
is what keeps the two counts equal. The counts below are taken from the tree with
`git ls-files`, not carried forward:

| Group | Paths | Composition |
| --- | --- | --- |
| repository root | 3 | `pyproject.toml`, `requirements.txt`, `README-python-migration.md` |
| `acas_posting/` | 89 | 5 at the package root, 9 `cli/`, 8 `cobol/`, 22 `dal/`, 4 `dictionary/`, 13 `programs/`, 28 `records/` |
| `data_dictionary/` | 2 | the generated dictionary and its JSON Schema |
| `docs/migration/` | 4 | this file, the anomaly log, the ambiguity register, the diff evidence |
| `harness/` | 19 | 11 at the harness root, 8 scenario definitions |
| `tests/` | 24 | `conftest.py`, 14 arithmetic, 8 scenario, 1 determinism |
| **total** | **141** | |

**Two tracked files sit outside those groups and are disclosed rather than counted:**
`.gitignore` and `.dockerignore`. Both are repository hygiene for the Python tree — they
keep `.venv/`, `__pycache__/`, coverage output and build artefacts out of the checkout and
out of the container build context. Neither is named in the AAP inventory, neither is a
migration artefact, and removing them would put generated files back into `git status`, so
they are recorded here as a deliberate, visible exception rather than left to be discovered
as a discrepancy.

### 17.3 Test artefacts beyond the planned inventory, named so R-5 covers them

R-5 requires that the mapping be *recorded*, and a test that locks a mapping is part
of that record. The artefacts below reach beyond the planned per-file tables, so they are
named here rather than left discoverable only by reading the suite. Every
name was read out of the file it lives in.

**`tests/arithmetic/test_comp_binary.py`** carries numbered
sections in its merged shared-storage group, and the numbering is carried across the
merge unchanged so that every reference to a section number resolves. Those beyond the
planned set:

| Section | What it locks |
| --- | --- |
| §17 | what the harness **generates** versus what it **reuses** — the provenance boundary |
| §18 | **withdrawn**, and deliberately left in place as a withdrawn marker rather than renumbered: the `gl051` control-total gate is driven by `test_control_total_comparison.py` instead |
| §19 | `gl072`'s two silent skips, driven against the migrated loop — and the derivation of why **no seed can reach either**, which is `A-NEW-18`/`N-KEY` |
| §20 | **A-6**, locked at the handler where it lives: the migrated `acas008` is called once per refused verb and must return the measured `WE-Error 988` / `FS-Reply 99` pair |
| §21 | the **tier-import contract** — that the arithmetic tier imports only the semantics and records tiers, bounded so the assertion cannot pass vacuously |
| §22 | the **`POST-KEY` round trip**, measured and pinned — the byte-level half of `A-NEW-18`/`N-KEY` |
| §23 | the **citation contract**: every `[path:Lnnn]` in this migration's own files must resolve to a line that exists |

**§23 bounds what it can prove, and the bound matters when reading any locator in
these documents.** It checks that a cited path exists and that the cited line is
within that file. It cannot check that the line *says what the surrounding prose
claims*, so an off-by-one inside a valid range passes. Two such errors were found by
hand — `HV-POST-KEY` cited at `[common/glpostingMT.cbl:L282]`, which is `HV-POST-RRN`;
the declaration is at `[common/glpostingMT.cbl:L283]` — so semantic spot-checking of
load-bearing locators remains manual work that §23 narrows rather than replaces.

**Other tests beyond the planned set**, with the question or anomaly each closes:

| Test | Locks |
| --- | --- |
| `test_comp_binary.py` GROUP 12, six tests | `Q-5.1` as measured: a **pictured** `COMP` store reduces on **digits**, a **pictureless** `BINARY-*` item wraps at its signed **byte capacity**, and the two are **not the same rule** |
| `test_gl080_cycle_divide_rounded.py`, four tests | `Q-GL080-DIVIDE-BY-ZERO` — that the zero divisor is reachable and **stores nothing**, that the guard can pre-empt it, that control still **reaches Phase 5**, and that subscript zero writes `Ledger-Last`, a **real `GLLEDGER-REC` column** |
| `test_irs_date_component_derivation.py`, two `Q-1` tests | that a rejected date leaves the binary field **untouched**, and that a **non-zero** binary field selects the **reverse** conversion — the second being the direction nobody had asked about |

### 17.4 What this document does **not** claim

- **This document is not the runtime evidence register.** The strict oracle
  build and the empty scenario diffs — nine of them as of this revision — are recorded in
  [`scenario-diff-evidence.md`](scenario-diff-evidence.md); compiled semantic
  arbitrations are recorded in
  [`ambiguity-resolutions.md`](ambiguity-resolutions.md). This file continues
  to own only the R-5 mapping.
- **A green parity suite does not close every semantic question.** Values that
  need a boundary-specific experiment — for example `Q-3`, `Q-4`, `Q-5.2`,
  and `Q-SORT-TIE-ORDER` — remain cross-referenced rather than guessed.
- **No anomaly is re-described.** Anomalies are cross-referenced by identifier — the sixteen A-1,
  A-2, A-3, A-4, A-5, A-6, A-7, A-8, A-11, A-12, A-13, A-14, A-16, A-17, A-21 and A-22 all appear
  above, and A-15 and A-NEW-13 are named in this section — and [`anomaly-log.md`](anomaly-log.md)
  remains the single place each is specified. Identifiers are **never renumbered**, for the reason
  that register gives in its own §5.
- **No out-of-scope name is presented as migrated.** The eleven out-of-scope tables and eight
  out-of-scope bridges appear in §10.4 as counts and name lists only. The eight out-of-scope handlers
  appear in §13 only as the complement that makes 21 − 8 = 13.
- **No COBOL is implied at runtime.** Every COBOL locator is cited as specification. §2.2 gives the
  three structural proofs that the shipped package cannot reach the harness.

---

## 18. Companion documents

This is one of four migration documents and deliberately does not duplicate the others. All four are
companion deliverables of the same single execution phase, per AAP §0.4.5 and §0.4.1.7.

| Document | What it carries | Why it is not here | Present today |
| --- | --- | --- | --- |
| [`anomaly-log.md`](anomaly-log.md) | the twenty-two reproduced legacy defects, each with locators, a reproducing module and a locking test where one applies | R-4's register. This document cites `A-` identifiers and stops there | **yes** |
| [`ambiguity-resolutions.md`](ambiguity-resolutions.md) | each `Q-` question, the oracle experiment, and the resolution where one has been observed | R-6's arbitration record. This document cross-references a `Q-` identifier rather than pre-empting its answer | **yes** |
| [`scenario-diff-evidence.md`](scenario-diff-evidence.md) | the observed empty-diff evidence, per mandated scenario | evidence of parity, which is a measurement; this document is a mapping | **yes** |

Further reading: [`../../README-python-migration.md`](../../README-python-migration.md)
for how to build the oracle, seed a scenario, run both cycles and diff them;
and the maintainer's own `README.TXT` and `Changelog` for the
COBOL system's own history, neither of which this work modifies. One statement in the latter bears
directly on how this document should be used — `[README.TXT:L50-L53]` records that testing is complete
for the IRS, Stock and Sales sub systems apart from some reports, while General has not been worked on
since the migration to the GnuCOBOL 3.2 compiler. The General Ledger contributes five of the twelve
in-scope programs. A mapping is not a measurement: where this document says a paragraph does something,
it says so because the source says so, and where the compiled General Ledger disagrees with the source,
the compiled behaviour is the specification and the disagreement belongs in
`ambiguity-resolutions.md`.

---

## Appendix A — the complete field → dictionary-entry enumeration

**This appendix discharges R-5's "every field maps to a data-dictionary entry" by enumeration rather
than by count.** Every one of the **1067** entries in
`data_dictionary/acas_posting_dictionary.json` appears below exactly once: **513** that reach a column
in the frozen schema, in §A.1, grouped by their **22** in-scope tables and ordered within each table by
the column ordinal the schema declares; and **554** that declare no column, in §A.2, grouped by the
**66** files that declare them. 513 + 554 = 1067, which is the artifact's own
`coverage.entry_count`.

**Provenance, stated before the tables so that no row is mistaken for hand-written.** These rows are
**rendered mechanically** from the committed JSON artifact. That artifact is in turn generated by
`acas_posting/dictionary/generate.py` from the three authoritative layers — the frozen copybook
picture clauses, the frozen bridges' host-variable declarations, and the frozen `CREATE TABLE`
statements of `mysql/ACASDB.sql` — which is the ordering AAP §0.8.1 mandates under "Data dictionary
first". No field's metadata was read off a source and typed in here. To confirm the artifact is itself
current, run:

```bash
python -m acas_posting.dictionary.generate --check
```

which re-derives it from the frozen sources and reports agreement without writing. **If this appendix
and that artifact ever disagree, the artifact is right and this appendix is stale.**

### How to read a row

| Column | What it holds |
| --- | --- |
| **Dictionary key** | the entry's key, `TABLE-NAME.COLUMN-NAME` for a column-bearing entry and `RECORD-NAME.FIELD-NAME` for a record-only one. This is the exact string `acas_posting.dictionary.loader.get_entry` takes |
| **Copybook / program-source field** | the COBOL declaration: name, level, picture, usage, signedness and sign position, `OCCURS`, `REDEFINES`, group and `FILLER` flags, then its `path:line` locator. `**absent**` means the field exists in the bridge and the schema but in **no** copybook — the case AAP §0.1.1 uses to argue the bridge is authoritative |
| **Bridge host variable** | the generated bridge's `01`-level host variable: name, picture, signedness, and whether the bridge's load and unload paragraphs actually move it. `NOT loaded` is load-bearing rather than trivia — see `GLPOSTING-REC.POST-RRN` |
| **SQL column** | name, declared type, unsignedness and primary-key flag, with its line in `mysql/ACASDB.sql` |
| **One-sided** | **yes** when at least one of the four layers does not declare this field. The generator flags it; nothing is inferred here |
| **Drift · derivation · storage** | where the layers disagree (signedness, usage, digits, scale, character length, name), how a bridge-only column is computed and under what guard, and which Python storage class carries the value |
| **A- / Q-** | the anomaly and ambiguity identifiers the generator attached to this entry. `A-` resolves in [`anomaly-log.md`](anomaly-log.md) and `Q-` in [`ambiguity-resolutions.md`](ambiguity-resolutions.md) |

### What the enumeration makes checkable that a count could not

Three claims elsewhere in this document are now verifiable by reading rows rather than by trusting a
sentence, and each is worth locating before scrolling:

- **A-11's sign loss at the bridge.** `SALEDGER-REC.SALES-AVERAGE` in §A.1 shows `BINARY-LONG · signed`
  in the copybook, `9(10) · unsigned` in the host variable and `int(8) unsigned` in the column, with
  `drift: signedness, usage` and refs `A-11`, `Q-3`. The sign is gone before any SQL runs.
- **A-12's width drift.** `GLLEDGER-REC.LEDGER-NAME` shows `x(24)` against `X(32)` against `char(32)`,
  with `drift: character_length` and ref `A-12` — the drift that makes the dump normaliser's
  trailing-space job necessary.
- **A-7's bridge-only columns.** `IRSPOSTING-REC.POST4-DAY` shows `**absent**` in the copybook column,
  `one_sided: yes`, and `derivation: BRIDGE_DERIVED guarded on ...` — three columns of a posting table
  that a copybook-driven migration would have silently omitted.

### A.1 The 513 entries that reach a column, by table

Each block is one in-scope table. The row order is the column ordinal the frozen schema declares,
so a reader walking a `CREATE TABLE` statement and a block side by side stays in step.

#### `ANALYSIS-REC` — 4 columns · bridge `analMT` · handler `acas015` · facade `Analysis`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 1 | `ANALYSIS-REC.PA-CODE` | `WS-Pa-Code` · lvl 03 · GROUP · group `[copybooks/wsanal.cob:L10]` | `HV-PA-CODE` · `X(3)` · unsigned · loaded/unloaded `[common/analMT.cbl:L283]` | `PA-CODE` · `char(3)` · **PK** `[mysql/ACASDB.sql:L32]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 2 | `ANALYSIS-REC.PA-GL` | `Pa-Gl` · lvl 03 · `9(6)` · DISPLAY `[copybooks/wsanal.cob:L15]` | `HV-PA-GL` · `9(08)` · unsigned · loaded/unloaded `[common/analMT.cbl:L284]` | `PA-GL` · `mediumint(6) unsigned` · unsigned `[mysql/ACASDB.sql:L33]` | no | drift: usage, digits; storage: INT | — |
| 3 | `ANALYSIS-REC.PA-DESC` | `Pa-Desc` · lvl 03 · `x(24)` `[copybooks/wsanal.cob:L16]` | `HV-PA-DESC` · `X(24)` · unsigned · loaded/unloaded `[common/analMT.cbl:L285]` | `PA-DESC` · `char(24)` `[mysql/ACASDB.sql:L34]` | no | storage: STR | — |
| 4 | `ANALYSIS-REC.PA-PRINT` | `Pa-Print` · lvl 03 · `xxx` `[copybooks/wsanal.cob:L17]` | `HV-PA-PRINT` · `X(3)` · unsigned · loaded/unloaded `[common/analMT.cbl:L286]` | `PA-PRINT` · `char(3)` `[mysql/ACASDB.sql:L35]` | no | storage: STR | — |

#### `GLBATCH-REC` — 21 columns · bridge `glbatchMT` · handler `acas007` · facade `GL-Batch`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 5 | `GLBATCH-REC.BATCH-KEY` | `WS-Batch-Key9` · lvl 03 · `9(6)` · DISPLAY · redefines `WS-Batch-Key` `[copybooks/wsbatch.cob:L20]` | `HV-BATCH-KEY` · `9(08)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L282]` | `BATCH-KEY` · `mediumint(6) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L81]` | no | drift: usage, digits, name; derivation: REDEFINES_ALTERNATIVE; storage: INT | `A-15`, `Q-4` |
| 6 | `GLBATCH-REC.ITEMS` | `Items` · lvl 03 · `99` · DISPLAY `[copybooks/wsbatch.cob:L23]` | `HV-ITEMS` · `9(03)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L283]` | `ITEMS` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L82]` | no | drift: usage, digits; storage: INT | `A-15`, `Q-4` |
| 7 | `GLBATCH-REC.BATCH-STATUS` | `Batch-Status` · lvl 03 · `9` · DISPLAY `[copybooks/wsbatch.cob:L25]` | `HV-BATCH-STATUS` · `9(03)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L284]` | `BATCH-STATUS` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L83]` | no | drift: usage, digits; storage: INT | `A-15`, `Q-4` |
| 8 | `GLBATCH-REC.CLEARED-STATUS` | `Cleared-Status` · lvl 03 · `9` · DISPLAY `[copybooks/wsbatch.cob:L29]` | `HV-CLEARED-STATUS` · `9(03)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L285]` | `CLEARED-STATUS` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L84]` | no | drift: usage, digits; storage: INT | `A-15`, `Q-4` |
| 9 | `GLBATCH-REC.BCYCLE` | `Bcycle` · lvl 03 · `99` · DISPLAY `[copybooks/wsbatch.cob:L34]` | `HV-BCYCLE` · `9(03)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L286]` | `BCYCLE` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L85]` | no | drift: usage, digits; storage: INT | `A-15`, `Q-4` |
| 10 | `GLBATCH-REC.ENTERED` | `Entered` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wsbatch.cob:L36]` | `HV-ENTERED` · `9(10)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L287]` | `ENTERED` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L86]` | no | drift: signedness, usage; storage: INT | `A-11`, `A-15`, `Q-3`, `Q-4` |
| 11 | `GLBATCH-REC.PROOFED` | `Proofed` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wsbatch.cob:L37]` | `HV-PROOFED` · `9(10)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L288]` | `PROOFED` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L87]` | no | drift: signedness, usage; storage: INT | `A-11`, `A-15`, `Q-3`, `Q-4` |
| 12 | `GLBATCH-REC.POSTED` | `Posted` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wsbatch.cob:L38]` | `HV-POSTED` · `9(10)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L289]` | `POSTED` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L88]` | no | drift: signedness, usage; storage: INT | `A-11`, `A-15`, `Q-3`, `Q-4` |
| 13 | `GLBATCH-REC.STORED` | `Stored` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wsbatch.cob:L39]` | `HV-STORED` · `9(10)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L290]` | `STORED` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L89]` | no | drift: signedness, usage; storage: INT | `A-11`, `A-15`, `Q-3`, `Q-4` |
| 14 | `GLBATCH-REC.INPUT-GROSS` | `Input-Gross` · lvl 05 · `9(9)v99` · COMP-3 `[copybooks/wsbatch.cob:L41]` | `HV-INPUT-GROSS` · `9(12)V9(02)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L291]` | `INPUT-GROSS` · `decimal(14,2) unsigned` · unsigned `[mysql/ACASDB.sql:L90]` | no | drift: usage, digits; storage: DECIMAL | `A-15`, `Q-4` |
| 15 | `GLBATCH-REC.INPUT-VAT` | `Input-Vat` · lvl 05 · `9(9)v99` · COMP-3 `[copybooks/wsbatch.cob:L42]` | `HV-INPUT-VAT` · `9(12)V9(02)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L292]` | `INPUT-VAT` · `decimal(14,2) unsigned` · unsigned `[mysql/ACASDB.sql:L91]` | no | drift: usage, digits; storage: DECIMAL | `A-15`, `Q-4` |
| 16 | `GLBATCH-REC.ACTUAL-GROSS` | `Actual-Gross` · lvl 05 · `9(9)v99` · COMP-3 `[copybooks/wsbatch.cob:L43]` | `HV-ACTUAL-GROSS` · `9(12)V9(02)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L293]` | `ACTUAL-GROSS` · `decimal(14,2) unsigned` · unsigned `[mysql/ACASDB.sql:L92]` | no | drift: usage, digits; storage: DECIMAL | `A-15`, `Q-4` |
| 17 | `GLBATCH-REC.ACTUAL-VAT` | `Actual-Vat` · lvl 05 · `9(9)v99` · COMP-3 `[copybooks/wsbatch.cob:L44]` | `HV-ACTUAL-VAT` · `9(12)V9(02)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L294]` | `ACTUAL-VAT` · `decimal(14,2) unsigned` · unsigned `[mysql/ACASDB.sql:L93]` | no | drift: usage, digits; storage: DECIMAL | `A-15`, `Q-4` |
| 18 | `GLBATCH-REC.DESCRIPTION` | `Description` · lvl 03 · `x(24)` `[copybooks/wsbatch.cob:L45]` | `HV-DESCRIPTION` · `X(24)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L295]` | `DESCRIPTION` · `char(24)` `[mysql/ACASDB.sql:L94]` | no | storage: STR | `A-15`, `Q-4` |
| 19 | `GLBATCH-REC.BDEFAULT` | `bDefault` · lvl 05 · `99` · DISPLAY `[copybooks/wsbatch.cob:L48]` | `HV-BDEFAULT` · `9(03)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L296]` | `BDEFAULT` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L95]` | no | drift: usage, digits; storage: INT | `A-15`, `Q-4` |
| 20 | `GLBATCH-REC.CONVENTION` | `Convention` · lvl 05 · `xx` `[copybooks/wsbatch.cob:L49]` | `HV-CONVENTION` · `X(2)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L297]` | `CONVENTION` · `char(2)` `[mysql/ACASDB.sql:L96]` | no | storage: STR | `A-15`, `Q-4` |
| 21 | `GLBATCH-REC.BATCH-DEF-AC` | `Batch-Def-AC` · lvl 05 · `9(6)` · DISPLAY `[copybooks/wsbatch.cob:L50]` | `HV-BATCH-DEF-AC` · `9(08)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L298]` | `BATCH-DEF-AC` · `mediumint(6) unsigned` · unsigned `[mysql/ACASDB.sql:L97]` | no | drift: usage, digits; storage: INT | `A-15`, `Q-4` |
| 22 | `GLBATCH-REC.BATCH-DEF-PC` | `Batch-Def-PC` · lvl 05 · `99` · DISPLAY `[copybooks/wsbatch.cob:L51]` | `HV-BATCH-DEF-PC` · `9(03)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L299]` | `BATCH-DEF-PC` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L98]` | no | drift: usage, digits; storage: INT | `A-15`, `Q-4` |
| 23 | `GLBATCH-REC.BATCH-DEF-CODE` | `Batch-Def-Code` · lvl 05 · `xx` `[copybooks/wsbatch.cob:L52]` | `HV-BATCH-DEF-CODE` · `X(2)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L300]` | `BATCH-DEF-CODE` · `char(2)` `[mysql/ACASDB.sql:L99]` | no | storage: STR | `A-15`, `Q-4` |
| 24 | `GLBATCH-REC.BATCH-DEF-VAT` | `Batch-Def-Vat` · lvl 05 · `x` `[copybooks/wsbatch.cob:L53]` | `HV-BATCH-DEF-VAT` · `X(1)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L301]` | `BATCH-DEF-VAT` · `char(1)` `[mysql/ACASDB.sql:L100]` | no | storage: STR | `A-15`, `Q-4` |
| 25 | `GLBATCH-REC.BATCH-START` | `Batch-Start` · lvl 03 · `9(5)` · DISPLAY `[copybooks/wsbatch.cob:L54]` | `HV-BATCH-START` · `9(08)` · unsigned · loaded/unloaded `[common/glbatchMT.cbl:L302]` | `BATCH-START` · `mediumint(5) unsigned` · unsigned `[mysql/ACASDB.sql:L101]` | no | drift: usage, digits; storage: INT | `A-15`, `Q-4` |

#### `GLLEDGER-REC` — 11 columns · bridge `nominalMT` · handler `acas005` · facade `GL-Nominal`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 26 | `GLLEDGER-REC.LEDGER-KEY` | `WS-Ledger-Key9` · lvl 03 · `9(8)` · DISPLAY · redefines `WS-Ledger-Key` `[copybooks/wsledger.cob:L21]` | `HV-LEDGER-KEY` · `9(10)` · unsigned · loaded/unloaded `[common/nominalMT.cbl:L295]` | `LEDGER-KEY` · `int(8) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L123]` | no | drift: usage, digits, name; derivation: REDEFINES_ALTERNATIVE; storage: INT | — |
| 27 | `GLLEDGER-REC.LEDGER-TYPE` | `Ledger-Type` · lvl 03 · `9` · DISPLAY `[copybooks/wsledger.cob:L23]` | `HV-LEDGER-TYPE` · `9(03)` · unsigned · loaded/unloaded `[common/nominalMT.cbl:L296]` | `LEDGER-TYPE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L124]` | no | drift: usage, digits; storage: INT | — |
| 28 | `GLLEDGER-REC.LEDGER-PLACE` | `Ledger-Place` · lvl 03 · `x` `[copybooks/wsledger.cob:L24]` | `HV-LEDGER-PLACE` · `X(1)` · unsigned · loaded/unloaded `[common/nominalMT.cbl:L297]` | `LEDGER-PLACE` · `char(1)` `[mysql/ACASDB.sql:L125]` | no | storage: STR | — |
| 29 | `GLLEDGER-REC.LEDGER-LEVEL` | `Ledger-Level` · lvl 03 · `9` · DISPLAY `[copybooks/wsledger.cob:L25]` | `HV-LEDGER-LEVEL` · `9(03)` · unsigned · loaded/unloaded `[common/nominalMT.cbl:L298]` | `LEDGER-LEVEL` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L126]` | no | drift: usage, digits; storage: INT | — |
| 30 | `GLLEDGER-REC.LEDGER-NAME` | `Ledger-Name` · lvl 03 · `x(24)` `[copybooks/wsledger.cob:L27]` | `HV-LEDGER-NAME` · `X(32)` · unsigned · loaded/unloaded `[common/nominalMT.cbl:L299]` | `LEDGER-NAME` · `char(32)` `[mysql/ACASDB.sql:L127]` | no | drift: character_length; storage: STR | `A-12` |
| 31 | `GLLEDGER-REC.LEDGER-BALANCE` | `Ledger-Balance` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wsledger.cob:L28]` | `HV-LEDGER-BALANCE` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/nominalMT.cbl:L300]` | `LEDGER-BALANCE` · `decimal(10,2)` `[mysql/ACASDB.sql:L128]` | no | drift: usage; storage: DECIMAL | — |
| 32 | `GLLEDGER-REC.LEDGER-LAST` | `Ledger-Last` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wsledger.cob:L29]` | `HV-LEDGER-LAST` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/nominalMT.cbl:L301]` | `LEDGER-LAST` · `decimal(10,2)` `[mysql/ACASDB.sql:L129]` | no | drift: usage; storage: DECIMAL | — |
| 33 | `GLLEDGER-REC.LEDGER-Q1` | `Ledger-Q1` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wsledger.cob:L31]` | `HV-LEDGER-Q1` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/nominalMT.cbl:L302]` | `LEDGER-Q1` · `decimal(10,2)` `[mysql/ACASDB.sql:L130]` | no | drift: usage; storage: DECIMAL | — |
| 34 | `GLLEDGER-REC.LEDGER-Q2` | `Ledger-Q2` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wsledger.cob:L32]` | `HV-LEDGER-Q2` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/nominalMT.cbl:L303]` | `LEDGER-Q2` · `decimal(10,2)` `[mysql/ACASDB.sql:L131]` | no | drift: usage; storage: DECIMAL | — |
| 35 | `GLLEDGER-REC.LEDGER-Q3` | `Ledger-Q3` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wsledger.cob:L33]` | `HV-LEDGER-Q3` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/nominalMT.cbl:L304]` | `LEDGER-Q3` · `decimal(10,2)` `[mysql/ACASDB.sql:L132]` | no | drift: usage; storage: DECIMAL | — |
| 36 | `GLLEDGER-REC.LEDGER-Q4` | `Ledger-Q4` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wsledger.cob:L34]` | `HV-LEDGER-Q4` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/nominalMT.cbl:L305]` | `LEDGER-Q4` · `decimal(10,2)` `[mysql/ACASDB.sql:L133]` | no | drift: usage; storage: DECIMAL | — |

#### `GLPOSTING-REC` — 14 columns · bridge `glpostingMT` · handler `acas006` · facade `GL-Posting`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 37 | `GLPOSTING-REC.POST-RRN` | `WS-Post-rrn` · lvl 03 · `9(5)` · DISPLAY `[copybooks/wspost.cob:L13]` | `HV-POST-RRN` · `9(08)` · unsigned · NOT loaded/NOT unloaded `[common/glpostingMT.cbl:L282]` | `POST-RRN` · `mediumint(5) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L155]` | no | drift: usage, digits, name; storage: INT | `Q-6` |
| 38 | `GLPOSTING-REC.POST-KEY` | `WS-Post-Key` · lvl 03 · GROUP · group `[copybooks/wspost.cob:L14]` | `HV-POST-KEY` · `9(18)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L283]` | `POST-KEY` · `bigint(10) unsigned` · unsigned `[mysql/ACASDB.sql:L156]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 39 | `GLPOSTING-REC.POST-CODE` | `Post-Code` · lvl 03 · `xx` `[copybooks/wspost.cob:L17]` | `HV-POST-CODE` · `X(2)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L284]` | `POST-CODE` · `char(2)` `[mysql/ACASDB.sql:L157]` | no | storage: STR | — |
| 40 | `GLPOSTING-REC.POST-DAT` | `Post-Date` · lvl 03 · `x(8)` `[copybooks/wspost.cob:L18]` | `HV-POST-DAT` · `X(8)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L285]` | `POST-DAT` · `char(8)` `[mysql/ACASDB.sql:L158]` | no | drift: name; storage: STR | — |
| 41 | `GLPOSTING-REC.POST-DR` | `Post-DR` · lvl 03 · `9(6)` · DISPLAY `[copybooks/wspost.cob:L19]` | `HV-POST-DR` · `9(08)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L286]` | `POST-DR` · `mediumint(6) unsigned` · unsigned `[mysql/ACASDB.sql:L159]` | no | drift: usage, digits; storage: INT | — |
| 42 | `GLPOSTING-REC.DR-PC` | `DR-PC` · lvl 03 · `99` · DISPLAY `[copybooks/wspost.cob:L20]` | `HV-DR-PC` · `9(03)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L287]` | `DR-PC` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L160]` | no | drift: usage, digits; storage: INT | — |
| 43 | `GLPOSTING-REC.POST-CR` | `Post-CR` · lvl 03 · `9(6)` · DISPLAY `[copybooks/wspost.cob:L21]` | `HV-POST-CR` · `9(08)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L288]` | `POST-CR` · `mediumint(6) unsigned` · unsigned `[mysql/ACASDB.sql:L161]` | no | drift: usage, digits; storage: INT | — |
| 44 | `GLPOSTING-REC.CR-PC` | `CR-PC` · lvl 03 · `99` · DISPLAY `[copybooks/wspost.cob:L22]` | `HV-CR-PC` · `9(03)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L289]` | `CR-PC` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L162]` | no | drift: usage, digits; storage: INT | — |
| 45 | `GLPOSTING-REC.POST-AMOUNT` | `Post-Amount` · lvl 03 · `s9(8)v99` · DISPLAY · signed · sign TRAILING_INCLUDED `[copybooks/wspost.cob:L23]` | `HV-POST-AMOUNT` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/glpostingMT.cbl:L290]` | `POST-AMOUNT` · `decimal(10,2)` `[mysql/ACASDB.sql:L163]` | no | drift: usage; storage: DECIMAL | — |
| 46 | `GLPOSTING-REC.POST-LEGEND` | `Post-Legend` · lvl 03 · `x(32)` `[copybooks/wspost.cob:L24]` | `HV-POST-LEGEND` · `X(32)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L291]` | `POST-LEGEND` · `char(32)` `[mysql/ACASDB.sql:L164]` | no | storage: STR | — |
| 47 | `GLPOSTING-REC.VAT-AC` | `Vat-AC` · lvl 03 · `9(6)` · DISPLAY `[copybooks/wspost.cob:L25]` | `HV-VAT-AC` · `9(08)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L292]` | `VAT-AC` · `mediumint(6) unsigned` · unsigned `[mysql/ACASDB.sql:L165]` | no | drift: usage, digits; storage: INT | — |
| 48 | `GLPOSTING-REC.VAT-PC` | `Vat-PC` · lvl 03 · `99` · DISPLAY `[copybooks/wspost.cob:L26]` | `HV-VAT-PC` · `9(03)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L293]` | `VAT-PC` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L166]` | no | drift: usage, digits; storage: INT | — |
| 49 | `GLPOSTING-REC.POST-VAT-SIDE` | `Post-Vat-Side` · lvl 03 · `xx` `[copybooks/wspost.cob:L27]` | `HV-POST-VAT-SIDE` · `X(2)` · unsigned · loaded/unloaded `[common/glpostingMT.cbl:L294]` | `POST-VAT-SIDE` · `char(2)` `[mysql/ACASDB.sql:L167]` | no | storage: STR | — |
| 50 | `GLPOSTING-REC.VAT-AMOUNT` | `Vat-Amount` · lvl 03 · `s9(8)v99` · DISPLAY · signed · sign TRAILING_INCLUDED `[copybooks/wspost.cob:L28]` | `HV-VAT-AMOUNT` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/glpostingMT.cbl:L295]` | `VAT-AMOUNT` · `decimal(10,2)` `[mysql/ACASDB.sql:L168]` | no | drift: usage; storage: DECIMAL | — |

#### `IRSDFLT-REC` — 4 columns · bridge `irsdfltMT` · handler `acasirsub3` · facade `IRS defaults`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 51 | `IRSDFLT-REC.DEF-REC-KEY` | **absent** | `HV-DEF-REC-KEY` · `9(03)` · unsigned · loaded/unloaded `[common/irsdfltMT.cbl:L324]` | `DEF-REC-KEY` · `tinyint(2) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L190]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 52 | `IRSDFLT-REC.DEF-ACS` | `Def-Acs` · lvl 05 · `9(5)` · DISPLAY `[copybooks/irswsdflt.cob:L10]` | `HV-DEF-ACS` · `9(05)` · unsigned · loaded/unloaded `[common/irsdfltMT.cbl:L325]` | `DEF-ACS` · `decimal(5,0) unsigned` · unsigned `[mysql/ACASDB.sql:L191]` | no | drift: usage; derivation: BRIDGE_DERIVED guarded on `if Def-Acs (A) numeric`; storage: INT | — |
| 53 | `IRSDFLT-REC.DEF-CODES` | `Def-Codes` · lvl 05 · `xx` `[copybooks/irswsdflt.cob:L11]` | `HV-DEF-CODES` · `X(2)` · unsigned · loaded/unloaded `[common/irsdfltMT.cbl:L326]` | `DEF-CODES` · `char(2)` `[mysql/ACASDB.sql:L192]` | no | storage: STR | — |
| 54 | `IRSDFLT-REC.DEF-VAT` | `Def-Vat` · lvl 05 · `x` `[copybooks/irswsdflt.cob:L12]` | `HV-DEF-VAT` · `X(1)` · unsigned · loaded/unloaded `[common/irsdfltMT.cbl:L327]` | `DEF-VAT` · `char(1)` `[mysql/ACASDB.sql:L193]` | no | storage: STR | — |

#### `IRSFINAL-REC` — 3 columns · bridge `irsfinalMT` · handler `acasirsub5` · facade `IRS final`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 55 | `IRSFINAL-REC.IRS-FINAL-ACC-REC-KEY` | **absent** | `HV-IRS-FINAL-ACC-REC-KEY` · `9(03)` · unsigned · loaded/unloaded `[common/irsfinalMT.cbl:L172]` | `IRS-FINAL-ACC-REC-KEY` · `tinyint(2) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L215]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 56 | `IRSFINAL-REC.IRS-AR1` | `ar1` · lvl 05 · `x(24)` · occurs 26 `[copybooks/irswsfinal.cob:L36]` | `HV-IRS-AR1` · `X(24)` · unsigned · loaded/unloaded `[common/irsfinalMT.cbl:L173]` | `IRS-AR1` · `char(24)` `[mysql/ACASDB.sql:L216]` | no | drift: name; derivation: REDEFINES_ALTERNATIVE; storage: STR | — |
| 57 | `IRSFINAL-REC.IRS-AR2` | `ar2` · lvl 05 · `x` · occurs 26 `[copybooks/irswsfinal.cob:L66]` | `HV-IRS-AR2` · `X(1)` · unsigned · loaded/unloaded `[common/irsfinalMT.cbl:L174]` | `IRS-AR2` · `char(1)` `[mysql/ACASDB.sql:L217]` | no | drift: name; derivation: REDEFINES_ALTERNATIVE; storage: STR | — |

#### `IRSNL-REC` — 15 columns · bridge `irsnominalMT` · handler `acasirsub1` · facade `IRS nominal`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 58 | `IRSNL-REC.KEY-1` | `NL-Key` · lvl 03 · GROUP · group `[copybooks/irswsnl.cob:L9]` | `HV-KEY-1` · `9(18)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L195]` | `KEY-1` · `bigint(10) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L239]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 59 | `IRSNL-REC.TIPE` | `NL-Type` · lvl 03 · `x` `[copybooks/irswsnl.cob:L12]` | `HV-TIPE` · `X(1)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L196]` | `TIPE` · `char(1)` `[mysql/ACASDB.sql:L240]` | no | drift: name; storage: STR | — |
| 60 | `IRSNL-REC.NL-NAME` | `NL-Name` · lvl 05 · `x(24)` `[copybooks/irswsnl.cob:L16]` | `HV-NL-NAME` · `X(24)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L197]` | `NL-NAME` · `char(24)` `[mysql/ACASDB.sql:L241]` | no | derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: STR | — |
| 61 | `IRSNL-REC.DR` | `NL-DR` · lvl 05 · `9(8)v99` · COMP `[copybooks/irswsnl.cob:L17]` | `HV-DR` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L198]` | `DR` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L242]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: DECIMAL | — |
| 62 | `IRSNL-REC.CR` | `NL-CR` · lvl 05 · `9(8)v99` · COMP `[copybooks/irswsnl.cob:L18]` | `HV-CR` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L199]` | `CR` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L243]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: DECIMAL | — |
| 63 | `IRSNL-REC.DR-LAST-01` | `NL-DR-Last` · lvl 05 · `9(8)v99` · COMP · occurs 4 `[copybooks/irswsnl.cob:L19]` | `HV-DR-LAST-01` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L200]` | `DR-LAST-01` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L244]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: DECIMAL | — |
| 64 | `IRSNL-REC.CR-LAST-01` | `NL-CR-Last` · lvl 05 · `9(8)v99` · COMP · occurs 4 `[copybooks/irswsnl.cob:L20]` | `HV-CR-LAST-01` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L201]` | `CR-LAST-01` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L245]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: DECIMAL | — |
| 65 | `IRSNL-REC.DR-LAST-02` | `NL-DR-Last` · lvl 05 · `9(8)v99` · COMP · occurs 4 `[copybooks/irswsnl.cob:L19]` | `HV-DR-LAST-02` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L202]` | `DR-LAST-02` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L246]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: DECIMAL | — |
| 66 | `IRSNL-REC.CR-LAST-02` | `NL-CR-Last` · lvl 05 · `9(8)v99` · COMP · occurs 4 `[copybooks/irswsnl.cob:L20]` | `HV-CR-LAST-02` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L203]` | `CR-LAST-02` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L247]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: DECIMAL | — |
| 67 | `IRSNL-REC.DR-LAST-03` | `NL-DR-Last` · lvl 05 · `9(8)v99` · COMP · occurs 4 `[copybooks/irswsnl.cob:L19]` | `HV-DR-LAST-03` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L204]` | `DR-LAST-03` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L248]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: DECIMAL | — |
| 68 | `IRSNL-REC.CR-LAST-03` | `NL-CR-Last` · lvl 05 · `9(8)v99` · COMP · occurs 4 `[copybooks/irswsnl.cob:L20]` | `HV-CR-LAST-03` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L205]` | `CR-LAST-03` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L249]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: DECIMAL | — |
| 69 | `IRSNL-REC.DR-LAST-04` | `NL-DR-Last` · lvl 05 · `9(8)v99` · COMP · occurs 4 `[copybooks/irswsnl.cob:L19]` | `HV-DR-LAST-04` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L206]` | `DR-LAST-04` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L250]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: DECIMAL | — |
| 70 | `IRSNL-REC.CR-LAST-04` | `NL-CR-Last` · lvl 05 · `9(8)v99` · COMP · occurs 4 `[copybooks/irswsnl.cob:L20]` | `HV-CR-LAST-04` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L207]` | `CR-LAST-04` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L251]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: DECIMAL | — |
| 71 | `IRSNL-REC.AC` | `NL-AC` · lvl 05 · `x` `[copybooks/irswsnl.cob:L21]` | `HV-AC` · `X(1)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L208]` | `AC` · `char(1)` `[mysql/ACASDB.sql:L252]` | no | drift: name; derivation: BRIDGE_DERIVED guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: STR | — |
| 72 | `IRSNL-REC.REC-POINTER` | `NL-Pointer` · lvl 05 · `9(5)` · DISPLAY `[copybooks/irswsnl.cob:L23]` | `HV-REC-POINTER` · `9(08)` · unsigned · loaded/unloaded `[common/irsnominalMT.cbl:L209]` | `REC-POINTER` · `mediumint(5) unsigned` · unsigned `[mysql/ACASDB.sql:L253]` | no | drift: usage, digits, name; derivation: REDEFINES_ALTERNATIVE guarded on `if NL-Pointer numeric and NL-Pointer > zero`; storage: INT | — |

#### `IRSPOSTING-REC` — 13 columns · bridge `irspostingMT` · handler `acasirsub4` · facade `IRS posting`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 73 | `IRSPOSTING-REC.KEY-4` | `Post-Key` · lvl 03 · `9(5)` · DISPLAY `[copybooks/irswspost.cob:L9]` | `HV-KEY-4` · `9(08)` · unsigned · loaded/unloaded `[common/irspostingMT.cbl:L174]` | `KEY-4` · `mediumint(5) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L275]` | no | drift: usage, digits, name; storage: INT | — |
| 74 | `IRSPOSTING-REC.POST4-CODE` | `Post-Code` · lvl 03 · `xx` `[copybooks/irswspost.cob:L10]` | `HV-POST4-CODE` · `X(2)` · unsigned · loaded/unloaded `[common/irspostingMT.cbl:L175]` | `POST4-CODE` · `char(2)` `[mysql/ACASDB.sql:L276]` | no | drift: name; storage: STR | — |
| 75 | `IRSPOSTING-REC.POST4-DAT` | `Post-Date` · lvl 03 · `x(8)` `[copybooks/irswspost.cob:L11]` | `HV-POST4-DAT` · `X(8)` · unsigned · loaded/unloaded `[common/irspostingMT.cbl:L176]` | `POST4-DAT` · `char(8)` `[mysql/ACASDB.sql:L277]` | no | drift: name; storage: STR | — |
| 76 | `IRSPOSTING-REC.POST4-DAY` | **absent** | `HV-POST4-DAY` · `9(03)` · unsigned · loaded/NOT unloaded `[common/irspostingMT.cbl:L177]` | `POST4-DAY` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L278]` | **yes** | derivation: BRIDGE_DERIVED guarded on `if Post-Date (1:2) numeric` | `A-7` |
| 77 | `IRSPOSTING-REC.POST4-MONTH` | **absent** | `HV-POST4-MONTH` · `9(03)` · unsigned · loaded/NOT unloaded `[common/irspostingMT.cbl:L178]` | `POST4-MONTH` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L279]` | **yes** | derivation: BRIDGE_DERIVED guarded on `if Post-Date (4:2) numeric` | `A-7` |
| 78 | `IRSPOSTING-REC.POST4-YEAR` | **absent** | `HV-POST4-YEAR` · `9(03)` · unsigned · loaded/NOT unloaded `[common/irspostingMT.cbl:L179]` | `POST4-YEAR` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L280]` | **yes** | derivation: BRIDGE_DERIVED guarded on `if Post-Date (7:2) numeric` | `A-7` |
| 79 | `IRSPOSTING-REC.POST4-DR` | `Post-DR` · lvl 03 · `9(5)` · DISPLAY `[copybooks/irswspost.cob:L12]` | `HV-POST4-DR` · `9(08)` · unsigned · loaded/unloaded `[common/irspostingMT.cbl:L180]` | `POST4-DR` · `mediumint(5) unsigned` · unsigned `[mysql/ACASDB.sql:L281]` | no | drift: usage, digits, name; storage: INT | — |
| 80 | `IRSPOSTING-REC.POST4-CR` | `Post-CR` · lvl 03 · `9(5)` · DISPLAY `[copybooks/irswspost.cob:L13]` | `HV-POST4-CR` · `9(08)` · unsigned · loaded/unloaded `[common/irspostingMT.cbl:L181]` | `POST4-CR` · `mediumint(5) unsigned` · unsigned `[mysql/ACASDB.sql:L282]` | no | drift: usage, digits, name; storage: INT | — |
| 81 | `IRSPOSTING-REC.POST4-AMOUNT` | `Post-Amount` · lvl 03 · `s9(7)v99` · DISPLAY · signed · sign LEADING_INCLUDED `[copybooks/irswspost.cob:L14]` | `HV-POST4-AMOUNT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/irspostingMT.cbl:L182]` | `POST4-AMOUNT` · `decimal(9,2)` `[mysql/ACASDB.sql:L283]` | no | drift: usage, name; storage: DECIMAL | — |
| 82 | `IRSPOSTING-REC.POST4-LEGEND` | `Post-Legend` · lvl 03 · `x(32)` `[copybooks/irswspost.cob:L15]` | `HV-POST4-LEGEND` · `X(32)` · unsigned · loaded/unloaded `[common/irspostingMT.cbl:L183]` | `POST4-LEGEND` · `char(32)` `[mysql/ACASDB.sql:L284]` | no | drift: name; storage: STR | — |
| 83 | `IRSPOSTING-REC.VAT-AC-DEF4` | `Vat-AC-Def` · lvl 03 · `99` · DISPLAY `[copybooks/irswspost.cob:L16]` | `HV-VAT-AC-DEF4` · `9(03)` · unsigned · loaded/unloaded `[common/irspostingMT.cbl:L184]` | `VAT-AC-DEF4` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L285]` | no | drift: usage, digits, name; storage: INT | — |
| 84 | `IRSPOSTING-REC.POST4-VAT-SIDE` | `Post-Vat-Side` · lvl 03 · `xx` `[copybooks/irswspost.cob:L17]` | `HV-POST4-VAT-SIDE` · `X(2)` · unsigned · loaded/unloaded `[common/irspostingMT.cbl:L185]` | `POST4-VAT-SIDE` · `char(2)` `[mysql/ACASDB.sql:L286]` | no | drift: name; storage: STR | — |
| 85 | `IRSPOSTING-REC.VAT-AMOUNT4` | `Vat-Amount` · lvl 03 · `s9(7)v99` · DISPLAY · signed · sign LEADING_INCLUDED `[copybooks/irswspost.cob:L18]` | `HV-VAT-AMOUNT4` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/irspostingMT.cbl:L186]` | `VAT-AMOUNT4` · `decimal(9,2)` `[mysql/ACASDB.sql:L287]` | no | drift: usage, name; storage: DECIMAL | — |

#### `PSIRSPOST-REC` — 10 columns · bridge `slpostingMT` · handler `acas008` · facade `SPL-Posting`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 86 | `PSIRSPOST-REC.IRS-POST-KEY` | `WS-IRS-Post-Key` · lvl 03 · GROUP · group `[copybooks/wspost-irs.cob:L14]` | `HV-IRS-POST-KEY` · `S9(18)` · signed · loaded/unloaded `[common/slpostingMT.cbl:L266]` | `IRS-POST-KEY` · `bigint(11)` · **PK** `[mysql/ACASDB.sql:L367]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 87 | `PSIRSPOST-REC.IRS-POST-CODE` | `WS-IRS-Post-Code` · lvl 03 · `xx` `[copybooks/wspost-irs.cob:L17]` | `HV-IRS-POST-CODE` · `X(2)` · unsigned · loaded/unloaded `[common/slpostingMT.cbl:L267]` | `IRS-POST-CODE` · `char(2)` `[mysql/ACASDB.sql:L368]` | no | drift: name; storage: STR | — |
| 88 | `PSIRSPOST-REC.IRS-POST-DAT` | `WS-IRS-Post-Date` · lvl 03 · `x(8)` `[copybooks/wspost-irs.cob:L18]` | `HV-IRS-POST-DAT` · `X(8)` · unsigned · loaded/unloaded `[common/slpostingMT.cbl:L268]` | `IRS-POST-DAT` · `char(8)` `[mysql/ACASDB.sql:L369]` | no | drift: name; storage: STR | — |
| 89 | `PSIRSPOST-REC.IRS-POST-DR` | `WS-IRS-Post-DR` · lvl 03 · `9(5)` · DISPLAY `[copybooks/wspost-irs.cob:L19]` | `HV-IRS-POST-DR` · `9(10)` · unsigned · loaded/unloaded `[common/slpostingMT.cbl:L269]` | `IRS-POST-DR` · `int(5) unsigned` · unsigned `[mysql/ACASDB.sql:L370]` | no | drift: usage, digits, name; storage: INT | — |
| 90 | `PSIRSPOST-REC.IRS-POST-CR` | `WS-IRS-Post-CR` · lvl 03 · `9(5)` · DISPLAY `[copybooks/wspost-irs.cob:L20]` | `HV-IRS-POST-CR` · `9(10)` · unsigned · loaded/unloaded `[common/slpostingMT.cbl:L270]` | `IRS-POST-CR` · `int(5) unsigned` · unsigned `[mysql/ACASDB.sql:L371]` | no | drift: usage, digits, name; storage: INT | — |
| 91 | `PSIRSPOST-REC.IRS-POST-AMOUNT` | `WS-IRS-Post-Amount` · lvl 03 · `s9(7)v99` · DISPLAY · signed · sign LEADING_INCLUDED `[copybooks/wspost-irs.cob:L21]` | `HV-IRS-POST-AMOUNT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slpostingMT.cbl:L271]` | `IRS-POST-AMOUNT` · `decimal(9,2)` `[mysql/ACASDB.sql:L372]` | no | drift: usage, name; storage: DECIMAL | — |
| 92 | `PSIRSPOST-REC.IRS-POST-LEGEND` | `WS-IRS-Post-Legend` · lvl 03 · `x(32)` `[copybooks/wspost-irs.cob:L22]` | `HV-IRS-POST-LEGEND` · `X(32)` · unsigned · loaded/unloaded `[common/slpostingMT.cbl:L272]` | `IRS-POST-LEGEND` · `char(32)` `[mysql/ACASDB.sql:L373]` | no | drift: name; storage: STR | — |
| 93 | `PSIRSPOST-REC.IRS-VAT-AC-DEF` | `WS-IRS-Vat-AC-Def` · lvl 03 · `99` · DISPLAY `[copybooks/wspost-irs.cob:L23]` | `HV-IRS-VAT-AC-DEF` · `9(03)` · unsigned · loaded/unloaded `[common/slpostingMT.cbl:L273]` | `IRS-VAT-AC-DEF` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L374]` | no | drift: usage, digits, name; storage: INT | — |
| 94 | `PSIRSPOST-REC.IRS-POST-VAT-SIDE` | `WS-IRS-Post-Vat-Side` · lvl 03 · `xx` `[copybooks/wspost-irs.cob:L24]` | `HV-IRS-POST-VAT-SIDE` · `X(2)` · unsigned · loaded/unloaded `[common/slpostingMT.cbl:L274]` | `IRS-POST-VAT-SIDE` · `char(2)` `[mysql/ACASDB.sql:L375]` | no | drift: name; storage: STR | — |
| 95 | `PSIRSPOST-REC.IRS-VAT-AMOUNT` | `WS-IRS-Vat-Amount` · lvl 03 · `s9(7)v99` · DISPLAY · signed · sign LEADING_INCLUDED `[copybooks/wspost-irs.cob:L25]` | `HV-IRS-VAT-AMOUNT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slpostingMT.cbl:L275]` | `IRS-VAT-AMOUNT` · `decimal(9,2)` `[mysql/ACASDB.sql:L376]` | no | drift: usage, name; storage: DECIMAL | — |

#### `PUINV-LINES-REC` — 14 columns · bridge `plinvoiceMT` · handler `acas026` · facade `PInvoice`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 96 | `PUINV-LINES-REC.IL-LINE-KEY` | `il-Key` · lvl 05 · GROUP · group `[copybooks/plwspinv.cob:L67]` | `HV1-IL-LINE-KEY` · `X(10)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L426]` | `IL-LINE-KEY` · `char(10)` · **PK** `[mysql/ACASDB.sql:L511]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 97 | `PUINV-LINES-REC.IL-INVOICE` | `il-invoice` · lvl 07 · `9(8)` · DISPLAY `[copybooks/plwspinv.cob:L68]` | `HV1-IL-INVOICE` · `9(10)` · unsigned · loaded/NOT unloaded `[common/plinvoiceMT.cbl:L427]` | `IL-INVOICE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L512]` | no | drift: usage, digits; storage: INT | — |
| 98 | `PUINV-LINES-REC.IL-LINE` | `il-line` · lvl 07 · `99` · DISPLAY `[copybooks/plwspinv.cob:L69]` | `HV1-IL-LINE` · `9(03)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L428]` | `IL-LINE` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L513]` | no | drift: usage, digits; storage: INT | — |
| 99 | `PUINV-LINES-REC.IL-PRODUCT` | `il-product` · lvl 05 · `x(13)` `[copybooks/plwspinv.cob:L70]` | `HV1-IL-PRODUCT` · `X(13)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L429]` | `IL-PRODUCT` · `char(13)` `[mysql/ACASDB.sql:L514]` | no | storage: STR | — |
| 100 | `PUINV-LINES-REC.IL-PA` | `il-pa` · lvl 05 · `xx` `[copybooks/plwspinv.cob:L71]` | `HV1-IL-PA` · `X(2)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L430]` | `IL-PA` · `char(2)` `[mysql/ACASDB.sql:L515]` | no | storage: STR | — |
| 101 | `PUINV-LINES-REC.IL-QTY` | `il-qty` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L73]` | `HV1-IL-QTY` · `9(05)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L431]` | `IL-QTY` · `smallint(6) unsigned` · unsigned `[mysql/ACASDB.sql:L516]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 102 | `PUINV-LINES-REC.IL-TYPE` | `il-type` · lvl 05 · `x` `[copybooks/plwspinv.cob:L74]` | `HV1-IL-TYPE` · `X(1)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L432]` | `IL-TYPE` · `char(1)` `[mysql/ACASDB.sql:L517]` | no | storage: STR | — |
| 103 | `PUINV-LINES-REC.IL-DESCRIPTION` | `il-description` · lvl 05 · `x(24)` `[copybooks/plwspinv.cob:L75]` | `HV1-IL-DESCRIPTION` · `X(24)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L433]` | `IL-DESCRIPTION` · `char(24)` `[mysql/ACASDB.sql:L518]` | no | storage: STR | — |
| 104 | `PUINV-LINES-REC.IL-NET` | `il-net` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L77]` | `HV1-IL-NET` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L434]` | `IL-NET` · `decimal(9,2)` `[mysql/ACASDB.sql:L519]` | no | drift: usage; storage: DECIMAL | — |
| 105 | `PUINV-LINES-REC.IL-UNIT` | `il-unit` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L78]` | `HV1-IL-UNIT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L435]` | `IL-UNIT` · `decimal(9,2)` `[mysql/ACASDB.sql:L520]` | no | drift: usage; storage: DECIMAL | — |
| 106 | `PUINV-LINES-REC.IL-DISCOUNT` | `il-discount` · lvl 05 · `99v99` · COMP `[copybooks/plwspinv.cob:L79]` | `HV1-IL-DISCOUNT` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L436]` | `IL-DISCOUNT` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L521]` | no | storage: DECIMAL | — |
| 107 | `PUINV-LINES-REC.IL-VAT` | `il-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L80]` | `HV1-IL-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L437]` | `IL-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L522]` | no | drift: usage; storage: DECIMAL | — |
| 108 | `PUINV-LINES-REC.IL-VAT-CODE` | `il-vat-code` · lvl 05 · `9` · DISPLAY `[copybooks/plwspinv.cob:L81]` | `HV1-IL-VAT-CODE` · `9(03)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L438]` | `IL-VAT-CODE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L523]` | no | drift: usage, digits; storage: INT | — |
| 109 | `PUINV-LINES-REC.IL-UPDATE` | `il-update` · lvl 05 · `x` `[copybooks/plwspinv.cob:L82]` | `HV1-IL-UPDATE` · `X(1)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L439]` | `IL-UPDATE` · `char(1)` `[mysql/ACASDB.sql:L524]` | no | storage: STR | — |

#### `PUINVOICE-REC` — 30 columns · bridge `plinvoiceMT` · handler `acas026` · facade `PInvoice`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 110 | `PUINVOICE-REC.PINVOICE-KEY` | `WS-Invoice-Key` · lvl 05 · GROUP · group `[copybooks/plwspinv.cob:L10]` | `HV-PINVOICE-KEY` · `X(10)` · unsigned · loaded/NOT unloaded `[common/plinvoiceMT.cbl:L391]` | `PINVOICE-KEY` · `char(10)` · **PK** `[mysql/ACASDB.sql:L546]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 111 | `PUINVOICE-REC.IH-INVOICE` | `ih-Invoice` · lvl 07 · `9(8)` · DISPLAY `[copybooks/plwspinv.cob:L11]` | `HV-IH-INVOICE` · `9(10)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L392]` | `IH-INVOICE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L547]` | no | drift: usage, digits; storage: INT | — |
| 112 | `PUINVOICE-REC.IH-TEST` | `ih-Test` · lvl 07 · `99` · DISPLAY `[copybooks/plwspinv.cob:L12]` | `HV-IH-TEST` · `9(03)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L393]` | `IH-TEST` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L548]` | no | drift: usage, digits; storage: INT | — |
| 113 | `PUINVOICE-REC.IH-SUPPLIER` | `ih-Supplier` · lvl 05 · GROUP · group `[copybooks/plwspinv.cob:L13]` | `HV-IH-SUPPLIER` · `X(7)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L394]` | `IH-SUPPLIER` · `char(7)` `[mysql/ACASDB.sql:L549]` | no | derivation: GROUP_CONCATENATION | — |
| 114 | `PUINVOICE-REC.IH-DAT` | `ih-Date` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L16]` | `HV-IH-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L395]` | `IH-DAT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L550]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 115 | `PUINVOICE-REC.IH-ORDER` | `ih-order` · lvl 05 · GROUP · group `[copybooks/plwspinv.cob:L17]` | `HV-IH-ORDER` · `X(10)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L396]` | `IH-ORDER` · `char(10)` `[mysql/ACASDB.sql:L551]` | no | derivation: GROUP_CONCATENATION | — |
| 116 | `PUINVOICE-REC.IH-TYPE` | `ih-Type` · lvl 05 · `9` · DISPLAY `[copybooks/plwspinv.cob:L28]` | `HV-IH-TYPE` · `9(03)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L397]` | `IH-TYPE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L552]` | no | drift: usage, digits; storage: INT | — |
| 117 | `PUINVOICE-REC.IH-REF` | `ih-Ref` · lvl 05 · `x(10)` `[copybooks/plwspinv.cob:L29]` | `HV-IH-REF` · `X(10)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L398]` | `IH-REF` · `char(10)` `[mysql/ACASDB.sql:L553]` | no | storage: STR | — |
| 118 | `PUINVOICE-REC.IH-P-C` | `ih-p-c` · lvl 07 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L32]` | `HV-IH-P-C` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L399]` | `IH-P-C` · `decimal(9,2)` `[mysql/ACASDB.sql:L554]` | no | drift: usage; storage: DECIMAL | — |
| 119 | `PUINVOICE-REC.IH-NET` | `ih-net` · lvl 07 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L33]` | `HV-IH-NET` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L400]` | `IH-NET` · `decimal(9,2)` `[mysql/ACASDB.sql:L555]` | no | drift: usage; storage: DECIMAL | — |
| 120 | `PUINVOICE-REC.IH-EXTRA` | `ih-extra` · lvl 07 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L34]` | `HV-IH-EXTRA` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L401]` | `IH-EXTRA` · `decimal(9,2)` `[mysql/ACASDB.sql:L556]` | no | drift: usage; storage: DECIMAL | — |
| 121 | `PUINVOICE-REC.IH-CARRIAGE` | `ih-carriage` · lvl 07 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L35]` | `HV-IH-CARRIAGE` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L402]` | `IH-CARRIAGE` · `decimal(9,2)` `[mysql/ACASDB.sql:L557]` | no | drift: usage; storage: DECIMAL | — |
| 122 | `PUINVOICE-REC.IH-VAT` | `ih-vat` · lvl 07 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L36]` | `HV-IH-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L403]` | `IH-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L558]` | no | drift: usage; storage: DECIMAL | — |
| 123 | `PUINVOICE-REC.IH-DISCOUNT` | `ih-discount` · lvl 07 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L37]` | `HV-IH-DISCOUNT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L404]` | `IH-DISCOUNT` · `decimal(9,2)` `[mysql/ACASDB.sql:L559]` | no | drift: usage; storage: DECIMAL | — |
| 124 | `PUINVOICE-REC.IH-E-VAT` | `ih-e-vat` · lvl 07 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L38]` | `HV-IH-E-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L405]` | `IH-E-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L560]` | no | drift: usage; storage: DECIMAL | — |
| 125 | `PUINVOICE-REC.IH-C-VAT` | `ih-c-vat` · lvl 07 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L39]` | `HV-IH-C-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/plinvoiceMT.cbl:L406]` | `IH-C-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L561]` | no | drift: usage; storage: DECIMAL | — |
| 126 | `PUINVOICE-REC.IH-STATUS` | `ih-status` · lvl 05 · `x` `[copybooks/plwspinv.cob:L40]` | `HV-IH-STATUS` · `X(1)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L407]` | `IH-STATUS` · `char(1)` `[mysql/ACASDB.sql:L562]` | no | storage: STR | — |
| 127 | `PUINVOICE-REC.IH-STATUS-A` | **absent** | `HV-IH-STATUS-A` · `X(1)` · unsigned · NOT loaded/NOT unloaded `[common/plinvoiceMT.cbl:L408]` | `IH-STATUS-A` · `char(1)` `[mysql/ACASDB.sql:L563]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 128 | `PUINVOICE-REC.IH-STATUS-C` | **absent** | `HV-IH-STATUS-C` · `X(1)` · unsigned · NOT loaded/NOT unloaded `[common/plinvoiceMT.cbl:L409]` | `IH-STATUS-C` · `char(1)` `[mysql/ACASDB.sql:L564]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 129 | `PUINVOICE-REC.IH-STATUS-I` | **absent** | `HV-IH-STATUS-I` · `X(1)` · unsigned · NOT loaded/NOT unloaded `[common/plinvoiceMT.cbl:L410]` | `IH-STATUS-I` · `char(1)` `[mysql/ACASDB.sql:L565]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 130 | `PUINVOICE-REC.IH-STATUS-L` | **absent** | `HV-IH-STATUS-L` · `X(1)` · unsigned · NOT loaded/NOT unloaded `[common/plinvoiceMT.cbl:L411]` | `IH-STATUS-L` · `char(1)` `[mysql/ACASDB.sql:L566]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 131 | `PUINVOICE-REC.IH-STATUS-P` | **absent** | `HV-IH-STATUS-P` · `X(1)` · unsigned · NOT loaded/NOT unloaded `[common/plinvoiceMT.cbl:L412]` | `IH-STATUS-P` · `char(1)` `[mysql/ACASDB.sql:L567]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 132 | `PUINVOICE-REC.IH-DEDUCT-DAYS` | `ih-deduct-days` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L45]` | `HV-IH-DEDUCT-DAYS` · `9(03)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L413]` | `IH-DEDUCT-DAYS` · `tinyint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L568]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 133 | `PUINVOICE-REC.IH-DEDUCT-AMT` | `ih-deduct-amt` · lvl 05 · `999v99` · COMP `[copybooks/plwspinv.cob:L46]` | `HV-IH-DEDUCT-AMT` · `9(03)V9(02)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L414]` | `IH-DEDUCT-AMT` · `decimal(5,2) unsigned` · unsigned `[mysql/ACASDB.sql:L569]` | no | storage: DECIMAL | — |
| 134 | `PUINVOICE-REC.IH-DEDUCT-VAT` | `ih-deduct-vat` · lvl 05 · `999v99` · COMP `[copybooks/plwspinv.cob:L47]` | `HV-IH-DEDUCT-VAT` · `9(03)V9(02)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L415]` | `IH-DEDUCT-VAT` · `decimal(5,2) unsigned` · unsigned `[mysql/ACASDB.sql:L570]` | no | storage: DECIMAL | — |
| 135 | `PUINVOICE-REC.IH-DAYS` | `ih-days` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L48]` | `HV-IH-DAYS` · `9(03)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L416]` | `IH-DAYS` · `tinyint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L571]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 136 | `PUINVOICE-REC.IH-CR` | `ih-cr` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L49]` | `HV-IH-CR` · `9(10)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L417]` | `IH-CR` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L572]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 137 | `PUINVOICE-REC.IH-LINES` | `ih-lines` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L44]` | `HV-IH-LINES` · `9(03)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L418]` | `IH-LINES` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L573]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 138 | `PUINVOICE-REC.IH-DAY-BOOK-FLAG` | `ih-day-book-flag` · lvl 05 · `x` `[copybooks/plwspinv.cob:L50]` | `HV-IH-DAY-BOOK-FLAG` · `X(1)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L419]` | `IH-DAY-BOOK-FLAG` · `char(1)` `[mysql/ACASDB.sql:L574]` | no | storage: STR | — |
| 139 | `PUINVOICE-REC.IH-UPDATE` | `ih-update` · lvl 05 · `x` `[copybooks/plwspinv.cob:L52]` | `HV-IH-UPDATE` · `X(1)` · unsigned · loaded/unloaded `[common/plinvoiceMT.cbl:L420]` | `IH-UPDATE` · `char(1)` `[mysql/ACASDB.sql:L575]` | no | storage: STR | — |

#### `PUITM5-REC` — 29 columns · bridge `otm5MT` · handler `acas029` · facade `OTM5`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 140 | `PUITM5-REC.OI5-KEY` | `oi5-key` · lvl 03 · GROUP · group `[copybooks/plwsoi5B.cob:L13]` | `HV-OI5-KEY` · `X(15)` · unsigned · loaded/NOT unloaded `[common/otm5MT.cbl:L304]` | `OI5-KEY` · `char(15)` · **PK** `[mysql/ACASDB.sql:L597]` | no | derivation: GROUP_CONCATENATION | — |
| 141 | `PUITM5-REC.OI5-SUPPLIER` | `OI-Supplier` · lvl 07 · GROUP · group `[copybooks/plwsoi.cob:L15]` | `HV-OI5-SUPPLIER` · `X(7)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L305]` | `OI5-SUPPLIER` · `char(7)` `[mysql/ACASDB.sql:L598]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 142 | `PUITM5-REC.OI5-INVOICE` | `OI-Invoice` · lvl 05 · `9(8)` · DISPLAY `[copybooks/plwsoi.cob:L18]` | `HV-OI5-INVOICE` · `9(10)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L306]` | `OI5-INVOICE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L599]` | no | drift: usage, digits, name; storage: INT | — |
| 143 | `PUITM5-REC.OI5-DAT` | `OI-Date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L19]` | `HV-OI5-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L307]` | `OI5-DAT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L600]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 144 | `PUITM5-REC.OI5-BATCH` | `OI-Batch` · lvl 03 · GROUP · group `[copybooks/plwsoi.cob:L20]` | `HV-OI5-BATCH` · `X(8)` · unsigned · loaded/NOT unloaded `[common/otm5MT.cbl:L308]` | `OI5-BATCH` · `char(8)` `[mysql/ACASDB.sql:L601]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 145 | `PUITM5-REC.OI5-BATCH-NOS` | `OI-B-Nos` · lvl 05 · `9(5)` · COMP `[copybooks/plwsoi.cob:L21]` | `HV-OI5-BATCH-NOS` · `X(5)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L309]` | `OI5-BATCH-NOS` · `char(5)` `[mysql/ACASDB.sql:L602]` | no | drift: usage, name; storage: INT | — |
| 146 | `PUITM5-REC.OI5-BATCH-ITEM` | `OI-B-Item` · lvl 05 · `999` · COMP `[copybooks/plwsoi.cob:L22]` | `HV-OI5-BATCH-ITEM` · `X(3)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L310]` | `OI5-BATCH-ITEM` · `char(3)` `[mysql/ACASDB.sql:L603]` | no | drift: usage, name; storage: INT | — |
| 147 | `PUITM5-REC.OI5-TYPE` | `OI-Type` · lvl 03 · `9` · DISPLAY `[copybooks/plwsoi.cob:L23]` | `HV-OI5-TYPE` · `X(1)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L311]` | `OI5-TYPE` · `char(1)` `[mysql/ACASDB.sql:L604]` | no | drift: usage, name; storage: INT | — |
| 148 | `PUITM5-REC.OI5-REF` | `OI-ref` · lvl 03 · `x(10)` `[copybooks/plwsoi.cob:L36]` | `HV-OI5-REF` · `X(10)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L312]` | `OI5-REF` · `char(10)` `[mysql/ACASDB.sql:L605]` | no | drift: name; storage: STR | — |
| 149 | `PUITM5-REC.OI5-ORDER` | `OI-order` · lvl 03 · `x(10)` `[copybooks/plwsoi.cob:L37]` | `HV-OI5-ORDER` · `X(10)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L313]` | `OI5-ORDER` · `char(10)` `[mysql/ACASDB.sql:L606]` | no | drift: name; storage: STR | — |
| 150 | `PUITM5-REC.OI5-HOLD-FLAG` | `OI-hold-flag` · lvl 03 · `x` `[copybooks/plwsoi.cob:L38]` | `HV-OI5-HOLD-FLAG` · `X(1)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L314]` | `OI5-HOLD-FLAG` · `char(1)` `[mysql/ACASDB.sql:L607]` | no | drift: name; storage: STR | — |
| 151 | `PUITM5-REC.OI5-UNAPL` | `OI-unapl` · lvl 03 · `x` `[copybooks/plwsoi.cob:L40]` | `HV-OI5-UNAPL` · `X(1)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L315]` | `OI5-UNAPL` · `char(1)` `[mysql/ACASDB.sql:L608]` | no | drift: name; storage: STR | — |
| 152 | `PUITM5-REC.OI5-P-C` | `OI-P-C` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L42]` | `HV-OI5-P-C` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L316]` | `OI5-P-C` · `decimal(9,2)` `[mysql/ACASDB.sql:L609]` | no | drift: usage, name; storage: DECIMAL | — |
| 153 | `PUITM5-REC.OI5-NET` | `OI-Net` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L43]` | `HV-OI5-NET` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L317]` | `OI5-NET` · `decimal(9,2)` `[mysql/ACASDB.sql:L610]` | no | drift: usage, name; storage: DECIMAL | — |
| 154 | `PUITM5-REC.OI5-EXTRA` | `OI-Extra` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L46]` | `HV-OI5-EXTRA` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L318]` | `OI5-EXTRA` · `decimal(9,2)` `[mysql/ACASDB.sql:L611]` | no | drift: usage, name; storage: DECIMAL | — |
| 155 | `PUITM5-REC.OI5-CARRIAGE` | `OI-Carriage` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L47]` | `HV-OI5-CARRIAGE` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L319]` | `OI5-CARRIAGE` · `decimal(9,2)` `[mysql/ACASDB.sql:L612]` | no | drift: usage, name; storage: DECIMAL | — |
| 156 | `PUITM5-REC.OI5-VAT` | `OI-Vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L48]` | `HV-OI5-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L320]` | `OI5-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L613]` | no | drift: usage, name; storage: DECIMAL | — |
| 157 | `PUITM5-REC.OI5-DISCOUNT` | `OI-Discount` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L49]` | `HV-OI5-DISCOUNT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L321]` | `OI5-DISCOUNT` · `decimal(9,2)` `[mysql/ACASDB.sql:L614]` | no | drift: usage, name; storage: DECIMAL | — |
| 158 | `PUITM5-REC.OI5-E-VAT` | `OI-E-Vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L50]` | `HV-OI5-E-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L322]` | `OI5-E-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L615]` | no | drift: usage, name; storage: DECIMAL | — |
| 159 | `PUITM5-REC.OI5-C-VAT` | `OI-C-Vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L51]` | `HV-OI5-C-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L323]` | `OI5-C-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L616]` | no | drift: usage, name; storage: DECIMAL | — |
| 160 | `PUITM5-REC.OI5-PAID` | `OI-Paid` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L52]` | `HV-OI5-PAID` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L324]` | `OI5-PAID` · `decimal(9,2)` `[mysql/ACASDB.sql:L617]` | no | drift: usage, name; storage: DECIMAL | — |
| 161 | `PUITM5-REC.OI5-STATUS` | `OI-Status` · lvl 03 · `9` · DISPLAY `[copybooks/plwsoi.cob:L53]` | `HV-OI5-STATUS` · `X(1)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L325]` | `OI5-STATUS` · `char(1)` `[mysql/ACASDB.sql:L618]` | no | drift: usage, name; storage: INT | — |
| 162 | `PUITM5-REC.OI5-DEDUCT-DAYS` | `OI-Deduct-Days` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L56]` | `HV-OI5-DEDUCT-DAYS` · `9(03)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L326]` | `OI5-DEDUCT-DAYS` · `tinyint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L619]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 163 | `PUITM5-REC.OI5-DEDUCT-AMT` | `OI-Deduct-Amt` · lvl 03 · `s999v99` · COMP · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L57]` | `HV-OI5-DEDUCT-AMT` · `S9(03)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L327]` | `OI5-DEDUCT-AMT` · `decimal(5,2)` `[mysql/ACASDB.sql:L620]` | no | drift: name; storage: DECIMAL | — |
| 164 | `PUITM5-REC.OI5-DEDUCT-VAT` | `OI-Deduct-Vat` · lvl 03 · `s999v99` · COMP · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L58]` | `HV-OI5-DEDUCT-VAT` · `S9(03)V9(02)` · signed · loaded/unloaded `[common/otm5MT.cbl:L328]` | `OI5-DEDUCT-VAT` · `decimal(5,2)` `[mysql/ACASDB.sql:L621]` | no | drift: name; storage: DECIMAL | — |
| 165 | `PUITM5-REC.OI5-DAYS` | `OI-Days` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L59]` | `HV-OI5-DAYS` · `9(03)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L329]` | `OI5-DAYS` · `tinyint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L622]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 166 | `PUITM5-REC.OI5-CR` | `OI-CR` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L60]` | `HV-OI5-CR` · `S9(10)` · signed · loaded/unloaded `[common/otm5MT.cbl:L330]` | `OI5-CR` · `int(8)` `[mysql/ACASDB.sql:L623]` | no | drift: usage, name; storage: INT | — |
| 167 | `PUITM5-REC.OI5-APPLIED` | `OI-Applied` · lvl 03 · `x` `[copybooks/plwsoi.cob:L61]` | `HV-OI5-APPLIED` · `X(1)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L331]` | `OI5-APPLIED` · `char(1)` `[mysql/ACASDB.sql:L624]` | no | drift: name; storage: STR | — |
| 168 | `PUITM5-REC.OI5-DATE-CLEARED` | `OI-Date-Cleared` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi.cob:L62]` | `HV-OI5-DATE-CLEARED` · `9(10)` · unsigned · loaded/unloaded `[common/otm5MT.cbl:L332]` | `OI5-DATE-CLEARED` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L625]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |

#### `PULEDGER-REC` — 29 columns · bridge `purchMT` · handler `acas022` · facade `Purch`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 169 | `PULEDGER-REC.PURCH-KEY` | `WS-Purch-Key` · lvl 03 · `x(7)` `[copybooks/wspl.cob:L14]` | `HV-PURCH-KEY` · `X(7)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L285]` | `PURCH-KEY` · `char(7)` · **PK** `[mysql/ACASDB.sql:L647]` | no | drift: name; storage: STR | — |
| 170 | `PULEDGER-REC.PURCH-STATUS` | `Purch-Status` · lvl 03 · `9` · DISPLAY `[copybooks/wspl.cob:L18]` | `HV-PURCH-STATUS` · `9(03)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L286]` | `PURCH-STATUS` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L648]` | no | drift: usage, digits; storage: INT | — |
| 171 | `PULEDGER-REC.PURCH-NOTES-TAG` | `Purch-Notes-Tag` · lvl 03 · `9` · DISPLAY `[copybooks/wspl.cob:L21]` | `HV-PURCH-NOTES-TAG` · `9(03)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L287]` | `PURCH-NOTES-TAG` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L649]` | no | drift: usage, digits; storage: INT | — |
| 172 | `PULEDGER-REC.PURCH-NAME` | `Purch-Name` · lvl 03 · `x(30)` `[copybooks/wspl.cob:L22]` | `HV-PURCH-NAME` · `X(30)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L288]` | `PURCH-NAME` · `char(30)` `[mysql/ACASDB.sql:L650]` | no | storage: STR | — |
| 173 | `PULEDGER-REC.PURCH-ADDRESS` | `Purch-Address` · lvl 03 · GROUP · group `[copybooks/wspl.cob:L23]` | `HV-PURCH-ADDRESS` · `X(96)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L289]` | `PURCH-ADDRESS` · `char(96)` `[mysql/ACASDB.sql:L651]` | no | derivation: GROUP_CONCATENATION | — |
| 174 | `PULEDGER-REC.PURCH-PHONE` | `Purch-Phone` · lvl 03 · `x(13)` `[copybooks/wspl.cob:L26]` | `HV-PURCH-PHONE` · `X(13)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L290]` | `PURCH-PHONE` · `char(13)` `[mysql/ACASDB.sql:L652]` | no | storage: STR | — |
| 175 | `PULEDGER-REC.PURCH-EXT` | `Purch-Ext` · lvl 03 · `x(4)` `[copybooks/wspl.cob:L27]` | `HV-PURCH-EXT` · `X(4)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L291]` | `PURCH-EXT` · `char(4)` `[mysql/ACASDB.sql:L653]` | no | storage: STR | — |
| 176 | `PULEDGER-REC.PURCH-FAX` | `Purch-Fax` · lvl 03 · `x(13)` `[copybooks/wspl.cob:L28]` | `HV-PURCH-FAX` · `X(13)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L292]` | `PURCH-FAX` · `char(13)` `[mysql/ACASDB.sql:L654]` | no | storage: STR | — |
| 177 | `PULEDGER-REC.PURCH-EMAIL` | `Purch-Email` · lvl 03 · `x(30)` `[copybooks/wspl.cob:L29]` | `HV-PURCH-EMAIL` · `X(30)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L293]` | `PURCH-EMAIL` · `char(30)` `[mysql/ACASDB.sql:L655]` | no | storage: STR | — |
| 178 | `PULEDGER-REC.PURCH-DISCOUNT` | `Purch-Discount` · lvl 03 · `99v99` · COMP `[copybooks/wspl.cob:L30]` | `HV-PURCH-DISCOUNT` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L294]` | `PURCH-DISCOUNT` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L656]` | no | storage: DECIMAL | — |
| 179 | `PULEDGER-REC.PURCH-CREDIT` | `Purch-Credit` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L31]` | `HV-PURCH-CREDIT` · `9(08)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L295]` | `PURCH-CREDIT` · `mediumint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L657]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 180 | `PULEDGER-REC.PURCH-SORTCODE` | `Purch-SortCode` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L32]` | `HV-PURCH-SORTCODE` · `9(08)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L296]` | `PURCH-SORTCODE` · `mediumint(6) unsigned` · unsigned `[mysql/ACASDB.sql:L658]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 181 | `PULEDGER-REC.PURCH-ACCOUNTNO` | `Purch-Accountno` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L33]` | `HV-PURCH-ACCOUNTNO` · `9(10)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L297]` | `PURCH-ACCOUNTNO` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L659]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 182 | `PULEDGER-REC.PURCH-LIMIT` | `Purch-Limit` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L34]` | `HV-PURCH-LIMIT` · `9(10)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L298]` | `PURCH-LIMIT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L660]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 183 | `PULEDGER-REC.PURCH-ACTIVETY` | `Purch-Activety` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L35]` | `HV-PURCH-ACTIVETY` · `9(10)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L299]` | `PURCH-ACTIVETY` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L661]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 184 | `PULEDGER-REC.PURCH-LAST-INV` | `Purch-Last-inv` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L36]` | `HV-PURCH-LAST-INV` · `9(10)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L300]` | `PURCH-LAST-INV` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L662]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 185 | `PULEDGER-REC.PURCH-LAST-PAY` | `Purch-Last-pay` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L37]` | `HV-PURCH-LAST-PAY` · `9(10)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L301]` | `PURCH-LAST-PAY` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L663]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 186 | `PULEDGER-REC.PURCH-AVERAGE` | `Purch-Average` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L38]` | `HV-PURCH-AVERAGE` · `9(10)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L302]` | `PURCH-AVERAGE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L664]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 187 | `PULEDGER-REC.PURCH-CREATE-DAT` | `Purch-Create-Date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L39]` | `HV-PURCH-CREATE-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L303]` | `PURCH-CREATE-DAT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L665]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 188 | `PULEDGER-REC.PURCH-PAY-ACTIVETY` | `Purch-Pay-Activety` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L40]` | `HV-PURCH-PAY-ACTIVETY` · `9(10)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L304]` | `PURCH-PAY-ACTIVETY` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L666]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 189 | `PULEDGER-REC.PURCH-PAY-AVERAGE` | `Purch-Pay-Average` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L41]` | `HV-PURCH-PAY-AVERAGE` · `9(10)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L305]` | `PURCH-PAY-AVERAGE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L667]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 190 | `PULEDGER-REC.PURCH-PAY-WORST` | `Purch-Pay-Worst` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L42]` | `HV-PURCH-PAY-WORST` · `9(10)` · unsigned · loaded/unloaded `[common/purchMT.cbl:L306]` | `PURCH-PAY-WORST` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L668]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 191 | `PULEDGER-REC.PURCH-CURRENT` | `Purch-Current` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L43]` | `HV-PURCH-CURRENT` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/purchMT.cbl:L307]` | `PURCH-CURRENT` · `decimal(10,2)` `[mysql/ACASDB.sql:L669]` | no | drift: usage; storage: DECIMAL | — |
| 192 | `PULEDGER-REC.PURCH-LAST` | `Purch-Last` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L44]` | `HV-PURCH-LAST` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/purchMT.cbl:L308]` | `PURCH-LAST` · `decimal(10,2)` `[mysql/ACASDB.sql:L670]` | no | drift: usage; storage: DECIMAL | — |
| 193 | `PULEDGER-REC.TURNOVER-Q1` | `Turnover-q1` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L46]` | `HV-TURNOVER-Q1` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/purchMT.cbl:L309]` | `TURNOVER-Q1` · `decimal(10,2)` `[mysql/ACASDB.sql:L671]` | no | drift: usage; storage: DECIMAL | — |
| 194 | `PULEDGER-REC.TURNOVER-Q2` | `Turnover-q2` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L47]` | `HV-TURNOVER-Q2` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/purchMT.cbl:L310]` | `TURNOVER-Q2` · `decimal(10,2)` `[mysql/ACASDB.sql:L672]` | no | drift: usage; storage: DECIMAL | — |
| 195 | `PULEDGER-REC.TURNOVER-Q3` | `Turnover-q3` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L48]` | `HV-TURNOVER-Q3` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/purchMT.cbl:L311]` | `TURNOVER-Q3` · `decimal(10,2)` `[mysql/ACASDB.sql:L673]` | no | drift: usage; storage: DECIMAL | — |
| 196 | `PULEDGER-REC.TURNOVER-Q4` | `Turnover-q4` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L49]` | `HV-TURNOVER-Q4` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/purchMT.cbl:L312]` | `TURNOVER-Q4` · `decimal(10,2)` `[mysql/ACASDB.sql:L674]` | no | drift: usage; storage: DECIMAL | — |
| 197 | `PULEDGER-REC.PURCH-UNAPPLIED` | `Purch-Unapplied` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wspl.cob:L52]` | `HV-PURCH-UNAPPLIED` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/purchMT.cbl:L313]` | `PURCH-UNAPPLIED` · `decimal(10,2)` `[mysql/ACASDB.sql:L675]` | no | drift: usage; storage: DECIMAL | — |

#### `SAINV-LINES-REC` — 14 columns · bridge `slinvoiceMT` · handler `acas016` · facade `Invoice`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 198 | `SAINV-LINES-REC.IL-LINE-KEY` | `sil-Key` · lvl 05 · GROUP · group `[copybooks/slwsinv.cob:L82]` | `HV1-IL-LINE-KEY` · `X(10)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L427]` | `IL-LINE-KEY` · `char(10)` · **PK** `[mysql/ACASDB.sql:L810]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 199 | `SAINV-LINES-REC.IL-INVOICE` | `sil-invoice` · lvl 07 · `9(8)` · DISPLAY `[copybooks/slwsinv.cob:L83]` | `HV1-IL-INVOICE` · `9(10)` · unsigned · loaded/NOT unloaded `[common/slinvoiceMT.cbl:L428]` | `IL-INVOICE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L811]` | no | drift: usage, digits, name; storage: INT | — |
| 200 | `SAINV-LINES-REC.IL-LINE` | `sil-line` · lvl 07 · `99` · DISPLAY `[copybooks/slwsinv.cob:L84]` | `HV1-IL-LINE` · `9(03)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L429]` | `IL-LINE` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L812]` | no | drift: usage, digits, name; storage: INT | — |
| 201 | `SAINV-LINES-REC.IL-PRODUCT` | `sil-product` · lvl 05 · `x(13)` `[copybooks/slwsinv.cob:L85]` | `HV1-IL-PRODUCT` · `X(13)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L430]` | `IL-PRODUCT` · `char(13)` `[mysql/ACASDB.sql:L813]` | no | drift: name; storage: STR | — |
| 202 | `SAINV-LINES-REC.IL-PA` | `sil-pa` · lvl 05 · `xx` `[copybooks/slwsinv.cob:L86]` | `HV1-IL-PA` · `X(2)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L431]` | `IL-PA` · `char(2)` `[mysql/ACASDB.sql:L814]` | no | drift: name; storage: STR | — |
| 203 | `SAINV-LINES-REC.IL-QTY` | `sil-qty` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L87]` | `HV1-IL-QTY` · `9(05)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L432]` | `IL-QTY` · `smallint(6) unsigned` · unsigned `[mysql/ACASDB.sql:L815]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 204 | `SAINV-LINES-REC.IL-TYPE` | `sil-type` · lvl 05 · `x` `[copybooks/slwsinv.cob:L88]` | `HV1-IL-TYPE` · `X(1)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L433]` | `IL-TYPE` · `char(1)` `[mysql/ACASDB.sql:L816]` | no | drift: name; storage: STR | — |
| 205 | `SAINV-LINES-REC.IL-DESCRIPTION` | `sil-description` · lvl 05 · `x(32)` `[copybooks/slwsinv.cob:L89]` | `HV1-IL-DESCRIPTION` · `X(32)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L434]` | `IL-DESCRIPTION` · `char(32)` `[mysql/ACASDB.sql:L817]` | no | drift: name; storage: STR | — |
| 206 | `SAINV-LINES-REC.IL-NET` | `sil-net` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L90]` | `HV1-IL-NET` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L435]` | `IL-NET` · `decimal(9,2)` `[mysql/ACASDB.sql:L818]` | no | drift: usage, name; storage: DECIMAL | — |
| 207 | `SAINV-LINES-REC.IL-UNIT` | `sil-unit` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L91]` | `HV1-IL-UNIT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L436]` | `IL-UNIT` · `decimal(9,2)` `[mysql/ACASDB.sql:L819]` | no | drift: usage, name; storage: DECIMAL | — |
| 208 | `SAINV-LINES-REC.IL-DISCOUNT` | `sil-discount` · lvl 05 · `99v99` · COMP `[copybooks/slwsinv.cob:L92]` | `HV1-IL-DISCOUNT` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L437]` | `IL-DISCOUNT` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L820]` | no | drift: name; storage: DECIMAL | — |
| 209 | `SAINV-LINES-REC.IL-VAT` | `sil-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L93]` | `HV1-IL-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L438]` | `IL-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L821]` | no | drift: usage, name; storage: DECIMAL | — |
| 210 | `SAINV-LINES-REC.IL-VAT-CODE` | `sil-vat-code` · lvl 05 · `9` · DISPLAY `[copybooks/slwsinv.cob:L94]` | `HV1-IL-VAT-CODE` · `9(03)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L439]` | `IL-VAT-CODE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L822]` | no | drift: usage, digits, name; storage: INT | — |
| 211 | `SAINV-LINES-REC.IL-UPDATE` | `sil-update` · lvl 05 · `x` `[copybooks/slwsinv.cob:L95]` | `HV1-IL-UPDATE` · `X(1)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L440]` | `IL-UPDATE` · `char(1)` `[mysql/ACASDB.sql:L823]` | no | drift: name; storage: STR | — |

#### `SAINVOICE-REC` — 31 columns · bridge `slinvoiceMT` · handler `acas016` · facade `Invoice`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 212 | `SAINVOICE-REC.SINVOICE-KEY` | `WS-Invoice-Key` · lvl 03 · GROUP · group `[copybooks/slwsinv.cob:L20]` | `HV-SINVOICE-KEY` · `X(10)` · unsigned · loaded/NOT unloaded `[common/slinvoiceMT.cbl:L391]` | `SINVOICE-KEY` · `char(10)` · **PK** `[mysql/ACASDB.sql:L845]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 213 | `SAINVOICE-REC.IH-INVOICE` | `sih-invoice` · lvl 05 · `9(8)` · DISPLAY `[copybooks/slwsinv.cob:L21]` | `HV-IH-INVOICE` · `9(10)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L392]` | `IH-INVOICE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L846]` | no | drift: usage, digits, name; storage: INT | — |
| 214 | `SAINVOICE-REC.IH-TEST` | `sih-test` · lvl 05 · `99` · DISPLAY `[copybooks/slwsinv.cob:L22]` | `HV-IH-TEST` · `9(03)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L393]` | `IH-TEST` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L847]` | no | drift: usage, digits, name; storage: INT | — |
| 215 | `SAINVOICE-REC.IH-CUSTOMER` | `sih-customer` · lvl 03 · GROUP · group `[copybooks/slwsinv.cob:L23]` | `HV-IH-CUSTOMER` · `X(7)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L394]` | `IH-CUSTOMER` · `char(7)` `[mysql/ACASDB.sql:L848]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 216 | `SAINVOICE-REC.IH-DAT` | `sih-date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L26]` | `HV-IH-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L395]` | `IH-DAT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L849]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 217 | `SAINVOICE-REC.IH-ORDER` | `sih-order` · lvl 03 · `x(10)` `[copybooks/slwsinv.cob:L27]` | `HV-IH-ORDER` · `X(10)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L396]` | `IH-ORDER` · `char(10)` `[mysql/ACASDB.sql:L850]` | no | drift: name; storage: STR | — |
| 218 | `SAINVOICE-REC.IH-TYPE` | `sih-type` · lvl 03 · `9` · DISPLAY `[copybooks/slwsinv.cob:L39]` | `HV-IH-TYPE` · `9(03)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L397]` | `IH-TYPE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L851]` | no | drift: usage, digits, name; storage: INT | — |
| 219 | `SAINVOICE-REC.IH-REF` | `sih-ref` · lvl 03 · `x(10)` `[copybooks/slwsinv.cob:L40]` | `HV-IH-REF` · `X(10)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L398]` | `IH-REF` · `char(10)` `[mysql/ACASDB.sql:L852]` | no | drift: name; storage: STR | — |
| 220 | `SAINVOICE-REC.IH-DESCRIPTION` | `sih-description` · lvl 03 · `x(32)` `[copybooks/slwsinv.cob:L42]` | `HV-IH-DESCRIPTION` · `X(32)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L399]` | `IH-DESCRIPTION` · `char(32)` `[mysql/ACASDB.sql:L853]` | no | drift: name; storage: STR | — |
| 221 | `SAINVOICE-REC.IH-P-C` | `sih-p-c` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L44]` | `HV-IH-P-C` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L400]` | `IH-P-C` · `decimal(9,2)` `[mysql/ACASDB.sql:L854]` | no | drift: usage, name; storage: DECIMAL | — |
| 222 | `SAINVOICE-REC.IH-NET` | `sih-net` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L45]` | `HV-IH-NET` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L401]` | `IH-NET` · `decimal(9,2)` `[mysql/ACASDB.sql:L855]` | no | drift: usage, name; storage: DECIMAL | — |
| 223 | `SAINVOICE-REC.IH-EXTRA` | `sih-extra` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L46]` | `HV-IH-EXTRA` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L402]` | `IH-EXTRA` · `decimal(9,2)` `[mysql/ACASDB.sql:L856]` | no | drift: usage, name; storage: DECIMAL | — |
| 224 | `SAINVOICE-REC.IH-CARRIAGE` | `sih-carriage` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L47]` | `HV-IH-CARRIAGE` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L403]` | `IH-CARRIAGE` · `decimal(9,2)` `[mysql/ACASDB.sql:L857]` | no | drift: usage, name; storage: DECIMAL | — |
| 225 | `SAINVOICE-REC.IH-VAT` | `sih-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L48]` | `HV-IH-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L404]` | `IH-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L858]` | no | drift: usage, name; storage: DECIMAL | — |
| 226 | `SAINVOICE-REC.IH-DISCOUNT` | `sih-discount` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L49]` | `HV-IH-DISCOUNT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L405]` | `IH-DISCOUNT` · `decimal(9,2)` `[mysql/ACASDB.sql:L859]` | no | drift: usage, name; storage: DECIMAL | — |
| 227 | `SAINVOICE-REC.IH-E-VAT` | `sih-e-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L50]` | `HV-IH-E-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L406]` | `IH-E-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L860]` | no | drift: usage, name; storage: DECIMAL | — |
| 228 | `SAINVOICE-REC.IH-C-VAT` | `sih-c-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L51]` | `HV-IH-C-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/slinvoiceMT.cbl:L407]` | `IH-C-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L861]` | no | drift: usage, name; storage: DECIMAL | — |
| 229 | `SAINVOICE-REC.IH-STATUS` | `sih-status` · lvl 03 · `x` `[copybooks/slwsinv.cob:L52]` | `HV-IH-STATUS` · `X(1)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L408]` | `IH-STATUS` · `char(1)` `[mysql/ACASDB.sql:L862]` | no | drift: name; storage: STR | — |
| 230 | `SAINVOICE-REC.IH-STATUS-P` | `sih-status-P` · lvl 03 · `x` `[copybooks/slwsinv.cob:L56]` | `HV-IH-STATUS-P` · `X(1)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L409]` | `IH-STATUS-P` · `char(1)` `[mysql/ACASDB.sql:L863]` | no | drift: name; storage: STR | — |
| 231 | `SAINVOICE-REC.IH-STATUS-L` | `sih-status-L` · lvl 03 · `x` `[copybooks/slwsinv.cob:L57]` | `HV-IH-STATUS-L` · `X(1)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L410]` | `IH-STATUS-L` · `char(1)` `[mysql/ACASDB.sql:L864]` | no | drift: name; storage: STR | — |
| 232 | `SAINVOICE-REC.IH-STATUS-C` | `sih-status-C` · lvl 03 · `x` `[copybooks/slwsinv.cob:L58]` | `HV-IH-STATUS-C` · `X(1)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L411]` | `IH-STATUS-C` · `char(1)` `[mysql/ACASDB.sql:L865]` | no | drift: name; storage: STR | — |
| 233 | `SAINVOICE-REC.IH-STATUS-A` | `sih-status-A` · lvl 03 · `x` `[copybooks/slwsinv.cob:L59]` | `HV-IH-STATUS-A` · `X(1)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L412]` | `IH-STATUS-A` · `char(1)` `[mysql/ACASDB.sql:L866]` | no | drift: name; storage: STR | — |
| 234 | `SAINVOICE-REC.IH-STATUS-I` | `sih-status-I` · lvl 03 · `x` `[copybooks/slwsinv.cob:L60]` | `HV-IH-STATUS-I` · `X(1)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L413]` | `IH-STATUS-I` · `char(1)` `[mysql/ACASDB.sql:L867]` | no | drift: name; storage: STR | — |
| 235 | `SAINVOICE-REC.IH-DEDUCT-DAYS` | `sih-deduct-days` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L62]` | `HV-IH-DEDUCT-DAYS` · `9(03)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L414]` | `IH-DEDUCT-DAYS` · `tinyint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L868]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 236 | `SAINVOICE-REC.IH-DEDUCT-AMT` | `sih-deduct-amt` · lvl 03 · `999v99` · COMP `[copybooks/slwsinv.cob:L63]` | `HV-IH-DEDUCT-AMT` · `9(03)V9(02)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L415]` | `IH-DEDUCT-AMT` · `decimal(5,2) unsigned` · unsigned `[mysql/ACASDB.sql:L869]` | no | drift: name; storage: DECIMAL | — |
| 237 | `SAINVOICE-REC.IH-DEDUCT-VAT` | `sih-deduct-vat` · lvl 03 · `999v99` · COMP `[copybooks/slwsinv.cob:L64]` | `HV-IH-DEDUCT-VAT` · `9(03)V9(02)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L416]` | `IH-DEDUCT-VAT` · `decimal(5,2) unsigned` · unsigned `[mysql/ACASDB.sql:L870]` | no | drift: name; storage: DECIMAL | — |
| 238 | `SAINVOICE-REC.IH-DAYS` | `sih-days` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L65]` | `HV-IH-DAYS` · `9(03)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L417]` | `IH-DAYS` · `tinyint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L871]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 239 | `SAINVOICE-REC.IH-CR` | `sih-cr` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L66]` | `HV-IH-CR` · `9(10)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L418]` | `IH-CR` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L872]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 240 | `SAINVOICE-REC.IH-LINES` | `sih-lines` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L61]` | `HV-IH-LINES` · `9(03)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L419]` | `IH-LINES` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L873]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 241 | `SAINVOICE-REC.IH-DAY-BOOK-FLAG` | `sih-day-book-flag` · lvl 03 · `x` `[copybooks/slwsinv.cob:L67]` | `HV-IH-DAY-BOOK-FLAG` · `X(1)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L420]` | `IH-DAY-BOOK-FLAG` · `char(1)` `[mysql/ACASDB.sql:L874]` | no | drift: name; storage: STR | — |
| 242 | `SAINVOICE-REC.IH-UPDATE` | `sih-update` · lvl 03 · `x` `[copybooks/slwsinv.cob:L69]` | `HV-IH-UPDATE` · `X(1)` · unsigned · loaded/unloaded `[common/slinvoiceMT.cbl:L421]` | `IH-UPDATE` · `char(1)` `[mysql/ACASDB.sql:L875]` | no | drift: name; storage: STR | — |

#### `SAITM3-REC` — 28 columns · bridge `otm3MT` · handler `acas019` · facade `OTM3`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 243 | `SAITM3-REC.OI3-KEY` | `OI3-Key` · lvl 03 · GROUP · group `[copybooks/slwsoi3.cob:L12]` | `HV-OI3-KEY` · `X(15)` · unsigned · loaded/NOT unloaded `[common/otm3MT.cbl:L302]` | `OI3-KEY` · `char(15)` · **PK** `[mysql/ACASDB.sql:L897]` | no | derivation: GROUP_CONCATENATION | — |
| 244 | `SAITM3-REC.OI3-CUSTOMER` | `OI-Customer` · lvl 03 · GROUP · group `[copybooks/slwsoi.cob:L10]` | `HV-OI3-CUSTOMER` · `X(7)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L303]` | `OI3-CUSTOMER` · `char(7)` `[mysql/ACASDB.sql:L898]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 245 | `SAITM3-REC.OI3-INVOICE` | `OI-Invoice` · lvl 03 · `9(8)` · DISPLAY `[copybooks/slwsoi.cob:L13]` | `HV-OI3-INVOICE` · `9(10)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L304]` | `OI3-INVOICE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L899]` | no | drift: usage, digits, name; storage: INT | — |
| 246 | `SAITM3-REC.OI3-DAT` | `OI-Date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L15]` | `HV-OI3-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L305]` | `OI3-DAT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L900]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 247 | `SAITM3-REC.OI3-BATCH` | `OI-Batch` · lvl 03 · GROUP · group `[copybooks/slwsoi.cob:L16]` | `HV-OI3-BATCH` · `X(8)` · unsigned · loaded/NOT unloaded `[common/otm3MT.cbl:L306]` | `OI3-BATCH` · `char(8)` `[mysql/ACASDB.sql:L901]` | no | drift: name; derivation: GROUP_CONCATENATION | — |
| 248 | `SAITM3-REC.OI3-BATCH-NOS` | `OI-B-Nos` · lvl 05 · `9(5)` · COMP `[copybooks/slwsoi.cob:L17]` | `HV-OI3-BATCH-NOS` · `X(5)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L307]` | `OI3-BATCH-NOS` · `char(5)` `[mysql/ACASDB.sql:L902]` | no | drift: usage, name; storage: INT | — |
| 249 | `SAITM3-REC.OI3-BATCH-ITEM` | `OI-B-Item` · lvl 05 · `999` · COMP `[copybooks/slwsoi.cob:L18]` | `HV-OI3-BATCH-ITEM` · `X(3)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L308]` | `OI3-BATCH-ITEM` · `char(3)` `[mysql/ACASDB.sql:L903]` | no | drift: usage, name; storage: INT | — |
| 250 | `SAITM3-REC.OI3-TYPE` | `OI-Type` · lvl 03 · `9` · DISPLAY `[copybooks/slwsoi.cob:L19]` | `HV-OI3-TYPE` · `X(1)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L309]` | `OI3-TYPE` · `char(1)` `[mysql/ACASDB.sql:L904]` | no | drift: usage, name; storage: INT | — |
| 251 | `SAITM3-REC.OI3-DESCRIPTION` | `OI-Description` · lvl 03 · `x(25)` `[copybooks/slwsoi.cob:L32]` | `HV-OI3-DESCRIPTION` · `X(32)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L310]` | `OI3-DESCRIPTION` · `char(32)` `[mysql/ACASDB.sql:L905]` | no | drift: character_length, name; storage: STR | `A-12` |
| 252 | `SAITM3-REC.OI3-HOLD-FLAG` | `OI-Hold-flag` · lvl 03 · `x` `[copybooks/slwsoi.cob:L33]` | `HV-OI3-HOLD-FLAG` · `X(1)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L311]` | `OI3-HOLD-FLAG` · `char(1)` `[mysql/ACASDB.sql:L906]` | no | drift: name; storage: STR | — |
| 253 | `SAITM3-REC.OI3-UNAPL` | `OI-Unapl` · lvl 03 · `x` `[copybooks/slwsoi.cob:L34]` | `HV-OI3-UNAPL` · `X(1)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L312]` | `OI3-UNAPL` · `char(1)` `[mysql/ACASDB.sql:L907]` | no | drift: name; storage: STR | — |
| 254 | `SAITM3-REC.OI3-P-C` | `OI-P-C` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L36]` | `HV-OI3-P-C` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L313]` | `OI3-P-C` · `decimal(9,2)` `[mysql/ACASDB.sql:L908]` | no | drift: usage, name; storage: DECIMAL | — |
| 255 | `SAITM3-REC.OI3-NET` | `OI-Net` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L37]` | `HV-OI3-NET` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L314]` | `OI3-NET` · `decimal(9,2)` `[mysql/ACASDB.sql:L909]` | no | drift: usage, name; storage: DECIMAL | — |
| 256 | `SAITM3-REC.OI3-EXTRA` | `OI-Extra` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L40]` | `HV-OI3-EXTRA` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L315]` | `OI3-EXTRA` · `decimal(9,2)` `[mysql/ACASDB.sql:L910]` | no | drift: usage, name; storage: DECIMAL | — |
| 257 | `SAITM3-REC.OI3-CARRIAGE` | `OI-Carriage` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L41]` | `HV-OI3-CARRIAGE` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L316]` | `OI3-CARRIAGE` · `decimal(9,2)` `[mysql/ACASDB.sql:L911]` | no | drift: usage, name; storage: DECIMAL | — |
| 258 | `SAITM3-REC.OI3-VAT` | `OI-Vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L42]` | `HV-OI3-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L317]` | `OI3-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L912]` | no | drift: usage, name; storage: DECIMAL | — |
| 259 | `SAITM3-REC.OI3-DISCOUNT` | `OI-Discount` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L43]` | `HV-OI3-DISCOUNT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L318]` | `OI3-DISCOUNT` · `decimal(9,2)` `[mysql/ACASDB.sql:L913]` | no | drift: usage, name; storage: DECIMAL | — |
| 260 | `SAITM3-REC.OI3-E-VAT` | `OI-E-Vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L44]` | `HV-OI3-E-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L319]` | `OI3-E-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L914]` | no | drift: usage, name; storage: DECIMAL | — |
| 261 | `SAITM3-REC.OI3-C-VAT` | `OI-C-Vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L45]` | `HV-OI3-C-VAT` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L320]` | `OI3-C-VAT` · `decimal(9,2)` `[mysql/ACASDB.sql:L915]` | no | drift: usage, name; storage: DECIMAL | — |
| 262 | `SAITM3-REC.OI3-PAID` | `OI-Paid` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L46]` | `HV-OI3-PAID` · `S9(07)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L321]` | `OI3-PAID` · `decimal(9,2)` `[mysql/ACASDB.sql:L916]` | no | drift: usage, name; storage: DECIMAL | — |
| 263 | `SAITM3-REC.OI3-STATUS` | `OI-Status` · lvl 03 · `9` · DISPLAY `[copybooks/slwsoi.cob:L47]` | `HV-OI3-STATUS` · `X(1)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L322]` | `OI3-STATUS` · `char(1)` `[mysql/ACASDB.sql:L917]` | no | drift: usage, name; storage: INT | — |
| 264 | `SAITM3-REC.OI3-DEDUCT-DAYS` | `OI-Deduct-Days` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L50]` | `HV-OI3-DEDUCT-DAYS` · `9(03)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L323]` | `OI3-DEDUCT-DAYS` · `tinyint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L918]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 265 | `SAITM3-REC.OI3-DEDUCT-AMT` | `OI-Deduct-Amt` · lvl 03 · `s999v99` · COMP · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L51]` | `HV-OI3-DEDUCT-AMT` · `S9(03)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L324]` | `OI3-DEDUCT-AMT` · `decimal(5,2)` `[mysql/ACASDB.sql:L919]` | no | drift: name; storage: DECIMAL | — |
| 266 | `SAITM3-REC.OI3-DEDUCT-VAT` | `OI-Deduct-Vat` · lvl 03 · `s999v99` · COMP · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L52]` | `HV-OI3-DEDUCT-VAT` · `S9(03)V9(02)` · signed · loaded/unloaded `[common/otm3MT.cbl:L325]` | `OI3-DEDUCT-VAT` · `decimal(5,2)` `[mysql/ACASDB.sql:L920]` | no | drift: name; storage: DECIMAL | — |
| 267 | `SAITM3-REC.OI3-DAYS` | `OI-Days` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L53]` | `HV-OI3-DAYS` · `9(03)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L326]` | `OI3-DAYS` · `tinyint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L921]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 268 | `SAITM3-REC.OI3-CR` | `OI-Cr` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L54]` | `HV-OI3-CR` · `S9(10)` · signed · loaded/unloaded `[common/otm3MT.cbl:L327]` | `OI3-CR` · `int(8)` `[mysql/ACASDB.sql:L922]` | no | drift: usage, name; storage: INT | — |
| 269 | `SAITM3-REC.OI3-APPLIED` | `OI-Applied` · lvl 03 · `x` `[copybooks/slwsoi.cob:L55]` | `HV-OI3-APPLIED` · `X(1)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L328]` | `OI3-APPLIED` · `char(1)` `[mysql/ACASDB.sql:L923]` | no | drift: name; storage: STR | — |
| 270 | `SAITM3-REC.OI3-DATE-CLEARED` | `OI-Date-Cleared` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi.cob:L56]` | `HV-OI3-DATE-CLEARED` · `9(10)` · unsigned · loaded/unloaded `[common/otm3MT.cbl:L329]` | `OI3-DATE-CLEARED` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L924]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |

#### `SALEDGER-REC` — 37 columns · bridge `salesMT` · handler `acas012` · facade `Sales`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 271 | `SALEDGER-REC.SALES-KEY` | `WS-Sales-Key` · lvl 03 · `x(7)` `[copybooks/wssl.cob:L13]` | `HV-SALES-KEY` · `X(7)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L285]` | `SALES-KEY` · `char(7)` · **PK** `[mysql/ACASDB.sql:L946]` | no | drift: name; storage: STR | — |
| 272 | `SALEDGER-REC.SALES-NAME` | `Sales-Name` · lvl 03 · `x(30)` `[copybooks/wssl.cob:L17]` | `HV-SALES-NAME` · `X(30)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L286]` | `SALES-NAME` · `char(30)` `[mysql/ACASDB.sql:L947]` | no | storage: STR | — |
| 273 | `SALEDGER-REC.SALES-ADDRESS` | `Sales-Address` · lvl 03 · GROUP · group `[copybooks/wssl.cob:L18]` | `HV-SALES-ADDRESS` · `X(96)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L287]` | `SALES-ADDRESS` · `char(96)` `[mysql/ACASDB.sql:L948]` | no | derivation: GROUP_CONCATENATION | — |
| 274 | `SALEDGER-REC.SALES-PHONE` | `Sales-Phone` · lvl 03 · `x(13)` `[copybooks/wssl.cob:L21]` | `HV-SALES-PHONE` · `X(13)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L288]` | `SALES-PHONE` · `char(13)` `[mysql/ACASDB.sql:L949]` | no | storage: STR | — |
| 275 | `SALEDGER-REC.SALES-EXT` | `Sales-Ext` · lvl 03 · `x(4)` `[copybooks/wssl.cob:L22]` | `HV-SALES-EXT` · `X(4)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L289]` | `SALES-EXT` · `char(4)` `[mysql/ACASDB.sql:L950]` | no | storage: STR | — |
| 276 | `SALEDGER-REC.SALES-EMAIL` | `Sales-Email` · lvl 03 · `x(30)` `[copybooks/wssl.cob:L23]` | `HV-SALES-EMAIL` · `X(30)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L290]` | `SALES-EMAIL` · `char(30)` `[mysql/ACASDB.sql:L951]` | no | storage: STR | — |
| 277 | `SALEDGER-REC.SALES-FAX` | `Sales-Fax` · lvl 03 · `x(13)` `[copybooks/wssl.cob:L24]` | `HV-SALES-FAX` · `X(13)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L291]` | `SALES-FAX` · `char(13)` `[mysql/ACASDB.sql:L952]` | no | storage: STR | — |
| 278 | `SALEDGER-REC.SALES-STATUS` | `Sales-Status` · lvl 03 · `9` · DISPLAY `[copybooks/wssl.cob:L25]` | `HV-SALES-STATUS` · `9(03)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L292]` | `SALES-STATUS` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L953]` | no | drift: usage, digits; storage: INT | — |
| 279 | `SALEDGER-REC.SALES-LATE` | `Sales-Late` · lvl 03 · `9` · DISPLAY `[copybooks/wssl.cob:L28]` | `HV-SALES-LATE` · `9(03)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L293]` | `SALES-LATE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L954]` | no | drift: usage, digits; storage: INT | — |
| 280 | `SALEDGER-REC.SALES-DUNNING` | `Sales-Dunning` · lvl 03 · `9` · DISPLAY `[copybooks/wssl.cob:L30]` | `HV-SALES-DUNNING` · `9(03)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L294]` | `SALES-DUNNING` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L955]` | no | drift: usage, digits; storage: INT | — |
| 281 | `SALEDGER-REC.EMAIL-INVOICE` | `Email-Invoice` · lvl 03 · `9` · DISPLAY `[copybooks/wssl.cob:L32]` | `HV-EMAIL-INVOICE` · `9(03)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L295]` | `EMAIL-INVOICE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L956]` | no | drift: usage, digits; storage: INT | — |
| 282 | `SALEDGER-REC.EMAIL-STATEMENT` | `Email-Statement` · lvl 03 · `9` · DISPLAY `[copybooks/wssl.cob:L34]` | `HV-EMAIL-STATEMENT` · `9(03)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L296]` | `EMAIL-STATEMENT` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L957]` | no | drift: usage, digits; storage: INT | — |
| 283 | `SALEDGER-REC.EMAIL-LETTERS` | `Email-Letters` · lvl 03 · `9` · DISPLAY `[copybooks/wssl.cob:L36]` | `HV-EMAIL-LETTERS` · `9(03)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L297]` | `EMAIL-LETTERS` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L958]` | no | drift: usage, digits; storage: INT | — |
| 284 | `SALEDGER-REC.DELIVERY-TAG` | `Delivery-Tag` · lvl 03 · `9` · DISPLAY `[copybooks/wssl.cob:L38]` | `HV-DELIVERY-TAG` · `9(03)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L298]` | `DELIVERY-TAG` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L959]` | no | drift: usage, digits; storage: INT | — |
| 285 | `SALEDGER-REC.NOTES-TAG` | `Notes-Tag` · lvl 03 · `9` · DISPLAY `[copybooks/wssl.cob:L39]` | `HV-NOTES-TAG` · `9(03)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L299]` | `NOTES-TAG` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L960]` | no | drift: usage, digits; storage: INT | — |
| 286 | `SALEDGER-REC.SALES-CREDIT` | `Sales-Credit` · lvl 03 · `99` · DISPLAY `[copybooks/wssl.cob:L41]` | `HV-SALES-CREDIT` · `9(03)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L300]` | `SALES-CREDIT` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L961]` | no | drift: usage, digits; storage: INT | — |
| 287 | `SALEDGER-REC.SALES-DISCOUNT` | `Sales-Discount` · lvl 03 · `99v99` · COMP `[copybooks/wssl.cob:L42]` | `HV-SALES-DISCOUNT` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L301]` | `SALES-DISCOUNT` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L962]` | no | storage: DECIMAL | — |
| 288 | `SALEDGER-REC.SALES-LATE-MIN` | `Sales-Late-Min` · lvl 03 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L43]` | `HV-SALES-LATE-MIN` · `9(05)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L302]` | `SALES-LATE-MIN` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L963]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 289 | `SALEDGER-REC.SALES-LATE-MAX` | `Sales-Late-Max` · lvl 03 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L44]` | `HV-SALES-LATE-MAX` · `9(05)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L303]` | `SALES-LATE-MAX` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L964]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 290 | `SALEDGER-REC.SALES-LIMIT` | `Sales-Limit` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L45]` | `HV-SALES-LIMIT` · `9(10)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L304]` | `SALES-LIMIT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L965]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 291 | `SALEDGER-REC.SALES-ACTIVETY` | `Sales-Activety` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L46]` | `HV-SALES-ACTIVETY` · `9(10)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L305]` | `SALES-ACTIVETY` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L966]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 292 | `SALEDGER-REC.SALES-LAST-INV` | `Sales-Last-Inv` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L47]` | `HV-SALES-LAST-INV` · `9(10)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L306]` | `SALES-LAST-INV` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L967]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 293 | `SALEDGER-REC.SALES-LAST-PAY` | `Sales-Last-Pay` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L48]` | `HV-SALES-LAST-PAY` · `9(10)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L307]` | `SALES-LAST-PAY` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L968]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 294 | `SALEDGER-REC.SALES-AVERAGE` | `Sales-Average` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L49]` | `HV-SALES-AVERAGE` · `9(10)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L308]` | `SALES-AVERAGE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L969]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 295 | `SALEDGER-REC.SALES-PAY-ACTIVETY` | `Sales-Pay-Activety` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L50]` | `HV-SALES-PAY-ACTIVETY` · `9(10)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L309]` | `SALES-PAY-ACTIVETY` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L970]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 296 | `SALEDGER-REC.SALES-PAY-AVERAGE` | `Sales-Pay-Average` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L51]` | `HV-SALES-PAY-AVERAGE` · `9(10)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L310]` | `SALES-PAY-AVERAGE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L971]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 297 | `SALEDGER-REC.SALES-PAY-WORST` | `Sales-Pay-Worst` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L52]` | `HV-SALES-PAY-WORST` · `9(10)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L311]` | `SALES-PAY-WORST` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L972]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 298 | `SALEDGER-REC.SALES-CREATE-DAT` | `Sales-Create-Date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L53]` | `HV-SALES-CREATE-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/salesMT.cbl:L312]` | `SALES-CREATE-DAT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L973]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 299 | `SALEDGER-REC.SALES-CURRENT` | `Sales-Current` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L54]` | `HV-SALES-CURRENT` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/salesMT.cbl:L313]` | `SALES-CURRENT` · `decimal(10,2)` `[mysql/ACASDB.sql:L974]` | no | drift: usage; storage: DECIMAL | — |
| 300 | `SALEDGER-REC.SALES-LAST` | `Sales-Last` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L55]` | `HV-SALES-LAST` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/salesMT.cbl:L314]` | `SALES-LAST` · `decimal(10,2)` `[mysql/ACASDB.sql:L975]` | no | drift: usage; storage: DECIMAL | — |
| 301 | `SALEDGER-REC.TURNOVER-Q1` | `Turnover-Q1` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L57]` | `HV-TURNOVER-Q1` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/salesMT.cbl:L315]` | `TURNOVER-Q1` · `decimal(10,2)` `[mysql/ACASDB.sql:L976]` | no | drift: usage; storage: DECIMAL | — |
| 302 | `SALEDGER-REC.TURNOVER-Q2` | `Turnover-Q2` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L58]` | `HV-TURNOVER-Q2` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/salesMT.cbl:L316]` | `TURNOVER-Q2` · `decimal(10,2)` `[mysql/ACASDB.sql:L977]` | no | drift: usage; storage: DECIMAL | — |
| 303 | `SALEDGER-REC.TURNOVER-Q3` | `Turnover-Q3` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L59]` | `HV-TURNOVER-Q3` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/salesMT.cbl:L317]` | `TURNOVER-Q3` · `decimal(10,2)` `[mysql/ACASDB.sql:L978]` | no | drift: usage; storage: DECIMAL | — |
| 304 | `SALEDGER-REC.TURNOVER-Q4` | `Turnover-Q4` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L60]` | `HV-TURNOVER-Q4` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/salesMT.cbl:L318]` | `TURNOVER-Q4` · `decimal(10,2)` `[mysql/ACASDB.sql:L979]` | no | drift: usage; storage: DECIMAL | — |
| 305 | `SALEDGER-REC.SALES-UNAPPLIED` | `Sales-Unapplied` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssl.cob:L63]` | `HV-SALES-UNAPPLIED` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/salesMT.cbl:L319]` | `SALES-UNAPPLIED` · `decimal(10,2)` `[mysql/ACASDB.sql:L980]` | no | drift: usage; storage: DECIMAL | — |
| 306 | `SALEDGER-REC.SALES-STATS-DATE` | `Sales-Stats-Date` · lvl 03 · `9(4)` · DISPLAY `[copybooks/wssl.cob:L64]` | `HV-SALES-STATS-DATE` · `X(4)` · unsigned · NOT loaded/NOT unloaded `[common/salesMT.cbl:L320]` | `SALES-STATS-DATE` · `char(4)` `[mysql/ACASDB.sql:L981]` | no | drift: usage; storage: INT | — |
| 307 | `SALEDGER-REC.SALES-PARTIAL-SHIP-FLAG` | `Sales-Partial-Ship-Flag` · lvl 03 · `x` `[copybooks/wssl.cob:L65]` | `HV-SALES-PARTIAL-SHIP-FLAG` · `X(1)` · unsigned · NOT loaded/NOT unloaded `[common/salesMT.cbl:L321]` | `SALES-PARTIAL-SHIP-FLAG` · `char(1)` `[mysql/ACASDB.sql:L982]` | no | storage: STR | — |

#### `SYSDEFLT-REC` — 4 columns · bridge `dfltMT` · handler `acas000` · facade `System defaults`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 308 | `SYSDEFLT-REC.DEF-REC-KEY` | **absent** | `HV-DEF-REC-KEY` · `9(03)` · unsigned · loaded/unloaded `[common/dfltMT.cbl:L316]` | `DEF-REC-KEY` · `tinyint(2) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L1139]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 309 | `SYSDEFLT-REC.DEF-ACS` | `Def-Acs` · lvl 05 · `9(4)v99` · COMP `[copybooks/wsdflt.cob:L16]` | `HV-DEF-ACS` · `9(04)V9(02)` · unsigned · loaded/unloaded `[common/dfltMT.cbl:L317]` | `DEF-ACS` · `decimal(6,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1140]` | no | derivation: BRIDGE_DERIVED guarded on `if Def-Acs (A) numeric`; storage: DECIMAL | — |
| 310 | `SYSDEFLT-REC.DEF-CODES` | `Def-Codes` · lvl 05 · `xx` `[copybooks/wsdflt.cob:L17]` | `HV-DEF-CODES` · `X(2)` · unsigned · loaded/unloaded `[common/dfltMT.cbl:L318]` | `DEF-CODES` · `char(2)` `[mysql/ACASDB.sql:L1141]` | no | storage: STR | — |
| 311 | `SYSDEFLT-REC.DEF-VAT` | `Def-Vat` · lvl 05 · `x` `[copybooks/wsdflt.cob:L18]` | `HV-DEF-VAT` · `X(1)` · unsigned · loaded/unloaded `[common/dfltMT.cbl:L319]` | `DEF-VAT` · `char(1)` `[mysql/ACASDB.sql:L1142]` | no | storage: STR | — |

#### `SYSFINAL-REC` — 2 columns · bridge `finalMT` · handler `acas000` · facade `System final`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 312 | `SYSFINAL-REC.FINAL-ACC-REC-KEY` | **absent** | `HV-FINAL-ACC-REC-KEY` · `9(03)` · unsigned · loaded/unloaded `[common/finalMT.cbl:L314]` | `FINAL-ACC-REC-KEY` · `tinyint(2) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L1164]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 313 | `SYSFINAL-REC.AR1` | `ar1` · lvl 03 · `x(16)` · occurs 26 `[copybooks/wsfinal.cob:L11]` | `HV-AR1` · `X(16)` · unsigned · loaded/unloaded `[common/finalMT.cbl:L315]` | `AR1` · `char(16)` `[mysql/ACASDB.sql:L1165]` | no | storage: STR | — |

#### `SYSTEM-REC` — 169 columns · bridge `systemMT` · handler `acas000` · facade `System`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 314 | `SYSTEM-REC.SYSTEM-REC-KEY` | **absent** | `HV-SYSTEM-REC-KEY` · `9(03)` · unsigned · loaded/NOT unloaded `[common/systemMT.cbl:L324]` | `SYSTEM-REC-KEY` · `tinyint(1) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L1187]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 315 | `SYSTEM-REC.SYSTEM-RECORD-VERSION-PRIME` | `System-Record-Version-Prime` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L53]` | `HV-SYSTEM-RECORD-VERSION-PRIME` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L325]` | `SYSTEM-RECORD-VERSION-PRIME` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L1188]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 316 | `SYSTEM-REC.SYSTEM-RECORD-VERSION-SECONDAR` | `System-Record-Version-Secondary` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L54]` | `HV-SYSTEM-RECORD-VERSION-SECON` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L326]` | `SYSTEM-RECORD-VERSION-SECONDAR` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L1189]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 317 | `SYSTEM-REC.VAT-RATE-1` | `Vat-Rate-1` · lvl 07 · `99v99` · COMP `[copybooks/wssystem.cob:L56]` | `HV-VAT-RATE-1` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L327]` | `VAT-RATE-1` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1190]` | no | storage: DECIMAL | — |
| 318 | `SYSTEM-REC.VAT-RATE-2` | `Vat-Rate-2` · lvl 07 · `99v99` · COMP `[copybooks/wssystem.cob:L57]` | `HV-VAT-RATE-2` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L328]` | `VAT-RATE-2` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1191]` | no | storage: DECIMAL | — |
| 319 | `SYSTEM-REC.VAT-RATE-3` | `Vat-Rate-3` · lvl 07 · `99v99` · COMP `[copybooks/wssystem.cob:L58]` | `HV-VAT-RATE-3` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L329]` | `VAT-RATE-3` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1192]` | no | storage: DECIMAL | — |
| 320 | `SYSTEM-REC.VAT-RATE-4` | `Vat-Rate-4` · lvl 07 · `99v99` · COMP `[copybooks/wssystem.cob:L59]` | `HV-VAT-RATE-4` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L330]` | `VAT-RATE-4` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1193]` | no | storage: DECIMAL | — |
| 321 | `SYSTEM-REC.VAT-RATE-5` | `Vat-Rate-5` · lvl 07 · `99v99` · COMP `[copybooks/wssystem.cob:L60]` | `HV-VAT-RATE-5` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L331]` | `VAT-RATE-5` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1194]` | no | storage: DECIMAL | — |
| 322 | `SYSTEM-REC.CYCLEA` | `Cyclea` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L62]` | `HV-CYCLEA` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L332]` | `CYCLEA` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L1195]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 323 | `SYSTEM-REC.PERIOD` | `Period` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L64]` | `HV-PERIOD` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L333]` | `PERIOD` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L1196]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 324 | `SYSTEM-REC.PAGE-LINES` | `Page-Lines` · lvl 05 · BINARY-CHAR `[copybooks/wssystem.cob:L65]` | `HV-PAGE-LINES` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L334]` | `PAGE-LINES` · `tinyint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L1197]` | no | drift: usage; storage: INT | — |
| 325 | `SYSTEM-REC.NEXT-INVOICE` | `Next-Invoice` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L66]` | `HV-NEXT-INVOICE` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L335]` | `NEXT-INVOICE` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1198]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 326 | `SYSTEM-REC.RUN-DAT` | `Run-Date` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L67]` | `HV-RUN-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L336]` | `RUN-DAT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1199]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 327 | `SYSTEM-REC.START-DAT` | `Start-Date` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L68]` | `HV-START-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L337]` | `START-DAT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1200]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 328 | `SYSTEM-REC.END-DAT` | `End-Date` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L69]` | `HV-END-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L338]` | `END-DAT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1201]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 329 | `SYSTEM-REC.SUSER` | `Suser` · lvl 05 · GROUP · group `[copybooks/wssystem.cob:L70]` | `HV-SUSER` · `X(32)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L339]` | `SUSER` · `char(32)` `[mysql/ACASDB.sql:L1202]` | no | derivation: GROUP_CONCATENATION | — |
| 330 | `SYSTEM-REC.USER-CODE` | `User-Code` · lvl 05 · `x(32)` `[copybooks/wssystem.cob:L72]` | `HV-USER-CODE` · `X(32)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L340]` | `USER-CODE` · `char(32)` `[mysql/ACASDB.sql:L1203]` | no | storage: STR | — |
| 331 | `SYSTEM-REC.ADDRESS-1` | `Address-1` · lvl 05 · `x(24)` `[copybooks/wssystem.cob:L73]` | `HV-ADDRESS-1` · `X(24)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L341]` | `ADDRESS-1` · `char(24)` `[mysql/ACASDB.sql:L1204]` | no | storage: STR | — |
| 332 | `SYSTEM-REC.ADDRESS-2` | `Address-2` · lvl 05 · `x(24)` `[copybooks/wssystem.cob:L74]` | `HV-ADDRESS-2` · `X(24)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L342]` | `ADDRESS-2` · `char(24)` `[mysql/ACASDB.sql:L1205]` | no | storage: STR | — |
| 333 | `SYSTEM-REC.ADDRESS-3` | `Address-3` · lvl 05 · `x(24)` `[copybooks/wssystem.cob:L75]` | `HV-ADDRESS-3` · `X(24)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L343]` | `ADDRESS-3` · `char(24)` `[mysql/ACASDB.sql:L1206]` | no | storage: STR | — |
| 334 | `SYSTEM-REC.ADDRESS-4` | `Address-4` · lvl 05 · `x(24)` `[copybooks/wssystem.cob:L76]` | `HV-ADDRESS-4` · `X(24)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L344]` | `ADDRESS-4` · `char(24)` `[mysql/ACASDB.sql:L1207]` | no | storage: STR | — |
| 335 | `SYSTEM-REC.POST-CODE` | `Post-Code` · lvl 05 · `x(12)` `[copybooks/wssystem.cob:L77]` | `HV-POST-CODE` · `X(12)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L345]` | `POST-CODE` · `char(12)` `[mysql/ACASDB.sql:L1208]` | no | storage: STR | — |
| 336 | `SYSTEM-REC.COMPANY-EMAIL` | `Company-Email` · lvl 05 · `x(30)` `[copybooks/wssystem.cob:L146]` | `HV-COMPANY-EMAIL` · `X(30)` · unsigned · NOT loaded/NOT unloaded `[common/systemMT.cbl:L346]` | `COMPANY-EMAIL` · `char(30)` `[mysql/ACASDB.sql:L1209]` | no | storage: STR | — |
| 337 | `SYSTEM-REC.COUNTRY` | `Country` · lvl 05 · `x(24)` `[copybooks/wssystem.cob:L78]` | `HV-COUNTRY` · `X(24)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L347]` | `COUNTRY` · `char(24)` `[mysql/ACASDB.sql:L1210]` | no | storage: STR | — |
| 338 | `SYSTEM-REC.PRINT-SPOOL-NAME` | `Print-Spool-Name` · lvl 05 · `x(48)` `[copybooks/wssystem.cob:L79]` | `HV-PRINT-SPOOL-NAME` · `X(48)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L348]` | `PRINT-SPOOL-NAME` · `char(48)` `[mysql/ACASDB.sql:L1211]` | no | storage: STR | — |
| 339 | `SYSTEM-REC.PASS-VALUE` | `Pass-Value` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L82]` | `HV-PASS-VALUE` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L349]` | `PASS-VALUE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1212]` | no | drift: usage, digits; storage: INT | — |
| 340 | `SYSTEM-REC.LEVEL-1` | `Level-1` · lvl 07 · `9` · DISPLAY `[copybooks/wssystem.cob:L84]` | `HV-LEVEL-1` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L350]` | `LEVEL-1` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1213]` | no | drift: usage, digits; storage: INT | — |
| 341 | `SYSTEM-REC.LEVEL-2` | `Level-2` · lvl 07 · `9` · DISPLAY `[copybooks/wssystem.cob:L86]` | `HV-LEVEL-2` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L351]` | `LEVEL-2` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1214]` | no | drift: usage, digits; storage: INT | — |
| 342 | `SYSTEM-REC.LEVEL-3` | `Level-3` · lvl 07 · `9` · DISPLAY `[copybooks/wssystem.cob:L88]` | `HV-LEVEL-3` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L352]` | `LEVEL-3` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1215]` | no | drift: usage, digits; storage: INT | — |
| 343 | `SYSTEM-REC.LEVEL-4` | `Level-4` · lvl 07 · `9` · DISPLAY `[copybooks/wssystem.cob:L90]` | `HV-LEVEL-4` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L353]` | `LEVEL-4` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1216]` | no | drift: usage, digits; storage: INT | — |
| 344 | `SYSTEM-REC.LEVEL-5` | `Level-5` · lvl 07 · `9` · DISPLAY `[copybooks/wssystem.cob:L92]` | `HV-LEVEL-5` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L354]` | `LEVEL-5` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1217]` | no | drift: usage, digits; storage: INT | — |
| 345 | `SYSTEM-REC.LEVEL-6` | `Level-6` · lvl 07 · `9` · DISPLAY `[copybooks/wssystem.cob:L95]` | `HV-LEVEL-6` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L355]` | `LEVEL-6` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1218]` | no | drift: usage, digits; storage: INT | — |
| 346 | `SYSTEM-REC.PASS-WORD` | `Pass-Word` · lvl 05 · `x(4)` `[copybooks/wssystem.cob:L97]` | `HV-PASS-WORD` · `X(4)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L356]` | `PASS-WORD` · `char(4)` `[mysql/ACASDB.sql:L1219]` | no | storage: STR | — |
| 347 | `SYSTEM-REC.HOST` | `Host` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L98]` | `HV-HOST` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L357]` | `HOST` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1220]` | no | drift: usage, digits; storage: INT | — |
| 348 | `SYSTEM-REC.OP-SYSTEM` | `Op-System` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L100]` | `HV-OP-SYSTEM` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L358]` | `OP-SYSTEM` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1221]` | no | drift: usage, digits; storage: INT | — |
| 349 | `SYSTEM-REC.CURRENT-QUARTER` | `Current-Quarter` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L110]` | `HV-CURRENT-QUARTER` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L359]` | `CURRENT-QUARTER` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1222]` | no | drift: usage, digits; storage: INT | — |
| 350 | `SYSTEM-REC.FILE-SYSTEM-USED` | `File-System-Used` · lvl 07 · `9` · DISPLAY `[copybooks/wssystem.cob:L112]` | `HV-FILE-SYSTEM-USED` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L360]` | `FILE-SYSTEM-USED` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1223]` | no | drift: usage, digits; storage: INT | — |
| 351 | `SYSTEM-REC.FILE-DUPLICATES-IN-USE` | `File-Duplicates-In-Use` · lvl 07 · `9` · DISPLAY `[copybooks/wssystem.cob:L123]` | `HV-FILE-DUPLICATES-IN-USE` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L361]` | `FILE-DUPLICATES-IN-USE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1224]` | no | drift: usage, digits; storage: INT | — |
| 352 | `SYSTEM-REC.MAPS-SER` | `Maps-Ser` · lvl 05 · GROUP · group `[copybooks/wssystem.cob:L125]` | `HV-MAPS-SER` · `X(6)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L362]` | `MAPS-SER` · `char(6)` `[mysql/ACASDB.sql:L1225]` | no | derivation: GROUP_CONCATENATION | — |
| 353 | `SYSTEM-REC.DATE-FORM` | `Date-Form` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L128]` | `HV-DATE-FORM` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L363]` | `DATE-FORM` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1226]` | no | drift: usage, digits; storage: INT | — |
| 354 | `SYSTEM-REC.DATA-CAPTURE-USED` | `Data-Capture-Used` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L133]` | `HV-DATA-CAPTURE-USED` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L364]` | `DATA-CAPTURE-USED` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1227]` | no | drift: usage, digits; storage: INT | — |
| 355 | `SYSTEM-REC.RDBMS-DB-NAME` | `RDBMS-DB-Name` · lvl 05 · `x(12)` `[copybooks/wssystem.cob:L137]` | `HV-RDBMS-DB-NAME` · `X(12)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L365]` | `RDBMS-DB-NAME` · `char(12)` `[mysql/ACASDB.sql:L1228]` | no | storage: STR | — |
| 356 | `SYSTEM-REC.RDBMS-USER` | `RDBMS-User` · lvl 05 · `x(12)` `[copybooks/wssystem.cob:L138]` | `HV-RDBMS-USER` · `X(12)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L366]` | `RDBMS-USER` · `char(12)` `[mysql/ACASDB.sql:L1229]` | no | storage: STR | — |
| 357 | `SYSTEM-REC.RDBMS-PASSWD` | `RDBMS-Passwd` · lvl 05 · `x(12)` `[copybooks/wssystem.cob:L139]` | `HV-RDBMS-PASSWD` · `X(12)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L367]` | `RDBMS-PASSWD` · `char(12)` `[mysql/ACASDB.sql:L1230]` | no | storage: STR | — |
| 358 | `SYSTEM-REC.RDBMS-PORT` | `RDBMS-Port` · lvl 05 · `x(5)` `[copybooks/wssystem.cob:L142]` | `HV-RDBMS-PORT` · `X(5)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L368]` | `RDBMS-PORT` · `char(5)` `[mysql/ACASDB.sql:L1231]` | no | storage: STR | — |
| 359 | `SYSTEM-REC.RDBMS-HOST` | `RDBMS-Host` · lvl 05 · `x(32)` `[copybooks/wssystem.cob:L143]` | `HV-RDBMS-HOST` · `X(32)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L369]` | `RDBMS-HOST` · `char(32)` `[mysql/ACASDB.sql:L1232]` | no | storage: STR | — |
| 360 | `SYSTEM-REC.RDBMS-SOCKET` | `RDBMS-Socket` · lvl 05 · `x(64)` `[copybooks/wssystem.cob:L144]` | `HV-RDBMS-SOCKET` · `X(64)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L370]` | `RDBMS-SOCKET` · `char(64)` `[mysql/ACASDB.sql:L1233]` | no | storage: STR | — |
| 361 | `SYSTEM-REC.VAT-REG-NUMBER` | `VAT-Reg-Number` · lvl 05 · `x(11)` `[copybooks/wssystem.cob:L140]` | `HV-VAT-REG-NUMBER` · `X(11)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L371]` | `VAT-REG-NUMBER` · `char(11)` `[mysql/ACASDB.sql:L1234]` | no | storage: STR | — |
| 362 | `SYSTEM-REC.PARAM-RESTRICT` | `Param-Restrict` · lvl 05 · `x` `[copybooks/wssystem.cob:L141]` | `HV-PARAM-RESTRICT` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L372]` | `PARAM-RESTRICT` · `char(1)` `[mysql/ACASDB.sql:L1235]` | no | storage: STR | — |
| 363 | `SYSTEM-REC.STATS-DATE-PERIOD` | `Stats-Date-Period` · lvl 05 · `9(4)` · DISPLAY `[copybooks/wssystem.cob:L145]` | `HV-STATS-DATE-PERIOD` · `X(4)` · unsigned · NOT loaded/NOT unloaded `[common/systemMT.cbl:L373]` | `STATS-DATE-PERIOD` · `char(4)` `[mysql/ACASDB.sql:L1236]` | no | drift: usage; storage: INT | — |
| 364 | `SYSTEM-REC.P-C` | `P-C` · lvl 05 · `x` `[copybooks/wssystem.cob:L151]` | `HV-P-C` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L374]` | `P-C` · `char(1)` `[mysql/ACASDB.sql:L1237]` | no | storage: STR | — |
| 365 | `SYSTEM-REC.P-C-GROUPED` | `P-C-Grouped` · lvl 05 · `x` `[copybooks/wssystem.cob:L154]` | `HV-P-C-GROUPED` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L375]` | `P-C-GROUPED` · `char(1)` `[mysql/ACASDB.sql:L1238]` | no | storage: STR | — |
| 366 | `SYSTEM-REC.P-C-LEVEL` | `P-C-Level` · lvl 05 · `x` `[copybooks/wssystem.cob:L156]` | `HV-P-C-LEVEL` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L376]` | `P-C-LEVEL` · `char(1)` `[mysql/ACASDB.sql:L1239]` | no | storage: STR | — |
| 367 | `SYSTEM-REC.COMPS` | `Comps` · lvl 05 · `x` `[copybooks/wssystem.cob:L158]` | `HV-COMPS` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L377]` | `COMPS` · `char(1)` `[mysql/ACASDB.sql:L1240]` | no | storage: STR | — |
| 368 | `SYSTEM-REC.COMPS-ACTIVE` | `Comps-Active` · lvl 05 · `x` `[copybooks/wssystem.cob:L160]` | `HV-COMPS-ACTIVE` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L378]` | `COMPS-ACTIVE` · `char(1)` `[mysql/ACASDB.sql:L1241]` | no | storage: STR | — |
| 369 | `SYSTEM-REC.M-V` | `M-V` · lvl 05 · `x` `[copybooks/wssystem.cob:L162]` | `HV-M-V` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L379]` | `M-V` · `char(1)` `[mysql/ACASDB.sql:L1242]` | no | storage: STR | — |
| 370 | `SYSTEM-REC.ARCH` | `Arch` · lvl 05 · `x` `[copybooks/wssystem.cob:L164]` | `HV-ARCH` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L380]` | `ARCH` · `char(1)` `[mysql/ACASDB.sql:L1243]` | no | storage: STR | — |
| 371 | `SYSTEM-REC.TRANS-PRINT` | `Trans-Print` · lvl 05 · `x` `[copybooks/wssystem.cob:L166]` | `HV-TRANS-PRINT` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L381]` | `TRANS-PRINT` · `char(1)` `[mysql/ACASDB.sql:L1244]` | no | storage: STR | — |
| 372 | `SYSTEM-REC.TRANS-PRINTED` | `Trans-Printed` · lvl 05 · `x` `[copybooks/wssystem.cob:L168]` | `HV-TRANS-PRINTED` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L382]` | `TRANS-PRINTED` · `char(1)` `[mysql/ACASDB.sql:L1245]` | no | storage: STR | — |
| 373 | `SYSTEM-REC.HEADER-LEVEL` | `Header-Level` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L170]` | `HV-HEADER-LEVEL` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L383]` | `HEADER-LEVEL` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1246]` | no | drift: usage, digits; storage: INT | — |
| 374 | `SYSTEM-REC.SALES-RANGE` | `Sales-Range` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L171]` | `HV-SALES-RANGE` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L384]` | `SALES-RANGE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1247]` | no | drift: usage, digits; storage: INT | — |
| 375 | `SYSTEM-REC.PURCHASE-RANGE` | `Purchase-Range` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L172]` | `HV-PURCHASE-RANGE` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L385]` | `PURCHASE-RANGE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1248]` | no | drift: usage, digits; storage: INT | — |
| 376 | `SYSTEM-REC.VAT` | `Vat` · lvl 05 · `x` `[copybooks/wssystem.cob:L173]` | `HV-VAT` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L386]` | `VAT` · `char(1)` `[mysql/ACASDB.sql:L1249]` | no | storage: STR | — |
| 377 | `SYSTEM-REC.BATCH-ID` | `Batch-Id` · lvl 05 · `x` `[copybooks/wssystem.cob:L175]` | `HV-BATCH-ID` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L387]` | `BATCH-ID` · `char(1)` `[mysql/ACASDB.sql:L1250]` | no | storage: STR | — |
| 378 | `SYSTEM-REC.LEDGER-2ND-INDEX` | `Ledger-2nd-Index` · lvl 05 · `x` `[copybooks/wssystem.cob:L177]` | `HV-LEDGER-2ND-INDEX` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L388]` | `LEDGER-2ND-INDEX` · `char(1)` `[mysql/ACASDB.sql:L1251]` | no | storage: STR | — |
| 379 | `SYSTEM-REC.IRS-INSTEAD` | `IRS-Instead` · lvl 05 · `x` `[copybooks/wssystem.cob:L179]` | `HV-IRS-INSTEAD` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L389]` | `IRS-INSTEAD` · `char(1)` `[mysql/ACASDB.sql:L1252]` | no | storage: STR | — |
| 380 | `SYSTEM-REC.LEDGER-SEC` | `Ledger-Sec` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L182]` | `HV-LEDGER-SEC` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L390]` | `LEDGER-SEC` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1253]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 381 | `SYSTEM-REC.UPDATES` | `Updates` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L183]` | `HV-UPDATES` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L391]` | `UPDATES` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1254]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 382 | `SYSTEM-REC.POSTINGS` | `Postings` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L184]` | `HV-POSTINGS` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L392]` | `POSTINGS` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1255]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 383 | `SYSTEM-REC.NEXT-BATCH` | `Next-Batch` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L185]` | `HV-NEXT-BATCH` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L393]` | `NEXT-BATCH` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1256]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 384 | `SYSTEM-REC.EXTRA-CHARGE-AC` | `Extra-Charge-Ac` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L186]` | `HV-EXTRA-CHARGE-AC` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L394]` | `EXTRA-CHARGE-AC` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1257]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 385 | `SYSTEM-REC.VAT-AC` | `Vat-Ac` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L187]` | `HV-VAT-AC` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L395]` | `VAT-AC` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1258]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 386 | `SYSTEM-REC.PRINT-SPOOL-NAME2` | `Print-Spool-Name2` · lvl 05 · `x(48)` `[copybooks/wssystem.cob:L188]` | `HV-PRINT-SPOOL-NAME2` · `X(48)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L396]` | `PRINT-SPOOL-NAME2` · `char(48)` `[mysql/ACASDB.sql:L1259]` | no | storage: STR | — |
| 387 | `SYSTEM-REC.NEXT-FOLIO` | `Next-Folio` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L193]` | `HV-NEXT-FOLIO` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L397]` | `NEXT-FOLIO` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1260]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 388 | `SYSTEM-REC.BL-PAY-AC` | `BL-Pay-Ac` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L194]` | `HV-BL-PAY-AC` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L398]` | `BL-PAY-AC` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1261]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 389 | `SYSTEM-REC.P-CREDITORS` | `P-Creditors` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L195]` | `HV-P-CREDITORS` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L399]` | `P-CREDITORS` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1262]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 390 | `SYSTEM-REC.BL-PURCH-AC` | `BL-Purch-Ac` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L196]` | `HV-BL-PURCH-AC` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L400]` | `BL-PURCH-AC` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1263]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 391 | `SYSTEM-REC.GL-BL-PAY-AC` | `GL-BL-Pay-Ac` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L280]` | `HV-GL-BL-PAY-AC` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L401]` | `GL-BL-PAY-AC` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1264]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 392 | `SYSTEM-REC.GL-P-CREDITORS` | `GL-P-Creditors` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L281]` | `HV-GL-P-CREDITORS` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L402]` | `GL-P-CREDITORS` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1265]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 393 | `SYSTEM-REC.GL-BL-PURCH-AC` | `GL-BL-Purch-Ac` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L282]` | `HV-GL-BL-PURCH-AC` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L403]` | `GL-BL-PURCH-AC` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1266]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 394 | `SYSTEM-REC.GL-SL-PAY-AC` | `GL-SL-Pay-Ac` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L283]` | `HV-GL-SL-PAY-AC` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L404]` | `GL-SL-PAY-AC` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1267]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 395 | `SYSTEM-REC.GL-S-DEBTORS` | `GL-S-Debtors` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L284]` | `HV-GL-S-DEBTORS` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L405]` | `GL-S-DEBTORS` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1268]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 396 | `SYSTEM-REC.GL-SL-SALES-AC` | `GL-SL-Sales-Ac` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L285]` | `HV-GL-SL-SALES-AC` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L406]` | `GL-SL-SALES-AC` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1269]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 397 | `SYSTEM-REC.BL-END-CYCLE-DAT` | `BL-End-Cycle-Date` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L197]` | `HV-BL-END-CYCLE-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L407]` | `BL-END-CYCLE-DAT` · `int(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1270]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 398 | `SYSTEM-REC.BL-NEXT-BATCH` | `BL-Next-Batch` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L198]` | `HV-BL-NEXT-BATCH` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L408]` | `BL-NEXT-BATCH` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1271]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 399 | `SYSTEM-REC.AGE-TO-PAY` | `Age-To-Pay` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L199]` | `HV-AGE-TO-PAY` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L409]` | `AGE-TO-PAY` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1272]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 400 | `SYSTEM-REC.PURCHASE-LEDGER` | `Purchase-Ledger` · lvl 05 · `x` `[copybooks/wssystem.cob:L200]` | `HV-PURCHASE-LEDGER` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L410]` | `PURCHASE-LEDGER` · `char(1)` `[mysql/ACASDB.sql:L1273]` | no | storage: STR | — |
| 401 | `SYSTEM-REC.PL-DELIM` | `PL-Delim` · lvl 05 · `x` `[copybooks/wssystem.cob:L202]` | `HV-PL-DELIM` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L411]` | `PL-DELIM` · `char(1)` `[mysql/ACASDB.sql:L1274]` | no | storage: STR | — |
| 402 | `SYSTEM-REC.ENTRY-LEVEL` | `Entry-Level` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L203]` | `HV-ENTRY-LEVEL` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L412]` | `ENTRY-LEVEL` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1275]` | no | drift: usage, digits; storage: INT | — |
| 403 | `SYSTEM-REC.P-FLAG-A` | `P-Flag-A` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L204]` | `HV-P-FLAG-A` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L413]` | `P-FLAG-A` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1276]` | no | drift: usage, digits; storage: INT | — |
| 404 | `SYSTEM-REC.P-FLAG-I` | `P-Flag-I` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L205]` | `HV-P-FLAG-I` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L414]` | `P-FLAG-I` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1277]` | no | drift: usage, digits; storage: INT | — |
| 405 | `SYSTEM-REC.P-FLAG-P` | `P-Flag-P` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L206]` | `HV-P-FLAG-P` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L415]` | `P-FLAG-P` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1278]` | no | drift: usage, digits; storage: INT | — |
| 406 | `SYSTEM-REC.PL-STOCK-LINK` | `PL-Stock-Link` · lvl 05 · `x` `[copybooks/wssystem.cob:L207]` | `HV-PL-STOCK-LINK` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L416]` | `PL-STOCK-LINK` · `char(1)` `[mysql/ACASDB.sql:L1279]` | no | storage: STR | — |
| 407 | `SYSTEM-REC.PRINT-SPOOL-NAME3` | `Print-Spool-Name3` · lvl 05 · `x(48)` `[copybooks/wssystem.cob:L208]` | `HV-PRINT-SPOOL-NAME3` · `X(48)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L417]` | `PRINT-SPOOL-NAME3` · `char(48)` `[mysql/ACASDB.sql:L1280]` | no | storage: STR | — |
| 408 | `SYSTEM-REC.PL-AUTOGEN` | `PL-Autogen` · lvl 05 · `x` `[copybooks/wssystem.cob:L209]` | `HV-PL-AUTOGEN` · `X(1)` · unsigned · NOT loaded/NOT unloaded `[common/systemMT.cbl:L418]` | `PL-AUTOGEN` · `char(1)` `[mysql/ACASDB.sql:L1281]` | no | storage: STR | — |
| 409 | `SYSTEM-REC.PL-NEXT-REC` | `PL-Next-Rec` · lvl 05 · BINARY-SHORT `[copybooks/wssystem.cob:L210]` | `HV-PL-NEXT-REC` · `9(05)` · unsigned · NOT loaded/NOT unloaded `[common/systemMT.cbl:L419]` | `PL-NEXT-REC` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1282]` | no | drift: usage; storage: INT | — |
| 410 | `SYSTEM-REC.SALES-LEDGER` | `Sales-Ledger` · lvl 05 · `x` `[copybooks/wssystem.cob:L216]` | `HV-SALES-LEDGER` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L420]` | `SALES-LEDGER` · `char(1)` `[mysql/ACASDB.sql:L1283]` | no | storage: STR | — |
| 411 | `SYSTEM-REC.SL-DELIM` | `SL-Delim` · lvl 05 · `x` `[copybooks/wssystem.cob:L218]` | `HV-SL-DELIM` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L421]` | `SL-DELIM` · `char(1)` `[mysql/ACASDB.sql:L1284]` | no | storage: STR | — |
| 412 | `SYSTEM-REC.OI-3-FLAG` | `Oi-3-Flag` · lvl 05 · `x` `[copybooks/wssystem.cob:L219]` | `HV-OI-3-FLAG` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L422]` | `OI-3-FLAG` · `char(1)` `[mysql/ACASDB.sql:L1285]` | no | storage: STR | — |
| 413 | `SYSTEM-REC.CUST-FLAG` | `Cust-Flag` · lvl 05 · `x` `[copybooks/wssystem.cob:L220]` | `HV-CUST-FLAG` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L423]` | `CUST-FLAG` · `char(1)` `[mysql/ACASDB.sql:L1286]` | no | storage: STR | — |
| 414 | `SYSTEM-REC.OI-5-FLAG` | `Oi-5-Flag` · lvl 05 · `x` `[copybooks/wssystem.cob:L221]` | `HV-OI-5-FLAG` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L424]` | `OI-5-FLAG` · `char(1)` `[mysql/ACASDB.sql:L1287]` | no | storage: STR | — |
| 415 | `SYSTEM-REC.S-FLAG-OI-3` | `S-Flag-Oi-3` · lvl 05 · `x` `[copybooks/wssystem.cob:L222]` | `HV-S-FLAG-OI-3` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L425]` | `S-FLAG-OI-3` · `char(1)` `[mysql/ACASDB.sql:L1288]` | no | storage: STR | — |
| 416 | `SYSTEM-REC.FULL-INVOICING` | `Full-Invoicing` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L223]` | `HV-FULL-INVOICING` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L426]` | `FULL-INVOICING` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1289]` | no | drift: usage, digits; storage: INT | — |
| 417 | `SYSTEM-REC.S-FLAG-A` | `S-Flag-A` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L224]` | `HV-S-FLAG-A` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L427]` | `S-FLAG-A` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1290]` | no | drift: usage, digits; storage: INT | — |
| 418 | `SYSTEM-REC.S-FLAG-I` | `S-Flag-I` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L225]` | `HV-S-FLAG-I` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L428]` | `S-FLAG-I` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1291]` | no | drift: usage, digits; storage: INT | — |
| 419 | `SYSTEM-REC.S-FLAG-P` | `S-Flag-P` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L226]` | `HV-S-FLAG-P` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L429]` | `S-FLAG-P` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1292]` | no | drift: usage, digits; storage: INT | — |
| 420 | `SYSTEM-REC.SL-DUNNING` | `SL-Dunning` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L227]` | `HV-SL-DUNNING` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L430]` | `SL-DUNNING` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1293]` | no | drift: usage, digits; storage: INT | — |
| 421 | `SYSTEM-REC.SL-CHARGES` | `SL-Charges` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L228]` | `HV-SL-CHARGES` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L431]` | `SL-CHARGES` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1294]` | no | drift: usage, digits; storage: INT | — |
| 422 | `SYSTEM-REC.SL-OWN-NOS` | `Sl-Own-Nos` · lvl 05 · `x` `[copybooks/wssystem.cob:L229]` | `HV-SL-OWN-NOS` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L432]` | `SL-OWN-NOS` · `char(1)` `[mysql/ACASDB.sql:L1295]` | no | storage: STR | — |
| 423 | `SYSTEM-REC.SL-STATS-RUN` | `SL-Stats-Run` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L230]` | `HV-SL-STATS-RUN` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L433]` | `SL-STATS-RUN` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1296]` | no | drift: usage, digits; storage: INT | — |
| 424 | `SYSTEM-REC.SL-DAY-BOOK` | `Sl-Day-Book` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L231]` | `HV-SL-DAY-BOOK` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L434]` | `SL-DAY-BOOK` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1297]` | no | drift: usage, digits; storage: INT | — |
| 425 | `SYSTEM-REC.INVOICER` | `invoicer` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L232]` | `HV-INVOICER` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L435]` | `INVOICER` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1298]` | no | drift: usage, digits; storage: INT | — |
| 426 | `SYSTEM-REC.EXTRA-DESC` | `Extra-Desc` · lvl 05 · `x(14)` `[copybooks/wssystem.cob:L237]` | `HV-EXTRA-DESC` · `X(14)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L436]` | `EXTRA-DESC` · `char(14)` `[mysql/ACASDB.sql:L1299]` | no | storage: STR | — |
| 427 | `SYSTEM-REC.EXTRA-TYPE` | `Extra-Type` · lvl 05 · `x` `[copybooks/wssystem.cob:L238]` | `HV-EXTRA-TYPE` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L437]` | `EXTRA-TYPE` · `char(1)` `[mysql/ACASDB.sql:L1300]` | no | storage: STR | — |
| 428 | `SYSTEM-REC.EXTRA-PRINT` | `Extra-Print` · lvl 05 · `x` `[copybooks/wssystem.cob:L241]` | `HV-EXTRA-PRINT` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L438]` | `EXTRA-PRINT` · `char(1)` `[mysql/ACASDB.sql:L1301]` | no | storage: STR | — |
| 429 | `SYSTEM-REC.SL-STOCK-LINK` | `SL-Stock-Link` · lvl 05 · `x` `[copybooks/wssystem.cob:L242]` | `HV-SL-STOCK-LINK` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L439]` | `SL-STOCK-LINK` · `char(1)` `[mysql/ACASDB.sql:L1302]` | no | storage: STR | — |
| 430 | `SYSTEM-REC.SL-STOCK-AUDIT` | `SL-Stock-Audit` · lvl 05 · `x` `[copybooks/wssystem.cob:L243]` | `HV-SL-STOCK-AUDIT` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L440]` | `SL-STOCK-AUDIT` · `char(1)` `[mysql/ACASDB.sql:L1303]` | no | storage: STR | — |
| 431 | `SYSTEM-REC.SL-LATE-PER` | `SL-Late-Per` · lvl 05 · `99v99` · COMP `[copybooks/wssystem.cob:L245]` | `HV-SL-LATE-PER` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L441]` | `SL-LATE-PER` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1304]` | no | storage: DECIMAL | — |
| 432 | `SYSTEM-REC.SL-DISC` | `SL-Disc` · lvl 05 · `99v99` · COMP `[copybooks/wssystem.cob:L246]` | `HV-SL-DISC` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L442]` | `SL-DISC` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1305]` | no | storage: DECIMAL | — |
| 433 | `SYSTEM-REC.EXTRA-RATE` | `Extra-Rate` · lvl 05 · `99v99` · COMP `[copybooks/wssystem.cob:L247]` | `HV-EXTRA-RATE` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L443]` | `EXTRA-RATE` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1306]` | no | storage: DECIMAL | — |
| 434 | `SYSTEM-REC.SL-DAYS-1` | `SL-Days-1` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L248]` | `HV-SL-DAYS-1` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L444]` | `SL-DAYS-1` · `smallint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L1307]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 435 | `SYSTEM-REC.SL-DAYS-2` | `SL-Days-2` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L249]` | `HV-SL-DAYS-2` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L445]` | `SL-DAYS-2` · `smallint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L1308]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 436 | `SYSTEM-REC.SL-DAYS-3` | `SL-Days-3` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L250]` | `HV-SL-DAYS-3` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L446]` | `SL-DAYS-3` · `smallint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L1309]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 437 | `SYSTEM-REC.SL-CREDIT` | `SL-Credit` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L251]` | `HV-SL-CREDIT` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L447]` | `SL-CREDIT` · `smallint(3) unsigned` · unsigned `[mysql/ACASDB.sql:L1310]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 438 | `SYSTEM-REC.SL-MIN` | `SL-Min` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L253]` | `HV-SL-MIN` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L448]` | `SL-MIN` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1311]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 439 | `SYSTEM-REC.SL-MAX` | `SL-Max` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L254]` | `HV-SL-MAX` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L449]` | `SL-MAX` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1312]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 440 | `SYSTEM-REC.PF-RETENTION` | `PF-Retention` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L255]` | `HV-PF-RETENTION` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L450]` | `PF-RETENTION` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1313]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 441 | `SYSTEM-REC.FIRST-SL-BATCH` | `First-Sl-Batch` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L256]` | `HV-FIRST-SL-BATCH` · `9(05)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L451]` | `FIRST-SL-BATCH` · `smallint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1314]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 442 | `SYSTEM-REC.FIRST-SL-INV` | `First-Sl-Inv` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L257]` | `HV-FIRST-SL-INV` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L452]` | `FIRST-SL-INV` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1315]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 443 | `SYSTEM-REC.SL-LIMIT` | `SL-Limit` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L258]` | `HV-SL-LIMIT` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L453]` | `SL-LIMIT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1316]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 444 | `SYSTEM-REC.SL-PAY-AC` | `SL-Pay-Ac` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L259]` | `HV-SL-PAY-AC` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L454]` | `SL-PAY-AC` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1317]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 445 | `SYSTEM-REC.S-DEBTORS` | `S-Debtors` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L260]` | `HV-S-DEBTORS` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L455]` | `S-DEBTORS` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1318]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 446 | `SYSTEM-REC.SL-SALES-AC` | `SL-Sales-Ac` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L261]` | `HV-SL-SALES-AC` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L456]` | `SL-SALES-AC` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1319]` | no | drift: signedness, usage; storage: INT | `A-11`, `Q-3` |
| 447 | `SYSTEM-REC.S-END-CYCLE-DAT` | `S-End-Cycle-Date` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L262]` | `HV-S-END-CYCLE-DAT` · `9(10)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L457]` | `S-END-CYCLE-DAT` · `int(8) unsigned` · unsigned `[mysql/ACASDB.sql:L1320]` | no | drift: signedness, usage, name; storage: INT | `A-11`, `Q-3` |
| 448 | `SYSTEM-REC.SL-COMP-HEAD-PICK` | `SL-Comp-Head-Pick` · lvl 05 · `x` `[copybooks/wssystem.cob:L263]` | `HV-SL-COMP-HEAD-PICK` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L458]` | `SL-COMP-HEAD-PICK` · `char(1)` `[mysql/ACASDB.sql:L1321]` | no | storage: STR | — |
| 449 | `SYSTEM-REC.SL-COMP-HEAD-INV` | `SL-Comp-Head-Inv` · lvl 05 · `x` `[copybooks/wssystem.cob:L265]` | `HV-SL-COMP-HEAD-INV` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L459]` | `SL-COMP-HEAD-INV` · `char(1)` `[mysql/ACASDB.sql:L1322]` | no | storage: STR | — |
| 450 | `SYSTEM-REC.SL-COMP-HEAD-STAT` | `SL-Comp-Head-Stat` · lvl 05 · `x` `[copybooks/wssystem.cob:L267]` | `HV-SL-COMP-HEAD-STAT` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L460]` | `SL-COMP-HEAD-STAT` · `char(1)` `[mysql/ACASDB.sql:L1323]` | no | storage: STR | — |
| 451 | `SYSTEM-REC.SL-COMP-HEAD-LETS` | `SL-Comp-Head-Lets` · lvl 05 · `x` `[copybooks/wssystem.cob:L269]` | `HV-SL-COMP-HEAD-LETS` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L461]` | `SL-COMP-HEAD-LETS` · `char(1)` `[mysql/ACASDB.sql:L1324]` | no | storage: STR | — |
| 452 | `SYSTEM-REC.SL-VAT-PRINTED` | `SL-VAT-Printed` · lvl 05 · `x` `[copybooks/wssystem.cob:L271]` | `HV-SL-VAT-PRINTED` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L462]` | `SL-VAT-PRINTED` · `char(1)` `[mysql/ACASDB.sql:L1325]` | no | storage: STR | — |
| 453 | `SYSTEM-REC.SL-INVOICE-LINES` | `SL-Invoice-Lines` · lvl 05 · `99` · DISPLAY `[copybooks/wssystem.cob:L273]` | `HV-SL-INVOICE-LINES` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L463]` | `SL-INVOICE-LINES` · `tinyint(2) unsigned` · unsigned `[mysql/ACASDB.sql:L1326]` | no | drift: usage, digits; storage: INT | — |
| 454 | `SYSTEM-REC.SL-AUTOGEN` | `SL-Autogen` · lvl 05 · `x` `[copybooks/wssystem.cob:L274]` | `HV-SL-AUTOGEN` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L464]` | `SL-AUTOGEN` · `char(1)` `[mysql/ACASDB.sql:L1327]` | no | storage: STR | — |
| 455 | `SYSTEM-REC.SL-NEXT-REC` | `SL-Next-Rec` · lvl 05 · BINARY-SHORT `[copybooks/wssystem.cob:L275]` | `HV-SL-NEXT-REC` · `S9(05)` · signed · loaded/unloaded `[common/systemMT.cbl:L465]` | `SL-NEXT-REC` · `smallint(4)` `[mysql/ACASDB.sql:L1328]` | no | drift: signedness, usage; storage: INT | — |
| 456 | `SYSTEM-REC.STK-ABREV-REF` | `Stk-Abrev-Ref` · lvl 05 · `x(6)` `[copybooks/wssystem.cob:L291]` | `HV-STK-ABREV-REF` · `X(6)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L466]` | `STK-ABREV-REF` · `char(6)` `[mysql/ACASDB.sql:L1329]` | no | storage: STR | — |
| 457 | `SYSTEM-REC.STK-DEBUG` | `Stk-Debug` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L292]` | `HV-STK-DEBUG` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L467]` | `STK-DEBUG` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1330]` | no | drift: usage, digits; storage: INT | — |
| 458 | `SYSTEM-REC.STK-MANU-USED` | `Stk-Manu-Used` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L293]` | `HV-STK-MANU-USED` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L468]` | `STK-MANU-USED` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1331]` | no | drift: usage, digits; storage: INT | — |
| 459 | `SYSTEM-REC.STK-OE-USED` | `Stk-OE-Used` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L294]` | `HV-STK-OE-USED` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L469]` | `STK-OE-USED` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1332]` | no | drift: usage, digits; storage: INT | — |
| 460 | `SYSTEM-REC.STK-AUDIT-USED` | `Stk-Audit-Used` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L295]` | `HV-STK-AUDIT-USED` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L470]` | `STK-AUDIT-USED` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1333]` | no | drift: usage, digits; storage: INT | — |
| 461 | `SYSTEM-REC.STK-MOV-AUDIT` | `Stk-Mov-Audit` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L296]` | `HV-STK-MOV-AUDIT` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L471]` | `STK-MOV-AUDIT` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1334]` | no | drift: usage, digits; storage: INT | — |
| 462 | `SYSTEM-REC.STK-PERIOD-CUR` | `Stk-Period-Cur` · lvl 05 · `x` `[copybooks/wssystem.cob:L297]` | `HV-STK-PERIOD-CUR` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L472]` | `STK-PERIOD-CUR` · `char(1)` `[mysql/ACASDB.sql:L1335]` | no | storage: STR | — |
| 463 | `SYSTEM-REC.STK-PERIOD-DAT` | `Stk-Period-dat` · lvl 05 · `x` `[copybooks/wssystem.cob:L298]` | `HV-STK-PERIOD-DAT` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L473]` | `STK-PERIOD-DAT` · `char(1)` `[mysql/ACASDB.sql:L1336]` | no | storage: STR | — |
| 464 | `SYSTEM-REC.STOCK-CONTROL` | `Stock-Control` · lvl 05 · `x` `[copybooks/wssystem.cob:L300]` | `HV-STOCK-CONTROL` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L474]` | `STOCK-CONTROL` · `char(1)` `[mysql/ACASDB.sql:L1337]` | no | storage: STR | — |
| 465 | `SYSTEM-REC.STK-AVERAGING` | `Stk-Averaging` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L302]` | `HV-STK-AVERAGING` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L475]` | `STK-AVERAGING` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1338]` | no | drift: usage, digits; storage: INT | — |
| 466 | `SYSTEM-REC.STK-ACTIVITY-REP-RUN` | `Stk-Activity-Rep-Run` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L304]` | `HV-STK-ACTIVITY-REP-RUN` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L476]` | `STK-ACTIVITY-REP-RUN` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1339]` | no | drift: usage, digits; storage: INT | — |
| 467 | `SYSTEM-REC.STK-PAGE-LINES` | `Stk-Page-Lines` · lvl 05 · BINARY-CHAR `[copybooks/wssystem.cob:L306]` | `HV-STK-PAGE-LINES` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L477]` | `STK-PAGE-LINES` · `tinyint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1340]` | no | drift: usage; storage: INT | — |
| 468 | `SYSTEM-REC.STK-AUDIT-NO` | `Stk-Audit-No` · lvl 05 · BINARY-CHAR `[copybooks/wssystem.cob:L307]` | `HV-STK-AUDIT-NO` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L478]` | `STK-AUDIT-NO` · `tinyint(4) unsigned` · unsigned `[mysql/ACASDB.sql:L1341]` | no | drift: usage; storage: INT | — |
| 469 | `SYSTEM-REC.CLIENT` | `Client` · lvl 05 · `x(24)` `[copybooks/wssystem.cob:L310]` | `HV-CLIENT` · `X(24)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L479]` | `CLIENT` · `char(24)` `[mysql/ACASDB.sql:L1342]` | no | storage: STR | — |
| 470 | `SYSTEM-REC.NEXT-POST` | `Next-Post` · lvl 05 · `9(5)` · DISPLAY `[copybooks/wssystem.cob:L311]` | `HV-NEXT-POST` · `9(08)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L480]` | `NEXT-POST` · `mediumint(5) unsigned` · unsigned `[mysql/ACASDB.sql:L1343]` | no | drift: usage, digits; storage: INT | — |
| 471 | `SYSTEM-REC.VAT1` | `vat1` · lvl 07 · `99v99` · DISPLAY `[copybooks/wssystem.cob:L313]` | `HV-VAT1` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L481]` | `VAT1` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1344]` | no | drift: usage; storage: DECIMAL | — |
| 472 | `SYSTEM-REC.VAT2` | `vat2` · lvl 07 · `99v99` · DISPLAY `[copybooks/wssystem.cob:L314]` | `HV-VAT2` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L482]` | `VAT2` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1345]` | no | drift: usage; storage: DECIMAL | — |
| 473 | `SYSTEM-REC.VAT3` | `vat3` · lvl 07 · `99v99` · DISPLAY `[copybooks/wssystem.cob:L315]` | `HV-VAT3` · `9(02)V9(02)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L483]` | `VAT3` · `decimal(4,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1346]` | no | drift: usage; storage: DECIMAL | — |
| 474 | `SYSTEM-REC.IRS-PASS-VALUE` | `IRS-Pass-Value` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L318]` | `HV-IRS-PASS-VALUE` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L484]` | `IRS-PASS-VALUE` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1347]` | no | drift: usage, digits; storage: INT | — |
| 475 | `SYSTEM-REC.SAVE-SEQU` | `Save-Sequ` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L319]` | `HV-SAVE-SEQU` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L485]` | `SAVE-SEQU` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1348]` | no | drift: usage, digits; storage: INT | — |
| 476 | `SYSTEM-REC.SYSTEM-WORK-GROUP` | `System-Work-Group` · lvl 05 · `x(18)` `[copybooks/wssystem.cob:L320]` | `HV-SYSTEM-WORK-GROUP` · `X(18)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L486]` | `SYSTEM-WORK-GROUP` · `char(18)` `[mysql/ACASDB.sql:L1349]` | no | storage: STR | — |
| 477 | `SYSTEM-REC.PL-APP-CREATED` | `PL-App-Created` · lvl 05 · `x` `[copybooks/wssystem.cob:L321]` | `HV-PL-APP-CREATED` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L487]` | `PL-APP-CREATED` · `char(1)` `[mysql/ACASDB.sql:L1350]` | no | storage: STR | — |
| 478 | `SYSTEM-REC.PL-APPROP-AC` | `PL-Approp-AC` · lvl 07 · `9(5)` · DISPLAY `[copybooks/wssystem.cob:L325]` | `HV-PL-APPROP-AC` · `9(08)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L488]` | `PL-APPROP-AC` · `mediumint(5) unsigned` · unsigned `[mysql/ACASDB.sql:L1351]` | no | drift: usage, digits; derivation: REDEFINES_ALTERNATIVE; storage: INT | — |
| 479 | `SYSTEM-REC.1ST-TIME-FLAG` | `1st-Time-Flag` · lvl 05 · `9` · DISPLAY `[copybooks/wssystem.cob:L326]` | `HV-1ST-TIME-FLAG` · `9(03)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L489]` | `1ST-TIME-FLAG` · `tinyint(1) unsigned` · unsigned `[mysql/ACASDB.sql:L1352]` | no | drift: usage, digits; storage: INT | — |
| 480 | `SYSTEM-REC.PL-APPROP-AC6` | `PL-Approp-AC6` · lvl 05 · `9(6)` · DISPLAY `[copybooks/wssystem.cob:L322]` | `HV-PL-APPROP-AC6` · `9(08)` · unsigned · NOT loaded/NOT unloaded `[common/systemMT.cbl:L490]` | `PL-APPROP-AC6` · `mediumint(6) unsigned` · unsigned `[mysql/ACASDB.sql:L1353]` | no | drift: usage, digits; storage: INT | — |
| 481 | `SYSTEM-REC.SL-BO-FLAG` | `SL-BO-Flag` · lvl 05 · `x` `[copybooks/wssystem.cob:L276]` | `HV-SL-BO-FLAG` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L491]` | `SL-BO-FLAG` · `char(1)` `[mysql/ACASDB.sql:L1354]` | no | storage: STR | — |
| 482 | `SYSTEM-REC.STK-BO-ACTIVE` | `Stk-BO-Active` · lvl 05 · `x` `[copybooks/wssystem.cob:L305]` | `HV-STK-BO-ACTIVE` · `X(1)` · unsigned · loaded/unloaded `[common/systemMT.cbl:L492]` | `STK-BO-ACTIVE` · `char(1)` `[mysql/ACASDB.sql:L1355]` | no | storage: STR | — |

#### `SYSTOT-REC` — 21 columns · bridge `sys4MT` · handler `acas000` · facade `System totals`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 483 | `SYSTOT-REC.LEDGER-TOTALS-REC-KEY` | **absent** | `HV-LEDGER-TOTALS-REC-KEY` · `9(03)` · unsigned · loaded/NOT unloaded `[common/sys4MT.cbl:L315]` | `LEDGER-TOTALS-REC-KEY` · `tinyint(1) unsigned` · unsigned · **PK** `[mysql/ACASDB.sql:L1377]` | **yes** | derivation: BRIDGE_DERIVED | — |
| 484 | `SYSTOT-REC.SL-OS-BAL-LAST-MONTH` | `sl-os-bal-last-month` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L10]` | `HV-SL-OS-BAL-LAST-MONTH` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L316]` | `SL-OS-BAL-LAST-MONTH` · `decimal(10,2)` `[mysql/ACASDB.sql:L1378]` | no | drift: usage; storage: DECIMAL | — |
| 485 | `SYSTOT-REC.SL-OS-BAL-THIS-MONTH` | `sl-os-bal-this-month` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L11]` | `HV-SL-OS-BAL-THIS-MONTH` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L317]` | `SL-OS-BAL-THIS-MONTH` · `decimal(10,2)` `[mysql/ACASDB.sql:L1379]` | no | drift: usage; storage: DECIMAL | — |
| 486 | `SYSTOT-REC.SL-INVOICES-THIS-MONTH` | `sl-invoices-this-month` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L12]` | `HV-SL-INVOICES-THIS-MONTH` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L318]` | `SL-INVOICES-THIS-MONTH` · `decimal(10,2)` `[mysql/ACASDB.sql:L1380]` | no | drift: usage; storage: DECIMAL | — |
| 487 | `SYSTOT-REC.SL-CREDIT-NOTES-THIS-MONTH` | `sl-credit-notes-this-month` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L13]` | `HV-SL-CREDIT-NOTES-THIS-MONTH` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L319]` | `SL-CREDIT-NOTES-THIS-MONTH` · `decimal(10,2)` `[mysql/ACASDB.sql:L1381]` | no | drift: usage; storage: DECIMAL | — |
| 488 | `SYSTOT-REC.SL-VARIANCE` | `sl-variance` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L14]` | `HV-SL-VARIANCE` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L320]` | `SL-VARIANCE` · `decimal(10,2)` `[mysql/ACASDB.sql:L1382]` | no | drift: usage; storage: DECIMAL | — |
| 489 | `SYSTOT-REC.SL-CREDIT-DEDUCTIONS` | `sl-credit-deductions` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L15]` | `HV-SL-CREDIT-DEDUCTIONS` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L321]` | `SL-CREDIT-DEDUCTIONS` · `decimal(10,2)` `[mysql/ACASDB.sql:L1383]` | no | drift: usage; storage: DECIMAL | — |
| 490 | `SYSTOT-REC.SL-CN-UNAPPL-THIS-MONTH` | `sl-cn-unappl-this-month` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L16]` | `HV-SL-CN-UNAPPL-THIS-MONTH` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L322]` | `SL-CN-UNAPPL-THIS-MONTH` · `decimal(10,2)` `[mysql/ACASDB.sql:L1384]` | no | drift: usage; storage: DECIMAL | — |
| 491 | `SYSTOT-REC.SL-PAYMENTS` | `sl-payments` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L17]` | `HV-SL-PAYMENTS` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L323]` | `SL-PAYMENTS` · `decimal(10,2)` `[mysql/ACASDB.sql:L1385]` | no | drift: usage; storage: DECIMAL | — |
| 492 | `SYSTOT-REC.SL4-SPARE1` | `sl4-spare1` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L18]` | `HV-SL4-SPARE1` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L324]` | `SL4-SPARE1` · `decimal(10,2)` `[mysql/ACASDB.sql:L1386]` | no | drift: usage; storage: DECIMAL | — |
| 493 | `SYSTOT-REC.SL4-SPARE2` | `sl4-spare2` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L19]` | `HV-SL4-SPARE2` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L325]` | `SL4-SPARE2` · `decimal(10,2)` `[mysql/ACASDB.sql:L1387]` | no | drift: usage; storage: DECIMAL | — |
| 494 | `SYSTOT-REC.PL-OS-BAL-LAST-MONTH` | `pl-os-bal-last-month` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L21]` | `HV-PL-OS-BAL-LAST-MONTH` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L326]` | `PL-OS-BAL-LAST-MONTH` · `decimal(10,2)` `[mysql/ACASDB.sql:L1388]` | no | drift: usage; storage: DECIMAL | — |
| 495 | `SYSTOT-REC.PL-OS-BAL-THIS-MONTH` | `pl-os-bal-this-month` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L22]` | `HV-PL-OS-BAL-THIS-MONTH` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L327]` | `PL-OS-BAL-THIS-MONTH` · `decimal(10,2)` `[mysql/ACASDB.sql:L1389]` | no | drift: usage; storage: DECIMAL | — |
| 496 | `SYSTOT-REC.PL-INVOICES-THIS-MONTH` | `pl-invoices-this-month` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L23]` | `HV-PL-INVOICES-THIS-MONTH` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L328]` | `PL-INVOICES-THIS-MONTH` · `decimal(10,2)` `[mysql/ACASDB.sql:L1390]` | no | drift: usage; storage: DECIMAL | — |
| 497 | `SYSTOT-REC.PL-CREDIT-NOTES-THIS-MONTH` | `pl-credit-notes-this-month` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L24]` | `HV-PL-CREDIT-NOTES-THIS-MONTH` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L329]` | `PL-CREDIT-NOTES-THIS-MONTH` · `decimal(10,2)` `[mysql/ACASDB.sql:L1391]` | no | drift: usage; storage: DECIMAL | — |
| 498 | `SYSTOT-REC.PL-VARIANCE` | `pl-variance` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L25]` | `HV-PL-VARIANCE` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L330]` | `PL-VARIANCE` · `decimal(10,2)` `[mysql/ACASDB.sql:L1392]` | no | drift: usage; storage: DECIMAL | — |
| 499 | `SYSTOT-REC.PL-CREDIT-DEDUCTIONS` | `pl-credit-deductions` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L26]` | `HV-PL-CREDIT-DEDUCTIONS` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L331]` | `PL-CREDIT-DEDUCTIONS` · `decimal(10,2)` `[mysql/ACASDB.sql:L1393]` | no | drift: usage; storage: DECIMAL | — |
| 500 | `SYSTOT-REC.PL-CN-UNAPPL-THIS-MONTH` | `pl-cn-unappl-this-month` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L27]` | `HV-PL-CN-UNAPPL-THIS-MONTH` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L332]` | `PL-CN-UNAPPL-THIS-MONTH` · `decimal(10,2)` `[mysql/ACASDB.sql:L1394]` | no | drift: usage; storage: DECIMAL | — |
| 501 | `SYSTOT-REC.PL-PAYMENTS` | `pl-payments` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L28]` | `HV-PL-PAYMENTS` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L333]` | `PL-PAYMENTS` · `decimal(10,2)` `[mysql/ACASDB.sql:L1395]` | no | drift: usage; storage: DECIMAL | — |
| 502 | `SYSTOT-REC.SL4-SPARE3` | `sl4-spare3` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L29]` | `HV-SL4-SPARE3` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L334]` | `SL4-SPARE3` · `decimal(10,2)` `[mysql/ACASDB.sql:L1396]` | no | drift: usage; storage: DECIMAL | `A-20` |
| 503 | `SYSTOT-REC.SL4-SPARE4` | `sl4-spare4` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wssys4.cob:L30]` | `HV-SL4-SPARE4` · `S9(08)V9(02)` · signed · loaded/unloaded `[common/sys4MT.cbl:L335]` | `SL4-SPARE4` · `decimal(10,2)` `[mysql/ACASDB.sql:L1397]` | no | drift: usage; storage: DECIMAL | `A-20` |

#### `VALUEANAL-REC` — 10 columns · bridge `valueMT` · handler `acas013` · facade `Value`

| # | Dictionary key | Copybook / program-source field | Bridge host variable | SQL column | One-sided | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | :---: | --- | --- |
| 504 | `VALUEANAL-REC.VA-CODE` | `va-code` · lvl 03 · GROUP · group `[copybooks/wsval.cob:L10]` | `HV-VA-CODE` · `X(3)` · unsigned · loaded/unloaded `[common/valueMT.cbl:L287]` | `VA-CODE` · `char(3)` · **PK** `[mysql/ACASDB.sql:L1419]` | no | derivation: GROUP_CONCATENATION | — |
| 505 | `VALUEANAL-REC.VA-GL` | `va-gl` · lvl 03 · `9(6)` · DISPLAY `[copybooks/wsval.cob:L15]` | `HV-VA-GL` · `9(08)` · unsigned · loaded/unloaded `[common/valueMT.cbl:L288]` | `VA-GL` · `mediumint(6) unsigned` · unsigned `[mysql/ACASDB.sql:L1420]` | no | drift: usage, digits; storage: INT | — |
| 506 | `VALUEANAL-REC.VA-DESC` | `va-desc` · lvl 03 · `x(24)` `[copybooks/wsval.cob:L16]` | `HV-VA-DESC` · `X(24)` · unsigned · loaded/unloaded `[common/valueMT.cbl:L289]` | `VA-DESC` · `char(24)` `[mysql/ACASDB.sql:L1421]` | no | storage: STR | — |
| 507 | `VALUEANAL-REC.VA-PRINT` | `va-print` · lvl 03 · `xxx` `[copybooks/wsval.cob:L17]` | `HV-VA-PRINT` · `X(3)` · unsigned · loaded/unloaded `[common/valueMT.cbl:L290]` | `VA-PRINT` · `char(3)` `[mysql/ACASDB.sql:L1422]` | no | storage: STR | — |
| 508 | `VALUEANAL-REC.VA-T-THIS` | `va-t-this` · lvl 03 · `9(5)` · COMP `[copybooks/wsval.cob:L18]` | `HV-VA-T-THIS` · `9(08)` · unsigned · loaded/unloaded `[common/valueMT.cbl:L291]` | `VA-T-THIS` · `mediumint(5) unsigned` · unsigned `[mysql/ACASDB.sql:L1423]` | no | drift: digits; storage: INT | — |
| 509 | `VALUEANAL-REC.VA-T-LAST` | `va-t-last` · lvl 03 · `9(5)` · COMP `[copybooks/wsval.cob:L19]` | `HV-VA-T-LAST` · `9(08)` · unsigned · loaded/unloaded `[common/valueMT.cbl:L292]` | `VA-T-LAST` · `mediumint(5) unsigned` · unsigned `[mysql/ACASDB.sql:L1424]` | no | drift: digits; storage: INT | — |
| 510 | `VALUEANAL-REC.VA-T-YEAR` | `va-t-year` · lvl 03 · `9(5)` · COMP `[copybooks/wsval.cob:L20]` | `HV-VA-T-YEAR` · `9(08)` · unsigned · loaded/unloaded `[common/valueMT.cbl:L293]` | `VA-T-YEAR` · `mediumint(5) unsigned` · unsigned `[mysql/ACASDB.sql:L1425]` | no | drift: digits; storage: INT | — |
| 511 | `VALUEANAL-REC.VA-V-THIS` | `va-v-this` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wsval.cob:L21]` | `HV-VA-V-THIS` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/valueMT.cbl:L294]` | `VA-V-THIS` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1426]` | no | drift: signedness, usage; storage: DECIMAL | `A-11`, `Q-3` |
| 512 | `VALUEANAL-REC.VA-V-LAST` | `va-v-last` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wsval.cob:L22]` | `HV-VA-V-LAST` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/valueMT.cbl:L295]` | `VA-V-LAST` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1427]` | no | drift: signedness, usage; storage: DECIMAL | `A-11`, `Q-3` |
| 513 | `VALUEANAL-REC.VA-V-YEAR` | `va-v-year` · lvl 03 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/wsval.cob:L23]` | `HV-VA-V-YEAR` · `9(08)V9(02)` · unsigned · loaded/unloaded `[common/valueMT.cbl:L296]` | `VA-V-YEAR` · `decimal(10,2) unsigned` · unsigned `[mysql/ACASDB.sql:L1428]` | no | drift: signedness, usage; storage: DECIMAL | `A-11`, `Q-3` |

### A.2 The 554 entries that declare no column, by declaring file

These are the record-layout entries with no relational counterpart: group items, `FILLER`s,
`REDEFINES` views, condition-name carriers, and the fields of records the cycle passes through
linkage or a work file rather than through a table. Every one is `one_sided: true`, and each is
here because R-5 says *every* field maps to an entry — not every field that happens to reach SQL.

#### `copybooks/wsanal.cob` — 5 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 1 | `WS-Analysis-Record.WS-Analysis-Record` | `WS-Analysis-Record` · lvl 01 · GROUP · group `[copybooks/wsanal.cob:L9]` | copybook | — | — |
| 2 | `WS-Analysis-Record.Pa-System` | `Pa-System` · lvl 05 · `x` `[copybooks/wsanal.cob:L11]` | copybook | storage: STR | — |
| 3 | `WS-Analysis-Record.Pa-Group` | `Pa-Group` · lvl 05 · GROUP · group `[copybooks/wsanal.cob:L12]` | copybook | — | — |
| 4 | `WS-Analysis-Record.Pa-First` | `Pa-First` · lvl 07 · `x` `[copybooks/wsanal.cob:L13]` | copybook | storage: STR | — |
| 5 | `WS-Analysis-Record.Pa-Second` | `Pa-Second` · lvl 07 · `x` `[copybooks/wsanal.cob:L14]` | copybook | storage: STR | — |

#### `copybooks/wsbatch.cob` — 7 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 6 | `WS-Batch-Record.WS-Batch-Record` | `WS-Batch-Record` · lvl 01 · GROUP · group `[copybooks/wsbatch.cob:L13]` | copybook | — | `A-15`, `Q-4` |
| 7 | `WS-Batch-Record.WS-Batch-Key` | `WS-Batch-Key` · lvl 03 · GROUP · group `[copybooks/wsbatch.cob:L14]` | copybook | — | `A-15`, `Q-4` |
| 8 | `WS-Batch-Record.WS-Ledger` | `WS-Ledger` · lvl 05 · `9` · DISPLAY `[copybooks/wsbatch.cob:L15]` | copybook | storage: INT | `A-15`, `Q-4` |
| 9 | `WS-Batch-Record.WS-Batch-Nos` | `WS-Batch-Nos` · lvl 05 · `9(5)` · DISPLAY `[copybooks/wsbatch.cob:L19]` | copybook | storage: INT | `A-15`, `Q-4` |
| 10 | `WS-Batch-Record.Dates` | `Dates` · lvl 03 · GROUP · group `[copybooks/wsbatch.cob:L35]` | copybook | — | `A-15`, `Q-4` |
| 11 | `WS-Batch-Record.Amounts` | `Amounts` · lvl 03 · GROUP · group `[copybooks/wsbatch.cob:L40]` | copybook | — | `A-15`, `Q-4` |
| 12 | `WS-Batch-Record.posting-data` | `posting-data` · lvl 03 · GROUP · group `[copybooks/wsbatch.cob:L47]` | copybook | — | `A-15`, `Q-4` |

#### `copybooks/wsledger.cob` — 12 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 13 | `WS-Ledger-Record.WS-Ledger-Record` | `WS-Ledger-Record` · lvl 01 · GROUP · group `[copybooks/wsledger.cob:L12]` | copybook | — | — |
| 14 | `WS-Ledger-Record.WS-Ledger-Key` | `WS-Ledger-Key` · lvl 03 · GROUP · group `[copybooks/wsledger.cob:L13]` | copybook | — | — |
| 15 | `WS-Ledger-Record.WS-Ledger-Nos` | `WS-Ledger-Nos` · lvl 05 · `9(6)` · DISPLAY `[copybooks/wsledger.cob:L14]` | copybook | storage: INT | — |
| 16 | `WS-Ledger-Record.filler#16` | `filler` · lvl 05 · GROUP · redefines `WS-Ledger-Nos` · group · FILLER `[copybooks/wsledger.cob:L16]` | copybook | — | — |
| 17 | `WS-Ledger-Record.Ledger-n` | `Ledger-n` · lvl 07 · `9(4)` · DISPLAY `[copybooks/wsledger.cob:L17]` | copybook | storage: INT | — |
| 18 | `WS-Ledger-Record.Ledger-s` | `Ledger-s` · lvl 07 · `9(2)` · DISPLAY `[copybooks/wsledger.cob:L18]` | copybook | storage: INT | — |
| 19 | `WS-Ledger-Record.Ledger-PC` | `Ledger-PC` · lvl 05 · `9(2)` · DISPLAY `[copybooks/wsledger.cob:L20]` | copybook | storage: INT | — |
| 20 | `WS-Ledger-Record.filler#26` | `filler` · lvl 03 · `x(5)` · FILLER `[copybooks/wsledger.cob:L26]` | copybook | storage: STR | — |
| 21 | `WS-Ledger-Record.Quarters` | `Quarters` · lvl 03 · GROUP · group `[copybooks/wsledger.cob:L30]` | copybook | — | — |
| 22 | `WS-Ledger-Record.filler#35` | `filler` · lvl 03 · GROUP · redefines `Quarters` · group · FILLER `[copybooks/wsledger.cob:L35]` | copybook | — | — |
| 23 | `WS-Ledger-Record.Ledger-Q` | `Ledger-Q` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY · occurs 4 `[copybooks/wsledger.cob:L36]` | copybook | storage: DECIMAL | — |
| 24 | `WS-Ledger-Record.filler#37` | `filler` · lvl 03 · `x(50)` · FILLER `[copybooks/wsledger.cob:L37]` | copybook | storage: STR | — |

#### `copybooks/wspost.cob` — 3 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 25 | `WS-Posting-Record.WS-Posting-Record` | `WS-Posting-Record` · lvl 01 · GROUP · group `[copybooks/wspost.cob:L12]` | copybook | — | — |
| 26 | `WS-Posting-Record.Batch` | `Batch` · lvl 05 · `9(5)` · DISPLAY `[copybooks/wspost.cob:L15]` | copybook | storage: INT | — |
| 27 | `WS-Posting-Record.Post-Number` | `Post-Number` · lvl 05 · `9(5)` · DISPLAY `[copybooks/wspost.cob:L16]` | copybook | storage: INT | — |

#### `copybooks/irswsdflt.cob` — 2 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 28 | `Default-Record.Default-Record#8` | `Default-Record` · lvl 01 · GROUP · group `[copybooks/irswsdflt.cob:L8]` | copybook | — | — |
| 29 | `Default-Record.Def-Group#9` | `Def-Group` · lvl 03 · GROUP · occurs 33 · group `[copybooks/irswsdflt.cob:L9]` | copybook | — | — |

#### `copybooks/irswsfinal.cob` — 58 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 30 | `Final-Record.Final-Record#7` | `Final-Record` · lvl 01 · GROUP · group `[copybooks/irswsfinal.cob:L7]` | copybook | — | — |
| 31 | `Final-Record.ar1-fields` | `ar1-fields` · lvl 03 · GROUP · group `[copybooks/irswsfinal.cob:L8]` | copybook | — | — |
| 32 | `Final-Record.ar1-1` | `ar1-1` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L9]` | copybook | storage: STR | — |
| 33 | `Final-Record.ar1-2` | `ar1-2` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L10]` | copybook | storage: STR | — |
| 34 | `Final-Record.ar1-3` | `ar1-3` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L11]` | copybook | storage: STR | — |
| 35 | `Final-Record.ar1-4` | `ar1-4` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L12]` | copybook | storage: STR | — |
| 36 | `Final-Record.ar1-5` | `ar1-5` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L13]` | copybook | storage: STR | — |
| 37 | `Final-Record.ar1-6` | `ar1-6` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L14]` | copybook | storage: STR | — |
| 38 | `Final-Record.ar1-7` | `ar1-7` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L15]` | copybook | storage: STR | — |
| 39 | `Final-Record.ar1-8` | `ar1-8` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L16]` | copybook | storage: STR | — |
| 40 | `Final-Record.ar1-9` | `ar1-9` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L17]` | copybook | storage: STR | — |
| 41 | `Final-Record.ar1-10` | `ar1-10` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L18]` | copybook | storage: STR | — |
| 42 | `Final-Record.ar1-11` | `ar1-11` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L19]` | copybook | storage: STR | — |
| 43 | `Final-Record.ar1-12` | `ar1-12` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L20]` | copybook | storage: STR | — |
| 44 | `Final-Record.ar1-13` | `ar1-13` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L21]` | copybook | storage: STR | — |
| 45 | `Final-Record.ar1-14` | `ar1-14` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L22]` | copybook | storage: STR | — |
| 46 | `Final-Record.ar1-15` | `ar1-15` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L23]` | copybook | storage: STR | — |
| 47 | `Final-Record.ar1-16` | `ar1-16` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L24]` | copybook | storage: STR | — |
| 48 | `Final-Record.ar1-17` | `ar1-17` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L25]` | copybook | storage: STR | — |
| 49 | `Final-Record.ar1-18` | `ar1-18` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L26]` | copybook | storage: STR | — |
| 50 | `Final-Record.ar1-19` | `ar1-19` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L27]` | copybook | storage: STR | — |
| 51 | `Final-Record.ar1-20` | `ar1-20` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L28]` | copybook | storage: STR | — |
| 52 | `Final-Record.ar1-21` | `ar1-21` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L29]` | copybook | storage: STR | — |
| 53 | `Final-Record.ar1-22` | `ar1-22` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L30]` | copybook | storage: STR | — |
| 54 | `Final-Record.ar1-23` | `ar1-23` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L31]` | copybook | storage: STR | — |
| 55 | `Final-Record.ar1-24` | `ar1-24` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L32]` | copybook | storage: STR | — |
| 56 | `Final-Record.ar1-25` | `ar1-25` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L33]` | copybook | storage: STR | — |
| 57 | `Final-Record.ar1-26` | `ar1-26` · lvl 05 · `x(24)` `[copybooks/irswsfinal.cob:L34]` | copybook | storage: STR | — |
| 58 | `Final-Record.filler#35` | `filler` · lvl 03 · GROUP · redefines `ar1-fields` · group · FILLER `[copybooks/irswsfinal.cob:L35]` | copybook | — | — |
| 59 | `Final-Record.ar2-fields` | `ar2-fields` · lvl 03 · GROUP · group `[copybooks/irswsfinal.cob:L38]` | copybook | — | — |
| 60 | `Final-Record.ar2-1` | `ar2-1` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L39]` | copybook | storage: STR | — |
| 61 | `Final-Record.ar2-2` | `ar2-2` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L40]` | copybook | storage: STR | — |
| 62 | `Final-Record.ar2-3` | `ar2-3` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L41]` | copybook | storage: STR | — |
| 63 | `Final-Record.ar2-4` | `ar2-4` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L42]` | copybook | storage: STR | — |
| 64 | `Final-Record.ar2-5` | `ar2-5` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L43]` | copybook | storage: STR | — |
| 65 | `Final-Record.ar2-6` | `ar2-6` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L44]` | copybook | storage: STR | — |
| 66 | `Final-Record.ar2-7` | `ar2-7` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L45]` | copybook | storage: STR | — |
| 67 | `Final-Record.ar2-8` | `ar2-8` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L46]` | copybook | storage: STR | — |
| 68 | `Final-Record.ar2-9` | `ar2-9` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L47]` | copybook | storage: STR | — |
| 69 | `Final-Record.ar2-10` | `ar2-10` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L48]` | copybook | storage: STR | — |
| 70 | `Final-Record.ar2-11` | `ar2-11` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L49]` | copybook | storage: STR | — |
| 71 | `Final-Record.ar2-12` | `ar2-12` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L50]` | copybook | storage: STR | — |
| 72 | `Final-Record.ar2-13` | `ar2-13` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L51]` | copybook | storage: STR | — |
| 73 | `Final-Record.ar2-14` | `ar2-14` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L52]` | copybook | storage: STR | — |
| 74 | `Final-Record.ar2-15` | `ar2-15` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L53]` | copybook | storage: STR | — |
| 75 | `Final-Record.ar2-16` | `ar2-16` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L54]` | copybook | storage: STR | — |
| 76 | `Final-Record.ar2-17` | `ar2-17` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L55]` | copybook | storage: STR | — |
| 77 | `Final-Record.ar2-18` | `ar2-18` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L56]` | copybook | storage: STR | — |
| 78 | `Final-Record.ar2-19` | `ar2-19` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L57]` | copybook | storage: STR | — |
| 79 | `Final-Record.ar2-20` | `ar2-20` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L58]` | copybook | storage: STR | — |
| 80 | `Final-Record.ar2-21` | `ar2-21` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L59]` | copybook | storage: STR | — |
| 81 | `Final-Record.ar2-22` | `ar2-22` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L60]` | copybook | storage: STR | — |
| 82 | `Final-Record.ar2-23` | `ar2-23` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L61]` | copybook | storage: STR | — |
| 83 | `Final-Record.ar2-24` | `ar2-24` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L62]` | copybook | storage: STR | — |
| 84 | `Final-Record.ar2-25` | `ar2-25` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L63]` | copybook | storage: STR | — |
| 85 | `Final-Record.ar2-26` | `ar2-26` · lvl 05 · `x` `[copybooks/irswsfinal.cob:L64]` | copybook | storage: STR | — |
| 86 | `Final-Record.filler#65` | `filler` · lvl 03 · GROUP · redefines `ar2-fields` · group · FILLER `[copybooks/irswsfinal.cob:L65]` | copybook | — | — |
| 87 | `Final-Record.ar3` | `ar3` · lvl 03 · `x(5)` `[copybooks/irswsfinal.cob:L68]` | copybook | storage: STR | — |

#### `copybooks/irswsnl.cob` — 5 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 88 | `NL-Record.NL-Record` | `NL-Record` · lvl 01 · GROUP · group `[copybooks/irswsnl.cob:L8]` | copybook | — | — |
| 89 | `NL-Record.NL-Owning` | `NL-Owning` · lvl 05 · `9(5)` · DISPLAY `[copybooks/irswsnl.cob:L10]` | copybook | storage: INT | — |
| 90 | `NL-Record.NL-Sub-Nominal` | `NL-Sub-Nominal` · lvl 05 · `9(5)` · DISPLAY `[copybooks/irswsnl.cob:L11]` | copybook | storage: INT | — |
| 91 | `NL-Record.NL-Data` | `NL-Data` · lvl 03 · GROUP · group `[copybooks/irswsnl.cob:L15]` | copybook | — | — |
| 92 | `NL-Record.filler` | `filler` · lvl 03 · GROUP · redefines `NL-Data` · group · FILLER `[copybooks/irswsnl.cob:L22]` | copybook | — | — |

#### `copybooks/irswspost.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 93 | `Posting-Record.Posting-Record` | `Posting-Record` · lvl 01 · GROUP · group `[copybooks/irswspost.cob:L8]` | copybook | — | — |

#### `copybooks/wspost-irs.cob` — 3 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 94 | `WS-IRS-Posting-Record.WS-IRS-Posting-Record` | `WS-IRS-Posting-Record` · lvl 01 · GROUP · group `[copybooks/wspost-irs.cob:L13]` | copybook | — | — |
| 95 | `WS-IRS-Posting-Record.WS-IRS-Batch` | `WS-IRS-Batch` · lvl 05 · `9(5)` · DISPLAY `[copybooks/wspost-irs.cob:L15]` | copybook | storage: INT | — |
| 96 | `WS-IRS-Posting-Record.WS-IRS-Post-Number` | `WS-IRS-Post-Number` · lvl 05 · `9(5)` · DISPLAY `[copybooks/wspost-irs.cob:L16]` | copybook | storage: INT | — |

#### `copybooks/plwspinv.cob` — 14 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 97 | `PInvoice-Header.PInvoice-Header` | `PInvoice-Header` · lvl 01 · GROUP · group `[copybooks/plwspinv.cob:L8]` | copybook | — | — |
| 98 | `PInvoice-Header.ih-prime` | `ih-prime` · lvl 03 · GROUP · group `[copybooks/plwspinv.cob:L9]` | copybook | — | — |
| 99 | `PInvoice-Header.ih-Nos` | `ih-Nos` · lvl 07 · `x(6)` `[copybooks/plwspinv.cob:L14]` | copybook | storage: STR | — |
| 100 | `PInvoice-Header.ih-Check` | `ih-Check` · lvl 07 · `9` · DISPLAY `[copybooks/plwspinv.cob:L15]` | copybook | storage: INT | — |
| 101 | `PInvoice-Header.ih-Freq` | `ih-Freq` · lvl 07 · `x` `[copybooks/plwspinv.cob:L18]` | copybook | storage: STR | — |
| 102 | `PInvoice-Header.ih-Repeat` | `ih-Repeat` · lvl 07 · `99` · DISPLAY `[copybooks/plwspinv.cob:L25]` | copybook | storage: INT | — |
| 103 | `PInvoice-Header.filler` | `filler` · lvl 07 · `xxx` · FILLER `[copybooks/plwspinv.cob:L26]` | copybook | storage: STR | — |
| 104 | `PInvoice-Header.ih-Last-Date` | `ih-Last-Date` · lvl 07 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv.cob:L27]` | copybook | storage: INT | — |
| 105 | `PInvoice-Header.ih-sub-prime` | `ih-sub-prime` · lvl 03 · GROUP · group `[copybooks/plwspinv.cob:L30]` | copybook | — | — |
| 106 | `PInvoice-Header.ih-Fig` | `ih-Fig` · lvl 05 · GROUP · group `[copybooks/plwspinv.cob:L31]` | copybook | — | — |
| 107 | `Pinvoice-Bodies.Pinvoice-Bodies` | `Pinvoice-Bodies` · lvl 01 · GROUP · group `[copybooks/plwspinv.cob:L65]` | copybook | — | — |
| 108 | `Pinvoice-Bodies.invoice-line` | `invoice-line` · lvl 03 · GROUP · occurs 40 · group `[copybooks/plwspinv.cob:L66]` | copybook | — | — |
| 109 | `Pinvoice-Bodies.filler#72` | `filler` · lvl 05 · `xx` · FILLER `[copybooks/plwspinv.cob:L72]` | copybook | storage: STR | — |
| 110 | `Pinvoice-Bodies.filler#76` | `filler` · lvl 05 · `xx` · FILLER `[copybooks/plwspinv.cob:L76]` | copybook | storage: STR | — |

#### `copybooks/plwspinv2.cob` — 54 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 111 | `WS-PInvoice-Record.WS-PInvoice-Record` | `WS-PInvoice-Record` · lvl 01 · GROUP · group `[copybooks/plwspinv2.cob:L10]` | copybook | — | — |
| 112 | `WS-PInvoice-Record.Invoice-Key` | `Invoice-Key` · lvl 03 · GROUP · group `[copybooks/plwspinv2.cob:L11]` | copybook | — | — |
| 113 | `WS-PInvoice-Record.Invoice-Nos` | `Invoice-Nos` · lvl 05 · `9(8)` · DISPLAY `[copybooks/plwspinv2.cob:L12]` | copybook | storage: INT | — |
| 114 | `WS-PInvoice-Record.Item-Nos` | `Item-Nos` · lvl 05 · `99` · DISPLAY `[copybooks/plwspinv2.cob:L13]` | copybook | storage: INT | — |
| 115 | `WS-PInvoice-Record.Invoice-Supplier` | `Invoice-Supplier` · lvl 03 · `x(7)` `[copybooks/plwspinv2.cob:L14]` | copybook | storage: STR | — |
| 116 | `WS-PInvoice-Record.Invoice-Date` | `Invoice-Date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L15]` | copybook | storage: INT | — |
| 117 | `WS-PInvoice-Record.Inv-Order` | `Inv-Order` · lvl 03 · `x(10)` `[copybooks/plwspinv2.cob:L16]` | copybook | storage: STR | — |
| 118 | `WS-PInvoice-Record.Invoice-Type` | `Invoice-Type` · lvl 03 · `9` · DISPLAY `[copybooks/plwspinv2.cob:L17]` | copybook | storage: INT | — |
| 119 | `WS-PInvoice-Record.filler#18` | `filler` · lvl 03 · `x(10)` · FILLER `[copybooks/plwspinv2.cob:L18]` | copybook | storage: STR | — |
| 120 | `WS-PInvoice-Record.filler#19` | `filler` · lvl 03 · `x(58)` · FILLER `[copybooks/plwspinv2.cob:L19]` | copybook | storage: STR | — |
| 121 | `Invoice-Header.Invoice-Header#21` | `Invoice-Header` · lvl 01 · GROUP · redefines `WS-PInvoice-Record` · group `[copybooks/plwspinv2.cob:L21]` | copybook | — | — |
| 122 | `Invoice-Header.ih-invoice#22` | `ih-invoice` · lvl 03 · `9(8)` · DISPLAY `[copybooks/plwspinv2.cob:L22]` | copybook | storage: INT | — |
| 123 | `Invoice-Header.ih-test#23` | `ih-test` · lvl 03 · `99` · DISPLAY `[copybooks/plwspinv2.cob:L23]` | copybook | storage: INT | — |
| 124 | `Invoice-Header.ih-supplier` | `ih-supplier` · lvl 03 · GROUP · group `[copybooks/plwspinv2.cob:L24]` | copybook | — | — |
| 125 | `Invoice-Header.ih-nos#25` | `ih-nos` · lvl 05 · `x(6)` `[copybooks/plwspinv2.cob:L25]` | copybook | storage: STR | — |
| 126 | `Invoice-Header.ih-check#26` | `ih-check` · lvl 05 · `9` · DISPLAY `[copybooks/plwspinv2.cob:L26]` | copybook | storage: INT | — |
| 127 | `Invoice-Header.ih-date#27` | `ih-date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L27]` | copybook | storage: INT | — |
| 128 | `Invoice-Header.ih-order#28` | `ih-order` · lvl 03 · `x(10)` `[copybooks/plwspinv2.cob:L28]` | copybook | storage: STR | — |
| 129 | `Invoice-Header.ih-type#29` | `ih-type` · lvl 03 · `9` · DISPLAY `[copybooks/plwspinv2.cob:L29]` | copybook | storage: INT | — |
| 130 | `Invoice-Header.ih-ref#30` | `ih-ref` · lvl 03 · `x(10)` `[copybooks/plwspinv2.cob:L30]` | copybook | storage: STR | — |
| 131 | `Invoice-Header.ih-fig#31` | `ih-fig` · lvl 03 · GROUP · group `[copybooks/plwspinv2.cob:L31]` | copybook | — | — |
| 132 | `Invoice-Header.ih-p-c#32` | `ih-p-c` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L32]` | copybook | storage: DECIMAL | — |
| 133 | `Invoice-Header.ih-net#33` | `ih-net` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L33]` | copybook | storage: DECIMAL | — |
| 134 | `Invoice-Header.ih-extra#34` | `ih-extra` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L34]` | copybook | storage: DECIMAL | — |
| 135 | `Invoice-Header.ih-carriage#35` | `ih-carriage` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L35]` | copybook | storage: DECIMAL | — |
| 136 | `Invoice-Header.ih-vat#36` | `ih-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L36]` | copybook | storage: DECIMAL | — |
| 137 | `Invoice-Header.ih-discount#37` | `ih-discount` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L37]` | copybook | storage: DECIMAL | — |
| 138 | `Invoice-Header.ih-e-vat#38` | `ih-e-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L38]` | copybook | storage: DECIMAL | — |
| 139 | `Invoice-Header.ih-c-vat#39` | `ih-c-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L39]` | copybook | storage: DECIMAL | — |
| 140 | `Invoice-Header.ih-status#40` | `ih-status` · lvl 03 · `x` `[copybooks/plwspinv2.cob:L40]` | copybook | storage: STR | — |
| 141 | `Invoice-Header.ih-lines#44` | `ih-lines` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L44]` | copybook | storage: INT | — |
| 142 | `Invoice-Header.ih-deduct-days#45` | `ih-deduct-days` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L45]` | copybook | storage: INT | — |
| 143 | `Invoice-Header.ih-deduct-amt#46` | `ih-deduct-amt` · lvl 03 · `999v99` · COMP `[copybooks/plwspinv2.cob:L46]` | copybook | storage: DECIMAL | — |
| 144 | `Invoice-Header.ih-deduct-vat#47` | `ih-deduct-vat` · lvl 03 · `999v99` · COMP `[copybooks/plwspinv2.cob:L47]` | copybook | storage: DECIMAL | — |
| 145 | `Invoice-Header.ih-days#48` | `ih-days` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L48]` | copybook | storage: INT | — |
| 146 | `Invoice-Header.ih-cr#49` | `ih-cr` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L49]` | copybook | storage: INT | — |
| 147 | `Invoice-Header.ih-day-book-flag#50` | `ih-day-book-flag` · lvl 03 · `x` `[copybooks/plwspinv2.cob:L50]` | copybook | storage: STR | — |
| 148 | `Invoice-Header.ih-update#52` | `ih-update` · lvl 03 · `x` `[copybooks/plwspinv2.cob:L52]` | copybook | storage: STR | — |
| 149 | `Invoice-Line.Invoice-Line#56` | `Invoice-Line` · lvl 01 · GROUP · redefines `WS-PInvoice-Record` · group `[copybooks/plwspinv2.cob:L56]` | copybook | — | — |
| 150 | `Invoice-Line.il-invoice#57` | `il-invoice` · lvl 03 · `9(8)` · DISPLAY `[copybooks/plwspinv2.cob:L57]` | copybook | storage: INT | — |
| 151 | `Invoice-Line.il-line#58` | `il-line` · lvl 03 · `99` · DISPLAY `[copybooks/plwspinv2.cob:L58]` | copybook | storage: INT | — |
| 152 | `Invoice-Line.il-product#59` | `il-product` · lvl 03 · `x(13)` `[copybooks/plwspinv2.cob:L59]` | copybook | storage: STR | — |
| 153 | `Invoice-Line.il-pa#60` | `il-pa` · lvl 03 · `xx` `[copybooks/plwspinv2.cob:L60]` | copybook | storage: STR | — |
| 154 | `Invoice-Line.filler#61` | `filler` · lvl 03 · `xx` · FILLER `[copybooks/plwspinv2.cob:L61]` | copybook | storage: STR | — |
| 155 | `Invoice-Line.il-qty#62` | `il-qty` · lvl 03 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L62]` | copybook | storage: INT | — |
| 156 | `Invoice-Line.il-type#63` | `il-type` · lvl 03 · `x` `[copybooks/plwspinv2.cob:L63]` | copybook | storage: STR | — |
| 157 | `Invoice-Line.il-description#64` | `il-description` · lvl 03 · `x(24)` `[copybooks/plwspinv2.cob:L64]` | copybook | storage: STR | — |
| 158 | `Invoice-Line.filler#65` | `filler` · lvl 03 · `xx` · FILLER `[copybooks/plwspinv2.cob:L65]` | copybook | storage: STR | — |
| 159 | `Invoice-Line.il-net#66` | `il-net` · lvl 03 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L66]` | copybook | storage: DECIMAL | — |
| 160 | `Invoice-Line.il-unit#67` | `il-unit` · lvl 03 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L67]` | copybook | storage: DECIMAL | — |
| 161 | `Invoice-Line.il-discount#68` | `il-discount` · lvl 03 · `99v99` · COMP `[copybooks/plwspinv2.cob:L68]` | copybook | storage: DECIMAL | — |
| 162 | `Invoice-Line.il-vat#69` | `il-vat` · lvl 03 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/plwspinv2.cob:L69]` | copybook | storage: DECIMAL | — |
| 163 | `Invoice-Line.il-vat-code#70` | `il-vat-code` · lvl 03 · `9` · DISPLAY `[copybooks/plwspinv2.cob:L70]` | copybook | storage: INT | — |
| 164 | `Invoice-Line.il-update#71` | `il-update` · lvl 03 · `x` `[copybooks/plwspinv2.cob:L71]` | copybook | storage: STR | — |

#### `copybooks/plwsoi.cob` — 7 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 165 | `OI-Header.OI-Header#12` | `OI-Header` · lvl 01 · GROUP · group `[copybooks/plwsoi.cob:L12]` | copybook | — | — |
| 166 | `OI-Header.OI-Key` | `OI-Key` · lvl 03 · GROUP · group `[copybooks/plwsoi.cob:L13]` | copybook | — | — |
| 167 | `OI-Header.OI-Customer` | `OI-Customer` · lvl 05 · GROUP · group `[copybooks/plwsoi.cob:L14]` | copybook | — | — |
| 168 | `OI-Header.OI-Nos#16` | `OI-Nos` · lvl 09 · `X(6)` `[copybooks/plwsoi.cob:L16]` | copybook | storage: STR | — |
| 169 | `OI-Header.OI-Check#17` | `OI-Check` · lvl 09 · `9` · DISPLAY `[copybooks/plwsoi.cob:L17]` | copybook | storage: INT | — |
| 170 | `OI-Header.filler#41` | `filler` · lvl 03 · GROUP · group · FILLER `[copybooks/plwsoi.cob:L41]` | copybook | — | — |
| 171 | `OI-Header.OI-Approp#44` | `OI-Approp` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY · redefines `OI-Net` `[copybooks/plwsoi.cob:L44]` | copybook | storage: DECIMAL | — |

#### `copybooks/plwsoi5B.cob` — 6 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 172 | `WS-OTM5-Record.WS-OTM5-Record` | `WS-OTM5-Record` · lvl 01 · `x(113)` `[copybooks/plwsoi5B.cob:L10]` | copybook | storage: STR | — |
| 173 | `Open-Item-Record-5.Open-Item-Record-5` | `Open-Item-Record-5` · lvl 01 · GROUP · redefines `WS-OTM5-Record` · group `[copybooks/plwsoi5B.cob:L12]` | copybook | — | — |
| 174 | `Open-Item-Record-5.oi5-supplier` | `oi5-supplier` · lvl 05 · `x(7)` `[copybooks/plwsoi5B.cob:L14]` | copybook | storage: STR | — |
| 175 | `Open-Item-Record-5.oi5-invoice` | `oi5-invoice` · lvl 05 · `9(8)` · DISPLAY `[copybooks/plwsoi5B.cob:L15]` | copybook | storage: INT | — |
| 176 | `Open-Item-Record-5.oi5-date` | `oi5-date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi5B.cob:L16]` | copybook | storage: INT | — |
| 177 | `Open-Item-Record-5.filler` | `filler` · lvl 03 · `x(94)` · FILLER `[copybooks/plwsoi5B.cob:L17]` | copybook | storage: STR | — |

#### `copybooks/plwsoi5C.cob` — 7 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 178 | `WS-OTM5-Record.WS-OTM5-Record@plwsoi5C` | `WS-OTM5-Record` · lvl 01 · `x(113)` `[copybooks/plwsoi5C.cob:L10]` | copybook | storage: STR | — |
| 179 | `Open-Item-Record-5.Open-Item-Record-5@plwsoi5C` | `Open-Item-Record-5` · lvl 01 · GROUP · redefines `WS-OTM5-Record` · group `[copybooks/plwsoi5C.cob:L12]` | copybook | — | — |
| 180 | `Open-Item-Record-5.oi5-key` | `oi5-key` · lvl 03 · GROUP · group `[copybooks/plwsoi5C.cob:L13]` | copybook | — | — |
| 181 | `Open-Item-Record-5.oi5-supplier@plwsoi5C` | `oi5-supplier` · lvl 05 · `x(7)` `[copybooks/plwsoi5C.cob:L14]` | copybook | storage: STR | — |
| 182 | `Open-Item-Record-5.oi5-invoice@plwsoi5C` | `oi5-invoice` · lvl 05 · `9(8)` · DISPLAY `[copybooks/plwsoi5C.cob:L15]` | copybook | storage: INT | — |
| 183 | `Open-Item-Record-5.oi5-date@plwsoi5C` | `oi5-date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/plwsoi5C.cob:L16]` | copybook | storage: INT | — |
| 184 | `Open-Item-Record-5.filler@plwsoi5C` | `filler` · lvl 03 · `x(94)` · FILLER `[copybooks/plwsoi5C.cob:L17]` | copybook | storage: STR | — |

#### `copybooks/wspl.cob` — 8 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 185 | `WS-Purch-Record.WS-Purch-Record` | `WS-Purch-Record` · lvl 01 · GROUP · group `[copybooks/wspl.cob:L13]` | copybook | — | — |
| 186 | `WS-Purch-Record.Purch-Addr1` | `Purch-Addr1` · lvl 05 · `x(48)` `[copybooks/wspl.cob:L24]` | copybook | storage: STR | — |
| 187 | `WS-Purch-Record.Purch-Addr2` | `Purch-Addr2` · lvl 05 · `x(48)` `[copybooks/wspl.cob:L25]` | copybook | storage: STR | — |
| 188 | `WS-Purch-Record.Quarters` | `Quarters` · lvl 03 · GROUP · group `[copybooks/wspl.cob:L45]` | copybook | — | — |
| 189 | `WS-Purch-Record.filler#50` | `filler` · lvl 03 · GROUP · redefines `Quarters` · group · FILLER `[copybooks/wspl.cob:L50]` | copybook | — | — |
| 190 | `WS-Purch-Record.PTurnover-q` | `PTurnover-q` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY · occurs 4 `[copybooks/wspl.cob:L51]` | copybook | storage: DECIMAL | — |
| 191 | `WS-Purch-Record.Purch-Stats-Date` | `Purch-Stats-Date` · lvl 03 · `9(4)` · DISPLAY `[copybooks/wspl.cob:L53]` | copybook | storage: INT | — |
| 192 | `WS-Purch-Record.filler#54` | `filler` · lvl 03 · `x(12)` · FILLER `[copybooks/wspl.cob:L54]` | copybook | storage: STR | — |

#### `copybooks/slwsinv.cob` — 14 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 193 | `SInvoice-Header.SInvoice-Header` | `SInvoice-Header` · lvl 01 · GROUP · group `[copybooks/slwsinv.cob:L18]` | copybook | — | — |
| 194 | `SInvoice-Header.sih-prime` | `sih-prime` · lvl 02 · GROUP · group `[copybooks/slwsinv.cob:L19]` | copybook | — | — |
| 195 | `SInvoice-Header.sih-nos` | `sih-nos` · lvl 05 · `x(6)` `[copybooks/slwsinv.cob:L24]` | copybook | storage: STR | — |
| 196 | `SInvoice-Header.sih-check` | `sih-check` · lvl 05 · `9` · DISPLAY `[copybooks/slwsinv.cob:L25]` | copybook | storage: INT | — |
| 197 | `SInvoice-Header.filler#28` | `filler` · lvl 03 · GROUP · redefines `sih-order` · group · FILLER `[copybooks/slwsinv.cob:L28]` | copybook | — | — |
| 198 | `SInvoice-Header.sih-Freq` | `sih-Freq` · lvl 05 · `x` `[copybooks/slwsinv.cob:L29]` | copybook | storage: STR | — |
| 199 | `SInvoice-Header.sih-Repeat` | `sih-Repeat` · lvl 05 · `99` · DISPLAY `[copybooks/slwsinv.cob:L36]` | copybook | storage: INT | — |
| 200 | `SInvoice-Header.filler#37` | `filler` · lvl 05 · `xxx` · FILLER `[copybooks/slwsinv.cob:L37]` | copybook | storage: STR | — |
| 201 | `SInvoice-Header.sih-Last-Date` | `sih-Last-Date` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv.cob:L38]` | copybook | storage: INT | — |
| 202 | `SInvoice-Header.Sih-Sub-Prime` | `Sih-Sub-Prime` · lvl 02 · GROUP · group `[copybooks/slwsinv.cob:L41]` | copybook | — | — |
| 203 | `SInvoice-Header.sih-fig` | `sih-fig` · lvl 03 · GROUP · group `[copybooks/slwsinv.cob:L43]` | copybook | — | — |
| 204 | `SInvoice-Bodies.SInvoice-Bodies` | `SInvoice-Bodies` · lvl 01 · GROUP · group `[copybooks/slwsinv.cob:L80]` | copybook | — | — |
| 205 | `SInvoice-Bodies.Invoice-Line` | `Invoice-Line` · lvl 03 · GROUP · occurs 40 · group `[copybooks/slwsinv.cob:L81]` | copybook | — | — |
| 206 | `SInvoice-Bodies.sil-Back-Ordered` | `sil-Back-Ordered` · lvl 05 · `x` `[copybooks/slwsinv.cob:L97]` | copybook | storage: STR | — |

#### `copybooks/slwsinv2.cob` — 66 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 207 | `Invoice-Record.Invoice-Record` | `Invoice-Record` · lvl 01 · GROUP · group `[copybooks/slwsinv2.cob:L27]` | copybook | — | — |
| 208 | `Invoice-Record.Invoice-Key` | `Invoice-Key` · lvl 03 · GROUP · group `[copybooks/slwsinv2.cob:L28]` | copybook | — | — |
| 209 | `Invoice-Record.Invoice-Nos` | `Invoice-Nos` · lvl 05 · `9(8)` · DISPLAY `[copybooks/slwsinv2.cob:L29]` | copybook | storage: INT | — |
| 210 | `Invoice-Record.Item-Nos` | `Item-Nos` · lvl 05 · `99` · DISPLAY `[copybooks/slwsinv2.cob:L30]` | copybook | storage: INT | — |
| 211 | `Invoice-Record.Invoice-Customer` | `Invoice-Customer` · lvl 03 · `x(7)` `[copybooks/slwsinv2.cob:L31]` | copybook | storage: STR | — |
| 212 | `Invoice-Record.Invoice-Date` | `Invoice-Date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L32]` | copybook | storage: INT | — |
| 213 | `Invoice-Record.Filler` | `Filler` · lvl 03 · `x(10)` · FILLER `[copybooks/slwsinv2.cob:L33]` | copybook | storage: STR | — |
| 214 | `Invoice-Record.Invoice-Type` | `Invoice-Type` · lvl 03 · `9` · DISPLAY `[copybooks/slwsinv2.cob:L34]` | copybook | storage: INT | — |
| 215 | `Invoice-Record.filler#35` | `filler` · lvl 03 · `x(10)` · FILLER `[copybooks/slwsinv2.cob:L35]` | copybook | storage: STR | — |
| 216 | `Invoice-Record.filler#36` | `filler` · lvl 03 · `x(95)` · FILLER `[copybooks/slwsinv2.cob:L36]` | copybook | storage: STR | — |
| 217 | `Invoice-Header.Invoice-Header#38` | `Invoice-Header` · lvl 01 · GROUP · redefines `Invoice-Record` · group `[copybooks/slwsinv2.cob:L38]` | copybook | — | — |
| 218 | `Invoice-Header.ih-prime` | `ih-prime` · lvl 02 · GROUP · group `[copybooks/slwsinv2.cob:L39]` | copybook | — | — |
| 219 | `Invoice-Header.ih-invoice#40` | `ih-invoice` · lvl 03 · `9(8)` · DISPLAY `[copybooks/slwsinv2.cob:L40]` | copybook | storage: INT | — |
| 220 | `Invoice-Header.ih-test#41` | `ih-test` · lvl 03 · `99` · DISPLAY `[copybooks/slwsinv2.cob:L41]` | copybook | storage: INT | — |
| 221 | `Invoice-Header.ih-customer` | `ih-customer` · lvl 03 · GROUP · group `[copybooks/slwsinv2.cob:L42]` | copybook | — | — |
| 222 | `Invoice-Header.ih-nos#43` | `ih-nos` · lvl 05 · `x(6)` `[copybooks/slwsinv2.cob:L43]` | copybook | storage: STR | — |
| 223 | `Invoice-Header.ih-check#44` | `ih-check` · lvl 05 · `9` · DISPLAY `[copybooks/slwsinv2.cob:L44]` | copybook | storage: INT | — |
| 224 | `Invoice-Header.ih-date#45` | `ih-date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L45]` | copybook | storage: INT | — |
| 225 | `Invoice-Header.ih-order#46` | `ih-order` · lvl 03 · `x(10)` `[copybooks/slwsinv2.cob:L46]` | copybook | storage: STR | — |
| 226 | `Invoice-Header.filler#47` | `filler` · lvl 03 · GROUP · redefines `ih-order` · group · FILLER `[copybooks/slwsinv2.cob:L47]` | copybook | — | — |
| 227 | `Invoice-Header.ih-Freq` | `ih-Freq` · lvl 05 · `x` `[copybooks/slwsinv2.cob:L48]` | copybook | storage: STR | — |
| 228 | `Invoice-Header.ih-Repeat` | `ih-Repeat` · lvl 05 · `99` · DISPLAY `[copybooks/slwsinv2.cob:L55]` | copybook | storage: INT | — |
| 229 | `Invoice-Header.filler#56` | `filler` · lvl 05 · `xxx` · FILLER `[copybooks/slwsinv2.cob:L56]` | copybook | storage: STR | — |
| 230 | `Invoice-Header.ih-Last-Date` | `ih-Last-Date` · lvl 05 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L57]` | copybook | storage: INT | — |
| 231 | `Invoice-Header.ih-type#58` | `ih-type` · lvl 03 · `9` · DISPLAY `[copybooks/slwsinv2.cob:L58]` | copybook | storage: INT | — |
| 232 | `Invoice-Header.ih-ref#59` | `ih-ref` · lvl 03 · `x(10)` `[copybooks/slwsinv2.cob:L59]` | copybook | storage: STR | — |
| 233 | `Invoice-Header.ih-sub-prime` | `ih-sub-prime` · lvl 02 · GROUP · group `[copybooks/slwsinv2.cob:L60]` | copybook | — | — |
| 234 | `Invoice-Header.ih-description` | `ih-description` · lvl 03 · `x(32)` `[copybooks/slwsinv2.cob:L61]` | copybook | storage: STR | — |
| 235 | `Invoice-Header.ih-fig#62` | `ih-fig` · lvl 03 · GROUP · group `[copybooks/slwsinv2.cob:L62]` | copybook | — | — |
| 236 | `Invoice-Header.ih-p-c#63` | `ih-p-c` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L63]` | copybook | storage: DECIMAL | — |
| 237 | `Invoice-Header.ih-net#64` | `ih-net` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L64]` | copybook | storage: DECIMAL | — |
| 238 | `Invoice-Header.ih-extra#65` | `ih-extra` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L65]` | copybook | storage: DECIMAL | — |
| 239 | `Invoice-Header.ih-carriage#66` | `ih-carriage` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L66]` | copybook | storage: DECIMAL | — |
| 240 | `Invoice-Header.ih-vat#67` | `ih-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L67]` | copybook | storage: DECIMAL | — |
| 241 | `Invoice-Header.ih-discount#68` | `ih-discount` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L68]` | copybook | storage: DECIMAL | — |
| 242 | `Invoice-Header.ih-e-vat#69` | `ih-e-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L69]` | copybook | storage: DECIMAL | — |
| 243 | `Invoice-Header.ih-c-vat#70` | `ih-c-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L70]` | copybook | storage: DECIMAL | — |
| 244 | `Invoice-Header.ih-status#71` | `ih-status` · lvl 03 · `x` `[copybooks/slwsinv2.cob:L71]` | copybook | storage: STR | — |
| 245 | `Invoice-Header.ih-status-P` | `ih-status-P` · lvl 03 · `x` `[copybooks/slwsinv2.cob:L75]` | copybook | storage: STR | — |
| 246 | `Invoice-Header.ih-status-L` | `ih-status-L` · lvl 03 · `x` `[copybooks/slwsinv2.cob:L76]` | copybook | storage: STR | — |
| 247 | `Invoice-Header.ih-status-C` | `ih-status-C` · lvl 03 · `x` `[copybooks/slwsinv2.cob:L77]` | copybook | storage: STR | — |
| 248 | `Invoice-Header.ih-status-A` | `ih-status-A` · lvl 03 · `x` `[copybooks/slwsinv2.cob:L78]` | copybook | storage: STR | — |
| 249 | `Invoice-Header.ih-status-I` | `ih-status-I` · lvl 03 · `x` `[copybooks/slwsinv2.cob:L79]` | copybook | storage: STR | — |
| 250 | `Invoice-Header.ih-lines#80` | `ih-lines` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L80]` | copybook | storage: INT | — |
| 251 | `Invoice-Header.ih-deduct-days#81` | `ih-deduct-days` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L81]` | copybook | storage: INT | — |
| 252 | `Invoice-Header.ih-deduct-amt#82` | `ih-deduct-amt` · lvl 03 · `999v99` · COMP `[copybooks/slwsinv2.cob:L82]` | copybook | storage: DECIMAL | — |
| 253 | `Invoice-Header.ih-deduct-vat#83` | `ih-deduct-vat` · lvl 03 · `999v99` · COMP `[copybooks/slwsinv2.cob:L83]` | copybook | storage: DECIMAL | — |
| 254 | `Invoice-Header.ih-days#84` | `ih-days` · lvl 03 · BINARY-CHAR · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L84]` | copybook | storage: INT | — |
| 255 | `Invoice-Header.ih-cr#85` | `ih-cr` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L85]` | copybook | storage: INT | — |
| 256 | `Invoice-Header.ih-day-book-flag#86` | `ih-day-book-flag` · lvl 03 · `x` `[copybooks/slwsinv2.cob:L86]` | copybook | storage: STR | — |
| 257 | `Invoice-Header.ih-update#88` | `ih-update` · lvl 03 · `x` `[copybooks/slwsinv2.cob:L88]` | copybook | storage: STR | — |
| 258 | `Invoice-Line.Invoice-Line#91` | `Invoice-Line` · lvl 01 · GROUP · redefines `Invoice-Record` · group `[copybooks/slwsinv2.cob:L91]` | copybook | — | — |
| 259 | `Invoice-Line.il-invoice#92` | `il-invoice` · lvl 05 · `9(8)` · DISPLAY `[copybooks/slwsinv2.cob:L92]` | copybook | storage: INT | — |
| 260 | `Invoice-Line.il-line#93` | `il-line` · lvl 05 · `99` · DISPLAY `[copybooks/slwsinv2.cob:L93]` | copybook | storage: INT | — |
| 261 | `Invoice-Line.il-product#94` | `il-product` · lvl 05 · `x(13)` `[copybooks/slwsinv2.cob:L94]` | copybook | storage: STR | — |
| 262 | `Invoice-Line.il-pa#95` | `il-pa` · lvl 05 · `xx` `[copybooks/slwsinv2.cob:L95]` | copybook | storage: STR | — |
| 263 | `Invoice-Line.il-qty#96` | `il-qty` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L96]` | copybook | storage: INT | — |
| 264 | `Invoice-Line.il-type#97` | `il-type` · lvl 05 · `x` `[copybooks/slwsinv2.cob:L97]` | copybook | storage: STR | — |
| 265 | `Invoice-Line.il-description#98` | `il-description` · lvl 05 · `x(32)` `[copybooks/slwsinv2.cob:L98]` | copybook | storage: STR | — |
| 266 | `Invoice-Line.il-net#99` | `il-net` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L99]` | copybook | storage: DECIMAL | — |
| 267 | `Invoice-Line.il-unit#100` | `il-unit` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L100]` | copybook | storage: DECIMAL | — |
| 268 | `Invoice-Line.il-discount#101` | `il-discount` · lvl 05 · `99v99` · COMP `[copybooks/slwsinv2.cob:L101]` | copybook | storage: DECIMAL | — |
| 269 | `Invoice-Line.il-vat#102` | `il-vat` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY `[copybooks/slwsinv2.cob:L102]` | copybook | storage: DECIMAL | — |
| 270 | `Invoice-Line.il-vat-code#103` | `il-vat-code` · lvl 05 · `9` · DISPLAY `[copybooks/slwsinv2.cob:L103]` | copybook | storage: INT | — |
| 271 | `Invoice-Line.il-update#104` | `il-update` · lvl 05 · `x` `[copybooks/slwsinv2.cob:L104]` | copybook | storage: STR | — |
| 272 | `Invoice-Line.il-Back-Ordered` | `il-Back-Ordered` · lvl 05 · `x` `[copybooks/slwsinv2.cob:L106]` | copybook | storage: STR | — |

#### `copybooks/slwsoi.cob` — 7 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 273 | `OI-Header.OI-Header#8` | `OI-Header` · lvl 01 · GROUP · group `[copybooks/slwsoi.cob:L8]` | copybook | — | — |
| 274 | `OI-Header.OI-key` | `OI-key` · lvl 02 · GROUP · group `[copybooks/slwsoi.cob:L9]` | copybook | — | — |
| 275 | `OI-Header.OI-Nos#11` | `OI-Nos` · lvl 05 · `x(6)` `[copybooks/slwsoi.cob:L11]` | copybook | storage: STR | — |
| 276 | `OI-Header.OI-Check#12` | `OI-Check` · lvl 05 · `9` · DISPLAY `[copybooks/slwsoi.cob:L12]` | copybook | storage: INT | — |
| 277 | `OI-Header.filler#14` | `filler` · lvl 02 · GROUP · group · FILLER `[copybooks/slwsoi.cob:L14]` | copybook | — | — |
| 278 | `OI-Header.filler#35` | `filler` · lvl 03 · GROUP · group · FILLER `[copybooks/slwsoi.cob:L35]` | copybook | — | — |
| 279 | `OI-Header.OI-Approp#38` | `OI-Approp` · lvl 05 · `s9(7)v99` · COMP-3 · signed · sign IMPLICIT_BINARY · redefines `OI-Net` `[copybooks/slwsoi.cob:L38]` | copybook | storage: DECIMAL | — |

#### `copybooks/slwsoi3.cob` — 6 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 280 | `WS-OTM3-Record.WS-OTM3-Record` | `WS-OTM3-Record` · lvl 01 · `x(118)` `[copybooks/slwsoi3.cob:L9]` | copybook | storage: STR | — |
| 281 | `Open-Item-Record-3.Open-Item-Record-3` | `Open-Item-Record-3` · lvl 01 · GROUP · redefines `WS-OTM3-Record` · group `[copybooks/slwsoi3.cob:L11]` | copybook | — | — |
| 282 | `Open-Item-Record-3.OI3-Customer` | `OI3-Customer` · lvl 05 · `x(7)` `[copybooks/slwsoi3.cob:L13]` | copybook | storage: STR | — |
| 283 | `Open-Item-Record-3.OI3-Invoice` | `OI3-Invoice` · lvl 05 · `9(8)` · DISPLAY `[copybooks/slwsoi3.cob:L14]` | copybook | storage: INT | — |
| 284 | `Open-Item-Record-3.OI3-Date` | `OI3-Date` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/slwsoi3.cob:L15]` | copybook | storage: INT | — |
| 285 | `Open-Item-Record-3.filler` | `filler` · lvl 03 · `x(99)` · FILLER `[copybooks/slwsoi3.cob:L16]` | copybook | storage: STR | — |

#### `copybooks/wssl.cob` — 8 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 286 | `WS-Sales-Record.WS-Sales-Record` | `WS-Sales-Record` · lvl 01 · GROUP · group `[copybooks/wssl.cob:L12]` | copybook | — | — |
| 287 | `WS-Sales-Record.Sales-Addr1` | `Sales-Addr1` · lvl 05 · `x(48)` `[copybooks/wssl.cob:L19]` | copybook | storage: STR | — |
| 288 | `WS-Sales-Record.Sales-Addr2` | `Sales-Addr2` · lvl 05 · `x(48)` `[copybooks/wssl.cob:L20]` | copybook | storage: STR | — |
| 289 | `WS-Sales-Record.filler#40` | `filler` · lvl 03 · `xxx` · FILLER `[copybooks/wssl.cob:L40]` | copybook | storage: STR | — |
| 290 | `WS-Sales-Record.Quarters` | `Quarters` · lvl 03 · GROUP · group `[copybooks/wssl.cob:L56]` | copybook | — | — |
| 291 | `WS-Sales-Record.filler#61` | `filler` · lvl 03 · GROUP · redefines `Quarters` · group · FILLER `[copybooks/wssl.cob:L61]` | copybook | — | — |
| 292 | `WS-Sales-Record.STurnover-Q` | `STurnover-Q` · lvl 05 · `s9(8)v99` · COMP-3 · signed · sign IMPLICIT_BINARY · occurs 4 `[copybooks/wssl.cob:L62]` | copybook | storage: DECIMAL | — |
| 293 | `WS-Sales-Record.filler#68` | `filler` · lvl 03 · `x(5)` · FILLER `[copybooks/wssl.cob:L68]` | copybook | storage: STR | — |

#### `copybooks/wsdflt.cob` — 3 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 294 | `Default-Record.Default-Record#14` | `Default-Record` · lvl 01 · GROUP · group `[copybooks/wsdflt.cob:L14]` | copybook | — | — |
| 295 | `Default-Record.Def-Group#15` | `Def-Group` · lvl 03 · GROUP · occurs 33 · group `[copybooks/wsdflt.cob:L15]` | copybook | — | — |
| 296 | `Default-Record.filler` | `filler` · lvl 03 · `x(793)` · FILLER `[copybooks/wsdflt.cob:L19]` | copybook | storage: STR | — |

#### `copybooks/wsfinal.cob` — 2 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 297 | `Final-Record.Final-Record#10` | `Final-Record` · lvl 01 · GROUP · group `[copybooks/wsfinal.cob:L10]` | copybook | — | — |
| 298 | `Final-Record.filler#12` | `filler` · lvl 03 · `x(608)` · FILLER `[copybooks/wsfinal.cob:L12]` | copybook | storage: STR | — |

#### `copybooks/wssystem.cob` — 31 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 299 | `System-Record.System-Record` | `System-Record` · lvl 01 · GROUP · group `[copybooks/wssystem.cob:L48]` | copybook | — | — |
| 300 | `System-Record.System-Data-Block` | `System-Data-Block` · lvl 03 · GROUP · group `[copybooks/wssystem.cob:L52]` | copybook | — | — |
| 301 | `System-Record.Vat-Rates` | `Vat-Rates` · lvl 05 · GROUP · group `[copybooks/wssystem.cob:L55]` | copybook | — | — |
| 302 | `System-Record.Vat-Rate` | `Vat-Rate` · lvl 05 · `99v99` · COMP · occurs 5 · redefines `Vat-Rates` `[copybooks/wssystem.cob:L61]` | copybook | storage: DECIMAL | — |
| 303 | `System-Record.Scycle` | `Scycle` · lvl 05 · BINARY-CHAR · signed · sign IMPLICIT_BINARY · redefines `cyclea` `[copybooks/wssystem.cob:L63]` | copybook | storage: INT | — |
| 304 | `System-Record.Usera` | `Usera` · lvl 07 · `x(32)` `[copybooks/wssystem.cob:L71]` | copybook | storage: STR | — |
| 305 | `System-Record.Phone-No` | `Phone-No` · lvl 05 · `x(12)` `[copybooks/wssystem.cob:L80]` | copybook | storage: STR | — |
| 306 | `System-Record.FILLER#81` | `FILLER` · lvl 05 · `x(20)` · FILLER `[copybooks/wssystem.cob:L81]` | copybook | storage: STR | — |
| 307 | `System-Record.Level` | `Level` · lvl 05 · GROUP · group `[copybooks/wssystem.cob:L83]` | copybook | — | — |
| 308 | `System-Record.RDBMS-Flat-Statuses` | `RDBMS-Flat-Statuses` · lvl 05 · GROUP · group `[copybooks/wssystem.cob:L111]` | copybook | — | — |
| 309 | `System-Record.Maps-Ser-xx` | `Maps-Ser-xx` · lvl 07 · `xx` `[copybooks/wssystem.cob:L126]` | copybook | storage: STR | — |
| 310 | `System-Record.Maps-Ser-nn` | `Maps-Ser-nn` · lvl 07 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wssystem.cob:L127]` | copybook | storage: INT | — |
| 311 | `System-Record.General-Ledger-Block` | `General-Ledger-Block` · lvl 03 · GROUP · group `[copybooks/wssystem.cob:L150]` | copybook | — | — |
| 312 | `System-Record.Purchase-Ledger-Block` | `Purchase-Ledger-Block` · lvl 03 · GROUP · group `[copybooks/wssystem.cob:L192]` | copybook | — | — |
| 313 | `System-Record.FILLER#211` | `FILLER` · lvl 05 · `x(7)` · FILLER `[copybooks/wssystem.cob:L211]` | copybook | storage: STR | — |
| 314 | `System-Record.Sales-Ledger-Block` | `Sales-Ledger-Block` · lvl 03 · GROUP · group `[copybooks/wssystem.cob:L215]` | copybook | — | — |
| 315 | `System-Record.FILLER#252` | `FILLER` · lvl 05 · BINARY-SHORT · signed · sign IMPLICIT_BINARY · FILLER `[copybooks/wssystem.cob:L252]` | copybook | storage: INT | — |
| 316 | `System-Record.SL-BO-Default` | `SL-BO-Default` · lvl 05 · `x` `[copybooks/wssystem.cob:L277]` | copybook | storage: STR | — |
| 317 | `System-Record.FILLER#278` | `FILLER` · lvl 05 · `X(14)` · FILLER `[copybooks/wssystem.cob:L278]` | copybook | storage: STR | — |
| 318 | `System-Record.Stock-Control-Block` | `Stock-Control-Block` · lvl 03 · GROUP · group `[copybooks/wssystem.cob:L290]` | copybook | — | — |
| 319 | `System-Record.FILLER#299` | `FILLER` · lvl 05 · `x` · FILLER `[copybooks/wssystem.cob:L299]` | copybook | storage: STR | — |
| 320 | `System-Record.FILLER#308` | `FILLER` · lvl 05 · `x(68)` · FILLER `[copybooks/wssystem.cob:L308]` | copybook | storage: STR | — |
| 321 | `System-Record.IRS-Entry-Block` | `IRS-Entry-Block` · lvl 03 · GROUP · group `[copybooks/wssystem.cob:L309]` | copybook | — | — |
| 322 | `System-Record.Vat-Rates2` | `Vat-Rates2` · lvl 05 · GROUP · group `[copybooks/wssystem.cob:L312]` | copybook | — | — |
| 323 | `System-Record.Vat-Group` | `Vat-Group` · lvl 05 · GROUP · redefines `Vat-Rates2` · group `[copybooks/wssystem.cob:L316]` | copybook | — | — |
| 324 | `System-Record.Vat-Psent` | `Vat-Psent` · lvl 07 · `99v99` · DISPLAY · occurs 3 `[copybooks/wssystem.cob:L317]` | copybook | storage: DECIMAL | — |
| 325 | `System-Record.FILLER#323` | `FILLER` · lvl 05 · GROUP · redefines `PL-Approp-AC6` · group · FILLER `[copybooks/wssystem.cob:L323]` | copybook | — | — |
| 326 | `System-Record.FILLER#324` | `FILLER` · lvl 07 · `9` · DISPLAY · FILLER `[copybooks/wssystem.cob:L324]` | copybook | storage: INT | — |
| 327 | `System-Record.FILLER#327` | `FILLER` · lvl 05 · `x(59)` · FILLER `[copybooks/wssystem.cob:L327]` | copybook | storage: STR | — |
| 328 | `System-Record.IRS-Data-Block` | `IRS-Data-Block` · lvl 03 · GROUP · redefines `IRS-Entry-Block` · group `[copybooks/wssystem.cob:L328]` | copybook | — | — |
| 329 | `System-Record.FILLER-Dummy4` | `FILLER-Dummy4` · lvl 05 · `x(128)` `[copybooks/wssystem.cob:L329]` | copybook | storage: STR | — |

#### `copybooks/wssys4.cob` — 4 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 330 | `System-Record-4.System-Record-4` | `System-Record-4` · lvl 01 · GROUP · group `[copybooks/wssys4.cob:L8]` | copybook | — | — |
| 331 | `System-Record-4.Sales-Ledger-Data` | `Sales-Ledger-Data` · lvl 03 · GROUP · group `[copybooks/wssys4.cob:L9]` | copybook | — | — |
| 332 | `System-Record-4.Purchase-Ledger-Data` | `Purchase-Ledger-Data` · lvl 03 · GROUP · group `[copybooks/wssys4.cob:L20]` | copybook | — | — |
| 333 | `System-Record-4.filler` | `filler` · lvl 03 · `x(904)` · FILLER `[copybooks/wssys4.cob:L31]` | copybook | storage: STR | — |

#### `copybooks/wsval.cob` — 5 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 334 | `WS-Value-Record.WS-Value-Record` | `WS-Value-Record` · lvl 01 · GROUP · group `[copybooks/wsval.cob:L9]` | copybook | — | — |
| 335 | `WS-Value-Record.va-system` | `va-system` · lvl 05 · `x` `[copybooks/wsval.cob:L11]` | copybook | storage: STR | — |
| 336 | `WS-Value-Record.va-group` | `va-group` · lvl 05 · GROUP · group `[copybooks/wsval.cob:L12]` | copybook | — | — |
| 337 | `WS-Value-Record.va-first` | `va-first` · lvl 07 · `x` `[copybooks/wsval.cob:L13]` | copybook | storage: STR | — |
| 338 | `WS-Value-Record.va-second` | `va-second` · lvl 07 · `x` `[copybooks/wsval.cob:L14]` | copybook | storage: STR | — |

#### `copybooks/Test-Data-Flags.cob` — 4 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 339 | `ACAS-DAL-Common-data.ACAS-DAL-Common-data` | `ACAS-DAL-Common-data` · lvl 01 · GROUP · group `[copybooks/Test-Data-Flags.cob:L6]` | copybook | — | — |
| 340 | `ACAS-DAL-Common-data.SW-Testing` | `SW-Testing` · lvl 03 · `9` · DISPLAY `[copybooks/Test-Data-Flags.cob:L10]` | copybook | storage: INT | — |
| 341 | `ACAS-DAL-Common-data.SW-Testing-2` | `SW-Testing-2` · lvl 03 · `9` · DISPLAY `[copybooks/Test-Data-Flags.cob:L15]` | copybook | storage: INT | — |
| 342 | `ACAS-DAL-Common-data.Log-File-Rec-Written` | `Log-File-Rec-Written` · lvl 03 · `9(6)` · DISPLAY `[copybooks/Test-Data-Flags.cob:L18]` | copybook | storage: INT | — |

#### `copybooks/file00.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 343 | `File-Defs.file-0` | `file-0` · lvl 03 · `x(532)` `[copybooks/file00.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file02.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 344 | `File-Defs.file-2` | `file-2` · lvl 03 · `x(532)` `[copybooks/file02.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file03.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 345 | `File-Defs.file-3` | `file-3` · lvl 03 · `x(532)` `[copybooks/file03.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file04.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 346 | `File-Defs.file-4` | `file-4` · lvl 03 · `x(532)` `[copybooks/file04.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file05.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 347 | `File-Defs.file-5` | `file-5` · lvl 03 · `x(532)` `[copybooks/file05.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file06.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 348 | `File-Defs.file-6` | `file-6` · lvl 03 · `x(532)` `[copybooks/file06.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file07.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 349 | `File-Defs.file-7` | `file-7` · lvl 03 · `x(532)` `[copybooks/file07.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file08.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 350 | `File-Defs.file-8` | `file-8` · lvl 03 · `x(532)` `[copybooks/file08.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file09.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 351 | `File-Defs.file-9` | `file-9` · lvl 03 · `x(532)` `[copybooks/file09.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file10.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 352 | `File-Defs.file-10` | `file-10` · lvl 03 · `x(532)` `[copybooks/file10.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file11.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 353 | `File-Defs.file-11` | `file-11` · lvl 03 · `x(532)` `[copybooks/file11.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file12.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 354 | `File-Defs.file-12` | `file-12` · lvl 03 · `x(532)` `[copybooks/file12.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file13.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 355 | `File-Defs.file-13` | `file-13` · lvl 03 · `x(532)` `[copybooks/file13.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file14.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 356 | `File-Defs.file-14` | `file-14` · lvl 03 · `x(532)` `[copybooks/file14.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file15.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 357 | `File-Defs.file-15` | `file-15` · lvl 03 · `x(532)` `[copybooks/file15.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file16.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 358 | `File-Defs.file-16` | `file-16` · lvl 03 · `x(532)` `[copybooks/file16.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file17.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 359 | `File-Defs.file-17` | `file-17` · lvl 03 · `x(532)` `[copybooks/file17.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file18.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 360 | `File-Defs.file-18` | `file-18` · lvl 03 · `x(532)` `[copybooks/file18.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file19.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 361 | `File-Defs.file-19` | `file-19` · lvl 03 · `x(532)` `[copybooks/file19.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file20.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 362 | `File-Defs.file-20` | `file-20` · lvl 03 · `x(532)` `[copybooks/file20.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file21.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 363 | `File-Defs.file-21` | `file-21` · lvl 03 · `x(532)` `[copybooks/file21.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file22.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 364 | `File-Defs.file-22` | `file-22` · lvl 03 · `x(532)` `[copybooks/file22.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file23.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 365 | `File-Defs.file-23` | `file-23` · lvl 03 · `x(532)` `[copybooks/file23.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file24.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 366 | `File-Defs.file-24` | `file-24` · lvl 03 · `x(532)` `[copybooks/file24.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file26.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 367 | `File-Defs.file-26` | `file-26` · lvl 03 · `x(532)` `[copybooks/file26.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file27.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 368 | `File-Defs.file-27` | `file-27` · lvl 03 · `x(532)` `[copybooks/file27.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file28.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 369 | `File-Defs.file-28` | `file-28` · lvl 03 · `x(532)` `[copybooks/file28.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file29.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 370 | `File-Defs.file-29` | `file-29` · lvl 03 · `x(532)` `[copybooks/file29.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file30.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 371 | `File-Defs.file-30` | `file-30` · lvl 03 · `x(532)` `[copybooks/file30.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file31.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 372 | `File-Defs.file-31` | `file-31` · lvl 03 · `x(532)` `[copybooks/file31.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file32.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 373 | `File-Defs.file-32` | `file-32` · lvl 03 · `x(532)` `[copybooks/file32.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/file33.cob` — 1 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 374 | `File-Defs.file-33` | `file-33` · lvl 03 · `x(532)` `[copybooks/file33.cob:L1]` | copybook | storage: STR | — |

#### `copybooks/irswssystem.cob` — 28 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 375 | `system-record.system-record` | `system-record` · lvl 01 · GROUP · group `[copybooks/irswssystem.cob:L13]` | copybook | — | — |
| 376 | `system-record.run-date` | `run-date` · lvl 03 · `x(8)` `[copybooks/irswssystem.cob:L14]` | copybook | storage: STR | — |
| 377 | `system-record.suser` | `suser` · lvl 03 · `x(24)` `[copybooks/irswssystem.cob:L15]` | copybook | storage: STR | — |
| 378 | `system-record.client` | `client` · lvl 03 · `x(24)` `[copybooks/irswssystem.cob:L16]` | copybook | storage: STR | — |
| 379 | `system-record.address-1` | `address-1` · lvl 03 · `x(24)` `[copybooks/irswssystem.cob:L17]` | copybook | storage: STR | — |
| 380 | `system-record.address-2` | `address-2` · lvl 03 · `x(24)` `[copybooks/irswssystem.cob:L18]` | copybook | storage: STR | — |
| 381 | `system-record.address-3` | `address-3` · lvl 03 · `x(24)` `[copybooks/irswssystem.cob:L19]` | copybook | storage: STR | — |
| 382 | `system-record.address-4` | `address-4` · lvl 03 · `x(24)` `[copybooks/irswssystem.cob:L20]` | copybook | storage: STR | — |
| 383 | `system-record.start-date` | `start-date` · lvl 03 · `x(8)` `[copybooks/irswssystem.cob:L21]` | copybook | storage: STR | — |
| 384 | `system-record.end-date` | `end-date` · lvl 03 · `x(8)` `[copybooks/irswssystem.cob:L22]` | copybook | storage: STR | — |
| 385 | `system-record.system-ops` | `system-ops` · lvl 03 · `x` `[copybooks/irswssystem.cob:L23]` | copybook | storage: STR | — |
| 386 | `system-record.pass-word` | `pass-word` · lvl 03 · `x(4)` `[copybooks/irswssystem.cob:L24]` | copybook | storage: STR | — |
| 387 | `system-record.next-post` | `next-post` · lvl 03 · `9(5)` · DISPLAY `[copybooks/irswssystem.cob:L25]` | copybook | storage: INT | — |
| 388 | `system-record.vat-rates` | `vat-rates` · lvl 03 · GROUP · group `[copybooks/irswssystem.cob:L26]` | copybook | — | — |
| 389 | `system-record.vat` | `vat` · lvl 05 · `99v99` · DISPLAY `[copybooks/irswssystem.cob:L27]` | copybook | storage: DECIMAL | — |
| 390 | `system-record.vat2` | `vat2` · lvl 05 · `99v99` · DISPLAY `[copybooks/irswssystem.cob:L28]` | copybook | storage: DECIMAL | — |
| 391 | `system-record.vat3` | `vat3` · lvl 05 · `99v99` · DISPLAY `[copybooks/irswssystem.cob:L29]` | copybook | storage: DECIMAL | — |
| 392 | `system-record.vat-group` | `vat-group` · lvl 03 · GROUP · redefines `vat-rates` · group `[copybooks/irswssystem.cob:L30]` | copybook | — | — |
| 393 | `system-record.vat-psent` | `vat-psent` · lvl 05 · `99v99` · DISPLAY · occurs 3 `[copybooks/irswssystem.cob:L31]` | copybook | storage: DECIMAL | — |
| 394 | `system-record.pass-value` | `pass-value` · lvl 03 · `9` · DISPLAY `[copybooks/irswssystem.cob:L32]` | copybook | storage: INT | — |
| 395 | `system-record.save-sequ` | `save-sequ` · lvl 03 · `9` · DISPLAY `[copybooks/irswssystem.cob:L33]` | copybook | storage: INT | — |
| 396 | `system-record.system-work-group` | `system-work-group` · lvl 03 · `x(18)` `[copybooks/irswssystem.cob:L34]` | copybook | storage: STR | — |
| 397 | `system-record.PL-App-Created` | `PL-App-Created` · lvl 03 · `x` `[copybooks/irswssystem.cob:L35]` | copybook | storage: STR | — |
| 398 | `system-record.PL-Approp-AC` | `PL-Approp-AC` · lvl 03 · `9(5)` · DISPLAY `[copybooks/irswssystem.cob:L36]` | copybook | storage: INT | — |
| 399 | `system-record.Print-Spool-Name` | `Print-Spool-Name` · lvl 03 · `x(32)` `[copybooks/irswssystem.cob:L37]` | copybook | storage: STR | — |
| 400 | `system-record.First-Time-FLag` | `First-Time-FLag` · lvl 03 · `9` · DISPLAY `[copybooks/irswssystem.cob:L38]` | copybook | storage: INT | — |
| 401 | `system-record.filler#39` | `filler` · lvl 03 · `9(7)` · DISPLAY · FILLER `[copybooks/irswssystem.cob:L39]` | copybook | storage: INT | — |
| 402 | `system-record.filler#40` | `filler` · lvl 03 · `x` · FILLER `[copybooks/irswssystem.cob:L40]` | copybook | storage: STR | — |

#### `copybooks/wscall.cob` — 8 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 403 | `WS-Calling-Data.WS-Calling-Data` | `WS-Calling-Data` · lvl 01 · GROUP · group `[copybooks/wscall.cob:L6]` | copybook | — | — |
| 404 | `WS-Calling-Data.WS-Called` | `WS-Called` · lvl 03 · `x(8)` `[copybooks/wscall.cob:L7]` | copybook | storage: STR | — |
| 405 | `WS-Calling-Data.WS-Caller` | `WS-Caller` · lvl 03 · `x(8)` `[copybooks/wscall.cob:L8]` | copybook | storage: STR | — |
| 406 | `WS-Calling-Data.WS-Del-Link` | `WS-Del-Link` · lvl 03 · `x(8)` `[copybooks/wscall.cob:L9]` | copybook | storage: STR | — |
| 407 | `WS-Calling-Data.WS-Term-Code` | `WS-Term-Code` · lvl 03 · `99` · DISPLAY `[copybooks/wscall.cob:L10]` | copybook | storage: INT | — |
| 408 | `WS-Calling-Data.WS-Process-Func` | `WS-Process-Func` · lvl 03 · `9` · DISPLAY `[copybooks/wscall.cob:L12]` | copybook | storage: INT | — |
| 409 | `WS-Calling-Data.WS-Sub-Function` | `WS-Sub-Function` · lvl 03 · `9` · DISPLAY `[copybooks/wscall.cob:L13]` | copybook | storage: INT | — |
| 410 | `WS-Calling-Data.WS-CD-Args` | `WS-CD-Args` · lvl 03 · `x(13)` `[copybooks/wscall.cob:L14]` | copybook | storage: STR | — |

#### `copybooks/wsfnctn.cob` — 41 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 411 | `File-Access.File-Access` | `File-Access` · lvl 01 · GROUP · group `[copybooks/wsfnctn.cob:L22]` | copybook | — | — |
| 412 | `File-Access.We-Error` | `We-Error` · lvl 03 · `999` · DISPLAY `[copybooks/wsfnctn.cob:L23]` | copybook | storage: INT | — |
| 413 | `File-Access.Rrn` | `Rrn` · lvl 03 · `9(5)` · COMP `[copybooks/wsfnctn.cob:L24]` | copybook | storage: INT | — |
| 414 | `File-Access.Fs-Reply` | `Fs-Reply` · lvl 03 · `99` · DISPLAY `[copybooks/wsfnctn.cob:L25]` | copybook | storage: INT | — |
| 415 | `File-Access.s1` | `s1` · lvl 03 · `x` `[copybooks/wsfnctn.cob:L26]` | copybook | storage: STR | — |
| 416 | `File-Access.Curs` | `Curs` · lvl 03 · `9(4)` · DISPLAY `[copybooks/wsfnctn.cob:L27]` | copybook | storage: INT | — |
| 417 | `File-Access.filler#28` | `filler` · lvl 03 · GROUP · redefines `Curs` · group · FILLER `[copybooks/wsfnctn.cob:L28]` | copybook | — | — |
| 418 | `File-Access.Lin` | `Lin` · lvl 05 · `99` · DISPLAY `[copybooks/wsfnctn.cob:L29]` | copybook | storage: INT | — |
| 419 | `File-Access.Cole` | `Cole` · lvl 05 · `99` · DISPLAY `[copybooks/wsfnctn.cob:L30]` | copybook | storage: INT | — |
| 420 | `File-Access.Curs2` | `Curs2` · lvl 03 · `9(4)` · DISPLAY `[copybooks/wsfnctn.cob:L31]` | copybook | storage: INT | — |
| 421 | `File-Access.filler#32` | `filler` · lvl 03 · GROUP · redefines `Curs2` · group · FILLER `[copybooks/wsfnctn.cob:L32]` | copybook | — | — |
| 422 | `File-Access.Lin2` | `Lin2` · lvl 05 · `99` · DISPLAY `[copybooks/wsfnctn.cob:L33]` | copybook | storage: INT | — |
| 423 | `File-Access.Col2` | `Col2` · lvl 05 · `99` · DISPLAY `[copybooks/wsfnctn.cob:L34]` | copybook | storage: INT | — |
| 424 | `File-Access.ACAS-Path` | `ACAS-Path` · lvl 03 · `x(525)` `[copybooks/wsfnctn.cob:L38]` | copybook | storage: STR | — |
| 425 | `File-Access.Path-Work` | `Path-Work` · lvl 03 · `x(525)` `[copybooks/wsfnctn.cob:L39]` | copybook | storage: STR | — |
| 426 | `File-Access.FS-Action` | `FS-Action` · lvl 03 · `x(22)` `[copybooks/wsfnctn.cob:L41]` | copybook | storage: STR | — |
| 427 | `File-Access.Logging-Data` | `Logging-Data` · lvl 03 · GROUP · group `[copybooks/wsfnctn.cob:L44]` | copybook | — | — |
| 428 | `File-Access.Accept-Reply` | `Accept-Reply` · lvl 05 · `x` `[copybooks/wsfnctn.cob:L45]` | copybook | storage: STR | — |
| 429 | `File-Access.File-Key-No` | `File-Key-No` · lvl 05 · `9` · DISPLAY `[copybooks/wsfnctn.cob:L46]` | copybook | storage: INT | — |
| 430 | `File-Access.ws-Log-System` | `ws-Log-System` · lvl 05 · `9` · DISPLAY `[copybooks/wsfnctn.cob:L47]` | copybook | storage: INT | — |
| 431 | `File-Access.ws-No-Paragraph` | `ws-No-Paragraph` · lvl 05 · `999` · DISPLAY `[copybooks/wsfnctn.cob:L48]` | copybook | storage: INT | — |
| 432 | `File-Access.SQL-Err` | `SQL-Err` · lvl 05 · `x(5)` `[copybooks/wsfnctn.cob:L49]` | copybook | storage: STR | — |
| 433 | `File-Access.SQL-Msg` | `SQL-Msg` · lvl 05 · `x(512)` `[copybooks/wsfnctn.cob:L50]` | copybook | storage: STR | — |
| 434 | `File-Access.SQL-State` | `SQL-State` · lvl 05 · `x(5)` `[copybooks/wsfnctn.cob:L51]` | copybook | storage: STR | — |
| 435 | `File-Access.WS-File-Key` | `WS-File-Key` · lvl 05 · `x(64)` `[copybooks/wsfnctn.cob:L52]` | copybook | storage: STR | — |
| 436 | `File-Access.WS-Log-Where` | `WS-Log-Where` · lvl 05 · `x(231)` `[copybooks/wsfnctn.cob:L53]` | copybook | storage: STR | — |
| 437 | `File-Access.WS-Log-File-No` | `WS-Log-File-No` · lvl 05 · `99` · DISPLAY `[copybooks/wsfnctn.cob:L54]` | copybook | storage: INT | — |
| 438 | `File-Access.WS-Count-Rows` | `WS-Count-Rows` · lvl 05 · `9(7)` · DISPLAY `[copybooks/wsfnctn.cob:L55]` | copybook | storage: INT | — |
| 439 | `File-Access.RDB-Data` | `RDB-Data` · lvl 03 · GROUP · group `[copybooks/wsfnctn.cob:L56]` | copybook | — | — |
| 440 | `File-Access.DB-Schema` | `DB-Schema` · lvl 05 · `x(12)` `[copybooks/wsfnctn.cob:L57]` | copybook | storage: STR | — |
| 441 | `File-Access.DB-UName` | `DB-UName` · lvl 05 · `x(12)` `[copybooks/wsfnctn.cob:L58]` | copybook | storage: STR | — |
| 442 | `File-Access.DB-UPass` | `DB-UPass` · lvl 05 · `x(12)` `[copybooks/wsfnctn.cob:L59]` | copybook | storage: STR | — |
| 443 | `File-Access.DB-Host` | `DB-Host` · lvl 05 · `x(32)` `[copybooks/wsfnctn.cob:L60]` | copybook | storage: STR | — |
| 444 | `File-Access.DB-Socket` | `DB-Socket` · lvl 05 · `x(64)` `[copybooks/wsfnctn.cob:L61]` | copybook | storage: STR | — |
| 445 | `File-Access.DB-Port` | `DB-Port` · lvl 05 · `x(5)` `[copybooks/wsfnctn.cob:L62]` | copybook | storage: STR | — |
| 446 | `File-Access.Main-Record-Move-Flag` | `Main-Record-Move-Flag` · lvl 03 · `9` · DISPLAY `[copybooks/wsfnctn.cob:L66]` | copybook | storage: INT | — |
| 447 | `File-Access.FA-RDBMS-Flat-Statuses` | `FA-RDBMS-Flat-Statuses` · lvl 03 · GROUP · group `[copybooks/wsfnctn.cob:L72]` | copybook | — | — |
| 448 | `File-Access.FA-File-System-Used` | `FA-File-System-Used` · lvl 07 · `9` · DISPLAY `[copybooks/wsfnctn.cob:L73]` | copybook | storage: INT | — |
| 449 | `File-Access.FA-File-Duplicates-In-Use` | `FA-File-Duplicates-In-Use` · lvl 07 · `9` · DISPLAY `[copybooks/wsfnctn.cob:L82]` | copybook | storage: INT | — |
| 450 | `File-Access.File-Function` | `File-Function` · lvl 03 · `99` · DISPLAY `[copybooks/wsfnctn.cob:L88]` | copybook | storage: INT | — |
| 451 | `File-Access.Access-Type` | `Access-Type` · lvl 03 · `9` · DISPLAY `[copybooks/wsfnctn.cob:L107]` | copybook | storage: INT | — |

#### `copybooks/wsmaps03.cob` — 25 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 452 | `maps03-ws.maps03-ws` | `maps03-ws` · lvl 01 · GROUP · group `[copybooks/wsmaps03.cob:L6]` | copybook | — | — |
| 453 | `maps03-ws.u-date` | `u-date` · lvl 03 · `x(10)` `[copybooks/wsmaps03.cob:L7]` | copybook | storage: STR | — |
| 454 | `maps03-ws.u-UK` | `u-UK` · lvl 03 · GROUP · redefines `u-date` · group `[copybooks/wsmaps03.cob:L8]` | copybook | — | — |
| 455 | `maps03-ws.u-days` | `u-days` · lvl 05 · `99` · DISPLAY `[copybooks/wsmaps03.cob:L9]` | copybook | storage: INT | — |
| 456 | `maps03-ws.filler#10` | `filler` · lvl 05 · `x` · FILLER `[copybooks/wsmaps03.cob:L10]` | copybook | storage: STR | — |
| 457 | `maps03-ws.u-month` | `u-month` · lvl 05 · `99` · DISPLAY `[copybooks/wsmaps03.cob:L11]` | copybook | storage: INT | — |
| 458 | `maps03-ws.filler#12` | `filler` · lvl 05 · `x` · FILLER `[copybooks/wsmaps03.cob:L12]` | copybook | storage: STR | — |
| 459 | `maps03-ws.u-year` | `u-year` · lvl 05 · GROUP · group `[copybooks/wsmaps03.cob:L13]` | copybook | — | — |
| 460 | `maps03-ws.u-cc` | `u-cc` · lvl 07 · `99` · DISPLAY `[copybooks/wsmaps03.cob:L14]` | copybook | storage: INT | — |
| 461 | `maps03-ws.u-yy` | `u-yy` · lvl 07 · `99` · DISPLAY `[copybooks/wsmaps03.cob:L15]` | copybook | storage: INT | — |
| 462 | `maps03-ws.u-USA` | `u-USA` · lvl 03 · GROUP · redefines `u-date` · group `[copybooks/wsmaps03.cob:L16]` | copybook | — | — |
| 463 | `maps03-ws.u-usa-month` | `u-usa-month` · lvl 05 · `99` · DISPLAY `[copybooks/wsmaps03.cob:L17]` | copybook | storage: INT | — |
| 464 | `maps03-ws.filler#18` | `filler` · lvl 05 · `x` · FILLER `[copybooks/wsmaps03.cob:L18]` | copybook | storage: STR | — |
| 465 | `maps03-ws.u-usa-days` | `u-usa-days` · lvl 05 · `99` · DISPLAY `[copybooks/wsmaps03.cob:L19]` | copybook | storage: INT | — |
| 466 | `maps03-ws.filler#20` | `filler` · lvl 05 · `x` · FILLER `[copybooks/wsmaps03.cob:L20]` | copybook | storage: STR | — |
| 467 | `maps03-ws.filler#21` | `filler` · lvl 05 · `x(4)` · FILLER `[copybooks/wsmaps03.cob:L21]` | copybook | storage: STR | — |
| 468 | `maps03-ws.u-Intl` | `u-Intl` · lvl 03 · GROUP · redefines `u-date` · group `[copybooks/wsmaps03.cob:L22]` | copybook | — | — |
| 469 | `maps03-ws.u-intl-year` | `u-intl-year` · lvl 05 · GROUP · group `[copybooks/wsmaps03.cob:L23]` | copybook | — | — |
| 470 | `maps03-ws.u-intl-cc` | `u-intl-cc` · lvl 07 · `99` · DISPLAY `[copybooks/wsmaps03.cob:L24]` | copybook | storage: INT | — |
| 471 | `maps03-ws.u-intl-yy` | `u-intl-yy` · lvl 07 · `99` · DISPLAY `[copybooks/wsmaps03.cob:L25]` | copybook | storage: INT | — |
| 472 | `maps03-ws.filler#26` | `filler` · lvl 05 · `x` · FILLER `[copybooks/wsmaps03.cob:L26]` | copybook | storage: STR | — |
| 473 | `maps03-ws.u-intl-month` | `u-intl-month` · lvl 05 · `99` · DISPLAY `[copybooks/wsmaps03.cob:L27]` | copybook | storage: INT | — |
| 474 | `maps03-ws.filler#28` | `filler` · lvl 05 · `x` · FILLER `[copybooks/wsmaps03.cob:L28]` | copybook | storage: STR | — |
| 475 | `maps03-ws.u-intl-days` | `u-intl-days` · lvl 05 · `99` · DISPLAY `[copybooks/wsmaps03.cob:L29]` | copybook | storage: INT | — |
| 476 | `maps03-ws.u-bin` | `u-bin` · lvl 03 · BINARY-LONG · signed · sign IMPLICIT_BINARY `[copybooks/wsmaps03.cob:L30]` | copybook | storage: INT | — |

#### `copybooks/wsnames.cob` — 32 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 477 | `File-Defs.File-Defs` | `File-Defs` · lvl 01 · GROUP · group `[copybooks/wsnames.cob:L13]` | copybook | — | — |
| 478 | `File-Defs.file-defs-a` | `file-defs-a` · lvl 02 · GROUP · group `[copybooks/wsnames.cob:L14]` | copybook | — | — |
| 479 | `File-Defs.pre-trans-name` | `pre-trans-name` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L15]` | copybook | storage: STR | — |
| 480 | `File-Defs.post-trans-name` | `post-trans-name` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L16]` | copybook | storage: STR | — |
| 481 | `File-Defs.file-34` | `file-34` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L51]` | copybook | storage: STR | — |
| 482 | `File-Defs.file-35` | `file-35` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L52]` | copybook | storage: STR | — |
| 483 | `File-Defs.file-36` | `file-36` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L53]` | copybook | storage: STR | — |
| 484 | `File-Defs.file-37` | `file-37` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L54]` | copybook | storage: STR | — |
| 485 | `File-Defs.file-38` | `file-38` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L55]` | copybook | storage: STR | — |
| 486 | `File-Defs.file-39` | `file-39` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L58]` | copybook | storage: STR | — |
| 487 | `File-Defs.file-40` | `file-40` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L59]` | copybook | storage: STR | — |
| 488 | `File-Defs.file-41` | `file-41` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L60]` | copybook | storage: STR | — |
| 489 | `File-Defs.file-42` | `file-42` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L61]` | copybook | storage: STR | — |
| 490 | `File-Defs.file-43` | `file-43` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L62]` | copybook | storage: STR | — |
| 491 | `File-Defs.file-44` | `file-44` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L63]` | copybook | storage: STR | — |
| 492 | `File-Defs.file-45` | `file-45` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L64]` | copybook | storage: STR | — |
| 493 | `File-Defs.file-46` | `file-46` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L65]` | copybook | storage: STR | — |
| 494 | `File-Defs.file-47` | `file-47` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L66]` | copybook | storage: STR | — |
| 495 | `File-Defs.file-48` | `file-48` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L67]` | copybook | storage: STR | — |
| 496 | `File-Defs.file-49` | `file-49` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L69]` | copybook | storage: STR | — |
| 497 | `File-Defs.file-50` | `file-50` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L70]` | copybook | storage: STR | — |
| 498 | `File-Defs.file-51` | `file-51` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L71]` | copybook | storage: STR | — |
| 499 | `File-Defs.file-52` | `file-52` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L72]` | copybook | storage: STR | — |
| 500 | `File-Defs.file-53` | `file-53` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L73]` | copybook | storage: STR | — |
| 501 | `File-Defs.file-54` | `file-54` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L74]` | copybook | storage: STR | — |
| 502 | `File-Defs.file-55` | `file-55` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L75]` | copybook | storage: STR | — |
| 503 | `File-Defs.file-56` | `file-56` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L76]` | copybook | storage: STR | — |
| 504 | `File-Defs.file-57` | `file-57` · lvl 03 · `x(532)` `[copybooks/wsnames.cob:L78]` | copybook | storage: STR | — |
| 505 | `File-Defs.filler` | `filler` · lvl 02 · GROUP · redefines `file-defs-a` · group · FILLER `[copybooks/wsnames.cob:L80]` | copybook | — | — |
| 506 | `File-Defs.System-File-Names` | `System-File-Names` · lvl 03 · `x(532)` · occurs 58 `[copybooks/wsnames.cob:L81]` | copybook | storage: STR | — |
| 507 | `File-Defs.File-Defs-Count` | `File-Defs-Count` · lvl 02 · BINARY-SHORT · signed · sign IMPLICIT_BINARY `[copybooks/wsnames.cob:L82]` | copybook | storage: INT | — |
| 508 | `File-Defs.File-Defs-os-Delimiter` | `File-Defs-os-Delimiter` · lvl 02 · `x` `[copybooks/wsnames.cob:L83]` | copybook | storage: STR | — |

#### `general/gl070.cbl` — 9 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 509 | `pre-trans-record.pre-trans-record#108` | `pre-trans-record` · lvl 01 · GROUP · group `[general/gl070.cbl:L108]` | program_source | — | — |
| 510 | `pre-trans-record.pre-batch#109` | `pre-batch` · lvl 03 · `9(5)` · DISPLAY `[general/gl070.cbl:L109]` | program_source | storage: INT | — |
| 511 | `pre-trans-record.pre-post#110` | `pre-post` · lvl 03 · `9(5)` · DISPLAY `[general/gl070.cbl:L110]` | program_source | storage: INT | — |
| 512 | `pre-trans-record.pre-code#111` | `pre-code` · lvl 03 · `xx` `[general/gl070.cbl:L111]` | program_source | storage: STR | — |
| 513 | `pre-trans-record.pre-date#112` | `pre-date` · lvl 03 · `x(8)` `[general/gl070.cbl:L112]` | program_source | storage: STR | — |
| 514 | `pre-trans-record.pre-ac#113` | `pre-ac` · lvl 03 · `9(6)` · DISPLAY `[general/gl070.cbl:L113]` | program_source | storage: INT | — |
| 515 | `pre-trans-record.pre-pc#114` | `pre-pc` · lvl 03 · `99` · DISPLAY `[general/gl070.cbl:L114]` | program_source | storage: INT | — |
| 516 | `pre-trans-record.pre-amount#115` | `pre-amount` · lvl 03 · `s9(8)v99` · DISPLAY · signed · sign TRAILING_INCLUDED `[general/gl070.cbl:L115]` | program_source | storage: DECIMAL | — |
| 517 | `pre-trans-record.pre-legend#116` | `pre-legend` · lvl 03 · `x(32)` `[general/gl070.cbl:L116]` | program_source | storage: STR | — |

#### `general/gl071.cbl` — 27 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 518 | `pre-trans-record.pre-trans-record#112` | `pre-trans-record` · lvl 01 · GROUP · group `[general/gl071.cbl:L112]` | program_source | — | — |
| 519 | `pre-trans-record.pre-batch#113` | `pre-batch` · lvl 03 · `9(5)` · DISPLAY `[general/gl071.cbl:L113]` | program_source | storage: INT | — |
| 520 | `pre-trans-record.pre-post#114` | `pre-post` · lvl 03 · `9(5)` · DISPLAY `[general/gl071.cbl:L114]` | program_source | storage: INT | — |
| 521 | `pre-trans-record.pre-code#115` | `pre-code` · lvl 03 · `xx` `[general/gl071.cbl:L115]` | program_source | storage: STR | — |
| 522 | `pre-trans-record.pre-date#116` | `pre-date` · lvl 03 · `x(8)` `[general/gl071.cbl:L116]` | program_source | storage: STR | — |
| 523 | `pre-trans-record.pre-ac#117` | `pre-ac` · lvl 03 · `9(6)` · DISPLAY `[general/gl071.cbl:L117]` | program_source | storage: INT | — |
| 524 | `pre-trans-record.pre-pc#118` | `pre-pc` · lvl 03 · `99` · DISPLAY `[general/gl071.cbl:L118]` | program_source | storage: INT | — |
| 525 | `pre-trans-record.pre-amount#119` | `pre-amount` · lvl 03 · `s9(8)v99` · DISPLAY · signed · sign TRAILING_INCLUDED `[general/gl071.cbl:L119]` | program_source | storage: DECIMAL | — |
| 526 | `pre-trans-record.pre-legend#120` | `pre-legend` · lvl 03 · `x(32)` `[general/gl071.cbl:L120]` | program_source | storage: STR | — |
| 527 | `post-trans-record.post-trans-record#124` | `post-trans-record` · lvl 01 · GROUP · group `[general/gl071.cbl:L124]` | program_source | — | `A-14` |
| 528 | `post-trans-record.post-batch#125` | `post-batch` · lvl 03 · `9(5)` · DISPLAY `[general/gl071.cbl:L125]` | program_source | storage: INT | `A-14` |
| 529 | `post-trans-record.post-post#126` | `post-post` · lvl 03 · `9(5)` · DISPLAY `[general/gl071.cbl:L126]` | program_source | storage: INT | `A-14` |
| 530 | `post-trans-record.post-code#127` | `post-code` · lvl 03 · `xx` `[general/gl071.cbl:L127]` | program_source | storage: STR | `A-14` |
| 531 | `post-trans-record.post-date#128` | `post-date` · lvl 03 · `x(8)` `[general/gl071.cbl:L128]` | program_source | storage: STR | `A-14` |
| 532 | `post-trans-record.post-ac#129` | `post-ac` · lvl 03 · `9(6)` · DISPLAY `[general/gl071.cbl:L129]` | program_source | storage: INT | `A-14` |
| 533 | `post-trans-record.post-pc#130` | `post-pc` · lvl 03 · `99` · DISPLAY `[general/gl071.cbl:L130]` | program_source | storage: INT | `A-14` |
| 534 | `post-trans-record.post-amount#131` | `post-amount` · lvl 03 · `s9(8)v99` · DISPLAY · signed · sign TRAILING_INCLUDED `[general/gl071.cbl:L131]` | program_source | storage: DECIMAL | `A-14` |
| 535 | `post-trans-record.post-legend#132` | `post-legend` · lvl 03 · `x(32)` `[general/gl071.cbl:L132]` | program_source | storage: STR | `A-14` |
| 536 | `sort-trans-record.sort-trans-record` | `sort-trans-record` · lvl 01 · GROUP · group `[general/gl071.cbl:L136]` | program_source | — | `A-14` |
| 537 | `sort-trans-record.sort-batch` | `sort-batch` · lvl 03 · `9(5)` · DISPLAY `[general/gl071.cbl:L137]` | program_source | storage: INT | `A-14` |
| 538 | `sort-trans-record.sort-post` | `sort-post` · lvl 03 · `9(5)` · DISPLAY `[general/gl071.cbl:L138]` | program_source | storage: INT | `A-14` |
| 539 | `sort-trans-record.sort-code` | `sort-code` · lvl 03 · `xx` `[general/gl071.cbl:L139]` | program_source | storage: STR | `A-14` |
| 540 | `sort-trans-record.sort-date` | `sort-date` · lvl 03 · `x(8)` `[general/gl071.cbl:L140]` | program_source | storage: STR | `A-14` |
| 541 | `sort-trans-record.sort-ac` | `sort-ac` · lvl 03 · `9(6)` · DISPLAY `[general/gl071.cbl:L141]` | program_source | storage: INT | `A-14` |
| 542 | `sort-trans-record.sort-pc` | `sort-pc` · lvl 03 · `99` · DISPLAY `[general/gl071.cbl:L142]` | program_source | storage: INT | `A-14` |
| 543 | `sort-trans-record.sort-amount` | `sort-amount` · lvl 03 · `s9(8)v99` · DISPLAY · signed · sign TRAILING_INCLUDED `[general/gl071.cbl:L143]` | program_source | storage: DECIMAL | `A-14` |
| 544 | `sort-trans-record.sort-legend` | `sort-legend` · lvl 03 · `x(32)` `[general/gl071.cbl:L144]` | program_source | storage: STR | `A-14` |

#### `general/gl072.cbl` — 10 entries

| # | Dictionary key | Field | Presence | Drift · derivation · storage | A- / Q- |
| ---: | --- | --- | --- | --- | --- |
| 545 | `post-trans-record.post-trans-record#110` | `post-trans-record` · lvl 01 · GROUP · group `[general/gl072.cbl:L110]` | program_source | — | `A-14` |
| 546 | `post-trans-record.post-batch#111` | `post-batch` · lvl 03 · `9(5)` · DISPLAY `[general/gl072.cbl:L111]` | program_source | storage: INT | `A-14` |
| 547 | `post-trans-record.post-post#112` | `post-post` · lvl 03 · `9(5)` · DISPLAY `[general/gl072.cbl:L112]` | program_source | storage: INT | `A-14` |
| 548 | `post-trans-record.post-code#113` | `post-code` · lvl 03 · `xx` `[general/gl072.cbl:L113]` | program_source | storage: STR | `A-14` |
| 549 | `post-trans-record.post-date#114` | `post-date` · lvl 03 · `x(8)` `[general/gl072.cbl:L114]` | program_source | storage: STR | `A-14` |
| 550 | `post-trans-record.post-ledger` | `post-ledger` · lvl 03 · GROUP · group `[general/gl072.cbl:L115]` | program_source | — | `A-14` |
| 551 | `post-trans-record.post-ac#116` | `post-ac` · lvl 05 · `9(6)` · DISPLAY `[general/gl072.cbl:L116]` | program_source | storage: INT | `A-14` |
| 552 | `post-trans-record.post-pc#117` | `post-pc` · lvl 05 · `99` · DISPLAY `[general/gl072.cbl:L117]` | program_source | storage: INT | `A-14` |
| 553 | `post-trans-record.post-amount#118` | `post-amount` · lvl 03 · `s9(8)v99` · DISPLAY · signed · sign TRAILING_INCLUDED `[general/gl072.cbl:L118]` | program_source | storage: DECIMAL | `A-14` |
| 554 | `post-trans-record.post-legend#119` | `post-legend` · lvl 03 · `x(32)` `[general/gl072.cbl:L119]` | program_source | storage: STR | `A-14` |
