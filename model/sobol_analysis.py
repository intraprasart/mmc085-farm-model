# -*- coding: utf-8 -*-
"""การวิเคราะห์ความไวเชิงโลกด้วยดัชนีโซบอล (Sobol' variance-based sensitivity analysis)

   ตอบคำถามว่า "ความไม่แน่นอนของผลลัพธ์มาจากพารามิเตอร์ตัวไหนบ้าง และมากแค่ไหน"
   ต่างจากการรบกวนทีละตัว (one-at-a-time) ตรงที่กวาดทั้งปริภูมิพารามิเตอร์พร้อมกัน
   จึงจับผลของอันตรกิริยาระหว่างตัวแปรได้ด้วย

   ดัชนีที่รายงาน
     S_i   ดัชนีลำดับที่หนึ่ง  สัดส่วนความแปรปรวนที่อธิบายได้ด้วยพารามิเตอร์ i เพียงตัวเดียว
     S_Ti  ดัชนีรวม           สัดส่วนความแปรปรวนที่หายไปถ้าตรึงพารามิเตอร์ i ไว้ (รวมอันตรกิริยา)
     S_Ti - S_i  คือส่วนที่มาจากอันตรกิริยากับตัวอื่น

   ข้อสมมติของการสุ่มซึ่งต้องแถลงคู่กับผลเสมอ เพราะดัชนีโซบอลขึ้นกับการแจกแจงของตัวป้อน
     * พารามิเตอร์ทั้งแปดเป็นอิสระต่อกัน
     * แจกแจงแบบสม่ำเสมอ (uniform) ภายในช่วงของตนเอง
     * k_p เป็นตัวเดียวที่ช่วงมาจากเอกสาร (0.70-0.80 ตาม FAO-56) และขยายขอบบนเป็น 0.85 เอง
       เพื่อทดสอบเลยขอบที่เอกสารระบุ อีกเจ็ดตัวเป็นช่วงที่ทีมกำหนดขึ้นรอบค่าฐาน

   หมายเหตุการตีความ: ผลรวม S_Ti ที่มากกว่า 1 บ่งชี้ว่ามีอันตรกิริยา แต่ส่วนที่เกิน 1
   ไม่ใช่สัดส่วนความแปรปรวนที่มาจากอันตรกิริยาโดยตรง เพราะพจน์อันตรกิริยาพจน์เดียว
   ถูกนับซ้ำใน S_Ti ของพารามิเตอร์หลายตัว

   วิธีสุ่ม: ลำดับโซบอลแบบ scramble (scipy.stats.qmc) ตามแผนของ Saltelli
   ตัวประมาณ: Saltelli (2010) สำหรับ S_i และ Jansen (1999) สำหรับ S_Ti
   จำนวนการเรียกแบบจำลอง = N x (k + 2)

   วิธีรัน: python sobol_analysis.py [N]      (ค่าตั้งต้น N = 1024)
"""
import json
import sys
import numpy as np
from scipy.stats import qmc

import farm_model as M
from farm_model import simulate, SCEN10

# ---------------------------------------------------------------- แบบที่วิเคราะห์
J = json.load(open("out/v3_results.json"))
REC = J["recommended"]
AREAS = tuple(REC["areas"])
N_CK, RHO = int(REC["n_ck"]), REC["rho"]
THR, THG = REC["th"]

