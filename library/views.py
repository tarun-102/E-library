from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegisterForm
from .models import Book, IssuedBook


def _active_loan_book_ids():
    return set(
        IssuedBook.objects.filter(
            status__in=(IssuedBook.Status.PENDING, IssuedBook.Status.APPROVED),
        ).values_list("book_id", flat=True)
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
    return render(
        request,
        "librarian_dashboard.html",
        {"pending": pending, "active": active},
    )


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
