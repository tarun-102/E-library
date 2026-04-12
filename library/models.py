from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Book(models.Model):
    class Category(models.TextChoices):
        FICTION = "fiction", "Fiction"
        TECH = "tech", "Tech"
        SCI_FI = "sci-fi", "Sci-Fi"
        NON_FICTION = "non-fiction", "Non-Fiction"
        BIOGRAPHY = "biography", "Biography"
        HISTORY = "history", "History"
        OTHER = "other", "Other"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="International Standard Book Number (optional).",
    )
    category = models.CharField(
        max_length=32,
        choices=Category.choices,
        default=Category.FICTION,
    )
    image = models.ImageField(
        upload_to="book_covers/",
        blank=True,
        null=True,
        help_text="Upload a cover file. If set, this is shown instead of the URL below.",
    )
    image_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Or paste a direct image link (https://…jpg/png). Used when no file is uploaded.",
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def cover_display_url(self):
        """Which cover to show in templates: uploaded file wins, else external URL."""
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url.strip()
        return ""


class IssuedBook(models.Model):
    """
    Borrow request / loan row.

    - ``book`` + ``user``: which student asked for which copy (many rows per book over time).
    - ``issue_date``: auto-set when the row is first saved (request / record created).
    - ``return_date``: due date — always set to today + 14 days on first save.
    - ``status``: Pending until staff approves; Approved while on loan; Returned when closed.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        RETURNED = "returned", "Returned"

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="issued_books",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issued_books",
    )
    issue_date = models.DateField(auto_now_add=True)
    return_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )

    class Meta:
        ordering = ["-issue_date"]
        verbose_name = "Issued book"
        verbose_name_plural = "Issued books"

    def __str__(self):
        return f"{self.book.title} — {self.user} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if self._state.adding and not self.return_date:
            self.return_date = timezone.now().date() + timedelta(days=14)
        super().save(*args, **kwargs)
