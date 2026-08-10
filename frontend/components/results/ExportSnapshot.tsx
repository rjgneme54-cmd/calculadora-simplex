import { forwardRef } from "react";
import { GraphicalMethod } from "@/components/results/GraphicalMethod";
import { SummaryTab } from "@/components/results/SummaryTab";
import type { SolveResponse } from "@/types/api";

/**
 * Always mounted (off-screen) whenever a result exists, independent of which results tab
 * is active. Radix Tabs unmounts inactive TabsContent entirely, so there is no reliable way
 * to capture "whatever the user is currently looking at" -- this renders summary + graph
 * fresh from data instead, guaranteeing both are available to export on demand.
 */
export const ExportSnapshot = forwardRef<HTMLDivElement, { result: SolveResponse }>(
  function ExportSnapshot({ result }, ref) {
    return (
      <div ref={ref} className="w-[800px] bg-background p-8 text-foreground">
        <h1 className="mb-4 text-xl font-semibold">Simplex Solver — Resultado</h1>
        <SummaryTab result={result} />
        {result.graphical && (
          <div className="mt-6">
            <h2 className="mb-2 text-base font-semibold">Método gráfico</h2>
            <GraphicalMethod graphical={result.graphical} status={result.status} />
          </div>
        )}
      </div>
    );
  },
);
