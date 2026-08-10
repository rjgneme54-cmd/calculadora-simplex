import { create } from "zustand";
import type { ProblemFormValues } from "@/lib/schemas";
import type { SolveResponse } from "@/types/api";

interface ProblemState {
  lastSubmittedProblem: ProblemFormValues | null;
  result: SolveResponse | null;
  isLoading: boolean;
  error: string | null;
  setLoading: () => void;
  setResult: (problem: ProblemFormValues, result: SolveResponse) => void;
  setError: (message: string) => void;
  reset: () => void;
}

export const useProblemStore = create<ProblemState>((set) => ({
  lastSubmittedProblem: null,
  result: null,
  isLoading: false,
  error: null,
  setLoading: () => set({ isLoading: true, error: null }),
  setResult: (problem, result) =>
    set({ lastSubmittedProblem: problem, result, isLoading: false, error: null }),
  setError: (message) => set({ isLoading: false, error: message }),
  reset: () => set({ lastSubmittedProblem: null, result: null, isLoading: false, error: null }),
}));
