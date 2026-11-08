import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { FileUploadZone } from '@/components/FileUploadZone';
import { ProcessingIndicator } from '@/components/ProcessingIndicator';
import {
  Code2,
  Cpu,
  Fingerprint,
  Image as ImageIcon,
  Video,
  Mic,
  FileText,
} from 'lucide-react';
import {
  performDetection,
  validateFile,
  validateUrl,
} from '@/services/detectionService';
import type { DetectionRequest, MediaType } from '@/types/types';
import { toast } from 'sonner';

interface ResultMetadata {
  fileName?: string | null;
  contentPreview?: string | null;
}

export default function DetectionPage() {
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<MediaType>('image');
  const [isProcessing, setIsProcessing] = useState(false);

  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState('');

  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState('');

  const [audioFile, setAudioFile] = useState<File | null>(null);

  const [textContent, setTextContent] = useState('');

  const [codeContent, setCodeContent] = useState('');
  const [codeFile, setCodeFile] = useState<File | null>(null);
  const [languageHint, setLanguageHint] = useState('auto');

  const [embeddingFile, setEmbeddingFile] = useState<File | null>(null);
  const [embeddingText, setEmbeddingText] = useState('');

  const [watermarkFile, setWatermarkFile] = useState<File | null>(null);
  const [watermarkUrl, setWatermarkUrl] = useState('');

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
          fileName: metadata.fileName ?? request.file?.name ?? request.url ?? null,
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
      toast.error(validation.error || 'The selected file is not supported.');
      return false;
    }

    return true;
  };

  const validateAssetUrl = (url: string) => {
    const validation = validateUrl(url.trim());

    if (!validation.valid) {
      toast.error(validation.error || 'Please enter a valid URL.');
      return false;
    }

    return true;
  };

  const handleImageDetection = () => {
    if (imageFile && imageUrl.trim()) {
      toast.error('Choose an image file or a URL, not both.');
      return;
    }

    if (!imageFile && !imageUrl.trim()) {
      toast.error('Upload an image or enter an image URL.');
      return;
    }

    if (imageFile) {
      if (!validateUploadedFile(imageFile, 'image')) return;

      void runAnalysis(
        { mediaType: 'image', file: imageFile },
        { fileName: imageFile.name, contentPreview: imageFile.name },
      );
      return;
    }

    if (!validateAssetUrl(imageUrl)) return;

    void runAnalysis(
      { mediaType: 'image', url: imageUrl.trim() },
      { fileName: imageUrl.trim(), contentPreview: imageUrl.trim() },
    );
  };

  const handleVideoDetection = () => {
    if (videoFile && videoUrl.trim()) {
      toast.error('Choose a video file or a URL, not both.');
      return;
    }

    if (!videoFile && !videoUrl.trim()) {
      toast.error('Upload a video or enter a video URL.');
      return;
    }

    if (videoFile) {
      if (!validateUploadedFile(videoFile, 'video')) return;

      void runAnalysis(
        { mediaType: 'video', file: videoFile },
        { fileName: videoFile.name, contentPreview: videoFile.name },
      );
      return;
    }

    if (!validateAssetUrl(videoUrl)) return;

    void runAnalysis(
      { mediaType: 'video', url: videoUrl.trim() },
      { fileName: videoUrl.trim(), contentPreview: videoUrl.trim() },
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
      { fileName: audioFile.name, contentPreview: audioFile.name },
    );
  };

  const handleTextDetection = () => {
    const content = textContent.trim();

    if (!content) {
      toast.error('Please enter text to analyze.');
      return;
    }

    if (content.length > 10000) {
      toast.error('Text cannot exceed 10,000 characters.');
      return;
    }

    void runAnalysis(
      { mediaType: 'text', content },
      { contentPreview: content.slice(0, 200) },
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
        languageHint: languageHint !== 'auto' ? languageHint : undefined,
      },
      {
        fileName: codeFile?.name ?? 'source_snippet',
        contentPreview: content.slice(0, 200),
      },
    );
  };

  const handleEmbeddingDetection = () => {
    if (!embeddingFile && !embeddingText.trim()) {
      toast.error('Upload an asset or enter representation text.');
      return;
    }

    void runAnalysis(
      {
        mediaType: 'embedding',
        content: embeddingText.trim() || undefined,
        file: embeddingFile || undefined,
        embeddingModel: 'auto',
      },
      {
        fileName: embeddingFile?.name ?? 'embedding_input',
        contentPreview: embeddingText.trim()
          ? embeddingText.trim().slice(0, 200)
          : embeddingFile?.name ?? null,
      },
    );
  };

  const handleWatermarkDetection = () => {
    if (watermarkFile && watermarkUrl.trim()) {
      toast.error('Choose an asset file or a URL, not both.');
      return;
    }

    if (!watermarkFile && !watermarkUrl.trim()) {
      toast.error('Upload an asset or enter its URL.');
      return;
    }

    if (watermarkFile) {
      void runAnalysis(
        { mediaType: 'watermark', file: watermarkFile },
        {
          fileName: watermarkFile.name,
          contentPreview: watermarkFile.name,
        },
      );
      return;
    }

    if (!validateAssetUrl(watermarkUrl)) return;

    void runAnalysis(
      { mediaType: 'watermark', url: watermarkUrl.trim() },
      {
        fileName: watermarkUrl.trim(),
        contentPreview: watermarkUrl.trim(),
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
                  onValueChange={(value) => setActiveTab(value as MediaType)}
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
                    <TabsTrigger value="embedding" className="flex items-center gap-1.5 py-2">
                      <Cpu className="h-3.5 w-3.5" />
                      Embedding
                    </TabsTrigger>
                    <TabsTrigger value="watermark" className="flex items-center gap-1.5 py-2">
                      <Fingerprint className="h-3.5 w-3.5" />
                      Watermark
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="image" className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <Label>Upload image</Label>
                      <FileUploadZone
                        onFileSelect={(file) => {
                          setImageFile(file);
                          if (file) setImageUrl('');
                        }}
                        accept="image/jpeg,image/png,image/gif,image/webp"
                      />
                      <p className="text-xs text-muted-foreground">
                        Supported formats: JPG, PNG, GIF, WebP.
                      </p>
                    </div>

                    <div className="text-center text-xs text-muted-foreground">OR</div>

                    <div className="space-y-2">
                      <Label htmlFor="image-url">Image URL</Label>
                      <Input
                        id="image-url"
                        type="url"
                        placeholder="https://example.com/image.jpg"
                        value={imageUrl}
                        onChange={(event) => {
                          setImageUrl(event.target.value);
                          if (event.target.value) setImageFile(null);
                        }}
                      />
                    </div>

                    <Button
                      className="w-full"
                      onClick={handleImageDetection}
                      disabled={!imageFile && !imageUrl.trim()}
                    >
                      Analyze Image
                    </Button>
                  </TabsContent>

                  <TabsContent value="video" className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <Label>Upload video</Label>
                      <FileUploadZone
                        onFileSelect={(file) => {
                          setVideoFile(file);
                          if (file) setVideoUrl('');
                        }}
                        accept="video/mp4,video/avi,video/quicktime,video/webm"
                      />
                      <p className="text-xs text-muted-foreground">
                        Supported formats: MP4, AVI, MOV, WebM.
                      </p>
                    </div>

                    <div className="text-center text-xs text-muted-foreground">OR</div>

                    <div className="space-y-2">
                      <Label htmlFor="video-url">Video URL</Label>
                      <Input
                        id="video-url"
                        type="url"
                        placeholder="https://example.com/video.mp4"
                        value={videoUrl}
                        onChange={(event) => {
                          setVideoUrl(event.target.value);
                          if (event.target.value) setVideoFile(null);
                        }}
                      />
                    </div>

                    <Button
                      className="w-full"
                      onClick={handleVideoDetection}
                      disabled={!videoFile && !videoUrl.trim()}
                    >
                      Analyze Video
                    </Button>
                  </TabsContent>

                  <TabsContent value="audio" className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <Label>Upload audio</Label>
                      <FileUploadZone
                        onFileSelect={setAudioFile}
                        accept="audio/mpeg,audio/wav,audio/mp4,audio/ogg"
                      />
                      <p className="text-xs text-muted-foreground">
                        Supported formats: MP3, WAV, M4A, OGG.
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

                  <TabsContent value="text" className="space-y-4 pt-4">
                    <div className="space-y-2">
                      <Label htmlFor="text-content">Text content</Label>
                      <Textarea
                        id="text-content"
                        placeholder="Paste or type the text you want to analyze..."
                        value={textContent}
                        onChange={(event) => setTextContent(event.target.value)}
                        rows={10}
                        maxLength={10000}
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

                  <TabsContent value="code" className="space-y-4 pt-4">
                    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                      <div>
                        <Label className="text-base font-semibold">Source code</Label>
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
                          onChange={(event) => setLanguageHint(event.target.value)}
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

                  <TabsContent value="embedding" className="space-y-4 pt-4">
                    <div className="rounded-md border border-border bg-muted/30 p-3">
                      <div className="mb-1 flex items-center gap-2">
                        <Cpu className="h-4 w-4 text-primary" />
                        <span className="text-sm font-semibold">
                          Embedding Analysis
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Submit an asset or an existing representation for
                        analysis. The available checks depend on the embedding
                        extraction and comparison methods configured by the backend.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label>Upload an asset or representation file</Label>
                      <FileUploadZone
                        onFileSelect={setEmbeddingFile}
                        accept="image/*,video/*,audio/*,text/plain,application/json,.npy,.npz,.pt,.pth"
                      />
                    </div>

                    <div className="text-center text-xs text-muted-foreground">
                      OR ENTER REPRESENTATION DATA
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="embedding-text">
                        Text or vector representation
                      </Label>
                      <Textarea
                        id="embedding-text"
                        placeholder="Enter text or an existing vector representation..."
                        value={embeddingText}
                        onChange={(event) => setEmbeddingText(event.target.value)}
                        rows={5}
                      />
                    </div>

                    <Button
                      className="w-full"
                      onClick={handleEmbeddingDetection}
                      disabled={!embeddingFile && !embeddingText.trim()}
                    >
                      Analyze Representation
                    </Button>
                  </TabsContent>

                  <TabsContent value="watermark" className="space-y-4 pt-4">
                    <div className="rounded-md border border-border bg-muted/30 p-3">
                      <div className="mb-1 flex items-center gap-2">
                        <Fingerprint className="h-4 w-4 text-primary" />
                        <span className="text-sm font-semibold">
                          Watermark and Provenance Checks
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Submit an asset to check for supported watermark signals,
                        embedded metadata, or provenance records. Not every
                        watermark format or provenance standard is detectable.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label>Upload an asset</Label>
                      <FileUploadZone
                        onFileSelect={(file) => {
                          setWatermarkFile(file);
                          if (file) setWatermarkUrl('');
                        }}
                        accept="image/jpeg,image/png,image/webp,video/mp4,audio/wav,audio/mpeg,application/pdf"
                      />
                    </div>

                    <div className="text-center text-xs text-muted-foreground">
                      OR ENTER AN ASSET URL
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="watermark-url">Asset URL</Label>
                      <Input
                        id="watermark-url"
                        type="url"
                        placeholder="https://example.com/asset.png"
                        value={watermarkUrl}
                        onChange={(event) => {
                          setWatermarkUrl(event.target.value);
                          if (event.target.value) setWatermarkFile(null);
                        }}
                      />
                    </div>

                    <Button
                      className="w-full"
                      onClick={handleWatermarkDetection}
                      disabled={!watermarkFile && !watermarkUrl.trim()}
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