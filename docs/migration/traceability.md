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

**There is no user rules document for this project.** The `review_rules` facility was called twice
while this document was written, the second time as a full-document read with an explicit range, and
both calls returned exactly:

```text
No user rules provided.
```

Do not go looking for a rules file. There is none. Stated plainly, as the absence requires: this
project has no rules document, and **enterprise-standard best practice therefore applies wherever
the Agent Action Plan is silent**. Nothing has been invented to fill the gap, and the absence is not
treated as permission to lower the bar.

The six binding rules of this engagement — **R-1 … R-6** — nevertheless exist. They live in the
**Agent Action Plan itself, §0.7.2**, as a labelled rules block inside the user's requirements, and
their exact wording is retrievable via **`review_prompt`**, *not* via `review_rules`. Quoting AAP
§0.7.1: *"downstream execution agents that need the exact wording must read it there."*

Both facts are recorded rather than one of them quietly dropped, because AAP §0.7.4 **C-5** requires
it. Its resolution, quoted verbatim:

> *"claiming a rules document exists when it does not would send downstream agents to an empty source. Recording both facts is the only resolution that misleads no one."*

---

## 2. The rules that govern this document

### 2.1 R-5 — Full traceability ★ primary owner of this document

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
`harness`."* Three proofs of that were verified in this checkout rather than assumed:

- `harness/` contains **no `__init__.py`**, so it is not an importable package.
- A search of `harness/*.py` for `import acas_posting` or `from acas_posting` returns **zero** hits,
  so the harness does not reach into the package either.
- `pyproject.toml` declares packaging as an explicit **allow-list** of eight entries — the seven
  code packages of `acas_posting` plus `acas_posting.data_dictionary` as a data directory — with
  `include-package-data = false`. `harness` is excluded by construction, not by pattern.

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

⚠️ **The Agent Action Plan contains numerous citation errors, and this document uses verified values
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
| `general/gl051.cbl` | 1282 | `acas_posting/programs/gl051_batch_control_check.py` | **PARTIAL** — the control-total gate only: `batch-print` §999, spanning `[general/gl051.cbl:L999-L1166]`, of which `end-batch` L1096-L1134 is the gate; plus `net.` L788, `gross.` L793 and `get-description.` L799, whose two `ROUNDED` VAT computes (L791, L796) and destructive `subtract` (L797) the gate consumes |
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
verified by listing the directory. Every one of the twelve exposes precisely one public symbol,
`run`, and its positional parameters preserve the COBOL `PROCEDURE DIVISION USING` order exactly;
§14 gives the three shapes.

### 7.1 The two partial boundaries are narrow, and both files are dominated by out-of-scope code

Quoting AAP §0.8.7: *"an agent working from the file rather than from the stated boundary would
migrate several hundred lines that must not be migrated."* The boundaries are therefore stated as
line spans, not as prose.

**`gl051` — 1282 lines, of which 172 are in scope.** Out of scope, and named here so the boundary is
unmistakable: `gl051-Main` §359, `proof-all` §474, `gl050c` §496, `batch-amendment` §825 and
`gl050d` §961. The in-scope span is `batch-print` §999 through L1166 plus the three paragraphs at
L788, L793 and L799 that sit *inside* the out-of-scope `gl050c` section but are reached by the gate.

⭐ **`gl051` has no command-line entry point.** It is the one in-scope program that no menu
paragraph dispatches as part of a posting run — the General menu's posting routes are `load08.` and
`load09.` `[general/general.cbl:L805-L815]`, `[general/general.cbl:L817-L821]`, and neither names
`gl051`. Its module is consequently a library function, exercised at the arithmetic tier by the
control-total parity test named in AAP §0.4.1.7, and §7.2 of `anomaly-log.md` records the same
boundary from the anomaly side.

**`irs030` — 1733 lines, of which 187 are in scope.** Out of scope: `Init-Main` §557,
`Input-Headings` §1239, `Date-Validate` §1285, `Initialise-Main` §1402, `Show-Default` §1504 and
`file-init` §1518.

