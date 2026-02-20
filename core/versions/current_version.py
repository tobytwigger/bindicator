from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]

def get_current_version() -> str:
    """
    Get the current software version from the VERSION file.
    :return: The current software version as a string.
    """
    try:
        # Open the VERSION file from the root of the project and read its contents
        with open(f"{root_dir}/VERSION", "r") as version_file:
            version = version_file.read().strip()
            return version
    except Exception as e:
        print(f"Error reading VERSION file: {e}")
        return "Unknown"