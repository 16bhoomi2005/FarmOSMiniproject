import os

pages_dir = 'pages'
# THE NEW ESSENTIALS - DO NOT DELETE
essentials = [
    '1_🗺️_My_Fields.py',
    '2_🚨_Alerts.py',
    '3_📚_Help.py'
]

for filename in os.listdir(pages_dir):
    if filename.endswith('.py') and filename not in essentials:
        file_path = os.path.join(pages_dir, filename)
        print(f"Deleting technical clutter: {filename}")
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete {filename}: {e}")
