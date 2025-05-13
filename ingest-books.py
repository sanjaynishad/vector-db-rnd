from embeddings import add_document
import json
import argparse

parser = argparse.ArgumentParser(description="Ingest Books")
parser.add_argument("path", help="Path to file")
parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
parser.add_argument("--count", help="Count")
args = parser.parse_args()

print("Filename:", args.path)
print("Verbose:", args.verbose)

book_path = args.path  # "../book-scrape-nodejs/.tmp"
count = args.count  # "../book-scrape-nodejs/.tmp"


def get_book_index():
    with open(f"{book_path}/book-index.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def read_books_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content.strip()


def format_breadcrumb_metadata(breadcrumbs):
    meta = {}
    for i, crumb in enumerate(breadcrumbs):
        meta[f"level{i+1}"] = crumb["label"]
        meta[f"level{i+1}Link"] = crumb["link"]
    meta["levels"] = len(breadcrumbs)
    meta["breadcrumbs"] = " > ".join(c["label"] for c in breadcrumbs)
    meta["breadcrumbsJson"] = json.dumps(breadcrumbs, ensure_ascii=False)
    return meta


def ingest_books():
    books = get_book_index()
    total = len(books)
    success_count = 0
    fail_count = 0

    for i, book in enumerate(books, 1):
        try:
            if i > count:
                return
            file_name = book.get("fileName")
            file_path = file_name.replace(".html", ".txt")

            text = read_books_from_file(f"{book_path}/text-files/{file_path}")

            if not text:
                print(f"[{i}/{total}] ⚠️ Skipping empty or missing file: {file_path}")
                fail_count += 1
                continue

            metadata = {
                "title": book.get("title"),
                "type": book.get("type"),
                "fileName": book.get("fileName"),
                **format_breadcrumb_metadata(book.get("breadcrumbs")),
            }

            print(f"[{i}/{total}] ✅ Ingesting: {file_path}")
            add_document(
                file_name,
                text,
                metadata,
            )
            success_count += 1

        except Exception as e:
            print(f"[{i}/{total}] ❌ Error reading {file_name}: {e}")
            fail_count += 1
            continue

    print(f"\n📚 Ingestion complete: {success_count} succeeded, {fail_count} failed.")


ingest_books()
