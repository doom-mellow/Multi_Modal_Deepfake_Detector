
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  Save,
  RotateCcw,
  Code2,
  Cpu,
  Fingerprint,
  AlertTriangle,
  Check,
  X,
  GitCommit,
} from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ConfidenceScore } from '@/components/ConfidenceScore';
import { ResultBadge } from '@/components/ResultBadge';

import { saveToHistory } from '@/services/historyService';
import type { DetectionResult, MediaType } from '@/types/types';

interface LocationState {
  mediaType: MediaType;
  result: DetectionResult;
  fileName?: string;
  contentPreview?: string;
}

function isValidResult(value: unknown): value is DetectionResult {
  if (!value || typeof value !== 'object') return false;

  const result = value as Partial<DetectionResult>;

  return (
    (result.result === 'real' || result.result === 'ai-generated') &&
    typeof result.confidence === 'number' &&
    Number.isFinite(result.confidence) &&
    result.confidence >= 0 &&
    result.confidence <= 100 &&
    typeof result.explanation === 'string' &&
    Array.isArray(result.indicators)
  );
}

function isMediaType(value: unknown): value is MediaType {
  return [
    'image',
    'video',
    'audio',
    'text',
    'code',
    'embedding',
    'watermark',
  ].includes(String(value));
}

export default function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  const state = location.state as LocationState | null;
  const validState =
    state &&
    isMediaType(state.mediaType) &&
    isValidResult(state.result);

  useEffect(() => {
    if (!validState) {
      toast.error('No valid analysis result was found.');
      navigate('/detection', { replace: true });
    }
  }, [validState, navigate]);

  if (!validState || !state) return null;

  const { mediaType, result, fileName, contentPreview } = state;

  const handleSaveToHistory = async () => {
    if (isSaving || isSaved) return;

    setIsSaving(true);

    try {
      const response = await saveToHistory(
        mediaType,
        result.result,
        result.confidence,
        contentPreview || null,
        fileName || null,
        result as unknown as Record<string, unknown>,
      );

      if (!response.success) {
        toast.error(response.error || 'Failed to save this result.');
        return;
      }

      setIsSaved(true);
      toast.success('Result saved to history.');
    } catch {
      toast.error('Failed to save this result.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors">
      <main className="container mx-auto max-w-4xl space-y-6 px-4 py-8">
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>Analysis Results</CardTitle>
                <CardDescription>
                  Findings for your submitted {mediaType} content.
                </CardDescription>
              </div>
              <ResultBadge result={result.result} confidence={result.confidence} />
            </div>
          </CardHeader>

          <CardContent>
            <div className="flex flex-col items-center py-6">
              <ConfidenceScore score={result.confidence} size="lg" />
              <p className="mt-6 max-w-2xl text-center text-sm leading-relaxed text-muted-foreground">
                {result.explanation}
              </p>
              <p className="mt-3 max-w-2xl text-center text-xs text-muted-foreground">
                Confidence scores are model outputs, not guarantees of authenticity or authorship.
              </p>
            </div>
          </CardContent>
        </Card>

        {result.codeBreakdown && (
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <Code2 className="h-5 w-5 text-primary" />
                  <div>
                    <CardTitle>Code Analysis</CardTitle>
                    <CardDescription>
                      Structural and stylistic indicators in the submitted source code.
                    </CardDescription>
                  </div>
                </div>
                <Badge variant="outline">{result.codeBreakdown.language}</Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Metric
                  label="Authorship Signal"
                  value={`${result.codeBreakdown.authorshipProbability}%`}
                />
                <Metric
                  label="AST Token Entropy"
                  value={`${result.codeBreakdown.astEntropy} / 1.0`}
                />
                <Metric
                  label="Token Perplexity"
                  value={String(result.codeBreakdown.tokenPerplexity)}
                />
                <Metric
                  label="Comment Ratio"
                  value={`${result.codeBreakdown.commentRatio}%`}
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Style consistency</span>
                  <span className="font-medium">
                    {result.codeBreakdown.styleConsistency}%
                  </span>
                </div>
                <Progress value={result.codeBreakdown.styleConsistency} />
              </div>

              {result.codeBreakdown.patternsFound.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">Observed Patterns</h3>
                  <ul className="space-y-2">
                    {result.codeBreakdown.patternsFound.map((pattern, index) => (
                      <li
                        key={`${pattern}-${index}`}
                        className="flex items-start gap-2 rounded-md border border-border bg-muted/20 p-3 text-sm"
                      >
                        <Code2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                        <span>{pattern}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {result.embeddingBreakdown && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <Cpu className="h-5 w-5 text-primary" />
                <div>
                  <CardTitle>Embedding Analysis</CardTitle>
                  <CardDescription>
                    Feature-space measurements from the selected representation model.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              <div className="grid gap-3 md:grid-cols-3">
                <Metric
                  label="Feature Dimension"
                  value={`${result.embeddingBreakdown.featureDimension}D`}
                />
                <Metric
                  label="Cosine Similarity"
                  value={`${(result.embeddingBreakdown.cosineSimilarity * 100).toFixed(1)}%`}
                />
                <Metric
                  label="Euclidean Distance"
                  value={String(result.embeddingBreakdown.euclideanDistance)}
                />
              </div>

              <div className="rounded-md border border-border p-3">
                <p className="text-xs text-muted-foreground">Representation Model</p>
                <p className="mt-1 break-words text-sm font-medium">
                  {result.embeddingBreakdown.modelArchitecture}
                </p>
              </div>

              {result.embeddingBreakdown.clusterDistributions.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-medium">Similarity by Reference Cluster</h3>
                  {result.embeddingBreakdown.clusterDistributions.map((cluster, index) => (
                    <div key={`${cluster.cluster}-${index}`} className="space-y-1">
                      <div className="flex justify-between gap-3 text-xs">
                        <span className="text-muted-foreground">{cluster.cluster}</span>
                        <span className="font-medium tabular-nums">
                          {(cluster.similarity * 100).toFixed(1)}%
                        </span>
                      </div>
                      <Progress value={cluster.similarity * 100} />
                    </div>
                  ))}
                </div>
              )}

              <p className="text-xs text-muted-foreground">
                Similarity to a reference cluster does not independently establish
                whether content was generated by a particular model or person.
              </p>
            </CardContent>
          </Card>
        )}

        {result.watermarkBreakdown && (
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <Fingerprint className="h-5 w-5 text-primary" />
                  <div>
                    <CardTitle>Watermark and Provenance Analysis</CardTitle>
                    <CardDescription>
                      Available watermark, content credential, and provenance findings.
                    </CardDescription>
                  </div>
                </div>

                {result.watermarkBreakdown.watermarkDetected ? (
                  <Badge variant="destructive">Watermark Signal Detected</Badge>
                ) : result.watermarkBreakdown.c2paSignatureValid ? (
                  <Badge variant="default">C2PA Signature Valid</Badge>
                ) : (
                  <Badge variant="outline">No Supported Signal Found</Badge>
                )}
              </div>
            </CardHeader>

            <CardContent className="space-y-5">
              <div className="grid gap-3 md:grid-cols-2">
                <EvidenceItem
                  title="Digital Watermark"
                  description={
                    result.watermarkBreakdown.watermarkType ||
                    (result.watermarkBreakdown.watermarkDetected
                      ? 'A watermark signal was reported.'
                      : 'No supported watermark signal was reported.')
                  }
                  status={result.watermarkBreakdown.watermarkDetected ? 'found' : 'not-found'}
                />

                <EvidenceItem
                  title="C2PA Content Credentials"
                  description={
                    result.watermarkBreakdown.c2paSignatureValid
                      ? `Signature reported as valid${result.watermarkBreakdown.issuerOrg ? ` for ${result.watermarkBreakdown.issuerOrg}` : ''}.`
                      : result.watermarkBreakdown.c2paManifestPresent
                        ? 'A manifest is present, but its signature was not validated.'
                        : 'No C2PA manifest was reported.'
                  }
                  status={
                    result.watermarkBreakdown.c2paSignatureValid
                      ? 'found'
                      : result.watermarkBreakdown.c2paManifestPresent
                        ? 'warning'
                        : 'not-found'
                  }
                />
              </div>

              {result.watermarkBreakdown.provenanceChain.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">Reported Provenance Records</h3>
                  <div className="rounded-md border border-border p-3">
                    {result.watermarkBreakdown.provenanceChain.map((step, index) => (
                      <div
                        key={`${step.action}-${step.timestamp}-${index}`}
                        className="flex flex-col gap-2 border-b border-border/60 py-3 last:border-0 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="flex items-start gap-2">
                          <GitCommit className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                          <div>
                            <p className="text-sm font-medium">{step.action}</p>
                            <p className="text-xs text-muted-foreground">{step.actor}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 pl-6 sm:pl-0">
                          <span className="text-xs text-muted-foreground">{step.timestamp}</span>
                          <Badge variant="outline">
                            {step.valid ? 'Verified' : 'Unsigned'}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-xs text-muted-foreground">
                Absence of a watermark or provenance manifest does not establish that
                content is original or unmodified.
              </p>
            </CardContent>
          </Card>
        )}

        {result.indicators.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Analysis Indicators</CardTitle>
              <CardDescription>
                Supporting observations returned by the analysis service.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {result.indicators.map((indicator, index) => (
                  <li key={`${indicator}-${index}`} className="flex items-start gap-3">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <span className="text-sm">{indicator}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {(contentPreview || fileName) && (
          <Card>
            <CardHeader>
              <CardTitle>Submitted Content</CardTitle>
            </CardHeader>
            <CardContent>
              {fileName && (
                <p className="mb-2 break-all text-sm text-muted-foreground">
                  File: {fileName}
                </p>
              )}
              {contentPreview && (
                <p className="whitespace-pre-wrap break-words text-sm text-muted-foreground">
                  {contentPreview}
                  {contentPreview.length >= 200 ? '…' : ''}
                </p>
              )}
            </CardContent>
          </Card>
        )}

        <div className="flex flex-col gap-3 sm:flex-row">
          <Button
            onClick={handleSaveToHistory}
            disabled={isSaving || isSaved}
            className="flex-1"
            variant={isSaved ? 'outline' : 'default'}
          >
            {isSaved ? (
              <>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Saved to History
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                {isSaving ? 'Saving…' : 'Save to History'}
              </>
            )}
          </Button>

          <Button
            onClick={() => navigate('/detection')}
            variant="outline"
            className="flex-1"
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            New Analysis
          </Button>
        </div>
      </main>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-muted/30 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-lg font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function EvidenceItem({
  title,
  description,
  status,
}: {
  title: string;
  description: string;
  status: 'found' | 'not-found' | 'warning';
}) {
  const Icon = status === 'found' ? Check : status === 'warning' ? AlertTriangle : X;

  return (
    <div className="flex items-start gap-3 rounded-md border border-border bg-muted/20 p-3">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
      <div>
        <p className="text-sm font-medium">{title}</p>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
