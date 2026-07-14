$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonCmd = $venvPython
} else {
    $pythonCmd = "python"
}

Write-Host "Using Python: $pythonCmd"

& $pythonCmd -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao instalar dependencias de desenvolvimento."
}

& $pythonCmd -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name PokedexDataStudio `
    --hidden-import=kivy_deps.sdl2 `
    --hidden-import=kivy_deps.glew `
    --hidden-import=kivy_deps.angle `
    --exclude-module kivy.tests `
    main.py

if ($LASTEXITCODE -ne 0) {
    throw "Falha ao gerar executavel com PyInstaller."
}

Write-Host "Build concluido em dist\PokedexDataStudio" -ForegroundColor Green
