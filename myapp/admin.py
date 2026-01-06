from django.contrib import admin
from .models import *
from .models import (
    Job, employee, Profile,
    BoilerOperationLog, YoshimineLog, Banpong1Log, ChengchenLog, TakumaLog, Banpong2Log,
    MaintenanceLog, KPIMetric, BoilerDailyKPI
)
from .models import MillReport

admin.site.register(Job)
admin.site.register(employee)
admin.site.register(Profile)

@admin.register(BoilerOperationLog)
class BoilerOperationLogAdmin(admin.ModelAdmin):
    list_display = ('jt_date', 'jt_time', 'jt_steam_pressure', 'jt_steam_flow', 'jt_temp_steam', 'jt_feed_water_flow', 'jt_temp_deaerator', 'jt_temp_gas_stack', 'jt_ph_boiler')
    list_filter = ('jt_date',)
    search_fields = ('jt_problem_cause',)
    ordering = ('-jt_date', '-jt_time')

# 2.Chengchen Log
@admin.register(ChengchenLog)
class ChengchenLogAdmin(admin.ModelAdmin):
    list_display = ('ch_date', 'ch_time', 'ch_steam_pressure', 'ch_steam_flow', 'ch_steam_temp', 'ch_feed_water_flow', 'ch_dea_temp', 'ch_stack_temp', 'ch_ph_water')
    list_filter = ('ch_date',)
    search_fields = ('ch_remark',)
    ordering = ('-ch_date', '-ch_time')

@admin.register(TakumaLog)
class TakumaLogAdmin(admin.ModelAdmin):
    list_display = ('tk_date', 'tk_time', 'tk_steam_pressure', 'tk_steam_flow', 'tk_steam_temp', 'tk_feed_water_flow', 'tk_dea_temp', 'tk_stack_temp' ,'tk_ph_water' )
    list_filter = ('tk_date',)
    search_fields = ('tk_remark',)
    ordering = ('-tk_date', '-tk_time')

# 4. Yoshimine Log ,bagasse_moisture ตัวแปรของ ph boiler
@admin.register(YoshimineLog)
class YoshimineLogAdmin(admin.ModelAdmin):
    list_display = ('yos_date', 'yos_time', 'yos_main_steam_pressure', 'yos_main_steam_flow', 'yos_main_steam_temp', 'yos_feed_water_flow', 'yos_feed_water_in_temp', 'yos_bagasse_moisture', 'yos_gas_exit_temp', 'yos_blowdown_flow' ) 
    list_filter = ('yos_date',)
    search_fields = ('yos_remark',)
    ordering = ('-yos_date', '-yos_time')

# 5. Banpong 1 Log (เพิ่มใหม่)
@admin.register(Banpong1Log)
class Banpong1LogAdmin(admin.ModelAdmin):
    list_display = ('bp1_date', 'bp1_time', 'bp1_main_steam_pressure', 'bp1_main_steam_flow', 'bp1_main_steam_temp', 'bp1_feed_water_flow', 'bp1_feed_water_in_temp', 'bp1_gas_exit_temp')
    list_filter = ('bp1_date',)
    search_fields = ('bp1_remark',)
    ordering = ('-bp1_date', '-bp1_time')

# 6. Banpong 2 Log (เพิ่มใหม่)
@admin.register(Banpong2Log)
class Banpong2LogAdmin(admin.ModelAdmin):
    list_display = ('bp2_date', 'bp2_time', 'bp2_main_steam_pressure', 'bp2_main_steam_flow', 'bp2_main_steam_temp', 'bp2_feed_water_flow', 'bp2_feed_water_in_temp', 'bp2_gas_exit_temp')
    list_filter = ('bp2_date',)
    search_fields = ('bp2_remark',)
    ordering = ('-bp2_date', '-bp2_time')

@admin.register(BoilerDailyKPI)
class BoilerDailyKPIAdmin(admin.ModelAdmin):
    list_display = ('date', 'pressure_20bar', 'pressure_40bar', 'total_steam_20bar', 'total_steam_40bar', 'shredder_consumption')
    list_filter = ('date',)
    ordering = ('-date',)

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'machine', 'dept', 'problem', 'downtime_stop', 'reporter')
    list_filter = ('date', 'dept', 'category', 'is_leak')
    search_fields = ('machine', 'problem', 'reporter')
    ordering = ('-date',)

@admin.register(KPIMetric)
class KPIMetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'target', 'actual', 'score', 'weight')
    list_editable = ('actual', 'score') # ให้แก้คะแนนจากหน้า list ได้เลย
    list_filter = ('category',)

@admin.register(MillReport)
class MillReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'line', 'cane_weight', 'overall_recovery', 'target_crushing', 'reduced_capacity_hours', 'first_mill_extraction', 'reduced_pol_extraction', 'cane_preparation_index', 'purity_drop', 'bagasse_moisture', 'pol_bagasse', 'imbibition_cane', 'imbibition_fiber', 'loss_bagasse', 'downtime', 'created_at' )
    list_filter = ('date', 'line' )
    search_fields = ('date',)
    ordering = ('-date', 'line')