import React, { useEffect, useState } from 'react';
import { fetchEmailStatus } from '../services/api';

const DEMO_MESSAGE_IDS = [
  "msg_038",
  "msg_052",
  "msg_020",
  "msg_060",
  "msg_033",
  "msg_041",
  "msg_031"
];

export default function CriticalQueue({ selectedId, onSelectEmail }) {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadQueue() {
      try {
        const promises = DEMO_MESSAGE_IDS.map(id => fetchEmailStatus(id).catch(() => null));
        const results = await Promise.all(promises);
        setEmails(results.filter(Boolean));
      } catch (err) {
        console.error('Error loading critical queue:', err);
      } finally {
        setLoading(false);
      }
    }
    loadQueue();
  }, []);

  const getUrgencyBadgeClass = (urgency) => {
    switch (urgency?.toLowerCase()) {
      case 'critical': return 'badge badge-critical';
      case 'high': return 'badge badge-high';
      case 'medium': return 'badge badge-medium';
      default: return 'badge badge-low';
    }
  };

  const getSafetyBadgeClass = (safety) => {
    switch (safety?.toLowerCase()) {
      case 'blocked': return 'badge badge-blocked';
      case 'restricted': return 'badge badge-restricted';
      case 'safe': return 'badge badge-safe';
      default: return 'badge badge-low';
    }
  };

  if (loading) {
    return <div className="queue-loading">Loading Triage Queue...</div>;
  }

  return (
    <div className="queue-container">
      <h3>🚨 Critical Escalation Queue</h3>
      <div className="queue-list">
        {emails.map((email) => {
          const isSelected = email.message_id === selectedId;
          const allowed = email.auto_reply_allowed;
          return (
            <div
              key={email.message_id}
              className={`queue-card ${isSelected ? 'selected' : ''}`}
              onClick={() => onSelectEmail(email)}
            >
              <div className="queue-card-top">
                <span className="msg-id">{email.message_id}</span>
                <span className={getUrgencyBadgeClass(email.urgency)}>{email.urgency || 'Low'}</span>
              </div>
              <div className="queue-category">{email.category || 'Other'}</div>
              <div className="queue-card-meta">
                <span>Score: {email.priority_score}</span>
                {email.safety_level && (
                  <span className={getSafetyBadgeClass(email.safety_level)}>
                    {email.safety_level.toUpperCase()}
                  </span>
                )}
              </div>
              <div className="queue-card-footer">
                {allowed ? (
                  <span className="badge badge-auto-allowed">🤖 Auto-Reply Allowed</span>
                ) : (
                  <span className="badge badge-auto-blocked">🚫 Auto-Reply Blocked</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
