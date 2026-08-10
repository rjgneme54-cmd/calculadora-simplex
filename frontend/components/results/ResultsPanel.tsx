"use client";

import { useRef } from "react";
import { FileQuestion } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { BranchBoundTree } from "@/components/results/BranchBoundTree";
import { DualPanel } from "@/components/results/DualPanel";
import { ExportButton } from "@/components/results/ExportButton";
import { ExportSnapshot } from "@/components/results/ExportSnapshot";
import { GraphicalMethod } from "@/components/results/GraphicalMethod";
import { SensitivityPanel } from "@/components/results/SensitivityPanel";
import { SummaryTab } from "@/components/results/SummaryTab";
import { TableauViewer } from "@/components/results/TableauViewer";
import { useProblemStore } from "@/store/problem-store";
import { useUiStore, type ResultsTab } from "@/store/ui-store";

const TAB_LABELS: { value: ResultsTab; label: string }[] = [
  { value: "resumen", label: "Resumen" },
  { value: "iteraciones", label: "Iteraciones" },
  { value: "grafico", label: "Gráfico" },
  { value: "sensibilidad", label: "Sensibilidad" },
  { value: "dual", label: "Dual" },
  { value: "entera", label: "Entera" },
];

export function ResultsPanel() {
  const result = useProblemStore((s) => s.result);
  const isLoading = useProblemStore((s) => s.isLoading);
  const activeTab = useUiStore((s) => s.activeTab);
  const setActiveTab = useUiStore((s) => s.setActiveTab);
  const snapshotRef = useRef<HTMLDivElement>(null);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4" aria-busy="true" aria-live="polite">
        <span className="sr-only">Resolviendo el problema…</span>
        <Skeleton className="h-10 w-full max-w-md" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border p-8 text-center">
        <FileQuestion className="size-10 text-muted-foreground" aria-hidden="true" />
        <div>
          <p className="font-medium text-foreground">Todavía no resolviste ningún problema</p>
          <p className="text-sm text-muted-foreground">
            Completá el formulario o cargá un ejemplo y presioná «Resolver».
          </p>
        </div>
      </div>
    );
  }

  const availability: Record<ResultsTab, boolean> = {
    resumen: true,
    iteraciones: result.iterations.length > 0,
    grafico: result.graphical !== null,
    sensibilidad: result.sensitivity !== null,
    dual: result.dual !== null,
    entera: result.branch_and_bound !== null,
  };

  return (
    <>
      <div className="fixed top-0 left-[-9999px] -z-10" aria-hidden="true">
        <ExportSnapshot ref={snapshotRef} result={result} />
      </div>

      <div className="mb-4 flex justify-end">
        <ExportButton targetRef={snapshotRef} />
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as ResultsTab)}>
        <TabsList className="h-auto w-full flex-wrap justify-start gap-1 bg-transparent p-0 sm:w-auto">
          {TAB_LABELS.map(({ value, label }) => (
            <TabsTrigger
              key={value}
              value={value}
              disabled={!availability[value]}
              className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="resumen" className="mt-4">
          <SummaryTab result={result} />
        </TabsContent>
        <TabsContent value="iteraciones" className="mt-4">
          <TableauViewer iterations={result.iterations} method={result.method} />
        </TabsContent>
        <TabsContent value="grafico" className="mt-4">
          {result.graphical ? (
            <GraphicalMethod graphical={result.graphical} status={result.status} />
          ) : (
            <p className="text-sm text-muted-foreground">
              El método gráfico solo está disponible para problemas de exactamente 2 variables.
            </p>
          )}
        </TabsContent>
        <TabsContent value="sensibilidad" className="mt-4">
          {result.sensitivity ? (
            <SensitivityPanel sensitivity={result.sensitivity} />
          ) : (
            <p className="text-sm text-muted-foreground">
              El análisis de sensibilidad solo está disponible cuando existe una solución óptima.
            </p>
          )}
        </TabsContent>
        <TabsContent value="dual" className="mt-4">
          {result.dual ? (
            <DualPanel dual={result.dual} />
          ) : (
            <p className="text-sm text-muted-foreground">
              El problema dual solo está disponible cuando existe una solución óptima.
            </p>
          )}
        </TabsContent>
        <TabsContent value="entera" className="mt-4">
          {result.branch_and_bound ? (
            <BranchBoundTree data={result.branch_and_bound} />
          ) : (
            <p className="text-sm text-muted-foreground">
              Marcá al menos una variable como entera o binaria para ver Branch &amp; Bound.
            </p>
          )}
        </TabsContent>
      </Tabs>
    </>
  );
}
