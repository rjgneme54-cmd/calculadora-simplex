"use client";

import { InlineMath } from "react-katex";
import "katex/dist/katex.min.css";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatFraction } from "@/lib/fraction-format";
import { varNameToLatex } from "@/lib/katex-helpers";
import { useUiStore } from "@/store/ui-store";
import type { FractionValue, SensitivityData } from "@/types/api";

function boundLabel(bound: FractionValue | null, displayMode: "fraction" | "decimal"): string {
  return bound === null ? "sin límite" : formatFraction(bound, displayMode);
}

export function SensitivityPanel({ sensitivity }: { sensitivity: SensitivityData }) {
  const displayMode = useUiStore((s) => s.displayMode);

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Rangos de la función objetivo</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Variable</TableHead>
                <TableHead className="text-right">Valor actual</TableHead>
                <TableHead className="text-right">Límite inferior</TableHead>
                <TableHead className="text-right">Límite superior</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sensitivity.objective_ranges.map((r) => (
                <TableRow key={r.variable_name}>
                  <TableCell className="font-mono font-medium">
                    <InlineMath math={varNameToLatex(r.variable_name)} />
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums">
                    {formatFraction(r.current_value, displayMode)}
                  </TableCell>
                  {r.applicable ? (
                    <>
                      <TableCell className="text-right font-mono tabular-nums">
                        {boundLabel(r.lower, displayMode)}
                      </TableCell>
                      <TableCell className="text-right font-mono tabular-nums">
                        {boundLabel(r.upper, displayMode)}
                      </TableCell>
                    </>
                  ) : (
                    <TableCell colSpan={2} className="text-center text-sm text-muted-foreground">
                      No aplica (variable libre)
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <p className="mt-2 text-xs text-muted-foreground">
            Rango en el que puede variar cada coeficiente sin que cambie la base óptima actual.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Precios sombra y rangos del lado derecho (RHS)</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Restricción</TableHead>
                <TableHead className="text-right">RHS actual</TableHead>
                <TableHead className="text-right">Límite inferior</TableHead>
                <TableHead className="text-right">Límite superior</TableHead>
                <TableHead className="text-right">Precio sombra</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sensitivity.rhs_ranges.map((r) => (
                <TableRow key={r.constraint_name}>
                  <TableCell className="font-medium">{r.constraint_name}</TableCell>
                  <TableCell className="text-right font-mono tabular-nums">
                    {formatFraction(r.current_value, displayMode)}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums">
                    {boundLabel(r.lower, displayMode)}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums">
                    {boundLabel(r.upper, displayMode)}
                  </TableCell>
                  <TableCell className="text-right font-mono font-semibold tabular-nums">
                    {formatFraction(r.shadow_price, displayMode)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="mt-3 flex flex-col gap-1.5 text-sm">
            {sensitivity.rhs_ranges.map((r) => (
              <p key={r.constraint_name} className="text-muted-foreground">
                <span className="font-medium text-foreground">{r.constraint_name}:</span>{" "}
                {r.shadow_price.num === 0 ? (
                  <>no es restrictiva en el óptimo (holgura); cambiar su RHS dentro del rango no afecta a Z.</>
                ) : (
                  <>
                    es restrictiva en el óptimo: por cada unidad que aumente su RHS, Z cambia en{" "}
                    <span className="font-mono">{formatFraction(r.shadow_price, displayMode)}</span>,
                    mientras el RHS se mantenga en el rango indicado.
                  </>
                )}
              </p>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
