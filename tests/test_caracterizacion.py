"""Pruebas de caracterizacion: fijan el comportamiento ACTUAL del programa.

Se escribieron contra el codigo original (antes de refactorizar), incluyendo
los bugs conocidos que por regla NO se corrigen (N6, N15, N19, N20 del
diagnostico). Si una refactorizacion rompe alguna de estas pruebas, cambio el
comportamiento observable.

Solo usan la API publica de gestor, almacen, reportes y main.
"""

import json
import math
from pathlib import Path

import pytest

import almacen
import gestor
import main
import reportes

DATOS_EJEMPLO = Path(__file__).parent.parent / "datos_ejemplo.json"

MENU = (
    "\n"
    "1) Agregar producto\n"
    "2) Registrar venta\n"
    "3) Cotizar\n"
    "4) Reporte de inventario\n"
    "5) Resumen de ventas\n"
    "6) Mas vendidos\n"
    "7) Alertas de stock bajo\n"
    "8) Guardar y salir\n"
)
BIENVENIDA = "Bienvenido al gestor de la tienda La Esquina\n"
ENCABEZADO_TICKET = "TIENDA LA ESQUINA\n----------------------------\n"


def _venta_unica(precio, cantidad, cliente=""):
    gestor.agregarProducto("A1", "Producto de prueba", precio, 1000)
    return gestor.registrar_venta("A1", cantidad, cliente)


def _simular_entradas(monkeypatch, entradas):
    """Reemplaza input() por una secuencia fija y registra los prompts."""
    pendientes = iter(entradas)
    prompts = []

    def falso_input(mensaje=""):
        prompts.append(mensaje)
        return next(pendientes)

    monkeypatch.setattr("builtins.input", falso_input)
    return prompts


# ---------------------------------------------------------------
# Ticket de venta
# ---------------------------------------------------------------


def test_ticket_sin_descuento():
    venta = _venta_unica(10.0, 2)
    assert venta["ticket"] == (
        ENCABEZADO_TICKET
        + "Folio: 1\n"
        + "Producto de prueba x2\n"
        + "Subtotal: $20.0\n"
        + "IVA: $3.2\n"
        + "TOTAL: $23.2\n"
    )


def test_ticket_con_descuento_por_volumen():
    venta = _venta_unica(100.0, 6)
    assert venta["ticket"] == (
        ENCABEZADO_TICKET
        + "Folio: 1\n"
        + "Producto de prueba x6\n"
        + "Subtotal: $600.0\n"
        + "Descuento: -$30.0\n"
        + "IVA: $91.2\n"
        + "TOTAL: $661.2\n"
    )


def test_ticket_con_descuento_solo_vip():
    # subtotal < 500: sin descuento por volumen, pero VIP aplica porque > 200
    venta = _venta_unica(300.0, 1, "VIP1")
    assert venta["ticket"] == (
        ENCABEZADO_TICKET
        + "Folio: 1\n"
        + "Producto de prueba x1\n"
        + "Subtotal: $300.0\n"
        + "Descuento: -$6.0\n"
        + "IVA: $47.04\n"
        + "TOTAL: $341.04\n"
    )


def test_ticket_con_precio_entero_no_agrega_decimales():
    venta = _venta_unica(10, 1)
    assert "Subtotal: $10\n" in venta["ticket"]
    assert venta["subtotal"] == 10
    assert isinstance(venta["subtotal"], int)


def test_campos_y_orden_de_la_venta():
    venta = _venta_unica(10.0, 2)
    assert list(venta.keys()) == [
        "folio", "codigo", "nombre", "cantidad", "subtotal", "descuento",
        "impuesto", "total", "cliente", "fecha", "ticket",
    ]
    assert venta["cliente"] == ""
    assert venta["impuesto"] == 3.2
    assert venta is gestor.VENTAS[-1]


def test_descuento_cero_es_entero():
    venta = _venta_unica(10.0, 2)
    assert venta["descuento"] == 0
    assert isinstance(venta["descuento"], int)


