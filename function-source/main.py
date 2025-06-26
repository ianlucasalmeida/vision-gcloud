import os
import re
import logging
from urllib.parse import unquote
from google.cloud import storage
from PIL import Image, UnidentifiedImageError
import pillow_heif

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Registra o suporte para HEIF/HEIC
pillow_heif.register_heif_opener()

def sanitize_filename(filename):
    """Remove caracteres especiais e espaços do nome do arquivo"""
    base_name = os.path.basename(filename)
    clean_name = re.sub(r'[^\w.-]', '_', base_name)
    return clean_name[:150]  # Limita o tamanho do nome

def apply_sepia(img):
    """Aplica filtro de sépia de forma otimizada"""
    if img.mode != 'RGB':
        img = img.convert('RGB')
    sepia_matrix = (
        0.393, 0.769, 0.189, 0,
        0.349, 0.686, 0.168, 0,
        0.272, 0.534, 0.131, 0
    )
    return img.convert('RGB', sepia_matrix)

def vision_gcloud_processor(event, context):
    """Processa imagens com tratamento robusto de erros e sanitização"""
    file_data = event
    bucket_name = file_data['bucket']
    raw_file_name = unquote(file_data['name'])  # Decodifica caracteres especiais
    clean_file_name = sanitize_filename(raw_file_name)
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    try:
        blob = bucket.get_blob(raw_file_name)
        if not blob:
            logger.error(f"Arquivo '{raw_file_name}' não encontrado no bucket")
            return

        # Validação de metadados
        if not blob.metadata or 'action' not in blob.metadata:
            logger.warning(f"Arquivo '{clean_file_name}' sem metadado 'action'")
            return
            
        action = blob.metadata['action']
        logger.info(f"Processando: {clean_file_name} | Ação: {action}")

        # Configuração do bucket de destino
        destination_bucket_name = os.environ.get('DESTINATION_BUCKET', 'vision-gcloud-processed')
        destination_bucket = client.bucket(destination_bucket_name)
        
        # Caminhos temporários sanitizados
        temp_input_path = f"/tmp/input_{os.getpid()}_{clean_file_name}"
        blob.download_to_filename(temp_input_path)
        
        # Processamento da imagem
        with Image.open(temp_input_path) as img:
            # Tratamento de transparência
            if img.mode in ('RGBA', 'LA') or (hasattr(img, 'transparency') and img.transparency is not None):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            else:
                img = img.convert('RGB')

            # Aplicação das transformações
            output_format = 'JPEG'
            prefix = ""
            
            if action == 'bw':
                processed_img = img.convert('L')
                prefix = "bw_"
            elif action == 'sepia':
                processed_img = apply_sepia(img)
                prefix = "sepia_"
            elif action == 'png':
                output_format = 'PNG'
                processed_img = img
            elif action == 'jpg':
                processed_img = img
            elif action == 'image-to-pdf':
                output_format = 'PDF'
                processed_img = img
            else:
                raise ValueError(f"Ação inválida: {action}")

            # Nome do arquivo de saída sanitizado
            base_name = os.path.splitext(clean_file_name)[0]
            processed_file_name = f"{prefix}{base_name}.{output_format.lower() if output_format != 'PDF' else 'pdf'}"
            temp_output_path = f"/tmp/output_{os.getpid()}_{processed_file_name}"
            
            # Salvamento com tratamento de erros
            try:
                processed_img.save(
                    temp_output_path,
                    format=output_format,
                    quality=85,
                    optimize=True
                )
            except OSError as e:
                logger.error(f"Erro ao salvar imagem: {str(e)}")
                # Tenta fallback para JPEG
                if output_format != 'JPEG':
                    processed_file_name = f"{prefix}{base_name}.jpg"
                    temp_output_path = f"/tmp/output_{os.getpid()}_{processed_file_name}"
                    processed_img.save(temp_output_path, format='JPEG', quality=85)
                    output_format = 'JPEG'

            # Upload para GCS
            destination_blob = destination_bucket.blob(processed_file_name)
            destination_blob.upload_from_filename(temp_output_path)
            
            # Define content-type correto
            content_type = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'PDF': 'application/pdf'
            }.get(output_format, 'application/octet-stream')
            
            destination_blob.content_type = content_type
            destination_blob.patch()
            
            logger.info(f"Sucesso: {processed_file_name} salvo em {destination_bucket_name}")

    except UnidentifiedImageError:
        logger.error(f"Formato de imagem inválido: {clean_file_name}")
    except ValueError as ve:
        logger.error(f"Erro de valor: {str(ve)}")
    except Exception as e:
        logger.exception(f"Erro crítico no processamento de {clean_file_name}")
    finally:
        # Limpeza segura com verificação
        for path in [temp_input_path, temp_output_path]:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except (OSError, NameError, TypeError) as clean_error:
                logger.warning(f"Erro na limpeza: {str(clean_error)}")
        
        logger.info("Limpeza de temporários concluída")