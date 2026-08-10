from __future__ import annotations

from fractions import Fraction

from app.core.models import LPProblem, Method, Sense, SimplexResult, SolveStatus, TableauIteration
from app.core.simplex.engine_loop import run_phase
from app.core.simplex.pivot import Tableau, compute_reduced_costs, compute_z_value
from app.core.standard_form import build_standard_form, extract_original_values

INFEASIBLE_MESSAGE = (
    "El problema no tiene solución factible: en la Fase 1, al menos una variable "
    "artificial permanece positiva en el óptimo, lo que significa que no existe ningún "
    "punto que satisfaga todas las restricciones simultáneamente."
)
UNBOUNDED_MESSAGE = (
    "El problema no tiene solución acotada: es posible aumentar (o disminuir) "
    "indefinidamente el valor de la función objetivo sin violar ninguna restricción."
)
ALTERNATE_OPTIMA_NOTE = (
    " Existen múltiples soluciones óptimas (óptimos alternativos): al menos una "
    "variable no básica tiene costo reducido igual a cero, por lo que otros puntos "
    "distintos alcanzan el mismo valor de Z."
)
DEGENERATE_NOTE = (
    " La solución es degenerada: alguna variable básica vale cero, lo cual puede "
    "deberse a una restricción redundante entre las restricciones o a un empate en "
    "la prueba de la razón mínima durante el proceso."
)


def solve_two_phase(problem: LPProblem) -> SimplexResult:
    sf = build_standard_form(problem)
    artificial_set = set(sf.artificial_cols)

    tableau = Tableau(
        var_names=sf.var_names,
        basis=list(sf.initial_basis),
        body=[row[:] for row in sf.a],
        rhs=list(sf.b),
        z_row=[Fraction(0)] * sf.num_cols(),
        z_value=Fraction(0),
    )

    iterations: list[TableauIteration] = []
    iter_no = 1
    is_degenerate = False

    if artificial_set:
        phase1_c = [
            Fraction(-1) if j in artificial_set else Fraction(0) for j in range(sf.num_cols())
        ]
        tableau.z_row = compute_reduced_costs(tableau, phase1_c, Fraction(0))
        tableau.z_value = compute_z_value(tableau, phase1_c, Fraction(0))

        _status, iter_no, degenerate_seen = run_phase(
            tableau,
            phase=1,
            iterations=iterations,
            iter_no=iter_no,
            excluded=set(),
            artificial_cols=artificial_set,
        )
        is_degenerate = is_degenerate or degenerate_seen

        if tableau.z_value != 0:
            return SimplexResult(
                status=SolveStatus.INFEASIBLE,
                method=Method.TWO_PHASE,
                iterations=iterations,
                solution=None,
                z=None,
                has_alternate_optima=False,
                is_degenerate=is_degenerate,
                message=INFEASIBLE_MESSAGE,
            )

    tableau.z_row = compute_reduced_costs(tableau, sf.c, Fraction(0))
    tableau.z_value = compute_z_value(tableau, sf.c, Fraction(0))

    status, _iter_no, degenerate_seen = run_phase(
        tableau,
        phase=2 if artificial_set else 0,
        iterations=iterations,
        iter_no=iter_no,
        excluded=artificial_set,
        artificial_cols=artificial_set,
    )
    is_degenerate = is_degenerate or degenerate_seen

    if status == "unbounded":
        return SimplexResult(
            status=SolveStatus.UNBOUNDED,
            method=Method.TWO_PHASE,
            iterations=iterations,
            solution=None,
            z=None,
            has_alternate_optima=False,
            is_degenerate=is_degenerate,
            message=UNBOUNDED_MESSAGE,
        )

    column_values = tableau.column_values()
    original_values = extract_original_values(problem, sf, column_values)
    z_internal = tableau.z_value
    z_final = z_internal if problem.sense == Sense.MAX else -z_internal

    basis_set = set(tableau.basis)
    has_alt = any(
        tableau.z_row[j] == 0 and j not in basis_set and j not in artificial_set
        for j in range(sf.num_cols())
    )
    final_bfs_degenerate = any(tableau.rhs[i] == 0 for i in range(tableau.num_rows()))
    is_degenerate = is_degenerate or final_bfs_degenerate

    message = "Se encontró la solución óptima."
    if has_alt:
        message += ALTERNATE_OPTIMA_NOTE
    if is_degenerate:
        message += DEGENERATE_NOTE

    return SimplexResult(
        status=SolveStatus.OPTIMAL,
        method=Method.TWO_PHASE,
        iterations=iterations,
        solution=original_values,
        z=z_final,
        has_alternate_optima=has_alt,
        is_degenerate=is_degenerate,
        message=message,
    )
