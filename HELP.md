# App Manager Help Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Adding Applications](#adding-applications)
3. [Managing Applications](#managing-applications)
4. [Troubleshooting](#troubleshooting)
5. [FAQ](#faq)

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)
- Git (for version control)

### Installation
1. Clone the repository:
```bash
git clone https://github.com/BigAlzz/AppManager.git
cd AppManager
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the server:
```bash
python manage.py runserver
```

## Adding Applications

### Manual Addition
1. Click the "Add Application" button
2. Fill in the required fields:
   - Name: A descriptive name for your application
   - Path: Full path to the application directory
   - Type: Select the application type (Django/Flask/Python Script)
3. Optional fields:
   - Description: Brief description of the application
   - User Guide: Markdown-formatted guide for using the application
   - Star Rating: Rate the application (1-5 stars)

### Auto-discovery
1. Click "Autodiscover Apps"
2. Select the root directory to scan
3. The system will automatically:
   - Find Python applications
   - Detect application type
   - Locate virtual environments
   - Extract descriptions from README files

## Managing Applications

### Launching Applications
1. Click the "Launch" button on the application card
2. For web applications:
   - A port will be automatically assigned
   - The application will open in a new browser tab
3. For scripts:
   - Output will be displayed in the terminal window

### Stopping Applications
1. Click the "Stop" button on the application card
2. The system will:
   - Terminate all related processes
   - Free the assigned port
   - Update the application status

### Features
- **Quick Search**: Filter applications by name or description
- **Sorting**: Sort by name, rating, status, or creation date
- **Star Rating**: Rate your favorite applications
- **Status Monitoring**: Real-time status updates
- **Terminal Output**: View application logs and output

## Troubleshooting

### Common Issues

#### Application Won't Start
1. Check if the path is correct
2. Verify virtual environment exists
3. Ensure requirements.txt is present
4. Check application permissions

#### Port Already in Use
1. Stop any running instances
2. Check for other applications using the port
3. Restart the App Manager

#### Virtual Environment Issues
1. Ensure venv directory exists
2. Check Python version compatibility
3. Verify activation script permissions

### Error Messages

#### "Failed to launch application"
- Verify the application path exists
- Check if requirements.txt is present
- Ensure virtual environment is accessible

#### "Port {port} is already in use"
- Stop other applications using the port
- Check for background processes
- Try restarting the application

## FAQ

### Q: How does auto-discovery work?
A: The system scans directories for Python files, identifies application types based on file patterns (manage.py for Django, app.py for Flask), and detects virtual environments.

### Q: Can I manage non-Python applications?
A: Currently, the system supports Python applications (Django, Flask, scripts). Support for other types may be added in future versions.

### Q: How are ports assigned?
A: Ports are automatically assigned from a range of 9000-9999, ensuring no conflicts with other applications.

### Q: Can I customize the port range?
A: Yes, modify the port range in the application settings file.

### Q: How do I update application details?
A: Click the edit icon on the application card to modify name, description, or other details.

### Q: What happens to running applications when I close App Manager?
A: The system attempts to gracefully stop all running applications before shutting down. 