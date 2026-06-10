import React, { useEffect, useState } from 'react';
import { fetchThreadHistory } from '../services/api';

export default function ThreadHistoryPanel({ sender }) {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!sender) {
      setHistory(null);
      return;
    }

    async function loadHistory() {
      setLoading(true);
      setError(null);
      setHistory(null);
      try {
        const data = await fetchThreadHistory(sender);
        setHistory(data);
      } catch (err) {
        console.error('Error fetching thread history:', err);
        // Clean error message, often 404 if contact has no DB profile yet
        setError(err.message.includes('404') 
          ? 'No contact profile found. Thread view available through backend endpoint.'
          : 'Failed to load thread history.'
        );
      } finally {
        setLoading(false);
      }
    }

    loadHistory();
  }, [sender]);

  if (!sender) {
    return (
      <div className="thread-panel-container empty">
        <h3>💬 Thread History & Contact Profile</h3>
        <p className="empty-text">Select an email to view sender's thread history.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="thread-panel-container">
        <h3>💬 Thread History & Contact Profile</h3>
        <div className="panel-loading">Fetching customer history...</div>
      </div>
    );
  }

  if (error || !history) {
    return (
      <div className="thread-panel-container">
        <h3>💬 Thread History & Contact Profile</h3>
        <div className="panel-error-box">
          <p>{error || 'No historical thread data found for this contact.'}</p>
        </div>
      </div>
    );
  }

  const { contact, threads } = history;
  const churnRiskColor = contact.churn_risk_score > 0.6 ? '#ef4444' : contact.churn_risk_score > 0.3 ? '#f97316' : '#10b981';

  return (
    <div className="thread-panel-container">
      <h3>💬 Thread History & Contact Profile</h3>

      {/* Contact Profile Summary */}
      <div className="contact-profile-card">
        <div className="profile-header">
          <div>
            <h4 className="profile-name">{contact.name || 'Anonymous Contact'}</h4>
            <p className="profile-company text-gray">{contact.company || 'Direct Customer'}</p>
          </div>
          <span className="profile-email font-mono">{contact.email}</span>
        </div>
        <div className="profile-stats">
          <div className="profile-stat-box">
            <span className="stat-label">Account Value</span>
            <span className="stat-value font-bold text-green">
              ${contact.account_value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
          <div className="profile-stat-box">
            <span className="stat-label">Churn Risk</span>
            <span 
              className="stat-value font-bold" 
              style={{ color: churnRiskColor }}
            >
              {(contact.churn_risk_score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="profile-stat-box">
            <span className="stat-label">Lifecycle Status</span>
            <span className="stat-value font-bold text-blue">{contact.status}</span>
          </div>
        </div>
      </div>

      {/* Threads list */}
      <div className="threads-list">
        {threads.length === 0 ? (
          <p className="no-threads text-gray">No email threads recorded for this contact.</p>
        ) : (
          threads.map((thread) => (
            <div key={thread.id} className="thread-group-card">
              <div className="thread-header">
                <span className="thread-subject font-bold">Subject: {thread.subject}</span>
                <span className={`badge thread-status-badge status-${thread.status.toLowerCase()}`}>
                  {thread.status}
                </span>
              </div>
              <div className="thread-meta text-xs text-gray">
                Thread ID: <span className="font-mono">{thread.thread_id}</span> | Last updated: {new Date(thread.last_updated_at).toLocaleString()}
              </div>

              {/* Message loop within thread */}
              <div className="thread-messages">
                {thread.emails.map((msg, index) => {
                  const isIncoming = msg.sender.toLowerCase() === sender.toLowerCase();
                  return (
                    <div key={msg.id} className={`message-item ${isIncoming ? 'incoming' : 'outgoing'}`}>
                      <div className="message-item-header">
                        <span className="message-sender font-bold">
                          {isIncoming ? '📥 Customer' : '📤 CRM Auto-Reply'}
                        </span>
                        <span className="message-time text-xs">
                          {new Date(msg.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="message-body">{msg.body}</div>
                      
                      {/* Show categories for incoming emails */}
                      {isIncoming && (
                        <div className="message-badges">
                          <span className="badge badge-category">{msg.category}</span>
                          <span className={`badge urgency-${msg.urgency?.toLowerCase()}`}>{msg.urgency}</span>
                          <span className="badge badge-status">Status: {msg.status}</span>
                        </div>
                      )}

                      {/* Show agent action execution details if there's any */}
                      {msg.actions && msg.actions.length > 0 && (
                        <div className="message-actions-log">
                          {msg.actions.map((act) => (
                            <div key={act.id} className="action-entry">
                              <span className="action-label">🤖 Agent Action Taken:</span>
                              <span className="action-type font-semibold">{act.action_type}</span>
                              {act.proposed_content && (
                                <div className="action-draft">
                                  <strong>Reply Sent:</strong> "{act.proposed_content}"
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
