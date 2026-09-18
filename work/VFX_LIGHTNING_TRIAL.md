# Clash lightning v1 — runtime candidate

The user accepted the model in actual gameplay on September 14: "The model looks good", with colors slightly too dark. This supersedes the historical pending model gate. Geometry, the 67 torso seam corrections, cuff, shield, rig and exports remain closed.

## Build and rollback

- Core: `build/lightning_v1/core/Braum_Clash_Core_v1.fantome`
- E/Q isolation: `build/lightning_v1/eq/Braum_Clash_Eq_v1.fantome`
- E isolation: `build/lightning_v1/e/Braum_Clash_E_v1.fantome`
- Brightness only: `build/lightning_v1/brightness/Braum_Clash_Brightness_v1.fantome`
- Gameplay-accepted rollback: `work/checkpoints/model_runtime_accepted/Braum_Clash_Model_Trial.fantome` (byte-identical to the original build, SHA-256 `f3b055eff6f590f9a8a265aa1a878d4f2f20abf77d52049d495538945f868554`).
- Accepted body scene: `work/scenes/clash_braum_body_atlas_accepted.blend`; packaged shield source: `work/scenes/clash_braum_shield_material_trial.blend`. Neither changed.

Only enable one Clash package. The new manager profile is `Clash Lightning v1`; the existing `Clash Braum Runtime Trial` profile remains the rollback selection.

## Brightness

Two diffuse maps only: body and shield frame. In normalized encoded RGB, `rgb *= 1 + .18 * (1 - max(rgb))`. This keeps RGB ratios until 8-bit rounding, preserves black and white, lifts dark/middle values modestly, and tapers the change near highlights. Maximum channel increase is 11/255 for body, 10/255 for shield. Alpha is byte-identical. New PNGs: `work/textures/brightness_v1/{body,shield_frame}.png`. BC3 TEX/mips rebuilt; mip0/2/4 decode successfully. Gloss and normal binding unchanged. The textures are numerically brighter; gameplay acceptance remains separate.

## VFX mapping and implementation

The existing complete map is `audit/evidence/base_vfx_dependencies.json`; exact selected systems/emitters/owner hashes are in `validation/lightning_v1_build.json` and the explicit `SPELLS` allowlist in `work/scripts/build_lightning_trial.py`.

| Spell | Changed components | Cloned systems |
|---|---|---:|
| E | Sustain enchant layers/line, BA and spell block flashes, block splash, first block, expiration sparks | 9 |
| Q | Two travel trails and spark, champion and monster impact accents | 3 |
| R | Main/small rupture line, PBAOE cast line, first knockup lightning flash | 4 |
| W | Arrival line and protection sparkle | 2 |

24 selected emitters across 18 cloned definitions. Owner BINs: `eb9d53354a504663` (base skin), `2dc39c165f3aa923`, `b8d6f27624ae797b`, `f2ef4463d62600e6`. New entries use `Characters/Braum/Skins/Skin0/Particles/Clash_v1_*`. Original effect keys resolve to clones; original shared files are never packaged or changed. Unchanged child references continue to their native resources. No clone has child rewrites because this pass changes only selected emitter texture/color fields.

The supplied single-frame lightning trail `d840318cf56171b6.tex` is copied byte-for-byte to `assets/characters/braum/skins/base/braum_clash/lightning_trail.tex`. It was visually inspected against a dark background. Selected color curves retain their peak value and alpha, with RGB ratios `.60/.78/1.0` for steel-blue electrical energy tied to the armor. Native envelope/intensity differences remain. Near-white textured cores support visibility; this is an initial shared language, not a completed storm conversion.

The original 2x2 random sprite sampling on E expiration and W sparkle is removed for the new single-frame texture. The initial generator correctly stopped at that mismatch; its partial output is preserved at `build/lightning_v1_aborted_atlas_guard`. No failed package was installed. No particle count, rate, lifetime, scale, orientation, attachment, visibility, gameplay, animation, sound or telegraph changes.

## Validation and remaining visual work

All four archives pass ZIP integrity, RitoBin candidate byte-stable roundtrip, manager backend import/export/reimport and independent wadtools extraction with exact path hashes and payload byte identity. All four source owner BINs pass byte-identical no-op conversion. Original skin entries are exact except the selected resolver targets; model SKN/SKL bytes are exact. Per-emitter guards prove unchanged fields outside texture/RGB/static-atlas sampling. No geometry validation was rerun because geometry and rig bytes did not change.

Reports: `validation/lightning_v1_build.json`, `validation/lightning_v1_build_logs.json`, `validation/lightning_v1_validation.json`. The build report binds package/source hashes. Runtime findings will be recorded separately; an offline pass does not accept an effect.

**Runtime attempted, September 14:** core imported/selected alone in `Clash Lightning v1`; loader built the overlay and the game entered Practice Tool with base Braum and one Rakan bot. Custom body/shield and spawn/idle visibly load. Client displayed 26.18; capture at 00:26 shows 139 FPS (one sample, not comparative performance validation). Gameplay input to learn E failed twice with `SendInput sent 0 of 1 events; GetLastError=87`, including after refreshing/activating the target. Further input stopped. No spells were cast, so no VFX or brightness A/B acceptance is claimed. Practice session is left open for manual casting; loader remains running. Evidence/report: `validation/previews/lightning_v1_runtime/practice_spawn.png`, `validation/lightning_v1_runtime.json`. This is an input capability failure, not a package-load failure or a new permission requirement.

Known limitations: R still has native animated ice/ground meshes; Q retains its native projectile mesh; E keeps its original enchant mesh, multiplier masks and legacy material override. E alignment against the custom physical shield especially needs gameplay inspection. Original idle shield-eye/gem particles, passive, basic attacks, audio and recall are unchanged. Do not claim a fully converted lightning kit yet.

## Reproduction

From project root, using the Python path in `work/README.md`:

```powershell
& $taskPython work/scripts/build_lightning_trial.py
& $taskPython work/scripts/validate_lightning_trial.py
```

Builder refuses an existing `build/lightning_v1`; validation refuses an existing stage validation folder. Preserve these checkpoints and choose a new version before iterating. Requirements: Pillow, NumPy and xxhash (the validator also checks the existing `audit/scratch/python_lib` dependency location); installed RitoBin/mod-tools/wadtools paths are explicit in scripts; existing ltk-tex-utils is reused. No ignored cache is authoritative project memory.

## Minimum runtime test

Use base Braum at normal gameplay zoom in Practice Tool. Check idle/running brightness; E activation, sustained orientation, block and expiry; Q travel and target impact; W allied-target arrival/protection; R cast, moving rupture, lingering zone and cleanup. Repeat casts and combos. Record missing/black textures, sprite rectangles, misaligned E shell, excessive glow, disappearance/cleanup and obvious FPS loss. Preserve red/blue ground distinction. Return a short normal-zoom clip showing E front/side/block/expiry and Q/W/R with the package version. The first priority is E sustain alignment and actual visibility of the lightning texture; only refine from that evidence.
