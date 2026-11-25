
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
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
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

  const validResultType =
    result.result === 'real' ||
    result.result === 'ai-generated' ||
    result.result === 'analysis-complete';

  const validConfidence =
    result.confidence === undefined ||
    (
      typeof result.confidence === 'number' &&
      Number.isFinite(result.confidence) &&
      result.confidence >= 0 &&
      result.confidence <= 100
    );

  const requiresConfidence = result.result !== 'analysis-complete';

  return (
    validResultType &&
    validConfidence &&
    (!requiresConfidence || typeof result.confidence === 'number') &&
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

  const hasConfidence = typeof result.confidence === 'number';
  const isAnalysisOnly = result.result === 'analysis-complete';

  const handleSaveToHistory = async () => {
    if (isSaving || isSaved) return;

    if (isAnalysisOnly || result.confidence === undefined) {
      toast.error(
        'History currently supports scored authenticity results only.',
      );
      return;
    }

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

              <ResultBadge
                result={result.result}
                confidence={result.confidence}
              />
            </div>
          </CardHeader>

          <CardContent>
            <div className="flex flex-col items-center py-6">
              {hasConfidence ? (
                <>
                  <ConfidenceScore score={result.confidence!} size="lg" />
                  <p className="mt-3 max-w-2xl text-center text-xs text-muted-foreground">
                    Confidence scores are model outputs, not guarantees of
                    authenticity or authorship.
                  </p>
                </>
              ) : (
                <div className="rounded-lg border border-border bg-muted/30 px-6 py-5 text-center">
                  <CheckCircle2 className="mx-auto mb-2 h-8 w-8 text-primary" />
                  <p className="font-medium">Analysis completed</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    This module reports extracted features and observations.
                    It does not produce an authenticity confidence score.
                  </p>
                </div>
              )}

              <p className="mt-6 max-w-2xl text-center text-sm leading-relaxed text-muted-foreground">
                {result.explanation}
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
                      Structural and lexical measurements from the submitted source code.
                      These measurements do not establish code authorship.
                    </CardDescription>
                  </div>
                </div>
                <Badge variant="outline">
                  {result.codeBreakdown.language_hint ?? 'Auto-detected'}
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Metric
                  label="Lines of Code"
                  value={String(result.codeBreakdown.line_count ?? 0)}
                />
                <Metric
                  label="Total Tokens"
                  value={String(result.codeBreakdown.token_count ?? 0)}
                />
                <Metric
                  label="Unique Tokens"
                  value={String(result.codeBreakdown.unique_token_count ?? 0)}
                />
                <Metric
                  label="Token Diversity"
                  value={`${((result.codeBreakdown.token_diversity ?? 0) * 100).toFixed(1)}%`}
                />
                <Metric
                  label="Non-empty Lines"
                  value={String(result.codeBreakdown.nonempty_line_count ?? 0)}
                />
                <Metric
                  label="Comment Lines"
                  value={String(result.codeBreakdown.comment_line_count ?? 0)}
                />
                <Metric
                  label="Comment Ratio"
                  value={`${((result.codeBreakdown.comment_line_ratio ?? 0) * 100).toFixed(1)}%`}
                />
                <Metric
                  label="Average Line Length"
                  value={String(result.codeBreakdown.average_line_length ?? 0)}
                />
              </div>

              <div className="space-y-2">
                <h3 className="text-sm font-medium">Repeated Lines</h3>
                {Object.keys(result.codeBreakdown.repeated_lines ?? {}).length > 0 ? (
                  <ul className="space-y-2">
                    {Object.entries(result.codeBreakdown.repeated_lines ?? {}).map(
                      ([line, count]) => (
                        <li
                          key={line}
                          className="rounded-md border border-border bg-muted/20 p-3 text-sm"
                        >
                          <code className="break-all">{line}</code>
                          <span className="ml-2 text-muted-foreground">
                            Repeated {count} times
                          </span>
                        </li>
                      ),
                    )}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No repeated non-empty lines were found.
                  </p>
                )}
              </div>
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
                      Inspection of supported watermark metadata and content credential markers.
                    </CardDescription>
                  </div>
                </div>

                {result.watermarkBreakdown.watermarkDetected ? (
                  <Badge variant="destructive">
                    Watermark-Related Signal Found
                  </Badge>
                ) : result.watermarkBreakdown.c2paMarkersFound ? (
                  <Badge variant="secondary">
                    C2PA-Related Marker Found
                  </Badge>
                ) : (
                  <Badge variant="outline">
                    No Supported Markers Found
                  </Badge>
                )}
              </div>
            </CardHeader>

            <CardContent className="space-y-5">
              <div className="grid gap-3 md:grid-cols-2">
                <EvidenceItem
                  title="Digital Watermark"
                  description={
                    result.watermarkBreakdown.watermarkType ||
                    'No supported watermark-related metadata signals were found. Invisible watermarks are not checked.'
                  }
                  status={
                    result.watermarkBreakdown.watermarkDetected
                      ? 'found'
                      : 'not-found'
                  }
                />

                <EvidenceItem
                  title="C2PA and Content Credential Markers"
                  description={
                    result.watermarkBreakdown.c2paMarkersFound
                      ? 'C2PA-related marker strings were found. A valid manifest and signature have not been established.'
                      : 'No supported C2PA-related marker strings were found. This does not prove that content credentials are absent.'
                  }
                  status={
                    result.watermarkBreakdown.c2paMarkersFound
                      ? 'warning'
                      : 'not-found'
                  }
                />
              </div>

              {result.watermarkBreakdown.provenanceChain.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">
                    Reported Provenance Records
                  </h3>
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
                          <span className="text-xs text-muted-foreground">
                            {step.timestamp}
                          </span>
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
                This module inspects supported metadata and known marker strings only.
                It does not classify AI-generated or human-created content, verify
                cryptographic signatures, decode invisible watermarks, or establish
                file authenticity. Absence of supported markers does not prove that
                a file is original or unmodified.
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
          {!isAnalysisOnly && (
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
          )}

          <Button
            onClick={() => navigate('/detection')}
            variant="outline"
            className="flex-1"
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            New Analysis
          </Button>
        </div>

        {isAnalysisOnly && (
          <p className="text-center text-xs text-muted-foreground">
            History saving for analysis-only results will be enabled after
            the history database supports unscored analysis records.
          </p>
        )}
      </main>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-muted/30 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-lg font-semibold tabular-nums">
        {value}
      </p>
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
  const Icon =
    status === 'found' ? Check : status === 'warning' ? AlertTriangle : X;

  return (
    <div className="flex items-start gap-3 rounded-md border border-border bg-muted/20 p-3">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
      <div>
        <p className="text-sm font-medium">{title}</p>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          {description}
        </p>
      </div>
    </div>
  );
}
