from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import App, AppLog
from django.http import JsonResponse
import json
import os
from pathlib import Path
import string
import psutil

def app_list(request):
    apps = App.objects.all().order_by('-created_at')
    return render(request, 'dashboard/app_list.html', {'apps': apps})

def app_add(request):
    if request.method == 'POST':
        try:
            data = request.POST
            app = App.objects.create(
                name=data['name'],
                path=data['path'],
                type=data['type'],
                description=data.get('description', ''),
                user_guide=data.get('user_guide', '')
            )
            messages.success(request, 'Application added successfully!')
            return redirect('app_list')
        except Exception as e:
            messages.error(request, f'Error adding application: {str(e)}')
    return render(request, 'dashboard/app_form.html', {'action': 'Add'})

def app_edit(request, pk):
    app = get_object_or_404(App, pk=pk)
    if request.method == 'POST':
        try:
            data = request.POST
            app.name = data['name']
            app.path = data['path']
            app.type = data['type']
            app.description = data.get('description', '')
            app.user_guide = data.get('user_guide', '')
            app.save()
            messages.success(request, 'Application updated successfully!')
            return redirect('app_list')
        except Exception as e:
            messages.error(request, f'Error updating application: {str(e)}')
    return render(request, 'dashboard/app_form.html', {'app': app, 'action': 'Edit'})

def app_delete(request, pk):
    app = get_object_or_404(App, pk=pk)
    if request.method == 'POST':
        try:
            app.delete()
            messages.success(request, 'Application deleted successfully!')
            return redirect('app_list')
        except Exception as e:
            messages.error(request, f'Error deleting application: {str(e)}')
    return render(request, 'dashboard/app_confirm_delete.html', {'app': app})

def list_directory(request):
    try:
        path = request.GET.get('path', '')
        
        # If no path is provided, list available drives on Windows
        if not path:
            drives = []
            for drive in string.ascii_uppercase:
                drive_path = f"{drive}:\\"
                if os.path.exists(drive_path):
                    try:
                        drive_type = psutil.disk_partitions()[0].fstype
                        drive_usage = psutil.disk_usage(drive_path)
                        total_gb = drive_usage.total / (1024**3)
                        free_gb = drive_usage.free / (1024**3)
                        drives.append({
                            'name': f"Drive {drive}",
                            'path': drive_path,
                            'type': 'directory',
                            'details': f"({drive_type}) {free_gb:.1f}GB free of {total_gb:.1f}GB"
                        })
                    except:
                        # If we can't get drive info, just show the drive
                        drives.append({
                            'name': f"Drive {drive}",
                            'path': drive_path,
                            'type': 'directory'
                        })
            
            return JsonResponse({
                'current_path': '',
                'parent_path': None,
                'items': drives,
                'is_root': True
            })
        
        # For regular directory listing
        path = Path(path)
        
        # Get parent directory (None if we're at a drive root)
        parent = str(path.parent) if len(str(path)) > 3 else None
        
        # List directories and files
        items = []
        try:
            for item in path.iterdir():
                try:
                    is_dir = item.is_dir()
                    stats = item.stat()
                    size_mb = stats.st_size / (1024 * 1024) if not is_dir else 0
                    modified = stats.st_mtime
                    
                    items.append({
                        'name': item.name,
                        'path': str(item),
                        'type': 'directory' if is_dir else 'file',
                        'details': f"{size_mb:.1f}MB" if not is_dir else None
                    })
                except (PermissionError, OSError):
                    continue
            
            # Sort items: directories first, then files, both alphabetically
            items.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
            
            return JsonResponse({
                'current_path': str(path),
                'parent_path': parent,
                'items': items,
                'is_root': False
            })
        except PermissionError:
            return JsonResponse({
                'error': 'Permission denied'
            }, status=403)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

def app_autodiscover(request):
    if request.method == 'POST':
        try:
            directory = request.POST.get('directory')
            if not directory:
                messages.error(request, 'Please provide a directory path')
                return redirect('app_autodiscover')

            # Store discovery logs in session
            request.session['discovery_logs'] = []
            def log_progress(message):
                logs = request.session.get('discovery_logs', [])
                logs.append(message)
                request.session['discovery_logs'] = logs
                request.session.modified = True

            discovered_apps = App.discover_apps(directory, progress_callback=log_progress)
            
            # Filter out apps that already exist (based on path)
            existing_paths = set(App.objects.values_list('path', flat=True))
            new_apps = [app for app in discovered_apps if app['path'] not in existing_paths]

            if not new_apps:
                messages.info(request, 'No new applications found in the specified directory')
                return render(request, 'dashboard/app_autodiscover.html', {
                    'logs': request.session.get('discovery_logs', [])
                })

            # Add new applications
            for app_info in new_apps:
                App.objects.create(**app_info)

            messages.success(request, f'Successfully added {len(new_apps)} new applications')
            
            # Pass the logs to the template
            return render(request, 'dashboard/app_autodiscover.html', {
                'logs': request.session.get('discovery_logs', []),
                'success': True
            })

        except Exception as e:
            messages.error(request, f'Error during autodiscovery: {str(e)}')
            return render(request, 'dashboard/app_autodiscover.html', {
                'logs': request.session.get('discovery_logs', []),
                'error': str(e)
            })

    return render(request, 'dashboard/app_autodiscover.html')

def cleanup_autodiscovered(request):
    if request.method == 'POST':
        try:
            minutes = int(request.POST.get('minutes', 5))
            count = App.cleanup_recent_apps(minutes=minutes)
            messages.success(request, f'Successfully removed {count} applications added in the last {minutes} minutes')
        except ValueError:
            messages.error(request, 'Invalid time range specified')
        except Exception as e:
            messages.error(request, f'Error cleaning up applications: {str(e)}')
    return redirect('app_list')
