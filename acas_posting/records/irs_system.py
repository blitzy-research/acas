"""IRS system parameters - the first argument of the IRS linkage shape.

Agent Action Plan section 0.4.1.3 gives this module its whole mandate in one
row of the record-layout transformation table:

    acas_posting/records/irs_system.py | CREATE | copybooks/irswssystem.cob |
    "IRS system parameters - the first argument of the IRS linkage shape
    [irs/irs030.cbl:L552-L554]"

and the folder's rule, from the same section: every module is a CREATE from
its copybook, translating each 05/03 field to a dataclass attribute whose
descriptor is looked up in the generated dictionary, and oddities in the
source are preserved rather than put right.

A note on how the AAP is cited below. COBOL source text is always quoted
verbatim - that is the whole point of a record module. AAP directives, by
contrast, are paraphrased with their section number carrying the provenance,
because rule R-4 prohibits a short vocabulary of "the implementation knows
better" words outright and some of those directives use the very words the
rule bans. Paraphrasing keeps this file clear of the banned vocabulary
without losing a syllable of the meaning.

Its shape is fixed by section 0.8.1 - "Plain modules and dataclasses; no ORM
entity layer" - and by rule R-3, under which the record modules "mirror their
copybooks field for field with nothing added".

This file is a record LAYOUT and nothing else. It binds no argv, opens no
connection, computes no VAT, reads no clock, parses no date and validates
nothing. Those responsibilities belong to acas_posting/cli/args.py,
acas_posting/cli/irs_post.py, acas_posting/programs/irs030_posting.py,
acas_posting/clock.py and acas_posting/dates.py, and not one of them is
imported here - see LAYERING below.

THIS RECORD IS WHY THE IRS ENTRY POINT HAS ITS OWN ARGUMENT SHAPE
-----------------------------------------------------------------
Section 0.1.1 observes that the command-line contract for this migration was
written decades ago, in the LINKAGE SECTIONs:

    "The CLI contract is already written, in the LINKAGE SECTIONs. ... there
    are exactly three distinct shapes. The General Ledger family takes `using
    ws-calling-data, system-record, to-day, file-defs`
    [general/gl070.cbl:L245-L248]. The Sales and Purchase families add the
    fourth system record [sales/sl060.cbl:L395-L399]. The IRS program is
    materially different - it takes neither the calling-data block nor the run
    date: `using IRS-System-Params, WS-System-Record, File-Defs`
    [irs/irs030.cbl:L552-L554]. The Python CLI entry points must accept
    exactly these logical inputs, which means three argument shapes, not one."

Checked against the frozen source, and the plan's citation is exact:

    L552   procedure division using IRS-System-Params
    L553                            WS-System-Record
    L554                            File-Defs.

`IrsSystemParams` is parameter #1 of that third shape. It is the reason
acas_posting/cli/irs_post.py cannot share an argument binding with the other
six entry points, and section 0.4.1.1 says so in as many words: that module
uses "the third linkage shape - IRS-System-Params, WS-System-Record,
File-Defs, with no calling-data block and no to-day".

NO TABLE, NO BRIDGE, NO HANDLER - AND WHY THAT MATTERS HERE
-----------------------------------------------------------
The frozen schema declares 33 tables, five of them IRS-named -
`IRSDFLT-REC` [mysql/ACASDB.sql:L189], `IRSFINAL-REC` [:L214], `IRSNL-REC`
[:L238], `IRSPOSTING-REC` [:L274] and `PSIRSPOST-REC` [:L366] - and NONE of
them is an IRS system table. The entity-to-table spine of section 0.2.1.1 has
no row for copybooks/irswssystem.cob at all; its single `System` row maps
`acas000` key 1 to `systemMT` to `SYSTEM-REC` to copybooks/wssystem.cob,
which is a different copybook and a different record.

So this is a copybook-only, LINKAGE-ONLY record. It reaches no table, passes
through no generated bridge and is reached by no numbered handler. It joins
the small set in this folder that has no MySQL counterpart, alongside
records/calling_data.py, records/file_access.py, records/file_defs.py,
records/maps03.py, records/test_data_flags.py and records/work_records.py.

Two consequences follow, and both are load-bearing.

First, the preserved user requirement of section 0.8.2 - that the maintainer's
one-way COBOL-to-MySQL bridge is what defines the record-layout to table
mapping, and is therefore the data dictionary for this migration - cannot be
applied to this record in the ordinary way, because there is no bridge for it
to define anything with. The copybook is necessarily its own authority here,
and it is the only source the generated dictionary had for these 28 fields.
That is stated
rather than left implicit so that a reader does not go hunting for a
`irswssystemMT.scb` that has never existed.

Second, the dictionary keys for this record take the copybook-only form,
`<COPYBOOK-RECORD>.<FIELD-NAME>`, and never the `<TABLE-NAME>.<COLUMN-NAME>`
form. The loader's table-keyed accessor is meaningless for a record that has
no table, and is not called anywhere in this module; the copybook-record
accessor is what section 3.3 directs be used, and it is what was used.

THE DICTIONARY PROBE, AND THE GUARD IT HAD TO PASS
--------------------------------------------------
Rule R-5 and section 0.8.1's "Data dictionary first" directive require that
every field here cite a generated entry rather than carry hand-typed
metadata. Because the record name collides with the General Ledger system
record (see THE 01-NAME IS LOWER CASE below), the lookup was PROBED before
anything was written, and the probe result is recorded here as the provenance
of every descriptor in this file:

    loader.entries_for_copybook_record("system-record")
        -> 28 entries
        -> distinct copybook.file values: exactly one,
           "copybooks/irswssystem.cob"
        -> system-record.run-date resolves ALPHANUMERIC x(8)
    loader.entries_for_copybook_record("IRS-System-Params")
        -> DictionaryLookupError: no such copybook record
    loader.entries_for_copybook_record("System-Record")
        -> 199 entries, every one from copybooks/wssystem.cob

The working key form is therefore `system-record.<FIELD-NAME>`: the record
half in this copybook's own lower case, each field half in its own casing,
and the two FILLERs disambiguated by the dictionary's own `#` convention as
`filler#39` and `filler#40`. The caller-side `replacing` name
`IRS-System-Params` is NOT a dictionary record name; it names a view that
exists only inside irs030, so it appears in this file as a class name and in
prose, never as a key.

The mandatory guard - that no entry resolves to copybooks/wssystem.cob -
passes, and it passes structurally rather than by luck: loader lookups are
exact and fold no case, so the lower-case record half `system-record.` cannot
reach the General Ledger record's mixed-case `System-Record` keys. The
strongest single check is that `run-date` comes back ALPHANUMERIC x(8); had it
come back `binary-long` this would have been the wrong record entirely
[copybooks/wssystem.cob:L67].

Every field of this record resolves, so the descriptor path is
`FieldDescriptor.from_dictionary_key` for all 28 entries and
`FieldDescriptor.for_working_storage` for none of them.

DRIFT: THERE IS NONE TO REPORT, AND THAT IS ITSELF THE FINDING
--------------------------------------------------------------
`loader.drift_for` was called for this record's fields and returns, for every
one of them, `Drift(signedness=False, usage=False, digits=False, scale=False,
character_length=False, name=False, details=())`. The host-variable view and
the column view are both `None`, so `loader.cite` renders every field as
`bridge=absent  column=absent`, and `anomaly_refs` and `ambiguity_refs` are
empty for all of them.

That is not an omission - it is what a record with one layer looks like. A
field can only drift between layers that both exist, and this record has no
bridge and no column to disagree with its copybook. Contrast
`SALEDGER-REC.SALES-AVERAGE`, where the copybook says signed and both the
bridge and the column say unsigned [copybooks/wssl.cob:L49],
[common/salesMT.cbl:L308]. Nothing of that kind can arise here, and the
absence is recorded so that a later reader does not mistake it for an
unfinished check. Each descriptor still answers `cite()` and `drift()` - the
loader's own primitives, surfaced through the descriptor rather than
reimplemented.

THE COPYBOOK HEADER, VERBATIM - FOUR RECORD SIZES IN SEVEN YEARS
----------------------------------------------------------------
copybooks/irswssystem.cob is 40 lines. Its header is quoted verbatim because
the successive sizes are the evidence for the length contradiction below:

    L3   "Working Storage for the System File"
    L4   "Incomplete Records System ONLY"
    L7   "256 bytes (01/03/09)"
    L8   "288 bytes 21/09/10 - added print-spool-name"
    L9   "312 bytes 21/11/11 - Added first-time-flag, two extra vat rates
          and 15 byte filler"
    L10  "256 bytes 30/11/16 - Removed system file names as using ACAS /
          tables."
    L11  "With this record created by irs.cbl"

Only L9 is wrapped, and only because it is 85 characters long; its words are
unaltered.

L11 names the creator: irs/irs.cbl, the IRS menu shell, which section 0.2.2
places OUT of scope among the "Interactive data-entry, amendment and menu
programs". The record's creation logic is therefore deliberately absent from
the migrated tree, and this note exists so a reader does not go looking for
it. irs/irs.cbl is named here and nowhere else in this file: it is not
imported, not invoked and not reimplemented.

THE RECORD, VERBATIM - L13 THROUGH L40
--------------------------------------
Reproduced exactly as the frozen copybook writes it, including the four
missing byte-offset comments, the eight that are one byte short, the
one-space indentation slip on L23, the capital-L typo on L38 and both
trailing FILLERs. Nothing below has been altered in any way:

L13  01  system-record.
L14      03  run-date           pic x(8).
L15      03  suser              pic x(24).
L16      03  client             pic x(24). *> 56
L17      03  address-1          pic x(24). *> 80
L18      03  address-2          pic x(24).
L19      03  address-3          pic x(24). *> 128
L20      03  address-4          pic x(24). *> 152
L21      03  start-date         pic x(8).  *> 160
L22      03  end-date           pic x(8).  *> 168
L23       03  system-ops       pic x.     *> 169
L24      03  pass-word          pic x(4).  *> 173
L25      03  next-post          pic 9(5).  *> 178
L26      03  vat-rates.
L27          05  vat            pic 99v99. *> 182   *> Standard
L28          05  vat2           pic 99v99. *> 186   *> reduced 1 [not yet used]
L29          05  vat3           pic 99v99. *> 190   *> reduced 2 [not yet used]
L30      03  vat-group redefines vat-rates.
L31          05  vat-psent      pic 99v99    occurs 3.
L32      03  pass-value         pic 9.
L33      03  save-sequ          pic 9.     *> 191
L34      03  system-work-group  pic x(18). *> 209
L35      03  PL-App-Created     pic x.     *> 210
L36      03  PL-Approp-AC       pic 9(5).  *> 215
L37      03  Print-Spool-Name   pic x(32). *> 247
L38      03  First-Time-FLag    pic 9.     *> 248
L39      03  filler             pic 9(7).  *> 255
L40      03  filler             pic x.     *> 256

Counted: one 01-level group, 23 items at 03 level (two of them groups, two of
them FILLER) and four items at 05 level. That is 27 subordinate items, which
is exactly the number of members this module declares, and 28 dictionary
entries once the 01 group itself is counted.

BYTE OFFSETS - THE COPYBOOK'S OWN FIGURES BESIDE THIS MIGRATION'S
-----------------------------------------------------------------
Both columns are given, and NEITHER is presented as a correction of the
other. The left column is what the frozen copybook writes; the right column
is this migration's own arithmetic, computed by summing the declared field
widths in declaration order and treating `vat-group redefines vat-rates` as
occupying no additional bytes.

    line  field              pic     width  copybook  computed
    L14   run-date           x(8)        8   (none)          8
    L15   suser              x(24)      24   (none)         32
    L16   client             x(24)      24       56         56
    L17   address-1          x(24)      24       80         80
    L18   address-2          x(24)      24   (none)        104
    L19   address-3          x(24)      24      128        128
    L20   address-4          x(24)      24      152        152
    L21   start-date         x(8)        8      160        160
    L22   end-date           x(8)        8      168        168
    L23   system-ops         x           1      169        169
    L24   pass-word          x(4)        4      173        173
    L25   next-post          9(5)        5      178        178
    L27   vat                99v99       4      182        182
    L28   vat2               99v99       4      186        186
    L29   vat3               99v99       4      190        190
    L32   pass-value         9           1   (none)        191
    L33   save-sequ          9           1      191        192
    L34   system-work-group  x(18)      18      209        210
    L35   PL-App-Created     x           1      210        211
    L36   PL-Approp-AC       9(5)        5      215        216
    L37   Print-Spool-Name   x(32)      32      247        248
    L38   First-Time-FLag    9           1      248        249
    L39   filler             9(7)        7      255        256
    L40   filler             x           1      256        257

    computed field-width sum   257
    header's claim (L7, L10)   256

ANOMALY - THE DECLARED LENGTH AND THE FIELD SUM DISAGREE BY ONE BYTE
--------------------------------------------------------------------
The widths sum to 257 while the header claims 256, twice - at L7 and again at
L10, seven years apart and across two intervening size revisions.

This is a NEW anomaly. It is not one of the twenty-two the plan registers in
section 0.6.7, and it should be ADDED to docs/migration/anomaly-log.md with
this module named as its recording site. It is a direct structural analogue of
registered anomaly 15, "The batch record's declared length contradicts the sum
of its fields" [copybooks/wsbatch.cob], and it inherits that anomaly's open
question verbatim from section 0.6.8:

    "Whether the declared length or the field sum governs the record actually
    read affects field alignment for the trailing fields, and only execution
    shows which."

The same question applies here, and to the same trailing fields - the eight
from L33 to L40 whose offset comments are also the ones that disagree. It is
recorded as an open question for docs/migration/ambiguity-resolutions.md and
is settled NOWHERE in this file, because rule R-6 gives that decision to the
compiled program and to nothing else.

What that means concretely for this module, and it is a short list of
prohibitions:

    * no RECORD_LENGTH, RECORD_SIZE or BYTE_LENGTH constant is declared, at
      any scope. A constant would be an answer, and there is no answer yet;
    * no padding byte is added to make the sum 256;
    * neither FILLER is dropped to make the sum 256. Both are declared,
      because dropping either would silently change the very length the open
      question is about.

Anyone needing a width can compute it from the dictionary's own descriptors
rather than from a figure this file asserts. The recipe is exact: sum
`byte_length` over the NON-GROUP members of `IrsSystemParams.FIELDS` - 21 of
the 23, since a group item has no width of its own and raises if asked for one
- then add the sum over `VatRates.FIELDS`, and add nothing at all for
`VatGroup.FIELDS`, which redefines those same twelve bytes. That comes to 257,
derived, attributed, and visibly this migration's arithmetic.

ANOMALY - EIGHT BYTE-OFFSET COMMENTS ARE EACH ONE BYTE SHORT
------------------------------------------------------------
Every offset comment from L16 to L29 agrees with the computed running end
offset. Every offset comment from L33 to L40 is exactly one lower: 191 for
192, 209 for 210, 210 for 211, 215 for 216, 247 for 248, 248 for 249, 255 for
256 and 256 for 257.

The cause is visible in the source. `pass-value pic 9.` was inserted at L32
without a byte-offset comment of its own and without renumbering the eight
comments below it, so its one byte is missing from every figure that follows.
The `vat-group redefines vat-rates` at L30-L31 is not the cause: a REDEFINES
occupies no additional storage, and the offsets on either side of it (190 at
L29, and the run resuming at L33) are consistent with that.

Also a NEW anomaly, also for docs/migration/anomaly-log.md with this module as
its recording site. Every one of the eight comments is reproduced verbatim at
its field below, wrong figure included, because rule R-4 is explicit: "A
defect reproduced is correct; a defect fixed is a failure." The computed
figures live in the table above and in the labelled column of each field
comment, never overwriting the copybook's own.

ANOMALY - THE 01-NAME IS LOWER CASE, AND IT COLLIDES HEAD-ON
------------------------------------------------------------
The record is declared `01  system-record.` [copybooks/irswssystem.cob:L13],
all lower case. copybooks/wssystem.cob declares `System-Record` in mixed
case. COBOL folds case, so these are THE SAME IDENTIFIER, and any program
copying both books has a genuine collision on its hands.

The lower-case spelling is preserved verbatim in the descriptor's own `name`,
which comes from the dictionary rather than from this file, and it is quoted
verbatim here. It is not title-cased anywhere.

irs030 resolves the collision at the point of copy
[irs/irs030.cbl:L416-L417]:

    L416   copy "irswssystem.cob"   *> IRS param record
    L417                replacing system-record  by IRS-System-Params.
           *> (01 level)

The plan's citation for this copy needed correction: it is at L416-L417, not
L415-L416. The class name `IrsSystemParams` comes from that caller-side
`replacing` name, exactly as records/irs_nominal.py and records/irs_dflt.py
take theirs from [irs/irs030.cbl:L286] and [irs/irs030.cbl:L287].

THE 29-IDENTIFIER REPLACING CLAUSE - ANOMALY 21 AT ITS LARGEST
--------------------------------------------------------------
Registered anomaly 21 is "Field-name collisions across three posting
copybooks force qualified references", cited at [general/gl070.cbl:L510].
That citation also needed correction: L510 is `write pre-trans-record.`, which
is unqualified. The real posting-copybook qualification sites are

    [general/gl070.cbl:L497]   move post-code in WS-Posting-Record to pre-code
    [general/gl070.cbl:L521]   if vat-ac of WS-Posting-Record = zero
    [general/gl070.cbl:L525]   move vat-ac of WS-Posting-Record to pre-ac

But the largest collision in the whole in-scope set is the one THIS record
causes. Immediately after copying this copybook, irs030 copies
copybooks/wssystem.cob [irs/irs030.cbl:L419] under a `replacing` clause
spanning [irs/irs030.cbl:L420-L448] that renames TWENTY-NINE identifiers -
counted, one per line, L420 through L448. Reproduced in full so that
docs/migration/traceability.md can lift it as the definitive collision
register:

    L420   System-Record      -> WS-System-Record
    L421   Run-Date           -> ACAS-Run-Date      *> these 3 are in binary
    L422   Start-Date         -> ACAS-Start-Date    *> IRS expects as x(8)
    L423   End-Date           -> ACAS-End-Date      *>  dd/mm/yy
    L424   suser              -> ACAS-suser
    L425   Address-1          -> ACAS-Address-1
    L426   Address-2          -> ACAS-Address-2
    L427   Address-3          -> ACAS-Address-3
    L428   Address-4          -> ACAS-Address-4
    L429   Post-Code          -> ACAS-Post-Code
    L430   Print-Spool-Name   -> ACAS-Print-Spool-Name
    L431   Pass-Value         -> ACAS-Pass-Value
    L432   Pass-Word          -> ACAS-Pass-Word
    L433   OP-System          -> ACAS-Op-System
    L434   Vat                -> VatCode
    L435   Client             -> IRS-Client
    L436   System-Ops         -> IRS-System-Ops
    L437   Next-Post          -> IRS-Next-Post
    L438   Vat-Rates2         -> IRS-Vat-Rates2
    L439   Vat1               -> IRS-Vat1
    L440   Vat2               -> IRS-Vat2
    L441   Vat3               -> IRS-Vat3
    L442   Vat-Group          -> IRS-Vat-Group
    L443   Vat-Psent          -> IRS-Vat-Psent
    L444   Save-Sequ          -> IRS-Save-Sequ
    L445   System-Work-Group  -> IRS-System-Work-Group
    L446   PL-App-Created     -> IRS-PL-App-Created
    L447   PL-Approp-AC       -> IRS-PL-Approp-AC
    L448   1st-Time-Flag      -> IRS-First-Time-Flag

Two facts about that list are easy to miss and both are recorded.

The DIRECTION of the rename is the reverse of what one would expect. It is
the General Ledger record that gets renamed away, because THIS record was
copied first, at L416, and so claimed the plain names. That single ordering
fact explains why the General Ledger system record is called
`WS-System-Record` inside irs030 while it is `System-Record` everywhere else
in the codebase.

The list is also BROADER than the strict collision set. `Post-Code`,
`OP-System` and `Vat1` are renamed even though this copybook declares no field
of any of those names - defensive over-renaming, and evidence that the
maintainer could not track the collisions precisely. That imprecision is
itself the point of anomaly 21, so it is recorded rather than tidied.

None of those renamed names appears as an attribute name in this module. The
`ACAS-` and `IRS-` prefixes belong to the OTHER record's view inside irs030,
and this module models this record's own names only. records/system_record.py
is not imported here, not merged with this file and shares no descriptor with
it.

THREE DATES THAT ARE TEXT HERE AND BINARY IN THE GENERAL LEDGER RECORD
----------------------------------------------------------------------
`run-date` [:L14], `start-date` [:L21] and `end-date` [:L22] are each
`pic x(8)` - eight characters of TEXT. The General Ledger system record
declares the same two concepts as binary: `Run-Date binary-long`
[copybooks/wssystem.cob:L67] and `Start-Date binary-long`
[copybooks/wssystem.cob:L68].

The maintainer documents the mismatch himself, in the rename clause above
[irs/irs030.cbl:L421-L423]:

    "these 3 are in binary"       against the wssystem names
    "IRS expects as x(8)"
    " dd/mm/yy"

So these three are `str` of width 8 holding DD/MM/YY two-digit-year text.
They are not parsed, not converted, not validated and not widened to ten
characters anywhere in this file. acas_posting/dates.py owns every date
conversion in this migration and acas_posting/clock.py owns the pinned
observables; neither is imported here.

One point deserves stating outright, because it is the determinism gate this
file turns on. Section 0.1.1 records that the controlled clock pins exactly
two observables - "the text date `to-day pic x(10)` in DD/MM/CCYY form, and
the binary `Run-Date` [copybooks/wssystem.cob:L67]" - and that "the IRS
program ... takes neither the calling-data block nor the run date". This
record's `run-date` is therefore NEITHER of the two pinned observables: it
arrives inside the parameter block, from the caller, already set. Nothing in
this module reads a clock to fill it, and nothing may.

Section 0.6.6 also requires the harness dump-comparison step to bring "the
two-digit versus four-digit date text forms that the schema stores side by
side" into one shape before two dumps are compared. This record supplies three
of the two-digit forms. That harness step owns the work; this file only
records where the forms come from.

THE VAT RATES - THREE DISPLAY HERE, FIVE COMP IN THE OTHER RECORD
-----------------------------------------------------------------
`03 vat-rates.` [:L26] carries NO usage clause, so its three children `vat`,
`vat2` and `vat3` [:L27-L29] are zoned DISPLAY: unsigned, four digits, scale
two, and therefore `Decimal`.

The comparison with copybooks/wssystem.cob is deliberate and must not be
smoothed over. There, `05  Vat-Rates                    comp.`
[copybooks/wssystem.cob:L55] puts the usage on the GROUP HEADER, so its five
`07`-level children `Vat-Rate-1` through `Vat-Rate-5`
[copybooks/wssystem.cob:L56-L60] - each also `pic 99v99` - INHERIT COMP. Two
near-identical VAT rate groups, differing in arity (three against five) and
in storage class (DISPLAY against COMP). The generated dictionary records the
difference exactly, and it is visible in the descriptors:

    system-record.vat        usage DISPLAY  usage_declared_at DEFAULT
                             usage_inherited_from None
    SYSTEM-REC.VAT-RATE-1    usage COMP     usage_declared_at GROUP
                             usage_inherited_from Vat-Rates

Nothing is harmonised. Getting that direction wrong in either module would
change every stored VAT rate, which is why the metadata is looked up rather
than typed.

The maintainer's inline rate annotations are preserved verbatim at their
fields: "Standard" on `vat` [:L27], "reduced 1 [not yet used]" on `vat2`
[:L28] and "reduced 2 [not yet used]" on `vat3` [:L29]. The "not yet used"
notes are recorded and NOT acted on - all three rates are declared, because
the copybook declares all three.

`03 vat-group redefines vat-rates.` [:L30] with `05 vat-psent pic 99v99
occurs 3.` [:L31] is the ARRAY VIEW over the same twelve bytes. It is modelled
as its own dataclass holding a fixed-length tuple of three `Decimal`s, the way
the other REDEFINES array views in this folder are modelled. There is no
`Union`, no tagged variant, no property that switches views and no "primary"
designation, because the two views are simultaneous in COBOL and neither is
privileged. COBOL `OCCURS` subscripts are ONE-BASED, so `vat-psent (1)` is
`vat_psent[0]`; no accessor is provided that hides the offset, because hiding
it would be a behaviour this migration invented.

THREE MORE SOURCE ODDITIES, PRESERVED VERBATIM
----------------------------------------------
`03  system-ops` at [:L23] is indented ONE SPACE further than every other
`03` in the record - six leading spaces against five - and its picture column
sits one column earlier as a result. It is the only line in the copybook with
that indentation. Cosmetic to the compiler, and a fact of the source, so it is
recorded at the field rather than tidied away.

`First-Time-FLag` at [:L38] carries the maintainer's capital-L typo: `FLag`,
not `Flag`. It is preserved verbatim in the dictionary key
`system-record.First-Time-FLag`, in the descriptor's `name` and in the field
comment. FOUR spellings of this one concept coexist in the frozen tree, and
none is harmonised:

    First-Time-FLag        here                 [copybooks/irswssystem.cob:L38]
    1st-Time-Flag          General Ledger       [copybooks/wssystem.cob:L326]
    IRS-First-Time-Flag    the rename           [irs/irs030.cbl:L448]
    First-Time-Flag        wssystem's own comment on L326, which reads "(was
                           First-Time-Flag in IRS system file)" - and so
                           mis-quotes this copybook's own spelling in the act
                           of citing it

FOUR storage-bearing fields carry no byte-offset comment at all, not two.
The plan named `address-2` at [:L18] and `pass-value` at [:L32] as "the only
two", and that needed correction: `run-date` at [:L14] and `suser` at [:L15]
have none either - the copybook's offset comments simply do not begin until
`client` at [:L16], which is the first one it writes. Counted from the source:

    L14   run-date            no offset comment
    L15   suser               no offset comment
    L18   address-2           no offset comment
    L32   pass-value          no offset comment

Three further lines also carry none - `vat-rates` at [:L26], `vat-group` at
[:L30] and `vat-psent` at [:L31] - but those are the two group headers and the
array item that redefines the first group's bytes, so they are not omissions of
the same kind: a group has no offset of its own to state. Seven lines in
L14-L40 therefore lack a comment, of which four are genuine absences on
storage-bearing items.

The absence is recorded at each of the four fields, and no comment is invented
for any of them.

WHAT THE IN-SCOPE POSTING PATH ACTUALLY READS FROM THIS RECORD
--------------------------------------------------------------
Only the `Ledger-Postings-Add` section of irs030 is in scope
[irs/irs030.cbl:L1569-L1733]; section 0.2.2 excludes the rest of that file.
Within those lines this record is touched at exactly one place, and it is a
read-modify-write of the posting-number allocator:

    [irs/irs030.cbl:L1670]   move     next-post to post-key.
    [irs/irs030.cbl:L1671]   add      1 to next-post.

The VAT rates reach the compiled program's arithmetic by a longer route, and
the plan's shorter description of it is refined here after checking each hop.
`VAT-Psent (b)` - this record's array view - is copied into the program's own
rate table `WS-Vat-Rate (b)` at [irs/irs030.cbl:L1471-L1473], a table whose
declaration is annotated "taken from IRS system rec."
[irs/irs030.cbl:L273-L274]. The operator's choice of rate lands in
`WS-Vat-Current` at [irs/irs030.cbl:L721], and `WS-Vat-Current` is the
multiplier in the two ROUNDED VAT computes at [irs/irs030.cbl:L1551] and
[irs/irs030.cbl:L1562-L1563] - two of only five ROUNDED sites in the entire
in-scope cycle. Worth being precise about: those two computes are performed
only from [irs/irs030.cbl:L917] and [irs/irs030.cbl:L920], on the interactive
entry path, which is OUTSIDE the in-scope section; the transfer records the
in-scope section walks already carry their VAT amounts. The rates in this
record are nonetheless the ultimate inputs to those figures, which is why a
binary floating-point value here would corrupt exactly what
tests/arithmetic/test_compute_rounded_half_up.py exists to lock.

Note also, and reproduce nothing of it here, that the superseded commented-out
variants of both computes survive beside the live ones at
[irs/irs030.cbl:L1550] and [irs/irs030.cbl:L1561], naming the bare `vat` -
this record's L27 field - where the live code names `WS-Vat-Current`. That is
registered anomaly 19, and it belongs to
acas_posting/programs/irs030_posting.py rather than to a record layout. No VAT
arithmetic is implemented in this file.

Everything else this record carries is consumed outside the in-scope section:
`client`, `run-date`, `start-date` and `end-date` appear in irs030's SCREEN
SECTION items [irs/irs030.cbl:L460-L492], which section 0.3.4 removes rather
than reimplements, and `pass-word` survives only in a commented-out test
[irs/irs030.cbl:L1529]. The fields are all declared regardless: R-3 requires
the layout to mirror the copybook, not the subset one section happens to read.

WHAT IS NOT IN THIS RECORD
--------------------------
There are NO `88`-level condition names anywhere in this copybook -
`grep -c ' 88 '` returns 0 - so none is declared here. That absence is worth
naming for two fields in particular: `system-ops` and `First-Time-FLag` are
switches by nature, and the General Ledger record gives its analogous
switches condition names [copybooks/wssystem.cob:L179-L181], but this copybook
gives these two none. No predicate, no enum and no boolean property is
invented for them.

There is also no COMP, no COMP-3, no `binary-*` and no sign clause anywhere in
this record: every item is zoned DISPLAY or alphanumeric. A precise grep for
usage tokens across the file returns nothing. One caveat for whoever repeats
the check: the naive `grep -ci 'comp\\|binary\\|sign'` returns 1, not 0, and
the single match is the word "Incomplete" in the boxed header at L4 - a
comment, not a declaration. That is a genuine contrast with the General Ledger
system record, which is dense with COMP and `binary-*`.

REGISTERS THIS MODULE FEEDS
---------------------------
    docs/migration/anomaly-log.md
        two NEW entries, neither among the twenty-two of section 0.6.7, with
        this module as the recording site: the 256-against-257 declared-length
        contradiction, and the eight byte-offset comments left one byte short
        by the insertion of `pass-value`. Plus this module's share of
        registered anomaly 21, the 29-identifier replacing clause, whose
        collision register is reproduced above in full.
    docs/migration/ambiguity-resolutions.md
        one open question: whether the declared 256 bytes or the 257-byte
        field sum governs the record actually read, and what that does to the
        alignment of the eight trailing fields. Arbitrated by the compiled
        program under rule R-6, and by nothing in this file.
    docs/migration/traceability.md
        the 29-entry collision register, the copybook's own offsets beside
        this migration's computed offsets, the three linkage shapes and the
        four-size header history, all lifted from this docstring. Plus the
        three corrections below, each found by checking a citation against
        the frozen source rather than trusting it:

            the copy of this copybook is at [irs/irs030.cbl:L416-L417],
            not at L415-L416                                  (see above)

            registered anomaly 21's cited site [general/gl070.cbl:L510] is
            an unqualified `write pre-trans-record.`; the real qualified
            posting-copybook references are at [general/gl070.cbl:L497],
            [general/gl070.cbl:L521] and [general/gl070.cbl:L525]

            the fields with no byte-offset comment are FOUR, not two:
            [:L14], [:L15], [:L18] and [:L32]. The plan named only the last
            two, and the first two are absences of exactly the same kind

LAYERING - THIS IS A LEAF MODULE
--------------------------------
Section 0.4.3 grants records/*.py exactly two internal imports, for a stated
reason: "this keeps the record layer a leaf". This module needs only one of
them, `acas_posting.cobol.field`, plus the standard library. Provenance is
surfaced through `FieldDescriptor.cite()` and `FieldDescriptor.drift()`, which
delegate to `acas_posting.dictionary.loader` rather than reimplementing it, so
the loader is reached without a second import here and nothing is duplicated.

Not imported, and each for a reason worth naming because several are live
temptations: `programs` - irs030_posting.py takes this record as parameter #1,
which makes it the caller, not a dependency; `cli` - irs_post.py and args.py
bind this block to argv, and that is their job; `clock` - this record carries
three date fields and must read no clock, which is the single most important
gate in this file; `dates` - three `x(8)` date texts sit here that must not be
parsed; and every other `records` module, above all records/system_record.py,
for the collision reasons set out above. Also absent: `dal`, `workfiles`,
`cobol.arithmetic`, `cobol.move`, `cobol.picture`, `cobol.usage`,
`cobol.condition_names`, `cobol.sortverb`, `dictionary.generate` and the
compiled oracle in its sibling tree.

Section 0.4.3 gives the consequence that makes this worth enforcing: "the
arithmetic suite imports only cobol and records and touches no database, so it
runs anywhere".

TYPE DISCIPLINE (R-2) AND DETERMINISM (R-6)
-------------------------------------------
Rule R-2 forbids binary floating point outright - "not in computation, not in
storage, not in transport". The three VAT rates and the three-element array
view are `decimal.Decimal` at scale 2, defaulting to `Decimal("0.00")` and
never to a binary floating-point literal. Every other numeric item here is an
unsigned zoned DISPLAY integer and is carried as `int`. No binary
floating-point type, literal or conversion appears anywhere in this file.

Rule R-6 and section 0.1.1 - "Every one of the in-scope posting programs
contains zero clock reads; the date arrives purely through linkage" - give
this file its determinism obligations. There is no wall-clock read, no import
of any clock or date module, no non-deterministic value source, no unique-id
generation, no environment, host or user inspection, and no date formatting or
parsing. Member order is copybook declaration order. `FIELDS` and the array
view are tuples rather than lists. Nothing is read when this module is
imported beyond the dictionary loader's own lazy, cached read of the
generated artifact.

THE SHAPE OF THIS MODULE
------------------------
    _SYSTEM_RECORD .. _FILLER_40   28 module-private descriptors, one per
                                   copybook line from L13 to L40, each looked
                                   up by its dictionary key and each carrying
                                   the copybook's own offset comment verbatim
                                   beside this migration's computed figure
    VatRates                       03 vat-rates            [:L26]
    VatGroup                       03 vat-group redefines  [:L30]
    IrsSystemParams                01 system-record        [:L13]

Each class exposes two class-level constants and neither is a dataclass field:
`GROUP`, the descriptor of the class's own group item - which is where the
REDEFINES relationship comes from, derived from the dictionary rather than
asserted here - and `FIELDS`, its members' descriptors in declaration order.
Between them the three classes cite all 28 dictionary entries.

The two trailing FILLERs are named `filler_39` and `filler_40`. The scheme is
the copybook line number, chosen because it is the dictionary's own
disambiguator: the entries are keyed `system-record.filler#39` and
`system-record.filler#40`, so the Python name follows the key mechanically
rather than by invention. Their COBOL name is `filler` in both cases, and both
descriptors report `is_filler` true. They are NOT the same type: L39 is
`pic 9(7)` and numeric, L40 is `pic x` and alphanumeric.

None of the three classes is frozen. The block is linkage: the caller fills it
in before the CALL, so it has to be mutable. There is no post-initialisation
hook, no validation and no padding, quantising or coercion of any kind - a
record layout describes storage, and the store direction belongs to
acas_posting/cobol/arithmetic.py and acas_posting/cobol/move.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

# Sorted, as the three names of this module's public surface. Written as a
# tuple rather than a list because rule R-6 asks for tuples throughout this
# file and because every other module of this package spells `__all__` the
# same way; `list(__all__)` is the three names in this order.
__all__: Final[tuple[str, ...]] = (
    "IrsSystemParams",
    "VatGroup",
    "VatRates",
)


# =============================================================================
#  THE DICTIONARY KEYS  (rule R-5; section 0.8.1's "Data dictionary first")
#
#  The key form for this record was established by the probe recorded in the
#  module docstring: <COPYBOOK-RECORD>.<FIELD-NAME>, with the record half in
#  this copybook's own lower case and the two FILLERs disambiguated by the
#  dictionary's own '#' convention. Lookups are exact and fold no case, which
#  is what keeps `system-record.` from ever reaching the General Ledger
#  record's mixed-case `System-Record.` keys - the guard this record needs
#  because the two share an 01-name. The loader's table-keyed accessor has no
#  meaning for a record with no table and is not called anywhere in this file.
#
#  `_desc` is `FieldDescriptor.from_dictionary_key`, the constructor the field
#  module publishes for dictionary-backed descriptors, under a shorter local
#  name: the same function, memoised on its key, not a
#  reimplementation of it. It reads each entry's COPYBOOK view for digits,
#  scale, sign and usage, and sets both `dictionary_key` and `source_locator`,
#  so every descriptor below satisfies rule R-5's provenance invariant by
#  construction and none of this metadata is transcribed by eye. Nothing is
#  read until the first call, and the loader reads the generated artifact
#  lazily and once.
# =============================================================================

_desc: Final = FieldDescriptor.from_dictionary_key

# -- the 01-level group -------------------------------------------------------
_SYSTEM_RECORD: Final = _desc("system-record.system-record")       # L13

# -- the 03-level and 05-level items, in declaration order --------------------
_RUN_DATE: Final = _desc("system-record.run-date")                 # L14
_SUSER: Final = _desc("system-record.suser")                       # L15
_CLIENT: Final = _desc("system-record.client")                     # L16
_ADDRESS_1: Final = _desc("system-record.address-1")               # L17
_ADDRESS_2: Final = _desc("system-record.address-2")               # L18
_ADDRESS_3: Final = _desc("system-record.address-3")               # L19
_ADDRESS_4: Final = _desc("system-record.address-4")               # L20
_START_DATE: Final = _desc("system-record.start-date")             # L21
_END_DATE: Final = _desc("system-record.end-date")                 # L22
_SYSTEM_OPS: Final = _desc("system-record.system-ops")             # L23
_PASS_WORD: Final = _desc("system-record.pass-word")               # L24
_NEXT_POST: Final = _desc("system-record.next-post")               # L25
_VAT_RATES: Final = _desc("system-record.vat-rates")               # L26 group
_VAT: Final = _desc("system-record.vat")                           # L27
_VAT2: Final = _desc("system-record.vat2")                         # L28
_VAT3: Final = _desc("system-record.vat3")                         # L29
_VAT_GROUP: Final = _desc("system-record.vat-group")               # L30 group
_VAT_PSENT: Final = _desc("system-record.vat-psent")               # L31
_PASS_VALUE: Final = _desc("system-record.pass-value")             # L32
_SAVE_SEQU: Final = _desc("system-record.save-sequ")               # L33
_SYSTEM_WORK_GROUP: Final = _desc("system-record.system-work-group")  # L34
_PL_APP_CREATED: Final = _desc("system-record.PL-App-Created")     # L35
_PL_APPROP_AC: Final = _desc("system-record.PL-Approp-AC")         # L36
_PRINT_SPOOL_NAME: Final = _desc("system-record.Print-Spool-Name")  # L37
_FIRST_TIME_FLAG: Final = _desc("system-record.First-Time-FLag")   # L38
_FILLER_39: Final = _desc("system-record.filler#39")               # L39
_FILLER_40: Final = _desc("system-record.filler#40")               # L40


# =============================================================================
#  THE DEFAULT FOR AN ALPHANUMERIC MEMBER
# =============================================================================


def _spaces(descriptor: FieldDescriptor) -> str:
    """Return an alphanumeric item's declared width, in spaces.

    The default for every `PIC X(n)` member below, DERIVED from that member's
    own dictionary entry rather than written as a literal width, in the spirit
    of section 0.3.3: "Field metadata is therefore derived, not transcribed".

    Spaces rather than the empty string, and the declared width rather than
    one space, because that is what the frozen system does with an unset
    alphanumeric field. Section 0.6.2 records that each bridge load paragraph
    "begins by initialising the host-variable group, so unset fields become
    zero or space rather than SQL NULL", which is "why the Python layer must
    default rather than omit". Keeping the width also leaves this record's byte
    layout - the subject of the open length question - visible in a bare
    instance. The same reasoning gives the numeric members a default of 0 and
    the VAT rates a default of `Decimal("0.00")`.

    A group item carries no character length and would yield the empty string;
    no group is defaulted this way below. This runs once per member while the
    classes are being defined and never on a data value, so it validates
    nothing and coerces nothing (rule R-3).

    Args:
        descriptor: The member's descriptor, from the generated dictionary.

    Returns:
        The member's declared width as a run of spaces.
    """
    return " " * (descriptor.character_length or 0)


# =============================================================================
#  03  vat-rates.                                 [copybooks/irswssystem.cob]
# =============================================================================


@dataclass(slots=True)
class VatRates:
    """The three VAT rates - `03 vat-rates.` [copybooks/irswssystem.cob:L26].

    Which VAT rate group this is matters, because the frozen tree holds two
    that are easy to confuse. This one belongs to copybooks/irswssystem.cob,
    has an arity of THREE, and its children are zoned DISPLAY because the
    group header at L26 carries no usage clause at all. The other one belongs
    to copybooks/wssystem.cob, is modelled inside records/system_record.py,
    has an arity of FIVE, and its children inherit COMP from a group header
    that does carry the usage: `05  Vat-Rates                    comp.`
    [copybooks/wssystem.cob:L55], over `07`-level children `Vat-Rate-1`
    through `Vat-Rate-5` [copybooks/wssystem.cob:L56-L60].

    The class keeps the copybook's own group name, `VatRates`, because that is
    what this copybook calls it; Python module namespaces keep the two apart,
    and neither is renamed to make the distinction for the reader. The
    difference shows in the descriptors themselves rather than in prose:
    `usage_declared_at` is DEFAULT here and GROUP there, with
    `usage_inherited_from` None here and `Vat-Rates` there. Nothing is
    harmonised - getting that direction wrong in either module would change
    every stored VAT rate.

    Each rate is four digits at scale two, unsigned, and carried as
    `decimal.Decimal` (rule R-2). The maintainer's own annotations are quoted
    at their fields, "not yet used" included; all three rates are declared
    because the copybook declares all three.

    No arithmetic is performed here. These rates are the ultimate inputs to
    the two ROUNDED VAT computes at [irs/irs030.cbl:L1551] and
    [irs/irs030.cbl:L1562-L1563], reached by way of the program's own rate
    table [irs/irs030.cbl:L1471-L1473] and `WS-Vat-Current`
    [irs/irs030.cbl:L721]; those computes belong to
    acas_posting/programs/irs030_posting.py.
    """

    #: The group item this class models, from the generated dictionary.
    GROUP: ClassVar[FieldDescriptor] = _VAT_RATES
    #: Its members' descriptors, in copybook declaration order (rule R-6).
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_VAT, _VAT2, _VAT3)

    # 05  vat   pic 99v99.   *> 182   *> Standard   <- the copybook's own two
    #   computed running end offset 182  |  [copybooks/irswssystem.cob:L27]
    #   The bare name `vat` is also what the superseded commented-out VAT
    #   compute at [irs/irs030.cbl:L1550] still refers to (anomaly 19).
    vat: Decimal = Decimal("0.00")

    # 05  vat2  pic 99v99.   *> 186   *> reduced 1 [not yet used]
    #   computed running end offset 186  |  [copybooks/irswssystem.cob:L28]
    vat2: Decimal = Decimal("0.00")

    # 05  vat3  pic 99v99.   *> 190   *> reduced 2 [not yet used]
    #   computed running end offset 190  |  [copybooks/irswssystem.cob:L29]
    vat3: Decimal = Decimal("0.00")


# =============================================================================
#  03  vat-group redefines vat-rates.              [copybooks/irswssystem.cob]
# =============================================================================


@dataclass(slots=True)
class VatGroup:
    """The array view over the rates - `03 vat-group redefines vat-rates.`.

    Declared at [copybooks/irswssystem.cob:L30-L31] as a REDEFINES of
    `vat-rates`, giving the same twelve bytes a second, subscripted shape:
    `05  vat-psent      pic 99v99    occurs 3.`

    The REDEFINES relationship is not asserted here - it is carried by the
    group's own descriptor, whose `redefines` member reads `vat-rates`
    straight from the generated dictionary. Both views are simultaneous in
    COBOL and neither is privileged, so there is no `Union`, no tagged
    variant, no property that switches between them and no "primary"
    designation. A caller that means the subscripted view uses this class; one
    that means the three named rates uses `VatRates`.

    COBOL `OCCURS` subscripts are ONE-BASED: `vat-psent (1)` is
    `vat_psent[0]`, `vat-psent (3)` is `vat_psent[2]`. No accessor is provided
    that hides that offset, because hiding it would be a behaviour this
    migration invented rather than one it reproduces. The frozen program reads
    the view exactly that way, one-based, at [irs/irs030.cbl:L1471-L1473].

    A fixed-length tuple of three `decimal.Decimal`s, at scale two: a tuple
    rather than a list because the arity is fixed at three by the copybook and
    because rule R-6 asks for tuples here.
    """

    #: The group item this class models, from the generated dictionary. Its
    #: `redefines` member is where the REDEFINES fact comes from.
    GROUP: ClassVar[FieldDescriptor] = _VAT_GROUP
    #: Its one member's descriptor, which carries `occurs` = 3.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_VAT_PSENT,)

    # 05  vat-psent  pic 99v99  occurs 3.    <- no offset comment on this line
    #   computed running end offset 190, over the same bytes as vat/vat2/vat3
    #   |  [copybooks/irswssystem.cob:L31]
    vat_psent: tuple[Decimal, Decimal, Decimal] = (
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    )


# =============================================================================
#  01  system-record.                              [copybooks/irswssystem.cob]
#      renamed by the caller to IRS-System-Params  [irs/irs030.cbl:L416-L417]
# =============================================================================


@dataclass(slots=True)
class IrsSystemParams:
    """IRS system parameters - parameter #1 of the IRS linkage shape.

    TWO COBOL identifiers name this one record, and both are quoted verbatim
    because the pair is the whole reason this class is not called
    `SystemRecord`:

        `01  system-record.`            [copybooks/irswssystem.cob:L13]
        `replacing system-record  by IRS-System-Params.`
                                        [irs/irs030.cbl:L416-L417]

    The declaration is all LOWER CASE in the frozen copybook, and it is left
    that way in the descriptor's `name`, which comes from the dictionary. It is
    not title-cased. Because COBOL folds case, that name is the same
    identifier as copybooks/wssystem.cob's mixed-case `System-Record`, so the
    two records genuinely collide, and the class name follows the caller-side
    `replacing` name to keep the two apart in Python.

    The direction of that resolution is the reverse of what one would expect,
    and it is worth carrying: irs030 copies THIS record first, at L416, so it
    keeps the plain names, and it is the General Ledger record - copied second
    at L419 - that gets renamed away, under a `replacing` clause of
    twenty-nine identifiers at [irs/irs030.cbl:L420-L448]. That single
    ordering fact is why the General Ledger system record is called
    `WS-System-Record` inside irs030 and `System-Record` everywhere else. The
    full collision register is in this module's docstring.

    This class models the copybook's own names only. No `ACAS-` or `IRS-`
    prefixed name from that rename clause appears as an attribute here: those
    prefixes belong to the other record's view inside irs030, which
    records/system_record.py models and which this module does not import,
    merge with, or share a descriptor with.

    THE MEMBER SET, and why it counts as it does. 23 dataclass fields: 19
    scalar items, the 2 group members `vat_rates` and `vat_group`, and the 2
    trailing FILLERs. With `VatRates`'s 3 and `VatGroup`'s 1 that is 27 Python
    members for the copybook's 27 subordinate items, one for one, and the
    01-level group is this class itself - the 28th dictionary entry, cited as
    `GROUP`. Nothing is added and nothing is dropped (rule R-3).

    The order is copybook declaration order, L14 through L40, so this class
    can be set beside `cat -n copybooks/irswssystem.cob` and diffed by eye.

    NOT FROZEN, deliberately: this is a linkage parameter block that the caller
    fills in before the CALL. There is no post-initialisation hook, no
    validation and no padding, quantising or coercion - the store direction
    belongs to acas_posting/cobol/arithmetic.py and
    acas_posting/cobol/move.py, and adding a check here would be exactly the
    added validation rule R-3 forbids.

    NO CONDITION NAMES, because the copybook declares none - `grep -c ' 88 '`
    over it returns 0. That absence is deliberate for `system_ops` and
    `first_time_flag` in particular, which are switches by nature and whose
    General Ledger analogues do have condition names
    [copybooks/wssystem.cob:L179-L181]. None is invented for them here.

    NO LENGTH CONSTANT. The copybook's header claims 256 bytes at L7 and L10
    while its field widths sum to 257, and rule R-6 leaves that contradiction
    for the compiled program to settle. A width can still be derived from the
    dictionary's own descriptors - sum `byte_length` over the non-group members
    of `FIELDS`, add the sum over `VatRates.FIELDS`, add nothing for
    `VatGroup.FIELDS` - and it comes to 257. This class asserts no figure of
    its own, declares no length constant, adds no padding byte and drops
    neither FILLER.
    """

    #: The 01-level group item this class models, from the dictionary.
    GROUP: ClassVar[FieldDescriptor] = _SYSTEM_RECORD
    #: Its members' descriptors, in copybook declaration order L14 -> L40
    #: (rule R-6). 23 of them: 19 scalars, 2 groups and 2 FILLERs.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _RUN_DATE,
        _SUSER,
        _CLIENT,
        _ADDRESS_1,
        _ADDRESS_2,
        _ADDRESS_3,
        _ADDRESS_4,
        _START_DATE,
        _END_DATE,
        _SYSTEM_OPS,
        _PASS_WORD,
        _NEXT_POST,
        _VAT_RATES,
        _VAT_GROUP,
        _PASS_VALUE,
        _SAVE_SEQU,
        _SYSTEM_WORK_GROUP,
        _PL_APP_CREATED,
        _PL_APPROP_AC,
        _PRINT_SPOOL_NAME,
        _FIRST_TIME_FLAG,
        _FILLER_39,
        _FILLER_40,
    )

    # 03  run-date  pic x(8).    <- the FIRST of the four storage-bearing
    #   fields for which the copybook writes NO offset comment at all
    #   computed running end offset 8  |  [copybooks/irswssystem.cob:L14]
    #   TEXT, not binary: `binary-long` in the General Ledger record
    #   [copybooks/wssystem.cob:L67], and irs030 says so itself against that
    #   name - "these 3 are in binary" [irs/irs030.cbl:L421], "IRS expects as
    #   x(8)" [irs/irs030.cbl:L422], " dd/mm/yy" [irs/irs030.cbl:L423]. Eight
    #   characters of DD/MM/YY, neither parsed nor widened here, and NOT one
    #   of the two observables the controlled clock pins: it arrives inside
    #   this parameter block, already set by the caller.
    run_date: str = _spaces(_RUN_DATE)

    # 03  suser  pic x(24).      <- the SECOND of the four fields with no
    #   offset comment; the copybook's own numbering starts at `client`, L16
    #   computed running end offset 32  |  [copybooks/irswssystem.cob:L15]
    suser: str = _spaces(_SUSER)

    # 03  client  pic x(24).  *> 56           <- the copybook's own comment
    #   computed running end offset 56  |  [copybooks/irswssystem.cob:L16]
    client: str = _spaces(_CLIENT)

    # 03  address-1  pic x(24).  *> 80        <- the copybook's own comment
    #   computed running end offset 80  |  [copybooks/irswssystem.cob:L17]
    address_1: str = _spaces(_ADDRESS_1)

    # 03  address-2  pic x(24).   <- the third of the FOUR storage-bearing
    #   fields the copybook leaves without an offset comment, after L14 and
    #   L15; the absence is recorded, none is invented
    #   computed running end offset 104  |  [copybooks/irswssystem.cob:L18]
    address_2: str = _spaces(_ADDRESS_2)

    # 03  address-3  pic x(24).  *> 128       <- the copybook's own comment
    #   computed running end offset 128  |  [copybooks/irswssystem.cob:L19]
    address_3: str = _spaces(_ADDRESS_3)

    # 03  address-4  pic x(24).  *> 152       <- the copybook's own comment
    #   computed running end offset 152  |  [copybooks/irswssystem.cob:L20]
    address_4: str = _spaces(_ADDRESS_4)

    # 03  start-date  pic x(8).  *> 160       <- the copybook's own comment
    #   computed running end offset 160  |  [copybooks/irswssystem.cob:L21]
    #   TEXT here, `Start-Date binary-long` in the General Ledger record
    #   [copybooks/wssystem.cob:L68]. Not parsed, not converted, not widened.
    start_date: str = _spaces(_START_DATE)

    # 03  end-date  pic x(8).    *> 168       <- the copybook's own comment
    #   computed running end offset 168  |  [copybooks/irswssystem.cob:L22]
    #   The third of the three x(8) date texts irs030 flags as " dd/mm/yy"
    #   [irs/irs030.cbl:L423]. The harness dump-comparison step owns the
    #   two-digit versus four-digit reconciliation section 0.6.6 calls for;
    #   this is a source of the two-digit form and does nothing about it.
    end_date: str = _spaces(_END_DATE)

    # 03  system-ops  pic x.     *> 169       <- the copybook's own comment
    #   computed running end offset 169  |  [copybooks/irswssystem.cob:L23]
    #   THE INDENTATION SLIP: this is the only line in the copybook whose 03
    #   sits one space further right than every other, six leading spaces
    #   against five, which also shifts its picture column one place left.
    #   Cosmetic to the compiler, a fact of the source, recorded not tidied.
    #   A switch with NO 88-level condition name in this copybook.
    system_ops: str = _spaces(_SYSTEM_OPS)

    # 03  pass-word  pic x(4).   *> 173       <- the copybook's own comment
    #   computed running end offset 173  |  [copybooks/irswssystem.cob:L24]
    #   Survives in irs030 only in a commented-out test
    #   [irs/irs030.cbl:L1529]; declared regardless, as R-3 requires.
    pass_word: str = _spaces(_PASS_WORD)

    # 03  next-post  pic 9(5).   *> 178       <- the copybook's own comment
    #   computed running end offset 178  |  [copybooks/irswssystem.cob:L25]
    #   The ONLY member of this record the in-scope posting section touches:
    #   [irs/irs030.cbl:L1670] `move next-post to post-key.` and
    #   [irs/irs030.cbl:L1671] `add 1 to next-post.` Unsigned zoned DISPLAY,
    #   scale 0, so `int` - the allocator is counted, never scaled.
    next_post: int = 0

    # 03  vat-rates.             <- group header, no offset comment, no usage
    #   clause, so its three children are zoned DISPLAY
    #   computed running end offset 190  |  [copybooks/irswssystem.cob:L26]
    vat_rates: VatRates = field(default_factory=VatRates)

    # 03  vat-group redefines vat-rates.      <- the array view over the SAME
    #   twelve bytes; a REDEFINES occupies no additional storage, which is why
    #   the offsets on either side of it are consistent
    #   computed running end offset 190  |  [copybooks/irswssystem.cob:L30]
    vat_group: VatGroup = field(default_factory=VatGroup)

    # 03  pass-value  pic 9.      <- the last of the FOUR fields with no
    #   offset comment, and the cause of the eight that follow being one byte
    #   short, unlike L14/L15/L18 which cause nothing: it was
    #   inserted here without a comment of its own and without renumbering
    #   them. The absence is recorded; no comment is invented.
    #   computed running end offset 191  |  [copybooks/irswssystem.cob:L32]
    pass_value: int = 0

    # 03  save-sequ  pic 9.      *> 191       <- the copybook's own comment,
    #   REPRODUCED AS WRITTEN and one byte short: this migration computes the
    #   running end offset as 192. Neither figure corrects the other (R-4).
    #   |  [copybooks/irswssystem.cob:L33]
    save_sequ: int = 0

    # 03  system-work-group  pic x(18).  *> 209   <- the copybook's own
    #   comment, reproduced as written and one byte short; computed 210
    #   |  [copybooks/irswssystem.cob:L34]
    system_work_group: str = _spaces(_SYSTEM_WORK_GROUP)

    # 03  PL-App-Created  pic x.  *> 210      <- the copybook's own comment,
    #   reproduced as written and one byte short; computed 211
    #   |  [copybooks/irswssystem.cob:L35]
    pl_app_created: str = _spaces(_PL_APP_CREATED)

    # 03  PL-Approp-AC  pic 9(5).  *> 215     <- the copybook's own comment,
    #   reproduced as written and one byte short; computed 216
    #   |  [copybooks/irswssystem.cob:L36]
    pl_approp_ac: int = 0

    # 03  Print-Spool-Name  pic x(32).  *> 247    <- the copybook's own
    #   comment, reproduced as written and one byte short; computed 248
    #   |  [copybooks/irswssystem.cob:L37]
    #   The report spool-out path this names is out of scope: section 0.1.1
    #   excludes the `call "SYSTEM" using Print-Report` hand-off. The field is
    #   part of the layout and is declared; nothing here acts on it.
    print_spool_name: str = _spaces(_PRINT_SPOOL_NAME)

    # 03  First-Time-FLag  pic 9.  *> 248     <- the copybook's own comment,
    #   reproduced as written and one byte short; computed 249
    #   |  [copybooks/irswssystem.cob:L38]
    #   THE CAPITAL-L TYPO is the maintainer's: `FLag`, not `Flag`. Preserved
    #   verbatim in the dictionary key `system-record.First-Time-FLag` and in
    #   the descriptor's `name`. Four spellings of this one concept coexist -
    #   `1st-Time-Flag` [copybooks/wssystem.cob:L326],
    #   `IRS-First-Time-Flag` [irs/irs030.cbl:L448], and that same L326's own
    #   comment "(was First-Time-Flag in IRS system file)", which mis-quotes
    #   this copybook while citing it. None of the four is harmonised.
    #   Another switch with no 88-level condition name here.
    first_time_flag: int = 0

    # 03  filler  pic 9(7).      *> 255       <- the copybook's own comment,
    #   reproduced as written and one byte short; computed 256
    #   |  [copybooks/irswssystem.cob:L39]
    #   COBOL name `filler`; the Python name carries the copybook line because
    #   that is the dictionary's own disambiguator, `system-record.filler#39`.
    #   NUMERIC - `pic 9(7)`, so `int`, unlike its neighbour on L40. Declared
    #   because dropping it would change the record length the open question
    #   in this module's docstring is about.
    filler_39: int = 0

    # 03  filler  pic x.         *> 256       <- the copybook's own comment,
    #   reproduced as written and one byte short; computed 257 - the field sum
    #   the header's 256 contradicts
    #   |  [copybooks/irswssystem.cob:L40]
    #   COBOL name `filler`; key `system-record.filler#40`. ALPHANUMERIC -
    #   `pic x`, so `str`, deliberately not typed like L39's numeric FILLER.
    filler_40: str = _spaces(_FILLER_40)
