---
name: High-Performance Geovis
description: Advanced React and Leaflet patterns for 60fps geospatial visualizations with many markers.
---

# High-Performance Geovis Skill

Patterns for keeping the Dhaka Crime Index map fluid and visually stunned.

## 🚀 Rendering Engine (WebGL/Canvas)
- **Rule**: If markers > 100, always use `preferCanvas: true` on the `MapContainer`.
- **Canvas Path Options**: Leaflet's `CircleMarker` on Canvas ignores CSS variables; use explicit `hsl()` or hex strings.

## 🧠 Memoization Strategy
- **React.memo**: Wrap `CrimeMap` and `IndexPanel` to prevent re-renders when parent states (like sidebar toggles) change.
- **useMemo**: Pre-calculate marker `radius` and `color` tokens once when data arrives, not inside the render loop.
- **useCallback**: Memoize the `popover` or `click` handlers to prevent child component churn.

## ✨ Visual Excellence
- **Hardware Acceleration**: Apply `will-change: transform` to any overlay panels (like the Risk Panel) that float above the map.
- **GPU Layers**: Use `transform: translate3d(0,0,0)` to force the sidebar into its own compositing layer, preventing repaint lag during map pans.
- **Glassmorphism**: When using `backdrop-filter: blur()`, always pair with `transform: translateZ(0)` to minimize the performance impact.
