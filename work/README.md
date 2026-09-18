# Braum → Clash working pipeline

## Start here

HUD-only reproduction: [UI icon builder/checks](scripts/build_ui_icons_v1.py) uses the fully user-accepted audio_3x_v1 parent, `Ability icons/` inputs, saved [R image/prompt](textures/ui_icons_v1/R_PROMPT.md), and `clash new.avif` face crop. Seven added HUD assets only; all parent payloads exact. Includes native format/alpha and isolated backend checks. Current UI acceptance is recorded in the master checkpoint.

3x voice/SFX reproduction: [audio gain builder/checks](scripts/build_audio_3x_v1.py) derives from the custom-hex candidate and supplied native English VO event bank. Applies +9.542425dB to sound-level Volume, independently parses both banks and checks isolated backend extraction. Media is not reencoded; refuses an existing output directory. Current acceptance remains in the master checkpoint.

Custom user hex palette: [builder/checks](scripts/build_user_hex_v1.py) uses the B/full-R parent, existing palette atlas inputs and original pre-palette texture guides retained under `build/palette_b_silver_v1/`. Reproduce missing inputs via the B instructions below. Mapped review: Blender `render_palette_a.py -- --candidate user_hex_v1`. Preserves original compressed alpha and mapped trouser RGB blocks; no BIN changes. Current candidate/acceptance is in the master checkpoint.

Palette B/silver + full R reproduction: reuse the unchanged hash-recorded palette atlas inputs (or run `inspect_palette_a.py` in background Blender if missing), then [B texture builder](scripts/build_palette_b_silver_v1.py), then [full R combiner](scripts/build_palette_b_full_r_v1.py) and `validate_e_electric_v2.py palette_b_full_r_v1`. Optional mapped texture review: Blender `render_palette_a.py -- --candidate palette_b_silver_v1`. Combiner binds named legacy source text to archived BIN and changes only three R entries; current status is in the master checkpoint.

Palette A reproduction: run [read-only atlas extraction](scripts/inspect_palette_a.py) in background Blender, then [texture builder/checks](scripts/build_palette_a_v2.py), then [read-only mapped preview](scripts/render_palette_a.py). Outputs `build/palette_a_v2`; preserves completed candidates. Original BC3 alpha blocks are retained across all mips. Uses existing tooling only; no game/manager interaction. The master checkpoint controls acceptance.

