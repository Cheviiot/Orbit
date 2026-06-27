#!/usr/bin/env python3
"""Helpers for publishing the Orbit Flatpak repository."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


USER_AGENT = "Orbit Flatpak Repository Publisher"
GITHUB_API = "https://api.github.com"


def load_package_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    source = config.get("source")
    packages = config.get("packages")
    if not isinstance(source, dict):
        raise ValueError("package config must contain a source object")
    if not isinstance(packages, list) or not packages:
        raise ValueError("package config must contain at least one package")

    repository = source.get("repository")
    if not isinstance(repository, str) or "/" not in repository:
        raise ValueError("source.repository must use owner/name format")
    source.setdefault("release", "latest")

    seen_assets: set[str] = set()
    seen_ids: set[str] = set()
    for package in packages:
        if not isinstance(package, dict):
            raise ValueError("each package entry must be an object")
        app_id = package.get("id")
        asset = package.get("asset")
        title = package.get("title")
        if not isinstance(app_id, str) or not app_id:
            raise ValueError("each package must define id")
        if not isinstance(asset, str) or not asset.endswith(".flatpak"):
            raise ValueError(f"package {app_id} must define a .flatpak asset")
        if title is not None and not isinstance(title, str):
            raise ValueError(f"package {app_id} title must be a string")
        if app_id in seen_ids:
            raise ValueError(f"duplicate app id: {app_id}")
        if asset in seen_assets:
            raise ValueError(f"duplicate asset: {asset}")
        seen_ids.add(app_id)
        seen_assets.add(asset)

    return config


def github_request(url: str, token: str | None = None) -> urllib.request.Request:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def fetch_json(url: str, token: str | None = None) -> dict[str, Any]:
    request = github_request(url, token)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed: {error.code} {details}") from error
    return json.loads(data.decode("utf-8"))


def release_api_url(repository: str, release: str) -> str:
    escaped_repo = "/".join(urllib.parse.quote(part, safe="") for part in repository.split("/", 1))
    if release == "latest":
        return f"{GITHUB_API}/repos/{escaped_repo}/releases/latest"
    return f"{GITHUB_API}/repos/{escaped_repo}/releases/tags/{urllib.parse.quote(release, safe='')}"


def fetch_release(repository: str, release: str, token: str | None = None) -> dict[str, Any]:
    return fetch_json(release_api_url(repository, release), token)


def select_release_assets(release: dict[str, Any], packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ValueError("release payload does not contain an assets list")

    by_name = {asset.get("name"): asset for asset in assets if isinstance(asset, dict)}
    selected: list[dict[str, Any]] = []
    missing: list[str] = []

    for package in packages:
        asset_name = package["asset"]
        asset = by_name.get(asset_name)
        if asset is None:
            missing.append(asset_name)
            continue

        download_url = asset.get("browser_download_url")
        if not isinstance(download_url, str) or not download_url:
            raise ValueError(f"asset {asset_name} does not expose browser_download_url")

        selected.append(
            {
                "app_id": package["id"],
                "title": package.get("title", package["id"]),
                "name": asset_name,
                "url": download_url,
                "digest": asset.get("digest"),
                "size": asset.get("size"),
                "release_tag": release.get("tag_name"),
                "release_url": release.get("html_url"),
            }
        )

    if missing:
        raise ValueError("missing configured release assets: " + ", ".join(missing))

    return selected


def download_file(url: str, destination: Path, token: str | None = None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT}
    if token and "github.com" in urllib.parse.urlparse(url).netloc:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            with destination.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"download failed for {url}: {error.code} {details}") from error


def verify_sha256_digest(path: Path, digest: str | None) -> None:
    if not digest:
        raise ValueError(f"asset {path.name} has no digest in GitHub API response")
    if not digest.startswith("sha256:"):
        raise ValueError(f"unsupported digest format for {path.name}: {digest}")

    expected = digest.removeprefix("sha256:").lower()
    actual_hash = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            actual_hash.update(chunk)
    actual = actual_hash.hexdigest()

    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}: expected {expected}, got {actual}")


def render_flatpakrepo(
    *,
    title: str,
    url: str,
    homepage: str,
    comment: str,
    description: str,
    gpg_key: str,
) -> str:
    lines = [
        "[Flatpak Repo]",
        f"Title={title}",
        f"Url={url}",
        f"Homepage={homepage}",
        f"Comment={comment}",
        f"Description={description}",
        f"GPGKey={gpg_key}",
        "",
    ]
    return "\n".join(lines)


def render_index(
    *,
    title: str,
    base_url: str,
    repo_file: str,
    remote_name: str,
    packages: list[dict[str, Any]],
    source_url: str,
) -> str:
    rows = []
    for package in packages:
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(str(package['app_id']))}</code></td>"
            f"<td>{html.escape(str(package.get('title', package['app_id'])))}</td>"
            f"<td>{html.escape(str(package.get('release_tag', 'unknown')))}</td>"
            "</tr>"
        )
    rows_html = "\n".join(rows)
    escaped_title = html.escape(title)
    escaped_base_url = html.escape(base_url.rstrip("/"))
    escaped_repo_file = html.escape(repo_file)
    escaped_remote = html.escape(remote_name)
    escaped_source = html.escape(source_url)
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 900px; line-height: 1.5; padding: 0 1rem; }}
    code, pre {{ background: #f3f3f3; border-radius: 4px; padding: .15rem .3rem; }}
    pre {{ overflow-x: auto; padding: 1rem; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
    th, td {{ border-bottom: 1px solid #ddd; padding: .6rem; text-align: left; }}
  </style>
</head>
<body>
  <h1>{escaped_title}</h1>
  <p>Flatpak-репозиторий для выбранных пакетов.</p>
  <h2>Подключение</h2>
  <pre>flatpak remote-add --user --if-not-exists {escaped_remote} {escaped_base_url}/{escaped_repo_file}</pre>
  <h2>Пакеты</h2>
  <table>
    <thead><tr><th>App ID</th><th>Название</th><th>Релиз</th></tr></thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
  <p>Источник пакетов: <a href="{escaped_source}">{escaped_source}</a></p>
</body>
</html>
"""


