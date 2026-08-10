import type { ProblemFormValues } from "@/lib/schemas";
import type { ExampleProblem, SolveRequestPayload, SolveResponse } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function buildSolveRequest(values: ProblemFormValues): SolveRequestPayload {
  return {
    sense: values.sense,
    method: values.method,
    objective: values.objectiveCoeffs,
    variables: values.variables.map((v) => ({ name: v.name, sign: v.sign, kind: v.kind })),
    constraints: values.constraints.map((c) => ({
      coeffs: c.coeffs,
      op: c.op,
      rhs: c.rhs,
      name: c.name || undefined,
    })),
  };
}

export async function fetchExamples(): Promise<ExampleProblem[]> {
  const res = await fetch(`${API_BASE_URL}/api/examples`);
  if (!res.ok) {
    throw new ApiError("No se pudieron cargar los ejemplos precargados.", res.status);
  }
  return res.json();
}

export async function solveProblem(payload: SolveRequestPayload): Promise<SolveResponse> {
  const res = await fetch(`${API_BASE_URL}/api/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    let detail = "Ocurrió un error inesperado al resolver el problema.";
    try {
      const body = await res.json();
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // el cuerpo no era JSON; se conserva el mensaje genérico
    }
    throw new ApiError(detail, res.status);
  }

  return res.json();
}
