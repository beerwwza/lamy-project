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
admin.site.register(LatheJob)

@admin.register(BoilerOperationLog)
class BoilerOperationLogAdmin(admin.ModelAdmin):
    list_display = ('jt_date', 'jt_time', 'jt_steam_pressure', 'jt_steam_flow', 'jt_temp_steam', 'jt_o2_gas', 'jt_feeder_speed' , 'jt_feed_water_flow', 'jt_temp_deaerator', 'jt_temp_gas_stack', 'jt_ph_boiler')
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
    list_display = ('yos_date', 'yos_time', 'yos_main_steam_pressure', 'yos_main_steam_flow', 'yos_main_steam_temp', 'yos_feed_water_flow', 'yos_feed_water_in_temp', 'yos_dc_gas_out_temp', 'yos_blowdown_flow' ) 
    list_filter = ('yos_date',)
    search_fields = ('yos_remark',)
    ordering = ('-yos_date', '-yos_time')

# 5. Banpong 1 Log (เพิ่มใหม่)
@admin.register(Banpong1Log)
class Banpong1LogAdmin(admin.ModelAdmin):
    list_display = ('bp1_date', 'bp1_time', 'bp1_main_steam_pressure', 'bp1_main_steam_flow',
                     'bp1_main_steam_temp', 'bp1_desuperheat_valve', 'bp1_desuperheat_in_temp', 
                     'bp1_desuperheat_out_temp', 'bp1_drum_level', 'bp1_drum_pressure', 'bp1_feed_water_flow', 'bp1_feed_water_pressure', 'bp1_feed_water_in_temp', 'bp1_eco_out_temp', 'bp1_eco_out_pressure', 'bp1_bd_flow', 'bp1_cbd_valve', 'bp1_ins_air_pressure', 'bp1_main_feeder', 'bp1_bd_ah1_in_temp', 'bp1_bd_ah1_in_press', 'bp1_bd_ah1_out_temp', 'bp1_bd_ah1_out_press', 'bp1_ah1_air_out_press', 'bp1_ah1_air_out_temp', 'bp1_ah2_air_out_temp', 'bp1_under_grate_air_temp', 'bp1_under_grate_air_press', 'bp1_furnace_pressure', 'bp1_gas_exit_temp', 'bp1_gas_exit_pressure', 'bp1_eco_out_gas_temp', 'bp1_eco_out_gas_press', 'bp1_ah2_gas_out_temp', 'bp1_ah2_gas_out_press', 'bp1_dc_gas_out_temp', 'bp1_dc_gas_out_press', 'bp1_esp_gas_in_temp', 'bp1_esp_gas_out_temp', 'bp1_esp_gas_out_press', 'bp1_ah1_gas_out_temp', 'bp1_ah1_gas_out_press', 'bp1_fdf_damper', 'bp1_faf_damper', 'bp1_faf_air_press','bp1_fdf2_damper', 'bp1_fdf2_air_press', 'bp1_under_gate_damper', 'bp1_idf_damper', 'bp1_esp_c1_volt', 'bp1_esp_c1_curr', 'bp1_esp_c2_volt', 'bp1_esp_c2_curr', 'bp1_esp_c3_volt', 'bp1_esp_c3_curr', 'bp1_steam_sum', 'bp1_feed_water_sum', 'bp1_blowdown_sum', 'bp1_cem_so2', 'bp1_cem_no2', 'bp1_cem_nox','bp1_cem_co', 'bp1_cem_tsp', 'bp1_cem_o2',)
    list_filter = ('bp1_date',)
    search_fields = ('bp1_remark',)
    ordering = ('-bp1_date', '-bp1_time')

# 6. Banpong 2 Log (เพิ่มใหม่)
@admin.register(Banpong2Log)
class Banpong2LogAdmin(admin.ModelAdmin):
    list_display = ('bp2_date', 'bp2_time', 'bp2_main_steam_pressure', 'bp2_main_steam_flow', 'bp2_main_steam_temp', 'bp2_feed_water_flow', 'bp2_feed_water_in_temp', 'bp2_ah1_gas_out_temp')
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
    list_display = ('date', 'line', 'cane_weight', 'target_crushing', 'first_mill_extraction', 'reduced_pol_extraction', 'cane_preparation_index', 'purity_drop', 'bagasse_moisture', 'pol_bagasse', 'imbibition_cane', 'imbibition_fiber', 'loss_bagasse', 'ccs', 'created_at' ) #เอา tash ออก 26/1/69
    list_filter = ('date', 'line' )
    search_fields = ('date',)
    ordering = ('-date', 'line')

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('equipment_id', 'name', 'location', 'priority_level', 'is_active')
    search_fields = ('equipment_id', 'name')
    list_filter = ('priority_level', 'is_active')

@admin.register(EquipmentBOM)
class EquipmentBOMAdmin(admin.ModelAdmin):
    list_display = ('part_no', 'part_name', 'equipment', 'qty', 'stock_qty')
    search_fields = ('part_no', 'part_name', 'equipment__equipment_id')

@admin.register(CBMVisualTest)
class CBMVisualTestAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'inspection_date', 'overall_condition')
    list_filter = ('overall_condition', 'inspection_date')

@admin.register(CBMVibration)
class CBMVibrationAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'inspection_date', 'status')
    list_filter = ('status', 'inspection_date')

@admin.register(CBMThermoscan)
class CBMThermoscanAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'inspection_date')
    list_filter = ('inspection_date',)

@admin.register(CBMOilAnalysis)
class CBMOilAnalysisAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'collection_date')
    list_filter = ('collection_date',)

@admin.register(CBMAcoustic)
class CBMAcousticAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'inspection_date', 'sound_pattern')
    list_filter = ('sound_pattern', 'inspection_date')