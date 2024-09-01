Melee dockerfile
================
tag:240902

WARNING: THIS IS THE NIGHTLY BUILD OF MELEE-DOCKER.
CHECK THE VERSION OF THE tag and build date

Necessary additional files
--------------------------
```
- ssbm.iso
- Slippi_Online-x86_64-ExiAI.Appimage
```

File tree
---------
```
.
├── .gitignore
├── agents_example.py
├── Dockerfile
├── Dolphin.ini
├── matchmaking/
├── multi-env/
├── readme.md
├── requirements.txt
├── Slippi_Online-x86_64-ExiAI.AppImage  <- Additional file
├── sources.list
├── ssbm.iso                             <- Additional file
└── test/
```

How to build image
------------------
```
docker build --tag melee-env:240902 .
```


How to create container 
-----------------------
```
docker create -it --gpus all --device /dev/input/event22 --privileged --ipc host -v /dev/bus/usb:/dev/bus/usb --name {your_container_name} melee-env:240902
```

Python librarys
---------------
```
wandb
matplotlib
seaborn
numpy
nvitop
scikit-learn
tqdm
torch
melee
melee-env
requests
ray
lz4
```
