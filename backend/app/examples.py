EXAMPLES = [
    {
        "id": "wyndor-glass",
        "title": "Wyndor Glass Co. (máximo, todas ≤)",
        "description": (
            "El ejemplo clásico de Hillier & Lieberman: dos productos y tres restricciones de "
            "capacidad, todas de tipo ≤. Óptimo único, sin casos especiales."
        ),
        "request": {
            "sense": "max",
            "objective": [3, 5],
            "variables": [{"name": "x1"}, {"name": "x2"}],
            "constraints": [
                {"coeffs": [1, 0], "op": "<=", "rhs": 4, "name": "Planta 1"},
                {"coeffs": [0, 2], "op": "<=", "rhs": 12, "name": "Planta 2"},
                {"coeffs": [3, 2], "op": "<=", "rhs": 18, "name": "Planta 3"},
            ],
            "method": "two_phase",
        },
    },
    {
        "id": "minimizacion-costos-ge",
        "title": "Minimización de costos (restricciones ≥)",
        "description": (
            "Un problema de minimización con dos restricciones de tipo ≥ (por ejemplo, "
            "requisitos mínimos de nutrientes o de producción). Requiere variables "
            "artificiales: buen ejemplo para ver el Método de las Dos Fases en acción."
        ),
        "request": {
            "sense": "min",
            "objective": [2, 3],
            "variables": [{"name": "x1"}, {"name": "x2"}],
            "constraints": [
                {"coeffs": [1, 1], "op": ">=", "rhs": 4, "name": "Requisito 1"},
                {"coeffs": [1, 2], "op": ">=", "rhs": 6, "name": "Requisito 2"},
            ],
            "method": "two_phase",
        },
    },
    {
        "id": "mezcla-restricciones",
        "title": "Mezcla de restricciones (=, ≥, ≤)",
        "description": (
            "Combina los tres tipos de restricción en un solo problema de minimización. "
            "La solución óptima cae en valores fraccionarios exactos (2/5, 9/5), ideal para "
            "comprobar la aritmética exacta con fracciones."
        ),
        "request": {
            "sense": "min",
            "objective": [4, 1],
            "variables": [{"name": "x1"}, {"name": "x2"}],
            "constraints": [
                {"coeffs": [3, 1], "op": "=", "rhs": 3, "name": "Restricción 1"},
                {"coeffs": [4, 3], "op": ">=", "rhs": 6, "name": "Restricción 2"},
                {"coeffs": [1, 2], "op": "<=", "rhs": 4, "name": "Restricción 3"},
            ],
            "method": "two_phase",
        },
    },
    {
        "id": "programacion-entera",
        "title": "Programación entera (Ramificación y Acotamiento)",
        "description": (
            "La relajación lineal da un óptimo fraccionario (3, 1.5). Al exigir que ambas "
            "variables sean enteras, Branch & Bound encuentra el verdadero óptimo entero "
            "en (4, 0), distinto del redondeo ingenuo de la relajación."
        ),
        "request": {
            "sense": "max",
            "objective": [5, 4],
            "variables": [
                {"name": "x1", "kind": "integer"},
                {"name": "x2", "kind": "integer"},
            ],
            "constraints": [
                {"coeffs": [6, 4], "op": "<=", "rhs": 24, "name": "Recurso 1"},
                {"coeffs": [1, 2], "op": "<=", "rhs": 6, "name": "Recurso 2"},
            ],
            "method": "two_phase",
        },
    },
]
