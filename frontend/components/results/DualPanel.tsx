"use client";

import { CheckCircle2, XCircle } from "lucide-react";
import { InlineMath } from "react-katex";
import "katex/dist/katex.min.css";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatFraction } from "@/lib/fraction-format";
import { constraintToLatex, objectiveToLatex, varNameToLatex } from "@/lib/katex-helpers";
import { useUiStore } from "@/store/ui-store";
import type { DualData, DualVariableSign } from "@/types/api";

const SIGN_LABEL: Record<DualVariableSign, string> = {
  nonnegative: "≥ 0",
  nonpositive: "≤ 0",
  free: "libre",
};

export function DualPanel({ dual }: { dual: DualData }) {
  const displayMode = useUiStore((s) => s.displayMode);
  const dualVarNames = dual.dual_variables.map((v) => v.name);

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Formulación del dual</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="overflow-x-auto rounded-md bg-muted/40 p-3">
            <InlineMath
              math={objectiveToLatex(dual.dual_sense, dual.dual_objective_coeffs, dualVarNames, displayMode, "W")}
            />
          </div>
          <p className="text-xs text-muted-foreground">Sujeto a:</p>
          <div className="flex flex-col gap-1.5 overflow-x-auto rounded-md bg-muted/40 p-3">
            {dual.dual_constraints.map((c) => (
              <div key={c.primal_variable_name} className="flex items-center gap-3">
                <InlineMath math={constraintToLatex(c.coeffs, dualVarNames, c.op, c.rhs, displayMode)} />
                <span className="text-xs text-muted-foreground">
                  (variable dual de {c.primal_variable_name})
                </span>
              </div>
            ))}
            <div className="mt-1 flex flex-wrap gap-1.5">
              {dual.dual_variables.map((v) => (
                <Badge key={v.name} variant="outline" className="font-mono text-xs">
                  {v.name} {SIGN_LABEL[v.sign]}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Solución del dual</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Variable dual</TableHead>
                <TableHead>Restricción primal asociada</TableHead>
                <TableHead>Signo</TableHead>
                <TableHead className="text-right">Valor</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dual.dual_variables.map((v) => (
                <TableRow key={v.name}>
                  <TableCell className="font-mono font-medium">
                    <InlineMath math={varNameToLatex(v.name)} />
                  </TableCell>
                  <TableCell>{v.primal_constraint_name}</TableCell>
                  <TableCell className="font-mono text-muted-foreground">
                    {SIGN_LABEL[v.sign]}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums">
                    {formatFraction(v.value, displayMode)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card className={dual.strong_duality_holds ? "border-success/30 bg-success/10" : "border-destructive/30 bg-destructive/10"}>
        <CardContent className="flex items-center gap-3 pt-6">
          {dual.strong_duality_holds ? (
            <CheckCircle2 className="size-5 shrink-0 text-success" aria-hidden="true" />
          ) : (
            <XCircle className="size-5 shrink-0 text-destructive" aria-hidden="true" />
          )}
          <p className="text-sm">
            <span className="font-medium">Dualidad fuerte:</span> Z primal ={" "}
            <span className="font-mono">{formatFraction(dual.primal_z, displayMode)}</span> = Z dual{" "}
            <span className="font-mono">{formatFraction(dual.dual_z, displayMode)}</span>.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Holgura complementaria</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {dual.complementary_slackness.map((item, idx) => (
            <div key={idx} className="flex items-start gap-2 text-sm">
              {item.holds ? (
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" aria-hidden="true" />
              ) : (
                <XCircle className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden="true" />
              )}
              <span className={item.holds ? "text-foreground/90" : "text-destructive"}>
                {item.description}
              </span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
