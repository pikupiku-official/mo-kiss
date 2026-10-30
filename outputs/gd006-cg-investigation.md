# GD006 CG performance investigation

2026-10-31, Windows / Python 3.12 / Pygame 2.6.1.

## Reproduced causes

1. `夜教室.JPG` is 6000×4000. Its decoded RGBA surface is 91.55 MiB,
   exceeding the native image cache's 64 MiB budget. Fetching a CG evicted
   the background; fetching the background next frame evicted the CGs.
   CG rendering fetched native images every frame, repeatedly decoding the
   same files and invalidating the source-identity scale cache.
2. CG variants used the transparent-character crossfade compositor. Its
   per-frame full-screen RGBA channel multiplication was unnecessary for
   GD006's fully opaque, identically positioned CG rectangles.

## Changes

- CG geometry and resized pixels now use the existing scene-owned,
  byte-bounded image cache, keyed by asset and output dimensions.
- Authored CG variants/zoom endpoints are prepared with the scene's character
  images during loading. Endpoint preparation precedes the fade clock.
- Matching opaque CG rectangles use an RGB source-over blend, equivalent to
  the same linear interpolation within integer rounding. Transparency,
  different positions/sizes, show and hide retain the original compositor.
- No scenario text, source images, fade durations or SKIP input rules changed.

## Real-runtime comparison

The runner loads the real GD006 demo scene, seeks to the preceding dialogue,
renders it once, then uses Space-key SKIP with the real clock for all 21 CG
commands. SDL video/audio are headless; no mocked frame clock is used.
Runs use an isolated save profile. PNG encoding occurs after playback.
The baseline loads the committed CG module in memory without reverting files.

| Measurement | Before | After |
| --- | ---: | ---: |
| Scene render median | 564.28 ms | 10.23 ms |
| Scene render p95 | 616.93 ms | 14.72 ms |
| Scene render maximum | 694.85 ms | 64.23 ms |
| CG variant draw median | 37.56 ms | 5.97 ms |
| Image decodes during CG sequence | 111 | 0 |
| Frames per authored 300 ms variant fade | 1 | 8–16 |

The initial show remains 500 ms; all 20 variant fades remain 300 ms.
The prepared scene-image cache uses 107.02 MiB within its 256 MiB budget.
Real-asset pixel comparison at 0%, 25%, 50%, 75%, 100% found a maximum
channel difference of 2/255; the endpoints match exactly.
Authored KS and main save data hashes match before/after both runtime runs.
Physical-display visual confirmation remains unperformed.

## Verification

- 93 related tests passed, covering CGs, fade timing, transparent/moving CG
  fallbacks, byte-cache eviction, character fade continuity, SKIP controls,
  image preparation and loading progress.
- The eviction regression exercises an oversized background and asserts
  zero file decodes from CG show through variant-fade completion.
- A broader run: 139 passed, 1 skipped, 2 failures. The same two editor tests
  fail with the committed CG module and CG preparation disabled:
  `test_scene_builder_background_x_is_normalized_image_center` (float equality)
  and `test_chara_shift_can_explicitly_clear_an_existing_effect` (missing checkbox).

Reproduce the runtime comparison:

```powershell
python tests/gd006_cg_playback_runner.py outputs/gd006-cg-before --reference
python tests/gd006_cg_playback_runner.py outputs/gd006-cg-after
```

Raw metrics and screenshots are in `gd006-cg-before/` and `gd006-cg-after/`.
Pixel comparison results are in `gd006-cg-pixel-comparison.json`.
