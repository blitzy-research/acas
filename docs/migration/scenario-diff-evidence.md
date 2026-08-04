# ACAS posting-cycle scenario diff evidence

This document records the observed parity evidence for the eight scenarios
mandated by the Agent Action Plan (AAP). It is not a statement of intended
behaviour. Each verdict below was produced by running the compiled COBOL cycle
and the Python 3.12 migration from the same loader-built seed, normalising both
captures, and requiring an empty state diff.

> “seed identically through the maintainer's load programs, run the compiled
> cycle, dump the affected tables ordering-normalised, reset, run the Python
> cycle, dump again — and the diff **must be empty**.”

The evidence in this file was last re-run on **2026-08-04**. The complete
standalone sweep is recorded in
`/tmp/blitzy_phase5_run_parity_all_eight.log`; every invocation of
`harness/run_parity.sh` completed stages 1 through 10 with exit status zero.
The committed scenario tier independently passed in both file orders:

- declared order: **93 passed** in 153.99 seconds;
- reverse order: **93 passed** in 163.42 seconds.

Those aggregate test records are
`/tmp/blitzy_phase5_scenario_tier_original_order.log` and
`/tmp/blitzy_phase5_scenario_tier_reverse_order.log`.

## Rules provenance

There is no separate user-rules document. The six binding rules live in AAP
§0.7.2. The rules relevant to this evidence are:

1. **R-1 — No COBOL at runtime.** The compiled system is confined to
   `harness/` and is used only as an out-of-process comparison oracle. Nothing
   under `acas_posting/` imports or invokes it.
2. **R-2 — Zero binary floating point.** Accounting values are exact decimal
   strings or integers in the captures. A binary `float` makes the dump
   malformed and the comparison errors rather than passes.
3. **R-3 — No new validation, fields, schema changes, or concurrency.** The
   frozen schema is re-applied verbatim and scenarios run strictly one at a
   time.
4. **R-4 — Legacy anomalies are reproduced, never corrected.** Several
   scenarios deliberately prove a no-op or an odd stored value. Such an empty
   diff is success because the compiled behaviour is the specification.
5. **R-5 — Full traceability.** Program, paragraph, field, and data-access
   mappings are recorded in [`traceability.md`](traceability.md).
6. **R-6 — Compiled behaviour is the tie-breaker.** Where reading left more
   than one possible interpretation, the result below comes from the compiled
   run and is recorded in
   [`ambiguity-resolutions.md`](ambiguity-resolutions.md).

The frozen COBOL, bridge, copybook, and schema files were read but not edited.
Build-only compatibility shims are installed solely in `$ACAS_BUILD`.

## Verdict vocabulary

- **EMPTY DIFF — OBSERVED**: both complete, attested normalised trees were
  compared and `harness/diff_states.py` returned zero.
- **NON-EMPTY DIFF — OBSERVED**: the comparison returned one. No scenario in
  this evidence set has this status.
- **HARNESS ERROR**: the comparison could not be performed and returned two,
  or an earlier protocol stage failed. This is never treated as parity.

For an empty diff, stage 10's comparison report contains no row-level finding.
The driver then prints its own explicit summary that the two states are
identical. The driver summary is not a substitute for the diff exit code; it is
printed only after that code is zero.

## The rigid ten-stage protocol

`harness/run_parity.sh` executes the following order and stops at the first
non-zero status:

1. `harness/reset_db.sh` — re-apply the frozen schema and seed the scenario.
2. `harness/run_cobol_scenario.sh` — drive the compiled menu path.
3. `harness/dump_tables.py --side cobol` — capture the bounded tables.
4. `harness/normalize.py --side cobol` — canonicalise representation only.
5. `harness/reset_db.sh` — re-apply and re-seed the same scenario.
6. `harness/run_python_scenario.sh` — drive the migrated cycle.
7. `harness/dump_tables.py --side python` — capture the same bounded tables.
8. `harness/normalize.py --side python`.
9. Verify that both complete manifests were published.
10. `harness/diff_states.py` — require an empty diff.

The standalone command used for each scenario was:

