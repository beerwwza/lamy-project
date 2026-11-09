# แผนปรับปรุง: Module "ใบลองเครื่อง Gearbox & Gearmotor" (ยึดโครงสร้าง MEInspection)

## Context
แผนต้นฉบับ `GearTrialRun_Module_Plan.md` (แนวทางหลัก ข้อตัดสินใจ 3 ข้อ และ T1–T6 ยังใช้ตามเดิม) ถูกตรวจเทียบกับโค้ดที่ clone มาบนเครื่องนี้ (branch `MatID`, tree สะอาด) แล้ว
ผู้ใช้ยืนยันว่า concept ใกล้เคียงใบตรวจเช็คซ่อม (ME) จึงให้ลอก pattern ของ ME ให้มากที่สุด รวมถึงส่วนที่แผนเดิมยังไม่ได้พูดถึง

## สิ่งที่ตรวจพบ (ต้องแก้แผนเดิม)

| หัวข้อ | แผนเดิม | ของจริงบนเครื่องนี้ |
|---|---|---|
| เลขบรรทัด | models 2548, views 7464, base.html ~158 | `MEInspection` models.py:2557, helper `_me_dec2/_me_dec3` :2544-2549, views 7520–7800, เมนู ME base.html:158-160 (ใช้ค้นชื่อ ไม่ยึดเลข) |
| migration ล่าสุด | 0107 (main) | `0110_equipmentbom_material` บน MatID (ทำงานบน MatID ต่อ จึงต่อจาก 0110) |
| path docs | `docs/MatID_Module_Plan.md` | ยังไม่มีโฟลเดอร์ `docs/` ในเครื่องนี้ → สร้างใหม่ตอนบันทึกแผน |
| **สิทธิ์การเขียน** | ไม่มี (มีแค่ `@login_required`) | ระบบ module permission มีอยู่แล้ว: ME ใช้ `@module_required_any(*ME_WRITE_MODULES)` โดย `ME_WRITE_MODULES = ('maintenance','cbm')` (views.py:7214) + `_me_can_write()` ส่งเข้า template |
| API เติมสเปค | `me_equipment_search_api` | มีอีกตัว `me_inspection_last_api` (smart memory: ดึงค่าจากใบล่าสุดของเครื่องเดียวกัน) และ `_me_equipment_snapshot(eq)` |
| list/filter | filter ใน view ตรงๆ | ME แยก `_me_filtered(request)` ใช้ร่วม list + dashboard + Paginator |

## ส่วนที่ต้องเพิ่ม/ปรับในแผน

1. **สิทธิ์ (สำคัญ)** — add/edit/delete ของ Gear ต้องใส่ `@module_required_any('maintenance','cbm')` (นิยามค่าคงที่ `GEAR_WRITE_MODULES` ชุดเดียวกับ ME แล้วอ้าง `ME_WRITE_MODULES` ซ้ำได้), list/dashboard/print ใช้ `@login_required`, ส่ง `can_write` เข้า template ซ่อนปุ่มเพิ่ม/แก้/ลบ; ไม่ต้องสร้าง module key ใหม่ ไม่ต้อง migration สิทธิ์ (ต่างจากกรณี Energy)
2. **ใช้ pattern ME ซ้ำ ไม่เขียนใหม่**
   - `_gear_filtered(request)` เลียนแบบ `_me_filtered` → ใช้ร่วม list/dashboard, `Paginator`, ตัวกรองวันที่พร้อม `bad_dates` message
   - `_gear_equipment_snapshot(eq)` เลียนแบบ `_me_equipment_snapshot` (map `power_kw`, `rpm_input`, `model`, `manufacturer`)
   - ช่องค้นหาเครื่อง: **ใช้ `me_equipment_search_api` เดิมซ้ำได้** ถ้า payload พอ (มี brand/model/kw/rpm) — ไม่ต้องสร้าง API ใหม่; เพิ่มเฉพาะ `gear_trial_run_last_api` (smart memory ค่าเนมเพลทจากใบก่อนหน้าของเครื่องเดียวกัน) เป็นทางเลือกใน T3
   - helper field: `_gear_dec2(label)` ในรูปแบบเดียวกับ `_me_dec2`
   - ป้าย `ME-{pk}` → `GT-{pk}` ในข้อความ delete
   - add/edit redirect กลับหน้า edit หลังบันทึก (ตาม ME) เพื่อให้ต่อยอดกรอกส่วน 3–5 ได้ระหว่างลองเครื่อง
