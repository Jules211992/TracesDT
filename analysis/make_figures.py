"""TRACES-DT -- figures 3 a 9, format IEEE une colonne (3.5 in).
Chaque figure lit uniquement les fichiers sources fournis (SHA-256 verifies contre le manifeste).
Aucune valeur simulee, interpolee ou estimee. Usage: python3 make_figures.py <DATA_DIR> <OUT_DIR>
"""
import sys, os, json, glob, csv, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

DATA, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

# ---------- Style IEEE commun ----------
for f in glob.glob("/usr/share/fonts/truetype/liberation/LiberationSerif-*.ttf"):
    font_manager.fontManager.addfont(f)
COL_W = 3.5  # in, largeur d'une colonne IEEE
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "Times"],
    "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "xtick.direction": "in", "ytick.direction": "in", "xtick.top": False, "ytick.right": False,
    "lines.linewidth": 1.0, "lines.markersize": 3.5,
    "axes.grid": True, "grid.linewidth": 0.35, "grid.linestyle": ":", "grid.color": "0.6",
    "axes.axisbelow": True,
    "legend.frameon": False, "legend.handlelength": 1.8, "legend.columnspacing": 1.0,
    "legend.handletextpad": 0.4, "legend.borderaxespad": 0.2,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 600,
    "hatch.linewidth": 0.5,
})
# Palette Okabe-Ito (sure pour daltoniens) + marqueurs/hachures distincts (lisible en N&B)
C = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "verm": "#D55E00",
     "sky": "#56B4E9", "purple": "#CC79A7", "yellow": "#F0E442", "grey": "#7F7F7F", "black": "#000000"}
METHOD_STYLE = {  # couleur, marqueur, hachure, style de ligne
    "B0": (C["verm"], "o", "////", "-"), "B1": (C["orange"], "s", "\\\\\\\\", "--"),
    "B2": (C["sky"], "^", "....", "-."), "B3": (C["blue"], "D", "", ":"),
}

def panel_label(ax, txt):
    ax.text(-0.13, 1.02, txt, transform=ax.transAxes, fontsize=8, fontweight="bold", va="bottom", ha="left")

def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(os.path.join(OUT, name + ".png"), bbox_inches="tight", pad_inches=0.02, dpi=600)
    plt.close(fig)

def save_exact(fig, name):  # largeur exacte d'une colonne IEEE (pas de bbox tight)
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=600)
    plt.close(fig)

LOG = []  # valeurs exactes tracees, pour verification
def log(fig, **kv):
    LOG.append({"figure": fig, **{k: (round(v, 6) if isinstance(v, float) else v) for k, v in kv.items()}})

def wilson(k, n, z=1.959963984540054):
    if n == 0: return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

# =====================================================================
# Fig. 3 -- R01, B0/A6/S3 : commande XMV(7) imposee apres la decision (10 graines)
# =====================================================================
def fig3():
    files = sorted(glob.glob(os.path.join(DATA, "FIG_3/R01/P09_B0_A6_S3_seed*_r0_result.json")))
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.13, 0.14, 0.855, 0.845])
    psv_drawn = nopsv_drawn = False
    for f in files:
        d = json.load(open(f))
        recs = d["override_records"]
        t0 = d["decision_sequence"]
        t = np.array([r["from_sequence"] - t0 for r in recs] + [recs[-1]["to_sequence"] - t0], float)
        ctrl = np.array([r["controller_value"] for r in recs], float)
        app = np.array([r["applied_value"] for r in recs], float)
        psv = bool(d["physical_outcome"]["Physical_Safety_Violation"])
        # escalier : chaque valeur appliquee est tenue de from_sequence a to_sequence
        y = np.append(app, app[-1])
        if psv:
            ax.step(t, y, where="post", color=C["verm"], lw=1.3, zorder=3,
                    label="Applied, PSV seed")
            ax.plot(t[:-1], ctrl, ls="--", color=C["verm"], lw=0.8, zorder=3,
                    label="Controller, PSV seed")
            psv_drawn = True
        else:
            ax.step(t, y, where="post", color=C["grey"], lw=0.7, alpha=0.8, zorder=2,
                    label=None if nopsv_drawn else "Applied, no-PSV seeds")
            nopsv_drawn = True
        log("Fig3", seed=d["seed"], psv=psv, n_records=len(recs), t_start=t[0], t_end=t[-1],
            applied_first=app[0], applied_last=app[-1], applied_min=app.min(),
            any_clipped=any(r["clipped"] for r in recs), sha256=hashlib.sha256(open(f, "rb").read()).hexdigest())
    ax.set_xlabel("Time since agent decision (s)")
    ax.set_ylabel("XMV(7) applied value (%)")
    ax.set_xlim(0, 30); ax.set_ylim(0, 45)
    box_legend(ax, loc="lower left", ncol=1)
    save_exact(fig, "Fig3_R01_B0_A6_S3_XMV7")

# =====================================================================
# Fig. 4 -- R01, barres groupees UPR / UER / PSV par methode (IC Wilson 95 %)
# =====================================================================
FIG_W, FIG_H = 3.5, 2.75  # meme dimension pour toutes les figures (une colonne IEEE)

def two_panel(left=0.15):
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    gs = fig.add_gridspec(2, 1, hspace=0.0, left=left, right=0.985, bottom=0.14, top=0.985)
    a1 = fig.add_subplot(gs[0]); a2 = fig.add_subplot(gs[1], sharex=a1)
    a1.tick_params(axis="x", labelbottom=False)
    return fig, a1, a2

def box_legend(ax, **kw):
    opts = dict(fontsize=6, frameon=True, fancybox=False, edgecolor="black", framealpha=1.0,
                handlelength=1.6, borderpad=0.35, labelspacing=0.25, columnspacing=0.8, borderaxespad=0.4)
    opts.update(kw)
    ax.legend(**opts).get_frame().set_linewidth(0.5)

def inner_label(ax, txt, x=0.015, y=0.965, ha="left"):
    ax.text(x, y, txt, transform=ax.transAxes, ha=ha, va="top", fontsize=7, fontweight="bold")

BRIGHT = {"blue": "#4477AA", "cyan": "#66CCEE", "green": "#228833", "yellow": "#CCBB44",
          "red": "#EE6677", "purple": "#AA3377", "grey": "#BBBBBB"}  # palette Paul Tol "bright"

def fig4():
    """Barres groupees (modele de reference) : UPR, UER, PSV par methode, IC de Wilson a 95 %."""
    df = pd.read_csv(os.path.join(DATA, "FIG_4/R01/R01_MASTER_RESULTS_v1.csv"))
    st = json.load(open(os.path.join(DATA, "FIG_4/R01/R01_STATISTICS_v1.json")))
    main = df[df.scope == "main"]
    metrics = ["UPR", "UER", "PSV"]; methods = ["B0", "B1", "B2", "B3"]
    cols = [BRIGHT["red"], BRIGHT["yellow"], BRIGHT["green"], BRIGHT["blue"]]
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.13, 0.14, 0.855, 0.845])
    w = 0.2; x = np.arange(len(metrics))
    for i, m in enumerate(methods):
        vals, lo, hi = [], [], []
        for met in metrics:
            sub = main[main.method == m][met]; k, n = int(sub.sum()), int(sub.count())
            bm = st["method_summaries"][m]["binary_metrics"][met]
            assert bm["numerator"] == k and bm["denominator"] == n
            ci = wilson(k, n)
            assert abs(ci[0] - bm["ci95_wilson"][0]) < 1e-9 and abs(ci[1] - bm["ci95_wilson"][1]) < 1e-9
            r = 100 * k / n; vals.append(r); lo.append(r - 100 * ci[0]); hi.append(100 * ci[1] - r)
            log("Fig4", method=m, metric=met, k=k, n=n, rate_pct=r, ci_lo_pct=100 * ci[0], ci_hi_pct=100 * ci[1])
        pos = x + (i - 1.5) * w
        ax.bar(pos, vals, w, color=cols[i], edgecolor="black", linewidth=0.3, zorder=2, label=m)
        ax.errorbar(pos, vals, yerr=[lo, hi], fmt="none", ecolor="black", elinewidth=0.6, capsize=1.6, zorder=3)
        for p_, v in zip(pos, vals):
            if v == 0:
                ax.plot(p_, 0, marker="x", ms=3.2, mew=0.9, color=cols[i], zorder=4, clip_on=False)
    ax.set_xticks(x); ax.set_xticklabels(metrics); ax.set_xlabel("Metric")
    ax.set_ylabel("Rate (%)"); ax.set_ylim(0, 35); ax.set_yticks([0, 5, 10, 15, 20, 25, 30])
    ax.set_xlim(-0.55, 2.55)
    ax.grid(axis="x", visible=False); ax.grid(axis="y", linestyle="--", linewidth=0.4, color="0.7")
    box_legend(ax, loc="upper right", ncol=4, handlelength=1.2)
    save_exact(fig, "Fig4_R01_UPR_UER_PSV")

