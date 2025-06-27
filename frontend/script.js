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
            fileNameSpan.textContent = "Nenhum ficheiro selecionado";
            uploadButton.disabled = true;
            fileLabel.textContent = "Escolher Imagem";
        }
    });

    /**
     * Função auxiliar para "limpar" o nome de um ficheiro, removendo caracteres
     * especiais, da mesma forma que o backend faz.
     * @param {string} filename - O nome original do ficheiro.
     * @returns {string} - O nome do ficheiro limpo.
     */
    const secureFilename = (filename) => {
        // Substitui caracteres não seguros por um underscore
        return filename.replace(/[^a-zA-Z0-9_.-]/g, '_');
    }

    // ===================================================================
    // --- 4. FUNÇÃO DE POLLING MELHORADA ---
    // ===================================================================
    /**
     * Verifica periodicamente se um ficheiro está disponível para download,
     * atualizando a interface durante o processo.
     * @param {string} url - A URL da função de download que tentará obter o ficheiro.
     * @param {number} attempts - O número máximo de tentativas.
     * @param {number} interval - O intervalo em milissegundos entre as tentativas.
     * @returns {Promise<boolean>} - Retorna true se o ficheiro estiver pronto, false caso contrário.
     */
    const waitUntilFileReady = async (url, attempts = 20, interval = 2500) => {
        for (let i = 0; i < attempts; i++) {
            statusDiv.innerHTML = `<p>A verificar o resultado... Tentativa ${i + 1} de ${attempts}</p>`;
            try {
                // A nossa função de streaming retorna 200 OK se encontrar o ficheiro.
                const res = await fetch(url);
                if (res.ok) {
                    console.log(`Ficheiro pronto após ${i + 1} tentativas.`);
                    return true;
                }
            } catch (e) {
                console.warn(`A verificação falhou, a tentar novamente...`, e);
            }
            // Aguarda o próximo intervalo antes de tentar novamente.
            await new Promise(r => setTimeout(r, interval));
        }
        console.error("Tempo limite atingido. O ficheiro não ficou pronto a tempo.");
        return false;
    };

    // ===================================================================
    // --- 5. LÓGICA PRINCIPAL DE UPLOAD E PROCESSAMENTO ---
    // ===================================================================
    uploadButton.addEventListener('click', async () => {
        if (!selectedFile) {
            alert("Por favor, selecione um ficheiro.");
            return;
        }

        // UI: Reset e Feedback Inicial
        uploadButton.disabled = true;
        uploadButton.textContent = "A enviar...";
        statusDiv.innerHTML = `<p>A enviar o ficheiro para o servidor...</p>`;
        downloadLink.classList.add('hidden');

        const action = conversionTypeSelect.value;
        const cleanFilename = secureFilename(selectedFile.name);

        const formData = new FormData();
        formData.append('file', selectedFile, cleanFilename);
        formData.append('action', action);

        try {
            // ETAPA A: Upload
            const uploadResponse = await fetch(UPLOAD_URL, {
                method: 'POST',
                body: formData,
            });

            if (!uploadResponse.ok) {
                throw new Error(`Falha no upload (Status: ${uploadResponse.status})`);
            }
            
            // ETAPA B: Aguardar o Processamento (com Polling)
            const originalBaseName = cleanFilename.split('.').slice(0, -1).join('.');
            let resultFileName;

            // Lógica de nomeação de ficheiros corrigida e sincronizada com o backend
            if (action === 'image-to-pdf') {
                resultFileName = `${originalBaseName}.pdf`;
            } else if (action === 'png') {
                resultFileName = `${originalBaseName}.png`;
            } else if (action === 'jpg') {
                resultFileName = `${originalBaseName}.jpg`;
            } else { // bw, sepia
                resultFileName = `${action}_${originalBaseName}.jpg`;
            }

            const downloadUrlWithParam = `${DOWNLOAD_URL_GENERATOR}?file=${encodeURIComponent(resultFileName)}`;

            const fileReady = await waitUntilFileReady(downloadUrlWithParam);

            // ETAPA C: Apresentar o Resultado
            if (fileReady) {
                statusDiv.innerHTML = `<p>Processamento concluído! Pronto para download.</p>`;
                downloadLink.href = downloadUrlWithParam;
                downloadLink.textContent = `Download de ${resultFileName}`;
                downloadLink.classList.remove('hidden');
                uploadButton.textContent = "Processar Outro Ficheiro";
            } else {
                statusDiv.innerHTML = `<p>Tempo limite atingido. O processamento demorou mais que o esperado.</p>`;
                uploadButton.textContent = "Tentar Novamente";
            }

        } catch (error) {
            console.error('Erro no processo:', error);
            statusDiv.innerHTML = `<p>Erro: ${error.message}</p>`;
            uploadButton.textContent = "Tentar Novamente";
        }

        uploadButton.disabled = false;
    });
});
