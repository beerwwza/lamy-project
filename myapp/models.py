from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 1. User & Employee Management Models
# ==========================================

class Job(models.Model):
    fullname = models.CharField(max_length=255)
    tel = models.IntegerField(null=True,blank=True)
    position = models.CharField(max_length=255)

    def __str__(self):
        return self.fullname

class employee(models.Model):
    name = models.CharField(max_length=255)
    employeeID = models.CharField(max_length=10)
    tell = models.CharField(max_length=12)
    group = models.CharField(max_length=100)
    department = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.name
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employeeID = models.CharField(max_length=50, blank=True, null=True) # รหัสพนักงาน
    tel = models.CharField(max_length=20, blank=True, null=True)        # เบอร์โทรศัพท์
    group = models.CharField(max_length=100, blank=True, null=True)     # ฝ่าย
    department = models.CharField(max_length=100, blank=True, null=True)# แผนก

    def __str__(self):
        return self.user.username

# ==========================================
# 2. Boiler & Machine Operation Logs
# ==========================================

class BoilerOperationLog(models.Model):
    # Main Fields (1-30 + Date/Time)
    jt_date = models.DateField(verbose_name="วันที่")
    jt_time = models.TimeField(verbose_name="เวลา")
    
    jt_steam_flow = models.FloatField(verbose_name="1) ไอน้ำจ่าย (T/H)", blank=True, null=True)
    jt_steam_pressure = models.FloatField(verbose_name="2) ความดันไอน้ำ (bar)", blank=True, null=True)
    jt_o2_gas = models.FloatField(verbose_name="3) O2 แก๊สออกจากเตา (%)", blank=True, null=True)
    
    jt_feeder_speed = models.FloatField(verbose_name="4) เครื่องป้อนกากอ้อย (%)", blank=True, null=True)
    jt_damper_fdf = models.FloatField(verbose_name="5) แดมป์เปอร์ พัดลมเป่า FDF", blank=True, null=True)
    jt_damper_idf = models.FloatField(verbose_name="6) แดมป์เปอร์ พัดลมดูด IDF", blank=True, null=True)
    jt_amp_oaf = models.FloatField(verbose_name="7) แอมป์ พัดลมเป่าเย็น OAF", blank=True, null=True)
    jt_amp_fdf = models.FloatField(verbose_name="8) แอมป์ พัดลมเป่า FDF", blank=True, null=True)
    jt_amp_idf = models.FloatField(verbose_name="9) แอมป์ พัดลมดูด IDF", blank=True, null=True)
    
    jt_drum_level = models.FloatField(verbose_name="10) ระดับน้ำหม้อบน", blank=True, null=True)
    jt_feed_water_valve = models.FloatField(verbose_name="11) วาล์วน้ำป้อน", blank=True, null=True)
    jt_feed_water_flow = models.FloatField(verbose_name="12) ปริมาตรน้ำป้อน", blank=True, null=True)
    jt_deaerator_level = models.FloatField(verbose_name="13) ระดับน้ำถังดีแอร์", blank=True, null=True)
    jt_deaerator_valve = models.FloatField(verbose_name="14) วาล์วน้ำถังดีแอร์", blank=True, null=True)
    
    jt_ph_boiler = models.FloatField(verbose_name="15) pH น้ำในเตา", blank=True, null=True)
    jt_tds_boiler = models.FloatField(verbose_name="16) TDS น้ำในเตา", blank=True, null=True)
    
    jt_temp_steam = models.FloatField(verbose_name="17) อุณหภูมิไอน้ำ", blank=True, null=True)
    jt_temp_deaerator = models.FloatField(verbose_name="18) อุณหภูมิน้ำถังดีแอร์", blank=True, null=True)
    jt_temp_feed_water_eco = models.FloatField(verbose_name="19) อุณหภูมิน้ำป้อนออกอีโค", blank=True, null=True)
    jt_temp_air_out_ah = models.FloatField(verbose_name="20) อากาศออกแอร์ฮีทเตอร์", blank=True, null=True)
    jt_temp_gas_in_ah = models.FloatField(verbose_name="21) แก๊สเข้าแอร์ฮีทเตอร์", blank=True, null=True)
    jt_temp_gas_in_eco = models.FloatField(verbose_name="22) แก๊สเข้าอีโค", blank=True, null=True)
    jt_temp_gas_stack = models.FloatField(verbose_name="23) แก๊สออกปล่อง", blank=True, null=True)
    
    jt_press_furnace = models.FloatField(verbose_name="24) ความดันในเตา", blank=True, null=True)
    jt_press_gas_out_ah = models.FloatField(verbose_name="25) ความดันแก๊สออกแอร์ฮีทเตอร์", blank=True, null=True)
    jt_press_gas_out_eco = models.FloatField(verbose_name="26) ความดันแก๊สออกจากโค", blank=True, null=True) # Typo in CSV: โค -> Eco? Assume Eco
    jt_press_gas_out_dc = models.FloatField(verbose_name="27) ความดันแก๊สออก DC", blank=True, null=True)
    
    jt_inlet_wet_scrubber = models.FloatField(verbose_name="28) Inlet wet scrubber", blank=True, null=True)
    jt_outlet_wet_scrubber = models.FloatField(verbose_name="29) Outlet wet scrubber", blank=True, null=True)
    jt_inlet_stack = models.FloatField(verbose_name="30) Inlet stack", blank=True, null=True)
    
    # Remark & Sums
    jt_problem_cause = models.TextField(verbose_name="ปัญหาและสาเหตุ", blank=True, null=True)
    
    jt_sum_steam = models.FloatField(verbose_name="SUM ไอจ่าย", blank=True, null=True)
    jt_sum_feed_water = models.FloatField(verbose_name="SUM น้ำป้อน", blank=True, null=True)
    
    # CEM
    jt_cem_so2 = models.FloatField(verbose_name="Continous Emissions Monitoring (SO2)", blank=True, null=True)
    jt_cem_no2 = models.FloatField(verbose_name="Continous Emissions Monitoring (NO2)", blank=True, null=True)
    jt_cem_nox = models.FloatField(verbose_name="Continous Emissions Monitoring (NOX)", blank=True, null=True)
    jt_cem_co = models.FloatField(verbose_name="Continous Emissions Monitoring (CO)", blank=True, null=True)
    jt_cem_dust = models.FloatField(verbose_name="Continous Emissions Monitoring (Dust)", blank=True, null=True)
    jt_cem_o2 = models.FloatField(verbose_name="Continous Emissions Monitoring (O2)", blank=True, null=True)

    jt_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"JT Log {self.jt_date} {self.jt_time}"


