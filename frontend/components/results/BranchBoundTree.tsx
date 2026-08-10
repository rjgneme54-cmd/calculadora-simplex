"use client";

import { Ban, CheckCircle2, GitBranch, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { formatFraction } from "@/lib/fraction-format";
import { useUiStore } from "@/store/ui-store";
import type { BranchAndBoundData, BranchBoundNode, BranchBoundOutcome } from "@/types/api";

const OUTCOME_CONFIG: Record<
  BranchBoundOutcome,
  { label: string; icon: typeof CheckCircle2; className: string }
> = {
  branched: {
    label: "Ramifica",
    icon: GitBranch,
    className: "border-primary/30 bg-primary/10 text-primary",
  },
  pruned_integer: {
    label: "Entera (candidata)",
    icon: CheckCircle2,
    className: "border-success/30 bg-success/10 text-success",
  },
  pruned_bound: {
    label: "Podado por cota",
    icon: Ban,
    className: "border-warning/30 bg-warning/10 text-warning",
  },
  pruned_infeasible: {
    label: "Infactible",
    icon: XCircle,
    className: "border-destructive/30 bg-destructive/10 text-destructive",
  },
};

function NodeCard({ node, isIncumbent }: { node: BranchBoundNode; isIncumbent: boolean }) {
  const displayMode = useUiStore((s) => s.displayMode);
  const config = OUTCOME_CONFIG[node.outcome];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "flex min-w-56 flex-col gap-1.5 rounded-md border p-2.5 text-sm",
        config.className,
        isIncumbent && "ring-2 ring-success",
      )}
    >
      <div className="flex flex-wrap items-center gap-1.5 font-medium">
        <Icon className="size-4 shrink-0" aria-hidden="true" />
        Nodo {node.id}
        {isIncumbent && (
          <Badge className="border-success/30 bg-success/10 text-xs text-success">
            Óptima entera
          </Badge>
        )}
      </div>
      {node.branch_description && (
        <p className="font-mono text-xs text-muted-foreground">{node.branch_description}</p>
      )}
      {node.status === "infeasible" ? (
        <p className="text-xs">Sin solución factible</p>
      ) : (
        <>
          <p className="font-mono text-xs tabular-nums">
            Z = {node.z ? formatFraction(node.z, displayMode) : "—"}
          </p>
          {node.solution && (
            <p className="font-mono text-xs tabular-nums text-muted-foreground">
              {Object.entries(node.solution)
                .map(([name, value]) => `${name}=${formatFraction(value, displayMode)}`)
                .join(", ")}
            </p>
          )}
        </>
      )}
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge variant="outline" className="w-fit text-xs">
          {config.label}
        </Badge>
        {node.branched_variable && (
          <span className="text-xs text-muted-foreground">sobre {node.branched_variable}</span>
        )}
      </div>
    </div>
  );
}

function TreeNode({
  node,
  childrenByParent,
  incumbentNodeId,
}: {
  node: BranchBoundNode;
  childrenByParent: Map<number, BranchBoundNode[]>;
  incumbentNodeId: number | null;
}) {
  const children = childrenByParent.get(node.id) ?? [];
  return (
    <div className="flex flex-col items-start">
      <NodeCard node={node} isIncumbent={node.id === incumbentNodeId} />
      {children.length > 0 && (
        <div className="mt-3 ml-6 flex flex-col gap-3 border-l-2 border-dashed border-border pl-6">
          {children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              childrenByParent={childrenByParent}
              incumbentNodeId={incumbentNodeId}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function BranchBoundTree({ data }: { data: BranchAndBoundData }) {
  const displayMode = useUiStore((s) => s.displayMode);
  const root = data.nodes.find((n) => n.parent_id === null);

  const childrenByParent = new Map<number, BranchBoundNode[]>();
  for (const node of data.nodes) {
    if (node.parent_id !== null) {
      const list = childrenByParent.get(node.parent_id) ?? [];
      list.push(node);
      childrenByParent.set(node.parent_id, list);
    }
  }

  const incumbentNode = data.nodes.find(
    (n) =>
      n.outcome === "pruned_integer" &&
      n.z !== null &&
      data.z !== null &&
      n.z.num === data.z.num &&
      n.z.den === data.z.den,
  );

  return (
    <div className="flex flex-col gap-4">
      <Card
        className={
          data.status === "optimal"
            ? "border-success/30 bg-success/10"
            : "border-destructive/30 bg-destructive/10"
        }
      >
        <CardContent className="flex items-start gap-3 pt-6">
          {data.status === "optimal" ? (
            <CheckCircle2 className="mt-0.5 size-6 shrink-0 text-success" aria-hidden="true" />
          ) : (
            <XCircle className="mt-0.5 size-6 shrink-0 text-destructive" aria-hidden="true" />
          )}
          <div className="flex flex-col gap-2">
            <p className="text-lg font-semibold">
              {data.status === "optimal" ? "Solución entera óptima" : "Sin solución entera"}
            </p>
            <p className="text-sm leading-relaxed text-foreground/90">{data.message}</p>
            {data.status === "optimal" && data.solution && data.z && (
              <div className="mt-1 flex flex-wrap items-center gap-4">
                <p className="font-mono text-2xl font-semibold tabular-nums text-primary">
                  Z = {formatFraction(data.z, displayMode)}
                </p>
                <p className="font-mono text-sm tabular-nums">
                  {Object.entries(data.solution)
                    .map(([name, value]) => `${name} = ${formatFraction(value, displayMode)}`)
                    .join(",  ")}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Árbol de Ramificación y Acotamiento</CardTitle>
        </CardHeader>
        <CardContent>
          {root ? (
            <div className="overflow-x-auto rounded-md border border-border p-4">
              <TreeNode
                node={root}
                childrenByParent={childrenByParent}
                incumbentNodeId={incumbentNode?.id ?? null}
              />
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No hay árbol para mostrar.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
