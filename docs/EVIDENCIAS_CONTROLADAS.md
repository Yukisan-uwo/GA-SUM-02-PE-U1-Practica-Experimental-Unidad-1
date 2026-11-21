# Evidencias personales de caída y recorrido causal

Sesión: `personal-20261121-152127`, iniciada por Roger el 21 de noviembre de 2026
a las 15:21:27 UTC−05:00 en `roger@omarchy`. El entorno completo está en
`data/controlados/personal-20261121-152127/environment.json`.

Se revisaron sus 32 casos, los 171 archivos del manifiesto y la reproducción de
sus resúmenes. Las tablas publicadas en `docs/tablas/controlados/` se generan
desde esta sesión, no desde los datos asistidos de `r01`.

## Capturas originales

Archivos en `docs/evidencias/Roger/controlados/`:

| Archivo | Qué documenta |
|---|---|
| `control_01_ejecucion.png` | Comando, fecha, usuario, máquina, 32 casos y salida 0/0 |
| `control_02_fallo.png` | Consulta posterior del registro: C terminado, fallo B→C y continuidad A→B |
| `control_03_analisis.png` | Analizador, 32 casos validados y tabla de los datos personales |
| `control_04_hashes.png` | Revisión posterior con SHA256 quiet y código 0 |
| `control-20261121-152127.log` | Salida original de la ejecución |

Las capturas 2 y 4 corresponden a consultas/comprobaciones realizadas después
de la corrida, no a nuevas ejecuciones. La comprobación quiet valida todos los
archivos aunque no muestre una línea por cada uno. No se reconstruyeron ni
editaron capturas. Los cinco archivos están cubiertos por el SHA256SUMS de su carpeta.

## Alcance

La prueba de caída termina C entre intercambios, no durante un RPC activo.
El resultado general OK confirma que se observó el fallo esperado y la respuesta
del enlace sano; no significa que C respondiera al intento posterior.

Estas fotos documentan la sesión personal de pruebas controladas. No acreditan
ejecución manual de las capturas de 300 solicitudes ni sustituyen el video o
demostración. Código, preparación y verificación tuvieron asistencia de IA.
