/**
 * Prediction Widgets - Real-time ML Prediction Visualization
 * FASE 14: ML-Based Sales Probability Predictions
 *
 * Provides:
 * - Conversion probability gauge (radial chart)
 * - Confidence score indicator
 * - Risk factors visualization
 * - Positive factors visualization
 * - Recommended timeline to close
 * - Anomaly detection alerts
 */

class PredictionGauge {
    /**
     * Create a radial gauge for conversion probability
     * @param {string} containerId - Element ID for the gauge
     * @param {number} probability - Probability 0-100
     * @param {number} confidence - Confidence 0-100
     */
    constructor(containerId, probability = 0, confidence = 80) {
        this.containerId = containerId;
        this.probability = probability;
        this.confidence = confidence;
        this.canvas = null;
        this.ctx = null;
        this.animationId = null;
        this.currentValue = 0;
    }

    /**
     * Initialize and render the gauge
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // Clear container
        container.innerHTML = '';

        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.width = 220;
        canvas.height = 220;
        container.appendChild(canvas);

        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');

        // Add text below gauge
        const textDiv = document.createElement('div');
        textDiv.style.cssText = `
            text-align: center;
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 12px;
        `;
        textDiv.innerHTML = `
            <div style="font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">
                ${this.probability}%
            </div>
            <div style="font-size: 12px;">Conversion Probability</div>
            <div style="font-size: 11px; margin-top: 8px;">
                Confidence: ${this.confidence}%
            </div>
        `;
        container.appendChild(textDiv);

        // Start animation
        this.animate();
    }

    /**
     * Animate gauge from 0 to target value
     */
    animate() {
        const targetValue = this.probability;
        const speed = 2; // Degrees per frame

        const draw = () => {
            if (this.currentValue < targetValue) {
                this.currentValue += speed;
                if (this.currentValue > targetValue) {
                    this.currentValue = targetValue;
                }
            }

            this.draw(this.currentValue);

            if (this.currentValue < targetValue) {
                this.animationId = requestAnimationFrame(draw);
            }
        };

        draw();
    }

    /**
     * Draw the gauge
     * @param {number} value - Current value (0-100)
     */
    draw(value) {
        const ctx = this.ctx;
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const radius = 80;
        const startAngle = Math.PI + 0.2;
        const endAngle = Math.PI * 0.2;
        const maxAngle = Math.PI * 1.6;

        // Clear canvas
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw background track (light gray)
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, startAngle, startAngle + maxAngle);
        ctx.strokeStyle = 'var(--border)';
        ctx.lineWidth = 12;
        ctx.stroke();

        // Draw colored track based on value
        const currentAngle = (value / 100) * maxAngle;
        const color = this.getGaugeColor(value);

        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, startAngle, startAngle + currentAngle);
        ctx.strokeStyle = color;
        ctx.lineWidth = 12;
        ctx.lineCap = 'round';
        ctx.stroke();

        // Draw center circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, 50, 0, Math.PI * 2);
        ctx.fillStyle = 'var(--bg-card)';
        ctx.fill();
        ctx.strokeStyle = 'var(--border)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw percentage text
        ctx.fillStyle = 'var(--text-primary)';
        ctx.font = 'bold 32px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${Math.round(value)}%`, centerX, centerY);
    }

    /**
     * Get color based on probability value
     * @param {number} value - Probability 0-100
     * @returns {string} CSS color
     */
    getGaugeColor(value) {
        if (value < 30) return '#f44336'; // Red - Low
        if (value < 60) return '#ff9800'; // Orange - Medium
        if (value < 80) return '#2196f3'; // Blue - Good
        return '#4caf50'; // Green - High
    }

    /**
     * Update probability value
     * @param {number} newValue - New probability 0-100
     */
    update(newValue) {
        this.probability = Math.min(100, Math.max(0, newValue));
        this.currentValue = 0;
        this.animate();
    }
}

/**
 * Risk Factors Display
 */
class RiskFactorsWidget {
    constructor(containerId) {
        this.containerId = containerId;
        this.factors = [];
    }

    /**
     * Set risk factors to display
     * @param {Array<Object>} factors - Risk factors with {name, severity, description}
     */
    setFactors(factors) {
        this.factors = factors || [];
        this.render();
    }

