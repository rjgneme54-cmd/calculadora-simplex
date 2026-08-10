from __future__ import annotations

from app.core.models import LPProblem, Method, SimplexResult
from app.core.simplex.big_m import solve_big_m
from app.core.simplex.two_phase import solve_two_phase


def solve_simplex(problem: LPProblem, method: Method = Method.TWO_PHASE) -> SimplexResult:
    if method == Method.BIG_M:
        return solve_big_m(problem)
    return solve_two_phase(problem)
