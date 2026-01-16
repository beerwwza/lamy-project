import pandas as pd
import numpy as np
from datetime import datetime, time
from django.shortcuts import render, redirect
from django.db.models import Sum, Avg
from django.http import HttpResponse, JsonResponse
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import json
from django.core.serializers.json import DjangoJSONEncoder
from .models import BoilerOperationLog, ChengchenLog, TakumaLog, YoshimineLog, Banpong1Log, Banpong2Log, BoilerDailyKPI
from .forms import BoilerOperationForm, ChengchenForm, TakumaForm, YoshimineForm, Banpong1Form, Banpong2Form, BoilerDailyKPIForm
from .models import MillReport
from .forms import MillReportForm
from .models import MaintenanceLog, KPIMetric
from .forms import MaintenanceLogForm, KPIMetricForm


#def Home(request):
    #if request.method == 'POST':
        #data = request.POST.copy()
        #print('DATA: ',data)
        #name = data.get('ชื่อ')
        #employeeID = data.get('รหัสพนักงาน')
        #tel = data.get('เบอร์โทรศัพท์')
        #group = data.get('ฝ่าย')
        #department = data.get('แผนก')
        #print('ชื่อ: ',name)
        #print('รหัสพนักงาน: ',employeeID)
        #print('เบอร์โทรศัพท์: ',tel)
        #print('ฝ่าย: ',group)
        #print('แผนก: ',department)
        
        #newemployee = employee()
        #newemployee.name = name
        #newemployee.employeeID = employeeID
        #newemployee.tel = tel
        #newemployee.group = group
        #newemployee.department = department
        #newemployee.save()

    #return render(request, 'myapp/home.html')

# --- แก้ไขฟังก์ชัน Register ---
def register(request):
    context = {}
    if request.method == 'POST':
        data = request.POST.copy()
        
        # 1. รับค่าจากฟอร์มให้ครบ 8 ค่า
        username = data.get("username")         # 1. Username
        password = data.get("password")         # 2. Password
        email = data.get("email")               # 3. Email
        first_name = data.get("first_name")     # 4. ชื่อ-นามสกุล
        employeeID = data.get("employeeID")     # 5. รหัสพนักงาน
        tel = data.get("tel")                   # 6. เบอร์โทรศัพท์
        group = data.get("group")               # 7. ฝ่าย
        department = data.get("department")     # 8. แผนก

        # ตรวจสอบว่า Username ซ้ำหรือไม่
        if User.objects.filter(username=username).exists():
            context["user_taken"] = True
            context["message"] = "Username นี้ถูกใช้งานแล้ว"
            return render(request, "myapp/register.html", context)
            
        # สร้าง User ใหม่
        try:
            # สร้าง User หลัก (เก็บ Username, Email, Password, ชื่อ)
            new_user = User.objects.create_user(username=username, email=email, password=password)
            new_user.first_name = first_name
            new_user.save()

            # สร้าง Profile เพื่อเก็บข้อมูลเพิ่มเติม (รหัสพนักงาน, เบอร์, ฝ่าย, แผนก)
            # หมายเหตุ: ต้องมี models.Profile ตามข้อ 1
            profile = Profile(
                user=new_user,
                employeeID=employeeID,
                tel=tel,
                group=group,
                department=department
            )
            profile.save() # อย่าลืมวงเล็บ ()

            context['success'] = True
            return redirect("login")

        except Exception as e:
            print(e)
            context["error"] = "เกิดข้อผิดพลาดในการบันทึกข้อมูล"

    return render(request, "myapp/register.html", context)

