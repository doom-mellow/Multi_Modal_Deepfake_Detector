import { Badge } from "@/components/ui/badge";
import type { DetectionResultType } from "@/types/types";
import { CheckCircle2, XCircle, Info } from "lucide-react";

interface ResultBadgeProps {
  result: DetectionResultType;
  confidence?: number;
  showIcon?: boolean;
}

export function ResultBadge({
  result,
  confidence,
  showIcon = true,
}: ResultBadgeProps) {
  const isAnalysisComplete = result === "analysis-complete";
  const isAiGenerated = result === "ai-generated";

  const label = isAnalysisComplete
    ? "Analysis Completed"
    : isAiGenerated
      ? "Likely AI-Generated"
      : "Likely Authentic";

  const variant = isAnalysisComplete
    ? "secondary"
    : isAiGenerated
      ? "destructive"
      : "success";

  const Icon = isAnalysisComplete
    ? Info
    : isAiGenerated
      ? XCircle
      : CheckCircle2;

  const safeConfidence =
    typeof confidence === "number" && Number.isFinite(confidence)
      ? Math.min(100, Math.max(0, confidence))
      : null;

  return (
    <Badge
      variant={variant}
      title={
        safeConfidence === null
          ? "No authenticity confidence score was produced"
          : `Model confidence: ${safeConfidence.toFixed(1)}%`
      }
      className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wide"
    >
      {showIcon && <Icon className="mr-1 h-4 w-4" />}
      {label}
    </Badge>
  );
}