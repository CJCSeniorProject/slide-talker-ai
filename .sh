!update-alternatives --install /usr/local/bin/python3 python3 /usr/bin/python3.8 2  
!update-alternatives --install /usr/local/bin/python3 python3 /usr/bin/python3.9 1  
!python --version  
!apt-get update
!apt install software-properties-common
!sudo dpkg --remove --force-remove-reinstreq python3-pip python3-setuptools python3-wheel
!apt-get install python3-pip

print('Git clone project and install requirements...')
!git clone https://github.com/Winfredy/SadTalker &> /dev/null
%cd SadTalker 
!export PYTHONPATH=/content/SadTalker:$PYTHONPATH 
!python3.8 -m pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113
!apt update
!apt install ffmpeg &> /dev/null  
!python3.8 -m pip install -r requirements.txt

print('Download pre-trained models...')
!rm -rf checkpoints
!bash scripts/download_models.sh

!conda activate sadtalker