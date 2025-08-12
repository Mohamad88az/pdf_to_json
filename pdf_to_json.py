#pdf_to_json
import json
import pdfplumber
from typing import Dict, List, Optional
from datetime import datetime

class PDFtoJSONConverter:
    """
    A smart PDF to JSON converter with advanced text extraction capabilities
    """
    
    def __init__(self):
        self.metadata_fields = [
            'Title', 'Author', 'Subject', 'Keywords',
            'Creator', 'Producer', 'CreationDate', 'ModDate'
        ]
    
    def extract_metadata(self, pdf) -> Dict[str, str]:
        """Extract document metadata with proper type conversion"""
        meta = {}
        raw_meta = pdf.metadata or {}
        
        for field in self.metadata_fields:
            if field in raw_meta:
                # Convert PDF date format to readable string
                if 'Date' in field and raw_meta[field].startswith('D:'):
                    date_str = raw_meta[field][2:]
                    try:
                        dt = datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
                        meta[field] = dt.isoformat()
                    except:
                        meta[field] = raw_meta[field]
                else:
                    meta[field] = raw_meta[field]
        
        return meta
    
    def extract_page_content(self, page) -> Dict[str, any]:
        """Intelligently extract content from a single page"""
        content = {
            "text": page.extract_text() or "",
            "tables": [],
            "images": False,  # Placeholder for image detection
            "layout": []      # For storing layout information
        }
        
        # Extract tables if any
        tables = page.extract_tables()
        if tables:
            content["tables"] = [{"data": table} for table in tables]
        
        # Simple layout analysis (improve with more sophisticated logic)
        words = page.extract_words()
        if words:
            content["layout"] = {
                "word_count": len(words),
                "avg_word_length": sum(len(w['text']) for w in words)/len(words)
            }
        
        return content
    
    def convert(self, pdf_path: str) -> Optional[Dict[str, any]]:
        """
        Convert PDF file to structured JSON data
        
        Args:
            pdf_path: Path to input PDF file
            
        Returns:
            Dictionary containing structured document data or None if error occurs
        """
        result = {
            "metadata": {},
            "pages": [],
            "stats": {}
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract document metadata
                result["metadata"] = self.extract_metadata(pdf)
                
                # Process each page
                for i, page in enumerate(pdf.pages, start=1):
                    page_data = {
                        "page_number": i,
                        "dimensions": {
                            "width": page.width,
                            "height": page.height
                        },
                        "content": self.extract_page_content(page)
                    }
                    result["pages"].append(page_data)
                
                # Calculate document statistics
                result["stats"] = {
                    "total_pages": len(pdf.pages),
                    "total_words": sum(
                        len(p["content"]["text"].split()) 
                        for p in result["pages"]
                    )
                }
                
                return result
                
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return None
    
    def save_as_json(self, data: Dict[str, any], output_path: str) -> bool:
        """
        Save converted data to JSON file
        
        Args:
            data: Converted PDF data
            output_path: Path to output JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving JSON: {str(e)}")
            return False

def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert PDF files to structured JSON format'
    )
    parser.add_argument('input_pdf', help='Path to input PDF file')
    parser.add_argument('-o', '--output', help='Path to output JSON file')
    parser.add_argument('-p', '--pretty', 
                       action='store_true',
                       help='Pretty print JSON to console')
    
    args = parser.parse_args()
    
    converter = PDFtoJSONConverter()
    result = converter.convert(args.input_pdf)
    
    if result is None:
        sys.exit(1)
    
    if args.output:
        if converter.save_as_json(result, args.output):
            print(f"Successfully saved to {args.output}")
        else:
            sys.exit(1)
    elif args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()



