# Issue #11 — IFC→XML floating-point serialization on a pinned public input

Date: 2026-11-09 · Scope: **G1-03**, narrow projection improvement only.

## Observed blocker (before change)

The trusted, offline IFC→XML projection of the *input only* for the frozen pilot task `WIN-UPD-DIR-A-002` failed during XSD parsing. A calculated world-coordinate y value was written with a long binary-float expansion (`-0.00000000000005995204332975845`) and libxml2 rejected it as `xs:decimal`. The input file was already byte-cached and pinned; no ground truth, prompt content, private target metadata, or IFC result was handed to an LLM.

## Change and precision bound

`src/runtime/ifc_projection.py::_number` now emits at most **9 decimal places in metres**, without scientific notation or negative zero, and rejects nonfinite or out-of-policy world coordinates (absolute value above 100,000,000). At ordinary IFC world coordinates the worst absolute quantization is **0.5×10^-9 m** (0.5 nm), far below this experiment's 10^-6 m geometry tolerance. This is an explicit *lossy numerical representation*, **not** a lossless native BIM serialization. The immutable original IFC remains the backend data source; an XML no-op must copy the IFC exactly, not reconstruct it from rounded coordinates.

## Measured regression

PowerShell:
```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m unittest tests.test_projection_numeric_precision tests.test_ifc_projection -v
```

- Before fix: four test methods produced five failing assertions and one real-source XML schema error.
- After fix: **15 tests passed**, including pinned public input XML schema validation and source SHA integrity.
- The same pinned source can now project into XML. Its target Window and Opening are represented, but **the requested relocation remains unsupported** because its host Wall world frame is rotated and the trusted opening-move preflight refuses the operation.
- A separate real-source full no-op compile was attempted: the compiler declined with `CompilerError` caused by `BindingError` (`Filling exceeds opening height`) and did not publish any IFC output. This is **still a distinct blocker**; success of XML projection is not proof of end-to-end authoring support. Do not change the no-op compiler status to PASS without a subsequent demonstrated fix.

## Scientific status

This fixes an IFC→XML *read* failure, not official benchmark evaluation, scoring parity, arbitrary rotated-wall geometry or matched D0/I0 authoring. It changes no schema, sampling, tasks, scores, GT files, API provider usage, or real model IFC bytes. All official pilot gates remain blocked. If the precision policy changes again, its error bound and pinned IFC regression must be versioned and reviewed.