# ---------------------------------------------------------------
# Limites de descuentos, VIP e IVA
# ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("precio", "cliente", "descuento", "impuesto", "total"),
    [
        (499.99, "", 0, 80.0, 579.99),
        (500.0, "", 25.0, 76.0, 551.0),
        (999.99, "", 50.0, 152.0, 1101.99),
        (1000.0, "", 100.0, 144.0, 1044.0),
        # VIP: estrictamente mayor a 200 sobre el monto ya con descuento
        (200.0, "VIP1", 0, 32.0, 232.0),
        (200.01, "VIP1", 4.0, 31.36, 227.37),
        (210.0, "VIP1", 4.2, 32.93, 238.73),
    ],
)
def test_limites_de_descuento(precio, cliente, descuento, impuesto, total):
    venta = _venta_unica(precio, 1, cliente)
    assert venta["descuento"] == descuento
    assert venta["impuesto"] == impuesto
    assert venta["total"] == total


def test_vip_en_minusculas_no_recibe_extra():
    venta = _venta_unica(100.0, 6, "vip007")
    assert venta["descuento"] == 30.0
    assert venta["total"] == 661.2


def test_vip_con_cliente_none_no_falla():
    venta = _venta_unica(100.0, 6, None)
    assert venta["total"] == 661.2
    assert venta["cliente"] is None


@pytest.mark.parametrize("precio", [9.99, 33.33, 99.99, 166.67, 249.99, 333.33])
@pytest.mark.parametrize("cantidad", [1, 2, 3, 5, 7])
def test_cotizar_coincide_con_venta_sin_vip(precio, cantidad):
    gestor.agregarProducto("A1", "Producto", precio, 1000)
    estimado = gestor.cotizar("A1", cantidad)
    venta = gestor.registrar_venta("A1", cantidad)
    assert estimado == venta["total"]


def test_cotizar_no_revisa_stock():
    gestor.agregarProducto("A1", "Producto", 10.0, 2)
    assert gestor.cotizar("A1", 1000) == 10440.0
    assert gestor.INVENTARIO["A1"]["stock"] == 2


# ---------------------------------------------------------------
# Mensajes de ultimo_error
# ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("codigo", "precio", "stock", "mensaje"),
    [
        ("", 10.0, 1, "codigo vacio"),
        (None, 10.0, 1, "codigo vacio"),
        ("A1", 10.0, 1, "el producto ya existe"),
        ("A2", 0, 1, "precio invalido"),
        ("A2", 10.0, -1, "stock invalido"),
    ],
)
def test_mensajes_de_agregar_producto(codigo, precio, stock, mensaje):
    gestor.agregarProducto("A1", "Existente", 10.0, 1)
    assert gestor.agregarProducto(codigo, "Nuevo", precio, stock) is False
    assert gestor.ultimo_error == mensaje


def test_mensajes_de_eliminar_y_actualizar_stock():
    assert gestor.eliminar_producto("ZZ") is False
    assert gestor.ultimo_error == "producto no existe"
    assert gestor.actualizar_stock("ZZ", 1) is False
    assert gestor.ultimo_error == "producto no existe"
    gestor.agregarProducto("A1", "Producto", 10.0, 1)
    assert gestor.actualizar_stock("A1", -2) is False
    assert gestor.ultimo_error == "el stock no puede quedar negativo"


@pytest.mark.parametrize(
    ("codigo", "cantidad", "mensaje"),
    [
        ("", 1, "codigo vacio"),
        (None, 1, "codigo vacio"),
        ("ZZ", 1, "producto no existe"),
        ("A1", 0, "cantidad invalida"),
        ("A1", None, "cantidad invalida"),
        ("A1", 3, "stock insuficiente"),
        # el orden de validacion importa: codigo antes que cantidad
        ("", 0, "codigo vacio"),
        ("ZZ", 0, "producto no existe"),
    ],
)
def test_mensajes_de_registrar_venta(codigo, cantidad, mensaje):
    gestor.agregarProducto("A1", "Producto", 10.0, 2)
    assert gestor.registrar_venta(codigo, cantidad) is None
    assert gestor.ultimo_error == mensaje
    assert gestor.INVENTARIO["A1"]["stock"] == 2
    assert gestor.VENTAS == []


