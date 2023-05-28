

provider "aws" {
  region = "eu-central-1"

  assume_role {
    role_arn      = "arn:aws:iam::465016927915:role/CircleciRole"
  }
  
}
terraform {
backend "s3"{
	access_key  = "ASIAQR2VRMQ3GIBSDCUQ"
	secret_key = "BPSjVRVLQdIVuhmHN3+PgTNsVRh1X6qFZC6UXiCL"
    bucket      = "my-tf-test-bucket-mkzielak1"
    key        = "oidc/terraform.tfstate"
    region      = "eu-central-1"
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