
import { cn } from "@/lib/utils";

interface ConfidenceScoreProps {
  score: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizes = {
  sm: {
    radius: 40,
    stroke: 6,
    fontSize: "text-lg",
    labelSize: "text-xs",
  },
  md: {
    radius: 60,
    stroke: 8,
    fontSize: "text-3xl",
    labelSize: "text-sm",
  },
  lg: {
    radius: 80,
    stroke: 10,
    fontSize: "text-5xl",
    labelSize: "text-base",
  },
};

export function ConfidenceScore({
  score,
  size = "md",
  className,
}: ConfidenceScoreProps) {
  const isValid = Number.isFinite(score);
  const safeScore = isValid ? Math.min(100, Math.max(0, score)) : 0;

  const config = sizes[size];
  const diameter = (config.radius + config.stroke) * 2;
  const circumference = 2 * Math.PI * config.radius;
  const offset = circumference * (1 - safeScore / 100);

  return (
    <div
      className={cn("flex flex-col items-center gap-2", className)}
      role="progressbar"
      aria-label="Model confidence"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={isValid ? safeScore : undefined}
      aria-valuetext={
        isValid ? `${safeScore.toFixed(1)} percent` : "Unavailable"
      }
    >
      <div className="relative">
        <svg
          width={diameter}
          height={diameter}
          viewBox={`0 0 ${diameter} ${diameter}`}
          className="-rotate-90"
          aria-hidden="true"
        >
          <circle
            cx={diameter / 2}
            cy={diameter / 2}
            r={config.radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={config.stroke}
            className="text-muted"
          />

          <circle
            cx={diameter / 2}
            cy={diameter / 2}
            r={config.radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={config.stroke}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="text-primary transition-all duration-700 ease-out"
          />
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("font-bold", config.fontSize)}>
            {isValid ? safeScore.toFixed(0) : "--"}
          </span>

          <span className={cn("text-muted-foreground", config.labelSize)}>
            Confidence
          </span>
        </div>
      </div>
    </div>
  );
}
