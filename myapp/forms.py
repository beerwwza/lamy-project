from django import forms
from .models import employee  # เรียกใช้ Model ที่เราสร้างไว้
from .models import BoilerOperationLog, ChengchenLog, TakumaLog, YoshimineLog, Banpong1Log,  Banpong2Log, MaintenanceLog, KPIMetric, RepairDocument
from .models import MillReport, BoilerDailyKPI
from .models import Equipment, EquipmentBOM, CBMVisualTest, CBMVibration, CBMThermoscan, CBMOilAnalysis, CBMAcoustic
from .models import PMSchedule

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = employee  # บอกว่าจะสร้างฟอร์มจาก Model ไหน
        fields = ['name', 'employeeID', 'tell', 'group', 'department'] # เลือก field ที่จะให้กรอก
        
        # กำหนด Label ภาษาไทยที่จะไปโชว์หน้าเว็บ
        labels = {
            'name': 'ชื่อ-นามสกุล',
            'employeeID': 'รหัสพนักงาน',
            'tell': 'เบอร์โทรศัพท์',
            'group': 'ฝ่าย',
            'department': 'แผนก',
        }
        
        # ใส่ Class ของ Bootstrap เพื่อให้ฟอร์มสวยเหมือนเดิม
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'กรุณากรอกชื่อ'}),
            'employeeID': forms.TextInput(attrs={'class': 'form-control'}),
            'tell': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
        }
