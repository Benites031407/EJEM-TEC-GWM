from django.urls import path
from . import views
from .views import estatisticas_view, historico_view, login_redirect, validar_codigo
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from main.forms import CustomLoginForm

urlpatterns = [
    path('',auth_views.LoginView.as_view(
            template_name='main/login.html',
            authentication_form=CustomLoginForm
        ),
        name='login'),
    path('redirect/', login_redirect, name='login_redirect'),
    path('home', views.home, name='home'),
    path('estatisticas/', estatisticas_view, name='estatisticas'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/assessor/', views.dashboard_assessor, name='dashboard_assessor'),
    path('planejado/', views.planejado_view, name='planejado'),
    path('executado/', views.executado_view, name='executado'),
    path('captacao/', views.captacao_view, name='captacao'),
    path('historico/', historico_view, name='historico'),
    path('dashboard/master/', views.dashboard_master, name='dashboard_master'),
    path('dashboard/master/area/<slug:area_slug>/', views.dashboard_area, name='dashboard_area'),
    path('unidades/', views.lista_unidades, name='unidades'),
    path('unidades/<slug:slug>/', views.dashboard_unidade, name='dashboard_unidade'),
    path('home/master/', views.home_master, name='home_master'),
    path('home/head/', views.home_head, name='home_head'),
    path('historico/head/', views.historico_head, name='historico_head'),
    path('painel/alertas/', views.painel_alertas_master, name='painel_alertas_master'),
    path('validar-codigo/', views.validar_codigo, name='validar_codigo'),
    path('home/headunidade/', views.home_headunidade, name='home_headunidade'),
    
    # New URLs for Unit Head dashboard functionality
    path('dashboard/headunidade/', views.dashboard_headunidade, name='dashboard_headunidade'),
    path('assessor-monitoring/', views.assessor_monitoring, name='assessor_monitoring'),
    path('assessor-monitoring/<int:assessor_id>/', views.assessor_monitoring, name='assessor_monitoring_detail'),
    
    # Organizational hierarchy views
    path('units/', views.unit_hierarchy_view, name='units_list'),
    path('units/<int:unit_id>/', views.unit_hierarchy_view, name='unit_detail'),
    path('areas/<int:area_id>/', views.area_detail_view, name='area_detail'),
    path('team/', views.team_structure_view, name='my_team'),
    path('team/<int:user_id>/', views.team_structure_view, name='user_team'),
    path('supervisor/', views.my_supervisor_view, name='my_supervisor'),
    
    # API endpoints
    path('api/units/<int:unit_id>/', views.api_unit_structure, name='api_unit_structure'),
    path('api/team/<int:user_id>/', views.api_team_hierarchy, name='api_team_hierarchy'),
    path('unidades/minhas/', views.minhas_unidades, name='minhas_unidades'),

]

