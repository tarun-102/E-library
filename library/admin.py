from django.contrib import admin

from .models import Book, IssuedBook


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn", "category", "is_available")
    list_display_links = ("title",)
    list_editable = ("is_available",)
    list_filter = ("category", "is_available")
    search_fields = ("title", "author", "isbn")
    fieldsets = (
        (None, {"fields": ("title", "author", "isbn", "category", "is_available")}),
        (
            "Cover (choose one or both — file is shown first)",
            {"fields": ("image", "image_url")},
        ),
    )


@admin.register(IssuedBook)
class IssuedBookAdmin(admin.ModelAdmin):
    list_display = (
        "book",
        "user",
        "status",
        "issue_date",
        "return_date",
    )
    list_filter = ("status",)
    search_fields = ("book__title", "user__username")
    autocomplete_fields = ("book", "user")
    date_hierarchy = "issue_date"
