from __future__ import annotations

from fractions import Fraction

from pydantic import BaseModel

from app.core.branch_and_bound import BranchAndBoundResult, BranchBoundNode
from app.core.duality import ComplementarySlacknessItem, DualConstraint, DualData, DualVariable
from app.core.graphical import GraphicalData, LineSegment, PlotPoint, Vertex
from app.core.models import Method, RatioTestRow, SolveStatus, TableauIteration
from app.core.sensitivity import ObjectiveCoeffRange, RhsRangeItem, SensitivityData
from app.core.simplex.big_m_number import BigMNumber
from app.core.standard_form import StandardForm


class FractionOut(BaseModel):
    num: int
    den: int
    decimal: float

    @classmethod
    def from_fraction(cls, value: Fraction) -> FractionOut:
        return cls(num=value.numerator, den=value.denominator, decimal=float(value))


class CellValueOut(BaseModel):
    num: int
    den: int
    decimal: float
    m_num: int = 0
    m_den: int = 1

    @classmethod
    def from_value(cls, value: object) -> CellValueOut:
        if isinstance(value, BigMNumber):
            const, m = value.const, value.m_coeff
            return cls(
                num=const.numerator,
                den=const.denominator,
                decimal=float(const),
                m_num=m.numerator,
                m_den=m.denominator,
            )
        f = value if isinstance(value, Fraction) else Fraction(value)
        return cls(num=f.numerator, den=f.denominator, decimal=float(f))


class RatioTestRowOut(BaseModel):
    row: int
    basic_var: str
    rhs: CellValueOut
    coeff: CellValueOut
    ratio: FractionOut | None
    eligible: bool

    @classmethod
    def from_domain(cls, row: RatioTestRow) -> RatioTestRowOut:
        return cls(
            row=row.row,
            basic_var=row.basic_var,
            rhs=CellValueOut.from_value(row.rhs),
            coeff=CellValueOut.from_value(row.coeff),
            ratio=FractionOut.from_fraction(row.ratio) if row.ratio is not None else None,
            eligible=row.eligible,
        )


class TableauIterationOut(BaseModel):
    iteration: int
    phase: int
    basis: list[str]
    var_names: list[str]
    matrix: list[list[CellValueOut]]
    rhs: list[CellValueOut]
    z_row: list[CellValueOut]
    z_value: CellValueOut
    entering: str | None
    leaving: str | None
    pivot_row: int | None
    pivot_col: int | None
    pivot_element: CellValueOut | None
    ratio_test: list[RatioTestRowOut]
    explanation: str
    is_optimal: bool
    is_degenerate_step: bool

    @classmethod
    def from_domain(cls, it: TableauIteration) -> TableauIterationOut:
        return cls(
            iteration=it.iteration,
            phase=it.phase,
            basis=it.basis,
            var_names=it.var_names,
            matrix=[[CellValueOut.from_value(v) for v in row] for row in it.matrix],
            rhs=[CellValueOut.from_value(v) for v in it.rhs],
            z_row=[CellValueOut.from_value(v) for v in it.z_row],
            z_value=CellValueOut.from_value(it.z_value),
            entering=it.entering,
            leaving=it.leaving,
            pivot_row=it.pivot_row,
            pivot_col=it.pivot_col,
            pivot_element=(
                CellValueOut.from_value(it.pivot_element) if it.pivot_element is not None else None
            ),
            ratio_test=[RatioTestRowOut.from_domain(r) for r in it.ratio_test],
            explanation=it.explanation,
            is_optimal=it.is_optimal,
            is_degenerate_step=it.is_degenerate_step,
        )


class StandardFormOut(BaseModel):
    var_names: list[str]
    column_kinds: list[str]
    objective_coeffs: list[FractionOut]
    constraint_rows: list[list[FractionOut]]
    rhs: list[FractionOut]
    artificial_var_names: list[str]

    @classmethod
    def from_domain(cls, sf: StandardForm) -> StandardFormOut:
        return cls(
            var_names=sf.var_names,
            column_kinds=[c.kind for c in sf.columns],
            objective_coeffs=[FractionOut.from_fraction(v) for v in sf.c],
            constraint_rows=[[FractionOut.from_fraction(v) for v in row] for row in sf.a],
            rhs=[FractionOut.from_fraction(v) for v in sf.b],
            artificial_var_names=[sf.columns[i].name for i in sf.artificial_cols],
        )


