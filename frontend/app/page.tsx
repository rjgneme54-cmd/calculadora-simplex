import { AppShell } from "@/components/layout/AppShell";
import { ProblemForm } from "@/components/problem-form/ProblemForm";
import { ResultsPanel } from "@/components/results/ResultsPanel";

export default function Home() {
  return <AppShell formSlot={<ProblemForm />} resultsSlot={<ResultsPanel />} />;
}
