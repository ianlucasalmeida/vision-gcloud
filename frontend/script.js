// Espera o HTML ser completamente carregado para executar o script
document.addEventListener('DOMContentLoaded', () => {

    // 1. Seleciona os elementos do HTML com os quais vamos interagir
    const fileInput = document.getElementById('fileInput');
    const fileLabel = document.querySelector('.file-label'); // Seleciona pela classe
    const fileNameSpan = document.getElementById('fileName');
    const uploadButton = document.getElementById('uploadButton');
    const statusDiv = document.getElementById('status');
    const downloadLink = document.getElementById('downloadLink');

    // Variável para guardar o arquivo selecionado
    let selectedFile = null;

    // 2. Adiciona um "ouvinte" para o campo de seleção de arquivo
    fileInput.addEventListener('change', (event) => {
        // Pega o primeiro arquivo da lista de arquivos selecionados
        selectedFile = event.target.files[0];

        if (selectedFile) {
            // Se um arquivo foi selecionado:
            fileNameSpan.textContent = selectedFile.name; // Mostra o nome do arquivo
            uploadButton.disabled = false; // Habilita o botão de conversão
            fileLabel.textContent = "Trocar Arquivo"; // Muda o texto do botão de seleção
        } else {
            // Se o usuário cancelou a seleção:
            fileNameSpan.textContent = "Nenhum arquivo selecionado";
            uploadButton.disabled = true; // Mantém o botão desabilitado
            fileLabel.textContent = "Escolher Arquivo";
        }
    });

    // 3. Adiciona um "ouvinte" para o clique no botão de conversão
    // POR ENQUANTO, essa função apenas mostrará um alerta.
    // A lógica de upload virá no próximo passo.
    uploadButton.addEventListener('click', () => {
        if (selectedFile) {
            // Lógica de upload virá aqui
            alert(`Lógica de upload para o arquivo: ${selectedFile.name} será implementada aqui!`);
            statusDiv.innerHTML = `<p>Iniciando upload de ${selectedFile.name}...</p>`;
        } else {
            alert("Nenhum arquivo selecionado!");
        }
    });
});