class PlotPointOut(BaseModel):
    x: float
    y: float

    @classmethod
    def from_domain(cls, p: PlotPoint) -> PlotPointOut:
        return cls(x=p.x, y=p.y)


class LineSegmentOut(BaseModel):
    label: str
    point1: PlotPointOut
    point2: PlotPointOut

    @classmethod
    def from_domain(cls, line: LineSegment) -> LineSegmentOut:
        return cls(
            label=line.label,
            point1=PlotPointOut.from_domain(line.point1),
            point2=PlotPointOut.from_domain(line.point2),
        )


class VertexOut(BaseModel):
    label: str
    x: FractionOut
    y: FractionOut
    z: FractionOut

    @classmethod
    def from_domain(cls, vertex: Vertex) -> VertexOut:
        return cls(
            label=vertex.label,
            x=FractionOut.from_fraction(vertex.x),
            y=FractionOut.from_fraction(vertex.y),
            z=FractionOut.from_fraction(vertex.z),
        )


class PlotBoundsOut(BaseModel):
    xmin: float
    xmax: float
    ymin: float
    ymax: float


class GraphicalDataOut(BaseModel):
    var_names: tuple[str, str]
    lines: list[LineSegmentOut]
    feasible_vertices: list[VertexOut]
    optimal_vertices: list[VertexOut]
    objective_coeffs: tuple[FractionOut, FractionOut]
    plot_bounds: PlotBoundsOut
    is_unbounded_region: bool

    @classmethod
    def from_domain(cls, data: GraphicalData) -> GraphicalDataOut:
        xmin, xmax, ymin, ymax = data.plot_bounds
        c1, c2 = data.objective_coeffs
        return cls(
            var_names=data.var_names,
            lines=[LineSegmentOut.from_domain(line) for line in data.lines],
            feasible_vertices=[VertexOut.from_domain(v) for v in data.feasible_vertices],
            optimal_vertices=[VertexOut.from_domain(v) for v in data.optimal_vertices],
            objective_coeffs=(FractionOut.from_fraction(c1), FractionOut.from_fraction(c2)),
            plot_bounds=PlotBoundsOut(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax),
            is_unbounded_region=data.is_unbounded_region,
        )


class ObjectiveCoeffRangeOut(BaseModel):
    variable_name: str
    current_value: FractionOut
    lower: FractionOut | None
    upper: FractionOut | None
    applicable: bool

    @classmethod
    def from_domain(cls, r: ObjectiveCoeffRange) -> ObjectiveCoeffRangeOut:
        return cls(
            variable_name=r.variable_name,
            current_value=FractionOut.from_fraction(r.current_value),
            lower=FractionOut.from_fraction(r.lower) if r.lower is not None else None,
            upper=FractionOut.from_fraction(r.upper) if r.upper is not None else None,
            applicable=r.applicable,
        )


class RhsRangeItemOut(BaseModel):
    constraint_name: str
    current_value: FractionOut
    lower: FractionOut | None
    upper: FractionOut | None
    shadow_price: FractionOut

    @classmethod
    def from_domain(cls, r: RhsRangeItem) -> RhsRangeItemOut:
        return cls(
            constraint_name=r.constraint_name,
            current_value=FractionOut.from_fraction(r.current_value),
            lower=FractionOut.from_fraction(r.lower) if r.lower is not None else None,
            upper=FractionOut.from_fraction(r.upper) if r.upper is not None else None,
            shadow_price=FractionOut.from_fraction(r.shadow_price),
        )


class SensitivityOut(BaseModel):
    objective_ranges: list[ObjectiveCoeffRangeOut]
    rhs_ranges: list[RhsRangeItemOut]

    @classmethod
    def from_domain(cls, data: SensitivityData) -> SensitivityOut:
        return cls(
            objective_ranges=[ObjectiveCoeffRangeOut.from_domain(r) for r in data.objective_ranges],
            rhs_ranges=[RhsRangeItemOut.from_domain(r) for r in data.rhs_ranges],
        )


