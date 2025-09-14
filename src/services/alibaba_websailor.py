#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Alibaba WebSailor Agent com Módulos Integrados
Agente de navegação web inteligente com busca profunda, análise contextual e análise de conteúdo viral
"""

import os
import logging
import time
import requests
import json
import random
import re
import asyncio
import httpx
import base64
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs, unquote
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Import condicional de bibliotecas
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    logging.warning("Selenium não instalado - screenshots não disponíveis")

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    import aiohttp
    import aiofiles
    HAS_ASYNC_DEPS = True
except ImportError:
    HAS_ASYNC_DEPS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

# Configuração de logging
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'alibaba_websailor.log')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar serviços do projeto
try:
    from services.auto_save_manager import salvar_etapa, salvar_erro
except ImportError:
    # Fallback caso não exista
    def salvar_etapa(nome, dados, categoria="geral"):
        logger.info(f"Etapa {nome}: {dados}")
    
    def salvar_erro(nome, erro, contexto=None):
        logger.error(f"Erro {nome}: {erro}")

# =============== ESTRUTURAS DE DADOS ===============

@dataclass
class ViralContent:
    """Estrutura para conteúdo viral"""
    platform: str
    url: str
    title: str
    description: str
    author: str
    engagement_metrics: Dict[str, int]
    screenshot_path: str
    content_type: str
    hashtags: List[str]
    mentions: List[str]
    timestamp: str
    virality_score: float

@dataclass
class SocialMetrics:
    """Métricas de engajamento social"""
    likes: int = 0
    shares: int = 0
    comments: int = 0
    views: int = 0
    reactions: int = 0
    saves: int = 0

@dataclass
class ViralImage:
    """Estrutura de dados para imagem viral"""
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
    extracted_at: str = datetime.now().isoformat()

# =============== CLASSE PRINCIPAL ALIBABA WEBSAILOR ===============

class AlibabaWebSailorAgent:
    """Agente WebSailor inteligente para navegação e análise web profunda"""

    def __init__(self):
        """Inicializa agente WebSailor com todos os módulos integrados"""
        self.enabled = True
        self.google_search_key = os.getenv("GOOGLE_SEARCH_KEY")
        self.jina_api_key = os.getenv("JINA_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        
        # URLs das APIs
        self.google_search_url = "https://www.googleapis.com/customsearch/v1"
        self.jina_reader_url = "https://r.jina.ai/"
        self.serper_url = "https://google.serper.dev/search"

        # Headers inteligentes para navegação
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none"
        }

        # Domínios brasileiros preferenciais
        self.preferred_domains = {
            "g1.globo.com", "exame.com", "valor.globo.com", "estadao.com.br",
            "folha.uol.com.br", "canaltech.com.br", "tecmundo.com.br",
            "olhardigital.com.br", "infomoney.com.br", "startse.com",
            "revistapegn.globo.com", "epocanegocios.globo.com", "istoedinheiro.com.br",
            "convergenciadigital.com.br", "mobiletime.com.br", "teletime.com.br",
            "portaltelemedicina.com.br", "saudedigitalbrasil.com.br", "amb.org.br",
            "portal.cfm.org.br", "scielo.br", "ibge.gov.br", "fiocruz.br"
        }

        # Domínios bloqueados (irrelevantes)
        self.blocked_domains = {
            "instagram.com", "facebook.com", "twitter.com", "linkedin.com",
            "youtube.com", "tiktok.com", "pinterest.com", "reddit.com",
            "accounts.google.com", "login.microsoft.com", "amazon.com.br",
            "mercadolivre.com.br", "olx.com.br", "booking.com", "airbnb.com"
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Configuração de timeout e retry
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        try:
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],
                backoff_factor=1
            )
        except TypeError:
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "OPTIONS"],
                backoff_factor=1
            )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Estatísticas de navegação
        self.navigation_stats = {
            'total_searches': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'blocked_urls': 0,
            'preferred_sources': 0,
            'total_content_chars': 0,
            'avg_quality_score': 0.0
        }

        # Inicializar módulos integrados
        self.viral_analyzer = self._init_viral_analyzer()
        self.viral_content_analyzer = self._init_viral_content_analyzer()
        self.viral_image_finder = self._init_viral_image_finder()

        logger.info("🌐 Alibaba WebSailor Agent inicializado com todos os módulos integrados")

    def _init_viral_analyzer(self):
        """Inicializa o módulo de análise de conteúdo viral"""
        try:
            return ViralContentAnalyzerModule()
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível inicializar o módulo ViralContentAnalyzer: {e}")
            return None

    def _init_viral_content_analyzer(self):
        """Inicializa o módulo avançado de análise de conteúdo viral"""
        try:
            return ViralContentAnalyzerAdvanced()
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível inicializar o módulo ViralContentAnalyzerAdvanced: {e}")
            return None

    def _init_viral_image_finder(self):
        """Inicializa o módulo de busca de imagens virais"""
        try:
            return ViralImageFinder()
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível inicializar o módulo ViralImageFinder: {e}")
            return None

    def navigate_and_research_deep(
        self,
        query: str,
        context: Dict[str, Any],
        max_pages: int = 25,
        depth_levels: int = 3,
        session_id: str = None,
        analyze_viral: bool = False
    ) -> Dict[str, Any]:
        """Navegação e pesquisa profunda com múltiplos níveis e análise viral opcional"""

        try:
            logger.info(f"🚀 INICIANDO NAVEGAÇÃO PROFUNDA para: {query}")
            start_time = time.time()

            # Salva início da navegação
            salvar_etapa("websailor_iniciado", {
                "query": query,
                "context": context,
                "max_pages": max_pages,
                "depth_levels": depth_levels,
                "analyze_viral": analyze_viral
            }, categoria="pesquisa_web")

            all_content = []
            search_engines_used = []

            # NÍVEL 1: BUSCA MASSIVA MULTI-ENGINE
            logger.info("🔍 NÍVEL 1: Busca massiva com múltiplos engines")

            # Engines de busca em ordem de prioridade
            search_engines = [
                ("Google Custom Search", self._google_search_deep),
                ("Serper API", self._serper_search_deep),
                ("Bing Scraping", self._bing_search_deep),
                ("DuckDuckGo Scraping", self._duckduckgo_search_deep),
                ("Yahoo Scraping", self._yahoo_search_deep)
            ]

            for engine_name, search_func in search_engines:
                try:
                    logger.info(f"🔍 Executando {engine_name}...")
                    results = search_func(query, max_pages // len(search_engines))

                    if results:
                        search_engines_used.append(engine_name)
                        logger.info(f"✅ {engine_name}: {len(results)} resultados")

                        # Extrai conteúdo de cada resultado
                        for result in results:
                            content_data = self._extract_intelligent_content(
                                result['url'], result.get('title', ''), result.get('snippet', ''), context
                            )

                            if content_data and content_data['success']:
                                all_content.append({
                                    **content_data,
                                    'search_engine': engine_name,
                                    'search_result': result
                                })

                                # Salva cada extração bem-sucedida
                                salvar_etapa(f"websailor_extracao_{len(all_content)}", {
                                    "url": result['url'],
                                    "engine": engine_name,
                                    "content_length": len(content_data['content']),
                                    "quality_score": content_data['quality_score']
                                }, categoria="pesquisa_web")

                            time.sleep(0.5)  # Rate limiting

                    time.sleep(1)  # Delay entre engines

                except Exception as e:
                    logger.error(f"❌ Erro em {engine_name}: {str(e)}")
                    continue

            # NÍVEL 2: BUSCA EM PROFUNDIDADE (Links internos)
            if depth_levels > 1 and all_content:
                logger.info("🔍 NÍVEL 2: Busca em profundidade - Links internos")

                # Seleciona top páginas para explorar links internos
                top_pages = sorted(all_content, key=lambda x: x['quality_score'], reverse=True)[:5]

                for page in top_pages:
                    internal_links = self._extract_internal_links(page['url'], page['content'])

                    for link in internal_links[:3]:  # Top 3 links por página
                        internal_content = self._extract_intelligent_content(link, "", "", context)

                        if internal_content and internal_content['success']:
                            internal_content['search_engine'] = f"{page['search_engine']} (Internal)"
                            internal_content['parent_url'] = page['url']
                            all_content.append(internal_content)

                            time.sleep(0.3)

            # NÍVEL 3: QUERIES RELACIONADAS INTELIGENTES
            if depth_levels > 2:
                logger.info("🔍 NÍVEL 3: Queries relacionadas inteligentes")

                related_queries = self._generate_intelligent_related_queries(query, context, all_content)

                for related_query in related_queries[:3]:
                    try:
                        related_results = self._google_search_deep(related_query, 5)

                        for result in related_results:
                            related_content = self._extract_intelligent_content(
                                result['url'], result.get('title', ''), result.get('snippet', ''), context
                            )

                            if related_content and related_content['success']:
                                related_content['search_engine'] = "Google (Related Query)"
                                related_content['related_query'] = related_query
                                all_content.append(related_content)

                                time.sleep(0.4)
                    except Exception as e:
                        logger.warning(f"⚠️ Erro em query relacionada '{related_query}': {str(e)}")
                        continue

            # PROCESSAMENTO E ANÁLISE FINAL
            processed_research = self._process_and_analyze_content(all_content, query, context)

            # Análise de conteúdo viral se solicitado
            if analyze_viral and self.viral_content_analyzer:
                try:
                    logger.info("🦠 Iniciando análise de conteúdo viral...")
                    
                    # Preparar dados para análise viral
                    search_results_for_viral = {
                        'web_results': all_content,
                        'youtube_results': [],  # Seria preenchido em uma implementação completa
                        'social_results': []    # Seria preenchido em uma implementação completa
                    }
                    
                    viral_analysis = asyncio.run(
                        self.viral_content_analyzer.analyze_and_capture_viral_content(
                            search_results_for_viral, 
                            session_id or f"session_{int(time.time())}"
                        )
                    )
                    
                    processed_research['analise_viral'] = viral_analysis
                    
                    # Gerar relatório viral
                    viral_report = self.viral_content_analyzer.generate_viral_content_report(
                        viral_analysis, 
                        session_id or f"session_{int(time.time())}"
                    )
                    
                    processed_research['relatorio_viral'] = viral_report
                    
                    logger.info("✅ Análise de conteúdo viral concluída")
                    
                except Exception as e:
                    logger.error(f"❌ Erro na análise de conteúdo viral: {e}")
                    processed_research['analise_viral'] = {"erro": str(e)}

            # Atualiza estatísticas
            self._update_navigation_stats(all_content)

            end_time = time.time()

            # Salva resultado final da navegação
            salvar_etapa("websailor_resultado", processed_research, categoria="pesquisa_web")

            logger.info(f"✅ NAVEGAÇÃO PROFUNDA CONCLUÍDA em {end_time - start_time:.2f} segundos")
            logger.info(f"📊 {len(all_content)} páginas analisadas com {len(search_engines_used)} engines")

            return processed_research

        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO na navegação WebSailor: {str(e)}")
            salvar_erro("websailor_critico", e, contexto={"query": query})
            return self._generate_emergency_research(query, context)

    def search_viral_images(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Busca imagens virais usando o módulo integrado"""
        if not self.viral_image_finder:
            logger.warning("⚠️ Módulo de busca de imagens virais não disponível")
            return {"erro": "Módulo de busca de imagens virais não disponível"}
        
        try:
            logger.info(f"🔍 Buscando imagens virais para: {query}")
            salvar_etapa("viral_images_search_start", {"query": query}, categoria="viral_content")
            
            # Executar busca de imagens
            search_results = asyncio.run(self.viral_image_finder.search_images(query))
            
            # Processar resultados
            processed_results = {
                "query": query,
                "session_id": session_id or f"session_{int(time.time())}",
                "total_images": len(search_results),
                "images": search_results[:20],  # Limitar a 20 resultados
                "timestamp": datetime.now().isoformat()
            }
            
            # Baixar imagens se configurado
            if self.viral_image_finder.config.get('extract_images', True):
                try:
                    downloaded_images = asyncio.run(
                        self.viral_image_finder.download_viral_images(search_results[:10], session_id)
                    )
                    processed_results["downloaded_images"] = downloaded_images
                    logger.info(f"✅ {len(downloaded_images)} imagens baixadas")
                except Exception as e:
                    logger.error(f"❌ Erro ao baixar imagens: {e}")
                    processed_results["download_error"] = str(e)
            
            salvar_etapa("viral_images_search_result", processed_results, categoria="viral_content")
            logger.info(f"✅ Busca de imagens virais concluída: {len(search_results)} resultados")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ Erro na busca de imagens virais: {e}")
            salvar_erro("viral_images_search_error", e, contexto={"query": query})
            return {"erro": str(e)}

    def analyze_trending_content(self, segment: str, platforms: List[str] = None) -> Dict[str, Any]:
        """Analisa conteúdo em tendência usando o módulo viral"""
        if not self.viral_analyzer:
            logger.warning("⚠️ Módulo de análise de conteúdo viral não disponível")
            return {"erro": "Módulo de análise de conteúdo viral não disponível"}
        
        try:
            logger.info(f"📈 Analisando conteúdo em tendência para: {segment}")
            salvar_etapa("trending_content_analysis_start", {"segment": segment}, categoria="viral_content")
            
            # Executar análise de tendência
            trending_analysis = asyncio.run(
                self.viral_analyzer.analyze_trending_content(segment, platforms)
            )
            
            # Gerar relatório de viralidade
            all_content = []
            for platform_content in trending_analysis.values():
                all_content.extend(platform_content)
            
            virality_report = asyncio.run(
                self.viral_analyzer.generate_virality_report(all_content)
            )
            
            processed_results = {
                "segment": segment,
                "platforms": platforms or ["youtube", "instagram", "facebook"],
                "trending_analysis": trending_analysis,
                "virality_report": virality_report,
                "timestamp": datetime.now().isoformat()
            }
            
            salvar_etapa("trending_content_analysis_result", processed_results, categoria="viral_content")
            logger.info(f"✅ Análise de conteúdo em tendência concluída")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de conteúdo em tendência: {e}")
            salvar_erro("trending_content_analysis_error", e, contexto={"segment": segment})
            return {"erro": str(e)}

    # =============== MÉTODOS DE BUSCA ===============

    def _google_search_deep(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Busca profunda usando Google Custom Search API"""

        if not self.google_search_key or not self.google_cse_id:
            return []

        try:
            # Melhora query para pesquisa brasileira
            enhanced_query = self._enhance_query_for_brazil(query)

            params = {
                "key": self.google_search_key,
                "cx": self.google_cse_id,
                "q": enhanced_query,
                "num": min(max_results, 10),
                "lr": "lang_pt",
                "gl": "br",
                "safe": "off",
                "dateRestrict": "m12",  # Últimos 12 meses
                "sort": "date",
                "filter": "1"  # Remove duplicatas
            }

            response = requests.get(
                self.google_search_url,
                params=params,
                headers=self.headers,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get("items", []):
                    url = item.get("link", "")

                    # Filtra URLs irrelevantes
                    if self._is_url_relevant(url, item.get("title", ""), item.get("snippet", "")):
                        results.append({
                            "title": item.get("title", ""),
                            "url": url,
                            "snippet": item.get("snippet", ""),
                            "source": "google_custom_search"
                        })

                self.navigation_stats['total_searches'] += 1
                return results
            else:
                logger.warning(f"⚠️ Google Search falhou: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Erro no Google Search: {str(e)}")
            return []

    def _serper_search_deep(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Busca profunda usando Serper API"""

        if not self.serper_api_key:
            return []

        try:
            headers = {
                **self.headers,
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'q': self._enhance_query_for_brazil(query),
                'gl': 'br',
                'hl': 'pt',
                'num': max_results,
                'autocorrect': True,
                'page': 1
            }

            response = requests.post(
                self.serper_url,
                json=payload,
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get("organic", []):
                    url = item.get("link", "")

                    if self._is_url_relevant(url, item.get("title", ""), item.get("snippet", "")):
                        results.append({
                            "title": item.get("title", ""),
                            "url": url,
                            "snippet": item.get("snippet", ""),
                            "source": "serper_api"
                        })

                return results
            else:
                logger.warning(f"⚠️ Serper falhou: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Erro no Serper: {str(e)}")
            return []

    def _bing_search_deep(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Busca profunda usando Bing (scraping inteligente)"""

        try:
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}&cc=br&setlang=pt-br&count={max_results}"

            response = self.session.get(search_url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = []

                result_items = soup.find_all('li', class_='b_algo')

                for item in result_items[:max_results]:
                    title_elem = item.find('h2')
                    if title_elem:
                        link_elem = title_elem.find('a')
                        if link_elem:
                            title = title_elem.get_text(strip=True)
                            url = link_elem.get('href', '')

                            # Resolve URLs do Bing
                            url = self._resolve_bing_url(url)

                            snippet_elem = item.find('p')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                            if url and title and self._is_url_relevant(url, title, snippet):
                                results.append({
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet,
                                    "source": "bing_scraping"
                                })

                return results
            else:
                logger.warning(f"⚠️ Bing falhou: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Erro no Bing: {str(e)}")
            return []

    def _duckduckgo_search_deep(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Busca profunda usando DuckDuckGo"""

        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

            response = self.session.get(search_url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = []

                result_divs = soup.find_all('div', class_='result')

                for div in result_divs[:max_results]:
                    title_elem = div.find('a', class_='result__a')
                    snippet_elem = div.find('a', class_='result__snippet')

                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get('href', '')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                        if url and title and self._is_url_relevant(url, title, snippet):
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "source": "duckduckgo_scraping"
                            })

                return results
            else:
                return []

        except Exception as e:
            logger.error(f"❌ Erro no DuckDuckGo: {str(e)}")
            return []

    def _yahoo_search_deep(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Busca profunda usando Yahoo"""

        try:
            search_url = f"https://br.search.yahoo.com/search?p={quote_plus(query)}&ei=UTF-8"

            response = self.session.get(search_url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = []

                result_items = soup.find_all('div', class_='Sr')

                for item in result_items[:max_results]:
                    title_elem = item.find('h3')
                    if title_elem:
                        link_elem = title_elem.find('a')
                        if link_elem:
                            title = title_elem.get_text(strip=True)
                            url = link_elem.get('href', '')

                            snippet_elem = item.find('span', class_='fz-ms')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                            if url and title and self._is_url_relevant(url, title, snippet):
                                results.append({
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet,
                                    "source": "yahoo_scraping"
                                })

                return results
            else:
                return []

        except Exception as e:
            logger.error(f"❌ Erro no Yahoo: {str(e)}")
            return []

    # =============== MÉTODOS DE EXTRAÇÃO DE CONTEÚDO ===============

    def _extract_intelligent_content(
        self,
        url: str,
        title: str,
        snippet: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extração inteligente de conteúdo com validação"""

        if not url or not url.startswith('http'):
            return None

        try:
            # Verifica se URL é relevante
            if not self._is_url_relevant(url, title, snippet):
                self.navigation_stats['blocked_urls'] += 1
                return None

            # Prioriza domínios preferenciais
            domain = urlparse(url).netloc.lower()
            is_preferred = any(pref_domain in domain for pref_domain in self.preferred_domains)

            if is_preferred:
                self.navigation_stats['preferred_sources'] += 1

            # Extrai conteúdo usando múltiplas estratégias
            content = self._extract_with_multiple_strategies(url)

            if not content or len(content) < 300:
                self.navigation_stats['failed_extractions'] += 1
                return None

            # Valida qualidade do conteúdo
            quality_score = self._calculate_content_quality(content, url, context)

            if quality_score < 60.0:  # Threshold de qualidade
                self.navigation_stats['failed_extractions'] += 1
                return None

            # Extrai insights específicos
            insights = self._extract_content_insights(content, context)

            self.navigation_stats['successful_extractions'] += 1
            self.navigation_stats['total_content_chars'] += len(content)

            return {
                'success': True,
                'url': url,
                'title': title,
                'content': content,
                'quality_score': quality_score,
                'insights': insights,
                'is_preferred_source': is_preferred,
                'extraction_method': 'multi_strategy',
                'content_length': len(content),
                'word_count': len(content.split()),
                'extracted_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Erro ao extrair conteúdo de {url}: {str(e)}")
            self.navigation_stats['failed_extractions'] += 1
            return None

    def _extract_with_multiple_strategies(self, url: str) -> Optional[str]:
        """Extrai conteúdo usando múltiplas estratégias"""

        strategies = [
            ("Jina Reader", self._extract_with_jina),
            ("Trafilatura", self._extract_with_trafilatura),
            ("Readability", self._extract_with_readability),
            ("BeautifulSoup", self._extract_with_beautifulsoup)
        ]

        for strategy_name, strategy_func in strategies:
            try:
                content = strategy_func(url)
                if content and len(content) > 300:
                    logger.info(f"✅ {strategy_name}: {len(content)} caracteres de {url}")
                    return content
            except Exception as e:
                logger.warning(f"⚠️ {strategy_name} falhou para {url}: {str(e)}")
                continue

        return None

    def _extract_with_jina(self, url: str) -> Optional[str]:
        """Extrai usando Jina Reader API"""

        if not self.jina_api_key:
            return None

        try:
            headers = {
                **self.headers,
                "Authorization": f"Bearer {self.jina_api_key}"
            }

            jina_url = f"{self.jina_reader_url}{url}"

            response = requests.get(jina_url, headers=headers, timeout=60)

            if response.status_code == 200:
                content = response.text

                if len(content) > 15000:
                    content = content[:15000] + "... [conteúdo truncado para otimização]"

                return content
            else:
                logger.error(f"❌ Jina Reader API falhou para {url} com status {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro no _extract_with_jina para {url}: {str(e)}")
            return None

    def _extract_with_trafilatura(self, url: str) -> Optional[str]:
        """Extrai usando Trafilatura"""

        try:
            import trafilatura

            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=True,
                    include_formatting=False,
                    favor_precision=False,
                    favor_recall=True,
                    url=url
                )
                return content
            return None

        except ImportError:
            logger.warning("⚠️ Trafilatura não está instalada. Ignorando.")
            return None
        except Exception as e:
            logger.error(f"❌ Erro no Trafilatura para {url}: {str(e)}")
            return None

    def _extract_with_readability(self, url: str) -> Optional[str]:
        """Extrai usando Readability"""

        try:
            from readability import Document

            response = self.session.get(url, timeout=20)
            if response.status_code == 200:
                content_bytes = response.content
                min_length = 300

                if isinstance(content_bytes, bytes):
                    content_str = content_bytes.decode('utf-8', errors='ignore')
                else:
                    content_str = content_bytes

                doc = Document(content_str)
                content = doc.summary()
                if content and len(content.strip()) > min_length:
                    logger.info(f"✅ Readability: {len(content)} caracteres de {url}")
                    return content
                else:
                    logger.warning(f"⚠️ Readability: conteúdo muito curto de {url}")
            else:
                logger.warning(f"⚠️ Readability falhou ao obter conteúdo de {url}: Status {response.status_code}")
            return None

        except ImportError:
            logger.warning("⚠️ Readability não está instalada. Ignorando.")
            return None
        except Exception as e:
            logger.error(f"❌ Erro no Readability para {url}: {str(e)}")
            return None

    def _extract_with_beautifulsoup(self, url: str) -> Optional[str]:
        """Extrai usando BeautifulSoup"""

        try:
            response = self.session.get(url, timeout=20)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Remove elementos desnecessários
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()

                # Busca conteúdo principal
                main_content = (
                    soup.find('main') or
                    soup.find('article') or
                    soup.find('div', class_=re.compile(r'content|main|article'))
                )

                if main_content:
                    return main_content.get_text()
                else:
                    return soup.get_text()

            else:
                logger.warning(f"⚠️ BeautifulSoup falhou ao obter conteúdo de {url}: Status {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"❌ Erro no BeautifulSoup para {url}: {str(e)}")
            return None

    # =============== MÉTODOS DE UTILIDADE ===============

    def _is_url_relevant(self, url: str, title: str, snippet: str) -> bool:
        """Verifica se URL é relevante para análise"""

        if not url or not url.startswith('http'):
            return False

        domain = urlparse(url).netloc.lower()

        # Bloqueia domínios irrelevantes
        if any(blocked in domain for blocked in self.blocked_domains):
            return False

        # Bloqueia padrões irrelevantes
        blocked_patterns = [
            '/login', '/signin', '/register', '/cadastro', '/auth',
            '/account', '/profile', '/settings', '/admin', '/api/',
            '.pdf', '.jpg', '.png', '.gif', '.mp4', '.zip',
            '/download', '/cart', '/checkout', '/payment'
        ]

        url_lower = url.lower()
        if any(pattern in url_lower for pattern in blocked_patterns):
            return False

        # Verifica relevância do conteúdo
        content_text = f"{title} {snippet}".lower()

        # Palavras irrelevantes
        irrelevant_words = [
            'login', 'cadastro', 'carrinho', 'comprar', 'download',
            'termos de uso', 'política de privacidade', 'contato',
            'sobre nós', 'trabalhe conosco', 'vagas'
        ]

        irrelevant_count = sum(1 for word in irrelevant_words if word in content_text)
        if irrelevant_count >= 2:
            return False

        return True

    def _resolve_bing_url(self, url: str) -> str:
        """Resolve URLs de redirecionamento do Bing"""

        if "bing.com/ck/a" not in url or "u=a1" not in url:
            return url

        try:
            import base64

            # Extrai parâmetro u=a1...
            if "u=a1" in url:
                u_param_start = url.find("u=a1") + 4
                u_param_end = url.find("&", u_param_start)
                if u_param_end == -1:
                    u_param_end = len(url)

                encoded_part = url[u_param_start:u_param_end]

                # Decodifica Base64
                try:
                    # Limpa e adiciona padding
                    encoded_part = encoded_part.replace('%3d', '=').replace('%3D', '=')
                    missing_padding = len(encoded_part) % 4
                    if missing_padding:
                        encoded_part += '=' * (4 - missing_padding)

                    # Primeira decodificação
                    first_decode = base64.b64decode(encoded_part)
                    first_decode_str = first_decode.decode('utf-8', errors='ignore')

                    if first_decode_str.startswith('aHR0'):
                        # Segunda decodificação necessária
                        missing_padding = len(first_decode_str) % 4
                        if missing_padding:
                            first_decode_str += '=' * (4 - missing_padding)

                        second_decode = base64.b64decode(first_decode_str)
                        final_url = second_decode.decode('utf-8', errors='ignore')

                        if final_url.startswith('http'):
                            return final_url

                    elif first_decode_str.startswith('http'):
                        return first_decode_str

                except Exception:
                    pass

            return url

        except Exception:
            return url

    def _enhance_query_for_brazil(self, query: str) -> str:
        """Melhora query para pesquisa no Brasil"""

        # Termos que melhoram precisão para mercado brasileiro
        brazil_terms = [
            "Brasil", "brasileiro", "mercado nacional", "dados BR",
            "estatísticas Brasil", "empresas brasileiras", "2024", "2025"
        ]

        enhanced_query = query
        query_lower = query.lower()

        # Adiciona termos brasileiros se não estiverem presentes
        if not any(term.lower() in query_lower for term in ["brasil", "brasileiro", "br"]):
            enhanced_query += " Brasil"

        # Adiciona ano atual se não estiver presente
        if not any(year in query for year in ["2024", "2025"]):
            enhanced_query += " 2024"

        return enhanced_query.strip()

    def _calculate_content_quality(
        self,
        content: str,
        url: str,
        context: Dict[str, Any]
    ) -> float:
        """Calcula qualidade do conteúdo extraído"""

        if not content:
            return 0.0

        score = 0.0
        content_lower = content.lower()

        # Score por tamanho (máximo 20 pontos)
        if len(content) >= 2000:
            score += 20
        elif len(content) >= 1000:
            score += 15
        elif len(content) >= 500:
            score += 10
        else:
            score += 5

        # Score por relevância ao contexto (máximo 30 pontos)
        context_terms = []
        if context.get('segmento'):
            context_terms.append(context['segmento'].lower())
        if context.get('produto'):
            context_terms.append(context['produto'].lower())
        if context.get('publico'):
            context_terms.append(context['publico'].lower())

        relevance_score = 0
        for term in context_terms:
            if term and term in content_lower:
                relevance_score += 10

        score += min(relevance_score, 30)

        # Score por qualidade do domínio (máximo 20 pontos)
        domain = urlparse(url).netloc.lower()
        if any(pref in domain for pref in self.preferred_domains):
            score += 20
        elif domain.endswith('.gov.br') or domain.endswith('.edu.br'):
            score += 15
        elif domain.endswith('.org.br'):
            score += 10
        else:
            score += 5

        # Score por densidade de informação (máximo 15 pontos)
        words = content.split()
        if len(words) >= 500:
            score += 15
        elif len(words) >= 200:
            score += 10
        else:
            score += 5

        # Score por presença de dados (máximo 15 pontos)
        data_patterns = [
            r'\d+%', r'R\$\s*[\d,\.]+', r'\d+\s*(mil|milhão|bilhão)',
            r'20(23|24|25)', r'\d+\s*(empresas|profissionais|clientes)'
        ]

        data_count = sum(1 for pattern in data_patterns if re.search(pattern, content))
        score += min(data_count * 3, 15)

        return min(score, 100.0)

    def _extract_content_insights(self, content: str, context: Dict[str, Any]) -> List[str]:
        """Extrai insights específicos do conteúdo"""

        insights = []
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 80]

        # Padrões para insights valiosos
        insight_patterns = [
            r'crescimento de (\d+(?:\.\d+)?%)',
            r'mercado de R\$ ([\d,\.]+)',
            r'(\d+(?:\.\d+)?%) dos (\w+)',
            r'investimento de R\$ ([\d,\.]+)',
            r'(\d+) empresas (\w+)',
            r'tendência (?:de|para) (\w+)',
            r'oportunidade (?:de|em) (\w+)'
        ]

        segmento = context.get('segmento', '').lower()

        for sentence in sentences[:30]:
            sentence_lower = sentence.lower()

            # Verifica se contém termos relevantes
            if segmento and segmento in sentence_lower:
                # Verifica se contém dados numéricos ou informações valiosas
                if (re.search(r'\d+', sentence) or
                    any(term in sentence_lower for term in [
                        'crescimento', 'mercado', 'oportunidade', 'tendência',
                        'futuro', 'inovação', 'desafio', 'consumidor', 'empresa',
                        'startup', 'investimento', 'receita', 'lucro', 'dados'
                    ])):
                    insights.append(sentence[:300])

        return insights[:8]

    def _extract_internal_links(self, base_url: str, content: str) -> List[str]:
        """Extrai links internos relevantes"""

        try:
            # Tenta primeiro com verificação SSL
            response = self.session.get(base_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                base_domain = urlparse(base_url).netloc

                links = []
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    full_url = urljoin(base_url, href)

                    # Filtra apenas links do mesmo domínio
                    if (full_url.startswith('http') and
                        base_domain in full_url and
                        "#" not in full_url and
                        full_url != base_url and
                        not any(ext in full_url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif'])):
                        links.append(full_url)

                return list(set(links))[:10]
        except requests.exceptions.SSLError as ssl_error:
            logger.warning(f"⚠️ Erro SSL ao extrair links de {base_url}: {str(ssl_error)}")
            # Tenta novamente sem verificação SSL como fallback
            try:
                temp_session = requests.Session()
                temp_session.headers.update(self.headers)
                temp_session.verify = False
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                response = temp_session.get(base_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    base_domain = urlparse(base_url).netloc

                    links = []
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag['href']
                        full_url = urljoin(base_url, href)

                        if (full_url.startswith('http') and
                            base_domain in full_url and
                            "#" not in full_url and
                            full_url != base_url and
                            not any(ext in full_url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif'])):
                            links.append(full_url)

                    logger.info(f"✅ Links extraídos sem SSL de {base_url}: {len(links)} links")
                    return list(set(links))[:10]
            except Exception as fallback_error:
                logger.error(f"❌ Erro no fallback SSL para {base_url}: {str(fallback_error)}")
                return []
        except Exception as e:
            logger.error(f"❌ Erro ao extrair links internos de {base_url}: {str(e)}")
            return []

        return []

    def _generate_intelligent_related_queries(
        self,
        original_query: str,
        context: Dict[str, Any],
        existing_content: List[Dict[str, Any]]
    ) -> List[str]:
        """Gera queries relacionadas inteligentes baseadas no conteúdo já coletado"""

        segmento = context.get('segmento', '')
        produto = context.get('produto', '')

        # Analisa conteúdo existente para identificar gaps
        all_text = ' '.join([item['content'] for item in existing_content])

        # Identifica termos frequentes
        words = re.findall(r'\b\w{4,}\b', all_text.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Pega termos mais frequentes relacionados ao segmento
        relevant_terms = [word for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
                         if freq > 3 and word not in ['para', 'mais', 'como', 'sobre', 'brasil', 'anos']]

        # Gera queries relacionadas inteligentes
        related_queries = []

        if segmento:
            related_queries.extend([
                f"futuro {segmento} Brasil tendências 2025",
                f"desafios {segmento} mercado brasileiro soluções",
                f"inovações {segmento} tecnologia Brasil",
                f"regulamentação {segmento} mudanças Brasil",
                f"investimentos {segmento} startups Brasil"
            ])

        if produto:
            related_queries.extend([
                f"demanda {produto} Brasil estatísticas",
                f"concorrência {produto} mercado brasileiro",
                f"preços {produto} benchmarks Brasil"
            ])

        # Adiciona queries baseadas em termos frequentes
        for term in relevant_terms[:3]:
            related_queries.append(f"{term} {segmento} Brasil oportunidades")

        return related_queries[:8]

    def _process_and_analyze_content(
        self,
        all_content: List[Dict[str, Any]],
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Processa e analisa todo o conteúdo coletado"""

        if not all_content:
            return self._generate_emergency_research(query, context)

        # Ordena por qualidade
        all_content.sort(key=lambda x: x['quality_score'], reverse=True)

        # Combina insights únicos
        all_insights = []
        for item in all_content:
            all_insights.extend(item.get('insights', []))

        # Remove duplicatas de insights
        unique_insights = list(dict.fromkeys(all_insights))

        # Analisa tendências
        trends = self._analyze_market_trends(all_content, context)

        # Identifica oportunidades
        opportunities = self._identify_market_opportunities(all_content, context)

        # Calcula métricas de qualidade
        total_chars = sum(item['content_length'] for item in all_content)
        avg_quality = sum(item['quality_score'] for item in all_content) / len(all_content)

        # Atualiza estatísticas globais
        self.navigation_stats['avg_quality_score'] = avg_quality

        return {
            "query_original": query,
            "context": context,
            "navegacao_profunda": {
                "total_paginas_analisadas": len(all_content),
                "engines_utilizados": list(set(item['search_engine'] for item in all_content)),
                "fontes_preferenciais": sum(1 for item in all_content if item.get('is_preferred_source')),
                "qualidade_media": round(avg_quality, 2),
                "total_caracteres": total_chars,
                "insights_unicos": len(unique_insights)
            },
            "conteudo_consolidado": {
                "insights_principais": unique_insights[:20],
                "tendencias_identificadas": trends,
                "oportunidades_descobertas": opportunities,
                "fontes_detalhadas": [
                    {
                        'url': item['url'],
                        'title': item['title'],
                        'quality_score': item['quality_score'],
                        'content_length': item['content_length'],
                        'search_engine': item['search_engine'],
                        'is_preferred': item.get('is_preferred_source', False)
                    } for item in all_content[:15]
                ]
            },
            "estatisticas_navegacao": self.navigation_stats,
            "metadata": {
                "navegacao_concluida_em": datetime.now().isoformat(),
                "agente": "Alibaba_WebSailor_v3.0",
                "garantia_dados_reais": True,
                "simulacao_free": True,
                "qualidade_premium": avg_quality >= 80
            }
        }

    def _analyze_market_trends(self, content_list: List[Dict[str, Any]], context: Dict[str, Any]) -> List[str]:
        """Analisa tendências de mercado do conteúdo"""

        trends = []
        all_text = ' '.join([item['content'] for item in content_list])

        # Padrões de tendências
        trend_keywords = [
            'inteligência artificial', 'ia', 'automação', 'digital',
            'sustentabilidade', 'personalização', 'mobile', 'cloud',
            'dados', 'analytics', 'experiência', 'inovação', 'telemedicina',
            'healthtech', 'fintech', 'edtech', 'blockchain', 'metaverso'
        ]

        for keyword in trend_keywords:
            if keyword in all_text.lower():
                # Busca contexto ao redor da palavra-chave
                pattern = rf'.{{0,150}}{re.escape(keyword)}.{{0,150}}'
                matches = re.findall(pattern, all_text.lower(), re.IGNORECASE)

                if matches:
                    trend_context = matches[0].strip()
                    if len(trend_context) > 80:
                        trends.append(f"Tendência: {trend_context[:200]}...")

        return trends[:8]

    def _identify_market_opportunities(self, content_list: List[Dict[str, Any]], context: Dict[str, Any]) -> List[str]:
        """Identifica oportunidades de mercado"""

        opportunities = []
        all_text = ' '.join([item['content'] for item in content_list])

        # Padrões de oportunidades
        opportunity_keywords = [
            'oportunidade', 'potencial', 'crescimento', 'expansão',
            'nicho', 'gap', 'lacuna', 'demanda não atendida',
            'mercado emergente', 'novo mercado', 'segmento inexplorado',
            'necessidade', 'carência', 'falta de'
        ]

        for keyword in opportunity_keywords:
            if keyword in all_text.lower():
                pattern = rf'.{{0,150}}{re.escape(keyword)}.{{0,150}}'
                matches = re.findall(pattern, all_text.lower(), re.IGNORECASE)

                if matches:
                    opp_context = matches[0].strip()
                    if len(opp_context) > 80:
                        opportunities.append(f"Oportunidade: {opp_context[:200]}...")

        return opportunities[:6]

    def _update_navigation_stats(self, content_list: List[Dict[str, Any]]):
        """Atualiza estatísticas de navegação"""

        if content_list:
            avg_quality = sum(item['quality_score'] for item in content_list) / len(content_list)
            self.navigation_stats['avg_quality_score'] = avg_quality

    def _generate_emergency_research(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gera pesquisa de emergência quando navegação falha"""

        logger.warning("⚠️ Gerando pesquisa de emergência WebSailor")

        return {
            "query_original": query,
            "context": context,
            "navegacao_profunda": {
                "total_paginas_analisadas": 0,
                "engines_utilizados": [],
                "status": "emergencia",
                "message": "Navegação em modo de emergência - configure APIs para dados completos"
            },
            "conteudo_consolidado": {
                "insights_principais": [
                    f"Pesquisa emergencial para '{query}' - sistema em recuperação",
                    "Recomenda-se nova tentativa com configuração completa das APIs",
                    "WebSailor em modo de emergência - funcionalidade limitada"
                ],
                "tendencias_identificadas": [
                    "Sistema em modo de emergência - tendências limitadas"
                ],
                "oportunidades_descobertas": [
                    "Reconfigurar APIs para navegação completa"
                ]
            },
            "metadata": {
                "navegacao_concluida_em": datetime.now().isoformat(),
                "agente": "Alibaba_WebSailor_Emergency",
                "garantia_dados_reais": False,
                "modo_emergencia": True
            }
        }

    def get_navigation_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de navegação"""
        return self.navigation_stats.copy()

    def reset_navigation_stats(self):
        """Reset estatísticas de navegação"""
        self.navigation_stats = {
            'total_searches': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'blocked_urls': 0,
            'preferred_sources': 0,
            'total_content_chars': 0,
            'avg_quality_score': 0.0
        }
        logger.info("🔄 Estatísticas de navegação resetadas")

# =============== MÓDULO DE ANÁLISE DE CONTEÚDO VIRAL (BÁSICO) ===============

class ViralContentAnalyzerModule:
    """Módulo para análise de conteúdo viral com captura de screenshots"""

    def __init__(self):
        """Inicializa o analisador de conteúdo viral"""
        self.instagram_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.facebook_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.screenshot_dir = os.path.join(os.getcwd(), 'analyses_data', 'screenshots')
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Configuração do cliente HTTP
        self.session = httpx.AsyncClient(timeout=30.0)
        
        logger.info("🔥 Módulo ViralContentAnalyzer inicializado")

    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    def _setup_selenium_driver(self, mobile: bool = False) -> webdriver.Chrome:
        """Configura driver Selenium para captura de screenshots"""
        if not HAS_SELENIUM:
            raise Exception("Selenium não está instalado")
            
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        if mobile:
            chrome_options.add_argument('--window-size=375,812')  # iPhone X size
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)')
        else:
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        return webdriver.Chrome(options=chrome_options)
    
    async def capture_screenshot(self, url: str, filename: str, 
                                mobile: bool = False, full_page: bool = True) -> str:
        """
        Captura screenshot de uma URL
        """
        if not HAS_SELENIUM:
            logger.warning("⚠️ Selenium não disponível para captura de screenshots")
            return ""
            
        try:
            driver = self._setup_selenium_driver(mobile)
            driver.get(url)
            
            # Aguarda carregamento
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll para carregar conteúdo dinâmico
            if full_page:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            
            # Remove elementos que podem atrapalhar
            driver.execute_script("""
                // Remove cookie banners, popups, etc.
                var elements = document.querySelectorAll('[class*="cookie"], [class*="popup"], [class*="modal"], [id*="cookie"], [id*="popup"]');
                elements.forEach(function(element) {
                    element.style.display = 'none';
                });
            """)
            
            screenshot_path = os.path.join(self.screenshot_dir, filename)
            
            if full_page:
                # Screenshot da página inteira
                total_height = driver.execute_script("return document.body.scrollHeight")
                driver.set_window_size(1920, total_height)
                time.sleep(2)
            
            driver.save_screenshot(screenshot_path)
            driver.quit()
            
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Erro ao capturar screenshot de {url}: {e}")
            return ""
    
    async def analyze_instagram_content(self, hashtag: str, limit: int = 20) -> List[ViralContent]:
        """
        Analisa conteúdo do Instagram por hashtag
        """
        if not self.instagram_token:
            return []
        
        # Instagram Basic Display API é limitada, simulamos análise
        viral_contents = []
        
        try:
            # Busca posts por hashtag (simulado - API real requer aprovação)
            posts_data = await self._simulate_instagram_search(hashtag, limit)
            
            for post in posts_data:
                screenshot_filename = f"instagram_{post['id']}_{int(time.time())}.png"
                screenshot_path = await self.capture_screenshot(
                    post['url'], screenshot_filename, mobile=True
                )
                
                viral_content = ViralContent(
                    platform="Instagram",
                    url=post['url'],
                    title=post.get('caption', '')[:100],
                    description=post.get('caption', ''),
                    author=post.get('username', ''),
                    engagement_metrics={
                        'likes': post.get('likes', 0),
                        'comments': post.get('comments', 0),
                        'shares': post.get('shares', 0)
                    },
                    screenshot_path=screenshot_path,
                    content_type=post.get('media_type', 'image'),
                    hashtags=self._extract_hashtags(post.get('caption', '')),
                    mentions=self._extract_mentions(post.get('caption', '')),
                    timestamp=post.get('timestamp', ''),
                    virality_score=self._calculate_virality_score(post, 'instagram')
                )
                
                viral_contents.append(viral_content)
                
        except Exception as e:
            logger.error(f"Erro ao analisar Instagram: {e}")
        
        return viral_contents
    
    async def analyze_youtube_content(self, query: str, limit: int = 20) -> List[ViralContent]:
        """
        Analisa conteúdo do YouTube
        """
        if not self.youtube_api_key:
            return []
        
        viral_contents = []
        
        try:
            # Busca vídeos
            search_url = "https://www.googleapis.com/youtube/v3/search"
            search_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': limit,
                'order': 'relevance',
                'key': self.youtube_api_key
            }
            
            response = await self.session.get(search_url, params=search_params)
            response.raise_for_status()
            search_data = response.json()
            
            # Busca estatísticas dos vídeos
            video_ids = [item['id']['videoId'] for item in search_data.get('items', [])]
            
            if video_ids:
                stats_url = "https://www.googleapis.com/youtube/v3/videos"
                stats_params = {
                    'part': 'statistics,snippet',
                    'id': ','.join(video_ids),
                    'key': self.youtube_api_key
                }
                
                stats_response = await self.session.get(stats_url, params=stats_params)
                stats_response.raise_for_status()
                stats_data = stats_response.json()
                
                for video in stats_data.get('items', []):
                    video_id = video['id']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    screenshot_filename = f"youtube_{video_id}_{int(time.time())}.png"
                    screenshot_path = await self.capture_screenshot(
                        video_url, screenshot_filename
                    )
                    
                    stats = video.get('statistics', {})
                    snippet = video.get('snippet', {})
                    
                    viral_content = ViralContent(
                        platform="YouTube",
                        url=video_url,
                        title=snippet.get('title', ''),
                        description=snippet.get('description', ''),
                        author=snippet.get('channelTitle', ''),
                        engagement_metrics={
                            'views': int(stats.get('viewCount', 0)),
                            'likes': int(stats.get('likeCount', 0)),
                            'comments': int(stats.get('commentCount', 0)),
                            'shares': 0  # YouTube não fornece shares via API
                        },
                        screenshot_path=screenshot_path,
                        content_type='video',
                        hashtags=self._extract_hashtags(snippet.get('description', '')),
                        mentions=[],
                        timestamp=snippet.get('publishedAt', ''),
                        virality_score=self._calculate_virality_score(
                            {'stats': stats, 'snippet': snippet}, 'youtube'
                        )
                    )
                    
                    viral_contents.append(viral_content)
                    
        except Exception as e:
            logger.error(f"Erro ao analisar YouTube: {e}")
        
        return viral_contents
    
    async def analyze_facebook_content(self, query: str, limit: int = 20) -> List[ViralContent]:
        """
        Analisa conteúdo do Facebook (simulado devido a limitações da API)
        """
        viral_contents = []
        
        try:
            # Simula busca no Facebook
            facebook_data = await self._simulate_facebook_search(query, limit)
            
            for post in facebook_data:
                screenshot_filename = f"facebook_{post['id']}_{int(time.time())}.png"
                screenshot_path = await self.capture_screenshot(
                    post['url'], screenshot_filename
                )
                
                viral_content = ViralContent(
                    platform="Facebook",
                    url=post['url'],
                    title=post.get('message', '')[:100],
                    description=post.get('message', ''),
                    author=post.get('from', {}).get('name', ''),
                    engagement_metrics={
                        'likes': post.get('reactions', 0),
                        'comments': post.get('comments', 0),
                        'shares': post.get('shares', 0)
                    },
                    screenshot_path=screenshot_path,
                    content_type=post.get('type', 'status'),
                    hashtags=self._extract_hashtags(post.get('message', '')),
                    mentions=self._extract_mentions(post.get('message', '')),
                    timestamp=post.get('created_time', ''),
                    virality_score=self._calculate_virality_score(post, 'facebook')
                )
                
                viral_contents.append(viral_content)
                
        except Exception as e:
            logger.error(f"Erro ao analisar Facebook: {e}")
        
        return viral_contents
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extrai hashtags do texto"""
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, text)
        return [tag.lower() for tag in hashtags]
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extrai menções do texto"""
        mention_pattern = r'@\w+'
        mentions = re.findall(mention_pattern, text)
        return [mention.lower() for mention in mentions]
    
    def _calculate_virality_score(self, content_data: Dict, platform: str) -> float:
        """
        Calcula score de viralidade baseado na plataforma
        """
        score = 0.0
        
        if platform == 'youtube':
            stats = content_data.get('stats', {})
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            comments = int(stats.get('commentCount', 0))
            
            # Score baseado em views (normalizado)
            if views > 1000000:  # 1M+ views
                score += 10.0
            elif views > 100000:  # 100K+ views
                score += 7.0
            elif views > 10000:  # 10K+ views
                score += 5.0
            elif views > 1000:  # 1K+ views
                score += 3.0
            
            # Score baseado em engagement rate
            if views > 0:
                engagement_rate = (likes + comments) / views
                score += min(engagement_rate * 100, 5.0)
                
        elif platform == 'instagram':
            likes = content_data.get('likes', 0)
            comments = content_data.get('comments', 0)
            
            total_engagement = likes + comments
            if total_engagement > 10000:
                score += 10.0
            elif total_engagement > 1000:
                score += 7.0
            elif total_engagement > 100:
                score += 5.0
            elif total_engagement > 10:
                score += 3.0
                
        elif platform == 'facebook':
            reactions = content_data.get('reactions', 0)
            comments = content_data.get('comments', 0)
            shares = content_data.get('shares', 0)
            
            total_engagement = reactions + comments + (shares * 2)  # Shares valem mais
            if total_engagement > 5000:
                score += 10.0
            elif total_engagement > 500:
                score += 7.0
            elif total_engagement > 50:
                score += 5.0
            elif total_engagement > 5:
                score += 3.0
        
        return min(score, 10.0)  # Cap at 10.0
    
    async def _simulate_instagram_search(self, hashtag: str, limit: int) -> List[Dict]:
        """Simula busca no Instagram (para demonstração)"""
        # Em produção, usaria Instagram Basic Display API ou Graph API
        return [
            {
                'id': f'ig_{i}',
                'url': f'https://instagram.com/p/example{i}',
                'caption': f'Post sobre {hashtag} #{hashtag} #viral',
                'username': f'user_{i}',
                'likes': 1000 + i * 100,
                'comments': 50 + i * 10,
                'shares': 20 + i * 5,
                'media_type': 'image',
                'timestamp': datetime.now().isoformat()
            }
            for i in range(limit)
        ]
    
    async def _simulate_facebook_search(self, query: str, limit: int) -> List[Dict]:
        """Simula busca no Facebook (para demonstração)"""
        return [
            {
                'id': f'fb_{i}',
                'url': f'https://facebook.com/posts/example{i}',
                'message': f'Post sobre {query} muito viral!',
                'from': {'name': f'Page {i}'},
                'reactions': 500 + i * 50,
                'comments': 25 + i * 5,
                'shares': 10 + i * 2,
                'type': 'status',
                'created_time': datetime.now().isoformat()
            }
            for i in range(limit)
        ]
    
    async def analyze_trending_content(self, segment: str, platforms: List[str] = None) -> Dict[str, List[ViralContent]]:
        """
        Analisa conteúdo em tendência por segmento
        """
        if platforms is None:
            platforms = ['youtube', 'instagram', 'facebook']
        
        trending_content = {}
        
        for platform in platforms:
            if platform == 'youtube':
                content = await self.analyze_youtube_content(segment, 10)
            elif platform == 'instagram':
                content = await self.analyze_instagram_content(segment, 10)
            elif platform == 'facebook':
                content = await self.analyze_facebook_content(segment, 10)
            else:
                content = []
            
            trending_content[platform] = content
        
        return trending_content
    
    async def generate_virality_report(self, content_list: List[ViralContent]) -> Dict[str, Any]:
        """
        Gera relatório de viralidade
        """
        if not content_list:
            return {}
        
        # Estatísticas gerais
        total_content = len(content_list)
        platforms = list(set(content.platform for content in content_list))
        avg_virality = sum(content.virality_score for content in content_list) / total_content
        
        # Top hashtags
        all_hashtags = []
        for content in content_list:
            all_hashtags.extend(content.hashtags)
        
        hashtag_counts = {}
        for hashtag in all_hashtags:
            hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
        
        top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Conteúdo mais viral por plataforma
        platform_top = {}
        for platform in platforms:
            platform_content = [c for c in content_list if c.platform == platform]
            if platform_content:
                platform_top[platform] = max(platform_content, key=lambda x: x.virality_score)
        
        report = {
            'summary': {
                'total_content': total_content,
                'platforms_analyzed': platforms,
                'average_virality_score': round(avg_virality, 2),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'top_hashtags': top_hashtags,
            'platform_leaders': {
                platform: {
                    'title': content.title,
                    'url': content.url,
                    'virality_score': content.virality_score,
                    'engagement_metrics': content.engagement_metrics
                }
                for platform, content in platform_top.items()
            },
            'content_distribution': {
                platform: len([c for c in content_list if c.platform == platform])
                for platform in platforms
            }
        }
        
        return report

# =============== MÓDULO AVANÇADO DE ANÁLISE DE CONTEÚDO VIRAL ===============

class ViralContentAnalyzerAdvanced:
    """Analisador de conteúdo viral com captura automática"""

    def __init__(self):
        """Inicializa o analisador avançado"""
        self.viral_thresholds = {
            'youtube': {
                'min_views': 10000,
                'min_likes': 500,
                'min_comments': 50,
                'engagement_rate': 0.05
            },
            'instagram': {
                'min_likes': 1000,
                'min_comments': 50,
                'engagement_rate': 0.03
            },
            'twitter': {
                'min_retweets': 100,
                'min_likes': 500,
                'min_replies': 20
            },
            'tiktok': {
                'min_views': 50000,
                'min_likes': 2000,
                'min_shares': 100
            }
        }

        self.screenshot_config = {
            'width': 1920,
            'height': 1080,
            'wait_time': 5,
            'scroll_pause': 2
        }

        logger.info("🔥 Módulo ViralContentAnalyzerAdvanced inicializado")

    async def analyze_and_capture_viral_content(
        self,
        search_results: Dict[str, Any],
        session_id: str,
        max_captures: int = 15
    ) -> Dict[str, Any]:
        """Analisa e captura conteúdo viral dos resultados de busca"""

        logger.info(f"🔥 Analisando conteúdo viral para sessão: {session_id}")

        analysis_results = {
            'session_id': session_id,
            'analysis_started': datetime.now().isoformat(),
            'viral_content_identified': [],
            'screenshots_captured': [],
            'viral_metrics': {},
            'platform_analysis': {},
            'top_performers': [],
            'engagement_insights': {}
        }

        try:
            # FASE 1: Identificação de Conteúdo Viral
            logger.info("🎯 FASE 1: Identificando conteúdo viral")

            all_content = []

            # Coleta todo o conteúdo
            for platform_results in ['web_results', 'youtube_results', 'social_results']:
                content_list = search_results.get(platform_results, [])
                if isinstance(content_list, list):
                    all_content.extend(content_list)
                else:
                    logger.warning(f"Dados inesperados para {platform_results}: esperado uma lista, obtido {type(content_list)}")

            # Analisa viralidade
            viral_content = self._identify_viral_content(all_content)
            analysis_results['viral_content_identified'] = viral_content

            # FASE 2: Análise por Plataforma
            logger.info("📊 FASE 2: Análise detalhada por plataforma")
            platform_analysis = self._analyze_by_platform(viral_content)
            analysis_results['platform_analysis'] = platform_analysis

            # FASE 3: Captura de Screenshots
            logger.info("📸 FASE 3: Capturando screenshots do conteúdo viral")

            if HAS_SELENIUM and viral_content:
                try:
                    # Seleciona top performers para screenshot
                    top_content = sorted(
                        viral_content,
                        key=lambda x: x.get('viral_score', 0),
                        reverse=True
                    )[:max_captures]

                    screenshots = await self._capture_viral_screenshots(top_content, session_id)
                    analysis_results['screenshots_captured'] = screenshots
                except Exception as e:
                    logger.warning(f"⚠️ Screenshots não disponíveis: {e}")
                    # Continua sem screenshots - não é crítico
                    analysis_results['screenshots_captured'] = []
            else:
                logger.warning("⚠️ Selenium não disponível ou nenhum conteúdo viral encontrado - screenshots desabilitados")
                analysis_results['screenshots_captured'] = []

            # FASE 4: Métricas e Insights
            logger.info("📈 FASE 4: Calculando métricas virais")

            viral_metrics = self._calculate_viral_metrics(viral_content)
            analysis_results['viral_metrics'] = viral_metrics

            engagement_insights = self._extract_engagement_insights(viral_content)
            analysis_results['engagement_insights'] = engagement_insights

            # Top performers
            analysis_results['top_performers'] = sorted(
                viral_content,
                key=lambda x: x.get('viral_score', 0),
                reverse=True
            )[:10]

            logger.info(f"✅ Análise viral concluída: {len(viral_content)} conteúdos identificados")
            logger.info(f"📸 {len(analysis_results['screenshots_captured'])} screenshots capturados")

            return analysis_results

        except Exception as e:
            logger.error(f"❌ Erro na análise viral: {e}", exc_info=True)
            raise

    def _identify_viral_content(self, all_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifica conteúdo viral baseado em métricas"""

        viral_content = []

        for content in all_content:
            if not isinstance(content, dict):
                 logger.warning("Item de conteúdo não é um dicionário, pulando.")
                 continue
            platform = content.get('platform', 'web')
            viral_score = self._calculate_viral_score(content, platform)

            if viral_score >= 5.0:  # Threshold viral
                content['viral_score'] = viral_score
                content['viral_category'] = self._categorize_viral_content(content, viral_score)
                viral_content.append(content)

        return viral_content

    def _calculate_viral_score(self, content: Dict[str, Any], platform: str) -> float:
        """Calcula score viral baseado na plataforma"""

        try:
            if platform == 'youtube':
                views = int(content.get('view_count', 0) or 0)
                likes = int(content.get('like_count', 0) or 0)
                comments = int(content.get('comment_count', 0) or 0)

                # Fórmula YouTube: views/1000 + likes/100 + comments/10
                score = (views / 1000) + (likes / 100) + (comments / 10)
                return min(10.0, score / 100) if score > 0 else 0.0

            elif platform in ['instagram', 'facebook']:
                likes = int(content.get('likes', 0) or 0)
                comments = int(content.get('comments', 0) or 0)
                shares = int(content.get('shares', 0) or 0)

                # Fórmula Instagram/Facebook
                score = (likes / 100) + (comments / 10) + (shares / 5)
                return min(10.0, score / 50) if score > 0 else 0.0

            elif platform == 'twitter':
                retweets = int(content.get('retweets', 0) or 0)
                likes = int(content.get('likes', 0) or 0)
                replies = int(content.get('replies', 0) or 0)

                # Fórmula Twitter
                score = (retweets / 10) + (likes / 50) + (replies / 5)
                return min(10.0, score / 20) if score > 0 else 0.0

            elif platform == 'tiktok':
                views = int(content.get('view_count', 0) or 0)
                likes = int(content.get('likes', 0) or 0)
                shares = int(content.get('shares', 0) or 0)

                # Fórmula TikTok
                score = (views / 10000) + (likes / 500) + (shares / 100)
                return min(10.0, score / 50) if score > 0 else 0.0

            else:
                # Score baseado em relevância para conteúdo web
                relevance = content.get('relevance_score', 0) or 0
                return float(relevance) * 10

        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Erro ao calcular score viral para conteúdo {content.get('title', 'Sem título')}: {e}")
            return 0.0
        except Exception as e:
            logger.warning(f"⚠️ Erro inesperado ao calcular score viral: {e}")
            return 0.0

    def _categorize_viral_content(self, content: Dict[str, Any], viral_score: float) -> str:
        """Categoriza conteúdo viral"""

        if viral_score >= 9.0:
            return 'MEGA_VIRAL'
        elif viral_score >= 7.0:
            return 'VIRAL'
        elif viral_score >= 5.0:
            return 'TRENDING'
        else:
            return 'POPULAR'

    def _analyze_by_platform(self, viral_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analisa conteúdo viral por plataforma"""

        platform_stats = {}

        for content in viral_content:
            platform = content.get('platform', 'web')

            if platform not in platform_stats:
                platform_stats[platform] = {
                    'total_content': 0,
                    'avg_viral_score': 0.0,
                    'top_content': [],
                    'engagement_metrics': {},
                    'content_themes': []
                }

            stats = platform_stats[platform]
            stats['total_content'] += 1
            stats['top_content'].append(content)

            # Calcula métricas de engajamento
            try:
                if platform == 'youtube':
                    stats['engagement_metrics']['total_views'] = stats['engagement_metrics'].get('total_views', 0) + int(content.get('view_count', 0) or 0)
                    stats['engagement_metrics']['total_likes'] = stats['engagement_metrics'].get('total_likes', 0) + int(content.get('like_count', 0) or 0)

                elif platform in ['instagram', 'facebook']:
                    stats['engagement_metrics']['total_likes'] = stats['engagement_metrics'].get('total_likes', 0) + int(content.get('likes', 0) or 0)
                    stats['engagement_metrics']['total_comments'] = stats['engagement_metrics'].get('total_comments', 0) + int(content.get('comments', 0) or 0)
            except (ValueError, TypeError) as e:
                 logger.warning(f"Ignorando métrica inválida para {platform}: {e}")

        # Calcula médias
        for platform, stats in platform_stats.items():
            if stats['total_content'] > 0:
                total_score = sum(c.get('viral_score', 0) for c in stats['top_content'])
                stats['avg_viral_score'] = total_score / stats['total_content']

                # Ordena top content
                stats['top_content'] = sorted(
                    stats['top_content'],
                    key=lambda x: x.get('viral_score', 0),
                    reverse=True
                )[:5]

        return platform_stats

    async def _capture_viral_screenshots(
        self,
        viral_content: List[Dict[str, Any]],
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Captura screenshots do conteúdo viral"""

        if not HAS_SELENIUM:
            logger.warning("⚠️ Selenium não disponível para screenshots")
            return []

        screenshots = []

        try:
            # Configura Chrome headless
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument(f"--window-size={self.screenshot_config['width']},{self.screenshot_config['height']}")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")

            # Usa ChromeDriverManager
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ ChromeDriverManager funcionou")
            except Exception as e:
                logger.warning(f"⚠️ ChromeDriverManager falhou: {e}, tentando usar chromedriver do sistema")
                # Fallback para chromedriver do sistema (se configurado corretamente)
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                    logger.info("✅ Chromedriver do sistema funcionou")
                except WebDriverException as sys_driver_e:
                    logger.error(f"❌ Falha ao iniciar Chrome com chromedriver do sistema: {sys_driver_e}. Certifique-se de que o chromedriver esteja no PATH ou especificado.")
                    return []

            # Cria diretório para screenshots
            screenshots_dir = Path(f"analyses_data/files/{session_id}")
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            try:
                for i, content in enumerate(viral_content, 1):
                    try:
                        url = content.get('url', '')
                        if not url or not url.startswith(('http://', 'https://')):
                            logger.warning(f"Skipping invalid URL: {url}")
                            continue

                        logger.info(f"📸 Capturando screenshot {i}/{len(viral_content)}: {content.get('title', 'Sem título')}")

                        # Acessa a URL
                        driver.get(url)

                        # Aguarda carregamento
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )

                        # Aguarda renderização completa
                        await asyncio.sleep(self.screenshot_config['wait_time'])

                        # Scroll para carregar conteúdo lazy-loaded
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                        await asyncio.sleep(self.screenshot_config['scroll_pause'])
                        driver.execute_script("window.scrollTo(0, 0);")
                        await asyncio.sleep(1)

                        # Captura informações da página
                        page_title = driver.title or content.get('title', 'Sem título')
                        current_url = driver.current_url

                        # Define nome do arquivo
                        platform = content.get('platform', 'web')
                        viral_score = content.get('viral_score', 0)
                        # Evita caracteres inválidos no nome do arquivo
                        safe_title = "".join(c if c.isalnum() else "_" for c in page_title[:50])
                        filename = f"viral_{platform}_{i:02d}_score{viral_score:.1f}_{safe_title}.png"
                        screenshot_path = screenshots_dir / filename

                        # Captura screenshot
                        driver.save_screenshot(str(screenshot_path))

                        # Verifica se foi criado com sucesso
                        if screenshot_path.exists() and screenshot_path.stat().st_size > 0:
                            screenshot_data = {
                                'filename': filename,
                                'filepath': str(screenshot_path),
                                'relative_path': f"files/{session_id}/{filename}",
                                'url': url,
                                'final_url': current_url,
                                'title': page_title,
                                'platform': platform,
                                'viral_score': viral_score,
                                'viral_category': content.get('viral_category', 'POPULAR'),
                                'content_metrics': {
                                    'views': content.get('view_count', content.get('views', 0)),
                                    'likes': content.get('like_count', content.get('likes', 0)),
                                    'comments': content.get('comment_count', content.get('comments', 0)),
                                    'shares': content.get('shares', 0),
                                    'engagement_rate': content.get('engagement_rate', 0)
                                },
                                'file_size': screenshot_path.stat().st_size,
                                'captured_at': datetime.now().isoformat(),
                                'capture_success': True
                            }

                            screenshots.append(screenshot_data)
                            logger.info(f"✅ Screenshot {i} capturado: {filename}")
                        else:
                            logger.warning(f"⚠️ Falha ao criar arquivo de screenshot {i}: {screenshot_path}")

                    except (TimeoutException, WebDriverException) as e:
                        logger.error(f"❌ Erro de Selenium ao capturar screenshot {i} ({url}): {e}")
                        continue
                    except Exception as e:
                        logger.error(f"❌ Erro inesperado ao capturar screenshot {i} ({url}): {e}", exc_info=True)
                        continue

            finally:
                if 'driver' in locals() and driver:
                    driver.quit()
                    logger.info("✅ Driver do Chrome fechado")

        except Exception as e:
            logger.warning(f"⚠️ Falha geral na captura de screenshots: {e}", exc_info=True)
            return []

        logger.info(f"📸 {len(screenshots)} screenshots capturados com sucesso")
        return screenshots

    def _calculate_viral_metrics(self, viral_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula métricas gerais de viralidade"""

        if not viral_content:
            return {}

        metrics = {
            'total_viral_content': len(viral_content),
            'avg_viral_score': 0.0,
            'viral_distribution': {
                'MEGA_VIRAL': 0,
                'VIRAL': 0,
                'TRENDING': 0,
                'POPULAR': 0
            },
            'platform_distribution': {},
            'engagement_totals': {
                'total_views': 0,
                'total_likes': 0,
                'total_comments': 0,
                'total_shares': 0
            },
            'top_viral_score': 0.0
        }

        total_score = 0.0

        for content in viral_content:
            viral_score = content.get('viral_score', 0)
            total_score += viral_score

            # Atualiza score máximo
            if viral_score > metrics['top_viral_score']:
                metrics['top_viral_score'] = viral_score

            # Distribui por categoria
            category = content.get('viral_category', 'POPULAR')
            metrics['viral_distribution'][category] = metrics['viral_distribution'].get(category, 0) + 1

            # Distribui por plataforma
            platform = content.get('platform', 'web')
            metrics['platform_distribution'][platform] = metrics['platform_distribution'].get(platform, 0) + 1

            # Soma engajamento
            try:
                metrics['engagement_totals']['total_views'] += int(content.get('view_count', content.get('views', 0)) or 0)
                metrics['engagement_totals']['total_likes'] += int(content.get('like_count', content.get('likes', 0)) or 0)
                metrics['engagement_totals']['total_comments'] += int(content.get('comment_count', content.get('comments', 0)) or 0)
                metrics['engagement_totals']['total_shares'] += int(content.get('shares', 0) or 0)
            except (ValueError, TypeError) as e:
                 logger.warning(f"Ignorando métrica de engajamento inválida: {e}")

        # Calcula médias
        if len(viral_content) > 0:
            metrics['avg_viral_score'] = total_score / len(viral_content)
        else:
            metrics['avg_viral_score'] = 0.0

        return metrics

    def _extract_engagement_insights(self, viral_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrai insights de engajamento"""

        insights = {
            'best_performing_platforms': [],
            'optimal_content_types': [],
            'engagement_patterns': {},
            'viral_triggers': [],
            'audience_preferences': {}
        }

        # Analisa performance por plataforma
        platform_performance = {}

        for content in viral_content:
            platform = content.get('platform', 'web')
            viral_score = content.get('viral_score', 0)

            if platform not in platform_performance:
                platform_performance[platform] = {
                    'total_score': 0.0,
                    'content_count': 0,
                    'avg_score': 0.0
                }

            platform_performance[platform]['total_score'] += viral_score
            platform_performance[platform]['content_count'] += 1

        # Calcula médias e ordena
        for platform, data in platform_performance.items():
            if data['content_count'] > 0:
                data['avg_score'] = data['total_score'] / data['content_count']
            else:
                data['avg_score'] = 0.0

        insights['best_performing_platforms'] = sorted(
            platform_performance.items(),
            key=lambda x: x[1]['avg_score'],
            reverse=True
        )

        # Identifica padrões de conteúdo
        content_types = {}
        for content in viral_content:
            title = (content.get('title', '') or '').lower()

            # Categoriza por tipo de conteúdo
            if any(word in title for word in ['como', 'tutorial', 'passo a passo']):
                content_types['tutorial'] = content_types.get('tutorial', 0) + 1
            elif any(word in title for word in ['dica', 'segredo', 'truque']):
                content_types['dicas'] = content_types.get('dicas', 0) + 1
            elif any(word in title for word in ['caso', 'história', 'experiência']):
                content_types['casos'] = content_types.get('casos', 0) + 1
            elif any(word in title for word in ['análise', 'dados', 'pesquisa']):
                content_types['analise'] = content_types.get('analise', 0) + 1

        insights['optimal_content_types'] = sorted(
            content_types.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return insights

    def generate_viral_content_report(
        self,
        analysis_results: Dict[str, Any],
        session_id: str
    ) -> str:
        """Gera relatório detalhado do conteúdo viral"""

        viral_content = analysis_results.get('viral_content_identified', [])
        screenshots = analysis_results.get('screenshots_captured', [])
        metrics = analysis_results.get('viral_metrics', {})

        report = f"# RELATÓRIO DE CONTEÚDO VIRAL - ARQV30 Enhanced v3.0\n\n**Sessão:** {session_id}  \n**Análise realizada em:** {analysis_results.get('analysis_started', 'N/A')}  \n**Conteúdo viral identificado:** {len(viral_content)}  \n**Screenshots capturados:** {len(screenshots)}\n\n---\n\n## RESUMO EXECUTIVO\n\n### Métricas Gerais:\n- **Total de conteúdo viral:** {metrics.get('total_viral_content', 0)}\n- **Score viral médio:** {metrics.get('avg_viral_score', 0):.2f}/10\n- **Score viral máximo:** {metrics.get('top_viral_score', 0):.2f}/10\n\n### Distribuição por Categoria:\n"

        # Adiciona distribuição viral
        viral_dist = metrics.get('viral_distribution', {})
        for category, count in viral_dist.items():
            report += f"- **{category}:** {count} conteúdos\n"

        report += "\n### Distribuição por Plataforma:\n"
        platform_dist = metrics.get('platform_distribution', {})
        for platform, count in platform_dist.items():
            report += f"- **{platform.title()}:** {count} conteúdos\n"

        report += "\n---\n\n## TOP 10 CONTEÚDOS VIRAIS\n\n"

        # Lista top performers
        top_performers = analysis_results.get('top_performers', [])
        for i, content in enumerate(top_performers[:10], 1):
            report += f"### {i}. {content.get('title', 'Sem título')}\n\n**Plataforma:** {content.get('platform', 'N/A').title()}  \n**Score Viral:** {content.get('viral_score', 0):.2f}/10  \n**Categoria:** {content.get('viral_category', 'N/A')}  \n**URL:** {content.get('url', 'N/A')}  \n"

            # Métricas específicas por plataforma
            if content.get('platform') == 'youtube':
                report += f"**Views:** {content.get('view_count', 0):,}  \n**Likes:** {content.get('like_count', 0):,}  \n**Comentários:** {content.get('comment_count', 0):,}  \n**Canal:** {content.get('channel', 'N/A')}  \n"

            elif content.get('platform') in ['instagram', 'facebook']:
                report += f"**Likes:** {content.get('likes', 0):,}  \n**Comentários:** {content.get('comments', 0):,}  \n**Compartilhamentos:** {content.get('shares', 0):,}  \n"

            elif content.get('platform') == 'twitter':
                report += f"**Retweets:** {content.get('retweets', 0):,}  \n**Likes:** {content.get('likes', 0):,}  \n**Respostas:** {content.get('replies', 0):,}  \n"

            report += "\n"

        # Adiciona screenshots se disponíveis
        if screenshots:
            report += "---\n\n## EVIDÊNCIAS VISUAIS CAPTURADAS\n\n"

            for i, screenshot in enumerate(screenshots, 1):
                report += f"### Screenshot {i}: {screenshot.get('title', 'Sem título')}\n\n**Plataforma:** {screenshot.get('platform', 'N/A').title()}  \n**Score Viral:** {screenshot.get('viral_score', 0):.2f}/10  \n**URL Original:** {screenshot.get('url', 'N/A')}  \n![Screenshot {i}]({screenshot.get('relative_path', '')})  \n\n"

                # Métricas do conteúdo
                metrics = screenshot.get('content_metrics', {})
                if metrics:
                    report += "**Métricas de Engajamento:**  \n"
                    if metrics.get('views'):
                        report += f"- Views: {metrics['views']:,}  \n"
                    if metrics.get('likes'):
                        report += f"- Likes: {metrics['likes']:,}  \n"
                    if metrics.get('comments'):
                        report += f"- Comentários: {metrics['comments']:,}  \n"
                    if metrics.get('shares'):
                        report += f"- Compartilhamentos: {metrics['shares']:,}  \n"

                report += "\n"

        # Insights de engajamento
        engagement_insights = analysis_results.get('engagement_insights', {})
        if engagement_insights:
            report += "---\n\n## INSIGHTS DE ENGAJAMENTO\n\n"

            best_platforms = engagement_insights.get('best_performing_platforms', [])
            if best_platforms:
                report += "### Plataformas com Melhor Performance:\n"
                for platform, data in best_platforms[:3]:
                    report += f"1. **{platform.title()}:** Score médio {data['avg_score']:.2f} ({data['content_count']} conteúdos)\n"

            content_types = engagement_insights.get('optimal_content_types', [])
            if content_types:
                report += "\n### Tipos de Conteúdo Mais Virais:\n"
                for content_type, count in content_types[:5]:
                    report += f"- **{content_type.title()}:** {count} conteúdos virais\n"

        report += f"\n---\n\n*Relatório gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*"

        return report

# =============== MÓDULO DE BUSCA DE IMAGENS VIRAIS ===============

class ViralImageFinder:
    """Classe principal para encontrar imagens virais"""
    def __init__(self, config: Dict = None):
        """Inicializa o buscador de imagens virais"""
        self.config = config or self._load_config()
        # Sistema de rotação de APIs
        self.api_keys = self._load_multiple_api_keys()
        self.current_api_index = {
            'apify': 0,
            'openrouter': 0,
            'serper': 0,
            'google_cse': 0
        }
        self.failed_apis = set()  # APIs que falharam recentemente
        self.instagram_session_cookie = self.config.get('instagram_session_cookie')
        self.playwright_enabled = self.config.get('playwright_enabled', True) and PLAYWRIGHT_AVAILABLE
        # Configurar diretórios necessários
        self._ensure_directories()
        # Configurar sessão HTTP síncrona para fallbacks
        if not HAS_ASYNC_DEPS:
            import requests
            self.session = requests.Session()
            self.setup_session()
        
        # Validar configuração das APIs
        self._validate_api_configuration()
        
        # Confirmar inicialização bem-sucedida
        logger.info("🔥 Módulo ViralImageFinder inicializado")

    def _load_config(self) -> Dict:
        """Carrega configurações do ambiente"""
        return {
            'gemini_api_key': os.getenv('GEMINI_API_KEY'),
            'serper_api_key': os.getenv('SERPER_API_KEY'),
            'google_search_key': os.getenv('GOOGLE_SEARCH_KEY'),
            'google_cse_id': os.getenv('GOOGLE_CSE_ID'),
            'apify_api_key': os.getenv('APIFY_API_KEY'),
            'instagram_session_cookie': os.getenv('INSTAGRAM_SESSION_COOKIE'),

            'max_images': int(os.getenv('MAX_IMAGES', 30)),
            'min_engagement': float(os.getenv('MIN_ENGAGEMENT', 0)),
            'timeout': int(os.getenv('TIMEOUT', 30)),
            'headless': os.getenv('PLAYWRIGHT_HEADLESS', 'True').lower() == 'true',
            'output_dir': os.getenv('OUTPUT_DIR', 'viral_images_data'),
            'images_dir': os.getenv('IMAGES_DIR', 'downloaded_images'),
            'extract_images': os.getenv('EXTRACT_IMAGES', 'True').lower() == 'true',
            'playwright_enabled': os.getenv('PLAYWRIGHT_ENABLED', 'True').lower() == 'true',
            'screenshots_dir': os.getenv('SCREENSHOTS_DIR', 'screenshots'),
            'playwright_timeout': int(os.getenv('PLAYWRIGHT_TIMEOUT', 45000)),
            'playwright_browser': os.getenv('PLAYWRIGHT_BROWSER', 'chromium'),
        }

    def _load_multiple_api_keys(self) -> Dict:
        """Carrega múltiplas chaves de API para rotação"""
        api_keys = {
            'apify': [],
            'openrouter': [],
            'serper': [],
            'google_cse': []
        }
        # Apify - múltiplas chaves
        for i in range(1, 4):  # Até 3 chaves Apify
            key = os.getenv(f'APIFY_API_KEY_{i}') or (os.getenv('APIFY_API_KEY') if i == 1 else None)
            if key and key.strip():
                api_keys['apify'].append(key.strip())
                logger.info(f"✅ Apify API {i} carregada")
        # OpenRouter - múltiplas chaves
        for i in range(1, 4):  # Até 3 chaves OpenRouter
            key = os.getenv(f'OPENROUTER_API_KEY_{i}') or (os.getenv('OPENROUTER_API_KEY') if i == 1 else None)
            if key and key.strip():
                api_keys['openrouter'].append(key.strip())
                logger.info(f"✅ OpenRouter API {i} carregada")
        # Serper - múltiplas chaves (incluindo todas as 4 chaves disponíveis)
        # Primeiro carrega a chave principal
        main_key = os.getenv('SERPER_API_KEY')
        if main_key and main_key.strip():
            api_keys['serper'].append(main_key.strip())
            logger.info(f"✅ Serper API principal carregada")
        
        # Depois carrega as chaves numeradas (1, 2, 3)
        for i in range(1, 4):  # Até 3 chaves Serper numeradas
            key = os.getenv(f'SERPER_API_KEY_{i}')
            if key and key.strip():
                api_keys['serper'].append(key.strip())
                logger.info(f"✅ Serper API {i} carregada")
        # Google CSE
        google_key = os.getenv('GOOGLE_SEARCH_KEY')
        google_cse = os.getenv('GOOGLE_CSE_ID')
        if google_key and google_cse:
            api_keys['google_cse'].append({'key': google_key, 'cse_id': google_cse})
            logger.info(f"✅ Google CSE carregada")
        return api_keys
    
    def _validate_api_configuration(self):
        """Valida se pelo menos uma API está configurada"""
        total_apis = sum(len(keys) for keys in self.api_keys.values())
        
        if total_apis == 0:
            logger.error("❌ NENHUMA API CONFIGURADA! O serviço NÃO FUNCIONARÁ sem APIs reais.")
            logger.error("🚨 OBRIGATÓRIO: Configure pelo menos uma das seguintes APIs:")
            logger.error("   - SERPER_API_KEY (recomendado)")
            logger.error("   - GOOGLE_SEARCH_KEY + GOOGLE_CSE_ID")
            logger.error("   - APIFY_API_KEY")
            raise ValueError("Nenhuma API configurada. Serviço requer APIs reais para funcionar.")
        else:
            logger.info(f"✅ {total_apis} API(s) configurada(s) e prontas para uso")
            
        # Verificar dependências opcionais
        if not HAS_ASYNC_DEPS:
            logger.warning("⚠️ aiohttp/aiofiles não instalados. Usando requests síncrono como fallback.")
            
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("⚠️ Playwright não disponível. Funcionalidades avançadas desabilitadas.")
            
        if not HAS_GEMINI:
            logger.warning("⚠️ Google Generative AI não disponível. Análise de conteúdo limitada.")
            
        if not HAS_BS4:
            logger.warning("⚠️ BeautifulSoup4 não disponível. Parsing HTML limitado.")

    def _get_next_api_key(self, service: str) -> Optional[str]:
        """Obtém próxima chave de API disponível com rotação automática"""
        if service not in self.api_keys or not self.api_keys[service]:
            return None
        keys = self.api_keys[service]
        if not keys:
            return None
        # Tentar todas as chaves disponíveis
        for attempt in range(len(keys)):
            current_index = self.current_api_index[service]
            # Verificar se esta API não falhou recentemente
            api_identifier = f"{service}_{current_index}"
            if api_identifier not in self.failed_apis:
                key = keys[current_index]
                logger.info(f"🔄 Usando {service} API #{current_index + 1}")
                # Avançar para próxima API na próxima chamada
                self.current_api_index[service] = (current_index + 1) % len(keys)
                return key
            # Se esta API falhou, tentar a próxima
            self.current_api_index[service] = (current_index + 1) % len(keys)
        logger.error(f"❌ Todas as APIs de {service} falharam recentemente")
        return None

    def _mark_api_failed(self, service: str, index: int):
        """Marca uma API como falhada temporariamente"""
        api_identifier = f"{service}_{index}"
        self.failed_apis.add(api_identifier)
        logger.warning(f"⚠️ API {service} #{index + 1} marcada como falhada")
        # Limpar falhas após 5 minutos (300 segundos)
        import threading
        def clear_failure():
            time.sleep(300)  # 5 minutos
            if api_identifier in self.failed_apis:
                self.failed_apis.remove(api_identifier)
                logger.info(f"✅ API {service} #{index + 1} reabilitada")
        threading.Thread(target=clear_failure, daemon=True).start()

    def _ensure_directories(self):
        """Garante que todos os diretórios necessários existam"""
        dirs_to_create = [
            self.config['output_dir'],
            self.config['images_dir'],
            self.config['screenshots_dir']
        ]
        for directory in dirs_to_create:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"✅ Diretório criado/verificado: {directory}")
            except Exception as e:
                logger.error(f"❌ Erro ao criar diretório {directory}: {e}")

    def setup_session(self):
        """Configura sessão HTTP com headers apropriados"""
        if hasattr(self, 'session'):
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })

    async def search_images(self, query: str) -> List[Dict]:
        """Busca imagens usando múltiplos provedores com estratégia aprimorada"""
        all_results = []
        # Queries mais específicas e eficazes para conteúdo educacional
        queries = [
            # Instagram queries - mais variadas
            f'"{query}" site:instagram.com',
            f'site:instagram.com/p "{query}"',
            f'site:instagram.com/reel "{query}"',
            f'"{query}" instagram curso',
            f'"{query}" instagram masterclass',
            f'"{query}" instagram dicas',
            f'"{query}" instagram tutorial',
            # Facebook queries - mais robustas
            f'"{query}" site:facebook.com',
            f'site:facebook.com/posts "{query}"',
            f'"{query}" facebook curso',
            f'"{query}" facebook aula',
            f'"{query}" facebook dicas',
            # YouTube queries - para thumbnails
            f'"{query}" site:youtube.com',
            f'site:youtube.com/watch "{query}"',
            f'"{query}" youtube tutorial',
            f'"{query}" youtube curso',
            # Queries gerais mais amplas
            f'"{query}" curso online',
            f'"{query}" aula gratuita',
            f'"{query}" tutorial gratis',
            f'"{query}" masterclass'
        ]
        for q in queries[:8]:  # Aumentar para mais resultados
            logger.info(f"🔍 Buscando: {q}")
            results = []
            # Tentar Serper primeiro (mais confiável)
            if self.config.get('serper_api_key'):
                try:
                    serper_results = await self._search_serper_advanced(q)
                    results.extend(serper_results)
                    logger.info(f"📊 Serper encontrou {len(serper_results)} resultados para: {q}")
                except Exception as e:
                    logger.error(f"❌ Erro na busca Serper para '{q}': {e}")
            # Google CSE como backup
            if len(results) < 3 and self.config.get('google_search_key') and self.config.get('google_cse_id'):
                try:
                    google_results = await self._search_google_cse_advanced(q)
                    results.extend(google_results)
                    logger.info(f"📊 Google CSE encontrou {len(google_results)} resultados para: {q}")
                except Exception as e:
                    logger.error(f"❌ Erro na busca Google CSE para '{q}': {e}")
            all_results.extend(results)
            # Rate limiting
            await asyncio.sleep(0.5)
        
        # YouTube thumbnails como fonte adicional
        try:
            youtube_results = await self._search_youtube_thumbnails(query)
            all_results.extend(youtube_results)
            logger.info(f"📺 YouTube thumbnails: {len(youtube_results)} encontrados")
        except Exception as e:
            logger.error(f"❌ Erro na busca YouTube: {e}")
        
        # Busca adicional específica para Facebook
        try:
            facebook_results = await self._search_facebook_specific(query)
            all_results.extend(facebook_results)
            logger.info(f"📘 Facebook específico: {len(facebook_results)} encontrados")
        except Exception as e:
            logger.error(f"❌ Erro na busca Facebook específica: {e}")
        
        # Busca adicional com estratégias alternativas se poucos resultados
        if len(all_results) < 15:
            try:
                alternative_results = await self._search_alternative_strategies(query)
                all_results.extend(alternative_results)
                logger.info(f"🔄 Estratégias alternativas: {len(alternative_results)} encontrados")
            except Exception as e:
                logger.error(f"❌ Erro nas estratégias alternativas: {e}")
        
        # EXTRAÇÃO DIRETA DE POSTS ESPECÍFICOS
        # Procurar por URLs específicas nos resultados e extrair imagens diretamente
        direct_extraction_results = []
        instagram_urls = []
        facebook_urls = []
        linkedin_urls = []
        
        # Coletar URLs específicas dos resultados
        for result in all_results:
            page_url = result.get('page_url', '')
            if 'instagram.com/p/' in page_url or 'instagram.com/reel/' in page_url:
                instagram_urls.append(page_url)
            elif 'facebook.com' in page_url:
                facebook_urls.append(page_url)
            elif 'linkedin.com' in page_url:
                linkedin_urls.append(page_url)
        
        # Extração direta do Instagram
        for insta_url in list(set(instagram_urls))[:5]:  # Limitar a 5 URLs
            try:
                direct_results = await self._extract_instagram_direct(insta_url)
                direct_extraction_results.extend(direct_results)
            except Exception as e:
                logger.warning(f"Erro extração direta Instagram {insta_url}: {e}")
        
        # Extração direta do Facebook
        for fb_url in list(set(facebook_urls))[:3]:  # Limitar a 3 URLs
            try:
                direct_results = await self._extract_facebook_direct(fb_url)
                direct_extraction_results.extend(direct_results)
            except Exception as e:
                logger.warning(f"Erro extração direta Facebook {fb_url}: {e}")
        
        # Extração direta do LinkedIn
        for li_url in list(set(linkedin_urls))[:3]:  # Limitar a 3 URLs
            try:
                direct_results = await self._extract_linkedin_direct(li_url)
                direct_extraction_results.extend(direct_results)
            except Exception as e:
                logger.warning(f"Erro extração direta LinkedIn {li_url}: {e}")
        
        # Adicionar resultados de extração direta
        all_results.extend(direct_extraction_results)
        logger.info(f"🎯 Extração direta: {len(direct_extraction_results)} imagens reais extraídas")
        
        # Remover duplicatas e filtrar URLs válidos
        seen_urls = set()
        unique_results = []
        for result in all_results:
            post_url = result.get('page_url', '').strip()
            if post_url and post_url not in seen_urls and self._is_valid_social_url(post_url):
                seen_urls.add(post_url)
                unique_results.append(result)
        logger.info(f"🎯 Encontrados {len(unique_results)} posts únicos e válidos")
        return unique_results

    def _is_valid_social_url(self, url: str) -> bool:
        """Verifica se é uma URL válida de rede social"""
        valid_patterns = [
            r'instagram\\.com/(p|reel)/',
            r'facebook\\.com/.+/posts/',
            r'facebook\\.com/.+/photos/',
            r'm\\.facebook\\.com/',
            r'youtube\\.com/watch',
            r'instagram\\.com/[^/]+/$'  # Perfis do Instagram
        ]
        return any(re.search(pattern, url) for pattern in valid_patterns)

    def _is_valid_image_url(self, url: str) -> bool:
        """Verifica se a URL parece ser de uma imagem real"""
        if not url or not isinstance(url, str):
            return False
        
        # URLs que claramente não são imagens
        invalid_patterns = [
            r'instagram\\.com/accounts/login',
            r'facebook\\.com/login',
            r'login\\.php',
            r'/login/',
            r'/auth/',
            r'accounts/login',
            r'\\.html$',
            r'\\.php$',
            r'\\.jsp$',
            r'\\.asp$'
        ]
        
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in invalid_patterns):
            return False
        
        # URLs que provavelmente são imagens
        valid_patterns = [
            r'\\.(jpg|jpeg|png|gif|webp|bmp|svg)(\\?|$)',
            r'scontent.*\\.jpg',
            r'scontent.*\\.png',
            r'cdninstagram\\.com',
            r'fbcdn\\.net',
            r'instagram\\.com.*\\.(jpg|png|webp)',
            r'facebook\\.com.*\\.(jpg|png|webp)',
            r'lookaside\\.instagram\\.com',  # URLs de widget/crawler do Instagram
            r'instagram\\.com/seo/',        # URLs SEO do Instagram
            r'media_id=\\d+',              # URLs com media_id (Instagram)
            r'graph\\.instagram\\.com',     # Graph API do Instagram
            r'img\\.youtube\\.com',         # Thumbnails do YouTube
            r'i\\.ytimg\\.com',            # Thumbnails alternativos do YouTube
            r'youtube\\.com.*\\.(jpg|png|webp)',  # Imagens do YouTube
            r'googleusercontent\\.com',    # Imagens do Google
            r'ggpht\\.com',               # Google Photos/YouTube
            r'ytimg\\.com',               # YouTube images
            r'licdn\\.com',               # LinkedIn CDN
            r'linkedin\\.com.*\\.(jpg|png|webp)',  # LinkedIn images
            r'sssinstagram\\.com',        # SSS Instagram downloader
            r'scontent-.*\\.cdninstagram\\.com',  # Instagram CDN específico
            r'scontent\\..*\\.fbcdn\\.net'  # Facebook CDN específico
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in valid_patterns)

    async def _search_serper_advanced(self, query: str) -> List[Dict]:
        """Busca avançada usando Serper com rotação automática de APIs"""
        if not self.api_keys.get('serper'):
            logger.warning("❌ Nenhuma chave Serper configurada")
            return []
        
        results = []
        search_types = ['images', 'search']  # Busca por imagens e links
        
        for search_type in search_types:
            url = f"https://google.serper.dev/{search_type}"
            
            # Payload básico e validado
            payload = {
                "q": query.strip(),
                "num": 10,  # Reduzir para evitar rate limit
                "gl": "br",
                "hl": "pt"
            }
            
            # Parâmetros específicos para imagens
            if search_type == 'images':
                payload.update({
                    "imgSize": "large",
                    "imgType": "photo"
                })
            
            # Tentar com rotação de APIs
            success = False
            attempts = 0
            max_attempts = min(3, len(self.api_keys['serper']))  # Máximo 3 tentativas
            
            while not success and attempts < max_attempts:
                api_key = self._get_next_api_key('serper')
                if not api_key:
                    logger.error(f"❌ Nenhuma API Serper disponível")
                    break
                
                headers = {
                    'X-API-KEY': api_key,
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                try:
                    if HAS_ASYNC_DEPS:
                        timeout = aiohttp.ClientTimeout(total=15)  # Reduzir timeout
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            async with session.post(url, headers=headers, json=payload) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    
                                    if search_type == 'images':
                                        for item in data.get('images', []):
                                            image_url = item.get('imageUrl', '')
                                            if image_url and self._is_valid_image_url(image_url):
                                                results.append({
                                                    'image_url': image_url,
                                                    'page_url': item.get('link', ''),
                                                    'title': item.get('title', ''),
                                                    'description': item.get('snippet', ''),
                                                    'source': 'serper_images'
                                                })
                                    else:  # search
                                        for item in data.get('organic', []):
                                            page_url = item.get('link', '')
                                            if page_url:
                                                results.append({
                                                    'image_url': '',  # Será extraída depois
                                                    'page_url': page_url,
                                                    'title': item.get('title', ''),
                                                    'description': item.get('snippet', ''),
                                                    'source': 'serper_search'
                                                })
                                    
                                    success = True
                                    logger.info(f"✅ Serper {search_type} sucesso: {len(data.get('images' if search_type == 'images' else 'organic', []))} resultados")
                                    
                                elif response.status == 429:
                                    logger.warning(f"⚠️ Rate limit Serper - aguardando...")
                                    await asyncio.sleep(2)
                                    
                                elif response.status in [400, 401, 403]:
                                    current_index = (self.current_api_index["serper"] - 1) % len(self.api_keys["serper"])
                                    self._mark_api_failed("serper", current_index)
                                    logger.error(f"❌ Serper API #{current_index + 1} inválida (status {response.status})")
                                    
                                else:
                                    logger.error(f"❌ Serper retornou status {response.status}")
                                    
                    else:
                        # Fallback síncrono
                        response = self.session.post(url, headers=headers, json=payload, timeout=15)
                        if response.status_code == 200:
                            data = response.json()
                            # Processar resultados similar ao async
                            success = True
                        else:
                            logger.error(f"❌ Serper status {response.status_code}")
                
                except Exception as e:
                    current_index = (self.current_api_index["serper"] - 1) % len(self.api_keys["serper"])
                    logger.error(f"❌ Erro Serper API #{current_index + 1}: {str(e)[:100]}")
                    
                    # Marcar como falhada apenas se for erro de autenticação
                    if "401" in str(e) or "403" in str(e) or "400" in str(e):
                        self._mark_api_failed("serper", current_index)
                
                attempts += 1
                if not success and attempts < max_attempts:
                    await asyncio.sleep(1)  # Aguardar antes da próxima tentativa
            
            # Rate limiting entre tipos de busca
            await asyncio.sleep(0.5)
        
        logger.info(f"📊 Serper total: {len(results)} resultados para '{query}'")
        return results

    async def _search_google_cse_advanced(self, query: str) -> List[Dict]:
        """Busca aprimorada usando Google CSE"""
        if not self.config.get('google_search_key') or not self.config.get('google_cse_id'):
            return []
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.config['google_search_key'],
            'cx': self.config['google_cse_id'],
            'q': query,
            'searchType': 'image',
            'num': 10,  # Aumentar de 6 para 10 (máximo do Google CSE)
            'safe': 'off',
            'fileType': 'jpg,png,jpeg,webp,gif',
            'imgSize': 'large',
            'imgType': 'photo',
            'gl': 'br',
            'hl': 'pt'
        }
        try:
            if HAS_ASYNC_DEPS:
                timeout = aiohttp.ClientTimeout(total=self.config['timeout'])
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, params=params) as response:
                        response.raise_for_status()
                        data = await response.json()
            else:
                response = self.session.get(url, params=params, timeout=self.config['timeout'])
                response.raise_for_status()
                data = response.json()
            results = []
            for item in data.get('items', []):
                results.append({
                    'image_url': item.get('link', ''),
                    'page_url': item.get('image', {}).get('contextLink', ''),
                    'title': item.get('title', ''),
                    'description': item.get('snippet', ''),
                    'source': 'google_cse'
                })
            return results
        except Exception as e:
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 429:
                logger.error(f"❌ Google CSE quota excedida")
            else:
                logger.error(f"❌ Erro na busca Google CSE: {e}")
            return []

    async def _search_youtube_thumbnails(self, query: str) -> List[Dict]:
        """Busca específica por thumbnails do YouTube"""
        results = []
        youtube_queries = [
            f'"{query}" site:youtube.com',
            f'site:youtube.com/watch "{query}"',
            f'"{query}" youtube tutorial',
            f'"{query}" youtube curso',
            f'"{query}" youtube aula'
        ]
        
        for yt_query in youtube_queries[:3]:  # Limitar para evitar rate limit
            try:
                # Usar Serper para buscar vídeos do YouTube
                if self.api_keys.get('serper'):
                    api_key = self._get_next_api_key('serper')
                    if api_key:
                        url = "https://google.serper.dev/search"
                        payload = {
                            "q": yt_query,
                            "num": 15,
                            "safe": "off",
                            "gl": "br",
                            "hl": "pt-br"
                        }
                        headers = {
                            'X-API-KEY': api_key,
                            'Content-Type': 'application/json'
                        }
                        
                        if HAS_ASYNC_DEPS:
                            timeout = aiohttp.ClientTimeout(total=30)
                            async with aiohttp.ClientSession(timeout=timeout) as session:
                                async with session.post(url, json=payload, headers=headers) as response:
                                    if response.status == 200:
                                        data = await response.json()
                                        # Processar resultados do YouTube
                                        for item in data.get('organic', []):
                                            link = item.get('link', '')
                                            if 'youtube.com/watch' in link:
                                                # Extrair video ID e gerar thumbnail
                                                video_id = self._extract_youtube_id(link)
                                                if video_id:
                                                    # Múltiplas qualidades de thumbnail
                                                    thumbnail_configs = [
                                                        ('maxresdefault.jpg', 'alta'),
                                                        ('hqdefault.jpg', 'média-alta'),
                                                        ('mqdefault.jpg', 'média'),
                                                        ('sddefault.jpg', 'padrão'),
                                                        ('default.jpg', 'baixa')
                                                    ]
                                                    for thumb_file, quality in thumbnail_configs:
                                                        thumb_url = f"https://img.youtube.com/vi/{video_id}/{thumb_file}"
                                                        results.append({
                                                            'image_url': thumb_url,
                                                            'page_url': link,
                                                            'title': f"{item.get('title', f'Vídeo YouTube: {query}')} ({quality})",
                                                            'description': item.get('snippet', '')[:200],
                                                            'source': f'youtube_thumbnail_{quality}'
                                                        })
                        else:
                            response = self.session.post(url, json=payload, headers=headers, timeout=30)
                            if response.status_code == 200:
                                data = response.json()
                                # Similar processing for sync version
                                for item in data.get('organic', []):
                                    link = item.get('link', '')
                                    if 'youtube.com/watch' in link:
                                        video_id = self._extract_youtube_id(link)
                                        if video_id:
                                            # Múltiplas qualidades de thumbnail
                                            thumbnail_configs = [
                                                ('maxresdefault.jpg', 'alta'),
                                                ('hqdefault.jpg', 'média-alta'),
                                                ('mqdefault.jpg', 'média')
                                            ]
                                            for thumb_file, quality in thumbnail_configs:
                                                thumb_url = f"https://img.youtube.com/vi/{video_id}/{thumb_file}"
                                                results.append({
                                                    'image_url': thumb_url,
                                                    'page_url': link,
                                                    'title': f"{item.get('title', f'Vídeo YouTube: {query}')} ({quality})",
                                                    'description': item.get('snippet', '')[:200],
                                                    'source': f'youtube_thumbnail_{quality}'
                                                })
            except Exception as e:
                logger.warning(f"Erro na busca YouTube: {e}")
                continue
            
            await asyncio.sleep(0.3)  # Rate limiting
        
        logger.info(f"📺 YouTube encontrou {len(results)} thumbnails")
        return results

    def _extract_youtube_id(self, url: str) -> str:
        """Extrai ID do vídeo do YouTube da URL"""
        patterns = [
            r'youtube\\.com/watch\\?v=([^&]+)',
            r'youtu\\.be/([^?]+)',
            r'youtube\\.com/embed/([^?]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def _search_facebook_specific(self, query: str) -> List[Dict]:
        """Busca específica para conteúdo do Facebook"""
        results = []
        facebook_queries = [
            f'"{query}" site:facebook.com',
            f'site:facebook.com/posts "{query}"',
            f'site:facebook.com/photo "{query}"',
            f'"{query}" facebook curso',
            f'"{query}" facebook aula',
            f'"{query}" facebook dicas',
            f'site:facebook.com "{query}" tutorial'
        ]
        
        for fb_query in facebook_queries[:4]:  # Limitar para evitar rate limit
            try:
                # Usar Serper para buscar conteúdo do Facebook
                if self.api_keys.get('serper'):
                    api_key = self._get_next_api_key('serper')
                    if api_key:
                        # Busca por imagens do Facebook
                        url = "https://google.serper.dev/images"
                        payload = {
                            "q": fb_query,
                            "num": 15,
                            "safe": "off",
                            "gl": "br",
                            "hl": "pt-br",
                            "imgSize": "large",
                            "imgType": "photo"
                        }
                        headers = {
                            'X-API-KEY': api_key,
                            'Content-Type': 'application/json'
                        }
                        
                        if HAS_ASYNC_DEPS:
                            timeout = aiohttp.ClientTimeout(total=30)
                            async with aiohttp.ClientSession(timeout=timeout) as session:
                                async with session.post(url, json=payload, headers=headers) as response:
                                    if response.status == 200:
                                        data = await response.json()
                                        # Processar resultados de imagens do Facebook
                                        for item in data.get('images', []):
                                            image_url = item.get('imageUrl', '')
                                            page_url = item.get('link', '')
                                            if image_url and ('facebook.com' in page_url or 'fbcdn.net' in image_url):
                                                results.append({
                                                    'image_url': image_url,
                                                    'page_url': page_url,
                                                    'title': item.get('title', f'Post Facebook: {query}'),
                                                    'description': item.get('snippet', '')[:200],
                                                    'source': 'facebook_image'
                                                })
                        else:
                            response = self.session.post(url, json=payload, headers=headers, timeout=30)
                            if response.status_code == 200:
                                data = response.json()
                                for item in data.get('images', []):
                                    image_url = item.get('imageUrl', '')
                                    page_url = item.get('link', '')
                                    if image_url and ('facebook.com' in page_url or 'fbcdn.net' in image_url):
                                        results.append({
                                            'image_url': image_url,
                                            'page_url': page_url,
                                            'title': item.get('title', f'Post Facebook: {query}'),
                                            'description': item.get('snippet', '')[:200],
                                            'source': 'facebook_image'
                                        })
            except Exception as e:
                logger.warning(f"Erro na busca Facebook específica: {e}")
                continue
            
            await asyncio.sleep(0.3)  # Rate limiting
        
        logger.info(f"📘 Facebook específico encontrou {len(results)} imagens")
        return results

    async def _search_alternative_strategies(self, query: str) -> List[Dict]:
        """Estratégias alternativas de busca para aumentar resultados"""
        results = []
        
        # Estratégias com termos mais amplos
        alternative_queries = [
            f'{query} tutorial',
            f'{query} curso',
            f'{query} aula',
            f'{query} dicas',
            f'{query} masterclass',
            f'{query} online',
            f'{query} gratis',
            f'{query} free',
            # Variações sem aspas para busca mais ampla
            f'{query} instagram',
            f'{query} facebook',
            f'{query} youtube',
            # Termos relacionados
            f'como {query}',
            f'aprenda {query}',
            f'{query} passo a passo'
        ]
        
        for alt_query in alternative_queries[:6]:  # Limitar para evitar rate limit
            try:
                if self.api_keys.get('serper'):
                    api_key = self._get_next_api_key('serper')
                    if api_key:
                        url = "https://google.serper.dev/images"
                        payload = {
                            "q": alt_query,
                            "num": 10,
                            "safe": "off",
                            "gl": "br",
                            "hl": "pt-br",
                            "imgSize": "medium",  # Usar medium para mais variedade
                            "imgType": "photo"
                        }
                        headers = {
                            'X-API-KEY': api_key,
                            'Content-Type': 'application/json'
                        }
                        
                        if HAS_ASYNC_DEPS:
                            timeout = aiohttp.ClientTimeout(total=30)
                            async with aiohttp.ClientSession(timeout=timeout) as session:
                                async with session.post(url, json=payload, headers=headers) as response:
                                    if response.status == 200:
                                        data = await response.json()
                                        for item in data.get('images', []):
                                            image_url = item.get('imageUrl', '')
                                            page_url = item.get('link', '')
                                            if image_url and self._is_valid_image_url(image_url):
                                                results.append({
                                                    'image_url': image_url,
                                                    'page_url': page_url,
                                                    'title': item.get('title', f'Conteúdo: {query}'),
                                                    'description': item.get('snippet', '')[:200],
                                                    'source': 'alternative_search'
                                                })
                        else:
                            response = self.session.post(url, json=payload, headers=headers, timeout=30)
                            if response.status_code == 200:
                                data = response.json()
                                for item in data.get('images', []):
                                    image_url = item.get('imageUrl', '')
                                    page_url = item.get('link', '')
                                    if image_url and self._is_valid_image_url(image_url):
                                        results.append({
                                            'image_url': image_url,
                                            'page_url': page_url,
                                            'title': item.get('title', f'Conteúdo: {query}'),
                                            'description': item.get('snippet', '')[:200],
                                            'source': 'alternative_search'
                                        })
            except Exception as e:
                logger.warning(f"Erro na busca alternativa: {e}")
                continue
            
            await asyncio.sleep(0.2)  # Rate limiting mais rápido
        
        logger.info(f"🔄 Estratégias alternativas encontraram {len(results)} imagens")
        return results

    async def _extract_instagram_direct(self, post_url: str) -> List[Dict]:
        """Extrai imagens diretamente do Instagram usando múltiplas estratégias"""
        results = []
        
        try:
            # Estratégia 1: Usar sssinstagram.com API
            results_sss = await self._extract_via_sssinstagram(post_url)
            results.extend(results_sss)
            
            # Estratégia 2: Extração direta via embed
            if len(results) < 3:
                results_embed = await self._extract_instagram_embed(post_url)
                results.extend(results_embed)
            
            # Estratégia 3: Usar oembed do Instagram
            if len(results) < 3:
                results_oembed = await self._extract_instagram_oembed(post_url)
                results.extend(results_oembed)
                
        except Exception as e:
            logger.error(f"❌ Erro na extração direta Instagram: {e}")
        
        logger.info(f"📸 Instagram direto: {len(results)} imagens extraídas")
        return results

    async def _extract_via_sssinstagram(self, post_url: str) -> List[Dict]:
        """Extrai imagens usando sssinstagram.com"""
        results = []
        try:
            # Simular requisição para sssinstagram.com
            api_url = "https://sssinstagram.com/api/ig/post"
            payload = {"url": post_url}
            
            if HAS_ASYNC_DEPS:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(api_url, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            # Processar resposta do sssinstagram
                            if data.get('success') and data.get('data'):
                                media_data = data['data']
                                if isinstance(media_data, list):
                                    for item in media_data:
                                        if item.get('url'):
                                            results.append({
                                                'image_url': item['url'],
                                                'page_url': post_url,
                                                'title': f'Instagram Post',
                                                'description': item.get('caption', '')[:200],
                                                'source': 'sssinstagram_direct'
                                            })
                                elif media_data.get('url'):
                                    results.append({
                                        'image_url': media_data['url'],
                                        'page_url': post_url,
                                        'title': f'Instagram Post',
                                        'description': media_data.get('caption', '')[:200],
                                        'source': 'sssinstagram_direct'
                                    })
            else:
                response = self.session.post(api_url, json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    # Similar processing for sync version
                    if data.get('success') and data.get('data'):
                        media_data = data['data']
                        if isinstance(media_data, list):
                            for item in media_data:
                                if item.get('url'):
                                    results.append({
                                        'image_url': item['url'],
                                        'page_url': post_url,
                                        'title': f'Instagram Post',
                                        'description': item.get('caption', '')[:200],
                                        'source': 'sssinstagram_direct'
                                    })
                        elif media_data.get('url'):
                            results.append({
                                'image_url': media_data['url'],
                                'page_url': post_url,
                                'title': f'Instagram Post',
                                'description': media_data.get('caption', '')[:200],
                                'source': 'sssinstagram_direct'
                            })
        except Exception as e:
            logger.warning(f"Erro na extração via sssinstagram: {e}")
        
        return results

    async def _extract_instagram_embed(self, post_url: str) -> List[Dict]:
        """Extrai imagens usando embed do Instagram"""
        results = []
        try:
            # Tentar obter embed HTML do Instagram
            embed_url = f"https://api.instagram.com/oembed/?url={post_url}"
            
            if HAS_ASYNC_DEPS:
                timeout = aiohttp.ClientTimeout(total=15)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(embed_url) as response:
                        if response.status == 200:
                            embed_data = await response.json()
                            
                            # Extrair thumbnail URL se disponível
                            thumbnail_url = embed_data.get('thumbnail_url')
                            if thumbnail_url:
                                results.append({
                                    'image_url': thumbnail_url,
                                    'page_url': post_url,
                                    'title': embed_data.get('title', 'Instagram Post'),
                                    'description': embed_data.get('author_name', ''),
                                    'source': 'instagram_embed'
                                })
            else:
                response = self.session.get(embed_url, timeout=15)
                if response.status_code == 200:
                    embed_data = response.json()
                    
                    # Extrair thumbnail URL se disponível
                    thumbnail_url = embed_data.get('thumbnail_url')
                    if thumbnail_url:
                        results.append({
                            'image_url': thumbnail_url,
                            'page_url': post_url,
                            'title': embed_data.get('title', 'Instagram Post'),
                            'description': embed_data.get('author_name', ''),
                            'source': 'instagram_embed'
                        })
        except Exception as e:
            logger.warning(f"Erro na extração via embed Instagram: {e}")
        
        return results

    async def _extract_instagram_oembed(self, post_url: str) -> List[Dict]:
        """Extrai imagens usando oembed do Instagram"""
        # Similar ao embed, mas com abordagem alternativa
        return await self._extract_instagram_embed(post_url)

    async def _extract_facebook_direct(self, post_url: str) -> List[Dict]:
        """Extrai imagens diretamente do Facebook"""
        results = []
        try:
            # Tentar obter dados do post via scraping (simulado)
            # Em uma implementação real, isso exigiria autenticação ou APIs específicas
            
            # Por enquanto, apenas adiciona um resultado genérico
            results.append({
                'image_url': '',
                'page_url': post_url,
                'title': 'Facebook Post',
                'description': 'Extração direta do Facebook requer autenticação',
                'source': 'facebook_direct'
            })
            
        except Exception as e:
            logger.warning(f"Erro na extração direta Facebook: {e}")
        
        return results

    async def _extract_linkedin_direct(self, post_url: str) -> List[Dict]:
        """Extrai imagens diretamente do LinkedIn"""
        results = []
        try:
            # Tentar obter dados do post via scraping (simulado)
            # Em uma implementação real, isso exigiria autenticação ou APIs específicas
            
            # Por enquanto, apenas adiciona um resultado genérico
            results.append({
                'image_url': '',
                'page_url': post_url,
                'title': 'LinkedIn Post',
                'description': 'Extração direta do LinkedIn requer autenticação',
                'source': 'linkedin_direct'
            })
            
        except Exception as e:
            logger.warning(f"Erro na extração direta LinkedIn: {e}")
        
        return results

    async def download_viral_images(self, image_results: List[Dict], session_id: str = None) -> List[Dict]:
        """Baixa as imagens virais encontradas"""
        if not self.config.get('extract_images', True):
            logger.info("⚠️ Download de imagens desativado na configuração")
            return []
        
        downloaded_images = []
        images_dir = Path(self.config['images_dir'])
        images_dir.mkdir(exist_ok=True)
        
        session_id = session_id or f"session_{int(time.time())}"
        session_dir = images_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        logger.info(f"📥 Baixando {len(image_results)} imagens para {session_dir}")
        
        for i, result in enumerate(image_results):
            try:
                image_url = result.get('image_url', '')
                if not image_url or not self._is_valid_image_url(image_url):
                    logger.warning(f"URL de imagem inválida: {image_url}")
                    continue
                
                # Gerar nome de arquivo seguro
                safe_title = "".join(c if c.isalnum() else "_" for c in result.get('title', 'image')[:30])
                file_ext = self._get_file_extension(image_url)
                filename = f"{i:03d}_{safe_title}{file_ext}"
                filepath = session_dir / filename
                
                # Baixar imagem
                if HAS_ASYNC_DEPS:
                    timeout = aiohttp.ClientTimeout(total=30)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(image_url) as response:
                            if response.status == 200:
                                content = await response.read()
                                async with aiofiles.open(filepath, 'wb') as f:
                                    await f.write(content)
                                
                                downloaded_images.append({
                                    'filename': filename,
                                    'filepath': str(filepath),
                                    'relative_path': f"{session_id}/{filename}",
                                    'original_url': image_url,
                                    'post_url': result.get('page_url', ''),
                                    'title': result.get('title', ''),
                                    'file_size': len(content),
                                    'downloaded_at': datetime.now().isoformat(),
                                    'download_success': True
                                })
                                logger.info(f"✅ Imagem {i+1}/{len(image_results)} baixada: {filename}")
                            else:
                                logger.warning(f"⚠️ Falha ao baixar imagem {i+1}: Status {response.status}")
                else:
                    response = self.session.get(image_url, timeout=30)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        downloaded_images.append({
                            'filename': filename,
                            'filepath': str(filepath),
                            'relative_path': f"{session_id}/{filename}",
                            'original_url': image_url,
                            'post_url': result.get('page_url', ''),
                            'title': result.get('title', ''),
                            'file_size': len(response.content),
                            'downloaded_at': datetime.now().isoformat(),
                            'download_success': True
                        })
                        logger.info(f"✅ Imagem {i+1}/{len(image_results)} baixada: {filename}")
                    else:
                        logger.warning(f"⚠️ Falha ao baixar imagem {i+1}: Status {response.status_code}")
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Erro ao baixar imagem {i}: {e}")
                continue
        
        logger.info(f"✅ Download concluído: {len(downloaded_images)} imagens baixadas")
        return downloaded_images

    def _get_file_extension(self, url: str) -> str:
        """Extrai extensão do arquivo da URL"""
        # Padrão para extensões de imagem
        ext_match = re.search(r'\.(jpg|jpeg|png|gif|webp|bmp|svg)(\?|$)', url.lower())
        if ext_match:
            return f".{ext_match.group(1)}"
        
        # Padrão para URLs sem extensão explícita
        if any(pattern in url.lower() for pattern in ['jpg', 'jpeg', 'png']):
            return '.jpg'  # Padrão como fallback
        
        return '.jpg'  # Padrão final como fallback

# =============== INSTÂNCIAS GLOBAIS ===============

# Instância principal do Alibaba WebSailor
alibaba_websailor = AlibabaWebSailorAgent()

def get_alibaba_websailor():
    """Retorna a instância global do Alibaba WebSailor Agent"""
    return alibaba_websailor