from rag_engine import build_knowledge_base, retrieve_context

# Build the knowledge base first
build_knowledge_base()

# Test retrieval
query = "What does high WBC count mean?"
context = retrieve_context(query)
print("Query:", query)
print("Retrieved context:")
print(context)