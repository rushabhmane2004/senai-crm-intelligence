import React, { useEffect, useState } from 'react';
import StatsCards from './components/StatsCards';
import CriticalQueue from './components/CriticalQueue';
import EmailInspector from './components/EmailInspector';
import AgentActionPanel from './components/AgentActionPanel';
import RagContextPanel from './components/RagContextPanel';
import ThreadHistoryPanel from './components/ThreadHistoryPanel';
import { fetchStats } from './services/api';
import './App.css';

function App() {
  const [stats, setStats] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState(null);
  const [refreshCount, setRefreshCount] = useState(0);

  useEffect(() => {
    async function loadStats() {
      setLoadingStats(true);
      setStatsError(null);
      try {
        const data = await fetchStats();
        setStats(data);
      } catch (err) {
        console.error('Error loading stats:', err);
        setStatsError('Failed to fetch CRM stats from backend.');
      } finally {
        setLoadingStats(false);
      }
    }
    loadStats();
  }, [refreshCount]);

  const handleSelectEmail = (email) => {
    setSelectedEmail(email);
  };

  const handleRefresh = () => {
    setRefreshCount(prev => prev + 1);
  };

  return (
    <div className="app-container">
      {/* Header Section */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1>Agentic CRM Intelligence Platform</h1>
          <p className="subtitle">Real-time Email Operations, RAG Policy Grounding, and Safe Triage Agent</p>
        </div>
        <button className="refresh-button" onClick={handleRefresh} disabled={loadingStats}>
          {loadingStats ? 'Refreshing...' : '🔄 Refresh Data'}
        </button>
      </header>

      {/* Stats Cards Section */}
      {statsError ? (
        <div className="stats-error-bar">{statsError}</div>
      ) : (
        <StatsCards stats={stats} />
      )}

      {/* Main Grid Layout */}
      <main className="dashboard-grid">
        {/* Left column: Critical queue */}
        <section className="col-queue">
          <CriticalQueue 
            selectedId={selectedEmail?.message_id} 
            onSelectEmail={handleSelectEmail} 
          />
        </section>

        {/* Center column: Email details & thread history */}
        <section className="col-inspect">
          <EmailInspector email={selectedEmail} />
          <ThreadHistoryPanel sender={selectedEmail?.sender} />
        </section>

        {/* Right column: CRM Action & reasoning trace, RAG Policy Context */}
        <section className="col-agent">
          <AgentActionPanel messageId={selectedEmail?.message_id} />
          <RagContextPanel email={selectedEmail} />
        </section>
      </main>
    </div>
  );
}

export default App;
