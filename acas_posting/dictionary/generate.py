"""Generate the machine-readable data dictionary from the frozen ACAS sources.

Reads the authoritative triple - the record copybooks under `copybooks/`, the
bridge pairs `common/*MT.scb` and `common/*MT.cbl`, and the frozen schema
`mysql/ACASDB.sql` - and emits `data_dictionary/acas_posting_dictionary.json`.

Every source is READ ONLY. The generator opens no database, runs no compiler and
writes nothing outside the artifact and its schema.

`--check` regenerates in memory and reports whether the committed artifact still
matches, which is how a change to a frozen source is noticed rather than
discovered later; a mismatch is an exit status, not a silent rewrite. A field
present in one source and absent from another is flagged rather than filled in,
because that asymmetry is a fact about the frozen system - three columns of the
IRS posting table exist only in the bridge
[common/irspostingMT.cbl:L982-L987].
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Final

from acas_posting import DATA_DICTIONARY_PATH, REPOSITORY_ROOT
from acas_posting.dictionary import model


#: The entity-to-table spine of the posting cycle, in the order the plan states it
#: (section 0.2.1.1). Each row is (entity facade, handler, bridge, tables, copybooks).
_SPINE: Final[
    tuple[tuple[str, str, str, tuple[str, ...], tuple[str, ...]], ...]
] = (
    ("System", "acas000", "systemMT", ("SYSTEM-REC",), ("copybooks/wssystem.cob",)),
    ("System defaults", "acas000", "dfltMT", ("SYSDEFLT-REC",), ("copybooks/wsdflt.cob",)),
    ("System final", "acas000", "finalMT", ("SYSFINAL-REC",), ("copybooks/wsfinal.cob",)),
    ("System totals", "acas000", "sys4MT", ("SYSTOT-REC",), ("copybooks/wssys4.cob",)),
    ("GL-Nominal", "acas005", "nominalMT", ("GLLEDGER-REC",), ("copybooks/wsledger.cob",)),
    ("GL-Posting", "acas006", "glpostingMT", ("GLPOSTING-REC",), ("copybooks/wspost.cob",)),
    ("GL-Batch", "acas007", "glbatchMT", ("GLBATCH-REC",), ("copybooks/wsbatch.cob",)),
    ("SPL-Posting", "acas008", "slpostingMT", ("PSIRSPOST-REC",),
     ("copybooks/wspost-irs.cob",)),
    ("Sales", "acas012", "salesMT", ("SALEDGER-REC",), ("copybooks/wssl.cob",)),
    ("Value", "acas013", "valueMT", ("VALUEANAL-REC",), ("copybooks/wsval.cob",)),
    ("Analysis", "acas015", "analMT", ("ANALYSIS-REC",), ("copybooks/wsanal.cob",)),
    ("Invoice", "acas016", "slinvoiceMT", ("SAINVOICE-REC", "SAINV-LINES-REC"),
     ("copybooks/slwsinv.cob", "copybooks/slwsinv2.cob")),
    ("OTM3", "acas019", "otm3MT", ("SAITM3-REC",), ("copybooks/slwsoi3.cob",)),
    ("Purch", "acas022", "purchMT", ("PULEDGER-REC",), ("copybooks/wspl.cob",)),
    ("PInvoice", "acas026", "plinvoiceMT", ("PUINVOICE-REC", "PUINV-LINES-REC"),
     ("copybooks/plwspinv.cob", "copybooks/plwspinv2.cob")),
    ("OTM5", "acas029", "otm5MT", ("PUITM5-REC",),
     ("copybooks/plwsoi5B.cob", "copybooks/plwsoi5C.cob")),
    ("IRS nominal", "acasirsub1", "irsnominalMT", ("IRSNL-REC",), ("copybooks/irswsnl.cob",)),
    ("IRS defaults", "acasirsub3", "irsdfltMT", ("IRSDFLT-REC",),
     ("copybooks/irswsdflt.cob",)),
    ("IRS posting", "acasirsub4", "irspostingMT", ("IRSPOSTING-REC",),
     ("copybooks/irswspost.cob",)),
    ("IRS final", "acasirsub5", "irsfinalMT", ("IRSFINAL-REC",),
     ("copybooks/irswsfinal.cob",)),
)

_BY_BRIDGE: Final[dict[str, tuple[str, str, tuple[str, ...], tuple[str, ...]]]] = {
    bridge: (entity, handler, tables, copybooks)
    for entity, handler, bridge, tables, copybooks in _SPINE
}
_BY_TABLE: Final[dict[str, tuple[str, str, str, tuple[str, ...]]]] = {
    table: (bridge, handler, entity, copybooks)
    for entity, handler, bridge, tables, copybooks in _SPINE
    for table in tables
}
#: The 22 in-scope tables, derived from the spine so the two can never disagree.
_IN_SCOPE_TABLES: Final[tuple[str, ...]] = tuple(sorted(_BY_TABLE))

_EXTRA_COPYBOOK_ROOTS: Final[tuple[str, ...]] = (
    "copybooks/Test-Data-Flags.cob",
    "copybooks/irswssystem.cob",
    "copybooks/wscall.cob",
    "copybooks/wsfnctn.cob",
    "copybooks/wsmaps03.cob",
    "copybooks/wsnames.cob",
)

#: Copybooks a bridge COPYs for infrastructure rather than for a record layout.
_INFRASTRUCTURE_COPYBOOKS: Final[frozenset[str]] = frozenset(
    ("acas-sqlstate-error-list.cob", "envdiv.cob", "wsfnctn.cob", "test-data-flags.cob")
)

#: The records the posting programs declare INLINE, in their own FILE and SORT SECTIONs,
#: rather than by COPY: the General Ledger work files.
_PROGRAM_SOURCE_RECORDS: Final[tuple[tuple[str, str, str, int, int], ...]] = (
    ("general/gl070.cbl", "pre-trans-record", "FD", 108, 116),
    ("general/gl071.cbl", "pre-trans-record", "FD", 112, 120),
    ("general/gl071.cbl", "post-trans-record", "FD", 124, 132),
    ("general/gl071.cbl", "sort-trans-record", "SD", 136, 144),
    ("general/gl072.cbl", "post-trans-record", "FD", 110, 119),
)

#: The sequential read that turns the sort order of these records into a correctness
#: requirement, quoted as a locator wherever the notes explain why a transient work file
#: is in a data dictionary at all. The read is guarded at L407.
_SEQUENTIAL_READ_LOCATOR: Final[str] = "general/gl072.cbl:L408"

#: The records whose field order the sorted stream depends on, and which therefore carry
#: anomaly A-14. `pre-trans-record` is deliberately absent.
_ORDERING_CRITICAL_RECORDS: Final[frozenset[str]] = frozenset(
    ("post-trans-record", "sort-trans-record")
)

_SCHEMA_REL: Final[str] = "mysql/ACASDB.sql"
_DICTIONARY_VERSION: Final[str] = "1.0.0"

#: The frozen dump declares 33 tables; 22 belong to the cycle.
_OUT_OF_SCOPE_TABLES: Final[int] = 11
_OUT_OF_SCOPE_BRIDGES: Final[int] = 8

_DETERMINISM_MEMBER_ORDER: Final[str] = (
    "Object members are emitted in the order the JSON Schema declares them in each properties "
    "block, never sorted alphabetically, so the document reads top-down in the same shape as "
    "the frozen sources it describes: identity before sources, sources before tables, tables "
    "before entries, and inside an entry the views in layer order - copybook first, then the "
    "program-source view that stands in its place for a work-file field, then bridge host "
    "variable, then column. Sorting members would produce a valid but different file and "
    "break the byte-for-byte guarantee."
)

_ARRAY_ORDER_TABLES: Final[str] = "By table name, ASCII ascending."

_ARRAY_ORDER_ENTRIES: Final[str] = (
    "Grouped by table name ASCII ascending, then by the column ordinal the frozen dump fixes "
    "within that table. The copybook-only fields of a table's own records follow its "
    "column-mapped entries in copybook declaration order, and the copybook-only fields of the "
    "in-scope copybooks that correspond to no table at all come last, by path. Where one "
    "copybook serves two tables its leftover fields belong to the first of them, ASCII "
    "ascending, so their position is decided by the data and never by traversal order. The "
    "program-source entries - the fields of the General Ledger work-file records, which "
    "belong to no table because they reach none - come last of all, by program path ASCII "
    "ascending and then by declaration line ascending."
)

_ARRAY_ORDER_BRIDGES: Final[str] = "By .scb filename, ASCII ascending."

_ARRAY_ORDER_COPYBOOKS: Final[str] = "By path, ASCII ascending."

_ARRAY_ORDER_PROGRAM_SOURCES: Final[str] = (
    "By program path ASCII ascending, then by the record's declaration line ascending. Two "
    "keys rather than one, because general/gl071.cbl declares three of these records."
)

_FORBIDDEN_CONTENT: Final[tuple[str, ...]] = (
    (
        "Timestamps and dates of generation. A date quoted from a comment in a frozen source "
        "is evidence about that source and is kept verbatim; a date describing when this "
        "document was produced would differ between two otherwise identical regenerations and "
        "appears nowhere."
    ),
    "Hostnames and usernames.",
    (
        "Absolute filesystem paths. Every path is repository-relative, and every locator is a "
        "repository-relative path followed by a line reference."
    ),
    "Git revisions, branch names and working-copy state.",
    (
        "Environment-derived tool versions. The only version recorded is the database server "
        "version the frozen dump states in its own header."
    ),
    (
        "Random, hashed or sequence-allocated identifiers. Every key is derived from the "
        "names the frozen sources themselves use."
    ),
    (
        "Any ordering that depends on filesystem traversal. Every directory listing and every "
        "mapping is sorted before it is iterated."
    ),
    (
        "Credential values. The connection block is catalogued as field layouts only; no "
        "schema name, user, password, host, socket or port value is recorded anywhere."
    ),
)

_RULE_ENTRY_KEY: Final[str] = (
    "For an entry that maps to a MySQL column the key is the table name, a full stop, and the "
    "column name exactly as the DDL spells it between backticks. For a copybook-only field it "
    "is the 01-level record name, a full stop, and the field name with the copybook's own "
    "casing. Where that would produce a key more than once - because FILLER repeats inside a "
    "record, or because two copybooks declare a record of the same name - every colliding "
    "occurrence gains # followed by its one-based declaration line, which is unique and stays "
    "traceable. The table or record name is always part of the key, which is what keeps "
    "PSIRSPOST-REC and IRSPOSTING-REC apart: they are different tables with near-identical "
    "field names and copybooks/wspost-irs.cob:L6-L7 says so outright. Entries are built in "
    "two passes and the order matters for reproducing this file exactly. The first pass walks "
    "the 22 tables in name order and, for each column in the ordinal the DDL declares it at, "
    "emits the column-mapped entry and marks the copybook field it resolved to as consumed. "
    "The second pass walks the copybooks in path order and emits every field the first pass "
    "did not consume, once per distinct record, name, level, declaration line, picture, usage "
    "and redefines target. A consequence to expect rather than correct: where two in-scope "
    "copybooks declare an identical item at an identical line - copybooks/plwsoi5B.cob and "
    "copybooks/plwsoi5C.cob are variants that differ only in whether one COPY is commented "
    "out - the two cannot both hold a key, because record, field and line are all equal and "
    "the entryKey form admits no file segment, so the first occurrence in path order is cited "
    "and the duplicate is disclosed in the copybook record notes. Where the earlier "
    "copybook's occurrence was already consumed by a column in the first pass, the surviving "
    "copybook-only citation is the later copybook's - copybooks/plwsoi5C.cob:L13 carries "
    "Open-Item-Record-5.oi5-key for exactly this reason, because copybooks/plwsoi5B.cob:L13 "
    "is cited by PUITM5-REC.OI5-KEY. A third and final pass emits the fields of the records "
    "the posting programs declare inline in their own FILE SECTIONs, keyed on the "
    "same record-name-and-field-name form; they take no part in the second pass's election, "
    "because two programs declaring a work-file record are two physical sources and not two "
    "spellings of one, so both declarations are emitted and the # line segment keeps them "
    "apart."
)

_RULE_PRESENCE_AND_ONE_SIDED: Final[str] = (
    "in_copybook, in_bridge, in_column and in_program_source are set from what the generator "
    "actually found: each is true exactly when the corresponding view object is non-null. "
    "one_sided is the negation of the conjunction of the first three, so it is true for any "
    "field that one layer of the authoritative triple declares and another does not; "
    "in_program_source is not a term of it, because a field a program declares inline in its "
    "own FILE SECTION reaches no table and so has all three of those false and is "
    "one-sided by construction rather than by comparison. No field is ever dropped for being "
    "absent from a source; absence is recorded as a false and the field still gets an "
    "entry. Notes are composed "
    "mechanically from the same facts and never editorially. On a copybook record: every "
    "header comment line the copybook states about its own record length or byte count, or "
    "shouts as a warning in capitals, quoted verbatim in the order stated with the comment "
    "marker and any box border stripped and joined to its continuation only where a box "
    "border shows the sentence has not ended - a repeated length figure therefore stays "
    "visible in notes even though declared_lengths carries each distinct length once, in "
    "first-stated order, as the schema requires; then the other 01-level records it declares, "
    "any in-scope copybook whose items are identical to its own, any bridge that COPYs it "
    "with the line that does so, and every spelling of a SIGN clause it uses. On an entry, "
    "only facts no structured member already carries: the drift details, the load and unload "
    "facts, and the maintainer's own words where the source carries a comment about that "
    "field. THE COPYBOOK-ONLY TAXONOMY IS PUBLISHED STRUCTURALLY RATHER THAN IN PROSE, and "
    "this is the rule for reading it. A field with in_copybook true and in_bridge and "
    "in_column false reaches no column, and which of the four kinds it is follows from its "
    "own members: is_filler true means a FILLER, which names no value; redefines non-null "
    "means a REDEFINES alternative view of storage another item already declares, and so "
    "does a null redefines whose parent_group chain reaches an ancestor with one, which is "
    "the commoner case because a subordinate of a redefining group carries no clause of its "
    "own; is_group true means a group item whose subordinate items carry the values; and none "
    "of those means a plain field the bridge does not carry. No such field is dropped - it is "
    "recorded and flagged - and no entry restates in prose what those members already say. "
    "THE MIRROR CASE READS THE SAME WAY. in_copybook false with in_bridge and in_column "
    "true means NO COPYBOOK DECLARES THE COLUMN: it exists in the bridge host-variable "
    "group and in the frozen dump alone, its derivation.kind is BRIDGE_DERIVED, and it is "
    "in this dictionary because the bridge - not the copybook - is the authoritative "
    "record-layout to table mapping, which meta.authority states verbatim. Fourteen "
    "columns read that way, three of them the date components of IRSPOSTING-REC that no "
    "copybook mentions at all."
)

_RULE_DRIFT_DETECTION: Final[str] = (
    "Every flag is computed by comparing the views that are present, never by consulting a "
    "list of known cases - which is why the dictionary finds signedness narrowing in "
    "copybooks/wsbatch.cob as well as in copybooks/wssl.cob. signedness compares the copybook "
    "picture or binary declaration, the S in the host-variable picture, and the absence of "
    "the column's unsigned suffix. usage compares the copybook storage class against the host "
    "variable's. digits compares total and integer digit counts, taking a DECIMAL column's "
    "precision and scale as its counts. scale compares fractional digit counts. "
    "character_length compares declared character widths, taking a CHAR column's width as "
    "its. name compares the copybook data-name, the host-variable name with its HV or HV1 "
    "prefix removed, and the column name, case-insensitively. Each set flag adds one sentence "
    "to details naming the views and what each says. A flag is a record of disagreement and "
    "never a resolution of it: no view is corrected, preferred or collapsed (R-4). WHAT A "
    "SIGNEDNESS NARROWING ACTUALLY STORES was measured rather than reasoned about, and is "
    "recorded here once for every entry it applies to. Where the copybook is signed and the "
    "host variable is not, GnuCOBOL 3.2.0 stores the ABSOLUTE VALUE and then truncates it to "
    "the host variable's digit count rather than wrapping it: a signed source of -1 stores 1, "
    "-1000 stores 1000, -2147483648 stores 2147483648, and -123456 into a four-digit unsigned "
    "host variable stores 3456, which is what +123456 stores too. The sign is discarded and "
    "the magnitude survives, so the debit-versus-credit sense of the statistic is gone. That "
    "is question Q-3, resolved by measurement, and anomaly A-11, reproduced rather than "
    "corrected - which is why each affected entry carries A-11 in anomaly_refs and a note "
    "citing the measurement, and none of them carries Q-3 as though it were still open."
)

_RULE_DIGITS_AND_SCALE: Final[str] = (
    "A picture is expanded so that 9(4) becomes 9999, then integer_digits is the count of 9 "
    "before any V, scale is the count after it, and digits is their sum. character_length is "
    "the expanded length of an X or A picture, and the digit members are null for such an "
    "item. An item with no picture - a group, or a BINARY-CHAR, BINARY-SHORT or BINARY-LONG "
    "item whose range comes from its usage rather than from a picture - carries null in all "
    "four, because inventing a digit count would be adding a fact the source does not state "
    "(R-3)."
)

_RULE_SIGN_POSITION: Final[str] = (
    "NONE for an unsigned item and for a group. IMPLICIT_BINARY for a signed COMP, COMP-3, "
    "COMP-5 or BINARY-* item, where the sign belongs to the binary or packed representation. "
    "LEADING_INCLUDED or TRAILING_INCLUDED when a SIGN clause names the position, and the "
    "SEPARATE forms when it says so. TRAILING_INCLUDED for a signed DISPLAY item with no SIGN "
    "clause, which is COBOL's default overpunch. The clause text itself is kept verbatim in "
    "sign_clause_text, so the two spellings the copybooks use - \"sign leading\" at "
    "copybooks/wspost-irs.cob:L21 and \"sign is leading\" at copybooks/irswspost.cob:L14 - "
    "are preserved as written and never normalised to one form (R-3). Signedness of a "
    "BINARY-* item is taken from the presence of UNSIGNED, not from the usage name."
)

_RULE_USAGE_INHERITANCE: Final[str] = (
    "The parser keeps a stack of open levels. A group that declares a USAGE passes it to "
    "every subordinate item that declares none, and the inheritance is recorded rather than "
    "silently applied: usage_declared_at is FIELD when the clause is on the item, GROUP when "
    "it was inherited - with usage_inherited_from naming the group and usage_group_source "
    "citing its line - and DEFAULT when no clause governs the item anywhere, so COBOL's "
    "DISPLAY applies. This is the single highest-risk rule in the whole generator: "
    "copybooks/wsbatch.cob:L40 declares 03 Amounts comp-3 and the four amount fields beneath "
    "it at L41-L44 carry no usage on their own picture lines, and copybooks/wssys4.cob:L9 and "
    "L20 do the same for twenty period totals. Reading usage from the picture line alone "
    "would class all of them as DISPLAY and every stored value would be wrong. A PIC X item "
    "is recorded as ALPHANUMERIC and an item with subordinates and no picture as GROUP. The "
    "inheritance is published through those four members alone and is never restated as prose "
    "on the inheriting entry: the members carry the declaring group's own line, which prose "
    "repeated per entry would only paraphrase."
)

_RULE_BRIDGE_DERIVED_COLUMNS: Final[str] = (
    "A host variable is bound to the copybook field it carries by trying, in this fixed "
    "order: the data-name the load move names, the data-name the unload move names, the "
    "host-variable name with its HV or HV1 prefix removed, and the column name; each also "
    "retried under the spelling substitutions the frozen source itself evidences - adding or "
    "removing a WS- prefix, expanding a trailing -DAT to -DATE, reading TIPE as TYPE, and "
    "reading an OI3- or OI5- prefix as OI-. Finally a trailing -NN is stripped and the base "
    "retried, binding only when the field found declares OCCURS at least NN, which is how the "
    "bridges that flatten an array into separately named columns still reach the single "
    "copybook item that declares it. A reference modification such as Post-Date (1:2) is "
    "never a binding candidate, because it derives a new value from part of a field rather "
    "than carrying that field - which is exactly why the three IRS date components correctly "
    "have no copybook view. When no candidate binds and a column exists, the entry carries "
    "copybook null and a derivation: BRIDGE_DERIVED when the bridge computes the value from "
    "other record data, from a literal, or from the subscript of an OCCURS group; "
    "GROUP_CONCATENATION when a whole copybook group is moved into one host variable; "
    "REDEFINES_ALTERNATIVE when the value comes from a REDEFINES view of the storage. A load "
    "made inside an IF records that condition verbatim as the guard and states in "
    "guard_failure_behaviour what is stored when it does not hold, because the failure mode "
    "is part of the specification and must be reproduced rather than repaired (R-4)."
)

_RULE_COBOL_PYTHON_STORAGE: Final[str] = (
    "Chosen from the declaring COBOL view alone - the copybook view, or the program-source "
    "view for a work-file field that no copybook declares: NONE for a group item or for an "
    "entry with neither of those views; STR for an alphanumeric item; DECIMAL for a "
    "numeric item with a non-zero "
    "scale; INT for the BINARY-CHAR, BINARY-SHORT, BINARY-LONG and COMP-5 family and for any "
    "zero-scale integer. This member exists only so that the choice between decimal.Deci"
    "mal and int is data-driven rather than hand-coded per field (R-2); getting the binary "
    "family right is what makes the integer truncation in the legacy moving averages "
    "reproducible. It is emphatically NOT a settlement of any drift: it describes the COBOL "
    "side alone, and anything that needs to know what the bridge or the database does must "
    "read those views instead."
)

_RULE_PROGRAM_SOURCE_ENTRIES: Final[str] = (
    "A record a posting program declares INLINE, in its own FILE SECTION rather than "
    "by COPY, is read from a stated line span and never from a search: the generator holds "
    "the program path, the 01-level record name, whether an FD or an SD introduces it, and "
    "the first and last physical lines of the declaration, and it refuses to parse a span "
    "whose first line does not declare the named record or whose nearest preceding FD or SD "
    "does not match. Five such records exist, all of them General Ledger work files - "
    "pre-trans-record in general/gl070.cbl and general/gl071.cbl, post-trans-record in "
    "general/gl071.cbl and general/gl072.cbl, and sort-trans-record in general/gl071.cbl. "
    "The declarations are parsed by the same code that parses a copybook, because a COBOL "
    "data declaration has one shape wherever it is written, so digits, scale, signedness, "
    "sign position and storage class are derived for these fields exactly as they are for "
    "every other field and none of them is hand-bound (R-5). Their bridge and column views "
    "are recorded as ABSENT rather than searched for: copybooks/wsnames.cob:L15-L16 names "
    "pretrans.tmp and postrans.tmp as transient work files, no bridge COPYs these records "
    "and the frozen dump declares no table for them, so presence.in_program_source is true "
    "with in_copybook, in_bridge and in_column all false, one_sided is true by construction, "
    "and derivation is null because there is no column to derive. They are in the dictionary "
    "because their widths and their order are load-bearing anyway: general/gl072.cbl:"
    "L408 locates a nominal-ledger account by sequential read and therefore depends on "
    "the order general/gl071.cbl sorted the stream into, which is anomaly A-14."
)

_BINDING_RULE_SUMMARIES: Final[tuple[str, ...]] = (
    (
        "No COBOL at runtime. This document is pure static data, loadable with the "
        "standard-library json module alone: it names no command, no executable, no compiler "
        "and no absolute path, and COBOL sources appear only as repository-relative "
        "provenance locators. Capturing the bridge's semantics as data is precisely what lets "
        "the Python data-access layer reproduce the bridge without ever calling it."
    ),
    (
        "Zero binary flo"
        "ating point in accounting computation. Every value, picture clause, SQL type and "
        "sign clause is a JSON string; only dimensionless counts are JSON integers, and no "
        "JSON flo"
        "at or exponent appears anywhere. Every numeric view carries usage, signedness, sign "
        "position, digits and scale so that decimal.Deci"
        "mal versus int is selected from data. The frozen schema corroborates it: zero FLOAT, "
        "DOUBLE or REAL columns."
    ),
    (
        "No new validations, fields or schema changes, and no concurrency. Every field "
        "recorded exists in at least one of the three sources; none is inferred or invented. "
        "The document emits no DDL and proposes no type, width or index - it describes and "
        "never prescribes. Source spellings are preserved exactly, including the two forms of "
        "the leading-sign clause and names that carry the wrong ledger's prefix. Generation "
        "is a single sequential pass."
    ),
    (
        "Legacy anomalies reproduced, never fixed. Where the three sources disagree all three "
        "views are recorded independently, the drift flags are set by comparison, and details "
        "plus notes explain the disagreement in plain words. No drift is ever collapsed into "
        "a single value and no source is corrected: a signed value narrowed to an unsigned "
        "column, a name spelled differently at each layer, and a record length its own author "
        "disputes are all stated as facts."
    ),
    (
        "Full traceability. Every field of every in-scope record has exactly one entry with a "
        "stable unique key, and every view carries a path and line locator into the frozen "
        "source. A field present in one source and absent from another is flagged through "
        "presence and one_sided rather than dropped, and coverage.one_sided_entry_keys lists "
        "every such key in one place."
    ),
    (
        "Compiled behaviour is the tie-breaker. Where reading the source cannot settle a "
        "question the entry carries an ambiguity_refs identifier rather than a guessed answer, "
        "and once measurement settles the question the identifier is withdrawn and the measured "
        "fact is published in its place - because publishing a settled question as an open one "
        "misreports it just as badly as guessing. Two identifiers are published: Q-4, on the "
        "entries of the record whose two declared lengths contradict each other, and Q-6, on "
        "the one column whose bridge source records the maintainer's own doubt. Both were put "
        "to the compiled program and both are now RESOLVED BY ORACLE, so each entry carries the "
        "identifier as the trail to the measurement rather than as an open item. A third, Q-3 - "
        "what a negative binary value becomes once it has passed through an unsigned host "
        "variable into an unsigned column - was published here until it was measured; it is "
        "withdrawn, and the measured store now lives once in derivation_rules.drift_detection "
        "with a note on each affected entry citing it. Anomaly A-11 stays regardless: measuring "
        "the sign loss did not repair it (R-4)."
    ),
)

_SCHEMA_NOTE_TEMPLATES: Final[tuple[str, ...]] = (
    (
        "The dump declares %d tables and %d columns in all; %d of those tables and %d of "
        "those columns belong to the posting cycle and are catalogued here. The remaining "
        "tables lie outside the cycle and are referred to by count only, never by name."
    ),
    (
        "The dump carries %d version-guarded key-management comments naming ALTER TABLE, one "
        "to disable and one to enable each table's keys around its data section. They are "
        "mysqldump artefacts inside a version guard, not structural change, which is why the "
        "count of structural changes is %d and is reported separately. Neither figure is a "
        "statement this document makes about what the schema should be: the schema is frozen "
        "and this document only describes it."
    ),
    (
        "There is not one FLOAT, DOUBLE or REAL column anywhere in the dump, so the database "
        "cannot hand a binary flo"
        "ating-point value to the Python layer; every accounting value is carried as "
        "decimal.Deci"
        "mal or int end to end."
    ),
    (
        "Every character column is fixed width - %d CHAR declarations and %d VARCHAR - so "
        "trailing padding is significant and any comparison of two table states has to "
        "canonicalise it."
    ),
    (
        "Every one of the %d in-scope columns is declared NOT NULL, with not one exception, "
        "and the bridges keep it that way by issuing INITIALIZE on the whole host-variable "
        "group before loading it, so an unset field arrives as zero or space rather than as "
        "SQL NULL. The Python data-access layer must therefore supply a default for every "
        "column instead of omitting it."
    ),
    (
        "All %d in-scope tables have a single-column primary key and no secondary index, and "
        "none carries a timestamp column or an auto-increment column. Exactly %d in-scope "
        "column of the %d declares a default: %s at %s, whose default is %s. This is what "
        "lets an ordering-normalised state dump be a plain ordered select with no "
        "tie-breaking."
    ),
    (
        "%d in-scope columns carry a COMMENT; the text is kept verbatim on the column view "
        "rather than paraphrased."
    ),
    (
        "A null scale and a zero scale are different facts: %d in-scope column is DECIMAL "
        "with an explicit scale of zero, so a scale is recorded exactly as parsed and never "
        "defaulted."
    ),
)

# READING THE FROZEN SOURCES - read-only, contained, line-exact, digested Every byte
# this generator turns into dictionary content arrives through `_read_lines`, and
# `_read_lines` is the only place in the module that opens a file for reading.

_O_NOFOLLOW: Final[int] = getattr(os, "O_NOFOLLOW", 0)

#: The shape a `COPY "..."` literal must take before it is turned into a path.
_COPY_TARGET_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")

_COPYBOOK_ROOT: Final[str] = "copybooks"


class SourceContainmentError(ValueError):
    """A path the generator was asked to read is not a contained frozen source.

    Raised rather than skipped.
    """


#: Line caches keyed by (root, repository-relative path) so a second `--repo-root` can
#: never see the first one's text.
_LINE_CACHE: dict[tuple[str, str], list[str]] = {}

#: The SHA-256 and byte length of every frozen source actually opened, keyed exactly as
#: `_LINE_CACHE` is. This IS the provenance manifest.
_INPUT_DIGESTS: dict[tuple[str, str], tuple[str, int]] = {}

#: Roots whose manifest has been taken.
_SEALED_ROOTS: set[str] = set()
_COPYBOOK_CACHE: dict[tuple[str, str], list["_CopybookItem"]] = {}
_PROGRAM_SOURCE_CACHE: dict[tuple[str, str, str], list["_CopybookItem"]] = {}
_LINEAGE_CACHE: dict[tuple[str, str], dict[tuple[int, str], bool]] = {}
_ODD_PREFIX_CACHE: dict[tuple[str, str], frozenset[tuple[int, str]]] = {}

_WHITESPACE_RUN: Final[re.Pattern[str]] = re.compile(r"\s+")


def _contained_path(root: Path, rel: str) -> Path:
    """Resolve a repository-relative path and prove it stays inside the repository.

    The shape test comes first because it is the cheap one and it rejects the whole
    class outright.
    Args:
        root: The repository root, as given on the command line or defaulted.
        rel: The path to read, relative to that root.

    Returns:
        The fully resolved absolute path of the file to open.

    Raises:
        SourceContainmentError: `rel` is not a contained repository-relative path, or it
            resolves outside the root - whether by dot-dot segments or by following a
            symbolic link out of the tree.
        FileNotFoundError: Neither the root nor the target exists. Resolution is strict
            deliberately.
    """
    if model.REPO_PATH_PATTERN.match(rel) is None:
        raise SourceContainmentError(
            "%r is not a contained repository-relative path" % rel)
    anchor = root.resolve(strict=True)
    target = (anchor / rel).resolve(strict=True)
    if target == anchor or not target.is_relative_to(anchor):
        raise SourceContainmentError(
            "%r resolves outside the repository root %s" % (rel, anchor))
    return target


def _copy_target(literal: str) -> str:
    """Turn a `COPY "..."` literal into the contained copybook path it names.

    This is the one place a value taken FROM a frozen source becomes a path this program
    opens, so it is the one place that has to be suspicious.

    Args:
        literal: The quoted name exactly as the frozen source writes it.

    Returns:
        The repository-relative path of the copybook, under `copybooks/`.

    Raises:
        SourceContainmentError: The literal is not a single bare file name, so joining
            it to the copybook directory would not stay inside that directory.
    """
    if _COPY_TARGET_PATTERN.match(literal) is None:
        raise SourceContainmentError(
            "COPY %r does not name a single contained copybook file" % literal)
    return "%s/%s" % (_COPYBOOK_ROOT, literal)


def _read_lines(root: Path, rel: str) -> list[str]:
    """Return the physical lines of a frozen source, 1-based when indexed from zero+1.

    Opened read-only and never for writing - the freeze forbids any write to these paths
    - and only after `_contained_path` has proved the target sits inside the repository.

    Raises:
        SourceContainmentError: The path is not a contained frozen source.
        RuntimeError: The provenance manifest for this root has already been taken and
            this file was not part of it.
    """
    key = (str(root), rel)
    cached = _LINE_CACHE.get(key)
    if cached is None:
        if key[0] in _SEALED_ROOTS:
            raise RuntimeError(
                "%s was read after the provenance manifest for %s was taken"
                % (rel, key[0]))
        target = _contained_path(root, rel)
        descriptor = os.open(target, os.O_RDONLY | _O_NOFOLLOW)
        try:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1 << 20)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(descriptor)
        raw = b"".join(chunks)
        _INPUT_DIGESTS[key] = (hashlib.sha256(raw).hexdigest(), len(raw))
        text = raw.decode("utf-8", errors="surrogateescape")
        cached = [line.rstrip("\r") for line in text.split("\n")]
        _LINE_CACHE[key] = cached
    return cached


def _input_digest_manifest(root: Path) -> tuple[model.SourceDigest, ...]:
    """The provenance manifest for one root: every file read, with digest and length.

    Args:
        root: The repository root whose reads are being summarised.

    Returns:
        One `SourceDigest` per frozen source this run opened under that root, sorted by
            path so the manifest does not depend on the order the stages happened to
            read them in (rule R-6).
    """
    _SEALED_ROOTS.add(str(root))
    anchor = str(root)
    return tuple(
        model.SourceDigest(path=rel, sha256=digest, byte_length=length)
        for (cached_root, rel), (digest, length) in sorted(_INPUT_DIGESTS.items())
        if cached_root == anchor
    )


def _strip_comment(line: str) -> tuple[str, str]:
    """Split one physical line into (code, comment body).

    Three comment forms occur across the in-scope sources and all three are handled: the
    free-format `*>` marker at any column, the fixed-format `*` in column 7, and a line
    whose first non-blank character is `*`.
    """
    marker = line.find("*>")
    if marker >= 0:
        return line[:marker], line[marker + 2:]
    if len(line) > 6 and line[6] == "*" and not line[:6].strip():
        return "", line[7:]
    stripped = line.strip()
    if stripped.startswith("*"):
        return "", stripped[1:]
    return line, ""


def _collapse(text: str) -> str:
    """Collapse runs of whitespace and trim, for quoting COBOL back as one sentence."""
    return _WHITESPACE_RUN.sub(" ", text).strip()


_CREATE_TABLE_RE: Final[re.Pattern[str]] = re.compile(r"^CREATE TABLE `([^`]+)` \($")
_COLUMN_RE: Final[re.Pattern[str]] = re.compile(r"^  `([^`]+)` (.+?),?$")
_PRIMARY_KEY_RE: Final[re.Pattern[str]] = re.compile(r"^  PRIMARY KEY \(`([^`]+)`\)")
_SQL_TYPE_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<base>[a-z]+)(?:\((?P<width>\d+)(?:,(?P<scale>\d+))?\))?(?P<rest>.*)$"
)
_SQL_COMMENT_RE: Final[re.Pattern[str]] = re.compile(r"\s+COMMENT '((?:[^']|'')*)'\s*$")
_SQL_DEFAULT_RE: Final[re.Pattern[str]] = re.compile(r"\s+DEFAULT (.+?)\s*$")
_SERVER_VERSION_RE: Final[re.Pattern[str]] = re.compile(r"^-- Server version\s+(\S+)")
_GUARDED_ALTER_RE: Final[re.Pattern[str]] = re.compile(r"ALTER TABLE")
_INDEX_RE: Final[re.Pattern[str]] = re.compile(r"^CREATE\s+(?:UNIQUE\s+)?INDEX\b",
                                               re.IGNORECASE)
#: The three binary real types SQL can declare. The alternation is assembled from
#: fragments on purpose.
_BINARY_REAL_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:" + "flo" + "at|dou" + "ble|real)\b", re.IGNORECASE)


class _SchemaFacts:
    """Everything Stage 1 learns from the frozen dump.

    Attributes:
        tables: table name -> {"line", "cols", "pk"}, `cols` being a list of (physical
            line, column name, declaration text) in DDL order.
        server_version: The producing server, quoted from the dump's own header.
        server_version_line: The physical line that states it.
        create_table_count: How many tables the dump declares.
        create_index_count: How many standalone index statements it carries.
        structural_alter_count: How many ALTER TABLE statements are real DDL rather than
            a version-guarded mysqldump comment.
        guarded_alter_comment_count: How many are exactly that comment.
        binary_real_columns: How many columns declare a binary real type.
    """

    __slots__ = ("tables", "server_version", "server_version_line", "create_table_count",
                 "create_index_count", "structural_alter_count",
                 "guarded_alter_comment_count", "binary_real_columns")


def _parse_schema(root: Path) -> _SchemaFacts:
    """Parse `mysql/ACASDB.sql` into table, column and census facts.

    The one trap worth naming: `ALTER TABLE` appears 66 times in the dump and every
    single occurrence sits inside a `/*!` version guard, two per table, disabling and
    re-enabling that table's keys around its data section.
    """
    lines = _read_lines(root, _SCHEMA_REL)
    facts = _SchemaFacts()
    facts.tables = {}
    facts.server_version = ""
    facts.server_version_line = 0
    facts.create_table_count = 0
    facts.create_index_count = 0
    facts.structural_alter_count = 0
    facts.guarded_alter_comment_count = 0
    facts.binary_real_columns = 0
    current: dict[str, object] | None = None
    for number, raw in enumerate(lines, 1):
        guarded = raw.lstrip().startswith("/*!")
        commented = raw.lstrip().startswith("--")
        if _GUARDED_ALTER_RE.search(raw):
            if guarded or commented:
                facts.guarded_alter_comment_count += 1
            else:
                facts.structural_alter_count += 1
        if not facts.server_version:
            found = _SERVER_VERSION_RE.match(raw)
            if found:
                facts.server_version = found.group(1)
                facts.server_version_line = number
        if guarded or commented:
            continue
        if _INDEX_RE.match(raw):
            facts.create_index_count += 1
            continue
        opened = _CREATE_TABLE_RE.match(raw)
        if opened:
            facts.create_table_count += 1
            current = {"name": opened.group(1), "line": number, "cols": [], "pk": None}
            facts.tables[opened.group(1)] = current
            continue
        if current is None:
            continue
        if raw.startswith(")"):
            current = None
            continue
        key = _PRIMARY_KEY_RE.match(raw)
        if key:
            current["pk"] = key.group(1)
            continue
        column = _COLUMN_RE.match(raw)
        if column:
            current["cols"].append((number, column.group(1), column.group(2)))
            if _BINARY_REAL_RE.search(column.group(2)):
                facts.binary_real_columns += 1
    return facts


def _column_view(lineno: int, name: str, declaration: str, primary_key: str | None,
                 ordinal: int) -> model.MysqlColumn:
    """Build the column view of one field from its `CREATE TABLE` line.

    `sql_type` is the dump's own text, display width and `unsigned` suffix included. It
    is never re-rendered from the parsed parts.
    """
    sql_type = declaration
    comment = None
    found = _SQL_COMMENT_RE.search(sql_type)
    if found:
        comment = found.group(1).replace("''", "'")
        sql_type = sql_type[:found.start()]
    default = None
    found = _SQL_DEFAULT_RE.search(sql_type)
    if found:
        default = found.group(1)
        sql_type = sql_type[:found.start()]
    nullable = True
    if sql_type.upper().endswith(" NOT NULL"):
        nullable = False
        sql_type = sql_type[: -len(" NOT NULL")]
    elif sql_type.upper().endswith(" NULL"):
        sql_type = sql_type[: -len(" NULL")]
    sql_type = sql_type.strip()
    parsed = _SQL_TYPE_RE.match(sql_type)
    if parsed is None:  # pragma: no cover - the frozen dump has no other shape
        raise ValueError("unparsable column type %r at %s:L%d"
                         % (sql_type, _SCHEMA_REL, lineno))
    width = int(parsed.group("width")) if parsed.group("width") else None
    scale = int(parsed.group("scale")) if parsed.group("scale") else None
    return model.MysqlColumn(
        file=_SCHEMA_REL,
        source="%s:L%d" % (_SCHEMA_REL, lineno),
        name=name,
        sql_type=sql_type,
        base_type=model.SqlBaseType(parsed.group("base").upper()),
        display_width=width,
        scale=scale,
        unsigned="unsigned" in parsed.group("rest").lower(),
        nullable=nullable,
        column_default=default,
        is_primary_key=name == primary_key,
        ordinal=ordinal,
        comment=comment,
    )


_LEVEL_RE: Final[re.Pattern[str]] = re.compile(r"^(0[1-9]|[1-4][0-9]|66|77|88)$")
_COPY_RE: Final[re.Pattern[str]] = re.compile(r'^\s*copy\s+"([^"]+)"', re.IGNORECASE)

_SELECT_ASSIGN_RE: Final[re.Pattern[str]] = re.compile(
    r"(?i)^select\s+([A-Za-z][A-Za-z0-9-]*)\s+assign\b")
#: A quoted literal, a pseudo-text delimiter pair, or a run of non-blanks. Quoted forms
#: come first so a literal containing blanks stays one token.
_TOKEN_RE: Final[re.Pattern[str]] = re.compile(r'"[^"]*"|\'[^\']*\'|==[^=]*==|[^\s]+')
_USAGE_SPELLINGS: Final[dict[str, str]] = {
    "comp": "COMP", "computational": "COMP", "comp-1": "COMP", "comp-2": "COMP",
    "comp-3": "COMP-3", "computational-3": "COMP-3", "packed-decimal": "COMP-3",
    "comp-4": "COMP", "comp-5": "COMP-5", "computational-5": "COMP-5",
    "comp-6": "COMP-3", "binary": "COMP", "binary-char": "BINARY-CHAR",
    "binary-short": "BINARY-SHORT", "binary-long": "BINARY-LONG",
    "binary-double": "BINARY-LONG", "display": "DISPLAY", "pointer": "POINTER",
}
_BINARY_USAGES: Final[frozenset[str]] = frozenset(
    ("COMP", "COMP-3", "COMP-5", "BINARY-CHAR", "BINARY-SHORT", "BINARY-LONG")
)
_IMPLICIT_INT_USAGES: Final[frozenset[str]] = frozenset(
    ("BINARY-CHAR", "BINARY-SHORT", "BINARY-LONG", "COMP-5")
)
_SIGN_WORDS: Final[frozenset[str]] = frozenset(
    ("is", "leading", "trailing", "separate", "character")
)


def _logical_statements(lines: list[str]) -> list[tuple[int, str]]:
    """Accumulate physical lines into period-terminated logical statements.

    Four in-scope copybooks split a declaration across physical lines - `wsbatch.cob`,
    `wsledger.cob`, `slwsoi.cob` and `plwsoi.cob`. `copybooks/wsbatch.cob:L20-L21` is
    the clearest: the level, name and REDEFINES target sit on one line and the picture
    on the next.
    """
    statements: list[tuple[int, str]] = []
    buffer = ""
    start: int | None = None
    for number, raw in enumerate(lines, 1):
        code, _ = _strip_comment(raw)
        text = code.strip()
        if not text:
            continue
        if text.startswith(">>"):
            continue
        if start is None:
            start = number
        buffer = (buffer + " " + text) if buffer else text
        while True:
            cut = _statement_terminator(buffer)
            if cut is None:
                break
            statements.append((start or number, buffer[:cut].strip()))
            buffer = buffer[cut + 1:].strip()
            start = number if buffer else None
            if not buffer:
                break
    if buffer.strip():
        statements.append((start or len(lines), buffer.strip()))
    return statements


def _statement_terminator(text: str) -> int | None:
    """Index of the period that ends a statement, or None if the statement is open."""
    quote: str | None = None
    for index, char in enumerate(text):
        if quote:
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            continue
        if char == "." and (index + 1 == len(text) or text[index + 1].isspace()):
            return index
    return None


def _expand_picture(picture: str) -> str:
    """Expand a picture's parenthesised repeat counts into a flat symbol string.

    `9(4)v99` becomes `9999v99`, so counting digits is a matter of counting symbols and
    the repeated-symbol and parenthesised forms need no separate handling. All of it is
    integer work; no value is ever evaluated (R-2).
    """
    symbols: list[str] = []
    index = 0
    while index < len(picture):
        char = picture[index]
        if char == "(":
            close = picture.index(")", index)
            count = int(picture[index + 1:close])
            symbols.extend([symbols[-1]] * (count - 1))
            index = close + 1
            continue
        symbols.append(char)
        index += 1
    return "".join(symbols)


class _CopybookItem:
    """One data item as the copybook declares it, plus what the parse needs afterwards.

    The public members mirror `model.CopybookField` exactly; `record`, `own_usage` and
    `value_text` are parse state that never reaches the document.
    """

    __slots__ = ("file", "line", "level", "name", "picture", "usage", "usage_declared_at",
                 "usage_inherited_from", "usage_group_source", "signed", "sign_position",
                 "sign_clause_text", "digits", "integer_digits", "scale",
                 "character_length", "redefines", "occurs", "is_filler", "is_group",
                 "parent_group", "condition_names", "record", "own_usage", "value_text")

    @property
    def source(self) -> str:
        """The repository-relative locator of this item's first physical line."""
        return "%s:L%d" % (self.file, self.line)

    def view(self) -> model.CopybookField:
        """Return the copybook view this item contributes to the document."""
        return model.CopybookField(
            file=self.file,
            source=self.source,
            name=self.name,
            level=self.level,
            picture=self.picture,
            usage=model.Usage(self.usage),
            usage_declared_at=model.UsageDeclaredAt(self.usage_declared_at),
            usage_inherited_from=self.usage_inherited_from,
            usage_group_source=self.usage_group_source,
            signed=self.signed,
            sign_position=model.SignPosition(self.sign_position),
            sign_clause_text=self.sign_clause_text,
            digits=self.digits,
            integer_digits=self.integer_digits,
            scale=self.scale,
            character_length=self.character_length,
            redefines=self.redefines,
            occurs=self.occurs,
            is_filler=self.is_filler,
            is_group=self.is_group,
            parent_group=self.parent_group,
            condition_names=tuple(self.condition_names),
        )


