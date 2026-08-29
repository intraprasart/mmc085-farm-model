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
LBL = {"C0": "C0 ใกล้ทฤษฎีใหม่ (สระ32.5 นา32.5 ไม้ผล12.5)", "C1": "C1 กำไรสูงสุด (ผัก 51.2%)",
       "C2": "C2 + ข้าวพอกิน (นา 25%)"}
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
fig, ax = plt.subplots(figsize=(9.2, 6.2))
cmap = plt.cm.YlGn.copy(); cmap.set_bad("#d9d9d9")
im = ax.imshow(np.ma.masked_invalid(Z), origin="lower", cmap=cmap, aspect="auto",
               extent=[-0.025, grid[-1] + 0.025, -0.025, grid[-1] + 0.025],
               vmin=np.nanmin(Z) - 0.15, vmax=np.nanmax(Z))
ax.plot(thG, thR, marker="*", ms=22, color="#b22222", mec="white", mew=1.2)
ax.annotate("จุดที่เลือก: กฎเดียว 1.20 ม.\nทั้งนาและผัก", xy=(thG, thR),
            xytext=(thG - 0.28, thR + 0.13), fontsize=14, arrowprops=dict(arrowstyle="->"))
ax.text(0.075, 0.5, "สีเทา = ไม่รอด\nแล้งซ้อน 2 ปี", fontsize=13.5, ha="center", color="#333")
sec = ax.secondary_xaxis("top", functions=(lambda x: 3 * x, lambda x: x / 3))
sec.set_xlabel("เกณฑ์ความลึกน้ำงดรอบผัก (เมตร)", fontsize=14)
sec2 = ax.secondary_yaxis("right", functions=(lambda x: 3 * x, lambda x: x / 3))
sec2.set_ylabel("เกณฑ์ความลึกน้ำงดทำนา (เมตร)", fontsize=14)
ax.set_xlabel(r"เกณฑ์ลงผัก $\theta_G$ (สัดส่วนของ $V_{\max}$)")
ax.set_ylabel(r"เกณฑ์ทำนา $\theta_R$ (สัดส่วนของ $V_{\max}$)")
ax.set_title("แผนที่สอบเทียบเกณฑ์ (C2v3): ความมั่งคั่งปกติ 5 ปี (ล้านบาท)\n"
             "เลือกจุดในเขตกำไรสูงสุดที่ให้กันชนน้ำมากที่สุด — ได้กฎเดียว 1.20 ม.", fontsize=16)
cb = fig.colorbar(im, ax=ax); cb.set_label("ความมั่งคั่งปลายปีที่ 5 ปีปกติ W60 (ล้านบาท)", fontsize=14)
fig.tight_layout(); fig.savefig("out/fig_v3_thresh.png", bbox_inches="tight"); plt.close(fig)

# ---------- F4: แล้งซ้อน M1 vs M2 ----------
m1, m2 = J["m2"]["m1_dd"], J["m2"]["dd"]
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.2), sharex=True)
ax1.plot(tt, m1["V"], color="#b22222", lw=2, ls="--",
         label=f"M1 พฤติกรรมคงที่ — ต่ำสุด {m1['minV']:,.0f} ลบ.ม. (สระแห้ง)")
