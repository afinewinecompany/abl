import os
import shutil
import subprocess
import sys

def main():
    """
    This script installs the FantraxAPI module from the local clone
    and makes it available to the main application.
    """
    print("Installing FantraxAPI module...")
    
    # Check if FantraxAPI directory exists
    if not os.path.exists('FantraxAPI'):
        print("ERROR: FantraxAPI directory not found.")
        print("Please ensure the FantraxAPI repository is cloned into the project root.")
        return False
    
    try:
        # Run pip install in development mode
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', './FantraxAPI'])
        print("✅ Successfully installed FantraxAPI module.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install FantraxAPI module. Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("Installation failed. Please check the error messages above.")
    else:
        print("You can now use the FantraxAPI in your application.")