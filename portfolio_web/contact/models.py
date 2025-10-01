from django.db import models


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    consent = models.BooleanField(default=False)  # GDPR/explicit consent
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        base = self.subject or (
            self.message[:40] + ("…" if len(self.message) > 40 else "")
        )
        return f"{self.name} — {base}"
