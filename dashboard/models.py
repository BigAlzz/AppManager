from django.db import models
import os
from pathlib import Path
import re
from django.utils import timezone
from datetime import timedelta
import psutil

# Create your models here.

class App(models.Model):
    APP_TYPES = [
        ('executable', 'Executable'),
        ('script', 'Script'),
        ('web', 'Web Tool'),
    ]

    RATING_CHOICES = [
        (1, '★'),
        (2, '★★'),
        (3, '★★★'),
        (4, '★★★★'),
        (5, '★★★★★'),
    ]

    name = models.CharField(max_length=100)
    path = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=APP_TYPES)
    status = models.CharField(max_length=20, default='Stopped')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True)
    user_guide = models.TextField(blank=True, help_text="Detailed instructions on how to use this application")
    port = models.IntegerField(null=True, blank=True, help_text="Port number for web applications")
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True, help_text="Star rating for this application")
    
    # Class variables for port management
    PORT_RANGE_START = 9000  # Starting from port 9000 to avoid common ports
    PORT_RANGE_END = 9999
    RESERVED_PORTS = {5000, 8000, 8080}  # Common ports to avoid
    
    def __str__(self):
        return f"{self.name} ({self.type})"

    @staticmethod
    def get_file_type(file_path):
        """Determine the type of the application based on file extension"""
        ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
        if ext in ['exe']:
            return 'executable'
        elif ext in ['py', 'bat', 'cmd', 'ps1', 'vbs']:
            return 'script'
        elif ext in ['url', 'html', 'htm']:
            return 'web'
        return None

    @staticmethod
    def extract_text_from_file(file_path, max_size=100000):
        """Extract text content from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read(max_size)
        except:
            try:
                # Try different encoding if utf-8 fails
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read(max_size)
            except:
                return None

    @staticmethod
    def is_main_file(file_path, content=None):
        """Check if the file is likely a main entry point"""
        file_name = os.path.basename(file_path).lower()
        if file_name in ['manage.py', 'main.py']:
            return True
            
        if not content and file_path.endswith('.py'):
            content = App.extract_text_from_file(file_path)
            
        if content:
            # Look for common main patterns in Python files
            main_patterns = [
                'if __name__ == "__main__"',
                'if __name__ == \'__main__\'',
                'def main():',
                'class Main',
                'argparse.ArgumentParser',
                'sys.argv'
            ]
            return any(pattern in content for pattern in main_patterns)
        return False

    @classmethod
    def discover_apps(cls, directory_path, progress_callback=None):
        """
        Discover applications in the given directory and its subdirectories
        Returns a list of dictionaries containing app information
        """
        def log(message):
            if progress_callback:
                progress_callback(message)

        def is_backup_path(path):
            """Check if path contains backup folders or is too deeply nested"""
            parts = Path(path).parts
            # Check for backup indicators
            backup_indicators = ['backup', 'bak', '.bak', 'old', '.old']
            has_backup = any(part.lower() in backup_indicators for part in parts)
            # Check for repeated folder names (indicating backup copies)
            has_repeats = any(parts.count(part) > 1 for part in parts)
            # Check for excessive nesting
            is_too_deep = len(parts) > 10
            return has_backup or has_repeats or is_too_deep

        discovered_apps = []
        directory_path = Path(directory_path)
        log(f"Starting discovery in: {directory_path}")

        # Keep track of discovered app paths to avoid duplicates
        discovered_paths = set()

        for root, dirs, files in os.walk(directory_path):
            # Skip if this is a backup path or too deeply nested
            if is_backup_path(root):
                log(f"Skipping backup/nested path: {root}")
                dirs.clear()  # Skip all subdirectories
                continue

            root_path = Path(root)
            log(f"\nScanning directory: {root_path}")
            
            # Skip common non-app directories
            skip_dirs = ['.git', '__pycache__', 'node_modules', 'build', 'dist', 'backup', 'bak', '.bak']
            # Don't skip venv directories during scan, but don't scan inside them
            venv_dirs = ['venv', '.venv', 'env', '.env']
            has_venv = any(vd in dirs for vd in venv_dirs)
            
            # Update dirs in place to skip unwanted directories
            dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and d not in venv_dirs]
            
            # Look for Django apps (manage.py)
            if 'manage.py' in files:
                file_path = root_path / 'manage.py'
                if str(file_path) not in discovered_paths and cls.extract_text_from_file(file_path) and 'DJANGO_SETTINGS_MODULE' in cls.extract_text_from_file(file_path):
                    log(f"Found Django application: {file_path}")
                    app_info = {
                        'name': root_path.name,
                        'path': str(file_path),
                        'type': 'script',
                        'description': f'Django web application{" (with venv)" if has_venv else ""}',
                        'user_guide': ''
                    }
                    cls._process_documentation(root_path, files, app_info, log)
                    discovered_apps.append(app_info)
                    discovered_paths.add(str(file_path))
                    log(f"Added Django application: {app_info['name']}")
                    continue

            # Look for Flask apps (app.py, run.py, main.py)
            flask_files = [f for f in files if f.lower() in ['app.py', 'run.py', 'main.py']]
            for file_name in flask_files:
                file_path = root_path / file_name
                if str(file_path) not in discovered_paths:
                    content = cls.extract_text_from_file(file_path)
                    if content and ('from flask import' in content or 'import flask' in content.lower()):
                        log(f"Found Flask application: {file_path}")
                        app_info = {
                            'name': root_path.name,
                            'path': str(file_path),
                            'type': 'script',
                            'description': f'Flask web application{" (with venv)" if has_venv else ""}',
                            'user_guide': ''
                        }
                        cls._process_documentation(root_path, files, app_info, log)
                        discovered_apps.append(app_info)
                        discovered_paths.add(str(file_path))
                        log(f"Added Flask application: {app_info['name']}")
                        break  # Only add one Flask app per directory

        log(f"\nDiscovery complete. Found {len(discovered_apps)} applications.")
        return discovered_apps

    @classmethod
    def _process_documentation(cls, root_path, files, app_info, log):
        """Helper method to process documentation files"""
        # Look for documentation
        log("Searching for documentation...")
        doc_files = [f for f in files if f.lower() in [
            'readme.txt', 'readme.md', 'help.txt', 'guide.txt',
            'manual.txt', 'instructions.txt', 'about.txt'
        ]]

        for doc_file in doc_files:
            doc_path = root_path / doc_file
            log(f"Found documentation: {doc_file}")
            content = cls.extract_text_from_file(doc_path)
            if content:
                # Use first few lines as description
                lines = content.split('\n')
                app_info['description'] = '\n'.join(lines[:3])
                app_info['user_guide'] = content
                log("Extracted description and user guide from documentation")
                break  # Use only the first documentation file found

        # Look for specific user guide files if no documentation was found
        if not app_info['user_guide']:
            guide_files = [f for f in files if f.lower() in [
                'userguide.txt', 'user_guide.txt', 'manual.pdf',
                'guide.md', 'instructions.md'
            ]]

            if guide_files:
                guide_path = root_path / guide_files[0]
                log(f"Found user guide: {guide_files[0]}")
                content = cls.extract_text_from_file(guide_path)
                if content:
                    app_info['user_guide'] = content
                    log("Extracted user guide content")

    @classmethod
    def cleanup_recent_apps(cls, minutes=5):
        """Remove apps that were added in the last X minutes"""
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        recent_apps = cls.objects.filter(created_at__gte=cutoff_time)
        count = recent_apps.count()
        recent_apps.delete()
        return count

    @classmethod
    def get_next_available_port(cls):
        """Find the next available port number"""
        # Get all currently used ports
        used_ports = set(cls.objects.exclude(port__isnull=True).values_list('port', flat=True))
        used_ports.update(cls.RESERVED_PORTS)
        
        # Find the first available port in our range
        for port in range(cls.PORT_RANGE_START, cls.PORT_RANGE_END + 1):
            if port not in used_ports:
                return port
        return None

    def allocate_port(self):
        """Allocate a port number for this application"""
        if not self.port:
            self.port = self.get_next_available_port()
            if self.port:
                self.save(update_fields=['port'])
                return True
        return False

    def release_port(self):
        """Release the allocated port"""
        if self.port:
            self.port = None
            self.save(update_fields=['port'])
            return True
        return False

    def is_django_app(self):
        """Check if this is a Django application"""
        if not self.path.endswith('manage.py'):
            return False
        content = self.extract_text_from_file(self.path)
        return content and 'DJANGO_SETTINGS_MODULE' in content

    def is_flask_app(self):
        """Check if this is a Flask application"""
        if not self.path.endswith('.py'):
            return False
        content = self.extract_text_from_file(self.path)
        return content and ('from flask import' in content or 'import flask' in content.lower())

    def get_venv_path(self):
        """Get virtual environment information if it exists."""
        app_dir = os.path.dirname(self.path)
        venv_dirs = ['venv', '.venv', 'env', '.env']
        
        for venv_name in venv_dirs:
            venv_path = os.path.join(app_dir, venv_name)
            if os.path.isdir(venv_path):
                # Check for Windows vs Unix
                if os.name == 'nt':
                    python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
                    activate_path = os.path.join(venv_path, 'Scripts', 'activate.bat')
                else:
                    python_path = os.path.join(venv_path, 'bin', 'python')
                    activate_path = os.path.join(venv_path, 'bin', 'activate')
                
                if os.path.exists(python_path):
                    return {
                        'root': venv_path,
                        'python': python_path,
                        'activate': activate_path
                    }
        return None

    def get_activate_command(self):
        """Get the command to activate the virtual environment"""
        venv_info = self.get_venv_path()
        if venv_info:
            return f'"{venv_info["activate"]}"'
        return ""

    def get_django_settings_module(self):
        """Get the Django settings module name from manage.py"""
        if not self.is_django_app():
            return None
            
        content = self.extract_text_from_file(self.path)
        if not content:
            return None
            
        # Try to find the settings module in manage.py
        match = re.search(r'os\.environ\.setdefault\(["\']DJANGO_SETTINGS_MODULE["\'],\s*["\']([^"\']+)["\']\)', content)
        if match:
            return match.group(1)
            
        # If not found in manage.py, look for settings.py in common locations
        app_dir = os.path.dirname(self.path)
        possible_locations = [
            os.path.join(app_dir, 'settings.py'),
            os.path.join(app_dir, 'config', 'settings.py'),
            os.path.join(app_dir, app_dir.split(os.path.sep)[-1], 'settings.py')
        ]
        
        for settings_path in possible_locations:
            if os.path.exists(settings_path):
                # Use the directory name as the module name
                module_name = os.path.basename(app_dir)
                return f"{module_name}.settings"
                
        return None

    def get_run_command(self):
        """Get the command to run the application."""
        if not os.path.exists(self.path):
            return None
        
        venv_info = self.get_venv_path()
        app_dir = os.path.dirname(self.path)
        
        # Handle different app types
        if self.is_django_app():
            project_root = os.path.dirname(self.path)
            settings_module = self.get_django_settings_module()
            
            if os.name == 'nt':
                # For Windows, create a minimal batch file
                batch_content = [
                    '@echo off',
                    'title Django Server',  # Set a consistent title for the window
                    f'cd /d "{project_root}"'
                ]
                
                # Add venv activation if available
                if venv_info:
                    batch_content.append(f'call "{venv_info["activate"]}" > nul 2>&1')
                    
                    # Check for requirements.txt and install if exists
                    requirements_file = os.path.join(project_root, 'requirements.txt')
                    if os.path.exists(requirements_file):
                        batch_content.extend([
                            'echo Installing dependencies...',
                            f'pip install -r "{requirements_file}" > nul 2>&1',
                            'if errorlevel 1 (',
                            '    echo Failed to install dependencies',
                            '    pause',
                            '    exit /b 1',
                            ')',
                            'echo Dependencies installed successfully'
                        ])
                
                # Add environment variables and Django command with minimal output
                if settings_module:
                    batch_content.append(f'set "DJANGO_SETTINGS_MODULE={settings_module}" > nul 2>&1')
                    batch_content.append('set "PYTHONUNBUFFERED=1" > nul 2>&1')
                
                # Run Django with minimal output
                batch_content.append(f'python -W ignore manage.py runserver 127.0.0.1:{self.port} --noreload --nothreading')
                
                # Create a temporary batch file
                batch_path = os.path.join(project_root, '_temp_run.bat')
                with open(batch_path, 'w') as f:
                    f.write('\n'.join(batch_content))
                
                # Return command to run the batch file in a new window
                return f'start "Django Server - {self.name}" /min cmd /k "{batch_path}"'
            else:
                # For Unix systems, minimal command
                cmd_parts = [
                    'gnome-terminal -- bash -c "',
                    f'cd "{project_root}"'
                ]
                
                if venv_info:
                    cmd_parts.append(f'source "{venv_info["activate"]}" > /dev/null 2>&1')
                    
                    # Check for requirements.txt and install if exists
                    requirements_file = os.path.join(project_root, 'requirements.txt')
                    if os.path.exists(requirements_file):
                        cmd_parts.extend([
                            'echo Installing dependencies...',
                            f'pip install -r "{requirements_file}" > /dev/null 2>&1 || {{ echo "Failed to install dependencies"; read -p "Press Enter to continue..."; exit 1; }}',
                            'echo Dependencies installed successfully'
                        ])
                
                if settings_module:
                    cmd_parts.append(f'export DJANGO_SETTINGS_MODULE={settings_module}')
                    cmd_parts.append('export PYTHONUNBUFFERED=1')
                
                cmd_parts.append(f'python -W ignore manage.py runserver 127.0.0.1:{self.port} --noreload --nothreading"')
                
                return ' && '.join(cmd_parts)
                
        elif self.is_flask_app():
            if os.name == 'nt':
                # Create minimal batch file for Flask app
                batch_content = [
                    '@echo off',
                    f'cd /d "{app_dir}"'
                ]
                
                if venv_info:
                    batch_content.append(f'call "{venv_info["activate"]}" > nul')
                
                batch_content.append(f'python "{os.path.basename(self.path)}" --host 127.0.0.1 --port {self.port}')
                
                # Create a temporary batch file
                batch_path = os.path.join(app_dir, '_temp_run.bat')
                with open(batch_path, 'w') as f:
                    f.write('\n'.join(batch_content))
                
                return f'start "Flask Server - {self.name}" cmd /k "{batch_path}"'
            else:
                cmd_parts = [
                    'gnome-terminal -- bash -c "',
                    f'cd "{app_dir}"'
                ]
                
                if venv_info:
                    cmd_parts.append(f'source "{venv_info["activate"]}" > /dev/null')
                
                cmd_parts.append(f'python "{os.path.basename(self.path)}" --host 127.0.0.1 --port {self.port}"')
                
                return ' && '.join(cmd_parts)
                
        elif self.path.lower().endswith('.py'):
            if os.name == 'nt':
                # Create minimal batch file for Python script
                batch_content = [
                    '@echo off',
                    f'cd /d "{app_dir}"'
                ]
                
                if venv_info:
                    batch_content.append(f'call "{venv_info["activate"]}" > nul')
                
                batch_content.append(f'python "{os.path.basename(self.path)}"')
                
                # Create a temporary batch file
                batch_path = os.path.join(app_dir, '_temp_run.bat')
                with open(batch_path, 'w') as f:
                    f.write('\n'.join(batch_content))
                
                return f'start "Python Script - {self.name}" cmd /k "{batch_path}"'
            else:
                cmd_parts = [
                    'gnome-terminal -- bash -c "',
                    f'cd "{app_dir}"'
                ]
                
                if venv_info:
                    cmd_parts.append(f'source "{venv_info["activate"]}" > /dev/null')
                
                cmd_parts.append(f'python "{os.path.basename(self.path)}"')
                
                return ' && '.join(cmd_parts)
        
        return None

    def get_url(self):
        """Get the URL for the application if it's a web app"""
        if self.port:
            return f"http://localhost:{self.port}"
        return None

    def is_running(self):
        """Check if the application is actually running"""
        # Get the latest launch log to find the process ID
        latest_launch = self.logs.filter(action='launch').order_by('-timestamp').first()
        
        if latest_launch:
            try:
                # Extract PID from launch details
                pid_match = re.search(r'PID: (\d+)', latest_launch.details)
                if pid_match:
                    pid = int(pid_match.group(1))
                    try:
                        process = psutil.Process(pid)
                        if process.is_running():
                            # Check if this is actually our process
                            cmdline = ' '.join(process.cmdline())
                            if self.path in cmdline:
                                return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception:
                pass
            
        # For web apps, try to connect to the port as a fallback
        if self.port and (self.is_django_app() or self.is_flask_app()):
            import socket
            try:
                sock = socket.create_connection(('127.0.0.1', self.port), timeout=1)
                sock.close()
                return True
            except (socket.timeout, ConnectionRefusedError):
                pass
            
        return False

    def update_status(self):
        """Update the application status based on whether it's actually running"""
        is_running = self.is_running()
        if is_running and self.status != 'Running':
            self.status = 'Running'
            self.save(update_fields=['status'])
            AppLog.objects.create(
                app=self,
                action='status_update',
                details='Application detected as running'
            )
        elif not is_running and self.status == 'Running':
            self.status = 'Stopped'
            if self.port:
                self.release_port()
            self.save(update_fields=['status', 'port'])
            AppLog.objects.create(
                app=self,
                action='status_update',
                details='Application detected as stopped'
            )
        return self.status

class AppLog(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()
    
    def __str__(self):
        return f"{self.app.name} - {self.action} at {self.timestamp}"
