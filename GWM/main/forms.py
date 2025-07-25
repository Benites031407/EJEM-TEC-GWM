from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Planejado, Executado, Captacao, Estatisticas, Area, FinanceHistory
from decimal import Decimal
import re

#Formulário de login customizado para mostrar como forma de login o email corporativo
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email Corporativo", 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu email corporativo'
        })
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        })
    )

#Criação dos campos do formulário de ações planejadas (Head)
class PlanejadoForm(forms.ModelForm):
    class Meta:
        model = Planejado
        exclude = ['user', 'month', 'year', 'created_at']
        labels = {
            'auc': 'AUC Planejado',
            'receita': 'Receita Estimada',
            'headcount': 'Quantidade de Funcionários',
            'entrevistas': 'Entrevistas Previstas',
            'contratacoes': 'Contratações Previstas',
            'nps': 'NPS Esperado',
        }
        widgets = {
            'auc': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o AUC esperado...'}),
            'receita': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o valor da receita esperada...'}),
            'headcount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insira o valor esperado...'}),
            'entrevistas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insira o número de entrevistas planejadas...'}),
            'contratacoes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número de contratações esperadas...'}),
            'nps': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o NPS esperado...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if self.fields[field].initial == 0:
                self.fields[field].initial = None


#Criação dos campos do formulário de ações executadas (Head)
class ExecutadoForm(forms.ModelForm):
    class Meta:
        model = Executado
        exclude = ['user', 'month', 'year', 'created_at']
        labels = {
            'auc': 'AUC Realizado',
            'receita': 'Receita Alcançada',
            'headcount': 'Quantidade de Funcionários',
            'entrevistas': 'Entrevistas Realizadas',
            'contratacoes': 'Contratações Realizadas',
            'nps': 'NPS Atingido',
        }
        widgets = {
            'auc': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o AUC alcançado'}),
            'receita': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o valor da receita alcançada...'}),
            'headcount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insira o valor...'}),
            'entrevistas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insira o número de entrevistas realizadas...'}),
            'contratacoes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insira o número de contratações realizadas...'}),
            'nps': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insira o NPS alcançado...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if self.fields[field].initial == 0:
                self.fields[field].initial = None



