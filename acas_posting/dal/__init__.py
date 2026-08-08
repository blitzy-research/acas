"""Data access for the migrated ACAS posting cycle.

The COBOL reaches a table through four hops - a facade paragraph from a shared
copybook, a numbered handler program, a generated bridge program, then literal
SQL. Here that becomes two: `facade` publishes the verb vocabulary, and one
module per handler owns the SQL for its tables.

    facade          the single doorway, publishing both COBOL naming conventions
    connection      the open path and the connection the handlers share
    status          the `FS-Reply` protocol and the operation vocabulary
    cursor_state    ISAM `START` / `READ NEXT` positioning

Then the seventeen handler modules, each owning the SQL for its own tables:
acas000_system, acas005_gl_nominal, acas006_gl_posting, acas007_gl_batch,
acas008_spl_posting, acas012_sales, acas013_value, acas015_analysis,
acas016_invoice, acas019_otm3, acas022_purch, acas026_pinvoice, acas029_otm5,
acasirsub1_irs_nominal, acasirsub3_irs_dflt, acasirsub4_irs_posting and
acasirsub5_irs_final.

ONE MODULE PER HANDLER, NOT PER TABLE. The COBOL call chain routes through
handlers and they are not one-to-one with tables: `acas000` dispatches to four
bridges by key number, and `acas016` and `acas026` each own a header table plus a
lines table. Mirroring the handler boundary keeps the Python module set in
correspondence with the COBOL programs and preserves the dispatch rather than
flattening it.

THE FACADE PUBLISHES TWO NAME SETS OVER ONE IMPLEMENTATION: the entity-named
vocabulary of [copybooks/Proc-ACAS-FH-Calls.cob] and the handler-named vocabulary
of [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob]. The difference is behavioural, not
cosmetic - the IRS convention wraps each call in a per-handler error check that
returns from the program outright on an unrecoverable open failure
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364], while the
General/Sales/Purchase convention has no such paragraph and its callers test the
reply inline.

Constraints on everything in this package, each with the reason it exists rather
than the rule number alone:
    * SQL against the frozen schema only - `SELECT`, `INSERT`, `UPDATE`,
      `DELETE`. No DDL of any kind, and no index however tempting: `gl072`
      locates its nominal account with a sequential read, so the ordering the
      upstream sort produces is what makes the posting correct.
    * SQLAlchemy at Core level; no ORM entity layer, which would want to own
      schema definition and would obscure the statement ordering the scenario
      state diff compares.
    * Strictly sequential, matching the single-threaded COBOL.
    * Exact numerics only. Every value arrives as `Decimal`, `int`, `str`,
      `bytes` or `None`; never a binary float.
    * THE BRIDGE IS NOT A TRANSPARENT PIPE. Where the copybook declaration, the
      bridge host variable and the column disagree, the handler module reproduces
      the bridge's own conversion, because that conversion happens before any SQL
      executes.

This marker declares no name and performs no input or output.
"""
