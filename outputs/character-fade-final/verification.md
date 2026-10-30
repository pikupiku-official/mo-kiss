# Character fade verification

2026-10-30 JST. Windows / Python 3.12 / Pygame 2.6.1, SDL dummy display.

- Character rendering, cache, timing, background and input regression tests: 89 passed.
- Demo flow, preview entry points and manual save tests: 26 passed.
- Two independent code reviews; the reported CG-hidden timing and combined linear zoom/crossfade preparation issues were corrected and covered by regression tests.
- Actual GD001 demo UI playback: SKIP activation/cancellation, free-input stop, incorrect-answer retry, real semantic-model correct answer, and transition to the next scene all passed.
- Authored KS and main save state hashes were unchanged by the final playback run.

The same playback runner measured an overall frame-time median of 47 ms before the change and 24 ms afterwards. Character assets are prepared during scene loading; loading time is outside these playback measurements. This does not establish a sustained 60 fps rate.

Final character-fade samples, excluding frames that entered another IR step:

| Measurement | Result |
| --- | ---: |
| Frames | 452 |
| Image loads during these frames | 0 |
| Median frame time | 25.19 ms |
| 95th percentile | 58.71 ms |
| Maximum | 104.53 ms |
| Compact character cache for GD001 | 143.42 MiB |

Raw evidence is in `fade-frames.json`, `gd001-playback.prof`, and `../character-fade-final.log`. Screenshots are `gd001-input.png` and `gd001-success.png`. Physical-window animation smoothness has not been manually assessed; these results cover headless runtime behavior and pixel-comparison tests.
