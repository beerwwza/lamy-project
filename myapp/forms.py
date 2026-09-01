from django import forms
from django.forms import inlineformset_factory
from .models import employee  # เรียกใช้ Model ที่เราสร้างไว้
from .models import BoilerOperationLog, ChengchenLog, TakumaLog, YoshimineLog, Banpong1Log,  Banpong2Log, MaintenanceLog, KPIMetric, RepairDocument
from .models import MillReport, BoilerDailyKPI
from .models import Equipment, EquipmentBOM, EquipmentLink, CBMVisualTest, CBMVibration, CBMThermoscan, CBMOilAnalysis, CBMAcoustic
from .models import PMSchedule, PMPlan, PMPlanItem, WorkOrder
from .models import TrainingSkill, EmployeeSkillLevel, TrainingCourse, TrainingRecord
from .models import TrainingCourseMaterial, TrainingQuizQuestion, TrainingQuizChoice, CareerLadderStep
from .models import (
    Manual, ManualSafetyItem, ManualPartItem, ManualPrecheckItem, ManualOperatingStep,
    ManualMaintenanceDailyItem, ManualMaintenancePeriodicItem, ManualTroubleshootItem,
    ManualSpecItem,
)
from .models import MachineTask, MachineTaskVibration
from .models import ProcessCategory

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = employee
        fields = ['first_name', 'last_name', 'employeeID', 'tell', 'group', 'department', 'is_active']

        labels = {
            'first_name': 'ชื่อ',
            'last_name': 'นามสกุล',
            'employeeID': 'รหัสพนักงาน',
            'tell': 'เบอร์โทรศัพท์',
            'group': 'กลุ่มงาน',
            'department': 'แผนก',
            'is_active': 'ยังทำงานอยู่ (ไม่ติ๊ก = ลาออก)',
        }

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'กรุณากรอกชื่อ'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'กรุณากรอกนามสกุล'}),
            'employeeID': forms.TextInput(attrs={'class': 'form-control'}),
            'tell': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น ช่างเทคนิค L1'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
    LEGACY_KEEP_VALUE = '__keep_current_process__'

    class Meta:
        model = Equipment
        exclude = ['motor', 'panel', 'starter', 'breaker', 'drive_type', 'updated_by']

    def __init__(self, *args, **kwargs):
        super(EquipmentForm, self).__init__(*args, **kwargs)

        active_names = list(
            ProcessCategory.objects.filter(is_active=True).order_by('name').values_list('name', flat=True)
        )
        process_choices = [('', '-- เลือกกระบวนการ --')] + [(name, name) for name in active_names]

        self._legacy_process_value = None
        if self.instance and self.instance.pk:
            current = self.instance.process
            if not current or current not in active_names:
                self._legacy_process_value = current or ''
                legacy_label = (
                    f'{current} (ค่าเดิม — ไม่อยู่ในรายการปัจจุบัน)'
                    if current else '(ว่าง / ไม่ระบุ — ค่าเดิม)'
                )
                process_choices.append((self.LEGACY_KEEP_VALUE, legacy_label))

        self.fields['process'] = forms.ChoiceField(
            choices=process_choices,
            required=True,
            label=self.fields['process'].label,
        )
        if self._legacy_process_value is not None:
            self.initial['process'] = self.LEGACY_KEEP_VALUE

        for fname in ['mtbf', 'mttr', 'acc_cost']:
            if fname in self.fields:
                self.fields[fname].required = False
        for field in self.fields:
            if field != 'image' and field != 'is_active':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': '-'
                })

    def clean_process(self):
        value = self.cleaned_data.get('process')
        if value == self.LEGACY_KEEP_VALUE:
            return self._legacy_process_value
        return value

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

class EquipmentLinkForm(forms.ModelForm):
    class Meta:
        model = EquipmentLink
        fields = ['label', 'linked_equipment_id', 'order']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น Pump, Utility Fan'}),
            'linked_equipment_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'รหัสเครื่องจักร'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


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

