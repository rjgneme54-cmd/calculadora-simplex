import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProblemForm } from "@/components/problem-form/ProblemForm";

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return {
    ...actual,
    fetchExamples: vi.fn().mockResolvedValue([]),
    solveProblem: vi.fn(),
  };
});

describe("ProblemForm dynamic rows", () => {
  it("starts with 2 variables and 1 constraint by default", () => {
    render(<ProblemForm />);
    expect(screen.getByLabelText("Nombre de la variable 1")).toBeInTheDocument();
    expect(screen.getByLabelText("Nombre de la variable 2")).toBeInTheDocument();
    expect(screen.queryByLabelText("Nombre de la variable 3")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Coeficiente de x1 en la restricción 1")).toBeInTheDocument();
  });

  it("adding a variable adds a coefficient cell to the objective and every constraint", async () => {
    const user = userEvent.setup();
    render(<ProblemForm />);

    await user.click(screen.getByRole("button", { name: "Agregar variable" }));

    expect(screen.getByLabelText("Nombre de la variable 3")).toBeInTheDocument();
    expect(screen.getByLabelText("Coeficiente de x3 en la función objetivo")).toBeInTheDocument();
    expect(screen.getByLabelText("Coeficiente de x3 en la restricción 1")).toBeInTheDocument();
  });

  it("removing a variable removes its coefficient cell everywhere", async () => {
    const user = userEvent.setup();
    render(<ProblemForm />);

    await user.click(screen.getByRole("button", { name: "Quitar variable 2" }));

    expect(screen.queryByLabelText("Nombre de la variable 2")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Coeficiente de x2 en la función objetivo")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Coeficiente de x2 en la restricción 1")).not.toBeInTheDocument();
  });

  it("adding a constraint adds a row with one coefficient per current variable", async () => {
    const user = userEvent.setup();
    render(<ProblemForm />);

    await user.click(screen.getByRole("button", { name: "Agregar restricción" }));

    expect(screen.getByLabelText("Coeficiente de x1 en la restricción 2")).toBeInTheDocument();
    expect(screen.getByLabelText("Coeficiente de x2 en la restricción 2")).toBeInTheDocument();
  });

  it("disables removing the last remaining variable", async () => {
    const user = userEvent.setup();
    render(<ProblemForm />);

    await user.click(screen.getByRole("button", { name: "Quitar variable 2" }));

    expect(screen.getByRole("button", { name: "Quitar variable 1" })).toBeDisabled();
  });

  it("disables removing the last remaining constraint", () => {
    render(<ProblemForm />);
    expect(screen.getByRole("button", { name: "Quitar restricción 1" })).toBeDisabled();
  });
});
