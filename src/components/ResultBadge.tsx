
import { Badge } from "@/components/ui/badge";
import type { DetectionResultType } from "@/types/types";
import { CheckCircle2, XCircle } from "lucide-react";

interface ResultBadgeProps {
  result: DetectionResultType;
  confidence: number;
  showIcon?: boolean;
}

export function ResultBadge({
  result,
  confidence,
  showIcon = true,
}: ResultBadgeProps) {
  const isAiGenerated = result === "ai-generated";

  const label = isAiGenerated
    ? "Likely AI-Generated"
    : "Likely Authentic";

  const variant = isAiGenerated ? "destructive" : "success";
  const Icon = isAiGenerated ? XCircle : CheckCircle2;

  const safeConfidence = Number.isFinite(confidence)
    ? Math.min(100, Math.max(0, confidence))
    : null;

  return (
    <Badge
      variant={variant}
      title={
        safeConfidence === null
          ? "Confidence unavailable"
          : `Model confidence: ${safeConfidence.toFixed(1)}%`
      }
      className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wide"
    >
      {showIcon && <Icon className="mr-1 h-4 w-4" />}
      {label}
    </Badge>
  );
}
