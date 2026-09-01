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
    path('api/equipment/by-process/', api_equipment_by_process, name='api_equipment_by_process'),
    path('equipment/<path:eq_id>/inline-update/', equipment_inline_update, name='equipment_inline_update'),
    path('equipment/<path:eq_id>/change-code/', views.equipment_change_code, name='equipment_change_code'),
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
    path('inventory/readiness/',          inventory_readiness_list, name='inventory_readiness_list'),
    path('inventory/readiness/add/',      inventory_readiness_add,  name='inventory_readiness_add'),

    # ----- API (fetch + CSRF) -----
    path('api/inventory/checkout/',       api_inventory_checkout, name='api_inventory_checkout'),
    path('api/inventory/receive/',        api_inventory_receive,  name='api_inventory_receive'),
    path('api/inventory/add-item/',       api_inventory_add_item, name='api_inventory_add_item'),
    path('api/inventory/item/<int:pk>/edit/', api_inventory_update_item, name='api_inventory_update_item'),
    path('api/inventory/item/<int:pk>/delete/', api_inventory_delete_item, name='api_inventory_delete_item'),
    path('api/inventory/item/<int:pk>/upload-image/', upload_inventory_item_image, name='upload_inventory_item_image'),

    # ===== Tools Module (แยกจาก Inventory ทั่วไป) =====
    path('tools/',                        tools_dashboard,        name='tools_dashboard'),
    path('tools/types/',                  tools_type_list,        name='tools_type_list'),
    path('tools/types/<int:pk>/',         tools_type_detail,      name='tools_type_detail'),
    path('tools/unit/<int:pk>/',          tools_unit_detail,      name='tools_unit_detail'),
    path('tools/overdue/',                tools_overdue_list,     name='tools_overdue_list'),
    path('tools/readiness/add/',          tools_readiness_add,    name='tools_readiness_add'),

    path('api/tools/checkout/',           api_tools_checkout,     name='api_tools_checkout'),
    path('api/tools/return/',             api_tools_return,       name='api_tools_return'),
    path('api/tools/type/add/',           api_tools_type_add,     name='api_tools_type_add'),
    path('api/tools/unit/add/',           api_tools_unit_add,     name='api_tools_unit_add'),
    path('api/tools/unit/<int:pk>/edit/', api_tools_unit_update,  name='api_tools_unit_update'),

    # ===== Training / Knowledge Center Module =====
    path('training/',                          training_overview,        name='training_overview'),
    path('training/employees/',                training_employees,           name='training_employees'),
    path('training/employees/add/',            training_employee_add,        name='training_employee_add'),
    path('training/employees/<int:employee_id>/edit/',       training_employee_edit,       name='training_employee_edit'),
    path('training/employees/<int:employee_id>/delete/',     training_employee_delete,     name='training_employee_delete'),
    path('training/employees/<int:employee_id>/reactivate/', training_employee_reactivate, name='training_employee_reactivate'),
    path('training/exam/',                     training_exam,            name='training_exam'),
    path('training/exam/delete/<int:score_id>/', training_exam_delete,   name='training_exam_delete'),
    path('training/matrix/',                   training_matrix,          name='training_matrix'),
    path('training/progress/',                 training_progress,        name='training_progress'),
    path('training/progress/add/',             training_record_add,      name='training_record_add'),
    path('training/progress/delete/<int:record_id>/',  training_record_delete,  name='training_record_delete'),
    path('training/progress/approve/<int:record_id>/', training_record_approve, name='training_record_approve'),
    path('training/courses/',                  training_courses,         name='training_courses'),
    path('training/courses/add/',              training_course_add,      name='training_course_add'),
    path('training/courses/delete/<int:course_id>/', training_course_delete, name='training_course_delete'),
    path('training/profile/<int:employee_id>/',       training_profile,       name='training_profile'),
    path('training/profile/<int:employee_id>/print/', training_profile_print, name='training_profile_print'),
    path('training/certificate/<int:record_id>/',     training_certificate,   name='training_certificate'),
    path('training/career/',                   training_career,          name='training_career'),
    path('training/career/<int:employee_id>/', training_career,          name='training_career_detail'),
    path('training/career/step/add/',                    training_career_step_add,    name='training_career_step_add'),
    path('training/career/step/<int:step_id>/edit/',     training_career_step_edit,   name='training_career_step_edit'),
    path('training/career/step/<int:step_id>/delete/',   training_career_step_delete, name='training_career_step_delete'),
    path('training/gap/',                      training_gap,             name='training_gap'),

    path('training/courses/<int:course_id>/edit/',                training_course_edit,             name='training_course_edit'),
    path('training/courses/<int:course_id>/materials/upload/',    training_course_material_upload,  name='training_course_material_upload'),
    path('training/materials/delete/<int:material_id>/',          training_course_material_delete,  name='training_course_material_delete'),
    path('training/courses/<int:course_id>/quiz/',                training_quiz_manage,             name='training_quiz_manage'),
    path('training/courses/<int:course_id>/quiz/add/',            training_quiz_question_add,       name='training_quiz_question_add'),
    path('training/quiz/<int:question_id>/edit/',                 training_quiz_question_edit,      name='training_quiz_question_edit'),
    path('training/quiz/delete/<int:question_id>/',               training_quiz_question_delete,    name='training_quiz_question_delete'),

    path('training/learn/<int:course_id>/',                       training_learn,                   name='training_learn'),
    path('training/learn/<int:course_id>/<int:employee_id>/',     training_learn_detail,            name='training_learn_detail'),
    path('training/learn/<int:course_id>/<int:employee_id>/exam/', training_exam_take,              name='training_exam_take'),
    path('training/learn/<int:course_id>/<int:employee_id>/exam/result/<int:attempt_id>/', training_exam_result, name='training_exam_result'),

    # ===== Manual Library Module =====
    path('manuals/',                        manual_list,   name='manual_list'),
    path('manuals/add/',                    manual_add,    name='manual_add'),
    path('manuals/<int:manual_id>/',        manual_detail, name='manual_detail'),
    path('manuals/<int:manual_id>/edit/',   manual_edit,   name='manual_edit'),
    path('manuals/<int:manual_id>/delete/', manual_delete, name='manual_delete'),

    # ===== Task Manager Module =====
    path('tasks/',                                     machine_task_list,            name='machine_task_list'),
    path('tasks/add/',                                 machine_task_add,             name='machine_task_add'),
    path('tasks/edit/<int:task_id>/',                  machine_task_edit,            name='machine_task_edit'),
    path('tasks/delete/<int:task_id>/',                machine_task_delete,          name='machine_task_delete'),
    path('tasks/<int:task_id>/',                       machine_task_detail,          name='machine_task_detail'),
    path('tasks/<int:task_id>/vibration/<str:phase>/', machine_task_vibration_save,  name='machine_task_vibration_save'),

    #EX. path('aboutus', AboutUs)@ localhost:8000/aboutus
]
