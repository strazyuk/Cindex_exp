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
    startTransition(() => {
      refetch();
    });
  };

  return (
    <div className="relative w-full h-screen bg-background text-foreground overflow-hidden font-sans">
      {/* Background Map with Suspense fallback */}
      <Suspense fallback={
        <div className="absolute inset-0 flex items-center justify-center bg-background/50 backdrop-blur-sm z-50">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
      }>
        <CrimeMap data={data} />
      </Suspense>

      {/* Floating UI Panel */}
      <IndexPanel 
        data={data} 
        loading={loading || isPending} 
        refetch={handleRefetch} 
      />

      {/* Initial Loading Overlay */}
      {loading && data.length === 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-background z-[2000] p-6 text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-6"></div>
          <p className="text-sm font-bold text-muted-foreground uppercase tracking-widest animate-pulse">
            Synchronizing Dhaka Intelligence Layer...
          </p>
        </div>
      )}

      {/* Error Overlay */}
      {error && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 bg-destructive text-destructive-foreground px-6 py-3 rounded-lg z-[2000] flex items-center gap-3 shadow-2xl border border-white/10 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <AlertTriangle size={18} />
          <span className="text-sm font-bold tracking-tight">System Feed Error: {error}</span>
        </div>
      )}
    </div>
  );
}

export default App;
