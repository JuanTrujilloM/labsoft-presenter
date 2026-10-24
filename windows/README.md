# Presenter para Windows

Aún no hay ejecutable. PyInstaller solo empaqueta para el sistema donde se ejecuta, así que `Presenter.exe` se genera en un PC con Windows:

```bash
uv sync --group package
uv run pyinstaller presenter.spec --noconfirm
```

El resultado queda en `dist/Presenter.exe`. Cópialo a esta carpeta.