def user_login(request):
    if request.method == 'POST':
        data = request.POST.copy()
        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)
        print(user, "username")

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง!!')
    return render(request, 'myapp/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'คุณได้ออกจากระบบแล้ว')
    return redirect('login')

#@login_required
#def table_employee(request):
    #if request.user.profile.user_type != 'admin':
        #return redirect('home')
    
    #Employee = employee.objects.all()
    #context = {'Employee':Employee}
    #return render(request,'myapp/tableemployee.html',context)

def detail_job(request,ID):
    Employee = employee.objects.get(id=ID)
    context = {'Employee':Employee}
    return render(request,'myapp/detail-job.html',context)

def dashboard(request):
    # ฟังก์ชันนี้จะเรียกไฟล์ template dashboard.html ที่เราเพิ่งแก้ไปมาแสดง
    return render(request, 'myapp/dashboard.html')

@login_required
def boiler(request):
    # Helper: ดึงข้อมูลล่าสุด
    def get_latest(model, date_field, time_field):
        return model.objects.order_by(f'-{date_field}', f'-{time_field}').first()

    # Helper: จัดรูปแบบข้อมูลสำหรับแสดงผล
    def format_boiler_data(obj, prefix, name):
        if not obj:
            return {
                'name': name,
                'status': 'Offline',
                'press': '-',
                'flow': '-',
                'temp': '-',
                'last_update': '-'
            }
        
        # กำหนดชื่อ Field ตาม Model ของแต่ละเครื่อง
        if prefix == 'jt':
            press_field = 'jt_steam_pressure'
            flow_field = 'jt_steam_flow'
            temp_field = 'jt_temp_steam'
        elif prefix in ['ch', 'tk']:
            press_field = f'{prefix}_steam_pressure'
            flow_field = f'{prefix}_steam_flow'
            temp_field = f'{prefix}_steam_temp'
        else: # yos, bp1, bp2
            press_field = f'{prefix}_main_steam_pressure'
            flow_field = f'{prefix}_main_steam_flow'
            temp_field = f'{prefix}_main_steam_temp'

        # ดึงค่า
        press = getattr(obj, press_field, 0)
        flow = getattr(obj, flow_field, 0)
        temp = getattr(obj, temp_field, 0)
        
        date_val = getattr(obj, f'{prefix}_date')
        time_val = getattr(obj, f'{prefix}_time')

        # Logic สถานะ (ตัวอย่าง: ถ้า Pressure > 2 ถือว่า Run)
        status = 'Running' if press and press > 2 else 'Offline'

        return {
            'name': name,
            'status': status,
            'press': press if press is not None else '-',
            'flow': flow if flow is not None else '-',
            'temp': temp if temp is not None else '-',
            'last_update': f"{date_val.strftime('%d/%m/%Y')} {time_val.strftime('%H:%M')}" if date_val and time_val else '-'
        }

    # 1. Boiler 20 Bar Group
    boilers_20bar = [
        format_boiler_data(get_latest(BoilerOperationLog, 'jt_date', 'jt_time'), 'jt', 'John Thomson'),
        format_boiler_data(get_latest(ChengchenLog, 'ch_date', 'ch_time'), 'ch', 'Chengchen'),
        format_boiler_data(get_latest(TakumaLog, 'tk_date', 'tk_time'), 'tk', 'Takuma'),
    ]

    # 2. Boiler 40 Bar Group
    boilers_40bar = [
        format_boiler_data(get_latest(YoshimineLog, 'yos_date', 'yos_time'), 'yos', 'Yoshimine'),
        format_boiler_data(get_latest(Banpong1Log, 'bp1_date', 'bp1_time'), 'bp1', 'Banpong 1'),
        format_boiler_data(get_latest(Banpong2Log, 'bp2_date', 'bp2_time'), 'bp2', 'Banpong 2'),
    ]

    # ข้อมูลสำหรับกราฟ (ใช้ของ JT เป็นตัวอย่าง หรือจะปรับออกก็ได้)
    logs = BoilerOperationLog.objects.order_by('jt_date', 'jt_time').last()
    graph_data = BoilerOperationLog.objects.order_by('jt_date', 'jt_time').all()[:24] 
    times = [log.jt_time.strftime('%H:%M') for log in graph_data] if graph_data else []
    pressure_data = [log.jt_steam_pressure for log in graph_data] if graph_data else []
    temp_data = [log.jt_temp_steam for log in graph_data] if graph_data else []
    o2_data = [log.jt_o2_gas for log in graph_data] if graph_data else []

    context = {
        'boilers_20bar': boilers_20bar,
        'boilers_40bar': boilers_40bar,
        'latest_log': logs,
        'chart_labels': json.dumps(times, cls=DjangoJSONEncoder),
        'chart_pressure': json.dumps(pressure_data, cls=DjangoJSONEncoder),
        'chart_temp': json.dumps(temp_data, cls=DjangoJSONEncoder),
        'chart_o2': json.dumps(o2_data, cls=DjangoJSONEncoder),
    }
    return render(request, 'myapp/boiler.html', context)


@login_required
def operation_dashboard(request):
    """
    ฟังก์ชันสำหรับแสดงหน้าจอรวม Operation ของเครื่องจักรทุกตัว
    """
    # Helper function เพื่อดึงค่าจาก Model อย่างปลอดภัย (ป้องกัน Error กรณีไม่มีข้อมูล)
    def get_val(obj, field, default="-"):
        return getattr(obj, field, default) if obj else default

    # ดึงข้อมูลล่าสุดของแต่ละเครื่อง (สมมติว่าใช้ Field name ตาม Pattern เดียวกับ John Thomson แต่เปลี่ยน Prefix)
    # ** หมายเหตุ: คุณต้องตรวจสอบชื่อ Field ใน models.py ของคุณให้ตรงกับด้านล่างนี้ **
    jt = BoilerOperationLog.objects.order_by('jt_date', 'jt_time').last()
    ch = ChengchenLog.objects.order_by('ch_date', 'ch_time').last() # สมมติว่ามี timestamp หรือ id ให้เรียง
    tk = TakumaLog.objects.order_by('tk_date', 'tk_time').last()
    yos = YoshimineLog.objects.order_by('yos_date', 'yos_time').last()
    bp1 = Banpong1Log.objects.order_by('bp1_date', 'bp1_time').last()
    bp2 = Banpong2Log.objects.order_by('bp2_date', 'bp2_time').last()

    # สร้าง Dictionary ข้อมูลเพื่อส่งไปแปลงเป็น JSON
    # หมายเหตุ: ผมใส่ชื่อ field สมมติไว้ (เช่น cc_steam_pressure) คุณต้องแก้ให้ตรงกับ Model จริงของคุณ
    machine_data = {
        'john_thomson': {
            'name': 'John Thomson',
            'press': get_val(jt, 'jt_steam_pressure'),
            'flow': get_val(jt, 'jt_steam_flow'),
            'temp': get_val(jt, 'jt_temp_steam'),
            'fw_flow': get_val(jt, 'jt_feed_water_flow', '-'), # Field สมมติ
            'dea_temp': get_val(jt, 'jt_deaerator_temp', '-'), # Field สมมติ
            'stack_temp': get_val(jt, 'jt_stack_temp', '-'),   # Field สมมติ
            'ph': get_val(jt, 'jt_ph', '-'),                   # Field สมมติ
            'bd_flow': get_val(jt, 'jt_blowdown_flow', '-')    # Field สมมติ
        },
        'chengchen': {
            'name': 'Chengchen',
            'press': get_val(ch, 'ch_steam_pressure'), # แก้ชื่อ field ให้ตรงกับ Model ChengchenLog
            'flow': get_val(ch, 'ch_steam_flow'),
            'temp': get_val(ch, 'ch_steam_temp'),
            'fw_flow': get_val(ch, 'ch_feed_water_flow'),
            'dea_temp': get_val(ch, 'ch_dea_temp'),
            'stack_temp': get_val(ch, 'ch_stack_temp'),
            'ph': get_val(ch, 'ch_ph_water'), 
            #'bd_flow': get_val(ch, ''),
        },
        'takuma': {
            'name': 'Takuma',
            'press': get_val(tk, 'tk_steam_pressure'), # แก้ชื่อ field ให้ตรงกับ Model takama
            'flow': get_val(tk, 'tk_steam_flow'),
            'temp': get_val(tk, 'tk_steam_temp'),
            'fw_flow': get_val(tk, 'tk_feed_water_flow'),
            'dea_temp': get_val(tk, 'tk_dea_temp'),
            'stack_temp': get_val(tk, 'tk_stack_temp'),
            'ph': get_val(tk, 'tk_ph_water'), 
        },
        'yoshimine': {
            'name': 'Yoshimine',
            'press': get_val(yos, 'yos_main_steam_pressure'), # แก้ชื่อ field ให้ตรงกับ Model
            'flow': get_val(yos, 'yos_main_steam_flow'),
            'temp': get_val(yos, 'yos_main_steam_temp'),
            'fw_flow': get_val(yos, 'yos_feed_water_flow'),
            'dea_temp': get_val(yos, 'yos_feed_water_in_temp'),
            'stack_temp': get_val(yos, 'yos_gas_exit_temp'),
            'ph': get_val(yos, 'yos_bagasse_moisture'),
            'bd_flow': get_val(yos,'yos_blowdown_flow'), 
        },
        'banpong1': {
            'name': 'Banpong 1',
            'press': get_val(bp1, 'bp1_main_steam_pressure'), # แก้ชื่อ field ให้ตรงกับ Model
            'flow': get_val(bp1, 'bp1_main_steam_flow'),
            'temp': get_val(bp1, 'bp1_main_steam_temp'),
            'fw_flow': get_val(bp1, 'bp1_feed_water_flow'),
            'dea_temp': get_val(bp1, 'bp1_feed_water_in_temp'),
            'stack_temp': get_val(bp1, 'bp1_ah1_gas_out_temp'),
            #'ph': get_val(bp1, 'bp1_ph_boiler'),
            'bd_flow': get_val(bp1,'bp1_bd_flow'), 
        },
        'banpong2': {
            'name': 'Banpong 2',
            'press': get_val(bp2, 'bp2_main_steam_pressure'), # แก้ชื่อ field ให้ตรงกับ Model
            'flow': get_val(bp2, 'bp2_main_steam_flow'),
            'temp': get_val(bp2, 'bp2_main_steam_temp'),
            'fw_flow': get_val(bp2, 'bp2_feed_water_flow'),
            'dea_temp': get_val(bp2, 'bp2_feed_water_in_temp'),
            'stack_temp': get_val(bp2, 'bp2_gas_exit_temp'),
            #'ph': get_val(bp2, 'bp2_ph_boiler'),
            'bd_flow': get_val(bp2,'bp2_bd_flow'), 
        },
    }

    context = {
        'machine_data_json': json.dumps(machine_data, cls=DjangoJSONEncoder)
    }
    return render(request, 'myapp/boiler_operation.html', context)

# --- Import Data Logic (Fixed Encoding & Dependency Check) ---
@login_required
def import_data(request):
    if request.method == 'POST' and request.FILES.get('file_upload'):
        file = request.FILES['file_upload']
        machine_type = request.POST.get('machine_type')
        
        # Configuration
        config = {
            'john_thomson': {'model': BoilerOperationLog, 'prefix': 'jt'},
            'chengchen': {'model': ChengchenLog, 'prefix': 'ch'},
            'takuma': {'model': TakumaLog, 'prefix': 'tk'},
            'yoshimine': {'model': YoshimineLog, 'prefix': 'yos'},
            'banpong1': {'model': Banpong1Log, 'prefix': 'bp1'},
            'banpong2': {'model': Banpong2Log, 'prefix': 'bp2'},
        }
        
        selected_config = config.get(machine_type)
        if not selected_config:
            messages.error(request, 'Invalid machine type selected')
            return redirect('operation_dashboard')

        try:
            df = None
            
            # Helper function to validate header
            def is_valid_header(dataframe):
                if dataframe is None or dataframe.empty: return False
                # คำค้นหาที่ควรเจอใน Header
                check_cols = ['วันที่', 'Date', 'Main Steam Flow', 'Steam Flow', 'เวลา', 'Time', 'Data']
                cols_upper = [str(c).upper().strip() for c in dataframe.columns]
                return any(c.upper() in cols_upper for c in check_cols)

            # กำหนดค่า NaN
            na_values = ['-', 'NaN', 'nan', '', ' ']

            # -------------------------------------------------------
            # 1. READ FILE LOGIC (Robust CSV/Excel Handling)
            # -------------------------------------------------------
            if file.name.endswith('.csv'):
                # ลอง Encoding หลายแบบ: utf-8-sig (Excel CSV), cp874 (Thai Windows), utf-8
                encodings_to_try = ['utf-8-sig', 'cp874', 'tis-620', 'utf-8']
                
                for encoding in encodings_to_try:
                    try:
                        file.seek(0) # Reset file pointer
                        # ลองอ่านบรรทัดแรก
                        temp_df = pd.read_csv(file, encoding=encoding, na_values=na_values)
                        
                        if is_valid_header(temp_df):
                            df = temp_df
                            break
                        
                        # ถ้าบรรทัดแรกไม่ใช่ Header ลองอ่านบรรทัดที่ 2
                        file.seek(0)
                        temp_df = pd.read_csv(file, header=1, encoding=encoding, na_values=na_values)
                        if is_valid_header(temp_df):
                            df = temp_df
                            break
                    except UnicodeDecodeError:
                        continue # ลอง encoding ถัดไป
                    except Exception:
                        continue

                if df is None:
                    raise Exception("ไม่สามารถอ่านไฟล์ CSV ได้ (Encoding Error) กรุณาลอง Save As CSV UTF-8")

            else: # .xlsx, .xls files
                try:
                    # เช็คว่ามี openpyxl หรือไม่
                    import openpyxl
                except ImportError:
                    raise Exception("Server ขาด Library 'openpyxl' กรุณาติดตั้ง: pip install openpyxl")

                # อ่าน Excel
                try:
                    df = pd.read_excel(file, na_values=na_values)
                    if not is_valid_header(df):
                        file.seek(0)
                        df = pd.read_excel(file, header=1, na_values=na_values)
                except Exception as e:
                    raise Exception(f"อ่านไฟล์ Excel ไม่สำเร็จ: {str(e)}")

            if df is None or df.empty:
                messages.error(request, "ไฟล์ว่างเปล่าหรือไม่พบ Header ที่ถูกต้อง")
                return redirect('operation_dashboard')

            # -------------------------------------------------------
            # 2. PRE-PROCESS & MAPPING
            # -------------------------------------------------------
            df.columns = df.columns.str.strip() 
            df = df.replace({np.nan: None})
            
            model_class = selected_config['model']
            prefix = selected_config['prefix']
            
            col_to_field_map = {}
            model_fields = model_class._meta.get_fields()
            
            def normalize_name(name):
                if not name: return ""
                name = str(name).lower()
                name = name.replace('.', '').replace('/', '').replace('#', '').replace(' ', '').replace('_', '')
                name = name.replace('pressure', 'press')
                name = name.replace('temperature', 'temp')
                name = name.replace('outlet', 'out')
                name = name.replace('inlet', 'in')
                name = name.replace('flowcontrolvalve', 'valve')
                name = name.replace('controlvalve', 'valve')
                return name

            # Mapping จาก Verbose Name
            field_lookup = {}
            for field in model_fields:
                if hasattr(field, 'verbose_name') and field.verbose_name:
                    norm_v_name = normalize_name(field.verbose_name)
                    field_lookup[norm_v_name] = field.name
            
            for col in df.columns:
                norm_col = normalize_name(col)
                
                # Direct Match
                if norm_col in field_lookup:
                    col_to_field_map[col] = field_lookup[norm_col]
                
                # Specific Mapping (Fallback)
                else:
                    if 'mainsteamtemp' in norm_col:
                        col_to_field_map[col] = f'{prefix}_main_steam_temp'
                    elif 'desuperheatflow' in norm_col:
                        col_to_field_map[col] = f'{prefix}_desuperheat_valve'
                    elif 'continousblowdown' in norm_col or 'continuousblowdown' in norm_col:
                        col_to_field_map[col] = f'{prefix}_cbd_valve'
                    elif 'date' == norm_col or 'วันที่' == norm_col:
                        col_to_field_map[col] = f'{prefix}_date'
                    elif 'time' == norm_col or 'เวลา' == norm_col or 'data' == norm_col: # เพิ่ม 'data'
                        col_to_field_map[col] = f'{prefix}_time'

            objects_to_create = []
            
            # -------------------------------------------------------
            # 3. CREATE OBJECTS
            # -------------------------------------------------------
            for index, row in df.iterrows():
                obj = model_class()
                has_date = False
                has_time = False
                
                for excel_col, db_field in col_to_field_map.items():
                    val = row.get(excel_col)
                    
                    if val is None: continue
                    
                    # Clean Strings
                    if isinstance(val, str):
                        val = val.strip()
                        if val == '' or val == '-': continue

                    # Handle Date
                    if 'date' in db_field:
                        if isinstance(val, str):
                            try:
                                if '-' in val:
                                    parts = val.split('-')
                                    if len(parts) == 3 and int(parts[0]) > 2400: # 2568 -> 2025
                                        val = f"{int(parts[0])-543}-{parts[1]}-{parts[2]}"
                                has_date = True
                            except: continue 
                        elif isinstance(val, (datetime, pd.Timestamp)):
                             has_date = True
                    
                    # Handle Time
                    elif 'time' in db_field:
                        if isinstance(val, str):
                            has_time = True
                        elif isinstance(val, (datetime, time)):
                            val = val if isinstance(val, time) else val.time()
                            has_time = True
                        
                    # Set Value
                    try:
                        # Convert string numbers (e.g. "1,200.50")
                        if 'date' not in db_field and 'time' not in db_field and isinstance(val, str):
                            val = float(val.replace(',', ''))
                        
                        setattr(obj, db_field, val)
                    except:
                        pass
                
                if has_date and has_time:
                    objects_to_create.append(obj)
            
            if objects_to_create:
                model_class.objects.bulk_create(objects_to_create)
                messages.success(request, f'Import สำเร็จ: {len(objects_to_create)} รายการ ({machine_type})')
            else:
                messages.warning(request, f'ไม่พบข้อมูลที่นำเข้าได้ ตรวจสอบคอลัมน์: {list(df.columns)}')
                
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            
    return redirect('operation_dashboard')


@login_required
def boiler_operation_add(request):
    if request.method == 'POST':
        form = BoilerOperationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler') 
    else:
        form = BoilerOperationForm()
    return render(request, 'myapp/boiler_operation_form.html', {'form': form})

# (Keep other views: yoshimine_operation_add, banpong1_operation_add, chengchen_operation_add, etc.)
@login_required
def yoshimine_operation_add(request):
    if request.method == 'POST':
        form = YoshimineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler')
    else:
        form = YoshimineForm()
    return render(request, 'myapp/yoshimine_form.html', {'form': form})

@login_required
def banpong1_operation_add(request):
    if request.method == 'POST':
        form = Banpong1Form(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler')
    else:
        form = Banpong1Form()
    return render(request, 'myapp/banpong1_form.html', {'form': form})

@login_required
def chengchen_operation_add(request):
    if request.method == 'POST':
        form = ChengchenForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler')
    else:
        form = ChengchenForm()
    return render(request, 'myapp/chengchen_form.html', {'form': form})

@login_required
def takuma_operation_add(request):
    if request.method == 'POST':
        form = TakumaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler')
    else:
        form = TakumaForm()
    return render(request, 'myapp/takuma_form.html', {'form': form})

@login_required
def banpong2_operation_add(request):
    if request.method == 'POST':
        form = Banpong2Form(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler')
    else:
        form = Banpong2Form()
    return render(request, 'myapp/banpong2_form.html', {'form': form})

@login_required
def boiler(request):
    # 1. ดึงข้อมูล KPI ล่าสุดมาแสดงผลตัวเลข (Cards)
    latest_kpi = BoilerDailyKPI.objects.order_by('-date').first()

    # 2. ดึงข้อมูลย้อนหลัง 7 วันเพื่อทำกราฟ (เรียงตามวันที่)
    history_kpi = BoilerDailyKPI.objects.order_by('-date')[:7]
    history_kpi = reversed(list(history_kpi)) # กลับด้านให้เรียงจาก อดีต -> ปัจจุบัน

    # 3. เตรียมข้อมูล Array สำหรับกราฟ
    dates = []
    press_20 = []
    flow_20 = []
    press_40 = []
    flow_40 = []

    for kpi in history_kpi:
        # แปลงวันที่เป็นรูปแบบสั้น (เช่น 05/01)
        dates.append(kpi.date.strftime('%d/%m'))
        press_20.append(kpi.pressure_20bar or 0)
        flow_20.append(kpi.flow_20bar or 0)
        press_40.append(kpi.pressure_40bar or 0)
        flow_40.append(kpi.flow_40bar or 0)

    # Context ส่งไปที่ Template
    context = {
        'latest_kpi': latest_kpi,
        # แปลงข้อมูล List เป็น JSON String เพื่อให้ JavaScript นำไปใช้ได้
        'chart_dates': json.dumps(dates, cls=DjangoJSONEncoder),
        'chart_press_20': json.dumps(press_20, cls=DjangoJSONEncoder),
        'chart_flow_20': json.dumps(flow_20, cls=DjangoJSONEncoder),
        'chart_press_40': json.dumps(press_40, cls=DjangoJSONEncoder),
        'chart_flow_40': json.dumps(flow_40, cls=DjangoJSONEncoder),
    }
    return render(request, 'myapp/boiler.html', context)

@login_required
def boiler_kpi_form(request):    
    if request.method == 'POST':
        form = BoilerDailyKPIForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "บันทึกข้อมูล KPI เรียบร้อยแล้ว")
            return redirect('boiler')
        else:
            messages.error(request, "เกิดข้อผิดพลาด กรุณาตรวจสอบข้อมูล")
            print(form.errors) # ปริ้น Error ออกมาดูใน Terminal ถ้าบันทึกไม่ได้
    else:
        form = BoilerDailyKPIForm()
    
    return render(request, 'myapp/boiler_kpi_form.html', {'form': form})


@login_required
def maintenance_dashboard(request):
    logs = MaintenanceLog.objects.all().order_by('-date')
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'date': log.date.strftime('%d/%m/%Y') if log.date else "-",
            'machine': log.machine,
            'dept': log.dept,
            'problem': log.problem,
            'cause': log.cause or "-",
            'solution': log.solution or "-",
            'downtimeStop': log.downtime_stop or 0,
            'downtimeReduced': log.downtime_reduced or 0,
            'downtimeNonStop': log.downtime_non_stop or 0,
            'category': log.category,
            'isLeak': log.is_leak,
            'sparePart': log.spare_part,
            'qty': log.qty,
            'reporter': log.reporter,
            'resolver': log.resolver,
        })

    kpis = KPIMetric.objects.all()
    kpi_data = []
    for k in kpis:
        kpi_data.append({
            'id': k.id,
            'name': k.name,
            'category': k.category,
            'target': k.target,
            'unit': k.unit,
            'weight': k.weight,
            'actual': k.actual,
            'score': k.score,
            'weightedScore': k.weight * k.score
        })

    context = {
        'logs_json': json.dumps(logs_data, cls=DjangoJSONEncoder),
        'kpi_json': json.dumps(kpi_data, cls=DjangoJSONEncoder),
    }
    return render(request, 'myapp/maintenance_dashboard.html', context)

