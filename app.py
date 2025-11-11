from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from utils.processador_email import processar_conteudo_email
from utils.classificador_ia import classificar_email, gerar_resposta

app = Flask(__name__)
app.config['PASTA_UPLOAD'] = 'uploads'
app.config['TAMANHO_MAXIMO_CONTEUDO'] = 16 * 1024 * 1024  # 16MB tamanho máximo do arquivo

# Criar diretório de uploads se não existir
os.makedirs(app.config['PASTA_UPLOAD'], exist_ok=True)

EXTENSOES_PERMITIDAS = {'txt', 'pdf'}

def arquivo_permitido(nome_arquivo):
    return '.' in nome_arquivo and \
           nome_arquivo.rsplit('.', 1)[1].lower() in EXTENSOES_PERMITIDAS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classificar', methods=['POST'])
def classificar():
    try:
        conteudo_email = ""
        
        # Verificar se é upload de arquivo
        if 'arquivo' in request.files:
            arquivo = request.files['arquivo']
            if arquivo and arquivo.filename != '' and arquivo_permitido(arquivo.filename):
                nome_arquivo = secure_filename(arquivo.filename)
                caminho_arquivo = os.path.join(app.config['PASTA_UPLOAD'], nome_arquivo)
                arquivo.save(caminho_arquivo)
                
                # Processar arquivo
                conteudo_email = processar_conteudo_email(caminho_arquivo)
                
                # Remover arquivo após processamento
                os.remove(caminho_arquivo)
            else:
                return jsonify({'erro': 'Arquivo inválido. Use .txt ou .pdf'}), 400
        
        # Verificar se é texto direto
        elif 'texto' in request.form and request.form['texto'].strip():
            conteudo_email = request.form['texto'].strip()
        
        else:
            return jsonify({'erro': 'Nenhum conteúdo de email fornecido'}), 400
        
        if not conteudo_email:
            return jsonify({'erro': 'Não foi possível extrair conteúdo do email'}), 400
        
        # Classificar email
        resultado_classificacao = classificar_email(conteudo_email)
        
        # Gerar resposta automática
        sugestao_resposta = gerar_resposta(conteudo_email, resultado_classificacao)
        
        return jsonify({
            'sucesso': True,
            'classificacao': resultado_classificacao,
            'resposta': sugestao_resposta,
            'preview_conteudo': conteudo_email[:200] + '...' if len(conteudo_email) > 200 else conteudo_email
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro no processamento: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)