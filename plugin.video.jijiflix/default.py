import sys, re, time, ssl
import urllib.parse
import requests
from bs4 import BeautifulSoup
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc
import concurrent.futures
import ssl
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import SSLError
from urllib3.poolmanager import PoolManager


# Configure SSL globally
ssl._create_default_https_context = ssl.create_default_context

class PremiumizeDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.progress = 0
        self.status = ""
        self.files = []
        
    def update_direct_download(self, status, files):
        self.status = status
        self.files = files or []
        
    def update_transfer_status(self, transfer, percent, message):
        self.progress = percent
        self.status = message
        
    def show_success(self, file_info):
        self.close()
        xbmcgui.Dialog().ok("Success", "Stream is ready to play!")
        
    def show_error(self, message):
        self.close()
        xbmcgui.Dialog().ok("Error", message)
        
    def iscanceled(self):
        return False
        
    def close(self):
        pass
    
class SSLContextAdapter(HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context or self._create_default_ssl_context()
        super().__init__(**kwargs)

    def _create_default_ssl_context(self):
        context = ssl.create_default_context()
        # Modern secure settings
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.verify_mode = ssl.CERT_OPTIONAL
        context.check_hostname = False
        return context

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context
        )

from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
FORUM_DOMAIN = ADDON.getSetting("forum_domain") or "www.1tamilmv.boo"

# Language and quality mapping
LANGUAGE_QUALITY_MAP = {
    "Malayalam": {
        "WEB-HD / iTunes-HD / BluRay": f"http://{FORUM_DOMAIN}/index.php?/forums/forum/36-web-hd-itunes-hd-bluray/",
        "PreDVD / DVDScr / CAM / TC": f"http://{FORUM_DOMAIN}/index.php?/forums/forum/35-predvd-dvdscr-cam-tc/"
    },
    "Tamil": {
        "WEB-HD / iTunes-HD / BluRay": f"http://{FORUM_DOMAIN}/index.php?/forums/forum/11-web-hd-itunes-hd-bluray/",
        "PreDVD / DVDScr / CAM / TC": f"http://{FORUM_DOMAIN}/index.php?/forums/forum/10-predvd-dvdscr-cam-tc/"
    },
    "Telugu": {
        "WEB-HD / iTunes-HD / BluRay": f"http://{FORUM_DOMAIN}/index.php?/forums/forum/24-web-hd-itunes-hd-bluray/",
        "PreDVD / DVDScr / CAM / TC": f"http://{FORUM_DOMAIN}/index.php?/forums/forum/23-predvd-dvdscr-cam-tc/"
    },
    "Hindi": {
        "WEB-HD / iTunes-HD / BluRay": f"http://{FORUM_DOMAIN}/index.php?/forums/forum/58-web-hd-itunes-hd-bluray/",
        "PreDVD / DVDScr / CAM / TC": f"http://{FORUM_DOMAIN}/index.php?/forums/forum/57-predvd-dvdscr-cam-tc/"
    },
    "Kannada": {
        "WEB-HD / iTunes-HD / BluRay": f"http://{FORUM_DOMAIN}/index.php?/forums/forum/69-web-hd-itunes-hd-bluray/",
        "PreDVD / DVDScr / CAM / TC": f"http://{FORUM_DOMAIN}/index.php?/forums/forum/68-predvd-dvdscr-cam-tc/"
    }
}

def log_info(message: str):
    xbmc.log(f"[JijiFlix] {message}", xbmc.LOGINFO)

def log_error(message: str):
    xbmc.log(f"[JijiFlix] {message}", xbmc.LOGERROR)

def get_url(**kwargs):
    return sys.argv[0] + '?' + urllib.parse.urlencode(kwargs)

