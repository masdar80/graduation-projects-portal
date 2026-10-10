"""
===============================================================================
مشروع التوأم الرقمي لمصفاة بانياس للنفط (Baniyas Refinery Digital Twin)
سكريبت توليد البيانات الصناعية والحرارية للمصفاة (Refinery Process Data Generator)
===============================================================================

الوصف:
هذا السكريبت يحاكي بدقة فيزيائية وحرارية مجمع التقطير الجوي (Atmospheric Distillation Unit)
وشبكة تسخين النفط الخام (Crude Preheat Train) وفرن التقطير (Furnace F-101) في مصفاة بانياس بسوريا.

يحاكي السكريبت تأثير معالجة النفط السوري الثقيل (نفط السويدية، API ~24°، كبريت عالي ~4% وأسفلتين مرتفع)
على تراكم الترسبات الهيدروكربونية والتكلس (Asphaltene Fouling & Coke Deposition) في خطي المبادلات (Train A & Train B)
وأنابيب الفرن الحراري، وإصدار توصيات الصيانة المتوازية (Bypass Online Cleaning) لتجنب الإطفاء الكلي للمصفاة.

الأنماط المدعومة:
1. التوليد الافتراضي السريع:
   - تشغيل طبيعي مستقر (refinery_cdu_normal.csv).
   - تكلس متسارع في الخط A (refinery_severe_fouling_train_a.csv).
   - ارتفاع حرارة جدار أنابيب الفرن (refinery_furnace_tube_overheating.csv).
   - متسلسلة زمنية تدهورية شاملة لـ 30 يوماً (refinery_fouling_timeseries_30days.csv).
2. التوليد المخصص حسب الطلب (On-Demand):
   - دعم التوليد لأي مدة زمنية (ساعات، أيام، أسابيع، شهور) عبر سطر الأوامر CLI.
===============================================================================
"""

import os
import argparse
import numpy as np
import pandas as pd

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def convert_to_hours(duration, unit):
    unit = unit.lower()
    if unit in ['hour', 'hours', 'ساعة', 'ساعات']:
        return float(duration)
    elif unit in ['day', 'days', 'يوم', 'أيام', 'ايام']:
        return float(duration) * 24.0
    elif unit in ['week', 'weeks', 'أسبوع', 'اسبوع', 'أسابيع', 'اسابيع']:
        return float(duration) * 24.0 * 7.0
    elif unit in ['month', 'months', 'شهر', 'شهور', 'أشهر']:
        return float(duration) * 24.0 * 30.0
    else:
        raise ValueError(f"وحدة الوقت غير مدعومة: {unit}")

