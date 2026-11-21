# Caída de nodo y recorrido de información causal

Requiere las dependencias del proyecto y se ejecuta desde la raíz. No modifica
el benchmark de 2000 RTT ni sus archivos. Cada ejecución usa una carpeta nueva.

```fish
.venv/bin/python analysis/run_controlled_checks.py --output data/controlados/personal-r02 --origin personal
.venv/bin/python analysis/analyze_controlled_checks.py data/controlados/personal-r02 --output analysis/controlados_personal_r02
```

Se ejecutan TCP y gRPC por separado. El origen es una declaración, no prueba
automática de participación: deben conservarse capturas personales y logs.

## Caída controlada

1. Se crean tres procesos con servidor, cliente, reloj y registro por nodo.
2. A→B y B→C completan un intercambio cada uno.
3. El coordinador termina el proceso C y espera su salida.
4. B intenta otro envío por la conexión previamente establecida hacia C.
5. A→B completa otro intercambio para comprobar que ese enlace sigue disponible.

El envío fallido incrementa B, pero no se inventa una recepción en C. El CSV
conserva ese evento. El verificador estricto lo rechaza por intercambio incompleto;
el análisis específico exige exactamente ese único envío huérfano y ningún otro
error. No presenta todo el registro como una corrida sin fallos.

La prueba es una terminación entre intercambios, no una caída a mitad de un RPC
ni una partición de red. No implementa recuperación, persistencia de reloj o
reintentos. El error observado depende del transporte y se conserva en result.json.

## Efecto del número de nodos

Se crean 2, 3 y 5 procesos en cinco repeticiones por mecanismo. Con los servidores
ya disponibles, el coordinador ordena A→B, B→C, etc. Cada nodo intermedio recibe
el evento causal antes de enviar el siguiente mensaje de la cadena.

El intervalo medido es completar N−1 intercambios secuenciales con acuses. Incluye
IPC de control, conexiones y transporte; no es latencia pura de red, RTT por mensaje
ni tiempo de sincronización física. Más nodos también implican más saltos en esta
topología. Las repeticiones crean procesos y relojes nuevos; no hay calentamiento
descartado en esta prueba distinta del benchmark.

Los relojes solo registran eventos de aplicación, no los mensajes IPC del
coordinador. No se afirma que los contadores deban igualarse o converger.
Los puertos de estas pruebas son libres/dinámicos para permitir variar N; las
pruebas oficiales de veinte intercambios ya usan 5000/5001/5002.

## Archivos y reproducción

- `data/controlados/r01/`: ejecuciones automatizadas asistidas, con procedencia explícita.
- `data/controlados/personal-20261121-152127/`: sesión personal de Roger; fuente
  de las tablas publicadas, con evidencias en `docs/EVIDENCIAS_CONTROLADAS.md`.
- Cada caso conserva CSV de eventos, resultado y SHA256SUMS.
- El entorno y el manifiesto agregado están en la raíz del conjunto de casos.
- `docs/tablas/controlados/`: resúmenes CSV/Markdown y tablas generadas por el analizador.
- No editar los CSV ni rellenar eventos faltantes para aprobar la verificación.

Recalcular los resultados publicados en una carpeta nueva:

```fish
.venv/bin/python analysis/analyze_controlled_checks.py data/controlados/personal-20261121-152127 --output analysis/controlados_personal_recalculado
pushd data/controlados/personal-20261121-152127
sha256sum --check SHA256SUMS
popd
```

Las ejecuciones de r01 fueron realizadas mediante herramientas del asistente,
no se atribuyen a una sesión manual de Roger. Código y textos tuvieron asistencia
de IA. Las fotos personales y la defensa del trabajo se acreditan por separado.
La sesión personal está respaldada por fotos y log; sus datos no se mezclan con r01.
