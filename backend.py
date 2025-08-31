from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from transformers import pipeline
from rapidfuzz import fuzz
import uvicorn
import pytesseract
from PIL import Image
import io
import whisper
from moviepy.editor import VideoFileClip
from twitter_integration import (
    get_twitter_client, 
    fetch_india_related_tweets, 
    fetch_hashtag_tweets,
    TweetPreprocessor
)
from typing import List, Optional
import pandas as pd

# ---------- FastAPI App ----------
app = FastAPI()

# ---------- Input Models ----------
class TextInput(BaseModel):
    text: str

class TwitterHashtagSearch(BaseModel):
    hashtags: List[str]
    count: Optional[int] = 50
    lang: Optional[str] = None

class TwitterKeywordSearch(BaseModel):
    keywords: List[str]
    count: Optional[int] = 50
    lang: Optional[str] = None

# ---------- Load Models ----------
print("🔄 Loading models, please wait...")
text_classifier = pipeline(
    "text-classification",
    model="unitary/toxic-bert",
    tokenizer="unitary/toxic-bert"
)
whisper_model = whisper.load_model("base")  # speech-to-text

# ---------- Positive SAFE Phrases ----------
POSITIVE_PHRASES = [
    "بھارت زندہ باد", "जय हिन्द", "भारत महान है",
    "long live india", "jai hind", "vande mataram",
    "जय भारत", "bharat mata ki jai"
]

# ---------- Negative ANTI-INDIA Phrases ----------
ANTI_INDIA_PATTERNS = [
    # Hindi
    "भारत खत्म", "भारत का नाश", "भारत मुर्दाबाद", "भारत मिटा दो", "भारत को जला दो", "भारत को तोड़ दो",
    "भारत का विनाश", "भारत का अंत", "भारत खत्म हो", "भारत खत्म होगा", "भारत को खत्म करो", "भारत बर्बाद",
    "हिंदुस्तान खत्म", "हिंदुस्तान मुर्दाबाद", "हिंदुस्तान मिटा दो",

    # English
    "destroy india", "down with india", "death to india", "wipe out india", "kill india", "burn india",
    "remove india", "end india", "india must die", "india should perish", "india no more", "india must fall",

    # Bengali
    "ভারত ধ্বংস", "ভারতকে মুছে ফেল", "ভারত শেষ করো", "ভারতকে জ্বালাও", "ভারত নিপাত যাক", "ভারতকে ভেঙে দাও",

    # Urdu
    "بھارت ختم", "بھارت مردہ باد", "بھارت کو مٹا دو", "بھارت کو جلا دو", "بھارت کو توڑ دو", "بھارت نیست و نابود ہو",

    # Transliterations
    "bharat khatm", "bharat khatam", "bharat murdabad", "bharath murdabad", "indya murdabad", "india murdabaad",
    "indya khatm", "bharat khatm hoga", "bharat khatam karo", "bharat nasht", "bharat barbaad",
    "bharat ko khatam karo", "hindustan murdabad", "hindustan khatm"
]

# ---------- Suspicious NEGATIVE Words ----------
NEGATIVE_WORDS = [
    # English
    "bad", "worst", "evil", "dirty", "useless", "corrupt", "stupid",
    # Hindi
    "निकृष्ट", "बुरा", "घटिया", "नालायक",
    # Bengali
    "খারাপ", "নষ্ট", "অপদার্থ"
]

# ---------- Analyze Text ----------
@app.post("/analyze-text")
async def analyze_text(input: TextInput):
    text = input.text.strip().lower()

    # Positive whitelist check
    for phrase in POSITIVE_PHRASES:
        score = fuzz.partial_ratio(phrase.lower(), text)
        if score > 85:
            return {
                "label": "SAFE",
                "toxicity_percent": 0,
                "method": "Positive whitelist",
                "matched_phrase": phrase,
                "text": input.text
            }

    # Anti-India destructive patterns
    for phrase in ANTI_INDIA_PATTERNS:
        score = fuzz.partial_ratio(phrase.lower(), text)
        if score > 80:
            return {
                "label": "ANTI-INDIA",
                "toxicity_percent": 99,
                "method": "Rule-based destructive phrase",
                "matched_phrase": phrase,
                "match_score": score,
                "text": input.text
            }

    # Suspicious: India + negative word
    for word in NEGATIVE_WORDS:
        if ("india" in text or "भारत" in text or "ভারত" in text) and word in text:
            return {
                "label": "SUSPICIOUS",
                "toxicity_percent": 60,
                "method": f"Rule-based suspicious (matched '{word}')",
                "text": input.text
            }

    # ML fallback
    result = text_classifier(text)[0]
    score = round(float(result["score"]) * 100, 2)
    label_raw = result["label"].upper()

    if "TOXIC" in label_raw:
        if score > 70:
            label = "SUSPICIOUS"
        else:
            label = "SAFE"
    else:
        label = "SAFE"

    return {
        "label": label,
        "toxicity_percent": score,
        "method": "ML model",
        "text": input.text
    }

