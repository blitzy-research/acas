r"""Purchase Open-Item (OTM5) record layout - ``PUITM5-REC``.

The purchase ledger's unpaid-item register. ``pl060`` writes and applies these
rows; ``pl100`` clears them and reads ``OI-Date`` against ``OI-Date-Cleared``
to drive the payment-days average at ``[purchase/pl100.cbl:L498]`` and
``[purchase/pl100.cbl:L502]``. Both of those fields are ``binary-long``, so
that average is INTEGER arithmetic - see "TYPE DISCIPLINE" below, because
typing either of them as a scaled quantity would change the average and
silently repair three registered anomalies.

This module declares data layout and nothing else. It performs no arithmetic,
opens no connection, reads no file at import, and holds no business logic.

THE FIVE FROZEN SOURCES
-----------------------
Every one is READ-ONLY specification. Nothing here modifies, reformats,
relocates or regenerates any of them, and nothing here executes any of them.

  ``copybooks/plwsoi5B.cob``   21 lines. The key-only view. Declares the
                               113-byte buffer and a short view over it, and
                               its ``COPY`` of the body is COMMENTED OUT.
  ``copybooks/plwsoi5C.cob``   21 lines. The same file with that ``COPY``
                               ACTIVE, so it carries the full field set too.
  ``copybooks/plwsoi.cob``     63 lines. The body - the 29-field layout.
  ``common/otm5MT.cbl``        2219 lines. The one-way bridge. The Agent
                               Action Plan designates the bridge as the data
                               dictionary for this migration, which is why
                               field metadata here is looked up from the
                               generated artifact rather than transcribed.
  ``mysql/ACASDB.sql``         The frozen schema. ``PUITM5-REC`` is declared
                               at ``[mysql/ACASDB.sql:L596]`` with 29 columns
                               at ``L597-L625``, all ``NOT NULL``, primary key
                               ``OI5-KEY char(15)`` at ``L626``, and
                               ``ENGINE=InnoDB DEFAULT CHARSET=utf8mb3
                               COLLATE=utf8mb3_general_ci`` at ``L627``.

Entity facade OTM5, handler ``acas029``, bridge ``otm5MT``, table
``PUITM5-REC`` - the spine row from Agent Action Plan section 0.2.1.1.

WHY THE PLAN NAMES TWO COPYBOOKS, AND WHY BOTH ARE PUBLISHED HERE
-----------------------------------------------------------------
``plwsoi5B.cob`` and ``plwsoi5C.cob`` are 21-line near-twins that differ in
exactly two ways, and ``diff`` shows both:

  (i)  One space of indentation on L12. ``plwsoi5B.cob:L12`` writes
       ``01  Open-Item-Record-5   redefines WS-OTM5-Record.`` with THREE
       spaces; ``plwsoi5C.cob:L12`` writes the same line with FOUR.

  (ii) The two-line ``COPY`` at L19-L20 is commented out in 5B and live in
       5C - and 5B's commented form is malformed. Verbatim,
       ``[copybooks/plwsoi5B.cob:L19-L20]``::

           *> copy "    plwsoi.cob" replacing ==OI-Header==
           *>                     by ==OI-Header redefines WS-OTM5-Record==.

       FOUR SPACES sit inside the quoted filename, so the statement would
       name a file that does not exist if it were ever made live again.
       ``[copybooks/plwsoi5C.cob:L19-L20]`` carries the same statement with a
       clean filename and no comment marker.

So 5B is a strict subset of 5C, reached by commenting out two lines. They are
not alternatives in any semantic sense. Both are live in the frozen tree:
``[purchase/pl060.cbl:L147]`` copies 5B, so ``pl060`` cannot name a single
``OI-*`` field, while ``[purchase/pl100.cbl:L213]`` copies 5C and therefore
sees the whole body. Fourteen programs copy one or the other. Neither variant
may be dropped, and this module publishes both shapes: ``WsOtm5Record`` plus
``OpenItemRecord5`` for the 5B/5C short view, and ``OiHeader`` for the body.

WHERE THE ``OI5-`` COLUMN PREFIX COMES FROM
-------------------------------------------
Every column and every host variable is prefixed ``OI5-``, while every field
in ``plwsoi.cob`` is prefixed ``OI-``. The prefix is NOT invented by the
bridge - ``grep -n "plwsoi5" common/otm5MT.cbl`` returns nothing, so the
bridge never sees those files. The prefix comes from the two plan-named
copybooks, which declare ``03 oi5-key.`` ``[copybooks/plwsoi5B.cob:L13]``,
``05 oi5-supplier pic x(7).`` ``[:L14]``, ``05 oi5-invoice PIC 9(8).``
``[:L15]`` and ``03 oi5-date binary-long.`` ``[:L16]``.

That is why the column is ``OI5-SUPPLIER`` and not ``OI5-CUSTOMER``, and why
``oi5-date`` lands as ``OI5-DAT``. The generated dictionary carries the split
provenance untouched and it is visible per key: the copybook side of
``PUITM5-REC.OI5-KEY`` is ``copybooks/plwsoi5B.cob:L13`` while the copybook
side of ``PUITM5-REC.OI5-SUPPLIER`` is ``copybooks/plwsoi.cob:L15``. One
table, two copybook files feeding it.

PRACTICAL CONSEQUENCE, AND THE ONE MISTAKE NOT TO MAKE HERE: a dictionary key
is never built by upper-casing a copybook field name. Upper-casing ``OI-Net``
yields ``OI-NET``, which does not exist. The entry is ``PUITM5-REC.OI5-NET``.
Every key used below was obtained by walking ``loader.entries_for_table`` and
``loader.entries_for_copybook_file`` and reading each entry's copybook name.

``WS-OTM5-Record`` MEANS TWO INCOMPATIBLE THINGS
-----------------------------------------------
The plan-named copybooks and the bridge use one identifier for two different
data items, and the difference is the ``replacing`` form each writes.

``[copybooks/plwsoi5C.cob:L19-L20]`` KEEPS the name and ADDS a redefines::

     copy "plwsoi.cob" replacing ==OI-Header==
                         by ==OI-Header redefines WS-OTM5-Record==.

``[common/otm5MT.cbl:L348-L349]`` RENAMES outright, with no redefines::

     copy "plwsoi.cob" replacing OI-Header
                   by WS-OTM5-Record.

Therefore ``WS-OTM5-Record`` is an ELEMENTARY ``pic x(113)`` in
``[copybooks/plwsoi5B.cob:L10]`` and ``[copybooks/plwsoi5C.cob:L10]``, and is
the FULL 29-FIELD GROUP inside the bridge after L349. Both files feed this
module. Neither meaning is folded into the other: ``WsOtm5Record`` models the
elementary buffer as declared, and ``OiHeader`` models the field set.

THE ``OI-Type`` DOMAIN BLOCK - DOCUMENTATION, NEVER A CHECK
-----------------------------------------------------------
``[copybooks/plwsoi.cob:L25-L35]`` documents the type domain, verbatim::

    *>                              ***********************************
    *>                              * 1  =  Receipt                   *
    *>                              * 2  =  Account Invoice           *
    *>                              * 3  =  Cr. Note                  *
    *>                              * 4  =  Proforma                  *
    *>                              * 5  =  Payment                   *
    *>                              * 6  =  Journal-Unapplied Cash    *
    *>                              * 7  =  Journal Type B (Not Used) *
    *>                              * 9  =  Old Payments              *
    *>                              ***********************************

The block SKIPS 8 - it lists 1 to 7 and then 9. The COBOL declares no
condition name at all on ``OI-Type``, so this stays prose: no enum, no lookup
table, no membership test, no predicate. R-3 forbids adding a check the
frozen source does not declare, and R-4 forbids tidying the gap at 8.

BYTE ARITHMETIC - REPORTED, NOT SETTLED
---------------------------------------
The plan-named copybooks declare 113 bytes at ``[copybooks/plwsoi5B.cob:L4]``
(``*>       Rec size 113 Bytes.                *``) and their own short view
sums to exactly that: 7 + 8 + 4 + 94 = 113. ``plwsoi.cob``'s header records
the change at ``[copybooks/plwsoi.cob:L6-L9]`` - ``109 bytes 26/03/09``, then
``24/04/17 VBC changed size to 113 from 109 after changing Inv from L-bin to
9(8)``.

Summing the body's own storage widths, taken from each field's dictionary
entry rather than from its digit count, gives:

    6 + 1 + 8            = 15   OI-Nos, OI-Check, OI-Invoice   (OI-Key)
    + 4                  = 19   OI-Date            binary-long
    + 4 + 2              = 25   OI-B-Nos, OI-B-Item      under COMP
    + 1                  = 26   OI-Type
    + 10 + 10            = 46   OI-ref, OI-order
    + 1 + 1              = 48   OI-hold-flag, OI-unapl
    + 9 x 5              = 93   the nine COMP-3 money fields
    + 1                  = 94   OI-Status
    + 1                  = 95   OI-Deduct-Days     binary-char
    + 4 + 4              = 103  OI-Deduct-Amt, OI-Deduct-Vat  s999v99 comp
    + 1                  = 104  OI-Days            binary-char
    + 4                  = 108  OI-CR              binary-long
    + 1                  = 109  OI-Applied
    + 4                  = 113  OI-Date-Cleared    binary-long

``OI-Approp`` REDEFINES ``OI-Net`` and so contributes zero. ``OI-Customer``
and ``OI-Supplier`` span the same seven bytes. The field sum is 113 and the
declaration says 113, and the running total at ``OI-Applied`` is 109 - which
arithmetically corroborates the maintainer's own 109-to-113 note, since the
invoice field's move from a four-byte binary to an eight-digit zoned item is
exactly the missing four bytes.

Those figures are reported and nothing is inferred from them. No record-length
constant is declared here, in line with the precedent set by the 96-versus-98
batch-record contradiction, which Agent Action Plan section 0.6.8 makes a
question for the compiled program rather than a question for a reader.

TYPE DISCIPLINE (R-2) - THE TWO-DIRECTION RULE
----------------------------------------------
Three carriers only, and no binary floating-point type anywhere, in
computation, in storage or in transport:

    ``Decimal``   a numeric item whose scale is greater than zero. The nine
                  ``pic s9(7)v99`` money fields under the COMP-3 group
                  header, plus ``OI-Deduct-Amt`` and ``OI-Deduct-Vat``.
    ``int``       a numeric item whose scale is zero. The whole binary family
                  - ``OI-Date``, ``OI-Deduct-Days``, ``OI-Days``, ``OI-CR``,
                  ``OI-Date-Cleared`` - plus the zoned ``Pic 9(n)`` items and
                  both children of the COMP group header.
    ``str``       every ``pic x(n)`` item, and the elementary 113-byte buffer.

The rule runs in BOTH directions and "COMP means int" is false. ``OI-B-Nos``
is ``COMP`` and is ``int`` because its scale is zero; ``OI-Deduct-Amt`` is
also ``COMP`` and is ``Decimal`` because its scale is two. Getting either
direction wrong corrupts every stored value in that field.

The integer direction is load-bearing beyond storage. Agent Action Plan
section 0.6.1 records that for binary-family fields "truncation on divide is
integer truncation, which is exactly what makes the moving-average defect
reproducible". ``OI-Date`` and ``OI-Date-Cleared`` are exactly such fields and
their difference feeds the purchase payment-days average at
``[purchase/pl100.cbl:L498]`` and ``[purchase/pl100.cbl:L502]``.

GROUP-USAGE INHERITANCE - TWELVE FIELDS, TWO GROUP HEADERS
----------------------------------------------------------
``[copybooks/plwsoi.cob:L20]`` writes ``03  OI-Batch  Comp.`` and its two
children at L21-L22 carry no usage clause of their own.
``[copybooks/plwsoi.cob:L41]`` writes ``03  filler  comp-3.`` - an UNNAMED
group - and its ten children at L42-L52 likewise carry none.

Twelve fields therefore take their storage class from a group header. Reading
usage off the PICTURE line alone would type all twelve as zoned display and
every stored value would be wrong. Each of the twelve reports
``usage_declared_at == UsageDeclaredAt.GROUP`` with ``usage_inherited_from``
naming ``"OI-Batch"`` or ``"filler"`` - and the second of those names a
FILLER, which is carried as declared rather than replaced with an invented
name.

THE OPPOSITE CASE, in this same layout: ``OI-Deduct-Amt`` and
``OI-Deduct-Vat`` at ``[copybooks/plwsoi.cob:L57-L58]`` write ``comp`` on
their own PICTURE line, so they report ``usage_declared_at ==
UsageDeclaredAt.FIELD`` and ``usage_inherited_from is None``.

Note the spelling drift while reading those lines: the group headers write
``Comp.`` with a capital C at L20 but ``comp-3.`` in lower case at L41, and
the two deduction fields write lower-case ``comp``. Same usage, three
spellings, all preserved.

SIGNEDNESS DRIFT IS PER-BRIDGE, NOT PER-TYPE
--------------------------------------------
This table is direct evidence for Agent Action Plan section 0.6.2, which
states that "the drift is specific rather than systemic and must be handled
field by field from the dictionary". Three fields KEEP their sign here from
declarations that lose it in the two invoice bridges, and four LOSE it here:

    SIGN KEPT at all three layers
      OI-CR           ``binary-long``    -> ``S9(10) COMP``       -> ``int(8)``
                      ``[copybooks/plwsoi.cob:L60]``, ``[common/otm5MT.cbl:L330]``
      OI-Deduct-Amt   ``s999v99 comp``   -> ``S9(03)V9(02) COMP`` -> ``decimal(5,2)``
      OI-Deduct-Vat   ``s999v99 comp``   -> ``S9(03)V9(02) COMP`` -> ``decimal(5,2)``
      plus all nine COMP-3 money fields -> ``S9(07)V9(02) COMP``  -> ``decimal(9,2)``

    SIGN LOST at the bridge - four sites, all binary family
      OI-Date         ``Binary-long``    -> ``9(10) COMP``  -> ``int(8) unsigned``
      OI-Deduct-Days  ``binary-char``    -> ``9(03) COMP``  -> ``tinyint(3) unsigned``
      OI-Days         ``binary-char``    -> ``9(03) COMP``  -> ``tinyint(3) unsigned``
      OI-Date-Cleared ``binary-long``    -> ``9(10) COMP``  -> ``int(8) unsigned``

The identically-declared ``ih-cr binary-long`` becomes an UNSIGNED host
variable and an unsigned column in the invoice bridges. So no rule of the form
"binary-long always loses its sign" exists, and none is applied here.

Section 0.6.2 also records that "a negative value computed in COBOL loses its
sign AT THE BRIDGE, not at the database - so the Python data-access layer must
reproduce the bridge's conversion". Reproducing it is
``acas_posting/dal/acas029_otm5.py``'s job, never this module's. Every
descriptor below reports the COPYBOOK view - signed where the copybook says
signed - and offers the three-layer disagreement untouched through
``loader.drift_for(key)``. No descriptor here blends layers, widens a field to
a column width, or retypes a numeric item as character to match a column.

TYPE-CLASS DRIFT NUMERIC TO CHARACTER - FOUR SITES
--------------------------------------------------
    OI-Type    ``pic 9`` ``[copybooks/plwsoi.cob:L23]`` -> ``X(1)`` -> ``char(1)``
    OI-Status  ``pic 9`` ``[copybooks/plwsoi.cob:L53]`` -> ``X(1)`` -> ``char(1)``
    OI-B-Nos   ``Pic 9(5)`` under COMP        -> ``X(5)`` -> ``char(5)``
    OI-B-Item  ``Pic 999``  under COMP        -> ``X(3)`` -> ``char(3)``

All four are declared ``int`` below, because the copybook view is numeric.
``OI-Status`` is the sharpest of them: it is ``pic 9`` carrying two condition
names with NUMERIC values yet lands in a ``char(1)`` column.

Two further drifts of the same family: ``OI-Invoice`` is ``Pic 9(8)`` zoned
display with eight digits ``[copybooks/plwsoi.cob:L18]`` and becomes a
ten-digit binary host variable ``[common/otm5MT.cbl:L306]``; the descriptor
reports eight digits and zoned display. And ``oi5-date`` / ``OI-Date`` becomes
``OI5-DAT`` - the trailing E dropped ``[common/otm5MT.cbl:L307]`` - while
``OI-Date-Cleared`` keeps its full name ``[common/otm5MT.cbl:L332]``, so the
truncation is a one-off and not a general rule.

``OI-Customer`` HAS NO HOST VARIABLE AND NO COLUMN
--------------------------------------------------
``[copybooks/plwsoi.cob:L14]`` declares ``05  OI-Customer.`` wrapping
``07  OI-Supplier.`` at L15, which wraps the two 09-level children. The outer
and inner groups span IDENTICAL bytes - 6 + 1 = 7 - so the nesting is
redundant, four levels deep for a seven-byte item.

The bridge loads its host variable from the INNER group.
``[common/otm5MT.cbl:L1350-L1351]``, verbatim::

         move     OI-Supplier to HV-OI5-SUPPLIER
                                 WS-Temp-Ed-Supplier.

``OI-Customer`` is moved nowhere and has no column. Its two grandchildren
``OI-Nos`` and ``OI-Check`` have no columns either, for the same reason - the
bridge takes the seven-byte group whole. All three are declared here anyway.
R-3 cuts both ways: nothing added AND nothing removed.

``OI-Approp`` SURVIVES ONLY AS A COLUMN COMMENT
-----------------------------------------------
``grep -inc "approp" common/otm5MT.cbl`` returns 0. The field exists in the
copybook, across two physical lines forming one declaration,
``[copybooks/plwsoi.cob:L44-L45]``::

         05  OI-Approp redefines OI-Net
                         pic s9(7)v99.

and the schema records the relationship only as prose on the base field's
column: ``OI5-NET decimal(9,2) NOT NULL COMMENT 'Also called Approp'`` at
``[mysql/ACASDB.sql:L610]``. It is declared below as a redefine view over
``oi_net``, with ``redefines == "OI-Net"`` verbatim.

TRIPLE MATERIALISATION OF ``OI-Batch``
--------------------------------------
``[copybooks/plwsoi.cob:L20-L22]`` declares one group and two children. The
bridge produces THREE host variables ``[common/otm5MT.cbl:L308-L310]`` and the
schema THREE columns - the group gets a column of its own alongside both of
its children, and all three become CHARACTER although the children are
numeric under an inherited COMP:

    ``OI5-BATCH char(8)``
    ``OI5-BATCH-NOS char(5) COMMENT 'Batch content'``     ``[mysql/ACASDB.sql:L602]``
    ``OI5-BATCH-ITEM char(3) COMMENT 'Batch content'``    ``[mysql/ACASDB.sql:L603]``

The group's column is DERIVED rather than moved. ``[common/otm5MT.cbl:L1354-
L1358]`` sends each child to its own host variable and to a bridge-internal
edit field, then sends the eight-digit redefines view of that edit group to
``HV-OI5-BATCH`` - the edit group being declared at
``[common/otm5MT.cbl:L238-L242]``, where a ``pic 9(8)`` redefines supplies the
numeric rendering that a ``char(8)`` column receives.

Those bridge-internal edit fields are NOT modelled here; reproducing the
derivation belongs to ``acas_posting/dal/acas029_otm5.py``. The descriptors
below report the copybook view - the group with its own usage, and the two
children as numeric with their inheritance recorded.

The composite key is materialised the same way, twice over rather than three
times: ``oi5-key`` becomes ``OI5-KEY char(15) COMMENT 'Supplier, Invoice'``
``[mysql/ACASDB.sql:L597]`` while both members also become columns of their
own. Its host variable is likewise derived through a bridge-internal edit
group ``[common/otm5MT.cbl:L233-L236]``, which itself replicates the
copybook's redundant one-child nesting and drifts in casing within four lines.
Also bridge-internal, also not modelled here.

TWO WRITE-ONLY HOST VARIABLES
-----------------------------
The load paragraph ``[common/otm5MT.cbl:L1338-L1385]`` loads all 29 host
variables, including ``HV-OI5-KEY`` at L1352 and ``HV-OI5-BATCH`` at L1358.
The unload paragraph ``[common/otm5MT.cbl:L1387-L1425]`` opens with
``initialize WS-OTM5-Record.`` and then moves only 27 of them back - counted
mechanically, 27 moves naming 27 distinct host variables. ``HV-OI5-KEY`` and
``HV-OI5-BATCH`` are moved nowhere.

Both are therefore write-only: loaded on a write, never unloaded on a read. If
the stored ``OI5-KEY`` or ``OI5-BATCH`` ever diverged from the member columns
they are built from, the divergence would be invisible on read-back. This is
the inverse of the never-LOADED ``HV-POST-RRN`` at
``[common/glpostingMT.cbl:L282]`` - here a never-UNLOADED pair.

Two related oddities in the same two paragraphs. The unload order differs from
the load order: the load runs INVOICE, SUPPLIER, KEY, BATCH-NOS, BATCH-ITEM,
BATCH, DAT, TYPE, while the unload runs INVOICE, SUPPLIER, DAT, BATCH-NOS,
BATCH-ITEM, TYPE. And because ``initialize WS-OTM5-Record`` clears the whole
renamed group, ``OI-Approp`` is populated IMPLICITLY by the move into
``OI-Net``, the two sharing storage.

A COMMENT DESCRIBING A SITUATION THAT DOES NOT EXIST
----------------------------------------------------
Immediately above the bridge's ``COPY``, ``[common/otm5MT.cbl:L345-L346]``
reads, verbatim::

    *>  Using the first record but not the 2nd as it uses occurs 40 but
    *>   to reduce Ram usage get rid of the occurs, hopefully.

``grep -in "occurs" copybooks/plwsoi.cob`` returns nothing, and the bridge's
``replacing`` clause strips nothing. The comment is residue copy-pasted from
the invoice bridge at ``[common/plinvoiceMT.cbl:L452-L453]``. There is no
``OCCURS`` anywhere in this layout and none is introduced below.

FIELD-NAME COLLISIONS ACROSS THE TWO OPEN-ITEM COPYBOOKS
--------------------------------------------------------
Registered anomaly 21 is the field-name collision that forces the general
ledger posting path to write qualified references at
``[general/gl070.cbl:L497]``, ``[:L521]`` and ``[:L525]``. This layout
contributes a severe case: EVERY ``OI-*`` name in ``copybooks/plwsoi.cob``
also appears in the sales open-item copybook ``copybooks/slwsoi.cob`` -
``OI-Header``, ``OI-Key``, ``OI-Customer``, ``OI-Nos``, ``OI-Check``,
``OI-Invoice``, ``OI-Date``, ``OI-Batch``, ``OI-B-Nos``, ``OI-B-Item``,
``OI-Type``, ``OI-hold-flag``, ``OI-unapl``, all ten money fields,
``OI-Status``, ``S-Open``, ``S-Closed``, ``OI-Deduct-Days``,
``OI-Deduct-Amt``, ``OI-Deduct-Vat``, ``OI-Days``, ``OI-CR``, ``OI-Applied``
and ``OI-Date-Cleared``. Any program copying both would collide on all of
them.

The Python module namespace removes the collision for free, but the collision
is recorded rather than left implicit, because it has a mechanical consequence
for anyone looking a field up here. ``loader.entries_for_copybook_record
("OI-Header")`` returns 69 entries - 35 from ``copybooks/plwsoi.cob`` and 34
from ``copybooks/slwsoi.cob`` - because BOTH copybooks declare an
``01 OI-Header``. The generated artifact separates them by appending the
declaration line, giving ``OI-Header#12`` here against ``OI-Header#8`` for
sales, ``OI-Approp#44`` against ``#38``, ``OI-Nos#16`` against ``#11``,
``OI-Check#17`` against ``#12`` and ``filler#41`` against ``filler#14`` and
``filler#35`` - and it separates ``OI-Key`` here from ``OI-key`` for sales BY
CASE ALONE. Every key used below is therefore written out in full rather than
looked up by record name.

SALES AND PURCHASE ARE GENUINELY DIFFERENT SHAPES
-------------------------------------------------
The sales open-item layout is not a template for this one and nothing here is
shared with it, imported from it, aliased to it or derived from it. Eight
divergences were checked in the frozen source and every one must survive
independently:

  1. Sales declares ``03 OI-Description pic x(25).`` and has no reference or
     order field. This layout has NO such field and declares
     ``03 OI-ref pic x(10).`` ``[copybooks/plwsoi.cob:L36]`` and
     ``03 OI-order pic x(10).`` ``[:L37]`` instead.
  2. The sales key nests three levels; this one nests four, through the
     redundant ``OI-Customer`` / ``OI-Supplier`` pair.
  3. Sales declares no condition name on its hold flag; this one declares
     ``88 payment-held value "H".`` ``[copybooks/plwsoi.cob:L39]``.
  4. Sales writes ``OI-Cr`` in mixed case; this one writes ``OI-CR`` in upper
     case ``[copybooks/plwsoi.cob:L60]``.
  5. Sales puts its date field inside an unnamed ``02 filler.`` group; here
     ``OI-Date`` sits at ``03`` level directly under ``OI-Header``
     ``[copybooks/plwsoi.cob:L19]`` and there is no outer filler group at all.
  6. The sales record is 118 bytes; this one is 113.
  7. Sales writes its batch group header as ``comp.`` in lower case; this one
     writes ``Comp.`` with a capital C ``[copybooks/plwsoi.cob:L20]``.
  8. The type domain prose differs - sales writes ``2 = Account`` and
     ``4 = Proforma (Not used)`` where this one writes ``2 = Account
     Invoice`` and ``4 = Proforma``.

The two tables differ too: 29 columns here against 28 for the sales open item,
with ``OI5-REF``, ``OI5-ORDER`` and ``OI5-SUPPLIER`` present only here and the
customer and item-text columns present only there.

CONDITION NAMES ARE PUBLISHED AS DATA
-------------------------------------
Exactly three ``88`` levels exist in this layout, and ``condition_names()``
publishes all three in declaration order with their declared values and
locators. Their values are carried as STRINGS in the form the COBOL writes
them - the figurative constant at ``[copybooks/plwsoi.cob:L54]`` stays the
word it is written as and is never turned into a digit, and the alphanumeric
literal at ``[copybooks/plwsoi.cob:L39]`` keeps the quotation marks that are
part of its declared form.

No predicate is built here. Agent Action Plan section 0.4.1.4 assigns
predicate construction to ``acas_posting/cobol/condition_names.py``, and
importing that module from here would be a layering violation.

NO DEFAULT VALUES ARE SUPPLIED
------------------------------
Not one of the 29 fields carries a ``VALUE`` clause in either copybook, so
there is no declared initial content for this module to publish, and every
dataclass field below is required. Supplying a default would be adding state
the frozen source does not declare, which R-3 forbids.

The ``initialize`` statements that do exist are the BRIDGE's, on the BRIDGE's
own data - ``initialize TD-PUITM5-REC.`` at ``[common/otm5MT.cbl:L1346]`` and
``initialize WS-OTM5-Record.`` at ``[common/otm5MT.cbl:L1393]``. Agent Action
Plan section 0.6.2 explains what they buy: "each load paragraph begins by
initialising the host-variable group, so unset fields become zero or space
rather than SQL NULL", which is why every column in this table is declared
``NOT NULL``. Reproducing that is the handler module's job at the bridge
boundary. A caller that needs those values can obtain each one from the
field's own descriptor - ``descriptor.store(0)`` yields a zero at the declared
scale and ``descriptor.store("")`` yields spaces at the declared width - so
even there nothing has to be typed by hand.

HOW TO READ A FIELD'S METADATA
------------------------------
No picture clause, digit count, scale, sign position or storage class is
written by hand anywhere in this module. Each dataclass field carries its
dictionary key, and ``descriptors_of`` turns the keys of one class into
descriptors. Taking ``descriptors_of`` and ``OiHeader`` from this module::

    for attribute, d in descriptors_of(OiHeader).items():
        print(attribute, d.name, d.usage, d.python_storage, d.cite())

Where only one field is wanted the key alone is enough - lift it out of the
field's metadata and hand it to ``FieldDescriptor.from_dictionary_key``, which
``acas_posting.cobol.field`` publishes::

    keys = {f.name: f.metadata["dictionary_key"]
            for f in dataclasses.fields(OiHeader)}
    d = FieldDescriptor.from_dictionary_key(keys["oi_cr"])

``FieldDescriptor.from_dictionary_key`` is memoised and reads the generated
artifact lazily, so importing this module performs no I/O of any kind: nothing
is read at import, no clock is consulted, no environment is inspected and no
directory is walked. ``d.cite()`` produces the three-locator provenance line
that R-5 rests on - for example, for the credit field::

    PUITM5-REC.OI5-CR  copybook=copybooks/plwsoi.cob:L60
                       bridge=common/otm5MT.cbl:L330
                       column=mysql/ACASDB.sql:L623

and for a field the bridge never sees::

    OI-Header.OI-Approp#44  copybook=copybooks/plwsoi.cob:L44
                            bridge=absent  column=absent

``cite()`` is surfaced, never reimplemented. Whole-record access is available
through ``FieldDescriptor``'s own module-level helpers,
``descriptors_for_table("PUITM5-REC")`` and
``descriptors_for_copybook_record``, and the three-layer disagreement for any
key through ``loader.drift_for(key)``.

Each field's metadata also carries ``cobol_name`` - the declared identifier
verbatim, case and hyphens intact. That is a name, not storage metadata, and
it is recorded because the collision described above makes names the thing a
reader most needs to see beside each attribute.

LAYERING - THIS IS A LEAF MODULE
--------------------------------
Agent Action Plan section 0.4.3 permits ``records/*.py`` to import
``cobol.field`` and ``dictionary.loader`` and nothing else, which "keeps the
record layer a leaf". The third import below, ``dictionary.model``, supplies
the ``ConditionName`` type that the generated artifact's own entries are
instances of; taking it from there rather than declaring a competing copy is
the same architectural edge ``acas_posting/cobol/field.py`` documents for
itself.

Not imported, and none of it may be: ``acas_posting.dal`` in any part,
``acas_posting.programs``, ``acas_posting.cli``, ``acas_posting.clock``,
``acas_posting.dates``, ``acas_posting.workfiles``, the remaining
``acas_posting.cobol`` modules including ``condition_names``,
``acas_posting.dictionary.generate``, ``harness`` in any part, and any other
module in ``acas_posting.records`` - the sales open-item layout most of all.
Section 0.4.3 gives the concrete reason: the arithmetic test tier "imports
only ``cobol`` and ``records`` and touches no database, so it runs anywhere",
and one forbidden import would put a database driver in that tier.

THE ANOMALY REGISTER FOR THIS LAYOUT
------------------------------------
Every item below is REPRODUCED, never fixed. A defect reproduced is correct; a
defect fixed is a failure. Each has a locator comment at its site in the code,
and the register of all of them is ``docs/migration/anomaly-log.md``.

   1. The two plan-named copybooks are 21-line near-twins differing only by a
      commented-out ``COPY`` whose quoted filename contains four spaces, and
      by one space of indentation. ``[copybooks/plwsoi5B.cob:L12,L19-L20]``
      against ``[copybooks/plwsoi5C.cob:L12,L19-L20]``.
   2. ``HV-OI5-KEY`` and ``HV-OI5-BATCH`` are write-only host variables -
      loaded at ``[common/otm5MT.cbl:L1352]`` and ``[:L1358]``, never unloaded
      ``[:L1387-L1425]``.
   3. A copy-pasted comment describes an ``occurs 40`` that does not exist.
      ``[common/otm5MT.cbl:L345-L346]``.
   4. ``OI-Customer`` has no host variable and no column, proven from the load
      paragraph. ``[copybooks/plwsoi.cob:L14]`` against
      ``[common/otm5MT.cbl:L1350-L1351]``. Its two grandchildren ``OI-Nos``
      and ``OI-Check`` have none either.
   5. ``WS-OTM5-Record`` names two incompatible items - an elementary
      ``pic x(113)`` at ``[copybooks/plwsoi5C.cob:L10]`` and the full
      29-field group after ``[common/otm5MT.cbl:L348-L349]``.
   6. ``OI-Approp`` has no host variable; its existence survives only as a
      column comment. ``[copybooks/plwsoi.cob:L44-L45]``,
      ``[mysql/ACASDB.sql:L610]``.
   7. Triple materialisation of ``OI-Batch`` with numeric-to-character drift
      on all three, the group column derived through a bridge-internal
      redefines. ``[copybooks/plwsoi.cob:L20-L22]``,
      ``[common/otm5MT.cbl:L308-L310]``, ``[:L238-L242]``, ``[:L1354-L1358]``.
   8. Signedness drift is per-bridge, not per-type - ``OI-CR`` keeps its sign
      here while an identically-declared field loses it in the invoice
      bridges. ``[common/otm5MT.cbl:L330]``.
   9. Four signedness narrowings, surfaced untouched: ``OI-Date``,
      ``OI-Deduct-Days``, ``OI-Days``, ``OI-Date-Cleared``.
  10. Four numeric-to-character drifts: ``OI-Type``, ``OI-Status``,
      ``OI-B-Nos``, ``OI-B-Item``.
  11. Name truncation ``oi5-date`` and ``OI-Date`` to ``OI5-DAT``
      ``[common/otm5MT.cbl:L307]`` while ``OI-Date-Cleared`` is not truncated
      ``[:L332]``.
  12. The systematic ``OI-*`` to ``OI5-*`` prefix rename across all 29
      columns, sourced from the plan-named copybooks' own ``oi5-*`` names.
  13. An unnamed FILLER group carries the storage class for ten money fields
      ``[copybooks/plwsoi.cob:L41]``, with no outer filler group above the
      date field, unlike the sales layout.
  14. Four-level key nesting with a redundant one-child group
      ``[copybooks/plwsoi.cob:L13-L17]``, replicated inside the bridge's own
      edit group ``[common/otm5MT.cbl:L233-L236]``.
  15. ``88 payment-held value "H".`` exists here and not in the sales layout
      ``[copybooks/plwsoi.cob:L39]``.
  16. ``OI-CR`` in upper case ``[copybooks/plwsoi.cob:L60]``; ``OI-ref``,
      ``OI-order``, ``OI-hold-flag`` and ``OI-unapl`` in lower case
      ``[:L36-L40]`` beside ``OI-Deduct-Days``, ``OI-Applied`` and
      ``OI-Date-Cleared`` capitalised.
  17. Mixed-case picture keywords within one file - ``Pic``, ``Binary-long``
      and ``Comp.`` at ``[copybooks/plwsoi.cob:L16-L22]`` beside ``pic``,
      ``comp-3``, ``binary-char`` and ``comp`` from L23 down.
  18. Upper-case ``PIC`` amid lower-case ``pic``
      ``[copybooks/plwsoi5C.cob:L15]``.
  19. Declaration beats comment on the invoice field: it is declared
      ``Pic 9(8)`` at ``[copybooks/plwsoi.cob:L18]`` with the trailing note
      ``*> Was Binary-long.  *> and inv was outside the key``, and
      ``PIC 9(8). *> Was binary-long.`` at
      ``[copybooks/plwsoi5C.cob:L15]``. Eight-digit zoned display, scale zero.
  20. The type domain comment block, which skips 8
      ``[copybooks/plwsoi.cob:L25-L35]`` - prose, never a check.
  21. ``88 S-Open value zero.`` beside ``88 S-Closed value 1.`` - figurative
      constant next to literal ``[copybooks/plwsoi.cob:L54-L55]``.
  22. Dual materialisation of the composite key - the group and both members
      each get a column, the key column carrying ``COMMENT 'Supplier,
      Invoice'`` that the sales key column lacks ``[mysql/ACASDB.sql:L597]``.
  23. Two different ``replacing`` forms for the same ``COPY`` - the copybook
      adds a redefines, the bridge renames
      ``[copybooks/plwsoi5C.cob:L19-L20]`` against
      ``[common/otm5MT.cbl:L348-L349]``.
  24. ``*> TESING data`` - a typo for TESTING - at
      ``[common/otm5MT.cbl:L229]``, above the bridge's edit work fields, whose
      own casing drifts within four lines ``[:L233-L235]``.
  25. The unload order differs from the load order, and ``OI-Approp`` is
      populated implicitly through shared storage
      ``[common/otm5MT.cbl:L1338-L1425]``.

Three further oddities found while reading, recorded for completeness: the two
plan-named copybooks use CRLF line endings while the body copybook uses LF
only; ``[copybooks/plwsoi.cob:L7]`` writes the maintainer's initials in lower
case while ``[:L8]`` writes them in upper case, in the same file; and the
bridge's load paragraph writes ``OI-Ref``, ``OI-Order``, ``OI-Hold-Flag`` and
``OI-Unapl`` capitalised where the copybook declares them lower case.

QUESTIONS FOR THE COMPILED PROGRAM (R-6)
----------------------------------------
None of these can be settled by reading the frozen source, so none is settled
here. Each is written up in ``docs/migration/ambiguity-resolutions.md``.

  1. Which of the two plan-named copybooks governs the bytes on disk, given
     that they are not interchangeable and that ``pl060`` copies the
     key-only variant while ``pl100`` copies the full one.
  2. What is actually stored in ``OI5-KEY`` and ``OI5-BATCH`` on a write, and
     what a read observes, both host variables being write-only and both
     derived through bridge-internal edit fields, one of them through a
     redefines.
  3. What is stored in ``OI5-BATCH-NOS`` and ``OI5-BATCH-ITEM`` - numeric
     under an inherited COMP in the copybook, character in the table.
  4. What is stored in ``OI5-STATUS`` and ``OI5-TYPE``, both ``pic 9`` in the
     copybook and ``char(1)`` in the table, and whether the figurative-zero
     condition arrives as a digit or as a space.
  5. What appears in ``OI5-NET`` once ``OI-Approp`` has been written, the two
     sharing storage, and which programs write which name in which order.
  6. What value is stored when a negative ``binary-char`` or ``binary-long``
     passes through an unsigned host variable into an unsigned column - four
     sites here.
  7. Whether the field sum governs the record actually read, or the declared
     length does, given the 109-to-113 history.
  8. Which layout governs, the plan-named copybooks or the body copybook the
     bridge takes directly, the bridge copying neither plan-named file.

THE SIX BINDING RULES, AS THEY APPLY HERE
-----------------------------------------
This project carries no separate rules document; R-1 to R-6 are the Agent
Action Plan's own, section 0.7.2, and that is where their full text lives.

  R-1  No COBOL at runtime. This module reads no file, spawns no process,
       loads no shared library and links no compiled extension. All five
       frozen sources were read while authoring it and are never touched at
       runtime.
  R-2  Zero binary floating-point arithmetic. Three carriers only, per the
       two-direction rule above.
  R-3  Nothing added and nothing removed. No check, no enum, no lookup, no
       derived property, no post-initialisation hook, no default, no object-
       relational base or declarative metadata, no schema statement, no
       concurrency.
  R-4  Legacy anomalies reproduced, never fixed - the 25-item register above,
       each with a locator comment at its site.
  R-5  Full traceability. Every field carries a dictionary key; every class
       states its COBOL identifier verbatim with a locator; ``cite()`` is
       surfaced rather than reimplemented.
  R-6  The compiled program is the tie-breaker. Field order follows copybook
       declaration order; fixed collections are tuples; the eight questions
       above are recorded rather than answered.
"""

