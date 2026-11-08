
import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
  className?: string;
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { toggleTheme, isDark } = useTheme();

  const nextTheme = isDark ? "light" : "dark";

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={toggleTheme}
      className={cn(
        "relative h-9 gap-2 border-border bg-card px-3 text-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
        className,
      )}
      aria-label={`Switch to ${nextTheme} mode`}
      title={`Switch to ${nextTheme === "light" ? "Light" : "Dark"} Mode`}
    >
      {isDark ? (
        <>
          <Sun className="h-4 w-4 text-warning" />
          <span className="hidden text-xs font-medium sm:inline">
            Light Mode
          </span>
        </>
      ) : (
        <>
          <Moon className="h-4 w-4 text-primary" />
          <span className="hidden text-xs font-medium sm:inline">
            Dark Mode
          </span>
        </>
      )}
    </Button>
  );
}
