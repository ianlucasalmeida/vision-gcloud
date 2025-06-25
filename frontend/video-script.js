document.addEventListener('DOMContentLoaded', () => {
    // --- Seleção dos Elementos da Página de Vídeo ---
    const fileInput = document.getElementById('fileInput'); // O ID no HTML é fileInput
    const videoActionSelect = document.getElementById('videoActionType');
    const uploadButton = document.getElementById('uploadButton'); // O ID no HTML é uploadButton
    const fileNameSpan = document.getElementById('fileName');
    const fileLabel = document.querySelector('.file-label');
    const statusDiv = document.getElementById('status');
    const downloadLink = document.getElementById('downloadLink');
    const thumbSecondInput = document.getElementById('thumbSecond');

    // URLs de produção confirmadas
    const UPLOAD_URL = "https://direct-upload-file-egxj6adibq-rj.a.run.app"; 
    const DOWNLOAD_URL = "https://stream-download-file-egxj6adibq-rj.a.run.app";

    let selectedFile = null;

    fileInput.addEventListener('change', (event) => {
        selectedFile = event.target.files[0];
        if (selectedFile) {
            fileNameSpan.textContent = selectedFile.name;
            uploadButton.disabled = false;
            fileLabel.textContent = "Trocar Vídeo";
        } else {
            fileNameSpan.textContent = "Nenhum arquivo selecionado";
            uploadButton.disabled = true;
            fileLabel.textContent = "Escolher Vídeo";
        }
    });

    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) return;

        uploadButton.disabled = true;
        uploadButton.textContent = "A enviar...";
        statusDiv.innerHTML = `<p>A enviar o ficheiro para o servidor... Pode demorar.</p>`;
        downloadLink.classList.add('hidden');

        const action = videoActionSelect.value;
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('action', action);

        // Envia o segundo do thumbnail se a ação for essa
        if (action === 'thumbnail') {
            formData.append('thumb_second', thumbSecondInput.value);
        }

        try {
            const uploadResponse = await fetch(UPLOAD_URL, {
                method: 'POST',
                body: formData,
            });
            if (!uploadResponse.ok) throw new Error(`Falha no upload (Status: ${uploadResponse.status})`);
            
            statusDiv.innerHTML = `<p>Sucesso! O ficheiro foi enviado e está a ser processado...</p>`;
            
            setTimeout(() => {
                statusDiv.innerHTML = `<p>Processamento finalizado! O seu download está pronto.</p>`;
                
                const originalBaseName = selectedFile.name.split('.').slice(0, -1).join('.');
                let resultFileName;

                if (action === 'thumbnail') {
                    resultFileName = `thumbnail_${originalBaseName}.jpg`;
                }
                // Adicione outras lógicas de nome para novas ações de vídeo aqui

                const downloadUrlWithParam = `${DOWNLOAD_URL}?file=${resultFileName}`;
                
                downloadLink.href = downloadUrlWithParam;
                downloadLink.textContent = `Download de ${resultFileName}`;
                downloadLink.classList.remove('hidden');
                
                uploadButton.disabled = false;
                uploadButton.textContent = "Processar Outro Vídeo";
            }, 25000); // Aumentado para 25 segundos para processamento de vídeo

        } catch (error) {
            console.error('Erro no processo:', error);
            statusDiv.innerHTML = `<p>ERRO: ${error.message}</p>`;
            uploadButton.disabled = false;
            uploadButton.textContent = "Tentar Novamente";
        }
    });
});
