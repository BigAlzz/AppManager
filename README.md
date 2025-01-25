# App Manager

A powerful Django-based application manager that helps you organize, discover, and run your Python applications from a single dashboard. App Manager automatically detects application types, manages virtual environments, and provides a modern, user-friendly interface for application management.

![App Manager Dashboard](docs/images/dashboard.png)

## Key Features

### Application Management
- **Smart Detection**: Automatically identifies Django, Flask, and Python script applications
- **Virtual Environment Integration**: Detects and utilizes project-specific virtual environments
- **Dependency Management**: Handles package installation and requirements.txt
- **Port Management**: Automatic port allocation for web applications
- **Process Control**: Clean process management with proper termination

### User Interface
- **Modern Dashboard**: Card-based interface with application details
- **Real-time Updates**: Live status and output monitoring
- **Quick Search**: Instant filtering of applications
- **Smart Sorting**: Organize by name, status, rating, or date
- **Star Ratings**: Rate and track favorite applications
- **Terminal Output**: View application logs and messages
- **Loading Screens**: Visual feedback during operations

### Application Support
- **Django Applications**: Automatic settings detection and port assignment
- **Flask Applications**: Proper host/port configuration
- **Python Scripts**: Terminal output capture and virtual env support
- **Auto-discovery**: Scan directories for Python applications

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Git (for version control)
- Virtual environment (recommended)

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

The application will be available at `http://127.0.0.1:8000/`

## Usage

### Adding Applications
- **Manual**: Add applications with custom names and descriptions
- **Auto-discover**: Scan directories to find Python applications automatically

### Managing Applications
- Launch/Stop applications with a single click
- Monitor application status and output
- Rate applications with the star system
- Filter and sort applications as needed

### Features in Detail
- Real-time status monitoring
- Terminal output capture
- Automatic port management
- Virtual environment integration
- Process cleanup on stop
- Modern card-based design
- Real-time search filtering
- Multiple sorting options
- Star rating system
- Terminal output display
- Loading screens with progress
- User guide support

## Documentation

For detailed information about using App Manager, please refer to the [Help Guide](HELP.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Django Framework
- Bootstrap for UI components
- Font Awesome for icons
- All contributors who have helped shape this project 