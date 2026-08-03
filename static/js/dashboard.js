document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById("articlesByMonthChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const chartData = JSON.parse(canvas.dataset.chart);
    const context = canvas.getContext("2d");
    const gradient = context.createLinearGradient(0, 0, 0, 280);

    gradient.addColorStop(0, "rgba(37, 99, 235, .28)");
    gradient.addColorStop(1, "rgba(37, 99, 235, 0)");

    const datasets = chartData.datasets || [
        {
            label: "Artículos",
            data: chartData.values,
            borderColor: "#2563eb",
            backgroundColor: gradient,
            borderWidth: 2.5,
            fill: true,
            pointBackgroundColor: "#fff",
            pointBorderColor: "#2563eb",
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            tension: 0.38,
        },
    ];

    new Chart(context, {
        type: "line",
        data: { labels: chartData.labels, datasets },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: datasets.length > 1 } },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "#64748b", font: { family: "Inter" } },
                },
                y: {
                    beginAtZero: true,
                    border: { display: false },
                    grid: { color: "rgba(148, 163, 184, .18)" },
                    ticks: {
                        color: "#64748b",
                        precision: 0,
                        font: { family: "Inter" },
                    },
                },
            },
        },
    });
});
