# Draw.io Diagram Exports

This directory contains draw.io source files (`.drawio`) and their exported SVG versions (`.svg`).

## Exporting SVGs

To export an SVG from a `.drawio` file:

```bash
xvfb-run --auto-servernum /snap/bin/drawio \
  --export --format svg \
  --output docs/draw-io-exports/<name>.svg \
  docs/draw-io-exports/<name>.drawio
```

## Required Diagrams

Each state machine implemented by the service should have a corresponding diagram:

- `populate-draft-data.drawio` → `populate-draft-data.svg`
- `validate-draft-and-put-ready-event.drawio` → `validate-draft-and-put-ready-event.svg`
- `launch-pieriandx-from-ready-event.drawio` → `launch-pieriandx-from-ready-event.svg`
- `monitor-pdx-runs.drawio` → `monitor-pdx-runs.svg`
- `glue-succeeded-events-to-draft-update.drawio` → `glue-succeeded-events-to-draft-update.svg`

## TODO

- [ ] Create `.drawio` source files for each state machine using the `asl-to-drawio` skill
- [ ] Export SVGs from the `.drawio` files
- [ ] Migrate existing diagrams from `docs/drawio-exports/` (legacy location) to this directory
