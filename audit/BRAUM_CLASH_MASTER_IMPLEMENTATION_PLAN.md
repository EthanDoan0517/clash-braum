# BRAUM → CLASH MASTER IMPLEMENTATION PLAN

## Implementation tracker — continuation started 2026-09-10 UTC

The original 310-line handoff was read completely before changes. Its supplied file ends after the package validation paragraph; the referenced numbered stages and footnote definitions are absent. The ordered stages below make the documented dependencies executable without revisiting the established design. Historical Phase 0 statements below remain the audit baseline; this tracker records subsequent outputs.

| Stage | Status | Work / exit gate |
|---|---|---|
| 0. Source audit | Complete and re-verified | All 1,849 original hashes and 54 extracted Clash members match. See `validation/source_integrity.json`. |
| 1. Export foundation | Offline checks complete | Vanilla round-trip, 11 export-contract regressions, byte-identical skin0 BIN round-trip, and cslol-go backend fixture import/export/reimport passed. Runtime acceptance remains a separate gate. |
| 2. Source preparation | In progress | All 11 OBJ groups/material assignments reconstructed; two-face discrepancy resolved; shield transforms baked and finite UVs rebuilt. Viewport classification/open-aperture decision is complete. Finished source-material response and replacement shield materials remain. |
| 3. Proportion and rig work | Hand/equipment/cloth refinement implemented; final art gate open | Continue from `work/scenes/clash_braum_rig_refined.blend`. Both hands refit and individually weighted by digit; 100 equipment/fastener components have stable attachments; nine cloth/neck shells refined. All 59 native actions retained. Final grip, shoulder/cuff and pelvis deformation review remains; numerical checks are not final art approval. |
| 4. Geometry and texture finish | Pending | Reduce to the documented initial triangle target; bake controlled atlases; assess silhouette and normals. |
| 5. Model-only build | Development export validated; actual model-only package pending stages 3–4 | Draft pair has 50,002 exported vertices / 54,447 triangles, 51 palette entries, exact native joint records and retained Poro. No atlas/BIN material integration or installable Clash build yet. |
| 6. Animation and runtime gate | Pending verified baseline and completed model | All documented animation families, directional E, culling, Poro reveal and materials. Live main WAD now exists but differs in SHA-256 from the Downloads provenance archive; patch compatibility/pristine status remains unverified. |
| 7. Electrical VFX | Pending stage 6 | Clone only changed definitions into skin0; isolated custom texture and particle geometry paths; preserve state/timing/readability. |
| 8. Selected SFX | Pending model/VFX gates | Audition and select media; version-145 bank no-op and compatible WEM replacement tests. VO remains optional. |
| 9. Release package | Pending all gates; backend format compatibility tested | Only used replacements in `Braum_Clash.fantome`; closure/hash/CRC tests and final manager import/reimport. The vanilla backend fixture passed but is not the Clash release. |

Repository discovery: this folder has no Git repository or applicable `AGENTS.md`; no `work/`, `build/`, `validation/` or `dist/` existed on arrival. Blender 5.2 is installed. The provided audit scripts are evidence generators with top-level side effects, so new implementation helpers live under `work/scripts/` instead of importing or re-running those scripts and overwriting the baseline inventory.

Reproduction begins with `work/scripts/bootstrap.py` and `work/scripts/roundtrip.py`. Machine-readable validation reports are written under `validation/`; working scenes under `work/scenes/`. No release artifact is claimed by an offline export.

### Verified implementation discoveries

