# دليل مرحلة استحواذ وتوليد البيانات (Data Acquisition & Benchmark Manual)

يقدم هذا المجلد الأدوات والتوجيهات الكاملة الخاصة **بالمرحلة الثانية: استحواذ وتوليد البيانات** لمشروع التخرج في الصيانة التنبؤية للمحركات الحثية (Predictive Maintenance for 3-Phase Induction Motors).

---

## 📂 فهرس ملفات ومجلدات المرحلة (Data Acquisition Directory Map)

### 📁 المجلد الرئيسي: `data_acquisition/`

#### 1️⃣ مجلد البيانات المولدة اصطناعياً (`generated_datasets/`) - الخيار الأول:
* 📊 `synthetic_motor_normal.csv` — إشارات المحرك في الحالة السليمة (2 ثانية @ 1000Hz).
* 📊 `synthetic_motor_bearing_fault.csv` — إشارات عطل المحامل الميكانيكي (120Hz BPFO).
* 📊 `synthetic_motor_stator_fault.csv` — إشارات عطل ملفات العضو الثابت وعدم اتزان الأطوار.
* 📊 `synthetic_motor_rul_degradation.csv` — متسلسلة التدهور ومراقبة العمر RUL (100 ساعة).
* 📊 `synthetic_rul_7_days.csv` — متسلسلة تدهور مخصصة لأسبوع كامل (168 ساعة).

#### 2️⃣ مجلد قواعد البيانات العالمية (`benchmark_datasets/`) - الخيار الثاني:
* 📁 `CWRU_Bearing_Data/` ➔ 📊 `CWRU_Benchmark_Sample.csv` — بيانات جامعة كيس ويسترن ريسرف (12kHz).
* 📁 `NASA_Prognostics_Data/` ➔ 📊 `NASA_FD001_Bearing_Degradation.csv` — بيانات مركز ناسا لتوقع العمر RUL.

#### 3️⃣ الأكواد وأدلة التوثيق (Scripts & Manuals):
* 🐍 `generate_synthetic_motor_data.py` — سكريبت بايثون المطور لتوليد البيانات (الافتراضي أو المخصص لأيام/شهور).
* 🌐 `README_data_acquisition.html` — الدليل التفاعلي الكامل للمرحلة (صفحة ويب متكاملة).
* 📘 `README_data_acquisition.md` — الدليل المكتوب بصيغة Markdown للقراءة السريعة.

---

## 🟢 الخيار الأول: التوليد الاصطناعي (Synthetic Data Generator)

### 💡 هل تُولد هذه الأكواد بيانات ثابتة أم متغيرة حسب الحاجة (أيام / أسابيع / أشهر)؟
**الإجابة:** الأكواد تدعم النمطين معاً بأعلى مرونة:
1. **النمط الافتراضي السريع (Fixed Quick-Start):**
   عند تشغيل السكريبت المباشر، يُنتج فوراً الحزم القياسية الأربعة السريعة (سليم، عطل محامل، عطل ملفات، وتدهور 100 ساعة) لتجربة الكود والتدريب الفوري.
2. **نمط التوليد المخصص حسب الطلب (Dynamic On-Demand):**
   يمكنك تحديد أي مدة زمنية بالكامل عبر المعاملات:
   - **بالساعات (Hours):** مثلاً 24 ساعة، 48 ساعة.
   - **بالأيام (Days):** مثلاً 7 أيام (أسبوع)، 14 يوماً، 30 يوماً.
   - **بالأسابيع (Weeks):** مثلاً أسبوعين، 4 أسابيع.
   - **بالأشهر (Months):** مثلاً شهر واحد، 3 أشهر، 6 أشهر.
   - **بالثواني أو الدقائق:** للموجات اللحظية عالية التردد (Waveforms).

---

### 🧠 الفرق العلمي بين نوعي البيانات المولدة

| وجه المقارنة | إشارات الموجات اللحظية (Waveforms) | بيانات المراقبة والتدهور التراكمية (RUL Telemetry) |
|---|---|---|
| **الهدف الهندسي** | تشخيص نوع العطل (Fault Classification) ومطياف FFT | توقع العمر الافتراضي المتبقي (RUL) ومؤشر الصحة |
| **معدل أخذ العينات** | عالي جداً: 1,000Hz إلى 12,000Hz | معدل زمني منتظم: مثلاً 6 عينات/ساعة (كل 10 دقائق) |
| **المدى الزمني المناسب** | ثوانٍ أو دقائق (لقطات سريعة Bursts) | أيام، أسابيع، أو أشهر لمحاكاة دورة حياة المحرك |
| **المتغيرات المسجلة** | اهتزاز فوري X, Y، تيار الأطوار 3، حرارة لحظية | RMS الاهتزاز، Crest Factor، Kurtosis، اتزان التيار، RUL |

---

### 💻 أوامر التشغيل والاستخدام في Terminal

المكتبات المطلوبة:
```bash
pip install numpy pandas
```

1. **التشغيل الافتراضي السريع:**
```bash
python data_acquisition/generate_synthetic_motor_data.py
```

