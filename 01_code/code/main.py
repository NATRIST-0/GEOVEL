"""GEOVEL Application
This is the main entry point for the application.
It initializes the PyQt6 application, creates the main window, and starts the event loop.

comboBox_grad_method
"""

# ========== Imports ==========
import sys
import traceback
import pandas as pd
from pathlib import Path
from ui_mainwindow import Ui_MainWindow

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal, QObject, QThread
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QVBoxLayout,
)

from core.data_io import read_cnv_files, derive_plane_equations, export_processed_data
from core.map_coords import draw_localization_plot
from core.ctd_profiles import draw_ctd_profiles
from core.derive_geovel import derive_geostrophic_velocity
from core.velocity_profiles import draw_geovel_profiles
from core.hodograph import draw_hodograph

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar


# ========== Dummy Stream ==========
# to avoid crashes when the app tries to print to a console that doesn't exist
class DummyStream:
    def write(self, text):
        pass

    def flush(self):
        pass


if sys.stdout is None or getattr(sys.stdout, "closed", True):
    sys.stdout = DummyStream()
if sys.stderr is None or getattr(sys.stderr, "closed", True):
    sys.stderr = DummyStream()


# ========== Terminal Redirector ==========
class StreamRedirector(QObject):
    # first string is the print, second one is the color
    text_written = pyqtSignal(str, str)

    def __init__(self, color="black"):
        super().__init__()
        self.color = color

    def write(self, text):
        self.text_written.emit(str(text), self.color)

    def flush(self):
        pass


