
# subsidy_advisor_project/urls.py - 高機能リダイレクト版
# より洗練されたリダイレクト機能

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Django認証システムのURL
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # アプリケーションのURL
    path('advisor/', include('advisor.urls')),
    
    # ルートURL（'/'）をadvisorにリダイレクト
    # permanent=True は301リダイレクト（SEO向け）
    # permanent=False は302リダイレクト（一時的）
    path('', RedirectView.as_view(url='/advisor/', permanent=False), name='root_redirect'),
]