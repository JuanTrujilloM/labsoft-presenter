# Presenter para Linux

`Presenter-linux-x86_64.tar.gz` es para PCs de 64 bits (x86_64) con Ubuntu 22.04 o posterior, Debian 12, Fedora 36 o cualquier distribución con glibc 2.35 o más nueva.

```bash
tar -xzf Presenter-linux-x86_64.tar.gz
./Presenter/Presenter
```

Los atajos globales y el zoom necesitan una sesión X11. En Ubuntu, elige **Ubuntu en Xorg** en la pantalla de inicio de sesión. En Wayland la barra, el dibujo y el resto siguen funcionando.

Algunos escritorios usan los mismos atajos y se adelantan a Presenter: en Ubuntu, Ctrl+Alt+T abre la terminal; en XFCE, Ctrl+Alt+D muestra el escritorio (minimiza la presentación) y Ctrl+Alt+L bloquea la pantalla; en KDE, Ctrl+Alt+L también bloquea la pantalla. Usa los botones de la barra para esas herramientas o quita esos atajos en la configuración del teclado del escritorio.