```bash
C="docker exec \
  -e ACAS_SEED_AUTOCOMMIT=on \
  -e ACAS_TIMEOUT_DRIVE=300 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/repo \
  acas-harness-001-gnucobol-1"

$C sh -lc '
  cd /repo
  harness/run_parity.sh \
    harness/scenarios/<scenario>.yaml \
    --seed-dir /data/fixtures/<scenario>
'
```

The fixture directory says **where** the files are. The scenario's
`seed_files` list remains the authority on **which** files may be used.
`run_parity.sh` supplies both `ACAS_DATA` and `ACAS_LEDGERS` as the isolated
`/data/<scenario>` directory for the two run stages. For
`period_end_totals`, it drives all four declared menu operations sequentially
without resetting between them and preserves operation one's seed attestation
for the eventual COBOL dump.

### Seeding constraints

- `common/masterLD.sh` is not invoked. It is marked untested
  `[common/masterLD.sh:L4-L5]`, its 24 loader lines at L93-L116 are
  syntactically invalid, and its final interactive pager would block a
  non-interactive run.
- `harness/seed.sh` reproduces the per-file loader contract instead.
- The harness establishes the loader's required seeding mode explicitly with
  `ACAS_SEED_AUTOCOMMIT=on`; without that declared deviation the measured
  result is zero persisted rows and exit 76.
- Every generated fixture and run artifact containing credentials or execution
  data is owner-only.

### Diff and normalisation contract

`harness/dump_tables.py` emits exactly five keys in order:
`table`, `primary_key`, `columns`, `row_count`, and `rows`. Rows are ordered by
the table's single-column primary key. Decimal values are canonical strings;
integer fields remain integers.

`harness/normalize.py` performs exactly three representation jobs:

1. remove trailing ASCII spaces from fixed-character columns;
2. render decimals at the column's declared scale, without rounding;
3. canonicalise only the explicit five-column date-text allow-list.

It does not ignore rows, coerce types, apply tolerances, or alter integer day
numbers. `harness/diff_states.py` aligns rows by primary-key value, compares
exactly, and has no ignore list.

## Inputs common to all scenarios

- Text clock: **`21/09/2025`**, DD/MM/CCYY.
- Binary clock: **`Run-Date = 155127`**, using the 1600-12-31 epoch
  `[common/maps04.cbl:L39-L42]`.
- `SYSTEM-REC.FILE-SYSTEM-USED = 1`.
- `Cyclea = Scycle = 1`.
- IRS fan-out: one space, meaning General Ledger only unless the IRS operation
  itself is being driven.
- Runtime mode: sequential, one shared MariaDB, no xdist or concurrent
  scenarios.

Both runners query `SYSTEM-REC` before and after their operation. They refuse
the flat-file selector, assert the Cyclea/Scycle shared-storage view, and read
back the pinned `RUN-DAT`. These checks close the false-pass paths where a run
could otherwise be deterministic while bypassing MariaDB or carrying a
maps04-degraded zero date.

## Observed summary

| Scenario | Declared table effect | Observed operation status | Tables | COBOL rows | Python rows | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `clean_batch_gl` | unchanged | 0 | 3 | 6 | 6 | **EMPTY DIFF — OBSERVED** |
| `clean_batch_sl` | changed | 0 | 10 | 21 | 21 | **EMPTY DIFF — OBSERVED** |
| `clean_batch_pl` | changed | 0 | 10 | 17 | 17 | **EMPTY DIFF — OBSERVED** |
| `clean_batch_irs` | changed | 0 | 4 | 50 | 50 | **EMPTY DIFF — OBSERVED** |
| `mixed_accepted_rejected` | unchanged | 0 | 3 | 8 | 8 | **EMPTY DIFF — OBSERVED** |
| `period_end_totals` | changed | 0, 0, 0, 0 | 14 | 45 | 45 | **EMPTY DIFF — OBSERVED** |
| `control_total_mismatch` | unchanged | 5 | 3 | 6 | 6 | **EMPTY DIFF — OBSERVED** |
| `empty_batch` | unchanged | 0 | 3 | 5 | 5 | **EMPTY DIFF — OBSERVED** |

