import os
import google.generativeai as genai
from typing import Dict

class ClassificadorIA:
    def __init__(self):
        self.chave_api_gemini = os.getenv('GEMINI_API_KEY')
        
        # Configurar o Gemini
        genai.configure(api_key=self.chave_api_gemini)
        
        # Listar modelos disponíveis e escolher um adequado
        try:
            modelos = genai.list_models()
            modelos_disponiveis = [modelo.name for modelo in modelos]
            print(f"Modelos disponíveis: {modelos_disponiveis}")
            
            # Procurar por modelos que suportam generateContent
            modelos_suportados = []
            for nome_modelo in modelos_disponiveis:
                info_modelo = genai.get_model(nome_modelo)
                # Verificar se o modelo suporta generateContent
                if hasattr(info_modelo, 'supported_generation_methods') and 'generateContent' in info_modelo.supported_generation_methods:
                    modelos_suportados.append(nome_modelo)
            
            print(f"Modelos suportados para generateContent: {modelos_suportados}")
            
            # Priorizar modelos específicos
            modelos_preferidos = [
                'models/gemini-2.0-flash',
                'models/gemini-2.0-flash-001', 
                'models/gemini-flash-latest',
                'models/gemini-pro-latest',
                'models/gemini-2.5-flash',
                'models/gemini-2.5-flash-lite'
            ]
            
            modelo_selecionado = None
            for preferido in modelos_preferidos:
                if preferido in modelos_suportados:
                    modelo_selecionado = preferido
                    break
            
            # Se não encontrou um preferido, usar o primeiro suportado
            if not modelo_selecionado and modelos_suportados:
                modelo_selecionado = modelos_suportados[0]
            
            if modelo_selecionado:
                self.modelo = genai.GenerativeModel(modelo_selecionado)
                print(f"Modelo selecionado: {modelo_selecionado}")
            else:
                raise Exception("Nenhum modelo compatível com generateContent encontrado")
                    
        except Exception as e:
            print(f"Erro ao configurar modelo: {e}")
            # Fallback para modelos mais recentes
            try:
                self.modelo = genai.GenerativeModel('gemini-2.0-flash')
                print("Usando fallback: gemini-2.0-flash")
            except:
                try:
                    self.modelo = genai.GenerativeModel('gemini-flash-latest')
                    print("Usando fallback: gemini-flash-latest")
                except:
                    raise Exception("Não foi possível inicializar nenhum modelo Gemini")

    def classificar_email(self, texto_email: str) -> Dict:
        """Classifica email usando Google Gemini com análise contextual"""
        
        prompt = f"""
        Analise o seguinte email e classifique-o como "Produtivo" ou "Improdutivo" baseando-se no contexto e intenção.
        Além disso, atribua uma porcentagem específica de 0% a 100% que represente o nível de produtividade do email.

        EMAIL: "{texto_email}"

        CRITÉRIOS PARA CLASSIFICAÇÃO:
        - "Produtivo": Requer ação, resposta específica, solicitação de suporte, problema técnico, dúvida operacional, atualização de status, questões comerciais
        - "Improdutivo": Saudações, agradecimentos, mensagens sociais, felicitações, contatos informais, spam, mensagens que não exigem ação

        ESCALA DE PORCENTAGEM:
        - 0-20%: Claramente improdutivo (saudações simples, spam)
        - 21-40%: Majoritariamente improdutivo (agradecimentos, felicitações)
        - 41-60%: Neutro/misto (pode conter elementos dos dois)
        - 61-80%: Majoritariamente produtivo (dúvidas simples, solicitações)
        - 81-100%: Claramente produtivo (problemas urgentes, solicitações específicas)

        Responda APENAS no formato JSON:
        {{
            "categoria": "Produtivo" ou "Improdutivo",
            "pontuacao_produtividade": número entre 0 e 100,
            "razao": "breve explicação da classificação e pontuação"
        }}
        """
        
        try:
            resposta = self.modelo.generate_content(prompt)
            texto_resposta = resposta.text.strip()
            print(f"Resposta bruta do Gemini: {texto_resposta}")  # Debug
            
            # Tentar parsear como JSON
            if texto_resposta.startswith('{') and texto_resposta.endswith('}'):
                import json
                resultado = json.loads(texto_resposta)
                
                # Garantir que a categoria e pontuação estejam corretas
                pontuacao_produtividade = resultado.get("pontuacao_produtividade", 50)
                
                # Se a pontuação for string, converter para número
                if isinstance(pontuacao_produtividade, str):
                    pontuacao_produtividade = float(pontuacao_produtividade.replace('%', ''))
                
                # Determinar categoria baseada na pontuação
                if pontuacao_produtividade >= 50:
                    resultado["categoria"] = "Produtivo"
                else:
                    resultado["categoria"] = "Improdutivo"
                
                # Garantir que a pontuação está entre 0-100
                resultado["pontuacao_produtividade"] = max(0, min(100, pontuacao_produtividade))
                resultado["confianca"] = resultado["pontuacao_produtividade"] / 100
                
                return resultado
            else:
                # Fallback: análise direta do texto
                return self._classificacao_fallback(texto_resposta, texto_email)
                
        except Exception as e:
            print(f"Erro na classificação com Gemini: {e}")
            return self._classificacao_emergencia(texto_email)

    def _classificacao_fallback(self, texto_resposta: str, email_original: str) -> Dict:
        """Fallback quando a resposta não é JSON válido"""
        texto_resposta_minusculo = texto_resposta.lower()
        email_original_minusculo = email_original.lower()
        
        # Tentar extrair números da resposta
        import re
        numeros = re.findall(r'\d+', texto_resposta)
        pontuacao_produtividade = 50  # padrão
        
        if numeros:
            pontuacao_produtividade = min(100, max(0, int(numeros[0])))
        
        if "produtivo" in texto_resposta_minusculo or pontuacao_produtividade >= 50:
            categoria = "Produtivo"
            # Ajustar score baseado no contexto
            if pontuacao_produtividade == 50:
                pontuacao_produtividade = 75
        else:
            categoria = "Improdutivo"
            if pontuacao_produtividade == 50:
                pontuacao_produtividade = 25
        
        return {
            "categoria": categoria,
            "pontuacao_produtividade": pontuacao_produtividade,
            "confianca": pontuacao_produtividade / 100,
            "razao": "Classificação por fallback - análise textual"
        }

    def _classificacao_emergencia(self, texto_email: str) -> Dict:
        """Classificação de emergência total"""
        texto_email_minusculo = texto_email.lower()
        
        # Indicadores de email produtivo
        indicadores_produtivos = [
            'problema', 'erro', 'bug', 'não funciona', 'como faço', 'suporte técnico',
            'urgente', 'importante', 'solicitação', 'requisição', 'ajuda', 'suporte',
            'contrato', 'pagamento', 'fatura', 'serviço', 'manutenção', 'atualização',
            'status', 'dúvida', 'questão', 'reclamação', 'assistência'
        ]
        
        # Indicadores de email improdutivo  
        indicadores_improdutivos = [
            'obrigado', 'obrigada', 'parabéns', 'feliz natal', 'boas festas', 
            'cumprimentos', 'saudações', 'ola', 'oi', 'espero', 'família', 
            'amigo', 'contato', 'agradecimento', 'felicidades'
        ]
        
        contador_produtivo = sum(1 for palavra in indicadores_produtivos if palavra in texto_email_minusculo)
        contador_improdutivo = sum(1 for palavra in indicadores_improdutivos if palavra in texto_email_minusculo)
        
        total_indicadores = contador_produtivo + contador_improdutivo
        
        if total_indicadores > 0:
            pontuacao_produtividade = (contador_produtivo / total_indicadores) * 100
        else:
            # Se não encontrou indicadores, análise por tamanho e estrutura
            if len(texto_email) > 100 and any(caractere in texto_email for caractere in ['?', '!']):
                pontuacao_produtividade = 70  # Provavelmente produtivo
            else:
                pontuacao_produtividade = 30  # Provavelmente improdutivo
        
        categoria = "Produtivo" if pontuacao_produtividade >= 50 else "Improdutivo"
        
        return {
            "categoria": categoria,
            "pontuacao_produtividade": pontuacao_produtividade,
            "confianca": pontuacao_produtividade / 100,
            "razao": "Classificação de emergência por análise de palavras-chave"
        }

    def gerar_resposta(self, texto_email: str, classificacao: Dict) -> str:
        """Gera resposta automática contextual usando Gemini"""
        
        categoria = classificacao["categoria"]
        pontuacao_produtividade = classificacao.get("pontuacao_produtividade", 50)
        
        if categoria == "Produtivo":
            prompt = f"""
            Com base neste email CLASSIFICADO COMO PRODUTIVO (pontuação: {pontuacao_produtividade}%), gere uma resposta profissional em português:

            EMAIL: "{texto_email}"

            INSTRUÇÕES:
            - Agradeça pelo contato
            - Confirme o recebimento e processamento
            - Ofereça prazo realista (24-48h)
            - Mantenha tom empático mas profissional
            - Seja conciso (3-4 frases)
            - Finalize com saudação profissional

            RESPOSTA:
            """
        else:
            prompt = f"""
            Com base neste email CLASSIFICADO COMO IMPRODUTIVO (pontuação: {pontuacao_produtividade}%), gere uma resposta cordial em português:

            EMAIL: "{texto_email}"

            INSTRUÇÕES:
            - Agradeça pela mensagem
            - Seja breve e educado
            - Mantenha tom leve e amigável
            - Não ofereça suporte técnico
            - 1-2 frases no máximo
            - Finalize com saudação amigável

            RESPOSTA:
            """
        
        try:
            resposta = self.modelo.generate_content(prompt)
            return resposta.text.strip()
                
        except Exception as e:
            print(f"Erro na geração de resposta: {e}")
            return self._obter_resposta_fallback_com_ia(texto_email, categoria)

    def _obter_resposta_fallback_com_ia(self, texto_email: str, categoria: str) -> str:
        """Gera resposta fallback usando IA com prompt mais simples"""
        try:
            # Usar o mesmo modelo principal para fallback
            if categoria == "Produtivo":
                prompt_simples = f"Gere resposta profissional breve em português para este email de suporte: {texto_email[:200]}"
            else:
                prompt_simples = f"Gere resposta educada breve em português para este email social: {texto_email[:200]}"
            
            resposta = self.modelo.generate_content(prompt_simples)
            return resposta.text.strip()
            
        except Exception as e:
            print(f"Erro até no fallback com IA: {e}")
            # Último recurso - respostas genéricas muito básicas
            return self._obter_resposta_emergencia(categoria)

    def _obter_resposta_emergencia(self, categoria: str) -> str:
        """Resposta de emergência absoluta (sem IA)"""
        if categoria == "Produtivo":
            return "Agradecemos seu contato. Sua solicitação foi recebida e será processada. Att, Equipe"
        else:
            return "Agradecemos sua mensagem! Desejamos um ótimo dia. Att, Equipe"

# Instância global
classificador = ClassificadorIA()

def classificar_email(texto_email: str) -> Dict:
    return classificador.classificar_email(texto_email)

def gerar_resposta(texto_email: str, classificacao: Dict) -> str:
    return classificador.gerar_resposta(texto_email, classificacao)