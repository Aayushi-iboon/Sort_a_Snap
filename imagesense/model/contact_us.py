from django.db import models

class ContactUs(models.Model):
    name = models.CharField(max_length=50,null=True,blank=True)
    email = models.EmailField(unique=True,null=True,blank=True)
    phone_no = models.CharField(max_length=15,null=True, blank=True)
    message = models.TextField(help_text="Add your message", error_messages={
        'blank': 'Please enter a comment before submitting.',
        'null': 'Comment cannot be null. It is a required field.',
    })
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.email}"

    class Meta:
        verbose_name = "Contact Us"
        verbose_name_plural = "Contact Us"