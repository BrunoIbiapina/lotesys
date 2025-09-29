from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_auth(request):
    """
    Endpoint para autenticação de usuários via WhatsApp Bot
    Recebe: {"username": "usuario", "password": "senha"}
    Retorna: {"success": True/False, "message": "...", "user_data": {...}}
    """
    try:
        # Parse do JSON
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': '❌ Nome de usuário e senha são obrigatórios'
            })
        
        # Tentar autenticar o usuário
        user = authenticate(username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Usuário autenticado com sucesso
                return JsonResponse({
                    'success': True,
                    'message': '✅ Login realizado com sucesso!',
                    'user_data': {
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser
                    }
                })
            else:
                # Usuário existe mas está inativo
                return JsonResponse({
                    'success': False,
                    'message': '❌ Sua conta está desativada. Contate o administrador.'
                })
        else:
            # Credenciais inválidas
            return JsonResponse({
                'success': False,
                'message': '❌ Nome de usuário ou senha incorretos'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '❌ Dados inválidos enviados'
        })
    except Exception as e:
        logger.error(f"Erro na autenticação WhatsApp: {e}")
        return JsonResponse({
            'success': False,
            'message': '❌ Erro interno do servidor'
        })

@csrf_exempt  
@require_http_methods(["POST"])
def whatsapp_user_info(request):
    """
    Endpoint para buscar informações de um usuário por ID
    Usado para validar sessões ativas
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'ID do usuário é obrigatório'
            })
        
        try:
            user = User.objects.get(id=user_id, is_active=True)
            return JsonResponse({
                'success': True,
                'user_data': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser
                }
            })
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '❌ Usuário não encontrado ou inativo'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '❌ Dados inválidos'
        })
    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {e}")
        return JsonResponse({
            'success': False,
            'message': '❌ Erro interno do servidor'
        })
