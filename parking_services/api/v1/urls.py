from parking_services.api.v1 import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter(trailing_slash=False)
router.register('parking_section', views.ParkingSectionViewSet, basename='parking_section')
router.register('parking_state', views.ParkingStateViewSet, basename='parking_state')


urlpatterns = router.urls
