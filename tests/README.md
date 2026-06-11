# Tests

```bash
pip install -r requirements.txt -r requirements-dev.txt

pytest -m "not live"   # unit + unit canaries — what CI runs
pytest -m live         # live integration — requires a running UEFN listener
pytest                 # everything (live tests auto-skip if no listener)
```

| File | Layer | Needs editor? |
|------|-------|---------------|
| `test_log_selection.py` | unit — editor-log selection + filtering | no |
| `test_transport.py` | unit — MCP server HTTP transport (mocked) | no |
| `test_canaries.py` | unit canaries — negative controls | no |
| `test_integration_live.py` | live — real listener: ping, log, screenshot | yes |

The testing strategy, the unit/live boundary, and the canary methodology are
documented in **[../docs/TESTING.md](../docs/TESTING.md)**.
