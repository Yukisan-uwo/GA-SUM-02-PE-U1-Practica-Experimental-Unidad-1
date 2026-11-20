# Bitácora del equipo

**Integrantes:** Joseph (`JosephACS`) · Mera Jumbo Allison (`ameraj2-bit`) · Roger [apellido] · Mario Zambrano (`Yukisan-uwo`)

## Formato de cada entrada

### AAAA-MM-DD · Nombre de quien registra
- **Integrantes presentes:** quiénes trabajaron en esa sesión.
- **Commit(s):** `hash corto` — mensaje del commit.
- **Qué se hizo:** tarea realizada.
- **Problema encontrado:** dificultad o aspecto pendiente.
- **Solución y comprobación:** qué se cambió y cómo se verificó que funcionó.
- **Tiempo dedicado:** X h Y min.

---

## Registro de trabajo

### 2026-11-17 · Mario Zambrano
- **Integrantes presentes:** Mario Zambrano.
- **Commit(s):** `cf7cf95` — Estructura inicial para el documento latex, `443c61e` — Creacion de archivo para los requerimientos, `524499e` — Carpeta para los CSV y SHA256SUMS, `4ae980a` — Creacion de carpeta para codigo, `0cad7fe` — Creacion de carpeta para codigo, `70efbe7` — Creacion de carpeta para codigo, `57bcab3` — Creacion de carpeta para el analisis, `9aaf256` — Creacion de Bitacora.
- **Qué se hizo:** Organicé la estructura inicial del repositorio según la rúbrica: `analysis/`, `data/`, `src/` (con `sockets/`, `grpc/` y `proto/`) y `docs/sections/` para el informe en LaTeX, deje la plantilla del documento latex para saber que hacer y seguir segun la rúbrica, y deje la plantilla para la Bitacora. También repartí el trabajo entre los integrantes.
- **Problema encontrado:** Git no registra carpetas vacías, así que la estructura no se veía en GitHub.
- **Solución y comprobación:** Agregué archivos `.gitkeep` en las carpetas vacías y verifiqué en GitHub que aparecieran.
- **Tiempo dedicado:** 2 h 12 min.

### 2026-11-17 · Mera Jumbo Allison
- **Integrantes presentes:** Mera Jumbo Allison.
- **Commit(s):** `a3d0825` — Configura dependencias del proyecto y agrega gitignore.
- **Qué se hizo:** Cloné el repositorio, creé el entorno virtual con Python 3.14.0 e instalé grpcio, grpcio-tools, protobuf, pandas y matplotlib. Fijé sus versiones exactas en `requirements.txt` y agregué `.gitignore` para no subir `.venv/` ni `__pycache__/`.
- **Problema encontrado:** El `git push` falló con error 403 porque Windows tenía guardada la sesión de otra cuenta de GitHub sin permisos en el repo.
- **Solución y comprobación:** Borré la credencial de GitHub en el Administrador de credenciales de Windows, revisé con `git log` que el commit tuviera mi correo y volví a hacer push iniciando sesión con `ameraj2-bit`. El push terminó con `main -> main`.
- **Tiempo dedicado:** 45 min.

### 2026-11-18 · Mario Zambrano
- **Integrantes presentes:** Mario Zambrano.
- **Commit(s):** `b8c215e` — Implemente una configuracion inicial del benchmark.
- **Qué se hizo:** Implementé la configuración inicial del benchmark para las pruebas de sockets TCP y gRPC. Definí los tamaños de mensaje, la cantidad de envíos, las repeticiones y el calentamiento. Ejecuté pruebas desde PowerShell para comprobar la planificación de las 2000 mediciones y la selección individual de gRPC con mensajes de 10 KB.
- **Problema encontrado:** Los clientes TCP y gRPC todavía no están implementados, por lo que no es posible obtener las latencias reales.
- **Solución y comprobación:** Dejé preparado el planificador y comprobé que funciona con diferentes parámetros. También verifiqué que rechaza una configuración de cuatro repeticiones, ya que la rúbrica exige un mínimo de cinco.
- **Tiempo dedicado:** 53 minutos.

### 2026-11-18 · Mera Jumbo Allison
- **Integrantes presentes:** Mera Jumbo Allison.
- **Commit(s):**
  - `bbe177f` — Define servicio MessagingService en messaging.proto y genera codigo Python.
  - `cc48b85` — Implementa servidor gRPC por nodo con reloj Lamport.
