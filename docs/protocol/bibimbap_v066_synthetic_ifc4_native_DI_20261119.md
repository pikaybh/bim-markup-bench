# BIBIMBAP v0.66 / Issue #247 — synthetic IFC4 native D_FULL / D_MANAGED / I_NATIVE engineering evidence

**Status:** REAL local native IFC4 engineering proof, **NOT a blinded/model-generated experiment, original GNI asset validation, original author task grade, rights certification, trial authorization or general IFC4 editor**.

## Motivation and scope

The newly identified GNI public-source candidate declares IFC2X3 and **IFC4** models (not IFC4X3). Previously frozen source-neutral hosted Door creation tested **IFC2X3 + IFC4X3**, and Window move/delete admitted only **IFC4X3**. Thus *a schema family central to the prospective GNI cohort had no native source-neutral hosted-door D/I engineering proof*. No actual GNI IFC was downloaded, opened or uploaded in this checkpoint. The original 31 previously inspected BIBIMBAP source families remain excluded from fresh-blind classification.

Instead, this checkpoint produces **four wholly self-authored IFC4 sources**, testing physical wall-mounted Door + Opening **create** through two source unit systems and two represented straight Wall axes:

| IFC4 synthetic scenario | Local SI length | Wall axis | Expected true CSG void volume |
| --- | --- | --- | ---: |
| metre-X | 1 metre/unit | X | 0.462 m³ |
| metre-Y | 1 metre/unit | Y | 0.462 m³ |
| millimetre-X | 0.001 metre/unit | X | 0.462 m³ |
| millimetre-Y | 0.001 metre/unit | Y | 0.462 m³ |

Each source consists of a physical 6 m × 0.2 m × 3 m wall and an **unrelated opaque slab** whose native entity attributes, relationships and physical shape must remain preserved. The task is a *self-authored developer control* to add a true through-thickness 1.05 m × 0.2 m × 2.2 m aperture hosting a nominal 1.00 m × 0.06 m × 2.10 m door. No GNI source, BIBIMBAP benchmark answer, source hidden grader or original task-specific coordinates were used. This is not an unseen evaluation set and provides no statistical evidence of agent capability.

## Actual implemented representation and runtime controls

Implementation:

- Self-authored original IFC4 generator: tools/bibimbap_v066_ifc4_synthetic_host.py
- Isolated IFC4 schema-compatible copy of the source-neutral v0.65 hosted-Door grammar and trusted compiler: tools/bibimbap_v066_ifc4_source_neutral_door.py
- Isolated extension of v0.66 STEP-number-independent full IFC semantic/physical gate to **IFC4**: tools/bibimbap_v066_ifc4_native_semantic_admission.py
- Actual local D/I auditor with independent pure Python worker code and source controls: tools/audit_bibimbap_v066_synthetic_ifc4_DI.py
- 60 negative/positive unit checks: tests/test_bibimbap_v066_synthetic_ifc4_DI.py
- Canonical report: reports/bibimbap_v066_synthetic_ifc4_DI_20261119.json

**Frozen report SHA256:** 40149f8f4f86f8e86421926d71d11ccdfb9bb0d99b573c943127395dcebcb378.

The original v0.65 grammar and v0.66 evaluator source files are NEVER modified (past SHA-frozen reports remain reproducible). The added IFC4 source-neutral compiler preserves the old v0.65 final-state XML namespace and version field, and extends its schema admission to IFC4 in a separately versioned module. D_FULL sends complete final BuildingState XML with immutable source snapshot and complete Wall roster; D_MANAGED sends a complete linked final roster and new physical products rehydrated from the source SHA. **Neither D arm accepts an operation-list XML command** or gives the authoring agent direct IfcOpenShell edit tooling. Source is a native IFC-backed partial projection, never a complete lossless IFC-to-XML transformation.

The third **I_NATIVE** path uses independently authored ordinary Python/IfcOpenShell source code, no imports from the D compiler or private grader. It actually executes and commits in the previously SHA-pinned **local Linux Docker sandbox**, on a fresh original IFC clone. Crucially the independent Python calculates Door overall width and height using the actual source length-unit scale, **NOT a hard-coded millimetre multiplier**. These are deliberately authored engineering controls, not AI-produced answers.