The harness wrapper status is distinct from the operation status. A wrapper
exits zero after it has verified a declared operation status, including the
behavioural status 5 in `control_total_mismatch`. Machine-readable
`OPERATION_STATUS` records carry the operation values shown above.

## Per-scenario evidence

### `clean_batch_gl`

- **Operation:** `gl_post_cycle`.
- **Seed:** `system.dat`, `ledger.dat`, `batch.dat`, `posting.dat`.
- **Affected tables:** `GLBATCH-REC`, `GLLEDGER-REC`,
  `GLPOSTING-REC`.
- **Expected and observed effect:** unchanged.
- **Expected and observed status:** 0.
- **Evidence:** both sides contain six rows across the three bounded tables;
  stage 10 found no difference.

The no-op is deliberate. Compiled measurement established that
`bb000-HV-Load` does not move `WS-Post-rrn` to `HV-POST-RRN`. The one
reachable posting is therefore persisted under key zero and skipped by
`[general/gl070.cbl:L490-L493]`; the end-batch rewrite at
`[general/gl072.cbl:L372-L377]` is unreachable and `POSTED` remains zero.
The determinism test therefore witnesses the pinned clock through the
runner's database-backed `SYSTEM-REC.RUN-DAT` readback rather than demanding
an impossible batch timestamp.

Manifest SHA-256:

- COBOL: `cf94ac60332fd35cfc18d6a3c71e7a1303873017fabe94617d7d732f46b0ef63`
- Python: `2ba368cba37b2fc4bcd2e0a7e1cf292c44c1acf8a6d1c2e52fba6884b2413260`

### `clean_batch_sl`

- **Operation:** `sl_invoice_post`.
- **Seed:** `system.dat`, `analysis.dat`, `value.dat`, `salesled.dat`,
  `invoice.dat`, `openitm3.dat`.
- **Affected tables:** `ANALYSIS-REC`, `GLBATCH-REC`,
  `GLPOSTING-REC`, `PSIRSPOST-REC`, `SAINV-LINES-REC`,
  `SAINVOICE-REC`, `SAITM3-REC`, `SALEDGER-REC`, `SYSTOT-REC`,
  `VALUEANAL-REC`.
- **Expected and observed effect:** changed.
- **Expected and observed status:** 0.
- **Evidence:** 21 rows on each side and an empty diff.

The open-item invoice numbers are 10 and 11 rather than colliding with the
phase-one invoice-header keys. The COBOL-only `sl830` pre-pass was observed to
leave all four autogen tables empty with the seeded switch off.

Manifest SHA-256:

- COBOL: `e5ee3411d34b66df35fb810f429cdb9b2083dcfe9be7a647a1074f2149b8328f`
- Python: `6351e0e0c9c3f80154ec9c43862ea2a05f1533d2b1da72c0dca3d0d9b2e0f6d2`

### `clean_batch_pl`

- **Operation:** `pl_order_post`.
- **Seed:** `system.dat`, `analysis.dat`, `value.dat`, `purchled.dat`,
  `pinvoice.dat`, `openitm5.dat`.
- **Affected tables:** `ANALYSIS-REC`, `GLBATCH-REC`,
  `GLPOSTING-REC`, `PSIRSPOST-REC`, `PUINV-LINES-REC`,
  `PUINVOICE-REC`, `PUITM5-REC`, `PULEDGER-REC`, `SYSTOT-REC`,
  `VALUEANAL-REC`.
- **Expected and observed effect:** changed.
- **Expected and observed status:** 0.
- **Evidence:** 17 rows on each side and an empty diff.

`Purch-SortCode` is pinned to `"0"`. Compiled probes showed that the
`binary-long` caller storage is reinterpreted through the bridge's
`PIC 9(8) COMP` linkage without conversion; a realistic six-digit sort code
therefore exceeds the frozen `mediumint(6) unsigned` column. The zero seed is
the reachable store state, not a correction to the migration.

Manifest SHA-256:

- COBOL: `c3726b2d1047b3dd007f81814d127acb27fae69e14e4518a1c6fee3d49d09b98`
- Python: `f58f32ba47f8bb240fa0a081eb79271ed6ebbce9e5c59efe653f4dce8f90d0be`