- **Exporter correction:** the unmodified Aventurine vanilla round-trip regenerated inverse-bind components with a maximum difference of `0.0027103424` game units and discarded original normals (maximum component difference `1.5527793`). This failed the planned preservation gate. `work/scripts/native_export.py` retains Aventurine's SKN packing/palette code, collects corner normals with inverse-transpose transforms and corrected handedness, and preserves original SKL joint records. If the palette changes, only palette header fields/resource size change and a new palette table is appended. With an unchanged palette, the SKL is byte-identical to S0. Bone names/order/parents/rest frames and identity armature transform are checked before export. No vendor files or original assets were edited.
- **Corrected round-trip:** max position error `0.0000152588`, UV error `0`, weight error `0.0000001192`, normal error `0.0000002384`; bind error `0`; identical 76-entry palette. Exact float normals are retained for immutable vanilla/Poro geometry because Blender's compressed custom-normal storage slightly perturbs a few source corners. New geometry uses its actual corner normals and splits at hard edges.
- **OBJ discrepancy resolved:** lines 104661–104662 in group `Object007` repeat position index 19005 inside each triangle. Both triangles have zero area. The reproducible group importer omits exactly those two faces, yielding the previously observed 41,173 triangles. See `validation/body_source_preparation.json` for original statements and all group assignments.
- **Additional missing texture:** the `eye` material references an absent `Textures/CHR_Clash_Eyes_DiffuseMap.dds`. The supplied `.tga` is a documented preview substitute requiring visual review. The misleading `hair_front (1)` material/group is around the eyes, not scalp hair; do not delete it just because the target is bald.
- **Source materials:** use exact `matName` relationships from the tbscene evidence. Color textures, base normal maps, source channel assignments and full source blocks are retained in the preparation report. Principled preview response is an approximation; the custom detail-normal shader, source reflectance and atlas bake remain unfinished.
- **Shield sanitation:** all seven source meshes retain their world-space coordinates, with identity object transforms and one fresh finite UV set each. Original missing textures and unused packed hair images are excluded from the working scene. The source shield remains untouched.
- **Viewport geometry:** front/back/oblique renders and bidirectional ray tests confirm open areas at the central viewport and beside the upper bars; hardware and lower armor control rays hit geometry. The initial model uses these existing apertures. No opaque plane was added. `mesh_22.001` is a small hardware display and `mesh_23.001` a small hardware surface, not a full ballistic window. See `validation/shield_aperture.json` and `validation/shield_components.json`.
- **Draft rig validation:** all 59 native ANMs load into `work/scenes/clash_braum_animation_review.blend`; first/middle/last samples have finite mesh coordinates. Eight representative renders cover idle, attack, run, recall, Q/W/E/R. The first collar test borrowed clavicle/shoulder-helper weights and visibly stretched; the upper collar now follows Spine3. The Shield prop was repositioned from a bounding-box fit to measured idle/E/run hand landmarks without changing any joint. Further grip/finger, wrist, knee and equipment refinement remains mandatory.
- **Matched draft pair:** `build/model_draft/braum_clash.skn` and `.skl` are development outputs only. The palette differs (51 versus the original 76 entries) and has been independently verified against every positive vertex weight. All 97 joint records match the source exactly. Poro retains 769 vertices / 1,018 triangles; corner position/normal/weight differences are below `0.000002`, UVs identical. Do not install this pair by itself: the source-material submesh names remain temporary, atlases are unbaked, and `skin0.bin` has not been repathed.
- **Manager resolved by the user:** `C:\Users\etqdo\Downloads\cslol-go`, containing `ModLoader.exe` and bundled `cslol-tools/ritobin_cli.exe` / `mod-tools.exe`. `ModLoader.dll` reports file version 2.15.0 and product build `1.0.0+e5983b3964e726a7baaecfc9d1649f8a3fd95bb1`. Executable hashes are recorded in `validation/manager_compatibility.json`. The [project README](https://github.com/Aurecueil/Cs-lol-go) identifies this as cslol-go and its ModLoader entry point (accessed 2026-09-10); compatibility claims here come from the supplied binaries, not from assuming cslol-manager and cslol-go are identical.
- **Backend compatibility passed:** a clearly labeled vanilla fixture under `build/manager_compat/` imports, exports and reimports with the user's `mod-tools.exe`. The reexport is a conventional packed WAD in a ZIP; independent wadtools extraction confirms both exact payloads and expected WAD hashes. Both ZIP CRCs and case-insensitive path uniqueness pass. No overlay was started, no game files were modified, and the manager GUI was not used to install a skin. GUI import and actual League acceptance remain open gates.
- **BIN writer established:** the user's RitoBin converts the complete skin0 BIN to hashed text and back with byte-identical SHA-256 `3f9b4f8c3b621db3354b059ea037d1b065bb83feb5fc9392480d2e028436c576`. Use this binary and hashed format for subsequent lossless whole-entry edits; preserve all unrelated records.

### Stage 3 continuation — 2026-09-10

The complete existing plan, pipeline README, saved scenes, exporter and relevant validation records were checked. This is still not a Git repository, and no applicable `AGENTS.md` was found. Source audit, import reconstruction and manager compatibility work were not restarted.

- **Implemented:** `work/scripts/refine_rig.py` reads the previous animation review checkpoint and writes a separate `work/scenes/clash_braum_rig_refined.blend`. It does not regenerate or overwrite that input scene. The draft left fingers had no finger-joint weights, while several right fingers inherited index-finger weights. A measured, orientation-preserving hand fit and explicit digit-shell assignments now correct 2,076 hand/cuff vertices. Source physical shell IDs and fit residuals are retained in `validation/rig_regions.json` and `validation/rig_refinement.json`.
- **Equipment and cloth:** 78 deliberately selected equipment/strap/armor shells plus 22 nearby fasteners (100 components / 8,352 vertices) now follow stable native bones. Nine continuous cloth/neck shells receive local weight smoothing across coincident position seams, preserving geometry, UVs, head rigidity and digit assignments. The lower neck no longer borrows jaw/clavicle motion. No joints, native animations, gameplay records, shield geometry or Poro geometry were changed.
- **Development export:** `build/model_rig_refined/braum_clash.skn` and `.skl` are the current refinement pair: 50,002 exported vertices, 54,447 triangles including Poro, and a 64-entry palette. Exact native joint records, rigid Shield weights, normalized maximum-four influences and Poro corner preservation pass the existing independent export checks. This is still above the triangle target and has temporary material names; do not install it as a finished skin. `export_draft.py` now accepts explicit scene/output arguments; its original defaults remain available.
- **Important new review evidence:** first/middle/last samples missed severe intermediate deformation. The new validator samples all 3,963 integer frames across the 59 native clips and compares actual evaluated mesh data, rigid-component transforms and unchanged imported action channels. `braum_spell4` frame 3 also stretches vanilla Braum under the same action; the source ANM contains unusually large joint translations there (see `validation/animation_extremes.json` and `validation/previews/vanilla_extremes/`). Preserve this source motion. Do not classify every large edge ratio as a Clash-specific failure or modify ANMs to lower the score.
- **Visual status:** hand close-ups show the draft left wrist collapse corrected and right digits curling together in E. Recall/dance hardware spikes were traced to individual components and corrected. Stage 3 is **not final**: inspect forearm/cuff continuity and armpit/shoulder attachment at recall frame 65, the seat/crotch and torso overlap at dance-loop frame 50, and palm/handle contact through E angles and R. These are concrete remaining art checks before reduction/baking. Render manifests identify the scene hash and exact cases; a numerical pass does not establish collision-free poses or runtime snapping.
- **Final checks for this checkpoint passed:** all 3,963 frames have finite evaluated geometry and valid authored weights; all ten exposed digit shells address their intended native digit chains; imported action channels and native rest contract are unchanged. Maximum error between 100 rigid components and their intended native bone transforms is `0.0000023383` Blender units. Current export preserves Poro with maximum corner-position error `0.0000019074` game units and identical UVs. Python compilation passes. The final 27-render set and labeled contact sheets are in `validation/previews/`; [hand comparison](../validation/previews/rig_hand_comparison.png) shows before/after with matching cameras. Detailed results: `validation/rig_refinement_validation.json`, `validation/model_rig_refined_export.json`, `validation/refined_render_manifest.json`. No atlas, skin0 integration, model-only install or release package has been produced.
- **Corrected external checkpoint:** the live `C:/Riot Games/League of Legends/Game/DATA/FINAL/Champions/Braum.wad.client` now exists (92,800,510 bytes). SHA-256 is `fa02c0a98b5080f3524d8d6daafc4bf3019b83c60d5a42b64bd88cd9bf722414`, versus `e2b651ef2a582c23331d848019949079a9235ed6d1a4c8c21da4fb55c361627d` for the Downloads archive. This session only read/hashed it. Presence and equal file size do not establish patch compatibility or identical member content. See `validation/live_wad_checkpoint.json`; perform provenance/content verification at the runtime baseline gate instead of assuming it is still missing.

The original `clash_braum_animation_review.blend`, `clash_braum_fit_draft.blend` and `build/model_draft/` remain earlier checkpoints. Use the refined scene and pair for continuation. The [working pipeline instructions](../work/README.md) include the new commands and diagnostic tools.

### Next implementation work from this checkpoint

1. Finish stage 3 from **`work/scenes/clash_braum_rig_refined.blend`**, not the earlier seed. Start with the remaining forearm/cuff and shoulder continuity at `braum_recall` frame 65, pelvis/seat and torso overlap at `braum_dance_loop` frame 50, then palm/handle contact at E directional extremes and R overhead/landing. Use `inspect_cloth_defects.py` for exact remaining edges and `render_rig_refinement.py` for isolated poses. Keep the original R-frame-3 stretch; the vanilla comparison and source translations establish that it is not introduced by this hand/equipment pass. Do not mark the rig final because the all-frame numerical checks passed.
2. Reduce the current 53,429 body+shield triangles toward 15,000–25,000, retaining the separate 1,018-triangle Poro. Preserve face/fingers/outline; remove hidden or redundant source geometry before aggressive decimation. Validate exported split-vertex counts again.
3. Bake reconstructed materials to a controlled atlas, including source channel/detail interpretation. Author finished shield frame/electronics textures. Replace temporary source submesh names with `Braum` / `ShieldFrame` and retain `Poro`; add `ShieldGlass` only for a separately tested pane.
4. Use the proven RitoBin no-op workflow for exact new model/texture references in skin0, then validate model-only reference closure and package it for cslol-go. The live main WAD now exists; establish its pristine, patch-compatible content before runtime testing. Its hash differs from the supplied provenance archive.
5. Resume VFX, then selected SFX, only after the model gate. No electrical effects, replacement audio or final `Braum_Clash.fantome` has been produced yet.

See [working pipeline instructions](../work/README.md) for commands and generated-file ownership. Source preparation renders are under `validation/previews/`; draft animation renders under `validation/previews/draft/`.

## Technical decision

The conversion is feasible as a substantial mesh, material and effects project. It is **not ready for direct export**. Use base Braum, the supplied bald Clash body, and the supplied reworked CCE shield. Preserve Braum’s native joint hierarchy, bind pose, animation graph, gameplay records and event timing. Reshape and weight Clash to that system. Build a matched SKN/SKL pair, validate a model-only replacement, then add electrical effects and selected audio.

The highest-priority discoveries are:

1. **Braum’s shield is part of his character mesh, with its own animated skeletal branch.** It is not a separate shield file attached to the left hand. Exactly 1,398 vertices in the original `Braum` submesh are rigidly weighted to `Shield`. The branch is `Origin → Shield`; both hand snap bones are separate helpers.
2. **The Clash body has no usable rig.** The supplied OBJ has geometry and UV coordinates but no armature, weights or material assignments. A complete Braum-compatible weighting pass is required.
3. **The shield source is incomplete.** Three distinct active texture files are missing, a duplicate image datablock points to one of those same files, and several of its 11 UV layers contain inappropriate values, including NaNs. The transparent viewport is not an export-ready material.
4. **Preserving the skeleton does not mean blindly reusing its original bytes.** Aventurine rebuilds the mesh’s bone influence palette. A newly exported SKN must be paired with a compatible SKL palette while retaining the original joint names, hierarchy and bind transforms.
5. **Most base effects are in shared multi-skin BINs.** Only three relevant VFX definitions are embedded in `skin0.bin`. Copying or editing presumed “base particle files” would miss the actual relationships and could affect other skins.
6. **The live main Braum WAD is absent at the inspected installation path.** A separate archive in Downloads exactly reproduces the supplied extraction, but the live game needs a pristine, patch-matched archive before testing.

The recommended first release includes the Clash body, tactical equipment, rigid CCE shield, a tested translucent or open-aperture viewport, readable electrical Passive/Q/W/E/R effects, and selected electrical SFX. Full custom voice-over is an optional extension. Keep the original Poro joke component for compatibility in the first release; it is a small deliberate visual exception, not an overlooked mesh.

This document specifies future work. No replacement skin, modified game asset or `.fantome` package was created in Phase 0. All 1,849 original project files passed a final SHA-256 preservation check. Audit-only extracted copies, decoded records, inspection scripts and a geometry diagnostic image are separate from the originals.[^1]

## Evidence and confidence

**Confirmed** means directly read from the supplied files, archive records, installed binaries or inspected source code. **Recommendation** means an engineering decision based on that evidence. **Test gate** means behavior that requires a future export or in-game check; it is not represented as already working.

The local League metadata reports `16.17.8104348+branch.releases-16-17.content.release` and the corresponding `.code.public` version. This identifies the inspected installation; it does not prove the separately supplied main WAD belongs to that exact patch, nor establish the latest public patch. The main and localized archives use WAD version 3.4. Source archive provenance is partially established: all 1,843 supplied extracted files match an independent extraction of the Downloads archive, with no missing or mismatched files.[^1]

The audit resolves **1,802 of 1,852 combined WAD entries**: 1,793 of the 1,843 main entries, plus all nine localized entries. Fifty original main entries retain unknown paths. All 91 supplied BINs parse successfully and their file paths are resolved. All 72 non-null base VFX bindings resolve to definitions; their 135 unique explicit file dependencies are supplied. This is not a claim that every engine shader, shared audio object or global game dependency is contained in this champion archive.

The complete evidence accompanies this report:

- [Searchable original-file inventory](ORIGINAL_FILE_INVENTORY.html): every original filename, extension, absolute original path, likely purpose, relevance, discovered references, size and SHA-256.
- [Technical appendices](TECHNICAL_APPENDICES.md): exact shared BIN paths, all 97 joints, all 59 animation files and graph bindings, every base VFX dependency, all 94 audio events and their media relationships, and all archive members.
- [Machine-readable inventory](evidence/project_inventory.json), [BIN index](evidence/bin_index.json), [path map](evidence/path_map.json), [preservation check](evidence/preservation_check.json).

No in-game test, new asset export, material conversion or auditory identification of every media clip was performed. Shader compatibility, deformation quality, actual sound selection and manager import behavior remain explicit later gates.

## Supplied project inventory

Project root, abbreviated **P** below, is `C:\Users\etqdo\Downloads\Clash Braum project`. Original source paths are immutable inputs. Future paths beginning `work/`, `build/`, `validation/` or `dist/` are **proposed outputs**, not files claimed to exist.

| Original path relative to P | Type / count | Likely purpose and relevance |
|---|---|---|
| `Aventurine-3.1.5.zip` | ZIP, 465,077 bytes | League Blender addon distribution; relevant tool, not game content. Full members in appendix 7. |
| `Braum.en_US.wad.client` | WAD 3.4, 5,237,821 bytes; nine entries | Localized base/skin02/skin24 audio archives. Only base is in scope. |
| `CHR_Clash.rar` | RAR, 47,873,174 bytes; 54 files | Body OBJ, Marmoset scene, reference JPG, 44 DDS and seven TGA textures. |
| `clash new.avif` | AVIF, 45,272 bytes | Newer appearance reference; not the selected body target. |
| `clash old.jpg` | JPEG, 1,107,281 bytes | Original bald Clash reference; relevant appearance guide. |
| `Rework_Clash_Shield.blend` | Blender scene, 5,335,807 bytes | Selected shield geometry and incomplete material setup. |
| `Braum.wad/` | **Directory**, 1,843 hash-named files | Extracted main champion archive, including many other skins and shared dependencies. It is not itself a WAD archive. |

The extracted directory contains 1,298 TEX, 198 SCB, 154 ANM, 91 BIN, 34 SKL, 34 SKN, 18 BNK, 13 DDS and three extensionless files. SCB static particle meshes are essential additional formats. One extensionless entry resolves to `data/final/champions/braum.wad.subchunktoc`; the other two remain unidentified. Do not package these extraction/container implementation records as custom assets.

The original project has 1,849 files totaling 291,524,517 bytes, excluding archive members counted a second time and excluding audit outputs. The RAR contains additional `.obj`, `.tbscene` and `.tga` formats. WEM media is embedded inside BNK/WPK containers; its absence as loose files is expected.

Additional relevant files found outside P:

| Absolute path | Finding |
|---|---|
| `C:\Users\etqdo\Downloads\wadtools-0.5.7-windows-x64\Braum.wad.client` | 92,800,510-byte main archive; independent extraction matches all supplied main entries. Retain as provenance evidence. |
| `C:\Riot Games\League of Legends\Game\DATA\FINAL\Champions\Braum.wad.client` | **Absent at inspection.** Restore a pristine current game copy through the normal game repair/update workflow before testing. Do not assume the Downloads copy is the current patch. |
| `C:\Riot Games\League of Legends\Game\DATA\FINAL\Champions\Braum.en_US.wad.client` | Localized champion archive exists. English-only voice work must target this locale deliberately. |

The 50 unresolved names are listed by exact hash and original type in appendix 8. Nothing is renamed or guessed to conceal incomplete hash coverage. League WAD paths are hashed; the public hash lists plus strings recovered from actual BIN references enabled exact matches.[^2]

## Actual Braum construction

### Core files and material binding

In the following table, supplied filenames live under `P\Braum.wad\`. The right-hand column is the actual WAD-relative path, not a proposed name.

| Role / input alias | Supplied filename | Actual WAD-relative path |
|---|---|---|
| **B0** skin configuration | `eb9d53354a504663.bin` | `data/characters/braum/skins/skin0.bin` |
| **A0** animation graph | `0b01eaec2c944f55.bin` | `data/characters/braum/animations/skin0.bin` |
| Gameplay records — protected | `52d36b20890112f7.bin` | `data/characters/braum/braum.bin` |
| Skin root | `e63e7a9cbb51a42f.bin` | `data/characters/braum/skins/root.bin` |
| **M0** body/shield/Poro mesh | `fbf88fcfc8ec8dc4.skn` | `assets/characters/braum/skins/base/braum_base.skn` |
| **S0** skeleton | `9b8248658ce51711.skl` | `assets/characters/braum/skins/base/braum_base.skl` |
| Base color | `55b5d46776387920.tex` | `assets/characters/braum/skins/base/braum_base_tx_cm.tex` |
| Gloss | `9b701e6000aefb27.tex` | `assets/characters/braum/skins/base/braum_base_tx_gm.tex` |
| Poro color | `47f822652c3d3374.tex` | `assets/characters/braum/skins/base/braum_base_poro_tx_cm.tex` |
| Reflection cube | `36c71f4a03654e59.dds` | `assets/characters/braum/skins/base/braum_base_cubemap.dds` |
| Loading screen | `74d1db81b910ba99.tex` | `assets/characters/braum/skins/base/braumloadscreen.tex` |

`Characters/Braum/Skins/Skin0` binds these through `SkinMeshProperties`. It uses a legacy implicit material setup: `Texture`, `GlossTexture`, reflection map and related parameters. **There is no explicit named base `StaticMaterialDef` or shader file path in this record.** The default shader is selected by the engine; claiming a specific standalone base shader file from these inputs would be speculation. Other supplied skins contain explicit materials and can provide controlled experiments, not proof of base compatibility.

The original skin scale is approximately **1.15**, self illumination **0.7**, and `OverrideBoundingBox` is `[180,180,180]`. These are visual configuration values, not collision dimensions. Retain them initially; inspect culling if the new shield exceeds the original visual envelope. Never change gameplay radius, hitboxes or statistics to compensate for visual geometry.

The SKN is version **4.1**, with 8,837 vertices, 13,392 triangles, 52-byte vertices and two submeshes. `Braum` contains 8,068 vertices and 12,374 triangles, including the body and shield under the same original material. `Poro` contains 769 vertices and 1,018 triangles. B0 initially hides `Poro` and provides its separate texture override. Joke animation events reveal the Poro; removing it or repurposing that submesh name can create later animation defects.

### Skeleton and shield behavior

S0 contains **97 joints and a 76-entry influence palette**. Original vertices have up to four influences and normalized weights. Preserve all joints, including non-weighted buff bones, helper bones, snap bones and Poro bones. Complete names and parents are in appendix 2; native transforms are retained in `evidence/braum_skeleton.json`.

The body chain includes `Root → Spine1 → Spine2 → Spine3 → Neck → Head`, with clavicles, upper arms, forearms, hands, fingers and twist helpers. The pelvis branches from Root; legs include both upper and lower knee helpers before feet and toes. That structure differs materially from a conventional realistic human rig.

The shield is an independent animated branch: **`Origin` joint 67 → `Shield` joint 68**. `Snap_Shield2LHand` is a child of `L_Hand`; `Snap_Shield2RHand` is a child of `R_Hand`. Their names support a snapping role, but the supplied data does not establish every runtime constraint. Do not replace this system with a simple left-hand parent. All 59 inspected base animation files include a Shield track.

`Shield` also parents `Cstm_Buffbone_L_Shield_Eye`, `Cstm_Buffbone_R_Shield_Eye` and `Cstm_Buffbone_Shield_Gem`. B0 binds three idle particle keys to those bones. Remap their visual offsets/effects to shield electronics later; preserve the bones. Q, E and R also have separate particle shield geometry, so replacing only M0 leaves some original shield imagery in abilities.

### Animation coverage

A0 has **79 clip records and 1,806 blend-table records**. Its atomic resources resolve to the 59 supplied ANM files listed in appendix 3. Important actual files under `assets/characters/braum/skins/base/animations/` include:

| Behavior | Actual files / graph behavior |
|---|---|
| Idle | `braum_idle_in.anm`, `braum_idle_01_in.anm`, `braum_idle_01_loop.anm`; retain B0’s `Idle_shield` default token even though no same-name explicit clip was found. |
| Locomotion | `braum_run_02.anm`, `braum_run_slow.anm`, `braum_run_haste_01.anm`. No distinct walk ANM was identified; use the actual Run graph and its slow/haste conditions. |
| Attacks | `braum_attack_01.anm`, `braum_attack_02.anm`, `braum_attack_03.anm`, turret, critical and passive attack variants; exact spellings in appendix. |
| Q / W / R | `braum_spell1.anm`, `braum_spell2.anm`, `braum_spell4.anm`. |
| E | Directional `braum_spell3_idle…`, `braum_spell3_run…`, leap and punch variants. Idle covers ±180°, ±90° and 0°; running covers ±179°, ±90° and 0°. |
| Recall / channel | Recall, recall return, channel in/loop/windup clips, as bound in A0. |
| Other | Death, laugh, taunt, dance windup/loop, joke and joke2 sequences. |

E uses angle-driven blends through `LookAtSpellTargetAngleParametricUpdater` and conditional attack selection. One counterintuitive stock binding maps `Spell3_Punch045` to `braum_spell3_punch0-45.anm`, with the reciprocal mapping also present. Preserve the supplied mapping. Do not “correct” stock names based on intuition. Some stock animation tracks have no matching joint hash in the supplied skeleton; preserve this baseline unless a specific runtime defect establishes otherwise.

## Clash body suitability and preparation

`CHR_Clash.rar` contains `CHR_Clash/CHR_Clash.obj`, `CHR_Clash/CHR_Clash.tbscene`, a reference JPG and `CHR_Clash/Textures/…`. The OBJ exporter comment identifies a 3ds Max Wavefront export dated 2018. There is no supplied FBX, MTL, armature, skin weighting or animation. The Marmoset scene is a material/reference aid, not a League rig.

The raw OBJ has **21,324 positions, 21,255 UV coordinates, 26,495 normals and 41,175 face statements**. Blender’s inspection import yields 41,173 triangles; the two-face discrepancy must be reviewed as a degeneracy/import issue during preparation. There are 11 OBJ groups: `hjhjh_2`, `hjhjh_3`, `hjhjh_4`, `hjhjh_16`, `Object001`, `Object002`, `Object004`, `Object005`, `Object006`, `Object007` and `Object009`. These are not trustworthy semantic labels. The default inspection import produces one mesh with no materials; group reconstruction and texture assignment need deliberate work.

The source is Y-up by its coordinate distribution: approximate height 179.624, width 111.092 and depth 50.491 in unspecified OBJ units. Blender’s default OBJ axis conversion makes that height Z-up. Centimeters are plausible, but not established metadata. Match feet, pelvis, shoulders, neck and hand landmarks to the imported Braum skeleton; do not blindly apply a guessed meter conversion or bake B0’s 1.15 scale twice.

UVs span approximately U −0.9902 to 1.9863 and V 0 to 1.0001. Tiling, overlap and group-specific textures require material reconstruction followed by baking to a controlled atlas. Do not flatten the entire OBJ onto one of its source diffuse images.

The 44 DDS files include diffuse, normal, specular, mask and detail-normal maps for accessories, arms, badge, head, legs, mouth, pouches, straps and torso. Seven TGA files include eyes and six `Color_Textures3` body/gear color maps. The supplied `.tbscene` specifically binds the torso color to `Textures/Color_Textures3/CHR_Clash_Torso_DiffuseMap.tga`, not simply the similarly named torso DDS.

The readable `body_mainq` material block uses `CHR_Clash_Torso_SpecularMap.dds` channel 0 for microsurface, channel 1 for specular and channel 2 for occlusion. It uses the mask’s RGB channels for different tiled detail normals. These are source-scene channel assignments, **not a generic metallic/roughness/AO convention**. The scene records color-space flags as well; preserve their evidence and evaluate the reconstructed result before baking. A referenced custom shader, `detail_normal_rgba.frag`, is absent. Reconstruct or bake those details with available Blender nodes; this shader cannot be imported into League as a Marmoset shader.

The source is suitable as a **modeling and texture starting point**. It is unsuitable for direct League export. Body plus shield currently total approximately **53,429 triangles**, about four times the original whole Braum mesh. Use 15,000–25,000 total body-and-shield triangles as an initial art/performance target, not a claimed engine limit. Preserve the face, fingers, silhouette and shield edges while reducing hidden surfaces and redundant tessellation. Inspect final exported vertex count after UV and normal splits.

## Braum ↔ Clash rigging strategy

**Keep Braum’s animation system; adapt Clash’s mesh.** No animation retargeting from Rainbow Six is possible from the supplied inputs because none is supplied. Import S0/M0 in Aventurine’s native orientation mode, retain native bind metadata, and establish a reproducible import/export preset before reshaping the character.

| Region | Recommended adaptation and verification |
|---|---|
| Shoulders / upper arms | Broaden and raise the shoulder silhouette enough to meet Braum’s clavicles and arm reach. Use armor and sleeves to disguise the proportion change. Test overhead R, wide attack swings and E punches before refining textures. |
| Elbows / wrists / hands | Position elbow loops around the actual joint pivots, retain twist influence where useful, reshape palms to Braum’s grip and manually weight fingers. Test both shield snap poses and extreme wrist rotation. |
| Torso / neck / head | Extend torso and reposition collar/vest against the existing spine chain. Preserve the bald head silhouette; manually correct neck, jaw and collar weights. Do not stretch the face through torso weight transfer. |
| Pelvis / hips | Align the pelvis and crotch loops to the native hip motion; reshape tactical belt and pouches to avoid thigh penetration. Rigid pouches should follow a suitable bone or small stable influence set. |
| Knees / legs / feet | Account for Braum’s two knee helper segments. Maintain bending loops, plant boots on the original ground plane, and inspect slow/haste running, leaps, recall and death for skating and collapsing kneepads. |
| Equipment | Weight armor plates, pouches and radio components deliberately. Use restrained deformation; no new cloth simulation or extra dynamic skeleton is required. |
| Shield | Rigid weight 1.0 to `Shield` for frame, glass and attached CCE hardware. Align handles to actual animated hand poses rather than moving the Shield joint to fit the imported prop. |

Transfer weights from the original body only as a seed. Exclude the original shield and Poro from nearest-surface transfer. Normalize, remove negligible influences and enforce at most four influences per exported vertex, then manually correct joints. Automatic weights alone are not an acceptable final rig.

**Exporter contract:** the inspected Aventurine 3.1.5 code writes SKN 1.1 and compacts weighted joints into a new sorted influence palette. It enforces 65,535 exported vertices, 32 submeshes/materials and 256 weighted palette entries. These are the inspected exporter’s constraints, not an exhaustive statement of every modern engine limit. The input SKN being 4.1 does not automatically make an output 1.1 invalid; a vanilla round-trip and in-game test must establish acceptance.[^3]

Export the new SKN **with its paired SKL**. Compare all 97 joint names, order, parent relationships and native bind transforms against S0. Allow only the corresponding palette representation to differ unless a separately reviewed requirement exists. A byte-identical original SKL may be reused only if the exported SKN indices demonstrably address its original palette correctly. Do not delete helper bones to make a warning disappear.

Do not modify individual ANMs in the initial build. Correct geometry and weights first. If a specific motion remains unacceptable, record the exact clip, frame interval, defect and proposed cosmetic correction. An animation exception requires Very High reasoning, full transition tests, preserved duration/events and proof that it does not change gameplay timing. Wholesale animation replacement is not recommended.

## CCE shield implementation

The shield blend contains seven mesh objects, no armature and no vertex groups. It has **13,868 vertices and 12,256 triangles**. `mesh_14.001` is the main parent; its world-space bounding box is approximately 1.088 wide, 0.506 deep and 2.382 high in a metric scene with unit scale 1. Child objects carry negative scales and inherited rotations. Applying the parent/child world transform correctly is necessary to avoid mirrored normals and double rotations.

| Object | Vertices / triangles | Assigned material |
|---|---|---|
| `mesh_13.001` | 5,123 / 4,750 | `Material.015` |
| `mesh_14.001` | 7,293 / 5,874 | `Material.003` |
| `mesh_15.001` | 52 / 48 | None |
| `mesh_16` | 999 / 1,060 | None |
| `mesh_21.001` | 388 / 514 | `Material.016` |
| `mesh_22.001` | 9 / 8 | `Material.017`, no nodes |
| `mesh_23.001` | 4 / 2 | `Material.018` |

The file contains 41 material and 70 image datablocks, mostly leftovers. Only four images are packed, and those are unrelated hair maps. The active shield materials reference these missing source files:

- `000002177C0DE0C0.png`
- `00000216131DB050.png`
- `0000021700354BA0.png`

`00000216131DB050.png.001` is a duplicate datablock, with `//00000216131DB050.png` as its path. The other references point to an unavailable `C:\Users\Draft\AppData\Roaming\Ninja Ripper\…\frame_1\` location. Exact stored paths are retained in `evidence/shield_scene.json`. Recover those three source files if available. **Recommended default if they remain unavailable: author replacement shield textures from the supplied geometry and references.** Do not request all unused image datablocks or claim those files are embedded.

The shield’s UV layers `uv_0` through `uv_10` include extreme tiled values and NaNs in `uv_9`. Choose or rebuild a finite UV set after identifying geometry; the numerically plausible `uv_2` is only a candidate, not a validated final layout. Remove unused layers in the future working copy and ensure the exported single UV set is intentional.

### Transparent ballistic viewport

Separate frame and viewport faces into distinct export submeshes/materials. The source does not establish a finished dedicated glass component simply through its material names. Use the read-only geometry diagnostic in `evidence/shield_geometry_front.png` to locate surfaces, then inspect both sides and handles in Blender during preparation.

An alpha channel in a texture alone does **not** establish transparency under B0’s implicit opaque material setup. A supplied experimental donor is `data/characters/braum/skins/skin54.bin` (`07f65b37fb75e834.bin`), material `Characters/Braum/Skins/Skin54/Materials/Braum_Skin54_Ice2_inst`, referencing logical shader `Shaders/SkinnedMesh/HKG_MatCap_Diff_Mask_Alpha`. Its blend state is enabled with factors 6/7 and a four-weight skinning switch. This proves a relevant alpha-capable configuration exists in supplied data; it does not prove a direct transplant works in base Braum.

Build an early isolated glass test. Copy only required material/shader settings into a new material entry and bind the viewport by exact submesh name. Do not copy the donor’s unrelated dynamic-material conditions wholesale. The engine/global shader implementation is an external dependency; no new custom shader compilation is planned.

Test visibility from front/back and oblique angles, alpha sorting against the body and arcs, depth writes, fog/stealth transitions and ground telegraphs behind the shield. Prefer one simple pane with restrained tint/reflection. Physically accurate refraction, multi-layer thick glass and full Rainbow Six renderer fidelity are not promised. If a stable skinned translucent material cannot be established, use an open aperture with a subtle modeled rim or a restrained visual glass approximation. Never fill the entire viewport with an opaque white electrical plane.

Braum E remains the same directional defensive ability. Keep its distinct first-block, sustained active, subsequent-block and expiration states. Add arcs along shield edges and CCE emitters while preserving the visible outline and facing direction. Do not add a deployable shield, continuous taser beam, new collision surface or new gameplay interaction.

## Ability VFX plan

B0’s `Characters/Braum/Skins/Skin0/Resources` maps effect keys to definitions in **13 actual owner BINs**. Appendix 1 gives the complete long `braum_multi_skins_…bin` paths; appendix 4 gives every key, definition, owner hash and dependency. Short owner hashes below are exact supplied identifiers and can be looked up without guessing a filename.

The recommended architecture is to clone only changed VFX definitions to new logical entries inside the modified skin0 BIN, preserve existing effect keys, and point those base resolver bindings at the clones. Rewire any cloned child references explicitly. Keep original linked BINs for unchanged resources. This avoids changing shared multi-skin definitions and avoids relying on unverified duplicate-entry precedence.

| Area | Actual resolver family / dependencies | Proposed cosmetic change | Difficulty and reason |
|---|---|---|---|
| Passive | `Braum_P_…` stack1/2/3/3_warning/4, stun, debuff timers, cooldown-hit and Poro-mustache effects; exact spelling in appendix | Electrical stack marks, brief white/blue discharge on stun, restrained cooldown indication | **MODERATE.** Preserve four-stack progression, near-stun warning, stun recognition and cooldown state. A static “electric aura” would conceal state changes. |
| Q | `Braum_Q_mis`, hit/monster-hit systems and `Braum_Q_Shield_base_cas`; SCB projectile/shield geometry and trails/textures | Compact electrical projectile and discharge, with original travel/readability envelope | **MODERATE.** Geometry, trail and hit systems need coordinated changes. A continuous hitscan-looking beam is **NOT RECOMMENDED** because Q remains a traveling projectile. |
| W | Cast, `Braum_W_Dash_Land`, landing indicator and shield-buff family | Small tactical pulse and restrained electrical landing accent | **MODERATE** for the complete conversion; tint-only is **EASY**. Preserve ally landing and buff communication; avoid making W resemble an offensive stun. |
| E | `Braum_E_Shield_cas`, block-BA/block-spell variants, self effect, dummy timer, first-block/end, shield-end and speed buff | Energized CCE outline, controlled white/blue arcs, differentiated activation/first block/impact/expiry | **DIFFICULT.** Multiple state transitions, independently animated shield, attachment alignment and transparency interact. Persistent loop cleanup must work on death and cancellation. |
| R | Missile/small missile/rock child, first/small knockup, endcaps, PBAOE cast, slow/freeze, team telegraphs, zone/pulse sound and shield-cast systems | Electrical ground shockwave with retained width, travel, endpoints and lingering-zone clarity | **HIGH RISK** for full geometry replacement. Retinting alone is easier but leaves ice meshes. Ground mesh animation, child effects and team-specific telegraphs must remain synchronized. |
| Attacks | `Braum_BA_Hit_01/02/03`, critical hit and trail families | Restrained shield impact sparks, short electrical accents where appropriate | **EASY–MODERATE.** Preserve attack readability and passive-proc distinction; inspect animation-triggered trails. |
| Idle / recall / emotes | Shield gem/eyes, recall and joke systems, contextual action data | Replace shield idle glow with electronics; retain recall/joke behavior initially | **MODERATE.** Avoid persistent particles at old shield-eye positions and preserve Poro visibility events. |

The three VFX definitions embedded directly in B0 are `Braum_E_Shield_cas`, `Braum_Q_Shield_base_cas` and `Braum_R_shield_Base_cas` families. Most remaining definitions live elsewhere. Some base effects legitimately reference `skin10` textures. A texture’s directory does not establish the selected skin slot; changing it globally could affect multiple skins.

R has an important hidden dependency: `assets/characters/braum/skins/base/particles/braum_base_r_ice_shard.skn`, `.skl` and `.anm`, supplied as `4e39c2b7f8fb2101.skn`, `8d71893c571f5f5d.skl` and `82c69c58b966af73.anm`. Recoloring sprites will not remove this animated ice geometry. There are also SCB static particle meshes. For the first electrical R, retain the tested movement envelope and progressively substitute low-profile electrical ground visuals; do not remove the lingering zone cue.

Preserve ally/enemy telegraph differentiation, endpoint placement, visibility duration and impact hierarchy. Avoid global shared texture overwrites; give custom textures new verified WAD paths. Do not alter the protected champion/spell BIN, missile behavior, damage, hitboxes, effect trigger times or animation event timing. VFX rendering changes must stay aligned with the existing gameplay.

## Audio plan

Base Braum exposes **53 SFX events and 41 VO events** through B0. All 94 names were matched to supplied Wwise event IDs. Wwise event hashing here is lowercase **FNV-1**, distinct from BIN’s FNV-1a and WAD’s XXH64. The archive path segment `wwise2016` is not evidence that Wwise 2016 should be installed. The inspected banks have **BKHD version 145**.

| Container | Actual path / supplied identifier | Contents and replacement scope |
|---|---|---|
| SFX media bank | `assets/sounds/wwise2016/sfx/characters/braum/skins/base/braum_base_sfx_audio.bnk` — `668ac17b89a8d8ea.bnk` | Bank ID 3580963463; DIDX/DATA with **114 media**. Preferred unit for selected SFX replacement. |
| SFX events bank | Same directory, `braum_base_sfx_events.bnk` — `6a0cd1a55c7df583.bnk` | Bank ID 924561672; 368 HIRC objects, including 53 events. Preserve when media-only replacement is sufficient. |
| Base VO events | `assets/sounds/wwise2016/vo/en_us/characters/braum/skins/base/braum_base_vo_events.bnk` — `17802985c2cae524.bnk` | Localized WAD; 41 events and their container graph. |
| Base VO audio bank | Same VO directory, `braum_base_vo_audio.bnk` — `1edf235828b09246.bnk` | **48 bytes, BKHD only. No voice samples.** Replacing it alone cannot replace the dialogue. |
| Base VO media | Same VO directory, `braum_base_vo_audio.wpk` — `4826a53ff12ced20.wpk` | WPK `r3d2`, version 1, **115 media entries**. Actual localized voice media. |

All 114 reachable SFX media and all 115 reachable VO media are present. Every inspected payload is **mono, 44,100 Hz Wwise Vorbis**, RIFF format tag `0xffff`. The event traversal identifies possible media variants; runtime switches, randomness and contextual conditions determine which plays. Twenty-one SFX media IDs and seven VO media IDs are shared across multiple events. Replacing shared media affects every listed event, not just the event used to find it.[^4]

One graph edge remains unresolved: `Play_sfx_Braum_BraumRWrapper_OnHit`, event **4008465767**, references action **792732449**, which targets object **222662794**. That object is absent from every supplied BNK. It may be external or stale. Leave the event untouched and identify its audible behavior from a clean baseline/global bank inspection if that exact cue becomes necessary. This gap does not prevent replacing the separately resolved R cast and pulse cues.

| Candidate cue | Confirmed event ID / media example | Recommended scope |
|---|---|---|
| Q discharge | `Play_sfx_Braum_BraumQ_OnCast` **4193070101** → media 22215941, 40941018, 41688918, 45474400, 47820709 | **MODERATE.** Two listed media also serve attacks; use the shared-media appendix before selecting samples. |
| Q impact | `Play_sfx_Braum_BraumQMissile_hit` **656004614** → 103689118, 680861900, 1071447244 | **MODERATE.** Audition variants, preserve impact duration and loudness. |
| Shield activation | `Play_sfx_Braum_BraumEShieldBuff_OnBuffActivate` **2600776008** → 541689440, 557873384 | **MODERATE.** Electrical charge/loop must respect original stop/deactivate behavior. |
| Large shield block | `Play_sfx_Braum_BraumEShieldBuff_block_large` **1065834682** → 169392210, 278315751, 491993041 | **MODERATE.** Retain distinction from small/layered block cues. |
| R cast | `Play_sfx_Braum_BraumRWrapper_OnCast` **1869821925** → 309351640 | **MODERATE.** Short electrical shockwave cue; retain envelope and spatial behavior. |
| Passive-related attack hit | `Play_sfx_Braum_BraumBasicAttackPassiveOverride_hit` **3139578176** → 510145146, 786873024, 1041470451 | **MODERATE.** Verify actual trigger by audition and gameplay; do not label it the universal fourth-stack stun solely from its name. |
| General attacks / equipment | Attack cast/hit, shield override, critical and tower events in appendix | **MODERATE–DIFFICULT** due to shared variants. No dedicated equipment-footstep event was established in the base list; avoid global footstep replacement. |
| Full voice-over | 41 localized events, 115 media and contextual selection | **HIGH RISK / optional.** Requires a coherent recording set and contextual mapping; preserve spatial modes and special interaction semantics. |

Use newly recorded or otherwise available Clash-inspired electricity and voice sources; no Clash audio was supplied and none is assumed available. Recommended audio authoring masters are lossless PCM WAV, optionally 24-bit/48 kHz for editing. For this exact replacement set, encode delivery WEM to the observed **mono 44.1 kHz** configuration unless an individually tested requirement justifies a change. Preserve useful duration, leading silence, gain and loop metadata. Renaming WAV/OGG/MP3 to `.wem` does not create compatible Wwise media.

Quartz’s SoundBanks functionality and `bnk-extract-GUI` are candidates for extraction, replacement and repacking. They are sufficient for bank operations if they pass a version-145 no-op round-trip and a single-sample replacement test. **Compatible WEM encoding is a separate requirement.** Do not infer encoder compatibility from a successful bank parse. Wwise authoring is conditional if the selected tooling cannot produce accepted media; its required version must be established from the encoding workflow, not from the directory name. `wwiser` is useful for event inspection and does not edit banks.[^5]

Retain event IDs, play/stop actions, switches, random containers, attenuation and 2D/3D behavior whenever replacing only sound content. Preserve W activation/deactivation stop events, E shutdown and death/cancellation cleanup. If a shared media replacement must affect only one event, cloning containers/IDs becomes a separate difficult task; defer that complexity for the first release.

## `.fantome` architecture

The final artifact must be **`Braum_Clash.fantome`**. Use a conventional single-layer ZIP-based package with `META/info.json` and WAD-targeted replacements. Do not substitute `.modpkg`, introduce optional-layer extensions, or package the entire project. The established format supports a directory named after a target WAD or a packed replacement WAD containing only changed entries.[^6]

### Proposed exact output namespace

These names are design choices for future assets, clearly distinct from discovered vanilla names:

| Alias | Exact future path relative to P |
|---|---|
| **PKG** | `build/package/` |
| **MAIN** | `build/package/WAD/Braum.wad.client/` |
| **BASE** | `build/package/WAD/Braum.wad.client/assets/characters/braum/skins/base/braum_clash/` |
| **OUTBIN** | `build/package/WAD/Braum.wad.client/data/characters/braum/skins/skin0.bin` |
| **VOICE** | `build/package/WAD/Braum.en_US.wad.client/assets/sounds/wwise2016/vo/en_us/characters/braum/skins/base/` |

The intended package tree is:

```text
Braum_Clash.fantome
├── META/
│   └── info.json
└── WAD/
    ├── Braum.wad.client/
    │   ├── data/characters/braum/skins/skin0.bin
    │   └── assets/
    │       ├── characters/braum/skins/base/braum_clash/
    │       │   ├── braum_clash.skn
    │       │   ├── braum_clash.skl
    │       │   ├── body.tex
    │       │   ├── body_gloss.tex
    │       │   ├── shield_frame.tex
    │       │   ├── shield_glass.tex
    │       │   ├── electric_arcs.tex
    │       │   └── ground_pulse.tex
    │       └── sounds/wwise2016/sfx/characters/braum/skins/base/
    │           └── braum_base_sfx_audio.bnk
    └── Braum.en_US.wad.client/        [only if VO is implemented]
        └── assets/sounds/wwise2016/vo/en_us/characters/braum/skins/base/
            └── braum_base_vo_audio.wpk
```

Include only assets actually used by the final build; unused glass/future VFX files must be omitted. Conditional additional particle outputs are specified in Stage 7. Metadata `image.png` is optional and not required for the cosmetic result. A proposed metadata record is:

```json
{
  "Name": "Braum - Clash",
  "Author": "Ethan",
  "Version": "1.0.0",
  "Description": "Base Braum cosmetic conversion using Clash-inspired tactical equipment, CCE shield and electrical effects."
}
```

OUTBIN points `SimpleSkin` and `Skeleton` to the new matched files in BASE. It binds the new texture/material entries and custom VFX while retaining all gameplay-facing keys, animation graph links and unchanged dependencies. `Braum`, `ShieldFrame`, `ShieldGlass` and retained `Poro` are the proposed export submesh names. Material overrides must match those names exactly. Preserve Poro’s original texture reference through the base game dependency.

### Path, hash and override rules

WAD lookup uses the canonical game path’s XXH64 identity. BIN entry/field identity uses separate 32-bit hashing. Use forward slashes and consistent lowercase game paths when hashing; preserve known logical references through a format-aware writer. Verify each packaged entry hash and every new reference rather than relying on the visual folder name.

For an existing path, the mod entry replaces the corresponding base archive entry. For a new path, the mod adds an entry that must be referenced by OUTBIN or a reachable custom resource. New textures dropped into a folder with no updated reference will never appear. A replacement `skin0.bin` is a whole entry: preserve unknown and unrelated fields through a lossless parse/write workflow, not a hand-written minimal imitation.

The very long shared BIN names can exceed normal Windows path-component limits. Read them by supplied hash filenames and retain their game-path mapping; avoid trying to materialize every long name as a Windows file. This design does not modify those shared owner files. Modern packers may support raw 16-hex-hash entries, but **do not assume every existing manager recognizes `hash.tex` as a precomputed hash**. Prefer readable verified paths for this package or use a tested WAD writer when a raw-hash replacement is unavoidable.[^7]

Do not include the source RAR/BLEND/OBJ/TGA collection, addon ZIP, audit directory, all 1,843 extracted files, untouched ANMs, untouched root/gameplay BINs, unrelated skins, `*.wad.subchunktoc`, unknown extraction entries, development renders, shader caches, loose WAV masters or unused banks. A modified audio bank or WPK contains its needed unchanged media internally because that container is the replacement unit; this does not justify shipping every champion bank.

No changes to `RAW/` are needed. The ZIP root must immediately contain `META/` and `WAD/`, without an extra `Braum_Clash/` wrapper. File extension must be `.fantome`, not `.fantome.zip`. Validate archive CRCs, duplicate case-insensitive paths, allowed WAD targets, reference closure, SHA-256 manifest and an import/reimport using the already-owned manager. That manager’s exact implementation was not identified; the conventional layout is the recommended baseline, and its acceptance remains a test gate.