# Log environment details at startup
log_info(f"Python version: {sys.version}")
log_info(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
log_info(f"Requests version: {requests.__version__}")
log_info(f"Supported protocols: {ssl.PROTOCOL_TLSv1_2 if hasattr(ssl, 'PROTOCOL_TLSv1_2') else 'TLSv1.2 not supported'}")

@dataclass
class MovieThumbnail:
    url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

    def is_valid_url(self) -> bool:
        if not self.url:
            return False
        try:
            result = urlparse(self.url)
            return all([result.scheme, result.netloc])
        except:
            return False

@dataclass
class MoviePost:
    title: str
    link: str
    thumbnail: Optional[MovieThumbnail] = None
    description: Optional[str] = None
    magnet_link: Optional[str] = None

def fetch_magnet_link(post_url: str) -> List[Dict[str, str]]:
    headers = {"User-Agent": "Mozilla/5.0"}
    log_info(f"Fetching magnet from: {post_url}")
    
    try:
        response = requests.get(post_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        magnet_links = []
        seen_magnets = set()
        
        magnet_tags = (
            soup.find_all("a", class_="skyblue-button", href=lambda x: x and x.startswith("magnet:")) or
            soup.find_all("a", href=lambda x: x and x.startswith("magnet:"))
        )
        
        for magnet_tag in magnet_tags:
            magnet_link = magnet_tag["href"]
            
            hash_match = re.search(r'btih:([a-fA-F0-9]+)', magnet_link)
            if not hash_match:
                continue
                
            magnet_hash = hash_match.group(1).lower()
            if magnet_hash in seen_magnets:
                continue
                
            seen_magnets.add(magnet_hash)
            
            quality = "Unknown Quality"
            size_text = ""
            info_text = []
            
            if "2160p" in magnet_link or "4k" in magnet_link.lower() or "uhd" in magnet_link.lower():
                quality = "4K"
            elif "1080p" in magnet_link:
                quality = "1080p"
            elif "720p" in magnet_link:
                quality = "720p"
            elif "480p" in magnet_link:
                quality = "480p"
                
            size_text = ""
            size_match = re.search(r'dn=([^&]+)', magnet_link)
            if size_match:
                size_str = size_match.group(1)
                size_parts = re.match(r'(\d+(?:\.\d+)?)\s*(GB|MB)', size_str, re.IGNORECASE)
                if size_parts:
                    size_num, size_unit = size_parts.groups()
                    if size_unit.upper() == "MB":
                        size_num = float(size_num) / 1024
                    size_text = f" - {size_num:.2f} GB"
                
            if "hevc" in magnet_link.lower() or "x265" in magnet_link.lower():
                info_text.append("HEVC")
            elif "x264" in magnet_link.lower():
                info_text.append("x264")
            if "hdr" in magnet_link.lower():
                info_text.append("HDR")
                
            info_str = " | ".join(info_text) if info_text else ""
            
            magnet_links.append({
                "link": magnet_link,
                "description": f"{quality}{size_text}",
                "info": info_str,
                "context": magnet_link[:200] + "..." if len(magnet_link) > 200 else magnet_link
            })
            
        return magnet_links
            
    except Exception as e:
        log_info(f"Error fetching magnet links: {str(e)}")
        return []

def fetch_post_details(post_data: Dict) -> MoviePost:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(post_data["link"], headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        thumbnail_data = None
        img_tag = soup.find("img", class_="ipsImage")
        if img_tag:
            thumb_url = img_tag.get("src", "").strip()
            if thumb_url:
                if not thumb_url.startswith(("http://", "https://")):
                    thumb_url = f"https://{FORUM_DOMAIN}{thumb_url}"
                thumbnail_data = MovieThumbnail(url=thumb_url)
                log_info(f"Found thumbnail: {thumb_url}")
        
        magnet_links = fetch_magnet_link(post_data["link"])
        magnet_link = magnet_links[0]["link"] if magnet_links else None
        description = magnet_links[0]["description"] if magnet_links else None
        
        return MoviePost(
            title=post_data["title"],
            link=post_data["link"],
            thumbnail=thumbnail_data,
            magnet_link=magnet_link,
            description=description
        )
    except Exception as e:
        log_info(f"Error processing post {post_data['title']}: {str(e)}")
        return MoviePost(
            title=post_data["title"],
            link=post_data["link"]
        )

def fetch_forum_posts(base_url: str, page: int = 1) -> tuple[List[MoviePost], bool]:
    headers = {"User-Agent": "Mozilla/5.0"}
    page_url = f"{base_url}&page={page}" if page > 1 else base_url
    log_info(f"Fetching feed from: {page_url}")

    try:
        # First attempt with secure settings
        secure_context = ssl.create_default_context()
        secure_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        session = requests.Session()
        adapter = SSLContextAdapter(ssl_context=secure_context, max_retries=Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        ))
        session.mount('https://', adapter)
        response = session.get(page_url, headers=headers, timeout=15)
        response.raise_for_status()

    except requests.exceptions.SSLError as e:
        log_error(f"Secure SSL connection failed, trying with more lenient settings: {str(e)}")
        try:
            # Fallback with more lenient settings (less secure)
            lenient_context = ssl.create_default_context()
            lenient_context.verify_mode = ssl.CERT_OPTIONAL  # Insecure!
            lenient_context.check_hostname = False       # Insecure!
            
            session = requests.Session()
            adapter = SSLContextAdapter(ssl_context=lenient_context, max_retries=Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504]
            ))
            session.mount('https://', adapter)
            response = session.get(page_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            log_info("Connection succeeded with lenient SSL settings (less secure)")
            
        except Exception as fallback_e:
            log_error(f"All SSL connection attempts failed: {str(fallback_e)}")
            raise Exception("All connection attempts failed.") from fallback_e

    except Exception as e:
        log_error(f"Failed to fetch posts: {e}")
        raise Exception("Connection failed.") from e

    soup = BeautifulSoup(response.text, "html.parser")
    log_info(response.text)  # For debugging purposes, remove in production
    posts = []
    
    pagination = soup.find("ul", class_="ipsPagination")
    has_next = False
    if pagination:
        next_link = pagination.find("li", class_="ipsPagination_next")
        has_next = next_link and "ipsPagination_inactive" not in next_link.get("class", [])
        log_info(f"Pagination found - Has next page: {has_next}")
    
    basic_posts = []
    for post in soup.select(".ipsDataItem"):
        title_tag = post.select_one(".ipsDataItem_title a")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag["href"]
        basic_posts.append({"title": title, "link": link})
    
    processed_posts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_post = {executor.submit(fetch_post_details, post): post for post in basic_posts}
        
        progress = xbmcgui.DialogProgress()
        progress.create("Loading Movies", "Fetching movie details...")
        total_posts = len(basic_posts)
        completed = 0
        
        for future in concurrent.futures.as_completed(future_to_post):
            try:
                processed_post = future.result()
                processed_posts.append(processed_post)
                
                completed += 1
                percent = (completed * 100) // total_posts
                progress.update(percent, f"Loading movies... ({completed}/{total_posts})")
                
                log_info(f"Successfully processed post: {processed_post.title}")
            except Exception as e:
                post = future_to_post[future]
                log_info(f"Post processing failed for {post['title']}: {str(e)}")
            
            if progress.iscanceled():
                break
        
        progress.close()
    
    log_info(f"Total posts processed: {len(processed_posts)}")
    return processed_posts, has_next

def list_movies(language: str, quality_type: str, page: int = 1):
    base_url = LANGUAGE_QUALITY_MAP.get(language, {}).get(quality_type)
    if not base_url:
        log_info(f"Invalid language or quality type: {language}, {quality_type}")
        xbmcgui.Dialog().ok("Error", "Invalid language or quality type selected.")
        return
    
    posts, has_next = fetch_forum_posts(base_url, page)
    for post in posts:
        url = get_url(action="play", link=post.link)
        
        year_match = re.search(r'\((\d{4})\)', post.title)
        year = year_match.group(1) if year_match else "Unknown"
        
        label = post.title
        if post.description:
            label += f" [{post.description}]"
        
        list_item = xbmcgui.ListItem(label=label)
        
        if post.thumbnail and post.thumbnail.is_valid_url():
            art_dict = {
                "thumb": post.thumbnail.url,
                "icon": post.thumbnail.url,
                "poster": post.thumbnail.url,
                "fanart": post.thumbnail.url
            }
            list_item.setArt(art_dict)
        
        info_labels = {
            "mediatype": "movie",
            "title": post.title,
            "year": year
        }
        list_item.setInfo("video", info_labels)
        
        play_commands = []
        play_commands.append(("Play Movie", f'PlayMedia({url})'))
        yt_url = f"plugin://plugin.video.youtube/kodion/search/query/?q={urllib.parse.quote(post.title + ' trailer')}&autoplay=true"
        play_commands.append(("Play Trailer", f'PlayMedia({yt_url})'))
        play_commands.append(("Back to Main Menu", f'Container.Update({get_url(action="main_menu")})'))
        list_item.addContextMenuItems(play_commands)
        
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=True)
    
    if has_next:
        next_page = page + 1
        next_url = get_url(action="list", language=language, quality_type=quality_type, page=next_page)
        next_item = xbmcgui.ListItem(label="Next Page >>")
        next_item.setProperty('SpecialSort', 'bottom')
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=next_url, listitem=next_item, isFolder=True)
        
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)

