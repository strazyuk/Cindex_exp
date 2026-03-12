import { create } from 'zustand';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost/api';

export const useCrimeStore = create((set, get) => ({
  data: [],         // items with valid coords (for map)
  allData: [],      // all items (for panel stats)
  loading: true,
  error: null,
  lastRefreshed: null,

  fetchData: async () => {
    try {
      set({ loading: true, error: null });
      const response = await axios.get(`${API_URL}/indexes`);
      
      const rawData = response.data;
      let parsedData = [];
      
      if (Array.isArray(rawData)) {
        parsedData = rawData;
      } else if (typeof rawData === 'object' && rawData !== null) {
        parsedData = Object.entries(rawData).map(([area, details]) => ({
          area,
          ...details
        }));
      }

      // Only items with valid coordinates can appear on the map
      const withCoords = parsedData.filter(item =>
        item.area &&
        item.lat != null && item.lng != null &&
        !isNaN(Number(item.lat)) && !isNaN(Number(item.lng))
      );

      set({ 
        allData: parsedData, 
        data: withCoords, 
        loading: false, 
        lastRefreshed: new Date() 
      });
    } catch (err) {
      console.error('Error fetching crime data:', err);
      set({ error: err.message || 'Failed to fetch crime data', loading: false });
    }
  }
}));