- **Qué se hizo:** Acordé con Joseph el contrato común entre TCP y gRPC (campos de la solicitud y del acuse, conexión reutilizada, timeout de 2 s e interfaz `conectar/enviar/cerrar`). Creé `src/grpc/messaging.proto` con el servicio `MessagingService` y los mensajes `Request` y `Response`, y generé el código Python con `grpcio-tools`. Comprobé que un `Request` serializado ocupa 16 bytes. Después implementé `server_grpc.py`: cada nodo levanta su servidor gRPC en su puerto (5000, 5001 o 5002), actualiza el reloj de Lamport al recibir y responde con el acuse. Lo probé enviándole al nodo-A dos mensajes con timestamp 5, y el reloj pasó a 6 y luego a 7. Por ahora el servidor usa un reloj provisional hasta que Roger suba su módulo.
- **Problema encontrado:** La guía en PDF pide el `.proto` en `/src/grpc/` y el texto del SGA lo pide en `/proto/`, mientras que el repo tenía `src/proto/`. También, el comando `code .`
- **Solución y comprobación:** El equipo decidió seguir la guía y dejar el archivo en `src/grpc/messaging.proto`. 
- **Tiempo dedicado:** 1 hora.

### 2026-11-18 · Joseph Calderón Saltos
- **Integrantes presentes:** Joseph Calderón Saltos.
- **Commit(s):**
  - `3f1ae82` — Implemento comunicación TCP y registro de eventos.
  - `e89de69` — Create tcp_20_intercambios_2026-11-18.png.
  - `1be2d16` — Agrega evidencia de 20 intercambios TCP exitosos.
- **Qué se hizo:** Subí el servidor, el cliente y el registro CSV de TCP. Probé 20 intercambios con mensajes de 100 bytes y guardé la captura en `docs/evidencias/Joseph/`.
- **comprobación:** Inicié el servidor en una ventana aparte y repetí la prueba. Los 20 mensajes recibieron acuse `ok: True`. La ejecución fue una prueba funcional con `--run 0`, no una medición oficial del benchmark.
- **Tiempo dedicado:**  30 minutos


### 2026-11-19 · Mera Jumbo Allison
- **Integrantes presentes:** Mera Jumbo Allison.
- **Commit(s):**
  - `f42cc78` — Integra reloj Lamport compartido y registro CSV en servidor gRPC.
  - `4c04d92` — Implementa cliente gRPC con interfaz comun y medicion de latencia.
  - `baa84cb` — Agrega evidencias de 20 intercambios gRPC y prueba de nodo caido.
- **Qué se hizo:** Reemplacé el reloj provisional del servidor por el `LamportClock` de Roger. Hice que el envío del acuse cuente como evento nuevo (receive y luego tick), igual que en TCP, y agregué `registro_grpc.py` para guardar eventos y latencias en CSV con las mismas columnas que TCP. Implementé `client_grpc.py` con la misma interfaz que el cliente TCP (`conectar/enviar/cerrar`). Ejecuté 20 intercambios nodo-A → nodo-B con mensajes de 100 bytes y la secuencia de relojes coincidió con la de TCP (acuse final 79, reloj local 80). También probé enviar a un nodo apagado (nodo-C) y el cliente avisó que no pudo conectar, mientras el nodo-B seguía respondiendo.
- **Problema encontrado:** Al probar el servidor seguía saliendo el comportamiento anterior (respondía 6 en lugar de 7), y en la primera corrida de los 20 intercambios el cliente no pudo conectar.
- **Solución y comprobación:** El archivo no estaba guardado en VS Code (tenía el punto en la pestaña). Lo guardé, reinicié el servidor y respondió 7. En el segundo caso, el servidor del nodo-B no estaba encendido; lo levanté y los 20 envíos terminaron con `ok: True`. Validé además que un timestamp negativo devuelve `INVALID_ARGUMENT` sin tumbar el servidor.
- **Tiempo dedicado:** 45 min.

### 2026-11-19 · Mario Zambrano
- **Integrantes presentes:** Mario Zambrano.
- **Commit(s):** `a276d52` — Integre los clientes TCP y gRPC al benchmark.
- **Qué se hizo:** Actualicé `analysis/benchmark.py` para conectarlo con los clientes TCP y gRPC desarrollados por mis compañeros. Incorporé la ejecución de pruebas reales utilizando la interfaz común de ambos clientes y conservé las opciones de configuración del experimento. Probé la comunicación con el servidor `nodo-B` en el puerto 5001, realizando tres envíos de 100 bytes por cada mecanismo. En ambos casos se recibieron correctamente los tres acuses con `ok=True` y se mostraron los tiempos RTT. También guardé dos capturas de estas pruebas en `docs/evidencias/Mario/`.
- **Problema encontrado:** Al intentar iniciar el servidor gRPC, apareció un error por incompatibilidad entre la versión de Protobuf utilizada para generar `messaging_pb2.py` (7.35.1) y la instalada en mi computadora (6.33.6).
- **Solución y comprobación:** Creé un entorno virtual `.venv` e instalé las dependencias definidas en `requirements.txt`. Después pude iniciar el servidor gRPC y ejecutar las tres solicitudes correctamente. La prueba TCP también terminó sin errores. Por ahora las pruebas son de integración y no corresponden a las mediciones oficiales de 100 envíos.
- **Tiempo dedicado:** 48 minutos.


