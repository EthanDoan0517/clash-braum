# Braum → Clash working pipeline

The authoritative progress record is [the master plan](../audit/BRAUM_CLASH_MASTER_IMPLEMENTATION_PLAN.md). These scripts implement the offline source, export and draft-rig stages. They do not build the finished cosmetic replacement.

## Outputs to inspect

| File | Purpose |
|---|---|
| `scenes/braum_native_baseline.blend` | Original mesh and all 97 native joints, corrected imported winding and preserved normals. |
| `scenes/clash_source_materials.blend` | Eleven OBJ groups and reconstructed source material assignments. |
| `scenes/shield_prepared.blend` | Original shield geometry with baked transforms and rebuilt finite UVs. |
| `scenes/clash_braum_fit_draft.blend` | Draft body fit, seed weights with selected corrections, rigid shield and retained hidden Poro. |
| `scenes/clash_braum_animation_review.blend` | Same draft with all 59 native animations as retained Blender actions. Select `Braum_Native` and an action in the Action Editor. |
| `scenes/clash_braum_rig_refined.blend` | **Current continuation scene.** Authored hand fit/digit weights, rigid equipment and fasteners, smoothed cloth/neck weights; all 59 original actions retained. Stage 3 remains open for final contact/deformation review. |
| `../build/model_draft/braum_clash.skn` / `.skl` | Valid development pair. Not a standalone installable skin. |
| `../build/model_rig_refined/braum_clash.skn` / `.skl` | Current refinement export, independently checked against native joints and Poro. Temporary materials and unreduced geometry remain. |
| `../validation/previews/draft/` | Eight representative motion renders. |
| `../validation/previews/refined/` | Current whole-body and hand close-ups, directional E, worst-frame diagnostics. Use the render manifest to distinguish the current scene's renders. |

The source groups, facial details and body material maps were reconstructed from actual OBJ/tbscene records. Principled response and the missing eye DDS→TGA substitution remain preview approximations. The draft is above the triangle target, lacks final atlas/material integration, and needs further hand/joint/equipment refinement. It is not ready for release.

## Reproduce

Run from the project root in PowerShell. These are generated outputs: **copy any manually edited scene to a new filename before rerunning its generator**. The original source archives, source shield and `Braum.wad/` inputs are never changed. Do not rerun the old Phase 0 inventory scripts after adding build files; their broad inventory scan would replace the immutable baseline.

```powershell
$taskPython = 'C:/Users/etqdo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$taskBlender = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'

& $taskPython work/scripts/bootstrap.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/roundtrip.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/test_export_contract.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/prepare_sources.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/render_preparation.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_aperture.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/fit_draft.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/review_draft.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/export_draft.py
& $taskPython work/scripts/manager_checks.py
```

Stop if a command exits nonzero. The installed Blender sometimes reports blocked profile-cache/thumbnail writes in this sandbox; those do not affect the saved scene or numerical validation. Real script failures exit with code 1 because `--python-exit-code 1` is supplied.

### Continue stage 3 from the saved checkpoint

Do not run the preceding source/import pipeline just to resume. The refinement generator reads `clash_braum_animation_review.blend` and writes **only** `clash_braum_rig_refined.blend`. Preserve a separately named copy before making hand edits in Blender. Its physical component IDs refer to that original review scene, so inspect/regenerate the mapping if topology changes; do not run this generator over a reduced mesh.

```powershell
# rig_regions.json is already present; regenerate only if its input scene changed.
# & $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_rig_regions.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/refine_rig.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_rig_refinement.py -- --reuse-before
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/export_draft.py -- --scene clash_braum_rig_refined.blend --output model_rig_refined
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/render_rig_refinement.py
```

The validation script samples **every integer frame** of all 59 native actions (3,963 frames per revision), tests authored digit assignments and equipment transforms, checks finite geometry/normalized weights, and verifies native rest bones and imported action channels. `--reuse-before` reuses only the prior pose measurements for the byte-identical original review scene and ANMs; it still compares action channels between scenes. Omit the flag for a fully fresh baseline comparison. Edge stretch is a diagnostic, not a universal pass threshold.

`render_rig_refinement.py -- --case braum_recall:65:body` renders one named frame; repeat `--case` to select more. `--vanilla --label vanilla_extremes` renders the original reference under the same actions. Rendering never saves over the working scene. The manifest records scene SHA-256 and the exact rendered cases; an ad hoc render replaces that manifest with only its cases. Run the full default render for a complete current set.

`inspect_cloth_defects.py` locates specific remaining elongated edges without editing; `inspect_animation_extremes.py` records saved-pose values and source ANM keys. At R frame 3 the extreme extension also appears on vanilla, and source translations contain the large offsets. Do not erase that pose or alter native ANMs to make numerical stretch scores smaller. Recall frame 65 and dance frame 50 remain useful checks for Clash-specific cloth/contact defects.

After the full render, `$taskPython work/scripts/compose_rig_review.py` assembles labeled contact sheets and a hand before/after comparison. It verifies the render manifest's scene hash first. The current checkpoint has 27 renders, 100 rigid equipment/fastener components, nine smoothed cloth shells and a 64-entry export palette. See the master plan for exact remaining art checks.

`bootstrap.py` verifies 1,849 originals and 54 already-extracted Clash members, stages the supplied addon under `work/tools/`, and records the native export preset. `native_export.py` is a separate adapter; the staged addon is unmodified. Its SKL writer keeps source joint records byte for byte and appends a replacement palette when necessary. It rejects renamed/reparented/edited rest bones, moved armatures, nonfinite data and invalid weights. The exporter keeps at most four **already-authored** influences; it rejects excess rather than silently assigning a fallback bone.

The source staging scale of 0.01 is not a claim about OBJ unit metadata. `fit_draft.py` uses explicit landmark fits and leaves the skeleton untouched. It uses a body-only BVH donor, maps decorative stock armor weights onto the corresponding body bones, sets upper face/eyes rigid to Head, and anchors the reviewed upper collar to Spine3. It remains a starting point for art refinement.

`review_draft.py` preserves the native ANM files, importing actions for preview only. First/middle/last finite-coordinate samples are not collision, penetration, transition, gameplay or in-game shader tests. Poro is retained but hidden for ordinary preview renders; native joke visibility events remain a runtime gate.

`manager_checks.py` uses `C:/Users/etqdo/Downloads/cslol-go` by default; `--manager` can override it. It runs the bundled RitoBin and mod-tools against isolated fixtures in `build/`, then uses the supplied wadtools with project-local cache/config paths for independent extraction. The fixture `.fantome` files are labeled vanilla validation tests, never the Clash release. It does not launch a game overlay or install a mod into the manager's library.

## Validation records

Reports under `../validation/` cover source preservation, vanilla round-trip, eleven export regression checks, body groups/material records, shield sanitation/apertures, draft fitting, 59-animation sampling, Poro/Shield/palette checks, BIN byte preservation, and backend package round-trips. They separate offline passes from unfinished art and runtime gates.

The next phase is manual deformation refinement, geometry reduction and atlas baking. The final `Braum_Clash.fantome` is intentionally absent until those stages and the model/runtime/VFX/audio gates are complete.
