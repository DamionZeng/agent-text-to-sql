import os
from langchain.chat_models import init_chat_model
from app.conf.app_config import conf

llm = init_chat_model(
    model= conf.llm.model_name,
    model_provider= "openai",
    api_key= os.getenv(conf.llm.api_key),
    base_url = conf.llm.base_url,
    temperature=0,
)

if __name__ == '__main__':
    print(llm.invoke("你好，你是谁").content)