### 2026-11-19 · Joseph Calderón Saltos
- **Integrantes presentes:** Joseph Calderón Saltos.
- **Commit(s):**
  - `a613e00` — Agrega referencias de TCP, Lamport y RPC.
  - `db0ba65` — Documenta la implementación TCP.
- **Qué se hizo:** Agregué las referencias bibliográficas y documenté el funcionamiento del cliente y el servidor TCP, junto con un fragmento del código real.
- **Problema encontrado:** El CSV de los 20 intercambios todavía no está en el repositorio. También falta confirmar con Roger la regla del reloj de Lamport al enviar el acuse.
- **Solución y comprobación:** Contrasté la descripción con los archivos actuales del cliente y el servidor. Dejé la parte de los 20 intercambios para completarla cuando se incorpore el CSV y se confirme la regla del reloj.
- **Tiempo dedicado:** 35 minutos.

### 2026-11-20 · Mario Zambrano
- **Integrantes presentes:** Mario Zambrano.
- **Commit(s):** `5903b17` — Objetivos e hipotesis previa al benchmark.
- **Qué se hizo:** Redacté los objetivos generales y específicos de la práctica, tomando en cuenta los requisitos del experimento con sockets TCP, gRPC y relojes de Lamport. También establecí la hipótesis de que TCP podría presentar una menor latencia media que gRPC en localhost, considerando mensajes de 100 bytes y 10 KB. Para fundamentarla, utilicé las características de las implementaciones desarrolladas por el equipo y referencias bibliográficas incluidas en `referencias.bib`. La hipótesis quedó registrada en el repositorio antes de ejecutar las mediciones oficiales.
- **Problema encontrado:** Ningun problema.
- **Solución y comprobación:** Todo bien.
- **Tiempo dedicado:** 32 minutos.

### 2026-11-20 · Mario Zambrano

- **Integrantes presentes:** Mario Zambrano.
- **Commit(s):** `a33f110` — Benchmark real y analisis estadistico TCP gRPC.
- **Qué se hizo:** Ejecuté las mediciones de latencia y rendimiento de los clientes TCP y gRPC utilizando el benchmark desarrollado anteriormente. Para cada mecanismo se realizaron cinco corridas de 100 envíos con mensajes de 100 y 10240 bytes, descartando una corrida previa de calentamiento por tamaño. En total se obtuvieron 2000 mediciones válidas, sin acuses fallidos ni tiempos RTT inválidos. Después desarrollé y ejecuté `analysis/analisis_resultados.py` para calcular la media, mediana, desviación estándar, percentil 95 y rendimiento a partir de los CSV originales. Los resultados mostraron una latencia media de 0,122 y 0,197 ms para TCP, frente a 0,547 y 0,564 ms para gRPC, respectivamente. También se generaron automáticamente las tablas LaTeX y los gráficos de cajas y barras con intervalos. Guardé las capturas de ejecución y registré los hashes SHA-256 de los cuatro CSV consolidados.
- **Problema encontrado:** Al revisar las tablas generadas, algunos caracteres acentuados aparecían incorrectamente en la terminal de PowerShell. Además, fue necesario distinguir los CSV oficiales de los registros automáticos producidos por los clientes durante las pruebas preliminares.
- **Solución y comprobación:** Verifiqué mediante Python que las tablas estaban correctamente codificadas en UTF-8. Comprobé también que cada condición experimental contenía 500 mediciones, distribuidas en cinco corridas de 100 envíos. El script confirmó la validez de los 2000 registros y generó los resultados sin modificar los archivos originales. Finalmente, creé `data/SHA256SUMS` y verifiqué que los cuatro archivos consolidados coincidieran con sus hashes. Los registros adicionales de eventos y latencias permanecen conservados para las pruebas pendientes.
- **Tiempo dedicado:** 1 hora 5 minutos.

### 2026-11-20 · Mario Zambrano

