from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index_alias'),
    path('logout/', views.logout_view, name='logout_alias'),
    path('menu/', views.menu, name='menu_alias'),
    path('atrasados/', views.atrasados, name='atrasados_alias'),
    path('chat/', views.chat, name='chat_alias'),
    path('dashboard/', views.metricas, name='metricas_alias'),

    # Integracao via Pandas (CSV in/out)
    path('exportar_livros_csv/', views.exportar_livros_csv, name='exportar_livros_csv_alias'),
    path('importar_livros_csv/', views.importar_livros_csv, name='importar_livros_csv_alias'),

    path('pessoa/', views.pessoa_menu.as_view(), name='pessoa_menu_alias'),
    path('pessoa/list/', views.pessoa_list.as_view(), name='pessoa_list_alias'),
    path('pessoa/create/', views.pessoa_create.as_view(), name='pessoa_create_alias'),
    path('pessoa/update/<int:pk>/', views.pessoa_update.as_view(), name='pessoa_update_alias'),
    path('pessoa/delete/<int:pk>/', views.pessoa_delete.as_view(), name='pessoa_delete_alias'),

    path('livro/', views.livro_menu.as_view(), name='livro_menu_alias'),
    path('livro/list/', views.livro_list.as_view(), name='livro_list_alias'),
    path('livro/create/', views.livro_create.as_view(), name='livro_create_alias'),
    path('livro/detail/<int:pk>/', views.livro_detail.as_view(), name='livro_detail_alias'),
    path('livro/update/<int:pk>/', views.livro_update.as_view(), name='livro_update_alias'),
    path('livro/delete/<int:pk>/', views.livro_delete.as_view(), name='livro_delete_alias'),

    path('emprestimo/', views.emprestimo_menu.as_view(), name='emprestimo_menu_alias'),
    path('emprestimo/list/', views.emprestimo_list.as_view(), name='emprestimo_list_alias'),
    path('emprestimo/create/', views.emprestimo_create.as_view(), name='emprestimo_create_alias'),
    path('emprestimo/update/<int:pk>/', views.emprestimo_update.as_view(), name='emprestimo_update_alias'),
    path('emprestimo/delete/<int:pk>/', views.emprestimo_delete.as_view(), name='emprestimo_delete_alias'),
]
