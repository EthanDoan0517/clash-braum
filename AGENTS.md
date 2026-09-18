# Clash Braum — Codex Project Instructions

## Objective and continuation

Deliver an in-game satisfactory Clash skin for Braum with the accepted model, electrical VFX, authentic Clash SFX, and authentic English Clash voice lines. All four are required; historical optional-VO wording is superseded.

Before substantial work, read the current-state block at the top of `audit/BRAUM_CLASH_MASTER_IMPLEMENTATION_PLAN.md` and the current routing section of `work/README.md`. Inspect only relevant source, validation records, and Git history afterward. The master plan is the authoritative status and decision record. Historical next steps are not active instructions. Do not reconstruct or substantially re-plan adequately specified work without contrary repository evidence.

### Default meaning of “continue”

Treat “continue” as authorization to execute the master plan's immediate next action through implementation, proportionate validation and checkpointing. Do not stop at a plan or ask the user to restate recorded decisions. Honor recorded user-input gates: “continue” alone does not supply missing files, gameplay feedback or acceptance. If a gate blocks the next action, report the exact missing input briefly and pursue independent authorized work only when useful; do not repeat unchanged checks or rewrite an unchanged checkpoint.

For a fresh session, use supplied AGENTS instructions; read the disk copy if absent, potentially changed, or being edited. Read only the master plan's current-state section and README's Start here section, ending at the next `##` heading. Use a bounded streaming read (for example, `Get-Content ... | Select-Object -First N`, with N determined from heading locations) rather than large arbitrary line counts. Batch independent reads. Within a session, reuse already-read unchanged context; after truncation, retrieve only the missing relevant section, not the original broad read.

Inspect only the files/functions and evidence needed for the recorded action, using targeted `rg` searches and bounded excerpts. Do not activate planning workflows, audit the whole repository, or reconstruct history on ordinary continuation. Expand inspection only to resolve a concrete missing fact, failure or dependency. Use the existing tools and pipeline; add no continuation infrastructure.

Finish each substantive work unit with one concise master-plan checkpoint: result, candidate/evidence paths, validation performed or reused with rationale, remaining blocker and one executable next action. Check only the edited documentation when checkpointing. End with the result and required user action, not another proposal to begin.

## Manual installation and gameplay testing only

Do not launch or control League of Legends or cslol-go, install/import mods into the manager, modify its library or profiles, start overlays, or automate gameplay. The user loads and plays every candidate themselves. Historical automation instructions and prior runtime access do not authorize these actions.

When gameplay evidence is needed, provide a clickable link to the existing or newly built `.fantome` file, say what it includes, and give a short normal-zoom observation checklist. Wait for user feedback before dependent fixes or acceptance. Do not rebuild an unchanged candidate merely to hand it off, retry gameplay input, or repeat offline checks while waiting. Do not infer runtime acceptance from packaging or offline import success.

Offline command-line packaging checks in isolated project output directories are allowed when justified by the validation policy below; they must not launch the manager or alter its installed state.

## Resource efficiency and reasoning

Use targeted searches and existing evidence instead of broad exploration, repeated large-file reads, or context reconstruction. Keep full logs on disk and report concise outcomes, failures, and evidence paths. Batch independent reads. Do not add infrastructure or dependencies merely to manage this workflow.

Use Low reasoning for routine edits and checks, Medium for bounded design or debugging, and higher effort only for a specific unresolved architectural, security, or difficult debugging problem. Return to routine effort after resolving it. A new session is not a reason to redo planning.

## Change-dependent validation

Before each check, identify the changed input, affected behavior, and new evidence the check will provide. Reuse passing evidence when its relevant inputs, validator, tool versions, and runtime assumptions remain unchanged. Verify freshness narrowly using recorded hashes or relevant diffs; do not run a broad baseline sweep merely to establish freshness. Since much work may be uncommitted, Git HEAD alone does not identify the validated candidate.

- Documentation only: inspect edited text and links; no builds, renders, or asset tests.
- Brightness/texture changes: check affected texture encoding, alpha, and relevant mip output; request a gameplay comparison.
- Ability VFX: check affected references, protected fields, and candidate-package integrity; request that ability's gameplay behavior and cleanup.
- SFX/VO: check changed media/container integrity and shared-event impact; request playback, timing, and stop behavior.
- Geometry/rig/exporter changes: run affected deformation/export checks; broaden only when the change scope or a failure warrants it.
- Final integrated release candidate: run whole-package checks once and request whole-skin gameplay acceptance. After a fix, rerun affected checks; repeat broader checks only if their evidence was invalidated.

Keep cheap deterministic build guards. Do not rebuild every intermediate package, repeat unchanged source no-ops/backend roundtrips, or run full animation sweeps after unrelated edits. Never skip a necessary correctness check merely to save tokens. Record which prior evidence was reused and why in the master-plan checkpoint.

## Acceptance and bounded retries

Preserve accepted model geometry, torso/cuff/shield work, all 67 seam fixes, rig, and exports. Reopen them only for a demonstrated visible gameplay regression or explicit user request. Judge cosmetic quality at normal gameplay zoom; accepted microscopic cuff issues are closed.

After two attempts on the same defect without useful new evidence, stop repeating the approach. Record attempted fixes, the exact blocker or missing evidence, and one next action. Continue independent authorized work if useful; do not substitute offline testing for missing gameplay feedback. Distinguish completed, awaiting user gameplay, and blocked states. Do not claim the whole skin complete while required VFX, SFX, or VO remain unfinished.

## Implementation and persistent state

For substantial work: select the current unfinished item, inspect necessary context, implement, run proportionate checks, fix introduced regressions, and update the master plan with evidence and the next actionable task.

Maintain one short current-state block at the top of the master plan: accepted work, candidate path, evidence, outstanding defects/scope, blocker, and one immediate next action. Keep prior entries as historical evidence. Keep `work/README.md` as an entry point and reproduction reference, not a competing status log. Future sessions must resume from repository files without chat history. Update the checkpoint before ending substantial work.

## Files and safety

Respect `.gitignore`. Preserve existing user changes. Do not delete or overwrite source assets or valuable Blender files to clean the repository; preserve consequential files when uncertain. Use separate candidate outputs and retain the accepted rollback package.

Do not require ignored caches, Blender backups, generated builds, or scratch data to explain project state when tracked source/configuration can do so. Do not commit credentials, secrets, machine-specific configuration, or unnecessary generated artifacts. Keep concise evidence paths and reproduction instructions in the master plan.
