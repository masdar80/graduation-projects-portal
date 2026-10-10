"""
===============================================================================
مشروع الصيانة التنبؤية للمحركات الحثية (Predictive Maintenance for Induction Motors)
سكريبت توليد البيانات الاصطناعية المتقدم والمرن (Flexible Synthetic Data Generator)
===============================================================================

الوصف:
هذا السكريبت يتيح خيارين رئيسيين لتوليد البيانات الاصطناعية:
1. التوليد الافتراضي السريع (Standard Default):
   توليد الحزم القياسية الأربعة المباشرة (سليم، عطل محامل، عطل ملفات، تدهور 100 ساعة).
2. التوليد المخصص حسب الحاجة (Custom On-Demand Generation):
   توليد سلاسل زمنية للمراقبة مخصصة لأي مدة زمنية يحددها المستخدم:
   (ثوانٍ، دقائق، ساعات، أيام، أسابيع، أو شهور) مع التحكم بمعدل أخذ العينات ونوع العطل.

أنواع البيانات المولدة:
أ) بيانات الموجات اللحظية عالية التردد (High-Frequency Waveforms):
   - إشارات اهتزاز ثنائية المحور (X, Y) بتردد 1,000Hz فأكثر مع ضوضاء وتوافقيات.
   - تيارات كهربائية ثلاثية الأطوار (Ia, Ib, Ic) مع إمكانية محاكاة عدم الاتزان.
   - درجة الحرارة الفورية (°C).
   - تُستخدم لاختبار تحويل فورييه (FFT) وتشخيص الأعطال (Fault Classification).

ب) بيانات المراقبة والتدهور التراكمية (Long-term Degradation & RUL Telemetry):
   - متسلسلة زمنية تحاكي تشغيل المحرك على مدار ساعات، أيام، أسابيع، أو شهور.
   - مؤشرات إحصائية مستخرجة: RMS, Crest Factor, Kurtosis, Unbalance Ratio.
   - مؤشر صحة المحرك (Health Index) من 1.0 (جديد) إلى 0.0 (منهار).
   - العمر الافتراضي المتبقي الدقيق (Remaining Useful Life - RUL) وحالة الإنذار (NORMAL, WARNING, CRITICAL).
===============================================================================
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd

def ensure_dir(directory):
    """التأكد من وجود مجلد المخرجات"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_motor_signals(sampling_rate=1000, duration_sec=2.0, fault_type="normal", degradation_factor=0.0):
    """
    توليد إشارات المحرك اللحظية عالية التردد (Waveforms)
    
    المعاملات:
    - sampling_rate: تردد العينات بالهرتز (مثلاً 1000 عينة/ثانية)
    - duration_sec: مدة التسجيل بالثواني
    - fault_type: نوع الحالة ('normal', 'bearing_fault', 'stator_fault')
    - degradation_factor: معامل التدهور من 0.0 (سليم) إلى 1.0 (انهيار كامل)
    """
    num_samples = int(sampling_rate * duration_sec)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    
    # 1. إشارة الاهتزاز الأساسية (تردد دوران 50Hz للمحرك + ضوضاء ميكانيكية)
    base_freq = 50.0 
    vibration_x = np.sin(2 * np.pi * base_freq * t)
    vibration_y = np.cos(2 * np.pi * base_freq * t)
    
    noise_level = 0.2 + (0.35 * degradation_factor)
    vibration_x += np.random.normal(0, noise_level, len(t))
    vibration_y += np.random.normal(0, noise_level, len(t))
    
    # 2. إشارات التيار الكهربائي ثلاثي الأطوار (Ia, Ib, Ic)
    # زوايا الطور: 0, 120, 240 درجة
    current_amp = 10.0 # أمبير
    Ia = current_amp * np.sin(2 * np.pi * base_freq * t)
    Ib = current_amp * np.sin(2 * np.pi * base_freq * t - (2 * np.pi / 3))
    Ic = current_amp * np.sin(2 * np.pi * base_freq * t + (2 * np.pi / 3))
    
    # 3. درجة حرارة المحرك الأساسية (°C)
    temperature = 45.0 + (12.0 * degradation_factor)
    
    # تطبيق الأعطال الفيزيائية
    if fault_type == "bearing_fault":
        # تردد عطل محامل BPFO = 120Hz
        fault_freq = 120.0
        fault_amp = 1.5 + (2.5 * degradation_factor)
        vibration_x += fault_amp * np.sin(2 * np.pi * fault_freq * t)
        vibration_y += fault_amp * np.cos(2 * np.pi * fault_freq * t)
        temperature += 16.0 # ارتفاع الحرارة بسبب احتكاك الكرات
        
    elif fault_type == "stator_fault":
        # عدم اتزان أطوار وارتفاع تيار أحد الفازات (Stator Unbalance / Turn-to-Turn)
        Ia *= (1.4 + 0.6 * degradation_factor)
        Ib *= max(0.1, (0.3 - 0.2 * degradation_factor))
        temperature += 32.0 # سخونة عالية في ملفات العضو الثابت
        vibration_x += 0.9 * np.sin(2 * np.pi * 100.0 * t) # نبضات بتردد مضاعف 100Hz
        
    df = pd.DataFrame({
        'time_sec': np.round(t, 4),
        'vibration_x_g': np.round(vibration_x, 4),
        'vibration_y_g': np.round(vibration_y, 4),
        'current_Ia_amp': np.round(Ia, 3),
        'current_Ib_amp': np.round(Ib, 3),
        'current_Ic_amp': np.round(Ic, 3),
        'temperature_c': np.round(temperature + np.random.normal(0, 0.2, len(t)), 2),
        'fault_label': fault_type,
        'degradation_ratio': np.round(degradation_factor, 3)
    })
    return df

