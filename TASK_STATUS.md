# Task status

Status: not_completed
Remaining items: 1
Current item: Разблокировать запуск GitHub Actions в аккаунте

Completed items:
- Выбрано название репозитория: Orbit.
- Проверена доступность `gh`, `git`, `flatpak`, `flatpak build-import-bundle` и `flatpak build-update-repo`.
- Проверено, что `Cheviiot/Orbit` еще не существует на GitHub.
- Проверены два исходных релизных пакета GeneralsX: `GeneralsX-linux.flatpak` и `GeneralsXZH-linux.flatpak`.
- Создан локальный каркас репозитория Orbit.
- Добавлены тесты для выбора assets, проверки SHA-256, генерации `.flatpakrepo` и проверки инициализации OSTree repo.
- Реализованы утилиты синхронизации релизных bundles из `fbraz3/GeneralsX`.
- Добавлен workflow публикации Flatpak remote через GitHub Pages.
- Проверена загрузка и SHA-256 валидация двух bundles из релиза `GeneralsX-Beta-11`.
- Проверен импорт двух bundles во временный OSTree repo.
- Проверена полная локальная генерация `public/` с временным GPG-ключом.
- Создан публичный GitHub-репозиторий `Cheviiot/Orbit`.
- `main` запушен в `https://github.com/Cheviiot/Orbit`.
- Добавлены GitHub Secrets `GPG_PRIVATE_KEY` и `GPG_KEY_ID`.
- GitHub Pages включен в режиме `workflow`.
- Проверен GitHub Actions run `28279112210`: job `build` не стартовал на runner.
- Проверена annotation check-run `83791357867`: запуск заблокирован GitHub из-за billing issue аккаунта.

Blocked items:
- GitHub Actions для `Cheviiot/Orbit` не стартует: `The job was not started because your account is locked due to a billing issue.`

Last checks:
- `gh auth status`
- `flatpak --version`
- `flatpak build-import-bundle --help`
- `flatpak build-update-repo --help`
- `gh api repos/fbraz3/GeneralsX/releases/latest`
- `python3 -m unittest discover -s tests -v`
- `python3 tools/orbit_tools.py sync-bundles --config packages/generalsx.json --output-dir dist/bundles --metadata dist/generalsx-release.json`
- `flatpak build-import-bundle` в `/tmp/orbit-import-check`
- `scripts/build_pages.sh` с временным GPG-ключом
- `gh run list --repo Cheviiot/Orbit --workflow publish.yml --limit 5`
- `gh run view 28279112210 --repo Cheviiot/Orbit --json status,conclusion,event,createdAt,updatedAt,displayTitle,headSha,jobs`
- `gh api repos/Cheviiot/Orbit/check-runs/83791357867/annotations`

Notes:
- Репозиторий должен публиковать настоящий Flatpak remote через GitHub Pages, а не только `.flatpak` bundles в GitHub Releases.
- Первые пакеты: `com.fbraz3.GeneralsX` и `com.fbraz3.GeneralsXZH`.
- После разблокировки billing нужно вручную запустить workflow `Publish Flatpak Repository` или сделать новый push.
