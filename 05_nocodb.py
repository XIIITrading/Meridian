"""
NocoDB Launcher for Trading System
Starts Docker Desktop and opens NocoDB in Chrome
"""

import subprocess
import time
import socket
import sys
import os
from pathlib import Path

class NocoDBLauncher:
    def __init__(self):
        self.docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
        self.container_name = "nocodb_trading"
        self.nocodb_url = "http://localhost:8080"
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        
    def is_port_open(self, port=8080, host='localhost'):
        """Check if a port is accessible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def is_docker_running(self):
        """Check if Docker daemon is running"""
        try:
            result = subprocess.run(['docker', 'version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def start_docker_desktop(self):
        """Start Docker Desktop if not running"""
        print("🔍 Checking Docker Desktop...")
        
        if self.is_docker_running():
            print("✅ Docker is already running")
            return True
        
        print("🚀 Starting Docker Desktop...")
        try:
            subprocess.Popen([self.docker_path])
            
            # Wait for Docker to be ready (max 60 seconds)
            for i in range(60):
                time.sleep(1)
                if i % 5 == 0:
                    print(f"   Waiting for Docker... {i}s")
                if self.is_docker_running():
                    print("✅ Docker Desktop is ready!")
                    time.sleep(3)  # Extra time for full initialization
                    return True
            
            print("❌ Docker Desktop took too long to start")
            return False
            
        except FileNotFoundError:
            print("❌ Docker Desktop not found at expected location")
            print(f"   Expected: {self.docker_path}")
            return False
    
    def start_nocodb_container(self):
        """Start the NocoDB container"""
        print(f"🔍 Checking {self.container_name} container...")
        
        try:
            # Check container status
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', f'name={self.container_name}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                print(f"❌ Container '{self.container_name}' not found")
                print("   Please create it first using Docker Desktop")
                return False
            
            status = result.stdout.strip().lower()
            
            if 'up' in status:
                print(f"✅ {self.container_name} is already running")
                return True
            
            # Start the container
            print(f"🚀 Starting {self.container_name} container...")
            subprocess.run(['docker', 'start', self.container_name], check=True)
            
            # Wait for NocoDB to be accessible
            print("   Waiting for NocoDB to be ready...")
            for i in range(30):
                time.sleep(1)
                if self.is_port_open():
                    print("✅ NocoDB is ready!")
                    return True
                if i % 5 == 0:
                    print(f"   Still waiting... {i}s")
            
            print("❌ NocoDB took too long to start")
            return False
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error managing container: {e}")
            return False
    
    def open_chrome(self):
        """Open Chrome with NocoDB URL"""
        print("🌐 Opening Chrome...")
        
        try:
            # Try using Chrome directly
            if os.path.exists(self.chrome_path):
                subprocess.Popen([self.chrome_path, self.nocodb_url])
                print(f"✅ Opened {self.nocodb_url} in Chrome")
            else:
                # Fallback to default browser
                subprocess.run(['start', self.nocodb_url], shell=True)
                print(f"✅ Opened {self.nocodb_url} in default browser")
            return True
            
        except Exception as e:
            print(f"❌ Error opening browser: {e}")
            return False
    
    def launch(self):
        """Main launch sequence"""
        print("=" * 50)
        print("🚀 NocoDB Trading System Launcher")
        print("=" * 50)
        
        # Step 1: Start Docker
        if not self.start_docker_desktop():
            print("\n❌ Failed to start Docker Desktop")
            input("Press Enter to exit...")
            return False
        
        # Step 2: Start Container
        if not self.start_nocodb_container():
            print("\n❌ Failed to start NocoDB container")
            input("Press Enter to exit...")
            return False
        
        # Step 3: Open Browser
        time.sleep(2)  # Small delay before opening browser
        if not self.open_chrome():
            print("\n⚠️  Please manually open: http://localhost:8080")
        
        print("\n" + "=" * 50)
        print("✅ NocoDB Trading System is ready!")
        print("=" * 50)
        print("\n📊 Access NocoDB at: http://localhost:8080")
        print("💡 Tip: Keep this window open or NocoDB will keep running")
        print("\nPress Enter to exit (NocoDB will continue running)...")
        input()
        return True

def main():
    launcher = NocoDBLauncher()
    launcher.launch()

if __name__ == "__main__":
    main()