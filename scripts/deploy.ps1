$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$Stage = if ($args.Length -gt 0) { $args[0] } else { "develop" }
$StackName = "nyx-e2e-chat-$Stage"
$deployArgs = if ($args.Length -gt 1) { $args[1..($args.Length - 1)] } else { @() }

if (-not (Get-Command sam -ErrorAction SilentlyContinue)) {
    throw "[deploy] AWS SAM CLI is required"
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "[deploy] npm is required"
}

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
if (Get-Command aws -ErrorAction SilentlyContinue) {
    try {
        $apiBaseUrl = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue" --output text
    } catch {
        $apiBaseUrl = $null
    }
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

if ($env:FRONTEND_BUCKET) {
    $targetBucket = "$($env:FRONTEND_BUCKET)-$Stage"
    Write-Host "[deploy] Uploading frontend dist/ to s3://$targetBucket"
    aws s3 sync dist/ "s3://$targetBucket"
} else {
    Write-Host "[deploy] FRONTEND_BUCKET not set, skipping S3 sync"
}
