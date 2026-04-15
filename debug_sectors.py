"""
Quick diagnostic — run with:  python debug_sectors.py
Shows exactly what NDVI each sector gets and which one wins priority.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Patch out streamlit so data_loader imports cleanly
import types
st_mock = types.ModuleType("streamlit")
st_mock.cache_data = lambda **kw: (lambda f: f)   # no-op decorator
st_mock.session_state = {}
sys.modules["streamlit"] = st_mock

import data_loader as dl

print("\n=== SECTOR ANALYSIS ===")
sectors = dl.get_sector_analysis()
for name, data in sectors.items():
    ndvi = data.get('ndvi')
    label = data.get('label')
    source = data.get('source')
    ndvi_str = f"{ndvi:.4f}" if ndvi is not None else "None"
    print(f"  {name:20s}  NDVI={ndvi_str}  label={label:10s}  source={source}")

print("\n=== PRIORITY ZONE ===")
pz = dl.get_priority_zone()
print(f"  Winner: {pz['name']}  (label={pz['label']}, ndvi={pz['ndvi']})")
print(f"  Reason: {pz['reason']}")
