from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.core.models import ConstraintOp, Method, Sense, VarKind, VarSign

Number = float | int | str


class VariableIn(BaseModel):
    name: str | None = None
    sign: VarSign = VarSign.NONNEGATIVE
    kind: VarKind = VarKind.CONTINUOUS


class ConstraintIn(BaseModel):
    coeffs: list[Number]
    op: ConstraintOp
    rhs: Number
    name: str | None = None


class SolveRequest(BaseModel):
    sense: Sense
    objective: list[Number] = Field(min_length=1)
    variables: list[VariableIn] = Field(default_factory=list)
    constraints: list[ConstraintIn] = Field(min_length=1)
    method: Method = Method.TWO_PHASE

    @model_validator(mode="after")
    def _check_dimensions_and_fill_defaults(self) -> SolveRequest:
        n = len(self.objective)

        if not self.variables:
            self.variables = [VariableIn(name=f"x{i + 1}") for i in range(n)]
        else:
            if len(self.variables) != n:
                raise ValueError(
                    f"El número de variables ({len(self.variables)}) no coincide con el número "
                    f"de coeficientes de la función objetivo ({n})."
                )
            for i, v in enumerate(self.variables):
                if not v.name:
                    v.name = f"x{i + 1}"

        names = [v.name for v in self.variables]
        if len(set(names)) != len(names):
            raise ValueError("Los nombres de las variables deben ser únicos.")

        for idx, constraint in enumerate(self.constraints, start=1):
            if len(constraint.coeffs) != n:
                raise ValueError(
                    f"La restricción #{idx} tiene {len(constraint.coeffs)} coeficientes, pero "
                    f"el problema tiene {n} variables."
                )

        return self
