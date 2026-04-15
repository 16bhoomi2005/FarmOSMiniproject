import re

def fix():
    with open('data_loader.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == "'''FarmOS UI — deep forest green background, amber accent, earthen glass panels.'''" or line.strip() == '\"\"\"FarmOS UI — deep forest green background, amber accent, earthen glass panels.\"\"\"':
            start_idx = i + 2 # keep function sig, docstring, import, styled injection... wait actually line 1558 is exactly the blank line.
            
        if "def get_field_sidebar():" in line:
            end_idx = i
            break
            
    if start_idx == -1 or end_idx == -1:
        print(f"Could not find indices: start={start_idx}, end={end_idx}")
        return
        
    # hardcode indices for safety based on what we saw
    keep_lines = lines[:1558] + ["\n"] + lines[end_idx:]
    with open('data_loader.py', 'w', encoding='utf-8') as f:
        f.writelines(keep_lines)
    print("Fixed data_loader.py")

if __name__ == "__main__":
    fix()