# Updated YoshimineLog based on new Excel Structure
class YoshimineLog(models.Model):
    yos_date = models.DateField(verbose_name="วันที่")
    yos_time = models.TimeField(verbose_name="เวลา")
    
    # Steam
    yos_main_steam_flow = models.FloatField(verbose_name="Main Steam Flow", blank=True, null=True)
    yos_main_steam_pressure = models.FloatField(verbose_name="Main Steam Pressure", blank=True, null=True)
    yos_main_steam_temp = models.FloatField(verbose_name="Main Steam Outlet Temp", blank=True, null=True)
    yos_desuperheat_valve = models.FloatField(verbose_name="De-Superheat Flow Control Valve", blank=True, null=True)
    yos_desuperheat_in_temp = models.FloatField(verbose_name=".De-Superheat Inlet Temp", blank=True, null=True)
    yos_desuperheat_out_temp = models.FloatField(verbose_name="De-Superheat Outlet Temp", blank=True, null=True)
    
    # Water & Drum
    yos_drum_level = models.FloatField(verbose_name="Drum Level", blank=True, null=True)
    yos_drum_pressure = models.FloatField(verbose_name="Drum Pressure", blank=True, null=True)
    yos_feed_water_flow = models.FloatField(verbose_name="Feed Water Flow", blank=True, null=True)
    yos_feed_water_pressure = models.FloatField(verbose_name="Feed Water Pressure", blank=True, null=True)
    yos_feed_water_in_temp = models.FloatField(verbose_name="Feed Water Inlet Temp", blank=True, null=True)
    yos_eco_out_temp = models.FloatField(verbose_name="Eco Outlet Temp", blank=True, null=True)
    
    # Blowdown
    yos_blowdown_flow = models.FloatField(verbose_name=".Blow Down Flow", blank=True, null=True)
    yos_cbd_valve = models.FloatField(verbose_name="Continous Blow Down Flow Control Valve", blank=True, null=True)
    
    # Air
    yos_ins_air_pressure = models.FloatField(verbose_name="Ins. Air Pressure", blank=True, null=True)
    yos_main_feeder = models.FloatField(verbose_name="Main Feeder", blank=True, null=True)
    yos_bd_ah1_in_temp = models.FloatField(verbose_name="Blow Down Air Preheater#1 Inlet Temp", blank=True, null=True)
    yos_bd_ah1_in_press = models.FloatField(verbose_name="Blow Down Air Preheater#1 Inlet Pressure", blank=True, null=True)
    yos_bd_ah1_out_temp = models.FloatField(verbose_name="Blow Down Air Preheater#1 Outlet Temp", blank=True, null=True)
    yos_ah1_air_out_press = models.FloatField(verbose_name="A/H# 1 Air Outlet Pressure", blank=True, null=True)
    yos_ah1_air_out_temp = models.FloatField(verbose_name="A/H# 1 Air Outlet Temp", blank=True, null=True)
    yos_ah2_air_out_temp = models.FloatField(verbose_name="A/H# 2 Air Outlet Temp", blank=True, null=True)
    yos_sh_out_gas_temp = models.FloatField(verbose_name="1st sH Outlet Gas Temp", blank=True, null=True)
    yos_under_grate_press = models.FloatField(verbose_name="Under Grate Air Pressure", blank=True, null=True)
    
    # Furnace & Gas
    yos_furnace_pressure = models.FloatField(verbose_name="Furnace Pressure", blank=True, null=True)
    yos_gas_exit_temp = models.FloatField(verbose_name="Gas Exit Temp", blank=True, null=True)
    yos_gas_exit_press = models.FloatField(verbose_name="Gas Exit Pressure", blank=True, null=True)
    yos_eco_out_gas_temp = models.FloatField(verbose_name="Eco Outlet Gas Temp", blank=True, null=True)
    yos_eco_out_gas_press = models.FloatField(verbose_name="Eco Outlet Gas Pressure", blank=True, null=True)
    yos_ah2_gas_out_temp = models.FloatField(verbose_name="A/H#2 Gas Outlet Temp", blank=True, null=True)
    yos_ah2_gas_out_press = models.FloatField(verbose_name="A/H#2 Gas Outlet Pressure", blank=True, null=True)
    yos_dc_gas_out_temp = models.FloatField(verbose_name="D/C Gas Outlet Temp", blank=True, null=True)
    yos_dc_gas_out_press = models.FloatField(verbose_name="D/C Gas Outlet Pressure", blank=True, null=True)
    yos_esp_gas_out_press = models.FloatField(verbose_name="Esp Gas Outlet Pressure", blank=True, null=True)
    yos_ah1_gas_out_press = models.FloatField(verbose_name="A/H#1 Gas Outlet Pressure", blank=True, null=True)
    
    # Dampers
    yos_sf_damper = models.FloatField(verbose_name="SF. Damper แดมป์เปอร์ลมเป่ากากอ้อย", blank=True, null=True)
    yos_sf_air_press = models.FloatField(verbose_name="SF. Air Pressure", blank=True, null=True)
    yos_fdf2_air_press = models.FloatField(verbose_name="2nd FDF. Air Pressure", blank=True, null=True)
    yos_under_gate_damper = models.FloatField(verbose_name="Under Gate Damper", blank=True, null=True)
    yos_idf_damper = models.FloatField(verbose_name="IDF. Damper", blank=True, null=True)
    
    # ESP
    yos_esp_c1_volt = models.FloatField(verbose_name="Esp Cell1 Voltage", blank=True, null=True)
    yos_esp_c1_curr = models.FloatField(verbose_name="Esp Cell1 Current", blank=True, null=True)
    yos_esp_c2_volt = models.FloatField(verbose_name="Esp Cell2 Voltage", blank=True, null=True)
    yos_esp_c2_curr = models.FloatField(verbose_name="Esp Cell2 Current", blank=True, null=True)
    
    # Sums
    yos_steam_sum = models.FloatField(verbose_name="Steam Sum", blank=True, null=True)
    yos_feed_water_sum = models.FloatField(verbose_name="Feed Water Sum", blank=True, null=True)
    
    # CEM
    yos_cem_so2 = models.FloatField(verbose_name="Continous Emissions Monitoring (SO2)", blank=True, null=True)
    yos_cem_no2 = models.FloatField(verbose_name="Continous Emissions Monitoring (NO2)", blank=True, null=True)
    yos_cem_nox = models.FloatField(verbose_name="Continous Emissions Monitoring (NOX)", blank=True, null=True)
    yos_cem_co = models.FloatField(verbose_name="Continous Emissions Monitoring (CO)", blank=True, null=True)
    yos_cem_dust = models.FloatField(verbose_name="Continous Emissions Monitoring (Dust)", blank=True, null=True)
    yos_cem_o2 = models.FloatField(verbose_name="Continous Emissions Monitoring (O2)", blank=True, null=True)
    
    # Tanks
    yos_steam_transform_level = models.FloatField(verbose_name="Steam Tremformer Level", blank=True, null=True)
    yos_steam_transform_valve = models.FloatField(verbose_name="Steam Tremformer Control valve", blank=True, null=True)
    yos_condensate_tank_level = models.FloatField(verbose_name="Condensate Tank Level", blank=True, null=True)
    yos_header_temp = models.FloatField(verbose_name="Header Temp", blank=True, null=True)
    
    # Deaerator
    yos_dea_level = models.FloatField(verbose_name="Deaerator Level", blank=True, null=True)
    yos_dea_pressure = models.FloatField(verbose_name="Deaerator Pressure", blank=True, null=True)
    yos_dea_valve = models.FloatField(verbose_name="Deaerator Control valve", blank=True, null=True)
    
    yos_oxygen = models.FloatField(verbose_name="Oxygen (O2)", blank=True, null=True)
    yos_remark = models.TextField(verbose_name="หมายเหตุ", blank=True, null=True)
    yos_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Yoshimine Log {self.yos_date} {self.yos_time}"