def show_quality_menu(language: str):
    quality_types = list(LANGUAGE_QUALITY_MAP[language].keys())
    quality_labels = [qt for qt in quality_types]
    
    dialog = xbmcgui.Dialog()
    selected = dialog.select(f"Select Quality Type for {language}", quality_labels)
    
    if selected < 0:
        log_info("User canceled quality type selection")
        return
    
    quality_type = quality_types[selected]
    list_movies(language, quality_type)

def show_main_menu():
    languages = list(LANGUAGE_QUALITY_MAP.keys())
    
    for language in languages:
        url = get_url(action="select_quality", language=language)
        list_item = xbmcgui.ListItem(label=language)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=list_item, isFolder=True)
    
    xbmcplugin.endOfDirectory(HANDLE)

def resolve_with_premiumize(magnet_link):
    from premiumize_dialog import PremiumizeDialog
    
    api_key = ADDON.getSetting("premiumize_api_key")
    if not api_key:
        log_info("No Premiumize API key configured")
        xbmcgui.Dialog().ok("Premiumize", "Please set your Premiumize API key in the addon settings.")
        return None

    log_info(f"Starting Premiumize resolution for magnet: {magnet_link[:60]}...")
    
    progress = PremiumizeDialog()
    start_time = time.time()
    
    log_info("Attempting direct download first...")
    direct_dl = get_direct_download(api_key, magnet_link)
    log_info(f"Direct download response: {direct_dl}")
    elapsed = time.time() - start_time
    progress.update_direct_download(f"Checking cache ({elapsed:.1f}s)", direct_dl.get("content", []))
    
    if direct_dl and direct_dl.get("status") == "success":
        content = direct_dl.get("content", [])
        log_info(f"Found {len(content)} content items")
        if content:
            video_files = [
                f for f in content
                if f.get("link") and f.get("link").endswith((".mp4", ".mkv", ".avi"))
            ]
            log_info(f"Found {len(video_files)} video files")
            if video_files:
                largest_file = sorted(video_files, key=lambda x: int(x.get("size", 0)), reverse=True)[0]
                log_info(f"Selected largest file: {largest_file}")
                size_mb = largest_file.get("size", 0) / (1024 * 1024)
                progress.update_direct_download(f"Found file: {size_mb:.1f} MB", [largest_file])
                
                if largest_file.get("stream_link") and largest_file.get("transcode_status") in ["finished", "good_as_is"]:
                    log_info(f"Found transcoded stream link: {largest_file['stream_link']}")
                    progress.show_success(largest_file)
                    progress.close()
                    return largest_file["stream_link"]
                elif largest_file.get("link"):
                    log_info(f"Found direct link: {largest_file['link']}")
                    progress.show_success(largest_file)
                    progress.close()
                    return largest_file["link"]

    log_info("Direct download unavailable, creating transfer...")
    elapsed = time.time() - start_time
    progress.update_direct_download(f"No cache found ({elapsed:.1f}s)", None)
    
    transfer_data = create_transfer(api_key, magnet_link)
    log_info(f"Transfer creation response: {transfer_data}")
    if not transfer_data:
        log_info("Transfer creation failed - no response")
        progress.show_error("Failed to create transfer - no response from server")
        progress.close()
        return None
    elif transfer_data.get("status") != "success":
        error_msg = transfer_data.get("message", "Unknown error")
        log_info(f"Failed to create transfer: {error_msg}")
        progress.show_error(f"Failed to create transfer: {error_msg}")
        progress.close()
        return None

    transfer_id = transfer_data.get("id")
    if not transfer_id:
        log_info("No transfer ID received in response")
        progress.show_error("Failed to get transfer ID from response")
        progress.close()
        return None
    
    log_info(f"Successfully created transfer with ID: {transfer_id}")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        if progress.iscanceled():
            log_info("Transfer monitoring canceled by user")
            return None
            
        transfer_status = check_transfer_status(api_key, transfer_id)
        log_info(f"Transfer status check {attempt + 1}/{max_attempts}: {transfer_status}")
        elapsed = time.time() - start_time
        if not transfer_status:
            log_info("Failed to get transfer status")
            progress.show_error("Failed to get transfer status from server")
            progress.close()
            return None
            
        status = transfer_status.get("status", "")
        percent = min((attempt + 1) * 100 // max_attempts, 100)
        message = f"Transferring... ({elapsed:.1f}s)"
        if "progress" in transfer_status:
            speed = transfer_status.get("speed", 0) / (1024 * 1024)
            message += f" {speed:.1f} MB/s"
        progress.update_transfer_status(transfer_status, percent, message)
        
        if status == "finished":
            break
        elif status in ["error", "deleted"]:
            error_msg = transfer_status.get("message", "Unknown error")
            log_info(f"Transfer failed - {error_msg}")
            progress.show_error(f"Transfer failed: {error_msg}")
            progress.close()
            return None
            
        xbmc.sleep(1000)
        
    else:
        log_info("Transfer monitoring timed out")
        progress.show_error("Transfer timed out - please try again")
        progress.close()
        return None

    files = get_files(api_key, transfer_id)
    elapsed = time.time() - start_time
    progress.update_transfer_status({"status": "fetching files"}, 90, f"Fetching files ({elapsed:.1f}s)")
    
    if not files or files.get("status") != "success":
        log_info("Failed to get file list")
        progress.show_error("Failed to get file list")
        progress.close()
        return None

    content = files.get("content", [])
    video_files = [
        f for f in content
        if f.get("link") and f.get("link").endswith((".mp4", ".mkv", ".avi"))
    ]
    
    if not video_files:
        log_info("No video files found")
        progress.show_error("No video files found")
        progress.close()
        return None

    largest_file = sorted(video_files, key=lambda x: int(x.get("size", 0)), reverse=True)[0]
    if largest_file.get("stream_link") and largest_file.get("transcode_status") in ["finished", "good_as_is"]:
        stream_url = largest_file["stream_link"]
        log_info("Using transcoded stream")
    else:
        stream_url = largest_file["link"]
        log_info("Using direct link")

    progress.show_success(largest_file)
    progress.close()
    return stream_url

def get_mime_type(url):
    extension = url.lower().split('.')[-1]
    mime_types = {
        'mp4': 'video/mp4',
        'mkv': 'video/x-matroska',
        'avi': 'video/x-msvideo'
    }
    return mime_types.get(extension, 'video/mp4')

def get_direct_download(api_key, magnet):
    url = "https://www.premiumize.me/api/transfer/directdl"
    params = {"apikey": api_key, "src": magnet}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        log_info(f"Direct download check failed: {str(e)}")
        return None

def create_transfer(api_key, magnet):
    url = "https://www.premiumize.me/api/transfer/create"
    params = {"apikey": api_key, "src": magnet}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        log_info(f"Create transfer failed: {str(e)}")
        return None

def check_transfer_status(api_key, transfer_id):
    url = "https://www.premiumize.me/api/transfer/list"
    params = {"apikey": api_key}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        transfers = data.get("transfers", [])
        return next((t for t in transfers if t.get("id") == transfer_id), None)
    except Exception as e:
        log_info(f"Check transfer status failed: {str(e)}")
        return None

def get_files(api_key, transfer_id):
    url = "https://www.premiumize.me/api/folder/list"
    params = {"apikey": api_key, "id": transfer_id}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        log_info(f"Get files failed: {str(e)}")
        return None

def play_movie(link):
    log_info(f"Starting playback for link: {link}")
    
    try:
        xbmc.executebuiltin('ActivateWindow(busydialog)')
        magnet_links = fetch_magnet_link(link)
        xbmc.executebuiltin('Dialog.Close(busydialog)')
        
        if not magnet_links:
            log_info("No magnet links found in post")
            xbmcgui.Dialog().ok("Error", "No magnet links found in the post. Please try another movie.")
            return
        
        options = []
        for m in magnet_links:
            desc = m['description']
            desc = re.sub(r'(\d+)\.\d+\s*GB', r'\1GB', desc)
            desc = desc.replace(' - ', ' ')
            info = m['info'].replace(' | ', '|') if m['info'] else ''
            if len(desc) + len(info) < 25:
                option = f"{desc} {info}".strip()
            else:
                desc = desc[:15]
                info = info[:15] if info else ''
                option = f"{desc}\n{info}".strip()
            options.append(option)
        
        dialog = xbmcgui.Dialog()
        selected = dialog.select("Choose Quality", options)
        
        if selected < 0:
            log_info("User canceled quality selection")
            return
            
        magnet_link = magnet_links[selected]["link"]
        log_info(f"Selected magnet link: {magnet_link[:60]}...")
        
        xbmc.executebuiltin('ActivateWindow(busydialog)')
        stream_url = resolve_with_premiumize(magnet_link)
        
        if not stream_url:
            xbmc.executebuiltin('Dialog.Close(busydialog)')
            log_info("No stream_url resolved")
            xbmcgui.Dialog().ok("Error", "Failed to resolve stream URL. Check your Premiumize API key or internet connection.")
            return
            
        api_key = ADDON.getSetting("premiumize_api_key")
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = requests.head(stream_url, timeout=5, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code != 200:
                    log_info(f"Invalid stream_url: HTTP {response.status_code}")
                    xbmcgui.Dialog().ok("Error", f"Stream URL is invalid: HTTP {response.status_code}. Please try again.")
                    xbmc.executebuiltin('Dialog.Close(busydialog)')
                    return
                log_info(f"Stream_url validated: {stream_url}")
                content_type = response.headers.get('Content-Type', '')
                mime_type = content_type.split(';')[0] if content_type else get_mime_type(stream_url)
                log_info(f"Determined MIME type: {mime_type}")
                break
            except requests.exceptions.SSLError as e:
                log_info(f"SSL error during validation, attempting with verify=False: {str(e)}")
                try:
                    response = requests.head(stream_url, timeout=5, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
                    if response.status_code != 200:
                        log_info(f"Invalid stream_url with verify=False: HTTP {response.status_code}")
                        xbmcgui.Dialog().ok("Error", f"Stream URL is invalid: HTTP {response.status_code}. Please try again.")
                        xbmc.executebuiltin('Dialog.Close(busydialog)')
                        return
                    log_info(f"Stream_url validated with verify=False: {stream_url}")
                    content_type = response.headers.get('Content-Type', '')
                    mime_type = content_type.split(';')[0] if content_type else get_mime_type(stream_url)
                    log_info(f"Determined MIME type with verify=False: {mime_type}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        log_info(f"Retrying stream_url validation ({attempt + 1}/{max_retries}): {str(e)}")
                        xbmc.sleep(2000)
                        continue
                    log_info(f"Stream_url validation failed after retries: {str(e)}")
                    retry = xbmcgui.Dialog().yesno("Error", f"Failed to validate stream URL: {str(e)}\nRetry?", yeslabel="Retry", nolabel="Cancel")
                    if retry:
                        play_movie(link)
                        return
                    xbmc.executebuiltin('Dialog.Close(busydialog)')
                    return
            except Exception as e:
                if attempt < max_retries - 1:
                    log_info(f"Retrying stream_url validation ({attempt + 1}/{max_retries}): {str(e)}")
                    xbmc.sleep(2000)
                    continue
                log_info(f"Stream_url validation failed after retries: {str(e)}")
                retry = xbmcgui.Dialog().yesno("Error", f"Failed to validate stream URL: {str(e)}\nRetry?", yeslabel="Retry", nolabel="Cancel")
                if retry:
                    play_movie(link)
                    return
                xbmc.executebuiltin('Dialog.Close(busydialog)')
                return
        
        play_item = xbmcgui.ListItem(path=stream_url)
        play_item.setProperty('IsPlayable', 'true')
        play_item.setInfo('video', {'mediatype': 'video', 'title': 'Stream'})
        play_item.setMimeType(mime_type)
        headers = {'User-Agent': 'Mozilla/5.0'}
        stream_url_with_headers = f"{stream_url}|{'&'.join(f'{k}={urllib.parse.quote(v)}' for k, v in headers.items())}"
        play_item.setPath(stream_url_with_headers)
        
        xbmc.executebuiltin('Dialog.Close(busydialog)')
        log_info(f"Attempting playback with stream_url: {stream_url}, MIME type: {mime_type}")
        xbmcplugin.setResolvedUrl(HANDLE, True, play_item)
        
        xbmc.sleep(2000)
        if not xbmc.Player().isPlaying():
            log_info("Playback did not start, retrying with xbmc.Player")
            try:
                xbmc.Player().play(stream_url_with_headers, play_item)
                xbmc.sleep(2000)
                if not xbmc.Player().isPlaying():
                    log_info("Fallback playback failed")
                    retry = xbmcgui.Dialog().yesno("Error", "Playback failed: Unable to start stream.\nRetry?", yeslabel="Retry", nolabel="Cancel")
                    if retry:
                        play_movie(link)
                        return
            except Exception as e:
                log_info(f"Fallback playback error: {str(e)}")
                retry = xbmcgui.Dialog().yesno("Error", f"Playback failed: {str(e)}\nRetry?", yeslabel="Retry", nolabel="Cancel")
                if retry:
                    play_movie(link)
                    return
        
    except Exception as e:
        xbmc.executebuiltin('Dialog.Close(busydialog)')
        log_info(f"Playback error: {str(e)}")
        xbmcgui.Dialog().ok("Error", f"Playback failed: {str(e)}. Please check your internet connection or try another movie.")
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())

def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring[1:]))
    log_info(f"Router params: {params}")
    
    if params:
        if params['action'] == 'play':
            play_movie(params['link'])
        elif params['action'] == 'list':
            language = params.get('language')
            quality_type = params.get('quality_type')
            page = int(params.get('page', 1))
            list_movies(language, quality_type, page)
        elif params['action'] == 'select_quality':
            language = params.get('language')
            show_quality_menu(language)
        elif params['action'] == 'main_menu':
            show_main_menu()
    else:
        # Always show the main menu when no parameters are provided
        show_main_menu()

if __name__ == '__main__':
    router(sys.argv[2])