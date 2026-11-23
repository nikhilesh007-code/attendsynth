"use client";

import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { useTheme } from "@/context/ThemeContext";

interface DistributionBarChartProps {
  data: { bin?: string; course?: string; count?: number; engagement?: number; attendance?: number }[];
  xKey: string;
  barKey: string;
  barName: string;
  color?: string;
}

export function DistributionBarChart({
  data,
  xKey,
  barKey,
  barName,
  color,
}: DistributionBarChartProps) {
  const { theme } = useTheme();
  const isLight = theme === "light";
  const defaultBarColor = color || (isLight ? "#059669" : "#10b981");

  if (!data || data.length === 0) {
    return (
      <div className="h-52 flex items-center justify-center text-xs text-slate-500">
        No bar distribution data.
      </div>
    );
  }

  return (
    <div className="h-52 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={isLight ? "#e2e8f0" : "#1e293b"} vertical={false} />
          <XAxis
            dataKey={xKey}
            stroke={isLight ? "#64748b" : "#94a3b8"}
            fontSize={10}
            tickLine={false}
            tickFormatter={(val) => (val.length > 14 ? `${val.slice(0, 12)}…` : val)}
          />
          <YAxis stroke={isLight ? "#64748b" : "#94a3b8"} fontSize={10} tickLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: isLight ? "#ffffff" : "#090e17",
              borderColor: isLight ? "#e2e8f0" : "#1e293b",
              borderRadius: "0.5rem",
              fontSize: "12px",
              color: isLight ? "#0f172a" : "#f8fafc",
              boxShadow: isLight ? "0 4px 6px -1px rgba(0, 0, 0, 0.08)" : "none",
            }}
          />
          <Bar dataKey={barKey} name={barName} fill={defaultBarColor} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
