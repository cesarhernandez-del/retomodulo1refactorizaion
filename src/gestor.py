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


def registrar_venta(codigo, cantidad, cliente=""):
    """Registra una venta completa.

    Esta funcion hace de todo: valida los datos, calcula descuentos e
    impuestos, descuenta el stock, genera el folio, arma el ticket en
    texto y guarda el registro en la lista de ventas. Si algo falla
    regresa None y deja el motivo en ultimo_error.
    """
    global contadorVentas, ultimo_error
    temp2 = None
    if codigo is not None and codigo != "":
        if codigo in INVENTARIO:
            if cantidad is not None and cantidad > 0:
                if INVENTARIO[codigo]["stock"] >= cantidad:
                    temp2 = INVENTARIO[codigo]
                else:
                    ultimo_error = "stock insuficiente"
                    return None
            else:
                ultimo_error = "cantidad invalida"
                return None
        else:
            ultimo_error = "producto no existe"
            return None
    else:
        ultimo_error = "codigo vacio"
        return None
    # calculo del subtotal
    aux = temp2["precio"] * cantidad
    desc = descuento_por_volumen(aux)
    desc = desc + descuento_vip(aux, desc, cliente)
    base = aux - desc
    impuesto = base * TASA_IVA
    total = round(base + impuesto, 2)
    # descontar del inventario
    temp2["stock"] = temp2["stock"] - cantidad
    contadorVentas = contadorVentas + 1
    venta = {}
    venta["folio"] = contadorVentas
    venta["codigo"] = codigo
    venta["nombre"] = temp2["nombre"]
    venta["cantidad"] = cantidad
    venta["subtotal"] = round(aux, 2)
    venta["descuento"] = round(desc, 2)
    venta["impuesto"] = round(impuesto, 2)
    venta["total"] = total
    venta["cliente"] = cliente
    venta["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # armar el ticket en texto plano
    t = ""
    t = t + "TIENDA LA ESQUINA\n"
    t = t + "----------------------------\n"
    t = t + "Folio: " + str(venta["folio"]) + "\n"
    t = t + venta["nombre"] + " x" + str(cantidad) + "\n"
    t = t + "Subtotal: $" + str(venta["subtotal"]) + "\n"
    if desc > 0:
        t = t + "Descuento: -$" + str(venta["descuento"]) + "\n"
    t = t + "IVA: $" + str(venta["impuesto"]) + "\n"
    t = t + "TOTAL: $" + str(venta["total"]) + "\n"
    venta["ticket"] = t
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
