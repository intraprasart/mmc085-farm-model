# -*- coding: utf-8 -*-
"""
แบบจำลองการจัดสรรพื้นที่เกษตรยั่งยืนรับมือวิกฤตเอลนีโญ
=======================================================
โจทย์รอบชิงชนะเลิศ MMC 2569 (ทีม MMC085)
ที่ดิน 4 ไร่ (6,400 ตร.ม.) ทุนตั้งต้น 200,000 บาท ครัวเรือน 4 คน ระยะเวลา 5 ปี (60 เดือน)

แบบจำลองเป็นระบบพลวัตรายเดือนที่มีตัวแปรสถานะสามตัวเดินไปพร้อมกัน
    V_t  น้ำในสระ (ลิตร)
    M_t  เงินสด (บาท)
    S_t  ยุ้งข้าว (กก. ข้าวเปลือก)

หลักการที่ใช้ตลอดแบบจำลอง
    * ต้นทุนที่อยู่อาศัยจ่ายจริง 500 บ./ตร.ม. ทุกตารางเมตรของโซนตามตารางโจทย์
      A_H = A_HOUSE_MIN + COOP_M2 * n  (บ้าน 80 ตร.ม. + เล้าไก่ 0.5 ตร.ม./ตัว)
      จัดสรรที่ดินครั้งเดียวที่ t=0 แต่ก่อสร้างเป็นเฟส ค่าเล้าจ่ายเมื่อกฎทบทวนประจำปีอนุมัติซื้อไก่
    * น้ำครัวเรือนคิดตามจำนวนคน 12,800 ล./เดือน ไม่ผูกกับขนาดโซน
    * กติกา "กินก่อน เหลือจึงขาย" ใช้กับข้าว ไข่ และปลา
    * ค่าคงตัวที่มีช่วงความไม่แน่นอนเลือกขอบที่เป็นคุณต่อปริมาณน้ำ (k_p=0.70, c=0.30)
    * สมดุลน้ำรักษาการอนุรักษ์มวล ฝนที่ตกบนแปลงถูกใช้ครั้งเดียว คือให้พืชใช้ก่อน
      แล้วส่วนเกินจึงไหลลงสระตามสัมประสิทธิ์น้ำท่า c ไม่นับซ้ำทั้งสองทาง

ระดับของแบบจำลองเลือกได้จากอาร์กิวเมนต์ของ simulate()
    thR=thG=0 และ w_rice=180  ->  M1  การจัดสรรคงที่ พฤติกรรมคงที่
    thR,thG>0 และ w_rice=135  ->  M2  เกณฑ์ระดับน้ำ + นาเปียกสลับแห้ง
    เพิ่ม n_ck, rho           ->  M3  ไก่ไข่ ปลานิล และเกษตรหมุนเวียน

พารามิเตอร์ทุกตัวเป็นค่าตัวแทนจากแหล่งอ้างอิงที่ระบุไว้ในภาคผนวก ก ของรายงาน
ก่อนนำไปใช้กับพื้นที่จริงควรตรวจสอบและปรับให้ตรงกับข้อมูลท้องถิ่น
"""

# ---------------- ข้อมูลโจทย์ (เรียงปีจำลอง พ.ค. ... เม.ย.) ----------------
RAIN_N = [150, 180, 200, 250, 300, 200, 80, 20, 20, 30, 50, 80]
RAIN_D = [40, 50, 60, 50, 80, 40, 80, 20, 20, 30, 50, 80]      # แล้ง พ.ค.-ต.ค.
EVAP_N = [150, 140, 140, 130, 120, 130, 130, 120, 120, 140, 160, 170]
EVAP_D = [180, 170, 170, 180, 160, 150, 130, 120, 120, 140, 160, 170]

