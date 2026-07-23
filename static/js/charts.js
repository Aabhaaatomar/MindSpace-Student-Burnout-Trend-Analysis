/*
    MindSpace - Chart.js Rendering Engine
*/

document.addEventListener('DOMContentLoaded', () => {
    // Check if chart canvas elements exist before initializing
    if (!document.getElementById('burnoutDonutChart') && !document.getElementById('departmentBarChart')) {
        return; // Not on the dashboard page
    }

    let chartsList = {};

    // Colors adjusted for Dark / Light theme compatibility
    function getThemeColors() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            textColor: isDark ? '#94A3B8' : '#64748B',
            gridColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.04)',
            tooltipBg: isDark ? '#1E293B' : '#FFFFFF',
            tooltipText: isDark ? '#F8FAFC' : '#1E293B',
            tooltipBorder: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)',
        };
    }

    // Main fetch and render function
    function fetchAndRenderCharts() {
        const theme = getThemeColors();

        fetch('/api/charts-data')
            .then(res => res.json())
            .then(data => {
                if (!data || Object.keys(data).length === 0) {
                    console.warn("No chart data retrieved.");
                    return;
                }

                // Destroy existing charts before redraw if they exist
                Object.keys(chartsList).forEach(key => {
                    if (chartsList[key]) chartsList[key].destroy();
                });

                // 1. Burnout Category Distribution (Donut Chart)
                const donutCtx = document.getElementById('burnoutDonutChart');
                if (donutCtx && data.burnout_distribution) {
                    chartsList.burnoutDonut = new Chart(donutCtx, {
                        type: 'doughnut',
                        data: {
                            labels: data.burnout_distribution.labels,
                            datasets: [{
                                data: data.burnout_distribution.data,
                                backgroundColor: ['#EF5350', '#4CAF50', '#F4B400'], // High (Danger), Low (Accent), Medium (Warning)
                                borderWidth: 0,
                                hoverOffset: 8
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'bottom',
                                    labels: { color: theme.textColor, font: { family: 'Inter', weight: 500 } }
                                },
                                tooltip: {
                                    backgroundColor: theme.tooltipBg,
                                    titleColor: theme.tooltipText,
                                    bodyColor: theme.textColor,
                                    borderColor: theme.tooltipBorder,
                                    borderWidth: 1
                                }
                            },
                            cutout: '70%'
                        }
                    });
                }

                // 2. Department-wise Burnout & Stress (Grouped Bar Chart)
                const deptCtx = document.getElementById('departmentBarChart');
                if (deptCtx && data.department_analysis) {
                    chartsList.deptBar = new Chart(deptCtx, {
                        type: 'bar',
                        data: {
                            labels: data.department_analysis.labels,
                            datasets: [
                                {
                                    label: 'Burnout Score (avg)',
                                    data: data.department_analysis.burnout,
                                    backgroundColor: '#8E7CFF',
                                    borderRadius: 6
                                },
                                {
                                    label: 'Stress Level (avg/10)',
                                    data: data.department_analysis.stress,
                                    backgroundColor: '#5B8DEF',
                                    borderRadius: 6
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'top',
                                    labels: { color: theme.textColor }
                                },
                                tooltip: {
                                    backgroundColor: theme.tooltipBg,
                                    titleColor: theme.tooltipText,
                                    bodyColor: theme.textColor,
                                    borderColor: theme.tooltipBorder,
                                    borderWidth: 1
                                }
                            },
                            scales: {
                                x: {
                                    grid: { color: 'transparent' },
                                    ticks: { color: theme.textColor }
                                },
                                y: {
                                    grid: { color: theme.gridColor },
                                    ticks: { color: theme.textColor }
                                }
                            }
                        }
                    });
                }

                // 3. Stress Distribution (Histogram/Bar)
                const stressCtx = document.getElementById('stressDistributionChart');
                if (stressCtx && data.stress_distribution) {
                    chartsList.stressBar = new Chart(stressCtx, {
                        type: 'bar',
                        data: {
                            labels: data.stress_distribution.labels,
                            datasets: [{
                                label: 'Students Count',
                                data: data.stress_distribution.data,
                                backgroundColor: 'rgba(91, 141, 239, 0.75)',
                                borderColor: '#5B8DEF',
                                borderWidth: 1,
                                borderRadius: 6
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: theme.tooltipBg,
                                    titleColor: theme.tooltipText,
                                    bodyColor: theme.textColor,
                                    borderColor: theme.tooltipBorder,
                                    borderWidth: 1
                                }
                            },
                            scales: {
                                x: {
                                    grid: { color: 'transparent' },
                                    ticks: { color: theme.textColor },
                                    title: { display: true, text: 'Stress Level (1-10)', color: theme.textColor }
                                },
                                y: {
                                    grid: { color: theme.gridColor },
                                    ticks: { color: theme.textColor }
                                }
                            }
                        }
                    });
                }

                // 4. Study Hours vs Burnout Score (Scatter Chart)
                const studyScatterCtx = document.getElementById('studyScatterChart');
                if (studyScatterCtx && data.study_vs_burnout) {
                    chartsList.studyScatter = new Chart(studyScatterCtx, {
                        type: 'scatter',
                        data: {
                            datasets: [{
                                label: 'Student Data Point',
                                data: data.study_vs_burnout,
                                backgroundColor: 'rgba(142, 124, 255, 0.65)',
                                pointRadius: 5,
                                pointHoverRadius: 8
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: theme.tooltipBg,
                                    titleColor: theme.tooltipText,
                                    bodyColor: theme.textColor,
                                    borderColor: theme.tooltipBorder,
                                    borderWidth: 1,
                                    callbacks: {
                                        label: function(context) {
                                            const point = context.raw;
                                            return `${point.name}: Study=${point.x}h, Burnout=${point.y.toFixed(2)}`;
                                        }
                                    }
                                }
                            },
                            scales: {
                                x: {
                                    grid: { color: theme.gridColor },
                                    ticks: { color: theme.textColor },
                                    title: { display: true, text: 'Daily Study Hours', color: theme.textColor }
                                },
                                y: {
                                    grid: { color: theme.gridColor },
                                    ticks: { color: theme.textColor },
                                    title: { display: true, text: 'Burnout Index (0.0-1.0)', color: theme.textColor }
                                }
                            }
                        }
                    });
                }

                // 5. Sleep Analysis (Histogram/Bar)
                const sleepCtx = document.getElementById('sleepDistributionChart');
                if (sleepCtx && data.sleep_distribution) {
                    chartsList.sleepBar = new Chart(sleepCtx, {
                        type: 'bar',
                        data: {
                            labels: data.sleep_distribution.labels,
                            datasets: [{
                                label: 'Students Count',
                                data: data.sleep_distribution.data,
                                backgroundColor: 'rgba(76, 175, 80, 0.7)',
                                borderColor: '#4CAF50',
                                borderWidth: 1,
                                borderRadius: 6
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: theme.tooltipBg,
                                    titleColor: theme.tooltipText,
                                    bodyColor: theme.textColor,
                                    borderColor: theme.tooltipBorder,
                                    borderWidth: 1
                                }
                            },
                            scales: {
                                x: {
                                    grid: { color: 'transparent' },
                                    ticks: { color: theme.textColor }
                                },
                                y: {
                                    grid: { color: theme.gridColor },
                                    ticks: { color: theme.textColor }
                                }
                            }
                        }
                    });
                }

                // 6. Year Analysis (Line Chart)
                const yearCtx = document.getElementById('yearTrendChart');
                if (yearCtx && data.year_analysis) {
                    chartsList.yearLine = new Chart(yearCtx, {
                        type: 'line',
                        data: {
                            labels: data.year_analysis.labels,
                            datasets: [{
                                label: 'Average Burnout Index',
                                data: data.year_analysis.data,
                                borderColor: '#5B8DEF',
                                backgroundColor: 'rgba(91, 141, 239, 0.1)',
                                fill: true,
                                tension: 0.3,
                                pointBackgroundColor: '#8E7CFF',
                                pointBorderColor: '#fff',
                                pointRadius: 6,
                                pointHoverRadius: 8
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: theme.tooltipBg,
                                    titleColor: theme.tooltipText,
                                    bodyColor: theme.textColor,
                                    borderColor: theme.tooltipBorder,
                                    borderWidth: 1
                                }
                            },
                            scales: {
                                x: {
                                    grid: { color: 'transparent' },
                                    ticks: { color: theme.textColor }
                                },
                                y: {
                                    grid: { color: theme.gridColor },
                                    ticks: { color: theme.textColor },
                                    suggestedMin: 0.2,
                                    suggestedMax: 0.8
                                }
                            }
                        }
                    });
                }

                // 7. Gender-wise Burnout (Pie Chart)
                const genderCtx = document.getElementById('genderPieChart');
                if (genderCtx && data.gender_analysis) {
                    chartsList.genderPie = new Chart(genderCtx, {
                        type: 'pie',
                        data: {
                            labels: data.gender_analysis.labels,
                            datasets: [{
                                data: data.gender_analysis.data,
                                backgroundColor: ['#5B8DEF', '#8E7CFF', '#4CAF50'],
                                borderWidth: 0
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'right',
                                    labels: { color: theme.textColor }
                                },
                                tooltip: {
                                    backgroundColor: theme.tooltipBg,
                                    titleColor: theme.tooltipText,
                                    bodyColor: theme.textColor,
                                    borderColor: theme.tooltipBorder,
                                    borderWidth: 1
                                }
                            }
                        }
                    });
                }

                // 8. Heatmap rendering (Correlation Matrix in pure HTML & CSS)
                const heatmapEl = document.getElementById('correlationHeatmap');
                if (heatmapEl && data.correlation_matrix) {
                    renderCorrelationHeatmap(heatmapEl, data.correlation_matrix);
                }
            })
            .catch(err => console.error("Error drawing charts:", err));
    }

    // Render HTML-based correlation matrix heatmap
    function renderCorrelationHeatmap(container, matrixData) {
        container.innerHTML = ''; // Clear previous
        const labels = matrixData.labels;
        const values = matrixData.data;

        // Render headers first
        let headerRow = document.createElement('div');
        headerRow.style.display = 'contents';
        
        // Blank top-left corner
        let blankCorner = document.createElement('div');
        blankCorner.className = 'd-none d-md-flex align-items-center justify-content-center text-muted small fw-bold';
        blankCorner.style.gridColumn = '1';
        blankCorner.textContent = '';
        container.appendChild(blankCorner);

        // Column Labels
        labels.forEach((label, index) => {
            let colLabel = document.createElement('div');
            colLabel.className = 'text-center text-truncate py-1 px-1 text-muted small fw-bold';
            colLabel.style.gridColumn = `${index + 2}`;
            colLabel.style.fontSize = '0.7rem';
            colLabel.textContent = label;
            colLabel.title = label;
            container.appendChild(colLabel);
        });

        // Heatmap Cells
        values.forEach((row, rIdx) => {
            // Row Label
            let rowLabel = document.createElement('div');
            rowLabel.className = 'd-flex align-items-center pe-2 text-muted small fw-bold';
            rowLabel.style.gridColumn = '1';
            rowLabel.style.fontSize = '0.7rem';
            rowLabel.textContent = labels[rIdx];
            rowLabel.title = labels[rIdx];
            container.appendChild(rowLabel);

            // Cells in Row
            row.forEach((val, cIdx) => {
                let cell = document.createElement('div');
                cell.className = 'heatmap-cell';
                cell.style.gridColumn = `${cIdx + 2}`;
                cell.textContent = val.toFixed(2);
                cell.title = `${labels[rIdx]} vs ${labels[cIdx]}: ${val.toFixed(2)}`;

                // Style based on correlation value
                // Maps positive correlations to shades of secondary (#8E7CFF) and negative to red/primary
                const absVal = Math.abs(val);
                if (val > 0) {
                    // Positive correlation
                    cell.style.backgroundColor = `rgba(142, 124, 255, ${0.1 + absVal * 0.9})`;
                    cell.style.color = absVal > 0.5 ? '#fff' : 'var(--text-primary)';
                } else {
                    // Negative correlation
                    cell.style.backgroundColor = `rgba(91, 141, 239, ${0.1 + absVal * 0.9})`;
                    cell.style.color = absVal > 0.5 ? '#fff' : 'var(--text-primary)';
                }

                container.appendChild(cell);
            });
        });
    }

    // Listen to themeChanged event from main.js to update styles and re-draw
    window.addEventListener('themeChanged', () => {
        fetchAndRenderCharts();
    });

    // Initial load
    fetchAndRenderCharts();
});