# =====================================================================
# Fig. 5 -- Latence par tour vs N (fichier historique fig5_latency_scalability)
# =====================================================================
def fig5():
    # Barres groupees et empilees : T_round = T_local + surcout post-local (verifie ci-dessous).
    df = pd.read_csv(os.path.join(DATA, "FIG_5/HISTORY/11506_fig5_latency_scalability.csv"))
    resid = (df.T_local_mean_ms + df.post_local_system_mean_ms - df.T_round_mean_ms).abs().max()
    assert resid < 1e-3, resid
    Ns = sorted(df.N.unique()); methods = ["B0", "B1", "B2", "B3"]
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.13, 0.14, 0.855, 0.845])
    x = np.arange(len(Ns)); w = 0.2
    for j, b in enumerate(methods):
        col, _, ht, _ = METHOD_STYLE[b]
        s = df[df.baseline == b].set_index("N").loc[Ns]
        pos = x + (j - 1.5) * w
        loc_s = s.T_local_mean_ms.values / 1e3; ovh = s.post_local_system_mean_ms.values / 1e3
        ax.bar(pos, loc_s, w, color="0.88", edgecolor="black", linewidth=0.4, zorder=2)
        ax.bar(pos, ovh, w, bottom=loc_s, color=col, edgecolor="black", linewidth=0.4, hatch=ht, zorder=2, label=b)
        ax.errorbar(pos, s.T_round_mean_ms.values / 1e3, yerr=s.T_round_sd_ms.values / 1e3, fmt="none",
                    ecolor="black", elinewidth=0.6, capsize=1.4, zorder=3)
        for n_, r in s.iterrows():
            log("Fig5", baseline=b, N=int(n_), T_local_s=r.T_local_mean_ms / 1e3,
                post_local_s=r.post_local_system_mean_ms / 1e3, T_round_mean_s=r.T_round_mean_ms / 1e3,
                T_round_sd_s=r.T_round_sd_ms / 1e3, sum_check_ms=r.T_local_mean_ms + r.post_local_system_mean_ms - r.T_round_mean_ms)
    from matplotlib.patches import Patch
    h, l = ax.get_legend_handles_labels()
    h = [Patch(facecolor="0.88", edgecolor="black", linewidth=0.4)] + h
    l = ["Local"] + [f"{m} overhead" for m in l]
    box_legend(ax, handles=h, labels=l, loc="upper left", ncol=3, handlelength=1.4)
    ax.set_xticks(x); ax.set_xticklabels([str(int(n)) for n in Ns]); ax.set_xlabel("$N$")
    ax.set_ylabel("Round latency (s)"); ax.set_ylim(0, 115); ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_xlim(-0.55, len(Ns) - 0.45); ax.grid(axis="x", visible=False)
    save_exact(fig, "Fig5_latency_vs_N")

# =====================================================================
# Fig. 6 -- IPFS historique : latences et debits vs taille d'objet (R0)
# =====================================================================
def fig6():
    """(a) latences en courbes ; (b) debits en barres groupees (modele de reference), echelle log."""
    df = pd.read_csv(os.path.join(DATA, "FIG_6/HISTORY/11393_ipfs_benchmark_summary.csv"))
    assert (df[["add_success", "get_success", "replication_success", "cid_consistent", "hash_consistent"]] == 1).all().all()
    df = df.sort_values("size_bytes").reset_index(drop=True)
    x = np.arange(len(df)); labs = [l.replace("KB", "K").replace("MB", "M") for l in df.size_label]
    cW, cR, cP = "#EE7733", "#009988", "#33BBEE"  # palette Paul Tol "vibrant"
    fig, a1, a2 = two_panel(left=0.15)
    a1.plot(x, df.add_latency_s * 1e3, color=cW, marker="o", ms=3, label="Add")
    a1.plot(x, df.get_latency_s * 1e3, color=cR, marker="s", ms=3, ls="--", mfc="white", label="Get")
    a1.plot(x, df.replication_convergence_s * 1e3, color=cP, marker="^", ms=3, ls="-.", label="Replication")
    w = 0.38
    a2.bar(x - w / 2, df.write_throughput_mib_s, w, color=cW, edgecolor="black", linewidth=0.3, zorder=2, label="Write")
    a2.bar(x + w / 2, df.read_throughput_mib_s, w, color=cR, edgecolor="black", linewidth=0.3, zorder=2, label="Read")
    for _, r in df.iterrows():
        log("Fig6", size=r.size_label, n=int(r.n), add_ms=r.add_latency_s * 1e3, get_ms=r.get_latency_s * 1e3,
            repl_ms=r.replication_convergence_s * 1e3, write_MiBs=r.write_throughput_mib_s, read_MiBs=r.read_throughput_mib_s)
    a1.set_ylabel("Latency (ms)"); a1.set_ylim(0, 800); a1.set_yticks([0, 200, 400, 600])
    a2.set_ylabel("Throughput (MiB/s)"); a2.set_yscale("log"); a2.set_ylim(3e-3, 1e3)
    a2.set_yticks([1e-2, 1e-1, 1, 10, 100]); a2.minorticks_off()
    a2.set_xticks(x); a2.set_xticklabels(labs, fontsize=6.5); a2.set_xlabel("Object size (bytes)")
    a2.set_xlim(-0.6, len(df) - 0.4)
    for a in (a1, a2): a.grid(axis="x", visible=False)
    a2.grid(axis="y", linestyle="--", linewidth=0.4, color="0.7")
    box_legend(a1, loc="upper left", bbox_to_anchor=(0.09, 1.0), ncol=1)
    box_legend(a2, loc="upper left", bbox_to_anchor=(0.09, 1.0), ncol=2)
    inner_label(a1, "(a)"); inner_label(a2, "(b)")
    save_exact(fig, "Fig6_IPFS_size_sweep")

# =====================================================================
# Fig. 7 -- B3/A1/S1 : composantes temporelles mesurees par graine (barres horizontales empilees)
# =====================================================================
def fig7():
    files = sorted(glob.glob(os.path.join(DATA, "FIG_7/R01/P09_B3_A1_S1_seed*_r0_result.json")))
    seeds, agent, guard = [], [], []
    for f in files:
        d = json.load(open(f))
        assert d["fabric"] is False and d["ipfs"] is False
        seeds.append(str(d["seed"])); agent.append(d["agent"]["decision_latency_ms"] / 1e3)
        guard.append(d["method_result"]["safeguard_latency_ms"] / 1e3)
        log("Fig7", seed=d["seed"], agent_s=agent[-1], safeguard_ms=d["method_result"]["safeguard_latency_ms"],
            final_action=d["final_action"], fabric=d["fabric"], ipfs=d["ipfs"])
    y = np.arange(len(seeds))[::-1]
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.235, 0.14, 0.75, 0.845])
    ax.barh(y, agent, 0.66, color=C["sky"], edgecolor="black", linewidth=0.4, label="Agent inference", zorder=2)
    ax.barh(y, guard, 0.66, left=agent, color=C["verm"], edgecolor=C["verm"], linewidth=1.2,
            label="B3 safeguard check", zorder=3)
    ax.set_yticks(y); ax.set_yticklabels(seeds, fontsize=6.5); ax.set_ylabel("Seed")
    ax.set_ylim(-0.6, len(seeds) - 0.4)
    ax.set_xlabel("Measured latency (s)"); ax.set_xlim(0, 60)
    ax.grid(axis="y", visible=False)
    box_legend(ax, loc="lower right", ncol=1)
    save_exact(fig, "Fig7_B3_A1_S1_latency_components")

