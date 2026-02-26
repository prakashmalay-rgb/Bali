import asyncio
from app.services.google_sheets import get_workbook
from app.services.pinconeservice import get_index
from app.settings.config import settings

def extract_and_ingest():
    print("Connecting to Google Sheets...")
    workbook = get_workbook("1tuGBnQFjDntJQglofA17uHhiyekkVyDoSInErbwfR24")
    
    # 1. Create or Extract Villa FAQs sheet
    try:
        faq_sheet = workbook.worksheet("Villa FAQs")
        print("Villa FAQs sheet found.")
    except Exception:
        print("Villa FAQs sheet not found. Creating it...")
        faq_sheet = workbook.add_worksheet("Villa FAQs", rows=1000, cols=10)
        faq_sheet.append_row(["Villa Code", "Villa Name", "Question", "Answer"])
        print("Setup headers for 'Villa FAQs'. Please populate data here.")
        
    data = faq_sheet.get_all_values()
    if len(data) <= 1:
        print("No data in Villa FAQs yet. Add data to ingest to Pinecone.")
        return

    # 2. Ingest to Pinecone
    print("Generating embeddings and ingesting to Pinecone...")
    index_name = "villa-faqs"
    index = get_index(index_name)
    
    if not index:
        print("Failed to access Pinecone.")
        return
        
    print(f"Connected to Pinecone index: {index_name}")

if __name__ == "__main__":
    extract_and_ingest()
