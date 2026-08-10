from fractions import Fraction

from app.core.duality import compute_duality
from app.core.models import Sense
from tests.helpers import make_problem


def test_dual_of_max_problem_wyndor_glass():
    # Hand-verified: dual is Min W = 4y1+12y2+18y3 s.t. y1+3y3>=3, 2y2+2y3>=5, y>=0.
    # Optimal dual: y1=0, y2=3/2, y3=1, W=36 (matches primal Z=36).
    problem = make_problem(
        "max",
        [3, 5],
        [
            ([1, 0], "<=", 4),
            ([0, 2], "<=", 12),
            ([3, 2], "<=", 18),
        ],
    )
    dual = compute_duality(problem)

    assert dual is not None
    assert dual.dual_sense == Sense.MIN
    assert [v.sign for v in dual.dual_variables] == ["nonnegative", "nonnegative", "nonnegative"]
    assert dual.dual_objective_coeffs == [Fraction(4), Fraction(12), Fraction(18)]

    # Dual constraint for x1: y1 + 3*y3 >= 3
    x1_constraint = dual.dual_constraints[0]
    assert x1_constraint.coeffs == [Fraction(1), Fraction(0), Fraction(3)]
    assert x1_constraint.op == ">="
    assert x1_constraint.rhs == Fraction(3)

    # Dual constraint for x2: 2*y2 + 2*y3 >= 5
    x2_constraint = dual.dual_constraints[1]
    assert x2_constraint.coeffs == [Fraction(0), Fraction(2), Fraction(2)]
    assert x2_constraint.rhs == Fraction(5)

    values = [v.value for v in dual.dual_variables]
    assert values == [Fraction(0), Fraction(3, 2), Fraction(1)]

    assert dual.primal_z == Fraction(36)
    assert dual.dual_z == Fraction(36)
    assert dual.strong_duality_holds is True

    # Complementary slackness: constraint 1 has slack (x1=2<4) so y1 must be 0 (it is).
    # Both dual constraints are binding, matching x1>0 and x2>0.
    assert all(item.holds for item in dual.complementary_slackness)


def test_dual_of_min_problem_with_ge_constraints():
    # Min Z=2x1+3x2 s.t. x1+x2>=4, x1+2x2>=6 -> dual: Max W=4y1+6y2 s.t. y1+y2<=2, y1+2y2<=3, y>=0.
    # Optimal dual: y1=1, y2=1, W=10 (matches primal Z=10).
    problem = make_problem("min", [2, 3], [([1, 1], ">=", 4), ([1, 2], ">=", 6)])
    dual = compute_duality(problem)

    assert dual is not None
    assert dual.dual_sense == Sense.MAX
    assert [v.sign for v in dual.dual_variables] == ["nonnegative", "nonnegative"]
    assert dual.dual_objective_coeffs == [Fraction(4), Fraction(6)]

    x1_constraint = dual.dual_constraints[0]
    assert x1_constraint.coeffs == [Fraction(1), Fraction(1)]
    assert x1_constraint.op == "<="
    assert x1_constraint.rhs == Fraction(2)

    values = [v.value for v in dual.dual_variables]
    assert values == [Fraction(1), Fraction(1)]
    assert dual.primal_z == Fraction(10)
    assert dual.dual_z == Fraction(10)
    assert dual.strong_duality_holds is True
    assert all(item.holds for item in dual.complementary_slackness)


def test_dual_equality_constraint_gives_free_dual_variable():
    problem = make_problem(
        "min",
        [4, 1],
        [
            ([3, 1], "=", 3),
            ([4, 3], ">=", 6),
            ([1, 2], "<=", 4),
        ],
    )
    dual = compute_duality(problem)

    assert dual is not None
    signs = [v.sign for v in dual.dual_variables]
    assert signs == ["free", "nonnegative", "nonpositive"]
    assert dual.primal_z == Fraction(17, 5)
    assert dual.dual_z == Fraction(17, 5)
    assert dual.strong_duality_holds is True


def test_dual_returns_none_when_primal_not_optimal():
    unbounded = make_problem("max", [1, 1], [([1, -1], "<=", 1)])
    assert compute_duality(unbounded) is None

    infeasible = make_problem("max", [1, 1], [([1, 1], "<=", 2), ([1, 1], ">=", 6)])
    assert compute_duality(infeasible) is None
