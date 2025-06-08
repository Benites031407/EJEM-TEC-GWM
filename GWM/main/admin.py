from django.contrib import admin
from .models import (
    CustomUser, Unidade, Area, 
    AgendamentoMensal, 
    AlertaDuplicado, CodigoEdicao,
    ObjetivoAnual
)
from django.utils import timezone
from django.contrib.admin import SimpleListFilter
from django import forms
from django.shortcuts import render, redirect
from django.urls import path
from django.db import models

class AreaInline(admin.TabularInline):
    model = CustomUser
    fk_name = 'area_ref'
    extra = 1
    fields = ('username', 'first_name', 'last_name', 'cargo')
    readonly_fields = ('username',)
    verbose_name = "Membro da Área"
    verbose_name_plural = "Membros da Área"

@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'get_head_display', 'roa')
    search_fields = ('nome',)
    
    def get_head_display(self, obj):
        return obj.head.get_full_name() if obj.head else "Sem Head"
    get_head_display.short_description = "Head de Unidade"

class SubordinadosInline(admin.TabularInline):
    model = CustomUser
    fk_name = 'supervisor'
    extra = 0
    fields = ('username', 'first_name', 'last_name', 'cargo', 'unidade')
    readonly_fields = ('username',)
    
@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'get_head_display', 'get_members_count')
    search_fields = ('nome',)
    
    def get_head_display(self, obj):
        return obj.head.get_full_name() if obj.head else "Sem Head"
    get_head_display.short_description = "Head de Área"
    
    def get_members_count(self, obj):
        return obj.membros.count()
    get_members_count.short_description = "Total de Membros"
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Limit head choices to users with the 'head' cargo
        if db_field.name == 'head':
            kwargs['queryset'] = CustomUser.objects.filter(
                cargo__in=['head', 'headunidade', 'master']
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'cargo', 'get_unidade_display', 'get_supervisor_display')
    list_filter = ('cargo', 'unidade')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    def get_fieldsets(self, request, obj=None):
        # Set base fieldsets for all users
        fieldsets = [
            (None, {'fields': ('username', 'password')}),
            ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'birth_date', 'cge')}),
            ('Estrutura Organizacional', {'fields': ('cargo', 'unidade', 'supervisor')}),
            ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ]
        
        # Add area_ref field only for users who aren't assessors
        if obj and not obj.is_assessor():
            fieldsets[2][1]['fields'] = ('cargo', 'unidade', 'area_ref', 'supervisor')
            
        return fieldsets
    
    def get_unidade_display(self, obj):
        return obj.unidade.nome if obj.unidade else "Sem Unidade"
    get_unidade_display.short_description = "Unidade"
    
    def get_supervisor_display(self, obj):
        return obj.supervisor.get_full_name() if obj.supervisor else "Sem Supervisor"
    get_supervisor_display.short_description = "Supervisor"
    
    def save_model(self, request, obj, form, change):
        # If user is an assessor, make sure area_ref is None
        if obj.is_assessor():
            obj.area_ref = None
        super().save_model(request, obj, form, change)

@admin.register(AgendamentoMensal)
class AgendamentoMensalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'mes', 'ano', 'get_periodo_display', 'recorrente', 'esta_aberto_hoje')
    list_filter = ('nome', 'mes', 'ano', 'recorrente')
    search_fields = ('nome',)
    fieldsets = (
        (None, {
            'fields': ('nome', 'mes', 'ano')
        }),
        ('Período de Abertura', {
            'fields': ('dia_inicio', 'dia_fim')
        }),
        ('Configuração de Recorrência', {
            'fields': ('recorrente',)
        }),
        ('Dias Específicos', {
            'fields': ('dias_especificos',),
            'description': 'Se preenchido, apenas estes dias específicos estarão abertos no mês selecionado.'
        })
    )
    
    def get_periodo_display(self, obj):
        if obj.dias_especificos:
            return f"Dias: {obj.dias_especificos}"
        return f"{obj.dia_inicio} a {obj.dia_fim}"
    get_periodo_display.short_description = "Período"
    
    def esta_aberto_hoje(self, obj):
        now = timezone.now()
        if obj.mes != now.month or obj.ano != now.year:
            return False
        return obj.esta_disponivel_hoje()
    esta_aberto_hoje.boolean = True
    esta_aberto_hoje.short_description = "Aberto Hoje?"

class YearFilter(SimpleListFilter):
    title = 'Ano'
    parameter_name = 'year'
    
    def lookups(self, request, model_admin):
        current_year = timezone.now().year
        return [(str(y), str(y)) for y in range(current_year-2, current_year+3)]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(year=self.value())
        return queryset