from __future__ import annotations

import functools
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader
from acas_posting.dictionary.model import ConditionName

__all__: Final[tuple[str, ...]] = (
    # Deterministically sorted (R-6). Nine layout classes - one per group item
    # the two copybooks declare - plus the condition-name inventory and the
    # descriptor accessor, which are the module's two traceability surfaces.
    "Filler1",
    "Oi5Key",
    "OiBatch",
    "OiCustomer",
    "OiHeader",
    "OiKey",
    "OiSupplier",
    "OpenItemRecord5",
    "WsOtm5Record",
    "condition_names",
    "descriptors_of",
)


# =============================================================================
#  FIELD BINDING
#
#  Every dataclass field below is bound to two facts and no others: the COBOL
#  identifier exactly as the frozen source writes it, and the key of its entry
#  in the generated data dictionary. Storage metadata - picture, usage, digits,
#  scale, sign, width - is never written here; it is obtained by passing the
#  key to `FieldDescriptor.from_dictionary_key`, which reads the artifact
#  lazily and memoises the result. That keeps this module free of transcription
#  (R-5) and free of import-time I/O (R-6).
#
#  `field()` is called WITHOUT a default and WITHOUT a default_factory, so
#  every attribute stays required. See "NO DEFAULT VALUES ARE SUPPLIED" in the
#  module docstring: not one of the 29 fields carries a VALUE clause in either
#  copybook, so there is no declared initial content to publish, and inventing
#  one would add state the frozen source does not declare (R-3).
# =============================================================================


