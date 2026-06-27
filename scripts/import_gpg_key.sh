#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${GPG_PRIVATE_KEY:-}" ]]; then
  echo "GPG_PRIVATE_KEY is required" >&2
  exit 1
fi

if [[ -z "${GPG_KEY_ID:-}" ]]; then
  echo "GPG_KEY_ID is required" >&2
  exit 1
fi

mkdir -p "${HOME}/.gnupg"
chmod 700 "${HOME}/.gnupg"

printf '%s' "${GPG_PRIVATE_KEY}" | gpg --batch --import
gpg --batch --list-secret-keys --keyid-format=long "${GPG_KEY_ID}" >/dev/null

if [[ -n "${GPG_PASSPHRASE:-}" ]]; then
  echo "allow-preset-passphrase" >> "${HOME}/.gnupg/gpg-agent.conf"
  gpg-connect-agent reloadagent /bye >/dev/null

  keygrip="$(gpg --batch --with-colons --with-keygrip --list-secret-keys "${GPG_KEY_ID}" | awk -F: '/^grp:/ { print $10; exit }')"
  if [[ -z "${keygrip}" ]]; then
    echo "Could not determine GPG keygrip for ${GPG_KEY_ID}" >&2
    exit 1
  fi

  preset_tool=""
  for candidate in \
    "$(command -v gpg-preset-passphrase || true)" \
    /usr/libexec/gpg-preset-passphrase \
    /usr/lib/gnupg/gpg-preset-passphrase; do
    if [[ -n "${candidate}" && -x "${candidate}" ]]; then
      preset_tool="${candidate}"
      break
    fi
  done

  if [[ -z "${preset_tool}" ]]; then
    echo "gpg-preset-passphrase was not found, but GPG_PASSPHRASE is set" >&2
    exit 1
  fi

  printf '%s' "${GPG_PASSPHRASE}" | "${preset_tool}" --preset "${keygrip}"
fi
