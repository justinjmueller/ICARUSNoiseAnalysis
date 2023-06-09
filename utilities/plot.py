import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import colors as colors
from matplotlib import cm as cm
from fnal import Dataset

def plot_tpc(datasets, labels, metric='rawrms', tpc=0) -> None:
    """
    Plots the desired metric (channel-to-channel by wire plane) for
    the specified TPC.

    Parameters
    ----------
    datasets: list[Dataset]
        The Dataset objects to be plotted against each other.
    labels: list[str]
        The labels for each Dataset's entry in the legend.
    metric: str
        The key in the Dataset that specifies the metric.
    tpc: int or list[int]
        The index of the tpc(s) to select and plot.
    """
    plt.style.use('plot_style.mplstyle')
    figure = plt.figure(figsize=(26,16))
    gspec = figure.add_gridspec(3,8)
    saxs = [figure.add_subplot(gspec[i,0:6]) for i in [0,1,2]]
    haxs = [figure.add_subplot(gspec[i,6:8]) for i in [0,1,2]]
    planes = ['Induction 1', 'Induction 2', 'Collection']
    nchannels = [2304, 5760, 5760]
    ndivs = [288, 576, 576]

    for pi, p in enumerate(planes):
        for di, d in enumerate(datasets):
            mask = ((d['tpc'] == tpc) & (d['plane'] == pi))

            saxs[pi].scatter(d['channel_id'][mask], d[metric][mask], label=labels[di])
            xlow = 13824*tpc + sum(nchannels[:pi])
            xhigh = xlow + nchannels[pi]
            saxs[pi].set_xlim(xlow,xhigh)
            saxs[pi].set_ylim(0,10)
            saxs[pi].set_xticks(np.arange(xlow, xhigh+ndivs[pi], ndivs[pi]))
            saxs[pi].set_xlabel('Channel ID')
            saxs[pi].set_ylabel('RMS [ADC]')
            saxs[pi].set_title(p)

            haxs[pi].hist(d[metric][mask], range=(0,10), bins=50,
                          label=labels[di], histtype='step')
            haxs[pi].legend()
            haxs[pi].set_xlim(0,10)
            haxs[pi].set_xlabel('RMS [ADC]')
            haxs[pi].set_ylabel('Entries')

def plot_crate(datasets, labels, metric='rawrms', component='WW19') -> None:
    """
    Plots the desired metric (channel-to-channel for the specified
    component) for each of the input Datasets. A Dataset can also
    be an INFNDataset.

    Parameters
    ----------
    datasets: list[Dataset]
        The Dataset objects to be plotted against each other.
    labels: list[str]
        The labels for each Dataset's entry in the legend.
    metric: str
        The key in the Dataset that specifies the metric.
    component: str or list[str]
        The name of the component(s) to select and plot.

    Returns
    -------
    None.
    """
    plt.style.use('plot_style.mplstyle')
    figure = plt.figure(figsize=(8,6))
    ax = figure.add_subplot()
    for di, d in enumerate(datasets):
        if isinstance(component, list) and len(component) == len(datasets):
            c = component[di]
            title = ' vs. '.join(component)
        else:
            c = component
            title = component
        selected = d['flange'] == c
        x = 64*d['board'][selected] + d['ch'][selected]
        ax.scatter(x, d[metric][selected], label=labels[di])
    ax.set_xlim(0,576)
    ax.set_ylim(0, 10.0)
    ax.set_xticks([64*i for i in range(10)])
    ax.set_xlabel('Channel Number')
    ax.set_ylabel('RMS [ADC]')
    ax.legend()
    figure.suptitle(title)

def plot_wire_planes(data, metric, metric_label, tpc=0):
    """
    Create and save a plot displaying a per-plane view with each wire
    in its physical location colored by the specified metric.

    Parameters
    ----------
    data: Dataset
        The dataset containing the data.
    metric: str
        The name of the metric to be plotted.
    metric_label: str
        The label for the metric.
    tpc: int
        The desired TPC to display (0, 1, 2, 3 = EE, EW, WE, WW).

    Returns
    -------
    None.
    """
    plt.style.use('plot_style.mplstyle')
    figure = plt.figure(figsize=(20,12))
    gspec = figure.add_gridspec(ncols=10, nrows=3)
    axs = [figure.add_subplot(gspec[i, :9]) for i in [0,1,2]]
    cmap = plt.cm.ScalarMappable(cmap=cm.viridis, norm=colors.Normalize(0,1))
    cmap.set_clim(0,10)
    plane_label = {0: 'Induction 1', 1: 'Induction 2', 2: 'Collection'}

    for p in [0,1,2]:
        mask = data.chmap['channel_id'] // 13824 == tpc
        wires = data.chmap.loc[mask][['channel_id', 'z0', 'y0', 'z1', 'y1']]
        tmp = pd.DataFrame({'channel_id': data['channel_id'], metric: data[metric]}).loc[data['plane'] == p]
        wires = wires.merge(tmp, how='inner', left_on='channel_id', right_on='channel_id')
        cs = cmap.to_rgba(wires[metric])
        wires = [[(x[1], x[2]), (x[3], x[4])] for x in wires.to_numpy()]
        axs[p].add_collection(LineCollection(wires, colors=cs))
        axs[p].set_xlim(-895.95, 895.95)
        axs[p].set_ylim(-181.70, 134.80)
        axs[p].set_xlabel('Z Position [cm]')
        axs[p].set_ylabel('Y Position [cm]')
        axs[p].set_title(plane_label[p])
    cax = figure.add_axes([0.92, 0.05, 0.035, 0.89])
    axcb = figure.colorbar(cmap, ax=axs, cax=cax, use_gridspec=True)
    axcb.set_label(metric_label)
    axcb.solids.set_edgecolor('face')
    tpc_name = {0: 'EE', 1: 'EW', 2: 'WE', 3: 'WW'}
    figure.suptitle(f'{metric_label.split(" [")[0]} by Plane for {tpc_name[tpc]}')

"""
    axcb.set_label(f'Status', fontsize=18)
    axcb.solids.set_edgecolor('face')
    cax.tick_params(labelsize=16)
    tpc_name = {0: 'EE', 1: 'EW', 2: 'WE', 3: 'WW'}[tpc]
    figure.suptitle(f'Channel Status of TPC: {tpc_name}',
                    x=0.465, fontsize=24)
"""

def plot_waveform(waveform, title) -> None:
    """
    Plot a single waveform over its full range.

    Parameters
    ----------
    waveform: np.array
        The input waveform to plot. Assumed shape of (4096,).
    title: str
        The title to be displayed at the top of the plot.

    Returns
    -------
    None.
    """
    plt.style.use('plot_style.mplstyle')
    figure = plt.figure(figsize=(14,6))
    ax = figure.add_subplot()
    ax.plot(np.arange(4096), waveform, linestyle='-', linewidth=1)
    ax.set_xlim(0,4096)
    ax.set_ylim(-20, 20)
    ax.set_xlabel('Time [ticks]')
    ax.set_ylabel('Waveform Height [ADC]')
    figure.suptitle(title)