# -*- coding: utf-8 -*-
"""รันการทดลองทั้งหมดที่ใช้ในรายงาน แล้วบันทึกผลลงไฟล์ out/v3_results.json

   S1  M1 กวาดตะแกรงหาการจัดสรรที่รอด 6 ฉาก
   S2  M2 สอบเทียบเกณฑ์ระดับน้ำ และเทียบสองนโยบายเรื่องนา
   S3  M3 คัดแบบแนะนำภายใต้เงื่อนไขครบทุกข้อ

   จัดอันดับด้วยความมั่งคั่ง W60 = เงินสด + มูลค่ายุ้งข้าว
   วิธีรัน: python run_experiments.py"""
import json
from farm_model import (simulate, invest0, lab, a_house, P_PADDY,
                      SCEN6, SCEN10, DOUBLES, TOTAL, BUDGET)

def evaluate(A_P, A_R, A_F, A_G, n_ck=0, rho=0.0, thR=0.0, thG=0.0,
             scens=SCEN10, w_rice=None):
    kw = {} if w_rice is None else {"w_rice": w_rice}
    out = {}
    for sc in scens:
        s = simulate(A_P, A_R, A_F, A_G, n_ck, rho, thR, thG, sc, **kw)
        if not s["feasible"]:
            return None
        out[sc] = s
    return dict(normal=out[()], all=out,
                worstV=min(s["minV"] for sc, s in out.items() if sc))

J = {}
print("=" * 104)
print("S1 | M1 (บ้าน 80, นา 180, ไม่มีประตู, โมดูลข้าวสะสม): กวาด 160 ตร.ม., รอด 6 ฉาก, จัดอันดับด้วย W60")
print("=" * 104)
feas = []
for ip in range(2, 40):
    A_P = ip * 160.0
    for ir in range(0, 40):
        A_R = ir * 160.0
        for f in range(0, 40):
            A_F = f * 160.0
            A_G = TOTAL - 80.0 - A_P - A_R - A_F
            if A_G < -1e-9:
                break
            r = evaluate(A_P, A_R, A_F, max(A_G, 0.0), thR=0, thG=0, scens=SCEN6, w_rice=180.0)
            if r:
                n = r["normal"]
                feas.append((n["wealth"], A_P, A_R, A_F, max(A_G, 0.0), r["worstV"], n))
feas.sort(key=lambda x: -x[0])
print(f"  รอด {len(feas):,} แบบ")
C1 = feas[0]
C2 = next(x for x in feas if x[2] >= 1600)
target = (0.30 * TOTAL, 0.30 * TOTAL, 0.15 * TOTAL)
C0 = min(feas, key=lambda x: (x[1]-target[0])**2 + (x[2]-target[1])**2 + (x[3]-target[2])**2)
J["m1_traj"] = {}
for tag, x in (("C0", C0), ("C1", C1), ("C2", C2)):
    W, P, R, F, G, wv, n = x
    dd = min(simulate(P, R, F, G, thR=0, thG=0, drought=sc, w_rice=180.0)["minV"] for sc in DOUBLES)
    d1 = simulate(P, R, F, G, thR=0, thG=0, drought=(0,), w_rice=180.0)
    print(f"  {tag}: {lab(P,R,F,G,80)} | I0={invest0(P,R,F,G):,.0f}")
    print(f"      W60={W:,.0f} (เงินสด {n['endM']:,.0f} + ยุ้ง {n['S_end']:,.0f} กก.) ขาย {n['rice_sold']:,.0f} ซื้อ {n['rice_bought']:,.0f} กก."
          f" | แล้งเดี่ยว minV={d1['minV']:,.0f} | แล้งซ้อน {'ตาย %.0f' % dd if dd < 0 else 'รอด'}")
    J["m1_traj"][tag] = dict(V=d1["V"], M=d1["M"], design=[P, R, F, G])
J["m1"] = dict(C0=C0[:6], C1=C1[:6], C2=C2[:6])
_, P2, R2, F2, G2, _, _ = C2

print()
print("=" * 104)
print("S2 | M2 บน C2v3: สอบเทียบประตู (tie-break: W60 ปกติ, กันชน) — คำถามใหม่: ค่าซื้อข้าวปีแล้งดันประตูนาลงหรือไม่")
print("=" * 104)
grid = [i / 20 for i in range(0, 13)]
best, table = None, {}
for thR in grid:
    for thG in grid:
        r = evaluate(P2, R2, F2, G2, thR=thR, thG=thG)
        table[(thR, thG)] = r
        if r:
            key = (r["normal"]["wealth"], r["worstV"])
            if best is None or key > best[0]:
                best = (key, thR, thG, r)