# ---------------------------------------------------------------- พารามิเตอร์และช่วง
# ช่วงเลือกจากความไม่แน่นอนที่อ้างอิงได้จริง มิใช่การรบกวนแบบสุ่มรอบค่ากลาง
PARAMS = [
    ("k_p",       0.70, 0.85, "สัมประสิทธิ์ถาดวัดการระเหย (FAO-56 ช่วงมาตรฐาน)"),
    ("c",         0.15, 0.35, "สัมประสิทธิ์น้ำท่าของฝนส่วนเกิน"),
    ("r",         0.85, 1.15, "ตัวคูณปริมาณฝนทุกเดือน"),
    ("y_R",       0.36, 0.56, "ผลผลิตข้าวเปลือก กก./ตร.ม. (~580-900 กก./ไร่)"),
    ("w_R",     120.0, 160.0, "ความต้องการน้ำนาเปียกสลับแห้ง ล./ตร.ม./เดือน"),
    ("y_V",      64.0,  96.0, "รายได้พืชผัก บาท/ตร.ม./รอบ (+-20% ของตารางโจทย์)"),
    # ปรับเฉพาะค่าเมื่อยุ้งเบิกได้ (AC_HI) ส่วน AC_LO = 0.10 เมื่อยุ้งไม่พอ ตรึงไว้
    ("alpha_C_hi", 0.15,  0.40, "ส่วนลดค่าอาหารไก่เมื่อยุ้งข้าวเบิกได้ (ค่าเมื่อยุ้งไม่พอตรึงที่ 0.10)"),
    # ปรับเฉพาะพจน์ฐาน AF_BASE ส่วนความชัน AF_SLOPE = 0.35 ตรึงไว้
    ("alpha_F_0",  0.05,  0.25, "ส่วนลดพื้นฐานค่าอาหารปลา (ความชัน 0.35 ตรึงไว้)"),
]
NAMES = [p[0] for p in PARAMS]
LOW = np.array([p[1] for p in PARAMS])
HIGH = np.array([p[2] for p in PARAMS])
K = len(PARAMS)

_BASE = dict(KP=M.KP, RUNOFF_C=M.RUNOFF_C, RAIN_N=list(M.RAIN_N), RAIN_D=list(M.RAIN_D),
             Y_RICE=M.Y_RICE, P_PADDY=M.P_PADDY, VEG_REV=M.VEG["rev"],
             AC_HI=M.AC_HI, AF_BASE=M.AF_BASE)


def evaluate(x):
    """คืนผลลัพธ์สามตัวของแบบแนะนำ ภายใต้ค่าพารามิเตอร์ชุด x"""
    kp, c, r, yR, wR, yV, aC, aF = x
    M.KP, M.RUNOFF_C = kp, c
    M.RAIN_N[:] = [v * r for v in _BASE["RAIN_N"]]
    M.RAIN_D[:] = [v * r for v in _BASE["RAIN_D"]]
    M.Y_RICE = yR
    M.P_PADDY = 45.0 / yR          # ราคาโดยนัยผูกกับรายได้ 45 บ./ตร.ม. ที่โจทย์กำหนด
    M.VEG["rev"] = yV
    M.AC_HI, M.AF_BASE = aC, aF
    try:
        n_survive, worst_v, w_norm, w_dd = 0, 1e18, np.nan, np.nan
        for sc in SCEN10:
            s = simulate(*AREAS, N_CK, RHO, THR, THG, drought=sc, w_rice=wR)
            if s["feasible"]:
                n_survive += 1
            if sc:
                worst_v = min(worst_v, s["minV"])
            else:
                w_norm = s["wealth"]
            if sc == (0, 1):
                w_dd = s["wealth"]
    finally:
        M.KP, M.RUNOFF_C = _BASE["KP"], _BASE["RUNOFF_C"]
        M.RAIN_N[:], M.RAIN_D[:] = _BASE["RAIN_N"], _BASE["RAIN_D"]
        M.Y_RICE, M.P_PADDY = _BASE["Y_RICE"], _BASE["P_PADDY"]
        M.VEG["rev"] = _BASE["VEG_REV"]
        M.AC_HI, M.AF_BASE = _BASE["AC_HI"], _BASE["AF_BASE"]
    return w_norm, worst_v, float(n_survive)


OUTPUTS = [("W60 ปีปกติ (บาท)", 0), ("กันชนน้ำ (ลบ.ม.)", 1), ("จำนวนฉากที่รอด (0-10)", 2)]


def sobol_indices(fA, fB, fAB):
    """Saltelli (2010) สำหรับ S_i และ Jansen (1999) สำหรับ S_Ti"""
    var = np.var(np.concatenate([fA, fB]), ddof=1)
    if var <= 0:
        return np.zeros(K), np.zeros(K)
    Si = np.array([np.mean(fB * (fAB[:, i] - fA)) / var for i in range(K)])
    STi = np.array([np.mean((fA - fAB[:, i]) ** 2) / (2 * var) for i in range(K)])
    return Si, STi