    /**
     * Render risk factors
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        container.innerHTML = '';

        if (this.factors.length === 0) {
            container.innerHTML = '<div style="color: var(--text-light); font-size: 13px; padding: 16px;">No risk factors identified</div>';
            return;
        }

        const list = document.createElement('div');
        list.style.cssText = 'display: flex; flex-direction: column; gap: 12px;';

        this.factors.forEach(factor => {
            const item = this.createFactorItem(factor);
            list.appendChild(item);
        });

        container.appendChild(list);
    }

    /**
     * Create a single factor item
     * @param {Object} factor - Factor with {name, severity, description}
     * @returns {HTMLElement}
     */
    createFactorItem(factor) {
        const item = document.createElement('div');
        item.style.cssText = `
            display: flex;
            gap: 12px;
            padding: 12px;
            background: var(--bg);
            border-radius: 8px;
            border-left: 3px solid ${this.getSeverityColor(factor.severity)};
        `;

        const icon = document.createElement('div');
        icon.style.cssText = `
            flex-shrink: 0;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            background: ${this.getSeverityColor(factor.severity)};
            color: white;
        `;
        icon.textContent = '⚠';

        const content = document.createElement('div');
        content.style.cssText = 'flex: 1; font-size: 13px;';
        content.innerHTML = `
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">${factor.name}</div>
            <div style="color: var(--text-secondary); font-size: 12px;">${factor.description}</div>
        `;

        item.appendChild(icon);
        item.appendChild(content);

        return item;
    }

    /**
     * Get color based on severity
     */
    getSeverityColor(severity) {
        const severities = {
            'critical': '#f44336',
            'high': '#ff9800',
            'medium': '#ffc107',
            'low': '#2196f3'
        };
        return severities[severity] || '#2196f3';
    }
}

/**
 * Positive Factors Display
 */
class PositiveFactorsWidget {
    constructor(containerId) {
        this.containerId = containerId;
        this.factors = [];
    }

    /**
     * Set positive factors to display
     * @param {Array<Object>} factors - Factors with {name, impact, description}
     */
    setFactors(factors) {
        this.factors = factors || [];
        this.render();
    }

    /**
     * Render positive factors
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        container.innerHTML = '';

        if (this.factors.length === 0) {
            container.innerHTML = '<div style="color: var(--text-light); font-size: 13px; padding: 16px;">No positive factors yet</div>';
            return;
        }

        const list = document.createElement('div');
        list.style.cssText = 'display: flex; flex-direction: column; gap: 12px;';

        this.factors.forEach(factor => {
            const item = this.createFactorItem(factor);
            list.appendChild(item);
        });

        container.appendChild(list);
    }

    /**
     * Create a single positive factor item
     */
    createFactorItem(factor) {
        const item = document.createElement('div');
        item.style.cssText = `
            display: flex;
            gap: 12px;
            padding: 12px;
            background: rgba(76, 175, 80, 0.1);
            border-radius: 8px;
            border-left: 3px solid #4caf50;
        `;

        const icon = document.createElement('div');
        icon.style.cssText = `
            flex-shrink: 0;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            background: #4caf50;
            color: white;
        `;
        icon.textContent = '✓';

        const content = document.createElement('div');
        content.style.cssText = 'flex: 1; font-size: 13px;';
        content.innerHTML = `
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">${factor.name}</div>
            <div style="color: var(--text-secondary); font-size: 12px;">${factor.description}</div>
            ${factor.impact ? `<div style="color: #4caf50; font-size: 11px; margin-top: 4px;">+${factor.impact}% impact</div>` : ''}
        `;

        item.appendChild(icon);
        item.appendChild(content);

        return item;
    }
}

/**
 * Timeline to Close Widget
 */
class TimelineWidget {
    constructor(containerId) {
        this.containerId = containerId;
        this.days = 0;
        this.confidence = 0;
    }

    /**
     * Set timeline data
     * @param {number} days - Estimated days to close
     * @param {number} confidence - Confidence level 0-100
     */
    setTimeline(days, confidence = 80) {
        this.days = days;
        this.confidence = confidence;
        this.render();
    }

    /**
     * Render timeline
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        container.innerHTML = '';

        const timeline = document.createElement('div');
        timeline.style.cssText = `
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
            text-align: center;
        `;

        const days = Math.max(0, this.days);
        const nextMilestone = new Date();
        nextMilestone.setDate(nextMilestone.getDate() + days);

        const dateString = nextMilestone.toLocaleDateString('es-ES', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        timeline.innerHTML = `
            <div style="font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;">
                Estimated Close Date
            </div>
            <div style="font-size: 28px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; font-variant-numeric: tabular-nums;">
                ${days} days
            </div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 16px;">
                ${dateString}
            </div>
            <div style="
                background: linear-gradient(90deg, #667eea 0%, #f093fb 100%);
                height: 4px;
                border-radius: 2px;
                margin-bottom: 12px;
            "></div>
            <div style="font-size: 11px; color: var(--text-light);">
                Confidence: ${this.confidence}%
            </div>
        `;

        container.appendChild(timeline);
    }
}

/**
 * Anomaly Alert Widget
 */
class AnomalyAlertWidget {
    constructor(containerId) {
        this.containerId = containerId;
        this.anomalies = [];
    }

    /**
     * Set anomalies to display
     * @param {Array<Object>} anomalies - Anomalies with {type, severity, description}
     */
    setAnomalies(anomalies) {
        this.anomalies = anomalies || [];
        this.render();
    }