_, thR2, thG2, rb = best
n0, dd0, d10 = rb["normal"], rb["all"][(0, 1)], rb["all"][(0,)]
print(f"  ประตูที่ดีที่สุด: งดนา<{thR2*3:.2f} ม. งดผัก<{thG2*3:.2f} ม.")
print(f"  ปกติ: W60={n0['wealth']:,.0f} ซื้อข้าว {n0['buy_months']} ด. | กันชน={rb['worstV']:,.0f}")
print(f"  แล้งเดี่ยว: W60={d10['wealth']:,.0f} ซื้อ {d10['rice_bought']:,.0f} กก. ({d10['buy_months']} ด.)")
print(f"  แล้งซ้อน:  W60={dd0['wealth']:,.0f} ซื้อ {dd0['rice_bought']:,.0f} กก. ({dd0['buy_months']} ด.) งดปลูก {len(dd0['skips'])} ครั้ง")
# เทียบนโยบายขั้ว: งดนาแบบเดิม (thR สูง) vs ทำนาปีแล้งด้วย AWD (thR=0) ที่ thG เท่ากัน
alt = evaluate(P2, R2, F2, G2, thR=0.0, thG=thG2)
hi = evaluate(P2, R2, F2, G2, thR=0.40, thG=thG2)
for name, r in (("ทำนาทุกปี (thR=0, AWD)", alt), ("งดนาปีแล้ง (thR=1.20 ม.)", hi)):
    if r:
        d = r["all"][(0, 1)]
        print(f"    {name}: แล้งซ้อน W60={d['wealth']:,.0f} ซื้อข้าว {d['rice_bought']:,.0f} กก. | กันชน={r['worstV']:,.0f}")
surv = ["รอด" if simulate(P2, R2, F2, G2, thR=0, thG=0, drought=sc)["minV"] >= 0 else "ตาย" for sc in DOUBLES]
print(f"  ablation AWD เดี่ยวไม่มีประตู รายคู่: {list(zip(['1-2','2-3','3-4','4-5'], surv))}")
mayS = simulate(P2, R2, F2, G2, thR=0, thG=0, drought=(0,), w_rice=180.0)
janS = simulate(P2, R2, F2, G2, thR=0, thG=0, drought=(0,), w_rice=180.0, start_offset=8)
print(f"  จุดเริ่ม: พ.ค. minV={mayS['minV']:,.0f} | ม.ค. minV={janS['minV']:,.0f}")
J["start"] = dict(may=mayS["V"], jan=janS["V"], mayMin=mayS["minV"], janMin=janS["minV"])
J["m2"] = dict(th=[thR2, thG2],
               heat={f"{a:.2f},{b:.2f}": (v["normal"]["wealth"] if v else None) for (a, b), v in table.items()},
               m1_dd={k: simulate(P2, R2, F2, G2, thR=0, thG=0, drought=(0, 1), w_rice=180.0)[k] for k in ("V", "M", "minV")},
               dd=dict(V=dd0["V"], M=dd0["M"], minV=dd0["minV"], endM=dd0["endM"], wealth=dd0["wealth"],
                       skips=[(t, w) for t, w in dd0["skips"]], rice_bought=dd0["rice_bought"]),
               n=dict(wealth=n0["wealth"], endM=n0["endM"]), d1=dict(wealth=d10["wealth"]),
               worstV=rb["worstV"], design=[P2, R2, F2, G2])

print()
print("=" * 104)
print("S3 | เพดานแรงงาน (C9: ผัก<=1,600) + เกณฑ์ครบ -> แบบแนะนำ (จัดอันดับ W60; ซื้อข้าวปกติต้อง = 0)")
print("=" * 104)
cand = []
for n_ck in (40, 60):
    AH = a_house(n_ck)
    for A_P in (640.0, 800.0, 960.0, 1120.0, 1280.0, 1440.0, 1600.0, 1920.0):
        for A_G in (1280.0, 1440.0, 1600.0):
            for A_F in (0.0, 320.0, 640.0, 960.0, 1280.0):
                A_R = TOTAL - AH - A_P - A_G - A_F
                if A_R < 1600 or invest0(A_P, A_R, A_F, A_G) > BUDGET:
                    continue
                for rho in (1.0, 2.0):
                    r = evaluate(A_P, A_R, A_F, A_G, n_ck, rho, thR2, thG2)
                    if r is None:
                        continue
                    n = r["normal"]
                    if n["protein_yr"] < 80 or n["buy_months"] > 0 or r["worstV"] < 150:
                        continue
                    cand.append((n["wealth"], A_P, A_R, A_F, A_G, n_ck, rho, r))
