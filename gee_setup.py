import ee
import webbrowser
import os
import json

GEE_CONFIG_FILE = "gee_config.json"

def _save_project_id(project_id):
    """Persist project ID so satellite_service.py picks it up automatically."""
    try:
        with open(GEE_CONFIG_FILE, "w") as f:
            json.dump({"project_id": project_id}, f)
        print(f"💾 Project ID saved to {GEE_CONFIG_FILE}")
    except Exception as e:
        print(f"⚠️ Could not save project ID: {e}")

def authenticate_gee():
    """
    Handles Google Earth Engine authentication with Project ID support.
    """
    try:
        # Try initializing with default credentials
        try:
            ee.Initialize()
            print("✅ Google Earth Engine is already authenticated and initialized!")
        except ee.EEException as e:
            if "no project found" in str(e).lower():
                print("⚠️ Authentication valid, but no Cloud Project found.")
                print("ℹ️ Google Earth Engine requires a Google Cloud Project.")
                project_id = input("👉 Please enter your Google Cloud Project ID (e.g., 'my-rice-project-123'): ").strip()
                if project_id:
                    print(f"🔄 Attempting to initialize with project: {project_id}...")
                    ee.Initialize(project=project_id)
                    _save_project_id(project_id)  # ← Save so dashboard uses it automatically
                    print("✅ Initialization successful!")
                else:
                    print("❌ No project ID provided. Setup aborted.")
            else:
                raise e

    except (ee.EEException, Exception):
        print("⚠️ Not authenticated. Triggering authentication flow...")
        try:
            # Force high-entropy auth flow
            ee.Authenticate()
            
            print("\n🔄 Re-attempting initialization...")
            try:
                ee.Initialize()
                print("✅ Authentication successful! Google Earth Engine is ready.")
            except ee.EEException as e:
                # If it fails again after auth, it's likely the project ID issue again
                if "no project found" in str(e).lower():
                     print("ℹ️ Almost there! We just need a Project ID.")
                     project_id = input("👉 Please enter your Google Cloud Project ID: ").strip()
                     if project_id:
                        ee.Initialize(project=project_id)
                        _save_project_id(project_id)  # ← Save so dashboard uses it automatically
                        print("✅ Initialization successful!")
                else:
                    print(f"❌ Initialization failed: {e}")

        except Exception as e:
            print(f"❌ Authentication Setup failed: {e}")
            print("\n📋 Manual Fix:")
            print("1. Open your terminal.")
            print("2. Run: earthengine authenticate --auth_mode=notebook")
            print("3. Follow the link and copy the code.")

if __name__ == "__main__":
    print("🌍 Starting Google Earth Engine Setup...")
    print("---------------------------------------")
    authenticate_gee()
