# KS movie overlay

KS can play one continuously looping movie layer above the background, CG, and
characters and below the dialogue UI.

```ks
[bg storage="通学路①"]
[rain_sound preset="heavy" volume="0.32" fade="0.8"]
[haze_show color="218,226,232" opacity="0.16" fade="0.8"]
[movie_show file="heavy_rain.mp4" loop="true" opacity="0.55" fade="0.8" mode="alpha" fit="cover"]
[movie_hide fade="0.8"]
[rain_sound_stop fade="0.8"]
[haze_hide fade="0.8"]
```

`movie_show` accepts these attributes:

- `file` or `storage`: a file in `movies/`; the extension may be omitted.
- `loop`: `true` by default.
- `opacity`: overlay strength from `0.0` to `1.0`; default `1.0`.
- `fade` or `fade_in`: show fade duration in seconds.
- `mode`: `alpha` (default) treats black as transparent; `opaque` keeps the
  whole decoded frame.
- `x`, `y`, `zoom`: normalized center and scale; defaults are `0.5`, `0.5`,
  and `1.0`.
- `fit`: `cover` preserves the movie aspect ratio and crops only the centered
  edges to fill the 4:3 virtual screen; `stretch` keeps the legacy full-frame
  stretch.
- `speed`: playback speed; default `1.0`.
- `start`: start position in seconds; default `0`.

`movie_hide` accepts `fade`, `fade_out`, or `time`, all in seconds. The fade
duration blocks advancement for that action, while a looping movie itself does
not block dialogue. Use `movie_hide` when the effect should stop.

The runtime prefers OpenCV and falls back to `ffmpeg`/`ffprobe` on `PATH`, so
the latter must be installed when OpenCV cannot decode the file.

Two intensity presets are bundled: `movies/light_rain.mp4` and
`movies/heavy_rain.mp4`. They use the same black-key transparency path, with
the light preset reducing the rain alpha to about 45%.

The bundled `movies/heavy_rain.mp4` is a lightweight H.264 compatibility copy
of the 1920x1080, 10-second ProRes 4444 alpha-channel rain clip from
[Miirriin rain material](https://miirriin.com/en/rain01-2/). The conversion stores
the source alpha as white rain on a black background; `mode="alpha"` keys out
that black background at runtime. The source page states that its materials are
free for personal and commercial use.

## Rain ambience and BG haze

`rain_sound` uses an independent mixer channel, so it does not replace the
scene BGM or one-shot SE. `preset="normal"` and `preset="heavy"` select the
bundled loop files in `sounds/ambience/`; `file="..."`, `volume`, and `fade`
can be used when a different ambience file is needed. Stop it with
`rain_sound_stop`.

`haze_show` is a uniform translucent veil drawn over the BG and applied to
each character according to its displayed `size`. The character haze amount is
relative to `haze_show`'s `opacity`: `size=0.5` receives 100%, `size=1.0`
receives 50%, and `size=2.0` or larger receives 0%, with linear interpolation
between those points. CGs and the later rain movie layer are not affected;
character draw order is unchanged. The legacy `drift` attribute is accepted
for script compatibility but has no visual effect. Stop it with `haze_hide`.
