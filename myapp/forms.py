from django import forms
from .models import employee  # เรียกใช้ Model ที่เราสร้างไว้
from .models import BoilerOperationLog, ChengchenLog, TakumaLog, YoshimineLog, Banpong1Log,  Banpong2Log, MaintenanceLog, KPIMetric
from .models import MillReport, BoilerDailyKPI

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
            'jt_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border rounded'}),
            'jt_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full p-2 border rounded'}),
            'jt_problem_cause': forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-2 border rounded'}),
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

#class YoshimineForm(forms.ModelForm):
    #class Meta:
        #model = YoshimineLog
        #fields = '__all__'
        #widgets = {
            #'yos_date': forms.DateInput(attrs={'type': 'date'}),
            #'yos_time': forms.TimeInput(attrs={'type': 'time'}),
            #'yos_remark': forms.Textarea(attrs={'rows': 3}),
        #}

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
            'bp1_date': forms.DateInput(attrs={'type': 'date'}),
            'bp1_time': forms.TimeInput(attrs={'type': 'time'}),
            'bp1_remark': forms.Textarea(attrs={'rows': 3}),
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
            'ch_date': forms.DateInput(attrs={'type': 'date'}),
            'ch_time': forms.TimeInput(attrs={'type': 'time'}),
            'ch_remark': forms.Textarea(attrs={'rows': 3}),
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
            'tk_date': forms.DateInput(attrs={'type': 'date'}),
            'tk_time': forms.TimeInput(attrs={'type': 'time'}),
            'tk_remark': forms.Textarea(attrs={'rows': 3}),
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
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'problem': forms.Textarea(attrs={'rows': 3}),
            'cause': forms.Textarea(attrs={'rows': 3}),
            'solution': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(MaintenanceLogForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'is_leak': # Checkbox doesn't need w-full
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