cand.sort(key=lambda x: -x[0])
print(f"  ผ่านครบเกณฑ์ {len(cand)} แบบ | 5 อันดับแรก:")
for W, P, R, F, G, nc, rh, r in cand[:5]:
    print(f"    {lab(P,R,F,G,a_house(nc))} ไก่{nc} ปลา{rh:.0f} | W60={W:>11,.0f} กันชน={r['worstV']:>6,.0f}")
best_W = cand[0][0]
pool = [x for x in cand if x[0] >= 0.99 * best_W]
pick = max(pool, key=lambda x: (x[3] > 0, x[7]["worstV"]))
W, A_P, A_R, A_F, A_G, n_ck, rho, r = pick
AH = a_house(n_ck)
n, d1, dd = r["normal"], r["all"][(0,)], r["all"][(0, 1)]
b = {sc: simulate(A_P, A_R, A_F, A_G, 0, 0.0, thR2, thG2, drought=sc) for sc in [(), (0,), (0, 1)]}
print(f"\n  แบบแนะนำ (เกณฑ์รองในกลุ่ม 1%: มีไม้ผล > กันชน): {lab(A_P,A_R,A_F,A_G,AH)} + ไก่ {n_ck} + ปลา {rho:.0f}")
print(f"    I0={invest0(A_P,A_R,A_F,A_G):,.0f} | กันชนทุกฉาก={r['worstV']:,.0f}")
for name, s, bs in (("ปกติ", n, b[()]), ("แล้งเดี่ยว", d1, b[(0,)]), ("แล้งซ้อน", dd, b[(0, 1)])):
    print(f"    {name:10s} W60={s['wealth']:>11,.0f} เงินสด={s['endM']:>11,.0f} ยุ้ง={s['S_end']:>5,.0f} กก. "
          f"(ไร้สัตว์ W60={bs['wealth']:>11,.0f}) ปลา {s['fish_ok']}/10 ฉก.{s['fish_emerg']} "
          f"ซื้อข้าว {s['rice_bought']:,.0f} กก./{s['buy_months']} ด. โปรตีน {s['protein_yr']:.0f} minV={s['minV']:,.0f}")
print(f"    ไก่เข้า t={n['ck_entry']} | M สิ้นเม.ย.ปี1={n['M'][11]:,.0f} | minM={n['minM']:,.0f}")
import farm_model as MV
ck, fr, sv = MV.P_EGG, MV.P_FISH, MV.SALVAGE
MV.P_EGG = MV.P_FISH = MV.SALVAGE = 0.0
c_n = simulate(A_P, A_R, A_F, A_G, n_ck, rho, thR2, thG2)
c_dd = simulate(A_P, A_R, A_F, A_G, n_ck, rho, thR2, thG2, drought=(0, 1))
MV.P_EGG, MV.P_FISH, MV.SALVAGE = ck, fr, sv
print(f"    สัตว์ล้มเหลวสมบูรณ์: ปกติ W60={c_n['wealth']:,.0f} รอด={c_n['feasible']} | แล้งซ้อน W60={c_dd['wealth']:,.0f} รอด={c_dd['feasible']}")
J["recommended"] = dict(areas=[A_P, A_R, A_F, A_G], AH=AH, n_ck=n_ck, rho=rho,
    I0=invest0(A_P, A_R, A_F, A_G), worstV=r["worstV"], th=[thR2, thG2],
    n={k: n[k] for k in ("V", "M", "S", "minV", "minM", "endM", "wealth", "S_end", "ck_entry", "fish_ok",
                         "fish_skip", "fish_emerg", "protein_yr", "fish_active", "fish_harv",
                         "rice_sold", "rice_bought", "buy_months")},
    d1={k: d1[k] for k in ("endM", "wealth", "minV", "fish_ok", "fish_emerg", "protein_yr", "rice_bought", "buy_months")},
    dd={k: dd[k] for k in ("V", "M", "S", "minV", "endM", "wealth", "S_end", "fish_ok", "fish_skip",
                           "fish_emerg", "protein_yr", "fish_active", "fish_harv", "rice_bought", "buy_months")},
    base={"n": b[()]["wealth"], "d1": b[(0,)]["wealth"], "dd": b[(0, 1)]["wealth"],
          "n_endM": b[()]["endM"], "dd_endM": b[(0, 1)]["endM"]},
    base_n_M=b[()]["M"], base_dd_M=b[(0, 1)]["M"],
    fail=dict(n=c_n["wealth"], dd=c_dd["wealth"], minM=c_n["minM"]),
    top5=[(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7]["worstV"]) for x in cand[:5]])

