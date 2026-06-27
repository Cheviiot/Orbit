# Orbit

Orbit — личный Flatpak-репозиторий для выбранных пакетов. Первый набор пакетов зеркалирует релизные Flatpak bundles из `fbraz3/GeneralsX`:

- `com.fbraz3.GeneralsX`
- `com.fbraz3.GeneralsXZH`

Репозиторий публикуется через GitHub Pages как обычный Flatpak remote.

## Подключение

После успешного выполнения workflow `Publish Flatpak Repository` подключи remote:

```bash
flatpak remote-add --user --if-not-exists orbit \
  https://cheviiot.github.io/Orbit/orbit.flatpakrepo
```

Установка пакетов:

```bash
flatpak install --user orbit com.fbraz3.GeneralsX
flatpak install --user orbit com.fbraz3.GeneralsXZH
```

Обновление:

```bash
flatpak update --user
```

## Как устроена публикация

Workflow `.github/workflows/publish.yml` выполняет полный цикл:

1. импортирует GPG-ключ из GitHub Secrets;
2. получает последний релиз `fbraz3/GeneralsX` через GitHub API;
3. скачивает `GeneralsX-linux.flatpak` и `GeneralsXZH-linux.flatpak`;
4. проверяет SHA-256 digest каждого asset из GitHub API;
5. импортирует bundles в локальный OSTree-репозиторий через `flatpak build-import-bundle`;
6. обновляет summary, AppStream и static deltas через `flatpak build-update-repo`;
7. генерирует `orbit.flatpakrepo`;
8. публикует `public/` через GitHub Pages.

## GitHub Secrets

Для публикации нужны secrets:

| Secret | Обязателен | Назначение |
| --- | --- | --- |
| `GPG_PRIVATE_KEY` | Да | ASCII-armored приватный GPG-ключ для подписи Flatpak remote. |
| `GPG_KEY_ID` | Да | ID ключа, которым подписываются commits и summary. |
| `GPG_PASSPHRASE` | Нет | Пароль ключа, если ключ создан с passphrase. |

Пример подготовки ключа, совместимый со старыми версиями GnuPG:

```bash
cat > orbit-gpg-batch <<'EOF'
Key-Type: RSA
Key-Length: 3072
Name-Real: Orbit Flatpak Repository
Name-Email: orbit@example.invalid
Expire-Date: 2y
%no-protection
%commit
EOF

gpg --batch --gen-key orbit-gpg-batch
gpg --list-secret-keys --keyid-format=long
gpg --armor --export-secret-keys <KEY_ID> > orbit-private.asc
```

Содержимое `orbit-private.asc` добавляется в `GPG_PRIVATE_KEY`, а `<KEY_ID>` — в `GPG_KEY_ID`.

## Локальные проверки

Проверка тестов:

```bash
python3 -m unittest discover -s tests -v
```

Проверка загрузки релизных bundles без публикации:

```bash
python3 tools/orbit_tools.py sync-bundles \
  --config packages/generalsx.json \
  --output-dir dist/bundles \
  --metadata dist/generalsx-release.json
```

Локальная сборка `public/` требует доступного GPG secret key:

```bash
ORBIT_GPG_KEY_ID=<KEY_ID> scripts/build_pages.sh
```

## Добавление пакетов

Для нового пакета из того же релиза добавь запись в `packages/generalsx.json`:

```json
{
  "id": "com.example.App",
  "title": "Example App",
  "asset": "Example-linux.flatpak"
}
```

Если пакет берется из другого upstream-репозитория, лучше добавить отдельный config и расширить workflow отдельным шагом синхронизации.
