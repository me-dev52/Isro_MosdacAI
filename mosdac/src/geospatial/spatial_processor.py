"""
Geospatial Intelligence Module for MOSDAC AI Help Bot
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path

import folium
import geopandas as gpd
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
import pyproj
from pyproj import CRS, Transformer

from config.config import get_geospatial_config
from src.utils.logger import get_logger

@dataclass
class SpatialQuery:
    """Spatial query representation"""
    query_type: str  # 'point', 'polygon', 'buffer', 'intersection'
    geometry: Union[Point, Polygon]
    crs: str
    parameters: Dict[str, Any]

@dataclass
class SpatialResult:
    """Spatial query result"""
    query: SpatialQuery
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    visualization: Optional[str] = None

class SpatialProcessor:
    """Handles geospatial queries and processing"""
    
    def __init__(self):
        self.config = get_geospatial_config()
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize coordinate reference systems
        self.crs_dict = {}
        for crs_code in self.config.supported_crs:
            try:
                self.crs_dict[crs_code] = CRS(crs_code)
            except Exception as e:
                self.logger.warning(f"Failed to initialize CRS {crs_code}: {e}")
                
        # Default CRS
        self.default_crs = CRS(self.config.default_crs)
        
        # Common location coordinates (example data)
        self.location_database = self._init_location_database()
        
    def _init_location_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize database of common locations"""
        return {
            'mumbai': {
                'name': 'Mumbai',
                'coordinates': [72.8777, 19.0760],
                'bbox': [72.7749, 18.8876, 72.9944, 19.1808],
                'state': 'Maharashtra',
                'country': 'India'
            },
            'delhi': {
                'name': 'Delhi',
                'coordinates': [77.2090, 28.7041],
                'bbox': [76.8389, 28.4189, 77.3487, 28.8835],
                'state': 'Delhi',
                'country': 'India'
            },
            'bangalore': {
                'name': 'Bangalore',
                'coordinates': [77.5946, 12.9716],
                'bbox': [77.4661, 12.8342, 77.6413, 13.0841],
                'state': 'Karnataka',
                'country': 'India'
            },
            'chennai': {
                'name': 'Chennai',
                'coordinates': [80.2707, 13.0827],
                'bbox': [80.0889, 12.9198, 80.2707, 13.2334],
                'state': 'Tamil Nadu',
                'country': 'India'
            },
            'kolkata': {
                'name': 'Kolkata',
                'coordinates': [88.3639, 22.5726],
                'bbox': [88.2234, 22.4396, 88.4504, 22.6343],
                'state': 'West Bengal',
                'country': 'India'
            }
        }
        
    def process_spatial_query(self, query_text: str) -> SpatialResult:
        """
        Process a spatial query from natural language
        
        Args:
            query_text: Natural language spatial query
            
        Returns:
            SpatialResult object
        """
        try:
            # Parse the spatial query
            spatial_query = self._parse_spatial_query(query_text)
            
            if not spatial_query:
                return SpatialResult(
                    query=SpatialQuery('unknown', Point(0, 0), self.config.default_crs, {}),
                    results=[],
                    metadata={'error': 'Could not parse spatial query'}
                )
                
            # Execute the spatial query
            results = self._execute_spatial_query(spatial_query)
            
            # Generate visualization
            visualization = self._generate_visualization(spatial_query, results)
            
            return SpatialResult(
                query=spatial_query,
                results=results,
                metadata={'query_type': spatial_query.query_type, 'crs': spatial_query.crs},
                visualization=visualization
            )
            
        except Exception as e:
            self.logger.error(f"Error processing spatial query: {e}")
            return SpatialResult(
                query=SpatialQuery('error', Point(0, 0), self.config.default_crs, {}),
                results=[],
                metadata={'error': str(e)}
            )
            
    def _parse_spatial_query(self, query_text: str) -> Optional[SpatialQuery]:
        """
        Parse natural language into spatial query
        
        Args:
            query_text: Natural language query
            
        Returns:
            SpatialQuery object or None
        """
        query_lower = query_lower = query_text.lower()
        
        # Check for location-based queries
        location_match = self._extract_location(query_lower)
        if location_match:
            return self._create_location_query(location_match)
            
        # Check for coordinate-based queries
        coord_match = self._extract_coordinates(query_lower)
        if coord_match:
            return self._create_coordinate_query(coord_match)
            
        # Check for area/region queries
        area_match = self._extract_area_query(query_lower)
        if area_match:
            return self._create_area_query(area_match)
            
        # Check for buffer queries
        buffer_match = self._extract_buffer_query(query_lower)
        if buffer_match:
            return self._create_buffer_query(buffer_match)
            
        return None
        
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location name from query"""
        for location in self.location_database.keys():
            if location in query:
                return location
        return None
        
    def _extract_coordinates(self, query: str) -> Optional[Tuple[float, float]]:
        """Extract coordinates from query"""
        # Pattern for lat, lon coordinates
        coord_pattern = r'(\d+\.?\d*)[°\s]*([NS]?)[,\s]+(\d+\.?\d*)[°\s]*([EW]?)'
        match = re.search(coord_pattern, query)
        
        if match:
            lat = float(match.group(1))
            lat_dir = match.group(2)
            lon = float(match.group(3))
            lon_dir = match.group(4)
            
            # Apply direction
            if lat_dir == 'S':
                lat = -lat
            if lon_dir == 'W':
                lon = -lon
                
            return (lat, lon)
            
        return None
        
    def _extract_area_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract area/region query parameters"""
        area_keywords = ['area', 'region', 'zone', 'boundary', 'extent']
        
        if any(keyword in query for keyword in area_keywords):
            # Look for specific area names
            for location in self.location_database.keys():
                if location in query:
                    return {
                        'type': 'area',
                        'location': location,
                        'data': self.location_database[location]
                    }
                    
        return None
        
    def _extract_buffer_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract buffer query parameters"""
        buffer_pattern = r'(\d+)\s*(km|kilometers?|m|meters?)\s*(?:around|near|within|from)'
        match = re.search(buffer_pattern, query)
        
        if match:
            distance = float(match.group(1))
            unit = match.group(2)
            
            # Convert to meters
            if unit in ['km', 'kilometers', 'kilometer']:
                distance *= 1000
                
            # Extract center point
            location_match = self._extract_location(query)
            if location_match:
                return {
                    'type': 'buffer',
                    'distance': distance,
                    'location': location_match,
                    'data': self.location_database[location_match]
                }
                
        return None
        
    def _create_location_query(self, location: str) -> SpatialQuery:
        """Create spatial query for a location"""
        location_data = self.location_database[location]
        point = Point(location_data['coordinates'])
        
        return SpatialQuery(
            query_type='point',
            geometry=point,
            crs=self.config.default_crs,
            parameters={'location': location, 'data': location_data}
        )
        
    def _create_coordinate_query(self, coords: Tuple[float, float]) -> SpatialQuery:
        """Create spatial query for coordinates"""
        point = Point(coords[1], coords[0])  # lon, lat
        
        return SpatialQuery(
            query_type='point',
            geometry=point,
            crs=self.config.default_crs,
            parameters={'coordinates': coords}
        )
        
    def _create_area_query(self, area_data: Dict[str, Any]) -> SpatialQuery:
        """Create spatial query for an area"""
        bbox = area_data['data']['bbox']
        polygon = box(bbox[0], bbox[1], bbox[2], bbox[3])
        
        return SpatialQuery(
            query_type='polygon',
            geometry=polygon,
            crs=self.config.default_crs,
            parameters=area_data
        )
        
    def _create_buffer_query(self, buffer_data: Dict[str, Any]) -> SpatialQuery:
        """Create spatial query for a buffer"""
        center_point = Point(buffer_data['data']['coordinates'])
        buffer_geom = center_point.buffer(buffer_data['distance'] / 111000)  # Approximate conversion
        
        return SpatialQuery(
            query_type='buffer',
            geometry=buffer_geom,
            crs=self.config.default_crs,
            parameters=buffer_data
        )
        
    def _execute_spatial_query(self, spatial_query: SpatialQuery) -> List[Dict[str, Any]]:
        """
        Execute a spatial query
        
        Args:
            spatial_query: SpatialQuery object
            
        Returns:
            List of results
        """
        results = []
        
        if spatial_query.query_type == 'point':
            results = self._query_point(spatial_query)
        elif spatial_query.query_type == 'polygon':
            results = self._query_polygon(spatial_query)
        elif spatial_query.query_type == 'buffer':
            results = self._query_buffer(spatial_query)
            
        return results
        
    def _query_point(self, spatial_query: SpatialQuery) -> List[Dict[str, Any]]:
        """Query for data at a specific point"""
        point = spatial_query.geometry
        results = []
        
        # Find locations within proximity
        for location_name, location_data in self.location_database.items():
            loc_point = Point(location_data['coordinates'])
            distance = point.distance(loc_point)
            
            if distance < 0.1:  # Within ~11km
                results.append({
                    'type': 'nearby_location',
                    'name': location_data['name'],
                    'distance_km': round(distance * 111, 2),
                    'coordinates': location_data['coordinates'],
                    'metadata': location_data
                })
                
        # Add satellite data availability info
        results.append({
            'type': 'satellite_data',
            'availability': 'Available',
            'coverage': 'Full coverage',
            'sensors': ['MODIS', 'VIIRS', 'Landsat'],
            'temporal_resolution': 'Daily',
            'spatial_resolution': '250m - 30m'
        })
        
        return results
        
    def _query_polygon(self, spatial_query: SpatialQuery) -> List[Dict[str, Any]]:
        """Query for data within a polygon area"""
        polygon = spatial_query.geometry
        results = []
        
        # Find locations within the area
        for location_name, location_data in self.location_database.items():
            loc_point = Point(location_data['coordinates'])
            if polygon.contains(loc_point):
                results.append({
                    'type': 'contained_location',
                    'name': location_data['name'],
                    'coordinates': location_data['coordinates'],
                    'metadata': location_data
                })
                
        # Add area statistics
        area_km2 = polygon.area * 111 * 111  # Approximate conversion
        results.append({
            'type': 'area_statistics',
            'area_km2': round(area_km2, 2),
            'perimeter_km': round(polygon.length * 111, 2),
            'satellite_coverage': 'Complete coverage',
            'data_products': ['Land cover', 'Vegetation indices', 'Surface temperature']
        })
        
        return results
        
    def _query_buffer(self, spatial_query: SpatialQuery) -> List[Dict[str, Any]]:
        """Query for data within a buffer area"""
        buffer_geom = spatial_query.geometry
        buffer_distance = spatial_query.parameters['distance']
        results = []
        
        # Find locations within buffer
        for location_name, location_data in self.location_database.items():
            loc_point = Point(location_data['coordinates'])
            if buffer_geom.contains(loc_point):
                results.append({
                    'type': 'buffer_location',
                    'name': location_data['name'],
                    'coordinates': location_data['coordinates'],
                    'distance_from_center_km': round(
                        loc_point.distance(Point(spatial_query.parameters['data']['coordinates'])) * 111, 2
                    ),
                    'metadata': location_data
                })
                
        # Add buffer information
        results.append({
            'type': 'buffer_info',
            'radius_km': round(buffer_distance / 1000, 2) if buffer_distance >= 1000 else round(buffer_distance, 2),
            'area_km2': round(buffer_geom.area * 111 * 111, 2),
            'satellite_data': 'Available within buffer',
            'coverage_type': 'Circular coverage'
        })
        
        return results
        
    def _generate_visualization(self, spatial_query: SpatialQuery, results: List[Dict[str, Any]]) -> str:
        """
        Generate map visualization for spatial query
        
        Args:
            spatial_query: SpatialQuery object
            results: Query results
            
        Returns:
            HTML string for map visualization
        """
        try:
            # Create base map
            if spatial_query.query_type == 'point':
                center = [spatial_query.geometry.y, spatial_query.geometry.x]
            else:
                center = spatial_query.geometry.centroid
                center = [center.y, center.x]
                
            m = folium.Map(location=center, zoom_start=10)
            
            # Add query geometry
            if spatial_query.query_type == 'point':
                folium.Marker(
                    center,
                    popup=f"Query Point<br>Type: {spatial_query.query_type}",
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
                
            elif spatial_query.query_type in ['polygon', 'buffer']:
                # Convert geometry to GeoJSON
                geojson_data = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [list(spatial_query.geometry.exterior.coords)]
                    },
                    'properties': {
                        'query_type': spatial_query.query_type,
                        'crs': spatial_query.crs
                    }
                }
                
                folium.GeoJson(
                    geojson_data,
                    style_function=lambda x: {
                        'fillColor': 'red',
                        'color': 'red',
                        'weight': 2,
                        'fillOpacity': 0.3
                    },
                    popup=folium.Popup(f"Query Area<br>Type: {spatial_query.query_type}")
                ).add_to(m)
                
            # Add result locations
            for result in results:
                if 'coordinates' in result:
                    coords = result['coordinates']
                    name = result.get('name', 'Unknown')
                    result_type = result.get('type', 'Unknown')
                    
                    folium.Marker(
                        [coords[1], coords[0]],  # lat, lon
                        popup=f"{name}<br>Type: {result_type}",
                        icon=folium.Icon(color='blue', icon='info-sign')
                    ).add_to(m)
                    
            # Convert to HTML
            return m._repr_html_()
            
        except Exception as e:
            self.logger.error(f"Error generating visualization: {e}")
            return f"<p>Error generating map: {str(e)}</p>"
            
    def get_spatial_suggestions(self, query: str) -> List[str]:
        """
        Get spatial query suggestions
        
        Args:
            query: User query
            
        Returns:
            List of suggested spatial queries
        """
        suggestions = [
            "Show satellite data for Mumbai region",
            "What data is available around Delhi?",
            "Show coverage within 50km of Bangalore",
            "What satellite imagery covers Chennai area?",
            "Show data availability for coordinates 77.2090, 28.7041",
            "What's the coverage area for Kolkata region?"
        ]
        
        # Filter suggestions based on query content
        query_lower = query.lower()
        relevant_suggestions = []
        
        for suggestion in suggestions:
            if any(word in query_lower for word in suggestion.lower().split()):
                relevant_suggestions.append(suggestion)
                
        # Add general suggestions if not enough specific ones
        while len(relevant_suggestions) < 3:
            for suggestion in suggestions:
                if suggestion not in relevant_suggestions:
                    relevant_suggestions.append(suggestion)
                    break
                    
        return relevant_suggestions[:3]
        
    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """
        Validate coordinate values
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if valid, False otherwise
        """
        return -90 <= lat <= 90 and -180 <= lon <= 180
        
    def convert_crs(self, geometry, from_crs: str, to_crs: str):
        """
        Convert geometry between coordinate reference systems
        
        Args:
            geometry: Shapely geometry
            from_crs: Source CRS
            to_crs: Target CRS
            
        Returns:
            Converted geometry
        """
        try:
            transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
            if hasattr(geometry, 'coords'):
                # Point
                x, y = transformer.transform(geometry.x, geometry.y)
                return Point(x, y)
            elif hasattr(geometry, 'exterior'):
                # Polygon
                coords = list(geometry.exterior.coords)
                transformed_coords = [transformer.transform(x, y) for x, y in coords]
                return Polygon(transformed_coords)
            else:
                return geometry
        except Exception as e:
            self.logger.error(f"Error converting CRS: {e}")
            return geometry
