# v0.46 — Original 27 IFC native-source model-read parity index (paged, read only)

**Research Issue:** [#207](https://github.com/pikaybh/bim-markup-bench/issues/207)
**Stacked base:** v0.45 [Draft PR #206](https://github.com/pikaybh/bim-markup-bench/pull/206), exact original frozen commit `f385ad2ecb9a62a3663d408bc9a998cf5e016f25`.
**Frozen prior source audit:** v0.43 SHA-256 `eb05633d152b1ff15e4fdd888bb62924b31b126f6cddd05fb23e54fce3ef8dbf`.
**Frozen prior native edit audit:** v0.45 SHA-256 `7d7518f6c65242f7f00066beeb0229fbb6e42e44d5e841243666ac375105c4b3`.
**Original author source Git SHA:** `667004e16bd38fd7d538bcee56191465429fd975`; original published question/data source Git SHA `f2a7dfa1ca0858a1751f1bbcd1d9f64db696d5ca`. Original question CSV SHA-256 `21c07f08c923cdb748255d7960535bab05e2887e4d093d64f87f76ff6d6d100b`. Author and dataset clean, unmodified.

## Why a PAGED native source catalog?

The original public BIBIMBAP population remains **45 published original tasks**, 15 CREATE / 15 UPDATE / 15 DELETE, with **31 unique original native IFC source SHA-256 files** across IFC2X3/IFC4/IFC4X3 in original millimetres.

Prior v0.43 independently measured substantive source-info differences in **27** unique source IFC files that existing XML projections could read: the original XML did not expose **1,743/1,757 native `IfcRelationship` GUIDs**, **121/433 `IfcProduct` GUIDs**, and **all original material and PropertySet name strings**. The other exact four source hashes were addressed as read-only v0.44 and bounded typed native mutations v0.45. The 27 remaining source files underpin **41 of the 45 original task rows** because the same basic source IFC is reused by 15 different original published questions. We **do not** multiply shared IFC entries by task count when reporting source metadata totals.

The largest original `geometry_test_16` file is **389,958 bytes** and has **8,304 actual native original STEP DATA entity lines**, some up to 5.2 KB. Therefore copying the entire native IFC into a single XML response violates the original benchmark harness's ~300 KB input-size cap. Silently omitting the source entities would defeat parity auditing. This checkpoint instead allows an LLM to **request successive bounded pages** of exact original native source facts when needed. This is an explicit *tool-interface change*, not the default old benchmark arm or equal instant context/token consumption.

## Read-only source mode (three actual model-facing tools)

```python
session = XmlSourceEditSession(
    immutable_original_public_IFC,
    isolated_trial_folder,
    experimental_original_native_catalog_v046=True,
)

manifest = session.call("read_building_xml", {})
roots_page = session.call("read_native_ifc_page", {"catalog": "roots", "page": 0})
step_page = session.call("read_native_ifc_page", {"catalog": "step", "page": 0})
attempt = session.call("submit_building_xml", {"xml_text": manifest["xml"]})
# attempt.status == "error"; original source and native IFC files unchanged
```

The new mode is **explicitly opt-in**, is recognized **only for the 27 exact immutable original source SHA-256s** from the previously frozen v0.43 audit, and is mutually exclusive with prior v0.38–v0.45 flags. The original provider `run_one_pair` still invokes the default XML session without it. This mode does not create a normalized/metre IFC file; every native source lookup reads the original IFC4X3/IFC4/IFC2X3 bytes and checks the source SHA at page request time. It does not invoke an original author grader, hidden benchmark ground truth, Python code supplied by a model, Docker or paid provider.

The unchanged familiar model tool `read_building_xml` returns **a manifest**, with the source IFC SHA, original schema/mm units, exact eight catalog entry counts, page counts and canonical per-catalog SHA-256. The additional `read_native_ifc_page` returns XML with at most **16 exact source records per page**, by original catalog and zero-based page index:

1. `roots` — every original `IfcRoot` GUID, native class, name/description and original source STEP ID.
2. `products` — every original `IfcProduct` GUID/class and original object type, predefined type, source placement STEP ID and representation STEP ID.
3. `relationships` — every original `IfcRelationship` GUID/class/name and every direct reference endpoint with native IFC attribute/role, STEP ID and source GUID (where the endpoint is an `IfcRoot`). No fabricated topology, boundary, intersection or containment.
4. `property_sets` — every original `IfcPropertySet` GUID/name/description and its exact original contained property STEP IDs, original property names, IFC nominal-value class and nominal value text. General property types without `NominalValue` explicitly carry no fabricated nominal value.
5. `materials` — every original `IfcMaterial` name, source STEP ID, original Description/Category where that schema defines them. IFC2X3 `IfcMaterial.Description` is **absent**, not an empty invented native field; the published XML optional textual display is safe and the full original STEP source is separately available.
6. `placements` — every native `IfcLocalPlacement` source ID, parent/relative placement IDs and all 16 entries of its actual original physical local-to-world matrix (native millimetres).
7. `geometry` — every original source `IfcProduct` with explicit one of (a) original-world physical mesh 1µm vertex/face count, bbox and ordered triangle/vertex digest, (b) actual IFC representation geometry computation error class, or (c) no source IFC geometric representation. These are source-derived geometric **summaries**, not a full geometrical authoring/edit surface.
8. `step` — **every original literal native IFC DATA entity text line in the original byte order**, per-entity original source STEP ID, IFC class, and independent line SHA-256. The index pages are source quotations, not generated normalized IFC statements, and do not execute their contents.

Each 16-record page is bounded by **300,000 bytes**; the largest actual observed page is **24,717 bytes**, even for the oversized original IFCs. A source with zero original entries in a catalog has zero pages and rejects page 0. Invalid catalog, negative/non-int/Boolean/oversized page, unknown source, extra arguments, source hash changed after initialization, and all native mutation submissions fail closed. The `submit_building_xml` tool is explicit that **editing is unsupported** in this separate read-only mode, and does not create a candidate IFC or attempt directory.

## Actual full 27-source independent audit (not model evaluation)

The **actual model-facing** `read_building_xml` and `read_native_ifc_page` tools were invoked across **ALL 27 unique source IFCs**, for each original eight catalog records and for every valid page. A **separately implemented independent oracle** (`tools/bibimbap_v046_independent_native_catalog_oracle.py`, no v0.46 projector/author evaluator import) opened the original published IFC file itself, independently enumerated every GUID/class/name/direct relationship reference/property/material/placement and independently recomputed geometric source-world triangle digests/bboxes and literal original source STEP lines. All returned XML attributes, element types, page indices, record order, per-catalog canonical digests, property values, endpoint roles and exact original STEP text were compared 1:1. All 27 source SHA-256s and original 45 question SHA-256s were frozen/pinned.

| Measure | Verified result over **27 unique original IFCs**, not 41 task duplicates |
| --- | ---: |
| Original IFC files independently opened and fully verified | **27/27** |
| Model-tool page calls actually issued and verified | **2,037/2,037** |
| All original literal STEP DATA entities available in correct order/text via paging | **23,120** |
| Native source `IfcRoot` GUIDs | **3,514** |
| Native source `IfcProduct` GUIDs | **433** |
| Native source `IfcRelationship` GUIDs and direct endpoint references | **1,757** |
| Native source `IfcPropertySet` names and contained property value records | **1,170** |
| Native source `IfcMaterial` names | **64** |
| Native source `IfcLocalPlacement` matrices | **433** |
| Native source actual computed physical-world product meshes (bbox+digest+counts) | **325** |
| Native products with no original IFC Representation | **108** |
| Native sources with represented but unavailable geometry | **0** |
| Maximum actual one-page model-tool XML bytes | **24,717** |
| Actual model-facing mutated/source candidate IFCs | **0** |
| Real model-paired XML/Python trials / original benchmark scorer | **0 / 0** |

The 31 original source IFCs are not all in v0.46: four source hashes belong to v0.45's separate edit mode. As a **collection of separately enabled research modes**, all 45 tasks now have source-read access, but this is **not one uniform arm** and it is **not yet a fair matched XML-vs-Python comparison**.

## Integrity, immutable manifest and limitations

**Frozen report:** `reports/bibimbap_v046_original27_all_native_IFC_paged_source_catalog_20261117.json`
**SHA-256:** `beab50998c1f2f984342cf784fe910adc384752a16b8f0eed40623421c38509f`

The reporter stores the actual all-source model-page/verifier summaries by unique source SHA and the exact 45 original task/question/source provenance records, **not 2,037 copies of the underlying source IFC data**. It is written once with exclusive `xb` creation and independently byte-exact reproducible. Prior original full45 v0.43 and v0.45 reports remain frozen.

- **No source-data substitution:** original author/project/data Git, all 45 questions and 31 source IFC SHA-256, original grader/hidden GT untouched. No research main merge or Xim/BIXML product repo change. Existing stash and other stacked worktrees preserved.
- **Accessible on demand ≠ equally consumed:** all original STEP DATA and native metadata are *available through up to hundreds of optional model page requests*. The model receives only a ~1.7KB manifest at the first read; it does not automatically consume 23,120 STEP lines. A Python arm may use direct IfcOpenShell queries with different runtime, token, interaction, and cost semantics.
- **Readable metadata ≠ editable authority:** v0.46 is intentionally **read-only** for 27 sources. It does not match unrestricted original IFC Python edits and does not elevate the four v0.45 mutators. There is no task-conditioned native write parity across the original 45.
- **Complete native DATA text is not equivalent to complete IFC API execution:** exact original literal STEP DATA can be retrieved, but the IFC HEADER and arbitrary IfcOpenShell derived helpers are not an executable function of this XML tool. Physical geometry is returned as bbox/triangle digest, not full mesh in the summary; the exact original source STEP entities may describe the underlying geometry if the model requests them.
- **No original task-success claim:** zero original author/evaluator invocations, zero hidden scores, zero paid LLM/Docker paired trials, and zero newly created correct original CREATE developer D0/I0 pairs. Historical original CREATE developer control pairs remain **5/15**.

### Reproduction commands

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'

& $py -m tools.audit_bibimbap_v046_original27_native_catalog `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') --progress

& $py -m unittest -q tests.test_bibimbap_v046_original27_native_catalog
```

### Next v0.47

Define a prospective **task-conditioned equal-information and equal-native-mutation-authority subset** using the 27 original native catalog source indexing and four true v0.45 native writer gates. Either build a matched **restricted Python tool** that queries the same source index/pages and modifies the same original source states, or explicitly label a Python-unrestricted vs XML-restricted experiment as a **tool-bundle comparison** rather than causal XML markup advantage. Require frozen original task native oracle eligibility, provider/model/token/cost equalization and no hidden benchmark evaluator leakage before score claims. Do not alter any original public task or invent ground truth.