def _parse_copybook(root: Path, rel: str) -> list["_CopybookItem"]:
    """Parse one copybook into its data items, in declaration order.

    The load-bearing rule here is group-level USAGE inheritance. A group item that
    carries a USAGE and no PICTURE lends that storage class to every subordinate item
    that declares none of its own.
    """
    key = (str(root), rel)
    cached = _COPYBOOK_CACHE.get(key)
    if cached is not None:
        return cached
    items = _items_from_declarations(rel, _declarations_in(_read_lines(root, rel)))
    _COPYBOOK_CACHE[key] = items
    return items


def _declarations_in(lines: list[str]) -> list[tuple[int, list[str]]]:
    """Every data declaration in the given source lines, as (first line, tokens).

    The line number is one-based within the list that was passed, which is the whole
    file for a copybook and a single record's span for a program-source record.
    """
    declarations: list[tuple[int, list[str]]] = []
    for start, code in _logical_statements(lines):
        tokens = _TOKEN_RE.findall(code)
        if not tokens or not _LEVEL_RE.match(tokens[0]):
            continue
        declarations.append((start, tokens))
    return declarations


def _items_from_declarations(rel: str,
                             declarations: list[tuple[int, list[str]]],
                             ) -> list["_CopybookItem"]:
    """Turn a run of COBOL data declarations into items, in declaration order.

    Shared verbatim by the copybook parse and by the program-source parse, because a
    COBOL data declaration has one shape wherever it is written.
    """
    items: list[_CopybookItem] = []
    stack: list[_CopybookItem] = []
    record: str | None = None
    for index, (start, tokens) in enumerate(declarations):
        level = tokens[0]
        if level == "88":
            if items:
                items[-1].condition_names.append(
                    model.ConditionName(name=tokens[1],
                                        value=_condition_value(tokens),
                                        source="%s:L%d" % (rel, start)))
            continue
        if level in ("66", "77"):
            continue

        item = _CopybookItem()
        item.file, item.line, item.level = rel, start, level
        item.condition_names = []
        item.name = tokens[1] if len(tokens) > 1 else "filler"
        item.is_filler = item.name.lower() == "filler"
        clauses = _parse_clauses(tokens)
        item.picture = clauses["picture"]
        item.own_usage = clauses["usage"]
        item.occurs = clauses["occurs"]
        item.redefines = clauses["redefines"]
        item.sign_clause_text = (clauses["sign"].lower() if clauses["sign"] else None)
        item.value_text = clauses["value"]

        numeric_level = int(level)
        while stack and int(stack[-1].level) >= numeric_level:
            stack.pop()
        item.parent_group = stack[-1].name if stack else None
        if numeric_level == 1:
            record = item.name
        item.record = record

        following = None
        for ahead in range(index + 1, len(declarations)):
            level_ahead = declarations[ahead][1][0]
            if level_ahead in ("88", "66", "77"):
                continue
            following = int(level_ahead)
            break
        item.is_group = (item.picture is None and following is not None
                         and following > numeric_level)

        _resolve_usage(item, stack)
        _resolve_arithmetic_shape(item, clauses["unsigned"])
        items.append(item)
        stack.append(item)

    return items


