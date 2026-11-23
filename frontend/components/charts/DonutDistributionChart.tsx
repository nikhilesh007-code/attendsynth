"use client";

import React from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import { useTheme } from "@/context/ThemeContext";

interface DonutDistributionChartProps {
  data: { name: string; value: number; color: string }[];
  title?: string;
}

export function DonutDistributionChart({ data, title }: DonutDistributionChartProps) {
  const { theme } = useTheme();
  const isLight = theme === "light";

  if (!data || data.length === 0 || data.every((d) => d.value === 0)) {
    return (
      <div className="h-48 flex items-center justify-center text-xs text-slate-500">
        No distribution data.
      </div>
    );
  }

  return (
    <div className="h-52 w-full flex flex-col items-center">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
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
            verticalAlign="bottom"
            iconType="circle"
            wrapperStyle={{ fontSize: "11px", paddingTop: "6px" }}
          />
          <Pie
            data={data}
            cx="50%"
            cy="45%"
            innerRadius={45}
            outerRadius={68}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color}
                stroke={isLight ? "#ffffff" : "#090e17"}
                strokeWidth={2}
              />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