class BoilerOperationForm(forms.ModelForm):
    class Meta:
        model = BoilerOperationLog
        fields = '__all__'
        widgets = {
            'jt_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'jt_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(BoilerOperationForm, self).__init__(*args, **kwargs)
        # Loop ใส่ class ให้ทุก field ที่เหลือ (ที่เป็นตัวเลข)
        for field in self.fields:
            if field not in ['jt_date', 'jt_time', 'jt_problem_cause']:
                self.fields[field].widget.attrs.update({
                    'class': 'w-full p-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                    'step': '0.01', # ให้กรอกทศนิยมได้
                    'placeholder': '-'
                })

                # ... BoilerOperationForm code ...

class YoshimineForm(forms.ModelForm):
    class Meta:
        model = YoshimineLog
        fields = '__all__'
        widgets = {
            'yos_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'yos_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }


    def __init__(self, *args, **kwargs):
        super(YoshimineForm, self).__init__(*args, **kwargs)
        # Loop ใส่ class ให้ทุก field
        for field in self.fields:
            if field not in ['yos_date', 'yos_time', 'yos_remark']:
                self.fields[field].widget.attrs.update({
                    'class': 'w-full p-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                    'step': '0.01',
                    'placeholder': '-'
                })

class Banpong1Form(forms.ModelForm):
    class Meta:
        model = Banpong1Log
        fields = '__all__'
        widgets = {
            'bp1_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bp1_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(Banpong1Form, self).__init__(*args, **kwargs)
        # วนลูปเพื่อใส่ CSS Class ให้ทุกช่อง (Styling)
        for field in self.fields:
            if field not in ['bp1_date', 'bp1_time', 'bp1_remark']:
                self.fields[field].widget.attrs.update({
                    'class': 'w-full p-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                    'step': '0.01',      # รองรับทศนิยม
                    'placeholder': '-'   # แสดงขีดเมื่อยังไม่กรอก
                })

class ChengchenForm(forms.ModelForm):
    class Meta:
        model = ChengchenLog
        fields = '__all__'
        widgets = {
            'ch_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ch_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'ch_remark': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        

    def __init__(self, *args, **kwargs):
        super(ChengchenForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['ch_date', 'ch_time', 'ch_remark']:
                self.fields[field].widget.attrs.update({
                    'class': 'w-full p-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                    'step': '0.01',
                    'placeholder': '-'
                })

class TakumaForm(forms.ModelForm):
    class Meta:
        model = TakumaLog
        fields = '__all__'
        widgets = {
            'tk_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tk_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'tk_remark': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(TakumaForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['tk_date', 'tk_time', 'tk_remark']:
                self.fields[field].widget.attrs.update({
                    'class': 'w-full p-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                    'step': '0.01',
                    'placeholder': '-'
                })

class Banpong2Form(forms.ModelForm):
    class Meta:
        model = Banpong2Log
        fields = '__all__'
        widgets = {
            'bp2_date': forms.DateInput(attrs={'type': 'date'}),
            'bp2_time': forms.TimeInput(attrs={'type': 'time'}),
            'bp2_remark': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(Banpong2Form, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['bp2_date', 'bp2_time', 'bp2_remark']:
                self.fields[field].widget.attrs.update({
                    'class': 'w-full p-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                    'step': '0.01',
                    'placeholder': '-'
                })

class BoilerDailyKPIForm(forms.ModelForm):
    class Meta:
        model = BoilerDailyKPI
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(BoilerDailyKPIForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            # ใส่ Styling Tailwind ให้ทุกช่อง
            self.fields[field].widget.attrs.update({
                'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block dark:bg-slate-700 dark:border-slate-600 dark:placeholder-slate-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01'
            })
            # ยกเว้นช่อง Date ไม่ต้องใส่ step
            if field == 'date':
                self.fields[field].widget.attrs.pop('step', None)

class MillReportForm(forms.ModelForm):
    class Meta:
        model = MillReport
        fields = '__all__'
        # fields ที่เราจะใช้รับค่าทั้งหมด (ไม่ต้องระบุทีละตัวเพราะ HTML name ตรงกับ model แล้ว)

class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        exclude = ['equipment_fk']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'machine': forms.TextInput(attrs={
                'list': 'equipment-datalist',
                'autocomplete': 'off',
                'placeholder': 'พิมพ์ชื่อหรือรหัสเครื่องจักร...',
            }),
            'problem': forms.Textarea(attrs={'rows': 3}),
            'cause': forms.Textarea(attrs={'rows': 3}),
            'solution': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(MaintenanceLogForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'is_leak':
                self.fields[field].widget.attrs.update({
                    'class': 'w-full p-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white'
                })

class KPIMetricForm(forms.ModelForm):
    class Meta:
        model = KPIMetric
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super(KPIMetricForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full p-2 border border-slate-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white'
            })

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(EquipmentForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'image' and field != 'is_active':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': '-'
                })

class EquipmentBOMForm(forms.ModelForm):
    class Meta:
        model = EquipmentBOM
        fields = ['part_no', 'part_name', 'qty', 'location', 'stock_qty']

    def __init__(self, *args, **kwargs):
        super(EquipmentBOMForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'qty' and field != 'stock_qty':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': '-'
                })
            elif field == 'qty' or field == 'stock_qty':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'min': '0'
                })

class CBMVisualTestForm(forms.ModelForm):
    class Meta:
        model = CBMVisualTest
        exclude = ('equipment',)
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'inspector': forms.TextInput(attrs={'class': 'form-control'}),
            'overall_condition': forms.Select(attrs={'class': 'form-select'}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image_file_id': forms.HiddenInput(),
        }

class CBMVibrationForm(forms.ModelForm):
    class Meta:
        model = CBMVibration
        exclude = ('equipment',)
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'inspector': forms.TextInput(attrs={'class': 'form-control'}),
            'measurement_point': forms.TextInput(attrs={'class': 'form-control'}),
            'velocity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'acceleration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bearing_temp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class CBMThermoscanForm(forms.ModelForm):
    class Meta:
        model = CBMThermoscan
        exclude = ('equipment',)
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'inspector': forms.TextInput(attrs={'class': 'form-control'}),
            'location_target': forms.TextInput(attrs={'class': 'form-control'}),
            'max_temp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'ambient_temp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'delta_t': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'image_file_id': forms.HiddenInput(),
        }

class CBMOilAnalysisForm(forms.ModelForm):
    class Meta:
        model = CBMOilAnalysis
        exclude = ('equipment',)
        widgets = {
            'collection_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'inspector': forms.TextInput(attrs={'class': 'form-control'}),
            'oil_type': forms.TextInput(attrs={'class': 'form-control'}),
            'viscosity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'water_content': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'wear_particle': forms.TextInput(attrs={'class': 'form-control'}),
            'oil_remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ระบุสถานะปัจจุบันของน้ำมัน เช่น สีเปลี่ยน, กลิ่นไหม้, มีตะกอน ฯลฯ'}),
            'lab_report_file_id': forms.HiddenInput(),
        }

class CBMAcousticForm(forms.ModelForm):
    class Meta:
        model = CBMAcoustic
        exclude = ('equipment',)
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'inspector': forms.TextInput(attrs={'class': 'form-control'}),
            'inspection_point': forms.TextInput(attrs={'class': 'form-control'}),
            'decibel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'sound_pattern': forms.Select(attrs={'class': 'form-select'}),
            'audio_file_id': forms.HiddenInput(),
        }

