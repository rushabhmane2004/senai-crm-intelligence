import React from 'react';

export default function EmailInspector({ email }) {
  if (!email) {
    return (
      <div className="empty-panel">
        <p>Select an email from the queue to inspect details, agent reasoning trace, and grounding context.</p>
      </div>
    );
  }

  const rawEntities = email.raw_entities || {};
  const emailSubject = email.subject || rawEntities.subject || "No subject available";
  const emailBody = email.body || rawEntities.body || "No body available";
  const senderAddress = email.sender || rawEntities.sender || "unknown@domain.com";

  return (
    <div className="inspector-container">
      <h3>✉️ Email Inspector</h3>
      <div className="inspector-fields">
        <div className="field-row">
          <span className="field-label">Message ID:</span>
          <span className="field-value font-mono">{email.message_id}</span>
        </div>
        <div className="field-row">
          <span className="field-label">Sender:</span>
          <span className="field-value font-mono">{senderAddress}</span>
        </div>
        <div className="field-row">
          <span className="field-label">Subject:</span>
          <span className="field-value font-bold">{emailSubject}</span>
        </div>
        <div className="field-row-multi">
          <span className="field-label">Body Preview:</span>
          <div className="field-body">{emailBody}</div>
        </div>
        <div className="field-grid">
          <div>
            <span className="field-label">Category:</span>
            <span className="badge badge-category">{email.category || 'Other'}</span>
          </div>
          <div>
            <span className="field-label">Urgency:</span>
            <span className="badge badge-urgency">{email.urgency || 'Low'}</span>
          </div>
          <div>
            <span className="field-label">Status:</span>
            <span className="badge badge-status">{email.status}</span>
          </div>
          <div>
            <span className="field-label">Priority:</span>
            <span className="font-bold">{email.priority_score}</span>
          </div>
          <div>
            <span className="field-label">Human Needed:</span>
            <span className="font-bold">{email.requires_human ? 'Yes' : 'No'}</span>
          </div>
        </div>

        <div className="rag-triage-info">
          <h4>🤖 RAG Policy Grounding Info</h4>
          <div className="field-row">
            <span className="field-label">RAG Used:</span>
            <span className={`font-bold ${rawEntities.rag_used ? 'text-green' : 'text-gray'}`}>
              {rawEntities.rag_used ? 'TRUE' : 'FALSE'}
            </span>
          </div>
          {rawEntities.rag_used && (
            <div className="field-row">
              <span className="field-label">RAG Query:</span>
              <span className="field-value italic">"{rawEntities.rag_query}"</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
