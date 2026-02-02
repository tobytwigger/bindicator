import argparse
import json
from database.db import Home
from data.bins import BinDayRepository


def run():
    parser = argparse.ArgumentParser(prog="api.py")
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True  # required since 3.7

    #  subparser for testing a home connection to the council website
    parser_test_home = subparsers.add_parser('test-home', help='Test the connection for a home to the council website.')
    # add a required argument
    parser_test_home.add_argument(
        'home_id',
        help='The ID of the home.',
        type=int
    )

    #  subparser for getting available bins
    parser_get_bin_options = subparsers.add_parser('get-bin-options')
    # add a required argument
    parser_get_bin_options.add_argument(
        'home_id',
        help='The ID of the home.',
        type=int
    )

    args = parser.parse_args()

    if args.subcommand == 'test-home':
        test_home(args.home_id)
    elif args.subcommand == 'get-bin-options':
        get_bin_options(args.home_id)
    else:
        raise Exception("Invalid subcommand")



def get_bin_options(home_id):
    # Get the home record
    home = Home.get_by_id(home_id)

    bins = BinDayRepository(home, home.bins)
    bin_options = bins.get_bin_options()

    output({
        'options': bin_options
    })

def test_home(home_id):
    # Get the home record
    home = Home.get_by_id(home_id)

    try:
        bins = BinDayRepository(home, home.bins)
        bins.get_bin_data()
    except Exception as e:
        output({'valid': False, 'error': str(e)})
        return

    output({'valid': True})

def output(j: dict):
    print(json.dumps(j))

if __name__ == "__main__":
    run()

