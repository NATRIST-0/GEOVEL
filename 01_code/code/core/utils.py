#!/usr/bin/python3
# author: Tristan Gayrard

import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.axes
from collections import defaultdict

# Style sheet params
font_size = 10
plt.rcParams.update(
    {
        "svg.fonttype": "none",
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI"],
        "font.size": font_size,
        "axes.titlesize": font_size,
        "axes.labelsize": font_size,
        "xtick.labelsize": font_size,
        "ytick.labelsize": font_size,
        "legend.fontsize": font_size,
        "figure.titlesize": font_size,
        "mathtext.fontset": "custom",
        "mathtext.rm": "Segoe UI",
        "mathtext.it": "Segoe UI:italic",
        "mathtext.bf": "Segoe UI:bold",
    }
)

def plot_layout(
    target=None,
    layout_type="paper",
    shape="square",
    grid=True,
):
    """
    Applies unified scientific layout.
    Simplified version tailored specifically for the GEOVEL core modules.
    """
    # Detect target axes
    if target is None:
        fig = plt.gcf()
        target_axes = fig.axes
    elif isinstance(target, matplotlib.figure.Figure):
        fig = target
        target_axes = fig.axes
    elif isinstance(target, matplotlib.axes.Axes):
        fig = target.get_figure()
        target_axes = [target]
    elif isinstance(target, (list, tuple)):
        fig = target[0].get_figure()
        target_axes = target
    else:
        raise ValueError("Target must be Figure, Axes, list of Axes, or None.")

    if not target_axes:
        target_axes = [plt.gca()]
        fig = plt.gcf()

    global_primary_ax = target_axes[0]

    # Group by subplot
    subplot_groups = defaultdict(list)
    for ax in target_axes:
        try:
            spec = ax.get_subplotspec()
            key = spec if spec is not None else tuple(ax.get_position().bounds)
        except AttributeError:
            key = tuple(ax.get_position().bounds)
        subplot_groups[key].append(ax)

    # Apply style per subplot group
    for key, axes_in_subplot in subplot_groups.items():
        primary_ax = axes_in_subplot[0]

        for ax in axes_in_subplot:
            
            # PAPER STYLE
            if layout_type == "paper":
                ax.minorticks_on()
                y_scale, x_scale = 1.2, 1.5

                # Single ax config
                ax.tick_params(
                    axis="both", which="major", direction="in",
                    top=True, right=True, width=1.0 * y_scale, length=4 * y_scale, pad=4,
                )

                # Minor ticks config
                ax.tick_params(
                    axis="both", which="minor", direction="in",
                    width=0.5 * x_scale, length=2 * x_scale,
                )
                
                # No minor ticks or labels on top spine
                ax.tick_params(axis="x", which="minor", top=False, labeltop=False)
                ax.tick_params(axis="x", which="major", labeltop=False)

            # OCEANO STYLE
            elif layout_type == "oceano":
                if ax == primary_ax:
                    ax.invert_yaxis()
                    ax.xaxis.set_ticks_position("top")
                    ax.xaxis.set_label_position("top")

                for spine_name in ["right", "bottom"]:
                    if spine_name in ax.spines:
                        ax.spines[spine_name].set_color("lightgrey")

                ax.plot(1, 1, ">k", transform=ax.transAxes, clip_on=False, markersize=8, zorder=10)
                ax.plot(0, 0, marker=(3, 0, 180), color="k", transform=ax.transAxes, clip_on=False, markersize=8, zorder=10)

            # ARROW STYLE
            elif layout_type == "arrow":
                for spine_name in ["right", "top"]:
                    if spine_name in ax.spines:
                        ax.spines[spine_name].set_color("lightgrey")

                ax.plot(1, 0, ">k", transform=ax.transAxes, clip_on=False, markersize=8, zorder=10)
                ax.plot(0, 1, "^k", transform=ax.transAxes, clip_on=False, markersize=8, zorder=10)

        # Smart grid (primary ax only)
        if grid:
            primary_ax.grid(True, which="major", linestyle="-", linewidth=0.75, alpha=0.25)
            primary_ax.grid(True, which="minor", linestyle="-", linewidth=0.25, alpha=0.15)
            primary_ax.set_axisbelow(True)

    # Figure aspect ratio
    if shape == "square":
        for ax in target_axes:
            if hasattr(ax, 'get_subplotspec') and ax.get_subplotspec() is not None:
                rows, cols, _, _ = ax.get_subplotspec().get_geometry()
                ax.set_box_aspect(cols / rows)
            else:
                # If it's a single plot, force a 1:1 square ratio
                global_primary_ax.set_box_aspect(1)
        
        fig.tight_layout()