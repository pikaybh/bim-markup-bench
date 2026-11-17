# v0.47 — Original BIBIMBAP four-task restricted matched XML versus Python native IFC edit pilot

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/209
**Frozen base:** v0.46 Draft PR #208, commit e9697c07f005517545b6b3cdb45a066528cd9c6d.
**Prior v0.46 report SHA:** beab50998c1f2f984342cf784fe910adc384752a16b8f0eed40623421c38509f.
**Prior v0.45 report SHA:** 7d7518f6c65242f7f00066beeb0229fbb6e42e44d5e841243666ac375105c4b3.

## Goal, exact population and exclusions

This is **a source-information and bounded native-edit authority parity pilot**, **not an LLM accuracy benchmark**. The original published BIBIMBAP population is unchanged at **45 tasks** (15 CREATE, 15 UPDATE, 15 DELETE), **31 distinct original byte-SHA-pinned source IFCs**. The original author/question/data repo, original IFC inputs, hidden GT and grader are unchanged. No Xim CAD program, research main, default provider tools or other versioned reports are changed.

The restricted four-task pilot uses the **exact original public questions and source IFCS** already established in v0.45:

| Actual original public task | Original published request (brief) | Allowed native source edit |
| --- | --- | --- |
| geometry_test_14 (UPDATE) | Make slab square by increasing one side | Change exactly one original IfcSlab rectangle dimension upward |
| geometry_test_15 (UPDATE) | Move one column so the four columns form a rectangle | Move one original mapped IfcColumn native world XY; preserve parent placement |
| topological_test_11 (UPDATE) | Make all columns contact named original slab | Change the shared original mapped Column extrusion height (two physical columns) |
| topological_test_17 (DELETE) | Delete columns unrelated to named original slab | Delete explicit original Column GUIDs and only exclusively owned original relationships |

The other **41 original public tasks are OUT OF PILOT**, not counted as attempted or supported for matched native edits.

## Model-facing matched source and edit interfaces

Each independent model-facing session starts with the **same original IFC4X3/native-millimetre file**, source SHA validated. Each exposes **two tools and a hard cap of 25 model calls**. No original correct answers, inferred connectivity, hidden grader or Python IFC API is injected into either source.

**XML arm: MatchedOriginalXmlSession047** wraps the *unchanged v0.45 XML session*, with an additional 25-call cap and source-SHA guard. Its first tool, read_building_xml, exposes the full unchanged original v0.45 XML, including immutable source native STEP DATA entity lines, GUIDs, original relationships, properties/materials, placement evidence and original physical world geometry. Its second tool, submit_building_xml, accepts the entire strict original-source XML and one source-bound NativeEditPlan through the v0.45 native writer and independent original physical oracle.

**Python arm: RestrictedOriginalPythonSession047** deliberately supplies **exactly the same underlying source XML bytes**, but embedded losslessly as a Python string literal assignment named ORIGINAL_SOURCE_XML; ast.literal_eval is used **by the auditor only** to prove round-trip source equality. The read_source_python tool has no additional source facts. The submit_native_python tool accepts exactly one AST-validated *source-conditional typed Python function call*, which is translated into that same original v0.45 NativeEditPlan. **The submitted Python code is never executed.** The v0.45 original native-mm trusted writer and independent original-source physical oracle then produce and gate actual IFC candidates exactly as for XML.

Permitted restricted Python function forms:

    set_slab_rectangle_dimensions(ifc_guid=..., new_x_dim_m=..., new_y_dim_m=...)
    move_column_placement(ifc_guid=..., new_world_origin_x_m=..., new_world_origin_y_m=...)
    set_all_mapped_column_depth(new_depth_m=...)
    delete_columns_by_guid(ifc_guids=[...])

Only the function corresponding to the source's actual original question is permitted. Wrong function or edit attributes, imported libraries, os calls, exec/eval, function/attribute expressions, arithmetic, dynamic GUID creation, assignments, multiple Python statements, booleans-as-numbers, NaN, Infinity, extra/dynamic **kwargs, nonoriginal GUIDs, too-large code, invalid or duplicated deletion targets and violations of native physical bounds are rejected. No arbitrary Python execution, IfcOpenShell API calls or private grader access. Invalid follow-up tool submissions do not change the last verified native candidate, original source bytes or valid state.

## Actual two-arm original IFC native physical results

