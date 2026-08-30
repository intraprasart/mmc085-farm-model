# -*- coding: utf-8 -*-
"""สร้างรูปทั้งหมดที่ใช้ในรายงานจากผลใน out/v3_results.json
   ต้องรัน run_experiments.py ก่อน
   วิธีรัน: python make_figures.py"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from pathlib import Path

for p in [Path.home() / "Library/Fonts/THSarabunNew.ttf", Path("/Library/Fonts/THSarabunNew.ttf")]:
    if p.exists():
        font_manager.fontManager.addfont(str(p)); break
plt.rcParams.update({"font.family": "TH Sarabun New", "font.size": 16,
                     "axes.unicode_minus": False, "figure.dpi": 150})
J = json.load(open("out/v3_results.json"))
tt = list(range(1, 61))
_d = lambda tag: J["m1_traj"][tag]["design"]          # [สระ, นา, ไม้ผล, ผัก] ตร.ม.
_pc = lambda v: v / 64.0                               # ตร.ม. -> % ของ 6,400
LBL = {"C0": f"C0 ใกล้ทฤษฎีใหม่ (สระ{_pc(_d('C0')[0]):.1f} นา{_pc(_d('C0')[1]):.1f} ไม้ผล{_pc(_d('C0')[2]):.1f})",
       "C1": f"C1 กำไรสูงสุด (ผัก {_pc(_d('C1')[3]):.1f}%)",
       "C2": f"C2 + ข้าวพอกิน (นา {_pc(_d('C2')[1]):.1f}%)"}
CLR = {"C0": "#b22222", "C1": "#e0a010", "C2": "#1c7a3c"}

# ---------- F1: M1 วิถีแล้งปีที่ 1 ----------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
for tag in ("C0", "C1", "C2"):
    ax1.plot(tt, J["m1_traj"][tag]["V"], color=CLR[tag], lw=2, label=LBL[tag])
    ax2.plot(tt, [m / 1000 for m in J["m1_traj"][tag]["M"]], color=CLR[tag], lw=2, label=LBL[tag])
ax1.axhline(0, color="black", lw=1); ax1.axvspan(1, 6, color="#c44", alpha=0.10)
ax1.text(3.5, 5600, "แล้ง พ.ค.–ต.ค. ปีที่ 1", ha="center", color="#a22", fontsize=13)
ax1.set_ylabel("น้ำในสระ (ลบ.ม.)")
ax1.set_title("M1 (บ้านตามตาราง + โมดูลข้าวสะสม): วิถีน้ำและเงินสด 60 เดือน เมื่อแล้งปีที่ 1\n"
              r"$k_p=0.70$, $c=0.30$, สระลึก 3 ม., เริ่ม พ.ค., นาแบบเดิม 180 ล./ตร.ม./เดือน", fontsize=16)
ax1.legend(loc="lower right", fontsize=12.5); ax1.grid(alpha=0.25)
ax2.axhline(0, color="black", lw=1); ax2.axvspan(1, 6, color="#c44", alpha=0.10)
for k in range(1, 5):
    for ax in (ax1, ax2):
        ax.axvline(12 * k + 0.5, color="#999", lw=0.6, ls=":")
ax2.set_xlabel("เดือนที่ (t=1 คือ พ.ค. ปีที่ 1)"); ax2.set_ylabel("เงินสดสะสม (พันบาท)")
ax2.set_xticks([1, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]); ax2.set_xlim(1, 60)
ax2.legend(loc="upper left", fontsize=12.5); ax2.grid(alpha=0.25)
fig.tight_layout(); fig.savefig("out/fig_v3_m1.png", bbox_inches="tight"); plt.close(fig)

# ---------- F2: จุดเริ่มปฏิทิน ----------
S = J["start"]
fig, ax = plt.subplots(figsize=(10, 4.4))
ax.plot(tt, S["may"], color="#1c7a3c", lw=2, label=f"เริ่ม พ.ค. — ต่ำสุด {S['mayMin']:,.0f} ลบ.ม. (รอด)")
ax.plot(tt, S["jan"], color="#b22222", lw=2, label=f"เริ่ม ม.ค. — ต่ำสุด {S['janMin']:,.0f} ลบ.ม. (สระแห้ง)")
ax.axhline(0, color="black", lw=1)
ax.fill_between(tt, 0, [min(v, 0) for v in S["jan"]], color="#b22222", alpha=0.25)
ax.set_title("จุดเริ่มปฏิทิน $t{=}1$ คือตัวแปรออกแบบ: ขุดสระเสร็จรับต้นฤดูฝน (พ.ค.) หรือกลางแล้ง (ม.ค.)\n"
             "(การจัดสรร C2 เดียวกัน แล้งปีที่ 1 เหมือนกัน)", fontsize=16)
ax.set_xlabel("เดือนที่"); ax.set_ylabel("น้ำในสระ (ลบ.ม.)")
ax.set_xlim(1, 60); ax.grid(alpha=0.25); ax.legend(fontsize=13.5)
fig.tight_layout(); fig.savefig("out/fig_v3_start.png", bbox_inches="tight"); plt.close(fig)

# ---------- F3: heatmap สอบเทียบเกณฑ์ ----------
grid = sorted({float(k.split(",")[0]) for k in J["m2"]["heat"]})
Z = np.full((len(grid), len(grid)), np.nan)
for k, v in J["m2"]["heat"].items():
    a, b = (float(x) for x in k.split(","))
    if v is not None:
        Z[grid.index(a), grid.index(b)] = v / 1e6
thR, thG = J["m2"]["th"]
GATE = (f"กฎเดียว {thR*3:.2f} ม." if abs(thR - thG) < 1e-9
        else f"นา {thR*3:.2f} ม. / ผัก {thG*3:.2f} ม.")
fig, ax = plt.subplots(figsize=(9.2, 6.2))
cmap = plt.cm.YlGn.copy(); cmap.set_bad("#d9d9d9")
im = ax.imshow(np.ma.masked_invalid(Z), origin="lower", cmap=cmap, aspect="auto",
               extent=[-0.025, grid[-1] + 0.025, -0.025, grid[-1] + 0.025],
               vmin=np.nanmin(Z) - 0.15, vmax=np.nanmax(Z))
ax.plot(thG, thR, marker="*", ms=22, color="#b22222", mec="white", mew=1.2)
ax.annotate(f"จุดที่เลือก: {GATE}\nทั้งนาและผัก", xy=(thG, thR),
            xytext=(thG - 0.28, thR + 0.13), fontsize=14, arrowprops=dict(arrowstyle="->"))
ax.text(0.075, 0.5, "สีเทา = ไม่รอด\nแล้งซ้อน 2 ปี", fontsize=13.5, ha="center", color="#333")
sec = ax.secondary_xaxis("top", functions=(lambda x: 3 * x, lambda x: x / 3))
sec.set_xlabel("เกณฑ์ความลึกน้ำงดรอบผัก (เมตร)", fontsize=14)
sec2 = ax.secondary_yaxis("right", functions=(lambda x: 3 * x, lambda x: x / 3))
sec2.set_ylabel("เกณฑ์ความลึกน้ำงดทำนา (เมตร)", fontsize=14)
ax.set_xlabel(r"เกณฑ์ลงผัก $\theta_G$ (สัดส่วนของ $V_{\max}$)")
ax.set_ylabel(r"เกณฑ์ทำนา $\theta_R$ (สัดส่วนของ $V_{\max}$)")
ax.set_title("แผนที่สอบเทียบเกณฑ์ (C2v3): ความมั่งคั่งปกติ 5 ปี (ล้านบาท)\n"
             f"เลือกจุดในเขตกำไรสูงสุดที่ให้กันชนน้ำมากที่สุด — ได้{GATE}", fontsize=16)
cb = fig.colorbar(im, ax=ax); cb.set_label("ความมั่งคั่งปลายปีที่ 5 ปีปกติ W60 (ล้านบาท)", fontsize=14)
fig.tight_layout(); fig.savefig("out/fig_v3_thresh.png", bbox_inches="tight"); plt.close(fig)

# ---------- F4: แล้งซ้อน M1 vs M2 ----------
m1, m2 = J["m2"]["m1_dd"], J["m2"]["dd"]
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.2), sharex=True)
ax1.plot(tt, m1["V"], color="#b22222", lw=2, ls="--",
         label=f"M1 พฤติกรรมคงที่ — ต่ำสุด {m1['minV']:,.0f} ลบ.ม. (สระแห้ง)")
ax1.plot(tt, m2["V"], color="#1c7a3c", lw=2.2,
         label=f"M2 {GATE} — ต่ำสุด {m2['minV']:,.0f} ลบ.ม. (รอด)")
died = next(i for i, v in enumerate(m1["V"]) if v < 0) + 1
ax1.annotate(f"M1 สระแห้งเดือนที่ {died}", xy=(died, 0), xytext=(died + 5, 2600),
             color="#b22222", fontsize=14, arrowprops=dict(arrowstyle="->", color="#b22222"))
sk_g = [(t + 1, m2["V"][t]) for t, w in m2["skips"] if w == "ผัก"]
sk_r = [(t + 1, m2["V"][t]) for t, w in m2["skips"] if w == "นา"]
if sk_g: ax1.scatter(*zip(*sk_g), marker="v", s=70, color="#e0a010", zorder=5, label=f"งดรอบผัก ({len(sk_g)} ครั้ง)")
if sk_r: ax1.scatter(*zip(*sk_r), marker="X", s=90, color="#7a1c5c", zorder=5, label=f"งดทำนา ({len(sk_r)} ครั้ง)")
ax1.axhline(0, color="black", lw=1); ax1.axvspan(1, 18, color="#c44", alpha=0.08)
ax1.text(9.5, 5650, "แล้งซ้อน 2 ปี (พ.ค.ปี1–ต.ค.ปี2)", ha="center", color="#a22", fontsize=13)
ax1.set_ylabel("น้ำในสระ (ลบ.ม.)")
_c2 = _d("C2")
ax1.set_title(f"บททดสอบแล้งซ้อน 2 ปีติด — การจัดสรร C2 เดียวกัน "
              f"(สระ{_pc(_c2[0]):.1f} นา{_pc(_c2[1]):.1f} ผัก{_pc(_c2[3]):.1f})\n"
              f"กฎ M2: เห็นน้ำลึกต่ำกว่า {thR*3:.2f} ม. ก่อนหว่าน — งดรอบนั้น (นาและผักใช้เกณฑ์เดียวกัน)", fontsize=15.5)
ax1.legend(loc="upper right", fontsize=12.5); ax1.grid(alpha=0.25)
ax2.plot(tt, [m / 1000 for m in m1["M"]], color="#b22222", lw=2, ls="--", label="M1 (เส้นสมมติ — ระบบล่มจริง)")
ax2.plot(tt, [m / 1000 for m in m2["M"]], color="#1c7a3c", lw=2.2,
         label=f"M2 — จบ 5 ปีที่ {m2['endM']/1e6:.2f} ล้านบาท")
ax2.axvspan(1, 18, color="#c44", alpha=0.08); ax2.axhline(0, color="black", lw=1)
for k in range(1, 5):
    for ax in (ax1, ax2):
        ax.axvline(12 * k + 0.5, color="#999", lw=0.6, ls=":")
ax2.set_xlabel("เดือนที่ (t=1 คือ พ.ค. ปีที่ 1)"); ax2.set_ylabel("เงินสดสะสม (พันบาท)")
ax2.set_xticks([1, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]); ax2.set_xlim(1, 60)
ax2.legend(loc="upper left", fontsize=13); ax2.grid(alpha=0.25)
fig.tight_layout(); fig.savefig("out/fig_v3_double.png", bbox_inches="tight"); plt.close(fig)

# ---------- F6: แบบแนะนำ (3 แผง: น้ำ / ยุ้งข้าว / เงินสด) ----------
Rc = J["recommended"]
A_P = Rc["areas"][0]
n, dd = Rc["n"], Rc["dd"]
spans = set(dd["fish_active"])
fig, (ax1, axS, ax2) = plt.subplots(3, 1, figsize=(10, 10.6), sharex=True,
                                    gridspec_kw={"height_ratios": [3, 1.6, 3]})
for a in sorted(spans):
    ax1.axvspan(a + 0.5, a + 1.5, color="#9fc6e8", alpha=0.5, lw=0)
ax1.plot(tt, n["V"], color="#1c7a3c", lw=1.4, ls="--", alpha=0.6, label="ปีปกติล้วน")
ax1.plot(tt, dd["V"], color="#1c7a3c", lw=2.2, label=f"แล้งซ้อนปี 1–2 (ต่ำสุด {dd['minV']:,.0f} ลบ.ม.)")
ax1.scatter([t + 1 for t in dd["fish_harv"]], [dd["V"][t] for t in dd["fish_harv"]],
            marker="D", s=55, color="#1f4e79", zorder=5, label=f"จับปลาครบรอบ ({dd['fish_ok']} รอบ)")
ax1.axhline(1.2 * A_P, color="#1f4e79", lw=1.1, ls=":")
ax1.axhline(0.5 * A_P, color="#b22222", lw=1.1, ls=":")
ax1.text(60.6, 1.2 * A_P, f"เกณฑ์ปล่อยปลา 1.2 ม. ({1.2*A_P:,.0f})", fontsize=12, va="center", color="#1f4e79")
ax1.text(60.6, 0.5 * A_P, f"พื้นปลา 0.5 ม. ({0.5*A_P:,.0f})", fontsize=12, va="center", color="#b22222")
ax1.axhline(0, color="black", lw=1); ax1.axvspan(1, 18, color="#c44", alpha=0.07)
ax1.set_ylabel("น้ำในสระ (ลบ.ม.)")
_ra = Rc["areas"]; _nck = int(Rc["n_ck"]); _rho = Rc["rho"]
_zone = " : ".join(f"{_pc(v):.1f}" for v in _ra) + f" : {_pc(Rc['AH']):.1f}"
ax1.set_title(f"แบบแนะนำ: สระ : นา : ไม้ผล : ผัก : บ้าน = {_zone} (%) "
              f"+ ไก่ {_nck} ตัว + ปลานิล {_rho*_ra[0]:,.0f} ตัว/รอบ ({_rho:.0f} ตัว/ตร.ม.)\n"
              f"{GATE} + นาเปียกสลับแห้ง + เพดานแรงงานผัก 1 ไร่ + ยุ้งข้าว (ขายครึ่ง–เก็บครึ่ง)", fontsize=15)
ax1.legend(loc="upper right", fontsize=12); ax1.grid(alpha=0.25)

axS.plot(tt, n["S"], color="#7a5c10", lw=1.6, ls="--", alpha=0.7, label=f"ปกติ — ปลายปีที่ 5 เหลือ {n['S_end']:,.0f} กก.")
axS.plot(tt, dd["S"], color="#7a5c10", lw=2.2, label=f"แล้งซ้อน — ซื้อข้าว {dd['rice_bought']:,.0f} กก. ใน {dd['buy_months']} เดือน")
axS.axhline(0, color="black", lw=1)
axS.axvspan(1, 18, color="#c44", alpha=0.07)
buy = [t + 1 for t in range(60) if dd["S"][t] <= 1e-9]
axS.scatter(buy, [0]*len(buy), marker="|", s=90, color="#b22222", label="เดือนที่ยุ้งหมด (ครัวเรือนซื้อข้าว)")
axS.set_ylabel("ยุ้งข้าว (กก.)")
axS.legend(loc="upper right", fontsize=11.5); axS.grid(alpha=0.25)

ax2.plot(tt, [m / 1e6 for m in n["M"]], color="#1c7a3c", lw=2.2, label=f"มีสัตว์ ปีปกติ — เงินสด {n['endM']/1e6:.2f} ล้าน")
ax2.plot(tt, [m / 1e6 for m in Rc["base_n_M"]], color="#888", lw=1.6, ls="--", label="ไร้สัตว์ ปีปกติ")
ax2.plot(tt, [m / 1e6 for m in dd["M"]], color="#b26b22", lw=2.2, label=f"มีสัตว์ แล้งซ้อน — {dd['endM']/1e6:.2f} ล้าน")
ax2.plot(tt, [m / 1e6 for m in Rc["base_dd_M"]], color="#b8a58a", lw=1.6, ls="--", label="ไร้สัตว์ แล้งซ้อน")
ck = n["ck_entry"] + 1
ax2.scatter([ck], [n["M"][ck - 1] / 1e6], marker="*", s=240, color="#b22222", zorder=6)
ax2.annotate(f"ซื้อไก่ {_nck} ตัว + สร้างเล้า ({450*_nck:,.0f} บ.)\nพ.ค. ปีที่ 2 — กฎทบทวนประจำปี",
             xy=(ck, n["M"][ck - 1] / 1e6), xytext=(ck + 3, 0.12), fontsize=12.5, color="#b22222",
             arrowprops=dict(arrowstyle="->", color="#b22222"))
ax2.axvspan(1, 18, color="#c44", alpha=0.07); ax2.axhline(0, color="black", lw=1)
for k in range(1, 5):
    for ax in (ax1, axS, ax2):
        ax.axvline(12 * k + 0.5, color="#999", lw=0.6, ls=":")
ax2.set_xlabel("เดือนที่ (t=1 คือ พ.ค. ปีที่ 1)"); ax2.set_ylabel("เงินสดสะสม (ล้านบาท)")
ax2.set_xticks([1, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]); ax2.set_xlim(1, 60)
ax2.legend(loc="upper left", fontsize=12); ax2.grid(alpha=0.25)
fig.tight_layout(); fig.savefig("out/fig_v3_final.png", bbox_inches="tight"); plt.close(fig)
print("saved v3 figures")

# ---------- F7: frontier ขนาดสระ ใต้เงื่อนไขครบ ----------
fr = J["pond_frontier"]
pn = [f["pond"] / 64 for f in fr]
Wv = [f["W"] / 1e6 for f in fr]
bf = [f["worstV"] for f in fr]
lbl = [f"{p:.1f}" for p in pn]
rec_pond = Rc["areas"][0] / 64
ri = min(range(len(pn)), key=lambda i: abs(pn[i] - rec_pond))
lo_i = min(range(len(bf)), key=lambda i: bf[i])
fig, ax = plt.subplots(figsize=(10.8, 5.8))
cols = ["#1c7a3c" if i == ri else "#a8c9a8" for i in range(len(pn))]
bars = ax.bar(lbl, Wv, width=0.60, color=cols)
for b_, w in zip(bars, Wv):
    ax.text(b_.get_x() + b_.get_width() / 2, w + 0.006, f"{w:.2f}", ha="center", fontsize=10.5)
span = max(Wv) - min(Wv)
ax.set_ylim(min(Wv) - 0.10, max(Wv) + 0.12)
ax.set_ylabel("ความมั่งคั่งปลายปีที่ 5 ปีปกติ (ล้านบาท)")
ax.set_xlabel("ขนาดสระ (% ของพื้นที่) — องค์ประกอบอื่นเลือกดีที่สุดภายใต้เงื่อนไขครบทุกข้อ")
ax.text(0.5, 0.95, f"นอกช่วง {pn[0]:.1f}–{pn[-1]:.1f}% ไม่มีการจัดสรรใดที่ผ่านเงื่อนไขครบและทนการรบกวนได้ทุกข้อ",
        transform=ax.transAxes, ha="center", fontsize=13.5, color="#1c7a3c")
ax2 = ax.twinx()
ax2.plot(lbl, bf, "o-", color="#1f4e79", lw=2, ms=8, zorder=5)
ax2.set_ylabel("กันชนน้ำ: น้ำต่ำสุดร่วมทุกฉาก (ลบ.ม.)", color="#1f4e79")
ax2.tick_params(axis="y", labelcolor="#1f4e79")
ax2.set_ylim(0, max(bf) * 1.55)
for x_, y_ in zip(range(len(bf)), bf):
    dy = -max(bf) * 0.085 if x_ == ri else max(bf) * 0.045      # จุดที่ถูกวงไว้ ย้ายป้ายลงล่างกันทับ
    ax2.text(x_, y_ + dy, f"{y_:,.0f}", ha="center", fontsize=11, color="#1f4e79")
ax2.scatter([ri], [bf[ri]], s=200, facecolors="none", edgecolors="#b22222", lw=2.2, zorder=6)
ax2.annotate(f"แบบแนะนำ สระ {pn[ri]:.1f}%\nมั่งคั่งสูงสุด {Wv[ri]:.2f} ล้านบาท และกันชน {bf[ri]:,.0f} ลบ.ม.",
             xy=(ri, bf[ri]), xytext=(max(ri - 3.6, 0.05), max(bf) * 1.30), fontsize=13, color="#b22222",
             arrowprops=dict(arrowstyle="->", color="#b22222"))
ax.set_title("ความมั่งคั่งไต่ขึ้นจนถึงสระ 30% แล้วร่วงลง เพราะสระที่ใหญ่เกินไปกินพื้นที่เพาะปลูกและเพิ่มผิวระเหย\n"
             "ขณะที่กันชนน้ำแทบไม่เปลี่ยน ขนาดสระที่เหมาะสมจึงถูกกำหนดด้วยเงื่อนไขความอยู่รอด ไม่ใช่ด้วยผลตอบแทน",
             fontsize=15.5)
ax.grid(alpha=0.22, axis="y")
fig.tight_layout(); fig.savefig("out/fig_v3_frontier.png", bbox_inches="tight"); plt.close(fig)
print("saved fig_v3_frontier.png")

# ---------- F8: วิถีความมั่งคั่ง 15 ปี ----------
LR = J["longrun"]; T2 = LR["traj2"]; cm = LR["cross_month"]
tt15 = list(range(1, 181))
fig, ax = plt.subplots(figsize=(10.8, 5.6))
ax.plot(tt15, [w / 1e6 for w in T2["flat"]], color="#7a5c10", lw=1.8, ls="--",
        label="แล้ง 3 ครั้ง — รายได้ไม้ผลแบนราบตามตารางโจทย์")
ax.plot(tt15, [w / 1e6 for w in T2["curve_gate_d3"]], color="#1c7a3c", lw=2.4,
        label="แล้ง 3 ครั้ง — เส้นโค้งอายุไม้ผล (เกณฑ์เดียวกัน)")
ax.plot(tt15, [w / 1e6 for w in T2["hard_gate"]], color="#1f4e79", lw=2.0,
        label="แล้งหนัก — เส้นโค้งอายุ + เกณฑ์ปลูกไม้ผล")
NG = LR.get("nogate", {})
_ngm = NG.get("neg_months") or []
_nglab = ("แล้งหนัก — ไม่มีเกณฑ์ปลูกไม้ผล (เส้นสมมติ: เงินสดติดลบเดือนที่ "
          + ", ".join(str(m) for m in _ngm) + " จึงผิดเงื่อนไข)") if _ngm else \
         "แล้งหนัก — เส้นโค้งอายุ แต่ไม่มีเกณฑ์ปลูกไม้ผล"
ax.plot(tt15, [w / 1e6 for w in T2["hard_nogate"]], color="#b22222", lw=1.8, ls=":", label=_nglab)
if _ngm:
    ax.scatter([_ngm[0]], [T2["hard_nogate"][_ngm[0] - 1] / 1e6], marker="X", s=130,
               color="#b22222", zorder=6)
yc = T2["curve_gate_d3"][cm - 1] / 1e6
ax.axvline(cm, color="#1c7a3c", lw=1.0, ls=":")
ax.scatter([cm], [yc], s=150, facecolors="none", edgecolors="#1c7a3c", lw=2, zorder=6)
ax.annotate(f"จุดตัดเดือนที่ {cm} (ปีที่ {(cm - 1)//12 + 1})\nไม้ผลเริ่มคุ้มจากตรงนี้ไป",
            xy=(cm, yc), xytext=(cm + 9, yc - 1.75), fontsize=13, color="#1c7a3c",
            arrowprops=dict(arrowstyle="->", color="#1c7a3c"))
for k in range(1, 15):
    ax.axvline(12 * k + 0.5, color="#999", lw=0.5, ls=":")
ax.set_xlim(1, 180); ax.set_xticks([1] + [12 * k for k in range(1, 16)])
ax.set_xticklabels(["1"] + [f"{k}" for k in range(1, 16)])
ax.set_xlabel("ปีที่ (แกนเดินทีละเดือน รวม 180 เดือน)")
ax.set_ylabel("ความมั่งคั่งสะสม (ล้านบาท)")
ax.set_title("วิถีความมั่งคั่ง 15 ปีของแบบแนะนำ: ไม้ผลตามหลังในช่วงต้นแล้วแซงในระยะยาว\n"
             "และเกณฑ์ปลูกไม้ผลคือสิ่งที่กันไม่ให้เงินสดติดลบในฉากแล้งหนัก", fontsize=15.5)
ax.legend(loc="upper left", fontsize=12); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig("out/fig_v3_longrun.png", bbox_inches="tight"); plt.close(fig)
print("saved fig_v3_longrun.png")
