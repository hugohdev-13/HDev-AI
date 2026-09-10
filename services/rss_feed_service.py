from dataclasses import dataclass
from datetime import datetime,timezone
from html import unescape
import ipaddress,re,socket
from urllib.parse import urljoin, urlparse
import feedparser,requests
from dtos.rss_entry_dto import RSSEntryDTO
from repositories.source_repository import SourceRepository
@dataclass
class RSSFeedResult:
    success:bool; entries:list; feed_title:str|None; fetched_at:datetime; error_code:str|None=None; message:str|None=None
class RSSFeedService:
    @staticmethod
    def safe_url(url):
        p=urlparse(url)
        if p.scheme not in ('http','https') or not p.hostname: raise ValueError('URL bloqueada por seguridad.')
        if p.hostname.lower()=='localhost': raise ValueError('URL bloqueada por seguridad.')
        for x in {i[4][0] for i in socket.getaddrinfo(p.hostname,None)}:
            i=ipaddress.ip_address(x)
            if i.is_private or i.is_loopback or i.is_link_local or i.is_unspecified: raise ValueError('URL bloqueada por seguridad.')
        return url
    @staticmethod
    def fetch_feed(url):
        current_url = RSSFeedService.safe_url(url)
        for _ in range(4):
            response = requests.get(
                current_url,
                timeout=10,
                allow_redirects=False,
                headers={'User-Agent': 'HDevAI-RSS/1.0'},
            )
            if response.status_code not in {301, 302, 303, 307, 308}:
                response.raise_for_status()
                return response.content[:2_000_000]
            location = response.headers.get('Location')
            if not location:
                raise requests.RequestException('RSS redirect did not include a location.')
            current_url = RSSFeedService.safe_url(urljoin(current_url, location))
        raise requests.RequestException('RSS feed exceeded the redirect limit.')
    @staticmethod
    def parse_feed(content,limit=20):
        p=feedparser.parse(content)
        if p.bozo and not p.entries: raise ValueError('Feed inválido.')
        out=[]
        for e in p.entries[:min(max(limit,1),50)]:
            summary=re.sub(r'\s+',' ',re.sub(r'<[^>]*>',' ',unescape(e.get('summary','')))).strip() or None; d=e.get('published_parsed') or e.get('updated_parsed'); date=datetime(*d[:6],tzinfo=timezone.utc) if d else None; media=e.get('media_content') or e.get('media_thumbnail') or []
            out.append(RSSEntryDTO(e.get('title','Sin título'),e.get('link'),e.get('id') or e.get('guid'),summary,e.get('author'),date,media[0].get('url') if media else None))
        return p.feed.get('title'),out
    @staticmethod
    def get_entries(source,limit=20):
        now=datetime.now(timezone.utc).replace(tzinfo=None)
        try:
            if source is None: raise ValueError('Fuente no encontrada.')
            if source.source_type!='rss': raise ValueError('La fuente no es de tipo RSS.')
            if not source.is_active: raise ValueError('La fuente está inactiva.')
            if not source.feed_url: raise ValueError('La fuente no tiene feed URL.')
            title,entries=RSSFeedService.parse_feed(RSSFeedService.fetch_feed(source.feed_url),limit);source.last_synced_at=now;source.last_sync_status='success';source.last_sync_message=f'{len(entries)} entradas detectadas.';SourceRepository.save(source);return RSSFeedResult(True,entries,title,now,message='Feed leído correctamente.')
        except (ValueError,requests.RequestException,socket.gaierror) as e:
            if source is not None: source.last_synced_at=now;source.last_sync_status='failed';source.last_sync_message=str(e)[:500];SourceRepository.save(source)
            return RSSFeedResult(False,[],None,now,'rss_error','No fue posible leer el feed RSS.')
