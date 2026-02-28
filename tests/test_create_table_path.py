import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CreateTablePathTests(unittest.TestCase):
    def test_create_table_writes_database_next_to_script(self):
        repo_root = Path(__file__).resolve().parents[1]
        source_script = repo_root / "db" / "createTable.py"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            script_dir = tmp_path / "copied" / "db"
            script_dir.mkdir(parents=True)
            copied_script = script_dir / "createTable.py"
            shutil.copy2(source_script, copied_script)

            work_dir = tmp_path / "work"
            work_dir.mkdir()

            subprocess.run(
                [sys.executable, str(copied_script)],
                cwd=work_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertTrue((script_dir / "database.db").exists())
            self.assertFalse((work_dir / "database.db").exists())


if __name__ == "__main__":
    unittest.main()
