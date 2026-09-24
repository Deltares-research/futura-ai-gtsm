import numpy as np

import cht_cyclones as cht
from cht_cyclones.wind_profiles import holland2010
from cht_cyclones.fit_holland_2010 import fit_wind_field_holland2010
from tqdm import tqdm

knots_to_ms = 0.514444
datefmt = "%Y%m%d %H%M%S"


def _calc_hav_dist(point1, point2):
    """
    Calculate the haversine distance between two points on the earth specified in decimal degrees.
    """
    # convert decimal degrees to radians
    lon1, lat1 = np.radians(point1)
    lon2, lat2 = np.radians(point2)

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    theta = 2 * np.arcsin(np.sqrt(a))
    r = 6371000.0  # Radius of earth in meters
    return theta * r, theta  # distance in meters, angle in radians


def _wind_press_single_timestep(tc_gdf, points, config):
    quadrants_speed = (
        np.array([35.0, 50.0, 65.0, 100.0])
        * knots_to_ms
        * config["wind_conversion_factor"]
    )
    quadrants_radii = np.zeros((4, 4))
    quadrants_radii[0, 0] = tc_gdf.r35_ne
    quadrants_radii[0, 1] = tc_gdf.r35_se
    quadrants_radii[0, 2] = tc_gdf.r35_sw
    quadrants_radii[0, 3] = tc_gdf.r35_nw
    quadrants_radii[1, 0] = tc_gdf.r50_ne
    quadrants_radii[1, 1] = tc_gdf.r50_se
    quadrants_radii[1, 2] = tc_gdf.r50_sw
    quadrants_radii[1, 3] = tc_gdf.r50_nw
    quadrants_radii[2, 0] = tc_gdf.r65_ne
    quadrants_radii[2, 1] = tc_gdf.r65_se
    quadrants_radii[2, 2] = tc_gdf.r65_sw
    quadrants_radii[2, 3] = tc_gdf.r65_nw
    quadrants_radii[3, 0] = tc_gdf.r100_ne
    quadrants_radii[3, 1] = tc_gdf.r100_se
    quadrants_radii[3, 2] = tc_gdf.r100_sw
    quadrants_radii[3, 3] = tc_gdf.r100_nw

    vmax = tc_gdf.vmax
    pc = tc_gdf.pc
    dpcdt = tc_gdf.dpcdt
    rmax = tc_gdf.rmw
    lat, lon = tc_gdf.geometry.y, tc_gdf.geometry.x
    pn = config["background_pressure"]
    phia = config["phi_trans"] * np.pi / 180.0
    dp = pn - pc
    xn = 0.5

    dist = np.array([(r / 1000, 180.0 * phi / np.pi) for (r, phi) in [_calc_hav_dist((lon, lat), point) for point in points]])
    r = dist[:, 0]
    phi = dist[:, 1]

    vt = np.sqrt(tc_gdf.vtx ** 2 + tc_gdf.vty ** 2)
    phit = 180.0 * np.arctan2(tc_gdf.vtx, tc_gdf.vty) / np.pi

    if config["asymmetry_option"] == "schwerdt1979":
        a = vt / knots_to_ms  # convert back to kts
        vtcor = 1.5 * a ** 0.63 * knots_to_ms
    elif config["asymmetry_option"] == "mvo":
        vtcor = vt * 0.6
    elif config["asymmetry_option"] == "none":
        vtcor = 0.0
    else:
        raise Exception("This asymmetry_option is not supported")

    if config["wind_profile"] == "holland2010":
        fit_wind = False
        if np.sum(~np.isnan(quadrants_radii)) > 0:
            fit_wind = True

        if fit_wind:
            obs = {
                "quadrants_speed": quadrants_speed,
                "quadrants_radii": quadrants_radii,
            }
            [xn, vtcor, phia] = fit_wind_field_holland2010(
                vmax,
                rmax,
                pc,
                vt,
                phit,
                pn,
                config["phi_spiral"],
                lat,
                dpcdt,
                obs
            )

    if config["wind_profile"] == "holland2008":
        xn = 0.6 * (1 - dp / 215)

    if config["wind_profile"] == "holland1980" or config["wind_profile"] == "holland2010":
        vrel = vmax - vtcor
        [vr, pr] = holland2010(
            r, vrel, pc, pn, rmax, dpcdt, lat, vt, xn
        )
    else:
        raise Exception("This wind_profile is not supported")

    if lat >= 0:
        phi = 90.0 + phi + config["phi_spiral"]
    else:
        phi = -90.0 + phi - config["phi_spiral"]

    u_prop = vtcor * np.cos((phit + phia) * np.pi / 180.0)
    v_prop = vtcor * np.sin((phit + phia) * np.pi / 180.0)

    wind_x = vr * np.cos(phi * np.pi / 180.0) + u_prop
    wind_y = vr * np.sin(phi * np.pi / 180.0) + v_prop

    return [wind_x, wind_y, 100*pr]


def get_uvp_timeseries(tc, points):
    wind_x_series = []
    wind_y_series = []
    pressure_series = []

    tc.track.gdf[tc.track.gdf.select_dtypes(include=["float32"]).columns] = \
        tc.track.gdf.select_dtypes(include=["float32"]).astype("float64")

    tc.compute_metric_track()
    tc.track_metric.compute_forward_speed()
    tc.track_metric.estimate_missing_values(tc.config)

    tc_gdf = tc.track_metric.gdf.sort_values("datetime")

    for timestep in tqdm(tc_gdf.itertuples()):
        [wind_x, wind_y, pressure] = _wind_press_single_timestep(timestep, points, tc.config)
        wind_x_series.append(wind_x)
        wind_y_series.append(wind_y)
        pressure_series.append(pressure)

    return np.array(wind_x_series), np.array(wind_y_series), np.array(pressure_series)