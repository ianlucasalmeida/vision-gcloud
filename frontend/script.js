// Espera o HTML ser completamente carregado para executar o script
document.addEventListener('DOMContentLoaded', () => {

    // --- Seleção dos Elementos da Página ---
    const fileInput = document.getElementById('fileInput');
    const conversionTypeSelect = document.getElementById('conversionType');
    const uploadButton = document.getElementById('uploadButton');
    const fileNameSpan = document.getElementById('fileName');
    const fileLabel = document.querySelector('.file-label');
    const statusDiv = document.getElementById('status');
    const downloadLink = document.getElementById('downloadLink');

    // IMPORTANTE: Cole a URL da sua NOVA função 'http-upload-file' aqui após o deploy dela.
    const httpUploadUrl = "COLE_A_URL_DA_SUA_NOVA_FUNCAO_HTTP_UPLOAD_AQUI"; 

    let selectedFile = null;

    // --- Lógica de Interação com a Página ---
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

    // --- Lógica Principal de Upload (Método Simplificado) ---
    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) {
            alert("Por favor, selecione um arquivo primeiro.");
            return;
        }

        // Desabilita o botão e atualiza o status
        uploadButton.disabled = true;
        uploadButton.textContent = "Enviando...";
        downloadLink.classList.add('hidden');
        statusDiv.innerHTML = `<p>Enviando arquivo para o servidor...</p>`;

        // Pega a opção de conversão para montar o nome do arquivo final
        const actionPrefix = conversionTypeSelect.value;
        const finalFileName = `${actionPrefix}_${selectedFile.name}`;

        // Cria um objeto FormData para encapsular o arquivo
        const formData = new FormData();
        formData.append('file', selectedFile, finalFileName);

        try {
            // --- ETAPA ÚNICA: Enviar o arquivo diretamente para a função de upload ---
            const response = await fetch(httpUploadUrl, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                // Se a resposta do servidor não for bem-sucedida, tenta ler o corpo como JSON
                const errorData = await response.json().catch(() => null);
                if (errorData && errorData.traceback) {
                    // Exibe o traceback do backend diretamente na tela
                    statusDiv.innerHTML = `<p>ERRO NO BACKEND:</p><pre>${errorData.traceback}</pre>`;
                } else {
                    throw new Error(`Falha no upload (Status: ${response.status})`);
                }
                uploadButton.disabled = false;
                uploadButton.textContent = "Tentar Novamente";
                return;
            }
            
            // --- Sucesso! Exibir o link para download do arquivo processado ---
            statusDiv.innerHTML = `<p>Sucesso! O arquivo foi enviado e está sendo processado.</p>`;
            
            setTimeout(() => {
                statusDiv.innerHTML = `<p>Processamento finalizado! Seu download está pronto.</p>`;
                
                const originalBaseName = selectedFile.name.split('.').slice(0, -1).join('.');
                let resultFileName;
                
                if (actionPrefix === 'pdf') {
                    resultFileName = `pdf_${originalBaseName}.pdf`;
                } else if (actionPrefix === 'jpg') {
                    resultFileName = `converted_${originalBaseName}.jpg`;
                } else {
                    resultFileName = `${actionPrefix}_${selectedFile.name}`;
                }

                const destinationBucket = 'vision-gcloud-processed';
                const publicDownloadUrl = `https://storage.googleapis.com/${destinationBucket}/${resultFileName}`;
                
                downloadLink.href = publicDownloadUrl;
                downloadLink.textContent = `Download de ${resultFileName}`;
                downloadLink.classList.remove('hidden');
                
                uploadButton.disabled = false;
                uploadButton.textContent = "Processar Outra Imagem";

            }, 8000);

        } catch (error) {
            console.error('Erro no processo:', error);
            
            // --- MUDANÇA CRUCIAL PARA DEPURAÇÃO ---
            if (error.response && typeof error.response.json === 'function') {
                const errorData = await error.response.json();
                statusDiv.innerHTML = `<p>ERRO NO BACKEND:</p><pre>${errorData.traceback}</pre>`;
            } else {
                statusDiv.innerHTML = `<p>ERRO: ${error.message}</p>`;
            }
            
            uploadButton.disabled = false;
            uploadButton.textContent = "Tentar Novamente";
        }
    });
});