#Criação dos campos do forulário de captação de clientes (Assessor)
class CaptacaoForm(forms.ModelForm):
    # Add custom fields for currency input
    pl_display = forms.CharField(
        label="Patrimônio Líquido do cliente", 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control money-mask',
            'placeholder': 'R$ 0,00',
            'data-type': 'currency',
            'inputmode': 'decimal'
        })
    )
    planejado_migracao_display = forms.CharField(
        label="Planejado Migração", 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control money-mask',
            'placeholder': 'R$ 0,00',
            'data-type': 'currency',
            'inputmode': 'decimal'
        })
    )
    
    class Meta:
        model = Captacao
        exclude = ['user', 'month', 'year', 'created_at', 'pl', 'planejado_migracao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo',
                'autocomplete': 'name'
            }),
            'origem': forms.Select(attrs={'class': 'form-select'}),
            'acao': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comentario': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Comentários adicionais (opcional)',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        
        # If we have an instance, format the currency values for display
        if instance:
            if hasattr(instance, 'pl') and instance.pl:
                initial['pl_display'] = f"R$ {instance.pl:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            if hasattr(instance, 'planejado_migracao') and instance.planejado_migracao:
                initial['planejado_migracao_display'] = f"R$ {instance.planejado_migracao:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        
        # Make all fields required except comentario
        for field_name, field in self.fields.items():
            if field_name != 'comentario' and field_name != 'pl_display' and field_name != 'planejado_migracao_display':
                field.required = True
            if isinstance(field.widget, forms.Select) and field.initial == 'Não Selecionado':
                field.widget.attrs['class'] += ' is-invalid'
        
        # Make comentario field optional
        self.fields['comentario'].required = False
        self.fields['pl_display'].required = True
        self.fields['planejado_migracao_display'].required = True

    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure no 'Não Selecionado' values are submitted
        for field_name in ['origem', 'acao', 'status']:
            if cleaned_data.get(field_name) == 'Não Selecionado':
                self.add_error(field_name, 'Por favor, selecione uma opção válida.')
        
        # Process currency fields
        for field_name, model_field in [('pl_display', 'pl'), ('planejado_migracao_display', 'planejado_migracao')]:
            value = self.data.get(field_name, '')
            # Garante que value é string antes de usar .strip()
            if isinstance(value, list):
                value = value[0] if value else ''
            # If value is empty or just R$, set to zero
            if not value or value.strip() == 'R$' or value.strip() == 'R$ ,':
                cleaned_data[model_field] = 0.0
                continue
            # Remove currency symbol and whitespace
            value = value.strip().replace('R$', '').strip()
            # Handle empty string after removing R$
            if not value:
                cleaned_data[model_field] = 0.0
                continue
            try:
                # Replace dots (thousand separators) and change comma to decimal point
                if ',' in value and '.' in value:
                    # Brazilian format (1.234,56)
                    value = value.replace('.', '').replace(',', '.')
                elif ',' in value:
                    # Format like 1234,56
                    value = value.replace(',', '.')
                # Convert to float
                float_value = float(value)
                cleaned_data[model_field] = float_value
            except (ValueError, TypeError):
                self.add_error(field_name, 'Informe um número.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set the currency fields from cleaned_data
        if hasattr(self, 'cleaned_data'):
            if 'pl' in self.cleaned_data:
                instance.pl = self.cleaned_data['pl']
            if 'planejado_migracao' in self.cleaned_data:
                instance.planejado_migracao = self.cleaned_data['planejado_migracao']
        
        if commit:
            instance.save()
        
        return instance



#Criação dos campos do formulário de estatísticas individuais (Assessor)
class EstatisticasForm(forms.ModelForm):
    class Meta:
        model = Estatisticas
        exclude = ['user', 'month', 'year', 'created_at', 'descricao_operacao']

        widgets = {
            # Primeira pergunta: apenas Sim e Não
            'efetivou_operacao': forms.RadioSelect(
                choices=[
                    (True, 'Sim'),
                    (False, 'Não'),
                ]
            ),

            # Campo motivo (apenas utilizado internamente)
            'motivo': forms.Textarea(attrs={
                'class': 'form-control', 
                'style': 'display: none;'
            }),
            
            # Campo de comentário opcional
            'comentario': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Comentários adicionais (opcional)',
                'rows': 3
            }),

            # Campos subsequentes usando Select para melhor UX
            'rv': forms.Select(choices=[(True, 'Sim'), (False, 'Não'), (None, 'Não selecionado')], attrs={'class': 'form-select'}),
            'cambio': forms.Select(choices=[(True, 'Sim'), (False, 'Não'), (None, 'Não selecionado')], attrs={'class': 'form-select'}),
            'seguros': forms.Select(choices=[(True, 'Sim'), (False, 'Não'), (None, 'Não selecionado')], attrs={'class': 'form-select'}),
            'consorcio': forms.Select(choices=[(True, 'Sim'), (False, 'Não'), (None, 'Não selecionado')], attrs={'class': 'form-select'}),
            'corporate': forms.Select(choices=[(True, 'Sim'), (False, 'Não'), (None, 'Não selecionado')], attrs={'class': 'form-select'}),
            'expansao': forms.Select(choices=[(True, 'Sim'), (False, 'Não'), (None, 'Não selecionado')], attrs={'class': 'form-select'}),
            'banking': forms.Select(choices=[(True, 'Sim'), (False, 'Não'), (None, 'Não selecionado')], attrs={'class': 'form-select'}),
            'advisory': forms.Select(choices=[(True, 'Sim'), (False, 'Não'), (None, 'Não selecionado')], attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Garante que a primeira pergunta seja obrigatória
        self.fields['efetivou_operacao'].required = True

        # Torna os campos de quantidade não obrigatórios
        for field_name in ['qtd_rv', 'qtd_cambio', 'qtd_seguros', 'qtd_consorcio', 
                          'qtd_corporate', 'qtd_expansao', 'qtd_banking', 'qtd_advisory']:
            if field_name in self.fields:
                self.fields[field_name].required = False
                
        # Make comentario field optional
        self.fields['comentario'].required = False

    def clean(self):
        cleaned_data = super().clean()
        efetivou_operacao = cleaned_data.get('efetivou_operacao')
        
        if efetivou_operacao is None:
            self.add_error('efetivou_operacao', 'Este campo é obrigatório.')
            
        # Se não efetivou operação, verifica se há motivo
        if efetivou_operacao is False and not cleaned_data.get('motivo'):
            motivo_nao = self.data.get('motivo_nao')
            if not motivo_nao:
                self.add_error('efetivou_operacao', 'Se não efetivou operação, informe o motivo.')
            else:
                cleaned_data['motivo'] = motivo_nao
                
        # Se efetivou operação, verifica se alguma área foi selecionada
        if efetivou_operacao is True:
            area_selected = False
            boolean_fields = ['rv', 'cambio', 'seguros', 'consorcio', 'corporate', 'expansao', 'banking', 'advisory']
            
            # Verifica se alguma área foi selecionada como True
            for field in boolean_fields:
                if cleaned_data.get(field) is True:
                    area_selected = True
                    break
            
            if not area_selected:
                self.add_error('efetivou_operacao', 'Se efetivou operação, selecione pelo menos uma área.')
            
            # Verifica se todas as áreas têm um valor explícito (True ou False, não None)
            for field in boolean_fields:
                if cleaned_data.get(field) is None:
                    self.add_error(field, 'Por favor, selecione "Sim" ou "Não" para esta área.')
                
        return cleaned_data

# --- Area-specific Planejado and Executado Forms (updated: no headcount) ---

# Expansão
class PlanejadoExpansaoForm(forms.ModelForm):
    nps = forms.IntegerField(
        label='NPS Esperado',
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o NPS esperado...'})
    )
    class Meta:
        model = Planejado
        fields = ['entrevistas', 'contratacoes', 'nps']
        labels = {
            'entrevistas': 'Entrevistas Previstas',
            'contratacoes': 'Contratações Previstas',
            'nps': 'NPS Esperado',
        }
        widgets = {
            'entrevistas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insira o número de entrevistas planejadas...'}),
            'contratacoes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número de contratações esperadas...'}),
            'nps': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o NPS esperado...'}),
        }

