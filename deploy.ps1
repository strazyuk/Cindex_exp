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
    Write-Host "  -> Zipping archive (Python-based)..."
    $zipPath = ".\build\$service.zip"
    if (!(Test-Path ".\build")) { New-Item -ItemType Directory -Force -Path ".\build" | Out-Null }
    if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
    
    python .\scripts\zip_service.py $buildDir $zipPath
    
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

function Deploy-Frontend {
    Write-Host "`n🎨 Starting Frontend Deployment..." -ForegroundColor Cyan
    
    $frontendDir = "services/frontend"
    
    # 1. Get frontend bucket name and cloudfront ID from terraform if not provided
    Write-Host "  -> Retrieving infrastructure details..."
    $terraformOutput = terraform output -json | ConvertFrom-Json
    $frontendBucket = $terraformOutput.frontend_bucket_name.value
    $cfDistributionId = $terraformOutput.cloudfront_id.value # We need to add this output to terraform.tf
    
    if (!$frontendBucket) {
        Write-Error "Could not find frontend_bucket_name in terraform outputs. Please run 'terraform apply' first."
        return
    }

    # 2. Build React App
    Write-Host "  -> Building production bundle (Vite)..."
    Push-Location $frontendDir
    npm install --quiet
    npm run build
    Pop-Location

    # 3. Sync to S3
    Write-Host "  -> Syncing assets to S3 ($frontendBucket)..."
    aws s3 sync "$frontendDir/dist" "s3://$frontendBucket" --delete --quiet

    # 4. Invalidate CloudFront (Optional but recommended)
    if ($cfDistributionId) {
        Write-Host "  -> Invalidating CloudFront cache ($cfDistributionId)..."
        aws cloudfront create-invalidation --distribution-id $cfDistributionId --paths "/*" --quiet | Out-Null
    }

    Write-Host "✅ Frontend Deployment Complete!" -ForegroundColor Green
    Write-Host "🌍 URL: $($terraformOutput.cloudfront_url.value)" -ForegroundColor Yellow
}

Write-Host "🚀 Starting Dhaka Crime Serverless Deployment...`n" -ForegroundColor Magenta

# Deploy Backend
# Build-And-Deploy -service "crawler" -functionName "dhaka-crime-crawler"
# Build-And-Deploy -service "nlp" -functionName "dhaka-crime-nlp-processor"
Build-And-Deploy -service "index-calculator" -functionName "dhaka-crime-index-calculator"

# Deploy Frontend
Deploy-Frontend

Write-Host "`n🎉 All Services Deployed Successfully!" -ForegroundColor Magenta

