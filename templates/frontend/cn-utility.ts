/**
 * Tailwind CSS class merge utility.
 *
 * Combines clsx (conditional classes) with tailwind-merge
 * (deduplicates conflicting Tailwind classes).
 *
 * Usage:
 *   cn("px-4 py-2", isActive && "bg-blue-500", className)
 *
 * Install: npm install clsx tailwind-merge
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
