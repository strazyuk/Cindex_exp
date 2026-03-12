import React, { useMemo } from 'react';
import { Activity, ShieldAlert, AlertTriangle, TrendingUp, ChevronRight } from 'lucide-react';

const getIntensityClass = (score) => {
  if (score >= 50) return 'intensity-critical';
  if (score >= 35) return 'intensity-high';
  if (score >= 20) return 'intensity-moderate';
  if (score >= 10) return 'intensity-low';
  return 'intensity-minimal';
};

import { List } from 'react-window';

const AreaRow = ({ index, style, items }) => {
  const area = items[index];
  const score30d = area.crime_index_30d || area.crime_index || 0;
  const scoreCum = area.crime_index_cumulative || 0;

  return (
    <div style={style}>
      <li className="area-item" style={{ height: 'calc(100% - 10px)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ 
            width: '4px', 
            height: '24px', 
            borderRadius: '2px', 
            background: `var(--${getIntensityClass(score30d)})` 
          }} />
          <span className="area-name">{area.area}</span>
        </div>
        
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <span className={`area-score ${getIntensityClass(score30d)}`} style={{ minWidth: '40px', textAlign: 'right' }}>
            {score30d.toFixed(1)}
          </span>
          <span className="area-score" style={{ color: '#818cf8', fontSize: '0.95rem', minWidth: '40px', textAlign: 'right' }}>
            {scoreCum.toFixed(1)}
          </span>
          <ChevronRight size={14} color="var(--text-muted)" />
        </div>
      </li>
    </div>
  );
};

export const IndexPanel = React.memo(({ data, loading, refetch }) => {
  // Memoize data calculations for performance
  const stats = useMemo(() => {
    if (!data || data.length === 0) return { sorted: [], avg30d: 0, totalCum: 0 };

    const sorted = [...data].sort((a, b) => {
      const scoreA = a.crime_index_30d || a.crime_index || 0;
      const scoreB = b.crime_index_30d || b.crime_index || 0;
      return scoreB - scoreA;
    });

    const sum30d = data.reduce((acc, curr) => acc + (curr.crime_index_30d || curr.crime_index || 0), 0);
    const totalCum = data.reduce((acc, curr) => acc + (curr.event_count_cumulative || curr.event_count_30d || 0), 0);
    
    return {
      sorted,
      avg30d: (sum30d / data.length).toFixed(1),
      totalCum
    };
  }, [data]);

  if (!data) return null;

  return (
    <div className="panel-container">
      <div className="panel-header">
        <h1 className="panel-title">
          <ShieldAlert size={28} color="var(--intensity-critical)" />
          Dhaka City Index
        </h1>
        <p className="panel-subtitle">Regional Safety Intelligence (30d & All-Time)</p>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">System Avg</div>
          <div className={`stat-value ${getIntensityClass(stats.avg30d)}`}>
            {stats.avg30d}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Unified Events</div>
          <div className="stat-value" style={{ color: 'var(--text-primary)' }}>
            {stats.totalCum}
          </div>
        </div>
      </div>

      <div style={{ marginBottom: '32px' }}>
        <button 
          className="btn-primary"
          onClick={refetch}
          disabled={loading}
        >
          <Activity size={18} />
          {loading ? 'Analyzing...' : 'Live Refetch'}
        </button>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <div className="area-list-header">
          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={14} /> Regional Risk Rankings
          </span>
          <span style={{ display: 'flex', gap: '20px' }}>
            <span title="Last 30 Days">30d</span>
            <span title="All Time Cumulative">Cum</span>
          </span>
        </div>
        
        <div className="area-list-viewport" style={{ flex: 1, minHeight: 0 }}>
          {stats.sorted.length > 0 ? (
            <List
              height={400}
              rowCount={stats.sorted.length}
              rowHeight={65}
              width="100%"
              rowComponent={AreaRow}
              rowProps={{ items: stats.sorted }}
              className="scrollbar-hidden"
            />
          ) : !loading && (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
              Waiting for live signals...
            </div>
          )}
        </div>
      </div>

      <div className="panel-footer" style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid var(--glass-border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          <TrendingUp size={16} />
          <span>Showing {stats.sorted.length} active crime hotspots</span>
        </div>
      </div>
    </div>
  );
});
