"""
Twitter API v2 Integration Module
Handles authentication, tweet fetching, and data preprocessing for the Anti-India Detection System.
"""

import tweepy
import os
import re
import time
import logging
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterAPIClient:
    """
    Secure Twitter API v2 client with rate limiting and error handling.
    """
    
    def __init__(self):
        """Initialize Twitter API client with secure authentication."""
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        # Rate limiting configuration
        self.rate_limit_buffer = int(os.getenv('TWITTER_RATE_LIMIT_BUFFER', 5))
        self.max_tweets_per_request = int(os.getenv('MAX_TWEETS_PER_REQUEST', 100))
        self.default_tweet_count = int(os.getenv('DEFAULT_TWEET_COUNT', 50))
        
        # Validate credentials
        if not self.bearer_token:
            raise ValueError("Twitter Bearer Token not found. Please set TWITTER_BEARER_TOKEN in .env file")
        
        # Initialize Tweepy client
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True
        )
        
        logger.info("Twitter API client initialized successfully")
    
    def validate_connection(self) -> bool:
        """
        Test Twitter API connection.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to get user info as a connection test
            me = self.client.get_me()
            if me.data:
                logger.info(f"Twitter API connection validated for user: {me.data.username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Twitter API connection failed: {str(e)}")
            return False
    
    def fetch_tweets_by_hashtag(
        self, 
        hashtags: List[str], 
        count: Optional[int] = None,
        exclude_retweets: bool = True,
        lang: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch tweets containing specific hashtags.
        
        Args:
            hashtags: List of hashtags to search for (without #)
            count: Number of tweets to fetch (default from env)
            exclude_retweets: Whether to exclude retweets
            lang: Language code (e.g., 'en', 'hi') or None for all languages
            
        Returns:
            List of tweet dictionaries with metadata
        """
        if count is None:
            count = self.default_tweet_count
        
        # Ensure minimum count for Twitter API
        count = max(10, count)
            
        # Construct search query
        hashtag_query = " OR ".join([f"#{tag}" for tag in hashtags])
        query = hashtag_query
        
        if exclude_retweets:
            query += " -is:retweet"
            
        if lang:
            query += f" lang:{lang}"
            
        logger.info(f"Searching tweets with query: {query}")
        
        try:
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'lang', 'context_annotations'],
                user_fields=['username', 'name', 'verified'],
                expansions=['author_id'],
                max_results=min(count, self.max_tweets_per_request)
            ).flatten(limit=count)
            
            processed_tweets = []
            users_dict = {}
            
            # Process tweets and build user lookup
            tweet_list = list(tweets)
            if hasattr(tweet_list, 'includes') and 'users' in tweet_list.includes:
                users_dict = {user.id: user for user in tweet_list.includes['users']}
            
            for tweet in tweet_list:
                user = users_dict.get(tweet.author_id)
                username = user.username if user else f"user_{tweet.author_id}"
                
                processed_tweets.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'username': f"@{username}",
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'lang': tweet.lang,
                    'retweet_count': tweet.public_metrics.get('retweet_count', 0) if tweet.public_metrics else 0,
                    'like_count': tweet.public_metrics.get('like_count', 0) if tweet.public_metrics else 0,
                    'reply_count': tweet.public_metrics.get('reply_count', 0) if tweet.public_metrics else 0,
                    'quote_count': tweet.public_metrics.get('quote_count', 0) if tweet.public_metrics else 0,
                    'author_verified': user.verified if user else False
                })
            
            logger.info(f"Successfully fetched {len(processed_tweets)} tweets")
            return processed_tweets
            
        except Exception as e:
            logger.error(f"Error fetching tweets: {str(e)}")
            return []
    
    def fetch_tweets_by_keywords(
        self, 
        keywords: List[str], 
        count: Optional[int] = None,
        exclude_retweets: bool = True,
        lang: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch tweets containing specific keywords.
        
        Args:
            keywords: List of keywords to search for
            count: Number of tweets to fetch (default from env)
            exclude_retweets: Whether to exclude retweets
            lang: Language code (e.g., 'en', 'hi') or None for all languages
            
        Returns:
            List of tweet dictionaries with metadata
        """
        if count is None:
            count = self.default_tweet_count
        
        # Ensure minimum count for Twitter API
        count = max(10, count)
            
        # Construct search query - wrap phrases in quotes for exact match
        keyword_query = " OR ".join([f'"{keyword}"' for keyword in keywords])
        query = keyword_query
        
        if exclude_retweets:
            query += " -is:retweet"
            
        if lang:
            query += f" lang:{lang}"
            
        logger.info(f"Searching tweets with query: {query}")
        
        try:
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'lang', 'context_annotations'],
                user_fields=['username', 'name', 'verified'],
                expansions=['author_id'],
                max_results=min(count, self.max_tweets_per_request)
            ).flatten(limit=count)
            
            processed_tweets = []
            users_dict = {}
            
            # Process tweets and build user lookup
            tweet_list = list(tweets)
            if hasattr(tweet_list, 'includes') and 'users' in tweet_list.includes:
                users_dict = {user.id: user for user in tweet_list.includes['users']}
            
            for tweet in tweet_list:
                user = users_dict.get(tweet.author_id)
                username = user.username if user else f"user_{tweet.author_id}"
                
                processed_tweets.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'username': f"@{username}",
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'lang': tweet.lang,
                    'retweet_count': tweet.public_metrics.get('retweet_count', 0) if tweet.public_metrics else 0,
                    'like_count': tweet.public_metrics.get('like_count', 0) if tweet.public_metrics else 0,
                    'reply_count': tweet.public_metrics.get('reply_count', 0) if tweet.public_metrics else 0,
                    'quote_count': tweet.public_metrics.get('quote_count', 0) if tweet.public_metrics else 0,
                    'author_verified': user.verified if user else False
                })
            
            logger.info(f"Successfully fetched {len(processed_tweets)} tweets")
            return processed_tweets
            
        except Exception as e:
            logger.error(f"Error fetching tweets: {str(e)}")
            return []


class TweetPreprocessor:
    """
    Utility class for cleaning and preprocessing tweets for ML analysis.
    """
    
    @staticmethod
    def clean_tweet_text(text: str) -> str:
        """
        Clean tweet text for analysis by removing URLs, mentions, and extra whitespace.
        
        Args:
            text: Raw tweet text
            
        Returns:
            Cleaned text suitable for ML analysis
        """
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove @mentions but keep the rest of the text
        text = re.sub(r'@\w+', '', text)
        
        # Remove hashtags but keep the text (optional - you might want to keep hashtags)
        # text = re.sub(r'#\w+', '', text)
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """
        Extract hashtags from tweet text.
        
        Args:
            text: Tweet text
            
        Returns:
            List of hashtags (without #)
        """
        hashtags = re.findall(r'#(\w+)', text)
        return [tag.lower() for tag in hashtags]
    
    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """
        Extract user mentions from tweet text.
        
        Args:
            text: Tweet text
            
        Returns:
            List of usernames (without @)
        """
        mentions = re.findall(r'@(\w+)', text)
        return [mention.lower() for mention in mentions]
    
    @staticmethod
    def preprocess_for_analysis(tweet_data: Dict) -> Dict:
        """
        Preprocess tweet data for analysis pipeline.
        
        Args:
            tweet_data: Raw tweet dictionary
            
        Returns:
            Preprocessed tweet dictionary with additional fields
        """
        original_text = tweet_data.get('text', '')
        cleaned_text = TweetPreprocessor.clean_tweet_text(original_text)
        
        return {
            **tweet_data,
            'original_text': original_text,
            'cleaned_text': cleaned_text,
            'hashtags': TweetPreprocessor.extract_hashtags(original_text),
            'mentions': TweetPreprocessor.extract_mentions(original_text),
            'text_length': len(original_text),
            'cleaned_text_length': len(cleaned_text),
            'has_urls': bool(re.search(r'http[s]?://', original_text)),
            'mention_count': len(TweetPreprocessor.extract_mentions(original_text)),
            'hashtag_count': len(TweetPreprocessor.extract_hashtags(original_text))
        }


def get_twitter_client() -> Optional[TwitterAPIClient]:
    """
    Factory function to create and validate Twitter API client.
    
    Returns:
        TwitterAPIClient instance if credentials are valid, None otherwise
    """
    try:
        client = TwitterAPIClient()
        if client.validate_connection():
            return client
        else:
            logger.error("Twitter API connection validation failed")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize Twitter client: {str(e)}")
        return None


# Example usage functions for common tasks
def fetch_india_related_tweets(count: int = 50) -> List[Dict]:
    """
    Fetch tweets related to India using common keywords and hashtags.
    
    Args:
        count: Number of tweets to fetch
        
    Returns:
        List of preprocessed tweet dictionaries
    """
    client = get_twitter_client()
    if not client:
        return []
    
    # Common India-related keywords
    keywords = [
        "India", "भारत", "ভারত", "بھارت",
        "Hindustan", "हिंदुस्तान", "ہندوستان"
    ]
    
    tweets = client.fetch_tweets_by_keywords(keywords, count=count)
    
    # Preprocess tweets
    preprocessed_tweets = []
    for tweet in tweets:
        processed = TweetPreprocessor.preprocess_for_analysis(tweet)
        preprocessed_tweets.append(processed)
    
    return preprocessed_tweets


def fetch_hashtag_tweets(hashtags: List[str], count: int = 50) -> List[Dict]:
    """
    Fetch tweets by specific hashtags and preprocess them.
    
    Args:
        hashtags: List of hashtags to search (without #)
        count: Number of tweets to fetch
        
    Returns:
        List of preprocessed tweet dictionaries
    """
    client = get_twitter_client()
    if not client:
        return []
    
    tweets = client.fetch_tweets_by_hashtag(hashtags, count=count)
    
    # Preprocess tweets
    preprocessed_tweets = []
    for tweet in tweets:
        processed = TweetPreprocessor.preprocess_for_analysis(tweet)
        preprocessed_tweets.append(processed)
    
    return preprocessed_tweets


def monitor_keywords_realtime(
    keywords: List[str], 
    analysis_callback,
    duration_minutes: int = 60
):
    """
    Monitor keywords in real-time and analyze tweets as they come in.
    
    Args:
        keywords: List of keywords to monitor
        analysis_callback: Function to call for each tweet analysis
        duration_minutes: How long to monitor (in minutes)
    """
    client = get_twitter_client()
    if not client:
        logger.error("Cannot start monitoring - Twitter client unavailable")
        return
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    logger.info(f"Starting keyword monitoring for {duration_minutes} minutes...")
    
    while datetime.now() < end_time:
        try:
            tweets = client.fetch_tweets_by_keywords(keywords, count=10)
            
            for tweet in tweets:
                processed_tweet = TweetPreprocessor.preprocess_for_analysis(tweet)
                analysis_callback(processed_tweet)
            
            # Sleep to respect rate limits
            time.sleep(client.rate_limit_buffer)
            
        except Exception as e:
            logger.error(f"Error during monitoring: {str(e)}")
            time.sleep(30)  # Wait longer on error
    
    logger.info("Keyword monitoring completed")


if __name__ == "__main__":
    # Test the integration
    print("Testing Twitter API integration...")
    
    client = get_twitter_client()
    if client:
        print("✅ Twitter API client created successfully")
        
        # Test fetching some India-related tweets
        test_tweets = fetch_india_related_tweets(count=10)
        print(f"✅ Fetched {len(test_tweets)} test tweets")
        
        if test_tweets:
            print("\nSample tweet:")
            sample = test_tweets[0]
            print(f"Username: {sample['username']}")
            print(f"Original: {sample['original_text'][:100]}...")
            print(f"Cleaned: {sample['cleaned_text'][:100]}...")
            print(f"Hashtags: {sample['hashtags']}")
    else:
        print("❌ Failed to create Twitter API client")
        print("Please check your .env file and Twitter API credentials")
