// Data path:
// button -> fetch -> Flask endpoint -> SQLAlchemy -> pandas -> JSON -> Chart.js

const API = "/api";

// Names EXACTLY as the REN API returns them. Do not translate:
// these are data values, not interface text. Translating them here
// would make the filter match nothing.
const SOURCES = ["Solar", "Eólica", "Hídrica", "Biomassa", "Gás Natural"];

// English labels for display. Keeping the value and the label apart
// lets the interface be in one language and the data in another,
// without touching the data.
const LABELS = {
    "Solar": "Solar",
    "Eólica": "Wind",
    "Hídrica": "Hydro",
    "Biomassa": "Biomass",
    "Gás Natural": "Natural gas",
};

const COLORS = {
    "Solar": "#f59e0b",
    "Eólica": "#0ea5e9",
    "Hídrica": "#2563eb",
    "Biomassa": "#16a34a",
    "Gás Natural": "#9ca3af",
};

// Kept so they can be destroyed before redrawing.
// Without this, Chart.js stacks charts on top of each other.
let timelineChart = null;
let correlationChart = null;


/** Returns the date N days ago, in the YYYY-MM-DD format the API expects. */
function startDateFor(days) {
    const d = new Date();
    d.setDate(d.getDate() - days);
    return d.toISOString().slice(0, 10);
}


/** Fetches JSON from the API, with a readable error if it fails. */
async function getJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`${url} responded ${response.status}`);
    }
    return response.json();
}


function showError(message) {
    const box = document.getElementById("error");
    box.textContent = "Failed to load data: " + message;
    box.style.display = "block";
}


// ---------- KPIs ----------

function renderKpis(insights) {
    document.getElementById("kpi-pct").textContent =
        insights.avg_renewable_pct + "%";

    document.getElementById("kpi-pct-note").textContent =
        `${insights.period_days}-day average`;

    document.getElementById("kpi-best").textContent =
        insights.best_day.renewable_pct + "%";

    document.getElementById("kpi-best-note").textContent =
        insights.best_day.day;

    // Translate the source name, falling back to the original
    const source = insights.most_volatile_source;
    document.getElementById("kpi-volatile").textContent =
        LABELS[source] ?? source;
}


// ---------- Chart 1: timeline ----------

function renderTimeline(records) {
    // The API returns a flat list: [{day, source, avg_mw}, ...]
    // Chart.js needs one series per source, all aligned to the same
    // days, so the data has to be pivoted.

    const days = [...new Set(records.map(r => r.day))].sort();

    // Fast lookup: "2026-05-18|Solar" -> 1304.3
    const lookup = {};
    records.forEach(r => {
        lookup[r.day + "|" + r.source] = r.avg_mw;
    });

    const datasets = SOURCES.map(source => ({
        label: LABELS[source],
        data: days.map(day => lookup[day + "|" + source] ?? null),
        borderColor: COLORS[source],
        backgroundColor: COLORS[source],
        borderWidth: 1.8,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.25,
    }));

    if (timelineChart) timelineChart.destroy();

    timelineChart = new Chart(document.getElementById("timeline"), {
        type: "line",
        data: { labels: days, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { position: "bottom", labels: { boxWidth: 12 } },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y} MW`,
                    },
                },
            },
            scales: {
                x: { ticks: { maxTicksLimit: 12 }, grid: { display: false } },
                y: {
                    title: { display: true, text: "MW (daily average)" },
                    beginAtZero: true,
                },
            },
        },
    });
}


// ---------- Chart 2: correlations ----------

function renderCorrelation(results) {
    // results: [{source, correlations: {...}}, ...]
    const labels = results.map(r => LABELS[r.source] ?? r.source);

    const variables = [
        { key: "shortwave_radiation", name: "Solar radiation", color: "#f59e0b" },
        { key: "wind_speed_kmh", name: "Wind speed", color: "#0ea5e9" },
        { key: "temperature_c", name: "Temperature", color: "#ef4444" },
    ];

    const datasets = variables.map(v => ({
        label: v.name,
        data: results.map(r => r.correlations[v.key]),
        backgroundColor: v.color,
        borderRadius: 3,
    }));

    if (correlationChart) correlationChart.destroy();

    correlationChart = new Chart(document.getElementById("correlation"), {
        type: "bar",
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom", labels: { boxWidth: 12 } },
            },
            scales: {
                // Pearson correlation always sits between -1 and 1.
                // Fixing the scale stops the chart exaggerating
                // small differences.
                y: {
                    min: -1,
                    max: 1,
                    title: { display: true, text: "Correlation coefficient" },
                },
                x: { grid: { display: false } },
            },
        },
    });
}


// ---------- Loading ----------

async function loadAll(days) {
    const start = startDateFor(days);

    try {
        // All requests go out at once instead of waiting for each
        // other. Promise.all waits for them all to finish.
        const [insights, timeline, correlations] = await Promise.all([
            getJSON(`${API}/insights?start=${start}`),
            getJSON(`${API}/production/timeline?start=${start}`),
            Promise.all(
                SOURCES.map(source =>
                    getJSON(
                        `${API}/correlation/weather-production` +
                        `?source=${encodeURIComponent(source)}&start=${start}`
                    )
                )
            ),
        ]);

        renderKpis(insights);
        renderTimeline(timeline);
        renderCorrelation(correlations);

        document.getElementById("error").style.display = "none";
    } catch (error) {
        showError(error.message);
    }
}


// Wire up the buttons and load the initial period
document.querySelectorAll(".periods button").forEach(button => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".periods button")
            .forEach(b => b.classList.remove("active"));
        button.classList.add("active");
        loadAll(Number(button.dataset.days));
    });
});

loadAll(180);