def _declared(cobol_name: str, dictionary_key: str) -> Any:
    """Bind one dataclass field to its COBOL name and its dictionary key.

    Args:
        cobol_name: The identifier verbatim from the frozen copybook, case and
            hyphens intact - ``"OI-hold-flag"``, ``"oi5-supplier"``,
            ``"filler"``. Never rewritten, never case-folded. It is recorded
            per field because every ``OI-*`` name in this layout collides with
            one in the sales open-item copybook, so the declared name is what
            a reader most needs beside the attribute.
        dictionary_key: The generated artifact's key for the field -
            ``"<TABLE>.<COLUMN>"`` for a column-backed field,
            ``"<COPYBOOK-RECORD>.<FIELD>"`` for one the bridge never sees,
            with a ``#`` and the declaration line where a name repeats across
            copybooks. Written out in full rather than derived from
            ``cobol_name``, because the bridge renames every field of this
            record from the ``OI-`` prefix to ``OI5-`` and truncates one of
            them, so upper-casing a copybook name would produce a key that
            does not exist.

    Returns:
        A ``dataclasses.Field`` carrying the two names as metadata and no
        default, so the attribute remains required.
    """
    return field(
        metadata={
            "cobol_name": cobol_name,
            "dictionary_key": dictionary_key,
        }
    )