def _program_source_span(rel: str, record: str) -> tuple[str, int, int]:
    """The declaring section and the line span the frozen table states for one record.

    Raises `KeyError` rather than guessing: a record this generator was not told about
    is not a record it may invent a span for.
    """
    for path, name, section, first, last in _PROGRAM_SOURCE_RECORDS:
        if path == rel and name == record:
            return section, first, last
    raise KeyError("%s declares no catalogued record named %s" % (rel, record))


def _program_source_siblings(rel: str, record: str) -> list[str]:
    """The other programs the table records as declaring a record of the same name."""
    return sorted(path for path, name, _s, _f, _l in _PROGRAM_SOURCE_RECORDS
                  if name == record and path != rel)


def _program_source_introducer(root: Path, rel: str,
                               first: int) -> tuple[int, str, str]:
    """The FD or SD immediately above a record declaration."""
    lines = _read_lines(root, rel)
    for number in range(first - 1, 0, -1):
        code, _comment = _strip_comment(lines[number - 1])
        tokens = _TOKEN_RE.findall(code)
        if not tokens:
            continue
        return (number, tokens[0].rstrip(".").upper(),
                tokens[1].rstrip(".") if len(tokens) > 1 else "")
    return 0, "", ""


def _program_source_select(root: Path, rel: str, file_name: str) -> tuple[int, str]:
    """The FILE-CONTROL SELECT statement that assigns the named file, and its line."""
    for number, code in _logical_statements(_read_lines(root, rel)):
        text = _collapse(code)
        match = _SELECT_ASSIGN_RE.match(text)
        if match and match.group(1).lower() == file_name.lower():
            return number, text
    return 0, ""


def _program_source_declared_lengths(root: Path, rel: str, first: int,
                                     last: int) -> tuple[str, ...]:
    """Every record length the program states in comments inside the record's span.

    Derived rather than asserted empty.
    """
    found: list[str] = []
    for number in range(first, last + 1):
        _code, comment = _strip_comment(_read_lines(root, rel)[number - 1])
        for digits in _BYTES_RE.findall(comment):
            if digits not in found:
                found.append(digits)
    return tuple(found)


def _parse_program_source(root: Path, rel: str, record: str) -> list["_CopybookItem"]:
    """Parse one record a posting program declares inline, from its stated span.

    The span comes from `_PROGRAM_SOURCE_RECORDS` rather than from a search, so no FILE
    SECTION of any other program can be drawn in by a pattern that happens to match, and
    the parse is checked against the frozen text before it is trusted.
    """
    key = (str(root), rel, record)
    cached = _PROGRAM_SOURCE_CACHE.get(key)
    if cached is not None:
        return cached

    section, first, last = _program_source_span(rel, record)
    lines = _read_lines(root, rel)
    declarations = [(first - 1 + start, tokens)
                    for start, tokens in _declarations_in(lines[first - 1:last])]
    if not declarations:
        raise ValueError("%s:L%d-L%d declares no data item" % (rel, first, last))
    head_line, head_tokens = declarations[0]
    if head_line != first or head_tokens[0] != "01" or len(head_tokens) < 2 \
            or head_tokens[1].lower() != record.lower():
        raise ValueError("%s:L%d does not declare 01 %s" % (rel, first, record))

    declared = None
    for number in range(first - 1, 0, -1):
        code, _comment = _strip_comment(lines[number - 1])
        tokens = _TOKEN_RE.findall(code)
        if not tokens:
            continue
        keyword = tokens[0].rstrip(".").upper()
        if keyword in ("FD", "SD"):
            declared = keyword
        break
    if declared != section:
        raise ValueError("%s:L%d is introduced by %s, not the %s the table states"
                         % (rel, first, declared, section))

    items = _items_from_declarations(rel, declarations)
    _PROGRAM_SOURCE_CACHE[key] = items
    return items


def _condition_value(tokens: list[str]) -> str:
    """The literal an 88-level condition name tests for, VALUE keyword removed."""
    for index in range(2, len(tokens)):
        if tokens[index].lower() in ("value", "values"):
            rest = tokens[index + 1:]
            if rest and rest[0].lower() == "is":
                rest = rest[1:]
            return " ".join(rest).rstrip(".")
    return ""


def _parse_clauses(tokens: list[str]) -> dict[str, object]:
    """Read the PICTURE, USAGE, OCCURS, REDEFINES, SIGN and VALUE clauses of one item.

    Both SIGN spellings are captured verbatim and neither is normalised against the
    other: `copybooks/wspost-irs.cob:L21` writes `sign leading` and
    `copybooks/irswspost.cob:L14` writes `sign is leading` for the same intent, and rule
    R-4 keeps that divergence visible.
    """
    picture: str | None = None
    usage: str | None = None
    occurs: int | None = None
    redefines: str | None = None
    sign: str | None = None
    value: str | None = None
    unsigned = False
    index = 2
    while index < len(tokens):
        word = tokens[index].lower().rstrip(".")
        if word in ("pic", "picture"):
            ahead = index + 1
            if ahead < len(tokens) and tokens[ahead].lower() == "is":
                ahead += 1
            picture = tokens[ahead].rstrip(".")
            index = ahead + 1
            continue
        if word == "redefines":
            redefines = tokens[index + 1].rstrip(".")
            index += 2
            continue
        if word == "occurs":
            occurs = int(re.sub(r"\D", "", tokens[index + 1]))
            index += 2
            continue
        if word == "usage":
            ahead = index + 1
            if ahead < len(tokens) and tokens[ahead].lower() == "is":
                ahead += 1
            spelling = tokens[ahead].lower().rstrip(".")
            if spelling in _USAGE_SPELLINGS:
                usage = _USAGE_SPELLINGS[spelling]
            index = ahead + 1
            continue
        if word in _USAGE_SPELLINGS:
            usage = _USAGE_SPELLINGS[word]
            index += 1
            continue
        if word == "sign":
            parts = [tokens[index]]
            ahead = index + 1
            while ahead < len(tokens) and tokens[ahead].lower().rstrip(".") in _SIGN_WORDS:
                parts.append(tokens[ahead].rstrip("."))
                ahead += 1
            sign = " ".join(parts)
            index = ahead
            continue
        if word == "unsigned":
            unsigned = True
            index += 1
            continue
        if word in ("value", "values"):
            value = " ".join(tokens[index + 1:]).rstrip(".")
            break
        index += 1
    return {"picture": picture, "usage": usage, "occurs": occurs, "redefines": redefines,
            "sign": sign, "value": value, "unsigned": unsigned}


def _resolve_usage(item: "_CopybookItem", stack: list["_CopybookItem"]) -> None:
    """Decide the item's storage class and record where that class was declared."""
    item.usage_inherited_from = None
    item.usage_group_source = None
    if item.is_group:
        item.usage = "GROUP"
        item.usage_declared_at = "FIELD" if item.own_usage else "DEFAULT"
        return
    if item.own_usage:
        item.usage = item.own_usage
        item.usage_declared_at = "FIELD"
        return
    ancestor = next((group for group in reversed(stack) if group.own_usage), None)
    if ancestor is not None:
        item.usage = ancestor.own_usage
        item.usage_declared_at = "GROUP"
        item.usage_inherited_from = ancestor.name
        item.usage_group_source = "%s:L%d" % (ancestor.file, ancestor.line)
        return
    if item.picture and re.search(r"[xXaA]", item.picture):
        item.usage = "ALPHANUMERIC"
    else:
        item.usage = "DISPLAY"
    item.usage_declared_at = "DEFAULT"


def _resolve_arithmetic_shape(item: "_CopybookItem", unsigned: bool) -> None:
    """Decompose the picture into digits, scale, width, signedness and sign position.

    `V` is an implied decimal point and contributes no character position. All counts
    are integers (R-2).
    """
    item.digits = item.integer_digits = item.scale = item.character_length = None
    item.signed = False
    item.sign_position = "NONE"
    if not item.is_group and item.picture:
        symbols = _expand_picture(item.picture).upper()
        if "9" in symbols:
            head, tail = symbols.split("V", 1) if "V" in symbols else (symbols, "")
            item.integer_digits = head.count("9")
            item.scale = tail.count("9")
            item.digits = item.integer_digits + item.scale
            item.signed = symbols.startswith("S")
        else:
            item.character_length = len(symbols.replace("S", ""))
    if not item.is_group and item.picture is None and item.usage in _IMPLICIT_INT_USAGES:
        item.signed = not unsigned
    if not item.signed:
        return
    if item.usage in _BINARY_USAGES:
        item.sign_position = "IMPLICIT_BINARY"
    elif item.sign_clause_text:
        leading = "leading" in item.sign_clause_text
        separate = "separate" in item.sign_clause_text
        item.sign_position = ("LEADING_" if leading else "TRAILING_") + (
            "SEPARATE" if separate else "INCLUDED")
    else:
        item.sign_position = "TRAILING_INCLUDED"


