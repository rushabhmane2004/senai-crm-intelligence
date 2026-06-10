import React, { useEffect, useState } from 'react';
import { fetchEmailAction } from '../services/api';

export default function AgentActionPanel({ messageId }) {
  const [actionData, setActionData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!messageId) return;

    async function loadAction() {
      setLoading(true);
      setError(null);
      setActionData(null);
      try {
        const data = await fetchEmailAction(messageId);
        setActionData(data.agent_action);
      } catch (err) {
        console.error('Error fetching action details:', err);
        setError('Failed to load action trace from backend.');
      } finally {
        setLoading(false);
      }
    }
    loadAction();
  }, [messageId]);

  if (loading) {
    return <div className="panel-loading">Analyzing Action & Reasoning Trace...</div>;
  }

  if (error) {
    return <div className="panel-error">{error}</div>;
  }

  if (!actionData) return null;

  const getSafetyBadgeClass = (safety) => {
    switch (safety?.toLowerCase()) {
      case 'blocked': return 'badge badge-blocked';
      case 'restricted': return 'badge badge-restricted';
      case 'safe': return 'badge badge-safe';
      default: return 'badge badge-low';
    }
  };

  return (
    <div className="action-panel-container">
      <h3>🛠️ CRM Safe Action Planner</h3>
      
      <div className="action-grid">
        <div className="field-row">
          <span className="field-label">Agent Version:</span>
          <span className="field-value font-mono">triage-agent-v1</span>
        </div>
        <div className="field-row">
          <span className="field-label">Triage Decision:</span>
          <span className="field-value font-bold">{actionData.decision}</span>
        </div>
        <div className="field-row">
          <span className="field-label">Safety Status:</span>
          <span className={getSafetyBadgeClass(actionData.safety_level)}>
            {actionData.safety_level?.toUpperCase()}
          </span>
        </div>
        <div className="field-row">
          <span className="field-label">Recommended Action:</span>
          <span className="field-value font-semibold text-orange">{actionData.recommended_action}</span>
        </div>
        <div className="field-row">
          <span className="field-label">Escalation Target:</span>
          <span className="field-value text-red font-bold font-mono">{actionData.escalation_team || 'None'}</span>
        </div>
      </div>

      <div className="action-badges">
        {actionData.auto_reply_allowed ? (
          <span className="badge badge-auto-allowed">🤖 Auto-Reply Allowed</span>
        ) : (
          <span className="badge badge-auto-blocked">🚫 Auto-Reply Blocked (Ransomware/Legal/Privacy rule)</span>
        )}
        {actionData.requires_human_approval ? (
          <span className="badge badge-human-needed">👥 Human Approval Required</span>
        ) : (
          <span className="badge badge-human-not-needed">⚡ Auto-execution Eligible</span>
        )}
      </div>

      {actionData.draft_reply && (
        <div className="draft-reply-section">
          <h4>📝 Grounded AI Draft Reply</h4>
          <div className="draft-reply-box">
            <p className="draft-header">To: customer (draft)</p>
            <p className="draft-body">{actionData.draft_reply}</p>
          </div>
        </div>
      )}

      {actionData.next_actions && actionData.next_actions.length > 0 && (
        <div className="next-actions-section">
          <h4>📋 Next Action Checklists</h4>
          <ul className="next-actions-list">
            {actionData.next_actions.map((act, i) => (
              <li key={i}>
                <input type="checkbox" defaultChecked readOnly />
                <span>{act}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {actionData.reasoning_trace && actionData.reasoning_trace.length > 0 && (
        <div className="reasoning-trace-section">
          <h4>🔍 Triage Reasoning Trace (Audit Log)</h4>
          <div className="reasoning-steps">
            {actionData.reasoning_trace.map((step, idx) => (
              <div key={idx} className="reasoning-step-card">
                <div className="step-number">Step {step.step}</div>
                <div className="step-content">
                  <div><strong>Observation:</strong> {step.observation}</div>
                  <div><strong>Reasoning:</strong> {step.reasoning}</div>
                  <div><strong>Result:</strong> {step.result}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
