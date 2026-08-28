---
name: ks-script-format
description: Normalize speaker and dialogue layout in events/*.ks files. Use for KS script-formatting requests that wrap speaker names in //...//, place dialogue on following lines, and align speaker/dialogue lines with one tab; do not use for expression drafting or content edits.
---

# KS Script Format

Format only speaker and dialogue lines in `events/*.ks`.

## Canonical form

```ks
	//純一//
	「セリフ」
	「同じ話者の続き」[female]
```

- Put every speaker name on its own line, wrapped by exactly two half-width slashes on each side.
- Put the first dialogue line immediately below its speaker line, without inserting a blank line.
- Begin both speaker lines and dialogue lines with exactly one tab. They have the same indentation depth.
- Treat a full line already shaped like `//...//` as a speaker line.
- Treat a bare, short line immediately followed by a line beginning with `「` as a speaker candidate only when it is not a KS command, label, comment, or scene separator. Review every newly inferred speaker in the diff.
- Treat lines whose first non-whitespace character is `「` as dialogue. Preserve dialogue text and trailing KS tags such as `[female]` byte-for-byte; replace only leading indentation.

## Boundaries

Do not change dialogue wording, punctuation, bracket style, names, commands, labels, comments, blank-line layout, encoding, line endings, or unrelated formatting. Do not edit `chara_show`, `chara_shift`, backgrounds, audio, branches, or event control as part of this skill.

Do not guess when a bare line could be either a speaker name or a scene heading. Leave it unchanged and report it. A line with multiple apparent speakers, such as `桃子 杏`, is also ambiguous: ask whether the intended form is `//桃子 杏//` or `//桃子// //杏//`. The formatter leaves such lines unchanged until that convention is established. For a clear inline form such as `純一「……」`, split it manually into the canonical two-line form only after confirming from context that the prefix is a speaker.

## Workflow

1. Inspect the requested files and `git status --short`; preserve unrelated user changes.
2. Preview the formatter's unified diff from the repository root:

   ```powershell
   python .agents/skills/ks-script-format/scripts/format_ks.py <target>
   ```

   `<target>` may be a KS file or a directory. With no target, it scans `events` recursively.
3. Review inferred bare speakers and confirm that only speaker wrappers and leading indentation change. If the formatter reports an ambiguous speaker, resolve the convention before using `--write`.
4. Apply the reviewed changes:

   ```powershell
   python .agents/skills/ks-script-format/scripts/format_ks.py <target> --write
   ```

5. Verify idempotence and inspect the final diff:

   ```powershell
   python .agents/skills/ks-script-format/scripts/format_ks.py <target> --check
   git diff -- <target>
   ```

If the user says “one paragraph below” or equivalent without further detail, interpret it as “the dialogue starts on the next line, with no blank line,” because speaker and dialogue indentation must both be one tab. State this interpretation in the handoff when it matters.