def simulate_refinery_cdu(total_hours=100.0, samples_per_hour=2, scenario="normal"):
    """
    محاكاة حرارية وديناميكية لمجمع التقطير الجوي بمصفاة بانياس
    """
    total_steps = int(total_hours * samples_per_hour)
    if total_steps < 10:
        total_steps = 10

    records = []

    # المعايير التصميمية لمصفاة بانياس (Design Parameters)
    nominal_flow_total = 450.0  # m3/h إجمالي تدفق الخام (حوالي 130,000 برميل/يوم)
    nominal_train_flow = nominal_flow_total / 2.0  # 225 m3/h لكل خط مبادلات
    clean_U = 650.0  # W/m2·K معامل انتقال الحرارة النظيف
    target_furnace_outlet = 360.0  # °C حرارة مخرج الفرن للدخول إلى برج التقطير
    clean_tube_skin = 395.0  # °C حرارة جدار أنبوب الفرن في الحالة النظيفة

    for step in range(total_steps):
        t_hours = (step / total_steps) * total_hours
        progress = step / total_steps

        # تذبذب طفيف واقعي في معدل تدفق الخام من الخزانات
        flow_total = nominal_flow_total + np.random.normal(0, 3.5)
        flow_a = (flow_total / 2.0) + np.random.normal(0, 1.5)
        flow_b = flow_total - flow_a
        crude_inlet_temp = 28.0 + np.random.normal(0, 0.5)

        # حساب معدل التكلس ومقاومة الترسب Rf وفق السيناريو (نموذج Ebert-Panchal)
        if scenario == "normal":
            # ترسب طفيف جداً ضمن المعدل الطبيعي المصمم
            rf_a = 0.0002 + (0.0001 * progress)
            rf_b = 0.0002 + (0.00008 * progress)
            coking_factor = progress * 0.1
            status = "NORMAL"

        elif scenario == "severe_fouling":
            # ترسب متسارع في الخط A بسبب ترسبات الأسفلتين ونفط السويدية الثقيل
            rf_a = 0.0002 + (0.0028 * (progress ** 1.8))
            rf_b = 0.0002 + (0.0004 * progress)
            coking_factor = progress * 0.4
            status = "NORMAL" if rf_a < 0.001 else ("WARNING_FOULING_TRAIN_A" if rf_a < 0.0022 else "BYPASS_CLEANING_RECOMMENDED")

        elif scenario == "tube_overheating":
            # تكلس كربوني داخل أنابيب الفرن الحراري
            rf_a = 0.0002 + (0.0008 * progress)
            rf_b = 0.0002 + (0.0007 * progress)
            coking_factor = (progress ** 1.6) * 1.0  # تكلس شديد في الفرن
            status = "NORMAL" if coking_factor < 0.3 else ("WARNING_FURNACE_HOTSPOT" if coking_factor < 0.7 else "CRITICAL_TUBE_OVERHEAT")

        elif scenario in ["timeseries", "timeseries_30days"]:
            # متسلسلة زمنية تتبع تدهور حقيقي وتفعيل وضع التجاوز في النهاية
            rf_a = 0.0002 + (0.0032 * (progress ** 1.9))
            rf_b = 0.0002 + (0.0009 * progress)
            coking_factor = (progress ** 1.5) * 0.75
            if rf_a < 0.0012:
                status = "NORMAL"
            elif rf_a < 0.0024:
                status = "WARNING_FOULING_TRAIN_A"
            else:
                status = "BYPASS_CLEANING_RECOMMENDED"

        # حساب معامل انتقال الحرارة U (W/m2·K)
        u_a = 1.0 / ((1.0 / clean_U) + rf_a)
        u_b = 1.0 / ((1.0 / clean_U) + rf_b)

        # حساب درجات حرارة مخرج المبادلات (°C)
        train_a_outlet = crude_inlet_temp + (210.0 * (u_a / clean_U)) + np.random.normal(0, 0.4)
        train_b_outlet = crude_inlet_temp + (210.0 * (u_b / clean_U)) + np.random.normal(0, 0.4)

        # حرارة مدخل الفرن F-101 هي الخليط بين الخطين
        furnace_inlet_temp = ((train_a_outlet * flow_a) + (train_b_outlet * flow_b)) / flow_total

        # حرارة جدار أنبوب الفرن F-101 (°C) - ترتفع بشدة مع انخفاض حرارة المدخل ونمو الكوك الداخلي
        skin_temp = clean_tube_skin + (coking_factor * 52.0) + ((230.0 - furnace_inlet_temp) * 0.15) + np.random.normal(0, 0.6)

        # هبوط الضغط عبر المبادلات (bar) - يزداد مع ضيق الأنابيب بسبب التكلس
        dp_a = 3.5 + (rf_a * 1400.0) + np.random.normal(0, 0.05)
        dp_b = 3.5 + (rf_b * 1400.0) + np.random.normal(0, 0.05)

        # استهلاك غاز الوقود في الفرن (Fuel Gas kg/h) لتعويض هبوط كفاءة المبادلات
        fuel_consumption = 1850.0 + ((235.0 - furnace_inlet_temp) * 14.5) + np.random.normal(0, 8.0)

        records.append({
            'operating_hours': np.round(t_hours, 2),
            'crude_flow_total_m3h': np.round(flow_total, 2),
            'flow_train_a_m3h': np.round(flow_a, 2),
            'flow_train_b_m3h': np.round(flow_b, 2),
            'crude_inlet_temp_c': np.round(crude_inlet_temp, 2),
            'train_a_outlet_temp_c': np.round(train_a_outlet, 2),
            'train_b_outlet_temp_c': np.round(train_b_outlet, 2),
            'furnace_inlet_temp_c': np.round(furnace_inlet_temp, 2),
            'furnace_outlet_temp_c': np.round(target_furnace_outlet + np.random.normal(0, 0.3), 2),
            'furnace_tube_skin_temp_c': np.round(skin_temp, 2),
            'delta_p_train_a_bar': np.round(dp_a, 3),
            'delta_p_train_b_bar': np.round(dp_b, 3),
            'U_coeff_train_a_W_m2K': np.round(u_a, 2),
            'U_coeff_train_b_W_m2K': np.round(u_b, 2),
            'Rf_fouling_train_a': np.round(rf_a, 6),
            'Rf_fouling_train_b': np.round(rf_b, 6),
            'fuel_consumption_kg_h': np.round(fuel_consumption, 1),
            'operating_status': status
        })

    return pd.DataFrame(records)