- **Integrantes presentes:** Mario Zambrano.
- **Commit(s):** `253b344` — Protocolo y condiciones del benchmark.
- **Qué se hizo:** Completé la sección 10 del informe LaTeX, correspondiente al protocolo experimental. Documenté las características de la computadora utilizada, las versiones de Python y sus bibliotecas, y las condiciones bajo las que realicé las mediciones TCP y gRPC. También expliqué cómo se organizaron las cinco corridas de 100 envíos para cada mecanismo y tamaño de mensaje, incluyendo las pruebas de calentamiento que se descartaron. Incorporé las fórmulas utilizadas para calcular la latencia RTT y el rendimiento en mensajes por segundo, una tabla con la distribución de las 2000 mediciones y el procedimiento de validación de los CSV mediante SHA-256.
- **Problema encontrado:** Era necesario diferenciar las mediciones secuenciales del benchmark de las pruebas con tres nodos y clientes concurrentes, para evitar presentar como ejecutadas actividades que todavía corresponden a otros integrantes. También se identificaron algunas limitaciones de la comparación, como las diferencias de serialización entre TCP y gRPC y el uso de localhost.
- **Solución y comprobación:** Revisé el contenido de la sección tomando como referencia el código del benchmark, los clientes desarrollados por el equipo y los resultados obtenidos anteriormente. Dejé documentadas las condiciones reales de las mediciones y sus limitaciones. La prueba de concurrencia quedó identificada como una evaluación independiente, cuyos resultados se incorporarán cuando Roger proporcione las evidencias correspondientes.
- **Tiempo dedicado:** 32 minutos.

### 2026-11-20 · Mario Zambrano
- **Integrantes presentes:** Mario Zambrano.
- **Commit(s):** `a354f04` — Latencias, rendimiento y graficas TCP gRPC.
- **Qué se hizo:** Completé la sección 11 del informe LaTeX, correspondiente a los resultados del benchmark. Incorporé las tablas de estadísticas descriptivas y rendimiento que se generaron anteriormente con Python, junto con el gráfico de cajas y el gráfico de barras. También redacté la explicación de los resultados, comparando las latencias, la dispersión de los tiempos y los mensajes procesados por segundo para TCP y gRPC. Se mantuvo la distinción entre las mediciones secuenciales realizadas y las pruebas de concurrencia que corresponden a otra parte del trabajo.
- **Problema encontrado:** Al revisar el PDF observé que algunas figuras se desplazaban de la posición en la que estaban colocadas en el archivo LaTeX, lo que provocaba una distribución poco adecuada del texto.
- **Solución y comprobación:** Ajusté el tamaño y la posición de las figuras utilizando el paquete `float` y la opción `[H]`.
- **Tiempo dedicado:** 36 minutos.

### 2026-11-20 · Mera Jumbo Allison
- **Integrantes presentes:** Mera Jumbo Allison.
- **Commit(s):**
  - `1b5dc15` — Documenta implementacion gRPC con contrato, errores y 20 intercambios.
  - `685df58` — Agrega seccion 03 de comunicacion y referencias oficiales de gRPC, Protobuf y RMI.
  - `41bbf64` — Agrega respuesta sobre efecto de un nodo caido en los relojes Lamport.
  - `88217e1` — Agrega analisis de tipado y manejo de errores en gRPC a la discusion.
  - `18b317e` — Redacta conclusion individual sobre implementacion gRPC.
  - `986c7d8` — Corrección ortográfica.
- **Qué se hizo:** Redacté la sección 08 (implementación gRPC) con el contrato, fragmentos del servidor y del cliente, la tabla de errores y los 20 intercambios. Redacté la sección 03 (sockets, RPC, gRPC, Protocol Buffers y RMI) con un diagrama de secuencia en TikZ y agregué tres referencias oficiales al `.bib`. Respondí la pregunta del anexo sobre la caída de un nodo, escribí mi parte de la discusión sobre tipado y manejo de errores, y mi conclusión individual relacionada con el PFC.
- **Problema encontrado:** Las tablas y figuras de la sección 08 se movían a otras partes del documento (una figura quedó en la 4.3), y una cita atribuía a un artículo algo que no se pudo verificar. Además, mi conclusión tenía un error de tipeo.
- **Solución y comprobación:** Fijé las tablas y figuras para que queden después del párrafo que las menciona y lo comprobé compilando en TeXstudio. Cambié la cita por la documentación oficial de gRPC y el artículo de Niswar, que sí lo respaldan. El error de la conclusión lo corregí desde GitHub.
- **Tiempo dedicado:** 2 horas 30 min.
