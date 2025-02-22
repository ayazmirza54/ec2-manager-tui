from textual.app import App, ComposeResult
from textual.widgets import DataTable, Button, Footer, Static, Checkbox
from textual.containers import Vertical, Horizontal
import boto3
import time
import botocore.exceptions
import logging
from datetime import datetime


def setup_logging():
    """Setup logging configuration"""
    log_filename = f"ec2_manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        filename=log_filename,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.info("Starting EC2 Manager Application")


class EC2Manager(App):
    """A TUI application to manage AWS EC2 instances using boto3."""

    TITLE = "AWS EC2 Instance Manager"

    def __init__(self):
        super().__init__()
        setup_logging()  # Initialize logging when app starts
        self.selected_instance = None
        self.selected_row_key = None  # Add this to track selected row

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        self.instances_table = DataTable()
        self.instances_table.cursor_type = (
            "row"  # Add this line to enable row selection
        )
        yield Static("EC2 Instance Manager", id="title")
        yield self.instances_table
        yield Horizontal(
            Checkbox("Enable Instance Control", id="enable_control"), id="controls"
        )
        yield Vertical(
            Button("Start Instance", id="start", disabled=True),
            Button("Stop Instance", id="stop", disabled=True),
            Button("Refresh", id="refresh"),
            id="buttons",
        )
        yield Footer()

    def on_mount(self):
        """Called when the app starts."""
        try:
            self.ec2 = boto3.client("ec2")  # Initialize EC2 client
            logging.info("✅ Connected to AWS EC2 successfully!")
        except botocore.exceptions.NoCredentialsError:
            logging.error(
                "❌ No AWS credentials found! Run `aws configure` to set them up."
            )
            return
        except Exception as e:
            logging.error(f"❌ AWS Connection Error: {e}")
            return

        self.refresh_instances()

    def refresh_instances(self):
        """Fetch and display EC2 instances."""
        current_selection = self.selected_instance  # Store current selection
        self.instances_table.clear()
        self.instances_table.add_columns(
            "ID", "Type", "State", "Public IP", "Private IP"
        )

        try:
            response = self.ec2.describe_instances()
            row_index = 0  # Add counter for row index
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    logging.debug(
                        f"Debug - AWS Instance State: {instance['State']['Name']}"
                    )
                    row = (
    instance["InstanceId"],
    instance["InstanceType"],
    instance["State"]["Name"],
    "XXX.XXX.XXX.XXX" if "PublicIpAddress" in instance else "N/A",
    "XXX.XXX.XXX.XXX" if "PrivateIpAddress" in instance else "N/A",
)

                    self.instances_table.add_row(*row)

                    # If this is the previously selected instance, restore selection
                    if instance["InstanceId"] == current_selection:
                        logging.debug(
                            f"🔍 Debug - Restoring selection to row {row_index}"
                        )
                        self.instances_table.cursor_row = row_index
                        self.selected_instance = current_selection
                        # Re-enable buttons based on checkbox state
                        checkbox = self.query_one("#enable_control")
                        if checkbox.value:
                            self.update_button_states(instance["State"]["Name"])

                    row_index += 1

            logging.info("✅ Instance list refreshed.")
        except Exception as e:
            logging.error(f"❌ Error fetching instances: {e}")

        if not self.selected_instance:
            self.disable_buttons()

    def disable_buttons(self):
        """Disable Start/Stop buttons when no instance is selected."""
        self.query_one("#start").disabled = True
        self.query_one("#stop").disabled = True
        self.query_one("#enable_control").value = False

    def update_button_states(self, instance_state):
        """Update button states based on instance state."""
        start_btn = self.query_one("#start")
        stop_btn = self.query_one("#stop")
        checkbox = self.query_one("#enable_control")

        if checkbox.value and self.selected_instance:
            # Enable/disable based on instance state
            start_btn.disabled = instance_state.lower() == "running"
            stop_btn.disabled = instance_state.lower() == "stopped"
        else:
            start_btn.disabled = True
            stop_btn.disabled = True

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes."""
        logging.debug(f"🔍 Debug - Checkbox changed: {event.value}")
        if self.selected_instance:
            try:
                # Get current instance state
                response = self.ec2.describe_instances(
                    InstanceIds=[self.selected_instance]
                )
                current_state = response["Reservations"][0]["Instances"][0]["State"][
                    "Name"
                ]
                self.update_button_states(current_state)
                logging.info(
                    f"✅ Instance control {'enabled' if event.value else 'disabled'}"
                )
            except Exception as e:
                logging.error(f"Error getting instance state: {e}")
                self.disable_buttons()
        else:
            logging.warning("⚠️ No instance selected when checkbox changed")
            self.disable_buttons()

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        """Handle instance selection."""
        row_key = event.row_key
        logging.debug(f"🔍 Row selected: {row_key}")
        try:
            row_data = self.instances_table.get_row(row_key)
            logging.debug(f"🔍 Debug - Row data: {row_data}")  # Add this debug line

            if row_data:
                self.selected_instance = row_data[0]  # Instance ID
                self.selected_row_key = row_key  # Store selected row key
                current_state = row_data[2]  # Get instance state

                # Set cursor to selected row
                self.instances_table.cursor_row = row_key

                checkbox = self.query_one("#enable_control")
                logging.debug(f"🔍 Debug - Checkbox state: {checkbox.value}")
                logging.debug(f"🔍 Debug - Selected instance: {self.selected_instance}")
                logging.debug(f"🔍 Debug - Instance state: {current_state}")

                self.update_button_states(current_state)

                logging.info(f"✅ Selected Instance: {self.selected_instance}")
        except Exception as e:
            logging.error(f"❌ Error selecting row: {e}")
            import traceback

            logging.error(
                f"🔍 Debug - Selection error traceback: {traceback.format_exc()}"
            )

    def manage_instance(self, action):
        """Start or Stop the selected instance."""
        if not self.selected_instance:
            logging.warning("⚠️ No instance selected!")
            return

        try:
            logging.debug(f"🔍 Debug - Current instance: {self.selected_instance}")
            logging.debug(f"🔍 Debug - Attempting action: {action}")

            # Get current instance state
            response = self.ec2.describe_instances(InstanceIds=[self.selected_instance])
            current_state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
            logging.debug(f"🔍 Debug - Current instance state: {current_state}")

            if action == "start":
                if current_state == "running":
                    logging.warning("⚠️ Instance is already running!")
                    return
                logging.info(f"🚀 Starting instance: {self.selected_instance}")
                response = self.ec2.start_instances(
                    InstanceIds=[self.selected_instance]
                )
                logging.debug(f"🔍 Debug - Start response: {response}")
            elif action == "stop":
                if current_state == "stopped":
                    logging.warning("⚠️ Instance is already stopped!")
                    return
                logging.info(f"🛑 Stopping instance: {self.selected_instance}")
                response = self.ec2.stop_instances(InstanceIds=[self.selected_instance])
                logging.debug(f"🔍 Debug - Stop response: {response}")

            # Wait for the instance state to change before refreshing
            logging.info("⏳ Waiting for instance state update...")
            target_state = "running" if action == "start" else "stopped"
            max_attempts = 40
            attempt = 0

            while attempt < max_attempts:
                try:
                    response = self.ec2.describe_instances(
                        InstanceIds=[self.selected_instance]
                    )
                    current_state = response["Reservations"][0]["Instances"][0][
                        "State"
                    ]["Name"]
                    logging.debug(f"Waiting... Current state: {current_state}")

                    if current_state == target_state:
                        logging.info(f"✅ Instance is now {target_state}")
                        break
                    elif current_state in ["pending", "stopping"]:
                        attempt += 1
                        time.sleep(5)
                    else:
                        logging.warning(f"⚠️ Unexpected state: {current_state}")
                        break
                except Exception as e:
                    logging.error(f"Error checking instance state: {e}")
                    break

            if attempt >= max_attempts:
                logging.warning("⚠️ Timeout waiting for instance state change")

            self.refresh_instances()
        except Exception as e:
            logging.error(f"❌ Error managing instance: {e}")
            import traceback

            logging.error(f"🔍 Debug - Full error: {traceback.format_exc()}")

    def on_button_pressed(self, event):
        """Handle button presses."""
        logging.debug(f"🔍 Debug - Button pressed: {event.button.id}")
        if event.button.id == "refresh":
            logging.info("🔄 Refreshing instance list...")
            self.refresh_instances()
        elif event.button.id == "start":
            logging.info("🚀 Start button pressed")
            if not self.selected_instance:
                logging.warning("⚠️ No instance selected for start operation")
                return
            self.manage_instance("start")
        elif event.button.id == "stop":
            logging.info("🛑 Stop button pressed")
            if not self.selected_instance:
                logging.warning("⚠️ No instance selected for stop operation")
                return
            self.manage_instance("stop")


if __name__ == "__main__":
    EC2Manager().run()
