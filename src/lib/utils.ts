import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combine conditional class names and resolve Tailwind conflicts.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export type Params = Record<
  string,
  string | number | null | undefined
>;

/**
 * Create an updated query string while preserving existing parameters.
 *
 * Null or undefined values remove the corresponding parameter.
 */
export function createQueryString(
  params: Params,
  searchParams: URLSearchParams,
): string {
  const updatedParams = new URLSearchParams(searchParams.toString());

  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined) {
      updatedParams.delete(key);
    } else {
      updatedParams.set(key, String(value));
    }
  }

  return updatedParams.toString();
}

/**
 * Format a date using the Indian English locale.
 */
export function formatDate(
  date: Date | string | number,
  options: Intl.DateTimeFormatOptions = {},
): string {
  const parsedDate = new Date(date);

  if (Number.isNaN(parsedDate.getTime())) {
    return "Invalid date";
  }

  return new Intl.DateTimeFormat("en-IN", {
    month: "long",
    day: "numeric",
    year: "numeric",
    ...options,
  }).format(parsedDate);
}