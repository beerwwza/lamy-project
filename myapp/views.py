import os
import random
import pandas as pd
import numpy as np
import csv
import io
import urllib.request
import base64
from datetime import datetime, time, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction, connection
from django.db.models import Sum, Avg, Count, Q, F, Max
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse, Http404
from functools import wraps
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_POST
from django.core.serializers.json import DjangoJSONEncoder
from .models import BoilerOperationLog, ChengchenLog, TakumaLog, YoshimineLog, Banpong1Log, Banpong2Log, BoilerDailyKPI, LatheJob
from .forms import BoilerOperationForm, ChengchenForm, TakumaForm, YoshimineForm, Banpong1Form, Banpong2Form, BoilerDailyKPIForm
from .models import MillReport
from .forms import MillReportForm
from .models import MaintenanceLog, KPIMetric, InventoryItem, InventoryTransaction
from .forms import MaintenanceLogForm, KPIMetricForm
from .models import Equipment, EquipmentBOM, EquipmentLink, CBMVisualTest, CBMVibration, CBMThermoscan, CBMOilAnalysis, CBMAcoustic, InventoryItem, InventoryTransaction
from .models import PMSchedule
from .forms import EquipmentForm, EquipmentBOMForm, EquipmentLinkForm, CBMVisualTestForm, CBMVibrationForm, CBMThermoscanForm, CBMOilAnalysisForm, CBMAcousticForm, RepairDocumentForm
from .forms import PMScheduleForm, PMPlanForm, PMPlanItemForm, WorkOrderForm, WorkOrderStatusForm
from .forms import MachineTaskForm, MachineTaskVibrationForm
from .models import TrainingSkill, EmployeeSkillLevel, TrainingCourse, TrainingRecord, TrainingExamScore
from .models import (TrainingCourseMaterial, TrainingQuizQuestion, TrainingQuizChoice,
                      TrainingCourseExamAttempt, TrainingCourseExamAnswer)
from .forms import (TrainingSkillForm, EmployeeSkillLevelForm, TrainingCourseForm, TrainingRecordForm,
                     TrainingCourseMaterialForm,
                     TrainingQuizQuestionForm, TrainingQuizChoiceFormSet, EmployeeForm, CareerLadderStepForm)
from .forms import (
    ManualForm, ManualSafetyItemFormSet, ManualPartItemFormSet, ManualPrecheckItemFormSet,
    ManualOperatingStepFormSet, ManualMaintenanceDailyItemFormSet, ManualMaintenancePeriodicItemFormSet,
    ManualTroubleshootItemFormSet, ManualSpecItemFormSet,
)
from decimal import Decimal, InvalidOperation
from django.utils import timezone
import calendar


def _add_interval(base_date, value, unit):
    """คำนวณวันที่ถัดไปจากวันที่ตั้งต้น + จำนวนหน่วยความถี่ (ไม่ใช้ python-dateutil)"""
    if unit == 'day':
        return base_date + timedelta(days=value)
    if unit == 'week':
        return base_date + timedelta(weeks=value)
    # month
    month_index = base_date.month - 1 + value
    year = base_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base_date.day, calendar.monthrange(year, month)[1])
    return base_date.replace(year=year, month=month, day=day)


# --- Equipment Views ---
@login_required
def equipment_data(request, eq_id=None):
    if not eq_id:
        return redirect('equipment_list')
    equipment = Equipment.objects.filter(equipment_id=eq_id).first()
    if not equipment:
        messages.error(request, 'ไม่พบเครื่องจักรที่ระบุ')
        return redirect('equipment_list')
        
    boms = EquipmentBOM.objects.filter(equipment=equipment) if equipment else []
    # TODO: Fetch the latest records and forms for all 5 CBM models
    latest_cbm_visual = CBMVisualTest.objects.filter(equipment=equipment).order_by('-inspection_date').first() if equipment else None
    latest_cbm_vibration = CBMVibration.objects.filter(equipment=equipment).order_by('-inspection_date').first() if equipment else None
    latest_cbm_thermoscan = CBMThermoscan.objects.filter(equipment=equipment).order_by('-inspection_date').first() if equipment else None
    latest_cbm_oil = CBMOilAnalysis.objects.filter(equipment=equipment).order_by('-collection_date').first() if equipment else None
    latest_cbm_acoustic = CBMAcoustic.objects.filter(equipment=equipment).order_by('-inspection_date').first() if equipment else None
    
    # Optional list for a dropdown to switch equipment
    equipment_list = Equipment.objects.filter(is_active=True).values('equipment_id', 'name')
    
    motor_equipment = None
    if equipment and equipment.motor:
        motor_equipment = Equipment.objects.filter(equipment_id=equipment.motor.strip()).first()

    # Phase 2: maintenance history via FK
    maintenance_logs = MaintenanceLog.objects.filter(equipment_fk=equipment).order_by('-date')[:20]

    # Phase 3: PM schedules
    from django.urls import reverse
    pm_schedules = PMSchedule.objects.filter(equipment=equipment, is_active=True).order_by('next_due_date')
    pm_add_url   = reverse('pm_schedule_add', args=[equipment.equipment_id])

    # Phase 4: reliability metrics
    repair_count = MaintenanceLog.objects.filter(equipment_fk=equipment).count()
    total_down   = MaintenanceLog.objects.filter(equipment_fk=equipment).aggregate(
        td=Sum('downtime_stop'))['td'] or 0
    mttr_calc    = round(total_down / repair_count, 2) if repair_count else 0
    if equipment.mtbf and equipment.mttr:
        avail_pct = round(equipment.mtbf / (equipment.mtbf + equipment.mttr) * 100, 1) if (equipment.mtbf + equipment.mttr) else None
    else:
        avail_pct = None

    links = list(EquipmentLink.objects.filter(equipment=equipment)) if equipment else []
    if links:
        link_eq_ids = [l.linked_equipment_id.strip() for l in links if l.linked_equipment_id]
        link_eq_map = {e.equipment_id: e for e in Equipment.objects.filter(equipment_id__in=link_eq_ids)}
        for link in links:
            link.resolved = link_eq_map.get(link.linked_equipment_id.strip(), None) if link.linked_equipment_id else None

    today = timezone.now().date()
    pm_plans = list(PMPlan.objects.filter(equipment=equipment).prefetch_related('items'))
    for plan in pm_plans:
        base = plan.last_completed_date or plan.start_date
        plan.next_due_date = _add_interval(base, plan.interval_value, plan.interval_unit)
        days_left = (plan.next_due_date - today).days
        plan.days_left = days_left
        plan.days_overdue = abs(days_left) if days_left < 0 else 0
        plan.is_overdue = days_left < 0
        plan.is_due_soon = 0 <= days_left <= 7
    pm_plans.sort(key=lambda p: p.next_due_date)

    pm_summary = {
        'total': len(pm_plans),
        'overdue': sum(1 for p in pm_plans if p.is_overdue),
        'due_soon': sum(1 for p in pm_plans if p.is_due_soon),
        'completed_this_month': PMPlanCompletion.objects.filter(
            plan__equipment=equipment, completed_date__year=today.year, completed_date__month=today.month
        ).count(),
    }
    pm_completion_history = PMPlanCompletion.objects.filter(plan__equipment=equipment).select_related('plan')[:20]

    manuals = RepairDocument.objects.filter(equipment=equipment).select_related('uploaded_by').order_by('-created_at')
    form_document = RepairDocumentForm(initial={'equipment': equipment})

    work_orders = WorkOrder.objects.filter(equipment=equipment)
    completed_wos = [wo for wo in work_orders if wo.status == 'completed' and wo.completed_date]
    wo_avg_resolution_days = (
        round(sum((wo.completed_date - wo.report_date).days for wo in completed_wos) / len(completed_wos), 1)
        if completed_wos else None
    )
    wo_summary = {
        'total': len(work_orders),
        'pending': sum(1 for wo in work_orders if wo.status == 'pending'),
        'in_progress': sum(1 for wo in work_orders if wo.status == 'in_progress'),
        'completed': len(completed_wos),
        'avg_resolution_days': wo_avg_resolution_days,
    }

    context = {
        'equipment': equipment,
        'motor_equipment': motor_equipment,
        'links': links,
        'form_link': EquipmentLinkForm(),
        'boms': boms,
        'latest_cbm_visual': latest_cbm_visual,
        'latest_cbm_vibration': latest_cbm_vibration,
        'latest_cbm_thermoscan': latest_cbm_thermoscan,
        'latest_cbm_oil': latest_cbm_oil,
        'latest_cbm_acoustic': latest_cbm_acoustic,
        'equipment_list': equipment_list,
        'maintenance_logs': maintenance_logs,
        'pm_schedules': pm_schedules,
        'pm_add_url': pm_add_url,
        'repair_count': repair_count,
        'total_down': total_down,
        'mttr_calc': mttr_calc,
        'avail_pct': avail_pct,
        'form_visual': CBMVisualTestForm(),
        'form_vibration': CBMVibrationForm(),
        'form_thermoscan': CBMThermoscanForm(),
        'form_oil': CBMOilAnalysisForm(),
        'form_acoustic': CBMAcousticForm(),
        'form_bom': EquipmentBOMForm(),
        'pm_plans': pm_plans,
        'form_pm_plan': PMPlanForm(),
        'form_pm_item': PMPlanItemForm(),
        'work_orders': work_orders,
        'form_wo': WorkOrderForm(),
        'form_wo_status': WorkOrderStatusForm(),
        'pm_summary': pm_summary,
        'pm_completion_history': pm_completion_history,
        'wo_summary': wo_summary,
        'manuals': manuals,
        'form_document': form_document,
    }
    return render(request, 'myapp/equipment_data.html', context)

@login_required
@csrf_exempt
def equipment_form(request, eq_id=None):
    equipment = Equipment.objects.filter(equipment_id=eq_id).first() if eq_id else None
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=equipment)
        if form.is_valid():
            try:
                instance = form.save(commit=False)
                instance.mtbf = instance.mtbf if instance.mtbf is not None else 0
                instance.mttr = instance.mttr if instance.mttr is not None else 0
                instance.acc_cost = instance.acc_cost if instance.acc_cost is not None else 0
                instance.updated_by = request.user.username
                instance.save()
                messages.success(request, f'บันทึกข้อมูลเครื่องจักร {instance.equipment_id} เรียบร้อยแล้ว')
                if eq_id:
                    return redirect('equipment_form_edit', eq_id=instance.equipment_id)
                else:
                    return redirect('equipment_list')
            except Exception as e:
                messages.error(request, f'เกิดข้อผิดพลาดในการบันทึก: [{type(e).__name__}] {str(e)}')
        else:
            error_details = '; '.join([f'{k}: {", ".join(v)}' for k, v in form.errors.items()])
            messages.error(request, f'บันทึกไม่สำเร็จ — {error_details}')
        return render(request, 'myapp/equipment_form.html', {'form': form, 'equipment': equipment})

    else:
        form = EquipmentForm(instance=equipment)

    return render(request, 'myapp/equipment_form.html', {'form': form, 'equipment': equipment})

@login_required
def equipment_bom(request):
    # This is a popup modal view. Passing the parameters into the template.
    action = request.GET.get('action', 'add')
    part_no = request.GET.get('partNo', '')
    
    # Send an empty form to the frontend
    form = EquipmentBOMForm()
    
    context = {
        'action': action,
        'part_no': part_no,
        'form': form
    }
    return render(request, 'myapp/equipment_BOM.html', context)

@login_required
def bom_add(request, eq_id):
    equipment = Equipment.objects.filter(equipment_id=eq_id).first()
    if not equipment:
        messages.error(request, 'ไม่พบเครื่องจักรที่ระบุ')
        return redirect('equipment_list')
    
    if request.method == 'POST':
        form = EquipmentBOMForm(request.POST)
        if form.is_valid():
            bom = form.save(commit=False)
            bom.equipment = equipment
            bom.save()
            messages.success(request, f'เพิ่มอะไหล่ {bom.part_no} เรียบร้อยแล้ว')
        else:
            messages.error(request, 'เพิ่มอะไหล่ไม่สำเร็จ กรุณาตรวจสอบข้อมูลอีกครั้ง')
    
    return redirect('equipment_data_detail', eq_id=eq_id)

@login_required
def bom_delete(request, bom_id):
    bom = EquipmentBOM.objects.filter(id=bom_id).first()
    if bom:
        eq_id = bom.equipment.equipment_id
        part_no = bom.part_no
        bom.delete()
        messages.success(request, f'ลบอะไหล่ {part_no} เรียบร้อยแล้ว')
        return redirect('equipment_data_detail', eq_id=eq_id)
    else:
        messages.error(request, 'ไม่พบรายการอะไหล่ที่ต้องการลบ')
        return redirect('equipment_list')

@login_required
def bom_edit(request, bom_id):
    bom = EquipmentBOM.objects.filter(id=bom_id).first()
    if not bom:
        messages.error(request, 'ไม่พบรายการอะไหล่ที่ต้องการแก้ไข')
        return redirect('equipment_list')

    eq_id = bom.equipment.equipment_id
    if request.method == 'POST':
        form = EquipmentBOMForm(request.POST, instance=bom)
        if form.is_valid():
            form.save()
            messages.success(request, f'แก้ไขอะไหล่ {bom.part_no} เรียบร้อยแล้ว')
        else:
            messages.error(request, 'แก้ไขอะไหล่ไม่สำเร็จ กรุณาตรวจสอบข้อมูลอีกครั้ง')
    return redirect('equipment_data_detail', eq_id=eq_id)

