"""
Advanced Image Analysis Module using Google Gemini API
Provides comprehensive image understanding for anti-India content detection.
"""

import google.generativeai as genai
import os
import base64
import io
from PIL import Image
import requests
import json
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiImageAnalyzer:
    """
    Advanced image analyzer using Google Gemini API for comprehensive anti-India content detection.
    """
    
    def __init__(self):
        """Initialize Gemini API client."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
                self.model = None
        
        self.backend_url = "http://127.0.0.1:8000"
    
    def create_analysis_prompt(self) -> str:
        """
        Create a comprehensive prompt for anti-India content detection in images.
        """
        return """
Analyze this image for anti-India content and sentiment. Look for:

**VISUAL ELEMENTS:**
1. Text in any language (English, Hindi, Bengali, Urdu, etc.)
2. Symbols, flags, or imagery related to India
3. Political figures (Modi, Indian leaders)
4. Maps showing India or Kashmir
5. Religious symbols (Hindu, Sikh, Muslim, etc.)
6. Protest signs or banners
7. Memes or caricatures

**ANTI-INDIA INDICATORS:**
1. **Direct Attacks:** "Destroy India", "Down with India", burning Indian flag
2. **Government Criticism:** Calling Indian government "dictator", "fascist", "authoritarian"
3. **Religious Hatred:** Anti-Hindu, anti-Sikh content
4. **Separatist Content:** Kashmir independence, Khalistan promotion
5. **Historical Distortion:** False claims about Indian history
6. **Territorial Disputes:** Supporting Pakistan/China claims on Indian territory
7. **Cultural Mockery:** Ridiculing Indian customs, traditions
8. **Economic Attacks:** "India is poor", "India is backward"

**SUSPICIOUS INDICATORS:**
1. Subtle criticism of Indian policies
2. Negative portrayal of Indian culture
3. One-sided coverage of Indian issues
4. Promoting anti-India narratives

**SAFE CONTENT:**
1. Positive portrayal of India
2. Cultural appreciation
3. Tourism promotion
4. Educational content about India
5. Neutral news coverage

Please provide your analysis in this EXACT JSON format:
{
  "classification": "ANTI-INDIA" | "SUSPICIOUS" | "SAFE",
  "confidence_score": <0-100>,
  "extracted_text": "any text visible in the image",
  "visual_elements": ["list of key visual elements seen"],
  "reasoning": "detailed explanation of your classification",
  "risk_factors": ["specific anti-India elements if found"],
  "language_detected": "languages visible in the image"
}

