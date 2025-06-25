from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.conf import settings
from django.utils.text import slugify

class Unidade(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descricao = models.TextField(blank=True)
    roa = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    head = models.OneToOneField('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='unidade_gerenciada')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class Area(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    head = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='areas_gerenciadas')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nome

class ObjetivoAnual(models.Model):
    """
    Model to store annual objectives for users (specifically assessors)
    This is defined by masters for annual planning purposes
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='objetivos_anuais')
    year = models.IntegerField("Ano")
    valor = models.DecimalField("Objetivo Anual (PL)", max_digits=15, decimal_places=2)
    
    # Master who defined this objective
    definido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    related_name='objetivos_definidos', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Objetivo Anual"
        verbose_name_plural = "Objetivos Anuais"
        unique_together = ('user', 'year')
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.year}: {self.valor}"

class ObjetivoUnidade(models.Model):
    """
    Model to store annual AUC objectives for units
    This is defined by masters/admin users for unit planning purposes
    """
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='objetivos_anuais')
    year = models.IntegerField("Ano")
    objetivo_auc = models.DecimalField("Objetivo AUC Anual (R$)", max_digits=15, decimal_places=2)
    
    # Admin user who defined this objective
    definido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    related_name='objetivos_unidade_definidos', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Objetivo de Unidade"
        verbose_name_plural = "Objetivos de Unidade"
        unique_together = ('unidade', 'year')
        
    def __str__(self):
        return f"{self.unidade.nome} - {self.year}: R$ {self.objetivo_auc:,.2f}"

class CustomUser(AbstractUser):
    phone_number = models.CharField("Telefone", max_length=15, blank=True)
    birth_date = models.DateField("Data de Nascimento", null=True, blank=True)
    cge = models.CharField("CGE", max_length=50, blank=True)

    unidade = models.ForeignKey('Unidade', on_delete=models.SET_NULL, null=True, blank=True, related_name='membros')
    # Head users can be linked to areas in two ways:
    # 1. Through the Area.head FK (user.areas_gerenciadas.all()) - This sets the user as head of an area
    # 2. Through this area_ref FK (user.area_ref) - This assigns an area to the user
    # Both associations are checked when determining which areas a head manages
    area_ref = models.ForeignKey('Area', on_delete=models.SET_NULL, null=True, blank=True, related_name='membros')
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinados')

    CARGO_CHOICES = [
        ('master', 'Master'),
        ('head', 'Head de Área'),
        ('assessor', 'Assessor'),
        ('headunidade', 'Head de Unidade'),
    ]

    cargo = models.CharField("Cargo", max_length=20, choices=CARGO_CHOICES, default='assessor', null=False, blank=False,)

    def __str__(self):
        return self.username

    def is_master(self):
        return self.cargo == 'master'

    def is_head(self):
        return self.cargo == 'head'

    def is_assessor(self):
        return self.cargo == 'assessor'
    
    def is_headunidade(self):
        return self.cargo == 'headunidade'

    def get_subordinados(self):
        return self.subordinados.all()
    
    # Modified to only return area_head for non-assessor users
    def get_head_area(self):
        if not self.is_assessor() and self.area_ref:
            return self.area_ref.head
        return None
    
    def get_head_unidade(self):
        if self.unidade:
            return self.unidade.head
        return None

    def get_areas_gerenciadas(self):
        """
        Returns all areas this user is head of
        """
        # Only heads and masters should have managed areas
        if self.is_assessor() or self.is_headunidade():
            return self.areas_gerenciadas.none()
        return self.areas_gerenciadas.all()

#Modelo do formulário de ações planejadas (Head)
class Planejado(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    
    auc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    entrevistas = models.IntegerField(null=True, blank=True)
    contratacoes = models.IntegerField(null=True, blank=True)
    nps = models.IntegerField(null=True, blank=True)
    qtd_reunioes = models.IntegerField(null=True, blank=True)
    qtd_seguros = models.IntegerField(null=True, blank=True)
    volume_pa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    receita = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cpfs_operados = models.IntegerField(null=True, blank=True)
    volume_ofertas = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    volume_operado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    assessores_ativos = models.IntegerField(null=True, blank=True)
    volume_credito = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    principalidade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cartoes_emitidos = models.IntegerField(null=True, blank=True)
    seguidores = models.IntegerField(null=True, blank=True)
    interacoes = models.IntegerField(null=True, blank=True)
    leads_sociais = models.IntegerField(null=True, blank=True)
    percentual_pl_credito = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    captacao_mesa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    qtd_consorcios = models.IntegerField(null=True, blank=True)
    volume_financeiro = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    percentual_atingido = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pace = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pl_liquidez = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    percentual_pl_liquidez = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ofertas_publicas = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'month', 'year')

    def __str__(self):
        return f"Planejado {self.user.username} - {self.month}/{self.year}"


#Modelo do formulário de ações executadas (Head)
class Executado(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()

    auc = models.DecimalField(max_digits=12, decimal_places=2)
    entrevistas = models.IntegerField(null=True, blank=True)
    contratacoes = models.IntegerField(null=True, blank=True)
    nps = models.IntegerField(null=True, blank=True)
    qtd_reunioes = models.IntegerField(null=True, blank=True)
    qtd_seguros = models.IntegerField(null=True, blank=True)
    volume_pa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    receita = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cpfs_operados = models.IntegerField(null=True, blank=True)
    volume_ofertas = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    volume_operado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    assessores_ativos = models.IntegerField(null=True, blank=True)
    volume_credito = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    principalidade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cartoes_emitidos = models.IntegerField(null=True, blank=True)
    seguidores = models.IntegerField(null=True, blank=True)
    interacoes = models.IntegerField(null=True, blank=True)
    leads_sociais = models.IntegerField(null=True, blank=True)
    percentual_pl_credito = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    captacao_mesa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    qtd_consorcios = models.IntegerField(null=True, blank=True)
    volume_financeiro = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    percentual_atingido = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pace = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pl_liquidez = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    percentual_pl_liquidez = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ofertas_publicas = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'month', 'year')

    def __str__(self):
        return f"Executado {self.user.username} - {self.month}/{self.year}"
    

#Modelo do formulário de captação de clientes (Assessor)
class Captacao(models.Model):
    ORIGEM_CHOICES = [
        ('Família', 'Família'),
        ('Relacionamento', 'Relacionamento'),
        ('Indicação', 'Indicação'),
        ('Redes Sociais', 'Redes Sociais'),
        ('Palestras', 'Palestras'),
        ('Alunos', 'Alunos'),
        ('Já é cliente', 'Já é cliente'),
        ('Não Selecionado', 'Não Selecionado'),
    ]

    ACAO_CHOICES = [
        ('Marcar 1ª Reunião', 'Marcar 1ª Reunião'),
        ('Marcar 2ª Reunião', 'Marcar 2ª Reunião'),
        ('Abrir conta', 'Abrir conta'),
        ('Pedir TED', 'Pedir TED'),
        ('Trocar Assessoria', 'Trocar Assessoria'),
        ('Fazer STVM', 'Fazer STVM'),
        ('Não Selecionado', 'Não Selecionado'),
    ]

    STATUS_CHOICES = [
        ('Quente', 'Quente'),
        ('Morno', 'Morno'),
        ('Frio', 'Frio'),
        ('Não Selecionado', 'Não Selecionado'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()

    nome = models.CharField("Nome do cliente", max_length=255)
    pl = models.DecimalField("Patrimônio Líquido do cliente", max_digits=20, decimal_places=2, default=0)
    planejado_migracao = models.DecimalField("Planejado Migração", max_digits=20, decimal_places=2, default=0)
    origem = models.CharField("Origem", max_length=50, choices=ORIGEM_CHOICES, default='Não Selecionado')
    acao = models.CharField("Ação", max_length=50, choices=ACAO_CHOICES, default='Não Selecionado')
    status = models.CharField("Status", max_length=50, choices=STATUS_CHOICES, default='Não Selecionado')
    comentario = models.TextField("Comentários (opcional)", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} - {self.month}/{self.year} - {self.status}"


#Modelo do formulário de estatísticas individuais (Assessor)
class Estatisticas(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()

    efetivou_operacao = models.BooleanField("Efetivou alguma operação/Indicação?", null=True, blank=True)
    descricao_operacao = models.TextField("Com quais áreas?", blank=True)  # Deprecated field, kept for backward compatibility
    motivo = models.TextField("Motivo de não ter feito operação", blank=True)
    comentario = models.TextField("Comentários (opcional)", blank=True)

    rv = models.BooleanField("RV", null=True, blank=True)
    qtd_rv = models.PositiveIntegerField("Quantidade de operações RV", default=0, null=False)

    cambio = models.BooleanField("Câmbio", null=True, blank=True)
    qtd_cambio = models.PositiveIntegerField("Quantidade de operações Câmbio", default=0, null=False)

    seguros = models.BooleanField("Seguros", null=True, blank=True)
    qtd_seguros = models.PositiveIntegerField("Quantidade de operações Seguros", default=0, null=False)

    consorcio = models.BooleanField("Consórcio", null=True, blank=True)
    qtd_consorcio = models.PositiveIntegerField("Quantidade de operações Consórcio", default=0, null=False)

    corporate = models.BooleanField("Corporate", null=True, blank=True)
    qtd_corporate = models.PositiveIntegerField("Quantidade de operações Corporate", default=0, null=False)

    expansao = models.BooleanField("Expansão", null=True, blank=True)
    qtd_expansao = models.PositiveIntegerField("Quantidade de operações Expansão", default=0, null=False)

    banking = models.BooleanField("Banking", null=True, blank=True)
    qtd_banking = models.PositiveIntegerField("Quantidade de operações Banking", default=0, null=False)

    advisory = models.BooleanField("Advisory", null=True, blank=True)
    qtd_advisory = models.PositiveIntegerField("Quantidade de operações Advisory", default=0, null=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'month', 'year')

    def __str__(self):
        return f"Estatísticas - {self.user.username} ({self.month}/{self.year})"



#Modelo da função de agendamento dos períodos dos formulários
class AgendamentoMensal(models.Model):
    FORMULARIOS = [
        ('Planejado', 'Planejado'),
        ('Executado', 'Executado'),
        ('Estatísticas', 'Estatísticas'),
    ]

    nome = models.CharField(max_length=20, choices=FORMULARIOS)
    mes = models.IntegerField()
    ano = models.IntegerField()
    dia_inicio = models.IntegerField()
    dia_fim = models.IntegerField()
    # Novos campos
    dias_especificos = models.CharField(max_length=200, blank=True, help_text="Dias específicos do mês separados por vírgula (ex: 1,5,10,15,20,25)")
    recorrente = models.BooleanField(default=True, help_text="Se marcado, este agendamento será automaticamente criado para o próximo mês")

    class Meta:
        unique_together = ('nome', 'mes', 'ano')
        verbose_name = "Agendamento Mensal"
        verbose_name_plural = "Agendamentos Mensais"

    def __str__(self):
        if self.dias_especificos:
            return f"{self.nome} - {self.mes}/{self.ano} (dias: {self.dias_especificos})"
        return f"{self.nome} - {self.mes}/{self.ano} ({self.dia_inicio} a {self.dia_fim})"

    def get_dias_disponiveis(self):
        """Retorna uma lista de dias disponíveis"""
        if self.dias_especificos:
            try:
                return [int(dia.strip()) for dia in self.dias_especificos.split(',') if dia.strip().isdigit()]
            except (ValueError, TypeError):
                pass
        return list(range(self.dia_inicio, self.dia_fim + 1))

    def esta_disponivel_hoje(self):
        """Verifica se o formulário está disponível no dia atual"""
        today = timezone.now().day
        if self.dias_especificos:
            try:
                dias = [int(dia.strip()) for dia in self.dias_especificos.split(',') if dia.strip().isdigit()]
                return today in dias
            except (ValueError, TypeError):
                pass
        return self.dia_inicio <= today <= self.dia_fim


#ALERTA DE CLIENTE DUPLICADO
class AlertaDuplicado(models.Model):
    assessor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Alerta - {self.nome}'
    
#CÓDIGO DE EDIÇÃO MASTER
class CodigoEdicao(models.Model):
    codigo = models.CharField(max_length=100)

    def __str__(self):
        return "Código de Edição Master"

    class Meta:
        verbose_name = "Código de Edição"
        verbose_name_plural = "Código de Edição"