⭐ Two distinct facts about `irs030`'s tail must both be recorded, because conflating them produces a
citation that does not resolve:

- The **section** ends at **L1730** — `main99-exit.` at L1729, `exit     section.` at L1730.
- The **file** is exactly **1733** lines, and L1732 is `copy "Proc-ZZ100-ACAS-IRS-Calls.cob".`

⭐ A third fact makes the boundary sharper still: `Input-Loop` is declared **twice** in `irs030` — at
`[irs/irs030.cbl:L797]` inside the out-of-scope `Init-Main`, and at `[irs/irs030.cbl:L1619]` inside
the in-scope `Ledger-Postings-Add`. COBOL resolves an unqualified paragraph reference within the
containing section first, so the four `go to Input-Loop` statements at L1634, L1652, L1683 and L1700
all target **L1619**. The Python function is `_input_loop`, private to
`acas_posting/programs/irs030_posting.py`, and the out-of-scope twin has no counterpart at all.

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
| **2** forward terminator | targets a label that ends the iteration and then continues with post-loop work — `end-run`, `end-report`, `main-end`, `end-loop`, `input-end`, `pack-end`, `loop1-end`, `loop2-end`, `headings-end`, `loop-end`, `da040-close-files`, `EOJ` | `break` **plus** faithful placement of the post-loop block | ⚠️ The transformation is `break` **and the work**, never `break` alone. AAP §0.6.3: *"Mis-splitting here would silently drop end-of-run processing."* §9.4 walks the strongest instance in full |
| **3** section or paragraph exit | targets the trailing exit label — `main-exit`, `main-ex`, `main99-exit`, `menu-exit`, `csp-exit`, `zz050-exit`, `zz060-Exit`, `zz070-Exit`, `db999-main-exit`, `dc999-main-exit`, `dd999-main-ex`, `Main-Exit` | `return` | Unconditionally safe: a forward transfer to a section's trailing exit label cannot skip code that would otherwise run |
| **4** sibling re-dispatch | targets a peer paragraph that performs work and then itself transfers control — `da030-skip-invoice`, `next-1`, `file-error`, `ba000-Main-Rewrite`, `main-rewrite`, `Get-Default`, `Open-Error-Continued`, `header-analysis`, `Create-Anal`, `Chk-Ans` | a named call followed by an **explicit** `continue` or `return` | ⚠️ **The only class requiring per-site proof.** Which control statement follows the call depends on where the target's *own* transfer goes, so each site is argued individually |

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
| `net.` | `L788` | consumed by `_end_batch` via `acas_posting/cobol/arithmetic.py`; the `ROUNDED` compute is at L791 | — |
| `gross.` | `L793` | as above; `ROUNDED` compute L796, destructive `subtract` L797 | — |
| `get-description.` | `L799` | the `gl050c` twin, distinct from the L1136 paragraph | — |

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

⭐ `gl070` has **four distinct `loop.` labels** — L305, L344, L450 and L483 — and **twelve**
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

⭐ **`gl071` contributes two rows, and that is the point.** It declares **no sections at all**, two
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

⚠️ One property of that `SORT` is **not** settled by reading it: `[general/gl071.cbl:L172-L178]`
declares no `with duplicates in order` phrase, so the compiled tie order for two records carrying an
identical `(sort-batch, sort-ac, sort-pc, sort-post)` is whatever GnuCOBOL 3.2 chooses. The Python
sort is stable unconditionally, which may or may not agree. Under R-6 that is a question for the
oracle, and it is carried as **`Q-SORT-TIE-ORDER`** in `ambiguity-resolutions.md` rather than settled
here.

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

⭐ **`headings-end.` at L369 is an empty label** — there is no statement between it and `end-batch.`
at L372. It exists solely as the terminus of `perform headings through headings-end` (§9.5). The
Python module keeps `_headings_end` as a real function anyway, because C-4 fixes the function boundary
at the paragraph boundary; deleting it would make the `through` transformation unverifiable.

