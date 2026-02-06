import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from django.shortcuts import render, redirect
from django.db.models import Sum, Avg, Count
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

@login_required
def dashboard(request):
    # 1. Milling Data (Latest)
    mill_obj = MillReport.objects.order_by('-date').first()
    mill_data = {
        'cane_weight': f"{mill_obj.cane_weight:,.0f}" if mill_obj and mill_obj.cane_weight else "0",
        'ccs': f"{mill_obj.ccs:.2f}" if mill_obj and mill_obj.ccs else "0.00",
        'trash': f"{mill_obj.trash:.2f}" if mill_obj and mill_obj.trash else "0.00",
        'purity_drop': f"{mill_obj.purity_drop:.2f}" if mill_obj and mill_obj.purity_drop else "0.00",
    }

    # 2. Boiler Data (Yoshimine as Example)
    boiler_obj = YoshimineLog.objects.order_by('-yos_date', '-yos_time').first()
    boiler_data = {
        'steam_flow': f"{boiler_obj.yos_main_steam_flow:.1f}" if boiler_obj and boiler_obj.yos_main_steam_flow else "0.0",
        'pressure': f"{boiler_obj.yos_main_steam_pressure:.1f}" if boiler_obj and boiler_obj.yos_main_steam_pressure else "0.0",
        'temp': f"{boiler_obj.yos_main_steam_temp:.0f}" if boiler_obj and boiler_obj.yos_main_steam_temp else "0",
        'eco': f"{boiler_obj.yos_eco_out_temp:.0f}" if boiler_obj and boiler_obj.yos_eco_out_temp else "0",
    }

    # 3. Maintenance Data (Latest) & 4. Lathe Data (Latest)
    # Since MaintenanceLog is transactional, we might want "Today's Stats" or just "Latest Ticket"
    # For dashboard summary, let's show "Today's Downtime" if available, else 0
    today = datetime.now().date()
    
    # Maintenance (Exclude Lathe)
    maint_qs = MaintenanceLog.objects.filter(date=today).exclude(dept='โรงกลึง')
    maint_downtime = maint_qs.aggregate(Sum('downtime_stop'))['downtime_stop__sum'] or 0
    maint_tickets = maint_qs.count()

    # Lathe (Dept = 'โรงกลึง')
    lathe_qs = MaintenanceLog.objects.filter(date=today, dept='โรงกลึง')
    lathe_downtime = lathe_qs.aggregate(Sum('downtime_stop'))['downtime_stop__sum'] or 0
    lathe_jobs = lathe_qs.count()

    context = {
        'mill': mill_data,
        'boiler': boiler_data,
        'maint': {
            'downtime': maint_downtime,
            'tickets': maint_tickets
        },
        'lathe': {
            'downtime': lathe_downtime,
            'jobs': lathe_jobs
        }
    }
    return render(request, 'myapp/dashboard.html', context)