class ExecutadoExpansaoForm(forms.ModelForm):
    nps = forms.IntegerField(
        label='NPS Atingido',
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o NPS alcançado...'})
    )
    class Meta:
        model = Executado
        fields = ['entrevistas', 'contratacoes', 'nps']
        labels = {
            'entrevistas': 'Entrevistas Realizadas',
            'contratacoes': 'Contratações Realizadas',
            'nps': 'NPS Atingido',
        }
        widgets = {
            'entrevistas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insira o número de entrevistas realizadas...'}),
            'contratacoes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insira o número de contratações realizadas...'}),
            'nps': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insira o NPS alcançado...'}),
        }

# Renda Variável
class PlanejadoRendaVariavelForm(forms.ModelForm):
    receita = forms.CharField(
        label='Receita Estimada',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite a receita estimada...'}),
        required=True
    )
    volume_ofertas = forms.CharField(
        label='Volume em Ofertas Públicas Esperado',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume alocado em ofertas públicas...'}),
        required=True
    )
    class Meta:
        model = Planejado
        fields = ['receita', 'cpfs_operados', 'volume_ofertas']
        labels = {
            'receita': 'Receita Estimada',
            'cpfs_operados': 'CPFs Esperados',
            'volume_ofertas': 'Volume em Ofertas Públicas Esperado',
        }
        widgets = {
            'cpfs_operados': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número de CPFs operados...'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance is not None:
            receita_val = getattr(instance, 'receita', None)
            if receita_val is None or receita_val == 0:
                self.fields['receita'].initial = ''
        else:
            self.fields['receita'].initial = ''
        self.fields['receita'].required = True
        self.fields['cpfs_operados'].required = True
        self.fields['volume_ofertas'].required = True
    def clean_receita(self):
        raw = self.cleaned_data['receita']
        val = parse_brl_currency(raw)
        if val is None:
            raise forms.ValidationError('Informe um número válido no formato 0,00')
        return val
    def clean_volume_ofertas(self):
        return parse_brl_currency(self.cleaned_data['volume_ofertas'])
    def clean(self):
        cleaned_data = super().clean()
        missing = []
        for field in ['receita', 'cpfs_operados', 'volume_ofertas']:
            value = cleaned_data.get(field)
            if value in [None, '', 0]:
                missing.append(self.fields[field].label)
        if missing:
            raise forms.ValidationError(f'Todos os campos são obrigatórios: {", ".join(missing)}')
        return cleaned_data

class ExecutadoRendaVariavelForm(forms.ModelForm):
    receita = forms.CharField(
        label='Receita Alcançada',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite a receita alcançada...'}),
        required=True
    )
    volume_ofertas = forms.CharField(
        label='Volume em Ofertas Públicas Atingido',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume alocado em ofertas públicas...'}),
        required=True
    )
    class Meta:
        model = Executado
        fields = ['receita', 'cpfs_operados', 'volume_ofertas']
        labels = {
            'receita': 'Receita Alcançada',
            'cpfs_operados': 'CPFs Operados',
            'volume_ofertas': 'Volume em Ofertas Públicas Atingido',
        }
        widgets = {
            'receita': forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite a receita alcançada...'}),
            'cpfs_operados': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número de CPFs operados...'}),
            'volume_ofertas': forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume alocado em ofertas públicas...'}),
        }
    def clean_receita(self):
        return parse_brl_currency(self.cleaned_data['receita'])
    def clean_volume_ofertas(self):
        return parse_brl_currency(self.cleaned_data['volume_ofertas'])

# Câmbio
class PlanejadoCambioForm(forms.ModelForm):
    receita = forms.CharField(
        label='Receita Estimada',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite a receita estimada...'})
    )
    volume_operado = forms.CharField(
        label='Volume estimado a ser Operado (R$)',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume operado...'})
    )
    class Meta:
        model = Planejado
        fields = ['receita', 'volume_operado', 'assessores_ativos']
        labels = {
            'receita': 'Receita Estimada',
            'volume_operado': 'Volume estimado a ser Operado (R$)',
            'assessores_ativos': 'Quantidade de Assessores que irão operar',
        }
        widgets = {
            'assessores_ativos': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de assessores que operaram...'}),
        }
    def clean_receita(self):
        return parse_brl_currency(self.cleaned_data['receita'])
    def clean_volume_operado(self):
        return parse_brl_currency(self.cleaned_data['volume_operado'])

class ExecutadoCambioForm(forms.ModelForm):
    receita = forms.CharField(
        label='Receita Alcançada',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite a receita alcançada...'})
    )
    volume_operado = forms.CharField(
        label='Volume Operado (R$)',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume operado...'})
    )
    class Meta:
        model = Executado
        fields = ['receita', 'volume_operado', 'assessores_ativos']
        labels = {
            'receita': 'Receita Alcançada',
            'volume_operado': 'Volume Operado',
            'assessores_ativos': 'Quantidade de assessores que operaram',
        }
        widgets = {
            'assessores_ativos': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de assessores que operaram...'}),
        }
    def clean_receita(self):
        return parse_brl_currency(self.cleaned_data['receita'])
    def clean_volume_operado(self):
        return parse_brl_currency(self.cleaned_data['volume_operado'])

# Seguro
class PlanejadoSegurosForm(forms.ModelForm):
    volume_pa = forms.CharField(
        label='Volume de PA Planejado',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume de PA...'})
    )
    class Meta:
        model = Planejado
        fields = ['qtd_reunioes', 'qtd_seguros', 'volume_pa']
        labels = {
            'qtd_reunioes': 'Quantidade de Reuniões Planejadas',
            'qtd_seguros': 'Quantidade de Seguros Planejados',
            'volume_pa': 'Volume de PA Planejado',
        }
        widgets = {
            'qtd_reunioes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de reuniões...'}),
            'qtd_seguros': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de seguros realizados...'}),
        }
    def clean_volume_pa(self):
        return parse_brl_currency(self.cleaned_data['volume_pa'])