@pytest.mark.parametrize(
    ("codigo", "cantidad", "mensaje"),
    [
        # a diferencia de registrar_venta, "" no da "codigo vacio"
        ("", 1, "producto no existe"),
        ("ZZ", 1, "producto no existe"),
        ("A1", 0, "cantidad invalida"),
        ("A1", None, "cantidad invalida"),
    ],
)
def test_mensajes_de_cotizar(codigo, cantidad, mensaje):
    gestor.agregarProducto("A1", "Producto", 10.0, 2)
    assert gestor.cotizar(codigo, cantidad) is None
    assert gestor.ultimo_error == mensaje


def test_ultimo_error_no_se_limpia_tras_un_exito():
    gestor.agregarProducto("A1", "Producto", 0, 1)
    assert gestor.agregarProducto("A2", "Producto", 10.0, 1) is True
    assert gestor.ultimo_error == "precio invalido"


def test_reiniciar_limpia_error_y_folio_in_situ():
    inventario, ventas = gestor.INVENTARIO, gestor.VENTAS
    gestor.agregarProducto("A1", "Producto", 0, 1)
    gestor.agregarProducto("A1", "Producto", 10.0, 5)
    gestor.registrar_venta("A1", 1)
    gestor.reiniciar_sistema()
    assert gestor.ultimo_error == ""
    assert gestor.INVENTARIO is inventario
    assert gestor.VENTAS is ventas
    gestor.agregarProducto("A1", "Producto", 10.0, 5)
    assert gestor.registrar_venta("A1", 1)["folio"] == 1


def test_venta_fallida_no_consume_folio():
    gestor.agregarProducto("A1", "Producto", 10.0, 5)
    gestor.registrar_venta("A1", 99)
    assert gestor.registrar_venta("A1", 1)["folio"] == 1


# ---------------------------------------------------------------
# Busqueda y reportes
# ---------------------------------------------------------------


def test_buscar_producto_casos_limite():
    gestor.agregarProducto("A1", "Café de grano", 185.0, 10)
    gestor.agregarProducto("A2", "Azúcar", 32.5, 40)
    assert gestor.buscarProducto("zzz") == []
    todos = gestor.buscarProducto("")
    assert [p["codigo"] for p in todos] == ["A1", "A2"]
    # regresa los mismos diccionarios del inventario, no copias
    assert todos[0] is gestor.INVENTARIO["A1"]


def test_stock_bajo_es_estrictamente_menor_a_cinco():
    gestor.agregarProducto("A1", "Cuatro", 10.0, 4)
    gestor.agregarProducto("A2", "Cinco", 10.0, 5)
    bajos = reportes.productos_stock_bajo()
    assert [p["codigo"] for p in bajos] == ["A1"]
    assert bajos[0] is gestor.INVENTARIO["A1"]


def test_reporte_inventario_texto_exacto(capsys):
    gestor.agregarProducto("A1", "Leche", 26.0, 3)
    gestor.agregarProducto("A2", "Azúcar", 32.5, 40)
    esperado = (
        "===== INVENTARIO =====\n"
        "A1 | Leche | $26.0 | stock: 3  <-- STOCK BAJO\n"
        "A2 | Azúcar | $32.5 | stock: 40\n"
        "Valor total del inventario: $1378.0\n"
    )
    assert reportes.reporte_inventario() == esperado
    assert capsys.readouterr().out == esperado + "\n"


def test_reportes_vacios(capsys):
    assert reportes.reporte_inventario() == (
        "===== INVENTARIO =====\nValor total del inventario: $0\n"
    )
    assert reportes.resumen_ventas() == (
        "===== RESUMEN DE VENTAS =====\nNumero de ventas: 0\nTotal del dia: $0\n"
    )
    assert reportes.mas_vendidos() == []
    capsys.readouterr()


