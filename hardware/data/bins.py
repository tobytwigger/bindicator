import datetime
from uk_bin_collection.uk_bin_collection.collect_data import UKBinCollectionApp
from dataclasses import dataclass
import json
from database.db import Home, Bin, BinDay, Schedule, BinSchedule

from data.selenium import SeleniumDriverManager



@dataclass
class BinInformation:
    """Class for a specific bin"""
    position: int
    name: str
    id: int


@dataclass
class BinDayInformation:
    """Class with all the bins to go out on a given day"""
    bins: list[BinInformation]
    date: datetime.date

    def push(self, bin: BinInformation):
        self.bins.append(bin)


@dataclass
class BinDayInformationCollection:
    bin_days: list[BinDayInformation]

    def __init__(self, bin_days: list[BinDayInformation]):
        self.bin_days = bin_days
    def _get_bin_days_for_position(self, bin_position: int or None = None) -> list[BinDayInformation]:
        if len(self.bin_days) == 0:
            return []

        return [b for b in self.bin_days if bin_position is None or any([b2.position == bin_position for b2 in b.bins])]

    def first_date(self, bin_position: int or None = None) -> datetime.date or None:
        bin_days = self._get_bin_days_for_position(bin_position)

        if len(bin_days) == 0:
            return None
        return min([b.date for b in bin_days])

    def last_date(self) -> datetime.date or None:
        if len(self.bin_days) == 0:
            return None
        return max([b.date for b in self.bin_days])

    def next_date_after(self, after_date, bin_position: int or None = None):
        if after_date is None:
            return None

        for b in self.bin_days:
            if b.date > after_date and (bin_position is None or any([b2.position == bin_position for b2 in b.bins])):
                return b.date

        return None

    def date_before(self, before_date, bin_position: int or None = None):
        if before_date is None:
            return None

        for b in reversed(self.bin_days):
            if b.date < before_date and (bin_position is None or any([b2.position == bin_position for b2 in b.bins])):
                return b.date

        return None

    def get_dates_for_bin(self, bin_position: int or None = None) -> list[datetime.date]:
        dates = []
        for b in self.bin_days:
            for bin in b.bins:
                if bin.position == bin_position:
                    dates.append(b.date)

        return dates

    def get_for_date(self, date, bin_position: int or None = None) -> BinDayInformation or None:
        for b in self.bin_days:
            if b.date == date and (bin_position is None or any([b2.position == bin_position for b2 in b.bins])):
                return b

        return None


class BinDayRepository:

    def __init__(self, home: Home, bin_config: list[Bin]):
        self._home = home
        self._bin_config = bin_config

    def _create_bin_information(self, bin_id: int) -> BinInformation:
        bins = self._bin_config

        for b in bins:
            if b.id == bin_id:
                return BinInformation(b.position, b.name, b.id)

    def get_bin_data(self) -> BinDayInformationCollection:
        # Get all the future bin days from the database

        # 1 minute past midnight tomorrow
        get_bins_after_date = datetime.datetime.now().replace(hour=23, minute=59, second=59) - datetime.timedelta(days=1)

        # Convert to milliseconds. This is because the database is controlled by js, which uses milliseconds in timestamps
        timestamp_in_milliseconds = get_bins_after_date.timestamp() * 1000

        bins = (BinDay.select(BinDay.date, BinDay.bin_id, BinDay.home_id, Bin.id, Bin.name)
                .join(Bin, on=(Bin.id == BinDay.bin_id))
                .where(BinDay.home_id == self._home.id)
                .where(BinDay.date >= timestamp_in_milliseconds)
                .order_by(BinDay.date)
                )

        bins_grouped_by_date = {}

        for b in bins:
            bin_timestamp = int(float(b.date)) / 1000
            bin_date_formatted = datetime.datetime.fromtimestamp(bin_timestamp).strftime("%d/%m/%Y")

            new_bin = self._create_bin_information(b.bin_id.id)
            if new_bin:
                day = bins_grouped_by_date.setdefault(bin_date_formatted, BinDayInformation(
                    bins=[],
                    date=datetime.datetime.strptime(bin_date_formatted, "%d/%m/%Y").date()
                ))
                day.push(new_bin)

        collection = BinDayInformationCollection(list(bins_grouped_by_date.values()))

        return collection

    def get_bin_options(self):
        remote_repository = RemoteBinDayRepository(self._home, self._bin_config)

        return remote_repository.get_bin_options()


class RemoteBinDayRepository:

    def __init__(self, home: Home, bin_config: list[Bin]):
        self._home = home
        self._bin_config = bin_config
        self._setup_bin_app()

    def _setup_bin_app(self):
        args = [
            self._home.council,  # Council name
            "http://example.com",  # URL to scrape
            "-s",
        ]

        if 'postcode' in self._home.council_data:
            args.append("-p")
            args.append(self._home.council_data['postcode'])

        if 'house_number' in self._home.council_data:
            args.append("-n")
            args.append(self._home.council_data['house_number'])

        if 'uprn' in self._home.council_data:
            args.append("-u")
            args.append(self._home.council_data['uprn'])

        self._bin_collection_api = UKBinCollectionApp()
        self._bin_collection_api.set_args(args)

        selenium_manager = SeleniumDriverManager()
        selenium_manager.setup_cache()

    def get_bin_data(self) -> BinDayInformationCollection:
        remote_bin_data = self._bin_collection_api.run()

        json_bin_data = json.loads(remote_bin_data)
        bins_grouped_by_date = {}

        for b in json_bin_data["bins"]:
            new_bin = self._create_bin_information(b["type"])
            if new_bin:
                day = bins_grouped_by_date.setdefault(b["collectionDate"], BinDayInformation(
                    bins=[],
                    date=datetime.datetime.strptime(b["collectionDate"], "%d/%m/%Y").date()
                ))
                day.push(new_bin)

        collection = BinDayInformationCollection(list(bins_grouped_by_date.values()))

        return collection

    def _create_bin_information(self, bin_name: str) -> BinInformation:
        bins = self._bin_config

        for b in bins:
            if b.council_name == bin_name:
                return BinInformation(b.position, b.council_name, b.name)

    def get_bin_options(self):
        remote_bin_data = self._bin_collection_api.run()

        json_bin_data = json.loads(remote_bin_data)

        bins = set()

        for b in json_bin_data["bins"]:
            bins.add(b["type"])

        return list(bins)