class ExecutadoSegurosForm(forms.ModelForm):
    volume_pa = forms.CharField(
        label='Volume de PA Realizado',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume de PA...'})
    )
    class Meta:
        model = Executado
        fields = ['qtd_reunioes', 'qtd_seguros', 'volume_pa']
        labels = {
            'qtd_reunioes': 'Quantidade de Reuniões Realizadas',
            'qtd_seguros': 'Quantidade de Seguros Realizados',
            'volume_pa': 'Volume de PA Realizado',
        }
        widgets = {
            'qtd_reunioes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de reuniões...'}),
            'qtd_seguros': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de seguros realizados...'}),
        }
    def clean_volume_pa(self):
        return parse_brl_currency(self.cleaned_data['volume_pa'])

# Corporate
class PlanejadoCorporateForm(forms.ModelForm):
    volume_credito = forms.CharField(
        label= 'Volume de Liberação de Crédito Planejado (R$)',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume de crédito...'})
    )
    class Meta:
        model = Planejado
        fields = ['volume_credito', 'qtd_reunioes']
        labels = {
            'volume_credito': 'Volume de Liberação de Crédito Planejado (R$)',
            'qtd_reunioes': 'Quantidade de Reuniões Planejadas',
        }
        widgets = {
            'qtd_reunioes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de reuniões...'}),
        }
    def clean_volume_credito(self):
        return parse_brl_currency(self.cleaned_data['volume_credito'])

