import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools import orbit_tools


class OrbitToolsTests(unittest.TestCase):
    def test_selects_configured_assets_from_release(self):
        release = {
            "tag_name": "GeneralsX-Beta-11",
            "html_url": "https://github.com/fbraz3/GeneralsX/releases/tag/GeneralsX-Beta-11",
            "assets": [
                {
                    "name": "GeneralsX-linux.flatpak",
                    "browser_download_url": "https://example.invalid/GeneralsX-linux.flatpak",
                    "digest": "sha256:abc",
                    "size": 10,
                },
                {
                    "name": "GeneralsXZH-linux.flatpak",
                    "browser_download_url": "https://example.invalid/GeneralsXZH-linux.flatpak",
                    "digest": "sha256:def",
                    "size": 20,
                },
                {
                    "name": "macos-generalsx-app.tar.zip",
                    "browser_download_url": "https://example.invalid/macos.zip",
                    "digest": "sha256:unused",
                    "size": 30,
                },
            ],
        }
        packages = [
            {"id": "com.fbraz3.GeneralsX", "asset": "GeneralsX-linux.flatpak"},
            {"id": "com.fbraz3.GeneralsXZH", "asset": "GeneralsXZH-linux.flatpak"},
        ]

        selected = orbit_tools.select_release_assets(release, packages)

        self.assertEqual([asset["name"] for asset in selected], ["GeneralsX-linux.flatpak", "GeneralsXZH-linux.flatpak"])
        self.assertEqual(selected[0]["app_id"], "com.fbraz3.GeneralsX")
        self.assertEqual(selected[1]["app_id"], "com.fbraz3.GeneralsXZH")

    def test_missing_configured_asset_is_an_error(self):
        release = {"tag_name": "GeneralsX-Beta-11", "assets": []}
        packages = [{"id": "com.fbraz3.GeneralsX", "asset": "GeneralsX-linux.flatpak"}]

        with self.assertRaisesRegex(ValueError, "GeneralsX-linux.flatpak"):
            orbit_tools.select_release_assets(release, packages)

    def test_sha256_digest_verification_accepts_matching_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = Path(tmpdir) / "bundle.flatpak"
            bundle.write_bytes(b"flatpak bundle")
            digest = "sha256:" + hashlib.sha256(b"flatpak bundle").hexdigest()

            orbit_tools.verify_sha256_digest(bundle, digest)

    def test_sha256_digest_verification_rejects_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = Path(tmpdir) / "bundle.flatpak"
            bundle.write_bytes(b"flatpak bundle")

            with self.assertRaisesRegex(ValueError, "SHA-256"):
                orbit_tools.verify_sha256_digest(bundle, "sha256:" + "0" * 64)

    def test_flatpakrepo_uses_required_keys(self):
        content = orbit_tools.render_flatpakrepo(
            title="Orbit",
            url="https://cheviiot.github.io/Orbit/repo/",
            homepage="https://cheviiot.github.io/Orbit/",
            comment="Личный Flatpak-репозиторий",
            description="Личный Flatpak-репозиторий с выбранными приложениями.",
            gpg_key="BASE64KEY",
        )

        self.assertIn("[Flatpak Repo]\n", content)
        self.assertIn("Title=Orbit\n", content)
        self.assertIn("Url=https://cheviiot.github.io/Orbit/repo/\n", content)
        self.assertIn("GPGKey=BASE64KEY\n", content)

    def test_package_config_validation_rejects_duplicate_assets(self):
        config = {
            "source": {"repository": "fbraz3/GeneralsX", "release": "latest"},
            "packages": [
                {"id": "com.fbraz3.GeneralsX", "asset": "GeneralsX-linux.flatpak"},
                {"id": "com.fbraz3.Other", "asset": "GeneralsX-linux.flatpak"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "packages.json"
            path.write_text(json.dumps(config), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicate asset"):
                orbit_tools.load_package_config(path)

    def test_index_uses_configured_base_url(self):
        content = orbit_tools.render_index(
            title="Orbit",
            base_url="https://example.com/custom",
            repo_file="orbit.flatpakrepo",
            remote_name="orbit",
            packages=[
                {
                    "app_id": "com.fbraz3.GeneralsX",
                    "title": "GeneralsX",
                    "release_tag": "GeneralsX-Beta-11",
                }
            ],
            source_url="https://github.com/fbraz3/GeneralsX/releases/tag/GeneralsX-Beta-11",
        )

        self.assertIn("https://example.com/custom/orbit.flatpakrepo", content)
        self.assertNotIn("https://cheviiot.github.io/Orbit/orbit.flatpakrepo", content)


if __name__ == "__main__":
    unittest.main()