Read the [current-state checkpoint](../audit/BRAUM_CLASH_MASTER_IMPLEMENTATION_PLAN.md#current-state--controlling-checkpoint-2026-09-17) for accepted work, the current `.fantome`, validation evidence, outstanding scope, and the single next action. That is the authoritative status; do not reconstruct it from historical entries below.

English VO reproduction: [local transcription](scripts/transcribe_clash_vo.py), [clip preparation](scripts/prepare_clash_vo.py), [VO and louder Q/R builder](scripts/build_clash_vo_v1.py), then [targeted validator](scripts/validate_clash_vo_v1.py). Uses root `Clash voice line.wav`, persisted [choices](audio/clash_vo_choices.json) and [transcript](audio/clash_vo_transcript.json); clip preparation/build require fresh output directories. Transcription uses faster-whisper 1.2.1/small.en in ignored `work/cache/voice_python` and `whisper_models`; encoding uses the existing portable wav2wem/vgmstream tools and corrected FNV-1 setup hashes. [Event mapping](audio/CLASH_VO_MAPPING_V1.md) documents native trigger limitations; exact source times/hashes are in `audio/clash_vo_mapping_v1.json`. Builder preserves the hash-bound directional/SFX v3 parent, including approved E, and boosts only seven Q/R volumes another 6dB. Runtime status remains in the master checkpoint.

“Continue” executes that next action under [AGENTS.md's continuation rules](../AGENTS.md#default-meaning-of-continue). Startup reading stops at the next `##` heading in each entry section; reuse unchanged context within a session. User-input gates remain binding.

Follow [AGENTS.md](../AGENTS.md) for change-dependent checks and bounded retries. Gameplay testing belongs to the user: provide a clickable `.fantome` link and a short checklist. Do not open/control League or cslol-go, install mods, change profiles, start overlays, or automate gameplay. Do not rebuild or repeat offline tests while waiting for feedback.

[VFX_LIGHTNING_TRIAL.md](VFX_LIGHTNING_TRIAL.md) contains the current trial's mappings, limitations, and reproduction commands. Reproduction commands are references, not a startup checklist; run only those justified by an actual change. Consult historical evidence selectively.

E v2 reproduction: [builder](scripts/build_e_electric_v2.py) and [targeted package validator](scripts/validate_e_electric_v2.py). These derive one candidate from v1 and refuse existing output directories. Current acceptance and next action remain in the master checkpoint.

Texture-only color-pop reproduction: [builder and texture checks](scripts/build_color_pop_v1.py), deriving from E v2 and preserving its VFX. Refuses existing output; current acceptance remains in the master checkpoint.

E motion/body-shadow follow-up: [E motion builder](scripts/build_e_motion_v3.py), then `validate_e_electric_v2.py e_motion_v3`, then [body shadow builder/checks](scripts/build_color_pop_v2.py). One combined handoff; fresh outputs only. Runtime status remains in the master checkpoint.

Clean-shield/stronger-color reproduction: [combined builder](scripts/build_color_pop_v3.py), then `validate_e_electric_v2.py color_pop_v3`. Refuses existing output; current acceptance remains in the master checkpoint.

Dark-blue kit/loading/passive reproduction: [kit builder](scripts/build_darkblue_kit_v1.py), [four-quarter passive builder](scripts/build_clash_passive_v1.py), then `validate_e_electric_v2.py clash_passive_v1`. User sources: root `clash new.avif` and `work/textures/passive_clash/source_logo.png`. Fresh outputs only; status and handoff remain in the master checkpoint.

White-core crackle reproduction: [builder](scripts/build_crackle_v1.py), then `validate_e_electric_v2.py crackle_v1`. Generated sprite source and prompt are under `work/textures/crackle_v1/`. E layer identification gate is recorded in the master checkpoint.

Gameplay-readability follow-up: [builder](scripts/build_readability_v1.py), then `validate_e_electric_v2.py readability_v1`. Covers centered loading crop, Q core, faint W logo, camera-facing E removal and sparse/dark-ground R. Fresh outputs only; status is in the master checkpoint.

Electrical SFX reproduction: [source inspection](scripts/inspect_sfx_source.py), [builder](scripts/build_sfx_v1.py), then [targeted validator](scripts/validate_sfx_v1.py). Requires root electricity WAV, native supplied banks, readability v1 parent, and portable wav2wem v0.1 / vgmstream r2117 at the paths recorded in the scripts. Tool provenance/hashes and source selection are in `validation/sfx_v1_build.json`. Uses mono 44.1kHz Vorbis at native durations/byte extents and preserves event banks. Builder/validator require fresh output directories; manual gameplay is the acceptance gate.

Logo/equipment refinement: [builder](scripts/build_refinement_v2.py), then `validate_e_electric_v2.py refinement_v2`. [Read-only atlas inspection](scripts/inspect_equipment_atlas.py) provides named-group UV masks and optional mapped texture previews without saving a scene. Current acceptance remains in the master checkpoint.

SFX cache-hash repair: v1 is a historical build stage with a known invalid setup hash, not a playable handoff. [Diagnosis](scripts/diagnose_sfx_silence.py) verifies native FNV-1 setup hashes; [v2 repair](scripts/build_sfx_v2.py) fixes IDs from retained v1, then `validate_sfx_v1.py sfx_v2` verifies. [Combine with refinement](scripts/combine_sfx_v2_refinement.py), then `validate_sfx_v1.py sfx_v2_refinement`, to preserve newer visuals without regeneration. Use the master checkpoint's final combined candidate for manual testing.

SFX volume adjustment: [volume builder and checks](scripts/build_sfx_v3_volume.py) adds +10dB only to the 20 custom sound objects in the events bank, preserves the working media bank/visuals, verifies the result with wwiser and an isolated package check, and requires a fresh output directory.

Directional Q / balanced E / connected W / sparse R reproduction: [visual builder](scripts/build_directional_v1.py), [preserve louder SFX v3](scripts/combine_directional_sfx_v3.py), then `validate_e_electric_v2.py directional_sfx_v3`. Fresh outputs only. Scoped checks cover the static particle mesh, changed texture and emitter fields; accepted character exports remain untouched. Current candidate and gameplay gate remain in the master checkpoint.

Travelling R strikes / stronger W / Q-R ice cast removal: [visual builder](scripts/build_strike_v1.py), [preserve latest VO and mix](scripts/combine_strikes_vo_v1.py), then `validate_e_electric_v2.py strike_vo_v1`. Fresh outputs only; accepted E is protected. Current acceptance remains in the master checkpoint.

## Historical pipeline and reproduction reference


All dated continuation status, runtime-access claims, and next steps below are historical. The master plan's current-state block and AGENTS.md supersede them, including old pending-model gates and optional-VO wording. Preserve this material for evidence and reproducibility, not as a queue of work to repeat.

## Latest continuation — accepted body atlas (2026-09-13)

**Now also built:** `build/model_runtime_trial/Braum_Clash_Model_Trial.fantome`. See [runtime test instructions](RUNTIME_MODEL_TRIAL.md). The shield coating is a separate trial; model-only packaging passes offline backend roundtrip and six-payload byte identity. Four key installed assets match the source baseline. Actual game validation is pending: native Computer Use currently exposes no apps. The runtime trial uses legacy diffuse/low-gloss and does **not** bind the accepted Blender normal map. No electrical VFX/audio or final release is claimed.

Reproduce the new continuation with `bake_shield_material.py` (only if its target scene is absent), `export_draft.py -- --scene clash_braum_shield_material_trial.blend --output model_shield_material`, then `$taskPython work/scripts/build_model_trial.py`. Tool binary: official `https://github.com/LeagueToolkit/ltk-tex-utils/releases/download/v0.3.0/ltk-tex-utils-windows.exe`, stored locally at `work/tools/ltk-tex-utils.exe`; hash recorded in the build report. `validate_model_runtime_trial.py` requires the prior package import and four installed-baseline extractions recorded in the validation logs. Full reproduction commands for those prerequisites are added below.

```powershell
& 'C:/Users/etqdo/Downloads/cslol-go/cslol-tools/mod-tools.exe' import build/model_runtime_trial/Braum_Clash_Model_Trial.fantome build/model_runtime_trial/imported
& 'C:/Users/etqdo/Downloads/wadtools-0.5.7-windows-x64/wadtools.exe' --config work/config/wadtools.toml --hashtable-dir work/cache/hashes --progress=false extract -i 'C:/Riot Games/League of Legends/Game/DATA/FINAL/Champions/Braum.wad.client' -o build/model_runtime_trial/live_baseline -H audit/sources/project.hashes.txt --hash eb9d53354a504663 --hash fbf88fcfc8ec8dc4 --hash 9b8248658ce51711 --hash 0b01eaec2c944f55 --no-bin-paths
& $taskPython work/scripts/validate_model_runtime_trial.py
```

Resume from `scenes/clash_braum_body_atlas_accepted.blend` (SHA-256 `e0f0664f45d6474fe988e3dcd07c7aad77311207e660c0af52d77260185fdafc`). Cuff/torso and reduced shield remain closed. The master plan's newest entry supersedes historical next steps below. Base color/opacity/normal bakes are complete and gameplay-equivalent to the reconstructed source preview in eight paired views. Fresh3963-frame validation and export pass; 58,314 exported vertices /51,253 triangles. This is offline acceptance, not an installable or runtime-accepted skin.

The incoming `body_atlas_ready_trial` was still failing21 overlaps and had never baked. Preserved it; the new `body_atlas_packed_trial` uses AABB packing and passes zero overlaps. Preview and accepted copies preserve all source mesh data, source UVs and67 torso corrections. Textures are `textures/body_atlas_trial/clash_body_{basecolor,opacity,normal}.png`. Four-pixel padding and13.17% atlas coverage have passed these gameplay-size previews; actual Riot mips/shader remain gates. See `validation/body_atlas_acceptance.json` for hash-bound evidence and limitations.

Reproduce only to new/absent output scene names; generators refuse existing target scenes. From project root, using the `$taskBlender` / `$taskPython` paths in the Reproduce section:

```powershell
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/repair_shield_atlas.py -- --scene clash_braum_body_atlas_ready_trial.blend --label body_atlas_packed_trial --uv-report body_atlas_ready_uv_validation.json --body --aabb
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/check_atlas_uv.py -- --scene clash_braum_body_atlas_packed_trial.blend --output body_atlas_packed_uv_validation.json --body
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/bake_body_atlas.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_body_atlas_contract.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_rig_refinement.py -- --scene clash_braum_body_atlas_preview_trial.blend --refinement torso_refinement.json --report body_atlas_full_validation.json --reuse-before
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/export_draft.py -- --scene clash_braum_body_atlas_preview_trial.blend --output model_body_atlas
& $taskPython work/scripts/compare_body_atlas.py
& $taskPython work/scripts/accept_body_atlas.py
```

Comparison render manifests record scenes, camera direction, scale, resolution and four exact cases. Use `render_rig_refinement.py` with those arguments to regenerate the two source/two baked sets before composing sheets. `export_draft.py` combines body objects only in export memory to produce one unique `Braum` material submesh; the editable scene retains all11 groups. Next: shield texture/material finish, model-only BIN/texture integration, package and runtime gate, then VFX/SFX/VO.

The authoritative progress record is [the master plan](../audit/BRAUM_CLASH_MASTER_IMPLEMENTATION_PLAN.md). These scripts implement the offline source, export and draft-rig stages. They do not build the finished cosmetic replacement.

Current scope is **playable first**: finish and validate the model-only build in the intended runtime, preserve a recoverable checkpoint, then implement electrical VFX, authentic Clash SFX and authentic Clash English VO. All four are required for final completion; earlier optional-VO wording in historical plans is superseded. Audio extraction is deferred until that checkpoint and must not bypass access controls.

### Latest continuation — cuff gameplay gate closed; Stage 4 active (2026-09-13)

**Accepted offline gameplay baseline:** `scenes/clash_braum_gameplay_accepted.blend`, a byte-identical copy of `scenes/clash_braum_torso.blend` at SHA-256 `2501fd57112bb324515e56dc33cb986905f0e50813f5aa946c56ad27e24f030a`. No new attachment is retained; zero accepted vertices/faces/weights/UVs changed and all67 torso seam corrections remain. This supersedes older instructions below to keep iterating on the cuff or block Stage4.

All28 individual seam attachments had already been tested on17 poses. Only871→657 passed strict collision samples; the new measured report shows it worsens incident stretch (R17 elongation0.0352516→0.0519370) without meaningful visual benefit. The final gameplay review inspected102 renders: parent/single/all28,17 difficult poses including R3/R16/R17/R18 and recall65, two opposing elevated cameras at360px/ortho-scale5. Single871 differs by no pixels>8/255 across34 views; all28 differs by only27 such pixels total. No obvious open cuff hole or major local clipping appeared at that scale. Close-up stretch/intersections are accepted minor limitations; native extreme arm extension remains. This is an offline visual judgment, not a live-game certificate. **Do not reopen microscopic cuff work.**

Fresh17-pose single and identity checks have zero new pairs and exact protected topology/UV/weight contracts. Fresh59-action/3,963-frame structural validation passed (rigid max error0.000002338248); export passed at50,002 vertices/54,447 triangles/97 native joints with1,018-triangle Poro preserved. Acceptance and exact evidence: `../validation/gameplay_checkpoint_acceptance.json`, `cuff_seam_measured_options.json`, `gameplay_checkpoint_validation.json`, `model_gameplay_checkpoint_export.json`. Export files are under `../build/model_gameplay_checkpoint/`, development-only.

**Stage4 trial:** `scenes/clash_braum_shield_collapse_trial.blend` reduces the rigid shield12,256→9,062 triangles, preserves every body mesh exactly, and restores the main shield part that exceeded the explicitly chosen approximate reduction budget. Retained max bidirectional sample error0.000967754 units.17-pose protected-body/rigid-shield checks pass; four gameplay views show no obvious silhouette regression. Export passes at46,765 vertices/51,253 triangles/97 joints. **Not promoted**: normals, UV interpolation, aperture/contact review and full animation checks remain. The planar and weld-planar scenes are superseded diagnostic trials (only4/3 triangles removed).

Reproduction from the project root, with the runtime paths defined below:

```powershell
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/measure_cuff_seam_options.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/render_cuff_gameplay.py
& $taskPython work/scripts/compose_cuff_gameplay.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_cuff_gameplay_targeted.py
& $taskPython work/scripts/accept_gameplay_checkpoint.py
# Generator refuses to overwrite an existing trial; do not rerun over edited scenes.
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/trial_shield_planar_reduction.py -- --weld --collapse --max-surface-error .003
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_shield_reduction_targeted.py
```

Next: finish reduced-shield UV/normal/aperture/contact review with matched close-up front/back and directional-E views, then all-action validation before promoting the reduction. Continue body reduction and controlled atlas baking toward the15,000–25,000 body+shield target. Read the newest master-plan entry for precise changed-part counts, prior failures and evidence scope. No installable Clash package, runtime acceptance or audiovisual implementation is claimed.

### Latest support-topology tests — 2026-09-13

The accepted scene is still `scenes/clash_braum_torso.blend`, unchanged. The proposed broad support-loop experiment below has now been implemented and **rejected**. Three diagnostic scenes (`clash_braum_cuff_support_v2_trial.blend`, `clash_braum_cuff_support_control.blend`, `clash_braum_cuff_support_linear_trial.blend`) each fail all 17 sampled poses, including R16–R18. Added forearm geometry is 508 vertices / 1,016 triangles; no original rest vertices moved. The first `clash_braum_cuff_support_trial.blend` is a superseded, unvalidated generator draft. None is a checkpoint to continue modeling from.

`cuff_support_topology.py` retains explicit source-face/vertex ancestry and UV/normal mapping; `validate_cuff_support.py` uses those mappings for collision comparison and principal stretch measurements. Protected contracts pass, but surface/shape gates fail. The unchanged-scene control passes with zero new pairs. Full animation validation/export remains deferred for these rejected candidates. Reports and recurring original face/vertex/pose mappings are in `../validation/cuff_support_review.json`. R17/recall65 images are under `../validation/previews/cuff_support_v2/`, `cuff_support_control/` and `cuff_support_linear/`.

Next: a smaller cuff-rim attachment/clearance correction against the **unchanged forearm**, starting with Object009 polygon1221 versus Object004 polygons2448/2449 and the opposite contact Object009 polygon1325 versus Object004 polygon98. Exact vertices and failing pose lists are already recorded. Do not repeat the broad subdivision or smooth/linear trials. Read the newest master-plan section before changes.

For evidence inspection (no regeneration of scenes):

```powershell
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_cuff_support_failures.py
```

`trial_cuff_support.py` refuses to overwrite any existing scene. A future experiment must use a distinct `--label`. The validators record failures in JSON even when the Blender process exits0; do not confuse successful execution with acceptance.

### Current cuff continuation — 2026-09-13

Continue from `scenes/clash_braum_torso.blend` (SHA-256 `2501fd57112bb324515e56dc33cb986905f0e50813f5aa946c56ad27e24f030a`). Accepted torso work and all67 seam corrections are closed/preserved under the latest user instruction. The historical outline continuation below is not the current task. No new scene was accepted or saved this session.

Five cuff candidates completed15-pose testing and were rejected: existing full-ring skin transfer (new intersections in14 poses), initial wrist attachment, finger-preserving wrist attachment, outward clearance fit, and coupled distal-skin attachment (each fails all15 poses). Protected geometry/weight, topology and UV checks passed; collision and/or silhouette gates failed. R17/recall65 comparison renders were inspected. The coupled version visually attaches the cuff but raises forearm R17 edge elongation0.48781→0.75662, so it is not a solution. Full structural validation/export was correctly deferred for these rejected candidates; the accepted parent's previous passes remain authoritative.

Read `../validation/cuff_continuation_review.json` and the newest master-plan entry for exact reports, candidate names and unvalidated alternatives. All new changes are diagnostic Python scripts, candidate JSONs and renders; source/accepted Blender files are preserved. `inspect_cuff_attachment.py` reads the actual saved scene and measures cuff shell coordinates/weights and native posed edges. `trial_cuff_wrist.py`, `trial_cuff_envelope.py` and `trial_cuff_distal_skin.py` generate only in-memory candidate descriptions. Their default output names are fixed; preserve evidence before rerunning a modified generator. The surface validator reports failures in JSON even when the process exits0.

Next: investigate local cuff/distal-forearm support loops and a continuous attachment transition. Preserve inner/outer thickness and finger influences. Explicitly map old/new polygons before testing any topology change. Start with left edges2671–2673/2696–3353 and right895–986/993–1001 at R17 and recall65, checking both cuffs and bare forearms. No existing cuff candidate is suitable for promotion.

Regenerate the compact review without repeating Blender validation:

```powershell
& $taskPython work/scripts/finalize_cuff_review.py
```

### Interrupted half-strength torso validation

The structural 3,963-frame run and development export completed successfully in `../validation/torso_outline_validation.json` and `../validation/model_torso_outline_export.json`. They applied `torso_local_alternatives.json:outline_s0.5` in memory to `scenes/clash_braum_torso.blend`; no accepted scene was saved. Do not repeat those completed checks merely because the prior turn ended. All-frame local surface regression is a separate check:

```powershell
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_torso_coupled_targeted.py -- --candidate-weights torso_local_alternatives.json:outline_s0.5 --all-frames --output torso_outline_half_all_frame_local.json
```

**Final result: half strength REJECTED; accepted scene remains `scenes/clash_braum_torso.blend`.** The full local sweep found58 new pair/frame occurrences in33 frames (seven clips). Both revisions completed3,963 frames. No candidate scene was saved. Exact failures and recovered structural/export identity are in `../validation/torso_outline_recovery_audit.json`; regenerate that read-only summary with `work/scripts/audit_outline_checkpoint.py`.

The checker preserves original polygon IDs and uses conservative bounding-box culling before the existing BVH overlap test. Its optimized 15-pose results exactly match the prior report (`torso_outline_half_culling_check.json`). It checks changed-vertex incident faces against body/shield surfaces, excluding shared-vertex self pairs, Poro and the vanilla reference; this is not a whole-body or runtime collision certificate. Use repeatable `--case clip:frame` for small follow-ups.

`search_outline_backoff.py` tested five smaller deltas at48 poses; only one-sixteenth of half strength cleared those samples, with negligible improvement and no acceptance. `search_outline_constraints.py` tested252 nearby weight combinations plus two controls; none cleared those poses with >0.0001 improvement in both target edges. These scripts never save scenes. Their JSON reports preserve all results. Do not rerun completed searches blindly.

Next: a local topology/clearance investigation around Object002 vertex143 and its incident faces231/316/558/559, preserving all67 accepted seam corrections. `inspect_outline_failure_geometry.py` maps colliding Object007 shells1668/1672/1676/1680, Object004 shell12 and Object009 shell652. Start at recall66–72 and passive18–29. A topology-changing trial needs an explicit surface mapping for regression comparison; raw old/new polygon IDs are insufficient. The master plan records the complete failing-frame set and remaining grip/cuff/art gates. Stage3 remains open; there is no playable build yet.

## Outputs to inspect

| File | Purpose |
|---|---|
| `scenes/braum_native_baseline.blend` | Original mesh and all 97 native joints, corrected imported winding and preserved normals. |
| `scenes/clash_source_materials.blend` | Eleven OBJ groups and reconstructed source material assignments. |
| `scenes/shield_prepared.blend` | Original shield geometry with baked transforms and rebuilt finite UVs. |
| `scenes/clash_braum_fit_draft.blend` | Draft body fit, seed weights with selected corrections, rigid shield and retained hidden Poro. |
| `scenes/clash_braum_animation_review.blend` | Same draft with all 59 native animations as retained Blender actions. Select `Braum_Native` and an action in the Action Editor. |
| `scenes/clash_braum_torso.blend` | **Current partial-improvement checkpoint.** 67-vertex lower-vest seam correction; remaining multi-pose tradeoffs documented for Medium. |
| `scenes/clash_braum_shoulders.blend` | Previous checkpoint. Partial shoulder/sleeve correction and three torso hardware attachments; see latest continuation. |
| `scenes/clash_braum_deformation.blend` | Previous checkpoint. Local forearm, seat and belt weight corrections; see deformation continuation below. |
| `scenes/clash_braum_rig_refined.blend` | Previous checkpoint. Authored hand fit/digit weights, rigid equipment and fasteners, smoothed cloth/neck weights; all 59 original actions retained. Stage 3 remains open for final contact/deformation review. |
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

### Latest local review (2026-09-12)

The working checkpoint is still `scenes/clash_braum_torso.blend`. The new `clash_braum_torso_coupled.blend` and `clash_braum_handle*_trial.blend` files are **rejected diagnostic trials**. See the latest master-plan section and `validation/stage3_local_review.json` before using them. No new comprehensive validation/export was run because no trial passed visual acceptance.

New read-only diagnostics:

```powershell
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_torso_coupled.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_local_handle.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_local_handle_targeted.py -- --scene clash_braum_handle_normal_trial.blend --output local_handle_normal_targeted.json
```

Use `render_rig_refinement.py` with `--edge Object002:143:190 --scale .4` for local edge views. Grip views can combine `--isolate-grip --hand-surfaces` to remove sleeve occlusion; `--vanilla --isolate-grip` is now supported. These remove faces in memory for rendering only and never save a scene. Supply distinct labels and an explicit scene; manifests record the diagnostic options.

`trial_local_handle.py` reproduces only auxiliary-handle experiments from the torso parent. Its `--label` determines both child scene and report; always choose a new label for a new trial. The last rejected fit used `--knuckles --normal --offset=-.06 --label handle_normal_trial`. Do not regenerate existing trials over manually edited files. The two `search_local_handle_*` scripts retain bounded collision-free numerical alternatives, not accepted fits. The next grip step requires a contoured surface fit; straight-bar variants either cut through the glove or leave the fingers open beside it.

### Latest lower-torso continuation

Continue from `scenes/clash_braum_torso.blend` with the shoulder parent preserved for comparison. The master plan records the remaining short-seam versus long-edge tradeoff and rejected grip offset; **Medium is recommended for the next coupled correction**. Reproduce only this child if it has no newer manual edits:

```powershell
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/refine_torso.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_torso_targeted.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_cloth_defects.py -- --scene clash_braum_torso.blend --output torso_cloth_defects.json --case braum_spell4:17 --case braum_dance_loop:50
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_rig_refinement.py -- --scene clash_braum_torso.blend --refinement torso_refinement.json --report torso_validation.json --reuse-before
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/export_draft.py -- --scene clash_braum_torso.blend --output model_torso
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_grip_targets.py -- --scene clash_braum_torso.blend
```

Use the 15-pose check during iteration; comprehensive checks belong at a final checkpoint. New development pair: `build/model_torso/`. Repeat the unsaved rejected offset experiment with `inspect_native_grip.py -- --scene clash_braum_torso.blend --output grip_offset_trial.json --trial-left-offset`; it does not save any scene. Omit that flag and use a distinct output for a baseline report. For lower-torso matching renders use `--only-object Object002 --direction=3,7,2 --case braum_spell4:17:torso --case braum_dance_loop:50:torso`; for the running-E left palm use `--isolate-grip --direction=3,-7,3 --case braum_spell3_run0:14:L_Hand`. Explicitly supply scene and label. Do not force R26 contact or rerun discarded broad torso weighting approaches.

### Previous shoulder continuation

Continue from `scenes/clash_braum_shoulders.blend`. Preserve it under a separate name before manual edits or rerunning its generator. The parent deformation scene is unchanged. These commands reproduce/check only this continuation:

```powershell
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/refine_shoulders.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_shoulders_targeted.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_cloth_defects.py -- --scene clash_braum_shoulders.blend --output shoulder_cloth_defects.json
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_rig_refinement.py -- --scene clash_braum_shoulders.blend --refinement shoulder_refinement.json --report shoulder_validation.json --reuse-before
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/export_draft.py -- --scene clash_braum_shoulders.blend --output model_shoulders
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_native_grip.py
```

Use the 12-pose targeted check during iteration; full validation is for meaningful checkpoints. New pair: `build/model_shoulders/`; 104 rigid components. For matching isolated shoulder renders, use `--only-object Object002 --only-object Object004 --case braum_recall:65:torso --direction=-3,-7,2` with an explicit scene and distinct label. Cloth inspection now accepts `--case braum_spell4:17`. The master plan records partial improvement, pose tradeoffs and exact remaining torso/cuff edges. Running E frame14 left-hand proximity differs substantially from native; R26 already separates hands from the native shield and should not be forced into contact based on this offline pose.

### Previous deformation continuation

Continue from `scenes/clash_braum_deformation.blend`; the refined scene below is its preserved input. Do not rerun earlier pipeline stages. Reproduce this child only if it has no additional manual edits:

```powershell
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/refine_deformation.py
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_cloth_defects.py -- --scene clash_braum_deformation.blend --output deformation_cloth_defects.json
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/validate_rig_refinement.py -- --scene clash_braum_deformation.blend --refinement deformation_refinement.json --report deformation_validation.json --reuse-before
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/export_draft.py -- --scene clash_braum_deformation.blend --output model_deformation
& $taskBlender --background --factory-startup --python-exit-code 1 --python work/scripts/inspect_grip_targets.py
```

The new development pair is `build/model_deformation/`. For unobstructed grip views use `render_rig_refinement.py -- --scene clash_braum_deformation.blend --label deformation_grip_isolated --isolate-grip --direction=-3,7,3 --case braum_spell3_idle180:29:R_Hand`. Isolation is temporary render visibility, not a scene edit or collision check. The master plan records remaining shoulder edges and E/R grip limitations. New checks cover 101 rigid components; old reports/renders below describe their earlier checkpoint.

### Previous refinement checkpoint reproduction

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
