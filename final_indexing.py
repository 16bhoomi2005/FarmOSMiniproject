import os

pages_dir = 'pages'
# THE FINAL 4 PAGES (in addition to Home/Today)
final_indexing = {
    '1_🗺️_My_Fields.py': '1_🗺️_My_Fields.py',
    '2_💧_Ground_Condition.py': '2_💧_Ground_Condition.py',
    '2_🚨_Alerts.py': '3_🚨_Alerts.py',
    '3_📚_Help.py': '4_📚_Help.py'
}

# Current files in pages/
current_files = os.listdir(pages_dir)

# 1. Rename/Move the ones we want to keep/shift
for old_name, new_name in final_indexing.items():
    if old_name in current_files:
        old_path = os.path.join(pages_dir, old_name)
        new_path = os.path.join(pages_dir, new_name)
        if old_path != new_path:
            print(f"Renaming {old_name} -> {new_name}")
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                print(f"Could not rename {old_name}: {e}")

# 2. Delete everything else to clean the sidebar for the exhibition
keep_list = list(final_indexing.values())
for filename in os.listdir(pages_dir):
    if filename.endswith('.py') and filename not in keep_list:
        file_path = os.path.join(pages_dir, filename)
        print(f"Removing technical clutter: {filename}")
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Could not remove {filename}: {e}")
