# controller/orden_controller.py
from __future__ import annotations
from typing import Any, List


class OrdenControlador:
    """
    Envuelve OrdenModelo con una API simple para la fachada.
    """
    def __init__(self, modelo) -> None:
        self.m = modelo

    def listar(self) -> List[Any]:
        return self.m.listar()

    def insertar(
        self,
        cve_status: int,
        eq_marca: str,
        eq_modelo: str,
        cve_tipo_equipo: int,
        notas_cliente: str,
        cliente: int,
        cve_taller: int,
        cve_tecnico: int,
    ) -> Any:
        return self.m.insertar(
            cve_status, eq_marca, eq_modelo, cve_tipo_equipo,
            notas_cliente, cliente, cve_taller, cve_tecnico
        )

    def tecnicos_orden(self, cve_orden: int, horas: bool = False):
        return self.m.tecnicos_orden(cve_orden, horas)