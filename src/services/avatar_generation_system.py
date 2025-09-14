#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Geração de 4 Avatares Únicos - V3.0
Gera perfis completos com nomes reais e análises personalizadas
"""
import os
import json
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, date
import logging

# Importar o sistema real de IA
try:
    from .enhanced_ai_manager import EnhancedAIManager
    HAS_AI_MANAGER = True
except ImportError:
    try:
        from enhanced_ai_manager import EnhancedAIManager
        HAS_AI_MANAGER = True
    except ImportError:
        HAS_AI_MANAGER = False

logger = logging.getLogger(__name__)

@dataclass
class DadosDemograficos:
    nome_completo: str
    idade: int
    genero: str
    estado_civil: str
    localizacao: str
    profissao: str
    renda_mensal: float
    escolaridade: str
    filhos: int

@dataclass
class PerfilPsicologico:
    personalidade_mbti: str
    valores_principais: List[str]
    medos_primarios: List[str]
    desejos_ocultos: List[str]
    motivadores_internos: List[str]
    padroes_comportamentais: List[str]
    gatilhos_emocionais: List[str]
    estilo_comunicacao: str

@dataclass
class ContextoDigital:
    plataformas_ativas: List[str]
    tempo_online_diario: int
    tipos_conteudo_consumido: List[str]
    influenciadores_seguidos: List[str]
    habitos_compra_online: Dict[str, Any]
    dispositivos_utilizados: List[str]
    horarios_pico_atividade: List[str]

@dataclass
class DoresEObjetivos:
    dor_primaria_emocional: str
    dor_secundaria_pratica: str
    frustracao_principal: str
    objetivo_principal: str
    objetivo_secundario: str
    sonho_secreto: str
    maior_medo: str
    maior_desejo: str

@dataclass
class ComportamentoConsumo:
    processo_decisao: List[str]
    fatores_influencia: List[str]
    objecoes_comuns: List[str]
    gatilhos_compra: List[str]
    canais_preferidos: List[str]
    ticket_medio: float
    frequencia_compra: str
    sensibilidade_preco: str

@dataclass
class AvatarCompleto:
    id_avatar: str
    dados_demograficos: DadosDemograficos
    perfil_psicologico: PerfilPsicologico
    contexto_digital: ContextoDigital
    dores_objetivos: DoresEObjetivos
    comportamento_consumo: ComportamentoConsumo
    historia_pessoal: str
    dia_na_vida: str
    jornada_cliente: Dict[str, str]
    drivers_mentais_efetivos: List[str]
    estrategia_abordagem: Dict[str, str]
    scripts_personalizados: Dict[str, str]
    metricas_conversao: Dict[str, float]

class AvatarGenerationSystem:
    """
    Sistema avançado de geração de avatares únicos e realistas
    """
    def __init__(self):
        if HAS_AI_MANAGER:
            self.ai_manager = EnhancedAIManager()
            logger.info("✅ Avatar Generation System inicializado com Enhanced AI Manager")
        else:
            self.ai_manager = None
            logger.warning("⚠️ Enhanced AI Manager não disponível, usando fallback")
        
        # Databases dinâmicos removidos - agora usa geração via IA

    async def _generate_nome_dinamico(self, genero: str, contexto_nicho: str = "") -> str:
        """Gera nome dinâmico usando IA baseado no contexto do nicho"""
        try:
            if self.ai_manager:
                prompt = f"""
                Gere um nome completo brasileiro REAL e comum para uma pessoa do gênero {genero.lower()}.
                Contexto do nicho: {contexto_nicho}
                
                Requisitos:
                - Nome + sobrenome brasileiro comum
                - Adequado para o contexto profissional do nicho
                - Sem caracteres especiais
                - Formato: Nome Sobrenome
                
                Responda APENAS com o nome completo, sem explicações.
                """
                
                nome = await self.ai_manager.generate_content(prompt, model_preference='gemini')
                return nome.strip()
            else:
                # Fallback usando geração aleatória baseada em padrões brasileiros
                import random
                primeiros_nomes_m = ['João', 'Carlos', 'Rafael', 'Lucas', 'Pedro', 'Felipe', 'Bruno', 'Thiago', 'Diego', 'Mateus']
                primeiros_nomes_f = ['Maria', 'Ana', 'Juliana', 'Camila', 'Larissa', 'Gabriela', 'Priscila', 'Tatiane', 'Vanessa', 'Renata']
                sobrenomes = ['Silva', 'Santos', 'Oliveira', 'Costa', 'Lima', 'Ferreira', 'Martins', 'Pereira', 'Souza', 'Carvalho']
                
                if genero.lower() == 'masculino':
                    primeiro = random.choice(primeiros_nomes_m)
                else:
                    primeiro = random.choice(primeiros_nomes_f)
                
                sobrenome = random.choice(sobrenomes)
                return f"{primeiro} {sobrenome}"
                
        except Exception as e:
            logger.warning(f"Erro ao gerar nome dinâmico: {e}")
            # Fallback final
            return "João Silva" if genero.lower() == 'masculino' else "Maria Santos"

    async def _generate_profissao_dinamica(self, contexto_nicho: str, faixa_renda: str) -> Dict[str, Any]:
        """Gera profissão dinâmica usando IA baseada no contexto do nicho"""
        try:
            if self.ai_manager:
                prompt = f"""
                Gere uma profissão brasileira REAL adequada para o contexto: {contexto_nicho}
                Faixa de renda desejada: {faixa_renda}
                
                Retorne APENAS um JSON no formato:
                {{
                    "nome": "Nome da profissão",
                    "renda_min": valor_minimo_numerico,
                    "renda_max": valor_maximo_numerico,
                    "escolaridade": "Médio/Superior/Técnico"
                }}
                
                Requisitos:
                - Profissão real e comum no Brasil
                - Valores de renda realistas para 2024
                - Adequada ao contexto do nicho
                """
                
                response = await self.ai_manager.generate_content(prompt, model_preference='gemini')
                import json
                profissao_data = json.loads(response.strip())
                return profissao_data
            else:
                # Fallback com profissões baseadas no contexto
                import random
                profissoes_contexto = {
                    'tecnologia': [
                        {'nome': 'Desenvolvedor de Software', 'renda_min': 5500, 'renda_max': 15000, 'escolaridade': 'Superior'},
                        {'nome': 'Analista de Sistemas', 'renda_min': 4500, 'renda_max': 12000, 'escolaridade': 'Superior'}
                    ],
                    'saude': [
                        {'nome': 'Fisioterapeuta', 'renda_min': 3800, 'renda_max': 8500, 'escolaridade': 'Superior'},
                        {'nome': 'Nutricionista', 'renda_min': 3200, 'renda_max': 7500, 'escolaridade': 'Superior'}
                    ],
                    'default': [
                        {'nome': 'Analista de Marketing', 'renda_min': 4500, 'renda_max': 8500, 'escolaridade': 'Superior'},
                        {'nome': 'Administrador', 'renda_min': 3500, 'renda_max': 10000, 'escolaridade': 'Superior'}
                    ]
                }
                
                contexto_key = 'default'
                for key in profissoes_contexto.keys():
                    if key in contexto_nicho.lower():
                        contexto_key = key
                        break
                
                return random.choice(profissoes_contexto[contexto_key])
                
        except Exception as e:
            logger.warning(f"Erro ao gerar profissão dinâmica: {e}")
            # Fallback final
            return {'nome': 'Analista de Marketing', 'renda_min': 4500, 'renda_max': 8500, 'escolaridade': 'Superior'}

    async def _generate_localizacao_dinamica(self, contexto_nicho: str) -> str:
        """Gera localização dinâmica usando IA baseada no contexto do nicho"""
        try:
            if self.ai_manager:
                prompt = f"""
                Gere uma localização brasileira REAL (cidade, estado) adequada para o contexto: {contexto_nicho}
                
                Requisitos:
                - Cidade real brasileira
                - Formato: "Cidade, UF"
                - Adequada ao contexto do nicho
                - Considere centros econômicos relevantes
                
                Responda APENAS com a localização no formato "Cidade, UF", sem explicações.
                """
                
                localizacao = await self.ai_manager.generate_content(prompt, model_preference='gemini')
                return localizacao.strip()
            else:
                # Fallback com localizações baseadas no contexto
                import random
                localizacoes_contexto = {
                    'tecnologia': ['São Paulo, SP', 'Florianópolis, SC', 'Belo Horizonte, MG', 'Campinas, SP'],
                    'saude': ['São Paulo, SP', 'Rio de Janeiro, RJ', 'Brasília, DF', 'Porto Alegre, RS'],
                    'educacao': ['São Paulo, SP', 'Rio de Janeiro, RJ', 'Brasília, DF', 'Belo Horizonte, MG'],
                    'default': ['São Paulo, SP', 'Rio de Janeiro, RJ', 'Belo Horizonte, MG', 'Brasília, DF', 
                               'Salvador, BA', 'Fortaleza, CE', 'Curitiba, PR', 'Recife, PE', 'Porto Alegre, RS']
                }
                
                contexto_key = 'default'
                for key in localizacoes_contexto.keys():
                    if key in contexto_nicho.lower():
                        contexto_key = key
                        break
                
                return random.choice(localizacoes_contexto[contexto_key])
                
        except Exception as e:
            logger.warning(f"Erro ao gerar localização dinâmica: {e}")
            # Fallback final
            return "São Paulo, SP"

    async def gerar_4_avatares_completos(self, contexto_nicho: str, 
                                       dados_pesquisa: Dict[str, Any]) -> List[AvatarCompleto]:
        """
        Gera 4 avatares únicos e completos para o nicho
        """
        logger.info(f"👥 Gerando 4 avatares únicos para: {contexto_nicho}")
        avatares = []
        # Definir arquétipos base para diversidade
        arquetipos = [
            {
                'tipo': 'Iniciante Ambicioso',
                'caracteristicas': 'Jovem, motivado, pouca experiência, alta energia',
                'faixa_etaria': (25, 35),
                'renda_faixa': 'media_baixa'
            },
            {
                'tipo': 'Profissional Estabelecido',
                'caracteristicas': 'Experiente, estável, busca otimização, pragmático',
                'faixa_etaria': (35, 45),
                'renda_faixa': 'media_alta'
            },
            {
                'tipo': 'Empreendedor Frustrado',
                'caracteristicas': 'Tentou várias vezes, cético, mas ainda esperançoso',
                'faixa_etaria': (30, 50),
                'renda_faixa': 'variavel'
            },
            {
                'tipo': 'Expert Buscando Evolução',
                'caracteristicas': 'Muito conhecimento, busca próximo nível, exigente',
                'faixa_etaria': (40, 55),
                'renda_faixa': 'alta'
            }
        ]

        for i, arquetipo in enumerate(arquetipos):
            logger.info(f"🎭 Gerando avatar {i+1}: {arquetipo['tipo']}")
            avatar = await self._gerar_avatar_individual(
                f"avatar_{i+1}",
                arquetipo,
                contexto_nicho,
                dados_pesquisa
            )
            avatares.append(avatar)
        
        logger.info(f"✅ 4 avatares únicos gerados com sucesso")
        return avatares

    async def _gerar_avatar_individual(self, avatar_id: str, arquetipo: Dict[str, Any],
                                     contexto_nicho: str, dados_pesquisa: Dict[str, Any]) -> AvatarCompleto:
        """
        Gera um avatar individual completo
        """
        # Gerar dados demográficos
        demograficos = await self._gerar_dados_demograficos(arquetipo, contexto_nicho)
        
        # Gerar perfil psicológico usando IA
        psicologico = await self._gerar_perfil_psicologico(demograficos, arquetipo, contexto_nicho)
        
        # Gerar contexto digital
        digital = self._gerar_contexto_digital(demograficos, psicologico)
        
        # Gerar dores e objetivos
        dores_objetivos = await self._gerar_dores_objetivos(demograficos, psicologico, contexto_nicho)
        
        # Gerar comportamento de consumo
        comportamento = await self._gerar_comportamento_consumo(demograficos, psicologico, contexto_nicho)
        
        # Gerar história pessoal
        historia = await self._gerar_historia_pessoal(demograficos, psicologico, dores_objetivos)
        
        # Gerar dia na vida
        dia_vida = await self._gerar_dia_na_vida(demograficos, psicologico, digital)
        
        # Gerar jornada do cliente
        jornada = await self._gerar_jornada_cliente(demograficos, comportamento, contexto_nicho)
        
        # Identificar drivers mentais efetivos
        drivers_efetivos = self._identificar_drivers_efetivos(psicologico, dores_objetivos)
        
        # Gerar estratégia de abordagem
        estrategia = await self._gerar_estrategia_abordagem(demograficos, psicologico, drivers_efetivos)
        
        # Gerar scripts personalizados
        scripts = await self._gerar_scripts_personalizados(demograficos, psicologico, estrategia)
        
        # Calcular métricas de conversão esperadas
        metricas = self._calcular_metricas_conversao(psicologico, comportamento)

        avatar = AvatarCompleto(
            id_avatar=avatar_id,
            dados_demograficos=demograficos,
            perfil_psicologico=psicologico,
            contexto_digital=digital,
            dores_objetivos=dores_objetivos,
            comportamento_consumo=comportamento,
            historia_pessoal=historia,
            dia_na_vida=dia_vida,
            jornada_cliente=jornada,
            drivers_mentais_efetivos=drivers_efetivos,
            estrategia_abordagem=estrategia,
            scripts_personalizados=scripts,
            metricas_conversao=metricas
        )
        return avatar

    async def _gerar_dados_demograficos(self, arquetipo: Dict[str, Any], contexto_nicho: str) -> DadosDemograficos:
        """Gera dados demográficos realistas usando IA dinâmica"""
        # Selecionar gênero aleatoriamente
        genero = random.choice(['Masculino', 'Feminino'])
        
        # Gerar nome dinâmico baseado no contexto
        nome = await self._generate_nome_dinamico(genero, contexto_nicho)
        
        # Gerar idade dentro da faixa do arquétipo
        idade = random.randint(*arquetipo['faixa_etaria'])
        
        # Gerar profissão dinâmica baseada no contexto
        profissao_data = await self._generate_profissao_dinamica(contexto_nicho, arquetipo['renda_faixa'])
        
        # Ajustar renda baseada na faixa do arquétipo
        renda_base = random.randint(profissao_data['renda_min'], profissao_data['renda_max'])
        if arquetipo['renda_faixa'] == 'media_baixa':
            renda = renda_base * random.uniform(0.7, 1.0)
        elif arquetipo['renda_faixa'] == 'media_alta':
            renda = renda_base * random.uniform(1.0, 1.4)
        elif arquetipo['renda_faixa'] == 'alta':
            renda = renda_base * random.uniform(1.3, 2.0)
        else:  # variável
            renda = renda_base * random.uniform(0.6, 1.8)
        
        # Estado civil baseado na idade
        if idade < 28:
            estado_civil = random.choice(['Solteiro(a)', 'Solteiro(a)', 'Namorando'])
        elif idade < 35:
            estado_civil = random.choice(['Solteiro(a)', 'Casado(a)', 'Namorando'])
        else:
            estado_civil = random.choice(['Casado(a)', 'Casado(a)', 'Divorciado(a)', 'Solteiro(a)'])
        
        # Filhos baseado na idade e estado civil
        if idade < 25 or estado_civil == 'Solteiro(a)':
            filhos = 0
        elif estado_civil == 'Casado(a)' and idade > 30:
            filhos = random.choice([0, 1, 2, 2])
        else:
            filhos = random.choice([0, 0, 1])
        
        # Gerar localização dinâmica baseada no contexto
        localizacao = await self._generate_localizacao_dinamica(contexto_nicho)
        
        return DadosDemograficos(
            nome_completo=nome,
            idade=idade,
            genero=genero,
            estado_civil=estado_civil,
            localizacao=localizacao,
            profissao=profissao_data['nome'],
            renda_mensal=round(renda, 2),
            escolaridade=profissao_data['escolaridade'],
            filhos=filhos
        )

    async def _gerar_perfil_psicologico(self, demograficos: DadosDemograficos, 
                                      arquetipo: Dict[str, Any], contexto_nicho: str) -> PerfilPsicologico:
        """Gera perfil psicológico detalhado usando IA"""
        prompt = f"""
        # GERAÇÃO DE PERFIL PSICOLÓGICO DETALHADO
        ## DADOS DEMOGRÁFICOS
        - Nome: {demograficos.nome_completo}
        - Idade: {demograficos.idade} anos
        - Profissão: {demograficos.profissao}
        - Renda: R$ {demograficos.renda_mensal:,.2f}
        - Estado Civil: {demograficos.estado_civil}
        - Filhos: {demograficos.filhos}
        - Localização: {demograficos.localizacao}
        ## ARQUÉTIPO
        - Tipo: {arquetipo['tipo']}
        - Características: {arquetipo['caracteristicas']}
        ## CONTEXTO DO NICHO
        {contexto_nicho}
        ## TAREFA
        Crie um perfil psicológico REALISTA e ESPECÍFICO para esta pessoa, considerando:
        1. **Personalidade MBTI**: Escolha o tipo mais provável baseado nos dados
        2. **Valores Principais**: 5 valores que realmente guiam suas decisões
        3. **Medos Primários**: 3 medos profundos e específicos
        4. **Desejos Ocultos**: 3 desejos que ela não admite publicamente
        5. **Motivadores Internos**: 4 coisas que realmente a movem
        6. **Padrões Comportamentais**: 5 comportamentos típicos
        7. **Gatilhos Emocionais**: 4 coisas que despertam emoções fortes
        8. **Estilo de Comunicação**: Como ela prefere se comunicar
        Formato JSON:
        {{
            "personalidade_mbti": "XXXX",
            "valores_principais": ["valor1", "valor2", "valor3", "valor4", "valor5"],
            "medos_primarios": ["medo1", "medo2", "medo3"],
            "desejos_ocultos": ["desejo1", "desejo2", "desejo3"],
            "motivadores_internos": ["motivador1", "motivador2", "motivador3", "motivador4"],
            "padroes_comportamentais": ["padrao1", "padrao2", "padrao3", "padrao4", "padrao5"],
            "gatilhos_emocionais": ["gatilho1", "gatilho2", "gatilho3", "gatilho4"],
            "estilo_comunicacao": "Descrição do estilo"
        }}
        IMPORTANTE: Seja ESPECÍFICO e REALISTA. Evite generalidades.
        """
        try:
            if self.ai_manager:
                response = await self.ai_manager.generate_text(prompt, max_tokens=2048, temperature=0.7)
                # Tentar extrair JSON da resposta
                if response:
                    # Procurar por JSON na resposta
                    start_idx = response.find('{')
                    end_idx = response.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response[start_idx:end_idx]
                        psico_data = json.loads(json_str)
                        return PerfilPsicologico(
                            personalidade_mbti=psico_data.get('personalidade_mbti', 'INTJ'),
                            valores_principais=psico_data.get('valores_principais', ['Crescimento', 'Autonomia', 'Impacto']),
                            medos_primarios=psico_data.get('medos_primarios', ['Fracasso', 'Rejeição', 'Instabilidade']),
                            desejos_ocultos=psico_data.get('desejos_ocultos', ['Reconhecimento', 'Liberdade', 'Impacto']),
                            motivadores_internos=psico_data.get('motivadores_internos', ['Crescimento', 'Segurança', 'Realização']),
                            padroes_comportamentais=psico_data.get('padroes_comportamentais', ['Planejamento', 'Análise', 'Cautela']),
                            gatilhos_emocionais=psico_data.get('gatilhos_emocionais', ['Injustiça', 'Ineficiência', 'Desrespeito']),
                            estilo_comunicacao=psico_data.get('estilo_comunicacao', 'Direto e objetivo')
                        )
                    else:
                        logger.warning("Resposta da IA não contém JSON válido, usando fallback")
                        return self._gerar_perfil_psicologico_fallback(demograficos, arquetipo)
                else:
                    logger.warning("Resposta vazia da IA, usando fallback")
                    return self._gerar_perfil_psicologico_fallback(demograficos, arquetipo)
            else:
                logger.warning("AI Manager não disponível, usando fallback")
                return self._gerar_perfil_psicologico_fallback(demograficos, arquetipo)
        except Exception as e:
            logger.error(f"❌ Erro na geração psicológica: {e}")
            return self._gerar_perfil_psicologico_fallback(demograficos, arquetipo)

    def _gerar_perfil_psicologico_fallback(self, demograficos: DadosDemograficos, 
                                         arquetipo: Dict[str, Any]) -> PerfilPsicologico:
        """Gera perfil psicológico básico quando IA não está disponível"""
        mbti_options = ['ENTJ', 'ENFJ', 'INTJ', 'INFJ', 'ESTP', 'ESFP', 'ISTP', 'ISFP',
                       'ESTJ', 'ESFJ', 'ISTJ', 'ISFJ', 'ENTP', 'ENFP', 'INTP', 'INFP']
        return PerfilPsicologico(
            personalidade_mbti=random.choice(mbti_options),
            valores_principais=['Família', 'Sucesso profissional', 'Segurança financeira', 'Reconhecimento', 'Liberdade'],
            medos_primarios=['Fracasso', 'Rejeição', 'Instabilidade financeira'],
            desejos_ocultos=['Reconhecimento público', 'Liberdade total', 'Impacto significativo'],
            motivadores_internos=['Crescimento pessoal', 'Segurança', 'Realização', 'Conexão'],
            padroes_comportamentais=['Planejamento detalhado', 'Busca por aprovação', 'Procrastinação em decisões grandes', 'Comparação com outros', 'Busca por eficiência'],
            gatilhos_emocionais=['Injustiça', 'Desrespeito', 'Incerteza', 'Pressão social'],
            estilo_comunicacao='Direto mas cordial, prefere exemplos práticos e dados concretos'
        )

    def _gerar_contexto_digital(self, demograficos: DadosDemograficos, 
                               psicologico: PerfilPsicologico) -> ContextoDigital:
        """Gera contexto digital baseado no perfil"""
        # Plataformas baseadas na idade e perfil
        if demograficos.idade < 30:
            plataformas = ['Instagram', 'TikTok', 'YouTube', 'WhatsApp', 'LinkedIn']
        elif demograficos.idade < 40:
            plataformas = ['Instagram', 'Facebook', 'YouTube', 'WhatsApp', 'LinkedIn']
        else:
            plataformas = ['Facebook', 'WhatsApp', 'YouTube', 'LinkedIn', 'Instagram']
        # Tempo online baseado na profissão
        if 'Digital' in demograficos.profissao or 'Desenvolvedor' in demograficos.profissao:
            tempo_online = random.randint(6, 10)
        else:
            tempo_online = random.randint(2, 5)
        return ContextoDigital(
            plataformas_ativas=plataformas,
            tempo_online_diario=tempo_online,
            tipos_conteudo_consumido=['Educacional', 'Entretenimento', 'Notícias', 'Inspiracional'],
            influenciadores_seguidos=['Especialistas do nicho', 'Empreendedores', 'Coaches'],
            habitos_compra_online={
                'frequencia': 'Semanal' if demograficos.renda_mensal > 5000 else 'Mensal',
                'valor_medio': demograficos.renda_mensal * 0.1,
                'categorias': ['Educação', 'Tecnologia', 'Lifestyle']
            },
            dispositivos_utilizados=['Smartphone', 'Notebook', 'Tablet'],
            horarios_pico_atividade=['07:00-09:00', '12:00-13:00', '19:00-22:00']
        )

    async def _gerar_dores_objetivos(self, demograficos: DadosDemograficos,
                                   psicologico: PerfilPsicologico, contexto_nicho: str) -> DoresEObjetivos:
        """Gera dores e objetivos específicos"""
        prompt = f"""
        # IDENTIFICAÇÃO DE DORES E OBJETIVOS ESPECÍFICOS
        ## PERFIL DA PESSOA
        - Nome: {demograficos.nome_completo}
        - Idade: {demograficos.idade} anos
        - Profissão: {demograficos.profissao}
        - Renda: R$ {demograficos.renda_mensal:,.2f}
        - Personalidade: {psicologico.personalidade_mbti}
        - Medos: {', '.join(psicologico.medos_primarios)}
        - Desejos: {', '.join(psicologico.desejos_ocultos)}
        ## CONTEXTO DO NICHO
        {contexto_nicho}
        ## TAREFA
        Identifique as dores e objetivos ESPECÍFICOS desta pessoa no contexto do nicho:
        1. **Dor Primária Emocional**: A dor emocional mais profunda
        2. **Dor Secundária Prática**: O problema prático do dia a dia
        3. **Frustração Principal**: O que mais a frustra atualmente
        4. **Objetivo Principal**: O que ela mais quer alcançar
        5. **Objetivo Secundário**: Segundo objetivo em importância
        6. **Sonho Secreto**: O que ela sonha mas não conta para ninguém
        7. **Maior Medo**: O que ela mais teme que aconteça
        8. **Maior Desejo**: O que ela mais deseja profundamente
        Formato JSON:
        {{
            "dor_primaria_emocional": "Dor emocional específica",
            "dor_secundaria_pratica": "Problema prático específico",
            "frustracao_principal": "Frustração específica",
            "objetivo_principal": "Objetivo principal específico",
            "objetivo_secundario": "Objetivo secundário específico",
            "sonho_secreto": "Sonho secreto específico",
            "maior_medo": "Maior medo específico",
            "maior_desejo": "Maior desejo específico"
        }}
        IMPORTANTE: Seja ESPECÍFICO para esta pessoa e contexto!
        """
        try:
            if self.ai_manager:
                response = await self.ai_manager.generate_text(prompt, max_tokens=1024, temperature=0.7)
                if response:
                    # Procurar por JSON na resposta
                    start_idx = response.find('{')
                    end_idx = response.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response[start_idx:end_idx]
                        dores_data = json.loads(json_str)
                        return DoresEObjetivos(
                            dor_primaria_emocional=dores_data.get('dor_primaria_emocional', 'Sensação de estagnação profissional'),
                            dor_secundaria_pratica=dores_data.get('dor_secundaria_pratica', 'Falta de tempo para crescimento'),
                            frustracao_principal=dores_data.get('frustracao_principal', 'Ver outros progredindo'),
                            objetivo_principal=dores_data.get('objetivo_principal', 'Alcançar próximo nível na carreira'),
                            objetivo_secundario=dores_data.get('objetivo_secundario', 'Ter mais segurança financeira'),
                            sonho_secreto=dores_data.get('sonho_secreto', 'Ser reconhecido como referência'),
                            maior_medo=dores_data.get('maior_medo', 'Ficar para trás'),
                            maior_desejo=dores_data.get('maior_desejo', 'Ter liberdade e autonomia')
                        )
                    else:
                        logger.warning("Resposta da IA não contém JSON válido para dores/objetivos, usando fallback")
                        return self._gerar_dores_objetivos_fallback(demograficos, psicologico)
                else:
                    logger.warning("Resposta vazia da IA para dores/objetivos, usando fallback")
                    return self._gerar_dores_objetivos_fallback(demograficos, psicologico)
            else:
                logger.warning("AI Manager não disponível para dores/objetivos, usando fallback")
                return self._gerar_dores_objetivos_fallback(demograficos, psicologico)
        except Exception as e:
            logger.error(f"❌ Erro na geração de dores/objetivos: {e}")
            return self._gerar_dores_objetivos_fallback(demograficos, psicologico)

    def _gerar_dores_objetivos_fallback(self, demograficos: DadosDemograficos,
                                      psicologico: PerfilPsicologico) -> DoresEObjetivos:
        """Fallback para dores e objetivos"""
        return DoresEObjetivos(
            dor_primaria_emocional="Sensação de estar estagnado profissionalmente",
            dor_secundaria_pratica="Falta de tempo para se dedicar ao crescimento",
            frustracao_principal="Ver outros progredindo enquanto se sente parado",
            objetivo_principal="Alcançar próximo nível na carreira",
            objetivo_secundario="Ter mais segurança financeira",
            sonho_secreto="Ser reconhecido como referência na área",
            maior_medo="Ficar para trás e se tornar irrelevante",
            maior_desejo="Ter liberdade e autonomia total"
        )

    async def _gerar_comportamento_consumo(self, demograficos: DadosDemograficos,
                                         psicologico: PerfilPsicologico, contexto_nicho: str) -> ComportamentoConsumo:
        """Gera comportamento de consumo específico"""
        # Processo de decisão baseado na personalidade
        if psicologico.personalidade_mbti[0] == 'E':  # Extrovertido
            processo = ['Busca opinião de outros', 'Pesquisa online', 'Compara opções', 'Decide rapidamente']
        else:  # Introvertido
            processo = ['Pesquisa extensiva', 'Analisa prós e contras', 'Reflete sozinho', 'Decide com cautela']
        # Sensibilidade ao preço baseada na renda
        if demograficos.renda_mensal > 8000:
            sensibilidade = 'Baixa - foca no valor'
        elif demograficos.renda_mensal > 4000:
            sensibilidade = 'Média - equilibra preço e valor'
        else:
            sensibilidade = 'Alta - muito sensível ao preço'
        return ComportamentoConsumo(
            processo_decisao=processo,
            fatores_influencia=['Recomendações', 'Prova social', 'Garantias', 'Autoridade'],
            objecoes_comuns=['Preço', 'Tempo', 'Ceticismo', 'Prioridades'],
            gatilhos_compra=['Urgência', 'Escassez', 'Bônus', 'Garantia'],
            canais_preferidos=['WhatsApp', 'Email', 'Instagram', 'Site'],
            ticket_medio=demograficos.renda_mensal * 0.05,
            frequencia_compra='Mensal' if demograficos.renda_mensal > 5000 else 'Trimestral',
            sensibilidade_preco=sensibilidade
        )

    async def _gerar_historia_pessoal(self, demograficos: DadosDemograficos,
                                     psicologico: PerfilPsicologico, dores: DoresEObjetivos) -> str:
        """Gera história pessoal envolvente"""
        prompt = f"""
        Crie uma história pessoal REALISTA e ENVOLVENTE para:
        {demograficos.nome_completo}, {demograficos.idade} anos, {demograficos.profissao}
        Personalidade: {psicologico.personalidade_mbti}
        Dor principal: {dores.dor_primaria_emocional}
        Objetivo: {dores.objetivo_principal}
        A história deve ter:
        - Background familiar e educacional
        - Momentos marcantes da carreira
        - Desafios enfrentados
        - Conquistas importantes
        - Situação atual
        Máximo 300 palavras, tom narrativo e humanizado.
        """
        try:
            if self.ai_manager:
                historia_texto = await self.ai_manager.generate_text(prompt, max_tokens=1024, temperature=0.8)
                if historia_texto and len(historia_texto.strip()) > 50:
                    return historia_texto.strip()
                else:
                    logger.warning("História gerada pela IA muito curta, usando fallback")
                    return self._gerar_historia_fallback(demograficos, dores)
            else:
                logger.warning("AI Manager não disponível para história, usando fallback")
                return self._gerar_historia_fallback(demograficos, dores)
        except Exception as e:
            logger.error(f"❌ Erro na geração de história: {e}")
            return self._gerar_historia_fallback(demograficos, dores)
    
    def _gerar_historia_fallback(self, demograficos: DadosDemograficos, dores: DoresEObjetivos) -> str:
        """Gera história pessoal fallback"""
        return f"""
        {demograficos.nome_completo} cresceu em {demograficos.localizacao.split(',')[1].strip()}, em uma família de classe média que sempre valorizou a educação. 
        Formou-se em {demograficos.escolaridade} e começou a trabalhar como {demograficos.profissao} há alguns anos. Apesar do sucesso aparente, sente que está em um platô profissional.
        {dores.dor_primaria_emocional.lower()} tem sido sua maior luta recentemente. Vê colegas avançando enquanto se sente estagnado.
        Seu maior objetivo é {dores.objetivo_principal.lower()}, mas enfrenta desafios de tempo e direcionamento. É uma pessoa determinada que busca constantemente formas de evoluir.
        Atualmente mora em {demograficos.localizacao} e dedica seu tempo livre a estudar formas de acelerar seu crescimento profissional.
        """

    async def _gerar_dia_na_vida(self, demograficos: DadosDemograficos,
                                psicologico: PerfilPsicologico, digital: ContextoDigital) -> str:
        """Gera descrição de um dia típico"""
        return f"""
        **6:30** - Acorda e verifica WhatsApp e Instagram por 15 minutos
        **7:00** - Café da manhã enquanto assiste YouTube ou lê notícias
        **8:00** - Trabalho como {demograficos.profissao}
        **12:00** - Almoço e pausa para redes sociais ({digital.tempo_online_diario//3} minutos)
        **14:00** - Retorna ao trabalho
        **18:00** - Fim do expediente, verifica mensagens
        **19:00** - Jantar e tempo com família/relacionamento
        **20:30** - Tempo pessoal: estuda, assiste conteúdo educacional ou relaxa
        **22:00** - Última checada nas redes sociais antes de dormir
        **23:00** - Dorme pensando em como melhorar sua situação profissional
        **Fins de semana**: Dedica tempo para planejamento pessoal, cursos online e networking.
        """

    async def _gerar_jornada_cliente(self, demograficos: DadosDemograficos,
                                   comportamento: ComportamentoConsumo, contexto_nicho: str) -> Dict[str, str]:
        """Gera jornada do cliente específica"""
        return {
            'consciencia': f"Percebe que precisa de ajuda através de {comportamento.canais_preferidos[0]}",
            'interesse': f"Busca informações e consome conteúdo educacional sobre o tema",
            'consideracao': f"Compara opções, lê depoimentos e busca recomendações",
            'decisao': f"Decide baseado em {', '.join(comportamento.fatores_influencia[:2])}",
            'acao': f"Compra através do canal preferido: {comportamento.canais_preferidos[0]}",
            'retencao': f"Mantém engajamento através de resultados e comunidade"
        }

    def _identificar_drivers_efetivos(self, psicologico: PerfilPsicologico,
                                    dores: DoresEObjetivos) -> List[str]:
        """Identifica drivers mentais mais efetivos para este avatar"""
        drivers_efetivos = []
        # Baseado nos medos
        if 'fracasso' in ' '.join(psicologico.medos_primarios).lower():
            drivers_efetivos.append('Diagnóstico Brutal')
        if 'rejeição' in ' '.join(psicologico.medos_primarios).lower():
            drivers_efetivos.append('Prova Social')
        # Baseado nos desejos
        if 'reconhecimento' in ' '.join(psicologico.desejos_ocultos).lower():
            drivers_efetivos.append('Troféu Secreto')
        if 'liberdade' in ' '.join(psicologico.desejos_ocultos).lower():
            drivers_efetivos.append('Identidade Aprisionada')
        # Drivers universais efetivos
        drivers_efetivos.extend(['Relógio Psicológico', 'Ambição Expandida', 'Método vs Sorte'])
        return list(set(drivers_efetivos))  # Remove duplicatas

    async def _gerar_estrategia_abordagem(self, demograficos: DadosDemograficos,
                                        psicologico: PerfilPsicologico, drivers: List[str]) -> Dict[str, str]:
        """Gera estratégia de abordagem personalizada"""
        return {
            'tom_comunicacao': psicologico.estilo_comunicacao,
            'canais_prioritarios': 'Instagram e WhatsApp' if demograficos.idade < 35 else 'Facebook e Email',
            'horarios_otimos': '19:00-22:00 (maior engajamento)',
            'tipos_conteudo': 'Casos práticos, dados concretos, depoimentos',
            'drivers_principais': ', '.join(drivers[:3]),
            'abordagem_inicial': f"Foco na dor: {psicologico.medos_primarios[0]}",
            'desenvolvimento': f"Mostrar caminho para: {psicologico.desejos_ocultos[0]}",
            'fechamento': 'Urgência + Garantia + Prova Social'
        }

    async def _gerar_scripts_personalizados(self, demograficos: DadosDemograficos,
                                          psicologico: PerfilPsicologico, estrategia: Dict[str, str]) -> Dict[str, str]:
        """Gera scripts personalizados para este avatar"""
        return {
            'abertura_email': f"Olá {demograficos.nome_completo.split()[0]}, você como {demograficos.profissao} já passou por...",
            'hook_instagram': f"Se você é {demograficos.profissao} e sente que...",
            'cta_principal': f"Clique aqui para descobrir como outros {demograficos.profissao}s estão...",
            'objecao_preco': f"Entendo sua preocupação com investimento. Como {demograficos.profissao}, você sabe que...",
            'urgencia': f"Apenas {demograficos.profissao}s como você têm acesso até...",
            'fechamento': f"Sua decisão hoje define se você continuará como {demograficos.profissao} comum ou..."
        }

    def _calcular_metricas_conversao(self, psicologico: PerfilPsicologico,
                                   comportamento: ComportamentoConsumo) -> Dict[str, float]:
        """Calcula métricas de conversão esperadas"""
        # Base de conversão baseada na personalidade
        if psicologico.personalidade_mbti[3] == 'J':  # Julgamento - mais decisivo
            base_conversao = 0.15
        else:  # Percepção - mais cauteloso
            base_conversao = 0.08
        # Ajustes baseados no comportamento
        if comportamento.sensibilidade_preco == 'Baixa - foca no valor':
            base_conversao *= 1.3
        elif comportamento.sensibilidade_preco == 'Alta - muito sensível ao preço':
            base_conversao *= 0.7
        return {
            'taxa_abertura_email': 0.25,
            'taxa_clique': 0.12,
            'taxa_conversao_lead': base_conversao,
            'taxa_conversao_venda': base_conversao * 0.3,
            'lifetime_value': comportamento.ticket_medio * 3,
            'tempo_decisao_dias': 7 if psicologico.personalidade_mbti[3] == 'J' else 14
        }



    def salvar_avatares(self, session_id: str, avatares: List[AvatarCompleto]) -> str:
        """
        Salva os 4 avatares gerados
        """
        try:
            # Usar o diretório correto do projeto V60v3
            session_dir = f"/workspace/project/V60v3/analyses_data/{session_id}"
            avatares_dir = os.path.join(session_dir, 'avatares')
            os.makedirs(avatares_dir, exist_ok=True)
            # Salvar cada avatar individualmente
            for avatar in avatares:
                avatar_path = os.path.join(avatares_dir, f'{avatar.id_avatar}.json')
                with open(avatar_path, 'w', encoding='utf-8') as f:
                    json.dump(asdict(avatar), f, ensure_ascii=False, indent=2, default=str)
            # Salvar resumo comparativo
            resumo_path = os.path.join(avatares_dir, 'resumo_avatares.json')
            resumo = {
                'total_avatares': len(avatares),
                'resumo_demografico': {
                    'idades': [a.dados_demograficos.idade for a in avatares],
                    'rendas': [a.dados_demograficos.renda_mensal for a in avatares],
                    'profissoes': [a.dados_demograficos.profissao for a in avatares],
                    'localizacoes': [a.dados_demograficos.localizacao for a in avatares]
                },
                'drivers_mais_efetivos': self._identificar_drivers_comuns(avatares),
                'metricas_medias': self._calcular_metricas_medias(avatares)
            }
            with open(resumo_path, 'w', encoding='utf-8') as f:
                json.dump(resumo, f, ensure_ascii=False, indent=2, default=str)
            # Salvar manual dos avatares
            manual_path = os.path.join(avatares_dir, 'manual_avatares.md')
            with open(manual_path, 'w', encoding='utf-8') as f:
                f.write(self._gerar_manual_avatares(avatares))
            logger.info(f"✅ 4 avatares salvos: {avatares_dir}")
            return avatares_dir
        except Exception as e:
            logger.error(f"❌ Erro ao salvar avatares: {e}")
            return ""

    def _identificar_drivers_comuns(self, avatares: List[AvatarCompleto]) -> List[str]:
        """Identifica drivers mentais comuns entre os avatares"""
        todos_drivers = []
        for avatar in avatares:
            todos_drivers.extend(avatar.drivers_mentais_efetivos)
        # Contar frequência
        driver_count = {}
        for driver in todos_drivers:
            driver_count[driver] = driver_count.get(driver, 0) + 1
        # Retornar os mais comuns
        return sorted(driver_count.items(), key=lambda x: x[1], reverse=True)

    def _calcular_metricas_medias(self, avatares: List[AvatarCompleto]) -> Dict[str, float]:
        """Calcula métricas médias dos avatares"""
        metricas_keys = avatares[0].metricas_conversao.keys()
        metricas_medias = {}
        for key in metricas_keys:
            valores = [avatar.metricas_conversao[key] for avatar in avatares]
            metricas_medias[key] = sum(valores) / len(valores)
        return metricas_medias

    def _gerar_manual_avatares(self, avatares: List[AvatarCompleto]) -> str:
        """Gera manual completo dos avatares"""
        manual = f"""# Manual dos 4 Avatares Únicos
## Visão Geral
Sistema completo com 4 avatares únicos e realistas, cada um representando um segmento específico do público-alvo.
---
"""
        for i, avatar in enumerate(avatares, 1):
            manual += f"""
## Avatar {i}: {avatar.dados_demograficos.nome_completo}
### 📊 Dados Demográficos
- **Idade**: {avatar.dados_demograficos.idade} anos
- **Profissão**: {avatar.dados_demograficos.profissao}
- **Renda**: R$ {avatar.dados_demograficos.renda_mensal:,.2f}/mês
- **Localização**: {avatar.dados_demograficos.localizacao}
- **Estado Civil**: {avatar.dados_demograficos.estado_civil}
- **Filhos**: {avatar.dados_demograficos.filhos}
### 🧠 Perfil Psicológico
- **Personalidade**: {avatar.perfil_psicologico.personalidade_mbti}
- **Valores**: {', '.join(avatar.perfil_psicologico.valores_principais)}
- **Medos**: {', '.join(avatar.perfil_psicologico.medos_primarios)}
- **Desejos Ocultos**: {', '.join(avatar.perfil_psicologico.desejos_ocultos)}
### 💔 Dores e Objetivos
- **Dor Principal**: {avatar.dores_objetivos.dor_primaria_emocional}
- **Objetivo Principal**: {avatar.dores_objetivos.objetivo_principal}
- **Sonho Secreto**: {avatar.dores_objetivos.sonho_secreto}
- **Maior Medo**: {avatar.dores_objetivos.maior_medo}
### 📱 Contexto Digital
- **Plataformas**: {', '.join(avatar.contexto_digital.plataformas_ativas)}
- **Tempo Online**: {avatar.contexto_digital.tempo_online_diario}h/dia
- **Horários Pico**: {', '.join(avatar.contexto_digital.horarios_pico_atividade)}
### 🛒 Comportamento de Consumo
- **Processo de Decisão**: {' → '.join(avatar.comportamento_consumo.processo_decisao)}
- **Fatores de Influência**: {', '.join(avatar.comportamento_consumo.fatores_influencia)}
- **Objeções Comuns**: {', '.join(avatar.comportamento_consumo.objecoes_comuns)}
- **Ticket Médio**: R$ {avatar.comportamento_consumo.ticket_medio:.2f}
### 🎯 Drivers Mentais Efetivos
{chr(10).join([f"- {driver}" for driver in avatar.drivers_mentais_efetivos])}
### 📈 Estratégia de Abordagem
- **Tom**: {avatar.estrategia_abordagem['tom_comunicacao']}
- **Canais**: {avatar.estrategia_abordagem['canais_prioritarios']}
- **Horários**: {avatar.estrategia_abordagem['horarios_otimos']}
- **Abordagem**: {avatar.estrategia_abordagem['abordagem_inicial']}
### 💬 Scripts Personalizados
- **Abertura Email**: {avatar.scripts_personalizados['abertura_email']}
- **Hook Instagram**: {avatar.scripts_personalizados['hook_instagram']}
- **CTA Principal**: {avatar.scripts_personalizados['cta_principal']}
### 📊 Métricas Esperadas
- **Taxa de Conversão**: {avatar.metricas_conversao['taxa_conversao_venda']*100:.1f}%
- **Lifetime Value**: R$ {avatar.metricas_conversao['lifetime_value']:.2f}
- **Tempo de Decisão**: {avatar.metricas_conversao['tempo_decisao_dias']} dias
### 📖 História Pessoal
{avatar.historia_pessoal}
### 🕐 Um Dia na Vida
{avatar.dia_na_vida}
---
"""
        manual += f"""
## Resumo Estratégico
### Drivers Mentais Mais Efetivos (Todos os Avatares)
{chr(10).join([f"- **{driver}**: {count} avatares" for driver, count in self._identificar_drivers_comuns(avatares)[:5]])}
### Canais Prioritários
- **Jovens (25-35)**: Instagram, TikTok, WhatsApp
- **Adultos (35-45)**: Facebook, LinkedIn, Email
- **Experientes (45+)**: Facebook, Email, WhatsApp
### Horários Ótimos
- **Manhã**: 07:00-09:00 (check matinal)
- **Almoço**: 12:00-13:00 (pausa trabalho)
- **Noite**: 19:00-22:00 (tempo pessoal)
### Abordagens por Perfil
1. **Iniciante Ambicioso**: Foco em crescimento rápido e oportunidades
2. **Profissional Estabelecido**: Otimização e próximo nível
3. **Empreendedor Frustrado**: Método comprovado e garantias
4. **Expert em Evolução**: Estratégias avançadas e exclusividade
*Sistema de 4 Avatares Únicos - Análises Personalizadas Completas*
"""
        return manual

# Instância global
avatar_system = AvatarGenerationSystem()

def get_avatar_system() -> AvatarGenerationSystem:
    """Retorna instância do sistema de avatares"""
    return avatar_system

# --- EXEMPLO DE USO ---
if __name__ == "__main__":
    import asyncio
    import logging

    # Configuração básica de logging
    logging.basicConfig(level=logging.INFO)

    async def main():
        sistema = get_avatar_system()
        
        contexto_nicho_exemplo = """
        Nicho: Marketing Digital para Profissionais Liberais (Advogados, Médicos, Psicólogos)
        Objetivo: Ajudar esses profissionais a atrair clientes qualificados online, aumentando sua visibilidade e faturamento.
        Produto: Um curso completo de marketing digital prático e específico para o nicho.
        """
        
        dados_pesquisa_exemplo = {
            "segmento": "Saúde e Jurídico",
            "publico_principal": "Profissionais liberais com 5-15 anos de experiência",
            "dor_principal": "Dificuldade em conseguir novos clientes consistentemente"
        }

        print("Gerando 4 avatares únicos...")
        avatares_gerados = await sistema.gerar_4_avatares_completos(contexto_nicho_exemplo, dados_pesquisa_exemplo)
        
        print("\n--- AVATARES GERADOS ---")
        for avatar in avatares_gerados:
            print(f"\n--- {avatar.id_avatar.upper()}: {avatar.dados_demograficos.nome_completo} ---")
            print(f"  Profissão: {avatar.dados_demograficos.profissao}")
            print(f"  Idade: {avatar.dados_demograficos.idade}")
            print(f"  Localização: {avatar.dados_demograficos.localizacao}")
            print(f"  Renda Mensal: R$ {avatar.dados_demograficos.renda_mensal:,.2f}")
            print(f"  Personalidade MBTI: {avatar.perfil_psicologico.personalidade_mbti}")
            print(f"  Dor Primária: {avatar.dores_objetivos.dor_primaria_emocional}")
            print(f"  Objetivo Principal: {avatar.dores_objetivos.objetivo_principal}")
            print(f"  Desejo Oculto: {avatar.perfil_psicologico.desejos_ocultos[0]}")
            print(f"  Medo Primário: {avatar.perfil_psicologico.medos_primarios[0]}")
            print(f"  Estilo de Comunicação: {avatar.perfil_psicologico.estilo_comunicacao}")
            print(f"  Drivers Mentais: {', '.join(avatar.drivers_mentais_efetivos)}")
            print("\n  HISTÓRIA PESSOAL RESUMIDA:")
            # Imprime as primeiras 2 linhas da história
            linhas_historia = avatar.historia_pessoal.strip().split('\n')
            for linha in linhas_historia[:2]:
                print(f"    {linha}")
            if len(linhas_historia) > 2:
                print("    ...")

        # Salvar avatares (opcional, requer permissão de escrita no diretório)
        # session_id_teste = "teste_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        # caminho_salvo = sistema.salvar_avatares(session_id_teste, avatares_gerados)
        # if caminho_salvo:
        #     print(f"\n✅ Avatares salvos em: {caminho_salvo}")

    asyncio.run(main())

# Instância global
avatar_generation_system = AvatarGenerationSystem()