class Banpong1Log(models.Model):
    bp1_date = models.DateField(verbose_name="วันที่")
    bp1_time = models.TimeField(verbose_name="เวลา")

    # --- Group 1: Steam & De-superheat ---
    bp1_main_steam_flow = models.FloatField(verbose_name="Main Steam Flow", blank=True, null=True)
    bp1_main_steam_pressure = models.FloatField(verbose_name="Main Steam Pressure", blank=True, null=True)
    bp1_main_steam_temp = models.FloatField(verbose_name="Main Steam Outlet Temp", blank=True, null=True)
    bp1_desuperheat_valve = models.FloatField(verbose_name="De-Superheat Valve", blank=True, null=True)
    bp1_desuperheat_in_temp = models.FloatField(verbose_name="De-Superheat Inlet Temp", blank=True, null=True)
    bp1_desuperheat_out_temp = models.FloatField(verbose_name="De-Superheat Outlet Temp", blank=True, null=True)

    # --- Group 2: Water System ---
    bp1_drum_level = models.FloatField(verbose_name="Drum Level", blank=True, null=True)
    bp1_drum_pressure = models.FloatField(verbose_name="Drum Pressure", blank=True, null=True)
    bp1_feed_water_flow = models.FloatField(verbose_name="Feed Water Flow", blank=True, null=True)
    bp1_feed_water_pressure = models.FloatField(verbose_name="Feed Water Pressure", blank=True, null=True)
    bp1_feed_water_in_temp = models.FloatField(verbose_name="Feed Water Inlet Temp", blank=True, null=True)
    bp1_eco_out_temp = models.FloatField(verbose_name="Eco Outlet Temp", blank=True, null=True)
    bp1_eco_out_pressure = models.FloatField(verbose_name="Eco Outlet Pressure", blank=True, null=True)
    bp1_bd_flow = models.FloatField(verbose_name="Blow Down Flow", blank=True, null=True)
    bp1_cbd_valve = models.FloatField(verbose_name="CBD Valve", blank=True, null=True)
    #bp1_ph_boiler = models.FloatField(verbose_name="pH_boiler", blank=True, null=True)

    # --- Group 3: Air, Fans, Feeder ---
    bp1_main_feeder = models.FloatField(verbose_name="Main Feeder", blank=True, null=True)
    bp1_under_grate_air_temp = models.FloatField(verbose_name="Under Grate Air Temp", blank=True, null=True)
    bp1_under_grate_air_press = models.FloatField(verbose_name="Under Grate Air Press", blank=True, null=True)
    bp1_ins_air_pressure = models.FloatField(verbose_name="Ins. Air Pressure", blank=True, null=True)
    
    # Air Heater Air Side
    bp1_ah1_air_out_press = models.FloatField(verbose_name="AH1 Air Out Press", blank=True, null=True)
    bp1_ah1_air_out_temp = models.FloatField(verbose_name="AH1 Air Out Temp", blank=True, null=True)
    bp1_ah2_air_out_press = models.FloatField(verbose_name="AH2 Air Out Press", blank=True, null=True)
    
    # FDF
    bp1_fdf_damper = models.FloatField(verbose_name="FDF Damper", blank=True, null=True)
    bp1_fdf2_damper = models.FloatField(verbose_name="2nd FDF Damper", blank=True, null=True)
    bp1_fdf2_air_press = models.FloatField(verbose_name="2nd FDF Air Press", blank=True, null=True)
    
    # FAF/SDF
    bp1_faf_damper = models.FloatField(verbose_name="FAF Damper", blank=True, null=True)
    bp1_faf_air_press = models.FloatField(verbose_name="FAF Air Press", blank=True, null=True)
    
    # Other Dampers
    bp1_under_gate_damper = models.FloatField(verbose_name="Under Gate Damper", blank=True, null=True)
    bp1_idf_damper = models.FloatField(verbose_name="IDF Damper", blank=True, null=True)
    
    # Blow Down Air
    bp1_bd_ah1_in_press = models.FloatField(verbose_name="BD AH1 In Press", blank=True, null=True)
    bp1_bd_ah1_out_temp = models.FloatField(verbose_name="BD AH1 Out Temp", blank=True, null=True)
    bp1_bd_ah1_out_press = models.FloatField(verbose_name="BD AH1 Out Press", blank=True, null=True)

    # --- Group 4: Gas System ---
    bp1_furnace_pressure = models.FloatField(verbose_name="Furnace Pressure", blank=True, null=True)
    bp1_gas_exit_temp = models.FloatField(verbose_name="Gas Exit Temp", blank=True, null=True)
    bp1_gas_exit_pressure = models.FloatField(verbose_name="Gas Exit Pressure", blank=True, null=True)
    
    # Gas Path
    bp1_eco_out_gas_temp = models.FloatField(verbose_name="Eco Out Gas Temp", blank=True, null=True)
    bp1_eco_out_gas_press = models.FloatField(verbose_name="Eco Out Gas Press", blank=True, null=True)
    bp1_ah2_gas_out_temp = models.FloatField(verbose_name="AH2 Gas Out Temp", blank=True, null=True)
    bp1_ah2_gas_out_press = models.FloatField(verbose_name="AH2 Gas Out Press", blank=True, null=True)
    bp1_dc_gas_out_temp = models.FloatField(verbose_name="DC Gas Out Temp", blank=True, null=True)
    bp1_dc_gas_out_press = models.FloatField(verbose_name="DC Gas Out Press", blank=True, null=True)
    bp1_esp_gas_in_temp = models.FloatField(verbose_name="ESP Gas In Temp", blank=True, null=True)
    bp1_esp_gas_in_press = models.FloatField(verbose_name="ESP Gas In Press", blank=True, null=True)
    bp1_ah1_gas_out_temp = models.FloatField(verbose_name="AH1 Gas Out Temp", blank=True, null=True)
    bp1_ah1_gas_out_press = models.FloatField(verbose_name="AH1 Gas Out Press", blank=True, null=True)

    # --- Group 5: ESP ---
    bp1_esp_c1_volt = models.FloatField(verbose_name="ESP C1 Volt", blank=True, null=True)
    bp1_esp_c1_curr = models.FloatField(verbose_name="ESP C1 Curr", blank=True, null=True)
    bp1_esp_c2_volt = models.FloatField(verbose_name="ESP C2 Volt", blank=True, null=True)
    bp1_esp_c2_curr = models.FloatField(verbose_name="ESP C2 Curr", blank=True, null=True)
    bp1_esp_c3_volt = models.FloatField(verbose_name="ESP C3 Volt", blank=True, null=True)
    bp1_esp_c3_curr = models.FloatField(verbose_name="ESP C3 Curr", blank=True, null=True)

    bp1_remark = models.TextField(verbose_name="หมายเหตุ", blank=True, null=True)
    bp1_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Banpong1 Log {self.bp1_date} {self.bp1_time}"

