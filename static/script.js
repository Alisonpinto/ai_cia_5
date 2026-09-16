/* =====================================================
   GLOBAL STATE & CHART INSTANCES
   ==================================================== */
let scoreChartInstance = null;
let typeChartInstance = null;

/* =====================================================
   TOAST NOTIFICATION HELPER
   ===================================================== */
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? '✓' : type === 'error' ? '⚠️' : 'ℹ️';
    toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            toast.remove();
            if (container.children.length === 0) {
                container.remove();
            }
        }, 300);
    }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {

    // Universal Logout Button (on navbar)
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                await fetch('/api/logout', { method: 'POST' });
            } catch (err) {
                console.error('Logout error:', err);
                showToast('Something went wrong. Please try again.', 'error');
            } finally {
                sessionStorage.clear();
                window.location.href = '/login';
            }
        });
    }

    /* =====================================================
       LOGIN & REGISTRATION PAGE
       ===================================================== */
    const loginForm = document.getElementById('loginForm');
    const loginError = document.getElementById('loginError');
    const registerForm = document.getElementById('registerForm');
    const registerMsg = document.getElementById('registerMsg');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (loginError) {
                loginError.textContent = '';
                loginError.classList.remove('show');
            }

            const username = document.getElementById('username')?.value.trim();
            const user_key = document.getElementById('user_key')?.value.trim();

            if (!username || !user_key) {
                if (loginError) {
                    loginError.textContent = 'Please enter both username and user key.';
                    loginError.classList.add('show');
                }
                return;
            }

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, user_key })
                });

                const data = await response.json().catch(() => ({}));

                if (response.ok && data.status === 'ok') {
                    window.location.href = '/dashboard';
                } else {
                    if (loginError) {
                        loginError.textContent = data.message || 'Login failed. Please verify credentials.';
                        loginError.classList.add('show');
                    }
                }
            } catch (err) {
                if (loginError) {
                    loginError.textContent = 'Network error. Please try again later.';
                    loginError.classList.add('show');
                }
                showToast('Something went wrong. Please try again.', 'error');
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (registerMsg) {
                registerMsg.textContent = '';
                registerMsg.className = 'mt-2';
            }

            const username = document.getElementById('reg_username')?.value.trim();
            const email = document.getElementById('reg_email')?.value.trim();
            const password = document.getElementById('reg_password')?.value.trim();

            if (!username || !email || !password) {
                if (registerMsg) {
                    registerMsg.textContent = 'Please fill in all registration fields.';
                    registerMsg.className = 'error-msg show mt-2';
                }
                return;
            }

            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });

                const data = await response.json().catch(() => ({}));

                if (response.ok && data.status === 'ok') {
                    if (registerMsg) {
                        registerMsg.innerHTML = `Registered! Your key is <strong>${escapeHtml(data.user_key)}</strong> (save this).`;
                        registerMsg.className = 'success-msg show mt-2';
                    }
                    showToast('Registration successful! User key generated.', 'success');

                    const loginUsername = document.getElementById('username');
                    const loginUserKey = document.getElementById('user_key');
                    if (loginUsername) loginUsername.value = username;
                    if (loginUserKey) loginUserKey.value = data.user_key;

                    registerForm.reset();
                } else {
                    if (registerMsg) {
                        registerMsg.textContent = data.message || 'Registration failed.';
                        registerMsg.className = 'error-msg show mt-2';
                    }
                }
            } catch (err) {
                if (registerMsg) {
                    registerMsg.textContent = 'Network error during registration.';
                    registerMsg.className = 'error-msg show mt-2';
                }
                showToast('Something went wrong. Please try again.', 'error');
            }
        });
    }

    /* =====================================================
       DASHBOARD PAGE
       ===================================================== */
    const findBtn = document.getElementById('findBtn');

    if (findBtn) {
        fetchStats();

        const maxPrice = document.getElementById('maxPrice');
        const priceVal = document.getElementById('priceVal');
        if (maxPrice && priceVal) {
            maxPrice.addEventListener('input', () => {
                priceVal.textContent = `$${parseFloat(maxPrice.value).toFixed(2)}`;
            });
        }

        const minTrust = document.getElementById('minTrust');
        const trustVal = document.getElementById('trustVal');
        if (minTrust && trustVal) {
            minTrust.addEventListener('input', () => {
                trustVal.textContent = parseFloat(minTrust.value).toFixed(2);
            });
        }

        let currentType = 'SaaS';
        const tiles = document.querySelectorAll('.type-tile');
        tiles.forEach(tile => {
            tile.addEventListener('click', () => {
                tiles.forEach(t => t.classList.remove('active'));
                tile.classList.add('active');
                currentType = tile.getAttribute('data-type') || 'SaaS';
            });
        });

        findBtn.addEventListener('click', () => {
            const price = maxPrice ? parseFloat(maxPrice.value) : 5.0;
            const trust = minTrust ? parseFloat(minTrust.value) : 0.7;
            const durationInput = document.getElementById('duration');
            const minScoreInput = document.getElementById('minScore');

            const duration = durationInput ? parseInt(durationInput.value, 10) || 4 : 4;
            const minScore = minScoreInput ? parseFloat(minScoreInput.value) || 0.0 : 0.0;

            const searchPrefs = {
                service_type: currentType,
                max_price: price,
                min_trust: trust,
                duration: duration,
                min_score: minScore
            };

            sessionStorage.setItem('searchPrefs', JSON.stringify(searchPrefs));
            window.location.href = '/results';
        });
    }

    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            if (!res.ok) return;
            const data = await res.json();

            const statProviders = document.getElementById('statProviders');
            const statServices = document.getElementById('statServices');
            const statSaaS = document.getElementById('statSaaS');
            const statIaaS = document.getElementById('statIaaS');
            const statPaaS = document.getElementById('statPaaS');

            if (statProviders) statProviders.textContent = data.total_providers ?? '–';
            if (statServices) statServices.textContent = data.total_services ?? '–';
            if (statSaaS) statSaaS.textContent = data.by_type?.SaaS ?? '0';
            if (statIaaS) statIaaS.textContent = data.by_type?.IaaS ?? '0';
            if (statPaaS) statPaaS.textContent = data.by_type?.PaaS ?? '0';
        } catch (err) {
            console.error('Error fetching dashboard stats:', err);
            showToast('Something went wrong. Please try again.', 'error');
        }
    }

    /* =====================================================
       RESULTS PAGE
       ===================================================== */
    const resultsSection = document.getElementById('resultsSection');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const errorReason = document.getElementById('errorReason');
    const againBtn = document.getElementById('againBtn');

    if (resultsSection) {
        const rawPrefs = sessionStorage.getItem('searchPrefs');
        if (!rawPrefs) {
            window.location.href = '/dashboard';
            return;
        }

        let prefs;
        try {
            prefs = JSON.parse(rawPrefs);
        } catch (e) {
            window.location.href = '/dashboard';
            return;
        }

        const chipType = document.getElementById('chipType');
        const chipPrice = document.getElementById('chipPrice');
        const chipTrust = document.getElementById('chipTrust');
        const chipDuration = document.getElementById('chipDuration');

        if (chipType) chipType.textContent = `Type: ${prefs.service_type || '—'}`;
        if (chipPrice) chipPrice.textContent = `Max: $${Number(prefs.max_price || 0).toFixed(2)}`;
        if (chipTrust) chipTrust.textContent = `Min Trust: ${Number(prefs.min_trust || 0).toFixed(2)}`;
        if (chipDuration) chipDuration.textContent = `Duration: ${prefs.duration || 0}h`;

        if (loadingState) loadingState.style.display = 'block';
        if (resultsSection) resultsSection.style.display = 'none';
        if (errorState) errorState.style.display = 'none';

        executeSearch(prefs);

        if (againBtn) {
            againBtn.addEventListener('click', () => {
                sessionStorage.removeItem('searchPrefs');
                window.location.href = '/dashboard';
            });
        }
    }

    async function executeSearch(prefs) {
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(prefs)
            });

            const result = await response.json().catch(() => ({}));

            if (loadingState) loadingState.style.display = 'none';

            if (!response.ok || !result.success || !result.chosen) {
                if (errorState) {
                    errorState.style.display = 'block';
                    if (errorReason) {
                        errorReason.textContent = result.reason || 'Try increasing your budget or lowering trust requirements.';
                    }
                }
                return;
            }

            if (resultsSection) resultsSection.style.display = 'block';

            // A. Winner Hero Card
            const chosen = result.chosen;
            const winnerName = document.getElementById('winnerName');
            const winnerProvider = document.getElementById('winnerProvider');
            const winnerScore = document.getElementById('winnerScore');
            const winnerSpecs = document.getElementById('winnerSpecs');

            if (winnerName) winnerName.textContent = chosen.name;
            if (winnerProvider) winnerProvider.textContent = `${chosen.provider_name} • ${chosen.category.toUpperCase()} • ${chosen.service_type}`;
            if (winnerScore) winnerScore.textContent = Number(chosen.fuzzy_score).toFixed(2);

            if (winnerSpecs) {
                winnerSpecs.innerHTML = `
                    <div class="spec-item">
                        <span class="spec-label">Price / hr</span>
                        <span class="spec-val">$${Number(chosen.price).toFixed(2)}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Trust Score</span>
                        <span class="spec-val">${Number(chosen.trustworthiness).toFixed(2)}</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Compute</span>
                        <span class="spec-val">${chosen.cpu} Cores / ${chosen.ram} GB RAM</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Bandwidth</span>
                        <span class="spec-val">${chosen.bandwidth} Mbps</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Max Duration</span>
                        <span class="spec-val">${chosen.duration} hours</span>
                    </div>
                    <div class="spec-item">
                        <span class="spec-label">Available Slots</span>
                        <span class="spec-val">${chosen.available_slots}</span>
                    </div>
                `;
            }

            // Wire Contract Button
            const contractBtn = document.getElementById('contractBtn');
            const contractMsg = document.getElementById('contractMsg');
            if (contractBtn) {
                contractBtn.onclick = () => {
                    contractBtn.disabled = true;
                    contractBtn.textContent = 'Contract Saved ✓';
                    contractBtn.style.background = 'var(--success)';
                    contractBtn.style.cursor = 'default';
                    if (contractMsg) {
                        contractMsg.textContent = `Contract #${result.contract_id || 1} confirmed and active in SQLite database.`;
                        contractMsg.className = 'success-msg show mt-2';
                    }
                    showToast('Contract saved successfully', 'success');
                };
            }

            // B. Candidates Comparison Table
            const candidatesBody = document.getElementById('candidatesBody');
            if (candidatesBody && Array.isArray(result.candidates)) {
                const sorted = [...result.candidates].sort((a, b) => (b.fuzzy_score ?? 0) - (a.fuzzy_score ?? 0));
                candidatesBody.innerHTML = '';

                sorted.forEach((service, index) => {
                    let status = 'ok';
                    let badgeClass = 'status-ok';
                    let rowClass = '';

                    if (service.id === chosen.id) {
                        status = 'Winner';
                        badgeClass = 'status-winner';
                        rowClass = 'row-winner';
                    } else if (
                        (service.fuzzy_score ?? 0) >= (prefs.min_score || 0) &&
                        service.price <= prefs.max_price &&
                        service.trustworthiness >= prefs.min_trust
                    ) {
                        status = 'Eligible';
                        badgeClass = 'status-ok';
                    } else {
                        status = 'Rejected';
                        badgeClass = 'status-rejected';
                        rowClass = 'row-rejected';
                    }

                    const tr = document.createElement('tr');
                    if (rowClass) tr.className = rowClass;
                    tr.innerHTML = `
                        <td>${index + 1}</td>
                        <td><strong>${escapeHtml(service.name)}</strong></td>
                        <td>${escapeHtml(service.provider_name || '–')}</td>
                        <td>$${Number(service.price).toFixed(2)}</td>
                        <td>${Number(service.trustworthiness).toFixed(2)}</td>
                        <td><strong>${Number(service.fuzzy_score ?? 0).toFixed(2)}</strong></td>
                        <td><span class="status-badge ${badgeClass}">${status}</span></td>
                    `;
                    candidatesBody.appendChild(tr);
                });
            }

            // C. Dynamic Charts
            renderCharts(result.candidates, result.chosen ? result.chosen.id : null);

            // D. Agent Conversation Log
            const agentLog = document.getElementById('agentLog');
            if (agentLog && Array.isArray(result.logs)) {
                agentLog.innerHTML = '';
                const chronologicalLogs = [...result.logs].reverse();
                const useDelay = chronologicalLogs.length <= 40;

                chronologicalLogs.forEach((entry, i) => {
                    const renderEntry = () => {
                        const div = document.createElement('div');
                        div.className = 'log-entry';

                        let timeStr = '';
                        if (entry.timestamp) {
                            const parts = entry.timestamp.split(' ');
                            timeStr = parts[1] ? parts[1].substring(0, 8) : entry.timestamp;
                        } else {
                            timeStr = new Date().toLocaleTimeString();
                        }

                        div.innerHTML = `
                            <span class="log-time">[${escapeHtml(timeStr)}]</span>
                            <span class="log-agent ${escapeHtml(entry.agent_type)}">[${escapeHtml(entry.agent_type)}]</span>
                            <span class="log-msg">${escapeHtml(entry.message)}</span>
                        `;
                        agentLog.appendChild(div);
                        agentLog.scrollTop = agentLog.scrollHeight;
                    };

                    if (useDelay) {
                        setTimeout(renderEntry, i * 200);
                    } else {
                        renderEntry();
                    }
                });
            }

        } catch (err) {
            console.error('Search request error:', err);
            if (loadingState) loadingState.style.display = 'none';
            if (errorState) {
                errorState.style.display = 'block';
                if (errorReason) errorReason.textContent = 'Connection error. Please try again.';
            }
            showToast('Something went wrong. Please try again.', 'error');
        }
    }

    /* =====================================================
       CHARTS HELPER
       ===================================================== */
    function renderCharts(candidates, chosenId) {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded');
            return;
        }

        const scoreCanvas = document.getElementById('scoreChart');
        const typeCanvas = document.getElementById('typeChart');
        if (!scoreCanvas || !typeCanvas || !Array.isArray(candidates) || candidates.length === 0) {
            return;
        }

        const labels = candidates.map(c => c.name);
        const scores = candidates.map(c => Number(c.fuzzy_score ?? 0).toFixed(2));
        const colors = candidates.map(c =>
            c.id === chosenId ? 'rgba(99, 102, 241, 1)'
                              : 'rgba(99, 102, 241, 0.35)'
        );

        if (scoreChartInstance) scoreChartInstance.destroy();

        const ctx1 = scoreCanvas.getContext('2d');
        scoreChartInstance = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Fuzzy Score',
                    data: scores,
                    backgroundColor: colors,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#e2e8f0',
                        bodyColor: '#94a3b8',
                        callbacks: {
                            label: (ctx) => 'Score: ' + parseFloat(ctx.parsed.x).toFixed(2)
                        }
                    }
                },
                scales: {
                    x: {
                        min: 0,
                        max: 1,
                        grid: { color: 'rgba(51, 65, 85, 0.4)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#e2e8f0', font: { size: 11 } }
                    }
                }
            }
        });

        const typeCounts = { SaaS: 0, IaaS: 0, PaaS: 0 };
        candidates.forEach(c => {
            if (typeCounts[c.service_type] !== undefined) {
                typeCounts[c.service_type]++;
            }
        });

        if (typeChartInstance) typeChartInstance.destroy();

        const ctx2 = typeCanvas.getContext('2d');
        typeChartInstance = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: Object.keys(typeCounts),
                datasets: [{
                    data: Object.values(typeCounts),
                    backgroundColor: [
                        'rgba(99, 102, 241, 0.9)',
                        'rgba(34, 211, 238, 0.9)',
                        'rgba(16, 185, 129, 0.9)'
                    ],
                    borderColor: '#0f172a',
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e2e8f0',
                            padding: 16,
                            font: { size: 12 },
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#e2e8f0',
                        bodyColor: '#94a3b8'
                    }
                }
            }
        });
    }
});
