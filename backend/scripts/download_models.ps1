# Downloads the MediaPipe model files required by app/video_analysis.
# Run from anywhere: powershell -ExecutionPolicy Bypass -File backend/scripts/download_models.ps1

$ErrorActionPreference = "Stop"

$modelsDir = Join-Path $PSScriptRoot "..\app\video_analysis\models"
New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null

$models = @(
    @{
        Name = "face_landmarker.task"
        Url  = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    },
    @{
        Name = "pose_landmarker.task"
        Url  = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    },
    @{
        Name = "hand_landmarker.task"
        Url  = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    }
)

foreach ($model in $models) {
    $dest = Join-Path $modelsDir $model.Name
    if (Test-Path $dest) {
        Write-Host "[skip] $($model.Name) already exists"
        continue
    }
    Write-Host "[download] $($model.Name)..."
    Invoke-WebRequest -Uri $model.Url -OutFile $dest
}

Write-Host "All MediaPipe models ready in $modelsDir"