# Define a form for bulk objective setting
class BulkObjetivoAnualForm(forms.Form):
    year = forms.IntegerField(label='Ano', initial=timezone.now().year)
    area = forms.ModelChoiceField(
        label='Área',
        queryset=Area.objects.all(),
        required=False,
        help_text='Filtrar assessores por área'
    )
    unidade = forms.ModelChoiceField(
        label='Unidade',
        queryset=Unidade.objects.all(),
        required=False,
        help_text='Filtrar assessores por unidade'
    )
    valor_padrao = forms.DecimalField(
        label='Valor Padrão (R$)', 
        decimal_places=2, 
        max_digits=15,
        required=False,
        help_text='Se definido, será usado para assessores sem objetivo individual'
    )
    
    def __init__(self, *args, **kwargs):
        assessores = kwargs.pop('assessores', None)
        super(BulkObjetivoAnualForm, self).__init__(*args, **kwargs)
        
        if assessores:
            for assessor in assessores:
                field_name = f'assessor_{assessor.id}'
                self.fields[field_name] = forms.DecimalField(
                    label=f'{assessor.get_full_name()} ({assessor.username})',
                    decimal_places=2,
                    max_digits=15,
                    required=False
                )

@admin.register(ObjetivoAnual)
class ObjetivoAnualAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'valor_formatado', 'definido_por', 'updated_at')
    list_filter = (YearFilter, 'definido_por')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    def valor_formatado(self, obj):
        return f"R$ {obj.valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    valor_formatado.short_description = "Objetivo Anual"
    
    def save_model(self, request, obj, form, change):
        # Set the current user as the definer if not already set
        if not obj.definido_por:
            obj.definido_por = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Masters can see all objectives
        if request.user.is_master() or request.user.is_superuser:
            return qs
        # Other users can only see their own objectives
        return qs.filter(user=request.user)
    
    def has_change_permission(self, request, obj=None):
        # Only masters and superusers can change objectives
        if request.user.is_master() or request.user.is_superuser:
            return True
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only masters and superusers can delete objectives
        if request.user.is_master() or request.user.is_superuser:
            return True
        return False
        
    def has_add_permission(self, request):
        # Only masters and superusers can add objectives
        if request.user.is_master() or request.user.is_superuser:
            return True
        return False
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('definir-objetivos-em-massa/',
                self.admin_site.admin_view(self.bulk_objectives_view),
                name='main_objetivoanual_bulk'),
        ]
        return custom_urls + urls
        
    def bulk_objectives_view(self, request):
        # Base queryset for assessors
        assessores_queryset = CustomUser.objects.filter(cargo='assessor')
        
        if request.method == 'POST':
            # First, get the filter values
            form = BulkObjetivoAnualForm(request.POST)
            if form.is_valid():
                area = form.cleaned_data.get('area')
                unidade = form.cleaned_data.get('unidade')
                
                # Apply filters
                if area:
                    assessores_queryset = assessores_queryset.filter(area_ref=area)
                if unidade:
                    assessores_queryset = assessores_queryset.filter(unidade=unidade)
                
                # Get filtered assessors
                assessores = assessores_queryset.order_by('first_name', 'last_name')
                
                # Create a new form with the filtered assessors
                form = BulkObjetivoAnualForm(request.POST, assessores=assessores)
                
            if form.is_valid():
                year = form.cleaned_data['year']
                valor_padrao = form.cleaned_data['valor_padrao']
                
                # Process each assessor's objetivo
                for assessor in assessores:
                    field_name = f'assessor_{assessor.id}'
                    if field_name in form.cleaned_data and form.cleaned_data[field_name]:
                        # Use the specific value for this assessor
                        valor = form.cleaned_data[field_name]
                        ObjetivoAnual.objects.update_or_create(
                            user=assessor,
                            year=year,
                            defaults={
                                'valor': valor,
                                'definido_por': request.user
                            }
                        )
                    elif valor_padrao:
                        # Use the default value
                        ObjetivoAnual.objects.update_or_create(
                            user=assessor,
                            year=year,
                            defaults={
                                'valor': valor_padrao,
                                'definido_por': request.user
                            }
                        )
                
                self.message_user(request, f"Objetivos definidos com sucesso para o ano {year}!")
                return redirect('..')
            
            # If form is not valid, get all assessors for display
            assessores = assessores_queryset.order_by('first_name', 'last_name')
        else:
            # For GET requests, get all assessors
            assessores = assessores_queryset.order_by('first_name', 'last_name')
            
            # Pre-populate with existing values if any
            current_year = timezone.now().year
            existing_objectives = ObjetivoAnual.objects.filter(year=current_year)
            
            initial_data = {'year': current_year}
            for obj in existing_objectives:
                field_name = f'assessor_{obj.user.id}'
                initial_data[field_name] = obj.valor
                
            # Create form with initial data and all assessors
            form = BulkObjetivoAnualForm(initial=initial_data, assessores=assessores)
        
        # Add a link to this view in the admin list view
        context = {
            'title': 'Definir Objetivos Anuais em Massa',
            'form': form,
            'opts': self.model._meta,
            'assessores': assessores,
        }
        return render(request, 'admin/bulk_objetivo_anual.html', context)
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_bulk_button'] = True
        return super().changelist_view(request, extra_context=extra_context)

# Register remaining models
admin.site.register(AlertaDuplicado)
admin.site.register(CodigoEdicao)