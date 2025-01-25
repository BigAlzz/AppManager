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
        app = self.get_object()
        try:
            # Create a temporary file to capture output early
            output_file = os.path.join(os.path.dirname(app.path), '_temp_output.txt')
            
            # Start with initial output
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

            # Allocate port for Django/Flask apps
            if app.type == 'script' and (app.is_django_app() or app.is_flask_app()):
                if not app.port:
                    if not app.allocate_port():
                        return Response({
                            'status': 'error',
                            'message': 'No available ports'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    with open(output_file, 'a', encoding='utf-8') as f:
                        f.write(f"Allocated port {app.port} for web application\n")

            # Get the command with port if available
            cmd = app.get_run_command()
            if not cmd:
                return Response({
                    'status': 'error',
                    'message': 'Failed to generate run command'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Start the process in a new terminal window
            try:
                # Modify the command to be more verbose and capture output
                if os.name == 'nt':
                    verbose_cmd = [
                        'echo Preparing to launch application...',
                        'echo Checking Python environment...',
                        'python --version',
                        'echo.',
                        'echo Loading required modules...',
                        'python -c "import sys; print(\\"Python path:\\", *sys.path, sep=\\"\\n  \\")"',
                        cmd.replace('cmd /k', '')  # Remove the cmd /k prefix as we'll add it back
                    ]
                    
                    # Join commands with && for sequential execution
                    cmd = f'cmd /k "{" && ".join(verbose_cmd)} > "{output_file}" 2>&1"'
                
                process = subprocess.Popen(cmd, shell=True)
                
                # Store the process ID in the app log
                AppLog.objects.create(
                    app=app,
                    action='launch',
                    details=f'Process started with PID: {process.pid}'
                )
                
                # Mark as running and save immediately
                app.status = 'Running'
                app.save()
                
                # Try to read initial output
                startup_output = []
                try:
                    if os.path.exists(output_file):
                        with open(output_file, 'r', encoding='utf-8') as f:
                            startup_output = f.readlines()
                except:
                    pass

                # For web apps, wait a bit and try to connect to verify the server is running
                if app.is_django_app() or app.is_flask_app():
                    import socket
                    max_retries = 10  # Try for up to 10 seconds
                    server_started = False
                    
                    for i in range(max_retries):
                        try:
                            sock = socket.create_connection(('127.0.0.1', app.port), timeout=1)
                            sock.close()
                            server_started = True
                            break
                        except (socket.timeout, ConnectionRefusedError):
                            time.sleep(1)
                            continue
                    
                    if not server_started:
                        app.release_port()
                        return Response({
                            'status': 'error',
                            'message': 'Failed to start server',
                            'command': cmd,
                            'output': startup_output
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                return Response({
                    'status': 'success',
                    'message': 'Application launched successfully',
                    'port': app.port,
                    'url': app.get_url(),
                    'app_status': app.status,
                    'app_name': app.name,
                    'startup_output': startup_output
                })

            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': f'Failed to start process: {str(e)}',
                    'command': cmd
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        app = self.get_object()
        killed_pids = []
        
        try:
            # Get the latest launch log to find the process ID
            latest_launch = app.logs.filter(action='launch').order_by('-timestamp').first()
            if latest_launch:
                pid_match = re.search(r'PID: (\d+)', latest_launch.details)
                if pid_match:
                    main_pid = int(pid_match.group(1))
                    try:
                        # Get the main process
                        process = psutil.Process(main_pid)
                        
                        # Get all child processes before killing the parent
                        children = process.children(recursive=True)
                        
                        # Kill all child processes first
                        for child in children:
                            try:
                                child.kill()
                                killed_pids.append(child.pid)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                        
                        # Kill the main process
                        process.kill()
                        killed_pids.append(main_pid)
                            
                        # Find and kill any PowerShell/CMD windows running our app
                        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                            try:
                                if proc.name().lower() in ['powershell.exe', 'cmd.exe']:
                                    cmdline = ' '.join(proc.cmdline()).lower()
                                    if app.path.lower() in cmdline:
                                        # Get children before killing
                                        shell_children = proc.children(recursive=True)
                                        for child in shell_children:
                                            try:
                                                child.kill()
                                                killed_pids.append(child.pid)
                                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                                pass
                                        proc.kill()
                                        killed_pids.append(proc.pid)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                            
                    except psutil.NoSuchProcess:
                        pass
            
            # Update app status
            app.status = 'Stopped'
            if app.port:
                app.release_port()
            app.save()
            
            # Log the stop action
            AppLog.objects.create(
                app=app,
                action='stop',
                details=f'Application stopped. Terminated PIDs: {killed_pids}'
            )
            
            return Response({
                'status': 'success',
                'message': 'Application stopped successfully',
                'terminated_pids': killed_pids
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error stopping application: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
