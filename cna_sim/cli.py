import argparse
from .builder import default_context_builder

def run():
    parser = argparse.ArgumentParser(description='Say hi.')
    parser.add_argument('-f', '--file', type=str, nargs='+', help='File path of configurations')
    parser.add_argument('-fo', '--folder', type=str, nargs='+', help='Folder of configurations')
    parser.add_argument('-d', '--duration', type=float, help='Duration of the simulation (in seconds)')
    args = parser.parse_args()

    builder = default_context_builder()
    if args.file is not None:
        for file_path in args.file:
            builder.add_file(file_path)

    if args.folder is not None:
        if args.folder is not None:
            for folder_path in args.folder:
                builder.add_folder(folder_path)

    duration = 0
    if args.duration is not None:
        duration = args.duration

    with builder.build() as context:
        print('Simulation started.')
        context.simulate(duration)
        print('Simulation ended.')