def generate_full_degradation_timeseries(total_hours=100.0, samples_per_hour=10):
    """
    توليد متسلسلة زمنية تدهورية لمحاكاة عمر المحرك (Run-to-Failure Degradation)
    
    المعاملات:
    - total_hours: إجمالي ساعات التشغيل المحاكاة (مثلاً 24 ساعة، 168 ساعة لأسبوع، 720 لشهر)
    - samples_per_hour: عدد السجلات المسجلة في كل ساعة
    """
    total_steps = int(total_hours * samples_per_hour)
    if total_steps < 10:
        total_steps = 10
        
    records = []
    
    for step in range(total_steps):
        time_hours = (step / total_steps) * total_hours
        # منحنى تدهور تدريجي أسي يعكس التآكل الميكانيكي الواقعي (Weibull / Exponential)
        degradation = (step / total_steps) ** 2.2
        rul_hours = max(0.0, total_hours - time_hours)
        
        # نوع العطل يتطور تلقائياً مع زيادة نسبة التدهور
        if degradation < 0.35:
            fault_type = "normal"
            status = "NORMAL"
        elif degradation < 0.70:
            fault_type = "bearing_fault" if step % 2 == 0 else "stator_fault"
            status = "WARNING"
        else:
            fault_type = "bearing_fault"
            status = "CRITICAL"
            
        # محاكاة لقطة اهتزاز قصيرة لاستخراج المؤشرات الإحصائية
        sample_df = generate_motor_signals(sampling_rate=500, duration_sec=0.5, fault_type=fault_type, degradation_factor=degradation)
        vib_x = sample_df['vibration_x_g'].values
        
        # حساب المؤشرات الإحصائية المعتمدة صناعياً (Time-Domain Features)
        rms = np.sqrt(np.mean(vib_x ** 2))
        crest_factor = np.max(np.abs(vib_x)) / (rms + 1e-6)
        kurtosis = np.mean(((vib_x - np.mean(vib_x)) / (np.std(vib_x) + 1e-6)) ** 4)
        avg_temp = sample_df['temperature_c'].mean()
        
        # نسبة عدم اتزان التيار (Current Unbalance Ratio)
        current_means = [sample_df['current_Ia_amp'].mean(), sample_df['current_Ib_amp'].mean(), sample_df['current_Ic_amp'].mean()]
        unbalance = np.std(current_means)
        
        records.append({
            'operating_hours': np.round(time_hours, 2),
            'rms_vibration': np.round(rms, 4),
            'crest_factor': np.round(crest_factor, 4),
            'kurtosis': np.round(kurtosis, 4),
            'avg_temperature_c': np.round(avg_temp, 2),
            'current_unbalance_ratio': np.round(unbalance, 3),
            'health_index': np.round(max(0.0, 1.0 - degradation), 4),
            'RUL_hours': np.round(rul_hours, 2),
            'status': status
        })
        
    return pd.DataFrame(records)