3. **สถานะใบงาน** (ยืมแนว `ME_STATUS_*`) — ใบลองเครื่องกรอกต่อเนื่องหลายช่วง (0/15/30 นาที) จึงเพิ่ม `status` (กำลังทดสอบ/เสร็จสิ้น) ให้ list กรองได้ และ dashboard นับเฉพาะใบที่เสร็จ; ให้ถือเป็นข้อเสนอ → ยืนยันตอน to-spec
4. **Tab layout** — ฟอร์มยาวมาก (~100 ช่อง) ทำเป็นแท็บ vanilla JS แบบเดียวกับ `me_inspection_form.html` (แท็บ: ข้อมูลทั่วไป+เนมเพลท / ก่อนเดิน / ลองเดิน No-Load&Load / Vibration / หลังหยุด+สรุป) บนมือถือแท็บต้อง scroll แนวนอนได้
5. **ชนิดข้อมูล** — ใช้ `Decimal(8,2)` สำหรับอุณหภูมิ/กระแส/แรงดัน/vibration ตามแผนเดิม (ไม่ต้อง 3 ตำแหน่งเหมือนขนาดเชิงกลของ ME)
6. **Test** — เพิ่มใน `myapp/tests.py` (ไฟล์เดียวตามโครงสร้างโปรเจกต์) รวมกรณี: ผู้ใช้ไม่มีสิทธิ์ write → 403 ที่ add/edit/delete แต่เปิด list/print ได้

## ลำดับงาน (ปรับจากเดิม)
0. ทำต่อบน branch `MatID` ปัจจุบันเลย (ไม่แตก branch ใหม่) — migration ใหม่จะต่อจาก `0110_equipmentbom_material` ตามที่ `makemigrations` ออกให้
1. บันทึกแผนที่ปรับแล้วลง `docs/GearTrialRun_Module_Plan.md`
2. to-spec → ผู้ใช้อนุมัติ (ยืนยัน: เกณฑ์ 75/85°C, FLA 95%, ISO 10816-3 2.8/4.5 mm/s, field `status`, สิทธิ์ `maintenance`/`cbm`)
3. to-tickets → T1 Model+migration+admin+helper+test · T2 Form+add/edit/list+สิทธิ์+เมนู · T3 JS สีสด+เติมเนมเพลท · T4 Dashboard · T5 print A4+delete · T6 README+responsive
4. implement ทีละ ticket (ไม่ commit เอง) → code-review เทียบ spec + CLAUDE.md → ผู้ใช้สั่ง commit/merge

## ไฟล์ที่ต้องแก้ (pattern ซ้ำจาก ME)
`myapp/models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`, `tests.py`, `templates/myapp/base.html` (เมนูถัดจาก "ใบตรวจเช็คซ่อม (ME)" ใช้ `request.resolver_match.url_name` แบบเดียวกัน), `templates/myapp/gear_trial_run_{form,list,dashboard,print}.html`, `README.md`

## Verification
```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test myapp
```
+ Unit test เกณฑ์ขอบ (75/75.1/85/85.1°C, 95%/100% FLA, 2.8/2.81/4.5/4.51 mm/s, ว่าง→None), view test (login/สิทธิ์/POST/validation/delete ด้วย GET ไม่ได้), timezone test (`test_date` default = `timezone.localdate()`)
+ runserver ตรวจ 375/768/1280px: ไม่มี scroll แนวนอนนอกตาราง, sidebar มือถือ, `<select>` สูงเท่า `<input>`, หน้าพิมพ์ลง A4
