FROM nvidia/cuda:11.7.1-cudnn8-devel-ubuntu22.04
SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND noninteractive
ENV MPLLOCALFREETYPE 1
RUN sed -i 's|http://archive.ubuntu|http://mirror.kakao|g' /etc/apt/sources.list
RUN sed -i 's|http://security.ubuntu|http://mirror.kakao|g' /etc/apt/sources.list

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PATH=/opt/conda/bin:$PATH
ENV TZ=Asia/Seoul

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y wget unzip zip
RUN apt-get update --fix-missing


# Install Python
RUN apt-get install -y python3.10 python3-pip

# Install basic packages
RUN apt-get install -y \
    build-essential cmake libtool autoconf \
    bzip2 curl git tty-clock vim tmux dpkg \
    htop kmod gcc-10 g++-10 clang

# Install headless packages
RUN apt-get install -y \ 
    hicolor-icon-theme libgl1-mesa-dri \
    libgl1-mesa-glx libpulse0 \
    libv4l-0 fonts-symbola \
    libfontconfig1 libxrender1 \ 
    libxrandr2 libxinerama1 \ 
    libopenal1 mesa-utils 

# Install dolphin dependencies
RUN apt-get install -y \ 
    pkg-config libgl1-mesa-dev libglu1-mesa-dev \
    libx11-dev libavcodec-dev libavformat-dev libavfilter-dev \
    libudev-dev libevdev-dev libxi-dev libzstd-dev clisp-module-zlib \
    liblzma-dev minizip libssl-dev liblzo2-dev libpam0g-dev \
    liblz4-dev libpugixml-dev libfmt-dev bzip2 libsdl2-dev zlib1g-dev qt6-base-dev libqt6svg6-dev

RUN apt-get update --fix-missing
RUN apt-get upgrade -y

RUN apt-get install sudo
RUN apt-get update
RUN apt-get autoremove

# Install libusb
COPY ./sources.list /etc/apt/sources.list
RUN sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3B4FE6ACC0B21F32
RUN sudo apt-get update
RUN sudo apt-get install -y libusb-1.0-0-dev

# GCC, G++ update from 9 to 10 (no use in ubuntu 22.04)
# RUN sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 40
# RUN sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-10 60
# RUN sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 40
# RUN sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 60

# Test
COPY ./test /root/test
RUN sh /root/test/test.sh
RUN rm -rf /root/test

# Copy and install requirements.txt
COPY requirements.txt /root/requirements.txt
RUN pip3 install -r /root/requirements.txt

# Install Pytorch
RUN pip3 install torch==1.13.1+cu117 torchvision==0.14.1+cu117 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu117

# Update requests
RUN pip3 install --upgrade requests

# Install libmelee & melee-env
RUN pip3 install git+https://github.com/vladfi1/libmelee@dev
COPY ./multi-env /root/multi-env
WORKDIR /root/multi-env
RUN pip3 install -e libmelee
RUN pip3 install -e melee-env 

# Install & Extract Appimage
WORKDIR /root
COPY ./Slippi_Online-x86_64-ExiAI.AppImage /root/Slippi_Online-x86_64-ExiAI.AppImage
RUN chmod 0700 ./Slippi_Online-x86_64-ExiAI.AppImage
RUN ~/Slippi_Online-x86_64-ExiAI.AppImage --appimage-extract

# Make replay directory
RUN mkdir slippi_replays
RUN mkdir slippi_replays/Regenerated

# Copy ISO file
COPY ./ssbm.iso /root/ssbm.iso

# Install Dolphin
COPY ./agents_example.py /root/agents_example.py
RUN python3 agents_example.py --iso ssbm.iso

# Copy & Apply Dolphin.ini
COPY ./Dolphin.ini /root/Dolphin.ini
RUN mkdir ~/.local/share/melee-env/Slippi/data
RUN mkdir ~/.local/share/melee-env/Slippi/data/Config
RUN mv ~/Dolphin.ini ~/.local/share/melee-env/Slippi/data/Config/Dolphin.ini

# Copy & Apply ExiAI Appimage
RUN mv ~/.local/share/melee-env/Slippi/squashfs-root ~/.local/share/melee-env/Slippi/squashfs-root.old
RUN mv squashfs-root ~/.local/share/melee-env/Slippi

RUN python3 agents_example.py --iso ssbm.iso

# Clean up files
RUN rm agents_example.py
RUN rm requirements.txt

# remove cache
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*