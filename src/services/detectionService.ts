
import type {
  DetectionRequest,
  DetectionResult,
  MediaType,
} from "@/types/types";

const MAX_FILE_SIZE = 100 * 1024 * 1024;

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1"
).replace(/\/+$/, "");

const SUPPORTED_FORMATS: Record<MediaType, string[]> = {
  image: ["image/jpeg", "image/png", "image/gif", "image/webp"],
  video: ["video/mp4", "video/avi", "video/quicktime", "video/webm"],
  audio: ["audio/mpeg", "audio/wav", "audio/mp4", "audio/ogg", "audio/webm"],
  text: ["text/plain"],
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
    "py",
    "js",
    "jsx",
    "ts",
    "tsx",
    "cpp",
    "c",
    "h",
    "hpp",
    "java",
    "go",
    "rs",
    "php",
    "rb",
    "swift",
    "kt",
    "cs",
    "html",
    "css",
    "json",
  ],
  watermark: [
    "jpg",
    "jpeg",
    "png",
    "webp",
    "mp4",
    "mp3",
    "wav",
    "pdf",
  ],
};

function getExtension(fileName: string): string {
  const parts = fileName.toLowerCase().split(".");
  return parts.length > 1 ? parts.pop() ?? "" : "";
}

function hasSupportedExtension(
  file: File,
  mediaType: MediaType,
): boolean {
  return SUPPORTED_EXTENSIONS[mediaType].includes(
    getExtension(file.name),
  );
}

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

  const mimeType = file.type.toLowerCase();

  const validMimeType =
    mimeType !== "" &&
    SUPPORTED_FORMATS[mediaType].includes(mimeType);

  const validExtension = hasSupportedExtension(file, mediaType);

  if (!validMimeType && !validExtension) {
    return {
      valid: false,
      error: `Unsupported file format for ${mediaType} analysis.`,
    };
  }

  return { valid: true };
}

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
        throw new Error(
          "Please provide an image or video file or URL.",
        );
      }
      break;

    case "audio":
      if (!file) {
        throw new Error("Please upload an audio file.");
      }
      break;

    case "text":
    case "code":
      if (!content?.trim()) {
        throw new Error("Please provide content to analyze.");
      }
      break;

    case "watermark":
      if (!content?.trim() && !file && !url) {
        throw new Error(
          "Please provide an asset or representation input.",
        );
      }
      break;

    default:
      throw new Error("Unsupported analysis category.");
  }
}

function formatIndicator(indicator: unknown): string {
  if (typeof indicator === "string") {
    return indicator;
  }

  if (indicator && typeof indicator === "object") {
    const item = indicator as Record<string, unknown>;

    const description =
      item.description ??
      item.detail ??
      item.message ??
      item.name;

    if (typeof description === "string") {
      return description;
    }

    return Object.entries(item)
      .map(([key, value]) => `${key}: ${String(value)}`)
      .join(", ");
  }

  return String(indicator);
}

function normalizeResponse(data: unknown): DetectionResult {
  if (!data || typeof data !== "object") {
    throw new Error("The backend returned an invalid response.");
  }

  const response = data as Record<string, unknown>;

  const result = response.result;

  if (
    result !== "real" &&
    result !== "ai-generated" &&
    result !== "analysis-complete"
  ) {
    throw new Error("The backend returned an unsupported result type.");
  }

  let confidence: number | undefined;

  const hasConfidence =
    response.confidence !== undefined &&
    response.confidence !== null;

  if (hasConfidence) {
    const rawConfidence = Number(response.confidence);

    if (!Number.isFinite(rawConfidence)) {
      throw new Error(
        "The backend returned an invalid confidence score.",
      );
    }

    // Convert model confidence from 0–1 to frontend percentage.
    confidence =
      rawConfidence >= 0 && rawConfidence <= 1
        ? rawConfidence * 100
        : rawConfidence;

    if (confidence < 0 || confidence > 100) {
      throw new Error(
        "The backend returned a confidence score outside 0–100.",
      );
    }
  } else if (result !== "analysis-complete") {
    throw new Error(
      "The backend did not return a confidence score for its classification.",
    );
  }

  const indicators = Array.isArray(response.indicators)
    ? response.indicators.map(formatIndicator)
    : [];

  const metadata =
    response.metadata &&
    typeof response.metadata === "object" &&
    !Array.isArray(response.metadata)
      ? (response.metadata as Record<string, unknown>)
      : undefined;

  return {
    result,
    ...(confidence !== undefined ? { confidence } : {}),
    explanation:
      typeof response.explanation === "string"
        ? response.explanation
        : "Analysis completed.",
    indicators,
    ...(metadata ? { metadata } : {}),
    ...(response.codeBreakdown
      ? {
          codeBreakdown:
            response.codeBreakdown as DetectionResult["codeBreakdown"],
        }
      : {}),
    ...(response.watermarkBreakdown
      ? {
          watermarkBreakdown:
            response.watermarkBreakdown as DetectionResult["watermarkBreakdown"],
        }
      : {}),
  };
}

export async function performDetection(
  request: DetectionRequest,
): Promise<DetectionResult> {
  validateRequest(request);

  const formData = new FormData();

  if (request.content) {
    formData.append("content", request.content);
  }

  if (request.url) {
    formData.append("url", request.url);
  }

  if (request.languageHint) {
    formData.append("language_hint", request.languageHint);
  }

  // Send the original filename separately.
  // This is required when a .txt file is read and submitted as text content.
  if (request.filename) {
    formData.append("filename", request.filename);
  }

  if (request.file) {
    formData.append(
      "file",
      request.file,
      request.file.name,
    );
  }

  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/detect/${request.mediaType}`,
      {
        method: "POST",
        body: formData,
      },
    );
  } catch {
    throw new Error(
      "Cannot connect to the DeepShield backend. Make sure the FastAPI server is running on port 8000.",
    );
  }

  const data: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const errorData = data as
      | {
          detail?: string | Array<{ msg?: string }>;
        }
      | null;

    const detail = errorData?.detail;

    if (typeof detail === "string") {
      throw new Error(detail);
    }

    if (Array.isArray(detail)) {
      throw new Error(
        detail
          .map((item) => item.msg || "Invalid input")
          .join("; "),
      );
    }

    throw new Error(
      `Analysis failed with HTTP ${response.status}.`,
    );
  }

  return normalizeResponse(data);
}
