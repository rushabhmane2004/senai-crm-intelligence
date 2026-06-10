import React from 'react';

export default function RagContextPanel({ email }) {
  if (!email) return null;

  const rawEntities = email.raw_entities || {};
  const ragUsed = rawEntities.rag_used;
  const ragContext = rawEntities.rag_context || [];
  const skipReason = rawEntities.rag_skip_reason;
  const ragError = rawEntities.rag_error;

  return (
    <div className="rag-panel-container">
      <h3>📖 RAG Policy Grounding Context</h3>

      {!ragUsed ? (
        <div className="rag-inactive">
          <div className="rag-status-badge inactive">RAG Grounding Offline / Skipped</div>
          {skipReason && <p className="rag-reason">Reason: {skipReason}</p>}
          {ragError && <p className="rag-error-text">Error: {ragError}</p>}
        </div>
      ) : (
        <div className="rag-active">
          <div className="rag-status-badge active">🛡️ Grounding Active</div>
          {rawEntities.rag_query && (
            <div className="rag-query-box">
              <span className="field-label">Generated Query:</span>
              <code className="rag-query">{rawEntities.rag_query}</code>
            </div>
          )}
          
          <div className="rag-chunks">
            {ragContext.length === 0 ? (
              <p className="no-chunks text-gray">No policy references matched the generated query.</p>
            ) : (
              ragContext.map((chunk, idx) => {
                const scorePercent = (chunk.similarity_score * 100).toFixed(1);
                return (
                  <div key={idx} className="rag-chunk-card">
                    <div className="rag-chunk-header">
                      <div className="rag-chunk-source">
                        <span className="doc-icon">📄</span>
                        <span className="doc-name font-bold">{chunk.source_doc}</span>
                        {chunk.policy_ref && (
                          <span className="policy-ref font-mono">[{chunk.policy_ref}]</span>
                        )}
                      </div>
                      <span className="similarity-badge">
                        Match: {scorePercent}%
                      </span>
                    </div>
                    <div className="rag-chunk-text">
                      "{chunk.chunk_preview}"
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
