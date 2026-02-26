import asyncio
from app.services.google_sheets import get_workbook

def main():
    try:
        workbook = get_workbook("1tuGBnQFjDntJQglofA17uHhiyekkVyDoSInErbwfR24")
        
        print("Available worksheets:")
        for sheet in workbook.worksheets():
            print(f"- {sheet.title}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