@login_required
def equipment_link_add(request, eq_id):
    equipment = Equipment.objects.filter(equipment_id=eq_id).first()
    if not equipment:
        messages.error(request, 'ไม่พบเครื่องจักรที่ระบุ')
        return redirect('equipment_list')
    if request.method == 'POST':
        form = EquipmentLinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.equipment = equipment
            link.save()
            messages.success(request, f'เพิ่ม {link.label} เรียบร้อยแล้ว')
        else:
            messages.error(request, 'เพิ่มไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    return redirect('equipment_data_detail', eq_id=eq_id)


@login_required
def equipment_link_delete(request, link_id):
    link = EquipmentLink.objects.filter(id=link_id).first()
    if link:
        eq_id = link.equipment.equipment_id
        label = link.label
        link.delete()
        messages.success(request, f'ลบ {label} เรียบร้อยแล้ว')
        return redirect('equipment_data_detail', eq_id=eq_id)
    messages.error(request, 'ไม่พบรายการที่ต้องการลบ')
    return redirect('equipment_list')


# --- PM Plan Views ---
@login_required
def pm_plan_add(request, eq_id):
    equipment = Equipment.objects.filter(equipment_id=eq_id).first()
    if not equipment:
        messages.error(request, 'ไม่พบเครื่องจักรที่ระบุ')
        return redirect('equipment_list')
    if request.method == 'POST':
        form = PMPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.equipment = equipment
            plan.save()
            messages.success(request, f'เพิ่มแผน PM {plan.pm_code} เรียบร้อยแล้ว')
        else:
            messages.error(request, 'เพิ่มแผน PM ไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    return redirect('equipment_data_detail', eq_id=eq_id)


@login_required
def pm_plan_edit(request, plan_id):
    plan = PMPlan.objects.filter(id=plan_id).first()
    if not plan:
        messages.error(request, 'ไม่พบแผน PM ที่ต้องการแก้ไข')
        return redirect('equipment_list')
    eq_id = plan.equipment.equipment_id
    if request.method == 'POST':
        form = PMPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, f'แก้ไขแผน PM {plan.pm_code} เรียบร้อยแล้ว')
        else:
            messages.error(request, 'แก้ไขแผน PM ไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    return redirect('equipment_data_detail', eq_id=eq_id)


@login_required
def pm_plan_delete(request, plan_id):
    plan = PMPlan.objects.filter(id=plan_id).first()
    if plan:
        eq_id = plan.equipment.equipment_id
        pm_code = plan.pm_code
        plan.delete()
        messages.success(request, f'ลบแผน PM {pm_code} เรียบร้อยแล้ว')
        return redirect('equipment_data_detail', eq_id=eq_id)
    messages.error(request, 'ไม่พบแผน PM ที่ต้องการลบ')
    return redirect('equipment_list')


@login_required
@require_POST
def pm_plan_complete(request, plan_id):
    plan = PMPlan.objects.filter(id=plan_id).first()
    if plan:
        eq_id = plan.equipment.equipment_id
        today = timezone.now().date()
        plan.last_completed_date = today
        plan.save()
        PMPlanCompletion.objects.create(plan=plan, completed_date=today, completed_by=request.user.username)
        messages.success(request, f'บันทึกการทำ PM {plan.pm_code} เรียบร้อยแล้ว')
        return redirect('equipment_data_detail', eq_id=eq_id)
    messages.error(request, 'ไม่พบแผน PM ที่ระบุ')
    return redirect('equipment_list')


@login_required
def pm_plan_item_add(request, plan_id):
    plan = PMPlan.objects.filter(id=plan_id).first()
    if not plan:
        messages.error(request, 'ไม่พบแผน PM ที่ระบุ')
        return redirect('equipment_list')
    eq_id = plan.equipment.equipment_id
    if request.method == 'POST':
        form = PMPlanItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.plan = plan
            item.save()
            messages.success(request, f'เพิ่มรายการตรวจ "{item.description}" เรียบร้อยแล้ว')
        else:
            messages.error(request, 'เพิ่มรายการตรวจไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    return redirect('equipment_data_detail', eq_id=eq_id)


@login_required
def pm_plan_item_delete(request, item_id):
    item = PMPlanItem.objects.filter(id=item_id).first()
    if item:
        eq_id = item.plan.equipment.equipment_id
        description = item.description
        item.delete()
        messages.success(request, f'ลบรายการตรวจ "{description}" เรียบร้อยแล้ว')
        return redirect('equipment_data_detail', eq_id=eq_id)
    messages.error(request, 'ไม่พบรายการตรวจที่ต้องการลบ')
    return redirect('equipment_list')


# --- Work Order Views ---
@login_required
def work_order_add(request, eq_id):
    equipment = Equipment.objects.filter(equipment_id=eq_id).first()
    if not equipment:
        messages.error(request, 'ไม่พบเครื่องจักรที่ระบุ')
        return redirect('equipment_list')
    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.equipment = equipment
            if not wo.report_date:
                wo.report_date = timezone.now().date()
            yymm = wo.report_date.strftime('%y%m')
            seq = WorkOrder.objects.filter(wo_no__startswith=f'WO-{yymm}-').count() + 1
            wo.wo_no = f'WO-{yymm}-{seq:04d}'
            wo.status = 'pending'
            wo.save()
            messages.success(request, f'แจ้งซ่อม {wo.wo_no} เรียบร้อยแล้ว')
        else:
            messages.error(request, 'แจ้งซ่อมไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    return redirect('equipment_data_detail', eq_id=eq_id)


@login_required
def work_order_edit(request, wo_id):
    wo = WorkOrder.objects.filter(id=wo_id).first()
    if not wo:
        messages.error(request, 'ไม่พบใบสั่งซ่อมที่ระบุ')
        return redirect('equipment_list')
    eq_id = wo.equipment.equipment_id
    if request.method == 'POST':
        form = WorkOrderStatusForm(request.POST, instance=wo)
        if form.is_valid():
            wo = form.save(commit=False)
            if wo.status == 'completed' and not wo.completed_date:
                wo.completed_date = timezone.now().date()
            wo.save()
            messages.success(request, f'อัปเดตสถานะ {wo.wo_no} เรียบร้อยแล้ว')
        else:
            messages.error(request, 'อัปเดตสถานะไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    return redirect('equipment_data_detail', eq_id=eq_id)


@login_required
def work_order_delete(request, wo_id):
    wo = WorkOrder.objects.filter(id=wo_id).first()
    if wo:
        eq_id = wo.equipment.equipment_id
        wo_no = wo.wo_no
        wo.delete()
        messages.success(request, f'ลบใบสั่งซ่อม {wo_no} เรียบร้อยแล้ว')
        return redirect('equipment_data_detail', eq_id=eq_id)
    messages.error(request, 'ไม่พบใบสั่งซ่อมที่ต้องการลบ')
    return redirect('equipment_list')


@login_required
def equipment_cbm(request, eq_id=None):
    equipment = Equipment.objects.filter(equipment_id=eq_id).first()
    if not equipment:
        messages.error(request, 'ไม่พบเครื่องจักรที่ระบุ')
        return redirect('equipment_list')
        
    if request.method == 'POST':
        cbm_type = request.POST.get('cbm_type')
        form = None
        
        # Determine which form to process
        if cbm_type == 'visual':
            form = CBMVisualTestForm(request.POST)
        elif cbm_type == 'vibration':
            form = CBMVibrationForm(request.POST)
        elif cbm_type == 'thermoscan':
            form = CBMThermoscanForm(request.POST)
        elif cbm_type == 'oil':
            form = CBMOilAnalysisForm(request.POST)
        elif cbm_type == 'acoustic':
            form = CBMAcousticForm(request.POST)
            
        if form and form.is_valid():
            cbm = form.save(commit=False)
            cbm.equipment = equipment
            cbm.save()
            messages.success(request, f'บันทึกข้อมูล {cbm_type} สำเร็จ')
        else:
            messages.error(request, 'กรุณาตรวจสอบข้อมูลอีกครั้ง: ' + str(form.errors if form else 'Invalid CBM type'))
    
    return redirect('equipment_data_detail', eq_id=eq_id)


CBM_TYPE_CONFIG = {
    'visual':     {'model': CBMVisualTest, 'date_field': 'inspection_date', 'label': 'Visual Test', 'numeric_fields': []},
    'vibration':  {'model': CBMVibration, 'date_field': 'inspection_date', 'label': 'Vibration',
                   'numeric_fields': [
                       ('amp', 'Amp'),
                       ('de_ge', 'DE (gE)'), ('de_v', 'DE (V)'), ('de_h', 'DE (H)'), ('de_a', 'DE (A)'), ('de_m', 'DE (M)'),
                       ('nde_ge', 'NDE (gE)'), ('nde_v', 'NDE (V)'), ('nde_h', 'NDE (H)'), ('nde_a', 'NDE (A)'), ('nde_m', 'NDE (M)'),
                       ('temp_de', 'Temp.(DE)'), ('temp_frame', 'Temp.(FRAME)'), ('temp_nde', 'Temp.(NDE)'),
                   ]},
    'thermoscan': {'model': CBMThermoscan, 'date_field': 'inspection_date', 'label': 'Thermoscan',
                   'numeric_fields': [('max_temp', 'Max Temp (°C)'), ('ambient_temp', 'Ambient (°C)'), ('delta_t', 'Delta T (°C)')]},
    'oil':        {'model': CBMOilAnalysis, 'date_field': 'collection_date', 'label': 'Oil Analysis',
                   'numeric_fields': [('viscosity', 'Viscosity (cSt)'), ('water_content', 'Water Content (%)')]},
    'acoustic':   {'model': CBMAcoustic, 'date_field': 'inspection_date', 'label': 'Acoustic Emission',
                   'numeric_fields': [('decibel', 'Decibel (dB/RMS)')]},
}

@login_required
def cbm_summary(request, eq_id, cbm_type):
    equipment = Equipment.objects.filter(equipment_id=eq_id).first()
    if not equipment:
        messages.error(request, 'ไม่พบเครื่องจักรที่ระบุ')
        return redirect('equipment_list')

    config = CBM_TYPE_CONFIG.get(cbm_type)
    if not config:
        messages.error(request, 'ประเภทการตรวจสอบไม่ถูกต้อง')
        return redirect('equipment_data_detail', eq_id=eq_id)

    records = list(config['model'].objects.filter(equipment=equipment).order_by(config['date_field']))
    dates = [getattr(r, config['date_field']).strftime('%Y-%m-%d') for r in records]

    condition_counts = None
    if cbm_type == 'visual':
        condition_counts = {
            'good': sum(1 for r in records if r.overall_condition == 'good'),
            'fair': sum(1 for r in records if r.overall_condition == 'fair'),
            'poor': sum(1 for r in records if r.overall_condition == 'poor'),
        }
        chart_data_json = json.dumps(condition_counts, cls=DjangoJSONEncoder)
    else:
        chart_data = {
            'labels': dates,
            'datasets': [
                {'label': field_label, 'data': [getattr(r, field_name) for r in records]}
                for field_name, field_label in config['numeric_fields']
            ],
        }
        chart_data_json = json.dumps(chart_data, cls=DjangoJSONEncoder)

    context = {
        'equipment': equipment,
        'cbm_type': cbm_type,
        'cbm_label': config['label'],
        'records': list(reversed(records)),
        'chart_data_json': chart_data_json,
        'condition_counts': condition_counts,
    }
    return render(request, 'myapp/cbm_summary.html', context)


ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
ALLOWED_IMAGE_MIMETYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'}

@login_required
def upload_equipment_image(request, eq_id):
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded = request.FILES['image']
        ext = os.path.splitext(uploaded.name)[1].lower()
        content_type = uploaded.content_type.split(';')[0].strip().lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS or content_type not in ALLOWED_IMAGE_MIMETYPES:
            return JsonResponse({'status': 'error', 'message': 'อนุญาตเฉพาะไฟล์รูปภาพ (jpg, png, gif, webp, bmp) เท่านั้น'})
        equipment = Equipment.objects.filter(equipment_id=eq_id).first()
        if equipment:
            equipment.image = uploaded
            equipment.save()
            return JsonResponse({'status': 'success', 'message': 'อัปโหลดรูปภาพสำเร็จ'})
        return JsonResponse({'status': 'error', 'message': 'ไม่พบเครื่องจักร'})
    return JsonResponse({'status': 'error', 'message': 'ไม่มีรูปภาพถูกส่งมา'})

PROCESS_OTHER_BUCKET = '__other__'

EQUIPMENT_INLINE_FIELDS = {
    'name': 'str', 'location': 'str', 'process': 'str', 'belongs_to': 'str',
    'model': 'str', 'manufacturer': 'str', 'serial_no': 'str', 'capacity': 'str',
    'head_size': 'str', 'power_kw': 'decimal', 'rpm_input': 'decimal', 'rpm': 'str', 'motor': 'str', 'panel': 'str',
    'starter': 'str', 'breaker': 'str', 'drive_type': 'str',
    'installation_date': 'date', 'warranty_exp': 'date',
    'purchase_price': 'decimal', 'replacement_cost': 'decimal',
    'priority_level': 'choice', 'mtbf': 'float', 'mttr': 'float', 'acc_cost': 'decimal',
}

@login_required
@require_POST
def equipment_inline_update(request, eq_id):
    equipment = Equipment.objects.filter(equipment_id=eq_id).first()
    if not equipment:
        return JsonResponse({'status': 'error', 'message': 'ไม่พบเครื่องจักร'})

    for field, ftype in EQUIPMENT_INLINE_FIELDS.items():
        if field not in request.POST:
            continue
        raw = request.POST.get(field, '').strip()
        try:
            if ftype == 'str':
                setattr(equipment, field, raw)
            elif ftype == 'date':
                setattr(equipment, field, datetime.strptime(raw, '%Y-%m-%d').date() if raw else None)
            elif ftype == 'float':
                setattr(equipment, field, float(raw) if raw else 0)
            elif ftype == 'decimal':
                setattr(equipment, field, Decimal(raw) if raw else Decimal('0'))
            elif ftype == 'choice':
                if raw in ('1', '2', '3'):
                    setattr(equipment, field, raw)
        except (ValueError, InvalidOperation):
            return JsonResponse({'status': 'error', 'message': f'ค่าฟิลด์ {field} ไม่ถูกต้อง'})

    equipment.updated_by = request.user.username
    equipment.save()
    return JsonResponse({'status': 'success', 'message': 'บันทึกข้อมูลเรียบร้อยแล้ว'})

@login_required
def equipment_toggle_status(request, eq_id):
    equipment = Equipment.objects.filter(equipment_id=eq_id).first()
    if equipment:
        equipment.is_active = not equipment.is_active
        equipment.save()
        status_text = "เปิดใช้งาน" if equipment.is_active else "ปิดใช้งาน"
        messages.success(request, f'เปลี่ยนสถานะการใช้งานเครื่องจักร {equipment.equipment_id} เป็น {status_text} เรียบร้อยแล้ว')
    else:
        messages.error(request, 'ไม่พบเครื่องจักรที่ระบุ')
    return redirect('equipment_list')


@login_required
def api_equipment_by_process(request):
    process = request.GET.get('process', '').strip()
    if not process:
        return JsonResponse({'error': 'ต้องระบุ process'}, status=400)

    active_names = list(ProcessCategory.objects.filter(is_active=True).values_list('name', flat=True))
    qs = Equipment.objects.filter(is_active=True)
    if process == PROCESS_OTHER_BUCKET:
        qs = qs.filter(Q(process__isnull=True) | Q(process__exact='') | ~Q(process__in=active_names))
    else:
        if process not in active_names:
            return JsonResponse({'error': 'ไม่พบกระบวนการที่ระบุ'}, status=400)
        qs = qs.filter(process=process)

    rows = qs.order_by('equipment_id').values('equipment_id', 'name', 'power_kw', 'rpm_input', 'rpm')
    equipment = [
        {
            'equipment_id': r['equipment_id'],
            'name': r['name'],
            'power_kw': str(r['power_kw']) if r['power_kw'] is not None else '',
            'rpm_input': str(r['rpm_input']) if r['rpm_input'] is not None else '',
            'rpm': r['rpm'] or '',
        }
        for r in rows
    ]
    return JsonResponse({'equipment': equipment})


# ─── PM Schedule Views ────────────────────────────────────────────────────────

@login_required
def pm_schedule_add(request, eq_id):
    equipment = get_object_or_404(Equipment, equipment_id=eq_id)
    if request.method == 'POST':
        form = PMScheduleForm(request.POST)
        if form.is_valid():
            pm = form.save(commit=False)
            pm.equipment = equipment
            if pm.last_completed_date and not pm.next_due_date:
                pm.calculate_next_due()
            pm.save()
            messages.success(request, f'เพิ่มแผน PM "{pm.task_name}" เรียบร้อยแล้ว')
            return redirect('equipment_data_detail', eq_id=eq_id)
    else:
        form = PMScheduleForm()
    return render(request, 'myapp/pm_form.html', {
        'form': form, 'equipment': equipment, 'action': 'เพิ่มแผน PM ใหม่',
    })


@login_required
def pm_schedule_edit(request, pm_id):
    pm = get_object_or_404(PMSchedule, id=pm_id)
    if request.method == 'POST':
        form = PMScheduleForm(request.POST, instance=pm)
        if form.is_valid():
            pm = form.save()
            messages.success(request, f'แก้ไขแผน PM "{pm.task_name}" เรียบร้อยแล้ว')
            return redirect('equipment_data_detail', eq_id=pm.equipment_id)
    else:
        form = PMScheduleForm(instance=pm)
    return render(request, 'myapp/pm_form.html', {
        'form': form, 'equipment': pm.equipment, 'action': 'แก้ไขแผน PM', 'pm': pm,
    })


@login_required
def pm_schedule_complete(request, pm_id):
    from datetime import date
    if request.method != 'POST':
        return redirect('equipment_list')
    pm = get_object_or_404(PMSchedule, id=pm_id)
    pm.last_completed_date = date.today()
    pm.calculate_next_due()
    pm.save()
    messages.success(request, f'บันทึกการทำ PM "{pm.task_name}" เรียบร้อย — ครั้งต่อไป {pm.next_due_date}')
    return redirect('equipment_data_detail', eq_id=pm.equipment_id)


@login_required
def pm_schedule_delete(request, pm_id):
    if request.method != 'POST':
        return redirect('equipment_list')
    pm = get_object_or_404(PMSchedule, id=pm_id)
    eq_id = pm.equipment_id
    task  = pm.task_name
    pm.delete()
    messages.success(request, f'ลบแผน PM "{task}" เรียบร้อยแล้ว')
    return redirect('equipment_data_detail', eq_id=eq_id)


@login_required
def equipment_list(request):
    search_query    = request.GET.get('q', '').strip()
    process_filter  = request.GET.get('process', '')
    location_filter = request.GET.get('location', '')
    status_filter   = request.GET.get('status', '')  # '', 'active', 'inactive'

    equipments = Equipment.objects.annotate(
        manual_count=Count('repair_documents', distinct=True)
    ).order_by('equipment_id')

    active_process_names = list(
        ProcessCategory.objects.filter(is_active=True).order_by('name').values_list('name', flat=True)
    )

    if process_filter == PROCESS_OTHER_BUCKET:
        equipments = equipments.filter(
            Q(process__isnull=True) | Q(process__exact='') | ~Q(process__in=active_process_names)
        )
    elif process_filter:
        equipments = equipments.filter(process=process_filter)
    if location_filter:
        equipments = equipments.filter(location=location_filter)
    if status_filter == 'active':
        equipments = equipments.filter(is_active=True)
    elif status_filter == 'inactive':
        equipments = equipments.filter(is_active=False)
    if search_query:
        equipments = equipments.filter(
            Q(equipment_id__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(manufacturer__icontains=search_query) |
            Q(serial_no__icontains=search_query)
        )

    paginator = Paginator(equipments, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    querystring = request.GET.copy()
    querystring.pop('page', None)
    querystring = querystring.urlencode()

    locations = Equipment.objects.exclude(location__isnull=True).exclude(location__exact='').values_list('location', flat=True).distinct().order_by('location')

    context = {
        'page_obj': page_obj,
        'processes': active_process_names,
        'locations': list(locations),
        'search_query': search_query,
        'process_filter': process_filter,
        'location_filter': location_filter,
        'status_filter': status_filter,
        'querystring': querystring,
    }
    return render(request, 'myapp/equipment_list.html', context)

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
    # 1. Milling Data
    # A. Total Accumulated Cane & Avg Trash (All Records)
    mill_agg = MillReport.objects.aggregate(
        total_cane=Sum('cane_weight'),
        avg_trash=Avg('trash')
    )
    
    # B. Latest Records for Line A & Line B (Filter out empty/future records)
    line_a_obj = MillReport.objects.filter(line='A', cane_weight__gt=0).order_by('-date').first()
    line_b_obj = MillReport.objects.filter(line='B', cane_weight__gt=0).order_by('-date').first()
    
    recent_mill_qs = MillReport.objects.select_related('created_by', 'updated_by').order_by('-date')[:10]
    recent_mill = []
    for r in recent_mill_qs:
        recent_mill.append({
            'date': r.date.strftime('%Y-%m-%d'),
            'line': r.line,
            'cane_weight': f"{r.cane_weight:,.0f}" if r.cane_weight else "0",
            'ccs': f"{r.ccs:.2f}" if r.ccs else "-",
            'created_by': r.created_by.get_full_name() or r.created_by.username if r.created_by else None,
            'created_at': r.created_at.strftime('%d/%m %H:%M') if r.created_at else None,
            'updated_by': r.updated_by.get_full_name() or r.updated_by.username if r.updated_by else None,
            'updated_at': r.updated_at.strftime('%d/%m %H:%M') if r.updated_at else None,
        })

    mill_data = {
        'total_cane': f"{mill_agg['total_cane']:,.0f}" if mill_agg['total_cane'] else "0",
        'avg_trash': f"{mill_agg['avg_trash']:.2f}" if mill_agg['avg_trash'] else "0.00",
        'recent': recent_mill,
        'line_a': {
            'date': line_a_obj.date.strftime('%Y-%m-%d') if line_a_obj else "-",
            'cane_weight': f"{line_a_obj.cane_weight:,.0f}" if line_a_obj and line_a_obj.cane_weight else "0",
            'ccs': f"{line_a_obj.ccs:.2f}" if line_a_obj and line_a_obj.ccs else "0.00",
            'extraction_1st': f"{line_a_obj.first_mill_extraction:.2f}" if line_a_obj and line_a_obj.first_mill_extraction else "0.00",
            'pol_extraction': f"{line_a_obj.reduced_pol_extraction:.2f}" if line_a_obj and line_a_obj.reduced_pol_extraction else "0.00",
            'purity_drop': f"{line_a_obj.purity_drop:.2f}" if line_a_obj and line_a_obj.purity_drop else "0.00",
        },
        'line_b': {
            'date': line_b_obj.date.strftime('%Y-%m-%d') if line_b_obj else "-",
            'cane_weight': f"{line_b_obj.cane_weight:,.0f}" if line_b_obj and line_b_obj.cane_weight else "0",
            'ccs': f"{line_b_obj.ccs:.2f}" if line_b_obj and line_b_obj.ccs else "0.00",
            'extraction_1st': f"{line_b_obj.first_mill_extraction:.2f}" if line_b_obj and line_b_obj.first_mill_extraction else "0.00",
            'pol_extraction': f"{line_b_obj.reduced_pol_extraction:.2f}" if line_b_obj and line_b_obj.reduced_pol_extraction else "0.00",
            'purity_drop': f"{line_b_obj.purity_drop:.2f}" if line_b_obj and line_b_obj.purity_drop else "0.00",
        }
    }

    # 2. Boiler Data — ดึงจาก BoilerDailyKPI เหมือนหน้า boiler.html
    boiler_kpi = BoilerDailyKPI.objects.order_by('-date').first()
    boiler_data = {
        'date': boiler_kpi.date.strftime('%Y-%m-%d') if boiler_kpi else "-",
        'downtime_a': float(boiler_kpi.downtime_a) if boiler_kpi else 0,
        'downtime_b': float(boiler_kpi.downtime_b) if boiler_kpi else 0,
        'reduced_cap_a': float(boiler_kpi.reduced_cap_a) if boiler_kpi else 0,
        'reduced_cap_b': float(boiler_kpi.reduced_cap_b) if boiler_kpi else 0,
        'flow_20bar': float(boiler_kpi.flow_20bar) if boiler_kpi else 0,
        'flow_40bar': float(boiler_kpi.flow_40bar) if boiler_kpi else 0,
        'alert': bool(boiler_kpi and (boiler_kpi.downtime_a > 1.01 or boiler_kpi.downtime_b > 1.01
                                      or boiler_kpi.reduced_cap_a > 1.02 or boiler_kpi.reduced_cap_b > 1.02)),
        'downtime_a_alert': bool(boiler_kpi and boiler_kpi.downtime_a > 1.01),
        'downtime_b_alert': bool(boiler_kpi and boiler_kpi.downtime_b > 1.01),
        'reduced_cap_a_alert': bool(boiler_kpi and boiler_kpi.reduced_cap_a > 1.02),
        'reduced_cap_b_alert': bool(boiler_kpi and boiler_kpi.reduced_cap_b > 1.02),
    }

    # 3. Maintenance Data — วันนี้ (ยกเว้นโรงกลึง)
    today = datetime.now().date()
    maint_qs = MaintenanceLog.objects.filter(date=today).exclude(dept='โรงกลึง')
    maint_count = maint_qs.count()
    maint_agg = maint_qs.aggregate(
        total_stop=Sum('downtime_stop'),
        total_reduced=Sum('downtime_reduced'),
    )
    maint_stop = maint_agg['total_stop'] or 0
    maint_reduced = maint_agg['total_reduced'] or 0
    maint_leaks = maint_qs.filter(is_leak=True).count()
    maint_mttr = round(maint_stop / maint_count, 2) if maint_count > 0 else 0
    maint_data = {
        'repairs': maint_count,
        'mttr': maint_mttr,
        'downtime_stop': round(maint_stop, 2),
        'downtime_reduced': round(maint_reduced, 2),
        'leaks': maint_leaks,
        'alert': maint_count > 0 or maint_leaks > 0,
        'mttr_alert': maint_mttr > 2,
        'stop_alert': float(maint_stop) > 0,
        'reduced_alert': float(maint_reduced) > 0,
        'leaks_alert': maint_leaks > 0,
    }

    # 4. Lathe Data
    lathe_qs = LatheJob.objects.all()
    lathe_agg = lathe_qs.aggregate(total_pieces=Sum('pieces'), total_hours=Sum('hours'))
    lathe_pending = lathe_qs.filter(status='Pending').count()
    lathe_data = {
        'pending': lathe_pending,
        'in_progress': lathe_qs.filter(status='In Progress').count(),
        'done': lathe_qs.filter(status='Done').count(),
        'total_pieces': int(lathe_agg['total_pieces'] or 0),
        'total_hours': round(float(lathe_agg['total_hours'] or 0), 1),
        'alert': lathe_pending > 5,
    }

    context = {
        'mill': mill_data,
        'boiler': boiler_data,
        'maint': maint_data,
        'lathe': lathe_data,
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

    def fmt_update(obj, date_field, time_field):
        d = getattr(obj, date_field, None) if obj else None
        t = getattr(obj, time_field, None) if obj else None
        if d and t:
            return f"{d.strftime('%d/%m/%Y')} {t.strftime('%H:%M')}"
        return None

    machine_data = {
        'john_thomson': {
            'name': 'John Thomson',
            'press': get_val(jt, 'jt_steam_pressure'),
            'flow': get_val(jt, 'jt_steam_flow'),
            'temp': get_val(jt, 'jt_temp_steam'),
            'last_update': fmt_update(jt, 'jt_date', 'jt_time'),
            'all_fields': get_all_fields(jt, 'jt')
        },
        'chengchen': {
            'name': 'Chengchen',
            'press': get_val(ch, 'ch_steam_pressure'),
            'flow': get_val(ch, 'ch_steam_flow'),
            'temp': get_val(ch, 'ch_steam_temp'),
            'last_update': fmt_update(ch, 'ch_date', 'ch_time'),
            'all_fields': get_all_fields(ch, 'ch')
        },
        'takuma': {
            'name': 'Takuma',
            'press': get_val(tk, 'tk_steam_pressure'),
            'flow': get_val(tk, 'tk_steam_flow'),
            'temp': get_val(tk, 'tk_steam_temp'),
            'last_update': fmt_update(tk, 'tk_date', 'tk_time'),
            'all_fields': get_all_fields(tk, 'tk')
        },
        'yoshimine': {
            'name': 'Yoshimine',
            'press': get_val(yos, 'yos_main_steam_pressure'),
            'flow': get_val(yos, 'yos_main_steam_flow'),
            'temp': get_val(yos, 'yos_main_steam_temp'),
            'last_update': fmt_update(yos, 'yos_date', 'yos_time'),
            'all_fields': get_all_fields(yos, 'yos')
        },
        'banpong1': {
            'name': 'Banpong 1',
            'press': get_val(bp1, 'bp1_main_steam_pressure'),
            'flow': get_val(bp1, 'bp1_main_steam_flow'),
            'temp': get_val(bp1, 'bp1_main_steam_temp'),
            'last_update': fmt_update(bp1, 'bp1_date', 'bp1_time'),
            'all_fields': get_all_fields(bp1, 'bp1')
        },
        'banpong2': {
            'name': 'Banpong 2',
            'press': get_val(bp2, 'bp2_main_steam_pressure'),
            'flow': get_val(bp2, 'bp2_main_steam_flow'),
            'temp': get_val(bp2, 'bp2_main_steam_temp'),
            'last_update': fmt_update(bp2, 'bp2_date', 'bp2_time'),
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
                # Set active records based on (date, hour)
                active_map = {}
                for obj in objects_to_create:
                    d = getattr(obj, f'{prefix}_date')
                    t = getattr(obj, f'{prefix}_time')
                    if d and t:
                        active_map[(d, t.hour)] = obj
                
                # Update existing records to is_active=False
                for (d, h) in active_map.keys():
                    model_class.objects.filter(**{
                        f'{prefix}_date': d,
                        f'{prefix}_time__hour': h,
                        'is_active': True
                    }).update(is_active=False)
                
                # Handle active state within the imported file itself
                for obj in objects_to_create:
                    d = getattr(obj, f'{prefix}_date')
                    t = getattr(obj, f'{prefix}_time')
                    if d and t and active_map.get((d, t.hour)) is obj:
                        obj.is_active = True
                    else:
                        obj.is_active = False

                model_class.objects.bulk_create(objects_to_create)
                messages.success(request, f'Import สำเร็จ: {len(objects_to_create)} รายการ ({machine_type})')
            else:
                messages.warning(request, f'ไม่พบข้อมูลที่สมบูรณ์ (ต้องมีทั้งวันที่และเวลา) ตรวจสอบไฟล์: {file.name}')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            
    return redirect('operation_dashboard')

def save_timeseries_log(model_class, form, date_field, time_field):
    instance = form.save(commit=False)
    date_val = getattr(instance, date_field)
    time_val = getattr(instance, time_field)
    
    if date_val and time_val:
        filter_kwargs = {
            date_field: date_val,
            f"{time_field}__hour": time_val.hour,
            'is_active': True
        }
        model_class.objects.filter(**filter_kwargs).update(is_active=False)
        
    instance.is_active = True
    instance.save()
    return instance

@login_required
def boiler_operation_add(request):
    if request.method == 'POST':
        form = BoilerOperationForm(request.POST)
        if form.is_valid():
            save_timeseries_log(BoilerOperationLog, form, 'jt_date', 'jt_time')
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
            save_timeseries_log(YoshimineLog, form, 'yos_date', 'yos_time')
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
            save_timeseries_log(Banpong1Log, form, 'bp1_date', 'bp1_time')
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
            save_timeseries_log(ChengchenLog, form, 'ch_date', 'ch_time')
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
            save_timeseries_log(TakumaLog, form, 'tk_date', 'tk_time')
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
            save_timeseries_log(Banpong2Log, form, 'bp2_date', 'bp2_time')
            return redirect('boiler')
    else:
        form = Banpong2Form()
    return render(request, 'myapp/banpong2_form.html', {'form': form})

@login_required
def boiler(request):
    from datetime import date as date_cls

    # 1. Date range from query params
    days_param = request.GET.get('days', '7')
    start_str = request.GET.get('start', '')
    end_str = request.GET.get('end', '')
    today = date_cls.today()

    is_custom = bool(start_str and end_str)
    if is_custom:
        try:
            start_date = date_cls.fromisoformat(start_str)
            end_date = date_cls.fromisoformat(end_str)
        except ValueError:
            start_date = today - timedelta(days=6)
            end_date = today
            is_custom = False
    else:
        try:
            days = int(days_param)
        except ValueError:
            days = 7
        end_date = today
        start_date = today - timedelta(days=days - 1)

    # 2. Latest KPI in period
    latest_kpi = BoilerDailyKPI.objects.filter(date__lte=end_date).order_by('-date').first()

    # 3. History for charts + stats
    history_qs = list(BoilerDailyKPI.objects.filter(
        date__gte=start_date, date__lte=end_date
    ).order_by('date'))

    # 4. Scorecard stats
    def _stats(qs, field, threshold):
        vals = [getattr(r, field) for r in qs if getattr(r, field) is not None]
        if not vals:
            return {'avg': None, 'max': None, 'min': None, 'days_ok': 0, 'days_total': 0}
        days_ok = sum(1 for v in vals if v <= threshold)
        return {
            'avg': round(sum(vals) / len(vals), 3),
            'max': round(max(vals), 3),
            'min': round(min(vals), 3),
            'days_ok': days_ok,
            'days_total': len(vals),
        }

    scorecard = {
        'downtime_a':   _stats(history_qs, 'downtime_a', 1.01),
        'downtime_b':   _stats(history_qs, 'downtime_b', 1.01),
        'downtime_melt':_stats(history_qs, 'downtime_sugar_melt', 0.70),
        'reduced_a':    _stats(history_qs, 'reduced_cap_a', 1.02),
        'reduced_b':    _stats(history_qs, 'reduced_cap_b', 1.02),
    }

    # 5. Trend: compare avg of current vs previous period
    period_days = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_days - 1)
    prev_qs = list(BoilerDailyKPI.objects.filter(date__gte=prev_start, date__lte=prev_end))

    def _avg(qs, field):
        vals = [getattr(r, field) for r in qs if getattr(r, field) is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    kpi_fields = ['downtime_a', 'downtime_b', 'downtime_sugar_melt', 'reduced_cap_a', 'reduced_cap_b']
    trend = {}
    for f in kpi_fields:
        curr = _avg(history_qs, f)
        prev = _avg(prev_qs, f)
        if curr is not None and prev is not None:
            delta = round(curr - prev, 3)
            trend[f] = {'delta': abs(delta), 'direction': 'up' if delta > 0 else ('down' if delta < 0 else 'flat')}
        else:
            trend[f] = {'delta': None, 'direction': 'flat'}

    # 6. Alert history: records that exceeded threshold
    thresholds = {
        'downtime_a': (1.01, 'Downtime A'),
        'downtime_b': (1.01, 'Downtime B'),
        'downtime_sugar_melt': (0.70, 'Downtime ละลาย'),
        'reduced_cap_a': (1.02, 'ลดกำลัง A'),
        'reduced_cap_b': (1.02, 'ลดกำลัง B'),
    }
    alert_records = []
    for rec in history_qs:
        for field, (threshold, label) in thresholds.items():
            val = getattr(rec, field)
            if val is not None and val > threshold:
                alert_records.append({
                    'date': rec.date.strftime('%d/%m/%Y'),
                    'kpi': label,
                    'value': round(val, 3),
                    'target': threshold,
                    'excess': round(val - threshold, 3),
                })
    alert_records.sort(key=lambda x: x['date'], reverse=True)

    # 7. Chart arrays
    dates  = [r.date.strftime('%d/%m') for r in history_qs]
    press_20 = [r.pressure_20bar or 0 for r in history_qs]
    flow_20  = [r.flow_20bar or 0 for r in history_qs]
    press_40 = [r.pressure_40bar or 0 for r in history_qs]
    flow_40  = [r.flow_40bar or 0 for r in history_qs]

    context = {
        'latest_kpi': latest_kpi,
        'scorecard': scorecard,
        'trend': trend,
        'alert_records': alert_records,
        'selected_days': days_param,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'is_custom': is_custom,
        'chart_dates':    json.dumps(dates, cls=DjangoJSONEncoder),
        'chart_press_20': json.dumps(press_20, cls=DjangoJSONEncoder),
        'chart_flow_20':  json.dumps(flow_20, cls=DjangoJSONEncoder),
        'chart_press_40': json.dumps(press_40, cls=DjangoJSONEncoder),
        'chart_flow_40':  json.dumps(flow_40, cls=DjangoJSONEncoder),
    }
    return render(request, 'myapp/boiler.html', context)


@login_required
def boiler_export_csv(request):
    import csv
    from datetime import date as date_cls
    from django.http import HttpResponse

    days_param = request.GET.get('days', '7')
    start_str = request.GET.get('start', '')
    end_str = request.GET.get('end', '')
    today = date_cls.today()

    if start_str and end_str:
        try:
            start_date = date_cls.fromisoformat(start_str)
            end_date = date_cls.fromisoformat(end_str)
        except ValueError:
            start_date = today - timedelta(days=6)
            end_date = today
    else:
        try:
            days = int(days_param)
        except ValueError:
            days = 7
        end_date = today
        start_date = today - timedelta(days=days - 1)

    qs = BoilerDailyKPI.objects.filter(date__gte=start_date, date__lte=end_date).order_by('date')
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="boiler_kpi_{start_date}_{end_date}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Downtime A%', 'Downtime B%', 'Downtime Melt%',
                     'Reduced Cap A%', 'Reduced Cap B%',
                     'Pressure 20bar', 'Flow 20bar', 'Pressure 40bar', 'Flow 40bar',
                     'Shredder (T/Day)'])
    for r in qs:
        writer.writerow([r.date, r.downtime_a, r.downtime_b, r.downtime_sugar_melt,
                         r.reduced_cap_a, r.reduced_cap_b,
                         r.pressure_20bar, r.flow_20bar, r.pressure_40bar, r.flow_40bar,
                         r.shredder_consumption])
    return response

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


def _auto_link_equipment(log):
    if log.equipment_fk_id:
        return
    key = (log.machine or '').strip().lower()
    if not key:
        return
    eq = (Equipment.objects.filter(equipment_id__iexact=key).first() or
          Equipment.objects.filter(name__iexact=key).first() or
          Equipment.objects.filter(name__icontains=key).first())
    if eq:
        log.equipment_fk = eq


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
            'downtimeDissolve': log.downtime_dissolve or 0,
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
    equipment_choices = Equipment.objects.filter(is_active=True).order_by('equipment_id')
    prefill_eq = request.GET.get('equipment', '')
    if request.method == 'POST':
        form = MaintenanceLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            _auto_link_equipment(log)
            log.save()
            if log.equipment_fk:
                log.equipment_fk.update_reliability_metrics()
            return redirect('maintenance_dashboard')
    else:
        initial = {}
        if prefill_eq:
            eq = Equipment.objects.filter(equipment_id=prefill_eq).first()
            if eq:
                initial['machine'] = eq.name
        form = MaintenanceLogForm(initial=initial)
    return render(request, 'myapp/maintenance_log_form.html', {
        'form': form,
        'equipment_choices': equipment_choices,
    })

@login_required
def maintenance_log_edit(request, log_id):
    log = get_object_or_404(MaintenanceLog, id=log_id)
    equipment_choices = Equipment.objects.filter(is_active=True).order_by('equipment_id')
    if request.method == 'POST':
        form = MaintenanceLogForm(request.POST, instance=log)
        if form.is_valid():
            log = form.save(commit=False)
            _auto_link_equipment(log)
            log.save()
            if log.equipment_fk:
                log.equipment_fk.update_reliability_metrics()
            return redirect('maintenance_dashboard')
    else:
        form = MaintenanceLogForm(instance=log)
    return render(request, 'myapp/maintenance_log_form.html', {
        'form': form,
        'equipment_choices': equipment_choices,
        'is_edit': True,
        'log_id': log_id,
    })

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

@login_required
def maintenance_import_csv(request):
    if request.method == 'POST' and request.FILES.get('file'):
        csv_file = request.FILES['file']
        
        # ตรวจสอบนามสกุลไฟล์
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({'success': False, 'error': 'กรุณาอัปโหลดไฟล์นามสกุล .csv เท่านั้น'})
            
        try:
            # อ่านไฟล์และจัดการภาษาไทย (utf-8-sig เพื่อตัด BOM)
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            headers = reader.fieldnames
            if not headers:
                return JsonResponse({'success': False, 'error': 'ไฟล์ CSV ว่างเปล่าหรือไม่ถูกต้อง'})
                
            success_count = 0
            import_type = 'unknown'

            # -----------------------------------------------------
            # 1. ตรวจสอบว่าเป็นไฟล์ KPI
            # -----------------------------------------------------
            if 'name' in headers or 'หัวข้อ KPI' in headers or 'weight' in headers:
                import_type = 'kpi'
                for row in reader:
                    name_val = row.get('name') or row.get('หัวข้อ KPI')
                    if not name_val:
                        continue # ข้ามแถวที่ไม่มีชื่อ KPI
                        
                    def to_float(val):
                        try: return float(val) if val else 0.0
                        except ValueError: return 0.0
                        
                    def to_int(val):
                        try: return int(float(val)) if val else 0
                        except ValueError: return 0

                    KPIMetric.objects.create(
                        name=name_val.strip(),
                        category=row.get('category') or row.get('หมวดหมู่') or 'General',
                        target=to_float(row.get('target') or row.get('เป้าหมาย')),
                        unit=row.get('unit') or row.get('หน่วย') or '',
                        weight=to_float(row.get('weight') or row.get('น้ำหนัก')),
                        actual=to_float(row.get('actual') or row.get('ผลลัพธ์')),
                        score=to_int(row.get('score') or row.get('คะแนน'))
                    )
                    success_count += 1
            
            # -----------------------------------------------------
            # 2. กรณีที่เป็นไฟล์ งานซ่อมเครื่องจักร (Maintenance Log)
            # -----------------------------------------------------
            else:
                import_type = 'maintenance'
                for row in reader:
                    date_str = row.get('date') or row.get('วันที่')
                    machine_name = row.get('machine') or row.get('ชื่อเครื่องจักร')
                    
                    if not date_str or not machine_name:
                        continue # ข้ามแถวที่ข้อมูลหลักไม่ครบ
                        
                    try:
                        d, m, y = map(int, date_str.split('/'))
                        if y > 2400: y -= 543 # แปลง พ.ศ. เป็น ค.ศ.
                        parsed_date = datetime(y, m, d).date()
                    except Exception:
                        parsed_date = datetime.now().date()
                    
                    def to_float(val):
                        try: return float(val) if val else 0.0
                        except ValueError: return 0.0
                    
                    problem_text = row.get('problem') or row.get('ปัญหาที่เกิด') or '-'
                    cause_text = row.get('cause') or row.get('สาเหตุที่เกิด') or '-'
                    
                    is_leak_val = str(row.get('isLeak') or row.get('รั่วไหล') or '').lower()
                    is_leak = is_leak_val in ['true', '1', 'yes', 'ใช่'] or 'รั่ว' in problem_text or 'รั่ว' in cause_text

                    MaintenanceLog.objects.create(
                        date=parsed_date,
                        machine=machine_name.strip(),
                        dept=row.get('dept') or row.get('แผนก') or 'ไม่ระบุ',
                        problem=problem_text,
                        cause=cause_text,
                        solution=row.get('solution') or row.get('การแก้ไข') or '-',
                        downtime_stop=to_float(row.get('downtimeStop') or row.get('เสียเวลาหยุดหีบ')),
                        downtime_reduced=to_float(row.get('downtimeReduced') or row.get('ลดรอบ')),
                        downtime_non_stop=to_float(row.get('downtimeNonStop') or row.get('เสียเวลาไม่หยุดหีบ')),
                        category=row.get('category') or row.get('หัวข้อ') or 'อื่นๆ',
                        is_leak=is_leak,
                        spare_part=row.get('sparePart') or row.get('อะไหล่ที่เปลี่ยน') or '-',
                        qty=to_float(row.get('qty') or row.get('จำนวน')),
                        reporter=row.get('reporter') or row.get('ผู้แจ้ง') or '-',
                        resolver=row.get('resolver') or row.get('ผู้แก้ไข') or '-'
                    )
                    success_count += 1
                    
            return JsonResponse({'success': True, 'count': success_count, 'type': import_type})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'ไม่มีไฟล์ถูกส่งมา'})
    
@login_required
def mill(request):
    # (Same as provided logic)
    today = datetime.now().date()
    # Get latest report that actually has data (cane_weight is not null)
    latest_a = MillReport.objects.filter(line='A', cane_weight__isnull=False).order_by('-date', '-created_at').first()
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

    latest_b = MillReport.objects.filter(line='B', cane_weight__isnull=False).order_by('-date', '-created_at').first()
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

@login_required
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
            start_date = end_date - timedelta(days=29) # 30 days total (inclusive)
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

@login_required
def mill_report(request):
    if request.method == 'POST':
        form = MillReportForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
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
                    # Convert row to string, lowercase, and strip whitespace for flexible matching
                    row_values = [str(val).lower().strip() for val in row.values]
                    if any(x in ['date', 'วันที่', 'วัน/เดือน/ปี'] for x in row_values):
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
            date_col_name = next((col for col in df.columns if str(col).lower().strip() in ['date', 'วันที่', 'วัน/เดือน/ปี']), None)
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
                mill_obj, created = MillReport.objects.update_or_create(
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
                if created:
                    mill_obj.created_by = request.user
                    mill_obj.save(update_fields=['created_by'])
                else:
                    mill_obj.updated_by = request.user
                    mill_obj.save(update_fields=['updated_by'])
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



@login_required
def lathe_api(request):
    if request.method == 'GET':
        jobs = LatheJob.objects.all().values()
        jobs_list = list(jobs)
        # จัดการรูปแบบวันที่ให้ส่งเป็น JSON ได้
        for job in jobs_list:
            if job['date']: job['date'] = job['date'].strftime('%Y-%m-%d')
            if job['req_date']: job['req_date'] = job['req_date'].strftime('%Y-%m-%d')
            if job['plan_due_date']: job['plan_due_date'] = job['plan_due_date'].strftime('%Y-%m-%d')
        return JsonResponse(jobs_list, safe=False)
    
    elif request.method == 'POST':
        try:
            if request.content_type.startswith('multipart/form-data'):
                data_str = request.POST.get('data')
                data = json.loads(data_str) if data_str else {}
            else:
                data = json.loads(request.body)

            action = data.get('action')
            
            if action == 'save_job':
                job_data = data.get('job')
                job, created = LatheJob.objects.update_or_create(
                    job_no=job_data.get('job_no'),
                    defaults={
                        'date': job_data.get('date') or None,
                        'requester': job_data.get('requester'),
                        'dept': job_data.get('dept'),
                        'tel': job_data.get('tel'),
                        'machine': job_data.get('machine'),
                        'cust_machine': job_data.get('cust_machine'),
                        'topic': job_data.get('topic'),
                        'job_type': ','.join(job_data.get('job_type', [])),
                        'priority': job_data.get('priority'),
                        'req_date': job_data.get('req_date') or None,
                        'has_drawing': job_data.get('has_drawing', False),
                        'has_sample': job_data.get('has_sample', False),
                        'has_material': job_data.get('has_material', False),
                        'plan_status': job_data.get('plan_status'),
                        'plan_reject_reason': job_data.get('plan_reject_reason'),
                        'plan_due_date': job_data.get('plan_due_date') or None,
                        'maker': job_data.get('maker'),
                        'material_cost': float(job_data.get('material_cost', 0) or 0),
                        'hours': float(job_data.get('hours', 0) or 0),
                        'pieces': float(job_data.get('pieces', 1) or 1),
                        'qc_result': job_data.get('qc_result'),
                        'qc_note': job_data.get('qc_note'),
                        'receiver': job_data.get('receiver'),
                        'status': job_data.get('status', 'Pending'),
                        'attachment': job_data.get('attachment')
                    }
                )

                return JsonResponse({'status': 'success', 'job_no': job.job_no})
            
            elif action == 'update_status':
                job_no = data.get('job_no')
                new_status = data.get('status')
                LatheJob.objects.filter(job_no=job_no).update(status=new_status)
                return JsonResponse({'status': 'success'})

            elif action == 'sync_all':
                 jobs_data = data.get('jobs', [])
                 for job_data in jobs_data:
                     LatheJob.objects.update_or_create(
                        job_no=job_data.get('job_no'),
                        defaults={
                            'date': job_data.get('date') or None,
                            'topic': job_data.get('topic'),
                            'dept': job_data.get('dept'),
                            'machine': job_data.get('machine'),
                            'cust_machine': job_data.get('cust_machine'),
                            'maker': job_data.get('maker'),
                            'hours': float(job_data.get('hours', 0) or 0),
                            'pieces': float(job_data.get('pieces', 1) or 1),
                            'status': job_data.get('status', 'Pending'),
                            'material_cost': float(job_data.get('material_cost', 0) or 0),
                        }
                     )
                 return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'invalid method'}, status=405)


# ─── View 1: หน้ารายการ + Dashboard ─────────────────────────────────────────
@login_required
def doc_repository(request):
    from django.db.models import Sum, Count
    from datetime import date

    # ── Filters ──────────────────────────────────────────────
    dept_filter  = request.GET.get('dept', '')
    type_filter  = request.GET.get('type', '')
    year_filter  = request.GET.get('year', '')
    search_query = request.GET.get('q', '').strip()

    docs = RepairDocument.objects.select_related('equipment', 'uploaded_by').all()

    if dept_filter:
        docs = docs.filter(department=dept_filter)
    if type_filter:
        docs = docs.filter(doc_type=type_filter)
    if year_filter:
        docs = docs.filter(budget_year=year_filter)
    if search_query:
        docs = docs.filter(
            models.Q(title__icontains=search_query) |
            models.Q(equipment__equipment_id__icontains=search_query) |
            models.Q(po_number__icontains=search_query)
        )

    # ── KPIs ─────────────────────────────────────────────────
    today        = date.today()
    all_docs     = RepairDocument.objects.all()
    total_docs   = all_docs.count()
    monthly_docs = all_docs.filter(
        created_at__year=today.year, created_at__month=today.month
    ).count()
    total_budget = all_docs.aggregate(s=Sum('budget_amount'))['s'] or 0

    # นับแยกแผนก (สำหรับ filter badge)
    dept_counts = {}
    for dept, _ in RepairDocument.DEPT_CHOICES:
        dept_counts[dept] = all_docs.filter(department=dept).count()

    # ปีงบประมาณที่มีในระบบ (สำหรับ dropdown) — ต้องเป็น string เพื่อเทียบกับ year_filter ที่มาจาก GET
    budget_years = [
        str(y) for y in all_docs.values_list('budget_year', flat=True).distinct().order_by('-budget_year')
    ]

    context = {
        'docs':          docs,
        'equipments':    Equipment.objects.filter(is_active=True).order_by('equipment_id'),
        'form':          RepairDocumentForm(),
        # KPIs
        'total_docs':    total_docs,
        'monthly_docs':  monthly_docs,
        'total_budget':  total_budget,
        # Filter state
        'dept_filter':   dept_filter,
        'type_filter':   type_filter,
        'year_filter':   year_filter,
        'search_query':  search_query,
        'dept_counts':   dept_counts,
        'budget_years':  budget_years,
        # Dept choices for filter tabs
        'dept_choices':  RepairDocument.DEPT_CHOICES,
        'doc_count':     docs.count(),
    }
    return render(request, 'myapp/doc_repository.html', context)

# ─── Helper: อัปโหลดไฟล์ไป Google Drive ผ่าน Apps Script ────────────────────

def _upload_to_drive(uploaded_file, filename, folder_path):
    """
    อัปโหลดไฟล์ไป Google Drive ผ่าน Google Apps Script Web App
    ต้องตั้งค่า GAS_WEBAPP_URL ใน .env ก่อน
    คืนค่า file_id หากสำเร็จ หรือ None หากล้มเหลว
    """
    if not os.environ.get('GAS_WEBAPP_URL', ''):
        print('[Drive] GAS_WEBAPP_URL ยังไม่ได้ตั้งค่าใน .env')
        return None

    try:
        file_data = base64.b64encode(uploaded_file.read()).decode('utf-8')
        mime_type = getattr(uploaded_file, 'content_type', 'application/octet-stream')
        result = _send_to_gas({
            'action':     'upload',
            'filename':   filename,
            'mimeType':   mime_type,
            'fileData':   file_data,
            'folderPath': folder_path,
        }, timeout=90)

        if not result:
            print('[Drive] ไม่ได้รับ response จาก GAS')
            return None

        file_id = result.get('fileId') or result.get('id') or result.get('file_id')
        if file_id:
            print(f'[Drive] อัปโหลดสำเร็จ: {file_id}')
            return file_id
        print(f'[Drive] ตอบกลับไม่มี fileId: {result}')
        return None
    except Exception as e:
        print(f'[Drive Error] {type(e).__name__}: {e}')
        return None


# ─── Helper: ส่ง JSON ไป GAS (รองรับ redirect) ───────────────────────────────

def _send_to_gas(payload_dict, timeout=90):
    script_url = os.environ.get('GAS_WEBAPP_URL', '')
    if not script_url:
        return None
    import http.cookiejar
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    payload = json.dumps(payload_dict).encode('utf-8')
    req = urllib.request.Request(
        script_url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8')
        return json.loads(raw)
    except Exception as e:
        print(f'[GAS] {type(e).__name__}: {e}')
        return None


# ─── Helper: อัปโหลดไฟล์ใหญ่ผ่าน GAS chunk upload ───────────────────────────

CHUNK_SIZE_BYTES = 20 * 1024 * 1024   # 20 MB raw → ~26 MB base64 (ปลอดภัยใต้ขีด GAS 50 MB)

def _upload_to_drive_chunked(uploaded_file, filename, folder_path):
    """
    ใช้กับไฟล์ที่ใหญ่เกิน GAS single-upload limit (~35 MB)
    GAS จะสร้าง Drive resumable session แล้วรับ chunk ทีละก้อน
    """
    import uuid
    script_url = os.environ.get('GAS_WEBAPP_URL', '')
    if not script_url:
        print('[Drive Chunk] GAS_WEBAPP_URL ยังไม่ได้ตั้งค่าใน .env')
        return None

    upload_id = str(uuid.uuid4())
    file_size  = uploaded_file.size
    mime_type  = getattr(uploaded_file, 'content_type', 'application/octet-stream')

    try:
        # ① สร้าง resumable upload session ใน GAS
        init = _send_to_gas({
            'action':     'init',
            'uploadId':   upload_id,
            'filename':   filename,
            'mimeType':   mime_type,
            'folderPath': folder_path,
            'fileSize':   file_size,
        })
        if not init or init.get('status') != 'ok':
            print(f'[Drive Chunk] init ล้มเหลว: {init}')
            return None

        # ② ส่ง chunk ทีละก้อน
        chunk_start = 0
        while True:
            chunk_data = uploaded_file.read(CHUNK_SIZE_BYTES)
            if not chunk_data:
                break

            is_last = (chunk_start + len(chunk_data) >= file_size)
            result  = _send_to_gas({
                'action':     'chunk',
                'uploadId':   upload_id,
                'chunkStart': chunk_start,
                'chunkData':  base64.b64encode(chunk_data).decode('utf-8'),
                'fileSize':   file_size,
                'mimeType':   mime_type,
                'isLast':     is_last,
            }, timeout=120)

            if result is None:
                print(f'[Drive Chunk] ไม่ได้รับ response ที่ offset {chunk_start}')
                return None

            if result.get('status') == 'done':
                file_id = result.get('fileId')
                print(f'[Drive Chunk] อัปโหลดสำเร็จ: {file_id}')
                return file_id

            if result.get('error'):
                print(f'[Drive Chunk] error: {result["error"]}')
                return None

            chunk_start += len(chunk_data)

        print('[Drive Chunk] สิ้นสุด loop โดยไม่ได้รับ fileId')
        return None

    except Exception as e:
        print(f'[Drive Chunk Error] {type(e).__name__}: {e}')
        return None


# ─── View 2: รับฟอร์มลงทะเบียน + อัปโหลด Drive + แจ้ง LINE ─────────────────
MAX_UPLOAD_BYTES     = 100 * 1024 * 1024  # 100 MB
GAS_SIZE_LIMIT_BYTES =  35 * 1024 * 1024  # 35 MB — เกินนี้ใช้ chunk upload

@login_required
def doc_register(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    form = RepairDocumentForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'status': 'error', 'message': str(form.errors)}, status=400)

    doc = form.save(commit=False)
    doc.uploaded_by = request.user

    # ── ① อัปโหลดไฟล์ไป Google Drive ─────────────────────────
    uploaded_file = request.FILES.get('document_file')
    drive_success = False

    if uploaded_file:
        if uploaded_file.size > MAX_UPLOAD_BYTES:
            return JsonResponse({'status': 'error', 'message': f'ไฟล์ใหญ่เกิน 100 MB ({uploaded_file.size // (1024*1024)} MB)'}, status=400)

        eq_id       = doc.equipment.equipment_id if doc.equipment else 'UNASSIGNED'
        folder_path = f'LAMY/{doc.budget_year}/{eq_id}'

        if uploaded_file.size <= GAS_SIZE_LIMIT_BYTES:
            # ไฟล์ ≤ 35 MB → ใช้ GAS single upload (base64 JSON)
            file_id = _upload_to_drive(uploaded_file, uploaded_file.name, folder_path)
        else:
            # ไฟล์ > 35 MB → แบ่ง chunk ส่งผ่าน GAS resumable session
            print(f'[Drive] ไฟล์ {uploaded_file.size // (1024*1024)} MB เกิน GAS limit → ใช้ chunk upload')
            file_id = _upload_to_drive_chunked(uploaded_file, uploaded_file.name, folder_path)

        if file_id:
            doc.drive_file_id   = file_id
            doc.drive_file_name = uploaded_file.name
            drive_success       = True
        else:
            print(f'[Drive] upload ล้มเหลวสำหรับเอกสาร: {doc.title}')

    # ── ② บันทึกลงฐานข้อมูล ───────────────────────────────────
    doc.save()

    # ── ③ แจ้งเตือน LINE Notify ───────────────────────────────
    uploader_name = request.user.get_full_name() or request.user.username
    eq_display    = doc.equipment.equipment_id if doc.equipment else '—'
    drive_line    = f'\n📎 Drive: https://drive.google.com/file/d/{doc.drive_file_id}/view' if doc.drive_file_id else '\n📎 Drive: ยังไม่ได้อัปโหลด'

    line_message = (
        f'\n'
        f'📄 เอกสารใหม่ลงทะเบียนแล้ว\n'
        f'━━━━━━━━━━━━━━━━━━\n'
        f'📋 ชื่อ: {doc.title}\n'
        f'🔧 เครื่องจักร: {eq_display}\n'
        f'🏭 แผนก: {doc.department}\n'
        f'📝 ประเภท: {doc.get_doc_type_display()}\n'
        f'💰 PO: {doc.po_number or "—"}\n'
        f'👤 บันทึกโดย: {uploader_name}'
        f'{drive_line}'
    )
    _send_line_notify(line_message)

    # ── ④ ตอบกลับ ─────────────────────────────────────────────
    messages.success(request, f'ลงทะเบียนเอกสาร "{doc.title}" เรียบร้อยแล้ว')
    return JsonResponse({
        'status':       'success',
        'doc_id':       doc.id,
        'title':        doc.title,
        'drive_file_id': doc.drive_file_id or '',
        'drive_success': drive_success,
    })



# ─── View 3: ลบเอกสาร (optional) ────────────────────────────────────────────
@login_required
def doc_delete(request, doc_id):
    doc = RepairDocument.objects.filter(id=doc_id).first()
    if doc:
        title = doc.title
        doc.delete()
        messages.success(request, f'ลบเอกสาร "{title}" เรียบร้อยแล้ว')
    else:
        messages.error(request, 'ไม่พบเอกสารที่ระบุ')
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('doc_repository')

# ── LINE Bot helpers ──────────────────────────────────────────────────────────

# คำที่ใช้ปลุก bot
_LINE_TRIGGERS = {'lamy', 'LAMY', 'Lamy', 'รามี่'}
# timeout สถานะ "รอคำสั่ง" (วินาที)
_LINE_STATE_TTL = 300


def _reply_line(reply_token, text):
    """ตอบกลับข้อความผ่าน LINE Reply API (ใช้ replyToken จาก webhook event)"""
    token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
    if not token or not reply_token:
        return False
    try:
        payload = json.dumps({
            'replyToken': reply_token,
            'messages': [{'type': 'text', 'text': text}],
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://api.line.me/v2/bot/message/reply',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f'[LINE Bot] Reply OK: {resp.status}')
            return True
    except Exception as e:
        print(f'[LINE Bot Reply Error] {e}')
        return False


@csrf_exempt
def line_webhook(request):
    """
    Conversation flow:
      1. ผู้ใช้พิมพ์ trigger word (lamy / LAMY / Lamy / รามี่)
         → bot ตอบ "คะ เจ้านาย" และจำ state ไว้ 5 นาที
      2. ผู้ใช้พิมพ์ "ค้นหา <คำ>"
         → bot ค้นหาใน RepairDocument แล้วส่งผลลัพธ์พร้อมลิงก์
    """
    if request.method != 'POST':
        return HttpResponse('OK', status=200)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponse('OK', status=200)

    events = body.get('events', [])
    print(f'[LINE Webhook] รับ {len(events)} event(s)')

    for event in events:
        if event.get('type') != 'message':
            continue
        msg = event.get('message', {})
        if msg.get('type') != 'text':
            continue

        text        = msg.get('text', '').strip()
        reply_token = event.get('replyToken', '')
        source      = event.get('source', {})
        user_id     = source.get('userId', 'unknown')
        chat_id     = source.get('groupId', source.get('roomId', user_id))
        state_key   = f'line_awake_{chat_id}_{user_id}'

        print(f'[LINE Webhook] text="{text}" user={user_id[:8]}... chat={chat_id[:8]}...')

        # ── ขั้นที่ 1: ปลุก bot ──────────────────────────────────
        if text in _LINE_TRIGGERS:
            cache.set(state_key, True, _LINE_STATE_TTL)
            print(f'[LINE Webhook] Bot ตื่นแล้ว state_key={state_key}')
            _reply_line(
                reply_token,
                'คะ เจ้านาย 🙏 พร้อมค้นหาแล้วค่ะ\n'
                'พิมพ์ชื่อ / PO / รหัสเครื่องได้เลย\n'
                'เช่น: PO-001  หรือ  BL-JT-001',
            )
            continue

        # ── ขั้นที่ 2: รับคำสั่งค้นหา ──────────────────────────────
        # รองรับทั้งแบบ "ค้นหา xxx" และแบบพิมพ์ตรงๆ เมื่อ bot ตื่นอยู่
        is_awake = bool(cache.get(state_key))
        has_prefix = text.startswith('ค้นหา')

        if has_prefix and not is_awake:
            _reply_line(reply_token, 'พิมพ์ "lamy" ก่อนเพื่อปลุก bot แล้วค่อยค้นหาค่ะ 🙏')
            continue

        if is_awake or has_prefix:
            query = text[len('ค้นหา'):].strip() if has_prefix else text
            print(f'[LINE Webhook] ค้นหา: "{query}"')

            if not query:
                _reply_line(reply_token, 'กรุณาระบุสิ่งที่ต้องการค้นหาด้วยค่ะ\nเช่น: ค้นหา PO-001')
                continue

            docs_qs = RepairDocument.objects.filter(
                Q(po_number__icontains=query)  |
                Q(title__icontains=query)       |
                Q(equipment__equipment_id__icontains=query)
            ).select_related('equipment').order_by('-created_at')

            total = docs_qs.count()
            docs  = docs_qs[:5]

            if total == 0:
                _reply_line(reply_token, f'ไม่พบเอกสารที่ตรงกับ "{query}" ค่ะ')
                continue

            header = f'พบ {total} รายการสำหรับ "{query}"'
            if total > 5:
                header += ' (แสดง 5 รายการล่าสุด)'
            header += '\n' + '─' * 30

            blocks = [header]
            for doc in docs:
                eq   = doc.equipment.equipment_id if doc.equipment else '-'
                po   = doc.po_number or '-'
                link = doc.drive_url or '(ยังไม่มีลิงก์ Drive)'
                dept = doc.department or '-'
                blocks.append(
                    f'📄 {doc.title}\n'
                    f'   แผนก : {dept}\n'
                    f'   เครื่อง: {eq}  |  PO: {po}\n'
                    f'   {link}'
                )

            _reply_line(reply_token, '\n\n'.join(blocks))
            continue

    return HttpResponse('OK', status=200)


def _send_line_notify(message):
    """ส่งข้อความผ่าน LINE Messaging API (Push Message)"""
    token    = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
    group_id = os.environ.get('LINE_GROUP_ID', '')

    if not token or not group_id:
        print('[LINE Bot] LINE_CHANNEL_ACCESS_TOKEN หรือ LINE_GROUP_ID ยังไม่ได้ตั้งค่า')
        return False

    try:
        payload = json.dumps({
            'to': group_id,
            'messages': [{'type': 'text', 'text': message}]
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.line.me/v2/bot/message/push',
            data    = payload,
            headers = {
                'Content-Type':  'application/json',
                'Authorization': f'Bearer {token}',
            },
            method = 'POST',
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f'[LINE Bot] ส่งสำเร็จ: {resp.status}')
            return True
    except Exception as e:
        print(f'[LINE Bot Error] {e}')
        return False

# ---- helper: map choices -> dict สำหรับส่งสีไป template ----
CATEGORY_META = {
    'tools':       {'name': 'เครื่องมือช่าง',   'icon': '🔧', 'color': '#4f46e5'},
    'spares':      {'name': 'อะไหล่เครื่องจักร', 'icon': '⚙️', 'color': '#ea580c'},
    'consumables': {'name': 'วัสดุสิ้นเปลือง',   'icon': '📦', 'color': '#16a34a'},
    'lubricants':  {'name': 'น้ำมัน/สารเคมี',    'icon': '🛢️', 'color': '#b45309'},
    'steel':       {'name': 'เหล็กรูปพรรณ',     'icon': '🏗️', 'color': '#7c3aed'},
}
DEPARTMENT_META = {
    'mill_a':      {'name': 'ลูกหีบ A',        'color': '#2563eb'},
    'mill_b':      {'name': 'ลูกหีบ B',        'color': '#0284c7'},
    'boiler_20':   {'name': 'หม้อน้ำ 20 bar',  'color': '#ea580c'},
    'boiler_40':   {'name': 'หม้อน้ำ 40 bar',  'color': '#d97706'},
    'maintenance': {'name': 'ซ่อมบำรุงเครื่องกล', 'color': '#dc2626'},
    'lathe':       {'name': 'โรงกลึง',         'color': '#7c3aed'},
}


def _to_decimal(value, default='0'):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return Decimal(default)


# =====================================================================
# 1) DASHBOARD — ภาพรวม + KPI + Stock ต่ำ + TX ล่าสุด + สรุปแผนก
# =====================================================================
@login_required
def inventory_dashboard(request):
    # หมวด 'tools' แยกไปอยู่โมดูลเครื่องมือ (/tools/) แล้ว — ไม่นับรวมในภาพรวม Inventory ทั่วไป
    items = InventoryItem.objects.filter(is_active=True).exclude(category='tools')
    low_stock = items.filter(stock__lte=F('min_stock'))

    # สรุปแยกแผนก
    dept_stats = []
    for key, meta in DEPARTMENT_META.items():
        di = items.filter(department=key)
        issued = (InventoryTransaction.objects
                  .filter(department=key, tx_type='issue')
                  .aggregate(s=Sum('quantity'))['s'] or 0)
        dept_stats.append({
            'key': key, 'name': meta['name'], 'color': meta['color'],
            'total': di.count(),
            'low': di.filter(stock__lte=F('min_stock')).count(),
            'issued': issued,
            'value': sum(i.stock_value for i in di),
        })

    context = {
        'total_items':     items.count(),
        'low_stock_count': low_stock.count(),
        'tx_total':        InventoryTransaction.objects.count(),
        'total_value':     sum(i.stock_value for i in items),
        'low_stock_items': low_stock[:6],
        'recent_txs':      InventoryTransaction.objects.select_related('item')[:8],
        'dept_stats':      dept_stats,
        'category_meta':   CATEGORY_META,
        'department_meta': DEPARTMENT_META,
    }
    return render(request, 'myapp/inventory/dashboard.html', context)


# =====================================================================
# 2) LIST — ตารางรายการ + filter หมวด/แผนก/สถานะ/ค้นหา + เบิก-คืน/รับเข้า
#    (รวม inventory_checkout_page และ inventory_receive_page เดิมเข้าที่นี่)
#    หมวด 'tools' แยกไปอยู่โมดูลเครื่องมือ (/tools/) แล้ว — ไม่แสดงในลิสต์นี้
# =====================================================================
@login_required
def inventory_list(request):
    items = InventoryItem.objects.filter(is_active=True).exclude(category='tools')
    cat    = request.GET.get('cat', '')
    dept   = request.GET.get('dept', '')
    status = request.GET.get('status', '')
    q      = request.GET.get('q', '')

    if cat:
        items = items.filter(category=cat)
    if dept:
        items = items.filter(department=dept)
    if status == 'low':
        items = items.filter(stock__lte=F('min_stock'))
    elif status == 'out':
        items = items.filter(stock__lte=0)
    if q:
        items = items.filter(Q(name__icontains=q) | Q(code__icontains=q))

    context = {
        'items': items,
        'category_meta': CATEGORY_META,
        'department_meta': DEPARTMENT_META,
        'f_cat': cat, 'f_dept': dept, 'f_status': status, 'f_q': q,
        'category_choices': [c for c in InventoryItem.CATEGORY_CHOICES if c[0] != 'tools'],
        'department_choices': InventoryItem.DEPARTMENT_CHOICES,
        'equipment_choices': Equipment.objects.all().order_by('equipment_id'),
        'process_choices': list(ProcessCategory.objects.filter(is_active=True).order_by('name').values_list('name', flat=True)),
    }
    return render(request, 'myapp/inventory/list.html', context)


# =====================================================================
# 3) STOCK CARD — รายละเอียด 1 รายการ + ประวัติเคลื่อนไหว
# =====================================================================
@login_required
def inventory_stock_card(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    context = {
        'item': item,
        'transactions': item.transactions.select_related('maintenance_log', 'equipment')[:30],
        'category_meta': CATEGORY_META,
        'department_meta': DEPARTMENT_META,
        'category_choices': InventoryItem.CATEGORY_CHOICES,
        'department_choices': InventoryItem.DEPARTMENT_CHOICES,
        'equipment_choices': Equipment.objects.all().order_by('equipment_id'),
        'process_choices': list(ProcessCategory.objects.filter(is_active=True).order_by('name').values_list('name', flat=True)),
    }
    return render(request, 'myapp/inventory/stock_card.html', context)


# =====================================================================
# 4) DEPT SUMMARY + DETAIL — สรุปตามแผนก / drill-down
# =====================================================================
@login_required
def inventory_dept_summary(request):
    cards = []
    for key, meta in DEPARTMENT_META.items():
        di = InventoryItem.objects.filter(department=key, is_active=True)
        issued = (InventoryTransaction.objects
                  .filter(department=key, tx_type='issue')
                  .aggregate(s=Sum('quantity'))['s'] or 0)
        cards.append({
            'key': key, 'name': meta['name'], 'color': meta['color'],
            'total': di.count(),
            'low': di.exclude(category='tools').filter(stock__lte=F('min_stock')).count(),
            'issued': issued,
            'value': sum(i.stock_value for i in di),
        })
    return render(request, 'myapp/inventory/dept_summary.html',
                  {'cards': cards, 'category_meta': CATEGORY_META})


@login_required
def inventory_dept_detail(request, key):
    meta = DEPARTMENT_META.get(key)
    items = InventoryItem.objects.filter(department=key, is_active=True)
    txs = InventoryTransaction.objects.filter(department=key).select_related('item')
    context = {
        'dept_key': key, 'dept_meta': meta,
        'items': items,
        'recent_txs': txs[:8],
        'issued': txs.filter(tx_type='issue').aggregate(s=Sum('quantity'))['s'] or 0,
        'received': txs.filter(tx_type='receive').aggregate(s=Sum('quantity'))['s'] or 0,
        'low_count': items.exclude(category='tools').filter(stock__lte=F('min_stock')).count(),
        'total_value': sum(i.stock_value for i in items),
        'category_meta': CATEGORY_META,
    }
    return render(request, 'myapp/inventory/dept_detail.html', context)


# =====================================================================
# 5) TRANSACTIONS — ประวัติทั้งหมด + filter
# =====================================================================
@login_required
def inventory_tx_list(request):
    txs = InventoryTransaction.objects.select_related('item')
    t_type = request.GET.get('type', '')
    dept   = request.GET.get('dept', '')
    if t_type:
        txs = txs.filter(tx_type=t_type)
    if dept:
        txs = txs.filter(department=dept)
    context = {
        'transactions': txs,
        'category_meta': CATEGORY_META,
        'department_meta': DEPARTMENT_META,
        'f_type': t_type, 'f_dept': dept,
        'tx_types': InventoryTransaction.TX_TYPES,
        'department_choices': InventoryItem.DEPARTMENT_CHOICES,
    }
    return render(request, 'myapp/inventory/transactions.html', context)


# =====================================================================
# 6) API — เบิก-คืน / รับเข้า / เพิ่มรายการ  (เรียกด้วย fetch + CSRF)
#    คืน JSON ให้ JS อัปเดตหน้าได้แบบ real-time
# =====================================================================
@login_required
@require_POST
def api_inventory_checkout(request):
    """เบิกออก / คืน เครื่องมือช่าง"""
    data = json.loads(request.body or '{}')
    item = get_object_or_404(InventoryItem, pk=data.get('item_id'))
    tx_type = data.get('type', 'issue')      # 'issue' หรือ 'return'
    qty = _to_decimal(data.get('quantity', 1))

    if not data.get('employee'):
        return JsonResponse({'error': 'กรุณากรอกชื่อพนักงาน'}, status=400)
    if tx_type == 'issue' and item.stock < qty:
        return JsonResponse({'error': 'Stock ไม่เพียงพอ'}, status=400)
    if tx_type == 'return' and qty > item.outstanding_issued:
        return JsonResponse({'error': f'คืนได้ไม่เกินยอดที่เบิกไป ({item.outstanding_issued} {item.unit})'}, status=400)

    tx = InventoryTransaction.objects.create(
        item=item, tx_type=tx_type, quantity=qty,
        department=data.get('dept', item.department),
        work_group=data.get('work_group', ''),
        equipment_id=data.get('equipment_id') or None,
        employee_name=data.get('employee', ''),
        note=data.get('note', ''),
        # ถ้าส่ง maintenance_log_id มา จะ link เข้าใบแจ้งซ่อมให้อัตโนมัติ
        maintenance_log_id=data.get('maintenance_log_id') or None,
        created_by=request.user,
    )
    return JsonResponse({'success': True, 'new_stock': float(item.stock), 'tx_id': tx.id})


@login_required
@require_POST
def api_inventory_receive(request):
    """รับสินค้าเข้าคลัง (พร้อม PO)"""
    data = json.loads(request.body or '{}')
    item = get_object_or_404(InventoryItem, pk=data.get('item_id'))
    if not data.get('po_number'):
        return JsonResponse({'error': 'กรุณาระบุเลขที่ PO'}, status=400)

    InventoryTransaction.objects.create(
        item=item, tx_type='receive',
        quantity=_to_decimal(data.get('quantity', 1)),
        department=data.get('dept', item.department),
        work_group=data.get('work_group', ''),
        equipment_id=data.get('equipment_id') or None,
        employee_name=request.user.get_full_name() or request.user.username,
        po_number=data.get('po_number', ''),
        supplier=data.get('supplier', ''),
        created_by=request.user,
    )
    # อัปเดตราคา/หน่วยล่าสุดถ้าส่งมา
    price = data.get('unit_price')
    if price:
        item.unit_price = _to_decimal(price)
        item.save(update_fields=['unit_price'])
    return JsonResponse({'success': True, 'new_stock': float(item.stock)})


@login_required
@require_POST
def api_inventory_add_item(request):
    """เพิ่มรายการใหม่เข้าคลัง + เปิดยอดตั้งต้น (ถ้ามี)"""
    data = json.loads(request.body or '{}')
    if not data.get('code') or not data.get('name'):
        return JsonResponse({'error': 'กรุณากรอกรหัสและชื่อรายการ'}, status=400)
    if InventoryItem.objects.filter(code=data['code']).exists():
        return JsonResponse({'error': 'รหัสสินค้านี้มีอยู่แล้ว'}, status=400)

    item = InventoryItem.objects.create(
        code=data['code'], name=data['name'],
        category=data.get('category', 'consumables'),
        department=data.get('department', 'maintenance'),
        unit=data.get('unit', 'ชิ้น'),
        min_stock=_to_decimal(data.get('min_stock', 0)),
        max_stock=_to_decimal(data.get('max_stock', 0)),
        location=data.get('location', ''),
        unit_price=_to_decimal(data.get('unit_price', 0)),
    )
    initial = _to_decimal(data.get('initial_stock', 0))
    if initial > 0:
        InventoryTransaction.objects.create(
            item=item, tx_type='receive', quantity=initial,
            department=item.department,
            employee_name=request.user.get_full_name() or request.user.username,
            po_number='Initial Stock', note='เปิดบัญชีครั้งแรก',
            created_by=request.user,
        )
    return JsonResponse({'success': True, 'item_id': item.id})


@login_required
@require_POST
def api_inventory_update_item(request, pk):
    """แก้ไขข้อมูลรายการที่มีอยู่แล้ว (ไม่รวม stock — เปลี่ยนได้ผ่าน transaction เท่านั้น)"""
    item = get_object_or_404(InventoryItem, pk=pk)
    data = json.loads(request.body or '{}')
    code = data.get('code', '').strip()
    name = data.get('name', '').strip()
    if not code or not name:
        return JsonResponse({'error': 'กรุณากรอกรหัสและชื่อรายการ'}, status=400)
    if InventoryItem.objects.exclude(pk=item.pk).filter(code=code).exists():
        return JsonResponse({'error': 'รหัสสินค้านี้มีอยู่แล้ว'}, status=400)

    item.code = code
    item.name = name
    item.category = data.get('category', item.category)
    item.department = data.get('department', item.department)
    item.unit = data.get('unit', item.unit)
    item.min_stock = _to_decimal(data.get('min_stock', item.min_stock))
    item.max_stock = _to_decimal(data.get('max_stock', item.max_stock))
    item.location = data.get('location', item.location)
    item.unit_price = _to_decimal(data.get('unit_price', item.unit_price))
    item.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def api_inventory_delete_item(request, pk):
    """ปิดใช้งานรายการ (soft-delete) — คงประวัติ transaction ไว้เพราะ FK เป็น PROTECT"""
    item = get_object_or_404(InventoryItem, pk=pk)
    item.is_active = False
    item.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def upload_inventory_item_image(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    uploaded = request.FILES.get('image')
    if not uploaded:
        return JsonResponse({'error': 'ไม่มีรูปภาพถูกส่งมา'}, status=400)
    ext = os.path.splitext(uploaded.name)[1].lower()
    content_type = uploaded.content_type.split(';')[0].strip().lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS or content_type not in ALLOWED_IMAGE_MIMETYPES:
        return JsonResponse({'error': 'อนุญาตเฉพาะไฟล์รูปภาพ (jpg, png, gif, webp, bmp) เท่านั้น'}, status=400)
    item.image = uploaded
    item.save(update_fields=['image', 'updated_at'])
    return JsonResponse({'success': True, 'image_url': item.image.url})


# =====================================================================
# 9) TOOL READINESS CHECKLIST — log ความพร้อมเครื่องมือก่อนเบิก
# =====================================================================
@login_required
def inventory_readiness_list(request):
    checks = ToolReadinessCheck.objects.select_related('item', 'created_by')
    status  = request.GET.get('status', '')
    item_id = request.GET.get('item', '')

    if status:
        checks = checks.filter(overall_status=status)
    if item_id:
        checks = checks.filter(item_id=item_id)

    context = {
        'checks': checks,
        'tool_items': InventoryItem.objects.filter(category='tools', is_active=True),
        'f_status': status, 'f_item': item_id,
        'status_choices': ToolReadinessCheck.STATUS_CHOICES,
    }
    return render(request, 'myapp/inventory/readiness_list.html', context)


@login_required
def inventory_readiness_add(request):
    tool_items = InventoryItem.objects.filter(category='tools', is_active=True)

    if request.method == 'POST':
        item = get_object_or_404(InventoryItem, pk=request.POST.get('item'), category='tools')
        inspector = request.POST.get('inspector', '').strip()
        check_date = request.POST.get('check_date') or timezone.now().date()

        if not inspector:
            return render(request, 'myapp/inventory/readiness_form.html', {
                'tool_items': tool_items,
                'status_choices': ToolReadinessCheck.STATUS_CHOICES,
                'today': timezone.now().date(),
                'error': 'กรุณากรอกชื่อผู้ตรวจสอบ',
            })

        ToolReadinessCheck.objects.create(
            item=item,
            check_date=check_date,
            inspector=inspector,
            condition_ok='condition_ok' in request.POST,
            calibration_ok='calibration_ok' in request.POST,
            completeness_ok='completeness_ok' in request.POST,
            safety_ok='safety_ok' in request.POST,
            overall_status=request.POST.get('overall_status', 'ready'),
            note=request.POST.get('note', '').strip(),
            created_by=request.user,
        )
        return redirect('inventory_readiness_list')

    context = {
        'tool_items': tool_items,
        'status_choices': ToolReadinessCheck.STATUS_CHOICES,
        'today': timezone.now().date(),
    }
    return render(request, 'myapp/inventory/readiness_form.html', context)


# =====================================================================
# 10) TOOLS MODULE — เครื่องมือ แยกจาก Inventory ทั่วไป
#     - ติดตามรายชิ้น (ToolUnit) แก้ปัญหาเครื่องมือชนิดเดียวกันมีหลายชิ้น
#     - รวมหน้าตรวจสอบความพร้อม (ToolReadinessCheck) เข้ามาในโมดูลเดียวกัน
#     - เบิก/คืน (ToolCheckout) เตือนถ้าล่าสุด "ไม่พร้อมใช้งาน" แต่ไม่บล็อก
# =====================================================================
@login_required
def tools_dashboard(request):
    tool_items = InventoryItem.objects.filter(category='tools', is_active=True)
    units = ToolUnit.objects.filter(item__is_active=True)
    today = timezone.now().date()
    overdue_checkouts = (ToolCheckout.objects
                         .filter(return_date__isnull=True, due_date__lt=today)
                         .select_related('tool_unit', 'tool_unit__item')
                         .order_by('due_date'))
    context = {
        'type_count': tool_items.count(),
        'unit_count': units.count(),
        'available_count': units.filter(status='available').count(),
        'checked_out_count': units.filter(status='checked_out').count(),
        'maintenance_count': units.filter(status='maintenance').count(),
        'lost_count': units.filter(status='lost').count(),
        'overdue_checkouts': overdue_checkouts[:8],
        'overdue_count': overdue_checkouts.count(),
        'recent_checkouts': ToolCheckout.objects.select_related('tool_unit', 'tool_unit__item')[:8],
    }
    return render(request, 'myapp/tools/dashboard.html', context)


@login_required
def tools_type_list(request):
    q = request.GET.get('q', '')
    items = InventoryItem.objects.filter(category='tools', is_active=True)
    if q:
        items = items.filter(Q(name__icontains=q) | Q(code__icontains=q))

    type_rows = []
    for item in items:
        units = item.tool_units.all()
        type_rows.append({
            'item': item,
            'total': units.count(),
            'available': units.filter(status='available').count(),
            'checked_out': units.filter(status='checked_out').count(),
            'maintenance': units.filter(status='maintenance').count(),
            'lost': units.filter(status='lost').count(),
        })

    context = {
        'type_rows': type_rows,
        'f_q': q,
        'category_choices': InventoryItem.CATEGORY_CHOICES,
        'department_choices': InventoryItem.DEPARTMENT_CHOICES,
    }
    return render(request, 'myapp/tools/type_list.html', context)


@login_required
def tools_type_detail(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk, category='tools')
    units = item.tool_units.order_by('unit_code')

    unit_rows = []
    for u in units:
        latest = u.latest_readiness_check
        unit_rows.append({
            'unit': u,
            'latest_readiness': latest,
            'not_ready_alert': bool(latest and latest.overall_status == 'not_ready'),
            'active_checkout': u.checkouts.filter(return_date__isnull=True).first() if u.status == 'checked_out' else None,
        })

    context = {
        'item': item,
        'unit_rows': unit_rows,
        'status_choices': ToolUnit.STATUS_CHOICES,
        'department_choices': InventoryItem.DEPARTMENT_CHOICES,
    }
    return render(request, 'myapp/tools/type_detail.html', context)


@login_required
def tools_unit_detail(request, pk):
    unit = get_object_or_404(ToolUnit, pk=pk)
    context = {
        'unit': unit,
        'checkouts': unit.checkouts.all()[:30],
        'readiness_checks': unit.readiness_checks.all()[:30],
        'active_checkout': unit.checkouts.filter(return_date__isnull=True).first(),
        'status_choices': ToolUnit.STATUS_CHOICES,
        'department_choices': InventoryItem.DEPARTMENT_CHOICES,
    }
    return render(request, 'myapp/tools/unit_detail.html', context)


@login_required
def tools_overdue_list(request):
    today = timezone.now().date()
    checkouts = (ToolCheckout.objects
                 .filter(return_date__isnull=True, due_date__lt=today)
                 .select_related('tool_unit', 'tool_unit__item')
                 .order_by('due_date'))
    context = {'checkouts': checkouts, 'today': today}
    return render(request, 'myapp/tools/overdue_list.html', context)


@login_required
def tools_readiness_add(request):
    tool_units = ToolUnit.objects.select_related('item').exclude(status='retired').order_by('item__code', 'unit_code')
    preselect_unit = request.GET.get('unit')

    if request.method == 'POST':
        unit = get_object_or_404(ToolUnit, pk=request.POST.get('tool_unit'))
        inspector = request.POST.get('inspector', '').strip()
        check_date = request.POST.get('check_date') or timezone.now().date()

        if not inspector:
            return render(request, 'myapp/tools/readiness_form.html', {
                'tool_units': tool_units,
                'status_choices': ToolReadinessCheck.STATUS_CHOICES,
                'today': timezone.now().date(),
                'error': 'กรุณากรอกชื่อผู้ตรวจสอบ',
            })

        ToolReadinessCheck.objects.create(
            item=unit.item,
            tool_unit=unit,
            check_date=check_date,
            inspector=inspector,
            condition_ok='condition_ok' in request.POST,
            calibration_ok='calibration_ok' in request.POST,
            completeness_ok='completeness_ok' in request.POST,
            safety_ok='safety_ok' in request.POST,
            overall_status=request.POST.get('overall_status', 'ready'),
            note=request.POST.get('note', '').strip(),
            created_by=request.user,
        )
        return redirect('tools_unit_detail', pk=unit.pk)

    context = {
        'tool_units': tool_units,
        'status_choices': ToolReadinessCheck.STATUS_CHOICES,
        'today': timezone.now().date(),
        'preselect_unit': preselect_unit,
    }
    return render(request, 'myapp/tools/readiness_form.html', context)


@login_required
@require_POST
def api_tools_checkout(request):
    """เบิกเครื่องมือรายชิ้น — เตือนถ้าผลตรวจสอบความพร้อมล่าสุดคือ 'ไม่พร้อมใช้งาน' แต่ไม่บล็อก"""
    data = json.loads(request.body or '{}')
    unit = get_object_or_404(ToolUnit, pk=data.get('tool_unit_id'))
    borrower = (data.get('borrower') or '').strip()

    if not borrower:
        return JsonResponse({'error': 'กรุณากรอกชื่อผู้เบิก'}, status=400)
    if unit.status != 'available':
        return JsonResponse({'error': f'หน่วยนี้ไม่พร้อมเบิก (สถานะปัจจุบัน: {unit.get_status_display()})'}, status=400)

    checkout = ToolCheckout.objects.create(
        tool_unit=unit,
        borrower_name=borrower,
        department=data.get('department') or unit.item.department,
        checkout_date=data.get('checkout_date') or timezone.now().date(),
        due_date=data.get('due_date') or None,
        note=data.get('note', ''),
        created_by=request.user,
    )
    unit.status = 'checked_out'
    unit.save(update_fields=['status', 'updated_at'])

    InventoryTransaction.objects.create(
        item=unit.item, tool_unit=unit, tx_type='issue', quantity=Decimal('1'),
        department=checkout.department or unit.item.department,
        employee_name=borrower, note=data.get('note', ''),
        created_by=request.user,
    )

    warning = None
    latest = unit.latest_readiness_check
    if latest and latest.overall_status == 'not_ready':
        warning = f'คำเตือน: ผลตรวจสอบความพร้อมล่าสุด ({latest.check_date}) ระบุว่า "ไม่พร้อมใช้งาน" — ระบบยังบันทึกการเบิกให้ตามที่ร้องขอ'

    return JsonResponse({'success': True, 'checkout_id': checkout.id, 'warning': warning})


@login_required
@require_POST
def api_tools_return(request):
    """คืนเครื่องมือรายชิ้น — ปิด ToolCheckout ที่ค้างอยู่ล่าสุดของหน่วยนั้น"""
    data = json.loads(request.body or '{}')
    unit = get_object_or_404(ToolUnit, pk=data.get('tool_unit_id'))
    checkout = unit.checkouts.filter(return_date__isnull=True).order_by('-checkout_date').first()

    if not checkout:
        return JsonResponse({'error': 'หน่วยนี้ไม่มีรายการเบิกที่ค้างคืนอยู่'}, status=400)

    checkout.return_date = data.get('return_date') or timezone.now().date()
    note = data.get('note', '').strip()
    if note:
        checkout.note = (checkout.note + '\n' if checkout.note else '') + note
    checkout.save(update_fields=['return_date', 'note'])

    unit.status = 'available'
    unit.save(update_fields=['status', 'updated_at'])

    InventoryTransaction.objects.create(
        item=unit.item, tool_unit=unit, tx_type='return', quantity=Decimal('1'),
        department=checkout.department or unit.item.department,
        employee_name=checkout.borrower_name, note=note,
        created_by=request.user,
    )
    return JsonResponse({'success': True})


@login_required
@require_POST
def api_tools_type_add(request):
    """เพิ่มชนิดเครื่องมือใหม่ (InventoryItem หมวด 'tools') จากโมดูลเครื่องมือโดยตรง"""
    data = json.loads(request.body or '{}')
    if not data.get('code') or not data.get('name'):
        return JsonResponse({'error': 'กรุณากรอกรหัสและชื่อเครื่องมือ'}, status=400)
    if InventoryItem.objects.filter(code=data['code']).exists():
        return JsonResponse({'error': 'รหัสนี้มีอยู่แล้ว'}, status=400)

    item = InventoryItem.objects.create(
        code=data['code'], name=data['name'], category='tools',
        department=data.get('department', 'maintenance'),
        unit=data.get('unit', 'ชิ้น'),
        location=data.get('location', ''),
    )
    return JsonResponse({'success': True, 'item_id': item.id})


@login_required
@require_POST
def api_tools_unit_add(request):
    """เพิ่มหน่วยเครื่องมือใหม่ (รายชิ้น) ให้กับชนิดเครื่องมือที่มีอยู่"""
    data = json.loads(request.body or '{}')
    item = get_object_or_404(InventoryItem, pk=data.get('item_id'), category='tools')
    unit_code = (data.get('unit_code') or '').strip()
    if not unit_code:
        seq = item.tool_units.count() + 1
        unit_code = f'{item.code}-{seq:03d}'
    if ToolUnit.objects.filter(unit_code=unit_code).exists():
        return JsonResponse({'error': 'รหัสหน่วยนี้มีอยู่แล้ว'}, status=400)

    unit = ToolUnit.objects.create(
        item=item, unit_code=unit_code,
        location=data.get('location', '') or item.location,
        condition_note=data.get('condition_note', ''),
    )
    return JsonResponse({'success': True, 'unit_id': unit.id, 'unit_code': unit.unit_code})


@login_required
@require_POST
def api_tools_unit_update(request, pk):
    """แก้ไขสถานะ/ตำแหน่ง/หมายเหตุของหน่วยเครื่องมือ (แจ้งซ่อม, สูญหาย, ปลดระวาง ฯลฯ)"""
    unit = get_object_or_404(ToolUnit, pk=pk)
    data = json.loads(request.body or '{}')

    status = data.get('status')
    if status:
        if unit.status == 'checked_out' and status != 'checked_out':
            return JsonResponse({'error': 'หน่วยนี้ถูกเบิกออกอยู่ กรุณาคืนก่อนเปลี่ยนสถานะ'}, status=400)
        if status == 'checked_out':
            return JsonResponse({'error': 'กรุณาใช้ปุ่มเบิกเพื่อเปลี่ยนเป็นสถานะนี้'}, status=400)
        unit.status = status
    if 'location' in data:
        unit.location = data['location']
    if 'condition_note' in data:
        unit.condition_note = data['condition_note']
    unit.save()
    return JsonResponse({'success': True})


# ==========================================
# Training / Knowledge Center Module Views
# ==========================================

EXAM_PASS_SCORE = 60

ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov'}
TRAINING_MATERIAL_MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB

TRAINING_TARGET_TOTAL = 122
TRAINING_TARGET_L1 = 85
TRAINING_TARGET_L2 = 24
TRAINING_TARGET_L3 = 12


def get_expiring_certs_count(days_ahead=30):
    """นับใบรับรองที่กำลังจะหมดอายุใน N วันข้างหน้า (ยังไม่หมดอายุตอนนี้)"""
    today = timezone.now().date()
    soon = today + timedelta(days=days_ahead)
    records = TrainingRecord.objects.filter(
        status='passed', course__expiry_months__isnull=False
    ).select_related('course')
    count = 0
    for r in records:
        expiry_date = _add_interval(r.date, r.course.expiry_months, 'month')
        if today <= expiry_date <= soon:
            count += 1
    return count


def training_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


@login_required
def training_employees(request):
    q = request.GET.get('q', '')
    department_filter = request.GET.get('department', '')
    group_filter = request.GET.get('group', '')
    status_filter = request.GET.get('status', 'active')

    employees = employee.objects.all()
    if q:
        employees = employees.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(employeeID__icontains=q))
    if department_filter:
        employees = employees.filter(department=department_filter)
    if group_filter:
        employees = employees.filter(group=group_filter)
    if status_filter == 'active':
        employees = employees.filter(is_active=True)
    elif status_filter == 'inactive':
        employees = employees.filter(is_active=False)

    context = {
        'employees': employees,
        'department_choices': DEPARTMENT_CHOICES,
        'group_choices': employee.objects.exclude(group='').order_by('group').values_list('group', flat=True).distinct(),
        'q': q,
        'department_filter': department_filter,
        'group_filter': group_filter,
        'status_filter': status_filter,
    }
    return render(request, 'myapp/training/employee_list.html', context)


@login_required
def training_employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('training_employees')
    else:
        form = EmployeeForm()
    return render(request, 'myapp/training/employee_form.html', {'form': form})


@login_required
def training_employee_edit(request, employee_id):
    emp = get_object_or_404(employee, id=employee_id)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=emp)
        if form.is_valid():
            form.save()
            return redirect('training_employees')
    else:
        form = EmployeeForm(instance=emp)
    return render(request, 'myapp/training/employee_form.html', {'form': form, 'employee_obj': emp})


@login_required
@require_POST
def training_employee_delete(request, employee_id):
    emp = get_object_or_404(employee, id=employee_id)
    emp.is_active = False
    emp.save(update_fields=['is_active'])
    return redirect('training_employees')


@login_required
@require_POST
def training_employee_reactivate(request, employee_id):
    emp = get_object_or_404(employee, id=employee_id)
    emp.is_active = True
    emp.save(update_fields=['is_active'])
    return redirect('training_employees')


@login_required
def training_overview(request):
    total_employees = employee.objects.filter(is_active=True).count()

    avg_level = EmployeeSkillLevel.objects.aggregate(a=Avg('level'))['a'] or 0

    total_records = TrainingRecord.objects.count()
    passed_records = TrainingRecord.objects.filter(status='passed').count()
    pass_rate = round(passed_records / total_records * 100, 1) if total_records else 0

    passed_qs = TrainingRecord.objects.filter(status='passed').select_related('course')
    total_hours = sum(float(r.course.duration_days) * 8 for r in passed_qs)
    avg_hours = round(total_hours / total_employees, 1) if total_employees else 0
    total_budget = sum(float(r.course.cost_per_person) for r in passed_qs)

    best_per_employee = EmployeeSkillLevel.objects.values('employee').annotate(max_level=Max('level'))
    evaluated_count = best_per_employee.count()
    l1_count = best_per_employee.filter(max_level__gte=1).count()
    l2_count = best_per_employee.filter(max_level__gte=2).count()
    l3_count = best_per_employee.filter(max_level__gte=3).count()

    def pct(value, target):
        return min(round(value / target * 100), 100) if target else 0

    context = {
        'total_employees': total_employees,
        'avg_level': round(avg_level, 2),
        'pass_rate': pass_rate,
        'avg_hours': avg_hours,
        'total_budget': total_budget,
        'l3_expert_count': l3_count,

        'target_total': TRAINING_TARGET_TOTAL,
        'target_l1': TRAINING_TARGET_L1,
        'target_l2': TRAINING_TARGET_L2,
        'target_l3': TRAINING_TARGET_L3,
        'evaluated_count': evaluated_count,
        'l1_count': l1_count,
        'l2_count': l2_count,
        'evaluated_pct': pct(evaluated_count, TRAINING_TARGET_TOTAL),
        'l1_pct': pct(l1_count, TRAINING_TARGET_L1),
        'l2_pct': pct(l2_count, TRAINING_TARGET_L2),
        'l3_pct': pct(l3_count, TRAINING_TARGET_L3),

        'expiring_soon_count': get_expiring_certs_count(),
    }
    return render(request, 'myapp/training/overview.html', context)


@login_required
def training_exam(request):
    course_filter = request.GET.get('course', '')

    scores_qs = TrainingExamScore.objects.select_related('employee').all()
    if course_filter:
        scores_qs = scores_qs.filter(course_id=course_filter)

    best_per_emp = {}
    for s in scores_qs:
        current = best_per_emp.get(s.employee_id)
        if current is None or s.score > current['score']:
            best_per_emp[s.employee_id] = {'employee': s.employee, 'score': s.score, 'exam_date': s.exam_date}

    ranking = sorted(best_per_emp.values(), key=lambda x: -x['score'])
    for i, row in enumerate(ranking):
        rank = i + 1
        row['rank'] = rank
        row['is_gold'] = rank == 1
        row['is_silver'] = rank == 2
        row['is_bronze'] = rank == 3
        row['passed'] = row['score'] >= EXAM_PASS_SCORE

    recent_course_attempts = TrainingCourseExamAttempt.objects.select_related('employee', 'course').order_by('-submitted_at')
    if course_filter:
        recent_course_attempts = recent_course_attempts.filter(course_id=course_filter)
    recent_course_attempts = recent_course_attempts[:20]

    context = {
        'ranking': ranking,
        'exam_pass_score': EXAM_PASS_SCORE,
        'recent_course_attempts': recent_course_attempts,
        'courses': TrainingCourse.objects.filter(is_active=True).order_by('name'),
        'course_filter': course_filter,
    }
    return render(request, 'myapp/training/exam.html', context)


@login_required
@require_POST
def training_exam_delete(request, score_id):
    score = get_object_or_404(TrainingExamScore, id=score_id)
    score.delete()
    return redirect('training_exam')


@login_required
def training_matrix(request):
    q = request.GET.get('q', '')
    department_filter = request.GET.get('department', '')
    group_filter = request.GET.get('group', '')

    employees = employee.objects.filter(is_active=True)
    if q:
        employees = employees.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(employeeID__icontains=q))
    if department_filter:
        employees = employees.filter(department=department_filter)
    if group_filter:
        employees = employees.filter(group=group_filter)

    skills = TrainingSkill.objects.all().order_by('display_order')
    level_map = {(l.employee_id, l.skill_id): l.level for l in EmployeeSkillLevel.objects.all()}

    rows = []
    for emp in employees:
        cells = [{'skill_id': sk.id, 'level': level_map.get((emp.id, sk.id), 0)} for sk in skills]
        rows.append({'employee': emp, 'cells': cells})

    context = {
        'skills': skills,
        'rows': rows,
        'department_choices': DEPARTMENT_CHOICES,
        'group_choices': employee.objects.exclude(group='').order_by('group').values_list('group', flat=True).distinct(),
        'q': q,
        'department_filter': department_filter,
        'group_filter': group_filter,
    }
    return render(request, 'myapp/training/matrix.html', context)


@login_required
def training_progress(request):
    employee_filter = request.GET.get('employee', '')
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')

    records = TrainingRecord.objects.select_related('employee', 'course').all()
    if employee_filter:
        records = records.filter(employee_id=employee_filter)
    if status_filter:
        records = records.filter(status=status_filter)
    if type_filter:
        records = records.filter(training_type=type_filter)

    attempts_by_record_id = {
        a.training_record_id: a
        for a in TrainingCourseExamAttempt.objects.filter(training_record__in=records)
    }
    rows = [{'record': r, 'exam_attempt': attempts_by_record_id.get(r.id)} for r in records]

    context = {
        'rows': rows,
        'employees': employee.objects.filter(is_active=True),
        'status_choices': TrainingRecord.STATUS_CHOICES,
        'type_choices': TrainingRecord.TYPE_CHOICES,
        'employee_filter': employee_filter,
        'status_filter': status_filter,
        'type_filter': type_filter,
    }
    return render(request, 'myapp/training/progress.html', context)


@login_required
def training_record_add(request):
    if request.method == 'POST':
        form = TrainingRecordForm(request.POST)
        if form.is_valid():
            record = form.save()
            if record.status == 'passed':
                _bump_skill_level_on_pass(record.employee, record.course)
            return redirect('training_progress')
    else:
        form = TrainingRecordForm()
    return render(request, 'myapp/training/record_form.html', {'form': form})


@login_required
@require_POST
def training_record_delete(request, record_id):
    record = get_object_or_404(TrainingRecord, id=record_id)
    record.delete()
    return redirect('training_progress')


@login_required
@require_POST
def training_record_approve(request, record_id):
    record = get_object_or_404(TrainingRecord, id=record_id)
    was_passed = record.status == 'passed'
    record.status = 'passed'
    record.approved_by = request.user
    record.save()
    if not was_passed:
        _bump_skill_level_on_pass(record.employee, record.course)
    return redirect('training_progress')


@login_required
def training_courses(request):
    q = request.GET.get('q', '').strip()
    courses = TrainingCourse.objects.select_related('skill').prefetch_related('materials', 'quiz_questions').all()
    if q:
        courses = courses.filter(name__icontains=q)
    context = {'courses': courses, 'search_query': q}
    return render(request, 'myapp/training/courses.html', context)


@login_required
@training_admin_required
def training_course_add(request):
    if request.method == 'POST':
        form = TrainingCourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            return redirect('training_course_edit', course_id=course.id)
    else:
        form = TrainingCourseForm()
    return render(request, 'myapp/training/course_form.html', {'form': form})


@login_required
@training_admin_required
@require_POST
def training_course_delete(request, course_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    course.delete()
    return redirect('training_courses')


def _bump_skill_level_on_pass(emp, course):
    if not course.skill_id:
        return
    level_obj, created = EmployeeSkillLevel.objects.get_or_create(
        employee=emp, skill=course.skill, defaults={'level': 1})
    if not created and level_obj.level < 3:
        level_obj.level += 1
        level_obj.save(update_fields=['level'])


def _build_profile_context(emp):
    skill_levels = EmployeeSkillLevel.objects.filter(employee=emp).select_related('skill').order_by('skill__display_order')
    skill_rows = [{'skill': sl.skill, 'level': sl.level, 'pct': round(sl.level / 3 * 100)} for sl in skill_levels]

    today = timezone.now().date()
    records = TrainingRecord.objects.filter(employee=emp).select_related('course').order_by('-date')
    record_rows = []
    for r in records:
        is_expired = False
        is_expiring_soon = False
        if r.status == 'passed' and r.course.expiry_months:
            expiry_date = _add_interval(r.date, r.course.expiry_months, 'month')
            is_expired = expiry_date < today
            is_expiring_soon = not is_expired and (expiry_date - today).days <= 30
        record_rows.append({'record': r, 'is_expired': is_expired, 'is_expiring_soon': is_expiring_soon})

    exam_scores = TrainingExamScore.objects.filter(employee=emp).order_by('-exam_date')
    best_exam_score = exam_scores.aggregate(m=Max('score'))['m']

    course_exam_attempts = TrainingCourseExamAttempt.objects.filter(employee=emp).select_related('course').order_by('-submitted_at')

    return {
        'employee': emp,
        'skill_rows': skill_rows,
        'record_rows': record_rows,
        'exam_scores': exam_scores,
        'best_exam_score': best_exam_score,
        'course_exam_attempts': course_exam_attempts,
    }


@login_required
def training_profile(request, employee_id):
    emp = get_object_or_404(employee, id=employee_id)
    context = _build_profile_context(emp)
    return render(request, 'myapp/training/profile.html', context)


@login_required
def training_profile_print(request, employee_id):
    emp = get_object_or_404(employee, id=employee_id)
    context = _build_profile_context(emp)
    return render(request, 'myapp/training/profile_print.html', context)


@login_required
def training_certificate(request, record_id):
    record = get_object_or_404(TrainingRecord.objects.select_related('employee', 'course'), id=record_id)
    if record.status != 'passed':
        raise Http404('ยังไม่ผ่านการฝึกอบรม ไม่สามารถออกใบรับรองได้')
    context = {'record': record}
    return render(request, 'myapp/training/certificate.html', context)


def _career_step_sections(step):
    fields = [
        ('ตำแหน่งหน้าที่', step.position_duty),
        ('ขอบเขตหน้าที่', step.scope),
        ('ผลประโยชน์ที่ได้รับ', step.benefits),
        ('หมายเหตุ/อื่นๆ', step.notes),
    ]
    return [{'label': label, 'content': content} for label, content in fields if content]


@login_required
def training_career(request, employee_id=None):
    emp = None
    steps_qs = CareerLadderStep.objects.all()
    step_names = list(steps_qs.values_list('name', flat=True))
    current_step_index = None
    if employee_id:
        emp = get_object_or_404(employee, id=employee_id)
        if emp.group in step_names:
            current_step_index = step_names.index(emp.group)

    steps = [{'id': s.id, 'index': i, 'name': s.name, 'is_current': i == current_step_index, 'sections': _career_step_sections(s)}
             for i, s in enumerate(steps_qs)]

    context = {
        'employee': emp,
        'steps': steps,
        'employees': employee.objects.filter(is_active=True),
    }
    return render(request, 'myapp/training/career.html', context)


@login_required
def training_career_step_add(request):
    if request.method == 'POST':
        form = CareerLadderStepForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('training_career')
    else:
        form = CareerLadderStepForm()
    return render(request, 'myapp/training/career_step_form.html', {'form': form})


@login_required
def training_career_step_edit(request, step_id):
    step = get_object_or_404(CareerLadderStep, id=step_id)
    if request.method == 'POST':
        form = CareerLadderStepForm(request.POST, instance=step)
        if form.is_valid():
            form.save()
            return redirect('training_career')
    else:
        form = CareerLadderStepForm(instance=step)
    return render(request, 'myapp/training/career_step_form.html', {'form': form, 'step': step})


@login_required
@require_POST
def training_career_step_delete(request, step_id):
    step = get_object_or_404(CareerLadderStep, id=step_id)
    step.delete()
    return redirect('training_career')


@login_required
def training_gap(request):
    skills = TrainingSkill.objects.all().order_by('display_order')
    total_employees = employee.objects.filter(is_active=True).count()

    gap_rows = []
    for sk in skills:
        counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for row in EmployeeSkillLevel.objects.filter(skill=sk, employee__is_active=True).values('level').annotate(c=Count('id')):
            counts[row['level']] = row['c']

        evaluated = sum(counts.values())
        missing = total_employees - evaluated
        critical = counts[0] + missing
        warning = counts[1]
        good = counts[2] + counts[3]

        critical_ratio = critical / total_employees if total_employees else 0
        warning_ratio = warning / total_employees if total_employees else 0

        if critical_ratio > 0.3:
            severity = 'critical'
            recommendation = f'เร่งจัดอบรมพื้นฐานด้าน {sk.name} ด่วน (ยังไม่ผ่าน {critical} คน)'
        elif warning_ratio > 0.3:
            severity = 'warning'
            recommendation = f'วางแผนจัด Workshop เพิ่มเติมสำหรับทักษะ {sk.name}'
        else:
            severity = 'good'
            recommendation = f'ทักษะ {sk.name} อยู่ในเกณฑ์ดี ควรรักษาระดับต่อไป'

        gap_rows.append({
            'skill': sk, 'critical': critical, 'warning': warning, 'good': good,
            'severity': severity, 'recommendation': recommendation,
        })

    context = {'gap_rows': gap_rows, 'total_employees': total_employees}
    return render(request, 'myapp/training/gap.html', context)


# ----- คลังหลักสูตร: เอกสาร/วิดีโอการเรียน -----

@login_required
@training_admin_required
def training_course_edit(request, course_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    if request.method == 'POST':
        form = TrainingCourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('training_course_edit', course_id=course.id)
    else:
        form = TrainingCourseForm(instance=course)

    materials = course.materials.all()
    context = {
        'course': course,
        'form': form,
        'documents': [m for m in materials if m.material_type == 'document'],
        'videos': [m for m in materials if m.material_type == 'video'],
        'question_count': course.quiz_questions.filter(is_active=True).count(),
    }
    return render(request, 'myapp/training/course_edit.html', context)


@login_required
@training_admin_required
@require_POST
def training_course_material_upload(request, course_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    uploaded = request.FILES.get('file')
    material_type = request.POST.get('material_type')
    title = request.POST.get('title', '').strip()

    if not uploaded or material_type not in ('document', 'video'):
        return JsonResponse({'success': False, 'error': 'ข้อมูลไม่ครบถ้วน'})

    ext = os.path.splitext(uploaded.name)[1].lower()
    allowed = ALLOWED_VIDEO_EXTENSIONS if material_type == 'video' else ALLOWED_DOCUMENT_EXTENSIONS
    if ext not in allowed:
        return JsonResponse({'success': False, 'error': f'นามสกุลไฟล์ {ext} ไม่ได้รับอนุญาตสำหรับประเภทนี้'})

    if uploaded.size > TRAINING_MATERIAL_MAX_UPLOAD_BYTES:
        max_mb = TRAINING_MATERIAL_MAX_UPLOAD_BYTES // (1024 * 1024)
        return JsonResponse({'success': False, 'error': f'ไฟล์ใหญ่เกิน {max_mb} MB ({uploaded.size // (1024*1024)} MB)'})

    material = TrainingCourseMaterial.objects.create(
        course=course, material_type=material_type,
        title=title or uploaded.name,
        file=uploaded,
        display_order=course.materials.count(),
    )
    return JsonResponse({
        'success': True,
        'id': material.id,
        'title': material.title,
        'material_type': material.material_type,
        'file_url': material.file.url,
        'is_video': material.material_type == 'video',
    })


@login_required
@training_admin_required
@require_POST
def training_course_material_delete(request, material_id):
    material = get_object_or_404(TrainingCourseMaterial, id=material_id)
    course_id = material.course_id
    material.delete()
    return redirect('training_course_edit', course_id=course_id)


# ----- คลังหลักสูตร: คลังคำถามแบบทดสอบ -----

@login_required
@training_admin_required
def training_quiz_manage(request, course_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    questions = course.quiz_questions.prefetch_related('choices').all()
    context = {'course': course, 'questions': questions}
    return render(request, 'myapp/training/quiz_manage.html', context)


def _validate_correct_choice(formset, correct_index):
    """ตรวจสอบว่าเลือกคำตอบที่ถูกต้องไว้ 1 ข้อ และตัวเลือกนั้นมีข้อความจริง (ไม่ใช่แถวว่างที่ formset จะข้ามไป)"""
    if correct_index is None or not correct_index.isdigit():
        return False
    idx = int(correct_index)
    if idx >= len(formset.forms):
        return False
    return bool(formset.forms[idx].cleaned_data.get('choice_text', '').strip())


def _finalize_choices(formset, correct_index):
    """ตั้งค่า is_correct ตามข้อที่เลือก และเรียงลำดับ display_order ตามลำดับที่ส่งมา (เนื่องจากฟอร์มไม่ให้ผู้ใช้กรอกลำดับเอง)"""
    idx = int(correct_index)
    for i, cform in enumerate(formset.forms):
        if cform.cleaned_data.get('DELETE'):
            continue
        instance = cform.instance
        if instance.pk:
            is_correct = (i == idx)
            instance.is_correct = is_correct
            instance.display_order = i
            instance.save(update_fields=['is_correct', 'display_order'])


@login_required
@training_admin_required
def training_quiz_question_add(request, course_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    question = TrainingQuizQuestion(course=course)
    formset_error = None
    correct_choice_initial = None

    if request.method == 'POST':
        question_form = TrainingQuizQuestionForm(request.POST)
        formset = TrainingQuizChoiceFormSet(request.POST, instance=question)
        correct_index = request.POST.get('correct_choice')
        correct_choice_initial = int(correct_index) if correct_index and correct_index.isdigit() else None

        if question_form.is_valid() and formset.is_valid():
            if _validate_correct_choice(formset, correct_index):
                question = question_form.save(commit=False)
                question.course = course
                question.display_order = TrainingQuizQuestion.objects.filter(course=course).count()
                question.save()
                formset.instance = question
                formset.save()
                _finalize_choices(formset, correct_index)
                return redirect('training_quiz_manage', course_id=course.id)
            formset_error = 'กรุณาเลือกคำตอบที่ถูกต้อง 1 ข้อ (ตัวเลือกที่เลือกต้องมีข้อความคำตอบ)'
    else:
        question_form = TrainingQuizQuestionForm()
        formset = TrainingQuizChoiceFormSet(instance=question)

    context = {
        'course': course, 'question_form': question_form, 'formset': formset,
        'formset_error': formset_error, 'correct_choice_initial': correct_choice_initial,
    }
    return render(request, 'myapp/training/quiz_question_form.html', context)


@login_required
@training_admin_required
def training_quiz_question_edit(request, question_id):
    question = get_object_or_404(TrainingQuizQuestion, id=question_id)
    course = question.course
    formset_error = None
    correct_choice_initial = None

    if request.method == 'POST':
        question_form = TrainingQuizQuestionForm(request.POST, instance=question)
        formset = TrainingQuizChoiceFormSet(request.POST, instance=question)
        correct_index = request.POST.get('correct_choice')
        correct_choice_initial = int(correct_index) if correct_index and correct_index.isdigit() else None

        if question_form.is_valid() and formset.is_valid():
            if _validate_correct_choice(formset, correct_index):
                question_form.save()
                formset.save()
                _finalize_choices(formset, correct_index)
                return redirect('training_quiz_manage', course_id=course.id)
            formset_error = 'กรุณาเลือกคำตอบที่ถูกต้อง 1 ข้อ (ตัวเลือกที่เลือกต้องมีข้อความคำตอบ)'
    else:
        question_form = TrainingQuizQuestionForm(instance=question)
        formset = TrainingQuizChoiceFormSet(instance=question)
        existing_choices = list(question.choices.all())
        correct_choice_initial = next((i for i, c in enumerate(existing_choices) if c.is_correct), None)

    context = {
        'course': course, 'question': question, 'question_form': question_form, 'formset': formset,
        'formset_error': formset_error, 'correct_choice_initial': correct_choice_initial,
    }
    return render(request, 'myapp/training/quiz_question_form.html', context)


@login_required
@training_admin_required
@require_POST
def training_quiz_question_delete(request, question_id):
    question = get_object_or_404(TrainingQuizQuestion, id=question_id)
    course_id = question.course_id
    question.delete()
    return redirect('training_quiz_manage', course_id=course_id)


# ----- โหมด Kiosk: พนักงานดูสื่อการเรียนแล้วสอบทันที -----

EXAM_QUESTION_SAMPLE_SIZE = 10


def _grade_course_exam(questions, submitted_answers):
    """questions: list ของ TrainingQuizQuestion ที่สุ่มมาใช้ในการสอบครั้งนี้ (แต่ละคำถามมีคำตอบที่ถูกเพียง 1 ข้อ)
    submitted_answers: dict {question_id: selected_choice_id หรือ None}
    ถูก = 100% ของข้อนั้น, ผิด = 0%
    """
    total = len(questions)
    fully_correct = 0
    results = []
    for q in questions:
        correct_choice = next((c for c in q.choices.all() if c.is_correct), None)
        selected_id = submitted_answers.get(q.id)
        is_correct = bool(correct_choice and selected_id == correct_choice.id)
        if is_correct:
            fully_correct += 1
        results.append((q, selected_id, is_correct))
    overall_score = round(fully_correct / total * 100, 2) if total else 0
    return overall_score, fully_correct, total, results


@login_required
def training_learn(request, course_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    context = {
        'course': course,
        'employees': employee.objects.filter(is_active=True),
    }
    return render(request, 'myapp/training/learn_picker.html', context)


@login_required
def training_learn_detail(request, course_id, employee_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    emp = get_object_or_404(employee, id=employee_id)
    materials = course.materials.all()
    context = {
        'course': course,
        'employee': emp,
        'documents': [m for m in materials if m.material_type == 'document'],
        'videos': [m for m in materials if m.material_type == 'video'],
        'has_quiz': course.quiz_questions.filter(is_active=True).exists(),
    }
    return render(request, 'myapp/training/learn_detail.html', context)


@login_required
def training_exam_take(request, course_id, employee_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    emp = get_object_or_404(employee, id=employee_id)

    if request.method == 'POST':
        question_ids = [int(v) for v in request.POST.getlist('question_ids') if v.isdigit()]
        questions = list(
            course.quiz_questions.filter(is_active=True, id__in=question_ids).prefetch_related('choices')
        )

        submitted_answers = {}
        for q in questions:
            val = request.POST.get(f'q_{q.id}')
            submitted_answers[q.id] = int(val) if val and val.isdigit() else None

        overall_score, fully_correct, total, results = _grade_course_exam(questions, submitted_answers)

        today = timezone.now().date()
        attempt_no = TrainingCourseExamAttempt.objects.filter(employee=emp, course=course).count() + 1
        attempt = TrainingCourseExamAttempt.objects.create(
            employee=emp, course=course, attempt_no=attempt_no,
            total_questions=total, fully_correct_count=fully_correct, score=overall_score,
            passed=(overall_score >= EXAM_PASS_SCORE),
        )
        for q, selected_id, is_correct in results:
            answer = TrainingCourseExamAnswer.objects.create(
                attempt=attempt, question=q,
                question_score=(100 if is_correct else 0), is_fully_correct=is_correct,
            )
            if selected_id:
                answer.selected_choices.set([selected_id])

        existing_record = TrainingRecord.objects.filter(employee=emp, course=course, training_type='online').first()
        was_passed = existing_record.status == 'passed' if existing_record else False

        record, _ = TrainingRecord.objects.update_or_create(
            employee=emp, course=course, training_type='online',
            defaults={'date': today, 'score': overall_score,
                      'status': 'passed' if attempt.passed else 'failed'},
        )
        attempt.training_record = record
        attempt.save(update_fields=['training_record'])

        if not was_passed and record.status == 'passed':
            _bump_skill_level_on_pass(emp, course)

        return redirect('training_exam_result', course_id=course.id, employee_id=emp.id, attempt_id=attempt.id)

    all_active_questions = list(course.quiz_questions.filter(is_active=True).prefetch_related('choices'))
    sample_size = min(EXAM_QUESTION_SAMPLE_SIZE, len(all_active_questions))
    questions = random.sample(all_active_questions, sample_size) if sample_size else []

    context = {'course': course, 'employee': emp, 'questions': questions}
    return render(request, 'myapp/training/exam_take.html', context)


@login_required
def training_exam_result(request, course_id, employee_id, attempt_id):
    course = get_object_or_404(TrainingCourse, id=course_id)
    emp = get_object_or_404(employee, id=employee_id)
    attempt = get_object_or_404(TrainingCourseExamAttempt, id=attempt_id, course=course, employee=emp)
    context = {
        'course': course,
        'employee': emp,
        'attempt': attempt,
        'exam_pass_score': EXAM_PASS_SCORE,
    }
    return render(request, 'myapp/training/exam_result.html', context)


@login_required
def equipment_change_code(request, eq_id):
    equipment = get_object_or_404(Equipment, equipment_id=eq_id)

    if request.method == 'POST':
        new_id = (request.POST.get('new_equipment_id') or '').strip()

        if not new_id:
            messages.error(request, 'กรุณาระบุรหัสเครื่องจักรใหม่')
        elif new_id == eq_id:
            messages.error(request, 'รหัสใหม่ต้องไม่ซ้ำกับรหัสเดิม')
        elif Equipment.objects.filter(equipment_id=new_id).exists():
            messages.error(request, f'รหัสเครื่องจักร "{new_id}" ถูกใช้งานแล้ว')
        else:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('PRAGMA defer_foreign_keys = 1')

                Equipment.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                PMSchedule.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                EquipmentBOM.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                CBMVisualTest.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                CBMVibration.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                CBMThermoscan.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                CBMOilAnalysis.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                CBMAcoustic.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                PMPlan.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                WorkOrder.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                EquipmentLink.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                EquipmentLink.objects.filter(linked_equipment_id=eq_id).update(linked_equipment_id=new_id)
                MaintenanceLog.objects.filter(equipment_fk_id=eq_id).update(equipment_fk_id=new_id)
                RepairDocument.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)
                InventoryTransaction.objects.filter(equipment_id=eq_id).update(equipment_id=new_id)

            messages.success(request, f'เปลี่ยนรหัสเครื่องจักรจาก "{eq_id}" เป็น "{new_id}" เรียบร้อยแล้ว')
            return redirect('equipment_form_edit', eq_id=new_id)

    return render(request, 'myapp/equipment_change_code.html', {'equipment': equipment})


# ==========================================
# Manual Library Module (คู่มือปฏิบัติงานเครื่องจักร)
# ==========================================

MANUAL_FORMSET_CONFIG = [
    ('safety',         ManualSafetyItemFormSet),
    ('parts',          ManualPartItemFormSet),
    ('precheck',       ManualPrecheckItemFormSet),
    ('steps',          ManualOperatingStepFormSet),
    ('maint_daily',    ManualMaintenanceDailyItemFormSet),
    ('maint_periodic', ManualMaintenancePeriodicItemFormSet),
    ('troubleshoot',   ManualTroubleshootItemFormSet),
    ('specs',          ManualSpecItemFormSet),
]


@login_required
def manual_list(request):
    manuals = Manual.objects.all().order_by('-updated_at')
    return render(request, 'myapp/manual_list.html', {'manuals': manuals})


@login_required
def manual_add(request):
    manual = Manual()
    if request.method == 'POST':
        form = ManualForm(request.POST)
        formsets = {key: Cls(request.POST, prefix=key, instance=manual) for key, Cls in MANUAL_FORMSET_CONFIG}
        if form.is_valid() and all(fs.is_valid() for fs in formsets.values()):
            with transaction.atomic():
                manual = form.save(commit=False)
                manual.created_by = request.user
                manual.save()
                for fs in formsets.values():
                    fs.instance = manual
                    fs.save()
            messages.success(request, f'สร้างคู่มือ "{manual.machine_name}" เรียบร้อยแล้ว')
            return redirect('manual_detail', manual_id=manual.id)
    else:
        form = ManualForm()
        formsets = {key: Cls(prefix=key, instance=manual) for key, Cls in MANUAL_FORMSET_CONFIG}

    return render(request, 'myapp/manual_form.html', {
        'form': form, 'formsets': formsets, 'is_edit': False,
    })


@login_required
def manual_edit(request, manual_id):
    manual = get_object_or_404(Manual, id=manual_id)
    if request.method == 'POST':
        form = ManualForm(request.POST, instance=manual)
        formsets = {key: Cls(request.POST, prefix=key, instance=manual) for key, Cls in MANUAL_FORMSET_CONFIG}
        if form.is_valid() and all(fs.is_valid() for fs in formsets.values()):
            with transaction.atomic():
                manual = form.save()
                for fs in formsets.values():
                    fs.instance = manual
                    fs.save()
            messages.success(request, f'บันทึกคู่มือ "{manual.machine_name}" เรียบร้อยแล้ว')
            return redirect('manual_detail', manual_id=manual.id)
    else:
        form = ManualForm(instance=manual)
        formsets = {key: Cls(prefix=key, instance=manual) for key, Cls in MANUAL_FORMSET_CONFIG}

    return render(request, 'myapp/manual_form.html', {
        'form': form, 'formsets': formsets, 'is_edit': True, 'manual': manual,
    })


@login_required
def manual_detail(request, manual_id):
    manual = get_object_or_404(Manual, id=manual_id)
    return render(request, 'myapp/manual_detail.html', {'manual': manual})


@login_required
def manual_delete(request, manual_id):
    manual = get_object_or_404(Manual, id=manual_id)
    if request.method == 'POST':
        name = manual.machine_name
        manual.delete()
        messages.success(request, f'ลบคู่มือ "{name}" เรียบร้อยแล้ว')
    return redirect('manual_list')


# ===== Task Manager Module =====

MACHINE_TASK_VIBRATION_FIELDS = [
    ('amp', 'Amp'),
    ('de_ge', 'DE (gE)'),
    ('de_v', 'DE (V)'),
    ('de_h', 'DE (H)'),
    ('de_a', 'DE (A)'),
    ('de_m', 'DE (M)'),
    ('nde_ge', 'NDE (gE)'),
    ('nde_v', 'NDE (V)'),
    ('nde_h', 'NDE (H)'),
    ('nde_a', 'NDE (A)'),
    ('nde_m', 'NDE (M)'),
    ('temp_de', 'Temp.(DE)'),
    ('temp_frame', 'Temp.(FRAME)'),
    ('temp_nde', 'Temp.(NDE)'),
]


@login_required
def machine_task_list(request):
    tasks = MachineTask.objects.select_related('equipment').all()
    title_filter = request.GET.get('title') or ''
    status_filter = request.GET.get('status') or ''
    if title_filter:
        tasks = tasks.filter(title__icontains=title_filter)
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    tasks = list(tasks)

    active_names = list(
        ProcessCategory.objects.filter(is_active=True).order_by('name').values_list('name', flat=True)
    )
    active_set = set(active_names)

    equipment_rows = Equipment.objects.filter(is_active=True).order_by('equipment_id').values(
        'equipment_id', 'name', 'process', 'power_kw', 'rpm_input', 'rpm'
    )
    equipment_by_process = {}
    for row in equipment_rows:
        key = row['process'] if row['process'] in active_set else PROCESS_OTHER_BUCKET
        equipment_by_process.setdefault(key, []).append(row)

    for task in tasks:
        eq = task.equipment
        proc = eq.process if eq else None
        task.effective_process = proc if proc in active_set else PROCESS_OTHER_BUCKET
        scoped = list(equipment_by_process.get(task.effective_process, []))
        if eq and not any(r['equipment_id'] == eq.equipment_id for r in scoped):
            # เครื่องจักรปัจจุบันของ task ต้องเลือกได้เสมอ แม้ is_active=False หรือ process ไม่ตรง bucket
            scoped.insert(0, {
                'equipment_id': eq.equipment_id, 'name': eq.name,
                'power_kw': eq.power_kw, 'rpm_input': eq.rpm_input, 'rpm': eq.rpm,
            })
        task.scoped_equipment = scoped

    return render(request, 'myapp/machine_task_list.html', {
        'tasks': tasks,
        'form': MachineTaskForm(),
        'process_choices': active_names,
        'status_choices': MachineTask.STATUS_CHOICES,
        'title_filter': title_filter,
        'status_filter': status_filter,
        'title_history': MachineTask.objects.exclude(title='').values_list('title', flat=True).distinct().order_by('title'),
    })


@login_required
def machine_task_add(request):
    if request.method == 'POST':
        form = MachineTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.updated_by = request.user.username
            task.save()
            messages.success(request, f'เพิ่มงาน "{task.title}" เรียบร้อยแล้ว')
        else:
            messages.error(request, 'เพิ่มงานไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    return redirect('machine_task_list')


@login_required
def machine_task_edit(request, task_id):
    task = get_object_or_404(MachineTask, id=task_id)
    if request.method == 'POST':
        form = MachineTaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.updated_by = request.user.username
            task.save()
            messages.success(request, f'อัปเดตงาน "{task.title}" เรียบร้อยแล้ว')
        else:
            messages.error(request, 'อัปเดตงานไม่สำเร็จ กรุณาตรวจสอบข้อมูล')
    return redirect('machine_task_list')


@login_required
def machine_task_delete(request, task_id):
    task = get_object_or_404(MachineTask, id=task_id)
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'ลบงาน "{title}" เรียบร้อยแล้ว')
    return redirect('machine_task_list')


@login_required
def machine_task_detail(request, task_id):
    task = get_object_or_404(MachineTask.objects.select_related('equipment'), id=task_id)
    readings = {r.phase: r for r in task.vibration_readings.all()}
    no_load = readings.get('no_load')
    loaded = readings.get('loaded')

    comparison_rows = [
        {
            'label': label,
            'no_load': getattr(no_load, field, None) if no_load else None,
            'loaded': getattr(loaded, field, None) if loaded else None,
        }
        for field, label in MACHINE_TASK_VIBRATION_FIELDS
    ]

    return render(request, 'myapp/machine_task_detail.html', {
        'task': task,
        'no_load': no_load,
        'loaded': loaded,
        'no_load_form': MachineTaskVibrationForm(instance=no_load),
        'loaded_form': MachineTaskVibrationForm(instance=loaded),
        'comparison_rows': comparison_rows,
        'edit_form': MachineTaskForm(instance=task),
    })


@login_required
def machine_task_vibration_save(request, task_id, phase):
    task = get_object_or_404(MachineTask, id=task_id)
    if phase not in dict(MachineTaskVibration.PHASE_CHOICES):
        raise Http404('ไม่พบช่วงการทดสอบที่ระบุ')

    if request.method == 'POST':
        instance = MachineTaskVibration.objects.filter(task=task, phase=phase).first()
        form = MachineTaskVibrationForm(request.POST, instance=instance)
        if form.is_valid():
            reading = form.save(commit=False)
            reading.task = task
            reading.phase = phase
            reading.save()

            phase_label = reading.get_phase_display()
            CBMVibration.objects.create(
                equipment=task.equipment,
                inspection_date=reading.inspection_date,
                inspector=reading.inspector,
                measurement_point=f'[Task Manager] {phase_label} - {task.title}'[:150],
                amp=reading.amp, de_ge=reading.de_ge, de_v=reading.de_v, de_h=reading.de_h,
                de_a=reading.de_a, de_m=reading.de_m, nde_ge=reading.nde_ge, nde_v=reading.nde_v,
                nde_h=reading.nde_h, nde_a=reading.nde_a, nde_m=reading.nde_m,
                temp_de=reading.temp_de, temp_frame=reading.temp_frame, temp_nde=reading.temp_nde,
                status=reading.status,
            )

            if phase == 'no_load' and task.status in ('wait', 'todo'):
                task.status = 'doing'
                task.updated_by = request.user.username
                task.save(update_fields=['status', 'updated_by', 'updated_at'])
            elif phase == 'loaded':
                task.status = 'done'
                task.updated_by = request.user.username
                task.save(update_fields=['status', 'updated_by', 'updated_at'])

            messages.success(request, f'บันทึกข้อมูล {phase_label} เรียบร้อยแล้ว')
        else:
            messages.error(request, 'บันทึกข้อมูลไม่สำเร็จ กรุณาตรวจสอบข้อมูล')

    return redirect('machine_task_detail', task_id=task.id)

