"use client";

import { Calculator, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui-store";

export function AppShell({
  formSlot,
  resultsSlot,
}: {
  formSlot: React.ReactNode;
  resultsSlot: React.ReactNode;
}) {
  const collapsed = useUiStore((s) => s.formPanelCollapsed);
  const toggleFormPanel = useUiStore((s) => s.toggleFormPanel);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between border-b border-border bg-card/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-card/75 sm:px-6">
        <div className="flex items-center gap-2.5">
          <div className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Calculator className="size-4" aria-hidden="true" />
          </div>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-foreground">Simplex Solver</p>
            <p className="hidden text-xs text-muted-foreground sm:block">
              Programación Lineal · Método Simplex y Gráfico
            </p>
          </div>
        </div>
        <ThemeToggle />
      </header>

      <div className="flex flex-1 flex-col lg:flex-row">
        <aside
          className={cn(
            "border-border bg-card lg:sticky lg:top-14 lg:h-[calc(100vh-3.5rem)] lg:overflow-y-auto lg:border-r",
            collapsed ? "lg:hidden" : "lg:w-[440px] lg:shrink-0",
          )}
        >
          <div className="p-4 sm:p-6">{formSlot}</div>
        </aside>

        <button
          type="button"
          onClick={toggleFormPanel}
          className="sticky top-14 z-20 hidden h-10 w-6 shrink-0 items-center justify-center self-start border-y border-r border-border bg-card text-muted-foreground transition-colors hover:text-foreground lg:flex"
          aria-label={collapsed ? "Mostrar panel de entrada" : "Ocultar panel de entrada"}
        >
          {collapsed ? (
            <PanelLeftOpen className="size-4" aria-hidden="true" />
          ) : (
            <PanelLeftClose className="size-4" aria-hidden="true" />
          )}
        </button>

        <main className="min-w-0 flex-1 p-4 sm:p-6">{resultsSlot}</main>
      </div>
    </div>
  );
}
