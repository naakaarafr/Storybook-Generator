import os
import time
import threading
from datetime import datetime, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.callbacks.base import BaseCallbackHandler
import logging

# Environment variables - make sure to set these
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Rate limiting configuration for Gemini API
class RateLimiter:
    def __init__(self, max_requests_per_minute=15):
        """
        Initialize rate limiter for Gemini API
        
        Args:
            max_requests_per_minute (int): Maximum requests allowed per minute
                                         Default is 15 (conservative for free tier)
        """
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = threading.Lock()
        
    def wait_if_needed(self):
        """Wait if we've exceeded the rate limit"""
        with self.lock:
            now = datetime.now()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < timedelta(minutes=1)]
            
            if len(self.requests) >= self.max_requests:
                # Calculate how long to wait
                oldest_request = min(self.requests)
                wait_until = oldest_request + timedelta(minutes=1)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    print(f"🕐 Rate limit reached. Waiting {wait_seconds:.1f} seconds until next minute...")
                    time.sleep(wait_seconds + 1)  # Add 1 second buffer
                    
                    # Clean up old requests after waiting
                    now = datetime.now()
                    self.requests = [req_time for req_time in self.requests 
                                   if now - req_time < timedelta(minutes=1)]
            
            # Record this request
            self.requests.append(now)

# Global rate limiter instance
rate_limiter = RateLimiter(max_requests_per_minute=15)  # Conservative limit

class RateLimitCallback(BaseCallbackHandler):
    """Callback to handle rate limiting before each LLM call"""
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Called before each LLM request"""
        rate_limiter.wait_if_needed()

# Create LLM with proper configuration and rate limiting
def create_llm():
    """Create LLM with proper retry configuration and rate limiting"""
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.7,
        google_api_key=GOOGLE_API_KEY,
        max_retries=3,
        request_timeout=60,
        callbacks=[RateLimitCallback()],
        max_output_tokens=2048,
        top_p=0.9,
        top_k=40
    )

# Enhanced LLM wrapper that delegates to the underlying LLM
class GeminiLLMWrapper:
    def __init__(self):
        self.llm = create_llm()
        self.consecutive_failures = 0
        self.last_failure_time = None
        
    def __call__(self, *args, **kwargs):
        return self.invoke(*args, **kwargs)
    
    def __getattr__(self, name):
        """Delegate attribute access to the underlying LLM"""
        return getattr(self.llm, name)
    
    def invoke(self, *args, **kwargs):
        """Invoke with enhanced error handling and backoff"""
        max_retries = 5
        base_delay = 30  # Base delay in seconds
        
        for attempt in range(max_retries):
            try:
                # Check if we need to wait due to previous failures
                if self.consecutive_failures > 0 and self.last_failure_time:
                    time_since_failure = time.time() - self.last_failure_time
                    # Wait longer after consecutive failures
                    required_wait = base_delay * (2 ** (self.consecutive_failures - 1))
                    
                    if time_since_failure < required_wait:
                        wait_time = required_wait - time_since_failure
                        print(f"⏳ Waiting {wait_time:.1f} seconds due to previous failures...")
                        time.sleep(wait_time)
                
                # Apply rate limiting
                rate_limiter.wait_if_needed()
                
                # Make the actual call
                result = self.llm.invoke(*args, **kwargs)
                
                # Reset failure counter on success
                self.consecutive_failures = 0
                self.last_failure_time = None
                
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                if "429" in error_msg or "quota" in error_msg or "rate" in error_msg:
                    self.consecutive_failures += 1
                    self.last_failure_time = time.time()
                    
                    # Extract retry delay from error message if available
                    retry_delay = 60  # Default 1 minute
                    if "retry_delay" in error_msg:
                        try:
                            # Try to extract the retry delay from the error
                            import re
                            delay_match = re.search(r'seconds: (\d+)', error_msg)
                            if delay_match:
                                retry_delay = int(delay_match.group(1))
                        except:
                            pass
                    
                    wait_time = max(retry_delay, base_delay * (2 ** (attempt)))
                    
                    if attempt < max_retries - 1:
                        print(f"🚫 Rate limit exceeded (attempt {attempt + 1}/{max_retries})")
                        print(f"⏳ Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Max retries exceeded. Please check your API quota and billing.")
                        raise
                
                elif "timeout" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = 10 * (attempt + 1)
                        print(f"⏳ Timeout error. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise
                
                else:
                    # For other errors, re-raise immediately
                    raise
        
        raise Exception("Max retries exceeded for LLM calls")

# Create the LLM instance
llm = GeminiLLMWrapper()

# Hugging Face API Configuration
HF_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
HF_HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

# File paths
TEMPLATE_FILE = "template.md"
OUTPUT_MARKDOWN = "story.md"

# Logging configuration for better debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# API Usage tracking
class APIUsageTracker:
    def __init__(self):
        self.requests_today = 0
        self.last_reset = datetime.now().date()
        
    def track_request(self):
        """Track API request usage"""
        today = datetime.now().date()
        if today != self.last_reset:
            self.requests_today = 0
            self.last_reset = today
        
        self.requests_today += 1
        
        # Warn if approaching daily limits (assuming 1500 requests/day for free tier)
        if self.requests_today > 1200:
            print(f"⚠️  High API usage today: {self.requests_today} requests")
        
        return self.requests_today

# Global usage tracker
usage_tracker = APIUsageTracker()

def get_api_status():
    """Get current API usage status"""
    return {
        'requests_today': usage_tracker.requests_today,
        'rate_limit_requests': len(rate_limiter.requests),
        'max_requests_per_minute': rate_limiter.max_requests
    }

def print_api_status():
    """Print current API usage status"""
    status = get_api_status()
    print(f"📊 API Status:")
    print(f"   Daily requests: {status['requests_today']}")
    print(f"   Current minute: {status['rate_limit_requests']}/{status['max_requests_per_minute']}")

# Configuration validation
def validate_config():
    """Validate configuration and API keys"""
    issues = []
    
    if not GOOGLE_API_KEY:
        issues.append("GOOGLE_API_KEY environment variable not set")
    
    if not HUGGINGFACE_API_KEY:
        issues.append("HUGGINGFACE_API_KEY environment variable not set")
    
    if issues:
        print("❌ Configuration Issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ Configuration validated successfully")
    return True