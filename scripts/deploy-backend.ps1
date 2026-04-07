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
    throw "[deploy-backend] AWS SAM CLI is required"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "[deploy-backend] Python 3.12+ is required"
}

Write-Host "[deploy-backend] Building and deploying backend"
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
