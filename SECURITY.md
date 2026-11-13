# Security Policy

## Never commit secrets or private data

This repository must never contain:

- Gemini, YouTube, GitHub or other API keys;
- Colab, Google Drive or browser cookies and session exports;
- `.env` files or credential JSON files;
- runtime state (`published_history.json`, `upload_queue.json`, `ultra_quota_ledger.json` and similar), generated videos or Chrome profiles;
- screenshots that show account e-mails, avatars or file paths.

## If a secret is exposed

1. Revoke or rotate it at the provider immediately.
2. Remove it from the current tree.
3. If it reached a public commit, treat it as compromised even after removal; history rewriting does not undo copies already made.

## Reporting

Open a GitHub issue without including the secret itself, or contact the maintainer through the GitHub profile.
