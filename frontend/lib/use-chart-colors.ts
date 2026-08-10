"use client";

import { useEffect, useState } from "react";

export interface ChartColors {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  destructive: string;
  border: string;
  foreground: string;
  mutedForeground: string;
  card: string;
}

const CSS_VAR_NAME: Record<keyof ChartColors, string> = {
  primary: "--primary",
  secondary: "--secondary",
  success: "--success",
  warning: "--warning",
  destructive: "--destructive",
  border: "--border",
  foreground: "--foreground",
  mutedForeground: "--muted-foreground",
  card: "--card",
};

function defaultColors(): ChartColors {
  return {
    primary: "#1e40af",
    secondary: "#3b82f6",
    success: "#059669",
    warning: "#d97706",
    destructive: "#dc2626",
    border: "#e2e8f0",
    foreground: "#0f172a",
    mutedForeground: "#64748b",
    card: "#ffffff",
  };
}

function readColors(): ChartColors {
  if (typeof window === "undefined") return defaultColors();
  const styles = getComputedStyle(document.documentElement);
  const fallback = defaultColors();
  const next = {} as ChartColors;
  (Object.keys(CSS_VAR_NAME) as (keyof ChartColors)[]).forEach((key) => {
    const value = styles.getPropertyValue(CSS_VAR_NAME[key]).trim();
    next[key] = value || fallback[key];
  });
  return next;
}

/**
 * Reads theme colors from the resolved CSS custom properties instead of tracking
 * next-themes' resolvedTheme directly: next-themes toggles the `dark` class on
 * <html> from its own effect, and effects run children-first within a commit, so
 * a child effect keyed on resolvedTheme would read the *previous* class value.
 * Observing the class attribute mutation itself sidesteps that ordering race.
 */
export function useChartColors(): ChartColors {
  const [colors, setColors] = useState<ChartColors>(readColors);

  useEffect(() => {
    const update = () => setColors(readColors());
    update();
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  return colors;
}
