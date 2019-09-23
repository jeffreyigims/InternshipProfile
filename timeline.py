import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from datetime import datetime as dt
import matplotlib.patches as mpatches
import pandas as pd
from brokenaxes import brokenaxes
import matplotlib.ticker as ticker
import matplotlib

def plot_stem(eligible_dates, recurrent_met_dates, injuries, title, start_dates, end_dates, claim_endpoints, injury_endpoints):

    print('STEM')
    dates = []
    names = []
    for item in eligible_dates:
        dates.append(str(item).split(' ')[0])
        names.append([str(item).split(' ')[0], claim])
    for date in recurrent_met_dates:
        dates.append(str(date[0]).split(' ')[0])
        names.append([str(date[0]).split(' ')[0] + ': ' + str(date[1]) + ' Games', recurrent])
    for injury in injuries:
        dates.append(str(injury[1]).split(' ')[0])
        names.append([str(injury[1]).split(' ')[0] + '\n' + injury[0], placed])
        dates.append(str(injury[2]).split(' ')[0])
        names.append([str(injury[2]).split(' ')[0], reinstated])
    dates = [dt.strptime(d, "%Y-%m-%d") for d in dates]
    pairs = sorted(zip(dates, names))
    dates, names = map(list, zip(*pairs))

    length = len(eligible_dates) + len(recurrent_met_dates) + (2 * len(injuries))
    levels_list = [1, -1, 2, -2, 1.5, -.5]
    adjusted_list = []
    for i in range(0, len(dates)):
        adjusted_list.append(levels_list[i % len(levels_list)])
    levels = np.tile(adjusted_list, int(np.ceil(len(dates)/6)))[:len(dates)]

    # Create figure and plot a stem plot
    fig, ax = plt.subplots(figsize=(18, 6), constrained_layout=True)
    ax.set(title = title)
    markerline, stemline, baseline = ax.stem(dates, levels,
                                             linefmt="C3-", basefmt="k-",
                                             use_line_collection=True)
    plt.setp(markerline, mec="k", mfc="w", zorder=3)

    # Shift the markers to the baseline
    markerline.set_ydata(np.zeros(len(dates)))

    # Annotate lines
    vert = np.array(['top', 'bottom'])[(levels > 0).astype(int)]
    for d, l, x, va in zip(dates, levels, names, vert):
        r = x[0]
        c = x[1]
        ax.annotate(r, xy=(d, l), xytext=(-3, np.sign(l)*3),
                    textcoords="offset points", va=va, ha="center", fontsize = 7, color = c)

    min = dates[0]
    max = dates[-1]
    # index = pd.DatetimeIndex(start = dates[0], end = dates[7], freq = 'M')
    # Format with intervals
    #ax.get_xaxis().set_major_locator(mdates.MonthLocator(interval=2))
    #ax.get_xaxis().set_major_formatter(mdates.DateFormatter("%b %Y"))
    ticks = []
    labels = []
    for start_date, end_date in zip(start_dates, end_dates):
        if(min <= start_date + pd.to_timedelta('1Y') and max >= start_date):
            ticks.append(start_date)
            ticks.append(start_date + (end_date - start_date) / 2)
            ticks.append(end_date)
            labels.append('')
            labels.append(str(end_date.year))
            labels.append('')
    ax.get_xaxis().set_major_locator(ticker.MultipleLocator(2))
    ax.get_xaxis().set_major_formatter(mdates.DateFormatter("%b %Y"))


    # ax_next = plt.subplot(ax)
    # plt.xticks(matplotlib.dates.date2num(start_dates[0:2] + start_dates[5:]))
    plt.xticks(ticks, labels)
    #ax_next.plot()

    #ax.set_xlim(ticks[0], ticks[2])
    #ax_next.set_xlim(ticks[8], ticks[-1])
    #ax.spines['left'].set_visible(False)
    #ax_next.spines['right'].set_visible(False)
    #ax.yaxis.tick_left()
    #ax.tick_params(labelright='off')
    #ax2.yaxis.tick_right()
    plt.setp(ax.get_xticklabels(), rotation=30, ha="center")

    # Get rid of vertical axis
    ax.get_yaxis().set_visible(False)
    for spine in ["left", "top", "right"]:
        ax.spines[spine].set_visible(False)

    placed_patch = mpatches.Patch(color = placed, label = 'Placed')
    reinstated_patch = mpatches.Patch(color = reinstated, label = 'Reinstated')
    claim_patch = mpatches.Patch(color = claim, label = 'Eligible')
    recurrent_patch = mpatches.Patch(color = recurrent, label = 'Recurrent Met')
    season_patch = mpatches.Patch(color = start, alpha = .5, label = 'In Season')
    hurt_patch = mpatches.Patch(color = '#1F77B4', alpha = .5, label = 'Hurt')
    eligible_patch = mpatches.Patch(color = '#1F77B4', alpha = .5, hatch = '////', label = 'Claim Eligible')


    for start_date, end_date in zip(start_dates, end_dates):
        if(min <= start_date + pd.to_timedelta('1Y') and max >= start_date):
            ax.axvspan(start_date, end_date, alpha = .5, color = start)

    for points in claim_endpoints:
        ax.add_patch(mpatches.Rectangle((points[1], -.35), points[2] - points[1], .7, alpha = .5, hatch = '/'))
        ax.add_patch(mpatches.Rectangle((points[0], -.35), points[1] - points[0], .7, alpha = .5))
    for points in injury_endpoints:
        clear = True
        test = pd.date_range(start = points[0], end = points[1])
        for new in claim_endpoints:
            if(not test.intersection(pd.date_range(start = new[0], end = new[2])).empty): clear = False
        if(clear == True): ax.add_patch(mpatches.Rectangle((points[0], -.35), points[1] - points[0], .7, alpha = .5))


    first_legend = plt.legend(handles=[recurrent_patch, claim_patch, reinstated_patch, placed_patch], title = 'Text')
    plt.gca().add_artist(first_legend)
    plt.legend(handles=[season_patch, hurt_patch, eligible_patch], title = 'Blocks', loc = 2)
    ax.set_ymargin(2)
    ax.margins(y=0.1)
    #cid = fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()
