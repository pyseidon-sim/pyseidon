"""
    Simulator profiler: profiles the resources usage of the simulator

    This script runs an instance of the simulator and tracks CPU and
    RAM usage of the process. The process is forced to run on a single
    CPU.

    To use this tool simply run `python profiler.py`.

    In addition to the dependencies listed in requirements.txt you
    also need the following to run this script:

    - matplotlib
    - psutil
    - bitmath
"""

import time
import psutil
from bitmath import Byte, ALL_UNIT_TYPES
import matplotlib.pyplot as plt
import matplotlib.animation as animation


MSEC_PER_SEC = 1000
PLOT_DELAY = 1 * MSEC_PER_SEC
DATA_POINTS_LIMIT = 200


process = psutil.Popen([
    "python",
    "main.py",
    "--graphics",
    "n",
    "--out",
    "/dev/null",
    "--verbose",
    "n"
])
# Force using a single CPU
process.cpu_affinity(cpus=[1])
start_time = int(time.time())

time_points, cpu_data, ram_data = [], [], []

# Setup the plot
fig, (cpu_ax, ram_ax) = plt.subplots(
    nrows=2,
    figsize=(8, 12),
    num="Simulation Profiler")

# Set up the CPU plot
cpu_ax.set_xlabel("Elapsed seconds")
cpu_ax.set_ylabel("CPU %")
cpu_ax.set_title("CPU usage")

cpu_ax.set_ylim(0, 100)
cpu_ax.set_xlim(0, 30)

cpu_ax.grid()

cpu_line, = cpu_ax.plot([], [], color="#F39C12")
cpu_line.set_data(time_points, cpu_data)

# Set up the RAM plot
ram_ax.set_xlabel("Elapsed seconds")
ram_ax.set_ylabel("RAM usage (MB)")
ram_ax.set_title("RAM usage")

ram_ax.set_ylim(0, 100)
ram_ax.set_xlim(0, 30)

ram_ax.grid()

ram_line, = ram_ax.plot([], [], color="#3498db")
ram_line.set_data(time_points, ram_data)

def refresh_stats(unit='MB'):
    assert unit in ALL_UNIT_TYPES, "Invalid unit"
    
    while True:
        # Refresh the stats
        elapsed_seconds = int(time.time()) - start_time
        cpu_percent = process.cpu_percent()
        ram = float(getattr(Byte(process.memory_info().rss), unit))

        yield elapsed_seconds, cpu_percent, ram

def run(data):
    elapsed_seconds, cpu_percent, ram = data

    time_points.append(elapsed_seconds)
    cpu_data.append(cpu_percent)
    ram_data.append(ram)

    xmin, xmax = cpu_ax.get_xlim()
    ram_ymin, ram_ymax = ram_ax.get_ylim()

    if elapsed_seconds >= xmax:
        duplicate_x_ax_size(cpu_ax, xmin, xmax)
        duplicate_x_ax_size(ram_ax, xmin, xmax)

    # Update the ram maximum limit
    if ram_ymax < ram:
        ram_ax.set_ylim(ram_ymin, ram * 1.5)

    # Limit the amount of data points shown to DATA_POINTS_LIMIT
    xmin, xmax = cpu_ax.get_xlim()
    if len(time_points) > DATA_POINTS_LIMIT:
        time_points.pop(0)
        cpu_data.pop(0)
        ram_data.pop(0)

        cpu_ax.set_xlim(xmin + 1, xmax)
        ram_ax.set_xlim(xmin + 1, xmax)

    cpu_line.set_data(time_points, cpu_data)
    ram_line.set_data(time_points, ram_data)

    return cpu_line,

def duplicate_x_ax_size(ax, xmin, xmax):
    ax.set_xlim(xmin, 2 * xmax)
    ax.figure.canvas.draw()

plot_animation = animation.FuncAnimation(
    fig,
    run,
    refresh_stats,
    blit=False,
    interval=PLOT_DELAY,
    repeat=False)

plt.show()
process.kill()