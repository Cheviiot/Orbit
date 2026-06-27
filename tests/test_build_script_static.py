from pathlib import Path
import unittest


class BuildScriptStaticTests(unittest.TestCase):
    def test_build_script_initializes_ostree_repo_before_import(self):
        script = Path("scripts/build_pages.sh").read_text(encoding="utf-8")

        init_index = script.index("ostree --repo=repo init --mode=archive-z2")
        import_index = script.index("flatpak build-import-bundle")

        self.assertLess(init_index, import_index)


if __name__ == "__main__":
    unittest.main()
