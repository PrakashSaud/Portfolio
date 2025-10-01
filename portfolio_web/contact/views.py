from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render

from .forms import ContactForm


def contact_index(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ip_address = get_client_ip(request)
            msg.save()

            # send email (dev backend: console)
            send_mail(
                subject=f"New Contact from {msg.name}",
                message=msg.message,
                from_email=msg.email,
                recipient_list=["owner@example.com"],
                fail_silently=True,
            )

            # HTMX: return success fragment
            return HttpResponse(
                "<div class='p-4 bg-green-100 text-green-800'>Thanks, we’ll be in touch!</div>"
            )
    else:
        form = ContactForm()

    return render(request, "contact/contact_index.html", {"form": form})


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0]
    return request.META.get("REMOTE_ADDR")
