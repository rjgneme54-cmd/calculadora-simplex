"use client";

import { useFormContext } from "react-hook-form";
import { Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { ConstraintOp, ProblemFormValues } from "@/lib/schemas";

export function ConstraintRow({
  index,
  variableNames,
  canRemove,
  onRemove,
}: {
  index: number;
  variableNames: string[];
  canRemove: boolean;
  onRemove: () => void;
}) {
  const { register, watch, setValue, formState } = useFormContext<ProblemFormValues>();
  const op = watch(`constraints.${index}.op`);
  const coeffsError = formState.errors.constraints?.[index]?.coeffs?.message;

  return (
    <div className="flex flex-col gap-2 rounded-md border border-border bg-card p-2">
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <span className="shrink-0 font-mono text-xs text-muted-foreground">
          R{index + 1}
        </span>
        {variableNames.map((name, varIdx) => (
          <div key={varIdx} className="flex shrink-0 items-center gap-1">
            <Input
              {...register(`constraints.${index}.coeffs.${varIdx}`, { valueAsNumber: true })}
              type="number"
              step="any"
              aria-label={`Coeficiente de ${name} en la restricción ${index + 1}`}
              className="h-9 w-20 font-mono tabular-nums"
            />
            <span className="font-mono text-sm text-muted-foreground">{name}</span>
            {varIdx < variableNames.length - 1 && <span className="text-muted-foreground">+</span>}
          </div>
        ))}

        <Select value={op} onValueChange={(v) => setValue(`constraints.${index}.op`, v as ConstraintOp)}>
          <SelectTrigger className="h-9 w-20 shrink-0 font-mono" aria-label={`Operador de la restricción ${index + 1}`}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="<=">≤</SelectItem>
            <SelectItem value=">=">≥</SelectItem>
            <SelectItem value="=">=</SelectItem>
          </SelectContent>
        </Select>

        <Input
          {...register(`constraints.${index}.rhs`, { valueAsNumber: true })}
          type="number"
          step="any"
          aria-label={`Lado derecho de la restricción ${index + 1}`}
          className="h-9 w-24 shrink-0 font-mono tabular-nums"
        />

        <Input
          {...register(`constraints.${index}.name`)}
          placeholder="Nombre (opcional)"
          aria-label={`Nombre de la restricción ${index + 1}`}
          className="h-9 w-40 shrink-0"
        />

        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-11 shrink-0 text-muted-foreground hover:text-destructive"
          onClick={onRemove}
          disabled={!canRemove}
          aria-label={`Quitar restricción ${index + 1}`}
        >
          <Trash2 className="size-4" aria-hidden="true" />
        </Button>
      </div>
      {coeffsError && <p className="text-xs text-destructive">{coeffsError}</p>}
    </div>
  );
}
