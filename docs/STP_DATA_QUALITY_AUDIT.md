# STP Operational Data Quality Audit

## Scope

This review covers the bundled transcription at `data/stp_exploratory_dataset.json`.
It is a quality-control checklist, not a replacement dataset and not a certification
that the original workbook has been transcribed correctly.

## Current contents

- 27 tank / sampling-point records.
- 12 flow / gas records.
- Source workbook label: `BIT_STP_Operational_Data_20261022.xlsx`.
- Source SHA-256 recorded in the JSON: `caf51f66bf62f879ba42435528981b96edf870ebb9d909550359f4c6bf87d294`.

## Issues requiring source verification

1. **Flow/gas totals:** several stored totals do not clearly reconcile with the three recorded readings. For example, the 8 October 2026 "Pre-digester to main digester" row contains readings 173, 206, and 134, while the written total is 3406. Do not recompute or replace the written total without checking the original workbook or instrument log.
2. **Units and intervals:** gas-flow units and reading intervals are unclear for multiple rows. A number without a verified unit and time interval must not be converted to a daily gas-production rate.
3. **Tank-column alignment:** the source notes flag uncertainty for BOD, DO, TSS, TDS, and turbidity in several rows. Confirm each value against the original page and instrument record.
4. **Missing fields:** blanks represent unknown/unrecorded values, not zero.
5. **Provenance:** distinguish workbook transcription, website-entered rows, measured observations, public reference data, and modelled outputs.
6. **Training eligibility:** these STP wastewater records are not campus food/garden feedstock characterization or measured anaerobic-digestion methane-yield targets. Do not use them as such.

## Recommended review fields

For each record, retain the original value and add separate fields for:

- `verification_status`: `unreviewed`, `verified`, or `needs_correction`
- `verified_by` and `verified_at`
- `source_page_or_instrument_id`
- `unit_verified` and `measurement_interval_verified`
- `quality_flags` as a list, without deleting the original notes

## Acceptance criteria before model training

- Confirm source row, column, unit, and sampling time against the original workbook or instrument log.
- Resolve duplicate identifiers and verify date parsing.
- Keep missing values null/blank; never silently impute zero.
- Check physical ranges and cross-field consistency with domain review.
- Keep training, validation, and test sets grouped by independent sample/run IDs to reduce leakage.
- Record the model version, feature definitions, units, split method, metrics, and limitations.
- Do not call a model validated for BIT until independent measured digestion runs are available.

## Safe handling

This audit deliberately leaves `data/stp_exploratory_dataset.json` unchanged. Corrections should be made only after the source records are checked and should preserve the original transcription for traceability.