⭐ **`end-account` is performed before `end-batch`, while being declared after it.** The at-end phrase
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

⭐ The section at L590 is **`dc000-Store-Specials`**, not merely the exit label the plan's inventory
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

⭐ **`main-exit.` is declared six times in `sl060`** — L763, L789, L813, L829, L845 and L973 — not the
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

⭐ `[sales/sl100.cbl:L516-L517]` is `csp-exit.` followed by a **bare `exit.`**, not `exit section.`
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

⭐ `Net` and `Gross` end with a **bare `exit.`** at L1554 and L1567, not `exit section.`, even though
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

⭐ Two of those rows are **mutually re-dispatching pairs** — `Create-Main` ⇄ `Create-Anal` in `pl055`
and `DB000-Create-Main` ⇄ `db010-Create-Anal` in `sl055` — where each paragraph can transfer to the
other. Mutual recursion is *not* a faithful rendering, because COBOL's transfer does not stack a
return address. The sibling modules keep the two as separate functions, `_create__create_main` /
`_create__create_anal` and `_db000_create_main` / `_db010_create_anal`, and drive the alternation from
the enclosing section function, so no frame accumulates. Where the *number of alternations* a given
input produces cannot be settled by reading, it is a question for the oracle rather than for this
document, and is cross-referenced as a `Q-` entry in `ambiguity-resolutions.md` (§18) rather than
asserted here.

### 9.5 `PERFORM … THROUGH` and `PERFORM … THRU` — individually hand-verified

⚠️ **The construct appears in two spellings, and a search for `THRU` alone misses `gl072` entirely.**
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

Accordingly, this section does **not** reproduce several hundred field rows in Markdown. Doing so
would be transcription by eye — precisely the failure the directive forbids — and the table would
diverge from the code the first time a locator changed. Instead, the field-to-entry mapping *is* the
generated artifact, and this section is its specification and its index: what an entry contains, how
many there are, what the three source layers are, and how to resolve a field to its entry.

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
`pyproject.toml` therefore ships the dictionary as package data, because a wheel without it cannot
import `acas_posting.records` at all.

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
in this checkout: of the 1061 entries, the 1001 that declare a `copybook` layer, the 513 that declare
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
is **unchanged** and that it holds **1061 entries covering 513 columns, 513 host variables, 1001
copybook fields and 46 program-source work-file fields across 22 tables and 20 bridges**. The
artifact's own `coverage` block carries the same figures, and each was reproduced here by parsing the
frozen sources independently:

| Quantity | Value | How it decomposes |
| --- | --- | --- |
| Tables in `mysql/ACASDB.sql` | **33** | **22 in scope + 11 out of scope** |
| Bridges in `common/` | **28** | **20 in scope + 8 out of scope** |
| Columns of the 22 in-scope tables | **513** | see the per-table list in §10.4 |
| Host variables covered | **513** | one per in-scope column |
| Copybook fields covered | **1001** | includes groups, redefines and filler, which have no column |
| Program-source work-file fields | **46** | the `pre-trans` / `post-trans` records, declared in `gl070` and `gl071` rather than in a copybook |
| Entries | **1061** | 513 column-anchored plus the one-sided entries of §10.7 |

`mysql/ACASDB.sql` is **1459** lines. It contains **33** `CREATE TABLE` statements and **33**
`DROP TABLE IF EXISTS` statements — so re-applying the file *is* the drop-and-recreate — together with
**zero** `CREATE DATABASE`, **zero** `USE` (the database name must therefore be supplied on the client
command line) and **zero** `INSERT INTO`. The 22 in-scope tables carry 513 columns, **all** of them
`NOT NULL`, **all 22** with a single-column primary key, and **zero** secondary indexes anywhere.
There are **zero `TIMESTAMP`** columns.

