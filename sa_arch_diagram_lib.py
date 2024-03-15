import warnings
warnings.filterwarnings('ignore')

import json
import os
import sys
import subprocess

import boto3
# from typing import Dict

import requests
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.prompts.prompt import PromptTemplate
from PIL import Image
# from transformers import Tool

class CloudDiagramTool():
    name = "CloudDiagramTool"
    generated_code = ""
    error_msg = ""
    image_path = "./images/"
    image_filename = "demo.png"
    claude3_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    def save_and_run_python_code(self):
        # Save the code to a file
        script_file_name = self.image_filename+".py"
        with open(self.image_path+script_file_name, "w") as file:
            file.write(self.generated_code)

        # Run the code using a subprocess
        try:
            result = subprocess.run(
                ["python39", self.image_path+script_file_name], capture_output=True, text=True, check=True
            )
            self.error_msg = ""
        except subprocess.CalledProcessError as e:
            print("Error occurred while running the code:")
            print(e.stdout)
            print(e.stderr)
            self.error_msg = e.stdout+e.stderr

    
    def process_code(self, code):
        # Split the code into lines
        lines = code.split("\n")
        # print(code)
        # Initialize variables to store the updated code and diagram filename
        updated_lines = []
        diagram_filename = None
        inside_diagram_block = False

        for line in lines:
            
            if  "<code>" in line:
                line = ""
                inside_diagram_block = True                
            if  "</code>" in line:
                line = ""
                inside_diagram_block = False

            # Check if the line contains "with Diagram("
            if "with Diagram(" in line:
                # Extract the diagram name between "with Diagram('NAME',"
                diagram_name = (
                    line.split("with Diagram(")[1].split(",")[0].strip("'").strip("\"\):")
                )

                # Convert the diagram name to lowercase, replace spaces with underscores, and add ".png" extension
                diagram_filename = diagram_name.lower().replace(" ", "_").replace("/","_") + ".png"

                # Check if the line contains "filename="
                if "filename=" in line:
                    # Extract the filename from the "filename=" parameter
                    diagram_filename = (
                        line.split("filename=")[1].split(")")[0].strip("'").strip('"')
                        + ".png"
                    )

            if inside_diagram_block:
                updated_lines.append(line)

        # Join the updated lines to create the updated code
        updated_code = "\n".join(updated_lines)

        self.generated_code = updated_code
        self.image_filename = diagram_filename
    
    def call_bedrock(self,payload):
        # modelId = 'anthropic.claude-3-sonnet-20240229-v1:0'
        accept = 'application/json'
        contentType = 'application/json'
        
        query = payload
        
        prompt_data = f"""
        Write an executable Python code according to user's input <query> using Diagrams library following the <instructions>.
        <query>{query}</query> 
        <instructions>
           1. Please place the generated Python code only in <code></code> and other information into <explain></explain>
           2. Double check the generated code, fix error of 'Diagram' or 'Cluster' is not defined by importing Diagram and Cluster from diagrams
           3. SQSQueue should be replaced by SQS or SimpleQueueServiceSqsQueue in the generated code and imported from diagrams.aws.integration
           4. DynamoDB should be replaced by Dynamodb in the generated code
           5. For APIGateway please import it from diagrams.aws.mobile instead of diagrams.aws
           6. CloudwatchEventEventBridge should be replaced by CloudwatchEventEventBased and Eventbridge
           7. diagrams.aws.databases should be diagrams.aws.database in the generated code
           8. EventBridge should be replaced by Eventbridge in the generated code,imported from diagrams.aws.integration
           9. ECSService should be replaced by ECS in the generated code
           10. FargateCluster should be replaced by Fargate in the generated code
           11. QuickSight should be replaced by Quicksight in the generated code
           12. ECRRegistry should be replaced by ECR in the generated code and it should be imported from diagrams.aws.compute
           13. all objects begin with Code should be imported from diagrams.aws.devtools
           14. CloudwatchLogs should be  replaced by Cloudwatch in the generated code and imported from diagrams.aws.management
           15. Codepipeline, Codebuild, Codedeploy or Codecommit could be imported from diagrams.aws.devtools
           16. Amplify, APIGateway, Appsync, DeviceFarm, Mobile or Pinpoint could be imported from diagrams.aws.mobile
           17. objects begin with Cloudwatch should be imported from diagrams.aws.management
           18. the parameter show of Diagram should be True instead of False and Diagram
           19. for clients you can import MobileClient, Client, User or Users from diagrams.aws.general
           20. KinesisFirehose, KinesisStreams should be replaced by KinesisDataFirehose and KinesisDataStreams
           21. Lambda should be imported from diagrams.aws.compute
           22. objects begin with Kinesis should be imported from diagrams.aws.analytics
           23. EventBridge should be replaced by Eventbridge in the generated code
           24. CodePipeline should be Codepipeline, CodeBuild should be Codebuild, CodeDeploy should be Codedeploy, CodeCommit should be Codecommit
           25. You can import StepFunctions from diagrams.aws.integration
           26. Quicksight should be imported from diagrams.aws.analytics
        </instructions>
        
        """
        systemPrompt = """
                你是一名亚马逊 AWS 认证的专家架构师，你的角色是帮助客户应用云上最佳实践，你将利用工具生成代码、架构图以及架构图的解释说明；
        """
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.9,
            "system" : systemPrompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_data
                        }
                    ],
                }
            ],
        } 
        jsonBody = json.dumps(body)
        # print(jsonBody)

        session = boto3.Session()
        bedrock = session.client(service_name='bedrock-runtime') #creates a Bedrock client    

        response = bedrock.invoke_model(body=jsonBody, modelId=self.claude3_model_id, accept=accept, contentType=contentType)
        response_body = json.loads(response.get('body').read()) # read the response
    
        code = response_body['content'][0]['text']
        
        return code  
    
    def get_diagram_filename(self):
        return self.image_path+ self.image_filename   
    
    def run(self,query,claude3_option = "Sonnet"):
        if claude3_option == "Sonnet":
            self.claude3_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        elif claude3_option == "Haiku":
            self.claude3_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        
        bedrockResponse = self.call_bedrock(query)
            
        # Clean up hallucinated code
        self.process_code(bedrockResponse)
        self.generated_code = self.generated_code.replace("```python","").replace("```","").replace('"""',"")
        
        try:
            # Code to run
            self.save_and_run_python_code()
            if os.path.exists(self.image_filename):
                imgage_bytes = Image.open(self.image_filename)
                subprocess.call(["mv",self.image_filename,self.image_path])
                return imgage_bytes
        except Exception as e:
            print("Error - "+e)
            self.error_msg = self.error_msg + e.__str__
        
        return self.error_msg
    


