import type { DetectionRequest, MediaType } from "@/types/types";

const MAX_FILE_SIZE = 100 * 1024 * 1024;

const SUPPORTED_FORMATS: Record<MediaType, string[]> = {
  image: [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
  ],
  video: [
    "video/mp4",
    "video/avi",
    "video/quicktime",
    "video/webm",
  ],
  audio: [
    "audio/mpeg",
    "audio/wav",
    "audio/mp4",
    "audio/ogg",
    "audio/webm",
  ],
  text: [
    "text/plain",
  ],
  code: [
    "text/plain",
    "text/x-python",
    "text/javascript",
    "application/javascript",
    "text/typescript",
    "application/typescript",
    "text/x-c",
    "text/x-c++",
    "text/x-java",
    "text/x-go",
    "text/x-rust",
    "application/json",
  ],
  embedding: [
    "image/jpeg",
    "image/png",
    "image/webp",
    "video/mp4",
    "audio/mpeg",
    "audio/wav",
    "text/plain",
    "application/json",
  ],
  watermark: [
    "image/jpeg",
    "image/png",
    "image/webp",
    "video/mp4",
    "audio/mpeg",
    "audio/wav",
    "application/pdf",
  ],
};

const SUPPORTED_EXTENSIONS: Record<MediaType, string[]> = {
  image: ["jpg", "jpeg", "png", "gif", "webp"],
  video: ["mp4", "avi", "mov", "webm"],
  audio: ["mp3", "wav", "m4a", "ogg", "webm"],
  text: ["txt"],
  code: [
    "py", "js", "jsx", "ts", "tsx", "cpp", "c", "h",
    "hpp", "java", "go", "rs", "php", "rb", "swift",
    "kt", "cs", "html", "css", "json",
  ],
  embedding: [
    "jpg", "jpeg", "png", "webp", "mp4", "mp3",
    "wav", "txt", "json",
  ],
  watermark: [
    "jpg", "jpeg", "png", "webp", "mp4", "mp3",
    "wav", "pdf",
  ],
};

function getExtension(fileName: string): string {
  const parts = fileName.toLowerCase().split(".");
  return parts.length > 1 ? parts.pop() ?? "" : "";
}

function hasSupportedExtension(file: File, mediaType: MediaType): boolean {
  const extension = getExtension(file.name);
  return SUPPORTED_EXTENSIONS[mediaType].includes(extension);
}

function validateRequest(request: DetectionRequest): void {
  const { mediaType, content, file, url } = request;

  if (file) {
    const validation = validateFile(file, mediaType);

    if (!validation.valid) {
      throw new Error(validation.error);
    }
  }

  if (url) {
    const validation = validateUrl(url);

    if (!validation.valid) {
      throw new Error(validation.error);
    }
  }

  switch (mediaType) {
    case "image":
    case "video":
      if (!file && !url) {
        throw new Error("Please provide an image or video file or URL.");
      }
      break;

    case "audio":
      if (!file) {
        throw new Error("Please upload an audio file.");
      }
      break;

    case "text":
      if (!content?.trim() && !file) {
        throw new Error("Please provide text to analyse.");
      }
      break;

    case "code":
      if (!content?.trim() && !file) {
        throw new Error("Please provide a source code file or snippet.");
      }
      break;

    case "embedding":
      if (!content?.trim() && !file && !url) {
        throw new Error("Please provide an asset or representation input.");
      }
      break;

    case "watermark":
      if (!file && !url && !content?.trim()) {
        throw new Error("Please provide an asset to inspect.");
      }
      break;

    default:
      throw new Error("Unsupported analysis category.");
  }
}

/**
 * Main analysis entry point.
 *
 * Actual detector adapters will be connected here.
 * This function deliberately does not generate simulated results.
 */
export async function performDetection(
  request: DetectionRequest,
): Promise<never> {
  validateRequest(request);

  const pipelineNames: Record<MediaType, string> = {
    image: "Image analysis",
    video: "Video analysis",
    audio: "Audio analysis",
    text: "Text analysis",
    code: "Code analysis",
    embedding: "Embedding analysis",
    watermark: "Watermark and provenance analysis",
  };

  throw new Error(
    `${pipelineNames[request.mediaType]} is not connected yet. ` +
    "The input was validated, but no analysis result was generated.",
  );
}

/**
 * Validate an uploaded file.
 */
export function validateFile(
  file: File,
  mediaType: MediaType,
): { valid: boolean; error?: string } {
  if (!file || file.size === 0) {
    return {
      valid: false,
      error: "The selected file is empty or unreadable.",
    };
  }

  if (file.size > MAX_FILE_SIZE) {
    return {
      valid: false,
      error: "File size exceeds the 100 MB upload limit.",
    };
  }

  const allowedMimeTypes = SUPPORTED_FORMATS[mediaType];
  const mimeType = file.type.toLowerCase();

  const validMimeType =
    mimeType !== "" && allowedMimeTypes.includes(mimeType);

  const validExtension = hasSupportedExtension(file, mediaType);

  // Some browsers do not provide a MIME type for source files.
  // In those cases, use the file extension as a fallback.
  if (!validMimeType && !validExtension) {
    return {
      valid: false,
      error: `Unsupported file format for ${mediaType} analysis.`,
    };
  }

  return { valid: true };
}

/**
 * Validate an HTTP or HTTPS URL.
 */
export function validateUrl(
  value: string,
): { valid: boolean; error?: string } {
  try {
    const parsedUrl = new URL(value.trim());

    if (!["http:", "https:"].includes(parsedUrl.protocol)) {
      return {
        valid: false,
        error: "Only HTTP and HTTPS URLs are supported.",
      };
    }

    return { valid: true };
  } catch {
    return {
      valid: false,
      error: "Invalid URL. Please enter a valid HTTP or HTTPS address.",
    };
  }
}