# =====================================================================
# Fig. 8 -- R10 (gel de preuves) : deux panneaux de barres
# =====================================================================
def fig8():
    fr = json.load(open(os.path.join(DATA, "FIG_8/MAC/R10_EVIDENCE_FREEZE.json")))
    assert fr["status"] == "R10_EVIDENCE_FREEZE_PASS"
    agg = fr["R10_S4"]["aggregate"]
    perts = ["SINGLE_7", "SINGLE_12", "JOINT_7_12", "JOINT_5_REF"]
    labels = ["XMEAS(7)", "XMEAS(12)", "XMEAS(7,12)", "5 refs."]
    set_cols = [C["blue"], C["green"], C["purple"], C["orange"]]  # une couleur par jeu de mesures
    fig, a1, a2 = two_panel()
    x = np.arange(len(perts)); w = 0.36
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    for ax, key in ((a1, "decision_changes"), (a2, "eligibility_changes")):
        for j, rt in enumerate(("HONEST_AGE", "FORGED_FRESH")):
            for k, p in enumerate(perts):
                cnt, n = agg[p][rt][key], agg[p][rt]["cases"]
                pct = 100.0 * cnt / n; pos = x[k] + (j - 0.5) * w
                if j == 0:
                    ax.bar(pos, pct, w, color=set_cols[k], edgecolor="black", linewidth=0.4, zorder=2)
                else:
                    ax.bar(pos, pct, w, color="white", edgecolor=set_cols[k], linewidth=0.9, hatch="//////", zorder=2)
                if cnt == 0:  # rend visible un compte nul
                    ax.plot(pos, 0, marker="x", ms=3.5, mew=0.9, color=set_cols[k], zorder=4, clip_on=False)
                log("Fig8", perturbation=p, replay=rt, metric=key, count=cnt, cases=n, pct=pct)
        ax.set_ylim(0, 140); ax.set_yticks([0, 25, 50, 75, 100])
        ax.grid(axis="x", visible=False)
    a1.set_ylabel("Decision chg. (%)"); a2.set_ylabel("Eligibility chg. (%)")
    a2.set_xticks(x); a2.set_xticklabels(labels); a2.set_xlabel("Replayed measurement set")
    a2.set_xlim(-0.6, len(perts) - 0.4)
    h = [Patch(facecolor="0.55", edgecolor="black", linewidth=0.4),
         Patch(facecolor="white", edgecolor="0.3", linewidth=0.9, hatch="//////"),
         Line2D([], [], ls="none", marker="x", ms=3.5, mew=0.9, color="0.3")]
    box_legend(a1, handles=h, labels=["Honest aged", "Forged fresh", "Zero"], loc="upper right", ncol=3,
               handlelength=1.4)
    inner_label(a1, "(a)"); inner_label(a2, "(b)")
    save_exact(fig, "Fig8_R10_S4_replay")

# =====================================================================
# Fig. 9 -- R12 Qwen authentique : flux d'actions (a) et distribution du temps de generation (b)
# =====================================================================
def fig9():
    df = pd.read_csv(os.path.join(DATA, "FIG_9/MAC/R12_QWEN_30_ROWS.csv"))
    sm = json.load(open(os.path.join(DATA, "FIG_9/MAC/R12_QWEN_SUMMARY.json")))
    # recoupement CSV <-> JSON par graine
    per = {}
    for f in sorted(glob.glob(os.path.join(DATA, "FIG_9/MAC/R12_QWEN_seed*.json"))):
        d = json.load(open(f)); per[d["seed"]] = d
        assert d["actual_model_call"] is True and d["constructed_agent_proposal"] is False
    assert len(per) == 30 == len(df) == sm["count"]
    for _, r in df.iterrows():
        d = per[r.seed]
        assert d["action_id"] == r.action and d["v3_decision"] == r.decision and d["v3_effective_action"] == r.effective_action
        assert abs(d["generation_ms"] - r.generation_ms) < 1e-6
    # Mise en page IEEE une colonne (3.5 in exact) : bande d'actions par graine (haut),
    # temps de generation par graine (bas gauche), boite a moustaches marginale (bas droite).
    df = df.sort_values("seed").reset_index(drop=True)
    idx = np.arange(1, len(df) + 1)
    W, H = 3.5, 2.75
    fig = plt.figure(figsize=(W, H))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.62, 1.7], width_ratios=[5.6, 0.85],
                          hspace=0.0, wspace=0.0, left=0.285, right=0.985, bottom=0.14, top=0.985)
    a1 = fig.add_subplot(gs[0, 0]); a2 = fig.add_subplot(gs[1, 0], sharex=a1)
    a3 = fig.add_subplot(gs[1, 1], sharey=a2)
    # (a) bande categorielle : une cellule par graine et par etape
    rows = [("action", "Proposal"), ("decision", "Safeguard"), ("effective_action", "Effective")]
    cols = [C["verm"], C["blue"], C["green"]]
    hatches = ["////", "", "...."]
    ylabels = []
    for i, ((colname, name), col, ht) in enumerate(zip(rows, cols, hatches)):
        y = 2 - i
        cats = df[colname].unique()
        assert len(cats) == 1  # verifie : une seule categorie par etape dans R12
        a1.barh(np.full(len(idx), y), np.ones(len(idx)), left=idx - 0.5, height=0.78, color=col,
                edgecolor="white", linewidth=0.5, hatch=ht, zorder=2)
        ylabels.append(f"{name}: {cats[0]}")
        log("Fig9a", stage=name, category=cats[0], count=int((df[colname] == cats[0]).sum()))
    a1.set_yticks([2, 1, 0]); a1.set_yticklabels(ylabels, fontsize=6.5)
    a1.tick_params(axis="y", pad=2)
    a1.set_ylim(-0.55, 2.55); a1.grid(False)
    a1.tick_params(axis="x", bottom=False, labelbottom=False)
    a1.tick_params(axis="y", length=0)
    # (b) temps de generation par graine ; marqueur selon la sortie brute (modale ou non)
    g = df.generation_ms.values / 1e3
    modal = df.raw_output_sha256 == df.raw_output_sha256.mode()[0]
    med = float(np.median(g))
    for k in range(len(df)):
        log("Fig9b_seeds", seed_index=int(idx[k]), seed=int(df.seed[k]), generation_s=float(g[k]),
            modal_raw_output=bool(modal[k]), raw_output_sha256=df.raw_output_sha256[k])
    a2.axhline(med, color=C["verm"], ls="--", lw=0.9, zorder=3, label="Median")
    a2.bar(idx[modal], g[modal], 0.78, color=C["sky"], edgecolor="black", linewidth=0.4,
           zorder=2, label="Modal output")
    a2.bar(idx[~modal], g[~modal], 0.78, color="white", edgecolor=C["blue"], linewidth=0.6,
           hatch="//////", zorder=2, label="Other outputs")
    a2.set_xlim(0.5, len(idx) + 0.5); a2.set_xticks([1, 5, 10, 15, 20, 25, 30])
    a2.set_xlabel("Seed index"); a2.set_ylabel("Generation time (s)")
    a2.set_ylim(0, 60); a2.set_yticks([0, 10, 20, 30, 40, 50, 60])
    a2.grid(axis="x", visible=False)
    a2.legend(loc="upper center", ncol=3, columnspacing=0.8, fontsize=6, frameon=True, fancybox=False, edgecolor="black",
              framealpha=1.0, handlelength=1.5, borderpad=0.35, labelspacing=0.25,
              borderaxespad=0.4).get_frame().set_linewidth(0.5)
    # (c) boite a moustaches marginale (meme axe y)
    a3.boxplot(g, positions=[0], widths=0.55, patch_artist=True, showfliers=True,
               boxprops=dict(facecolor=C["sky"], edgecolor="black", linewidth=0.5),
               medianprops=dict(color=C["verm"], linewidth=1.0),
               whiskerprops=dict(linewidth=0.5), capprops=dict(linewidth=0.5),
               flierprops=dict(marker="D", markersize=2.6, mfc="white", mec="black", mew=0.5))
    a3.set_xlim(-0.6, 0.6); a3.set_xticks([])
    a3.tick_params(axis="y", left=False, labelleft=False)
    a3.grid(axis="x", visible=False)
    a0 = fig.add_subplot(gs[0, 1]); a0.axis("off")
    a0.text(0.5, 0.5, "(a)", transform=a0.transAxes, ha="center", va="center", fontsize=7, fontweight="bold")
    a3.text(0.5, 0.975, "(b)", transform=a3.transAxes, ha="center", va="top", fontsize=7, fontweight="bold")
    log("Fig9b", n=len(g), min_s=float(g.min()), median_s=med, mean_s=float(g.mean()), max_s=float(g.max()),
        q1_s=float(np.percentile(g, 25)), q3_s=float(np.percentile(g, 75)),
        distinct_raw_outputs=int(df.raw_output_sha256.nunique()))
    save_exact(fig, "Fig9_R12_Qwen_flow_latency")

