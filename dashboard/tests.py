from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import os
import tempfile
import shutil
from .models import App
import re
from pathlib import Path
import glob
import json

class AppModelTests(TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories for different app types
        self.test_dir = tempfile.mkdtemp()
        self.django_app_dir = os.path.join(self.test_dir, 'django_app')
        self.flask_app_dir = os.path.join(self.test_dir, 'flask_app')
        self.python_script_dir = os.path.join(self.test_dir, 'python_script')
        
        # Create app directories
        os.makedirs(self.django_app_dir)
        os.makedirs(self.flask_app_dir)
        os.makedirs(self.python_script_dir)
        
        # Create Django app files
        self.manage_py_path = os.path.join(self.django_app_dir, 'manage.py')
        django_app_dir = os.path.join(self.django_app_dir, 'django_app')
        os.makedirs(django_app_dir)
        
        with open(self.manage_py_path, 'w') as f:
            f.write('''#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
''')
        
        # Create settings module
        with open(os.path.join(django_app_dir, '__init__.py'), 'w') as f:
            f.write('')
        with open(os.path.join(django_app_dir, 'settings.py'), 'w') as f:
            f.write('''
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'test-key'
DEBUG = True
ALLOWED_HOSTS = []
INSTALLED_APPS = []
''')
        
        # Create Flask app file
        self.flask_app_path = os.path.join(self.flask_app_dir, 'app.py')
        with open(self.flask_app_path, 'w') as f:
            f.write('''
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run()
''')
        
        # Create Python script
        self.script_path = os.path.join(self.python_script_dir, 'script.py')
        with open(self.script_path, 'w') as f:
            f.write('''
print("Hello from test script!")
''')
        
        # Create virtual environment structure for each app type
        for app_dir in [self.django_app_dir, self.flask_app_dir, self.python_script_dir]:
            venv_dir = os.path.join(app_dir, 'venv')
            scripts_dir = os.path.join(venv_dir, 'Scripts' if os.name == 'nt' else 'bin')
            os.makedirs(scripts_dir)
            
            if os.name == 'nt':
                activate_bat = os.path.join(scripts_dir, 'activate.bat')
                python_exe = os.path.join(scripts_dir, 'python.exe')
                with open(activate_bat, 'w') as f:
                    f.write('@echo off\nset "VIRTUAL_ENV=%~dp0.."\n')
                with open(python_exe, 'wb') as f:
                    f.write(b'dummy')
            else:
                activate_sh = os.path.join(scripts_dir, 'activate')
                python_bin = os.path.join(scripts_dir, 'python')
                with open(activate_sh, 'w') as f:
                    f.write('#!/bin/bash\nexport VIRTUAL_ENV="${BASH_SOURCE[0]%/*}/.."')
                with open(python_bin, 'wb') as f:
                    f.write(b'dummy')
                os.chmod(activate_sh, 0o755)
                os.chmod(python_bin, 0o755)

    def tearDown(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.test_dir)
        except (OSError, IOError):
            pass  # Ignore cleanup errors

    def test_app_creation(self):
        """Test basic app creation"""
        app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path,
            description="Test Description"
        )
        self.assertEqual(app.name, "Test Django App")
        self.assertEqual(app.path, self.manage_py_path)
        self.assertEqual(app.description, "Test Description")

    def test_is_django_app(self):
        """Test Django app detection"""
        app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path
        )
        self.assertTrue(app.is_django_app())

    def test_is_flask_app(self):
        """Test Flask app detection"""
        app = App.objects.create(
            name="Test Flask App",
            path=self.flask_app_path
        )
        self.assertTrue(app.is_flask_app())

    def test_get_venv_path(self):
        """Test virtual environment detection"""
        app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path
        )
        
        venv_info = app.get_venv_path()
        self.assertIsNotNone(venv_info)
        self.assertTrue(os.path.exists(venv_info['activate']))
        self.assertTrue(os.path.exists(venv_info['python']))

    def test_get_django_settings_module(self):
        """Test Django settings module detection"""
        app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path
        )
        settings_module = app.get_django_settings_module()
        self.assertEqual(settings_module, 'django_app.settings')

    def test_get_url(self):
        """Test URL generation for web apps"""
        app = App.objects.create(
            name="Test Web App",
            path=self.manage_py_path,
            port=8000
        )
        self.assertEqual(app.get_url(), "http://localhost:8000")

    def test_get_run_command_django(self):
        """Test run command generation for Django apps"""
        app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path,
            port=8000
        )
        
        # Generate and read the batch file content
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract the batch file path from the command
        batch_path = re.search(r'start "[^"]+" /min cmd /c "([^"]+)"', cmd).group(1)
        self.assertTrue(os.path.exists(batch_path))
        
        # Read the batch file content
        with open(batch_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        self.assertIn('python manage.py runserver', content)
        self.assertIn('8000', content)

    def test_get_run_command_flask(self):
        """Test run command generation for Flask apps"""
        app = App.objects.create(
            name="Test Flask App",
            path=self.flask_app_path,
            port=5000
        )
        
        # Generate and read the batch file content
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract the batch file path from the command
        batch_path = re.search(r'start "[^"]+" /min cmd /c "([^"]+)"', cmd).group(1)
        self.assertTrue(os.path.exists(batch_path))
        
        # Read the batch file content
        with open(batch_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        self.assertIn('python', content)
        self.assertIn('app.py', content)
        self.assertIn('5000', content)

    def test_get_run_command_python_script(self):
        """Test run command generation for Python scripts"""
        app = App.objects.create(
            name="Test Python Script",
            path=self.script_path
        )
        
        # Generate and read the batch file content
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract the batch file path from the command
        batch_path = re.search(r'start "[^"]+" /min cmd /c "([^"]+)"', cmd).group(1)
        self.assertTrue(os.path.exists(batch_path))
        
        # Read the batch file content
        with open(batch_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        self.assertIn('python', content)
        self.assertIn('script.py', content)

    def test_batch_file_persistence(self):
        """Test that batch files persist while the app is running"""
        app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path,
            port=8000
        )
        
        # Generate the batch file
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract the batch file path
        batch_path = re.search(r'start "[^"]+" /min cmd /c "([^"]+)"', cmd).group(1)
        self.assertTrue(os.path.exists(batch_path))
        
        # Simulate app running
        app.status = 'Running'
        app.save()
        
        # Batch file should still exist
        self.assertTrue(os.path.exists(batch_path))
        
        # Stop the app
        app.status = 'Stopped'
        app.save()
        
        # Generate a new batch file
        new_cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(new_cmd)
        
        # Extract the new batch file path
        new_batch_path = re.search(r'start "[^"]+" /min cmd /c "([^"]+)"', new_cmd).group(1)
        self.assertTrue(os.path.exists(new_batch_path))
        
        # The paths should be different
        self.assertNotEqual(batch_path, new_batch_path)

    def test_launch_django_app_integration(self):
        """Integration test for launching a Django app"""
        app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path,
            port=9001,
            type='web'
        )
        
        # Generate the command
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract and verify the batch file
        batch_path = re.search(r'start "[^"]+" /min cmd /c "([^"]+)"', cmd).group(1)
        self.assertTrue(os.path.exists(batch_path))
        
        # Read and verify batch file content
        with open(batch_path, 'r') as f:
            content = f.read()
            
        # Check for essential components
        self.assertIn('cd /d', content)  # Directory change
        self.assertIn('call', content)  # Virtual env activation
        self.assertIn('python manage.py runserver', content)  # Server start command
        self.assertIn('127.0.0.1:9001', content)  # Port specification
        self.assertIn('DJANGO_SETTINGS_MODULE', content)  # Django settings
        
        # Verify health check file
        health_files = glob.glob(os.path.join(os.path.dirname(batch_path), '_temp_health_*.bat'))
        self.assertEqual(len(health_files), 1, "Expected exactly one health check file")
        
        # Read and verify health check content
        with open(health_files[0], 'r') as f:
            health_content = f.read()
            
        # Check for essential components in health check
        self.assertIn('cd /d', health_content)  # Directory change
        self.assertIn('call', health_content)  # Virtual env activation
        self.assertIn('python -c', health_content)  # Python command
        self.assertIn('import requests', health_content)  # Requests import
        self.assertIn('requests.get', health_content)  # HTTP request
        self.assertIn('127.0.0.1:9001', health_content)  # Port specification
        self.assertIn('response.status_code == 200', health_content)  # Status check

    def test_launch_flask_app_integration(self):
        """Integration test for launching a Flask app"""
        app = App.objects.create(
            name="Test Flask App",
            path=self.flask_app_path,
            port=5000,
            type='web'
        )
        
        # Generate the command
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract and verify the batch file
        batch_path = re.search(r'start "[^"]+" /min cmd /c "([^"]+)"', cmd).group(1)
        self.assertTrue(os.path.exists(batch_path))
        
        # Read and verify batch file content
        with open(batch_path, 'r') as f:
            content = f.read()
            
        # Check for essential components
        self.assertIn('cd /d', content)  # Directory change
        self.assertIn('call', content)  # Virtual env activation
        self.assertIn('python', content)  # Python command
        self.assertIn('--host 127.0.0.1', content)  # Host specification
        self.assertIn('--port 5000', content)  # Port specification

    def test_launch_python_script_integration(self):
        """Integration test for launching a Python script"""
        # Create a more complex test script
        script_content = '''
import sys
import time

def main():
    print("Script started")
    for i in range(3):
        print(f"Running iteration {i}")
        time.sleep(1)
    print("Script completed")

if __name__ == '__main__':
    main()
'''
        with open(self.script_path, 'w') as f:
            f.write(script_content)

        app = App.objects.create(
            name="Test Python Script",
            path=self.script_path,
            type='script'
        )
        
        # Generate the command
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract and verify the batch file
        batch_path = re.search(r'start "[^"]+" /min cmd /c "([^"]+)"', cmd).group(1)
        self.assertTrue(os.path.exists(batch_path))
        
        # Read and verify batch file content
        with open(batch_path, 'r') as f:
            content = f.read()
            
        # Check for essential components
        self.assertIn('cd /d', content)  # Directory change
        self.assertIn('call', content)  # Virtual env activation
        self.assertIn('python', content)  # Python command
        self.assertIn('script.py', content)  # Script name
        self.assertIn('pause', content)  # Keep window open
        
        # Verify error handling
        self.assertIn('if !errorlevel! neq 0', content)  # Error checking
        self.assertIn('Script failed', content)  # Error message

class AppUITests(TestCase):
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        # Create temporary directories for different app types
        self.test_dir = tempfile.mkdtemp()
        self.django_app_dir = os.path.join(self.test_dir, 'django_app')
        os.makedirs(self.django_app_dir)
        
        # Create Django app files
        self.manage_py_path = os.path.join(self.django_app_dir, 'manage.py')
        with open(self.manage_py_path, 'w') as f:
            f.write('''#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
''')
        
        # Create virtual environment structure
        venv_dir = os.path.join(self.django_app_dir, 'venv')
        scripts_dir = os.path.join(venv_dir, 'Scripts' if os.name == 'nt' else 'bin')
        os.makedirs(scripts_dir)
        
        if os.name == 'nt':
            activate_bat = os.path.join(scripts_dir, 'activate.bat')
            python_exe = os.path.join(scripts_dir, 'python.exe')
            with open(activate_bat, 'w') as f:
                f.write('@echo off\nset "VIRTUAL_ENV=%~dp0.."\n')
            with open(python_exe, 'wb') as f:
                f.write(b'dummy')
        else:
            activate_sh = os.path.join(scripts_dir, 'activate')
            python_bin = os.path.join(scripts_dir, 'python')
            with open(activate_sh, 'w') as f:
                f.write('#!/bin/bash\nexport VIRTUAL_ENV="${BASH_SOURCE[0]%/*}/.."')
            with open(python_bin, 'wb') as f:
                f.write(b'dummy')
            os.chmod(activate_sh, 0o755)
            os.chmod(python_bin, 0o755)

        # Create test app
        self.app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path,
            type='web',
            port=9001
        )

    def tearDown(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.test_dir)
        except (OSError, IOError):
            pass

    def test_loading_screen_visibility(self):
        """Test that loading screen is shown and hidden appropriately"""
        # Get the app list page
        response = self.client.get(reverse('app_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that loading screen div exists and is initially hidden
        self.assertContains(response, 'id="loadingScreen"')
        self.assertContains(response, 'class="loading-screen"')
        
        # Check for loading screen content
        self.assertContains(response, 'Loading')
        self.assertContains(response, 'spinner')

    def test_button_states_and_status_updates(self):
        """Test button states and status updates when app is running/stopped."""
        response = self.client.get(reverse('app_list'))
        self.assertEqual(response.status_code, 200)
        
        # Initial state
        self.assertContains(response, 'bg-secondary')  # Status badge should be secondary
        self.assertContains(response, 'btn-success')  # Launch button should be success
        self.assertContains(response, 'Stopped')  # Status should be Stopped
        
        # Simulate app running
        app = App.objects.first()
        app.status = 'Running'
        app.port = 9001
        app.save()
        
        response = self.client.get(reverse('app_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bg-success')  # Status badge should be success
        self.assertContains(response, 'btn-danger')  # Stop button should be danger
        self.assertContains(response, '9001')  # Port should be shown

    def test_launch_button_click(self):
        """Test the launch button click behavior"""
        # Get the initial state
        response = self.client.get(reverse('app_list'))
        self.assertEqual(response.status_code, 200)
        
        # Verify initial button state
        self.assertContains(response, 'data-app-id="{}"'.format(self.app.id))
        self.assertContains(response, 'btn-primary')  # Launch button class
        
        # Simulate launch API call
        response = self.client.post(
            reverse('launch_app', args=[self.app.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check response format
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertIn('port', data)

    def test_stop_button_click(self):
        """Test the stop button click behavior"""
        # Set app as running
        self.app.status = 'Running'
        self.app.save()
        
        # Get the page with running app
        response = self.client.get(reverse('app_list'))
        self.assertEqual(response.status_code, 200)
        
        # Verify stop button state
        self.assertContains(response, 'data-app-id="{}"'.format(self.app.id))
        self.assertContains(response, 'btn-danger')  # Stop button class
        
        # Simulate stop API call
        response = self.client.post(
            reverse('stop_app', args=[self.app.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check response format
        data = json.loads(response.content)
        self.assertIn('status', data)

    def test_status_polling(self):
        """Test status polling functionality"""
        # Set up app with running status
        self.app.status = 'Running'
        self.app.save()
        
        # Test status endpoint
        response = self.client.get(reverse('app_status', args=[self.app.id]))
        self.assertEqual(response.status_code, 200)
        
        # Check response format
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertIn('port', data)
        self.assertEqual(data['status'], 'Running')
        self.assertEqual(data['port'], self.app.port)
