import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
} from "chart.js";
import { useMemo } from "react";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

function formatLabel(rawDate) {
  const date = new Date(rawDate);
  if (Number.isNaN(date.getTime())) {
    return String(rawDate ?? "-");
  }
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function PerformanceChart({ data = [] }) {
  const labels = useMemo(
    () => data.map((item) => formatLabel(item?.date)),
    [data],
  );
  const values = useMemo(
    () => data.map((item) => Number(item?.average_score ?? 0)),
    [data],
  );

  const chartData = useMemo(
    () => ({
      labels,
      datasets: [
        {
          label: "Average Score",
          data: values,
          borderColor: "#00d4ff",
          borderWidth: 2.5,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: "#8b5cf6",
          fill: true,
          tension: 0.35,
          backgroundColor: (context) => {
            const chart = context.chart;
            const { ctx, chartArea } = chart;
            if (!chartArea) {
              return "rgba(0, 212, 255, 0.12)";
            }
            const gradient = ctx.createLinearGradient(
              0,
              chartArea.top,
              0,
              chartArea.bottom,
            );
            gradient.addColorStop(0, "rgba(0, 212, 255, 0.35)");
            gradient.addColorStop(1, "rgba(0, 212, 255, 0.02)");
            return gradient;
          },
        },
      ],
    }),
    [labels, values],
  );

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: "rgba(15,23,42,0.95)",
          borderColor: "rgba(0,212,255,0.35)",
          borderWidth: 1,
          titleColor: "#c7f6ff",
          bodyColor: "#e2e8f0",
          callbacks: {
            label: (context) => ` Score: ${Math.round(context.parsed.y)}%`,
          },
        },
      },
      scales: {
        x: {
          grid: {
            color: "rgba(148,163,184,0.12)",
            drawBorder: false,
          },
          ticks: {
            color: "#a5b4fc",
            maxRotation: 0,
          },
        },
        y: {
          min: 0,
          max: 100,
          ticks: {
            color: "#94a3b8",
            callback: (value) => `${value}%`,
          },
          grid: {
            color: "rgba(148,163,184,0.12)",
            drawBorder: false,
          },
        },
      },
      interaction: {
        intersect: false,
        mode: "index",
      },
    }),
    [],
  );

  return (
    <div className="h-72 md:h-80 w-full">
      <Line data={chartData} options={options} />
    </div>
  );
}
