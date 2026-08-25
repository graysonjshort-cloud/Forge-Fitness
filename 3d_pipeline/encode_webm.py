from pathlib import Path
import argparse, subprocess, shutil

p=argparse.ArgumentParser()
p.add_argument("--frames",required=True)
p.add_argument("--out",required=True)
p.add_argument("--fps",type=int,default=30)
a=p.parse_args()
if not shutil.which("ffmpeg"):
    raise SystemExit("ffmpeg is required to encode WebM")
frames=Path(a.frames)
out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
cmd=["ffmpeg","-y","-framerate",str(a.fps),"-i",str(frames/"frame_%04d.png"),
     "-c:v","libvpx-vp9","-crf","31","-b:v","0","-pix_fmt","yuv420p",
     "-an",str(out)]
subprocess.run(cmd,check=True)
print(out)
