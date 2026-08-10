"use client";

import { useFormContext } from "react-hook-form";
import { Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { VariableTypeSelect } from "@/components/problem-form/VariableTypeSelect";
import type { ProblemFormValues, VarKind, VarSign } from "@/lib/schemas";

export function VariableRow({
  index,
  canRemove,
  onRemove,
}: {
  index: number;
  canRemove: boolean;
  onRemove: () => void;
}) {
  const { register, watch, setValue, formState } = useFormContext<ProblemFormValues>();
  const sign = watch(`variables.${index}.sign`);
  const kind = watch(`variables.${index}.kind`);
  const nameError = formState.errors.variables?.[index]?.name?.message;

  return (
    <div className="flex flex-wrap items-start gap-2 rounded-md border border-border bg-card p-2 sm:flex-nowrap sm:items-center">
      <div className="min-w-24 flex-1 sm:flex-none sm:basis-24">
        <Input
          {...register(`variables.${index}.name`)}
          aria-label={`Nombre de la variable ${index + 1}`}
          aria-invalid={!!nameError}
          className="h-9 font-mono"
        />
        {nameError && <p className="mt-1 text-xs text-destructive">{nameError}</p>}
      </div>

      <Select value={sign} onValueChange={(v) => setValue(`variables.${index}.sign`, v as VarSign)}>
        <SelectTrigger className="h-9 w-full min-w-32 sm:w-36" aria-label={`Signo de la variable ${index + 1}`}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="nonnegative">No negativa (≥ 0)</SelectItem>
          <SelectItem value="free">Libre (sin restricción)</SelectItem>
        </SelectContent>
      </Select>

      <VariableTypeSelect
        value={kind as VarKind}
        onChange={(v) => setValue(`variables.${index}.kind`, v)}
        ariaLabel={`Tipo de la variable ${index + 1}`}
      />

      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="ml-auto size-11 shrink-0 text-muted-foreground hover:text-destructive"
        onClick={onRemove}
        disabled={!canRemove}
        aria-label={`Quitar variable ${index + 1}`}
      >
        <Trash2 className="size-4" aria-hidden="true" />
      </Button>
    </div>
  );
}