def _copybook_copies(root: Path, rel: str) -> list[str]:
    """The `.cob` files this copybook textually COPYs, in declaration order."""
    out: list[str] = []
    for raw in _read_lines(root, rel):
        code, _ = _strip_comment(raw)
        found = _COPY_RE.match(code)
        if found and found.group(1).lower().endswith(".cob"):
            out.append(_copy_target(found.group(1)))
    return out


def _bridge_copies(root: Path, bridge: str) -> list[tuple[int, str]]:
    """Every `.cob` a generated bridge COPYs, as (physical line, file name)."""
    out: list[tuple[int, str]] = []
    for number, raw in enumerate(_read_lines(root, "common/%s.cbl" % bridge), 1):
        code, _ = _strip_comment(raw)
        found = _COPY_RE.match(code)
        if found and found.group(1).lower().endswith(".cob"):
            out.append((number, found.group(1)))
    return out


def _bridge_record_copies(root: Path, bridge: str) -> list[tuple[int, str]]:
    """The record-layout copybooks a bridge COPYs, infrastructure excluded."""
    return [(number, name) for number, name in _bridge_copies(root, bridge)
            if name.lower() not in _INFRASTRUCTURE_COPYBOOKS]


def _copybook_closure(root: Path) -> list[str]:
    """The in-scope copybook set: the COPY closure of the bridges plus the extra roots.

    Filtered to files that exist and declare at least one data item, which drops the
    environment-division and facade copybooks (they declare procedure text only) and
    `ACAS-SQLstate-error-list.cob`, which is absent from the frozen archive.
    """
    roots: set[str] = set(_EXTRA_COPYBOOK_ROOTS)
    for bridge in sorted(_BY_BRIDGE):
        for _number, name in _bridge_copies(root, bridge):
            roots.add(_copy_target(name))
    for _entity, _handler, _bridge, _tables, copybooks in _SPINE:
        roots.update(copybooks)

    seen: set[str] = set()
    pending = sorted(roots)
    while pending:
        rel = pending.pop(0)
        if rel in seen:
            continue
        seen.add(rel)
        if not (root / rel).is_file():
            continue
        for target in _copybook_copies(root, rel):
            if target not in seen:
                pending.append(target)
        pending.sort()
    return sorted(rel for rel in seen
                  if (root / rel).is_file() and _parse_copybook(root, rel))


def _resolve_record_names(root: Path, order: list[str]) -> dict[str, str | None]:
    """Give every copybook a record name, inheriting one where the file declares none.
    """
    own = {rel: next((item.name for item in _parse_copybook(root, rel)
                      if item.level == "01"), None) for rel in order}
    parents: dict[str, list[str]] = {}
    for rel in order:
        for child in _copybook_copies(root, rel):
            parents.setdefault(child, []).append(rel)
    changed = True
    while changed:
        changed = False
        for rel in order:
            if own[rel] is not None:
                continue
            for parent in sorted(parents.get(rel, ())):
                if own.get(parent):
                    own[rel] = own[parent]
                    changed = True
                    break
    for rel in order:
        for item in _parse_copybook(root, rel):
            if item.record is None:
                item.record = own[rel]
    return own


_NON_PARAGRAPH: Final[frozenset[str]] = frozenset("""
identification environment data procedure configuration input-output file working-storage
local-storage linkage report screen communication program-id author date-written security
installation date-compiled remarks exit continue goback stop else
end-if end-perform end-read end-evaluate end-string end-add end-subtract end-multiply
end-divide end-compute end-call end-search end-unstring end-start end-write end-rewrite
end-delete end-accept end-display end-return end-invoke end-exec end-of-page
""".split())
_PARAGRAPH_RE: Final[re.Pattern[str]] = re.compile(
    r"^ {0,7}([A-Za-z][A-Za-z0-9-]*)(\s+(?i:section))?\s*\."
)
_DIRECTIVE_OPEN: Final[str] = "/MYSQL VAR\\"
_DIRECTIVE_CLOSE: Final[str] = "/MYSQL-END\\"
_DIRECTIVE_TABLE_RE: Final[re.Pattern[str]] = re.compile(
    r"^TABLE=([A-Z][A-Z0-9-]*),(HV[0-9]?)\s*$", re.IGNORECASE
)
_DIRECTIVE_BASE_RE: Final[re.Pattern[str]] = re.compile(r"^BASE=(\S+)\s*$", re.IGNORECASE)
_KEY_TABLE_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*01\s+table-of-keynames\s*\.\s*$", re.IGNORECASE
)
_KEY_FILLER_RE: Final[re.Pattern[str]] = re.compile(
    r"""^\s*\d\d\s+filler\s+pic\s+(?:x\((\d+)\)|(x+))\s+value\s+("([^"]*)"|'([^']*)')\s*\.\s*$""",
    re.IGNORECASE,
)
_TD_GROUP_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*01\s+(TD-[A-Z][A-Z0-9-]*)\s*\.\s*$", re.IGNORECASE
)
_HOST_VARIABLE_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*\d\d\s+(HV[0-9]?-[A-Za-z0-9-]+)\s+(?:PIC|PICTURE)\s+(\S+?)\s*"
    r"(COMP-3|COMP-5|COMP|BINARY-LONG|BINARY-SHORT|BINARY-CHAR|DISPLAY)?\s*\.\s*$",
    re.IGNORECASE,
)
_MOVE_INTO_HV_RE: Final[re.Pattern[str]] = re.compile(
    r"(?i)\bmove\s+(.+?)\s+to\s+(HV[0-9]?-[A-Za-z0-9-]+)\s*\.?\s*$"
)
_MOVE_OUT_OF_HV_RE: Final[re.Pattern[str]] = re.compile(
    r"(?i)\bmove\s+(HV[0-9]?-[A-Za-z0-9-]+)(\s*\([^)]*\))?\s+to\s+(.+?)\s*\.?\s*$"
)
#: The `INITIALIZE` of a host-variable group that precedes its load, in EITHER SPELLING.
_INITIALIZE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?i)^\s*initiali[sz]e\s+(TD-[A-Z0-9-]+)\s*\.?\s*$"
)


def _paragraphs(lines: list[str]) -> list[tuple[int, str]]:
    """Every paragraph and section header in a bridge, as (physical line, name)."""
    out: list[tuple[int, str]] = []
    for number, raw in enumerate(lines, 1):
        code, _ = _strip_comment(raw)
        found = _PARAGRAPH_RE.match(code.rstrip())
        if found and found.group(1).lower() not in _NON_PARAGRAPH:
            out.append((number, found.group(1)))
    return out


def _paragraph_span(paragraphs: list[tuple[int, str]], start: int,
                    total: int) -> tuple[int, int]:
    """The line range a paragraph owns: its header through the line before the next."""
    for number, _name in paragraphs:
        if number > start:
            return start, number - 1
    return start, total


def _owning_paragraph(paragraphs: list[tuple[int, str]],
                      line: int) -> tuple[int, str] | None:
    """The paragraph a given physical line belongs to."""
    current: tuple[int, str] | None = None
    for number, name in paragraphs:
        if number <= line:
            current = (number, name)
        else:
            break
    return current


def _parse_scb(root: Path, bridge: str) -> tuple[str, str, list[dict[str, str]],
                                                 list[model.BridgeKey], str]:
    r"""Read a bridge source: its base, its tables, its key metadata and the locators.

    The directive block is anchored on a column-1 `/MYSQL VAR\` that CONTAINS a `BASE=`
    line, and a table line must carry the `,HV` or `,HV1` suffix. That precision is
    necessary rather than fussy.
    """
    rel = "common/%s.scb" % bridge
    lines = _read_lines(root, rel)
    base = ""
    tables: list[dict[str, str]] = []
    directive_source = ""
    for number, raw in enumerate(lines, 1):
        if not raw.startswith(_DIRECTIVE_OPEN):
            continue
        end = number
        while end <= len(lines) and not lines[end - 1].startswith(_DIRECTIVE_CLOSE):
            end += 1
        if end > len(lines):
            continue
        body = [text.strip() for text in lines[number:end - 1]]
        if not any(_DIRECTIVE_BASE_RE.match(text) for text in body):
            continue
        for text in body:
            found = _DIRECTIVE_BASE_RE.match(text)
            if found:
                base = found.group(1)
            found = _DIRECTIVE_TABLE_RE.match(text)
            if found:
                name = found.group(1).upper()
                tables.append({"name": name,
                               "hv_group_suffix": found.group(2).upper(),
                               "hv_group_name": "TD-" + name})
        directive_source = "%s:L%d-L%d" % (rel, number, end)
        break

    keys: list[model.BridgeKey] = []
    for number, raw in enumerate(lines, 1):
        code, _ = _strip_comment(raw)
        if not _KEY_TABLE_RE.match(code):
            continue
        triple: list[tuple[int, str]] = []
        ahead = number + 1
        while ahead <= len(lines):
            code_ahead, _ = _strip_comment(lines[ahead - 1])
            if re.match(r"^\s*01\s", code_ahead):
                break
            found = _KEY_FILLER_RE.match(code_ahead)
            if found:
                value = found.group(4) if found.group(4) is not None else found.group(5)
                triple.append((ahead, value))
                if len(triple) == 3:
                    offsets = triple[1][1]
                    keys.append(model.BridgeKey(
                        name_in_rdb=triple[0][1].rstrip(),
                        offset=int(offsets[:4]),
                        length=int(offsets[4:8]),
                        type=triple[2][1].strip(),
                        source="%s:L%d-L%d" % (rel, triple[0][0], triple[2][0]),
                    ))
                    triple = []
            ahead += 1
        break
    return rel, base, tables, keys, directive_source


def _transfer_paragraphs(
    root: Path, bridge: str, tables: list[dict[str, str]]
) -> tuple[dict[tuple[str, str], tuple[int, str] | None],
           dict[tuple[str, str], tuple[int, int] | None], set[str]]:
    """Find the load and unload paragraph for each host-variable group of one bridge.

    Four in-scope bridges - dfltMT, finalMT, irsdfltMT and irsfinalMT - have no
    dedicated `bb000-HV-Load` section at all.
    """
    lines = _read_lines(root, "common/%s.cbl" % bridge)
    paragraphs = _paragraphs(lines)
    moves: list[tuple[int, str, str, str]] = []
    for number, raw in enumerate(lines, 1):
        code, _ = _strip_comment(raw)
        text = code.strip()
        found = _MOVE_OUT_OF_HV_RE.search(text)
        if found:
            moves.append((number, "U", found.group(1).upper(), found.group(3)))
            continue
        found = _MOVE_INTO_HV_RE.search(text)
        if found:
            moves.append((number, "L", found.group(2).upper(), found.group(1)))

    tally: dict[tuple[str, str], Counter[tuple[int, str]]] = {}
    for number, direction, name, _operand in moves:
        owner = _owning_paragraph(paragraphs, number)
        if owner is None:
            continue
        prefix = name.split("-", 1)[0]
        tally.setdefault((prefix, direction), Counter())[owner] += 1

    chosen: dict[tuple[str, str], tuple[int, str] | None] = {}
    spans: dict[tuple[str, str], tuple[int, int] | None] = {}
    for slot, counts in tally.items():
        winner = max(counts.items(), key=lambda pair: (pair[1], -pair[0][0]))[0]
        chosen[slot] = winner
        spans[slot] = _paragraph_span(paragraphs, winner[0], len(lines))
    for prefix in {name.split("-", 1)[0] for _n, _d, name, _o in moves}:
        for direction in ("L", "U"):
            chosen.setdefault((prefix, direction), None)
            spans.setdefault((prefix, direction), None)

    group_names = {table["hv_group_name"].upper() for table in tables}
    initialised: set[str] = set()
    for number, raw in enumerate(lines, 1):
        code, _ = _strip_comment(raw)
        found = _INITIALIZE_RE.match(code)
        if found is None:
            continue
        group = found.group(1).upper()
        if group not in group_names:
            continue
        suffix = next(table["hv_group_suffix"] for table in tables
                      if table["hv_group_name"].upper() == group)
        span = spans.get((suffix, "L"))
        if span and span[0] <= number <= span[1]:
            initialised.add(group)
    return chosen, spans, initialised


class _HostVariable:
    """One host variable plus the parse state the join and the derivation need."""

    __slots__ = ("view", "table", "load_line", "load_operand", "unload_operand",
                 "load_span")


def _parse_host_variables(root: Path, bridge: str, tables: list[dict[str, str]],
                          spans: dict[tuple[str, str], tuple[int, int] | None],
                          initialised: set[str]) -> list["_HostVariable"]:
    """Read a generated bridge's host-variable groups and their load and unload moves.

    Host-variable pictures are UPPER CASE in the generated bridges while copybook
    pictures are lower case; both are stored exactly as written and only compared case-
    insensitively.
    """
    rel = "common/%s.cbl" % bridge
    lines = _read_lines(root, rel)
    by_group = {table["hv_group_name"].upper(): table for table in tables}

    loads: dict[str, tuple[int, str]] = {}
    unloads: dict[str, tuple[int, str]] = {}
    for number, raw in enumerate(lines, 1):
        code, _ = _strip_comment(raw)
        text = code.strip()
        found = _MOVE_OUT_OF_HV_RE.search(text)
        direction, name, operand = None, None, None
        if found:
            direction, name, operand = "U", found.group(1).upper(), found.group(3)
        else:
            found = _MOVE_INTO_HV_RE.search(text)
            if found:
                direction, name, operand = "L", found.group(2).upper(), found.group(1)
        if direction is None or name is None or operand is None:
            continue
        span = spans.get((name.split("-", 1)[0], direction))
        if not span or not span[0] <= number <= span[1]:
            continue
        # First occurrence wins.
        (loads if direction == "L" else unloads).setdefault(name, (number, operand))

    out: list[_HostVariable] = []
    current: dict[str, str] | None = None
    for number, raw in enumerate(lines, 1):
        code, _ = _strip_comment(raw)
        found = _TD_GROUP_RE.match(code)
        if found:
            current = by_group.get(found.group(1).upper())
            continue
        if re.match(r"^\s*01\s", code):
            current = None
        found = _HOST_VARIABLE_RE.match(code)
        if found is None or current is None:
            continue
        name = found.group(1).upper()
        picture = found.group(2)
        usage = (found.group(3) or "").upper()
        if not usage:
            usage = "ALPHANUMERIC" if re.search(r"[xXaA]", picture) else "DISPLAY"
        symbols = _expand_picture(picture).upper()
        digits = integer_digits = scale = character_length = None
        signed = False
        if "9" in symbols:
            head, tail = symbols.split("V", 1) if "V" in symbols else (symbols, "")
            integer_digits = head.count("9")
            scale = tail.count("9")
            digits = integer_digits + scale
            signed = symbols.startswith("S")
        else:
            character_length = len(symbols.replace("S", ""))
        loaded = loads.get(name)
        unloaded = unloads.get(name)
        record = _HostVariable()
        record.table = current["name"]
        record.load_line = loaded[0] if loaded else None
        record.load_operand = loaded[1] if loaded else None
        record.unload_operand = unloaded[1] if unloaded else None
        record.load_span = spans.get((current["hv_group_suffix"], "L"))
        record.view = model.BridgeHostVariable(
            file=rel,
            source="%s:L%d" % (rel, number),
            hv_group_name=current["hv_group_name"],
            hv_group_suffix=current["hv_group_suffix"],
            name=name,
            picture=picture,
            usage=model.Usage(usage),
            signed=signed,
            digits=digits,
            integer_digits=integer_digits,
            scale=scale,
            character_length=character_length,
            loaded_from_record=loaded is not None,
            load_source=("%s:L%d" % (rel, loaded[0])) if loaded else None,
            unloaded_to_record=unloaded is not None,
            unload_source=("%s:L%d" % (rel, unloaded[0])) if unloaded else None,
            group_initialised_before_load=current["hv_group_name"].upper() in initialised,
        )
        out.append(record)
    return out


#: Figurative constants a load move may name instead of a record field. They carry no
#: field, so they are never a binding candidate.
_FIGURATIVE: Final[frozenset[str]] = frozenset("""zero zeros zeroes space spaces
high-value high-values low-value low-values quote quotes all null nulls""".split())
_REFERENCE_MODIFICATION_RE: Final[re.Pattern[str]] = re.compile(r"\(\s*\d+\s*:")
_LEADING_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^([A-Za-z][A-Za-z0-9-]*)")
_TRAILING_INDEX_RE: Final[re.Pattern[str]] = re.compile(r"^(.*)-(\d+)$")


def _table_copybooks(root: Path, table: str) -> list[str]:
    """The copybooks a table's fields may come from, by path.

    Both the spine's own naming and the bridge's actual COPY are listed. They diverge
    for two entities and the divergence is disclosed rather than resolved.
    """
    bridge, _handler, _entity, spine_copybooks = _BY_TABLE[table]
    out = set(spine_copybooks)
    for _number, name in _bridge_record_copies(root, bridge):
        out.add(_copy_target(name))
    return sorted(out)


def _data_name(operand: str | None) -> str | None:
    """The bare data name a move operand refers to, or None if it names no field.

    A reference modification such as `Post-Date (1:2)` is deliberately rejected: it
    derives a new value from part of a field rather than carrying that field, which is
    exactly why the three IRS date components correctly have no copybook view.
    """
    if operand is None:
        return None
    text = operand.strip()
    if _REFERENCE_MODIFICATION_RE.search(text):
        return None
    found = _LEADING_NAME_RE.match(text)
    if found is None:
        return None
    name = found.group(1)
    return None if name.lower() in _FIGURATIVE else name


def _spelling_variants(name: str) -> list[str]:
    """The spellings of one name the frozen sources themselves evidence.

    Each substitution is present in the checkout rather than invented.
    """
    out: list[str] = []
    seen: set[str] = set()

    def add(candidate: str | None) -> None:
        if candidate and candidate.upper() not in seen:
            seen.add(candidate.upper())
            out.append(candidate)

    add(name)
    index = 0
    while index < len(out):
        current = out[index]
        upper = current.upper()
        if upper.startswith("WS-"):
            add(current[3:])
        else:
            add("WS-" + current)
        if upper.endswith("-DAT"):
            add(current + "E")
        if "TIPE" in upper:
            add(re.sub("(?i)tipe", "Type", current))
        if upper.startswith("OI3-") or upper.startswith("OI5-"):
            add("OI-" + current[4:])
        index += 1
    return out


def _bind(host: "_HostVariable", column_name: str,
          pool: list["_CopybookItem"]) -> tuple["_CopybookItem | None", int | None]:
    """Bind a host variable to the copybook field it carries."""
    index: dict[str, list[_CopybookItem]] = {}
    for item in pool:
        index.setdefault(item.name.upper(), []).append(item)

    candidates: list[str] = []
    for candidate in (_data_name(host.load_operand), _data_name(host.unload_operand),
                      host.view.name.split("-", 1)[1], column_name):
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        for spelling in _spelling_variants(candidate):
            found = index.get(spelling.upper())
            if found:
                return found[0], None

    for candidate in candidates:
        split = _TRAILING_INDEX_RE.match(candidate)
        if split is None:
            continue
        base, occurrence = split.group(1), int(split.group(2))
        for spelling in _spelling_variants(base):
            found = index.get(spelling.upper())
            if found and found[0].occurs and found[0].occurs >= occurrence:
                return found[0], occurrence
            suffix = "-" + spelling.upper()
            for item in pool:
                if (item.name.upper().endswith(suffix) and item.occurs
                        and item.occurs >= occurrence):
                    return item, occurrence
    return None, None