# =====================================================================
# Variantes de mise en page (Fig. 3 et Fig. 7)
# =====================================================================
def fig3b():
    """Carte de chaleur : une ligne par graine, une colonne par seconde, couleur = XMV(7) applique."""
    files = sorted(glob.glob(os.path.join(DATA, "FIG_3/R01/P09_B0_A6_S3_seed*_r0_result.json")))
    M, seeds, psv_rows = [], [], []
    for i, f in enumerate(files):
        d = json.load(open(f)); recs = d["override_records"]; t0 = d["decision_sequence"]
        assert [r["from_sequence"] - t0 for r in recs] == list(range(30))  # pas de 1 s, sans trou
        M.append([r["applied_value"] for r in recs]); seeds.append(str(d["seed"]))
        if d["physical_outcome"]["Physical_Safety_Violation"]: psv_rows.append(i)
    M = np.array(M)
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.205, 0.14, 0.64, 0.845]); cax = fig.add_axes([0.865, 0.14, 0.03, 0.845])
    im = ax.imshow(M, aspect="auto", cmap="viridis", vmin=0, vmax=45, origin="upper",
                   extent=[0, 30, len(seeds) - 0.5, -0.5], interpolation="nearest")
    for r in psv_rows:
        ax.add_patch(matplotlib.patches.Rectangle((0, r - 0.5), 30, 1, fill=False, edgecolor=C["verm"],
                                                  linewidth=1.4, zorder=3))
    ax.set_yticks(range(len(seeds))); ax.set_yticklabels(seeds, fontsize=6.5); ax.set_ylabel("Seed")
    ax.set_xlabel("Time since agent decision (s)"); ax.set_xticks([0, 5, 10, 15, 20, 25, 30])
    ax.grid(False); ax.tick_params(direction="out")
    cb = fig.colorbar(im, cax=cax); cb.set_label("XMV(7) applied value (%)", fontsize=7)
    cb.ax.tick_params(labelsize=6.5, direction="out"); cb.outline.set_linewidth(0.5)
    for r in psv_rows:  # ligne PSV signalee par l'etiquette (rouge, gras) et le cadre, sans legende
        lab = ax.get_yticklabels()[r]; lab.set_color(C["verm"]); lab.set_fontweight("bold")
    save_exact(fig, "Fig3_ALT_heatmap")

def fig7b():
    """Graphique a points (echelle log) : inference de l'agent vs verification du garde-fou B3."""
    files = sorted(glob.glob(os.path.join(DATA, "FIG_7/R01/P09_B3_A1_S1_seed*_r0_result.json")))
    seeds, agent, guard = [], [], []
    for f in files:
        d = json.load(open(f)); assert d["fabric"] is False and d["ipfs"] is False
        seeds.append(str(d["seed"])); agent.append(d["agent"]["decision_latency_ms"] / 1e3)
        guard.append(d["method_result"]["safeguard_latency_ms"] / 1e3)
    y = np.arange(len(seeds))[::-1]
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.235, 0.14, 0.75, 0.845])
    ax.hlines(y, guard, agent, color="0.7", lw=0.8, zorder=1)
    ax.plot(guard, y, ls="none", marker="D", ms=3.6, mfc=C["verm"], mec="black", mew=0.4, zorder=3,
            label="B3 safeguard check")
    ax.plot(agent, y, ls="none", marker="o", ms=4.0, mfc=C["blue"], mec="black", mew=0.4, zorder=3,
            label="Agent inference")
    ax.set_xscale("log"); ax.set_xlim(2e-5, 5e2)
    ax.set_xticks([1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100]); ax.minorticks_off()
    ax.set_yticks(y); ax.set_yticklabels(seeds, fontsize=6.5); ax.set_ylabel("Seed")
    ax.set_ylim(-1.9, len(seeds) - 0.4)  # bande libre en bas pour la legende interne
    ax.set_xlabel("Measured latency (s, log scale)")
    ax.grid(axis="y", visible=False)
    box_legend(ax, loc="lower center", ncol=2)
    save_exact(fig, "Fig7_ALT_log_dotplot")

def fig3c():
    """Enveloppe min-max et mediane des 9 graines sans PSV + graine PSV (appliquee et controleur)."""
    files = sorted(glob.glob(os.path.join(DATA, "FIG_3/R01/P09_B0_A6_S3_seed*_r0_result.json")))
    nop, psv_app, psv_ctrl = [], None, None
    for f in files:
        d = json.load(open(f)); recs = d["override_records"]; t0 = d["decision_sequence"]
        assert [r["from_sequence"] - t0 for r in recs] == list(range(30))
        app = np.array([r["applied_value"] for r in recs]); ctrl = np.array([r["controller_value"] for r in recs])
        if d["physical_outcome"]["Physical_Safety_Violation"]: psv_app, psv_ctrl = app, ctrl
        else: nop.append(app)
    nop = np.array(nop); assert nop.shape == (9, 30) and psv_app is not None
    t = np.arange(30)
    lo, hi, med = nop.min(0), nop.max(0), np.median(nop, 0)
    ext = lambda v: np.append(v, v[-1])  # tient la derniere valeur jusqu'a t = 30 s (to_sequence)
    te = np.arange(31)
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.13, 0.14, 0.855, 0.845])
    ax.fill_between(te, ext(lo), ext(hi), step="post", color="0.82", lw=0, zorder=1, label="No-PSV seeds, range")
    ax.step(te, ext(med), where="post", color="0.25", lw=1.0, zorder=2, label="No-PSV seeds, median")
    ax.step(te, ext(psv_app), where="post", color=C["verm"], lw=1.4, zorder=3, label="PSV seed, applied")
    ax.plot(t, psv_ctrl, color=C["blue"], ls="--", lw=0.9, zorder=3, label="PSV seed, controller")
    ax.set_xlim(0, 30); ax.set_xticks([0, 5, 10, 15, 20, 25, 30])
    ax.set_ylim(0, 45); ax.set_yticks([0, 10, 20, 30, 40])
    ax.set_xlabel("Time since agent decision (s)"); ax.set_ylabel("XMV(7) applied value (%)")
    box_legend(ax, loc="lower left")
    for i in range(30):
        log("Fig3c", t_s=int(t[i]), nopsv_min=float(lo[i]), nopsv_median=float(med[i]), nopsv_max=float(hi[i]),
            psv_applied=float(psv_app[i]), psv_controller=float(psv_ctrl[i]))
    save_exact(fig, "Fig3_ALT2_envelope")