def descriptors_of(
    record_class: type[Any], *, path: Path | None = None
) -> Mapping[str, FieldDescriptor]:
    """Map each attribute of one of this module's classes to its descriptor.

    The R-5 primitive for this layout: it turns the dictionary key each field
    carries into that field's declared storage shape, so that every attribute
    of every class here can state its provenance without a single picture
    clause, digit count, scale or sign position written by hand. Agent Action
    Plan section 0.3.3 gives the reason - "field metadata is therefore derived,
    not transcribed, which eliminates an entire class of transcription error
    across several hundred fields".

    It is the per-class counterpart of ``FieldDescriptor``'s own whole-record
    helpers, ``descriptors_for_table`` and ``descriptors_for_copybook_record``,
    and it is scoped to one class because this layout's fields are spread over
    nine of them, two copybook files and two dictionary key spaces - the table
    space for column-backed fields and the copybook-record space for the seven
    fields the bridge never sees.

    The returned descriptors report the COPYBOOK view and nothing else. They
    are never blended with the bridge or column view; the three-layer
    disagreement is available untouched from ``loader.drift_for(key)``, and
    reproducing the bridge's conversions belongs to
    ``acas_posting/dal/acas029_otm5.py``. Each descriptor's ``cite()`` gives
    the three-locator provenance line, and ``cite()`` is surfaced here rather
    than reimplemented.

    ``FieldDescriptor.from_dictionary_key`` reads the generated artifact
    lazily and memoises the result, so nothing is read until this function is
    called and importing this module performs no I/O at all (R-6).

    One field carries a second key. ``OpenItemRecord5.oi5_key`` is declared in
    both plan-named copybooks and the generated artifact holds an entry for
    each, so its metadata also carries ``twin_dictionary_key``; this function
    returns the descriptor for the primary key, and the twin is reachable
    through the field's metadata. Both are carried and neither is chosen over
    the other.

    Args:
        record_class: One of this module's nine dataclasses. Any dataclass
            whose fields carry a ``dictionary_key`` in their metadata works.
        path: An alternative dictionary artifact, for the generator's own
            round-trip checks. ``None`` uses the committed artifact.

    Returns:
        A read-only mapping from attribute name to descriptor, in copybook
        declaration order because that is the order the fields are declared in
        (R-6).

    Raises:
        KeyError: If a field carries no ``dictionary_key`` metadata, which
            would mean an attribute had been added here without provenance.
    """
    return MappingProxyType(
        {
            attribute.name: FieldDescriptor.from_dictionary_key(
                attribute.metadata["dictionary_key"], path=path
            )
            for attribute in fields(record_class)
        }
    )


