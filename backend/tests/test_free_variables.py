from fractions import Fraction

import pytest

from app.core.models import Method, SolveStatus, VarSign
from app.core.simplex.solve import solve_simplex
from tests.helpers import check_constraints_satisfied, make_problem


@pytest.mark.parametrize("method", [Method.TWO_PHASE, Method.BIG_M])
def test_free_variable_can_be_negative_at_optimum(method):
    # x2 is unrestricted in sign. Max Z = x1 + x2 s.t. x1<=1, x2<=-2.
    # Forces the optimal x2 to be negative (-2), exercising the split x2 = x2_pos - x2_neg
    # and the negative-RHS row flip (x2<=-2 -> -x2>=2) at the same time.
    problem = make_problem(
        "max",
        [1, 1],
        [
            ([1, 0], "<=", 1),
            ([0, 1], "<=", -2),
        ],
        var_signs=[VarSign.NONNEGATIVE, VarSign.FREE],
    )
    result = solve_simplex(problem, method=method)

    assert result.status == SolveStatus.OPTIMAL
    assert result.solution["x1"] == Fraction(1)
    assert result.solution["x2"] == Fraction(-2)
    assert result.z == Fraction(-1)
    assert check_constraints_satisfied(problem, result.solution)
