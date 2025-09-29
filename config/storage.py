from cloudinary_storage.storage import MediaCloudinaryStorage
import cloudinary.uploader
import cloudinary
import mimetypes
import os

class CustomCloudinaryStorage(MediaCloudinaryStorage):
    """
    Storage customizado que gera URLs corretas para PDFs e outros arquivos
    """
    
    def _save(self, name, content):
        """
        Salvar arquivo no Cloudinary com resource_type apropriado
        """
        # Detectar tipo de arquivo
        content_type, _ = mimetypes.guess_type(name)
        
        # Configurações de upload
        options = {
            'invalidate': True,
            'use_filename': True,
            'unique_filename': True,
            'folder': 'media',
        }
        
        # Para PDFs e outros arquivos não-imagem, usar resource_type='raw'
        if content_type and not content_type.startswith('image/'):
            options['resource_type'] = 'raw'
        
        try:
            response = cloudinary.uploader.upload(content, **options)
            return response['public_id']
        except Exception as e:
            # Fallback: tentar como raw se falhar
            if 'resource_type' not in options:
                options['resource_type'] = 'raw'
                response = cloudinary.uploader.upload(content, **options)
                return response['public_id']
            raise e
    
    def url(self, name):
        """
        Gerar URL correta baseada no tipo de arquivo
        """
        if not name:
            return name
            
        # Detectar se é PDF ou outro tipo de arquivo
        _, ext = os.path.splitext(name)
        
        try:
            # Para PDFs, usar raw/upload para forçar download/visualização
            if ext.lower() == '.pdf':
                return cloudinary.CloudinaryResource(name).build_url(
                    resource_type='raw',
                    secure=True,
                    flags='attachment'  # Força download em vez de tentar renderizar
                )
            else:
                # Para imagens, usar o método padrão
                return super().url(name)
        except:
            # Fallback para URL padrão
            return super().url(name)