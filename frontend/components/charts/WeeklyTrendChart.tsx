"use client";

import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { WeeklyTrend } from "@/types";
import { useTheme } from "@/context/ThemeContext";

interface WeeklyTrendChartProps {
  data: WeeklyTrend[];
}

export function WeeklyTrendChart({ data }: WeeklyTrendChartProps) {
  const { theme } = useTheme();
  const isLight = theme === "light";

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-500">
        No longitudinal weekly records available.
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={isLight ? "#e2e8f0" : "#1e293b"} />
          <XAxis dataKey="week" stroke={isLight ? "#64748b" : "#94a3b8"} fontSize={11} tickLine={false} />
          <YAxis stroke={isLight ? "#64748b" : "#94a3b8"} fontSize={11} domain={[0, 100]} tickLine={false} />
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
          <Legend
            verticalAlign="top"
            align="right"
            iconType="circle"
            wrapperStyle={{ fontSize: "11px", paddingBottom: "8px" }}
          />
          <Line
            type="monotone"
            dataKey="avg_engagement"
            name="Engagement Index"
            stroke={isLight ? "#059669" : "#10b981"}
            strokeWidth={2.5}
            dot={{ r: 3, fill: isLight ? "#059669" : "#10b981" }}
            activeDot={{ r: 5 }}
          />
          <Line
            type="monotone"
            dataKey="avg_attendance"
            name="Attendance %"
            stroke={isLight ? "#0284c7" : "#38bdf8"}
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
