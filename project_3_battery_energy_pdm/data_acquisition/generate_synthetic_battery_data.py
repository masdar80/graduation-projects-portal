#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
محاكي ومولد بيانات بطاريات أيونات الليثيوم (Lithium-ion Battery Prognostics Simulator)
========================================================================================
المشروع الثالث: المنظومة التنبؤية لتقدير الحالة الصحية وتوقع العمر المتبقي (SOH & RUL)
               وحماية منظومات الطاقة من الهروب الحراري (Thermal Runaway)

الميزات:
- محاكاة كهروكيميائية وحرارية لخلايا الليثيوم 18650 / LFP / NMC.
- توليد منحنيات الشحن والتفريغ (CC-CV Charging & Dynamic Discharge).
- نمذجة تدهور السعة (Capacity Fade) وازدياد المقاومة الداخلية (Internal Resistance).
- نمذجة مؤشرات ما قبل الهروب الحراري (Thermal Runaway Early Precursors & ISC).
- دعم التوليد الفوري للحزم الافتراضية، أو التوليد المخصص لأي مدة (أيام، أسابيع، أشهر، دورات).

الاستخدام:
    python generate_synthetic_battery_data.py                           # التوليد الافتراضي
    python generate_synthetic_battery_data.py --duration 7 --unit days # توليد أسبوع كامل
    python generate_synthetic_battery_data.py --scenario rul --duration 600 --unit cycles
