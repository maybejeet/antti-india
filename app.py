import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Team CodeBlooded", layout="wide")
st.title("🚀 Anti-India Detection System")

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["📝 Text", "🖼️ Image", "🎙️ Audio", "🎥 Video", "📊 Social Feed", "📡 Live Feed", "🐦 Twitter Live"]
)

# ---------------- TEXT ----------------
with tab1:
    txt = st.text_area("Enter text to analyze")
    if st.button("Analyze Text"):
        res = requests.post("http://127.0.0.1:8000/analyze-text", json={"text": txt})
        st.json(res.json())

# ---------------- IMAGE ----------------
with tab2:
    f = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if f:
        st.image(f, use_column_width=True)
        f.seek(0)  # reset pointer before sending
        res = requests.post("http://127.0.0.1:8000/analyze-image", files={"file": f})
        st.json(res.json())

# ---------------- AUDIO ----------------
with tab3:
    a = st.file_uploader("Upload an audio file", type=["mp3", "wav"])
    if a:
        with open("temp_audio.mp3", "wb") as out:
            out.write(a.read())
        res = requests.post("http://127.0.0.1:8000/analyze-audio", files={"file": open("temp_audio.mp3", "rb")})
        st.json(res.json())

# ---------------- VIDEO ----------------
with tab4:
    v = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])
    if v:
        st.video(v)
        with open("temp_video.mp4", "wb") as out:
            out.write(v.read())
        res = requests.post("http://127.0.0.1:8000/analyze-video", files={"file": open("temp_video.mp4", "rb")})
        st.json(res.json())

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
    
    # Check Twitter API status first
    try:
        status_res = requests.get("http://127.0.0.1:8000/twitter-status")
        status_data = status_res.json()
        
        if status_data["status"] == "connected":
            st.success("✅ Twitter API Connected")
        else:
            st.error(f"❌ Twitter API Status: {status_data['message']}")
            st.info("Please check your .env file and Twitter API credentials")
    except:
        st.error("❌ Cannot connect to backend. Make sure the backend server is running.")
    
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
