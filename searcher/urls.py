from django.urls import path

from . import views

app_name = 'searcher'
urlpatterns = [
    path('', views.index, name='index'),
    path('results/', views.results, name='results'),
    path('details/<int:pk>', views.details, name='details'),
    path('results/<int:page_order>', views.next_page, name='next_page')
]