TOTAL, BUDGET, DEPTH = 6400.0, 200_000.0, 3.0
KP, RUNOFF_C = 0.70, 0.30
# สัมประสิทธิ์เกษตรหมุนเวียน แยกออกมาเป็นค่าคงตัวเพื่อให้การวิเคราะห์ความไวปรับได้
AC_HI, AC_LO = 0.30, 0.10        # ส่วนลดค่าอาหารไก่ เมื่อยุ้งเบิกได้ / เมื่อเบิกไม่ได้
AF_BASE, AF_SLOPE = 0.15, 0.35   # ส่วนลดค่าอาหารปลา = AF_BASE + AF_SLOPE*min(1, n/100)
RICE = dict(cost=15.0, rev=45.0, water=180.0)   # M1 ใช้ 180; M2+ ใช้ W_RICE_AWD
FRUIT = dict(cost=40.0, rev=65.0, water=90.0)
VEG = dict(cost=25.0, rev=80.0, water=120.0)
W_RICE_AWD = 135.0
RICE_M, VEG_START = (2, 3, 4, 5), (0, 2, 4, 6)

# ---------------- ต้นทุนที่อยู่อาศัย ----------------
ZONE_RATE = 500.0          # บ./ตร.ม. ของโซนที่อยู่อาศัยและสิ่งปลูกสร้าง (ตามตาราง)
A_HOUSE_MIN = 80.0         # บ้านขั้นต่ำครอบครัว 4 คน (~20 ตร.ม./คน)
COOP_M2 = 0.5              # พื้นที่เล้า+ลาน ตร.ม./ไก่
HOUSE_WATER_MO = 12_800.0  # ล./เดือน คิดตามหัวคน ไม่ผูกกับ A_H

# ---------------- สัตว์ (M3) ----------------
CK_BIRD = 200.0            # พันธุ์ไก่สาว บ./ตัว (เล้าคิดตามอัตราตาราง 500 x 0.5 = 250 บ./ตัว)
CK_FEED, CK_REP, CK_WATER = 55.2, 90.0, 7.5
EGG_PER_CK_MO, P_EGG = 270.0 / 12, 3.5     # ผลิตไข่ 22.5 ฟอง/ตัว/เดือน; ราคา 3.5 บ./ฟอง
EGG_HH_MO = 120.0          # ครัวเรือนบริโภคไข่ 120 ฟอง/เดือน (4 คน x 1 ฟอง/วัน) - กินก่อน เหลือจึงขาย
EGG_PROT_MO = EGG_PER_CK_MO * 6.5 / 1000
FISH_START = (0, 6)
FG_COST, FISH_FEED, FISH_KG, P_FISH = 0.7, 9.0, 0.30, 60.0
FISH_HH_KG = 60.0          # ครัวเรือนเก็บปลาบริโภค 60 กก./รอบจับ (~30 กก./คน/ปี) - เหลือจึงขาย
H_STOCK, H_FLOOR, SALVAGE, FISH_PROT = 1.2, 0.5, 0.6, 0.18
CASH_BUFFER, FISH_BUFFER = 20_000.0, 10_000.0

# ---------------- โมดูลข้าวสะสม (บริโภค-สะสม-ขาย) ----------------
Y_RICE = 0.46              # ผลผลิตข้าวเปลือก กก./ตร.ม. (~740 กก./ไร่ นาน้ำเสริม; กรมการข้าว)
P_PADDY = 45.0 / Y_RICE    # ราคาโดยนัยของตาราง ~97.83 บ./กก. (ใช้ราคาเดียวทั้งขาย/ซื้อ กัน arbitrage)
HH_RICE_MO = 60.0          # ครัวเรือนบริโภคข้าวเปลือก กก./เดือน (4 คน; ข้าวสาร ~9.75 กก./คน/เดือน ที่อัตราสี 0.65)
CK_RICE_MO = 1.0           # ไก่เบิกข้าวเปลือก กก./ตัว/เดือน (~30% ของอาหาร 3.45 กก.) เมื่อยุ้งมีพอ
SELL_FRAC = 0.5            # ข้าวเหลือจากสำรองบริโภค: ขายครึ่ง เก็บครึ่ง
S_INIT = 6 * HH_RICE_MO    # เสบียงย้ายเข้า 6 เดือน (360 กก. นอกงบ) ให้ถึงเก็บเกี่ยวแรกพอดี