def fig7c():
    """Meme construction que la Fig. 9 : (a) garde-fou B3 en ms, (b) inference en s, une barre par graine."""
    files = sorted(glob.glob(os.path.join(DATA, "FIG_7/R01/P09_B3_A1_S1_seed*_r0_result.json")))
    agent, guard = [], []
    for f in files:
        d = json.load(open(f)); assert d["fabric"] is False and d["ipfs"] is False
        agent.append(d["agent"]["decision_latency_ms"] / 1e3); guard.append(d["method_result"]["safeguard_latency_ms"])
    agent, guard = np.array(agent), np.array(guard); idx = np.arange(1, len(agent) + 1)
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.8, 1.5], width_ratios=[5.6, 0.85], hspace=0.0, wspace=0.0,
                          left=0.15, right=0.985, bottom=0.14, top=0.985)
    a1 = fig.add_subplot(gs[0, 0]); a2 = fig.add_subplot(gs[1, 0], sharex=a1)
    b1 = fig.add_subplot(gs[0, 1], sharey=a1); b2 = fig.add_subplot(gs[1, 1], sharey=a2)
    a1.bar(idx, guard, 0.7, color=C["verm"], edgecolor="black", linewidth=0.4, hatch="////", zorder=2,
           label="B3 safeguard check")
    a1.axhline(np.median(guard), color="0.2", ls="--", lw=0.8, zorder=3, label="Median")
    a2.bar(idx, agent, 0.7, color=C["sky"], edgecolor="black", linewidth=0.4, zorder=2, label="Agent inference")
    a2.axhline(np.median(agent), color="0.2", ls="--", lw=0.8, zorder=3, label="Median")
    a1.set_ylim(0, 0.16); a1.set_yticks([0, 0.05, 0.10]); a1.set_ylabel("Check (ms)")
    a2.set_ylim(0, 70); a2.set_yticks([0, 20, 40, 60]); a2.set_ylabel("Inference (s)")
    a1.tick_params(axis="x", labelbottom=False)
    a2.set_xlim(0.4, len(idx) + 0.6); a2.set_xticks(idx); a2.set_xlabel("Seed index")
    for a in (a1, a2): a.grid(axis="x", visible=False)
    for b, v, col, ht in ((b1, guard, C["verm"], "////"), (b2, agent, C["sky"], "")):
        b.boxplot(v, positions=[0], widths=0.55, patch_artist=True,
                  boxprops=dict(facecolor=col, edgecolor="black", linewidth=0.5, hatch=ht),
                  medianprops=dict(color="black", linewidth=1.0), whiskerprops=dict(linewidth=0.5),
                  capprops=dict(linewidth=0.5), flierprops=dict(marker="D", markersize=2.6, mfc="white", mec="black", mew=0.5))
        b.set_xlim(-0.6, 0.6); b.set_xticks([]); b.tick_params(axis="y", left=False, labelleft=False)
        b.grid(axis="x", visible=False)
    box_legend(a1, loc="upper left", ncol=2); box_legend(a2, loc="upper right", ncol=2)
    inner_label(b1, "(a)", x=0.5, ha="center"); inner_label(b2, "(b)", x=0.5, ha="center")
    save_exact(fig, "Fig7_ALT2_two_scales")

def fig3d():
    """Style Fig. 9 : (a) ecart graine PSV - mediane sans PSV (pp) ; (b) XMV(7) par seconde ;
    marges : boites a moustaches. Donnees : override_records des 10 graines B0/A6/S3."""
    files = sorted(glob.glob(os.path.join(DATA, "FIG_3/R01/P09_B0_A6_S3_seed*_r0_result.json")))
    nop, psv = [], None
    for f in files:
        d = json.load(open(f)); recs = d["override_records"]; t0 = d["decision_sequence"]
        assert [r["from_sequence"] - t0 for r in recs] == list(range(30))
        app = np.array([r["applied_value"] for r in recs])
        if d["physical_outcome"]["Physical_Safety_Violation"]: psv = app
        else: nop.append(app)
    nop = np.array(nop); assert nop.shape == (9, 30) and psv is not None
    med, lo, hi = np.median(nop, 0), nop.min(0), nop.max(0)
    dev = psv - med
    t = np.arange(30) + 0.5  # centre de chaque intervalle d'une seconde
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.8, 1.5], width_ratios=[5.6, 0.85], hspace=0.0, wspace=0.0,
                          left=0.15, right=0.985, bottom=0.14, top=0.985)
    a1 = fig.add_subplot(gs[0, 0]); a2 = fig.add_subplot(gs[1, 0], sharex=a1)
    b1 = fig.add_subplot(gs[0, 1], sharey=a1); b2 = fig.add_subplot(gs[1, 1], sharey=a2)
    # (a) ecart signe
    neg = dev < 0
    a1.bar(t[neg], dev[neg], 0.8, color=C["blue"], edgecolor="black", linewidth=0.3, zorder=2, label="Below median")
    a1.bar(t[~neg], dev[~neg], 0.8, color=C["verm"], edgecolor="black", linewidth=0.3, hatch="////", zorder=2,
           label="Above median")
    a1.axhline(0, color="black", lw=0.6, zorder=3)
    a1.set_ylim(-8, 8); a1.set_yticks([-5, 0, 5]); a1.set_ylabel("Gap (pp)")
    a1.tick_params(axis="x", labelbottom=False)
    # (b) valeurs par seconde : mediane sans PSV (barres + plage min-max) et graine PSV (losanges)
    a2.bar(t, med, 0.8, color="0.85", edgecolor="black", linewidth=0.3, zorder=2, label="No-PSV median")
    a2.errorbar(t, med, yerr=[med - lo, hi - med], fmt="none", ecolor="0.35", elinewidth=0.5, capsize=0.8,
                zorder=3, label="No-PSV range")
    a2.plot(t, psv, ls="none", marker="D", ms=2.6, mfc=C["verm"], mec="black", mew=0.35, zorder=4, label="PSV seed")
    a2.set_ylim(0, 50); a2.set_yticks([0, 10, 20, 30, 40]); a2.set_ylabel("XMV(7) (%)")
    a2.set_xlim(0, 30); a2.set_xticks([0, 5, 10, 15, 20, 25, 30]); a2.set_xlabel("Time since agent decision (s)")
    for a in (a1, a2): a.grid(axis="x", visible=False)
    # marges : distribution sur les 30 s
    for b, v, col, ht in ((b1, dev, C["verm"], "////"), (b2, psv, C["verm"], "")):
        b.boxplot(v, positions=[0], widths=0.55, patch_artist=True,
                  boxprops=dict(facecolor="white" if ht else col, edgecolor="black", linewidth=0.5, hatch=ht),
                  medianprops=dict(color="black", linewidth=1.0), whiskerprops=dict(linewidth=0.5),
                  capprops=dict(linewidth=0.5), flierprops=dict(marker="D", markersize=2.4, mfc="white", mec="black", mew=0.5))
        b.set_xlim(-0.6, 0.6); b.set_xticks([]); b.tick_params(axis="y", left=False, labelleft=False)
        b.grid(axis="x", visible=False)
    box_legend(a1, loc="lower left", ncol=2)
    box_legend(a2, loc="upper right", ncol=1)
    inner_label(b1, "(a)", x=0.5, ha="center"); inner_label(b2, "(b)", x=0.5, ha="center")
    for i in range(30):
        log("Fig3d", t_s=i, nopsv_min=float(lo[i]), nopsv_median=float(med[i]), nopsv_max=float(hi[i]),
            psv_applied=float(psv[i]), gap_pp=float(dev[i]))
    save_exact(fig, "Fig3_ALT3_fig9style")

