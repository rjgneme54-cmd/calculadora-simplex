from __future__ import annotations


def _phase_label(phase: int) -> str:
    if phase == 1:
        return "Fase 1"
    if phase == 2:
        return "Fase 2"
    return "el tableau"


def explain_optimal(phase: int) -> str:
    return (
        f"Se alcanzó la solución óptima de {_phase_label(phase)}: todos los coeficientes "
        "de la fila Z son menores o iguales a cero, por lo que ninguna variable no básica "
        "puede mejorar más el valor de la función objetivo."
    )


def explain_unbounded(entering: str) -> str:
    return (
        f"La variable {entering} puede aumentar indefinidamente sin violar ninguna "
        "restricción (todos los coeficientes de su columna son menores o iguales a cero), "
        "por lo que el problema no tiene solución acotada."
    )


def explain_pivot(entering: str, leaving: str, pivot_element: object, phase: int) -> str:
    prefix = f"[{_phase_label(phase)}] " if phase in (1, 2) else ""
    return (
        f"{prefix}La variable {entering} entra a la base porque tiene el mayor coeficiente "
        f"positivo en la fila Z, lo que más mejora la función objetivo. La variable "
        f"{leaving} sale de la base según la prueba de la razón mínima. El elemento "
        f"pivote es {pivot_element}."
    )
