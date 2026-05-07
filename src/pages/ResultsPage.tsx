import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ConfidenceScore } from '@/components/ConfidenceScore';
import { ResultBadge } from '@/components/ResultBadge';
import { Shield, ArrowLeft, Save, RotateCcw, CheckCircle2 } from 'lucide-react';
import { saveToHistory } from '@/services/historyService';
import type { DetectionResult, MediaType } from '@/types/types';
import { toast } from 'sonner';

interface LocationState {
  mediaType: MediaType;
  result: DetectionResult;
  fileName?: string;
  contentPreview?: string;
}

export default function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  const state = location.state as LocationState | null;

  useEffect(() => {
    if (!state) {
      navigate('/detection');
    }
  }, [state, navigate]);

  if (!state) {
    return null;
  }

  const { mediaType, result, fileName, contentPreview } = state;

  const handleSaveToHistory = async () => {
    setIsSaving(true);
    try {
      const response = await saveToHistory(
        mediaType,
        result.result,
        result.confidence,
        contentPreview || null,
        fileName || null
      );

      if (response.success) {
        setIsSaved(true);
        toast.success('Result saved to history');
      } else {
        toast.error(response.error || 'Failed to save to history');
      }
    } catch (error) {
      toast.error('Failed to save to history');
    } finally {
      setIsSaving(false);
    }
  };

  const handleNewDetection = () => {
    navigate('/detection');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-primary" />
              <h1 className="text-2xl font-bold text-foreground">Detection Results</h1>
            </div>
            <Button onClick={() => navigate('/')} variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Confidence Score Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Analysis Complete</CardTitle>
                  <CardDescription>
                    AI detection analysis results for {mediaType} content
                  </CardDescription>
                </div>
                <ResultBadge result={result.result} confidence={result.confidence} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center py-8">
                <ConfidenceScore score={result.confidence} size="lg" />
                <p className="mt-6 text-center text-muted-foreground max-w-2xl">
                  {result.explanation}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Detection Indicators */}
          {result.indicators.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Detection Indicators</CardTitle>
                <CardDescription>
                  Key findings from the forensic analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {result.indicators.map((indicator, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-foreground">{indicator}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Content Preview */}
          {contentPreview && (
            <Card>
              <CardHeader>
                <CardTitle>Content Preview</CardTitle>
              </CardHeader>
              <CardContent>
                {mediaType === 'text' ? (
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {contentPreview}
                    {contentPreview.length >= 200 && '...'}
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    File: {contentPreview}
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4">
            <Button
              onClick={handleSaveToHistory}
              disabled={isSaving || isSaved}
              className="flex-1"
              variant={isSaved ? 'outline' : 'default'}
            >
              {isSaved ? (
                <>
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Saved to History
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save to History
                </>
              )}
            </Button>
            <Button
              onClick={handleNewDetection}
              variant="outline"
              className="flex-1"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              New Detection
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
