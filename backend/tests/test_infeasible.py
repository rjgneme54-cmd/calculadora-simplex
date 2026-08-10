import pytest

from app.core.models import Method, SolveStatus
from app.core.simplex.solve import solve_simplex
from tests.helpers import make_problem


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_infeasible_problem_detected(method):
    # Max Z = x1 + x2 s.t. x1+x2<=2, x1+x2>=6 -> contradictory, empty feasible region
    problem = make_problem(
        "max",
        [1, 1],
        [
            ([1, 1], "<=", 2),
            ([1, 1], ">=", 6),
        ],
    )
    result = solve_simplex(problem, method=method)

    assert result.status == SolveStatus.INFEASIBLE
    assert result.solution is None
    assert result.z is None
    assert "no tiene solución factible" in result.message
