"""Data-access module for the OTM3 entity: COBOL handler ``acas019`` + bridge ``otm3MT``.

Spine, from AAP section 0.2.1.1::

    entity OTM3
      -> handler common/acas019.cbl      (631 lines)   -> this module's dispatch()
      -> bridge  common/otm3MT.cbl       (2192 lines)  -> this module's otm3_mt()
                 common/otm3MT.scb       (1205 lines)  -> key metadata
      -> table   SAITM3-REC              (28 columns, PK OI3-KEY) [mysql/ACASDB.sql:L896]
      -> record  copybooks/slwsoi3.cob   (20 lines, the CALLER's working-storage view)
                 copybooks/slwsoi.cob    (57 lines, the field layout both sides copy)
      -> module  acas_posting/records/otm3.py  (WsOtm3Record, OpenItemRecord3, OiHeader)

AAP section 0.3.1 fixes the granularity: "One data-access module per handler, not per
table ... preserves the dispatch semantics rather than flattening them." So this one
module carries BOTH programs, each as its own set of paragraph functions, and nothing
is merged between them.

SAITM3-REC is the Sales open-item file. Handler ``acas019`` is, by its own remarks, the
model the maintainer copied the rest of the file handlers from - it "came from acas016
(Invoice)" and is "the model for all other FH and DALs" [common/acas019.cbl:L1-L60].
That pedigree is why so many of the oddities recorded below recur verbatim in sibling
handlers, and why the divergences that do exist are worth naming precisely.

===============================================================================
PART 0 - SIX VERIFIED CORRECTIONS TO THIS MODULE'S OWN BRIEF
===============================================================================

Rule R-6 makes compiled behaviour the tie-breaker for every behavioural decision, so
where the brief's prose and the frozen source disagree, THE SOURCE WINS. Six such
disagreements were found and each is resolved here against the source, with the
verifying locator. They are recorded in the module docstring because a future reader
comparing this module against the brief would otherwise read them as defects.

C1. FUNCTION CODES 32 AND 33 *ARE* IMPLEMENTED - BY THE BRIDGE, NOT THE HANDLER.
    The brief states they are "implemented NOWHERE" and must not be implemented.
    VERIFIED FALSE for the bridge. [common/otm3MT.cbl:L422-L427]::

        when  32
              go to ba140-Process-Read-Next    *> Sorted-By-Batch (nos,item,type,date,inv)
        when  33
              go to ba150-Process-Read-Next    *> Sorted-By-Cust (cust,date,inv,type)

    What is true is narrower and is exactly what the brief verified: ``acas019``'s own
    FLAT-FILE dispatch [common/acas019.cbl:L283-L302] names neither code. Both
    statements therefore hold at once, because the two dispatches are different
    dispatches on different paths - see C2.

    ==> dispatch() implements NINE codes.  otm3_mt() implements ELEVEN.
    Dropping 32/33 from the bridge would DELETE compiled behaviour, which rule R-4
    makes a failure just as surely as fixing a defect does. The declaration the brief
    cites, [copybooks/wsfnctn.cob:L103-L104], is therefore honoured rather than
    orphaned::

        88  fn-Read-By-Batch   value 32.       *> 08/02/17 for OTM3/5 (sl095/pl095)
        88  fn-Read-By-Cust    value 33.       *> 09/02/17 for OTM3 (sl110, 120, 190)

    Corroborated independently, and from the other direction, by
    ``cursor_state.EXTRA_READ_ORDERS["SAITM3-REC"]``, which encodes both orders with
    ``owning_handlers=("acas019",)``.

C2. THE RDB PATH NEVER REACHES THE HANDLER'S DISPATCH. [common/acas019.cbl:L262-L266]::

        if       not FS-Cobol-Files-Used
                 move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
                 perform ba-Process-RDBMS
                 go to AA-Main-Exit
        end-if.

    The branch is taken BEFORE the nine-code ``evaluate`` at L283, and it leaves by
    ``go to AA-Main-Exit``. So ``aa020`` .. ``aa100`` are FLAT-FILE ONLY; on the DAL
    path ``acas019`` delegates wholesale to ``otm3MT``. The key guard at L245-L259 sits
    ABOVE the branch, so it is the one piece of handler logic that governs BOTH paths.

C3. HANDLER AND BRIDGE SEE THE *SAME* DECLARATION OF THE PARAMETER.
    The brief's anomaly "N-two-record-views" says the two sides see different
    declarations of ``WS-OTM3-Record``. VERIFIED FALSE. The handler's LINKAGE SECTION
    copies the field layout exactly as the bridge does [common/acas019.cbl:L215]::

        copy "slwsoi.cob" replacing OI-Header by WS-OTM3-Record.

    and [common/otm3MT.cbl:L345-L346]::

        copy "slwsoi.cob" replacing OI-Header
                      by WS-OTM3-Record.

    ``copybooks/slwsoi3.cob`` - the flat ``pic x(118)`` with two redefinitions - is NOT
    copied by ``acas019`` at all. It is the CALLER's working-storage view. And the
    handler's FILE record comes from a third place, ``copybooks/slfdoi3.cob``, where
    ``01 Open-Item-Record-3`` is a STANDALONE record, not a ``redefines``, carrying its
    own revision date (20/08/17) that differs from ``slwsoi3.cob``'s (08/02/17).

    ==> The real finding is sharper than the brief's: THREE arrangements over the same
    118 bytes, declared in THREE different places, agreeing on the size and disagreeing
    on the shape. Modelled explicitly below as the linkage view, the caller view and
    the file view.

C4. ``move OI-Key to OI3-Key`` IS *NOT* A SELF-COPY. The brief calls
    [common/acas019.cbl:L406] "a self-assignment through two views". VERIFIED FALSE: it
    copies LINKAGE (``OI-Key``, in ``WS-OTM3-Record``) into the FILE record
    (``OI3-Key``, in ``Open-Item-Record-3``) - two distinct storage areas in two
    different sections. The maintainer says so at [common/acas019.cbl:L454]::

        *> copy WS to file

    It is still reproduced as an explicit re-materialisation through both layouts,
    which is what the brief asked for; only the reason changes.

C5. THE THREE CURSORS ARE *NOT* SURPLUS. The brief records "three cursors in a
    single-table bridge with no repeating group" and asks that the surplus be recorded.
    VERIFIED: all three are used, one per read-next paragraph -
    ``ba040`` drives ``Most-Cursor-Set`` [common/otm3MT.cbl:L262],
    ``ba140`` (code 32) drives ``Most-Cursor-Set-2`` [:L265],
    ``ba150`` (code 33) drives ``Most-Cursor-Set-3`` [:L268].
    So the count follows from C1: three sort orders, three cursors. There is no
    surplus, and the maintainer's hedging comments ("RG 1 or special", "RG 2 or
    special") describe an intent the code outgrew rather than dead state.

C6. THE SIGN IS DROPPED FOR *EVERY* NUMERIC COLUMN, IN THE SQL TEXT.
    This is the largest correction and it inverts the brief's headline finding. The
    brief celebrates ``OI3-CR`` as the field whose sign SURVIVES. It survives at the
    host-variable layer only, and never reaches the stored value, because of how the
    bridge renders numbers into SQL. [common/otm3MT.cbl:L226]::

        01  WS-MYSQL-EDIT      PIC -Z(18)9.9(9).

    That is 30 character positions: the sign at position 1, eighteen zero-suppressed
    digits at 2..19, a guaranteed digit at 20, the point at 21, nine decimals at
    22..30. EVERY numeric render in the INSERT and the UPDATE slices this image, and
    every slice starts at or after position 11::

        9(10)          -> WS-MYSQL-EDIT(11:10)
        9(03)          -> WS-MYSQL-EDIT(18:03)
        S9(07)V9(02)   -> WS-MYSQL-EDIT(14:07) '.' WS-MYSQL-EDIT(22:02)
        S9(03)V9(02)   -> WS-MYSQL-EDIT(18:03) '.' WS-MYSQL-EDIT(22:02)

    Position 1 is in NO slice. Verified verbatim at three sites of three different
    shapes: ``OI3-P-C`` [common/otm3MT.cbl:L1542], ``OI3-DEDUCT-AMT`` [:L1716] and
    ``OI3-CR`` [:L1762].

    ==> Negative money, and a negative ``OI3-CR``, are stored as UNSIGNED MAGNITUDE in
    a signed column. The signedness drift the dictionary reports for four fields is
    real but is not the whole story; the render drops the sign for all twenty-two
    numeric columns, drift or no drift. This module reproduces it by building the
    edited image and slicing it, which drops the sign MECHANICALLY - there is no
    absolute-value call anywhere in this file, and rule R-2's prohibition on
    binary floating-point is untouched because the image is built from Decimal and int.

===============================================================================
PART 1 - THE TWO PUBLISHED SIGNATURES (rule R-5)
===============================================================================

AAP section 0.4.3 fixes the handler contract in form::

    FROM:  call "acas019" using System-Record WS-OTM3-Record File-Access
                                File-Defs ACAS-DAL-Common-data
    TO:    acas019_otm3.dispatch(system, otm3, file_access, file_defs, dal_common)

verified against [common/acas019.cbl:L225-L231]::

    Procedure Division Using System-Record
                             WS-OTM3-Record
                             File-Access
                             File-Defs
                             ACAS-DAL-Common-data.

and the bridge contract against [common/otm3MT.cbl:L611-L615] as reached from the
handler [common/acas019.cbl:L611-L615]::

    call     "otm3MT" using  File-Access
                                 ACAS-DAL-Common-data
                                 WS-OTM3-Record
    end-call.

    TO:    acas019_otm3.otm3_mt(file_access, dal_common, otm3)

Both are published because both are called in the frozen system, and rule R-5 requires
a reader following either call site to find a correspondingly named function. The
parameter ORDER of each differs from the other and both are preserved exactly.

Neither ever raises. [common/acas019.cbl:L617] is the contract::

    *>   Any errors leave it to caller to recover from

so every path returns the ``(FsReply, We-Error)`` pair and writes it into
``file_access``, including driver failures, which are classified through
``dal/status.py`` rather than propagated.

===============================================================================
PART 2 - VERB SETS AND DISPATCH ORDER
===============================================================================

Handler, [common/acas019.cbl:L283-L302] - nine codes, in this source order::

    1 -> aa020-Process-Open           5 -> aa070-Process-Write
    2 -> aa030-Process-Close          7 -> aa090-Process-Rewrite
    3 -> aa040-Process-Read-Next      8 -> aa080-Process-Delete
    4 -> aa050-Process-Read-Indexed   9 -> aa060-Process-Start
                                  other -> aa100-Bad-Function   *> 6 is spare / unused

``aa100-Bad-Function`` has TWO entry paths: the ``when other`` arm, and an
unconditional fall-through immediately after the ``evaluate`` [:L304-L305]::

    *>  Should never get here but in case :(
    go       to aa100-Bad-Function.

Bridge, [common/otm3MT.cbl:L406-L429] - eleven codes; the same nine plus 32 and 33.

There is NO code 6, no 31, no 34, and NO Delete-All on either side.

===============================================================================
PART 3 - THE OI-Type LEGEND, QUOTED (only place these codes are documented)
===============================================================================

[copybooks/slwsoi.cob:L19-L30], verbatim::

    03  OI-Type          pic 9.
                           ***********************************
                           *  1  =  Receipt                  *
                           *  2  =  Account                  *
                           *  3  =  Cr. Note                 *
                           *  4  =  Proforma (Not used)      *
                           *  5  =  Payment                  *
                           *  6  =  Journal-Unapplied Cash   *
                           *  7  =  Journal Type B (Not Used)*
                           *  9  =  Old Payments             *
                           ***********************************

Note what the legend does and does not say: 4 and 7 are both marked "(Not used)" and
yet are documented; 8 is absent entirely while 9 is present. The COBOL field is
``pic 9`` - numeric - but the column is ``char(1)``, so the values arrive as
CHARACTERS. See anomaly N-numeric-to-char.

The ``88``-level condition names over ``OI-Status`` [copybooks/slwsoi.cob:L48-L49]::

    88  S-Open                         value zero.
    88  S-Closed                       value 1.      *> Paid

belong to ``acas_posting/records/otm3.py``, reachable through its
``condition_names_for()``. They are deliberately NOT re-declared here: AAP section
0.4.3's import table does not permit ``dal/*`` to import ``acas_posting.cobol.*``, and
duplicating the predicates in the data-access layer would put business meaning in a
layer that must not hold any.

===============================================================================
PART 4 - THE DRIFT TABLE: copybook -> host variable -> column
===============================================================================

Twenty-eight columns. Every conversion below is TAKEN FROM the generated dictionary
when this module loads, never transcribed - AAP section 0.8.1 is prescriptive here:
"Data dictionary first ... every Python field definition cites its entry. This ordering
is a directive, not a preference - it is what prevents fields being transcribed by
eye." The table is reproduced here as prose so a reader can audit the generator's
output, not as the source of truth.

Column order below is the table's own ordinal order [mysql/ACASDB.sql:L896-L926]::

  #  column              sql type              copybook field   copybook decl     drift
  -- ------------------- --------------------- ---------------- ----------------- -----
  1  OI3-KEY             char(15)  PRIMARY KEY OI3-Key/OI-key   group             DERIVED, WRITE-ONLY
  2  OI3-CUSTOMER        char(7)               OI-Customer      group x(6)+9      group flattened
  3  OI3-INVOICE         int(8) unsigned       OI-Invoice       9(8)  DISPLAY      8 -> 10 -> 8
  4  OI3-DAT             int(8) unsigned       OI-Date          binary-long       SIGN LOST; RENAMED
  5  OI3-BATCH           char(8)               OI-Batch         COMP group        DERIVED, WRITE-ONLY
  6  OI3-BATCH-NOS       char(5)               OI-B-Nos         9(5)  COMP        binary -> char
  7  OI3-BATCH-ITEM      char(3)               OI-B-Item        999   COMP        binary -> char
  8  OI3-TYPE            char(1)               OI-Type          9     DISPLAY     numeric -> char
  9  OI3-DESCRIPTION     char(32)              OI-Description   x(25)             width 25 -> 32
 10  OI3-HOLD-FLAG       char(1)               OI-Hold-flag     x                 clean
 11  OI3-UNAPL           char(1)               OI-Unapl         x                 clean
 12  OI3-P-C             decimal(9,2)          OI-P-C           s9(7)v99 COMP-3   signed all layers
 13  OI3-NET             decimal(9,2)          OI-Net           s9(7)v99 COMP-3   signed all layers
 14  OI3-EXTRA           decimal(9,2)          OI-Extra         s9(7)v99 COMP-3   signed all layers
 15  OI3-CARRIAGE        decimal(9,2)          OI-Carriage      s9(7)v99 COMP-3   signed all layers
 16  OI3-VAT             decimal(9,2)          OI-Vat           s9(7)v99 COMP-3   signed all layers
 17  OI3-DISCOUNT        decimal(9,2)          OI-Discount      s9(7)v99 COMP-3   signed all layers
 18  OI3-E-VAT           decimal(9,2)          OI-E-Vat         s9(7)v99 COMP-3   signed all layers
 19  OI3-C-VAT           decimal(9,2)          OI-C-Vat         s9(7)v99 COMP-3   signed all layers
 20  OI3-PAID            decimal(9,2)          OI-Paid          s9(7)v99 COMP-3   signed all layers
 21  OI3-STATUS          char(1)               OI-Status        9     DISPLAY     numeric -> char
 22  OI3-DEDUCT-DAYS     tinyint(3) unsigned   OI-Deduct-Days   binary-Char       SIGN LOST
 23  OI3-DEDUCT-AMT      decimal(5,2)          OI-Deduct-Amt    s999v99 COMP      signed all layers
 24  OI3-DEDUCT-VAT      decimal(5,2)          OI-Deduct-Vat    s999v99 COMP      signed all layers
 25  OI3-DAYS            tinyint(3) unsigned   OI-Days          binary-Char       SIGN LOST
 26  OI3-CR              int(8)                OI-Cr            binary-long       sign kept in HV
 27  OI3-APPLIED         char(1)               OI-Applied       x                 clean
 28  OI3-DATE-CLEARED    int(8) unsigned       OI-Date-Cleared  binary-long       SIGN LOST

FOUR SIGNEDNESS DRIFTS at the host-variable layer - ``OI3-DAT``, ``OI3-DEDUCT-DAYS``,
``OI3-DAYS``, ``OI3-DATE-CLEARED`` - each a signed COBOL field narrowed to an unsigned
host variable [common/otm3MT.cbl:L305, :L323, :L326, :L329] and an unsigned column.
This is the AAP Anomaly #11 family, and AAP section 0.6.2 is explicit about the
obligation: "the Python data-access layer must reproduce the bridge's conversion, not
merely write the computed value and let MySQL complain."

AND the twist recorded as C6: the SQL render drops the sign for ALL TWENTY-TWO numeric
columns regardless, so the four drifts change the HOST VARIABLE while the render changes
the STORED VALUE. Both are reproduced, in that order, because they happen in that
order. ``OI3-CR``, ``OI3-DEDUCT-AMT`` and ``OI3-DEDUCT-VAT`` keep their sign through the
host variable and lose it at the render; the other nineteen lose it twice over.

TWO WRITE-ONLY DERIVED COLUMNS. ``OI3-KEY`` and ``OI3-BATCH`` are assembled by the
bridge and stored, and are NEVER read back into the record. The load performs 28
host-variable assignments [common/otm3MT.cbl:L1341-L1374]; the unload performs 26
[:L1386-L1413], and the two it omits are exactly these. See N-two-write-only-columns.

===============================================================================
PART 5 - FIELDS WITH NO HOST VARIABLE AND NO COLUMN (recorded omissions, rule R-5)
===============================================================================

AAP section 0.7.2 R-5: "Deliberate omissions are recorded as omissions." Each of the
following exists in the copybook and reaches neither the host-variable group nor the
schema. None is invented into existence here.

* ``OI-Nos``   ``pic x(6)`` and ``OI-Check`` ``pic 9`` [copybooks/slwsoi.cob:L11-L12] -
  the two children of ``OI-Customer``. The group is FLATTENED into the single
  ``char(7)`` column ``OI3-CUSTOMER``; the children have no columns of their own.
* ``OI-Approp`` [copybooks/slwsoi.cob:L38-L39] - NOT A FIELD. It is
  ``redefines OI-Net``, and the frozen schema records the fact in a column comment:
  ``OI3-NET decimal(9,2) NOT NULL COMMENT 'Also called Approp'``. There is no
  ``OI3-APPROP`` column and no ``HV-OI3-APPROP`` host variable, and neither is added.
  ``records.otm3.Filler2`` does carry an ``oi_approp`` attribute, faithfully, because
  the redefinition exists in the copybook; this module writes ``oi_net``.
* The two unnamed ``filler`` groups at [copybooks/slwsoi.cob:L14] and [:L35]. They
  occupy no bytes of their own; they exist to carry ``COMP`` / ``COMP-3`` usage down to
  their children. ``records.otm3`` models them as ``Filler1`` / ``Filler2``.
* ``filler pic x(99)`` at [copybooks/slwsoi3.cob:L16] - padding in the CALLER's short
  view only, blind to 99 of the 118 bytes. Never a column.

RECORD SIZE, AGREED. Both copybooks state 118 bytes and both explain the revision from
114 [copybooks/slwsoi3.cob:L4-L7], [copybooks/slwsoi.cob:L6]::

    *> 08/02/17 VBC changed size to 118 (from 114) after
    *>          changing Inv from Bin to 9(8)

Recording the AGREEMENT matters as much as recording the disputes: it is a second
counter-example, alongside ``wsanal.cob``, to the contradicted sizes in ``wsbatch.cob``
(AAP Anomaly #15), ``wsval.cob`` and ``slwsinv.cob``, and it shows those are genuine
findings rather than a habit of the codebase.

===============================================================================
PART 6 - ANOMALY REGISTER (rule R-4: reproduced, never fixed)
===============================================================================

AAP section 0.8.2: "compiled COBOL execution is the behavioral specification, defects
included. A defect reproduced is correct; a defect fixed is a failure." AAP section
0.7.4 C-4 additionally requires "a comment at each reproduction site citing the COBOL
locator", which every entry below has. Every entry also belongs in
``docs/migration/anomaly-log.md`` naming THIS module as the reproducing module.

N-two-write-only-columns  ``HV-OI3-KEY`` [:L1345] and ``HV-OI3-BATCH`` [:L1351] are
    loaded and never unloaded [:L1386-L1413]. Reproduced by omitting both from
    ``bb100_unload_hvs``. The unload is NOT completed.
N-sql-render-drops-sign   C6 above. Reproduced by ``ws_mysql_edit`` + slicing.
N-oi3-cr-sign-survives    ``OI-Cr binary-long`` [copybooks/slwsoi.cob:L54] ->
    ``HV-OI3-CR PIC S9(10) COMP`` [common/otm3MT.cbl:L327] -> ``OI3-CR int(8)`` signed.
    The logically identical field in the invoice bridge loses its sign:
    ``sih-cr binary-long`` -> ``HV-IH-CR PIC 9(10) COMP``
    [common/slinvoiceMT.cbl:L418] -> ``IH-CR int(8) unsigned``. One logical field, two
    bridges, two answers. No rule of the form "counters lose signs, money does not"
    survives contact with this codebase; only the per-field, per-bridge dictionary does.
N-deduct-sign-divergence  ``OI-Deduct-Amt`` / ``-Vat`` are signed at all three layers
    here [copybooks/slwsoi.cob:L51-L52], [common/otm3MT.cbl:L324-L325],
    ``decimal(5,2)`` - and unsigned at both in the invoice bridge
    [common/slinvoiceMT.cbl:L415-L416], ``decimal(5,2) unsigned``.
N-signloss                The four fields listed in PART 4. Applied in the load, before
    any statement is built, behind one named helper. No error is raised, no clamping and
    no absolute-value call. The exact stored value is an AAP section 0.6.8 oracle
    question, recorded in ``docs/migration/ambiguity-resolutions.md``.
N-batch-triple            The batch is stored THREE TIMES per row - whole, plus both
    components [common/otm3MT.cbl:L306-L308], [:L1347-L1351] - and the schema flags the
    components ``COMMENT 'Batch content'``.
N-binary-to-char          ``OI-Batch`` is a ``COMP`` group [copybooks/slwsoi.cob:L16-L18]
    whose three columns are ALL ``char``. The ``WS-Temp-ED-Batch`` staging converts
    binary to display digits en route. Integers are never stored.
N-numeric-to-char         ``OI-Type`` [copybooks/slwsoi.cob:L19] and ``OI-Status``
    [:L47] are ``pic 9`` in COBOL and ``char(1)`` in the schema.
N-desc-width              ``OI-Description`` drifts 25 -> 32 [copybooks/slwsoi.cob:L32],
    [common/otm3MT.cbl:L310]. The value survives; the padding differs; padding is
    visible in a table dump, which is why ``harness/normalize.py`` canonicalises it.
N-oi-approp-redefine      PART 5. No column, no host variable, nothing added.
N-three-record-views      C3 above: linkage [common/acas019.cbl:L215], caller
    [copybooks/slwsoi3.cob:L9-L19], file [copybooks/slfdoi3.cob]. Three arrangements,
    three places, one size.
N-false-occurs-comment    [common/otm3MT.cbl:L342-L343]::

        *>  Using the first record but not the 2nd as it uses occurs 40 but
        *>   to reduce Ram usage get rid of the occurs, hopefully.

    A copy-paste from [common/slinvoiceMT.cbl:L453-L454] and INAPPLICABLE:
    ``copybooks/slwsoi.cob`` contains no ``occurs`` and no second record, and the
    ``REPLACING`` removes no OCCURS. The maintainer appended "hopefully". Recorded as a
    false comment and NOT repeated as fact.
N-three-cursors           C5 above. All three reproduced as state.
N-aa041-move-inv-data     [common/acas019.cbl:L390] - a paragraph name that appears in
    no other handler, occupying the slot where ``acas005``/``006``/``007``/``012`` have
    ``aa041-Reread``. Kept under its own name.
N-oi-key-cross-section-copy  C4 above. [common/acas019.cbl:L406]. Reproduced as an
    explicit re-materialisation through both layouts, not optimised away.
N-deadbranches            ``aa045-Eval-Keys``'s ``when 5``/``7``/``8``/``9`` arms are
    UNREACHABLE, because its only caller is the read-indexed path. The maintainer's own
    doubt is on the line above [common/acas019.cbl:L395]::

        *>   The next block will never get executed unless performed  so is it needed ?

    Reproduced whole, dead arms included.
N-spaces-into-numeric     ``move spaces to OI3-Key`` [common/acas019.cbl:L368], into a
    group whose second half is ``PIC 9(8)``. Reproduced literally; zeros are NOT
    substituted.
N-codes-32-33             See C1: declared at [copybooks/wsfnctn.cob:L103-L104],
    dispatched by the BRIDGE and by neither handler's flat-file dispatch.
N-log                     ``WS-Log-File-No`` 15 [common/acas019.cbl:L241] overwritten
    with 25 [:L557], with the casing flipped from ``-No`` to ``-no``. Collides with
    ``acas008``, which also goes 15 -> 25 [common/acas008.cbl:L294, :L523] but with
    ``WS-Log-System = 1`` (IRS) against this handler's 3 (SL). Only the
    ``(system, file)`` PAIR disambiguates. Fourth such collision in the folder
    (11->21, 12->22 x3, 13->23 x2, 15->25 x2).
N-logsystem5-meaning      The legend at [common/acas019.cbl:L240] says ``5=Invoice``,
    agreeing with [common/acas016.cbl:L248] and contradicting
    [common/acas013.cbl:L298] and [common/acas015.cbl:L291], which both say
    ``5=Stock``.
N-noopenoutput            There is NO ``if fn-Open and fn-output`` block anywhere in
    ``acas019`` - a FOURTH distinct Open-Output semantics across six handlers:
    ``acas005`` has one commented out [common/acas005.cbl:L307-L314]; ``acas006`` /
    ``acas007`` make two bridge calls, open then delete-all by fall-through
    [common/acas006.cbl:L313-L318, :L640-L644, :L653]; ``acas008`` coerces the function
    to delete-all [common/acas008.cbl:L313-L319, :L571-L574]; ``acas015`` /
    ``acas016`` / ``acas019`` have NO block at all. Open with ``Open-Output`` here is a
    plain open and removes NOTHING. ``acas008``'s coercion is deliberately not ported.
N-nobadal                 No ``ba020-*`` paragraph on the handler side; the bridge
    ``call`` is inline in ``ba015-Test-Ends`` [common/acas019.cbl:L611-L615].
N-stop                    A debugging ``stop "Cobol File EOF"``
    [common/acas019.cbl:L371], on the flat-file path, unreachable in the migrated cycle.
    Recorded as anomaly AND as omission: no pause, no console read, no delay is
    reproduced, per AAP section 0.3.4's rule for acknowledgement prompts.
N-noparagraph-collision   ``WS-No-Paragraph`` 201..208 is identical to ``acas013``,
    ``acas015`` and ``acas016``.
N-nolog-on-dal            [common/acas019.cbl:L623] carries its comment on the label
    line itself::

        Ca-Process-Logs. *> Not called on DAL access as it does it already

    so this module does not log through the handler on the DAL path.
N-996-comment             The 996 comment at [common/acas019.cbl:L255] is a verbatim
    copy of the 998 comment at [:L249] - both read "file seeks key type out of range",
    which describes neither a delete nor its own code. Not rewritten. Not harmonised
    with ``acas000``'s different guarded set (4, 5, 7).
N-initialize              THREE ``initialize WS-OTM3-Record with filler`` sites
    [common/otm3MT.cbl:L626, :L1123, :L1277] against ONE plain
    ``initialize WS-OTM3-Record`` [:L1384] - the widest such split in the checkout. Each
    is reproduced in place with its own semantics.
N-loadorder               The LOAD order [common/otm3MT.cbl:L1341-L1374], the UNLOAD
    order [:L1386-L1413] and the COLUMN order are THREE DIFFERENT LISTS, and are kept
    as three separate lists here. None is derived from another.
N-punctuation             Irregular periods in the load: [:L1345] is unpunctuated
    between punctuated neighbours [:L1342, :L1344, :L1348, :L1350, :L1351], then
    [:L1353] to [:L1374] are unpunctuated throughout. Recorded, not normalised.
N-casing                  ``WS-Temp-ED-Key`` declared [:L232] and referenced
    ``WS-Temp-Ed-Key`` [:L1345]; ``HV-OI3-KEY`` [:L741] against ``HV-OI3-Key``
    [:L1139, :L1293]; ``WS-Log-File-No`` against ``WS-Log-File-no``
    [common/acas019.cbl:L241, :L557]; ``aa045-Eval-Keys`` declared [:L397] and
    performed ``aa045-Eval-keys`` [:L418]; and the handler's own
    ``WS-Temp-ED`` / ``ws-temp-ed-1`` / ``WS-Temp-ed-2`` [:L202-L204] - three casings of
    one name. Plus the typo ``*> TESING data`` [common/otm3MT.cbl:L228]. Recorded, not
    fixed.
N-kortype                 ``KOR-Type`` carries ``'STR'`` [common/otm3MT.cbl:L251] while
    its own declaration comment says "Not used currently" [:L258] - the same
    contradiction as ``nominalMT``, ``glpostingMT``, ``glbatchMT``, ``analMT`` and
    ``slinvoiceMT``; only ``slpostingMT`` says ``'BNT'``.
N-cdftodo                 The unfinished compiler-directive TODO
    [common/acas019.cbl:L604-L609] - the maintainer's note that a directive is needed to
    select between the JC, dbpre and Prima translators, deferred "after system testing
    and pre code release". Recorded; there is one translator and one path.
N-deadfields              ``WS-Body-Key pic x(9)`` [common/otm3MT.cbl:L280] - here with
    NO "Not used" comment, unlike the same field in ``slinvoiceMT`` - and
    ``WS-Temp-ED-Row`` [:L230], which IS used, but only to render a row count into a log
    string. Recorded as declared-and-otherwise-dead.
N-read-indexed-23         NEW, verified. ``ba050`` reports a missed key as
    ``FS-Reply 23`` [common/otm3MT.cbl:L689-L692]::

        if     WS-MYSQL-Count-Rows = zero
               move 23  to fs-Reply             *> could also be 21 or 14
               move zero to WE-Error

    where the canonical bridge reports 21 for the same condition, with the mirror-image
    comment ``*> could also be 23 or 14`` and twice more ``*> from 23``. The two bridges
    disagree, and each documents the other's answer as the alternative it rejected.
    This module therefore owns its read-indexed statuses locally instead of delegating
    to ``dal/cursor_state.read_indexed``, whose 21 belongs to the other bridge.
N-start-997-vs-998        NEW, verified. The SAME guard condition -
    ``access-type`` outside 5..8 - yields ``We-Error 998`` in the handler
    [common/acas019.cbl:L437-L448, aa060] and ``997`` in the bridge
    [common/otm3MT.cbl:L758-L762]. Both reproduced, each on its own side.
    ``fn-not-greater-than value 9`` is rejected by BOTH guards even though
    [copybooks/wsfnctn.cob:L116] declares it and [:L20] records it "Activated", and
    even though the bridge's own relation table [common/otm3MT.cbl:L785-L786] gives it
    an arm labelled "[ not currently used in ACAS ]". Widening either guard would fix a
    defect.
N-string-pointer-overrun  NEW, verified. Every predicate the bridge builds is read back
    as ``WS-Where (1:J)`` where ``J`` is the STRING pointer AFTER the transfer, so the
    slice is one character LONGER than the text and carries a trailing space into the
    statement - ``... WHERE `OI3-KEY`="..." ;``. Reproduced in the statement text.
N-ba998-frees-primary-only  NEW, verified. ``ba998-Free`` always
    ``set Cursor-Not-Active to true`` [common/otm3MT.cbl:L1317] - the PRIMARY flag -
    even when it is freeing after a code-32 or code-33 read that activated the SECONDARY
    or TERTIARY cursor. Reproduced: the free clears the primary flag only.
N-sorted-order-is-a-syntax-error  NEW, verified, and the sharpest defect in the bridge.
    ``ba140`` and ``ba150`` put ONLY an ORDER BY into ``WS-Where``
    [common/otm3MT.cbl:L1000-L1007, :L1153-L1159] while the SELECT template
    unconditionally emits ``" WHERE "`` before it, and every ordering term is
    SINGLE-QUOTED - a string constant, which orders nothing. The statement reaching
    MySQL is::

        SELECT * FROM `SAITM3-REC` WHERE  ORDER BY 'OI3-INVOICE', 'OI3-DAT' ASC, ... ;

    which is a syntax error, so both sorted reads fail at the driver. ``ba140``'s prose
    comment [:L991-L993] additionally lists the terms in the REVERSE of the code's
    order - a second false comment. Both paragraphs also compute ``K`` and ``L`` from
    the key table and then never use them. Reproduced exactly, statement text included;
    ``cursor_state.EXTRA_READ_ORDERS`` records the same finding as its anomaly A8 with
    the ``(99, 911)`` outcome.

N-file-status-is-the-linkage-field  NEW, verified, and it changes what EVERY verb
    paragraph reports. The SELECT declares ``status  fs-Reply``
    [copybooks/slseloi3.cob:L2-L6], so the ISAM runtime writes each operation's file
    status directly into the CALLER's ``File-Access.Fs-Reply``. Two things follow that a
    reading of the paragraphs alone would miss. First, the ``move`` inside an
    ``invalid key`` phrase NORMALISES rather than reports - the runtime has already stored
    22 for a duplicate and 23 for a missing record, and ``move 22 to FS-Reply``
    [common/acas019.cbl:L496] then collapses the whole '2x' class onto one value, so a
    duplicate and a boundary violation are indistinguishable to a caller of the write BY
    CONSTRUCTION. Second, a failure OUTSIDE that class never runs the phrase at all, so
    the runtime's own status survives - a permanent error 30 or a lock 9x reaches the
    caller as itself, NOT as 21 or 22. Reproduced by ``_invalid_key_condition``: every
    verb stores the status first and applies its phrase only inside range(21, 25).
    Collapsing every non-zero status into the phrase's value would have invented a
    translation the frozen program does not perform.

N-start-fs-reply-stays-zero  NEW, verified. ``aa060-Process-Start`` zeroes BOTH fields at
    [common/acas019.cbl:L443-L444] and its parameter guard at [:L447-L449] then sets
    ``move 998 to WE-Error`` AND NOTHING ELSE. So a rejected START is reported as
    ``FS-Reply`` = 0 with ``WE-Error`` = 998: a caller testing only ``FS-Reply`` - which is
    the field the ``status`` clause makes authoritative everywhere else - sees SUCCESS on
    an operation that never positioned the cursor. The BRIDGE does set both, ``(99, 997)``
    [common/otm3MT.cbl:L760-L762], so the two programs disagree about the value AND about
    how many fields to write. Reproduced: the guard below passes ``context.fs_reply``
    through unchanged rather than forcing 99.

N-stale-901  NEW, verified. ``ba012-Test-WS-Rec-Size-2`` splits one test into two
    statements: [common/acas019.cbl:L568-L571] MAY set ``WE-Error`` to 901, and
    [:L572] then asks whether ``WE-Error`` IS 901. Nothing zeroes it beforehand -
    ``aa010-main`` would have, but [:L279-L280] are commented out, and the RDB path arrives
    from [:L265] carrying whatever the caller left in the linkage item. A caller still
    holding 901 from an earlier failure therefore drives the entire diagnostic-and-transfer
    branch even though the two record lengths agree. Reproduced: the second test reads
    ``WE-Error`` rather than re-deriving the comparison.

N-first-call-guard-shared  NEW, verified, latent. ``A`` is a single WORKING-STORAGE ``77``
    [common/acas019.cbl:L194] gating the credential load at [:L593-L598], and BOTH entry
    points run through it - the section from [:L265] and the bare paragraph from [:L271].
    Whichever path arrives first consumes the one shot, so a flat-file CALL arriving first
    would load credentials it cannot use and leave a later RDB CALL to connect with an
    unset ``DB-Schema``. Unreachable in practice because ``File-System-Used`` is one
    system-record flag that cannot change within a run. Reproduced as written: the guard is
    keyed on the shared ``_BridgeWorkingStorage.ws_length_a`` and nothing distinguishes the
    caller.

N-nolog-on-dal-contradicted  NEW, verified, and it qualifies N-nolog-on-dal above.
    ``Ca-Process-Logs``'s own label-line comment [common/acas019.cbl:L623] claims it is
    ``*> Not called on DAL access as it does it already``, yet [:L582-L584] performs it -
    under ``Testing-1``, inside the record-size diagnostic, in a paragraph the DAL path
    runs. The claim holds for the normal path and is false for that one. Reproduced: the
    diagnostic branch calls ``acas019_ca_process_logs`` and ``ba-rdbms-exit`` does not.

N-sl904-comment-mismatch  NEW, verified. ``SL904``'s continuation comment
    [common/acas019.cbl:L209] sketches the message as ``yyy <Open-Item-Record-3 = zzz``
    while the ``string`` that builds it [:L577] writes ``"OTM3-Record = "``. The comment and
    the code disagree about the field name; the code is what runs and is what
    ``_SL904`` plus the assembly below reproduce.

===============================================================================
PART 7 - RECORDED DEVIATIONS FROM THE FROZEN SOURCE
===============================================================================

Four, all bounded, all recorded here rather than left to be discovered.

D1. VALUES ARE BOUND, NOT INTERPOLATED. The bridge builds one string containing both
    the statement and its data. This module builds the identical statement text with
    ``%s`` placeholders in place of the quoted data and binds the SAME RENDERED STRINGS
    as parameters. The bytes MySQL receives for each value are identical, so no stored
    value and no selected value changes; what changes is that a key containing a quote
    can no longer alter the statement. The rendered strings are bound - never the raw
    ``Decimal`` or ``int`` - precisely because binding the signed value would store
    something the compiled system never stored (C6).

D2. PRESENTATION IS DROPPED, per AAP section 0.3.4. The bridge's section head sets up
    curses and reads the terminal height [common/otm3MT.cbl:L371-L382]; the
    ``if Testing-2 display Display-Message-1`` sites and the handler's
    ``display ... at 2301`` / ``accept Accept-Reply at 2433`` in the record-size guard
    [common/acas019.cbl:L570-L582] have no database effect. The DIAGNOSTIC content
    becomes log records at matching severity and the CONTROL TRANSFER that follows the
    prompt - ``go to ba-rdbms-exit`` - is preserved exactly. The pause itself is not.

D3. THE FLAT-FILE MEDIUM IS INJECTED. ``aa020`` .. ``aa100`` drive a real ISAM file
    declared at [copybooks/slseloi3.cob] as ``organization indexed, access dynamic,
    status fs-Reply, record key OI3-Key``. The migrated system has no ISAM store - AAP
    section 0.3.1's target architecture contains no such layer - and rule R-1 forbids
    delegating to the compiled program. Each flat-file paragraph is therefore
    reproduced in full, with its status protocol and control flow intact, and the six
    file verbs are taken from a ``FlatFileMedium`` whose contract is nothing more than
    that SELECT clause: each verb returns the ``FS-Reply`` the file status clause would
    have written. The default medium is absent and returns ``FsReply.ERROR`` for every
    verb, after which the handler's OWN branches decide the outcome - no status is
    invented by this module. Per C2 the migrated cycle never reaches these paragraphs,
    because ``FS-Cobol-Files-Used`` is false for every in-scope scenario.

D4. THE CROSS-VIEW MOVES CARRY THE NAMED OVERLAP ONLY. ``move Open-Item-Record-3 to
    WS-OTM3-Record`` [common/acas019.cbl:L385, :L422] and its inverse
    [:L491, :L502, :L514] are group moves between two DIFFERENT arrangements of the same
    118 bytes (C3): the LINKAGE view names all 118 as fields; the FILE view names the
    first 19 - a 15-character key and a ``binary-long`` date - and leaves the other 99
    as an elementary ``filler`` [copybooks/slfdoi3.cob]. A group move is a byte copy, so
    in COBOL all 118 bytes transfer and the receiving view simply reinterprets them.

    This module has no byte buffer to copy: both views are dataclasses of typed fields
    (AAP section 0.8.1 mandates dataclasses, and R-2 forbids reconstructing packed and
    binary fields through a byte image, which is where binary floating point would be
    tempting). The
    moves therefore transfer THE FIELDS THE TWO VIEWS BOTH NAME - the 15-character key,
    as customer plus invoice, and the date - and the remaining 99 bytes stay in whichever
    view already held them. The consequence is bounded and stated plainly: on the
    FLAT-FILE path only, a record round-tripped through the file view carries its key and
    date but not its money, batch or flags.

    Nothing on the DAL path depends on this, because per C2 the RDB branch leaves the
    handler before the flat-file paragraphs and the bridge works on the LINKAGE view
    throughout - ``bb000-HV-Load`` reads ``OI-*`` and ``bb100-UnloadHVs`` writes ``OI-*``,
    never ``OI3-*``. A future ISAM medium supplying real 118-byte images would replace
    these two helpers and nothing else.

===============================================================================
PART 8 - RULE COMPLIANCE
===============================================================================

R-1  No COBOL at runtime. No process spawning, no foreign-function interface, no
     linkage to the bridge's C interface object, no import of the oracle harness. Both
     programs are reimplemented natively.
R-2  Zero binary floating-point. The eleven ``decimal(9,2)`` and two ``decimal(5,2)``
     columns are ``Decimal``; invoice number, the two dates, the two day counts, the
     batch components, type, status and ``OI3-CR`` are ``int``. The edited-picture
     emulator works on integer digit strings. No binary floating-point type is
     constructed, and no ``Decimal`` is ever built from one.
R-3  Only SELECT, INSERT, UPDATE and DELETE are issued. No schema definition of any
     kind. Execution is strictly sequential - no threads, no event loop, no process
     pool, no connection pool - matching the single-threaded COBOL, and no
     object-relational entity machinery is used.
R-4  PART 6. Every anomaly has a reproduction site carrying its locator.
R-5  PART 1 publishes both signatures; every paragraph of BOTH programs has its own
     function carrying its locator; every column cites its dictionary entry through
     ``dictionary.loader``; PART 5 records every omission.
R-6  Determinism. No clock is read, no entropy source is drawn on, no identifier is
     generated and nothing is delayed. The column list is built once at import from the
     committed dictionary and frozen, so two processes produce byte-identical statements.

Further reading:
    ``docs/migration/anomaly-log.md``            - the register, with reproducing modules
    ``docs/migration/ambiguity-resolutions.md``  - the oracle questions PART 4 raises
    ``docs/migration/traceability.md``           - paragraph-to-function, with GO TO classes
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from types import MappingProxyType
from typing import Callable, Final, Mapping, Protocol, Sequence

from acas_posting.dal.connection import (
    TransportSecurity,
    cobol_string_delimited_by_space,
    transport_category,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    EXTRA_READ_ORDERS,
    SEQUENTIAL_READ_START,
    TABLE_OF_KEYNAMES,
    CursorSlot,
    CursorState,
    CursorStateTable,
    KeyOfReference,
    OrderQuoting,
)
from acas_posting.dal.status import (
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    is_duplicate_key_bridge_level,
    log_cobol_stop,
    log_file_handler_record,
    log_handler_failure,
    mysql_1100_db_error,
    sanitise_for_log,
    start_access_type_is_valid,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.otm3 import (
    Filler1,
    Filler2,
    Oi3Key,
    OiBatch,
    OiCustomer,
    OiHeader,
    OiKey,
    OpenItemRecord3,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

# Every public name this module defines is published, matching the convention the rest of
# the layer already follows - `dal/connection.py`, `dal/status.py` and `dal/cursor_state.py`
# each list every public function and class they define. Here that matters for a second
# reason: rule R-5 requires one named function per COBOL paragraph, and a paragraph that
# cannot be reached by name from outside the module is a paragraph a traceability check
# cannot confirm. The paragraph entries are therefore grouped by program and held in COBOL
# SOURCE ORDER rather than alphabetically, so this tuple reads as the two programs' own
# paragraph inventories - `docs/migration/traceability.md` is built from exactly this list.
__all__ = (
    # -- The two published entry points (AAP section 0.4.3) -------------------------
    "dispatch",
    "otm3_mt",
    # -- Constants, models and the arithmetic primitive ----------------------------
    "ACCESS_TYPE_RELATION_ARMS",
    "BRIDGE_FUNCTIONS",
    "BRIDGE_PARAGRAPH_NUMBERS",
    "BRIDGE_PROGRAM_ID",
    "COLUMNS",
    "COLUMN_NAMES",
    "ColumnBinding",
    "FlatFileMedium",
    "HANDLER_FUNCTIONS",
    "HANDLER_PARAGRAPH_NUMBERS",
    "HANDLER_PROGRAM_ID",
    "KEY_OF_REFERENCE",
    "LOAD_SEQUENCE",
    "RECORD_LENGTH",
    "SIGN_LOSS_COLUMNS",
    "TABLE_NAME",
    "TdSaitm3Rec",
    "UNLOAD_SEQUENCE",
    "WRITE_ONLY_COLUMNS",
    "WS_LOG_FILE_NO_FLAT_FILE",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "WS_MYSQL_EDIT_PICTURE",
    "WsTempEd",
    "WsTempEdBatch",
    "WsTempEdKey",
    "ws_mysql_edit",
    # -- `otm3MT` paragraphs, source order [common/otm3MT.cbl:L370-L2192] ----------
    "ba_acas_dal_process",
    "ba010_initialise",
    "ba020_process_open",
    "ba030_process_close",
    "ba040_process_read_next",
    "ba041_reread",
    "ba050_process_read_indexed",
    "ba060_process_start",
    "ba070_process_write",
    "ba080_process_delete",
    "ba090_process_rewrite",
    "ba140_process_read_next",
    "ba141_reread",
    "ba150_process_read_next",
    "ba151_reread",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "ba999_exit",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    # `Ca-Process-Logs` and `ca-Exit` are declared by BOTH programs, so these two pairs
    # alone carry a program qualifier - see the naming note in the docstring.
    "otm3mt_ca_process_logs",
    "otm3mt_ca_exit",
    # -- `acas019` paragraphs, source order [common/acas019.cbl:L234-L629] ---------
    "aa_process_flat_file",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa041_move_inv_data",
    "aa045_eval_keys",
    "aa050_process_read_indexed",
    "aa060_process_start",
    "aa070_process_write",
    "aa080_process_delete",
    "aa090_process_rewrite",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_main_exit",
    "aa_exit",
    "ba_process_rdbms",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba_rdbms_exit",
    "acas019_ca_process_logs",
    "acas019_ca_exit",
)

_LOG: Final = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Program identity and the frozen constants both programs declare.
# ---------------------------------------------------------------------------

HANDLER_PROGRAM_ID: Final = "acas019"
BRIDGE_PROGRAM_ID: Final = "otm3MT"
TABLE_NAME: Final = "SAITM3-REC"

#: The declared record size, stated consistently by BOTH copybooks and revised from 114
#: on 08/02/17 when the invoice went from binary to ``9(8)``
#: [copybooks/slwsoi3.cob:L4-L7], [copybooks/slwsoi.cob:L6]. See docstring PART 5.
RECORD_LENGTH: Final = 118

#: ``move 3 to WS-Log-System`` [common/acas019.cbl:L240]. The legend on that same line
#: reads ``*> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Invoice`` - and anomaly N-logsystem5-meaning
#: records that ``acas013``/``acas015`` say ``5=Stock`` for the same code.
WS_LOG_SYSTEM: Final = int(LogSystem.SL)

#: ``move 15 to WS-Log-File-No`` [common/acas019.cbl:L241] - the value on the flat-file
#: path, which never reaches ``ba010`` and so never sees the overwrite below.
WS_LOG_FILE_NO_FLAT_FILE: Final = 15

#: ``move 25 to WS-Log-File-no`` [common/acas019.cbl:L557] - anomaly N-log. The RDB path
#: reaches this through ``perform ba-Process-RDBMS``, which enters the section at
#: ``ba010-Test-WS-Rec-Size``. Note the ``-No`` -> ``-no`` casing flip (N-casing), and
#: that ``acas008`` uses the same 15 -> 25 pair under ``WS-Log-System = 1``, so only the
#: ``(system, file)`` pair disambiguates the two.
WS_LOG_FILE_NO_RDB: Final = 25

#: ``WS-File-Key pic x(64)`` [copybooks/wsfnctn.cob:L52]. Every log string this module
#: builds is truncated into this width exactly as a COBOL ``MOVE`` would.
WS_FILE_KEY_WIDTH: Final = 64

#: ``WS-Log-Where pic x(231)`` [copybooks/wsfnctn.cob:L53].
WS_LOG_WHERE_WIDTH: Final = 231

#: ``77 Display-Blk pic x(75) value spaces.`` [common/acas019.cbl:L196] - the handler's own
#: screen buffer. The one ``string`` that fills it [:L573-L579] is assembled into this width
#: so the log record carries the same 75 bytes the screen would have shown, truncation
#: included; only the ``display`` itself is dropped (deviation D2).
_DISPLAY_BLK_WIDTH: Final = 75

#: ``03 SL901 pic x(31) value "SL901 Note error and hit return".``
#: [common/acas019.cbl:L207]. Displayed at 2401 immediately before the dropped ``accept``
#: [:L581, :L585], so its own instruction no longer applies.
#:
#: DECLARED AND DELIBERATELY UNREFERENCED. The declaration is a fact about the frozen
#: ``Error-Messages`` group and R-5 keeps it verbatim, but the literal's whole text is the
#: acknowledgement half of the 904 diagnostic, and quoting an acknowledgement prompt in a
#: log line is still emitting it. Only ``_SL904``, which names the error, reaches a record.
_SL901: Final = "SL901 Note error and hit return"

#: ``03 SL904 pic x(32) value "SL904 Program Error: Temp rec = ".``
#: [common/acas019.cbl:L208], with the maintainer's own continuation comment on the next
#: line: ``*>                                        yyy <Open-Item-Record-3 = zzz``. Note
#: that the comment sketches ``<Open-Item-Record-3 =`` while the ``string`` at [:L577]
#: actually writes ``"OTM3-Record = "`` - the comment and the code disagree about the
#: field name, and the code is what runs. Anomaly N-sl904-comment-mismatch; the literal
#: below is the code's.
_SL904: Final = "SL904 Program Error: Temp rec = "

#: The handler's nine-code dispatch, in the SOURCE ORDER of the ``evaluate``
#: [common/acas019.cbl:L283-L302]. Code 6 is spare, and 32/33 are absent - see
#: docstring C1. This tuple exists so a caller can ask what the HANDLER accepts without
#: reading the dispatch table below.
HANDLER_FUNCTIONS: Final = (
    int(FileFunction.OPEN),          # 1 -> aa020-Process-Open
    int(FileFunction.CLOSE),         # 2 -> aa030-Process-Close
    int(FileFunction.READ_NEXT),     # 3 -> aa040-Process-Read-Next
    int(FileFunction.READ_INDEXED),  # 4 -> aa050-Process-Read-Indexed
    int(FileFunction.WRITE),         # 5 -> aa070-Process-Write
    int(FileFunction.RE_WRITE),      # 7 -> aa090-Process-Rewrite
    int(FileFunction.DELETE),        # 8 -> aa080-Process-Delete
    int(FileFunction.START),         # 9 -> aa060-Process-Start
    # ANOMALY N-codes-32-33, THE HANDLER'S HALF: 32 and 33 are ABSENT here. The strings
    # "32" and "33" do not occur anywhere in [common/acas019.cbl], so no flat-file verb
    # exists for either, even though [copybooks/wsfnctn.cob:L103-L104] names OTM3 as their
    # consumer. Code 6 is also absent - `*> 6 is spare / unused` [:L300].
)

#: The bridge's eleven-code dispatch, in the source order of ITS ``evaluate``
#: [common/otm3MT.cbl:L406-L429]: the handler's nine, plus the two sorted reads that
#: [copybooks/wsfnctn.cob:L103-L104] declares for OTM3/OTM5. See docstring C1 - the other
#: half of anomaly N-codes-32-33, and the correction to the brief: the two codes ARE
#: implemented, by the BRIDGE, and only the handler's dispatch omits them.
BRIDGE_FUNCTIONS: Final = HANDLER_FUNCTIONS + (
    int(FileFunction.READ_BY_BATCH),  # 32 -> ba140-Process-Read-Next (Sorted-By-Batch)
    int(FileFunction.READ_BY_CUST),   # 33 -> ba150-Process-Read-Next (Sorted-By-Cust)
)

#: ``move NNN to WS-No-Paragraph`` in the handler's flat-file paragraphs. Anomaly
#: N-noparagraph-collision: 201..208 is identical to ``acas013``, ``acas015`` and
#: ``acas016``, so the number alone does not identify the handler.
HANDLER_PARAGRAPH_NUMBERS: Final = MappingProxyType(
    {
        "aa020-Process-Open": 201,           # [common/acas019.cbl:L309]
        "aa030-Process-Close": 202,          # [common/acas019.cbl:L347]
        "aa040-Process-Read-Next": 203,      # [common/acas019.cbl:L364]
        "aa050-Process-Read-Indexed": 204,   # [common/acas019.cbl:L417]
        "aa060-Process-Start": 205,          # [common/acas019.cbl:L441]
        "aa070-Process-Write": 206,          # [common/acas019.cbl:L491]
        "aa080-Process-Delete": 207,         # [common/acas019.cbl:L502]
        "aa090-Process-Rewrite": 208,        # [common/acas019.cbl:L514]
    }
)

#: ``move N to ws-No-Paragraph`` in the bridge. Two collisions inside the bridge itself:
#: ``ba140`` and ``ba150`` BOTH stamp 21, and ``ba141`` and ``ba151`` BOTH stamp 22
#: [common/otm3MT.cbl:L1010, :L1067, :L1163, :L1221], so the stamp cannot distinguish
#: the by-batch read from the by-customer read. 7, 9, 11, 12, 14..16, 18 and 19 are
#: never used by this bridge at all.
BRIDGE_PARAGRAPH_NUMBERS: Final = MappingProxyType(
    {
        "ba020-Process-Open": 1,           # [common/otm3MT.cbl:L458]
        "ba030-Process-Close": 2,          # [common/otm3MT.cbl:L479]
        "ba040-Process-Read-Next": 3,      # [common/otm3MT.cbl:L516]
        "ba041-Reread": 4,                 # [common/otm3MT.cbl:L568]
        "ba050-Process-Read-Indexed": 5,   # [common/otm3MT.cbl:L669]
        "ba050-Fetch": 6,                  # [common/otm3MT.cbl:L695]
        "ba060-Process-Start": 8,          # [common/otm3MT.cbl:L805]
        "ba070-Process-Write": 10,         # [common/otm3MT.cbl:L868]
        "ba080-Process-Delete": 13,        # [common/otm3MT.cbl:L913]
        "ba090-Process-Rewrite": 17,       # [common/otm3MT.cbl:L949]
        "ba140-Process-Read-Next": 21,     # [common/otm3MT.cbl:L1010]
        "ba141-Reread": 22,                # [common/otm3MT.cbl:L1067]
        "ba150-Process-Read-Next": 21,     # [common/otm3MT.cbl:L1163] - collides
        "ba151-Reread": 22,                # [common/otm3MT.cbl:L1221] - collides
        "ba998-Free": 20,                  # [common/otm3MT.cbl:L1306]
    }
)

#: The single key of reference, from the bridge's own metadata table
#: [common/otm3MT.scb:L249-L251] / [common/otm3MT.cbl:L248-L258]: ``OI3-KEY``, offset
#: 0001, length 0015, type ``'STR'``. Exactly ONE key exists, which is precisely what
#: makes the handler's ``if File-Key-No not = 1`` guard the only guard it needs.
#: Anomaly N-kortype: the type is populated with ``'STR'`` while its own declaration
#: comment says "Not used currently".
KEY_OF_REFERENCE: Final[KeyOfReference] = TABLE_OF_KEYNAMES[TABLE_NAME][0]

#: ``evaluate Access-Type`` [common/otm3MT.cbl:L779-L787], transcribed. Arm 9 is
#: declared and unreachable, because the guard above it admits 5..8 only - anomaly
#: N-start-997-vs-998. There is NO ``when other``, so an out-of-range value leaves
#: ``MOST-Relation`` at the spaces set immediately before the ``evaluate``.
ACCESS_TYPE_RELATION_ARMS: Final = MappingProxyType(
    {
        int(AccessType.EQUAL_TO): "=  ",          # 5  fn-equal-to
        int(AccessType.LESS_THAN): "<  ",         # 6  fn-less-than
        int(AccessType.GREATER_THAN): ">  ",      # 7  fn-greater-than
        int(AccessType.NOT_LESS_THAN): ">= ",     # 8  fn-not-less-than
        int(AccessType.NOT_GREATER_THAN): "<= ",  # 9  [ not currently used in ACAS ]
    }
)

#: The relation and low key the sequential read positions with
#: [common/otm3MT.cbl:L504-L505], through the shared table so the two modules cannot
#: drift apart.
_SEQUENTIAL_START: Final = SEQUENTIAL_READ_START[TABLE_NAME]

#: The sorted-read metadata for codes 32 and 33 - slot, predicate presence and locator -
#: taken from the shared table. The ORDER BY TEXT is NOT taken from here: see
#: :data:`_SORTED_ORDER_BY_TEXT` for why.
_EXTRA_READS: Final = EXTRA_READ_ORDERS[TABLE_NAME]

#: The ORDER BY clauses of ``ba140`` and ``ba150``, transcribed CHARACTER FOR CHARACTER
#: from the frozen literals [common/otm3MT.cbl:L1000-L1007] and [:L1153-L1159] rather
#: than rebuilt from :data:`_EXTRA_READS`. Two reasons, both fidelity:
#:
#: * The COBOL attaches ``ASC``/``DESC`` to only SOME terms, letting the rest inherit;
#:   rebuilding term by term would emit a keyword on every term and change the text.
#: * Every term is SINGLE-QUOTED, i.e. a string constant that orders nothing, and the
#:   surrounding ``WS-Where`` carries no predicate while the SELECT template always
#:   emits ``" WHERE "``. The result is a syntax error - anomaly
#:   N-sorted-order-is-a-syntax-error - and a syntax error is only reproducible if the
#:   text is reproduced exactly.
#:
#: The quoting is recorded against the shared vocabulary so the intent is unambiguous.
_SORTED_ORDER_BY_QUOTING: Final = OrderQuoting.STRING_CONSTANT
_SORTED_ORDER_BY_TEXT: Final = MappingProxyType(
    {
        # [common/otm3MT.cbl:L1000-L1007]. The prose comment above it [:L991-L993] lists
        # the terms in the REVERSE of this order - a second false comment.
        int(FileFunction.READ_BY_BATCH): (
            " ORDER BY "
            "'OI3-INVOICE', 'OI3-DAT' ASC, "
            "'OI3-TYPE' DESC, "
            "'OI3-BATCH-ITEM', 'OI3-BATCH-NOS' ASC "
        ),
        # [common/otm3MT.cbl:L1153-L1159].
        int(FileFunction.READ_BY_CUST): (
            " ORDER BY "
            "'OI3-CUSTOMER', 'OI3-DAT', "
            "'OI3-INVOICE', 'OI3-TYPE' ASC "
        ),
    }
)

#: ``move "..." to WS-File-Key`` literals, transcribed. Reproduced verbatim because
#: they are the only trace the compiled system leaves of which path it took.
_FILE_KEY_OPEN: Final = "OPEN SL OTM3"    # [common/otm3MT.cbl:L466]
_FILE_KEY_CLOSE: Final = "CLOSE SL OTM3"  # [common/otm3MT.cbl:L481]
_FILE_KEY_NO_DATA: Final = "No Data"      # [common/otm3MT.cbl:L546, :L1039, :L1189]
_FILE_KEY_SORTED: Final = "Sorted"        # [common/otm3MT.cbl:L1023, :L1176]
_FILE_KEY_EOF: Final = "EOF"              # [common/otm3MT.cbl:L610, :L1110, :L1264]
_FILE_KEY_EOF2: Final = "EOF2"            # [common/otm3MT.cbl:L629, :L1124, :L1278]
_FILE_KEY_EOF3: Final = "EOF3"            # [common/otm3MT.cbl:L638, :L1134, :L1288]
_FILE_KEY_FLAT_EOF: Final = "EOF"         # [common/acas019.cbl:L380]
_FILE_KEY_FAILED_ACTION: Final = "Failed action"  # [common/acas019.cbl:L430]

# ---------------------------------------------------------------------------
# WS-MYSQL-EDIT - the edited picture through which EVERY number becomes SQL text.
#
# `01  WS-MYSQL-EDIT      PIC -Z(18)9.9(9).`  [common/otm3MT.cbl:L226]
#
# Thirty character positions:
#
#     pos  1        the sign: '-' when negative, a SPACE when not
#     pos  2..19    eighteen Z positions: leading zeros become SPACES
#     pos 20        one 9 position: ALWAYS a digit, even for a value of zero
#     pos 21        the decimal point
#     pos 22..30    nine 9 positions: the fraction, zero-filled on the right
#
# Docstring C6 is entirely a consequence of this layout: every slice the bridge takes
# begins at or after position 11, so position 1 is in none of them and the sign is
# dropped on the way into every numeric column. The drop is therefore MECHANICAL here
# too - this module slices the same windows and never calls an absolute-value helper.
# ---------------------------------------------------------------------------

WS_MYSQL_EDIT_PICTURE: Final = "-Z(18)9.9(9)"
_EDIT_LENGTH: Final = 30
_EDIT_INTEGER_FIRST_POSITION: Final = 2
_EDIT_INTEGER_LAST_POSITION: Final = 20
_EDIT_INTEGER_POSITIONS: Final = _EDIT_INTEGER_LAST_POSITION - _EDIT_INTEGER_FIRST_POSITION + 1
_EDIT_POINT_POSITION: Final = 21
_EDIT_DECIMAL_FIRST_POSITION: Final = 22
_EDIT_DECIMAL_POSITIONS: Final = 9


def ws_mysql_edit(value: Decimal | int) -> str:
    """Build the 30-character ``WS-MYSQL-EDIT`` image of ``value``.

    Reproduces ``move <numeric> to WS-MYSQL-EDIT`` for the picture at
    [common/otm3MT.cbl:L226]. The image is what the bridge then slices; see
    :func:`_edit_slice`.

    ⭐⭐ THIS FUNCTION AND :func:`_edit_slice` TOGETHER ARE THE REPRODUCTION SITE OF ANOMALY
    N-sql-render-drops-sign (docstring C6). The ``-`` sits at position 1 of the picture and
    EVERY slice the bridge takes starts at position 11 or later - verified at
    [common/otm3MT.cbl:L1542] for ``OI3-P-C``, [:L1716] for ``OI3-DEDUCT-AMT`` and [:L1762]
    for ``OI3-CR`` - so the sign is never inside a window and every one of the 22 numeric
    columns is written unsigned regardless of what its host variable declares. That is why
    ``OI3-CR`` keeping its sign through the host variable (anomaly N-oi3-cr-sign-survives)
    changes nothing about the value stored. The drop happens by SLICING - by the window
    simply not covering position 1 - and never by taking a magnitude.

    COBOL semantics reproduced here, in the order they apply:

    * The value is aligned on the decimal point, not left- or right-justified.
    * The fraction is truncated toward zero to nine places - a plain ``MOVE`` never
      rounds, and rule R-2's ``Decimal`` arithmetic makes the truncation exact.
    * Leading zeros in positions 2..19 are suppressed to SPACES by the ``Z``; position
      20 is a ``9`` and keeps its digit, so a value of zero still shows ``0`` there.
    * Integer digits beyond the nineteen available are truncated from the HIGH ORDER
      end, which is what a COBOL ``MOVE`` into too small a receiving field does.
    * The sign occupies position 1 alone.

    Args:
        value: A ``Decimal`` or ``int``. Never a binary floating-point value: rule R-2
            forbids one anywhere in this module, and an inexact value would render an
            inexact digit string into the statement.

    Returns:
        Exactly ``_EDIT_LENGTH`` characters.
    """
    amount = value if isinstance(value, Decimal) else Decimal(int(value))
    if not amount.is_finite():
        # A non-finite value cannot arrive from the frozen schema or from the record
        # layer, both of which carry only fixed-point fields. Rather than raise - this
        # module never raises, per [common/acas019.cbl:L617] - the condition is logged
        # and rendered as zero, which is what an `initialize`d host variable holds.
        #  THE VALUE ITSELF IS NOT LOGGED. It is a monetary or quantity figure
        #  from a posting, which the safe-event schema forbids in a record
        #  (CWE-532); the table and the condition are what identify the fault, and
        #  the caller that produced it is named by the traceback of its own tests.
        #  This record is NOT a narration of frozen control flow - `ws_mysql_edit`
        #  has no such arm - it is a programming-error guard on an input rule R-2
        #  makes impossible, so it is kept at ERROR rather than removed.
        _LOG.error(
            "ws_mysql_edit received a non-finite value; rendering the zero image. "
            "No field of %s can hold one",
            TABLE_NAME,
        )
        amount = Decimal(0)

    # Split sign from digits through the value's own representation rather than by
    # negating it: that is how the picture itself separates the two, and it keeps this
    # function free of any absolute-value call while staying exact for every input.
    sign, significand, exponent = amount.as_tuple()
    negative = sign == 1
    magnitude = "".join(str(digit) for digit in significand)

    if exponent >= 0:
        # An integral value: the exponent scales the digits up, and there is no fraction.
        integer_digits = magnitude + "0" * int(exponent)
        fraction_digits = "0" * _EDIT_DECIMAL_POSITIONS
    else:
        # `-exponent` fractional digits are present. Pad on the left so the split always
        # leaves at least one integer digit, then truncate the fraction toward zero to
        # the nine positions the picture provides - a plain MOVE never rounds.
        present = int(-exponent)
        padded = magnitude.rjust(present + 1, "0")
        integer_digits = padded[:-present]
        fraction_digits = (padded[-present:] + "0" * _EDIT_DECIMAL_POSITIONS)[
            :_EDIT_DECIMAL_POSITIONS
        ]

    # `Z(18)9`: right-justify in nineteen positions and let the padding BE the zero
    # suppression, because a suppressed leading zero is exactly a space. Python's
    # `rjust` pads with spaces and `str` of a magnitude always yields at least one
    # digit, so position 20 is never blank - the `9` honoured without a special case.
    integer_image = integer_digits.lstrip("0") or "0"
    integer_image = integer_image[-_EDIT_INTEGER_POSITIONS:].rjust(
        _EDIT_INTEGER_POSITIONS
    )

    image = f"{'-' if negative else ' '}{integer_image}.{fraction_digits}"
    return image[:_EDIT_LENGTH]


def _edit_slice(image: str, start: int, length: int) -> str:
    """COBOL reference modification ``WS-MYSQL-EDIT(start:length)``, 1-based.

    Every numeric value in the bridge's INSERT and UPDATE is one or two of these
    slices; the windows are listed in docstring C6 and verified at
    [common/otm3MT.cbl:L1542], [:L1716] and [:L1762].
    """
    first = start - 1
    return image[first : first + length]


def _render_integer(value: int, digits: int) -> str:
    """Render an integer host variable as the bridge does: one slice, sign dropped.

    ``MOVE HV-OI3-INVOICE TO WS-MYSQL-EDIT`` then
    ``STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))`` [common/otm3MT.cbl:L1453-L1457].

    The window is derived from the host variable's own digit count rather than
    hard-coded, because the dictionary is the authority on that count (rule R-5). The
    integer positions end at ``_EDIT_INTEGER_LAST_POSITION``, so a ``9(n)`` host
    variable slices ``(21 - n : n)`` - which resolves to the ``(11:10)`` of
    ``HV-OI3-INVOICE`` and the ``(18:03)`` of ``HV-OI3-DEDUCT-DAYS`` exactly as the
    frozen source writes them.

    ``FUNCTION TRIM`` with no LEADING/TRAILING phrase removes BOTH ends, so the spaces
    the ``Z`` positions left disappear here. Position 20 is a ``9`` and always holds a
    digit, and it is inside every window, so the trimmed result is never empty.
    """
    start = _EDIT_INTEGER_LAST_POSITION - digits + 1
    return _edit_slice(ws_mysql_edit(value), start, digits).strip()


def _render_decimal(value: Decimal, integer_digits: int, scale: int) -> str:
    """Render a scaled host variable as the bridge does: two slices joined by a point.

    Three statements, and the asymmetry between them matters
    [common/otm3MT.cbl:L1540-L1549]::

        MOVE HV-OI3-P-C TO WS-MYSQL-EDIT
        STRING FUNCTION TRIM (WS-MYSQL-EDIT(14:07)) ...
        STRING "." ...
        STRING WS-MYSQL-EDIT(22:02) ...

    THE INTEGER SLICE IS TRIMMED AND THE FRACTION SLICE IS NOT. The integer window is
    derived exactly as in :func:`_render_integer`; the fraction window always starts at
    ``_EDIT_DECIMAL_FIRST_POSITION`` and runs for the host variable's scale, and needs no
    trimming because ``9`` positions are never suppressed. Verified for both scaled
    shapes: ``S9(07)V9(02)`` at [:L1542-L1549] and ``S9(03)V9(02)`` at [:L1716-L1723].
    """
    image = ws_mysql_edit(value)
    integer_part = _edit_slice(
        image, _EDIT_INTEGER_LAST_POSITION - integer_digits + 1, integer_digits
    ).strip()
    fraction_part = _edit_slice(image, _EDIT_DECIMAL_FIRST_POSITION, scale)
    return f"{integer_part}.{fraction_part}"


def _cobol_move_alphanumeric(value: str, width: int) -> str:
    """``MOVE`` of an alphanumeric item into ``PIC X(width)``.

    Left-justified, space-padded on the right, truncated on the right when too long -
    the receiving-field rules, not assignment.
    """
    return value[:width].ljust(width)


# ---------------------------------------------------------------------------
# The 28-column mapping, DERIVED from the committed data dictionary.
#
# AAP section 0.8.1: "Data dictionary first ... every Python field definition cites its
# entry. This ordering is a directive, not a preference - it is what prevents fields
# being transcribed by eye." Nothing below is typed out from the schema or the bridge by
# hand; it is read from `data_dictionary/acas_posting_dictionary.json` at import and
# frozen into tuples, so two processes build byte-identical statements (rule R-6).
#
# THREE SEPARATE ORDERS exist and are kept separate - anomaly N-loadorder:
#
#   COLUMNS         table ordinal order       [mysql/ACASDB.sql:L896-L926]
#   LOAD_SEQUENCE   the load's move order     [common/otm3MT.cbl:L1341-L1374]
#   UNLOAD_SEQUENCE the unload's move order   [common/otm3MT.cbl:L1386-L1413]
#
# None is derived from another. The column order comes from the column ordinal, the load
# order from each entry's own recorded load site, and the unload order is transcribed
# from the unload paragraph - which is the only one of the three the dictionary does not
# record, because two of its columns have no unload at all.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ColumnBinding:
    """One column of ``SAITM3-REC``, with everything needed to render and place it.

    Every instance is built by :func:`_build_columns` from a single
    ``dictionary.loader`` entry, so each carries its dictionary key and citation and
    nothing about it is transcribed (rule R-5).

    The render form is chosen from the BRIDGE HOST VARIABLE's picture, never from the
    copybook's storage class, because the host variable is what the statement is built
    out of. That distinction is load-bearing here: ``OI3-BATCH-NOS`` is ``9(5) COMP`` in
    the copybook and ``X(5)`` in the host variable, and it is the ``X(5)`` that decides
    the column is written as characters (anomaly N-binary-to-char). The same applies to
    ``OI3-TYPE`` and ``OI3-STATUS`` (anomaly N-numeric-to-char).
    """

    column_name: str
    ordinal: int
    dictionary_key: str
    citation: str
    quoted_column: str
    sql_type: str
    column_unsigned: bool
    is_primary_key: bool
    column_comment: str
    hv_name: str
    hv_attribute: str
    hv_picture: str
    hv_signed: bool
    hv_digits: int | None
    hv_integer_digits: int | None
    hv_scale: int | None
    hv_character_length: int | None
    copybook_field: str
    copybook_source: str
    signedness_drift: bool
    unloaded_to_record: bool
    derivation_kind: str
    derivation_expression: str
    load_source: str

    @property
    def is_character(self) -> bool:
        """True when the host variable is ``PIC X(n)`` and the value is text."""
        return self.hv_character_length is not None and self.hv_digits is None

    @property
    def is_scaled(self) -> bool:
        """True when the host variable carries a ``V9(n)`` fraction."""
        return self.hv_scale is not None and self.hv_scale > 0

    @property
    def is_derived(self) -> bool:
        """True for the two columns the bridge assembles rather than copies."""
        return self.derivation_kind != ""

    def initial_value(self) -> str | int | Decimal:
        """The value ``initialize TD-SAITM3-REC`` leaves in this host variable.

        [common/otm3MT.cbl:L1339] is the FIRST statement of the load, which is why every
        column of this table can be ``NOT NULL`` and why this module must default rather
        than omit - AAP section 0.6.2: "the Python layer must default rather than omit."
        Alphanumeric host variables become spaces at their declared width; numeric ones
        become zero at their declared scale.
        """
        if self.is_character:
            return " " * int(self.hv_character_length or 0)
        if self.is_scaled:
            return Decimal(0).scaleb(0).quantize(
                Decimal(1).scaleb(-int(self.hv_scale or 0)), rounding=ROUND_DOWN
            )
        return 0

    def coerce(self, value: str | int | Decimal) -> str | int | Decimal:
        """Apply the ``MOVE`` into this host variable, receiving-field rules and all.

        Three behaviours, in the order COBOL applies them:

        1. Alphanumeric receivers pad or truncate on the right. This is where the
           ``OI-Description`` width drift 25 -> 32 materialises as seven trailing spaces
           (anomaly N-desc-width), and where ``OI-Type`` and ``OI-Status`` stop being
           numbers (anomaly N-numeric-to-char).
        2. Scaled receivers truncate the fraction toward zero to the receiver's scale -
           never rounding, because the frozen ``MOVE`` carries no ``ROUNDED``.
        3. UNSIGNED receivers DROP THE SIGN. This is anomaly N-signloss, and it happens
           HERE - at the bridge, before any statement exists - for the four fields whose
           copybook declaration is signed and whose host variable is not. AAP section
           0.6.2: "the Python data-access layer must reproduce the bridge's conversion,
           not merely write the computed value and let MySQL complain."
        """
        if self.is_character:
            text = value if isinstance(value, str) else _display_digits(value, self)
            return _cobol_move_alphanumeric(text, int(self.hv_character_length or 0))

        if self.is_scaled:
            amount = value if isinstance(value, Decimal) else Decimal(int(value))
            amount = amount.quantize(
                Decimal(1).scaleb(-int(self.hv_scale or 0)), rounding=ROUND_DOWN
            )
            return _drop_sign_for_unsigned_receiver(amount, self)

        whole = int(value) if not isinstance(value, Decimal) else int(value.to_integral_value(rounding=ROUND_DOWN))
        return _drop_sign_for_unsigned_receiver(whole, self)

    def render(self, value: str | int | Decimal) -> str:
        """Render the host variable exactly as the bridge renders it into SQL text.

        Alphanumeric columns go through ``FUNCTION TRIM (HV-... TRAILING)``; numeric
        columns go through ``WS-MYSQL-EDIT`` and lose their sign to the slice - see
        docstring C6, verified at [common/otm3MT.cbl:L1542], [:L1716] and [:L1762].
        """
        if self.is_character:
            text = value if isinstance(value, str) else str(value)
            return text.rstrip(" ")
        if self.is_scaled:
            amount = value if isinstance(value, Decimal) else Decimal(int(value))
            return _render_decimal(
                amount, int(self.hv_integer_digits or 0), int(self.hv_scale or 0)
            )
        whole = int(value) if not isinstance(value, Decimal) else int(value)
        return _render_integer(whole, int(self.hv_digits or 0))


def _display_digits(value: int | Decimal, binding: ColumnBinding) -> str:
    """Convert a binary or display-numeric COBOL value into the digit characters a
    ``PIC X(n)`` host variable receives.

    Anomaly N-binary-to-char and anomaly N-numeric-to-char both land here. A COBOL
    ``MOVE`` of a numeric item to an alphanumeric item transfers the item's DISPLAY
    representation - unsigned digit characters, zero-filled to the sending field's digit
    count - which for ``OI-B-Nos pic 9(5) COMP`` into ``HV-OI3-BATCH-NOS PIC X(5)`` is
    five digit characters, and for ``OI-Type pic 9`` into ``X(1)`` is one.

    The sign is not part of that representation, which is a third, independent place the
    sign disappears; it is only ever visible for the four fields of anomaly N-signloss
    because those are numeric on both sides.
    """
    width = int(binding.hv_character_length or 0)
    whole = int(value)
    digits = "".join(character for character in str(whole) if character.isdigit())
    return digits.rjust(width, "0")[-width:] if width else digits


def _drop_sign_for_unsigned_receiver(
    value: int | Decimal, binding: ColumnBinding
) -> int | Decimal:
    """The single named helper for anomaly N-signloss.

    Applies to exactly the four fields listed in :data:`SIGN_LOSS_COLUMNS` - the ones
    the dictionary reports a signedness drift for - and to no others. ``OI3-CR``,
    ``OI3-DEDUCT-AMT`` and ``OI3-DEDUCT-VAT`` are signed at all three layers and pass
    through untouched here; they lose their sign later, at the render, along with every
    other numeric column (docstring C6).

    A COBOL ``MOVE`` into an unsigned receiver stores the ABSOLUTE VALUE. It is produced
    here by subtracting from zero rather than by an absolute-value call, so the arithmetic
    stays visibly exact and rule R-2's ``Decimal``-only discipline is self-evident.
    Nothing is raised, nothing is clamped: AAP section 0.6.8 makes the exact stored value
    an oracle question, recorded in ``docs/migration/ambiguity-resolutions.md``.
    """
    if binding.hv_signed or value >= 0:
        return value
    #  NO RECORD HERE. The frozen `move` into an unsigned host variable
    #  [see `binding.load_source`] narrows in silence - it writes no status, sets no
    #  flag and displays nothing - so a record was invented (R-4), and the silence
    #  IS anomaly N-signloss as the register describes it. The record it replaced
    #  also interpolated the value being narrowed, which is a posted figure
    #  (CWE-532). The anomaly is documented in `ANOMALIES` below and in
    #  `docs/migration/anomaly-log.md`, where a reader can find it without an
    #  operator having to see it once per column per row.
    return 0 - value


def _load_line(binding: ColumnBinding) -> int:
    """The source line of this column's ``move`` inside ``bb000-HV-Load``.

    Each dictionary entry records its own load site, e.g.
    ``common/otm3MT.cbl:L1345`` for the derived key. Ordering the columns on this number
    reconstructs the load's move order from the dictionary rather than from a hand-typed
    list, which is what AAP section 0.8.1's "data dictionary first" directive asks for.
    A column with no recorded site sorts last rather than failing the import.
    """
    _, _, line = binding.load_source.rpartition(":L")
    return int(line) if line.isdigit() else 1 << 30


def _build_columns() -> tuple[ColumnBinding, ...]:
    """Read the 28 columns of ``SAITM3-REC`` from the committed data dictionary.

    ``loader.entries_for_table`` returns them in COLUMN-ORDINAL order, which is the
    order the INSERT and the UPDATE name them in
    [common/otm3MT.cbl:L1418-L1798, :L1799-L2183]. Called exactly once, at import.
    """
    bindings: list[ColumnBinding] = []
    for entry in loader.entries_for_table(TABLE_NAME):
        column = entry.column
        host_variable = entry.bridge_host_variable
        copybook_field = entry.copybook
        derivation = entry.derivation
        bindings.append(
            ColumnBinding(
                column_name=column.name,
                ordinal=int(column.ordinal),
                dictionary_key=entry.key,
                citation=loader.cite(entry.key),
                quoted_column=quote_identifier(column.name),
                sql_type=column.sql_type,
                column_unsigned=bool(column.unsigned),
                is_primary_key=bool(column.is_primary_key),
                column_comment=column.comment or "",
                hv_name=host_variable.name,
                hv_attribute=host_variable.name.replace("-", "_").lower(),
                hv_picture=host_variable.picture or "",
                hv_signed=bool(host_variable.signed),
                hv_digits=host_variable.digits,
                hv_integer_digits=host_variable.integer_digits,
                hv_scale=host_variable.scale,
                hv_character_length=host_variable.character_length,
                copybook_field=copybook_field.name if copybook_field else "",
                # `CopybookField.source` is ALREADY a full `<path>:L<n>` locator - the
                # dictionary stores it that way, and `.file` is the same path without the
                # line. Taking `.source` verbatim is what keeps every citation in this
                # module in the one form rule R-4 requires; composing it from `.file`
                # would double the path.
                copybook_source=(
                    copybook_field.source if copybook_field is not None else ""
                ),
                signedness_drift=bool(loader.drift_for(entry.key).signedness),
                unloaded_to_record=bool(host_variable.unloaded_to_record),
                derivation_kind=(
                    str(derivation.kind.value) if derivation is not None else ""
                ),
                derivation_expression=(
                    derivation.expression if derivation is not None else ""
                ),
                load_source=host_variable.load_source or "",
            )
        )
    return tuple(bindings)


#: The 28 columns in TABLE ORDINAL order [mysql/ACASDB.sql:L896-L926]. This is the order
#: the INSERT and the UPDATE name them in, and the order ``harness/dump_tables.py`` sees.
COLUMNS: Final[tuple[ColumnBinding, ...]] = _build_columns()

#: The column names, in the same order. Frozen so the statement text cannot vary between
#: processes (rule R-6).
COLUMN_NAMES: Final[tuple[str, ...]] = tuple(binding.column_name for binding in COLUMNS)

_COLUMN_BY_NAME: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.column_name: binding for binding in COLUMNS}
)

#: The four host variables anomaly N-signloss applies to, derived from the dictionary's
#: own signedness drift rather than listed by hand - ``OI3-DAT``, ``OI3-DEDUCT-DAYS``,
#: ``OI3-DAYS``, ``OI3-DATE-CLEARED``. ``OI3-CR`` is deliberately NOT among them
#: [common/otm3MT.cbl:L327]; see anomaly N-oi3-cr-sign-survives.
SIGN_LOSS_COLUMNS: Final[tuple[str, ...]] = tuple(
    binding.column_name for binding in COLUMNS if binding.signedness_drift
)

#: The two columns the bridge writes and never reads back - anomaly
#: N-two-write-only-columns. Derived from the dictionary's ``unloaded_to_record`` flag,
#: which the generator took from the unload paragraph itself
#: [common/otm3MT.cbl:L1386-L1413]. Both are also the only two DERIVED columns, which is
#: what makes the asymmetry survivable: on a read the record's own components are
#: authoritative and the derived forms are simply not needed.
WRITE_ONLY_COLUMNS: Final[tuple[str, ...]] = tuple(
    binding.column_name for binding in COLUMNS if not binding.unloaded_to_record
)

#: ``bb000-HV-Load``'s move order [common/otm3MT.cbl:L1341-L1374], derived by ordering
#: the columns on the load site each dictionary entry records for itself. The resulting
#: order is INVOICE, CUSTOMER, KEY, BATCH-NOS, BATCH-ITEM, BATCH, DAT, TYPE,
#: DESCRIPTION, HOLD-FLAG, UNAPL, the nine money fields, STATUS, DEDUCT-DAYS,
#: DEDUCT-AMT, DEDUCT-VAT, DAYS, CR, APPLIED, DATE-CLEARED - which is NOT the column
#: order: the two derived columns are assembled AFTER their components, so ``OI3-KEY``
#: is third and ``OI3-BATCH`` sixth rather than first and fifth (anomaly N-loadorder).
LOAD_SEQUENCE: Final[tuple[str, ...]] = tuple(
    binding.column_name
    for binding in sorted(
        COLUMNS, key=lambda item: (_load_line(item), item.ordinal)
    )
)

#: ``bb100-UnloadHVs``'s move order [common/otm3MT.cbl:L1386-L1413], TRANSCRIBED because
#: it is the one order the dictionary cannot supply - it records only WHETHER a column is
#: unloaded, not where. Twenty-six entries for twenty-eight columns, and the two missing
#: are the two derived ones. Note ``OI3-DAT`` moves THIRD here, straight after CUSTOMER,
#: where the load moves it seventh, after the whole batch block.
UNLOAD_SEQUENCE: Final[tuple[str, ...]] = (
    "OI3-INVOICE",       # [common/otm3MT.cbl:L1386]
    "OI3-CUSTOMER",      # [common/otm3MT.cbl:L1387]
    "OI3-DAT",           # [common/otm3MT.cbl:L1388]
    "OI3-BATCH-NOS",     # [common/otm3MT.cbl:L1390]
    "OI3-BATCH-ITEM",    # [common/otm3MT.cbl:L1391]
    "OI3-TYPE",          # [common/otm3MT.cbl:L1393]
    "OI3-DESCRIPTION",   # [common/otm3MT.cbl:L1394]
    "OI3-HOLD-FLAG",     # [common/otm3MT.cbl:L1395]
    "OI3-UNAPL",         # [common/otm3MT.cbl:L1396]
    "OI3-P-C",           # [common/otm3MT.cbl:L1397]
    "OI3-NET",           # [common/otm3MT.cbl:L1398]
    "OI3-EXTRA",         # [common/otm3MT.cbl:L1399]
    "OI3-CARRIAGE",      # [common/otm3MT.cbl:L1400]
    "OI3-VAT",           # [common/otm3MT.cbl:L1401]
    "OI3-DISCOUNT",      # [common/otm3MT.cbl:L1402]
    "OI3-E-VAT",         # [common/otm3MT.cbl:L1403]
    "OI3-C-VAT",         # [common/otm3MT.cbl:L1404]
    "OI3-PAID",          # [common/otm3MT.cbl:L1405]
    "OI3-STATUS",        # [common/otm3MT.cbl:L1406]
    "OI3-DEDUCT-DAYS",   # [common/otm3MT.cbl:L1407]
    "OI3-DEDUCT-AMT",    # [common/otm3MT.cbl:L1408]
    "OI3-DEDUCT-VAT",    # [common/otm3MT.cbl:L1409]
    "OI3-DAYS",          # [common/otm3MT.cbl:L1410]
    "OI3-CR",            # [common/otm3MT.cbl:L1411]
    "OI3-APPLIED",       # [common/otm3MT.cbl:L1412]
    "OI3-DATE-CLEARED",  # [common/otm3MT.cbl:L1413]
)


def _verify_unload_sequence() -> None:
    """Cross-check the transcribed unload order against the dictionary's own flags.

    :data:`UNLOAD_SEQUENCE` is the one of the three orders that had to be typed out, so
    it is the one that can be mistyped. The dictionary independently records, per column,
    whether the unload paragraph mentions it; the two views must agree exactly - 26
    names, and the two absentees exactly :data:`WRITE_ONLY_COLUMNS`.

    A disagreement is logged rather than raised. Raising here would make a diagnostic
    unable to be imported, and this module's contract is that it never raises
    [common/acas019.cbl:L617].
    """
    transcribed = set(UNLOAD_SEQUENCE)
    expected = {binding.column_name for binding in COLUMNS if binding.unloaded_to_record}
    if transcribed != expected or len(UNLOAD_SEQUENCE) != len(transcribed):
        _LOG.error(
            "UNLOAD_SEQUENCE disagrees with the data dictionary for %s: "
            "only-in-transcription=%s only-in-dictionary=%s duplicates=%d. "
            "The authority is [common/otm3MT.cbl:L1386-L1413]",
            TABLE_NAME,
            sorted(transcribed - expected),
            sorted(expected - transcribed),
            len(UNLOAD_SEQUENCE) - len(transcribed),
        )
    # The success arm emits NOTHING. A per-import summary of the column counts is a
    # restatement of the data dictionary, which is the authority for all of it and is
    # committed as an artifact; logging it made every import of this module write a
    # record no operator acts on. Only the DISAGREEMENT above is reportable.


_verify_unload_sequence()


# ---------------------------------------------------------------------------
# TD-SAITM3-REC - the bridge's host-variable group.
#
# `/MYSQL VAR\  ACASDB  TABLE=SAITM3-REC,HV`  [common/otm3MT.cbl:L293-L296]
# `01  TD-SAITM3-REC.`                        [common/otm3MT.cbl:L301-L329]
#
# The 28 host variables in DECLARATION order. This group is the layer at which anomaly
# N-signloss happens and the layer at which anomaly N-oi3-cr-sign-survives is true; the
# render that follows is where docstring C6 takes the sign away again.
#
# The other `/MYSQL-END\` markers in the file, at [:L468] and [:L485], and the
# per-statement `TABLE=SAITM3-REC` blocks from [:L521] onward, are translator artefacts
# repeating the same declaration. This group is the authoritative one.
# ---------------------------------------------------------------------------


@dataclass
class TdSaitm3Rec:
    """The host-variable group, one attribute per column, in declaration order.

    Attribute names are the host-variable names lowercased with hyphens replaced, and
    :attr:`ColumnBinding.hv_attribute` is derived the same way from the dictionary, so
    the generic accessors below and these declarations cannot drift apart.

    The literal defaults document what ``initialize TD-SAITM3-REC`` leaves behind; use
    :meth:`initialize` to construct one, because that reads the widths and scales from
    the dictionary and is therefore the authority.
    """

    hv_oi3_key: str = " " * 15                    # PIC X(15)          [:L302]
    hv_oi3_customer: str = " " * 7                # PIC X(7)           [:L303]
    hv_oi3_invoice: int = 0                       # PIC 9(10) COMP     [:L304]
    hv_oi3_dat: int = 0                           # PIC 9(10) COMP     [:L305]
    hv_oi3_batch: str = " " * 8                   # PIC X(8)           [:L306]
    hv_oi3_batch_nos: str = " " * 5               # PIC X(5)           [:L307]
    hv_oi3_batch_item: str = " " * 3              # PIC X(3)           [:L308]
    hv_oi3_type: str = " "                        # PIC X(1)           [:L309]
    hv_oi3_description: str = " " * 32            # PIC X(32)          [:L310]
    hv_oi3_hold_flag: str = " "                   # PIC X(1)           [:L311]
    hv_oi3_unapl: str = " "                       # PIC X(1)           [:L312]
    hv_oi3_p_c: Decimal = Decimal("0.00")         # PIC S9(07)V9(02)   [:L313]
    hv_oi3_net: Decimal = Decimal("0.00")         # PIC S9(07)V9(02)   [:L314]
    hv_oi3_extra: Decimal = Decimal("0.00")       # PIC S9(07)V9(02)   [:L315]
    hv_oi3_carriage: Decimal = Decimal("0.00")    # PIC S9(07)V9(02)   [:L316]
    hv_oi3_vat: Decimal = Decimal("0.00")         # PIC S9(07)V9(02)   [:L317]
    hv_oi3_discount: Decimal = Decimal("0.00")    # PIC S9(07)V9(02)   [:L318]
    hv_oi3_e_vat: Decimal = Decimal("0.00")       # PIC S9(07)V9(02)   [:L319]
    hv_oi3_c_vat: Decimal = Decimal("0.00")       # PIC S9(07)V9(02)   [:L320]
    hv_oi3_paid: Decimal = Decimal("0.00")        # PIC S9(07)V9(02)   [:L321]
    hv_oi3_status: str = " "                      # PIC X(1)           [:L322]
    hv_oi3_deduct_days: int = 0                   # PIC 9(03) COMP     [:L323]
    hv_oi3_deduct_amt: Decimal = Decimal("0.00")  # PIC S9(03)V9(02)   [:L324]
    hv_oi3_deduct_vat: Decimal = Decimal("0.00")  # PIC S9(03)V9(02)   [:L325]
    hv_oi3_days: int = 0                          # PIC 9(03) COMP     [:L326]
    hv_oi3_cr: int = 0                            # PIC S9(10) COMP    [:L327]  SIGNED
    hv_oi3_applied: str = " "                     # PIC X(1)           [:L328]
    hv_oi3_date_cleared: int = 0                  # PIC 9(10) COMP     [:L329]

    @classmethod
    def initialize(cls) -> TdSaitm3Rec:
        """``initialize TD-SAITM3-REC`` [common/otm3MT.cbl:L1339].

        The FIRST statement of the load, and the reason every column of this table can be
        declared ``NOT NULL``: an unset host variable holds zero or spaces, never a
        database null. Widths and scales come from the dictionary.
        """
        group = cls()
        for binding in COLUMNS:
            setattr(group, binding.hv_attribute, binding.initial_value())
        return group

    def value_of(self, binding: ColumnBinding) -> str | int | Decimal:
        """Read one host variable."""
        return getattr(self, binding.hv_attribute)

    def store(self, binding: ColumnBinding, value: str | int | Decimal) -> None:
        """``move <record field> to <host variable>`` - the MOVE, not an assignment.

        :meth:`ColumnBinding.coerce` applies the receiving-field rules, which is where
        anomaly N-signloss, anomaly N-binary-to-char and anomaly N-numeric-to-char all
        take effect.
        """
        setattr(self, binding.hv_attribute, binding.coerce(value))

    def rendered(self, binding: ColumnBinding) -> str:
        """The SQL text form of one host variable - see :meth:`ColumnBinding.render`."""
        return binding.render(self.value_of(binding))


# ---------------------------------------------------------------------------
# The staging records the two derived columns are assembled in.
#
# `*> TESING data`                             [common/otm3MT.cbl:L228]  (typo, kept)
# `01  WS-Temp-ED-Row     pic 9(7).`           [common/otm3MT.cbl:L230]
# `01  WS-Temp-ED-Key.`                        [common/otm3MT.cbl:L232-L234]
# `01  WS-Temp-ED-Batch.`                      [common/otm3MT.cbl:L236-L238]
# `01  WS-Temp-ED-Batch9 redefines ... 9(8).`  [common/otm3MT.cbl:L239-L240]
#
# Anomaly N-casing: the key group is DECLARED `WS-Temp-ED-Key` and REFERENCED
# `WS-Temp-Ed-Key` [:L1345]; its children are declared `WS-Temp-Ed-Customer` /
# `WS-Temp-Ed-Invoice` in the same breath as `WS-Temp-ED-Batch-Nos`. Recorded, not fixed.
# ---------------------------------------------------------------------------


@dataclass
class WsTempEdKey:
    """``WS-Temp-ED-Key`` - the 15-character primary key, assembled from two fields.

    Anomaly N-two-write-only-columns begins here. The group is CUSTOMER then INVOICE by
    declaration [common/otm3MT.cbl:L233-L234], and the load fills it INVOICE FIRST
    [:L1341] and CUSTOMER SECOND [:L1343] - the reverse of declaration order - before
    moving the whole group into ``HV-OI3-KEY`` [:L1345]. Both orders are reproduced: the
    fields are filled in the load's order and read in the declaration's order.
    """

    ws_temp_ed_customer: str = " " * 7  # pic x(7)  [common/otm3MT.cbl:L233]
    ws_temp_ed_invoice: int = 0         # pic 9(8)  [common/otm3MT.cbl:L234]

    @property
    def image(self) -> str:
        """The group's 15 bytes: ``x(7)`` then ``9(8)``, in DECLARATION order.

        ``move WS-Temp-Ed-Key to HV-OI3-KEY`` [common/otm3MT.cbl:L1345] - the statement
        with no terminating period between punctuated neighbours (anomaly N-punctuation).
        """
        customer = _cobol_move_alphanumeric(self.ws_temp_ed_customer, 7)
        invoice = str(int(self.ws_temp_ed_invoice)).rjust(8, "0")[-8:]
        return f"{customer}{invoice}"


@dataclass
class WsTempEdBatch:
    """``WS-Temp-ED-Batch`` and its ``pic 9(8)`` redefinition ``WS-Temp-ED-Batch9``.

    The second half of anomaly N-two-write-only-columns, and the whole of anomaly
    N-binary-to-char: ``OI-Batch`` is a ``COMP`` group in the copybook
    [copybooks/slwsoi.cob:L16-L18] and all three of its columns are ``char``, because the
    binary components are staged into these DISPLAY digit fields on the way
    [common/otm3MT.cbl:L1347-L1351]. Integers are never stored.
    """

    ws_temp_ed_batch_nos: int = 0   # pic 9(5)  [common/otm3MT.cbl:L237]
    ws_temp_ed_batch_item: int = 0  # pic 999   [common/otm3MT.cbl:L238]

    @property
    def batch9(self) -> str:
        """``WS-Temp-ED-Batch9`` - the same 8 bytes read as one ``pic 9(8)``.

        ``move WS-Temp-ED-Batch9 to HV-OI3-BATCH`` [common/otm3MT.cbl:L1351]. Reading the
        group through the redefinition is what turns two numbers into one 8-digit string,
        and it is why the batch ends up stored THREE TIMES per row - whole here, and
        component by component in ``OI3-BATCH-NOS`` / ``OI3-BATCH-ITEM``, which the
        schema flags ``COMMENT 'Batch content'`` (anomaly N-batch-triple).
        """
        nos = str(int(self.ws_temp_ed_batch_nos)).rjust(5, "0")[-5:]
        item = str(int(self.ws_temp_ed_batch_item)).rjust(3, "0")[-3:]
        return f"{nos}{item}"


@dataclass
class WsTempEd:
    """``WS-Temp-ED`` - the HANDLER's own logging-key builder, not the bridge's.

    [common/acas019.cbl:L202-L204], verbatim::

        01  WS-Temp-ED.
            03  ws-temp-ed-1       pic x(7).    *> Cust #
            03  WS-Temp-ed-2       pic 9(8).    *> Inv  #

    Anomaly N-casing in its purest form: three casings of one name in three consecutive
    lines. The shape is identical to the bridge's :class:`WsTempEdKey` - 7 characters then
    8 digits - but it is a different group in a different program used for a different
    purpose, so it is modelled separately rather than shared. ``aa041-Move-Inv-Data``
    fills it and moves it to ``WS-File-Key``.
    """

    ws_temp_ed_1: str = " " * 7  # pic x(7)  Cust #  [common/acas019.cbl:L203]
    ws_temp_ed_2: int = 0        # pic 9(8)  Inv  #  [common/acas019.cbl:L204]

    @property
    def image(self) -> str:
        """The group's 15 bytes, in declaration order - customer then invoice."""
        customer = _cobol_move_alphanumeric(self.ws_temp_ed_1, 7)
        invoice = str(int(self.ws_temp_ed_2)).rjust(8, "0")[-8:]
        return f"{customer}{invoice}"


# ---------------------------------------------------------------------------
# THE THREE RECORD VIEWS over the same 118 bytes - docstring C3.
#
#   LINKAGE view  `copy "slwsoi.cob" replacing OI-Header by WS-OTM3-Record`
#                 [common/acas019.cbl:L215] and [common/otm3MT.cbl:L345-L346].
#                 The field layout. BOTH programs see this one, identically - which is
#                 the correction C3 records against this module's brief.
#   CALLER view   [copybooks/slwsoi3.cob:L9-L19] - a flat `pic x(118)` with
#                 `Open-Item-Record-3` and `OI-Header` redefining it. Working storage in
#                 the calling program; `acas019` does not copy it.
#   FILE view     [copybooks/slfdoi3.cob] - a STANDALONE `01 Open-Item-Record-3`, not a
#                 redefines, carrying its own revision date (20/08/17) against the caller
#                 view's 08/02/17, and a `filler pic x(99)` that leaves it blind to 99 of
#                 the 118 bytes. Selected by [copybooks/slseloi3.cob] as
#                 `organization indexed, access dynamic, status fs-Reply,
#                  record key OI3-Key`.
#
# Three arrangements, three declarations, one agreed size of 118 bytes. The handler moves
# between the linkage view and the file view constantly - `move Open-Item-Record-3 to
# WS-OTM3-Record` [common/acas019.cbl:L385] before a read is used, and `move
# WS-OTM3-Record to Open-Item-Record-3` before every write, rewrite and delete.
# ---------------------------------------------------------------------------


def _initialize_oi_header(*, with_filler: bool) -> OiHeader:
    """``initialize WS-OTM3-Record`` over the LINKAGE view, with or without ``FILLER``.

    Anomaly N-initialize, and a verified refinement of it. The bridge writes
    ``initialize WS-OTM3-Record with filler`` at three sites
    [common/otm3MT.cbl:L626, :L1123, :L1277] and the plain form at one [:L1384] - the
    widest such split in the checkout.

    VERIFIED: over THIS view the two forms have the SAME effect. ``INITIALIZE`` acts on
    elementary items, and the ``FILLER`` phrase extends it to elementary items NAMED
    filler. ``copybooks/slwsoi.cob`` declares two FILLER GROUPS - at [:L14] and [:L35] -
    and NOT ONE elementary FILLER item, because every leaf under them is named
    (``OI-Date``, ``OI-P-C`` and so on). So the phrase has nothing extra to reach and the
    inconsistency is cosmetic HERE.

    It is NOT cosmetic over the FILE view, which does declare an elementary
    ``filler pic x(99)``; see :func:`_initialize_open_item_record_3`. The parameter is
    kept, and every call site passes it explicitly, so that each of the four sites records
    which form the frozen source used rather than silently collapsing them.
    """
    # NO RECORD HERE. `initialize` displays nothing, and the equivalence argument the
    # record used to carry is an argument about the SOURCE, which belongs in this
    # docstring - where it is - and not in a line emitted once per record initialised.
    return OiHeader(
        oi_key=OiKey(
            oi_customer=OiCustomer(oi_nos=" " * 6, oi_check=0),
            oi_invoice=0,
        ),
        filler_1=Filler1(
            oi_date=0,
            oi_batch=OiBatch(oi_b_nos=0, oi_b_item=0),
            oi_type=0,
            oi_description=" " * 25,
            oi_hold_flag=" ",
            oi_unapl=" ",
            filler_2=Filler2(
                oi_p_c=Decimal("0.00"),
                oi_net=Decimal("0.00"),
                # `OI-Approp redefines OI-Net` [copybooks/slwsoi.cob:L38-L39] - the same
                # bytes under a second name, which is why it has no column of its own
                # (anomaly N-oi-approp-redefine). Initialised to match `oi_net`.
                oi_approp=Decimal("0.00"),
                oi_extra=Decimal("0.00"),
                oi_carriage=Decimal("0.00"),
                oi_vat=Decimal("0.00"),
                oi_discount=Decimal("0.00"),
                oi_e_vat=Decimal("0.00"),
                oi_c_vat=Decimal("0.00"),
                oi_paid=Decimal("0.00"),
            ),
            oi_status=0,
            oi_deduct_days=0,
            oi_deduct_amt=Decimal("0.00"),
            oi_deduct_vat=Decimal("0.00"),
            oi_days=0,
            oi_cr=0,
            oi_applied=" ",
            oi_date_cleared=0,
        ),
    )


def _copy_oi_header(source: OiHeader, target: OiHeader) -> None:
    """Overwrite ``target``'s fields from ``source`` - a group move between two OI-Headers.

    ``bb100-UnloadHVs`` writes into ``WS-OTM3-Record``, which is the LINKAGE item the
    CALLER owns [common/otm3MT.cbl:L611-L615] - the bridge does not return a record, it
    mutates the caller's. :func:`bb100_unload_hvs` builds a fresh record because that is
    what makes it independently testable, so this copies the result back into the linkage
    item, field by field, exactly as the group move would.

    ``oi_approp`` is copied along with ``oi_net`` because the two names address the same
    bytes [copybooks/slwsoi.cob:L38-L39]; letting them diverge would be a fiction the
    118-byte record cannot represent.
    """
    target.oi_key.oi_customer.oi_nos = source.oi_key.oi_customer.oi_nos
    target.oi_key.oi_customer.oi_check = source.oi_key.oi_customer.oi_check
    target.oi_key.oi_invoice = source.oi_key.oi_invoice
    source_filler, target_filler = source.filler_1, target.filler_1
    target_filler.oi_date = source_filler.oi_date
    target_filler.oi_batch.oi_b_nos = source_filler.oi_batch.oi_b_nos
    target_filler.oi_batch.oi_b_item = source_filler.oi_batch.oi_b_item
    target_filler.oi_type = source_filler.oi_type
    target_filler.oi_description = source_filler.oi_description
    target_filler.oi_hold_flag = source_filler.oi_hold_flag
    target_filler.oi_unapl = source_filler.oi_unapl
    source_money, target_money = source_filler.filler_2, target_filler.filler_2
    target_money.oi_p_c = source_money.oi_p_c
    target_money.oi_net = source_money.oi_net
    target_money.oi_approp = source_money.oi_approp
    target_money.oi_extra = source_money.oi_extra
    target_money.oi_carriage = source_money.oi_carriage
    target_money.oi_vat = source_money.oi_vat
    target_money.oi_discount = source_money.oi_discount
    target_money.oi_e_vat = source_money.oi_e_vat
    target_money.oi_c_vat = source_money.oi_c_vat
    target_money.oi_paid = source_money.oi_paid
    target_filler.oi_status = source_filler.oi_status
    target_filler.oi_deduct_days = source_filler.oi_deduct_days
    target_filler.oi_deduct_amt = source_filler.oi_deduct_amt
    target_filler.oi_deduct_vat = source_filler.oi_deduct_vat
    target_filler.oi_days = source_filler.oi_days
    target_filler.oi_cr = source_filler.oi_cr
    target_filler.oi_applied = source_filler.oi_applied
    target_filler.oi_date_cleared = source_filler.oi_date_cleared


def _copy_open_item_record_3(
    source: OpenItemRecord3, target: OpenItemRecord3
) -> None:
    """Overwrite ``target``'s fields from ``source`` - a group move between two FILE views.

    The ``read`` verbs deliver a record into the file's own record area, which is the
    handler's persistent ``01 Open-Item-Record-3`` [copybooks/slfdoi3.cob]. The injected
    medium (deviation D3) returns a fresh object instead, so this writes it into the
    persistent one - which is what makes ``aa040``'s ``initialize`` at
    [common/acas019.cbl:L379] observable across CALLs.

    All three fields transfer, ``filler_1`` included: this is a copy WITHIN one view, so
    deviation D4's named-overlap limitation does not apply.
    """
    target.oi3_key.oi3_customer = source.oi3_key.oi3_customer
    target.oi3_key.oi3_invoice = source.oi3_key.oi3_invoice
    target.oi3_date = source.oi3_date
    target.filler_1 = source.filler_1


def _initialize_oi_header_in_place(record: OiHeader, *, with_filler: bool) -> None:
    """``initialize WS-OTM3-Record with filler`` applied to the CALLER's record.

    [common/otm3MT.cbl:L626, :L1123, :L1277] - the three ``with filler`` sites, all inside
    a reread's error branch. The linkage item belongs to the caller, so the initialise
    must land there rather than on a copy; :func:`_initialize_oi_header` supplies the
    initial values and this writes them across.
    """
    _copy_oi_header(_initialize_oi_header(with_filler=with_filler), record)


def _initialize_open_item_record_3(
    record: OpenItemRecord3, *, with_filler: bool
) -> OpenItemRecord3:
    """``initialize Open-Item-Record-3`` over the FILE view [common/acas019.cbl:L379].

    Here the ``FILLER`` phrase DOES change the outcome, because the file view declares an
    elementary ``filler pic x(99)`` [copybooks/slwsoi3.cob:L16] holding 99 of the 118
    bytes. The frozen statement at [common/acas019.cbl:L379] is the PLAIN form, so those
    99 bytes are left EXACTLY AS THEY WERE while the key and the date go to their initial
    values. Reproduced: ``filler_1`` is carried across untouched unless ``with_filler``.

    This is the sharp end of anomaly N-initialize, and it is why the handler follows every
    read with ``move Open-Item-Record-3 to WS-OTM3-Record`` [:L385] - the short view alone
    cannot see the bytes that matter.
    """
    return OpenItemRecord3(
        oi3_key=Oi3Key(oi3_customer=" " * 7, oi3_invoice=0),
        oi3_date=0,
        filler_1=(" " * 99) if with_filler else record.filler_1,
    )


def _blank_open_item_record_3() -> OpenItemRecord3:
    """A file-view record with every byte at its initial value.

    Used only where the handler has no prior record to preserve, so the distinction
    :func:`_initialize_open_item_record_3` draws does not arise.
    """
    return OpenItemRecord3(
        oi3_key=Oi3Key(oi3_customer=" " * 7, oi3_invoice=0),
        oi3_date=0,
        filler_1=" " * 99,
    )


def _oi_key_image(record: OiHeader) -> str:
    """``WS-OTM3-Record (1:15)`` - the 15 bytes the bridge slices for every predicate.

    Every ``WS-Where`` the bridge builds takes the key straight out of the RECORD BUFFER
    rather than out of a host variable: ``WS-OTM3-Record (K:L)`` with ``K`` and ``L``
    taken from the key metadata table [common/otm3MT.cbl:L653-L654, :L662]. Since
    ``KOR-offset`` is 1 and ``KOR-length`` is 15, that slice is exactly the ``OI-key``
    group - ``OI-Customer`` ``x(6)`` plus ``OI-Check`` ``9`` plus ``OI-Invoice`` ``9(8)``.
    """
    customer = _cobol_move_alphanumeric(record.oi_key.oi_customer.oi_nos, 6)
    check = str(int(record.oi_key.oi_customer.oi_check)).rjust(1, "0")[-1:]
    invoice = str(int(record.oi_key.oi_invoice)).rjust(8, "0")[-8:]
    return f"{customer}{check}{invoice}"


def _oi_customer_image(record: OiHeader) -> str:
    """``OI-Customer`` as the 7 bytes a group move transfers.

    ``move OI-Customer to HV-OI3-CUSTOMER`` [common/otm3MT.cbl:L1343] moves a GROUP to
    ``PIC X(7)``, so the transfer is byte-for-byte: ``OI-Nos`` ``x(6)`` followed by
    ``OI-Check`` ``9`` rendered as one digit character. The two children have no columns
    of their own - the group is flattened into ``OI3-CUSTOMER`` and that is the whole of
    their representation (docstring PART 5).
    """
    nos = _cobol_move_alphanumeric(record.oi_key.oi_customer.oi_nos, 6)
    check = str(int(record.oi_key.oi_customer.oi_check)).rjust(1, "0")[-1:]
    return f"{nos}{check}"


def _oi3_key_image(record: OpenItemRecord3) -> str:
    """``Open-Item-Record-3``'s own 15-byte key: ``OI3-Customer`` ``x(7)`` + ``9(8)``.

    The file view collapses the caller's ``x(6)`` + ``9`` customer into a single ``x(7)``
    [copybooks/slwsoi3.cob:L13], so the two 15-byte images coincide byte for byte while
    being described differently - which is what lets the handler move between the views.
    """
    customer = _cobol_move_alphanumeric(record.oi3_key.oi3_customer, 7)
    invoice = str(int(record.oi3_key.oi3_invoice)).rjust(8, "0")[-8:]
    return f"{customer}{invoice}"


# ---------------------------------------------------------------------------
# bb000-HV-Load  Section.    [common/otm3MT.cbl:L1331]
#   "Load the Host variables with data from the passed record"
#
# Performed from ba070-Process-Write [:L863] - "move WS-OTM3-Record fields to HV fields" -
# and from ba090-Process-Rewrite [:L945] - "Load up the HV fields from table record in
# WS". Two call sites, two different comments for the same paragraph.
# ---------------------------------------------------------------------------


def bb000_hv_load(record: OiHeader) -> tuple[TdSaitm3Rec, WsTempEdKey, WsTempEdBatch]:
    """``bb000-HV-Load`` - fill the host-variable group from the record.

    Transcribed statement for statement from [common/otm3MT.cbl:L1339-L1374]. The move
    ORDER is :data:`LOAD_SEQUENCE`, which the dictionary supplies from each column's own
    recorded load site; it is NOT the column order, because the two derived columns are
    assembled only after their components exist (anomaly N-loadorder).

    Anomaly N-punctuation is visible in the layout of the source this mirrors: [:L1342],
    [:L1344], [:L1348], [:L1350] and [:L1351] end with a period, [:L1345] does not, and
    [:L1353] through [:L1374] carry none at all. The punctuation has no effect - every
    statement is a ``move`` in a paragraph with no conditional - so it is recorded here
    rather than reproduced as structure.

    Returns:
        The loaded group and the two staging records, so a caller (or a test) can inspect
        the derivations that produced ``HV-OI3-KEY`` and ``HV-OI3-BATCH``.
    """
    # `initialize TD-SAITM3-REC.` [common/otm3MT.cbl:L1339] - FIRST, which is what makes
    # every column NOT NULL-able and why nothing is ever bound as a database null.
    group = TdSaitm3Rec.initialize()
    temp_key = WsTempEdKey()
    temp_batch = WsTempEdBatch()

    # [:L1341-L1342] `move OI-Invoice to HV-OI3-INVOICE  WS-Temp-Ed-Invoice.`
    # ONE statement, TWO receivers - and the invoice reaches the staging record BEFORE
    # the customer does, the reverse of the staging group's own declaration order.
    group.store(_COLUMN_BY_NAME["OI3-INVOICE"], record.oi_key.oi_invoice)
    temp_key.ws_temp_ed_invoice = int(record.oi_key.oi_invoice)

    # [:L1343-L1344] `move OI-Customer to HV-OI3-CUSTOMER  WS-Temp-Ed-Customer.`
    customer_image = _oi_customer_image(record)
    group.store(_COLUMN_BY_NAME["OI3-CUSTOMER"], customer_image)
    temp_key.ws_temp_ed_customer = customer_image

    # [:L1345] `move WS-Temp-Ed-Key  to HV-OI3-KEY`  <- no terminating period
    # THE FIRST DERIVED COLUMN. Read out in the staging group's DECLARATION order -
    # customer then invoice - even though it was filled invoice first. Loaded here and
    # never unloaded: anomaly N-two-write-only-columns.
    group.store(_COLUMN_BY_NAME["OI3-KEY"], temp_key.image)

    # [:L1347-L1348] `move OI-B-Nos to HV-OI3-BATCH-NOS  WS-Temp-ED-Batch-Nos.`
    # A COMP field into PIC X(5): anomaly N-binary-to-char.
    group.store(_COLUMN_BY_NAME["OI3-BATCH-NOS"], record.filler_1.oi_batch.oi_b_nos)
    temp_batch.ws_temp_ed_batch_nos = int(record.filler_1.oi_batch.oi_b_nos)

    # [:L1349-L1350] `move OI-B-Item to HV-OI3-BATCH-ITEM  WS-Temp-ED-Batch-Item.`
    group.store(_COLUMN_BY_NAME["OI3-BATCH-ITEM"], record.filler_1.oi_batch.oi_b_item)
    temp_batch.ws_temp_ed_batch_item = int(record.filler_1.oi_batch.oi_b_item)

    # [:L1351] `move WS-Temp-ED-Batch9 to HV-OI3-BATCH.`
    # THE SECOND DERIVED COLUMN, read through the `pic 9(8)` redefinition. With the two
    # components above, this stores the batch three times per row: anomaly N-batch-triple.
    group.store(_COLUMN_BY_NAME["OI3-BATCH"], temp_batch.batch9)

    # [:L1353] `move OI-Date to HV-OI3-DAT` - SEVENTH here, THIRD in the unload, and
    # renamed `Date` -> `DAT` on the way. Signed source, unsigned receiver: the first of
    # the four sites of anomaly N-signloss, applied inside `store`.
    group.store(_COLUMN_BY_NAME["OI3-DAT"], record.filler_1.oi_date)

    # [:L1354] `move OI-Type to HV-OI3-TYPE` - `pic 9` into `PIC X(1)`, anomaly
    # N-numeric-to-char. The legend for the values is quoted in docstring PART 3.
    group.store(_COLUMN_BY_NAME["OI3-TYPE"], record.filler_1.oi_type)

    # [:L1355] `move OI-Description to HV-OI3-DESCRIPTION` - x(25) into X(32), which pads
    # with seven trailing spaces: anomaly N-desc-width.
    group.store(_COLUMN_BY_NAME["OI3-DESCRIPTION"], record.filler_1.oi_description)

    # [:L1356-L1357]
    group.store(_COLUMN_BY_NAME["OI3-HOLD-FLAG"], record.filler_1.oi_hold_flag)
    group.store(_COLUMN_BY_NAME["OI3-UNAPL"], record.filler_1.oi_unapl)

    # [:L1358-L1366] the nine money fields, signed at all three layers. `OI-Approp` is
    # NOT among them - it redefines `OI-Net` and has no column
    # [copybooks/slwsoi.cob:L38-L39], anomaly N-oi-approp-redefine.
    money = record.filler_1.filler_2
    group.store(_COLUMN_BY_NAME["OI3-P-C"], money.oi_p_c)            # [:L1358]
    group.store(_COLUMN_BY_NAME["OI3-NET"], money.oi_net)            # [:L1359]
    group.store(_COLUMN_BY_NAME["OI3-EXTRA"], money.oi_extra)        # [:L1360]
    group.store(_COLUMN_BY_NAME["OI3-CARRIAGE"], money.oi_carriage)  # [:L1361]
    group.store(_COLUMN_BY_NAME["OI3-VAT"], money.oi_vat)            # [:L1362]
    group.store(_COLUMN_BY_NAME["OI3-DISCOUNT"], money.oi_discount)  # [:L1363]
    group.store(_COLUMN_BY_NAME["OI3-E-VAT"], money.oi_e_vat)        # [:L1364]
    group.store(_COLUMN_BY_NAME["OI3-C-VAT"], money.oi_c_vat)        # [:L1365]
    group.store(_COLUMN_BY_NAME["OI3-PAID"], money.oi_paid)          # [:L1366]

    # [:L1367] `pic 9` into `PIC X(1)` again - anomaly N-numeric-to-char. The `88`s over
    # this field, `S-Open` and `S-Closed`, live in `records/otm3.py`.
    group.store(_COLUMN_BY_NAME["OI3-STATUS"], record.filler_1.oi_status)

    # [:L1368] second site of anomaly N-signloss: `binary-Char` -> `9(03)`.
    group.store(_COLUMN_BY_NAME["OI3-DEDUCT-DAYS"], record.filler_1.oi_deduct_days)

    # [:L1369-L1370] signed at all three layers HERE, and unsigned at both in the invoice
    # bridge [common/slinvoiceMT.cbl:L415-L416] - anomaly N-deduct-sign-divergence.
    group.store(_COLUMN_BY_NAME["OI3-DEDUCT-AMT"], record.filler_1.oi_deduct_amt)
    group.store(_COLUMN_BY_NAME["OI3-DEDUCT-VAT"], record.filler_1.oi_deduct_vat)

    # [:L1371] third site of anomaly N-signloss.
    group.store(_COLUMN_BY_NAME["OI3-DAYS"], record.filler_1.oi_days)

    # [:L1372] `HV-OI3-CR PIC S9(10) COMP` - SIGNED, unlike the invoice bridge's
    # `HV-IH-CR PIC 9(10) COMP` [common/slinvoiceMT.cbl:L418]. Anomaly
    # N-oi3-cr-sign-survives: the sign survives HERE and is then taken away by the render
    # like every other numeric column (docstring C6).
    group.store(_COLUMN_BY_NAME["OI3-CR"], record.filler_1.oi_cr)

    # [:L1373-L1374] the last is the fourth site of anomaly N-signloss.
    group.store(_COLUMN_BY_NAME["OI3-APPLIED"], record.filler_1.oi_applied)
    group.store(_COLUMN_BY_NAME["OI3-DATE-CLEARED"], record.filler_1.oi_date_cleared)

    return group, temp_key, temp_batch


# ---------------------------------------------------------------------------
# bb100-UnloadHVs  Section.   [common/otm3MT.cbl:L1379]
#
# Performed from ba041-Reread [:L641], ba050-Process-Read-Indexed [:L750], ba141-Reread
# [:L1138] and ba151-Reread [:L1292] - four sites, and [:L641] and [:L750] carry
# different comments for the same call ("Record layout" against "ws-Record layout").
#
# TWENTY-SIX MOVES FOR TWENTY-EIGHT COLUMNS. `HV-OI3-KEY` and `HV-OI3-BATCH` are absent,
# and the unload is NOT completed: anomaly N-two-write-only-columns.
# ---------------------------------------------------------------------------


def _unload_customer(record: OiHeader, value: str | int | Decimal) -> None:
    """``move HV-OI3-CUSTOMER to OI-Customer`` [common/otm3MT.cbl:L1387].

    ``PIC X(7)`` into the GROUP, so the 7 bytes split back into ``OI-Nos`` ``x(6)`` and
    ``OI-Check`` ``9``. A non-digit in the check position cannot arise from a column the
    bridge itself wrote, and is carried as zero rather than rejected - rule R-3 forbids
    adding a validation the frozen system does not have.
    """
    text = _cobol_move_alphanumeric(str(value), 7)
    record.oi_key.oi_customer.oi_nos = text[:6]
    check = text[6:7].strip()
    record.oi_key.oi_customer.oi_check = int(check) if check.isdigit() else 0


def _unload_integer_from_character(value: str | int | Decimal) -> int:
    """``move <PIC X(n)> to <pic 9(n)>`` - an alphanumeric host variable into a numeric
    record field, which is the reverse of anomalies N-binary-to-char and N-numeric-to-char.

    COBOL reads the digit characters and treats spaces as zero. Non-numeric content in a
    column the bridge wrote is impossible, and is carried as zero rather than rejected.
    """
    text = str(value).strip()
    return int(text) if text.isdigit() else 0


def _unload_scaled(value: str | int | Decimal, scale: int) -> Decimal:
    """``move <COMP scaled HV> to <COMP-3 scaled record field>`` - same scale, no rounding.

    The receiving field's scale is 2 for every scaled field of this record, matching the
    host variable, so the truncation never actually discards a digit; it is applied anyway
    because the frozen ``move`` carries no ``ROUNDED`` and a widened source must truncate.
    """
    amount = value if isinstance(value, Decimal) else Decimal(str(value))
    return amount.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_DOWN)


#: One setter per unloaded column, keyed by column name, each citing its own ``move``.
#: :data:`UNLOAD_SEQUENCE` drives the order, so the transcribed order is load-bearing
#: rather than decorative and a mistranscription would show up in behaviour rather than
#: only in a comment.
_UNLOAD_SETTERS: Final[
    Mapping[str, Callable[[OiHeader, str | int | Decimal], None]]
] = MappingProxyType(
    {
        # [:L1386] `move HV-OI3-INVOICE to OI-Invoice`
        "OI3-INVOICE": lambda record, value: setattr(
            record.oi_key, "oi_invoice", int(value)
        ),
        # [:L1387] `move HV-OI3-CUSTOMER to OI-Customer`
        "OI3-CUSTOMER": _unload_customer,
        # [:L1388] `move HV-OI3-DAT to OI-Date` - THIRD here, seventh in the load.
        "OI3-DAT": lambda record, value: setattr(
            record.filler_1, "oi_date", int(value)
        ),
        # [:L1390] `move HV-OI3-BATCH-NOS to OI-B-Nos`   - char back to COMP
        "OI3-BATCH-NOS": lambda record, value: setattr(
            record.filler_1.oi_batch, "oi_b_nos", _unload_integer_from_character(value)
        ),
        # [:L1391] `move HV-OI3-BATCH-ITEM to OI-B-Item` - char back to COMP
        "OI3-BATCH-ITEM": lambda record, value: setattr(
            record.filler_1.oi_batch, "oi_b_item", _unload_integer_from_character(value)
        ),
        # [:L1393] `move HV-OI3-TYPE to OI-Type` - char back to `pic 9`
        "OI3-TYPE": lambda record, value: setattr(
            record.filler_1, "oi_type", _unload_integer_from_character(value)
        ),
        # [:L1394] `move HV-OI3-DESCRIPTION to OI-Description` - X(32) into x(25), so the
        # width drift of anomaly N-desc-width truncates on the way BACK.
        "OI3-DESCRIPTION": lambda record, value: setattr(
            record.filler_1, "oi_description", _cobol_move_alphanumeric(str(value), 25)
        ),
        # [:L1395-L1396]
        "OI3-HOLD-FLAG": lambda record, value: setattr(
            record.filler_1, "oi_hold_flag", _cobol_move_alphanumeric(str(value), 1)
        ),
        "OI3-UNAPL": lambda record, value: setattr(
            record.filler_1, "oi_unapl", _cobol_move_alphanumeric(str(value), 1)
        ),
        # [:L1397-L1405] the nine money fields.
        "OI3-P-C": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_p_c", _unload_scaled(value, 2)
        ),
        # `OI-Net` and `OI-Approp` are the SAME BYTES [copybooks/slwsoi.cob:L38-L39], so
        # the one move lands in both names. Anomaly N-oi-approp-redefine, from the read
        # side: there is no second column to read it from.
        "OI3-NET": lambda record, value: _unload_net_and_approp(record, value),
        "OI3-EXTRA": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_extra", _unload_scaled(value, 2)
        ),
        "OI3-CARRIAGE": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_carriage", _unload_scaled(value, 2)
        ),
        "OI3-VAT": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_vat", _unload_scaled(value, 2)
        ),
        "OI3-DISCOUNT": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_discount", _unload_scaled(value, 2)
        ),
        "OI3-E-VAT": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_e_vat", _unload_scaled(value, 2)
        ),
        "OI3-C-VAT": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_c_vat", _unload_scaled(value, 2)
        ),
        "OI3-PAID": lambda record, value: setattr(
            record.filler_1.filler_2, "oi_paid", _unload_scaled(value, 2)
        ),
        # [:L1406] `move HV-OI3-STATUS to OI-Status` - char back to `pic 9`
        "OI3-STATUS": lambda record, value: setattr(
            record.filler_1, "oi_status", _unload_integer_from_character(value)
        ),
        # [:L1407-L1413]
        "OI3-DEDUCT-DAYS": lambda record, value: setattr(
            record.filler_1, "oi_deduct_days", int(value)
        ),
        "OI3-DEDUCT-AMT": lambda record, value: setattr(
            record.filler_1, "oi_deduct_amt", _unload_scaled(value, 2)
        ),
        "OI3-DEDUCT-VAT": lambda record, value: setattr(
            record.filler_1, "oi_deduct_vat", _unload_scaled(value, 2)
        ),
        "OI3-DAYS": lambda record, value: setattr(
            record.filler_1, "oi_days", int(value)
        ),
        "OI3-CR": lambda record, value: setattr(record.filler_1, "oi_cr", int(value)),
        "OI3-APPLIED": lambda record, value: setattr(
            record.filler_1, "oi_applied", _cobol_move_alphanumeric(str(value), 1)
        ),
        "OI3-DATE-CLEARED": lambda record, value: setattr(
            record.filler_1, "oi_date_cleared", int(value)
        ),
    }
)


def _unload_net_and_approp(record: OiHeader, value: str | int | Decimal) -> None:
    """``move HV-OI3-NET to OI-Net`` [common/otm3MT.cbl:L1398], both names at once.

    ``OI-Approp redefines OI-Net`` [copybooks/slwsoi.cob:L38-L39], so in COBOL there is
    one field with two names and the single move sets both views. The record dataclass
    carries them as two attributes, faithfully mirroring the copybook, so both are written
    here - anything else would leave a redefinition disagreeing with the bytes it
    redefines.
    """
    amount = _unload_scaled(value, 2)
    record.filler_1.filler_2.oi_net = amount
    record.filler_1.filler_2.oi_approp = amount


def bb100_unload_hvs(group: TdSaitm3Rec) -> OiHeader:
    """``bb100-UnloadHVs`` - build the record from the host-variable group.

    [common/otm3MT.cbl:L1384-L1413]. Twenty-six moves, in :data:`UNLOAD_SEQUENCE` order,
    which is neither the load order nor the column order (anomaly N-loadorder).

    ``HV-OI3-KEY`` and ``HV-OI3-BATCH`` ARE DELIBERATELY NOT UNLOADED - anomaly
    N-two-write-only-columns. On a read the record's ``OI-key`` is reconstituted from
    ``OI-Customer`` and ``OI-Invoice`` alone, and ``OI-Batch`` from its two components
    alone; the two derived columns the bridge stored are simply never consulted. The
    unload is not "completed", because completing it would fix a defect.
    """
    # `initialize WS-OTM3-Record.` [common/otm3MT.cbl:L1384] - the PLAIN form, against
    # `with filler` at the three other sites (anomaly N-initialize). Over this view the
    # two coincide; see `_initialize_oi_header`.
    record = _initialize_oi_header(with_filler=False)

    for column_name in UNLOAD_SEQUENCE:
        binding = _COLUMN_BY_NAME[column_name]
        _UNLOAD_SETTERS[column_name](record, group.value_of(binding))

    return record


# ---------------------------------------------------------------------------
# Working storage that OUTLIVES a single CALL.
#
# A COBOL sub-program's WORKING-STORAGE persists between CALLs unless the program is
# CANCELled, and both programs rely on that: the bridge keeps its connection handle and
# its three cursor flags there, and the handler keeps `A` and `B` there precisely so the
# record-size guard runs "on very first call only  (So do NOT use var A & B again)"
# [common/acas019.cbl:L551-L554]. Module-level state is therefore the FAITHFUL model, not
# a shortcut.
#
# Execution is strictly sequential (rule R-3): one connection, one statement at a time,
# no pool, no lock, no event loop. That is what the single-threaded COBOL does.
# ---------------------------------------------------------------------------


@dataclass
class _BridgeWorkingStorage:
    """``otm3MT``'s WORKING-STORAGE, less the presentation items (deviation D2)."""

    #: The connection handle the bridge holds in ``Ws-Mysql-Cid`` across CALLs, opened by
    #: ``ba020-Process-Open`` and released by ``ba030-Process-Close``.
    connection: object | None = None

    #: The three cursors of ``01 DAL-Data`` [common/otm3MT.cbl:L260-L270]:
    #: ``Most-Cursor-Set`` (PRIMARY, ``ba040``), ``Most-Cursor-Set-2`` (SECONDARY,
    #: ``ba140``, function 32) and ``Most-Cursor-Set-3`` (TERTIARY, ``ba150``, function
    #: 33). All three are used - docstring C5, which is why anomaly N-three-cursors is
    #: recorded as "reproduced as state" rather than as a surplus to be collapsed: the
    #: brief expected two of the three to be dead, and reading the bridge disproved it.
    cursors: CursorStateTable = field(default_factory=CursorStateTable)

    #: ``MOST-Relation pic xxx`` [common/otm3MT.cbl:L261], set by ``ba060`` and read by
    #: the predicate it builds. Spaces until a START sets it, and left at spaces by an
    #: out-of-range access type because the ``evaluate`` has no ``when other``.
    most_relation: str = "   "

    #: The credentials carrier. ``ba012-Test-WS-Rec-Size-2`` loads ``DB-Schema`` and its
    #: five companions from the system record "hopefully once is enough  :)"
    #: [common/acas019.cbl:L586-L588], and ``ba020`` then strings them into the connect
    #: parameters. Holding the system record is the equivalent, because
    #: ``connection.mysql_1000_open`` reads the same six values from it.
    system_record: SystemRecord | None = None

    #: ``WS-Temp-ED-Row pic 9(7)`` [common/otm3MT.cbl:L230] - anomaly N-deadfields. Used
    #: for nothing but rendering a row count into a log string.
    ws_temp_ed_row: int = 0

    #: ``WS-Body-Key pic x(9)`` [common/otm3MT.cbl:L280] - anomaly N-deadfields. Declared
    #: here WITHOUT the "Not used" comment the same field carries in ``slinvoiceMT``, and
    #: read by nothing in this bridge.
    ws_body_key: str = " " * 9

    #: ``A`` and ``B`` from the handler's record-size guard
    #: [common/acas019.cbl:L559-L570]. Zero means "not yet called", which is the only
    #: thing the guard tests.
    ws_length_a: int = 0
    ws_length_b: int = 0

    #: The transport declaration handed to ``connection.py``, and it is ``None``:
    #: THIS HANDLER DECLARES NOTHING AND MUST NOT. There is no counterpart in the
    #: frozen bridge - ``call "MySQL_real_connect"`` [common/otm3MT.cbl:L459] passes
    #: host, user, password, schema, port and socket and NOTHING else, no
    #: certificate, no key, no verification mode - so the compiled system's
    #: transport is plaintext to whatever host the row names.
    #:
    #: ⭐ ``None`` MEANS "USE THE ONE INSTALLED POLICY", which
    #: ``connection.mysql_1000_open`` resolves from
    #: ``connection.connection_policy()``. An earlier revision defaulted this field
    #: to ``TransportSecurity(isolated_oracle=True)`` so that the container-hosted
    #: comparison database could be reached; that made THIS handler the only one of
    #: the twenty that declared a policy of its own, which is precisely the
    #: inconsistency the single boundary exists to remove - the same run would then
    #: have declared different things depending on which table it touched. The
    #: declaration now belongs to the deployment, is made once at the entry point,
    #: and reaches every handler identically.
    transport: TransportSecurity | None = None

    #: Whether the shipped placeholder credentials of
    #: [copybooks/wssystem.cob:L138-L139] may be used. ``None``, meaning THIS HANDLER
    #: DECLARES NOTHING: the compiled program connects with whatever the row holds and
    #: reports what the server says, so the decision belongs to the deployment's one
    #: installed ``ConnectionPolicy`` and not to any one table's working storage. Left
    #: as a slot rather than a constant so a disposable-server scenario can narrow it
    #: here if it ever needs to.
    allow_frozen_placeholder_credentials: bool | None = None


#: The single, module-level instance. One program, one working storage.
_BRIDGE: Final = _BridgeWorkingStorage()


def _reset_working_storage() -> None:
    """Return the module-level working storage to its ``VALUE`` clauses.

    Not a COBOL paragraph: the equivalent of ``CANCEL "otm3MT"``, which is how a COBOL
    caller discards a sub-program's working storage. Provided so a scenario harness can
    start from a known state between runs, which is what makes two runs byte-identical
    (rule R-6). It does not close the connection: ``ba030-Process-Close`` does that, and
    silently dropping a live handle here would diverge from the frozen close path.
    """
    _BRIDGE.connection = None
    _BRIDGE.cursors = CursorStateTable()
    _BRIDGE.most_relation = "   "
    _BRIDGE.system_record = None
    _BRIDGE.ws_temp_ed_row = 0
    _BRIDGE.ws_body_key = " " * 9
    _BRIDGE.ws_length_a = 0
    _BRIDGE.ws_length_b = 0
    # The two security declarations are reset with everything else, and for two
    # reasons. Determinism (rule R-6): a declaration `dispatch` recorded for one
    # scenario must not survive into the next, or two runs of the same scenario
    # differ by whichever ran before them. And fail-closed: a permissive
    # declaration is the one piece of state that must never be inherited by a
    # caller who did not ask for it.
    _BRIDGE.transport = None
    _BRIDGE.allow_frozen_placeholder_credentials = False


# ---------------------------------------------------------------------------
# File-Access accessors. Every status this module reports goes through these, so the
# `(FS-Reply, We-Error)` pair and the log fields are written in exactly one place each.
# ---------------------------------------------------------------------------


#: ``35`` - the ISAM "file not found" status the flat-file open path moves into
#: ``FS-Reply`` at [common/acas019.cbl:L313], and the ONE value this module produces that
#: is NOT a member of :class:`~acas_posting.dal.status.FsReply`.
#:
#: That exclusion is deliberate upstream, not an oversight to be repaired here.
#: ``dal/status.py``'s own class docstring records it: the mandated member set is exactly
#: 0, 10, 21, 22, 23, 99, other handlers document values outside it - it cites
#: ``common/acas008.cbl:L159``'s ``35 = File not found`` - and those are carried as
#: comments rather than added as members, because rule R-3 is that vocabulary is copied,
#: never extended. Adding a member would also be a change to a file this module is not
#: assigned, for a value the migrated cycle never sees: the RDB branch at [:L262-L266]
#: leaves before the dispatch (docstring C2), so only the flat-file path can reach it.
#:
#: The consequence for this module's own signatures is that ``FS-Reply`` is modelled as
#: what the copybook declares - ``pic 99``, an unsigned two-digit integer
#: [copybooks/wsfnctn.cob:L23-L38] - so a status pair is typed ``tuple[int, int]``.
#: :class:`FsReply` members are used wherever a named value exists, and being an
#: ``IntEnum`` they satisfy that annotation unchanged; this constant covers the one place
#: no name exists.
FS_REPLY_FILE_NOT_FOUND: Final = 35


def _as_fs_reply(value: FsReply | int) -> FsReply | int:
    """Name a raw ``FS-Reply`` value where a name exists, and pass it through where none does.

    Returns the :class:`FsReply` member for the six mandated values so that logging and
    comparisons read as the vocabulary does, and the plain integer for
    :data:`FS_REPLY_FILE_NOT_FOUND`. Never raises: rule R-3 forbids extending the
    vocabulary, and the contract at [common/acas019.cbl:L617] forbids raising at all.
    """
    if isinstance(value, FsReply):
        return value
    raw = int(value)
    try:
        return FsReply(raw)
    except ValueError:
        # The vocabulary has no name for this value. `pic 99` holds it regardless, and the
        # caller tests the number - see FS_REPLY_FILE_NOT_FOUND for the only such site.
        return raw


#: The status range that raises the COBOL ``INVALID KEY`` condition: the '2x' class - 21
#: sequence error, 22 duplicate key, 23 record not found, 24 boundary violation. An
#: ``invalid key`` phrase runs for these and for nothing else, so a failure outside the
#: range leaves whatever the runtime stored and skips the phrase entirely.
_INVALID_KEY_STATUS_RANGE: Final = range(21, 25)


def _invalid_key_condition(status: FsReply | int) -> bool:
    """Would this file status raise ``INVALID KEY`` on an indexed file?

    ⭐⭐ THIS PREDICATE EXISTS BECAUSE ``FS-Reply`` IS THE FILE'S OWN FILE STATUS ITEM.
    The handler's SELECT declares it, VERBATIM [copybooks/slseloi3.cob:L2-L6]::

        select  Open-Item-File-3  assign        File-19
                                  access        dynamic
                                  organization  indexed
                                  status        fs-Reply
                                  record key    OI3-Key.

    ``status fs-Reply`` means the ISAM runtime writes each operation's two-character status
    STRAIGHT INTO THE LINKAGE FIELD - the caller's own ``File-Access.Fs-Reply``
    [copybooks/wsfnctn.cob:L23-L38]. Three consequences run through every verb paragraph:

    ONE - every verb sets ``FS-Reply`` whether or not its conditional phrase fires, which
    is why ``aa020`` can write ``open input`` and then simply ask ``if Fs-Reply not = zero``
    [common/acas019.cbl:L311-L312] with no status clause of its own.

    TWO - the ``move`` inside an ``invalid key`` phrase NORMALISES rather than reports. The
    runtime has already stored 22 for a duplicate or 23 for a missing record; ``move 22 to
    FS-Reply`` [:L496] then forces the whole '2x' class to one value. So a duplicate and a
    boundary violation are indistinguishable to the caller of a write, by construction.

    THREE - and this is what the predicate is for - a failure OUTSIDE the '2x' class does
    NOT run the phrase, so the runtime's own status survives into ``FS-Reply``. A permanent
    error (30) or a locked record (9x) reaches the caller as itself, NOT as 21 or 22.
    Collapsing every non-zero status into the phrase's value would invent a translation the
    frozen program does not perform, so each verb below stores the status first and applies
    its phrase only when this predicate holds.

    The ``at end`` condition is the neighbouring case - status 10 exactly - and
    ``aa040-Process-Read-Next`` handles it through the medium returning no record
    [:L375-L382] rather than through this predicate.

    This function IS the reproduction site of anomaly N-file-status-is-the-linkage-field;
    every verb paragraph that calls it carries the corresponding
    ``[copybooks/slseloi3.cob:L5]`` locator at the point the status lands.
    """
    return int(status) in _INVALID_KEY_STATUS_RANGE


def _write_status(
    file_access: FileAccess, fs_reply: FsReply | int, we_error: WeError | int
) -> tuple[int, int]:
    """``move <n> to fs-reply`` / ``move <n> to WE-Error`` - and return the pair.

    ``We-Error`` is ``pic 999`` and ``Fs-Reply`` is ``pic 99``
    [copybooks/wsfnctn.cob:L23-L38], so both are unsigned display integers. Every value the
    frozen source moves fits those widths, but not every one has a name in the
    :class:`FsReply` vocabulary - see :data:`FS_REPLY_FILE_NOT_FOUND` - so the value is
    named where a name exists and carried as a plain integer where none does.
    """
    reply = _as_fs_reply(fs_reply)
    file_access.fs_reply = int(reply)
    file_access.we_error = int(we_error)
    return reply, int(we_error)


def _write_file_key(file_access: FileAccess, text: str) -> None:
    """``move <literal or field> to WS-File-Key`` - truncated into ``pic x(64)``.

    [copybooks/wsfnctn.cob:L52]. A COBOL ``MOVE`` truncates on the right and pads with
    spaces, and both happen here so the logged key is byte-comparable with the compiled
    system's.
    """
    file_access.logging_data.ws_file_key = _cobol_move_alphanumeric(
        text, WS_FILE_KEY_WIDTH
    )


def _write_log_where(file_access: FileAccess, text: str) -> None:
    """``move WS-Where (1:J) to WS-Log-Where`` - truncated into ``pic x(231)``.

    [copybooks/wsfnctn.cob:L53]. ``J`` is the STRING pointer AFTER the transfer, so the
    slice carries one trailing space beyond the text - anomaly N-string-pointer-overrun,
    reproduced by :func:`_ws_where_1_to_j`.
    """
    file_access.logging_data.ws_log_where = _cobol_move_alphanumeric(
        text, WS_LOG_WHERE_WIDTH
    )


def _write_sql_fields(
    file_access: FileAccess,
    *,
    sql_err: str | None = None,
    sql_msg: str | None = None,
    sql_state: str | None = None,
) -> None:
    """Write the three diagnostic fields, each truncated into its declared width.

    ``SQL-Err``, ``SQL-Msg`` and ``SQL-State`` [copybooks/wsfnctn.cob:L44-L56]; the widths
    come from ``dal/status.py`` so every handler module truncates identically. Messages are
    passed through :func:`sanitise_for_log` first, because a driver message can quote the
    statement and a statement can quote a value.

    ``None`` means "the frozen source does not move anything into this field on this
    path", and the field is LEFT AS IT WAS. That distinction is load-bearing rather than
    convenient: the shared error ladder moves ``SQL-State`` unconditionally but moves
    ``SQL-Err`` and ``SQL-Msg`` only inside ``if WS-MYSQL-Error-Number not = "0  "``
    [common/otm3MT.cbl:L540-L544], so on a clean zero-row result the two message fields
    keep the spaces ``ba010`` put there - not an empty string this module invented.
    """
    logging_data = file_access.logging_data
    if sql_err is not None:
        logging_data.sql_err = _cobol_move_alphanumeric(sql_err, SQL_ERR_WIDTH)
    if sql_msg is not None:
        logging_data.sql_msg = _cobol_move_alphanumeric(
            sanitise_for_log(sql_msg, limit=SQL_MSG_WIDTH), SQL_MSG_WIDTH
        )
    if sql_state is not None:
        logging_data.sql_state = _cobol_move_alphanumeric(sql_state, SQL_STATE_WIDTH)


def _testing_1(dal_common: AcasDalCommonData) -> bool:
    """``Testing-1`` - ``SW-Testing = 1`` [copybooks/Test-Data-Flags.cob:L10-L16].

    Gates ``perform Ca-Process-Logs`` in both programs. Note anomaly N-nolog-on-dal: the
    handler's own logging paragraph carries ``*> Not called on DAL access as it does it
    already`` on its label line [common/acas019.cbl:L623].
    """
    return int(dal_common.sw_testing) == 1


def _testing_2(dal_common: AcasDalCommonData) -> bool:
    """``Testing-2`` - ``SW-Testing-2 = 1`` [copybooks/Test-Data-Flags.cob:L13-L16].

    Gates ``display Display-Message-1 with erase eos`` at five sites in the bridge. Those
    displays have no database effect, so per deviation D2 they become log records.
    """
    return int(dal_common.sw_testing_2) == 1


# ---------------------------------------------------------------------------
# WS-Where and the statement text.
#
# Every predicate the bridge builds takes the key straight from the RECORD BUFFER -
# `WS-OTM3-Record (K:L)` with K=1 and L=15 from the key metadata table - never from a
# host variable. And every predicate is read back as `WS-Where (1:J)`, where `J` is the
# STRING pointer left AFTER the transfer, so the slice is one character longer than the
# text: anomaly N-string-pointer-overrun.
# ---------------------------------------------------------------------------


def _quoted_key_name() -> str:
    """``"`" KeyName (KOR-x1) delimited by space "`"`` - the key column, backtick-quoted.

    ``KeyName`` is ``pic x(30)`` and holds ``'OI3-KEY                       '``
    [common/otm3MT.cbl:L249], so ``delimited by space`` is what reduces it to
    ``OI3-KEY``. Every identifier in this module goes through
    :func:`connection.quote_identifier`, without exception: every table and column name
    here contains a hyphen and would otherwise be a syntax error.
    """
    return quote_identifier(cobol_string_delimited_by_space(KEY_OF_REFERENCE.key_name))


_QUOTED_TABLE: Final = quote_identifier(TABLE_NAME)


def _ws_where_1_to_j(text: str) -> str:
    """``WS-Where (1:J)`` - the built text PLUS the one character the pointer overran.

    ``move 1 to J`` then ``STRING ... WITH POINTER J`` leaves ``J`` at one past the last
    character transferred, so ``WS-Where (1:J)`` is ``length + 1`` characters of a field
    that was set to spaces first - the text and one trailing space. Anomaly
    N-string-pointer-overrun.

    It is visible in the statements: the SELECT and the DELETE embed this slice UNTRIMMED,
    so a SELECT reads ``... WHERE `OI3-KEY`=%s ;`` with a space before the semicolon and a
    DELETE ends with a trailing space. The UPDATE wraps it in ``FUNCTION TRIM``
    [common/otm3MT.cbl:L2173-L2175] and so does not.
    """
    return f"{text} "


def _key_predicate() -> str:
    """``` `OI3-KEY`="<record(1:15)>" ``` with the value bound - deviation D1.

    Built by ``ba050`` [common/otm3MT.cbl:L655-L667], ``ba080``
    [:L900-L911] and ``ba090`` [:L955-L966], identically at all three sites.
    """
    return f"{_quoted_key_name()}=%s"


def _sequential_predicate() -> str:
    """``` `OI3-KEY` >= "000000000000000" ORDER BY `OI3-KEY` ASC ``` - ``ba040``'s SELECT.

    [common/otm3MT.cbl:L500-L513]. The relation and the low key come from
    ``cursor_state.SEQUENTIAL_READ_START`` so the two modules cannot drift; the literal
    spacing - ``" >= "`` with a space each side, against ``ba060``'s space-delimited
    relation with none - is transcribed.

    The low key is a LITERAL in the frozen statement rather than a bound value, because it
    is a constant of the program and not data; binding it would still be correct but would
    make the statement text differ from the one ``WS-Log-Where`` records.
    """
    key = _quoted_key_name()
    return (
        f"{key} {_SEQUENTIAL_START.relation.padded.strip()} "
        f'"{_SEQUENTIAL_START.low_key}"'
        f" ORDER BY {key} ASC"
    )


def _start_predicate(relation: str) -> str:
    """``ba060``'s predicate: relation from ``MOST-Relation``, then ORDER BY, then ASC.

    [common/otm3MT.cbl:L789-L802]. Three details are transcribed rather than tidied:
    ``MOST-relation delimited by space`` drops the padding so there is NO space between
    the column and the operator; the opening ``'"'`` follows immediately; and the trailing
    literal is ``' ASC  '`` with TWO trailing spaces, against ``ba040``'s single-space
    ``' ASC'``.
    """
    key = _quoted_key_name()
    operator = cobol_string_delimited_by_space(relation)
    return f"{key}{operator}%s ORDER BY {key} ASC  "


def _select_statement(predicate_1_to_j: str) -> str:
    """``SELECT * FROM `SAITM3-REC` WHERE <WS-Where (1:J)>;``

    The identical five-part template at all four SELECT sites - ``ba040``
    [common/otm3MT.cbl:L520-L526], ``ba050`` [:L677-L683], ``ba060`` [:L810-L816],
    ``ba140`` [:L1013-L1019] and ``ba150`` [:L1166-L1172]. The trailing ``X"00"`` is the C
    string terminator the interface object needs and is not part of the SQL.
    """
    return f"SELECT * FROM {_QUOTED_TABLE} WHERE {predicate_1_to_j};"


def _delete_statement(predicate_1_to_j: str) -> str:
    """``DELETE FROM `SAITM3-REC` WHERE <WS-Where (1:J)>`` - and NO semicolon.

    [common/otm3MT.cbl:L919-L925]. The INSERT [:L1788] and the UPDATE [:L2175] both end
    with ``";"``; this one ends with ``X"00"`` alone. Reproduced as written.
    """
    return f"DELETE FROM {_QUOTED_TABLE} WHERE {predicate_1_to_j}"


def _insert_statement() -> str:
    """``INSERT INTO `SAITM3-REC` SET `col`=%s, ... ;`` - ALL TWENTY-EIGHT columns.

    [common/otm3MT.cbl:L1426-L1789]. Column order is :data:`COLUMNS`, i.e. the table's own
    ordinal order, and EVERY column is named on EVERY insert - never a subset, and never a
    database null, because ``initialize TD-SAITM3-REC`` guaranteed a value for each
    (docstring PART 4, AAP section 0.6.2: "default rather than omit").

    Deviation D1: the frozen statement writes ``` `col`="<rendered text>" ``` and this one
    writes ``` `col`=%s ```, binding the same rendered text. The bytes the server receives
    for each value are identical.
    """
    assignments = ", ".join(f"{binding.quoted_column}=%s" for binding in COLUMNS)
    return f"INSERT INTO {_QUOTED_TABLE} SET {assignments};"


def _update_statement(predicate_trimmed: str) -> str:
    """``UPDATE `SAITM3-REC` SET <all 28> WHERE <TRIM(WS-Where (1:J))>;``

    [common/otm3MT.cbl:L1807-L2176]. THE PRIMARY KEY IS AMONG THE COLUMNS SET: ``OI3-KEY``
    is assigned first [:L1815-L1818] and is also the whole of the predicate, so the
    statement sets the key to the value it is selected by. Harmless, and reproduced.

    Unlike the SELECT and the DELETE, the predicate here IS trimmed [:L2173-L2175], so
    anomaly N-string-pointer-overrun's extra space does not reach this statement.
    """
    assignments = ", ".join(f"{binding.quoted_column}=%s" for binding in COLUMNS)
    return (
        f"UPDATE {_QUOTED_TABLE} SET {assignments} WHERE {predicate_trimmed};"
    )


def _insert_parameters(group: TdSaitm3Rec) -> tuple[str, ...]:
    """The 28 rendered values, in :data:`COLUMNS` order, to bind to the INSERT or UPDATE.

    Every value is the RENDERED TEXT, never the raw ``Decimal`` or ``int``: docstring C6
    establishes that the render is where the sign is dropped, so binding the numeric value
    would store something the compiled system never stored.
    """
    return tuple(group.rendered(binding) for binding in COLUMNS)


# ---------------------------------------------------------------------------
# The `mysql-procedures.cpy` primitives, at the level this bridge uses them.
#
# `COPY "mysql-procedures.cpy".` sits inside the bridge at [common/otm3MT.cbl:L1303],
# between `ba100-Bad-Function` and `ba998-Free`. Three of its procedures are performed
# from the paragraphs below and are reproduced here:
#
#   MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT   issue one statement, count affected rows,
#                                             and on a non-zero return perform
#                                             MYSQL-1100-DB-ERROR - which sets (99, 911)
#                                             and does NOT transfer control, so the
#                                             calling paragraph's own count test then
#                                             overwrites the pair.
#   MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT  materialise every qualifying row, after
#                                             which the count is the ROW count.
#   MySQL_fetch_record                        move one stored row into the host variables.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _CommandResult:
    """What a statement leaves behind for the calling paragraph to test.

    ``WS-MYSQL-Count-Rows`` is the field every paragraph branches on, and its meaning
    depends on the statement: affected rows after a command, stored rows after a store.
    ``errno`` is ``WS-MYSQL-Error-Number``, which the paragraphs test as
    ``not = "0  "`` - so a clean statement must leave the three-character zero, not an
    empty string.
    """

    count_rows: int
    errno: str
    message: str
    sql_state: str
    rows: tuple[Mapping[str, object], ...] = ()

    @property
    def driver_reported_error(self) -> bool:
        """``if WS-MYSQL-Error-Number not = "0  "`` - the test, spelled once."""
        return self.errno != _ERRNO_CLEAN


#: ``WS-MYSQL-Error-Number`` when nothing went wrong. The paragraphs compare against the
#: literal ``"0  "``, so the clean value is a zero in a three-character field.
_ERRNO_CLEAN: Final = "0  "


def _materialise_rows(cursor: object) -> tuple[Mapping[str, object], ...]:
    """``MYSQL-1220-STORE-RESULT`` - pull EVERY qualifying row to the client.

    [copybooks/mysql-procedures.cpy:L187-L192] as performed at
    [common/otm3MT.cbl:L527, :L684, :L817, :L1020, :L1173]. The whole result is stored and
    ``MySQL_num_rows`` counts THAT; the row-by-row walk afterwards is
    ``MySQL_fetch_record`` over the stored copy, which is why a cursor survives across
    CALLs and why ``ba998-Free`` exists at all.

    Rows are keyed by column name so the fetch below can address them by the name the
    dictionary knows. Both a tuple-returning and a mapping-returning driver cursor are
    accepted, because which one is in use is ``connection.py``'s decision, not this
    module's.
    """
    description = getattr(cursor, "description", None) or ()
    names = tuple(str(column[0]) for column in description)
    rows: list[Mapping[str, object]] = []
    fetchone = getattr(cursor, "fetchone")
    while True:
        row = fetchone()
        if row is None:
            return tuple(rows)
        if isinstance(row, Mapping):
            rows.append(MappingProxyType(dict(row)))
        else:
            rows.append(MappingProxyType(dict(zip(names, tuple(row)))))


def _mysql_1210_command(
    context: _BridgeContext,
    statement: str,
    parameters: Sequence[object] = (),
    *,
    store_result: bool = False,
) -> _CommandResult:
    """Issue one statement. Never raises; a driver failure becomes a status.

    Reproduces ``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT``, optionally followed by
    ``PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT`` when the statement is a
    SELECT - which is exactly the pairing the frozen source uses.

    THE ERROR PATH IS THE FROZEN ONE, IN TWO STAGES. ``Mysql-1100-Db-Error`` sets
    ``(99, 911)`` [copybooks/mysql-procedures.cpy:L127-L128] and does NOT transfer control,
    so ``WS-MYSQL-Count-Rows`` is left at zero and the calling paragraph's own test -
    ``= zero`` or ``not = 1`` - then OVERWRITES the pair with its own value. That is why
    this function returns a result rather than a status: the paragraph decides.

    ``dal/status.py``'s ``mysql_1100_db_error`` performs the classification so every
    handler module reports a driver failure identically.
    """
    connection = _BRIDGE.connection
    if connection is None:
        # `Ws-Mysql-Cid` is zero because no `ba020-Process-Open` has succeeded. The frozen
        # bridge would pass a null handle to the interface object and the query would fail,
        # which is the `Mysql-1100-Db-Error` path - so that is the status reported here,
        # with the RDB initialisation error the copybook itself uses.
        # ONE ERROR, through the shared reporter, so that every failure in every
        # handler renders with the same fields in the same order. The statement's
        # leading verb is no longer interpolated: it is the first token of the SQL
        # this module built, and the safe-event schema admits no SQL fragment at all
        # (CWE-532). The paragraph name identifies the site without it.
        log_handler_failure(
            _LOG,
            program=BRIDGE_PROGRAM_ID,
            paragraph="_mysql_command",
            locator="[common/otm3MT.cbl:L458-L468]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="a statement was issued with no open connection; "
            "ba020-Process-Open has not succeeded",
        )
        status = mysql_1100_db_error(
            errno=str(int(WeError.RDB_INIT_ERROR)),
            message="no open connection",
            sql_state="",
            command=statement,
        )
        status.apply_to_logging_data(context.file_access.logging_data)
        return _CommandResult(
            count_rows=0,
            errno=str(int(WeError.RDB_INIT_ERROR)),
            message="no open connection",
            sql_state="",
        )

    try:
        with execute_statement(connection, statement, tuple(parameters)) as cursor:
            if store_result:
                rows = _materialise_rows(cursor)
                return _CommandResult(
                    count_rows=len(rows),
                    errno=_ERRNO_CLEAN,
                    message="",
                    sql_state="",
                    rows=rows,
                )
            affected = int(getattr(cursor, "rowcount", 0) or 0)
            return _CommandResult(
                count_rows=max(affected, 0),
                errno=_ERRNO_CLEAN,
                message="",
                sql_state="",
            )
    except Exception as error:  # noqa: BLE001 - see below
        # EVERY driver failure takes this path, deliberately. The frozen bridge tests one
        # return code from `call "MySQL_query"` and cannot distinguish a syntax error from
        # a lost connection, so neither does this - and narrowing the catch would let an
        # exception escape a module whose contract is that it never raises
        # [common/acas019.cbl:L617].
        errno = str(getattr(error, "errno", "") or "").strip() or "1"
        sql_state = str(getattr(error, "sqlstate", "") or "")
        message = str(getattr(error, "msg", None) or error)
        status = mysql_1100_db_error(
            errno=errno, message=message, sql_state=sql_state, command=statement
        )
        status.apply_to_logging_data(context.file_access.logging_data)
        #  THE DRIVER'S TEXT IS NOT LOGGED. For this table it renders the whole
        #  statement and its bound values - the customer number, the invoice number
        #  and the deduction amounts - and `sanitise_for_log` escaped it rather than
        #  removing any of it (CWE-117 addressed, CWE-532 not). What remains is the
        #  errno, the SQLSTATE and the stable category derived from them, which is
        #  what an operator acts on.
        #  ONE ERROR, not two: `mysql_1100_db_error` above is the migration of
        #  `Mysql-1110-Report-Problem` [copybooks/mysql-procedures.cpy:L130-L137] and
        #  has already emitted the operator record. This site adds the paragraph
        #  identity the shared reporter cannot know, at the same level, and `message`
        #  is still RETURNED because `SQL-Msg` is a status field the paragraphs read.
        log_handler_failure(
            _LOG,
            program=BRIDGE_PROGRAM_ID,
            paragraph="_mysql_command",
            locator="[copybooks/mysql-procedures.cpy:L127-L128]",
            sql_err=errno,
            sql_state=sql_state,
            detail="the statement failed; the calling paragraph's own row-count "
            "test then overwrites the (99, 911) pair, as the frozen bridge does",
        )
        return _CommandResult(
            count_rows=0,
            errno=errno,
            message=message,
            sql_state=sql_state,
        )


def _mysql_fetch_record(group: TdSaitm3Rec, row: Mapping[str, object]) -> None:
    """``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT HV-OI3-KEY ...``

    [common/otm3MT.cbl:L700-L730] and the three sibling fetch sites. The interface object
    moves one stored row's columns into the twenty-eight host variables, IN THE ORDER THE
    CALL LISTS THEM - which is the column order, since the ``SELECT *`` returns them in
    that order.

    ALL TWENTY-EIGHT are fetched, including ``HV-OI3-KEY`` and ``HV-OI3-BATCH``: the two
    write-only columns ARE read into their host variables here and are then simply not
    unloaded into the record (anomaly N-two-write-only-columns). The asymmetry is in
    ``bb100-UnloadHVs``, not in the fetch.

    Each value passes through :meth:`ColumnBinding.coerce`, so it lands in the host
    variable under the same receiving-field rules the load applies - which for the four
    unsigned receivers of anomaly N-signloss means a negative value could not survive even
    if the column somehow held one.
    """
    for binding in COLUMNS:
        if binding.column_name in row:
            group.store(binding, row[binding.column_name])  # type: ignore[arg-type]
        else:
            # A column absent from the result is not a condition the frozen source has a
            # path for - `SELECT *` always returns all of them. It is recorded and left at
            # its initialised value rather than raising.
            _LOG.error(
                "%s: column %s absent from the result of a SELECT *; the host variable "
                "keeps its initialised value [%s]",
                BRIDGE_PROGRAM_ID,
                binding.column_name,
                binding.citation,
            )


@dataclass
class _BridgeContext:
    """``otm3MT``'s LINKAGE plus the per-CALL scratch its paragraphs share.

    The three linkage items are exactly the bridge's own, in its own order
    [common/otm3MT.cbl:L611-L615]: ``File-Access``, ``ACAS-DAL-Common-data``,
    ``WS-OTM3-Record``. Everything else here is bridge WORKING-STORAGE that does not
    outlive a CALL - the built predicate, the current host-variable group and the row
    count the paragraphs branch on.
    """

    file_access: FileAccess
    dal_common: AcasDalCommonData
    record: OiHeader
    group: TdSaitm3Rec = field(default_factory=TdSaitm3Rec.initialize)
    ws_where: str = ""
    count_rows: int = 0
    return_code: int = 0
    fs_reply: int = FsReply.SUCCESS
    we_error: int = 0

    def status(self, fs_reply: FsReply | int, we_error: WeError | int) -> None:
        """Write a status pair into ``File-Access`` and remember it for the return."""
        self.fs_reply, self.we_error = _write_status(
            self.file_access, fs_reply, we_error
        )

    def slot_state(self, slot: CursorSlot) -> CursorState:
        """One of the three cursors of ``01 DAL-Data`` - docstring C5."""
        return _BRIDGE.cursors.state_for(TABLE_NAME, slot)


# ---------------------------------------------------------------------------
# The flat-file medium - deviation D3.
#
# `select Open-Item-File-3 assign ... organization indexed, access dynamic,
#  status fs-Reply, record key OI3-Key` [copybooks/slseloi3.cob] is the whole of the
# contract the handler's `aa020` .. `aa100` need: six verbs, each of which leaves an
# `FS-Reply` behind, plus the `invalid key` condition the verbs test.
#
# The migrated system has no ISAM store and R-1 forbids reaching the compiled one, so the
# medium is an injected collaborator with an absent default. Every flat-file paragraph is
# reproduced in full regardless, because per C2 the migrated cycle never reaches them and
# omitting them would delete traceable behaviour (R-4, R-5).
# ---------------------------------------------------------------------------


class FlatFileMedium(Protocol):
    """The six ISAM verbs ``acas019``'s flat-file paragraphs issue.

    Each method returns the ``FS-Reply`` the ``status fs-Reply`` clause of
    [copybooks/slseloi3.cob] would have written - ``0`` for success, ``23`` for a
    not-found key, ``35`` for a missing file, and so on. NO method raises and NO method
    interprets its own status: the calling paragraph's branches do that, exactly as the
    COBOL's ``invalid key`` and ``at end`` phrases do.

    ``read_next`` and ``read_indexed`` additionally return the record they read, or
    ``None`` at end of file, so that ``aa040``'s ``at end`` phrase and ``aa050``'s
    ``invalid key`` phrase have something to test.
    """

    def open_file(self, mode: str) -> FsReply:
        """``open input | i-o | output | extend Open-Item-File-3`` - ``aa020``."""

    def close_file(self) -> FsReply:
        """``close Open-Item-File-3`` - ``aa030``."""

    def read_next(self) -> tuple[FsReply, OpenItemRecord3 | None]:
        """``read Open-Item-File-3 next record at end ...`` - ``aa040``."""

    def read_indexed(self, key: str) -> tuple[FsReply, OpenItemRecord3 | None]:
        """``read Open-Item-File-3 key OI3-Key invalid key ...`` - ``aa050``."""

    def start(self, key: str, relation: str) -> FsReply:
        """``start Open-Item-File-3 key <rel> OI3-Key invalid key ...`` - ``aa060``."""

    def write(self, record: OpenItemRecord3) -> FsReply:
        """``write Open-Item-Record-3 invalid key ...`` - ``aa070``."""

    def delete(self, record: OpenItemRecord3) -> FsReply:
        """``delete Open-Item-File-3 record invalid key ...`` - ``aa080``."""

    def rewrite(self, record: OpenItemRecord3) -> FsReply:
        """``rewrite Open-Item-Record-3 invalid key ...`` - ``aa090``."""


class _AbsentFlatFileMedium:
    """The default medium: no ISAM store is present, so every verb fails.

    ``FsReply.ERROR`` (99) is returned rather than a made-up file status, and the handler's
    OWN branches then decide the outcome - ``aa020``'s ``if Fs-Reply not = zero`` becomes
    ``move 35 to fs-Reply``, ``aa050``'s ``invalid key`` phrase becomes ``move 21 to
    we-error fs-reply``, and so on. No status is invented by this module.

    Every call is reported ONCE, AT ERROR, through the shared reporter, because on the
    DAL path it cannot happen: per C2 ``acas019`` leaves for ``ba-Process-RDBMS`` before
    the dispatch, so reaching here in a migrated run means ``FS-Cobol-Files-Used`` was
    true, which no in-scope scenario sets. A verb that returns 99 to its caller is a
    FAILURE, and reporting it at WARNING put it below the level an operator watches.
    """

    def _absent(self, verb: str) -> FsReply:
        """Report the attempt and return 99, the one status this class ever produces."""
        log_handler_failure(
            _LOG,
            program=HANDLER_PROGRAM_ID,
            paragraph="_AbsentFlatFileMedium.%s" % verb,
            locator="[copybooks/slseloi3.cob]",
            fs_reply=int(FsReply.ERROR),
            detail="a flat-file verb was requested but no ISAM medium is present; "
            "the paragraph's own branch interprets the 99 (deviation D3)",
        )
        return FsReply.ERROR

    def open_file(self, mode: str) -> FsReply:
        """No file to open, so ``aa020``'s ``if Fs-Reply not = zero`` [:L312] decides."""
        return self._absent(f"open {mode}")

    def close_file(self) -> FsReply:
        """No file to close; ``aa030`` [:L349] does not test the reply."""
        return self._absent("close")

    def read_next(self) -> tuple[FsReply, OpenItemRecord3 | None]:
        """No record, so ``aa040`` takes its ``at end`` branch [:L375-L381]."""
        return self._absent("read next"), None

    def read_indexed(self, key: str) -> tuple[FsReply, OpenItemRecord3 | None]:
        """No record, so ``aa050`` reports ``21`` in both fields [:L422]."""
        return self._absent("read indexed"), None

    def start(self, key: str, relation: str) -> FsReply:
        """No cursor to position, so ``aa060``'s ``invalid key`` phrase decides."""
        return self._absent(f"start {relation}")

    def write(self, record: OpenItemRecord3) -> FsReply:
        """99 is outside the '2x' class, so ``aa070``'s phrase does NOT fire [:L495]."""
        return self._absent("write")

    def delete(self, record: OpenItemRecord3) -> FsReply:
        """99 is outside the '2x' class, so ``aa080``'s phrase does NOT fire [:L506]."""
        return self._absent("delete")

    def rewrite(self, record: OpenItemRecord3) -> FsReply:
        """99 is outside the '2x' class, so ``aa090``'s phrase does NOT fire [:L518]."""
        return self._absent("rewrite")


_FLAT_FILE_MEDIUM_ABSENT: Final[FlatFileMedium] = _AbsentFlatFileMedium()  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# The cross-view group moves - deviation D4.
#
# `move Open-Item-Record-3 to WS-OTM3-Record` and its inverse are group moves between two
# arrangements of the same 118 bytes (C3). Here they transfer the fields BOTH views name -
# the 15-character key and the date - which is the whole of the overlap the FILE view
# declares before its `filler pic x(99)`.
#
# These two functions are the reproduction site of anomaly N-three-record-views. The three
# arrangements live in three places and are NOT redefinitions of one another: the LINKAGE
# view [common/acas019.cbl:L215] and the CALLER view [copybooks/slwsoi3.cob:L9-L19] and the
# FILE view [copybooks/slfdoi3.cob:L10-L15], the last a standalone `01` under the FD. The
# moves below cross between the linkage view and the file view, which is exactly the pair
# the handler's own statements name; the caller view is the third party's and this module
# never holds it. The brief called this "N-two-record-views" and had the direction of the
# disagreement wrong - see docstring C3 for the correction.
# ---------------------------------------------------------------------------


def _move_file_record_to_linkage(
    file_record: OpenItemRecord3, linkage: OiHeader
) -> None:
    """``move Open-Item-Record-3 to WS-OTM3-Record`` - [common/acas019.cbl:L385, :L422].

    The FILE view's ``OI3-Key`` is one 15-character group; the LINKAGE view splits the same
    15 bytes into ``OI-Customer`` (7, itself ``OI-Nos`` 6 plus ``OI-Check`` 1) and
    ``OI-Invoice`` (``pic 9(8)``). The split is performed here rather than assumed, so the
    receiving fields get exactly the bytes the overlay would have given them.

    ``OI-Invoice`` receives a numeric-edited move: non-numeric text in those eight bytes
    would be a data error the COBOL would carry silently into a ``pic 9(8)`` field, so it
    is logged and taken as zero rather than raised (deviation D4, R-4: the caller recovers,
    per [common/acas019.cbl:L617]).
    """
    key_image = _oi3_key_image(file_record)
    customer = _cobol_move_alphanumeric(key_image[:7], 7)
    linkage.oi_key.oi_customer.oi_nos = customer[:6]
    linkage.oi_key.oi_customer.oi_check = _character_digit(customer[6:7])
    linkage.oi_key.oi_invoice = _numeric_digits(key_image[7:15], "OI-Invoice")
    # `OI3-Date` and `OI-Date` occupy the same four bytes at offset 15 in both views, so
    # the group move carries the date across [copybooks/slfdoi3.cob], [copybooks/slwsoi.cob:L15].
    # The FILE view spells it `OI3-Date` and the LINKAGE view `OI-Date`; the two names are
    # NOT interchangeable, which is the whole point of docstring C3's three views.
    linkage.filler_1.oi_date = file_record.oi3_date


def _move_linkage_to_file_record(
    linkage: OiHeader, file_record: OpenItemRecord3
) -> None:
    """``move WS-OTM3-Record to Open-Item-Record-3`` - [:L491, :L502, :L514].

    The inverse of the above, and the first statement of ``aa070``, ``aa080`` and ``aa090``
    alike. ``OI3-Key`` is reassembled from the linkage view's customer and invoice by
    :func:`_oi_key_image`, which is the same assembly ``bb000-HV-Load`` performs for
    ``HV-OI3-KEY`` - the derived key of anomaly N-two-write-only-columns, built here for a
    different receiver.
    """
    key_image = _oi_key_image(linkage)
    file_record.oi3_key.oi3_customer = key_image[:7]
    file_record.oi3_key.oi3_invoice = _numeric_digits(key_image[7:15], "OI3-Invoice")
    file_record.oi3_date = linkage.filler_1.oi_date


def _character_digit(text: str) -> int:
    """``OI-Check pic 9`` receiving one character of a group move.

    A space or any other non-digit in that byte is what ``move spaces to OI3-Key``
    [common/acas019.cbl:L368] deliberately puts there - anomaly N-spaces-into-numeric - so
    it is taken as zero here rather than treated as an error.
    """
    stripped = text.strip()
    return int(stripped) if stripped.isdigit() else 0


def _numeric_digits(text: str, field_name: str) -> int:
    """Digits of a group move into a ``pic 9(n)`` receiver, spaces included.

    Anomaly N-spaces-into-numeric puts spaces into exactly such a field, and the compiled
    program carries them without complaint until something reads the field as a number.
    Here the value is taken as zero and the event is logged, because raising would break
    the never-raises contract at [common/acas019.cbl:L617].
    """
    stripped = text.strip()
    if stripped.isdigit():
        return int(stripped)
    if stripped:
        #  THE BYTES THEMSELVES ARE NOT LOGGED. They are whatever a group move
        #  put into the field, which on this record is part of a customer number or
        #  an invoice number - a business key even when it is malformed (CWE-532).
        #  The FIELD NAME is a record-layout identifier and is enough to locate it.
        _LOG.warning(
            "%s: %s received non-numeric bytes from a group move; taken as zero "
            "(anomaly N-spaces-into-numeric [common/acas019.cbl:L368])",
            HANDLER_PROGRAM_ID,
            field_name,
        )
    return 0


# ===========================================================================
# THE BRIDGE - otm3MT
#
# `ba-ACAS-DAL-Process section.` [common/otm3MT.cbl:L370] through
# `ca-Exit. exit.` [:L2190]. One function per paragraph, in source order, each stamping
# its own `ws-No-Paragraph` and each transfer annotated with its class from the AAP
# section 0.4.2 taxonomy.
#
# The bridge owns ALL SQL for SAITM3-REC and nothing else owns any.
# ===========================================================================


def ba_acas_dal_process(context: _BridgeContext) -> None:
    """``ba-ACAS-DAL-Process section.`` - [common/otm3MT.cbl:L370-L382].

    The section head runs before ``ba010-Initialise`` on every CALL and does nothing but
    presentation setup: it accepts the terminal height into ``ws-env-lines``, floors it at
    24, and forces the escape and screen-exception environment variables so that a curses
    ``display`` can detect Esc and the page keys::

        accept   ws-env-lines from lines.                          [:L372]
        if       ws-env-lines < 24  move 24 to ws-env-lines ws-lines  [:L373-L376]
        set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".        [:L379]
        set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".               [:L380]
        add      2 to ws-lines giving ws-99-lines.                  [:L381]
        add      1 to ws-lines giving ws-98-lines.                  [:L382]

    Not one of those six statements has a database effect, and the three fields they
    compute are read only by ``display ... at`` positions. Deviation D2 therefore drops
    the whole head, and the function exists so that the paragraph inventory is complete
    and the omission is visible at the place it happens rather than only in the docstring.

    ``ws-99-lines`` and ``ws-98-lines`` are additionally dead in this bridge: nothing
    reads them, because every ``display`` here is ``Display-Message-1 with erase eos``,
    which carries no line number.
    """
    # NO RECORD HERE. Six statements were dropped and not one of them displays
    # anything, so announcing the drop is announcing an omission - which belongs in
    # this docstring and in `docs/migration/traceability.md`, where it is, and not in a
    # line emitted on every relational call.
    return None


def ba010_initialise(context: _BridgeContext) -> tuple[int, int]:
    """``ba010-Initialise.`` - [common/otm3MT.cbl:L384-L429]. Clear, then dispatch.

    Two things happen, in this order.

    FIRST, the clear - and note WHAT IS NOT CLEARED::

        move     zero   to SQL-State.              [:L385]
    *>                      We-Error                [:L386]  <- commented out
    *>                      Fs-Reply.               [:L387]  <- commented out
        move     spaces to WS-MYSQL-Error-Message  [:L388]
                           WS-MYSQL-Error-Number
                           WS-Log-Where
                           WS-File-Key
                           SQL-Msg
                           SQL-Err.

    ``We-Error`` and ``Fs-Reply`` ARRIVE FROM THE CALLER AND ARE NOT RESET. This is the
    bridge's own deliberate non-initialisation, and it is the second one in the call
    chain: the handler has an identical pair commented out at
    [common/acas019.cbl:L279-L280]. It matters at ``ba041``, whose ``if fs-reply = 10``
    test [:L636] can therefore see a 10 the CALLER left behind rather than one this CALL
    produced. Anomaly N-initialise-partial; reproduced by not zeroing them.

    ``SQL-State`` gets ZERO, not spaces, while ``SQL-Err`` gets SPACES - two different
    clear values in one statement pair, transcribed as written.

    SECOND, the dispatch: the eleven-arm ``evaluate File-Function`` [:L406-L429], in the
    source order of its arms. Every arm is a ``go to``, so each is AAP section 0.4.2
    Class 4 - sibling re-dispatch - and each returns the status pair the target paragraph
    reached. Codes 32 and 33 are here and are absent from the handler's dispatch; see
    docstring C1.
    """
    # `move zero to SQL-State` [common/otm3MT.cbl:L385]. ZERO, into a `pic x(5)`, which
    # leaves "0" then four spaces - not "00000".
    context.file_access.logging_data.sql_state = _cobol_move_alphanumeric(
        "0", SQL_STATE_WIDTH
    )
    # `We-Error` and `Fs-Reply` are NOT cleared: [:L386-L387] are commented out. The
    # caller's values stand. Anomaly N-initialise-partial.
    context.fs_reply = _as_fs_reply(context.file_access.fs_reply)
    context.we_error = int(context.file_access.we_error)
    # `move spaces to WS-MYSQL-Error-Message WS-MYSQL-Error-Number WS-Log-Where
    #  WS-File-Key SQL-Msg SQL-Err` [:L388-L393].
    _write_log_where(context.file_access, "")
    _write_file_key(context.file_access, "")
    context.file_access.logging_data.sql_msg = " " * SQL_MSG_WIDTH
    context.file_access.logging_data.sql_err = " " * SQL_ERR_WIDTH

    # `evaluate File-Function` [:L406-L429]. Arms in source order; each is Class 4.
    function = int(context.file_access.file_function)
    if function == int(FileFunction.OPEN):                    # when 1  [:L407-L408]
        return ba020_process_open(context)
    if function == int(FileFunction.CLOSE):                   # when 2  [:L409-L410]
        return ba030_process_close(context)
    if function == int(FileFunction.READ_NEXT):               # when 3  [:L411-L412]
        return ba040_process_read_next(context)
    if function == int(FileFunction.READ_INDEXED):            # when 4  [:L413-L414]
        return ba050_process_read_indexed(context)
    if function == int(FileFunction.WRITE):                   # when 5  [:L415-L416]
        return ba070_process_write(context)
    if function == int(FileFunction.RE_WRITE):                # when 7  [:L417-L418]
        return ba090_process_rewrite(context)
    if function == int(FileFunction.DELETE):                  # when 8  [:L419-L420]
        return ba080_process_delete(context)
    if function == int(FileFunction.START):                   # when 9  [:L421-L422]
        return ba060_process_start(context)
    if function == int(FileFunction.READ_BY_BATCH):           # when 32 [:L423-L424]
        return ba140_process_read_next(context)
    if function == int(FileFunction.READ_BY_CUST):            # when 33 [:L425-L426]
        return ba150_process_read_next(context)
    # `when other  go to ba100-Bad-Function` [:L427-L428]. The inline comment on that arm
    # reads `*> 6 is spare / unused`.
    return ba100_bad_function(context)


def ba020_process_open(context: _BridgeContext) -> tuple[int, int]:
    """``ba020-Process-Open.`` - [common/otm3MT.cbl:L430-L472]. Connect, then flag.

    Six ``string`` statements marshal the credentials, each one
    ``delimited by space`` followed by a ``X"00"`` terminator
    [common/otm3MT.cbl:L434-L457], in this order: schema, host, user, password, port,
    socket. ``connection.mysql_1000_open`` performs the identical marshalling from the
    identical six fields - the AAP forbids duplicating its credential load - so this
    paragraph reads them and hands them over rather than re-marshalling them into a
    connect call of its own. Only the transport CLASS is recorded; see the comment at the
    record itself.

    Then::

        move     1 to ws-No-Paragraph.                    [:L458]
        PERFORM  MYSQL-1000-OPEN  THRU MYSQL-1090-EXIT.   [:L459]
        if       fs-reply not = zero  go to ba999-end.    [:L460-L461]
        move    "OPEN SL OTM3" to WS-File-Key             [:L466]
        set     Cursor-Not-Active to true                 [:L467]
        go      to ba999-end.                             [:L468]

    ⭐ THE OPEN MODE IS NEVER CONSULTED. ``Access-Type`` distinguishes input, i-o, output
    and extend for the flat-file handler, and this paragraph reads none of them: a
    connection is a connection. That is the mechanism behind anomaly N-noopenoutput - an
    Open+Output through the DAL path is a plain connect and DELETES NOTHING, unlike
    ``acas008``, which coerces the function to delete-all [common/acas008.cbl:L313-L319].

    ⭐ ONLY THE PRIMARY CURSOR IS FLAGGED INACTIVE at [:L467]. ``Most-Cursor-Set-2`` and
    ``Most-Cursor-Set-3`` keep whatever they held across the CALL, so an open following a
    sorted read leaves that sorted cursor believing it is still active - the same
    one-of-three asymmetry as anomaly N-ba998-frees-primary-only, at the other end of the
    connection's life.

    Transfers: ``go to ba999-end`` twice, both Class 3.
    """
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba020-Process-Open"
    ]

    # The six `string DB-* delimited by space X"00"` statements [:L434-L457]. `RDB-Data`
    # is part of `File-Access` [copybooks/wsfnctn.cob:L57-L64] and was filled by the
    # handler's `ba012-Test-WS-Rec-Size-2` [common/acas019.cbl:L586-L598].
    rdb = context.file_access.rdb_data
    #  THE ENDPOINT IS CLASSIFIED, NOT NAMED. This record used to carry the schema,
    #  the host, the port and the socket path. Withholding the user and the password was
    #  not enough: the four that remained are the deployment's own identity, they differ
    #  between every environment - so two runs of the same scenario could not produce the
    #  same line - and they are exactly what an attacker reading a log wants (CWE-532).
    #  `transport_category` answers the one question a record has to answer about a
    #  connect target, whether the credentials and the posted figures can be read off the
    #  wire, with one of five fixed tokens.
    _LOG.debug(
        "%s: ba020 connect [common/otm3MT.cbl:L434-L457] transport=%s",
        BRIDGE_PROGRAM_ID,
        transport_category(
            {
                "host": cobol_string_delimited_by_space(rdb.db_host),
                "unix_socket": cobol_string_delimited_by_space(rdb.db_socket),
            }
            if cobol_string_delimited_by_space(rdb.db_socket)
            else {"host": cobol_string_delimited_by_space(rdb.db_host)},
            _BRIDGE.transport,
        ),
    )

    system_record = _BRIDGE.system_record
    if system_record is None:
        # `Ws-Mysql-Cid` would be passed to `MySQL_real_connect` with blank credentials
        # and the connect would fail, which is the `Mysql-1100-Db-Error` path: (99, 911).
        log_handler_failure(
            _LOG,
            program=BRIDGE_PROGRAM_ID,
            paragraph="ba020-Process-Open",
            locator="[common/acas019.cbl:L586-L598]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="no system record in working storage: the handler's ba012 has "
            "not run, so DB-Schema and its five companions are unset",
        )
        status = mysql_1100_db_error(
            errno=str(int(WeError.RDB_INIT_ERROR)),
            message="credentials not loaded",
            sql_state="",
            command="MySQL_real_connect",
        )
        status.apply_to_logging_data(context.file_access.logging_data)
        context.status(status.fs_reply, status.we_error)
        return ba999_end(context)  # `go to ba999-end` [:L461] - Class 3

    try:
        # `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT` [:L459]. The credential load,
        # the three-step error ladder and the (99, 911) on failure all live in
        # `dal/connection.py`; this module calls it and never reimplements it.
        outcome = mysql_1090_exit(
            mysql_1000_open(
                system_record,
                ws_no_paragraph=BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"],
                transport=_BRIDGE.transport,
                allow_frozen_placeholder_credentials=(
                    _BRIDGE.allow_frozen_placeholder_credentials
                ),
            )
        )
    except Exception as error:  # noqa: BLE001 - the never-raises contract, [:L617]
        # `connection.py`'s policy layer refuses a placeholder credential or an
        # unprotected non-local target by raising. The frozen program has no such notion,
        # and its only failure outcome for an open is the one below, so the refusal is
        # reported as that outcome rather than escaping this module.
        #  THE REFUSAL'S OWN TEXT IS NOT LOGGED. `connection.py` raises with a
        #  message that names the target it refused and, for a placeholder credential,
        #  the credential's own value; `sanitise_for_log` escaped it and removed none
        #  of it (CWE-532). The exception TYPE names the reason without naming the
        #  deployment, and the policy layer has already reported its own refusal once.
        log_handler_failure(
            _LOG,
            program=BRIDGE_PROGRAM_ID,
            paragraph="ba020-Process-Open",
            locator="[common/otm3MT.cbl:L459-L461]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="the connect was refused by the connection policy layer (%s); "
            "reported as the frozen open-failure outcome rather than raised, per "
            "the never-raises contract" % type(error).__name__,
        )
        status = mysql_1100_db_error(
            errno=str(int(WeError.RDB_INIT_ERROR)),
            message=str(error),
            sql_state="",
            command="MySQL_real_connect",
        )
        status.apply_to_logging_data(context.file_access.logging_data)
        context.status(status.fs_reply, status.we_error)
        return ba999_end(context)  # Class 3

    outcome.apply_to_logging_data(context.file_access.logging_data)
    context.status(outcome.fs_reply, outcome.we_error)
    if int(outcome.fs_reply) != 0:
        # `if fs-reply not = zero  go to ba999-end.` [:L460-L461] - Class 3. Note what
        # this path does NOT do: no `WS-File-Key`, and no `set Cursor-Not-Active`.
        return ba999_end(context)

    _BRIDGE.connection = outcome.connection
    _write_file_key(context.file_access, _FILE_KEY_OPEN)      # [:L466]
    # `set Cursor-Not-Active to true` - the PRIMARY cursor only [:L467].
    context.slot_state(CursorSlot.PRIMARY).set_cursor_not_active()
    return ba999_end(context)                                 # [:L468] - Class 3


def ba030_process_close(context: _BridgeContext) -> tuple[int, int]:
    """``ba030-Process-Close.`` - [common/otm3MT.cbl:L474-L486]. Free, then disconnect.

    ::

        if      Cursor-Active   perform ba998-Free.            [:L475-L476]
        move     2 to ws-No-Paragraph.                         [:L479]
        move    "CLOSE SL OTM3" to WS-File-Key.                [:L480]
        PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT          [:L483]
        go      to ba999-end.                                  [:L486]

    ⭐ THE ``perform`` AT [:L476] IS NOT A ``go to``, AND THE DIFFERENCE IS LOAD-BEARING.
    ``ba998-Free`` has no ``go to`` of its own and FALLS THROUGH into ``ba999-end``
    [:L1309-L1321], so a ``go to ba998-Free`` runs the free AND THEN the logging exit,
    while this ``perform`` of the paragraph runs the free ONLY and returns here. Both
    forms appear in this bridge - ``ba050`` uses both - and they are reproduced as two
    different call shapes rather than one.

    ⭐ ONLY ``Cursor-Active`` - the PRIMARY flag - is tested, so a close following a
    sorted read frees nothing: the secondary or tertiary result set is abandoned to the
    connection teardown. Anomaly N-ba998-frees-primary-only, seen from the close side.

    ⭐ ``MYSQL-1980-CLOSE`` sets no status, so the pair returned is whatever ``ba010``
    left - which, since ``ba010`` does not clear it, is whatever THE CALLER passed in.

    Transfers: ``go to ba999-end``, Class 3.
    """
    # `if Cursor-Active perform ba998-Free.` [:L475-L476]. PERFORM, so the fall-through
    # into `ba999-end` does NOT happen here.
    if context.slot_state(CursorSlot.PRIMARY).cursor_active():
        ba998_free(context)

    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba030-Process-Close"
    ]                                                          # [:L479]
    _write_file_key(context.file_access, _FILE_KEY_CLOSE)       # [:L480]
    # `PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT` [:L483]. No status is written.
    mysql_1980_close(_BRIDGE.connection)  # type: ignore[arg-type]
    mysql_1999_exit()
    _BRIDGE.connection = None
    return ba999_end(context)                                  # [:L486] - Class 3


def _capture_driver_error(context: _BridgeContext, result: _CommandResult) -> None:
    """``call "MySQL_errno" ... "MySQL_sqlstate" ... "MySQL_error"`` - the shared ladder.

    Nine paragraphs contain this same block, always in this order and always with the
    same nesting::

        call  "MySQL_errno"    using WS-MYSQL-Error-Number
        call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
        move  WS-MYSQL-SqlState   to SQL-State
        if    WS-MYSQL-Error-Number  not = "0  "
              move WS-MYSQL-Error-Number  to SQL-Err
              call "MySQL_error" using WS-MYSQL-Error-Message
              move WS-MYSQL-Error-Message to SQL-Msg
        end-if

    ``SQL-State`` IS SET UNCONDITIONALLY; ``SQL-Err`` and ``SQL-Msg`` are set ONLY when the
    driver reports a non-zero error number. The maintainer's own comment on the test reads
    ``*> set non '0' if no rows ?`` [common/otm3MT.cbl:L540], and a second at [:L546]
    doubts the whole block - it is kept exactly as written.

    Sites: ``ba040`` [:L536-L545], ``ba041`` [:L619-L630], ``ba050`` [:L732-L744],
    ``ba060`` [:L825-L833], ``ba070`` [:L873-L887], ``ba080`` [:L925-L932],
    ``ba090`` [:L963-L970], ``ba141`` [:L1104-L1115], ``ba151`` [:L1258-L1269]. The order
    of the two moves inside the ``if`` differs between sites - ``ba040`` moves the number
    before calling ``MySQL_error``, ``ba041`` after - which changes nothing observable and
    is not modelled per-site.
    """
    _write_sql_fields(
        context.file_access,
        sql_state=result.sql_state,
        sql_err=result.errno if result.driver_reported_error else None,
        sql_msg=result.message if result.driver_reported_error else None,
    )


def ba040_process_read_next(context: _BridgeContext) -> tuple[int, int]:
    """``ba040-Process-Read-Next.`` - [common/otm3MT.cbl:L488-L562]. SELECT, then fetch.

    Positions a cursor on the whole table in key order, then FALLS THROUGH into
    ``ba041-Reread`` to deliver the first row. On every subsequent CALL the cursor is
    already active, the whole ``if`` is skipped, and control reaches ``ba041`` directly -
    which is how one paragraph pair serves both "open the sequence" and "advance it".

    ::

        if       Cursor-Not-Active                                  [:L493]
                 set      KOR-x1 to 1                               [:L494]
                 move     KOR-offset (KOR-x1) to K                  [:L495]
                 move     KOR-length (KOR-x1) to L                  [:L496]
                 move     spaces to WS-Where                        [:L497]
                 move     1   to J                                  [:L498]
                 string   "`" KeyName "`" " >= " '"000000000000000"'
                          ' ORDER BY ' "`" keyname "`" ' ASC'
                                      into ws-Where with pointer J  [:L500-L513]
                 move     ws-Where (1:J) to WS-Log-Where             [:L514]
                 move     3 to ws-No-Paragraph                      [:L516]
                 <SELECT * FROM `SAITM3-REC` WHERE <slice>;>         [:L520-L526]
                 move    "000000000000000" to WS-File-Key            [:L530]
                 if WS-MYSQL-Count-Rows = zero  ... (10,10) "No Data" -> ba999-End
                 set      Cursor-Active to true                      [:L549]
                 move     WS-MYSQL-Count-Rows to WS-Temp-ED-Row      [:L550]
                 string   "> 0 got cnt=" ... " recs for INVOICE-RECORD Table"  [:L551-L556]
                 perform ba999-End                                   [:L557]
        end-if.

    ⭐ ``K`` AND ``L`` ARE COMPUTED AND NEVER USED. The predicate embeds a LITERAL low key,
    not a slice of the record, so the offset and length fetched at [:L495-L496] are dead
    here. ``ba050``, ``ba060``, ``ba080`` and ``ba090`` all compute them and DO use them.

    ⭐ ``perform ba999-End`` AT [:L557] IS A PERFORM, NOT A ``go to``: the logging exit runs
    and control RETURNS, so execution then falls out of the ``end-if`` and straight into
    ``ba041-Reread``, which fetches the first row and writes its own status over the one
    just logged. So a successful positioning logs TWICE - once with the row count in
    ``WS-File-Key`` and once with the key of the first row. AAP section 0.4.2 Class 4:
    a named call followed by explicit fall-through. Reproduced.

    ⭐ THE EMPTY-TABLE PATH RETURNS ``(10, 10)`` - not ``(10, 0)``. The maintainer's own
    comment says so: ``*> should be 0 'JIC' likewise the others`` [:L544]. Both fields
    carry 10, which is what ``dal/status.py`` publishes as the paired end-of-file value.

    ⭐ THE LOG STRING SAYS ``" recs for INVOICE-RECORD Table"`` [:L555] - the wrong table.
    This is the OPEN-ITEM table; the text is a copy-paste from a sales-invoice bridge, the
    same family as anomaly N-false-occurs-comment. Reproduced verbatim.

    Transfers: ``go to ba999-End`` on the empty table, Class 3; the ``perform ba999-End``
    then fall-through, Class 4.
    """
    primary = context.slot_state(CursorSlot.PRIMARY)
    if primary.cursor_not_active():                              # [:L493]
        # `set KOR-x1 to 1` / `move KOR-offset (KOR-x1) to K` / `... to L` [:L494-L496].
        # Fetched exactly as the COBOL does, and - uniquely among the paragraphs that
        # fetch them - never used, because the predicate embeds a literal low key.
        # NO RECORD HERE. Three frozen `move`s that display nothing, whose whole
        # interest is that the values go unused - a fact about the SOURCE, recorded in
        # the comment above and in `docs/migration/anomaly-log.md`, not an event.
        # `KEY_OF_REFERENCE.kor_offset` and `.kor_length` are the two values the
        # frozen `move`s copy; nothing binds them here because nothing reads them.
        # `move spaces to WS-Where` / `move 1 to J` / the STRING [:L497-L513].
        context.ws_where = _ws_where_1_to_j(_sequential_predicate())
        _write_log_where(context.file_access, context.ws_where)   # [:L514]
        context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
            "ba040-Process-Read-Next"
        ]                                                        # [:L516]

        statement = _select_statement(context.ws_where)           # [:L520-L526]
        result = _mysql_1210_command(context, statement, store_result=True)
        context.count_rows = result.count_rows
        # `move "000000000000000" to WS-File-Key` [:L530] - the low key, not a row key.
        _write_file_key(context.file_access, _SEQUENTIAL_START.low_key)
        # `if Testing-2 display Display-Message-1 with erase eos` [:L531-L533] - deviation
        # D2: the diagnostic becomes a log record and the control flow is unchanged.
        if _testing_2(context.dal_common):
            #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
            #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
            #  customer and invoice key as a literal - or the statement itself. Both are
            #  forbidden in a record by the safe-event schema (CWE-532), and
            #  `sanitise_for_log` escaped them rather than removing them. This was a
            #  developer's trace read at the terminal beside the running program; nothing
            #  acts on it operationally. `WS-Where` is still BUILT and still stored in
            #  `Logging-Data`, because the bridge's own statements read it (R-3).
            pass

        if result.count_rows == 0:                                # [:L536]
            _capture_driver_error(context, result)                # [:L537-L545]
            # `move 10 to fs-reply` then `move 10 to WE-Error` - two statements, one pair
            # [:L543-L544]. The comment reads `*> should be 0 'JIC' likewise the others`.
            context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))
            _write_file_key(context.file_access, _FILE_KEY_NO_DATA)   # [:L545]
            return ba999_end(context)                             # [:L546] - Class 3

        primary.store_result(result.rows)                         # the stored result set
        primary.set_cursor_active()                               # [:L549]
        _BRIDGE.ws_temp_ed_row = result.count_rows                # [:L550]
        # `string "> 0 got cnt=" WS-Temp-ED-Row " recs for INVOICE-RECORD Table"`
        # [:L551-L556]. `WS-Temp-ED-Row` is `pic 9(7)`, so the count is zero-filled to
        # seven digits inside the message. "INVOICE-RECORD" is the wrong table name and is
        # reproduced as written.
        _write_file_key(
            context.file_access,
            f"> 0 got cnt={_BRIDGE.ws_temp_ed_row:07d}"
            " recs for INVOICE-RECORD Table",
        )
        # `perform ba999-End` [:L557] - Class 4. Logs, RETURNS, and falls through.
        ba999_end(context)

    # Fall-through out of the `end-if` at [:L562] into `ba041-Reread` - reached both by
    # falling out of the block above and by skipping it entirely on a later CALL.
    return ba041_reread(context)


def _fetch_one_row(
    context: _BridgeContext,
    state: CursorState,
    *,
    paragraph: str,
    slot_locator: str,
) -> tuple[int, int]:
    """The body shared, statement for statement, by ``ba041``, ``ba141`` and ``ba151``.

    The three reread paragraphs are textually identical apart from three things: the
    ``ws-No-Paragraph`` they stamp (4, 22, 22), the cursor flag they clear
    (``Cursor-Not-Active``, ``-2``, ``-3``) and the casing of ``HV-OI3-KEY`` versus
    ``HV-OI3-Key`` in the final move. Those three are parameters here; everything else is
    one body, because the frozen text is one body copied three times::

        move     spaces to WS-Log-Where.                     [:L566]
        move     N to ws-No-Paragraph.                        [:L567]
        move     zero to return-code.                         [:L568]
        CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT ...   [:L573-L603]
        if       return-code = -1                             [:L607]
                 move 10 to fs-Reply WE-Error                 [:L608-L609]
                 move    "EOF" to WS-File-Key                 [:L610]
                 set Cursor-Not-Active to true                [:L611]
                 go to ba999-End                              [:L612]
        end-if
        if       WS-MYSQL-Count-Rows = zero                   [:L615]
                 <driver error ladder, and INSIDE the if:>
                       initialize WS-OTM3-Record with filler   [:L626]
                       move    "EOF2" to WS-File-Key           [:L627]
                 move 10 to fs-reply / move 10 to WE-Error     [:L629-L630]
                 set Cursor-Not-Active to true                 [:L631]
                 go to ba999-End                               [:L632]
        end-if.
        if       fs-reply = 10                                 [:L635]
                 set Cursor-Not-Active to true                 [:L636]
                 move    "EOF3" to WS-File-Key                 [:L637]
                 go to ba999-End                               [:L638]
        end-if.
        perform  bb100-UnloadHVs.                              [:L641]
        move     HV-OI3-KEY to WS-File-Key.                    [:L642]
        move     zero to fs-reply WE-Error.                    [:L643]
        go       to ba999-end.                                 [:L644]

    ⭐ THREE END-OF-FILE PATHS, THREE DIFFERENT ``WS-File-Key`` VALUES, ONE STATUS PAIR.
    ``"EOF"`` is the real one; ``"EOF2"`` is guarded by ``*> no data but should not happen
    here`` [:L615]; ``"EOF3"`` by ``*> should not happen as tested prior`` [:L635]. All
    three return ``(10, 10)`` - or in the ``EOF3`` case, whatever the caller's 10 already
    was, since that path writes no status at all.

    ⭐ THE ``EOF3`` PATH IS REACHABLE ONLY BECAUSE ``ba010`` DOES NOT CLEAR ``Fs-Reply``.
    Nothing in this CALL can have set it to 10 before this test - the two paths that do so
    both transfer away first - so the only way ``fs-reply = 10`` here is that THE CALLER
    passed 10 in. The maintainer's "should not happen" is therefore wrong in a specific,
    reproducible way: a caller that reads to end of file and then reads again without
    clearing its own status gets ``EOF3`` rather than ``EOF``. Both are end of file, so
    nothing downstream diverges - which is exactly why it has survived.

    ⭐ ``initialize WS-OTM3-Record with filler`` AT [:L626] IS INSIDE THE INNER ``if``.
    The record is blanked only when the driver reports an error number; a zero row count
    with a clean errno leaves the record holding the PREVIOUS row. Reproduced by placing
    the initialise inside the same branch.

    ⭐ ``move zero to return-code`` [:L568] and the ``return-code = -1`` test [:L607] are
    the fetch's only end-of-data signal. The stored result set is walked by
    ``CursorState.fetch_record``, which returns ``None`` at the end - that ``None`` IS
    ``return-code = -1``.
    """
    _write_log_where(context.file_access, "")                    # [:L566]
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        paragraph
    ]                                                            # [:L567]
    context.return_code = 0                                      # [:L568]

    # `CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT HV-OI3-KEY ...` [:L573-L603].
    row = state.fetch_record()
    if row is None:
        context.return_code = -1
    else:
        _mysql_fetch_record(context.group, row)
        context.count_rows = 1

    if context.return_code == -1:                                # [:L607]
        context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))  # [:L608-L609]
        _write_file_key(context.file_access, _FILE_KEY_EOF)       # [:L610]
        state.set_cursor_not_active()                             # [:L611] - see locator
        # NO RECORD HERE. `set Cursor-Not-Active to true` displays nothing, and which
        # of the three flags each paragraph clears is documented in this function's own
        # docstring - the place a reader looks for it.
        return ba999_end(context)                                # [:L612] - Class 3

    if context.count_rows == 0:                                  # [:L615]
        result = _CommandResult(
            count_rows=0, errno=_ERRNO_CLEAN, message="", sql_state=""
        )
        _capture_driver_error(context, result)                   # [:L616-L628]
        if result.driver_reported_error:
            # `initialize WS-OTM3-Record with filler` [:L626] - INSIDE the inner `if`.
            _initialize_oi_header_in_place(context.record, with_filler=True)
            _write_file_key(context.file_access, _FILE_KEY_EOF2)  # [:L627]
        context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))  # [:L629-L630]
        state.set_cursor_not_active()                             # [:L631]
        return ba999_end(context)                                # [:L632] - Class 3

    if int(context.fs_reply) == int(FsReply.END_OF_FILE):        # [:L635]
        # Reachable only through the caller's own uncleared status - see the docstring.
        state.set_cursor_not_active()                             # [:L636]
        _write_file_key(context.file_access, _FILE_KEY_EOF3)      # [:L637]
        return ba999_end(context)                                # [:L638] - Class 3

    # `perform bb100-UnloadHVs.` [:L641]. The 26 moves; `HV-OI3-KEY` and `HV-OI3-BATCH`
    # are NOT among them - anomaly N-two-write-only-columns.
    unloaded = bb100_unload_hvs(context.group)
    _copy_oi_header(unloaded, context.record)
    # `move HV-OI3-KEY to WS-File-Key.` [:L642]. THE HOST VARIABLE, not the record: the
    # derived key that was never unloaded is nonetheless what gets logged.
    _write_file_key(
        context.file_access, str(context.group.hv_oi3_key)
    )
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))        # [:L643]
    return ba999_end(context)                                    # [:L644] - Class 3


def ba041_reread(context: _BridgeContext) -> tuple[int, int]:
    """``ba041-Reread.`` - [common/otm3MT.cbl:L563-L644]. Fetch one row, primary cursor.

    Entered by fall-through from ``ba040-Process-Read-Next``, never by a ``go to``. Stamps
    ``ws-No-Paragraph`` 4 and clears ``Most-Cursor-Set``.

    ⭐ THE PARAGRAPH NAME IS ``ba041-Reread`` HERE, while the HANDLER's paragraph in the
    same numeric slot is ``aa041-Move-Inv-Data`` [common/acas019.cbl:L390] and does
    something entirely different - it builds a logging key. Anomaly
    N-aa041-move-inv-data: the two programs use the same number for unrelated work, and
    neither name is renamed to match the other.
    """
    return _fetch_one_row(
        context,
        context.slot_state(CursorSlot.PRIMARY),
        paragraph="ba041-Reread",
        slot_locator="[common/otm3MT.cbl:L611] Most-Cursor-Set",
    )


def ba050_process_read_indexed(context: _BridgeContext) -> tuple[int, int]:
    """``ba050-Process-Read-Indexed.`` - [common/otm3MT.cbl:L646-L755]. One row, by key.

    ::

        set      KOR-x1 to 1.                                       [:L649]
        move     KOR-offset (KOR-x1) to K / KOR-length to L         [:L650-L651]
        move     spaces to WS-Where / move 1 to J                   [:L652-L653]
        string   "`" KeyName "`" '="' WS-OTM3-Record (K:L) '"'
                              into WS-Where with pointer J          [:L654-L665]
        move     WS-Where (1:J)   to WS-Log-Where.                  [:L666]
        move     5 to ws-No-Paragraph                               [:L669]
        <SELECT * FROM `SAITM3-REC` WHERE <slice>;>                 [:L673-L679]
        if     WS-MYSQL-Count-Rows = zero                           [:L681]
               move 23  to fs-Reply    *> could also be 21 or 14     [:L682]
               move zero to WE-Error                                [:L683]
               go to ba998-Free                                     [:L684]
        end-if
        move     6 to ws-No-Paragraph                               [:L686]
        CALL "MySQL_fetch_record" ...                               [:L690-L729]
        if       WS-MYSQL-Count-Rows not > zero                     [:L731]
                 <error ladder; 990 with an errno, 989 without>     [:L732-L744]
                 move 23   to fs-reply                              [:L745]
                 move spaces to WS-File-Key                         [:L746]
                 go to ba998-Free                                   [:L747]
        end-if
        perform bb100-UnloadHVs                                     [:L750]
        move     HV-OI3-KEY to WS-File-Key.                         [:L751]
        move     zero to FS-Reply WE-Error.                         [:L752]
        perform  ba998-Free.                                        [:L753]
        go       to ba999-End.                                      [:L754]

    ⭐⭐ ANOMALY N-read-indexed-23: THE KEY-NOT-FOUND STATUS IS ``23``, NOT ``21``, AND THE
    TWO BRIDGES DISAGREE. This one writes ``move 23 to fs-Reply`` with the comment
    ``*> could also be 21 or 14``; ``glpostingMT`` writes ``move 21 to fs-Reply`` with the
    comment ``*> could also be 23 or 14`` and carries ``*> from 23`` twice more. Each
    bridge documents the OTHER's answer as the one it rejected. This module therefore owns
    its read-indexed status rather than delegating to ``cursor_state.read_indexed``, whose
    published value is ``glpostingMT``'s 21. The delegation would have been silently wrong.

    ⭐ TWO PATHS SET ``fs-Reply`` 23 AND THEY DIFFER IN ``WE-Error``. The no-rows path sets
    ``WE-Error`` to ZERO [:L683]; the failed-fetch path sets it to 990 or 989 [:L735, :L740]
    and additionally blanks ``WS-File-Key`` [:L746]. A caller reading only ``fs-Reply``
    cannot tell an absent row from a broken fetch.

    ⭐ ``ba998-Free`` IS REACHED BY ``go to`` ON THE TWO FAILURE PATHS AND BY ``perform`` ON
    THE SUCCESS PATH. The ``go to`` form falls through into ``ba999-end``; the ``perform``
    form returns here and the explicit ``go to ba999-End`` at [:L754] follows. The observable
    outcome is the same and the two shapes are reproduced as written.

    ⭐ THE CURSOR IS FREED ON EVERY PATH, so a read-indexed never leaves a cursor active -
    which is why an indexed read can be issued in the middle of a sequential walk and will
    destroy it. Reproduced; ``ba998-Free`` clears the PRIMARY flag whatever slot was in use.

    Transfers: ``go to ba998-Free`` twice, Class 4 followed by the fall-through;
    ``go to ba999-End`` once, Class 3.
    """
    # `set KOR-x1 to 1` / offset / length [:L649-L651] - used here, unlike in `ba040`.
    key_value = _oi_key_image(context.record)[
        KEY_OF_REFERENCE.kor_offset - 1 : KEY_OF_REFERENCE.kor_offset
        - 1
        + KEY_OF_REFERENCE.kor_length
    ]
    # `move spaces to WS-Where` / `move 1 to J` / the STRING [:L652-L665].
    context.ws_where = _ws_where_1_to_j(_key_predicate())
    _write_log_where(context.file_access, context.ws_where)      # [:L666]
    if _testing_2(context.dal_common):                           # [:L667-L668] - D2
    #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
    #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
    #  customer and invoice key as a literal - or the statement itself. Both are
    #  forbidden in a record by the safe-event schema (CWE-532), and
    #  `sanitise_for_log` escaped them rather than removing them. This was a
    #  developer's trace read at the terminal beside the running program; nothing
    #  acts on it operationally. `WS-Where` is still BUILT and still stored in
    #  `Logging-Data`, because the bridge's own statements read it (R-3).
        pass
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba050-Process-Read-Indexed"
    ]                                                            # [:L669]

    statement = _select_statement(context.ws_where)              # [:L673-L679]
    result = _mysql_1210_command(context, statement, (key_value,), store_result=True)
    context.count_rows = result.count_rows

    if result.count_rows == 0:                                   # [:L681]
        # ANOMALY N-read-indexed-23: 23 here, 21 in `glpostingMT` [:L682].
        context.status(FsReply.KEY_NOT_FOUND, int(WeError.SUCCESS))  # [:L682-L683]
        ba998_free(context)                                      # `go to` [:L684]
        return ba999_end(context)                                # ba998 falls through

    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba050-Fetch"
    ]                                                            # [:L686]
    # `CALL "MySQL_fetch_record"` [:L690-L729]. The result was stored, so the single row
    # is taken from it directly - a read-indexed positions no cursor for a later fetch.
    row = result.rows[0] if result.rows else None
    if row is None:
        context.count_rows = 0
    else:
        _mysql_fetch_record(context.group, row)

    if context.count_rows <= 0:                                  # `not > zero` [:L731]
        _write_sql_fields(context.file_access, sql_state=result.sql_state)  # [:L734]
        if result.driver_reported_error:                         # [:L735]
            context.we_error = int(WeError.UNKNOWN_UNEXPECTED)    # 990 [:L736]
            _write_sql_fields(
                context.file_access, sql_err=result.errno, sql_msg=result.message
            )                                                    # [:L737-L739]
        else:
            context.we_error = int(WeError.READ_INDEXED_UNEXPECTED)  # 989 [:L741]
            # `move zero to SQL-Err` - ZERO, not spaces [:L742]; `spaces to SQL-Msg` [:L743].
            _write_sql_fields(context.file_access, sql_err="0", sql_msg="")
        context.status(FsReply.KEY_NOT_FOUND, context.we_error)   # [:L745]
        _write_file_key(context.file_access, "")                 # [:L746]
        ba998_free(context)                                      # `go to` [:L747]
        return ba999_end(context)                                # ba998 falls through

    unloaded = bb100_unload_hvs(context.group)                   # [:L750]
    _copy_oi_header(unloaded, context.record)
    # `move HV-OI3-KEY to WS-File-Key.` [:L751] - the host variable, never unloaded into
    # the record (anomaly N-two-write-only-columns) yet logged from here.
    _write_file_key(context.file_access, str(context.group.hv_oi3_key))
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))        # [:L752]
    ba998_free(context)                                          # `perform` [:L753]
    return ba999_end(context)                                    # [:L754] - Class 3


def ba060_process_start(context: _BridgeContext) -> tuple[int, int]:
    """``ba060-Process-Start.`` - [common/otm3MT.cbl:L756-L861]. Position, do not fetch.

    ::

        if       access-type < 5 or > 8                         [:L760]
                 move 99 to FS-Reply / move 997 to WE-Error     [:L761-L762]
                 go to ba999-end                                [:L763]
        end-if
        if       Cursor-Active  perform ba998-Free.             [:L766-L767]
        set      KOR-x1 to 1. / offset -> K / length -> L        [:L770-L772]
        move     spaces to MOST-Relation. / move 1 to J.        [:L773-L774]
        evaluate Access-Type  5 "=  " 6 "<  " 7 ">  " 8 ">= " 9 "<= "  [:L775-L787]
        move     spaces to WS-Where                             [:L788]
        string   "`" KeyName "`" MOST-relation '"' record(K:L) '"'
                 ' ORDER BY ' "`" keyname "`" ' ASC  '           [:L789-L802]
        move     WS-Where (1:J)  to WS-Log-Where.               [:L803]
        move     WS-OTM3-Record (K:L) to WS-File-Key            [:L804]
        move     8 to ws-No-Paragraph                           [:L808]
        <SELECT * FROM `SAITM3-REC` WHERE <slice>;>             [:L812-L818]
        if       WS-MYSQL-Count-Rows not zero  set Cursor-Active to true  [:L820-L822]
        if       WS-MYSQL-Count-Rows = zero
                 <error ladder>  move 21 to fs-reply / zero to WE-Error   [:L824-L835]
        else     move zero to FS-Reply WE-Error                 [:L837]
                 move WS-MYSQL-Count-Rows to WS-Temp-ED-Row     [:L838]
                 string MOST-relation record(K:L) " got " row " recs"  [:L839-L845]
        end-if
        go       to ba999-end.                                  [:L847]

    ⭐⭐ ANOMALY N-start-997-vs-998: THE HANDLER AND THE BRIDGE DISAGREE ON THE SAME GUARD.
    ``if access-type < 5 or > 8`` appears in both, and the handler moves 998
    [common/acas019.cbl:L437-L448] while the bridge moves 997 [:L762]. Each side keeps its
    own value; the ranges are identical and only the code differs. ``dal/status.py``
    publishes both: ``FILE_KEY_NO_OUT_OF_RANGE`` 998 and ``ACCESS_TYPE_WRONG`` 997.

    ⭐ ACCESS TYPE 9 IS DECLARED AND UNREACHABLE. The ``evaluate`` has an arm for
    ``fn-not-greater-than`` with the comment ``*> [ not currently used in ACAS ]`` [:L785],
    but the guard above admits 5..8 only, so ``"<= "`` can never be selected. The arm is
    reproduced regardless, because pruning it would delete the declaration.

    ⭐ THERE IS NO ``when other``. ``MOST-Relation`` was set to spaces immediately before
    [:L773], so an out-of-range access type would leave it blank and produce
    ``` `OI3-KEY`"key" ``` - a syntax error. Unreachable behind the guard, and reproduced by
    the absence of a default rather than by adding one.

    ⭐ THE CURSOR IS FLAGGED ACTIVE BEFORE THE ZERO TEST, IN A SEPARATE ``if`` [:L820-L822].
    Two consecutive tests on the same field where one ``if/else`` would do, so on a
    non-empty result the flag is set and THEN the ``else`` branch writes the status. The
    order is preserved because a future reader must see the same two tests.

    ⭐ ``move 21 to fs-reply`` ON AN EMPTY RESULT, with ``WE-Error`` zeroed and the comment
    ``*> this may need changing for val in WE-Error!!`` [:L834]. 21 is
    ``INVALID_KEY_ON_START``, distinct from the 23 ``ba050`` uses for the same emptiness.

    ⭐ ``WS-File-Key`` IS WRITTEN TWICE ON SUCCESS - the bare key at [:L804] and then the
    ``relation + key + " got " + count + " recs"`` string at [:L839-L845], which overwrites
    it. On the empty path the second write does not happen, so the bare key survives.

    Transfers: ``go to ba999-end`` twice, both Class 3.
    """
    access_type = int(context.file_access.access_type)
    # `if access-type < 5 or > 8` [:L760], with the inline comment
    # `*> not using not < or not >`. The bounds are NOT restated here: `dal/status.py`
    # holds the frozen (5, 8) pair in its own `START_ACCESS_TYPE_RANGE` and
    # `start_access_type_is_valid` is the single reader of it, so calling the helper
    # rather than re-deriving `< 5 or > 8` locally is what stops the two modules drifting.
    if not start_access_type_is_valid(access_type):
        context.status(FsReply.ERROR, int(WeError.ACCESS_TYPE_WRONG))  # 997 [:L761-L762]
        # ONE ERROR, through the shared reporter. A refusal that returns 99 to the
        # caller is a FAILURE, and WARNING put it below the level an operator watches.
        log_handler_failure(
            _LOG,
            program=BRIDGE_PROGRAM_ID,
            paragraph="ba060-Process-Start",
            locator="[common/otm3MT.cbl:L760-L763]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            detail="Access-Type rejected with We-Error 997; the HANDLER rejects the "
            "identical range with 998 [common/acas019.cbl:L437-L448] - anomaly "
            "N-start-997-vs-998",
        )
        return ba999_end(context)                                # [:L763] - Class 3

    # `if Cursor-Active perform ba998-Free.` [:L766-L767] - PERFORM, no fall-through.
    if context.slot_state(CursorSlot.PRIMARY).cursor_active():
        ba998_free(context)

    # `set KOR-x1 to 1` / offset / length [:L770-L772].
    key_value = _oi_key_image(context.record)[
        KEY_OF_REFERENCE.kor_offset - 1 : KEY_OF_REFERENCE.kor_offset
        - 1
        + KEY_OF_REFERENCE.kor_length
    ]
    # `move spaces to MOST-Relation.` [:L773] then the `evaluate` [:L775-L787]. An arm that
    # does not match leaves the spaces - there is no `when other`.
    context.most_relation = ACCESS_TYPE_RELATION_ARMS.get(access_type, "   ")
    _BRIDGE.most_relation = context.most_relation
    # `move spaces to WS-Where` and the STRING [:L788-L802].
    context.ws_where = _ws_where_1_to_j(_start_predicate(context.most_relation))
    _write_log_where(context.file_access, context.ws_where)      # [:L803]
    _write_file_key(context.file_access, key_value)              # [:L804]
    if _testing_2(context.dal_common):                           # [:L805-L807] - D2
    #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
    #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
    #  customer and invoice key as a literal - or the statement itself. Both are
    #  forbidden in a record by the safe-event schema (CWE-532), and
    #  `sanitise_for_log` escaped them rather than removing them. This was a
    #  developer's trace read at the terminal beside the running program; nothing
    #  acts on it operationally. `WS-Where` is still BUILT and still stored in
    #  `Logging-Data`, because the bridge's own statements read it (R-3).
        pass
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba060-Process-Start"
    ]                                                            # [:L808]

    statement = _select_statement(context.ws_where)              # [:L812-L818]
    result = _mysql_1210_command(context, statement, (key_value,), store_result=True)
    context.count_rows = result.count_rows

    primary = context.slot_state(CursorSlot.PRIMARY)
    # `if WS-MYSQL-Count-Rows not zero  set Cursor-Active to true  end-if` [:L820-L822] -
    # a separate `if`, evaluated BEFORE the zero test below.
    if result.count_rows != 0:
        primary.store_result(result.rows)
        primary.position_at(key_value)
        primary.set_cursor_active()

    if result.count_rows == 0:                                   # [:L823]
        _capture_driver_error(context, result)                   # [:L824-L833]
        # `move 21 to fs-reply` then `move zero to WE-Error` [:L834-L835].
        context.status(FsReply.INVALID_KEY_ON_START, int(WeError.SUCCESS))
    else:
        context.status(FsReply.SUCCESS, int(WeError.SUCCESS))    # [:L837]
        _BRIDGE.ws_temp_ed_row = result.count_rows               # [:L838]
        # `string MOST-relation WS-OTM3-Record (K:L) " got " WS-Temp-ED-Row " recs"`
        # [:L839-L845]. NEITHER `MOST-relation` NOR the key is `delimited by space` here -
        # unlike the predicate at [:L792] - so both carry their full padded width into the
        # message. Reproduced: three characters of relation, fifteen of key.
        _write_file_key(
            context.file_access,
            f"{context.most_relation}{key_value}"
            f" got {_BRIDGE.ws_temp_ed_row:07d} recs",
        )
    return ba999_end(context)                                    # [:L847] - Class 3


def ba070_process_write(context: _BridgeContext) -> tuple[int, int]:
    """``ba070-Process-Write.`` - [common/otm3MT.cbl:L862-L889]. Load, insert, classify.

    ::

        perform  bb000-HV-Load.                                 [:L863]
        move     OI-Key to WS-File-Key.                         [:L864]
        move     zero to FS-Reply WE-Error SQL-State.           [:L865-L867]
        move     spaces to SQL-Msg                              [:L868]
        move     zero to SQL-Err                                [:L869]
        move     10 to ws-No-Paragraph.                         [:L870]
        perform  bb200-Insert.                                  [:L871]
        if       WS-MYSQL-COUNT-ROWS not = 1                    [:L872]
                 <errno, sqlstate, SQL-State>                   [:L873-L875]
                 move  99 to fs-reply                           [:L876]
                 if    WS-MYSQL-Error-Number  not = "0  "       [:L877]
                       <MySQL_error, SQL-Err, SQL-Msg>          [:L878-L880]
                       if    SQL-Err (1:4) = "1062" or = "1022" [:L881-L882]
                             or Sql-State = "23000"             [:L883]
                              move 22 to fs-reply               [:L884]
                       end-if
                 end-if
        end-if
        go       to ba999-End.                                  [:L888]

    ⭐ ``WE-Error`` IS NEVER SET ON THE FAILURE PATH. It was zeroed at [:L866] and the
    failure branch moves 99 into ``fs-reply`` alone, so a failed insert reports
    ``(99, 0)`` - a hard error with no error code. ``ba080`` sets 995 and ``ba090`` sets
    994 for the analogous failure; the write sets nothing. Reproduced.

    ⭐ THE DUPLICATE-KEY TEST IS NESTED TWO DEEP INSIDE THE ERRNO TEST. A driver that
    reported SQLSTATE 23000 but a zero errno would never reach [:L883], so the duplicate
    would be reported as a plain 99. ``is_duplicate_key_bridge_level`` publishes the
    combined test; it is called only INSIDE the errno branch, which preserves the nesting.

    ⭐ ``SQL-Err (1:4) = "1062"`` compares FOUR characters of a FIVE-character field, so a
    five-digit errno beginning 1062 would also match. Reproduced by the shared helper.

    ⭐ ``move zero to SQL-Err`` [:L869] puts ``"0"`` into a ``pic x(5)``, not ``"00000"``,
    and ``move spaces to SQL-Msg`` precedes it - two different clear values, in that order.

    Transfers: ``go to ba999-End``, Class 3.
    """
    # `perform bb000-HV-Load.` [:L863] - the 28 loads, including the two derived columns.
    group, _key_staging, _batch_staging = bb000_hv_load(context.record)
    context.group = group
    # `move OI-Key to WS-File-Key.` [:L864] - the RECORD's key here, not the host variable.
    _write_file_key(context.file_access, _oi_key_image(context.record))
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))        # [:L865-L866]
    _write_sql_fields(
        context.file_access, sql_state="0", sql_msg="", sql_err="0"
    )                                                            # [:L867-L869]
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba070-Process-Write"
    ]                                                            # [:L870]

    result = bb200_insert(context)                               # [:L871]
    context.count_rows = result.count_rows
    if result.count_rows != 1:                                   # [:L872]
        _write_sql_fields(context.file_access, sql_state=result.sql_state)  # [:L873-L875]
        # `move 99 to fs-reply` and NOTHING into `WE-Error`, which stays at the zero from
        # [:L866].
        context.status(FsReply.ERROR, context.we_error)           # [:L876]
        if result.driver_reported_error:                         # [:L877]
            _write_sql_fields(
                context.file_access, sql_err=result.errno, sql_msg=result.message
            )                                                    # [:L878-L880]
            # The duplicate test, nested inside the errno test [:L881-L885].
            if is_duplicate_key_bridge_level(
                context.file_access.logging_data.sql_err,
                context.file_access.logging_data.sql_state,
            ):
                context.status(FsReply.DUPLICATE_KEY, context.we_error)  # [:L884]
    return ba999_end(context)                                    # [:L888] - Class 3


def ba080_process_delete(context: _BridgeContext) -> tuple[int, int]:
    """``ba080-Process-Delete.`` - [common/otm3MT.cbl:L890-L943]. One row, by key.

    ::

        set      KOR-x1 to 1. / offset -> K / length -> L        [:L891-L893]
        move     spaces to WS-Where / move 1 to J               [:L894-L895]
        string   "`" KeyName "`" '="' record (K:L) '"'          [:L896-L907]
        move     WS-OTM3-Record (K:L)  to WS-File-Key.          [:L908]
        move     WS-Where (1:J)   to WS-Log-Where.              [:L909]
        move     13 to ws-No-Paragraph.                         [:L913]
        <DELETE FROM `SAITM3-REC` WHERE <slice>>                [:L917-L923]
        if       WS-MYSQL-COUNT-ROWS not = 1                    [:L925]
                 <error ladder>                                 [:L926-L932]
                 move 99 to fs-reply / move 995 to WE-Error     [:L933-L934]
                 go to ba999-End                                [:L935]
        else     move spaces to SQL-Msg / move zero to SQL-Err  [:L937-L938]
        end-if.
        go       to ba999-End.                                  [:L941]

    ⭐ THE DELETE HAS NO TRAILING SEMICOLON. The INSERT [:L1788] and the UPDATE [:L2175]
    both end ``";" X"00"``; this one ends ``X"00"`` alone [:L923]. Harmless to a
    single-statement protocol, and reproduced because the statement text is what
    ``WS-Log-Where``'s companion records.

    ⭐ ANOMALY N-string-pointer-overrun IS VISIBLE HERE. The predicate is the untrimmed
    ``WS-Where (1:J)`` slice, so the statement ends with a trailing space before nothing at
    all - no semicolon to hide it.

    ⭐ ``WS-File-Key`` IS WRITTEN BEFORE ``WS-Log-Where``, the reverse of ``ba050``'s order.
    Both are logging-only, and both orders are transcribed as found.

    ⭐ TWO ``go to ba999-End`` STATEMENTS, ONE REACHABLE PER PATH. The failure branch
    transfers at [:L935]; the ``else`` branch falls to the identical transfer at [:L941].
    The duplicate is in the frozen source and is reproduced as two distinct returns.

    ⭐ NO DUPLICATE-KEY CLASSIFICATION HERE, unlike ``ba070``: a delete that matches no row
    is simply ``(99, 995)``, with no attempt to distinguish "absent" from "broken".

    Transfers: ``go to ba999-End`` twice, both Class 3.
    """
    # `set KOR-x1 to 1` / offset / length [:L891-L893].
    key_value = _oi_key_image(context.record)[
        KEY_OF_REFERENCE.kor_offset - 1 : KEY_OF_REFERENCE.kor_offset
        - 1
        + KEY_OF_REFERENCE.kor_length
    ]
    context.ws_where = _ws_where_1_to_j(_key_predicate())        # [:L894-L907]
    _write_file_key(context.file_access, key_value)              # [:L908]
    _write_log_where(context.file_access, context.ws_where)      # [:L909]
    if _testing_2(context.dal_common):                           # [:L910-L912] - D2
    #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
    #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
    #  customer and invoice key as a literal - or the statement itself. Both are
    #  forbidden in a record by the safe-event schema (CWE-532), and
    #  `sanitise_for_log` escaped them rather than removing them. This was a
    #  developer's trace read at the terminal beside the running program; nothing
    #  acts on it operationally. `WS-Where` is still BUILT and still stored in
    #  `Logging-Data`, because the bridge's own statements read it (R-3).
        pass
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba080-Process-Delete"
    ]                                                            # [:L913]

    # `DELETE FROM `SAITM3-REC` WHERE <slice>` - no semicolon [:L917-L923]. Note there is
    # no `MYSQL-1220-STORE-RESULT` here: a DELETE has no result set, so the count is the
    # AFFECTED-ROW count.
    statement = _delete_statement(context.ws_where)
    result = _mysql_1210_command(context, statement, (key_value,))
    context.count_rows = result.count_rows

    if result.count_rows != 1:                                   # [:L925]
        _capture_driver_error(context, result)                   # [:L926-L932]
        context.status(FsReply.ERROR, int(WeError.DELETE_SQLSTATE_NOT_00000))
        return ba999_end(context)                                # [:L935] - Class 3

    # `else move spaces to SQL-Msg / move zero to SQL-Err` [:L937-L938]. `SQL-State` is
    # NOT cleared here, so it keeps whatever `ba010` left - the "0" plus four spaces.
    _write_sql_fields(context.file_access, sql_msg="", sql_err="0")
    return ba999_end(context)                                    # [:L941] - Class 3


def ba090_process_rewrite(context: _BridgeContext) -> tuple[int, int]:
    """``ba090-Process-Rewrite.`` - [common/otm3MT.cbl:L944-L988]. Load, update, classify.

    ::

        perform  bb000-HV-Load.                                 [:L945]
       move     OI-Key to WS-File-Key.                          [:L946]  <- 4-space indent
       move     17 to ws-No-Paragraph.                          [:L947]  <- 4-space indent
        set      KOR-x1 to 1 / offset -> K / length -> L         [:L948-L950]
        move     spaces to WS-Where / move 1 to J               [:L951-L952]
        string   "`" KeyName "`" '="' record (K:L) '"'          [:L953-L964]
        move     WS-Where (1:J)   to WS-Log-Where.              [:L965]
        perform  bb300-Update.                                  [:L966]
        if       Testing-2  display ...                         [:L967-L969]
        if       WS-MYSQL-COUNT-ROWS not = 1                    [:L970]
                 <error ladder>                                 [:L971-L977]
                 move 99 to fs-reply / move 994 to WE-Error     [:L978-L979]
                 go to ba999-End                                [:L980]
        end-if
        move     zero   to FS-Reply WE-Error SQL-Err.           [:L982-L984]
        move     spaces to SQL-Msg.                             [:L985]
        go       to ba999-End.                                  [:L987]

    ⭐ ANOMALY N-punctuation, on the procedural side. [:L946] and [:L947] are indented FOUR
    spaces where every neighbouring statement uses five, so the two lines sit one column
    left of the block they belong to. Cosmetic, recorded, not normalised.

    ⭐ THE ``display`` COMES AFTER THE UPDATE, NOT BEFORE IT [:L967-L969]. Every other
    paragraph tests ``Testing-2`` before issuing its statement; this one has already
    updated the row by the time it would show the predicate. Reproduced in place.

    ⭐ THE STATUS IS ZEROED ONLY AT THE END, AFTER THE FAILURE TEST [:L982-L985]. So the
    values the caller passed in survive right through ``bb000-HV-Load`` and ``bb300-Update``
    - and the failure path at [:L978-L979] overwrites them without ever having cleared
    them. Reproduced by placing the clear after the test, as written.

    ⭐ THE UPDATE SETS ALL TWENTY-EIGHT COLUMNS INCLUDING THE PRIMARY KEY, and the key is
    also the whole of the predicate, so ``OI3-KEY`` is set to the value it is found by.
    Harmless and reproduced - see :func:`_update_statement`.

    Transfers: ``go to ba999-End`` twice, both Class 3.
    """
    group, _key_staging, _batch_staging = bb000_hv_load(context.record)  # [:L945]
    context.group = group
    # [:L946-L947] - the two four-space-indented statements (anomaly N-punctuation).
    _write_file_key(context.file_access, _oi_key_image(context.record))
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba090-Process-Rewrite"
    ]

    key_value = _oi_key_image(context.record)[
        KEY_OF_REFERENCE.kor_offset - 1 : KEY_OF_REFERENCE.kor_offset
        - 1
        + KEY_OF_REFERENCE.kor_length
    ]                                                            # [:L948-L950]
    context.ws_where = _ws_where_1_to_j(_key_predicate())        # [:L951-L964]
    _write_log_where(context.file_access, context.ws_where)      # [:L965]

    result = bb300_update(context, key_value)                    # [:L966]
    context.count_rows = result.count_rows
    if _testing_2(context.dal_common):                           # [:L967-L969] - AFTER
    #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
    #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
    #  customer and invoice key as a literal - or the statement itself. Both are
    #  forbidden in a record by the safe-event schema (CWE-532), and
    #  `sanitise_for_log` escaped them rather than removing them. This was a
    #  developer's trace read at the terminal beside the running program; nothing
    #  acts on it operationally. `WS-Where` is still BUILT and still stored in
    #  `Logging-Data`, because the bridge's own statements read it (R-3).
        pass

    if result.count_rows != 1:                                   # [:L970]
        _capture_driver_error(context, result)                   # [:L971-L977]
        context.status(FsReply.ERROR, int(WeError.REWRITE_SQLSTATE_NOT_00000))
        return ba999_end(context)                                # [:L980] - Class 3

    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))        # [:L982-L983]
    _write_sql_fields(context.file_access, sql_err="0", sql_msg="")  # [:L984-L985]
    return ba999_end(context)                                    # [:L987] - Class 3


def _sorted_read_next(
    context: _BridgeContext,
    *,
    function: FileFunction,
    slot: CursorSlot,
    paragraph: str,
    reread: Callable[[_BridgeContext], tuple[int, int]],
    file_key_suffix: str,
) -> tuple[int, int]:
    """The body ``ba140`` and ``ba150`` share, statement for statement.

    The two paragraphs differ in exactly four things: the cursor flag they test and set
    (``-2`` versus ``-3``), the ORDER BY literal, the reread they fall through into, and
    the tail of their success message. Everything else - including ``ws-No-Paragraph`` 21,
    which BOTH stamp - is one body copied twice in the frozen source.

    ::

        if       Cursor-Not-Active-N                              [:L995 / :L1151]
                 set      KOR-x1 to 1                            [:L996]
                 move     KOR-offset (KOR-x1) to K               [:L997]
                 move     KOR-length (KOR-x1) to L               [:L998]
                 move     spaces to WS-Where / move 1 to J       [:L999-L1000]
                 string   " ORDER BY " <single-quoted terms>     [:L1001-L1008]
                 move     ws-Where (1:J) to WS-Log-Where          [:L1009]
                 move     21 to ws-No-Paragraph                  [:L1010]
                 <SELECT * FROM `SAITM3-REC` WHERE <slice>;>      [:L1014-L1020]
                 move    "Sorted" to WS-File-Key                 [:L1023]
                 if WS-MYSQL-Count-Rows = zero ... (10,10) "No Data" -> ba999-End
                 set      Cursor-Active-N to true                [:L1043]
                 move     WS-MYSQL-Count-Rows to WS-Temp-Ed-Row  [:L1044]
                 string   "> 0 got cnt=" ... <suffix>            [:L1045-L1050]
                 perform ba999-End                               [:L1051]
        end-if.

    ⭐⭐ ANOMALY N-sorted-order-is-a-syntax-error. THREE INDEPENDENT DEFECTS COMPOUND HERE:

    1. ``WS-Where`` receives ONLY the ORDER BY clause - no predicate at all - while the
       SELECT template unconditionally emits ``" WHERE "`` [:L1017]. The statement is
       therefore ``SELECT * FROM `SAITM3-REC` WHERE  ORDER BY ...;``, which no SQL parser
       accepts.
    2. Every ORDER BY term is SINGLE-QUOTED, making it a string constant rather than a
       column reference. ``ORDER BY 'OI3-INVOICE'`` orders by the constant string, i.e.
       orders nothing - so even with the ``WHERE`` fixed, the sort would not happen.
    3. ``K`` and ``L`` are computed at [:L997-L998] and used by nothing, exactly as in
       ``ba040``.

    The outcome is a driver syntax error, which ``MYSQL-1210-COMMAND`` turns into
    ``(99, 911)`` and the ``= zero`` test then overwrites with ``(10, 10)`` and
    ``"No Data"`` - so THE CALLER SEES AN EMPTY TABLE, not an error. That is what makes the
    defect survivable and therefore invisible: a caller asking for a sorted read gets a
    clean end-of-file. Reproduced exactly, text included, because a syntax error is only
    reproducible if the text is.

    ⭐ ``ws-No-Paragraph`` 21 IS STAMPED BY BOTH PARAGRAPHS, and 22 by both rereads
    [:L1010, :L1067, :L1163, :L1221], so the stamp cannot tell the by-batch read from the
    by-customer read. Anomaly N-noparagraph-collision, inside a single program this time.

    ⭐ ``perform ba999-End`` [:L1051] IS AGAIN A PERFORM, so control returns and falls
    through into the paragraph's own reread - Class 4, as in ``ba040``.
    """
    state = context.slot_state(slot)
    if state.cursor_not_active():                                # [:L995]
        # `set KOR-x1 to 1` / offset / length [:L996-L998] - computed, then unused.
        # NO RECORD HERE, for the reason `ba040` gives: three `move`s that display
        # nothing and whose values go unused. `_EXTRA_READS` still carries this
        # paragraph's `source_locator` for the traceability tables.
        # `move spaces to WS-Where` / `move 1 to J` / the STRING [:L999-L1008]. The whole
        # of `WS-Where` is the ORDER BY - `_EXTRA_READS[function].predicate_present` is
        # False, which is the shared table's own record of the same fact.
        context.ws_where = _ws_where_1_to_j(_SORTED_ORDER_BY_TEXT[int(function)])
        _write_log_where(context.file_access, context.ws_where)   # [:L1009]
        context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
            paragraph
        ]                                                        # [:L1010]

        # The SELECT template emits " WHERE " with no predicate - defect 1 above.
        statement = _select_statement(context.ws_where)           # [:L1014-L1020]
        result = _mysql_1210_command(context, statement, store_result=True)
        context.count_rows = result.count_rows
        _write_file_key(context.file_access, _FILE_KEY_SORTED)    # [:L1023]
        if _testing_2(context.dal_common):                       # [:L1024-L1026] - D2
            #  THE `Testing-2` GUARD IS PRESERVED AND EMITS NOTHING.
            #  `Display-Message-1` renders `WS-Where (1:J)` - a SQL predicate carrying the
            #  customer and invoice key as a literal - or the statement itself. Both are
            #  forbidden in a record by the safe-event schema (CWE-532), and
            #  `sanitise_for_log` escaped them rather than removing them. This was a
            #  developer's trace read at the terminal beside the running program; nothing
            #  acts on it operationally. `WS-Where` is still BUILT and still stored in
            #  `Logging-Data`, because the bridge's own statements read it (R-3).
            pass

        if result.count_rows == 0:                               # [:L1029]
            _capture_driver_error(context, result)               # [:L1030-L1038]
            context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))  # [:L1037-L1038]
            _write_file_key(context.file_access, _FILE_KEY_NO_DATA)        # [:L1039]
            return ba999_end(context)                            # [:L1040] - Class 3

        state.store_result(result.rows)
        state.set_cursor_active()                                # [:L1043]
        _BRIDGE.ws_temp_ed_row = result.count_rows               # [:L1044]
        _write_file_key(
            context.file_access,
            f"> 0 got cnt={_BRIDGE.ws_temp_ed_row:07d}{file_key_suffix}",
        )                                                        # [:L1045-L1050]
        ba999_end(context)                                       # [:L1051] - Class 4

    # Fall-through out of the `end-if` into this paragraph's own reread.
    return reread(context)


def ba140_process_read_next(context: _BridgeContext) -> tuple[int, int]:
    """``ba140-Process-Read-Next.`` - [common/otm3MT.cbl:L989-L1061]. Function 32.

    ``fn-Read-By-Batch``, declared for OTM3/OTM5 at [copybooks/wsfnctn.cob:L103] and
    dispatched HERE - see docstring C1, which corrects the agent prompt's claim that codes
    32 and 33 are implemented nowhere. The HANDLER's dispatch omits them
    [common/acas019.cbl:L283-L302], so this arm is reachable only on the DAL path.

    ⭐ THE PROSE COMMENT ABOVE IT LISTS THE SORT TERMS IN THE REVERSE OF THE CODE'S ORDER::

        *>  Like 040 except we do order by B-Nos B-Item ASC, Type DES,   [:L991]
        *>              Date Invoice ASC                                 [:L992]

    The code orders by invoice and date first, then type descending, then batch item and
    batch nos [:L1002-L1007]. A second false comment, the same family as anomaly
    N-false-occurs-comment. Recorded; the CODE's order is what is reproduced.
    """
    return _sorted_read_next(
        context,
        function=FileFunction.READ_BY_BATCH,
        slot=CursorSlot.SECONDARY,
        paragraph="ba140-Process-Read-Next",
        reread=ba141_reread,
        # `" recs in sorted order"` [:L1049] - not `ba040`'s `" recs for INVOICE-RECORD
        # Table"`, and not `ba150`'s either.
        file_key_suffix=" recs in sorted order",
    )


def ba141_reread(context: _BridgeContext) -> tuple[int, int]:
    """``ba141-Reread.`` - [common/otm3MT.cbl:L1062-L1142]. Fetch one row, cursor 2.

    Identical to ``ba041-Reread`` apart from ``ws-No-Paragraph`` 22, the cursor flag
    ``Most-Cursor-Set-2``, and ``move HV-OI3-Key to WS-File-Key`` at [:L1139] - which
    spells the host variable ``HV-OI3-Key`` where ``ba041`` spells it ``HV-OI3-KEY``
    [:L642]. Anomaly N-casing, third instance in this program. Same field, same value.
    """
    return _fetch_one_row(
        context,
        context.slot_state(CursorSlot.SECONDARY),
        paragraph="ba141-Reread",
        slot_locator="[common/otm3MT.cbl:L1111] Most-Cursor-Set-2",
    )


def ba150_process_read_next(context: _BridgeContext) -> tuple[int, int]:
    """``ba150-Process-Read-Next.`` - [common/otm3MT.cbl:L1143-L1215]. Function 33.

    ``fn-Read-By-Cust``, declared at [copybooks/wsfnctn.cob:L104] with the note
    ``*> 09/02/17 for OTM3 (sl110, 120, 190)`` - three report programs, all of them out of
    scope for this migration [AAP section 0.2.2], which is why nothing in the migrated
    cycle issues this function. It is implemented because the bridge implements it.

    ⭐ ITS ORDER BY IS THE SHORTER OF THE TWO and carries ``ASC`` on the last pair only,
    letting the first three terms inherit: ``'OI3-CUSTOMER', 'OI3-DAT', 'OI3-INVOICE',
    'OI3-TYPE' ASC`` [:L1156-L1159]. Every term is single-quoted, so it orders nothing -
    the same three compounded defects as ``ba140``.
    """
    return _sorted_read_next(
        context,
        function=FileFunction.READ_BY_CUST,
        slot=CursorSlot.TERTIARY,
        paragraph="ba150-Process-Read-Next",
        reread=ba151_reread,
        # `" recs in sorted order"` [:L1203] - the same suffix as `ba140`, so the log line
        # cannot distinguish the two either. Third collision in the pair.
        file_key_suffix=" recs in sorted order",
    )


def ba151_reread(context: _BridgeContext) -> tuple[int, int]:
    """``ba151-Reread.`` - [common/otm3MT.cbl:L1216-L1296]. Fetch one row, cursor 3.

    Identical to ``ba141-Reread`` apart from the cursor flag ``Most-Cursor-Set-3``. It
    stamps the SAME ``ws-No-Paragraph`` 22 [:L1221] and uses the same ``HV-OI3-Key``
    casing [:L1293].
    """
    return _fetch_one_row(
        context,
        context.slot_state(CursorSlot.TERTIARY),
        paragraph="ba151-Reread",
        slot_locator="[common/otm3MT.cbl:L1265] Most-Cursor-Set-3",
    )


def ba100_bad_function(context: _BridgeContext) -> tuple[int, int]:
    """``ba100-Bad-Function.`` - [common/otm3MT.cbl:L1297-L1302].

    ::

    *> Houston; We have a problem                                [:L1299]
        move     990 to WE-Error.                                [:L1300]
        move     99 to Fs-Reply.                                 [:L1301]
        go       to ba999-end.                                   [:L1302]

    ⭐ THE BRIDGE SAYS 990 AND THE HANDLER SAYS 999 FOR THE SAME CONDITION. ``acas019``'s
    ``aa100-Bad-Function`` moves 999 [common/acas019.cbl:L528] - and carries the identical
    "Houston" comment. So an unrecognised function code reports ``(99, 999)`` on the
    flat-file path and ``(99, 990)`` on the DAL path. ``dal/status.py`` publishes 990 as
    ``UNKNOWN_UNEXPECTED`` and 999 as ``NOT_USED``; each side keeps its own.

    ⭐ 992 - ``INVALID_FUNCTION`` - is what the vocabulary reserves for exactly this, and
    NEITHER program uses it. Recorded; not substituted.

    ⭐ ``ba100`` IS REACHED ONE WAY ONLY here, from ``when other``. The handler reaches its
    equivalent TWO ways - ``when other`` and an unconditional fall-through at
    [common/acas019.cbl:L305] - see :func:`aa100_bad_function`.

    Transfers: ``go to ba999-end``, Class 3.
    """
    # ONE ERROR, through the shared reporter. `File-Function` is an operation code
    # from the frozen vocabulary [copybooks/wsfnctn.cob:L88-L118], not business data, so
    # it stays - the reporter renders it as its own field.
    log_handler_failure(
        _LOG,
        program=BRIDGE_PROGRAM_ID,
        paragraph="ba100-Bad-Function",
        locator="[common/otm3MT.cbl:L1300]",
        fs_reply=int(FsReply.ERROR),
        we_error=int(WeError.UNKNOWN_UNEXPECTED),
        detail="File-Function %d is not one this bridge implements; the bridge "
        "reports We-Error 990 where the handler reports 999 "
        "[common/acas019.cbl:L528]" % int(context.file_access.file_function),
    )
    context.status(FsReply.ERROR, int(WeError.UNKNOWN_UNEXPECTED))  # [:L1300-L1301]
    return ba999_end(context)                                      # [:L1302] - Class 3


def ba998_free(context: _BridgeContext) -> None:
    """``ba998-Free.`` - [common/otm3MT.cbl:L1309-L1319]. Release the result set.

    ::

        move     20 to ws-No-Paragraph.                          [:L1310]
        MOVE TP-SAITM3-REC TO WS-MYSQL-RESULT                    [:L1314]
        CALL "MySQL_free_result" USING WS-MYSQL-RESULT end-call  [:L1315]
        set      Cursor-Not-Active to true.                      [:L1318]

    ⭐⭐ ANOMALY N-ba998-frees-primary-only. THE PARAGRAPH ALWAYS CLEARS ``Most-Cursor-Set``,
    THE PRIMARY FLAG - never ``-2``, never ``-3``. So freeing after a function-32 or -33
    read releases the result set but leaves that cursor's flag ACTIVE, and the next sorted
    read of the same kind skips its SELECT and fetches from a freed result. In practice the
    sorted reads never reach a state where this bites, because their SELECT is a syntax
    error and the empty-table path clears their own flag - one defect masking another.
    Reproduced exactly: this function clears the primary flag and no other.

    ⭐ IT HAS NO ``go to`` AND FALLS THROUGH INTO ``ba999-end``. That makes the distinction
    between ``perform ba998-Free`` and ``go to ba998-Free`` observable - see
    :func:`ba030_process_close` for the analysis. This function reproduces the PARAGRAPH
    ONLY; every ``go to`` site calls it and then calls :func:`ba999_end` explicitly, with a
    comment saying so.

    ⭐ THE RESULT POINTER IS FREED FOR WHICHEVER SLOT HOLDS IT, because ``TP-SAITM3-REC`` is
    one pointer shared by all three cursors [:L300] - the bridge has one result pointer and
    three flags, which is the root of the asymmetry above. All three stored results are
    released here for that reason.
    """
    context.file_access.logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS[
        "ba998-Free"
    ]                                                            # [:L1310]
    # `CALL "MySQL_free_result" USING WS-MYSQL-RESULT` [:L1314-L1315]. One pointer,
    # `TP-SAITM3-REC` [:L300], so every slot's stored rows go.
    for slot in (CursorSlot.PRIMARY, CursorSlot.SECONDARY, CursorSlot.TERTIARY):
        context.slot_state(slot).free_result()
    # `set Cursor-Not-Active to true.` [:L1318] - PRIMARY ONLY, whatever slot was in use.
    context.slot_state(CursorSlot.PRIMARY).set_cursor_not_active()


def ba999_end(context: _BridgeContext) -> tuple[int, int]:
    """``ba999-end.`` - [common/otm3MT.cbl:L1321-L1326], then ``ba999-exit``.

    ::

    *>  Any Clean ups before quiting  move data record ?????  do so at the start as well ??????
        if       Testing-1                                       [:L1323]
                 perform Ca-Process-Logs                         [:L1324]
        end-if.                                                  [:L1325]

    Then falls through into ``ba999-exit. exit program.`` [:L1328-L1329], which is the
    return to ``acas019``.

    ⭐ THE BRIDGE DOES LOG, AND THE HANDLER DOES NOT - on the DAL path. ``acas019``'s
    ``Ca-Process-Logs`` carries its comment on the label line itself:
    ``*> Not called on DAL access as it does it already`` [common/acas019.cbl:L623].
    Anomaly N-nolog-on-dal: the logging happens exactly once per CALL, here, and the
    handler's ``aa999-main-exit`` is not reached on the DAL path at all because the RDB
    branch at [common/acas019.cbl:L262-L266] leaves for ``AA-Main-Exit`` (C2).

    ⭐ THE MAINTAINER'S COMMENT AT [:L1322] ASKS WHETHER THE DATA RECORD SHOULD BE MOVED
    HERE AND AT THE START. It is not moved at either point; each paragraph that produces a
    record does its own ``bb100-UnloadHVs``. Recorded, not acted on.
    """
    if _testing_1(context.dal_common):                           # [:L1323]
        otm3mt_ca_process_logs(context)                          # [:L1324]
    return ba999_exit(context)


def ba999_exit(context: _BridgeContext) -> tuple[int, int]:
    """``ba999-exit.  exit program.`` - [common/otm3MT.cbl:L1328-L1329].

    The return to the caller. ``File-Access`` already carries the status pair - every
    paragraph wrote it before transferring here - so the pair is returned as a convenience
    and NOT as the authoritative channel: the COBOL communicates through the linkage item,
    and so does this module.
    """
    return context.fs_reply, context.we_error


def bb200_insert(context: _BridgeContext) -> _CommandResult:
    """``bb200-Insert      Section.`` - [common/otm3MT.cbl:L1418-L1798].

    ``INSERT INTO `SAITM3-REC` SET `col`="value" , ... ;`` - one 370-line ``STRING``
    statement naming ALL TWENTY-EIGHT columns in table-ordinal order, then
    ``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT`` [:L1790].

    ⭐ EVERY COLUMN IS NAMED ON EVERY INSERT - never a subset. Combined with
    ``initialize TD-SAITM3-REC`` at the head of the load, that is what lets every column of
    this table be declared ``NOT NULL``: AAP section 0.6.2, "the Python layer must default
    rather than omit". NO parameter is ever ``None``.

    ⭐ EVERY VALUE IS RENDERED TEXT, DOUBLE-QUOTED IN THE FROZEN STATEMENT. Character
    columns go through ``FUNCTION TRIM (... TRAILING)``; numeric columns go through
    ``WS-MYSQL-EDIT`` and are sliced - which is where docstring C6's sign drop happens.
    Deviation D1 binds the identical strings instead of interpolating them.

    ⭐ ``MYSQL-1220-STORE-RESULT`` IS NOT PERFORMED HERE. An INSERT has no result set, so
    ``WS-MYSQL-Count-Rows`` is the AFFECTED-ROW count - which is why ``ba070`` tests
    ``not = 1`` rather than ``= zero``.
    """
    statement = _insert_statement()
    parameters = _insert_parameters(context.group)
    # Belt and braces on the NOT NULL invariant: 28 parameters, none of them None. The
    # assertion documents the invariant at the point it must hold and costs one comparison
    # per insert.
    if len(parameters) != len(COLUMNS) or any(
        parameter is None for parameter in parameters
    ):  # pragma: no cover - unreachable while `initialize` runs first
        # KEPT, and kept at ERROR. This is not a narration of frozen control flow -
        # the bridge has no such arm - it is a programming-error guard on an invariant
        # the schema imposes, and the two numbers it reports are COUNTS, which the
        # safe-event schema admits. No parameter VALUE is named.
        _LOG.error(
            "%s: bb200-Insert built %d parameters for %d columns; every column of "
            "SAITM3-REC is NOT NULL [mysql/ACASDB.sql:L896-L926]",
            BRIDGE_PROGRAM_ID,
            len(parameters),
            len(COLUMNS),
        )
    return _mysql_1210_command(context, statement, parameters)   # [:L1790]


def bb300_update(context: _BridgeContext, key_value: str) -> _CommandResult:
    """``bb300-Update      Section.`` - [common/otm3MT.cbl:L1799-L2180].

    ``UPDATE `SAITM3-REC` SET `col`="value" , ... WHERE FUNCTION TRIM (WS-Where (1:J));``
    then ``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT`` [:L2177].

    ⭐ ALL TWENTY-EIGHT COLUMNS ARE SET, THE PRIMARY KEY AMONG THEM [:L1815-L1818] - and
    the key is also the entire predicate, so the statement assigns ``OI3-KEY`` the value it
    selects by. Reproduced.

    ⭐ THE PREDICATE IS TRIMMED HERE AND NOWHERE ELSE [:L2173-L2175]. The SELECT and the
    DELETE embed the raw ``WS-Where (1:J)`` slice with its overrun space (anomaly
    N-string-pointer-overrun); this statement wraps it in ``FUNCTION TRIM``. One of the
    three, and the one where it makes no difference - which is presumably why it is the one
    that got it.

    ⭐ THE VALUE RENDERING IS IDENTICAL TO ``bb200-Insert``'s, character for character,
    including the asymmetric ``FUNCTION TRIM`` on the integer slice of a scaled number and
    its absence on the fraction slice. Both statements therefore share
    :func:`_insert_parameters`.
    """
    # `WHERE FUNCTION TRIM (WS-Where (1:J))` [:L2173-L2175] - trimmed, unlike the others.
    statement = _update_statement(context.ws_where.strip())
    parameters = _insert_parameters(context.group) + (key_value,)
    return _mysql_1210_command(context, statement, parameters)   # [:L2177]


def otm3mt_ca_process_logs(context: _BridgeContext) -> None:
    """``Ca-Process-Logs.`` in ``otm3MT`` - [common/otm3MT.cbl:L2184-L2188].

    ⭐ THE NAME IS QUALIFIED BY PROGRAM, AND ONLY BECAUSE IT HAS TO BE. ``acas019`` and
    ``otm3MT`` BOTH declare a paragraph called ``Ca-Process-Logs`` and both declare one
    called ``ca-Exit`` [common/acas019.cbl:L623, :L629] and [common/otm3MT.cbl:L2184,
    :L2190]. Two programs sharing one Python module cannot share one function name, so
    these two pairs - and only these two pairs - carry a program prefix:
    ``otm3mt_ca_process_logs`` / ``otm3mt_ca_exit`` against
    ``acas019_ca_process_logs`` / ``acas019_ca_exit``. Every other paragraph in both
    programs keeps its own name unaltered, because every other name is unique across the
    pair. Recorded in ``docs/migration/traceability.md`` as a naming disambiguation, not a
    rename.

    ::

        call     "fhlogger" using File-Access                     [:L2186]
                                 ACAS-DAL-Common-data.            [:L2187]

    ``fhlogger`` [common/fhlogger.cbl] is out of scope [AAP section 0.2.2, "Non-posting
    utilities"], so the record it would append is emitted through
    :func:`acas_posting.dal.status.log_file_handler_record`, THE ONE ADAPTER every handler
    in this package shares. It has no database effect - AAP section 0.3.4's first rule - so
    it becomes a log record and alters no control flow.

    TWO FIELDS ARE WITHHELD. ``WS-File-Key`` is the customer-and-invoice key and
    ``WS-Log-Where`` is a SQL predicate carrying that key as a literal; both are CWE-532 in
    a log and neither is needed to act on a failure.

    ⭐ THE HANDLER HAS A PARAGRAPH OF THE SAME NAME [common/acas019.cbl:L623] which is NOT
    called on this path, per the comment on its own label line. So one CALL produces one
    log record, from here. Anomaly N-nolog-on-dal.
    """
    logging_data = context.file_access.logging_data
    #  `Log-File-Rec-Written` IS NOW ADVANCED, NOT PINNED. Assigning 1 was wrong
    #  twice over: the field is `pic 9(6)` [copybooks/Test-Data-Flags.cob:L20], so it
    #  counts to 999999 and wraps, and it lives in `ACAS-DAL-Common-data`, which the
    #  CALLER owns and carries across calls - so pinning it to 1 discarded every count
    #  the rest of the cycle had accumulated. The adapter advances it by one, modulo one
    #  million, once per record it emits.
    log_file_handler_record(
        _LOG,
        program=BRIDGE_PROGRAM_ID,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=int(context.file_access.file_function),
        access_type=int(context.file_access.access_type),
        fs_reply=int(context.file_access.fs_reply),
        we_error=int(context.file_access.we_error),
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=context.dal_common,
    )
    otm3mt_ca_exit(context)


def otm3mt_ca_exit(context: _BridgeContext) -> None:
    """``ca-Exit.     exit.`` in ``otm3MT`` - [common/otm3MT.cbl:L2190].

    A bare ``exit``, which in COBOL is a no-operation that gives the paragraph a name to
    end at. Reproduced as a named function so the paragraph inventory is complete: the
    bridge's last paragraph exists and does nothing, and that is a fact about the bridge.

    Note the casing: the label is ``ca-Exit`` while the paragraph above it is
    ``Ca-Process-Logs``, and the handler spells its pair the same way
    [common/acas019.cbl:L623, :L629]. Anomaly N-casing.
    """


def otm3_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    otm3: OiHeader,
) -> tuple[int, int]:
    """``call "otm3MT" using File-Access, ACAS-DAL-Common-data, WS-OTM3-Record``.

    THE BRIDGE ENTRY POINT, with the bridge's own three parameters in the bridge's own
    order [common/acas019.cbl:L611-L615], VERBATIM::

        call     "otm3MT" using  File-Access
                                     ACAS-DAL-Common-data
                                     WS-OTM3-Record
        end-call.

    Note the order: ``File-Access`` FIRST here, where the handler's own linkage puts
    ``System-Record`` first and ``File-Access`` third [common/acas019.cbl:L225-L231]. The
    two signatures are published separately, in their own orders, so a reader following
    either call site finds the shape it wrote - rule R-5.

    This function owns ALL SQL for ``SAITM3-REC``: every SELECT, INSERT, UPDATE and DELETE
    against the table is issued from a paragraph below it, and nothing else in the codebase
    issues any. No DDL is emitted, ever - the schema is frozen (rule R-3).

    IT NEVER RAISES. [common/acas019.cbl:L617] states the contract in the maintainer's own
    words - ``*> Any errors leave it to caller to recover from`` - so every failure,
    including a driver exception and a policy refusal, is converted to an ``FS-Reply`` and
    ``We-Error`` pair written into ``file_access``. The pair is also returned, for callers
    that prefer it.

    Args:
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L64], carrying the
            requested ``File-Function`` and ``Access-Type`` in, and the status, the
            diagnostics and the logging fields out.
        dal_common: ``ACAS-DAL-Common-data``
            [copybooks/Test-Data-Flags.cob:L10-L16], whose two switches gate the logging
            (``Testing-1``) and the diagnostic display (``Testing-2``, deviation D2).
        otm3: ``WS-OTM3-Record`` as the bridge declares it - the FULL field layout, because
            [common/otm3MT.cbl:L345-L346] renames ``OI-Header`` to that name. MUTATED IN
            PLACE by a successful read, exactly as the COBOL mutates the caller's item.

    Returns:
        The ``(FS-Reply, We-Error)`` pair, which is also in ``file_access``.
    """
    context = _BridgeContext(
        file_access=file_access, dal_common=dal_common, record=otm3
    )
    ba_acas_dal_process(context)          # the section head [:L370-L382] - deviation D2
    return ba010_initialise(context)      # clear, then dispatch [:L384-L429]


# ===========================================================================
# THE HANDLER - acas019
#
# `aa-Process-Flat-File Section.` [common/acas019.cbl:L234] through
# `ca-Exit. exit.` [:L629]. One function per paragraph, in source order.
#
# Per docstring C2 the migrated cycle takes the RDB branch at [:L262-L266] and NEVER
# reaches the `aa` section: `dispatch` guards the key, then leaves for
# `ba-Process-RDBMS`, which calls the bridge. The whole `aa` section is nonetheless
# reproduced, because rule R-5 requires a function per paragraph and rule R-4 forbids
# deleting behaviour that is merely unreached.
# ===========================================================================


@dataclass
class _HandlerContext:
    """``acas019``'s five linkage items plus the per-CALL scratch its paragraphs share.

    The five are exactly the handler's own, in its own order
    [common/acas019.cbl:L225-L231]: ``System-Record``, ``WS-OTM3-Record``,
    ``File-Access``, ``File-Defs``, ``ACAS-DAL-Common-data``.

    ``file_record`` is the FILE view - ``01 Open-Item-Record-3`` from
    [copybooks/slfdoi3.cob], a STANDALONE ``01`` and not a redefines (docstring C3). It is
    the handler's own working item, not linkage, and it persists across CALLs exactly as
    the file's record area does.
    """

    system: SystemRecord
    record: OiHeader
    file_access: FileAccess
    file_defs: FileDefs
    dal_common: AcasDalCommonData
    medium: FlatFileMedium = _FLAT_FILE_MEDIUM_ABSENT
    file_record: OpenItemRecord3 = field(default_factory=_blank_open_item_record_3)
    ws_temp_ed: WsTempEd = field(default_factory=WsTempEd)
    cobol_file_status: int = 0
    cobol_file_eof: bool = False
    fs_reply: int = FsReply.SUCCESS
    we_error: int = 0

    def status(self, fs_reply: FsReply | int, we_error: WeError | int) -> None:
        """Write a status pair into ``File-Access`` and remember it for the return."""
        self.fs_reply, self.we_error = _write_status(
            self.file_access, fs_reply, we_error
        )

    def read_status(self) -> None:
        """Re-read the pair from ``File-Access`` after something else wrote it."""
        self.fs_reply = _as_fs_reply(self.file_access.fs_reply)
        self.we_error = int(self.file_access.we_error)


def aa_process_flat_file(context: _HandlerContext) -> tuple[int, int]:
    """``aa-Process-Flat-File Section.`` - [common/acas019.cbl:L234]. A bare section head.

    The section header carries no statements of its own; ``aa010-main`` at [:L236] is its
    first paragraph and runs immediately. The function exists so the inventory is complete
    and so the entry point into the section has a name, exactly as the COBOL does.
    """
    return aa010_main(context)


def aa010_main(context: _HandlerContext) -> tuple[int, int]:
    """``aa010-main.`` - [common/acas019.cbl:L236-L305]. Log identity, guard, branch, dispatch.

    Four things happen, in this order, and the ORDER IS THE WHOLE POINT of docstring C2.

    ONE - the log identity [:L240-L241], VERBATIM::

        move     3      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Invoice used in FH logging
        move     15     to WS-Log-File-No.  *> RDB, File/Table

    ⭐ ANOMALY N-logsystem5-meaning: the legend on [:L240] says ``5=Invoice``, matching
    ``acas016:L248``, while ``acas013:L298`` and ``acas015:L291`` both say ``5=Stock`` for
    the same code. Four handlers, two legends, one vocabulary.

    ⭐ ANOMALY N-log: file number 15 is set here and OVERWRITTEN with 25 by
    ``ba010-Test-WS-Rec-Size`` [:L557] - and the second statement spells the field
    ``WS-Log-File-no`` where the first spells it ``WS-Log-File-No``. The pair 15->25 is
    ALSO ``acas008``'s [common/acas008.cbl:L294, :L523], which uses it with
    ``WS-Log-System = 1``, so only the ``(system, file)`` pair identifies the handler.

    TWO - the key guard [:L245-L259]. Reproduced by :func:`_aa010_key_guard`.

    THREE - the RDB branch [:L262-L266], VERBATIM::

        if       not FS-Cobol-Files-Used
                 move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses    *> needed for DAL? not JC/dbpre versions
                 perform ba-Process-RDBMS                                *>  Can't hurt
                 go to AA-Main-Exit
        end-if.

    ⭐⭐ THIS IS WHERE EVERY MIGRATED RUN LEAVES. The dispatch below is FLAT-FILE ONLY. The
    two maintainer comments are preserved verbatim above because they are the only record of
    why the move and the perform are there - and the second one, ``*> Can't hurt``, is the
    entire justification for the DAL path existing at this point in the paragraph.

    FOUR - ``ba012``, the non-initialisation, and the dispatch [:L271-L305]::

        perform  ba012-Test-WS-Rec-Size-2.                        [:L271]
    *>  ?   move     zero   to  WE-Error                          [:L279]  <- commented out
    *>  ?                       FS-Reply.                         [:L280]  <- commented out
        move     spaces to SQL-Err SQL-Msg SQL-State.             [:L281]
        evaluate File-Function  ... nine arms ...                 [:L283-L302]
    *>  Should never get here but in case :(                      [:L304]
        go       to aa100-Bad-Function.                           [:L305]

    ⭐ ANOMALY N-initialize / the deliberate non-initialisation: [:L279-L280] are commented
    out, WITH A QUESTION MARK, so ``WE-Error`` and ``FS-Reply`` arrive from the caller and
    stand. The bridge has the identical pair commented out at [common/otm3MT.cbl:L386-L387].
    NOT zeroed here.

    ⭐ ANOMALY N-noopenoutput: there is NO ``if fn-Open and fn-output`` block anywhere in
    this handler - the fourth of four behaviours across six handlers, and the only one that
    is absent entirely. An Open+Output DELETES NOTHING. Reproduced by the absence.

    ⭐ ``aa100-Bad-Function`` IS REACHED TWO WAYS: from ``when other`` [:L300-L301] and from
    the unconditional fall-through at [:L305], whose own comment admits it should be
    unreachable. Both paths are reproduced - AAP section 0.4.2 Class 4 for the ``when
    other`` arm and Class 2 for the fall-through, which terminates the ``evaluate``.
    """
    logging_data = context.file_access.logging_data
    logging_data.ws_log_system = WS_LOG_SYSTEM                    # [:L240]
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT_FILE        # [:L241] - 15

    # TWO - the key guard [:L245-L259], which governs BOTH paths because it is above the
    # branch. A rejection returns immediately.
    guarded = _aa010_key_guard(context)
    if guarded is not None:
        return guarded

    # THREE - the RDB branch [:L262-L266]. `FS-Cobol-Files-Used` is a condition name on
    # `RDBMS-Flat-Statuses.File-System-Used` [copybooks/wsfnctn.cob], and the migrated
    # cycle always takes this branch (docstring C2).
    if not _fs_cobol_files_used(context.system):
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses` [:L263], with the
        # maintainer's `*> needed for DAL? not JC/dbpre versions`.
        source = context.system.system_data_block.rdbms_flat_statuses
        target = context.file_access.fa_rdbms_flat_statuses
        target.fa_file_system_used = source.file_system_used
        target.fa_file_duplicates_in_use = source.file_duplicates_in_use
        # `perform ba-Process-RDBMS` [:L264], with `*>  Can't hurt`.
        ba_process_rdbms(context)
        # `go to AA-Main-Exit` [:L265] - Class 3.
        return aa_main_exit(context)

    # FOUR - flat-file path only from here.
    #
    # `perform  ba012-Test-WS-Rec-Size-2.` [:L271] names a PARAGRAPH, so the range is that
    # paragraph ALONE: control returns here without reaching `ba015-Test-Ends` and the
    # bridge is never called on this path. Contrast `perform ba-Process-RDBMS` [:L265],
    # which names a SECTION and therefore falls through all four paragraphs - see
    # `ba_process_rdbms`. The boolean the paragraph returns reports its `go to
    # ba-rdbms-exit` [:L586], which only the SECTION range can act on; here it is
    # deliberately ignored, and the status pair it left in `File-Access` is what the caller
    # sees. `WS-Log-File-No` also stays at the 15 set above, because `ba010` was skipped.
    ba012_test_ws_rec_size_2(context)                             # [:L271]
    # [:L279-L280] are COMMENTED OUT. `WE-Error` and `FS-Reply` are NOT zeroed.
    context.read_status()
    # `move spaces to SQL-Err SQL-Msg SQL-State.` [:L281] - spaces into all three, unlike
    # the bridge's `ba010`, which puts ZERO into `SQL-State` [common/otm3MT.cbl:L385].
    _write_sql_fields(context.file_access, sql_err="", sql_msg="", sql_state="")

    # `evaluate File-Function` [:L283-L302]. Nine arms, each a `go to` - Class 4.
    function = int(context.file_access.file_function)
    if function == int(FileFunction.OPEN):                    # when 1  [:L284-L285]
        return aa020_process_open(context)
    if function == int(FileFunction.CLOSE):                   # when 2  [:L286-L287]
        return aa030_process_close(context)
    if function == int(FileFunction.READ_NEXT):               # when 3  [:L288-L289]
        return aa040_process_read_next(context)
    if function == int(FileFunction.READ_INDEXED):            # when 4  [:L290-L291]
        return aa050_process_read_indexed(context)
    if function == int(FileFunction.WRITE):                   # when 5  [:L292-L293]
        return aa070_process_write(context)
    if function == int(FileFunction.RE_WRITE):                # when 7  [:L294-L295]
        return aa090_process_rewrite(context)
    if function == int(FileFunction.DELETE):                  # when 8  [:L296-L297]
        return aa080_process_delete(context)
    if function == int(FileFunction.START):                   # when 9  [:L298-L299]
        return aa060_process_start(context)
    # `when other  go to aa100-Bad-Function` [:L300-L301] - `*> 6 is spare / unused`. Codes
    # 32 and 33 land here too: the HANDLER does not dispatch them, the bridge does
    # (docstring C1).
    # The unconditional `go to aa100-Bad-Function` at [:L305], whose comment reads
    # `*> Should never get here but in case :(`, is the same destination, so both paths
    # converge on one call.
    return aa100_bad_function(context)


def _aa010_key_guard(context: _HandlerContext) -> tuple[int, int] | None:
    """``evaluate File-Function`` at [common/acas019.cbl:L245-L259] - the key guard, VERBATIM::

        evaluate File-Function
                 when  4   *> fn-read-indexed
                 when  9   *> fn-start
                   if     File-Key-No not = 1
                          move 998 to WE-Error       *> file seeks key type out of range        998
                          move 99 to fs-reply
                          go   to aa999-main-exit
                   end-if
                 when     8  *> fn-delete
                   if     File-Key-No not = 1
                          move 996 to WE-Error       *> file seeks key type out of range        996
                          move 99 to fs-reply
                          go   to aa999-main-exit
                   end-if
        end-evaluate.

    ⭐ TWO ARMS, TWO ERROR CODES, ONE CONDITION. Read-indexed and start share an arm and
    report 998; delete has its own arm and reports 996. The test is identical in both.

    ⭐ ANOMALY N-996-comment: the comment beside the 996 is a VERBATIM COPY of the one
    beside the 998, ending in the wrong number's worth of alignment - ``*> file seeks key
    type out of range        996``. A delete does not seek. Reproduced, not rewritten.

    ⭐ THE GUARD IS ABOVE THE RDB BRANCH, so it governs BOTH paths - it is the only part of
    the ``aa`` section a migrated run executes. The bridge has no equivalent: its own
    comment says ``*>   Now Test for valid key for start, read-indexed and delete  ...
    *>      REMOVED as not used here`` [common/otm3MT.cbl:L395-L396].

    ⭐ EXACTLY ONE KEY EXISTS - ``OI3-KEY``, the sole entry in the bridge's metadata table
    [common/otm3MT.scb:L249-L251] - which is why ``not = 1`` is the whole of the test. There
    is no key 2 to admit, unlike ``acas000``, whose guard admits four.

    ⛔ NOT harmonised with ``acas000``'s different function set (4, 5, 7): this handler
    guards 4, 9 and 8, and no others. A WRITE with a bad key number passes straight through.

    Returns:
        The status pair if the guard rejected, or ``None`` to continue.
    """
    function = int(context.file_access.file_function)
    key_number = int(context.file_access.logging_data.file_key_no)

    if function in (int(FileFunction.READ_INDEXED), int(FileFunction.START)):
        # `when 4` / `when 9` share one arm [:L246-L252].
        if key_number != 1:
            context.status(
                FsReply.ERROR, int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
            )                                                    # 998 [:L249-L250]
            # ONE ERROR, through the shared reporter: the guard returns 99 to the
            # caller, so it is a failure and WARNING was below the level an operator
            # watches. `File-Key-No` and `File-Function` are operation codes from the
            # frozen vocabulary [copybooks/wsfnctn.cob:L88-L118], not business data.
            log_handler_failure(
                _LOG,
                program=HANDLER_PROGRAM_ID,
                paragraph="aa000-Main-Process key guard",
                locator="[common/acas019.cbl:L248-L251]",
                fs_reply=int(FsReply.ERROR),
                we_error=int(WeError.FILE_KEY_NO_OUT_OF_RANGE),
                detail="File-Key-No %d rejected for File-Function %d; SAITM3-REC "
                "declares exactly one key [common/otm3MT.scb:L249-L251]"
                % (key_number, function),
            )
            return aa999_main_exit(context)                      # [:L251] - Class 3
    elif function == int(FileFunction.DELETE):
        # `when 8` has its own arm and its own code [:L253-L258].
        if key_number != 1:
            context.status(
                FsReply.ERROR, int(WeError.DELETE_KEY_OUT_OF_RANGE)
            )                                                    # 996 [:L255-L256]
            # ONE ERROR, as above - the delete arm has its own code, 996.
            log_handler_failure(
                _LOG,
                program=HANDLER_PROGRAM_ID,
                paragraph="aa000-Main-Process key guard",
                locator="[common/acas019.cbl:L254-L257]",
                fs_reply=int(FsReply.ERROR),
                we_error=int(WeError.DELETE_KEY_OUT_OF_RANGE),
                detail="File-Key-No %d rejected for delete; the comment beside the "
                "frozen code is a verbatim copy of the 998 comment at [:L249] - "
                "anomaly N-996-comment" % key_number,
            )
            return aa999_main_exit(context)                      # [:L257] - Class 3
    return None


def _fs_cobol_files_used(system: SystemRecord) -> bool:
    """``FS-Cobol-Files-Used`` - the condition name the RDB branch tests at [:L262].

    Declared on ``File-System-Used`` inside ``RDBMS-Flat-Statuses``, VERBATIM
    [copybooks/wssystem.cob:L112-L116]::

        07  File-System-Used  pic 9.
            88  FS-Cobol-Files-Used    value zero.
            88  FS-MySql-Used          value 1.
                                     *> THESE NOT IN USE at this time
            88  FS-RDBMS-Used          value 1.  *> Was generic

    So ZERO - not one - is the flat-file state, and ``FS-MySql-Used`` and ``FS-RDBMS-Used``
    BOTH carry value 1: two condition names over one state, recorded in
    ``acas_posting/records/system_record.py`` as an oddity left as it stands. The same pair
    is redeclared on the ``File-Access`` copy of the group [copybooks/wsfnctn.cob:L73-L75],
    which is what [:L263] populates.

    The predicate lives here rather than in ``acas_posting.cobol.condition_names`` because
    AAP section 0.4.3's import table does not permit ``dal/*`` to import ``cobol/*``.

    Every in-scope scenario sets the RDBMS value 1, so this returns False and the RDB
    branch is taken - docstring C2.
    """
    return int(system.system_data_block.rdbms_flat_statuses.file_system_used) == 0


def aa020_process_open(context: _HandlerContext) -> tuple[int, int]:
    """``aa020-Process-Open.`` - [common/acas019.cbl:L307-L344]. Four modes, four shapes.

    ::

        move     spaces to WS-File-Key.     *> for logging          [:L308]
        move     201 to WS-No-Paragraph.                            [:L309]
        if       fn-input                                           [:L310]
                 open input Open-Item-File-3                        [:L311]
                 if   Fs-Reply not = zero                           [:L312]
                      move 35 to fs-Reply                           [:L313]
                      close Open-Item-File-3                        [:L314]
                      go to aa999-Main-Exit                         [:L315]
                 end-if
         else
          if     fn-i-o                                             [:L318]
                 open i-o Open-Item-File-3                          [:L319]
                 if       fs-reply not = zero                       [:L320]
                          close       Open-Item-File-3              [:L321]
                          open output Open-Item-File-3   *> Doesnt create in i-o   [:L322]
                          close       Open-Item-File-3              [:L323]
                          open i-o    Open-Item-File-3              [:L324]
                 end-if                  *> file-status will NOT be updated   ????   [:L325]
          else
           if    fn-output                      *> should not need to be used   [:L327]
                 open output Open-Item-File-3   *> caller should check fs-reply  [:L328]
           else
            if   fn-extend                      *> Must not be used for ISAM files [:L330]
    *>              open extend Open-Item-File-3                    [:L331]
                 move 997 to WE-Error                               [:L332]
                 move 99  to FS-Reply                               [:L333]
                 go to aa999-main-exit                              [:L334]
            end-if
        end-if.
    *> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.      [:L339]
        move     zero to Cobol-File-Status.                         [:L340]
        move     "OPEN SL OTM3 File" to WS-File-Key.                [:L341]
        if       fs-reply not = zero                                [:L342]
                 move  999 to WE-Error.                             [:L343]
        go       to aa999-main-exit.            *> with test for dup processing  [:L344]

    ⭐ THE I-O RETRY CREATES THE FILE AND THEN LOSES THE ANSWER. ``open i-o`` on a
    non-existent ISAM file fails, so the paragraph closes, opens OUTPUT to create it,
    closes, and opens i-o again [:L321-L324] - and the maintainer's own comment on the
    ``end-if`` says ``*> file-status will NOT be updated   ????``, meaning the final open's
    status is not what the ``if`` at [:L342] then tests. Reproduced, retry and doubt alike.

    ⭐ THE INPUT FAILURE PATH REPORTS 35 - "file not found" - AND CLOSES A FILE IT FAILED TO
    OPEN [:L313-L314]. In that order: the status is overwritten first, so the close's own
    status cannot be seen. Reproduced in that order.

    ⭐ ``fn-extend`` IS REJECTED WITH THE ``open extend`` COMMENTED OUT ABOVE IT [:L331], so
    the rejection is the whole of the arm. 997 is ``ACCESS_TYPE_WRONG`` - the same code the
    BRIDGE uses for an out-of-range start relation [common/otm3MT.cbl:L762], reached here
    for something else entirely.

    ⭐ ``fn-output`` IS A PLAIN OPEN, with ``*> should not need to be used`` and
    ``*> caller should check fs-reply`` [:L327-L328]. This is anomaly N-noopenoutput at the
    flat-file end: no delete-all, no coercion, nothing.

    ⭐ ANOMALY N-initialize, THIRD AND FOURTH SITES: [:L339] here and [:L350] in
    ``aa030`` are BOTH commented-out ``move zeros to FS-Reply WE-Error``, both dated
    ``27/07/16 16:30``, both left in place. Two more deliberate non-initialisations,
    additional to the pair at [:L279-L280].

    ⭐ THE 999 AT [:L343] IS A PERIOD-TERMINATED ``if`` WITH NO ``end-if``, so the ``go to``
    at [:L344] is NOT inside it - the transfer happens either way. Reproduced.

    Transfers: ``go to aa999-Main-Exit`` three times, all Class 3.
    """
    _write_file_key(context.file_access, "")                      # [:L308]
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa020-Process-Open"
    ]                                                             # [:L309]

    access_type = int(context.file_access.access_type)
    if access_type == int(AccessType.INPUT):                      # `fn-input` [:L310]
        reply = context.medium.open_file("input")                 # [:L311]
        context.status(reply, context.we_error)
        if int(reply) != 0:                                       # [:L312]
            # `move 35 to fs-Reply` BEFORE the close, so the close's status is invisible.
            context.status(35, context.we_error)                   # [:L313]
            context.medium.close_file()                            # [:L314]
            return aa999_main_exit(context)                       # [:L315] - Class 3
    elif access_type == int(AccessType.I_O):                       # `fn-i-o` [:L318]
        reply = context.medium.open_file("i-o")                    # [:L319]
        context.status(reply, context.we_error)
        if int(reply) != 0:                                        # [:L320]
            # The create-then-reopen retry [:L321-L324]. The maintainer's comment on the
            # `end-if` warns that the final status is NOT what [:L342] later tests.
            context.medium.close_file()                            # [:L321]
            context.medium.open_file("output")                     # [:L322]
            context.medium.close_file()                            # [:L323]
            context.medium.open_file("i-o")                        # [:L324]
    elif access_type == int(AccessType.OUTPUT):                    # `fn-output` [:L327]
        # A PLAIN OPEN. Anomaly N-noopenoutput: nothing is deleted, unlike `acas008`
        # [common/acas008.cbl:L313-L319].
        reply = context.medium.open_file("output")                 # [:L328]
        context.status(reply, context.we_error)
    elif access_type == int(AccessType.EXTEND):                    # `fn-extend` [:L330]
        # `open extend` is commented out at [:L331]; the rejection is the arm.
        context.status(FsReply.ERROR, int(WeError.ACCESS_TYPE_WRONG))  # [:L332-L333]
        # ONE ERROR, through the shared reporter. A published verb that can never
        # succeed is exactly what an operator must be able to find - the same reasoning
        # that took anomaly A6's refusal in `acas008` off DEBUG.
        log_handler_failure(
            _LOG,
            program=HANDLER_PROGRAM_ID,
            paragraph="aa020-Process-Open",
            locator="[common/acas019.cbl:L330-L334]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            detail="fn-extend refused: 'Must not be used for ISAM files'; the "
            "`open extend` itself is commented out in the frozen source",
        )
        return aa999_main_exit(context)                            # [:L334] - Class 3

    # [:L339] is COMMENTED OUT, dated 27/07/16 16:30 - anomaly N-initialize.
    context.cobol_file_status = 0                                  # [:L340]
    _write_file_key(context.file_access, "OPEN SL OTM3 File")      # [:L341]
    if int(context.fs_reply) != 0:                                 # [:L342]
        context.status(context.fs_reply, int(WeError.NOT_USED))     # 999 [:L343]
    return aa999_main_exit(context)                                # [:L344] - Class 3


def aa030_process_close(context: _HandlerContext) -> tuple[int, int]:
    """``aa030-Process-Close.`` - [common/acas019.cbl:L346-L357]. Close, log, and leave low.

    ::

        move     202 to WS-No-Paragraph.                            [:L347]
        move     spaces to WS-File-Key.     *> for logging          [:L348]
        close    Open-Item-File-3.                                  [:L349]
    *> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.      [:L350]
        move     zero to Cobol-File-Status.                         [:L351]
        move     "CLOSE SL OTM3 File" to WS-File-Key                [:L352]
        perform  aa999-main-exit.                                   [:L353]
        move     zero to  File-Function                             [:L354]
                          Access-Type.              *> close log file  [:L355]
        perform  Ca-Process-Logs.                                   [:L356]
        go       to aa-main-exit.                                   [:L357]

    ⭐⭐ THIS IS THE ONLY PARAGRAPH THAT LOGS TWICE, AND DELIBERATELY. ``perform
    aa999-main-exit`` at [:L353] logs the close itself; then ``File-Function`` and
    ``Access-Type`` are ZEROED and ``Ca-Process-Logs`` is performed AGAIN at [:L356], whose
    comment ``*> close log file`` says what the second record is for - a zero function is
    the logger's own end-of-file marker. So closing the data file writes two log records,
    the second with function and access type both zero. Reproduced exactly.

    ⭐ IT ZEROES TWO LINKAGE FIELDS THE CALLER OWNS. ``File-Function`` and ``Access-Type``
    are in ``File-Access`` [copybooks/wsfnctn.cob], so after a close the caller's own
    request fields are blank. Any caller that reused them would be surprised; every caller
    sets them before each call, so none is. Reproduced - the mutation is observable.

    ⭐ ``perform aa999-main-exit`` IS A PERFORM, so control returns here rather than
    exiting - AAP section 0.4.2 Class 4, and the reason [:L354-L357] execute at all. The
    ``go to aa-main-exit`` at [:L357] then skips ``aa999-main-exit``'s second logging, which
    is why the close's own record is written once and not three times.

    ⭐ [:L350] IS THE FOURTH COMMENTED-OUT STATUS RESET - anomaly N-initialize.

    Transfers: ``perform aa999-main-exit`` Class 4; ``go to aa-main-exit`` Class 3.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa030-Process-Close"
    ]                                                              # [:L347]
    _write_file_key(context.file_access, "")                       # [:L348]
    reply = context.medium.close_file()                            # [:L349]
    context.status(reply, context.we_error)
    # [:L350] is COMMENTED OUT - anomaly N-initialize, fourth site.
    context.cobol_file_status = 0                                  # [:L351]
    _write_file_key(context.file_access, "CLOSE SL OTM3 File")     # [:L352]
    aa999_main_exit(context)                                       # [:L353] - Class 4
    # `move zero to File-Function Access-Type.` [:L354-L355], `*> close log file`. These
    # are the CALLER's linkage fields.
    context.file_access.file_function = 0
    context.file_access.access_type = 0
    acas019_ca_process_logs(context)                               # [:L356]
    return aa_main_exit(context)                                   # [:L357] - Class 3


def aa040_process_read_next(context: _HandlerContext) -> tuple[int, int]:
    """``aa040-Process-Read-Next.`` - [common/acas019.cbl:L359-L388]. Sequential, with a STOP.

    ::

        move     203 to WS-No-Paragraph.                            [:L364]
        if       Cobol-File-Eof                                     [:L365]
                 move 10 to FS-Reply                                [:L366]
                            WE-Error                                [:L367]
                 move spaces to OI3-Key                             [:L368]
                                SQL-Err                             [:L369]
                                SQL-Msg                             [:L370]
                 stop "Cobol File EOF"               *> for testing  [:L371]
                 go to aa999-main-exit                              [:L372]
        end-if
        read     Open-Item-File-3 next record at end                [:L375]
                 move 10 to we-error fs-reply        *> EOF          [:L376]
                 set Cobol-File-EoF to true                          [:L377]
                 move 1 to Cobol-File-Status         *> JIC above dont work :)  [:L378]
                 initialize Open-Item-Record-3                       [:L379]
                 move "EOF" to WS-File-Key           *> for logging   [:L380]
                 go to aa999-main-exit                               [:L381]
        end-read.
        if       FS-Reply not = zero                                 [:L383]
                 go to aa999-main-exit.                              [:L384]
        move     Open-Item-Record-3 to WS-OTM3-Record.               [:L385]
        perform  aa041-Move-Inv-Data.                                [:L386]
        move     zeros to WE-Error.                                  [:L387]
        go to    aa999-main-exit.                                    [:L388]

    ⭐⭐ ANOMALY N-stop: ``stop "Cobol File EOF"`` at [:L371] HALTS THE PROGRAM AND WAITS FOR
    THE OPERATOR, on the second read past end of file. Its own comment says
    ``*> for testing`` and it was never removed. It is UNREACHABLE in the migrated cycle -
    the RDB branch leaves before the dispatch (C2) - and it is recorded BOTH as an anomaly
    and as a deliberate omission: ⛔ no pause, no ``input()``, no sleep is introduced, per
    AAP section 0.3.4's third rule, which drops an acknowledgement pause and keeps only the
    control transfer that follows it. The transfer at [:L372] IS kept.

    ⭐⭐ ANOMALY N-spaces-into-numeric: ``move spaces to OI3-Key`` at [:L368] moves SPACES
    into a group whose second half is ``PIC 9(8)`` [copybooks/slwsoi3.cob:L13-L14]. Not
    zeros - spaces. Reproduced literally, and :func:`_numeric_digits` is what tolerates the
    result when those bytes are next read as a number.

    ⭐ BOTH EOF PATHS SET ``FS-Reply`` AND ``WE-Error`` TO 10, and the second one adds
    ``move 1 to Cobol-File-Status`` with the comment ``*> JIC above dont work :)`` [:L378] -
    a belt-and-braces flag beside the ``set ... to true`` on the line above. Both are kept.

    ⭐ ``initialize Open-Item-Record-3`` AT [:L379] IS THE PLAIN FORM, not ``with filler``,
    and it is over the FILE view whose ``filler pic x(99)`` therefore SURVIVES. This is the
    one site where the ``FILLER`` phrase changes the outcome - anomaly N-initialize - and it
    is why 99 of the 118 bytes keep the previous record's contents at end of file.

    ⭐ ``perform aa041-Move-Inv-Data`` at [:L386] is AAP section 0.4.2 Class 4 - a sibling
    re-dispatch: the paragraph builds the logging key and returns.

    Transfers: ``go to aa999-main-exit`` four times, all Class 3; the ``perform`` Class 4.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa040-Process-Read-Next"
    ]                                                              # [:L364]

    if context.cobol_file_eof:                                     # [:L365]
        context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))  # [:L366-L367]
        # `move spaces to OI3-Key` [:L368] - anomaly N-spaces-into-numeric. The FILE view's
        # key group takes spaces, `PIC 9(8)` half included.
        context.file_record.oi3_key.oi3_customer = " " * 7
        context.file_record.oi3_key.oi3_invoice = _numeric_digits(
            " " * 8, "OI3-Invoice"
        )
        _write_sql_fields(context.file_access, sql_err="", sql_msg="")  # [:L369-L370]
        # `stop "Cobol File EOF"` [:L371] - anomaly N-stop, recorded as an omission. The
        # operator pause is NOT reproduced; the diagnostic becomes a log record and the
        # transfer below is preserved.
        #  ONE ERROR, THROUGH THE ONE REPORTER, worded and levelled identically
        #  to every sibling handler's record for the same statement. ERROR was already
        #  the right level here - a production `stop` that hangs an unattended batch run
        #  is exactly what an operator must see - but acas006 and acas007 logged it at
        #  WARNING, acas012 at INFO and acas016 at DEBUG, so one event read as four.
        log_cobol_stop(
            _LOG,
            program=HANDLER_PROGRAM_ID,
            paragraph="aa040-Process-Read-Next",
            literal="Cobol File EOF",
            locator="[common/acas019.cbl:L371]",
        )
        return aa999_main_exit(context)                            # [:L372] - Class 3

    reply, read_record = context.medium.read_next()                # [:L375]
    if read_record is None:                                        # `at end` [:L375]
        context.status(FsReply.END_OF_FILE, int(FsReply.END_OF_FILE))  # [:L376]
        context.cobol_file_eof = True                              # [:L377]
        context.cobol_file_status = 1                              # [:L378] - `*> JIC`
        # `initialize Open-Item-Record-3` [:L379] - PLAIN, so `filler pic x(99)` survives.
        _initialize_open_item_record_3(context.file_record, with_filler=False)
        _write_file_key(context.file_access, _FILE_KEY_FLAT_EOF)    # [:L380]
        return aa999_main_exit(context)                            # [:L381] - Class 3

    context.status(reply, context.we_error)
    if int(context.fs_reply) != 0:                                 # [:L383]
        return aa999_main_exit(context)                            # [:L384] - Class 3

    # `move Open-Item-Record-3 to WS-OTM3-Record.` [:L385] - deviation D4.
    _copy_open_item_record_3(read_record, context.file_record)
    _move_file_record_to_linkage(context.file_record, context.record)
    aa041_move_inv_data(context)                                   # [:L386] - Class 4
    context.status(context.fs_reply, int(WeError.SUCCESS))         # [:L387]
    return aa999_main_exit(context)                                # [:L388] - Class 3


def aa041_move_inv_data(context: _HandlerContext) -> None:
    """``aa041-Move-Inv-Data.`` - [common/acas019.cbl:L390-L393]. The logging key, VERBATIM::

        move     OI3-Invoice  to WS-Temp-ED-2.                      [:L391]
        move     OI3-Customer to WS-Temp-ED-1.                      [:L392]
        move     WS-Temp-ED   to WS-File-Key.                       [:L393]

    Over ``01 WS-Temp-ED`` [:L202-L204], VERBATIM::

        01  WS-Temp-ED.
            03  ws-temp-ed-1       pic x(7).    *> Cust #
            03  WS-Temp-ed-2       pic 9(8).    *> Inv  #

    ⭐⭐ ANOMALY N-aa041-move-inv-data: THIS PARAGRAPH NAME EXISTS IN NO OTHER HANDLER. It
    occupies the slot where ``acas005``, ``acas006``, ``acas007`` and ``acas012`` all have
    ``aa041-Reread``, and where the BRIDGE has ``ba041-Reread``
    [common/otm3MT.cbl:L563] - and it does something unrelated to any of them: it assembles
    a logging key rather than re-reading anything. ⛔ NOT renamed to ``aa041-Reread``.

    ⭐ THE MOVES FILL THE GROUP IN REVERSE DECLARATION ORDER. ``WS-Temp-ED-2`` (the invoice,
    the SECOND field) is filled first at [:L391], then ``WS-Temp-ED-1`` (the customer, the
    FIRST field) at [:L392]. The assembled result is customer-then-invoice regardless,
    because the layout decides that - but the STATEMENT order is invoice-first and is
    reproduced as such. The identical inversion appears in the BRIDGE's load
    [common/otm3MT.cbl:L1341-L1345].

    ⭐ ANOMALY N-casing: THREE CASINGS OF ONE NAME in four lines - ``WS-Temp-ED`` (the
    group, [:L202]), ``ws-temp-ed-1`` (all lower, [:L203]), ``WS-Temp-ed-2`` (mixed,
    [:L204]) - and the references at [:L391-L392] use ``WS-Temp-ED-2`` and ``WS-Temp-ED-1``,
    matching neither declaration exactly. COBOL is case-insensitive, so all of it resolves.
    Recorded; ⛔ not normalised.

    ⭐ THE SOURCE IS THE FILE VIEW, NOT THE LINKAGE VIEW: ``OI3-Invoice`` and
    ``OI3-Customer``, which is why [:L385] copies the file record across FIRST.
    """
    # `move OI3-Invoice to WS-Temp-ED-2.` [:L391] - the SECOND field, filled first.
    context.ws_temp_ed.ws_temp_ed_2 = int(context.file_record.oi3_key.oi3_invoice)
    # `move OI3-Customer to WS-Temp-ED-1.` [:L392] - the FIRST field, filled second.
    context.ws_temp_ed.ws_temp_ed_1 = _cobol_move_alphanumeric(
        str(context.file_record.oi3_key.oi3_customer), 7
    )
    # `move WS-Temp-ED to WS-File-Key.` [:L393] - the assembled 15 characters, customer
    # then invoice, into a 64-character field.
    _write_file_key(context.file_access, context.ws_temp_ed.image)


def aa045_eval_keys(context: _HandlerContext) -> None:
    """``aa045-Eval-Keys.`` - [common/acas019.cbl:L395-L413], VERBATIM::

    *>   The next block will never get executed unless performed  so is it needed ?  [:L395]
     aa045-Eval-Keys.                                               [:L397]
         evaluate File-Function      *> Set up keys just for logging [:L398]
                  when  4             *> fn-read-indexed             [:L399]
                  when  5             *> fn-write                    [:L400]
                  when  7             *> fn-re-write                 [:L401]
                  when  8             *> fn-delete    For delete can ignore Desc key  [:L402]
                  when  9             *> fn-start                    [:L403]
                        evaluate  File-Key-No                        [:L404]
                                  when   1                           [:L405]
                                         move   OI-Key     to OI3-Key   [:L406]
                                         perform aa041-Move-Inv-Data   [:L407]
                                  when   other                       [:L408]
                                         move   spaces     to WS-File-Key  [:L409]
                        end-evaluate                                 [:L410]
                  when  other                                        [:L411]
                        move   spaces    to WS-File-Key              [:L412]
         end-evaluate.                                               [:L413]

    ⭐ ANOMALY N-deadbranches: FOUR OF THE FIVE FUNCTION ARMS ARE UNREACHABLE. The paragraph
    is performed from exactly two places - ``aa050-Process-Read-Indexed`` [:L418] and
    ``aa060-Process-Start`` [:L442] - so only ``when 4`` and ``when 9`` can ever select it.
    ``when 5``, ``when 7`` and ``when 8`` are dead. The whole ``evaluate`` is reproduced,
    dead arms included; ⛔ NOT pruned.

    ⭐ THE MAINTAINER'S OWN COMMENT AT [:L395] DOUBTS THE PARAGRAPH - ``so is it needed ?`` -
    and the same comment appears in ``acas013:L451``, ``acas015:L443`` and ``acas016``. It
    IS needed: the two performs are real. Reproduced with the doubt recorded.

    ⭐⭐ ANOMALY N-oi-key-cross-section-copy: ``move OI-Key to OI3-Key`` at [:L406] is NOT a
    self-copy. Docstring C4 corrects the agent prompt on this: ``OI-Key`` is the LINKAGE
    view's key and ``OI3-Key`` is the FILE view's, and the maintainer says so himself with
    ``*> copy WS to file`` at [:L454]. It is reproduced as an explicit re-materialisation
    through both layouts (deviation D4) - which is what a linkage-to-file copy is - and ⛔
    NOT optimised away.

    ⭐ ``when other`` UNDER ``File-Key-No`` BLANKS ``WS-File-Key`` [:L409] and is
    unreachable behind the guard at [:L245-L259], which already rejected every key number
    but 1 for functions 4, 8 and 9. Only a WRITE or REWRITE with a bad key number could
    reach it - and neither performs this paragraph. Doubly dead, doubly reproduced.
    """
    function = int(context.file_access.file_function)
    if function in (
        int(FileFunction.READ_INDEXED),  # when 4  [:L399] - REACHABLE, from aa050
        int(FileFunction.WRITE),         # when 5  [:L400] - DEAD
        int(FileFunction.RE_WRITE),      # when 7  [:L401] - DEAD
        int(FileFunction.DELETE),        # when 8  [:L402] - DEAD
        int(FileFunction.START),         # when 9  [:L403] - REACHABLE, from aa060
    ):
        if int(context.file_access.logging_data.file_key_no) == 1:     # [:L405]
            # `move OI-Key to OI3-Key` [:L406] - LINKAGE to FILE, not a self-copy (C4).
            _move_linkage_to_file_record(context.record, context.file_record)
            aa041_move_inv_data(context)                               # [:L407] - Class 4
        else:                                                          # [:L408]
            _write_file_key(context.file_access, "")                   # [:L409]
    else:                                                              # [:L411]
        _write_file_key(context.file_access, "")                       # [:L412]


def aa050_process_read_indexed(context: _HandlerContext) -> tuple[int, int]:
    """``aa050-Process-Read-Indexed.`` - [common/acas019.cbl:L415-L435].

    ::

        move     204 to WS-No-Paragraph.                            [:L417]
        perform  aa045-Eval-keys.                                   [:L418]
        move     zero to Cobol-File-Status.                         [:L419]
        if       File-Key-No = 1                                    [:L420]
                 read     Open-Item-File-3 key OI3-Key       invalid key  [:L421]
                          move 21 to we-error fs-reply              [:L422]
                 end-read
                 if       fs-Reply = zero                           [:L424]
                          move     Open-Item-Record-3 to WS-OTM3-Record  [:L425]
                          perform  aa041-Move-Inv-Data              [:L426]
                 else
                          initialize WS-OTM3-Record                 [:L428]
                          move "Failed action" to WS-File-Key       [:L429]
                 end-if
                 go       to aa999-main-exit                        [:L431]
        end-if.
        move     998 to WE-Error       *> file seeks key type out of range but  [:L433]
        move     99 to fs-reply        *>        should never get here       998  [:L434]
        go       to aa999-main-exit.                                [:L435]

    ⭐ THE HANDLER REPORTS 21 FOR A MISSING KEY WHERE THE BRIDGE REPORTS 23. [:L422] moves
    21 into BOTH ``we-error`` and ``fs-reply``; the bridge's ``ba050`` moves 23 into
    ``fs-Reply`` and ZERO into ``WE-Error`` [common/otm3MT.cbl:L682-L683]. So the same
    lookup failure is ``(21, 21)`` on the flat-file path and ``(23, 0)`` on the DAL path -
    a THIRD disagreement between the two programs, after 998/997 and 999/990. Anomaly
    N-read-indexed-23 covers the bridge's half; this is the handler's.

    ⭐ ``move 21 to we-error fs-reply`` PUTS 21 IN ``WE-Error`` TOO. 21 is not a
    ``We-Error`` code at all - the vocabulary's codes are 9xx - so the field carries a file
    status in a slot meant for an internal code. Reproduced as written.

    ⭐ THE FAILURE BRANCH BLANKS THE WHOLE LINKAGE RECORD [:L428] with the PLAIN
    ``initialize``, over the LINKAGE view where the phrase makes no difference (every leaf
    is named - see :func:`_initialize_oi_header`). So a failed indexed read DESTROYS the
    caller's record, which a caller that wanted to retry with the same key would find
    inconvenient. Reproduced.

    ⭐ [:L433-L435] ARE UNREACHABLE. The guard at [:L245-L259] already rejected every key
    number but 1 for function 4, so ``File-Key-No = 1`` at [:L420] cannot be false here -
    and the maintainer's own comment says so: ``*> should never get here``. Reproduced.

    ⭐ ``perform aa045-Eval-keys`` SPELLS THE PARAGRAPH WITH A LOWER-CASE ``k`` at [:L418]
    and [:L442], while the label at [:L397] is ``aa045-Eval-Keys``. Anomaly N-casing.

    Transfers: ``go to aa999-main-exit`` twice, both Class 3; two ``perform`` Class 4.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa050-Process-Read-Indexed"
    ]                                                              # [:L417]
    aa045_eval_keys(context)                                       # [:L418] - Class 4
    context.cobol_file_status = 0                                  # [:L419]

    if int(context.file_access.logging_data.file_key_no) == 1:      # [:L420]
        key_value = _oi3_key_image(context.file_record)
        reply, read_record = context.medium.read_indexed(key_value)  # [:L421]
        # `status fs-Reply` [copybooks/slseloi3.cob:L5] - the read's status lands first.
        context.status(reply, context.we_error)
        if _invalid_key_condition(reply) or read_record is None:
            # `invalid key  move 21 to we-error fs-reply` [:L422] - ONE statement over BOTH
            # fields, and the only place this handler puts a file status into `WE-Error`.
            # The `read_record is None` arm covers a medium that reports the miss without a
            # '2x' status; the frozen runtime always pairs the two.
            context.status(FsReply.INVALID_KEY_ON_START, 21)

        if int(context.fs_reply) == 0:                              # [:L424]
            _copy_open_item_record_3(read_record, context.file_record)  # type: ignore[arg-type]
            _move_file_record_to_linkage(context.file_record, context.record)  # [:L425]
            aa041_move_inv_data(context)                            # [:L426] - Class 4
        else:
            # `initialize WS-OTM3-Record` [:L428] - PLAIN, over the linkage view where the
            # FILLER phrase is immaterial. The caller's record is destroyed.
            _initialize_oi_header_in_place(context.record, with_filler=False)
            _write_file_key(context.file_access, _FILE_KEY_FAILED_ACTION)  # [:L429]
        return aa999_main_exit(context)                             # [:L431] - Class 3

    # UNREACHABLE behind the guard at [:L245-L259] - `*> should never get here` [:L434].
    context.status(FsReply.ERROR, int(WeError.FILE_KEY_NO_OUT_OF_RANGE))  # [:L433-L434]
    return aa999_main_exit(context)                                 # [:L435] - Class 3


def aa060_process_start(context: _HandlerContext) -> tuple[int, int]:
    """``aa060-Process-Start.`` - [common/acas019.cbl:L437-L487]. FOUR separate START blocks.

    ::

        move     205 to WS-No-Paragraph.                            [:L441]
        perform  aa045-Eval-keys.                                   [:L442]
        move     zeros to fs-reply WE-Error.                        [:L443-L444]
        move     zero to Cobol-File-Status.                         [:L445]
        if       access-type < 5 or > 8                   *> NOT using 'not >'  [:L447]
                 move 998 to WE-Error                     *> 998 Invalid calling parameter settings  [:L448]
                 go to aa999-main-exit                              [:L449]
        end-if
        move     OI-Key to OI3-Key.      *> copy WS to file          [:L454]
        if File-Key-No = 1 and fn-equal-to        start ... key =     ... invalid key  21 -> exit  [:L455-L461]
        if File-Key-No = 1 and fn-less-than       start ... key <     ... invalid key  21 -> exit  [:L462-L468]
        if File-Key-No = 1 and fn-greater-than    start ... key >     ... invalid key  21 -> exit  [:L469-L475]
        if File-Key-No = 1 and fn-not-less-than   start ... key not < ... invalid key  21 -> exit  [:L476-L482]
        if       File-Key-No = 1                                    [:L483]
                 perform  aa041-Move-Inv-Data                       [:L484]
        else                                    *> changed for acas019 others ?  [:L485]
                 move     998 to WE-Error       *> file seeks key type out of range but  [:L486]
                 move     99 to fs-reply.        *>        should never get here       998  [:L487]
        go       to aa999-main-exit.                                [:L488]

    ⭐⭐ ANOMALY N-start-997-vs-998, THE HANDLER'S HALF: the guard is
    ``if access-type < 5 or > 8`` - character for character the bridge's test at
    [common/otm3MT.cbl:L760] - and this side moves 998 where the bridge moves 997. The
    inline comment here, ``*> NOT using 'not >'``, records that the maintainer chose the
    explicit form deliberately.

    ⭐⭐ ANOMALY N-start-fs-reply-stays-zero: THE GUARD WRITES ONE FIELD, NOT TWO.
    [:L443-L444] zeroes ``fs-reply`` AND ``WE-Error``, and [:L448] then moves 998 to
    ``WE-Error`` ALONE. So a rejected START leaves ``FS-Reply`` at ZERO - and ``FS-Reply``
    is the field the ``status`` clause [copybooks/slseloi3.cob:L5] makes authoritative for
    every other verb - so a caller testing only ``FS-Reply`` reads SUCCESS from an
    operation that positioned nothing. The bridge writes both, ``(99, 997)``. Reproduced
    below by passing ``context.fs_reply`` through unchanged rather than forcing 99.

    ⭐⭐ ACCESS TYPE 9 IS REJECTED BY BOTH PROGRAMS, THOUGH BOTH DECLARE IT.
    [copybooks/wsfnctn.cob:L116] declares ``fn-not-greater-than`` value 9 and the bridge
    even has an ``evaluate`` arm for it [common/otm3MT.cbl:L785]. Here it is worse: the
    guard rejects it AND there is no fourth relational block for it - the four blocks cover
    ``=``, ``<``, ``>`` and ``not <`` [:L455-L482] and there is NO ``not >`` block. So even
    if the guard admitted 9, no START would be issued and control would fall to [:L483] and
    report success without having positioned anything. Reproduced by keeping four blocks.

    ⭐ FOUR SEPARATE ``if`` BLOCKS, NOT ONE ``evaluate``. Each re-tests ``File-Key-No = 1``,
    each issues its own ``start``, each transfers away on ``invalid key``. On success each
    falls THROUGH to the next block, whose ``and fn-<other>`` is false - so exactly one
    START is issued and the rest are skipped by their own conditions. Reproduced as four
    blocks, because collapsing them would hide that the fall-through is what sequences them.

    ⭐ EVERY ``invalid key`` PHRASE MOVES 21 INTO ``Fs-Reply`` ONLY [:L458, :L465, :L472,
    :L479] - not into ``WE-Error``, unlike ``aa050``'s [:L422] which moves it into both.
    Two paragraphs, two conventions, one program.

    ⭐ ``move OI-Key to OI3-Key.`` AT [:L454] IS THE SITE THE MAINTAINER ANNOTATED
    ``*> copy WS to file`` - the evidence for docstring C4. It happens ONCE here, before the
    four blocks, and AGAIN inside ``aa045-Eval-Keys`` at [:L406], which this paragraph
    performed at [:L442]. So the copy is made twice per START. Reproduced.

    ⭐ [:L486-L487] ARE UNREACHABLE for the same reason as ``aa050``'s tail, with the same
    ``*> should never get here`` comment - plus a second, ``*> changed for acas019 others ?``
    at [:L485], recording that this ``else`` differs from the sibling handlers'.

    Transfers: ``go to aa999-main-exit`` six times, all Class 3; two ``perform`` Class 4.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa060-Process-Start"
    ]                                                              # [:L441]
    aa045_eval_keys(context)                                       # [:L442] - Class 4
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))          # [:L443-L444]
    context.cobol_file_status = 0                                  # [:L445]

    access_type = int(context.file_access.access_type)
    # `if access-type < 5 or > 8` [:L447] - the bridge's identical test reports 997.
    if not start_access_type_is_valid(access_type):
        context.status(context.fs_reply, int(WeError.FILE_KEY_NO_OUT_OF_RANGE))  # [:L448]
        # ONE ERROR, through the shared reporter - the refusal returns a failing
        # status to the caller, so WARNING was the wrong level, and it is now the same
        # level as the BRIDGE's record for the identical test.
        log_handler_failure(
            _LOG,
            program=HANDLER_PROGRAM_ID,
            paragraph="aa060-Process-Start",
            locator="[common/acas019.cbl:L447-L449]",
            fs_reply=int(context.fs_reply),
            we_error=int(WeError.FILE_KEY_NO_OUT_OF_RANGE),
            detail="Access-Type %d rejected with We-Error 998; the BRIDGE rejects the "
            "identical range with 997 [common/otm3MT.cbl:L760-L762] - anomaly "
            "N-start-997-vs-998" % access_type,
        )
        return aa999_main_exit(context)                            # [:L449] - Class 3

    # `move OI-Key to OI3-Key.  *> copy WS to file` [:L454] - the SECOND time this CALL,
    # after `aa045-Eval-Keys` already did it at [:L406].
    _move_linkage_to_file_record(context.record, context.file_record)
    key_value = _oi3_key_image(context.file_record)
    key_number = int(context.file_access.logging_data.file_key_no)

    # FOUR separate blocks [:L455-L482], each re-testing the key number, each with its own
    # `invalid key  move 21 to Fs-Reply  go to aa999-main-exit`. There is NO `not >` block.
    for relation, relation_access_type, block_locator in (
        ("=", int(AccessType.EQUAL_TO), "[common/acas019.cbl:L455-L461]"),
        ("<", int(AccessType.LESS_THAN), "[common/acas019.cbl:L462-L468]"),
        (">", int(AccessType.GREATER_THAN), "[common/acas019.cbl:L469-L475]"),
        ("not <", int(AccessType.NOT_LESS_THAN), "[common/acas019.cbl:L476-L482]"),
    ):
        if key_number == 1 and access_type == relation_access_type:
            reply = context.medium.start(key_value, relation)
            # `status fs-Reply` [copybooks/slseloi3.cob:L5] - the START's status lands
            # first, so a failure outside the '2x' class reaches the caller as itself.
            context.status(reply, context.we_error)
            if _invalid_key_condition(reply):
                # `invalid key  move 21 to Fs-Reply` - `Fs-Reply` ONLY, not `WE-Error`.
                context.status(FsReply.INVALID_KEY_ON_START, context.we_error)
                # NO RECORD HERE. `invalid key move 21 to Fs-Reply` displays nothing,
                # and an `invalid key` on a START is an ORDINARY outcome every caller
                # branches on - the same reasoning that took the equivalent record out
                # of `dal/cursor_state.py`. The status pair IS the report, and it
                # reaches the caller unchanged.
                return aa999_main_exit(context)                    # Class 3
            # On success control FALLS THROUGH; every later block's `and fn-<other>` is
            # false, so no second START is issued.

    if key_number == 1:                                            # [:L483]
        aa041_move_inv_data(context)                               # [:L484] - Class 4
    else:
        # UNREACHABLE - `*> changed for acas019 others ?` [:L485], `*> should never get
        # here` [:L487].
        context.status(FsReply.ERROR, int(WeError.FILE_KEY_NO_OUT_OF_RANGE))  # [:L486-L487]
    return aa999_main_exit(context)                                # [:L488] - Class 3


def aa070_process_write(context: _HandlerContext) -> tuple[int, int]:
    """``aa070-Process-Write.`` - [common/acas019.cbl:L490-L498].

    ::

        move     206 to WS-No-Paragraph.                            [:L491]
        move     WS-OTM3-Record to Open-Item-Record-3.              [:L492]
        move     zeros to FS-Reply  WE-Error.                       [:L493]
        move     zero to Cobol-File-Status.                         [:L494]
        write    Open-Item-Record-3 invalid key                     [:L495]
                 move 22 to FS-Reply                                [:L496]
        end-write.
        perform  aa041-Move-Inv-Data.                               [:L497]
        go       to aa999-main-exit.                                [:L498]

    ⭐ 22 IS DUPLICATE-KEY, and it is the ONLY status this paragraph can report besides
    zero: an ISAM ``write``'s ``invalid key`` on a keyed file means the key already exists.
    The BRIDGE reaches the same 22 by inspecting the driver's errno for 1062 or 1022 or
    SQLSTATE 23000 [common/otm3MT.cbl:L881-L884] - two entirely different mechanisms for
    the same published status, which is precisely why the status protocol has to be emulated
    rather than approximated (AAP section 0.1.1).

    ⭐ ``WE-Error`` IS ZEROED AND NEVER SET, so a duplicate reports ``(22, 0)``. The bridge
    does the same on ITS write path [common/otm3MT.cbl:L866, :L876]: both programs leave a
    failed write with no internal error code, and it is the ONE failure they agree on.

    ⭐ ``perform aa041-Move-Inv-Data`` RUNS ON BOTH PATHS [:L497] - after a successful write
    and after a duplicate alike - so the logging key is always the record's own. Reproduced
    by placing the call outside any branch.

    ⭐ THE KEY GUARD AT [:L245-L259] DOES NOT COVER FUNCTION 5, so a write with any key
    number reaches here. There is only one key, so nothing turns on it.

    Transfers: ``go to aa999-main-exit`` Class 3; the ``perform`` Class 4.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa070-Process-Write"
    ]                                                              # [:L491]
    # `move WS-OTM3-Record to Open-Item-Record-3.` [:L492] - deviation D4.
    _move_linkage_to_file_record(context.record, context.file_record)
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))          # [:L493]
    context.cobol_file_status = 0                                  # [:L494]
    reply = context.medium.write(context.file_record)              # [:L495]
    # `status fs-Reply` [copybooks/slseloi3.cob:L5] stores the write's own status in the
    # linkage field before any phrase runs - see `_invalid_key_condition`.
    context.status(reply, context.we_error)
    if _invalid_key_condition(reply):
        # `invalid key  move 22 to FS-Reply` [:L496] - the phrase NORMALISES the whole '2x'
        # class to 22; `WE-Error` is untouched. A failure outside that class keeps the
        # status stored above and never reaches here.
        context.status(FsReply.DUPLICATE_KEY, context.we_error)
    aa041_move_inv_data(context)                                   # [:L497] - Class 4
    return aa999_main_exit(context)                                # [:L498] - Class 3


def aa080_process_delete(context: _HandlerContext) -> tuple[int, int]:
    """``aa080-Process-Delete.`` - [common/acas019.cbl:L500-L509].

    ::

        move     207 to WS-No-Paragraph.                            [:L502]
        move     WS-OTM3-Record to Open-Item-Record-3.              [:L503]
        move     zeros to FS-Reply  WE-Error.                       [:L504]
        move     zero to Cobol-File-Status.                         [:L505]
        delete   Open-Item-File-3 record invalid key                [:L506]
                 move 21 to FS-Reply                                [:L507]
        end-delete.
        perform  aa041-Move-Inv-Data.                               [:L508]
        go       to aa999-main-exit.                                [:L509]

    ⭐ 21 HERE AND 22 IN ``aa070``, for the mirror-image condition. A write fails because
    the key EXISTS and reports duplicate-key; a delete fails because the key does NOT exist
    and reports invalid-key-on-start. Both leave ``WE-Error`` at zero.

    ⭐ THE BRIDGE REPORTS ``(99, 995)`` FOR THE SAME FAILURE
    [common/otm3MT.cbl:L933-L934] - a hard error with a specific code, where the handler
    reports a soft 21 with none. The FOURTH disagreement between the two programs.

    ⭐ ``move WS-OTM3-Record to Open-Item-Record-3`` FIRST [:L503], exactly as ``aa070`` and
    ``aa090`` do - a delete needs only the key, and the whole record is moved anyway. The
    ``*> For delete can ignore Desc key`` comment at [:L402] is about the same idea seen
    from ``aa045-Eval-Keys``.

    Transfers: ``go to aa999-main-exit`` Class 3; the ``perform`` Class 4.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa080-Process-Delete"
    ]                                                              # [:L502]
    _move_linkage_to_file_record(context.record, context.file_record)  # [:L503]
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))          # [:L504]
    context.cobol_file_status = 0                                  # [:L505]
    reply = context.medium.delete(context.file_record)             # [:L506]
    # `status fs-Reply` [copybooks/slseloi3.cob:L5] - the status lands first.
    context.status(reply, context.we_error)
    if _invalid_key_condition(reply):
        # `invalid key  move 21 to FS-Reply` [:L507] - 21 here where the write forces 22,
        # and `WE-Error` untouched in both. The BRIDGE reports a failed delete as
        # (99, 995) instead [common/otm3MT.cbl:L1005-L1012] - one of the five
        # handler/bridge disagreements in docstring PART 6.
        context.status(FsReply.INVALID_KEY_ON_START, context.we_error)
    aa041_move_inv_data(context)                                   # [:L508] - Class 4
    return aa999_main_exit(context)                                # [:L509] - Class 3


def aa090_process_rewrite(context: _HandlerContext) -> tuple[int, int]:
    """``aa090-Process-Rewrite.`` - [common/acas019.cbl:L511-L521].

    ::

        move     208 to WS-No-Paragraph.                            [:L514]
        move     WS-OTM3-Record to Open-Item-Record-3.              [:L515]
        move     zeros to FS-Reply  WE-Error.                       [:L516]
        move     zero to Cobol-File-Status.                         [:L517]
        rewrite  Open-Item-Record-3 invalid key                     [:L518]
                 move 21 to FS-Reply                                [:L519]
        end-rewrite                                                 [:L520]
        perform  aa041-Move-Inv-Data.                               [:L521]
        go       to aa999-main-exit.                                [:L522]

    ⭐ ANOMALY N-punctuation, THE HANDLER'S INSTANCE: ``end-rewrite`` at [:L520] has NO
    TERMINATING PERIOD, where ``aa070``'s ``end-write.`` [:L496] and ``aa080``'s
    ``end-delete.`` [:L507] both do. The next statement is a ``perform``, so the missing
    period changes nothing - the scope terminator already closed the ``rewrite``. Three
    sibling paragraphs, two punctuations. Recorded; ⛔ not normalised.

    ⭐ 21 AGAIN, matching ``aa080`` rather than ``aa070``: a rewrite of an absent key is an
    invalid key, not a duplicate. The BRIDGE reports ``(99, 994)``
    [common/otm3MT.cbl:L978-L979] - the FIFTH disagreement, and note 994/995 differ between
    rewrite and delete on the bridge side while the handler uses 21 for both.

    Transfers: ``go to aa999-main-exit`` Class 3; the ``perform`` Class 4.
    """
    context.file_access.logging_data.ws_no_paragraph = HANDLER_PARAGRAPH_NUMBERS[
        "aa090-Process-Rewrite"
    ]                                                              # [:L514]
    _move_linkage_to_file_record(context.record, context.file_record)  # [:L515]
    context.status(FsReply.SUCCESS, int(WeError.SUCCESS))          # [:L516]
    context.cobol_file_status = 0                                  # [:L517]
    reply = context.medium.rewrite(context.file_record)            # [:L518]
    # `status fs-Reply` [copybooks/slseloi3.cob:L5] - the status lands first.
    context.status(reply, context.we_error)
    if _invalid_key_condition(reply):
        # `invalid key  move 21 to FS-Reply` [:L519]. The BRIDGE reports (99, 994)
        # [common/otm3MT.cbl:L1084-L1091] - another of the five disagreements.
        context.status(FsReply.INVALID_KEY_ON_START, context.we_error)
    # [:L520] `end-rewrite` carries NO period - anomaly N-punctuation.
    aa041_move_inv_data(context)                                   # [:L521] - Class 4
    return aa999_main_exit(context)                                # [:L522] - Class 3


def aa100_bad_function(context: _HandlerContext) -> tuple[int, int]:
    """``aa100-Bad-Function.`` - [common/acas019.cbl:L524-L529].

    ::

    *> Houston; We have a problem                                   [:L526]
        move     999 to WE-Error.                         *> 999     [:L528]
        move     99  to fs-reply.                                    [:L529]

    ⭐ 999 HERE, 990 IN THE BRIDGE for the identical condition
    [common/otm3MT.cbl:L1300] - and both programs carry the SAME "Houston" comment, so the
    divergence is a copy that was edited on one side only. ``dal/status.py`` publishes 999
    as ``NOT_USED`` and 990 as ``UNKNOWN_UNEXPECTED``.

    ⭐ 992 - ``INVALID_FUNCTION`` - is the vocabulary's code for exactly this and NEITHER
    program uses it.

    ⭐ THERE IS NO ``go to`` HERE. The paragraph FALLS THROUGH into ``aa999-main-exit``
    [:L531], which is why an unrecognised function still gets logged. AAP section 0.4.2:
    fall-through made explicit.

    ⭐ REACHED TWO WAYS: ``when other`` [:L300-L301] and the unconditional
    ``go to aa100-Bad-Function`` at [:L305], whose comment is
    ``*> Should never get here but in case :(``.
    """
    # ONE ERROR, through the shared reporter, matching the bridge's own record for
    # its equivalent paragraph.
    log_handler_failure(
        _LOG,
        program=HANDLER_PROGRAM_ID,
        paragraph="aa100-Bad-Function",
        locator="[common/acas019.cbl:L528]",
        fs_reply=int(FsReply.ERROR),
        we_error=int(WeError.NOT_USED),
        detail="File-Function %d is not one this handler implements; the handler "
        "reports We-Error 999 where the bridge reports 990 "
        "[common/otm3MT.cbl:L1300]" % int(context.file_access.file_function),
    )
    context.status(FsReply.ERROR, int(WeError.NOT_USED))           # [:L528-L529]
    # No `go to`: falls through into `aa999-main-exit` [:L531].
    return aa999_main_exit(context)


def aa999_main_exit(context: _HandlerContext) -> tuple[int, int]:
    """``aa999-main-exit.`` - [common/acas019.cbl:L531-L534].

    ::

        if       Testing-1                                          [:L532]
                 perform Ca-Process-Logs                            [:L533]
        end-if.                                                     [:L534]

    Then falls through into ``aa-main-exit`` [:L536] and ``aa-Exit. exit program.``
    [:L540-L541].

    ⭐ THIS IS THE FLAT-FILE PATH'S LOGGING POINT, and it is NOT reached on the DAL path -
    the RDB branch leaves for ``AA-Main-Exit`` at [:L265], which is BELOW this paragraph.
    Anomaly N-nolog-on-dal: on the DAL path the bridge's own ``ba999-end`` logs instead, so
    a CALL produces exactly one log record either way, from a different program each time.

    ⭐ ``aa030-Process-Close`` PERFORMS this paragraph rather than falling into it [:L353],
    which is what lets it log twice - see :func:`aa030_process_close`.
    """
    if _testing_1(context.dal_common):                             # [:L532]
        acas019_ca_process_logs(context)                           # [:L533]
    return aa_main_exit(context)


def aa_main_exit(context: _HandlerContext) -> tuple[int, int]:
    """``aa-main-exit.`` - [common/acas019.cbl:L536-L538]. A label with no statements.

    ::

     aa-main-exit.                                                  [:L536]
    *> Now have processed cobol flat file,  so ..                    [:L538]

    The paragraph is empty and exists to be a ``go to`` target - and it has TWO callers with
    opposite intent: the RDB branch transfers here at [:L265] to SKIP the whole flat-file
    section, and ``aa030`` transfers here at [:L357] to skip a SECOND logging pass. Both
    then fall through into ``aa-Exit``.

    ⭐ THE COMMENT AT [:L538] IS TRUE ON ONE PATH ONLY. "Now have processed cobol flat file"
    is exactly what has NOT happened when the RDB branch arrives here. Recorded.
    """
    return aa_exit(context)


def aa_exit(context: _HandlerContext) -> tuple[int, int]:
    """``aa-Exit.  exit program.`` - [common/acas019.cbl:L540-L541].

    The return to the caller. ``File-Access`` already carries the status pair, so the
    returned tuple is a convenience and not the authoritative channel - the COBOL
    communicates through linkage, and so does this module.
    """
    return context.fs_reply, context.we_error


def ba_process_rdbms(context: _HandlerContext) -> None:
    """``ba-Process-RDBMS section.`` - [common/acas019.cbl:L543-L549]. A bare section head.

    Its four comment lines are the only statement of intent the handler makes about the DAL
    path, VERBATIM::

    *>********************************************************************
    *>  Here we call the relevent RDBMS module for this table            *
    *>   which will include processing any other joined tables as needed *
    *>********************************************************************

    ⭐ THE SECTION IS ENTERED AT ``ba010-Test-WS-Rec-Size``, NOT AT ``ba012``, AND THE
    DIFFERENCE IS THE LOG FILE NUMBER. ``perform ba-Process-RDBMS`` at [:L264] performs the
    WHOLE SECTION, so it begins at ``ba010`` [:L551] - which does nothing but
    ``move 25 to WS-Log-File-no`` [:L557] - and falls through into ``ba012``. The FLAT-FILE
    path instead performs ``ba012`` DIRECTLY at [:L271], skipping ``ba010`` entirely, so it
    keeps the 15 that ``aa010-main`` set. Anomaly N-log: the 15->25 overwrite happens on the
    DAL path only, and the entry point is what decides it.

    ⭐ "any other joined tables as needed" DOES NOT APPLY HERE. ``SAITM3-REC`` is a single
    table with no lines table, unlike ``acas016`` and ``acas026``, whose bridges own a
    header and a lines table each. The comment is generic boilerplate; recorded as such.

    ⭐⭐ THIS FUNCTION IS WHERE THE SECTION'S FALL-THROUGH LIVES, AND IT IS THE ONLY PLACE
    IT LIVES. ``perform ba-Process-RDBMS`` [:L265] names a SECTION, so its range is every
    paragraph in the section and control falls from each into the next:
    ``ba010-Test-WS-Rec-Size`` [:L551] -> ``ba012-Test-WS-Rec-Size-2`` [:L559] ->
    ``ba015-Test-Ends`` [:L601] -> ``ba-rdbms-exit`` [:L619]. ``perform
    ba012-Test-WS-Rec-Size-2.`` [:L271] names a PARAGRAPH, so its range is that paragraph
    ALONE and control returns to [:L271] without ever reaching ``ba015`` - which is why the
    flat-file path does not call the bridge even though it runs the same guard.

    Per AAP section 0.4.2, ``PERFORM ... THRU`` and fall-through become explicit sequential
    calls at the composition site. The four calls below ARE that composition; each
    paragraph function performs only its own statements and none calls the next, so the two
    ranges differ in exactly the way the COBOL's do.
    """
    # `ba010-Test-WS-Rec-Size` [:L551] - the log file renumber, then fall through.
    ba010_test_ws_rec_size(context)
    # `ba012-Test-WS-Rec-Size-2` [:L559]. A True return means it took
    # `go to ba-rdbms-exit` [:L586], which skips the remainder of the section - Class 2.
    if ba012_test_ws_rec_size_2(context):
        ba_rdbms_exit(context)
        return
    # `ba015-Test-Ends` [:L601] - the bridge CALL, then fall through.
    ba015_test_ends(context)
    # `ba-rdbms-exit.  exit section.` [:L619-L620].
    ba_rdbms_exit(context)


def ba010_test_ws_rec_size(context: _HandlerContext) -> None:
    """``ba010-Test-WS-Rec-Size.`` - [common/acas019.cbl:L551-L557]. ONE statement.

    ::

    *>     Test on very first call only  (So do NOT use var A & B again)   [:L553]
    *>       Lets test that Data-record size is = or > than declared Rec in DAL  [:L554]
    *>          as we cant adjust at compile/run time due to ALL Cobol compilers ?  [:L555]
        move     25 to WS-Log-File-no.        *> for FHlogger              [:L557]

    ⭐ THE PARAGRAPH IS NAMED FOR WORK IT DOES NOT DO. Its three comment lines describe the
    record-size test, and the test itself is in ``ba012-Test-WS-Rec-Size-2`` below. All this
    paragraph does is renumber the log file. So the name and the comments belong to the next
    paragraph, and only the fall-through makes the pairing work.

    ⭐ ANOMALY N-log: 15 -> 25, and the field is spelled ``WS-Log-File-no`` here against
    ``WS-Log-File-No`` at [:L241]. The pair 15->25 is ALSO ``acas008``'s
    [common/acas008.cbl:L294, :L523], which pairs it with ``WS-Log-System = 1`` (IRS) where
    this handler pairs it with 3 (SL). Only the ``(system, file)`` pair identifies the
    handler - the fourth such collision in the folder, after 11->21, 12->22 three times and
    13->23 twice.

    ⭐ IT HAS NO TRANSFER and falls through into ``ba012-Test-WS-Rec-Size-2`` [:L559]. The
    fall-through is composed by :func:`ba_process_rdbms`, not issued from here, because
    ``ba012`` is ALSO performed on its own from [:L271] and a call from here would make the
    two ranges identical - see :func:`ba_process_rdbms` for why they must not be.
    """
    context.file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB  # 25 [:L557]


def ba012_test_ws_rec_size_2(context: _HandlerContext) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` - [common/acas019.cbl:L559-L599]. Guard and credentials.

    VERBATIM, and the indentation matters because it is what fixes the guard's extent::

        ba012-Test-WS-Rec-Size-2.                                                   [:L559]
             if       A = zero                        *> so it is being called first time
                      move     function Length (
                                                WS-OTM3-Record
                                                         ) to A
                      move     function length (
                                                Open-Item-Record-3
                                                         ) to B
                      if   A < B                      *> COULD LET caller module deal with these errors !!!!!!!
                           move 901 to WE-Error       *> 901 Programming error; temp rec length is wrong caller must stop
                           move 99 to fs-reply        *> allow for last field ( FILLER) not being present in layout.
                      end-if
                      if       WE-Error = 901                  *> record length wrong so display error, accept and then stop run.
                               move spaces to Display-Blk
                               string SL904          delimited by size
                                      A              delimited by size
                                      " < "          delimited by size
                                      "OTM3-Record = " delimited by size
                                      B              delimited by size    into Display-Blk
                               end-string
                               display Display-Blk at 2301 with erase eol     *> BUT WILL REMIND ME TO SET IT UP correctly
                               display SL901 at 2401 with erase eol
                               if  Testing-1
                                   perform Ca-Process-Logs
                               end-if
                               accept Accept-Reply at 2433
                               go to ba-rdbms-exit
                      end-if
        *>
        *>  Not a error comparing the length of records so - -
        *>  Load up the DB settings from the system record as its not passed on
        *>           hopefully once is enough  :)
        *>
                      move     RDBMS-DB-Name to DB-Schema
                      move     RDBMS-User    to DB-UName
                      move     RDBMS-Passwd  to DB-UPass
                      move     RDBMS-Port    to DB-Port
                      move     RDBMS-Host    to DB-Host
                      move     RDBMS-Socket  to DB-Socket
             end-if.                                                            [:L599]

    ⭐⭐ EVERYTHING IS INSIDE ``if A = zero``, THE SIX CREDENTIAL MOVES INCLUDED. The
    ``end-if.`` at [:L599] closes the outer ``if`` opened at [:L561], and the six moves at
    [:L593-L598] sit at the same indentation as the two nested ``if``s above them. So the
    maintainer's ``*> hopefully once is enough  :)`` [:L591] is CORRECT: the credentials load
    on the first CALL of the process and never again. ``A`` and ``B`` are WORKING-STORAGE
    ``77`` items with ``value zero`` [:L194-L195], carrying the maintainer's own
    ``*> A & B used in 1st test ONLY`` and ``*>  in ba-Process-RDBMS``, so they persist
    between CALLs; once ``A`` holds 118 the whole paragraph is a no-op forever.

    ⭐⭐ THE ONE-SHOT GUARD IS SHARED BY BOTH ENTRY POINTS, and that is a latent defect -
    anomaly N-first-call-guard-shared. ``A`` is one variable, so whichever path runs first
    consumes it. A flat-file CALL arriving first would set ``A`` to 118 while loading
    credentials it cannot use, and a later RDB CALL would then skip [:L593-L598] entirely
    and try to connect with an unset ``DB-Schema``. It is unreachable in practice because
    ``File-System-Used`` is one system-record flag that does not change within a run, so
    both paths never occur in one process. Reproduced as written - the guard below is keyed
    on the shared :attr:`_BridgeWorkingStorage.ws_length_a` and nothing distinguishes the
    caller.

    ⭐⭐ THE SECOND ``if`` TESTS ``WE-Error``, NOT ``A < B``, AND THE TWO ARE SEPARATE
    STATEMENTS - anomaly N-stale-901. [:L568-L571] may set 901, and [:L572] then asks
    whether ``WE-Error`` IS 901. Nothing zeroes ``WE-Error`` before this point: ``aa010-main``
    would have, but [:L279-L280] are COMMENTED OUT, and the RDB path reaches here from
    [:L265] with whatever the CALLER left in the linkage item. So a caller that still holds
    901 from an earlier failure drives the whole diagnostic-and-transfer branch even though
    the record sizes agree. Reproduced exactly: the second test below reads ``WE-Error``
    rather than re-deriving the comparison.

    ⭐ THE TWO MOVES ARE IN THIS ORDER - ``901 to WE-Error`` FIRST [:L569], ``99 to fs-reply``
    SECOND [:L570] - which is the reverse of the pairing every other paragraph in this
    handler uses. Recorded; the pair is written atomically here, so the order has no
    observable effect and is not reproduced as two statements.

    ⭐ IT COMPARES THE LINKAGE VIEW AGAINST THE FILE VIEW - ``function Length(WS-OTM3-Record)``
    against ``function length(Open-Item-Record-3)``, with the intrinsic spelled ``Length``
    once and ``length`` once. Both records are 118 bytes [copybooks/slwsoi3.cob:L4],
    [copybooks/slwsoi.cob:L6], so ``A < B`` is false and the guard passes. That 118-byte
    agreement between two copybooks - recorded in docstring PART 5 - is exactly what makes
    this guard a permanent no-op, and it is worth contrasting with the records whose declared
    sizes are contradicted by their own field sums (AAP anomaly #15).

    ⭐ 901 IS ``RECORD_SIZE_MISMATCH``, reported with ``Fs-Reply`` 99, and the maintainer's
    own ``*> COULD LET caller module deal with these errors !!!!!!!`` [:L568] records that he
    considered doing something else with it.

    ⭐ THE DIAGNOSTIC BRANCH LOGS - ``if Testing-1 perform Ca-Process-Logs end-if``
    [:L582-L584] - WHICH CONTRADICTS ``Ca-Process-Logs``'s OWN COMMENT. That comment, on the
    label line at [:L623], reads ``*> Not called on DAL access as it does it already``, yet
    this call site is inside a paragraph the DAL path performs. Anomaly
    N-nolog-on-dal-contradicted: the claim holds for the normal path and is false for this
    one. Reproduced - the branch below calls :func:`acas019_ca_process_logs` under
    ``Testing-1``.

    ⭐ THE ``display``/``accept`` PAIR IS DEVIATION D2: two ``display ... with erase eol``
    become one log record at ERROR, and the ``accept Accept-Reply at 2433`` [:L585] is
    DROPPED because it only blocks a terminal. The ``go to ba-rdbms-exit`` [:L586] that
    follows it IS PRESERVED - AAP section 0.3.4's third rule exactly.

    Returns:
        ``True`` when the paragraph took ``go to ba-rdbms-exit`` at [:L586], so that
        :func:`ba_process_rdbms` can skip the rest of the section - AAP section 0.4.2
        Class 2. ``False`` on the normal path, where the section falls into ``ba015``.
        The flat-file caller at [:L271] performs this paragraph ALONE and therefore ignores
        the flag; see :func:`ba_process_rdbms` for why the two ranges differ.
    """
    if _BRIDGE.ws_length_a == 0:                                    # [:L561]
        # `move function Length (WS-OTM3-Record) to A` [:L562-L564] and
        # `move function length (Open-Item-Record-3) to B` [:L565-L567]. Both 118.
        _BRIDGE.ws_length_a = RECORD_LENGTH
        _BRIDGE.ws_length_b = RECORD_LENGTH
        if _BRIDGE.ws_length_a < _BRIDGE.ws_length_b:               # [:L568]
            # `move 901 to WE-Error` [:L569] then `move 99 to fs-reply` [:L570] - that
            # order, which is the reverse of this handler's usual pairing.
            context.status(FsReply.ERROR, int(WeError.RECORD_SIZE_MISMATCH))

        # [:L572] tests `WE-Error = 901`, NOT the comparison above - anomaly N-stale-901.
        # A caller that arrived holding 901 takes this branch with sizes that agree.
        if int(context.file_access.we_error) == int(WeError.RECORD_SIZE_MISMATCH):
            # `move spaces to Display-Blk` then the STRING into it [:L573-L579]. The
            # assembled text is built so the log record carries the same content the
            # screen would have: SL904, A, " < ", "OTM3-Record = ", B.
            display_blk = _cobol_move_alphanumeric(
                f"{_SL904}{_BRIDGE.ws_length_a:04d} < "
                f"OTM3-Record = {_BRIDGE.ws_length_b:04d}",
                _DISPLAY_BLK_WIDTH,
            )
            # `display Display-Blk at 2301 with erase eol` [:L580], carrying
            # `*> BUT WILL REMIND ME TO SET IT UP correctly`, and `display SL901 at 2401`
            # [:L581]. THE TWO DISPLAYS ARE NOT ONE RECORD, because they are not the
            # same kind of thing:
            #   * [:L580] carries `SL904` and the two lengths - the substance, so ONE
            #     record at ERROR, the severity a programming error the caller must stop
            #     for deserves.
            #   * [:L581] carries `SL901`, whose whole text asks the operator to note the
            #     error and hit return. That is the acknowledgement half, paired with the
            #     `accept` at [:L585], and AAP section 0.3.4 drops an acknowledgement
            #     pause entirely - QUOTING IT IN A LOG LINE IS STILL EMITTING IT, to a
            #     destination where no operator can answer it.
            #   * [:L586]'s `go to ba-rdbms-exit` is CONTROL, and it is preserved as this
            #     function's `return True`.
            _LOG.error(
                "%s: %s [common/acas019.cbl:L580]",
                HANDLER_PROGRAM_ID,
                display_blk.rstrip(),
            )
            # `if Testing-1 perform Ca-Process-Logs end-if` [:L582-L584] - the call site
            # that contradicts the paragraph's own comment at [:L623].
            if int(context.dal_common.sw_testing) == 1:             # [:L582]
                acas019_ca_process_logs(context)                    # [:L583]
            # `accept Accept-Reply at 2433` [:L585] - DROPPED, deviation D2.
            # `go to ba-rdbms-exit` [:L586] - PRESERVED, Class 2, reported to the caller.
            return True

        # The six credential moves [:L593-L598], INSIDE the guard, so once per process.
        # `*> Load up the DB settings from the system record as its not passed on` [:L590]
        # and `*> hopefully once is enough  :)` [:L591] - and it is.
        rdb = load_rdb_data_once(context.system)
        target = context.file_access.rdb_data
        target.db_schema = rdb.db_schema                             # [:L593]
        target.db_uname = rdb.db_uname                               # [:L594]
        target.db_upass = rdb.db_upass                               # [:L595]
        target.db_port = rdb.db_port                                 # [:L596]
        target.db_host = rdb.db_host                                 # [:L597]
        target.db_socket = rdb.db_socket                             # [:L598]
        # The bridge's `ba020` reads the six `DB-*` fields; `connection.mysql_1000_open`
        # reads the same six values from the system record itself, so the record is
        # remembered rather than the credentials being marshalled a second time (AAP: do
        # not duplicate connection.py's credential load). Remembered INSIDE the guard, so
        # anomaly N-first-call-guard-shared reproduces: skip the guard, get no record.
        _BRIDGE.system_record = context.system

    # `end-if.` [:L599] - no transfer, so the section falls into `ba015-Test-Ends`.
    return False


def ba015_test_ends(context: _HandlerContext) -> None:
    """``ba015-Test-Ends.`` - [common/acas019.cbl:L601-L617]. The bridge CALL, inline.

    ::

    *>   HERE we need a CDF [Compiler Directive] to select the correct DAL based  [:L604]
    *>     on the pre SQL compiler e.g., JCs or dbpre or Prima conversions <<<<  ? >>>>>  [:L605]
    *>        Do this after system testing and pre code release.                  [:L606]
    *>  NOW SET UP FOR JC pre-sql compiler system.                                [:L608]
    *>   DAL-Datablock not needed unless using RDBMS DAL from Prima & MS Sql       [:L609]
        call     "otm3MT" using  File-Access                                       [:L611]
                                     ACAS-DAL-Common-data                          [:L612]
                                     WS-OTM3-Record                                [:L614]
        end-call.                                                                  [:L615]
    *>   Any errors leave it to caller to recover from                              [:L617]

    ⭐ ANOMALY N-nobadal: THERE IS NO ``ba020-*`` PARAGRAPH IN THIS HANDLER. The bridge CALL
    is inline here, which is the ``acas008``/``acas015``/``acas016`` shape;
    ``acas005``/``acas006``/``acas007``/``acas012`` route it through a separate paragraph.
    Reproduced by NOT creating a ``ba020_process_dal`` function.

    ⭐ ANOMALY N-cdftodo: the unfinished compiler-directive plan at [:L604-L606], still
    unresolved, with the maintainer's own ``<<<<  ? >>>>>``. Recorded; the JC pre-SQL bridge
    is the one wired in, as [:L608] says.

    ⭐⭐ [:L617] IS THE MODULE'S ERROR CONTRACT IN THE MAINTAINER'S OWN WORDS -
    ``*> Any errors leave it to caller to recover from``. Neither this function nor
    :func:`otm3_mt` nor :func:`dispatch` raises: every failure becomes a status pair in
    ``File-Access``.

    ⭐ THE PARAMETER ORDER IS THE BRIDGE'S, NOT THE HANDLER'S - ``File-Access`` first, then
    ``ACAS-DAL-Common-data``, then the record. Rule R-5 publishes both orders.

    ⭐ IT HAS NO TRANSFER and falls through into ``ba-rdbms-exit`` [:L619]. As with
    ``ba010``, the fall-through is composed by :func:`ba_process_rdbms` rather than issued
    from here, so each paragraph function is exactly its own paragraph.
    """
    # `call "otm3MT" using File-Access ACAS-DAL-Common-data WS-OTM3-Record` [:L611-L615].
    otm3_mt(context.file_access, context.dal_common, context.record)
    # `*> Any errors leave it to caller to recover from` [:L617] - the reply is read back
    # from the linkage item and NOT interpreted here.
    context.read_status()


def ba_rdbms_exit(context: _HandlerContext) -> None:
    """``ba-rdbms-exit.  exit section.`` - [common/acas019.cbl:L619-L620].

    The section's exit. Two callers: the record-size guard transfers here at [:L581], and
    ``ba015-Test-Ends`` falls into it. ``exit section`` returns to the ``perform
    ba-Process-RDBMS`` at [:L264], after which ``aa010-main`` transfers to ``AA-Main-Exit``.

    ⭐ IT DOES NOT LOG. ``Ca-Process-Logs`` is BELOW it at [:L623] and is reached only by an
    explicit ``perform`` - which nothing on this path issues. Anomaly N-nolog-on-dal: the
    bridge's ``ba999-end`` already logged.

     AND NEITHER DOES THIS FUNCTION. ``exit section`` is one statement that writes
    nothing and displays nothing, so the position trace this paragraph used to emit was
    invented (R-4) - and it contradicted the docstring immediately above it, which says
    the paragraph does not log. The status pair it announced is the caller's to read from
    ``File-Access``, which is where the section leaves it.
    """
    del context


def acas019_ca_process_logs(context: _HandlerContext) -> None:
    """``Ca-Process-Logs.`` in ``acas019`` - [common/acas019.cbl:L623-L627], VERBATIM::

     Ca-Process-Logs.       *> Not called on DAL access as it does it already   [:L623]
         call     "fhlogger" using File-Access                                  [:L626]
                                   ACAS-DAL-Common-data.                        [:L627]

    ⭐⭐ ANOMALY N-nolog-on-dal, STATED BY THE MAINTAINER ON THE LABEL LINE ITSELF. The
    comment is not above the paragraph, it is ON it: ``*> Not called on DAL access as it
    does it already``. So this paragraph runs on the FLAT-FILE path only, from
    ``aa999-main-exit`` [:L533] and from ``aa030``'s second, deliberate call [:L356]. On the
    DAL path the bridge's ``ba999-end`` logs instead [common/otm3MT.cbl:L1323-L1324], which
    is why one CALL yields exactly one record.

    ⭐ THE NAME IS QUALIFIED BY PROGRAM only because ``otm3MT`` declares a paragraph of the
    same name - see :func:`otm3mt_ca_process_logs` for the reasoning. Two names in each
    program are qualified; every other paragraph keeps its own.

    ``fhlogger`` is out of scope [AAP section 0.2.2], so the record is emitted through
    :func:`acas_posting.dal.status.log_file_handler_record`, THE SAME ONE ADAPTER the
    bridge's like-named paragraph uses, so that the two render identically and differ only
    in the program they name. No database effect, no control-flow effect.

    ``WS-File-Key`` is WITHHELD: on this record it is the customer-and-invoice key
    (CWE-532). ``Log-File-Rec-Written`` is ADVANCED modulo one million rather than pinned
    to 1 - see :func:`otm3mt_ca_process_logs` for why pinning it was wrong twice over.
    """
    logging_data = context.file_access.logging_data
    log_file_handler_record(
        _LOG,
        program=HANDLER_PROGRAM_ID,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=int(context.file_access.file_function),
        access_type=int(context.file_access.access_type),
        fs_reply=int(context.file_access.fs_reply),
        we_error=int(context.file_access.we_error),
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=context.dal_common,
    )
    acas019_ca_exit(context)


def acas019_ca_exit(context: _HandlerContext) -> None:
    """``ca-Exit.  exit.`` in ``acas019`` - [common/acas019.cbl:L629-L630].

    A bare ``exit`` - a no-operation giving the paragraph a name to end at, and the last
    paragraph of the program. Reproduced as a named function so the inventory is complete.
    """


def dispatch(
    system: SystemRecord,
    otm3: OiHeader,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    allow_frozen_placeholder_credentials: bool | None = None,
) -> tuple[int, int]:
    """``call "acas019" using System-Record, WS-OTM3-Record, File-Access, File-Defs, ACAS-DAL-Common-data``.

    THE HANDLER ENTRY POINT, with the handler's five parameters in the handler's own order
    [common/acas019.cbl:L225-L231], VERBATIM::

        Procedure Division Using System-Record

                                 WS-OTM3-Record

                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data.

    Five parameters, and the blank lines are the maintainer's. ``File-Access`` is THIRD
    here, where the bridge's own CALL puts it FIRST [:L611-L615] - both orders are published,
    each as its own function, so a reader following either call site finds the shape it
    wrote (rule R-5). The AAP section 0.4.3 contract for this module is::

        FROM:  call "acas019" using System-Record WS-OTM3-Record File-Access
                                   File-Defs ACAS-DAL-Common-data
        TO:    acas019_otm3.dispatch(system, otm3, file_access, file_defs, dal_common)

    WHAT HAPPENS, in the COBOL's order: the log identity, then the key guard, then the RDB
    branch - and on the DAL path THAT IS ALL, because [:L262-L266] leaves for
    ``AA-Main-Exit`` before the function dispatch is reached (docstring C2). The flat-file
    path continues to ``ba012``, the two commented-out status resets, the ``move spaces to
    SQL-Err SQL-Msg SQL-State``, and the nine-arm ``evaluate`` whose ``aa100-Bad-Function``
    is reachable BOTH from ``when other`` and from the unconditional fall-through at [:L305].

    IT NEVER RAISES - [:L617], the maintainer's own words. Every failure, including a driver
    exception and a connection-policy refusal, becomes an ``FS-Reply``/``We-Error`` pair in
    ``file_access``.

    Args:
        system: ``System-Record`` [copybooks/wssystem.cob], read for
            ``RDBMS-Flat-Statuses`` at [:L262-L263] and for the six credential fields at
            [:L586-L591].
        otm3: ``WS-OTM3-Record``. The handler's LINKAGE declares it by
            ``copy "slwsoi.cob" replacing OI-Header by WS-OTM3-Record`` [:L215] - the SAME
            declaration the bridge uses [common/otm3MT.cbl:L345-L346], which is docstring
            C3's correction to the agent prompt. MUTATED IN PLACE by a successful read.
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L64], carrying the request
            in and the status, diagnostics, logging fields and ``RDB-Data`` out.
        file_defs: ``File-Defs`` [copybooks/wsnames.cob]. Held because the linkage declares
            it; this handler names no field of it, because the RDB path addresses a table
            rather than a file and the flat-file path's ``select`` resolves its own name
            [copybooks/slseloi3.cob]. Recorded as a linkage item consumed by neither path.
        dal_common: ``ACAS-DAL-Common-data``
            [copybooks/Test-Data-Flags.cob:L10-L16] - ``Testing-1`` gates the logging and
            ``Testing-2`` the diagnostics (deviation D2).
        transport: The caller's transport declaration, forwarded to the open. KEYWORD-ONLY
            and NOT part of the frozen five-parameter linkage, for the reason
            ``acas006_gl_posting.dispatch`` gives for the identical parameter: the bridge
            reaches the server through ``RDB-Data`` and a C interface that has no transport
            policy at all [common/otm3MT.cbl:L459], so there is no COBOL operand this could
            correspond to. ``None`` - the default - leaves the working-storage declaration
            alone, and that declaration is itself ``None``, which
            ``connection._require_permitted_connection`` resolves FAIL-CLOSED. Pass
            ``TransportSecurity(isolated_oracle=True)`` to declare the parity harness, or
            ``TransportSecurity(ca_file=...)`` to verify and encrypt. It changes no status,
            no statement and no write order.
        allow_frozen_placeholder_credentials: Whether the shipped placeholders of
            [copybooks/wssystem.cob:L138-L139] may authenticate. Keyword-only for the same
            reason, and ``None`` likewise leaves the working-storage declaration - itself
            ``False`` - alone.

    Returns:
        The ``(FS-Reply, We-Error)`` pair, which is also in ``file_access``.
    """
    # The two keyword-only declarations are recorded in working storage BEFORE the
    # dispatch, because `ba020-Process-Open` reads them from there - it is reached
    # through the nine-arm `evaluate` and cannot take arguments of its own. `None`
    # means "the caller stated nothing", which leaves the fail-closed default in
    # place rather than overwriting it with a permissive one.
    if transport is not None:
        _BRIDGE.transport = transport
    if allow_frozen_placeholder_credentials is not None:
        _BRIDGE.allow_frozen_placeholder_credentials = (
            allow_frozen_placeholder_credentials
        )

    context = _HandlerContext(
        system=system,
        record=otm3,
        file_access=file_access,
        file_defs=file_defs,
        dal_common=dal_common,
    )
    # `File-Defs` is a linkage item this handler never reads a field of. It is part of
    # the contract because the frozen `PROCEDURE DIVISION USING` list names it
    # [common/acas019.cbl:L225-L231], and the parameter above records that; NO RECORD IS
    # EMITTED to prove it. The frozen dispatch displays nothing, so a per-CALL trace was
    # invented (R-4) - and it would have been the highest-volume record in the module,
    # one per handler call, with `file-defs delimiter` carrying a fragment of the
    # deployment's own filesystem convention.
    return aa_process_flat_file(context)
