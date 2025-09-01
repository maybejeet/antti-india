import streamlit as st
import requests
import pandas as pd
from functools import lru_cache
import time

st.set_page_config(page_title="Team CodeBlooded", layout="wide")

# Add performance optimization
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    with st.spinner("🚀 Loading Anti-India Detection System..."):
        time.sleep(0.5)  # Brief loading animation

st.title("🚀 Anti-India Detection System")

# Cache API status checks to avoid repeated calls
@st.cache_data(ttl=60)  # Cache for 60 seconds
def check_gemini_status():
    try:
        gemini_status = requests.get("http://127.0.0.1:8000/gemini-status", timeout=5)
        return gemini_status.json()
    except:
        return {"status": "error", "message": "Cannot connect to backend"}

@st.cache_data(ttl=60)  # Cache for 60 seconds
def check_twitter_status():
    try:
        status_res = requests.get("http://127.0.0.1:8000/twitter-status", timeout=5)
        return status_res.json()
    except:
        return {"status": "error", "message": "Cannot connect to backend"}

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["📝 Text", "🖼️ Image", "🎙️ Audio", "🎥 Video", "📊 Social Feed", "📡 Live Feed", "🐦 Twitter Live"]
)

# ---------------- TEXT ----------------
with tab1:
    txt = st.text_area("Enter text to analyze")
    if st.button("Analyze Text"):
        if not txt.strip():
            st.error("Please enter some text to analyze")
        else:
            try:
                res = requests.post("http://127.0.0.1:8000/analyze-text", json={"text": txt})
                st.json(res.json())
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend server")
                st.info("🛠️ Please start the backend server first: `python3 backend.py`")