Four developer-chosen **NON-SOLUTION** typed edits were submitted through both actual model tool sessions, and both tools independently wrote two new real native IFC4X3/mm candidates from the exact original source. Both candidate files passed the **independent original native IFC physical oracle** (original entity GUIDs, property/relationship endpoints, original source schema/mm, original non-target geometry and exactly the target physical edit). Each pair of actual IFC candidates was **byte-for-byte identical (same SHA-256)**:

| Original public task | XML evidence bytes | Python literal source bytes | Both native candidate IFC SHA-256 |
| --- | ---: | ---: | --- |
| geometry_test_14 | 39,731 | 40,021 | 87da342354a606128103c8a9075f20914bf75d638db9f7cdcd0c1ec9d699035b |
| geometry_test_15 | 60,727 | 61,117 | 6f4a470edaa89cb120af3c2896c0d36eca6270a654cfaddebab24c3fc385df81 |
| topological_test_11 | 172,481 | 173,373 | e6508d5383a26c2e350a12bcb2e32e6bac8acfd8435c88646155fcf0515ca9b5 |
| topological_test_17 | 151,743 | 152,635 | fc1c08fe2d2aed9a18fa1ed6de869eba3018e41db775b513da238bdfb6335ec2 |

Actual tool call totals: **12 XML / 12 restricted Python**, three per arm per task (read, submit valid native mutation, submit invalid malformed mutation). Call limit: **25/arm/task**. The deliberately wrong second submission on both arms failed with unchanged previously validated IFC and source. Both original public source SHA values stayed fixed throughout.

**None of these four edits is an original benchmark solution.** The slab is lengthened by 0.4m but is not a square; the moved column is not proven to make a rectangle; the shared Column height of 2m is not proven to touch the named slab; the deleted arbitrary source Column is not proven to be the correct unrelated set. These samples prove *ability to apply equivalent selected original native IFC edits*, not original question correctness.

The original audit retained exact question/source hashes, named source task IDs and classes, independent native candidate SHA hashes and physical oracle results, model-facing source equality and model tool call counts. Frozen report:

**reports/bibimbap_v047_original4_restricted_XML_Python_native_matched_20261117.json**
**SHA-256: cf1d37bf84fe744921989affc8b524e296c4d3b38731601513fd1b9fa95a44aa**

The machine report is created only once with exclusive file creation and reproducible byte-identically. Previous v0.45/46 reports are preserved.

## Scientific non-equivalence, original scoring and next priority

- **Not original full Python/IfcOpenShell parity:** the Python side here understands ONLY the four task-bound typed AST calls. It cannot import or execute arbitrary Python code or invoke normal IfcOpenShell helpers. It is NOT the original benchmark's unrestricted imperative Python arm. This is a **restricted tool-surface pilot**.
- **Same facts do not mean same token cost:** Python views embed XML as a Python string literal and have slightly larger byte counts. Different tool names/descriptions/output formatting can change ergonomics. No tokenizer-specific prompt budget, provider response or latency equivalence has been measured.
- **Native write parity is limited to four selected original tasks**, not all 45. No v0.47 expansion of general IFC edit operations. Earlier other 27 original IFCs remain v0.46 read-only under a separate experimental flag.
- **No original benchmark model correctness:** zero original author grader/hidden GT/paid provider/LLM paired trials/Docker invocations, zero original task semantic success claims. Historical five CREATE D0/I0 developer control pairs remain five.
- **Do not claim causal XML markup superiority from this result.** Only identical original input evidence and identical trusted native output capabilities are established for these four selected restricted actions.

**Next v0.48:** preregister and independently implement task-semantic eligibility tests for the four original published questions (slab actually square, four Columns rectangular, mapped Columns physically contacting specified original slab, deletion set exactly unrelated to specified slab) **without exposing original ground truth to model tools**; then fix model/provider/token budgets, formalize the restricted-typed pilot versus unrestricted original Python/IfcOpenShell tool-bundle comparison, and only afterwards collect legitimate real original benchmark scores.

## Reproduction on the connected Windows host

Use the isolated v0.47 worktree from the exact v0.46 parent commit. No Docker, paid provider or external original grader required:

    $base = 'D:\문서\D__1_Projects\202611'
    $py = Join-Path $base 'bim-markup-bench\.venv\Scripts\python.exe'
    & $py -m tools.audit_bibimbap_v047_original4_matched_restricted --author (Join-Path $base 'bibimbap-author-upstream') --data (Join-Path $base 'bibimbap-author-data') --progress
    & $py -m unittest -q tests.test_bibimbap_v047_original4_restricted_matched

No main merge, author/data mutation, original grader, hidden answer, previous frozen reports, prior experimental worktrees or BIXML/Xim product changes.
