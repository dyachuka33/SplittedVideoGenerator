import random
import subprocess
import os
import shutil
import json
import random
import time
from PIL import Image


top_preset = []
bottom_preset = []

def select_random_file(directory):
    # Check if the directory exists
    if not os.path.exists(directory):
        print("Directory doesn't exist.")
        return None

    # Get a list of all files in the directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    # Check if there are any files in the directory
    if not files:
        print("No files found in the directory.")
        return None

    # Select a random file from the list
    random_file = random.choice(files)

    # Return the full path to the randomly selected file
    return os.path.join(directory, random_file)

def get_media_info(file_path, is_image):
    ffprobe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,duration:stream_tags=rotate',
        '-of', 'json',
        file_path
    ]

    result = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    width = data['streams'][0]['width']
    height = data['streams'][0]['height']
    duration = 0
    if is_image:
        duration = 0
    else :
        duration = data['streams'][0]['duration']

    rotation = 0
    if 'tags' in data['streams'][0] and 'rotate' in data['streams'][0]['tags']:
        rotation = data['streams'][0]['tags']['rotate']

    return width, height, duration, rotation

def zoom(value):
    crop_width = int(width * value / 100)
    crop_height = int(height * value / 100)

    return f"{width-crop_width}:{height-crop_height}"

options = {
    "blur": {"filter": "boxblur"},
    "rotate": {"filter": "rotate", "format": lambda value: value * (3.141592 / 180)},
    "mirror": {"filter": "hflip", "direct": True},
    "sharpen": {"filter": "unsharp", "format": lambda value: ("3:3:1.5", "5:5:2", "3:3:5", "13:13:2.5", "13:13:5")[value-1]},
    "pad": {"filter": "pad", "format": lambda value: f"width=iw+{value*2}:height=ih+{value*2}:x={value}:y={value}:color=black"},
    "speed": {"filter": "setpts", "format": lambda value: f"{1/value}*PTS"},
    "zoom": {"filter": "crop", "format": zoom},
    "brigthness": {"filter": "eq", "format": lambda value: f"brightness={value}"},
    "contrast": {"filter": "eq", "format": lambda value: f"contrast={value}"},
    "saturation": {"filter": "eq", "format": lambda value: f"saturation={value}"},
    "gamma": {"filter": "eq", "format": lambda value: f"gamma={value}"}
    }   


def generate_adjust_ffmpeg_command(input_path, preset, output_path):
    global width, height, duration_t
    width, height, duration_t, rotation = get_media_info(input_path, False)
    command = f'ffmpeg -hide_banner -noautorotate -i "{input_path}" -filter_complex "'
    filters = ""    
    for i, value in enumerate(preset):
        if value == 0:
            if all(item == 0 for item in preset):
                filters = "null"
                break
            continue
            
        option_dict = options.get(list(options.keys())[i])
        filter = option_dict.get("filter")

        if list(options.keys())[i] == "mirror": 
            if rotation == "90" or rotation == "270":
                filters += "vflip,"
            else:
                filters += "hflip,"
            continue
        if "format" in option_dict:
            filters += f"{filter}={option_dict.get('format')(value)},"
        elif "direct" in option_dict:
            filters += f"{filter},"
        else:
            filters += f"{filter}={value},"

    if filters != "":
        filters = filters[:-1:] if filters[-1] == "," else filters

    command += filters

    command = command[:-1:] if command[-1] == ";" else command

    mappings = f" -c:v h264_nvenc -s {width}x{height} -b:v 3500k " + output_path

    command = f'{command}"{mappings}'

    return command

def run_adjust_ffmpeg_command(command):
    os.system(command)

def get_presets(json_file):
    mode = 2
    if input("1- Auto create presets\n2- Get presets from json\n>>>") == "1":
        mode = 1
        top_preset = []
        for key, value in json_file["options"].items():
            orange = [int(x) for x in value.split(", ")[1].split("-")]
            top_preset.append(random.randint(orange[0], orange[1]))

        json_file["top_preset"] = top_preset
        bottom_preset = []
        for key, value in json_file["options"].items():
            orange = [int(x) for x in value.split(", ")[1].split("-")]
            bottom_preset.append(random.randint(orange[0], orange[1]))

        json_file["bottom_preset"] = bottom_preset
    return json_file, mode


def clean_output_folder():
    print("Clearing output folder...")
    shutil.rmtree("output")
    os.mkdir("output/")

def adjust_video(video_path, preset, output_path):
    command = generate_adjust_ffmpeg_command(video_path, preset, output_path=output_path)
    run_adjust_ffmpeg_command(command)
    pass


def generate_final_video(top_video, bottom_video, presets):
    temp_top_video = "output/top_video.mp4"
    temp_bottom_video = "output/bottom_video.mp4"
    adjust_video(top_video, presets['top_preset'], temp_top_video)
    adjust_video(bottom_video, presets['bottom_preset'], temp_bottom_video)
    _, _, top_duration, _ = get_media_info(temp_top_video, False)
    # _, _, bottom_duration, _ = get_media_info(temp_bottom_video, False)
    duration = top_duration
    # if float(top_duration) > 
    split_command = f'ffmpeg -y -i {temp_top_video} -i {temp_bottom_video} -filter_complex "[0:v]scale=1920:540[top];[1:v]scale=1920:540[bottom];[top][bottom]vstack" -c:v libx264 -preset ultrafast -t {duration} -r 30 -c:a aac output/output.mp4'
    time.sleep(0.5)
    os.system(split_command)
    os.remove(temp_bottom_video)
    os.remove(temp_top_video)
    pass

def main():
    global config
    
    os.system('cls' if os.name == 'nt' else 'clear')

    config = json.load(open('settings.json', 'r'))
    presets, _ = get_presets(config)
    if presets["clear_output_folder"] == "True":
        clean_output_folder()

    #files = [x.replace(" ", "").replace("(", "-").replace(")", "-") for x in files_dir]
    
    os.system('cls' if os.name == 'nt' else 'clear')


    
    top_video = presets["top_video"]
    bottom_video = select_random_file(presets["gameplay_clips"])


    generate_final_video(top_video, bottom_video, presets)

    

    print("All Files Done!")


if __name__ == "__main__":
    main()