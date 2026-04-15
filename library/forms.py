from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

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


class BulkBookUploadForm(forms.Form):
    json_payload = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": _INPUT,
                "rows": 10,
                "placeholder": (
                    '[\n'
                    '  {\n'
                    '    "title": "Atomic Habits",\n'
                    '    "author": "James Clear",\n'
                    '    "isbn": "9781847941831",\n'
                    '    "category": "non-fiction",\n'
                    '    "image_url": "https://example.com/atomic-habits.jpg",\n'
                    '    "is_available": true\n'
                    "  },\n"
                    '  {\n'
                    '    "title": "Clean Code",\n'
                    '    "author": "Robert C. Martin",\n'
                    '    "isbn": "9780132350884",\n'
                    '    "category": "tech",\n'
                    '    "image_url": "https://example.com/clean-code.jpg",\n'
                    '    "is_available": true\n'
                    "  }\n"
                    "]"
                ),
            }
        ),
        help_text="Paste a JSON array of books.",
    )
    csv_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": (
                    "block w-full cursor-pointer rounded-xl border border-white/10 "
                    "bg-slate-950/40 px-3 py-2 text-sm text-slate-200 file:mr-4 "
                    "file:rounded-lg file:border-0 file:bg-sky-600/80 file:px-3 "
                    "file:py-2 file:text-sm file:font-semibold file:text-white "
                    "hover:file:bg-sky-500"
                )
            }
        ),
        help_text="Or upload CSV with headers: title,author,isbn,category,image_url,is_available",
    )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("json_payload") and not cleaned_data.get("csv_file"):
            raise forms.ValidationError("Paste JSON data or upload a CSV file.")
        return cleaned_data
