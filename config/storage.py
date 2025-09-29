from cloudinary_storage.storage import MediaCloudinaryStorage
import cloudinary.uploader
import mimetypes
import os

class CustomCloudinaryStorage(MediaCloudinaryStorage):
    """
    Storage customizado para suportar PDFs e outros arquivos no Cloudinary
    """
    
    def _save(self, name, content):
        """
        Salvar arquivo no Cloudinary com resource_type apropriado
        """
        # Detectar tipo de arquivo
        content_type, _ = mimetypes.guess_type(name)
        
        # Configurações de upload
        options = {
            'public_id': self._get_public_id(name),
            'invalidate': True,
            'use_filename': True,
            'unique_filename': False,
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
    
    def _get_public_id(self, name):
        """
        Gerar public_id mantendo a estrutura de pastas
        """
        # Remover extensão para o public_id
        public_id = os.path.splitext(name)[0]
        return public_id