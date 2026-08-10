import { describe, expect, it } from "vitest";
import { formatCell, formatDecimal, formatFraction } from "@/lib/fraction-format";
import type { CellValue, FractionValue } from "@/types/api";

function frac(num: number, den: number): FractionValue {
  return { num, den, decimal: num / den };
}

function cell(num: number, den: number, mNum = 0, mDen = 1): CellValue {
  return { num, den, decimal: num / den, m_num: mNum, m_den: mDen };
}

describe("formatDecimal", () => {
  it("returns whole numbers without decimal point", () => {
    expect(formatDecimal(6)).toBe("6");
  });

  it("trims trailing zeros on non-integers", () => {
    expect(formatDecimal(2.5)).toBe("2.5");
  });

  it("rounds to the given number of digits", () => {
    expect(formatDecimal(1 / 3, 4)).toBe("0.3333");
  });
});

describe("formatFraction", () => {
  it("renders whole fractions (den=1) as plain integers", () => {
    expect(formatFraction(frac(36, 1), "fraction")).toBe("36");
  });

  it("renders non-trivial fractions as num/den", () => {
    expect(formatFraction(frac(7, 3), "fraction")).toBe("7/3");
  });

  it("renders negative fractions with the sign on the numerator", () => {
    expect(formatFraction(frac(-5, 2), "fraction")).toBe("-5/2");
  });

  it("switches to decimal display in decimal mode", () => {
    expect(formatFraction(frac(1, 2), "decimal")).toBe("0.5");
  });
});

describe("formatCell", () => {
  it("behaves like formatFraction when there is no M term", () => {
    expect(formatCell(cell(7, 3), "fraction")).toBe("7/3");
    expect(formatCell(cell(1, 2), "decimal")).toBe("0.5");
  });

  it("renders a pure M term without a spurious '0 +' prefix", () => {
    expect(formatCell(cell(0, 1, -1, 1), "fraction")).toBe("-M");
    expect(formatCell(cell(0, 1, 3, 1), "fraction")).toBe("3M");
  });

  it("renders a constant plus an M term with the correct sign", () => {
    expect(formatCell(cell(3, 1, -2, 1), "fraction")).toBe("3 - 2M");
    expect(formatCell(cell(3, 1, 2, 1), "fraction")).toBe("3 + 2M");
  });

  it("omits the coefficient when the M magnitude is 1", () => {
    expect(formatCell(cell(0, 1, 1, 1), "fraction")).toBe("M");
    expect(formatCell(cell(0, 1, -1, 1), "fraction")).toBe("-M");
  });
});
