import type { ComponentType } from "react";

export interface Option {
  label: string;
  value: string;
  icon?: ComponentType<{ className?: string }>;
  withCount?: boolean;
}