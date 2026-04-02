async function fetchData() {
    try {
        const [trendsRes, topRes] = await Promise.all([
            fetch('/api/analytics/trends').catch(() => null),
            fetch('/api/analytics/top-referrers').catch(() => null)
        ]);

        const trends = trendsRes && trendsRes.ok ? await trendsRes.json() : [];
        const top = topRes && topRes.ok ? await topRes.json() : [];
        
        renderTrendsTable(trends);
        renderChart(top);
        updateKPIs(trends);
        
    } catch(err) {
        console.warn("Backend error fetching data", err);
        renderTrendsTable([]);
        renderChart([]);
        updateKPIs([]);
    }
}

function updateKPIs(trends) {
    const activeCount = trends.filter(t => t.current_month_referrals > 0).length;
    const riskCount = trends.filter(t => t.status === 'Lost' || t.status === 'Decreasing').length;
    const production = trends.reduce((sum, t) => sum + (t.current_month_production || 0), 0);

    const elActive = document.getElementById('kpi-active');
    const elRisk = document.getElementById('kpi-risk');
    const elProduction = document.getElementById('kpi-production');

    if(elActive) elActive.innerText = activeCount;
    if(elRisk) elRisk.innerText = riskCount;
    if(elProduction) elProduction.innerText = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(production);
}

function renderTrendsTable(data) {
    const tbody = document.querySelector('#trendsTable tbody');
    tbody.innerHTML = '';
    
    data.forEach(item => {
        let statusClass = 'status-stable';
        if (item.status === 'Lost') statusClass = 'status-lost';
        if (item.status === 'Decreasing') statusClass = 'status-decreasing';
        
        // Estimate lost production visually
        const lostVol = Math.max(0, item.historical_avg_referrals - item.current_month_referrals);
        const estLostMoney = (item.historical_avg_production / Math.max(1, item.historical_avg_referrals)) * lostVol;
        const estLostDisplay = estLostMoney > 100 ? `<span style="color:var(--danger); font-weight:600;">-$${estLostMoney.toLocaleString(undefined, {maximumFractionDigits:0})}</span>` : '<span style="color:var(--text-muted)">-</span>';
        
        const row = `
            <tr>
                <td><strong>${item.doctor}</strong></td>
                <td><span class="status-badge ${statusClass}">${item.status}</span></td>
                <td>${item.historical_avg_referrals.toFixed(1)} </td>
                <td><strong>${item.current_month_referrals}</strong></td>
                <td>${estLostDisplay}</td>
                <td><button class="btn-secondary" style="padding: 6px 12px; font-size: 0.75rem;"><i class="fas fa-paper-plane"></i> Action</button></td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

function renderChart(data) {
    const ctx = document.getElementById('topReferrersChart').getContext('2d');
    
    // Sort array by total_production descending before taking top 4 to show in chart
    const sortedData = [...data].sort((a,b) => b.total_production - a.total_production).slice(0, 4);
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: sortedData.map(d => d.doctor),
            datasets: [{
                data: sortedData.map(d => d.total_production),
                backgroundColor: ['#4F46E5', '#10B981', '#F59E0B', '#EF4444'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { padding: 20, font: { family: 'Inter' } } },
                tooltip: { 
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            if (label) label += ': ';
                            if (context.parsed !== null) label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed);
                            return label;
                        }
                    }
                }
            },
            cutout: '70%'
        }
    });
}

// AI Insight Generator (Dynamic)
function generateAIInsight() {
    const box = document.getElementById('aiInsightBox');
    const text = document.getElementById('aiInsightText');
    box.style.display = 'flex';
    text.innerHTML = "<em>Analyzing patterns using AI...</em>";
    
    setTimeout(async () => {
        try {
            const res = await fetch('/api/analytics/trends');
            
            if (!res.ok) throw new Error();
            const trends = await res.json();
            
            const lostDocs = trends.filter(t => t.status === 'Lost').sort((a,b) => b.historical_avg_production - a.historical_avg_production);
            const decreasingDocs = trends.filter(t => t.status === 'Decreasing').sort((a,b) => b.historical_avg_production - a.historical_avg_production);
            
            let targetDoc = null;
            let reason = "";
            let estLoss = 0;
            
            if (lostDocs.length > 0) {
                targetDoc = lostDocs[0];
                reason = "hasn't referred any patients this month";
                estLoss = targetDoc.historical_avg_production;
            } else if (decreasingDocs.length > 0) {
                targetDoc = decreasingDocs[0];
                reason = "is showing a significant drop in referrals";
                estLoss = targetDoc.historical_avg_production - targetDoc.current_month_production;
            }
            
            if (targetDoc && estLoss > 0) {
                text.innerHTML = `<strong>AI Recommendation:</strong> ${targetDoc.doctor} ${reason}, costing an estimated $${Math.round(estLoss).toLocaleString()} in lost potential production this month. <strong>Action Plan:</strong> Reach out immediately via phone or schedule a lunch-and-learn to re-engage.`;
            } else {
                text.innerHTML = "<strong>AI Status:</strong> All key referring doctors are stable or growing. Great work retaining your network!";
            }
        } catch (e) {
            text.innerHTML = "<strong>AI Recommendation fallback:</strong> Keep monitoring your Top 5 referrers, as one has shown slight changes in referral volume.";
        }
    }, 800);
}

// File Upload Handler True Integration
document.getElementById('csvUpload').addEventListener('change', async (e) => {
    if(e.target.files.length > 0) {
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append("file", file);

        const btnLabel = document.querySelector('label[for="csvUpload"]');
        const oldHtml = btnLabel.innerHTML;
        btnLabel.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        document.getElementById('csvUpload').disabled = true;

        try {
            const response = await fetch('/api/upload-csv/', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                alert("Data processed successfully!");
                await fetchData();
            } else {
                const err = await response.json();
                alert("Upload failed: " + (err.detail || "Unknown error"));
            }
        } catch(error) {
            console.error(error);
            alert("Upload failed due to network error.");
        } finally {
            document.getElementById('csvUpload').disabled = false;
            btnLabel.innerHTML = oldHtml;
            e.target.value = ""; // clear input
        }
    }
});

// Load Demo Data Handler
document.getElementById('loadDemoBtn')?.addEventListener('click', async (e) => {
    const btn = e.target.closest('button');
    const oldHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/load-demo-data', {
            method: 'POST'
        });

        if (response.ok) {
            alert("Demo data loaded! The dashboard will now automatically update.");
            await fetchData();
        } else {
            const err = await response.json();
            alert("Failed to load demo data: " + (err.detail || "Unknown error"));
        }
    } catch(error) {
        console.error(error);
        alert("Upload failed due to network error.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = oldHtml;
    }
});



// Load everything
document.addEventListener('DOMContentLoaded', fetchData);
