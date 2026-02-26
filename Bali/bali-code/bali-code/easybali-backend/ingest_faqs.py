import asyncio
import hashlib
from app.services.google_sheets import get_workbook
from app.services.pinconeservice import get_index
from app.services.openai_client import client
from app.settings.config import settings

async def ingest_sheet(workbook, sheet_name, index_name, text_columns):
    """Generic function to ingest any sheet into a Pinecone index."""
    print(f"--- Ingesting {sheet_name} to index {index_name} ---")
    try:
        sheet = workbook.worksheet(sheet_name)
        data = sheet.get_all_values()
    except Exception as e:
        print(f"⚠️ Sheet '{sheet_name}' not found or error: {e}")
        return

    if len(data) <= 1:
        print(f"No data in {sheet_name}.")
        return

    headers = data[0]
    rows = data[1:]
    index = get_index(index_name)
    
    if not index:
        print(f"❌ Failed to reach Pinecone index: {index_name}")
        return

    vectors = []
    for i, row in enumerate(rows):
        # Create a text blob from specified columns
        text_parts = []
        for col in text_columns:
            if col in headers:
                val = row[headers.index(col)]
                if val: text_parts.append(f"{col}: {val}")
        
        text_content = "\n".join(text_parts)
        if not text_content.strip(): continue

        # Generate embedding
        try:
            embed_res = await client.embeddings.create(
                input=text_content,
                model="text-embedding-ada-002"
            )
            embedding = embed_res.data[0].embedding
            
            # Create a unique ID
            doc_id = hashlib.md5(text_content.encode()).hexdigest()
            
            vectors.append({
                "id": doc_id,
                "values": embedding,
                "metadata": {"text": text_content, "source": sheet_name}
            })
            
            # Batch upsert every 50 vectors
            if len(vectors) >= 50:
                index.upsert(vectors=vectors)
                print(f"Upserted 50 rows from {sheet_name}...")
                vectors = []
                
        except Exception as e:
            print(f"Error processing row {i} in {sheet_name}: {e}")

    # Final upsert
    if vectors:
        index.upsert(vectors=vectors)
        print(f"Upserted remaining {len(vectors)} rows from {sheet_name}.")

async def main():
    print("🚀 Starting RAG Data Ingestion Pipeline...")
    workbook_id = "1tuGBnQFjDntJQglofA17uHhiyekkVyDoSInErbwfR24"
    workbook = get_workbook(workbook_id)

    # 1. Villa FAQs
    await ingest_sheet(
        workbook, 
        "Villa FAQs", 
        "villa-faqs", 
        ["Villa Code", "Villa Name", "Question", "Answer"]
    )

    # 2. Local Cuisine (Guide)
    await ingest_sheet(
        workbook, 
        "Local Cuisine", 
        "local-cuisine", 
        ["Category", "Dish Name", "Description", "Warung Recommendation"]
    )

    # 3. Event Calendar
    await ingest_sheet(
        workbook, 
        "Event Calendar", 
        "event-calender", 
        ["Event Name", "Date", "Location", "Description", "Link"]
    )

    print("✅ Ingestion Pipeline Complete.")

if __name__ == "__main__":
    asyncio.run(main())

