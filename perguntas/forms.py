from django import forms
from .models import Pergunta, Categoria


class PerguntaForm(forms.ModelForm):
    class Meta:
        model = Pergunta
        fields = ['titulo', 'pergunta', 'categoria']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite um título claro para sua pergunta',
                'maxlength': 200
            }),
            'pergunta': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Descreva sua pergunta de forma detalhada...'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apenas categorias ativas
        self.fields['categoria'].queryset = Categoria.objects.filter(ativo=True)
        self.fields['categoria'].empty_label = "Selecione uma categoria"
        
        # Labels personalizadas
        self.fields['titulo'].label = "Título da Pergunta"
        self.fields['pergunta'].label = "Sua Pergunta"
        self.fields['categoria'].label = "Categoria"
        
        # Help texts
        self.fields['titulo'].help_text = "Seja claro e específico no título"
        self.fields['pergunta'].help_text = "Forneça todos os detalhes necessários para uma resposta completa"