@login_required
def maintenance_log_add(request):
    if request.method == 'POST':
        form = MaintenanceLogForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('maintenance_dashboard')
    else:
        form = MaintenanceLogForm()
    return render(request, 'myapp/maintenance_log_form.html', {'form': form})

@login_required
def maintenance_kpi_metric_add(request):
    if request.method == 'POST':
        form = KPIMetricForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('maintenance_dashboard')
    else:
        form = KPIMetricForm()
    return render(request, 'myapp/maintenance_kpi_metric_form.html', {'form': form})

def mill(request):
    # (Same as provided logic)
    latest_a = MillReport.objects.filter(line='A').order_by('-date', '-created_at').first()
    sum_cane_a = MillReport.objects.filter(line='A').aggregate(total=Sum('cane_weight'))['total'] or 0
    avg_a = MillReport.objects.filter(line='A').aggregate(
        first_mill_extraction__avg=Avg('first_mill_extraction'),
        reduced_pol_extraction__avg=Avg('reduced_pol_extraction'),
        purity_drop__avg=Avg('purity_drop'),
        imbibition_cane__avg=Avg('imbibition_cane'),
        imbibition_fiber__avg=Avg('imbibition_fiber'),
        bagasse_moisture__avg=Avg('bagasse_moisture'),
        cane_preparation_index__avg=Avg('cane_preparation_index'),
        pol_bagasse__avg=Avg('pol_bagasse'),
        loss_bagasse__avg=Avg('loss_bagasse'),
        ccs__avg=Avg('ccs'),
        trash__avg=Avg('trash')
    )

    latest_b = MillReport.objects.filter(line='B').order_by('-date', '-created_at').first()
    sum_cane_b = MillReport.objects.filter(line='B').aggregate(total=Sum('cane_weight'))['total'] or 0
    avg_b = MillReport.objects.filter(line='B').aggregate(
        first_mill_extraction__avg=Avg('first_mill_extraction'),
        reduced_pol_extraction__avg=Avg('reduced_pol_extraction'),
        purity_drop__avg=Avg('purity_drop'),
        imbibition_cane__avg=Avg('imbibition_cane'),
        imbibition_fiber__avg=Avg('imbibition_fiber'),
        bagasse_moisture__avg=Avg('bagasse_moisture'),
        cane_preparation_index__avg=Avg('cane_preparation_index'),
        pol_bagasse__avg=Avg('pol_bagasse'),
        loss_bagasse__avg=Avg('loss_bagasse'),
        ccs__avg=Avg('ccs'),
        trash__avg=Avg('trash')
    )

    def format_data(report, total_sum_cane, averages):
        if not averages: averages = {}
        if not report:
            if total_sum_cane > 0:
                 return {
                    'meta': {
                        'date': '-',
                        'cane_weight': 0,
                        'sum_cane_weight': total_sum_cane,
                        'target_crushing': 0,
                        
                    },
                    'kpis': {} 
                 }
            return None
            
        return {
            'meta': {
                'date': report.date.strftime('%d/%m/%Y'),
                'cane_weight': report.cane_weight,
                'sum_cane_weight': total_sum_cane,
                'target_crushing': report.target_crushing,
                
            },
            'kpis': {
                1: {'current': report.first_mill_extraction, 'average': averages.get('first_mill_extraction__avg') or 0},
                2: {'current': report.reduced_pol_extraction, 'average': averages.get('reduced_pol_extraction__avg') or 0},
                3: {'current': report.purity_drop, 'average': averages.get('purity_drop__avg') or 0},
                4: {'current': report.imbibition_cane, 'average': averages.get('imbibition_cane__avg') or 0},
                5: {'current': report.imbibition_fiber, 'average': averages.get('imbibition_fiber__avg') or 0},
                6: {'current': report.bagasse_moisture, 'average': averages.get('bagasse_moisture__avg') or 0},
                7: {'current': report.cane_preparation_index, 'average': averages.get('cane_preparation_index__avg') or 0},
                8: {'current': report.pol_bagasse, 'average': averages.get('pol_bagasse__avg') or 0},
                9: {'current': report.loss_bagasse, 'average': averages.get('loss_bagasse__avg') or 0},
                10: {'current': report.ccs, 'average': averages.get('ccs__avg') or 0},
                11: {'current': report.trash, 'average': averages.get('trash__avg') or 0},
            }
        }

    context = {
        'data_a': json.dumps(format_data(latest_a, sum_cane_a, avg_a)),
        'data_b': json.dumps(format_data(latest_b, sum_cane_b, avg_b)),
    }
    
    return render(request, 'myapp/mill.html', context)

