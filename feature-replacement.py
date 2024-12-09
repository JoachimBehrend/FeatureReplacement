import cv2
from pathlib import Path
import numpy as np
import sys
import os
import glob
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
import time
from datetime import timedelta
import insightface
from insightface.app import FaceAnalysis
from insightface.data import get_image as ins_get_image
import moviepy.config as mpy_config
mpy_config.change_settings({"FFMPEG_BINARY": "/usr/local/bin/ffmpeg"})
import moviepy.editor as moviepy
import wx
import faulthandler
from tkinter import filedialog as fd
conv = Converter()

faulthandler.enable()

## Fix moviepy library for --windowed app 
output = open("output.txt", "wt")
sys.stdout = output
sys.stderr = output
## --------------------------------------

filename = fd.askopenfilename()
if getattr(sys, 'frozen', False):
    onlyfiles = [f for f in os.listdir(os.path.join(sys._MEIPASS, "Files/SourceImages")) if os.path.isfile(os.path.join(sys._MEIPASS, "Files/SourceImages", f))]
else:
    onlyfiles = [f for f in os.listdir(".") if os.path.isfile(os.path.join(".", f))]

############## INPUTS ################################
app = wx.App(False)
original_video = wx.FileSelector("CHOOSE A VIDEO",default_path=os.getcwd())
app.Destroy()
if getattr(sys, 'frozen', False):
    app = wx.App(False)
    source_image_file = wx.FileSelector("CHOOSE A SOURCE IMAGE FROM THIS FOLDER",default_path=os.path.join(sys._MEIPASS, "Files/SourceImages"))
    app.Destroy()
else:
    app = wx.App(False)
    source_image_file = wx.FileSelector("CHOOSE A SOURCE IMAGE FROM THIS FOLDER",default_path="./Files/SourceImages")
    app.Destroy()

print(source_image_file)
s = source_image_file.split('/')
s_name = s[-1]
s_folder = source_image_file[:-len(s_name)]
source_image_approved = True
if getattr(sys, 'frozen', False) and not (os.path.samefile(s_folder,os.path.join(sys._MEIPASS, "Files/SourceImages"))):
    print("You can only choose a file from the SourceImages folder")
    sys.exit()


############## GLOBALS ##############################
l = original_video.split('/')
original_video_name = l[-1]
original_video_folder = original_video[:-len(original_video_name)]
output_folder = os.path.join(original_video_folder,original_video_name[:-4]+"_VideoFiles/")
Path(output_folder).mkdir(parents=True, exist_ok=True)
current_folder = os.getcwd()

if getattr(sys, 'frozen', False): ### If code is run as executable 
    source_image_path = os.path.join(sys._MEIPASS, "Files/SourceImages/", source_image_file)
    swapper = insightface.model_zoo.get_model(os.path.join(sys._MEIPASS, "Files/inswapper_128.onnx"), download=False, download_zip=False)
else: 
    source_image_path =os.path.join("./Files/SourceImages/", source_image_file)
    swapper = insightface.model_zoo.get_model("./Files/inswapper_128.onnx", download=False, download_zip=False)

images_with_error = []
start = time.time()
app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=0, det_size=(640, 640))

def get_png_files(folder_path): 
    filelist=os.listdir(folder_path)
    for fichier in filelist[:]: # filelist[:] makes a copy of filelist.
        if not(fichier.endswith(".jpg")):
            filelist.remove(fichier)
    filelist.sort(key=lambda item: (len(item),item))
    return filelist

def swap_image(path_to_image,source_face,face_analysis_app,swapping_app):
    target_image = cv2.imread(path_to_image)
    target_face_list = face_analysis_app.get(target_image)
    res = target_image.copy()
    include = True
    if len(target_face_list) > 0: 
        target_face = target_face_list[0]
        res = swapping_app.get(res,target_face,source_face,paste_back=True)
    else: 
        images_with_error.append(f)
        include = False 
    return res, include


if __name__ == "__main__":
    if len(sys.argv) > 1: 
        original_video = sys.argv[1]


    #########################################################################################
    ### SPLITTING THE VIDEO #################################################################
    #########################################################################################

    frames_folder = os.path.join(output_folder, "Frames/")
    print(frames_folder)
    Path(frames_folder).mkdir(parents=True, exist_ok=True)
    vidcap = cv2.VideoCapture(original_video)
    success,image = vidcap.read()
    count = 0
    while success:
        cv2.imwrite(frames_folder + "/frame%d.jpg" % count, image)     # save frame as JPEG file      
        success,image = vidcap.read()
        print('Read a new frame: ', success)
        count += 1


    #########################################################################################
    ### REPLACING FRAMES ####################################################################
    #########################################################################################
        
    target_images = get_png_files(frames_folder)
    replaced_frames_folder = os.path.join(output_folder,"FramesReplaced/")
    Path(replaced_frames_folder).mkdir(parents=True, exist_ok=True)
    source_image = cv2.imread(source_image_path)
    source_face_list = app.get(source_image)
    source_face = source_face_list[0]
    for idx,f in enumerate(target_images): 
        print("Progress: " + str(idx+1) + " out of " + str(len(target_images)) + "   |   current image: " + f + "   |   runningtime: " + str(timedelta(seconds=time.time() - start)))
        filename = frames_folder + f
        res, include = swap_image(filename,source_face,app,swapper)
        if include == True: 
            result_image_name = "swapped_" + f
            cv2.imwrite(os.path.join(replaced_frames_folder,result_image_name),res)
    print("The following images was not swapped")
    print(images_with_error)


    #########################################################################################
    ### RECOMBINING FRAMES TO VIDEO #########################################################
    #########################################################################################
    
    video_final = original_video_name[:-4] + "Replaced"
    images = [img for img in os.listdir(replaced_frames_folder) if img.endswith(".jpg")]
    images.sort(key= lambda item: (len(item),item))
    frame = cv2.imread(os.path.join(replaced_frames_folder, images[0]))
    height, width, layers = frame.shape
    video = cv2.VideoWriter(os.path.join(output_folder,video_final) + ".avi", 0, 30, (width,height))
    for image in images:
        video.write(cv2.imread(os.path.join(replaced_frames_folder, image)))
    cv2.destroyAllWindows()
    video.release()
    final_clip = moviepy.VideoFileClip(os.path.join(output_folder, video_final) + ".avi")
    video = moviepy.VideoFileClip(original_video)
    if video.audio != None:
        audio = video.audio
        final_clip = final_clip.set_audio(audio)

    final_clip.write_videofile(os.path.join(original_video_folder,video_final + ".mp4"))
    print("Video features sucessfully replaced")

    sys.exit()