# =============================================================================
#  CONDITION NAMES - PUBLISHED AS DATA, NEVER AS BEHAVIOUR
# =============================================================================

#  The two elementary items in this layout that carry an 88 level, in copybook
#  declaration order. The hold flag is declared at [copybooks/plwsoi.cob:L38]
#  and the status at [:L53], so this order is the source's order and the
#  accessor below preserves it.
_CONDITION_NAME_CARRIERS: Final[tuple[str, ...]] = (
    # 88 payment-held  value "H".            [copybooks/plwsoi.cob:L39]
    # R-4 site 15: this condition name exists here and NOT on the sales
    # open-item copybook's hold flag, which declares none. The asymmetry is
    # preserved rather than levelled.
    "PUITM5-REC.OI5-HOLD-FLAG",
    # 88 S-Open        value zero.           [copybooks/plwsoi.cob:L54]
    # 88 S-Closed      value 1.              [copybooks/plwsoi.cob:L55]
    # R-4 site 21: one uses the figurative constant, the other a literal.
    # Both values are carried in the form the COBOL writes them.
    "PUITM5-REC.OI5-STATUS",
)


@functools.cache
def condition_names(*, path: Path | None = None) -> tuple[ConditionName, ...]:
    """The three 88-level condition names this layout declares, as data.

    Returns them in copybook declaration order - ``payment-held`` at
    ``[copybooks/plwsoi.cob:L39]``, then ``S-Open`` at ``[:L54]``, then
    ``S-Closed`` at ``[:L55]`` - each carrying the name, the value and the
    locator exactly as the frozen source declares them.

    Values are strings in their DECLARED form and are never rewritten. The
    figurative constant on ``S-Open`` stays the word it is written as and is
    never turned into a digit; the alphanumeric literal on ``payment-held``
    keeps the quotation marks that are part of its declaration. Preserving the
    declared form is what lets the compiled program settle question 4 in the
    module docstring - whether a figurative zero reaches that ``char(1)``
    column as a digit or as a space - instead of this module pre-empting it.

    This is an inventory, not a test. No predicate is built here and none may
    be: Agent Action Plan section 0.4.1.4 assigns predicate construction to
    ``acas_posting/cobol/condition_names.py``, and importing that module from
    a record layout would break the leaf-layer contract of section 0.4.3.

    Nothing is transcribed. The names, values and locators are read from the
    generated data dictionary, which carries them per field.

    Args:
        path: An alternative dictionary artifact, for the generator's own
            round-trip checks. ``None`` uses the committed artifact.

    Returns:
        A tuple of three ``ConditionName`` records in declaration order.
        Memoised, so two calls in one process return the same object and two
        processes agree (R-6).
    """
    return tuple(
        condition
        for key in _CONDITION_NAME_CARRIERS
        for condition in loader.copybook_field_for(key, path=path).condition_names
    )


# =============================================================================
#  THE 5B / 5C SHORT VIEW - copybooks/plwsoi5B.cob, copybooks/plwsoi5C.cob
#
#  Both plan-named copybooks declare these three items identically; they differ
#  only in the two ways the module docstring sets out. The generated artifact
#  sources them from plwsoi5B.cob, and the composite key additionally appears
#  under plwsoi5C.cob - so both files are cited where both declare an item.
# =============================================================================


@dataclass(slots=True)
class WsOtm5Record:
    """The raw 113-byte buffer ``WS-OTM5-Record``, declared elementary.

    Declared ``01  WS-OTM5-Record         pic x(113).`` at
    ``[copybooks/plwsoi5B.cob:L10]`` and ``[copybooks/plwsoi5C.cob:L10]``,
    identical in both. Dictionary entry ``WS-OTM5-Record.WS-OTM5-Record``.

    R-4 site 5: an ELEMENTARY alphanumeric item - a raw 113-byte buffer - and
    not a group, even though ``OpenItemRecord5`` and ``OiHeader`` are both
    views over the same bytes. Its descriptor reports ``is_group`` false and
    ``character_length`` 113, and it is modelled with a single ``str``
    attribute rather than as a group, exactly as declared.

    The same identifier means something else entirely inside the bridge. After
    ``[common/otm5MT.cbl:L348-L349]`` renames ``OI-Header`` to
    ``WS-OTM5-Record`` - a rename, with no redefines, unlike the copybook's
    ``replacing`` at ``[copybooks/plwsoi5C.cob:L19-L20]`` which keeps the name
    and adds one - ``WS-OTM5-Record`` there is the full 29-field group. Both
    files feed this module and the two meanings are carried apart rather than
    folded together.

    The 113 in the field width is a FIELD width taken from the declaration; no
    record-length constant is declared anywhere in this module, and the
    109-versus-113 history is left as question 7 for the compiled program.
    """

    # 01  WS-OTM5-Record         pic x(113).   [copybooks/plwsoi5B.cob:L10]
    ws_otm5_record: str = _declared(
        "WS-OTM5-Record", "WS-OTM5-Record.WS-OTM5-Record"
    )


