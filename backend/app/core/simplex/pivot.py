from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from app.core.models import RatioTestRow


@dataclass
class Tableau:
    var_names: list[str]
    basis: list[int]
    body: list[list[object]]
    rhs: list[object]
    z_row: list[object]
    z_value: object

    def num_rows(self) -> int:
        return len(self.body)

    def num_cols(self) -> int:
        return len(self.var_names)

    def snapshot(self) -> tuple[list[str], list[list[object]], list[object], list[object], object]:
        basis_names = [self.var_names[b] for b in self.basis]
        matrix = [row[:] for row in self.body]
        return basis_names, matrix, self.rhs[:], self.z_row[:], self.z_value

    def column_values(self) -> list[Fraction]:
        values = [Fraction(0)] * self.num_cols()
        for row_idx, col_idx in enumerate(self.basis):
            values[col_idx] = self.rhs[row_idx]
        return values


def compute_reduced_costs(tableau: Tableau, c: list, zero: object) -> list:
    n = tableau.num_cols()
    z_row = []
    for j in range(n):
        zj = zero
        for i in range(tableau.num_rows()):
            zj = zj + c[tableau.basis[i]] * tableau.body[i][j]
        z_row.append(c[j] - zj)
    return z_row


def compute_z_value(tableau: Tableau, c: list, zero: object) -> object:
    zv = zero
    for i in range(tableau.num_rows()):
        zv = zv + c[tableau.basis[i]] * tableau.rhs[i]
    return zv


def select_entering_column(
    z_row: list[object], excluded: set[int] | None = None, use_bland: bool = False
) -> int | None:
    excluded = excluded or set()
    candidates = [j for j in range(len(z_row)) if j not in excluded and z_row[j] > 0]
    if not candidates:
        return None
    if use_bland:
        return min(candidates)
    best = candidates[0]
    for j in candidates[1:]:
        if z_row[j] > z_row[best]:
            best = j
    return best


def compute_ratio_test(
    tableau: Tableau, col: int, protected_rows: set[int] | None = None
) -> tuple[list[RatioTestRow], int | None, bool]:
    """protected_rows marks rows whose basic variable is an artificial currently at value 0.
    Any nonzero coefficient there -- even negative -- must force ratio 0: a negative
    coefficient would otherwise let that artificial grow positive as a side effect of this
    pivot without ever being checked, silently leaving the true feasible region."""
    protected_rows = protected_rows or set()
    rows: list[RatioTestRow] = []
    eligible: list[tuple[Fraction, int, int]] = []

    for i in range(tableau.num_rows()):
        coeff = tableau.body[i][col]
        basic_var = tableau.var_names[tableau.basis[i]]
        if i in protected_rows and coeff != 0:
            ratio = Fraction(0)
            eligible.append((ratio, i, tableau.basis[i]))
            rows.append(
                RatioTestRow(
                    row=i,
                    basic_var=basic_var,
                    rhs=tableau.rhs[i],
                    coeff=coeff,
                    ratio=ratio,
                    eligible=True,
                )
            )
        elif coeff > 0:
            ratio = tableau.rhs[i] / coeff
            eligible.append((ratio, i, tableau.basis[i]))
            rows.append(
                RatioTestRow(
                    row=i,
                    basic_var=basic_var,
                    rhs=tableau.rhs[i],
                    coeff=coeff,
                    ratio=ratio,
                    eligible=True,
                )
            )
        else:
            rows.append(
                RatioTestRow(
                    row=i,
                    basic_var=basic_var,
                    rhs=tableau.rhs[i],
                    coeff=coeff,
                    ratio=None,
                    eligible=False,
                )
            )

    if not eligible:
        return rows, None, False

    min_ratio = min(r[0] for r in eligible)
    tied = [r for r in eligible if r[0] == min_ratio]
    tie = len(tied) > 1
    best_row = min(tied, key=lambda r: r[2])[1]
    return rows, best_row, tie


def apply_pivot(tableau: Tableau, row: int, col: int) -> object:
    pivot_element = tableau.body[row][col]
    n = tableau.num_cols()

    tableau.body[row] = [v / pivot_element for v in tableau.body[row]]
    tableau.rhs[row] = tableau.rhs[row] / pivot_element

    for i in range(tableau.num_rows()):
        if i == row:
            continue
        factor = tableau.body[i][col]
        if factor == 0:
            continue
        tableau.body[i] = [tableau.body[i][j] - factor * tableau.body[row][j] for j in range(n)]
        tableau.rhs[i] = tableau.rhs[i] - factor * tableau.rhs[row]

    factor_z = tableau.z_row[col]
    if factor_z != 0:
        tableau.z_row = [tableau.z_row[j] - factor_z * tableau.body[row][j] for j in range(n)]
        tableau.z_value = tableau.z_value + factor_z * tableau.rhs[row]

    tableau.basis[row] = col
    return pivot_element
