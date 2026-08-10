"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { VarKind } from "@/lib/schemas";

const KIND_LABELS: Record<VarKind, string> = {
  continuous: "Continua",
  integer: "Entera",
  binary: "Binaria",
};

export function VariableTypeSelect({
  value,
  onChange,
  ariaLabel,
}: {
  value: VarKind;
  onChange: (value: VarKind) => void;
  ariaLabel: string;
}) {
  return (
    <Select value={value} onValueChange={(v) => onChange(v as VarKind)}>
      <SelectTrigger className="h-9 w-full min-w-28" aria-label={ariaLabel}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {(Object.entries(KIND_LABELS) as [VarKind, string][]).map(([value, label]) => (
          <SelectItem key={value} value={value}>
            {label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
