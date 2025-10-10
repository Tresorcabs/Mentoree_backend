"""
Models for the resources app.

This file defines the Category and Resource models for managing educational resources.
Resources can be articles, videos, PDFs, ebooks, templates, podcasts, or images.
Each resource has a validation workflow (pending -> validated/rejected).
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Category(models.Model):
    """
    Category model for organizing resources.

    Attributes:
        name (str): Unique name of the category (e.g., Backend, Mobile)
        slug (str): URL-friendly slug for the category
    """
    name = models.CharField(max_length=100, unique=True)  # nom de la catégorie (ex: Backend, Mobile)
    slug = models.SlugField(max_length=120, unique=True)  # slug pour les urls

    def __str__(self):
        return self.name


class Resource(models.Model):
    """
    Resource model representing educational content.

    Attributes:
        title (str): Title of the resource
        description (str): Short summary/description
        type (str): Type of resource (article, video, pdf, template, podcast, image)
        url (str): External URL (for videos, articles, etc.)
        file (File): Uploaded file (for PDFs, templates)
        category (Category): Associated category
        source (str): Source of the resource (youtube, dev.to, manual, etc.)
        origin (str): Geographic origin (local/international)
        difficulty (str): Difficulty level (beginner/intermediate/advanced)
        tags (list): JSON list of tags (e.g., ["#frontend", "#react"])
        created_by (User): User who created the resource
        status (str): Validation status (pending/validated/rejected)
        featured (bool): Whether resource is featured
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """

    # Resource type choices
    RESOURCE_TYPES = [
        ('article', 'Article'),
        ('video', 'Vidéo'),
        ('pdf', 'PDF / Ebook'),
        ('template', 'Template'),
        ('podcast', 'Podcast'),
        ('image', 'Image'),
    ]

    # Status choices for validation workflow
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('validated', 'Validée'),
        ('rejected', 'Rejetée'),
    ]

    # Origin choices
    ORIGIN_CHOICES = [
        ('local', 'Local'),
        ('international', 'International'),
    ]

    # Difficulty choices
    DIFFICULTY_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]

    title = models.CharField(max_length=255)  # Titre de la ressource
    description = models.TextField(blank=True)  # Résumé court
    type = models.CharField(max_length=20, choices=RESOURCE_TYPES)  # type
    url = models.URLField(blank=True, null=True)  # lien vers la ressource externe (Youtube, article, etc.)
    file = models.FileField(upload_to='resources/files/', blank=True, null=True)  # fichier téléchargeable (pdf, template)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='resources')
    source = models.CharField(max_length=100, default='manual')  # ex: 'youtube', 'dev.to', 'manual'
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES, default='international')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    tags = models.JSONField(default=list, blank=True)  # liste de tags (ex: ["#frontend","#react"])
    content = models.TextField(blank=True, null=True)  # contenu textuel pour articles et autres ressources textuelles
    summary = models.TextField(blank=True, null=True)  # résumé détaillé pour vidéos et podcasts
    keypoints = models.JSONField(default=list, blank=True)  # points clés abordés (liste de strings)
    duration = models.CharField(max_length=20, blank=True, null=True)  # durée (pour vidéos/podcasts)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    featured = models.BooleanField(default=False)  # affichage en mise en avant
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-featured', '-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        """
        Validate model fields.

        Ensures that:
        - For video type, URL is required
        - For pdf/template types, either URL or file is required
        """
        super().clean()

        if self.type == 'video' and not self.url:
            raise ValidationError({'url': 'URL is required for video resources.'})

        if self.type in ['pdf', 'template'] and not (self.url or self.file):
            raise ValidationError({'url': 'Either URL or file is required for PDF/Template resources.'})

    def save(self, *args, **kwargs):
        """
        Override save to run validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)