def sync_bundles(args: argparse.Namespace) -> int:
    config = load_package_config(Path(args.config))
    token = args.github_token or os.environ.get("GITHUB_TOKEN")
    release = fetch_release(config["source"]["repository"], config["source"].get("release", "latest"), token)
    selected = select_release_assets(release, config["packages"])

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "source_repository": config["source"]["repository"],
        "release_tag": release.get("tag_name"),
        "release_url": release.get("html_url"),
        "packages": [],
    }

    for asset in selected:
        destination = output_dir / asset["name"]
        print(f"Downloading {asset['name']} from {asset['release_tag']}", flush=True)
        download_file(asset["url"], destination, token)
        verify_sha256_digest(destination, asset.get("digest"))
        asset_metadata = dict(asset)
        asset_metadata["local_path"] = str(destination)
        metadata["packages"].append(asset_metadata)

    if args.metadata:
        metadata_path = Path(args.metadata)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return 0


def write_flatpakrepo(args: argparse.Namespace) -> int:
    gpg_key = Path(args.gpg_key_file).read_text(encoding="utf-8").strip()
    content = render_flatpakrepo(
        title=args.title,
        url=args.url,
        homepage=args.homepage,
        comment=args.comment,
        description=args.description,
        gpg_key=gpg_key,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return 0


def write_index(args: argparse.Namespace) -> int:
    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    content = render_index(
        title=args.title,
        base_url=args.base_url,
        repo_file=args.repo_file,
        remote_name=args.remote_name,
        packages=metadata["packages"],
        source_url=metadata["release_url"],
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Orbit Flatpak repository helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync = subparsers.add_parser("sync-bundles", help="Download and verify configured release bundles")
    sync.add_argument("--config", required=True)
    sync.add_argument("--output-dir", required=True)
    sync.add_argument("--metadata", required=True)
    sync.add_argument("--github-token", default=None)
    sync.set_defaults(func=sync_bundles)

    repo = subparsers.add_parser("render-flatpakrepo", help="Render a .flatpakrepo file")
    repo.add_argument("--title", required=True)
    repo.add_argument("--url", required=True)
    repo.add_argument("--homepage", required=True)
    repo.add_argument("--comment", required=True)
    repo.add_argument("--description", required=True)
    repo.add_argument("--gpg-key-file", required=True)
    repo.add_argument("--output", required=True)
    repo.set_defaults(func=write_flatpakrepo)

    index = subparsers.add_parser("render-index", help="Render the Pages index")
    index.add_argument("--title", required=True)
    index.add_argument("--base-url", required=True)
    index.add_argument("--repo-file", required=True)
    index.add_argument("--remote-name", required=True)
    index.add_argument("--metadata", required=True)
    index.add_argument("--output", required=True)
    index.set_defaults(func=write_index)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