@login_required
def dashboard_api(request):
    department = request.GET.get('department')
    metric = request.GET.get('metric')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not all([department, metric]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    # Date Filtering
    try:
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
             # Default to last 7 days
            start = datetime.now().date() - pd.Timedelta(days=7)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end = datetime.now().date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    data = []
    labels = []

    if department == 'milling':
        qs = MillReport.objects.filter(date__range=[start, end]).order_by('date')
        
        # Mapping metric to field
        field_map = {
            'cane_weight': 'cane_weight',
            'ccs': 'ccs',
            'trash': 'trash',
            'purity': 'purity_drop'
        }
        field = field_map.get(metric)
        if field:
            for item in qs:
                val = getattr(item, field, 0)
                labels.append(item.date.strftime('%Y-%m-%d'))
                data.append(val or 0)

    elif department == 'boiler':
        # Using Yoshimine as representative
        # Note: Logs are frequent (hourly?), so we should probably AVG per day for the graph
        # OR just show all data points if range is small.
        # Let's Aggregate by Day for clarity in "History"
        
        qs = YoshimineLog.objects.filter(yos_date__range=[start, end])
        
        field_map = {
            'steam_flow': 'yos_main_steam_flow',
            'pressure': 'yos_main_steam_pressure',
            'temp': 'yos_main_steam_temp',
            'eco': 'yos_eco_out_temp'
        }
        field = field_map.get(metric)

        if field:
            # Aggregate avg per day
            daily_data = qs.values('yos_date').annotate(avg_val=Avg(field)).order_by('yos_date')
            for item in daily_data:
                labels.append(item['yos_date'].strftime('%Y-%m-%d'))
                data.append(round(item['avg_val'] or 0, 2))

    elif department == 'maintenance':
        qs = MaintenanceLog.objects.filter(date__range=[start, end]).exclude(dept='โรงกลึง')
        
        if metric == 'downtime':
             daily_data = qs.values('date').annotate(total=Sum('downtime_stop')).order_by('date')
             for item in daily_data:
                labels.append(item['date'].strftime('%Y-%m-%d'))
                data.append(item['total'])
        elif metric == 'tickets':
             daily_data = qs.values('date').annotate(count=Count('id')).order_by('date')
             for item in daily_data:
                labels.append(item['date'].strftime('%Y-%m-%d'))
                data.append(item['count'])

    elif department == 'lathe':
        qs = MaintenanceLog.objects.filter(date__range=[start, end], dept='โรงกลึง')
        
        if metric == 'downtime':
             daily_data = qs.values('date').annotate(total=Sum('downtime_stop')).order_by('date')
             for item in daily_data:
                labels.append(item['date'].strftime('%Y-%m-%d'))
                data.append(item['total'])
        elif metric == 'jobs':
             daily_data = qs.values('date').annotate(count=Count('id')).order_by('date')
             for item in daily_data:
                labels.append(item['date'].strftime('%Y-%m-%d'))
                data.append(item['count'])

    return JsonResponse({
        'labels': labels,
        'data': data,
        'metric_label': metric.replace('_', ' ').title()
    })


@login_required
def boiler_history_api(request):
    machine = request.GET.get('machine')
    metric = request.GET.get('metric')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not all([machine, metric]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    # 1. Date Parsing
    try:
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start = datetime.now().date() - timedelta(days=7)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end = datetime.now().date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # 2. Config & Mapping
    # Structure: machine_key: (ModelClass, prefix)
    config = {
        'john_thomson': (BoilerOperationLog, 'jt'),
        'chengchen': (ChengchenLog, 'ch'),
        'takuma': (TakumaLog, 'tk'),
        'yoshimine': (YoshimineLog, 'yos'),
        'banpong1': (Banpong1Log, 'bp1'),
        'banpong2': (Banpong2Log, 'bp2'),
    }

    if machine not in config:
        return JsonResponse({'error': 'Invalid machine'}, status=400)

    model_class, prefix = config[machine]

    # Map generic metric names to specific DB fields
    # metric input ex: 'press', 'flow', 'temp', 'fw_flow'
    field_map = {
        'press': f'{prefix}_steam_pressure' if prefix in ['jt','ch','tk'] else f'{prefix}_main_steam_pressure',
        'flow': f'{prefix}_steam_flow' if prefix in ['jt','ch','tk'] else f'{prefix}_main_steam_flow',
        'temp': f'{prefix}_steam_temp' if prefix in ['jt','ch','tk'] else f'{prefix}_main_steam_temp',
        'fw_flow': f'{prefix}_feed_water_flow',
        'dea_temp': f'{prefix}_temp_deaerator' if prefix == 'jt' else (f'{prefix}_dea_temp' if prefix in ['ch','tk'] else f'{prefix}_feed_water_in_temp'), # Yos/BP uses feed_water_in_temp for Dea? Let's check model... Yos: feed_water_in_temp ok.
        'stack_temp': f'{prefix}_temp_gas_stack' if prefix == 'jt' else (f'{prefix}_stack_temp' if prefix in ['ch','tk'] else (f'{prefix}_dc_gas_out_temp' if prefix == 'yos' else f'{prefix}_ah1_gas_out_temp')),
        'ph': f'{prefix}_ph_boiler' if prefix == 'jt' else (f'{prefix}_ph_water' if prefix in ['ch','tk'] else f'{prefix}_bagasse_moisture'), # Placeholder for others if not present
        'bd_flow': f'{prefix}_blowdown_flow' if prefix == 'yos' else f'{prefix}_bd_flow',
    }
    
    # Specific fix for JT ph/tds/others if needed, but generic logic covers most.
    # Note: 'ph' for Yos/BP might not exist or be different? 
    # Yos Model: No pH field visible in previous `view_file` (checked lines 102-194). 
    # Wait, Yos has 'yos_bagasse_moisture' mapped in `operation_dashboard`? 
    # Line 421 of views.py: 'ph': get_val(yos, 'yos_bagasse_moisture'), <- User's existing code used this, I will stick to it or return specific failure.

    # Try mapped fields first, then direct attribute
    db_field = field_map.get(metric)
    if not db_field:
        # Security check: ensure the field actually exists on the model
        try:
            model_class._meta.get_field(metric)
            db_field = metric
        except:
            return JsonResponse({'error': f'Invalid metric: {metric}'}, status=400)
    
    data = []
    labels = []

    # 3. Query
    if db_field:
        date_field = f'{prefix}_date'
        time_field = f'{prefix}_time'
        
        # Order by Date, Time
        qs = model_class.objects.filter(**{f'{date_field}__range': [start, end]}).order_by(date_field, time_field)
        
        for item in qs:
            d = getattr(item, date_field)
            t = getattr(item, time_field)
            val = getattr(item, db_field, 0)
            
            if d and t:
                # Combine for chart label
                full_dt = datetime.combine(d, t)
                labels.append(full_dt.strftime('%Y-%m-%d %H:%M'))
                data.append(val if val is not None else 0)

    label_map = {
        'press': 'Steam Pressure (Bar)',
        'flow': 'Steam Flow (T/H)',
        'temp': 'Steam Temperature (°C)',
        'fw_flow': 'Feed Water Flow (T/H)',
        'dea_temp': 'Deaerator Temp (°C)',
        'stack_temp': 'Stack Temp (°C)',
        'ph': 'pH / Moisture',
        'bd_flow': 'Blowdown Flow (T/H)'
    }

    return JsonResponse({
        'labels': labels,
        'data': data,
        'machine': machine,
        'metric': metric,
        'metric_label': label_map.get(metric, metric.title())
    })

# --- Boiler Overview (Split Lines) ---
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

        # Logic สถานะ (ตัวอย่าง: ถ้า Pressure > 5 ถือว่า Run)
        status = 'Running' if press and press > 5 else 'Offline'

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
    def get_val(obj, field, default="-"):
        return getattr(obj, field, default) if obj else default

    # Helper to get all fields dynamically
    def get_all_fields(obj, prefix):
        if not obj: return []
        fields_data = []
        # Exclude internal/header fields
        exclude = ['id', f'{prefix}_date', f'{prefix}_time', 'created_at', 'updated_at', 'yos_created_at', 'tk_created_at', 'ch_created_at', 'bp1_created_at', 'bp2_created_at', 'jt_created_at']
        
        for field in obj._meta.fields:
            if field.name in exclude: continue
            
            # Get values
            val = getattr(obj, field.name)
            if val is None: val = "-"
            elif isinstance(val, float): val = round(val, 2)
            
            # Determine unit from verbose name (simple heuristic or just show label)
            label = field.verbose_name
            
            fields_data.append({
                'name': field.name,
                'label': label,
                'value': val
            })
        return fields_data

    jt = BoilerOperationLog.objects.order_by('jt_date', 'jt_time').last()
    ch = ChengchenLog.objects.order_by('ch_date', 'ch_time').last()
    tk = TakumaLog.objects.order_by('tk_date', 'tk_time').last()
    yos = YoshimineLog.objects.order_by('yos_date', 'yos_time').last()
    bp1 = Banpong1Log.objects.order_by('bp1_date', 'bp1_time').last()
    bp2 = Banpong2Log.objects.order_by('bp2_date', 'bp2_time').last()

    machine_data = {
        'john_thomson': {
            'name': 'John Thomson',
            'press': get_val(jt, 'jt_steam_pressure'),
            'flow': get_val(jt, 'jt_steam_flow'),
            'temp': get_val(jt, 'jt_temp_steam'),
            'all_fields': get_all_fields(jt, 'jt')
        },
        'chengchen': {
            'name': 'Chengchen',
            'press': get_val(ch, 'ch_steam_pressure'),
            'flow': get_val(ch, 'ch_steam_flow'),
            'temp': get_val(ch, 'ch_steam_temp'),
            'all_fields': get_all_fields(ch, 'ch')
        },
        'takuma': {
            'name': 'Takuma',
            'press': get_val(tk, 'tk_steam_pressure'),
            'flow': get_val(tk, 'tk_steam_flow'),
            'temp': get_val(tk, 'tk_steam_temp'),
            'all_fields': get_all_fields(tk, 'tk')
        },
        'yoshimine': {
            'name': 'Yoshimine',
            'press': get_val(yos, 'yos_main_steam_pressure'),
            'flow': get_val(yos, 'yos_main_steam_flow'),
            'temp': get_val(yos, 'yos_main_steam_temp'),
            'all_fields': get_all_fields(yos, 'yos')
        },
        'banpong1': {
            'name': 'Banpong 1',
            'press': get_val(bp1, 'bp1_main_steam_pressure'),
            'flow': get_val(bp1, 'bp1_main_steam_flow'),
            'temp': get_val(bp1, 'bp1_main_steam_temp'),
            'all_fields': get_all_fields(bp1, 'bp1')
        },
        'banpong2': {
            'name': 'Banpong 2',
            'press': get_val(bp2, 'bp2_main_steam_pressure'),
            'flow': get_val(bp2, 'bp2_main_steam_flow'),
            'temp': get_val(bp2, 'bp2_main_steam_temp'),
            'all_fields': get_all_fields(bp2, 'bp2')
        },
    }

    context = {
        'machine_data_json': json.dumps(machine_data, cls=DjangoJSONEncoder)
    }
    return render(request, 'myapp/boiler_operation.html', context)

# --- Import Data Logic (Fixed: NOT NULL constraint failed) ---
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
            # 1. READ FILE LOGIC
            df = None
            def is_valid_header(dataframe):
                # ตรวจสอบคอลัมน์สำคัญ (Case Insensitive)
                check_cols = ['Main Steam Flow', 'Steam Flow', 'Pressure', 'Temp', 'วันที่', 'Date']
                cols_upper = [str(c).upper().strip() for c in dataframe.columns]
                return any(any(k.upper() in c for k in check_cols) for c in cols_upper)

            # กำหนดค่าที่ควรอ่านเป็น NaN
            na_values = ['-', 'NaN', 'nan', '', ' ', 'NaT', 'None']

            if file.name.endswith('.csv'):
                encodings = ['utf-8-sig', 'utf-8', 'cp874', 'tis-620']
                for encoding in encodings:
                    try:
                        file.seek(0)
                        # Try reading header at row 0, 1, 2
                        for i in range(3):
                            try:
                                temp_df = pd.read_csv(file, header=i, encoding=encoding, na_values=na_values)
                                if is_valid_header(temp_df):
                                    df = temp_df
                                    break
                            except: pass
                            file.seek(0)
                        if df is not None: break
                    except UnicodeDecodeError: continue
            else:
                # Excel
                for i in range(3):
                    try:
                        file.seek(0)
                        temp_df = pd.read_excel(file, header=i, na_values=na_values)
                        if is_valid_header(temp_df):
                            df = temp_df
                            break
                    except Exception: pass
            
            if df is None:
                raise Exception("ไม่สามารถอ่านไฟล์ได้ กรุณาตรวจสอบ Header (Date, Time, Steam Flow)")

            # 2. CLEAN DATA
            df.columns = df.columns.str.strip() 
            # แทนค่า NaN/NaT เป็น None
            df = df.where(pd.notnull(df), None)
            
            model_class = selected_config['model']
            prefix = selected_config['prefix']
            
            # 3. MAPPING LOGIC
            col_to_field_map = {}
            model_fields = model_class._meta.get_fields()
            
            def normalize_name(name):
                if not name: return ""
                name = str(name).lower()
                name = name.replace('.', '').replace('/', '').replace('#', '').replace(' ', '').replace('_', '').replace('\n', '')
                name = name.replace('pressure', 'press').replace('temperature', 'temp')
                name = name.replace('outlet', 'out').replace('inlet', 'in')
                name = name.replace('flowcontrolvalve', 'valve').replace('controlvalve', 'valve')
                name = name.replace('continuous', '').replace('continous', '')
                return name

            field_lookup = {}
            for field in model_fields:
                if hasattr(field, 'verbose_name') and field.verbose_name:
                    norm_v_name = normalize_name(field.verbose_name)
                    field_lookup[norm_v_name] = field.name
            
            for col in df.columns:
                norm_col = normalize_name(col)
                if norm_col in field_lookup:
                    col_to_field_map[col] = field_lookup[norm_col]
                else:
                    # Specific Mapping
                    if 'steamflow' in norm_col and 'main' in norm_col: col_to_field_map[col] = f'{prefix}_main_steam_flow'
                    elif 'mainsteamtemp' in norm_col: col_to_field_map[col] = f'{prefix}_main_steam_temp'
                    elif 'desuperheatflow' in norm_col: col_to_field_map[col] = f'{prefix}_desuperheat_valve'
                    elif 'blowdownflow' in norm_col and ('continous' in norm_col or 'cbd' in norm_col): col_to_field_map[col] = f'{prefix}_cbd_valve'
                    elif 'blowdownflow' in norm_col: col_to_field_map[col] = f'{prefix}_blowdown_flow' if prefix == 'yos' else f'{prefix}_bd_flow'
                    
                    if 'date' == norm_col or 'วันที่' == norm_col: col_to_field_map[col] = f'{prefix}_date'
                    elif 'time' == norm_col or 'เวลา' == norm_col or 'data' == norm_col: col_to_field_map[col] = f'{prefix}_time'

            # 4. CREATE OBJECTS
            objects_to_create = []
            
            for index, row in df.iterrows():
                # FIX: Skip Control Row (Check value in first few columns)
                try:
                    # ตรวจสอบ 3 คอลัมน์แรก ถ้าเจอเครื่องหมายช่วงค่า ให้ข้าม
                    is_control_row = False
                    for c_idx in range(min(5, len(row))):
                        val_str = str(row.iloc[c_idx])
                        if " - " in val_str or "<" in val_str or ">" in val_str:
                            is_control_row = True
                            break
                    if is_control_row: continue
                except: pass

                obj = model_class()
                has_date = False
                has_time = False
                
                # วนลูปจับคู่ข้อมูล
                for excel_col, db_field in col_to_field_map.items():
                    val = row.get(excel_col)
                    
                    # Skip empty values
                    if val is None or pd.isna(val) or str(val).strip() == "" or str(val).strip() == "-":
                        continue

                    # --- Handle Date ---
                    if 'date' in db_field:
                        if isinstance(val, (datetime, pd.Timestamp)):
                             val = val.date()
                             has_date = True
                        elif isinstance(val, str):
                            try:
                                val = val.strip().replace('/', '-').replace('\\', '-')
                                parts = val.split('-')
                                if len(parts) == 3:
                                    y, m, d = 0, 0, 0
                                    # Case: YYYY-MM-DD
                                    if len(parts[0]) == 4: y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                                    # Case: DD-MM-YYYY
                                    elif len(parts[2]) == 4: d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                                    
                                    # Convert Buddhist Year
                                    if y > 2400: y -= 543
                                    
                                    # Assign valid date
                                    val = f"{y}-{m:02d}-{d:02d}"
                                    has_date = True
                            except: continue
                    
                    # --- Handle Time ---
                    elif 'time' in db_field:
                        if isinstance(val, str):
                            val = val.replace('.', ':').strip()
                            if ':' in val: has_time = True
                        elif isinstance(val, (datetime, time)):
                            val = val if isinstance(val, time) else val.time()
                            has_time = True
                        
                    # --- Handle Numbers ---
                    else:
                        try:
                            if isinstance(val, str):
                                val = float(val.replace(',', ''))
                            setattr(obj, db_field, val)
                        except: pass
                    
                    # Set Date/Time to object if valid
                    if 'date' in db_field and has_date: setattr(obj, db_field, val)
                    if 'time' in db_field and has_time: setattr(obj, db_field, val)

                # *** CRITICAL FIX: Only save if BOTH Date and Time are present ***
                if has_date and has_time:
                    objects_to_create.append(obj)
            
            if objects_to_create:
                model_class.objects.bulk_create(objects_to_create)
                messages.success(request, f'Import สำเร็จ: {len(objects_to_create)} รายการ ({machine_type})')
            else:
                messages.warning(request, f'ไม่พบข้อมูลที่สมบูรณ์ (ต้องมีทั้งวันที่และเวลา) ตรวจสอบไฟล์: {file.name}')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            
    return redirect('operation_dashboard')

@login_required
def boiler_operation_add(request):
    if request.method == 'POST':
        form = BoilerOperationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler') 
        else:
            print(f"Boiler Form Errors: {form.errors}")
    else:
        form = BoilerOperationForm()

    # Control Values Configuration (Taken from JT.csv Row 2)
    control_values = {
        'jt_steam_flow': "100 - 150",
        'jt_steam_pressure': "17 - 21",
        'jt_o2_gas': "4 - 7",
        'jt_feeder_speed': "0 - 100",
        'jt_damper_fdf': "0 - 100",
        'jt_damper_idf': "0 - 100",
        'jt_amp_oaf': "0 - 150",
        'jt_amp_fdf': "0 - 300",
        'jt_amp_idf': "0 - 350",
        'jt_drum_level': "0 - 100",
        'jt_feed_water_valve': "0 - 100",
        'jt_feed_water_flow': "100 - 150",
        'jt_deaerator_level': "50 - 80",
        'jt_deaerator_valve': "0 - 100",
        'jt_ph_boiler': "9.5 - 11.5",
        'jt_tds_boiler': "< 2500",
        'jt_temp_steam': "240 - 280",
        'jt_temp_deaerator': "102 - 105",
        'jt_temp_feed_water_eco': "130 - 180",
        'jt_temp_air_out_ah': "130 - 170",
        'jt_temp_gas_in_ah': "220 - 270",
        'jt_temp_gas_in_eco': "280 - 350",
        'jt_temp_gas_stack': "< 180",
        'jt_press_furnace': "-5 - 0",
        'jt_press_gas_out_ah': "-50 - -30",
        'jt_press_gas_out_eco': "-25 - -15",
        'jt_press_gas_out_dc': "-60 - -40",
        'jt_inlet_wet_scrubber': "-80 - -50",
        'jt_outlet_wet_scrubber': "-100 - -80",
        'jt_inlet_stack': "-120 - -100",
        'jt_sum_steam': "-",
        'jt_sum_feed_water': "-",
        'jt_cem_so2': "< 60",
        'jt_cem_no2': "< 200",
        'jt_cem_nox': "< 200",
        'jt_cem_co': "-",
        'jt_cem_dust': "< 120",
        'jt_cem_o2': "-",
    }

    # Grouping Fields
    field_groups = {
        'steam_combustion': [],
        'water_drum': [],
        'air_gas': [],
        'chemistry': [],
        'emissions': [],
        'others': []
    }

    for field in form:
        field.control_val = control_values.get(field.name)
        
        name = field.name
        if name in ['jt_date', 'jt_time']: continue
        
        if 'steam' in name or 'o2' in name or 'feeder' in name or 'amp' in name:
            field_groups['steam_combustion'].append(field)
        elif 'water' in name or 'drum' in name or 'deaerator' in name:
            field_groups['water_drum'].append(field)
        elif 'gas' in name or 'air' in name or 'press' in name or 'stack' in name or 'scrubber' in name:
            field_groups['air_gas'].append(field)
        elif 'ph' in name or 'tds' in name:
            field_groups['chemistry'].append(field)
        elif 'cem' in name:
            field_groups['emissions'].append(field)
        else:
            field_groups['others'].append(field)

    return render(request, 'myapp/boiler_operation_form.html', {
        'form': form,
        'field_groups': field_groups
    })

@login_required
def yoshimine_operation_add(request):
    if request.method == 'POST':
        form = YoshimineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler')
        else:
            print(f"Yoshimine Form Errors: {form.errors}")
    else:
        form = YoshimineForm()
    
    # Control Values Configuration
    control_values = {
        'yos_main_steam_flow': "0 - 150",
        'yos_main_steam_pressure': "40 - 43",
        'yos_main_steam_temp': "450 - 470",
        'yos_desuperheat_valve': "0 - 100",
        'yos_desuperheat_in_temp': "105 - 130",
        'yos_desuperheat_out_temp': "105 - 130",
        'yos_drum_level': "0 - 100",
        'yos_drum_pressure': "43 - 48",
        'yos_feed_water_flow': "0 - 150",
        'yos_feed_water_pressure': "50 - 65",
        'yos_feed_water_in_temp': "105 - 110",
        'yos_eco_out_temp': "180 - 230",
        'yos_blowdown_flow': "0 - 5",
        'yos_cbd_valve': "0 - 100",
        'yos_ins_air_pressure': "0 - 50",
        'yos_main_feeder': "0 - 100",
        'yos_bd_ah1_in_temp': "< 200",
        'yos_bd_ah1_in_press': "0 - 10",
        'yos_bd_ah1_out_temp': "< 180",
        'yos_ah1_air_out_press': "0 - 300",
        'yos_ah1_air_out_temp': "130 - 160",
        'yos_ah2_air_out_temp': "150 - 180",
        'yos_sh_out_gas_temp': "< 800",
        'yos_under_grate_press': "0 - 150",
        'yos_furnace_pressure': "-5 - 0",
        'yos_gas_exit_temp': "< 180",
        'yos_gas_exit_press': "-40 - -20",
        'yos_eco_out_gas_temp': "< 350",
        'yos_eco_out_gas_press': "-15 - -5",
        'yos_ah2_gas_out_temp': "< 250",
        'yos_ah2_gas_out_press': "-25 - -15",
        'yos_dc_gas_out_temp': "< 200",
        'yos_dc_gas_out_press': "-50 - -30",
        'yos_esp_gas_out_press': "-60 - -40",
        'yos_ah1_gas_out_press': "-40 - -20",
        'yos_sf_damper': "0 - 100",
        'yos_sf_air_press': "0 - 1000",
        'yos_fdf2_air_press': "0 - 400",
        'yos_under_gate_damper': "0 - 100",
        'yos_idf_damper': "0 - 100",
        'yos_esp_c1_volt': "40 - 60",
        'yos_esp_c1_curr': "200 - 800",
        'yos_esp_c2_volt': "40 - 60",
        'yos_esp_c2_curr': "200 - 800",
        'yos_steam_sum': "-",
        'yos_feed_water_sum': "-",
        'yos_cem_so2': "< 60",
        'yos_cem_no2': "< 200",
        'yos_cem_nox': "< 200",
        'yos_cem_co': "-",
        'yos_cem_dust': "< 120",
        'yos_cem_o2': "-",
        'yos_steam_transform_level': "0 - 100",
        'yos_steam_transform_valve': "0 - 100",
        'yos_condensate_tank_level': "0 - 100",
        'yos_header_temp': "< 450",
        'yos_dea_level': "50 - 80",
        'yos_dea_pressure': "0.2 - 0.5",
        'yos_dea_valve': "0 - 100",
        'yos_oxygen': "-",
    }

    # Prepare field groups for template
    steam_water_fields = []
    air_gas_fields = []
    other_fields = []

    for field in form:
        # ** FIX: Attach control value directly to field object **
        field.control_val = control_values.get(field.name)

        if field.name in ['yos_date', 'yos_time']:
            continue
        
        name = field.name.lower()
        is_steam_water = 'steam' in name or 'water' in name or 'drum' in name
        
        # Note: logic: ('temp' in name and 'steam' not in name)
        is_air_gas = 'air' in name or 'gas' in name or ('temp' in name and 'steam' not in name)

        if is_steam_water:
            steam_water_fields.append(field)
        elif is_air_gas:
            air_gas_fields.append(field)
        else:
            other_fields.append(field)

    return render(request, 'myapp/yoshimine_form.html', {
        'form': form,
        # 'control_values': control_values, # No longer needed in context
        'steam_water_fields': steam_water_fields,
        'air_gas_fields': air_gas_fields,
        'other_fields': other_fields,
    })

@login_required
def banpong1_operation_add(request):
    if request.method == 'POST':
        form = Banpong1Form(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler')
        else:
            print(f"Banpong1 Form Errors: {form.errors}")
    else:
        form = Banpong1Form()

    # Control Values (Row 2 from CSV)
    control_values = {
        'bp1_main_steam_flow': "< 150",
        'bp1_main_steam_pressure': "40 - 43",
        'bp1_main_steam_temp': "450 - 470",
        'bp1_desuperheat_valve': "< 99.5%",
        'bp1_desuperheat_in_temp': "390 - 450",
        'bp1_desuperheat_out_temp': "450 - 500",
        'bp1_drum_level': "100 - 200",
        'bp1_drum_pressure': "42 - 45",
        'bp1_feed_water_flow': "< 180",
        'bp1_feed_water_pressure': "61 - 66.5",
        'bp1_feed_water_in_temp': "50 - 110",
        'bp1_eco_out_temp': "150 - 200",
        'bp1_eco_out_pressure': "42 - 50",
        'bp1_bd_flow': "< 4",
        'bp1_cbd_valve': "< 99.5%",
        'bp1_ins_air_pressure': "> 7",
        'bp1_main_feeder': "16 - 100",
        'bp1_bd_ah1_in_temp': "-  C", # Placeholder
        'bp1_bd_ah1_in_press': "250 - 400",
        'bp1_bd_ah1_out_temp': "40 - 150",
        'bp1_bd_ah1_out_press': "0 - 10",
        'bp1_ah1_air_out_press': "150 - 200",
        'bp1_ah1_air_out_temp': "140 - 165",
        'bp1_ah2_air_out_temp': "140 - 165",
        'bp1_under_grate_air_temp': "< 165",
        'bp1_under_grate_air_press': "< 200",
        'bp1_furnace_pressure': "-5 - 0",
        'bp1_gas_exit_temp': "< 180",
        'bp1_gas_exit_pressure': "-35 - -20",
        'bp1_eco_out_gas_temp': "< 350",
        'bp1_eco_out_gas_press': "-15 - -5",
        'bp1_ah2_gas_out_temp': "< 260",
        'bp1_ah2_gas_out_press': "-25 - -15",
        'bp1_dc_gas_out_temp': "< 200",
        'bp1_dc_gas_out_press': "-35 - -20",
        'bp1_esp_gas_in_temp': "-40 - -25", # CSV Header says Inlet Pressure? but value seems temp range for pressure?
        'bp1_esp_gas_out_temp': "150 - 170",
        'bp1_esp_gas_out_press': "-50 - -30",
        'bp1_ah1_gas_out_temp': "< 200",
        'bp1_ah1_gas_out_press': "-35 - -20",
        'bp1_fdf_damper': "0 - 100",
        'bp1_faf_damper': "0 - 100",
        'bp1_faf_air_press': "< 1000",
        'bp1_fdf2_damper': "0 - 100",
        'bp1_fdf2_air_press': "< 400",
        'bp1_under_gate_damper': "0 - 100",
        'bp1_idf_damper': "0 - 100",
        'bp1_esp_c1_volt': "40 - 60",
        'bp1_esp_c1_curr': "200 - 800",
        'bp1_esp_c2_volt': "40 - 60",
        'bp1_esp_c2_curr': "200 - 800",
        'bp1_esp_c3_volt': "40 - 60",
        'bp1_esp_c3_curr': "200 - 800",
        'bp1_steam_sum': "-",
        'bp1_feed_water_sum': "-",
        'bp1_blowdown_sum': "-",
        'bp1_cem_so2': "< 60",
        'bp1_cem_no2': "< 200",
        'bp1_cem_nox': "< 200",
        'bp1_cem_co': "-",
        'bp1_cem_tsp': "< 120",
        'bp1_cem_o2': "-",
    }

    # Grouping Fields
    steam_water = []
    air_gas = []
    dampers_fans = []
    esp_system = []
    emissions = []
    others = []

    for field in form:
        field.control_val = control_values.get(field.name)
        
        name = field.name
        if name in ['bp1_date', 'bp1_time']: continue
        
        if 'steam' in name or 'water' in name or 'drum' in name or 'eco' in name or 'blowdown' in name or 'cbd' in name or 'desuperheat' in name:
            steam_water.append(field)
        elif 'air' in name or 'gas' in name or 'furnace' in name or 'press' in name or 'temp' in name:
            if 'esp' not in name:
                air_gas.append(field)
            else:
                esp_system.append(field)
        elif 'damper' in name or 'feeder' in name:
            dampers_fans.append(field)
        elif 'esp' in name:
            esp_system.append(field)
        elif 'cem' in name:
            emissions.append(field)
        else:
            others.append(field)

    return render(request, 'myapp/banpong1_form.html', {
        'form': form,
        'steam_water': steam_water,
        'air_gas': air_gas,
        'dampers_fans': dampers_fans,
        'esp_system': esp_system,
        'emissions': emissions,
        'others': others,
    })

@login_required
def chengchen_operation_add(request):
    if request.method == 'POST':
        form = ChengchenForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler')
        else:
            print(f"Chengchen Form Errors: {form.errors}")
    else:
        form = ChengchenForm()
    
    # Control Values (Row 2 from CSV)
    control_values = {
        'ch_steam_flow': "40 - 70",
        'ch_steam_pressure': "18 - 22",
        'ch_o2_percent': "3.5 - 6",
        'ch_feeder_control': "%", # No specific range in CSV, just unit
        'ch_fdf_damper': "%",
        'ch_idf_damper': "%",
        'ch_fdf_amp': "< 241",
        'ch_saf_amp_left': "< 86",
        'ch_saf_amp_right': "< 86",
        'ch_idf_amp': "< 131",
        'ch_drum_level': "40 - 60",
        'ch_feed_water_valve': "%",
        'ch_feed_water_flow': "40 - 75",
        'ch_ph_water': "9.5 - 11.5",
        'ch_tds_water': "< 2500",
        'ch_steam_temp': "360 - 410",
        'ch_dea_temp': "102 - 105",
        'ch_eco_out_temp': "140 - 190",
        'ch_air_heater_out_temp': "150 - 180",
        'ch_gas_furnace_ah_temp': "280 - 350",
        'ch_gas_in_eco_temp': "350 - 450",
        'ch_stack_temp': "< 180",
        'ch_furnace_pressure': "-5 - 0",
        'ch_gas_out_eco_pressure': "-30 - -10",
        'ch_gas_out_dc_pressure': "-60 - -30",
        'ch_inlet_wet_scrubber_press': "-100 - -60",
        'ch_outlet_wet_scrubber_press': "-120 - -80",
        'ch_inlet_stack_press': "-130 - -100",
    }

    # Grouping Fields
    field_groups = {
        'steam_combustion': [],
        'control_fans': [],
        'water_drum': [],
        'temperature': [],
        'pressure_draft': [],
        'others': []
    }

    for field in form:
        field.control_val = control_values.get(field.name)
        
        name = field.name
        if name in ['ch_date', 'ch_time']: continue
        
        if 'steam' in name or 'o2' in name:
            field_groups['steam_combustion'].append(field)
        elif 'feeder' in name or 'damper' in name or 'amp' in name:
            field_groups['control_fans'].append(field)
        elif 'water' in name or 'drum' in name or 'dea_level' in name or 'ph' in name or 'tds' in name:
            field_groups['water_drum'].append(field)
        elif 'temp' in name:
            field_groups['temperature'].append(field)
        elif 'pressure' in name and 'steam' not in name:
             field_groups['pressure_draft'].append(field)
        else:
            field_groups['others'].append(field)

    return render(request, 'myapp/chengchen_form.html', {
        'form': form,
        'field_groups': field_groups
    })

@login_required
def takuma_operation_add(request):
    if request.method == 'POST':
        form = TakumaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('boiler')
        else:
            print(f"Takuma Form Errors: {form.errors}")
    else:
        form = TakumaForm()
    
    # Control Values (Row 2 from CSV)
    control_values = {
        'tk_steam_flow': "40 - 70",
        'tk_steam_pressure': "18 - 22",
        'tk_o2_percent': "3.5 - 6",
        'tk_feeder_control': "%", # No specific range
        'tk_fdf_damper': "%",
        'tk_idf_damper': "%",
        'tk_fdf_amp': "< 241",
        'tk_saf_amp_left': "< 86",
        'tk_saf_amp_right': "< 86",
        'tk_idf_amp': "< 131",
        'tk_drum_level': "30 - 75",
        'tk_feed_water_valve': "%",
        'tk_feed_water_flow': "T/H",
        'tk_ph_water': "10.5 - 11.5",
        'tk_tds_water': "< 3000",
        'tk_steam_temp': "350 +/- 20",
        'tk_dea_temp': "95 - 105",
        'tk_eco_out_temp': "< 190", # Not in CSV but common
        'tk_air_heater_out_temp': "150 - 190",
        'tk_gas_furnace_ah_temp': "280 - 360",
        'tk_gas_in_eco_temp': "350 - 450", # Not in CSV
        'tk_stack_temp': "< 180",
        'tk_furnace_pressure': "-5 - 0",
        'tk_gas_out_eco_pressure': "-30 - -10", # Not in CSV
        'tk_gas_out_dc_pressure': "-60 - -30",
        'tk_inlet_wet_scrubber_press': "-100 - -60",
        'tk_outlet_wet_scrubber_press': "-120 - -80",
        'tk_inlet_stack_press': "-130 - -100",
    }

    # Grouping Fields
    field_groups = {
        'steam_combustion': [],
        'control_fans': [],
        'water_drum': [],
        'temperature': [],
        'pressure_draft': [],
        'others': []
    }

    for field in form:
        field.control_val = control_values.get(field.name)
        
        name = field.name
        if name in ['tk_date', 'tk_time']: continue
        
        if 'steam' in name or 'o2' in name:
            field_groups['steam_combustion'].append(field)
        elif 'feeder' in name or 'damper' in name or 'amp' in name:
            field_groups['control_fans'].append(field)
        elif 'water' in name or 'drum' in name or 'dea_level' in name or 'ph' in name or 'tds' in name:
            field_groups['water_drum'].append(field)
        elif 'temp' in name:
            field_groups['temperature'].append(field)
        elif 'pressure' in name and 'steam' not in name:
             field_groups['pressure_draft'].append(field)
        else:
            field_groups['others'].append(field)

    return render(request, 'myapp/takuma_form.html', {
        'form': form,
        'field_groups': field_groups
    })

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
        'combined_sum': sum_cane_a + sum_cane_b, # Add combined sum
    }
    
    
    return render(request, 'myapp/mill.html', context)

def mill_history_api(request):
    try:
        line = request.GET.get('line', 'A')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        # Default to last 7 days if no date provided
        if not end_date_str:
            end_date = datetime.now().date()
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
        if not start_date_str:
            start_date = end_date - timedelta(days=6) # 7 days total (inclusive)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        if line == 'ALL':
             reports_a = MillReport.objects.filter(line='A', date__range=[start_date, end_date]).values('date', 'cane_weight')
             reports_b = MillReport.objects.filter(line='B', date__range=[start_date, end_date]).values('date', 'cane_weight')
             
             # Convert to dict for easy lookup
             dict_a = {r['date']: r['cane_weight'] or 0 for r in reports_a}
             dict_b = {r['date']: r['cane_weight'] or 0 for r in reports_b}
             
             # Merge dates
             all_dates = sorted(list(set(list(dict_a.keys()) + list(dict_b.keys()))))
             
             data = []
             for d in all_dates:
                 val_a = dict_a.get(d, 0)
                 val_b = dict_b.get(d, 0)
                 data.append({
                     'date': d.strftime('%Y-%m-%d'),
                     'cane_a': val_a,
                     'cane_b': val_b,
                     'total': val_a + val_b
                 })
                 
             return JsonResponse({'status': 'success', 'data': data})

        reports = MillReport.objects.filter(
            line=line,
            date__range=[start_date, end_date]
        ).order_by('date')

        data = []
        for r in reports:
            data.append({
                'date': r.date.strftime('%Y-%m-%d'), ### Format for Chart.js
                'cane_weight': r.cane_weight,
                'kpis': {
                    1: r.first_mill_extraction,
                    2: r.reduced_pol_extraction,
                    3: r.purity_drop,
                    4: r.imbibition_cane,
                    5: r.imbibition_fiber,
                    6: r.bagasse_moisture,
                    7: r.cane_preparation_index,
                    8: r.pol_bagasse,
                    9: r.loss_bagasse,
                    10: r.ccs,
                    11: r.trash,
                }
            })

        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

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


@login_required
def lathe_dashboard(request):
    # Filter logs for 'โรงกลึง'
    logs = MaintenanceLog.objects.filter(dept='โรงกลึง').order_by('-date')
    
    # Simple stats for today
    today = datetime.now().date()
    today_logs = logs.filter(date=today)
    
    stats = {
        'today_count': today_logs.count(),
        'today_downtime': today_logs.aggregate(Sum('downtime_stop'))['downtime_stop__sum'] or 0
    }
    
    return render(request, 'myapp/lathe.html', {
        'logs': logs,
        'stats': stats
    })