Be thorough and consider context, implicit meanings, and cultural nuances.
"""
    
    def analyze_image_with_gemini(self, image_data: bytes) -> Dict:
        """
        Analyze image using Gemini API for comprehensive understanding.
        """
        if not self.model:
            return {
                "classification": "ERROR",
                "confidence_score": 0,
                "error": "Gemini API not available. Please set GEMINI_API_KEY in .env file"
            }
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Create the prompt
            prompt = self.create_analysis_prompt()
            
            # Generate content using Gemini
            response = self.model.generate_content([prompt, image])
            
            # Parse the response
            response_text = response.text.strip()
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    # If no JSON found, create a structured response
                    result = self._parse_text_response(response_text)
                
                # Validate and enhance the result
                result = self._validate_gemini_result(result)
                
                logger.info(f"Gemini analysis completed: {result.get('classification', 'UNKNOWN')}")
                return result
                
            except json.JSONDecodeError:
                # Fallback to text parsing
                return self._parse_text_response(response_text)
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {
                "classification": "ERROR",
                "confidence_score": 0,
                "error": f"Gemini API error: {str(e)}",
                "extracted_text": "",
                "visual_elements": [],
                "reasoning": "Failed to analyze image with Gemini API"
            }
    
    def _parse_text_response(self, response_text: str) -> Dict:
        """
        Parse non-JSON text response from Gemini.
        """
        # Default result
        result = {
            "classification": "SAFE",
            "confidence_score": 50,
            "extracted_text": "",
            "visual_elements": [],
            "reasoning": response_text[:500] + "..." if len(response_text) > 500 else response_text,
            "risk_factors": [],
            "language_detected": "unknown"
        }
        
        # Simple text analysis to determine classification
        text_lower = response_text.lower()
        
        anti_india_keywords = [
            "anti-india", "destroy india", "down with india", "dictator", "fascist",
            "burn", "hate", "against india", "enemy", "threat"
        ]
        
        suspicious_keywords = [
            "suspicious", "concerning", "negative", "criticism", "problem",
            "issue", "controversial"
        ]
        
        # Check for anti-India content
        if any(keyword in text_lower for keyword in anti_india_keywords):
            result["classification"] = "ANTI-INDIA"
            result["confidence_score"] = 85
        elif any(keyword in text_lower for keyword in suspicious_keywords):
            result["classification"] = "SUSPICIOUS"
            result["confidence_score"] = 70
        
        return result
    
    def _validate_gemini_result(self, result: Dict) -> Dict:
        """
        Validate and enhance Gemini API result.
        """
        # Ensure required fields exist
        required_fields = {
            "classification": "SAFE",
            "confidence_score": 50,
            "extracted_text": "",
            "visual_elements": [],
            "reasoning": "Analysis completed",
            "risk_factors": [],
            "language_detected": "unknown"
        }
        
        for field, default_value in required_fields.items():
            if field not in result:
                result[field] = default_value
        
        # Validate classification
        if result["classification"] not in ["ANTI-INDIA", "SUSPICIOUS", "SAFE"]:
            result["classification"] = "SAFE"
        
        # Ensure confidence score is valid
        if not isinstance(result["confidence_score"], (int, float)) or result["confidence_score"] < 0 or result["confidence_score"] > 100:
            result["confidence_score"] = 50
        
        # Convert confidence to toxicity percentage for consistency
        if result["classification"] == "ANTI-INDIA":
            result["toxicity_percent"] = max(85, result["confidence_score"])
        elif result["classification"] == "SUSPICIOUS":
            result["toxicity_percent"] = max(60, min(84, result["confidence_score"]))
        else:
            result["toxicity_percent"] = min(30, result["confidence_score"])
        
        # Add method information
        result["method"] = "Gemini AI Vision Analysis"
        result["label"] = result["classification"]
        
        return result
    
    def analyze_image_hybrid(self, image_data: bytes) -> Dict:
        """
        Hybrid analysis: Use Gemini for understanding + backend for text analysis.
        """
        # First, analyze with Gemini
        gemini_result = self.analyze_image_with_gemini(image_data)
        
        # If Gemini extracted text, also run it through our backend
        if gemini_result.get("extracted_text") and not gemini_result.get("error"):
            try:
                # Send extracted text to our backend for additional analysis
                response = requests.post(
                    f"{self.backend_url}/analyze-text",
                    json={"text": gemini_result["extracted_text"]},
                    timeout=10
                )
                
                if response.status_code == 200:
                    backend_result = response.json()
                    
                    # Combine results - use the more severe classification
                    severity_order = {"SAFE": 0, "SUSPICIOUS": 1, "ANTI-INDIA": 2}
                    
                    gemini_severity = severity_order.get(gemini_result["classification"], 0)
                    backend_severity = severity_order.get(backend_result["label"], 0)
                    
                    if backend_severity > gemini_severity:
                        gemini_result["classification"] = backend_result["label"]
                        gemini_result["label"] = backend_result["label"]
                        gemini_result["toxicity_percent"] = backend_result["toxicity_percent"]
                        gemini_result["backend_analysis"] = backend_result
                        gemini_result["method"] = "Gemini Vision + Rule-based Text Analysis"
                
            except Exception as e:
                logger.warning(f"Backend analysis failed: {e}")
                # Continue with Gemini result only
        
        return gemini_result
    
    def get_image_info(self, image_data: bytes) -> Dict:
        """
        Get basic image information.
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            return {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.size[0],
                "height": image.size[1],
                "file_size": len(image_data),
                "has_transparency": image.mode in ("RGBA", "LA") or "transparency" in image.info
            }
        except Exception as e:
            return {"error": str(e)}

# Convenience functions
def analyze_image_file(image_path: str) -> Dict:
    """
    Analyze an image file for anti-India content.
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        analyzer = GeminiImageAnalyzer()
        result = analyzer.analyze_image_hybrid(image_data)
        
        # Add image info
        image_info = analyzer.get_image_info(image_data)
        result["image_info"] = image_info
        
        return result
        
    except Exception as e:
        return {
            "classification": "ERROR",
            "confidence_score": 0,
            "error": str(e),
            "method": "File processing error"
        }

def analyze_image_url(image_url: str) -> Dict:
    """
    Analyze an image from URL for anti-India content.
    """
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        analyzer = GeminiImageAnalyzer()
        result = analyzer.analyze_image_hybrid(response.content)
        
        # Add image info
        image_info = analyzer.get_image_info(response.content)
        result["image_info"] = image_info
        result["source_url"] = image_url
        
        return result
        
    except Exception as e:
        return {
            "classification": "ERROR",
            "confidence_score": 0,
            "error": str(e),
            "method": "URL processing error"
        }

# Testing function
if __name__ == "__main__":
    print("🖼️ Gemini Image Analysis Test")
    
    # Check if API key is available
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("Please add your Gemini API key to the .env file:")
        print("GEMINI_API_KEY=your_api_key_here")
    else:
        print("✅ Gemini API key found")
        
        # Test with a simple image
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create test image
            img = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            # Add test text
            draw.text((50, 80), "Test image for analysis", fill='black')
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            
            # Analyze
            analyzer = GeminiImageAnalyzer()
            result = analyzer.analyze_image_with_gemini(img_bytes.getvalue())
            
            print(f"\n📊 Test Result:")
            print(f"Classification: {result.get('classification', 'Unknown')}")
            print(f"Confidence: {result.get('confidence_score', 0)}%")
            print(f"Method: {result.get('method', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
