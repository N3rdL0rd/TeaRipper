@echo off
rmdir /s /q dist
rmdir /s /q build
mkdir dist
mkdir build
pyinstaller --onedir --name teacx --distpath dist teacx.py & pyinstaller --onedir --name tearipper --distpath dist tearipper.py & pyinstaller --onedir --name teasnd --distpath dist teasnd.py