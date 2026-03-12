import { Suspense, lazy, useTransition } from 'react';
import { useCrimeData } from './hooks/useCrimeData';
import { IndexPanel } from './components/IndexPanel';
import { AlertTriangle } from 'lucide-react';
import './index.css';

// Lazy load the heavy map component to prioritize FCP
const CrimeMap = lazy(() => import('./components/CrimeMap').then(module => ({ default: module.CrimeMap })));

function App() {
  const { data, loading, error, refetch } = useCrimeData();
  const [isPending, startTransition] = useTransition();

  const handleRefetch = () => {
    // Concurrent update: keeps UI responsive during background refetch
    startTransition(() => {
      refetch();
    });
  };

  return (
    <div className="app-container">
      {/* Background Map with Suspense fallback */}
      <Suspense fallback={
        <div className="loading-overlay" style={{ background: 'transparent' }}>
          <div className="spinner"></div>
        </div>
      }>
        <CrimeMap data={data} />
      </Suspense>

      {/* Floating UI Panel - Atomic updates via memoization and store */}
      <IndexPanel 
        data={data} 
        loading={loading || isPending} 
        refetch={handleRefetch} 
      />

      {/* Initial Loading Overlay */}
      {loading && data.length === 0 && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p style={{ marginTop: '20px', color: 'var(--text-secondary)', fontWeight: '500' }}>
            Synchronizing Dhaka Crime Intelligence...
          </p>
        </div>
      )}

      {/* Error Overlay */}
      {error && (
        <div className="error-toast" style={{
          position: 'absolute',
          bottom: '32px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'var(--intensity-critical)',
          color: 'white',
          padding: '12px 24px',
          borderRadius: '12px',
          zIndex: 2000,
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
          animation: 'pulse 2s infinite'
        }}>
          <AlertTriangle size={20} />
          <span style={{ fontWeight: '600' }}>Live Feed Error: {error}</span>
        </div>
      )}
    </div>
  );
}

export default App;
