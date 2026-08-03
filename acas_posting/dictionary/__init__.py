"""The machine-readable data dictionary: model, generator and runtime loader.

The field-level authority for the migration. Every record field's digits, scale,
sign, usage, width and provenance is DERIVED from the frozen sources rather than
transcribed by hand, which is what rule R-5 requires and what eliminates a whole
class of transcription error across several hundred fields.
    model       the copybook / bridge host-variable / MySQL column triple
    generate    parses the frozen sources and emits the JSON artifact
    loader      runtime lookup, so every field can cite its entry

The authority is the BRIDGE, not the copybooks. The user's requirement, preserved
in the plan, is that the maintainer's one-way COBOL-to-MySQL bridge defines the
record-layout-to-table mapping. `IRSPOSTING-REC` proves why it matters:
`POST4-DAY`, `POST4-MONTH` and `POST4-YEAR` have no counterpart in any copybook
and exist only because the bridge derives them under a guarded substring rule
[common/irspostingMT.cbl:L982-L987], so a dictionary built from the copybooks
alone would omit three columns of a posting table.

Where the three layers disagree - a sign lost between a signed copybook field and
an unsigned column, a name widened, a group flattened - the disagreement is
RECORDED as drift and left unadjudicated. Deciding it here would hide it.
"""

# Provenance. Every fact this package publishes is derived from the maintainer's one-way
# COBOL-to-MySQL bridge (common/*MT.scb, common/*MT.cbl), the record copybooks under
# copybooks/, and the frozen schema mysql/ACASDB.sql.

# The public surface is deliberately empty: this file is a package marker, and a marker
# that exports something has taken on a second job.
__all__: tuple[str, ...] = ()
