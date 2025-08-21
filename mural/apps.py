from django.apps import AppConfig

class MuralConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mural"          # <-- tem que ser exatamente o nome da pasta do app
    verbose_name = "Mural"