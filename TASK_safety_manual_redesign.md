อ่าน CLAUDE.md ที่ root ของโปรเจกต์ก่อน แล้วทำตามข้อกำหนดในนั้นทุกข้อ (function-based views เท่านั้น, ทุกโมเดลอยู่ใน myapp/models.py, ทุกฟอร์มใน myapp/forms.py, ทุก view ใน myapp/views.py, ทุก URL ใน myapp/urls.py, ห้ามสร้าง app ใหม่, ห้ามใช้ React/Vue/framework ใดๆ, ใช้ Tailwind CSS + vanilla JS + Lucide icons ตามที่มีอยู่แล้วใน base.html, verbose_name เป็นภาษาไทยเสมอ, ฟิลด์ที่ไม่บังคับต้องมี null=True, blank=True)

## บริบท

โปรเจกต์ LAMY มีโมดูล "คู่มือความปลอดภัย" (JSA & SSOP) อยู่แล้วที่ `myapp/models.py` (โมเดล `SafetyManual`, `SafetyManualSsopStep`, `SafetyManualJsaItem`), `myapp/forms.py`, `myapp/views.py` (view `safety_manual_add` บรรทัดราว 5017), และ template `myapp/templates/myapp/safety_manual_form.html`. ตอนนี้มีแค่หน้า "เพิ่ม" (`/safety-manuals/add/`) เท่านั้น ไม่มีหน้ารายการ/แก้ไข

เป้าหมาย: ปรับฟอร์มและโครงสร้างข้อมูลให้ใช้งานง่ายขึ้น ใกล้เคียงกับเอกสารกระดาษ/Excel ต้นแบบที่บริษัทเคยใช้ก่อนย้ายมาเป็นเว็บแอป โดยเอกสารต้นแบบมีโครงสร้างดังนี้:
- SSOP: แบ่งขั้นตอนเป็น 3 ระยะคงที่เสมอ — "ก่อนปฏิบัติงาน", "ขณะปฏิบัติงาน", "เมื่อเลิกงาน" — แต่ละระยะมีรายการย่อยหลายข้อ พร้อมรูปประกอบ และช่อง "อุปกรณ์/เครื่องมือที่ต้องใช้" ที่แสดงเป็นไอคอนหลายชิ้น (หมวก ถุงมือ รองเท้า ประแจ ฯลฯ) ไม่ใช่รูปถ่ายเดียว
- JSA: แบ่งขั้นตอนเป็นกลุ่มตามงานจริง (เช่น "การเตรียมอุปกรณ์", "การถอดปั๊ม", "การยก" — ชื่อกลุ่มเปลี่ยนไปตามแต่ละงาน ไม่ตายตัว) แต่ละกลุ่มมีขั้นตอนย่อย รูปภาพ (บางขั้นตอนมีมากกว่า 1 รูป) อันตรายที่อาจเกิดขึ้น และมาตรการป้องกัน

หมายเหตุ: ฟิลด์ `phase` (ระยะ/กลุ่มขั้นตอน) และ `department` (แผนก) เคยมีอยู่ในโมเดลนี้มาก่อนแต่ถูกลบออกไปในการ refactor ล่าสุด (migration `0074_remove_safetymanualjsaitem_phase_and_more`) — งานนี้คือการเพิ่มกลับเข้ามาอย่างถูกต้อง พร้อมความสามารถใหม่ที่ไม่เคยมี

## ขอบเขตงาน

### 1. แก้ไขโมเดล (myapp/models.py)

**`SafetyManual`** — เพิ่มฟิลด์:
- `department` — `CharField(max_length=50, choices=[('ลูกหีบ','ลูกหีบ (Mill)'), ('หม้อน้ำ','หม้อน้ำ (Boiler)'), ('ซ่อมบำรุงเครื่องกล','ซ่อมบำรุงเครื่องกล (Mechanical)'), ('โรงกลึง','โรงกลึง (Lathe)')], null=True, blank=True, verbose_name="แผนก")`
- `purpose` — `TextField(null=True, blank=True, verbose_name="จุดประสงค์")`
- `manual_date` — `DateField(null=True, blank=True, verbose_name="วันที่")`

**`SafetyManualSsopStep`** — เพิ่มฟิลด์:
- `phase` — `CharField(max_length=50, choices=[('ก่อนปฏิบัติงาน','ก่อนปฏิบัติงาน'), ('ขณะปฏิบัติงาน','ขณะปฏิบัติงาน'), ('เมื่อเลิกงาน','เมื่อเลิกงาน')], null=True, blank=True, verbose_name="ระยะ")`
- แทนที่ `image_illustration` เดี่ยว ด้วยรูปได้สูงสุด 4 รูปต่อขั้นตอน: `image_illustration`, `image_illustration_2`, `image_illustration_3`, `image_illustration_4` (ทุกช่อง `ImageField(upload_to='safety_manual_ssop/', null=True, blank=True)`) — ถ้ามีข้อมูลเดิมในคอลัมน์ `image_illustration` อยู่แล้ว ให้เขียน migration ที่คง field เดิมไว้เป็นรูปแรก ไม่ทำลายข้อมูล
- เปลี่ยน `image_tools` เป็น field สำหรับ "อุปกรณ์อื่นๆ ที่ไม่อยู่ใน list" — เปลี่ยน verbose_name เป็น "รูปอุปกรณ์อื่นๆ (ถ้ามี)"
- เพิ่ม `equipment_items` — `ManyToManyField('SafetyManualEquipmentOption', blank=True, verbose_name="อุปกรณ์/เครื่องมือที่ต้องใช้")`