### 10.4 The frozen schema, stated as it is

⚠️ Three claims about this file are commonly repeated in a form that is wrong. Each is corrected here
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

⭐ **Primary-key names are not globally unique**, so a dictionary keyed on the column name alone would
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

⭐ **The decimal scale is not uniformly 2**, so a normaliser that assumed two places would corrupt the
comparison. Whole-file census: 68 × `decimal(9,2)`, 57 × `(10,2)`, 17 × `(4,2)`, 12 × `(5,2)`,
4 × `(14,2)`, 2 × `(2,0)`, 2 × `(14,4)`, and five singletons — `(5,0)`, `(6,2)`, `(10,4)`, `(11,2)`
and `(11,4)`. Restricted to the in-scope 22 the shape narrows usefully: 55 × `(10,2)`, 44 × `(9,2)`,
15 × `(4,2)`, 8 × `(5,2)`, 4 × `(14,2)`, 1 × `(5,0)`, 1 × `(6,2)` — **two distinct scales only, 0 and
2**, and eleven distinct precisions.

### 10.5 ⭐ The proof that the bridge is authoritative

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

⭐ **The three derived columns sit at ordinals 4, 5 and 6 — interleaved, not appended.** A reader who
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
  out of the source — it depends on the conversion the bridge's C interface performs — so the entry
  carries an `ambiguity_refs` cross-reference to **`Q-3`** rather than a guess, and A-11's status in
  [`anomaly-log.md`](anomaly-log.md) is `PENDING` for the same reason.
  `acas_posting/dal/acas012_sales.py` asserts at L357-L370 that all **eleven** columns it narrows
  carry both `A-11` and `Q-3` in the dictionary, raising at import time if any does not — so the open
  question cannot be lost by omission.
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

**The census.** Counted over all 187 files of `copybooks/` with the method stated so it is
reproducible: a regex per clause, applied twice — once to every line, and once to each line with any
`*>` comment tail removed. The all-lines figure includes the maintainer's inline annotations (many
`binary-long` declarations carry a `*> 9(8) comp.` note, which is why the two columns differ).

| Clause | All lines | Code only |
| --- | --- | --- |
| `comp-3` | 182 | 177 |
| `comp` (bare) | 214 | 144 |
| `binary-long` | 166 | 128 |
| `binary-char` | 84 | 59 |
| `binary-short` | 31 | 30 |
| `occurs` | 107 | 99 |
| `redefines` | 60 | 53 |
| `sign leading` | 4 | 4 |
| `sign is leading` | 2 | 2 |

And **zero** occurrences, in code or in comment, of every clause that would introduce a seventh
class: `comp-1`, `comp-2`, `comp-5`, `binary-double`, `sign trailing`, `sign separate`, `justified`,
blank-when-zero, `PIC A`, and `P` scaling. Zero code-line trailing `V` as well.

⭐ **One clause, two spellings, six fields, three files.** `sign leading` appears at
`[copybooks/fdpost-irs.cob:L20]`, `[copybooks/fdpost-irs.cob:L24]`, `[copybooks/wspost-irs.cob:L21]`
and `[copybooks/wspost-irs.cob:L25]`; `sign is leading` appears at `[copybooks/irswspost.cob:L14]`
and `[copybooks/irswspost.cob:L18]`. A parser matching only one spelling would silently treat two
signed fields of the internal IRS posting record as unsigned. `acas_posting/cobol/usage.py` handles
both, and `acas_posting/cobol/picture.py` parses the clause into the `SignPosition` the dictionary
records.

⚠️ The **width in bytes** of a leading-sign `DISPLAY` item is a second open question, carried as
**`Q-5.2`**. Two readings exist: the maintainer's own byte accounting at
`[copybooks/wspost.cob:L6-L7]` — 98 bytes, then 96 "(leading sign removed)" across two fields, so one
byte each — implies digits + 1; the ISO overpunch reading implies digits. Under R-6 the compiled
program decides, so the descriptor records which reading is in force and the question stays open.