def _column_arithmetic(column: model.MysqlColumn | None) -> tuple[
        bool | None, int | None, int | None, int | None, int | None]:
    """The column's (signed, digits, integer digits, scale, character length).

    A CHAR column states a width and says nothing about sign or digits. A DECIMAL
    column's precision and scale ARE its digit counts. Every other numeric column states
    only whether it is unsigned. All integer work (R-2).
    """
    if column is None:
        return None, None, None, None, None
    if column.base_type is model.SqlBaseType.CHAR:
        return None, None, None, None, column.display_width
    signed = not column.unsigned
    if column.base_type is model.SqlBaseType.DECIMAL:
        precision = column.display_width or 0
        scale = column.scale or 0
        return signed, precision, precision - scale, scale, None
    return signed, None, None, None, None


def _storage_of(view: model.CopybookField | None) -> model.CobolPythonStorage:
    """Choose the Python storage class from the DECLARING COBOL view alone.

    The declaring view is the copybook view where there is one, and the program-source
    view for a work-file field that no copybook declares.
    """
    if view is None or view.usage is model.Usage.GROUP:
        return model.CobolPythonStorage.NONE
    if view.usage is model.Usage.ALPHANUMERIC:
        return model.CobolPythonStorage.STR
    if view.scale:
        return model.CobolPythonStorage.DECIMAL
    return model.CobolPythonStorage.INT


_NO_DRIFT: Final[model.Drift] = model.Drift(
    signedness=False, usage=False, digits=False, scale=False, character_length=False,
    name=False, details=(),
)


def _drift_of(copybook: model.CopybookField | None,
              host: model.BridgeHostVariable | None,
              column: model.MysqlColumn | None) -> model.Drift:
    """Compare the views that are present and record every disagreement found.

    Detection is by comparison and never from a list of known cases, which is why the
    dictionary finds signedness narrowing in `copybooks/wsbatch.cob` as well as in the
    documented `copybooks/wssl.cob`. A flag records a disagreement; it never resolves
    one.
    """
    if copybook is None or host is None:
        return _NO_DRIFT
    signedness = usage = digits = scale = character_length = name = False
    details: list[str] = []
    col_signed, col_digits, col_int, col_scale, col_width = _column_arithmetic(column)
    group = copybook.usage is model.Usage.GROUP

    known_signs = [copybook.signed, host.signed]
    if col_signed is not None:
        known_signs.append(col_signed)
    if not group and len(set(known_signs)) > 1:
        signedness = True
        word = {True: "signed", False: "unsigned"}
        sentence = ("Signedness disagrees: copybook says %s, bridge host variable says %s"
                    % (word[copybook.signed], word[host.signed]))
        if col_signed is not None:
            sentence += ", column says %s" % word[col_signed]
        details.append(sentence + ".")

    if not group and copybook.usage != host.usage:
        usage = True
        details.append(
            "Storage class changes at the bridge: copybook declares %s, host variable "
            "declares %s, column is %s."
            % (copybook.usage, host.usage, column.base_type if column else "none"))

    pairs = [pair for pair in ((copybook.digits, copybook.integer_digits),
                               (host.digits, host.integer_digits)) if pair[0] is not None]
    column_pair = (col_digits, col_int) if col_digits is not None else None
    if column_pair is not None:
        pairs.append(column_pair)
    if len(pairs) > 1 and len(set(pairs)) > 1:
        digits = True
        segments: list[str] = []
        if copybook.digits is not None:
            segments.append("copybook has %d digits (%d integer)"
                            % (copybook.digits, copybook.integer_digits or 0))
        if host.digits is not None:
            segments.append("bridge host variable has %d digits (%d integer)"
                            % (host.digits, host.integer_digits or 0))
        if column_pair is not None:
            segments.append("column has %d digits (%d integer)" % column_pair)
        details.append("Digit count disagrees: " + ", ".join(segments) + ".")

    scales = [value for value in (copybook.scale, host.scale) if value is not None]
    if col_scale is not None:
        scales.append(col_scale)
    if len(scales) > 1 and len(set(scales)) > 1:
        scale = True
        segments = []
        if copybook.scale is not None:
            segments.append("copybook has %d" % copybook.scale)
        if host.scale is not None:
            segments.append("bridge host variable has %d" % host.scale)
        if col_scale is not None:
            segments.append("column has %d" % col_scale)
        details.append("Scale disagrees: " + ", ".join(segments) + " fractional digits.")

    widths = [value for value in (copybook.character_length, host.character_length)
              if value is not None]
    if col_width is not None:
        widths.append(col_width)
    if len(widths) > 1 and len(set(widths)) > 1:
        character_length = True
        segments = []
        if copybook.character_length is not None:
            segments.append("copybook is %d characters wide" % copybook.character_length)
        if host.character_length is not None:
            segments.append("bridge host variable is %d characters wide"
                            % host.character_length)
        if col_width is not None:
            segments.append("column is %d characters wide" % col_width)
        details.append("Character length disagrees: " + ", ".join(segments)
                       + ". The value is not corrupted but the padding differs, which "
                         "is visible in a table dump.")

    stripped = host.name.split("-", 1)[1]
    names = [copybook.name, stripped] + ([column.name] if column else [])
    if len({value.upper() for value in names}) > 1:
        name = True
        sentence = ("Name differs across views: copybook calls it %s, bridge host "
                    "variable calls it %s" % (copybook.name, stripped))
        if column:
            sentence += ", column calls it %s" % column.name
        details.append(sentence + ".")

    return model.Drift(signedness=signedness, usage=usage, digits=digits, scale=scale,
                       character_length=character_length, name=name,
                       details=tuple(details))


_IF_RE: Final[re.Pattern[str]] = re.compile(r"(?i)^if\b")
_CONDITION_CONTINUATION_RE: Final[re.Pattern[str]] = re.compile(r"(?i)^(and|or)\b")

_GUARD_FAILS_THEN: Final[str] = (
    "When the condition does not hold the move is not made, so the host variable keeps "
    "the value left by the INITIALIZE of its group - zero for a numeric, space for a "
    "character - while the rest of the row is still written."
)
_GUARD_FAILS_ELSE: Final[str] = (
    "This move is in the ELSE branch, so it is made precisely when the condition does "
    "NOT hold; when the condition does hold the move is not made and the host variable "
    "keeps the value left by the INITIALIZE of its group."
)
_GUARD_FAILS_SPLIT: Final[str] = (
    " The whole field is stored separately in %s, so a row whose guard failed carries "
    "the raw text there and a zero here: internally inconsistent, and reproduced as "
    "such rather than repaired (R-4)."
)


def _guard_context(root: Path, rel: str,
                   span: tuple[int, int]) -> dict[int, tuple[int, str, str]]:
    """Map each line inside a conditional to (IF line, condition text, branch).

    A conditional in a load paragraph is opened by IF, its condition may continue on
    following AND / OR lines, ELSE switches branch, and it closes on either END-IF or
    the terminating period of a statement.
    """
    lines = _read_lines(root, rel)
    low, high = span
    inside: dict[int, tuple[int, str, str]] = {}
    stack: list[list[object]] = []
    number = low
    while number <= high:
        code, _ = _strip_comment(lines[number - 1])
        text = code.strip()
        if not text:
            number += 1
            continue
        lowered = text.lower()
        if _IF_RE.match(text):
            condition = text
            ahead = number + 1
            while ahead <= high:
                next_code, _ = _strip_comment(lines[ahead - 1])
                next_text = next_code.strip()
                if not next_text:
                    ahead += 1
                    continue
                if not _CONDITION_CONTINUATION_RE.match(next_text):
                    break
                condition += " " + next_text
                ahead += 1
            closes = condition.rstrip().endswith(".")
            stack.append([number, _collapse(condition).rstrip("."), "THEN"])
            if closes:
                stack.pop()
            number = ahead
            continue
        if lowered in ("else", "else."):
            if stack:
                stack[-1][2] = "ELSE"
            number += 1
            continue
        if lowered.startswith("end-if"):
            if stack:
                stack.pop()
            if lowered.endswith("."):
                stack.clear()
            number += 1
            continue
        if stack:
            inside[number] = (int(stack[-1][0]), str(stack[-1][1]), str(stack[-1][2]))
        if text.endswith("."):
            stack.clear()
        number += 1
    return inside


def _move_text(root: Path, rel: str, line: int, host_name: str) -> str:
    """The move statement as one line of text, with the host-variable name canonicalised.

    Only the single physical line carrying the move is quoted, so a multi-destination
    move keeps just its own destination.
    """
    code, _ = _strip_comment(_read_lines(root, rel)[line - 1])
    return re.sub(r"(?i)\b" + re.escape(host_name) + r"\b", host_name, _collapse(code))


def _redefines_lineage(root: Path, rel: str, item: "_CopybookItem") -> bool:
    """True when any enclosing group of this item REDEFINES other storage."""
    key = (str(root), rel)
    cached = _LINEAGE_CACHE.get(key)
    if cached is None:
        cached = {}
        stack: list[_CopybookItem] = []
        for candidate in _parse_copybook(root, rel):
            while stack and int(stack[-1].level) >= int(candidate.level):
                stack.pop()
            cached[(candidate.line, candidate.name)] = any(
                ancestor.redefines is not None for ancestor in stack)
            stack.append(candidate)
        _LINEAGE_CACHE[key] = cached
    return cached[(item.line, item.name)]


def _derivation_of(root: Path, table: str, copybook: model.CopybookField | None,
                   item: "_CopybookItem | None", host: "_HostVariable",
                   column: model.MysqlColumn | None,
                   sibling_columns: dict[tuple[str, str], str]) -> model.Derivation | None:
    """Describe how the bridge produces a column no field simply carries, or None.

    Kind precedence, established by reading every case in the frozen sources: 1. no
    copybook field at all -> BRIDGE_DERIVED 2. a whole copybook group moved into one ->
    GROUP_CONCATENATION 3.
    """
    if column is None:
        return None
    span = host.load_span
    guarded = _guard_context(root, host.view.file, span) if span else {}
    line = host.load_line
    guard_line: int | None = None
    condition: str | None = None
    branch: str | None = None
    if line is not None and line in guarded:
        guard_line, condition, branch = guarded[line]

    if copybook is None:
        kind = model.DerivationKind.BRIDGE_DERIVED
    elif copybook.is_group:
        kind = model.DerivationKind.GROUP_CONCATENATION
    elif copybook.redefines is not None or (
            item is not None and _redefines_lineage(root, copybook.file, item)):
        kind = model.DerivationKind.REDEFINES_ALTERNATIVE
    elif condition is not None:
        kind = model.DerivationKind.BRIDGE_DERIVED
    else:
        return None

    if line is None:
        # Declared and never loaded. `common/plinvoiceMT.cbl:L408-L412` declares five
        # invoice-status host variables the load paragraph never writes to.
        return model.Derivation(
            kind=kind,
            expression="%s is declared but the load paragraph makes no move into it"
                       % host.view.name,
            guard=None,
            guard_failure_behaviour=None,
            source=host.view.source,
        )

    expression = _move_text(root, host.view.file, line, host.view.name)
    if condition is None:
        return model.Derivation(kind=kind, expression=expression.rstrip("."), guard=None,
                               guard_failure_behaviour=None,
                               source="%s:L%d" % (host.view.file, line))
    behaviour = _GUARD_FAILS_ELSE if branch == "ELSE" else _GUARD_FAILS_THEN
    operand = host.load_operand or ""
    if branch != "ELSE" and _REFERENCE_MODIFICATION_RE.search(operand):
        base = _LEADING_NAME_RE.match(operand.strip())
        sibling = sibling_columns.get((table, base.group(1).upper())) if base else None
        if sibling:
            behaviour += _GUARD_FAILS_SPLIT % sibling
    return model.Derivation(kind=kind, expression=expression, guard=condition,
                           guard_failure_behaviour=behaviour,
                           source="%s:L%d-L%d" % (host.view.file, guard_line, line))


# STAGE 4b - notes, anomaly references and ambiguity references Notes are composed
# mechanically from the facts already gathered and never editorially.
#
# EMISSION POLICY. A note is emitted only where it carries a fact that NO structured
# member of the entry already carries. Every general derivation rule lives once in
# meta.derivation_rules, never once per entry: presence and the copybook-only taxonomy
# in presence_and_one_sided, the measured effect of signedness narrowing in
# drift_detection, group-declared storage in usage_inheritance, and the inline
# work-file records in program_source_entries. So there is no note restating that a
# field reaches no column (presence and one_sided say it), that it is a FILLER, a
# REDEFINES view or a group (is_filler, redefines - directly or through a redefining
# ancestor reachable by parent_group - and is_group say it), that its storage class was
# inherited (usage_declared_at, usage_inherited_from and usage_group_source say it, with
# a source locator the prose did not carry), or which condition names it declares
# (condition_names says it, with a locator per name).

_WARNING_RE: Final[re.Pattern[str]] = re.compile(r"(?i)\bwarning\b")

_NOTE_SIGN_LOST: Final[str] = (
    "Signed in the copybook and unsigned in the bridge host variable, so this field "
    "loses the sign of a negative value at the bridge, before any SQL runs, and not at "
    "the database. MEASURED against GnuCOBOL 3.2.0 (question Q-3, resolved); "
    "meta.derivation_rules.drift_detection carries the measured store. That is anomaly "
    "A-11, reproduced rather than corrected."
)
_NOTE_NOT_UNLOADED: Final[str] = (
    "%s is never moved back into the record after a read, so a value read from the "
    "database does not reach the caller through this host variable."
)
_NOTE_NOT_LOADED: Final[str] = (
    "%s is declared in %s at %s but the load paragraph of %s makes no move into it, so "
    "nothing from the passed record reaches it."
)
_NOTE_NOT_INITIALISED: Final[str] = (
    "%s issues no INITIALIZE of %s before loading it, unlike the bridges that use a "
    "dedicated bb000-HV-Load section."
)
_NOTE_DDL_COMMENT: Final[str] = 'The column carries the DDL comment "%s".'
_NOTE_COLUMN_DEFAULT: Final[str] = (
    "The column declares DEFAULT %s - the only column-level default in the in-scope part "
    "of the frozen dump."
)
_NOTE_VARIANT: Final[str] = (
    "%s declares an identical item at the same line; the two copybooks are variants of "
    "one layout and this entry cites %s, the first in path order."
)
_NOTE_OCCURS: Final[str] = (
    "The copybook declares %s once with OCCURS %d at %s; the bridge flattens the array "
    "into separately named host variables and columns, and this entry is occurrence %d."
)
_NOTE_SIGN_CLAUSE: Final[str] = (
    'The copybook writes the sign clause as "%s"; the spelling is preserved exactly as '
    "declared and is not normalised against the other spelling used elsewhere."
)
_NOTE_SCB_DOUBT: Final[str] = (
    "The bridge source records the maintainer's own doubt about this column at %s: \"%s\" "
    "It is quoted because it is evidence about the frozen source, and it is left "
    "unresolved here."
)
_NOTE_GUARD_COMMENT: Final[str] = (
    "The bridge carries the maintainer's own comment immediately above this guard: \"%s\""
)
_NOTE_FRAGMENT: Final[str] = (
    "%s is a single-declaration COPY fragment that %s textually includes into its %s record."
)
_NOTE_PROGRAM_SOURCE_REPEAT: Final[str] = (
    "%s declares a record named %s at %s as well. The two are separate physical "
    "declarations rather than two spellings of one, so both are recorded and this entry's "
    "key carries its own declaration line to keep them apart."
)
_NOTE_PROGRAM_SOURCE_GROUP: Final[str] = (
    "This group exists in this declaration alone: %s declares the same record without it "
    "and carries the subordinate items flat at the group's own level instead. Both shapes "
    "are recorded and neither is harmonised against the other (R-4)."
)

#: Notes are emitted in this fixed order so the document is byte-reproducible (R-6).
_NOTE_ORDER: Final[tuple[str, ...]] = (
    "PROGRAM_SOURCE", "SIGN_LOST",
    "NOT_LOADED", "NOT_UNLOADED", "NOT_INITIALISED", "DDL_COMMENT", "COLUMN_DEFAULT",
    "GUARD_COMMENT", "SCB_DOUBT", "OCCURS",
    "SIGN_CLAUSE", "VARIANT", "FRAGMENT",
)


class _EntryDraft:
    """One dictionary entry under construction, with its private bookkeeping.

    The bookkeeping members - the copybook item the entry resolved to, its occurrence
    number, its duplicate signature and its copybook's own notes - are what the later
    stages need and are never emitted.
    """

    __slots__ = ("key", "table", "bridge", "handler", "entity_facade", "presence",
                 "one_sided", "copybook", "program_source", "host", "column", "drift",
                 "derivation", "storage", "notes", "anomaly_refs", "ambiguity_refs",
                 "item", "occurrence", "signature", "copybook_notes")

    def __init__(self, **members: object) -> None:
        for name in self.__slots__:
            setattr(self, name, members.get(name))

    def entry(self) -> model.DictionaryEntry:
        """The immutable, emittable entry."""
        return model.DictionaryEntry(
            key=str(self.key),
            table=self.table,
            bridge=self.bridge,
            handler=self.handler,
            entity_facade=(None if self.entity_facade is None
                           else model.EntityFacade(self.entity_facade)),
            presence=self.presence,
            one_sided=bool(self.one_sided),
            copybook=self.copybook,
            program_source=self.program_source,
            bridge_host_variable=None if self.host is None else self.host.view,
            column=self.column,
            drift=self.drift,
            derivation=self.derivation,
            cobol_python_storage=self.storage,
            notes=tuple(self.notes or ()),
            anomaly_refs=tuple(self.anomaly_refs or ()),
            ambiguity_refs=tuple(self.ambiguity_refs or ()),
        )


def _scb_warnings(
    root: Path, bridge: str, table_columns: dict[str, list[str]]
) -> dict[tuple[str, str], list[tuple[str, str]]]:
    """Maintainer WARNING comments in the .scb that name a column of one of its tables.

    `common/glpostingMT.scb:L229` doubts aloud whether the declared key should be a
    different column. It is quoted as evidence and acted upon nowhere (R-4, R-6).
    """
    rel = "common/%s.scb" % bridge
    found: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for number, raw in enumerate(_read_lines(root, rel), 1):
        code, comment = _strip_comment(raw)
        if code.strip() or not comment.strip() or not _WARNING_RE.search(comment):
            continue
        text = _collapse(comment)
        for table in sorted(table_columns):
            for column in table_columns[table]:
                boundary = r"(?<![A-Za-z0-9-])" + re.escape(column) + r"(?![A-Za-z0-9-])"
                if re.search(boundary, text, re.IGNORECASE):
                    found.setdefault((table, column), []).append(
                        ("%s:L%d" % (rel, number), text))
    return found


def _comment_block_above(root: Path, rel: str, line: int) -> str:
    """The contiguous run of comment-only lines immediately above `line`, joined."""
    lines = _read_lines(root, rel)
    parts: list[str] = []
    number = line - 1
    while number >= 1:
        code, comment = _strip_comment(lines[number - 1])
        if code.strip():
            break
        body = _collapse(comment)
        if body:
            parts.append(body)
        number -= 1
    parts.reverse()
    return " ".join(parts)


