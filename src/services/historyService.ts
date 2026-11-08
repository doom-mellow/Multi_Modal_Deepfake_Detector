import { supabase } from "@/db/supabase";

import type {
  HistoryRecord,
  DetectionResultType,
  MediaType,
} from "@/types/types";

interface ServiceResult {
  success: boolean;
  error?: string;
}

interface HistoryListResult {
  data: HistoryRecord[];
  total: number;
  error?: string;
}

interface SingleHistoryResult {
  data: HistoryRecord | null;
  error?: string;
}

function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function isValidConfidence(confidence: number): boolean {
  return (
    Number.isFinite(confidence) &&
    confidence >= 0 &&
    confidence <= 100
  );
}

function isValidMediaType(value: string): value is MediaType {
  return [
    "image",
    "video",
    "audio",
    "text",
    "code",
    "embedding",
    "watermark",
  ].includes(value);
}

function isValidResult(value: string): value is DetectionResultType {
  return value === "real" || value === "ai-generated";
}

/**
 * Save a detection result to the history table.
 */
export async function saveToHistory(
  mediaType: MediaType,
  result: DetectionResultType,
  confidence: number,
  contentPreview: string | null,
  fileName: string | null,
  metadata?: Record<string, unknown> | null,
): Promise<ServiceResult> {
  if (!isValidMediaType(mediaType)) {
    return {
      success: false,
      error: "Invalid analysis category.",
    };
  }

  if (!isValidResult(result)) {
    return {
      success: false,
      error: "Invalid detection result.",
    };
  }

  if (!isValidConfidence(confidence)) {
    return {
      success: false,
      error: "Confidence must be between 0 and 100.",
    };
  }

  try {
    const { error } = await supabase
      .from("detection_history")
      .insert({
        media_type: mediaType,
        result,
        confidence,
        content_preview: contentPreview,
        file_name: fileName,
        metadata: metadata ?? null,
      });

    if (error) {
      console.error("Failed to save detection history:", error);

      return {
        success: false,
        error: error.message,
      };
    }

    return { success: true };
  } catch (error: unknown) {
    console.error("Unexpected history save error:", error);

    return {
      success: false,
      error: getErrorMessage(
        error,
        "Unable to save the analysis record.",
      ),
    };
  }
}

/**
 * Retrieve paginated detection history.
 */
export async function fetchHistory(
  page = 1,
  pageSize = 10,
): Promise<HistoryListResult> {
  if (
    !Number.isInteger(page) ||
    page < 1 ||
    !Number.isInteger(pageSize) ||
    pageSize < 1
  ) {
    return {
      data: [],
      total: 0,
      error: "Page and page size must be positive integers.",
    };
  }

  try {
    const from = (page - 1) * pageSize;
    const to = from + pageSize - 1;

    const { data, error, count } = await supabase
      .from("detection_history")
      .select("*", { count: "exact" })
      .order("created_at", { ascending: false })
      .range(from, to);

    if (error) {
      console.error("Failed to fetch detection history:", error);

      return {
        data: [],
        total: 0,
        error: error.message,
      };
    }

    return {
      data: (data ?? []) as HistoryRecord[],
      total: count ?? 0,
    };
  } catch (error: unknown) {
    console.error("Unexpected history retrieval error:", error);

    return {
      data: [],
      total: 0,
      error: getErrorMessage(
        error,
        "Unable to retrieve detection history.",
      ),
    };
  }
}

/**
 * Delete a history record by its ID.
 */
export async function deleteHistoryRecord(
  id: string,
): Promise<ServiceResult> {
  if (!id.trim()) {
    return {
      success: false,
      error: "A valid record ID is required.",
    };
  }

  try {
    const { error } = await supabase
      .from("detection_history")
      .delete()
      .eq("id", id);

    if (error) {
      console.error("Failed to delete history record:", error);

      return {
        success: false,
        error: error.message,
      };
    }

    return { success: true };
  } catch (error: unknown) {
    console.error("Unexpected history deletion error:", error);

    return {
      success: false,
      error: getErrorMessage(
        error,
        "Unable to delete the history record.",
      ),
    };
  }
}

/**
 * Retrieve one history record by ID.
 */
export async function fetchHistoryRecord(
  id: string,
): Promise<SingleHistoryResult> {
  if (!id.trim()) {
    return {
      data: null,
      error: "A valid record ID is required.",
    };
  }

  try {
    const { data, error } = await supabase
      .from("detection_history")
      .select("*")
      .eq("id", id)
      .maybeSingle();

    if (error) {
      console.error("Failed to fetch history record:", error);

      return {
        data: null,
        error: error.message,
      };
    }

    return {
      data: data as HistoryRecord | null,
    };
  } catch (error: unknown) {
    console.error("Unexpected single-record retrieval error:", error);

    return {
      data: null,
      error: getErrorMessage(
        error,
        "Unable to retrieve the requested record.",
      ),
    };
  }
}