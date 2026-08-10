import random

import pytest
from scipy.optimize import linprog

from app.core.models import ConstraintOp, LPProblem, Method, Sense, SolveStatus, VarSign
from app.core.simplex.solve import solve_simplex
from tests.helpers import make_problem

TOL = 1e-6


def scipy_optimum(problem: LPProblem) -> tuple[int, float | None]:
    sign = -1 if problem.sense == Sense.MAX else 1
    c = [sign * float(coeff) for coeff in problem.objective]

    a_ub, b_ub, a_eq, b_eq = [], [], [], []
    for constraint in problem.constraints:
        row = [float(v) for v in constraint.coeffs]
        rhs = float(constraint.rhs)
        if constraint.op == ConstraintOp.LE:
            a_ub.append(row)
            b_ub.append(rhs)
        elif constraint.op == ConstraintOp.GE:
            a_ub.append([-v for v in row])
            b_ub.append(-rhs)
        else:
            a_eq.append(row)
            b_eq.append(rhs)

    bounds = [
        (0, None) if v.sign == VarSign.NONNEGATIVE else (None, None) for v in problem.variables
    ]

    res = linprog(
        c,
        A_ub=a_ub or None,
        b_ub=b_ub or None,
        A_eq=a_eq or None,
        b_eq=b_eq or None,
        bounds=bounds,
        method="highs",
    )
    if res.status == 0:
        return 0, sign * res.fun
    return res.status, None


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
@pytest.mark.parametrize(
    "sense,objective,constraints",
    [
        ("max", [3, 5], [([1, 0], "<=", 4), ([0, 2], "<=", 12), ([3, 2], "<=", 18)]),
        ("min", [2, 3], [([1, 1], ">=", 4), ([1, 2], ">=", 6)]),
        ("min", [4, 1], [([3, 1], "=", 3), ([4, 3], ">=", 6), ([1, 2], "<=", 4)]),
        ("max", [3, 9], [([1, 4], "<=", 8), ([1, 2], "<=", 4)]),
    ],
)
def test_engine_matches_scipy_on_curated_cases(method, sense, objective, constraints):
    problem = make_problem(sense, objective, constraints)
    result = solve_simplex(problem, method=method)
    status, scipy_z = scipy_optimum(problem)

    assert status == 0
    assert result.status == SolveStatus.OPTIMAL
    assert float(result.z) == pytest.approx(scipy_z, abs=1e-6)


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_engine_matches_scipy_on_unbounded_and_infeasible(method):
    unbounded = make_problem("max", [1, 1], [([1, -1], "<=", 1)])
    status, _ = scipy_optimum(unbounded)
    assert status == 3
    assert solve_simplex(unbounded, method=method).status == SolveStatus.UNBOUNDED

    infeasible = make_problem("max", [1, 1], [([1, 1], "<=", 2), ([1, 1], ">=", 6)])
    status, _ = scipy_optimum(infeasible)
    assert status == 2
    assert solve_simplex(infeasible, method=method).status == SolveStatus.INFEASIBLE


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_engine_matches_scipy_on_random_small_lps(method):
    rng = random.Random(42)
    for _ in range(8):
        n = rng.randint(2, 3)
        m = rng.randint(2, 3)
        objective = [rng.randint(1, 9) for _ in range(n)]
        constraints = []
        for _ in range(m):
            coeffs = [rng.randint(1, 9) for _ in range(n)]
            rhs = rng.randint(20, 60)
            constraints.append((coeffs, "<=", rhs))
        problem = make_problem("max", objective, constraints)

        result = solve_simplex(problem, method=method)
        status, scipy_z = scipy_optimum(problem)

        assert status == 0
        assert result.status == SolveStatus.OPTIMAL
        assert float(result.z) == pytest.approx(scipy_z, abs=1e-6)