def convert_to_hours(duration, unit):
    """تحويل وحدات الوقت المختلفة إلى ساعات"""
    unit = unit.lower()
    if unit in ['hour', 'hours', 'ساعة', 'ساعات']:
        return float(duration)
    elif unit in ['day', 'days', 'يوم', 'ايام', 'أيام']:
        return float(duration) * 24.0
    elif unit in ['week', 'weeks', 'اسبوع', 'اسابيع', 'أسبوع', 'أسابيع']:
        return float(duration) * 24.0 * 7.0
    elif unit in ['month', 'months', 'شهر', 'شهور', 'اشهر', 'أشهر']:
        return float(duration) * 24.0 * 30.0 # اعتبار الشهر 30 يوماً
    elif unit in ['minute', 'minutes', 'دقيقة', 'دقائق']:
        return float(duration) / 60.0
    elif unit in ['second', 'seconds', 'ثانية', 'ثواني']:
        return float(duration) / 3600.0
    else:
        raise ValueError(f"وحدة الوقت غير معروفة: {unit}. الخيارات المتاحة: seconds, minutes, hours, days, weeks, months")

def generate_default_suite(output_dir):
    """توليد الحزمة القياسية الأربعة المباشرة"""
    print("\n=================================================================")
    print("🚀 بدء توليد الحزمة القياسية الكاملة (الوضع الافتراضي السريع)...")
    print("=================================================================")
    
    # 1. إشارة محرك سليم (2 ثانية @ 1000Hz)
    df_normal = generate_motor_signals(sampling_rate=1000, duration_sec=2.0, fault_type="normal", degradation_factor=0.0)
    p_norm = os.path.join(output_dir, "synthetic_motor_normal.csv")
    df_normal.to_csv(p_norm, index=False)
    print(f"✔️ [1/4] تم حفظ بيانات المحرك السليم ({len(df_normal)} صف): {p_norm}")
    
    # 2. إشارة عطل محامل
    df_bearing = generate_motor_signals(sampling_rate=1000, duration_sec=2.0, fault_type="bearing_fault", degradation_factor=0.7)
    p_bear = os.path.join(output_dir, "synthetic_motor_bearing_fault.csv")
    df_bearing.to_csv(p_bear, index=False)
    print(f"✔️ [2/4] تم حفظ بيانات عطل المحامل ({len(df_bearing)} صف): {p_bear}")
    
    # 3. إشارة عطل ملفات
    df_stator = generate_motor_signals(sampling_rate=1000, duration_sec=2.0, fault_type="stator_fault", degradation_factor=0.8)
    p_stat = os.path.join(output_dir, "synthetic_motor_stator_fault.csv")
    df_stator.to_csv(p_stat, index=False)
    print(f"✔️ [3/4] تم حفظ بيانات عطل الملفات ({len(df_stator)} صف): {p_stat}")
    
    # 4. متسلسلة تدهور وعمر المحرك (100 ساعة)
    df_rul = generate_full_degradation_timeseries(total_hours=100.0, samples_per_hour=10)
    p_rul = os.path.join(output_dir, "synthetic_motor_rul_degradation.csv")
    df_rul.to_csv(p_rul, index=False)
    print(f"✔️ [4/4] تم حفظ متسلسلة التدهور و RUL ({len(df_rul)} نقطة زمنية - 100 ساعة): {p_rul}")
    
    print("\n✅ اكتمل توليد الحزمة القياسية بنجاح في المجلد `generated_datasets`!")