# =====================================================================
# Fig. 10 -- Hyperledger Fabric : (a) controle d'autorisation R07A, (b) resilience P14
# P13 exclu : statut Fabric enregistre = "failed".
# =====================================================================
def fig10():
    r = pd.read_csv(os.path.join(DATA, "FIG_5/HISTORY/06425_R07A_B3_FABRIC_RESULTS_v1.csv"))
    r = r.sort_values(["seed", "scenario"]).reset_index(drop=True)
    assert len(r) == 20 and (r.method == "B3").all() and (r.technical_valid == 1).all()
    p14 = json.load(open(os.path.join(DATA, "FIG_5/HISTORY/00150_P14_FABRIC_RESILIENCE_SUMMARY.json")))
    conds = [("Baseline", p14["baseline"]), ("One peer down", p14["resilience"]["one_peer_down"]),
             ("One orderer down", p14["resilience"]["one_orderer_down"])]
    for _, c in conds:
        assert c["ok"] and c["read_status"] == "success" and c["write_status"] == "success" and c["caliper_exit"] == 0
    idx = np.arange(1, len(r) + 1)
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.75, 1.55], width_ratios=[5.6, 0.85], hspace=0.0, wspace=0.0,
                          left=0.285, right=0.985, bottom=0.14, top=0.88)
    a1 = fig.add_subplot(gs[0, 0]); a2 = fig.add_subplot(gs[1, 0])
    l1 = fig.add_subplot(gs[0, 1]); l2 = fig.add_subplot(gs[1, 1])
    for l in (l1, l2):
        l.axis("off")
    # (a) une case par invocation : action autorisee acceptee (rc=0), action substituee rejetee (rc!=0)
    rows = [("Authorized action", r.correct_control_rc == 0, C["green"], "", "accepted"),
            ("Substituted action", r.wrong_invoke_rc != 0, C["verm"], "////", "rejected")]
    for i, (name, ok, col, ht, _) in enumerate(rows):
        y = 1 - i
        a1.barh(np.full(len(idx), y), np.ones(len(idx)), left=idx - 0.5, height=0.78, color=col,
                edgecolor="white", linewidth=0.5, hatch=ht, zorder=2)
        assert ok.all()
    for k_, row in r.iterrows():
        log("Fig10a", event_index=k_ + 1, seed=int(row.seed), scenario=row.scenario,
            authorized=row.authorized_action, substituted=row.substituted_action,
            correct_control_rc=int(row.correct_control_rc), wrong_invoke_rc=int(row.wrong_invoke_rc))
    a1.set_yticks([1, 0]); a1.set_yticklabels(["Authorized: accepted", "Substituted: rejected"], fontsize=6.5)
    a1.set_ylim(-0.55, 1.55); a1.set_xlim(0.5, len(idx) + 0.5); a1.grid(False)
    a1.set_xticks([1, 5, 10, 15, 20])
    a1.xaxis.tick_top(); a1.xaxis.set_label_position("top")
    a1.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False)
    a1.tick_params(axis="y", length=0, pad=2)
    a1.set_xlabel("Fabric invocation event", labelpad=2)
    # (b) latence d'ecriture/lecture Caliper par condition (une mesure par condition)
    lat = [int(c["latency_ns"]) / 1e9 for _, c in conds]
    cols = ["0.80", C["blue"], C["blue"]]; hts = ["", "////", "////"]
    xb = np.arange(len(conds))
    for j in range(len(conds)):
        a2.bar(xb[j], lat[j], 0.55, color=cols[j], edgecolor="black", linewidth=0.4, hatch=hts[j], zorder=2,
               label="Fault-free" if j == 0 else ("Single-node fault" if j == 1 else None))
        log("Fig10b", condition=conds[j][0], latency_s=lat[j], read=conds[j][1]["read_status"],
            write=conds[j][1]["write_status"], n=1)
    a2.set_yscale("log"); a2.set_ylim(0.1, 300); a2.set_yticks([0.1, 1, 10, 100]); a2.minorticks_off()
    a2.set_ylabel("Latency (s)")
    a2.set_xticks(xb); a2.set_xticklabels([c[0] for c in conds], fontsize=6.5)
    a2.set_xlim(-0.6, len(conds) - 0.4); a2.grid(axis="x", visible=False)
    box_legend(a2, loc="upper left")
    l1.text(0.5, 0.5, "(a)", ha="center", va="center", fontsize=7, fontweight="bold", transform=l1.transAxes)
    l2.text(0.5, 0.94, "(b)", ha="center", va="top", fontsize=7, fontweight="bold", transform=l2.transAxes)
    save_exact(fig, "Fig10_Fabric_authorization_resilience")

def fig10b():
    """Contenu de FIG10_FABRIC (P14 latence + controles negatifs R07A et P14) dans le style valide.
    Les deux protocoles restent separes (lignes distinctes, pas de cumul)."""
    r = pd.read_csv(os.path.join(DATA, "FIG_5/HISTORY/06425_R07A_B3_FABRIC_RESULTS_v1.csv"))
    assert len(r) == 20 and (r.wrong_invoke_rc == 1).all() and (r.correct_control_rc == 0).all() and (r.technical_valid == 1).all()
    p14 = json.load(open(os.path.join(DATA, "FIG_5/HISTORY/00150_P14_FABRIC_RESILIENCE_SUMMARY.json")))
    da = p14["distributed_authorization"]
    assert da["unauthorized_execution_outcome_rejected"] is True
    neg = {x["function"]: x["status"] for x in da["negative_statuses"]}
    assert neg["RecordExecutionOutcome_WITHOUT_AUTHORIZATION"] == "failed"
    conds = [("Baseline", p14["baseline"]), ("Peer down", p14["resilience"]["one_peer_down"]),
             ("Orderer down", p14["resilience"]["one_orderer_down"])]
    for _, c in conds:
        assert c["ok"] and c["read_status"] == "success" and c["write_status"] == "success"
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.55, 0.75], width_ratios=[5.6, 0.85], hspace=0.0, wspace=0.0,
                          left=0.285, right=0.985, bottom=0.14, top=0.925)
    a1 = fig.add_subplot(gs[0, 0]); a2 = fig.add_subplot(gs[1, 0])
    l1 = fig.add_subplot(gs[0, 1]); l2 = fig.add_subplot(gs[1, 1])
    for l in (l1, l2): l.axis("off")
    # (a) latence P14 (une mesure par condition)
    lat = [int(c["latency_ns"]) / 1e9 for _, c in conds]
    xb = np.arange(3)
    a1.bar(xb[0], lat[0], 0.55, color="0.80", edgecolor="black", linewidth=0.4, zorder=2, label="Fault-free")
    a1.bar(xb[1:], lat[1:], 0.55, color=C["blue"], edgecolor="black", linewidth=0.4, hatch="////", zorder=2,
           label="Single-node fault")
    a1.set_yscale("log"); a1.set_ylim(0.1, 300); a1.set_yticks([0.1, 1, 10, 100]); a1.minorticks_off()
    a1.set_ylabel("Latency (s)")
    a1.set_xticks(xb); a1.set_xticklabels([c[0] for c in conds], fontsize=6.5)
    a1.xaxis.tick_top(); a1.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False)
    a1.set_xlim(-0.6, 2.6); a1.grid(axis="x", visible=False)
    box_legend(a1, loc="upper left")
    for (name, c), v in zip(conds, lat):
        log("Fig10B_a", condition=name, latency_s=v, read=c["read_status"], write=c["write_status"], n=1)
    # (b) controles negatifs : une case par cas rejete, protocoles sur des lignes separees
    rows = [("Wrong action", 20, C["verm"], "////"), ("No authorization", 1, C["purple"], "")]
    for i, (name, n, col, ht) in enumerate(rows):
        y = 1 - i
        a2.barh(np.full(n, y), np.ones(n), left=np.arange(1, n + 1) - 0.5, height=0.72, color=col,
                edgecolor="white", linewidth=0.5, hatch=ht, zorder=2)
        log("Fig10B_b", check=name, rejected=n, cases=n,
            source="R07A" if n == 20 else "P14 distributed_authorization")
    a2.set_yticks([1, 0]); a2.set_yticklabels(["Wrong action", "No authorization"], fontsize=6.5)
    a2.tick_params(axis="y", length=0, pad=2)
    a2.set_ylim(-0.55, 1.55); a2.set_xlim(0.5, 20.5); a2.set_xticks([1, 5, 10, 15, 20])
    a2.set_xlabel("Rejected case"); a2.grid(False)
    l1.text(0.5, 0.97, "(a)", ha="center", va="top", fontsize=7, fontweight="bold", transform=l1.transAxes)
    l2.text(0.5, 0.5, "(b)", ha="center", va="center", fontsize=7, fontweight="bold", transform=l2.transAxes)
    save_exact(fig, "Fig10B_Fabric_latency_enforcement")

TOL = {"indigo": "#332288", "cyan": "#88CCEE", "teal": "#44AA99", "green": "#117733", "olive": "#999933",
       "sand": "#DDCC77", "rose": "#CC6677", "wine": "#882255", "purple": "#AA4499"}  # palette Paul Tol "muted"