_TW_VIBRATION = ('w-full p-2 border border-slate-300 rounded-lg text-sm '
                  'focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 '
                  'dark:bg-slate-800 dark:border-slate-700 dark:text-white')


class CBMVibrationForm(forms.ModelForm):
    class Meta:
        model = CBMVibration
        exclude = ('equipment', 'status')
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': _TW_VIBRATION}),
            'inspector': forms.TextInput(attrs={'class': _TW_VIBRATION}),
            'measurement_point': forms.TextInput(attrs={'class': _TW_VIBRATION}),
            'amp': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'de_ge': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'de_v': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'de_h': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'de_a': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'de_m': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'nde_ge': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'nde_v': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'nde_h': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'nde_a': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'nde_m': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'temp_de': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'temp_frame': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'temp_nde': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
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


class PMPlanForm(forms.ModelForm):
    class Meta:
        model = PMPlan
        fields = ['pm_code', 'title', 'interval_value', 'interval_unit', 'time_of_day', 'start_date', 'assigned_team', 'is_active']
        widgets = {
            'pm_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น PM-A02-M1'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น PM 1 เดือน (ตรวจสอบทั่วไป & อัดจาระบี)'}),
            'interval_value': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'interval_unit': forms.Select(attrs={'class': 'form-control'}),
            'time_of_day': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'assigned_team': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น ทีมช่างกล A02'}),
        }


class PMPlanItemForm(forms.ModelForm):
    class Meta:
        model = PMPlanItem
        fields = ['description', 'order']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น ตรวจสอบระดับน้ำมัน'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = ['problem_title', 'description', 'reporter', 'reporter_dept', 'report_date']
        widgets = {
            'problem_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น ซีลปั๊มรั่ว มีน้ำไหลซึม'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'รายละเอียดเพิ่มเติม'}),
            'reporter': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อผู้แจ้ง'}),
            'reporter_dept': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'แผนก'}),
            'report_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class WorkOrderStatusForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = ['status', 'current_action', 'progress_percent', 'mechanic', 'completed_date']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'current_action': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น กำลังเบิกอะไหล่'}),
            'progress_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'mechanic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อช่างซ่อม'}),
            'completed_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


# ===== Training / Knowledge Center Module =====

class TrainingSkillForm(forms.ModelForm):
    class Meta:
        model = TrainingSkill
        fields = ['name', 'description', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น Bolt&nut'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class EmployeeSkillLevelForm(forms.ModelForm):
    class Meta:
        model = EmployeeSkillLevel
        fields = ['employee', 'skill', 'level']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'skill': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = employee.objects.filter(is_active=True)


class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = ['name', 'skill', 'description', 'duration_days', 'cost_per_person', 'expiry_months', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น การขัน Bolt & Nut ที่ถูกวิธี'}),
            'skill': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0.5'}),
            'cost_per_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '100', 'min': '0'}),
            'expiry_months': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'เว้นว่างถ้าไม่มีวันหมดอายุ'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TrainingRecordForm(forms.ModelForm):
    class Meta:
        model = TrainingRecord
        fields = ['employee', 'course', 'date', 'training_type', 'score', 'status', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'training_type': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = employee.objects.filter(is_active=True)


class TrainingCourseMaterialForm(forms.ModelForm):
    class Meta:
        model = TrainingCourseMaterial
        fields = ['material_type', 'title', 'file', 'display_order']
        widgets = {
            'material_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น คู่มือการขัน Bolt & Nut'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class TrainingQuizQuestionForm(forms.ModelForm):
    class Meta:
        model = TrainingQuizQuestion
        fields = ['question_text']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class TrainingQuizChoiceForm(forms.ModelForm):
    class Meta:
        model = TrainingQuizChoice
        fields = ['choice_text']
        widgets = {
            'choice_text': forms.TextInput(attrs={'class': 'form-control'}),
        }


TrainingQuizChoiceFormSet = inlineformset_factory(
    TrainingQuizQuestion, TrainingQuizChoice,
    form=TrainingQuizChoiceForm, extra=4, can_delete=True,
)


class CareerLadderStepForm(forms.ModelForm):
    class Meta:
        model = CareerLadderStep
        fields = ['name', 'display_order', 'position_duty', 'scope', 'benefits', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น ช่างเทคนิค L1'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'position_duty': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'scope': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ==========================================
# Manual Library Module (คู่มือปฏิบัติงานเครื่องจักร)
# ==========================================

class ManualForm(forms.ModelForm):
    class Meta:
        model = Manual
        fields = ['machine_name', 'model_number', 'department', 'prepared_by', 'doc_no', 'revision', 'doc_date']
        widgets = {
            'machine_name': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'เช่น เครื่องหีบอ้อยหมายเลข 1',
            }),
            'model_number': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'department': forms.Select(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'prepared_by': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'doc_no': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'revision': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'doc_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
        }
        labels = {
            'machine_name': 'ชื่อเครื่องจักร',
            'model_number': 'รุ่น/Model',
            'department':   'แผนก',
            'prepared_by':  'ผู้จัดทำ',
            'doc_no':       'เลขที่เอกสาร',
            'revision':     'ฉบับแก้ไข (Rev.)',
            'doc_date':     'วันที่จัดทำ',
        }


class ManualSafetyItemForm(forms.ModelForm):
    class Meta:
        model = ManualSafetyItem
        fields = ['task', 'hazard', 'measure']
        widgets = {
            'task': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'ขั้นตอนการปฏิบัติงาน',
            }),
            'hazard': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'อันตรายที่อาจเกิดขึ้น',
            }),
            'measure': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'มาตรการป้องกันอันตราย',
            }),
        }

