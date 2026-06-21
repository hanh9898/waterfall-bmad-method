"""Keep regression-fixture payload out of pytest collection.

`process-review/fixtures/` holds frozen TD.0 data, including foreign `test_*.py`
files (the OPMS case code under `resource-plan-billable/code/tests/`). Those are
*fixture data*, not tests to run — they import Odoo and would error on collection.
Globs are relative to this conftest's directory.
"""

collect_ignore_glob = ["**/*.py"]
