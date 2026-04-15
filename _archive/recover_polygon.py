#!/usr/bin/env python3
"""
Bhandara District Polygon Recovery Tool
Extracts coordinates from existing Sentinel-2 data and helps recreate polygon
"""

import os
import xml.etree.ElementTree as ET
import json

def extract_tile_coordinates(safe_dir):
    """Extract geographic coordinates from Sentinel-2 .SAFE metadata"""
    
    # Find MTD_MSIL2A.xml (main metadata file)
    mtd_file = os.path.join(safe_dir, 'MTD_MSIL2A.xml')
    
    if not os.path.exists(mtd_file):
        print(f"❌ Metadata file not found: {mtd_file}")
        return None
    
    try:
        tree = ET.parse(mtd_file)
        root = tree.getroot()
        
        # Extract tile ID and coordinates
        tile_info = {}
        
        # Get tile geocoding info
        for geocoding in root.iter('Tile_Geocoding'):
            for geoposition in geocoding.iter('Geoposition'):
                ulx = geoposition.find('ULX')
                uly = geoposition.find('ULY')
                if ulx is not None and uly is not None:
                    tile_info['ULX'] = float(ulx.text)
                    tile_info['ULY'] = float(uly.text)
        
        # Get geographic extent
        for ext_pos in root.iter('EXT_POS_LIST'):
            coords_text = ext_pos.text.strip()
            coords = coords_text.split()
            
            # Parse coordinate pairs (lat lon lat lon ...)
            lats = [float(coords[i]) for i in range(0, len(coords), 2)]
            lons = [float(coords[i]) for i in range(1, len(coords), 2)]
            
            tile_info['extent'] = {
                'lats': lats,
                'lons': lons,
                'center_lat': sum(lats) / len(lats),
                'center_lon': sum(lons) / len(lons),
                'min_lat': min(lats),
                'max_lat': max(lats),
                'min_lon': min(lons),
                'max_lon': max(lons)
            }
        
        return tile_info
        
    except Exception as e:
        print(f"❌ Error parsing metadata: {e}")
        return None

def get_bhandara_polygon():
    """Return standard Bhandara district polygon coordinates"""
    
    # Bhandara district approximate boundaries
    # You can adjust these based on your specific farm location
    bhandara_center = {
        'lat': 21.1704,
        'lon': 79.6519
    }
    
    # Create a polygon around Bhandara district
    # Adjust the size based on your farm area
    offset = 0.05  # ~5km radius
    
    polygon = {
        'type': 'Polygon',
        'coordinates': [[
            [bhandara_center['lon'] - offset, bhandara_center['lat'] + offset],  # NW
            [bhandara_center['lon'] + offset, bhandara_center['lat'] + offset],  # NE
            [bhandara_center['lon'] + offset, bhandara_center['lat'] - offset],  # SE
            [bhandara_center['lon'] - offset, bhandara_center['lat'] - offset],  # SW
            [bhandara_center['lon'] - offset, bhandara_center['lat'] + offset]   # Close polygon
        ]]
    }
    
    return polygon, bhandara_center

def analyze_all_safe_files(sentinel_data_dir):
    """Analyze all .SAFE files to find coverage area"""
    
    print("🔍 Analyzing Sentinel-2 data files...\n")
    
    safe_dirs = [d for d in os.listdir(sentinel_data_dir) 
                 if d.endswith('.SAFE') and os.path.isdir(os.path.join(sentinel_data_dir, d))]
    
    all_coords = []
    
    for safe_dir in safe_dirs:
        full_path = os.path.join(sentinel_data_dir, safe_dir)
        print(f"📂 {safe_dir}")
        
        coords = extract_tile_coordinates(full_path)
        if coords and 'extent' in coords:
            extent = coords['extent']
            print(f"   Center: {extent['center_lat']:.4f}, {extent['center_lon']:.4f}")
            print(f"   Bounds: Lat [{extent['min_lat']:.4f}, {extent['max_lat']:.4f}]")
            print(f"           Lon [{extent['min_lon']:.4f}, {extent['max_lon']:.4f}]")
            all_coords.append(extent)
        print()
    
    if all_coords:
        # Calculate overall coverage area
        all_lats = []
        all_lons = []
        for c in all_coords:
            all_lats.extend([c['min_lat'], c['max_lat']])
            all_lons.extend([c['min_lon'], c['max_lon']])
        
        coverage = {
            'center_lat': sum(all_lats) / len(all_lats),
            'center_lon': sum(all_lons) / len(all_lons),
            'min_lat': min(all_lats),
            'max_lat': max(all_lats),
            'min_lon': min(all_lons),
            'max_lon': max(all_lons)
        }
        
        return coverage
    
    return None

