# Loop9 OpenCode XML Source Of Truth

This directory contains the single source of truth for the Loop9 workflow prompts.

## Files

- `.opencode/_xml/loop9.master.xml`
  - Master specification (defs + per-file definitions).
- `.opencode/_scripts/split_loop9_xml.py`
  - Generator that produces the OpenCode-facing markdown files.

## How To Regenerate

From repo root:

```bash
python3 .opencode/_scripts/split_loop9_xml.py
```

Notes:

- Generated outputs are:
  - `.opencode/command/loop9.md`
  - `.opencode/agents/loop9-controller.md`
  - `.opencode/agents/loop9-solver.md`
  - `.opencode/agents/loop9-validator.md`
  - `.opencode/agents/loop9-refiner.md`
- Do not edit the generated files directly; edit `loop9.master.xml` and re-run the generator.

## Strict Mode

The generator runs in strict mode by default:

- Missing `<include ref="..."/>` references cause failure.
- Forbidden prompt-trigger sequences are rejected to avoid unintended OpenCode expansions.

To disable strict mode:

```bash
python3 .opencode/_scripts/split_loop9_xml.py --strict=false
```
