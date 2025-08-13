import os
import requests
import re
import time
import random
import sys
import threading
import json
from colorama import init, Fore, Style, Back
from queue import Queue
from datetime import datetime, timedelta
ID=input(' ID: ')
# Initialize colorama for colored output
init(autoreset=True)

# Proxy settings
PROXY_URL = "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
PROXY_FILE = "proxies.txt"

def fetch_proxies():
    """Fetch fresh proxies from the URL and save to file"""
    try:
        print(f"{Fore.YELLOW}🔄 Fetching fresh proxies...{Style.RESET_ALL}")
        response = requests.get(PROXY_URL, timeout=10)
        if response.status_code == 200:
            proxies = response.text.strip().split('\n')
            with open(PROXY_FILE, 'w') as f:
                for proxy in proxies:
                    if proxy.strip():
                        f.write(proxy.strip() + '\n')
            print(f"{Fore.GREEN}✅ Fetched {len(proxies)} proxies and saved to {PROXY_FILE}{Style.RESET_ALL}")
            return proxies
        else:
            print(f"{Fore.RED}❌ Failed to fetch proxies. Status code: {response.status_code}{Style.RESET_ALL}")
            return []
    except Exception as e:
        print(f"{Fore.RED}❌ Error fetching proxies: {str(e)}{Style.RESET_ALL}")
        return []

