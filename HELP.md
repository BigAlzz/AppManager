# AppManager Help Guide

## Getting Started

### Dashboard Overview
The main dashboard shows all your applications in card format. Each card displays:
- Application name and type
- Current status (Running/Stopped)
- Star rating
- Description
- Path location
- Action buttons (Launch/Stop, Edit, Delete)

### Quick Actions
- **Search**: Use the quick filter box to find applications by name or path
- **Sort**: Use the dropdown to sort applications by:
  - Name
  - Running status
  - Rating (highest/lowest)
  - Date added (newest/oldest)
- **Clean**: Remove recently added applications using the cleanup dropdown

## Managing Applications

### Adding Applications Manually
1. Click the "Add Application" button
2. Fill in the required fields:
   - Name: A descriptive name for the application
   - Path: Full path to the executable/script
   - Type: Select from Django, Flask, Script, or Executable
3. Optional fields:
   - Description: Brief description of the application
   - User Guide: Detailed instructions for using the application

### Auto-discovering Applications
1. Click "Autodiscover Apps"
2. Select the directory to scan
3. AppManager will:
   - Find Python applications
   - Detect application type
   - Locate virtual environments
   - Extract descriptions from README files
   - Add discovered applications to the dashboard

### Running Applications
1. Click the "Launch" button on an application card
2. The system will:
   - Activate the virtual environment (if available)
   - Allocate a port (for web applications)
   - Open a terminal window
   - Start the application
   - Open a browser (for web applications)
3. Monitor the startup progress in the loading screen

### Stopping Applications
1. Click the "Stop" button on a running application
2. The system will:
   - Close the browser window (for web applications)
   - Stop all related processes
   - Release the allocated port
   - Update the application status

## Application Types

### Django Applications
- Automatically assigned a free port
- Runs with proper settings module
- Opens browser to application URL
- Shows running port in status

### Flask Applications
- Configured with correct host/port
- Runs in development mode
- Opens browser to application URL
- Shows running port in status

### Python Scripts
- Runs in dedicated terminal window
- Shows script output
- Maintains terminal session
- Proper virtual environment activation

### Executable Files
- Launches in appropriate mode
- Handles command-line arguments
- Manages process lifecycle

## Features Guide

### Star Ratings
- Click on stars to rate applications
- Ratings persist across sessions
- Sort applications by rating
- Use ratings to organize favorites

### Quick Filter
- Type to instantly filter applications
- Matches against names and paths
- Case-insensitive search
- Real-time updates

### Terminal Output
- View application startup messages
- See error messages and warnings
- Monitor application status
- Debug startup issues

### User Guides
- Add detailed instructions per application
- Access guides through card buttons
- Format text for readability
- Include setup and usage details

## Troubleshooting

### Common Issues
1. **Application Won't Start**
   - Check if port is already in use
   - Verify virtual environment exists
   - Check file permissions
   - Review terminal output for errors

2. **Application Won't Stop**
   - Use task manager to verify processes
   - Check terminal window status
   - Try stopping again after a moment
   - Restart AppManager if needed

3. **Missing Dependencies**
   - Create/update requirements.txt
   - Activate correct virtual environment
   - Install required packages
   - Check Python version compatibility

### Getting Help
- Check the terminal output for error messages
- Review application logs
- Verify file paths and permissions
- Ensure virtual environments are properly set up 