class ChengchenLog(models.Model):
    ch_date = models.DateField(verbose_name="วันที่")
    ch_time = models.TimeField(verbose_name="เวลา")
    
    # Steam & Combustion (1-3)
    ch_steam_flow = models.FloatField(verbose_name="1) ไอน้ำจ่าย", blank=True, null=True)
    ch_steam_pressure = models.FloatField(verbose_name="2) แรงดันไอน้ำ", blank=True, null=True)
    ch_o2_percent = models.FloatField(verbose_name="3) O2 ภายในเตา", blank=True, null=True)

    # Control & Fans (4-9)
    ch_feeder_control = models.FloatField(verbose_name="4) คอลโทรลเครื่องป้อนกากอ้อย", blank=True, null=True)
    ch_fdf_damper = models.FloatField(verbose_name="5) แดมเปอร์ พัดลมเป่า (FDF)", blank=True, null=True)
    ch_idf_damper = models.FloatField(verbose_name="6) แดมเปอร์ พัดลมดูด (IDF)", blank=True, null=True)
    ch_fdf_amp = models.FloatField(verbose_name="7) แอมป์ พัดลมเป่า (FDF)", blank=True, null=True)
    ch_saf_amp_left = models.FloatField(verbose_name="8) แอมป์ พัดลมช่วย SAF ซ้าย", blank=True, null=True)
    ch_saf_amp_right = models.FloatField(verbose_name="8) แอมป์ พัดลมช่วย SAF ขวา", blank=True, null=True)
    ch_idf_amp = models.FloatField(verbose_name="9) แอมป์ พัดลมดูด (IDF)", blank=True, null=True)

    # Water System (10-14)
    ch_drum_level = models.FloatField(verbose_name="10) ระดับน้ำหม้อบน", blank=True, null=True)
    ch_feed_water_valve = models.FloatField(verbose_name="11) คอลโทรลวาล์วน้ำป้อน", blank=True, null=True)
    ch_feed_water_flow = models.FloatField(verbose_name="12) ปริมาตรน้ำป้อน", blank=True, null=True)
    ch_ph_water = models.FloatField(verbose_name="13) pH น้ำในเตา", blank=True, null=True)
    ch_tds_water = models.FloatField(verbose_name="14) TDS น้ำในเตา", blank=True, null=True)

    # Temperature (15-21)
    ch_steam_temp = models.FloatField(verbose_name="15) อุณหภูมิไอน้ำ", blank=True, null=True)
    ch_dea_temp = models.FloatField(verbose_name="16) อุณหภูมิน้ำถังดีแอร์", blank=True, null=True)
    ch_eco_out_temp = models.FloatField(verbose_name="17) อุณหภูมิน้ำป้อนออกอีโค", blank=True, null=True)
    ch_air_heater_out_temp = models.FloatField(verbose_name="18) อากาศออกแอร์ฮีทเตอร์", blank=True, null=True)
    ch_gas_furnace_ah_temp = models.FloatField(verbose_name="19) แก๊สออกจากเตาเข้าแอร์ฮีทเตอร์", blank=True, null=True)
    ch_gas_in_eco_temp = models.FloatField(verbose_name="20) แก๊สเข้าอีโค", blank=True, null=True)
    ch_stack_temp = models.FloatField(verbose_name="21) แก๊สออกปล่อง", blank=True, null=True)

    # Pressure (22-24)
    ch_furnace_pressure = models.FloatField(verbose_name="22) ความดันในเตา", blank=True, null=True)
    ch_gas_out_eco_pressure = models.FloatField(verbose_name="23) ความดันแก๊สออกจากอีโค", blank=True, null=True)
    ch_gas_out_dc_pressure = models.FloatField(verbose_name="24) ความดันแก๊สออก DC", blank=True, null=True)
    
    # Scrubbers (25-27)
    ch_inlet_wet_scrubber_press = models.FloatField(verbose_name="25) Inlet wet scrubber gas pressure", blank=True, null=True)
    ch_outlet_wet_scrubber_press = models.FloatField(verbose_name="26) Outlet wet scrubber gas pressure", blank=True, null=True)
    ch_inlet_stack_press = models.FloatField(verbose_name="27) Inlet stack gas pressure", blank=True, null=True)

    ch_remark = models.TextField(verbose_name="ปัญหาสาเหตุ/การแก้ไข", blank=True, null=True)
    ch_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chengchen Log {self.ch_date} {self.ch_time}"
    
