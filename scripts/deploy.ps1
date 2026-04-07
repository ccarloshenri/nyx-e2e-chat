$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$Stage = "main"
$StackName = "nyx-main"
$deployArgs = $args

function Add-ToPathIfExists {
    param(
        [string]$PathEntry
    )

    if (-not (Test-Path $PathEntry)) {
        return
    }

    $pathParts = $env:Path -split ';'
    if ($pathParts -notcontains $PathEntry) {
        $env:Path = "$PathEntry;$env:Path"
    }
}

Add-ToPathIfExists (Join-Path $env:LocalAppData "Programs\Python\Python312")
Add-ToPathIfExists (Join-Path $env:LocalAppData "Programs\Python\Python312\Scripts")
Add-ToPathIfExists (Join-Path $env:LocalAppData "Programs\Python\Launcher")
Add-ToPathIfExists (Join-Path $env:ProgramFiles "Amazon\AWSCLIV2")

if (-not (Get-Command sam -ErrorAction SilentlyContinue)) {
    throw "[deploy] AWS SAM CLI is required"
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "[deploy] npm is required"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "[deploy] Python 3.12+ is required"
}

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "[deploy] AWS CLI is required"
}

function Ensure-FrontendBucket {
    param(
        [string]$Region
    )

    $accountId = aws sts get-caller-identity --query "Account" --output text
    if (-not $accountId -or $accountId -eq "None") {
        throw "[deploy] Could not resolve AWS account id"
    }

    if ($env:FRONTEND_BUCKET) {
        $bucketName = $env:FRONTEND_BUCKET
    } else {
        $bucketName = "nyx-frontend-$accountId-$Region"
    }

    $bucketExists = $false
    try {
        & aws s3api head-bucket --bucket $bucketName *> $null
        $bucketExists = $LASTEXITCODE -eq 0
    } catch {
        $bucketExists = $false
    }

    if (-not $bucketExists) {
        Write-Host "[deploy] Creating frontend bucket s3://$bucketName"
        if ($Region -eq "us-east-1") {
            aws s3api create-bucket --bucket $bucketName | Out-Null
        } else {
            aws s3api create-bucket --bucket $bucketName --create-bucket-configuration LocationConstraint=$Region | Out-Null
        }
    } else {
        Write-Host "[deploy] Frontend bucket already exists: s3://$bucketName"
    }

    return $bucketName
}

$awsRegion = aws configure get region
if (-not $awsRegion) {
    $awsRegion = "us-east-1"
}

$frontendBucket = Ensure-FrontendBucket -Region $awsRegion

Write-Host "[deploy] Building and deploying backend"
Set-Location (Join-Path $RootDir "backend")
sam build
sam deploy `
    --stack-name $StackName `
    --resolve-s3 `
    --capabilities CAPABILITY_IAM `
    --parameter-overrides `
    "StageName=$Stage" `
    "UsersTableName=nyx-users-$Stage" `
    "ConnectionsTableName=nyx-connections-$Stage" `
    "ConversationsTableName=nyx-conversations-$Stage" `
    "MessagesTableName=nyx-messages-$Stage" `
    "MessageQueueName=nyx-message-delivery-$Stage.fifo" `
    "MessageDlqName=nyx-message-delivery-dlq-$Stage.fifo" `
    @deployArgs

Write-Host "[deploy] Building frontend"
Set-Location (Join-Path $RootDir "frontend")
npm install

$apiBaseUrl = $null
try {
    $apiBaseUrl = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue" --output text
} catch {
    $apiBaseUrl = $null
}

if ($apiBaseUrl -and $apiBaseUrl -ne "None") {
    Write-Host "[deploy] Using deployed backend URL: $apiBaseUrl"
    $env:VITE_API_BASE_URL = $apiBaseUrl
    npm run build
    Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
} else {
    Write-Host "[deploy] Could not resolve HttpApiUrl output, building frontend with existing environment"
    npm run build
}

Write-Host "[deploy] Uploading frontend dist/ to s3://$frontendBucket"
aws s3 sync dist/ "s3://$frontendBucket"
