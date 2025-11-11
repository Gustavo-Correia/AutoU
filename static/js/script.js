document.addEventListener('DOMContentLoaded', function() {
    const emailForm = document.getElementById('emailForm');
    const fileUpload = document.getElementById('fileUpload');
    const fileInfo = document.getElementById('fileInfo');
    const emailText = document.getElementById('emailText');
    const submitBtn = document.getElementById('submitBtn');
    const resultsSection = document.getElementById('resultsSection');
    const errorSection = document.getElementById('errorSection');
    const classificationResult = document.getElementById('classificationResult');
    const categoryBadge = document.getElementById('categoryBadge');
    const confidenceText = document.getElementById('confidenceText');
    const responseContent = document.getElementById('responseContent');
    const previewContent = document.getElementById('previewContent');
    const copyBtn = document.getElementById('copyBtn');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    const errorMessage = document.getElementById('errorMessage');
    const retryBtn = document.getElementById('retryBtn');

    // Gerenciar upload de arquivo
    fileUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileInfo.textContent = `Arquivo selecionado: ${file.name}`;
            // Limpar textarea quando arquivo é selecionado
            emailText.value = '';
        } else {
            fileInfo.textContent = 'Nenhum arquivo selecionado';
        }
    });

    // Limpar seleção de arquivo quando textarea é usada
    emailText.addEventListener('input', function() {
        if (emailText.value.trim() !== '') {
            fileUpload.value = '';
            fileInfo.textContent = 'Nenhum arquivo selecionado';
        }
    });

    // Submissão do formulário
    emailForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const file = fileUpload.files[0];
        const text = emailText.value.trim();

        // Validação
        if (!file && !text) {
            showError('Por favor, selecione um arquivo ou digite o texto do email.');
            return;
        }

        if (file) {
            formData.append('file', file);
        }
        if (text) {
            formData.append('text', text);
        }

        await processEmail(formData);
    });

    async function processEmail(formData) {
        try {
            setLoading(true);
            hideResults();
            hideError();

            console.log('Enviando requisição para /classify...');
            
            const response = await fetch('/classify', {
                method: 'POST',
                body: formData
            });

            console.log('Status da resposta:', response.status);
            
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status} - ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Dados recebidos:', data);

            if (data.success) {
                displayResults(data);
            } else {
                showError(data.error || 'Erro desconhecido no processamento.');
            }
        } catch (error) {
            console.error('Erro detalhado:', error);
            showError(`Erro de conexão: ${error.message}. Verifique o console para mais detalhes.`);
        } finally {
            setLoading(false);
        }
    }

    
    async function testConnection() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            console.log('Teste de conexão:', data);
        } catch (error) {
            console.error('Teste de conexão falhou:', error);
        }
    }

    
    document.addEventListener('DOMContentLoaded', function() {
        testConnection();
    });

    function displayResults(data) {
        // Atualizar classificação
        const isProductive = data.classification.category === 'Produtivo';
        categoryBadge.textContent = data.classification.category;
        categoryBadge.className = `category-badge ${isProductive ? 'productive' : 'unproductive'}`;
        
        confidenceText.textContent = `Confiança: ${(data.classification.confidence * 100).toFixed(1)}%`;

        // Atualizar resposta
        responseContent.textContent = data.response;

        // Atualizar preview
        previewContent.textContent = data.content_preview;

        // Mostrar seção de resultados
        showResults();
    }

    function showResults() {
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    function hideResults() {
        resultsSection.style.display = 'none';
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
        errorSection.scrollIntoView({ behavior: 'smooth' });
    }

    function hideError() {
        errorSection.style.display = 'none';
    }

    function setLoading(loading) {
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoading = submitBtn.querySelector('.btn-loading');
        
        if (loading) {
            btnText.style.display = 'none';
            btnLoading.style.display = 'flex';
            submitBtn.disabled = true;
        } else {
            btnText.style.display = 'block';
            btnLoading.style.display = 'none';
            submitBtn.disabled = false;
        }
    }

    // Copiar resposta para clipboard
    copyBtn.addEventListener('click', function() {
        const responseText = responseContent.textContent;
        navigator.clipboard.writeText(responseText).then(function() {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copiado!';
            copyBtn.style.background = '#48bb78';
            
            setTimeout(function() {
                copyBtn.textContent = originalText;
                copyBtn.style.background = '';
            }, 2000);
        }).catch(function() {
            alert('Erro ao copiar texto.');
        });
    });

    // Nova análise
    newAnalysisBtn.addEventListener('click', function() {
        emailForm.reset();
        fileInfo.textContent = 'Nenhum arquivo selecionado';
        hideResults();
        hideError();
        
        // Scroll para o topo
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Retry button
    retryBtn.addEventListener('click', function() {
        hideError();
    });
});