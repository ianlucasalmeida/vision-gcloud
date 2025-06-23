// Espera o HTML ser completamente carregado para executar o script
document.addEventListener('DOMContentLoaded', () => {

    // --- Parte 1: Seleção dos Elementos do HTML ---
    const fileInput = document.getElementById('fileInput');
    const fileLabel = document.querySelector('.file-label');
    const fileNameSpan = document.getElementById('fileName');
    const uploadButton = document.getElementById('uploadButton');
    const statusDiv = document.getElementById('status');
    const downloadLink = document.getElementById('downloadLink');

    // ATENÇÃO: Substitua pela URL da sua função 'generate-upload-url'
    const signedUrlGeneratorUrl = "https://generate-upload-url-egxj6adibq-rj.a.run.app";

    let selectedFile = null;

    // --- Parte 2: Lógica de Interação com a Página ---
    fileInput.addEventListener('change', (event) => {
        selectedFile = event.target.files[0];
        if (selectedFile) {
            fileNameSpan.textContent = selectedFile.name;
            uploadButton.disabled = false;
            fileLabel.textContent = "Trocar Arquivo";
        } else {
            fileNameSpan.textContent = "Nenhum arquivo selecionado";
            uploadButton.disabled = true;
            fileLabel.textContent = "Escolher Arquivo";
        }
    });

    // --- Parte 3: Lógica de Upload (A mais importante) ---
    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) {
            alert("Nenhum arquivo selecionado!");
            return;
        }

        // Desabilita o botão para evitar múltiplos cliques
        uploadButton.disabled = true;
        uploadButton.textContent = "Enviando...";

        try {
            // --- ETAPA A: Pedir a URL assinada para nossa função de apoio ---
            statusDiv.innerHTML = `<p>1/3: Solicitando permissão de upload...</p>`;
            
            const response = await fetch(signedUrlGeneratorUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ fileName: selectedFile.name }),
            });

            if (!response.ok) {
                throw new Error('Falha ao obter a URL de upload.');
            }

            const data = await response.json();
            const signedUrl = data.url;

            // --- ETAPA B: Fazer o upload do arquivo para a URL recebida ---
            statusDiv.innerHTML = `<p>2/3: Enviando arquivo para o Cloud Storage...</p>`;
            
            const uploadResponse = await fetch(signedUrl, {
                method: 'PUT',
                body: selectedFile,
                headers: {
                    'Content-Type': 'application/octet-stream'
                }
            });

            if (!uploadResponse.ok) {
                throw new Error('Falha no upload do arquivo.');
            }

            // --- ETAPA C: Sucesso! Exibir o link de download ---
            statusDiv.innerHTML = `<p>3/3: Sucesso! Seu arquivo foi processado.</p>`;
            uploadButton.textContent = "Concluído!";

            // Monta o link para o arquivo processado no outro bucket
            const processedFileName = `bw_${selectedFile.name}`;
            const publicDownloadUrl = `https://storage.googleapis.com/vision-gcloud-processed/${processedFileName}`;
            
            downloadLink.href = publicDownloadUrl;
            downloadLink.classList.remove('hidden'); // Mostra o botão de download

        } catch (error) {
            console.error('Erro no processo:', error);
            statusDiv.innerHTML = `<p>ERRO: ${error.message}</p>`;
            uploadButton.disabled = false; // Reabilita o botão em caso de erro
            uploadButton.textContent = "Tentar Novamente";
        }
    });
});