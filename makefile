# Makefile for updating AWS Lambda function code

# Variables
FUNCTION_NAME := rss_feed_checker
ZIP_FILE := lambda.zip
AWS_REGION := us-east-2
LAMBDA_FILE := lambda_function.py
PROFILE ?= default

# Default target
.PHONY: update
update: package deploy

# Package the Lambda function
.PHONY: package
package:
	@echo "Packaging Lambda function..."
	zip $(ZIP_FILE) $(LAMBDA_FILE)

# Deploy the Lambda function
.PHONY: deploy
deploy:
	@echo "Updating Lambda function code..."
	aws lambda update-function-code \
		--function-name $(FUNCTION_NAME) \
		--zip-file fileb://$(ZIP_FILE) \
		--region $(AWS_REGION) \
		--profile $(PROFILE)

# Clean up
.PHONY: clean
clean:
	@echo "Cleaning up..."
	rm -f $(ZIP_FILE)
