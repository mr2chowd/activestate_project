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
