from django.test import TestCase
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import os
import tempfile
import shutil
from .models import App

class AppModelTests(TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a sample Django app
        self.django_app_dir = os.path.join(self.test_dir, 'test_django_app')
        os.makedirs(self.django_app_dir)
        
        # Create manage.py
        manage_py_content = '''#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_django_app.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
'''
        self.manage_py_path = os.path.join(self.django_app_dir, 'manage.py')
        with open(self.manage_py_path, 'w') as f:
            f.write(manage_py_content)
        
        # Create settings.py
        settings_dir = os.path.join(self.django_app_dir, 'test_django_app')
        os.makedirs(settings_dir)
        settings_content = '''
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'test-key'
DEBUG = True
ALLOWED_HOSTS = []
INSTALLED_APPS = []
MIDDLEWARE = []
ROOT_URLCONF = 'test_django_app.urls'
TEMPLATES = []
WSGI_APPLICATION = 'test_django_app.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
'''
        with open(os.path.join(settings_dir, 'settings.py'), 'w') as f:
            f.write(settings_content)
        
        # Create a sample Flask app
        self.flask_app_dir = os.path.join(self.test_dir, 'test_flask_app')
        os.makedirs(self.flask_app_dir)
        flask_content = '''
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run()
'''
        self.flask_app_path = os.path.join(self.flask_app_dir, 'app.py')
        with open(self.flask_app_path, 'w') as f:
            f.write(flask_content)
        
        # Create a sample Python script
        self.python_script_dir = os.path.join(self.test_dir, 'test_python_script')
        os.makedirs(self.python_script_dir)
        script_content = '''
print("Hello from test script!")
'''
        self.script_path = os.path.join(self.python_script_dir, 'script.py')
        with open(self.script_path, 'w') as f:
            f.write(script_content)
        
        # Create virtual environment structure
        self.venv_dir = os.path.join(self.test_dir, 'venv')
        os.makedirs(os.path.join(self.venv_dir, 'Scripts' if os.name == 'nt' else 'bin'))
        if os.name == 'nt':
            open(os.path.join(self.venv_dir, 'Scripts', 'activate.bat'), 'w').close()
            open(os.path.join(self.venv_dir, 'Scripts', 'python.exe'), 'w').close()
        else:
            open(os.path.join(self.venv_dir, 'bin', 'activate'), 'w').close()
            open(os.path.join(self.venv_dir, 'bin', 'python'), 'w').close()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

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
        # Create venv structure in the app directory
        app_venv_dir = os.path.join(self.django_app_dir, 'venv')
        os.makedirs(os.path.join(app_venv_dir, 'Scripts' if os.name == 'nt' else 'bin'))
        if os.name == 'nt':
            open(os.path.join(app_venv_dir, 'Scripts', 'activate.bat'), 'w').close()
            open(os.path.join(app_venv_dir, 'Scripts', 'python.exe'), 'w').close()
        else:
            open(os.path.join(app_venv_dir, 'bin', 'activate'), 'w').close()
            open(os.path.join(app_venv_dir, 'bin', 'python'), 'w').close()

        app = App.objects.create(
            name="Test App",
            path=os.path.join(self.django_app_dir, 'manage.py')
        )
        venv_info = app.get_venv_path()
        self.assertIsNotNone(venv_info)
        self.assertEqual(venv_info['root'], app_venv_dir)

    def test_get_django_settings_module(self):
        """Test Django settings module detection"""
        app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path
        )
        settings_module = app.get_django_settings_module()
        self.assertEqual(settings_module, 'test_django_app.settings')

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
        # Create venv structure
        venv_dir = os.path.join(self.django_app_dir, 'venv')
        os.makedirs(os.path.join(venv_dir, 'Scripts' if os.name == 'nt' else 'bin'))
        if os.name == 'nt':
            open(os.path.join(venv_dir, 'Scripts', 'activate.bat'), 'w').close()
            open(os.path.join(venv_dir, 'Scripts', 'python.exe'), 'w').close()
        else:
            open(os.path.join(venv_dir, 'bin', 'activate'), 'w').close()
            open(os.path.join(venv_dir, 'bin', 'python'), 'w').close()

        app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path,
            port=8000
        )
        
        # Generate and read the batch file content
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract the batch file path from the command
        import re
        batch_path = re.search(r'"([^"]+_temp_run\.bat)"', cmd).group(1)
        self.assertTrue(os.path.exists(batch_path))
        
        # Read the batch file content
        with open(batch_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        self.assertIn('python manage.py runserver', content)
        self.assertIn('8000', content)

    def test_get_run_command_flask(self):
        """Test run command generation for Flask apps"""
        # Create venv structure
        venv_dir = os.path.join(self.flask_app_dir, 'venv')
        os.makedirs(os.path.join(venv_dir, 'Scripts' if os.name == 'nt' else 'bin'))
        if os.name == 'nt':
            open(os.path.join(venv_dir, 'Scripts', 'activate.bat'), 'w').close()
            open(os.path.join(venv_dir, 'Scripts', 'python.exe'), 'w').close()
        else:
            open(os.path.join(venv_dir, 'bin', 'activate'), 'w').close()
            open(os.path.join(venv_dir, 'bin', 'python'), 'w').close()

        app = App.objects.create(
            name="Test Flask App",
            path=self.flask_app_path,
            port=5000
        )
        
        # Generate and read the batch file content
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract the batch file path from the command
        import re
        batch_path = re.search(r'"([^"]+_temp_run\.bat)"', cmd).group(1)
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
        # Create venv structure
        venv_dir = os.path.join(self.python_script_dir, 'venv')
        os.makedirs(os.path.join(venv_dir, 'Scripts' if os.name == 'nt' else 'bin'))
        if os.name == 'nt':
            open(os.path.join(venv_dir, 'Scripts', 'activate.bat'), 'w').close()
            open(os.path.join(venv_dir, 'Scripts', 'python.exe'), 'w').close()
        else:
            open(os.path.join(venv_dir, 'bin', 'activate'), 'w').close()
            open(os.path.join(venv_dir, 'bin', 'python'), 'w').close()

        app = App.objects.create(
            name="Test Python Script",
            path=self.script_path
        )
        
        # Generate and read the batch file content
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract the batch file path from the command
        import re
        batch_path = re.search(r'"([^"]+_temp_run\.bat)"', cmd).group(1)
        self.assertTrue(os.path.exists(batch_path))
        
        # Read the batch file content
        with open(batch_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        self.assertIn('python', content)
        self.assertIn('script.py', content)

    def test_batch_file_persistence(self):
        """Test that batch files persist while the app is running"""
        # Create venv structure
        venv_dir = os.path.join(self.django_app_dir, 'venv')
        os.makedirs(os.path.join(venv_dir, 'Scripts' if os.name == 'nt' else 'bin'))
        if os.name == 'nt':
            open(os.path.join(venv_dir, 'Scripts', 'activate.bat'), 'w').close()
            open(os.path.join(venv_dir, 'Scripts', 'python.exe'), 'w').close()

        app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path,
            port=8000
        )
        
        # Generate the batch file
        cmd = app.get_run_command(install_dependencies=False)
        self.assertIsNotNone(cmd)
        
        # Extract the batch file path
        import re
        batch_path = re.search(r'"([^"]+_temp_run\.bat)"', cmd).group(1)
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
        new_batch_path = re.search(r'"([^"]+_temp_run\.bat)"', new_cmd).group(1)
        self.assertTrue(os.path.exists(new_batch_path))
        
        # The paths should be different
        self.assertNotEqual(batch_path, new_batch_path)
