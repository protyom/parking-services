from django.urls import path, include

urlpatterns = [
    path('v1/', include('parking_services.api.v1.urls'), name='v1'),
]
