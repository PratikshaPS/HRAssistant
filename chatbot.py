from llama_parse import LlamaParse
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from groq import Groq
from langchain_groq import ChatGroq
import joblib
import os
import nest_asyncio  # noqa: E402
nest_asyncio.apply()
from langchain.chat_models import ChatOpenAI
import chardet
from dotenv import load_dotenv
import streamlit as st
from htmlTemplates import css, bot_template, user_template
from langchain_community.embeddings import OpenAIEmbeddings

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

llamaparse_api_key = os.environ.get('LLAMA_CLOUD_API_KEY')
openai_api_key = os.environ.get("OPENAI_API_KEY")

def load_or_parse_data():
    data_file = "./data/parsed_data.pkl"

    if os.path.exists(data_file):
        print("loading the data")
        # Load the parsed data from the file
        parsed_data = joblib.load(data_file)
    else:
        print("I'm in else")
        # Perform the parsing step and store the result in llama_parse_documents
        parsingInstructionUber10k = """The provided document is a HR policies
        of an organization.
        Try to be precise while answering the questions"""

        parser = LlamaParse(api_key=llamaparse_api_key,
                            result_type="markdown",
                            parsing_instruction=parsingInstructionUber10k,
                            max_timeout=5000,)
        llama_parse_documents = parser.load_data("./data/HR_Policy_Manual_KFSLnew.pdf")

        # Save the parsed data to a file
        print("Saving the parse results in .pkl format ..........")
        joblib.dump(llama_parse_documents, data_file)

        # Set the parsed data to the variable
        parsed_data = llama_parse_documents

    return parsed_data

def convert_to_utf8(file_path):

    with open(file_path, 'rb') as f:
        raw_data = f.read()

    # Detect file encoding using chardet
    result = chardet.detect(raw_data)
    encoding = result['encoding'] or 'utf-8'  # Default to utf-8 if detection fails

    print(f"Detected encoding: {encoding}")

    # Decode using the detected encoding and re-encode as utf-8
    text = raw_data.decode(encoding)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"File converted to UTF-8 successfully: {file_path}")



def create_vector_database():

    # Call the function to either load or parse the data
    llama_parse_documents = load_or_parse_data()

    print("function called")

    with open('data/output.md', 'a', encoding='utf-8', errors='ignore') as f:  # Open the file in append mode ('a')
        for doc in llama_parse_documents:
            f.write(doc.text + '\n')

    markdown_path = "./data/output.md"


    convert_to_utf8("data/output.md")
    print("utf conversion done")

    loader = UnstructuredMarkdownLoader(markdown_path)

   #loader = DirectoryLoader('data/', glob="**/*.md", show_progress=True)
    documents = loader.load()
    print("data loaded")

    # Split loaded documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)

    # Initialize Embeddings
    embed_model = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    # embed_model = OpenAIEmbeddings(model="bert-base-nli-mean-tokens")

    print("embeddings initiated")

    # Create and persist a Chroma vector database from the chunked documents
    # vs = Chroma.from_documents(
    #     documents=docs,
    #     embedding=embed_model,
    #     persist_directory="chroma_db_llamaparse1",  # Local mode with in-memory storage only
    #     collection_name="rag"
    # )

    # vs = FAISS.from_documents(documents=docs, embedding=embed_model)

    print('FAISS Vector DB created successfully !')
    return embed_model

def instantiate_vectordb(embed_model):

    print("loading vector model")
    
    vectorstore = Chroma(embedding_function=embed_model,
                        persist_directory="chroma_db_llamaparse1",
                        collection_name="rag")
    
    print("vector model loaded")

    retriever=vectorstore.as_retriever(search_kwargs={'k': 3})
    return retriever

def set_custom_prompt():

    custom_prompt_template = """Use the following pieces of information to answer the user's question.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    Context: {context}
    Question: {question}

    Only return the helpful answer below in a complete sentence and nothing else.
    format the answers in bullets wherever required and prettify the text. Mention all the nested points that are truly required.
    Helpful answer:
    """

    prompt = PromptTemplate(
        template=custom_prompt_template,
        input_variables=['context', 'question'])
    
    return prompt

def get_conversation_chain(prompt, retriever):

    llm = ChatOpenAI(
        model_name = 'gpt-3.5-turbo',
        temperature = 0
        )

    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

    conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            combine_docs_chain_kwargs={'prompt':prompt}
        )
    
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']
    # st.write(response['answer'])
    
    for i, message in enumerate(st.session_state.chat_history):
        msg_content = message.content.replace("\n","<br/>")
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", msg_content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", msg_content), unsafe_allow_html=True)

def main():
    load_dotenv()

    st.set_page_config(page_title="HR Assistant",page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    # st.subheader("HR Assistant :books:")

    # if "conversation" not in st.session_state:
    #     st.session_state.conversation = None
    # if "chat_history" not in st.session_state:
    #     st.session_state.chat_history = None
    # if "load_embeddings" not in st.session_state:
    #     st.session_state.load_embeddings = None



    # if st.session_state.load_embeddings is None:
    #     print("I'm here --------------------------------------------------------------------------------")
    #     print("embeddings ", st.session_state.load_embeddings)
    #     st.session_state.load_embeddings = "Loaded"

    #     prompt = set_custom_prompt()
    #     vs,embed_model = create_vector_database()
    #     retriever = instantiate_vectordb(embed_model)

    #     st.session_state.conversation = get_conversation_chain(prompt, retriever)
    #     st.write(st.session_state.conversation)

    # user_question = st.chat_input("Ask anything here:")
    # if user_question:
    #     handle_userinput(user_question)

    # Initialize Streamlit application
    # st.set_page_config(page_title="Conversational Chatbot", page_icon="🤖")

    # st.title("HR Policy Chatbot 🤖")
    # st.write("Ask any question related to HR policies, and I'll provide a helpful answer!")
    print("write done")
    
    # Text input for user queries
    

    # conversation = None
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    if "load_embeddings" not in st.session_state:
        st.session_state.load_embeddings = None

    user_input = st.chat_input("Ask anything here:")

    if user_input:
        print(st.session_state.conversation)
        print(st.session_state.load_embeddings)

        handle_userinput(user_input)
        # response = st.session_state.conversation({"question": user_input})
        # st.write(response['answer'])
        
        print("----------------------------------------------")
        print(st.session_state.conversation)


    if st.session_state.load_embeddings is None:
        
        print(st.session_state.load_embeddings)

        # Create the vector database and retriever
        embed_model = create_vector_database()
        retriever = instantiate_vectordb(embed_model)

        st.session_state.load_embeddings = "loaded"

        # Set up prompt and conversation chain
        custom_prompt = set_custom_prompt()
        st.session_state.conversation = get_conversation_chain(custom_prompt, retriever)

        print(st.session_state.conversation)


if __name__ == '__main__':
    main()
