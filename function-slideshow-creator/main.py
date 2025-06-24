import functions_framework
from google.cloud import storage
from moviepy.editor import ImageSequenceClip
import os

@functions_framework.http
def create_slideshow(request):
    """
    Função HTTP para criar um vídeo de slideshow a partir de imagens.
    Recebe um JSON: {"imageFiles": ["img1.jpg", "img2.png"], "duration": 3}
    """
    request_json = request.get_json(silent=True)
    image_files = request_json.get('imageFiles')
    duration = request_json.get('duration', 3) # Duração de 3s por padrão

    storage_client = storage.Client()
    source_bucket = storage_client.bucket(os.environ.get('UPLOAD_BUCKET_NAME'))
    destination_bucket = storage_client.bucket(os.environ.get('DESTINATION_BUCKET_NAME'))
    
    downloaded_images = []
    temp_paths = []
    
    try:
        # Baixar todas as imagens
        for file_name in image_files:
            temp_path = f"/tmp/{os.path.basename(file_name)}"
            source_bucket.blob(file_name).download_to_filename(temp_path)
            downloaded_images.append(temp_path)
        
        # Criar o clipe de vídeo
        print("INFO: Criando o clipe de vídeo com MoviePy.")
        video_clip = ImageSequenceClip(downloaded_images, fps=1.0/duration)
        
        output_filename = "slideshow.mp4"
        temp_video_path = f"/tmp/{output_filename}"
        video_clip.write_videofile(temp_video_path, codec='libx264')
        
        # Fazer upload do resultado
        destination_blob = destination_bucket.blob(output_filename)
        destination_blob.upload_from_filename(temp_video_path)
        destination_blob.make_public()
        
        return ("Slideshow criado com sucesso!", 200)

    except Exception as e:
        print(f"ERRO ao criar slideshow: {e}")
        return ("Erro interno.", 500)
    finally:
        # Limpeza
        for path in downloaded_images:
            if os.path.exists(path): os.remove(path)
        if 'temp_video_path' in locals() and os.path.exists(temp_video_path):
             os.remove(temp_video_path)