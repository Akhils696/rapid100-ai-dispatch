"""
Setup script for RAPID-100 Emergency Call Triage System
This script helps set up the environment and install dependencies
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def create_directories():
    """Create required directories"""
    directories = [
        "logs",
        "data",
        "backend/api",
        "backend/models", 
        "backend/services",
        "backend/utils",
        "backend/tests",
        "frontend/src/components",
        "frontend/public"
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def create_env_file():
    """Create .env file with default settings"""
    env_content = """# RAPID-100 Configuration
DEBUG=True
LOG_LEVEL=INFO
WHISPER_MODEL_SIZE=tiny
MAX_AUDIO_DURATION=300  # 5 minutes max
ENABLE_MOCK_SERVICES=True  # Set to False when deploying with real models
DATABASE_URL=sqlite:///./rapid100.db
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("Created .env file with default configuration")

def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/*.log
*.log

# Data
data/*.wav
data/*.mp3
data/__pycache__/

# Frontend
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Database
*.db
*.db-journal

# Model cache
.cache/
.huggingface/
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("Created .gitignore file")

def install_python_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Python dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Python dependencies: {e}")
        return False
    return True

def install_node_dependencies():
    """Install Node.js dependencies"""
    print("Installing Node.js dependencies...")
    try:
        os.chdir("frontend")
        subprocess.check_call(["npm", "install"])
        os.chdir("..")
        print("Node.js dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Node.js dependencies: {e}")
        return False
    return True

def download_sample_data():
    """Download or create sample data"""
    print("Setting up sample data...")
    # We already created the sample data file, so just verify it exists
    sample_file = Path("data/sample_calls.csv")
    if sample_file.exists():
        print("Sample data already exists")
    else:
        print("Creating sample data...")
        # We already created this, so this is just a verification step

def main():
    print("Setting up RAPID-100 Emergency Call Triage System...")
    print(f"Platform: {platform.system()} {platform.release()}")
    
    # Create required directories
    create_directories()
    
    # Create configuration files
    create_env_file()
    create_gitignore()
    
    # Install dependencies
    python_success = install_python_dependencies()
    node_success = install_node_dependencies()
    
    # Set up sample data
    download_sample_data()
    
    print("\nSetup completed!")
    print("\nTo start the application:")
    print("1. Start backend: cd backend && uvicorn main:app --reload")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Access the dashboard at http://localhost:3000")
    
    if not python_success:
        print("\n⚠️  Warning: Python dependencies were not installed successfully")
    if not node_success:
        print("\n⚠️  Warning: Node.js dependencies were not installed successfully")
    
    print("\nFor model evaluation, run: python backend/evaluate_models.py")

if __name__ == "__main__":
    main()