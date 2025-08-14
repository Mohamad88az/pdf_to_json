import json
import pdfplumber
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

class PDFtoJSONConverter:
    """Smart PDF to JSON converter with metadata, tables, layout, and basic image detection"""
    
    def __init__(self):
        self.metadata_fields = [
            'Title', 'Author', 'Subject', 'Keywords',
            'Creator', 'Producer', 'CreationDate', 'ModDate'
        ]
    
    def _parse_pdf_date(self, date_str: str) -> str:
        """Convert PDF date format to ISO string"""
        try:
            match = re.match(r"D:(\d{14})", date_str)
            if match:
                dt = datetime.strptime(match.group(1), '%Y%m%d%H%M%S')
                return dt.isoformat()
        except Exception:
            pass
        return date_str

    def extract_metadata(self, pdf) -> Dict[str, str]:
        meta = {}
        raw_meta = pdf.metadata or {}
        for field in self.metadata_fields:
            if field in raw_meta:
                if 'Date' in field:
                    meta[field] = self._parse_pdf_date(raw_meta[field])
                else:
                    meta[field] = raw_meta[field]
        return meta
    
    def extract_page_content(self, page) -> Dict[str, Any]:
        content: Dict[str, Any] = {
            "text": page.extract_text() or "",
            "tables": [{"data": t} for t in (page.extract_tables() or [])],
            "images": bool(page.images),
            "layout": {}
        }
        
        words = page.extract_words()
        if words:
            content["layout"] = {
                "word_count": len(words),
                "avg_word_length": sum(len(w['text']) for w in words)/len(words)
            }
        
        return content
    
    def convert(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        result = {"metadata": {}, "pages": [], "stats": {}}
        try:
            with pdfplumber.open(pdf_path) as pdf:
                result["metadata"] = self.extract_metadata(pdf)
                
                for i, page in enumerate(pdf.pages, start=1):
                    result["pages"].append({
                        "page_number": i,
                        "dimensions": {"width": page.width, "height": page.height},
                        "content": self.extract_page_content(page)
                    })
                
                total_words = sum(len(p["content"]["text"].split()) for p in result["pages"])
                result["stats"] = {"total_pages": len(pdf.pages), "total_words": total_words}
                
                return result
        except Exception as e:
            print(f"[Error] PDF processing failed: {e}")
            return None
    
    def save_as_json(self, data: Dict[str, Any], output_path: str, pretty: bool = True) -> bool:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2 if pretty else None)
            return True
        except Exception as e:
            print(f"[Error] Saving JSON failed: {e}")
            return False

# Example CLI usage
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Convert PDF to structured JSON")
    parser.add_argument("input_pdf", help="Path to input PDF file")
    parser.add_argument("-o", "--output", help="Path to output JSON file")
    parser.add_argument("-p", "--pretty", action="store_true", help="Pretty print JSON")
    args = parser.parse_args()

    converter = PDFtoJSONConverter()
    data = converter.convert(args.input_pdf)
    if data is None:
        sys.exit(1)

    if args.output:
        if converter.save_as_json(data, args.output, pretty=args.pretty):
            print(f"✅ JSON saved to {args.output}")
        else:
            sys.exit(1)
    elif args.pretty:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(data, ensure_ascii=False))
