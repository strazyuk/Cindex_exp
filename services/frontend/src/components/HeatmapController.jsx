import { useMap } from 'react-leaflet';
import { useHeatmapLayer } from '../hooks/useHeatmapLayer';
import { useCrimeStore } from '../store/useCrimeStore';

export function HeatmapController() {
  const map = useMap();
  // Subscribe specifically to the data slice needed for the map
  const crimeData = useCrimeStore(state => state.data);

  useHeatmapLayer(map, crimeData);

  return null; // This component has no UI, it only manages the heatmap layer
}
