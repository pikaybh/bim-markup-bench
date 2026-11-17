# BIBIMBAP v0.38 — original legacy IFC2X3 / IFC4 XML host, explicit opt-in P0 gate

**GitHub Issue:** https://github.com/pikaybh/bim-markup-bench/issues/191
**Stack base:** v0.37 issue #189 / Draft PR #190, parent SHA `030b45716d48d9f4fbc093709b0d0c973e1b13b3`
**Status:** research-only isolated **prospective model-facing XML tool-session capability** for exactly three original public CREATE IFCs. Not a real matched LLM experiment or task-specific author evaluation.

## Original frozen cohort and limits

The real published BIBIMBAP public cohort remains **45 / CREATE 15 / 10 CREATE without new task-specific developer D0/I0 pairs**. The five earlier task-specific semantic controls remain unchanged. v0.37 directly observed **three P0 schema admission rejects** in the normal `XmlSourceEditSession`; it froze the evidence that `geometry_test_03` and `geometry_test_04` are original **IFC2X3**, and `geometry_test_05` is actual **IFC4** (not IFC4X3).

This iteration does **not** change the default `XmlSourceEditSession` behavior: the default remains **IFC4X3-only** and still rejects those three originals. It introduces a deliberately named Python host constructor option, `experimental_original_legacy_v08=True`. When explicitly set, this authoring session admits **only the exact byte-hashed three publicly pinned original inputs**. The future paid matched25 CLI is **unchanged and does not automatically activate this option**, so the opt-in proof is confined to an actual instantiated model-facing session and its two existing tools; it is not proof an approved model trial is launch-ready.

The existing trusted experimental v0.8 **native-schema-preserving** projection, XSD and compiler are reused unchanged. No new LLM-visible API, direct IFC editing function or command wrapper is introduced. The model-facing user still reads a full declarative `Building` document and sends a full replacement version via `read_building_xml` and `submit_building_xml`; the trusted external compiler handles identity-based state differences. This partial source view does not purport to show all native IFC geometry or metadata. Original IFC documents, original question text, source model Git SHAs, author evaluator and hidden GT are untouched.

## Actual model-facing tool-call evidence

Each of the following is a **developer-authored illustrative XML mutation**, intentionally *not* an evaluated task answer. All occurred in fresh isolated temporary sessions on the original public IFC. The original IFC was cloned, converted **millimetres → metres** without changing the native IFC schema, compiled in source-native IFC2X3 or IFC4, converted **metres → original millimetres**, and reopened for independent read-only source-versus-output verification.

