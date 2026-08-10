from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from app.core.models import ConstraintOp, LPProblem, Sense, VarSign


@dataclass
class ColumnInfo:
    name: str
    kind: str  # "decision" | "slack" | "surplus" | "artificial"
    source_var: str | None = None
    sign_multiplier: int = 1  # +1 normally, -1 for the "negative part" column of a split free var


@dataclass
class StandardForm:
    columns: list[ColumnInfo]
    c: list[Fraction]
    a: list[list[Fraction]]
    b: list[Fraction]
    artificial_cols: list[int]
    initial_basis: list[int]
    original_sense: Sense
    var_column_map: dict[str, list[tuple[int, int]]]  # var name -> [(col_index, multiplier), ...]

    @property
    def var_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def num_cols(self) -> int:
        return len(self.columns)

    def num_rows(self) -> int:
        return len(self.b)


def build_standard_form(problem: LPProblem) -> StandardForm:
    columns: list[ColumnInfo] = []
    var_column_map: dict[str, list[tuple[int, int]]] = {}

    for variable in problem.variables:
        if variable.sign == VarSign.FREE:
            pos_idx = len(columns)
            columns.append(
                ColumnInfo(
                    name=f"{variable.name}_pos",
                    kind="decision",
                    source_var=variable.name,
                    sign_multiplier=1,
                )
            )
            neg_idx = len(columns)
            columns.append(
                ColumnInfo(
                    name=f"{variable.name}_neg",
                    kind="decision",
                    source_var=variable.name,
                    sign_multiplier=-1,
                )
            )
            var_column_map[variable.name] = [(pos_idx, 1), (neg_idx, -1)]
        else:
            idx = len(columns)
            columns.append(
                ColumnInfo(name=variable.name, kind="decision", source_var=variable.name)
            )
            var_column_map[variable.name] = [(idx, 1)]

    num_decision_cols = len(columns)

    def expand_row(coeffs: list[Fraction]) -> list[Fraction]:
        row = [Fraction(0)] * num_decision_cols
        for var, coeff in zip(problem.variables, coeffs, strict=True):
            for col_idx, mult in var_column_map[var.name]:
                row[col_idx] += coeff * mult
        return row

    sign = 1 if problem.sense == Sense.MAX else -1
    c = expand_row([sign * coeff for coeff in problem.objective])

    a_rows: list[list[Fraction]] = []
    b: list[Fraction] = []
    ops: list[ConstraintOp] = []
    for constraint in problem.constraints:
        row = expand_row(constraint.coeffs)
        rhs = constraint.rhs
        op = constraint.op
        if rhs < 0:
            row = [-v for v in row]
            rhs = -rhs
            if op == ConstraintOp.LE:
                op = ConstraintOp.GE
            elif op == ConstraintOp.GE:
                op = ConstraintOp.LE
        a_rows.append(row)
        b.append(rhs)
        ops.append(op)

    artificial_cols: list[int] = []
    initial_basis: list[int] = []

    for row_idx, op in enumerate(ops):
        if op == ConstraintOp.LE:
            slack_idx = len(columns)
            columns.append(ColumnInfo(name=f"s{row_idx + 1}", kind="slack"))
            for r_idx, r in enumerate(a_rows):
                r.append(Fraction(1) if r_idx == row_idx else Fraction(0))
            c.append(Fraction(0))
            initial_basis.append(slack_idx)
        elif op == ConstraintOp.GE:
            columns.append(ColumnInfo(name=f"e{row_idx + 1}", kind="surplus"))
            for r_idx, r in enumerate(a_rows):
                r.append(Fraction(-1) if r_idx == row_idx else Fraction(0))
            c.append(Fraction(0))

            art_idx = len(columns)
            columns.append(ColumnInfo(name=f"a{row_idx + 1}", kind="artificial"))
            for r_idx, r in enumerate(a_rows):
                r.append(Fraction(1) if r_idx == row_idx else Fraction(0))
            c.append(Fraction(0))
            artificial_cols.append(art_idx)
            initial_basis.append(art_idx)
        else:  # EQ
            art_idx = len(columns)
            columns.append(ColumnInfo(name=f"a{row_idx + 1}", kind="artificial"))
            for r_idx, r in enumerate(a_rows):
                r.append(Fraction(1) if r_idx == row_idx else Fraction(0))
            c.append(Fraction(0))
            artificial_cols.append(art_idx)
            initial_basis.append(art_idx)

    return StandardForm(
        columns=columns,
        c=c,
        a=a_rows,
        b=b,
        artificial_cols=artificial_cols,
        initial_basis=initial_basis,
        original_sense=problem.sense,
        var_column_map=var_column_map,
    )


def extract_original_values(
    problem: LPProblem, standard_form: StandardForm, column_values: list[Fraction]
) -> dict[str, Fraction]:
    result: dict[str, Fraction] = {}
    for variable in problem.variables:
        total = Fraction(0)
        for col_idx, mult in standard_form.var_column_map[variable.name]:
            total += column_values[col_idx] * mult
        result[variable.name] = total
    return result