# ---------- Analyze Image ----------
@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    contents = await file.read()
    img = Image.open(io.BytesIO(contents))

    extracted_text = pytesseract.image_to_string(img, lang="eng+hin+ben")
    response = await analyze_text(TextInput(text=extracted_text))
    response["extracted_text"] = extracted_text
    return response

# ---------- Analyze Audio ----------
@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    with open("temp_audio.mp3", "wb") as f:
        f.write(await file.read())

    result = whisper_model.transcribe("temp_audio.mp3")
    transcript = result["text"]

    response = await analyze_text(TextInput(text=transcript))
    response["transcript"] = transcript
    return response

# ---------- Analyze Video ----------
@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    with open("temp_video.mp4", "wb") as f:
        f.write(await file.read())

    clip = VideoFileClip("temp_video.mp4")
    clip.audio.write_audiofile("temp_video_audio.mp3")

    result = whisper_model.transcribe("temp_video_audio.mp3")
    transcript = result["text"]

    response = await analyze_text(TextInput(text=transcript))
    response["transcript"] = transcript
    return response

# ---------- Twitter API Endpoints ----------
@app.post("/fetch-tweets-by-hashtag")
async def fetch_tweets_by_hashtag_endpoint(search: TwitterHashtagSearch):
    """
    Fetch tweets by hashtags and return them with metadata.
    """
    try:
        client = get_twitter_client()
        if not client:
            raise HTTPException(status_code=503, detail="Twitter API client unavailable. Check credentials.")
        
        tweets = client.fetch_tweets_by_hashtag(
            hashtags=search.hashtags,
            count=search.count,
            lang=search.lang
        )
        
        if not tweets:
            return {"tweets": [], "message": "No tweets found for the specified hashtags"}
        
        return {
            "tweets": tweets,
            "count": len(tweets),
            "hashtags_searched": search.hashtags,
            "language_filter": search.lang
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tweets: {str(e)}")

@app.post("/fetch-tweets-by-keywords")
async def fetch_tweets_by_keywords_endpoint(search: TwitterKeywordSearch):
    """
    Fetch tweets by keywords and return them with metadata.
    """
    try:
        client = get_twitter_client()
        if not client:
            raise HTTPException(status_code=503, detail="Twitter API client unavailable. Check credentials.")
        
        tweets = client.fetch_tweets_by_keywords(
            keywords=search.keywords,
            count=search.count,
            lang=search.lang
        )
        
        if not tweets:
            return {"tweets": [], "message": "No tweets found for the specified keywords"}
        
        return {
            "tweets": tweets,
            "count": len(tweets),
            "keywords_searched": search.keywords,
            "language_filter": search.lang
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tweets: {str(e)}")

@app.post("/analyze-tweets-by-hashtag")
async def analyze_tweets_by_hashtag_endpoint(search: TwitterHashtagSearch):
    """
    Fetch tweets by hashtags and analyze them for anti-India content.
    """
    try:
        client = get_twitter_client()
        if not client:
            raise HTTPException(status_code=503, detail="Twitter API client unavailable. Check credentials.")
        
        tweets = client.fetch_tweets_by_hashtag(
            hashtags=search.hashtags,
            count=search.count,
            lang=search.lang
        )
        
        if not tweets:
            return {"analyzed_tweets": [], "message": "No tweets found for analysis"}
        
        analyzed_tweets = []
        for tweet in tweets:
            # Preprocess the tweet
            processed_tweet = TweetPreprocessor.preprocess_for_analysis(tweet)
            
            # Analyze the cleaned text
            analysis_result = await analyze_text(TextInput(text=processed_tweet['cleaned_text']))
            
            # Combine tweet data with analysis results
            analyzed_tweet = {
                **processed_tweet,
                "analysis": analysis_result,
                "risk_score": analysis_result["toxicity_percent"],
                "classification": analysis_result["label"]
            }
            analyzed_tweets.append(analyzed_tweet)
        
        # Sort by risk score (highest first)
        analyzed_tweets.sort(key=lambda x: x["risk_score"], reverse=True)
        
        # Generate summary statistics
        total_tweets = len(analyzed_tweets)
        anti_india_count = sum(1 for t in analyzed_tweets if t["classification"] == "ANTI-INDIA")
        suspicious_count = sum(1 for t in analyzed_tweets if t["classification"] == "SUSPICIOUS")
        safe_count = sum(1 for t in analyzed_tweets if t["classification"] == "SAFE")
        
        return {
            "analyzed_tweets": analyzed_tweets,
            "summary": {
                "total_tweets": total_tweets,
                "anti_india": anti_india_count,
                "suspicious": suspicious_count,
                "safe": safe_count,
                "anti_india_percentage": round((anti_india_count / total_tweets) * 100, 2) if total_tweets > 0 else 0,
                "suspicious_percentage": round((suspicious_count / total_tweets) * 100, 2) if total_tweets > 0 else 0
            },
            "hashtags_searched": search.hashtags,
            "language_filter": search.lang
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing tweets: {str(e)}")

@app.post("/analyze-tweets-by-keywords")
async def analyze_tweets_by_keywords_endpoint(search: TwitterKeywordSearch):
    """
    Fetch tweets by keywords and analyze them for anti-India content.
    """
    try:
        client = get_twitter_client()
        if not client:
            raise HTTPException(status_code=503, detail="Twitter API client unavailable. Check credentials.")
        
        tweets = client.fetch_tweets_by_keywords(
            keywords=search.keywords,
            count=search.count,
            lang=search.lang
        )
        
        if not tweets:
            return {"analyzed_tweets": [], "message": "No tweets found for analysis"}
        
        analyzed_tweets = []
        for tweet in tweets:
            # Preprocess the tweet
            processed_tweet = TweetPreprocessor.preprocess_for_analysis(tweet)
            
            # Analyze the cleaned text
            analysis_result = await analyze_text(TextInput(text=processed_tweet['cleaned_text']))
            
            # Combine tweet data with analysis results
            analyzed_tweet = {
                **processed_tweet,
                "analysis": analysis_result,
                "risk_score": analysis_result["toxicity_percent"],
                "classification": analysis_result["label"]
            }
            analyzed_tweets.append(analyzed_tweet)
        
        # Sort by risk score (highest first)
        analyzed_tweets.sort(key=lambda x: x["risk_score"], reverse=True)
        
        # Generate summary statistics
        total_tweets = len(analyzed_tweets)
        anti_india_count = sum(1 for t in analyzed_tweets if t["classification"] == "ANTI-INDIA")
        suspicious_count = sum(1 for t in analyzed_tweets if t["classification"] == "SUSPICIOUS")
        safe_count = sum(1 for t in analyzed_tweets if t["classification"] == "SAFE")
        
        return {
            "analyzed_tweets": analyzed_tweets,
            "summary": {
                "total_tweets": total_tweets,
                "anti_india": anti_india_count,
                "suspicious": suspicious_count,
                "safe": safe_count,
                "anti_india_percentage": round((anti_india_count / total_tweets) * 100, 2) if total_tweets > 0 else 0,
                "suspicious_percentage": round((suspicious_count / total_tweets) * 100, 2) if total_tweets > 0 else 0
            },
            "keywords_searched": search.keywords,
            "language_filter": search.lang
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing tweets: {str(e)}")

@app.get("/fetch-india-trending")
async def fetch_india_trending_tweets(count: int = 50):
    """
    Fetch trending India-related tweets using predefined keywords.
    """
    try:
        tweets = fetch_india_related_tweets(count=count)
        
        if not tweets:
            return {"tweets": [], "message": "No India-related tweets found"}
        
        return {
            "tweets": tweets,
            "count": len(tweets),
            "search_type": "India-related trending"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching India trending tweets: {str(e)}")

@app.get("/twitter-status")
async def twitter_api_status():
    """
    Check Twitter API connection status.
    """
    try:
        client = get_twitter_client()
        if client and client.validate_connection():
            return {
                "status": "connected",
                "message": "Twitter API is available and authenticated"
            }
        else:
            return {
                "status": "disconnected",
                "message": "Twitter API connection failed or credentials invalid"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking Twitter API status: {str(e)}"
        }

# ---------- Root ----------
@app.get("/")
async def root():
    return {"message": "🚀 Anti-India Detection Backend Running"}

# ---------- Run ----------
if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
