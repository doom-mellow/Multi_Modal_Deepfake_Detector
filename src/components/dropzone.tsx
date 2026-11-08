
import {
  createContext,
  useCallback,
  useContext,
  type PropsWithChildren,
} from "react";
import { CheckCircle, File, Loader2, Upload, X } from "lucide-react";

import { cn } from "@/lib/utils";
import type { UseSupabaseUploadReturn } from "@/hooks/use-supabase-upload";
import { Button } from "@/components/ui/button";

export const formatBytes = (
  bytes: number,
  decimals = 2,
  size?: "bytes" | "KB" | "MB" | "GB" | "TB" | "PB" | "EB" | "ZB" | "YB",
) => {
  const units = ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];

  if (!Number.isFinite(bytes) || bytes <= 0) {
    return size ? `0 ${size}` : "0 bytes";
  }

  const precision = Math.max(0, decimals);
  const index = size ? units.indexOf(size) : Math.floor(Math.log(bytes) / Math.log(1000));
  const safeIndex = Math.max(0, Math.min(index, units.length - 1));

  return `${parseFloat((bytes / Math.pow(1000, safeIndex)).toFixed(precision))} ${units[safeIndex]}`;
};

type DropzoneContextType = Omit<
  UseSupabaseUploadReturn,
  "getRootProps" | "getInputProps"
>;

const DropzoneContext = createContext<DropzoneContextType | undefined>(
  undefined,
);

type DropzoneProps = UseSupabaseUploadReturn & {
  className?: string;
};

const useDropzoneContext = () => {
  const context = useContext(DropzoneContext);

  if (!context) {
    throw new Error("useDropzoneContext must be used within a Dropzone.");
  }

  return context;
};

const Dropzone = ({
  className,
  children,
  getRootProps,
  getInputProps,
  ...restProps
}: PropsWithChildren<DropzoneProps>) => {
  const isSuccess = restProps.isSuccess;
  const isActive = restProps.isDragActive;

  const isInvalid =
    (restProps.isDragActive && restProps.isDragReject) ||
    (restProps.errors.length > 0 && !restProps.isSuccess) ||
    restProps.files.some((file) => file.errors.length > 0);

  return (
    <DropzoneContext.Provider value={restProps}>
      <div
        {...getRootProps({
          className: cn(
            "rounded-lg border-2 bg-card p-6 text-center text-foreground transition-colors duration-300",
            className,
            isSuccess ? "border-solid" : "border-dashed",
            isActive && "border-primary bg-primary/10",
            isInvalid && "border-destructive bg-destructive/10",
          ),
        })}
      >
        <input {...getInputProps()} />
        {children}
      </div>
    </DropzoneContext.Provider>
  );
};

const DropzoneContent = ({ className }: { className?: string }) => {
  const {
    files,
    setFiles,
    onUpload,
    loading,
    successes,
    errors,
    maxFiles,
    isSuccess,
  } = useDropzoneContext();

  const exceedMaxFiles = files.length > maxFiles;

  const handleRemoveFile = useCallback(
    (index: number) => {
      setFiles((currentFiles) => currentFiles.filter((_, i) => i !== index));
    },
    [setFiles],
  );

  if (isSuccess) {
    return (
      <div
        className={cn(
          "flex items-center justify-center gap-x-2",
          className,
        )}
      >
        <CheckCircle size={16} className="text-primary" />
        <p className="text-sm text-primary">
          Successfully uploaded {successes.length} file
          {successes.length === 1 ? "" : "s"}
        </p>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col", className)}>
      {files.map((file, index) => {
        const fileError = errors.find((error) => error.name === file.name);
        const isUploaded = successes.includes(file.name);

        return (
          <div
            key={`${file.name}-${index}`}
            className="flex items-center gap-x-4 border-b py-2 first:mt-4 last:mb-4"
          >
            {file.type.startsWith("image/") ? (
              <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded border bg-muted">
                <img
                  src={file.preview}
                  alt={file.name}
                  className="h-full w-full object-cover"
                />
              </div>
            ) : (
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded border bg-muted">
                <File size={18} />
              </div>
            )}

            <div className="flex min-w-0 grow flex-col items-start">
              <p title={file.name} className="max-w-full truncate text-sm">
                {file.name}
              </p>

              {file.errors.length > 0 ? (
                <p className="text-xs text-destructive">
                  {file.errors.map((error) => error.message).join(", ")}
                </p>
              ) : loading && !isUploaded ? (
                <p className="text-xs text-muted-foreground">
                  Uploading file...
                </p>
              ) : fileError ? (
                <p className="text-xs text-destructive">
                  Failed to upload: {fileError.message}
                </p>
              ) : isUploaded ? (
                <p className="text-xs text-primary">
                  Successfully uploaded file
                </p>
              ) : (
                <p className="text-xs text-muted-foreground">
                  {formatBytes(file.size)}
                </p>
              )}
            </div>

            {!loading && !isUploaded && (
              <Button
                type="button"
                size="icon"
                variant="ghost"
                className="shrink-0 text-muted-foreground hover:text-foreground"
                aria-label={`Remove ${file.name}`}
                onClick={(event) => {
                  event.stopPropagation();
                  handleRemoveFile(index);
                }}
              >
                <X />
              </Button>
            )}
          </div>
        );
      })}

      {exceedMaxFiles && (
        <p className="mt-2 text-left text-sm text-destructive">
          You may upload only up to {maxFiles} files. Please remove{" "}
          {files.length - maxFiles} file(s).
        </p>
      )}

      {files.length > 0 && !exceedMaxFiles && (
        <div className="mt-2">
          <Button
            type="button"
            variant="outline"
            disabled={
              loading || files.some((file) => file.errors.length > 0)
            }
            onClick={(event) => {
              event.stopPropagation();
              void onUpload();
            }}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              "Upload files"
            )}
          </Button>
        </div>
      )}
    </div>
  );
};

const DropzoneEmptyState = ({ className }: { className?: string }) => {
  const { maxFiles, maxFileSize, inputRef, isSuccess } =
    useDropzoneContext();

  if (isSuccess) return null;

  return (
    <div className={cn("flex flex-col items-center gap-y-2", className)}>
      <Upload size={20} className="text-muted-foreground" />

      <p className="text-sm">
        Upload{maxFiles > 1 ? ` up to ${maxFiles}` : ""} file
        {maxFiles === 1 ? "" : "s"}
      </p>

      <div className="flex flex-col items-center gap-y-1">
        <p className="text-xs text-muted-foreground">
          Drag and drop or{" "}
          <button
            type="button"
            className="underline transition hover:text-foreground"
            onClick={(event) => {
              event.stopPropagation();
              inputRef.current?.click();
            }}
          >
            select {maxFiles === 1 ? "file" : "files"}
          </button>
        </p>

        {maxFileSize !== Number.POSITIVE_INFINITY && (
          <p className="text-xs text-muted-foreground">
            Maximum file size: {formatBytes(maxFileSize)}
          </p>
        )}
      </div>
    </div>
  );
};

export {
  Dropzone,
  DropzoneContent,
  DropzoneEmptyState,
  useDropzoneContext,
};
