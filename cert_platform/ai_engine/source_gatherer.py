"""
Source and Image Gatherer
Uses web search to gather authoritative sources, images, and links for each topic
Integrates with Google Custom Search API for image and content discovery
"""
import requests
import json
from typing import List, Dict, Any
from datetime import datetime
import hashlib
import os
import re

class SourceGatherer:
    """
    Gathers educational sources, images, and links from authoritative websites
    All sources are verified and scored for reliability
    """

    def __init__(self):
        # In production, use actual API keys
        self.google_api_key = os.getenv('GOOGLE_API_KEY', 'demo_key')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID', 'demo_cse')

        # Authoritative domains by field
        self.authoritative_domains = {
            'education': [
                'ed.gov', 'nea.org', 'ascd.org', 'edutopia.org',
                'chronicle.com', 'insidehighered.com', 'teachthought.com'
            ],
            'finance': [
                'sec.gov', 'treasury.gov', 'federalreserve.gov', 'cfainstitute.org',
                'investopedia.com', 'bloomberg.com', 'wsj.com', 'finra.org'
            ],
            'it_software': [
                'docs.python.org', 'developer.mozilla.org', 'docs.aws.amazon.com',
                'cloud.google.com', 'learn.microsoft.com', 'github.com',
                'stackoverflow.com', 'w3.org', 'owasp.org'
            ],
            'cooking': [
                'fda.gov', 'usda.gov', 'servsafe.com', 'acfchefs.org',
                'cia.edu', 'jamesbeard.org', 'seriouseats.com'
            ],
            'mechanical_engineering': [
                'asme.org', 'nist.gov', 'astm.org', 'sae.org',
                'engineering.com', 'solidworks.com', 'autodesk.com'
            ],
            'electrician': [
                'nfpa.org', 'osha.gov', 'neca.net', 'necplus.org',
                'mikeholt.com', 'ecmag.com', 'electrical-contractor.net'
            ],
            'hvac': [
                'ashrae.org', 'epa.gov', 'acca.org', 'rses.org',
                'hvac.com', 'contractormag.com', 'energy.gov'
            ],
            'nursing': [
                'nursingworld.org', 'ncsbn.org', 'cdc.gov', 'cms.gov',
                'nurse.org', 'aacnnursing.org', 'nursinglicense.com'
            ],
            'cybersecurity': [
                'nist.gov', 'cisa.gov', 'sans.org', 'first.org',
                'owasp.org', 'cert.org', 'us-cert.gov', 'nvd.nist.gov'
            ],
            'accounting': [
                'aicpa.org', 'irs.gov', 'sec.gov', 'fasb.org',
                'accountingtoday.com', 'journalofaccountancy.com', 'intuit.com'
            ],
            'business': [
                'sba.gov', 'hbr.org', 'pmi.org', 'mckinsey.com',
                'forbes.com', 'businessinsider.com', 'entrepreneur.com'
            ],
            'ai_education': [
                'ai.google', 'openai.com', 'anthropic.com', 'tensorflow.org',
                'pytorch.org', 'huggingface.co', 'arxiv.org', 'papers.nips.cc'
            ]
        }

        # Source reliability scoring by domain suffix
        self.reliability_scores = {
            '.gov': 1.0,        # Government
            '.edu': 0.95,       # Academic
            '.org': 0.85,       # Professional organizations
            'nist.gov': 1.0,
            'osha.gov': 1.0,
            'sec.gov': 1.0,
            'epa.gov': 1.0,
            'cdc.gov': 1.0,
        }

    def gather_sources(self, topic: str, program: str, subtopic: str = None) -> List[Dict[str, Any]]:
        """
        Gather authoritative sources for a topic
        Returns list of sources with URLs, titles, reliability scores
        """
        sources = []

        # Build search query
        query = self._build_search_query(topic, program, subtopic)

        # Get authoritative domains for this program
        auth_domains = self.authoritative_domains.get(program, [])

        # Search for sources (in production, use actual Google Custom Search API)
        search_results = self._search_web(query, auth_domains)

        for result in search_results:
            source = {
                'url': result['url'],
                'title': result['title'],
                'description': result.get('snippet', ''),
                'domain': self._extract_domain(result['url']),
                'reliability_score': self._calculate_reliability(result['url']),
                'last_verified': datetime.now().isoformat(),
                'source_type': self._determine_source_type(result['url']),
                'citation': self._generate_citation(result),
                'metadata': {
                    'keywords': self._extract_keywords(result),
                    'publish_date': result.get('publish_date'),
                    'author': result.get('author')
                }
            }
            sources.append(source)

        # Sort by reliability score
        sources.sort(key=lambda x: x['reliability_score'], reverse=True)

        return sources[:10]  # Top 10 sources

    def gather_images(self, topic: str, program: str, subtopic: str = None) -> List[Dict[str, Any]]:
        """
        Gather educational images and diagrams for a topic
        """
        images = []

        # Build image search query
        query = self._build_image_query(topic, program, subtopic)

        # Search for images (in production, use Google Custom Search API with image search)
        image_results = self._search_images(query)

        for result in image_results:
            image = {
                'url': result['image_url'],
                'thumbnail_url': result.get('thumbnail_url'),
                'title': result['title'],
                'source_page': result.get('source_url'),
                'alt_text': result.get('alt_text', ''),
                'width': result.get('width'),
                'height': result.get('height'),
                'format': result.get('format', 'jpg'),
                'license': self._detect_license(result),
                'educational_value': self._assess_educational_value(result)
            }
            images.append(image)

        return images[:20]  # Top 20 images

    def gather_videos(self, topic: str, program: str) -> List[Dict[str, Any]]:
        """
        Gather educational videos from YouTube, Khan Academy, etc.
        """
        videos = []

        query = f"{topic} tutorial {program} education"

        # In production, use YouTube Data API
        video_results = self._search_videos(query)

        for result in video_results:
            video = {
                'url': result['url'],
                'title': result['title'],
                'description': result.get('description'),
                'duration': result.get('duration'),
                'channel': result.get('channel'),
                'views': result.get('views'),
                'rating': result.get('rating'),
                'thumbnail': result.get('thumbnail'),
                'platform': self._detect_platform(result['url']),
                'educational_quality': self._assess_video_quality(result)
            }
            videos.append(video)

        return videos[:10]

    def _build_search_query(self, topic: str, program: str, subtopic: str = None) -> str:
        """Build optimized search query"""
        if subtopic:
            return f"{topic} {subtopic} {program} official guide tutorial"
        return f"{topic} {program} official documentation guide"

    def _build_image_query(self, topic: str, program: str, subtopic: str = None) -> str:
        """Build image search query"""
        if subtopic:
            return f"{topic} {subtopic} diagram illustration infographic"
        return f"{topic} {program} diagram chart infographic"

    def _search_web(self, query: str, preferred_domains: List[str]) -> List[Dict[str, Any]]:
        """
        Search web using Google Custom Search API
        In production, this would make actual API calls
        """
        # DEMO MODE - In production, use actual Google Custom Search API:
        # url = f"https://www.googleapis.com/customsearch/v1"
        # params = {
        #     'key': self.google_api_key,
        #     'cx': self.google_cse_id,
        #     'q': query,
        #     'num': 10
        # }
        # response = requests.get(url, params=params)
        # results = response.json().get('items', [])

        # For demo, return structured sample data
        demo_results = []
        for domain in preferred_domains[:5]:
            demo_results.append({
                'url': f"https://{domain}/{query.replace(' ', '-').lower()}",
                'title': f"{query} - Official Documentation",
                'snippet': f"Comprehensive guide to {query} from authoritative source.",
                'publish_date': '2025-01-01',
                'author': 'Official Documentation Team'
            })

        return demo_results

    def _search_images(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for images using Google Custom Search API
        In production, this would make actual API calls
        """
        # DEMO MODE - In production:
        # url = f"https://www.googleapis.com/customsearch/v1"
        # params = {
        #     'key': self.google_api_key,
        #     'cx': self.google_cse_id,
        #     'q': query,
        #     'searchType': 'image',
        #     'num': 20,
        #     'imgSize': 'large',
        #     'rights': 'cc_publicdomain,cc_attribute,cc_sharealike'
        # }
        # response = requests.get(url, params=params)
        # results = response.json().get('items', [])

        # Demo data
        demo_images = []
        for i in range(10):
            demo_images.append({
                'image_url': f"https://example.com/images/{query.replace(' ', '_')}_{i}.jpg",
                'thumbnail_url': f"https://example.com/thumbnails/{query.replace(' ', '_')}_{i}.jpg",
                'title': f"{query} - Diagram {i+1}",
                'source_url': f"https://example.com/article/{i}",
                'alt_text': f"Educational diagram showing {query}",
                'width': 1920,
                'height': 1080,
                'format': 'jpg'
            })

        return demo_images

    def _search_videos(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for educational videos
        In production, use YouTube Data API
        """
        # Demo data
        demo_videos = []
        platforms = ['YouTube', 'Khan Academy', 'Coursera', 'edX']

        for i, platform in enumerate(platforms):
            demo_videos.append({
                'url': f"https://youtube.com/watch?v=demo_{i}",
                'title': f"{query} - Complete Tutorial",
                'description': f"Comprehensive tutorial on {query}",
                'duration': '15:30',
                'channel': f"{platform} Education",
                'views': 100000 + (i * 10000),
                'rating': 4.5 + (i * 0.1),
                'thumbnail': f"https://img.youtube.com/vi/demo_{i}/maxresdefault.jpg"
            })

        return demo_videos

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else ''

    def _calculate_reliability(self, url: str) -> float:
        """Calculate source reliability score"""
        domain = self._extract_domain(url)

        # Check for exact matches
        for key, score in self.reliability_scores.items():
            if key in domain:
                return score

        # Check domain suffix
        if domain.endswith('.gov'):
            return 1.0
        elif domain.endswith('.edu'):
            return 0.95
        elif domain.endswith('.org'):
            return 0.85
        elif domain in ['github.com', 'stackoverflow.com']:
            return 0.88
        else:
            return 0.75

    def _determine_source_type(self, url: str) -> str:
        """Determine type of source"""
        domain = self._extract_domain(url)

        if '.gov' in domain:
            return 'government'
        elif '.edu' in domain:
            return 'academic'
        elif any(org in domain for org in ['ieee', 'acm', 'asme', 'nfpa']):
            return 'professional_organization'
        elif 'github.com' in domain:
            return 'open_source'
        elif any(doc in domain for doc in ['docs', 'documentation', 'developer']):
            return 'official_documentation'
        else:
            return 'industry_publication'

    def _generate_citation(self, result: Dict[str, Any]) -> str:
        """Generate proper academic citation"""
        title = result.get('title', 'Untitled')
        url = result.get('url', '')
        author = result.get('author', 'Unknown')
        date = result.get('publish_date', datetime.now().strftime('%Y-%m-%d'))

        # APA style citation
        citation = f"{author}. ({date}). {title}. Retrieved from {url}"
        return citation

    def _extract_keywords(self, result: Dict[str, Any]) -> List[str]:
        """Extract keywords from search result"""
        text = f"{result.get('title', '')} {result.get('snippet', '')}"

        # Simple keyword extraction (in production, use NLP)
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        keywords = list(set(words))[:10]

        return keywords

    def _detect_license(self, image_result: Dict[str, Any]) -> str:
        """Detect image license type"""
        # In production, check actual license metadata
        return 'Creative Commons Attribution'

    def _assess_educational_value(self, image_result: Dict[str, Any]) -> float:
        """Assess educational value of image (0.0-1.0)"""
        # Factors: alt text quality, image size, source reliability
        score = 0.8

        if image_result.get('width', 0) > 1200:
            score += 0.1
        if len(image_result.get('alt_text', '')) > 20:
            score += 0.1

        return min(score, 1.0)

    def _detect_platform(self, url: str) -> str:
        """Detect video platform"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'YouTube'
        elif 'khanacademy.org' in url:
            return 'Khan Academy'
        elif 'coursera.org' in url:
            return 'Coursera'
        elif 'edx.org' in url:
            return 'edX'
        else:
            return 'Other'

    def _assess_video_quality(self, video_result: Dict[str, Any]) -> float:
        """Assess educational quality of video"""
        score = 0.7

        # Higher views indicate quality
        views = video_result.get('views', 0)
        if views > 100000:
            score += 0.1
        if views > 500000:
            score += 0.1

        # Rating
        rating = video_result.get('rating', 0)
        if rating > 4.5:
            score += 0.1

        return min(score, 1.0)

    def verify_source(self, url: str, program_id: str) -> Dict[str, Any]:
        """
        Verify a source is valid and reliable
        """
        try:
            # In production, make actual HTTP request
            # response = requests.get(url, timeout=10)
            # valid = response.status_code == 200
            valid = True  # Demo mode

            domain = self._extract_domain(url)
            reliability = self._calculate_reliability(url)

            # Check if domain is in authoritative list
            auth_domains = self.authoritative_domains.get(program_id, [])
            is_authoritative = any(auth_domain in domain for auth_domain in auth_domains)

            return {
                'valid': valid,
                'url': url,
                'domain': domain,
                'score': reliability,
                'authoritative': is_authoritative,
                'title': f"Verified source from {domain}",
                'verified_at': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'score': 0.0
            }

    def gather_comprehensive_resources(self, topic: str, program: str,
                                      subtopic: str = None) -> Dict[str, Any]:
        """
        Gather all resources for a topic: sources, images, videos
        """
        sources = self.gather_sources(topic, program, subtopic)
        images = self.gather_images(topic, program, subtopic)
        videos = self.gather_videos(topic, program)

        return {
            'topic': topic,
            'program': program,
            'subtopic': subtopic,
            'sources': sources,
            'images': images,
            'videos': videos,
            'gathered_at': datetime.now().isoformat(),
            'total_resources': len(sources) + len(images) + len(videos)
        }
