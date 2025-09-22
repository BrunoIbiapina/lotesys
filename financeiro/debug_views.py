"""
Views para debug de media e arquivos
"""
import os
from django.http import JsonResponse
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def debug_media(request):
    """View para debugar configuração de media (apenas para admins)"""
    
    info = {
        "media_root": str(settings.MEDIA_ROOT),
        "media_url": settings.MEDIA_URL,
        "media_root_exists": os.path.exists(settings.MEDIA_ROOT),
        "debug": settings.DEBUG,
        "render_hostname": os.getenv("RENDER_EXTERNAL_HOSTNAME", "N/A"),
        "serve_media": os.getenv("SERVE_MEDIA", "False"),
    }
    
    # Lista estrutura de pastas se existir
    if os.path.exists(settings.MEDIA_ROOT):
        try:
            structure = {}
            for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                rel_path = os.path.relpath(root, settings.MEDIA_ROOT)
                if rel_path == ".":
                    rel_path = "/"
                structure[rel_path] = {
                    "dirs": dirs,
                    "files": files[:10],  # Apenas primeiros 10 arquivos
                    "file_count": len(files)
                }
            info["structure"] = structure
        except Exception as e:
            info["structure_error"] = str(e)
    
    return JsonResponse(info, indent=2)