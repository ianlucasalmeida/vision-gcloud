document.addEventListener('DOMContentLoaded', () => {
    // ===================================================================
    // --- 1. SELEÇÃO DOS ELEMENTOS DA PÁGINA ---
    // ===================================================================
    const fileInput = document.getElementById('fileInput');
    const conversionTypeSelect = document.getElementById('conversionType');
    const uploadButton = document.getElementById('uploadButton');
    const fileNameSpan = document.getElementById('fileName');
    const fileLabel = document.querySelector('.file-label');
    const statusDiv = document.getElementById('status');
    const downloadLink = document.getElementById('downloadLink');

    // ===================================================================
    // --- 2. CONFIGURAÇÃO FINAL DAS URLS DO BACKEND ---
    // ===================================================================
    // URLs de produção confirmadas a partir dos seus logs de deploy.
    // Esta é a arquitetura final e robusta.
    const UPLOAD_URL = "https://direct-upload-file-egxj6adibq-rj.a.run.app"; 
    const DOWNLOAD_URL_GENERATOR = "https://stream-download-file-egxj6adibq-rj.a.run.app"; 

    let selectedFile = null;

    // ===================================================================
    // --- 3. LÓGICA DE INTERAÇÃO COM A INTERFACE ---
    // ===================================================================
    fileInput.addEventListener('change', (event) => {
        selectedFile = event.target.files[0];
        if (selectedFile) {
            fileNameSpan.textContent = selectedFile.name;
            uploadButton.disabled = false;
            fileLabel.textContent = "Trocar Imagem";
        } else {
            fileNameSpan.textContent = "Nenhum arquivo selecionado";
            uploadButton.disabled = true;
            fileLabel.textContent = "Escolher Imagem";
        }
    });

    // ===================================================================
    // --- 4. LÓGICA PRINCIPAL DE UPLOAD E PROCESSAMENTO ---
    // ===================================================================
    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) {
            alert("Por favor, selecione um ficheiro primeiro.");
            return;
        }

        // Reseta a interface para um novo processamento
        uploadButton.disabled = true;
        uploadButton.textContent = "A enviar...";
        statusDiv.innerHTML = `<p>A enviar o ficheiro para o servidor...</p>`;
        downloadLink.classList.add('hidden');

        // Pega a opção de conversão do menu para informar o backend
        const action = conversionTypeSelect.value;

        // Usa FormData para empacotar o ficheiro e a ação para envio
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('action', action);

        try {
            // --- ETAPA A: Envia o ficheiro e a ação para a função de upload direto ---
            const uploadResponse = await fetch(UPLOAD_URL, {
                method: 'POST',
                body: formData,
            });

            if (!uploadResponse.ok) {
                throw new Error(`Falha no upload (Status: ${uploadResponse.status})`);
            }
            
            // --- ETAPA B: Sucesso no upload, aguarda o processamento no backend ---
            statusDiv.innerHTML = `<p>Sucesso! O ficheiro foi enviado e está a ser processado...</p>`;
            
            // Usamos um timeout para dar tempo à função de processamento ser acionada e concluir
            setTimeout(() => {
                statusDiv.innerHTML = `<p>Processamento finalizado! O seu download está pronto.</p>`;
                
                // --- ETAPA C: Monta o link de download que aponta para a nossa função "porteiro" ---
                const originalBaseName = selectedFile.name.split('.').slice(0, -1).join('.');
                let resultFileName;
                
                if (action === 'pdf') {
                    resultFileName = `${originalBaseName}.pdf`;
                } else if (action === 'jpg') {
                    resultFileName = `${originalBaseName}.jpg`;
                } else {
                    // Para P&B, Sépia, etc., que salvamos como .jpg no backend
                    resultFileName = `${action}_${originalBaseName}.jpg`;
                }

                // O link agora aponta para a função que gera o download, passando o nome do ficheiro como parâmetro
                const downloadUrlWithParam = `${DOWNLOAD_URL_GENERATOR}?file=${resultFileName}`;
                
                downloadLink.href = downloadUrlWithParam;
                downloadLink.textContent = `Download de ${resultFileName}`;
                downloadLink.classList.remove('hidden'); // Mostra o botão de download
                
                uploadButton.disabled = false;
                uploadButton.textContent = "Processar Outra Imagem";

            }, 10000); // Espera 10 segundos

        } catch (error) {
            console.error('Erro no processo:', error);
            statusDiv.innerHTML = `<p>ERRO: ${error.message}</p>`;
            uploadButton.disabled = false;
            uploadButton.textContent = "Tentar Novamente";
        }
    });
});
