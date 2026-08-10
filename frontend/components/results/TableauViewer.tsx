"use client";

import { useEffect } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ChevronLeft, ChevronRight, Pause, Play } from "lucide-react";
import { InlineMath } from "react-katex";
import "katex/dist/katex.min.css";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { formatCell, formatFraction } from "@/lib/fraction-format";
import { varNameToLatex } from "@/lib/katex-helpers";
import { useUiStore } from "@/store/ui-store";
import type { TableauIteration } from "@/types/api";

const AUTOPLAY_INTERVAL_MS = 1800;

export function TableauViewer({
  iterations,
  method,
}: {
  iterations: TableauIteration[];
  method: "two_phase" | "big_m";
}) {
  const selected = useUiStore((s) => s.selectedIteration);
  const setSelected = useUiStore((s) => s.setSelectedIteration);
  const isAutoPlaying = useUiStore((s) => s.isAutoPlaying);
  const setAutoPlaying = useUiStore((s) => s.setAutoPlaying);
  const displayMode = useUiStore((s) => s.displayMode);
  const toggleDisplayMode = useUiStore((s) => s.toggleDisplayMode);
  const reduceMotion = useReducedMotion();

  const index = Math.min(selected, iterations.length - 1);
  const iteration = iterations[index];

  useEffect(() => {
    if (!isAutoPlaying) return;
    if (index >= iterations.length - 1) {
      setAutoPlaying(false);
      return;
    }
    const timer = setTimeout(() => setSelected(index + 1), AUTOPLAY_INTERVAL_MS);
    return () => clearTimeout(timer);
  }, [isAutoPlaying, index, iterations.length, setSelected, setAutoPlaying]);

  if (!iteration) {
    return <p className="text-sm text-muted-foreground">No hay iteraciones para mostrar.</p>;
  }

  const transition = reduceMotion ? { duration: 0 } : { duration: 0.22, ease: "easeOut" as const };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="size-11"
            disabled={index === 0}
            onClick={() => {
              setAutoPlaying(false);
              setSelected(index - 1);
            }}
            aria-label="Iteración anterior"
          >
            <ChevronLeft className="size-4" aria-hidden="true" />
          </Button>
          <span className="min-w-32 text-center font-mono text-sm tabular-nums">
            Iteración {index + 1} de {iterations.length}
          </span>
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="size-11"
            disabled={index === iterations.length - 1}
            onClick={() => {
              setAutoPlaying(false);
              setSelected(index + 1);
            }}
            aria-label="Iteración siguiente"
          >
            <ChevronRight className="size-4" aria-hidden="true" />
          </Button>
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setAutoPlaying(!isAutoPlaying)}
          disabled={index === iterations.length - 1 && !isAutoPlaying}
        >
          {isAutoPlaying ? (
            <>
              <Pause className="size-4" aria-hidden="true" /> Pausar
            </>
          ) : (
            <>
              <Play className="size-4" aria-hidden="true" /> Reproducir
            </>
          )}
        </Button>

        <div className="ml-auto flex items-center gap-2">
          <Label htmlFor="display-mode-toggle" className="text-sm text-muted-foreground">
            Fracción
          </Label>
          <Switch
            id="display-mode-toggle"
            checked={displayMode === "decimal"}
            onCheckedChange={toggleDisplayMode}
            aria-label="Alternar entre fracción y decimal"
          />
          <Label htmlFor="display-mode-toggle" className="text-sm text-muted-foreground">
            Decimal
          </Label>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="font-mono">
          {method === "two_phase" ? (iteration.phase === 1 ? "Fase 1" : "Fase 2") : "Gran M"}
        </Badge>
        {iteration.entering && (
          <Badge className="border-success/30 bg-success/10 text-success">
            Entra: <InlineMath math={varNameToLatex(iteration.entering)} />
          </Badge>
        )}
        {iteration.leaving && (
          <Badge className="border-destructive/30 bg-destructive/10 text-destructive">
            Sale: <InlineMath math={varNameToLatex(iteration.leaving)} />
          </Badge>
        )}
        {iteration.is_optimal && (
          <Badge className="border-success/30 bg-success/10 text-success">Óptima</Badge>
        )}
        {iteration.is_degenerate_step && (
          <Badge className="border-warning/30 bg-warning/10 text-warning">Empate (degenerado)</Badge>
        )}
      </div>

      <motion.p
        key={`explanation-${index}`}
        initial={reduceMotion ? false : { opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={transition}
        className="rounded-md border border-border bg-muted/40 p-3 text-sm leading-relaxed text-foreground/90"
      >
        {iteration.explanation}
      </motion.p>

      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="sticky left-0 z-10 min-w-24 bg-muted/50 px-3 py-2 text-left font-medium">
                Base
              </th>
              {iteration.var_names.map((name) => (
                <th key={name} className="min-w-20 px-3 py-2 text-right font-mono font-medium">
                  <InlineMath math={varNameToLatex(name)} />
                </th>
              ))}
              <th className="min-w-24 px-3 py-2 text-right font-medium">RHS</th>
            </tr>
          </thead>
            <motion.tbody
              key={`body-${index}`}
              initial={reduceMotion ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={transition}
            >
              {iteration.matrix.map((row, rowIdx) => (
                <tr key={rowIdx} className="border-b border-border last:border-b-0">
                  <td className="sticky left-0 z-10 bg-card px-3 py-2 font-mono font-medium">
                    <InlineMath math={varNameToLatex(iteration.basis[rowIdx])} />
                  </td>
                  {row.map((cell, colIdx) => {
                    const isPivot = iteration.pivot_row === rowIdx && iteration.pivot_col === colIdx;
                    return (
                      <td
                        key={colIdx}
                        className={cn(
                          "px-3 py-2 text-right font-mono tabular-nums",
                          isPivot && "relative bg-pivot/15 font-semibold text-pivot",
                        )}
                      >
                        {isPivot ? (
                          <motion.span
                            initial={reduceMotion ? false : { scale: 0.85 }}
                            animate={{ scale: 1 }}
                            transition={transition}
                            className="inline-flex rounded border-2 border-pivot px-1.5"
                          >
                            {formatCell(cell, displayMode)}
                          </motion.span>
                        ) : (
                          formatCell(cell, displayMode)
                        )}
                      </td>
                    );
                  })}
                  <td className="px-3 py-2 text-right font-mono tabular-nums">
                    {formatCell(iteration.rhs[rowIdx], displayMode)}
                  </td>
                </tr>
              ))}
              <tr className="bg-muted/30 font-medium">
                <td className="sticky left-0 z-10 bg-muted/30 px-3 py-2">Z</td>
                {iteration.z_row.map((cell, colIdx) => (
                  <td key={colIdx} className="px-3 py-2 text-right font-mono tabular-nums">
                    {formatCell(cell, displayMode)}
                  </td>
                ))}
                <td className="px-3 py-2 text-right font-mono tabular-nums">
                  {formatCell(iteration.z_value, displayMode)}
                </td>
              </tr>
            </motion.tbody>
        </table>
      </div>

      {iteration.ratio_test.length > 0 && (
        <div className="overflow-x-auto rounded-md border border-border">
          <p className="border-b border-border bg-muted/50 px-3 py-2 text-xs font-medium text-muted-foreground">
            Prueba de la razón mínima
          </p>
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="px-3 py-1.5 text-left font-medium">Var. básica</th>
                <th className="px-3 py-1.5 text-right font-medium">RHS</th>
                <th className="px-3 py-1.5 text-right font-medium">Coef. columna</th>
                <th className="px-3 py-1.5 text-right font-medium">Razón</th>
              </tr>
            </thead>
            <tbody>
              {iteration.ratio_test.map((row) => (
                <tr
                  key={row.row}
                  className={cn(
                    "border-b border-border font-mono tabular-nums last:border-b-0",
                    !row.eligible && "text-muted-foreground/60",
                    iteration.pivot_row === row.row && "bg-pivot/10 font-semibold text-pivot",
                  )}
                >
                  <td className="px-3 py-1.5 font-sans">
                    <InlineMath math={varNameToLatex(row.basic_var)} />
                  </td>
                  <td className="px-3 py-1.5 text-right">{formatCell(row.rhs, displayMode)}</td>
                  <td className="px-3 py-1.5 text-right">{formatCell(row.coeff, displayMode)}</td>
                  <td className="px-3 py-1.5 text-right">
                    {row.eligible && row.ratio ? formatFraction(row.ratio, displayMode) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
