@echo off
rem Filizyol pipeline - cift tiklayarak calistirma (masaustundeki "Filizyol Pipeline" kisayolu buraya gider).
rem Ayni secenekler verilebilir:  pipeline_calistir.cmd -MeslekHazirla   /   pipeline_calistir.cmd -SistemdekiniAl
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pipeline_calistir.ps1" %*
echo.
pause
