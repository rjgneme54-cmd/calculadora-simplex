import type { FractionValue } from "@/types/api";
import { formatDecimal, type DisplayMode } from "@/lib/fraction-format";

const OP_LATEX: Record<string, string> = { "<=": "\\leq", ">=": "\\geq", "=": "=" };

export function varNameToLatex(name: string): string {
  const match = name.match(/^([a-zA-Z]+)(\d+)$/);
  if (match) return `${match[1]}_{${match[2]}}`;
  return name.replace(/_/g, "\\_");
}

export function fractionToLatex(value: FractionValue, mode: DisplayMode): string {
  if (mode === "decimal") return formatDecimal(value.decimal);
  if (value.den === 1) return `${value.num}`;
  const sign = value.num < 0 ? "-" : "";
  return `${sign}\\frac{${Math.abs(value.num)}}{${value.den}}`;
}

function buildLinearExpression(
  coeffs: FractionValue[],
  varNames: string[],
  mode: DisplayMode,
): string {
  let result = "";
  coeffs.forEach((c, i) => {
    if (c.num === 0) return;
    const negative = c.num < 0;
    const absValue: FractionValue = { num: Math.abs(c.num), den: c.den, decimal: Math.abs(c.decimal) };
    const coefLatex = fractionToLatex(absValue, mode);
    const isOne = absValue.den === 1 && absValue.num === 1;
    const varLabel = varNameToLatex(varNames[i]);
    const term = isOne ? varLabel : `${coefLatex}\\,${varLabel}`;

    if (result === "") {
      result = negative ? `-${term}` : term;
    } else {
      result += negative ? ` - ${term}` : ` + ${term}`;
    }
  });
  return result || "0";
}

export function objectiveToLatex(
  sense: "max" | "min",
  coeffs: FractionValue[],
  varNames: string[],
  mode: DisplayMode,
  label = "Z",
): string {
  const senseText = sense === "max" ? "Max" : "Min";
  return `\\text{${senseText} } ${label} = ${buildLinearExpression(coeffs, varNames, mode)}`;
}

export function buildLinearExpressionFromNumbers(coeffs: number[], varNames: string[]): string {
  let result = "";
  coeffs.forEach((value, i) => {
    if (!value) return;
    const negative = value < 0;
    const abs = Math.abs(value);
    const varLabel = varNameToLatex(varNames[i] ?? `x_{${i + 1}}`);
    const term = abs === 1 ? varLabel : `${abs}\\,${varLabel}`;
    if (result === "") {
      result = negative ? `-${term}` : term;
    } else {
      result += negative ? ` - ${term}` : ` + ${term}`;
    }
  });
  return result || "0";
}

export function constraintToLatex(
  coeffs: FractionValue[],
  varNames: string[],
  op: string,
  rhs: FractionValue,
  mode: DisplayMode,
): string {
  const lhs = buildLinearExpression(coeffs, varNames, mode);
  const rhsLatex = fractionToLatex(rhs, mode);
  return `${lhs} ${OP_LATEX[op] ?? op} ${rhsLatex}`;
}