def test_resumen_ventas_texto_exacto(capsys):
    gestor.agregarProducto("A1", "Café", 100.0, 50)
    gestor.agregarProducto("B1", "Galletas", 5.0, 50)
    gestor.registrar_venta("A1", 6, "VIP007")
    gestor.registrar_venta("B1", 1)
    esperado = (
        "===== RESUMEN DE VENTAS =====\n"
        "Folio 1: Café x6 = $647.28\n"
        "Folio 2: Galletas x1 = $5.8\n"
        "Numero de ventas: 2\n"
        "Total del dia: $653.08\n"
    )
    assert reportes.resumen_ventas() == esperado
    assert capsys.readouterr().out == esperado + "\n"


def test_mas_vendidos_empates_conservan_orden_de_primera_venta():
    for codigo in ("B1", "A1", "C1", "D1"):
        gestor.agregarProducto(codigo, codigo, 1.0, 100)
    gestor.registrar_venta("B1", 2)
    gestor.registrar_venta("A1", 2)
    gestor.registrar_venta("C1", 3)
    gestor.registrar_venta("D1", 1)
    assert reportes.mas_vendidos() == [("C1", 3), ("B1", 2), ("A1", 2)]
    assert reportes.mas_vendidos(10) == [("C1", 3), ("B1", 2), ("A1", 2), ("D1", 1)]


# ---------------------------------------------------------------
# Persistencia (incluye N15)
# ---------------------------------------------------------------


def test_formato_del_json_guardado(tmp_path):
    ruta = tmp_path / "datos.json"
    gestor.agregarProducto("A1", "Café", 10.0, 50)
    gestor.registrar_venta("A1", 1)
    assert almacen.guardar_datos(str(ruta)) is True
    texto = ruta.read_text(encoding="utf-8")
    assert texto.startswith(
        '{\n  "inventario": {\n    "A1": {\n      "codigo": "A1",\n'
        '      "nombre": "Café",\n      "precio": 10.0,\n      "stock": 49\n'
    )
    assert '"descuento": 0,' in texto
    assert not texto.endswith("\n")
    datos = json.loads(texto)
    assert list(datos) == ["inventario", "ventas", "contador"]
    assert datos["contador"] == 1


def test_cargar_datos_ejemplo_del_repo():
    assert almacen.cargar_datos(str(DATOS_EJEMPLO)) is True
    assert list(gestor.INVENTARIO) == ["A001", "A002", "A003", "B001", "B002", "C001"]
    assert gestor.VENTAS == []


def test_cargar_conserva_los_mismos_objetos(tmp_path):
    ruta = str(tmp_path / "datos.json")
    inventario, ventas = gestor.INVENTARIO, gestor.VENTAS
    gestor.agregarProducto("A1", "Café", 10.0, 50)
    almacen.guardar_datos(ruta)
    almacen.cargar_datos(ruta)
    assert gestor.INVENTARIO is inventario
    assert gestor.VENTAS is ventas


def test_cargar_inexistente_deja_mensaje(tmp_path):
    assert almacen.cargar_datos(str(tmp_path / "no.json")) is False
    assert gestor.ultimo_error == "el archivo no existe"


def test_n15_archivo_corrupto(tmp_path):
    ruta = tmp_path / "datos.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"


def test_n15_archivo_binario_cuenta_como_corrupto(tmp_path):
    ruta = tmp_path / "datos.json"
    ruta.write_bytes(b"\xff\xfe\x00\x81")
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"


