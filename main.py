import sys
import os
import cv2
import time 
from tkinter import filedialog as fd
from tkinter import *
from tkinter import ttk
#import customtkinter
import insightface
from insightface.app import FaceAnalysis
from insightface.data import get_image as ins_get_image
import multiprocessing
from pathlib import Path
import subprocess

def copy_audio_ffmpeg(source_with_audio, target_without_audio, output_video):
    # Build the ffmpeg command to copy audio from one video to another
    path = resource_path("./Files/ffmpeg")

    command = [
        path,
        '-i', source_with_audio,        # Input file with audio
        '-i', target_without_audio,     # Input file with the video to retain
        '-c:v', 'copy',                 # Copy the video without re-encoding
        '-map', '0:a',                  # Select the audio from the first input
        '-map', '1:v',                  # Select the video from the second input
        output_video                    # Output file
    ]

    errorText.config(text="Audio copy process starting")
    subprocess.run(command, check=True)
    errorText.config(text="Audio Sucessfully Copied")

#################################################################################
################## PROGRAM FUNCTIONS ############################################
#################################################################################
    
def Replace():
    source = sourceImagePath.get()
    original = originalVideoPath.get()
    if source == "No Image Chosen":
        errorText.config(text="COULDNT REPLACE VIDEO\n CHOOSE SOURCE IMAGE")
        return
    if original == "No Video Chosen":
        errorText.config(text="COULDNT REPLACE VIDEO\n CHOOSE VIDEO")
    originalName = basename(original)
    originalFolder = original[:-len(originalName)]
    outputFolder = os.path.join(originalFolder,originalName[:-4]+"Replaced/")
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)
    

    #########################################################################################
    ### SPLITTING THE VIDEO #################################################################
    #########################################################################################
    framesFolder = video_split(original,outputFolder)
    errorText.config(text="WORKS UNTIL HEREE")

    #########################################################################################
    ### REPLACING FRAMES ####################################################################
    #########################################################################################
    replacedFramesFolder = replace_frames(outputFolder, framesFolder,source)
    errorText.config(text="HERRREEEE")
    
    #########################################################################################
    ### RECOMBINING FRAMES TO VIDEO #########################################################
    #########################################################################################
    recombineVideo(original,outputFolder,replacedFramesFolder)
    #main.destroy()

def video_split(originalFolder,outputFolder):
    framesFolder = os.path.join(outputFolder, "Frames/")
    if not os.path.exists(framesFolder):
        os.makedirs(framesFolder)
    vidcap = cv2.VideoCapture(originalFolder)
    success,image = vidcap.read()
    count = 0
    while success:
        cv2.imwrite(framesFolder + "/frame%d.jpg" % count, image)     # save frame as JPEG file      
        success,image = vidcap.read()
        count += 1
    return framesFolder


def replace_frames(outputFolder,framesFolder,source):
    target_images = get_png_files(framesFolder)
    replacedFramesFolder = os.path.join(outputFolder,"FramesReplaced/")
    if not os.path.exists(replacedFramesFolder):
        os.makedirs(replacedFramesFolder)
    sourceImage = cv2.imread(source)
    sourceFaceList = app.get(sourceImage)
    sourceFace = sourceFaceList[0]
    for idx,f in enumerate(target_images): 
        print("Progress: " + str(idx+1) + " out of " + str(len(target_images)) + "   |   current image: " + f)
        filename = framesFolder + f
        res, include = swapImage(filename,sourceFace,app,swapper)
        if include == True: 
            resultImageName = "swapped_" + f
            cv2.imwrite(os.path.join(replacedFramesFolder,resultImageName),res)
    return replacedFramesFolder

def swapImage(path_to_image,source_face,face_analysis_app,swapping_app):
    target_image = cv2.imread(path_to_image)
    target_face_list = face_analysis_app.get(target_image)
    res = target_image.copy()
    include = True
    if len(target_face_list) > 0: 
        target_face = target_face_list[0]
        res = swapping_app.get(res,target_face,source_face,paste_back=True)
    else: 
        images_with_error.append(basename(path_to_image))
        include = False 
    return res, include

