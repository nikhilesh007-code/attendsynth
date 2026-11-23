import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(val: number): string {
  return `${(val || 0).toFixed(1)}%`;
}

export function formatScore(val: number): string {
  return (val || 0).toFixed(1);
}