SINGLES = [(k,) for k in range(5)]
DOUBLES = [(0, 1), (1, 2), (2, 3), (3, 4)]
SCEN6 = [()] + SINGLES
SCEN10 = [()] + SINGLES + DOUBLES


def a_house(n_ck):
    return A_HOUSE_MIN + COOP_M2 * n_ck


def invest0(A_P, A_R, A_F, A_G):
    """เงินลงทุนเริ่มต้น (C4): สระ + บ้านขั้นต่ำ + เพาะปลูกรอบแรก (เล้าจ่ายทีหลังตามกฎ)"""
    return 30 * A_P + ZONE_RATE * A_HOUSE_MIN + RICE["cost"] * A_R + FRUIT["cost"] * A_F + VEG["cost"] * A_G


def simulate(A_P, A_R, A_F, A_G, n_ck=0, rho=0.0, thR=0.0, thG=0.0,
             drought=(), w_rice=W_RICE_AWD, n_years=5, start_offset=0, fruit_curve=None,
             fruit_gate=False):
    # fruit_curve: ตัวคูณรายได้ไม้ผลตามอายุ (list ยาว n_years); None = แบนราบตามตาราง
    # fruit_gate: ประตูไม้ผล — ปลูก ณ ก.ค. แรกที่ V >= 0.40 Vmax (เกณฑ์ 1.20 ม. เดียวกัน)
    #             ก่อนปลูก: ไม่มีต้นทุน/น้ำ/รายได้ไม้ผล; อายุนับจากปีที่ปลูก
    """จำลอง 60 เดือน; thR=thG=0 + w_rice=180 = M1; ประตู+AWD = M2; + n,rho = M3"""
    v_max = A_P * DEPTH * 1000.0
    V = 0.5 * v_max
    M = BUDGET - 30 * A_P - ZONE_RATE * A_HOUSE_MIN
    rice_on, veg_left = False, 0
    has_ck, ck_entry = False, None
    fruit_on, fruit_y0 = (not fruit_gate), 0      # ไม่มีประตู = ปลูกตั้งแต่ต้นตามเดิม
    fish_left, fish_rho = 0, 0.0
    S = S_INIT                                    # ยุ้งข้าว (กก. ข้าวเปลือก)
    ev = dict(skips=[], fish_ok=0, fish_skip=0, fish_emerg=0, protein=0.0,
              fish_active=[], fish_harv=[],
              rice_sold=0.0, rice_bought=0.0, buy_months=0)
    Vh, Mh, Sh, ok = [], [], [], True
    for t in range(n_years * 12):
        m, y = (t + start_offset) % 12, t // 12
        R = (RAIN_D if y in drought else RAIN_N)[m]
        E = (EVAP_D if y in drought else EVAP_N)[m]
        # ---- ต้นเดือน: กฎตัดสินใจ (ใช้ V,M ปลายเดือนก่อน)
        if m == 0:
            if n_ck > 0 and not has_ck:
                entry_cost = (CK_BIRD + ZONE_RATE * COOP_M2) * n_ck      # พันธุ์ + สร้างเล้าตามอัตราตาราง
                need_year = VEG["cost"] * A_G + FRUIT["cost"] * A_F + RICE["cost"] * A_R
                if M - entry_cost >= need_year + CASH_BUFFER:
                    has_ck, ck_entry = True, t
                    M -= entry_cost
            elif has_ck and t > ck_entry and (t - ck_entry) % 12 == 0:
                M -= CK_REP * n_ck
            if A_F > 0 and fruit_on and y > fruit_y0:
                M -= A_F * FRUIT["cost"]          # บำรุงรายปี (หลังปีปลูก)
            elif A_F > 0 and fruit_on and not fruit_gate and y == 0:
                M -= A_F * FRUIT["cost"]          # แบบเดิม: ปลูกทันที พ.ค. ปี 1
        if rho > 0 and m in FISH_START and fish_left == 0:
            if V >= H_STOCK * 1000.0 * A_P and M >= FG_COST * rho * A_P + FISH_BUFFER:
                fish_left, fish_rho = 6, rho
                M -= FG_COST * rho * A_P
            else:
                ev["fish_skip"] += 1
        if fruit_gate and not fruit_on and A_F > 0 and m == 2:
            if V >= 0.40 * v_max and M >= A_F * FRUIT["cost"]:
                fruit_on, fruit_y0 = True, y
                M -= A_F * FRUIT["cost"]          # ปลูกไม้ผลเมื่อประตูน้ำผ่าน
        if m == RICE_M[0]:
            rice_on = A_R > 0 and V >= thR * v_max and M >= A_R * RICE["cost"]
            if rice_on:
                M -= A_R * RICE["cost"]
            elif A_R > 0:
                ev["skips"].append((t, "นา"))
        if m in VEG_START:
            if A_G > 0 and V >= thG * v_max and M >= A_G * VEG["cost"]:
                veg_left = 2
                M -= A_G * VEG["cost"]
            elif A_G > 0:
                ev["skips"].append((t, "ผัก"))
        # ---- รายจ่ายสัตว์รายเดือน (เกษตรหมุนเวียน: ไก่เบิกข้าวจริงจากยุ้ง ถ้าพอ)
        if has_ck:
            draw = CK_RICE_MO * n_ck
            k_run = (5 - m) % 12 + 1              # เดือนที่คนต้องกินจนถึงเก็บเกี่ยวหน้า (รวมเดือนนี้)
            if S >= draw + k_run * HH_RICE_MO:    # ไก่เบิกได้เฉพาะส่วนเกินแท้จริง (คนก่อนเสมอ)
                S -= draw
                aC = AC_HI
            else:
                aC = AC_LO
            M -= CK_FEED * n_ck * (1 - aC)
        if fish_left > 0:
            aF = AF_BASE + (AF_SLOPE * min(1.0, n_ck / 100.0) if has_ck else 0.0)
            M -= (FISH_FEED / 6.0) * fish_rho * A_P * (1 - aF)
        # ---- สมดุลน้ำ
        need = A_R * max(0.0, w_rice - R) if (rice_on and m in RICE_M) else 0.0
        need += A_F * max(0.0, FRUIT["water"] - R) if fruit_on else 0.0
        need += A_G * max(0.0, VEG["water"] - R) if veg_left > 0 else 0.0
        need += HOUSE_WATER_MO
        need += CK_WATER * n_ck if has_ck else 0.0
        # น้ำท่าคิดจาก "ส่วนเกิน" ของฝนหลังหักที่พืชใช้ได้ในเดือนนั้นเท่านั้น
        # ฝนหนึ่งหน่วยจึงถูกใช้ครั้งเดียว ไม่นับซ้ำทั้งที่รากพืชและที่สระ
        # แปลงที่ไม่ได้เพาะปลูกในเดือนนั้นถือว่าฝนทั้งหมดเป็นส่วนเกิน
        sur_R = max(0.0, R - w_rice) if (rice_on and m in RICE_M) else R
        sur_F = max(0.0, R - FRUIT["water"]) if fruit_on else R
        sur_G = max(0.0, R - VEG["water"]) if veg_left > 0 else R
        runoff = RUNOFF_C * (sur_R * A_R + sur_F * A_F + sur_G * A_G)
        V = min(V + R * A_P + runoff - KP * E * A_P - need, v_max)
        # ---- ปลายเดือน: ปลา/เก็บเกี่ยว/ไข่
        if fish_left > 0:
            ev["fish_active"].append(t)
        if fish_left > 0 and V < H_FLOOR * 1000.0 * A_P:
            elapsed = 6 - fish_left
            M += FISH_KG * fish_rho * A_P * P_FISH * (elapsed / 6.0) * SALVAGE
            ev["protein"] += FISH_KG * fish_rho * A_P * (elapsed / 6.0) * SALVAGE * FISH_PROT
            fish_left = 0
            ev["fish_emerg"] += 1
        elif fish_left > 0:
            fish_left -= 1
            if fish_left == 0:
                harvest_kg = FISH_KG * fish_rho * A_P
                M += max(0.0, harvest_kg - FISH_HH_KG) * P_FISH   # เก็บกิน 60 กก. เหลือจึงขาย
                ev["protein"] += harvest_kg * FISH_PROT
                ev["fish_ok"] += 1
                ev["fish_harv"].append(t)
        if veg_left > 0:
            veg_left -= 1
            if veg_left == 0:
                M += A_G * VEG["rev"]
        if rice_on and m == RICE_M[-1]:
            S += Y_RICE * A_R                     # เก็บเกี่ยวเข้ายุ้ง (มวล ไม่ใช่เงิน)
            reserve = 12 * (HH_RICE_MO + (CK_RICE_MO * n_ck if n_ck > 0 else 0.0))  # สำรองตามฝูงที่วางแผน
            surplus = max(0.0, S - reserve)       # เหลือจากสำรองบริโภคคน+ไก่ 12 เดือน
            sale = SELL_FRAC * surplus            # ขายครึ่ง เก็บครึ่ง
            S -= sale
            M += P_PADDY * sale
            ev["rice_sold"] += sale
            rice_on = False
        if m == 11 and A_F > 0 and fruit_on:
            age = y - fruit_y0
            M += A_F * FRUIT["rev"] * (fruit_curve[age] if fruit_curve else 1.0)
        if has_ck:
            eggs = EGG_PER_CK_MO * n_ck
            M += max(0.0, eggs - EGG_HH_MO) * P_EGG   # กิน 120 ฟองก่อน เหลือจึงขาย
            ev["protein"] += EGG_PROT_MO * n_ck        # ศักยภาพโปรตีน (ผลิตทั้งหมด)
        if S >= HH_RICE_MO:                       # ครัวเรือนกินจากยุ้งก่อน
            S -= HH_RICE_MO
        else:
            short = HH_RICE_MO - S
            S = 0.0
            M -= P_PADDY * short                  # ขาดจึงซื้อ (ราคาเดียวกับขาย)
            ev["rice_bought"] += short
            ev["buy_months"] += 1
        Vh.append(V / 1000.0); Mh.append(M); Sh.append(S)
        if V < 0 or M < 0:
            ok = False
    return dict(feasible=ok and invest0(A_P, A_R, A_F, A_G) <= BUDGET,
                minV=min(Vh), minM=min(Mh), endM=Mh[-1], V=Vh, M=Mh, S=Sh,
                S_end=Sh[-1], wealth=Mh[-1] + P_PADDY * Sh[-1],
                ck_entry=ck_entry, protein_yr=ev["protein"] / n_years, **ev)


