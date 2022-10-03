# ActiveState Ephemeral Environment Project 

### Problem Scenario: 

You are a member of a team dedicated to maintaining cloud-based infrastructure, continuous 
integration and deployment systems, data and systems access, and the build system used to manage production systems

The developers you support will need to replicate the production environment to test their code and  data changes. This includes running applications and services as well as accessing data that represents real systems. Since code and data changes may conflict with each other, we would like to provide unique and ephemeral environments, rather than testing everything in a single, shared staging or testing environment. Our task is to design processes and tooling to: 

    a) Replicate the production environment 
    b) In a repeatable way
    c) With minimal effort from developers to request this environment

Since automation is better than manual work. The less effort required for a developer to request such an environment, the better.

Therefore, to simply the task we may assume: 

    1.) All of the developers in the team uses Git and Github 
    2.) The process for requestng a new environment can be tied to GitHub pull requests 
    3.) We have an existing CI-CD pipeline. 

### Benefits of Ephemeral Environment : 
An ephemeral environment is a temporary short lived environment thats helps developer test their new changes of the application in an environment that is a replica of the production environment. It could have many services and databases that is an exact copy of the production so that when the final code is deployed to the production, the chances of having deployment failures are as low as possible. Ephemeral environments provide robust, on-demand platforms for running tests, previewing features, and collaborating asynchronously across teams.

### Some prerequisites to deploy this project

    a) You need to have access to the [git account](https://github.com/mr2chowd/activestate_assignment.git) and have knowledge of the basic git commands to do a pull request and cloning the repo. 
    b) You need to have access to the private s3 buckets where the stacks are saved to be run from the git workflow
    c) An AWS account with payment system enabled. Please note running this stack will incur cost and there are some expensive services used. Run with caution. 
    d) AWS Command Line Interface

### Design Summary 

To simplify the design we assumed the developers are working on a simple static website where it has prebuilt CI-CD pipeline which they uses to deploy their applications. We are going to give them an ephemeral environment where all that they need to do is create a pull request to the repo and the environment will be created for them in less than 10 minutes. Once they are done with the environment, all that needs to be done is close the pull request which will delete all the services leaving no traces of ephemeral environment that ever existed. The following resources will be created to make the environment replicate the production environment : 

    a) A new VPC will be created to host the new servers and databases
    b) Two private subnets will be created to host the database
    c) Two public subnets will be created for the web front end to be hosted
    d) Internet Gateway will be attached to the VPC for outside connectivity
    e) NatGateway will be provided so that private subnet also has indirect connection to the do any kinds of updates and downloads from the internet in a secure way 
    f) Route tables will be created to ensure proper routing and subnet associations
    g) Proper IAM roles are provided in the stacks for the Lambda functions as well as EC2 instances where the websites will be hosted
    h) Security groups will be provided for Bastion Server as well as the EC2 instances where the webserver will be hosted
    i) Auto Scaling Groups will be created so that when the CPU utilizations reach a certain threshold, new instances will be created to cope up with the increased request and traffic 
    j) Launch Template will be provided for resuability and version controlling of type of EC2 instances that needs to be scaled 
    k) Load Balancers will be created to equally divided the load of the web application to different servers on different Availabilty Zone
    l) RDS will be provided with the latest database files so that the environment can have the upto date data when tests are done. 
    m) Lambda functions will be created to attain the latest database copy snapshot and change the ephemeral stack with latest arn so that the whole process is completely automated
    n) Disaster recovery backup instances are created for the database in situations of lag in read operations 

### Execution Steps
All the codes will be given at the end and not in the steps to ensure readability.
## Step 1
The process starts with creating an empty git repositoryy and cloning it. Then we can make a directory ".github/workflows where we save the steps that will execute when the pull request is executed. Please save the "create_ephemeral.yml" [file](#Create_ephimeral.yml script) codes in this directory. 

#Create_ephimeral.yml script

```
# This is a workflow which will create the ephemeral environment for ActiveState Developers
name: Deploy
# Controls when the action will run. 
on:
  # Triggers the workflow on push or pull request events but only for the main branch
  pull_request_target:
    branches: [ main ]
    types: [assigned, opened, synchronize, reopened]
  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

# A workflow run is made up of one or more jobs that can run sequentially or in parallel
jobs:
  build:
   # The type of runner that the job will run on
    runs-on: ubuntu-latest
    # This first step does a sanity check by creating a bucket
    steps:
      - name: Upload to S3
        run: aws s3 mb s3://testbucket
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: 'us-east-1'
    # This second step runs the stack which will create the lambda function,make sure you have saved your script in a s3 bucket
    # and change the link of the file as per your need
      - name: Create the lambda function and run python script
        run: aws cloudformation create-stack --stack-name lambda2 --capabilities CAPABILITY_IAM --template-url "https://activestatebucket.s3.amazonaws.com/snapshot_lambda.yml"
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: 'us-east-1'
     # This third step ensure that the previous stack is completed, before the lambda function can be trigerred        
      - name: This will ensure, the previous stack is complete before we trigger the lambda functioon
        run: aws cloudformation wait stack-create-complete --stack-name lambda2
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: 'us-east-1'
      
      # This fourth step ensure that the lambda function is triggered and given 30 seconds to finish   
      
      - name: This will ensure, the previous stack is complete before we trigger the lambda functioon
        run: aws lambda invoke --function-name ActiveStateGetRdsSnapshotLambda2 response.json
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: 'us-east-1'
          
      - name: This will wait for the lambda to trigger and make the necessary changes before the next stack is run
        run: sleep 30
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: 'us-east-1'

      # This final step ensure we run the final ephemeral environment stack with latest snapshot ids
      - name: Running the final.yaml script that contains the rest of the ephimeral enviroment scripts
        run: aws cloudformation create-stack --stack-name activestateephimeral --capabilities CAPABILITY_IAM --template-url "https://activestatebucket.s3.amazonaws.com/final.yaml"
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: 'us-east-1'
```