### `clean_batch_irs`

- **Operation:** `irs_post`.
- **Answer:** `irs_clear_postings: "Y"`.
- **Seed:** `system.dat`, `irsacnts.dat`, `irsdflt.dat`,
  `irsfinal.dat`, `irspost.dat`, `postings2irs.dat`.
- **Affected tables:** `IRSDFLT-REC`, `IRSNL-REC`,
  `IRSPOSTING-REC`, `PSIRSPOST-REC`.
- **Expected and observed effect:** changed.
- **Expected and observed status:** 0.
- **Evidence:** 50 rows on each side and an empty diff.

The six posting numbers are 1000 through 6000, producing six distinct
measured relational keys rather than collapsing through the bridge conversion.
Answering `Y` reaches `acas008-Open-Output` and the bounded transfer delete;
`PSIRSPOST-REC` may therefore legitimately end empty on both sides.

Manifest SHA-256:

- COBOL: `bf534469e144ad14bb26f6b6ea4c11a70bcd1cad39b946b5715fdc08de749a3d`
- Python: `7c4e9a8b22b376725e0a03a9cb3a0d128f420fee33b3c85cd13fa8cb33c4fcfe`

### `mixed_accepted_rejected`

- **Operation:** `gl_post_cycle`.
- **Seed:** `system.dat`, `ledger.dat`, `batch.dat`, `posting.dat`.
- **Affected tables:** `GLBATCH-REC`, `GLLEDGER-REC`,
  `GLPOSTING-REC`.
- **Expected and observed effect:** unchanged.
- **Expected and observed status:** 0.
- **Evidence:** eight rows on each side and an empty diff.

The measured RDBMS loader can persist only one posting primary key because
`HV-POST-RRN` is not loaded. The scenario therefore uses two batches and one
posting and proves the reachable no-op. It does not fabricate six independently
addressable postings merely to make the two silent `gl072` skip sites appear.

Manifest SHA-256:

- COBOL: `ba7c5c0586c71d42e6c8db936e8eeb6a61f77635cc3b63827f806082f099e0d8`
- Python: `8206a0c815708c43a51ec149dc8100b2411106738228e7e789232664e5c656ee`

### `period_end_totals`

- **Operations, in order:** `sl_invoice_post`, `sl_cash_post`,
  `pl_order_post`, `pl_payment_post`.
- **Answer:** `payment_post_confirm: "YES"`.
- **Seed:** `system.dat`, `analysis.dat`, `value.dat`, `salesled.dat`,
  `invoice.dat`, `openitm3.dat`, `purchled.dat`, `pinvoice.dat`,
  `openitm5.dat`.
- **Affected tables:** `ANALYSIS-REC`, `GLBATCH-REC`,
  `GLPOSTING-REC`, `PSIRSPOST-REC`, `PUINV-LINES-REC`,
  `PUINVOICE-REC`, `PUITM5-REC`, `PULEDGER-REC`,
  `SAINV-LINES-REC`, `SAINVOICE-REC`, `SAITM3-REC`,
  `SALEDGER-REC`, `SYSTOT-REC`, `VALUEANAL-REC`.
- **Expected and observed effect:** changed.
- **Expected and observed statuses:** 0, 0, 0, 0.
- **Evidence:** 45 rows on each side and an empty diff.

This is the only two-menu scenario. The oracle driver runs four separate menu
processes without a reset. Open-item keys are above the header range, the
Purchase sort code is reachable, and the build-copy menu shim preserves
`FILE-SYSTEM-USED = 1` in the flat mirror so the next menu process does not
silently switch to indexed files.

Manifest SHA-256:

- COBOL: `def2565ee813b5b0c0b112f6a822e618da2277a1538c2523d990097572491eca`
- Python: `d8eab313bdd9356d3719856093e71890e1d6aabaaa3ed6fa503ff84619688dd3`

### `control_total_mismatch`

- **Operation:** `gl_post_cycle`.
- **Seed:** `system.dat`, `ledger.dat`, `batch.dat`, `posting.dat`.
- **Affected tables:** `GLBATCH-REC`, `GLLEDGER-REC`,
  `GLPOSTING-REC`.
