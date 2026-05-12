// ================== RISK LINE GRAPH ==================
const ctx = document.getElementById('riskLineGraph').getContext('2d');
const riskLineChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', 'Now'],
        datasets: [
            {
                label: 'Critical',
                data: [3, 5, 4, 7, 6, 8, 5],
                borderColor: '#ff3b3b',
                backgroundColor: 'rgba(255,59,59,0.1)',
                borderWidth: 2,
                pointBackgroundColor: '#ff3b3b',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                tension: 0.4,
                fill: false
            },
            {
                label: 'High',
                data: [5, 7, 6, 4, 8, 7, 9],
                borderColor: '#ff8c42',
                backgroundColor: 'rgba(255,140,66,0.1)',
                borderWidth: 2,
                pointBackgroundColor: '#ff8c42',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                tension: 0.4,
                fill: false
            },
            {
                label: 'Low',
                data: [8, 9, 7, 10, 8, 9, 12],
                borderColor: '#2ecc71',
                backgroundColor: 'rgba(46,204,113,0.1)',
                borderWidth: 2,
                pointBackgroundColor: '#2ecc71',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                tension: 0.4,
                fill: false
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { 
            legend: { 
                display: false // Hide default legend since we have custom one
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: '#1e2228',
                titleColor: '#fff',
                bodyColor: '#8a8f99',
                borderColor: '#2a2f38',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8,
                displayColors: true,
                callbacks: {
                    label: function(context) {
                        return `${context.dataset.label}: ${context.raw} alerts`;
                    }
                }
            }
        },
        scales: {
            x: { 
                grid: { 
                    display: false,
                    drawBorder: true,
                    color: '#2a2f38'
                },
                ticks: { 
                    color: '#8a8f99',
                    font: {
                        size: 12
                    }
                }
            },
            y: { 
                min: 0,
                max: 15,
                grid: { 
                    color: '#2a2f38',
                    drawBorder: false,
                    lineWidth: 1
                },
                ticks: { 
                    color: '#8a8f99',
                    stepSize: 3,
                    font: {
                        size: 12
                    },
                    callback: function(value) {
                        return value + ' alerts';
                    }
                }
            }
        },
        elements: {
            line: {
                borderJoinStyle: 'round',
                borderCapStyle: 'round'
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        },
        hover: {
            mode: 'nearest',
            intersect: false
        }
    }
});

// ================== REAL-TIME UPDATE FUNCTION ==================
function addRiskPoint(time, critical, high, low) {
    // Keep last 12 data points for better visualization
    const maxDataPoints = 12;
    const labels = riskLineChart.data.labels;
    const criticalData = riskLineChart.data.datasets[0].data;
    const highData = riskLineChart.data.datasets[1].data;
    const lowData = riskLineChart.data.datasets[2].data;
    
    // Initialize if empty (first time)
    if (labels.length === 0 || (labels.length === 1 && labels[0] === '00:00')) {
        // Clear initial dummy data
        riskLineChart.data.labels = [];
        riskLineChart.data.datasets[0].data = [];
        riskLineChart.data.datasets[1].data = [];
        riskLineChart.data.datasets[2].data = [];
    }
    
    // Add new data point
    labels.push(time);
    criticalData.push(critical);
    highData.push(high);
    lowData.push(low);
    
    // Remove oldest data point if exceeding max
    if (labels.length > maxDataPoints) {
        labels.shift();
        criticalData.shift();
        highData.shift();
        lowData.shift();
    }
    
    // Update y-axis max based on data
    const allValues = [...criticalData, ...highData, ...lowData];
    const maxValue = Math.max(...allValues);
    riskLineChart.options.scales.y.max = Math.ceil(maxValue * 1.2); // Add 20% padding
    
    riskLineChart.update('none');
}

// ================== FETCH ALERTS ==================
async function fetchRiskData() {
    try {
        const res = await fetch("/api/alerts");
        const data = await res.json();

        let critical = 0, high = 0, low = 0, unauthorized = 0;

        data.forEach(alert => {
            if (alert.severity === "CRITICAL") critical++;
            else if (alert.severity === "HIGH") high++;
            else low++;

            if (alert.action === "PROJECT_ACCESS_DENIED" || alert.action === "PROFILE_ACCESS_DENIED") unauthorized++;
        });

        // Update top cards
        document.getElementById('critical-count').textContent = critical;
        document.getElementById('high-count').textContent = high;
        document.getElementById('low-count').textContent = low;
        document.getElementById('unauth-count').textContent = unauthorized;

        const timeLabel = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
        });
        addRiskPoint(timeLabel, critical, high, low);

    } catch (err) {
        console.error("Error fetching alerts:", err);
    }
}

// Initialize with some sample data for better visualization
function initializeChart() {
    const now = new Date();
    for (let i = 11; i >= 0; i--) {
        const pastTime = new Date(now.getTime() - i * 5 * 60000); // 5 minute intervals
        const timeLabel = pastTime.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
        });
        
        // Generate sample data that looks natural
        const critical = Math.floor(Math.random() * 4) + 2; // 2-6
        const high = Math.floor(Math.random() * 5) + 3; // 3-8
        const low = Math.floor(Math.random() * 6) + 5; // 5-11
        
        riskLineChart.data.labels.push(timeLabel);
        riskLineChart.data.datasets[0].data.push(critical);
        riskLineChart.data.datasets[1].data.push(high);
        riskLineChart.data.datasets[2].data.push(low);
    }
    riskLineChart.update();
}

// Call initialize function
initializeChart();

// ================== REFRESH DATA ==================
setInterval(fetchRiskData, 5000); // Changed to 5 seconds for better performance
fetchRiskData();

