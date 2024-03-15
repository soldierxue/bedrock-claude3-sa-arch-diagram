# Import libraries
import PIL
from PIL import PngImagePlugin
import streamlit as st

import sa_arch_diagram_lib as sadlib

if 'pehistory' not in st.session_state:
    st.session_state['pehistory'] = []
if 'isNewImage' not in st.session_state:
    st.session_state['isNewImage'] = False


st.set_page_config (layout="wide")

# @st.cache_resource
def load_tool():
    """
    Load the tool

    Returns:
        CloudDiagramTool (): The object of the tool

    """
    return sadlib.CloudDiagramTool()


def sidebar() -> None:
    """
    Purpose:
        Shows the side bar
    Args:
        N/A
    Returns:
        N/A
    """

    st.sidebar.image(
        "https://d1.awsstatic.com/gamedev/Programs/OnRamp/gt-well-architected.4234ac16be6435d0ddd4ca693ea08106bc33de9f.png",
        use_column_width=True,
    )

    st.sidebar.markdown(
        "Claude3 能否帮助架构师生成架构图？"
    )
    
    st.sidebar.selectbox(label="",options=["Sonnet","Haiku"],key="claude3_option")


def app() -> None:

    # Spin up the sidebar
    sidebar()
    tool = load_tool()
    colPEInput,colResult = st.columns(2)
    with colPEInput:
        st.subheader("输入架构图提示词：")
        pe_samples = ["The following diagram shows a Lambda function that reads objects from an S3 bucket in parallel. The diagram also has a Step Functions workflow for the AWS Lambda Power Tuning tool to fine-tune the Lambda function memory. This fine-tuning helps to achieve a good balance between cost and performance.","The diagram shows the following workflow: Data is ingested using Amazon API Gateway as a proxy for DynamoDB. You can also use any other source to ingest data into DynamoDB. Item-level changes are generated in near-real time in Kinesis Data Streams for delivery to Amazon S3.Kinesis Data Streams sends the records to Firehose for transformation and delivery. A Lambda function converts the records from a DynamoDB record format to JSON format, which contains only the record item attribute names and values.","This diagram shows how to build a modern serverless mobile web application in AWS for mobile or web clients, using AWS AppSync for frontend and ECS Fargate containers for backend application, along with Continuous Integration and Delivery and analytics to derive insight from application logs and structured data using the Amazon QuickSight dashboard"]
    
        st.selectbox(label="参考提示词：", options=pe_samples, key="pe_input")

        query = st.text_area(label="请描述你要生成的架构图:",height=250,key="peinput",value=st.session_state.pe_input)

        go_button = st.button("提交", type="primary")

        st.subheader("历史提示词：")

    with colResult:
        st.subheader("结果输出")
        # 输出提示词历史记录，如果有
        pe_statements = []
        for pehistoryobj in st.session_state.pehistory:
            pe_statements.append(pehistoryobj["pe"])
        colPEInput.table(pe_statements)
        # 提交并生成架构图
        if go_button:
            with st.spinner("工作中..."):
                result = tool.run(query,st.session_state.claude3_option)
                if type(result) == PngImagePlugin.PngImageFile:
                    st.image(image=result)
                    st.session_state.isNewImage = True
                else:
                    st.write(result)
                
                st.code(tool.generated_code)
    
    if st.session_state.isNewImage:
        st.session_state['pehistory'].append({"file_name":tool.get_diagram_filename(),"image":result,"pe":query})        
        st.session_state.isNewImage = False


def main() -> None:
    # Start the streamlit app
    st.title("Claude3 能否帮助架构师生成架构图？")

    app()


if __name__ == "__main__":
    main()
