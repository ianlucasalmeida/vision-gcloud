document.addEventListener('DOMContentLoaded', () => {
    // Seleção de Elementos
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const fileNameSpan = document.getElementById('fileName');
    const statusDiv = document.getElementById('status');
    const downloadLink = document.getElementById('downloadLink');

    // URLs de produção confirmadas (as mesmas de antes)
    const UPLOAD_URL = "https://direct-upload-file-egxj6adibq-rj.a.run.app"; 
    const DOWNLOAD_URL = "https://stream-download-file-egxj6adibq-rj.a.run.app";

    let selectedFile = null;

    fileInput.addEventListener('change', (event) => {
        selectedFile = event.target.files[0];
        if (selectedFile) {
            fileNameSpan.textContent = selectedFile.name;
            uploadButton.disabled = false;
        }
    });

    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) return;

        uploadButton.disabled = true;
        uploadButton.textContent = "A converter...";
        statusDiv.innerHTML = `<p>A enviar o ficheiro para o servidor...</p>`;
        downloadLink.classList.add('hidden');

        // A ação para esta página é sempre a mesma
        const action = 'docx-to-pdf';

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('action', action);

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
                const resultFileName = `${originalBaseName}.pdf`;
                const downloadUrlWithParam = `${DOWNLOAD_URL}?file=${resultFileName}`;
                
                downloadLink.href = downloadUrlWithParam;
                downloadLink.textContent = `Download de ${resultFileName}`;
                downloadLink.classList.remove('hidden');
                
                uploadButton.disabled = false;
                uploadButton.textContent = "Converter para PDF";
            }, 15000); // 15 segundos para conversão de documentos

        } catch (error) {
            console.error('Erro no processo:', error);
            statusDiv.innerHTML = `<p>ERRO: ${error.message}</p>`;
            uploadButton.disabled = false;
            uploadButton.textContent = "Tentar Novamente";
        }
    });
});
