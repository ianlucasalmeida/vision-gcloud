Vision-GCloud: Suíte de Ferramentas de Imagem e Documentos
1. Visão Geral do Projeto
O Vision-GCloud é uma aplicação web robusta, construída sobre uma arquitetura totalmente serverless na Google Cloud Platform (GCP). O objetivo é oferecer um conjunto de ferramentas de processamento de mídia de alta performance, focadas na manipulação de imagens e na conversão de documentos. A aplicação permite que os usuários enviem ficheiros de vários formatos, incluindo os de alta resolução, apliquem transformações complexas e descarreguem o resultado de forma segura e eficiente.

2. Arquitetura da Solução
A solução utiliza serviços gerenciados da Google Cloud para garantir escalabilidade e segurança. O fluxo de dados da aplicação segue o seguinte diagrama:

graph TD
    subgraph "Utilizador"
        A[Navegador do Utilizador]
    end

    subgraph "Firebase Hosting"
        B["Frontend: Landing Page & Ferramentas"]
    end

    subgraph "Google Cloud"
        C["Função: direct-upload-file (HTTP)"]
        D["Bucket: vision-gcloud-uploads"]
        E["Função: vision-gcloud-processor (Evento GCS)"]
        F["Bucket: vision-gcloud-processed"]
        G["Função: stream-download-file (HTTP)"]
    end

    A -- "1. Envia ficheiro e ação" --> C
    C -- "2. Guarda ficheiro com metadados" --> D
    D -- "3. Aciona evento de novo ficheiro" --> E
    E -- "4. Lê ficheiro, processa e guarda resultado" --> F
    A -- "5. Clica no link de download" --> G
    G -- "6. Lê ficheiro privado" --> F
    G -- "7. Entrega o ficheiro ao utilizador" --> A
    B -- "Serve o site para" --> A

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#9f9,stroke:#333,stroke-width:2px
    style D fill:#f96,stroke:#333,stroke-width:2px
    style E fill:#9f9,stroke:#333,stroke-width:2px
    style F fill:#f96,stroke:#333,stroke-width:2px
    style G fill:#9f9,stroke:#333,stroke-width:2px


Frontend (Firebase Hosting): Uma interface web reativa com uma Landing Page e páginas dedicadas para cada ferramenta.

Backend (Cloud Functions):

direct-upload-file: Valida o tamanho do ficheiro (limite de 100MB) e guarda-o no Cloud Storage com a ação desejada como metadado.

vision-gcloud-processor: O "cérebro" da aplicação. Acionada por eventos, lê os metadados e executa a transformação correta (imagem ou documento). Foi configurada com 2GiB de memória para processar ficheiros maiores.

stream-download-file: Atua como um "proxy" de download seguro, servindo os ficheiros privados para o utilizador final.

Armazenamento (Cloud Storage): Dois buckets privados para os ficheiros originais e os processados.

3. Funcionalidades Implementadas
Ferramentas de Imagem
Filtros Artísticos: Conversão para Preto e Branco e aplicação de Tom Sépia.

Conversão de Formato: Permite converter imagens de e para formatos populares como .jpg e .png.

Imagem para PDF: Converte um ficheiro de imagem diretamente para um documento .pdf.

Suporte a Múltiplos Formatos: Aceita uma vasta gama de formatos de entrada, incluindo .jpg, .png, .webp, e .heif/.heic.

Ferramentas de Documentos
Conversão DOCX para PDF: Converte ficheiros de formato .docx para o formato universal .pdf.

Métricas e Segurança
Limite de Tamanho de Upload: A função de upload rejeita ficheiros maiores que 100MB para garantir a estabilidade e controlar custos.

Download Seguro: Os ficheiros processados nunca são expostos publicamente. O download é gerenciado por uma função que entrega os ficheiros de forma segura e direta ao utilizador.

4. Como Executar o Projeto (Guia de Deploy)
Para implantar o projeto Vision-GCloud, são necessários os seguintes passos:

Pré-requisitos
Ter a gcloud CLI e a firebase CLI instaladas e autenticadas no seu ambiente.

Um projeto Google Cloud com o faturamento ativado (o Nível Gratuito cobre os custos deste projeto).

Ter as APIs Cloud Functions, Cloud Storage, Cloud Build, Cloud Run, e IAM Service Account Credentials ativadas no projeto.

1. Deploy do Backend
O backend consiste em três funções. Para cada uma, navegue até a sua respetiva pasta (function-direct-upload, function-stream-download, function-source) e execute o comando de deploy gcloud functions deploy ... apropriado, garantindo que as variáveis de ambiente e contas de serviço corretas sejam especificadas. A função vision-gcloud-processor deve ser implantada com uma alocação de memória maior (ex: 2GiB) para lidar com o processamento de ficheiros.

2. Deploy do Frontend
Navegue para a pasta raiz do projeto (vision-gcloud).

Execute firebase init hosting, configurando a pasta frontend como o diretório público.

Atualize as URLs das funções de backend no(s) ficheiro(s) JavaScript (script.js, etc.).

Execute firebase deploy --only hosting para publicar o site.

Após a conclusão, o site estará disponível na Hosting URL fornecida pelo Firebase.