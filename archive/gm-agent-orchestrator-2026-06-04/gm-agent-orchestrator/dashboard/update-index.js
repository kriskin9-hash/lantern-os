/**
 * Dashboard Live Queue & Agent Status Monitor
 * Reads from tasks/QUEUE_STATUS.json and orchestrator.json
 * Updates every 10 seconds
 */

class DashboardMonitor {
    constructor() {
        this.updateInterval = 10000; // 10 seconds
        this.queueStatusUrl = '../tasks/QUEUE_STATUS.json';
        this.orchestratorUrl = '/api/status';
        this.steeringActionUrl = '/artifacts/market-data/live-steering-action.json';
        this.steeringTelemetryUrl = '/artifacts/market-data/live-steering-telemetry.json';
        this.lastUpdate = null;
        this.activityLog = [];
    }

    async fetch(url) {
        try {
            const response = await fetch(url + '?t=' + Date.now());
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn('Failed to fetch:', url, error);
            return null;
        }
    }

    async update() {
        const status = await this.fetch(this.queueStatusUrl);
        const orchestrator = await this.fetch(this.orchestratorUrl);

        if (!status) return;

        this.updateQueueDisplay(status);
        this.updateNotifications(status);
        this.updateAgents(orchestrator);
        this.updateSteeringStatus(await this.fetch(this.steeringActionUrl), await this.fetch(this.steeringTelemetryUrl));
        this.lastUpdate = new Date();
    }

    updateQueueDisplay(status) {
        const { queue, health } = status;

        // Update queue counts
        const counts = {
            todo: document.getElementById('todoCount'),
            working: document.getElementById('workingCount'),
            done: document.getElementById('doneCount'),
            blocked: document.getElementById('blockedCount'),
            failed: document.getElementById('failedCount')
        };

        if (counts.todo) counts.todo.textContent = queue.todo;
        if (counts.working) counts.working.textContent = queue.working;
        if (counts.done) counts.done.textContent = queue.done;
        if (counts.blocked) counts.blocked.textContent = queue.blocked;
        if (counts.failed) counts.failed.textContent = queue.failed;

        // Update health indicator
        const healthDot = document.getElementById('healthDot');
        const healthText = document.getElementById('healthText');
        const queueCard = document.getElementById('queueStatusCard');

        if (health.needsAttention) {
            if (healthDot) healthDot.className = 'health-dot alert';
            if (healthText) healthText.textContent = '🚨 Needs Attention';
            if (queueCard) queueCard.classList.add('alert');
        } else if (queue.blocked > 0 || queue.failed > 0) {
            if (healthDot) healthDot.className = 'health-dot warning';
            if (healthText) healthText.textContent = '⚠️ Issues Found';
            if (queueCard) queueCard.classList.remove('alert');
        } else {
            if (healthDot) healthDot.className = 'health-dot healthy';
            if (healthText) healthText.textContent = '✅ System Healthy';
            if (queueCard) queueCard.classList.remove('alert');
        }
    }

    updateNotifications(status) {
        const { queue, health } = status;
        const bar = document.getElementById('notificationsBar');
        const text = document.getElementById('notificationText');

        if (!bar || !text) return;

        let message = '✨ System running smoothly';
        let shouldShow = false;

        if (health.needsAttention) {
            message = `🚨 System attention needed: ${queue.blocked} blocked, ${queue.failed} failed tasks`;
            shouldShow = true;
        } else if (queue.blocked > 0 || queue.failed > 0) {
            message = `⚠️ ${queue.blocked} blocked, ${queue.failed} failed tasks need review`;
            shouldShow = true;
        } else if (queue.todo > 0) {
            message = `📋 ${queue.todo} tasks waiting, ${queue.working} active`;
            shouldShow = true;
        }

        text.textContent = message;

        if (!shouldShow) {
            bar.classList.add('collapsed');
        } else {
            bar.classList.remove('collapsed');
        }
    }

