#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste completo do Viral Integration Service
Executa análise real com os dados fornecidos
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, 'src')

async def main():
    """Executa teste completo do sistema viral"""
    
    print("🔥 TESTE COMPLETO DO VIRAL INTEGRATION SERVICE")
    print("=" * 60)
    
    # Dados de teste conforme solicitado
    test_data = {
        "publico": "Mulheres entre 35 e 80 anos, casadas e solteiras, donas de casa, aposentadas",
        "produto": "Grupo de whatsapp com dicas e video aulas de patchwork e costura criativa",
        "segmento": "Patchwork Descomplicado",
        "query": "Patchwork e Costura"
    }
    
    print(f"📋 Dados de teste:")
    for key, value in test_data.items():
        print(f"  {key}: {value}")
    print()
    
    try:
        # Importa o serviço
        from services.viral_integration_service import viral_integration_service
        from services.viral_content_analyzer import viral_content_analyzer
        
        print("✅ Serviços importados com sucesso")
        
        # Verifica status do serviço
        status = viral_integration_service.get_service_status()
        print(f"📊 Status do serviço:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        print()
        
        # TESTE 1: Busca viral direta
        print("🔍 TESTE 1: Busca viral direta")
        print("-" * 40)
        
        viral_results = await viral_integration_service.find_viral_content(
            query=test_data["query"],
            platforms=['instagram', 'youtube', 'facebook'],
            max_results=15,
            session_id="test_patchwork_001"
        )
        
        print(f"✅ Busca viral concluída")
        print(f"📊 Resultados:")
        print(f"  - Conteúdos encontrados: {len(viral_results.get('viral_content', []))}")
        print(f"  - Imagens baixadas: {len(viral_results.get('images_downloaded', []))}")
        print(f"  - Erros: {len(viral_results.get('errors', []))}")
        print(f"  - Warnings: {len(viral_results.get('warnings', []))}")
        
        if viral_results.get('errors'):
            print("⚠️ Erros encontrados:")
            for error in viral_results['errors'][:5]:
                print(f"    - {error}")
        
        print()
        
        # TESTE 2: Análise completa com captura
        print("🔥 TESTE 2: Análise completa com captura")
        print("-" * 40)
        
        # Simula resultados de busca
        mock_search_results = {
            "query": test_data["query"],
            "all_results": [
                {
                    "success": True,
                    "results": [
                        {"url": "https://www.instagram.com/p/example1/", "title": "Patchwork tutorial"},
                        {"url": "https://www.youtube.com/watch?v=example1", "title": "Costura criativa"}
                    ]
                }
            ],
            "consolidated_urls": [
                "https://www.instagram.com/p/example1/",
                "https://www.youtube.com/watch?v=example1"
            ]
        }
        
        analysis_results = await viral_content_analyzer.analyze_and_capture_viral_content(
            search_results=mock_search_results,
            session_id="test_patchwork_002"
        )
        
        print(f"✅ Análise completa concluída")
        print(f"📊 Resultados da análise:")
        print(f"  - Conteúdos virais: {analysis_results['statistics']['total_viral_content']}")
        print(f"  - Screenshots: {analysis_results['statistics']['screenshots_taken']}")
        print(f"  - Plataformas analisadas: {analysis_results['statistics']['platforms_analyzed']}")
        print()
        
        # TESTE 3: Verificação de arquivos gerados
        print("📁 TESTE 3: Verificação de arquivos gerados")
        print("-" * 40)
        
        # Verifica diretórios
        directories = [
            Path("viral_images_data"),
            Path("downloaded_images"),
            Path("analyses_data/viral_screenshots")
        ]
        
        for directory in directories:
            if directory.exists():
                files = list(directory.glob("*"))
                print(f"✅ {directory}: {len(files)} arquivos")
                
                # Lista primeiros 3 arquivos
                for file in files[:3]:
                    size = file.stat().st_size if file.is_file() else 0
                    print(f"    - {file.name} ({size} bytes)")
            else:
                print(f"❌ {directory}: Diretório não existe")
        
        print()
        
        # TESTE 4: Verificação de relatórios
        print("📄 TESTE 4: Verificação de relatórios gerados")
        print("-" * 40)
        
        # Procura arquivos de relatório
        report_files = []
        for pattern in ["viral_results_*.json", "viral_report_*.txt", "viral_incorporation_*.txt"]:
            report_files.extend(Path(".").glob(pattern))
            report_files.extend(Path("viral_images_data").glob(pattern))
        
        if report_files:
            print(f"✅ {len(report_files)} relatórios encontrados:")
            for report in report_files:
                size = report.stat().st_size
                print(f"    - {report.name} ({size} bytes)")
        else:
            print("❌ Nenhum relatório encontrado")
        
        print()
        
        # TESTE 5: Verificação de rotação de APIs
        print("🔄 TESTE 5: Verificação de rotação de APIs")
        print("-" * 40)
        
        try:
            from services.enhanced_api_rotation_manager import get_api_manager
            api_manager = get_api_manager()
            
            if api_manager:
                status_report = api_manager.get_api_status_report()
                print("✅ API Manager ativo")
                
                for service, apis in status_report['services'].items():
                    if apis.get('total_apis', 0) > 0:
                        active = apis.get('active', 0)
                        total = apis.get('total_apis', 0)
                        print(f"  - {service}: {active}/{total} APIs ativas")
            else:
                print("❌ API Manager não disponível")
                
        except Exception as e:
            print(f"❌ Erro ao verificar APIs: {e}")
        
        print()
        
        # Resumo final
        print("📋 RESUMO DO TESTE")
        print("=" * 60)
        
        total_content = len(viral_results.get('viral_content', []))
        total_images = len(viral_results.get('images_downloaded', []))
        total_errors = len(viral_results.get('errors', []))
        
        print(f"✅ Conteúdos virais encontrados: {total_content}")
        print(f"📸 Imagens baixadas: {total_images}")
        print(f"❌ Erros encontrados: {total_errors}")
        print(f"📄 Relatórios gerados: {len(report_files)}")
        
        # Avaliação geral
        if total_content > 0 and total_images > 0:
            print("🎉 TESTE PASSOU: Sistema viral funcionando!")
        elif total_content > 0:
            print("⚠️ TESTE PARCIAL: Conteúdo encontrado mas imagens não baixadas")
        else:
            print("❌ TESTE FALHOU: Nenhum conteúdo viral encontrado")
        
        return {
            "test_passed": total_content > 0,
            "content_found": total_content,
            "images_downloaded": total_images,
            "errors_count": total_errors,
            "reports_generated": len(report_files)
        }
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO NO TESTE: {e}")
        return {"test_passed": False, "error": str(e)}

if __name__ == "__main__":
    # Executa o teste
    test_results = asyncio.run(main())
    
    # Salva resultados do teste
    with open("test_viral_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Resultados salvos em: test_viral_results.json")