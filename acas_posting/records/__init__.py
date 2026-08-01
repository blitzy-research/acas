"""Record layouts for the migrated ACAS posting cycle.

One module per record copybook, each declaring a `dataclass` whose attributes
are the copybook's `03`/`05` items in declaration order, field for field.
Nothing is added, nothing is renamed and nothing is corrected: the misnamed
spare fields, the record-length contradictions and the mixed casing are all
the copybooks' own and are preserved (rules R-3 and R-4).

Twenty-seven modules are present, covering the linkage blocks
(`calling_data`, `file_access`, `file_defs`, `maps03`, `test_data_flags`), the
system records (`system_record`, `system_record_4`, `system_dflt`,
`system_final`, `irs_system`), the General Ledger (`gl_batch`, `gl_ledger`,
`gl_posting`, `work_records`), the IRS side (`irs_nominal`, `irs_dflt`,
`irs_final`, `irs_posting`, `spl_irs_posting`), the Sales and Purchase ledgers
and their invoices and open items (`sales_ledger`, `sales_invoice`, `otm3`,
`purchase_ledger`, `purchase_invoice`, `otm5`) and the analysis records
(`analysis`, `value_analysis`).

Storage descriptions are looked up, never transcribed. Each field takes its
digits, scale, sign, usage and carrier type from the generated data dictionary
through `FieldDescriptor`, keyed `<COPYBOOK-RECORD>.<FIELD-NAME>` in the
copybook's own casing, so field metadata is derived rather than copied by eye
across several hundred fields (rule R-5). Most modules build those descriptors
at module scope, which means the first record module imported triggers the
loader's single cached read of the dictionary artifact.

HOW A FIELD PUBLISHES ITS DICTIONARY KEY - AND THE ONE PLACE TO ASK
===================================================================
These modules do not agree on where a field's key is published, and the
variety is real: 977 attributes across 141 dataclasses arrive by eighteen
different routes. A key may be held in the field's own
`dataclasses.field(metadata=...)` under `descriptor`, `cobol_field`,
`dictionary_key`, `acas_posting.dictionary_key` or `twin_dictionary_key`; in a
mapping or tuple bound at class scope or at module scope as `DESCRIPTORS`,
`FIELD_DESCRIPTORS`, `DICTIONARY_KEYS`, `FIELDS` or `ALL_FIELDS`; in a class
constant named after the attribute in upper case; by position in a `FIELDS`
tuple running parallel to the dataclass, which is how an unnamed FILLER item
is reached; or nowhere at all, for a group item whose own type carries its
members' keys.

Do not reimplement that ladder, and do not go looking for a hub here - this
package still publishes no aggregate surface. Ask
`acas_posting.dictionary.loader`, whose mandate is exactly this (Agent Action
Plan section 0.4.1.6, "Runtime lookup so every record field cites its entry"):

    loader.trace_record(GlBatchRecord)      every attribute, in declaration
                                            order, with its key, the route
                                            that carried it and its entry
    loader.field_keys_for(GlBatchRecord)    attribute -> key, reading no file
    loader.entry_for_field(rec, "bcycle")   the entry, or a loud failure
    loader.cite_field(rec, "batch_status")  the three-locator citation

A group item - `amounts`, say, which is the `03 Amounts comp-3.` group of
[copybooks/wsbatch.cob:L40] - carries no key of its own, so its trace names the
type to follow instead. That is a fact about the copybook, not a gap.

`loader.RECORD_FIELD_ROUTES` lists the eighteen in the order they are tried.
Those accessors changed nothing here: every route above keeps working exactly
as its module wrote it, no name is deprecated and no metadata is rewritten
(rules R-3 and R-4). They exist so a consumer need not know which of the 27
modules it happens to be holding.

Six numeric storage classes are modelled and none may be collapsed: `DISPLAY`,
`COMP`, `COMP-3`, `DISPLAY` with `SIGN LEADING` [copybooks/wspost-irs.cob:L21]
and its alternate spelling [copybooks/irswspost.cob:L14], and the
`BINARY-CHAR`/`BINARY-SHORT`/`BINARY-LONG` family. The last is why the sales
statistics fields are Python `int` and not `Decimal` - they are declared
`binary-long` [copybooks/wssl.cob:L46-L52], so their truncation on divide is
integer truncation, which is exactly what makes the moving-average defect
reproducible. Monetary and quantity values are `decimal.Decimal`; no
accounting value passes through a binary float (rule R-2).

This is a leaf layer. A record module may import `acas_posting.cobol.field`,
`acas_posting.dictionary.loader` and the standard library, and nothing else.
`dal` is the live temptation, because every handler takes a record as a
parameter; the arrow points one way, `dal` imports `records`.

Condition names are not here. The `88`-level predicates over these records
belong to `acas_posting.cobol.condition_names`, so a record stays a record.

This marker assigns an empty `__all__`: the package publishes no aggregate
surface, and each record type is imported from its own module.
"""

# Provenance. The COBOL system, its bridge programs and its schema are the
# maintainer's work and carry his own notice; this package migrates the posting
# cycle's behaviour and restates none of it. The rule identifiers R-1 through
# R-6 are the Agent Action Plan's own (section 0.7.2).

# Deliberately empty: this package publishes no aggregate surface. Import each
# record type from its own module, as the layering contract requires.
__all__: list[str] = []
