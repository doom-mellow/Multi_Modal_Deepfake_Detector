
import { Loader2 } from "lucide-react";

import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface ProcessingIndicatorProps {
  message?: string;
  className?: string;
}

export function ProcessingIndicator({
  message = "Analyzing content...",
  className,
}: ProcessingIndicatorProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 py-8",
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <Loader2
        className="h-12 w-12 animate-spin text-primary"
        aria-hidden="true"
      />

      <div className="w-full max-w-md space-y-2">
        <p className="text-center text-sm font-medium text-foreground">
          {message}
        </p>

        <Progress value={undefined} className="h-1" />
      </div>

      <span className="sr-only">Please wait while analysis is running.</span>
    </div>
  );
}
