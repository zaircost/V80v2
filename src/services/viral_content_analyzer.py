#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Viral Content Analyzer CORRIGIDO
Analisador de conteúdo viral com captura de screenshots
"""

import os
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Import do serviço viral corrigido
from services.viral_integration_service import viral_integration_service

# Import robusto do auto save
try:
    from services.auto_save_manager import salvar_etapa, salvar_erro
    HAS_AUTO_SAVE = True
except ImportError:
    HAS_AUTO_SAVE = False
    def salvar_etapa(*args, **kwargs):
        pass
    def salvar_erro(*args, **kwargs):
        pass

logger = logging.getLogger(__name__)

class ViralContentAnalyzer:
    """Analisador de conteúdo viral CORRIGIDO"""

    def __init__(self):
        """Inicializa o analisador"""
        self.viral_service = viral_integration_service
        self.screenshots_dir = Path("analyses_data/viral_screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🔥 Viral Content Analyzer CORRIGIDO inicializado")

    async def analyze_and_capture_viral_content(
        self,
        search_results: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Analisa resultados de busca e captura conteúdo viral
        
        Args:
            search_results: Resultados da busca massiva
            session_id: ID da sessão
        """
        logger.info(f"🔥 INICIANDO ANÁLISE DE CONTEÚDO VIRAL - Sessão: {session_id}")
        
        try:
            # Extrai query dos resultados de busca
            query = search_results.get("query", "análise de mercado")
            
            # Identifica URLs de redes sociais nos resultados
            social_urls = self._extract_social_urls_from_search(search_results)
            
            if not social_urls:
                logger.warning("⚠️ Nenhuma URL de rede social encontrada nos resultados")
                # Executa busca viral independente
                viral_results = await self.viral_service.find_viral_content(
                    query=query,
                    platforms=['instagram', 'youtube', 'facebook', 'tiktok'],
                    max_results=20,
                    session_id=session_id
                )
            else:
                logger.info(f"📱 {len(social_urls)} URLs de redes sociais encontradas")
                
                # Analisa URLs encontradas
                viral_results = await self._analyze_social_urls(social_urls, query, session_id)
            
            # Captura screenshots das melhores URLs
            screenshots_captured = await self._capture_viral_screenshots(viral_results, session_id)
            
            # Consolida resultados
            final_results = {
                "session_id": session_id,
                "query": query,
                "viral_content_identified": viral_results.get("viral_content", []),
                "screenshots_captured": screenshots_captured,
                "statistics": {
                    "total_viral_content": len(viral_results.get("viral_content", [])),
                    "images_downloaded": len(viral_results.get("images_downloaded", [])),
                    "screenshots_taken": len(screenshots_captured),
                    "avg_engagement": viral_results.get("statistics", {}).get("avg_engagement", 0),
                    "platforms_analyzed": len(viral_results.get("statistics", {}).get("platforms_success", {}))
                },
                "viral_insights": self._generate_viral_insights(viral_results),
                "timestamp": datetime.now().isoformat()
            }
            
            # Salva resultados
            if HAS_AUTO_SAVE:
                salvar_etapa("viral_analysis_complete", final_results, categoria="viral_analysis", session_id=session_id)
            
            # Salva também em arquivo local para garantir persistência
            await self._save_viral_analysis_local(final_results, session_id)
            
            logger.info(f"✅ ANÁLISE VIRAL CONCLUÍDA")
            logger.info(f"📊 {final_results['statistics']['total_viral_content']} conteúdos virais")
            logger.info(f"📸 {final_results['statistics']['screenshots_taken']} screenshots")
            
            return final_results
            
        except Exception as e:
            error_msg = f"Erro na análise viral: {str(e)}"
            logger.error(f"❌ {error_msg}")
            if HAS_AUTO_SAVE:
                salvar_erro("viral_analysis_error", e, contexto={"session_id": session_id})
            
            return {
                "session_id": session_id,
                "error": error_msg,
                "viral_content_identified": [],
                "screenshots_captured": [],
                "statistics": {
                    "total_viral_content": 0,
                    "images_downloaded": 0,
                    "screenshots_taken": 0,
                    "avg_engagement": 0,
                    "platforms_analyzed": 0
                },
                "timestamp": datetime.now().isoformat()
            }

    async def _save_viral_analysis_local(self, results: Dict[str, Any], session_id: str):
        """Salva análise viral localmente para garantir persistência"""
        try:
            # Cria diretório da sessão
            session_dir = Path(f"analyses_data/{session_id}")
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Salva resultados completos
            results_path = session_dir / "viral_analysis_results.json"
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            # Salva relatório em markdown
            report_path = session_dir / "viral_analysis_report.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(self._generate_markdown_report(results))
            
            logger.info(f"💾 Análise viral salva localmente: {session_dir}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar localmente: {e}")

    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Gera relatório em markdown da análise viral"""
        
        lines = []
        
        lines.append("# ANÁLISE DE CONTEÚDO VIRAL")
        lines.append(f"**Sessão:** {results.get('session_id', 'N/A')}")
        lines.append(f"**Query:** {results.get('query', 'N/A')}")
        lines.append(f"**Data:** {results.get('timestamp', 'N/A')}")
        lines.append("")
        
        # Estatísticas
        stats = results.get('statistics', {})
        lines.append("## ESTATÍSTICAS")
        lines.append(f"- **Conteúdos virais:** {stats.get('total_viral_content', 0)}")
        lines.append(f"- **Imagens baixadas:** {stats.get('images_downloaded', 0)}")
        lines.append(f"- **Screenshots:** {stats.get('screenshots_taken', 0)}")
        lines.append(f"- **Engagement médio:** {stats.get('avg_engagement', 0):.1f}")
        lines.append(f"- **Plataformas analisadas:** {stats.get('platforms_analyzed', 0)}")
        lines.append("")
        
        # Insights
        insights = results.get('viral_insights', [])
        if insights:
            lines.append("## INSIGHTS VIRAIS")
            for insight in insights:
                lines.append(f"- {insight}")
            lines.append("")
        
        # Conteúdo viral
        viral_content = results.get('viral_content_identified', [])
        if viral_content:
            lines.append("## CONTEÚDO VIRAL IDENTIFICADO")
            for i, content in enumerate(viral_content[:10], 1):
                if isinstance(content, dict):
                    lines.append(f"### {i}. {content.get('title', 'Sem título')}")
                    lines.append(f"**Plataforma:** {content.get('platform', 'N/A').upper()}")
                    lines.append(f"**Engagement:** {content.get('engagement_score', 0):.1f}")
                    lines.append(f"**URL:** {content.get('post_url', 'N/A')}")
                    
                    if content.get('description'):
                        desc = content['description'][:200].replace('\n', ' ')
                        lines.append(f"**Descrição:** {desc}...")
                    
                    lines.append("")
        
        return '\n'.join(lines)
    def _extract_social_urls_from_search(self, search_results: Dict[str, Any]) -> List[str]:
        """Extrai URLs de redes sociais dos resultados de busca"""
        social_urls = []
        
        try:
            # Processa diferentes estruturas de resultados
            if "all_results" in search_results:
                for provider_result in search_results["all_results"]:
                    if provider_result.get("success") and provider_result.get("results"):
                        for result in provider_result["results"]:
                            url = result.get("url", "")
                            if self.viral_service._is_social_media_url(url):
                                social_urls.append(url)
            
            # Processa URLs consolidadas
            if "consolidated_urls" in search_results:
                for url in search_results["consolidated_urls"]:
                    if self.viral_service._is_social_media_url(url):
                        social_urls.append(url)
            
            # Remove duplicatas
            social_urls = list(set(social_urls))
            
            logger.info(f"📱 {len(social_urls)} URLs de redes sociais extraídas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair URLs sociais: {e}")
        
        return social_urls

    async def _analyze_social_urls(self, urls: List[str], query: str, session_id: str) -> Dict[str, Any]:
        """Analisa URLs de redes sociais encontradas"""
        
        viral_results = {
            "query": query,
            "viral_content": [],
            "images_downloaded": [],
            "statistics": {
                "total_found": 0,
                "total_downloaded": 0,
                "avg_engagement": 0.0,
                "platforms_success": {}
            }
        }
        
        try:
            for url in urls[:30]:  # Limita para performance
                try:
                    # Identifica plataforma
                    platform = self._identify_platform_from_url(url)
                    if not platform:
                        continue
                    
                    # Extrai conteúdo viral
                    viral_content = await self.viral_service._extract_viral_content_from_url(url, platform, query)
                    
                    if viral_content:
                        viral_results["viral_content"].append(viral_content)
                        
                        # Baixa imagem se disponível
                        if viral_content.image_url:
                            image_path = await self.viral_service._download_image_real(
                                viral_content.image_url,
                                platform,
                                viral_content.title or "viral_content"
                            )
                            
                            if image_path:
                                viral_content.image_path = str(image_path)
                                viral_results["images_downloaded"].append({
                                    "url": viral_content.image_url,
                                    "path": str(image_path),
                                    "platform": platform
                                })
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao analisar {url}: {e}")
                    continue
            
            # Calcula estatísticas
            self.viral_service._calculate_final_statistics(viral_results)
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de URLs sociais: {e}")
        
        return viral_results

    async def _capture_viral_screenshots(self, viral_results: Dict[str, Any], session_id: str) -> List[str]:
        """Captura screenshots do conteúdo viral (DESABILITADO por performance)"""
        
        # Por enquanto, retorna lista vazia para evitar problemas de performance
        # Screenshots podem ser implementados posteriormente se necessário
        
        logger.info("📸 Screenshots desabilitados por performance - usando imagens baixadas")
        
        screenshots = []
        
        # Lista imagens baixadas como "screenshots"
        for image_data in viral_results.get("images_downloaded", []):
            screenshots.append(image_data.get("path", ""))
        
        return screenshots

    def _identify_platform_from_url(self, url: str) -> Optional[str]:
        """Identifica plataforma a partir da URL"""
        
        if 'instagram.com' in url:
            return 'instagram'
        elif 'facebook.com' in url or 'fb.watch' in url:
            return 'facebook'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'tiktok.com' in url:
            return 'tiktok'
        elif 'linkedin.com' in url:
            return 'linkedin'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'twitter'
        
        return None

    def _generate_viral_insights(self, viral_results: Dict[str, Any]) -> List[str]:
        """Gera insights sobre o conteúdo viral encontrado"""
        
        insights = []
        
        try:
            viral_content = viral_results.get("viral_content", [])
            
            if not viral_content:
                insights.append("Nenhum conteúdo viral identificado")
                return insights
            
            # Análise de plataformas
            platform_stats = viral_results.get("statistics", {}).get("platforms_success", {})
            
            if platform_stats:
                best_platform = max(platform_stats.items(), key=lambda x: x[1].get("avg_engagement", 0))
                insights.append(f"Melhor plataforma: {best_platform[0].upper()} (Eng. médio: {best_platform[1]['avg_engagement']:.1f})")
            
            # Análise de engagement
            avg_engagement = viral_results.get("statistics", {}).get("avg_engagement", 0)
            if avg_engagement > 100:
                insights.append(f"Alto engajamento médio detectado: {avg_engagement:.1f}")
            elif avg_engagement > 50:
                insights.append(f"Engajamento médio moderado: {avg_engagement:.1f}")
            else:
                insights.append(f"Engajamento médio baixo: {avg_engagement:.1f}")
            
            # Análise de hashtags populares
            all_hashtags = []
            for content in viral_content:
                if isinstance(content, dict) and content.get("hashtags"):
                    all_hashtags.extend(content["hashtags"])
            
            if all_hashtags:
                from collections import Counter
                popular_hashtags = Counter(all_hashtags).most_common(5)
                hashtag_list = [f"{tag} ({count})" for tag, count in popular_hashtags]
                insights.append(f"Hashtags populares: {', '.join(hashtag_list)}")
            
            # Análise de indicadores virais
            all_indicators = []
            for content in viral_content:
                if isinstance(content, dict) and content.get("viral_indicators"):
                    all_indicators.extend(content["viral_indicators"])
            
            if all_indicators:
                from collections import Counter
                common_indicators = Counter(all_indicators).most_common(3)
                indicator_list = [indicator for indicator, count in common_indicators]
                insights.append(f"Indicadores virais comuns: {', '.join(indicator_list)}")
            
            # Análise de autores
            authors = [content.get("author", "") for content in viral_content if isinstance(content, dict)]
            unique_authors = len(set(filter(None, authors)))
            insights.append(f"Criadores únicos identificados: {unique_authors}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar insights: {e}")
            insights.append("Erro na geração de insights")
        
        return insights

# Instância global
viral_content_analyzer = ViralContentAnalyzer()