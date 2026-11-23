import React from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

const variantStyles = {
  default:
    "border-emerald-200 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10",
  success:
    "border-emerald-200 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10",
  warning:
    "border-amber-200 dark:border-amber-500/30 text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10",
  danger:
    "border-rose-200 dark:border-rose-500/30 text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-500/10",
  info:
    "border-sky-200 dark:border-sky-500/30 text-sky-700 dark:text-sky-400 bg-sky-50 dark:bg-sky-500/10",
};

export function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = "default",
}: KPICardProps) {
  return (
    <div className="saas-card p-4 flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700 transition">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          {title}
        </span>
        <div className={cn("p-2 rounded-lg border", variantStyles[variant])}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white font-mono">
          {value}
        </span>
        {trend && (
          <span
            className={cn(
              "text-xs font-semibold",
              trend.isPositive ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
            )}
          >
            {trend.value}
          </span>
        )}
      </div>
      {subtitle && (
        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 truncate">
          {subtitle}
        </p>
      )}
    </div>
  );
}
