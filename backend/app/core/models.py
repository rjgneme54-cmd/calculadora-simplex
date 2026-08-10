from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction


class Sense(StrEnum):
    MAX = "max"
    MIN = "min"


class ConstraintOp(StrEnum):
    LE = "<="
    GE = ">="
    EQ = "="


class VarSign(StrEnum):
    NONNEGATIVE = "nonnegative"
    FREE = "free"


class VarKind(StrEnum):
    CONTINUOUS = "continuous"
    INTEGER = "integer"
    BINARY = "binary"


class SolveStatus(StrEnum):
    OPTIMAL = "optimal"
    UNBOUNDED = "unbounded"
    INFEASIBLE = "infeasible"


class Method(StrEnum):
    TWO_PHASE = "two_phase"
    BIG_M = "big_m"


@dataclass
class Variable:
    name: str
    sign: VarSign = VarSign.NONNEGATIVE
    kind: VarKind = VarKind.CONTINUOUS


@dataclass
class Constraint:
    coeffs: list[Fraction]
    op: ConstraintOp
    rhs: Fraction
    name: str | None = None


@dataclass
class LPProblem:
    sense: Sense
    objective: list[Fraction]
    variables: list[Variable]
    constraints: list[Constraint]
    objective_constant: Fraction = field(default_factory=lambda: Fraction(0))

    @property
    def n(self) -> int:
        return len(self.variables)

    @property
    def m(self) -> int:
        return len(self.constraints)


@dataclass
class RatioTestRow:
    row: int
    basic_var: str
    rhs: object
    coeff: object
    ratio: Fraction | None
    eligible: bool


@dataclass
class TableauIteration:
    iteration: int
    phase: int
    basis: list[str]
    var_names: list[str]
    matrix: list[list[object]]
    rhs: list[object]
    z_row: list[object]
    z_value: object
    entering: str | None
    leaving: str | None
    pivot_row: int | None
    pivot_col: int | None
    pivot_element: object | None
    ratio_test: list[RatioTestRow]
    explanation: str
    is_optimal: bool
    is_degenerate_step: bool = False


@dataclass
class SimplexResult:
    status: SolveStatus
    method: Method
    iterations: list[TableauIteration]
    solution: dict[str, Fraction] | None
    z: Fraction | None
    has_alternate_optima: bool
    is_degenerate: bool
    message: str