2. **توليد بيانات مراقبة وتدهور RUL لمدة أسبوع كامل (7 أيام):**
```bash
python data_acquisition/generate_synthetic_motor_data.py --mode rul --duration 7 --unit days --samples-per-hour 6
```

3. **توليد بيانات مراقبة وتدهور RUL لشهر كامل (30 يوماً / 720 ساعة):**
```bash
python data_acquisition/generate_synthetic_motor_data.py --mode rul --duration 1 --unit months --samples-per-hour 2
```

4. **توليد إشارة اهتزاز وتيار لحظية عالية التردد (2000Hz) لمدة 10 ثوانٍ:**
```bash
python data_acquisition/generate_synthetic_motor_data.py --mode waveform --fault bearing_fault --duration 10 --sampling-rate 2000
```

---

## 📊 أشكال الخرج ومواصفات الحقول بالتفصيل (Output Schemas)

### أ) شكل الخرج لملفات الإشارات اللحظية (Waveforms)
ينطبق على: `synthetic_motor_normal.csv`, `synthetic_motor_bearing_fault.csv`, `synthetic_motor_stator_fault.csv`

| اسم الحقل | الوحدة | الوصف الفيزيائي | مثال |
|---|---|---|---|
| `time_sec` | ثانية (s) | الزمن اللحظي بدقة 4 خانات عشرية | 0.0020 |
| `vibration_x_g` | g | تسارع الاهتزاز في المحور الأفقي X | 1.0821 |
| `vibration_y_g` | g | تسارع الاهتزاز في المحور الرأسي Y | -0.9415 |
| `current_Ia_amp` | A | تيار الطور الأول A (تردد 50Hz) | 9.852 |
| `current_Ib_amp` | A | تيار الطور الثاني B (فارق طور 120°) | -4.912 |
| `current_Ic_amp` | A | تيار الطور الثالث C (فارق طور 240°) | -4.940 |
| `temperature_c` | °C | درجة حرارة هيكل المحرك | 45.18 |
| `fault_label` | نص | التصنيف: normal, bearing_fault, stator_fault | normal |
| `degradation_ratio` | 0.0 - 1.0 | معامل التدهور المفروض | 0.000 |

### ب) شكل الخرج لملف متسلسلة التدهور والعمر (RUL Telemetry)
ينطبق على: `synthetic_motor_rul_degradation.csv` والملفات المخصصة للأيام والأسابيع والشهور.

| اسم الحقل | الوحدة | الوصف التشغيلي ونمذجة AI | التغير مع الزمن |
|---|---|---|---|
| `operating_hours` | hr | ساعات العمل التراكمية المنقضية | تزايدي (0 إلى أقصى مدة) |
| `rms_vibration` | g | جذر متوسط مربعات الاهتزاز (طاقة الاهتزاز) | يرتفع تدريجياً مع زيادة التآكل |
| `crest_factor` | نسبة | معامل القمة لكشف الصدمات المبكرة | يقفز بشدة عند حدوث الصدمات |
| `kurtosis` | نسبة | معامل التفرطح لتوزيع الإشارة (المعيار الصناعي) | يتجاوز 3.0 بشكل حاد عند العيوب |
| `avg_temperature_c` | °C | متوسط حرارة المحرك | يرتفع مع زيادة الاحتكاك |
| `current_unbalance_ratio` | نسبة | نسبة عدم الاتزان بين تيارات الأطوار | يقفز عند تآكل عوازل الملفات |
| `health_index` | 0.0 - 1.0 | مؤشر صحة المحرك (1.0 = جديد، 0.0 = منهار) | ينحدر تنازلياً مع اقتراب الفشل |
| `RUL_hours` | hr | العمر الافتراضي المتبقي الدقيق (Target) | ينخفض تنازلياً نحو الصفر |
| `status` | نص | حالة الخطر: NORMAL, WARNING, CRITICAL | يتغير تلقائياً حسب مؤشر الصحة |

---

## 🔵 الخيار الثاني: قواعد البيانات العالمية المعتمدة (Benchmark Datasets)

### 1. داتا سيت جامعة كيس ويسترن ريسرف (CWRU Bearing Dataset)
* **المصدر الرسمي:** [Case Western Reserve University Bearing Data Center](http://caseds.case.edu/)
* **المسار النسبي:** `data_acquisition/benchmark_datasets/CWRU_Bearing_Data/CWRU_Benchmark_Sample.csv`

### 2. داتا سيت ناسا لتوقع العمر الافتراضي المتبقي (NASA Prognostics Repository)
* **المصدر الرسمي:** [NASA Data Portal & Prognostics Center](https://data.nasa.gov/)
* **المسار النسبي:** `data_acquisition/benchmark_datasets/NASA_Prognostics_Data/NASA_FD001_Bearing_Degradation.csv`

---

## 🔗 الربط مع الصفحة الرئيسية
يمكنك فتح الدليل التفاعلي كصفحة ويب مباشرة عبر:
[README_data_acquisition.html](README_data_acquisition.html)
