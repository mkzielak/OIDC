

provider "aws" {
  region = "eu-central-1"

  assume_role {
    role_arn      = "arn:aws:iam::038297232438:role/mkzielak-barnaba"
  }
  
}
terraform {
  backend "s3" {
    bucket      = "my-tf-test-bucket-mkzielak"
    key         = "terraform.tfstate"
    region      = "eu-central-1"
    access_key  = "AKIAWYRJLG2V4CYA3NFB"
    secret_key  = "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"
  }
}

resource "aws_s3_bucket" "a" {
  bucket = "my-tf-test-bucket-a-20230226"


  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}
/*

resource "aws_s3_bucket" "b" {
  bucket = "my-tf-test-bucket-bb-20230226"


  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}
*/