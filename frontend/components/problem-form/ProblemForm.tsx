"use client";

import { useState } from "react";
import { FormProvider, useFieldArray, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Loader2, AlertCircle } from "lucide-react";
import { InlineMath } from "react-katex";
import "katex/dist/katex.min.css";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { VariableRow } from "@/components/problem-form/VariableRow";
import { ConstraintRow } from "@/components/problem-form/ConstraintRow";
import { ExampleLoader } from "@/components/problem-form/ExampleLoader";
import { buildLinearExpressionFromNumbers } from "@/lib/katex-helpers";
import { buildSolveRequest, solveProblem, ApiError } from "@/lib/api-client";
import { defaultConstraint, defaultProblem, defaultVariable, problemFormSchema, type ProblemFormValues } from "@/lib/schemas";
import { useProblemStore } from "@/store/problem-store";
import { useUiStore } from "@/store/ui-store";

export function ProblemForm() {
  const form = useForm<ProblemFormValues>({
    resolver: zodResolver(problemFormSchema),
    defaultValues: defaultProblem(),
    mode: "onBlur",
  });
  const { register, control, handleSubmit, watch, getValues, setValue } = form;

  const { fields: variableFields, append: appendVariable, remove: removeVariableField } = useFieldArray({
    control,
    name: "variables",
  });
  const { fields: constraintFields, append: appendConstraint, remove: removeConstraint } = useFieldArray({
    control,
    name: "constraints",
  });

  const setLoading = useProblemStore((s) => s.setLoading);
  const setResult = useProblemStore((s) => s.setResult);
  const setError = useProblemStore((s) => s.setError);
  const isLoading = useProblemStore((s) => s.isLoading);
  const submitError = useProblemStore((s) => s.error);
  const resetForNewResult = useUiStore((s) => s.resetForNewResult);

  const [dimensionError, setDimensionError] = useState<string | null>(null);

  const sense = watch("sense");
  const method = watch("method");
  const variableNames = watch("variables").map((v) => v.name);
  const objectiveCoeffs = watch("objectiveCoeffs");

  function addVariable() {
    const newIndex = getValues("variables").length;
    appendVariable(defaultVariable(newIndex));
    setValue("objectiveCoeffs", [...getValues("objectiveCoeffs"), 0]);
    getValues("constraints").forEach((c, idx) => {
      setValue(`constraints.${idx}.coeffs`, [...c.coeffs, 0]);
    });
  }

  function removeVariable(index: number) {
    if (getValues("variables").length <= 1) return;
    removeVariableField(index);
    setValue(
      "objectiveCoeffs",
      getValues("objectiveCoeffs").filter((_, i) => i !== index),
    );
    getValues("constraints").forEach((c, idx) => {
      setValue(
        `constraints.${idx}.coeffs`,
        c.coeffs.filter((_, i) => i !== index),
      );
    });
  }

  function addConstraint() {
    appendConstraint(defaultConstraint(getValues("variables").length));
  }

  async function onSubmit(values: ProblemFormValues) {
    setDimensionError(null);
    setLoading();
    resetForNewResult();
    try {
      const payload = buildSolveRequest(values);
      const response = await solveProblem(payload);
      setResult(values, response);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "No se pudo conectar con el servidor.";
      setError(message);
    }
  }

  return (
    <FormProvider {...form}>
      <form onSubmit={handleSubmit(onSubmit, () => setDimensionError("Revisá los campos marcados en rojo."))} className="flex flex-col gap-5">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ejemplos precargados</CardTitle>
          </CardHeader>
          <CardContent>
            <ExampleLoader />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Tipo de problema</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4 sm:flex-row">
            <div className="flex-1 space-y-1.5">
              <Label htmlFor="sense-select">Objetivo</Label>
              <Select value={sense} onValueChange={(v) => setValue("sense", v as "max" | "min")}>
                <SelectTrigger id="sense-select" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="max">Maximizar</SelectItem>
                  <SelectItem value="min">Minimizar</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 space-y-1.5">
              <Label htmlFor="method-select">Método</Label>
              <Select value={method} onValueChange={(v) => setValue("method", v as "two_phase" | "big_m")}>
                <SelectTrigger id="method-select" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="two_phase">Dos Fases</SelectItem>
                  <SelectItem value="big_m">Gran M</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Variables</CardTitle>
            <Button type="button" variant="outline" size="sm" onClick={addVariable}>
              <Plus className="size-4" aria-hidden="true" />
              Agregar variable
            </Button>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {variableFields.map((field, index) => (
              <VariableRow
                key={field.id}
                index={index}
                canRemove={variableFields.length > 1}
                onRemove={() => removeVariable(index)}
              />
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Función objetivo</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2 overflow-x-auto">
              <span className="font-mono text-sm text-muted-foreground">
                {sense === "max" ? "Max Z =" : "Min Z ="}
              </span>
              {variableFields.map((field, index) => (
                <div key={field.id} className="flex shrink-0 items-center gap-1">
                  <input
                    {...register(`objectiveCoeffs.${index}`, { valueAsNumber: true })}
                    type="number"
                    step="any"
                    aria-label={`Coeficiente de ${variableNames[index]} en la función objetivo`}
                    className="h-9 w-20 rounded-md border border-input bg-background px-2 font-mono text-sm tabular-nums shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                  <span className="font-mono text-sm text-muted-foreground">{variableNames[index]}</span>
                  {index < variableFields.length - 1 && <span className="text-muted-foreground">+</span>}
                </div>
              ))}
            </div>
            <Separator />
            <div className="overflow-x-auto rounded-md bg-muted/40 p-3">
              <InlineMath
                math={`\\text{${sense === "max" ? "Max" : "Min"} } Z = ${buildLinearExpressionFromNumbers(objectiveCoeffs, variableNames)}`}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Restricciones</CardTitle>
            <Button type="button" variant="outline" size="sm" onClick={addConstraint}>
              <Plus className="size-4" aria-hidden="true" />
              Agregar restricción
            </Button>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {constraintFields.map((field, index) => (
              <ConstraintRow
                key={field.id}
                index={index}
                variableNames={variableNames}
                canRemove={constraintFields.length > 1}
                onRemove={() => removeConstraint(index)}
              />
            ))}
          </CardContent>
        </Card>

        {dimensionError && (
          <Alert variant="destructive">
            <AlertCircle className="size-4" aria-hidden="true" />
            <AlertTitle>Formulario incompleto</AlertTitle>
            <AlertDescription>{dimensionError}</AlertDescription>
          </Alert>
        )}

        {submitError && (
          <Alert variant="destructive">
            <AlertCircle className="size-4" aria-hidden="true" />
            <AlertTitle>No se pudo resolver el problema</AlertTitle>
            <AlertDescription>{submitError}</AlertDescription>
          </Alert>
        )}

        <Button type="submit" size="lg" disabled={isLoading} className="min-h-11">
          {isLoading ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              Resolviendo…
            </>
          ) : (
            "Resolver"
          )}
        </Button>
      </form>
    </FormProvider>
  );
}
