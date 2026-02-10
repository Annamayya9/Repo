from google_storage import GoogleSheetsDB
import os

# Set environment variables
os.environ['GOOGLE_SHEET_ID'] = '1r_0Gd1fLlAxMZ-pMMFG0clHsk4PJfejuatgKwQ96JWk'
os.environ['GOOGLE_DRIVE_FOLDER_ID'] = '142rGEKf-EFiSbN505IvXfRU7NvjwmGQK'  # NEW!

# Initialize
db = GoogleSheetsDB()

# Test upload
test_pdf = 'biweekly_roundup_20251016.pdf'

if os.path.exists(test_pdf):
    print(f"Testing upload of: {test_pdf}")
    download_link, view_link = db.upload_pdf_to_drive(test_pdf)
    
    if download_link:
        print(f"\n✅ Success!")
        print(f"Download: {download_link}")
        print(f"View: {view_link}")
        
        # Save to metadata
        db.save_pdf_link(download_link, view_link)
        print("\n✅ Link saved to Metadata sheet")
    else:
        print("\n❌ Upload failed")
else:
    print(f"❌ File not found: {test_pdf}")