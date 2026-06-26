import numpy as np
import pandas as pd
from pathlib import Path
from .utils import plot_layout

def draw_geovel_profiles(ax, file_path: Path, show_avg_only: bool, method: str, level_of_no_motion: float):
    fig = ax.figure
    fig.clear()

    if not Path(file_path).exists():
        print("No data available.\nPlease run data processing first.")
        return

    df = pd.read_csv(file_path, comment='#')

    if not any("vx_" in col for col in df.columns):
        print("Velocity data missing.\nPlease calculate geostrophic velocities first.")
        return

    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122, sharey=ax1)

    plot_df = df.drop_duplicates(subset=["depth_m"]).sort_values("depth_m").reset_index(drop=True)
    ref_idx = (plot_df["depth_m"] - level_of_no_motion).abs().idxmin()

    available_triangles = sorted(list(set(col.split("_")[2] for col in df.columns if col.startswith("vx_isop_T"))))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    isob_shifted_vx = None
    isob_shifted_vy = None
    isop_mean_shifted_vx = None
    isop_mean_shifted_vy = None

    def plot_method_lines(prefix, linestyle, label_suffix=""):
        nonlocal isob_shifted_vx, isob_shifted_vy, isop_mean_shifted_vx, isop_mean_shifted_vy

        if prefix == "isob":
            # Isobaric is a single array-wide profile
            vx_col = "vx_isob_array_cm_s"
            vy_col = "vy_isob_array_cm_s"
            if vx_col in plot_df.columns and vy_col in plot_df.columns:
                shifted_vx = plot_df[vx_col] - plot_df[vx_col].loc[ref_idx]
                shifted_vy = plot_df[vy_col] - plot_df[vy_col].loc[ref_idx]
                
                isob_shifted_vx = shifted_vx
                isob_shifted_vy = shifted_vy
                
                # Using purple to distinctly separate the Array fit from Triangle colors
                ax1.plot(shifted_vx, -plot_df["depth_m"], label=f"Array {label_suffix}", color="#9467bd", linewidth=2.0, linestyle=linestyle)
                ax2.plot(shifted_vy, -plot_df["depth_m"], label=f"Array {label_suffix}", color="#9467bd", linewidth=2.0, linestyle=linestyle)
                
        elif prefix == "isop":
            # Isopycnal retains the triangle-level rendering
            vx_cols = [f"vx_isop_{t}_cm_s" for t in available_triangles if f"vx_isop_{t}_cm_s" in plot_df.columns]
            vy_cols = [f"vy_isop_{t}_cm_s" for t in available_triangles if f"vy_isop_{t}_cm_s" in plot_df.columns]

            if vx_cols and vy_cols:
                avg_vx = plot_df[vx_cols].mean(axis=1)
                avg_vx = avg_vx - avg_vx.loc[ref_idx]

                avg_vy = plot_df[vy_cols].mean(axis=1)
                avg_vy = avg_vy - avg_vy.loc[ref_idx]

                isop_mean_shifted_vx = avg_vx
                isop_mean_shifted_vy = avg_vy

                if show_avg_only:
                    ax1.plot(avg_vx, -plot_df["depth_m"], label=f"Mean {label_suffix}", color="crimson", linewidth=2.0, linestyle=linestyle)
                    ax2.plot(avg_vy, -plot_df["depth_m"], label=f"Mean {label_suffix}", color="crimson", linewidth=2.0, linestyle=linestyle)
                else:
                    plotted_vx, plotted_vy = [], []
                    for i, triangle in enumerate(available_triangles):
                        color = colors[i % len(colors)]
                        vx_col = f"vx_isop_{triangle}_cm_s"
                        vy_col = f"vy_isop_{triangle}_cm_s"

                        if vx_col in plot_df.columns and vy_col in plot_df.columns:
                            shifted_vx = plot_df[vx_col] - plot_df[vx_col].loc[ref_idx]
                            shifted_vy = plot_df[vy_col] - plot_df[vy_col].loc[ref_idx]
                            
                            current_vx = shifted_vx.fillna(99999).values
                            overlap_x = any(np.allclose(current_vx, prev_vx, atol=1e-5) for prev_vx in plotted_vx)
                            final_style_x = ":" if overlap_x else linestyle
                            
                            current_vy = shifted_vy.fillna(99999).values
                            overlap_y = any(np.allclose(current_vy, prev_vy, atol=1e-5) for prev_vy in plotted_vy)
                            final_style_y = ":" if overlap_y else linestyle

                            ax1.plot(shifted_vx, -plot_df["depth_m"], label=fr"$v_x$ {triangle} {label_suffix}", color=color, linewidth=1.5, linestyle=final_style_x)
                            ax2.plot(shifted_vy, -plot_df["depth_m"], label=f"$v_y$ {triangle} {label_suffix}", color=color, linewidth=1.5, linestyle=final_style_y)

                            plotted_vx.append(current_vx)
                            plotted_vy.append(current_vy)

    if "Isobaric" in method or "Both" in method:
        plot_method_lines("isob", "-", "(Isobaric)" if "Both" in method else "")
        
    if "Isopycnal" in method or "Both" in method:
        plot_method_lines("isop", "--", "(Isopycnal)" if "Both" in method else "")

    if "Both" in method and isob_shifted_vx is not None and isop_mean_shifted_vx is not None:
        diff_vx = (isob_shifted_vx - isop_mean_shifted_vx).abs()
        diff_vy = (isob_shifted_vy - isop_mean_shifted_vy).abs()
        print("Maximum difference between Isobaric and Isopycnal methods:")
        print(f"max(Δu₉)={diff_vx.max():.4f} cm s⁻¹")
        print(f"max(Δv₉)= {diff_vy.max():.4f} cm s⁻¹")

    ax1.axvline(x=0, color="black", linewidth=1, linestyle="--")
    ax1.set_xlabel(r"$u_g$ (cm s$^{-1}$)")
    ax1.set_ylabel(r"Depth (m)")
    ax1.legend(loc="best", fontsize=8)

    ax2.axvline(x=0, color="black", linewidth=1, linestyle="--")
    ax2.set_xlabel(r"$v_g$ (cm s$^{-1}$)")
    ax2.legend(loc="best", fontsize=8)

    plot_layout(target=fig, layout_type="oceano", shape="square")