- **Expected and observed effect:** unchanged.
- **Expected and observed operation status:** 5.
- **Wrapper status:** 0 after verifying the behavioural status.
- **Evidence:** six rows on each side and an empty diff.

The compiled menu's `gl060a` page choice has no `AUTO` clause
`[general/gl070.cbl:L421]`, so the driver sends `X` followed by Return, then a
second Return for the end-report acknowledgement. The menu returns after term
code 5 and does not dispatch `gl071` or `gl072`
`[general/general.cbl:L810-L811]`; the absence of their writes is the expected
database effect.

Manifest SHA-256:

- COBOL: `39e949de810ade9ab2e2481c1286161b3217808bdd705a4cadd5f497dda208a6`
- Python: `86c2e560a95aa682572aa2d400222cc5606303705b56e159a015db2f4b48e42b`

### `empty_batch`

- **Operation:** `gl_post_cycle`.
- **Seed:** `system.dat`, `ledger.dat`, `batch.dat`; deliberately no
  `posting.dat`.
- **Affected tables:** `GLBATCH-REC`, `GLLEDGER-REC`,
  `GLPOSTING-REC`.
- **Expected and observed effect:** unchanged.
- **Expected and observed status:** 0.
- **Evidence:** five rows on each side and an empty diff.

The scenario proves that the complete protocol is stable over a batch with no
posting rows. It is not accepted merely because both posting tables are empty:
the seeded batch and ledger rows, run attestations, file-system selector,
clock readback, and seed fingerprints are all checked independently.

Manifest SHA-256:

- COBOL: `7c895dc3c791f7a3726e360235805f0a2b9c2ac3d9288eab87297d27dd4c6933`
- Python: `55546dcc6bec6b66b405b151b898de607f6254faf8d915117fc5671cc9c68836`

## Determinism evidence

`tests/determinism/test_two_runs_byte_identical.py` runs
`clean_batch_gl` and `clean_batch_irs` twice each under the same pinned clock,
relocates run A before run B can overwrite it, compares structurally, and then
compares every affected-table file byte for byte.

Observed on 2026-08-04:

```text
6 passed in 18.33s
```

Evidence:
`/tmp/blitzy_phase5_determinism_after_witness_fix.log`.

The clock witness is database-backed:

- pre-run `SYSTEM-REC.FILE-SYSTEM-USED = 1`;
- post-run `SYSTEM-REC.RUN-DAT = 155127`.

This preserves the non-vacuity guard for the measured `clean_batch_gl` no-op,
where requiring `GLBATCH-REC.POSTED = 155127` would demand a frozen rewrite
that the zero-key posting cannot reach.

## Coverage limits stated explicitly

- No mandated scenario drives `gl080`; its end-of-cycle path remains outside
  this eight-scenario evidence set.
- `gl051` has no CLI entry point. The mismatch journey observes the gate
  indirectly through `gl070` and the menu's term-code boundary.
- The General and Purchase sub systems were not fully re-tested by the
  maintainer. Their expected values therefore come only from the compiled
  oracle, never from intended behaviour described in prose.
- Plaintext transport is permitted only because the compiled program has no
  stronger check. Every run reports this as a non-fatal security finding.

## Artifact layout

For each scenario `<name>`:

```text
/out/<name>/cobol.normalized/
/out/<name>/python.normalized/
/out/run-logs/<name>/cobol.log
/out/run-logs/<name>/cobol.result
/out/run-logs/<name>/cobol.run-status
/out/run-logs/<name>/cobol.seed-fingerprint
/out/run-logs/<name>/python.log
/out/run-logs/<name>/python.run-status
/out/run-logs/<name>/python.seed-fingerprint
```

`period_end_totals` additionally has one COBOL transcript for each operation
after the first. All credential-bearing and execution-data files are mode
0600 or live below an owner-only directory.

## Conclusion

All eight mandated scenarios are **EMPTY DIFF — OBSERVED**. The result was
obtained through the rigid protocol, reproduced in both scenario orders, and
supplemented by a passing two-run determinism tier. No frozen source or schema
was modified to obtain it.
