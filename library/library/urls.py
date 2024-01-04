from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static 
from core.views import HomeView
from . import views 

urlpatterns = [
    path('', HomeView.as_view(), name='home'),  
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('transaction/', include('transaction.urls')),
    path('', views.home, name="homepage"),  
    path('book/', views.book, name="book"),
    path('it/', views.it, name='it'),
    path('history/', views.history, name='history'),
    path('drama/', views.drama, name='drama'),
    path('all/', views.all, name='ALL'),
    # path('add_car/<int:id>/', views.add_car, name='add_car'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
