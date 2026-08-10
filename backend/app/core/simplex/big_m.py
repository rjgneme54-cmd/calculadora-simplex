from __future__ import annotations

from fractions import Fraction

from app.core.models import LPProblem, Method, Sense, SimplexResult, SolveStatus, TableauIteration
from app.core.simplex.big_m_number import BigMNumber
from app.core.simplex.engine_loop import run_phase
from app.core.simplex.pivot import Tableau, compute_reduced_costs, compute_z_value
from app.core.simplex.two_phase import ALTERNATE_OPTIMA_NOTE, DEGENERATE_NOTE, UNBOUNDED_MESSAGE
from app.core.standard_form import build_standard_form, extract_original_values

INFEASIBLE_MESSAGE = (
    "El problema no tiene solución factible: al menos una variable artificial "
    "permanece positiva en el óptimo (su costo -M no bastó para sacarla de la base), "
    "lo que significa que no existe ningún punto que satisfaga todas las "
    "restricciones simultáneamente."
)


def solve_big_m(problem: LPProblem) -> SimplexResult:
    sf = build_standard_form(problem)
    artificial_set = set(sf.artificial_cols)

    tableau = Tableau(
        var_names=sf.var_names,
        basis=list(sf.initial_basis),
        body=[row[:] for row in sf.a],
        rhs=list(sf.b),
        z_row=[BigMNumber(0) for _ in range(sf.num_cols())],
        z_value=BigMNumber(0),
    )

    c_bigm = [
        BigMNumber(sf.c[j], Fraction(-1)) if j in artificial_set else BigMNumber(sf.c[j])
        for j in range(sf.num_cols())
    ]
    tableau.z_row = compute_reduced_costs(tableau, c_bigm, BigMNumber(0))
    tableau.z_value = compute_z_value(tableau, c_bigm, BigMNumber(0))

    iterations: list[TableauIteration] = []
    status, _iter_no, is_degenerate = run_phase(
        tableau,
        phase=0,
        iterations=iterations,
        iter_no=1,
        excluded=artificial_set,
        artificial_cols=artificial_set,
    )

    if status == "unbounded":
        return SimplexResult(
            status=SolveStatus.UNBOUNDED,
            method=Method.BIG_M,
            iterations=iterations,
            solution=None,
            z=None,
            has_alternate_optima=False,
            is_degenerate=is_degenerate,
            message=UNBOUNDED_MESSAGE,
        )

    infeasible = any(
        tableau.basis[i] in artificial_set and tableau.rhs[i] != 0
        for i in range(tableau.num_rows())
    )
    if infeasible:
        return SimplexResult(
            status=SolveStatus.INFEASIBLE,
            method=Method.BIG_M,
            iterations=iterations,
            solution=None,
            z=None,
            has_alternate_optima=False,
            is_degenerate=is_degenerate,
            message=INFEASIBLE_MESSAGE,
        )

    column_values = tableau.column_values()
    original_values = extract_original_values(problem, sf, column_values)
    z_internal = tableau.z_value.const
    z_final = z_internal if problem.sense == Sense.MAX else -z_internal

    basis_set = set(tableau.basis)
    has_alt = any(
        tableau.z_row[j].is_zero() and j not in basis_set and j not in artificial_set
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
        method=Method.BIG_M,
        iterations=iterations,
        solution=original_values,
        z=z_final,
        has_alternate_optima=has_alt,
        is_degenerate=is_degenerate,
        message=message,
    )