@dataclass(slots=True)
class Oi5Key:
    """The composite key group ``oi5-key``, named in lower case.

    Declared ``03  oi5-key.`` at ``[copybooks/plwsoi5B.cob:L13]`` and
    ``[copybooks/plwsoi5C.cob:L13]``. Two dictionary entries hold this group,
    one per copybook file: ``PUITM5-REC.OI5-KEY`` sourced from
    ``plwsoi5B.cob:L13``, and ``Open-Item-Record-5.oi5-key`` sourced from
    ``plwsoi5C.cob:L13``. Both are cited on the attribute that holds this
    group, in ``OpenItemRecord5``.

    R-4 site 12: the name is ALL LOWER CASE in both files, unlike every field
    in the body copybook, and it is this spelling - not the bridge - that the
    ``OI5-`` column prefix comes from. Carried verbatim.

    R-4 site 22: dual materialisation. The group becomes the primary-key column
    ``OI5-KEY char(15) COMMENT 'Supplier, Invoice'``
    ``[mysql/ACASDB.sql:L597]`` - a comment the sales key column does not
    carry - and both of its members become columns of their own. Its host
    variable is derived through a bridge-internal edit group at
    ``[common/otm5MT.cbl:L233-L236]``, not moved; that edit group is not
    modelled here.

    Byte arithmetic: 7 + 8 = 15, matching the ``char(15)`` column and the
    inline marker ``*> 15`` at ``[copybooks/plwsoi5B.cob:L15]``.
    """

    # 05 oi5-supplier    pic x(7).            [copybooks/plwsoi5B.cob:L14]
    oi5_supplier: str = _declared(
        "oi5-supplier", "Open-Item-Record-5.oi5-supplier"
    )
    # 05 oi5-invoice     PIC 9(8).     *> Was binary-long.  *> 15
    #                                         [copybooks/plwsoi5B.cob:L15]
    # R-4 site 18: upper-case PIC amid lower-case pic in the same file.
    # R-4 site 19: declaration beats comment - the note records that this was
    # once a binary item, but it IS declared Pic 9(8), so eight-digit zoned
    # display at scale zero, carried as int.
    oi5_invoice: int = _declared(
        "oi5-invoice", "Open-Item-Record-5.oi5-invoice"
    )


@dataclass(slots=True)
class OpenItemRecord5:
    """The key-only view ``Open-Item-Record-5`` over the 113-byte buffer.

    Declared ``01  Open-Item-Record-5    redefines WS-OTM5-Record.`` at
    ``[copybooks/plwsoi5C.cob:L12]``. Dictionary entry
    ``Open-Item-Record-5.Open-Item-Record-5``, sourced from
    ``[copybooks/plwsoi5B.cob:L12]``, which declares the same line with THREE
    spaces before ``redefines`` where 5C writes FOUR.

    R-4 site 1: that one space is one of exactly two differences between the
    two plan-named copybooks. The other is that the two-line ``COPY`` of the
    body at L19-L20 is commented out in 5B - and malformed, its quoted
    filename containing four spaces - while it is live in 5C. So 5B publishes
    this short view alone and 5C publishes it together with ``OiHeader``. Both
    are live in the frozen tree: ``[purchase/pl060.cbl:L147]`` copies 5B and
    ``[purchase/pl100.cbl:L213]`` copies 5C. Neither is treated as governing
    and neither is dropped; which one governs the bytes on disk is question 1
    for the compiled program.

    Field order follows ``[copybooks/plwsoi5C.cob:L13-L17]`` (R-6). The
    trailing filler is declared, never dropped (R-3), and the inline offset
    markers in the source - ``*> 15``, ``*> 19``, ``*> 113`` - track the same
    7 + 8 + 4 + 94 = 113 the header states.
    """

    # 03  oi5-key.                            [copybooks/plwsoi5C.cob:L13]
    # Two entries hold this group, one per copybook file, and both are cited:
    #   dictionary_key       PUITM5-REC.OI5-KEY          <- plwsoi5B.cob:L13
    #   twin_dictionary_key  Open-Item-Record-5.oi5-key  <- plwsoi5C.cob:L13
    # R-4 site 1 again: the same declaration reached through two files. Both
    # are carried; neither is chosen over the other.
    oi5_key: Oi5Key = field(
        metadata={
            "cobol_name": "oi5-key",
            "dictionary_key": "PUITM5-REC.OI5-KEY",
            "twin_dictionary_key": "Open-Item-Record-5.oi5-key",
        }
    )
    # 03  oi5-date           binary-long.     *> 19
    #                                         [copybooks/plwsoi5C.cob:L16]
    # R-4 site 11: this is the field the bridge renames to OI5-DAT, dropping
    # the trailing E [common/otm5MT.cbl:L307], while OI-Date-Cleared keeps its
    # full name [:L332]. Signed binary at scale zero, so int (R-2); its sign
    # is lost at the bridge, which is the handler module's concern, not this
    # module's.
    oi5_date: int = _declared("oi5-date", "Open-Item-Record-5.oi5-date")
    # 03  filler             pic x(94).       *> 113
    #                                         [copybooks/plwsoi5C.cob:L17]
    # Declared, never silently dropped (R-3). Positionally named: it is the
    # first and only FILLER in this record.
    filler_1: str = _declared("filler", "Open-Item-Record-5.filler")


# =============================================================================
#  THE BODY - copybooks/plwsoi.cob, the 29-field layout
#
#  Field order within every class below follows copybook declaration order,
#  L12 to L62, so a reader can set this file beside `cat -n copybooks/
#  plwsoi.cob` and diff the two by eye (R-6). Class DEFINITION order is
#  innermost first, purely so each name exists before it is annotated; it is
#  the field order, not the class order, that carries the layout.
# =============================================================================


@dataclass(slots=True)
class OiSupplier:
    """The seven-byte supplier group ``OI-Supplier``, nested four deep.

    Declared ``07  OI-Supplier.`` at ``[copybooks/plwsoi.cob:L15]``. Dictionary
    entry ``PUITM5-REC.OI5-SUPPLIER`` - the group itself is column-backed, as
    ``OI5-SUPPLIER char(7)`` at ``[mysql/ACASDB.sql:L598]``.

    R-4 site 4: the bridge loads its host variable from THIS group, not from
    the outer one, at ``[common/otm5MT.cbl:L1350-L1351]``. That is the proof
    that the enclosing ``OI-Customer`` has no column - and equally that this
    group's own two children have none, because the bridge takes the seven
    bytes whole. Both children are declared here regardless: R-3 removes
    nothing.

    R-4 site 14: this is the third of four key levels, and it spans exactly the
    same seven bytes as ``OI-Customer`` above it, so the nesting is redundant.
    The bridge replicates that redundancy inside its own edit group at
    ``[common/otm5MT.cbl:L233-L236]``. Preserved, not flattened.
    """

    # 09  OI-Nos   Pic X(6).                       [copybooks/plwsoi.cob:L16]
    # R-4 site 17: capital-initial `Pic` here and at L17-L22, beside lower-case
    # `pic` from L23 down - mixed picture keywords within one file.
    # No column: see the class docstring.
    oi_nos: str = _declared("OI-Nos", "OI-Header.OI-Nos#16")
    # 09  OI-Check Pic 9.                          [copybooks/plwsoi.cob:L17]
    # Zoned display, scale zero, so int (R-2). No column.
    oi_check: int = _declared("OI-Check", "OI-Header.OI-Check#17")


@dataclass(slots=True)
class OiCustomer:
    """The column-less group ``OI-Customer``, declared but never loaded.

    Declared ``05  OI-Customer.`` at ``[copybooks/plwsoi.cob:L14]``. Dictionary
    entry ``OI-Header.OI-Customer``,
    which has NO bridge host variable and NO column - ``loader.column_for``
    and ``loader.host_variable_for`` both return ``None`` for it, and
    ``cite()`` reports ``bridge=absent  column=absent``.

    R-4 site 4: it is declared here even so. The bridge loads
    ``HV-OI5-SUPPLIER`` from the INNER ``OI-Supplier`` group at
    ``[common/otm5MT.cbl:L1350-L1351]`` and moves this group nowhere, so this
    is a copybook-only item. R-3 cuts both ways - nothing added AND nothing
    removed - and the same standard is applied here as to the other
    copybook-only items across this package.

    Its single child spans the identical seven bytes it does, which is what
    makes the nesting redundant. The name is also one of the collisions
    described in the module docstring: the sales open-item copybook declares an
    ``OI-Customer`` too, at a different level, wrapping different children.
    """

    # 07  OI-Supplier.                             [copybooks/plwsoi.cob:L15]
    # This attribute holds the group, so it carries the group's own descriptor
    # - PUITM5-REC.OI5-SUPPLIER, the column-backed one.
    oi_supplier: OiSupplier = _declared(
        "OI-Supplier", "PUITM5-REC.OI5-SUPPLIER"
    )


@dataclass(slots=True)
class OiKey:
    """The fifteen-byte key group ``OI-Key`` of the purchase open item.

    Declared ``03  OI-Key.`` at ``[copybooks/plwsoi.cob:L13]``. Dictionary entry
    ``OI-Header.OI-Key``,
    copybook-only: the composite key column ``OI5-KEY`` is sourced from the
    plan-named copybooks' lower-case ``oi5-key`` instead, which is where the
    ``OI5-`` prefix comes from.

    R-4 site 14: four levels of nesting for a fifteen-byte key -
    ``OI-Key`` to ``OI-Customer`` to ``OI-Supplier`` to the two 09-level
    children - with the middle two spanning identical bytes.

    The header records the restructuring that produced it:
    ``[copybooks/plwsoi.cob:L10]`` reads ``*>          Moved OI-Invoice into
    OI-Key``, and ``[:L8-L9]`` the accompanying size change from 109 to 113.

    Distinguished from the sales open-item copybook's ``OI-key`` BY CASE ALONE
    in the generated artifact - see the module docstring on collisions.
    """

    # 05  OI-Customer.                             [copybooks/plwsoi.cob:L14]
    oi_customer: OiCustomer = _declared(
        "OI-Customer", "OI-Header.OI-Customer"
    )
    # 05  OI-Invoice       Pic 9(8).
    #             *> Was Binary-long.  *> and inv was outside the key
    #                                         [copybooks/plwsoi.cob:L18]
    # R-4 site 19: declaration beats comment. Declared Pic 9(8) - eight-digit
    # zoned display, scale zero, int - while the bridge widens it to a
    # ten-digit binary host variable [common/otm5MT.cbl:L306] and the column is
    # `OI5-INVOICE int(8) unsigned` [mysql/ACASDB.sql:L599]. The descriptor
    # reports the copybook view: DISPLAY, eight digits. The widening is offered
    # untouched by loader.drift_for, never applied here.
    oi_invoice: int = _declared("OI-Invoice", "PUITM5-REC.OI5-INVOICE")