========================================================================================
"""

import os
import sys
import math
import random
import csv
import argparse

# مسار مجلد الإخراج الافتراضي للبيانات المولدة
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "generated_datasets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# الثوابت التصميمية لخلية الليثيوم القياسية 18650 NMC
NOMINAL_CAPACITY_AH = 2.50       # السعة الاسمية للخلية الجديدة
NOMINAL_VOLTAGE_V = 3.70         # الجهد الاسمي
MAX_CHARGE_VOLTAGE_V = 4.20      # جهد اكتمال الشحن
CUTOFF_DISCHARGE_VOLTAGE_V = 2.80# جهد قطع التفريغ
FRESH_RESISTANCE_OHM = 0.024     # المقاومة الداخلية لخلية جديدة (24 ميكرو أوم)
AMBIENT_TEMP_DEFAULT_C = 25.0    # درجة حرارة الغرفة الافتراضية


def generate_cycle_waveform(scenario='normal', num_samples=180, cycle_idx=10):
    """
    توليد بيانات لحظية تفصيلية لدورة شحن وتفريغ واحدة (Waveform)
    تضم: الزمن، الجهد، التيار، الحرارة، الشحنة المتراكمة، ومؤشر الحالة.
    """
    records = []
    
    # تحديد معاملات الحالة الصحية بناءً على السيناريو
    if scenario == 'normal':
        soh = 0.985 - (cycle_idx * 0.0003)
        actual_capacity = NOMINAL_CAPACITY_AH * soh
        internal_resistance = FRESH_RESISTANCE_OHM + (cycle_idx * 0.00003)
        base_status = "HEALTHY_CELL"
        has_thermal_anomaly = False
    elif scenario == 'aged':
        soh = 0.815 - (cycle_idx * 0.0005)
        actual_capacity = NOMINAL_CAPACITY_AH * soh
        internal_resistance = FRESH_RESISTANCE_OHM * 2.8
        base_status = "AGED_CELL_WARNING"
        has_thermal_anomaly = False
    elif scenario == 'thermal_runaway':
        soh = 0.74
        actual_capacity = NOMINAL_CAPACITY_AH * soh
        internal_resistance = FRESH_RESISTANCE_OHM * 4.2
        base_status = "CRITICAL_THERMAL_RUNAWAY_PRECURSOR"
        has_thermal_anomaly = True
    else:
        soh = 0.95
        actual_capacity = NOMINAL_CAPACITY_AH * soh
        internal_resistance = FRESH_RESISTANCE_OHM
        base_status = "NORMAL"
        has_thermal_anomaly = False

    time_sec = 0.0
    cell_temp = AMBIENT_TEMP_DEFAULT_C + random.uniform(-0.5, 0.8)
    cumulative_ah = 0.0
    
    # 1. مرحلة الشحن بتيار مستمر (CC Phase) - ثلث المدة
    cc_samples = num_samples // 3
    # 2. مرحلة الشحن بجهد ثابت (CV Phase) - سدس المدة
    cv_samples = num_samples // 6
    # 3. مرحلة الراحة (Rest Phase)
    rest_samples = num_samples // 6
    # 4. مرحلة التفريغ بحمل (Discharge Phase)
    discharge_samples = num_samples - (cc_samples + cv_samples + rest_samples)

    current_voltage = 3.20 if scenario != 'aged' else 3.05

    # تنفيذ مرحلة CC Charge
    for i in range(cc_samples):
        time_sec += 10.0
        current = 2.50 + random.uniform(-0.02, 0.02) # 1C Charge
        current_voltage += (MAX_CHARGE_VOLTAGE_V - current_voltage) * 0.04 + random.uniform(-0.003, 0.003)
        if current_voltage > MAX_CHARGE_VOLTAGE_V:
            current_voltage = MAX_CHARGE_VOLTAGE_V
            
        heat_gen = (current ** 2) * internal_resistance * 0.4
        cell_temp += heat_gen * 0.05 + random.uniform(-0.05, 0.1)
        cumulative_ah += (current * 10.0 / 3600.0)

        records.append({
            "timestamp_sec": round(time_sec, 1),
            "step_type": "CC_CHARGE",
            "voltage_v": round(current_voltage, 4),
            "current_a": round(current, 3),
            "cell_temperature_c": round(cell_temp, 2),
            "internal_resistance_ohm": round(internal_resistance, 5),
            "accumulated_capacity_ah": round(cumulative_ah, 4),
            "soh_percent": round(soh * 100.0, 2),
            "status": base_status
        })

    # مرحلة CV Charge
    for i in range(cv_samples):
        time_sec += 10.0
        current = max(0.12, 2.50 * math.exp(-i * 0.15)) + random.uniform(-0.01, 0.01)
        current_voltage = MAX_CHARGE_VOLTAGE_V + random.uniform(-0.002, 0.002)
        cell_temp += ((current ** 2) * internal_resistance * 0.2 - (cell_temp - AMBIENT_TEMP_DEFAULT_C) * 0.03)
        cumulative_ah += (current * 10.0 / 3600.0)

        records.append({
            "timestamp_sec": round(time_sec, 1),
            "step_type": "CV_CHARGE",
            "voltage_v": round(current_voltage, 4),
            "current_a": round(current, 3),
            "cell_temperature_c": round(cell_temp, 2),
            "internal_resistance_ohm": round(internal_resistance, 5),
            "accumulated_capacity_ah": round(cumulative_ah, 4),
            "soh_percent": round(soh * 100.0, 2),
            "status": base_status
        })

    # مرحلة الراحة Rest
    for i in range(rest_samples):
        time_sec += 10.0
        current = 0.0
        current_voltage -= 0.004 + random.uniform(0.0, 0.002) # الاسترخاء
        cell_temp -= (cell_temp - AMBIENT_TEMP_DEFAULT_C) * 0.05 + random.uniform(-0.02, 0.02)

        records.append({
            "timestamp_sec": round(time_sec, 1),
            "step_type": "REST",
            "voltage_v": round(current_voltage, 4),
            "current_a": round(current, 3),
            "cell_temperature_c": round(cell_temp, 2),
            "internal_resistance_ohm": round(internal_resistance, 5),
            "accumulated_capacity_ah": round(cumulative_ah, 4),
            "soh_percent": round(soh * 100.0, 2),
            "status": base_status
        })

    # مرحلة التفريغ Discharge
    for i in range(discharge_samples):
        time_sec += 10.0
        current = -2.50 + random.uniform(-0.03, 0.03) # 1C Discharge
        progress = i / max(1, discharge_samples)
        
        # هبوط الجهد غير الخطي
        base_v = 4.10 - (1.10 * progress) - (0.25 * (progress ** 3))
        current_voltage = base_v - (abs(current) * internal_resistance) + random.uniform(-0.005, 0.005)
        
        if has_thermal_anomaly and i > discharge_samples // 2:
            # محاكاة القصر الداخلي والشذوذ الحراري السابق للاشتعال
            current_voltage -= 0.35 + (i * 0.015)
            cell_temp += 1.45 + (i * 0.08) # ارتفاع حراري حرج متسارع
            status = "CRITICAL_RUNAWAY_TEMPERATURE_EXCEEDED"
        else:
            cell_temp += (abs(current) ** 2) * internal_resistance * 0.6 + random.uniform(-0.03, 0.05)
            status = base_status

        current_voltage = max(CUTOFF_DISCHARGE_VOLTAGE_V - 0.2, current_voltage)
        cumulative_ah += (current * 10.0 / 3600.0)

        records.append({
            "timestamp_sec": round(time_sec, 1),
            "step_type": "DISCHARGE",
            "voltage_v": round(current_voltage, 4),
            "current_a": round(current, 3),
            "cell_temperature_c": round(cell_temp, 2),
            "internal_resistance_ohm": round(internal_resistance, 5),
            "accumulated_capacity_ah": round(cumulative_ah, 4),
            "soh_percent": round(soh * 100.0, 2),
            "status": status
        })

    return records


def generate_rul_cycles_dataset(total_cycles=500):
    """
    توليد متسلسلة تدهور شاملة تغطي دورات حياة الخلية حتى نهاية العمر EOL
    (500 دورة شحن وتفريغ لمراقبة السعة والمقاومة والعمر المتبقي RUL).
    """
    records = []
    current_capacity = NOMINAL_CAPACITY_AH
    current_resistance = FRESH_RESISTANCE_OHM
    
    # حد نهاية العمر الافتراضي (End of Life - 80% SOH)
    eol_capacity = NOMINAL_CAPACITY_AH * 0.80

    for c in range(1, total_cycles + 1):
        # تدهور غير خطي: تآكل SEI الأولي سريع ثم خطي ثم تسارع عند التقادم
        sei_growth = 0.00075 / (math.sqrt(c) if c > 1 else 1.0)
        linear_fade = 0.00065
        knee_acceleration = 0.0012 if c > 380 else 0.0
        
        capacity_loss = sei_growth + linear_fade + knee_acceleration + random.uniform(-0.0002, 0.0002)
        current_capacity = max(1.50, current_capacity - capacity_loss)
        
        # ازدياد المقاومة الداخلية
        current_resistance += 0.000085 + random.uniform(-0.00001, 0.00002)
        
        # حساب SOH و RUL
        soh_pct = (current_capacity / NOMINAL_CAPACITY_AH) * 100.0
        
        # تقدير الدورات المتبقية حتى EOL
        if current_capacity > eol_capacity:
            remaining_cycles = int((current_capacity - eol_capacity) / 0.0011)
            remaining_cycles = max(0, remaining_cycles)
        else:
            remaining_cycles = 0

        # أقصى حرارة سجلت أثناء الدورة
        max_temp_c = 28.5 + ((current_resistance / FRESH_RESISTANCE_OHM) * 3.8) + random.uniform(-0.6, 0.8)
        
        # زمن اكتمال الشحن بالجهد الثابت CV
        cv_duration_min = 22.0 + (55.0 * (1.0 - (soh_pct / 100.0))) + random.uniform(-1.2, 1.5)

        # الحالة التشغيلية
        if soh_pct >= 90.0:
            status = "OPTIMAL_HEALTH"
        elif soh_pct >= 80.0:
            status = "HEALTHY_DEGRADATION"
        elif soh_pct >= 75.0:
            status = "WARNING_EOL_APPROACHING"
        else:
            status = "CRITICAL_REPLACE_CELL"

        records.append({
            "cycle_number": c,
            "measured_capacity_ah": round(current_capacity, 4),
            "soh_percent": round(soh_pct, 2),
            "internal_resistance_ohm": round(current_resistance, 5),
            "max_cycle_temperature_c": round(max_temp_c, 2),
            "cv_charge_duration_min": round(cv_duration_min, 1),
            "rul_cycles_remaining": remaining_cycles,
            "battery_health_status": status
        })

    return records


def generate_timeseries_monitoring(duration_val, unit='days'):
    """
    توليد سلسلة زمنية لمراقبة حزمة بطاريات طاقة شمسية أو مركبة كهربائية
    بشكل مستمر ساعة بساعة.
    """
    # تحويل المدة إلى ساعات
    if unit in ['hour', 'hours']:
        total_hours = duration_val
    elif unit in ['day', 'days']:
        total_hours = duration_val * 24
    elif unit in ['week', 'weeks']:
        total_hours = duration_val * 24 * 7
    elif unit in ['month', 'months']:
        total_hours = duration_val * 24 * 30
    else:
        total_hours = 24 * 7 # افتراضي أسبوع

    records = []
    soh_pct = 98.5
    capacity = NOMINAL_CAPACITY_AH * (soh_pct / 100.0)
    resistance = FRESH_RESISTANCE_OHM

    for h in range(1, total_hours + 1):
        # دورة اليوم (حرارة الجو وساعات النهار الشمسية)
        hour_of_day = h % 24
        ambient_temp = 22.0 + 8.0 * math.sin((hour_of_day - 8) * math.pi / 12.0) + random.uniform(-0.5, 0.5)
        
        # طبيعة الحمل: شحن نهاري وتفريغ مسائي
        if 8 <= hour_of_day <= 16:
            # شحن شمسي
            pack_current = random.uniform(8.0, 15.0)
            pack_voltage = 52.4 + random.uniform(-0.4, 0.6) # حزمة 48V
            op_mode = "SOLAR_CHARGING"
        elif 18 <= hour_of_day <= 23:
            # استهلاك مسائي ذروة
            pack_current = -random.uniform(10.0, 20.0)
            pack_voltage = 48.2 - random.uniform(0.0, 1.2)
            op_mode = "PEAK_DISCHARGING"
        else:
            # حمل خفيف ليلاً
            pack_current = -random.uniform(1.0, 3.5)
            pack_voltage = 49.5 + random.uniform(-0.2, 0.2)
            op_mode = "IDLE_STANDBY"

        cell_temp = ambient_temp + (abs(pack_current) * 0.35) + random.uniform(-0.3, 0.4)
        
        # تدهور طفيف جداً كل 100 ساعة
        soh_pct -= (0.0035 + random.uniform(0.0, 0.001))
        resistance += 0.000002

        rul_days = int((soh_pct - 80.0) / 0.02) if soh_pct > 80.0 else 0

        status = "NORMAL_OPERATION"
        if cell_temp > 48.0:
            status = "THERMAL_WARNING"
        elif soh_pct < 80.0:
            status = "MAINTENANCE_REQUIRED"

        records.append({
            "monitoring_hour": h,
            "day_number": round(h / 24.0, 2),
            "operation_mode": op_mode,
            "pack_voltage_v": round(pack_voltage, 2),
            "pack_current_a": round(pack_current, 2),
            "ambient_temp_c": round(ambient_temp, 1),
            "max_cell_temp_c": round(cell_temp, 2),
            "pack_soh_percent": round(soh_pct, 3),
            "cell_internal_resistance_ohm": round(resistance, 6),
            "predicted_rul_days": rul_days,
            "system_health_status": status
        })

    return records


def save_csv(filename, data):
    """حفظ البيانات في ملف CSV"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not data:
        print(f"⚠️ تحذير: لا توجد بيانات لحفظها في {filename}")
        return filepath
        
    keys = data[0].keys()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
        
    print(f"✔️ تم حفظ الملف بنجاح: {filename} ({len(data)} سجلاً)")
    return filepath


