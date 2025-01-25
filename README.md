# AppManager
Appmanager finds your apps and runs them from a single place.
# AppManager

A Django-based application manager that helps you organize, discover, and run your applications from a single dashboard.

## Features

- **Application Discovery**: Automatically scan directories to find Python applications, including Django and Flask apps
- **Smart Launch**: Automatically detects and runs applications in their correct environment
- **Virtual Environment Support**: Automatically detects and uses virtual environments for applications
- **Application Types Support**:
  - Django Applications
  - Flask Applications
  - Python Scripts
  - Executable Files
- **User Interface Features**:
  - Star Rating System
  - Quick Search Filter
  - Multiple Sorting Options (Name, Rating, Date, Running Status)
  - Real-time Status Updates
  - Terminal Output Display
  - User Guide Support
  - Application Cards with Description

## Installation

1. Clone the repository:
```bash
git clone https://github.com/BigAlzz/AppManager.git
cd AppManager
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
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

The application will be available at `http://127.0.0.1:8000/`

## Usage

1. **Adding Applications**:
   - Click "Add Application" button
   - Enter application details (name, path, type)
   - Optionally add description and user guide

2. **Auto-discovering Applications**:
   - Click "Autodiscover Apps" button
   - Select the directory to scan
   - AppManager will find and add applications automatically

3. **Managing Applications**:
   - Launch/Stop applications from the dashboard
   - Rate applications with the star system
   - Filter applications using the quick search
   - Sort applications by various criteria
   - View application status and terminal output

4. **Application Types**:
   - Django apps will run on automatically assigned ports
   - Flask apps will run with proper host/port configuration
   - Python scripts will run in their own terminal
   - All apps run in their respective virtual environments if available

## Features in Detail

### Smart Application Discovery
- Scans directories for Python applications
- Detects application type (Django, Flask, Script)
- Finds and uses virtual environments
- Extracts descriptions from README files

### Application Management
- Real-time status monitoring
- Terminal output capture
- Automatic port management
- Virtual environment integration
- Process cleanup on stop

### User Interface
- Modern card-based design
- Real-time search filtering
- Multiple sorting options
- Star rating system
- Terminal output display
- Loading screens with progress
- User guide modal

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
