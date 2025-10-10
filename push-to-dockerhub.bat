@echo off
REM Script to build and push Docker image to Docker Hub

SET DOCKER_USERNAME=dmitryodinoky
SET IMAGE_NAME=telegram-bot-sdxl
SET TAG=latest

echo ======================================
echo Building Docker Image for Coolify
echo ======================================

REM Build the image
echo Building image...
docker build -t %DOCKER_USERNAME%/%IMAGE_NAME%:%TAG% .

if %ERRORLEVEL% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

REM Tag with version (optional)
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
SET VERSION=%mydate%-%mytime%
docker tag %DOCKER_USERNAME%/%IMAGE_NAME%:%TAG% %DOCKER_USERNAME%/%IMAGE_NAME%:%VERSION%

echo.
echo ======================================
echo Image built successfully!
echo ======================================
echo Image: %DOCKER_USERNAME%/%IMAGE_NAME%:%TAG%
echo Version: %DOCKER_USERNAME%/%IMAGE_NAME%:%VERSION%
echo.

REM Login to Docker Hub
echo ======================================
echo Logging in to Docker Hub
echo ======================================
echo Please enter your Docker Hub credentials:
docker login

if %ERRORLEVEL% neq 0 (
    echo Login failed!
    pause
    exit /b 1
)

echo.
echo ======================================
echo Pushing to Docker Hub
echo ======================================

REM Push the images
echo Pushing latest tag...
docker push %DOCKER_USERNAME%/%IMAGE_NAME%:%TAG%

if %ERRORLEVEL% neq 0 (
    echo Push failed!
    pause
    exit /b 1
)

echo Pushing version tag...
docker push %DOCKER_USERNAME%/%IMAGE_NAME%:%VERSION%

echo.
echo ======================================
echo SUCCESS!
echo ======================================
echo Image pushed to Docker Hub:
echo   - %DOCKER_USERNAME%/%IMAGE_NAME%:%TAG%
echo   - %DOCKER_USERNAME%/%IMAGE_NAME%:%VERSION%
echo.
echo Update your Coolify docker-compose.yml to use:
echo   image: %DOCKER_USERNAME%/%IMAGE_NAME%:%TAG%
echo.
echo Or use docker-compose.coolify.yml which is already configured!
echo ======================================
pause