### 10.7 What is deliberately **not** a column-anchored entry

1001 copybook fields are covered but only 513 columns exist, so roughly half of the copybook surface
has no column. Those fields are still entries — the artifact marks them `one_sided: true` — and the
reasons are recorded rather than left as an unexplained gap:

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
- **⚠️ An unqualified leaf named `Batch`.** `[copybooks/wspost.cob:L15]` declares
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
| `keyOfReference occurs 1 indexed by KOR-x1` | `L237` | ⭐ **`occurs 1`** — one key of reference, independently corroborating the schema's single-column primary key |
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

Three of the twelve programs declare a block of one-byte stubs whose only purpose is to satisfy the
linker: the facade copybook references every entity's record, so a program that uses only some of
them must still declare the rest. Quoting AAP §0.4.3: *"Python has no equivalent need, so the block
maps to nothing."*

| Program | Block | Span | Live stubs | Commented out — i.e. actually in use |
| --- | --- | --- | --- | --- |
| `gl072` | `01  Dummies-4-Unused-ACAS-FH-Calls.` `[general/gl072.cbl:L135]`, annotated `*> Call blk at zz080-ACAS-Calls` | L135-L155 | 17 | **three**: `Default-Record` L136, `WS-Ledger-Record` L139, `WS-Batch-Record` L141 |
| `gl080` | `01  Dummies-4-Unused-ACAS-FH-Calls.` `[general/gl080.cbl:L194]`, same annotation | L194-L214 | 16 | **four**: `Default-Record` L195, `WS-Ledger-Record` L198, `WS-Posting-Record` L199, `WS-Batch-Record` L200 |
| `irs030` | `01  Dummies-For-Unused-FH-Calls.` `[irs/irs030.cbl:L291]`, annotated `*> IRS call blk at zz100-ACAS-IRS-Calls` | L291-L296 | **one** | **four**: `WS-IRSNL-Record` L292, `WS-IRS-Default-Record` L293, `Posting-Record` L294, `WS-IRS-Posting-Record` L295 |

⭐ The commented-out entries are the informative ones: a stub is commented out **because the record is
in use**, which the maintainer instructs at `[general/gl072.cbl:L133]` and `[general/gl080.cbl:L192]`
with `*> REMARK OUT ANY IN USE`. Read that way the blocks are a handler manifest per program, and they
agree with the facade verbs each program actually performs. `Proc-ZZ100-ACAS-IRS-Calls.cob` points at
its own block in its header at `[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L5-L6]`.

### 11.4 The preserved naming inconsistency in the date wrapper

`[general/gl070.cbl:L603]` declares the section `maps03` — named after the *interface copybook* — while
`[general/gl070.cbl:L608]` names its exit label `maps04-exit`, after the *called program*. The same
pairing recurs at `[general/gl051.cbl:L1273]` and `[general/gl051.cbl:L1278]`. Both are preserved as
evidence rather than smoothed away; cross-reference **A-22**.

⭐ The inconsistency is **General-ledger-only**, which is what makes it an accident rather than a
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

⚠️ **The one prompt that is *not* dropped** is the one that gates a database write. `EOJ-q1.` at
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

## 12. ⭐ The dual-alias facade: a **behavioural** difference, not merely naming

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

### 12.3 ⭐⭐ The `IR914` gap proves `acasirsub4` has no error check, and it is triple-sourced

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

## 13. ⚠️ The data-access layer: 17 files, 20 pairs, 22 modules

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

⭐ **`acas000` is a five-way dispatcher, not a four-way one.** `[common/acas000.cbl:L574]` opens
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

⭐ **The four IRS entities have no entity-convention name at all.** They are reachable only through
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

### 14.2 Sales and Purchase — ⚠️ **five** parameters, not four

`using ws-calling-data / system-record / system-record-4 / to-day / file-defs`