ManualSafetyItemFormSet = inlineformset_factory(
    Manual, ManualSafetyItem, form=ManualSafetyItemForm,
    extra=1, can_delete=True, max_num=100, validate_max=True,
)


class ManualPartItemForm(forms.ModelForm):
    class Meta:
        model = ManualPartItem
        fields = ['label_th', 'label_en']
        widgets = {
            'label_th': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'ชื่อชิ้นส่วน (ไทย)',
            }),
            'label_en': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'Part name (English)',
            }),
        }

ManualPartItemFormSet = inlineformset_factory(
    Manual, ManualPartItem, form=ManualPartItemForm,
    extra=1, can_delete=True, max_num=100, validate_max=True,
)


class ManualPrecheckItemForm(forms.ModelForm):
    class Meta:
        model = ManualPrecheckItem
        fields = ['point', 'detail', 'fix', 'note']
        widgets = {
            'point': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'จุดตรวจสอบ',
            }),
            'detail': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'รายละเอียดการตรวจสอบ',
            }),
            'fix': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'การแก้ไข',
            }),
            'note': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'หมายเหตุ',
            }),
        }

ManualPrecheckItemFormSet = inlineformset_factory(
    Manual, ManualPrecheckItem, form=ManualPrecheckItemForm,
    extra=1, can_delete=True, max_num=100, validate_max=True,
)


class ManualOperatingStepForm(forms.ModelForm):
    class Meta:
        model = ManualOperatingStep
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'หัวข้อขั้นตอน',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'รายละเอียดขั้นตอน',
            }),
        }

ManualOperatingStepFormSet = inlineformset_factory(
    Manual, ManualOperatingStep, form=ManualOperatingStepForm,
    extra=1, can_delete=True, max_num=100, validate_max=True,
)


class ManualMaintenanceDailyItemForm(forms.ModelForm):
    class Meta:
        model = ManualMaintenanceDailyItem
        fields = ['point', 'detail', 'fix']
        widgets = {
            'point': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'จุดตรวจสอบ',
            }),
            'detail': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'รายละเอียดการตรวจ',
            }),
            'fix': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'การแก้ไข',
            }),
        }

