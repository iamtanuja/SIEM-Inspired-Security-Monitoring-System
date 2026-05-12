
async function fetchLogs() {
try {
const res = await fetch("/api/logs");
if (!res.ok) throw new Error("Failed to fetch logs");
const data = await res.json();
const tbody = document.getElementById("logs-container");
tbody.innerHTML = "";

data.forEach(log => {  
        const tr = document.createElement("tr");  
        tr.innerHTML = `
           <td>${log.time}</td>
           <td>${log.username}</td>
           <td>${log.action}</td>
           <td>${log.alert_type}</td>
           <td>${log.description}</td>
           <td class="severity ${log.severity.toLowerCase()}">${log.severity}</td>
           <td>${log.status || ""}</td>
        `;
        tbody.appendChild(tr);  
    });  
} catch (err) {  
    console.error("Error fetching logs:", err);  
}

}

setInterval(fetchLogs, 2000);
fetchLogs();

// ================= CLOCK =================
function updateClock() {
const now = new Date();
let hours = now.getHours();
const minutes = now.getMinutes().toString().padStart(2, '0');
const ampm = hours >= 12 ? 'PM' : 'AM';
hours = hours % 12 || 12;

document.getElementById('time').textContent = `${hours}:${minutes} ${ampm}`;  
const options = { weekday: 'short', month: 'short', day: 'numeric' };  
document.getElementById('date').textContent = now.toLocaleDateString('en-US', options);

}
setInterval(updateClock, 1000);
updateClock();

// ================= SCREENSHOT DETECTION =================
document.addEventListener("keydown", function(e) {
if (e.key === "PrintScreen") {
sendScreenshotAlert();
}
});

function sendScreenshotAlert() {
if (!CURRENT_USER) return;

fetch("/api/alerts", {  
    method: "POST",  
    headers: { "Content-Type": "application/json" },  
    body: JSON.stringify({   
        user: CURRENT_USER,   
        action: "SCREENSHOT_ATTEMPT",   
        severity: "CRITICAL"   
    })  
})  
.then(res => res.json())  
.then(data => console.log("Screenshot alert sent:", data))  
.catch(err => console.error("Alert error:", err));

}

// ================== SCREENSHOT DETECTION (SEND TO BACKEND) ==================
async function logScreenshotAttempt(details) {
    try {
        const logData = {
            event_type: 'SCREENSHOT_ATTEMPT',
            page_url: window.location.pathname,
            method: details.method || 'unknown',
            attempt_count: details.count || 1,
            user_agent: navigator.userAgent,
            severity: 'WARNING'
        };
        await fetch('/api/logs/screenshot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(logData)
        });
    } catch (error) {
        console.error('Failed to log screenshot attempt', error);
    }
}

// Detect screenshot shortcuts
document.addEventListener('keydown', function(event) {
    if (event.key === 'PrintScreen' || event.keyCode === 44) {
        logScreenshotAttempt({ method: 'PrintScreen' });
    }
    if (event.key === 's' && event.shiftKey && event.metaKey) {
        logScreenshotAttempt({ method: 'Win+Shift+S' });
    }
    if (event.metaKey && event.shiftKey && (event.key === '3' || event.key === '4')) {
        logScreenshotAttempt({ method: 'Mac+Screenshot' });
    }
});

// Disable right-click (optional)
document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    logScreenshotAttempt({ method: 'right-click' });
});

// ================== FETCH AND DISPLAY SCREENSHOT LOGS ==================
async function fetchScreenshotLogs() {
    try {
        const response = await fetch('/api/logs/screenshot');
        const logs = await response.json();
        const tbody = document.getElementById('screenshot-log-body');
        if (!logs.length) {
            tbody.innerHTML = '<tr><td colspan="5">No screenshot attempts yet.</td></tr>';
            return;
        }
        let html = '';
        logs.forEach(log => {
            const time = new Date(log.timestamp).toLocaleString();
            html += `<tr>
                <td>${time}</td>
                <td>${log.page_url}</td>
                <td>${log.method}</td>
                <td>${log.ip}</td>
                <td>${log.user_agent.substring(0, 50)}...</td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (error) {
        console.error('Error fetching screenshot logs', error);
    }
}

// Call initially and set interval
fetchScreenshotLogs();
setInterval(fetchScreenshotLogs, 10000); // har 10 sec refresh