def evaluate(A_P, A_R, A_F, A_G, n_ck=0, rho=0.0, thR=0.0, thG=0.0,
             scens=SCEN10, w_rice=W_RICE_AWD):
    out = {}
    for sc in scens:
        s = simulate(A_P, A_R, A_F, A_G, n_ck, rho, thR, thG, sc, w_rice)
        if not s["feasible"]:
            return None
        out[sc] = s
    return dict(normal=out[()], all=out,
                worstV=min(s["minV"] for sc, s in out.items() if sc),
                falseskips=len(out[()]["skips"]) + out[()]["fish_skip"])


def grid_designs(A_H, step=160.0):
    """แจกแจง (A_P,A_R,A_F) โดย A_G เป็นตัวตาม (พื้นที่เพาะปลูกรวม = TOTAL - A_H)"""
    land = TOTAL - A_H
    n = int(TOTAL / step)
    for ip in range(2, n):
        A_P = ip * step
        for ir in range(0, n):
            A_R = ir * step
            for f in range(0, n):
                A_F = f * step
                A_G = land - A_P - A_R - A_F
                if A_G < -1e-9:
                    break
                yield A_P, A_R, A_F, max(A_G, 0.0)


def lab(A_P, A_R, A_F, A_G, A_H):
    f = lambda a: f"{a/TOTAL*100:.1f}"
    return f"สระ{f(A_P)} นา{f(A_R)} ไม้ผล{f(A_F)} ผัก{f(A_G)} บ้าน{f(A_H)} (%)"
