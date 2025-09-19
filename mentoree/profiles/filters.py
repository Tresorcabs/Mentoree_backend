import django_filters
from django.db.models import JSONField, Q
from django_filters import rest_framework as filters
from .models import MentorProfile

class MentorProfileFilter(django_filters.FilterSet):
    # Custom filters for frontend parameters
    domain = filters.CharFilter(method='filter_domain')
    city = filters.CharFilter(method='filter_city')
    price_range = filters.CharFilter(method='filter_price_range')
    experience = filters.CharFilter(method='filter_experience')

    class Meta:
        model = MentorProfile
        fields = ['expertise', 'years_of_experience', 'languages', 'location', 'is_featured', 'is_new']

        filter_overrides = {
            JSONField: {
                'filter_class': filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }

    def filter_domain(self, queryset, name, value):
        """Filter mentors by domain/expertise"""
        if not value:
            return queryset

        # Map frontend domain values to actual expertise terms
        domain_mapping = {
            'dev': ['développement', 'web', 'frontend', 'backend', 'fullstack', 'javascript', 'python', 'react', 'node'],
            'data': ['data', 'science', 'machine learning', 'ai', 'analytics', 'python', 'sql'],
            'design': ['design', 'ux', 'ui', 'figma', 'adobe', 'photoshop', 'illustrator'],
            'marketing': ['marketing', 'digital', 'seo', 'social media', 'content', 'advertising'],
            'finance': ['finance', 'accounting', 'investment', 'banking', 'financial'],
            'leadership': ['leadership', 'management', 'team', 'strategy', 'coaching'],
            'hr': ['hr', 'human resources', 'recruitment', 'talent', 'people']
        }

        expertise_terms = domain_mapping.get(value, [])
        if not expertise_terms:
            return queryset

        # Create Q objects for each expertise term
        query = Q()
        for term in expertise_terms:
            query |= Q(expertise__icontains=term)

        return queryset.filter(query)

    def filter_city(self, queryset, name, value):
        """Filter mentors by city/location"""
        if not value:
            return queryset

        # Map frontend city values to actual location names
        city_mapping = {
            'yaounde': ['yaoundé', 'yaounde'],
            'douala': ['douala'],
            'bamenda': ['bamenda'],
            'bafoussam': ['bafoussam'],
            'garoua': ['garoua'],
            'maroua': ['maroua']
        }

        location_terms = city_mapping.get(value, [])
        if not location_terms:
            return queryset

        # Create Q objects for each location term
        query = Q()
        for term in location_terms:
            query |= Q(location__icontains=term)

        return queryset.filter(query)

    def filter_price_range(self, queryset, name, value):
        """Filter mentors by hourly rate range"""
        if not value:
            return queryset

        try:
            if value == '0-30':
                return queryset.filter(hourly_rate__gte=0, hourly_rate__lte=30)
            elif value == '30-50':
                return queryset.filter(hourly_rate__gte=30, hourly_rate__lte=50)
            elif value == '50-70':
                return queryset.filter(hourly_rate__gte=50, hourly_rate__lte=70)
            elif value == '70+':
                return queryset.filter(hourly_rate__gte=70)
        except (ValueError, TypeError):
            pass

        return queryset

    def filter_experience(self, queryset, name, value):
        """Filter mentors by years of experience"""
        if not value:
            return queryset

        try:
            if value == '0-3':
                return queryset.filter(years_of_experience__gte=0, years_of_experience__lte=3)
            elif value == '3-7':
                return queryset.filter(years_of_experience__gte=3, years_of_experience__lte=7)
            elif value == '7-12':
                return queryset.filter(years_of_experience__gte=7, years_of_experience__lte=12)
            elif value == '12+':
                return queryset.filter(years_of_experience__gte=12)
        except (ValueError, TypeError):
            pass

        return queryset
