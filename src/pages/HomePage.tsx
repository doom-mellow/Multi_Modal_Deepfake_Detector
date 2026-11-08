import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Video,
  Mic,
  FileText,
  Shield,
  Search,
  Clock,
  Image as ImageIcon,
  Code2,
  Cpu,
  Fingerprint,
  ArrowRight,
} from 'lucide-react';

const analysisCategories = [
  {
    icon: ImageIcon,
    title: 'Image Analysis',
    description:
      'Examine images for visual artifacts, manipulation, and patterns associated with synthetic content.',
  },
  {
    icon: Video,
    title: 'Video Analysis',
    description:
      'Inspect video frames for possible facial manipulation and visual inconsistencies.',
  },
  {
    icon: Mic,
    title: 'Audio Analysis',
    description:
      'Examine audio characteristics for signals associated with synthetic or cloned speech.',
  },
  {
    icon: FileText,
    title: 'Text Analysis',
    description:
      'Review linguistic patterns that may be associated with AI-generated writing.',
  },
  {
    icon: Code2,
    title: 'Code Analysis',
    description:
      'Inspect source code structure and style for patterns associated with generated code.',
  },
  {
    icon: Cpu,
    title: 'Embedding Analysis',
    description:
      'Examine supported feature representations and similarity patterns.',
  },
  {
    icon: Fingerprint,
    title: 'Watermark and Provenance',
    description:
      'Check supported assets for available watermark signals and provenance metadata.',
  },
];

const platformFeatures = [
  {
    icon: Shield,
    title: 'Multiple Content Types',
    description:
      'A single workspace for examining images, videos, audio, text, code, and related forensic data.',
  },
  {
    icon: Search,
    title: 'Analysis Findings',
    description:
      'Review classifications, confidence information, and the indicators returned by each analysis.',
  },
  {
    icon: Clock,
    title: 'Analysis History',
    description:
      'Keep track of saved analyses and revisit previous results.',
  },
];

const workflowSteps = [
  {
    number: '01',
    title: 'Submit Content',
    description:
      'Upload a supported file, provide a URL, or enter text for analysis.',
  },
  {
    number: '02',
    title: 'Run an Analysis',
    description:
      'The configured analysis tools examine the submitted content.',
  },
  {
    number: '03',
    title: 'Review Findings',
    description:
      'Inspect the returned classification, confidence information, and supporting indicators.',
  },
];

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors">
      <main>
        <section className="container mx-auto px-4 py-20 md:py-28">
          <div className="mx-auto max-w-3xl space-y-6 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
              <Shield className="h-7 w-7 text-primary" />
            </div>

            <p className="text-sm font-medium uppercase tracking-wider text-primary">
              DeepShield AI
            </p>

            <h1 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl">
              Examine AI-Generated and Manipulated Content
            </h1>

            <p className="mx-auto max-w-2xl text-base leading-relaxed text-muted-foreground md:text-lg">
              A unified platform for examining digital content across
              multiple formats, reviewing forensic indicators, and exploring
              content authenticity.
            </p>

            <div className="flex flex-col justify-center gap-3 pt-2 sm:flex-row">
              <Button
                size="lg"
                onClick={() => navigate('/detection')}
                className="gap-2"
              >
                Start an Analysis
                <ArrowRight className="h-4 w-4" />
              </Button>

              <Button
                size="lg"
                variant="outline"
                onClick={() => navigate('/history')}
              >
                View Analysis History
              </Button>
            </div>
          </div>
        </section>

        <section className="container mx-auto px-4 py-12">
          <div className="mb-8 text-center">
            <h2 className="text-2xl font-bold">Analysis Categories</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Select the type of digital content you want to examine.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {analysisCategories.map((category) => {
              const Icon = category.icon;

              return (
                <Card key={category.title} className="h-full">
                  <CardHeader>
                    <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>

                    <CardTitle className="text-lg">
                      {category.title}
                    </CardTitle>

                    <CardDescription className="leading-relaxed">
                      {category.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              );
            })}
          </div>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            Available checks depend on the detectors and verification tools
            configured for each category.
          </p>
        </section>

        <section className="container mx-auto px-4 py-14">
          <div className="mb-8 text-center">
            <h2 className="text-2xl font-bold">Platform Features</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Tools to organize and review your analysis work.
            </p>
          </div>

          <div className="mx-auto grid max-w-5xl grid-cols-1 gap-5 md:grid-cols-3">
            {platformFeatures.map((feature) => {
              const Icon = feature.icon;

              return (
                <Card key={feature.title} className="h-full">
                  <CardHeader>
                    <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>

                    <CardTitle className="text-lg">
                      {feature.title}
                    </CardTitle>
                  </CardHeader>

                  <CardContent>
                    <p className="text-sm leading-relaxed text-muted-foreground">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>

        <section className="container mx-auto px-4 py-14">
          <div className="mx-auto max-w-4xl">
            <div className="mb-8 text-center">
              <h2 className="text-2xl font-bold">How It Works</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Three steps from submission to review.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
              {workflowSteps.map((step) => (
                <Card key={step.number} className="h-full">
                  <CardHeader>
                    <span className="text-sm font-semibold tracking-wider text-primary">
                      {step.number}
                    </span>
                    <CardTitle className="text-lg">
                      {step.title}
                    </CardTitle>
                    <CardDescription className="leading-relaxed">
                      {step.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>

            <p className="mt-6 text-center text-xs leading-relaxed text-muted-foreground">
              Detection results are analytical indicators, not absolute proof
              of whether content was created or modified by AI.
            </p>
          </div>
        </section>
      </main>

      <footer className="mt-12 border-t border-border bg-card">
        <div className="container mx-auto flex flex-col items-center justify-between gap-2 px-4 py-7 text-center sm:flex-row sm:text-left">
          <p className="text-sm text-muted-foreground">
            DeepShield AI · Digital Content Analysis
          </p>
          <p className="text-xs text-muted-foreground">
            Multi-modal content examination
          </p>
        </div>
      </footer>
    </div>
  );
}