| Program | Locator |
| --- | --- |
| `sl055` | `[sales/sl055.cbl:L271-L275]` |
| `sl060` | `[sales/sl060.cbl:L395-L399]` |
| `sl100` | `[sales/sl100.cbl:L272-L276]` |
| `pl055` | `[purchase/pl055.cbl:L239-L243]` |
| `pl060` | `[purchase/pl060.cbl:L340-L344]` |
| `pl100` | `[purchase/pl100.cbl:L265-L269]` |

⚠️ **AAP citation error (§6, C-05):** §0.4.1.1 calls this *"the four-parameter SL/PL linkage shape"*. It
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

⭐ The shape is an **IRS-wide idiom**, not a peculiarity of `irs030`: `irs010`
`[irs/irs010.cbl:L435-L437]`, `irs020` `[irs/irs020.cbl:L599-L601]` and `irs040`
`[irs/irs040.cbl:L290-L292]` all take the identical three parameters. The menu itself is the
exception — `[irs/irs.cbl:L470]` is `procedure division.` with **no** `USING`, because `irs.cbl` is a
**main** program rather than a called one.

⭐ **"No run date" never meant "no clock".** Parameter 2 still carries `Run-Date binary-long` at
`[copybooks/wssystem.cob:L67]`, so the IRS route pins one date observable rather than two.
`acas_posting/clock.py` publishes `PinnedRunDate`, `pin_from_calendar_date`, `pin_from_to_day`,
`pin_from_run_date` and `verify_pin`, which covers both cases from a single injected value. The one
clock read in the whole call chain is in the menu shell's date-service copybook, and it produces
exactly the two observables: `move function current-date to wse-date-block.`
`[copybooks/Proc-ACAS-Mapser-RDB.cob:L72]`, then `move u-date to to-day.`
`[copybooks/Proc-ACAS-Mapser-RDB.cob:L77]` and `move u-bin to run-date.`
`[copybooks/Proc-ACAS-Mapser-RDB.cob:L80]`, with the pre-zeroing of §9.7 in between at L78.

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

⭐ `WS-Term-Code` is **`pic 99`**, not `pic 9` — the maintainer's own change note at
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

⚠️ **AAP citation error (§6, C-06): Sales invoice posting is `load07.`, not `load08.`** Three
independent confirmations: the maintainer's own inline comment on the label —
`[sales/sales.cbl:L756]` reads `load07.             *> Sales trans posting`; the menu letter —
`"(G)  Sales Transactions Post"` at `[sales/sales.cbl:L545]` is the **seventh** option, with `(A)` at
L539; and what `load08.` actually does — `[sales/sales.cbl:L770-L774]` dispatches `sl080`, Payment
Input, which AAP §0.2.2 places out of scope. For contrast, Purchase's `load08` **is** correct, because
`"(H)  Purchase Transactions Post"` at `[purchase/purchase.cbl:L540]` is the eighth option with `(A)`
at L533.

⚠️ **AAP citation errors (§6, C-07 and C-08)** for the two General routes: the plan cites both
`L806-L816` and `L800-L814` for the post-cycle, and `L711-L723` for the `gl080` dispatch. The verified
spans are **L805-L815** and **L817-L821**; `L711` is `load00.`, the shared four-parameter call
paragraph.

`acas_posting/cli/` holds **ten** files: `__init__.py`, the seven route modules above, `args.py`, and
`rdbms_params.py`. The last is **not** in the AAP's target tree of §0.3.1;
`acas_posting/__main__.py` records at L407-L411 that `args.py` and `rdbms_params.py` are deliberately
libraries the routes use rather than routes themselves. It is noted here rather than passed over, so
that a reader diffing the tree against the plan finds the discrepancy already accounted for.

---

## 15. ⚠️ The three abort gates diverge — recorded, never harmonised (R-4)

The four menus gate the phases of a posting run differently, and one of them does not gate at all. R-4
forbids reconciling them.

### 15.1 The four routes, side by side

