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
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-border/80 bg-card/90 px-4 shadow-elevated backdrop-blur-md supports-[backdrop-filter]:bg-card/70 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="relative flex size-10 shrink-0 items-center justify-center">
            <span
              className="animate-pulse-ring absolute inset-0 rounded-xl bg-[color-mix(in_oklch,var(--primary-vivid)_55%,transparent)] blur-md"
              aria-hidden="true"
            />
            <div className="bg-gradient-primary shadow-glow-primary relative flex size-10 items-center justify-center rounded-xl text-primary-foreground">
              <Calculator className="size-5" aria-hidden="true" />
            </div>
          </div>
          <div className="leading-tight">
            <div className="flex items-center gap-2">
              <p className="text-base font-bold tracking-tight text-foreground">Simplex Solver</p>
              <svg width="26" height="14" viewBox="0 0 26 14" className="hidden opacity-80 sm:block" aria-hidden="true">
                <line x1="3" y1="11" x2="13" y2="3" stroke="var(--secondary)" strokeWidth="1.5" />
                <line x1="13" y1="3" x2="23" y2="9" stroke="var(--secondary)" strokeWidth="1.5" />
                <line x1="3" y1="11" x2="23" y2="9" stroke="var(--border)" strokeWidth="1.5" strokeDasharray="2 2" />
                <circle cx="3" cy="11" r="2" fill="var(--accent)" />
                <circle cx="23" cy="9" r="2" fill="var(--secondary)" />
                <circle cx="13" cy="3" r="2.5" fill="var(--primary-vivid)" />
              </svg>
            </div>
            <p className="hidden text-xs font-medium text-muted-foreground sm:block">
              Programación Lineal · Método Simplex y Gráfico
            </p>
          </div>
        </div>
        <ThemeToggle />
      </header>

      <div className="flex flex-1 flex-col lg:flex-row">
        <aside
          className={cn(
            "border-border/80 bg-card/60 lg:sticky lg:top-16 lg:h-[calc(100vh-4rem)] lg:overflow-y-auto lg:border-r",
            collapsed ? "lg:hidden" : "lg:w-[440px] lg:shrink-0",
          )}
        >
          <div className="p-4 sm:p-6">{formSlot}</div>
        </aside>

        <button
          type="button"
          onClick={toggleFormPanel}
          className="sticky top-16 z-20 hidden h-10 w-6 shrink-0 items-center justify-center self-start border-y border-r border-border/80 bg-card text-muted-foreground transition-colors hover:bg-muted hover:text-foreground lg:flex"
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