def generate_default_suite(output_dir):
    """توليد الحزم القياسية الأربعة المباشرة لمصفاة بانياس"""
    print("\n=================================================================")
    print("🚀 بدء توليد حزم بيانات التوأم الرقمي لمصفاة بانياس (الوضع الافتراضي)...")
    print("=================================================================")

    # 1. تشغيل طبيعي مستقر
    df_norm = simulate_refinery_cdu(total_hours=100.0, samples_per_hour=2, scenario="normal")
    p_norm = os.path.join(output_dir, "refinery_cdu_normal.csv")
    df_norm.to_csv(p_norm, index=False)
    print(f"✔️ [1/4] تم حفظ بيانات التشغيل المستقر ({len(df_norm)} صف): {p_norm}")

    # 2. تكلس وترسب حاد في الخط A
    df_foul = simulate_refinery_cdu(total_hours=100.0, samples_per_hour=2, scenario="severe_fouling")
    p_foul = os.path.join(output_dir, "refinery_severe_fouling_train_a.csv")
    df_foul.to_csv(p_foul, index=False)
    print(f"✔️ [2/4] تم حفظ بيانات تكلس الخط A ({len(df_foul)} صف): {p_foul}")

    # 3. ارتفاع حرارة جدار أنابيب الفرن
    df_overheat = simulate_refinery_cdu(total_hours=100.0, samples_per_hour=2, scenario="tube_overheating")
    p_over = os.path.join(output_dir, "refinery_furnace_tube_overheating.csv")
    df_overheat.to_csv(p_over, index=False)
    print(f"✔️ [3/4] تم حفظ بيانات حرارة أنابيب الفرن ({len(df_overheat)} صف): {p_over}")

    # 4. متسلسلة زمنية تدهورية شاملة لـ 30 يوماً
    df_timeseries = simulate_refinery_cdu(total_hours=720.0, samples_per_hour=1, scenario="timeseries_30days")
    p_time = os.path.join(output_dir, "refinery_fouling_timeseries_30days.csv")
    df_timeseries.to_csv(p_time, index=False)
    print(f"✔️ [4/4] تم حفظ متسلسلة التدهور للشهر الكامل (720 ساعة تشغيل): {p_time}")

    print("\n✅ اكتمل توليد حزم بيانات مصفاة بانياس بنجاح في مجلد generated_datasets!")

def main():
    parser = argparse.ArgumentParser(
        description="مولد بيانات مجمع التقطير الجوي لمصفاة بانياس (Refinery Digital Twin Generator)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--scenario',
        choices=['all', 'normal', 'severe_fouling', 'tube_overheating', 'timeseries'],
        default='all',
        help="السيناريو المطلوب:\n"
             " - all: توليد الحزم القياسية الأربعة (الافتراضي)\n"
             " - normal: تشغيل طبيعي مستقر\n"
             " - severe_fouling: تكلس حاد في الخط A\n"
             " - tube_overheating: ارتفاع حرارة أنابيب الفرن\n"
             " - timeseries: متسلسلة زمنية تدهورية طويلة"
    )
    parser.add_argument('--duration', type=float, default=None, help="المدة الزمنية المطلوبة للتوليد (مثلاً 7 للأيام أو 1 للأشهر)")
    parser.add_argument('--unit', choices=['hours', 'days', 'weeks', 'months'], default='days', help="وحدة الوقت (الافتراضي: days)")
    parser.add_argument('--samples-per-hour', type=int, default=2, help="معدل العينات لكل ساعة (الافتراضي: 2، أي عينة كل نصف ساعة)")
    parser.add_argument('--output-dir', type=str, default=None, help="مجلد الحفظ المخصص")
    parser.add_argument('--output-name', type=str, default=None, help="اسم الملف المخصص")

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = args.output_dir if args.output_dir else os.path.join(base_dir, "generated_datasets")
    ensure_dir(output_dir)

    if args.scenario == 'all' and args.duration is None:
        generate_default_suite(output_dir)
        return

    duration_val = args.duration if args.duration else 7.0
    total_hours = convert_to_hours(duration_val, args.unit)
    scen = args.scenario if args.scenario != 'all' else 'timeseries_30days'

    print(f"\n⏳ جاري محاكاة مصفاة بانياس لسيناريو ({scen}) لمدة {duration_val} {args.unit} ({total_hours:.1f} ساعة تشغيل)...")
    df = simulate_refinery_cdu(total_hours=total_hours, samples_per_hour=args.samples_per_hour, scenario=scen)

    fname = args.output_name if args.output_name else f"refinery_{scen}_{int(duration_val)}_{args.unit}.csv"
    out_path = os.path.join(output_dir, fname)
    df.to_csv(out_path, index=False)
    print(f"✅ تم توليد وحفظ ملف بيانات مصفاة بانياس بنجاح ({len(df)} نقطة تشغيل): {out_path}")

if __name__ == "__main__":
    main()