**`SafetyManualJsaItem`** — เพิ่มฟิลด์:
- `phase` — `CharField(max_length=255, null=True, blank=True, verbose_name="กลุ่มขั้นตอน")` (ข้อความอิสระ ไม่ใช่ choices เพราะกลุ่มเปลี่ยนตามแต่ละงาน)
- แทนที่ `image` เดี่ยว ด้วยรูปได้สูงสุด 4 รูปต่อขั้นตอน: `image`, `image_2`, `image_3`, `image_4` (เก็บ field `image` เดิมไว้เป็นรูปแรก อย่าทำลายข้อมูล)

**โมเดลใหม่ `SafetyManualEquipmentOption`** (preset อุปกรณ์/PPE แบบเลือกได้หลายอัน):
```python
class SafetyManualEquipmentOption(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่ออุปกรณ์")
    icon = models.CharField(max_length=50, default="wrench", verbose_name="ชื่อไอคอน (Lucide icon name)")
    display_order = models.PositiveIntegerField(default=0, verbose_name="ลำดับ")

    class Meta:
        verbose_name = "ตัวเลือกอุปกรณ์/PPE"
        verbose_name_plural = "ตัวเลือกอุปกรณ์/PPE"
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name
```
เขียน **data migration** เพื่อ seed ข้อมูลเริ่มต้น 12 รายการนี้ (เลือกชื่อ Lucide icon ที่มีอยู่จริงใน lucide-icons ให้ใกล้เคียงที่สุด ถ้าไม่แน่ใจว่ามีไอคอนตรงตัว ใช้ไอคอนทั่วไป เช่น `package` หรือ `shield` แทน — ผู้ใช้ปรับเองทีหลังได้):
1. หมวกนิรภัย
2. ถุงมือผ้า/ถุงมือหนัง
3. รองเท้าเซฟตี้
4. แว่นตานิรภัย
5. ชุดประแจ
6. สลิง/โซ่ยก
7. บันได
8. ใบอนุญาตทำงาน (Work Permit)
9. กุญแจล็อค (Lock-out Tag-out)
10. เข็มขัดนิรภัย
11. หน้ากากกันฝุ่น
12. ที่อุดหู

### 2. Migration

รัน `python manage.py makemigrations` แล้ว `python manage.py migrate` หลังแก้โมเดลเสร็จ (ห้ามแก้ไฟล์ migration ด้วยมือ) แล้วเขียน data migration แยกต่างหากสำหรับ seed `SafetyManualEquipmentOption`

### 3. แก้ไขฟอร์ม (myapp/forms.py)

- `SafetyManualForm` — เพิ่ม `department` (`forms.Select`), `purpose` (`forms.Textarea`), `manual_date` (`forms.DateInput(attrs={'type': 'date'})`) เข้า `fields` และ `widgets` โดยใช้ class `'w-full p-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:border-slate-700 dark:text-white'` ให้ตรงกับ widget อื่นในฟอร์มเดิม
- `SafetyManualSsopStepForm` — เพิ่ม `phase` (`forms.Select`), `image_illustration_2/3/4` (`forms.ClearableFileInput`), `equipment_items` (`forms.CheckboxSelectMultiple`)
- `SafetyManualJsaItemForm` — เพิ่ม `phase` (`forms.TextInput`), `image_2/3/4` (`forms.ClearableFileInput`)
- คง widget class เดิมของฟอร์มที่มีอยู่แล้วทั้งหมด (Tailwind classes ที่ใช้อยู่ในไฟล์ปัจจุบัน)

### 4. แก้ไข View (myapp/views.py)

แก้ `safety_manual_add` ให้รองรับฟิลด์ใหม่ (formset จะรับเองอัตโนมัติถ้า form ถูกต้อง ไม่ต้องแก้ logic การ save)

เพิ่ม view ใหม่ 2 ตัวหลัง `safety_manual_add`:

