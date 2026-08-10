"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import type { Data, Layout } from "plotly.js";
import { AlertTriangle, XCircle, Maximize2, RotateCcw, ZoomIn } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatFraction } from "@/lib/fraction-format";
import { useChartColors } from "@/lib/use-chart-colors";
import { useUiStore } from "@/store/ui-store";
import type { GraphicalData, PlotBounds, SolveStatus } from "@/types/api";

const Plot = dynamic(() => import("@/components/results/PlotlyChart"), {
  ssr: false,
  loading: () => <Skeleton className="h-[460px] w-full" />,
});

const FRAME_COUNT = 24;

function clipObjectiveLine(c1: number, c2: number, z: number, bounds: PlotBounds) {
  const { xmin, xmax, ymin, ymax } = bounds;
  if (c2 !== 0) {
    return { x: [xmin, xmax], y: [(z - c1 * xmin) / c2, (z - c1 * xmax) / c2] };
  }
  const x = c1 !== 0 ? z / c1 : 0;
  return { x: [x, x], y: [ymin, ymax] };
}

export function GraphicalMethod({
  graphical,
  status,
  interactive = true,
}: {
  graphical: GraphicalData;
  status: SolveStatus;
  interactive?: boolean;
}) {
  const displayMode = useUiStore((s) => s.displayMode);
  const colors = useChartColors();
  const [varX, varY] = graphical.var_names;
  const hasOptimal = status === "optimal" && graphical.optimal_vertices.length > 0;
  const [viewOverride, setViewOverride] = useState<{ xrange: [number, number]; yrange: [number, number] } | null>(
    null,
  );

  useEffect(() => {
    setViewOverride(null);
  }, [graphical]);

  const { data, layout, frames, bounds, fitBounds } = useMemo(() => {
    const bounds = graphical.plot_bounds;
    const c1 = graphical.objective_coeffs[0].decimal;
    const c2 = graphical.objective_coeffs[1].decimal;

    const traces: Data[] = [];

    if (graphical.feasible_vertices.length >= 3) {
      traces.push({
        type: "scatter",
        mode: "lines",
        x: [...graphical.feasible_vertices.map((v) => v.x.decimal), graphical.feasible_vertices[0].x.decimal],
        y: [...graphical.feasible_vertices.map((v) => v.y.decimal), graphical.feasible_vertices[0].y.decimal],
        fill: "toself",
        fillcolor: `${colors.primary}26`,
        line: { color: colors.primary, width: 1.5 },
        name: "Región factible",
        hoverinfo: "skip",
      });
    }

    for (const line of graphical.lines) {
      traces.push({
        type: "scatter",
        mode: "lines",
        x: [line.point1.x, line.point2.x],
        y: [line.point1.y, line.point2.y],
        line: { color: colors.mutedForeground, width: 1.5, dash: "dot" },
        name: line.label,
        hoverinfo: "name",
      });
    }

    if (graphical.feasible_vertices.length > 0) {
      traces.push({
        type: "scatter",
        mode: "text+markers",
        x: graphical.feasible_vertices.map((v) => v.x.decimal),
        y: graphical.feasible_vertices.map((v) => v.y.decimal),
        text: graphical.feasible_vertices.map((v) => v.label),
        textposition: "top center",
        marker: { color: colors.foreground, size: 7 },
        customdata: graphical.feasible_vertices.map(
          (v) =>
            `${v.label}: (${formatFraction(v.x, "fraction")}, ${formatFraction(v.y, "fraction")})  Z=${formatFraction(v.z, "fraction")}`,
        ),
        hovertemplate: "%{customdata}<extra></extra>",
        name: "Vértices",
      });
    }

    if (hasOptimal) {
      traces.push({
        type: "scatter",
        mode: "markers",
        x: graphical.optimal_vertices.map((v) => v.x.decimal),
        y: graphical.optimal_vertices.map((v) => v.y.decimal),
        marker: { color: colors.success, size: 15, symbol: "star", line: { color: colors.card, width: 1 } },
        customdata: graphical.optimal_vertices.map(
          (v) => `Óptimo ${v.label}: Z=${formatFraction(v.z, "fraction")}`,
        ),
        hovertemplate: "%{customdata}<extra></extra>",
        name: "Óptimo",
      });
    }

    const feasibleZs = graphical.feasible_vertices.map((v) => v.z.decimal);
    const zOptimal = hasOptimal ? graphical.optimal_vertices[0].z.decimal : 0;
    const zAverage = feasibleZs.length
      ? feasibleZs.reduce((a, b) => a + b, 0) / feasibleZs.length
      : 0;
    const zStart = feasibleZs.length
      ? zOptimal >= zAverage
        ? Math.min(...feasibleZs, 0)
        : Math.max(...feasibleZs, 0)
      : 0;

    const initialLine = clipObjectiveLine(c1, c2, hasOptimal ? zStart : 0, bounds);
    const objectiveIndex = traces.length;
    traces.push({
      type: "scatter",
      mode: "lines",
      x: initialLine.x,
      y: initialLine.y,
      line: { color: colors.warning, width: 2, dash: "dash" },
      name: "Función objetivo",
      hoverinfo: "name",
    });

    const animationFrames = hasOptimal
      ? Array.from({ length: FRAME_COUNT + 1 }, (_, i) => {
          const t = i / FRAME_COUNT;
          const z = zStart + (zOptimal - zStart) * t;
          const line = clipObjectiveLine(c1, c2, z, bounds);
          return { name: `f${i}`, data: [{ x: line.x, y: line.y }], traces: [objectiveIndex] };
        })
      : [];

    const chartLayout: Partial<Layout> = {
      autosize: true,
      height: 460,
      margin: { l: 55, r: 20, t: hasOptimal ? 50 : 20, b: 55 },
      xaxis: {
        title: { text: varX },
        range: [bounds.xmin, bounds.xmax],
        zeroline: true,
        gridcolor: colors.border,
      },
      yaxis: {
        title: { text: varY },
        range: [bounds.ymin, bounds.ymax],
        zeroline: true,
        gridcolor: colors.border,
      },
      showlegend: true,
      legend: { orientation: "h", y: -0.18 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: colors.foreground },
      dragmode: "zoom",
      updatemenus: hasOptimal
        ? [
            {
              type: "buttons",
              x: 0,
              y: 1.18,
              showactive: false,
              buttons: [
                {
                  label: "▶ Reproducir barrido",
                  method: "animate",
                  args: [
                    null,
                    {
                      frame: { duration: 90, redraw: true },
                      transition: { duration: 40 },
                      fromcurrent: false,
                      mode: "immediate",
                    },
                  ],
                },
              ],
            },
          ]
        : [],
    };

    const vx = graphical.feasible_vertices.map((v) => v.x.decimal);
    const vy = graphical.feasible_vertices.map((v) => v.y.decimal);
    const nonnegX = bounds.xmin >= -1e-9;
    const nonnegY = bounds.ymin >= -1e-9;
    const rawMinX = nonnegX ? 0 : Math.min(...vx, 0);
    const rawMaxX = Math.max(...vx, 1);
    const rawMinY = nonnegY ? 0 : Math.min(...vy, 0);
    const rawMaxY = Math.max(...vy, 1);
    const padX = (rawMaxX - rawMinX) * 0.15 || 1;
    const padY = (rawMaxY - rawMinY) * 0.15 || 1;
    const fitBounds =
      vx.length > 0
        ? { xmin: rawMinX - padX, xmax: rawMaxX + padX, ymin: rawMinY - padY, ymax: rawMaxY + padY }
        : bounds;

    return { data: traces, layout: chartLayout, frames: animationFrames, bounds, fitBounds };
  }, [graphical, hasOptimal, colors, varX, varY]);

  const displayLayout: Partial<Layout> = viewOverride
    ? {
        ...layout,
        xaxis: { ...layout.xaxis, range: viewOverride.xrange },
        yaxis: { ...layout.yaxis, range: viewOverride.yrange },
      }
    : layout;

  function resetView() {
    setViewOverride({ xrange: [bounds.xmin, bounds.xmax], yrange: [bounds.ymin, bounds.ymax] });
  }

  function fitToFeasibleRegion() {
    setViewOverride({ xrange: [fitBounds.xmin, fitBounds.xmax], yrange: [fitBounds.ymin, fitBounds.ymax] });
  }

  return (
    <div className="flex flex-col gap-4">
      {status === "infeasible" && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          <XCircle className="size-4 shrink-0" aria-hidden="true" />
          Ningún punto satisface todas las restricciones: no hay región factible que graficar.
        </div>
      )}
      {status === "unbounded" && (
        <div className="flex items-center gap-2 rounded-md border border-warning/30 bg-warning/10 p-3 text-sm text-warning">
          <AlertTriangle className="size-4 shrink-0" aria-hidden="true" />
          La región factible es no acotada: no existe un único punto óptimo para resaltar.
        </div>
      )}

      <div className="overflow-hidden rounded-md border border-border">
        {interactive && (
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-muted/40 px-3 py-2">
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <ZoomIn className="size-3.5 shrink-0" aria-hidden="true" />
              Rueda del mouse o pellizco para hacer zoom, arrastrá para desplazarte, doble clic para restablecer.
            </p>
            <div className="flex items-center gap-1.5">
              <Button type="button" variant="outline" size="sm" onClick={fitToFeasibleRegion}>
                <Maximize2 className="size-3.5" aria-hidden="true" />
                Ajustar a la región factible
              </Button>
              <Button type="button" variant="outline" size="sm" onClick={resetView}>
                <RotateCcw className="size-3.5" aria-hidden="true" />
                Restablecer vista
              </Button>
            </div>
          </div>
        )}
        <Plot
          data={data}
          layout={displayLayout}
          frames={frames}
          config={{
            scrollZoom: true,
            displaylogo: false,
            responsive: true,
            displayModeBar: interactive,
            doubleClick: "reset+autosize",
            modeBarButtonsToRemove: ["lasso2d", "select2d"],
          }}
          style={{ width: "100%", height: "460px" }}
          useResizeHandler
        />
      </div>

      <div className="overflow-x-auto rounded-md border border-border">
        <Table>
          <TableCaption className="text-left">
            Tabla de datos equivalente al gráfico, para lectores de pantalla o consulta exacta.
          </TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Vértice</TableHead>
              <TableHead className="text-right font-mono">{varX}</TableHead>
              <TableHead className="text-right font-mono">{varY}</TableHead>
              <TableHead className="text-right">Z</TableHead>
              <TableHead>Estado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {graphical.feasible_vertices.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  No hay vértices factibles.
                </TableCell>
              </TableRow>
            )}
            {graphical.feasible_vertices.map((vertex) => {
              const isOptimal = graphical.optimal_vertices.some((v) => v.label === vertex.label);
              return (
                <TableRow key={vertex.label} className={isOptimal ? "bg-success/10" : undefined}>
                  <TableCell className="font-mono font-medium">{vertex.label}</TableCell>
                  <TableCell className="text-right font-mono tabular-nums">
                    {formatFraction(vertex.x, displayMode)}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums">
                    {formatFraction(vertex.y, displayMode)}
                  </TableCell>
                  <TableCell className="text-right font-mono tabular-nums">
                    {formatFraction(vertex.z, displayMode)}
                  </TableCell>
                  <TableCell>
                    {isOptimal && (
                      <Badge className="border-success/30 bg-success/10 text-success">Óptimo</Badge>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
