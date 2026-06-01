"""Main Streamlit application for chatbot ordering system - Local LLM Version"""

import streamlit as st
from backend.menu_loader import MenuLoader
from backend.order_processor import OrderProcessor

# Import with error handling for different langchain versions
try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    try:
        from langchain_community.llms import Ollama as ChatOllama
        OLLAMA_AVAILABLE = True
    except ImportError:
        OLLAMA_AVAILABLE = False

# Import RAG pipeline with error handling
try:
    from rag.embedding_pipeline import RAGPipeline
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="CafeBot - Local AI",
    page_icon="☕",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "order_processor" not in st.session_state:
    st.session_state.order_processor = OrderProcessor()
if "menu_loader" not in st.session_state:
    st.session_state.menu_loader = MenuLoader()
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None
if "llm" not in st.session_state:
    st.session_state.llm = None

# Helper function to extract text from LLM response
def extract_response_text(response):
    """Extract just the text content from various response types"""
    if hasattr(response, 'content'):
        # AIMessage object
        return response.content
    elif isinstance(response, str):
        # Already a string
        return response
    else:
        # Fallback
        return str(response)

# Sidebar
with st.sidebar:
    st.title("☕ CafeBot")
    st.markdown("---")
    
    # Ollama configuration
    st.subheader("🤖 Local LLM Setup")
    
    if not OLLAMA_AVAILABLE:
        st.error("LangChain Ollama not installed. Run: pip install langchain-ollama")
    
    model_name = st.selectbox(
        "Select Model",
        ["llama3.2:1b", "llama3.2:3b", "mistral", "phi3:mini", "tinyllama"],
        help="Smaller models are faster but less capable. Run 'ollama list' to see installed models."
    )
    
    ollama_host = st.text_input(
        "Ollama Host",
        value="http://localhost:11434",
        help="Default Ollama server address"
    )
    
    temperature = st.slider(
        "Temperature (Creativity)",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Higher = more creative, Lower = more focused"
    )
    
    if st.button("🚀 Initialize AI Model", type="primary"):
        if not OLLAMA_AVAILABLE:
            st.error("Cannot initialize: langchain-ollama not installed")
        else:
            with st.spinner(f"Connecting to {model_name}..."):
                try:
                    # Try different import patterns
                    try:
                        from langchain_ollama import ChatOllama
                        llm = ChatOllama(
                            model=model_name,
                            base_url=ollama_host,
                            temperature=temperature
                        )
                    except:
                        from langchain_community.llms import Ollama as ChatOllama
                        llm = ChatOllama(
                            model=model_name,
                            base_url=ollama_host,
                            temperature=temperature
                        )
                    
                    # Test connection
                    test_response = llm.invoke("Say 'Ready!'")
                    test_text = extract_response_text(test_response)
                    
                    st.session_state.llm = llm
                    
                    if RAG_AVAILABLE:
                        st.session_state.rag_pipeline = RAGPipeline(
                            llm, 
                            st.session_state.menu_loader
                        )
                    st.success(f"✅ Connected to {model_name}!")
                    st.success("✅ AI Ready!")
                except Exception as e:
                    st.error(f"Failed to connect: {str(e)}")
                    st.info(f"Make sure Ollama is running and the model is downloaded: ollama pull {model_name}")
    
    if st.session_state.llm:
        st.info(f"✅ Active Model: {model_name}")
    
    st.markdown("---")
    
    # Display current order
    st.subheader("🛒 Current Order")
    if st.session_state.order_processor.current_order:
        order_summary = st.session_state.order_processor.get_current_order_summary()
        st.text(order_summary)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Clear Order"):
                st.session_state.order_processor.current_order = None
                st.rerun()
        with col2:
            if st.button("✅ Confirm Order"):
                customer_name = st.text_input("Your name (optional)", key="customer_name")
                result = st.session_state.order_processor.confirm_order(
                    customer_name if customer_name else None
                )
                if result["success"]:
                    st.success(result["message"])
                    st.balloons()
                    st.rerun()
    else:
        st.info("No active order. Start chatting to order!")
    
    st.markdown("---")
    
    with st.expander("📋 View Full Menu"):
        menu_preview = st.session_state.menu_loader.format_menu_for_display()
        st.text(menu_preview)
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
st.title("☕ Welcome to CafeBot! (Local AI)")
st.caption("Your AI assistant powered by local LLM - completely private and free")

# Display chat messages with proper formatting
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Format the content for better readability
        content = message["content"]
        
        # Replace newlines with line breaks for better display
        content = content.replace("\n", "\n\n")
        
        # Display with markdown formatting
        st.markdown(content)
        
        if "order_summary" in message and message["order_summary"]:
            with st.expander("📋 View Order Details"):
                st.text(message["order_summary"])

# Chat input
if prompt := st.chat_input("What would you like to order?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if st.session_state.rag_pipeline and st.session_state.llm:
                try:
                    # Use RAG pipeline for intelligent response
                    response_obj = st.session_state.rag_pipeline.query(prompt)
                    response = extract_response_text(response_obj)
                    
                    # Check if we need to add items to order
                    extraction = st.session_state.order_processor.extract_order_from_message(
                        prompt, 
                        st.session_state.menu_loader
                    )
                    
                    if extraction["items"]:
                        for item in extraction["items"]:
                            st.session_state.order_processor.add_to_order(
                                item["name"],
                                item["quantity"],
                                price=item["price"]
                            )
                        response += "\n\n" + st.session_state.order_processor.get_current_order_summary()
                    
                except Exception as e:
                    response = f"Sorry, I encountered an error: {str(e)}"
            elif st.session_state.llm:
                # Use simple LLM without RAG
                try:
                    response_obj = st.session_state.llm.invoke(prompt)
                    response = extract_response_text(response_obj)
                except Exception as e:
                    response = f"Error: {str(e)}"
            else:
                response = "Please click 'Initialize AI Model' in the sidebar to start ordering!"
        
        # Format and display the response
        formatted_response = response.replace("\n", "\n\n")
        st.markdown(formatted_response)
        
        # Add assistant message
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "order_summary": st.session_state.order_processor.get_current_order_summary() if st.session_state.order_processor.current_order else None
        })

# Footer
st.markdown("---")
st.caption("💡 Tip: Make sure Ollama is running locally. Download models with: ollama pull llama3.2:1b")