def main():
    parser = argparse.ArgumentParser(
        description="مولد البيانات الاصطناعية المتقدم لمشروع الصيانة التنبؤية للمحركات الحثية",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '--mode',
        choices=['all', 'waveform', 'rul'],
        default='all',
        help="نمط التشغيل:\n"
             " - all: توليد الحزمة القياسية الكاملة لجميع الملفات (الافتراضي)\n"
             " - waveform: توليد إشارات لحظية عالية التردد (اهتزاز وتيار)\n"
             " - rul: توليد متسلسلة زمنية تدهورية طويلة لتوقع العمر RUL"
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=None,
        help="المدة الزمنية المطلوبة للتوليد (مثلاً: 2 للثواني، أو 7 للأيام، أو 1 للأشهر)"
    )
    parser.add_argument(
        '--unit',
        choices=['seconds', 'minutes', 'hours', 'days', 'weeks', 'months'],
        default='hours',
        help="وحدة الوقت للخاصية --duration (الافتراضي: hours)"
    )
    parser.add_argument(
        '--sampling-rate',
        type=int,
        default=1000,
        help="معدل العينات بالهرتز (Hz) لنمط waveform (الافتراضي: 1000)"
    )
    parser.add_argument(
        '--samples-per-hour',
        type=int,
        default=6,
        help="عدد السجلات المأخوذة لكل ساعة لنمط rul (الافتراضي: 6، أي عينة كل 10 دقائق)"
    )
    parser.add_argument(
        '--fault',
        choices=['normal', 'bearing_fault', 'stator_fault'],
        default='normal',
        help="نوع العطل المطلوب لنمط waveform (الافتراضي: normal)"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help="المسار المخصص لحفظ الملفات الناتجة (الافتراضي: مجلد generated_datasets التابع للسكريبت)"
    )
    parser.add_argument(
        '--output-name',
        type=str,
        default=None,
        help="اسم ملف CSV المخصص عند التوليد المخصص"
    )

    args = parser.parse_args()

    # تحديد مجلد الإخراج
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = args.output_dir if args.output_dir else os.path.join(base_dir, "generated_datasets")
    ensure_dir(output_dir)

    # 1. إذا اختار المستخدم نمط all دون تحديد مدة مخصصة -> توليد الحزمة الافتراضية
    if args.mode == 'all' and args.duration is None:
        generate_default_suite(output_dir)
        return

    # 2. نمط الموجات اللحظية (Waveform Mode)
    if args.mode == 'waveform':
        duration_sec = args.duration if args.duration else 2.0
        if args.unit == 'minutes':
            duration_sec *= 60.0
        elif args.unit == 'hours':
            duration_sec *= 3600.0
        elif args.unit == 'days':
            duration_sec *= 86400.0
            
        print(f"\n⚡ جاري توليد إشارات لحظية ({args.fault}) لمدة {duration_sec} ثانية بتردد {args.sampling_rate} Hz...")
        df_wave = generate_motor_signals(
            sampling_rate=args.sampling_rate,
            duration_sec=duration_sec,
            fault_type=args.fault,
            degradation_factor=0.6 if args.fault != 'normal' else 0.0
        )
        
        file_name = args.output_name if args.output_name else f"custom_waveform_{args.fault}_{int(duration_sec)}s.csv"
        out_path = os.path.join(output_dir, file_name)
        df_wave.to_csv(out_path, index=False)
        print(f"✅ تم توليد ملف الإشارات بنجاح ({len(df_wave)} صف): {out_path}")
        return

    # 3. نمط متسلسلة التدهور والعمر (RUL Mode)
    if args.mode == 'rul' or (args.mode == 'all' and args.duration is not None):
        duration_val = args.duration if args.duration else 100.0
        total_hours = convert_to_hours(duration_val, args.unit)
        
        print(f"\n⏳ جاري محاكاة تدهور المحرك التراكمي لمدة {duration_val} {args.unit} (ما يعادل {total_hours:.1f} ساعة تشغيل)...")
        print(f"📊 معدل التسجيل: {args.samples_per_hour} عينة/ساعة...")
        
        df_rul = generate_full_degradation_timeseries(
            total_hours=total_hours,
            samples_per_hour=args.samples_per_hour
        )
        
        file_name = args.output_name if args.output_name else f"synthetic_rul_{int(duration_val)}_{args.unit}.csv"
        out_path = os.path.join(output_dir, file_name)
        df_rul.to_csv(out_path, index=False)
        print(f"✅ تم توليد ملف التدهور بنجاح ({len(df_rul)} نقطة مراقبة): {out_path}")
        print(f"   - بداية التشغيل: الحالة السليمة (Health Index: {df_rul['health_index'].iloc[0]})")
        print(f"   - نهاية التشغيل: حالة الانهيار (Health Index: {df_rul['health_index'].iloc[-1]})")
        print(f"   - العمر الافتراضي المتبقي (RUL): يبدأ من {df_rul['RUL_hours'].iloc[0]} ساعة وينحدر تدريجياً إلى 0.")

if __name__ == "__main__":
    main()
