# Builds the RAG index and fine-tunes the classifier as a detached process.
# Launch: Start-Process powershell -ArgumentList '-File training\run_training.ps1' -WindowStyle Hidden
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONIOENCODING = "utf-8"
$env:HF_HUB_DISABLE_PROGRESS_BARS = "1"
$py = ".venv\Scripts\python.exe"
New-Item -ItemType Directory -Force reports | Out-Null

"[$(Get-Date -Format s)] building RAG index" | Out-File reports\pipeline_jobs.log -Encoding utf8
& $py -W ignore -m app.rag.index *>> reports\pipeline_jobs.log

"[$(Get-Date -Format s)] training classifier" | Out-File reports\pipeline_jobs.log -Append -Encoding utf8
& $py -W ignore -u -m training.train_classifier --epochs 2 *> reports\train_classifier.log

"[$(Get-Date -Format s)] done (exit $LASTEXITCODE)" | Out-File reports\pipeline_jobs.log -Append -Encoding utf8