def fig10c():
    """(a) Chronologie reelle de l'essai P14 (debut = horodatage de l'event_id, duree = latence Caliper).
    (b) Matrice action soumise x issue sur le registre, 20 evenements R07A (teinte = proportion)."""
    import re, datetime as dt
    p14 = json.load(open(os.path.join(DATA, "FIG_5/HISTORY/00150_P14_FABRIC_RESILIENCE_SUMMARY.json")))
    r = pd.read_csv(os.path.join(DATA, "FIG_5/HISTORY/06425_R07A_B3_FABRIC_RESULTS_v1.csv"))
    assert len(r) == 20 and (r.technical_valid == 1).all()
    ts = lambda e: dt.datetime.strptime(re.search(r"(\d{8}T\d{12})Z", e).group(1), "%Y%m%dT%H%M%S%f")
    da = p14["distributed_authorization"]
    ev = [("Baseline", ts(p14["baseline"]["event_id"]), int(p14["baseline"]["latency_ns"]) / 1e9, "bar0"),
          ("Valid auth.", ts(da["valid_event"]), None, "ok"),
          ("No auth.", ts(da["negative_event"]), None, "ko"),
          ("Orderer down", ts(p14["resilience"]["one_orderer_down"]["event_id"]),
           int(p14["resilience"]["one_orderer_down"]["latency_ns"]) / 1e9, "bar1"),
          ("Peer down", ts(p14["resilience"]["one_peer_down"]["event_id"]),
           int(p14["resilience"]["one_peer_down"]["latency_ns"]) / 1e9, "bar1")]
    t0 = ev[0][1]
    assert all(v["status"] == "success" for v in da["valid_statuses"])
    assert da["unauthorized_execution_outcome_rejected"] is True
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.55, 0.75], width_ratios=[1.0, 0.045], hspace=0.40, wspace=0.05,
                          left=0.235, right=0.905, bottom=0.135, top=0.985)
    a1 = fig.add_subplot(gs[0, :]); a2 = fig.add_subplot(gs[1, 0]); cax = fig.add_subplot(gs[1, 1])
    ylab = []
    for i, (name, t, dur, kind) in enumerate(ev):
        y = len(ev) - 1 - i; x = (t - t0).total_seconds(); ylab.append((y, name))
        if kind == "bar0":
            a1.barh(y, dur, left=x, height=0.55, color=TOL["sand"], edgecolor="black", linewidth=0.4, zorder=3,
                    label="Write/read, fault-free")
        elif kind == "bar1":
            a1.barh(y, dur, left=x, height=0.55, color=TOL["indigo"], edgecolor="black", linewidth=0.4, zorder=3,
                    hatch="xxxx", label=None if any(l.startswith("Write/read, single") for l in
                                                    a1.get_legend_handles_labels()[1]) else "Write/read, single-node fault")
        elif kind == "ok":
            a1.plot(x, y, marker="o", ms=4.2, mfc=TOL["teal"], mec="black", mew=0.4, ls="none", zorder=4,
                    label="Authorized, accepted")
        else:
            a1.plot(x, y, marker="X", ms=5.0, mfc=TOL["wine"], mec="black", mew=0.4, ls="none", zorder=4,
                    label="Unauthorized, rejected")
        a1.hlines(y, 0, 62, color="0.85", lw=0.5, zorder=1)
        log("Fig10C_a", event=name, start_s=x, duration_s=dur if dur is not None else float("nan"))
    a1.set_yticks([y for y, _ in ylab]); a1.set_yticklabels([n for _, n in ylab], fontsize=6.5)
    a1.tick_params(axis="y", length=0, pad=2)
    a1.set_xlim(-2, 62); a1.set_ylim(-0.7, len(ev) - 0.3)
    a1.set_xlabel("Elapsed time in P14 run (s)", labelpad=1)
    a1.grid(axis="y", visible=False)
    box_legend(a1, loc="upper right", ncol=1, fontsize=5.8)
    # (b) matrice 2 x 2 (proportions, sans chiffres)
    sub_ok = int((r.wrong_invoke_rc == 0).sum()); sub_ko = int((r.wrong_invoke_rc != 0).sum())
    aut_ok = int((r.correct_control_rc == 0).sum()); aut_ko = int((r.correct_control_rc != 0).sum())
    M = np.array([[aut_ok, aut_ko], [sub_ok, sub_ko]]) / len(r)
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("tealseq", ["#F4F9F8", TOL["teal"], "#1B4D44"])
    im = a2.imshow(M, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    a2.set_xticks([0, 1]); a2.set_xticklabels(["Accepted", "Rejected"], fontsize=6.5)
    a2.set_yticks([0, 1]); a2.set_yticklabels(["Authorized", "Substituted"], fontsize=6.5)
    a2.set_xlabel("Ledger outcome (R07A)", labelpad=1); a2.grid(False)
    a2.tick_params(length=0)
    for e in np.arange(-0.5, 2, 1):
        a2.axhline(e, color="white", lw=1.2); a2.axvline(e, color="white", lw=1.2)
    cb = fig.colorbar(im, cax=cax); cb.set_ticks([0, 0.5, 1]); cb.set_ticklabels(["0", "0.5", "1"])
    cb.ax.tick_params(labelsize=6, length=2); cb.outline.set_linewidth(0.4)
    cb.set_label("Fraction", fontsize=6.5, labelpad=2)
    log("Fig10C_b", authorized_accepted=aut_ok, authorized_rejected=aut_ko,
        substituted_accepted=sub_ok, substituted_rejected=sub_ko, n=len(r))
    a1.text(0.985, 0.04, "(a)", transform=a1.transAxes, ha="right", va="bottom", fontsize=7, fontweight="bold")
    a2.text(1.42, 0.0, "(b)", fontsize=7, fontweight="bold", ha="right", va="center")  # cellule claire
    save_exact(fig, "Fig10C_Fabric_timeline_matrix")

def _p14():
    p14 = json.load(open(os.path.join(DATA, "FIG_5/HISTORY/00150_P14_FABRIC_RESILIENCE_SUMMARY.json")))
    conds = [("Baseline", p14["baseline"]), ("Peer down", p14["resilience"]["one_peer_down"]),
             ("Orderer down", p14["resilience"]["one_orderer_down"])]
    for _, c in conds:
        assert c["ok"] and c["read_status"] == "success" and c["write_status"] == "success"
    return [n for n, _ in conds], [int(c["latency_ns"]) / 1e9 for _, c in conds]

def fig10d():
    """Modele 1 : barres verticales a axe interrompu (echelle lineaire), un seul panneau."""
    names, lat = _p14()
    cols = [TOL["sand"], TOL["teal"], TOL["wine"]]; hts = ["", "....", "xxxx"]
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.6], hspace=0.06, left=0.13, right=0.985, bottom=0.11, top=0.985)
    top = fig.add_subplot(gs[0]); bot = fig.add_subplot(gs[1], sharex=top)
    for ax in (top, bot):
        for i, (n, v) in enumerate(zip(names, lat)):
            ax.bar(i, v, 0.55, color=cols[i], edgecolor="black", linewidth=0.4, hatch=hts[i], zorder=2, label=n)
        ax.grid(axis="x", visible=False)
    top.set_ylim(19.5, 23); top.set_yticks([20, 21, 22])
    bot.set_ylim(0, 0.8); bot.set_yticks([0, 0.2, 0.4, 0.6])
    top.spines["bottom"].set_visible(False); bot.spines["top"].set_visible(False)
    top.tick_params(axis="x", bottom=False, labelbottom=False)
    d = 0.012
    for ax, yy in ((top, 0), (bot, 1)):
        kw = dict(transform=ax.transAxes, color="black", clip_on=False, lw=0.6)
        ax.plot((-d, d), (yy - d * 2, yy + d * 2), **kw); ax.plot((1 - d, 1 + d), (yy - d * 2, yy + d * 2), **kw)
    bot.set_xticks(range(3)); bot.set_xticklabels(names)
    fig.text(0.025, 0.55, "Write/read latency (s)", rotation=90, va="center", ha="center", fontsize=8)
    box_legend(top, loc="upper left", ncol=1)
    save_exact(fig, "Fig10_M1_broken_axis")

def fig10e():
    """Modele 2 : barres horizontales, echelle log, un seul panneau."""
    names, lat = _p14()
    cols = [TOL["cyan"], TOL["olive"], TOL["purple"]]; hts = ["", "////", "xxxx"]
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.235, 0.14, 0.745, 0.845])
    y = np.arange(3)[::-1]
    for i in range(3):
        ax.barh(y[i], lat[i], 0.55, color=cols[i], edgecolor="black", linewidth=0.4, hatch=hts[i], zorder=2,
                label=names[i])
    ax.set_xscale("log"); ax.set_xlim(0.1, 200); ax.set_xticks([0.1, 1, 10, 100]); ax.minorticks_off()
    ax.set_yticks(y); ax.set_yticklabels(names); ax.set_ylim(-0.6, 2.6)
    ax.set_xlabel("Write/read latency (s)"); ax.grid(axis="y", visible=False)
    box_legend(ax, loc="lower right")
    save_exact(fig, "Fig10_M2_hbar_log")

