# Twitter API Integration Setup Guide

## Overview
This guide will help you integrate Twitter API v2 with your Social Media Content Analyzer to fetch and analyze real-time tweets for anti-India content detection.

## Prerequisites
1. Twitter Developer Account
2. Twitter API v2 Bearer Token (minimum required)
3. Python environment with the updated requirements

## Step 1: Get Twitter API Credentials

### Option A: Bearer Token Only (Recommended for beginners)
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app or use existing app
3. Navigate to "Keys and Tokens"
4. Generate/copy your **Bearer Token**

### Option B: Full OAuth (For advanced features)
1. Follow Option A to get Bearer Token
2. Also generate:
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret

## Step 2: Configure Environment Variables

1. Copy the template file:
```bash
cp .env.template .env
```

2. Edit `.env` file with your credentials:
```bash
# Minimum required (Bearer Token)
TWITTER_BEARER_TOKEN=your_actual_bearer_token_here

# Optional (for full OAuth)
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# Rate limiting (optional)
TWITTER_RATE_LIMIT_BUFFER=5
MAX_TWEETS_PER_REQUEST=100
DEFAULT_TWEET_COUNT=50
```

⚠️ **Security Note**: Never commit the `.env` file to version control!

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Test the Integration

Test the Twitter integration:
```bash
python twitter_integration.py
```

You should see:
```
✅ Twitter API client created successfully
✅ Fetched X test tweets
```

## Step 5: Start the Application

1. Start the backend server:
```bash
python backend.py
```

2. In a new terminal, start the frontend:
```bash
streamlit run app.py
```

3. Navigate to the "🐦 Twitter Live" tab in your browser

## New Features Added

### Backend API Endpoints

1. **`/twitter-status`** - Check API connection status
2. **`/fetch-tweets-by-hashtag`** - Fetch tweets by hashtags
3. **`/fetch-tweets-by-keywords`** - Fetch tweets by keywords  
4. **`/analyze-tweets-by-hashtag`** - Fetch and analyze tweets by hashtags
5. **`/analyze-tweets-by-keywords`** - Fetch and analyze tweets by keywords
6. **`/fetch-india-trending`** - Fetch trending India-related tweets

### Frontend Features

1. **Twitter Live Feed Tab** - Real-time tweet analysis
2. **Search Options** - Hashtags, Keywords, or India Trending
3. **Language Filtering** - Filter by English, Hindi, Bengali, Urdu
4. **Summary Statistics** - Count of Anti-India, Suspicious, and Safe tweets
5. **Risk Score Ranking** - Tweets sorted by toxicity score
6. **Detailed View** - Expandable details for high-risk tweets
7. **Quick Actions** - Pre-configured searches for common use cases

### Security Best Practices Implemented

✅ **Environment Variables**: API credentials stored in `.env` file  
✅ **No Hardcoded Secrets**: All sensitive data loaded from environment  
✅ **Rate Limiting**: Built-in rate limiting to respect Twitter API limits  
✅ **Error Handling**: Comprehensive error handling for API failures  
✅ **Connection Validation**: API status checking before operations  
✅ **Input Validation**: Proper validation of user inputs  

## Usage Examples

### Analyze Tweets by Hashtag
```python
# API call example
payload = {
    "hashtags": ["India", "भारत"],
    "count": 50,
    "lang": "en"
}
response = requests.post("http://127.0.0.1:8000/analyze-tweets-by-hashtag", json=payload)
```

### Analyze Tweets by Keywords
```python
# API call example
payload = {
    "keywords": ["India politics", "भारत"],
    "count": 30,
    "lang": None  # All languages
}
response = requests.post("http://127.0.0.1:8000/analyze-tweets-by-keywords", json=payload)
```

### Response Format
```json
{
    "analyzed_tweets": [
        {
            "id": "tweet_id",
            "username": "@user123",
            "original_text": "Original tweet text...",
            "cleaned_text": "Cleaned text for analysis...",
            "classification": "ANTI-INDIA|SUSPICIOUS|SAFE",
            "risk_score": 85,
            "analysis": {
                "label": "ANTI-INDIA",
                "toxicity_percent": 85,
                "method": "Rule-based destructive phrase"
            },
            "hashtags": ["india"],
            "mentions": ["user456"],
            "like_count": 10,
            "retweet_count": 5
        }
    ],
    "summary": {
        "total_tweets": 50,
        "anti_india": 5,
        "suspicious": 10,
        "safe": 35,
        "anti_india_percentage": 10.0,
        "suspicious_percentage": 20.0
    }
}
```

## Integration with ML Pipeline

The Twitter integration automatically connects to your existing ML pipeline:

1. **Text Preprocessing**: Tweets are cleaned (URLs, mentions removed)
2. **Rule-based Analysis**: Checked against anti-India patterns
3. **ML Classification**: Uses your existing toxic-bert model
4. **Risk Scoring**: Combines rule-based and ML scores
5. **Ranking**: Tweets sorted by risk level

## Rate Limiting & Best Practices

- Twitter API v2 has rate limits (450 requests per 15 minutes for search)
- The integration respects these limits with `wait_on_rate_limit=True`
- Configure `TWITTER_RATE_LIMIT_BUFFER` for additional safety
- Use language filters to reduce noise in results
- Monitor API usage in Twitter Developer Dashboard

## Troubleshooting

### Common Issues

1. **"Twitter API client unavailable"**
   - Check your `.env` file exists and has valid credentials
   - Run `python twitter_integration.py` to test connection

2. **"Rate limit exceeded"**
   - Wait 15 minutes for rate limit reset
   - Reduce tweet count in requests
   - Increase `TWITTER_RATE_LIMIT_BUFFER`

3. **"No tweets found"**
   - Try broader keywords/hashtags
   - Remove language filters
   - Check if hashtags/keywords actually exist on Twitter

4. **Backend connection errors**
   - Ensure backend is running on port 8000
   - Check firewall settings
   - Verify FastAPI server is accessible

## Next Steps

1. **Database Integration**: Store fetched tweets in MongoDB/Postgres
2. **Real-time Monitoring**: Set up continuous monitoring of keywords
3. **Alert System**: Add notifications for high-risk content detection
4. **Analytics Dashboard**: Create visualizations for trend analysis
5. **Batch Processing**: Process large volumes of historical tweets

## API Limits & Costs

- **Twitter API v2 Essential (Free)**: 500K tweets/month
- **Basic ($100/month)**: 10M tweets/month
- **Pro ($5000/month)**: 50M tweets/month

Choose the plan based on your expected usage volume.
