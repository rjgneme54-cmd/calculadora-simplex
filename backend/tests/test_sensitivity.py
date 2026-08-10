from fractions import Fraction

from app.core.models import SolveStatus
from app.core.sensitivity import compute_sensitivity
from app.core.simplex.solve import solve_simplex
from tests.helpers import make_problem


def wyndor():
    return make_problem(
        "max",
        [3, 5],
        [
            ([1, 0], "<=", 4),
            ([0, 2], "<=", 12),
            ([3, 2], "<=", 18),
        ],
    )


def test_shadow_prices_match_hand_verified_values():
    # Hand-verified: relaxing constraint 3 (binding) by 1 raises Z from 36 to 37 (shadow price 1).
    # Relaxing constraint 2 (binding) by 1 raises Z to 37.5 (shadow price 3/2).
    # Constraint 1 is slack at the optimum (x1=2<4), so its shadow price is 0.
    problem = wyndor()
    data = compute_sensitivity(problem)

    assert data is not None
    prices = {r.constraint_name: r.shadow_price for r in data.rhs_ranges}
    assert prices["R1"] == Fraction(0)
    assert prices["R2"] == Fraction(3, 2)
    assert prices["R3"] == Fraction(1)


def test_rhs_range_is_consistent_with_shadow_price_at_and_beyond_the_boundary():
    problem = wyndor()
    data = compute_sensitivity(problem)
    original_result = solve_simplex(problem)

    r3 = next(r for r in data.rhs_ranges if r.constraint_name == "R3")
    assert r3.upper is not None

    # At the boundary, the basis is still optimal and Z follows the linear shadow-price formula.
    boundary_problem = make_problem(
        "max",
        [3, 5],
        [([1, 0], "<=", 4), ([0, 2], "<=", 12), ([3, 2], "<=", r3.upper)],
    )
    boundary_result = solve_simplex(boundary_problem)
    assert boundary_result.status == SolveStatus.OPTIMAL
    expected_z = original_result.z + r3.shadow_price * (r3.upper - Fraction(18))
    assert boundary_result.z == expected_z

    # One unit past the boundary, the linear relationship must break (different active basis).
    beyond_problem = make_problem(
        "max",
        [3, 5],
        [([1, 0], "<=", 4), ([0, 2], "<=", 12), ([3, 2], "<=", r3.upper + 1)],
    )
    beyond_result = solve_simplex(beyond_problem)
    beyond_expected_if_unchanged = original_result.z + r3.shadow_price * (
        r3.upper + 1 - Fraction(18)
    )
    assert beyond_result.z != beyond_expected_if_unchanged


def test_objective_coefficient_range_for_basic_and_nonbasic_variables():
    problem = wyndor()
    data = compute_sensitivity(problem)

    ranges = {r.variable_name: r for r in data.objective_ranges}
    x1_range = ranges["x1"]
    x2_range = ranges["x2"]

    # Both x1 and x2 are basic at the optimum (2, 6). At the exact boundary of the range,
    # (2, 6) ties with a neighboring vertex for optimal Z (that's what defines the boundary),
    # so we check Z equality rather than which of the tied vertices the engine reports.
    for name, r in [("x1", x1_range), ("x2", x2_range)]:
        assert r.applicable is True
        if r.upper is not None:
            perturbed_obj = [3, 5]
            perturbed_obj[0 if name == "x1" else 1] = r.upper
            perturbed = make_problem(
                "max",
                perturbed_obj,
                [([1, 0], "<=", 4), ([0, 2], "<=", 12), ([3, 2], "<=", 18)],
            )
            result = solve_simplex(perturbed)
            expected_z = perturbed_obj[0] * Fraction(2) + perturbed_obj[1] * Fraction(6)
            assert result.status == SolveStatus.OPTIMAL
            assert result.z == expected_z
            assert result.has_alternate_optima is True


def test_sensitivity_returns_none_when_not_optimal():
    unbounded = make_problem("max", [1, 1], [([1, -1], "<=", 1)])
    assert compute_sensitivity(unbounded) is None

    infeasible = make_problem("max", [1, 1], [([1, 1], "<=", 2), ([1, 1], ">=", 6)])
    assert compute_sensitivity(infeasible) is None


def test_sensitivity_on_minimization_problem_shadow_price_sign():
    # Min Z = 2x1 + 3x2 s.t. x1+x2>=4, x1+2x2>=6 -> optimal (2,2), Z=10.
    # Tightening (raising) a binding >= constraint's RHS by 1 can only increase the minimum cost,
    # so the reported shadow price must be >= 0 for a binding constraint in a min problem too
    # (economically: "cost of tightening the requirement").
    problem = make_problem("min", [2, 3], [([1, 1], ">=", 4), ([1, 2], ">=", 6)])
    data = compute_sensitivity(problem)
    original_result = solve_simplex(problem)

    assert data is not None
    r2 = next(r for r in data.rhs_ranges if r.constraint_name == "R2")

    tightened = make_problem("min", [2, 3], [([1, 1], ">=", 4), ([1, 2], ">=", 7)])
    tightened_result = solve_simplex(tightened)
    assert tightened_result.status == SolveStatus.OPTIMAL
    assert tightened_result.z == original_result.z + r2.shadow_price * Fraction(1)


def test_objective_coefficient_range_on_minimization_problem():
    # Min Z = 2x1 + 3x2 s.t. x1+x2>=4, x1+2x2>=6 -> optimal (2,2).
    # Hand-derived (comparing Z at (2,2) vs neighboring vertices (6,0) and (0,4)):
    # c1 can range in [3/2, 3] before a different vertex becomes optimal.
    problem = make_problem("min", [2, 3], [([1, 1], ">=", 4), ([1, 2], ">=", 6)])
    data = compute_sensitivity(problem)
    x1_range = next(r for r in data.objective_ranges if r.variable_name == "x1")

    assert x1_range.lower == Fraction(3, 2)
    assert x1_range.upper == Fraction(3)

    at_lower = make_problem("min", [x1_range.lower, 3], [([1, 1], ">=", 4), ([1, 2], ">=", 6)])
    result_at_lower = solve_simplex(at_lower)
    assert result_at_lower.status == SolveStatus.OPTIMAL
    assert result_at_lower.solution["x1"] == Fraction(2)
    assert result_at_lower.solution["x2"] == Fraction(2)

    below_lower = make_problem(
        "min", [x1_range.lower - 1, 3], [([1, 1], ">=", 4), ([1, 2], ">=", 6)]
    )
    result_below = solve_simplex(below_lower)
    assert not (
        result_below.solution["x1"] == Fraction(2) and result_below.solution["x2"] == Fraction(2)
    )
