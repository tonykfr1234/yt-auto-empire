# Contributing

Contributions are welcome. Keep changes focused and testable.

Before opening a pull request:

1. Do not commit credentials, Gemini/YouTube keys, `client_secrets.json`, `token.json`, browser profiles or runtime state files.
2. Run `python -m py_compile *.py`.
3. If you change generation, editing or upload behavior, describe how you tested it (engine mode, video length, whether upload was dry-run).
4. Keep `README.md` (English), `README.zh-TW.md` and `README.zh-CN.md` aligned when behavior changes, and add an entry to `CHANGELOG.md`.
5. Only reference models and assets whose licenses allow redistribution or linking.
