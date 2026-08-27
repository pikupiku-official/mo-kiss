---
name: expression-draft
description: Create or revise an AI draft of character expressions in one events/*.ks scenario by studying human-confirmed KS examples. Use for Japanese hyojo-sabun requests, expression drafting, AI drafts, or context-aware chara_show/chara_shift expression work in this repository.
---

# KS Expression Draft

Create one manually requested KS expression draft. Use reviewed KS files as examples, preserve all non-expression behavior, and leave the result for human confirmation.

## Status contract

Each `events/*.ks` file has one KS-level status after `*start`:

- No marker or `;@expression-status: initial`: no reviewed expression draft.
- `;@expression-status: ai_draft`: Codex draft awaiting human review.
- `;@expression-status: human_confirmed`: human-confirmed example; never edit it in this workflow.

Use `python tools/expression_status.py get events/<target>.ks` to inspect a target. The tool also provides `list`, `set`, and `validate`. Never infer confirmation from filenames, history, comments, or apparent quality.

## Workflow

1. Require one user-specified target KS. Work only on manual request; do not batch-generate drafts or call an external model API.
2. Inspect status. Stop without editing a `human_confirmed` target. Revise an existing `ai_draft` only on explicit request.
3. Run `python tools/expression_status.py list --status human_confirmed` and read every listed KS before drafting.
4. Learn links between dialogue context and expressions: preceding and following turns, speaker and listener reactions, character identity, scene mood, and effective prior state. Unchanged turns are negative examples; do not make a change merely to make the draft look busy.
5. Read the whole target. Inspect relevant character templates, configuration, and assets to verify proposed part IDs. Prefer exact IDs used for that character in confirmed examples.
6. Build a dialogue-by-dialogue expression decision ledger for every line spoken by each staged character. For each line, explicitly choose one of: show, shift, keep the current expression, or hide. “Keep” is a deliberate decision and produces no tag. Then edit only the target and stay inside the mutation boundary.
7. Add a template interpretation pass before editing KS:
   - For each non-keep expression decision, first write the intended acting beat in plain language, then map it to the closest existing character template from `editor_data/chara_part_templates.json` when one matches.
   - Prefer a named template over manually combining individual parts. If no template fits, choose parts only from confirmed examples or verified assets and mark the ledger entry as a manual expression.
   - Treat templates as expression/pose presets only. Never let a template change dialogue, background, audio, branching, placement, size, or timing beyond the mutation boundary.
   - Re-apply the chosen template or manual expression back into the target KS after the full ledger is consistent. This second pass should catch duplicated shifts, stale effective state, and places where "keep" is better than another tag.
8. Review the diff, validate referenced assets, and confirm that no forbidden tag or text changed.
9. Only after validation, run `python tools/expression_status.py set events/<target>.ks ai_draft`.
10. Report the target, confirmed examples read, template mappings used, manual expressions used, expression changes, and validation.

## Mutation boundary

Allowed:

- Change expression/pose attributes on existing `chara_show` and `chara_shift`: `torso`, `eye`, `mouth`, `brow`, `cheek`, `effect`, `accessory`, and `blink`.
- Insert `chara_show` before a speaking character's first visible line when the scenario has no existing staging tag for that character. Reuse character-specific placement and sizing conventions from human-confirmed examples; the inserted tag may contain `name`, `x`, `y`, `size`, and `fade` only as required to establish that initial staging.
- Insert `chara_shift` only for a character already visible at that exact point. Use `name` only to identify that character and `fade` only when local convention requires it.
- Insert `chara_hide` when a visible character leaves the scene, at a scene boundary, or when the dialogue context clearly calls for removal. Use only `name` and locally conventional fade/timing attributes.
- Change target status from `initial` to `ai_draft` after validation.

Forbidden:

- Never modify background, music, or sound tags, including `bg`, `bg_show`, `bg_move`, `bgm`, `bgmstart`, `bgmstop`, `bgmend`, `se`, `sestop`, and `sewait`.
- Never modify dialogue, speaker names, choices, branches, labels, event control, scrolling, comments, or unrelated whitespace.
- Never change `name`, `x`, `y`, `size`, placement, or identity on an existing character tag.
- Never add `chara_move`, or alter non-expression staging that already exists. Newly inserted `chara_show`/`chara_hide` must only establish and end the dialogue-driven visibility lifecycle requested for the expression draft.
- Never edit a `human_confirmed` KS.

## Drafting rules

- Resolve effective state across partial `chara_shift` updates; omitted attributes retain prior values.
- Use full conversation context, not isolated-line classification.
- Make an explicit show/shift/keep/hide decision for every dialogue line of every staged character. Do not skip a line merely because no tag will be emitted; record it as `keep` in the internal review ledger.
- Prefer `chara_show` only when the character is not currently visible, `chara_shift` only when visible and the expression should change, and no tag when the effective expression should be retained. Never emit redundant shifts solely to demonstrate coverage.
- Ensure each scene's visibility state is closed deliberately: hide characters who should not carry into the next scene, while respecting any established cross-scene convention in confirmed examples.
- Consider listener reactions only when confirmed examples support that rhythm.
- Prefer a small, high-confidence set of changes. Reusing the current expression is valid.
- Keep the diff surgical for easy human review.
