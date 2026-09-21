#Requires -Version 5.1
# multi-agents.ps1 — abre 3 terminales independientes, una por agente (backend/frontend/QA)
# Uso:  .\multi-agents.ps1        (ejecutar desde la raiz del repo labcore-app)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Parent   = Split-Path -Parent $RepoRoot

$Roles = @(
    @{ Dir = "labcore-app-backend";  Branch = "dev/backend";  Etiqueta = "Backend (Django/DRF)";   Deps = "..\Proyectos-app\.venv\Scripts\python.exe" }
    @{ Dir = "labcore-app-frontend"; Branch = "dev/frontend"; Etiqueta = "Frontend (React/Vite)";   Deps = "..\Proyectos-app\frontend\node_modules" }
    @{ Dir = "labcore-app-qa";       Branch = "dev/qa";       Etiqueta = "QA (pytest + Playwright)"; Deps = "..\Proyectos-app\.venv + ..\Proyectos-app\qa\e2e\node_modules" }
)

foreach ($rol in $Roles) {
    $wtPath = Join-Path $Parent $rol.Dir

    if (-not (Test-Path -LiteralPath (Join-Path $wtPath ".git"))) {
        Write-Host "[git] git worktree add -b $($rol.Branch) $wtPath main" -ForegroundColor Cyan
        git -C $RepoRoot worktree add -b $rol.Branch $wtPath main
    } else {
        Write-Host "[git] worktree $($rol.Dir) ya existe" -ForegroundColor Yellow
    }

    $inner = "Write-Host ''; `$line = '=' * 56; Write-Host `$line -ForegroundColor Cyan; " +
        "Write-Host '  LABCORE-APP  |  rama: $($rol.Branch)'; " +
        "Write-Host '  rol:          $($rol.Etiqueta)'; " +
        "Write-Host '  worktree:     $($rol.Dir)'; " +
        "Write-Host ('-' * 56); " +
        "Write-Host '  Dependencias (viven en el repo principal):'; Write-Host '    $($rol.Deps)'; " +
        "Write-Host ('-' * 56); " +
        "Write-Host '  Lanza el agente con:  opencode'; Write-Host '  Para salir:  exit'; " +
        "Write-Host `$line -ForegroundColor Cyan; Write-Host ''; " +
        "if (Get-Command opencode -ErrorAction SilentlyContinue) { opencode } " +
        "else { Write-Host 'opencode no encontrado en el PATH. Instalalo o escribelo a mano.' -ForegroundColor Yellow }"

    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($inner))
    Start-Process powershell -NoExit -WorkingDirectory $wtPath `
        -ArgumentList "-NoExit", "-EncodedCommand", $encoded
}

Write-Host ""
Write-Host "3 terminales abiertas. Resumen de worktrees:" -ForegroundColor Green
git -C $RepoRoot worktree list
Write-Host ""
Write-Host "Para integrar un rol a main (desde el repo principal):"
Write-Host "  git checkout main"
Write-Host "  git merge dev/backend    # (luego dev/frontend, dev/qa)" -ForegroundColor White