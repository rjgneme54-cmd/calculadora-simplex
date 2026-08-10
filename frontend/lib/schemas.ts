import { z } from "zod";

export const senseSchema = z.enum(["max", "min"]);
export const constraintOpSchema = z.enum(["<=", ">=", "="]);
export const varSignSchema = z.enum(["nonnegative", "free"]);
export const varKindSchema = z.enum(["continuous", "integer", "binary"]);
export const methodSchema = z.enum(["two_phase", "big_m"]);

export type Sense = z.infer<typeof senseSchema>;
export type ConstraintOp = z.infer<typeof constraintOpSchema>;
export type VarSign = z.infer<typeof varSignSchema>;
export type VarKind = z.infer<typeof varKindSchema>;
export type Method = z.infer<typeof methodSchema>;

const numberField = z
  .number({ message: "Debe ser un número" })
  .finite("Debe ser un número finito");

export const variableFormSchema = z.object({
  name: z
    .string()
    .min(1, "El nombre no puede estar vacío")
    .max(20, "Máximo 20 caracteres"),
  sign: varSignSchema,
  kind: varKindSchema,
});

export const constraintFormSchema = z.object({
  name: z.string().max(40, "Máximo 40 caracteres").optional(),
  coeffs: z.array(numberField),
  op: constraintOpSchema,
  rhs: numberField,
});

export const problemFormSchema = z
  .object({
    sense: senseSchema,
    method: methodSchema,
    variables: z.array(variableFormSchema).min(1, "Agregá al menos una variable"),
    objectiveCoeffs: z.array(numberField),
    constraints: z.array(constraintFormSchema).min(1, "Agregá al menos una restricción"),
  })
  .superRefine((data, ctx) => {
    const n = data.variables.length;

    if (data.objectiveCoeffs.length !== n) {
      ctx.addIssue({
        code: "custom",
        message: `La función objetivo debe tener ${n} coeficientes.`,
        path: ["objectiveCoeffs"],
      });
    }

    const names = data.variables.map((v) => v.name);
    if (new Set(names).size !== names.length) {
      ctx.addIssue({
        code: "custom",
        message: "Los nombres de las variables deben ser únicos.",
        path: ["variables"],
      });
    }

    data.constraints.forEach((c, idx) => {
      if (c.coeffs.length !== n) {
        ctx.addIssue({
          code: "custom",
          message: `La restricción #${idx + 1} debe tener ${n} coeficientes.`,
          path: ["constraints", idx, "coeffs"],
        });
      }
    });
  });

export type ProblemFormValues = z.infer<typeof problemFormSchema>;

export function defaultVariable(index: number): z.infer<typeof variableFormSchema> {
  return { name: `x${index + 1}`, sign: "nonnegative", kind: "continuous" };
}

export function defaultConstraint(numVariables: number): z.infer<typeof constraintFormSchema> {
  return { name: "", coeffs: Array(numVariables).fill(0), op: "<=", rhs: 0 };
}

export function defaultProblem(): ProblemFormValues {
  return {
    sense: "max",
    method: "two_phase",
    variables: [defaultVariable(0), defaultVariable(1)],
    objectiveCoeffs: [0, 0],
    constraints: [defaultConstraint(2)],
  };
}

interface RequestLikePayload {
  sense: Sense;
  method?: Method;
  objective: number[];
  variables?: { name?: string; sign?: string; kind?: string }[];
  constraints: { coeffs: number[]; op: string; rhs: number; name?: string }[];
}

export function requestPayloadToFormValues(payload: RequestLikePayload): ProblemFormValues {
  const n = payload.objective.length;
  const variables =
    payload.variables && payload.variables.length === n
      ? payload.variables.map((v, i) => ({
          name: v.name || `x${i + 1}`,
          sign: (v.sign as VarSign) ?? "nonnegative",
          kind: (v.kind as VarKind) ?? "continuous",
        }))
      : Array.from({ length: n }, (_, i) => defaultVariable(i));

  return {
    sense: payload.sense,
    method: payload.method ?? "two_phase",
    variables,
    objectiveCoeffs: payload.objective,
    constraints: payload.constraints.map((c) => ({
      name: c.name ?? "",
      coeffs: c.coeffs,
      op: c.op as ConstraintOp,
      rhs: c.rhs,
    })),
  };
}
