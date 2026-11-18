# v0.54 — BIBIMBAP author deletion scoring, IFC schema delta and primary D/I fairness

**Issue:** https://github.com/pikaybh/bim-markup-bench/issues/223
**Stacked base:** v0.53 Draft PR #222, exact commit 8ac34a03648fd3987ec171bb5dcca9e2d2b3fb09.
**Status:** OFFLINE / NO LLM LAUNCH. Original public BIBIMBAP task, independent research only, NOT BIXML/Xim product. No original IFC, author-source grader, earlier frozen report, research main or stash mutation.

## Main finding: a misleading 1.00 original-author test score can be schema-invalid

On original topological_test_17, the five intended Columns are removed in all three positive developer-only candidates. The original IFC has 158 IfcRoot instances. Before deletion, 15 IfcRelDefinesByProperties and 5 IfcRelDefinesByType roots refer **exclusively** to one of the five deleted Columns. One separate IfcRelContainedInSpatialStructure is shared with an original surviving product.

| Edit method | Original author source score | NEW IfcOpenShell schema validation errors | Stronger native admission |
| --- | ---: | ---: | --- |
| Genuine D-state final XML state diff -> real native IFC | 0.50 | 0 | PASS |
| Genuine independent I-native IfcOpenShell root.remove_product -> native IFC | 0.50 | 0 | PASS |
| Deliberately unsafe low-level ifcopenshell.file.remove(IfcColumn) | 1.00 | 25 | REJECT |

The low-level removal deletes the intended Columns but leaves 15 IfcRelDefinesByProperties.RelatedObjects sets and 5 IfcRelDefinesByType.RelatedObjects sets empty, each contrary to required cardinalities. It also leaves 5 invalid IfcProductDefinitionShape.ShapeOfProduct inverse cardinalities. It still reopens in IfcOpenShell, passes both old v0.51 source-preservation/scope oracle and the v0.48 public-source research physical task predicate, and gets both original author task Boolean metrics TRUE. Thus **original author test success is insufficient to guarantee an admissible IFC**. Do not use this invalid candidate as a scientifically valid solution merely to inflate score.

The API and D-state correctly clean related native references, removing 15 IfcPropertySet, 15 IfcRelDefinesByProperties and 5 IfcRelDefinesByType dependent roots. This causes the original author's non_target_elements_unchanged test to reject the edit and give 0.50. The 20 original author deletion subchecks individually pass for all five targets. The discrepancy is confirmed in independent author code execution, not inferred from model predictions. It DOES NOT establish that all imaginable lawful edit variants would be impossible or that the exact published-paper benchmark used an identical scorer revision.

## New independent non-increasing IFC schema validation gate

A new v0.54 validator uses the installed IfcOpenShell 0.8.4.post1 actual IFC4X3 schema validator on BOTH the original and resulting native IFC paths. It compares error categories, attributes and error-message SHA256 as a multiset; it rejects **new** IFC type/attribute/inverse cardinality errors, while preserving visibility of inherited defects. The original untouched published IFC itself has one pre-existing IfcMaterialProfileSetUsage.AssociatedTo inverse cardinality error. Both proper D/I candidates retain that one source error, introducing zero additional errors. The malformed low-level candidate has 26 errors total: original 1 + introduced 25.

The stronger admission also requires the existing independent v0.51 source/non-target preservation oracle. This is non-mutating and fail-closed. EXPRESS WHERE/UNIQUE, other semantic constraints and all possible geometry validation are NOT completely checked by this specific installed validator (express_rules=False). Therefore **zero new validator errors is not proof of perfect global IFC validity**. It is a scientifically necessary new protection against the reproduced loophole, with explicit evidence labels.

## Rights and exact provider data boundaries

Original author source is the publicly accessible GitHub repository https://github.com/nbharathik/bibimbap at pinned commit 667004e16bd38fd7d538bcee56191465429fd975. The README references a LICENSE file, but the pinned local checkout has no common license file. A separate direct GitHub Contents API read at that exact commit returned 404 for LICENSE, LICENSE.md and COPYING on 2026-11-18. The original downloader references Hugging Face dataset clemenskujat/bibimbap-data. No verified dataset redistribution/third-party provider submission rights are established from the available checkout. This does not itself prove any specific copyright restriction; it means **permission has not been verified**. No author grader test code, hidden target GUIDs, original IFC bytes or source answer scripts are committed or sent to a model API.

## D/I source information parity is not provider-token parity

The four original source initial model-facing XML snapshots match exactly in both arms, with sizes 39,611; 60,856; 172,424; 151,968 UTF-8 bytes. Each D-model edit tool schema is 1,324 UTF-8 bytes; each I-native tool schema is 1,255 UTF-8 bytes, a difference of 69 bytes. The frozen common system and question prompts match, and both arms limit tools to 25 calls. **Byte size is not provider-billed tokens.** The full XML source and changed edit output capacity may exceed available context/response budgets depending on the future model snapshot. Tool description, action authority and feedback differ.

No provider, exact model snapshot, actual billed D/I token receipt, price quote, hard USD cap, data retention/rights, prompt truncation or error budget are approved. All fields remain explicitly null/false. The previous unconditional offline launch gate refuses even an all-true approval payload. There were zero LLM-generated trials and zero billable model calls.

## Test-process exit and remaining reproducibility limitations

A previous v0.53 30-test run printed OK but hung during Windows process teardown. In this v0.54 worktree an independent rerun of exactly that historical suite **completed 30/30 with actual PowerShell process EXIT=0** in 9.17 s, so that older delay was *not reproduced*. No confident root cause is assigned and no unnecessary test runner code patch was applied. New v0.54 suites and report regeneration must be independently checked with actual process exit before claiming fully successful regression.

## Frozen new evidence

Native schema and real D/I/raw author-score developer replay:
- Audit: tools/audit_bibimbap_v054_delete_schema_policy.py
- Frozen JSON: reports/bibimbap_v054_delete_source_schema_policy_20261118.json
- SHA256: **27d2ef5c6d24a99303975d32e3c1622f2c241b519d554bb8fe2eb17f50c17442**

Offline provider tokens, rights and paid no-launch gate:
- Audit: tools/audit_bibimbap_v054_offline_token_rights.py
- Frozen JSON: reports/bibimbap_v054_offline_paired_token_and_source_rights_20261118.json
- SHA256: **4eb66777ffeb0f38cb91e0ef1d75431f0473a11c44bd2cefd8a6f22244ff99a5**

Tests: tests/test_bibimbap_v054_delete_schema_policy.py (28 test cases), tests/test_bibimbap_v054_offline_token_rights.py (14 cases). Source/original author code and source IFC are used read-only outside model/agent directories. Each report is created exclusively once (--write) and --check reproduces real native control candidates, schema validation and evaluator results before exact byte comparison; previous v0.53 reports remain SHA-pinned and unchanged.

### Offline reproduction (original Windows checkout, research Python venv)

    python -m tools.audit_bibimbap_v054_delete_schema_policy --check
    python -m tools.audit_bibimbap_v054_offline_token_rights --check
    python -m unittest -q tests.test_bibimbap_v054_delete_schema_policy tests.test_bibimbap_v054_offline_token_rights tests.test_bibimbap_v053_author_scorer_prereg

No network, Docker execution, provider key or paid model call is required by those commands. These are **developer-controlled oracle/scorer/source experiments**, not actual LLM successes, official paper scores or causal representation conclusions.
