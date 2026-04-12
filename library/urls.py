from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    StaffLoginView,
    borrow_book,
    home,
    librarian_dashboard,
    register,
    student_dashboard,
)

urlpatterns = [
    path("", home, name="home"),
    path("accounts/register/", register, name="register"),
    path("accounts/login/", StaffLoginView.as_view(), name="login"),
    path(
        "accounts/logout/",
        LogoutView.as_view(next_page="/"),
        name="logout",
    ),
    path("books/<int:pk>/borrow/", borrow_book, name="borrow_book"),
    path("student/", student_dashboard, name="student_dashboard"),
    path("librarian/", librarian_dashboard, name="librarian_dashboard"),
]