@dataclass(slots=True)
class OiBatch:
    """The batch group ``OI-Batch``, carrying ``Comp`` for both children.

    Declared ``03  OI-Batch                        Comp.`` at
    ``[copybooks/plwsoi.cob:L20]``. Dictionary entry ``PUITM5-REC.OI5-BATCH``,
    backed by ``OI5-BATCH char(8)`` at ``[mysql/ACASDB.sql:L601]``.

    R-4 site 7: TRIPLE materialisation. This group gets a column of its own
    AND so does each of its two children ``[common/otm5MT.cbl:L308-L310]``, and
    all three columns are CHARACTER although both children are numeric under
    the inherited COMP. The group's column is DERIVED, not moved: the bridge
    sends each child to a bridge-internal edit field and then sends an
    eight-digit redefines view of that edit group to the host variable
    ``[common/otm5MT.cbl:L238-L242]``, ``[:L1354-L1358]``. None of those edit
    fields is modelled here - reproducing the derivation belongs to
    ``acas_posting/dal/acas029_otm5.py``.

    R-4 site 2: the group's host variable is one of the two that are loaded and
    never unloaded ``[common/otm5MT.cbl:L1358]`` against ``[:L1387-L1425]``, so
    a divergence between this column and its two member columns would be
    invisible on read-back.

    R-4 site 10: both children are numeric here and character in the table.
    They are declared ``int`` because the copybook view is what a descriptor
    reports; what a write actually stores is question 3 for the compiled
    program.

    GROUP-USAGE INHERITANCE. The usage clause sits on this header and NEITHER
    child carries one of its own, so both inherit COMP from here and both
    report ``usage_declared_at == UsageDeclaredAt.GROUP`` with
    ``usage_inherited_from == "OI-Batch"``. Reading usage off their PICTURE
    lines alone would type them zoned display and every stored value would be
    wrong. Note the spelling: ``Comp.`` with a capital C here, against
    lower-case ``comp-3.`` at L41 and lower-case ``comp`` at L57-L58.
    """

    # 05  OI-B-Nos    Pic 9(5).                    [copybooks/plwsoi.cob:L21]
    # COMP inherited from the group header at L20; scale zero, so int (R-2).
    oi_b_nos: int = _declared("OI-B-Nos", "PUITM5-REC.OI5-BATCH-NOS")
    # 05  OI-B-Item   Pic 999.                     [copybooks/plwsoi.cob:L22]
    # COMP inherited from the group header at L20; scale zero, so int (R-2).
    oi_b_item: int = _declared("OI-B-Item", "PUITM5-REC.OI5-BATCH-ITEM")


@dataclass(slots=True)
class Filler1:
    """The unnamed ``filler`` group carrying ``comp-3`` for ten children.

    Declared ``03  filler                          comp-3.`` at
    ``[copybooks/plwsoi.cob:L41]``. Dictionary entry ``OI-Header.filler#41``,
    copybook-only: an UNNAMED group carries no column of its own.

    R-4 site 13: the group is a FILLER and it is load-bearing. Its ten children
    at L42-L52 carry no usage clause, so every one of them inherits COMP-3 from
    this header and reports ``usage_declared_at == UsageDeclaredAt.GROUP`` with
    ``usage_inherited_from == "filler"`` - the inherited-from naming a filler,
    carried as declared rather than replaced with an invented name. Reading
    usage off their PICTURE lines alone would type all ten as zoned display and
    corrupt every money value in the record.

    It is modelled as a nested class because the frozen source declares it as a
    group and the generated artifact confirms it - each of the ten children
    reports ``parent_group == "filler"``. Flattening the ten into the enclosing
    record would discard the group that carries their storage class. The class
    name is the declared identifier in the package's PascalCase form plus the
    positional suffix that FILLER items take, this being the first filler in
    the enclosing record.

    Unlike the sales open-item copybook, this layout has NO outer ``02 filler.``
    group above the date field - the date sits at ``03`` level directly under
    the record. That missing wrapper is not invented here.

    The declaration is spelled ``comp-3.`` in LOWER CASE, against ``Comp.``
    with a capital C at L20 - R-4 site 17, mixed picture keywords within one
    file, both spellings preserved.
    """

    # 05  OI-P-C      pic s9(7)v99.                [copybooks/plwsoi.cob:L42]
    # COMP-3 inherited from the filler header at L41; scale two, so Decimal
    # (R-2). Signed at all three layers - copybook, host variable and
    # `OI5-P-C decimal(9,2)` [mysql/ACASDB.sql:L609] - a clean pass-through.
    oi_p_c: Decimal = _declared("OI-P-C", "PUITM5-REC.OI5-P-C")
    # 05  OI-Net      pic s9(7)v99.                [copybooks/plwsoi.cob:L43]
    # Its column carries the only trace the schema keeps of the redefine that
    # follows: `OI5-NET decimal(9,2) NOT NULL COMMENT 'Also called Approp'`
    # [mysql/ACASDB.sql:L610].
    oi_net: Decimal = _declared("OI-Net", "PUITM5-REC.OI5-NET")
    # 05  OI-Approp redefines OI-Net
    #                 pic s9(7)v99.
    #                                     [copybooks/plwsoi.cob:L44-L45]
    # R-4 site 6: TWO PHYSICAL LINES forming one declaration, and the field has
    # no host variable at all - `grep -inc "approp" common/otm5MT.cbl` returns
    # 0. Its existence survives in the schema only as the column comment
    # quoted above. Declared here as a redefine view over `oi_net`; its
    # descriptor reports `redefines == "OI-Net"` verbatim and, being a
    # redefine, it contributes zero bytes to the record.
    # R-4 site 25: on a read the bridge populates it IMPLICITLY, because
    # `initialize WS-OTM5-Record` [common/otm5MT.cbl:L1393] clears the whole
    # renamed group and the move into OI-Net then lands in shared storage.
    # Base and view are deliberately NOT kept in step here: the COBOL does not,
    # and adding logic that did would breach R-3. Which name a given program
    # writes, and in what order, is question 5 for the compiled program.
    oi_approp: Decimal = _declared("OI-Approp", "OI-Header.OI-Approp#44")
    # 05  OI-Extra    pic s9(7)v99.                [copybooks/plwsoi.cob:L46]
    oi_extra: Decimal = _declared("OI-Extra", "PUITM5-REC.OI5-EXTRA")
    # 05  OI-Carriage pic s9(7)v99.                [copybooks/plwsoi.cob:L47]
    oi_carriage: Decimal = _declared("OI-Carriage", "PUITM5-REC.OI5-CARRIAGE")
    # 05  OI-Vat      pic s9(7)v99.                [copybooks/plwsoi.cob:L48]
    oi_vat: Decimal = _declared("OI-Vat", "PUITM5-REC.OI5-VAT")
    # 05  OI-Discount pic s9(7)v99.                [copybooks/plwsoi.cob:L49]
    oi_discount: Decimal = _declared("OI-Discount", "PUITM5-REC.OI5-DISCOUNT")
    # 05  OI-E-Vat    pic s9(7)v99.                [copybooks/plwsoi.cob:L50]
    oi_e_vat: Decimal = _declared("OI-E-Vat", "PUITM5-REC.OI5-E-VAT")
    # 05  OI-C-Vat    pic s9(7)v99.                [copybooks/plwsoi.cob:L51]
    oi_c_vat: Decimal = _declared("OI-C-Vat", "PUITM5-REC.OI5-C-VAT")
    # 05  OI-Paid     pic s9(7)v99.                [copybooks/plwsoi.cob:L52]
    oi_paid: Decimal = _declared("OI-Paid", "PUITM5-REC.OI5-PAID")