# ---------------- IMAGE ----------------
with tab2:
    st.subheader("🖼️ Gemini AI Image Analysis")
    
    # Check Gemini API status with caching
    status_data = check_gemini_status()
    
    if status_data["status"] == "connected":
        st.success("✅ Gemini AI Vision API Connected")
    elif status_data["status"] == "error":
        st.error("❌ Cannot connect to backend")
    else:
        st.error(f"❌ Gemini API Status: {status_data['message']}")
        st.info("Please check your GEMINI_API_KEY in .env file")
    
    # Image upload
    f = st.file_uploader(
        "Upload an image for analysis", 
        type=["png", "jpg", "jpeg", "gif", "bmp"],
        help="Upload images containing text, flags, symbols, or any visual content related to India"
    )
    
    if f:
        # Display image
        st.image(f, use_column_width=True, caption=f"Analyzing: {f.name}")
        
        # Analyze button - always show when image is uploaded
        col1, col2 = st.columns([1, 4])
        with col1:
            analyze_btn = st.button("🔍 Analyze Image with Gemini AI", type="primary", key="analyze_image_btn")
        
        if analyze_btn:
            with st.spinner("Analyzing image with Gemini AI Vision..."):
                try:
                    f.seek(0)  # reset pointer before sending
                    res = requests.post(
                        "http://127.0.0.1:8000/analyze-image", 
                        files={"file": f},
                        timeout=60
                    )
                    
                    if res.status_code == 200:
                        result = res.json()
                        
                        # Display main result
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            classification = result.get('classification', result.get('label', 'Unknown'))
                            if classification == 'ANTI-INDIA':
                                st.error(f"🚨 {classification}")
                            elif classification == 'SUSPICIOUS':
                                st.warning(f"⚠️ {classification}")
                            else:
                                st.success(f"✅ {classification}")
                        
                        with col2:
                            toxicity = result.get('toxicity_percent', result.get('confidence_score', 0))
                            st.metric("Risk Score", f"{toxicity}%")
                        
                        with col3:
                            method = result.get('method', 'Unknown')
                            st.info(f"Method: {method}")
                        
                        # Show extracted text if available
                        if result.get('extracted_text'):
                            st.subheader("📝 Text Found in Image:")
                            st.text_area("Extracted Text:", result['extracted_text'], height=100)
                        
                        # Show visual elements detected
                        if result.get('visual_elements'):
                            st.subheader("👁️ Visual Elements Detected:")
                            for element in result['visual_elements']:
                                st.write(f"• {element}")
                        
                        # Show detailed reasoning
                        if result.get('reasoning'):
                            st.subheader("🧠 AI Analysis Reasoning:")
                            st.write(result['reasoning'])
                        
                        # Show risk factors if any
                        if result.get('risk_factors'):
                            st.subheader("⚠️ Risk Factors Identified:")
                            for factor in result['risk_factors']:
                                st.write(f"• {factor}")
                        
                        # Show language detected
                        if result.get('language_detected') and result['language_detected'] != 'unknown':
                            st.write(f"🌍 **Language Detected:** {result['language_detected']}")
                        
                        # Image info
                        if result.get('image_info'):
                            with st.expander("📊 Image Information"):
                                info = result['image_info']
                                st.write(f"**Format:** {info.get('format', 'Unknown')}")
                                st.write(f"**Size:** {info.get('width', 0)} x {info.get('height', 0)} pixels")
                                st.write(f"**File Size:** {info.get('file_size', 0):,} bytes")
                        
                        # Full JSON result (collapsible)
                        with st.expander("📊 Raw Analysis Data"):
                            st.json(result)
                    
                    else:
                        st.error(f"Error: {res.status_code} - {res.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏰ Analysis timed out. The image might be too large or complex.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Make sure the server is running.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # URL analysis option
    st.markdown("---")
    st.subheader("🌐 Analyze Image from URL")
    
    image_url = st.text_input(
        "Image URL:",
        placeholder="https://example.com/image.jpg",
        help="Enter a direct URL to an image file"
    )
    
    if image_url and st.button("🔍 Analyze URL Image"):
        with st.spinner("Downloading and analyzing image..."):
            try:
                res = requests.post(
                    "http://127.0.0.1:8000/analyze-image-url",
                    params={"image_url": image_url},
                    timeout=60
                )
                
                if res.status_code == 200:
                    result = res.json()
                    st.success("✅ Image analyzed successfully!")
                    
                    # Display results similar to file upload
                    classification = result.get('classification', result.get('label', 'Unknown'))
                    toxicity = result.get('toxicity_percent', result.get('confidence_score', 0))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Classification", classification)
                    with col2:
                        st.metric("Risk Score", f"{toxicity}%")
                    
                    if result.get('extracted_text'):
                        st.write(f"**Extracted Text:** {result['extracted_text']}")
                    
                    st.json(result)
                else:
                    st.error(f"Error: {res.status_code} - {res.text}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ---------------- AUDIO ----------------
with tab3:
    st.subheader("🎙️ Audio Analysis")
    st.write("Upload audio files to extract speech and analyze for anti-India content")
    
    a = st.file_uploader(
        "Upload an audio file", 
        type=["mp3", "wav", "m4a", "ogg"],
        help="Supported formats: MP3, WAV, M4A, OGG"
    )
    
    if a:
        # Display audio info
        st.audio(a, format='audio/mp3')
        st.write(f"**File:** {a.name}")
        st.write(f"**Size:** {len(a.getvalue()):,} bytes")
        
        # Analyze button
        col1, col2 = st.columns([1, 4])
        with col1:
            analyze_audio_btn = st.button("🎧 Analyze Audio", type="primary", key="analyze_audio_btn")
        
        if analyze_audio_btn:
            with st.spinner("Transcribing audio and analyzing content..."):
                try:
                    # Save audio file temporarily
                    with open("temp_audio.mp3", "wb") as out:
                        out.write(a.getvalue())
                    
                    # Send to backend for analysis
                    with open("temp_audio.mp3", "rb") as audio_file:
                        res = requests.post(
                            "http://127.0.0.1:8000/analyze-audio", 
                            files={"file": audio_file},
                            timeout=120
                        )
                    
                    if res.status_code == 200:
                        result = res.json()
                        
                        # Display main result
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            classification = result.get('label', 'Unknown')
                            if classification == 'ANTI-INDIA':
                                st.error(f"🚨 {classification}")
                            elif classification == 'SUSPICIOUS':
                                st.warning(f"⚠️ {classification}")
                            else:
                                st.success(f"✅ {classification}")
                        
                        with col2:
                            toxicity = result.get('toxicity_percent', 0)
                            st.metric("Risk Score", f"{toxicity}%")
                        
                        with col3:
                            method = result.get('method', 'Speech-to-Text + Analysis')
                            st.info(f"Method: {method}")
                        
                        # Show transcript if available
                        if result.get('transcript'):
                            st.subheader("📝 Audio Transcript:")
                            st.text_area("Transcribed Text:", result['transcript'], height=150)
                        
                        # Show analysis details
                        if result.get('matched_phrase'):
                            st.warning(f"**Matched Phrase:** {result['matched_phrase']}")
                        
                        # Full JSON result (collapsible)
                        with st.expander("📊 Raw Analysis Data"):
                            st.json(result)
                    
                    else:
                        st.error(f"Error: {res.status_code} - {res.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏰ Analysis timed out. The audio file might be too long or complex.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Make sure the server is running.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ---------------- VIDEO ----------------
with tab4:
    st.subheader("🎥 Video Analysis")
    st.write("Upload video files to extract audio, transcribe speech, and analyze for anti-India content")
    
    v = st.file_uploader(
        "Upload a video file", 
        type=["mp4", "avi", "mov", "mkv", "webm"],
        help="Supported formats: MP4, AVI, MOV, MKV, WEBM"
    )
    
    if v:
        # Display video info
        st.video(v)
        st.write(f"**File:** {v.name}")
        st.write(f"**Size:** {len(v.getvalue()):,} bytes")
        
        # Analyze button
        col1, col2 = st.columns([1, 4])
        with col1:
            analyze_video_btn = st.button("🎬 Analyze Video", type="primary", key="analyze_video_btn")
        
        if analyze_video_btn:
            with st.spinner("Extracting audio, transcribing speech, and analyzing content..."):
                try:
                    # Save video file temporarily
                    with open("temp_video.mp4", "wb") as out:
                        out.write(v.getvalue())
                    
                    # Send to backend for analysis
                    with open("temp_video.mp4", "rb") as video_file:
                        res = requests.post(
                            "http://127.0.0.1:8000/analyze-video", 
                            files={"file": video_file},
                            timeout=180  # 3 minutes timeout for video processing
                        )
                    
                    if res.status_code == 200:
                        result = res.json()
                        
                        # Display main result
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            classification = result.get('label', 'Unknown')
                            if classification == 'ANTI-INDIA':
                                st.error(f"🚨 {classification}")
                            elif classification == 'SUSPICIOUS':
                                st.warning(f"⚠️ {classification}")
                            else:
                                st.success(f"✅ {classification}")
                        
                        with col2:
                            toxicity = result.get('toxicity_percent', 0)
                            st.metric("Risk Score", f"{toxicity}%")
                        
                        with col3:
                            method = result.get('method', 'Video-to-Audio + Speech-to-Text + Analysis')
                            st.info(f"Method: {method}")
                        
                        # Show transcript if available
                        if result.get('transcript'):
                            st.subheader("📝 Video Audio Transcript:")
                            st.text_area("Transcribed Speech:", result['transcript'], height=150)
                        
                        # Show analysis details
                        if result.get('matched_phrase'):
                            st.warning(f"**Matched Phrase:** {result['matched_phrase']}")
                        
                        # Video processing info
                        st.info("🎥 **Processing:** Video → Audio Extraction → Speech Recognition → Text Analysis")
                        
                        # Full JSON result (collapsible)
                        with st.expander("📊 Raw Analysis Data"):
                            st.json(result)
                    
                    else:
                        st.error(f"Error: {res.status_code} - {res.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏰ Analysis timed out. The video file might be too long or complex.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Make sure the server is running.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Video analysis tips
        with st.expander("💡 Video Analysis Tips"):
            st.write("""
            **How Video Analysis Works:**
            1. 🎥 **Video Upload**: Your video file is processed
            2. 🎵 **Audio Extraction**: Audio track is extracted from the video
            3. 🎤 **Speech Recognition**: Audio is converted to text using Whisper AI
            4. 🔍 **Text Analysis**: Transcribed text is analyzed for anti-India content
            
            **Best Results:**
            - Clear audio with minimal background noise
            - Videos with spoken content in supported languages
            - File size under 100MB for faster processing
            
            **Supported Languages:** Hindi, English, Bengali, Urdu, and more
            """)

# ---------------- SOCIAL FEED ----------------
with tab5:
    st.subheader("Upload social feed CSV")
    sf = st.file_uploader("Choose CSV", type=["csv"])
    if sf:
        df = pd.read_csv(sf)
        st.dataframe(df)
        if st.button("Analyze Social Feed"):
            results = []
            for _, row in df.iterrows():
                res = requests.post("http://127.0.0.1:8000/analyze-text", json={"text": row["text"]})
                data = res.json()
                results.append({
                    "username": row.get("username", ""),
                    "text": row["text"],
                    "predicted": data["label"],
                    "toxicity": data["toxicity_percent"],
                    "method": data["method"]
                })
            st.dataframe(pd.DataFrame(results))

# ---------------- LIVE FEED ----------------
with tab6:
    st.subheader("Simulated Live Feed")
    lf = st.file_uploader("Choose Live Feed CSV", type=["csv"])
    if lf:
        df = pd.read_csv(lf)
        if "step" not in st.session_state:
            st.session_state.step = 1
        if st.button("Next Post"):
            st.session_state.step += 1
        live_df = df.head(st.session_state.step)
        results = []
        for _, row in live_df.iterrows():
            res = requests.post("http://127.0.0.1:8000/analyze-text", json={"text": row["text"]})
            data = res.json()
            results.append({
                "username": row.get("username", ""),
                "text": row["text"],
                "predicted": data["label"],
                "toxicity": data["toxicity_percent"],
                "method": data["method"]
            })
        st.dataframe(pd.DataFrame(results))

# ---------------- TWITTER LIVE FEED ----------------
with tab7:
    st.subheader("🐦 Twitter Live Feed Analysis")
    
    # Check Twitter API status with caching
    status_data = check_twitter_status()
    
    if status_data["status"] == "connected":
        st.success("✅ Twitter API Connected")
    elif status_data["status"] == "error":
        st.error("❌ Cannot connect to backend. Make sure the backend server is running.")
    else:
        st.error(f"❌ Twitter API Status: {status_data['message']}")
        st.info("Please check your .env file and Twitter API credentials")
    
    # Twitter search options
    search_type = st.selectbox(
        "Search Type",
        ["Hashtags", "Keywords", "India Trending"]
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if search_type == "Hashtags":
            hashtags_input = st.text_input(
                "Enter hashtags (comma-separated, without #)",
                placeholder="e.g., India, भारत, Pakistan"
            )
        elif search_type == "Keywords":
            keywords_input = st.text_input(
                "Enter keywords (comma-separated)",
                placeholder="e.g., India, भारत, Pakistan"
            )
    
    with col2:
        tweet_count = st.number_input(
            "Number of tweets",
            min_value=1,
            max_value=100,
            value=20,
            help="Number of tweets to fetch and analyze"
        )
        
        language_filter = st.selectbox(
            "Language Filter",
            ["All Languages", "English (en)", "Hindi (hi)", "Bengali (bn)", "Urdu (ur)"]
        )
    
    # Convert language selection to API format
    lang_code = None
    if language_filter != "All Languages":
        lang_code = language_filter.split("(")[1].split(")")[0]
    
    # Search and analyze button
    if st.button("🔍 Search & Analyze Tweets", type="primary"):
        with st.spinner("Fetching and analyzing tweets..."):
            try:
                if search_type == "Hashtags":
                    if not hashtags_input:
                        st.error("Please enter hashtags to search")
                    else:
                        hashtags = [tag.strip() for tag in hashtags_input.split(",")]
                        payload = {
                            "hashtags": hashtags,
                            "count": tweet_count,
                            "lang": lang_code
                        }
                        res = requests.post("http://127.0.0.1:8000/analyze-tweets-by-hashtag", json=payload)
                        
                elif search_type == "Keywords":
                    if not keywords_input:
                        st.error("Please enter keywords to search")
                    else:
                        keywords = [kw.strip() for kw in keywords_input.split(",")]
                        payload = {
                            "keywords": keywords,
                            "count": tweet_count,
                            "lang": lang_code
                        }
                        res = requests.post("http://127.0.0.1:8000/analyze-tweets-by-keywords", json=payload)
                        
                elif search_type == "India Trending":
                    res = requests.get(f"http://127.0.0.1:8000/fetch-india-trending?count={tweet_count}")
                    # For trending, we need to analyze the fetched tweets
                    if res.status_code == 200:
                        trending_data = res.json()
                        tweets = trending_data.get("tweets", [])
                        
                        analyzed_tweets = []
                        for tweet in tweets:
                            # Analyze each tweet
                            analysis_res = requests.post(
                                "http://127.0.0.1:8000/analyze-text", 
                                json={"text": tweet["cleaned_text"]}
                            )
                            analysis_data = analysis_res.json()
                            
                            analyzed_tweet = {
                                **tweet,
                                "analysis": analysis_data,
                                "risk_score": analysis_data["toxicity_percent"],
                                "classification": analysis_data["label"]
                            }
                            analyzed_tweets.append(analyzed_tweet)
                        
                        # Create mock response format
                        total_tweets = len(analyzed_tweets)
                        anti_india_count = sum(1 for t in analyzed_tweets if t["classification"] == "ANTI-INDIA")
                        suspicious_count = sum(1 for t in analyzed_tweets if t["classification"] == "SUSPICIOUS")
                        safe_count = sum(1 for t in analyzed_tweets if t["classification"] == "SAFE")
                        
                        mock_response = {
                            "analyzed_tweets": analyzed_tweets,
                            "summary": {
                                "total_tweets": total_tweets,
                                "anti_india": anti_india_count,
                                "suspicious": suspicious_count,
                                "safe": safe_count,
                                "anti_india_percentage": round((anti_india_count / total_tweets) * 100, 2) if total_tweets > 0 else 0,
                                "suspicious_percentage": round((suspicious_count / total_tweets) * 100, 2) if total_tweets > 0 else 0
                            }
                        }
                        res = type('Response', (), {'status_code': 200, 'json': lambda: mock_response})()
                
                if res.status_code == 200:
                    data = res.json()
                    
                    # Display summary statistics
                    if "summary" in data:
                        summary = data["summary"]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Tweets", summary["total_tweets"])
                        with col2:
                            st.metric("Anti-India", summary["anti_india"], f"{summary['anti_india_percentage']}%")
                        with col3:
                            st.metric("Suspicious", summary["suspicious"], f"{summary['suspicious_percentage']}%")
                        with col4:
                            st.metric("Safe", summary["safe"])
                        
                        st.markdown("---")
                    
                    # Display analyzed tweets
                    if "analyzed_tweets" in data and data["analyzed_tweets"]:
                        tweets = data["analyzed_tweets"]
                        
                        # Create display DataFrame
                        display_data = []
                        for tweet in tweets:
                            display_data.append({
                                "Username": tweet["username"],
                                "Text": tweet["original_text"][:100] + "..." if len(tweet["original_text"]) > 100 else tweet["original_text"],
                                "Classification": tweet["classification"],
                                "Risk Score": f"{tweet['risk_score']}%",
                                "Language": tweet.get("lang", "N/A"),
                                "Likes": tweet.get("like_count", 0),
                                "Retweets": tweet.get("retweet_count", 0),
                                "Verified": "✅" if tweet.get("author_verified", False) else "❌"
                            })
                        
                        # Color-code the dataframe
                        def highlight_classification(row):
                            if row["Classification"] == "ANTI-INDIA":
                                return ['background-color: #ffebee'] * len(row)
                            elif row["Classification"] == "SUSPICIOUS":
                                return ['background-color: #fff3e0'] * len(row)
                            else:
                                return ['background-color: #e8f5e8'] * len(row)
                        
                        df_display = pd.DataFrame(display_data)
                        st.dataframe(
                            df_display.style.apply(highlight_classification, axis=1),
                            use_container_width=True
                        )
                        
                        # Show detailed view for high-risk tweets
                        high_risk_tweets = [t for t in tweets if t["risk_score"] > 60]
                        if high_risk_tweets:
                            st.subheader("🚨 High Risk Tweets (Detailed View)")
                            for i, tweet in enumerate(high_risk_tweets[:5]):  # Show top 5
                                with st.expander(f"Risk Score: {tweet['risk_score']}% - {tweet['username']}"):
                                    st.write(f"**Original Text:** {tweet['original_text']}")
                                    st.write(f"**Cleaned Text:** {tweet['cleaned_text']}")
                                    st.write(f"**Classification:** {tweet['classification']}")
                                    st.write(f"**Analysis Method:** {tweet['analysis']['method']}")
                                    if "matched_phrase" in tweet['analysis']:
                                        st.write(f"**Matched Phrase:** {tweet['analysis']['matched_phrase']}")
                                    st.write(f"**Hashtags:** {', '.join(tweet.get('hashtags', []))}")
                                    st.write(f"**Mentions:** {', '.join(tweet.get('mentions', []))}")
                                    st.write(f"**Engagement:** {tweet.get('like_count', 0)} likes, {tweet.get('retweet_count', 0)} retweets")
                    
                    elif "tweets" in data:
                        # Handle non-analyzed tweet responses
                        tweets = data["tweets"]
                        st.info(f"Fetched {len(tweets)} tweets. Use the analyze endpoints for classification.")
                        st.dataframe(pd.DataFrame(tweets))
                    
                    else:
                        st.warning(data.get("message", "No tweets found"))
                
                else:
                    st.error(f"Error: {res.status_code} - {res.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure the backend server is running on port 8000.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Quick action buttons
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🇮🇳 Analyze India Trending"):
            with st.spinner("Fetching India trending tweets..."):
                try:
                    res = requests.get(f"http://127.0.0.1:8000/fetch-india-trending?count=20")
                    if res.status_code == 200:
                        st.success("✅ Fetched India trending tweets")
                        st.json(res.json())
                    else:
                        st.error(f"Error: {res.status_code}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("🔥 Check High-Risk Hashtags"):
            high_risk_hashtags = ["DestroyIndia", "IndiaFail", "AntiIndia"]
            with st.spinner("Analyzing high-risk hashtags..."):
                try:
                    payload = {"hashtags": high_risk_hashtags, "count": 15}
                    res = requests.post("http://127.0.0.1:8000/analyze-tweets-by-hashtag", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        if data["summary"]["total_tweets"] > 0:
                            st.warning(f"⚠️ Found {data['summary']['anti_india']} anti-India tweets")
                            st.json(data["summary"])
                        else:
                            st.success("✅ No concerning tweets found for high-risk hashtags")
                    else:
                        st.error(f"Error: {res.status_code}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col3:
        if st.button("📊 API Status"):
            try:
                res = requests.get("http://127.0.0.1:8000/twitter-status")
                status_data = res.json()
                if status_data["status"] == "connected":
                    st.success("✅ Twitter API is connected and ready")
                else:
                    st.error(f"❌ {status_data['message']}")
            except Exception as e:
                st.error(f"Error checking API status: {str(e)}")
