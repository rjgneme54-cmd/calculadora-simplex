import { describe, expect, it } from "vitest";
import {
  defaultProblem,
  problemFormSchema,
  requestPayloadToFormValues,
} from "@/lib/schemas";

describe("defaultProblem", () => {
  it("produces a value that satisfies the schema out of the box", () => {
    const result = problemFormSchema.safeParse(defaultProblem());
    expect(result.success).toBe(true);
  });
});

describe("problemFormSchema", () => {
  const base = defaultProblem();

  it("rejects an objective whose length does not match the number of variables", () => {
    const invalid = { ...base, objectiveCoeffs: [1, 2, 3] };
    const result = problemFormSchema.safeParse(invalid);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues.some((i) => i.path.includes("objectiveCoeffs"))).toBe(true);
    }
  });

  it("rejects a constraint whose coefficient count does not match the number of variables", () => {
    const invalid = {
      ...base,
      constraints: [{ name: "", op: "<=" as const, rhs: 4, coeffs: [1, 2, 3] }],
    };
    const result = problemFormSchema.safeParse(invalid);
    expect(result.success).toBe(false);
  });

  it("rejects duplicate variable names", () => {
    const invalid = {
      ...base,
      variables: [
        { name: "x1", sign: "nonnegative" as const, kind: "continuous" as const },
        { name: "x1", sign: "nonnegative" as const, kind: "continuous" as const },
      ],
    };
    const result = problemFormSchema.safeParse(invalid);
    expect(result.success).toBe(false);
  });

  it("requires at least one variable and one constraint", () => {
    expect(problemFormSchema.safeParse({ ...base, variables: [] }).success).toBe(false);
    expect(problemFormSchema.safeParse({ ...base, constraints: [] }).success).toBe(false);
  });

  it("accepts a well-formed problem with mixed constraint types", () => {
    const valid = {
      sense: "min" as const,
      method: "two_phase" as const,
      variables: [
        { name: "x1", sign: "nonnegative" as const, kind: "continuous" as const },
        { name: "x2", sign: "nonnegative" as const, kind: "continuous" as const },
      ],
      objectiveCoeffs: [4, 1],
      constraints: [
        { name: "", op: "=" as const, rhs: 3, coeffs: [3, 1] },
        { name: "", op: ">=" as const, rhs: 6, coeffs: [4, 3] },
        { name: "", op: "<=" as const, rhs: 4, coeffs: [1, 2] },
      ],
    };
    expect(problemFormSchema.safeParse(valid).success).toBe(true);
  });
});

describe("requestPayloadToFormValues", () => {
  it("round-trips an example payload into form values with matching lengths", () => {
    const payload = {
      sense: "max" as const,
      method: "two_phase" as const,
      objective: [3, 5],
      variables: [{ name: "x1" }, { name: "x2" }],
      constraints: [{ coeffs: [1, 0], op: "<=", rhs: 4 }],
    };
    const values = requestPayloadToFormValues(payload);
    expect(values.variables).toHaveLength(2);
    expect(values.objectiveCoeffs).toEqual([3, 5]);
    expect(values.constraints[0].coeffs).toEqual([1, 0]);
    expect(problemFormSchema.safeParse(values).success).toBe(true);
  });

  it("falls back to generated names when variables are omitted", () => {
    const payload = {
      sense: "max" as const,
      objective: [1, 1, 1],
      constraints: [{ coeffs: [1, 1, 1], op: "<=", rhs: 10 }],
    };
    const values = requestPayloadToFormValues(payload);
    expect(values.variables.map((v) => v.name)).toEqual(["x1", "x2", "x3"]);
  });
});
