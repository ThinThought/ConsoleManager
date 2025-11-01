scp -r root@192.168.1.140:/mnt/sdcard/Roms ./hot_copy
python scripts/sanitize_roms.py
scp -r ./hot_copy root@192.168.1.140:/mnt/sdcard/Roms