| Sub system | Locator | Predicate | Gates | Effect |
| --- | --- | --- | --- | --- |
| **General** | `[general/general.cbl:L805-L815]` | `ws-term-code = 5` at **L810-L811** | **one**, after `gl070` only | Quoting AAP §0.6.4: *"The effect is that `gl071` and `gl072` never run at all."* |
| **Sales** | `[sales/sales.cbl:L756-L768]` | `ws-term-code not = zero` | **two** — L761-L762 after `sl830`, L765-L766 after `sl055` | a different predicate, and one more gate |
| **Purchase** | `[purchase/purchase.cbl:L752-L762]` | — | ⚠️⚠️ **none** | see §15.3 |
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

### 15.3 ⚠️⚠️ Purchase has no abort gate, because the lines are commented out

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

⭐ **Three further Purchase-against-Sales divergences appear within those few lines**, and all three
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
**L1712**. ⚠️ **Two live closes, not three:** `perform acasirsub1-Close.` at L1710 is commented out,
its comment recording that the file is closed at end of job elsewhere. Dropping the post-loop block
would silently lose all of this, which is why §9.1's Class 2 is `break` **plus** the work.

⭐ **Three abort paths bypass `EOJ` entirely**, because `main99-exit.` at L1729 sits *after* `EOJ-q1.`
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

⚠️ **AAP citation error (§6, C-29):** the plan says it is tested at "three sites in each of the four
Sales and Purchase posting programs". The verified counts are **seven, seven, seven and six** —
**27** sites:

| Program | Sites |
| --- | --- |
| `sl060` | L1039, L1046, L1126, L1144, L1172, L1175, L1177 |
| `sl100` | L578, L585, L647, L665, L690, L693, L695 |
| `pl060` | L907, L914, L982, L999, L1027, L1030, L1032 |
| `pl100` | L566, L629, L646, L671, L674, L676 |

`sl055` and `pl055` test it nowhere.

⭐ **`pl100` tests a weaker predicate than its Sales twin at the corresponding site.**
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
| every field maps to a data-dictionary entry | §10 | **Yes** — 1061 entries over 513 columns, 513 host variables, 1001 copybook fields and 46 work-file fields, generated rather than transcribed, with §10.7 accounting for the one-sided remainder |
| the mapping is recorded as a document | this file | **Yes** |

### 17.2 Companion and test paths verified after QA remediation

The point-in-time absences recorded during initial authoring have been
superseded. Each item below was read in the completed checkout:

| Item | Status in this checkout |
| --- | --- |
| `tests/arithmetic/` | **present — fifteen test files**, including shared-storage and dispatch-boundary coverage |
| `tests/scenarios/` | **present — eight committed scenario tests** |
| `tests/determinism/test_two_runs_byte_identical.py` | **present** |
| `harness/scenarios/` | **present — all eight YAML definitions**, including `period_end_totals.yaml` |
| `docs/migration/ambiguity-resolutions.md` | **present** |
| `docs/migration/scenario-diff-evidence.md` | **present** |
| `README-python-migration.md` | **present at repository root** |

Everything else this document cites was read in this checkout: the twelve programs, the four menus, the
handlers and bridges named, the copybooks named, `mysql/ACASDB.sql`, the thirteen files of
`acas_posting/programs/`, the twenty-two of `acas_posting/dal/`, the ten of `acas_posting/cli/`, the
eight of `acas_posting/cobol/`, the twenty-eight of `acas_posting/records/`, the four of
`acas_posting/dictionary/`, both `data_dictionary/*.json`, `acas_posting/clock.py`,
`acas_posting/dates.py`, `acas_posting/workfiles.py`, `acas_posting/__main__.py`, `pyproject.toml`, and
[`anomaly-log.md`](anomaly-log.md).

### 17.3 What this document does **not** claim

- **This document is not the runtime evidence register.** The strict oracle
  build and all eight empty scenario diffs are recorded in
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