```python
@login_required
def safety_manual_list(request):
    manuals = SafetyManual.objects.all()
    department = request.GET.get('department')
    if department:
        manuals = manuals.filter(department=department)
    return render(request, 'myapp/safety_manual_list.html', {
        'manuals': manuals,
        'department_choices': SafetyManual._meta.get_field('department').choices,
        'selected_department': department,
    })


@login_required
def safety_manual_edit(request, pk):
    safety_manual = get_object_or_404(SafetyManual, pk=pk)
    if request.method == 'POST':
        form = SafetyManualForm(request.POST, request.FILES, instance=safety_manual)
        ssop_formset = SafetyManualSsopStepFormSet(request.POST, request.FILES, prefix='ssop', instance=safety_manual)
        jsa_formset = SafetyManualJsaItemFormSet(request.POST, request.FILES, prefix='jsa', instance=safety_manual)
        if form.is_valid() and ssop_formset.is_valid() and jsa_formset.is_valid():
            with transaction.atomic():
                form.save()
                ssop_formset.save()
                jsa_formset.save()
            messages.success(request, 'แก้ไขคู่มือความปลอดภัยเรียบร้อยแล้ว')
            return redirect('safety_manual_list')
    else:
        form = SafetyManualForm(instance=safety_manual)
        ssop_formset = SafetyManualSsopStepFormSet(prefix='ssop', instance=safety_manual)
        jsa_formset = SafetyManualJsaItemFormSet(prefix='jsa', instance=safety_manual)

    return render(request, 'myapp/safety_manual_form.html', {
        'form': form, 'ssop_formset': ssop_formset, 'jsa_formset': jsa_formset,
        'is_edit': True, 'safety_manual': safety_manual,
    })
```

(import `get_object_or_404` ถ้ายังไม่ได้ import อยู่ที่ด้านบนของไฟล์)

### 5. แก้ไข URL (myapp/urls.py)

เพิ่มหลังบรรทัด `path('safety-manuals/add/', ...)`:
```python
path('safety-manuals/', views.safety_manual_list, name='safety_manual_list'),
path('safety-manuals/<int:pk>/edit/', views.safety_manual_edit, name='safety_manual_edit'),
```

### 6. แก้ไข/สร้าง Template

**`myapp/templates/myapp/safety_manual_form.html`** (ใช้ร่วมกันทั้งเพิ่ม/แก้ไข ผ่าน context `is_edit`):
- เพิ่มช่อง แผนก / จุดประสงค์ / วันที่ ในส่วน "ข้อมูลทั่วไป"
- จัดกลุ่มแถว SSOP ตาม `phase` แบบ visual โดยแสดงเป็น 3 section หัวข้อ "1. ก่อนปฏิบัติงาน" / "2. ขณะปฏิบัติงาน" / "3. เมื่อเลิกงาน" (ยังใช้ formset เดิม ผูก dropdown `phase` ของแต่ละแถวไว้ แต่จัดกลุ่มด้วย JS ฝั่ง client หรือจะ render ตามลำดับ display_order/phase ก็ได้ ให้เลือกวิธีที่ทำได้ง่ายที่สุดโดยไม่กระทบ formset management form)
- แถว JSA/SSOP แต่ละแถว เพิ่มช่องอัปโหลดรูปที่ 2-4 (แสดง preview รูปเดิมถ้ามี เหมือน field รูปแรกที่ทำอยู่แล้ว)
- แถว SSOP เพิ่ม checkbox grid สำหรับ `equipment_items` แสดงเป็นไอคอน Lucide + ชื่ออุปกรณ์ (ใช้ `lucide.createIcons()` reinit ตามที่มี pattern อยู่แล้วในไฟล์)
- ปุ่ม submit เปลี่ยนข้อความเป็น "บันทึกการแก้ไข" เมื่อ `is_edit` เป็น True, หัวข้อ h1 เปลี่ยนเป็น "แก้ไขคู่มือความปลอดภัย"

**สร้างใหม่ `myapp/templates/myapp/safety_manual_list.html`**: extend `base.html`, ใช้โครง sidebar/header เดียวกับ `safety_manual_form.html`, แสดงตารางคู่มือทั้งหมด (ชื่องาน, แผนก, วันที่, ผู้จัดทำ, ปุ่มแก้ไข) พร้อม dropdown กรองตามแผนก (`department_choices`) และปุ่ม "สร้างคู่มือความปลอดภัย" ลิงก์ไป `safety_manual_add`

**แก้ `myapp/templates/myapp/manual_list.html`**: เปลี่ยนปุ่ม "สร้างคู่มือความปลอดภัย" ที่มีอยู่แล้ว ให้เพิ่มปุ่ม/ลิงก์ไปหน้า `safety_manual_list` ด้วย (ไม่ต้องลบปุ่มเดิม)

### 7. Admin (myapp/admin.py)

- อัปเดต `SafetyManualAdmin` (ถ้ายังไม่มีให้สร้าง) ให้ `list_display` รวม `job_name`, `department`, `manual_date`, `prepared_by`
- Register `SafetyManualEquipmentOption` พร้อม `list_display = ['name', 'icon', 'display_order']`

### 8. หลังแก้เสร็จ

- ตรวจสอบว่า `python manage.py check` ผ่านโดยไม่มี error
- อัปเดต README.md ตาม checklist ใน CLAUDE.md (section 9 Database Models, section 10 API Endpoints) เนื่องจากมีการเพิ่มโมเดลใหม่และ URL endpoint ใหม่
