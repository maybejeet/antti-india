# 🚀 Social Media Content Analyzer with Twitter Integration

A complete system for analyzing social media content (text, images, audio, video) and real-time Twitter feeds for anti-India sentiment detection.

## ✅ Quick Start

### Step 1: Start the Backend Server

Open a terminal and run:
```bash
./start_backend.sh
```

**Or manually:**
```bash
python3 backend.py
```

⏳ **Wait for:** "🚀 Anti-India Detection Backend Running" message
🌐 **Backend URL:** http://127.0.0.1:8000

### Step 2: Start the Frontend (in a NEW terminal window)

```bash
./start_frontend.sh
```

**Or manually:**
```bash
/Users/deepakkumar/Library/Python/3.9/bin/streamlit run app.py
```

🌐 **Frontend URL:** http://localhost:8501 (opens automatically)

## 🔧 Features Available

### 📝 Text Analysis
- Enter any text to analyze for anti-India sentiment
- Supports multiple languages (English, Hindi, Bengali, Urdu)

### 🖼️ Image Analysis
- Upload images with text (OCR analysis)
- Extracts and analyzes text from images

### 🎙️ Audio Analysis
- Upload MP3/WAV files
- Transcribes speech and analyzes content

### 🎥 Video Analysis
- Upload MP4/AVI/MOV files
- Extracts audio, transcribes, and analyzes

### 📊 Social Feed Analysis
- Upload CSV files with social media data
- Batch analysis of multiple posts

### 🐦 **NEW: Twitter Live Feed**
- **Real-time tweet analysis**
- Search by hashtags or keywords
- Language filtering
- Risk score ranking
- Summary statistics

## 🐦 Twitter Features

### Search Options:
1. **Hashtags**: `#India`, `#भारत`, etc.
2. **Keywords**: `India politics`, `भारत महान`, etc.
3. **India Trending**: Pre-configured India-related searches

### Language Support:
- All Languages
- English (en)
- Hindi (hi)
- Bengali (bn)
- Urdu (ur)

### Analysis Results:
- **ANTI-INDIA**: High-risk content (red)
- **SUSPICIOUS**: Medium-risk content (orange)
- **SAFE**: Low-risk content (green)

## 🔑 Twitter API Setup

1. Get credentials from [Twitter Developer Portal](https://developer.twitter.com/)
2. Your `.env` file is already configured ✅
3. Twitter API connection: **WORKING** ✅

## 📊 Sample Data

Test the system with provided sample files:
- `social_feed.csv` - Sample social media posts
- `live_feed.csv` - Sample live feed simulation

## 🛠️ Troubleshooting

### Backend won't start:
```bash
# Check if models are loading (wait 2-3 minutes)
python3 -c "from transformers import pipeline; print('Models ready!')"
```

### Frontend won't start:
```bash
# Try direct streamlit command
python3 -m streamlit run app.py
```

### Twitter API issues:
```bash
# Test Twitter connection
python3 twitter_integration.py
```

## 📋 System Requirements

- **Python**: 3.9+
- **Memory**: 4GB+ RAM (for ML models)
- **Storage**: 2GB+ free space
- **Internet**: Required for Twitter API and model downloads

## 🔒 Security

- ✅ API keys stored in `.env` (not in code)
- ✅ Rate limiting enabled
- ✅ Input validation
- ✅ Error handling

## 📈 Usage Tips

1. **First Run**: Backend startup takes 2-3 minutes (downloading models)
2. **Twitter Limits**: 450 requests per 15 minutes
3. **Best Results**: Use specific hashtags/keywords
4. **Language**: Hindi/Bengali detection works best with Unicode text

## 🆘 Need Help?

- Check console output for error messages
- Ensure both backend (port 8000) and frontend (port 8501) are running
- Twitter API rate limits reset every 15 minutes

---
**Version**: 2.0 with Twitter Integration  
**Team**: CodeBlooded
