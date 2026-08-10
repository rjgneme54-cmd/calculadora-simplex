import type { CellValue, FractionValue } from "@/types/api";

export type DisplayMode = "fraction" | "decimal";

export function formatDecimal(value: number, digits = 4): string {
  if (Number.isInteger(value)) return value.toString();
  const rounded = Number(value.toFixed(digits));
  return rounded.toString();
}

export function formatFraction(value: FractionValue, mode: DisplayMode): string {
  if (mode === "decimal") return formatDecimal(value.decimal);
  if (value.den === 1) return String(value.num);
  return `${value.num}/${value.den}`;
}

export function formatCell(value: CellValue, mode: DisplayMode): string {
  const constStr = formatFraction(value, mode);
  if (value.m_num === 0) return constStr;

  const mMagnitude = value.m_den === 1 ? `${Math.abs(value.m_num)}` : `${Math.abs(value.m_num)}/${value.m_den}`;
  const mTerm = `${mMagnitude === "1" ? "" : mMagnitude}M`;

  if (value.num === 0) {
    return value.m_num < 0 ? `-${mTerm}` : mTerm;
  }
  return `${constStr} ${value.m_num < 0 ? "-" : "+"} ${mTerm}`;
}
