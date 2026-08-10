from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from app.core.models import ConstraintOp, LPProblem, Sense, VarSign
from app.core.sensitivity import compute_sensitivity
from app.core.simplex.two_phase import solve_two_phase


@dataclass
class DualVariable:
    name: str
    primal_constraint_name: str
    sign: str
    value: Fraction


@dataclass
class DualConstraint:
    primal_variable_name: str
    coeffs: list[Fraction]
    op: str
    rhs: Fraction


@dataclass
class ComplementarySlacknessItem:
    description: str
    holds: bool


@dataclass
class DualData:
    dual_sense: Sense
    dual_variables: list[DualVariable]
    dual_constraints: list[DualConstraint]
    dual_objective_coeffs: list[Fraction]
    primal_z: Fraction
    dual_z: Fraction
    strong_duality_holds: bool
    complementary_slackness: list[ComplementarySlacknessItem]


def _dual_variable_sign(sense: Sense, op: ConstraintOp) -> str:
    if op == ConstraintOp.EQ:
        return "free"
    if sense == Sense.MAX:
        return "nonnegative" if op == ConstraintOp.LE else "nonpositive"
    return "nonnegative" if op == ConstraintOp.GE else "nonpositive"


def _dual_constraint_op(sense: Sense, var_sign: VarSign) -> str:
    if var_sign == VarSign.FREE:
        return "="
    return ">=" if sense == Sense.MAX else "<="


def _constraint_lhs(
    coeffs: list[Fraction], solution: dict[str, Fraction], problem: LPProblem
) -> Fraction:
    return sum(
        (coeff * solution[var.name] for coeff, var in zip(coeffs, problem.variables, strict=True)),
        Fraction(0),
    )


def _primal_slack(op: ConstraintOp, lhs: Fraction, rhs: Fraction) -> Fraction:
    if op == ConstraintOp.LE:
        return rhs - lhs
    if op == ConstraintOp.GE:
        return lhs - rhs
    return Fraction(0)


def compute_duality(problem: LPProblem) -> DualData | None:
    sensitivity = compute_sensitivity(problem)
    if sensitivity is None:
        return None

    primal_result = solve_two_phase(problem)
    solution = primal_result.solution

    dual_sense = Sense.MIN if problem.sense == Sense.MAX else Sense.MAX

    dual_variables = [
        DualVariable(
            name=f"y{i + 1}",
            primal_constraint_name=rhs_range.constraint_name,
            sign=_dual_variable_sign(problem.sense, constraint.op),
            value=rhs_range.shadow_price,
        )
        for i, (constraint, rhs_range) in enumerate(
            zip(problem.constraints, sensitivity.rhs_ranges, strict=True)
        )
    ]

    dual_constraints = [
        DualConstraint(
            primal_variable_name=variable.name,
            coeffs=[constraint.coeffs[j] for constraint in problem.constraints],
            op=_dual_constraint_op(problem.sense, variable.sign),
            rhs=problem.objective[j],
        )
        for j, variable in enumerate(problem.variables)
    ]

    dual_objective_coeffs = [constraint.rhs for constraint in problem.constraints]
    dual_z = sum(
        (b * v.value for b, v in zip(dual_objective_coeffs, dual_variables, strict=True)),
        Fraction(0),
    )

    slackness: list[ComplementarySlacknessItem] = []
    for i, constraint in enumerate(problem.constraints):
        lhs = _constraint_lhs(constraint.coeffs, solution, problem)
        primal_slack = _primal_slack(constraint.op, lhs, constraint.rhs)
        y = dual_variables[i].value
        holds = primal_slack == 0 or y == 0
        slackness.append(
            ComplementarySlacknessItem(
                description=(
                    f"{dual_variables[i].primal_constraint_name}: holgura primal = "
                    f"{primal_slack}, {dual_variables[i].name} = {y}"
                ),
                holds=holds,
            )
        )

    for j, variable in enumerate(problem.variables):
        x_j = solution[variable.name]
        dual_lhs = sum(
            (
                constraint.coeffs[j] * dual_variables[i].value
                for i, constraint in enumerate(problem.constraints)
            ),
            Fraction(0),
        )
        c_j = problem.objective[j]
        if variable.sign == VarSign.FREE:
            holds = dual_lhs == c_j
            description = f"{variable.name} (libre): restricción dual exacta -> {dual_lhs} = {c_j}"
        else:
            dual_slack = (dual_lhs - c_j) if problem.sense == Sense.MAX else (c_j - dual_lhs)
            holds = x_j == 0 or dual_slack == 0
            description = f"{variable.name} = {x_j}, holgura dual = {dual_slack}"
        slackness.append(ComplementarySlacknessItem(description=description, holds=holds))

    return DualData(
        dual_sense=dual_sense,
        dual_variables=dual_variables,
        dual_constraints=dual_constraints,
        dual_objective_coeffs=dual_objective_coeffs,
        primal_z=primal_result.z,
        dual_z=dual_z,
        strong_duality_holds=primal_result.z == dual_z,
        complementary_slackness=slackness,
    )
