# Pruebas controladas: caída y recorrido causal

Resultados generados desde CSV y mediciones reales con hashes comprobados.
No son las 2000 mediciones RTT ni una medición de sincronización física.

## Caída

- gRPC: 3 solicitudes completas, 1 intento fallido, 1 envío sin recepción; reloj 7→8; error UNAVAILABLE; canal sano posterior: True.
- TCP: 3 solicitudes completas, 1 intento fallido, 1 envío sin recepción; reloj 7→8; error ConnectionError; canal sano posterior: True.

La verificación estricta de intercambios completos rechaza ese envío huérfano,
como corresponde. La comprobación específica acepta solo ese caso previsto y exige
que no exista ningún otro error. No inventa la recepción ni elimina el envío fallido.

## Número de nodos

Se mide completar N−1 intercambios secuenciales de una cadena causal, desde el
coordinador. Incluye IPC, creación/reutilización de conexiones y acuses, no solo red.
El intervalo comienza cuando todos los servidores ya están listos. Los procesos y
relojes se crean de nuevo por repetición. No se afirma convergencia de los contadores.

| Mecanismo | Nodos | Corridas | Media ms | Mediana ms | P95 ms |
|---|---:|---:|---:|---:|---:|
| TCP | 2 | 5 | 2.200 | 2.217 | 2.381 |
| TCP | 3 | 5 | 4.384 | 4.306 | 4.839 |
| TCP | 5 | 5 | 10.941 | 11.186 | 12.637 |
| gRPC | 2 | 5 | 13.547 | 10.481 | 25.853 |
| gRPC | 3 | 5 | 16.622 | 16.547 | 19.587 |
| gRPC | 5 | 5 | 29.662 | 29.566 | 32.046 |

La cantidad de saltos varía con N: esta prueba describe esa topología y ese
procedimiento. No aísla el efecto del transporte ni garantiza crecimiento lineal.
El P95 utiliza interpolación lineal sobre el ordenamiento de las observaciones.
Consultar environment.json para origen declarado, sistema, versiones y fecha.
