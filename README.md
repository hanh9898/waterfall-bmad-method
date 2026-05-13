# HBLAB BMad Custom

Custom variants of BMad Method workflows by HBLAB.

## Requirements

- [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) v6.3.0+
- BMM (BMad Method Module) installed

## Installation

```bash
npx bmad-method install --custom-source https://github.com/<your-org>/hblab-bmad-custom
```

Select "HBLAB BMad Custom" when prompted.

## Skills Included

| Code | Skill | Description |
| --- | --- | --- |
| CI | hbc-create-invest-epics-and-stories | INVEST + 3C's variant of Create Epics & Stories |

## Key Differences from Standard Epics & Stories

1. AC describes observable user behavior only — no code/syntax/file paths
2. Stories sized 1-2 days max (Fibonacci: 1, 2, 3, 5, 8)
3. Enabler/foundation stories moved to Technical Tasks or DoD
4. "As a System" stories reframed user-centric
5. Dependencies minimized for parallel implementation
6. AC references Architecture.md for HOW
7. Output to `invest-stories.md` for side-by-side comparison with `epics.md`

## Usage

After installation:

- `CI` or `create invest stories` — Generate INVEST user stories
- Customizable via `_bmad/custom/hbc-create-invest-epics-and-stories.toml`

## License

UNLICENSED — Internal use only.
