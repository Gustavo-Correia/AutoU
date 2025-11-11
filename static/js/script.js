document.addEventListener('DOMContentLoaded', function() {
  const formularioEmail = document.getElementById('emailForm');
  const uploadArquivo = document.getElementById('fileUpload');
  const infoArquivo = document.getElementById('fileInfo');
  const textoEmail = document.getElementById('emailText');
  const botaoEnviar = document.getElementById('submitBtn');
  const secaoResultados = document.getElementById('resultsSection');
  const secaoErro = document.getElementById('errorSection');
  const emblemaCategoria = document.getElementById('categoryBadge');
  const textoConfianca = document.getElementById('confidenceText');
  const conteudoResposta = document.getElementById('responseContent');
  const conteudoPreview = document.getElementById('previewContent');
  const botaoCopiar = document.getElementById('copyBtn');
  const botaoNovaAnalise = document.getElementById('newAnalysisBtn');
  const mensagemErro = document.getElementById('errorMessage');
  const botaoTentarNovamente = document.getElementById('retryBtn');

  uploadArquivo.addEventListener('change', function(e) {
    const arquivo = e.target.files[0];
    infoArquivo.textContent = arquivo ? `Arquivo selecionado: ${arquivo.name}` : 'Nenhum arquivo selecionado';
    if (arquivo) textoEmail.value = '';
  });

  textoEmail.addEventListener('input', function() {
    if (textoEmail.value.trim() !== '') {
      uploadArquivo.value = '';
      infoArquivo.textContent = 'Nenhum arquivo selecionado';
    }
  });

  formularioEmail.addEventListener('submit', async function(e) {
    e.preventDefault();
    const fd = new FormData();
    const arquivo = uploadArquivo.files[0];
    const texto = textoEmail.value.trim();

    if (!arquivo && !texto) {
      mostrarErro('Por favor, selecione um arquivo ou digite o texto do email.');
      return;
    }

    if (arquivo) fd.append('file', arquivo);
    if (texto) fd.append('text', texto);

    await processarEmail(fd);
  });

  async function processarEmail(fd) {
    try {
      definirCarregamento(true);
      ocultarResultados();
      ocultarErro();

      const resp = await fetch('/classify', { method: 'POST', body: fd });
      const dados = await resp.json();

      if (dados.success) {
        exibirResultados(dados);
      } else {
        mostrarErro(dados.error || 'Erro desconhecido no processamento.');
      }
    } catch (err) {
      console.error(err);
      mostrarErro('Erro de conexão. Verifique sua internet e tente novamente.');
    } finally {
      definirCarregamento(false);
    }
  }

  function exibirResultados(dados) {
    const classificacao = dados.classification;
    const ehProdutivo = classificacao.categoria === 'Produtivo';

    emblemaCategoria.textContent = classificacao.categoria;
    emblemaCategoria.className = `category-badge ${ehProdutivo ? 'productive' : 'unproductive'}`;

    const pont = typeof classificacao.pontuacao_produtividade === 'number'
      ? classificacao.pontuacao_produtividade
      : Number(classificacao.pontuacao_produtividade) || 50;

    textoConfianca.textContent = `Produtividade: ${pont.toFixed(1)}%`;

    conteudoResposta.textContent = dados.response || '';
    conteudoPreview.textContent = dados.content_preview || '';

    mostrarResultados();
  }

  function mostrarResultados() {
    secaoResultados.style.display = 'block';
    secaoResultados.scrollIntoView({ behavior: 'smooth' });
  }

  function ocultarResultados() {
    secaoResultados.style.display = 'none';
  }

  function mostrarErro(msg) {
    mensagemErro.textContent = msg;
    secaoErro.style.display = 'block';
    secaoErro.scrollIntoView({ behavior: 'smooth' });
  }

  function ocultarErro() {
    secaoErro.style.display = 'none';
  }

  function definirCarregamento(carregando) {
    const texto = botaoEnviar.querySelector('.btn-text');
    const loading = botaoEnviar.querySelector('.btn-loading');
    if (carregando) {
      texto.style.display = 'none';
      loading.style.display = 'inline';
      botaoEnviar.disabled = true;
    } else {
      texto.style.display = 'inline';
      loading.style.display = 'none';
      botaoEnviar.disabled = false;
    }
  }

  botaoCopiar.addEventListener('click', function() {
    const txt = conteudoResposta.textContent || '';
    navigator.clipboard.writeText(txt).then(() => {
      const original = botaoCopiar.textContent;
      botaoCopiar.textContent = '✓ Copiado!';
      botaoCopiar.style.background = '#48bb78';
      setTimeout(() => {
        botaoCopiar.textContent = original;
        botaoCopiar.style.background = '';
      }, 1600);
    }).catch(() => alert('Erro ao copiar texto.'));
  });

  botaoNovaAnalise.addEventListener('click', function() {
    formularioEmail.reset();
    infoArquivo.textContent = 'Nenhum arquivo selecionado';
    ocultarResultados();
    ocultarErro();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  botaoTentarNovamente.addEventListener('click', function() {
    ocultarErro();
  });
});
