from pathlib import Path
import argparse, shutil, subprocess
p=argparse.ArgumentParser()
p.add_argument("--webm",required=True);p.add_argument("--out",required=True)
a=p.parse_args()
if not shutil.which("ffmpeg"): raise SystemExit("ffmpeg required")
out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(["ffmpeg","-y","-ss","1","-i",a.webm,"-frames:v","1","-c:v","libwebp",str(out)],check=True)
print(out)
