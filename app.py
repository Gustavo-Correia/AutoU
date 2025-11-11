import os
import sys
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

# Garantir import absoluto do diretório utils
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from utils.processador_email import processar_conteudo_email
from utils.classificador_ia import classificar_email, gerar_resposta

app = Flask(__name__)

# Limite de upload padrão do Flask
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB [adequado para txt/pdf]
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'txt', 'pdf'}

def arquivo_permitido(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify():
    try:
        conteudo_email = ""

        # 1) Arquivo (campo 'file')
        if 'file' in request.files:
            arquivo = request.files['file']
            if arquivo and arquivo.filename:
                if not arquivo_permitido(arquivo.filename):
                    return jsonify({'error': 'Arquivo inválido. Use .txt ou .pdf'}), 400
                nome_seguro = secure_filename(arquivo.filename)
                caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_seguro)
                arquivo.save(caminho)
                try:
                    conteudo_email = processar_conteudo_email(caminho)
                finally:
                    try:
                        os.remove(caminho)
                    except Exception:
                        pass

        # 2) Texto direto (campo 'text')
        if not conteudo_email and 'text' in request.form:
            texto = request.form.get('text', '').strip()
            if texto:
                conteudo_email = texto

        if not conteudo_email:
            return jsonify({'error': 'Não foi possível extrair conteúdo do email'}), 400

        # Classificação + resposta
        resultado_classificacao = classificar_email(conteudo_email)
        resposta_auto = gerar_resposta(conteudo_email, resultado_classificacao)

        return jsonify({
            'success': True,
            'classification': resultado_classificacao,
            'response': resposta_auto,
            'content_preview': (conteudo_email[:200] + '...') if len(conteudo_email) > 200 else conteudo_email
        })

    except Exception as e:
        import traceback
        print("Erro no servidor:", e)
        print(traceback.format_exc())
        return jsonify({'error': f'Erro no processamento: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
