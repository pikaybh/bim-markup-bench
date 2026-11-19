# BIBIMBAP v0.27 — Original `test_19` connected Wall: isolated native deletion and actual D0/I0 full IFC byte parity

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/168
**Frozen parent:** v0.26 Draft PR #167, Git SHA `8e3564ca19606d82b0880a279e0fd4c5dbed137d`. This is a **research-only checkpoint** in the independent `pikaybh/bim-markup-bench` repository. Do not modify Xim/BIXML product, production `main`, the original BIBIMBAP author scorer, original public dataset, hidden ground truth, or any prior frozen report.

## 1. Reason for this checkpoint

The original PUBLIC BIBIMBAP `test_19` asks to delete a connected `IfcWall` from the pinned IFC4X3 millimetre source `basic_tasks.ifc`, with original source Wall, **two native `IfcRelConnectsPathElements` to neighbors**, three individually owned property sets, and multi-member shared type/material/classification/storey memberships.

In v0.26, a complete ordinary XML state edit removing one existing `<Wall>` and its two existing `<Connects>` declarations was verified as a valid exact source graph delta. But the Windows IfcOpenShell native `root.remove_product` and several deep geometry/placement deletion strategies caused native process crashes. A less aggressive low-level deletion returned an IFC that could score 0.5 with the original author, but still contained two unowned Wall shape representations and one orphan each of ProductDefinitionShape and LocalPlacement. **v0.26 correctly failed closed** and kept the total at 8/45 verified developer native D0/I0 byte-equal cases. No v0.26 evidence was rewritten or relabeled.

## 2. New implementation: exact ordinary XML, trusted child native writer

v0.27 implements a **source-SHA-pinned, opt-in** trusted native backend for exactly this original connected Wall shape. The authoring model, if ever tested, receives only the normal complete declarative XML state, with three state elements removed: the one original source `<Wall>` and the two directly referencing `<Connects>` relations. There is no imperative `<Delete>` command, no native API, no geometry-tool call, no model-produced Python or command bus.

- `src/runtime/compiler.py` uses the **trusted host-side experiment flag `BMB_V027_ORIGINAL_CONNECTED_WALL_NATIVE=1`**, the exact frozen normalized source hash `16568e7c4b8b9d62567a7a199101269daa6e5b1b7535cec095b8e233ae2ef6ac`, and exactly one original Wall deletion with three removed typed graph edges to route to this backend. **Flag off is the default** and preserves v0.26's correctly unsupported and fail-closed behavior. This prevents historical v0.26 tests from being silently rewritten as successful. The flag is trusted runner configuration, not an editable XML attribute exposed to an LLM.
- `src/runtime/connected_wall_delete.py` independently preflights original source GUID/type, exact two directed neighbor-Wall links, exclusive three native Psets, four approved shared native memberships, storey, two original physical shape representations, uniquely shared presentation layer, no hosted openings, and no external product geometry or placement dependencies. Extra inverse relationships, shared property ownership, non-original source hashes, altered IFC schema, missing connections or non-target XML changes fail closed.
- `tools/bibimbap_v027_wall_worker.py` is a **child-process-only native implementation detail**, called with `subprocess.run` and `shell=False`, a limited allowlisted environment, public original Wall GUID from supervisor stdin, fixed source/output paths, and a **25 s timeout**. A native C++ access violation (`0xC0000005`), abnormal exit, invalid receipt or timeout **does not terminate or commit the parent compiler output**. This is process isolation, not a fully hardened model-code sandbox. The child is trusted developer code; untrusted user/model-generated Python is never executed.
- The child removes the two native path relationships, removes only the three exclusively owned property sets via the trusted IfcOpenShell Pset API, unassigns just the two target shape representations from the shared presentation layer, deletes the target native Wall identity, and then uses an incremental zero-inverse **reference-count sweep** over the original Wall's geometric/placement forward subgraphs. It does **not** use the previously crashing `remove_deep2` sequence or unrestricted `root.remove_product`; any still-referenced shared model/context/style assets remain unchanged.
- The trusted host independently reopens the child-staged IFC and validates **every original native `IfcRoot` GUID/class**, exactly **9 approved Root deletions** (Wall1, path links2, owned Psets3, exclusive Pset relations3), exactly **four approved shared Root membership changes** (type/material/classification/storey), and exactly **one presentation-layer membership edit** removing only the target Wall's two shape representations. **No added STEP entities; every surviving original STEP entity must be byte-equivalent as a serialized entity record except those five bounded changes.** Every removed nonroot STEP entity must derive from the original Wall's owned shape/placement/property-set subgraph.
- The target's own two shape representations, original ProductDefinitionShape, and LocalPlacement must all be **absent** in the output; baseline zero-inverse native geometry/placement counts must not increase. All original other 42 `IfcProduct` GUID/classes survive. Reprojection of the *entire resulting IFC* to the declared XML typed semantic graph must match the *entire* submitted complete XML graph.
- `stage_and_commit` alone publishes the IFC after the supervisor, independent native verifier and whole XML projection all pass, using a private temporary staged file and exclusive publish. Original public IFC source hashes are rechecked. A failure leaves the prior valid XML unchanged and publishes **no native IFC**.

