from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.branch_and_bound import compute_branch_and_bound
from app.core.duality import compute_duality
from app.core.graphical import compute_graphical_data
from app.core.sensitivity import compute_sensitivity
from app.core.simplex.solve import solve_simplex
from app.core.standard_form import build_standard_form
from app.core.validation import ValidationError, parse_problem
from app.examples import EXAMPLES
from app.schemas.request import SolveRequest
from app.schemas.response import (
    BranchAndBoundOut,
    DualOut,
    FractionOut,
    GraphicalDataOut,
    SensitivityOut,
    SolveResponse,
    StandardFormOut,
    TableauIterationOut,
)

router = APIRouter(prefix="/api")


@router.get("/examples")
def get_examples() -> list[dict]:
    return EXAMPLES


@router.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest) -> SolveResponse:
    try:
        problem = parse_problem(request)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc

    standard_form = build_standard_form(problem)
    result = solve_simplex(problem, method=request.method)
    graphical_data = compute_graphical_data(problem, result)
    sensitivity_data = compute_sensitivity(problem)
    dual_data = compute_duality(problem)
    branch_and_bound_data = compute_branch_and_bound(problem)

    return SolveResponse(
        status=result.status,
        method=result.method,
        message=result.message,
        standard_form=StandardFormOut.from_domain(standard_form),
        iterations=[TableauIterationOut.from_domain(it) for it in result.iterations],
        solution=(
            {name: FractionOut.from_fraction(v) for name, v in result.solution.items()}
            if result.solution is not None
            else None
        ),
        z=FractionOut.from_fraction(result.z) if result.z is not None else None,
        has_alternate_optima=result.has_alternate_optima,
        is_degenerate=result.is_degenerate,
        graphical=(
            GraphicalDataOut.from_domain(graphical_data) if graphical_data is not None else None
        ),
        sensitivity=(
            SensitivityOut.from_domain(sensitivity_data) if sensitivity_data is not None else None
        ),
        dual=DualOut.from_domain(dual_data) if dual_data is not None else None,
        branch_and_bound=(
            BranchAndBoundOut.from_domain(branch_and_bound_data)
            if branch_and_bound_data is not None
            else None
        ),
    )
