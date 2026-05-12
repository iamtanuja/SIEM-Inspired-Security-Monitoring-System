async function loadReports() {
    try {
        const res = await fetch('/api/reports');
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const reports = await res.json();

        const container = document.getElementById('reports-list');
        if (!container) {
            console.error('Container #reports-list not found');
            return;
        }
        container.innerHTML = '';

        if (reports.length === 0) {
            container.innerHTML = '<div class="no-reports">No reports available.</div>';
            return;
        }

        reports.forEach(report => {
            const item = document.createElement('div');
            item.className = 'report-item';

            // Add severity class for border colour
            if (report.type.includes('Critical')) {
                item.classList.add('critical');
            } else if (report.type.includes('High')) {
                item.classList.add('high');
            } else if (report.type.includes('Medium')) {
                item.classList.add('medium');
            }

            item.innerHTML = `
                <div class="info">
                    <span class="date">${report.date}</span>
                    <span class="type">${report.type}</span>
                    <span class="count">${report.count} incident${report.count !== 1 ? 's' : ''}</span>
                </div>
                <a href="${report.download_url}" class="download-btn" download>
                    ⬇️ Download
                </a>
            `;
            container.appendChild(item);
        });
    } catch (error) {
        console.error('Failed to load reports:', error);
        document.getElementById('reports-list').innerHTML =
            `<div class="no-reports">Error loading reports: ${error.message}</div>`;
    }
}

// Load reports when page loads
loadReports();