def test_n15_json_sin_ventas_lanza_keyerror_con_estado_a_medias(tmp_path):
    gestor.agregarProducto("X1", "Viejo", 1.0, 5)
    gestor.registrar_venta("X1", 1)
    ruta = tmp_path / "datos.json"
    nuevo = {"codigo": "A1", "nombre": "Nuevo", "precio": 1.0, "stock": 1}
    ruta.write_text(json.dumps({"inventario": {"A1": nuevo}}), encoding="utf-8")
    with pytest.raises(KeyError):
        almacen.cargar_datos(str(ruta))
    # el inventario ya se reemplazo y las ventas ya se vaciaron
    assert list(gestor.INVENTARIO) == ["A1"]
    assert gestor.VENTAS == []


def test_n15_json_sin_inventario_lanza_keyerror_y_vacia_inventario(tmp_path):
    gestor.agregarProducto("X1", "Viejo", 1.0, 5)
    gestor.registrar_venta("X1", 1)
    ruta = tmp_path / "datos.json"
    ruta.write_text(json.dumps({"ventas": []}), encoding="utf-8")
    with pytest.raises(KeyError):
        almacen.cargar_datos(str(ruta))
    assert gestor.INVENTARIO == {}
    assert len(gestor.VENTAS) == 1


def test_n15_json_sin_contador_reinicia_folio(tmp_path):
    ruta = tmp_path / "datos.json"
    producto = {"codigo": "A1", "nombre": "P", "precio": 1.0, "stock": 9}
    ruta.write_text(
        json.dumps({"inventario": {"A1": producto}, "ventas": []}), encoding="utf-8"
    )
    assert almacen.cargar_datos(str(ruta)) is True
    assert gestor.registrar_venta("A1", 1)["folio"] == 1


# ---------------------------------------------------------------
# Menu interactivo (N6, N19, N20)
# ---------------------------------------------------------------


