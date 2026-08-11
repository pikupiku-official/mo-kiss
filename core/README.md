# Core package boundaries

`core` is divided by primary responsibility. Every module belongs to exactly
one group according to what it decides or provides.

| Package | Responsibility | Must not |
| --- | --- | --- |
| `flow` | Decide the next application action or scene | Render UI or perform platform input |
| `ui` | Convert UI input into actions and render visual state | Execute save data or scene transitions |
| `runtime` | Provide the Pygame window and subsystem lifecycle contracts | Decide game progression |
| `services` | Provide reusable save, time, image, and audio capabilities | Select the next scene |

`config.py` and `path_utils.py` remain at the package root because all four
groups use them as shared configuration and path foundations.

## Dependency direction

```text
main and feature packages
    -> flow / ui / runtime
    -> services
    -> config / path_utils
```

Lower layers must not import the application entry point. Visual overlays emit
actions; `flow` decides what those actions mean for the application.
