import { create } from "zustand";

export type ResultsTab = "resumen" | "iteraciones" | "grafico" | "sensibilidad" | "dual" | "entera";
export type DisplayMode = "fraction" | "decimal";

interface UiState {
  activeTab: ResultsTab;
  setActiveTab: (tab: ResultsTab) => void;
  selectedIteration: number;
  setSelectedIteration: (index: number) => void;
  displayMode: DisplayMode;
  toggleDisplayMode: () => void;
  isAutoPlaying: boolean;
  setAutoPlaying: (playing: boolean) => void;
  formPanelCollapsed: boolean;
  toggleFormPanel: () => void;
  resetForNewResult: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  activeTab: "resumen",
  setActiveTab: (tab) => set({ activeTab: tab }),
  selectedIteration: 0,
  setSelectedIteration: (index) => set({ selectedIteration: index }),
  displayMode: "fraction",
  toggleDisplayMode: () =>
    set((s) => ({ displayMode: s.displayMode === "fraction" ? "decimal" : "fraction" })),
  isAutoPlaying: false,
  setAutoPlaying: (playing) => set({ isAutoPlaying: playing }),
  formPanelCollapsed: false,
  toggleFormPanel: () => set((s) => ({ formPanelCollapsed: !s.formPanelCollapsed })),
  resetForNewResult: () => set({ activeTab: "resumen", selectedIteration: 0, isAutoPlaying: false }),
}));
