import os
import subprocess
import sys
import importlib.util

def setup_environment():
    """Setup the project environment"""
    print("Setting up project environment...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        subprocess.run(["python3", "-m", "venv", "venv"])
        print("Virtual environment created.")
    
    # Determine the activate script based on OS
    if sys.platform == "win32":
        activate_script = os.path.join("venv", "Scripts", "activate")
    else:
        activate_script = os.path.join("venv", "bin", "activate")
    
    print(f"To activate the virtual environment, run: source {activate_script}")
    
    # Check if requirements.txt exists and install dependencies
    if os.path.exists("requirements.txt"):
        if sys.platform == "win32":
            subprocess.run([os.path.join("venv", "Scripts", "pip"), "install", "-r", "requirements.txt"])
        else:
            subprocess.run([os.path.join("venv", "bin", "pip"), "install", "-r", "requirements.txt"])
        print("Dependencies installed.")
    else:
        print("requirements.txt not found. Please create it and run this script again.")
        return False
    
    return True

def import_module_from_file(module_name, file_path):
    """Import a module from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def setup_database():
    """Setup the database"""
    print("Setting up database...")
    
    # Import setup_db module from file path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    setup_db_path = os.path.join(current_dir, "setup_db.py")
    setup_db_module = import_module_from_file("setup_db", setup_db_path)
    
    # Run database setup
    if not setup_db_module.main():
        print("Failed to set up database.")
        return False
    
    try:
        # Import create_tables functions from file path
        create_tables_path = os.path.join(current_dir, "create_tables.py")
        create_tables_module = import_module_from_file("create_tables", create_tables_path)
        
        # Call the functions from the module
        create_tables_module.create_tables()
        create_tables_module.create_triggers()
        create_tables_module.create_stored_procedures()
        create_tables_module.create_functions()
        create_tables_module.create_views()
        create_tables_module.create_indexes()
        create_tables_module.seed_initial_data()
        
        print("Database setup complete!")
        return True
    except Exception as e:
        print(f"Error during database setup: {e}")
        return False

def main():
    """Main initialization function"""
    print("Initializing Slate project...")
    
    if setup_environment():
        setup_database()
        print("Slate project initialized successfully!")
        print("\nTo start the API server, run:")
        print("1. Activate the virtual environment")
        print("2. Run: uvicorn app.main:app --reload")
    else:
        print("Failed to initialize project.")

if __name__ == "__main__":
    main()