class ExecutadoCorporateForm(forms.ModelForm):
    volume_credito = forms.CharField(
        label= 'Volume de Liberação de Crédito Realizado (R$)',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume de crédito...'})
    )
    class Meta:
        model = Executado
        fields = ['volume_credito', 'qtd_reunioes']
        labels = {
            'volume_credito': 'Volume de Liberação de Crédito Realizado (R$)',
            'qtd_reunioes': 'Quantidade de Reuniões Realizadas',
        }
        widgets = {
            'qtd_reunioes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de reuniões...'}),
        }
    def clean_volume_credito(self):
        return parse_brl_currency(self.cleaned_data['volume_credito'])

# Banking
class PlanejadoBankingForm(forms.ModelForm):
    principalidade = forms.CharField(
        label='Principalidade Planejada',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite a principalidade...'})
    )
    cartoes_emitidos = forms.CharField(
        label='Emissões de Cartões de Crédito Planejadas',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número de Emissões de Cartões de Crédito Planejadas'}),
    )
    class Meta:
        model = Planejado
        fields = ['principalidade', 'cartoes_emitidos']
        labels = {
            'principalidade': 'Principalidade Planejada',
            'cartoes_emitidos': 'Emissões de Cartões de Crédito Planejadas',
        }
    def clean_principalidade(self):
        return parse_brl_currency(self.cleaned_data['principalidade'])
    def clean_cartoes_emitidos(self):
        return parse_brl_currency(self.cleaned_data['cartoes_emitidos'])

class ExecutadoBankingForm(forms.ModelForm):
    principalidade = forms.CharField(
        label='Principalidade Realizada',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite a principalidade...'})
    )
    cartoes_emitidos = forms.CharField(
        label='Emissões de Cartões de Crédito Realizadas',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número de Emissões de Cartões de Crédito Realizadas'}),
    )
    class Meta:
        model = Executado
        fields = ['principalidade', 'cartoes_emitidos']
        labels = {
            'principalidade': 'Principalidade Realizada',
            'cartoes_emitidos': 'Emissões de Cartões de Crédito Realizadas',
        }
    def clean_principalidade(self):
        return parse_brl_currency(self.cleaned_data['principalidade'])
    def clean_cartoes_emitidos(self):
        return parse_brl_currency(self.cleaned_data['cartoes_emitidos'])

