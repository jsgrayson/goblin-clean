async function updateStatus() {
    try {
        let res = await fetch("/ui/status");
        let data = await res.json();

        // Update system metrics
        document.getElementById("cpu").innerText = data.cpu + "%";
        document.getElementById("mem").innerText = data.mem + "%";
        document.getElementById("disk").innerText = data.disk + "%";

        // Update agent colored dots
        for (const agent in data.agents) {
            let el = document.getElementById("agent-" + agent);
            if (el) el.className = "status-dot " + data.agents[agent];
        }

        // Update container list
        let contDiv = document.getElementById("containers");
        contDiv.innerHTML = "";
        data.containers.forEach(c => {
            contDiv.innerHTML += `
                <div class="container-card">
                    <strong>${c.name}</strong><br>
                    Status: ${c.status}
                </div>`;
        });

    } catch (err) {
        console.log("Status update failed:", err);
    }
}

setInterval(updateStatus, 5000);
updateStatus();


// ---------------------------------------------------------
// STEP 4 — SPINNER HELPERS
// ---------------------------------------------------------

function showSpinner(btn) {
    btn.dataset.original = btn.innerHTML;
    btn.innerHTML = btn.innerHTML + ' <span class="spinner"></span>';
}

function hideSpinner(btn) {
    if (btn.dataset.original) {
        btn.innerHTML = btn.dataset.original;
        delete btn.dataset.original;
    }
}


// ---------------------------------------------------------
// AGENT ACTIONS
// ---------------------------------------------------------

async function agentAction(agent, action) {
    try {
        const buttons = document.querySelectorAll(`.agent-card button`);
        const clicked = event.target;

        // Disable all buttons during action
        buttons.forEach(b => b.disabled = true);

        // Show loading spinner on clicked button
        showSpinner(clicked);

        let toast = document.getElementById("toast");
        toast.style.display = "block";
        toast.innerText = `Running ${action} on ${agent}...`;

        let res = await fetch(`/ui/actions/${action}/${agent}`, {
            method: "POST"
        });
        let data = await res.json();

        if (data.status === "ok") {
            toast.innerText = `${agent} ${action} completed`;
        } else {
            toast.innerText = `Error: ${data.message || "Unknown failure"}`;
        }

        hideSpinner(clicked);
        buttons.forEach(b => b.disabled = false);

        setTimeout(() => { toast.style.display = "none"; }, 4000);

        updateStatus();

    } catch (err) {
        console.log("Agent action failed:", err);

        const buttons = document.querySelectorAll(`.agent-card button`);
        buttons.forEach(b => b.disabled = false);

        hideSpinner(event.target);

        let toast = document.getElementById("toast");
        toast.style.display = "block";
        toast.innerText = "Action failed";
        setTimeout(() => { toast.style.display = "none"; }, 4000);
    }
}


// ---------------------------------------------------------
// SYSTEM ACTIONS (backup, update)
// ---------------------------------------------------------

async function systemAction(action) {
    try {
        const sysButtons = document.querySelectorAll(`.sys-btn`);
        const clicked = event.target;

        sysButtons.forEach(b => b.disabled = true);
        showSpinner(clicked);

        let toast = document.getElementById("toast");
        toast.style.display = "block";
        toast.innerText = `Running: ${action}...`;

        let res = await fetch(`/ui/actions/${action}`, { method: "POST" });
        let data = await res.json();

        if (data.status === "ok") {
            toast.innerText = `${action} completed successfully`;
        } else {
            toast.innerText = `Error: ${data.message || "Unknown failure"}`;
        }

        hideSpinner(clicked);
        sysButtons.forEach(b => b.disabled = false);

        setTimeout(() => { toast.style.display = "none"; }, 4000);

        updateStatus();

    } catch (err) {
        const sysButtons = document.querySelectorAll(`.sys-btn`);
        sysButtons.forEach(b => b.disabled = false);

        hideSpinner(event.target);

        let toast = document.getElementById("toast");
        toast.style.display = "block";
        toast.innerText = "System action failed";
        setTimeout(() => { toast.style.display = "none"; }, 4000);
    }
}
/* ---------------------------------------------------------
   STEP 5 — LOG VIEWER FUNCTIONS
--------------------------------------------------------- */

let currentLogAgent = null;

async function openLogs(agent) {
    currentLogAgent = agent;
    document.getElementById("logModal").style.display = "block";
    document.getElementById("logText").innerText = "(loading logs...)";
    refreshLogs();
}

async function refreshLogs() {
    if (!currentLogAgent) return;

    try {
        let res = await fetch(`/ui/logs/${currentLogAgent}`);
        let data = await res.json();

        if (data.status === "ok") {
            document.getElementById("logText").innerText = data.log;
        } else {
            document.getElementById("logText").innerText =
                "Error: " + (data.message || "unknown");
        }

    } catch (err) {
        document.getElementById("logText").innerText =
            "Network error loading logs.";
    }
}

function closeLogs() {
    document.getElementById("logModal").style.display = "none";
}

/* ---------------------------------------------------------
   STEP 6 — CHARTS (CPU / MEM / DISK / CONTAINERS)
--------------------------------------------------------- */

let cpuChart, memChart, diskChart, containerChart;

// Create empty datasets on page load
function initCharts() {
    const chartOptions = {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '',
                data: [],
                borderColor: '#40c4ff',
                backgroundColor: 'rgba(64,196,255,0.1)',
                borderWidth: 2,
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    };

    cpuChart = new Chart(document.getElementById('cpuChart'), JSON.parse(JSON.stringify(chartOptions)));
    cpuChart.data.datasets[0].label = "CPU %";

    memChart = new Chart(document.getElementById('memChart'), JSON.parse(JSON.stringify(chartOptions)));
    memChart.data.datasets[0].label = "Memory %";

    diskChart = new Chart(document.getElementById('diskChart'), JSON.parse(JSON.stringify(chartOptions)));
    diskChart.data.datasets[0].label = "Disk %";

    containerChart = new Chart(document.getElementById('containerChart'), JSON.parse(JSON.stringify(chartOptions)));
    containerChart.data.datasets[0].label = "Containers Running";
}

// Append a datapoint to a chart
function addPoint(chart, value) {
    const now = new Date().toLocaleTimeString();
    chart.data.labels.push(now);
    chart.data.datasets[0].data.push(value);

    // Keep only the last 20 points
    if (chart.data.labels.length > 20) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    chart.update();
}

// Patch updateStatus() to update charts
const originalUpdateStatus = updateStatus;

updateStatus = async function() {
    await originalUpdateStatus();

    // Grab updated values from UI
    const cpu = parseFloat(document.getElementById("cpu").innerText);
    const mem = parseFloat(document.getElementById("mem").innerText);
    const disk = parseFloat(document.getElementById("disk").innerText);
    const cont = document.getElementById("containers").children.length;

    addPoint(cpuChart, cpu);
    addPoint(memChart, mem);
    addPoint(diskChart, disk);
    addPoint(containerChart, cont);
};

// Initialize charts on page load
window.addEventListener("load", initCharts);

