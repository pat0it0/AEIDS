# controller/db_facade.py
from __future__ import annotations
from typing import Any

from model.oracle_model import OracleDB
from model.repositories import (
    OrdenModelo, NotaModelo, ParteModelo, ServicioModelo,
    ClienteModelo, CatalogosModelo
)
from controller.orden_controller import OrdenControlador
from controller.nota_controller import NotaControlador
from controller.parte_controller import ParteControlador
from controller.servicio_controller import ServicioControlador
from controller.cliente_controller import ClienteControlador
from controller.catalogos_controller import CatalogosControlador


class DBFacade:
    """
    Fachada para la UI.
    """

    def __init__(self, hostname: str, port: str | int, service_name: str,
                 username: str, password: str) -> None:
        self._db = OracleDB(
            hostname=hostname, port=port, service_name=service_name,
            username=username, password=password
        )

        om = OrdenModelo(self._db)
        nm = NotaModelo(self._db)
        pm = ParteModelo(self._db)
        sm = ServicioModelo(self._db)
        cm = ClienteModelo(self._db)
        catm = CatalogosModelo(self._db)

        self._orden = OrdenControlador(om)
        self._nota = NotaControlador(nm)
        self._parte = ParteControlador(pm)
        self._servicio = ServicioControlador(sm)
        self._cliente = ClienteControlador(cm)
        self._catalogos = CatalogosControlador(catm)

    # ================= Conexión =================
    def get_connection(self):
        return self._db.get_connection()

    def close_connection(self):
        return self._db.close_connection()

    # ================= Órdenes =================
    def ordenes(self):
        return self._orden.listar()

    def insertar_orden(self, *args, **kwargs):
        # ... (lo que ya tenías, sin cambios)
        return self._orden.insertar(*args, **kwargs)

    def tecnicos_orden(self, cve_orden, horas: bool = False):
        return self._orden.tecnicos_orden(cve_orden, horas)

    # NUEVO: actualizar orden (usado por el diálogo)
    def actualizar_orden(self, cve_orden: int, **kwargs):
        """
        kwargs permitidos (si existen en tu tabla): cve_status, eq_marca, eq_modelo,
        cve_tipo_equipo, notas_cliente, cve_taller, cve_tecnico
        """
        return self._orden.actualizar(int(cve_orden), **kwargs)

    # ================= Notas =================
    def notas(self, cve_orden):
        return self._nota.listar(cve_orden)

    def insertar_nota(self, cve_orden, nota):
        return self._nota.insertar(cve_orden, nota)

    def eliminar_nota(self, cve_nota):
        return self._nota.eliminar(cve_nota)

    # ================= Partes =================
    def partes(self):
        return self._parte.catalogo()

    def partes_orden(self, cve_orden):
        return self._parte.listar(cve_orden)

    def parte_orden(self, *args, **kwargs):
        return self._parte.insertar(*args, **kwargs)

    def eliminar_parte(self, cve_orden_parte):
        return self._parte.eliminar(cve_orden_parte)

    # ================= Servicios =================
    def servicios(self):
        return self._servicio.catalogo()

    def servicios_orden(self, cve_orden):
        return self._servicio.listar(cve_orden)

    def servicio_orden(self, *args, **kwargs):
        return self._servicio.insertar(*args, **kwargs)

    def eliminar_servicio(self, cve_orden_servicio):
        return self._servicio.eliminar(cve_orden_servicio)

    # ================= Cliente =================
    def insertar_cliente_y_verificar_datos(self, *args, **kwargs):
        return self._cliente.insertar_y_verificar(*args, **kwargs)

    # NUEVO: usar en “Editar cliente”
    def cliente_id_por_orden(self, cve_orden: int) -> int | None:
        return self._orden.cliente_id_por_orden(int(cve_orden))

    def cliente_detalle(self, cve_cliente: int) -> dict | None:
        return self._cliente.detalle(int(cve_cliente))

    def actualizar_cliente(self, cve_cliente: int, **kwargs):
        """
        kwargs típicos: nombre, paterno, materno, correo, telefono
        (la capa repo mapea a las columnas reales)
        """
        return self._cliente.actualizar(int(cve_cliente), **kwargs)

    def guardar_cliente_de_orden(
        self,
        cve_orden: int,
        nombre: str,
        paterno: str,
        materno: str,
        correo: str,
        telefono: str,
        dir_calle: str,
        dir_num: str,
    ) -> None:
        """
        Actualiza los datos del cliente asociado a una orden.
        - Resuelve el cve_cliente desde la tabla ORDEN.
        - Detecta dinámicamente columnas de CLIENTE (nombre/paterno/materno/correo/telefono/dir_calle/dir_num).
        - Ejecuta el UPDATE. (El commit lo hace la capa superior.)

        Lanza RuntimeError si no puede detectar columnas clave o la orden no existe.
        """
        conn = self._db.get_connection()

        def _cols(table: str):
            with conn.cursor() as c:
                c.execute(f"SELECT * FROM {table} WHERE 1=0")
                return [d[0].lower() for d in c.description]

        def _pick(cols, *candidates):
            for cand in candidates:
                c = cand.lower()
                if c in cols:
                    return c
            return None

        # --- ORDEN: obtener cve_cliente de la orden ---
        orden_cols = _cols("orden")
        ord_id_col = _pick(orden_cols, "cve_orden", "id_orden", "id", "cve")
        ord_cli_col = _pick(orden_cols, "cve_cliente", "id_cliente", "cliente")
        if not ord_id_col or not ord_cli_col:
            raise RuntimeError("No se pudo detectar columnas (id/cliente) en ORDEN.")

        with conn.cursor() as cur:
            cur.execute(f"SELECT {ord_cli_col} FROM orden WHERE {ord_id_col} = :v", {"v": int(cve_orden)})
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"No existe la orden #{cve_orden}.")
            cve_cliente = int(row[0])

        # --- CLIENTE: detectar columnas disponibles ---
        cli_cols = _cols("cliente")
        cli_id_col    = _pick(cli_cols, "cve_cliente", "id_cliente", "id", "cve")
        col_nombre    = _pick(cli_cols, "nombre", "nom_cliente", "cliente_nombre")
        col_paterno   = _pick(cli_cols, "paterno", "ap_paterno", "apellido_paterno")
        col_materno   = _pick(cli_cols, "materno", "ap_materno", "apellido_materno")
        col_correo    = _pick(cli_cols, "correo", "email", "mail")
        col_tel       = _pick(cli_cols, "telefono", "tel", "phone")
        col_calle     = _pick(cli_cols, "dir_calle", "calle", "direccion", "domicilio")
        col_num_calle = _pick(cli_cols, "dir_num", "numero", "no_calle", "num_calle", "numero_calle")

        if not cli_id_col:
            raise RuntimeError("No se pudo detectar columna id en CLIENTE.")

        # Construir SET dinámico sólo con columnas que existan
        sets = []
        binds: dict[str, Any] = {":id": cve_cliente}

        def _add(col: str | None, bind: str, value: Any):
            if col:
                sets.append(f"{col} = {bind}")
                binds[bind] = ("" if value is None else value)

        _add(col_nombre,    ":p1", (nombre or "").strip())
        _add(col_paterno,   ":p2", (paterno or "").strip())
        _add(col_materno,   ":p3", (materno or "").strip())
        _add(col_correo,    ":p4", (correo or "").strip())
        _add(col_tel,       ":p5", (telefono or "").strip())
        _add(col_calle,     ":p6", (dir_calle or "").strip())
        _add(col_num_calle, ":p7", (dir_num or "").strip())

        if not sets:
            # No hay campos actualizables en esta instalación
            return

        sql = f"UPDATE cliente SET {', '.join(sets)} WHERE {cli_id_col} = :id"
        with conn.cursor() as cur:
            cur.execute(sql, binds)
        # commit lo hace la UI/capa llamante

    # ================= Catálogos =================
    def tipos(self):
        return self._catalogos.tipos()

    def estados(self, pais):
        return self._catalogos.estados(pais)

    def paises(self):
        return self._catalogos.paises()

    def talleres(self):
        return self._catalogos.talleres()

    def tecnicos_taller(self, cve_taller):
        return self._catalogos.tecnicos_taller(cve_taller)

    def statuses(self):
        return self._catalogos.statuses()

    @property
    def _connection(self):
        return self._db.get_connection()