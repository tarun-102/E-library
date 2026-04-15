"""
Demo catalog when the database has no books (common on fresh / serverless SQLite).
Does not remove or overwrite existing rows.
"""

from django.db import transaction

from .models import Book

# Stable cover thumbnails (Open Library) — catalog still comes from the DB after insert.
_SAMPLE = (
    {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "category": "fiction",
        "image_url": "https://covers.openlibrary.org/b/id/8228641-L.jpg",
    },
    {
        "title": "1984",
        "author": "George Orwell",
        "category": "fiction",
        "image_url": "https://covers.openlibrary.org/b/id/7222246-L.jpg",
    },
    {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "category": "tech",
        "image_url": "https://covers.openlibrary.org/b/id/8380861-L.jpg",
    },
    {
        "title": "Dune",
        "author": "Frank Herbert",
        "category": "sci-fi",
        "image_url": "https://covers.openlibrary.org/b/id/9255566-L.jpg",
    },
    {
        "title": "Sapiens",
        "author": "Yuval Noah Harari",
        "category": "non-fiction",
        "image_url": "https://covers.openlibrary.org/b/id/8136571-L.jpg",
    },
    {
        "title": "The Diary of a Young Girl",
        "author": "Anne Frank",
        "category": "biography",
        "image_url": "https://covers.openlibrary.org/b/id/8739161-L.jpg",
    },
    {
        "title": "A Brief History of Time",
        "author": "Stephen Hawking",
        "category": "non-fiction",
        "image_url": "https://covers.openlibrary.org/b/id/10523225-L.jpg",
    },
    {
        "title": "Python Crash Course",
        "author": "Eric Matthes",
        "category": "tech",
        "image_url": "https://covers.openlibrary.org/b/id/8380861-L.jpg",
    },
)


def ensure_sample_books() -> None:
    if Book.objects.exists():
        return
    with transaction.atomic():
        Book.objects.bulk_create([Book(**row) for row in _SAMPLE])
