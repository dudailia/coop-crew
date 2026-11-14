# coop-crew on Windows runs inside WSL (Ubuntu). This script checks WSL and runs install.sh there.
# Email: on Windows there is no Mail adapter; outreach writes .eml drafts and a copy-ready list you send from your own client.
$ErrorActionPreference = "Stop"
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
  Write-Host "WSL is not installed. In an administrator PowerShell run:  wsl --install   then restart and run this script again."
  exit 1
}
$distros = (wsl.exe -l -q) -join " "
if ($distros.Trim() -eq "") {
  Write-Host "WSL has no Linux distribution yet. Run:  wsl --install -d Ubuntu   then run this script again."
  exit 1
}
$here = (Get-Location).Path
$wslPath = (wsl.exe wslpath -a "$here").Trim()
Write-Host "Installing coop-crew inside WSL at $wslPath ..."
wsl.exe bash -lc "cd '$wslPath' && ./install.sh"
Write-Host "Next: open Ubuntu (WSL), cd to $wslPath, run 'claude', then type /setup"
