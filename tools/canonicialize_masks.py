#!/usr/bin/env python3
import os
import sys
import subprocess
sys.path.append(os.getcwd())
import numpy as np
from viewer import fix, get_colormap
from tqdm import tqdm
from multiprocessing import Pool
from PIL import Image

colormap = get_colormap()

onlycheck = os.getenv("ONLYCHECK") is not None

def convert_string(x):
  if type(x) is str:
    return x
  else:
    return x.decode("utf-8")

def canon_mask(x):
  segi = fix(Image.open("masks/"+convert_string(x)))

  if segi.shape != (874, 1164, 3):
    print(convert_string(x)+" HAS BAD SHAPE", segi.shape)
    return True

  #print(x, segi.shape, segi.dtype)
  check = segi.reshape(-1, 3)

  ok = np.zeros(check.shape[0], dtype=np.bool)
  for v in colormap.values():
    okk = check == np.array(v)
    okk = np.all(okk, axis=1)
    ok |= okk

  bad = False

  if not np.all(ok):
    print(convert_string(x)+" HAS %d pixels with BAD COLORS" % sum(np.logical_not(ok)))
    print(check[np.logical_not(ok)])
    bad = True
    """
    cva = np.array(list(colormap.values()))
    maxb = 0
    for i in np.argwhere(np.logical_not(ok)):
      vv = np.mean((check[i] - cva)**2, axis=1)
      col = np.argmin(vv)
      maxb = max(vv[col], maxb)
      if maxb >= 20:
        break
      #print(i, check[i], col, vv[col])
      check[i] = cva[col]
    if maxb < 20:
      print("FIXED", maxb)
      segi = check.reshape(segi.shape)
    else:
      print("COULDN'T FIX", maxb)
    """

  if not onlycheck:
    im = Image.fromarray(segi)
    im.save("masks/"+x)

  #os.rename("masks/_"+x, "masks/"+x)
  return bad

if __name__ == "__main__":
  lst = sorted(os.listdir("masks/"))
  if len(sys.argv) > 1:
    canon_mask(lst[int(sys.argv[1])])
    exit(0)

  bads = []

  if onlycheck:
    # Only process changed files
    lst = subprocess.check_output("git diff --name-only HEAD origin/master masks/ | awk '{sub(/masks\//,\"\"); print }'", shell=True).strip().split(b"\n")
    if len(lst[0].decode("utf-8")) > 0:
      for bad in tqdm(map(canon_mask, lst), total=len(lst)):
        bads.append(bad)
  else:
    p = Pool(16)
    for bad in tqdm(p.imap_unordered(canon_mask, lst), total=len(lst)):
      bads.append(bad)

  if any(bads):
    print("THERE ARE %d BAD IMAGES IN THE DATASET" % sum(bads), list(np.where(bads)[0]))
    ALLOWED_BAD = 0
    if sum(bads) > ALLOWED_BAD:
      exit(-1)
    else:
      # TODO: as you fix the bad images, lower ALLOWED_BAD
      exit(0)
  else:
    exit(0)
