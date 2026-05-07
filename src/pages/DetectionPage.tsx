import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { FileUploadZone } from '@/components/FileUploadZone';
import { ProcessingIndicator } from '@/components/ProcessingIndicator';
import { Shield, ArrowLeft } from 'lucide-react';
import { performDetection, validateFile, validateUrl } from '@/services/detectionService';
import type { MediaType } from '@/types/types';
import { toast } from 'sonner';

export default function DetectionPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<MediaType>('image');
  const [isProcessing, setIsProcessing] = useState(false);

  // Image state
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState('');

  // Video state
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState('');

  // Audio state
  const [audioFile, setAudioFile] = useState<File | null>(null);

  // Text state
  const [textContent, setTextContent] = useState('');

  const handleImageDetection = async () => {
    if (!imageFile && !imageUrl) {
      toast.error('Please upload an image file or enter a URL');
      return;
    }

    if (imageFile) {
      const validation = validateFile(imageFile, 'image');
      if (!validation.valid) {
        toast.error(validation.error);
        return;
      }
    }

    if (imageUrl) {
      const validation = validateUrl(imageUrl);
      if (!validation.valid) {
        toast.error(validation.error);
        return;
      }
    }

    setIsProcessing(true);
    try {
      const result = await performDetection({
        mediaType: 'image',
        file: imageFile || undefined,
        url: imageUrl || undefined
      });

      navigate('/results', {
        state: {
          mediaType: 'image',
          result,
          fileName: imageFile?.name || imageUrl,
          contentPreview: imageUrl || imageFile?.name || null
        }
      });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Analysis failed, please try again later');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVideoDetection = async () => {
    if (!videoFile && !videoUrl) {
      toast.error('Please upload a video file or enter a URL');
      return;
    }

    if (videoFile) {
      const validation = validateFile(videoFile, 'video');
      if (!validation.valid) {
        toast.error(validation.error);
        return;
      }
    }

    if (videoUrl) {
      const validation = validateUrl(videoUrl);
      if (!validation.valid) {
        toast.error(validation.error);
        return;
      }
    }

    setIsProcessing(true);
    try {
      const result = await performDetection({
        mediaType: 'video',
        file: videoFile || undefined,
        url: videoUrl || undefined
      });

      navigate('/results', {
        state: {
          mediaType: 'video',
          result,
          fileName: videoFile?.name || videoUrl,
          contentPreview: videoUrl || videoFile?.name || null
        }
      });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Analysis failed, please try again later');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAudioDetection = async () => {
    if (!audioFile) {
      toast.error('Please upload an audio file');
      return;
    }

    const validation = validateFile(audioFile, 'audio');
    if (!validation.valid) {
      toast.error(validation.error);
      return;
    }

    setIsProcessing(true);
    try {
      const result = await performDetection({
        mediaType: 'audio',
        file: audioFile
      });

      navigate('/results', {
        state: {
          mediaType: 'audio',
          result,
          fileName: audioFile.name,
          contentPreview: audioFile.name
        }
      });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Analysis failed, please try again later');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTextDetection = async () => {
    if (!textContent.trim()) {
      toast.error('Please enter text content');
      return;
    }

    if (textContent.length > 10000) {
      toast.error('Text exceeds maximum length of 10,000 characters');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await performDetection({
        mediaType: 'text',
        content: textContent
      });

      navigate('/results', {
        state: {
          mediaType: 'text',
          result,
          contentPreview: textContent.substring(0, 200)
        }
      });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Analysis failed, please try again later');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-primary" />
              <h1 className="text-2xl font-bold text-foreground">Detection Analysis</h1>
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
        <div className="max-w-4xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Content Analysis</CardTitle>
              <CardDescription>
                Select the type of content you want to analyze and submit for AI detection
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isProcessing ? (
                <ProcessingIndicator message="Performing AI detection analysis..." />
              ) : (
                <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as MediaType)}>
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="image">Image</TabsTrigger>
                    <TabsTrigger value="video">Video</TabsTrigger>
                    <TabsTrigger value="audio">Audio</TabsTrigger>
                    <TabsTrigger value="text">Text</TabsTrigger>
                  </TabsList>

                  {/* Image Detection */}
                  <TabsContent value="image" className="space-y-4">
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label>Upload Image File</Label>
                        <FileUploadZone
                          onFileSelect={setImageFile}
                          accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                        />
                        <p className="text-xs text-muted-foreground">
                          Supported formats: JPG, JPEG, PNG, GIF, WebP
                        </p>
                      </div>

                      <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                          <span className="w-full border-t border-border" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                          <span className="bg-card px-2 text-muted-foreground">Or</span>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="image-url">Image URL</Label>
                        <Input
                          id="image-url"
                          type="url"
                          placeholder="https://example.com/image.jpg"
                          value={imageUrl}
                          onChange={(e) => setImageUrl(e.target.value)}
                        />
                      </div>

                      <Button 
                        onClick={handleImageDetection} 
                        className="w-full"
                        disabled={!imageFile && !imageUrl}
                      >
                        Analyze Image
                      </Button>
                    </div>
                  </TabsContent>

                  {/* Video Detection */}
                  <TabsContent value="video" className="space-y-4">
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label>Upload Video File</Label>
                        <FileUploadZone
                          onFileSelect={setVideoFile}
                          accept="video/mp4,video/avi,video/quicktime,video/webm"
                        />
                        <p className="text-xs text-muted-foreground">
                          Supported formats: MP4, AVI, MOV, WebM
                        </p>
                      </div>

                      <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                          <span className="w-full border-t border-border" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                          <span className="bg-card px-2 text-muted-foreground">Or</span>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="video-url">Video URL</Label>
                        <Input
                          id="video-url"
                          type="url"
                          placeholder="https://example.com/video.mp4"
                          value={videoUrl}
                          onChange={(e) => setVideoUrl(e.target.value)}
                        />
                      </div>

                      <Button 
                        onClick={handleVideoDetection} 
                        className="w-full"
                        disabled={!videoFile && !videoUrl}
                      >
                        Analyze Video
                      </Button>
                    </div>
                  </TabsContent>

                  {/* Audio Detection */}
                  <TabsContent value="audio" className="space-y-4">
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label>Upload Audio File</Label>
                        <FileUploadZone
                          onFileSelect={setAudioFile}
                          accept="audio/mpeg,audio/wav,audio/mp4,audio/ogg"
                        />
                        <p className="text-xs text-muted-foreground">
                          Supported formats: MP3, WAV, M4A, OGG
                        </p>
                      </div>

                      <Button 
                        onClick={handleAudioDetection} 
                        className="w-full"
                        disabled={!audioFile}
                      >
                        Analyze Audio
                      </Button>
                    </div>
                  </TabsContent>

                  {/* Text Detection */}
                  <TabsContent value="text" className="space-y-4">
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="text-content">Text Content</Label>
                        <Textarea
                          id="text-content"
                          placeholder="Paste or type the text content you want to analyze..."
                          value={textContent}
                          onChange={(e) => setTextContent(e.target.value)}
                          rows={10}
                          maxLength={10000}
                        />
                        <p className="text-xs text-muted-foreground text-right">
                          {textContent.length} / 10,000 characters
                        </p>
                      </div>

                      <Button 
                        onClick={handleTextDetection} 
                        className="w-full"
                        disabled={!textContent.trim()}
                      >
                        Analyze Text
                      </Button>
                    </div>
                  </TabsContent>
                </Tabs>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