def test_sesion_completa_del_menu(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    prompts = _simular_entradas(monkeypatch, [
        "1", "A1", "Café", "100", "10",
        "1", "B1", "Galletas", "5", "3",
        "2", "A1", "6", "VIP007",
        "2", "B1", "1", "",
        "3", "A1", "2",
        "3", "ZZ", "1",
        "4", "5", "6", "7", "9", "8",
    ])
    main.menu()

    ticket_1 = (
        ENCABEZADO_TICKET + "Folio: 1\nCafé x6\nSubtotal: $600.0\n"
        "Descuento: -$42.0\nIVA: $89.28\nTOTAL: $647.28\n"
    )
    ticket_2 = (
        ENCABEZADO_TICKET + "Folio: 2\nGalletas x1\nSubtotal: $5.0\n"
        "IVA: $0.8\nTOTAL: $5.8\n"
    )
    reporte = (
        "===== INVENTARIO =====\n"
        "A1 | Café | $100.0 | stock: 4  <-- STOCK BAJO\n"
        "B1 | Galletas | $5.0 | stock: 2  <-- STOCK BAJO\n"
        "Valor total del inventario: $410.0\n"
    )
    resumen = (
        "===== RESUMEN DE VENTAS =====\n"
        "Folio 1: Café x6 = $647.28\n"
        "Folio 2: Galletas x1 = $5.8\n"
        "Numero de ventas: 2\n"
        "Total del dia: $653.08\n"
    )
    esperado = (
        BIENVENIDA
        + MENU + "Producto agregado.\n"
        + MENU + "Producto agregado.\n"
        + MENU + ticket_1 + "\n"
        + MENU + ticket_2 + "\n"
        + MENU + "Total estimado (con IVA): $232.0\n"
        + MENU + "Error: producto no existe\n"
        + MENU + reporte + "\n"
        + MENU + resumen + "\n"
        + MENU + "A1 -> 6 unidades\nB1 -> 1 unidades\n"
        + MENU + "OJO: Café solo tiene 4 unidades\n"
        + "OJO: Galletas solo tiene 2 unidades\n"
        + MENU + "Opcion no valida.\n"
        + MENU + "Datos guardados. Hasta luego.\n"
    )
    assert capsys.readouterr().out == esperado
    assert prompts == [
        "Opcion: ", "Codigo: ", "Nombre: ", "Precio: ", "Stock inicial: ",
        "Opcion: ", "Codigo: ", "Nombre: ", "Precio: ", "Stock inicial: ",
        "Opcion: ", "Codigo del producto: ", "Cantidad: ",
        "Codigo de cliente (enter si no tiene): ",
        "Opcion: ", "Codigo del producto: ", "Cantidad: ",
        "Codigo de cliente (enter si no tiene): ",
        "Opcion: ", "Codigo del producto: ", "Cantidad: ",
        "Opcion: ", "Codigo del producto: ", "Cantidad: ",
        "Opcion: ", "Opcion: ", "Opcion: ", "Opcion: ", "Opcion: ", "Opcion: ",
    ]


def test_menu_errores_de_alta_y_venta(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    _simular_entradas(monkeypatch, [
        "1", "", "Nada", "10", "1",
        "2", "ZZ", "1", "",
        "7", "8",
    ])
    main.menu()
    assert capsys.readouterr().out == (
        BIENVENIDA
        + MENU + "Error: codigo vacio\n"
        + MENU + "Error: producto no existe\n"
        + MENU + "No hay productos con stock bajo.\n"
        + MENU + "Datos guardados. Hasta luego.\n"
    )


def test_n20_archivo_relativo_al_directorio_actual(monkeypatch, capsys, tmp_path):
    assert main.ARCHIVO == "datos_ejemplo.json"
    monkeypatch.chdir(tmp_path)
    _simular_entradas(monkeypatch, ["8"])
    main.menu()
    salida = capsys.readouterr().out
    assert "Datos cargados" not in salida
    assert (tmp_path / "datos_ejemplo.json").exists()


def test_n20_carga_el_archivo_del_directorio_actual(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datos_ejemplo.json").write_text(
        DATOS_EJEMPLO.read_text(encoding="utf-8"), encoding="utf-8"
    )
    _simular_entradas(monkeypatch, ["8"])
    main.menu()
    salida = capsys.readouterr().out
    assert salida.startswith(BIENVENIDA + "Datos cargados de datos_ejemplo.json\n")
    assert len(gestor.INVENTARIO) == 6


def test_n6_imprime_datos_cargados_aunque_el_archivo_este_corrupto(
    monkeypatch, capsys, tmp_path
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datos_ejemplo.json").write_text("{corrupto", encoding="utf-8")
    _simular_entradas(monkeypatch, ["8"])
    main.menu()
    salida = capsys.readouterr().out
    assert salida.startswith(BIENVENIDA + "Datos cargados de datos_ejemplo.json\n")
    assert gestor.ultimo_error == "archivo corrupto"


def test_n19_pedir_numero_reintenta_y_acepta_nan(monkeypatch, capsys):
    _simular_entradas(monkeypatch, ["abc", "", "nan"])
    resultado = main.pedir_numero("Precio: ")
    assert math.isnan(resultado)
    assert capsys.readouterr().out == "Eso no es un numero, intenta de nuevo.\n" * 2


def test_n19_cantidad_decimal_se_trunca(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    gestor.agregarProducto("A1", "Producto", 10.0, 10)
    _simular_entradas(monkeypatch, ["2", "A1", "2.7", "", "8"])
    main.menu()
    capsys.readouterr()
    assert gestor.VENTAS[0]["cantidad"] == 2
    assert gestor.INVENTARIO["A1"]["stock"] == 8


def test_n19_precio_nan_se_acepta(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    _simular_entradas(monkeypatch, ["1", "A1", "Raro", "nan", "1", "8"])
    main.menu()
    assert "Producto agregado." in capsys.readouterr().out
    assert math.isnan(gestor.INVENTARIO["A1"]["precio"])


def test_n19_cantidad_infinita_truena(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    gestor.agregarProducto("A1", "Producto", 10.0, 10)
    _simular_entradas(monkeypatch, ["2", "A1", "inf"])
    with pytest.raises(OverflowError):
        main.menu()
    capsys.readouterr()