The narrow source and flag pin remain explicit: **this is not general IfcWall deletion or IFC2X3/IFC4 support**.

## 3. Actual original-public matched experiment — complete native IFC bytes

`tools/audit_bibimbap_v027_original_wall.py` runs the exact original public IFC/source question without reading hidden ground truth or scorer expectations. D0 deletes the three existing elements in one complete XML source submission through the trusted compiler. The independent developer-only I0 `tools/bibimbap_v027_independent_wall_i0.py` separately implements native IfcOpenShell cleanup from the original PUBLIC Wall GUID in an independent Python child process and restores original millimetres. I0 imports neither the trusted XML compiler nor the D0 worker, does not use original author scorer logic, and is **not LLM-authored**.

| Actually executed original PUBLIC `test_19` | D0 XML source→trusted compiled IFC | I0 developer native Python/IfcOpenShell |
|---|---:|---:|
| Original IFC4X3 millimetre source | exact pinned original | same |
| One original connected Wall removed, its two original connections cleaned | **PASS** | **PASS** |
| Other 42 original `IfcProduct` GUIDs/classes preserved | **PASS** | **PASS** |
| Target's two original representations, shape object and placement cleaned | **PASS** | **PASS**, full IFC byte identical |
| Full resulting native IFC SHA-256 | **`5a3bf2626f32219cc770b5b8d68277f6e959aa7822a5ad92974931eb47b9941d`** | **same exact complete file bytes** |
| Original author `object_not_exists` | 1.0 | 1.0 |
| Original author `integrity_constraint` | 0.0 | 0.0 |
| Unchanged original author score | **0.5** | **0.5** |
| Actual LLM inference/provider spend | **0 / $0** | **0 / $0** |

Important: the original author scorer's score **remains 0.5**, not 1.0. A full file byte-identical developer D0/I0 result establishes only equivalent native outputs for this public task, not author-score perfection or LLM representation performance. Previous original author scorer source/data mismatch cases remain disclosed and unchanged.

The first audited real original `test_19` result is frozen at `reports/bibimbap_v027_original_test19_connected_wall_D0_I0_native_parity_20261116.json`, SHA-256 `9cee40c6cd75f5f5fc3c35f1d8ee5b0580681e38820da6178f39c413c71d63b4`. Replaying the **entire original native D0/I0 experiment and independent scorer** reproduces that complete JSON byte-for-byte, without embedding public raw GUIDs/question, hidden scorer target lists, raw IFC, credentials, original private answers or GT in Git.

## 4. Validation and negative controls

