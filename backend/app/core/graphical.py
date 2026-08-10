from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from app.core.models import ConstraintOp, LPProblem, Sense, SimplexResult, SolveStatus, VarSign


@dataclass
class PlotPoint:
    x: float
    y: float


@dataclass
class LineSegment:
    label: str
    point1: PlotPoint
    point2: PlotPoint


@dataclass
class Vertex:
    label: str
    x: Fraction
    y: Fraction
    z: Fraction


@dataclass
class GraphicalData:
    var_names: tuple[str, str]
    lines: list[LineSegment]
    feasible_vertices: list[Vertex]
    optimal_vertices: list[Vertex]
    objective_coeffs: tuple[Fraction, Fraction]
    plot_bounds: tuple[float, float, float, float]
    is_unbounded_region: bool


_BoundaryLine = tuple[Fraction, Fraction, Fraction, str]


def _satisfies_all(problem: LPProblem, x: Fraction, y: Fraction) -> bool:
    for constraint in problem.constraints:
        lhs = constraint.coeffs[0] * x + constraint.coeffs[1] * y
        if constraint.op == ConstraintOp.LE and lhs > constraint.rhs:
            return False
        if constraint.op == ConstraintOp.GE and lhs < constraint.rhs:
            return False
        if constraint.op == ConstraintOp.EQ and lhs != constraint.rhs:
            return False
    if problem.variables[0].sign == VarSign.NONNEGATIVE and x < 0:
        return False
    if problem.variables[1].sign == VarSign.NONNEGATIVE and y < 0:
        return False
    return True


def _boundary_lines(problem: LPProblem) -> list[_BoundaryLine]:
    lines: list[_BoundaryLine] = []
    for idx, constraint in enumerate(problem.constraints):
        name = constraint.name or f"R{idx + 1}"
        lines.append((constraint.coeffs[0], constraint.coeffs[1], constraint.rhs, name))
    if problem.variables[0].sign == VarSign.NONNEGATIVE:
        lines.append((Fraction(1), Fraction(0), Fraction(0), f"{problem.variables[0].name}=0"))
    if problem.variables[1].sign == VarSign.NONNEGATIVE:
        lines.append((Fraction(0), Fraction(1), Fraction(0), f"{problem.variables[1].name}=0"))
    return lines


def _intersect(l1: _BoundaryLine, l2: _BoundaryLine) -> tuple[Fraction, Fraction] | None:
    a1, b1, r1, _ = l1
    a2, b2, r2, _ = l2
    det = a1 * b2 - a2 * b1
    if det == 0:
        return None
    x = (r1 * b2 - r2 * b1) / det
    y = (a1 * r2 - a2 * r1) / det
    return x, y


def _label_for(index: int) -> str:
    if index < 26:
        return chr(ord("A") + index)
    return f"V{index + 1}"


def _order_polygon(points: list[tuple[Fraction, Fraction]]) -> list[tuple[Fraction, Fraction]]:
    if len(points) <= 2:
        return points
    cx = sum((p[0] for p in points), Fraction(0)) / len(points)
    cy = sum((p[1] for p in points), Fraction(0)) / len(points)
    return sorted(points, key=lambda p: math.atan2(float(p[1] - cy), float(p[0] - cx)))


def _compute_bounds(
    problem: LPProblem,
    feasible_points: list[tuple[Fraction, Fraction]],
    boundary_lines: list[_BoundaryLine],
) -> tuple[float, float, float, float]:
    xs = [abs(float(p[0])) for p in feasible_points]
    ys = [abs(float(p[1])) for p in feasible_points]
    if not xs and not ys:
        for a, b, r, _name in boundary_lines:
            if a != 0:
                xs.append(abs(float(r) / float(a)))
            if b != 0:
                ys.append(abs(float(r) / float(b)))

    max_x = max([*xs, 1.0])
    max_y = max([*ys, 1.0])
    nonneg_x = problem.variables[0].sign == VarSign.NONNEGATIVE
    nonneg_y = problem.variables[1].sign == VarSign.NONNEGATIVE
    xmin = 0.0 if nonneg_x else -max_x * 1.2
    ymin = 0.0 if nonneg_y else -max_y * 1.2
    return (xmin - max_x * 0.05, max_x * 1.2, ymin - max_y * 0.05, max_y * 1.2)


def _clip_line(line: _BoundaryLine, bounds: tuple[float, float, float, float]) -> LineSegment:
    a, b, r, name = line
    xmin, xmax, ymin, ymax = bounds
    af, bf, rf = float(a), float(b), float(r)
    if bf != 0:
        p1 = PlotPoint(xmin, (rf - af * xmin) / bf)
        p2 = PlotPoint(xmax, (rf - af * xmax) / bf)
    else:
        x = rf / af
        p1 = PlotPoint(x, ymin)
        p2 = PlotPoint(x, ymax)
    return LineSegment(label=name, point1=p1, point2=p2)


def compute_graphical_data(problem: LPProblem, result: SimplexResult) -> GraphicalData | None:
    if problem.n != 2:
        return None

    var_names = (problem.variables[0].name, problem.variables[1].name)
    boundary_lines = _boundary_lines(problem)
    constraint_lines = boundary_lines[: len(problem.constraints)]

    candidates: list[tuple[Fraction, Fraction]] = []
    for i in range(len(boundary_lines)):
        for j in range(i + 1, len(boundary_lines)):
            point = _intersect(boundary_lines[i], boundary_lines[j])
            if point is not None:
                candidates.append(point)

    seen: set[tuple[Fraction, Fraction]] = set()
    feasible_points: list[tuple[Fraction, Fraction]] = []
    for point in candidates:
        if point in seen:
            continue
        seen.add(point)
        if _satisfies_all(problem, point[0], point[1]):
            feasible_points.append(point)

    ordered_points = _order_polygon(feasible_points)

    c1, c2 = problem.objective[0], problem.objective[1]
    vertices = [
        Vertex(label=_label_for(i), x=p[0], y=p[1], z=c1 * p[0] + c2 * p[1])
        for i, p in enumerate(ordered_points)
    ]

    optimal_vertices: list[Vertex] = []
    if result.status == SolveStatus.OPTIMAL and vertices:
        best_z = (
            max(v.z for v in vertices) if problem.sense == Sense.MAX else min(v.z for v in vertices)
        )
        optimal_vertices = [v for v in vertices if v.z == best_z]

    bounds = _compute_bounds(problem, feasible_points, boundary_lines)
    lines = [_clip_line(line, bounds) for line in constraint_lines]

    return GraphicalData(
        var_names=var_names,
        lines=lines,
        feasible_vertices=vertices,
        optimal_vertices=optimal_vertices,
        objective_coeffs=(c1, c2),
        plot_bounds=bounds,
        is_unbounded_region=result.status == SolveStatus.UNBOUNDED,
    )
