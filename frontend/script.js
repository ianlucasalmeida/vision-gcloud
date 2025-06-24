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

    // IMPORTANTE: Cole a URL da sua função 'generate-upload-url' aqui
    const signedUrlGeneratorUrl = "https://generate-upload-url-egxj6adibq-rj.a.run.app";

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

    // --- Lógica Principal de Upload e Processamento ---
    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) {
            alert("Por favor, selecione um arquivo primeiro.");
            return;
        }

        // Desabilita o botão para evitar múltiplos envios
        uploadButton.disabled = true;
        uploadButton.textContent = "Processando...";
        downloadLink.classList.add('hidden'); // Esconde o link de download anterior

        // Lê a opção de conversão escolhida pelo usuário no menu dropdown
        const actionPrefix = conversionTypeSelect.value;
        // Monta o nome do arquivo com o prefixo para o backend saber o que fazer
        const finalFileName = `${actionPrefix}_${selectedFile.name}`;

        try {
            // ETAPA A: Pedir a URL assinada para nossa função de apoio
            statusDiv.innerHTML = `<p>1/3: Solicitando permissão de upload...</p>`;
            
            const response = await fetch(signedUrlGeneratorUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fileName: finalFileName }),
            });

            if (!response.ok) {
                // Se a resposta não for bem-sucedida, lança um erro
                throw new Error(`Falha ao obter a URL de upload (Status: ${response.status})`);
            }
            const data = await response.json();
            const signedUrl = data.url;

            // ETAPA B: Fazer o upload do arquivo para a URL recebida do Google
            statusDiv.innerHTML = `<p>2/3: Enviando arquivo para o Cloud Storage...</p>`;
            
            const uploadResponse = await fetch(signedUrl, {
                method: 'PUT',
                body: selectedFile,
                headers: { 'Content-Type': 'application/octet-stream' }
            });

            if (!uploadResponse.ok) {
                throw new Error('Falha no upload do arquivo para o Cloud Storage.');
            }

            // ETAPA C: Sucesso! Exibir o link para download do arquivo processado
            statusDiv.innerHTML = `<p>3/3: Sucesso! Aguarde a conversão ser concluída...</p>`;
            
            // Espera um tempo para dar à função de processamento tempo para executar
            setTimeout(() => {
                statusDiv.innerHTML = `<p>Processamento finalizado! Seu download está pronto.</p>`;
                
                // Lógica para montar o nome do arquivo de resultado corretamente
                const originalBaseName = selectedFile.name.split('.').slice(0, -1).join('.');
                let resultFileName;
                
                if (actionPrefix === 'pdf') {
                    resultFileName = `pdf_${originalBaseName}.pdf`;
                } else if (actionPrefix === 'jpg') {
                    resultFileName = `converted_${originalBaseName}.jpg`;
                } else if (actionPrefix === 'bw') {
                    // Nossa função de P&B salva como jpg para consistência
                    resultFileName = `bw_${originalBaseName}.jpg`;
                } else {
                    // Para sépia e outros filtros que mantêm o formato
                    resultFileName = `${actionPrefix}_${selectedFile.name}`;
                }

                const destinationBucket = 'vision-gcloud-processed'; // Seu bucket de destino
                const publicDownloadUrl = `https://storage.googleapis.com/${destinationBucket}/${resultFileName}`;
                
                downloadLink.href = publicDownloadUrl;
                downloadLink.textContent = `Download de ${resultFileName}`;
                downloadLink.classList.remove('hidden'); // Mostra o botão de download
                
                // Reabilita o botão para uma nova operação
                uploadButton.disabled = false;
                uploadButton.textContent = "Processar Outra Imagem";

            }, 8000); // Espera 8 segundos (aumentamos para conversões mais complexas)

        } catch (error) {
            console.error('Erro no processo:', error);
            statusDiv.innerHTML = `<p>ERRO: ${error.message}</p>`;
            uploadButton.disabled = false;
            uploadButton.textContent = "Tentar Novamente";
        }
    });
});