New source-pinned `tests/test_bibimbap_v027_original_connected_wall.py`: **32/32 PASS**, 56.116 s unittest / 64.610 s enclosing process, exit 0. This actually executes the original source, both native implementations, unchanged author scoring, frozen source/report checksums, native Root/STEP integrity and original shape/placement absence. Negative tests independently reject invalid GUID/type, source-SHA mismatch, extra original path relation, shared Pset, surprise Space boundary, forged neighbor native Root, presentation-layer tampering, storey relation tampering, unexpected new STEP, unsupported non-IFC4X3 inputs, invalid XML with dangling connections or unrelated Walls, child crash code `0xC0000005`, child timeout, invalid subprocess output and preexisting stage. The second full original-public auditor run reproduces the frozen JSON/hash. Off-by-default feature flag preserves older fail-closed v0.26 behavior.

**Observed v0.27 selected cross-version integration:** An actual **17-module non-Docker regression executed 316/316 tests PASS** (258.457 s unittest / 272.86 s enclosing process, exit code 0), spanning earlier v0.3/v0.4/v0.14–v0.27 original-public IFC editing and unchanged older v0.26 native fail-closed tests. New v0.27 tests separately **32/32 PASS** (56.116 s unittest / 64.610 s enclosing process). The additional immutable QA report is `reports/bibimbap_v027_selected_316_non_docker_regression_and_original19_native_QA_20261116.json`, SHA-256 `5cc9a36b6c2aad2b30d8240173f1eb0d35e470676383eae33c708fb6c6212c4c`. Independent read-only Docker Desktop Linux Engine `info`, pinned-image inspect, and orphan-container listing returned **HTTP 500 Internal Server Error** again in v0.27; therefore the prior v0.19 sealed-Docker module is excluded, and image presence/worker orphan state are **unverified, not zero or deleted**. No daemon restart/reset/rebuild/pull was attempted. **Do not claim historical whole-repository 832-case discovery or Docker-included regressions PASS.**

## 5. Honest cumulative original research accounting

| Measure | v0.26 frozen | v0.27 verified |
|---|---:|---:|
| Original PUBLIC intention-to-test tasks | 45 | 45 |
| Developer-only D0/I0 **full native output byte-identical** original task pairs | 8/45 | **9/45** |
| Both original-author-scoreable developer pairs | 6/45 | **7/45** |
| Other original tasks not tested under this exact paired protocol | 37 | **36** |
| Actual new model-generated paired XML-vs-Python attempts | 0 | **0** |
| Provider cost | $0 | **$0** |

The earlier two original author Window reference mismatch cases and the v0.22 nine coarse source-role gaps/three schema-admission exclusions remain factually recorded. Proving one public task's *write correctness* does **not** prove original45 full source information completeness, equal XML-vs-Python affordance, exposure/tool-call budget parity, or a causal model benchmark.

## 6. Reproduction on the authorized Windows research machine

```powershell
$base = 'D:\문서\D__1_Projects\202611'
$repo = Join-Path $base 'bim-markup-bench-issue168-original-wall-worker'
$py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
Set-Location $repo
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& $py -m unittest tests.test_bibimbap_v027_original_connected_wall -v

# The audited tool internally sets the trusted v0.27 feature flag ONLY
# for its D0 submit, then restores the environment. The target GUID is
# obtained from the original PUBLIC instruction; no hidden reference read.
# Always use a fresh ignored result destination. No prior report overwrite.
& $py -m tools.audit_bibimbap_v027_original_wall `
  --root . `
  --author (Join-Path $base 'bibimbap-author-upstream') `
  --data (Join-Path $base 'bibimbap-author-data') `
  --output 'results/UNIQUE_v027_actual_original_test19.json'
```

This remains an experimental and strictly bounded native capability. Next research priority is broadening **task-relevant native writable semantic coverage** and preregistering an explicitly budgeted fair D-vs-I **LLM model** trial only after source/feedback/tool-access parity has been independently established; no paid calls were made in v0.27.
