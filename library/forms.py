from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

_INPUT = (
    "w-full rounded-xl border border-white/10 bg-slate-950/50 px-4 py-3 text-sm "
    "text-white outline-none ring-2 ring-transparent focus:border-sky-400/40 "
    "focus:ring-sky-500/30"
)


class RegisterForm(UserCreationForm):
    """Minimal sign-up: username + password (with confirmation)."""

    class Meta:
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": _INPUT, "autocomplete": "username", "autofocus": True}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": _INPUT, "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": _INPUT, "autocomplete": "new-password"}
        )
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""
