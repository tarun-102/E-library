import csv
import io
import json

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BulkBookUploadForm, RegisterForm
from .models import Book, IssuedBook


def _active_loan_book_ids():
    return set(
        IssuedBook.objects.filter(
            status__in=(IssuedBook.Status.PENDING, IssuedBook.Status.APPROVED),
        ).values_list("book_id", flat=True)
    )


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    text = str(value).strip().lower()
    return text not in {"0", "false", "no", "n"}


def _normalize_category(value):
    if not value:
        return "fiction"
    return str(value).strip().lower()


def _build_book(row):
    title = str(row.get("title", "")).strip()
    author = str(row.get("author", "")).strip()
    if not title or not author:
        raise ValueError("Each row needs title and author.")
    return Book(
        title=title,
        author=author,
        isbn=str(row.get("isbn", "")).strip(),
        category=_normalize_category(row.get("category")),
        image_url=str(row.get("image_url", "")).strip(),
        is_available=_parse_bool(row.get("is_available", True)),
    )


def home(request):
    books = Book.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        books = books.filter(
            Q(title__icontains=q) | Q(category__icontains=q),
        )
    available_only = request.GET.get("available") == "1"
    if available_only:
        books = books.filter(is_available=True)

    blocked_ids = list(_active_loan_book_ids())
    return render(
        request,
        "home.html",
        {
            "books": books,
            "q": q,
            "available_only": available_only,
            "blocked_book_ids": blocked_ids,
        },
    )


def book_detail(request, pk):
    book = Book.objects.filter(pk=pk).first()
    if not book:
        messages.warning(
            request,
            "This book is no longer available in the catalog.",
        )
        return redirect("home")
    active_loan = (
        IssuedBook.objects.filter(book=book, status=IssuedBook.Status.APPROVED)
        .select_related("user")
        .first()
    )
    pending_count = IssuedBook.objects.filter(book=book, status=IssuedBook.Status.PENDING).count()
    can_borrow = (
        request.user.is_authenticated
        and book.is_available
        and book.id not in _active_loan_book_ids()
    )
    return render(
        request,
        "book_detail.html",
        {
            "book": book,
            "active_loan": active_loan,
            "pending_count": pending_count,
            "can_borrow": can_borrow,
        },
    )


@login_required
def borrow_book(request, pk):
    if request.method != "POST":
        return redirect("home")
    book = get_object_or_404(Book, pk=pk)
    if not book.is_available:
        messages.error(request, "This book is not available right now.")
        return redirect("home")
    if book.id in _active_loan_book_ids():
        messages.warning(
            request,
            "This book already has an active borrow request or is on loan.",
        )
        return redirect("home")
    IssuedBook.objects.create(book=book, user=request.user, status=IssuedBook.Status.PENDING)
    messages.success(request, "Borrow request sent. A librarian will review it.")
    return redirect("student_dashboard")


@login_required
def student_dashboard(request):
    loans = (
        IssuedBook.objects.filter(user=request.user)
        .select_related("book")
        .order_by("-issue_date")
    )
    return render(
        request,
        "student_dashboard.html",
        {"loans": loans},
    )


@user_passes_test(lambda u: u.is_staff)
def librarian_dashboard(request):
    if request.method == "POST":
        issued_id = request.POST.get("issued_id")
        action = request.POST.get("action")
        ib = get_object_or_404(IssuedBook, pk=issued_id)
        if action == "approve":
            with transaction.atomic():
                ib = IssuedBook.objects.select_for_update().get(pk=issued_id)
                if ib.status != IssuedBook.Status.PENDING:
                    messages.warning(request, "That request is no longer pending.")
                    return redirect("librarian_dashboard")
                if IssuedBook.objects.filter(
                    book=ib.book,
                    status=IssuedBook.Status.APPROVED,
                ).exists():
                    messages.error(request, "This book is already on loan.")
                    return redirect("librarian_dashboard")
                ib.status = IssuedBook.Status.APPROVED
                ib.book.is_available = False
                ib.book.save(update_fields=["is_available"])
                ib.save(update_fields=["status"])
                IssuedBook.objects.filter(
                    book=ib.book,
                    status=IssuedBook.Status.PENDING,
                ).exclude(pk=ib.pk).delete()
            messages.success(request, f"Approved: {ib.book.title}")
        elif action == "reject":
            if ib.status == IssuedBook.Status.PENDING:
                book = ib.book
                ib.delete()
                messages.info(request, "Request rejected and removed.")
                if not IssuedBook.objects.filter(
                    book=book,
                    status__in=(
                        IssuedBook.Status.PENDING,
                        IssuedBook.Status.APPROVED,
                    ),
                ).exists():
                    book.is_available = True
                    book.save(update_fields=["is_available"])
            else:
                messages.warning(request, "Only pending requests can be rejected.")
        elif action == "return":
            if ib.status == IssuedBook.Status.APPROVED:
                ib.status = IssuedBook.Status.RETURNED
                ib.book.is_available = True
                ib.book.save(update_fields=["is_available"])
                ib.save(update_fields=["status"])
                messages.success(request, f"Marked returned: {ib.book.title}")
            else:
                messages.warning(request, "Only approved loans can be marked returned.")
        return redirect("librarian_dashboard")

    pending = (
        IssuedBook.objects.filter(status=IssuedBook.Status.PENDING)
        .select_related("book", "user")
        .order_by("issue_date")
    )
    active = (
        IssuedBook.objects.filter(status=IssuedBook.Status.APPROVED)
        .select_related("book", "user")
        .order_by("return_date")
    )
    stats = {
        "total_books": Book.objects.count(),
        "available_books": Book.objects.filter(is_available=True).count(),
        "pending_requests": pending.count(),
        "active_loans": active.count(),
    }
    return render(
        request,
        "librarian_dashboard.html",
        {"pending": pending, "active": active, "stats": stats},
    )


@user_passes_test(lambda u: u.is_staff)
def bulk_add_books(request):
    if request.method == "POST":
        form = BulkBookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            books_to_create = []
            try:
                if form.cleaned_data.get("json_payload"):
                    payload = json.loads(form.cleaned_data["json_payload"])
                    if not isinstance(payload, list):
                        raise ValueError("JSON must be an array of objects.")
                    for row in payload:
                        if not isinstance(row, dict):
                            raise ValueError("Each JSON item must be an object.")
                        books_to_create.append(_build_book(row))
                else:
                    csv_data = form.cleaned_data["csv_file"].read().decode("utf-8")
                    reader = csv.DictReader(io.StringIO(csv_data))
                    for row in reader:
                        books_to_create.append(_build_book(row))
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                messages.error(request, f"Import failed: {exc}")
                return render(request, "bulk_add_books.html", {"form": form})

            if not books_to_create:
                messages.warning(request, "No valid rows found.")
                return render(request, "bulk_add_books.html", {"form": form})

            Book.objects.bulk_create(books_to_create, batch_size=200)
            messages.success(request, f"{len(books_to_create)} books added successfully.")
            return redirect("librarian_dashboard")
    else:
        form = BulkBookUploadForm()

    return render(request, "bulk_add_books.html", {"form": form})


class StaffLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Your account was created. You are now signed in.")
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})
