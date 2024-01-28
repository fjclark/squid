"""Main TUI implementation for squid

Author: Finlay Clark  
Created: 2024
"""
import py_cui

from .slurm import SlurmQueue, NAMES_TO_JOB_ATTRIBUTES, SlurmJob
from .logo import LOGO

from . import app_layout

# Create a fake job to use as a banner
slurm_banner_fake_job = SlurmJob(
    job_id="Job ID",
    name="Name",
    partition="Partition",
    time_used="Time",
    submit_time="Submit Time",
    start_time="Start Time",
    end_time="End Time",
    state="State",
    node_list="Node/Reason",
    array_job_id="Ar.J.Id",
    array_task_id="Ar.T.Id",
)


class SquidApp:
    """Main application class for squid"""

    def __init__(self, master: py_cui.PyCUI):
        self.master = master
        self.slurm_queue = SlurmQueue()
        self.job_filter_attribute = "name"
        self.job_filter_regex = ""

        self.create_display_objects()
        self.set_display_colours()
        self.set_focus_text()
        self.add_display_functionality()

    def create_display_objects(self):
        """Create the display objects, without adding functionality or setting colors"""
        self.job_display = self.master.add_scroll_menu(
            "Selected Jobs",
            app_layout.JOB_DISPLAY_ROW,
            app_layout.JOB_DISPLAY_COL,
            app_layout.JOB_DISPLAY_ROW_SPAN,
            app_layout.JOB_DISPLAY_COL_SPAN,
        )
        self.kill_all_button = self.master.add_button(
            "Kill Selected",
            app_layout.KILL_ALL_BUTTON_ROW,
            app_layout.KILL_ALL_BUTTON_COL,
            app_layout.KILL_ALL_BUTTON_ROW_SPAN,
            app_layout.KILL_ALL_BUTTON_COL_SPAN,
            command=self.kill_all_jobs,
        )
        self.hold_all_button = self.master.add_button(
            "Hold Selected",
            app_layout.HOLD_ALL_BUTTON_ROW,
            app_layout.HOLD_ALL_BUTTON_COL,
            app_layout.HOLD_ALL_BUTTON_ROW_SPAN,
            app_layout.HOLD_ALL_BUTTON_COL_SPAN,
            command=self.hold_all_jobs,
        )
        self.release_all_button = self.master.add_button(
            "Release Selected",
            app_layout.RELEASE_ALL_BUTTON_ROW,
            app_layout.RELEASE_ALL_BUTTON_COL,
            app_layout.RELEASE_ALL_BUTTON_ROW_SPAN,
            app_layout.RELEASE_ALL_BUTTON_COL_SPAN,
            command=self.release_all_jobs,
        )
        self.refresh_button = self.master.add_button(
            "Refresh Display",
            app_layout.REFRESH_BUTTON_ROW,
            app_layout.REFRESH_BUTTON_COL,
            app_layout.REFRESH_BUTTON_ROW_SPAN,
            app_layout.REFRESH_BUTTON_COL_SPAN,
            command=self.update_jobs,
        )
        self.filter_attribute_input = self.master.add_scroll_menu(
            "Filter By",
            app_layout.FILTER_ATTRIBUTE_INPUT_ROW,
            app_layout.FILTER_ATTRIBUTE_INPUT_COL,
            app_layout.FILTER_ATTRIBUTE_INPUT_ROW_SPAN,
            app_layout.FILTER_ATTRIBUTE_INPUT_COL_SPAN,
        )
        self.filter_regex_input = self.master.add_text_box(
            "Filter Regex",
            app_layout.FILTER_REGEX_INPUT_ROW,
            app_layout.FILTER_REGEX_INPUT_COL,
            app_layout.FILTER_REGEX_INPUT_ROW_SPAN,
            app_layout.FILTER_REGEX_INPUT_COL_SPAN,
        )
        self.logo = self.master.add_block_label(
            LOGO,
            app_layout.LOGO_ROW,
            app_layout.LOGO_COL,
            app_layout.LOGO_ROW_SPAN,
            app_layout.LOGO_COL_SPAN,
        )

        # Store lists of the objects by type.
        self.labels = [self.logo]
        self.buttons = [
            self.kill_all_button,
            self.hold_all_button,
            self.release_all_button,
            self.refresh_button,
        ]
        self.scroll_menus = [self.job_display, self.filter_attribute_input]
        self.block_labels = [self.filter_regex_input]

    def set_display_colours(self):
        """Set the colours for the display objects"""
        for label in self.labels:
            label.set_color(py_cui.WHITE_ON_BLACK)
        for button in self.buttons:
            button.set_color(py_cui.BLUE_ON_BLACK)
        for scroll_menu in self.scroll_menus:
            scroll_menu.set_color(py_cui.BLUE_ON_BLACK)
            scroll_menu.set_selected_color(py_cui.RED_ON_BLACK)

    def set_focus_text(self):
        """Set the focus text for the display objects"""
        self.job_display.set_focus_text(
            "Focus mode on Selected Jobs || Esc: Exit || Up/Down/PgUp/PgDown/Home/End: Scroll || k: Kill job || h: Hold job || r: Release job || u: Update job display"
        )
        self.filter_attribute_input.set_focus_text(
            "Focus mode on Filter By || Esc: Exit || Up/Down/PgUp/PgDown/Home/End: Scroll"
        )
        self.filter_regex_input.set_focus_text(
            "Focus mode on Filter Regex || Esc: Exit || Enter: Apply filter || Enter empty string to show all jobs"
        )

    def add_display_functionality(self):
        """Add required functionality to display objects"""
        # Add key bindings
        self.job_display.add_key_command(py_cui.keys.KEY_H_LOWER, self.hold_job)
        self.job_display.add_key_command(py_cui.keys.KEY_K_LOWER, self.kill_job)
        self.job_display.add_key_command(py_cui.keys.KEY_R_LOWER, self.release_job)
        self.job_display.add_key_command(py_cui.keys.KEY_U_LOWER, self.update_jobs)
        # Make the highlighted job red
        self.job_display.set_selected_color(py_cui.RED_ON_BLACK)
        # Make the highted widget red
        self.job_display.set_focus_border_color(py_cui.RED_ON_BLACK)
        self.filter_attribute_input.set_focus_border_color(py_cui.RED_ON_BLACK)
        self.filter_regex_input.set_focus_border_color(py_cui.RED_ON_BLACK)

        # Make default outlines blue.
        self.job_display.set_color(py_cui.BLUE_ON_BLACK)
        self.filter_attribute_input.set_color(py_cui.BLUE_ON_BLACK)
        self.filter_regex_input.set_color(py_cui.BLUE_ON_BLACK)

        # Add the job attributes to the filter attribute input
        for attribute in NAMES_TO_JOB_ATTRIBUTES:
            self.filter_attribute_input.add_item(attribute)

        # Make regex change self.filter_regex
        self.filter_regex_input.add_key_command(
            py_cui.keys.KEY_ENTER, self.set_filter_regex
        )

    def update_jobs(self):
        """Update the job display"""
        self.job_display.clear()
        self.slurm_queue.update(self.job_filter_attribute, self.job_filter_regex)
        self.job_display.add_item(slurm_banner_fake_job)
        for job in self.slurm_queue.jobs:
            self.job_display.add_item(job)

    def kill_job(self):
        """Kill selected job"""
        self.slurm_queue.kill_job(self.job_display.get())
        self.update_jobs()

    def hold_job(self):
        """Hold selected job"""
        self.slurm_queue.hold_job(self.job_display.get())
        self.update_jobs()

    def release_job(self):
        """Release selected job"""
        self.slurm_queue.release_job(self.job_display.get())
        self.update_jobs()

    def kill_all_jobs(self):
        """Kill all jobs"""
        for job in self.slurm_queue.jobs:
            self.slurm_queue.kill_job(job)
        self.update_jobs()

    def hold_all_jobs(self):
        """Hold all jobs"""
        for job in self.slurm_queue.jobs:
            self.slurm_queue.hold_job(job)
        self.update_jobs()

    def release_all_jobs(self):
        """Release all jobs"""
        for job in self.slurm_queue.jobs:
            self.slurm_queue.release_job(job)
        self.update_jobs()

    def set_filter_attribute(self):
        """Set the filter attribute"""
        filter_name = self.filter_attribute_input.get()
        self.job_filter_attribute = NAMES_TO_JOB_ATTRIBUTES[filter_name]
        self.update_jobs()

    def set_filter_regex(self):
        """Set the filter regex"""
        # Set the filter attribute so that we don't explictly have to
        # hit enter in the filter attribute input.
        self.set_filter_attribute()
        self.job_filter_regex = self.filter_regex_input.get()
        self.update_jobs()


def main():
    # Create the CUI with 7 rows 6 columns, pass it to the wrapper object, and start it
    root = py_cui.PyCUI(app_layout.NUM_ROWS, app_layout.NUM_COLS)
    # If we want to use unicode box characters, we toggle them on here.
    # Alternatively, you can define your own border characters using
    # root.set_border_characters(...)
    root.toggle_unicode_borders()
    root.set_title("SQUeue Interactive Display")
    root.set_status_bar_text(
        "   q: Quit || Arrow Keys: Navigate widgets || Enter: Focus on widget || Mouse click: Press button"
    )
    s = SquidApp(root)
    s.update_jobs()
    root.start()
