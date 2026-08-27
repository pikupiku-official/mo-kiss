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
6. Edit only the target and stay inside the mutation boundary.
7. Review the diff, validate referenced assets, and confirm that no forbidden tag or text changed.
8. Only after validation, run `python tools/expression_status.py set events/<target>.ks ai_draft`.
9. Report the target, confirmed examples read, expression changes, and validation.

## Mutation boundary

Allowed:

- Change expression/pose attributes on existing `chara_show` and `chara_shift`: `torso`, `eye`, `mouth`, `brow`, `cheek`, `effect`, `accessory`, and `blink`.
- Insert `chara_shift` only for a character already visible at that exact point. Use `name` only to identify that character and `fade` only when local convention requires it.
- Change target status from `initial` to `ai_draft` after validation.

Forbidden:

- Never modify background, music, or sound tags, including `bg`, `bg_show`, `bg_move`, `bgm`, `bgmstart`, `bgmstop`, `bgmend`, `se`, `sestop`, and `sewait`.
- Never modify dialogue, speaker names, choices, branches, labels, event control, scrolling, comments, or unrelated whitespace.
- Never change `name`, `x`, `y`, `size`, placement, or identity on an existing character tag.
- Never add, remove, or retime entrances, movement, or hiding. Do not add `chara_show`, `chara_move`, or `chara_hide`.
- Never edit a `human_confirmed` KS.

## Drafting rules

- Resolve effective state across partial `chara_shift` updates; omitted attributes retain prior values.
- Use full conversation context, not isolated-line classification.
- Consider listener reactions only when confirmed examples support that rhythm.
- Prefer a small, high-confidence set of changes. Reusing the current expression is valid.
- Keep the diff surgical for easy human review.