def _odd_prefix_fields(root: Path, rel: str) -> set[tuple[int, str]]:
    """Fields whose name prefix belongs to a sibling group rather than their own.

    `copybooks/wssys4.cob:L29-L30` declares sl4-spare3 and sl4-spare4 inside Purchase-
    Ledger-Data while every other member of that group is pl-prefixed. That is anomaly
    A-20; the fields are recorded under the group that really declares them and are
    never renamed (R-4).
    """
    key = (str(root), rel)
    cached = _ODD_PREFIX_CACHE.get(key)
    if cached is not None:
        return cached
    items = _parse_copybook(root, rel)
    members: dict[str, list[_CopybookItem]] = {}
    parent_of_group: dict[str, str] = {}
    stack: list[_CopybookItem] = []
    for item in items:
        while stack and int(stack[-1].level) >= int(item.level):
            stack.pop()
        if stack:
            members.setdefault(stack[-1].name, []).append(item)
            if item.is_group:
                parent_of_group[item.name] = stack[-1].name
        stack.append(item)

    def dominant(group: str) -> str | None:
        """The name prefix a strict majority of the group's own members share.

        A weak plurality is not evidence of a naming convention.
        `copybooks/wssystem.cob` declares heterogeneous blocks whose commonest prefix
        covers a small minority of members, and reading those as conventions would
        manufacture anomalies that the frozen source does not contain.
        """
        counts = Counter(x.name.split("-", 1)[0].lower() for x in members.get(group, ())
                         if not x.is_filler and "-" in x.name)
        if not counts:
            return None
        prefix, hits = counts.most_common(1)[0]
        return prefix if hits > 1 and hits * 2 > sum(counts.values()) else None

    dominants = {group: dominant(group) for group in members}
    odd: set[tuple[int, str]] = set()
    for group in sorted(members):
        own = dominants.get(group)
        if not own:
            continue
        siblings = [other for other, parent in parent_of_group.items()
                    if parent == parent_of_group.get(group) and other != group
                    and dominants.get(other)]
        for item in members[group]:
            if item.is_filler or "-" not in item.name:
                continue
            prefix = item.name.split("-", 1)[0].lower().rstrip("0123456789")
            if prefix == own.rstrip("0123456789"):
                continue
            if any(prefix == str(dominants[other]).rstrip("0123456789") for other in siblings):
                odd.add((item.line, item.name))
    _ODD_PREFIX_CACHE[key] = odd
    return odd


def _notes_and_refs(root: Path, draft: _EntryDraft,
                    warnings: dict[tuple[str, str], list[tuple[str, str]]],
                    variants: dict[object, list[str]],
                    fragment_parents: dict[str, str]) -> None:
    """Fill in the entry's notes, anomaly references and ambiguity references."""
    copybook = draft.copybook
    host = draft.host
    column = draft.column
    item = draft.item
    bucket: dict[str, list[str]] = {}
    anomalies: list[str] = []
    ambiguities: list[str] = []

    def add(kind: str, text: str) -> None:
        bucket.setdefault(kind, []).append(text)

    if draft.program_source is not None:
        source = draft.program_source
        record = item.record
        # No note that the field is program-source: presence.in_program_source and
        # program_source.file say it, sources.program_sources carries the record's FD or
        # SD introducer and its record-level notes, and
        # meta.derivation_rules.program_source_entries states the rule once.
        siblings = _program_source_siblings(source.file, record)
        for other in siblings:
            add("PROGRAM_SOURCE", _NOTE_PROGRAM_SOURCE_REPEAT % (
                other, record, "%s:L%d" % (other, _program_source_span(other, record)[1])))
        if source.is_group and source.level != "01":
            for other in siblings:
                if all(peer.name.lower() != source.name.lower()
                       for peer in _parse_program_source(root, other, record)):
                    add("PROGRAM_SOURCE", _NOTE_PROGRAM_SOURCE_GROUP % other)
        if record in _ORDERING_CRITICAL_RECORDS:
            anomalies.append("A-14")
    elif column is not None:
        view = host.view
        # No note where no copybook declares the column: presence.in_copybook false with
        # in_bridge and in_column true says exactly that, derivation.kind is
        # BRIDGE_DERIVED, and meta.authority states once why the bridge is the
        # authoritative mapping. See derivation_rules.presence_and_one_sided.
        if draft.drift.signedness and copybook is not None:
            if copybook.signed and not view.signed:
                # Q-3 IS NO LONGER OPEN and is therefore no longer recorded as an
                # ambiguity. The compiled oracle was asked directly
                # what a negative value becomes in an unsigned host variable, and it
                # answered: the absolute value, truncated to the receiving digit
                # count. The note above carries the measurement.
                #
                # A-11 STAYS. The ambiguity was "what value results"; the ANOMALY is
                # "the sign is lost before SQL runs", and that is a reproduced defect
                # (rule R-4), not a question. Dropping it because the question was
                # answered would delete the finding along with the uncertainty.
                add("SIGN_LOST", _NOTE_SIGN_LOST)
                # A-11 stays: the sign loss is a reproduced defect, and measuring it
                # did not repair it. Q-3 does NOT stay - it was the question of WHAT
                # the unsigned column ends up holding, and that has been measured
                # end to end through the compiled bridge (absolute value, then
                # high-order truncation if the magnitude overflows). Rule R-6 makes
                # the measurement the answer, so continuing to publish Q-3 on these
                # entries would misreport a settled question as an open one.
                anomalies.append("A-11")
            # The other direction - unsigned in the copybook, signed at the bridge -
            # gets no note: drift.signedness and drift.details already name every view
            # and what each says, and neither is preferred or corrected (R-4).
        if not view.loaded_from_record:
            add("NOT_LOADED", _NOTE_NOT_LOADED % (view.name, view.hv_group_name,
                                                  view.source, draft.bridge))
        if not view.unloaded_to_record:
            add("NOT_UNLOADED", _NOTE_NOT_UNLOADED % view.name)
        if not view.group_initialised_before_load:
            add("NOT_INITIALISED", _NOTE_NOT_INITIALISED % (draft.bridge,
                                                            view.hv_group_name))
        if column.comment is not None:
            add("DDL_COMMENT", _NOTE_DDL_COMMENT % column.comment)
        if column.column_default is not None:
            add("COLUMN_DEFAULT", _NOTE_COLUMN_DEFAULT % column.column_default)
        derivation = draft.derivation
        if derivation is not None and derivation.guard is not None:
            guard_line = int(derivation.source.rsplit(":L", 1)[1].split("-L")[0])
            block = _comment_block_above(root, view.file, guard_line)
            if block:
                add("GUARD_COMMENT", _NOTE_GUARD_COMMENT % block)
        for locator, text in warnings.get((draft.table, column.name), ()):
            add("SCB_DOUBT", _NOTE_SCB_DOUBT % (locator, text))
            if not view.loaded_from_record:
                ambiguities.append("Q-6")
        if draft.occurrence is not None:
            add("OCCURS", _NOTE_OCCURS % (copybook.name, item.occurs, copybook.source,
                                          draft.occurrence))
        if draft.drift.character_length:
            anomalies.append("A-12")
        if (derivation is not None and copybook is None
                and derivation.kind is model.DerivationKind.BRIDGE_DERIVED
                and derivation.guard is not None):
            anomalies.append("A-7")

    if copybook is not None:
        # No note for condition names or for group-declared storage: condition_names
        # carries every 88-level with its own locator, and usage, usage_declared_at,
        # usage_inherited_from and usage_group_source carry the inheritance with the
        # declaring group's line. Prose would restate both with less information.
        if copybook.sign_clause_text is not None:
            add("SIGN_CLAUSE", _NOTE_SIGN_CLAUSE % copybook.sign_clause_text)
        if column is None:
            others = [path for path in variants.get(draft.signature, ())
                      if path != copybook.file]
            if others:
                add("VARIANT", _NOTE_VARIANT % (others[0], copybook.file))
        parent = fragment_parents.get(copybook.file)
        if parent:
            add("FRAGMENT", _NOTE_FRAGMENT % (copybook.file, parent, item.record))
        if (item.line, item.name) in _odd_prefix_fields(root, copybook.file):
            anomalies.append("A-20")
        for note in draft.copybook_notes or ():
            if "length" in note:
                anomalies.append("A-15")
                ambiguities.append("Q-4")
                break

    notes: list[str] = []
    for kind in _NOTE_ORDER:
        notes.extend(bucket.get(kind, ()))
    draft.notes = notes
    draft.anomaly_refs = sorted(dict.fromkeys(anomalies),
                                key=lambda ref: int(ref.split("-")[1]))
    draft.ambiguity_refs = sorted(dict.fromkeys(ambiguities),
                                  key=lambda ref: int(ref.split("-")[1]))


_BYTES_RE: Final[re.Pattern[str]] = re.compile(r"(\d+)\s*bytes\b", re.IGNORECASE)
_SHOUTED_NOT_RE: Final[re.Pattern[str]] = re.compile(r"(?<![A-Za-z])NOT(?![A-Za-z])")

_CBNOTE_MULTIPLE_RECORDS: Final[str] = (
    "The copybook declares more than one 01-level record - %s - and record_name carries "
    "the first of them; every field keeps its own record in its entry key."
)
_CBNOTE_VARIANT: Final[str] = (
    "%s declares an identical set of items at identical lines; the two are variants of "
    "one layout and the entries cite whichever comes first in path order."
)
_CBNOTE_BRIDGE_COPY: Final[str] = (
    "The %s bridge COPYs this copybook at %s, so its items reach the database through "
    "that bridge."
)
_CBNOTE_FRAGMENT: Final[str] = (
    "A single-declaration COPY fragment that %s textually includes into its %s record."
)
_PSNOTE_INTRODUCER: Final[str] = (
    "%s %s at %s introduces the record, and the FILE-CONTROL entry that assigns that file "
    'reads "%s" at %s.'
)
_PSNOTE_TRANSIENT: Final[str] = (
    "Transient scratch storage: no bridge COPYs this record and the frozen dump declares no "
    "table for it, so every field of it is recorded with its bridge and column views absent "
    "rather than searched for. copybooks/wsnames.cob:L15-L16 names the two General Ledger "
    "work files pretrans.tmp and postrans.tmp and annotates both as belonging to gl071."
)
_PSNOTE_ALSO_DECLARED: Final[str] = (
    "%s declares a record of the same name at %s. The two are separate physical "
    "declarations, both are recorded in full, and neither is harmonised against the other "
    "(R-4)."
)
_PSNOTE_SHAPE_DIFFERS: Final[str] = (
    "The two declarations do not agree: %s additionally declares %s, which this one does "
    "not. Both shapes are kept exactly as written."
)
_PSNOTE_ORDER_CRITICAL: Final[str] = (
    "The order of these records is load-bearing rather than incidental: %s locates the "
    "nominal-ledger account for each posting by SEQUENTIAL read rather than by key, so it "
    "finds the right account only because general/gl071.cbl has already sorted the stream "
    "into nominal-key order. A change of sort key or of sort stability posts to the wrong "
    "account with no error and no diagnostic - anomaly A-14."
)

_CBNOTE_SIGN_CLAUSE: Final[str] = (
    'The copybook writes its leading-sign clause as "%s"; the spelling is kept exactly '
    "as written and is never normalised to one form."
)


def _header_quotes(root: Path, rel: str) -> list[str]:
    """The copybook's own header comments about its record length, quoted verbatim.

    Only the comment block before the first line of code is read, and only the lines
    that state a byte count, mention a length, or shout NOT in capitals.
    """
    bodies: list[tuple[str, bool]] = []
    for raw in _read_lines(root, rel):
        code, comment = _strip_comment(raw)
        if code.strip():
            break
        body = comment.rstrip()
        boxed = body.endswith("*")
        if boxed:
            body = body.rstrip("*").rstrip()
        bodies.append((body.strip(), boxed))

    quoted: list[str] = []
    total = len(bodies)
    for index, (body, boxed) in enumerate(bodies):
        if not body:
            continue
        if not (_BYTES_RE.search(body) or "length" in body.lower()
                or _SHOUTED_NOT_RE.search(body)):
            continue
        text = body
        if boxed and not text.endswith("."):
            ahead = index + 1
            while ahead < total and bodies[ahead][1] and bodies[ahead][0]:
                text += " " + bodies[ahead][0]
                if bodies[ahead][0].endswith("."):
                    break
                ahead += 1
        quoted.append(text)
    return quoted


def _declared_lengths(root: Path, rel: str) -> list[str]:
    """Every distinct record length the copybook states about itself, first-stated first.

    `copybooks/wsbatch.cob:L7-L9` states 96 bytes and then 98 bytes and says outright
    that the two do not agree. Both are recorded; neither is chosen (anomaly A-15).
    """
    lengths: list[str] = []
    for raw in _read_lines(root, rel):
        for found in _BYTES_RE.finditer(raw):
            value = found.group(1)
            if value not in lengths:
                lengths.append(value)
    return lengths


def _bridge_copy_sites(root: Path, wanted: list[str]) -> dict[str, list[tuple[str, str]]]:
    """For each copybook, the bridges that COPY it and the line at which they do."""
    want = set(wanted)
    sites: dict[str, list[tuple[str, str]]] = {}
    for bridge in sorted(_BY_BRIDGE):
        rel = "common/%s.cbl" % bridge
        for number, name in _bridge_copies(root, bridge):
            target = _copy_target(name)
            if target in want:
                sites.setdefault(target, []).append((bridge, "%s:L%d" % (rel, number)))
    return sites


def _build_copybook_sources(
        root: Path,
        order: list[str]) -> tuple[tuple[model.CopybookSource, ...],
                                   dict[str, list[str]], dict[str, str]]:
    """The copybook source records, their notes by path, and the COPY-fragment parents.
    """
    records = _resolve_record_names(root, order)
    parents: dict[str, list[str]] = {}
    for rel in order:
        for child in _copybook_copies(root, rel):
            parents.setdefault(child, []).append(rel)

    signatures: dict[str, tuple[object, ...]] = {}
    for rel in order:
        signatures[rel] = tuple(
            (item.name, item.level, item.line, item.picture, item.usage, item.redefines)
            for item in _parse_copybook(root, rel))
    same: dict[tuple[object, ...], list[str]] = {}
    for rel in order:
        if signatures[rel]:
            same.setdefault(signatures[rel], []).append(rel)

    sites = _bridge_copy_sites(root, order)
    built: list[model.CopybookSource] = []
    notes_by_path: dict[str, list[str]] = {}
    fragment_parents: dict[str, str] = {}
    for rel in order:
        items = _parse_copybook(root, rel)
        notes = _header_quotes(root, rel)
        declared = [item.name for item in items if item.level == "01"]
        if len(declared) > 1:
            notes.append(_CBNOTE_MULTIPLE_RECORDS % ", ".join(declared))
        for other in same.get(signatures[rel], ()):
            if other != rel:
                notes.append(_CBNOTE_VARIANT % other)
        for bridge, locator in sorted(sites.get(rel, ())):
            notes.append(_CBNOTE_BRIDGE_COPY % (bridge, locator))
        if not declared and len(items) == 1:
            parent = sorted(parents.get(rel, ()))[0]
            fragment_parents[rel] = parent
            notes.append(_CBNOTE_FRAGMENT % (parent, records[rel]))
        spellings: list[str] = []
        for item in items:
            if item.sign_clause_text and item.sign_clause_text not in spellings:
                spellings.append(item.sign_clause_text)
        for spelling in spellings:
            notes.append(_CBNOTE_SIGN_CLAUSE % spelling)
        notes_by_path[rel] = notes
        built.append(model.CopybookSource(
            path=rel,
            record_name=records[rel],
            declared_lengths=tuple(_declared_lengths(root, rel)),
            notes=tuple(notes),
        ))
    return tuple(built), notes_by_path, fragment_parents


def _program_source_sources(root: Path) -> tuple[model.ProgramSourceRecord, ...]:
    """The record inventory of the fourth source family, in the stated array order.

    Every member is derived from the frozen program text.
    """
    built: list[model.ProgramSourceRecord] = []
    for rel, record, section, first, last in sorted(
            _PROGRAM_SOURCE_RECORDS, key=lambda row: (row[0], row[3])):
        items = _parse_program_source(root, rel, record)
        line, keyword, file_name = _program_source_introducer(root, rel, first)
        select_line, select_text = _program_source_select(root, rel, file_name)
        notes = [_PSNOTE_INTRODUCER % (keyword, file_name, "%s:L%d" % (rel, line),
                                       select_text, "%s:L%d" % (rel, select_line)),
                 _PSNOTE_TRANSIENT]
        own = {item.name.lower() for item in items}
        for other in _program_source_siblings(rel, record):
            other_first = _program_source_span(other, record)[1]
            notes.append(_PSNOTE_ALSO_DECLARED % (other, "%s:L%d" % (other, other_first)))
            extra = [item.name for item in _parse_program_source(root, other, record)
                     if item.name.lower() not in own]
            if extra:
                notes.append(_PSNOTE_SHAPE_DIFFERS % (other, ", ".join(extra)))
        if record in _ORDERING_CRITICAL_RECORDS:
            notes.append(_PSNOTE_ORDER_CRITICAL % _SEQUENTIAL_READ_LOCATOR)
        built.append(model.ProgramSourceRecord(
            path=rel,
            record_name=record,
            section=section,
            declared_lengths=_program_source_declared_lengths(root, rel, first, last),
            notes=tuple(notes),
        ))
    return tuple(built)


# STAGE 5 - assemble the entries Entries are built in two passes and the order matters
# for reproducing the committed artifact exactly.


def _signature(item: "_CopybookItem") -> tuple[object, ...]:
    """What makes two copybook declarations the same declaration.

    The file is deliberately not part of it. `copybooks/plwsoi5B.cob` and
    `copybooks/plwsoi5C.cob` are variants of one layout that differ only in whether a
    single COPY is commented out, so they declare the same items at the same lines.
    """
    return (item.record, item.name, item.level, item.line, item.picture, item.usage,
            item.redefines)


