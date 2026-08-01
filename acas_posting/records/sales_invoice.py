"""Sales Invoice record layouts: the header, its lines, and the second view set.

One module, two frozen copybooks, three MySQL-facing shapes. This file mirrors
`copybooks/slwsinv.cob` and `copybooks/slwsinv2.cob` field for field and adds
nothing. It declares nineteen plain dataclasses and no behaviour: no arithmetic,
no SQL, no I/O, no predicate over a condition name. The Sales extract step
`sl055` and the Sales posting step `sl060` read and mutate these layouts; what
they do with them lives in `acas_posting/programs/`, not here.

WHY TWO COPYBOOKS PAIR INTO ONE MODULE - THE LOAD-BEARING FACT
==============================================================
The Agent Action Plan's transformation row for this file, section 0.4.1.3, names
both copybooks as its source and summarises the change as "Header and lines,
matching the two-table split". That pairing is structural rather than editorial,
and the reason is visible only when all four naming layers are set side by side:

    layer                     role          header        lines
    ------------------------  ------------  ------------  ------------
    copybooks/slwsinv.cob     the layout    sih-  [L21]   sil-  [L83]
    copybooks/slwsinv2.cob    2nd view set  ih-   [L40]   il-   [L92]
    bridge working storage    post-REPLACE  WS-Sih- [457]  WS-Sil- [362]
    bridge host variables     the columns   HV-IH-  [392]  HV1-IL- [428]

Line numbers are in each row's own copybook for the first two rows and in
`common/slinvoiceMT.cbl` for the last two. The host-variable prefixes shed
their `HV`/`HV1` on the way to the column names, becoming `IH-` and `IL-`.

The bridge copies `slwsinv.cob` and never `slwsinv2.cob`. Matching `copy "`
case-insensitively over `common/slinvoiceMT.cbl` returns six statements -
`envdiv.cob` L255, `wsfnctn.cob` L447, `Test-Data-Flags.cob` L451 and
`slwsinv.cob` L456, plus the two the preSQL translator emits in upper case,
`mysql-variables.cpy` L385 and `mysql-procedures.cpy` L1420. `slwsinv2.cob` is
not among them. Yet every column is spelt with `slwsinv2.cob`'s `ih-` / `il-`
prefix, so one copybook supplies the bytes and the other supplies the names, and
a reader who consults only the first cannot explain a single column name.

The practical consequence governs every line below: the entry for `sih-net`
[copybooks/slwsinv.cob:L45] is keyed `SAINVOICE-REC.IH-NET`, never
`SAINVOICE-REC.SIH-NET`, so upper-casing a field name to build a key produces a
key that does not exist. Every key here was obtained by reading the generated
dictionary and matching each entry's `copybook.name` to its field, never by
transforming a name, and the keys are written out so a reviewer can check each
one against the artifact.

THE ENTITY THIS RECORD BELONGS TO
=================================
    entity facade  Invoice
    handler        acas016              common/acas016.cbl
    bridge         slinvoiceMT          common/slinvoiceMT.cbl
    tables         SAINVOICE-REC        31 columns, PK SINVOICE-KEY char(10)
                   SAINV-LINES-REC      14 columns, PK IL-LINE-KEY char(10)

Invoice is one of only two in-scope entities owning two tables - the other is
PInvoice through `acas026` and `plinvoiceMT` - which is part of why Agent Action
Plan section 0.3.1 mirrors the handler boundary rather than the table boundary
in the data-access layer. Both tables are `NOT NULL` throughout with a
single-column primary key and no secondary index, which is what makes the
scenario state dump a plain ordered `SELECT`.

THE BRIDGE IS A TRANSFORMATION, NOT A PIPE - ITS OWN WORDS
==========================================================
Two declarations in the bridge settle it, and both are quoted verbatim because
paraphrase loses the force. First the four-part REPLACING clause
[common/slinvoiceMT.cbl:L456-L459]:

    copy "slwsinv.cob"   replacing SInvoice-Header   by WS-Invoice-Record
                                   leading ==sih-==  by ==WS-Sih-==
                                   ==occurs 40.==    by ==.==
                                   ==sil-==          by ==Un-Used-Sil-==.

preceded by the maintainer's explanation [common/slinvoiceMT.cbl:L452-L454]:

    "Using the first record but not the 2nd as it uses occurs 40 but
     to reduce Ram usage get rid of the occurs."

Four transformations in one clause: the `01` name is renamed, every header field
gains a prefix, `occurs 40.` is textually DELETED, and every `sil-` line field
is renamed `Un-Used-Sil-` - deliberately neutralised. Second, the bridge then
declares its own line record inline [common/slinvoiceMT.cbl:L361-L377], flat at
`03` level, one level shallower than the copybook's `05`/`07` nesting, with no
OCCURS, closing on `03 filler pic x.` [L377] commented "size 80 to here -1
26/7/23 2 match slwsinv". The dataclasses below are built from the COPYBOOKS,
not from that inline block; the inline block matters here only as evidence, and
for one anomaly it alone explains - see `sil-Back-Ordered` under ANOMALIES.

One further bridge fact worth recording: the preSQL directive block
[common/slinvoiceMT.cbl:L381-L384] names the schema `ACASDB` and then declares
TWO tables with TWO host-variable prefixes, `TABLE=SAINVOICE-REC,HV` followed by
`TABLE=SAINV-LINES-REC,HV1`. Counted strictly between the directive's opening
and closing markers, eighteen of the twenty in-scope bridges declare a single
table and only two declare a pair - this one and `plinvoiceMT`, the same
Invoice-shaped exception seen from the Purchase side.

THE THREE VIEWS OF slwsinv2.cob
===============================
`slwsinv2.cob` declares three `01` levels over one buffer, two of them
REDEFINES [copybooks/slwsinv2.cob:L27], [:L38], [:L91]:

    01  Invoice-Record.                            137 bytes
    01  Invoice-Header redefines Invoice-Record.    137 bytes
    01  Invoice-Line   redefines Invoice-Record.     80 bytes

All three are modelled, as `InvoiceRecord`, `IhInvoiceHeader` and
`IlInvoiceLine`, each with its own class docstring; none is collapsed into
another and none is treated as the real one. The base view is structurally
different from its own redefine, too: it declares a flat `Invoice-Customer pic
x(7)` [:L31] where the redefine nests `ih-nos` and `ih-check` [:L43-L44], and
`Invoice-Line` starts its members at level 05 directly under the `01`.

BYTE ARITHMETIC - COMPUTED, REPORTED, NOT SETTLED
=================================================
Every subtotal was computed from the declared fields, taking each field's
width from its dictionary entry rather than by counting characters by eye:

    sih-prime         [copybooks/slwsinv.cob:L19]  "42 bytes"
                      8+2+6+1+4+10+1+10                       =  42  agrees
    Sih-Sub-Prime     [:L41]                       "95 bytes"
                      32 + 8x5 + 1 + 5 + 1+1+4+4+1+4+1+1      =  95  agrees
    SInvoice-Header   [:L18]                       "137 bytes"
                      42 + 95                                 = 137  agrees
    Invoice-Line,     [:L77]   "80 bytes each = 3200 bytes"
      one occurrence  8+2+13+2+2+1+32+5+5+2+5+1+1+1           =  80  agrees
    filler redefines  overlays sih-order pic x(10)
      sih-order       1+2+3+4                                 =  10  agrees
    Invoice-Record    [copybooks/slwsinv2.cob:L27]  "137"
                      8+2+7+4+10+1+10+95                      = 137  agrees
    Invoice-Header    [copybooks/slwsinv2.cob:L38]  "137 bytes" = 137  agrees
    Invoice-Line      [copybooks/slwsinv2.cob:L91]  "80"       =  80  see below

The packed fields count 5 bytes each - nine digits plus a sign nibble - and the
two `999v99 comp` fields count 4 while `99v99 comp` counts 2. The running byte
comments the maintainer left inside the line record corroborate the 80-byte
figure independently, and are quoted where that record is declared.

Every declared subtotal in both copybooks therefore agrees with its field sum,
which is worth stating because it is not the general case in this folder: the
batch record's declared length contradicts its field sum, and so do the IRS
system parameters. One item does stay open, and it is a span rather than a sum
- `Invoice-Line` [copybooks/slwsinv2.cob:L91] describes 80 bytes of a 137-byte
buffer, leaving 57 unreachable through that view. COBOL permits a shorter
REDEFINES, so this is legal rather than broken; what the compiled program reads
past byte 80 has to be measured, not deduced.

No record-length constant is declared anywhere in this module: the figures
above live in this docstring and in comments only, following the precedent that
a declared-length-versus-field-sum disagreement is arbitrated by running the
compiled program. Two maintainer questions sit directly on this arithmetic and
are quoted rather than answered - "42 ??? bytes"
[copybooks/slwsinv2.cob:L39], "95 ??? bytes" [:L60], and "NEED TO DO A SIZING
CHECK for all INVOICE copybooks." [:L25].

FIELD-NAME COLLISIONS ACROSS THE TWO COPYBOOKS (ANOMALY A-21)
=============================================================
`pending`, `invoiced`, `day-booked` and `Invoice-Line` are each declared in
BOTH copybooks, and `Invoice-Line` names two structurally different things: an
`occurs 40` group under `SInvoice-Bodies` [copybooks/slwsinv.cob:L81], and an
`01`-level REDEFINES of a single buffer [copybooks/slwsinv2.cob:L91]. In COBOL
such collisions force qualified references, which is why the General Ledger
posting path writes `post-code in WS-Posting-Record` and `vat-ac of
WS-Posting-Record` [general/gl070.cbl:L497], [:L521], [:L525]. The class-name
prefixes `Sih`/`Sil` and `Ih`/`Il` separate them here for free, but the
collision is recorded because the migration's traceability document has to
explain why the COBOL is qualified and this module is not.

TYPE DISCIPLINE (R-2) - AND IT RUNS IN BOTH DIRECTIONS
======================================================
    pic x(n), pic xx, pic xxx, pic x            -> str
    pic 9(n), pic 99, pic 9   DISPLAY, scale 0  -> int
    binary-char / binary-short / binary-long    -> int   (signed; see below)
    pic s9(7)v99 under an inherited comp-3      -> Decimal, scale 2
    pic 999v99 comp / pic 99v99 comp            -> Decimal, scale 2
    group items                                 -> nested dataclass

The rule is scale, not usage: scale 0 gives `int`, scale above 0 gives
`Decimal`, whichever usage is declared. "COMP means integer" is false here -
`sih-deduct-amt pic 999v99 comp` [copybooks/slwsinv.cob:L63] and `sil-discount
pic 99v99 comp` [:L92] are COMP and are `Decimal`, because they carry two
decimal places. Getting that backwards changes stored values in either
direction: a `Decimal` over a binary integer carries a remainder the compiled
program discards on divide, and an `int` over two decimal places discards pence
it keeps. There is no binary floating-point type anywhere in this module - not
in computation, not in storage, not in transport.

GROUP-USAGE INHERITANCE - SIXTEEN FIELDS WHOSE PICTURE LINE MISLEADS
====================================================================
    03  sih-fig                          comp-3.   [copybooks/slwsinv.cob:L43]
    03  ih-fig                           comp-3.   [copybooks/slwsinv2.cob:L62]

Each carries eight children [copybooks/slwsinv.cob:L44-L51],
[copybooks/slwsinv2.cob:L63-L70] declared `pic s9(7)v99` with NO usage clause
of their own, so all sixteen are packed decimal by inheritance from the group
header. Reading usage off a child's own PICTURE line would type every one as
zoned DISPLAY, and nothing would fail - every stored figure would simply be
wrong until a scenario state diff showed it. Usage, scale and signedness are
therefore read from the dictionary for all sixteen and never typed here. The
`SihFig` and `IhFig` class docstrings carry the rule in full.

DRIFT IS SURFACED, NEVER SETTLED
================================
Where the copybook, the bridge host variable and the MySQL column disagree,
this module reports the COPYBOOK view - because a record layout describes
COBOL-side storage - and offers the disagreement untouched through
`descriptor_for(...).drift()`. It never blends layers, never widens a field to a
column width and never applies the bridge's signedness loss: reproducing that
conversion belongs to the `acas016` handler module.

Six fields lose their sign at the bridge, all of them integers:

    sih-date / ih-date        binary-long  signed  -> IH-DAT   int unsigned
    sih-lines / ih-lines      binary-char  signed  -> IH-LINES tinyint unsigned
    sih-deduct-days           binary-char  signed  -> tinyint unsigned
    sih-days                  binary-char  signed  -> tinyint unsigned
    sih-cr                    binary-long  signed  -> IH-CR    int unsigned
    sil-qty / il-qty          binary-short signed  -> IL-QTY smallint unsigned

That bare `binary-char` IS signed is not an assumption: the bridge writes the
keyword explicitly where it wants otherwise, in `03 ws-98-lines binary-char
unsigned value zero.` [common/slinvoiceMT.cbl:L355] and `ws-99-lines` [:L356].
The copybooks write plain `binary-char`, `binary-short` and `binary-long`, so
those six are signed and their descriptors say so.

Set against that, the money passes through cleanly: all sixteen `sih-fig` /
`ih-fig` children are signed at copybook, host variable and column alike, as
are `sil-net`, `sil-unit` and `sil-vat`. Money clean and integers narrowed in
one record is why field metadata is taken from the dictionary field by field
and never inferred from what kind of thing a field is.

ANOMALIES REPRODUCED HERE, NOT PUT RIGHT (R-4)
==============================================
From the preserved user requirement, Agent Action Plan section 0.8.2:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included.
    A defect reproduced is correct; a defect fixed is a failure."

Each site carries its own locator comment at the point of reproduction; the
register is the migration's anomaly log.

 1. `sil-Back-Ordered` [copybooks/slwsinv.cob:L97-L98] and `il-Back-Ordered`
    [copybooks/slwsinv2.cob:L106] have NO bridge host variable and NO column -
    `grep -inc "back-ordered" common/slinvoiceMT.cbl` returns 0, and
    SAINV-LINES-REC ends at IL-UPDATE with 14 columns. The cause is dated: the
    bridge still models that byte as `03 filler pic x.` commented "size 80 to
    here -1 26/7/23 2 match slwsinv" [common/slinvoiceMT.cbl:L377], while both
    copybooks replaced the filler with the named field on 03/03/24
    [copybooks/slwsinv.cob:L14-L15], [copybooks/slwsinv2.cob:L20-L21]. Both are
    declared here anyway: R-3 cuts both ways, nothing added AND nothing removed.
 2. The autogen overlay members - `sih-Freq`, `sih-Repeat`, an inner `filler
    pic xxx` and `sih-Last-Date` [copybooks/slwsinv.cob:L28-L38] with their
    `ih-` twins [copybooks/slwsinv2.cob:L47-L57] - likewise have no host
    variables and no columns; only the base `IH-ORDER char(10)` exists. All are
    declared. The two overlay class docstrings carry the evidence.
 3. Two condition names share the value "D": `88 sih-Daily` and `88 sih-Testing`
    [copybooks/slwsinv.cob:L33-L34], mirrored at
    [copybooks/slwsinv2.cob:L52-L53]. Both are carried; a lookup keyed by value
    would collapse them.
 4. The `88` value lists differ between the twins and the reason is written
    down. `slwsinv.cob` is dual case - `values "P" "p"` L53, `values "I" "i"`
    L54, `values "Z" "z"` L55, `values "B" "b"` L68, `values "Z" "z"` L70.
    `slwsinv2.cob` is upper case only - L72, L73, L74, L87, L89. Its own
    header says why: "Removed lowercase values so just using UC"
    [copybooks/slwsinv2.cob:L14]. Both lists are carried exactly as declared.
 5. The condition name itself diverges: `88 sapplied`
    [copybooks/slwsinv.cob:L55] against `88 applied`
    [copybooks/slwsinv2.cob:L74]. Both spellings are carried.
 6. Within one file the header `88`s are dual case but the line `88` is single
    case - `88 sil-analyised value "Z"` [copybooks/slwsinv.cob:L96]. The
    asymmetry stands.
 7. `analyised` is a misspelling and it stays, at all four copybook sites
    [copybooks/slwsinv.cob:L70], [:L96], [copybooks/slwsinv2.cob:L89], [:L105],
    and in the bridge's own `WS-Sil-Analyised` [common/slinvoiceMT.cbl:L376].
 8. Column reordering. `sih-lines` is declared immediately before
    `sih-deduct-days` [copybooks/slwsinv.cob:L61]; the bridge declares
    `HV-IH-LINES` after `HV-IH-CR` [common/slinvoiceMT.cbl:L419] and the column
    sits at ordinal 29, after `IH-CR` at 28. Dataclass field order below
    follows the COPYBOOK, so the two orders differ by design.
 9. Bridge-only primary keys with dual materialisation. `HV-SINVOICE-KEY X(10)`
    [common/slinvoiceMT.cbl:L391] and `HV1-IL-LINE-KEY X(10)` [:L427] have no
    copybook field of those names; each concatenates a two-member group, whose
    members are ALSO carried separately, so each key reaches the table twice.
    No concatenated attribute is invented here. The `WsInvoiceKey` and `SilKey`
    class docstrings carry the moves and the column names.
10. Name truncation: `sih-date` / `ih-date` becomes `HV-IH-DAT`
    [common/slinvoiceMT.cbl:L395] and column `IH-DAT` - the trailing E is
    dropped. The attribute keeps the copybook name.
11. Alphanumeric group concatenation: `sih-customer` / `ih-customer`, a group
    of `x(6)` plus `9`, becomes one `HV-IH-CUSTOMER X(7)`
    [common/slinvoiceMT.cbl:L394]. Group and both children are declared.
12. Declaration beats comment, four times: `sih-test pic 99 value zero.  *>
    WAS binary-char` [copybooks/slwsinv.cob:L22], `sil-line pic 99.  *> was
    binary-char.` [:L84], `ih-test` [copybooks/slwsinv2.cob:L41] and `il-line`
    [:L93]. These are zoned DISPLAY at scale 0 and therefore `int`. The comment
    records history; the declaration governs.
13. Capital-F `Filler` [copybooks/slwsinv2.cob:L33] sits beside lower-case
    `filler` at L35 and L36. The casing is preserved in the descriptor's name.
14. Group-name casing diverges: `Sih-Sub-Prime` mixed case
    [copybooks/slwsinv.cob:L41] against `ih-sub-prime` lower case
    [copybooks/slwsinv2.cob:L60], while `sih-prime` L19 and `ih-prime` L39 are
    both lower case - so the divergence is confined to that one group.
15. `sih-day-book-flag pic x value space.` [copybooks/slwsinv.cob:L67] carries
    a VALUE clause; its twin `ih-day-book-flag pic x.`
    [copybooks/slwsinv2.cob:L86] does not. One has a default, the other none.
16. The same divergence on a second field: `sih-test pic 99 value zero.`
    [copybooks/slwsinv.cob:L22] carries a VALUE clause while its twin `ih-test
    pic 99.` [copybooks/slwsinv2.cob:L41] does not. Preserved the same way.
17. Two commented-out `filler`s [copybooks/slwsinv.cob:L99],
    [copybooks/slwsinv2.cob:L107], both reading "was pic xx.", are dead source.
    Their existence is recorded; nothing is declared for them.
18. `pic xxx` and `pic xx` forms stand beside `pic x(n)` - the inner filler at
    [copybooks/slwsinv.cob:L37], `sil-pa` [:L86], `il-pa`
    [copybooks/slwsinv2.cob:L95], carrying character lengths 3 and 2.
19. OCCURS is treated three ways for one concept: `occurs 40` on `Invoice-Line`
    [copybooks/slwsinv.cob:L81], no OCCURS on the `slwsinv2.cob` redefine
    [copybooks/slwsinv2.cob:L91], and textual deletion in the bridge
    [common/slinvoiceMT.cbl:L458]. Each is preserved in its source's terms.
20. Both copybooks carry the same standing warning, "WARNING UPDATE all
    layouts for 5 byte increase (extra statuses)" [copybooks/slwsinv.cob:L12],
    [copybooks/slwsinv2.cob:L11], and `slwsinv.cob` records the 2024 change
    with the typo intact: "Addded lowercase values for some values - JIC."
    [copybooks/slwsinv.cob:L16].
21. The size histories differ between the twins. Both record 129 -> 134 -> 137
    bytes, on different dates: 09/03/09, 24/03/12, 18/01/17
    [copybooks/slwsinv.cob:L9-L11] against 09/03/09, 17/05/13, 25/01/17
    [copybooks/slwsinv2.cob:L7-L9].
22. Signedness is narrowed at the bridge on six integer fields, the Agent
    Action Plan's own anomaly 11, tagged A-11 in the dictionary. `sih-date`
    [copybooks/slwsinv.cob:L26], `sih-lines` [:L61], `sih-deduct-days` [:L62],
    `sih-days` [:L65] and `sih-cr` [:L66], plus `sil-qty` [:L87], are each a
    bare member of the binary family and therefore SIGNED; every one becomes an
    unsigned host variable and an unsigned column - `HV-IH-DAT PIC 9(10) COMP`
    [common/slinvoiceMT.cbl:L395], `HV-IH-LINES PIC 9(03) COMP` [:L419],
    `HV-IH-DEDUCT-DAYS` [:L414], `HV-IH-DAYS` [:L417], `HV-IH-CR` [:L418] and
    `HV1-IL-QTY PIC 9(05) COMP` [:L432]. The sign is lost AT THE BRIDGE, before
    any SQL runs; the conversion belongs to the `acas016` handler module. What a
    negative value actually stores is an open question, below, marked Q-3.

There is deliberately no settled, single-winner or put-right type, view, value
or picture anywhere below, and none may be introduced. Where two sources
disagree, both are carried and both are cited.

OPEN QUESTIONS FOR THE COMPILED PROGRAM (R-6)
=============================================
Recorded in the migration's ambiguity-resolutions document, none settled here:

  * `Invoice-Line` [copybooks/slwsinv2.cob:L91] describes 80 bytes of a
    137-byte buffer. What does the compiled program read past byte 80 through
    that view?
  * What value is stored when a negative `binary-char`, `binary-short` or
    `binary-long` passes through an unsigned host variable into an unsigned
    column? Six sites here; the dictionary marks them Q-3.
  * Does anything read `sil-Back-Ordered` or `il-Back-Ordered` back, given that
    neither the bridge nor the table carries the byte? A value written and
    re-read inside one run survives in memory, never in the database. The same
    question for `sih-Freq`, `sih-Repeat` and `sih-Last-Date`.
  * The Agent Action Plan names both copybooks as this record's layout sources;
    the bridge copies only the first. Which governs the bytes on disk?

LAYERING AND IMPORT-TIME COST
=============================
Agent Action Plan section 0.4.3 grants `records/*.py` two imports and forbids
the rest, so that the arithmetic test tier "imports only `cobol` and `records`
and touches no database, so it runs anywhere". This module imports
`acas_posting.cobol.field` and `acas_posting.dictionary.loader` - the two the
plan grants - and nothing else from the package. The object-model types it names
in return annotations come through the loader's re-exports, so
`acas_posting.dictionary.model` is never reached directly: not
`dal`, not `programs`, not `cli`, not `cobol.condition_names`, and no other
record module. In particular `records/purchase_invoice.py` is the Purchase
mirror of this file and is deliberately NOT shared with: the two must be free
to diverge exactly as their copybooks do, so any resemblance between them is
an outcome and never a mechanism.

Nothing is read at import. Each dataclass field carries its dictionary key as
field metadata - a plain string - and the descriptor is fetched on demand
through `descriptor_for`, which delegates to the memoised
`FieldDescriptor.from_dictionary_key`. Importing this module therefore parses no
artifact, opens no file, consults no clock and inspects no environment, so two
imports in two processes produce identical state.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from decimal import Decimal
from typing import Any, ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# Two dictionary types are needed for return annotations only, and neither has
# a substitute. `ConditionName` is the dictionary's own record for an 88-level -
# exactly the (name, value, source) triple this module hands back - and `Drift`
# is what `loader.drift_for` returns. Agent Action Plan section 0.4.3 lists
# `dictionary.loader` for this folder, and that is where both come from: the
# loader re-exports the object model's records alongside its accessors (see its
# `RE_EXPORTED_MODEL_NAMES`), each re-export being a BINDING to the single
# definition rather than a copy, so `loader.Drift` IS the class `loader.drift_for`
# returns. Declaring local copies instead would create exactly the duplicate,
# drifting definitions that R-4's divergence-preservation discipline exists to
# prevent, and reaching past the loader would breach a frozen plan.
from acas_posting.dictionary.loader import ConditionName, Drift


# The frozen spine this record sits on
# Named once, here, so that every citation below is a locator rather than a
# repeated string literal. Each value is copied from the source it names and
# from nowhere else; `loader.table_for("SAINVOICE-REC")` reports the same
# bridge, handler, entity facade and copybook pair independently.

#: The layout source. The bridge copies this one [common/slinvoiceMT.cbl:L456].
COPYBOOK_SLWSINV: Final[str] = "copybooks/slwsinv.cob"

#: The second view set. Supplies the names the MySQL columns use; the bridge
#: does not copy it. See the docstring's four-layer table.
COPYBOOK_SLWSINV2: Final[str] = "copybooks/slwsinv2.cob"

#: The one-way COBOL-to-MySQL bridge for this entity - the data dictionary for
#: this migration, per Agent Action Plan section 0.8.2.
BRIDGE: Final[str] = "common/slinvoiceMT.cbl"

#: The numbered file handler the posting programs CALL for this entity.
HANDLER: Final[str] = "acas016"

#: The entity facade name in `copybooks/Proc-ACAS-FH-Calls.cob`.
ENTITY_FACADE: Final[str] = "Invoice"

#: The invoice header table: 31 columns, primary key SINVOICE-KEY char(10).
HEADER_TABLE: Final[str] = "SAINVOICE-REC"

#: The invoice lines table: 14 columns, primary key IL-LINE-KEY char(10).
LINES_TABLE: Final[str] = "SAINV-LINES-REC"

# The dataclass-field metadata slot holding each attribute's dictionary key.
# Prefixed so it cannot collide with metadata any other tool attaches.
_DICTIONARY_KEY: Final[str] = "acas_posting.dictionary_key"


def _entry(dictionary_key: str) -> dict[str, str]:
    """Attach ``dictionary_key`` to a dataclass field as its provenance.

    R-5 requires every Python field definition to cite its data-dictionary
    entry. Carrying the key in field metadata rather than in a module-level
    constant keeps that citation attached to the attribute it describes and,
    critically, costs nothing at import: the value is a plain string, and the
    artifact is parsed only when :func:`descriptor_for` is first called for
    that key.

    Every key passed here was read out of the generated dictionary and matched
    to its field by the entry's own ``copybook.name``. None was built by
    transforming a COBOL name, because that does not work for this record -
    upper-casing ``sih-net`` yields ``SIH-NET``, which no entry carries; the
    entry is ``SAINVOICE-REC.IH-NET``.
    """
    return {_DICTIONARY_KEY: dictionary_key}


def dictionary_key_for(record: Any, attribute: str) -> str:
    """Return the data-dictionary key cited by ``attribute`` of ``record``.

    ``record`` is any dataclass in this module, as the class itself or as an
    instance.

    Raises:
        AttributeError: if ``record`` declares no such attribute.
        LookupError: if the attribute exists but cites no dictionary entry,
            which would mean the provenance invariant had been broken.
    """
    for declared in fields(record):
        if declared.name == attribute:
            key = declared.metadata.get(_DICTIONARY_KEY)
            if key is None:
                raise LookupError(
                    f"{_record_label(record)}.{attribute} cites no data-dictionary "
                    f"entry; every attribute in this module must carry one"
                )
            return key
    raise AttributeError(f"{_record_label(record)} declares no field {attribute!r}")


def dictionary_keys_for(record: Any) -> tuple[tuple[str, str], ...]:
    """Return ``(attribute, dictionary key)`` pairs in declaration order.

    Declaration order here is COBOL declaration order, because that is the
    order the dataclasses are written in. This is the pairing that
    the migration's traceability document tabulates, and the one a census
    diffs against ``cat -n`` of the copybook.
    """
    return tuple(
        (declared.name, declared.metadata[_DICTIONARY_KEY])
        for declared in fields(record)
        if _DICTIONARY_KEY in declared.metadata
    )


def descriptor_for(record: Any, attribute: str) -> FieldDescriptor:
    """Return the :class:`FieldDescriptor` for ``attribute`` of ``record``.

    The descriptor reports the COPYBOOK view of the field - its picture, usage,
    digits, scale, signedness and storage class as COBOL declares them - and
    offers any disagreement with the bridge host variable or the MySQL column
    through :func:`drift_for`, untouched. It never blends the three layers.

    Nothing about the field is transcribed here: the descriptor is built from
    the dictionary entry by ``FieldDescriptor.from_dictionary_key``, which is
    memoised, so repeated calls cost one lookup.
    """
    return FieldDescriptor.from_dictionary_key(dictionary_key_for(record, attribute))


def cite_for(record: Any, attribute: str) -> str:
    """Return the three-locator provenance line for ``attribute``.

    The shape, straight from the loader, is the R-5 primitive - copybook line,
    bridge line and column line for one field:

        SAINVOICE-REC.IH-NET  copybook=copybooks/slwsinv.cob:L45
        bridge=common/slinvoiceMT.cbl:L401  column=mysql/ACASDB.sql:L855

    A field the bridge and the table do not carry reports ``bridge=absent``
    and ``column=absent`` instead, which is how the copybook-only fields in
    this module - ``sil-Back-Ordered`` among them - identify themselves.
    """
    return loader.cite(dictionary_key_for(record, attribute))


def drift_for(record: Any, attribute: str) -> Drift:
    """Return the copybook/bridge/column disagreement for ``attribute``.

    Surfaced and left as it stands. Reproducing the bridge's conversions -
    notably the signedness loss on the six integer fields listed in the module
    docstring - is the `acas016` handler module's work, not this
    module's, and doing it here would put a second, disagreeing answer in the
    codebase.
    """
    return loader.drift_for(dictionary_key_for(record, attribute))


def record_dictionary_key(record: Any) -> str:
    """Return the dictionary key of the COBOL group ``record`` itself models."""
    return str(record.COBOL_DICTIONARY_KEY)


def record_descriptor(record: Any) -> FieldDescriptor:
    """Return the :class:`FieldDescriptor` for the COBOL group ``record`` models.

    This is where an OCCURS count lives: the descriptor for
    :class:`SilInvoiceLine` reports ``occurs == 40`` from
    [copybooks/slwsinv.cob:L81]. The count is not transcribed into this module
    as a constant, and no check enforces it, because either would be logic the
    copybook does not contain.
    """
    return FieldDescriptor.from_dictionary_key(record_dictionary_key(record))


def _record_label(record: Any) -> str:
    """Return a readable class name for ``record``, given a class or instance."""
    return record.__name__ if isinstance(record, type) else type(record).__name__


def _condition_source_line(condition: ConditionName) -> int:
    """Return the copybook line number a condition name was declared on.

    The dictionary does not hand condition names back in declaration order, and
    R-6 requires a deterministic order, so they are ordered by the line in
    their own ``source`` locator - which is declaration order by construction.
    """
    tail = condition.source.rsplit(":L", 1)[-1]
    return int(tail.split("-", 1)[0])


def _condition_names_declared_in(copybook: str) -> tuple[ConditionName, ...]:
    """Return every 88-level declared in ``copybook``, in declaration order."""
    declared = [
        condition
        for entry in loader.entries_for_copybook_file(copybook)
        for condition in entry.copybook.condition_names
    ]
    declared.sort(key=_condition_source_line)
    return tuple(declared)


def condition_names_slwsinv() -> tuple[ConditionName, ...]:
    """Return the twelve 88-levels of `copybooks/slwsinv.cob`, in source order.

    Carried as DATA, with each ``value`` the VALUE or VALUES literal text
    exactly as written, so a multi-value form stays one condition name with
    four literals: ``sih-Valid-Freqs`` is ``'"Y" "M" "Q" "D"'``, not four
    entries [copybooks/slwsinv.cob:L35].

    Two of the twelve share the literal ``"D"`` - ``sih-Daily``
    [copybooks/slwsinv.cob:L33] and ``sih-Testing`` [:L34], the maintainer's
    "These two are only for testing." / "So NOT documented and removed after
    tests." Both are returned. An index keyed by value would collapse them and
    lose one.

    Turning any of these into a predicate is `acas_posting/cobol/
    condition_names.py`'s job. This module publishes the declarations; that
    module evaluates them.
    """
    return _condition_names_declared_in(COPYBOOK_SLWSINV)


def condition_names_slwsinv2() -> tuple[ConditionName, ...]:
    """Return the twelve 88-levels of `copybooks/slwsinv2.cob`, in source order.

    The same twelve concepts as :func:`condition_names_slwsinv`, declared
    differently on purpose, and the module docstring lists every divergence:
    upper-case literals only where the twin is dual case, and ``applied``
    [copybooks/slwsinv2.cob:L74] where the twin writes ``sapplied``
    [copybooks/slwsinv.cob:L55]. The file says why itself - "Removed lowercase
    values so just using UC" [copybooks/slwsinv2.cob:L14]. Both lists are
    returned as declared; neither is adjusted towards the other.
    """
    return _condition_names_declared_in(COPYBOOK_SLWSINV2)


def condition_names_for(record: Any, attribute: str) -> tuple[ConditionName, ...]:
    """Return the 88-levels declared on one attribute, in declaration order.

    Empty for the great majority of attributes; six condition names hang off
    ``sih_freq`` and ``ih_freq``, three off each status byte, and one each off
    the day-book and update flags.
    """
    entry = loader.get_entry(dictionary_key_for(record, attribute))
    return tuple(sorted(entry.copybook.condition_names, key=_condition_source_line))


#  copybooks/slwsinv.cob - the layout the bridge copies
# Plain mutable dataclasses, because `sl055` and `sl060` read a record, change fields and write
# it back. Fields are keyword-only, and that is not decoration: `Sih-Sub-Prime` declares
# `sih-day-book-flag` carrying `value space` [copybooks/slwsinv.cob:L67] BEFORE `sih-update`,
# which carries none [:L69]. Positional fields would reject that order and force a reordering or
# an invented default - forbidden by R-6 and R-3 respectively.
# FIELD order is COBOL declaration order, so a class diffs against `cat -n` of the copybook;
# CLASS definitions run innermost-first. Copybook and column order genuinely differ here:
# `sih-lines` is declared immediately before `sih-deduct-days` [copybooks/slwsinv.cob:L61],
# while the bridge declares `HV-IH-LINES` after `HV-IH-CR` [common/slinvoiceMT.cbl:L419] and the
# column stands at ordinal 29. Copybook order governs here; column-ordinal order is what
# `loader.entries_for_table` reports.


@dataclass(kw_only=True, slots=True)
class WsInvoiceKey:
    """``03  WS-Invoice-Key.`` [copybooks/slwsinv.cob:L20] - the invoice key group.

    Ten bytes: an eight-digit invoice number and a two-digit test suffix.

    The bridge concatenates the whole group into a single alphanumeric host
    variable, `HV-SINVOICE-KEY X(10)` [common/slinvoiceMT.cbl:L391], by `move
    WS-Invoice-Key to HV-SINVOICE-KEY` [:L1455], and that becomes the primary
    key column `SINVOICE-KEY char(10)`. The two members are ALSO carried
    separately as `IH-INVOICE` and `IH-TEST`, so the key reaches the table
    twice - once joined, once split. No joined attribute is declared here: that
    name exists only on the column side, and building it is
    the `acas016` handler module's work.

    The dictionary records one more fact about that host variable worth knowing
    before reading a value back: it is never moved into the record after a
    read, so a value read from the database does not reach the caller through
    it.
    """

    COBOL_NAME: ClassVar[str] = "WS-Invoice-Key"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L20"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SAINVOICE-REC.SINVOICE-KEY"

    # 05  sih-invoice   pic 9(8).                    [copybooks/slwsinv.cob:L21]
    # Zoned DISPLAY at eight digits. The bridge widens it to `9(10) COMP`
    # [common/slinvoiceMT.cbl:L392]; the descriptor reports the copybook's eight.
    sih_invoice: int = field(metadata=_entry("SAINVOICE-REC.IH-INVOICE"))

    # 05  sih-test      pic 99  value zero.  *> WAS binary-char
    #                                                [copybooks/slwsinv.cob:L22]
    # R-4: declaration beats comment. The comment records that this field once
    # was binary; the live declaration is `pic 99`, so it is zoned DISPLAY at
    # scale 0 and therefore `int`. The `value zero` is the reason for the only
    # numeric default in this class. Its twin `ih-test` [copybooks/slwsinv2.cob:L41]
    # carries no VALUE clause at all, and that divergence stands.
    sih_test: int = field(default=0, metadata=_entry("SAINVOICE-REC.IH-TEST"))


@dataclass(kw_only=True, slots=True)
class SihCustomer:
    """``03  sih-customer.`` [copybooks/slwsinv.cob:L23] - the customer key group.

    Seven bytes: a six-character account number and a one-digit check digit.

    R-4, alphanumeric group concatenation: the bridge collapses the group into
    one `HV-IH-CUSTOMER X(7)` [common/slinvoiceMT.cbl:L394] through `move
    WS-Sih-Customer to HV-IH-CUSTOMER` [:L1459], stored as `IH-CUSTOMER
    char(7)`. Unlike the invoice key, the members are NOT also carried
    separately, so the seven bytes reach the table once. The group and both
    children are still declared, because the copybook declares them.

    The second view set is structured differently again: its base buffer
    declares a flat `Invoice-Customer pic x(7)` [copybooks/slwsinv2.cob:L31]
    with no members, while its own redefine nests `ih-nos` and `ih-check`
    [:L43-L44]. All three shapes are carried, in their own classes.
    """

    COBOL_NAME: ClassVar[str] = "sih-customer"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L23"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SAINVOICE-REC.IH-CUSTOMER"

    # 05  sih-nos       pic x(6).                    [copybooks/slwsinv.cob:L24]
    sih_nos: str = field(metadata=_entry("SInvoice-Header.sih-nos"))

    # 05  sih-check     pic 9.                       [copybooks/slwsinv.cob:L25]
    sih_check: int = field(metadata=_entry("SInvoice-Header.sih-check"))


@dataclass(kw_only=True, slots=True)
class SihOrderView:
    """``03  filler redefines sih-order.`` [copybooks/slwsinv.cob:L28].

    An unnamed REDEFINES laid over the ten bytes of `sih-order`
    [copybooks/slwsinv.cob:L27], carrying the autogen and recurring-invoice
    view the maintainer added in 2023: "New changes 24/3/23 for
    Autogen/recurring invoices" [:L27], introduced by "02/05/23 - updated for
    Autogen see below sih-Order" [:L13]. Its four members sum to 1 + 2 + 3 + 4
    = 10 bytes, exactly the field they overlay.

    R-4, copybook-only: not one of the four has a bridge host variable or a
    column. Only the base view `IH-ORDER char(10)` exists - searching
    `common/slinvoiceMT.cbl` case-insensitively for any of `freq`, `repeat` or
    `last-date` returns eight hits, every one of them unrelated "Repeat Group"
    metadata commentary. That is
    consistent with the Sales autogen tables (`SAAUTOGEN-REC` and its lines)
    being out of scope per Agent Action Plan section 0.2.2. All four are
    declared regardless: R-3 forbids removing a field as firmly as adding one.

    The maintainer's own open question about this overlay is carried unanswered:
    "Redefines of il-Order for recurring support. Needed ??"
    [copybooks/slwsinv2.cob:L22].

    Nothing here keeps the overlay and `sih_order` in step. The COBOL does not
    either - a REDEFINES shares storage, and this module models declarations,
    not storage - and synchronising them would be added behaviour.
    """

    COBOL_NAME: ClassVar[str] = "filler"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L28"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Header.filler#28"

    # 05  sih-Freq      pic x.                       [copybooks/slwsinv.cob:L29]
    # Six condition names hang off this one byte [:L30-L35], two of them
    # sharing the literal "D". See condition_names_slwsinv().
    sih_freq: str = field(metadata=_entry("SInvoice-Header.sih-Freq"))

    # 05  sih-Repeat    pic 99.                      [copybooks/slwsinv.cob:L36]
    sih_repeat: int = field(metadata=_entry("SInvoice-Header.sih-Repeat"))

    # 05  filler        pic xxx.                     [copybooks/slwsinv.cob:L37]
    # R-4: the `xxx` short form, not `x(3)`. The entry keeps the literal
    # picture text and reports character length 3. A filler occupies bytes and
    # so is declared, never dropped; the attribute is named for its
    # declaration line because the COBOL name is not unique.
    filler_37: str = field(metadata=_entry("SInvoice-Header.filler#37"))

    # 05  sih-Last-Date binary-long.                 [copybooks/slwsinv.cob:L38]
    # "4 bytes date an invoice was generated/posted". Signed binary, scale 0,
    # therefore `int` - and no column carries it.
    sih_last_date: int = field(metadata=_entry("SInvoice-Header.sih-Last-Date"))


@dataclass(kw_only=True, slots=True)
class SihPrime:
    """``02 sih-prime.`` [copybooks/slwsinv.cob:L19] - the first 42 bytes.

    The copybook annotates this group "42 bytes", and the declared members sum
    to 8 + 2 + 6 + 1 + 4 + 10 + 1 + 10 = 42, so the annotation agrees. The twin
    marks the same subtotal "42 ??? bytes" [copybooks/slwsinv2.cob:L39]; the
    question mark is the maintainer's and is left standing.

    Both the key group and the overlay that redefines `sih-order` are declared
    as members, in the order the copybook declares them.
    """

    COBOL_NAME: ClassVar[str] = "sih-prime"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L19"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Header.sih-prime"

    # 03  WS-Invoice-Key.                            [copybooks/slwsinv.cob:L20]
    ws_invoice_key: WsInvoiceKey = field(
        metadata=_entry("SAINVOICE-REC.SINVOICE-KEY")
    )

    # 03  sih-customer.                              [copybooks/slwsinv.cob:L23]
    sih_customer: SihCustomer = field(metadata=_entry("SAINVOICE-REC.IH-CUSTOMER"))

    # 03  sih-date          binary-long.             [copybooks/slwsinv.cob:L26]
    # "For autogen next date due". R-4, two drifts at once on one field: the
    # name loses its trailing E at the bridge - `HV-IH-DAT`
    # [common/slinvoiceMT.cbl:L395], column `IH-DAT` - and the signed binary
    # narrows to an unsigned column. The attribute keeps the copybook name and
    # the descriptor reports signed; what an unsigned column stores for a
    # negative value is an open question, marked Q-3 in the dictionary.
    sih_date: int = field(metadata=_entry("SAINVOICE-REC.IH-DAT"))

    # 03  sih-order         pic x(10).                [copybooks/slwsinv.cob:L27]
    sih_order: str = field(metadata=_entry("SAINVOICE-REC.IH-ORDER"))

    # 03  filler redefines sih-order.                [copybooks/slwsinv.cob:L28]
    filler_28: SihOrderView = field(metadata=_entry("SInvoice-Header.filler#28"))

    # 03  sih-type          pic 9.                    [copybooks/slwsinv.cob:L39]
    sih_type: int = field(metadata=_entry("SAINVOICE-REC.IH-TYPE"))

    # 03  sih-ref           pic x(10).                [copybooks/slwsinv.cob:L40]
    sih_ref: str = field(metadata=_entry("SAINVOICE-REC.IH-REF"))


@dataclass(kw_only=True, slots=True)
class SihFig:
    """``03  sih-fig                          comp-3.`` [copybooks/slwsinv.cob:L43].

    GROUP-USAGE INHERITANCE, and it is load-bearing. The group header carries
    `comp-3`; its eight children [copybooks/slwsinv.cob:L44-L51] are each
    declared `pic s9(7)v99` with NO usage clause of their own. All eight are
    therefore packed decimal, inherited from this line, and each descriptor
    reports ``usage == COMP-3``, ``usage_declared_at == GROUP`` and
    ``usage_inherited_from == "sih-fig"``.

    Reading usage off a child's own PICTURE line would type all eight as zoned
    DISPLAY. Nothing would fail; every stored figure would simply be wrong,
    and the first sign of it would be a scenario state diff. The values are
    taken from the dictionary and never typed here for exactly that reason.

    Contrast, in this same record: `sih-deduct-amt` and `sih-deduct-vat`
    [copybooks/slwsinv.cob:L63-L64] write `comp` on their own PICTURE lines, so
    those report ``usage_declared_at == FIELD`` with no inheritance. The
    direction of the rule is what matters, both ways.

    These eight are also the clean pass-through of the whole record: signed at
    copybook, host variable [common/slinvoiceMT.cbl:L400-L407] and column
    `decimal(9,2)` alike. Six integer fields in the same record are not, which
    is why signedness is read per field from the dictionary rather than guessed
    from a field's kind.
    """

    COBOL_NAME: ClassVar[str] = "sih-fig"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L43"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Header.sih-fig"

    # 05  sih-p-c       pic s9(7)v99.                [copybooks/slwsinv.cob:L44]
    sih_p_c: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-P-C"))

    # 05  sih-net       pic s9(7)v99.                [copybooks/slwsinv.cob:L45]
    sih_net: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-NET"))

    # 05  sih-extra     pic s9(7)v99.                [copybooks/slwsinv.cob:L46]
    sih_extra: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-EXTRA"))

    # 05  sih-carriage  pic s9(7)v99.                [copybooks/slwsinv.cob:L47]
    sih_carriage: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-CARRIAGE"))

    # 05  sih-vat       pic s9(7)v99.                [copybooks/slwsinv.cob:L48]
    sih_vat: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-VAT"))

    # 05  sih-discount  pic s9(7)v99.                [copybooks/slwsinv.cob:L49]
    sih_discount: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-DISCOUNT"))

    # 05  sih-e-vat     pic s9(7)v99.                [copybooks/slwsinv.cob:L50]
    sih_e_vat: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-E-VAT"))

    # 05  sih-c-vat     pic s9(7)v99.                [copybooks/slwsinv.cob:L51]
    sih_c_vat: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-C-VAT"))


@dataclass(kw_only=True, slots=True)
class SihSubPrime:
    """``02 Sih-Sub-Prime.`` [copybooks/slwsinv.cob:L41] - the remaining 95 bytes.

    R-4, group-name casing: this group is mixed case here and lower case as
    `ih-sub-prime` in the twin [copybooks/slwsinv2.cob:L60], while `sih-prime`
    [:L19] and `ih-prime` [copybooks/slwsinv2.cob:L39] are both lower case. The
    casing is carried as declared, in each class's own COBOL_NAME.

    The copybook annotates the group "95 bytes", and the members sum to 32 for
    the description, 40 for the eight packed figures, six status bytes, one
    line count, one deduction-days count, four and four for the two COMP
    deduction figures, one days count, four for the credit reference and two
    single-byte flags - 95, so the annotation agrees. The twin marks the same
    subtotal "95 ??? bytes" [copybooks/slwsinv2.cob:L60].

    Five individually named status bytes [copybooks/slwsinv.cob:L56-L60] follow
    the general status flag, each documented "space or X". They are five
    separate one-byte fields and are declared as five, never folded into a set.
    """

    COBOL_NAME: ClassVar[str] = "Sih-Sub-Prime"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L41"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Header.Sih-Sub-Prime"

    # 03  sih-description   pic x(32).               [copybooks/slwsinv.cob:L42]
    sih_description: str = field(metadata=_entry("SAINVOICE-REC.IH-DESCRIPTION"))

    # 03  sih-fig                          comp-3.   [copybooks/slwsinv.cob:L43]
    sih_fig: SihFig = field(metadata=_entry("SInvoice-Header.sih-fig"))

    # 03  sih-status        pic x.                   [copybooks/slwsinv.cob:L52]
    # Three dual-case condition names [:L53-L55], one of them `sapplied`, which
    # the twin spells `applied` [copybooks/slwsinv2.cob:L74].
    sih_status: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS"))

    # 03  sih-status-P      pic x.   *> Pick list Printed  space or P
    #                                                [copybooks/slwsinv.cob:L56]
    sih_status_p: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS-P"))

    # 03  sih-status-L      pic x.   *> Invoice Printed    space or L
    #                                                [copybooks/slwsinv.cob:L57]
    sih_status_l: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS-L"))

    # 03  sih-status-C      pic x.   *> Invoice Cleared    space or C
    #                                                [copybooks/slwsinv.cob:L58]
    sih_status_c: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS-C"))

    # 03  sih-status-A      pic x.   *> Invoice Applied to a/c  space or A
    #                                                [copybooks/slwsinv.cob:L59]
    sih_status_a: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS-A"))

    # 03  sih-status-I      pic x.   *> Invoice Item lines Deleted  space or D
    #                                                [copybooks/slwsinv.cob:L60]
    # Note the byte is named -I while the value it takes is D. Carried as is.
    sih_status_i: str = field(metadata=_entry("SAINVOICE-REC.IH-STATUS-I"))

    # 03  sih-lines         binary-char.             [copybooks/slwsinv.cob:L61]
    # "No. of following body line recs". R-4, column reordering: declared here,
    # third from the end of the group, but written to the table last but two -
    # `HV-IH-LINES` sits after `HV-IH-CR` [common/slinvoiceMT.cbl:L419] and
    # `IH-LINES` stands at ordinal 29, after `IH-CR` at 28. This module keeps
    # the copybook position. R-4 again, signedness: signed here, unsigned
    # tinyint in the table.
    sih_lines: int = field(metadata=_entry("SAINVOICE-REC.IH-LINES"))

    # 03  sih-deduct-days   binary-char.             [copybooks/slwsinv.cob:L62]
    # Signed here, unsigned tinyint in the table. Surfaced through drift_for.
    sih_deduct_days: int = field(metadata=_entry("SAINVOICE-REC.IH-DEDUCT-DAYS"))

    # 03  sih-deduct-amt    pic 999v99    comp.      [copybooks/slwsinv.cob:L63]
    # Usage is on this field's own PICTURE line, so no inheritance applies. And
    # it is `Decimal`, not `int`, despite being COMP: scale decides storage, not
    # usage. Unsigned at all three layers, so no signedness drift either.
    sih_deduct_amt: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-DEDUCT-AMT"))

    # 03  sih-deduct-vat    pic 999v99    comp.      [copybooks/slwsinv.cob:L64]
    sih_deduct_vat: Decimal = field(metadata=_entry("SAINVOICE-REC.IH-DEDUCT-VAT"))

    # 03  sih-days          binary-char.             [copybooks/slwsinv.cob:L65]
    # Signed here, unsigned tinyint in the table.
    sih_days: int = field(metadata=_entry("SAINVOICE-REC.IH-DAYS"))

    # 03  sih-cr            binary-long.             [copybooks/slwsinv.cob:L66]
    # Signed here, unsigned int in the table.
    sih_cr: int = field(metadata=_entry("SAINVOICE-REC.IH-CR"))

    # 03  sih-day-book-flag pic x               value space.
    #                                                [copybooks/slwsinv.cob:L67]
    # R-4: this field HAS a VALUE clause and its twin `ih-day-book-flag`
    # [copybooks/slwsinv2.cob:L86] has none. The default below reflects the
    # clause the copybook writes; no default is invented for the twin. Carrying
    # a VALUE clause after a field that has none is also why this class is
    # keyword-only.
    sih_day_book_flag: str = field(
        default=" ", metadata=_entry("SAINVOICE-REC.IH-DAY-BOOK-FLAG")
    )

    # 03  sih-update        pic x.                   [copybooks/slwsinv.cob:L69]
    # Carries `88 sih-analyised values "Z" "z".` [:L70]. R-4: `analyised` is a
    # misspelling and it stays, here and at three further copybook sites and in
    # the bridge's own `WS-Sil-Analyised` [common/slinvoiceMT.cbl:L376].
    sih_update: str = field(metadata=_entry("SAINVOICE-REC.IH-UPDATE"))


@dataclass(kw_only=True, slots=True)
class SInvoiceHeader:
    """``01  SInvoice-Header.`` [copybooks/slwsinv.cob:L18] - 137 bytes.

    The invoice header, in the layout the bridge actually copies
    [common/slinvoiceMT.cbl:L456], and the source of the 31 columns of
    `SAINVOICE-REC`. Two groups, and their annotated subtotals add up: 42 for
    `sih-prime` plus 95 for `Sih-Sub-Prime` is the 137 this record declares.

    The copybook's own size history, which the twin records differently:
    "size 129 bytes 09/03/09" [:L9], "size 134 bytes 24/03/12" [:L10], "size
    137 bytes 18/01/17" [:L11] - against 09/03/09, 17/05/13 and 25/01/17 in
    [copybooks/slwsinv2.cob:L7-L9]. Both files then carry the same standing
    warning, quoted intact: "WARNING UPDATE all layouts for 5 byte increase
    (extra statuses)" [copybooks/slwsinv.cob:L12], [copybooks/slwsinv2.cob:L11].

    The 2024 change is recorded with the maintainer's typo intact: "03/03/24 -
    in SInvoice-Bodies sil-Back-Ordered replaces the last field" / "(FILLER) -
    set to B for a BO item." / "Addded lowercase values for some values - JIC."
    [copybooks/slwsinv.cob:L14-L16].

    No record-length constant is declared. The arithmetic is in the module
    docstring; where a declared length and a field sum disagree in this
    codebase, the compiled program settles it, and this module does not
    pre-empt that even where the two agree.
    """

    COBOL_NAME: ClassVar[str] = "SInvoice-Header"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L18"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Header.SInvoice-Header"

    # 02 sih-prime.                    *> 42 bytes   [copybooks/slwsinv.cob:L19]
    sih_prime: SihPrime = field(metadata=_entry("SInvoice-Header.sih-prime"))

    # 02 Sih-Sub-Prime.                *> 95 bytes   [copybooks/slwsinv.cob:L41]
    sih_sub_prime: SihSubPrime = field(
        metadata=_entry("SInvoice-Header.Sih-Sub-Prime")
    )


@dataclass(kw_only=True, slots=True)
class SilKey:
    """``05  sil-Key.`` [copybooks/slwsinv.cob:L82] - the line key group, 10 bytes.

    R-4, the second bridge-only primary key: the group is concatenated into
    `HV1-IL-LINE-KEY X(10)` [common/slinvoiceMT.cbl:L427] by `move WS-Sil-Key
    to HV1-IL-LINE-KEY` [:L2789] and stored as `IL-LINE-KEY char(10)`, while
    its two members are ALSO carried separately as `IL-INVOICE` and `IL-LINE`.
    Dual materialisation again, and alphanumeric again - the same shape the
    General Ledger posting key takes numerically. The group and both children
    are declared; the joined column name is not an attribute here.
    """

    COBOL_NAME: ClassVar[str] = "sil-Key"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L82"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SAINV-LINES-REC.IL-LINE-KEY"

    # 07  sil-invoice pic 9(8).                      [copybooks/slwsinv.cob:L83]
    sil_invoice: int = field(metadata=_entry("SAINV-LINES-REC.IL-INVOICE"))

    # 07  sil-line    pic 99.       *> was binary-char.
    #                                                [copybooks/slwsinv.cob:L84]
    # R-4: declaration beats comment, as with `sih-test`. `pic 99` is zoned
    # DISPLAY at scale 0, therefore `int`.
    sil_line: int = field(metadata=_entry("SAINV-LINES-REC.IL-LINE"))


@dataclass(kw_only=True, slots=True)
class SilInvoiceLine:
    """``03  Invoice-Line                    occurs 40.`` [copybooks/slwsinv.cob:L81].

    One invoice body line - 80 bytes, documented "80 bytes each = 3200 bytes
    (17/05/13)" and "still valid 18/01/17" [copybooks/slwsinv.cob:L74-L78] -
    and the source of the 14 columns of `SAINV-LINES-REC`. The declared members
    sum to 80, and the maintainer's running byte comments along the way agree:
    "25" after `sil-pa`, "2 - 27" after `sil-qty`, "28" after `sil-type`, "60"
    after `sil-description`, "18 - 77" after `sil-vat`.

    R-4, one concept treated three ways. The OCCURS 40 is declared here and
    reported by this class's own descriptor - ``record_descriptor(...).occurs
    == 40`` - rather than transcribed as a constant. The twin's `Invoice-Line`
    [copybooks/slwsinv2.cob:L91] has no OCCURS at all, being a redefine of a
    single buffer. And the bridge deletes the clause textually, `==occurs 40.==
    by ==.==` [common/slinvoiceMT.cbl:L458], to spare the memory: "Using the
    first record but not the 2nd as it uses occurs 40 but to reduce Ram usage
    get rid of the occurs." [:L452-L454]. All three stand, each in its own
    source's terms.

    R-5, name collision: `Invoice-Line` names this `03` group and also an
    `01`-level redefine in the twin [copybooks/slwsinv2.cob:L91] - two
    structurally different things under one COBOL name. The class-name prefixes
    `Sil` and `Il` separate them here; in COBOL such collisions are what force
    the qualified references the posting path has to write.
    """

    COBOL_NAME: ClassVar[str] = "Invoice-Line"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L81"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Bodies.Invoice-Line"

    # 05  sil-Key.                     *> 10 bytes   [copybooks/slwsinv.cob:L82]
    sil_key: SilKey = field(metadata=_entry("SAINV-LINES-REC.IL-LINE-KEY"))

    # 05  sil-product     pic x(13).    *> +1 17/5/13 - 23
    #                                                [copybooks/slwsinv.cob:L85]
    sil_product: str = field(metadata=_entry("SAINV-LINES-REC.IL-PRODUCT"))

    # 05  sil-pa          pic xx.       *> 25        [copybooks/slwsinv.cob:L86]
    # R-4: the `xx` short form. Character length 2, literal picture text kept.
    sil_pa: str = field(metadata=_entry("SAINV-LINES-REC.IL-PA"))

    # 05  sil-qty         binary-short. *> 2 - 27    [copybooks/slwsinv.cob:L87]
    # R-4, signedness: signed binary here, `HV1-IL-QTY PIC 9(05) COMP`
    # [common/slinvoiceMT.cbl:L432], unsigned smallint in the table. Signed and
    # scale 0, therefore `int` - and it must stay `int`, because a quantity in
    # this suite is divided and the compiled program truncates the result the
    # way integer division does. A Decimal here would keep a remainder COBOL
    # discards.
    sil_qty: int = field(metadata=_entry("SAINV-LINES-REC.IL-QTY"))

    # 05  sil-type        pic x.        *> 28        [copybooks/slwsinv.cob:L88]
    sil_type: str = field(metadata=_entry("SAINV-LINES-REC.IL-TYPE"))

    # 05  sil-description pic x(32).    *> +8 17/5/13 60
    #                                                [copybooks/slwsinv.cob:L89]
    sil_description: str = field(metadata=_entry("SAINV-LINES-REC.IL-DESCRIPTION"))

    # 05  sil-net         pic s9(7)v99   comp-3.     [copybooks/slwsinv.cob:L90]
    # Usage on its own PICTURE line - no group to inherit from, unlike the
    # header's eight figures. Signed at all three layers.
    sil_net: Decimal = field(metadata=_entry("SAINV-LINES-REC.IL-NET"))

    # 05  sil-unit        pic s9(7)v99   comp-3.     [copybooks/slwsinv.cob:L91]
    sil_unit: Decimal = field(metadata=_entry("SAINV-LINES-REC.IL-UNIT"))

    # 05  sil-discount    pic 99v99      comp. *> 2  [copybooks/slwsinv.cob:L92]
    # COMP and still `Decimal`, because the scale is 2. Unsigned throughout.
    sil_discount: Decimal = field(metadata=_entry("SAINV-LINES-REC.IL-DISCOUNT"))

    # 05  sil-vat         pic s9(7)v99   comp-3. *> 18 - 77
    #                                                [copybooks/slwsinv.cob:L93]
    sil_vat: Decimal = field(metadata=_entry("SAINV-LINES-REC.IL-VAT"))

    # 05  sil-vat-code    pic 9.                     [copybooks/slwsinv.cob:L94]
    sil_vat_code: int = field(metadata=_entry("SAINV-LINES-REC.IL-VAT-CODE"))

    # 05  sil-update      pic x.                     [copybooks/slwsinv.cob:L95]
    # Carries `88 sil-analyised value "Z".` [:L96] - single case, inside a file
    # whose header condition names are dual case. R-4: the asymmetry stands.
    sil_update: str = field(metadata=_entry("SAINV-LINES-REC.IL-UPDATE"))

    #  05  sil-Back-Ordered   pic x.    [copybooks/slwsinv.cob:L97-L98]
    #       *> value space, or B for a BO item.   (the declaration spans both lines)
    # R-4, A NEW ANOMALY, and the cause is datable. This field has NO bridge host variable and
    # NO column: a case-insensitive count of "back-ordered" in common/slinvoiceMT.cbl returns 0,
    # and `SAINV-LINES-REC` ends at `IL-UPDATE` with 14 columns. The bridge still models the
    # byte as `03 filler pic x.` [common/slinvoiceMT.cbl:L377], whose comment "size 80 to here
    # -1 26/7/23 2 match slwsinv" dates it to 26/7/23, while both copybooks replaced that filler
    # with this named field on 03/03/24 [copybooks/slwsinv.cob:L14-L15],
    # [copybooks/slwsinv2.cob:L20-L21]. Neither bridge nor table was brought forward.
    # Declared anyway - R-3 cuts both ways: nothing added AND nothing removed. Whether any
    # program writes the byte and reads it back within a run, when it would live in memory and
    # never in the database, is an open question for the compiled program.
    sil_back_ordered: str = field(
        metadata=_entry("SInvoice-Bodies.sil-Back-Ordered")
    )

    # A commented-out `05  filler          pic x.  *> was pic xx.`
    # [copybooks/slwsinv.cob:L99] follows, with a bare `*>` at L100. Dead source:
    # its existence is recorded, and nothing is declared for it.


@dataclass(kw_only=True, slots=True)
class SInvoiceBodies:
    """``01  SInvoice-Bodies.`` [copybooks/slwsinv.cob:L80] - the 40-line table.

    "Working Storage For The Invoice Lines" [:L74], "80 bytes each = 3200 bytes
    (17/05/13)" [:L77], "still valid 18/01/17" [:L78].

    A tuple, not a list, because R-6 requires a deterministic shape and a fixed
    COBOL table is fixed. The OCCURS 40 count lives on the single member's
    descriptor - ``record_descriptor(SilInvoiceLine).occurs`` - and is neither
    transcribed here as a constant nor enforced by a check, since a length
    check would be validation the copybook does not contain and R-3 forbids
    adding.

    The bridge never sees this record. It strips the OCCURS and renames every
    `sil-` field to `Un-Used-Sil-` [common/slinvoiceMT.cbl:L456-L459],
    declaring its own flat line record inline instead [:L361-L377]. The lines
    still reach `SAINV-LINES-REC`, one row per line, through that inline
    record.
    """

    COBOL_NAME: ClassVar[str] = "SInvoice-Bodies"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv.cob:L80"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "SInvoice-Bodies.SInvoice-Bodies"

    # 03  Invoice-Line                    occurs 40. [copybooks/slwsinv.cob:L81]
    invoice_line: tuple[SilInvoiceLine, ...] = field(
        metadata=_entry("SInvoice-Bodies.Invoice-Line")
    )


#  copybooks/slwsinv2.cob - the second view set, and the source of the names
# "WS replacement of (File Definition) For The Invoice File" [:L3], taken from the Sales copy
# and prefixed [:L13], with lowercase values [:L14] and invoice-letter references [:L15]
# removed, reaching its present shape "from fdinv2.cob with FD removed" [:L19]. The sizing
# question at [:L25] is left standing.
# THREE 01-LEVELS OVER ONE 137-BYTE BUFFER, two of them REDEFINES: the base
# `Invoice-Record.` [:L27], then `Invoice-Header` [:L38] and `Invoice-Line`
# [:L91], each redefining it. All three are modelled, none collapsed.
# The bridge does NOT copy this file - its active copy list is `envdiv.cob`, `wsfnctn.cob`,
# `Test-Data-Flags.cob` and `slwsinv.cob` - yet every MySQL column in both tables is spelt with
# the `ih-` and `il-` prefixes declared here. That is why the plan pairs the two copybooks into
# one module, and why no key below could have come from transforming a field name.


@dataclass(kw_only=True, slots=True)
class InvoiceKey:
    """``03  Invoice-Key.`` [copybooks/slwsinv2.cob:L28] - the base view's key group.

    Ten bytes, the same two members the header view splits differently. No
    column is spelt from this view: the base view's names appear in the
    dictionary as copybook-only entries, because the table takes its names from
    the `Invoice-Header` and `Invoice-Line` redefines.
    """

    COBOL_NAME: ClassVar[str] = "Invoice-Key"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L28"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Record.Invoice-Key"

    # 05  Invoice-Nos    pic 9(8).              [copybooks/slwsinv2.cob:L29]
    invoice_nos: int = field(metadata=_entry("Invoice-Record.Invoice-Nos"))

    # 05  Item-Nos       pic 99.   *> was binary-char.
    #                                           [copybooks/slwsinv2.cob:L30]
    # R-4: declaration beats comment, and the file records the change itself -
    # "29/01/17 replaced item-nos from bin-char to pic 99." [:L18]. Zoned
    # DISPLAY at scale 0, therefore `int`.
    item_nos: int = field(metadata=_entry("Invoice-Record.Item-Nos"))


@dataclass(kw_only=True, slots=True)
class InvoiceRecord:
    """``01  Invoice-Record.`` [copybooks/slwsinv2.cob:L27] - the base buffer, 137.

    The buffer the other two views redefine. Its members sum to 8 + 2 + 7 + 4 +
    10 + 1 + 10 + 95 = 137, agreeing with the declared figure.

    R-4, structural divergence from its own redefine and from the twin file:
    this view declares a FLAT `Invoice-Customer pic x(7)` [:L31] with no
    members, where `Invoice-Header` nests `ih-nos` and `ih-check` [:L43-L44]
    and `slwsinv.cob` nests `sih-nos` and `sih-check`
    [copybooks/slwsinv.cob:L24-L25]. Interestingly the flat form is the one the
    bridge ends up with - a single `HV-IH-CUSTOMER X(7)`
    [common/slinvoiceMT.cbl:L394] - but that is a fact about the bridge,
    not a reason to prefer one view here. All three shapes are carried.

    R-4, filler casing: `Filler` at [:L33] is capital-F and sits between
    lower-case `filler` at [:L35] and [:L36]. The casing is preserved in each
    entry's own name; the attributes are numbered by declaration line because
    the COBOL names are not unique.
    """

    COBOL_NAME: ClassVar[str] = "Invoice-Record"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L27"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Record.Invoice-Record"

    # 03  Invoice-Key.                          [copybooks/slwsinv2.cob:L28]
    invoice_key: InvoiceKey = field(metadata=_entry("Invoice-Record.Invoice-Key"))

    # 03  Invoice-Customer   pic x(7).          [copybooks/slwsinv2.cob:L31]
    # Flat here; nested in both of the other two layouts. See the class
    # docstring.
    invoice_customer: str = field(
        metadata=_entry("Invoice-Record.Invoice-Customer")
    )

    # 03  Invoice-Date       binary-long.       [copybooks/slwsinv2.cob:L32]
    # Signed binary, scale 0, therefore `int`.
    invoice_date: int = field(metadata=_entry("Invoice-Record.Invoice-Date"))

    # 03  Filler             pic x(10).         [copybooks/slwsinv2.cob:L33]
    # R-4: capital F, unlike its two lower-case siblings below. Declared, never
    # dropped - a filler occupies bytes and so affects every field after it.
    filler_33: str = field(metadata=_entry("Invoice-Record.Filler"))

    # 03  Invoice-Type       pic 9.             [copybooks/slwsinv2.cob:L34]
    invoice_type: int = field(metadata=_entry("Invoice-Record.Invoice-Type"))

    # 03  filler             pic x(10).         [copybooks/slwsinv2.cob:L35]
    filler_35: str = field(metadata=_entry("Invoice-Record.filler#35"))

    # 03  filler             pic x(95).         [copybooks/slwsinv2.cob:L36]
    # The 95 bytes the header view spells out as `ih-sub-prime`.
    filler_36: str = field(metadata=_entry("Invoice-Record.filler#36"))


@dataclass(kw_only=True, slots=True)
class IhCustomer:
    """``03  ih-customer.`` [copybooks/slwsinv2.cob:L42] - the customer key group.

    Seven bytes as `x(6)` plus `9`, the nested form. Its members are the names
    the base view's flat `Invoice-Customer` [:L31] does not have, and the twin
    declares the same nesting as `sih-customer`
    [copybooks/slwsinv.cob:L23-L25].
    """

    COBOL_NAME: ClassVar[str] = "ih-customer"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L42"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-customer"

    # 05  ih-nos         pic x(6).              [copybooks/slwsinv2.cob:L43]
    ih_nos: str = field(metadata=_entry("Invoice-Header.ih-nos#43"))

    # 05  ih-check       pic 9.                 [copybooks/slwsinv2.cob:L44]
    ih_check: int = field(metadata=_entry("Invoice-Header.ih-check#44"))


@dataclass(kw_only=True, slots=True)
class IhOrderView:
    """``03  filler redefines ih-order.`` [copybooks/slwsinv2.cob:L47].

    The twin of :class:`SihOrderView`, laid over the ten bytes of `ih-order`
    [:L46] - "New changes 24/3/23 for Autogen/recurring invoices" - and
    summing to 1 + 2 + 3 + 4 = 10 bytes.

    R-4, copybook-only, same as its twin: none of the four members has a bridge
    host variable or a column, only the base `IH-ORDER char(10)`. Declared in
    full regardless. The maintainer's question about the whole overlay sits in
    the 03/03/24 header note [:L20-L23] and is quoted rather than answered:
    "Redefines of il-Order for recurring support. Needed ??" [:L22].

    Its six condition names are upper case only where the twin's are dual case -
    see :func:`condition_names_slwsinv2` - and two of them still share the
    literal "D" [:L52-L53].
    """

    COBOL_NAME: ClassVar[str] = "filler"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L47"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.filler#47"

    # 05  ih-Freq        pic x.                 [copybooks/slwsinv2.cob:L48]
    ih_freq: str = field(metadata=_entry("Invoice-Header.ih-Freq"))

    # 05  ih-Repeat      pic 99.                [copybooks/slwsinv2.cob:L55]
    ih_repeat: int = field(metadata=_entry("Invoice-Header.ih-Repeat"))

    # 05  filler         pic xxx.               [copybooks/slwsinv2.cob:L56]
    filler_56: str = field(metadata=_entry("Invoice-Header.filler#56"))

    # 05  ih-Last-Date binary-long.             [copybooks/slwsinv2.cob:L57]
    ih_last_date: int = field(metadata=_entry("Invoice-Header.ih-Last-Date"))


@dataclass(kw_only=True, slots=True)
class IhPrime:
    """``02  ih-prime.`` [copybooks/slwsinv2.cob:L39] - annotated "42 ??? bytes".

    R-4, and the question mark is the maintainer's: the annotation reads "42
    ??? bytes" here where the twin reads a plain "42 bytes"
    [copybooks/slwsinv.cob:L19]. Quoted, not answered. The members do sum to 8 +
    2 + 7 + 4 + 10 + 1 + 10 = 42.

    R-4, structural divergence: this group declares `ih-invoice` and `ih-test`
    as two separate `03` items [:L40-L41], where the twin wraps the same two
    bytes in a named group, `03 WS-Invoice-Key` [copybooks/slwsinv.cob:L20]. One
    layout has a key group and the other does not; both are carried, and the
    bridge concatenates from the twin's group because that is the file it
    copies.
    """

    COBOL_NAME: ClassVar[str] = "ih-prime"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L39"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-prime"

    # 03  ih-invoice         pic 9(8).          [copybooks/slwsinv2.cob:L40]
    ih_invoice: int = field(metadata=_entry("Invoice-Header.ih-invoice#40"))

    # 03  ih-test            pic 99.  *> was binary-char.
    #                                           [copybooks/slwsinv2.cob:L41]
    # R-4, twice over. Declaration beats comment, as always. And note what is
    # NOT here: the twin writes `pic 99 value zero.`
    # [copybooks/slwsinv.cob:L22] while this one carries no VALUE clause, so no
    # default is declared for it. Inventing one to match the twin would be
    # adding a field property the copybook does not state.
    ih_test: int = field(metadata=_entry("Invoice-Header.ih-test#41"))

    # 03  ih-customer.                          [copybooks/slwsinv2.cob:L42]
    ih_customer: IhCustomer = field(metadata=_entry("Invoice-Header.ih-customer"))

    # 03  ih-date            binary-long.       [copybooks/slwsinv2.cob:L45]
    # "For autogen next date due". The field whose name loses its trailing E at
    # the bridge - `HV-IH-DAT` [common/slinvoiceMT.cbl:L395] - and whose sign is
    # lost with it.
    ih_date: int = field(metadata=_entry("Invoice-Header.ih-date#45"))

    # 03  ih-order           pic x(10).         [copybooks/slwsinv2.cob:L46]
    ih_order: str = field(metadata=_entry("Invoice-Header.ih-order#46"))

    # 03  filler redefines ih-order.            [copybooks/slwsinv2.cob:L47]
    filler_47: IhOrderView = field(metadata=_entry("Invoice-Header.filler#47"))

    # 03  ih-type            pic 9.             [copybooks/slwsinv2.cob:L58]
    ih_type: int = field(metadata=_entry("Invoice-Header.ih-type#58"))

    # 03  ih-ref             pic x(10).         [copybooks/slwsinv2.cob:L59]
    ih_ref: str = field(metadata=_entry("Invoice-Header.ih-ref#59"))


@dataclass(kw_only=True, slots=True)
class IhFig:
    """``03  ih-fig                             comp-3.`` [copybooks/slwsinv2.cob:L62].

    GROUP-USAGE INHERITANCE, the twin of :class:`SihFig`. The group header
    carries `comp-3` and its eight children [:L63-L70] are declared `pic
    s9(7)v99` with no usage clause of their own, so all eight are packed
    decimal by inheritance and each descriptor reports ``usage == COMP-3``,
    ``usage_declared_at == GROUP`` and ``usage_inherited_from == "ih-fig"``.

    Taking usage from a child's PICTURE line would type all eight as zoned
    DISPLAY and silently change every stored figure. That is sixteen fields
    across the two view sets that depend on reading the group header, which is
    why usage is read from the dictionary and never typed into this module.
    """

    COBOL_NAME: ClassVar[str] = "ih-fig"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L62"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-fig#62"

    # 05  ih-p-c         pic s9(7)v99.          [copybooks/slwsinv2.cob:L63]
    ih_p_c: Decimal = field(metadata=_entry("Invoice-Header.ih-p-c#63"))

    # 05  ih-net         pic s9(7)v99.          [copybooks/slwsinv2.cob:L64]
    ih_net: Decimal = field(metadata=_entry("Invoice-Header.ih-net#64"))

    # 05  ih-extra       pic s9(7)v99.          [copybooks/slwsinv2.cob:L65]
    ih_extra: Decimal = field(metadata=_entry("Invoice-Header.ih-extra#65"))

    # 05  ih-carriage    pic s9(7)v99.          [copybooks/slwsinv2.cob:L66]
    ih_carriage: Decimal = field(metadata=_entry("Invoice-Header.ih-carriage#66"))

    # 05  ih-vat         pic s9(7)v99.          [copybooks/slwsinv2.cob:L67]
    ih_vat: Decimal = field(metadata=_entry("Invoice-Header.ih-vat#67"))

    # 05  ih-discount    pic s9(7)v99.          [copybooks/slwsinv2.cob:L68]
    ih_discount: Decimal = field(metadata=_entry("Invoice-Header.ih-discount#68"))

    # 05  ih-e-vat       pic s9(7)v99.          [copybooks/slwsinv2.cob:L69]
    ih_e_vat: Decimal = field(metadata=_entry("Invoice-Header.ih-e-vat#69"))

    # 05  ih-c-vat       pic s9(7)v99.          [copybooks/slwsinv2.cob:L70]
    ih_c_vat: Decimal = field(metadata=_entry("Invoice-Header.ih-c-vat#70"))


@dataclass(kw_only=True, slots=True)
class IhSubPrime:
    """``02 ih-sub-prime.`` [copybooks/slwsinv2.cob:L60] - annotated "95 ??? bytes".

    R-4 twice on one line. The group name is lower case where the twin is mixed
    case, `Sih-Sub-Prime` [copybooks/slwsinv.cob:L41], even though `ih-prime`
    and `sih-prime` are both lower case - so the casing divergence is confined
    to this one group. And the byte annotation again carries the maintainer's
    question mark, "95 ??? bytes", where the twin states a plain "95 bytes".
    The members do sum to 95.
    """

    COBOL_NAME: ClassVar[str] = "ih-sub-prime"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L60"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-sub-prime"

    # 03  ih-description     pic x(32).         [copybooks/slwsinv2.cob:L61]
    ih_description: str = field(metadata=_entry("Invoice-Header.ih-description"))

    # 03  ih-fig                             comp-3.
    #                                           [copybooks/slwsinv2.cob:L62]
    ih_fig: IhFig = field(metadata=_entry("Invoice-Header.ih-fig#62"))

    # 03  ih-status          pic x.             [copybooks/slwsinv2.cob:L71]
    # R-4: three condition names, upper case only [:L72-L74], against the twin's
    # dual-case lists [copybooks/slwsinv.cob:L53-L55], and one of them is named
    # `applied` where the twin names it `sapplied`. The file explains the case
    # difference itself - "Removed lowercase values so just using UC" [:L14] -
    # and both lists are carried exactly as each file declares them.
    ih_status: str = field(metadata=_entry("Invoice-Header.ih-status#71"))

    # 03  ih-status-P        pic x.             [copybooks/slwsinv2.cob:L75]
    ih_status_p: str = field(metadata=_entry("Invoice-Header.ih-status-P"))

    # 03  ih-status-L        pic x.             [copybooks/slwsinv2.cob:L76]
    ih_status_l: str = field(metadata=_entry("Invoice-Header.ih-status-L"))

    # 03  ih-status-C        pic x.             [copybooks/slwsinv2.cob:L77]
    ih_status_c: str = field(metadata=_entry("Invoice-Header.ih-status-C"))

    # 03  ih-status-A        pic x.             [copybooks/slwsinv2.cob:L78]
    ih_status_a: str = field(metadata=_entry("Invoice-Header.ih-status-A"))

    # 03  ih-status-I        pic x.   *> Invoice Item lines deleted  space or D
    #                                           [copybooks/slwsinv2.cob:L79]
    # The twin's comment on the same byte capitalises "Deleted"
    # [copybooks/slwsinv.cob:L60]; this one does not. Both stand. And as in the
    # twin, the byte is named -I while the value it carries is D.
    ih_status_i: str = field(metadata=_entry("Invoice-Header.ih-status-I"))

    # 03  ih-lines           binary-char.       [copybooks/slwsinv2.cob:L80]
    # R-4, column reordering: declared third from the end of the group, written
    # to the table at ordinal 29 after `IH-CR`
    # [common/slinvoiceMT.cbl:L419]. Copybook position kept. R-4, signedness:
    # signed here, unsigned tinyint in the table.
    ih_lines: int = field(metadata=_entry("Invoice-Header.ih-lines#80"))

    # 03  ih-deduct-days     binary-char.       [copybooks/slwsinv2.cob:L81]
    ih_deduct_days: int = field(
        metadata=_entry("Invoice-Header.ih-deduct-days#81")
    )

    # 03  ih-deduct-amt      pic 999v99    comp.
    #                                           [copybooks/slwsinv2.cob:L82]
    # Usage on its own PICTURE line, so no inheritance - and `Decimal` despite
    # COMP, because the scale is 2.
    ih_deduct_amt: Decimal = field(
        metadata=_entry("Invoice-Header.ih-deduct-amt#82")
    )

    # 03  ih-deduct-vat      pic 999v99    comp.
    #                                           [copybooks/slwsinv2.cob:L83]
    ih_deduct_vat: Decimal = field(
        metadata=_entry("Invoice-Header.ih-deduct-vat#83")
    )

    # 03  ih-days            binary-char.       [copybooks/slwsinv2.cob:L84]
    ih_days: int = field(metadata=_entry("Invoice-Header.ih-days#84"))

    # 03  ih-cr              binary-long.       [copybooks/slwsinv2.cob:L85]
    ih_cr: int = field(metadata=_entry("Invoice-Header.ih-cr#85"))

    # 03  ih-day-book-flag   pic x.             [copybooks/slwsinv2.cob:L86]
    # R-4: NO `value space` here, where the twin writes one
    # [copybooks/slwsinv.cob:L67]. No default is declared, deliberately. The
    # twin's default is on the twin's field and nowhere else.
    ih_day_book_flag: str = field(
        metadata=_entry("Invoice-Header.ih-day-book-flag#86")
    )

    # 03  ih-update          pic x.             [copybooks/slwsinv2.cob:L88]
    # Carries `88 ih-analyised value "Z".` [:L89] - single case here, dual case
    # in the twin. R-4: `analyised` keeps its misspelling.
    ih_update: str = field(metadata=_entry("Invoice-Header.ih-update#88"))


@dataclass(kw_only=True, slots=True)
class IhInvoiceHeader:
    """``01  Invoice-Header  redefines Invoice-Record.`` [copybooks/slwsinv2.cob:L38].

    The header view over the 137-byte base buffer - "137 bytes" as annotated,
    and 42 plus 95 as declared. It is this view's field names, prefixed `ih-`,
    that the bridge host variables and therefore the `SAINVOICE-REC` columns are
    spelt from, even though the bridge copies the other file entirely.

    Nothing here keeps this view and :class:`InvoiceRecord` in step. In COBOL a
    REDEFINES shares storage, so the two are the same bytes seen two ways; this
    module models declarations rather than a byte buffer, and adding
    synchronisation would be behaviour the copybook does not contain.
    """

    COBOL_NAME: ClassVar[str] = "Invoice-Header"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L38"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.Invoice-Header#38"

    # 02  ih-prime.          *> 42 ??? bytes    [copybooks/slwsinv2.cob:L39]
    ih_prime: IhPrime = field(metadata=_entry("Invoice-Header.ih-prime"))

    # 02 ih-sub-prime.       *> 95 ??? bytes    [copybooks/slwsinv2.cob:L60]
    ih_sub_prime: IhSubPrime = field(
        metadata=_entry("Invoice-Header.ih-sub-prime")
    )


@dataclass(kw_only=True, slots=True)
class IlInvoiceLine:
    """``01  Invoice-Line   redefines Invoice-Record.`` [copybooks/slwsinv2.cob:L91].

    The line view, annotated "*> Header." and "*> 80" on its own declaration
    line, and the source of the `il-` names the 14 `SAINV-LINES-REC` columns
    are spelt from.

    R-4, structural: its members start at level 05 directly under the `01`,
    with no `03` level at all, where the twin nests `05`/`07` beneath an
    `occurs 40` group [copybooks/slwsinv.cob:L81-L84] and the bridge declares
    its inline record flat at `03` [common/slinvoiceMT.cbl:L361-L377]. Three
    nesting depths for one 80-byte line; each is kept as its own source has it.
    There is also no key group here at all - `il-invoice` and `il-line` stand
    alone, where the twin wraps them in `sil-Key`.

    OPEN QUESTION for the compiled program. This view is documented at 80 bytes
    yet redefines a 137-byte record, leaving 57 bytes unreachable through it.
    COBOL permits a shorter REDEFINES, so the declaration is legal rather than
    broken, and the declared members do sum to 80. What the compiled program
    reads past byte 80 through this view has to be measured, not deduced, and
    is recorded in the migration's ambiguity-resolutions document.
    """

    COBOL_NAME: ClassVar[str] = "Invoice-Line"
    COBOL_SOURCE: ClassVar[str] = "copybooks/slwsinv2.cob:L91"
    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Line.Invoice-Line#91"

    # 05  il-invoice         pic 9(8).          [copybooks/slwsinv2.cob:L92]
    il_invoice: int = field(metadata=_entry("Invoice-Line.il-invoice#92"))

    # 05  il-line            pic 99.  *> was binary-char.
    #                                           [copybooks/slwsinv2.cob:L93]
    # R-4: declaration beats comment. Zoned DISPLAY at scale 0, so `int`.
    il_line: int = field(metadata=_entry("Invoice-Line.il-line#93"))

    # 05  il-product         pic x(13).   *> +1 17/5/13
    #                                           [copybooks/slwsinv2.cob:L94]
    il_product: str = field(metadata=_entry("Invoice-Line.il-product#94"))

    # 05  il-pa              pic xx.            [copybooks/slwsinv2.cob:L95]
    il_pa: str = field(metadata=_entry("Invoice-Line.il-pa#95"))

    # 05  il-qty             binary-short.      [copybooks/slwsinv2.cob:L96]
    # R-4, signedness: signed here, unsigned smallint in the table. `int` and it
    # must stay `int` - a quantity divided in this suite truncates the way
    # integer division truncates, and a Decimal would keep a remainder the
    # compiled program throws away.
    il_qty: int = field(metadata=_entry("Invoice-Line.il-qty#96"))

    # 05  il-type            pic x.             [copybooks/slwsinv2.cob:L97]
    il_type: str = field(metadata=_entry("Invoice-Line.il-type#97"))

    # 05  il-description     pic x(32).         [copybooks/slwsinv2.cob:L98]
    il_description: str = field(metadata=_entry("Invoice-Line.il-description#98"))

    # 05  il-net             pic s9(7)v99   comp-3.
    #                                           [copybooks/slwsinv2.cob:L99]
    il_net: Decimal = field(metadata=_entry("Invoice-Line.il-net#99"))

    # 05  il-unit            pic s9(7)v99   comp-3.
    #                                           [copybooks/slwsinv2.cob:L100]
    il_unit: Decimal = field(metadata=_entry("Invoice-Line.il-unit#100"))

    # 05  il-discount        pic 99v99      comp.
    #                                           [copybooks/slwsinv2.cob:L101]
    # COMP and `Decimal`: scale 2 decides it.
    il_discount: Decimal = field(metadata=_entry("Invoice-Line.il-discount#101"))

    # 05  il-vat             pic s9(7)v99   comp-3.
    #                                           [copybooks/slwsinv2.cob:L102]
    il_vat: Decimal = field(metadata=_entry("Invoice-Line.il-vat#102"))

    # 05  il-vat-code        pic 9.             [copybooks/slwsinv2.cob:L103]
    il_vat_code: int = field(metadata=_entry("Invoice-Line.il-vat-code#103"))

    # 05  il-update          pic x.             [copybooks/slwsinv2.cob:L104]
    # Carries `88 il-analyised value "Z".` [:L105].
    il_update: str = field(metadata=_entry("Invoice-Line.il-update#104"))

    # 05  il-Back-Ordered    pic x.  *> value space, or B for a BO item.
    #                                           [copybooks/slwsinv2.cob:L106]
    # R-4, the same new anomaly as its twin `sil-Back-Ordered`
    # [copybooks/slwsinv.cob:L97-L98]: NO bridge host variable and NO column.
    # `grep -inc "back-ordered" common/slinvoiceMT.cbl` returns 0, and
    # `SAINV-LINES-REC` ends at `IL-UPDATE` with 14 columns, because the bridge
    # still models this byte as `03 filler pic x.`
    # [common/slinvoiceMT.cbl:L377] - "size 80 to here -1 26/7/23 2 match
    # slwsinv" - while both copybooks named it on 03/03/24
    # [copybooks/slwsinv2.cob:L20-L21]. Declared anyway: R-3 forbids removing a
    # declared field as firmly as adding an undeclared one.
    il_back_ordered: str = field(metadata=_entry("Invoice-Line.il-Back-Ordered"))

    # A commented-out `05  filler          pic x.  *> was pic xx.`
    # [copybooks/slwsinv2.cob:L107] follows, with a bare `*>` at L108. Dead
    # source, exactly as in the twin: recorded here, declared nowhere. The file
    # closes noting "No Changes to Record size." [:L23].


__all__: Final[tuple[str, ...]] = (
    "BRIDGE",
    "COPYBOOK_SLWSINV",
    "COPYBOOK_SLWSINV2",
    "ENTITY_FACADE",
    "HANDLER",
    "HEADER_TABLE",
    "IhCustomer",
    "IhFig",
    "IhInvoiceHeader",
    "IhOrderView",
    "IhPrime",
    "IhSubPrime",
    "IlInvoiceLine",
    "InvoiceKey",
    "InvoiceRecord",
    "LINES_TABLE",
    "SInvoiceBodies",
    "SInvoiceHeader",
    "SihCustomer",
    "SihFig",
    "SihOrderView",
    "SihPrime",
    "SihSubPrime",
    "SilInvoiceLine",
    "SilKey",
    "WsInvoiceKey",
    "cite_for",
    "condition_names_for",
    "condition_names_slwsinv",
    "condition_names_slwsinv2",
    "descriptor_for",
    "dictionary_key_for",
    "dictionary_keys_for",
    "drift_for",
    "record_descriptor",
    "record_dictionary_key",
)