print()
print("=" * 104)
print("S4 | frontier ขนาดสระ ภายใต้เงื่อนไขครบทุกข้อ (ใช้สร้างรูปที่ 6 ของรายงาน)")
print("=" * 104)
rows = []
for ip in range(2, 14):
    A_P = ip * 160.0
    top = None
    for n_ck in (40, 60):
        AH = a_house(n_ck)
        for A_G in (1280.0, 1440.0, 1600.0):
            for A_F in (0.0, 320.0, 640.0, 960.0, 1280.0):
                A_R = TOTAL - AH - A_P - A_G - A_F
                if A_R < 1600 or invest0(A_P, A_R, A_F, A_G) > BUDGET:
                    continue
                for rho in (1.0, 2.0):
                    r = evaluate(A_P, A_R, A_F, A_G, n_ck, rho, thR2, thG2)
                    if r is None:
                        continue
                    n = r["normal"]
                    if n["protein_yr"] < 80 or n["buy_months"] > 0:
                        continue
                    if top is None or n["wealth"] > top[0]:
                        top = (n["wealth"], A_R, A_F, A_G, n_ck, rho, r["worstV"])
    if top:
        rows.append((A_P,) + top)
        W_, A_R, A_F, A_G, n_ck, rho, wv = top
        print(f"  สระ {A_P/64:5.1f}% | W60={W_:>11,.0f} | นา{A_R/64:4.1f} ไม้ผล{A_F/64:4.1f} ผัก{A_G/64:4.1f} "
              f"ไก่{n_ck} ปลา{rho:.0f} | กันชน {wv:>6,.0f}")
J["pond_frontier"] = [dict(pond=p, W=w, rice=r_, fruit=f, veg=g, n=nc, rho=rh, worstV=wv)
                      for p, w, r_, f, g, nc, rh, wv in rows]

print()
print("=" * 104)
print("S5 | ความทนต่อการรบกวนข้อสมมติ: เทียบแบบมีไม้ผลกับแบบไม่มีไม้ผล (ตารางที่ 9 ของรายงาน)")
print("=" * 104)
D2 = dict(name="ไม่มีไม้ผล (สระ30 นา43.4)", a=(1920.0, 2780.0, 0.0, 1600.0), n=40)
D3 = dict(name="มีไม้ผล 15% (สระ22.5 นา35.9)", a=(1440.0, 2300.0, 960.0, 1600.0), n=40)

def robust(d, kp=None, c=None, rainf=1.0):
    """ตรวจว่าการออกแบบยังรอดครบ 10 ฉากหรือไม่ เมื่อรบกวนข้อสมมติฝั่งดี"""
    old = (MV.KP, MV.RUNOFF_C, list(MV.RAIN_N), list(MV.RAIN_D))
    if kp: MV.KP = kp
    if c is not None: MV.RUNOFF_C = c
    if rainf != 1.0:
        MV.RAIN_N[:] = [x * rainf for x in old[2]]
        MV.RAIN_D[:] = [x * rainf for x in old[3]]
    wv, ok = 1e9, True
    for sc in SCEN10:
        s = simulate(*d["a"], d["n"], 2.0, thR2, thG2, drought=sc)
        if not s["feasible"]: ok = False
        if sc: wv = min(wv, s["minV"])
    MV.KP, MV.RUNOFF_C = old[0], old[1]
    MV.RAIN_N[:], MV.RAIN_D[:] = old[2], old[3]
    return ok, wv

