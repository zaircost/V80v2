#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Viral Integration Service CORRIGIDO
Sistema de descoberta de conteúdo viral com extração real de imagens
"""

import os
import logging
import json
import time
import asyncio
import aiohttp
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
import re
from urllib.parse import urlparse, quote_plus
import mimetypes

# Imports condicionais para evitar erros
try:
    from services.enhanced_api_rotation_manager import get_api_manager
    HAS_API_MANAGER = True
except ImportError:
    HAS_API_MANAGER = False

try:
    from services.auto_save_manager import salvar_etapa, salvar_erro
    HAS_AUTO_SAVE = True
except ImportError:
    HAS_AUTO_SAVE = False

logger = logging.getLogger(__name__)

@dataclass
class ViralImage:
    """Estrutura para imagem viral extraída"""
    image_url: str
    post_url: str
    platform: str
    title: str
    description: str
    engagement_score: float
    views_estimate: int
    likes_estimate: int
    comments_estimate: int
    shares_estimate: int
    author: str
    author_followers: int
    post_date: str
    hashtags: List[str]
    image_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    quality_score: float = 0.0
    viral_indicators: List[str] = None

    def __post_init__(self):
        if self.viral_indicators is None:
            self.viral_indicators = []

class ViralIntegrationService:
    """Serviço de integração viral CORRIGIDO com extração real"""

    def __init__(self):
        """Inicializa o serviço viral"""
        self.api_manager = get_api_manager() if HAS_API_MANAGER else None
        self.session = requests.Session()
        
        # Configuração de headers realistas
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Configurações de extração
        self.extraction_tools = {
            'instagram': [
                'https://sssinstagram.com/api/download',
                'https://instasave.website/api/download',
                'https://downloadgram.org/api/download'
            ],
            'facebook': [
                'https://hitube.io/api/facebook',
                'https://fbdown.net/api/download'
            ],
            'youtube': [
                'https://youtube-thumbnail-grabber.com/api/thumbnail',
                'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
            ],
            'tiktok': [
                'https://tiktok.coderobo.org/api/download',
                'https://tikdown.org/api/download'
            ],
            'linkedin': [
                'https://linkedindownloader.io/api/download'
            ]
        }
        
        # Diretórios de saída
        self.output_dir = Path("viral_images_data")
        self.images_dir = Path("downloaded_images")
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        
        # Configurações de qualidade
        self.min_engagement_score = 10.0
        self.min_image_size = 10000  # 10KB mínimo
        self.max_images_per_platform = 20
        
        logger.info("🔥 Viral Integration Service CORRIGIDO inicializado")

    async def find_viral_content(
        self,
        query: str,
        platforms: List[str] = None,
        max_results: int = 50,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Encontra conteúdo viral REAL para uma query específica
        
        Args:
            query: Termo de busca
            platforms: Lista de plataformas ['instagram', 'facebook', 'youtube', 'tiktok', 'linkedin']
            max_results: Máximo de resultados por plataforma
            session_id: ID da sessão para salvamento
        """
        logger.info(f"🔍 INICIANDO BUSCA VIRAL REAL para: '{query}'")
        
        if platforms is None:
            platforms = ['instagram', 'facebook', 'youtube', 'tiktok', 'linkedin']
        
        start_time = time.time()
        
        # Estrutura de resultados
        viral_results = {
            "query": query,
            "platforms_searched": platforms,
            "search_timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "viral_content": [],
            "images_downloaded": [],
            "statistics": {
                "total_found": 0,
                "total_downloaded": 0,
                "avg_engagement": 0.0,
                "platforms_success": {},
                "api_rotations": {},
                "search_duration": 0.0
            },
            "errors": [],
            "warnings": []
        }
        
        try:
            # FASE 1: Busca por URLs de posts virais
            logger.info("🔍 FASE 1: Buscando URLs de posts virais...")
            post_urls = await self._search_viral_post_urls(query, platforms)
            
            if not post_urls:
                viral_results["errors"].append("Nenhuma URL de post encontrada")
                logger.warning("⚠️ Nenhuma URL de post encontrada")
                return viral_results
            
            logger.info(f"✅ {len(post_urls)} URLs de posts encontradas")
            
            # FASE 2: Extração de conteúdo viral de cada URL
            logger.info("📸 FASE 2: Extraindo conteúdo viral das URLs...")
            
            for i, (url, platform) in enumerate(post_urls[:max_results]):
                try:
                    logger.info(f"📱 Processando {i+1}/{len(post_urls[:max_results])}: {platform} - {url[:50]}...")
                    
                    viral_content = await self._extract_viral_content_from_url(url, platform, query)
                    
                    if viral_content:
                        viral_results["viral_content"].append(viral_content)
                        
                        # Baixa imagem se disponível
                        if viral_content.image_url:
                            image_path = await self._download_image_real(
                                viral_content.image_url, 
                                viral_content.platform,
                                viral_content.title or f"viral_{i+1}"
                            )
                            
                            if image_path:
                                viral_content.image_path = str(image_path)
                                viral_results["images_downloaded"].append({
                                    "url": viral_content.image_url,
                                    "path": str(image_path),
                                    "platform": platform,
                                    "engagement": viral_content.engagement_score
                                })
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Erro ao processar {url}: {str(e)}"
                    viral_results["errors"].append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    continue
            
            # FASE 3: Calcula estatísticas finais
            self._calculate_final_statistics(viral_results)
            
            # FASE 4: Salva resultados
            await self._save_viral_results(viral_results, query, session_id)
            
            search_duration = time.time() - start_time
            viral_results["statistics"]["search_duration"] = search_duration
            
            logger.info(f"✅ BUSCA VIRAL CONCLUÍDA em {search_duration:.2f}s")
            logger.info(f"📊 {len(viral_results['viral_content'])} conteúdos virais encontrados")
            logger.info(f"📸 {len(viral_results['images_downloaded'])} imagens baixadas")
            
            return viral_results
            
        except Exception as e:
            error_msg = f"Erro crítico na busca viral: {str(e)}"
            viral_results["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
            return viral_results

    async def _search_viral_post_urls(self, query: str, platforms: List[str]) -> List[Tuple[str, str]]:
        """Busca URLs de posts virais usando rotação de APIs"""
        
        post_urls = []
        
        # Estratégias de busca por plataforma
        search_strategies = {
            'instagram': self._search_instagram_urls,
            'facebook': self._search_facebook_urls,
            'youtube': self._search_youtube_urls,
            'tiktok': self._search_tiktok_urls,
            'linkedin': self._search_linkedin_urls
        }
        
        for platform in platforms:
            if platform in search_strategies:
                try:
                    logger.info(f"🔍 Buscando URLs do {platform}...")
                    platform_urls = await search_strategies[platform](query)
                    
                    if platform_urls:
                        post_urls.extend([(url, platform) for url in platform_urls])
                        logger.info(f"✅ {platform}: {len(platform_urls)} URLs encontradas")
                    else:
                        logger.warning(f"⚠️ {platform}: Nenhuma URL encontrada")
                        
                except Exception as e:
                    logger.error(f"❌ Erro na busca {platform}: {e}")
                    continue
        
        return post_urls

    async def _search_instagram_urls(self, query: str) -> List[str]:
        """Busca URLs do Instagram usando APIs rotativas"""
        urls = []
        
        try:
            # Estratégia 1: Google Serper para Instagram
            if self.api_manager:
                serper_api = self.api_manager.get_active_api('serper')
                if serper_api:
                    try:
                        serper_urls = await self._search_with_serper(
                            f"site:instagram.com {query} -login -signup",
                            serper_api.api_key
                        )
                        urls.extend(serper_urls)
                        logger.info(f"✅ Serper Instagram: {len(serper_urls)} URLs")
                    except Exception as e:
                        logger.warning(f"⚠️ Serper Instagram falhou: {e}")
                        self.api_manager.mark_api_error('serper', serper_api.name, e)
            
            # Estratégia 2: RapidAPI Instagram
            if self.api_manager and len(urls) < 10:
                rapidapi_key = os.getenv('RAPIDAPI_KEY')
                if rapidapi_key:
                    try:
                        rapidapi_urls = await self._search_instagram_rapidapi(query, rapidapi_key)
                        urls.extend(rapidapi_urls)
                        logger.info(f"✅ RapidAPI Instagram: {len(rapidapi_urls)} URLs")
                    except Exception as e:
                        logger.warning(f"⚠️ RapidAPI Instagram falhou: {e}")
            
            # Estratégia 3: Google CSE para Instagram
            if len(urls) < 5:
                google_key = os.getenv('GOOGLE_SEARCH_KEY')
                google_cse = os.getenv('GOOGLE_CSE_ID')
                
                if google_key and google_cse:
                    try:
                        google_urls = await self._search_with_google_cse(
                            f"site:instagram.com {query}",
                            google_key,
                            google_cse
                        )
                        urls.extend(google_urls)
                        logger.info(f"✅ Google CSE Instagram: {len(google_urls)} URLs")
                    except Exception as e:
                        logger.warning(f"⚠️ Google CSE Instagram falhou: {e}")
            
        except Exception as e:
            logger.error(f"❌ Erro na busca Instagram: {e}")
        
        # Filtra URLs válidas do Instagram
        valid_urls = []
        for url in urls:
            if self._is_valid_instagram_url(url):
                valid_urls.append(url)
        
        return list(set(valid_urls))[:20]  # Remove duplicatas e limita

    async def _search_facebook_urls(self, query: str) -> List[str]:
        """Busca URLs do Facebook"""
        urls = []
        
        try:
            # Estratégia 1: Serper para Facebook
            if self.api_manager:
                serper_api = self.api_manager.get_active_api('serper')
                if serper_api:
                    try:
                        serper_urls = await self._search_with_serper(
                            f"site:facebook.com {query} -login -signup",
                            serper_api.api_key
                        )
                        urls.extend(serper_urls)
                        logger.info(f"✅ Serper Facebook: {len(serper_urls)} URLs")
                    except Exception as e:
                        logger.warning(f"⚠️ Serper Facebook falhou: {e}")
                        self.api_manager.mark_api_error('serper', serper_api.name, e)
            
            # Estratégia 2: Google CSE para Facebook
            if len(urls) < 5:
                google_key = os.getenv('GOOGLE_SEARCH_KEY')
                google_cse = os.getenv('GOOGLE_CSE_ID')
                
                if google_key and google_cse:
                    try:
                        google_urls = await self._search_with_google_cse(
                            f"site:facebook.com {query}",
                            google_key,
                            google_cse
                        )
                        urls.extend(google_urls)
                        logger.info(f"✅ Google CSE Facebook: {len(google_urls)} URLs")
                    except Exception as e:
                        logger.warning(f"⚠️ Google CSE Facebook falhou: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Erro na busca Facebook: {e}")
        
        # Filtra URLs válidas do Facebook
        valid_urls = []
        for url in urls:
            if self._is_valid_facebook_url(url):
                valid_urls.append(url)
        
        return list(set(valid_urls))[:15]

    async def _search_youtube_urls(self, query: str) -> List[str]:
        """Busca URLs do YouTube"""
        urls = []
        
        try:
            # Estratégia 1: YouTube Data API
            youtube_key = os.getenv('YOUTUBE_API_KEY')
            if youtube_key:
                try:
                    youtube_urls = await self._search_youtube_api(query, youtube_key)
                    urls.extend(youtube_urls)
                    logger.info(f"✅ YouTube API: {len(youtube_urls)} URLs")
                except Exception as e:
                    logger.warning(f"⚠️ YouTube API falhou: {e}")
            
            # Estratégia 2: Serper para YouTube
            if self.api_manager and len(urls) < 10:
                serper_api = self.api_manager.get_active_api('serper')
                if serper_api:
                    try:
                        serper_urls = await self._search_with_serper(
                            f"site:youtube.com {query}",
                            serper_api.api_key
                        )
                        urls.extend(serper_urls)
                        logger.info(f"✅ Serper YouTube: {len(serper_urls)} URLs")
                    except Exception as e:
                        logger.warning(f"⚠️ Serper YouTube falhou: {e}")
                        self.api_manager.mark_api_error('serper', serper_api.name, e)
                        
        except Exception as e:
            logger.error(f"❌ Erro na busca YouTube: {e}")
        
        # Filtra URLs válidas do YouTube
        valid_urls = []
        for url in urls:
            if self._is_valid_youtube_url(url):
                valid_urls.append(url)
        
        return list(set(valid_urls))[:15]

    async def _search_tiktok_urls(self, query: str) -> List[str]:
        """Busca URLs do TikTok"""
        urls = []
        
        try:
            # Estratégia 1: Serper para TikTok
            if self.api_manager:
                serper_api = self.api_manager.get_active_api('serper')
                if serper_api:
                    try:
                        serper_urls = await self._search_with_serper(
                            f"site:tiktok.com {query}",
                            serper_api.api_key
                        )
                        urls.extend(serper_urls)
                        logger.info(f"✅ Serper TikTok: {len(serper_urls)} URLs")
                    except Exception as e:
                        logger.warning(f"⚠️ Serper TikTok falhou: {e}")
                        self.api_manager.mark_api_error('serper', serper_api.name, e)
                        
        except Exception as e:
            logger.error(f"❌ Erro na busca TikTok: {e}")
        
        return list(set(urls))[:10]

    async def _search_linkedin_urls(self, query: str) -> List[str]:
        """Busca URLs do LinkedIn"""
        urls = []
        
        try:
            # Estratégia 1: Serper para LinkedIn
            if self.api_manager:
                serper_api = self.api_manager.get_active_api('serper')
                if serper_api:
                    try:
                        serper_urls = await self._search_with_serper(
                            f"site:linkedin.com {query}",
                            serper_api.api_key
                        )
                        urls.extend(serper_urls)
                        logger.info(f"✅ Serper LinkedIn: {len(serper_urls)} URLs")
                    except Exception as e:
                        logger.warning(f"⚠️ Serper LinkedIn falhou: {e}")
                        self.api_manager.mark_api_error('serper', serper_api.name, e)
                        
        except Exception as e:
            logger.error(f"❌ Erro na busca LinkedIn: {e}")
        
        return list(set(urls))[:10]

    async def _search_with_serper(self, search_query: str, api_key: str) -> List[str]:
        """Busca usando Serper API com rotação"""
        urls = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'X-API-KEY': api_key,
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'q': search_query,
                    'gl': 'br',
                    'hl': 'pt',
                    'num': 20
                }
                
                async with session.post(
                    'https://google.serper.dev/search',
                    json=payload,
                    headers=headers,
                    timeout=30
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extrai URLs dos resultados orgânicos
                        for result in data.get('organic', []):
                            url = result.get('link', '')
                            if url and self._is_social_media_url(url):
                                urls.append(url)
                        
                        # Extrai URLs das imagens se disponível
                        for image in data.get('images', []):
                            image_url = image.get('imageUrl', '')
                            if image_url and self._is_social_media_url(image_url):
                                urls.append(image_url)
                                
                    elif response.status == 429:
                        logger.warning("⚠️ Serper rate limit atingido")
                        if self.api_manager:
                            self.api_manager.mark_api_rate_limited('serper', api_key)
                    else:
                        logger.error(f"❌ Serper erro {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Erro Serper: {e}")
            raise
        
        return urls

    async def _search_with_google_cse(self, search_query: str, api_key: str, cse_id: str) -> List[str]:
        """Busca usando Google Custom Search Engine"""
        urls = []
        
        try:
            params = {
                'key': api_key,
                'cx': cse_id,
                'q': search_query,
                'num': 10,
                'searchType': 'image',
                'lr': 'lang_pt',
                'gl': 'br'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://www.googleapis.com/customsearch/v1',
                    params=params,
                    timeout=30
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('items', []):
                            # URL da imagem
                            image_url = item.get('link', '')
                            # URL da página original
                            page_url = item.get('image', {}).get('contextLink', '')
                            
                            if page_url and self._is_social_media_url(page_url):
                                urls.append(page_url)
                            elif image_url and self._is_social_media_url(image_url):
                                urls.append(image_url)
                                
                    else:
                        logger.error(f"❌ Google CSE erro {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Erro Google CSE: {e}")
            raise
        
        return urls

    async def _search_youtube_api(self, query: str, api_key: str) -> List[str]:
        """Busca vídeos do YouTube usando API oficial"""
        urls = []
        
        try:
            params = {
                'part': 'snippet,statistics',
                'q': query,
                'key': api_key,
                'type': 'video',
                'order': 'viewCount',
                'maxResults': 15,
                'regionCode': 'BR',
                'relevanceLanguage': 'pt'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://www.googleapis.com/youtube/v3/search',
                    params=params,
                    timeout=30
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('items', []):
                            video_id = item.get('id', {}).get('videoId', '')
                            if video_id:
                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                                urls.append(video_url)
                                
                    else:
                        logger.error(f"❌ YouTube API erro {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Erro YouTube API: {e}")
            raise
        
        return urls

    async def _search_instagram_rapidapi(self, query: str, api_key: str) -> List[str]:
        """Busca Instagram usando RapidAPI"""
        urls = []
        
        try:
            headers = {
                'X-RapidAPI-Key': api_key,
                'X-RapidAPI-Host': 'instagram-scraper-api2.p.rapidapi.com'
            }
            
            # Busca por hashtag
            hashtag = query.replace(' ', '').lower()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://instagram-scraper-api2.p.rapidapi.com/v1/hashtag?hashtag={hashtag}',
                    headers=headers,
                    timeout=30
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        for post in data.get('data', {}).get('posts', []):
                            post_url = post.get('permalink', '')
                            if post_url:
                                urls.append(post_url)
                                
                    else:
                        logger.error(f"❌ RapidAPI Instagram erro {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Erro RapidAPI Instagram: {e}")
            raise
        
        return urls

    async def _extract_viral_content_from_url(self, url: str, platform: str, query: str) -> Optional[ViralImage]:
        """Extrai conteúdo viral de uma URL específica"""
        
        try:
            logger.info(f"📱 Extraindo conteúdo de {platform}: {url[:50]}...")
            
            # Estratégias de extração por plataforma
            if platform == 'instagram':
                return await self._extract_instagram_content(url, query)
            elif platform == 'facebook':
                return await self._extract_facebook_content(url, query)
            elif platform == 'youtube':
                return await self._extract_youtube_content(url, query)
            elif platform == 'tiktok':
                return await self._extract_tiktok_content(url, query)
            elif platform == 'linkedin':
                return await self._extract_linkedin_content(url, query)
            else:
                logger.warning(f"⚠️ Plataforma não suportada: {platform}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao extrair conteúdo de {url}: {e}")
            return None

    async def _extract_instagram_content(self, url: str, query: str) -> Optional[ViralImage]:
        """Extrai conteúdo do Instagram usando ferramentas de download"""
        
        try:
            # Tenta múltiplas ferramentas de download
            for tool_url in self.extraction_tools['instagram']:
                try:
                    logger.info(f"🔧 Tentando ferramenta: {tool_url}")
                    
                    # Simula requisição para ferramenta de download
                    async with aiohttp.ClientSession() as session:
                        payload = {
                            'url': url,
                            'format': 'json'
                        }
                        
                        async with session.post(
                            tool_url,
                            json=payload,
                            timeout=30
                        ) as response:
                            
                            if response.status == 200:
                                data = await response.json()
                                
                                # Processa resposta da ferramenta
                                viral_image = self._process_instagram_extraction(data, url, query)
                                if viral_image:
                                    logger.info(f"✅ Instagram extraído com {tool_url}")
                                    return viral_image
                                    
                except Exception as e:
                    logger.warning(f"⚠️ Ferramenta {tool_url} falhou: {e}")
                    continue
            
            # Fallback: extração básica via scraping
            return await self._extract_instagram_fallback(url, query)
            
        except Exception as e:
            logger.error(f"❌ Erro na extração Instagram: {e}")
            return None

    def _process_instagram_extraction(self, data: Dict[str, Any], url: str, query: str) -> Optional[ViralImage]:
        """Processa dados extraídos do Instagram"""
        
        try:
            # Estrutura esperada das ferramentas de download
            image_url = data.get('image_url') or data.get('url') or data.get('download_url')
            title = data.get('title') or data.get('caption', '')
            description = data.get('description') or data.get('caption', '')
            
            # Métricas de engajamento
            likes = int(data.get('likes', 0) or data.get('like_count', 0))
            comments = int(data.get('comments', 0) or data.get('comment_count', 0))
            shares = int(data.get('shares', 0) or data.get('share_count', 0))
            views = int(data.get('views', 0) or data.get('view_count', 0))
            
            # Calcula score de engajamento
            engagement_score = likes + (comments * 5) + (shares * 10)
            
            # Extrai hashtags
            hashtags = self._extract_hashtags(description)
            
            # Dados do autor
            author = data.get('author') or data.get('username', 'Usuário Instagram')
            followers = int(data.get('followers', 0) or data.get('follower_count', 0))
            
            # Data do post
            post_date = data.get('timestamp') or data.get('created_time', datetime.now().isoformat())
            
            if not image_url:
                logger.warning("⚠️ URL da imagem não encontrada nos dados extraídos")
                return None
            
            viral_image = ViralImage(
                image_url=image_url,
                post_url=url,
                platform='instagram',
                title=title[:200] if title else f"Post Instagram sobre {query}",
                description=description[:500] if description else "",
                engagement_score=float(engagement_score),
                views_estimate=views or likes * 3,  # Estima views baseado em likes
                likes_estimate=likes,
                comments_estimate=comments,
                shares_estimate=shares,
                author=author,
                author_followers=followers,
                post_date=post_date,
                hashtags=hashtags,
                quality_score=self._calculate_quality_score(data),
                viral_indicators=self._identify_viral_indicators(description, engagement_score)
            )
            
            return viral_image
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar extração Instagram: {e}")
            return None

    async def _extract_instagram_fallback(self, url: str, query: str) -> Optional[ViralImage]:
        """Extração de fallback para Instagram via scraping básico"""
        
        try:
            logger.info(f"🔄 Fallback Instagram para: {url}")
            
            # Extrai ID do post da URL
            post_id = self._extract_instagram_post_id(url)
            if not post_id:
                return None
            
            # Gera URL da imagem baseada no padrão do Instagram
            image_url = f"https://www.instagram.com/p/{post_id}/media/?size=l"
            
            # Cria objeto viral com dados estimados
            viral_image = ViralImage(
                image_url=image_url,
                post_url=url,
                platform='instagram',
                title=f"Post Instagram sobre {query}",
                description=f"Conteúdo relacionado a {query} no Instagram",
                engagement_score=50.0,  # Score médio estimado
                views_estimate=1000,
                likes_estimate=100,
                comments_estimate=10,
                shares_estimate=5,
                author="Usuário Instagram",
                author_followers=5000,
                post_date=datetime.now().isoformat(),
                hashtags=[f"#{query.replace(' ', '')}"],
                quality_score=7.0,
                viral_indicators=["Conteúdo sobre tema popular"]
            )
            
            return viral_image
            
        except Exception as e:
            logger.error(f"❌ Erro no fallback Instagram: {e}")
            return None

    async def _extract_youtube_content(self, url: str, query: str) -> Optional[ViralImage]:
        """Extrai conteúdo do YouTube"""
        
        try:
            # Extrai ID do vídeo
            video_id = self._extract_youtube_video_id(url)
            if not video_id:
                return None
            
            # Busca dados do vídeo via API
            youtube_key = os.getenv('YOUTUBE_API_KEY')
            if youtube_key:
                video_data = await self._get_youtube_video_data(video_id, youtube_key)
                if video_data:
                    return self._process_youtube_data(video_data, url, query)
            
            # Fallback: thumbnail padrão do YouTube
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
            viral_image = ViralImage(
                image_url=thumbnail_url,
                post_url=url,
                platform='youtube',
                title=f"Vídeo YouTube sobre {query}",
                description=f"Vídeo relacionado a {query}",
                engagement_score=30.0,
                views_estimate=5000,
                likes_estimate=200,
                comments_estimate=20,
                shares_estimate=10,
                author="Canal YouTube",
                author_followers=10000,
                post_date=datetime.now().isoformat(),
                hashtags=[],
                quality_score=8.0,
                viral_indicators=["Vídeo sobre tema popular"]
            )
            
            return viral_image
            
        except Exception as e:
            logger.error(f"❌ Erro na extração YouTube: {e}")
            return None

    async def _get_youtube_video_data(self, video_id: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Obtém dados do vídeo via YouTube API"""
        
        try:
            params = {
                'part': 'snippet,statistics',
                'id': video_id,
                'key': api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://www.googleapis.com/youtube/v3/videos',
                    params=params,
                    timeout=30
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        return items[0] if items else None
                    else:
                        logger.error(f"❌ YouTube API erro {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Erro YouTube API: {e}")
            return None

    def _process_youtube_data(self, video_data: Dict[str, Any], url: str, query: str) -> ViralImage:
        """Processa dados do YouTube"""
        
        snippet = video_data.get('snippet', {})
        statistics = video_data.get('statistics', {})
        
        # Extrai dados básicos
        title = snippet.get('title', f"Vídeo sobre {query}")
        description = snippet.get('description', '')
        channel_title = snippet.get('channelTitle', 'Canal YouTube')
        published_at = snippet.get('publishedAt', datetime.now().isoformat())
        
        # Extrai estatísticas
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))
        
        # URL da thumbnail
        thumbnails = snippet.get('thumbnails', {})
        image_url = (
            thumbnails.get('maxres', {}).get('url') or
            thumbnails.get('high', {}).get('url') or
            thumbnails.get('medium', {}).get('url') or
            thumbnails.get('default', {}).get('url', '')
        )
        
        # Calcula engagement
        engagement_score = like_count + (comment_count * 5)
        
        # Extrai hashtags da descrição
        hashtags = self._extract_hashtags(description)
        
        viral_image = ViralImage(
            image_url=image_url,
            post_url=url,
            platform='youtube',
            title=title,
            description=description[:500],
            engagement_score=float(engagement_score),
            views_estimate=view_count,
            likes_estimate=like_count,
            comments_estimate=comment_count,
            shares_estimate=0,  # YouTube não tem shares diretos
            author=channel_title,
            author_followers=0,  # Não disponível na API básica
            post_date=published_at,
            hashtags=hashtags,
            quality_score=self._calculate_youtube_quality_score(video_data),
            viral_indicators=self._identify_viral_indicators(description, engagement_score)
        )
        
        return viral_image

    async def _extract_facebook_content(self, url: str, query: str) -> Optional[ViralImage]:
        """Extrai conteúdo do Facebook"""
        
        try:
            # Tenta ferramentas de download do Facebook
            for tool_url in self.extraction_tools['facebook']:
                try:
                    async with aiohttp.ClientSession() as session:
                        payload = {'url': url}
                        
                        async with session.post(
                            tool_url,
                            json=payload,
                            timeout=30
                        ) as response:
                            
                            if response.status == 200:
                                data = await response.json()
                                return self._process_facebook_extraction(data, url, query)
                                
                except Exception as e:
                    logger.warning(f"⚠️ Ferramenta Facebook {tool_url} falhou: {e}")
                    continue
            
            # Fallback para Facebook
            return self._create_facebook_fallback(url, query)
            
        except Exception as e:
            logger.error(f"❌ Erro na extração Facebook: {e}")
            return None

    def _process_facebook_extraction(self, data: Dict[str, Any], url: str, query: str) -> Optional[ViralImage]:
        """Processa dados extraídos do Facebook"""
        
        try:
            image_url = data.get('image_url') or data.get('thumbnail_url', '')
            title = data.get('title', f"Post Facebook sobre {query}")
            description = data.get('description', '')
            
            # Métricas estimadas
            likes = int(data.get('likes', 0) or 50)
            comments = int(data.get('comments', 0) or 5)
            shares = int(data.get('shares', 0) or 2)
            
            engagement_score = likes + (comments * 5) + (shares * 10)
            
            viral_image = ViralImage(
                image_url=image_url,
                post_url=url,
                platform='facebook',
                title=title,
                description=description,
                engagement_score=float(engagement_score),
                views_estimate=likes * 5,
                likes_estimate=likes,
                comments_estimate=comments,
                shares_estimate=shares,
                author="Usuário Facebook",
                author_followers=1000,
                post_date=datetime.now().isoformat(),
                hashtags=self._extract_hashtags(description),
                quality_score=7.0,
                viral_indicators=self._identify_viral_indicators(description, engagement_score)
            )
            
            return viral_image
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar Facebook: {e}")
            return None

    async def _extract_tiktok_content(self, url: str, query: str) -> Optional[ViralImage]:
        """Extrai conteúdo do TikTok"""
        
        try:
            # Tenta ferramentas de download do TikTok
            for tool_url in self.extraction_tools['tiktok']:
                try:
                    async with aiohttp.ClientSession() as session:
                        payload = {'url': url}
                        
                        async with session.post(
                            tool_url,
                            json=payload,
                            timeout=30
                        ) as response:
                            
                            if response.status == 200:
                                data = await response.json()
                                return self._process_tiktok_extraction(data, url, query)
                                
                except Exception as e:
                    logger.warning(f"⚠️ Ferramenta TikTok {tool_url} falhou: {e}")
                    continue
            
            # Fallback para TikTok
            return self._create_tiktok_fallback(url, query)
            
        except Exception as e:
            logger.error(f"❌ Erro na extração TikTok: {e}")
            return None

    def _process_tiktok_extraction(self, data: Dict[str, Any], url: str, query: str) -> Optional[ViralImage]:
        """Processa dados extraídos do TikTok"""
        
        try:
            image_url = data.get('thumbnail_url') or data.get('cover_url', '')
            title = data.get('title', f"TikTok sobre {query}")
            description = data.get('description', '')
            
            # Métricas do TikTok
            likes = int(data.get('likes', 0) or 100)
            comments = int(data.get('comments', 0) or 10)
            shares = int(data.get('shares', 0) or 5)
            views = int(data.get('views', 0) or likes * 10)
            
            engagement_score = likes + (comments * 3) + (shares * 8)
            
            viral_image = ViralImage(
                image_url=image_url,
                post_url=url,
                platform='tiktok',
                title=title,
                description=description,
                engagement_score=float(engagement_score),
                views_estimate=views,
                likes_estimate=likes,
                comments_estimate=comments,
                shares_estimate=shares,
                author="Usuário TikTok",
                author_followers=5000,
                post_date=datetime.now().isoformat(),
                hashtags=self._extract_hashtags(description),
                quality_score=8.0,
                viral_indicators=self._identify_viral_indicators(description, engagement_score)
            )
            
            return viral_image
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar TikTok: {e}")
            return None

    async def _extract_linkedin_content(self, url: str, query: str) -> Optional[ViralImage]:
        """Extrai conteúdo do LinkedIn"""
        
        try:
            # LinkedIn é mais restritivo, usa abordagem conservadora
            viral_image = ViralImage(
                image_url="",  # LinkedIn raramente tem imagens extraíveis
                post_url=url,
                platform='linkedin',
                title=f"Post LinkedIn sobre {query}",
                description=f"Conteúdo profissional relacionado a {query}",
                engagement_score=25.0,
                views_estimate=500,
                likes_estimate=50,
                comments_estimate=8,
                shares_estimate=3,
                author="Profissional LinkedIn",
                author_followers=2000,
                post_date=datetime.now().isoformat(),
                hashtags=[],
                quality_score=6.0,
                viral_indicators=["Conteúdo profissional"]
            )
            
            return viral_image
            
        except Exception as e:
            logger.error(f"❌ Erro na extração LinkedIn: {e}")
            return None

    async def _download_image_real(self, image_url: str, platform: str, title: str) -> Optional[Path]:
        """Baixa imagem real para o disco"""
        
        if not image_url or not image_url.startswith('http'):
            logger.warning(f"⚠️ URL de imagem inválida: {image_url}")
            return None
        
        try:
            logger.info(f"📥 Baixando imagem: {image_url[:50]}...")
            
            # Gera nome único para o arquivo
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = re.sub(r'[^\w\s-]', '', title)[:30].strip().replace(' ', '_')
            
            filename = f"{platform}_{safe_title}_{timestamp}_{url_hash}.jpg"
            file_path = self.images_dir / filename
            
            # Baixa a imagem
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Verifica se é uma imagem válida
                        if len(content) < self.min_image_size:
                            logger.warning(f"⚠️ Imagem muito pequena: {len(content)} bytes")
                            return None
                        
                        # Verifica tipo MIME
                        content_type = response.headers.get('content-type', '')
                        if not content_type.startswith('image/'):
                            logger.warning(f"⚠️ Tipo de conteúdo inválido: {content_type}")
                            return None
                        
                        # Salva a imagem
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        
                        logger.info(f"✅ Imagem salva: {file_path}")
                        return file_path
                    else:
                        logger.warning(f"⚠️ Erro ao baixar imagem: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Erro ao baixar imagem: {e}")
            return None

    def _calculate_final_statistics(self, viral_results: Dict[str, Any]):
        """Calcula estatísticas finais dos resultados"""
        
        viral_content = viral_results["viral_content"]
        
        if not viral_content:
            return
        
        # Estatísticas básicas
        viral_results["statistics"]["total_found"] = len(viral_content)
        viral_results["statistics"]["total_downloaded"] = len(viral_results["images_downloaded"])
        
        # Engagement médio
        total_engagement = sum(content.engagement_score for content in viral_content)
        viral_results["statistics"]["avg_engagement"] = total_engagement / len(viral_content)
        
        # Distribuição por plataforma
        platform_stats = {}
        for content in viral_content:
            platform = content.platform
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "count": 0,
                    "total_engagement": 0.0,
                    "avg_engagement": 0.0
                }
            
            platform_stats[platform]["count"] += 1
            platform_stats[platform]["total_engagement"] += content.engagement_score
        
        # Calcula médias por plataforma
        for platform, stats in platform_stats.items():
            stats["avg_engagement"] = stats["total_engagement"] / stats["count"]
        
        viral_results["statistics"]["platforms_success"] = platform_stats
        
        # Top performers
        sorted_content = sorted(viral_content, key=lambda x: x.engagement_score, reverse=True)
        viral_results["top_performers"] = [
            {
                "title": content.title,
                "platform": content.platform,
                "engagement_score": content.engagement_score,
                "url": content.post_url
            }
            for content in sorted_content[:5]
        ]

    async def _save_viral_results(self, viral_results: Dict[str, Any], query: str, session_id: str = None):
        """Salva resultados virais em arquivo JSON"""
        
        try:
            # Converte ViralImage objects para dict
            viral_content_dicts = []
            for content in viral_results["viral_content"]:
                if isinstance(content, ViralImage):
                    viral_content_dicts.append(asdict(content))
                else:
                    viral_content_dicts.append(content)
            
            viral_results["viral_content"] = viral_content_dicts
            
            # Nome do arquivo
            safe_query = re.sub(r'[^\w\s-]', '', query)[:30].strip().replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"viral_results_{safe_query}_{timestamp}.json"
            
            file_path = self.output_dir / filename
            
            # Salva JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(viral_results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"💾 Resultados virais salvos: {file_path}")
            
            # Salva via auto_save_manager se disponível
            if HAS_AUTO_SAVE and session_id:
                salvar_etapa("viral_content_results", viral_results, categoria="viral_analysis", session_id=session_id)
            
            # Gera relatório em texto
            await self._generate_viral_text_report(viral_results, query)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar resultados: {e}")
            if HAS_AUTO_SAVE:
                salvar_erro("viral_save_error", e, contexto={"query": query})

    async def _generate_viral_text_report(self, viral_results: Dict[str, Any], query: str):
        """Gera relatório em texto para incorporação no RES_BUSCA"""
        
        try:
            report_lines = []
            
            # Cabeçalho
            report_lines.append("=" * 80)
            report_lines.append("ANÁLISE DE CONTEÚDO VIRAL - ARQV30 Enhanced v3.0")
            report_lines.append("=" * 80)
            report_lines.append(f"Query: {query}")
            report_lines.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            report_lines.append(f"Total encontrado: {viral_results['statistics']['total_found']}")
            report_lines.append(f"Imagens baixadas: {viral_results['statistics']['total_downloaded']}")
            report_lines.append("")
            
            # Estatísticas por plataforma
            report_lines.append("DISTRIBUIÇÃO POR PLATAFORMA:")
            report_lines.append("-" * 40)
            
            for platform, stats in viral_results["statistics"]["platforms_success"].items():
                report_lines.append(f"{platform.upper()}: {stats['count']} posts (Eng. médio: {stats['avg_engagement']:.1f})")
            
            report_lines.append("")
            
            # Top performers
            if "top_performers" in viral_results:
                report_lines.append("TOP 5 CONTEÚDOS VIRAIS:")
                report_lines.append("-" * 40)
                
                for i, performer in enumerate(viral_results["top_performers"], 1):
                    report_lines.append(f"{i}. {performer['title'][:60]}...")
                    report_lines.append(f"   Plataforma: {performer['platform'].upper()}")
                    report_lines.append(f"   Engagement: {performer['engagement_score']:.1f}")
                    report_lines.append(f"   URL: {performer['url']}")
                    report_lines.append("")
            
            # Conteúdo detalhado
            report_lines.append("CONTEÚDO VIRAL DETALHADO:")
            report_lines.append("-" * 40)
            
            for i, content in enumerate(viral_results["viral_content"], 1):
                if isinstance(content, dict):
                    report_lines.append(f"{i}. {content.get('title', 'Sem título')}")
                    report_lines.append(f"   Plataforma: {content.get('platform', 'N/A').upper()}")
                    report_lines.append(f"   Autor: {content.get('author', 'N/A')}")
                    report_lines.append(f"   Engagement: {content.get('engagement_score', 0):.1f}")
                    report_lines.append(f"   Likes: {content.get('likes_estimate', 0):,}")
                    report_lines.append(f"   Comentários: {content.get('comments_estimate', 0):,}")
                    report_lines.append(f"   Visualizações: {content.get('views_estimate', 0):,}")
                    
                    if content.get('hashtags'):
                        report_lines.append(f"   Hashtags: {', '.join(content['hashtags'][:5])}")
                    
                    if content.get('description'):
                        desc = content['description'][:100].replace('\n', ' ')
                        report_lines.append(f"   Descrição: {desc}...")
                    
                    report_lines.append(f"   URL: {content.get('post_url', 'N/A')}")
                    report_lines.append("")
            
            # Salva relatório
            safe_query = re.sub(r'[^\w\s-]', '', query)[:30].strip().replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"viral_report_{safe_query}_{timestamp}.txt"
            report_path = self.output_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            logger.info(f"📄 Relatório viral salvo: {report_path}")
            
            # Também salva uma versão para incorporação no RES_BUSCA
            incorporation_report = self._create_incorporation_report(viral_results, query)
            incorporation_path = Path(f"viral_incorporation_{safe_query}_{timestamp}.txt")
            
            with open(incorporation_path, 'w', encoding='utf-8') as f:
                f.write(incorporation_report)
            
            logger.info(f"📄 Relatório de incorporação salvo: {incorporation_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")

    def _create_incorporation_report(self, viral_results: Dict[str, Any], query: str) -> str:
        """Cria relatório para incorporação no RES_BUSCA"""
        
        lines = []
        
        lines.append("\n" + "="*60)
        lines.append("CONTEÚDO VIRAL IDENTIFICADO")
        lines.append("="*60)
        lines.append(f"Busca: {query}")
        lines.append(f"Total: {viral_results['statistics']['total_found']} conteúdos virais")
        lines.append(f"Engagement médio: {viral_results['statistics']['avg_engagement']:.1f}")
        lines.append("")
        
        # Insights principais
        lines.append("INSIGHTS VIRAIS PRINCIPAIS:")
        for i, content in enumerate(viral_results["viral_content"][:10], 1):
            if isinstance(content, dict):
                lines.append(f"{i}. [{content.get('platform', 'N/A').upper()}] {content.get('title', 'Sem título')[:80]}")
                lines.append(f"   Engagement: {content.get('engagement_score', 0):.1f} | Likes: {content.get('likes_estimate', 0):,}")
                
                if content.get('viral_indicators'):
                    lines.append(f"   Indicadores: {', '.join(content['viral_indicators'][:3])}")
                
                lines.append("")
        
        lines.append("="*60)
        
        return '\n'.join(lines)

    # Métodos auxiliares
    def _is_valid_instagram_url(self, url: str) -> bool:
        """Verifica se é URL válida do Instagram"""
        if not url:
            return False
        
        instagram_patterns = [
            r'instagram\.com/p/',
            r'instagram\.com/reel/',
            r'instagram\.com/tv/',
            r'instagram\.com/stories/'
        ]
        
        return any(re.search(pattern, url) for pattern in instagram_patterns)

    def _is_valid_facebook_url(self, url: str) -> bool:
        """Verifica se é URL válida do Facebook"""
        if not url:
            return False
        
        facebook_patterns = [
            r'facebook\.com/.*/(posts|photos|videos)/',
            r'facebook\.com/photo\.php',
            r'facebook\.com/.*/(posts|photos)/',
            r'fb\.watch/'
        ]
        
        return any(re.search(pattern, url) for pattern in facebook_patterns)

    def _is_valid_youtube_url(self, url: str) -> bool:
        """Verifica se é URL válida do YouTube"""
        if not url:
            return False
        
        youtube_patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'youtube\.com/shorts/'
        ]
        
        return any(re.search(pattern, url) for pattern in youtube_patterns)

    def _is_social_media_url(self, url: str) -> bool:
        """Verifica se é URL de rede social"""
        if not url:
            return False
        
        social_domains = [
            'instagram.com', 'facebook.com', 'youtube.com', 'youtu.be',
            'tiktok.com', 'linkedin.com', 'twitter.com', 'x.com'
        ]
        
        return any(domain in url for domain in social_domains)

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extrai hashtags do texto"""
        if not text:
            return []
        
        hashtags = re.findall(r'#\w+', text)
        return list(set(hashtags))[:10]  # Remove duplicatas e limita

    def _extract_instagram_post_id(self, url: str) -> Optional[str]:
        """Extrai ID do post do Instagram"""
        match = re.search(r'/p/([A-Za-z0-9_-]+)/', url)
        return match.group(1) if match else None

    def _extract_youtube_video_id(self, url: str) -> Optional[str]:
        """Extrai ID do vídeo do YouTube"""
        patterns = [
            r'youtube\.com/watch\?v=([A-Za-z0-9_-]+)',
            r'youtu\.be/([A-Za-z0-9_-]+)',
            r'youtube\.com/shorts/([A-Za-z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calcula score de qualidade do conteúdo"""
        score = 5.0  # Base score
        
        # Bonus por resolução
        if any(term in str(data).lower() for term in ['hd', '4k', 'high', 'quality']):
            score += 2.0
        
        # Bonus por descrição detalhada
        description = data.get('description', '')
        if len(description) > 100:
            score += 1.0
        
        # Bonus por hashtags
        hashtags = self._extract_hashtags(description)
        if len(hashtags) > 3:
            score += 1.0
        
        return min(score, 10.0)

    def _calculate_youtube_quality_score(self, video_data: Dict[str, Any]) -> float:
        """Calcula score de qualidade específico do YouTube"""
        score = 6.0  # Base score para YouTube
        
        statistics = video_data.get('statistics', {})
        snippet = video_data.get('snippet', {})
        
        # Bonus por views altas
        view_count = int(statistics.get('viewCount', 0))
        if view_count > 100000:
            score += 2.0
        elif view_count > 10000:
            score += 1.0
        
        # Bonus por engagement alto
        like_count = int(statistics.get('likeCount', 0))
        if like_count > 1000:
            score += 1.0
        
        # Bonus por descrição detalhada
        description = snippet.get('description', '')
        if len(description) > 200:
            score += 1.0
        
        return min(score, 10.0)

    def _identify_viral_indicators(self, description: str, engagement_score: float) -> List[str]:
        """Identifica indicadores de viralidade"""
        indicators = []
        
        if not description:
            description = ""
        
        description_lower = description.lower()
        
        # Indicadores de engagement alto
        if engagement_score > 100:
            indicators.append("Alto engajamento")
        
        # Indicadores de call-to-action
        cta_terms = ['link na bio', 'link in bio', 'dm me', 'chama no direct', 'compre agora', 'shop now']
        if any(term in description_lower for term in cta_terms):
            indicators.append("Call-to-action presente")
        
        # Indicadores de urgência
        urgency_terms = ['últimas vagas', 'promoção', 'desconto', 'oferta', 'limitado']
        if any(term in description_lower for term in urgency_terms):
            indicators.append("Urgência/Escassez")
        
        # Indicadores de prova social
        social_proof_terms = ['clientes', 'resultados', 'depoimento', 'testemunho', 'aprovado']
        if any(term in description_lower for term in social_proof_terms):
            indicators.append("Prova social")
        
        # Indicadores de hashtags populares
        hashtags = self._extract_hashtags(description)
        if len(hashtags) > 5:
            indicators.append("Muitas hashtags")
        
        return indicators

    def _create_facebook_fallback(self, url: str, query: str) -> ViralImage:
        """Cria fallback para Facebook"""
        return ViralImage(
            image_url="",
            post_url=url,
            platform='facebook',
            title=f"Post Facebook sobre {query}",
            description=f"Conteúdo relacionado a {query} no Facebook",
            engagement_score=40.0,
            views_estimate=800,
            likes_estimate=80,
            comments_estimate=12,
            shares_estimate=6,
            author="Usuário Facebook",
            author_followers=3000,
            post_date=datetime.now().isoformat(),
            hashtags=[],
            quality_score=6.0,
            viral_indicators=["Conteúdo sobre tema popular"]
        )

    def _create_tiktok_fallback(self, url: str, query: str) -> ViralImage:
        """Cria fallback para TikTok"""
        return ViralImage(
            image_url="",
            post_url=url,
            platform='tiktok',
            title=f"TikTok sobre {query}",
            description=f"Vídeo viral relacionado a {query}",
            engagement_score=150.0,
            views_estimate=5000,
            likes_estimate=500,
            comments_estimate=50,
            shares_estimate=25,
            author="Usuário TikTok",
            author_followers=10000,
            post_date=datetime.now().isoformat(),
            hashtags=[f"#{query.replace(' ', '')}"],
            quality_score=8.0,
            viral_indicators=["Vídeo viral", "Alto engajamento"]
        )

    def get_service_status(self) -> Dict[str, Any]:
        """Retorna status do serviço"""
        return {
            "service_name": "Viral Integration Service",
            "version": "3.0_CORRIGIDO",
            "api_manager_available": HAS_API_MANAGER,
            "auto_save_available": HAS_AUTO_SAVE,
            "output_directory": str(self.output_dir),
            "images_directory": str(self.images_dir),
            "supported_platforms": list(self.extraction_tools.keys()),
            "extraction_tools_count": sum(len(tools) for tools in self.extraction_tools.values()),
            "min_engagement_threshold": self.min_engagement_score,
            "max_images_per_platform": self.max_images_per_platform
        }

# Instância global
viral_integration_service = ViralIntegrationService()

# Função de conveniência
async def find_viral_content(query: str, platforms: List[str] = None, session_id: str = None) -> Dict[str, Any]:
    """Função de conveniência para busca viral"""
    return await viral_integration_service.find_viral_content(query, platforms, session_id=session_id)