def run_default_suite():
    """توليد الحزمة القياسية الخماسية الجاهزة فوراً"""
    print("=" * 70)
    print("⚡ بدء توليد الحزم القياسية الخماسية لبطاريات الليثيوم (Project 3)...")
    print("=" * 70)

    # 1. خلية سليمة جديدة
    data_fresh = generate_cycle_waveform(scenario='normal', num_samples=180, cycle_idx=15)
    save_csv("synthetic_battery_fresh_cell.csv", data_fresh)

    # 2. خلية متقادمة
    data_aged = generate_cycle_waveform(scenario='aged', num_samples=180, cycle_idx=250)
    save_csv("synthetic_battery_aged_cell.csv", data_aged)

    # 3. تحذير هروب حراري وقصر داخلي
    data_thermal = generate_cycle_waveform(scenario='thermal_runaway', num_samples=180, cycle_idx=350)
    save_csv("synthetic_battery_thermal_runaway_warning.csv", data_thermal)

    # 4. متسلسلة تدهور كاملة لـ 500 دورة
    data_rul = generate_rul_cycles_dataset(total_cycles=500)
    save_csv("synthetic_battery_rul_500cycles.csv", data_rul)

    # 5. متسلسلة أسبوع كامل (7 أيام = 168 ساعة)
    data_7days = generate_timeseries_monitoring(7, unit='days')
    save_csv("synthetic_battery_timeseries_7days.csv", data_7days)

    print("=" * 70)
    print("🎉 اكتمل بنجاح توليد الملفات الـ 5 القياسية في مجلد generated_datasets/")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="محاكي ومولد بيانات بطاريات أيونات الليثيوم (Predictive BMS Simulator)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--duration", type=int, default=None, help="المدة الزمنية المطلوب محاكاتها (مثال: 7 أو 30 أو 500)")
    parser.add_argument("--unit", type=str, default="days", choices=["hours", "days", "weeks", "months", "cycles"], help="وحدة المدة الزمنية")
    parser.add_argument("--scenario", type=str, default="default", choices=["default", "normal", "aged", "thermal_runaway", "rul", "timeseries"], help="نوع السيناريو المطلوب")
    parser.add_argument("--output", type=str, default=None, help="اسم ملف الخرج المخصص (CSV)")

    args = parser.parse_args()

    # إذا تم التشغيل بدون معاملات، ننفذ الحزمة الافتراضية
    if args.duration is None and args.scenario == "default":
        run_default_suite()
        return

    # التوليد المخصص حسب الطلب
    print(f"🚀 بدء التوليد المخصص: سيناريو [{args.scenario}] بمدة [{args.duration} {args.unit}]...")

    if args.unit == "cycles" or args.scenario == "rul":
        cycles = args.duration if args.duration else 500
        data = generate_rul_cycles_dataset(total_cycles=cycles)
        filename = args.output if args.output else f"synthetic_battery_rul_{cycles}cycles.csv"
    elif args.scenario in ["normal", "aged", "thermal_runaway"]:
        samples = (args.duration * 30) if args.duration else 180
        data = generate_cycle_waveform(scenario=args.scenario, num_samples=samples)
        filename = args.output if args.output else f"synthetic_battery_{args.scenario}_custom.csv"
    else: # timeseries
        dur = args.duration if args.duration else 7
        data = generate_timeseries_monitoring(dur, unit=args.unit)
        filename = args.output if args.output else f"synthetic_battery_{dur}_{args.unit}_custom.csv"

    out_path = save_csv(filename, data)
    print(f"✅ تم الانتهاء بنجاح وحفظ الملف في: {out_path}")


if __name__ == "__main__":
    main()
