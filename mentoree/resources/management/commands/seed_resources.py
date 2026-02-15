"""
Management command to seed the database with sample resources.

This command creates categories and sample resources for testing and demonstration.
Run with: python manage.py seed_resources
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from resources.models import Category, Resource


class Command(BaseCommand):
    """
    Seed the database with sample resources and categories.
    """

    help = 'Seed the database with sample resources and categories'

    def handle(self, *args, **options):
        """
        Execute the seeding process.
        """
        self.stdout.write('Seeding resources...')

        # Get or create admin user for validated resources
        User = get_user_model()
        try:
            admin_user = User.objects.filter(is_staff=True).first()
            if not admin_user:
                admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                # Create a dummy admin user if none exists
                admin_user = User.objects.create_user(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    is_staff=True,
                    is_superuser=True
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created admin user: {admin_user.username}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not get/create admin user: {e}')
            )
            admin_user = None

        # Create categories
        categories_data = [
            {'name': 'Backend Development', 'slug': 'backend'},
            {'name': 'Frontend Development', 'slug': 'frontend'},
            {'name': 'Mobile Development', 'slug': 'mobile'},
            {'name': 'DevOps', 'slug': 'devops'},
            {'name': 'Career Development', 'slug': 'career'},
            {'name': 'Data Science', 'slug': 'data-science'},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={'name': cat_data['name']}
            )
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Sample resources data
        resources_data = [
            # Videos (validated)
            {
                'title': 'Introduction to React Hooks',
                'description': 'Learn the fundamentals of React Hooks with practical examples.',
                'type': 'video',
                'url': 'https://www.youtube.com/watch?v=dpw9EHDh2bM',
                'category': categories.get('frontend'),
                'source': 'youtube',
                'origin': 'international',
                'difficulty': 'intermediate',
                'tags': ['#react', '#hooks', '#javascript', '#frontend'],
                'summary': 'Cette vidéo couvre les concepts fondamentaux des React Hooks, incluant useState, useEffect, useContext et les hooks personnalisés. Vous apprendrez comment remplacer les composants de classe par des composants fonctionnels plus modernes et maintenables.',
                'keypoints': [
                    'Comprendre le cycle de vie des composants React',
                    'Maîtriser useState pour la gestion d\'état local',
                    'Utiliser useEffect pour les effets secondaires',
                    'Créer des hooks personnalisés réutilisables',
                    'Migrer des composants de classe vers des fonctions'
                ],
                'duration': '45:30',
                'status': 'validated',
                'featured': True,
                'created_by': admin_user,
            },
            {
                'title': 'Python Django REST Framework Tutorial',
                'description': 'Complete guide to building APIs with Django REST Framework.',
                'type': 'video',
                'url': 'https://www.youtube.com/watch?v=c708Nf0cHrs',
                'category': categories.get('backend'),
                'source': 'youtube',
                'origin': 'international',
                'difficulty': 'intermediate',
                'tags': ['#django', '#python', '#api', '#backend'],
                'status': 'validated',
                'featured': False,
                'created_by': admin_user,
            },
            # Articles (validated)
            {
                'title': 'Understanding TypeScript Generics',
                'description': 'A comprehensive guide to TypeScript generics with examples.',
                'type': 'article',
                'url': 'https://www.typescriptlang.org/docs/handbook/2/generics.html',
                'category': categories.get('frontend'),
                'source': 'typescript',
                'origin': 'international',
                'difficulty': 'advanced',
                'tags': ['#typescript', '#generics', '#frontend'],
                'content': '''# Comprendre les Génériques TypeScript

Les génériques TypeScript permettent d'écrire du code réutilisable qui fonctionne avec différents types tout en maintenant la sécurité de type.

## Qu'est-ce qu'un générique ?

Un générique est comme un paramètre pour les types. Au lieu de travailler avec un type spécifique, nous travaillons avec un type qui sera spécifié plus tard.

## Syntaxe de base

```typescript
function identity<T>(arg: T): T {
    return arg;
}
```

Le `<T>` après le nom de fonction indique que c'est une fonction générique avec un paramètre de type `T`.

## Utilisation des génériques

### Fonctions génériques
```typescript
function reverse<T>(items: T[]): T[] {
    return items.reverse();
}

reverse([1, 2, 3]);        // number[]
reverse(['a', 'b', 'c']);   // string[]
```

### Interfaces génériques
```typescript
interface Container<T> {
    value: T;
    getValue(): T;
}
```

### Classes génériques
```typescript
class Stack<T> {
    private items: T[] = [];

    push(item: T): void {
        this.items.push(item);
    }

    pop(): T | undefined {
        return this.items.pop();
    }
}
```

## Contraintes de génériques

Vous pouvez limiter les types possibles avec `extends` :

```typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key];
}
```

## Génériques avancés

### Types conditionnels
```typescript
type IsString<T> = T extends string ? 'yes' : 'no';
```

### Types utilitaires
TypeScript fournit plusieurs types utilitaires basés sur les génériques :
- `Partial<T>`
- `Required<T>`
- `Readonly<T>`
- `Pick<T, K>`
- `Omit<T, K>`

## Bonnes pratiques

1. Utilisez des noms descriptifs pour les paramètres de type (T, U, V...)
2. Évitez les génériques trop complexes
3. Utilisez des contraintes quand nécessaire
4. Documentez vos génériques avec des commentaires JSDoc

Les génériques sont un outil puissant pour écrire du code TypeScript maintenable et réutilisable.''',
                'status': 'validated',
                'featured': False,
                'created_by': admin_user,
            },
            {
                'title': 'Docker Best Practices for Development',
                'description': 'Essential Docker practices for efficient development workflows.',
                'type': 'article',
                'url': 'https://docs.docker.com/develop/dev-best-practices/',
                'category': categories.get('devops'),
                'source': 'docker',
                'origin': 'international',
                'difficulty': 'intermediate',
                'tags': ['#docker', '#devops', '#containers'],
                'status': 'validated',
                'featured': True,
                'created_by': admin_user,
            },
            # PDFs (validated) - using placeholder URLs since we can't create actual files
            {
                'title': 'Clean Code: A Handbook of Agile Software Craftsmanship',
                'description': 'Essential principles for writing clean, maintainable code.',
                'type': 'pdf',
                'url': 'https://example.com/clean-code.pdf',  # Placeholder
                'category': categories.get('career'),
                'source': 'book',
                'origin': 'international',
                'difficulty': 'intermediate',
                'tags': ['#clean-code', '#best-practices', '#software-craftsmanship'],
                'status': 'validated',
                'featured': False,
                'created_by': admin_user,
            },
            {
                'title': 'The Pragmatic Programmer',
                'description': 'Timeless tips for software developers.',
                'type': 'pdf',
                'url': 'https://example.com/pragmatic-programmer.pdf',  # Placeholder
                'category': categories.get('career'),
                'source': 'book',
                'origin': 'international',
                'difficulty': 'beginner',
                'tags': ['#pragmatic', '#software-development', '#career'],
                'status': 'validated',
                'featured': False,
                'created_by': admin_user,
            },
            # Local Cameroonian content (validated)
            {
                'title': 'Développement Mobile au Cameroun',
                'description': 'Guide du développement d\'applications mobiles au Cameroun.',
                'type': 'article',
                'url': 'https://example.com/mobile-dev-cameroun',  # Placeholder
                'category': categories.get('mobile'),
                'source': 'local',
                'origin': 'local',
                'difficulty': 'beginner',
                'tags': ['#cameroun', '#mobile', '#développement-local'],
                'status': 'validated',
                'featured': True,
                'created_by': admin_user,
            },
            # Pending resources
            {
                'title': 'Advanced Kubernetes Patterns',
                'description': 'Learn advanced patterns for Kubernetes deployments.',
                'type': 'template',
                'url': 'https://example.com/k8s-templates.zip',  # Placeholder
                'category': categories.get('devops'),
                'source': 'manual',
                'origin': 'international',
                'difficulty': 'advanced',
                'tags': ['#kubernetes', '#devops', '#templates'],
                'status': 'pending',
                'featured': False,
                'created_by': admin_user,
            },
            {
                'title': 'React Native Starter Template',
                'description': 'A comprehensive starter template for React Native projects.',
                'type': 'template',
                'url': 'https://example.com/react-native-starter.zip',  # Placeholder
                'category': categories.get('mobile'),
                'source': 'manual',
                'origin': 'international',
                'difficulty': 'intermediate',
                'tags': ['#react-native', '#mobile', '#template'],
                'status': 'pending',
                'featured': False,
                'created_by': admin_user,
            },
            {
                'title': 'DevOps Podcast: CI/CD Best Practices',
                'description': 'Discussion approfondie sur les meilleures pratiques d\'intégration et déploiement continu.',
                'type': 'podcast',
                'url': 'https://example.com/devops-podcast-ep1.mp3',  # Placeholder
                'category': categories.get('devops'),
                'source': 'manual',
                'origin': 'international',
                'difficulty': 'intermediate',
                'tags': ['#devops', '#ci-cd', '#automation', '#podcast'],
                'summary': 'Dans cet épisode, nous explorons les stratégies modernes de CI/CD (Continuous Integration/Continuous Deployment). Nos experts discutent des outils populaires comme GitHub Actions, GitLab CI, Jenkins et ArgoCD, ainsi que des meilleures pratiques pour automatiser vos pipelines de déploiement.',
                'keypoints': [
                    'Comprendre les principes fondamentaux du CI/CD',
                    'Choisir les bons outils selon vos besoins',
                    'Implémenter des tests automatisés efficaces',
                    'Gérer les déploiements en environnement multi-cloud',
                    'Surveiller et optimiser les performances des pipelines',
                    'Sécuriser vos processus de déploiement'
                ],
                'duration': '58:42',
                'status': 'validated',
                'featured': False,
                'created_by': admin_user,
            },
        ]

        # Create resources
        created_count = 0
        for resource_data in resources_data:
            resource, created = Resource.objects.get_or_create(
                title=resource_data['title'],
                defaults=resource_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created resource: {resource.title}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} resources and {len(categories)} categories'
            )
        )

        # Summary
        validated_count = Resource.objects.filter(status='validated').count()
        pending_count = Resource.objects.filter(status='pending').count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Resources summary: {validated_count} validated, {pending_count} pending'
            )
        )