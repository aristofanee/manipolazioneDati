$ProjectDir = $PSScriptRoot
$VenvDir = Join-Path $ProjectDir "venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

Write-Host "`n--- Pulling latest changes from Git..."
Set-Location $ProjectDir
git pull

if (-Not (Test-Path $VenvDir)) {
    Write-Host "`n--- Creating virtual environment..."
    python -m venv venv
}

& "venv\Scripts\activate"

Write-Host "`n--- Installing requirements..."
& "$PythonExe" -m pip install -r requirements.txt

Write-Host "`n--- Running main.py..."
& "$PythonExe" "src\main.py"


Write-Host "`n--- Done. Press Enter to exit."
Read-Host
