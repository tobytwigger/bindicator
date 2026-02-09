#!/home/toby/bindicator/.venv/bin/python
import datetime
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
root_dir = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=root_dir / ".env")

sys.path.append(str(root_dir))

from core.scheduler.scheduler import BinCollectionExplorer


def show_today():
    bin_collection_explorer = BinCollectionExplorer()

    # Use the smart action-based logic
    result = bin_collection_explorer.get_bins_requiring_action()

    print(result)

    bins_to_display = result['bins_to_display']
    display_date = result['display_date']
    next_collection_date = result['next_collection_date']

    if bins_to_display:
        print(f"Displaying {len(bins_to_display)} bins for {display_date}")
    else:
        print(f"No actionable bins, next collection: {next_collection_date}")

def show_next_collection():
    bin_collection_explorer = BinCollectionExplorer()
    next_date = bin_collection_explorer.get_collection_date_after(datetime.date.today())
    print(f"Next collection date: {next_date}")


    bins_on_date = self._bin_collection_explorer.get_bins_due_out_on(self._current_date)
    logger.debug(f"Found {len(bins_on_date)} bins due on {self._current_date}: {[b.name for b in bins_on_date]}")

    if bins_on_date:
        # Build bin data with status for this specific date
        bins_data = []
        for bin_obj in bins_on_date:
            status, put_out_datetime, put_out_id = self._bin_collection_explorer.get_bin_status_for_date(
                bin_obj.id,
                self._current_date
            )
            logger.debug(f"Bin '{bin_obj.name}' (id={bin_obj.id}): status={status}, put_out_id={put_out_id}")
            bins_data.append({
                'bin': bin_obj,
                'status': status,
                'put_out_datetime': put_out_datetime,
                'put_out_id': put_out_id
            })

        next_collection_date = self._bin_collection_explorer.get_collection_date_after(self._current_date)
        logger.debug(f"Next collection date after {self._current_date}: {next_collection_date}")
        self._display_bins_due(drivers, bins_data, self._current_date, next_collection_date)
    else:
        # No bins on this date
        logger.info(f"No bins due on {self._current_date}")
        next_collection_date = self._bin_collection_explorer.get_collection_date_after(self._current_date)
        logger.debug(f"Next collection date: {next_collection_date}")
        self._display_no_bins_due(drivers, next_collection_date)



def run():
    # Here we can test the outputs we're hoping for!

    # We start on 'today'
    show_today()

    # We then press the 'right' button
    show_next_collection()

if __name__ == "__main__":
    run()