import React, { useMemo, memo, useState } from 'react';
import { Activity, ShieldAlert, AlertTriangle, TrendingUp, ChevronRight, ChevronLeft, PanelLeftClose, PanelLeftOpen } from 'lucide-react';

const getIntensityBg = (score) => {
  const s = Number(score) || 0;
  if (s >= 50) return 'bg-destructive';
  if (s >= 35) return 'bg-orange-500';
  if (s >= 20) return 'bg-amber-500';
  if (s >= 10) return 'bg-yellow-500';
  return 'bg-primary';
};

const getIntensityText = (score) => {
  const s = Number(score) || 0;
  if (s >= 50) return 'text-destructive';
  if (s >= 35) return 'text-orange-500';
  if (s >= 20) return 'text-amber-500';
  if (s >= 10) return 'text-yellow-500';
  return 'text-primary';
};

const AreaRow = ({ area }) => {
  if (!area) return null;

  const score30d = Number(area.crime_index_30d || area.crime_index) || 0;
  const scoreCum = Number(area.crime_index_cumulative) || 0;

  return (
    <div className="flex items-center justify-between p-3 mb-2 bg-card border border-border rounded-lg hover:bg-accent transition-all cursor-pointer group">
      <div className="flex items-center gap-3 overflow-hidden">
        <div className={`w-1 h-6 rounded-full shrink-0 ${getIntensityBg(score30d)}`} />
        <span className="font-medium text-foreground truncate text-sm">{area.area || 'Unknown Sector'}</span>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="flex flex-col items-end min-w-[40px]">
          <span className={`text-sm font-bold ${getIntensityText(score30d)}`}>
            {score30d.toFixed(1)}
          </span>
          <span className="text-[10px] text-muted-foreground font-mono uppercase">30d</span>
        </div>
        <div className="flex flex-col items-end min-w-[40px]">
          <span className="text-sm font-bold text-foreground">
            {scoreCum.toFixed(1)}
          </span>
          <span className="text-[10px] text-muted-foreground font-mono uppercase">Cum</span>
        </div>
        <ChevronRight size={14} className="text-muted-foreground group-hover:text-foreground transition-colors" />
      </div>
    </div>
  );
};

export const IndexPanel = memo(({ data, loading, refetch }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const stats = useMemo(() => {
    try {
      if (!Array.isArray(data) || data.length === 0) {
        return { sorted: [], avg30d: 0, totalCum: 0 };
      }

      const sorted = [...data].sort((a, b) => {
        const scoreA = Number(a?.crime_index_30d || a?.crime_index) || 0;
        const scoreB = Number(b?.crime_index_30d || b?.crime_index) || 0;
        return scoreB - scoreA;
      });

      const sum30d = data.reduce((acc, curr) => acc + (Number(curr?.crime_index_30d || curr?.crime_index) || 0), 0);
      const totalCum = data.reduce((acc, curr) => acc + (Number(curr?.event_count_cumulative || curr?.event_count_30d) || 0), 0);
      
      return {
        sorted,
        avg30d: (sum30d / data.length).toFixed(1),
        totalCum
      };
    } catch (err) {
      console.error('Error calculating dashboard stats:', err);
      return { sorted: [], avg30d: '0.0', totalCum: 0 };
    }
  }, [data]);

  return (
    <div 
      className={`fixed top-4 right-4 h-[calc(100vh-32px)] transition-all duration-500 ease-in-out z-[1000] flex ${
        isCollapsed ? 'translate-x-[364px]' : 'translate-x-0'
      }`}
    >
      {/* Collapse Toggle Button */}
      <button 
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute left-0 -translate-x-full h-12 w-8 bg-background/95 backdrop-blur border border-border border-r-0 rounded-l-xl flex items-center justify-center text-foreground hover:bg-accent transition-colors shadow-lg"
        title={isCollapsed ? "Expand Terminal" : "Collapse Terminal"}
      >
        {isCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
      </button>

      {/* Main Panel Content */}
      <div className="w-[400px] h-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border border-border rounded-xl rounded-l-none shadow-xl flex flex-col overflow-hidden">
        <div className="p-6 pb-4 border-b border-border space-y-1">
          <div className="flex items-center gap-2">
            <ShieldAlert className="text-primary h-6 w-6" />
            <h1 className="text-xl font-bold tracking-tight text-foreground">Dhaka City Index</h1>
          </div>
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Regional Intelligence Terminal</p>
        </div>

        <div className="p-6 space-y-6 flex-1 flex flex-col min-h-0">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-secondary/50 border border-border space-y-1">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">System Avg</span>
              <div className={`text-2xl font-bold ${getIntensityText(stats.avg30d)}`}>
                {stats.avg30d}
              </div>
            </div>
            <div className="p-4 rounded-lg bg-secondary/50 border border-border space-y-1">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Unified Events</span>
              <div className="text-2xl font-bold text-foreground">
                {stats.totalCum}
              </div>
            </div>
          </div>

          <button 
            onClick={refetch}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-foreground text-background font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 transition-all active:scale-[0.98]"
          >
            <Activity size={16} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Analyzing...' : 'Live Refetch'}
          </button>

          <div className="flex-1 flex flex-col min-h-0 space-y-4">
            <div className="flex items-center justify-between text-[10px] font-bold text-muted-foreground uppercase tracking-widest px-2">
              <div className="flex items-center gap-1.5">
                <AlertTriangle size={12} />
                Risk Rankings
              </div>
              <span>Scores</span>
            </div>
            
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
              {stats.sorted.length > 0 ? (
                stats.sorted.map((area, idx) => (
                  <AreaRow key={area?.area || idx} area={area} />
                ))
              ) : !loading && (
                <div className="h-40 flex items-center justify-center text-sm text-muted-foreground italic">
                  Waiting for signals...
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-border bg-secondary/30">
          <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
            <TrendingUp size={14} />
            <span>Monitoring {stats.sorted.length} active sectors</span>
          </div>
        </div>
      </div>
    </div>
  );
});
