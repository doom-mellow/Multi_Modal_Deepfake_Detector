
import { Link, NavLink } from "react-router-dom";
import { Shield, Home, Search, History } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ThemeToggle";

interface NavigationHeaderProps {
  title?: string;
}

const navItems = [
  { label: "Home", path: "/", icon: Home },
  { label: "Detection", path: "/detection", icon: Search },
  { label: "History", path: "/history", icon: History },
];

export function NavigationHeader({ title }: NavigationHeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-card/95 backdrop-blur transition-colors">
      <div className="container mx-auto px-4 py-3.5">
        <div className="flex items-center justify-between gap-4">
          <Link
            to="/"
            className="flex shrink-0 select-none items-center gap-3"
            aria-label="DeepShield AI home"
          >
            <div className="rounded-lg border border-primary/20 bg-primary/10 p-1.5 text-primary">
              <Shield className="h-6 w-6" />
            </div>

            <div>
              <span className="text-lg font-bold tracking-tight text-foreground">
                DeepShield AI
              </span>

              {title && (
                <p className="hidden text-xs text-muted-foreground sm:block">
                  {title}
                </p>
              )}
            </div>
          </Link>

          <div className="flex items-center gap-2 sm:gap-3">
            <nav
              aria-label="Main navigation"
              className="mr-1 flex items-center gap-1 sm:gap-1.5"
            >
              {navItems.map((item) => {
                const Icon = item.icon;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === "/"}
                    className={({ isActive }) =>
                      [
                        "inline-flex h-8 items-center gap-1.5 rounded-md px-2.5 text-xs transition-colors sm:px-3",
                        isActive
                          ? "bg-secondary font-semibold text-primary"
                          : "text-muted-foreground hover:bg-accent hover:text-foreground",
                      ].join(" ")
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <Icon className="h-3.5 w-3.5" />
                        <span className="hidden md:inline">
                          {item.label}
                        </span>
                        {isActive && (
                          <span className="sr-only">(current page)</span>
                        )}
                      </>
                    )}
                  </NavLink>
                );
              })}
            </nav>

            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
}