All three native outputs pass an independent source-bound native IFC checker that verifies:
- Retention of original native IFC schema, entity/relationship/anonymous STEP graph fingerprints independent of numeric STEP labels, original GUID identity and all unchanged product geometry.
- Exact one new hosted IfcDoor, IfcOpeningElement, IfcRelVoidsElement, IfcRelFillsElement and one storey containment, with source wall and new target geometry connected correctly.
- Actual closed-solid world geometry and through-thickness wall boolean CSG volume (0.462 m³).
- Correct project LENGTHUNIT conversion in real native IfcDoor dimensions, including metre versus millimetre sources.
- No new IfcOpenShell schema validator findings; no unexplained original IFC changes or leaked anonymous native entities.

**12 genuine native outputs** (4 sources × 3 D_FULL/D_MANAGED/I_NATIVE) have equal native physical edit semantic digests. **4 genuine STEP-number reindexed IFC variants** pass the independent graph semantic gate. **28 negative controls** (4 sources × 4 malformed D XML + 3 actual mutated native IFC results) reject false acceptance: source hash tamper, incomplete Wall roster, fake XML operation nodes, physically impossible new door dimensions, original slab tampering, an orphan native entity and removal of the filling relation. Source generator canonicalizes native IFC SET order of units and spatially contained products, ensuring four original source IFC SHA values and the report bytes reproduce on repeated fresh runs, rather than hashing accidental iteration order.

### Frozen original synthetic source SHA256s

| Self-authored IFC4 source | SHA256 |
| --- | --- |
| metre-X | b7657e5fc4da366dac29bbdb8548d79750627d86bad9c5f1275af947cd1ed60f |
| metre-Y | 98fc29299dfa3ce55fa009d9e5ec2361ff5cc5dea7c610a4677bf19d23c911aa |
| millimetre-X | d0df2b3a96d9b3fdb4e6749d4565392bb53df9fc3f360efe9a6e3139d2e7e782 |
| millimetre-Y | d5890b0af03d6dcce502ad430182ccf407a3d3b858d9294f44adc301e63e0663 |

No source IFC file is committed to Git. The generator recreates the source from a fixed self-authored UUID namespace and canonical SET member ordering. The exact code and per-source SHA are in the report, rather than distributing source geometry or a benchmark GT.

## Scientific limits and next priority

This is an **IFC4 native authoring-compatibility feasibility** demonstration. It is not a real model-generated trial, does not show LLM D greater than I, does not demonstrate GNI's actual individual IFC representation compatibility, does not support general IFC4 assets, ignores complex IFC4 window move/delete and general arbitrary IFC mutation, and is not proof of an independently blind dataset. It is also not published EC³ original-author grader parity. The D compiler has bounded operation support; I is unrestricted Python — the representation-only causal estimand remains confounded.

The external evidence gates remain: first-party GNI Zenodo metadata has a CC BY 4.0 label but is not per-file and embedded product-rights certification, the original source IFC archive metadata is ~724.3 MB and NOT downloaded, no original GNI IFC source SHA/independent sealed task/GT/reviewer exists, no official BIBIMBAP paper-evaluator Git release crosswalk exists, and no paid/free provider/model trial or external IFC transfer has owner authorization. All previous 31 original IFCs remain historically exposed.

**Next practical priority:** independently author or obtain a legally cleared, source-representative IFC4 test set *under a non-agent independent steward*, audit which actual IFC4 element/placement/representation variants occur without exposing held-out tasks or GT to the developer, and extend managed XML + true IFC parity only on explicitly authorized, publicly disclosed training/developer fixtures. The genuine unseen evaluation cohort and author scorer stay separate.

## Offline reproduction

Use the existing local research Python venv and **already pinned Linux Docker image**:

    $py = 'D:\문서\D__1_Projects\202611\bim-markup-bench\.venv\Scripts\python.exe'
    & $py -m tools.audit_bibimbap_v066_synthetic_ifc4_DI --check
    & $py -m unittest -q tests.test_bibimbap_v066_synthetic_ifc4_DI

The audit reruns actual native four-source × three-arm IFC computation, four STEP renumber variants and seven bad outcomes per source; compares canonical output byte-for-byte against the committed report. Neither command uses any original author scorer, original BIBIMBAP/GNI IFC, provider/model API, network upload, rights grant or unseen reference answer. A PASS is native engineering evidence only, not a paper benchmark result.