ManualMaintenanceDailyItemFormSet = inlineformset_factory(
    Manual, ManualMaintenanceDailyItem, form=ManualMaintenanceDailyItemForm,
    extra=1, can_delete=True, max_num=100, validate_max=True,
)


class ManualMaintenancePeriodicItemForm(forms.ModelForm):
    class Meta:
        model = ManualMaintenancePeriodicItem
        fields = ['item', 'interval']
        widgets = {
            'item': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'รายการ',
            }),
            'interval': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'รอบเวลา',
            }),
        }

ManualMaintenancePeriodicItemFormSet = inlineformset_factory(
    Manual, ManualMaintenancePeriodicItem, form=ManualMaintenancePeriodicItemForm,
    extra=1, can_delete=True, max_num=100, validate_max=True,
)


class ManualTroubleshootItemForm(forms.ModelForm):
    class Meta:
        model = ManualTroubleshootItem
        fields = ['problem', 'cause', 'solution']
        widgets = {
            'problem': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'ปัญหา',
            }),
            'cause': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'สาเหตุ',
            }),
            'solution': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 2, 'placeholder': 'วิธีแก้ไข',
            }),
        }

ManualTroubleshootItemFormSet = inlineformset_factory(
    Manual, ManualTroubleshootItem, form=ManualTroubleshootItemForm,
    extra=1, can_delete=True, max_num=100, validate_max=True,
)


class ManualSpecItemForm(forms.ModelForm):
    class Meta:
        model = ManualSpecItem
        fields = ['label', 'value']
        widgets = {
            'label': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'รายการ',
            }),
            'value': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'ค่า',
            }),
        }

ManualSpecItemFormSet = inlineformset_factory(
    Manual, ManualSpecItem, form=ManualSpecItemForm,
    extra=1, can_delete=True, max_num=100, validate_max=True,
)


# ===== Task Manager Module =====

class MachineTaskForm(forms.ModelForm):
    class Meta:
        model = MachineTask
        fields = ['equipment', 'title', 'assignee', 'status', 'note',
                  'start_test_date', 'actual_current',
                  'rotation_direction_ok', 'control_local_ok', 'control_dcs_ok', 'control_remote_ok',
                  'participant_motor', 'participant_electrical', 'participant_control',
                  'participant_maintenance', 'participant_user']
        widgets = {
            'equipment': forms.Select(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'เช่น เตรียมความพร้อมก่อนสตาร์ทฤดูหีบ',
            }),
            'assignee': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'ชื่อผู้รับผิดชอบ',
            }),
            'status': forms.Select(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'note': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'rows': 3, 'placeholder': 'บันทึกปัญหาที่พบ (ถ้ามี)',
            }),
            'start_test_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
            }),
            'actual_current': forms.NumberInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'step': '0.01', 'placeholder': 'A',
            }),
            'participant_motor': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'ชื่อผู้ร่วมทดสอบ',
            }),
            'participant_electrical': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'ชื่อผู้ร่วมทดสอบ',
            }),
            'participant_control': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'ชื่อผู้ร่วมทดสอบ',
            }),
            'participant_maintenance': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'ชื่อผู้ร่วมทดสอบ',
            }),
            'participant_user': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border border-slate-300 rounded-lg text-sm '
                         'focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white',
                'placeholder': 'ชื่อผู้ร่วมทดสอบ',
            }),
        }


class MachineTaskVibrationForm(forms.ModelForm):
    class Meta:
        model = MachineTaskVibration
        exclude = ('task', 'phase')
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': _TW_VIBRATION}),
            'inspector': forms.TextInput(attrs={'class': _TW_VIBRATION}),
            'amp': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'de_ge': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'de_v': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'de_h': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'de_a': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'de_m': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'nde_ge': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'nde_v': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'nde_h': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'nde_a': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'nde_m': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'temp_de': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'temp_frame': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'temp_nde': forms.NumberInput(attrs={'class': _TW_VIBRATION, 'step': '0.01'}),
            'status': forms.Select(attrs={'class': _TW_VIBRATION}),
        }

