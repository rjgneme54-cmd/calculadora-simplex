from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from app.core.models import LPProblem, Sense, SolveStatus, VarSign
from app.core.simplex.two_phase import solve_two_phase
from app.core.standard_form import StandardForm, build_standard_form


@dataclass
class ObjectiveCoeffRange:
    variable_name: str
    current_value: Fraction
    lower: Fraction | None
    upper: Fraction | None
    applicable: bool


@dataclass
class RhsRangeItem:
    constraint_name: str
    current_value: Fraction
    lower: Fraction | None
    upper: Fraction | None
    shadow_price: Fraction


@dataclass
class SensitivityData:
    objective_ranges: list[ObjectiveCoeffRange]
    rhs_ranges: list[RhsRangeItem]


@dataclass
class _FinalTableauView:
    var_names: list[str]
    basis_cols: list[int]
    matrix: list[list[Fraction]]
    rhs: list[Fraction]
    z_row: list[Fraction]


def _solve_for_analysis(problem: LPProblem) -> tuple[StandardForm, _FinalTableauView] | None:
    """Resuelve con Dos Fases (sin importar el método pedido por el usuario) para obtener
    un tableau final sin términos M, apto para análisis de sensibilidad y dualidad."""
    result = solve_two_phase(problem)
    if result.status != SolveStatus.OPTIMAL:
        return None

    sf = build_standard_form(problem)
    final = result.iterations[-1]
    col_index = {name: i for i, name in enumerate(final.var_names)}
    view = _FinalTableauView(
        var_names=final.var_names,
        basis_cols=[col_index[name] for name in final.basis],
        matrix=[list(row) for row in final.matrix],
        rhs=list(final.rhs),
        z_row=list(final.z_row),
    )
    return sf, view


def _rhs_ranges(
    problem: LPProblem, sf: StandardForm, view: _FinalTableauView
) -> list[RhsRangeItem]:
    items: list[RhsRangeItem] = []
    for i, constraint in enumerate(problem.constraints):
        name = constraint.name or f"R{i + 1}"
        identity_col = sf.initial_basis[i]
        column = [row[identity_col] for row in view.matrix]

        lower_candidates = [-view.rhs[r] / c for r, c in enumerate(column) if c > 0]
        upper_candidates = [-view.rhs[r] / c for r, c in enumerate(column) if c < 0]
        delta_lower = max(lower_candidates) if lower_candidates else None
        delta_upper = min(upper_candidates) if upper_candidates else None

        internal_shadow_price = -view.z_row[identity_col]
        shadow_price = (
            internal_shadow_price if problem.sense == Sense.MAX else -internal_shadow_price
        )

        items.append(
            RhsRangeItem(
                constraint_name=name,
                current_value=constraint.rhs,
                lower=(constraint.rhs + delta_lower) if delta_lower is not None else None,
                upper=(constraint.rhs + delta_upper) if delta_upper is not None else None,
                shadow_price=shadow_price,
            )
        )
    return items


def _shift(current: Fraction, delta_internal: Fraction | None, sense_sign: int) -> Fraction | None:
    if delta_internal is None:
        return None
    return current + delta_internal / sense_sign


def _objective_ranges(
    problem: LPProblem, sf: StandardForm, view: _FinalTableauView
) -> list[ObjectiveCoeffRange]:
    basis_set = set(view.basis_cols)
    row_of_col = {col: row for row, col in enumerate(view.basis_cols)}
    sense_sign = 1 if problem.sense == Sense.MAX else -1
    # Artificial variables aren't real feasible directions -- increasing one from 0 would
    # leave the original feasible region, so they must be excluded from ranging, exactly
    # like they're excluded from entering-variable selection during Phase 2.
    excluded_cols = basis_set | set(sf.artificial_cols)

    items: list[ObjectiveCoeffRange] = []
    for var_idx, variable in enumerate(problem.variables):
        current = problem.objective[var_idx]

        if variable.sign == VarSign.FREE:
            items.append(ObjectiveCoeffRange(variable.name, current, None, None, applicable=False))
            continue

        col = sf.var_names.index(variable.name)

        if col not in basis_set:
            delta_lower_internal = None
            delta_upper_internal = -view.z_row[col]
        else:
            row = row_of_col[col]
            lower_candidates = []
            upper_candidates = []
            for k in range(len(view.var_names)):
                if k in excluded_cols:
                    continue
                coeff = view.matrix[row][k]
                if coeff == 0:
                    continue
                ratio = view.z_row[k] / coeff
                if coeff > 0:
                    lower_candidates.append(ratio)
                else:
                    upper_candidates.append(ratio)
            delta_lower_internal = max(lower_candidates) if lower_candidates else None
            delta_upper_internal = min(upper_candidates) if upper_candidates else None

        # Perturbing the *original* c_j by delta changes the internal (canonical-max)
        # objective by sense_sign * delta, so converting an internal delta bound back to
        # the original requires dividing by sense_sign -- for MIN (sense_sign=-1) this both
        # negates and swaps which internal bound becomes the original lower/upper.
        if sense_sign == 1:
            lower = _shift(current, delta_lower_internal, sense_sign)
            upper = _shift(current, delta_upper_internal, sense_sign)
        else:
            lower = _shift(current, delta_upper_internal, sense_sign)
            upper = _shift(current, delta_lower_internal, sense_sign)

        items.append(ObjectiveCoeffRange(variable.name, current, lower, upper, applicable=True))

    return items


def compute_sensitivity(problem: LPProblem) -> SensitivityData | None:
    analysis = _solve_for_analysis(problem)
    if analysis is None:
        return None
    sf, view = analysis

    return SensitivityData(
        objective_ranges=_objective_ranges(problem, sf, view),
        rhs_ranges=_rhs_ranges(problem, sf, view),
    )
