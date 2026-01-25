from django.urls import path
from .views import * #Home, register, user_login, user_logout การใช้ * เป็นการเรียกฟังก์ชั่นทั้งหมดในไฟล์นั้นมา ไม่ต้องเรียกใช้ฟังก์ชั่นที่ละตัว

urlpatterns = [
    #path('', Home, name='home'), #localhost:8000
    path('register/', register, name='register'),
    path('', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    #path('table-employee/', table_employee, name='table-employee'),
    #path('detail-job/<int:ID>/', detail_job, name='detail-job'),
    path('dashboard/', dashboard, name='dashboard'),
    path('boiler/', boiler, name='boiler'),
    path('boiler/operation/add/', boiler_operation_add, name='boiler_operation_add'), 
    path('boiler/yoshimine/add/', yoshimine_operation_add, name='yoshimine_operation_add'),
    path('boiler/banpong1/add/', banpong1_operation_add, name='banpong1_operation_add'),
    path('boiler/chengchen/add/', chengchen_operation_add, name='chengchen_operation_add'),
    path('boiler/takuma/add/', takuma_operation_add, name='takuma_operation_add'),
    path('boiler/banpong2/add/', banpong2_operation_add, name='banpong2_operation_add'),
    path('boiler/operation/', operation_dashboard, name='operation_dashboard'),
    path('boiler/kpi/add/', boiler_kpi_form, name='boiler_kpi_form'),


    path('maintenance/', maintenance_dashboard, name='maintenance_dashboard'),
    path('maintenance/add/', maintenance_log_add, name='maintenance_log_add'),
    path('maintenance/kpi/add/', maintenance_kpi_metric_add, name='maintenance_kpi_metric_add'),
    
    path('mill/', mill, name='mill'),
    path('mill/report/', mill_report, name='mill_report'),
    path('mill/import/', mill_import, name='mill_import'),

    # Path สำหรับ Import Data
    path('import-data/', import_data, name='import_data'),

    #EX. path('aboutus', AboutUs)@ localhost:8000/aboutus
]
