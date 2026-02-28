import os
import unittest
from pathlib import Path


class RunDevLocalScriptTests(unittest.TestCase):
    def test_run_dev_local_script_exists_and_contains_start_commands(self):
        script = Path(__file__).resolve().parents[1] / "run-dev-local.sh"
        self.assertTrue(script.exists())
        content = script.read_text(encoding="utf-8")
        self.assertIn("source .venv/bin/activate", content)
        self.assertIn("flask --app sau_backend run --debug --host 0.0.0.0 --port 5409", content)
        self.assertIn("npm run dev", content)


if __name__ == "__main__":
    unittest.main()
