import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import React, { useEffect, useMemo } from 'react';

// Fix Leaflet icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Optimized marker color mapping (5-Tier Intensity)
// Using explicit HSL strings with shorter scales for higher sensitivity
const getIntensityLevel = (score) => {
  if (score >= 50) return { label: 'Critical', color: 'hsl(0, 90%, 50%)', class: 'intensity-critical' };
  if (score >= 35) return { label: 'High', color: 'hsl(15, 90%, 55%)', class: 'intensity-high' };
  if (score >= 20) return { label: 'Moderate', color: 'hsl(35, 90%, 55%)', class: 'intensity-moderate' };
  if (score >= 10) return { label: 'Low', color: 'hsl(70, 80%, 50%)', class: 'intensity-low' };
  return { label: 'Minimal', color: 'hsl(140, 70%, 50%)', class: 'intensity-minimal' };
};

// Component to handle map bounds when data changes
const MapBounds = React.memo(({ data }) => {
  const map = useMap();

  useEffect(() => {
    if (data && data.length > 0) {
      // Leaflet automatically handles bounds for Dhaka City.
    }
  }, [data, map]);

  return null;
});

export const CrimeMap = React.memo(({ data }) => {
  // Center of Dhaka default
  const defaultCenter = [23.777, 90.399];
  
  // Strict bounds for Dhaka City
  const dhakaBounds = [
    [23.65, 90.28], // South West
    [23.95, 90.53]  // North East
  ];

  // Memoize marker data to prevent expensive recalculations
  const markers = useMemo(() => {
    return data.map((area) => {
      const score30d = area.crime_index_30d || area.crime_index || 0;
      const scoreCum = area.crime_index_cumulative || 0;
      const intensity = getIntensityLevel(score30d);
      
      // Radius scaling (min 12, max 45)
      const radius = Math.max(12, Math.min(45, score30d / 1.8 + 8));

      return {
        ...area,
        score30d,
        scoreCum,
        intensity,
        radius
      };
    });
  }, [data]);

  return (
    <MapContainer 
      center={defaultCenter} 
      zoom={13} 
      minZoom={12}
      maxZoom={16}
      maxBounds={dhakaBounds}
      zoomControl={false}
      preferCanvas={true}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
        updateWhenIdle={true}
        updateWhenZooming={false}
        keepBuffer={2}
      />
      
      {data && data.length > 0 && <MapBounds data={data} />}

      {markers.map((area, index) => (
        <CircleMarker
          key={`${area.area}-${index}`}
          center={[area.lat, area.lng]}
          radius={area.radius}
          pathOptions={{
            fillColor: area.intensity.color,
            color: area.intensity.color,
            weight: 2,
            opacity: 0.9,
            fillOpacity: 0.35,
          }}
        >
          <Popup className="dark-popup">
            <div style={{ padding: '8px', minWidth: '220px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ 
                  fontSize: '0.65rem', 
                  textTransform: 'uppercase', 
                  fontWeight: '800', 
                  padding: '2px 8px', 
                  borderRadius: '100px', 
                  background: 'rgba(255,255,255,0.1)',
                  color: area.intensity.color
                }}>
                  {area.intensity.label} Risk
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {area.thana || 'Dhaka'}
                </span>
              </div>

              <h3 style={{ margin: '0 0 16px 0', fontSize: '1.4rem', color: 'var(--text-primary)' }}>
                {area.area}
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Recent (30d):</span>
                  <strong className={area.intensity.class} style={{ fontSize: '1.1rem' }}>
                    {area.score30d.toFixed(1)}
                  </strong>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Cumulative:</span>
                  <strong style={{ color: '#818cf8', fontSize: '1.1rem' }}>
                    {area.scoreCum.toFixed(1)}
                  </strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginTop: '4px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Total Events:</span>
                  <span style={{ color: 'var(--text-primary)' }}>{area.event_count_cumulative}</span>
                </div>
              </div>

              <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--glass-border)', fontSize: '0.7rem', color: 'var(--text-muted)', textAlign: 'right' }}>
                Synced: {new Date(area.last_updated || Date.now()).toLocaleTimeString()}
              </div>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
});
