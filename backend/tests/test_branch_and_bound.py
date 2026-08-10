from fractions import Fraction

import numpy as np
import pytest
from scipy.optimize import Bounds, LinearConstraint, milp

from app.core.branch_and_bound import compute_branch_and_bound, has_integer_requirements
from app.core.models import VarKind
from tests.helpers import make_problem


def with_kinds(problem, kinds):
    for var, kind in zip(problem.variables, kinds, strict=True):
        var.kind = kind
    return problem


def scipy_milp_optimum(problem, integrality, bounds_upper=None):
    sign = -1 if problem.sense.value == "max" else 1
    c = [sign * float(v) for v in problem.objective]
    a_rows, lb, ub = [], [], []
    for constraint in problem.constraints:
        row = [float(v) for v in constraint.coeffs]
        rhs = float(constraint.rhs)
        a_rows.append(row)
        if constraint.op.value == "<=":
            lb.append(-np.inf)
            ub.append(rhs)
        elif constraint.op.value == ">=":
            lb.append(rhs)
            ub.append(np.inf)
        else:
            lb.append(rhs)
            ub.append(rhs)
    upper = bounds_upper or [np.inf] * len(problem.variables)
    res = milp(
        c,
        constraints=LinearConstraint(a_rows, lb, ub),
        integrality=integrality,
        bounds=Bounds(lb=[0] * len(problem.variables), ub=upper),
    )
    return sign * res.fun


def test_classic_integer_knapsack_style_problem():
    # Max Z = 5x1 + 4x2 s.t. 6x1+4x2<=24, x1+2x2<=6, x1,x2 integer.
    # LP relaxation optimum is (3, 1.5, Z=21); hand-verified integer optimum is (4, 0, Z=20).
    problem = with_kinds(
        make_problem("max", [5, 4], [([6, 4], "<=", 24), ([1, 2], "<=", 6)]),
        [VarKind.INTEGER, VarKind.INTEGER],
    )
    assert has_integer_requirements(problem)
    result = compute_branch_and_bound(problem)

    assert result.status == "optimal"
    assert result.solution["x1"] == Fraction(4)
    assert result.solution["x2"] == Fraction(0)
    assert result.z == Fraction(20)

    scipy_z = scipy_milp_optimum(problem, integrality=[1, 1])
    assert float(result.z) == pytest.approx(scipy_z, abs=1e-6)

    # Structural sanity checks on the tree.
    assert len(result.nodes) >= 1
    root = next(n for n in result.nodes if n.parent_id is None)
    assert root.depth == 0
    for node in result.nodes:
        if node.parent_id is not None:
            parent = next(n for n in result.nodes if n.id == node.parent_id)
            assert node.depth == parent.depth + 1
    leaf_outcomes = {"pruned_infeasible", "pruned_bound", "pruned_integer"}
    assert any(n.outcome == "pruned_integer" and n.z == Fraction(20) for n in result.nodes)
    assert all(n.outcome in leaf_outcomes | {"branched"} for n in result.nodes)


def test_root_relaxation_already_integer_needs_no_branching():
    problem = with_kinds(
        make_problem("max", [3, 5], [([1, 0], "<=", 4), ([0, 2], "<=", 12), ([3, 2], "<=", 18)]),
        [VarKind.INTEGER, VarKind.INTEGER],
    )
    result = compute_branch_and_bound(problem)

    assert result.status == "optimal"
    assert result.solution == {"x1": Fraction(2), "x2": Fraction(6)}
    assert result.z == Fraction(36)
    assert len(result.nodes) == 1
    assert result.nodes[0].outcome == "pruned_integer"


def test_binary_variables_are_bounded_between_zero_and_one():
    # Max Z = 8x1 + 5x2 s.t. x1+x2<=1.5 (forces at most one to be 1), x binary.
    problem = with_kinds(
        make_problem("max", [8, 5], [([1, 1], "<=", Fraction(3, 2))]),
        [VarKind.BINARY, VarKind.BINARY],
    )
    result = compute_branch_and_bound(problem)

    assert result.status == "optimal"
    assert result.solution["x1"] == Fraction(1)
    assert result.solution["x2"] == Fraction(0)
    assert result.z == Fraction(8)
    for node in result.nodes:
        if node.solution is not None:
            assert 0 <= node.solution["x1"] <= 1
            assert 0 <= node.solution["x2"] <= 1


def test_no_integer_solution_exists():
    # x1 + x2 = 1/2 with x1, x2 integer >= 0 has no integer solution: their sum is always
    # an integer.
    problem = with_kinds(
        make_problem("max", [1, 0], [([1, 1], "=", Fraction(1, 2))]),
        [VarKind.INTEGER, VarKind.INTEGER],
    )
    result = compute_branch_and_bound(problem)

    assert result.status == "infeasible"
    assert result.solution is None
    assert result.z is None


def test_returns_none_when_no_variable_requires_integrality():
    problem = make_problem(
        "max", [3, 5], [([1, 0], "<=", 4), ([0, 2], "<=", 12), ([3, 2], "<=", 18)]
    )
    assert has_integer_requirements(problem) is False
    assert compute_branch_and_bound(problem) is None


def test_mixed_integer_and_continuous_variables():
    # Only x1 is required to be integer; x2 stays continuous.
    problem = with_kinds(
        make_problem("max", [5, 4], [([6, 4], "<=", 24), ([1, 2], "<=", 6)]),
        [VarKind.INTEGER, VarKind.CONTINUOUS],
    )
    result = compute_branch_and_bound(problem)

    assert result.status == "optimal"
    assert result.solution["x1"].denominator == 1

    scipy_z = scipy_milp_optimum(problem, integrality=[1, 0])
    assert float(result.z) == pytest.approx(scipy_z, abs=1e-6)
