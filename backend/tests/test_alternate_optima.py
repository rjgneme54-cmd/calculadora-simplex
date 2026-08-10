from fractions import Fraction

import pytest

from app.core.models import Method, SolveStatus
from app.core.simplex.solve import solve_simplex
from tests.helpers import check_constraints_satisfied, evaluate_objective, make_problem


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_alternate_optima_detected(method):
    # Max Z = 4x1 + 8x2 s.t. x1+2x2<=8, x1<=4
    # Objective (4,8) is parallel to the first constraint (1,2) -> the whole edge
    # between (4,2) and (0,4) is optimal, both giving Z=32.
    problem = make_problem(
        "max",
        [4, 8],
        [
            ([1, 2], "<=", 8),
            ([1, 0], "<=", 4),
        ],
    )
    result = solve_simplex(problem, method=method)

    assert result.status == SolveStatus.OPTIMAL
    assert result.z == Fraction(32)
    assert result.has_alternate_optima is True
    assert "óptimos alternativos" in result.message
    assert check_constraints_satisfied(problem, result.solution)
    assert evaluate_objective(problem, result.solution) == result.z