class TakumaLog(models.Model):
    tk_date = models.DateField(verbose_name="วันที่")
    tk_time = models.TimeField(verbose_name="เวลา")
    
    # Steam & Combustion (1-3)
    tk_steam_flow = models.FloatField(verbose_name="1) ไอน้ำจ่าย", blank=True, null=True)
    tk_steam_pressure = models.FloatField(verbose_name="2) แรงดันไอน้ำ", blank=True, null=True)
    tk_o2_percent = models.FloatField(verbose_name="3) O2 ภายในเตา", blank=True, null=True)
    
    # Control & Fans (4-9)
    tk_feeder_control = models.FloatField(verbose_name="4) เครื่องป้อนกากอ้อย", blank=True, null=True)
    tk_fdf_damper = models.FloatField(verbose_name="5) แดมเปอร์ พัดลมเป่า (FDF)", blank=True, null=True)
    tk_idf_damper = models.FloatField(verbose_name="6) แดมเปอร์ พัดลมดูด (IDF)", blank=True, null=True)
    tk_fdf_amp = models.FloatField(verbose_name="7) แอมป์ พัดลมเป่า (FDF)", blank=True, null=True)
    tk_saf_amp_left = models.FloatField(verbose_name="8) แอมป์ พัดลมช่วย SAF ซ้าย", blank=True, null=True)
    tk_saf_amp_right = models.FloatField(verbose_name="8) แอมป์ พัดลมช่วย SAF ขวา", blank=True, null=True)
    tk_idf_amp = models.FloatField(verbose_name="9) แอมป์ พัดลมดูด (IDF)", blank=True, null=True)
    
    # Water System (10-14)
    tk_drum_level = models.FloatField(verbose_name="10) ระดับน้ำหม้อบน", blank=True, null=True)
    tk_feed_water_valve = models.FloatField(verbose_name="11) คอลโทรลวาล์วน้ำป้อน", blank=True, null=True)
    tk_feed_water_flow = models.FloatField(verbose_name="12) ปริมาตรน้ำป้อน", blank=True, null=True)
    tk_ph_water = models.FloatField(verbose_name="13) pH น้ำในเตา", blank=True, null=True)
    tk_tds_water = models.FloatField(verbose_name="14) TDS น้ำในเตา", blank=True, null=True)
    
    # Temperature (15-19)
    tk_steam_temp = models.FloatField(verbose_name="15) อุณหภูมิไอน้ำ", blank=True, null=True)
    tk_dea_temp = models.FloatField(verbose_name="16) อุณหภูมิน้ำถังดีแอร์", blank=True, null=True)
    tk_air_heater_out_temp = models.FloatField(verbose_name="17) อากาศออกแอร์ฮีทเตอร์", blank=True, null=True)
    tk_gas_furnace_ah_temp = models.FloatField(verbose_name="18) แก๊สออกจากเตาเข้าแอร์ฮีทเตอร์", blank=True, null=True)
    tk_stack_temp = models.FloatField(verbose_name="19) แก๊สออกปล่อง", blank=True, null=True)
    
    # Pressure (20-21)
    tk_furnace_pressure = models.FloatField(verbose_name="20) ความดันในเตา", blank=True, null=True)
    tk_gas_out_dc_pressure = models.FloatField(verbose_name="21) ความดันแก๊สออก DC", blank=True, null=True)
    
    # Scrubbers (22-24)
    tk_inlet_wet_scrubber_press = models.FloatField(verbose_name="22) Inlet wet scrubber gas pressure", blank=True, null=True)
    tk_outlet_wet_scrubber_press = models.FloatField(verbose_name="23) Outlet wet scrubber gas pressure", blank=True, null=True)
    tk_inlet_stack_press = models.FloatField(verbose_name="24) Inlet stack gas pressure", blank=True, null=True)

    tk_remark = models.TextField(verbose_name="ปัญหาสาเหตุ / การแก้ไข", blank=True, null=True)
    tk_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Takuma Log {self.tk_date} {self.tk_time}"