def _build_entries(root: Path, schema: _SchemaFacts,
                   scb: dict[str, tuple[str, str, list[dict[str, str]],
                                        list[model.BridgeKey], str]],
                   hosts: dict[tuple[str, str], "_HostVariable"],
                   order: list[str], copybook_notes: dict[str, list[str]],
                   fragment_parents: dict[str, str]) -> list[_EntryDraft]:
    """The complete, ordered entry set, fully annotated."""
    fields = {rel: _parse_copybook(root, rel) for rel in order}

    variants: dict[tuple[object, ...], list[str]] = {}
    for rel in order:
        for item in fields[rel]:
            paths = variants.setdefault(_signature(item), [])
            if rel not in paths:
                paths.append(rel)
    variants = {key: paths for key, paths in variants.items() if len(paths) > 1}

    consumed: set[int] = set()
    by_table: dict[str, list[_EntryDraft]] = {}
    owned: dict[str, list[str]] = {}
    for table in _IN_SCOPE_TABLES:
        bridge, handler, entity, _spine = _BY_TABLE[table]
        owned[table] = _table_copybooks(root, table)
        pool = [item for rel in owned[table] for item in fields[rel]]
        suffix = next(entry["hv_group_suffix"] for entry in scb[bridge][2]
                      if entry["name"] == table)
        facts = schema.tables[table]
        rows: list[_EntryDraft] = []
        for ordinal, (line, name, declaration) in enumerate(facts["cols"], 1):
            column = _column_view(line, name, declaration, facts["pk"], ordinal)
            host = hosts[("common/%s.cbl" % bridge, ("%s-%s" % (suffix, name))[:30])]
            item, occurrence = _bind(host, name, pool)
            if item is not None:
                consumed.add(id(item))
            copybook = None if item is None else item.view()
            rows.append(_EntryDraft(
                key="%s.%s" % (table, name), table=table, bridge=bridge, handler=handler,
                entity_facade=entity,
                presence=model.Presence(in_copybook=copybook is not None, in_bridge=True,
                                        in_column=True, in_program_source=False),
                one_sided=copybook is None, copybook=copybook, host=host, column=column,
                drift=_drift_of(copybook, host.view, column),
                storage=_storage_of(copybook), item=item, occurrence=occurrence,
                signature=None if item is None else _signature(item),
                copybook_notes=[] if copybook is None else copybook_notes[copybook.file],
            ))
        by_table[table] = rows

    # A column whose load move reads part of a field records which column carries the
    # whole of it, so the guard-failure note can name it.
    sibling_columns: dict[tuple[str, str], str] = {}
    for table in _IN_SCOPE_TABLES:
        for draft in by_table[table]:
            base = _data_name(draft.host.load_operand)
            if base is not None:
                sibling_columns.setdefault((table, base.upper()), draft.column.name)

    for table in _IN_SCOPE_TABLES:
        for draft in by_table[table]:
            draft.derivation = _derivation_of(root, table, draft.copybook, draft.item,
                                              draft.host, draft.column, sibling_columns)

    # Pass 2: ONE ENTRY PER PHYSICAL DECLARATION the columns did not consume.
    #
    # EVERY physical declaration, not one per signature. `_signature`
    # deliberately omits the file, so two variant copybooks that declare the same item at
    # the same line share one signature - copybooks/plwsoi5B.cob and
    # copybooks/plwsoi5C.cob are byte-identical apart from 5C's active
    # `copy "plwsoi.cob"', so all seven of their declarations collide. Electing one item
    # per signature therefore left SIX physical declarations of plwsoi5C.cob - its L10,
    # L12 and L14 through L17 - with no entry of their own, while the aggregate
    # `copybook_fields_covered' still read 1001 because six OCCURS-expanded IRS-nominal
    # views were counted twice over. Rule R-5 binds every FIELD to an entry, and a
    # declaration a reader can point at in a frozen file is a field; so each one now gets
    # an entry and the count below is over DISTINCT DECLARATIONS rather than over entries.
    #
    # KEYS STAY STABLE. Within one signature the CANONICAL copy - the first emitted in
    # closure order - keeps the plain `<record>.<name>' key and takes part in the existing
    # `#<line>' collision rule unchanged; every further copy is qualified with `@<file
    # stem>', which cannot collide with any plain key because no record or field name
    # contains `@'. So the 1061 unqualified keys are byte-identical to what the plain
    # rule alone produces, the record modules' citations keep resolving, and exactly the
    # six otherwise-missing declarations are added.
    groups: dict[tuple[object, ...], list[_CopybookItem]] = {}
    for rel in order:
        for item in fields[rel]:
            groups.setdefault(_signature(item), []).append(item)

    #: Which file owns the UNQUALIFIED key for each signature: the first file, in closure
    #: order, that actually emits a leftover entry for it. It is the first EMITTED copy
    #: rather than simply the first declaring file, because the column pass may have
    #: consumed the earlier file's item - `oi5-key' is bound by PUITM5-REC.OI5-KEY from
    #: plwsoi5B.cob, which is why plwsoi5C.cob is the canonical holder of
    #: `Open-Item-Record-5.oi5-key' and why that key must not move.
    canonical_file: dict[tuple[object, ...], str] = {}
    for rel in order:
        for item in fields[rel]:
            if id(item) in consumed:
                continue
            canonical_file.setdefault(_signature(item), rel)

    leftovers: dict[str, list[_EntryDraft]] = {}
    for rel in order:
        rows = []
        for item in fields[rel]:
            if id(item) in consumed:
                continue
            copybook = item.view()
            key = "%s.%s" % (item.record, item.name)
            if canonical_file[_signature(item)] != rel:
                key = "%s@%s" % (key, Path(rel).stem)
            rows.append(_EntryDraft(
                key=key, presence=model.Presence(
                    in_copybook=True, in_bridge=False, in_column=False,
                    in_program_source=False),
                one_sided=True, copybook=copybook, host=None, column=None,
                drift=_NO_DRIFT, derivation=None, storage=_storage_of(copybook),
                item=item, occurrence=None, signature=_signature(item),
                copybook_notes=copybook_notes[rel],
            ))
        leftovers[rel] = rows

    owner: dict[str, str] = {}
    for table in _IN_SCOPE_TABLES:
        for rel in owned[table]:
            owner.setdefault(rel, table)

    drafts: list[_EntryDraft] = []
    for table in _IN_SCOPE_TABLES:
        drafts.extend(by_table[table])
        for rel in sorted(rel for rel, holder in owner.items() if holder == table):
            drafts.extend(leftovers[rel])
    for rel in order:
        if rel not in owner:
            drafts.extend(leftovers[rel])

    # Pass 3: the records the posting programs declare inline in their own FILE
    # SECTIONs.
    for rel, record, _section, _first, _last in sorted(
            _PROGRAM_SOURCE_RECORDS, key=lambda row: (row[0], row[3])):
        for item in _parse_program_source(root, rel, record):
            view = item.view()
            drafts.append(_EntryDraft(
                key="%s.%s" % (item.record, item.name), presence=model.Presence(
                    in_copybook=False, in_bridge=False, in_column=False,
                    in_program_source=True),
                one_sided=True, copybook=None, program_source=view, host=None,
                column=None, drift=_NO_DRIFT, derivation=None, storage=_storage_of(view),
                item=item, occurrence=None, signature=_signature(item),
                copybook_notes=[],
            ))

    warnings: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for bridge in sorted(_BY_BRIDGE):
        columns = {table: [draft.column.name for draft in by_table[table]]
                   for table in _BY_BRIDGE[bridge][2]}
        warnings.update(_scb_warnings(root, bridge, columns))

    for draft in drafts:
        _notes_and_refs(root, draft, warnings, variants, fragment_parents)

    # A key that would otherwise repeat gains # and its one-based declaration line,
    # which is unique and stays traceable.
    counts = Counter(draft.key for draft in drafts)
    for draft in drafts:
        if counts[draft.key] > 1:
            draft.key = "%s#%d" % (draft.key, draft.item.line)

    _assert_declaration_closure(order, fields, drafts)
    return drafts


def _assert_declaration_closure(
    order: list[str],
    fields: dict[str, list["_CopybookItem"]],
    drafts: list[_EntryDraft],
) -> None:
    """Refuse to emit a dictionary that omits any physical copybook declaration (R-5).

    THE POPULATION IS THE MULTISET OF DECLARATIONS IN THE FROZEN FILES, not a total.
    A total cannot see a shortfall in one file that a surplus in another conceals:
    `copybooks/plwsoi5C.cob` has seven declarations and `copybooks/irswsnl.cob`
    fourteen, but six OCCURS-expanded views inflate the latter's entry count by
    exactly the amount the former's is short, so both counts agree while the mapping
    is wrong. This therefore compares the two SETS, file by file and line by line,
    and names what is missing.

    Args:
        order: The copybook closure, in the order it was parsed.
        fields: Every parsed declaration, by file.
        drafts: The assembled entry drafts, keys already final.

    Raises:
        ValueError: Some declaration in a parsed copybook has no entry citing it. The
            message names the file, the line and the field, because the fix is always to
            emit the entry and never to lower the expectation.
    """
    declared = {
        (rel, item.line, item.name.lower())
        for rel in order for item in fields[rel]
    }
    cited = {
        (draft.item.file, draft.item.line, draft.item.name.lower())
        for draft in drafts
        if draft.copybook is not None and draft.item is not None
    }
    missing = sorted(declared - cited)
    if missing:
        raise ValueError(
            "%d physical copybook declaration(s) have no dictionary entry, which "
            "rule R-5 does not permit: %s"
            % (len(missing),
               ", ".join("%s:L%d %s" % (rel, line, name) for rel, line, name in missing))
        )


_VARCHAR_PREFIX: Final[str] = "varchar"


def _default_phrase(text: str) -> str:
    """How a column default reads in prose, without altering what was parsed."""
    stripped = text.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in "'\"":
        if not stripped[1:-1]:
            return "the empty string"
    return text


def _schema_source(root: Path, facts: _SchemaFacts,
                   columns: list[model.MysqlColumn]) -> model.SchemaSource:
    """The schema source record: the dump's own facts, counted rather than assumed.

    Two populations are reported and each note says which it covers. The type census
    counts every column the dump declares, in scope or not, because it is a statement
    about the frozen dump.
    """
    census: Counter[str] = Counter()
    all_columns = 0
    varchar_columns = 0
    for name in sorted(facts.tables):
        table = facts.tables[name]
        for line, column_name, declaration in table["cols"]:
            all_columns += 1
            if declaration.strip().lower().startswith(_VARCHAR_PREFIX):
                varchar_columns += 1
                continue
            census[str(_column_view(line, column_name, declaration, None, 1).base_type)] += 1

    defaults = [column for column in columns if column.column_default is not None]
    default_column = ""
    default_locator = ""
    default_text = ""
    if defaults:
        first = defaults[0]
        owner = next(name for name in _IN_SCOPE_TABLES
                     if any(line == int(first.source.rsplit(":L", 1)[1])
                            for line, _n, _d in facts.tables[name]["cols"]))
        default_column = "%s.%s" % (owner, first.name)
        default_locator = first.source
        default_text = _default_phrase(str(first.column_default))

    commented = sum(1 for column in columns if column.comment is not None)
    zero_scale = sum(1 for column in columns
                     if column.base_type is model.SqlBaseType.DECIMAL and column.scale == 0)
    templates = _SCHEMA_NOTE_TEMPLATES
    notes = (
        templates[0] % (facts.create_table_count, all_columns, len(_IN_SCOPE_TABLES),
                        len(columns)),
        templates[1] % (facts.guarded_alter_comment_count, facts.structural_alter_count),
        templates[2],
        templates[3] % (census["CHAR"], varchar_columns),
        templates[4] % len(columns),
        templates[5] % (len(_IN_SCOPE_TABLES), len(defaults), len(columns),
                        default_column, default_locator, default_text),
        templates[6] % commented,
        templates[7] % zero_scale,
    )
    return model.SchemaSource(
        path=_SCHEMA_REL,
        server_version=facts.server_version,
        server_version_source="%s:L%d" % (_SCHEMA_REL, facts.server_version_line),
        create_table_count=facts.create_table_count,
        create_index_count=facts.create_index_count,
        schema_evolution_alter_table_count=facts.structural_alter_count,
        dump_key_management_comment_count=facts.guarded_alter_comment_count,
        float_double_real_column_count=facts.binary_real_columns,
        numeric_type_census=model.NumericTypeCensus(
            DECIMAL=census["DECIMAL"], INT=census["INT"], TINYINT=census["TINYINT"],
            SMALLINT=census["SMALLINT"], MEDIUMINT=census["MEDIUMINT"],
            BIGINT=census["BIGINT"], CHAR=census["CHAR"]),
        notes=notes,
    )


def _bridge_source(root: Path, bridge: str, base: str, tables: list[dict[str, str]],
                   keys: list[model.BridgeKey],
                   directive_source: str) -> model.BridgeSource:
    """The bridge source record: its directive, its keys and its transfer paragraphs."""
    rel = "common/%s.cbl" % bridge
    lines = _read_lines(root, rel)
    paragraphs = _paragraphs(lines)
    loads: Counter[tuple[int, str]] = Counter()
    unloads: Counter[tuple[int, str]] = Counter()
    for number, raw in enumerate(lines, 1):
        code, _ = _strip_comment(raw)
        text = code.strip()
        if _MOVE_OUT_OF_HV_RE.search(text):
            owner = _owning_paragraph(paragraphs, number)
            if owner is not None:
                unloads[owner] += 1
        elif _MOVE_INTO_HV_RE.search(text):
            owner = _owning_paragraph(paragraphs, number)
            if owner is not None:
                loads[owner] += 1

    def busiest(counts: Counter[tuple[int, str]]) -> tuple[int, str] | None:
        if not counts:
            return None
        return max(counts.items(), key=lambda pair: (pair[1], -pair[0][0]))[0]

    load = busiest(loads)
    unload = busiest(unloads)
    group_names = {table["hv_group_name"].upper() for table in tables}
    load_source = None
    initialised = False
    if load is not None:
        low, high = _paragraph_span(paragraphs, load[0], len(lines))
        load_source = "%s:L%d-L%d" % (rel, low, high)
        for number in range(low, high + 1):
            code, _ = _strip_comment(lines[number - 1])
            found = _INITIALIZE_RE.match(code)
            if found is not None and found.group(1).upper() in group_names:
                initialised = True
    unload_source = None
    if unload is not None:
        low, high = _paragraph_span(paragraphs, unload[0], len(lines))
        unload_source = "%s:L%d-L%d" % (rel, low, high)

    return model.BridgeSource(
        scb_path="common/%s.scb" % bridge,
        cbl_path=rel,
        base=base,
        directive_source=directive_source,
        tables=tuple(model.BridgeTableRef(name=table["name"],
                                         hv_group_suffix=table["hv_group_suffix"],
                                         hv_group_name=table["hv_group_name"])
                     for table in tables),
        keys=tuple(keys),
        load_paragraph=None if load is None else load[1],
        load_paragraph_source=load_source,
        unload_paragraph=None if unload is None else unload[1],
        unload_paragraph_source=unload_source,
        group_initialised_before_load=initialised,
    )


def _table_records(root: Path, facts: _SchemaFacts) -> tuple[model.TableRecord, ...]:
    """One record per in-scope table, in table-name order."""
    records: list[model.TableRecord] = []
    for table in _IN_SCOPE_TABLES:
        bridge, handler, entity, _spine = _BY_TABLE[table]
        detail = facts.tables[table]
        records.append(model.TableRecord(
            name=table,
            bridge=bridge,
            handler=handler,
            entity_facade=model.EntityFacade(entity),
            copybooks=tuple(_table_copybooks(root, table)),
            primary_key=detail["pk"],
            column_count=len(detail["cols"]),
            ordinal_source="%s:L%d" % (_SCHEMA_REL, detail["line"]),
        ))
    return tuple(records)


def _meta(source_inputs_sha256: str) -> model.Meta:
    """The identity block, including the determinism and derivation contracts.

    Nothing here is derived from the environment.

    Args:
        source_inputs_sha256: The roll-up digest of the provenance manifest, from
            `model.source_inputs_digest`.
    """
    return model.Meta(
        dictionary_name=model.DICTIONARY_NAME,
        dictionary_version=_DICTIONARY_VERSION,
        schema_ref=model.DICTIONARY_SCHEMA_REF,
        generated_by=model.DICTIONARY_GENERATED_BY,
        authority=model.DICTIONARY_AUTHORITY,
        determinism=model.Determinism(
            encoding=model.DETERMINISM_ENCODING,
            newline=model.DETERMINISM_NEWLINE,
            indent=model.DETERMINISM_INDENT,
            trailing_newline=model.DETERMINISM_TRAILING_NEWLINE,
            byte_order_mark=model.DETERMINISM_BYTE_ORDER_MARK,
            member_order=_DETERMINISM_MEMBER_ORDER,
            array_order=model.ArrayOrder(
                tables=_ARRAY_ORDER_TABLES,
                entries=_ARRAY_ORDER_ENTRIES,
                bridges=_ARRAY_ORDER_BRIDGES,
                copybooks=_ARRAY_ORDER_COPYBOOKS,
                program_sources=_ARRAY_ORDER_PROGRAM_SOURCES),
            forbidden_content=_FORBIDDEN_CONTENT,
        ),
        derivation_rules=model.DerivationRules(
            entry_key=_RULE_ENTRY_KEY,
            presence_and_one_sided=_RULE_PRESENCE_AND_ONE_SIDED,
            drift_detection=_RULE_DRIFT_DETECTION,
            digits_and_scale_from_picture=_RULE_DIGITS_AND_SCALE,
            sign_position_from_clause=_RULE_SIGN_POSITION,
            usage_inheritance=_RULE_USAGE_INHERITANCE,
            bridge_derived_columns=_RULE_BRIDGE_DERIVED_COLUMNS,
            cobol_python_storage=_RULE_COBOL_PYTHON_STORAGE,
            program_source_entries=_RULE_PROGRAM_SOURCE_ENTRIES,
        ),
        binding_rules=tuple(
            model.BindingRule(id="R-%d" % (index + 1), summary=summary)
            for index, summary in enumerate(_BINDING_RULE_SUMMARIES)),
        source_inputs_sha256=source_inputs_sha256,
    )


def _coverage(entries: tuple[model.DictionaryEntry, ...]) -> model.Coverage:
    """The auditable totals, every one of them counted from the entries themselves."""
    return model.Coverage(
        schema_tables_total=len(_IN_SCOPE_TABLES) + _OUT_OF_SCOPE_TABLES,
        in_scope_tables=len(_IN_SCOPE_TABLES),
        out_of_scope_tables=_OUT_OF_SCOPE_TABLES,
        in_scope_bridges=len(_BY_BRIDGE),
        out_of_scope_bridges=_OUT_OF_SCOPE_BRIDGES,
        in_scope_columns=sum(1 for entry in entries if entry.column is not None),
        entry_count=len(entries),
        columns_covered=sum(1 for entry in entries if entry.column is not None),
        host_variables_covered=sum(1 for entry in entries
                                   if entry.bridge_host_variable is not None),
        copybook_fields_covered=sum(1 for entry in entries if entry.copybook is not None),
        #  DISTINCT PHYSICAL DECLARATIONS, keyed by locator and name, so an OCCURS item
        #  bound by several columns counts ONCE however many entries cite it. Rule R-5's
        #  closure is about this number; the tally above is about entries.
        copybook_declarations_covered=len({
            (str(entry.copybook.source), str(entry.copybook.name))
            for entry in entries if entry.copybook is not None
        }),
        program_source_fields_covered=sum(1 for entry in entries
                                          if entry.program_source is not None),
        one_sided_entry_keys=tuple(entry.key for entry in entries if entry.one_sided),
    )


#: Tables the posting cycle never touches, and the bridges that serve them. They are
#: listed here for one purpose only.
_OUT_OF_SCOPE_NAMES: Final[tuple[str, ...]] = (
    "STOCK-REC", "STOCKAUDIT-REC", "DELIVERY-REC", "PUDELINV-REC", "SADELINV-REC",
    "SAAUTOGEN-REC", "SAAUTOGEN-LINES-REC", "PUAUTOGEN-REC", "PUAUTOGEN-LINES-REC",
    "PLPAY-REC", "PLPAY-RECrg01", "auditMT", "deliveryMT", "delfolioMT",
    "sldelinvnosMT", "stockMT", "paymentsMT", "plautogenMT", "slautogenMT",
)

#: The three groups whose USAGE clause is inherited by every subordinate item: the batch
#: amounts and the two ledger period-total blocks.
_INHERITING_GROUPS: Final[tuple[str, ...]] = (
    "Amounts", "Sales-Ledger-Data", "Purchase-Ledger-Data",
)
_INHERITING_GROUP_FIELDS: Final[int] = 24

