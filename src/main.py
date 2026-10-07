"""Punto de entrada del gestor de tienda (menu interactivo en consola)."""

from collections.abc import Callable

import almacen
import gestor
import reportes

ARCHIVO = "datos_ejemplo.json"


def pedir_numero(mensaje: str) -> float:
    """Pide un numero al usuario hasta que escriba algo valido."""
    while True:
        texto = input(mensaje)
        try:
            return float(texto)
        except ValueError:
            print("Eso no es un numero, intenta de nuevo.")


def cargar_datos_iniciales() -> None:
    """Carga el archivo de datos si existe.

    Avisa "Datos cargados" aunque la carga falle (comportamiento original).
    """
    if almacen.hay_archivo(ARCHIVO):
        almacen.cargar_datos(ARCHIVO)
        print("Datos cargados de", ARCHIVO)


def mostrar_opciones() -> None:
    """Imprime las opciones del menu."""
    print("")
    print("1) Agregar producto")
    print("2) Registrar venta")
    print("3) Cotizar")
    print("4) Reporte de inventario")
    print("5) Resumen de ventas")
    print("6) Mas vendidos")
    print("7) Alertas de stock bajo")
    print("8) Guardar y salir")


def opcion_agregar_producto() -> None:
    """Opcion 1: pide los datos de un producto y lo da de alta."""
    codigo = input("Codigo: ")
    nombre = input("Nombre: ")
    precio = pedir_numero("Precio: ")
    stock = int(pedir_numero("Stock inicial: "))
    if gestor.agregarProducto(codigo, nombre, precio, stock):
        print("Producto agregado.")
    else:
        print("Error:", gestor.ultimo_error)


def opcion_registrar_venta() -> None:
    """Opcion 2: registra una venta e imprime su ticket."""
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    cliente = input("Codigo de cliente (enter si no tiene): ")
    venta = gestor.registrar_venta(codigo, cantidad, cliente)
    if venta is not None:
        print(venta["ticket"])
    else:
        print("Error:", gestor.ultimo_error)


def opcion_cotizar() -> None:
    """Opcion 3: calcula el total de una compra sin registrarla."""
    codigo = input("Codigo del producto: ")
    cantidad = int(pedir_numero("Cantidad: "))
    total = gestor.cotizar(codigo, cantidad)
    if total is not None:
        print("Total estimado (con IVA): $" + str(total))
    else:
        print("Error:", gestor.ultimo_error)


def opcion_reporte_inventario() -> None:
    """Opcion 4: imprime el reporte de inventario."""
    reportes.reporte_inventario()


def opcion_resumen_ventas() -> None:
    """Opcion 5: imprime el resumen de ventas."""
    reportes.resumen_ventas()


def opcion_mas_vendidos() -> None:
    """Opcion 6: imprime los productos mas vendidos."""
    for codigo, unidades in reportes.mas_vendidos():
        print(codigo, "->", unidades, "unidades")


def opcion_stock_bajo() -> None:
    """Opcion 7: imprime una alerta por cada producto con stock bajo."""
    bajos = reportes.productos_stock_bajo()
    if not bajos:
        print("No hay productos con stock bajo.")
        return
    for producto in bajos:
        print("OJO:", producto["nombre"], "solo tiene", producto["stock"], "unidades")


def opcion_guardar_y_salir() -> bool:
    """Opcion 8: guarda los datos y regresa True para terminar el menu."""
    almacen.guardar_datos(ARCHIVO)
    print("Datos guardados. Hasta luego.")
    return True


OPCIONES: dict[str, Callable[[], bool | None]] = {
    "1": opcion_agregar_producto,
    "2": opcion_registrar_venta,
    "3": opcion_cotizar,
    "4": opcion_reporte_inventario,
    "5": opcion_resumen_ventas,
    "6": opcion_mas_vendidos,
    "7": opcion_stock_bajo,
    "8": opcion_guardar_y_salir,
}


def menu() -> None:
    """Ciclo principal: muestra el menu y ejecuta la opcion elegida."""
    print("Bienvenido al gestor de la tienda La Esquina")
    cargar_datos_iniciales()
    while True:
        mostrar_opciones()
        accion = OPCIONES.get(input("Opcion: "))
        if accion is None:
            print("Opcion no valida.")
        elif accion():
            break


if __name__ == "__main__":
    menu()
