export type MediaType =
  | "image"
  | "video"
  | "audio"
  | "text"
  | "code"
  | "embedding"
  | "watermark";

export type DetectionResultType = "real" | "ai-generated";

export interface CodeBreakdown {
  language: string;
  authorshipProbability: number;
  astEntropy: number;
  tokenPerplexity: number;
  syntheticBoilerplateDetected: boolean;
  patternsFound: string[];
  styleConsistency: number;
  commentRatio: number;
}

export interface EmbeddingBreakdown {
  modelArchitecture: string;
  cosineSimilarity: number;
  nearestCluster: string;
  euclideanDistance: number;
  outlierScore: number;
  isLatentOutlier: boolean;
  featureDimension: number;
  clusterDistributions: {
    cluster: string;
    similarity: number;
    color: string;
  }[];
}

export interface WatermarkBreakdown {
  watermarkDetected: boolean;
  watermarkType: string | null;
  confidenceLevel: number;
  c2paManifestPresent: boolean;
  c2paSignatureValid: boolean;
  issuerOrg: string | null;
  tamperingDetected: boolean;
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
  confidence: number;
  explanation: string;
  indicators: string[];
  codeBreakdown?: CodeBreakdown;
  embeddingBreakdown?: EmbeddingBreakdown;
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
  embeddingModel?: string;
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
  if (confidence <= 30) return "Low confidence";
  if (confidence <= 69) return "Inconclusive";
  return result === "ai-generated" ? "AI-generated" : "Authentic";
}