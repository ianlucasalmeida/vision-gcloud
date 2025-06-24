document.addEventListener('DOMContentLoaded', () => {
    // Seleciona os elementos da página
    const fileInput = document.getElementById('fileInput');
    const conversionTypeSelect = document.getElementById('conversionType');
    const uploadButton = document.getElementById('uploadButton');
    const fileNameSpan = document.getElementById('fileName');
    // ... (outras seleções de elementos como antes)
    const statusDiv = document.getElementById('status');
    const downloadLink = document.getElementById('downloadLink');

    const signedUrlGeneratorUrl = "COLE_A_URL_DA_SUA_FUNCAO_GENERATE_UPLOAD_URL_AQUI"; // IMPORTANTE

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

    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) return;

        uploadButton.disabled = true;
        uploadButton.textContent = "Processando...";
        downloadLink.classList.add('hidden');

        // Pega a opção de conversão escolhida pelo usuário
        const actionPrefix = conversionTypeSelect.value;
        const finalFileName = `${actionPrefix}_${selectedFile.name}`;

        try {
            statusDiv.innerHTML = `<p>1/3: Solicitando permissão de upload...</p>`;
            const response = await fetch(signedUrlGeneratorUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fileName: finalFileName }), // Envia o nome final com prefixo
            });
            if (!response.ok) throw new Error('Falha ao obter a URL de upload.');
            const data = await response.json();

            statusDiv.innerHTML = `<p>2/3: Enviando arquivo...</p>`;
            const uploadResponse = await fetch(data.url, {
                method: 'PUT',
                body: selectedFile,
                headers: { 'Content-Type': 'application/octet-stream' }
            });
            if (!uploadResponse.ok) throw new Error('Falha no upload do arquivo.');

            statusDiv.innerHTML = `<p>3/3: Sucesso! Aguarde a conversão...</p>`;
            
            setTimeout(() => {
                statusDiv.innerHTML = `<p>Processamento finalizado!</p>`;
                uploadButton.textContent = "Concluído!";
                
                // Monta o nome do arquivo de resultado
                const originalBaseName = selectedFile.name.split('.').slice(0, -1).join('.');
                let resultFileName;
                if(actionPrefix === 'pdf') {
                    resultFileName = `pdf_${originalBaseName}.pdf`;
                } else if(actionPrefix === 'jpg') {
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

            }, 7000); // Aumentamos o tempo para conversões mais demoradas

        } catch (error) {
            // ... (código de tratamento de erro permanece o mesmo)
        }
    });
});