class Banpong2Log(models.Model):
    bp2_date = models.DateField(verbose_name="วันที่")
    bp2_time = models.TimeField(verbose_name="เวลา")

    # --- Group 1: Steam & De-superheat ---
    bp2_main_steam_flow = models.FloatField(verbose_name="Main Steam Flow", blank=True, null=True)
    bp2_main_steam_pressure = models.FloatField(verbose_name="Main Steam Pressure", blank=True, null=True)
    bp2_main_steam_temp = models.FloatField(verbose_name="Main Steam Outlet Temp", blank=True, null=True)
    bp2_desuperheat_valve = models.FloatField(verbose_name="De-Superheat Flow Control Valve", blank=True, null=True)
    bp2_desuperheat_in_temp = models.FloatField(verbose_name="De-Superheat Inlet Temp", blank=True, null=True)
    bp2_desuperheat_out_temp = models.FloatField(verbose_name="De-Superheat Outlet Temp", blank=True, null=True)

    # --- Group 2: Feed water, Drum, Eco, Blowdown ---
    # Note: Deaerator fields not found in Banpong2 CSV, skipping per file content
    bp2_drum_level = models.FloatField(verbose_name="Drum Level", blank=True, null=True)
    bp2_drum_pressure = models.FloatField(verbose_name="Drum Pressure", blank=True, null=True)
    bp2_feed_water_flow = models.FloatField(verbose_name="Feed Water Flow", blank=True, null=True)
    bp2_feed_water_pressure = models.FloatField(verbose_name="Feed Water Pressure", blank=True, null=True)
    bp2_feed_water_in_temp = models.FloatField(verbose_name="Feed Water Inlet Temp", blank=True, null=True)
    bp2_eco_out_temp = models.FloatField(verbose_name="Eco Outlet Temp (Water)", blank=True, null=True)
    bp2_eco_out_pressure = models.FloatField(verbose_name="Eco Outlet Pressure", blank=True, null=True)
    bp2_bd_flow = models.FloatField(verbose_name="Blow Down Flow", blank=True, null=True)
    bp2_cbd_valve = models.FloatField(verbose_name="Continuous Blow Down Valve", blank=True, null=True)

    # --- Group 3: Air, Damper, FAN, FDF, IDF, SDF, Feeder ---
    # General & Feeder
    bp2_main_feeder = models.FloatField(verbose_name="Main Feeder", blank=True, null=True)
    bp2_ins_air_pressure = models.FloatField(verbose_name="Ins. Air Pressure", blank=True, null=True)
    
    # Air Temps & Pressures (Air Side)
    # Mapping "Blow Down Air Preheater" columns here
    bp2_bd_ah1_in_press = models.FloatField(verbose_name="AH#1 Inlet Pressure (Blow Down?)", blank=True, null=True)
    bp2_bd_ah1_out_temp = models.FloatField(verbose_name="AH#1 Outlet Temp", blank=True, null=True)
    bp2_bd_ah1_out_press = models.FloatField(verbose_name="AH#1 Outlet Pressure", blank=True, null=True)
    
    bp2_ah1_air_out_press = models.FloatField(verbose_name="AH#1 Air Outlet Pressure", blank=True, null=True)
    bp2_ah1_air_out_temp = models.FloatField(verbose_name="AH#1 Air Outlet Temp", blank=True, null=True)
    bp2_ah2_air_out_press = models.FloatField(verbose_name="AH#2 Air Outlet Pressure", blank=True, null=True)
    
    bp2_under_grate_air_temp = models.FloatField(verbose_name="Under Grate Air Temp", blank=True, null=True)
    bp2_under_grate_air_press = models.FloatField(verbose_name="Under Grate Air Pressure", blank=True, null=True)

    # Fans & Dampers
    bp2_fdf_damper = models.FloatField(verbose_name="FDF Damper", blank=True, null=True)
    bp2_faf_damper = models.FloatField(verbose_name="FAF Damper (SDF)", blank=True, null=True) # Mapping FAF to SDF
    bp2_faf_air_press = models.FloatField(verbose_name="FAF Air Pressure", blank=True, null=True)
    bp2_fdf2_damper = models.FloatField(verbose_name="2nd FDF Damper", blank=True, null=True)
    bp2_fdf2_air_press = models.FloatField(verbose_name="2nd FDF Air Pressure", blank=True, null=True)
    bp2_under_gate_damper = models.FloatField(verbose_name="Under Grate Damper", blank=True, null=True)
    bp2_idf_damper = models.FloatField(verbose_name="IDF Damper", blank=True, null=True)

    # --- Group 4: Gas, Stack, Furnace ---
    bp2_furnace_pressure = models.FloatField(verbose_name="Furnace Pressure", blank=True, null=True)
    bp2_gas_exit_temp = models.FloatField(verbose_name="Gas Exit Temp", blank=True, null=True)
    bp2_gas_exit_pressure = models.FloatField(verbose_name="Gas Exit Pressure", blank=True, null=True)
    
    bp2_eco_out_gas_temp = models.FloatField(verbose_name="Eco Outlet Gas Temp", blank=True, null=True)
    bp2_eco_out_gas_press = models.FloatField(verbose_name="Eco Outlet Gas Pressure", blank=True, null=True)
    
    bp2_ah2_gas_out_temp = models.FloatField(verbose_name="AH#2 Gas Outlet Temp", blank=True, null=True)
    bp2_ah2_gas_out_press = models.FloatField(verbose_name="AH#2 Gas Outlet Pressure", blank=True, null=True)
    
    bp2_dc_gas_out_temp = models.FloatField(verbose_name="D/C Gas Outlet Temp", blank=True, null=True)
    bp2_dc_gas_out_press = models.FloatField(verbose_name="D/C Gas Outlet Pressure", blank=True, null=True)
    
    bp2_esp_gas_in_temp = models.FloatField(verbose_name="ESP Gas Inlet Temp", blank=True, null=True)
    bp2_esp_gas_in_press = models.FloatField(verbose_name="ESP Gas Inlet Pressure", blank=True, null=True)
    
    bp2_ah1_gas_out_temp = models.FloatField(verbose_name="AH#1 Gas Outlet Temp", blank=True, null=True)
    bp2_ah1_gas_out_press = models.FloatField(verbose_name="AH#1 Gas Outlet Pressure", blank=True, null=True)

    # --- Group 5: ESP ---
    bp2_esp_c1_volt = models.FloatField(verbose_name="ESP Cell 1 Voltage", blank=True, null=True)
    bp2_esp_c1_curr = models.FloatField(verbose_name="ESP Cell 1 Current", blank=True, null=True)
    bp2_esp_c2_volt = models.FloatField(verbose_name="ESP Cell 2 Voltage", blank=True, null=True)
    bp2_esp_c2_curr = models.FloatField(verbose_name="ESP Cell 2 Current", blank=True, null=True)
    bp2_esp_c3_volt = models.FloatField(verbose_name="ESP Cell 3 Voltage", blank=True, null=True)
    bp2_esp_c3_curr = models.FloatField(verbose_name="ESP Cell 3 Current", blank=True, null=True)

    bp2_remark = models.TextField(verbose_name="หมายเหตุ", blank=True, null=True)
    bp2_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Banpong2 Log {self.bp2_date} {self.bp2_time}"

