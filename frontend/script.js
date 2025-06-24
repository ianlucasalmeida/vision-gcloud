document.addEventListener('DOMContentLoaded', () => {
    // --- Seleção de Elementos ---
    const fileInput = document.getElementById('fileInput');
    const conversionTypeSelect = document.getElementById('conversionType');
    const uploadButton = document.getElementById('uploadButton');
    const fileNameSpan = document.getElementById('fileName');
    const fileLabel = document.querySelector('.file-label');
    const statusDiv = document.getElementById('status');
    const downloadLink = document.getElementById('downloadLink');

    // --- Lógica de Interação com a Página ---
    let selectedFile = null;
    fileInput.addEventListener('change', (event) => {
        selectedFile = event.target.files[0];
        if (selectedFile) {
            fileNameSpan.textContent = selectedFile.name;
            uploadButton.disabled = false;
        } else {
            fileNameSpan.textContent = "Nenhum arquivo selecionado";
            uploadButton.disabled = true;
        }
    });

    // ===================================================================
    // --- NOVA LÓGICA DE UPLOAD (MÉTODO DIRETO E SIMPLIFICADO) ---
    // ===================================================================
    // IMPORTANTE: Cole a URL da sua NOVA função 'direct-upload-file' aqui
    const UPLOAD_URL = "https://direct-upload-file-egxj6adibq-rj.a.run.app";

    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) return;

        uploadButton.disabled = true;
        uploadButton.textContent = "Enviando...";
        statusDiv.innerHTML = `<p>Enviando arquivo para o servidor...</p>`;
        downloadLink.classList.add('hidden');

        const actionPrefix = conversionTypeSelect.value;
        const finalFileName = `${actionPrefix}_${selectedFile.name}`;

        const formData = new FormData();
        formData.append('file', selectedFile, finalFileName);

        try {
            const response = await fetch(UPLOAD_URL, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Falha no upload (Status: ${response.status})`);
            }
            
            statusDiv.innerHTML = `<p>Sucesso! O arquivo foi enviado e está sendo processado...</p>`;
            
            setTimeout(() => {
                statusDiv.innerHTML = `<p>Processamento finalizado! Seu download está pronto.</p>`;
                
                const originalBaseName = selectedFile.name.split('.').slice(0, -1).join('.');
                let resultFileName;
                
                if (actionPrefix === 'pdf') {
                    resultFileName = `pdf_${originalBaseName}.pdf`;
                } else if (actionPrefix === 'jpg') {
                    resultFileName = `converted_${originalBaseName}.jpg`;
                } else {
                    resultFileName = `${actionPrefix}_${originalBaseName}.jpg`;
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
            statusDiv.innerHTML = `<p>ERRO: ${error.message}</p>`;
            uploadButton.disabled = false;
            uploadButton.textContent = "Tentar Novamente";
        }
    });

    // ===================================================================
    // --- LÓGICA ANTIGA (SALVAGUARDA - URL ASSINADA) ---
    // ===================================================================
    /*
    const signedUrlGeneratorUrl = "COLE_A_URL_DA_FUNCAO_ANTIGA_GENERATE_UPLOAD_URL_AQUI";

    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) return;

        uploadButton.disabled = true;
        uploadButton.textContent = "Processando...";
        downloadLink.classList.add('hidden');

        const actionPrefix = conversionTypeSelect.value;
        const finalFileName = `${actionPrefix}_${selectedFile.name}`;

        try {
            statusDiv.innerHTML = `<p>1/3: Solicitando permissão de upload...</p>`;
            const response = await fetch(signedUrlGeneratorUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fileName: finalFileName }),
            });
            if (!response.ok) { throw new Error('Falha ao obter a URL de upload.'); }
            const data = await response.json();

            statusDiv.innerHTML = `<p>2/3: Enviando arquivo...</p>`;
            const uploadResponse = await fetch(data.url, {
                method: 'PUT',
                body: selectedFile,
                headers: { 'Content-Type': 'application/octet-stream' }
            });
            if (!uploadResponse.ok) { throw new Error('Falha no upload do arquivo.'); }

            statusDiv.innerHTML = `<p>3/3: Sucesso! Aguarde a conversão...</p>`;
            
            setTimeout(() => {
                // ... lógica para exibir o link de download ...
            }, 8000);

        } catch (error) {
            // ... lógica de tratamento de erro ...
        }
    });
    */
});