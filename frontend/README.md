# CalOmr Frontend

React-based frontend for CalOmr AI Question Solver with beautiful sky blue theme.

## 🚀 Quick Start

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
# Start the React development server (runs on port 3000)
npm start
```

Make sure the backend API is running on port 8000:
```bash
# In the main project directory
python api.py
```

### Production Build

```bash
npm run build
```

## 🎨 Features

- **Beautiful Sky Blue Theme**: Gradient backgrounds and smooth animations
- **Drag & Drop Upload**: Easy image upload with preview
- **Real-time Results**: See AI-generated answers with confidence scores
- **Statistics Dashboard**: Track usage and cache performance
- **Responsive Design**: Works on desktop and mobile
- **Answer Verification**: Optional double-check for accuracy

## 📁 Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── UploadArea.js       # Drag & drop file upload
│   │   ├── ResultDisplay.js    # Show answer and reasoning
│   │   └── Statistics.js       # Database statistics
│   ├── App.js                  # Main application
│   ├── App.css                 # Sky blue theme styles
│   ├── index.js                # React entry point
│   └── index.css               # Global styles
└── package.json
```

## 🎨 Theme Colors

- Primary: `#4a90e2` (Sky Blue)
- Secondary: `#87ceeb` (Light Sky Blue)
- Background: `#e0f7ff` to `#87ceeb` (Gradient)
- Accents: `#b3e5fc`

## 🔧 Configuration

The frontend connects to the backend API at `http://localhost:8000`. This is configured in `package.json`:

```json
"proxy": "http://localhost:8000"
```

To change the API URL for production, update the axios calls in components.

## 📱 Usage

1. **Upload**: Drag and drop or click to select a question image
2. **Verify** (Optional): Enable verification for higher accuracy
3. **Solve**: Click the solve button to get AI-powered answer
4. **Results**: View answer, confidence, reasoning, and statistics

## 🌟 Components

### UploadArea
- Drag and drop interface
- File type validation
- Image preview
- Click to browse

### ResultDisplay
- Large answer display
- Confidence meter with color coding
- Subject and topic information
- Full question and options display
- Detailed reasoning (collapsible)
- Source indicator (Cache vs AI)

### Statistics
- Total questions solved
- Cache hit rate
- Subject breakdown (Math, Physics, Chemistry)
- Auto-refresh every 30 seconds

## 🎯 API Endpoints

- `POST /solve` - Solve a question
  - Body: FormData with 'file' field
  - Query: `verify=true/false`
  
- `GET /stats` - Get statistics
  - Returns: Database statistics

- `GET /health` - Health check

## 💡 Tips

- Use clear, high-resolution images for best results
- First solve takes 2-3 seconds (AI processing)
- Repeat questions are instant (RAG cache)
- Enable verification for difficult questions

## 🐛 Troubleshooting

**"No response from server"**
- Ensure backend is running: `python api.py`
- Check port 8000 is available

**Image upload fails**
- Only JPG/PNG images supported
- Check file size (max ~10MB)

**Slow response**
- First run downloads AI models
- Check internet connection
- Groq API may have rate limits on free tier

## 🚀 Deployment

For production deployment:

1. Build the frontend:
```bash
npm run build
```

2. Serve the `build` folder with any static server

3. Update API URL in production environment

## 📄 License

MIT License - Same as main project
