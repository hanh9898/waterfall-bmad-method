# Quickstart (10 minutes)

> 🌐 **English** · [Tiếng Việt](../../vi/tutorials/quickstart.md)
>
> 📘 **Tutorial** — go from zero to your first win: see an agent greet you and produce your first D-02 document for your first feature. About 10 minutes.
>
> 📖 **Hit an unfamiliar term?** (deliverable, D-02, phase gate, traceability, per-feature/shared/dual scope…) → [Concept Glossary](../reference/concept-glossary.md).

## What you'll achieve

By the end you will: install HBC, run the **mandatory Phase 0** (`PI`) — the **first** step that lets HBC understand your project and create the shared deliverables, confirm the agent runs, then produce **your first D-02 Requirements file for a specific feature** — enough to know "yes, I can use HBC". Want the full 4 phases for a feature? Head to [Get Started with HBC (walkthrough)](getting-started-hbc.md) after this.

> ℹ️ **Delivery model:** HBC delivers **incrementally, per-feature**. Each feature goes through 4 phases + TDD, then ships independently. The *sequential, design-first discipline* (design-first, gate each milestone) applies inside a single feature; at the project level, slicing per feature keeps the whole delivery incremental.

## Step 0 — Prerequisites

| You need | Check |
| --- | --- |
| An **AI coding agent** (Claude Code, Cursor, or equivalent) | This is where you'll "type" commands like `PI`, `BA`, `REQ`… — **not** a plain terminal |
| **Node.js** (to run `npx`) | `node -v` |
| **Python 3.10+** (for HBC's validation scripts) | `python --version` |
| **2 companion BMad modules** — `core` + `bmm` (required) | `_bmad/core/` and `_bmad/bmm/` folders exist in the project |
| **Access to the HBC repo** | Try cloning / `ssh -T git@git.hblab.vn` |

## Step 1 — Install

HBC is a custom module, installed via BMad's interactive installer. You need **access to the HBC repo** — a Git URL over SSH (`git@git.hblab.vn:...`) or HTTPS, or a local path.

In a terminal, at the project root:

```bash
npx bmad-method install
```

The installer prompts step by step. Walk through it like this (the line under each question is what you choose/enter):

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│
◇  Installation directory:
│  C:\Users\HanhNT2\stc-erp-bmad-custom
│
o  Install to this directory?
│  Yes
│
o  How would you like to proceed?
│  Modify BMAD Installation
│
│  Found existing modules: core, bmm, bmb
│
o  Select official modules to install:
│    • BMad Core Module
│    • BMad Method
│    • BMad Builder
│
*  Do you want to install custom or community modules (Git URL or local path)?
│  > Yes
│
◇  Git URL or local path:
│  git@git.hblab.vn:stc/erp/stc-erp-bmad-custom.git
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

At the *"Select official modules"* step, make sure **BMad Core Module** (`core`) and **BMad Method** (`bmm`) are selected — HBC needs both (BMad Builder optional). When the custom-module list appears, select **"HBLAB BMad Custom"**, then enter your config (name, language…).

> ⚠️ **Non-interactive install (CI/scripts) — beware of losing modules!** Running `--custom-source` without `--modules` makes the installer keep only `core` + the custom module and **remove** `bmm`/`bmb`. Always list every module to keep (`core` is always included; `--tools` is required with `--yes` on a fresh install):
>
> ```bash
> npx bmad-method install --directory . --modules bmm,bmb \
>   --custom-source git@git.hblab.vn:stc/erp/stc-erp-bmad-custom.git \
>   --tools claude-code --yes
> ```
>
> To **update later** while preserving config & modules: `npx bmad-method install --action quick-update --custom-source <URL>`.
>
> ⚠️ **Permission/clone error?** You don't have repo access yet. Check your SSH key with `ssh -T git@git.hblab.vn`, or use the HTTPS URL, or request access from the team.

## Step 2 — Verify the install ✅

Don't rush into using it. Open your **AI coding agent** (e.g. Claude Code) **in the project directory**, then type:

```
bmad-help
```

`bmad-help` (a BMad **core** skill, not HBC-specific) inspects your project state and advises the next step — **illustrative example** (exact wording varies by version):

```text
BMad Help — inspected your project.
State: no deliverables yet in _bmad-output/ → you haven't initialized the project.
Suggestion: run hbc-project-init (type PI) ONCE to create the shared deliverables, then start your first feature.
```

> ℹ️ If your install doesn't have `bmad-help`, just skip this and type `PI` below — that's enough of a test to confirm HBC is ready.

## Step 3 — Phase 0 is MANDATORY and runs FIRST (`PI`)

Phase 0 (`hbc-project-init`) is **mandatory** and must **complete before** any feature work. Run it **once** for the whole project; to update it later, **re-run to edit directly** (it does not "skip what already exists"). This step takes **no** `feature` argument.

Phase 0 does **two things**:

1. **Understand the project.**
   - *Brownfield* (existing codebase): document the code first with `bmad-document-project`, then ensure `project-context.md` exists (via `bmad-generate-project-context`).
   - *Greenfield* (new project): take context from a PRD/brief, or the agent asks you.
2. **Create the shared deliverables FROM that context:** D-12 Coding Standards (brownfield: derived from existing code conventions), D-03 Glossary (from the domain), constitution.md (the cross-phase invariant principles), baseline D-19 ERD (brownfield: from the existing DB schema), baseline D-21 API (brownfield: from existing endpoints).

> ℹ️ D-12, D-03, and constitution.md are **Phase 0 shared** deliverables — not "optional steps" of Phase 1/2.

Still in the agent, type:

```
PI
```

**Expected result** — shared files appear under `_bmad-output/shared/` (**illustrative example**):

```text
hbc-project-init — created shared deliverables:
  _bmad-output/shared/coding-standards/  (D-12)
  _bmad-output/shared/glossary/          (D-03)
  _bmad-output/shared/constitution.md    (cross-phase invariant principles)
  _bmad-output/shared/erd/               (D-19 baseline)
  _bmad-output/shared/api/               (D-21 baseline)
```

> ℹ️ This is the common foundation for **every** feature, built **from** the project context in step (1). Do it once — later features reuse it (and can override it per-feature when needed); to update it, re-run `PI` to edit directly.

## Step 4 — Meet the Phase 1 agent 🎉

Now open the agent for your first feature. Type:

```
BA
```

**Expected result** — the Business Analyst agent greets you and shows the Phase 1 menu (**illustrative example**, exact wording may differ):

```text
Business Analyst — Phase 1 Analysis coordinator.
You can: REQ (create requirements D-02), GLO (glossary), BFD (business flow)...
```

> 🎉 **First win!** Seeing the agent greet you means you've successfully reached into HBC — the hard part (making it "alive") is done.

### If `BA` doesn't respond 🔧

This is where newcomers get stuck. Try in order:

1. **Are you inside an AI coding agent?** `BA` is an agent command, not a plain-terminal one.
2. **Right project directory?** The agent needs to see the `_bmad/hbc/` folder.
3. **Did the install finish?** Re-run Step 1; check for a `_bmad/hbc/` folder and `_bmad/hbc/config.yaml`.
4. **Still stuck?** Type `bmad-help` and describe the problem — it will help diagnose.

## Step 5 — Create your first document (D-02) for your first feature

D-02 is a **per-feature** deliverable — it always belongs to a specific feature. So you need to name the feature (`feature`) in **kebab-case**, e.g. `change-password`.

Still in the agent, type:

```
REQ
```

The agent asks for the feature name and interviews you about a requirement. Answer briefly, e.g.:

> **feature:** `change-password`
>
> A logged-in user can change their password: enter old password + new password; the system checks the old password is correct and the new one is ≥ 8 characters.

> 💡 **Not sure how to answer?** That's fine — give a rough answer. Re-run `REQ` in `update` mode later to refine it. The goal right now is just to produce your first D-02 file.

**Expected result** — a **D-02 Requirements Specification** file appears in `_bmad-output/features/change-password/planning-artifacts/`, with requirements numbered per feature: `REQ-CHANGE-PASSWORD-001`, `REQ-CHANGE-PASSWORD-002`… (the general pattern is `REQ-<FEAT>-NNN`). Open it: that's your first deliverable.

> ℹ️ **Output layout:** each feature has its own folder under `_bmad-output/features/<feature>/` (with `planning-artifacts`, `implementation-artifacts`, `gates`, `traceability`); shared deliverables live in `_bmad-output/shared/`. The old flat `_bmad-output/planning-artifacts/` folder is gone.

> 🎉 **You've finished the Quickstart!** You just: installed HBC → initialized the project (`PI`) → verified it → created D-02 for your first feature. This is a **stopping point** — you now know the basics of using HBC.
>
> ℹ️ **A note on `PG 1`:** D-02 alone won't pass the Phase 1 gate. Passing `PG 1` also needs **D-03 (from Phase 0, shared)**, **D-06 (BFD — the business flow diagram, per-feature, required)**, and item **`P1-09` model-validation** (you sign off that the domain model has been validated). The full Phase 1 flow is in [Get Started with HBC](getting-started-hbc.md).

## Next steps

- ▶️ **The full lifecycle:** [Get Started with HBC (4-phase walkthrough)](getting-started-hbc.md) — from D-02 to acceptance, shipping one feature independently.
- 🗺️ See the big picture: [Workflow Map](workflow-map.md).
- 💡 Understand the concepts: [Core Concepts](../explanation/concepts.md) · [Why incremental + TDD](../explanation/why-incremental-tdd.md).
- 🔧 Specific tasks: [Run a Phase Gate](../how-to/run-a-phase-gate.md) · [Manage Traceability](../how-to/manage-traceability.md) · [Use Headless Mode](../how-to/use-headless-mode.md) · [Customize Configuration](../how-to/customize-config.md).

> 💡 Whenever you're unsure what's next — type `bmad-help`.
>
> 🔧 **A skill errors out or produces an empty file?** Re-run it in `validate` mode (to check) or `update` mode (to fill in), or type `bmad-help` to diagnose.