    /**
     * Render anomaly alerts
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        container.innerHTML = '';

        if (this.anomalies.length === 0) {
            container.innerHTML = `
                <div style="
                    background: rgba(76, 175, 80, 0.1);
                    border-left: 3px solid #4caf50;
                    border-radius: 8px;
                    padding: 16px;
                    color: #4caf50;
                    font-size: 13px;
                    text-align: center;
                ">
                    ✓ No anomalies detected
                </div>
            `;
            return;
        }

        const list = document.createElement('div');
        list.style.cssText = 'display: flex; flex-direction: column; gap: 12px;';

        this.anomalies.forEach(anomaly => {
            const item = this.createAnomalyItem(anomaly);
            list.appendChild(item);
        });

        container.appendChild(list);
    }

    /**
     * Create a single anomaly item
     */
    createAnomalyItem(anomaly) {
        const severityColors = {
            'critical': '#f44336',
            'high': '#ff9800',
            'medium': '#ffc107'
        };

        const color = severityColors[anomaly.severity] || '#2196f3';

        const item = document.createElement('div');
        item.style.cssText = `
            display: flex;
            gap: 12px;
            padding: 12px;
            background: ${color}15;
            border-left: 3px solid ${color};
            border-radius: 8px;
        `;

        const icon = document.createElement('div');
        icon.style.cssText = `
            flex-shrink: 0;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            background: ${color};
            color: white;
        `;
        icon.textContent = '!';

        const content = document.createElement('div');
        content.style.cssText = 'flex: 1; font-size: 13px;';
        content.innerHTML = `
            <div style="font-weight: 600; color: ${color}; margin-bottom: 4px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">
                ${anomaly.type}
            </div>
            <div style="color: var(--text-secondary); font-size: 12px;">${anomaly.description}</div>
        `;

        item.appendChild(icon);
        item.appendChild(content);

        return item;
    }
}

/**
 * Recommendation Widget for suggested next actions
 */
class RecommendationWidget {
    constructor(containerId) {
        this.containerId = containerId;
        this.recommendations = [];
    }

    /**
     * Set recommendations
     */
    setRecommendations(recommendations) {
        this.recommendations = recommendations || [];
        this.render();
    }

    /**
     * Render recommendations
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        container.innerHTML = '';

        if (this.recommendations.length === 0) {
            container.innerHTML = `
                <div style="
                    text-align: center;
                    padding: 20px;
                    color: var(--text-secondary);
                    font-size: 13px;
                ">
                    Esperando recomendaciones...
                </div>
            `;
            return;
        }

        const list = document.createElement('div');
        list.style.cssText = 'display: flex; flex-direction: column; gap: 12px;';

        this.recommendations.forEach((rec, idx) => {
            const item = this.createRecommendationItem(rec, idx);
            list.appendChild(item);
        });

        container.appendChild(list);
    }

    /**
     * Create a single recommendation item
     */
    createRecommendationItem(recommendation, index) {
        const urgencyColors = {
            'urgent': '#f44336',
            'high': '#ff9800',
            'normal': '#2196f3',
            'low': '#4caf50'
        };

        const actionIcons = {
            'email': '📧',
            'call': '📞',
            'follow-up': '📋',
            'meeting': '📅',
            'proposal': '📄'
        };

        const urgency = recommendation.urgency || 'normal';
        const color = urgencyColors[urgency] || '#2196f3';
        const icon = actionIcons[recommendation.action_type] || '💡';

        const item = document.createElement('div');
        item.style.cssText = `
            display: flex;
            gap: 12px;
            padding: 12px;
            background: ${color}15;
            border-left: 3px solid ${color};
            border-radius: 8px;
            animation: slideIn 0.3s ease forwards;
            animation-delay: ${index * 0.1}s;
            opacity: 0;
        `;

        const actionIcon = document.createElement('div');
        actionIcon.style.cssText = `
            flex-shrink: 0;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        actionIcon.textContent = icon;

        const content = document.createElement('div');
        content.style.cssText = 'flex: 1; font-size: 13px;';
        content.innerHTML = `
            <div style="font-weight: 600; color: ${color}; margin-bottom: 4px;">
                ${recommendation.recommendation || 'Sin descripción'}
            </div>
            <div style="color: var(--text-secondary); font-size: 12px;">
                ${recommendation.action_type ? `Acción: ${recommendation.action_type}` : ''}
            </div>
        `;

        item.appendChild(actionIcon);
        item.appendChild(content);

        return item;
    }
}

// Add CSS animation for slide-in effect
if (!document.getElementById('prediction-widgets-styles')) {
    const style = document.createElement('style');
    style.id = 'prediction-widgets-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-10px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
    `;
    document.head.appendChild(style);
}

// Export for use in HTML
window.PredictionWidgets = {
    PredictionGauge,
    RiskFactorsWidget,
    PositiveFactorsWidget,
    TimelineWidget,
    AnomalyAlertWidget,
    RecommendationWidget
};
