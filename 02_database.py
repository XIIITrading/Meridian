# Create run_database.py in root directory
"""
NocoDB Database Manager for XIII Trading Systems
Starts, stops, and manages the NocoDB Docker container
"""

import subprocess
import time
import webbrowser
import sys
import os
from pathlib import Path

class NocoDB:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.nocodb_dir = self.root_dir / "nocodb"
        self.compose_file = "docker-compose-sqlite.yml"
        self.url = "http://localhost:8080"
        
    def start(self):
        """Start NocoDB container"""
        print("🚀 Starting NocoDB Database...")
        
        # Change to nocodb directory
        os.chdir(self.nocodb_dir)
        
        # Start Docker container
        result = subprocess.run(
            ["docker-compose", "-f", self.compose_file, "up", "-d"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ NocoDB container started successfully")
            print(f"⏳ Waiting for NocoDB to initialize...")
            time.sleep(5)
            
            # Check if container is running
            check = subprocess.run(
                ["docker", "ps", "--filter", "name=nocodb_trading", "--format", "{{.Status}}"],
                capture_output=True,
                text=True
            )
            
            if "Up" in check.stdout:
                print(f"✅ NocoDB is running at {self.url}")
                print("📊 Opening browser...")
                webbrowser.open(self.url)
                return True
            else:
                print("❌ Container failed to start properly")
                return False
        else:
            print(f"❌ Error starting container: {result.stderr}")
            return False
    
    def stop(self):
        """Stop NocoDB container"""
        print("🛑 Stopping NocoDB...")
        os.chdir(self.nocodb_dir)
        
        result = subprocess.run(
            ["docker-compose", "-f", self.compose_file, "down"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ NocoDB stopped successfully")
        else:
            print(f"❌ Error stopping container: {result.stderr}")
    
    def status(self):
        """Check NocoDB status"""
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=nocodb_trading", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True
        )
        
        if "nocodb_trading" in result.stdout:
            print("✅ NocoDB Status:")
            print(result.stdout)
        else:
            print("❌ NocoDB is not running")
    
    def logs(self, lines=50):
        """Show NocoDB logs"""
        print(f"📋 Showing last {lines} lines of logs:")
        subprocess.run(["docker", "logs", "nocodb_trading", "--tail", str(lines)])
    
    def restart(self):
        """Restart NocoDB"""
        print("🔄 Restarting NocoDB...")
        self.stop()
        time.sleep(2)
        self.start()

def main():
    """Main CLI interface"""
    db = NocoDB()
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        command = "start"  # Default action
    else:
        command = sys.argv[1].lower()
    
    commands = {
        "start": db.start,
        "stop": db.stop,
        "restart": db.restart,
        "status": db.status,
        "logs": db.logs,
    }
    
    if command in commands:
        commands[command]()
    else:
        print("📊 NocoDB Database Manager")
        print("========================")
        print("\nUsage: python run_database.py [command]")
        print("\nCommands:")
        print("  start    - Start NocoDB (default)")
        print("  stop     - Stop NocoDB")
        print("  restart  - Restart NocoDB")
        print("  status   - Check if NocoDB is running")
        print("  logs     - Show container logs")
        print("\nExample:")
        print("  python run_database.py start")

if __name__ == "__main__":
    main()