class RepairDocumentForm(forms.ModelForm):
    class Meta:
        model  = RepairDocument
        fields = [
            'title', 'equipment', 'department', 'doc_type',
            'po_number', 'budget_year', 'budget_amount', 'description',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'เช่น รายงานซ่อมปั๊มน้ำหม้อไอน้ำ JT',
            }),
            'equipment': forms.Select(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'department': forms.Select(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'doc_type': forms.Select(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'po_number': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'เช่น PO-2568-0001',
            }),
            'budget_year': forms.NumberInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'min': 2560, 'max': 2580,
            }),
            'budget_amount': forms.NumberInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'step': '0.01', 'placeholder': '0.00',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'คำอธิบายเพิ่มเติม (ถ้ามี)',
            }),
        }
        labels = {
            'title':         'ชื่อเอกสาร',
            'equipment':     'เครื่องจักร',
            'department':    'แผนก',
            'doc_type':      'ประเภทเอกสาร',
            'po_number':     'เลข PO / Budget Code',
            'budget_year':   'ปีงบประมาณ',
            'budget_amount': 'งบประมาณ (บาท)',
            'description':   'คำอธิบาย',
        }


_TW = ('w-full p-2 border border-slate-300 rounded-lg text-sm '
       'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 '
       'dark:bg-slate-800 dark:border-slate-700 dark:text-white')


class PMScheduleForm(forms.ModelForm):
    class Meta:
        model  = PMSchedule
        fields = ['task_name', 'frequency_type', 'frequency_value',
                  'last_completed_date', 'next_due_date',
                  'assigned_to', 'instructions', 'estimated_hours', 'is_active']
        widgets = {
            'task_name':            forms.TextInput(attrs={'class': _TW, 'placeholder': 'เช่น เปลี่ยนน้ำมันหล่อลื่น'}),
            'frequency_type':       forms.Select(attrs={'class': _TW}),
            'frequency_value':      forms.NumberInput(attrs={'class': _TW, 'min': 1}),
            'last_completed_date':  forms.DateInput(attrs={'class': _TW, 'type': 'date'}),
            'next_due_date':        forms.DateInput(attrs={'class': _TW, 'type': 'date'}),
            'assigned_to':          forms.TextInput(attrs={'class': _TW, 'placeholder': 'ชื่อช่างหรือทีม'}),
            'instructions':         forms.Textarea(attrs={'class': _TW, 'rows': 3}),
            'estimated_hours':      forms.NumberInput(attrs={'class': _TW, 'min': 0.5, 'step': 0.5}),
        }
        labels = {
            'task_name':            'งาน PM',
            'frequency_type':       'ความถี่',
            'frequency_value':      'ค่าความถี่ (ทุก N ครั้ง)',
            'last_completed_date':  'ทำ PM ล่าสุด',
            'next_due_date':        'ครั้งต่อไป',
            'assigned_to':          'ผู้รับผิดชอบ',
            'instructions':         'คำแนะนำ / ขั้นตอน',
            'estimated_hours':      'เวลาที่ใช้ (ชม.)',
            'is_active':            'เปิดใช้งาน',
        }