def bootstrap(fA, fB, fAB, n_boot=500, seed=1):
    rng = np.random.default_rng(seed)
    n = len(fA)
    out_s, out_t = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        s, t = sobol_indices(fA[idx], fB[idx], fAB[idx])
        out_s.append(s); out_t.append(t)
    return np.array(out_s), np.array(out_t)


def main(n_base):
    sampler = qmc.Sobol(d=2 * K, scramble=True, seed=20260830)
    base = sampler.random(n_base)                     # จุดในลูกบาศก์หนึ่งหน่วย
    A = LOW + base[:, :K] * (HIGH - LOW)
    B = LOW + base[:, K:] * (HIGH - LOW)

    total = n_base * (K + 2)
    print(f"Sobol' sensitivity analysis | k = {K} พารามิเตอร์ | N = {n_base:,} | "
          f"เรียกแบบจำลอง {total:,} ครั้ง ({total * 10:,} การจำลอง 60 เดือน)")
    print("แบบที่วิเคราะห์: " + " ".join(f"{a:,.0f}" for a in AREAS) +
          f" ตร.ม. | ไก่ {N_CK} | ปลา {RHO:.0f} ตัว/ตร.ม. | เกณฑ์ {THR*3:.2f} ม.\n")

    def run(mat, tag):
        res = np.empty((len(mat), 3))
        for i, x in enumerate(mat):
            res[i] = evaluate(x)
        print(f"  ประเมิน {tag} เสร็จ ({len(mat):,} จุด)")
        return res

    rA, rB = run(A, "A"), run(B, "B")
    rAB = np.empty((K, n_base, 3))
    for i in range(K):
        Mi = A.copy()
        Mi[:, i] = B[:, i]
        rAB[i] = run(Mi, f"AB[{NAMES[i]}]")

    out = {"n_base": n_base, "n_eval": total, "params": [
        dict(name=p[0], low=p[1], high=p[2], note=p[3]) for p in PARAMS]}
    for label, col in OUTPUTS:
        fA, fB = rA[:, col], rB[:, col]
        fAB = np.column_stack([rAB[i][:, col] for i in range(K)])
        Si, STi = sobol_indices(fA, fB, fAB)
        bs, bt = bootstrap(fA, fB, fAB)
        lo_s, hi_s = np.percentile(bs, [5, 95], axis=0)
        lo_t, hi_t = np.percentile(bt, [5, 95], axis=0)
        allf = np.concatenate([fA, fB])
        print(f"\n=== ผลลัพธ์: {label} ===")
        print(f"  ค่าเฉลี่ย {np.mean(allf):,.1f} | ส่วนเบี่ยงเบนมาตรฐาน {np.std(allf, ddof=1):,.1f} "
              f"| ต่ำสุด {np.min(allf):,.1f} | สูงสุด {np.max(allf):,.1f}")
        print(f"  {'พารามิเตอร์':>10} {'S_i':>8} {'ช่วง 90%':>16} {'S_Ti':>8} {'ช่วง 90%':>16} {'อันตรกิริยา':>11}")
        order = np.argsort(-STi)
        for i in order:
            print(f"  {NAMES[i]:>10} {Si[i]:8.3f} [{lo_s[i]:6.3f},{hi_s[i]:6.3f}] "
                  f"{STi[i]:8.3f} [{lo_t[i]:6.3f},{hi_t[i]:6.3f}] {STi[i]-Si[i]:11.3f}")
        print(f"  ผลรวม S_i = {Si.sum():.3f}   ผลรวม S_Ti = {STi.sum():.3f} "
              f"(ส่วนที่เกิน 1 คือสัดส่วนของอันตรกิริยา)")
        out[label] = dict(Si=Si.tolist(), STi=STi.tolist(),
                          Si_lo=lo_s.tolist(), Si_hi=hi_s.tolist(),
                          STi_lo=lo_t.tolist(), STi_hi=hi_t.tolist(),
                          mean=float(np.mean(allf)), std=float(np.std(allf, ddof=1)),
                          min=float(np.min(allf)), max=float(np.max(allf)),
                          frac_survive_all=float(np.mean(allf >= 10.0)) if col == 2 else None)
    with open("out/sobol_results.json", "w") as fp:
        json.dump(out, fp, ensure_ascii=False)
    print("\nบันทึกผลลง out/sobol_results.json แล้ว")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1024)
