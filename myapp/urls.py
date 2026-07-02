from django.urls import path
from .views import * #Home, register, user_login, user_logout การใช้ * เป็นการเรียกฟังก์ชั่นทั้งหมดในไฟล์นั้นมา ไม่ต้องเรียกใช้ฟังก์ชั่นที่ละตัว
from .views import equipment_toggle_status
from myapp import views

urlpatterns = [
    #path('', Home, name='home'), #localhost:8000
    path('register/', register, name='register'),
    path('', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    #path('table-employee/', table_employee, name='table-employee'),
    #path('detail-job/<int:ID>/', detail_job, name='detail-job'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/api/', dashboard_api, name='dashboard_api'),
    path('boiler/', boiler, name='boiler'),
    path('boiler/operation/add/', boiler_operation_add, name='boiler_operation_add'), 
    path('boiler/yoshimine/add/', yoshimine_operation_add, name='yoshimine_operation_add'),
    path('boiler/banpong1/add/', banpong1_operation_add, name='banpong1_operation_add'),
    path('boiler/chengchen/add/', chengchen_operation_add, name='chengchen_operation_add'),
    path('boiler/takuma/add/', takuma_operation_add, name='takuma_operation_add'),
    path('boiler/banpong2/add/', banpong2_operation_add, name='banpong2_operation_add'),
    path('boiler/operation/', operation_dashboard, name='operation_dashboard'),
    path('boiler/api/history/', boiler_history_api, name='boiler_history_api'),

    path('boiler/export/', boiler_export_csv, name='boiler_export_csv'),
    path('boiler/kpi/add/', boiler_kpi_form, name='boiler_kpi_form'),


    path('maintenance/', maintenance_dashboard, name='maintenance_dashboard'),
    path('maintenance/add/', maintenance_log_add, name='maintenance_log_add'),
    path('maintenance/edit/<int:log_id>/', maintenance_log_edit, name='maintenance_log_edit'),
    path('maintenance/kpi/add/', maintenance_kpi_metric_add, name='maintenance_kpi_metric_add'),
    
    path('mill/', mill, name='mill'),
    path('mill/report/', mill_report, name='mill_report'),
    path('mill/import/', mill_import, name='mill_import'),
    path('mill/api/history/', mill_history_api, name='mill_history_api'),

    path('lathe/', lathe_dashboard, name='lathe_dashboard'),
    path('api/lathe/', lathe_api, name='lathe_api'),

    # Equipment Data
    path('equipment/', equipment_data, name='equipment_data'),
    path('equipment/list/', equipment_list, name='equipment_list'),
    path('equipment/form/', equipment_form, name='equipment_form'),
    path('equipment/form/<path:eq_id>/', equipment_form, name='equipment_form_edit'),
    path('equipment/bom/', equipment_bom, name='equipment_bom'),
    path('equipment/<path:eq_id>/pm/add/',   pm_schedule_add,      name='pm_schedule_add'),
    path('equipment/<path:eq_id>/bom/add/', bom_add, name='bom_add'),
    path('equipment/bom/delete/<int:bom_id>/', bom_delete, name='bom_delete'),
    path('pm/<int:pm_id>/edit/',     pm_schedule_edit,     name='pm_schedule_edit'),
    path('pm/<int:pm_id>/complete/', pm_schedule_complete, name='pm_schedule_complete'),
    path('pm/<int:pm_id>/delete/',   pm_schedule_delete,   name='pm_schedule_delete'),
    path('equipment/bom/edit/<int:bom_id>/', bom_edit, name='bom_edit'),
    path('equipment/link/delete/<int:link_id>/', views.equipment_link_delete, name='equipment_link_delete'),
    path('equipment/<path:eq_id>/link/add/', views.equipment_link_add, name='equipment_link_add'),
    path('equipment/<path:eq_id>/pmplan/add/', views.pm_plan_add, name='pm_plan_add'),
    path('equipment/pm/edit/<int:plan_id>/', views.pm_plan_edit, name='pm_plan_edit'),
    path('equipment/pm/delete/<int:plan_id>/', views.pm_plan_delete, name='pm_plan_delete'),
    path('equipment/pm/<int:plan_id>/complete/', views.pm_plan_complete, name='pm_plan_complete'),
    path('equipment/pm/<int:plan_id>/item/add/', views.pm_plan_item_add, name='pm_plan_item_add'),
    path('equipment/pm/item/delete/<int:item_id>/', views.pm_plan_item_delete, name='pm_plan_item_delete'),
    path('equipment/<path:eq_id>/wo/add/', views.work_order_add, name='work_order_add'),
    path('equipment/wo/edit/<int:wo_id>/', views.work_order_edit, name='work_order_edit'),
    path('equipment/wo/delete/<int:wo_id>/', views.work_order_delete, name='work_order_delete'),
    path('equipment/cbm/<path:eq_id>/', equipment_cbm, name='equipment_cbm'),
    path('equipment/cbm-summary/<str:cbm_type>/<path:eq_id>/', cbm_summary, name='cbm_summary'),
    path('equipment/upload_image/<path:eq_id>/', upload_equipment_image, name='upload_equipment_image'),
    path('equipment/<path:eq_id>/toggle_status/', equipment_toggle_status, name='equipment_toggle_status'),
    path('equipment/<path:eq_id>/inline-update/', equipment_inline_update, name='equipment_inline_update'),
    path('equipment/<path:eq_id>/', equipment_data, name='equipment_data_detail'),

    # Path สำหรับ Import Data
    path('import-data/', import_data, name='import_data'),
    path('maintenance/import_csv/', maintenance_import_csv, name='maintenance_import_csv'),
    path('docs/',           doc_repository, name='doc_repository'),
    path('docs/register/', doc_register,   name='doc_register'),
    path('docs/delete/<int:doc_id>/', doc_delete, name='doc_delete'),
    path('webhook/line/', line_webhook, name='line_webhook'),

    # ===== Inventory Module =====
    path('inventory/',                    inventory_dashboard,    name='inventory_dashboard'),
    path('inventory/list/',               inventory_list,         name='inventory_list'),
    path('inventory/item/<int:pk>/',      inventory_stock_card,   name='inventory_stock_card'),
    path('inventory/departments/',        inventory_dept_summary, name='inventory_dept_summary'),
    path('inventory/department/<str:key>/', inventory_dept_detail, name='inventory_dept_detail'),
    path('inventory/transactions/',       inventory_tx_list,      name='inventory_tx_list'),

    # ----- API (fetch + CSRF) -----
    path('api/inventory/checkout/',       api_inventory_checkout, name='api_inventory_checkout'),
    path('api/inventory/receive/',        api_inventory_receive,  name='api_inventory_receive'),
    path('api/inventory/add-item/',       api_inventory_add_item, name='api_inventory_add_item'),

    #EX. path('aboutus', AboutUs)@ localhost:8000/aboutus
]