# Marketing
class PlanejadoMarketingForm(forms.ModelForm):
    percentual_pl_credito = forms.FloatField(
        label='Percentual do PL em Crédito Corporativo Planejado',
        min_value=0.0,
        max_value=100.0,
        widget=forms.TextInput(attrs={
            'class': 'form-control percent-mask',
            'data-type': 'percent',
            'placeholder': 'Digite o percentual do PL em Crédito Corporativo...'
        })
    )
    captacao_mesa = forms.CharField(
        label='Captação Mesa Trader (AUC) Esperado',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite a captação mesa trader...'})
    )
    class Meta:
        model = Planejado
        fields = ['seguidores', 'interacoes', 'leads_sociais', 'percentual_pl_credito', 'captacao_mesa']
        labels = {
            'seguidores': 'Quantidade de Seguidores Esperados',
            'interacoes': 'Interações em Posts e Stories Esperado',
            'leads_sociais': 'Leads Captados via Rede Sociais Esperado',
            'captacao_mesa': 'Captação Mesa Trader (AUC) Esperado',
        }
        widgets = {
            'seguidores': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de seguidores...'}),
            'interacoes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número de interações...'}),
            'leads_sociais': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número de leads...'}),
        }
    def clean_percentual_pl_credito(self):
        return parse_brl_currency(self.cleaned_data['percentual_pl_credito'])
    def clean_captacao_mesa(self):
        return parse_brl_currency(self.cleaned_data['captacao_mesa'])

class ExecutadoMarketingForm(forms.ModelForm):
    percentual_pl_credito = forms.FloatField(
        label='Percentual do PL em Crédito Corporativo Realizado',
        min_value=0.0,
        max_value=100.0,
        widget=forms.TextInput(attrs={
            'class': 'form-control percent-mask',
            'data-type': 'percent',
            'placeholder': 'Digite o percentual do PL em Crédito Corporativo...'
        })
    )
    captacao_mesa = forms.CharField(
        label='Captação Mesa Trader (AUC) Realizada',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite a captação mesa trader...'})
    )
    class Meta:
        model = Executado
        fields = ['seguidores', 'interacoes', 'leads_sociais', 'percentual_pl_credito', 'captacao_mesa']
        labels = {
            'seguidores': 'Quantidade de Seguidores Realizadas',
            'interacoes': 'Interações em Posts e Stories Realizadas',
            'leads_sociais': 'Leads Captados via Rede Sociais Realizadas',
            'percentual_pl_credito': '% do PL em Crédito Corporativo Realizado',
            'captacao_mesa': 'Captação Mesa Trader (AUC) Realizada',
        }
        widgets = {
            'seguidores': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de seguidores...'}),
            'interacoes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número de interações...'}),
            'leads_sociais': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número de leads...'}),
        }
    def clean_percentual_pl_credito(self):
        return parse_brl_currency(self.cleaned_data['percentual_pl_credito'])
    def clean_captacao_mesa(self):
        return parse_brl_currency(self.cleaned_data['captacao_mesa'])

# Consórcio
class PlanejadoConsorcioForm(forms.ModelForm):
    volume_financeiro = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume financeiro...'})
    )

    class Meta:
        model = Planejado
        fields = ['qtd_reunioes', 'qtd_consorcios', 'volume_financeiro']
        labels = {
            'qtd_reunioes': 'Quantidade de Reuniões Planejadas',
            'qtd_consorcios': 'Quantidade de Consórcios Planejados',
            'volume_financeiro': 'Volume Financeiro Planejado',
        }
        widgets = {
            'qtd_reunioes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de reuniões...'}),
            'qtd_consorcios': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de consórcios realizados...'}),
        }
    def clean_volume_financeiro(self):
        return parse_brl_currency(self.cleaned_data['volume_financeiro'])