@dataclass(slots=True)
class OiHeader:
    """The purchase open-item record ``OI-Header``, 29 leaf fields.

    Declared ``01  OI-Header.`` at ``[copybooks/plwsoi.cob:L12]``. Dictionary
    entry ``OI-Header.OI-Header#12`` - the ``#12`` being the declaration line the
    generated artifact appends because the sales open-item copybook declares an
    ``01 OI-Header`` too, at L8. The purchase open-item layout: 29 leaf fields
    across 17 attributes, reaching the table ``PUITM5-REC``.

    This is the body that both plan-named copybooks reach through the same
    two-line ``COPY`` - live in 5C, commented out in 5B - and that the bridge
    reaches directly. The two ``replacing`` forms differ, and R-4 site 23
    keeps them apart: ``[copybooks/plwsoi5C.cob:L19-L20]`` keeps the name and
    adds ``redefines WS-OTM5-Record``, while ``[common/otm5MT.cbl:L348-L349]``
    renames outright with no redefines. So this record is a third view over the
    same 113 bytes in the copybook, and is itself the meaning of
    ``WS-OTM5-Record`` inside the bridge.

    Behaviour that reads and writes it: ``pl060`` writes and applies these
    rows; ``pl100`` clears them and takes the difference of ``OI-Date`` and
    ``OI-Date-Cleared`` for the payment-days average at
    ``[purchase/pl100.cbl:L498]`` and ``[purchase/pl100.cbl:L502]``. Both are
    ``binary-long`` and therefore ``int``, so that difference and its division
    truncate as integers - which is what keeps the registered moving-average
    anomalies reproducible.

    Field order is copybook declaration order, L13 to L62 (R-6). Both group
    items that carry a usage clause - ``OI-Batch`` at L20 and the unnamed
    filler at L41 - are held as nested classes so the twelve fields that
    inherit their storage class keep the header that gives it to them.

    Every ``OI-*`` name below also appears in the sales open-item copybook, so
    the generated artifact distinguishes the two by declaration line and, for
    the key group, by case alone. Each key is therefore written out in full
    rather than looked up by record name; see the module docstring.
    """

    # 03  OI-Key.                                  [copybooks/plwsoi.cob:L13]
    oi_key: OiKey = _declared("OI-Key", "OI-Header.OI-Key")
    # 03  OI-Date         Binary-long.             [copybooks/plwsoi.cob:L19]
    # R-4 site 13 (contrast): at 03 level DIRECTLY under the record. The sales
    # open-item copybook wraps its date in an unnamed `02 filler.` group; this
    # layout has no such wrapper and none is invented.
    # R-4 site 9: signed here, unsigned host variable [common/otm5MT.cbl:L307]
    # and `OI5-DAT int(8) unsigned` [mysql/ACASDB.sql:L600] - the sign is lost
    # AT THE BRIDGE. The descriptor reports the copybook view, signed, and the
    # disagreement is offered untouched by loader.drift_for; reproducing the
    # conversion is acas_posting/dal/acas029_otm5.py's job. What a negative
    # value actually stores is question 6 for the compiled program.
    # R-4 site 11: renamed to OI5-DAT, the trailing E dropped.
    # Binary family, scale zero, so int - and this is one of the two fields the
    # purchase payment-days average consumes (R-2).
    oi_date: int = _declared("OI-Date", "PUITM5-REC.OI5-DAT")
    # 03  OI-Batch                        Comp.    [copybooks/plwsoi.cob:L20]
    oi_batch: OiBatch = _declared("OI-Batch", "PUITM5-REC.OI5-BATCH")
    # 03  OI-Type         pic 9.                   [copybooks/plwsoi.cob:L23]
    # R-4 site 10: numeric in the copybook, `OI5-TYPE char(1)`
    # [mysql/ACASDB.sql:L604] in the table. int, because the descriptor reports
    # the copybook view.
    # R-4 site 20: the domain block at L25-L35 - which skips 8 - documents the
    # values this field takes. It stays prose. No enum, no lookup, no
    # membership test: the COBOL declares no condition name on this field at
    # all, and R-3 forbids adding a check the source does not declare.
    # R-4 site 17: lower-case `pic` from here down, against capital-initial
    # `Pic` at L16-L22.
    oi_type: int = _declared("OI-Type", "PUITM5-REC.OI5-TYPE")
    # 03  OI-ref          pic x(10).               [copybooks/plwsoi.cob:L36]
    # R-4 site 16: lower-case `ref` after the prefix. Carried verbatim.
    # Purchase-only: the sales open-item copybook has no such field and instead
    # declares a 25-character text field this layout does not have. That
    # divergence is preserved, not levelled.
    oi_ref: str = _declared("OI-ref", "PUITM5-REC.OI5-REF")
    # 03  OI-order        pic x(10).               [copybooks/plwsoi.cob:L37]
    # R-4 site 16: lower-case `order`. Purchase-only, as above.
    oi_order: str = _declared("OI-order", "PUITM5-REC.OI5-ORDER")
    # 03  OI-hold-flag    pic x.                   [copybooks/plwsoi.cob:L38]
    #     88  payment-held                      value "H".        [:L39]
    # R-4 site 15: the condition name exists here and NOT on the sales
    # open-item copybook's hold flag. It is published as data by
    # `condition_names()`; no predicate is built here.
    # R-4 site 16: lower-case `hold-flag`, while the bridge's load paragraph
    # writes `OI-Hold-Flag` capitalised [common/otm5MT.cbl:L1363]. The
    # copybook's spelling is what this attribute records.
    oi_hold_flag: str = _declared("OI-hold-flag", "PUITM5-REC.OI5-HOLD-FLAG")
    # 03  OI-unapl        pic x.                   [copybooks/plwsoi.cob:L40]
    # R-4 site 16: lower-case `unapl`, capitalised by the bridge's load
    # paragraph. Copybook spelling recorded.
    oi_unapl: str = _declared("OI-unapl", "PUITM5-REC.OI5-UNAPL")
    # 03  filler                          comp-3.  [copybooks/plwsoi.cob:L41]
    # The unnamed usage-bearing group. Declared, never dropped (R-3); it is
    # what gives ten money fields their storage class.
    filler_1: Filler1 = _declared("filler", "OI-Header.filler#41")
    # 03  OI-Status       pic 9.                   [copybooks/plwsoi.cob:L53]
    #     88  S-Open                            value zero.       [:L54]
    #     88  S-Closed                          value 1.          [:L55]
    # R-4 site 10: numeric in the copybook, `OI5-STATUS char(1)`
    # [mysql/ACASDB.sql:L618] in the table - the sharpest of the four
    # numeric-to-character drifts, because this field carries two condition
    # names with numeric values yet lands in a character column. int here.
    # R-4 site 21: figurative constant beside literal. Both values are
    # published in their declared form by `condition_names()`; whether a
    # figurative zero reaches the column as a digit or a space is question 4
    # for the compiled program.
    oi_status: int = _declared("OI-Status", "PUITM5-REC.OI5-STATUS")
    # 03  OI-Deduct-Days  binary-char.             [copybooks/plwsoi.cob:L56]
    # R-4 site 9: signed here, `9(03) COMP` host variable
    # [common/otm5MT.cbl:L326] and `OI5-DEDUCT-DAYS tinyint(3) unsigned`
    # [mysql/ACASDB.sql:L619] - sign lost at the bridge, surfaced untouched.
    # Binary family, scale zero, so int (R-2).
    oi_deduct_days: int = _declared(
        "OI-Deduct-Days", "PUITM5-REC.OI5-DEDUCT-DAYS"
    )
    # 03  OI-Deduct-Amt   pic s999v99    comp.     [copybooks/plwsoi.cob:L57]
    # THE OPPOSITE CASE to the two group headers: `comp` sits on this field's
    # own PICTURE line, so it reports `usage_declared_at ==
    # UsageDeclaredAt.FIELD` and `usage_inherited_from is None`. Getting the
    # direction wrong would change every stored value.
    # AND the two-direction rule: usage is COMP yet the carrier is Decimal,
    # because the scale is two. "COMP means int" is false (R-2).
    # R-4 site 8: signed at ALL THREE layers - `S9(03)V9(02) COMP`
    # [common/otm5MT.cbl:L327], `OI5-DEDUCT-AMT decimal(5,2)`
    # [mysql/ACASDB.sql:L620] - while the identically-declared field in the
    # invoice bridges loses its sign. Evidence that the drift is per-bridge,
    # not per-type, so no blanket rule is applied anywhere in this module.
    oi_deduct_amt: Decimal = _declared(
        "OI-Deduct-Amt", "PUITM5-REC.OI5-DEDUCT-AMT"
    )
    # 03  OI-Deduct-Vat   pic s999v99    comp.     [copybooks/plwsoi.cob:L58]
    # As above: usage on the field's own line, scale two so Decimal, and signed
    # at all three layers [common/otm5MT.cbl:L328], [mysql/ACASDB.sql:L621].
    oi_deduct_vat: Decimal = _declared(
        "OI-Deduct-Vat", "PUITM5-REC.OI5-DEDUCT-VAT"
    )
    # 03  OI-Days         binary-char.             [copybooks/plwsoi.cob:L59]
    # R-4 site 9: sign lost at the bridge [common/otm5MT.cbl:L329],
    # `OI5-DAYS tinyint(3) unsigned` [mysql/ACASDB.sql:L622]. int (R-2).
    oi_days: int = _declared("OI-Days", "PUITM5-REC.OI5-DAYS")
    # 03  OI-CR           binary-long.             [copybooks/plwsoi.cob:L60]
    # R-4 site 16: UPPER-CASE `CR`, where the sales open-item copybook writes
    # it in mixed case. Carried verbatim.
    # R-4 site 8: the strongest single piece of evidence in this layout that
    # signedness drift is per-bridge. This field KEEPS its sign the whole way -
    # `HV-OI5-CR PIC S9(10) COMP` [common/otm5MT.cbl:L330] and `OI5-CR int(8)`
    # SIGNED [mysql/ACASDB.sql:L623] - while an identically-declared
    # `binary-long` field becomes an unsigned host variable and an unsigned
    # column in both invoice bridges. So no rule of the form "binary-long
    # always loses its sign" exists, and none is applied.
    # Storage class does change at the bridge, BINARY-LONG to COMP to INT, and
    # loader.drift_for reports it untouched.
    oi_cr: int = _declared("OI-CR", "PUITM5-REC.OI5-CR")
    # 03  OI-Applied      pic x.                   [copybooks/plwsoi.cob:L61]
    # The running byte total reaches 109 at this field, which is the size the
    # header recorded before the invoice field was widened - reported, not
    # acted on.
    oi_applied: str = _declared("OI-Applied", "PUITM5-REC.OI5-APPLIED")
    # 03  OI-Date-Cleared binary-long.             [copybooks/plwsoi.cob:L62]
    # R-4 site 11: NOT truncated - the column keeps the full name
    # `OI5-DATE-CLEARED` [common/otm5MT.cbl:L332], unlike OI-Date which became
    # OI5-DAT. So the truncation is a one-off, not a rule.
    # R-4 site 9: signed here, `OI5-DATE-CLEARED int(8) unsigned`
    # [mysql/ACASDB.sql:L625] - sign lost at the bridge, surfaced untouched.
    # Binary family, scale zero, so int - the second of the two fields the
    # purchase payment-days average consumes (R-2).
    oi_date_cleared: int = _declared(
        "OI-Date-Cleared", "PUITM5-REC.OI5-DATE-CLEARED"
    )
