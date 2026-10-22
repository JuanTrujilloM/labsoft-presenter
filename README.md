# Presenter

Una capa ligera para presentar en macOS. Resalta un elemento, amplía la pantalla o escribe sobre una diapositiva sin salir de ella.

## Ejecutar

```bash
uv sync
uv run presenter
```

La barra queda en la parte inferior de la pantalla. Arrastra el anillo dorado para moverla.

## Permisos de macOS

Presenter necesita dos permisos, y macOS se los concede a la app que abre Python (Terminal, iTerm o Cursor):

- **Accesibilidad** — atajos de teclado y enmarcar mientras sigues presentando.
- **Grabación de pantalla** — el zoom.

Si aparece un aviso, permítelo, cierra Presenter y ábrelo de nuevo.

## Atajos

| Acción | Atajo |
| --- | --- |
| Resaltar | ⌃⌥H |
| Láser | ⌃⌥L |
| Zoom | ⌃⌥Z |
| Dibujar | ⌃⌥D |
| Escribir | ⌃⌥T |
| Mostrar u ocultar herramientas | ⌃⌥P |
| Salir de la herramienta | Esc |
| Deshacer | ⌘Z |

Al resaltar, pulsa **Marco** y arrastra alrededor de un elemento. Mantén ⌥ y arrastra para enmarcar sin salir de la diapositiva. Desplázate, o usa + y −, para cambiar el foco de luz o el zoom. Con varias pantallas, Zoom pide primero cuál ampliar y sigue al puntero solo en esa pantalla. Con el zoom activo, un doble clic pasa al lápiz y otro doble clic vuelve a mover.

La tinta y los marcos permanecen al salir de una herramienta. **Borrar** los quita. **Listo** o Esc da un paso atrás.