# 4. NEW: Boiler Daily KPI (ตามรายการใหม่ 13 ข้อ)
# ==========================================

class BoilerDailyKPI(models.Model):
    # 1. Date
    date = models.DateField(verbose_name="1. วันที่")
    
    # Downtime & Loss (2-6)
    downtime_a = models.FloatField(verbose_name="2. % Downtime A", default=0)
    downtime_b = models.FloatField(verbose_name="3. % Downtime B", default=0)
    downtime_sugar_melt = models.FloatField(verbose_name="4. % Downtime ละลายน้ำตาล", default=0)
    reduced_cap_a = models.FloatField(verbose_name="5. % ลดกำลังการหีบ A", default=0)
    reduced_cap_b = models.FloatField(verbose_name="6. % ลดกำลังการหีบ B", default=0)
    
    # 20 Bar System (7-9)
    pressure_20bar = models.FloatField(verbose_name="7. แรงดันไอน้ำ Header 20 bar (bar)", default=0)
    flow_20bar = models.FloatField(verbose_name="8. จ่ายไอน้ำ 20 bar (ton/hr)", default=0)
    total_steam_20bar = models.FloatField(verbose_name="9. ผลรวมการผลิตไอน้ำ 20 bar (ton/day)", default=0)
    
    # 40 Bar System (10-12)
    pressure_40bar = models.FloatField(verbose_name="10. แรงดันไอน้ำ Header 40 bar (bar)", default=0)
    flow_40bar = models.FloatField(verbose_name="11. จ่ายไอน้ำ 40 bar (ton/hr)", default=0)
    total_steam_40bar = models.FloatField(verbose_name="12. ผลรวมการผลิตไอน้ำ 40 bar (ton/day)", default=0)
    
    # Consumption (13)
    shredder_consumption = models.FloatField(verbose_name="13. ปริมาณการใช้เครื่องตีใบอ้อย (ton/day)", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"KPI {self.date}"

# ==========================================
# 3. NEW: Maintenance Dashboard Models
# ==========================================

class MaintenanceLog(models.Model):
    CATEGORY_CHOICES = [
        ('สึกหรอ', 'สึกหรอ'),
        ('แปลกปลอม', 'แปลกปลอม'),
        ('สายพาน', 'สายพาน'),
        ('ออยซีล', 'ออยซีล'),
        ('ไฟฟ้า', 'ไฟฟ้า'),
        ('อื่นๆ', 'อื่นๆ'),
    ]

    date = models.DateField(verbose_name="วันที่")
    machine = models.CharField(max_length=255, verbose_name="เครื่องจักร")
    dept = models.CharField(max_length=100, verbose_name="แผนก", default="ไม่ระบุ")
    problem = models.TextField(verbose_name="ปัญหาที่เกิด")
    cause = models.TextField(verbose_name="สาเหตุ", blank=True, null=True)
    solution = models.TextField(verbose_name="การแก้ไข", blank=True, null=True)
    
    # Downtime & Stats
    downtime_stop = models.FloatField(default=0, verbose_name="เสียเวลาหยุดหีบ (ชม.)")
    downtime_reduced = models.FloatField(default=0, verbose_name="ลดรอบ (ชม.)")
    downtime_non_stop = models.FloatField(default=0, verbose_name="เสียเวลาไม่หยุดหีบ (ชม.)")
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='อื่นๆ', verbose_name="หัวข้อ")
    is_leak = models.BooleanField(default=False, verbose_name="รั่วไหลหรือไม่")
    
    # Spare Parts
    spare_part = models.CharField(max_length=255, default="-", verbose_name="อะไหล่ที่เปลี่ยน")
    qty = models.FloatField(default=0, verbose_name="จำนวน")
    
    # People
    reporter = models.CharField(max_length=100, verbose_name="ผู้แจ้ง", default="-")
    resolver = models.CharField(max_length=100, verbose_name="ผู้แก้ไข", default="-")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.machine}"

