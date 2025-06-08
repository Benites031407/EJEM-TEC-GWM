from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from main.forms import CustomLoginForm


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('login/',auth_views.LoginView.as_view(
            template_name='main/login.html',
            authentication_form=CustomLoginForm
        ),
        name='login'
    ),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dash/', include('django_plotly_dash.urls')),

]
