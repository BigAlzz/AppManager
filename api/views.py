from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import psutil
import subprocess
import os
import webbrowser
from dashboard.models import App, AppLog
from .serializers import AppSerializer, AppLogSerializer
from django.http import JsonResponse
import time
import re

# Create your views here.

class AppViewSet(viewsets.ModelViewSet):
    queryset = App.objects.all()
    serializer_class = AppSerializer

    @action(detail=True, methods=['post'])
    def launch(self, request, pk=None):
        """Launch an application."""
        app = self.get_object()
        
        # Get dependency installation preference from request
        install_dependencies = request.data.get('install_dependencies', True)
        
        # Create a temporary file for output
        output_file = os.path.join(os.path.dirname(app.path), '_temp_output.txt')
        
        try:
            # Initialize output file with header
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Starting {app.name}...\n")
                f.write("Checking environment...\n")
                
                # Log venv info if available
                venv_info = app.get_venv_path()
                if venv_info:
                    f.write(f"Using virtual environment: {venv_info['root']}\n")
                    f.write("Activating virtual environment...\n")
                else:
                    f.write("No virtual environment found, using system Python\n")
                
                if install_dependencies:
                    f.write("Will install dependencies before running\n")
                else:
                    f.write("Dependency installation skipped (user choice)\n")
            
            # For Django/Flask apps, ensure a port is allocated
            if app.is_django_app() or app.is_flask_app():
                if not app.port:
                    app.allocate_port()
                if not app.port:
                    return Response({
                        'success': False,
                        'error': 'Failed to allocate a port for the application'
                    })
            
            # Get the command to run the application
            cmd = app.get_run_command(install_dependencies)
            if not cmd:
                return Response({
                    'success': False,
                    'error': 'Failed to generate run command'
                })
            
            # Start the process with proper output redirection
            if os.name == 'nt':
                # For Windows, start the process and redirect output
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
            else:
                process = subprocess.Popen(cmd, shell=True)
            
            # Log the launch with PID
            app.logs.create(
                action='launch',
                details=f'Process started with PID: {process.pid}'
            )
            
            # Update app status
            app.status = 'Running'
            app.save()
            
            # Wait briefly for initial output
            time.sleep(1)
            
            # Try to read initial output
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    initial_output = f.read()
            except:
                initial_output = 'Initializing...'
            
            # Return success response with URL if it's a web app
            response_data = {
                'success': True,
                'output': initial_output,
                'pid': process.pid
            }
            
            if app.is_django_app() or app.is_flask_app():
                response_data['url'] = app.get_url()
            
            return Response(response_data)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            })

    @action(detail=True, methods=['GET'])
    def output(self, request, pk=None):
        """Get the terminal output for an application."""
        app = self.get_object()
        output_file = os.path.join(os.path.dirname(app.path), '_temp_output.txt')
        
        try:
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    output = f.read()
                return Response({'output': output})
            return Response({'output': ''})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop a running application."""
        app = self.get_object()
        terminated_pids = []
        
        # Get the latest launch log to find the process ID
        latest_launch = app.logs.filter(action='launch').order_by('-timestamp').first()
        
        if latest_launch:
            try:
                # Extract PID from launch details
                pid_match = re.search(r'PID: (\d+)', latest_launch.details)
                if pid_match:
                    pid = int(pid_match.group(1))
                    try:
                        process = psutil.Process(pid)
                        # Kill all child processes first
                        for child in process.children(recursive=True):
                            child.kill()
                            terminated_pids.append(child.pid)
                        # Then kill the main process
                        process.kill()
                        terminated_pids.append(pid)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e)
                })
        
        # Update app status
        app.status = 'Stopped'
        app.save()
        
        # Log the stop action
        app.logs.create(
            action='stop',
            details=f'Application stopped. Terminated PIDs: {terminated_pids}'
        )
        
        return Response({
            'success': True,
            'message': 'Application stopped successfully',
            'terminated_pids': terminated_pids
        })

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        app = self.get_object()
        return Response({'status': app.status})

    @action(detail=True, methods=['get'])
    def check_status(self, request, pk=None):
        """Check if the application is actually running and update its status"""
        app = self.get_object()
        
        # Get the latest launch log to find the process ID
        latest_launch = app.logs.filter(action='launch').order_by('-timestamp').first()
        
        if latest_launch:
            try:
                # Extract PID from launch details
                pid_match = re.search(r'PID: (\d+)', latest_launch.details)
                if pid_match:
                    pid = int(pid_match.group(1))
                    
                    # Check if process is still running
                    try:
                        process = psutil.Process(pid)
                        if process.is_running():
                            # Process is running, update status if needed
                            if app.status != 'Running':
                                app.status = 'Running'
                                app.save()
                                AppLog.objects.create(
                                    app=app,
                                    action='status_update',
                                    details=f'Process {pid} confirmed running'
                                )
                        else:
                            # Process not running, update status
                            if app.status == 'Running':
                                app.status = 'Stopped'
                                app.save()
                                AppLog.objects.create(
                                    app=app,
                                    action='status_update',
                                    details=f'Process {pid} not found, marked as stopped'
                                )
                    except psutil.NoSuchProcess:
                        # Process not found, update status
                        if app.status == 'Running':
                            app.status = 'Stopped'
                            app.save()
                            AppLog.objects.create(
                                app=app,
                                action='status_update',
                                details=f'Process {pid} not found, marked as stopped'
                            )
            except Exception as e:
                # Log the error but don't change status
                AppLog.objects.create(
                    app=app,
                    action='status_check_error',
                    details=f'Error checking status: {str(e)}'
                )
        
        return Response({
            'status': app.status,
            'port': app.port,
            'url': app.get_url()
        })

    @action(detail=True, methods=['POST'])
    def rate(self, request, pk=None):
        """Handle app rating updates"""
        app = self.get_object()
        try:
            rating = int(request.data.get('rating', 0))
            if 1 <= rating <= 5:  # Validate rating is between 1 and 5
                app.rating = rating
                app.save()
                return Response({
                    'status': 'success',
                    'message': 'Rating updated successfully',
                    'rating': rating
                })
            return Response({
                'status': 'error',
                'message': 'Rating must be between 1 and 5'
            }, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({
                'status': 'error',
                'message': 'Invalid rating value'
            }, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        """Create a new application."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set initial status
        serializer.validated_data['status'] = 'Stopped'
        
        # Create the app
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """Perform the creation of the application."""
        serializer.save(status='Stopped')