ax1.plot(tt, m2["V"], color="#1c7a3c", lw=2.2,
         label=f"M2 กฎเดียว 1.20 ม. — ต่ำสุด {m2['minV']:,.0f} ลบ.ม. (รอด)")
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
ax1.set_title("บททดสอบแล้งซ้อน 2 ปีติด — การจัดสรร C2v3 เดียวกัน (สระ32.5 นา25 ผัก41.2 บ้าน1.2)\n"
              "กฎ M2: เห็นน้ำลึกต่ำกว่า 1.20 ม. ก่อนหว่าน — งดรอบนั้น (นาและผักใช้เกณฑ์เดียวกัน)", fontsize=15.5)
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
ax1.set_title("แบบแนะนำ: สระ 22.5 : นา 35.9 : ไม้ผล 15 : ผัก 25 : บ้าน 1.6 (%) + ไก่ 40 ตัว + ปลานิล 2,880 ตัว/รอบ (2 ตัว/ตร.ม.)\n"
              "กฎเดียว 1.20 ม. + นาเปียกสลับแห้ง + เพดานแรงงานผัก 1 ไร่ + ยุ้งข้าว (ขายครึ่ง–เก็บครึ่ง)", fontsize=15)
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
ax2.annotate("ซื้อไก่ 40 ตัว + สร้างเล้า (18,000 บ.)\nพ.ค. ปีที่ 2 — กฎทบทวนประจำปี",
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

# ---------- F7: frontier ขนาดสระ ใต้เงื่อนไขครบ (v3) ----------
fr = J["pond_frontier"]
pn = [f["pond"] / 64 for f in fr]
Wv = [f["W"] / 1e6 for f in fr]
bf = [f["worstV"] for f in fr]
lbl = [f"{p:.1f}" for p in pn]
fig, ax = plt.subplots(figsize=(10.4, 5.8))
cols = ["#1c7a3c" if abs(p - 22.5) < 0.6 else "#a8c9a8" for p in pn]
bars = ax.bar(lbl, Wv, width=0.60, color=cols)
for b_, w in zip(bars, Wv):
    ax.text(b_.get_x() + b_.get_width() / 2, w + 0.008, f"{w:.2f}", ha="center", fontsize=11)
ax.set_ylim(2.00, 2.34)
ax.set_ylabel("ความมั่งคั่งปลายปีที่ 5 ปีปกติ (ล้านบาท)")
ax.set_xlabel("ขนาดสระ (% ของพื้นที่) — องค์ประกอบอื่นเลือกดีที่สุดภายใต้เงื่อนไขครบทุกข้อ")
ax.axhspan(min(Wv), max(Wv), color="#1c7a3c", alpha=0.07, zorder=0)
ax.text(0.5, 0.895, f"แถบเขียวอ่อน = ช่วงความมั่งคั่งทั้งหมด กว้างเพียง {max(Wv)-min(Wv):.3f} ล้านบาท (ต่างกันไม่ถึง 3 เปอร์เซ็นต์)",
        transform=ax.transAxes, ha="center", fontsize=13, color="#1c7a3c")
ax2 = ax.twinx()
ax2.plot(lbl, bf, "o-", color="#1f4e79", lw=2, ms=7, zorder=5)
ax2.set_ylabel("กันชนน้ำ: น้ำต่ำสุดร่วมทุกฉาก (ลบ.ม.)", color="#1f4e79")
ax2.tick_params(axis="y", labelcolor="#1f4e79")
ax2.set_ylim(0, 1250)
ax2.scatter([5], [393], s=160, facecolors="none", edgecolors="#b22222", lw=2, zorder=6)
ax2.annotate("แบบแนะนำ สระ 22.5%\nมั่งคั่งสูงสุด และกันชน 393", xy=(5.15, 393), xytext=(6.0, 205),
             fontsize=12.5, color="#b22222", arrowprops=dict(arrowstyle="->", color="#b22222"))
ax2.annotate("สระ 20% กันชนเหลือ 72", xy=(4, 72), xytext=(2.3, 95),
             fontsize=12.5, color="#b22222", arrowprops=dict(arrowstyle="->", color="#b22222"))
ax.set_title("เมื่อเงื่อนไขครบทุกข้อ ความมั่งคั่งแทบไม่ขึ้นกับขนาดสระ แต่กันชนน้ำต่างกันได้ถึง 11 เท่า\n"
             "ขนาดสระจึงต้องเลือกด้วยเกณฑ์ความทนทาน ไม่ใช่ด้วยผลตอบแทน", fontsize=15.5)
ax.grid(alpha=0.22, axis="y")
fig.tight_layout(); fig.savefig("out/fig_v3_frontier.png", bbox_inches="tight"); plt.close(fig)
print("saved fig_v3_frontier.png")