def load_proxies():
    """Load proxies from file or fetch if not available"""
    if os.path.exists(PROXY_FILE):
        try:
            with open(PROXY_FILE, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
            print(f"{Fore.GREEN}✅ Loaded {len(proxies)} proxies from {PROXY_FILE}{Style.RESET_ALL}")
            return proxies
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading proxies: {str(e)}{Style.RESET_ALL}")
    
    # If file doesn't exist or error, fetch fresh proxies
    return fetch_proxies()

# Auto-update Instagram API parameters
def update_api_params():
    """Fetch latest Instagram API parameters from remote source"""
    try:
        # Using a GitHub Gist as the remote source (you can replace with your own)
        response = requests.get("https://gist.githubusercontent.com/armaanofficial/abc123/raw/instagram_api_params.json", timeout=10)
        if response.status_code == 200:
            params = response.json()
            # Save to local config file
            with open('instagram_config.json', 'w') as f:
                json.dump(params, f, indent=4)
            print(f"{Fore.GREEN}✅ API parameters updated successfully!{Style.RESET_ALL}")
            return params
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️ Failed to update API parameters: {str(e)}{Style.RESET_ALL}")
    
    # Fallback to local config if available
    if os.path.exists('instagram_config.json'):
        try:
            with open('instagram_config.json', 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Default parameters if no config available
    return {
        "app_id": "936619743392459",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "x_ig_www_claim": "hmac.AR1qzeEVPBuPPsJxBMlPlU19lLRm0LG3bSnly_p3mz0aRW2P",
        "doc_id": "8481088891928753",
        "asbd_id_range": [30000, 79999],
        "ig_app_id_range": [1000, 3337],
        "instagram_ajax_range": [100, 3939],
        "last_updated": "2023-01-01"
    }

# Load API parameters
API_PARAMS = update_api_params()

class InstagramSession:
    def __init__(self, username, password, session_id, proxy=None):
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.session_id = session_id
        self.success_count = 0
        self.failure_count = 0
        self.csrftoken = None
        self.cookies = None
        self.lock = threading.Lock()
        self.is_logged_in = False
        self.api_params = API_PARAMS
        self.proxy = proxy
        self.last_request_time = 0
        self.min_delay = 2  # Minimum delay between requests in seconds
        
        # Set proxy if provided
        if proxy:
            self.session.proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            print(f"{Fore.CYAN}🌐 Session {session_id}: Using proxy {proxy}{Style.RESET_ALL}")
        
    def enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_delay:
            sleep_time = self.min_delay - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()
        
    def rotate_proxy(self):
        """Rotate to a new proxy if available"""
        if hasattr(self, 'reporter') and self.reporter.proxies:
            new_proxy = random.choice(self.reporter.proxies)
            self.session.proxies = {
                'http': f'http://{new_proxy}',
                'https': f'http://{new_proxy}'
            }
            self.proxy = new_proxy
            print(f"{Fore.CYAN}🔄 Session {self.session_id}: Rotated to new proxy {new_proxy}{Style.RESET_ALL}")
        
    def login(self):
        """Login to Instagram using username and password"""
        print(f"{Fore.YELLOW}🔄 Session {self.session_id}: Logging in as {self.username}...{Style.RESET_ALL}")
        
        try:
            # Get initial page to get CSRF token
            self.enforce_rate_limit()
            response = self.session.get("https://www.instagram.com/")
            csrf_match = re.search(r'"csrf_token":"(.*?)"', response.text)
            if not csrf_match:
                print(f"{Fore.RED}❌ Session {self.session_id}: Could not find CSRF token{Style.RESET_ALL}")
                return False
            csrf_token = csrf_match.group(1)
            
            # Prepare login data with updated encryption
            timestamp = int(time.time() * 1000)  # Use milliseconds
            login_data = {
                'username': self.username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{self.password}',
                'queryParams': '{}',
                'optIntoOneTap': 'false',
                'stopDeletion': 'false',
                'trustedDevice': 'false',
            }
            
            # Enhanced headers with required values
            headers = {
                'User-Agent': self.api_params.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
                'X-CSRFToken': csrf_token,
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://www.instagram.com/',
                'x-ig-app-id': self.api_params.get("app_id", "936619743392459"),
                'x-asbd-id': str(random.randint(*self.api_params.get("asbd_id_range", [30000, 79999]))),
                'x-ig-www-claim': self.api_params.get("x_ig_www_claim", "hmac.AR1qzeEVPBuPPsJxBMlPlU19lLRm0LG3bSnly_p3mz0aRW2P"),
                'x-instagram-ajax': str(random.randint(*self.api_params.get("instagram_ajax_range", [100, 3939]))),
            }
            
            # Send login request
            self.enforce_rate_limit()
            response = self.session.post(
                "https://www.instagram.com/accounts/login/ajax/",
                headers=headers,
                data=login_data
            )
            
            # Parse response
            try:
                response_json = response.json()
            except:
                response_text = response.text
                print(f"{Fore.RED}❌ Session {self.session_id}: Login failed - Invalid JSON response{Style.RESET_ALL}")
                print(f"{Fore.RED}Response: {response_text[:200]}...{Style.RESET_ALL}")
                return False
            
            # Check if authenticated
            if response_json.get('authenticated') or response_json.get('user'):
                print(f"{Fore.GREEN}✅ Session {self.session_id}: Login successful!{Style.RESET_ALL}")
                self.csrftoken = csrf_token
                self.cookies = self.session.cookies.get_dict()
                self.is_logged_in = True
                return True
            else:
                error_message = response_json.get('message', 'Unknown error')
                error_type = response_json.get('error_type', 'unknown')
                print(f"{Fore.RED}❌ Session {self.session_id}: Login failed! {error_type}: {error_message}{Style.RESET_ALL}")
                
                # Handle specific errors
                if "checkpoint_required" in response.text:
                    print(f"{Fore.YELLOW}⚠️ Session {self.session_id}: Checkpoint required. Please verify your account in the Instagram app.{Style.RESET_ALL}")
                elif "invalid_user" in response.text:
                    print(f"{Fore.YELLOW}⚠️ Session {self.session_id}: Invalid username or password.{Style.RESET_ALL}")
                elif "rate_limit" in response.text:
                    print(f"{Fore.YELLOW}⚠️ Session {self.session_id}: Rate limited. Try again later.{Style.RESET_ALL}")
                
                return False
        except Exception as e:
            print(f"{Fore.RED}❌ Session {self.session_id}: Login error: {str(e)}{Style.RESET_ALL}")
            return False
            
    def get_user_id(self, username):
        print(f"{Fore.YELLOW}🔍 Session {self.session_id}: Getting user ID for {username}...{Style.RESET_ALL}")
        url = f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}'
        headers = {'x-ig-app-id': self.api_params.get("app_id", "936619743392459")}
        
        try:
            self.enforce_rate_limit()
            response = self.session.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"{Fore.RED}❌ Session {self.session_id}: API error {response.status_code}{Style.RESET_ALL}")
                return None
                
            response_data = response.json()
            if 'data' not in response_data or 'user' not in response_data['data']:
                print(f"{Fore.RED}❌ Session {self.session_id}: Invalid user data format{Style.RESET_ALL}")
                return None
                
            user_data = response_data.get('data', {}).get('user', {})
            user_id = user_data.get('id')
            
            if not user_id:
                print(f"{Fore.RED}❌ Session {self.session_id}: User ID not found in response{Style.RESET_ALL}")
                return None
                
            print(f"{Fore.GREEN}✅ Session {self.session_id}: User ID found: {user_id}{Style.RESET_ALL}")
            return user_id
        except Exception as e:
            print(f'{Fore.RED}❌ Session {self.session_id}: Error getting user ID: {str(e)}{Style.RESET_ALL}')
            return None
        
    def get_story_id(self, user_id):
        print(f"{Fore.YELLOW}📷 Session {self.session_id}: Fetching story information...{Style.RESET_ALL}")
        headers = {
            'accept-language': 'en-US,en;q=0.9',
            'User-Agent': self.api_params.get("user_agent", "Mozilla/5.0 (Linux; Android 12; X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"),
            'x-asbd-id': str(random.randint(*self.api_params.get("asbd_id_range", [30000, 79999]))),
            'x-csrftoken': self.csrftoken,
            'x-ig-app-id': str(random.randint(*self.api_params.get("ig_app_id_range", [1000, 3337]))),
            'x-ig-www-claim': self.api_params.get("x_ig_www_claim", "hmac.AR1qzeEVPBuPPsJxBMlPlU19lLRm0LG3bSnly_p3mz0aRW2P"),
            'x-instagram-ajax': str(random.randint(*self.api_params.get("instagram_ajax_range", [100, 3939]))),
            'x-requested-with': 'XMLHttpRequest'
        }    	
        
        data = {
            'fb_api_req_friendly_name': 'PolarisStoriesV3ReelPageGalleryQuery',
            'variables': f'{{"initial_reel_id":"{user_id}","reel_ids":["{user_id}","65467266760"],"first":1}}',
            'server_timestamps': 'true',
            'doc_id': self.api_params.get("doc_id", "8481088891928753")
        }
        
        try:
            self.enforce_rate_limit()
            response = self.session.post(
                'https://www.instagram.com/graphql/query',
                cookies=self.cookies,
                headers=headers,
                data=data
            )   
            
            if response.status_code != 200:
                print(f"{Fore.RED}❌ Session {self.session_id}: API error {response.status_code}{Style.RESET_ALL}")
                return None
                
            response_text = response.text
            
            if 'organic_tracking_token' in response_text:
                pattern = r'"pk":"(\d{19})"'
                match = re.search(pattern, response_text)
                if match:
                    story_id = match.group(1)
                    print(f"{Fore.GREEN}✅ Session {self.session_id}: Story ID found: {story_id}{Style.RESET_ALL}")
                    return story_id
            print(f'{Fore.RED}❌ Session {self.session_id}: No stories found or account is private{Style.RESET_ALL}')
            return None
        except Exception as e:
            print(f'{Fore.RED}❌ Session {self.session_id}: Error getting story ID: {str(e)}{Style.RESET_ALL}')
            return None
    
    def get_post_id(self, user_id):
        print(f"{Fore.YELLOW}📸 Session {self.session_id}: Fetching post information...{Style.RESET_ALL}")
        headers = {
            'accept-language': 'en-US,en;q=0.9',
            'User-Agent': self.api_params.get("user_agent", "Mozilla/5.0 (Linux; Android 12; X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"),
            'x-asbd-id': str(random.randint(*self.api_params.get("asbd_id_range", [30000, 79999]))),
            'x-csrftoken': self.csrftoken,
            'x-ig-app-id': str(random.randint(*self.api_params.get("ig_app_id_range", [1000, 3337]))),
            'x-ig-www-claim': self.api_params.get("x_ig_www_claim", "hmac.AR1qzeEVPBuPPsJxBMlPlU19lLRm0LG3bSnly_p3mz0aRW2P"),
            'x-instagram-ajax': str(random.randint(*self.api_params.get("instagram_ajax_range", [100, 3939]))),
            'x-requested-with': 'XMLHttpRequest'
        }    	
        
        data = {
            'fb_api_req_friendly_name': 'PolarisProfileFeedQuery',
            'variables': f'{{"id":"{user_id}","first":1}}',
            'server_timestamps': 'true',
            'doc_id': self.api_params.get("doc_id", "8481088891928753")
        }
        
        try:
            self.enforce_rate_limit()
            response = self.session.post(
                'https://www.instagram.com/graphql/query',
                cookies=self.cookies,
                headers=headers,
                data=data
            )   
            
            if response.status_code != 200:
                print(f"{Fore.RED}❌ Session {self.session_id}: API error {response.status_code}{Style.RESET_ALL}")
                return None
                
            response_text = response.text
            
            if 'shortcode' in response_text:
                pattern = r'"shortcode":"([^"]+)"'
                match = re.search(pattern, response_text)
                if match:
                    post_id = match.group(1)
                    print(f"{Fore.GREEN}✅ Session {self.session_id}: Post ID found: {post_id}{Style.RESET_ALL}")
                    return post_id
            print(f'{Fore.RED}❌ Session {self.session_id}: No posts found or account is private{Style.RESET_ALL}')
            return None
        except Exception as e:
            print(f'{Fore.RED}❌ Session {self.session_id}: Error getting post ID: {str(e)}{Style.RESET_ALL}')
            return None
    
    def get_report_info(self, object_id, object_type):    
        print(f"{Fore.YELLOW}📋 Session {self.session_id}: Getting report information for {object_type}...{Style.RESET_ALL}")
        headers = {
            'accept-language': 'en-US,en;q=0.9',
            'User-Agent': self.api_params.get("user_agent", "Mozilla/5.0 (Linux; Android 12; X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"),
            'x-asbd-id': str(random.randint(*self.api_params.get("asbd_id_range", [30000, 79999]))),
            'x-csrftoken': self.csrftoken,
            'x-ig-app-id': str(random.randint(*self.api_params.get("ig_app_id_range", [1000, 3337]))),
            'x-ig-www-claim': self.api_params.get("x_ig_www_claim", "hmac.AR1qzeEVPBuPPsJxBMlPlU19lLRm0LG3bSnly_p3mz0aRW2P"),
            'x-instagram-ajax': str(random.randint(*self.api_params.get("instagram_ajax_range", [100, 3939]))),
            'x-requested-with': 'XMLHttpRequest'
        }
        
        # Different container_module based on object type
        container_modules = {
            'story': 'StoriesPage',
            'post': 'feed_timeline',
            'account': 'profile'
        }
        
        data = {
            'container_module': container_modules.get(object_type, 'feed_timeline'),
            'entry_point': '1',
            'location': '4',
            'object_id': object_id,
            'object_type': '1',
            'frx_prompt_request_type': '1'
        }
        
        try:
            self.enforce_rate_limit()
            response = self.session.post(
                'https://www.instagram.com/api/v1/web/reports/get_frx_prompt/',
                headers=headers,
                data=data,
                cookies=self.cookies
            )    
            
            if response.status_code != 200:
                print(f"{Fore.RED}❌ Session {self.session_id}: API error {response.status_code}{Style.RESET_ALL}")
                return None, None
                
            try:
                response_json = response.json()
            except:
                print(f"{Fore.RED}❌ Session {self.session_id}: Invalid JSON response{Style.RESET_ALL}")
                return None, None
                
            report_info = response_json.get('response', {}).get('report_info', {})
            context = response_json.get('response', {}).get('context', {})
            object_id = report_info.get("object_id", "").strip('"')       
            
            if not object_id or not context:
                print(f"{Fore.RED}❌ Session {self.session_id}: Invalid report info received{Style.RESET_ALL}")
                return None, None
                
            print(f"{Fore.GREEN}✅ Session {self.session_id}: Report information retrieved{Style.RESET_ALL}")
            return object_id, context
        except Exception as e:
            print(f'{Fore.RED}❌ Session {self.session_id}: Error getting report info: {str(e)}{Style.RESET_ALL}')
            return None, None
        
    def submit_report(self, object_id, context, report_reason='ig_i_dont_like_it_v3', object_type='story'):
        headers = {
            'accept-language': 'en-US,en;q=0.9',
            'User-Agent': self.api_params.get("user_agent", "Mozilla/5.0 (Linux; Android 12; X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"),
            'x-asbd-id': str(random.randint(*self.api_params.get("asbd_id_range", [30000, 79999]))),
            'x-csrftoken': self.csrftoken,
            'x-ig-app-id': str(random.randint(*self.api_params.get("ig_app_id_range", [1000, 3337]))),
            'x-ig-www-claim': self.api_params.get("x_ig_www_claim", "hmac.AR1qzeEVPBuPPsJxBMlPlU19lLRm0LG3bSnly_p3mz0aRW2P"),
            'x-instagram-ajax': str(random.randint(*self.api_params.get("instagram_ajax_range", [100, 3939]))),
            'x-requested-with': 'XMLHttpRequest'
        }
        
        # Different container_module based on object type
        container_modules = {
            'story': 'StoriesPage',
            'post': 'feed_timeline',
            'account': 'profile'
        }
        
        data = {
            'container_module': container_modules.get(object_type, 'feed_timeline'),
            'entry_point': '1',
            'location': '4',
            'object_id': object_id,
            'object_type': '1',
            'context': context,
            'selected_tag_types': f'["{report_reason}"]',
            'frx_prompt_request_type': '2',
        }
    
        try:
            self.enforce_rate_limit()
            response = self.session.post(
                'https://www.instagram.com/api/v1/web/reports/get_frx_prompt/',
                headers=headers,
                data=data,
                cookies=self.cookies
            )       
            
            if response.status_code != 200:
                print(f"{Fore.RED}❌ Session {self.session_id}: API error {response.status_code}{Style.RESET_ALL}")
                with self.lock:
                    self.failure_count += 1
                return False
                
            response_text = response.text
            
            if '"text":"Done"' in response_text or '"status":"ok"' in response_text:
                with self.lock:
                    self.success_count += 1
                print(f"{Fore.GREEN}✅ Session {self.session_id}: Report sent successfully! (Total: {self.success_count}){Style.RESET_ALL}")
                return True
            else:
                with self.lock:
                    self.failure_count += 1
                print(f"{Fore.RED}❌ Session {self.session_id}: Report failed! (Total failures: {self.failure_count}){Style.RESET_ALL}")
                
                # Handle specific errors
                if 'Try Again Later' in response_text or 'Please wait a few minutes' in response_text:
                    print(f"{Fore.YELLOW}⚠️ Session {self.session_id}: Rate limited. Increasing delay and rotating proxy.{Style.RESET_ALL}")
                    self.min_delay = min(self.min_delay * 2, 30)  # Double delay, max 30 seconds
                    self.rotate_proxy()
                elif 'checkpoint_required' in response_text:
                    print(f"{Fore.YELLOW}⚠️ Session {self.session_id}: Checkpoint required. This session may be blocked.{Style.RESET_ALL}")
                    self.is_logged_in = False  # Mark as logged out
                elif 'invalid_parameters' in response_text:
                    print(f"{Fore.YELLOW}⚠️ Session {self.session_id}: Invalid parameters. Trying different report reason.{Style.RESET_ALL}")
                    
                return False
        except Exception as e:
            with self.lock:
                self.failure_count += 1
            print(f"{Fore.RED}❌ Session {self.session_id}: Error submitting report: {str(e)}{Style.RESET_ALL}")
            return False

