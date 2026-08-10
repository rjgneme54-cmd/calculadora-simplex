from fractions import Fraction

import pytest

from app.core.graphical import compute_graphical_data
from app.core.models import Method
from app.core.simplex.solve import solve_simplex
from tests.helpers import make_problem


def vertex_points(data):
    return {(v.x, v.y) for v in data.feasible_vertices}


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_graphical_bounded_unique_optimum(method):
    # Wyndor Glass: pentagon with 5 feasible vertices, unique optimum at (2,6), Z=36.
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
    data = compute_graphical_data(problem, result)

    assert data is not None
    assert data.var_names == ("x1", "x2")
    assert len(data.lines) == 3
    assert vertex_points(data) == {
        (Fraction(0), Fraction(0)),
        (Fraction(4), Fraction(0)),
        (Fraction(4), Fraction(3)),
        (Fraction(2), Fraction(6)),
        (Fraction(0), Fraction(6)),
    }
    assert len(data.optimal_vertices) == 1
    optimal = data.optimal_vertices[0]
    assert (optimal.x, optimal.y) == (Fraction(2), Fraction(6))
    assert optimal.z == Fraction(36)
    assert optimal.z == result.z
    assert data.is_unbounded_region is False


def test_graphical_alternate_optima_marks_both_vertices_of_the_edge():
    problem = make_problem(
        "max",
        [4, 8],
        [
            ([1, 2], "<=", 8),
            ([1, 0], "<=", 4),
        ],
    )
    result = solve_simplex(problem)
    data = compute_graphical_data(problem, result)

    assert vertex_points(data) == {
        (Fraction(0), Fraction(0)),
        (Fraction(4), Fraction(0)),
        (Fraction(4), Fraction(2)),
        (Fraction(0), Fraction(4)),
    }
    assert len(data.optimal_vertices) == 2
    optimal_points = {(v.x, v.y) for v in data.optimal_vertices}
    assert optimal_points == {(Fraction(4), Fraction(2)), (Fraction(0), Fraction(4))}
    assert all(v.z == Fraction(32) for v in data.optimal_vertices)


def test_graphical_degenerate_vertex_is_not_duplicated():
    # Three boundary lines (x1+4x2=8, x1+2x2=4, x1=0) all meet at (0,2): must dedupe to one vertex.
    problem = make_problem(
        "max",
        [3, 9],
        [
            ([1, 4], "<=", 8),
            ([1, 2], "<=", 4),
        ],
    )
    result = solve_simplex(problem)
    data = compute_graphical_data(problem, result)

    assert vertex_points(data) == {
        (Fraction(0), Fraction(0)),
        (Fraction(4), Fraction(0)),
        (Fraction(0), Fraction(2)),
    }
    assert len(data.optimal_vertices) == 1
    assert (data.optimal_vertices[0].x, data.optimal_vertices[0].y) == (Fraction(0), Fraction(2))
    assert data.optimal_vertices[0].z == Fraction(18)


def test_graphical_unbounded_has_no_optimal_vertex():
    problem = make_problem("max", [1, 1], [([1, -1], "<=", 1)])
    result = solve_simplex(problem)
    data = compute_graphical_data(problem, result)

    assert data.is_unbounded_region is True
    assert data.optimal_vertices == []
    assert vertex_points(data) == {(Fraction(0), Fraction(0)), (Fraction(1), Fraction(0))}


def test_graphical_infeasible_has_no_feasible_vertices():
    problem = make_problem("max", [1, 1], [([1, 1], "<=", 2), ([1, 1], ">=", 6)])
    result = solve_simplex(problem)
    data = compute_graphical_data(problem, result)

    assert data.feasible_vertices == []
    assert data.optimal_vertices == []
    assert data.is_unbounded_region is False


def test_graphical_returns_none_for_non_two_variable_problems():
    problem = make_problem("max", [1, 1, 1], [([1, 1, 1], "<=", 10)])
    result = solve_simplex(problem)
    assert compute_graphical_data(problem, result) is None
