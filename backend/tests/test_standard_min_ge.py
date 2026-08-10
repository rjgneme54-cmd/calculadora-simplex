from fractions import Fraction

import pytest

from app.core.models import Method, SolveStatus
from app.core.simplex.solve import solve_simplex
from tests.helpers import check_constraints_satisfied, evaluate_objective, make_problem


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_minimization_with_ge_constraints(method):
    # Min Z = 2x1 + 3x2 s.t. x1+x2>=4, x1+2x2>=6  -> optimal (2,2), Z=10 (verified by hand)
    problem = make_problem(
        "min",
        [2, 3],
        [
            ([1, 1], ">=", 4),
            ([1, 2], ">=", 6),
        ],
    )
    result = solve_simplex(problem, method=method)

    assert result.status == SolveStatus.OPTIMAL
    assert result.solution["x1"] == Fraction(2)
    assert result.solution["x2"] == Fraction(2)
    assert result.z == Fraction(10)
    assert check_constraints_satisfied(problem, result.solution)
    assert evaluate_objective(problem, result.solution) == result.z

    phases_used = {it.phase for it in result.iterations}
    if method == Method.TWO_PHASE:
        assert 1 in phases_used
