# Agendamento Mensal Automático

## Visão Geral

O sistema de Agendamento Mensal foi aprimorado para permitir:

1. **Agendamentos recorrentes** que são automaticamente replicados a cada mês
2. **Dias específicos** em que os formulários estarão abertos (ao invés de apenas um intervalo)

## Como Configurar Agendamentos

1. Acesse o painel administrativo em `/admin/main/agendamentomensal/`
2. Crie um novo agendamento ou edite um existente:
   - Selecione o **Nome** do formulário (Planejado, Executado, Estatísticas)
   - Configure o **Mês** e **Ano** iniciais
   - Defina o intervalo padrão (**Dia Início** e **Dia Fim**)
   - Marque **Recorrente** para que este agendamento seja criado automaticamente todo mês
   - Opcionalmente, preencha **Dias Específicos** com os dias exatos em que o formulário estará disponível (ex: `1,5,10,15,20,25`)

## Como Funciona

### Dias Específicos

- Se o campo **Dias Específicos** estiver preenchido, apenas nesses dias o formulário estará disponível
- Se o campo estiver vazio, o sistema usará o intervalo definido por **Dia Início** e **Dia Fim**
- No painel de alertas, será exibido "Dias disponíveis: 1,5,10,15,20,25" ou "Prazo: 1 até 10", conforme configurado

### Recorrência Automática

- Agendamentos marcados como **Recorrente** serão automaticamente copiados para o próximo mês
- A cópia é feita através do comando `python manage.py criar_agendamentos_recorrentes`
- Este comando pode ser configurado para execução automática mensal (crontab ou agendador de tarefas)

## Criação Automática Mensal

### Usando o Comando Manualmente

```bash
# Criar agendamentos para o próximo mês
python manage.py criar_agendamentos_recorrentes

# Criar agendamentos para um mês/ano específico
python manage.py criar_agendamentos_recorrentes --mes 6 --ano 2025
```

### Configurando Execução Automática

Para que os agendamentos sejam criados automaticamente no final de cada mês:

#### No Linux (crontab)

```bash
# Editar o crontab
crontab -e

# Adicionar a linha para executar no dia 25 de cada mês às 00:00
0 0 25 * * cd /caminho/para/GWM && source venv/bin/activate && python manage.py criar_agendamentos_recorrentes
```

#### No Windows (Agendador de Tarefas)

1. Abra o Agendador de Tarefas
2. Crie uma nova tarefa para executar o script:
   - Programa: `cmd.exe`
   - Argumentos: `/c cd C:\caminho\para\GWM && venv\Scripts\activate && python manage.py criar_agendamentos_recorrentes`
   - Agendar para executar no dia 25 de cada mês

## Vantagens

- Menos trabalho administrativo (não precisa criar manualmente todo mês)
- Flexibilidade para escolher dias específicos (não apenas intervalos contínuos)
- Visualização clara de quando os formulários estarão disponíveis
- Automatização do processo de criação de períodos de formulário 