"use client";

import { useState } from "react";
import type { RefObject } from "react";
import { toPng } from "html-to-image";
import { jsPDF } from "jspdf";
import { AlertCircle, FileImage, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

type ExportKind = "image" | "pdf" | null;

async function captureSnapshot(node: HTMLDivElement): Promise<string> {
  const background =
    getComputedStyle(document.documentElement).getPropertyValue("--background").trim() || "#ffffff";
  return toPng(node, { backgroundColor: background, pixelRatio: 2 });
}

function triggerDownload(href: string, filename: string) {
  const link = document.createElement("a");
  link.href = href;
  link.download = filename;
  link.click();
}

export function ExportButton({ targetRef }: { targetRef: RefObject<HTMLDivElement | null> }) {
  const [exporting, setExporting] = useState<ExportKind>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleExportImage() {
    if (!targetRef.current) return;
    setError(null);
    setExporting("image");
    try {
      const dataUrl = await captureSnapshot(targetRef.current);
      triggerDownload(dataUrl, "simplex-solver-resultado.png");
    } catch {
      setError("No se pudo generar la imagen. Probá de nuevo.");
    } finally {
      setExporting(null);
    }
  }

  async function handleExportPdf() {
    if (!targetRef.current) return;
    setError(null);
    setExporting("pdf");
    try {
      const dataUrl = await captureSnapshot(targetRef.current);
      const image = await new Promise<HTMLImageElement>((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error("No se pudo procesar la imagen."));
        img.src = dataUrl;
      });
      const pdf = new jsPDF({
        orientation: image.width > image.height ? "landscape" : "portrait",
        unit: "px",
        format: [image.width, image.height],
      });
      pdf.addImage(dataUrl, "PNG", 0, 0, image.width, image.height);
      pdf.save("simplex-solver-resultado.pdf");
    } catch {
      setError("No se pudo generar el PDF. Probá de nuevo.");
    } finally {
      setExporting(null);
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleExportImage}
          disabled={exporting !== null}
        >
          {exporting === "image" ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <FileImage className="size-4" aria-hidden="true" />
          )}
          Imagen
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleExportPdf}
          disabled={exporting !== null}
        >
          {exporting === "pdf" ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <FileText className="size-4" aria-hidden="true" />
          )}
          PDF
        </Button>
      </div>
      {error && (
        <p className="flex items-center gap-1.5 text-xs text-destructive">
          <AlertCircle className="size-3.5 shrink-0" aria-hidden="true" />
          {error}
        </p>
      )}
    </div>
  );
}
