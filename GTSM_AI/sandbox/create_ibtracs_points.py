# %%

from pathlib import Path
from datetime import datetime

import cht_cyclones as cht
from cht_cyclones import CycloneTrackDatabase
import numpy as np
import matplotlib.pyplot as plt

from ibtracs_utils import get_uvp_timeseries

# %%

data_dir = Path(r"p:\11213404-futura\00_data\tropical_cyclone_tracks")
ibtracs_fn = data_dir / "ibtracs" / "IBTrACS.ALL.v04r01.nc"

dateformat = "%Y%m%d %H%M%S"

tracknames = {
    'Katrina': 2005, # Mississippi / Louisiana storm surge
    'Sandy': 2012, # New York City storm surge
    'Isabel': 2003, # storm surge in Chesapeake Bay
    'Irene': 2011, #storm surge in North Carolina
    'Floyd': 1999, # Storm surge in North Carolina
    'Rita': 2005, # Storm surge in Texas
    'Ike': 2008, # Storm surge in Texas
    'Ida': 2021, # Storm surge in Louisiana
    'Michael': 2018, # Storm surge in Florida Panhandle
}

points = [(-60, 15), (-63, 25), (-65, 30)]
# %%

db = CycloneTrackDatabase(
    path=data_dir,
    check_online=False
)

dataset = db.dataset[0]
dataset.read()
dataset.ds
# %%

id = 0

track_name = list(tracknames.keys())[id]
track_season = tracknames[track_name]
id = dataset.filter(name=track_name, year=track_season)

# %%


tc = dataset.get_track(id[0])

# %%

[u,v,p] = get_uvp_timeseries(tc, points)

# %%

time = tc.track_metric.gdf.datetime.values

fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

for ax in axes:
    ax.grid()
    ax.set_ylabel('m/s')

axes[0].plot(time, u)
axes[1].plot(time, v)
axes[2].plot(time, p)

axes[-1].set_xlabel('Time')

# %%

from datetime import datetime
import xarray as xr

dates = [datetime.strptime(str(t), "%Y%m%d %H%M%S") for t in time]
lat = [p[1] for p in points]
lon = [p[0] for p in points]

# %%

ds = xr.Dataset(
    data_vars={
        "wind_x": (("time", "station_id"), u),
        "wind_y": (("time", "station_id"), v),
        "pressure": (("time", "station_id"), p),
    },
    coords={
        "time": dates,
        # "station_id": np.arange(len(points)),
        "station_id": [f"point_{i}" for i in range(len(points))],
        "station_y_coordinate": ("station_id", lat),
        "station_x_coordinate": ("station_id", lon),
    }
)
# %%

ds.to_netcdf("test_track_series.nc")
# %%

from itertools import product

lat_range = np.arange(15,30,0.5)
lon_range = np.arange(-65,-60,0.5)

point_list = list(product(lon_range, lat_range))

list_frac = [0.01, 0.1, 0.25, 0.5, 0.75, 1.0]
# list_frac = [0.01, 0.1]

track_ids = range(len(tracknames))

timings = np.zeros((len(list_frac), len(track_ids)))
timings_per_point = np.zeros((len(list_frac), len(track_ids)))
timings_per_timestep = np.zeros((len(list_frac), len(track_ids)))

npoints = np.zeros(len(list_frac))
ntimesteps = np.zeros(len(track_ids))

# %%

for id in track_ids:
    for (frac_id, frac) in enumerate(list_frac):
        track_name = list(tracknames.keys())[id]
        track_season = tracknames[track_name]
        id_track = dataset.filter(name=track_name, year=track_season)
        tc = dataset.get_track(id_track[0])

        n_points = int(frac * len(point_list))
        points = point_list[:n_points]

        t0 = datetime.now()
        [u,v,p] = get_uvp_timeseries(tc, points)
        t1 = datetime.now()

        npoints[frac_id] = n_points
        ntimesteps[id] = len(tc.track_metric.gdf.datetime.values)

        timings[frac_id, id] = (t1 - t0).total_seconds()
        timings_per_point[frac_id, id] = timings[frac_id, id] / n_points
        timings_per_timestep[frac_id, id] = timings[frac_id, id] / len(tc.track_metric.gdf.datetime.values)
# %%

idxs = np.argsort(ntimesteps)
ntimesteps = ntimesteps[idxs]

timings = timings[:, idxs]


fig, axes = plt.subplots(3, 1, figsize=(10, 8))

c0 = axes[0].pcolor(ntimesteps, npoints, timings, shading="nearest")
axes[0].set_title("Total time (s)")
axes[0].set_xlabel("Number of timesteps")
axes[0].set_ylabel("Number of points")
fig.colorbar(c0, ax=axes[0], label="Total time (s)")

c1 = axes[1].pcolor(ntimesteps, npoints, timings_per_point)
axes[1].set_title("Time per point (s)")
axes[1].set_xlabel("Number of timesteps")
axes[1].set_ylabel("Number of points")
fig.colorbar(c1, ax=axes[1], label="Time per point (s)")

c2 = axes[2].pcolor(ntimesteps, npoints, timings_per_timestep)
axes[2].set_title("Time per timestep (s)")
axes[2].set_xlabel("Number of timesteps")
axes[2].set_ylabel("Number of points")
fig.colorbar(c2, ax=axes[2], label="Time per timestep (s)")

plt.subplots_adjust(hspace=0.5)

# %%
