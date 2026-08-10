"use client";

import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatFraction } from "@/lib/fraction-format";
import { varNameToLatex } from "@/lib/katex-helpers";
import { useUiStore } from "@/store/ui-store";
import type { SolveResponse } from "@/types/api";
import { InlineMath } from "react-katex";
import "katex/dist/katex.min.css";

const STATUS_CONFIG = {
  optimal: {
    label: "Solución óptima",
    icon: CheckCircle2,
    className: "border-success/30 bg-success/10 text-success",
  },
  unbounded: {
    label: "Problema no acotado",
    icon: AlertTriangle,
    className: "border-warning/30 bg-warning/10 text-warning",
  },
  infeasible: {
    label: "Problema infactible",
    icon: XCircle,
    className: "border-destructive/30 bg-destructive/10 text-destructive",
  },
} as const;

export function SummaryTab({ result }: { result: SolveResponse }) {
  const displayMode = useUiStore((s) => s.displayMode);
  const status = STATUS_CONFIG[result.status];
  const StatusIcon = status.icon;

  return (
    <div className="flex flex-col gap-4">
      <Card className={status.className}>
        <CardContent className="flex items-start gap-3 pt-6">
          <StatusIcon className="mt-0.5 size-6 shrink-0" aria-hidden="true" />
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-lg font-semibold">{status.label}</p>
              <Badge variant="outline" className="font-mono text-xs">
                {result.method === "two_phase" ? "Dos Fases" : "Gran M"}
              </Badge>
              {result.has_alternate_optima && (
                <Badge className="border-warning/30 bg-warning/10 text-warning">
                  Óptimos alternativos
                </Badge>
              )}
              {result.is_degenerate && (
                <Badge className="border-warning/30 bg-warning/10 text-warning">Degenerado</Badge>
              )}
            </div>
            <p className="text-sm leading-relaxed text-foreground/90">{result.message}</p>
          </div>
        </CardContent>
      </Card>

      {result.status === "optimal" && result.z && result.solution && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Valor óptimo</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-mono text-3xl font-semibold tabular-nums text-primary">
                Z = {formatFraction(result.z, displayMode)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Solución</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-1.5">
              {Object.entries(result.solution).map(([name, value]) => (
                <div key={name} className="flex items-center justify-between font-mono text-sm">
                  <InlineMath math={varNameToLatex(name)} />
                  <span className="tabular-nums">{formatFraction(value, displayMode)}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
