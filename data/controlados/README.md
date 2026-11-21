# Conjuntos de pruebas controladas

- `personal-20261121-152127/`: sesión ejecutada por Roger el 21/11/2026 a las
  15:21:27 UTC−05:00. Es la fuente de las tablas de `docs/tablas/controlados/`.
- `r01/`: sesión automatizada asistida anterior, conservada como conjunto
  independiente con su procedencia. Sus datos no se mezclan con la sesión personal.

Cada conjunto tiene dos pruebas de caída y treinta cadenas (TCP/gRPC, 2/3/5 nodos,
cinco repeticiones). No contar ambas sesiones como diez repeticiones de una única
condición ni mezclar CSV con IDs repetidos entre conjuntos.

Los archivos originales se conservan sin edición. Cada conjunto tiene su propio
manifiesto y el `SHA256SUMS` de este directorio cubre ambos conjuntos y este índice.
Las capturas personales y su manifiesto están en `docs/evidencias/Roger/controlados/`.

Código, preparación y verificación tuvieron asistencia de IA. La sesión personal
está documentada por su log, metadatos y capturas; los otros datos no se atribuyen
a ejecución manual.
