@echo off
setlocal
set PATH=%PATH%;C:\Program Files\7-Zip
robocopy /mt /move "dist\teacx" "dist" x* /E
robocopy /mt /move "dist\tearipper" "dist" x* /E
robocopy /mt /move "dist\teasnd" "dist" x* /E
rd /s /q "dist\teacx"
rd /s /q "dist\tearipper"
rd /s /q "dist\teasnd"
cd dist
7z a -tzip "tearipper.zip" "*"
cd ..
endlocal