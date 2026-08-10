from __future__ import annotations

from app.core.fraction_utils import to_fraction
from app.core.models import Constraint, LPProblem, Variable
from app.schemas.request import SolveRequest


class ValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def parse_problem(request: SolveRequest) -> LPProblem:
    try:
        objective = [to_fraction(v) for v in request.objective]
    except (ValueError, ZeroDivisionError) as exc:
        raise ValidationError(
            f"La función objetivo contiene un coeficiente numérico inválido: {exc}"
        ) from exc

    variables = [Variable(name=v.name, sign=v.sign, kind=v.kind) for v in request.variables]

    constraints: list[Constraint] = []
    for idx, c in enumerate(request.constraints, start=1):
        try:
            coeffs = [to_fraction(v) for v in c.coeffs]
            rhs = to_fraction(c.rhs)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValidationError(
                f"La restricción #{idx} contiene un valor numérico inválido: {exc}"
            ) from exc
        constraints.append(Constraint(coeffs=coeffs, op=c.op, rhs=rhs, name=c.name))

    return LPProblem(
        sense=request.sense, objective=objective, variables=variables, constraints=constraints
    )