class ExecutadoConsorcioForm(forms.ModelForm):
    volume_financeiro = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume financeiro...'})
    )
    class Meta:
        model = Executado
        fields = ['qtd_reunioes', 'qtd_consorcios', 'volume_financeiro']
        labels = {
            'qtd_reunioes': 'Quantidade de Reuniões Realizadas',
            'qtd_consorcios': 'Quantidade de Consórcios Realizados',
            'volume_financeiro': 'Volume Financeiro Realizado',
        }
        widgets = {
            'qtd_reunioes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de reuniões...'}),
            'qtd_consorcios': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Digite a quantidade de consórcios realizados...'}),
        }
    def clean_volume_financeiro(self):
        return parse_brl_currency(self.cleaned_data['volume_financeiro'])

# Advisory
class PlanejadoAdvisoryForm(forms.ModelForm):
    pl_liquidez = forms.CharField(
        label='PL em Liquidez Planejado',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o PL em liquidez...'})
    )
    percentual_pl_liquidez = forms.FloatField(
        label='Percentual do PL em Liquidez Planejado',
        min_value=0.0,
        max_value=100.0,
        widget=forms.TextInput(attrs={
            'class': 'form-control percent-mask',
            'data-type': 'percent',
            'placeholder': 'Digite o percentual do PL em liquidez...'
        })
    )
    volume_credito = forms.CharField(
        label='Volume Financeiro em Crédito Corporativo Esperado',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume financeiro em crédito corporativo...'})
    )
    percentual_pl_credito = forms.FloatField(
        label='Percentual do PL em Crédito Corporativo Esperado',
        min_value=0.0,
        max_value=100.0,
        widget=forms.TextInput(attrs={'class': 'form-control percent-mask', 'data-type': 'percent', 'placeholder': 'Digite o percentual do PL em crédito corporativo...'})
    )
    ofertas_publicas = forms.CharField(
        label='Quantidade de Ofertas Públicas Esperadas',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite as ofertas públicas...'})
    )
    class Meta:
        model = Planejado
        fields = ['pl_liquidez', 'percentual_pl_liquidez', 'volume_credito', 'percentual_pl_credito', 'ofertas_publicas']
        labels = {
            'pl_liquidez': 'PL em Liquidez Planejado',
            'percentual_pl_liquidez': '% do PL em Liquidez Planejado',
            'volume_credito': 'Volume Financeiro em Crédito Corporativo Esperado',
            'percentual_pl_credito': '% do PL em Crédito Corporativo Esperado',
            'ofertas_publicas': 'Ofertas Públicas Esperadas',
        }
    def clean_pl_liquidez(self):
        return parse_brl_currency(self.cleaned_data['pl_liquidez'])
    def clean_percentual_pl_liquidez(self):
        return parse_percent(self.cleaned_data['percentual_pl_liquidez'])
    def clean_volume_credito(self):
        return parse_brl_currency(self.cleaned_data['volume_credito'])
    def clean_percentual_pl_credito(self):
        return parse_percent(self.cleaned_data['percentual_pl_credito'])
    def clean_ofertas_publicas(self):
        return parse_brl_currency(self.cleaned_data['ofertas_publicas'])

