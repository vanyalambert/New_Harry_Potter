param(
  [int]$Port = 3000
)
Write-Host "Serving frontend at http://127.0.0.1:$Port"
python -m http.server $Port