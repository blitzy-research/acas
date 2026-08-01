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
