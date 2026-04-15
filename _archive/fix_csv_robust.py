import random

file_path = r'c:\CropSatelliteSensorMain\project\sample_ground_sensor_data.csv'
fields = ['North', 'South', 'East', 'West', 'Northwest', 'Northeast', 'Southwest', 'Southeast', 'Center']

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
# Header
header = lines[0].strip()
if not header.endswith(',Field'):
    header += ',Field'
new_lines.append(header + '\n')

# Data lines
for line in lines[1:]:
    clean_line = line.strip()
    if not clean_line:
        continue
    
    parts = clean_line.split(',')
    # If line already has 10 parts, it might have a field
    if len(parts) >= 10:
        new_lines.append(clean_line + '\n')
    else:
        # Append a random field
        new_lines.append(clean_line + ',' + random.choice(fields) + '\n')

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print(f"✅ Successfully reconstructed {file_path} with {len(new_lines)} lines.")
