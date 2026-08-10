from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from app.core.models import Constraint, ConstraintOp, LPProblem, Sense, SolveStatus, VarKind
from app.core.simplex.two_phase import solve_two_phase

MAX_NODES = 500


@dataclass
class BranchBoundNode:
    id: int
    parent_id: int | None
    depth: int
    branch_description: str | None
    status: str
    solution: dict[str, Fraction] | None
    z: Fraction | None
    is_integer_feasible: bool
    outcome: str
    branched_variable: str | None = None


@dataclass
class BranchAndBoundResult:
    status: str
    solution: dict[str, Fraction] | None
    z: Fraction | None
    nodes: list[BranchBoundNode]
    message: str


def has_integer_requirements(problem: LPProblem) -> bool:
    return any(v.kind in (VarKind.INTEGER, VarKind.BINARY) for v in problem.variables)


def _unit_row(n: int, idx: int) -> list[Fraction]:
    return [Fraction(1) if i == idx else Fraction(0) for i in range(n)]


def _binary_bound_constraints(problem: LPProblem) -> list[Constraint]:
    extra = []
    for idx, var in enumerate(problem.variables):
        if var.kind == VarKind.BINARY:
            extra.append(
                Constraint(
                    coeffs=_unit_row(problem.n, idx),
                    op=ConstraintOp.LE,
                    rhs=Fraction(1),
                    name=f"{var.name}<=1 (binaria)",
                )
            )
    return extra


def _integer_var_indices(problem: LPProblem) -> list[int]:
    return [
        i for i, v in enumerate(problem.variables) if v.kind in (VarKind.INTEGER, VarKind.BINARY)
    ]


def _most_fractional(
    solution: dict[str, Fraction], problem: LPProblem, integer_idx: list[int]
) -> tuple[int, Fraction] | None:
    best: tuple[int, Fraction, Fraction] | None = None
    for i in integer_idx:
        value = solution[problem.variables[i].name]
        if value.denominator == 1:
            continue
        frac_part = value - math.floor(value)
        distance = abs(frac_part - Fraction(1, 2))
        if best is None or distance < best[2]:
            best = (i, value, distance)
    return None if best is None else (best[0], best[1])


def compute_branch_and_bound(problem: LPProblem) -> BranchAndBoundResult | None:
    if not has_integer_requirements(problem):
        return None

    integer_idx = _integer_var_indices(problem)
    base_extra = _binary_bound_constraints(problem)
    is_max = problem.sense == Sense.MAX

    nodes: list[BranchBoundNode] = []
    incumbent_solution: dict[str, Fraction] | None = None
    incumbent_z: Fraction | None = None

    def is_better(z: Fraction) -> bool:
        return incumbent_z is None or (z > incumbent_z if is_max else z < incumbent_z)

    node_id_counter = 0
    stack: list[tuple[int | None, int, str | None, list[Constraint]]] = [
        (None, 0, None, list(base_extra))
    ]

    while stack and node_id_counter < MAX_NODES:
        parent_id, depth, branch_description, extra_constraints = stack.pop()
        node_id = node_id_counter
        node_id_counter += 1

        sub_problem = LPProblem(
            sense=problem.sense,
            objective=problem.objective,
            variables=problem.variables,
            constraints=problem.constraints + extra_constraints,
        )
        result = solve_two_phase(sub_problem)

        if result.status != SolveStatus.OPTIMAL:
            nodes.append(
                BranchBoundNode(
                    id=node_id,
                    parent_id=parent_id,
                    depth=depth,
                    branch_description=branch_description,
                    status=result.status.value,
                    solution=None,
                    z=None,
                    is_integer_feasible=False,
                    outcome="pruned_infeasible",
                )
            )
            continue

        z = result.z
        solution = result.solution

        if incumbent_z is not None and not is_better(z):
            nodes.append(
                BranchBoundNode(
                    id=node_id,
                    parent_id=parent_id,
                    depth=depth,
                    branch_description=branch_description,
                    status="optimal",
                    solution=solution,
                    z=z,
                    is_integer_feasible=False,
                    outcome="pruned_bound",
                )
            )
            continue

        frac_choice = _most_fractional(solution, problem, integer_idx)

        if frac_choice is None:
            if is_better(z):
                incumbent_solution = solution
                incumbent_z = z
            nodes.append(
                BranchBoundNode(
                    id=node_id,
                    parent_id=parent_id,
                    depth=depth,
                    branch_description=branch_description,
                    status="optimal",
                    solution=solution,
                    z=z,
                    is_integer_feasible=True,
                    outcome="pruned_integer",
                )
            )
            continue

        var_idx, value = frac_choice
        var_name = problem.variables[var_idx].name
        floor_val = math.floor(value)
        ceil_val = floor_val + 1

        nodes.append(
            BranchBoundNode(
                id=node_id,
                parent_id=parent_id,
                depth=depth,
                branch_description=branch_description,
                status="optimal",
                solution=solution,
                z=z,
                is_integer_feasible=False,
                outcome="branched",
                branched_variable=var_name,
            )
        )

        floor_constraint = Constraint(
            coeffs=_unit_row(problem.n, var_idx),
            op=ConstraintOp.LE,
            rhs=Fraction(floor_val),
            name=f"{var_name}<={floor_val}",
        )
        ceil_constraint = Constraint(
            coeffs=_unit_row(problem.n, var_idx),
            op=ConstraintOp.GE,
            rhs=Fraction(ceil_val),
            name=f"{var_name}>={ceil_val}",
        )

        stack.append(
            (
                node_id,
                depth + 1,
                f"{var_name} <= {floor_val}",
                [*extra_constraints, floor_constraint],
            )
        )
        stack.append(
            (node_id, depth + 1, f"{var_name} >= {ceil_val}", [*extra_constraints, ceil_constraint])
        )

    if incumbent_solution is None:
        return BranchAndBoundResult(
            status="infeasible",
            solution=None,
            z=None,
            nodes=nodes,
            message="No existe ninguna solución entera factible para este problema.",
        )

    return BranchAndBoundResult(
        status="optimal",
        solution=incumbent_solution,
        z=incumbent_z,
        nodes=nodes,
        message="Se encontró la solución entera óptima mediante Ramificación y Acotamiento.",
    )