| Original public task | Original native schema | Actual XML tool read/submit and restored native result |
| --- | --- | --- |
| `geometry_test_03` | IFC2X3 | Added `Opening` + `Door` to original source wall from public v0.8 fixture; output native **IfcOpeningElement + IfcDoor**, real Boolean Wall void and source-host void/fill relationships |
| `geometry_test_04` | IFC2X3 | Added representative **2 × 2 × 2 m IfcSpace** to existing original storey; output native IfcSpace + correct original storey aggregation |
| `geometry_test_05` | IFC4 | Added a representative **3 m** new IfcWall (not the original question's 5 m); output native IFC4 Wall and native original storey containment |

**3/3 explicit opt-in source admissions and 3/3 real original-native-mm IFC writes** succeeded. **0/3 default sessions** admit. Original native schema, original source millimetre units, all original IFC Root GUID/class/Name/Description and all source products are preserved. The independent restored-native oracle checks original containment and aggregation memberships (any additions restricted to the new products), old void/fill relationships, the new Door void+fill, real Wall physical void, all other original products' world vertices, native face planes and planar areas, as well as physical meshes of new products. It intentionally does **not** assert byte-for-byte equality of full STEP entities or universal IFC fidelity. Source input files are checked unchanged before and after.

Original source each case is byte-pinned:
- `geometry_test_03`: `88f315a0ec26c1e8bd5ea84fb254cf1d30b0ef143f03bbeffcee1dd8a69a2a59`.
- `geometry_test_04`: `d2d6a5e39dc144ef49a44baca8d4039c267cc3bb8b7bfc5eb473c1207b7a62ea`.
- `geometry_test_05`: `f637eceda5155c846f2c3f24e215ef2161151ccbff1ba2f9e098c71463322bcc`.

## Independent verification forensic correction

The first native-mm validator correctly refused one converted IFC2X3 IfcSpace output when its source triangle hashes appeared to change. We investigated this **before freezing the report**, using the actual original/source-output pairs. The problem was with the experimental independent comparison: IfcOpenShell's world shape iterator already returns SI-metres even for native-mm IFC, while the initial validator scaled its vertices by another 0.001; canonical serialized floating-point values also distinguished signed `-0.0` from `0.0`. The independent oracle now works on physical SI world coordinates and normalizes signed zero. It checks world point multiplicity, plane identity and per-plane area rather than declaring any changed diagonal an IFC failure. **A changed vertex, physical face, original IFC Root metadata or missing new geometry still triggers an explicit rejection.** The fixed validator independently confirms unchanged original physical surfaces after legacy native unit roundtrip; the historical source and original author grader were never changed or relaxed.

## Safety and negative cases

The actual host constructor refuses any non-allowlisted IFC, source SHA mismatch even if schema stays the same, altered source units, IFC4X3 with the legacy opt-in, duplicate session paths and schema masquerading. The frozen v0.8 parser rejects non-XML commands, DOCTYPE/XXE, original model hash spoofing, fabricated missing IFC4 Storey Elevation, unauthorized old native objects and unexpected multi-create diffs. Host `submit_building_xml` keeps its last valid source and previously committed candidate if an edit fails; never overwrites original IFC. Independent original native-mm verifier rejects altered original GUID/name, moved original Wall geometry, output schema mismatch and a newly created product whose representation has been removed.

This is **not** evidence that all source-relevant facts are visible to an LLM or that equal-facts/equal-write-effect conditions between XML and an isolated IfcOpenShell imperative arm have been met. The opt-in source only prepares a possible future experiment gate after separate isolation, equal-access, and paired task-specific capability checks.

## Reproduction, frozen report, and tests

- Host switch implementation: `tools/bibimbap_matched25_tools.py`, now accepts **keyword-only** `experimental_original_legacy_v08=True`; without it default IFC4X3 behavior is unchanged.
- Source pin and independent restored native oracle: `tools/bibimbap_v038_legacy_live_gate.py`.
- Actual host replay auditor: `tools/audit_bibimbap_v038_original_legacy_host.py`.
- Positive, negative, frozen integrity and actual host replay tests: `tests/test_bibimbap_v038_original_legacy_live_host.py`.
- Frozen machine JSON: `reports/bibimbap_v038_original_p0_legacy_xml_live_optin_20261117.json`, SHA256 **`c04448087528aa07b9cee64830defe61e5b3a7836fc4cae8f073dac4bfc7aad4`**.
- Unchanged original legacy v0.8 compiler baseline: **23/23 passing**.
- **v0.38 focused actual host plus negative and frozen replay tests:** **36/36 PASS** in 8.265s, process exit code 0, ignored log `results/v038_focused_final_20261117.log`.
- **Selected 22-module non-Docker multi-version regression:** **469 total, 465 PASS / 4 SKIP / 0 FAIL**, 213.223s, process exit code 0; log `results/v038_selected_nondocker_regression_20261117.log`. It includes prior v0.8 compiler and prior v0.20–v0.36 compatible modules, but excludes the v0.37 module whose frozen host-file SHA and replay are by construction specific to the earlier version. It is not an entire repository suite, an OS-isolated Python arm, or a Docker-backed LLM experiment.

At the separate Windows PC research Worktree:

```powershell
$base='D:\문서\D__1_Projects\202611'
$py=Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
& $py -m tools.audit_bibimbap_v038_original_legacy_host --author (Join-Path $base 'bibimbap-author-upstream') --data (Join-Path $base 'bibimbap-author-data')
& $py -m unittest -q tests.test_bibimbap_v038_original_legacy_live_host
```

`--write NEW_UNUSED_REPORT_PATH` uses exclusive create, never overwriting the immutable reference report. Old frozen v0.37 source auditor/test results were produced against the old host SHA; running the old v0.37 host-frozen identity assertions against the newly modified host **is not a valid regression metric**. Run historical v0.37 tests in their preserved baseline worktree; keep the v0.38 multi-version suite scope explicit. No Xim product code, research main, original Git stash, original data, hidden GT, author scorer, Docker or provider budget changes in this scope.

**Causal validity result: 0 original 45 tasks with proven complete equal model-visible information; 0 with proven equal complete native writes; 0 actual matched XML/Python LLM trials; 0 new paid provider requests; 0 original-author task scores in v0.38.** Exactly three previously hard-blocked source schemas now have **developer-verified, explicitly opted-in native tool creation**, not a published performance improvement.

**Next priority after v0.38:** P1 complex original IFC geometry projection rejects (`geometry_test_01`, `topological_test_05`), then P2 room/Space and original public GUID semantic ambiguity, then P3 current matched host generic Column/Slab support. Maintain all original 45 in ITT and refuse any easy-case-only parity claims.
