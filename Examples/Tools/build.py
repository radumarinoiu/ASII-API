import time
import argparse
import subprocess

if __name__ == '__main__':
    current_timestamp = int(time.time())
    parser = argparse.ArgumentParser()
    parser.add_argument("working_path")  # Directory that contains the project AND the Dockerfile
    parser.add_argument("image_path")  # dockerhub_username/repository_name format
    parser.add_argument("image_tag",  # leave empty for automatic versioning using current timestamp
                        nargs="?",
                        default=current_timestamp)
    args = parser.parse_args()

    subprocess.check_call([
        "docker", "build",
        "-t", "{}:{}".format(args.image_path, args.image_tag),
        args.working_path
    ])

    subprocess.check_call([
        "docker", "push",
        "{}:{}".format(args.image_path, args.image_tag)
    ])

    if args.image_tag == current_timestamp:
        subprocess.check_call([
            "docker", "push",
            "{}:latest".format(args.image_path)
        ])
        print("Released version tag: " + str(current_timestamp))
