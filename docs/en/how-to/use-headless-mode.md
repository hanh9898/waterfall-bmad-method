# How to Use Headless Mode

> 🌐 **English** · [Tiếng Việt](../../vi/how-to/use-headless-mode.md)
>
> 🔧 **How-to** — run HBC skills without interactive back-and-forth.

## Goal

Run a skill in automated mode (no stopping to ask you), suitable for scripts, CI, or when the input is already clear.

## Syntax

Add the `--headless` flag or its shorthand `-H` to the end of a command:

```
REQ create -H
PG 2 -H
TRU -H
```

Most workflow skills support `-H` (see the Args column in the [Skills Catalog](../reference/skills-catalog.md)).

## When to use it

| Situation | Why headless fits |
| --- | --- |
| Running in a CI/CD pipeline | No human to answer prompts |
| Input is already complete and clear | No need for the agent to ask more |
| Batch re-runs | Avoid mid-run pauses |
| Automation via scripts | Seamless execution |

## When **not** to use it

- First-time creation of a deliverable that needs discussion (e.g. the first `REQ`) — interactive mode enables better elicitation.
- When requirements are still vague — letting the agent ask yields higher quality.

> 💡 Simple rule: **interactive when first creating content; headless when validating, updating, or automating.**

## Combining with modes

`-H` pairs with a skill's mode/argument. For example, with traceability and the gate:

```
TRI -H
TRU -H
PG 1 -H
```

Or batch-validate at project end:

```
REQ validate -H
TS validate -H
```

## Related

- 📖 Per-skill Args column: [Skills Catalog](../reference/skills-catalog.md)
- 🔗 [Run a Phase Gate](run-a-phase-gate.md)
