import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  type Accept,
  type FileError,
  type FileRejection,
  useDropzone,
} from "react-dropzone";

import type { SupabaseClient } from "@supabase/supabase-js";

interface FileWithPreview extends File {
  preview?: string;
  errors: readonly FileError[];
}

export type UseSupabaseUploadOptions = {
  bucketName: string;
  path?: string;
  allowedMimeTypes?: string[];
  maxFileSize?: number;
  maxFiles?: number;
  cacheControl?: number;
  upsert?: boolean;
  supabase: SupabaseClient;
};

function createFileEntry(
  file: File,
  errors: readonly FileError[] = [],
): FileWithPreview {
  const entry = file as FileWithPreview;

  entry.preview = URL.createObjectURL(file);
  entry.errors = errors;

  return entry;
}

const useSupabaseUpload = (options: UseSupabaseUploadOptions) => {
  const {
    bucketName,
    path,
    allowedMimeTypes = [],
    maxFileSize = Number.POSITIVE_INFINITY,
    maxFiles = 1,
    cacheControl = 3600,
    upsert = false,
    supabase,
  } = options;

  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<
    { name: string; message: string }[]
  >([]);
  const [successes, setSuccesses] = useState<string[]>([]);

  const previewUrls = useRef(new Set<string>());

  const accept = useMemo<Accept>(() => {
    return allowedMimeTypes.reduce<Accept>((result, mimeType) => {
      result[mimeType] = [];
      return result;
    }, {});
  }, [allowedMimeTypes]);

  const isSuccess = useMemo(() => {
    return (
      files.length > 0 &&
      errors.length === 0 &&
      successes.length === files.filter((file) => file.errors.length === 0).length
    );
  }, [files, errors, successes]);

  /**
   * Add accepted and rejected files to the selection.
   */
  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      const acceptedEntries = acceptedFiles.map((file) =>
        createFileEntry(file),
      );

      const rejectedEntries = fileRejections.map(({ file, errors }) =>
        createFileEntry(file, errors),
      );

      for (const file of [...acceptedEntries, ...rejectedEntries]) {
        if (file.preview) {
          previewUrls.current.add(file.preview);
        }
      }

      setFiles((currentFiles) => {
        const existingNames = new Set(
          currentFiles.map((file) => file.name),
        );

        const newEntries = [...acceptedEntries, ...rejectedEntries]
          .filter((file) => !existingNames.has(file.name));

        return [...currentFiles, ...newEntries];
      });
    },
    [],
  );

  const dropzoneProps = useDropzone({
    onDrop,
    noClick: true,
    accept,
    maxSize: maxFileSize,
    maxFiles,
    multiple: maxFiles !== 1,
  });

  /**
   * Upload selected files to Supabase Storage.
   * Successfully uploaded files are skipped on subsequent attempts.
   */
  const onUpload = useCallback(async () => {
    if (loading || files.length === 0) {
      return;
    }

    const filesToUpload = files.filter(
      (file) =>
        file.errors.length === 0 &&
        !successes.includes(file.name),
    );

    if (filesToUpload.length === 0) {
      return;
    }

    setLoading(true);

    try {
      const responses = await Promise.all(
        filesToUpload.map(async (file) => {
          try {
            const filePath = path
              ? `${path.replace(/\/+$/, "")}/${file.name}`
              : file.name;

            const { error } = await supabase.storage
              .from(bucketName)
              .upload(filePath, file, {
                cacheControl: String(cacheControl),
                upsert,
              });

            if (error) {
              return {
                name: file.name,
                message: error.message,
              };
            }

            return {
              name: file.name,
              message: undefined,
            };
          } catch (error: unknown) {
            return {
              name: file.name,
              message:
                error instanceof Error
                  ? error.message
                  : "Unexpected upload error.",
            };
          }
        }),
      );

      const failedUploads = responses.filter(
        (response) => response.message !== undefined,
      );

      const successfulUploads = responses.filter(
        (response) => response.message === undefined,
      );

      setErrors((previousErrors) => {
        const remainingErrors = previousErrors.filter(
          (previous) =>
            !filesToUpload.some((file) => file.name === previous.name),
        );

        return [...remainingErrors, ...failedUploads] as {
          name: string;
          message: string;
        }[];
      });

      setSuccesses((previousSuccesses) => {
        return Array.from(
          new Set([
            ...previousSuccesses,
            ...successfulUploads.map((response) => response.name),
          ]),
        );
      });
    } finally {
      setLoading(false);
    }
  }, [
    loading,
    files,
    successes,
    path,
    bucketName,
    cacheControl,
    upsert,
    supabase,
  ]);

  /**
   * Clear upload errors when the selection is empty.
   */
  useEffect(() => {
    if (files.length === 0) {
      setErrors([]);
      setSuccesses([]);
    }
  }, [files.length]);

  /**
   * Release generated preview URLs when the hook is unmounted.
   */
  useEffect(() => {
    return () => {
      previewUrls.current.forEach((url) => {
        URL.revokeObjectURL(url);
      });

      previewUrls.current.clear();
    };
  }, []);

  return {
    files,
    setFiles,
    successes,
    isSuccess,
    loading,
    errors,
    setErrors,
    onUpload,
    maxFileSize,
    maxFiles,
    allowedMimeTypes,
    ...dropzoneProps,
  };
};

export { useSupabaseUpload };

export type UseSupabaseUploadReturn = ReturnType<
  typeof useSupabaseUpload
>;