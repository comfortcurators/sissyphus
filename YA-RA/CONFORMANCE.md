# YA|RA cross-backend conformance

Cells: `preserved` | `unsupported` | `observational` | `transport`. Never silently weakened.

| construct | python-measure | python-emit | c | cxx | rust | kernel | toe | quantum | llm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| words | preserved | preserved | preserved | preserved | preserved | preserved | preserved | observational | transport |
| exists | preserved | preserved | preserved | preserved | preserved | unsupported | preserved | observational | transport |
| contains | preserved | preserved | preserved | preserved | preserved | unsupported | preserved | observational | transport |
| eq | preserved | preserved | preserved | preserved | preserved | unsupported | preserved | observational | transport |
| run | preserved | preserved | preserved | preserved | preserved | unsupported | preserved | observational | transport |
| use | preserved | preserved | unsupported | unsupported | unsupported | unsupported | unsupported | observational | transport |
| measure all | preserved | preserved | preserved | preserved | preserved | preserved | preserved | observational | transport |
| measure any | preserved | preserved | preserved | preserved | unsupported | unsupported | preserved | observational | transport |

`run` under python-measure still requires `--allow-run`. Absence is a typed refusal, not a silent pass.
