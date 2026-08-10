from __future__ import annotations

from fractions import Fraction

from app.core.models import Constraint, ConstraintOp, LPProblem, Sense, Variable, VarSign


def frac(x) -> Fraction:
    if isinstance(x, tuple):
        return Fraction(*x)
    return Fraction(x)


def make_problem(
    sense: str,
    objective: list,
    constraints: list[tuple[list, str, object]],
    var_signs: list[VarSign] | None = None,
) -> LPProblem:
    n = len(objective)
    var_signs = var_signs or [VarSign.NONNEGATIVE] * n
    variables = [Variable(name=f"x{i + 1}", sign=var_signs[i]) for i in range(n)]
    objective_fracs = [frac(c) for c in objective]
    cons = []
    for coeffs, op, rhs in constraints:
        cons.append(
            Constraint(coeffs=[frac(c) for c in coeffs], op=ConstraintOp(op), rhs=frac(rhs))
        )
    return LPProblem(
        sense=Sense(sense), objective=objective_fracs, variables=variables, constraints=cons
    )


def evaluate_objective(problem: LPProblem, solution: dict[str, Fraction]) -> Fraction:
    total = Fraction(0)
    for var, coeff in zip(problem.variables, problem.objective, strict=True):
        total += coeff * solution[var.name]
    return total


def check_constraints_satisfied(problem: LPProblem, solution: dict[str, Fraction]) -> bool:
    for constraint in problem.constraints:
        lhs = Fraction(0)
        for var, coeff in zip(problem.variables, constraint.coeffs, strict=True):
            lhs += coeff * solution[var.name]
        if constraint.op == ConstraintOp.LE and lhs > constraint.rhs:
            return False
        if constraint.op == ConstraintOp.GE and lhs < constraint.rhs:
            return False
        if constraint.op == ConstraintOp.EQ and lhs != constraint.rhs:
            return False
    for var in problem.variables:
        if var.sign == VarSign.NONNEGATIVE and solution[var.name] < 0:
            return False
    return True
