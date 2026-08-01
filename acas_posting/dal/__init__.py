"""Data access for the migrated ACAS posting cycle.

In COBOL a posting program reaches a table through four hops: a facade
paragraph supplied by a shared copybook, a numbered handler program
(`common/acas0NN.cbl` and `common/acasirsubN.cbl`, both patterns rather than
literal paths), a generated bridge program, and finally SQL. Here that
collapses to two layers - a facade publishing the verb vocabulary, and one
module per handler owning the SQL for its tables.

Present in this package
    connection      the engine and connection, credentials from the `RDB-Data`
                    block [copybooks/wsfnctn.cob:L57-L64]; per-statement
                    autocommit as the COBOL does, no pooling; identifier
                    quoting, because every ACAS table and column name contains
                    a hyphen
    status          the `FS-Reply` value set 0/10/21/22/23/99, the `We-Error`
                    codes, the SQLSTATE mapping and the retry ladder
    cursor_state    ISAM `START` / `READ NEXT` emulation driven by each
                    bridge's declared key table and relation directive

Target inventory, not yet present: `facade`, and one module per handler -
acas000_system, acas005_gl_nominal, acas006_gl_posting, acas007_gl_batch,
acas008_spl_posting, acas012_sales, acas013_value, acas015_analysis,
acas016_invoice, acas019_otm3, acas022_purch, acas026_pinvoice, acas029_otm5,
acasirsub1_irs_nominal, acasirsub3_irs_dflt, acasirsub4_irs_posting and
acasirsub5_irs_final. The mapping is recorded here because it is the shape the
present modules are built to serve, not because the modules exist.

One module per handler, not per table. The COBOL call chain routes through
handlers and they are not one-to-one with tables: `acas000` dispatches to four
bridges by key number, and `acas016` and `acas026` each own a header table plus
a lines table. Mirroring the handler boundary keeps the Python module set in
correspondence with the COBOL programs and preserves the dispatch rather than
flattening it.

The facade will publish two name sets over one implementation: the
entity-named vocabulary of [copybooks/Proc-ACAS-FH-Calls.cob] and the
handler-named vocabulary of [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob]. The
difference is behavioural, not cosmetic - the IRS convention wraps each call in
a per-handler error check that returns from the program outright on an
unrecoverable open failure [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364],
while the General/Sales/Purchase convention has no such paragraph and its
callers test the reply inline.

Constraints on everything in this package
    * SQL against the frozen schema only - `SELECT`, `INSERT`, `UPDATE`,
      `DELETE`. No DDL of any kind, and no index, however tempting: gl072
      locates its nominal account with a sequential read, so the ordering the
      upstream sort produces is what makes the posting correct.
    * SQLAlchemy at Core level; no ORM entity layer, which would want to own
      schema definition and would obscure the statement ordering the scenario
      state diff compares.
    * Strictly sequential - no threads, no asyncio, no multiprocessing, no
      connection pool - matching the single-threaded COBOL.
    * Exact numerics only. Every value arrives as `Decimal`, `int`, `str`,
      `bytes` or `None`; never a binary float.
    * The bridge is not a transparent pipe. Where the copybook declaration, the
      bridge host variable and the column disagree, the handler module
      reproduces the bridge's own conversion, because the conversion happens
      before any SQL executes.

This marker declares no name and performs no input or output.
"""
