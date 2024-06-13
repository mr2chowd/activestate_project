# ActiveState Ephemeral Environment Project 

### Problem Scenario: 
The developers I support will need to replicate the production environment to test their code and  data changes. 
This includes running applications and services as well as accessing data that represents real systems. 
Since code and data changes may conflict with each other, we would like to provide unique and ephemeral environments, 
rather than testing everything in a single, shared staging or testing environment. Our task is to design processes and tooling to: 

    1) Replicate the production environment 
    2) In a repeatable way
    3) With minimal effort from developers to request this environment

Since automation is better than manual work. The less effort required for a developer to request such an environment, the better.

Therefore, to simplify the task we may assume: 

    1.) All of the developers in the team uses Git and Github 
    2.) The process for requestng a new environment can be tied to GitHub pull requests 
    3.) We have an existing CI-CD pipeline. 

### Benefits of Ephemeral Environment : 
An ephemeral environment is a temporary short-lived environment that helps developer test their 
new changes of the application in an environment that is a replica of the production environment. It could have many services and databases that is an exact copy of the production so that when the final code is deployed to the production, the chances of having deployment bugs are as low as possible. Ephemeral environments provide robust, on-demand platforms for running tests, previewing features, and collaborating asynchronously across teams.

### Some prerequisites to deploy this project:

1. You need to have access to the [git account](https://github.com/mr2chowd/activestate_assignment.git) and have knowledge of the basic git commands to do a pull request and cloning the repo.
2. You need to have access to the private s3 buckets where the stacks are saved to be run from the git workflow
3. An AWS account. Note that running this stack will incur cost and there are some expensive services used. Run with caution.
4. AWS Command Line Interface

### Design Summary:

To simplify the design we assumed the developers 
are working on a simple static website where it has prebuilt CI-CD 
pipeline which they uses to deploy their applications. 
We are going to give them an ephemeral environment where all that they 
need to do is create a pull request to the repo and the environment will 
be created for them in less than 15 minutes. Once they are done with the 
environment, all that needs to be done is close the pull request which
will delete all the services leaving no traces of ephemeral environment 
that it ever existed. The following resources will be created to make the environment replicate the production environment : 
    <br>
1. A new VPC will be created to host the new servers and databases
2. Two private subnets will be created to host the database
3. Two public subnets will be created for the web front end to be hosted
4. Internet Gateway will be attached to the VPC for outside connectivity
5. NatGateway will be provided so that private subnet also has indirect connection to the do any kinds of updates and downloads from the internet in a secure way
6. Route tables will be created to ensure proper routing and subnet associations
7. Proper IAM roles are provided in the stacks for the Lambda functions as well as EC2 instances where the websites will be hosted 
8. Security groups will be provided for Bastion Server as well as the EC2 instances where the webserver will be hosted 
9. Auto Scaling Groups will be created so that when the CPU utilizations reach a certain threshold, new instances will be created to cope up with the increased request and traffic 
10. Launch Template will be provided for resuability and version controlling of type of EC2 instances that needs to be scaled 
11. Load Balancers will be created to equally divided the load of the web application to different servers on different Availabilty Zone 
12. RDS will be provided with the latest database files so that the environment can have the upto date data when tests are done. 
13. Lambda functions will be created to attain the latest database copy snapshot and change the ephemeral stack with latest arn so that the whole process is completely automated 
14. Disaster recovery backup instances are created for the database in situations of lag in read operations 
15. A Bastion Server is created to reach the database with secure connection
16. SNS Topics are created to alert the Devops Engineer in case of any problems for the web server.

### Design Checks:
All the codes will be given at the end and not in the steps to ensure readability.

Basic steps are below: 

1.  Save the "create_ephemeral.yml" [file](#script-1) and "delete_ephemeral.yml" [file](#script-2) codes in this directory ".github/workflows".  
2.  Update your Repository secrets:
    -  Navigate to your repository on github and select Settings > Secrets > New repository secret 
    -  AWS_ACCESS_KEY_ID - your aws account access key id
    -  AWS_SECRET_ACCESS_KEY - your secret access key
3.  Ensure the lambda stack is saved in the activestate s3 bucket
4.  All the python dependencies are saved inside the s3 bucket as python.zip.
5.  Ephemeralenv.yml [file](#Script-5) needs to be saved in the s3 bucket so that [python](#Script-3) can find this script and update with the latest arn values
6. To increase security, save your database credentials in the AWS Secrets Manager

## Commentary of the design flow:
The process starts with creating an empty git repository and cloning it. Then we can make a directory ".github/workflows" where we save the steps that will run when the pull request is executed. An active state bucket is also created where various stacks are saved for bash execution in github workflows.

The script "create_ephemeral.yml" ensure the stacks and lambda functions are run in an order because of the dependancies. It starts by doing a sanity check of creating a bucket then it executes the lambda [stack](#Script-4). Lambda [stack](#Script-4) creates the lambda function in aws cloudformation and it also contains the python [script](#Script-3) which grabs the productions database's latest data snapshot from aws and attaches it to the final ephemeral scripts arn field. 

Once the lambda [stack](#Script-4) is created, step-3 in the create_ephemeral.yml file executes where it runs a bash script which ensures that previous stack is created and fully completed.Then only step-4 is executed which invokes the lambda function. This sanity check is needed to ensure the lambda function is created fully before it can be executed.It also gives a buffer of 30 second which is more than enough for all the task to be completed.

The final execution completion of the lambda function ensures that the "ephemeralenv.yml" [stack](#Script-5) is good to go and latest database snapshot arn are inserted in the final.yaml stack.

Once the developer is done with the ephemeral environment, they can choose to close the pull request 
which will trigger the delete_ephemeral.yml [script](#script-2). It deletes all the stack that were created
in logical order of last created. Upon completion, the whole environment will cease to exist leaving no traces of its existence.

These following scripts were executed for the whole process to complete: 

### Script-1
### Create_ephemeral.yml 
```
# Create_ephemeral.yml Script Below:
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

### Script-2
### Delete_ephemeral.yml 
```
# This is a workflow which will delete the ephemeral environment for ActiveState Developers

name: Deploy

# Controls when the action will run. 
on:
  # Triggers the workflow on push or pull request events but only for the main branch
  pull_request:
    branches: [ main ]
    types: [ closed ]
  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

# A workflow run is made up of one or more jobs that can run sequentially or in parallel
jobs:

  # This workflow contains a multiples job under "build"
  build:

   # The type of runner that the job will run on
    runs-on: ubuntu-latest

    #Deletes the sanity test bucket
    steps:
      - name: Upload to S3
        run: aws s3 rb s3://testbucket
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: 'us-east-1'
    #Deletes the lambda function stack
      - name: Delete the lambda function stack
        run: aws cloudformation delete-stack --stack-name lambda2 
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: 'us-east-1'
    #Remove the final.yaml script    
      - name: Remove the final.yaml script
        run: aws s3 rm s3://activestatebucket/final.yaml
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: 'us-east-1'
    # Deletes each and every single last services present in the environment along with RDS     
      - name: Delete the final ephimeral stack
        run: aws cloudformation delete-stack --stack-name activestateephimeral 
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: 'us-east-1'        
```
### Script-3
### Rdssnapshot.py Python Script 

```
        import json
        import boto3
        import yaml
        import io
        from datetime import datetime, timezone
        resource_name = "RDSCluster"
        def lambda_handler(event, context):

            today = (datetime.today()).date()
            rds_client = boto3.client('rds')
            snapshots = rds_client.describe_db_cluster_snapshots(DBClusterIdentifier='database-1',MaxRecords=20)
            
            list=[]
            for x in snapshots['DBClusterSnapshots']:
                list.append(x['SnapshotCreateTime'])
            
            latestsnapshottime=max(list)
            
            for x in snapshots['DBClusterSnapshots']:
                if x['SnapshotCreateTime'] == latestsnapshottime:
                    arnname = x['DBClusterSnapshotArn']
                    response = {'result': arnname}
                    # return response
                    
            s3 = boto3.client('s3')
            s3.download_file('activestatebucket', 'ephemeralenv.yml','/tmp/ephemeralenv.yaml')

            with open("/tmp/ephemeralenv.yaml", "r") as stream:
                data = yaml.safe_load(stream) 
                # print(data)
                data['Resources']['RDSCluster']['Properties']['SnapshotIdentifier'] = arnname    

            
            with io.open('/tmp/final.yaml', 'w', encoding='utf8') as outfile:
                yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True, sort_keys=False)
                s3.upload_file("/tmp/final.yaml", "activestatebucket", "final.yaml")

```
### Script-4
### Snapshot_lambda Script 

```
AWSTemplateFormatVersion: "2010-09-09"
Description: ActiveState Lambda function to retrieve latest Snapshot from Production RDS

Resources:
  LambdaLayer:
    Type: "AWS::Lambda::LayerVersion"
    Properties:
      CompatibleRuntimes:
        - python3.9
      Content:
        S3Bucket: activestatebucket
        S3Key: python.zip
      LayerName: "activestatelayers"
  
  Function:
    Type: AWS::Lambda::Function
    Properties:
      Layers: 
        - !Ref LambdaLayer
      FunctionName: ActiveStateGetRdsSnapshotLambda2
      Handler: index.lambda_handler
      Runtime: python3.9
      Role: !GetAtt LambdaFunctionRole.Arn
      Timeout: 50
      Code:
        ZipFile: |
              import json
              import boto3
              import yaml
              import io
              from datetime import datetime, timezone
              resource_name = "RDSCluster"
              def lambda_handler(event, context):

                  today = (datetime.today()).date()
                  rds_client = boto3.client('rds')
                  snapshots = rds_client.describe_db_cluster_snapshots(DBClusterIdentifier='database-1',MaxRecords=20)
                  
                  list=[]
                  for x in snapshots['DBClusterSnapshots']:
                      list.append(x['SnapshotCreateTime'])
                  
                  latestsnapshottime=max(list)
                  
                  for x in snapshots['DBClusterSnapshots']:
                      if x['SnapshotCreateTime'] == latestsnapshottime:
                          arnname = x['DBClusterSnapshotArn']
                          response = {'result': arnname}
                          # return response
                          
                  s3 = boto3.client('s3')
                  s3.download_file('activestatebucket', 'ephemeralenv.yml','/tmp/ephemeralenv.yaml')

                  with open("/tmp/ephemeralenv.yaml", "r") as stream:
                      data = yaml.safe_load(stream) 
                      # print(data)
                      data['Resources']['RDSCluster']['Properties']['SnapshotIdentifier'] = arnname    

                  
                  with io.open('/tmp/final.yaml', 'w', encoding='utf8') as outfile:
                      yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True, sort_keys=False)
                      s3.upload_file("/tmp/final.yaml", "activestatebucket", "final.yaml")

  LambdaFunctionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - lambda.amazonaws.com
            Action:
              - sts:AssumeRole
      Path: "/"
      Policies:
        - PolicyName: GetRdsSnapshotLog
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                  - cloudwatch:GetMetricStatistics
                  - logs:DescribeLogStreams
                  - logs:GetLogEvents
                Resource: "*"
        - PolicyName: GetRdsSnapshotLambdaPower
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - rds:Describe*
                  - rds:ListTagsForResource
                  - ec2:DescribeAccountAttributes
                  - ec2:DescribeAvailabilityZones
                  - ec2:DescribeInternetGateways
                  - ec2:DescribeSecurityGroups
                  - ec2:DescribeSubnets
                  - ec2:DescribeVpcAttribute
                  - ec2:DescribeVpcs
                  - s3:*
                  - s3-object-lambda:*
                Resource: "*"

```
### Script-5
### Ephemeralenv.yml Script 
```
Parameters:
  RDSEngineVersion:
    Type: String
    Default: 13.6
    AllowedValues:
      - 13.3
      - 13.4
      - 13.5
      - 13.6
      - 13.7
  EnvironmentName:
    Description: Ephemeral Environment
    Type: String
    Default: ActiveStateEphemeral

  KeyPairName:
    Type: AWS::EC2::KeyPair::KeyName
    Default: fouronekey2
    Description: The name of Key pair in parameter file to make SSH connection. Remember, Key should be available in your account.

  InstanceType:
    Type: String
    Default: t2.micro
    AllowedValues:
      - t2.micro    # free tier
      - t2.medium   # $0.0464/hour
      - t2.large    # $0.0928/hour
      - a1.medium   # $0.0255/hour
      - m6a.large   # $0.0864/hour
      - t4g.medium  # $0.0336/hour
    Description: Enter Instance type which is appropriate for you. As it is a exercise, I have used t2.micro.

  ImageId:
    Type: String
    Default: ami-05fa00d4c63e32376
    AllowedValues:
      - ami-05fa00d4c63e32376  # free tier
      - ami-02538f8925e3aa27a  # free tier
    Description: Enter Image ID of Amazon Linux 2 type instances

  VpcCIDR:
    Description: Please enter the IP range (CIDR notation) for this VPC
    Type: String
    Default: 10.192.0.0/16

  PublicSubnet1CIDR:
    Description: Please enter the IP range (CIDR notation) for the public subnet-1 in the first Availability Zone
    Type: String
    Default: 10.192.0.0/24

  PublicSubnet2CIDR:
    Description: Please enter the IP range (CIDR notation) for the public subnet-2 in the second Availability Zone
    Type: String
    Default: 10.192.1.0/24

  PrivateSubnet1CIDR:
    Description: Please enter the IP range (CIDR notation) for the private subnet-1 in the first Availability Zone
    Type: String
    Default: 10.192.2.0/24

  PrivateSubnet2CIDR:
    Description: Please enter the IP range (CIDR notation) for the private subnet-1 in the first Availability Zone
    Type: String
    Default: 10.192.3.0/24

Resources:
  ActiveStateVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 
        Ref: VpcCIDR
      Tags:
        - Key: Name
          Value: ActiveStateEphVPC

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      MapPublicIpOnLaunch: true
      AvailabilityZone: us-east-1a
      VpcId: 
        Ref: ActiveStateVPC
      CidrBlock: 
        Ref: PublicSubnet1CIDR
      Tags:
        - Key: Name
          Value: PublicSubnet1

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      AvailabilityZone: us-east-1b
      VpcId: 
        Ref: ActiveStateVPC
      CidrBlock: 
        Ref: PublicSubnet2CIDR
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: PublicSubnet2

  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      AvailabilityZone: us-east-1a
      VpcId: 
        Ref: ActiveStateVPC
      CidrBlock: 
        Ref: PrivateSubnet1CIDR
      Tags:
        - Key: Name
          Value: PrivateSubnet1

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      AvailabilityZone: us-east-1b
      VpcId: 
        Ref: ActiveStateVPC
      CidrBlock: 
        Ref: PrivateSubnet2CIDR
      Tags:
        - Key: Name
          Value: PrivateSubnet2

  InternetGateway1:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: User
          Value: mr2chowd

  InternetGatewayVPCAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: 
        Ref: ActiveStateVPC
      InternetGatewayId: 
        Fn::GetAtt: [InternetGateway1,InternetGatewayId]

  RouteTable1:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: 
        Ref: ActiveStateVPC

  PublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: 
        Ref: RouteTable1
      SubnetId: 
        Ref: PublicSubnet1

  PublicSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: 
        Ref: RouteTable1
      SubnetId: 
        Ref: PublicSubnet2

  InternetGatewayRoute:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: 
        Ref: RouteTable1
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: 
        Fn::GetAtt: [InternetGateway1,InternetGatewayId]

  NatGatewayEIP1:
    Type: AWS::EC2::EIP
    Properties:
      Domain: 
        Ref: ActiveStateVPC

  NateGateWay1:
    Type: AWS::EC2::NatGateway
    Properties:
      SubnetId: 
        Ref: PublicSubnet1
      AllocationId: 
        Fn::GetAtt: [NatGatewayEIP1,AllocationId]

  PrivateRouteTable1:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: 
        Ref: ActiveStateVPC

  PrivateSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: 
        Ref: PrivateRouteTable1
      SubnetId: 
        Ref: PrivateSubnet1

  PrivateSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      RouteTableId: 
        Ref: PrivateRouteTable1
      SubnetId: 
        Ref: PrivateSubnet2

  DefaultPrivateRoute1:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: 
        Ref: PrivateRouteTable1
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: 
        Ref: NateGateWay1

  IamRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - ec2.amazonaws.com
            Action:
              - sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforAWSCodeDeploy

  ProfileForEC2:
    Type: AWS::IAM::InstanceProfile
    Properties:
      InstanceProfileName: ProfileForEC2
      Roles:
        - Ref: IamRole

  AsgSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupName: AsgTraffic
      GroupDescription: Enable HTTP and SSH access on the inbound port for Asg
      VpcId: 
        Ref: ActiveStateVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 10.192.0.0/16
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 70.55.80.174/32
      Tags:
        - Key: Name
          Value: AsgSecurityGroup

  AsgLaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName:  ActiveStateLaunchTemplate
      LaunchTemplateData:
        NetworkInterfaces:
          - DeviceIndex: 0
            AssociatePublicIpAddress: true
            Groups:
              - Ref: AsgSecurityGroup
        InstanceType: 
          Ref: InstanceType
        KeyName: 
          Ref: KeyPairName
        ImageId: 
          Ref: ImageId
        IamInstanceProfile:
          Arn: 
            Fn::GetAtt: [ProfileForEC2,Arn]
        Monitoring:
          Enabled: True
        UserData:
          Fn::Base64:
            Fn::Sub: |
              #!/bin/bash
              sudo yum update -y
              sudo yum install -y httpd
              sudo yum install -y wget
              cd /var/www/html
              wget https://activestatebucket.s3.amazonaws.com/index.html
              sudo service httpd start
              sudo yum install ruby -y
              sudo yum install aws-cli -y
              cd /home/ec2-user
              wget https://aws-codedeploy-us-east-1.s3.us-east-1.amazonaws.com/latest/install
              sudo chmod +x ./install
              sudo ./install auto

  WebserverGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    DependsOn:
      - ELBTargetGroup
      - ElasticLoadBalancer
    Properties:
      VPCZoneIdentifier:
        - Ref: PublicSubnet1
        - Ref: PublicSubnet2
      LaunchTemplate:
        LaunchTemplateId: 
          Ref: AsgLaunchTemplate
        Version: 
          Fn::GetAtt: [AsgLaunchTemplate,LatestVersionNumber]
      MinSize: 2
      MaxSize: 5
      DesiredCapacity: 2
      HealthCheckGracePeriod: 300
      MaxInstanceLifetime: 2592000
      TargetGroupARNs:
        - Ref: ELBTargetGroup
      NotificationConfigurations:
        - NotificationTypes:
            - autoscaling:EC2_INSTANCE_LAUNCH
            - autoscaling:EC2_INSTANCE_LAUNCH_ERROR
            - autoscaling:EC2_INSTANCE_TERMINATE
            - autoscaling:EC2_INSTANCE_TERMINATE_ERROR
          TopicARN: 
            Ref: ActiveStateSNSTopic

  ScalingPolicy:
    Type: AWS::AutoScaling::ScalingPolicy
    Properties:
      AutoScalingGroupName: 
        Ref: WebserverGroup
      PolicyType: TargetTrackingScaling
      TargetTrackingConfiguration:
        PredefinedMetricSpecification:
          PredefinedMetricType: ASGAverageCPUUtilization
        TargetValue: 40

  ELBTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      HealthCheckIntervalSeconds: 6
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      Port: 80
      Protocol: HTTP
      UnhealthyThresholdCount: 2
      VpcId: 
        Ref: ActiveStateVPC
      TargetType: instance

  ELBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupName: ELBTraffic
      GroupDescription: Enable HTTP access on the inbound port for ELB
      VpcId: 
        Ref: ActiveStateVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Name
          Value: ELBSecurityGroup

  ElasticLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Subnets:
        - Ref: PublicSubnet1
        - Ref: PublicSubnet2
      SecurityGroups:
        - Ref: ELBSecurityGroup

  ElbListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: 
            Ref: ELBTargetGroup
      LoadBalancerArn: 
        Ref: ElasticLoadBalancer
      Port: 80
      Protocol: HTTP

  ActiveStateSNSTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: ActiveStateTopic

  MySubscription:
    Type: AWS::SNS::Subscription
    Properties:
      Endpoint: mr2chowd@uwaterloo.ca
      Protocol: email
      TopicArn: 
        Ref: ActiveStateSNSTopic

  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: DB Subnet Group for RDS
      DBSubnetGroupName: DB SubnetGroup
      SubnetIds:
        - Ref: PrivateSubnet1
        - Ref: PrivateSubnet2
  RDSCluster:
    Type: AWS::RDS::DBCluster
    Properties:
      SnapshotIdentifier: arn:heya
      Engine: aurora-postgresql
      DatabaseName: postgres
      AvailabilityZones:
        - us-east-1a
      Port: 5432
      DBClusterIdentifier: cluster2
      EngineVersion: 
        Ref: RDSEngineVersion
      # MasterUsername: "postgres"
      # MasterUserPassword: "postgres"
      MasterUsername: '{{resolve:secretsmanager:RDS/Aurora/ActiveState/Credentials:SecretString:Username}}'
      MasterUserPassword: '{{resolve:secretsmanager:RDS/Aurora/ActiveState/Credentials:SecretString:Password}}'
      DBSubnetGroupName: 
        Ref: DBSubnetGroup
      VpcSecurityGroupIds:
        - Fn::GetAtt: DBEC2SecurityGroup.GroupId

  RDSInstance1:
    Type: AWS::RDS::DBInstance
    Properties:
      DBClusterIdentifier: 
        Ref: RDSCluster
      DBInstanceClass: db.t4g.medium
      DBInstanceIdentifier: Writer1
      Engine: aurora-postgresql
      AvailabilityZone: us-east-1a
#      PubliclyAccessible: true

  RDSFallbackRescueInstance1:
    Type: AWS::RDS::DBInstance
    Properties:
      DBClusterIdentifier: 
        Ref: RDSCluster
      DBInstanceClass: db.t4g.medium
      DBInstanceIdentifier: Reader1
      Engine: aurora-postgresql
      AvailabilityZone: us-east-1a
#      PubliclyAccessible: true

  DBEC2SecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupName: RDSWebServerTraffic
      GroupDescription: Enable HTTP and SSH access on the inbound port for Asg
      VpcId: 
        Ref: ActiveStateVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: 
            Fn::GetAtt: [AsgSecurityGroup,GroupId]

  ActiveStateBastionServer:
    Type: AWS::EC2::Instance
    Properties:
      KeyName: fouronekey2
      SubnetId: 
        Ref: PublicSubnet1
      ImageId: 
        Ref: ImageId
      InstanceType:  
        Ref: InstanceType
      SecurityGroupIds:
        - Ref: SecurityGroup1
      Tags:
        - Key: "Name"
          Value: "ActiveStateBastionServer"
  SecurityGroup1:
    Type: AWS::EC2::SecurityGroup
    Description: Public Server Security Group
    Properties:
      GroupDescription: Allow ICMP and Tcp
      VpcId: 
        Ref: ActiveStateVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 70.55.80.174/24
        - IpProtocol: icmp
          FromPort: 8
          ToPort: -1
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
  PublicServerElasticIp:
    Type: AWS::EC2::EIP
    Properties:
      InstanceId: 
        Ref: ActiveStateBastionServer
      Tags:
        - Key: "Name"
          Value: "ActiveStateBastionServerElasticIp"
Outputs:
  VPCID:
    Description: A reference output to the created ActiveState VPC ID
    Value: 
      Ref: ActiveStateVPC
    Export:
      Name: ActiveState-vpc-id

  PublicSubnetId1:
    Description: Reference to the public subnet id 1
    Value: 
      Ref: PublicSubnet1
    Export:
      Name: ActiveState-publicsubnetid1

  PublicSubnetId2:
    Description: Reference to the public subnet id 2
    Value: 
      Ref: PublicSubnet2
    Export:
      Name: ActiveState-publicsubnetid2

  PrivateSubnet1:
    Description: A reference to the PRIVATE subnet in the 1st Availability Zone
    Value: 
      Ref: PrivateSubnet1
    Export:
      Name: ActiveState-privatesubnetid

  OutputELBTargetGroup:
    Description: A reference to the created Target Group
    Value: 
      Ref: ELBTargetGroup
  OutputELBSecurityGroup:
    Description: A reference to the created Security Group
    Value: 
      Ref: ELBSecurityGroup
  OutputElasticLoadBalancer:
    Description: A reference to the created Elastic Load Balancer
    Value: 
      Ref: ElasticLoadBalancer
  OutputElasticListener:
    Description: A reference to the created Elastic Load Balancer Listener
    Value: 
      Ref: ElbListener
  OutputAsgLaunchTemplate:
    Description: Id for autoscaling launch configuration
    Value: 
      Ref: AsgLaunchTemplate
  OutputAsgGroup:
    Description: Id for autoscaling group
    Value: 
      Ref: WebserverGroup
```
