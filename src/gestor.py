"""Modulo principal del gestor de inventario y ventas de "La Esquina".

Aqui vive casi toda la logica del negocio. Historicamente este archivo
lo fueron parchando varias personas, asi que hay de todo un poco.
"""

from datetime import datetime

# ---------------------------------------------------------------
# Reglas de negocio: descuentos e impuestos
# ---------------------------------------------------------------
UMBRAL_VOLUMEN_ALTO = 1000
TASA_VOLUMEN_ALTO = 0.10
UMBRAL_VOLUMEN_MEDIO = 500
TASA_VOLUMEN_MEDIO = 0.05
PREFIJO_VIP = "VIP"
MONTO_MINIMO_VIP = 200
TASA_VIP = 0.02
TASA_IVA = 0.16

# ---------------------------------------------------------------
# Estado global de la aplicacion (inventario, ventas y contadores)
# ---------------------------------------------------------------
INVENTARIO = {}
VENTAS = []
contadorVentas = 0
ultimo_error = ""


def reiniciar_sistema():
    """Borra todo el estado del sistema (inventario, ventas y folios)."""
    global contadorVentas, ultimo_error
    INVENTARIO.clear()
    VENTAS.clear()
    contadorVentas = 0
    ultimo_error = ""


def agregarProducto(codigo, nombre, precio, stock):
    # valida los datos y da de alta un producto en el inventario
    global ultimo_error
    if codigo is None or codigo == "":
        ultimo_error = "codigo vacio"
        return False
    if codigo in INVENTARIO:
        ultimo_error = "el producto ya existe"
        return False
    if precio <= 0:
        ultimo_error = "precio invalido"
        return False
    if stock < 0:
        ultimo_error = "stock invalido"
        return False
    x = {}
    x["codigo"] = codigo
    x["nombre"] = nombre
    x["precio"] = precio
    x["stock"] = stock
    INVENTARIO[codigo] = x
    return True


def eliminar_producto(codigo):
    """Quita un producto del inventario. Regresa False si no existe."""
    global ultimo_error
    if codigo in INVENTARIO:
        del INVENTARIO[codigo]
        return True
    ultimo_error = "producto no existe"
    return False


def actualizar_stock(codigo, cantidad):
    """Suma unidades al stock (o resta si la cantidad es negativa)."""
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return False
    aux = INVENTARIO[codigo]["stock"] + cantidad
    if aux < 0:
        ultimo_error = "el stock no puede quedar negativo"
        return False
    INVENTARIO[codigo]["stock"] = aux
    return True


def buscarProducto(texto):
    # busca productos cuyo nombre contenga el texto (sin importar mayusculas)
    temp2 = []
    for k in INVENTARIO:
        if texto.lower() in INVENTARIO[k]["nombre"].lower():
            temp2.append(INVENTARIO[k])
    return temp2


def descuento_por_volumen(subtotal: float) -> float:
    """Descuento segun el monto de la compra.

    Regresa el entero 0 (no 0.0) cuando no aplica ningun descuento.
    """
    if subtotal >= UMBRAL_VOLUMEN_ALTO:
        return subtotal * TASA_VOLUMEN_ALTO
    if subtotal >= UMBRAL_VOLUMEN_MEDIO:
        return subtotal * TASA_VOLUMEN_MEDIO
    return 0


def descuento_vip(subtotal: float, descuento: float, cliente: str | None) -> float:
    """Descuento extra para clientes VIP.

    Aplica si el codigo de cliente empieza con PREFIJO_VIP y la compra,
    ya con el descuento por volumen, pasa de MONTO_MINIMO_VIP. El extra
    se calcula sobre el subtotal bruto, no sobre el monto con descuento.
    """
    if (
        cliente
        and cliente.startswith(PREFIJO_VIP)
        and subtotal - descuento > MONTO_MINIMO_VIP
    ):
        return subtotal * TASA_VIP
    return 0


def validar_venta(codigo: str | None, cantidad: int | None) -> str | None:
    """Regresa el motivo por el que la venta no procede, o None si es valida.

    Las condiciones se revisan en este orden: codigo, existencia,
    cantidad y stock.
    """
    if codigo is None or codigo == "":
        return "codigo vacio"
    if codigo not in INVENTARIO:
        return "producto no existe"
    # "not ... > 0" en lugar de "<= 0" para que una cantidad NaN siga
    # siendo invalida, como en el codigo original
    if cantidad is None or not cantidad > 0:
        return "cantidad invalida"
    if not INVENTARIO[codigo]["stock"] >= cantidad:
        return "stock insuficiente"
    return None


def armar_ticket(venta: dict, descuento: float) -> str:
    """Arma el ticket en texto plano de una venta ya calculada.

    La linea de descuento depende del descuento sin redondear.
    """
    ticket = "TIENDA LA ESQUINA\n"
    ticket = ticket + "----------------------------\n"
    ticket = ticket + "Folio: " + str(venta["folio"]) + "\n"
    ticket = ticket + venta["nombre"] + " x" + str(venta["cantidad"]) + "\n"
    ticket = ticket + "Subtotal: $" + str(venta["subtotal"]) + "\n"
    if descuento > 0:
        ticket = ticket + "Descuento: -$" + str(venta["descuento"]) + "\n"
    ticket = ticket + "IVA: $" + str(venta["impuesto"]) + "\n"
    ticket = ticket + "TOTAL: $" + str(venta["total"]) + "\n"
    return ticket


def registrar_venta(
    codigo: str | None, cantidad: int | None, cliente: str | None = ""
) -> dict | None:
    """Registra una venta: descuenta el stock, asigna folio y arma el ticket.

    Si la venta no procede regresa None y deja el motivo en ultimo_error.
    """
    global contadorVentas, ultimo_error
    error = validar_venta(codigo, cantidad)
    if error is not None:
        ultimo_error = error
        return None
    producto = INVENTARIO[codigo]
    subtotal = producto["precio"] * cantidad
    descuento = descuento_por_volumen(subtotal)
    descuento = descuento + descuento_vip(subtotal, descuento, cliente)
    base = subtotal - descuento
    impuesto = base * TASA_IVA
    total = round(base + impuesto, 2)
    producto["stock"] = producto["stock"] - cantidad
    contadorVentas = contadorVentas + 1
    venta = {
        "folio": contadorVentas,
        "codigo": codigo,
        "nombre": producto["nombre"],
        "cantidad": cantidad,
        "subtotal": round(subtotal, 2),
        "descuento": round(descuento, 2),
        "impuesto": round(impuesto, 2),
        "total": total,
        "cliente": cliente,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    venta["ticket"] = armar_ticket(venta, descuento)
    VENTAS.append(venta)
    return venta


def cotizar(codigo: str, cantidad: int) -> float | None:
    """Calcula cuanto costaria una compra sin registrar la venta.

    No aplica el descuento VIP ni revisa el stock.
    """
    global ultimo_error
    if codigo not in INVENTARIO:
        ultimo_error = "producto no existe"
        return None
    if cantidad is None or cantidad <= 0:
        ultimo_error = "cantidad invalida"
        return None
    subtotal = INVENTARIO[codigo]["precio"] * cantidad
    base = subtotal - descuento_por_volumen(subtotal)
    total = base + base * TASA_IVA
    return round(total, 2)
