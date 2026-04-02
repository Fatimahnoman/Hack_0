# Live tail of Gold Tier pipeline logs (WhatsApp -> orchestrator -> dispatcher -> sender)
# Run: powershell -ExecutionPolicy Bypass -File monitor_gold_pipeline.ps1
# Or:  monitor_gold_pipeline.bat

$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$date = Get-Date -Format "yyyyMMdd"
$logs = @(
    @{ Path = "gold\logs\whatsapp_$date.log";          Label = "WHATSAPP WATCHER (needs_action)" },
    @{ Path = "gold\logs\linkedin_unified_$date.log";    Label = "LINKEDIN UNIFIED (feed / leads)" },
    @{ Path = "gold\logs\gmail_$date.log";               Label = "GMAIL WATCHER" },
    @{ Path = "gold\logs\gold_orchestrator_$date.log";   Label = "GOLD ORCHESTRATOR (pending_approval)" },
    @{ Path = "gold\logs\action_dispatcher_$date.log";   Label = "ACTION DISPATCHER (approved -> send)" },
    @{ Path = "gold\logs\whatsapp_sender_$date.log";     Label = "WHATSAPP SENDER" }
)

Write-Host "Gold pipeline monitor | Date=$date | Ctrl+C to stop" -ForegroundColor Green
Write-Host "Flow: needs_action -> pending_approval -> approved -> done" -ForegroundColor DarkGray
Write-Host ""

while ($true) {
    Clear-Host
    Write-Host "=== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" -ForegroundColor Cyan
    foreach ($entry in $logs) {
        $p = Join-Path $root $entry.Path
        Write-Host ""
        Write-Host "--- $($entry.Label) ---" -ForegroundColor Yellow
        Write-Host "    $p" -ForegroundColor DarkGray
        if (Test-Path $p) {
            Get-Content $p -Tail 18 -Encoding UTF8
        } else {
            Write-Host "    (no file yet)" -ForegroundColor DarkGray
        }
    }
    Start-Sleep -Seconds 10
}
