\# Clash Braum — Codex Project Instructions



\## Project Objective



This repository contains the Clash Braum implementation project.



Before beginning substantial work, read:



1\. `audit/BRAUM\_CLASH\_MASTER\_IMPLEMENTATION\_PLAN.md`

2\. `work/README.md`

3\. Relevant existing code, validation results, and Git history.



The master implementation plan is the primary record of project status,

decisions, completed work, remaining work, and known issues.



Do not regenerate or substantially re-plan work that is already adequately

specified unless repository evidence demonstrates that the existing plan is

incorrect or obsolete.



\## Resource-Efficiency Policy



Optimize for useful implementation completed per unit of Codex usage.



Do not perform broad repository exploration when targeted inspection is

sufficient.



Do not repeatedly reread files or analyze parts of the project that are

already adequately documented.



Prefer:

\- targeted searches

\- relevant source files

\- existing validation results

\- the master implementation plan

\- Git history



over reconstructing project context from scratch.



Keep explanations concise. Spend computation primarily on implementation,

verification, testing, debugging, and difficult reasoning rather than lengthy

status narration.



\## Reasoning Strategy



Use the lowest reasoning effort that can reliably complete the current task.



Routine implementation, mechanical changes, straightforward refactoring,

documentation, validation, and well-specified work should normally use Low

reasoning.



Use Medium reasoning when implementation requires meaningful design or

debugging.



Reserve High or Very High reasoning for:

\- major architectural decisions

\- genuinely ambiguous design problems

\- difficult debugging

\- security-sensitive changes

\- major failures of the existing plan

\- problems where deeper reasoning materially improves correctness



Do not redo expensive planning simply because a new session has started.



\## Implementation Workflow



When a task is already adequately specified in

`audit/BRAUM\_CLASH\_MASTER\_IMPLEMENTATION\_PLAN.md`, prefer implementation over

additional planning.



For substantial tasks:



1\. Determine the relevant unfinished master-plan item.

2\. Inspect only the files/context needed for that task.

3\. Implement the change.

4\. Run appropriate tests and validation.

5\. Fix regressions caused by the change.

6\. Update the master implementation plan.

7\. Record important discoveries, decisions, or blockers.

8\. Clearly identify the next actionable task.



\## Continuity



The repository itself is the persistent project memory.



Future sessions should be able to resume using:



\- `AGENTS.md`

\- `audit/BRAUM\_CLASH\_MASTER\_IMPLEMENTATION\_PLAN.md`

\- `work/README.md`

\- current source files

\- validation results

\- Git history



Do not rely on previous chat history being available.



Before ending substantial work, update the master implementation plan so a

fresh Codex session can continue without reconstructing prior reasoning.



\## Generated and Local-Only Files



Respect `.gitignore`.



Do not require ignored caches, temporary files, Blender backups, generated

build output, or audit scratch data to understand project state when the same

information is available from tracked source/configuration files.



Do not commit credentials, API keys, secrets, machine-specific configuration,

or unnecessary generated artifacts.



\## Safety



Do not delete or overwrite source assets merely to clean the repository.



Treat existing source assets and working Blender files as valuable unless the

master plan or repository structure clearly establishes that they are

generated/reproducible.



When uncertain whether a consequential file can be removed, preserve it.

