import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet.heat';
import { debounce } from '../utils/debounce';

const ZOOM_CONFIG = {
  // zoom: { radius, blur, maxPoints }
  10: { radius: 35, blur: 25, maxPoints: 300 },
  12: { radius: 25, blur: 18, maxPoints: 800 },
  14: { radius: 18, blur: 12, maxPoints: 2000 },
  16: { radius: 12, blur:  8, maxPoints: Infinity },
};

function getZoomConfig(zoom) {
  const levels = Object.keys(ZOOM_CONFIG).map(Number).sort((a, b) => b - a);
  const matched = levels.find(z => zoom >= z) ?? levels[levels.length - 1];
  return ZOOM_CONFIG[matched];
}

export function useHeatmapLayer(map, allPoints) {
  const heatLayerRef = useRef(null);

  useEffect(() => {
    if (!map) return;

    // Fix for potential HMR issues or double mount
    if (heatLayerRef.current) {
        heatLayerRef.current.remove();
    }

    heatLayerRef.current = L.heatLayer([], {
      radius: 25,
      blur: 15,
      maxZoom: 17,
      gradient: {
        0.2: 'blue',
        0.4: 'cyan',
        0.6: 'lime',
        0.8: 'yellow',
        1.0: 'red'
      }
    }).addTo(map);

    return () => {
      heatLayerRef.current?.remove();
      heatLayerRef.current = null;
    };
  }, [map]);

  useEffect(() => {
    if (!map || !heatLayerRef.current || !allPoints) return;

    function updateVisible() {
      if (!heatLayerRef.current) return;
      
      const bounds = map.getBounds();
      const zoom = map.getZoom();
      const { radius, blur, maxPoints } = getZoomConfig(zoom);

      const visible = allPoints
        .filter(p => bounds.contains([p.lat, p.lng]))
        .slice(0, maxPoints);

      heatLayerRef.current.setOptions({ radius, blur });
      heatLayerRef.current.setLatLngs(
        visible.map(p => [p.lat, p.lng, p.intensity_score ?? p.crime_index_30d ?? 1])
      );
    }

    const debouncedUpdate = debounce(updateVisible, 350);
    
    updateVisible(); // run once on data/map change
    map.on('moveend zoomend', debouncedUpdate);

    return () => {
        map.off('moveend zoomend', debouncedUpdate);
    };
  }, [map, allPoints]);

  return null;
}
