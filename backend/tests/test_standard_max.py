from fractions import Fraction

import pytest

from app.core.models import Method, SolveStatus
from app.core.simplex.solve import solve_simplex
from tests.helpers import check_constraints_satisfied, evaluate_objective, make_problem


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_wyndor_glass_standard_max(method):
    # Hillier & Lieberman: Max Z = 3x1 + 5x2 s.t. x1<=4, 2x2<=12, 3x1+2x2<=18
    problem = make_problem(
        "max",
        [3, 5],
        [
            ([1, 0], "<=", 4),
            ([0, 2], "<=", 12),
            ([3, 2], "<=", 18),
        ],
    )
    result = solve_simplex(problem, method=method)

    assert result.status == SolveStatus.OPTIMAL
    assert result.solution["x1"] == Fraction(2)
    assert result.solution["x2"] == Fraction(6)
    assert result.z == Fraction(36)
    assert result.has_alternate_optima is False
    assert result.is_degenerate is False
    assert check_constraints_satisfied(problem, result.solution)
    assert evaluate_objective(problem, result.solution) == result.z
    assert len(result.iterations) >= 1
    assert result.iterations[-1].is_optimal is True


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_iteration_snapshots_are_structured(method):
    problem = make_problem(
        "max",
        [3, 5],
        [
            ([1, 0], "<=", 4),
            ([0, 2], "<=", 12),
            ([3, 2], "<=", 18),
        ],
    )
    result = solve_simplex(problem, method=method)

    for iteration in result.iterations:
        assert iteration.var_names
        assert len(iteration.matrix) == len(iteration.basis)
        for row in iteration.matrix:
            assert len(row) == len(iteration.var_names)
        assert len(iteration.z_row) == len(iteration.var_names)
        assert isinstance(iteration.explanation, str) and len(iteration.explanation) > 0

    non_final = result.iterations[:-1]
    assert all(it.entering is not None for it in non_final)
    assert all(it.pivot_row is not None for it in non_final)