def fig10f():
    """Modele 3 : issues des controles d'application (barres 100 % empilees), un seul panneau."""
    r = pd.read_csv(os.path.join(DATA, "FIG_5/HISTORY/06425_R07A_B3_FABRIC_RESULTS_v1.csv"))
    p14 = json.load(open(os.path.join(DATA, "FIG_5/HISTORY/00150_P14_FABRIC_RESILIENCE_SUMMARY.json")))
    da = p14["distributed_authorization"]
    rows = [("Authorized (R07A)", int((r.correct_control_rc == 0).sum()), len(r)),
            ("Substituted (R07A)", int((r.wrong_invoke_rc == 0).sum()), len(r)),
            ("Valid auth. (P14)", int(all(v["status"] == "success" for v in da["valid_statuses"])), 1),
            ("No auth. (P14)", int(not da["unauthorized_execution_outcome_rejected"]), 1)]
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.255, 0.14, 0.725, 0.845])
    y = np.arange(len(rows))[::-1]
    for yy, (n, acc, tot) in zip(y, rows):
        fa = 100 * acc / tot
        ax.barh(yy, fa, 0.55, color=TOL["green"], edgecolor="black", linewidth=0.4, zorder=2,
                label="Accepted" if yy == y[0] else None)
        ax.barh(yy, 100 - fa, 0.55, left=fa, color=TOL["rose"], edgecolor="black", linewidth=0.4, hatch="////",
                zorder=2, label="Rejected" if yy == y[1] else None)
    ax.set_yticks(y); ax.set_yticklabels([n for n, _, _ in rows], fontsize=7)
    ax.set_xlim(0, 100); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xlabel("Share of invocations (%)")
    ax.set_ylim(-0.6, len(rows) - 0.4 + 0.9); ax.grid(axis="y", visible=False)
    box_legend(ax, loc="upper right", ncol=2)
    save_exact(fig, "Fig10_M3_enforcement")

TAB = ["#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD", "#8C564B", "#E377C2"]  # couleurs franches (modele fourni)

def fig10g():
    """Toutes les latences Fabric mesurees, barres groupees, echelle log (modele de reference fourni).
    Groupes R11 (Docker CLI + lecture pair, n=30) : mediane, moyenne, P95, max.
    Groupe P14 (Caliper ecriture/lecture, n=1 par condition) : sans panne, pair arrete, ordonnanceur arrete."""
    t = pd.read_csv(os.path.join(DATA, "FIG_6/MAC/R11_COMPONENT_TABLE.csv")).set_index("component")
    names_r11 = ["Fabric CLI: authorization read", "Fabric CLI: decision read"]
    for n in names_r11:
        assert int(t.loc[n, "n"]) == 30
    _, lat = _p14()
    stats = [("median_ms", "Median (R11)"), ("mean_ms", "Mean (R11)"), ("p95_ms", "P95 (R11)"), ("max_ms", "Max (R11)")]
    p14lab = ["Fault-free (P14)", "Peer down (P14)", "Orderer down (P14)"]
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.13, 0.14, 0.855, 0.845])
    w = 0.2
    for g, n in enumerate(names_r11):
        for j, (col, lab) in enumerate(stats):
            v = float(t.loc[n, col]) / 1e3
            ax.bar(g + (j - 1.5) * w, v, w, color=TAB[j], edgecolor="black", linewidth=0.3, zorder=2,
                   label=lab if g == 0 else None)
            log("Fig10G", group=n, series=lab, value_s=v, n=30)
    for j, (v, lab) in enumerate(zip(lat, p14lab)):
        ax.bar(2 + (j - 1) * w, v, w, color=TAB[4 + j], edgecolor="black", linewidth=0.3, zorder=2, label=lab)
        log("Fig10G", group="Caliper write/read", series=lab, value_s=v, n=1)
    ax.set_yscale("log"); ax.set_ylim(0.1, 1000); ax.set_yticks([0.1, 1, 10, 100, 1000]); ax.minorticks_off()
    ax.set_ylabel("Latency (s)")
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["Authorization read", "Decision read", "Write/read"])
    ax.set_xlabel("Hyperledger Fabric operation")
    ax.set_xlim(-0.55, 2.55)
    ax.grid(axis="x", visible=False); ax.grid(axis="y", linestyle="--", linewidth=0.4, color="0.7")
    box_legend(ax, loc="upper left", ncol=2, fontsize=5.8, handlelength=1.2)
    save_exact(fig, "Fig10G_Fabric_grouped_bars")

def fig10h():
    """Fig. 10 en deux panneaux separes (protocoles et echantillonnages differents, aucun cumul).
    (a) R11 : lectures Fabric via Docker CLI, n = 30 chacune (mediane, moyenne, P95, max).
    (b) P14 : ecriture/lecture Caliper, une mesure par condition (n = 1), echelle log."""
    t = pd.read_csv(os.path.join(DATA, "FIG_6/MAC/R11_COMPONENT_TABLE.csv")).set_index("component")
    ops = [("Fabric CLI: authorization read", "Authorization read"), ("Fabric CLI: decision read", "Decision read")]
    for o, _ in ops:
        assert int(t.loc[o, "n"]) == 30
    names, lat = _p14()
    stats = [("median_ms", "Median"), ("mean_ms", "Mean"), ("p95_ms", "P95"), ("max_ms", "Max")]
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1], hspace=0.42, left=0.15, right=0.985, bottom=0.075, top=0.985)
    a1 = fig.add_subplot(gs[0]); a2 = fig.add_subplot(gs[1])
    w = 0.2
    for g, (o, lab_o) in enumerate(ops):
        for j, (col, lab) in enumerate(stats):
            v = float(t.loc[o, col]) / 1e3
            a1.bar(g + (j - 1.5) * w, v, w, color=TAB[j], edgecolor="black", linewidth=0.3, zorder=2,
                   label=lab if g == 0 else None)
            log("Fig10H_a", operation=lab_o, statistic=lab, value_s=v, n=30, protocol="R11 Docker CLI peer read")
    a1.set_xticks([0, 1]); a1.set_xticklabels([l for _, l in ops]); a1.set_xlim(-0.55, 1.55)
    a1.set_ylabel("Latency (s)"); a1.set_ylim(0, 1.4); a1.set_yticks([0, 0.4, 0.8, 1.2])
    a1.grid(axis="x", visible=False); a1.grid(axis="y", linestyle="--", linewidth=0.4, color="0.7")
    box_legend(a1, loc="upper left", ncol=4, handlelength=1.2)
    a1.text(0.985, 0.965, "(a)", transform=a1.transAxes, ha="right", va="top", fontsize=7, fontweight="bold")
    cols = [TAB[4], TAB[5], TAB[6]]
    for j, (n_, v) in enumerate(zip(names, lat)):
        a2.bar(j, v, 0.5, color=cols[j], edgecolor="black", linewidth=0.3, zorder=2)
        log("Fig10H_b", condition=n_, value_s=v, n=1, protocol="P14 Caliper write/read")
    a2.set_yscale("log"); a2.set_ylim(0.1, 100); a2.set_yticks([0.1, 1, 10, 100]); a2.minorticks_off()
    a2.set_xticks(range(3)); a2.set_xticklabels(["Fault-free", "One peer down", "One orderer down"])
    a2.set_xlim(-0.6, 2.6); a2.set_ylabel("Latency (s)")
    a2.grid(axis="x", visible=False); a2.grid(axis="y", linestyle="--", linewidth=0.4, color="0.7")
    a2.text(0.015, 0.965, "(b)", transform=a2.transAxes, ha="left", va="top", fontsize=7, fontweight="bold")
    save_exact(fig, "Fig10H_Fabric_R11_P14")

if __name__ == "__main__":
    which = sys.argv[3].split(",") if len(sys.argv) > 3 else ["3", "4", "5", "6", "7", "8", "9"]
    for k in which: globals()["fig" + k]()  # ex. 3,3b,7,7b
    L = pd.DataFrame(LOG)
    for fg, sub in (L.groupby("figure") if len(L) else []):
        sub.dropna(axis=1, how="all").to_csv(os.path.join(OUT, f"PLOTTED_VALUES_{fg}.csv"), index=False)
    print("OK", which, len(LOG), "rows logged")
