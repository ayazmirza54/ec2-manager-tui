# AWS EC2 Instance Manager

This is a TUI (Text-based User Interface) application for managing AWS EC2 instances using `boto3` and `textual`. The application allows users to start, stop, and refresh EC2 instances efficiently.

## Features
- View a list of EC2 instances with masked instance IDs and IPs for privacy
- Start and stop instances using interactive buttons
- Checkbox-based instance control enablement
- Logs all operations for better tracking
- Uses `.env` files for AWS credentials instead of CLI configuration

## Installation

### Prerequisites
- Python 3.8+
- AWS account with EC2 access
- `.env` file with required AWS credentials

### Setup
1. Clone this repository:
   ```sh
   git clone https://github.com/your-repo/ec2-manager.git
   cd ec2-manager
   ```

2. Create a `.env` file in the root directory and add your AWS credentials:
   ```env
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_REGION=your-region
   ```

3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Run the application:
   ```sh
   python ec2_manager.py
   ```

## Usage
- The interface will display a list of EC2 instances.
- Select an instance to enable control.
- Use the Start/Stop buttons to manage the selected instance.
- Click Refresh to update the instance list.

## Future Improvements
- Add support for multiple AWS profiles.
- Improve UI for better usability.
- Implement SSH access from the interface.

## License
This project is licensed under the MIT License.