class InstagramReporter:
    def __init__(self):
        self.sessions = []
        self.proxies = []
        self.display_banner()
        self.main_menu()
        
    def display_banner(self):
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                 Instagram Multi-Reporter Tool              ║
║                         by ARMAAN                           ║
║              Story/Post/Account Reporting Edition          ║
║                 Multi-Session Login (50+)                  ║
║                 Auto-Update API Enabled                    ║
║                 Proxy Support Added                        ║
║                 Enhanced Error Handling                     ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(f"{Fore.MAGENTA}{banner}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
        
    def main_menu(self):
        while True:
            print(f"\n{Fore.CYAN}📋 Main Menu:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}1. Mass Reporting (Multiple Targets){Style.RESET_ALL}")
            print(f"{Fore.WHITE}2. Single Target Reporting{Style.RESET_ALL}")
            print(f"{Fore.WHITE}3. Account Management (Login/Logout){Style.RESET_ALL}")
            print(f"{Fore.WHITE}4. Proxy Management{Style.RESET_ALL}")
            print(f"{Fore.WHITE}5. Update Instagram API Parameters{Style.RESET_ALL}")
            print(f"{Fore.WHITE}6. Exit{Style.RESET_ALL}")
            
            choice = input(f"{Fore.CYAN}Enter your choice (1-6): {Style.RESET_ALL}")
            
            if choice == '1':
                self.mass_reporting_menu()
            elif choice == '2':
                self.single_target_reporting()
            elif choice == '3':
                self.account_management()
            elif choice == '4':
                self.proxy_management()
            elif choice == '5':
                global API_PARAMS
                API_PARAMS = update_api_params()
                print(f"{Fore.GREEN}✅ API parameters updated!{Style.RESET_ALL}")
            elif choice == '6':
                print(f"{Fore.YELLOW}👋 Exiting...{Style.RESET_ALL}")
                sys.exit(0)
            else:
                print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")
    
    def proxy_management(self):
        print(f"\n{Fore.CYAN}📋 Proxy Management Menu:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. Fetch Fresh Proxies{Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. Load Proxies from File{Style.RESET_ALL}")
        print(f"{Fore.WHITE}3. View Current Proxies{Style.RESET_ALL}")
        print(f"{Fore.WHITE}4. Back to Main Menu{Style.RESET_ALL}")
        
        choice = input(f"{Fore.CYAN}Enter your choice (1-4): {Style.RESET_ALL}")
        
        if choice == '1':
            self.proxies = fetch_proxies()
        elif choice == '2':
            self.proxies = load_proxies()
        elif choice == '3':
            self.view_proxies()
        elif choice == '4':
            return
        else:
            print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")
            self.proxy_management()
    
    def view_proxies(self):
        if not self.proxies:
            print(f"{Fore.YELLOW}⚠️ No proxies loaded.{Style.RESET_ALL}")
            return
            
        print(f"\n{Fore.CYAN}Loaded Proxies ({len(self.proxies)}):{Style.RESET_ALL}")
        for i, proxy in enumerate(self.proxies[:10]):  # Show first 10 proxies
            print(f"{i+1}. {proxy}")
        
        if len(self.proxies) > 10:
            print(f"... and {len(self.proxies) - 10} more")
    
    def mass_reporting_menu(self):
        print(f"\n{Fore.CYAN}📋 Mass Reporting Menu:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. Report Stories{Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. Report Posts{Style.RESET_ALL}")
        print(f"{Fore.WHITE}3. Report Accounts{Style.RESET_ALL}")
        print(f"{Fore.WHITE}4. Back to Main Menu{Style.RESET_ALL}")
        
        choice = input(f"{Fore.CYAN}Enter your choice (1-4): {Style.RESET_ALL}")
        
        if choice == '1':
            self.start_mass_reporting('story')
        elif choice == '2':
            self.start_mass_reporting('post')
        elif choice == '3':
            self.start_mass_reporting('account')
        elif choice == '4':
            return
        else:
            print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")
            self.mass_reporting_menu()
    
    def single_target_reporting(self):
        print(f"\n{Fore.CYAN}📋 Single Target Reporting Menu:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. Report Story{Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. Report Post{Style.RESET_ALL}")
        print(f"{Fore.WHITE}3. Report Account{Style.RESET_ALL}")
        print(f"{Fore.WHITE}4. Back to Main Menu{Style.RESET_ALL}")
        
        choice = input(f"{Fore.CYAN}Enter your choice (1-4): {Style.RESET_ALL}")
        
        if choice == '1':
            self.start_single_target_reporting('story')
        elif choice == '2':
            self.start_single_target_reporting('post')
        elif choice == '3':
            self.start_single_target_reporting('account')
        elif choice == '4':
            return
        else:
            print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")
            self.single_target_reporting()
    
    def account_management(self):
        print(f"\n{Fore.CYAN}📋 Account Management Menu:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. Login to Accounts{Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. View Active Sessions{Style.RESET_ALL}")
        print(f"{Fore.WHITE}3. Logout All Sessions{Style.RESET_ALL}")
        print(f"{Fore.WHITE}4. Back to Main Menu{Style.RESET_ALL}")
        
        choice = input(f"{Fore.CYAN}Enter your choice (1-4): {Style.RESET_ALL}")
        
        if choice == '1':
            self.setup_sessions()
        elif choice == '2':
            self.view_active_sessions()
        elif choice == '3':
            self.logout_all_sessions()
        elif choice == '4':
            return
        else:
            print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")
            self.account_management()
    
    def setup_sessions(self):
        print(f"{Fore.CYAN}Setting up Instagram sessions...{Style.RESET_ALL}")
        
        # Load proxies if not already loaded
        if not self.proxies:
            self.proxies = load_proxies()
        
        # Ask how many sessions to set up
        try:
            num_sessions = int(input(f"{Fore.CYAN}How many sessions to set up? (1-50): {Style.RESET_ALL}"))
            num_sessions = min(max(1, num_sessions), 50)
        except ValueError:
            print(f"{Fore.YELLOW}Invalid input. Using 10 sessions.{Style.RESET_ALL}")
            num_sessions = 10
        
        # Create and login sessions
        self.sessions = []
        successful_logins = 0
        
        for i in range(num_sessions):
            print(f"\n{Fore.YELLOW}Enter credentials for session {i+1}/{num_sessions}:{Style.RESET_ALL}")
            username = input(f"{Fore.CYAN}Username: {Style.RESET_ALL}")
            password = input(f"{Fore.CYAN}Password: {Style.RESET_ALL}")
            
            # Assign a proxy to each session if available
            proxy = None
            if self.proxies:
                proxy = random.choice(self.proxies)
            
            session = InstagramSession(username, password, i+1, proxy)
            # Add reference to reporter for proxy rotation
            session.reporter = self
            
            if session.login():
                self.sessions.append(session)
                successful_logins += 1
            else:
                print(f"{Fore.RED}❌ Session {i+1} failed to login{Style.RESET_ALL}")
                
        print(f"{Fore.GREEN}✅ {successful_logins} out of {num_sessions} sessions successfully logged in{Style.RESET_ALL}")
        
        if successful_logins < num_sessions:
            print(f"{Fore.YELLOW}⚠️ Only {successful_logins} sessions are available for reporting{Style.RESET_ALL}")
        
        # Show login summary
        print(f"\n{Fore.CYAN}Login Summary:{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Successful: {successful_logins}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {num_sessions - successful_logins}{Style.RESET_ALL}")
    
    def view_active_sessions(self):
        if not self.sessions:
            print(f"{Fore.YELLOW}⚠️ No active sessions found.{Style.RESET_ALL}")
            return
            
        print(f"\n{Fore.CYAN}Active Sessions ({len(self.sessions)}):{Style.RESET_ALL}")
        for session in self.sessions:
            status = f"{Fore.GREEN}Active{Style.RESET_ALL}" if session.is_logged_in else f"{Fore.RED}Inactive{Style.RESET_ALL}"
            proxy_info = f"Proxy: {session.proxy}" if session.proxy else "No Proxy"
            print(f"Session {session.session_id}: {session.username} - {status} - {proxy_info}")
            print(f"  Success: {session.success_count}, Failures: {session.failure_count}")
    
    def logout_all_sessions(self):
        if not self.sessions:
            print(f"{Fore.YELLOW}⚠️ No active sessions found.{Style.RESET_ALL}")
            return
            
        confirm = input(f"{Fore.YELLOW}Are you sure you want to logout all sessions? (y/n): {Style.RESET_ALL}")
        if confirm.lower() == 'y':
            self.sessions = []
            print(f"{Fore.GREEN}✅ All sessions logged out.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Operation cancelled.{Style.RESET_ALL}")
    
    def get_targets(self):
        print(f"\n{Fore.CYAN}📋 How would you like to input target usernames?{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. Enter manually{Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. Load from file (targets.txt){Style.RESET_ALL}")
        print(f"{Fore.WHITE}3. Generate random targets{Style.RESET_ALL}")
        
        choice = input(f"{Fore.CYAN}Enter your choice (1-3): {Style.RESET_ALL}")
        
        targets = []
        
        if choice == '1':
            print(f"{Fore.YELLOW}Enter target usernames (one per line, type 'done' when finished):{Style.RESET_ALL}")
            while True:
                username = input(f"{Fore.CYAN}Target username: {Style.RESET_ALL}")
                if username.lower() == 'done':
                    break
                if username.strip():
                    targets.append(username.strip())
                    
        elif choice == '2':
            if os.path.exists('targets.txt'):
                try:
                    with open('targets.txt', 'r') as f:
                        targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    print(f"{Fore.GREEN}✅ Loaded {len(targets)} targets from targets.txt{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}❌ Error loading targets: {str(e)}{Style.RESET_ALL}")
                    targets = []
            else:
                print(f"{Fore.YELLOW}targets.txt not found. Creating a new one...{Style.RESET_ALL}")
                with open('targets.txt', 'w') as f:
                    f.write("# Add one Instagram username per line\n")
                    f.write("# Example:\n")
                    f.write("target1\n")
                    f.write("target2\n")
                print(f"{Fore.GREEN}✅ Created targets.txt. Please add targets and run again.{Style.RESET_ALL}")
                return targets
                
        elif choice == '3':
            try:
                num_targets = int(input(f"{Fore.CYAN}How many random targets to generate? {Style.RESET_ALL}"))
                prefix = input(f"{Fore.CYAN}Username prefix (default: user): {Style.RESET_ALL}") or "user"
                for i in range(1, num_targets + 1):
                    targets.append(f"{prefix}{random.randint(1000, 9999)}")
                print(f"{Fore.GREEN}✅ Generated {len(targets)} random targets{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}❌ Invalid input. Using 5 random targets.{Style.RESET_ALL}")
                targets = [f"user{random.randint(1000, 9999)}" for _ in range(5)]
        else:
            print(f"{Fore.RED}❌ Invalid choice. Using manual input.{Style.RESET_ALL}")
            return self.get_targets()
            
        if not targets:
            print(f"{Fore.RED}❌ No targets provided.{Style.RESET_ALL}")
            return targets
            
        # Save targets to file
        with open('targets.txt', 'w') as f:
            f.write("# Instagram targets for reporting\n")
            for target in targets:
                f.write(f"{target}\n")
        print(f"{Fore.GREEN}✅ Saved {len(targets)} targets to targets.txt{Style.RESET_ALL}")
        
        return targets
    
    def get_single_target(self):
        target = input(f"{Fore.CYAN}Enter target username: {Style.RESET_ALL}")
        if not target.strip():
            print(f"{Fore.RED}❌ No target provided.{Style.RESET_ALL}")
            return None
        return target.strip()
    
    def get_report_reason(self):
        print(f"\n{Fore.CYAN}📝 Select report reason:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. I don't like this{Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. Harassment/Bullying{Style.RESET_ALL}")
        print(f"{Fore.WHITE}3. Suicide/Self-harm{Style.RESET_ALL}")
        print(f"{Fore.WHITE}4. Violence/Hate{Style.RESET_ALL}")
        print(f"{Fore.WHITE}5. Sale/Promotion{Style.RESET_ALL}")
        print(f"{Fore.WHITE}6. Nudity/Sexual{Style.RESET_ALL}")
        print(f"{Fore.WHITE}7. Scam/Spam{Style.RESET_ALL}")
        print(f"{Fore.WHITE}8. False Information{Style.RESET_ALL}")
        
        reason_choice = input(f"{Fore.CYAN}Enter your choice (1-8): {Style.RESET_ALL}")
        
        report_reasons = {
            '1': 'ig_i_dont_like_it_v3',
            '2': 'adult_content-threat_to_share_nude_images-u18-yes',
            '3': 'suicide_or_self_harm_concern-suicide_or_self_injury',
            '4': 'violent_hateful_or_disturbing-violence',
            '5': 'selling_or_promoting_restricted_items-drugs-high-risk',
            '6': 'adult_content-nudity_or_sexual_activity',
            '7': 'misleading_annoying_or_scam-fraud_or_scam',
            '8': 'misleading_annoying_or_scam-false_information-health'
        }
        
        return report_reasons.get(reason_choice, 'ig_i_dont_like_it_v3')
    
    def start_mass_reporting(self, report_type):
        # Filter out sessions that are not logged in
        active_sessions = [session for session in self.sessions if session.is_logged_in]
        if not active_sessions:
            print(f"{Fore.RED}❌ No active (logged-in) sessions available. Please check your login credentials.{Style.RESET_ALL}")
            return
            
        targets = self.get_targets()
        if not targets:
            return
        
        # Get report parameters
        try:
            reports_per_target = int(input(f'{Fore.CYAN}Enter number of reports per target: {Style.RESET_ALL}'))
        except ValueError:
            print(f"{Fore.YELLOW}Invalid input. Using default: 10 reports per target{Style.RESET_ALL}")
            reports_per_target = 10
            
        try:
            delay = float(input(f'{Fore.CYAN}Enter delay between reports in seconds (default: 2.0): {Style.RESET_ALL}') or "2.0")
        except ValueError:
            print(f"{Fore.YELLOW}Invalid input. Using default: 2.0 seconds{Style.RESET_ALL}")
            delay = 2.0
        
        # Set minimum delay for each session
        for session in active_sessions:
            session.min_delay = delay
        
        report_reason = self.get_report_reason()
        
        print(f"\n{Fore.GREEN}🚀 Starting mass {report_type} reporting for {len(targets)} targets...{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Sending {reports_per_target} reports per target with {delay}s delay between each{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Report reason: {report_reason}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Total reports to send: {len(targets) * reports_per_target}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Using {len(active_sessions)} active sessions{Style.RESET_ALL}\n")
        
        # Create a queue for targets - Add each target multiple times
        target_queue = Queue()
        for target in targets:
            for _ in range(reports_per_target):
                target_queue.put(target)
        
        # Shuffle the queue to distribute reports across sessions
        queue_items = []
        while not target_queue.empty():
            queue_items.append(target_queue.get())
        random.shuffle(queue_items)
        for item in queue_items:
            target_queue.put(item)
        
        # Start worker threads for each session
        threads = []
        for session in active_sessions:
            thread = threading.Thread(
                target=self.mass_report_worker,
                args=(session, target_queue, reports_per_target, delay, report_reason, report_type)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Wait for all targets to be processed
        target_queue.join()
        
        # Print summary
        total_success = sum(session.success_count for session in active_sessions)
        total_failure = sum(session.failure_count for session in active_sessions)
        
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🏁 Mass {report_type} reporting completed!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Total successful reports: {total_success}{Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Total failed reports: {total_failure}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        
        # Print per-session stats
        print(f"\n{Fore.CYAN}Per-session statistics:{Style.RESET_ALL}")
        for session in active_sessions:
            print(f"Session {session.session_id} ({session.username}): "
                  f"{Fore.GREEN}{session.success_count} success{Style.RESET_ALL}, "
                  f"{Fore.RED}{session.failure_count} failures{Style.RESET_ALL}")
    
    def start_single_target_reporting(self, report_type):
        # Filter out sessions that are not logged in
        active_sessions = [session for session in self.sessions if session.is_logged_in]
        if not active_sessions:
            print(f"{Fore.RED}❌ No active (logged-in) sessions available. Please check your login credentials.{Style.RESET_ALL}")
            return
            
        target = self.get_single_target()
        if not target:
            return
        
        # Get report parameters
        try:
            reports_count = int(input(f'{Fore.CYAN}Enter number of reports to send: {Style.RESET_ALL}'))
        except ValueError:
            print(f"{Fore.YELLOW}Invalid input. Using default: 10 reports{Style.RESET_ALL}")
            reports_count = 10
            
        try:
            delay = float(input(f'{Fore.CYAN}Enter delay between reports in seconds (default: 2.0): {Style.RESET_ALL}') or "2.0")
        except ValueError:
            print(f"{Fore.YELLOW}Invalid input. Using default: 2.0 seconds{Style.RESET_ALL}")
            delay = 2.0
        
        # Set minimum delay for each session
        for session in active_sessions:
            session.min_delay = delay
        
        report_reason = self.get_report_reason()
        
        print(f"\n{Fore.GREEN}🚀 Starting single target {report_type} reporting for {target}...{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Sending {reports_count} reports with {delay}s delay between each{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Report reason: {report_reason}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Using {len(active_sessions)} active sessions{Style.RESET_ALL}\n")
        
        # Create a queue for targets - Add the target multiple times
        target_queue = Queue()
        for _ in range(reports_count):
            target_queue.put(target)
        
        # Shuffle the queue to distribute reports across sessions
        queue_items = []
        while not target_queue.empty():
            queue_items.append(target_queue.get())
        random.shuffle(queue_items)
        for item in queue_items:
            target_queue.put(item)
        
        # Start worker threads for each session
        threads = []
        for session in active_sessions:
            thread = threading.Thread(
                target=self.mass_report_worker,
                args=(session, target_queue, reports_count, delay, report_reason, report_type)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Wait for all targets to be processed
        target_queue.join()
        
        # Print summary
        total_success = sum(session.success_count for session in active_sessions)
        total_failure = sum(session.failure_count for session in active_sessions)
        
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}🏁 Single target {report_type} reporting completed!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Total successful reports: {total_success}{Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Total failed reports: {total_failure}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        
        # Print per-session stats
        print(f"\n{Fore.CYAN}Per-session statistics:{Style.RESET_ALL}")
        for session in active_sessions:
            print(f"Session {session.session_id} ({session.username}): "
                  f"{Fore.GREEN}{session.success_count} success{Style.RESET_ALL}, "
                  f"{Fore.RED}{session.failure_count} failures{Style.RESET_ALL}")
    
    def mass_report_worker(self, session, target_queue, reports_per_target, delay, report_reason, report_type):
        # Check if session is logged in
        if not session.is_logged_in:
            print(f"{Fore.RED}❌ Session {session.session_id}: Not logged in. Skipping.{Style.RESET_ALL}")
            return
            
        # Keep track of reports sent per target
        reports_sent_per_target = {}
        
        while not target_queue.empty():
            try:
                target = target_queue.get_nowait()
            except:
                break
                
            # Initialize counter for this target if not exists
            if target not in reports_sent_per_target:
                reports_sent_per_target[target] = 0
                
            # Check if we've already sent enough reports for this target
            if reports_sent_per_target[target] >= reports_per_target:
                target_queue.task_done()
                continue
                
            print(f"{Fore.CYAN}🎯 Session {session.session_id}: Processing target {target}... (Report {reports_sent_per_target[target]+1}/{reports_per_target}){Style.RESET_ALL}")
            
            # Get user ID for this target
            user_id = session.get_user_id(target)
            if not user_id:
                target_queue.task_done()
                continue
            
            # Get object ID based on report type
            object_id = None
            if report_type == 'story':
                object_id = session.get_story_id(user_id)
            elif report_type == 'post':
                object_id = session.get_post_id(user_id)
            elif report_type == 'account':
                object_id = user_id  # For account reporting, we use user_id directly
            
            if not object_id:
                target_queue.task_done()
                continue
                
            # Send report for this target
            print(f"{Fore.YELLOW}📤 Session {session.session_id}: Sending report for {target}...{Style.RESET_ALL}")
            
            # Get report info for this session
            obj_id, context = session.get_report_info(object_id, report_type)
            if not obj_id or not context:
                target_queue.task_done()
                continue
                
            # Submit report
            success = session.submit_report(obj_id, context, report_reason, report_type)
            
            # Update counter if successful
            if success:
                reports_sent_per_target[target] += 1
                print(f"{Fore.GREEN}✅ Session {session.session_id}: Report sent for {target} ({reports_sent_per_target[target]}/{reports_per_target}){Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Session {session.session_id}: Failed to send report for {target}{Style.RESET_ALL}")
            
            # Mark target as processed
            target_queue.task_done()
            
            # If we haven't sent enough reports for this target, put it back in the queue
            if reports_sent_per_target[target] < reports_per_target:
                target_queue.put(target)
                # Small delay before retrying the same target
                time.sleep(0.5)

if __name__ == "__main__":
    reporter = InstagramReporter()