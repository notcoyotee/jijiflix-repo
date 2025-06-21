# JijiFlix - Kodi Video Addon

## Overview
JijiFlix is a Kodi video addon that provides access to movies in multiple Indian languages through a forum-based content aggregation system. The addon supports high-quality video streaming with Premiumize integration for torrent resolution.

## Key Features

### 1. Multi-Language Support
- Malayalam
- Tamil
- Telugu
- Hindi
- Kannada

### 2. Quality Categories
- WEB-HD / iTunes-HD / BluRay
- PreDVD / DVDScr / CAM / TC

### 3. Movie Browsing
- Paginated movie listings
- Thumbnail previews
- Year information extraction
- Quality and size information display
- Next page navigation

### 4. Playback Features
- Multiple quality options per movie
- Video format detection (4K, 1080p, 720p, 480p)
- Codec information (HEVC/x265, x264, HDR)
- File size display in GB

### 5. Context Menu Options
- Play Movie
- Play Trailer (YouTube integration)
- Back to Main Menu

### 6. Premiumize Integration
- API key configuration
- Direct download attempt
- Torrent transfer management
- Progress monitoring
- Stream URL resolution
- Transcoding support

### 7. Technical Features
- Concurrent processing for faster loading
- SSL/TLS support with fallback mechanisms
- MIME type detection
- User-Agent handling
- HTML parsing with BeautifulSoup4
  * Forum post extraction
  * Title and link parsing
  * Pagination detection
  * Error handling for malformed HTML
  * Custom SSL Context Handling:
    * Implements a custom `SSLContextAdapter` to handle servers with outdated or non-standard SSL/TLS configurations.
    * Uses `ssl.PROTOCOL_SSLv23` for broader compatibility, ensuring the addon can connect to a wider range of servers.
- Error handling and retry mechanisms
- Progress dialogs
- Extensive logging

## User Interface Flow
1. Main Menu (Language Selection)
2. Quality Type Selection
3. Movie Listing with Thumbnails
4. Quality Selection Dialog
5. Playback with Progress Monitoring

## Error Handling
- SSL certificate verification issues
- Network connectivity problems
- Invalid stream URLs
- Premiumize API errors
- Playback failures

## Configuration
- Premiumize API key setting
- Forum domain configuration

## Dependencies
- Python standard libraries
- Requests
- BeautifulSoup4
- Kodi Python API
- YouTube addon (for trailers)

## Performance Considerations
- Concurrent processing limited to 5 workers
- Multiple retry attempts for stream validation
- Caching of magnet links
- Progress monitoring with cancellation support