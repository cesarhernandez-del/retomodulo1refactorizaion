"""Reportes de la tienda: inventario, ventas y mas vendidos."""


import gestor

STOCK_MINIMO = 5


def formatear_dinero(valor: float) -> str:
    """Le da formato de dinero al numero (ej. 20 -> "$20", 20.0 -> "$20.0")."""
    return "$" + str(round(valor, 2))


def productos_stock_bajo() -> list[dict]:
    """Regresa la lista de productos con stock por debajo del minimo."""
    return [p for p in gestor.INVENTARIO.values() if p["stock"] < STOCK_MINIMO]


def reporte_inventario() -> str:
    """Arma el reporte del inventario, lo imprime y lo regresa como texto."""
    reporte = "===== INVENTARIO =====\n"
    valor_total = 0
    for producto in gestor.INVENTARIO.values():
        linea = producto["codigo"] + " | " + producto["nombre"] + " | "
        linea = linea + formatear_dinero(producto["precio"])
        linea = linea + " | stock: " + str(producto["stock"])
        if producto["stock"] < STOCK_MINIMO:
            linea = linea + "  <-- STOCK BAJO"
        reporte = reporte + linea + "\n"
        valor_total = valor_total + producto["precio"] * producto["stock"]
    reporte = reporte + "Valor total del inventario: "
    reporte = reporte + formatear_dinero(valor_total) + "\n"
    print(reporte)
    return reporte


def total_vendido() -> float:
    """Suma el total (con IVA) de todas las ventas registradas."""
    # suma en un ciclo a proposito: desde Python 3.12, sum() usa suma
    # compensada para floats y podria cambiar el resultado
    total = 0
    for venta in gestor.VENTAS:
        total = total + venta["total"]
    return round(total, 2)


def mas_vendidos(n: int = 3) -> list[tuple[str, int]]:
    """Regresa los n productos mas vendidos como lista de (codigo, unidades).

    En caso de empate conserva el orden de la primera venta de cada producto.
    """
    unidades_por_codigo = {}
    for venta in gestor.VENTAS:
        codigo = venta["codigo"]
        unidades_por_codigo[codigo] = (
            unidades_por_codigo.get(codigo, 0) + venta["cantidad"]
        )
    # sorted es estable tambien con reverse=True (no usar sorted(...)[::-1])
    ranking = sorted(
        unidades_por_codigo.items(), key=lambda par: par[1], reverse=True
    )
    return ranking[0:n]


def resumen_ventas() -> str:
    """Arma el resumen de ventas del dia, lo imprime y lo regresa."""
    resumen = "===== RESUMEN DE VENTAS =====\n"
    for venta in gestor.VENTAS:
        resumen = resumen + "Folio " + str(venta["folio"]) + ": " + venta["nombre"]
        resumen = resumen + " x" + str(venta["cantidad"]) + " = "
        resumen = resumen + formatear_dinero(venta["total"]) + "\n"
    resumen = resumen + "Numero de ventas: " + str(len(gestor.VENTAS)) + "\n"
    resumen = resumen + "Total del dia: " + formatear_dinero(total_vendido()) + "\n"
    print(resumen)
    return resumen
