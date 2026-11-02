param(
    [Parameter(Mandatory=$true)]
    [string]$IpAddress,
    [Parameter(Mandatory=$false)]
    [int]$Port = 4370,
    [Parameter(Mandatory=$false)]
    [string]$CommKey = "000000",
    [Parameter(Mandatory=$false)]
    [string]$SinceDate = ""
)

$path = "C:\Program Files (x86)\essl\eTimeTrackLite"
$env:PATH = "$path;$env:PATH"
Set-Location $path

try {
    $zk = New-Object -ComObject zkemkeeper.ZKEM
} catch {
    Write-Output (ConvertTo-Json @{ error = "Failed to create zkemkeeper COM object: $($_.Exception.Message)" })
    exit 1
}

if (-not [string]::IsNullOrWhiteSpace($CommKey)) {
    [void]$zk.SetCommPasswordEx($CommKey)
} else {
    [void]$zk.SetCommPasswordEx("000000")
}

$connected = $zk.Connect_Net($IpAddress, $Port)
if (-not $connected) {
    $err = 0
    $zk.GetLastError([ref]$err)
    Write-Output (ConvertTo-Json @{ error = "Failed to connect to device at $IpAddress`:$Port. Error code: $err" })
    exit 1
}

$readOk = $zk.ReadAllGLogData(1)
if (-not $readOk) {
    $zk.Disconnect()
    Write-Output (ConvertTo-Json @{ error = "ReadAllGLogData failed on device" })
    exit 1
}

$enrollNumber = ""
$verifyMode = 0
$inOutMode = 0
$year = 0
$month = 0
$day = 0
$hour = 0
$minute = 0
$second = 0
$workCode = 0

$logs = @()

$hasThreshold = $false
$threshold = [DateTime]::MinValue
if (-not [string]::IsNullOrWhiteSpace($SinceDate)) {
    try {
        $threshold = [DateTime]::Parse($SinceDate)
        $hasThreshold = $true
    } catch {}
}

while ($zk.SSR_GetGeneralLogData(1, [ref]$enrollNumber, [ref]$verifyMode, [ref]$inOutMode, [ref]$year, [ref]$month, [ref]$day, [ref]$hour, [ref]$minute, [ref]$second, [ref]$workCode)) {
    $dt = [DateTime]::new($year, $month, $day, $hour, $minute, $second)
    if (-not $hasThreshold -or $dt -ge $threshold) {
        $logs += [PSCustomObject]@{
            UserId = [string]$enrollNumber
            LogDate = $dt.ToString("yyyy-MM-dd HH:mm:ss")
            VerifyMode = [int]$verifyMode
            InOutMode = [int]$inOutMode
            WorkCode = [int]$workCode
        }
    }
}

$zk.Disconnect()

if ($logs.Count -eq 0) {
    Write-Output "[]"
} else {
    Write-Output (ConvertTo-Json $logs -Compress)
}
