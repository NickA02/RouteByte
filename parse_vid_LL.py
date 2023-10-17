import cv2 as cv
import numpy as np
import os
import xml.etree.ElementTree as ET
import multiprocessing

video_name_base = "/work/users/n/a/nalmy/ROUTES/"
output_dir = "/work/users/n/a/nalmy/split_clips_routebyte/"

def main():
    corrected_files = []
    for subdir in ['BUF OFF', 'CIN OFF', 'KC OFF', 'MIA OFF', 'PHI OFF', 'SF OFF']:
        if not os.path.exists(output_dir + subdir):
            os.mkdir(output_dir + subdir)
        d = os.listdir(video_name_base)
        d.pop(0)
        for file in d:
            if file[-4:] == '.mp4':
                corrected_files.append(video_name_base+subdir+"/"+file[:-4])
    # Number of CPU cores available
    
    num_cores = 12

    # Create a multiprocessing Pool with the specified number of cores

    
    pool = multiprocessing.Pool(processes=num_cores)
    
    # Map the video processing function to the list of video files
    pool.map(process_video, corrected_files)

    # Close the pool and wait for all processes to finish
    pool.close()
    pool.join()


def process_video(game: str):
    full_game_tree = ET.parse(f"{game}.xchange")

    clips = [x.text for x in full_game_tree.findall("Plays/Play/Views/View/MarkIn")]
    durs = [x.text for x in full_game_tree.findall("Plays/Play/Views/View/Duration")]

    v= VideoHandler(videoPath=game)
    first = clips.pop(0)

    while v.frame_number < int(first):
        v.feed()
    clip_num = 1
    cam = None
    for outmark in clips:
        cam: cv.VideoWriter = new_clip(clip_num, v, cam)
        while v.frame_number < int(outmark):
            add_frame(cam, v.currentFrame)
            v.feed()
        clip_num += 1

    cam: cv.VideoWriter = new_clip(clip_num, v, cam)
    while v.feed():
        add_frame(cam,v.currentFrame)
    cam.release()
    return




class VideoHandler:
    video_player: cv.VideoCapture
    currentFrame: np.ndarray
    frame_number: int = 0
    isPlaying: bool = True


    def __init__(self, videoPath: str):
        if not os.path.exists(f"{videoPath}.mp4"):
            raise Exception(f"Video path {videoPath}.mp4 not found")
        self.video_player = cv.VideoCapture(f"{videoPath}.mp4")
        if not self.video_player.isOpened():
            raise Exception("Error: Could not open video file")
        self.feed()

    
    def startFeed(self):
        self.isPlaying = True

    def pauseFeed(self):
        self.isPlaying = False
    
    def feed(self) -> int:
        if self.isPlaying:
            # Capture frame-by-frame
            ret, frame = self.video_player.read()
            # if frame is read correctly ret is True
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                return
            self.frame_number += 1
            self.currentFrame = frame
        return self.frame_number

            
    def skip_to_frame(self, frame_number: int):
        if frame_number < 0 or frame_number > self.video_player.get(cv.CAP_PROP_FRAME_COUNT):
            print(frame_number)
            print(self.video_player.get(cv.CAP_PROP_FRAME_COUNT))
            raise Exception("Error: Frame Index Out of Bounds")
        self.video_player.set(cv.CAP_PROP_POS_FRAMES, frame_number)
        self.frame_number = frame_number
        if not self.isPlaying:
            self.isPlaying = True
            self.feed()
            self.isPlaying = False
            return
        self.feed()
    
    def set_video(self, path: str):
        if self.video_player.isOpened():
            self.video_player.release()
        if not path.endswith(".mp4"):
            raise Exception("Error: Invalid Data Type for video")
        self.video_player = cv.VideoCapture(path)
        if not self.video_player.isOpened():
            raise Exception("Error: Could not open video file")
        self.skip_to_frame(0)
        self.feed()
    
    def getCurrentFrame(self) -> np.ndarray:
        """Retrieves current frame"""
        cf = self.currentFrame
        return cf

def new_clip(play_number, v, game, cam=None):
        """Function that ends current clip and begins a new one"""
        if  cam != None:
            cam.release()

        #Create new clip for next view
        return cv.VideoWriter(
            f"{output_dir}/{game[6:24]} {play_number}.mp4",
            cv.VideoWriter_fourcc(*'mp4v'),
            60,
            (v.currentFrame.shape[1], v.currentFrame.shape[0])
            )

def add_frame(cam, frame: np.array):
        """Function that adds a given frame to the clip"""
        try:
            cam.write(frame)
        except:
            print("Video not open. Done recording clips?")

if __name__ == "__main__":
    main()