PERTS = [("ฐาน (kp=0.70, c=0.30)", {}), ("kp=0.75", dict(kp=0.75)), ("kp=0.80", dict(kp=0.80)),
         ("c=0.25", dict(c=0.25)), ("c=0.20", dict(c=0.20)), ("ฝนทุกเดือน -10%", dict(rainf=0.9))]
J["diversity"] = {}
print(f"  {'การรบกวน':28s} | {D2['name']:>28s} | {D3['name']:>30s}")
for name, kw in PERTS:
    o2, w2 = robust(D2, **kw)
    o3, w3 = robust(D3, **kw)
    J["diversity"][name] = dict(d2_ok=o2, d2_wv=(None if w2 > 1e8 else w2),
                                d3_ok=o3, d3_wv=(None if w3 > 1e8 else w3))
    f = lambda o, w: (f"รอด กันชน {w:5.0f}" if o else "ไม่รอด")
    print(f"  {name:28s} | {f(o2,w2):>28s} | {f(o3,w3):>30s}")

print()
print("=" * 104)
print("S6 | ทางเลือกจ้างแรงงาน: ถอดเงื่อนไขทำเองได้ออก (หัวข้อ 6.5 ของรายงาน)")
print("=" * 104)
best = None
for n_ck in (40, 60):
    AH = a_house(n_ck)
    for ip in range(2, 14):
        A_P = ip * 160.0
        for ir in range(10, 20):
            A_R = ir * 160.0
            for A_F in (0.0, 320.0, 640.0, 960.0):
                A_G = TOTAL - AH - A_P - A_R - A_F
                if A_G < 0 or A_R < 1600 or invest0(A_P, A_R, A_F, A_G) > BUDGET:
                    continue
                for rho in (1.0, 2.0):
                    r = evaluate(A_P, A_R, A_F, A_G, n_ck, rho, thR2, thG2)
                    if r is None or r["normal"]["protein_yr"] < 80 or r["normal"]["buy_months"] > 0:
                        continue
                    if r["worstV"] < 150:
                        continue
                    if best is None or r["normal"]["wealth"] > best[0]:
                        best = (r["normal"]["wealth"], A_P, A_R, A_F, A_G, n_ck, rho, r)
Wu, A_P, A_R, A_F, A_G, n_ck, rho, r = best
rec_W = J["recommended"]["n"]["wealth"]
gain = Wu - rec_W
extra_rai = (A_G - 1600) / 1600
wage5 = extra_rai * 350 * 300 * 5
print(f"  ไม่มีเงื่อนไขทำเองได้: {lab(A_P, A_R, A_F, A_G, a_house(n_ck))} ไก่{n_ck} ปลา{rho:.0f}")
print(f"    W60 ปกติ={Wu:,.0f} | แล้งซ้อน={r['all'][(0,1)]['wealth']:,.0f} | กันชน={r['worstV']:,.0f} | ผัก {A_G/1600:.2f} ไร่")
print(f"    ส่วนต่างจากแบบแนะนำ +{gain:,.0f} | ค่าจ้าง {extra_rai:.2f} คน-ปี x 5 ปี = {wage5:,.0f} | สุทธิ {gain-wage5:+,.0f}")
J["hire_option"] = dict(areas=[A_P, A_R, A_F, A_G], n=n_ck, rho=rho, W=Wu,
                        dd=r["all"][(0, 1)]["wealth"], worstV=r["worstV"],
                        gain=gain, wage5=wage5, net=gain - wage5)

print()
print("=" * 104)
print("S7 | คาดการณ์ 15 ปี: เส้นโค้งอายุไม้ผล + เกณฑ์ปลูกไม้ผล (หัวข้อ 3.4 ของรายงาน)")
print("=" * 104)
REC = tuple(J["recommended"]["areas"])
n_rec, rho_rec = int(J["recommended"]["n_ck"]), J["recommended"]["rho"]
CURVE15 = [0.0, 0.0, 0.5, 1.0, 1.5] + [2.0] * 10
CURVE5 = CURVE15[:5]
W_at = lambda s, mo: s["M"][mo - 1] + P_PADDY * s["S"][mo - 1]

