import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Video, Mic, FileText, Shield, Search, Clock, Image as ImageIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function HomePage() {
  const navigate = useNavigate();

  const features = [
    {
      icon: ImageIcon,
      title: 'Image Detection',
      description: 'Analyze images for AI manipulation and deepfake content using advanced forensic techniques',
      color: 'text-primary'
    },
    {
      icon: Video,
      title: 'Video Detection',
      description: 'Analyze videos for deepfakes using biological signals and temporal consistency analysis',
      color: 'text-primary'
    },
    {
      icon: Mic,
      title: 'Audio Detection',
      description: 'Detect AI-generated voice clones through spectral analysis and prosody examination',
      color: 'text-primary'
    },
    {
      icon: FileText,
      title: 'Text Detection',
      description: 'Identify AI-written content using perplexity and burstiness pattern analysis',
      color: 'text-primary'
    }
  ];

  const capabilities = [
    {
      icon: Shield,
      title: 'Multi-Modal Analysis',
      description: 'Comprehensive detection across video, audio, and text media types'
    },
    {
      icon: Search,
      title: 'Forensic Precision',
      description: 'Advanced algorithms based on latest research in AI content detection'
    },
    {
      icon: Clock,
      title: 'Detection History',
      description: 'Track and review all your previous forensic analyses'
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-primary" />
              <h1 className="text-2xl font-bold text-foreground">DeepShield AI</h1>
            </div>
            <Button onClick={() => navigate('/history')} variant="outline">
              View History
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto text-center space-y-6">
          <h2 className="text-4xl md:text-5xl font-bold text-foreground">
            Detect AI-Generated Content with Confidence
          </h2>
          <p className="text-lg text-muted-foreground">
            Professional AI detection platform for identifying AI-manipulated images, videos, audio, and text. 
            Powered by advanced detection algorithms and multi-modal analysis techniques.
          </p>
          <Button 
            size="lg" 
            onClick={() => navigate('/detection')}
            className="mt-4"
          >
            Start Detection
          </Button>
        </div>
      </section>

      {/* Detection Types */}
      <section className="container mx-auto px-4 py-12">
        <h3 className="text-2xl font-bold text-center mb-8 text-foreground">Detection Capabilities</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature) => (
            <Card 
              key={feature.title}
              className="cursor-pointer transition-all hover:border-primary"
              onClick={() => navigate('/detection')}
            >
              <CardHeader>
                <feature.icon className={`w-12 h-12 mb-2 ${feature.color}`} />
                <CardTitle>{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      {/* Platform Features */}
      <section className="container mx-auto px-4 py-12">
        <h3 className="text-2xl font-bold text-center mb-8 text-foreground">Platform Features</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {capabilities.map((capability) => (
            <Card key={capability.title}>
              <CardHeader>
                <capability.icon className="w-10 h-10 mb-2 text-primary" />
                <CardTitle className="text-lg">{capability.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{capability.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-12">
        <div className="max-w-3xl mx-auto">
          <h3 className="text-2xl font-bold text-center mb-8 text-foreground">How It Works</h3>
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">1. Upload or Input Content</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Submit video files, audio recordings, or text content for analysis. Supports multiple formats and URL inputs.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">2. Forensic Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Our system performs multi-modal analysis using advanced detection algorithms based on latest research findings.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">3. Review Results</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Get detailed detection results with confidence scores, flagging indicators, and explanations of findings.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-muted-foreground">
              DeepShield AI - Professional AI content detection and verification
            </p>
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => navigate('/help')}
              className="text-muted-foreground hover:text-foreground"
            >
              Need Help?
            </Button>
          </div>
        </div>
      </footer>
    </div>
  );
}
