"""Analiza los CSV reales del benchmark TCP/gRPC de la práctica PE-U1.

Entrada (sin modificar):
    data/latency_sockets.csv, data/runs_sockets.csv
    data/latency_grpc.csv, data/runs_grpc.csv

Salida derivada, reproducible:
    analysis/resumen_latencias.csv
    analysis/resumen_rendimiento.csv
    docs/tablas/estadisticas.tex
    docs/tablas/rendimiento.tex
    docs/figures/boxplot.png
    docs/figures/barras_intervalos.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Permite generar figuras sin abrir una ventana interactiva.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data"
ANALISIS = RAIZ / "analysis"
TABLAS = RAIZ / "docs" / "tablas"
FIGURAS = RAIZ / "docs" / "figures"
MECANISMOS = ("TCP", "GRPC")
TAMANOS = (100, 10240)
CORRIDAS = (1, 2, 3, 4, 5)
ENVIOS_POR_CORRIDA = 100
ENTRADAS = {
    "TCP": (DATOS / "latency_sockets.csv", DATOS / "runs_sockets.csv"),
    "GRPC": (DATOS / "latency_grpc.csv", DATOS / "runs_grpc.csv"),
}

def leer_csv(ruta: Path, campos: set[str]) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"Falta el archivo de datos reales: {ruta}")
    datos = pd.read_csv(ruta)
    faltantes = campos.difference(datos.columns)
    if faltantes:
        raise ValueError(f"{ruta.name}: faltan columnas {sorted(faltantes)}")
    return datos


def normalizar_mecanismo(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.upper().str.strip()


def validar_latencias(datos: pd.DataFrame, mecanismo: str) -> pd.DataFrame:
    datos = datos.copy()
    datos["mecanismo"] = normalizar_mecanismo(datos["mecanismo"])
    for campo in ("tamano_bytes", "corrida", "intento", "latencia_ms"):
        datos[campo] = pd.to_numeric(datos[campo], errors="raise")
    correctos = datos["ok"].astype(str).str.lower().str.strip().eq("true")
    if not correctos.all():
        raise ValueError(f"{mecanismo}: hay {int((~correctos).sum())} acuses fallidos")
    if not np.isfinite(datos["latencia_ms"]).all() or (datos["latencia_ms"] <= 0).any():
        raise ValueError(f"{mecanismo}: hay latencias no finitas, nulas o negativas")
    if set(datos["mecanismo"]) != {mecanismo}:
        raise ValueError(f"Archivo {mecanismo}: identificadores de mecanismo inconsistentes")
    if datos.duplicated(subset=["tamano_bytes", "corrida", "intento"]).any():
        raise ValueError(f"{mecanismo}: existen intentos duplicados dentro de una condición")
    grupos = datos.groupby(["tamano_bytes", "corrida"]).size().to_dict()
    esperado = {(t, c): ENVIOS_POR_CORRIDA for t in TAMANOS for c in CORRIDAS}
    if grupos != esperado:
        raise ValueError(f"{mecanismo}: las corridas no contienen 100 envíos en las 10 condiciones. "
                         f"Encontrado: {grupos}")
    return datos


def validar_rendimiento(datos: pd.DataFrame, mecanismo: str) -> pd.DataFrame:
    datos = datos.copy()
    datos["mecanismo"] = normalizar_mecanismo(datos["mecanismo"])
    for campo in ("tamano_bytes", "corrida", "mensajes", "duracion_s", "mensajes_por_segundo"):
        datos[campo] = pd.to_numeric(datos[campo], errors="raise")
    if set(datos["mecanismo"]) != {mecanismo}:
        raise ValueError(f"Archivo de rendimiento {mecanismo}: mecanismo incorrecto")
    grupos = datos.groupby(["tamano_bytes", "corrida"]).size().to_dict()
    esperado = {(t, c): 1 for t in TAMANOS for c in CORRIDAS}
    if grupos != esperado:
        raise ValueError(f"{mecanismo}: faltan corridas de rendimiento o hay duplicadas: {grupos}")
    if (datos["mensajes"] != ENVIOS_POR_CORRIDA).any():
        raise ValueError(f"{mecanismo}: cantidad de mensajes inconsistente")
    if not np.isfinite(datos[["duracion_s", "mensajes_por_segundo"]].to_numpy()).all():
        raise ValueError(f"{mecanismo}: duración o rendimiento no finito")
    if (datos["duracion_s"] <= 0).any() or (datos["mensajes_por_segundo"] <= 0).any():
        raise ValueError(f"{mecanismo}: duración o rendimiento no positivo")
    calculado = datos["mensajes"] / datos["duracion_s"]
    if not np.allclose(datos["mensajes_por_segundo"], calculado, rtol=0.001, atol=0.02):
        raise ValueError(f"{mecanismo}: rendimiento incompatible con cantidad/duración")
    return datos

def cargar_y_validar() -> tuple[pd.DataFrame, pd.DataFrame]:
    todas_latencias = []
    todos_rendimientos = []
    for mecanismo, (ruta_l, ruta_r) in ENTRADAS.items():
        lat = leer_csv(ruta_l, {"mecanismo", "tamano_bytes", "corrida", "intento", "latencia_ms", "ok"})
        rend = leer_csv(ruta_r, {"mecanismo", "tamano_bytes", "corrida", "mensajes", "duracion_s", "mensajes_por_segundo"})
        todas_latencias.append(validar_latencias(lat, mecanismo))
        todos_rendimientos.append(validar_rendimiento(rend, mecanismo))
    return pd.concat(todas_latencias, ignore_index=True), pd.concat(todos_rendimientos, ignore_index=True)


def calcular_estadisticas(latencias: pd.DataFrame, rendimientos: pd.DataFrame):
    estadisticas = []
    resumen_rendimiento = []
    for mecanismo in MECANISMOS:
        for tamano in TAMANOS:
            sub = latencias[(latencias["mecanismo"] == mecanismo) & (latencias["tamano_bytes"] == tamano)]
            valores = sub["latencia_ms"]
            estadisticas.append({
                "mecanismo": mecanismo,
                "tamano_bytes": tamano,
                "n": len(sub),
                "media_ms": valores.mean(),
                "mediana_ms": valores.median(),
                "desviacion_ms": valores.std(ddof=1),
                "p95_ms": valores.quantile(0.95),
            })
            corridas = rendimientos[(rendimientos["mecanismo"] == mecanismo) & (rendimientos["tamano_bytes"] == tamano)]
            tasas = corridas["mensajes_por_segundo"]
            resumen_rendimiento.append({
                "mecanismo": mecanismo,
                "tamano_bytes": tamano,
                "corridas": len(corridas),
                "rendimiento_medio": tasas.mean(),
                "rendimiento_desviacion": tasas.std(ddof=1),
            })
    return pd.DataFrame(estadisticas), pd.DataFrame(resumen_rendimiento)


def formato_carga(tamano: int) -> str:
    return "100 B" if tamano == 100 else "10 KiB (10240 B)"


def guardar_tablas(estadisticas: pd.DataFrame, rendimiento: pd.DataFrame) -> None:
    # Estas tablas se producen automáticamente a partir de los CSV; no se editan a mano.
    lineas = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\resizebox{\linewidth}{!}{%", r"\begin{tabular}{llrrrrr}", r"\toprule",
        r"Mecanismo & Carga útil & $n$ & Media (ms) & Mediana (ms) & DE (ms) & P95 (ms) \\",
        r"\midrule",
    ]
    for fila in estadisticas.itertuples(index=False):
        nombre = "gRPC" if fila.mecanismo == "GRPC" else "TCP"
        lineas.append(f"{nombre} & {formato_carga(fila.tamano_bytes)} & {fila.n} & "
                      f"{fila.media_ms:.3f} & {fila.mediana_ms:.3f} & "
                      f"{fila.desviacion_ms:.3f} & {fila.p95_ms:.3f} " + r"\\")
    lineas += [r"\bottomrule", r"\end{tabular}%", r"}",
               r"\caption{Latencia RTT por mecanismo y tamaño de carga útil. DE: desviación estándar muestral; P95: percentil 95.}",
               r"\label{tab:estadisticas_rtt}", r"\end{table}"]
    (TABLAS / "estadisticas.tex").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    lineas = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\resizebox{\linewidth}{!}{%", r"\begin{tabular}{llrrr}", r"\toprule",
        r"Mecanismo & Carga útil & Corridas & Media (mensajes/s) & DE (mensajes/s) \\",
        r"\midrule",
    ]
    for fila in rendimiento.itertuples(index=False):
        nombre = "gRPC" if fila.mecanismo == "GRPC" else "TCP"
        lineas.append(f"{nombre} & {formato_carga(fila.tamano_bytes)} & "
                      f"{fila.corridas} & {fila.rendimiento_medio:.2f} & "
                      f"{fila.rendimiento_desviacion:.2f} " + r"\\")
    lineas += [r"\bottomrule", r"\end{tabular}%", r"}",
               r"\caption{Rendimiento observado, calculado como mensajes confirmados divididos entre la duración de cada corrida; media y desviación estándar de cinco corridas.}",
               r"\label{tab:rendimiento}", r"\end{table}"]
    (TABLAS / "rendimiento.tex").write_text("\n".join(lineas) + "\n", encoding="utf-8")

def guardar_boxplot(latencias: pd.DataFrame) -> None:
    series, etiquetas = [], []
    for mecanismo in MECANISMOS:
        for tamano in TAMANOS:
            muestras = latencias.loc[
                (latencias["mecanismo"] == mecanismo) & (latencias["tamano_bytes"] == tamano),
                "latencia_ms",
            ].to_numpy()
            series.append(muestras)
            etiquetas.append(f"{'gRPC' if mecanismo == 'GRPC' else 'TCP'}\n{formato_carga(tamano)}")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.boxplot(series, tick_labels=etiquetas, showfliers=True)
    ax.set_ylabel("Latencia RTT (ms)")
    ax.set_title("Distribución de latencias por mecanismo y carga útil")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURAS / "boxplot.png", dpi=300)
    plt.close(fig)


def guardar_barras(latencias: pd.DataFrame) -> None:
    etiquetas, medias, dispersion = [], [], []
    for mecanismo in MECANISMOS:
        for tamano in TAMANOS:
            sub = latencias[(latencias["mecanismo"] == mecanismo) & (latencias["tamano_bytes"] == tamano)]
            medias_corrida = sub.groupby("corrida")["latencia_ms"].mean()
            etiquetas.append(f"{'gRPC' if mecanismo == 'GRPC' else 'TCP'}\n{formato_carga(tamano)}")
            medias.append(medias_corrida.mean())
            dispersion.append(medias_corrida.std(ddof=1))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(etiquetas, medias, yerr=dispersion, capsize=5)
    ax.set_ylabel("Latencia RTT media (ms)")
    ax.set_title("Latencia media y variación entre las cinco corridas")
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    fig.text(0.5, 0.015,
             "Barras: media de las cinco medias por corrida; intervalos: ±1 desviación estándar entre corridas.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(FIGURAS / "barras_intervalos.png", dpi=300)
    plt.close(fig)

def main() -> int:
    latencias, rendimientos = cargar_y_validar()
    estadisticas, rendimiento = calcular_estadisticas(latencias, rendimientos)
    TABLAS.mkdir(parents=True, exist_ok=True)
    FIGURAS.mkdir(parents=True, exist_ok=True)
    estadisticas.to_csv(ANALISIS / "resumen_latencias.csv", index=False, float_format="%.6f")
    rendimiento.to_csv(ANALISIS / "resumen_rendimiento.csv", index=False, float_format="%.6f")
    guardar_tablas(estadisticas, rendimiento)
    guardar_boxplot(latencias)
    guardar_barras(latencias)
    print("VALIDACIÓN SATISFACTORIA: 2.000 RTT válidos; 20 corridas medidas; "
          "100 registros por corrida y condición.")
    print("\nLATENCIAS (ms)\n" + estadisticas.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print("\nRENDIMIENTO (mensajes/s)\n" + rendimiento.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
    print("\nArchivos generados:")
    for ruta in (ANALISIS / "resumen_latencias.csv", ANALISIS / "resumen_rendimiento.csv",
                 TABLAS / "estadisticas.tex", TABLAS / "rendimiento.tex",
                 FIGURAS / "boxplot.png", FIGURAS / "barras_intervalos.png"):
        print(" -", ruta.relative_to(RAIZ))
    print("\nLos CSV originales de data/ no fueron modificados.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
        sys.exit(f"ERROR DE VALIDACIÓN: {error}")