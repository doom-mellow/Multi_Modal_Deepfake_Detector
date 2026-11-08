
import { useCallback, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { Upload, File, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface FileUploadZoneProps {
  onFileSelect: (file: File) => void;
  accept: string;
  maxSize?: number;
  className?: string;
  disabled?: boolean;
}

function matchesAcceptedType(file: File, accept: string): boolean {
  const acceptedTypes = accept
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);

  if (acceptedTypes.length === 0) return true;

  const fileName = file.name.toLowerCase();

  return acceptedTypes.some((type) => {
    if (type.startsWith(".")) {
      return fileName.endsWith(type);
    }

    if (type.endsWith("/*")) {
      return file.type.startsWith(type.slice(0, -1));
    }

    return file.type.toLowerCase() === type;
  });
}

export function FileUploadZone({
  onFileSelect,
  accept,
  maxSize = 100 * 1024 * 1024,
  className,
  disabled = false,
}: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = useCallback(
    (file: File) => {
      if (file.size > maxSize) {
        setError(
          `File exceeds the maximum size of ${Math.round(maxSize / 1024 / 1024)} MB.`,
        );
        return;
      }

      if (!matchesAcceptedType(file, accept)) {
        setError("This file format is not supported.");
        return;
      }

      setError(null);
      setSelectedFile(file);
      onFileSelect(file);
    },
    [accept, maxSize, onFileSelect],
  );

  const handleDragOver = useCallback(
    (event: DragEvent<HTMLLabelElement>) => {
      event.preventDefault();
      if (!disabled) setIsDragging(true);
    },
    [disabled],
  );

  const handleDragLeave = useCallback(
    (event: DragEvent<HTMLLabelElement>) => {
      event.preventDefault();
      setIsDragging(false);
    },
    [],
  );

  const handleDrop = useCallback(
    (event: DragEvent<HTMLLabelElement>) => {
      event.preventDefault();
      setIsDragging(false);

      if (disabled) return;

      const file = event.dataTransfer.files[0];
      if (file) validateAndSelect(file);
    },
    [disabled, validateAndSelect],
  );

  const handleFileInput = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];

      if (file && !disabled) {
        validateAndSelect(file);
      }

      // Allows selecting the same file again after clearing it.
      event.target.value = "";
    },
    [disabled, validateAndSelect],
  );

  const handleClear = useCallback(() => {
    setSelectedFile(null);
    setError(null);
  }, []);

  return (
    <div className={cn("w-full", className)}>
      {!selectedFile ? (
        <label
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "flex h-48 w-full flex-col items-center justify-center rounded border-2 border-dashed transition-colors",
            isDragging && !disabled && "border-primary bg-primary/5",
            !isDragging &&
              !disabled &&
              "border-border hover:border-primary hover:bg-accent",
            disabled && "cursor-not-allowed opacity-50",
          )}
        >
          <div className="flex flex-col items-center justify-center px-4 text-center">
            <Upload
              className={cn(
                "mb-3 h-10 w-10",
                isDragging ? "text-primary" : "text-muted-foreground",
              )}
            />

            <p className="mb-2 text-sm text-foreground">
              <span className="font-semibold">Click to upload</span> or drag
              and drop
            </p>

            <p className="text-xs text-muted-foreground">
              Maximum file size: {Math.round(maxSize / 1024 / 1024)} MB
            </p>
          </div>

          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept={accept}
            onChange={handleFileInput}
            disabled={disabled}
          />
        </label>
      ) : (
        <div className="flex items-center justify-between rounded border bg-card p-4">
          <div className="flex min-w-0 items-center gap-3">
            <File className="h-8 w-8 shrink-0 text-primary" />

            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-foreground">
                {selectedFile.name}
              </p>
              <p className="text-xs text-muted-foreground">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          </div>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleClear}
            disabled={disabled}
            aria-label="Remove selected file"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {error && (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
