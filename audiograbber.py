import os
import inquirer
import json
import boto3
from urllib.request import urlopen
from urllib.parse import urlparse
from moviepy.editor import VideoFileClip
from pytube import YouTube
from sclib import SoundcloudAPI
import concurrent.futures
from urllib.parse import urlparse



class CurrentlyNotSupported(Exception):
    """Raised when URL is not supported by the service"""


services = ["youtube", "soundcloud"]
prefix = "."
path = "/Users/king-omar/Desktop/AudioGrabber/Music"


directories = [
    item
    for item in os.listdir(path)
    if (os.path.isdir(path)) and (not item.startswith(prefix))
]


class Youtube_File:
    def __init__(self, url, path, s3_bucket_name) -> None:
        self.url = url
        self.path = path
        self.s3_bucket_name = s3_bucket_name

    def download_mp3(self):
        try:
            yt = YouTube(self.url)
            yt.streams.get_highest_resolution()
            video_stream = yt.streams.filter().first()
            vid_download = video_stream.download(self.path)
            name = yt.title

            modified_name = name.replace(" ", "_")

            self.convert_to_mp3(vid_download, name=modified_name)

            # Upload to S3
            s3 = boto3.client(
                "s3",
                aws_access_key_id="AKIAQ4SE3SQ437UQXDMU",
                aws_secret_access_key="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",
            )
            s3_key = os.path.join("uploads", modified_name + ".mp3")

            filename = os.path.join(self.path, modified_name + ".mp3")
            s3.upload_file(filename, self.s3_bucket_name, s3_key)
        except Exception as e:
            print("Couldn't download or upload this file:", str(e))

        return

    def convert_to_mp3(self, downloaded_video, name):
        

        clip = VideoFileClip(downloaded_video)

        audio = clip.audio
        filename = os.path.join(self.path, name + ".mp3")

        audio.write_audiofile(filename)

        clip.close()
        audio.close()

        os.remove(downloaded_video)

        return


class Soundcloud_File:
    def __init__(self, url, file_path, s3_bucket_name):
        self.url: str = url
        self.file_path: str = file_path
        self.s3_bucket_name = s3_bucket_name

    def download_mp3(self):
        api = SoundcloudAPI()
        track = api.resolve(self.url)

        return


def process_file(to_save_dir):
    threads = []
    MAX_THREADS = 10
    song_file = json.loads(open("youtube.json").read())

    for key, value in song_file.items():
        parsed_url = urlparse(url=key)
        domain = parsed_url.netloc.split(".")
        if (domain[1] == "youtube") and (value != "DONE"):
            obj = Youtube_File(url=key, path=to_save_dir)
        elif (domain[0] == "soundcloud") and (value != "DONE"):
            obj = Soundcloud_File(url=key, file_path=to_save_dir)
        else:
            raise CurrentlyNotSupported

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = executor.submit(obj.download_mp3)
            print(futures.result())

    for thread in threads:
        thread.join()

    return


def download_music(url, save_dir, s3_bucket_name):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.split(".")
        if domain[1] == "youtube":
            youtube_obj = Youtube_File(url, save_dir, s3_bucket_name)
            youtube_obj.download_mp3()
        elif domain[0] == "soundcloud":
            soundcloud_obj = Soundcloud_File(url=url, file_path=save_dir)
            soundcloud_obj.download_mp3()
        else:
            raise CurrentlyNotSupported

    except Exception as e:
        print(f"Error: {e}")


def main():
    to_save_dir = prompt_question()
    process_file(to_save_dir)

    return


def prompt_question():
    question = [
        inquirer.List("directory", message="which directory?", choices=directories)
    ]
    answer = inquirer.prompt(question)
    if not answer:
        raise
    save_dir = f"{path}{answer['directory']}/"

    return save_dir


if __name__ == "__main__":
    main()
