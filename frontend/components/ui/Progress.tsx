import React from "react";
import { cn } from "@/lib/utils";

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0 to 100
  max?: number;
  indicatorColor?: "emerald" | "blue" | "amber" | "rose" | "purple";
  size?: "sm" | "md" | "lg";
}

export function Progress({
  className,
  value = 0,
  max = 100,
  indicatorColor = "emerald",
  size = "md",
  ...props
}: ProgressProps) {
  const percentage = Math.min(Math.max(0, (value / max) * 100), 100);

  const colorStyles = {
    emerald: "bg-emerald-500",
    blue: "bg-sky-500",
    amber: "bg-amber-500",
    rose: "bg-rose-500",
    purple: "bg-purple-500",
  };

  const sizeStyles = {
    sm: "h-1.5",
    md: "h-2.5",
    lg: "h-3.5",
  };

  return (
    <div
      className={cn("w-full overflow-hidden rounded-full bg-slate-800/80 border border-slate-700/50", sizeStyles[size], className)}
      {...props}
    >
      <div
        className={cn("h-full transition-all duration-500 ease-out rounded-full", colorStyles[indicatorColor])}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}
