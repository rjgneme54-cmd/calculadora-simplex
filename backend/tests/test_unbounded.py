import pytest

from app.core.models import Method, SolveStatus
from app.core.simplex.solve import solve_simplex
from tests.helpers import make_problem


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_unbounded_problem_detected(method):
    # Max Z = x1 + x2 s.t. x1 - x2 <= 1  -> region unbounded in the x2 direction
    problem = make_problem(
        "max",
        [1, 1],
        [
            ([1, -1], "<=", 1),
        ],
    )
    result = solve_simplex(problem, method=method)

    assert result.status == SolveStatus.UNBOUNDED
    assert result.solution is None
    assert result.z is None
    assert "no tiene solución acotada" in result.message
    assert len(result.iterations) >= 1
    last = result.iterations[-1]
    assert last.entering is not None
    assert last.leaving is None
    assert last.pivot_element is None