_REQUIRED_ENTRY_KEYS: Final[tuple[str, ...]] = (
    "IRSPOSTING-REC.POST4-DAY", "IRSPOSTING-REC.POST4-MONTH", "IRSPOSTING-REC.POST4-YEAR",
    "GLPOSTING-REC.POST-RRN", "GLLEDGER-REC.LEDGER-NAME", "SAITM3-REC.OI3-DESCRIPTION",
    "SALEDGER-REC.SALES-AVERAGE", "GLBATCH-REC.ENTERED",
)

#: The work-file fields `acas_posting/records/work_records.py` binds through this
#: dictionary rather than by hand. Every one must hold a key.
_REQUIRED_PROGRAM_SOURCE_KEYS: Final[tuple[str, ...]] = (
    "pre-trans-record.pre-batch#109", "pre-trans-record.pre-post#110",
    "pre-trans-record.pre-code#111", "pre-trans-record.pre-date#112",
    "pre-trans-record.pre-ac#113", "pre-trans-record.pre-pc#114",
    "pre-trans-record.pre-amount#115", "pre-trans-record.pre-legend#116",
    "post-trans-record.post-batch#125", "post-trans-record.post-post#126",
    "post-trans-record.post-code#127", "post-trans-record.post-date#128",
    "post-trans-record.post-ac#129", "post-trans-record.post-pc#130",
    "post-trans-record.post-amount#131", "post-trans-record.post-legend#132",
    "sort-trans-record.sort-batch", "sort-trans-record.sort-post",
    "sort-trans-record.sort-code", "sort-trans-record.sort-date",
    "sort-trans-record.sort-ac", "sort-trans-record.sort-pc",
    "sort-trans-record.sort-amount", "sort-trans-record.sort-legend",
    "post-trans-record.post-ledger", "post-trans-record.post-ac#116",
    "post-trans-record.post-pc#117",
)


def build_dictionary(root: Path) -> model.DataDictionary:
    """Parse the four frozen source families and build the whole dictionary.

    The stages run sequentially in a fixed order - schema, copybooks, bridges, join -
    with no concurrency of any kind (R-3), and every collection is sorted before it is
    iterated so nothing about the result depends on filesystem traversal (R-6).
    """
    facts = _parse_schema(root)
    order = _copybook_closure(root)
    copybooks, copybook_notes, fragment_parents = _build_copybook_sources(root, order)

    scb: dict[str, tuple[str, str, list[dict[str, str]], list[model.BridgeKey], str]] = {}
    hosts: dict[tuple[str, str], _HostVariable] = {}
    bridges: list[model.BridgeSource] = []
    for bridge in sorted(_BY_BRIDGE):
        parsed = _parse_scb(root, bridge)
        scb[bridge] = parsed
        _rel, base, tables, keys, directive_source = parsed
        _chosen, spans, initialised = _transfer_paragraphs(root, bridge, tables)
        for host in _parse_host_variables(root, bridge, tables, spans, initialised):
            hosts[(host.view.file, host.view.name)] = host
        bridges.append(_bridge_source(root, bridge, base, tables, keys, directive_source))

    drafts = _build_entries(root, facts, scb, hosts, order, copybook_notes,
                            fragment_parents)
    entries = tuple(draft.entry() for draft in drafts)
    columns = [entry.column for entry in entries if entry.column is not None]
    schema_source = _schema_source(root, facts, columns)
    table_records = _table_records(root, facts)
    coverage = _coverage(entries)

    # The last frozen source has now been read. Seal the root and take the manifest.
    input_digests = _input_digest_manifest(root)

    return model.DataDictionary(
        meta=_meta(model.source_inputs_digest(input_digests)),
        sources=model.Sources(schema=schema_source,
                              bridges=tuple(bridges),
                              copybooks=copybooks,
                              input_digests=input_digests,
                              program_sources=_program_source_sources(root)),
        tables=table_records,
        entries=entries,
        coverage=coverage,
    )


def _assert_no_binary_reals(node: object, where: str) -> None:
    """Refuse to emit any value that is not a bool, an int, a string or None.

    Rule R-2 forbids a binary real type anywhere in accounting code. This dictionary
    describes precision and scale, so it must state them as integers and pictures as
    strings and must never coerce a value through a binary real type.
    """
    if node is None or isinstance(node, (bool, int, str)):
        return
    if isinstance(node, dict):
        for key, value in node.items():
            if not isinstance(key, str):
                raise ValueError("non-string member name at %s: %r" % (where, key))
            _assert_no_binary_reals(value, "%s.%s" % (where, key))
        return
    if isinstance(node, list):
        for index, value in enumerate(node):
            _assert_no_binary_reals(value, "%s[%d]" % (where, index))
        return
    raise ValueError("value of prohibited type %s at %s: %r"
                     % (type(node).__name__, where, node))


def _verify(dictionary: model.DataDictionary, text: str) -> None:
    """Check the dictionary against the facts it must satisfy, or raise ValueError.

    A coverage shortfall is a hard failure, not a warning: rule R-5 requires every field
    to have an entry, and the column count is the mechanical proof of it.
    """
    coverage = dictionary.coverage
    schema = dictionary.sources.schema
    problems: list[str] = []

    if coverage.columns_covered != coverage.in_scope_columns:
        problems.append("columns covered %d of %d in scope"
                        % (coverage.columns_covered, coverage.in_scope_columns))
    if coverage.entry_count != len(dictionary.entries):
        problems.append("entry_count %d does not match %d entries"
                        % (coverage.entry_count, len(dictionary.entries)))
    if coverage.schema_tables_total != schema.create_table_count:
        problems.append("table total %d does not match the %d tables the dump declares"
                        % (coverage.schema_tables_total, schema.create_table_count))
    if coverage.in_scope_tables + coverage.out_of_scope_tables != coverage.schema_tables_total:
        problems.append("in-scope and out-of-scope tables do not sum to the total")
    if len(dictionary.tables) != coverage.in_scope_tables:
        problems.append("%d table records for %d in-scope tables"
                        % (len(dictionary.tables), coverage.in_scope_tables))
    if len(dictionary.sources.bridges) != coverage.in_scope_bridges:
        problems.append("%d bridge records for %d in-scope bridges"
                        % (len(dictionary.sources.bridges), coverage.in_scope_bridges))
    if schema.create_index_count or schema.schema_evolution_alter_table_count:
        problems.append("the frozen dump is not index-free and evolution-free as parsed")
    if schema.float_double_real_column_count:
        problems.append("%d columns declare a prohibited binary real type"
                        % schema.float_double_real_column_count)
    if not schema.server_version or not schema.server_version_source.startswith(
            _SCHEMA_REL + ":L"):
        problems.append("the server version was not parsed from the dump's own header")

    counts = Counter(entry.table for entry in dictionary.entries
                     if entry.column is not None)
    for record in dictionary.tables:
        if counts[record.name] != record.column_count:
            problems.append("%s: %d column entries for %d columns"
                            % (record.name, counts[record.name], record.column_count))

    inherited = sum(
        1 for entry in dictionary.entries
        if entry.copybook is not None
        and entry.copybook.usage_declared_at is model.UsageDeclaredAt.GROUP
        and entry.copybook.usage_inherited_from in _INHERITING_GROUPS)
    if inherited != _INHERITING_GROUP_FIELDS:
        problems.append("%d fields inherit USAGE from the batch and period-total groups, "
                        "expected %d" % (inherited, _INHERITING_GROUP_FIELDS))
    for entry in dictionary.entries:
        copybook = entry.copybook
        if copybook is None:
            continue
        if copybook.usage_declared_at is model.UsageDeclaredAt.GROUP and not (
                copybook.usage_inherited_from and copybook.usage_group_source):
            problems.append("%s inherits USAGE but names no group" % entry.key)

    present = {entry.key for entry in dictionary.entries}
    missing = [key for key in _REQUIRED_ENTRY_KEYS if key not in present]
    if missing:
        problems.append("missing entries: %s" % ", ".join(missing))
    if len(present) != len(dictionary.entries):
        problems.append("entry keys are not unique")

    for entry in dictionary.entries:
        presence = entry.presence
        if (presence.in_copybook != (entry.copybook is not None)
                or presence.in_bridge != (entry.bridge_host_variable is not None)
                or presence.in_column != (entry.column is not None)
                or presence.in_program_source != (entry.program_source is not None)):
            problems.append("%s: presence disagrees with the views it describes" % entry.key)
        if entry.one_sided != (not (presence.in_copybook and presence.in_bridge
                                    and presence.in_column)):
            problems.append("%s: one_sided disagrees with presence" % entry.key)

    program_source = [entry for entry in dictionary.entries
                      if entry.program_source is not None]
    if len(program_source) != coverage.program_source_fields_covered:
        problems.append("%d program-source entries for a tally of %d"
                        % (len(program_source), coverage.program_source_fields_covered))
    if len(dictionary.sources.program_sources) != len(_PROGRAM_SOURCE_RECORDS):
        problems.append("%d program-source records for the %d the generator was told of"
                        % (len(dictionary.sources.program_sources),
                           len(_PROGRAM_SOURCE_RECORDS)))
    for entry in program_source:
        if (entry.table is not None or entry.bridge is not None
                or entry.handler is not None or entry.entity_facade is not None
                or entry.copybook is not None or entry.bridge_host_variable is not None
                or entry.column is not None or entry.derivation is not None):
            problems.append("%s is a work-file field and reaches no table, so its table, "
                            "bridge, handler, facade, copybook, host-variable, column and "
                            "derivation members must all be null" % entry.key)
    missing_work = [key for key in _REQUIRED_PROGRAM_SOURCE_KEYS if key not in present]
    if missing_work:
        problems.append("missing work-record entries: %s" % ", ".join(missing_work))

    by_key = {entry.key: entry for entry in dictionary.entries}
    for key in ("IRSPOSTING-REC.POST4-DAY", "IRSPOSTING-REC.POST4-MONTH",
                "IRSPOSTING-REC.POST4-YEAR"):
        entry = by_key.get(key)
        if entry is None:
            continue
        if entry.copybook is not None or entry.derivation is None:
            problems.append("%s must be bridge-derived with no copybook view" % key)
        elif entry.derivation.guard is None or "A-7" not in entry.anomaly_refs:
            problems.append("%s must record its guard and anomaly A-7" % key)
    never_loaded = by_key.get("GLPOSTING-REC.POST-RRN")
    if never_loaded is not None:
        view = never_loaded.bridge_host_variable
        if view is None or view.loaded_from_record:
            problems.append("GLPOSTING-REC.POST-RRN must be recorded as never loaded")
        if not never_loaded.ambiguity_refs:
            problems.append("GLPOSTING-REC.POST-RRN must carry an ambiguity reference")
    for key in ("GLLEDGER-REC.LEDGER-NAME", "SAITM3-REC.OI3-DESCRIPTION"):
        entry = by_key.get(key)
        if entry is not None and not entry.drift.character_length:
            problems.append("%s must flag a character-length drift" % key)
    for key in ("SALEDGER-REC.SALES-AVERAGE", "GLBATCH-REC.ENTERED"):
        entry = by_key.get(key)
        if entry is not None and not entry.drift.signedness:
            problems.append("%s must flag a signedness drift" % key)
    for key in ("SALEDGER-REC.SALES-CURRENT", "SALEDGER-REC.SALES-LAST"):
        entry = by_key.get(key)
        if entry is not None and entry.drift.signedness:
            problems.append("%s must not flag a signedness drift: the monetary fields "
                            "pass through signed, which is what makes the narrowing "
                            "specific rather than systemic" % key)

    # The British spelling of INITIALIZE, asserted in BOTH directions.
    for key in ("IRSDFLT-REC.DEF-REC-KEY", "IRSDFLT-REC.DEF-ACS",
                "IRSDFLT-REC.DEF-CODES", "IRSDFLT-REC.DEF-VAT"):
        entry = by_key.get(key)
        if entry is None:
            problems.append("%s is missing: IRSDFLT-REC carries four columns" % key)
            continue
        view = entry.bridge_host_variable
        if view is None or not view.group_initialised_before_load:
            problems.append("%s must record its host-variable group as initialised "
                            "before the load: irsdfltMT spells the verb the British "
                            "way at common/irsdfltMT.cbl:L625" % key)
    for key in ("SYSDEFLT-REC.DEF-REC-KEY", "SYSFINAL-REC.FINAL-ACC-REC-KEY",
                "IRSFINAL-REC.IRS-FINAL-ACC-REC-KEY"):
        entry = by_key.get(key)
        if entry is None:
            continue
        view = entry.bridge_host_variable
        if view is not None and view.group_initialised_before_load:
            problems.append("%s must NOT record its host-variable group as "
                            "initialised: its bridge initialises the COBOL record "
                            "with filler and names no TD- group" % key)
    group_initialised = {source.cbl_path: source.group_initialised_before_load
                         for source in dictionary.sources.bridges}
    if group_initialised.get("common/irsdfltMT.cbl") is not True:
        problems.append("common/irsdfltMT.cbl must record group_initialised_before_load "
                        "true from its British-spelled INITIALISE at L625")
    for path in ("common/dfltMT.cbl", "common/finalMT.cbl", "common/irsfinalMT.cbl"):
        if group_initialised.get(path) is True:
            problems.append("%s must record group_initialised_before_load false: it "
                            "issues no INITIALIZE naming its TD- group" % path)

    lowered = text.lower()
    for name in _OUT_OF_SCOPE_NAMES:
        if name.lower() in lowered:
            problems.append("out-of-scope name %r reached the emitted document" % name)

    if problems:
        raise ValueError("; ".join(problems))


def render(dictionary: model.DataDictionary) -> str:
    """Serialise the dictionary under the byte contract the document itself states.

    UTF-8, LF, two-space indent, exactly one trailing newline, no byte-order mark, and
    members in the order the schema declares them - never sorted alphabetically, which
    would produce a valid but different file (R-6).
    """
    payload = model.to_json_obj(dictionary)
    _assert_no_binary_reals(payload, "$")
    text = json.dumps(payload, ensure_ascii=False,
                      indent=model.DETERMINISM_INDENT) + "\n"

    # Read the rendered bytes back through the reader's own gate before anyone is
    # offered them.
    reloaded = model.from_json_obj(json.loads(text, parse_float=str))
    if reloaded != dictionary:
        raise ValueError(
            "the rendered document does not read back as the dictionary it was "
            "rendered from")
    return text


_TEMP_SUFFIX: Final[str] = ".tmp"


def _write(path: Path, text: str) -> None:
    """Write the document to a fresh private file and move it into place atomically.

    Three separate weaknesses in the obvious one-line form are closed here, and each of
    them is a way the artifact - the document every record module cites under rule R-5 -
    could be corrupted or diverted by something other than this generator.

    Args:
        path: The document to write.
        text: The rendered document, newline-pinned by the caller.

    Raises:
        OSError: The directory could not be created, or the document could not be
            rendered, synced or moved into place.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        final_mode = path.stat().st_mode & 0o7777
    except FileNotFoundError:
        final_mode = 0o644

    # A staging file left behind by an interrupted run would otherwise make every later
    # run fail on `O_EXCL`.
    staging = path.with_name(path.name + ".partial")
    staging.unlink(missing_ok=True)
    descriptor = os.open(
        staging,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_NOFOLLOW,
        0o600,
    )
    try:
        os.fchmod(descriptor, 0o600)
        with open(descriptor, "w", encoding="utf-8", newline="\n",
                  closefd=False) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(descriptor)
        os.fchmod(descriptor, final_mode)
    finally:
        os.close(descriptor)
    try:
        os.replace(staging, path)
    except BaseException:
        staging.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    """Generate the data dictionary, or check the committed one against a fresh parse.

    Returns 0 on success, 1 when `--check` finds a difference, 2 on a parse or coverage
    failure, 3 when the file to compare against cannot be read and 4 when the document
    could not be written.
    """
    parser = argparse.ArgumentParser(
        prog="python -m acas_posting.dictionary.generate",
        description="Build data_dictionary/acas_posting_dictionary.json from the frozen "
                    "COBOL-to-MySQL bridge, the copybook record layouts and the frozen "
                    "schema. Reads only; writes only the output path.")
    parser.add_argument("--repo-root", type=Path, default=REPOSITORY_ROOT,
                        help="repository root holding common/, copybooks/ and mysql/ "
                             "(default: the root of the installed package)")
    #  `--output` DEFAULTS RELATIVE TO `--repo-root`, resolved after parsing rather than
    #  bound here as `DATA_DICTIONARY_PATH`. From a checkout the two are the same path,
    #  so nothing changes for the documented invocation. From an INSTALLED distribution
    #  they are not: `REPOSITORY_ROOT` is the parent of the installed package, so
    #  `--repo-root /repo` alone parsed the frozen sources correctly and then tried to
    #  write beside `site-packages/acas_posting`, which is not the repository's
    #  `data_dictionary/` and is not writable in a normal install. A reader had to pass
    #  BOTH options to get a coherent pair, and passing one was silently incoherent
    #  rather than refused. The default now follows the root it is derived from, which
    #  is the only pairing that can be right.
    parser.add_argument("--output", type=Path, default=None,
                        help="where to write the dictionary "
                             "(default: <--repo-root>/data_dictionary/"
                             "acas_posting_dictionary.json)")
    # One mode at a time.
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true",
                       help="do not write: compare a fresh parse against the file at "
                            "--output and report a unified diff of any difference. "
                            "Cannot be combined with --stdout")
    modes.add_argument("--stdout", action="store_true",
                       help="write the document to standard output instead of a file. "
                            "Cannot be combined with --check")
    args = parser.parse_args(argv)

    #  The pairing described at `--output` above, applied once, before any use of it.
    if args.output is None:
        args.output = (
            DATA_DICTIONARY_PATH
            if Path(args.repo_root) == REPOSITORY_ROOT
            else Path(args.repo_root) / DATA_DICTIONARY_PATH.parent.name
            / DATA_DICTIONARY_PATH.name
        )

    try:
        dictionary = build_dictionary(args.repo_root)
        text = render(dictionary)
        _verify(dictionary, text)
    except (OSError, ValueError) as error:
        print("acas_posting.dictionary.generate: %s" % error, file=sys.stderr)
        return 2

    coverage = dictionary.coverage
    summary = ("%d entries covering %d columns, %d host variables, %d copybook fields "
               "and %d program-source work-file fields across %d tables and %d bridges"
               % (coverage.entry_count, coverage.columns_covered,
                  coverage.host_variables_covered, coverage.copybook_fields_covered,
                  coverage.program_source_fields_covered, coverage.in_scope_tables,
                  coverage.in_scope_bridges))

    if args.check:
        try:
            committed = args.output.read_text(encoding="utf-8")
        except OSError as error:
            print("acas_posting.dictionary.generate: %s" % error, file=sys.stderr)
            return 3
        if committed == text:
            print("acas_posting.dictionary.generate: unchanged - %s" % summary,
                  file=sys.stderr)
            return 0
        sys.stderr.writelines(difflib.unified_diff(
            committed.splitlines(keepends=True), text.splitlines(keepends=True),
            fromfile="committed", tofile="regenerated", n=1))
        return 1

    if args.stdout:
        sys.stdout.write(text)
        print("acas_posting.dictionary.generate: %s" % summary, file=sys.stderr)
        return 0

    # A write failure is CLASSIFIED, not allowed to escape as a traceback.
    try:
        _write(args.output, text)
    except OSError as error:
        print("acas_posting.dictionary.generate: could not write %s: %s"
              % (args.output, error), file=sys.stderr)
        return 4
    print("acas_posting.dictionary.generate: wrote %s - %s" % (args.output.name, summary),
          file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
