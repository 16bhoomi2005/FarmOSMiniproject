import os
import shutil

pages_dir = 'pages'
backup_dir = 'backup_pages'

if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

# Essential Decision-First Files
essentials = [
    '1_🗺️_My_Fields.py',
    '2_🚨_Alerts.py',
    '3_📚_Help.py'
]

for filename in os.listdir(pages_dir):
    if filename.endswith('.py') and filename not in essentials:
        src = os.path.join(pages_dir, filename)
        dst = os.path.join(backup_dir, filename)
        print(f"Moving {src} to {dst}")
        try:
            shutil.move(src, dst)
        except Exception as e:
            print(f"Error moving {filename}: {e}")
