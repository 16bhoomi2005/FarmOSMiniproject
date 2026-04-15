import os

pages_dir = r"c:\CropSatelliteSensorMain\project\pages"
files = os.listdir(pages_dir)

mapping = {
    "1_🛰️_Satellite_Intelligence.py": "1_Field_Health_Map.py",
    "2_🌡️_Sensor_Insights.py": "2_Sensor_Monitoring.py",
    "3_🧠_Farming_AI.py": "3_AI_Risk_Prediction.py",
    "3_🧠_AI_Risk_Prediction.py": "3_AI_Risk_Prediction.py",
    "4_🚨_Alerts_&_Recommendations.py": "4_Alerts_Recommendations.py"
}

to_delete = [
    "4_📊_Business_&_ROI.py",
    "5_📖_Knowledge_Base.py",
    "6_🔮_Future_Projections.py"
]

for old_name, new_name in mapping.items():
    old_path = os.path.join(pages_dir, old_name)
    new_path = os.path.join(pages_dir, new_name)
    if os.path.exists(old_path):
        print(f"Renaming {old_name} to {new_name}")
        if os.path.exists(new_path) and old_path != new_path:
            os.remove(new_path)
        os.rename(old_path, new_path)

for name in to_delete:
    path = os.path.join(pages_dir, name)
    if os.path.exists(path):
        print(f"Deleting {name}")
        os.remove(path)

print("Done.")
