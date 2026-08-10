"use client";

import { useEffect, useState } from "react";
import { useFormContext } from "react-hook-form";
import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { fetchExamples } from "@/lib/api-client";
import { requestPayloadToFormValues, type ProblemFormValues } from "@/lib/schemas";
import type { ExampleProblem } from "@/types/api";

export function ExampleLoader() {
  const { reset } = useFormContext<ProblemFormValues>();
  const [examples, setExamples] = useState<ExampleProblem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    fetchExamples()
      .then((data) => {
        if (active) setExamples(data);
      })
      .catch(() => {
        if (active) setError(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return <p className="text-sm text-muted-foreground">Cargando ejemplos…</p>;
  }
  if (error || examples.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {examples.map((example) => (
        <Tooltip key={example.id}>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => reset(requestPayloadToFormValues(example.request))}
            >
              <FileText className="size-4" aria-hidden="true" />
              {example.title}
            </Button>
          </TooltipTrigger>
          <TooltipContent className="max-w-64">{example.description}</TooltipContent>
        </Tooltip>
      ))}
    </div>
  );
}
