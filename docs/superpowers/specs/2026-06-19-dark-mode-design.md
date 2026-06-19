# Dark Mode for plcc-ng Docs Site

**Date:** 2026-06-19
**Issue:** 070

## Problem

The docs site has no dark mode. Users who prefer dark mode (by system preference or personal choice) see only the light theme with no way to change it.

## Goal

- Auto-detect the user's system color-scheme preference and apply the matching theme.
- Provide a manual toggle so users can override the detected preference.
- Persist the user's override across page loads.

## Approach

Use MkDocs Material's built-in palette feature. Add a `palette` block to `mkdocs.yml` with two entries — one for light, one for dark — each wired to the corresponding `prefers-color-scheme` media query and a toggle icon. Material handles `localStorage` persistence automatically.

## Change

**File:** `mkdocs.yml` — add `palette` under the `theme` key:

```yaml
palette:
  - media: "(prefers-color-scheme: light)"
    scheme: default
    toggle:
      icon: material/weather-night
      name: Switch to dark mode
  - media: "(prefers-color-scheme: dark)"
    scheme: slate
    toggle:
      icon: material/weather-sunny
      name: Switch to light mode
```

No other files are touched.

## Default Behavior

When no system preference is detectable, the light theme (`scheme: default`) loads because it is listed first.

## Persistence

Material writes the user's toggle choice to `localStorage`. On subsequent visits, the stored value overrides the `media` query result.

## Testing

Manual verification only (no automated tests apply to a config-only docs change):

- Load the site with the OS set to dark → dark theme activates automatically.
- Load the site with the OS set to light → light theme activates automatically.
- Click the toggle → theme switches immediately.
- Reload the page → toggled choice persists.
