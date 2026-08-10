from fractions import Fraction

import pytest

from app.core.models import Method, SolveStatus
from app.core.simplex.solve import solve_simplex
from tests.helpers import check_constraints_satisfied, evaluate_objective, make_problem


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_degenerate_solution_detected(method):
    # Classic degenerate example: Max Z = 3x1 + 9x2 s.t. x1+4x2<=8, x1+2x2<=4
    # Both constraints pass through (0,2) -> tie in the first ratio test -> degeneracy.
    # Optimal by hand: (0,2), Z=18.
    problem = make_problem(
        "max",
        [3, 9],
        [
            ([1, 4], "<=", 8),
            ([1, 2], "<=", 4),
        ],
    )
    result = solve_simplex(problem, method=method)

    assert result.status == SolveStatus.OPTIMAL
    assert result.solution["x1"] == Fraction(0)
    assert result.solution["x2"] == Fraction(2)
    assert result.z == Fraction(18)
    assert result.is_degenerate is True
    assert "degenerada" in result.message
    assert check_constraints_satisfied(problem, result.solution)
    assert evaluate_objective(problem, result.solution) == result.z
