# Changelog

## 2026-06-27 14:43 VLAT

### Добавлено
- Создан каркас репозитория Orbit для публикации Flatpak remote через GitHub Pages.
- Добавлен список первых пакетов `com.fbraz3.GeneralsX` и `com.fbraz3.GeneralsXZH` в `packages/generalsx.json`.
- Добавлены утилиты `tools/orbit_tools.py` для получения релиза GeneralsX, выбора нужных assets, проверки SHA-256 и генерации `orbit.flatpakrepo`.
- Добавлены CI-скрипты `scripts/import_gpg_key.sh` и `scripts/build_pages.sh`.
- Добавлен workflow `.github/workflows/publish.yml` для сборки OSTree-репозитория и публикации через Pages.
- Добавлена русскоязычная инструкция в `README.md`.
- Создан публичный GitHub-репозиторий `Cheviiot/Orbit`.
- Добавлены GitHub Secrets `GPG_PRIVATE_KEY` и `GPG_KEY_ID` для подписанной публикации.
- GitHub Pages включен в режиме `workflow`.

### Изменено
- Инструкция генерации GPG-ключа в `README.md` переведена на batch-формат, совместимый со старыми версиями GnuPG.

### Проверено
- `python3 -m unittest discover -s tests -v` — 8 тестов прошли.
- `python3 tools/orbit_tools.py sync-bundles --config packages/generalsx.json --output-dir dist/bundles --metadata dist/generalsx-release.json` — скачаны и проверены `GeneralsX-linux.flatpak` и `GeneralsXZH-linux.flatpak`.
- `flatpak build-import-bundle` во временный OSTree repo — появились refs `app/com.fbraz3.GeneralsX/x86_64/master` и `app/com.fbraz3.GeneralsXZH/x86_64/master`.
- `scripts/build_pages.sh` с временным GPG-ключом — сгенерированы `public/orbit.flatpakrepo`, `public/repo/summary` и подписи summary.
- GitHub Actions run `28279112210` — job `build` не стартовал на runner.
- Check-run annotation `83791357867` — GitHub заблокировал запуск из-за billing issue аккаунта.

### Осталось
- Разблокировать GitHub Actions billing для аккаунта.
- После разблокировки запустить workflow `Publish Flatpak Repository`.
