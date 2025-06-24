document.addEventListener('DOMContentLoaded', () => {
    // Seleção dos Elementos da Página
    const fileInput = document.getElementById('fileInput');
    const conversionTypeSelect = document.getElementById('conversionType');
    const uploadButton = document.getElementById('uploadButton');
    const fileNameSpan = document.getElementById('fileName');
    const fileLabel = document.querySelector('.file-label');
    const statusDiv = document.getElementById('status');
    const downloadLink = document.getElementById('downloadLink');

    // URLs de produção confirmadas
    const UPLOAD_URL = "https://direct-upload-file-egxj6adibq-rj.a.run.app"; 
    const DOWNLOAD_URL_GENERATOR = "https://stream-download-file-egxj6adibq-rj.a.run.app";

    let selectedFile = null;

    // Lógica de Interação com a Interface
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

    // Lógica Principal de Upload e Download
    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) return;

        // Reset da interface
        uploadButton.disabled = true;
        uploadButton.textContent = "Enviando...";
        statusDiv.innerHTML = `<p>Enviando arquivo para o servidor...</p>`;
        downloadLink.classList.add('hidden');

        const actionPrefix = conversionTypeSelect.value;
        const finalFileName = `${actionPrefix}_${selectedFile.name}`;

        const formData = new FormData();
        formData.append('file', selectedFile, finalFileName);

        try {
            // Etapa A: Upload do ficheiro
            const uploadResponse = await fetch(UPLOAD_URL, {
                method: 'POST',
                body: formData,
            });
            if (!uploadResponse.ok) throw new Error(`Falha no upload (Status: ${uploadResponse.status})`);
            
            // Etapa B: Aguardar processamento
            statusDiv.innerHTML = `<p>Sucesso! O arquivo foi enviado e está sendo processado...</p>`;
            
            setTimeout(() => {
                statusDiv.innerHTML = `<p>Processamento finalizado! Seu download está pronto.</p>`;
                
                // Etapa C: Montar o link de download
                const originalBaseName = selectedFile.name.split('.').slice(0, -1).join('.');
                let resultFileName;
                
                if (actionPrefix === 'pdf') {
                    resultFileName = `pdf_${originalBaseName}.pdf`;
                } else if (actionPrefix === 'jpg') {
                    resultFileName = `converted_${originalBaseName}.jpg`;
                } else {
                    resultFileName = `${actionPrefix}_${originalBaseName}.jpg`;
                }
                
                const downloadUrlWithParam = `${DOWNLOAD_URL_GENERATOR}?file=${resultFileName}`;
                
                downloadLink.href = downloadUrlWithParam;
                downloadLink.textContent = `Download de ${resultFileName}`;
                downloadLink.classList.remove('hidden');
                
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