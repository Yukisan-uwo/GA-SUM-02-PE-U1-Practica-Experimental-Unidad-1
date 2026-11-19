"""Planificador inicial del experimento TCP/gRPC.

No realiza envíos ni genera resultados. La medición se integrará cuando
los clientes TCP y gRPC del equipo estén disponibles.
"""

import argparse

MECANISMOS = ("tcp", "grpc")
TAMANOS_BYTES = (100, 10 * 1024)
PUERTOS_NODOS = {"nodo-A": 5000, "nodo-B": 5001, "nodo-C": 5002}


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Muestra el plan de medición TCP/gRPC sin ejecutar envíos."
    )
    parser.add_argument(
        "--mecanismo", choices=("ambos", *MECANISMOS), default="ambos",
        help="Mecanismo que se desea planificar (predeterminado: ambos).",
    )
    parser.add_argument(
        "--tamano", choices=("ambos", "100", "10240"), default="ambos",
        help="Tamaño de carga útil en bytes (predeterminado: ambos).",
    )
    parser.add_argument(
        "--repeticiones", type=int, default=5,
        help="Corridas medidas por condición (mínimo: 5).",
    )
    parser.add_argument(
        "--envios", type=int, default=100,
        help="Envíos por corrida (mínimo: 100).",
    )
    parser.add_argument(
        "--calentamiento", type=int, default=1,
        help="Corridas previas no contabilizadas (mínimo: 1).",
    )
    return parser


def main() -> None:
    parser = construir_parser()
    args = parser.parse_args()

    if args.repeticiones < 5:
        parser.error("La rúbrica exige al menos 5 repeticiones medidas.")
    if args.envios < 100:
        parser.error("La rúbrica exige 100 envíos por corrida como mínimo.")
    if args.calentamiento < 1:
        parser.error("Se requiere al menos una corrida previa de calentamiento.")

    mecanismos = MECANISMOS if args.mecanismo == "ambos" else (args.mecanismo,)
    tamanos = TAMANOS_BYTES if args.tamano == "ambos" else (int(args.tamano),)

    print("PLAN EXPERIMENTAL — SOLO CONFIGURACIÓN (SIN MEDICIONES)")
    print("Nodos:", ", ".join(f"{nombre}:{puerto}" for nombre, puerto in PUERTOS_NODOS.items()))
    print("Métrica futura: latencia de ida y vuelta (RTT) con time.perf_counter().")
    print("Tamaños expresados en bytes de carga útil, no del mensaje serializado.")
    print()

    for mecanismo in mecanismos:
        for tamano in tamanos:
            print(
                f"- {mecanismo.upper():4} | {tamano:5} bytes | "
                f"{args.repeticiones} corridas x {args.envios} envíos | "
                f"{args.calentamiento} corrida(s) de calentamiento descartada(s)"
            )

    n_condiciones = len(mecanismos) * len(tamanos)
    print(f"\nTotal de envíos planificados para medición: {n_condiciones * args.repeticiones * args.envios}")
    print(f"Envíos de calentamiento (no contabilizados): {n_condiciones * args.calentamiento * args.envios}")
    print("Nota: aún no se han conectado clientes TCP/gRPC ni generado archivos CSV.")
    print("La prueba de concurrencia de tres clientes se incorporará por separado.")


if __name__ == "__main__":
    main()
