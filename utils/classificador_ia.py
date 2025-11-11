import os
import re
import json
import google.generativeai as genai
from typing import Dict, Any

class ClassificadorIA:
    def __init__(self):
        self.chave_api_gemini = os.getenv('GEMINI_API_KEY')
        
        genai.configure(api_key=self.chave_api_gemini)

        # Seleção de modelo simplificada e estável
        # Evita introspecção que pode variar entre versões/contas
        preferidos = [
            'models/gemini-2.5-flash',
            'models/gemini-2.0-flash',
            'gemini-2.5-flash',
            'gemini-2.0-flash',
        ]

        self.modelo = None
        for nome in preferidos:
            try:
                self.modelo = genai.GenerativeModel(nome)
                print(f"Modelo selecionado: {nome}")
                break
            except Exception as e:
                print(f"Tentativa falhou para modelo {nome}: {e}")

        if not self.modelo:
            # último recurso
            self.modelo = genai.GenerativeModel('gemini-2.0-flash')
            print("Usando fallback: gemini-2.0-flash")

    def _parse_json_resposta(self, texto: str) -> Dict[str, Any] | None:
        """
        Extrai JSON válido da resposta. Retorna dict ou None.
        Não reatribui categoria; apenas normaliza tipos.
        """
        if not texto:
            return None

        s = texto.strip()
        # Tenta bloco JSON direto
        if s.startswith('{') and s.endswith('}'):
            bloco = s
        else:
            m = re.search(r'\{[\s\S]*\}', s)
            if not m:
                return None
            bloco = m.group(0)

        data = json.loads(bloco)

        # Normaliza pontuação
        score = data.get("pontuacao_produtividade", 50)
        if isinstance(score, str):
            score = float(score.replace('%', '').strip() or 0)
        score = max(0, min(100, float(score)))

        categoria = data.get("categoria")
        if not categoria:
            # só derive se faltar
            categoria = "Produtivo" if score >= 50 else "Improdutivo"

        return {
            "categoria": "Produtivo" if str(categoria).lower() == "produtivo" else "Improdutivo",
            "pontuacao_produtividade": score,
            "confianca": round(score / 100.0, 4),
            "razao": data.get("razao", "Classificação gerada pelo modelo")
        }

    def classificar_email(self, texto_email: str) -> Dict[str, Any]:
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

Responda APENAS no formato JSON, sem markdown ou texto extra:
{{
  "categoria": "Produtivo" ou "Improdutivo",
  "pontuacao_produtividade": número entre 0 e 100,
  "razao": "breve explicação da classificação e pontuação"
}}
"""
        try:
            resposta = self.modelo.generate_content(prompt)
            texto_resposta = (resposta.text or "").strip()
            print(f"Resposta bruta do Gemini: {texto_resposta}")

            parsed = self._parse_json_resposta(texto_resposta)
            if parsed is not None:
                return parsed

            # Sem JSON válido: fallback baseado no email (não no texto da resposta)
            return self._classificacao_fallback(texto_email)

        except Exception as e:
            print(f"Erro na classificação com Gemini: {e}")
            return self._classificacao_emergencia(texto_email)

    def _classificacao_fallback(self, email_original: str) -> Dict[str, Any]:
        """
        Fallback quando a resposta não é JSON válido.
        Baseia-se APENAS no email original.
        """
        t = (email_original or "").lower()

        indicadores_produtivos = [
            'problema', 'erro', 'bug', 'não funciona', 'nao funciona', 'como faço', 'como faco',
            'suporte técnico', 'suporte', 'urgente', 'importante', 'solicitação', 'solicitacao',
            'requisição', 'requisicao', 'ajuda', 'contrato', 'pagamento', 'fatura', 'serviço',
            'servico', 'manutenção', 'manutencao', 'atualização', 'atualizacao', 'status',
            'dúvida', 'duvida', 'questão', 'questao', 'reclamação', 'reclamacao', 'assistência',
            'assistencia'
        ]
        indicadores_improdutivos = [
            'obrigado', 'obrigada', 'parabéns', 'parabens', 'feliz natal', 'boas festas',
            'cumprimentos', 'saudações', 'saudacoes', 'ola', 'oi', 'espero', 'família', 'familia',
            'amigo', 'contato', 'agradecimento', 'felicidades', 'test'
        ]

        prod = sum(1 for p in indicadores_produtivos if p in t)
        imp = sum(1 for p in indicadores_improdutivos if p in t)
        total = prod + imp

        if total > 0:
            score = (prod / total) * 100.0
        else:
            score = 70.0 if (len(t) > 100 and any(c in t for c in ['?', '!'])) else 30.0

        categoria = "Produtivo" if score >= 50 else "Improdutivo"
        return {
            "categoria": categoria,
            "pontuacao_produtividade": round(score, 2),
            "confianca": round(score / 100.0, 4),
            "razao": "Classificação por fallback - análise do conteúdo do email"
        }

    def _classificacao_emergencia(self, texto_email: str) -> Dict[str, Any]:
        # Reuso do fallback simples
        return self._classificacao_fallback(texto_email)

    def gerar_resposta(self, texto_email: str, classificacao: Dict[str, Any]) -> str:
        categoria = classificacao.get("categoria", "Produtivo")
        score = classificacao.get("pontuacao_produtividade", 50)

        if categoria == "Produtivo":
            prompt = f"""
Com base neste email CLASSIFICADO COMO PRODUTIVO (pontuação: {score}%), gere uma resposta profissional em português:

EMAIL: "{texto_email}"

INSTRUÇÕES:
- Agradeça pelo contato
- Confirme o recebimento e processamento
- Ofereça prazo realista (24-48h)
- Mantenha tom empático mas profissional
- Seja conciso (3-4 frases)
- Finalize com saudação profissional

Responda apenas com o texto final, sem preâmbulos.
"""
        else:
            prompt = f"""
Com base neste email CLASSIFICADO COMO IMPRODUTIVO (pontuação: {score}%), gere uma resposta cordial em português:

EMAIL: "{texto_email}"

INSTRUÇÕES:
- Agradeça pela mensagem
- Seja breve e educado
- Mantenha tom leve e amigável
- Não ofereça suporte técnico
- 1-2 frases no máximo
- Finalize com saudação amigável

Responda apenas com o texto final, sem preâmbulos.
"""
        try:
            resp = self.modelo.generate_content(prompt)
            return (resp.text or "").strip()
        except Exception as e:
            print(f"Erro na geração de resposta: {e}")
            return self._obter_resposta_emergencia(categoria)

    def _obter_resposta_emergencia(self, categoria: str) -> str:
        if categoria == "Produtivo":
            return "Agradecemos seu contato. Sua solicitação foi recebida e será processada. Att, Equipe"
        else:
            return "Agradecemos sua mensagem! Desejamos um ótimo dia. Att, Equipe"

# Instância global
classificador = ClassificadorIA()

def classificar_email(texto_email: str) -> Dict[str, Any]:
    return classificador.classificar_email(texto_email)

def gerar_resposta(texto_email: str, classificacao: Dict[str, Any]) -> str:
    return classificador.gerar_resposta(texto_email, classificacao)