# สอบเทียบเกณฑ์ใหม่ใต้โปรไฟล์อายุ เพราะโปรไฟล์รายได้เปลี่ยนแล้วเกณฑ์เดิมไม่เหมาะ
best3 = None
for thR in [i / 20 for i in range(13)]:
    for thG in [i / 20 for i in range(13)]:
        out, ok = {}, True
        for sc in SCEN10:
            s = simulate(*REC, n_rec, rho_rec, thR, thG, drought=sc, fruit_curve=CURVE5, fruit_gate=True)
            if not s["feasible"]:
                ok = False; break
            out[sc] = s
        if ok:
            key = (out[()]["wealth"], min(s["minV"] for sc, s in out.items() if sc))
            if best3 is None or key > best3[0]:
                best3 = (key, thR, thG)
(kW, kV), thR3, thG3 = best3
print(f"  เกณฑ์สอบเทียบใหม่ใต้โปรไฟล์อายุ: งดนา<{thR3*3:.2f} ม. งดผัก<{thG3*3:.2f} ม. (กันชน 5 ปี {kV:,.0f})")
SCN = {"ปกติล้วน": (), "แล้ง 3 ครั้ง (ปี 3,8,13)": (2, 7, 12), "แล้งหนัก (ซ้อน 1-2 + 8,13)": (0, 1, 7, 12)}
J["longrun"] = dict(th3=[thR3, thG3], EA={})
for name, dr in SCN.items():
    for cname, curve, gate in (("ตามตาราง", None, False), ("เส้นโค้งอายุ+เกณฑ์ปลูกไม้ผล", CURVE15, True)):
        th = (thR2, thG2) if not gate else (thR3, thG3)
        s = simulate(*REC, n_rec, rho_rec, th[0], th[1], drought=dr, n_years=15,
                     fruit_curve=curve, fruit_gate=gate)
        J["longrun"]["EA"][f"{name}|{cname}"] = [W_at(s, 60) / 1e6, W_at(s, 120) / 1e6,
                                                 W_at(s, 180) / 1e6, s["rice_bought"], s["feasible"]]
        print(f"  {name:26s} {cname:26s} W5={W_at(s,60)/1e6:5.2f} W10={W_at(s,120)/1e6:5.2f} "
              f"W15={W_at(s,180)/1e6:5.2f} ซื้อข้าว {s['rice_bought']:>5,.0f} กก. {'รอด' if s['feasible'] else 'ไม่รอด'}")

# วิถีสำหรับรูปที่ 9: เทียบสองโปรไฟล์ไม้ผลบนเกณฑ์เดียวกัน เพื่อแยกผลของเส้นโค้งอายุออกมาให้เห็นชัด
sf = simulate(*REC, n_rec, rho_rec, thR2, thG2, drought=(2, 7, 12), n_years=15)
sc_ = simulate(*REC, n_rec, rho_rec, thR2, thG2, drought=(2, 7, 12), n_years=15, fruit_curve=CURVE15, fruit_gate=True)
sh = simulate(*REC, n_rec, rho_rec, thR3, thG3, drought=(0, 1, 7, 12), n_years=15, fruit_curve=CURVE15, fruit_gate=True)
shx = simulate(*REC, n_rec, rho_rec, thR2, thG2, drought=(0, 1, 7, 12), n_years=15, fruit_curve=CURVE15)
Wser = lambda s: [m + P_PADDY * x for m, x in zip(s["M"], s["S"])]
# จุดตัดคือเดือนที่เส้นโค้งอายุแซงแล้วไม่กลับลงไปต่ำกว่าอีก ไม่ใช่เดือนแรกที่บังเอิญสูงกว่า
# (ห้าเดือนแรกเส้นโค้งอายุสูงกว่าเพราะยังไม่ถึงเดือนจ่ายค่าปลูกไม้ผล จึงต้องข้ามช่วงนั้นไป)
below = [t for t in range(180) if Wser(sc_)[t] < Wser(sf)[t]]
cross = (below[-1] + 1) if below else 0
print(f"  จุดตัด: เส้นโค้งอายุแซงโปรไฟล์ตารางที่เดือนที่ {cross+1} (ปีที่ {cross//12+1})")
J["longrun"]["cross_month"] = cross + 1
J["longrun"]["traj2"] = dict(flat=Wser(sf), curve_gate_d3=Wser(sc_), hard_gate=Wser(sh), hard_nogate=Wser(shx))

with open("out/v3_results.json", "w") as fp:
    json.dump(J, fp, ensure_ascii=False)
print("\nบันทึกผลทั้งหมดลง out/v3_results.json แล้ว")
