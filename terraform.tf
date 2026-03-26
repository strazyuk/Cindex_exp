# Provider Configuration
provider "aws" {
  region = "us-east-1"
}

# --- S3 & SQS ---
resource "random_id" "id" {
  byte_length = 4
}

resource "aws_s3_bucket" "html_storage" {
  bucket = "dhaka-crime-raw-html-${random_id.id.hex}"
}

resource "aws_sqs_queue" "crime_queue" {
  name                       = "crime-extraction-queue"
  visibility_timeout_seconds = 300 # 5 minutes, gives NLP lambda time to process
}

# --- Variables (Database and API Keys) ---
variable "database_url" {
  description = "Supabase PostgreSQL connection string"
  type        = string
  sensitive   = true
}

variable "groq_api_key" {
  description = "API Key for Groq Llama 3"
  type        = string
  sensitive   = true
}
# --- IAM Roles for Lambda ---
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_execution_role" {
  name               = "dhaka_crime_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_service_policy" {
  name        = "dhaka_crime_lambda_service_policy"
  description = "Permissions for S3 and SQS access for Lambdas"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:*"]
        Resource = ["${aws_s3_bucket.html_storage.arn}", "${aws_s3_bucket.html_storage.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["sqs:*"]
        Resource = aws_sqs_queue.crime_queue.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_app_policy" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_service_policy.arn
}

# --- Lambda Artifacts in S3 ---
resource "aws_s3_bucket" "lambda_artifacts" {
  bucket = "dhaka-crime-lambda-artifacts-${random_id.id.hex}"
}

# --- Dummy Zip Archives Removed ---
# Deployment is managed externally by deploy.ps1 to properly package dependencies.
# We no longer zip the source directory locally during terraform apply.

# --- 1. Crawler Lambda (Cron Triggered) ---
resource "aws_lambda_function" "crawler" {
  function_name    = "dhaka-crime-crawler"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "aws_handler.handler"
  runtime          = "python3.11"
  timeout          = 300 # 5 minutes
  s3_bucket        = aws_s3_bucket.lambda_artifacts.bucket
  s3_key           = "crawler.zip"

  environment {
    variables = {
      SQS_CRAWL_QUEUE_URL = aws_sqs_queue.crime_queue.url
      STORAGE_MODE        = "s3"
      S3_BUCKET_NAME      = aws_s3_bucket.html_storage.bucket
    }
  }

  lifecycle {
    ignore_changes = [
      s3_bucket,
      s3_key,
      source_code_hash,
    ]
  }
}

resource "aws_cloudwatch_event_rule" "crawler_cron" {
  name                = "every-hour-crawler"
  schedule_expression = "rate(2 hours)"
}

resource "aws_cloudwatch_event_target" "trigger_crawler" {
  rule      = aws_cloudwatch_event_rule.crawler_cron.name
  target_id = "lambda"
  arn       = aws_lambda_function.crawler.arn
}

resource "aws_lambda_permission" "allow_eventbridge_crawler" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.crawler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.crawler_cron.arn
}

# --- 2. NLP Service (SQS Triggered) ---
resource "aws_lambda_function" "nlp" {
  function_name    = "dhaka-crime-nlp-processor"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "aws_handler.handler"
  runtime          = "python3.11"
  timeout          = 300
  memory_size      = 256
  s3_bucket        = aws_s3_bucket.lambda_artifacts.bucket
  s3_key           = "nlp.zip"

  environment {
    variables = {
      GROQ_API_KEY = var.groq_api_key
      DATABASE_URL = var.database_url
    }
  }

  lifecycle {
    ignore_changes = [
      s3_bucket,
      s3_key,
      source_code_hash,
    ]
  }
}

resource "aws_lambda_event_source_mapping" "sqs_to_nlp" {
  event_source_arn = aws_sqs_queue.crime_queue.arn
  function_name    = aws_lambda_function.nlp.arn
  batch_size       = 5
}

# --- 3. Index Calculator (API Gateway + Cron) ---
resource "aws_lambda_function" "indexer" {
  function_name    = "dhaka-crime-index-calculator"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "main.handler" # Mangum wrapper
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256
  s3_bucket        = aws_s3_bucket.lambda_artifacts.bucket
  s3_key           = "indexer.zip"

  environment {
    variables = {
      DATABASE_URL      = var.database_url
    }
  }

  lifecycle {
    ignore_changes = [
      s3_bucket,
      s3_key,
      source_code_hash,
    ]
  }
}

# Cron for 15-minute recalculation
resource "aws_cloudwatch_event_rule" "indexer_cron" {
  name                = "every-15-min-indexer"
  schedule_expression = "rate(15 minutes)"
}

resource "aws_cloudwatch_event_target" "trigger_indexer" {
  rule      = aws_cloudwatch_event_rule.indexer_cron.name
  target_id = "lambda"
  arn       = aws_lambda_function.indexer.arn
  input     = jsonencode({ "action": "cron" }) # Dummy payload to trigger it
}

resource "aws_lambda_permission" "allow_eventbridge_indexer" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.indexer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.indexer_cron.arn
}

# HTTP API Gateway for React Frontend
resource "aws_apigatewayv2_api" "http_api" {
  name          = "dhaka-crime-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"] # Configure strictly in Production
    allow_methods = ["GET", "OPTIONS"]
    allow_headers = ["content-type", "x-amz-date", "authorization", "x-api-key"]
  }
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id             = aws_apigatewayv2_api.http_api.id
  integration_uri    = aws_lambda_function.indexer.invoke_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.indexer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# --- Outputs ---
output "api_gateway_url" {
  value = aws_apigatewayv2_api.http_api.api_endpoint
  description = "Set this as REACT_APP_API_URL in your React Frontend"
}
output "s3_bucket_name" {
  value = aws_s3_bucket.html_storage.bucket
}