def recombineVideo(originalVideo,outputFolder, replacedFramesFolder):
    video_final = basename(originalVideo)[:-4] + "Replaced"
    images = [img for img in os.listdir(replacedFramesFolder) if img.endswith(".jpg")]
    images.sort(key= lambda item: (len(item),item))
    frame = cv2.imread(os.path.join(replacedFramesFolder, images[0]))
    height, width, layers = frame.shape
    video = cv2.VideoWriter(os.path.join(outputFolder,video_final) + ".avi", 0, 30, (width,height))
    for image in images:
       video.write(cv2.imread(os.path.join(replacedFramesFolder, image)))
    cv2.destroyAllWindows()
    video.release()

    # Get folder of original video
    originalName = basename(originalVideo)
    originalFolder = originalVideo[:-len(originalName)]

    # Load the .avi video
    input_file = os.path.join(outputFolder,video_final) + ".avi"  # path to the input .avi file
    output_file = os.path.join(originalFolder,video_final) + ".mp4"  # path to the output .mp4 file

    # Open the .avi video file
    cap = cv2.VideoCapture(input_file)

    # Check if the video file was opened correctly
    if not cap.isOpened():
        print("Error: Could not open input file.")
        exit()

    # Get the frames per second (fps), frame width, and frame height of the input video
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use mp4 codec
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    # Loop through the video frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # Exit loop when there are no more frames
        
        # Write each frame to the output .mp4 file
        out.write(frame)
    cap.release()
    out.release()
    copy_audio_ffmpeg(originalVideo,os.path.join(originalFolder,video_final) + ".mp4",os.path.join(originalFolder,video_final) + "WithAudio.mp4")



def get_png_files(folder_path): 
    filelist=os.listdir(folder_path)
    for fichier in filelist[:]: # filelist[:] makes a copy of filelist.
        if not(fichier.endswith(".jpg")):
            filelist.remove(fichier)
    filelist.sort(key=lambda item: (len(item),item))
    return filelist

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def approve_source_folder(path):
    folder = resource_path("./Files/SOURCE IMAGES/")
    chosenFolder = path[:-len(basename(path))]
    return True if os.path.samefile(folder,chosenFolder) else False

def basename(path):
    res = path.split("/")
    return res[-1]

#################################################################################
################## GUI FUNCTIONS ################################################
#################################################################################

def setOriginalVideoPath():
    f = fd.askopenfilename(filetypes=(("video files","*.mp4"),("video files","*.MOV")),initialdir=os.path.join(sys.argv[0],"../../../.."))
    originalVideoPath.set(f)
    originalVideoPathText.config(text=str(basename(originalVideoPath.get())))

def setSourceImagePath():
    f = fd.askopenfilename(filetypes=(("image files","*.png"),("image files","*.jpg")),initialdir=resource_path("./Files/SOURCE IMAGES/"))
    if hasattr(sys, '_MEIPASS') and not approve_source_folder(f):
        sourceImagePathText.config(text="No Image Chosen")
        errorText.config(text="SOURCE IMAGE REJECTED:\nIMAGE MUST BE FROM THE FOLDER 'SOURCE IMAGES'")
        return
    sourceImagePath.set(f)
    sourceImagePathText.config(text=str(basename(sourceImagePath.get())))
    errorText.config(text="")


#################################################################################
################ CONSTANTS ######################################################
#################################################################################

app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=0, det_size=(640, 640))
if hasattr(sys, '_MEIPASS'):
    swapper = insightface.model_zoo.get_model(os.path.join(sys._MEIPASS, "Files/inswapper_128.onnx"), download=False, download_zip=False)
else: 
    swapper = insightface.model_zoo.get_model("./Files/inswapper_128.onnx", download=False, download_zip=False)


#################################################################################
################## GUI ##########################################################
#################################################################################

main = Tk()
images_with_error = []
main.geometry("400x300")
originalVideoPath = StringVar(main,"No Video Chosen")
sourceImagePath = StringVar(main,"No Image Chosen")
originalVideoPathText = Label(main,text=originalVideoPath.get())
originalVideoPathText.pack()
button_one = Button(main,text="Choose Video",height=1,width=20,fg="black",command=setOriginalVideoPath)
button_one.pack()
#finishLabel = customtkinter.CTkLabel(main,text="")
sourceImagePathText = Label(main,text=sourceImagePath.get())
sourceImagePathText.pack()
button_two = Button(main,text="Choose Source Image",height=1,width=20,fg="black",command=setSourceImagePath)
button_two.pack()
button_three = Button(main,text ="REPLACE VIDEO",height=1,width=15,command=Replace)
button_three.pack(pady=40)

pPercentage = Label(main,text="")
pPercentage.pack()
progressBar = ttk.Progressbar(main,mode="indeterminate")
#progressBar.pack()


errorText = Label(main,text="",fg = "red")
errorText.pack()
main.mainloop()
main.update_idletasks()
