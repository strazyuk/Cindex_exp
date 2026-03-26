# deploy.ps1
$bucket = "dhaka-crime-lambda-artifacts-0474af62"
$region = "us-east-1"

function Build-And-Deploy {
    param (
        [string]$service,
        [string]$functionName
    )

    Write-Host "Rebuilding $service..." -ForegroundColor Cyan
    $buildDir = "build_temp_$service"
    
    # Clean previous build directory
    if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
    New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
    
    # 1. Install dependencies into build directory
    Write-Host "  -> Installing Linux-compatible dependencies..."
    # The --platform and --only-binary flags ensure we get Linux .so files even on Windows
    pip install -r .\services\$service\requirements.txt -t $buildDir --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --only-binary=:all: --upgrade --quiet
    
    # 2. Copy application source code
    Write-Host "  -> Copying source code..."
    # Copy files while excluding __pycache__ to avoid conflicts
    Copy-Item -Path ".\services\$service\*" -Destination $buildDir -Recurse -Exclude "__pycache__" -Force
    
    # 3. Create ZIP archive
    Write-Host "  -> Zipping archive..."
    $zipPath = ".\build\$service.zip"
    if (!(Test-Path ".\build")) { New-Item -ItemType Directory -Force -Path ".\build" | Out-Null }
    if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
    Compress-Archive -Path ".\$buildDir\*" -DestinationPath $zipPath
    
    # 4. Upload ZIP to S3
    Write-Host "  -> Uploading to S3 Bucket ($bucket)..."
    aws s3 cp $zipPath "s3://$bucket/$service.zip" --quiet
    
    # 5. Inform Lambda to update its code from S3
    Write-Host "  -> Updating Lambda Function ($functionName)..."
    aws lambda update-function-code --function-name $functionName --s3-bucket $bucket --s3-key "$service.zip" --region $region | Out-Null
    
    # Cleanup temporary directory
    Remove-Item -Recurse -Force $buildDir
    Write-Host "✅ $service Deployment Complete!`n" -ForegroundColor Green
}

Write-Host "🚀 Starting Dhaka Crime Serverless Deployment...`n" -ForegroundColor Magenta

Build-And-Deploy -service "crawler" -functionName "dhaka-crime-crawler"
Build-And-Deploy -service "nlp" -functionName "dhaka-crime-nlp-processor"
Build-And-Deploy -service "index-calculator" -functionName "dhaka-crime-index-calculator"

Write-Host "🎉 All Serverless Functions Deployed Successfully!" -ForegroundColor Magenta
