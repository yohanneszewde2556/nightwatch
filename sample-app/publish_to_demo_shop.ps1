<#
.SYNOPSIS
    Publishes demo-shop with a realistic 3-commit history to GitHub.

.DESCRIPTION
    Clones https://github.com/yohanneszewde2556/demo-shop into a temporary directory,
    recreates the 3 sequential commits representing the demo lifecycle:
      1. "Initial demo-shop API" (v1 files, no discounts, no /logs)
      2. "Add discount codes to checkout" (adds discounts.py and updates checkout.py with the bug)
      3. "Add /logs endpoint and README" (adds structured logs ring buffer, /logs endpoint, README, tests)
    And pushes the result to the remote repository.

.NOTES
    DO NOT run automatically inside agent sessions. Run manually from PowerShell:
      .\publish_to_demo_shop.ps1
#>

[CmdletBinding()]
param(
    [string]$RepoUrl = "https://github.com/yohanneszewde2556/demo-shop.git",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TempDir = Join-Path $env:TEMP ("demo-shop-publish-" + [Guid]::NewGuid().ToString("N").Substring(0, 8))

Write-Host "=== Demo-Shop Publisher ===" -ForegroundColor Cyan
Write-Host "Source directory: $ScriptDir"
Write-Host "Target repo:      $RepoUrl"
Write-Host "Target branch:    $Branch"
Write-Host "Working temp dir: $TempDir"

try {
    # 1. Clone target repository
    Write-Host "`n--> Cloning repository..." -ForegroundColor Yellow
    git clone $RepoUrl $TempDir
    Set-Location $TempDir

    # Ensure branch exists and switch to it
    git checkout -B $Branch

    # Wipe existing files except .git
    Get-ChildItem -Path $TempDir -Exclude ".git" | Remove-Item -Recurse -Force

    # -------------------------------------------------------------
    # COMMIT 1: Initial demo-shop API
    # -------------------------------------------------------------
    Write-Host "`n--> Preparing Commit 1: Initial demo-shop API..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path (Join-Path $TempDir "app") -Force | Out-Null

    # Base files
    Copy-Item (Join-Path $ScriptDir "app\__init__.py") (Join-Path $TempDir "app\__init__.py")
    Copy-Item (Join-Path $ScriptDir "app\config.py") (Join-Path $TempDir "app\config.py")
    Copy-Item (Join-Path $ScriptDir "app\models.py") (Join-Path $TempDir "app\models.py")
    Copy-Item (Join-Path $ScriptDir "app\products.py") (Join-Path $TempDir "app\products.py")
    Copy-Item (Join-Path $ScriptDir "app\state.py") (Join-Path $TempDir "app\state.py")
    # v1 checkout snapshot (no discounts)
    Copy-Item (Join-Path $ScriptDir "history\checkout.py") (Join-Path $TempDir "app\checkout.py")
    Copy-Item (Join-Path $ScriptDir "Dockerfile") (Join-Path $TempDir "Dockerfile")
    Copy-Item (Join-Path $ScriptDir "requirements.txt") (Join-Path $TempDir "requirements.txt")
    Copy-Item (Join-Path $ScriptDir ".env.example") (Join-Path $TempDir ".env.example")

    # Basic .gitignore
    @"
__pycache__/
*.pyc
.env
.pytest_cache/
"@ | Set-Content (Join-Path $TempDir ".gitignore")

    # Minimal initial main.py without /logs or discounts
    @"
"""Main FastAPI application for demo-shop (v1)."""
import secrets
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from app.checkout import process_checkout
from app.config import settings
from app.models import (
    AdminStateResponse,
    ChaosRequest,
    CheckoutRequest,
    CheckoutResponse,
    DeployRequest,
    HealthResponse,
    Product,
)
from app.products import get_all_products, get_product
from app.state import state

app = FastAPI(title="demo-shop", version="1.0.0")

def verify_admin_token(x_admin_token: str | None = Header(None, alias="X-Admin-Token")) -> str:
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Token")
    return x_admin_token

@app.get("/health", response_model=HealthResponse)
def get_health():
    uptime = round(state.uptime_seconds, 2)
    if state.chaos_mode == "down":
        return JSONResponse(status_code=503, content={"status": "unhealthy", "version": state.version, "uptime_seconds": uptime, "error": "Chaos mode: down"})
    return HealthResponse(status="healthy", version=state.version, uptime_seconds=uptime)

@app.get("/products", response_model=list[Product])
def list_products():
    return get_all_products()

@app.get("/products/{product_id}", response_model=Product)
def get_product_by_id(product_id: int):
    product = get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product

@app.post("/checkout", response_model=CheckoutResponse)
def checkout(request: CheckoutRequest):
    try:
        return process_checkout(request, version=state.version)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/admin/state", response_model=AdminStateResponse, dependencies=[Depends(verify_admin_token)])
def get_admin_state():
    return AdminStateResponse(version=state.version, chaos_mode=state.chaos_mode, commit_label=state.commit_label)

@app.post("/admin/deploy", response_model=AdminStateResponse, dependencies=[Depends(verify_admin_token)])
def deploy_version(payload: DeployRequest):
    state.deploy(payload.version)
    return AdminStateResponse(version=state.version, chaos_mode=state.chaos_mode, commit_label=state.commit_label)

@app.post("/admin/rollback", response_model=AdminStateResponse, dependencies=[Depends(verify_admin_token)])
def rollback_version():
    state.rollback()
    return AdminStateResponse(version=state.version, chaos_mode=state.chaos_mode, commit_label=state.commit_label)

@app.post("/admin/chaos", response_model=AdminStateResponse, dependencies=[Depends(verify_admin_token)])
def set_chaos_mode(payload: ChaosRequest):
    state.set_chaos(payload.mode)
    return AdminStateResponse(version=state.version, chaos_mode=state.chaos_mode, commit_label=state.commit_label)
"@ | Set-Content (Join-Path $TempDir "app\main.py")

    git add -A
    git commit -m "Initial demo-shop API"

    # -------------------------------------------------------------
    # COMMIT 2: Add discount codes to checkout
    # -------------------------------------------------------------
    Write-Host "`n--> Preparing Commit 2: Add discount codes to checkout..." -ForegroundColor Yellow
    Copy-Item (Join-Path $ScriptDir "app\discounts.py") (Join-Path $TempDir "app\discounts.py")
    Copy-Item (Join-Path $ScriptDir "app\checkout.py") (Join-Path $TempDir "app\checkout.py")

    git add -A
    git commit -m "Add discount codes to checkout"

    # -------------------------------------------------------------
    # COMMIT 3: Add /logs endpoint and README
    # -------------------------------------------------------------
    Write-Host "`n--> Preparing Commit 3: Add /logs endpoint and README..." -ForegroundColor Yellow
    Copy-Item (Join-Path $ScriptDir "app\logs.py") (Join-Path $TempDir "app\logs.py")
    Copy-Item (Join-Path $ScriptDir "app\main.py") (Join-Path $TempDir "app\main.py")
    Copy-Item (Join-Path $ScriptDir "README.md") (Join-Path $TempDir "README.md")

    if (Test-Path (Join-Path $ScriptDir "tests")) {
        Copy-Item (Join-Path $ScriptDir "tests") (Join-Path $TempDir "tests") -Recurse
    }

    git add -A
    git commit -m "Add /logs endpoint and README"

    # -------------------------------------------------------------
    # Push to GitHub
    # -------------------------------------------------------------
    Write-Host "`n--> Pushing commits to $RepoUrl ($Branch)..." -ForegroundColor Yellow
    git push origin $Branch --force

    Write-Host "`n[SUCCESS] Successfully pushed 3 commits to demo-shop!" -ForegroundColor Green

} catch {
    Write-Host "`n[ERROR] An error occurred: $_" -ForegroundColor Red
    throw
} finally {
    Set-Location $ScriptDir
    if (Test-Path $TempDir) {
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
