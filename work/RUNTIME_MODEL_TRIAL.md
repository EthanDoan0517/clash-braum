# Model-only runtime trial

**2026-09-14 update:** user tested the model in actual gameplay and accepted it: "The model looks good"; only slight darkness reported. The geometry gate is closed. The historical test instructions below document the original package, not an outstanding reason to repeat model development. See [VFX_LIGHTNING_TRIAL.md](VFX_LIGHTNING_TRIAL.md) for the new restrained brightness correction and E/Q/R/W lightning candidates. The original archive is preserved, with a byte-identical rollback under `work/checkpoints/model_runtime_accepted/`. Detailed performance/Poro/opacity measurements were not supplied with the general user acceptance; do not invent them.

Package: `build/model_runtime_trial/Braum_Clash_Model_Trial.fantome`.
SHA-256: `f3b055eff6f590f9a8a265aa1a878d4f2f20abf77d52049d495538945f868554`.

This is an unaccepted test build, not the finished `Braum_Clash.fantome`. The separate accepted offline body checkpoint is `work/scenes/clash_braum_body_atlas_accepted.blend`. Shield coating is still `clash_braum_shield_material_trial.blend`; its eight gameplay previews are acceptable for taking this trial to the runtime gate. No source WAD or manager library was changed.

## What is implemented

- 51,253 triangles /58,314 exported vertices;97 original joints and original native animations.
- Body atlas, authored charcoal shield coating, preserved apertures, body/cuff and all67 torso corrections.
- One `Braum`, one `ShieldFrame` and one original `Poro` submesh.
- BC3 diffuse TEX files with mip chains; low constant gloss replaces the unrelated original gloss texture.
- Only `SkinMeshProperties` changed in skin0: model paths, diffuse/gloss paths and a shield texture override. Original Poro override/visibility, animation graph, event timing, VFX, SFX and VO remain.

## Known material limitation

The accepted Blender body atlas has a tangent normal map. **This runtime trial does not bind it.** The supplied base skin uses an implicit legacy shader with no established normal-map field. This trial establishes whether legacy diffuse/low-gloss rendering is gameplay-acceptable; do not call it equivalent to the Blender normal-mapped preview. Eyelash opacity, texture filtering and reflection response need runtime observation. Explicit material/shader integration is the next correction if their absence is visible at gameplay distance. Current electrical abilities and sounds remain vanilla pending the model gate.

## Test procedure

1. Import this trial through the existing cslol-go manager. Keep an independent vanilla/disabled-mod baseline and select base Braum in a practice session.
2. At normal gameplay zoom, inspect idle and running from different facing directions. Check missing/magenta textures, dark UV lines, shimmer, unexpected gloss, eye/lash opacity, shield aperture and body/shield clipping or disappearing geometry.
3. Cast Q, W, directional E while idle/running and blocking, then R. Test turning, recall/cancel, death/respawn and the Poro joke. Watch animation transitions and shield culling, not only frozen frames.
4. Compare performance to vanilla with the same camera/settings. Geometry is above the preferred target, although exporter limits pass. Reduce only if runtime evidence justifies it; retain face/fingers/cuff/torso corrections.
5. Record game version, manager version, graphics settings, zoom, failing action and screenshot/video timestamp. Save a model-only runtime acceptance report only after these checks pass. Keep this trial and the offline accepted body scene as separate rollback files.

Offline validation: `validation/model_runtime_trial_validation.json` records backend import/export/reimport, independent extraction and all six payload hashes. The installed skin0 BIN, animation graph, base SKN and SKL are byte-identical to supplied sources; this is not proof the entire installation is pristine. `validation/model_runtime_trial_build.json` binds package/tool/texture hashes. Tool source: https://github.com/LeagueToolkit/ltk-tex-utils/releases/tag/v0.3.0.

At handoff, Computer Use inventory returned no native apps (only the in-app browser), and no League game/client process was running. Native UI/runtime testing therefore requires the user or an enabled native Computer Use session. This is an execution capability blocker, not a request for new permission.
