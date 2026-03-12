---
name: PostGIS Analytics
description: Expert-level spatial analysis for crime hotspots using DBSCAN and optimized PostGIS queries.
---

# PostGIS Analytics Skill

Advanced methodologies for spatial data analysis in the Dhaka Crime Index project.

## 🗺️ Spatial Clustering (Hotspots)
When identifying recurring crime clusters, use **DBSCAN** (Density-Based Spatial Clustering of Applications with Noise) instead of simple area aggregation.
- **Goal**: Identify geographic "density" rather than administrative boundaries.
- **Implementation**:
  ```sql
  SELECT ST_ClusterDBSCAN(geom, eps := 0.002, minpoints := 3) OVER () AS cluster_id
  FROM incidents;
  ```
- **eps (Epsilon)**: Use `0.002` (approx 200m) for dense urban areas like Dhaka.

## ⚡ Query Optimization
- Use **GIST Indexes** for all geometry columns.
- Prefer `ST_DWithin` over `ST_Distance` for distance-based queries (it uses spatial indexes).
- Always use `ST_Transform(geom, 4326)` for WGS84 compatibility with Leaflet.

## 🛠️ Geometry Handling
- **Normalization**: Ensure all coordinates are strictly within Dhaka Bounds: `SRID=4326; POLYGON((90.28 23.65, 90.53 23.65, 90.53 23.95, 90.28 23.95, 90.28 23.65))`.
- **Simplification**: Use `ST_Simplify` for large polygons before sending to the frontend to reduce JSON payload size.
