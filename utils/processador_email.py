import PyPDF2
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

# Download recursos do NLTK (será feito apenas uma vez)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def processar_conteudo_email(caminho_arquivo):
    """Extrai e processa conteúdo de arquivos de email"""
    
    # Verificar extensão do arquivo
    if caminho_arquivo.lower().endswith('.txt'):
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.read()
    
    elif caminho_arquivo.lower().endswith('.pdf'):
        conteudo = extrair_texto_pdf(caminho_arquivo)
    
    else:
        raise ValueError("Formato de arquivo não suportado")
    
    return preprocessar_texto(conteudo)

def extrair_texto_pdf(caminho_arquivo):
    """Extrai texto de arquivos PDF"""
    texto = ""
    try:
        with open(caminho_arquivo, 'rb') as arquivo:
            leitor = PyPDF2.PdfReader(arquivo)
            for pagina in leitor.pages:
                texto += pagina.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Erro ao extrair texto do PDF: {str(e)}")
    
    return texto

def preprocessar_texto(texto):
    """Pré-processa o texto para análise"""
    # Converter para minúsculas
    texto = texto.lower()
    
    # Remover caracteres especiais e números
    texto = re.sub(r'[^a-zA-Z\s]', '', texto)
    
    # Tokenização
    tokens = word_tokenize(texto)
    
    # Remover stop words
    stop_words = set(stopwords.words('portuguese') + stopwords.words('english'))
    tokens_filtrados = [token for token in tokens if token not in stop_words]
    
    # Stemming
    stemmer = PorterStemmer()
    tokens_stemizados = [stemmer.stem(token) for token in tokens_filtrados]
    
    return ' '.join(tokens_stemizados)