class KPIMetric(models.Model):
    name = models.CharField(max_length=255, verbose_name="หัวข้อ KPI")
    category = models.CharField(max_length=100, verbose_name="หมวดหมู่") # Quality, Safety, Cost, etc.
    target = models.FloatField(verbose_name="เป้าหมาย")
    unit = models.CharField(max_length=50, verbose_name="หน่วย")
    weight = models.FloatField(verbose_name="น้ำหนัก")
    actual = models.FloatField(verbose_name="ผลลัพธ์ (Actual)")
    score = models.IntegerField(verbose_name="คะแนนที่ได้ (1-4)", default=0)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    @property
    def weighted_score(self):
        return self.weight * self.score
    
class MillReport(models.Model):
    # ตัวเลือกสำหรับสายการผลิต (Line)
    LINE_CHOICES = [
        ('A', 'Line A'),
        ('B', 'Line B'),
    ]

    # --- General Info ---
    date = models.DateField(verbose_name="วันที่")
    line = models.CharField(max_length=1, choices=LINE_CHOICES, verbose_name="สายการผลิต")

    # --- Production Data ---
    # แก้ไข: เพิ่ม blank=True, null=True เพื่อให้ฟอร์มไม่ error หากไม่ได้กรอกข้อมูลบางช่อง
    cane_weight = models.FloatField(default=0, blank=True, null=True, verbose_name="น้ำหนักอ้อย/วัน")
    target_crushing = models.FloatField(default=0, blank=True, null=True, verbose_name="เป้าหีบอ้อย/วัน")
    #reduced_capacity_hours = models.FloatField(default=0, blank=True, null=True, verbose_name="ชั่วโมงลดกำลังการผลิต")

    # --- KPIs: Extraction ---
    first_mill_extraction = models.FloatField(default=0, blank=True, null=True, verbose_name="1st Mill Extraction")
    reduced_pol_extraction = models.FloatField(default=0, blank=True, null=True, verbose_name="Reduced Pol Extraction")
    trash = models.FloatField(default=0, blank=True, null=True, verbose_name="trash")

    # --- KPIs: Quality ---
    cane_preparation_index = models.FloatField(default=0, blank=True, null=True, verbose_name="Cane Preparation Index")
    purity_drop = models.FloatField(default=0, blank=True, null=True, verbose_name="Purity Drop")
    bagasse_moisture = models.FloatField(default=0, blank=True, null=True, verbose_name="Bagasse Moisture")
    pol_bagasse = models.FloatField(default=0, blank=True, null=True, verbose_name="Pol % Bagasse")

    # --- KPIs: Process ---
    imbibition_cane = models.FloatField(default=0, blank=True, null=True, verbose_name="Imbibition % Cane")
    imbibition_fiber = models.FloatField(default=0, blank=True, null=True, verbose_name="Imbibition % Fiber")
    loss_bagasse = models.FloatField(default=0, blank=True, null=True, verbose_name="Loss in Bagasse")
    ccs = models.FloatField(default=0, blank=True, null=True, verbose_name="ccs")

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "รายงานลูกหีบ (Mill Report)"
        verbose_name_plural = "รายงานลูกหีบ (Mill Reports)"

    def __str__(self):
        return f"{self.date} - Line {self.line}"