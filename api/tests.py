from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
import os
import tempfile
import shutil
import time
import psutil
from dashboard.models import App

class AppAPITests(APITestCase):
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.processes_to_cleanup = []
        
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
        
        # Create test app in database
        self.app = App.objects.create(
            name="Test Django App",
            path=self.manage_py_path,
            description="Test Description"
        )

    def tearDown(self):
        """Clean up test environment"""
        # Kill any processes we started
        for pid in self.processes_to_cleanup:
            try:
                process = psutil.Process(pid)
                for child in process.children(recursive=True):
                    child.kill()
                process.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Wait a moment for processes to fully terminate
        time.sleep(1)
        
        # Try to remove the test directory multiple times
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if os.path.exists(self.test_dir):
                    shutil.rmtree(self.test_dir)
                break
            except (PermissionError, OSError):
                if attempt < max_attempts - 1:
                    time.sleep(1)
                    continue
                # On final attempt, ignore errors
                try:
                    for root, dirs, files in os.walk(self.test_dir, topdown=False):
                        for name in files:
                            try:
                                os.chmod(os.path.join(root, name), 0o777)
                                os.remove(os.path.join(root, name))
                            except:
                                pass
                        for name in dirs:
                            try:
                                os.chmod(os.path.join(root, name), 0o777)
                                os.rmdir(os.path.join(root, name))
                            except:
                                pass
                except:
                    pass

    def test_list_apps(self):
        """Test GET /api/apps/"""
        url = reverse('app-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Test Django App")

    def test_create_app(self):
        """Test POST /api/apps/"""
        url = reverse('app-list')
        data = {
            'name': 'New Test App',
            'path': self.manage_py_path,
            'description': 'New Test Description'
        }
        response = self.client.post(url, data, format='json')
        print(f"\nCreate app response: {response.status_code}")
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(App.objects.count(), 2)
        self.assertEqual(response.data['name'], 'New Test App')

    def test_get_app_detail(self):
        """Test GET /api/apps/{id}/"""
        url = reverse('app-detail', args=[self.app.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Django App")

    def test_update_app(self):
        """Test PUT /api/apps/{id}/"""
        url = reverse('app-detail', args=[self.app.id])
        data = {
            'name': 'Updated App Name',
            'path': self.manage_py_path,
            'description': 'Updated Description'
        }
        response = self.client.put(url, data, format='json')
        print(f"\nUpdate app response: {response.status_code}")
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated App Name')

    def test_delete_app(self):
        """Test DELETE /api/apps/{id}/"""
        url = reverse('app-detail', args=[self.app.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(App.objects.count(), 0)

    def test_launch_app(self):
        """Test POST /api/apps/{id}/launch/"""
        url = reverse('app-launch', args=[self.app.id])
        response = self.client.post(url, {'install_dependencies': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('pid', response.data)
        if 'pid' in response.data:
            self.processes_to_cleanup.append(response.data['pid'])

    def test_stop_app(self):
        """Test POST /api/apps/{id}/stop/"""
        # First launch the app
        launch_url = reverse('app-launch', args=[self.app.id])
        launch_response = self.client.post(launch_url, {'install_dependencies': False})
        if 'pid' in launch_response.data:
            self.processes_to_cleanup.append(launch_response.data['pid'])
        
        # Wait a moment for the app to start
        time.sleep(2)
        
        # Then try to stop it
        stop_url = reverse('app-stop', args=[self.app.id])
        response = self.client.post(stop_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertTrue(response.data.get('success', False))

    def test_get_app_status(self):
        """Test GET /api/apps/{id}/status/"""
        # First launch the app
        launch_url = reverse('app-launch', args=[self.app.id])
        launch_response = self.client.post(launch_url, {'install_dependencies': False})
        if 'pid' in launch_response.data:
            self.processes_to_cleanup.append(launch_response.data['pid'])
        
        # Wait a moment for the app to start
        time.sleep(2)
        
        url = reverse('app-status', args=[self.app.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'Running')

    def test_get_app_output(self):
        """Test GET /api/apps/{id}/output/"""
        # First launch the app
        launch_url = reverse('app-launch', args=[self.app.id])
        launch_response = self.client.post(launch_url, {'install_dependencies': False})
        if 'pid' in launch_response.data:
            self.processes_to_cleanup.append(launch_response.data['pid'])
        
        # Wait a moment for output to be generated
        time.sleep(2)
        
        # Then get its output
        output_url = reverse('app-output', args=[self.app.id])
        response = self.client.get(output_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('output', response.data)
