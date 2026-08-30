# -*- coding: utf-8 -*-
"""สร้างรูปสรุปดัชนีโซบอลจาก out/sobol_results.json  (รัน sobol_analysis.py ก่อน)"""
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

J = json.load(open("out/sobol_results.json"))
NAMES = [p["name"] for p in J["params"]]
LBL = {"k_p": r"$k_p$ ถาดระเหย", "c": r"$c$ น้ำท่า", "r": r"$r$ ตัวคูณฝน",
       "y_R": r"$y_R$ ผลผลิตข้าว", "w_R": r"$w_R$ น้ำนา", "y_V": r"$y_V$ รายได้ผัก",
       "alpha_C_hi": r"$\alpha_C^{hi}$ ส่วนลดอาหารไก่", "alpha_F_0": r"$\alpha_F^{0}$ ส่วนลดอาหารปลา"}
KEYS = [k for k in J if isinstance(J[k], dict) and "Si" in J[k]]

# ใช้ลำดับเดียวกันทั้งสามแผง เพราะแกน y ร่วมกัน และเทียบข้ามแผงได้ง่ายกว่า
ORDER_NAMES = ["alpha_C_hi", "alpha_F_0", "y_R", "y_V", "w_R", "c", "k_p", "r"]
order = [NAMES.index(n) for n in ORDER_NAMES]
y = np.arange(len(order))

fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.2), sharey=True)
for ax, key in zip(axes, KEYS):
    d = J[key]
    Si, STi = np.array(d["Si"])[order], np.array(d["STi"])[order]
    lo, hi = np.array(d["STi_lo"])[order], np.array(d["STi_hi"])[order]
    ax.barh(y + 0.19, STi, height=0.36, color="#1f4e79", label=r"$S_{Ti}$ ดัชนีรวม")
    ax.barh(y - 0.19, Si, height=0.36, color="#7fb3d5", label=r"$S_i$ ลำดับที่หนึ่ง")
    ax.errorbar(STi, y + 0.19, xerr=np.abs(np.vstack([STi - lo, hi - STi])), fmt="none",
                ecolor="#0d2b45", elinewidth=1.1, capsize=2.5)
    for yi, v in zip(y, STi):
        if v >= 0.01:
            ax.text(v + 0.02, yi + 0.19, f"{v:.2f}", va="center", fontsize=12.5, color="#1f4e79")
    ax.set_xlim(0, 1.14)
    ax.set_xlabel("สัดส่วนของความแปรปรวนที่อธิบายได้")
    sd = d["std"]
    sd_txt = f"{sd:,.0f}" if abs(sd) >= 100 else f"{sd:,.2f}"
    ax.set_title(f"{key}\nส่วนเบี่ยงเบนมาตรฐาน $=$ {sd_txt}", fontsize=15)
    ax.grid(alpha=0.22, axis="x")
axes[0].set_yticks(y)
axes[0].set_yticklabels([LBL[NAMES[i]] for i in order])
axes[0].legend(loc="lower right", fontsize=13)
fig.suptitle("การวิเคราะห์ความไวเชิงโลกด้วยดัชนีโซบอล: ความมั่งคั่งกับความอยู่รอด "
             "ถูกขับด้วยพารามิเตอร์คนละชุดกันโดยสิ้นเชิง\n"
             f"(กวาด {J['n_base']:,} จุดฐาน รวมเรียกแบบจำลอง {J['n_eval']:,} ครั้ง; "
             r"แถบดำคือช่วงความเชื่อมั่น 90% ของ $S_{Ti}$)", fontsize=16.5)
fig.tight_layout(rect=[0, 0, 1, 0.90])
fig.savefig("out/fig_v3_sobol.png", bbox_inches="tight")
print("saved fig_v3_sobol.png")