    updateAgents(orchestrator) {
        const grid = document.getElementById('agentsGrid');
        if (!grid || !orchestrator || !orchestrator.availability || !orchestrator.availability.slots) return;

        grid.innerHTML = '';
        const slots = orchestrator.availability.slots || [];

        if (slots.length === 0) {
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #64748b;">No agents configured</div>';
            return;
        }

        slots.forEach(slot => {
            const card = this.createAgentCard(slot);
            grid.appendChild(card);
        });
    }

    updateSteeringStatus(actionState, telemetryState) {
        const actionEl = document.getElementById('steeringAction');
        const reasonEl = document.getElementById('steeringReason');
        const pnlEl = document.getElementById('steeringPnl');
        const latencyEl = document.getElementById('steeringLatency');
        const modeEl = document.getElementById('steeringMode');

        const action = actionState && actionState.action ? String(actionState.action) : 'unknown';
        const reason = actionState && Array.isArray(actionState.reasons) && actionState.reasons.length > 0
            ? actionState.reasons[0]
            : 'no_reason';
        const pnl = actionState && actionState.telemetry && actionState.telemetry.realizedPnlUsd !== undefined
            ? Number(actionState.telemetry.realizedPnlUsd)
            : (telemetryState && telemetryState.realized_pnl_usd !== undefined ? Number(telemetryState.realized_pnl_usd) : null);
        const latency = actionState && actionState.telemetry && actionState.telemetry.fillLatencyMs !== undefined
            ? Number(actionState.telemetry.fillLatencyMs)
            : (telemetryState && telemetryState.fill_latency_ms !== undefined ? Number(telemetryState.fill_latency_ms) : null);
        const mode = actionState && actionState.state && actionState.state.recommendedMode
            ? String(actionState.state.recommendedMode)
            : 'unknown';

        if (actionEl) actionEl.textContent = action.toUpperCase();
        if (reasonEl) reasonEl.textContent = reason;
        if (pnlEl) pnlEl.textContent = pnl === null ? '--' : pnl.toFixed(2);
        if (latencyEl) latencyEl.textContent = latency === null ? '--' : String(latency);
        if (modeEl) modeEl.textContent = mode;
    }

            createAgentCard(slot) {
                const card = document.createElement('div');
                const stateClass = this.getStateClass(slot.state);
                
                card.className = `agent-card ${stateClass}`;
                card.innerHTML = `
                    <div class="agent-header">
                        <div class="agent-name">${slot.name}</div>
                        <div class="agent-status-badge ${stateClass}">${slot.state.toUpperCase()}</div>
                    </div>
                    <div class="agent-info">
                        <div class="agent-info-row">
                            <span class="info-label">Type:</span>
                            <span class="info-value">${slot.agent || 'unknown'}</span>
                        </div>
                        <div class="agent-info-row">
                            <span class="info-label">State:</span>
                            <span class="info-value">${slot.wakeState}</span>
                        </div>
                        ${slot.reason ? `<div class="agent-info-row"><span class="info-label">Reason:</span><span class="info-value">${slot.reason}</span></div>` : ''}
                    </div>
                    <div class="agent-actions">
                        <button class="agent-action-btn" onclick="alert('Wake action: ${slot.name}')">⚡ Wake</button>
                        <button class="agent-action-btn" onclick="alert('Details: ${slot.name}')">Details →</button>
                    </div>
                `;

                card.addEventListener('click', () => this.showAgentPanel(slot));
                return card;
            }

            getStateClass(state) {
                if (state === 'blocked') return 'stuck';
                if (state === 'idle') return 'healthy';
                if (state === 'active') return 'working'; // Assuming 'active' state exists
                return 'idle'; // Default case
            }

    getRelativeTime(timestamp) {
        const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
        const now = new Date();
        const diff = Math.round((now - date) / 1000);

        if (diff < 60) return `${diff}s ago`;
        if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
        return `${Math.round(diff / 3600)}h ago`;
    }

    start() {
        this.update();
        setInterval(() => this.update(), this.updateInterval);

        // Set up notification close
        const closeBtn = document.getElementById('closeNotification');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                document.getElementById('notificationsBar').classList.add('collapsed');
            });
        }
    }
}

// Auto-start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const monitor = new DashboardMonitor();
        monitor.start();
    });
} else {
    const monitor = new DashboardMonitor();
    monitor.start();
}