def generate_copernicus_search_url(polygon_coords, center):
    """Generate Copernicus Browser URL with polygon"""
    
    # Format: lat,lon for center
    center_str = f"{center['lat']},{center['lon']}"
    
    # Simplified bounding box for URL
    base_url = "https://browser.dataspace.copernicus.eu/"
    
    print("\n🌐 Copernicus Browser Search:")
    print(f"   URL: {base_url}")
    print(f"   Center coordinates: {center_str}")
    print(f"   Zoom to this location and draw your polygon")
    
    return base_url, center_str

def save_polygon_to_file(polygon, filename='bhandara_polygon.json'):
    """Save polygon to JSON file for future use"""
    with open(filename, 'w') as f:
        json.dump(polygon, f, indent=2)
    print(f"\n💾 Polygon saved to: {filename}")

if __name__ == "__main__":
    print("="*60)
    print("🗺️  BHANDARA DISTRICT POLYGON RECOVERY TOOL")
    print("="*60)
    
    sentinel_data_dir = 'Sentinel_Data'
    
    # Analyze existing Sentinel data
    if os.path.exists(sentinel_data_dir):
        coverage = analyze_all_safe_files(sentinel_data_dir)
        
        if coverage:
            print("\n📊 YOUR DATA COVERAGE AREA:")
            print(f"   Center: {coverage['center_lat']:.4f}°N, {coverage['center_lon']:.4f}°E")
            print(f"   Latitude range: {coverage['min_lat']:.4f}° to {coverage['max_lat']:.4f}°")
            print(f"   Longitude range: {coverage['min_lon']:.4f}° to {coverage['max_lon']:.4f}°")
            
            # Check if this is in Bhandara district
            bhandara_lat = 21.1704
            bhandara_lon = 79.6519
            
            if (abs(coverage['center_lat'] - bhandara_lat) < 1.0 and 
                abs(coverage['center_lon'] - bhandara_lon) < 1.0):
                print("\n✅ This data covers Bhandara district area!")
            else:
                print("\n⚠️  This data may not be Bhandara district")
                print(f"   Expected center: ~{bhandara_lat}°N, {bhandara_lon}°E")
    
    # Get standard Bhandara polygon
    polygon, center = get_bhandara_polygon()
    
    print("\n" + "="*60)
    print("📍 RECOMMENDED POLYGON FOR BHANDARA DISTRICT")
    print("="*60)
    print(f"\nCenter Point: {center['lat']:.4f}°N, {center['lon']:.4f}°E")
    print("\nPolygon Coordinates (copy these):")
    print("-" * 40)
    
    for i, coord in enumerate(polygon['coordinates'][0]):
        print(f"Point {i+1}: {coord[1]:.4f}°N, {coord[0]:.4f}°E")
    
    # Save polygon
    save_polygon_to_file(polygon)
    
    # Generate search URL
    url, center_str = generate_copernicus_search_url(polygon, center)
    
    print("\n" + "="*60)
    print("🚀 NEXT STEPS TO DOWNLOAD RECENT DATA")
    print("="*60)
    print("""
1. Visit: https://browser.dataspace.copernicus.eu/

2. Search for location:
   - Enter coordinates: 21.1704, 79.6519
   - Or search: "Bhandara, Maharashtra, India"

3. Draw polygon:
   - Click the polygon tool (⬡ icon)
   - Click to create corners around your farm area
   - Use the coordinates above as reference

4. Filter data:
   - Date: Last 30 days
   - Satellite: Sentinel-2
   - Product: L2A (atmospherically corrected)
   - Cloud coverage: < 10%

5. Download:
   - Select clearest image
   - Download as .SAFE format
   - Place in Sentinel_Data/ folder

6. Process:
   - Run: python enhanced_hybrid_system.py
   - Dashboard will update with recent data
    """)
    
    print("\n💡 TIP: Your existing data is from tile T44QLH")
    print("   Look for the same tile ID for consistency")