def mill_report(request):
    if request.method == 'POST':
        form = MillReportForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('mill') 
        else:
            print("Form errors:", form.errors)
    else:
        form = MillReportForm()
    return render(request, 'myapp/mill_report.html', {'form': form})

# 3. View สำหรับ Import Data
@login_required
def mill_import(request):
    if request.method == 'POST' and request.FILES.get('file'):
        line_selected = request.POST.get('line', 'A')
        uploaded_file = request.FILES['file']
        
        try:
            # 1. ตรวจสอบและอ่านไฟล์ (Auto-detect Encoding & File Type)
            df = None
            detected_encoding = None
            
            if uploaded_file.name.lower().endswith('.csv'):
                # เพิ่ม Encoding ภาษาไทยให้ครบถ้วน
                encodings_to_try = ['utf-8-sig', 'utf-8', 'cp874', 'tis-620', 'iso-8859-11', 'windows-874', 'latin-1']
                
                for encoding in encodings_to_try:
                    try:
                        uploaded_file.seek(0)
                        # ลองอ่าน 10 บรรทัดแรกเพื่อเช็ค Encoding
                        pd.read_csv(uploaded_file, header=None, encoding=encoding, nrows=10)
                        detected_encoding = encoding
                        break 
                    except Exception:
                        continue 
                
                if detected_encoding:
                    # ถ้าเจอ Encoding ที่ถูกต้อง ให้อ่านไฟล์ CSV
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, header=None, encoding=detected_encoding)
                else:
                    # Fallback: ถ้าอ่าน CSV ไม่ได้เลย อาจเป็นไฟล์ Excel ที่ตั้งชื่อเป็น .csv
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_excel(uploaded_file, header=None)
                    except Exception:
                        raise Exception("ไม่สามารถอ่านไฟล์ CSV ได้ (Encoding ไม่รองรับ หรือรูปแบบไฟล์ไม่ถูกต้อง)")
            
            else:
                # กรณีไฟล์ Excel (.xlsx, .xls)
                try:
                    df = pd.read_excel(uploaded_file, header=None)
                except Exception as e:
                     raise Exception(f"อ่านไฟล์ Excel ไม่สำเร็จ: {str(e)}")

            # 2. ค้นหาบรรทัด Header (หาคำว่า "Date" หรือ "วันที่")
            header_idx = -1
            if df is not None:
                for i, row in df.iterrows():
                    row_str = row.astype(str).str.lower().tolist()
                    if 'date' in row_str or 'วันที่' in row_str:
                        header_idx = i
                        break
            
            if header_idx == -1:
                messages.error(request, "ไม่พบคอลัมน์ 'Date' หรือ 'วันที่' ในไฟล์")
                return redirect('mill')

            # 3. จัดการ Header และอ่านข้อมูลจริง
            # ตั้งบรรทัดที่หาเจอเป็น Header
            df.columns = df.iloc[header_idx] 
            df = df.iloc[header_idx+1:].reset_index(drop=True)

            # 4. Clean Header (ลบช่องว่างหน้าหลังชื่อคอลัมน์ออก)
            df.columns = df.columns.astype(str).str.strip()
            
            # ลบแถวที่ไม่มีวันที่
            date_col_name = next((col for col in df.columns if col.lower() in ['date', 'วันที่']), None)
            if date_col_name:
                df = df.dropna(subset=[date_col_name])
            else:
                messages.error(request, "ไม่พบคอลัมน์วันที่ในการประมวลผล")
                return redirect('mill')

            count = 0
            for index, row in df.iterrows():
                # --- จัดการเรื่องวันที่ ---
                date_val = row.get(date_col_name)
                date_obj = None
                
                if pd.isna(date_val): continue

                if isinstance(date_val, (datetime, pd.Timestamp)):
                    date_obj = date_val.date()
                elif isinstance(date_val, str):
                    date_val = date_val.strip()
                    try:
                        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y'):
                            try:
                                date_obj = datetime.strptime(date_val, fmt).date()
                                break
                            except ValueError:
                                pass
                    except:
                        pass
                
                if not date_obj: continue

                # แก้ไขปี พ.ศ. เป็น ค.ศ.
                if date_obj.year > 2400:
                    try:
                        date_obj = date_obj.replace(year=date_obj.year - 543)
                    except ValueError:
                        continue

                # --- Helper Function แปลงตัวเลข ---
                def get_num(col_name_part):
                    col_match = [c for c in df.columns if col_name_part.lower() in c.lower()]
                    if col_match:
                        val = row.get(col_match[0])
                        if isinstance(val, str):
                            val = val.replace(',', '')
                        return pd.to_numeric(val, errors='coerce') or 0
                    return 0

                # --- บันทึกข้อมูลลง Database ---
                MillReport.objects.update_or_create(
                    date=date_obj,
                    line=line_selected,
                    defaults={
                        'cane_weight': get_num('น้ำหนักอ้อย'),
                        'target_crushing': get_num('เป้าหีบอ้อย'),
                        
                        'first_mill_extraction': get_num('1st Mill Extraction'),
                        'reduced_pol_extraction': get_num('Reduced Pol Extraction'),
                        
                        'cane_preparation_index': get_num('Cane Preparation Index'),
                        'purity_drop': get_num('Purity Drop'),
                        'bagasse_moisture': get_num('Bagasse Moisture'),
                        'pol_bagasse': get_num('Pol % Bagasse'),
                        
                        'imbibition_cane': get_num('Imbibition % Cane'),
                        'imbibition_fiber': get_num('Imbibition % Fiber'),
                        'loss_bagasse': get_num('Loss in Bagasse'),
                        
                    
                        
                        'ccs': get_num('CCS') if get_num('CCS') else 0,
                        'trash': get_num('Trash') if get_num('Trash') else 0,
                    }
                )
                count += 1
            
            messages.success(request, f"Import ข้อมูลสำเร็จ {count} รายการ (Line {line_selected})")
            return redirect('mill')

        except Exception as e:
            print(f"Error: {e}")
            messages.error(request, f"เกิดข้อผิดพลาด: {str(e)}")
            return redirect('mill')

    return redirect('mill')