class ExecutadoAdvisoryForm(forms.ModelForm):
    pl_liquidez = forms.CharField(
        label='PL em Liquidez Realizado',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o PL em liquidez...'})
    )
    percentual_pl_liquidez = forms.FloatField(
        label='Percentual do PL em Liquidez Realizado',
        min_value=0.0,
        max_value=100.0,
        widget=forms.TextInput(attrs={
            'class': 'form-control percent-mask',
            'data-type': 'percent',
            'placeholder': 'Digite o percentual do PL em liquidez...'
        })
    )
    volume_credito = forms.CharField(
        label='Volume Financeiro em Crédito Corporativo Realizado',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite o volume financeiro em crédito corporativo...'})
    )
    percentual_pl_credito = forms.FloatField(
        label='Percentual do PL em Crédito Corporativo Realizado',
        min_value=0.0,
        max_value=100.0,
        widget=forms.TextInput(attrs={'class': 'form-control percent-mask', 'data-type': 'percent', 'placeholder': 'Digite o percentual do PL em crédito corporativo...'})
    )
    ofertas_publicas = forms.CharField(
        label='Quantidade de Ofertas Públicas Realizadas',
        widget=forms.TextInput(attrs={'class': 'form-control money-mask', 'data-type': 'currency', 'placeholder': 'Digite as ofertas públicas...'})
    )
    class Meta:
        model = Executado
        fields = ['pl_liquidez', 'percentual_pl_liquidez', 'volume_credito', 'percentual_pl_credito', 'ofertas_publicas']
        labels = {
            'pl_liquidez': 'PL em Liquidez Realizado',
            'percentual_pl_liquidez': '% do PL em Liquidez Realizado',
            'volume_credito': 'Volume Financeiro em Crédito Corporativo Realizado',
            'percentual_pl_credito': '% do PL em Crédito Corporativo Realizado',
            'ofertas_publicas': 'Ofertas Públicas Realizadas',
        }
    def clean_pl_liquidez(self):
        return parse_brl_currency(self.cleaned_data['pl_liquidez'])
    def clean_percentual_pl_liquidez(self):
        return parse_percent(self.cleaned_data['percentual_pl_liquidez'])
    def clean_volume_credito(self):
        return parse_brl_currency(self.cleaned_data['volume_credito'])
    def clean_percentual_pl_credito(self):
        return parse_percent(self.cleaned_data['percentual_pl_credito'])
    def clean_ofertas_publicas(self):
        return parse_brl_currency(self.cleaned_data['ofertas_publicas'])

import re
from decimal import Decimal

def parse_brl_currency(value):
    """Converte string tipo 'R$ 1.234.567,89' para Decimal ou None se vazio."""
    
    # Trata None ou campos vazios
    if value in [None, "", "R$", "R$ ,", "R$ ,00"]:
        return None

    # Se já for Decimal, retorna
    if isinstance(value, Decimal):
        return value

    # Se for float ou int, converte direto para Decimal
    if isinstance(value, (float, int)):
        return Decimal(str(value))

    # Agora garante que é string e trata como moeda brasileira
    value = str(value).strip()
    value = re.sub(r'[^\d,]', '', value)  # remove R$, pontos e espaços
    value = value.replace('.', '').replace(',', '.')  # pt-BR → en-US

    try:
        return Decimal(value)
    except Exception:
        return None


# Função utilitária para parsear porcentagem
def parse_percent(value):
    """Converte '12,5%' ou '12.5' para Decimal('12.5')"""
    if not value:
        return None
    value = str(value).replace('%', '').replace(',', '.').strip()
    try:
        return Decimal(value)
    except Exception:
        raise forms.ValidationError('Informe um percentual válido, ex: 12,5')


class FinanceForm(forms.ModelForm):
    class Meta:
        model = FinanceHistory
        fields = ['receita_pj2', 'receita_pj1_planejado', 'receita_pj2_planejado']
        labels = {
            'receita_pj2': 'Receita PJ2 Executado',
            'receita_pj1_planejado': 'Receita PJ1 Planejado',
            'receita_pj2_planejado': 'Receita PJ2 Planejado',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply currency widget to all fields
        for field in self.fields.values():
            field.widget = forms.TextInput(attrs={
                'class': 'form-control money-mask',
                'data-type': 'currency',
                'placeholder': 'R$ 0,00'
            })

    def clean(self):
        cleaned_data = super().clean()
        
        # Convert all currency fields from string to Decimal
        for field_name in self.fields:
            if field_name in cleaned_data:
                value = cleaned_data[field_name]
                if isinstance(value, str):
                    cleaned_data[field_name] = parse_brl_currency(value) or Decimal('0')

        return cleaned_data



