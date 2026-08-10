from fractions import Fraction

import pytest

from app.core.models import Method, SolveStatus
from app.core.simplex.solve import solve_simplex
from tests.helpers import check_constraints_satisfied, evaluate_objective, make_problem


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_mixed_eq_ge_le_constraints(method):
    # Min Z = 4x1 + x2 s.t. 3x1+x2=3, 4x1+3x2>=6, x1+2x2<=4
    # Verified by hand: x1=2/5, x2=9/5, Z=17/5. Exercises '=', '>=' and '<=' in one problem.
    problem = make_problem(
        "min",
        [4, 1],
        [
            ([3, 1], "=", 3),
            ([4, 3], ">=", 6),
            ([1, 2], "<=", 4),
        ],
    )
    result = solve_simplex(problem, method=method)

    assert result.status == SolveStatus.OPTIMAL
    assert result.solution["x1"] == Fraction(2, 5)
    assert result.solution["x2"] == Fraction(9, 5)
    assert result.z == Fraction(17, 5)
    assert check_constraints_satisfied(problem, result.solution)
    assert evaluate_objective(problem, result.solution) == result.z
