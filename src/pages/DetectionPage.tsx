
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
  Code2,
  Fingerprint,
  Image as ImageIcon,
  Video,
  Mic,
  FileText,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { FileUploadZone } from '@/components/FileUploadZone';
import { ProcessingIndicator } from '@/components/ProcessingIndicator';

import {
  performDetection,
  validateFile,
} from '@/services/detectionService';

import type { DetectionRequest, MediaType } from '@/types/types';

interface ResultMetadata {
  fileName?: string | null;
  contentPreview?: string | null;
}

const MAX_TEXT_LENGTH = 10000;

export default function DetectionPage() {
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<MediaType>('image');
  const [isProcessing, setIsProcessing] = useState(false);

  const [imageFile, setImageFile] = useState<File | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);

  const [textContent, setTextContent] = useState('');
  const [textFile, setTextFile] = useState<File | null>(null);

  const [codeContent, setCodeContent] = useState('');
  const [codeFile, setCodeFile] = useState<File | null>(null);
  const [languageHint, setLanguageHint] = useState('auto');

  const [watermarkFile, setWatermarkFile] = useState<File | null>(null);

  const runAnalysis = async (
    request: DetectionRequest,
    metadata: ResultMetadata = {},
  ) => {
    if (isProcessing) return;

    setIsProcessing(true);

    try {
      const result = await performDetection(request);

      navigate('/results', {
        state: {
          mediaType: request.mediaType,
          result,
          fileName:
            metadata.fileName ?? request.file?.name ?? null,
          contentPreview: metadata.contentPreview ?? null,
        },
      });
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : 'Analysis failed. Please try again.',
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const validateUploadedFile = (
    file: File,
    mediaType: 'image' | 'video' | 'audio',
  ) => {
    const validation = validateFile(file, mediaType);

    if (!validation.valid) {
      toast.error(
        validation.error || 'The selected file is not supported.',
      );
      return false;
    }

    return true;
  };

  const handleImageDetection = () => {
    if (!imageFile) {
      toast.error('Please upload an image.');
      return;
    }

    if (!validateUploadedFile(imageFile, 'image')) return;

    void runAnalysis(
      { mediaType: 'image', file: imageFile },
      {
        fileName: imageFile.name,
        contentPreview: imageFile.name,
      },
    );
  };

  const handleVideoDetection = () => {
    if (!videoFile) {
      toast.error('Please upload a video.');
      return;
    }

    if (!validateUploadedFile(videoFile, 'video')) return;

    void runAnalysis(
      { mediaType: 'video', file: videoFile },
      {
        fileName: videoFile.name,
        contentPreview: videoFile.name,
      },
    );
  };

  const handleAudioDetection = () => {
    if (!audioFile) {
      toast.error('Please upload an audio file.');
      return;
    }

    if (!validateUploadedFile(audioFile, 'audio')) return;

    void runAnalysis(
      { mediaType: 'audio', file: audioFile },
      {
        fileName: audioFile.name,
        contentPreview: audioFile.name,
      },
    );
  };

  // Read an uploaded TXT file into the text editor.
  const handleTextFileSelect = (file: File) => {
    if (file.size > 100 * 1024 * 1024) {
      toast.error('Text file exceeds the maximum upload size of 100 MB.');
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      if (typeof reader.result !== 'string') {
        toast.error('Could not read the selected text file.');
        return;
      }

      const content = reader.result;

      if (!content.trim()) {
        toast.error('The selected text file is empty.');
        return;
      }

      if (content.length > MAX_TEXT_LENGTH) {
        setTextContent(content.slice(0, MAX_TEXT_LENGTH));
        setTextFile(file);

        toast.warning(
          `Only the first ${MAX_TEXT_LENGTH.toLocaleString()} characters were loaded.`,
        );
        return;
      }

      setTextContent(content);
      setTextFile(file);

      toast.success(`Loaded ${file.name}`);
    };

    reader.onerror = () => {
      toast.error('Could not read the selected text file.');
    };

    reader.readAsText(file);
  };

  // Submit both the text and original filename.
  const handleTextDetection = () => {
    const content = textContent.trim();

    if (!content) {
      toast.error('Please upload a text file or enter text to analyze.');
      return;
    }

    if (content.length > MAX_TEXT_LENGTH) {
      toast.error('Text cannot exceed 10,000 characters.');
      return;
    }

    void runAnalysis(
      {
        mediaType: 'text',
        content,
        filename: textFile?.name ?? undefined,
      },
      {
        fileName: textFile?.name ?? null,
        contentPreview: content.slice(0, 200),
      },
    );
  };

  const handleCodeFileSelect = (file: File | null) => {
    setCodeFile(file);

    if (!file) {
      setCodeContent('');
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      if (typeof reader.result !== 'string') {
        toast.error('Could not read the selected source file.');
        setCodeFile(null);
        return;
      }

      setCodeContent(reader.result);
      toast.success(`Loaded ${file.name}`);
    };

    reader.onerror = () => {
      toast.error('Could not read the selected source file.');
      setCodeFile(null);
    };

    reader.readAsText(file);
  };

  const handleCodeDetection = () => {
    const content = codeContent.trim();

    if (!content) {
      toast.error('Upload a source file or paste source code.');
      return;
    }

    void runAnalysis(
      {
        mediaType: 'code',
        content,
        file: codeFile || undefined,
        languageHint:
          languageHint !== 'auto' ? languageHint : undefined,
      },
      {
        fileName: codeFile?.name ?? 'source_snippet',
        contentPreview: content.slice(0, 200),
      },
    );
  };

  const handleWatermarkDetection = () => {
    if (!watermarkFile) {
      toast.error('Please upload an asset.');
      return;
    }

    void runAnalysis(
      { mediaType: 'watermark', file: watermarkFile },
      {
        fileName: watermarkFile.name,
        contentPreview: watermarkFile.name,
      },
    );
  };

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors">
      <main className="container mx-auto px-4 py-8">
        <div className="mx-auto max-w-4xl">
          <Card>
            <CardHeader>
              <CardTitle>Content Analysis</CardTitle>
              <CardDescription>
                Choose the type of content you want to examine. Available
                findings depend on the analysis tools configured for each
                category.
              </CardDescription>
            </CardHeader>

            <CardContent>
              {isProcessing ? (
                <ProcessingIndicator message="Analyzing submitted content..." />
              ) : (
                <Tabs
                  value={activeTab}
                  onValueChange={(value) =>
                    setActiveTab(value as MediaType)
                  }
                >
                  <TabsList className="grid h-auto w-full grid-cols-2 gap-1 bg-muted/60 p-1 sm:grid-cols-4 md:grid-cols-7">
                    <TabsTrigger value="image" className="flex items-center gap-1.5 py-2">
                      <ImageIcon className="h-3.5 w-3.5" />
                      Image
                    </TabsTrigger>

                    <TabsTrigger value="video" className="flex items-center gap-1.5 py-2">
                      <Video className="h-3.5 w-3.5" />
                      Video
                    </TabsTrigger>

                    <TabsTrigger value="audio" className="flex items-center gap-1.5 py-2">
                      <Mic className="h-3.5 w-3.5" />
                      Audio
                    </TabsTrigger>

                    <TabsTrigger value="text" className="flex items-center gap-1.5 py-2">
                      <FileText className="h-3.5 w-3.5" />
                      Text
                    </TabsTrigger>

                    <TabsTrigger value="code" className="flex items-center gap-1.5 py-2">
                      <Code2 className="h-3.5 w-3.5" />
                      Code
                    </TabsTrigger>

                    <TabsTrigger value="watermark" className="flex items-center gap-1.5 py-2">
                      <Fingerprint className="h-3.5 w-3.5" />
                      Watermark
                    </TabsTrigger>
                  </TabsList>

                  {/* IMAGE */}
                  <TabsContent value="image" className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <Label>Upload image</Label>
                      <FileUploadZone
                        onFileSelect={setImageFile}
                        accept="image/jpeg,image/png,image/gif,image/webp"
                      />
                      <p className="text-xs text-muted-foreground">
                        Supported formats: JPG, PNG, GIF, WebP.
                      </p>
                    </div>

                    <Button
                      className="w-full"
                      onClick={handleImageDetection}
                      disabled={!imageFile}
                    >
                      Analyze Image
                    </Button>
                  </TabsContent>

                  {/* VIDEO */}
                  <TabsContent value="video" className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <Label>Upload video</Label>
                      <FileUploadZone
                        onFileSelect={setVideoFile}
                        accept="video/mp4,video/avi,video/quicktime,video/webm"
                      />
                      <p className="text-xs text-muted-foreground">
                        Supported formats: MP4, AVI, MOV, WebM.
                      </p>
                    </div>

                    <Button
                      className="w-full"
                      onClick={handleVideoDetection}
                      disabled={!videoFile}
                    >
                      Analyze Video
                    </Button>
                  </TabsContent>

                  {/* AUDIO */}
                  <TabsContent value="audio" className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <Label>Upload audio</Label>
                      <FileUploadZone
                        onFileSelect={setAudioFile}
                        accept=".wav,.mp3,audio/wav,audio/mpeg"
                      />
                      <p className="text-xs text-muted-foreground">
                        Supported format: WAV (PCM).
                      </p>
                    </div>

                    <Button
                      className="w-full"
                      onClick={handleAudioDetection}
                      disabled={!audioFile}
                    >
                      Analyze Audio
                    </Button>
                  </TabsContent>

                  {/* TEXT */}
                  <TabsContent value="text" className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <Label className="text-base font-semibold">
                        Upload a text file
                      </Label>

                      <FileUploadZone
                        onFileSelect={handleTextFileSelect}
                        accept=".txt,text/plain"
                      />

                      <p className="text-xs text-muted-foreground">
                        Supported format: TXT. Maximum file size: 100 MB.
                      </p>
                    </div>

                    <div className="text-center text-xs text-muted-foreground">
                      OR PASTE TEXT
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="text-content">Text content</Label>
                      <Textarea
                        id="text-content"
                        placeholder="Upload a TXT file or paste/type the text you want to analyze..."
                        value={textContent}
                        onChange={(event) => {
                          setTextContent(event.target.value);
                          setTextFile(null);
                        }}
                        rows={10}
                        maxLength={MAX_TEXT_LENGTH}
                      />

                      <p className="text-right text-xs text-muted-foreground">
                        {textContent.length.toLocaleString()} / 10,000 characters
                      </p>
                    </div>

                    <Button
                      className="w-full"
                      onClick={handleTextDetection}
                      disabled={!textContent.trim()}
                    >
                      Analyze Text
                    </Button>
                  </TabsContent>

                  {/* CODE */}
                  <TabsContent value="code" className="space-y-4 pt-4">
                    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                      <div>
                        <Label className="text-base font-semibold">
                          Source code
                        </Label>
                        <p className="text-xs text-muted-foreground">
                          Upload a source file or paste code below.
                        </p>
                      </div>

                      <div className="w-full sm:w-48">
                        <Label
                          htmlFor="language-hint"
                          className="mb-1 block text-xs text-muted-foreground"
                        >
                          Language
                        </Label>

                        <select
                          id="language-hint"
                          value={languageHint}
                          onChange={(event) =>
                            setLanguageHint(event.target.value)
                          }
                          className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                        >
                          <option value="auto">Auto-detect</option>
                          <option value="python">Python</option>
                          <option value="typescript">TypeScript</option>
                          <option value="javascript">JavaScript</option>
                          <option value="cpp">C / C++</option>
                          <option value="java">Java</option>
                          <option value="go">Go</option>
                          <option value="rust">Rust</option>
                        </select>
                      </div>
                    </div>

                    <FileUploadZone
                      onFileSelect={handleCodeFileSelect}
                      accept=".py,.js,.ts,.tsx,.jsx,.java,.cpp,.c,.go,.rs,.rb,.php,.cs,.txt"
                    />

                    <div className="text-center text-xs text-muted-foreground">
                      OR PASTE SOURCE CODE
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="code-content">Code content</Label>
                      <Textarea
                        id="code-content"
                        placeholder="Paste source code here..."
                        value={codeContent}
                        onChange={(event) => {
                          setCodeContent(event.target.value);
                          setCodeFile(null);
                        }}
                        rows={12}
                        className="font-mono text-xs leading-relaxed"
                      />

                      <p className="text-right text-xs text-muted-foreground">
                        {codeContent.split('\n').length} lines · {codeContent.length} characters
                      </p>
                    </div>

                    <Button
                      className="w-full"
                      onClick={handleCodeDetection}
                      disabled={!codeContent.trim()}
                    >
                      Analyze Code
                    </Button>
                  </TabsContent>

                  {/* WATERMARK */}
                  <TabsContent value="watermark" className="space-y-4 pt-4">
                    <div className="rounded-md border border-border bg-muted/30 p-3">
                      <div className="mb-1 flex items-center gap-2">
                        <Fingerprint className="h-4 w-4 text-primary" />
                        <span className="text-sm font-semibold">
                          Watermark and Provenance Checks
                        </span>
                      </div>

                      <p className="text-xs text-muted-foreground">
                        Inspect uploaded assets for supported metadata and
                        embedded provenance markers. Invisible watermark
                        decoding and cryptographic signature verification
                        are not currently implemented.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label>Upload an asset</Label>
                      <FileUploadZone
                        onFileSelect={setWatermarkFile}
                        accept="image/jpeg,image/png,image/webp,video/mp4,audio/wav,audio/mpeg,.mp3,application/pdf,.txt"
                      />
                      <p className="text-xs text-muted-foreground">
                        Supported formats: JPG, PNG, WebP, MP4, WAV, MP3, PDF, TXT.
                      </p>
                    </div>

                    <Button
                      className="w-full"
                      onClick={handleWatermarkDetection}
                      disabled={!watermarkFile}
                    >
                      Analyze Watermark and Provenance
                    </Button>
                  </TabsContent>
                </Tabs>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