class DualVariableOut(BaseModel):
    name: str
    primal_constraint_name: str
    sign: str
    value: FractionOut

    @classmethod
    def from_domain(cls, v: DualVariable) -> DualVariableOut:
        return cls(
            name=v.name,
            primal_constraint_name=v.primal_constraint_name,
            sign=v.sign,
            value=FractionOut.from_fraction(v.value),
        )


class DualConstraintOut(BaseModel):
    primal_variable_name: str
    coeffs: list[FractionOut]
    op: str
    rhs: FractionOut

    @classmethod
    def from_domain(cls, c: DualConstraint) -> DualConstraintOut:
        return cls(
            primal_variable_name=c.primal_variable_name,
            coeffs=[FractionOut.from_fraction(v) for v in c.coeffs],
            op=c.op,
            rhs=FractionOut.from_fraction(c.rhs),
        )


class ComplementarySlacknessItemOut(BaseModel):
    description: str
    holds: bool

    @classmethod
    def from_domain(cls, item: ComplementarySlacknessItem) -> ComplementarySlacknessItemOut:
        return cls(description=item.description, holds=item.holds)


class DualOut(BaseModel):
    dual_sense: str
    dual_variables: list[DualVariableOut]
    dual_constraints: list[DualConstraintOut]
    dual_objective_coeffs: list[FractionOut]
    primal_z: FractionOut
    dual_z: FractionOut
    strong_duality_holds: bool
    complementary_slackness: list[ComplementarySlacknessItemOut]

    @classmethod
    def from_domain(cls, data: DualData) -> DualOut:
        return cls(
            dual_sense=data.dual_sense,
            dual_variables=[DualVariableOut.from_domain(v) for v in data.dual_variables],
            dual_constraints=[DualConstraintOut.from_domain(c) for c in data.dual_constraints],
            dual_objective_coeffs=[
                FractionOut.from_fraction(v) for v in data.dual_objective_coeffs
            ],
            primal_z=FractionOut.from_fraction(data.primal_z),
            dual_z=FractionOut.from_fraction(data.dual_z),
            strong_duality_holds=data.strong_duality_holds,
            complementary_slackness=[
                ComplementarySlacknessItemOut.from_domain(item)
                for item in data.complementary_slackness
            ],
        )


class BranchBoundNodeOut(BaseModel):
    id: int
    parent_id: int | None
    depth: int
    branch_description: str | None
    status: str
    solution: dict[str, FractionOut] | None
    z: FractionOut | None
    is_integer_feasible: bool
    outcome: str
    branched_variable: str | None

    @classmethod
    def from_domain(cls, node: BranchBoundNode) -> BranchBoundNodeOut:
        return cls(
            id=node.id,
            parent_id=node.parent_id,
            depth=node.depth,
            branch_description=node.branch_description,
            status=node.status,
            solution=(
                {name: FractionOut.from_fraction(v) for name, v in node.solution.items()}
                if node.solution is not None
                else None
            ),
            z=FractionOut.from_fraction(node.z) if node.z is not None else None,
            is_integer_feasible=node.is_integer_feasible,
            outcome=node.outcome,
            branched_variable=node.branched_variable,
        )


class BranchAndBoundOut(BaseModel):
    status: str
    solution: dict[str, FractionOut] | None
    z: FractionOut | None
    nodes: list[BranchBoundNodeOut]
    message: str

    @classmethod
    def from_domain(cls, data: BranchAndBoundResult) -> BranchAndBoundOut:
        return cls(
            status=data.status,
            solution=(
                {name: FractionOut.from_fraction(v) for name, v in data.solution.items()}
                if data.solution is not None
                else None
            ),
            z=FractionOut.from_fraction(data.z) if data.z is not None else None,
            nodes=[BranchBoundNodeOut.from_domain(n) for n in data.nodes],
            message=data.message,
        )


class SolveResponse(BaseModel):
    status: SolveStatus
    method: Method
    message: str
    standard_form: StandardFormOut
    iterations: list[TableauIterationOut]
    solution: dict[str, FractionOut] | None
    z: FractionOut | None
    has_alternate_optima: bool
    is_degenerate: bool
    graphical: GraphicalDataOut | None = None
    sensitivity: SensitivityOut | None = None
    dual: DualOut | None = None
    branch_and_bound: BranchAndBoundOut | None = None