class Worker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    plot_requested = pyqtSignal(dict)

    def __init__(self, params):
        super().__init__()
        self.params = params  # stock the params sent by the UI

    def run(self):
        try:
            # Extracting the user inputs
            file_1 = self.params["file_1"]
            file_2 = self.params["file_2"]
            file_3 = self.params["file_3"]
            file_4 = self.params["file_4"]
            lat_1 = self.params["lat_1"]
            lat_2 = self.params["lat_2"]
            lat_3 = self.params["lat_3"]
            lat_4 = self.params["lat_4"]
            lon_1 = self.params["lon_1"]
            lon_2 = self.params["lon_2"]
            lon_3 = self.params["lon_3"]
            lon_4 = self.params["lon_4"]

            all_dfs = []
            output_dir = None

            for i, (file_path, lat, lon) in enumerate(
                [
                    (file_1, lat_1, lon_1),
                    (file_2, lat_2, lon_2),
                    (file_3, lat_3, lon_3),
                    (file_4, lat_4, lon_4),
                ],
                start=1,
            ):
                if not file_path:
                    print(f"File {i} path is empty. Skipping.")
                    continue

                p = Path(file_path)
                if not p.exists():
                    raise FileNotFoundError(f"File {i} not found: {file_path}")

                # Saving the output directory based on the first valid file
                if output_dir is None:
                    output_dir = p.parent

                print(f"\nProcessing File {i}: {file_path}")

                # Converting lat and lon to float
                try:
                    lat_val = float(lat) if lat else None
                    lon_val = float(lon) if lon else None
                except ValueError:
                    lat_val, lon_val = None, None
                    print(f"Warning: Could not parse coordinates for File {i}")

                # Calling the read_cnv_files function to read the .cnv file
                df_station = read_cnv_files(p, lat=lat_val, lon=lon_val)
                print(f"DataFrame for File {i}:\n{df_station.head()}")

                all_dfs.append(df_station)

            # Combining and Exporting DataFrames
            if all_dfs:
                # Keeping the combined data in the memory
                combined_df = pd.concat(all_dfs, ignore_index=True)

                # Applying the plane equations on it
                final_df, metadata = derive_plane_equations(combined_df)

                # Saving the final result
                output_name = "combined_CTD_profiles.csv"
                output_path = output_dir / output_name
                export_processed_data(final_df, metadata, output_path)

                print(
                    f"\nCombined data with plane equations exported to:\n{output_path}"
                )
            else:
                print("\nNo valid data found to process or export.")
                return

        except Exception as e:
            error_trace = traceback.format_exc()
            print(
                f"\n=== ERROR DETAILS ===\n{error_trace}\n=================",
                file=sys.stderr,
            )
            self.error.emit(str(e))  # if an error occurs it sends it to the UI
        finally:
            self.finished.emit()  # doesn't matter what happens we tell it to close itself
            print(
                "==============================",
            )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
            iconpath = str(Path(__file__).parent.parent / "resources" / "icon.ico")
            self.setWindowIcon(QIcon(iconpath))
            self.ui.stackedWidget.setCurrentIndex(0)

            # Console redirection
            # Standard Redirection -> black
            self.stdout_redirector = StreamRedirector(color="black")
            self.stdout_redirector.text_written.connect(self.append_to_console)
            sys.stdout = self.stdout_redirector
            # Errors redirections -> red
            self.stderr_redirector = StreamRedirector(color="red")
            self.stderr_redirector.text_written.connect(self.append_to_console)
            sys.stderr = self.stderr_redirector

            # Initialazing the matplotlib layout
            self.plot_layout = QVBoxLayout(self.ui.graph_layout)
            self.plot_layout.setContentsMargins(0, 0, 0, 0)
            # Creating the fig and canvas used for plotting (not possible in QtDesigner)
            self.figure = Figure(facecolor="#FAFAFA")
            self.canvas = FigureCanvas(self.figure)
            self.plot_layout.addWidget(self.canvas)
            self.ax = self.figure.add_subplot(111)

            self.plot_layout.addWidget(NavigationToolbar(self.canvas, self))
            self.plot_layout.addWidget(self.canvas)

            # Connect signals to slots
            self.ui.actionLoad.triggered.connect(self.load_data)
            self.ui.actionSave.triggered.connect(self.save_data)
            self.ui.actionClean.triggered.connect(self.clean_fields)

            self.ui.actionLoad_Data.triggered.connect(
                lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.page_load_data)
            )
            self.ui.actionCoordinates.triggered.connect(
                lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.page_coords)
            )
            self.ui.actionCTD_profiles.triggered.connect(
                lambda: self.ui.stackedWidget.setCurrentWidget(
                    self.ui.page_CTD_profiles
                )
            )
            self.ui.actionSpeed_Profiles.triggered.connect(
                lambda: self.ui.stackedWidget.setCurrentWidget(
                    self.ui.page_speed_profiles
                )
            )
            self.ui.actionHodograph.triggered.connect(
                lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.page_hodograph)
            )

            # Connect Buttons
            self.ui.pushButton_browse_file1.clicked.connect(
                lambda: self.browse_file(self.ui.lineEdit_file1)
            )
            self.ui.pushButton_browse_file2.clicked.connect(
                lambda: self.browse_file(self.ui.lineEdit_file2)
            )
            self.ui.pushButton_browse_file3.clicked.connect(
                lambda: self.browse_file(self.ui.lineEdit_file3)
            )
            self.ui.pushButton_browse_file4.clicked.connect(
                lambda: self.browse_file(self.ui.lineEdit_file4)
            )
            self.ui.pushButton_read_treat_data.clicked.connect(self.read_and_treat_data)
            self.ui.pushButton_coords_plot.clicked.connect(
                self.generate_localization_plot
            )
            self.ui.pushButton_CTD_plot.clicked.connect(self.generate_ctd_plot)
            self.ui.pushButton_speed_plot.clicked.connect(self.generate_speed_plot)
            self.ui.pushButton_hodograph.clicked.connect(self.generate_hodograph_plot)

            print("Application initialized.\n")
        except Exception as e:
            print(f"Error during initialization: {e}")

    def read_and_treat_data(self):
        """Reads and treats the data from the paths and location parameters."""
        print("==============================")

        self.ui.pushButton_read_treat_data.setEnabled(
            False
        )  # Unableling the run pushButton while the function is running
        try:
            params = {
                "file_1": self.ui.lineEdit_file1.text(),
                "file_2": self.ui.lineEdit_file2.text(),
                "file_3": self.ui.lineEdit_file3.text(),
                "file_4": self.ui.lineEdit_file4.text(),
                "lat_1": self.ui.lineEdit_lat1.text(),
                "lat_2": self.ui.lineEdit_lat2.text(),
                "lat_3": self.ui.lineEdit_lat3.text(),
                "lat_4": self.ui.lineEdit_lat4.text(),
                "lon_1": self.ui.lineEdit_lon1.text(),
                "lon_2": self.ui.lineEdit_lon2.text(),
                "lon_3": self.ui.lineEdit_lon3.text(),
                "lon_4": self.ui.lineEdit_lon4.text(),
            }

            empty_inputs = [
                key
                for key, value in params.items()
                if isinstance(value, str) and value.strip() == ""
            ]
            if empty_inputs:
                print(f"Inputs missing: {', '.join(empty_inputs)}")

        except Exception as e:
            print(f"Error collecting parameters: {e}")
            self.ui.pushButton_read_treat_data.setEnabled(True)
            return

        self.worker = Worker(params)  # Passing the params to the worker

        self.worker.finished.connect(self.on_pipeline_finished)
        self.worker.error.connect(self.on_pipeline_error)
        self.worker.plot_requested.connect(self.handle_plot_request)
        self.worker.start()  # Thread starting

    def on_pipeline_finished(self):
        self.ui.pushButton_read_treat_data.setEnabled(True)

    def on_pipeline_error(self, error_message):
        print(f"\nError: {error_message}", file=sys.stderr)

    def handle_plot_request(self, data):
        """Func called in the main thread where plt.show() won't crash"""
        try:
            pass
            # if step_plot == 5:
            #     plot_data_step5(
            #         df=data["df"],
            #     )

        except Exception as e:
            print(f"Error while plotting: {e}")

    def browse_file(self, target_widget, row=None, col=None):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")

        if file_path:
            try:
                if isinstance(target_widget, QLineEdit):
                    target_widget.setText(file_path)
                    print(f"Path updated to: {file_path}")

                elif isinstance(target_widget, QTableWidget):
                    if row is not None and col is not None:
                        item = target_widget.item(row, col)
                        if item is None:
                            item = QTableWidgetItem(file_path)
                            target_widget.setItem(row, col, item)
                        else:
                            item.setText(file_path)
                        print(
                            f"Path updated in table (row {row}, col {col}) to: {file_path}"
                        )
                    else:
                        print("Error: QTableWidget row or col is None.")

                elif isinstance(target_widget, QTableWidgetItem):
                    print(
                        "Error: QTableWidgetItem was parsed instead of a QTableWidget with 'row' & 'col'."
                    )

                else:
                    print(f"Object type not supported: {type(target_widget)}")

            except Exception as e:
                print(f"Error while browsing file: {e}")

    def append_to_console(self, text, color="black"):
        cursor = self.ui.textEdit_console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        char_format = QTextCharFormat()
        char_format.setForeground(QColor(color))
        cursor.setCharFormat(char_format)

        cursor.insertText(text)
        self.ui.textEdit_console.setTextCursor(cursor)
        self.ui.textEdit_console.ensureCursorVisible()

    def save_data(self):
        """Saves current UI parameters to a simple .txt file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "", "Text Files (*.txt)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w") as f:
                # Save file, lat and lon parameters
                for i in range(1, 5):
                    f.write(
                        f"file_{i}={getattr(self.ui, f'lineEdit_file{i}').text()}\n"
                    )
                    f.write(f"lat_{i}={getattr(self.ui, f'lineEdit_lat{i}').text()}\n")
                    f.write(f"lon_{i}={getattr(self.ui, f'lineEdit_lon{i}').text()}\n")

            print(f"Configuration saved to {file_path}")
        except Exception as e:
            print(f"Error saving file: {e}")

    def load_data(self):
        """Loads parameters from a .txt file into the UI."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "Text Files (*.txt)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            for line in lines:
                if "=" not in line:
                    continue
                key, value = line.strip().split("=", 1)
                file_keys = (
                    "file_1",
                    "file_2",
                    "file_3",
                    "file_4",
                )
                lat_keys = (
                    "lat_1",
                    "lat_2",
                    "lat_3",
                    "lat_4",
                )
                lon_keys = (
                    "lon_1",
                    "lon_2",
                    "lon_3",
                    "lon_4",
                )

                if key in file_keys:
                    widget = getattr(
                        self.ui, f"lineEdit_file{file_keys.index(key) + 1}"
                    )
                    widget.setText(value)

                elif key in lat_keys:
                    widget = getattr(self.ui, f"lineEdit_lat{lat_keys.index(key) + 1}")
                    widget.setText(value)

                elif key in lon_keys:
                    widget = getattr(self.ui, f"lineEdit_lon{lon_keys.index(key) + 1}")
                    widget.setText(value)

            print(f"Configuration loaded from {file_path}")
        except Exception as e:
            print(f"Error loading file: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load configuration:\n{e}")

    def clean_fields(self):
        """Resets all fields to empty or default states."""
        try:
            self.ui.lineEdit_no_motion_level.clear()
            self.ui.comboBox_CTD.setCurrentIndex(0)
            self.ui.spinBox_resolution.setValue(5)
            self.ui.checkBox_avg_CTD_vals.setChecked(False)
            self.ui.checkBox_avg_T_vals.setChecked(False)

            for i in range(1, 5):
                getattr(self.ui, f"lineEdit_file{i}").clear()
                getattr(self.ui, f"lineEdit_lat{i}").clear()
                getattr(self.ui, f"lineEdit_lon{i}").clear()

            print("Fields cleaned.")
        except Exception as e:
            print(f"Error while cleaning fields: {e}")

    def generate_localization_plot(self):
        """Gathering station data from the UI and generating the localization plot."""

        self.figure.clear()  # Wipes the entire figure clean
        self.ax = self.figure.add_subplot(111)  # Creates a fresh, untainted axis

        try:

            base_file = (
                self.ui.lineEdit_file1.text()
                or self.ui.lineEdit_file2.text()
                or self.ui.lineEdit_file3.text()
                or self.ui.lineEdit_file4.text()
            )

            if not base_file:
                raise ValueError("No files loaded. Please load and treat data first.")

            csv_path = Path(base_file).parent / "combined_CTD_profiles.csv"
            
            # Calling the plotting function
            draw_localization_plot(self.ax, csv_path)

            self.canvas.draw()
            print("Localization plot updated.")

        except ValueError as e:
            print(
                f"Error: Invalid coordinate format. Please ensure you enter valid numbers. ({e})",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"Error while generating localization plot: {e}", file=sys.stderr)

    def generate_ctd_plot(self):
        """Gathering configuration and drawing the CTD profiles."""

        self.figure.clear()  # Wipes the entire figure clean
        self.ax = self.figure.add_subplot(111)  # Creates a fresh, untainted axis

        try:
            plot_type = self.ui.comboBox_CTD.currentText()

            base_file = (
                self.ui.lineEdit_file1.text()
                or self.ui.lineEdit_file2.text()
                or self.ui.lineEdit_file3.text()
                or self.ui.lineEdit_file4.text()
            )

            if not base_file:
                raise ValueError("No files loaded. Please load and treat data first.")

            csv_path = Path(base_file).parent / "combined_CTD_profiles.csv"
            show_avg = self.ui.checkBox_avg_CTD_vals.isChecked()

            draw_ctd_profiles(self.ax, csv_path, plot_type, show_avg)

            self.canvas.draw()
            print(f"{plot_type} plot updated.")

        except Exception as e:
            print(f"Error while generating {plot_type} plot: {e}", file=sys.stderr)

    def generate_speed_plot(self):
        """Calculates velocities based on UI input and updates the plot."""

        self.figure.clear()  # Wipes the entire figure clean
        self.ax = self.figure.add_subplot(111)  # Creates a fresh, untainted axis

        try:
            level_text = self.ui.lineEdit_no_motion_level.text().strip()
            if not level_text:
                raise ValueError(
                    "Please enter a valid depth for the level of no motion."
                )

            level_of_no_motion = float(level_text)

            base_file = (
                self.ui.lineEdit_file1.text()
                or self.ui.lineEdit_file2.text()
                or self.ui.lineEdit_file3.text()
                or self.ui.lineEdit_file4.text()
            )

            if not base_file:
                raise ValueError("No files loaded. Please load and treat data first.")
            csv_path = Path(base_file).parent / "combined_CTD_profiles.csv"
            show_avg = self.ui.checkBox_avg_T_vals.isChecked()

            derive_geostrophic_velocity(csv_path, level_of_no_motion)
            draw_geovel_profiles(self.ax, csv_path, show_avg)

            self.canvas.draw()
            print(
                f"Geostrophic velocities updated with reference level at {level_of_no_motion}m."
            )

        except Exception as e:
            print(f"Unexpected error while generating speed plot: {e}", file=sys.stderr)

    def generate_hodograph_plot(self):
        """Calculates velocities based on the hodograph page input and generates the plot."""

        self.figure.clear()  # Wipes the entire figure clean
        self.ax = self.figure.add_subplot(111)  # Creates a fresh, untainted axis

        try:
            level_text = (
                getattr(
                    self.ui,
                    "lineEdit_no_motion_level_2",
                    self.ui.lineEdit_no_motion_level_2,
                )
                .text()
                .strip()
            )

            if not level_text:
                raise ValueError(
                    "Please enter a valid depth for the level of no motion."
                )

            level_of_no_motion = float(level_text)

            base_file = (
                self.ui.lineEdit_file1.text()
                or self.ui.lineEdit_file2.text()
                or self.ui.lineEdit_file3.text()
                or self.ui.lineEdit_file4.text()
            )

            if not base_file:
                raise ValueError("No files loaded. Please load and treat data first.")

            csv_path = Path(base_file).parent / "combined_CTD_profiles.csv"

            # Recalculate geostrophic velocities using the new reference level in casee it changes
            derive_geostrophic_velocity(csv_path, level_of_no_motion)

            resolution_step = self.ui.spinBox_resolution.value()
            data_source = self.ui.comboBox_hodograph_from.currentText()

            draw_hodograph(self.ax, csv_path, data_source, resolution_step)
            self.canvas.draw()

            print(
                f"Hodograph updated (Reference level: {level_of_no_motion}m, Resolution: {resolution_step}m)."
            )

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
        except Exception as e:
            print(
                f"Unexpected error while generating hodograph plot: {e}",
                file=sys.stderr,
            )


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Global exception handler to catch unhandled exceptions and print them to stderr."""
    # Formatting the error
    traceback_details = "".join(
        traceback.format_exception(exc_type, exc_value, exc_traceback)
    )
    # Print it in stderr
    print(
        f"\n=== UNHANDLED ERROR ===\n{traceback_details}\n=======================",
        file=sys.stderr,
    )


# ========== Run ==========
if __name__ == "__main__":
    app = QApplication(sys.argv)
    sys.excepthook = global_exception_handler
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
