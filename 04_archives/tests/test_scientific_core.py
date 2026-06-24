from pathlib import Path
import sys
import unittest

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APPLICATION_ROOT = PROJECT_ROOT / "3d_visualization"
sys.path.insert(0, str(APPLICATION_ROOT))

from Ocean.Processing.cnv import read_cnv_vars
from Ocean.Processing.coords import load_xy_from_csv
from Ocean.Processing.ekman import compute_surface_ekman
from Ocean.Processing.figures import (
    fig_coords_static,
    fig_profiles_static,
    fig_vectors_static,
    fig_velocity_static,
)
from Ocean.Processing.pipeline import (
    STATIONS,
    run_geostrophic_pipeline,
    select_column_on_grid,
)


DATA_ROOT = APPLICATION_ROOT / "Data"
COORDINATES_PATH = DATA_ROOT / "Coords" / "stations_banyuls.csv"
CNV_PATHS = {
    station: DATA_ROOT / "Cnv" / f"{station}.cnv" for station in STATIONS
}


class ScientificCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = run_geostrophic_pipeline(COORDINATES_PATH, CNV_PATHS, z_ref=50)

    def test_reads_operational_cnv_files(self):
        references = {
            "nord": {
                "levels": 60,
                "last_depth": 60.0,
                "first": (1026.5154, 37.8581, 21.5761),
                "last": (1028.3392, 38.0737, 16.1664),
            },
            "est": {
                "levels": 82,
                "last_depth": 82.0,
                "first": (1026.5949, 37.9676, 21.5902),
                "last": (1028.7144, 38.1296, 15.1538),
            },
            "sud": {
                "levels": 58,
                "last_depth": 58.0,
                "first": (1026.6301, 38.0170, 21.5988),
                "last": (1028.1966, 38.0550, 16.6665),
            },
            "ouest": {
                "levels": 57,
                "last_depth": 57.0,
                "first": (1026.6578, 38.0072, 21.4737),
                "last": (1028.2522, 38.0744, 16.4785),
            },
        }

        for station, reference in references.items():
            with self.subTest(station=station):
                profile = read_cnv_vars(CNV_PATHS[station])
                self.assertEqual(
                    list(profile.columns),
                    ["depth", "density", "salinity", "temperature"],
                )
                self.assertEqual(len(profile), reference["levels"])
                self.assertEqual(float(profile["depth"].iloc[0]), 1.0)
                self.assertEqual(
                    float(profile["depth"].iloc[-1]),
                    reference["last_depth"],
                )
                self.assertTrue(np.all(np.diff(profile["depth"]) > 0))
                np.testing.assert_allclose(
                    profile.loc[profile.index[0], ["density", "salinity", "temperature"]],
                    reference["first"],
                    rtol=0.0,
                    atol=1e-4,
                )
                np.testing.assert_allclose(
                    profile.loc[profile.index[-1], ["density", "salinity", "temperature"]],
                    reference["last"],
                    rtol=0.0,
                    atol=1e-4,
                )

    def test_loads_station_coordinates(self):
        xy, meta = load_xy_from_csv(COORDINATES_PATH)

        self.assertEqual(set(xy), set(STATIONS))
        self.assertAlmostEqual(meta["lat0"], 42.483, places=12)
        self.assertAlmostEqual(meta["lon0"], 3.18825, places=12)
        self.assertAlmostEqual(meta["kx"], 82096.0238, places=4)
        self.assertAlmostEqual(meta["ky"], 111320.0, places=8)

        expected_xy = {
            "nord": (-20.5240, 890.5600),
            "est": (1046.7243, 0.0),
            "sud": (-102.6200, -890.5600),
            "ouest": (-923.5803, 0.0),
        }
        for station, expected in expected_xy.items():
            with self.subTest(station=station):
                np.testing.assert_allclose(xy[station], expected, rtol=0.0, atol=1e-4)

        np.testing.assert_allclose(
            np.sum(np.array(list(xy.values())), axis=0),
            (0.0, 0.0),
            rtol=0.0,
            atol=1e-9,
        )

    def test_runs_geostrophic_pipeline_at_50_metres(self):
        result = self.pipeline

        self.assertEqual(len(result["z"]), 57)
        self.assertEqual(int(result["z"][0]), 1)
        self.assertEqual(int(result["z"][-1]), 57)
        self.assertEqual(result["z_ref"], 50)
        self.assertAlmostEqual(result["rho0"], 1027.5379574561402, places=10)
        self.assertAlmostEqual(result["f"], 9.849751911572252e-5, places=16)

        for name in ("drdx", "drdy", "u", "v"):
            with self.subTest(array=name):
                self.assertEqual(result[name].shape, (57,))

        reference_index = int(np.where(result["z"] == 50)[0][0])
        self.assertEqual(float(result["u"][reference_index]), 0.0)
        self.assertEqual(float(result["v"][reference_index]), 0.0)

        references = {
            1: (-2.83024e-5, -6.30932e-5, 0.0324934, 0.1638680),
            25: (-1.04884e-4, 1.52185e-6, 0.1418046, -0.0280057),
            50: (8.70632e-5, 6.56623e-5, 0.0, 0.0),
            57: (9.04531e-5, 6.56184e-5, -0.0442504, 0.0626476),
        }
        for depth, expected in references.items():
            with self.subTest(depth=depth):
                index = int(np.where(result["z"] == depth)[0][0])
                observed = tuple(
                    float(result[name][index]) for name in ("drdx", "drdy", "u", "v")
                )
                np.testing.assert_allclose(observed, expected, rtol=0.0, atol=5e-8)

    def test_computes_surface_ekman_with_historical_defaults(self):
        result = compute_surface_ekman(
            wind_speed=8.0,
            drag_coefficient=1.5e-3,
            air_density=1.3,
            water_density=1025.0,
            eddy_viscosity=0.01,
            wind_direction=0.0,
            latitude=42.483,
        )

        self.assertEqual(result["errors"], [])
        self.assertAlmostEqual(result["f"], 9.849751911572252e-5, places=16)
        self.assertAlmostEqual(result["wind_stress"], 0.1248, places=12)
        self.assertAlmostEqual(result["surface_speed"], 0.12268121656025587, places=14)
        np.testing.assert_allclose(
            (result["wind_vector"]["x"], result["wind_vector"]["y"]),
            (0.0, 8.0),
            rtol=0.0,
            atol=1e-14,
        )
        np.testing.assert_allclose(
            (result["ekman_vector"]["x"], result["ekman_vector"]["y"]),
            (0.0867487, 0.0867487),
            rtol=0.0,
            atol=5e-8,
        )

    def test_main_figure_functions_return_matplotlib_figures(self):
        result = self.pipeline
        density_series = {
            station: select_column_on_grid(profile, result["z"], "density")
            for station, profile in result["stations"].items()
        }
        figures = [
            fig_coords_static(result["xy"], result["meta"]),
            fig_profiles_static(result["z"], density_series),
            fig_velocity_static(result["z"], result["u"], result["v"], result["z_ref"]),
            fig_vectors_static(result["z"], result["u"], result["v"], result["z_ref"]),
        ]

        try:
            for figure in figures:
                with self.subTest(figure=figure):
                    self.assertIsInstance(figure, Figure)
        finally:
            for figure in figures:
                plt.close(figure)


if __name__ == "__main__":
    unittest.main()
