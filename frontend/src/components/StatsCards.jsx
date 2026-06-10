import React from 'react';

export default function StatsCards({ stats }) {
  if (!stats) return null;

  const cards = [
    { label: 'Total Emails', value: stats.total_emails, icon: '✉️', color: '#6366f1' },
    { label: 'Pending Emails', value: stats.pending_emails, icon: '⏳', color: '#eab308' },
    { label: 'Spam Emails', value: stats.spam_emails, icon: '🚫', color: '#6b7280' },
    { label: 'Escalated Emails', value: stats.escalated_emails, icon: '⚠️', color: '#f97316' },
    { label: 'Critical Emails', value: stats.critical_emails, icon: '🚨', color: '#ef4444' },
    { label: 'Contacts', value: stats.total_contacts, icon: '👥', color: '#10b981' },
    { label: 'Threads', value: stats.total_threads, icon: '💬', color: '#06b6d4' }
  ];

  return (
    <div className="stats-container">
      {cards.map((card, i) => (
        <div key={i} className="stats-card" style={{ borderLeft: `4px solid ${card.color}` }}>
          <div className="stats-card-header">
            <span className="stats-icon">{card.icon}</span>
            <span className="stats-label">{card.label}</span>
          </div>
          <div className="stats-value">{card.value}</div>
        </div>
      ))}
    </div>
  );
}
