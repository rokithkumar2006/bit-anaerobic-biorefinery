# BIT Anaerobic Biorefinery — Phase 5 QA Plan

## Purpose
This document separates software smoke tests and user acceptance checks from scientific validation. A passing API test means the service executed; it does not prove the model is calibrated to BIT feedstock or experimentally validated.

## Automated smoke tests in the website
Open **Testing & report** in the deployed website and select **Run automated checks**. The page checks:

1. `GET /api/health` — endpoint response and installed model package status.
2. `GET /data/stp_exploratory_dataset.json` — bundled STP dataset availability and expected row counts (27 tank records and 12 flow/gas records).
3. `POST /api/simulate` — one-day disposable PyADM1ODE run and finite gas, methane and pH outputs. This test request is not stored as a measurement.
4. Public water-quality CSV — whether the third-party source is reachable and returns non-empty CSV content.

Automated checks should be rerun after relevant code or deployment changes. Record errors and do not mark a failed test as passed.

## Manual acceptance checks
Use the website checklist and mark each item only after performing the check:
- Navigate through all pages on desktop and mobile.
- Edit waste-profile data, export, re-import and remove temporary test rows.
- Review STP source counts, add a temporary test row, and test Excel import/export.
- Test Phase 3 sample/run IDs, required fields, duplicate rejection, deletion and workbook portability.
- Run PyADM1ODE twice with the same settings and document any differences.
- Run the public reference analysis and export the combined CSV.
- Confirm the campus biogas ML model stays gated until suitable measured feedstock and measured digester target data exist.
- Confirm optimization is disabled until a current model is trained.
- Confirm source labels, units, missing values and uncertainty notes are visible.
- Save exports and keep original source notebooks/workbooks unchanged.

## Scientific data boundaries
- The STP workbook contains preliminary operational records (27 tank readings and 12 flow/gas records). Several values, column positions, units and measurement intervals require verification against the original notebook and instruments.
- STP wastewater readings are not campus food/garden feedstock characterization.
- The public reference dataset consists of India surface-water monitoring station/year minimum/maximum summaries. A model trained on it and applied to STP observations yields a cross-source comparison, not validated STP prediction.
- The PyADM1ODE integration currently uses reference substrate proxies and an assumed bulk density. It is not calibrated to measured BIT feedstock properties.
- No suitable measured campus digestion-output dataset has been provided for training/independent validation of a campus-specific methane-yield model.
- Do not report simulated/modelled values as experimental observations. Keep measured, public-reference, illustrative and simulated values distinct.

## Exportable report
The website's **Export QA report CSV** combines the current automated test results, individual manual checklist status, and outstanding scientific limitations into a portable CSV file. Manual checklist state and feature data are stored in the browser/device unless exported; they do not automatically sync to a database.

## Current assessment
The QA panel is implemented, but test statuses begin as **Not run**. Do not claim Phase 5 test completion until the automated checks have been executed on the deployed site and manual acceptance checks have actually been carried out.
