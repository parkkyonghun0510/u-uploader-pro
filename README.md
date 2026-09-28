<p align="center">
  <img src="branding/master/yt-uploader-lockup-dark.svg" alt="YouTube Uploader Pro" width="560">
</p>

<p align="center">
  <strong>Intelligent Automated YouTube Video Dispatch, Queue Management & Scheduling Engine</strong>
</p>

<p align="center">
  <a href="branding/BRAND_GUIDELINES.md">Brand Guidelines</a> •
  <a href="branding/presentation.html">Brand Presentation</a> •
  <a href="branding/concepts/preview.html">Test Matrix</a>
</p>

---

## ✨ Features

- **🎨 Modern Web Dashboard** - Beautiful dark-themed UI with real-time progress tracking
- **📊 Upload Queue** - Manage multiple uploads with priority-based scheduling
- **📈 Real-time Progress** - Live progress bars and charts via WebSocket
- **📋 Upload History** - Complete history of all uploads
- **👤 Profile Management** - Save and switch between upload profiles
- **⏰ Scheduled Uploads** - Schedule videos for future upload
- **🔄 Auto-Retry** - Automatic retry with exponential backoff
- **📱 Responsive Design** - Works on desktop, tablet, and mobile

## 🚀 Quick Start

### Installation

```bash
cd youtube_uploader_selenium-master
pip install -r requirements.txt
```

### Start Web Dashboard

```bash
python upload.py --web
# or
python upload.py --web --port 8080
```

Then open `http://localhost:5000` in your browser.

### CLI Mode

```bash
# Basic upload
python upload.py --video my_video.mp4

# With metadata and thumbnail
python upload.py --video my_video.mp4 --meta metadata.json --thumbnail thumb.png

# With Firefox profile
python upload.py --video my_video.mp4 --profile my_profile

# Show queue status
python upload.py --status
```

### Metadata JSON Format

```json
{
  "title": "My Awesome Video",
  "description": "Check out this amazing content!",
  "tags": ["tutorial", "programming", "python"],
  "schedule": "06/15/2024, 14:30",
  "playlist_title": "My Playlist"
}
```

## 📁 Project Structure

```
youtube_uploader_selenium-master/
├── upload.py                  # CLI entry point
├── app.py                     # Flask web application
├── run.py                     # Application server
├── requirements.txt           # Python dependencies
├── templates/
│   └── index.html             # Web dashboard template
├── static/
│   ├── css/
│   │   └── style.css          # Modern stylesheet
│   └── js/
│       └── app.js             # Frontend application
├── youtube_uploader_selenium/
│   ├── __init__.py            # Main package & enhanced uploader
│   ├── Constant.py            # YouTube constants
│   ├── models.py              # Data models (UploadJob, UploadStatus)
│   ├── config.py              # Configuration manager
│   ├── queue.py               # Upload queue manager
│   ├── legacy_uploader.py     # Original Selenium uploader
│   └── utils.py               # Utility functions
├── config/                    # Saved profiles & settings
├── queue/                     # Upload queue data
├── logs/                      # Server & upload logs
└── tests/                     # Test files
```

## 🎯 Web Dashboard Features

### Dashboard
- Real-time statistics (total uploaded, completed, active, failed)
- Progress chart visualization
- Recent activity feed

### Upload Page
- Drag & drop file selection
- Metadata JSON preview
- Schedule and priority settings
- Multi-file support

### Queue Management
- Filter by status (All, Pending, Uploading, Done, Failed)
- Cancel active uploads
- Retry failed uploads
- View job details with logs

### Profiles
- Save upload configurations
- Switch between profiles
- Edit and delete profiles

### Settings
- Theme selection (Dark/Light)
- Retry configuration
- Auto-login toggle
- Notification preferences

## 🔧 System Improvements

### Error Handling
- Automatic retry with exponential backoff
- Detailed error messages and logging
- Graceful degradation on failures

### Session Management
- Cookie persistence across sessions
- Firefox profile support
- Automatic reconnection

### Performance
- WebSocket-based real-time updates
- Efficient queue sorting by priority
- Background upload processing

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard |
| `/api/jobs` | GET | List all jobs |
| `/api/jobs` | POST | Create new upload |
| `/api/jobs/<id>` | GET | Get job details |
| `/api/jobs/<id>/cancel` | POST | Cancel job |
| `/api/jobs/<id>/retry` | POST | Retry job |
| `/api/config` | GET | Get settings |
| `/api/config` | POST | Save settings |
| `/api/profiles` | GET | List profiles |
| `/api/profiles` | POST | Create profile |
| `/api/profiles/<name>` | DELETE | Delete profile |
| `/api/history` | GET | Upload history |
| `/api/health` | GET | Health check |

## 🔌 WebSocket Events

- `connect` - Client connects
- `disconnect` - Client disconnects
- `request_jobs` - Request job list
- `jobs_update` - Broadcast job updates
- `upload_progress` - Real-time progress updates

## 📝 Dependencies

- **selenium_firefox** - Firefox WebDriver management
- **selenium < 4** - Browser automation
- **Flask 3.0** - Web framework
- **Flask-SocketIO** - Real-time communication
- **eventlet** - Async server
- **gunicorn** - Production WSGI server

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

## 📄 License

MIT License
