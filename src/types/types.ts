
export type MediaType =
  | "image"
  | "video"
  | "audio"
  | "text"
  | "code"
  | "watermark";

export type DetectionResultType =
  | "real"
  | "ai-generated"
  | "analysis-complete";

export interface CodeBreakdown {
  language_hint: string;
  character_count: number;
  line_count: number;
  nonempty_line_count: number;
  token_count: number;
  unique_token_count: number;
  token_diversity: number;
  comment_line_count: number;
  comment_line_ratio: number;
  average_line_length: number;
  repeated_lines: Record<string, number>;
}

export interface WatermarkBreakdown {
  watermarkDetected: boolean;
  watermarkType: string | null;
  c2paMarkersFound: boolean;
  c2paSignatureVerification: string;
  issuerOrg: string | null;
  tamperingVerification: string;
  provenanceChain: {
    action: string;
    actor: string;
    timestamp: string;
    software: string;
    valid: boolean;
  }[];
}

export interface DetectionResult {
  result: DetectionResultType;
  confidence?: number;
  explanation: string;
  indicators: string[];
  metadata?: Record<string, unknown>;
  codeBreakdown?: CodeBreakdown;
  watermarkBreakdown?: WatermarkBreakdown;
}

export interface HistoryRecord {
  id: string;
  media_type: MediaType;
  result: DetectionResultType;
  confidence: number;
  content_preview: string | null;
  file_name: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface DetectionRequest {
  mediaType: MediaType;
  content?: string;
  file?: File;
  url?: string;
  languageHint?: string;
  filename?: string;
}

export type BadgeVariant = "success" | "warning" | "destructive";

export function getBadgeVariant(confidence: number): BadgeVariant {
  if (confidence <= 30) return "success";
  if (confidence <= 69) return "warning";
  return "destructive";
}

export function getBadgeLabel(
  result: DetectionResultType,
  confidence: number,
): string {
  if (result === "analysis-complete") return "Analysis Completed";
  if (confidence <= 30) return "Low confidence";
  if (confidence <= 69) return "Inconclusive";

  return result === "ai-generated" ? "AI-generated" : "Authentic";
}