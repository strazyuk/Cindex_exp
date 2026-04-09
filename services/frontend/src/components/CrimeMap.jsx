import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import React, { useEffect, useMemo, memo } from 'react';
import { HeatmapController } from './HeatmapController';

// Fix Leaflet icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Minimal color mapping
// Improved color mapping for more "frequent" visual feedback
const getIntensityLevel = (score) => {
  if (score >= 75) return { label: 'Sector Red', color: 'hsl(0, 100%, 60%)' };
  if (score >= 55) return { label: 'Sector Orange', color: 'hsl(25, 100%, 55%)' };
  if (score >= 35) return { label: 'Sector Amber', color: 'hsl(45, 100%, 55%)' };
  if (score >= 15) return { label: 'Sector Yellow', color: 'hsl(81, 100%, 50%)' };
  return { label: 'Sector Green', color: 'hsl(142, 100%, 45%)' };
};

const MapBounds = memo(({ data }) => {
  const map = useMap();
  useEffect(() => {
    if (data && data.length > 0) {
      // Bounds handled by maxBounds
    }
  }, [data, map]);
  return null;
});

const CrimeMarkers = memo(({ data }) => {
  const markers = useMemo(() => {
    return data.map((area) => {
      // Align with reworked historical weighting
      const score30d = area.crime_index_30d || 0;
      const scoreCum = area.crime_index_cumulative || area.crime_index || 0;
      
      // Use Cumulative score for the primary visual intensity
      const intensity = getIntensityLevel(scoreCum);
      const radius = Math.max(12, Math.min(45, scoreCum / 1.8 + 8));

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
    <>
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
            <div className="p-4 min-w-[240px] space-y-4">
              <div className="flex justify-between items-center">
                <span 
                  className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full border border-current"
                  style={{ color: area.intensity.color }}
                >
                  {area.intensity.label}
                </span>
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-tight">
                  {area.thana || 'Central'}
                </span>
              </div>

              <div className="space-y-1">
                <h3 className="text-lg font-bold leading-tight text-foreground">
                  {area.area}
                </h3>
                <p className="text-[10px] text-muted-foreground uppercase font-medium tracking-wide">Area Coordinates: {area.lat.toFixed(3)}, {area.lng.toFixed(3)}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-3 py-3 border-y border-border">
                <div className="space-y-0.5">
                  <span className="text-[9px] font-bold text-muted-foreground uppercase">30d Score</span>
                  <p className="text-sm font-bold text-foreground">{area.score30d.toFixed(1)}</p>
                </div>
                <div className="space-y-0.5 text-right">
                  <span className="text-[9px] font-bold text-muted-foreground uppercase">Cumulative</span>
                  <p className="text-sm font-bold text-foreground">{area.scoreCum.toFixed(1)}</p>
                </div>
              </div>

              <div className="flex justify-between text-[10px] font-bold">
                <span className="text-muted-foreground uppercase">Detection Count:</span>
                <span className="text-foreground">{area.event_count_cumulative}</span>
              </div>

              {area.last_updated && (
                <div className="text-[9px] text-muted-foreground font-mono text-right pt-2">
                  ID: {area.id?.substring(0, 8) || 'N/A'} | {new Date(area.last_updated).toLocaleTimeString()}
                </div>
              )}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </>
  );
});

const CrimeMapComponent = memo(({ data }) => {
  const defaultCenter = [23.777, 90.399];
  const dhakaBounds = [
    [23.65, 90.28],
    [23.95, 90.53]
  ];

  return (
    <MapContainer 
      center={defaultCenter} 
      zoom={13} 
      minZoom={12}
      maxZoom={16}
      maxBounds={dhakaBounds}
      zoomControl={false}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
        updateWhenIdle={true}
      />
      
      {data && data.length > 0 && (
        <>
          <MapBounds data={data} />
          <CrimeMarkers data={data} />
        </>
      )}
    </MapContainer>
  );
});

export default CrimeMapComponent;
