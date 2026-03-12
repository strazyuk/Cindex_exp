import { useEffect, useCallback } from 'react';
import { useCrimeStore } from '../store/useCrimeStore';

export const useCrimeData = () => {
  const { data, allData, loading, error, fetchData, lastRefreshed } = useCrimeStore();

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, allData, loading, error, refetch, lastRefreshed };
};
