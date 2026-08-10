from __future__ import annotations

from app.core.models import TableauIteration
from app.core.simplex.narration import explain_optimal, explain_pivot, explain_unbounded
from app.core.simplex.pivot import Tableau, apply_pivot, compute_ratio_test, select_entering_column

BLAND_THRESHOLD = 200
HARD_ITERATION_LIMIT = 2000


def run_phase(
    tableau: Tableau,
    phase: int,
    iterations: list[TableauIteration],
    iter_no: int,
    excluded: set[int],
    artificial_cols: set[int] | None = None,
) -> tuple[str, int, bool]:
    degenerate_seen = False
    pivots_done = 0
    artificial_cols = artificial_cols or set()

    while True:
        if pivots_done > HARD_ITERATION_LIMIT:
            raise RuntimeError("El método simplex no convergió dentro del límite de iteraciones.")
        use_bland = pivots_done > BLAND_THRESHOLD

        entering = select_entering_column(tableau.z_row, excluded=excluded, use_bland=use_bland)

        if entering is None:
            basis_names, matrix, rhs, z_row, z_value = tableau.snapshot()
            iterations.append(
                TableauIteration(
                    iteration=iter_no,
                    phase=phase,
                    basis=basis_names,
                    var_names=tableau.var_names,
                    matrix=matrix,
                    rhs=rhs,
                    z_row=z_row,
                    z_value=z_value,
                    entering=None,
                    leaving=None,
                    pivot_row=None,
                    pivot_col=None,
                    pivot_element=None,
                    ratio_test=[],
                    explanation=explain_optimal(phase),
                    is_optimal=True,
                )
            )
            return "optimal", iter_no, degenerate_seen

        entering_name = tableau.var_names[entering]
        protected_rows = {
            i
            for i, basis_col in enumerate(tableau.basis)
            if basis_col in artificial_cols and tableau.rhs[i] == 0
        }
        ratio_rows, leaving_row, tie = compute_ratio_test(tableau, entering, protected_rows)

        if leaving_row is None:
            basis_names, matrix, rhs, z_row, z_value = tableau.snapshot()
            iterations.append(
                TableauIteration(
                    iteration=iter_no,
                    phase=phase,
                    basis=basis_names,
                    var_names=tableau.var_names,
                    matrix=matrix,
                    rhs=rhs,
                    z_row=z_row,
                    z_value=z_value,
                    entering=entering_name,
                    leaving=None,
                    pivot_row=None,
                    pivot_col=entering,
                    pivot_element=None,
                    ratio_test=ratio_rows,
                    explanation=explain_unbounded(entering_name),
                    is_optimal=False,
                )
            )
            return "unbounded", iter_no, degenerate_seen

        if tie:
            degenerate_seen = True

        leaving_name = tableau.var_names[tableau.basis[leaving_row]]
        basis_names, matrix, rhs, z_row, z_value = tableau.snapshot()
        pivot_element_val = tableau.body[leaving_row][entering]

        iterations.append(
            TableauIteration(
                iteration=iter_no,
                phase=phase,
                basis=basis_names,
                var_names=tableau.var_names,
                matrix=matrix,
                rhs=rhs,
                z_row=z_row,
                z_value=z_value,
                entering=entering_name,
                leaving=leaving_name,
                pivot_row=leaving_row,
                pivot_col=entering,
                pivot_element=pivot_element_val,
                ratio_test=ratio_rows,
                explanation=explain_pivot(entering_name, leaving_name, pivot_element_val, phase),
                is_optimal=False,
                is_degenerate_step=tie,
            )
        )

        apply_pivot(tableau, leaving_row, entering)
        iter_no += 1
        pivots_done += 1
