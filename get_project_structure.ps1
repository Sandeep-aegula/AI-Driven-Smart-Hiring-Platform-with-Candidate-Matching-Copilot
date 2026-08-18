$excludeDirs = @('.git', '.venv', 'venv', '__pycache__', '.pytest_cache',
                  'node_modules', '.streamlit', '.claude', '.idea', '.vscode',
                  'dist', 'build', '.mypy_cache')

$excludePattern = ($excludeDirs | ForEach-Object { [regex]::Escape($_) }) -join '|'
$regex = "\\($excludePattern)(\\|$)"

$root = Get-Location
$outFile = Join-Path $root "project_structure.txt"

$items = Get-ChildItem -Recurse -Force -Path $root | Where-Object {
    $_.FullName -notmatch $regex
}

"Project structure for: $root" | Out-File -Encoding utf8 $outFile
"Generated: $(Get-Date)" | Out-File -Encoding utf8 -Append $outFile
"" | Out-File -Encoding utf8 -Append $outFile

foreach ($item in $items | Sort-Object FullName) {
    $relative = $item.FullName.Substring($root.Path.Length)
    if ($item.PSIsContainer) {
        "[DIR]  $relative" | Out-File -Encoding utf8 -Append $outFile
    } else {
        $sizeKB = [math]::Round($item.Length / 1KB, 1)
        "[FILE] $relative  ($sizeKB KB)" | Out-File -Encoding utf8 -Append $outFile
    }
}

Write-Host "Done. Structure saved to $outFile"
Write-Host "Total items: $($items.Count)"
