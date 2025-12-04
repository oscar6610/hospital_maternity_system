"""
Vistas HTML para el Sistema Fiori Launchpad
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login as django_login
from django.views.decorators.csrf import csrf_exempt
from .models import FioriApp, UserAppConfig, UserFioriPreferences
from django.db.models import Q
from django.db import models
from django.contrib.auth import logout as django_logout


def login_view(request):
    """
    Vista de login para Fiori Launchpad.
    
    Si el usuario ya está autenticado, redirige al launchpad.
    Si no, muestra el formulario de login.
    """
    # Si ya está autenticado, redirigir al launchpad
    if request.user.is_authenticated:
        return redirect('fiori:launchpad')
    
    # Si es POST, procesar login
    if request.method == 'POST':
        run = request.POST.get('run', '').strip()
        password = request.POST.get('password', '')
        
        if not run or not password:
            context = {
                'error': 'Por favor, ingresa tu RUN y contraseña.',
                'run': run
            }
            return render(request, 'fiori/login.html', context)
        
        # Autenticar usuario
        user = authenticate(request, run=run, password=password)
        
        if user is not None:
            django_login(request, user)
            
            # Redirigir a la página solicitada o al launchpad
            next_url = request.GET.get('next', '/fiori/')
            return redirect(next_url)
        else:
            # Error de autenticación
            context = {
                'error': 'Credenciales inválidas. Por favor, verifica tu RUN y contraseña.',
                'run': run
            }
            return render(request, 'fiori/login.html', context)
    
    # Si es GET, mostrar formulario
    return render(request, 'fiori/login.html')


@login_required
def logout_view(request):
    """
    Vista de logout.
    """
    django_logout(request)
    return redirect('fiori:login')

@login_required
def launchpad(request):
    """
    Vista principal del Fiori Launchpad.
    Muestra las aplicaciones disponibles para el usuario.
    """
    user = request.user
    
    # Obtener apps accesibles para el usuario
    if user.is_superuser or user.groups.filter(name='Supervisor/Jefe de Área').exists():
        available_apps = FioriApp.objects.filter(active=True)
    else:
        available_apps = FioriApp.objects.filter(
            active=True
        ).filter(
            Q(allowed_groups__in=user.groups.all()) |
            Q(allowed_groups__isnull=True)
        ).distinct()
    
    # Filtrar apps realmente accesibles (verificar permisos)
    accessible_apps = [
        app for app in available_apps
        if app.is_accessible_by_user(user)
    ]
    
    # Obtener preferencias del usuario
    preferences, _ = UserFioriPreferences.objects.get_or_create(user=user)
    
    # Obtener configuraciones del usuario
    user_configs = UserAppConfig.objects.filter(
        user=user,
        app__in=accessible_apps
    ).select_related('app', 'app__category')
    
    # Crear mapeo de configuraciones
    config_map = {config.app.id_app: config for config in user_configs}
    
    # Construir datos de apps con configuración
    apps_with_config = []
    for app in accessible_apps:
        config = config_map.get(app.id_app)
        
        if config:
            is_visible = config.is_visible
            custom_order = config.custom_order
            is_favorite = config.is_favorite
            access_count = config.access_count
            last_accessed = config.last_accessed
        else:
            # Valores por defecto si no hay configuración
            is_visible = True
            custom_order = app.default_order
            is_favorite = False
            access_count = 0
            last_accessed = None
        
        if is_visible:  # Solo mostrar apps visibles
            apps_with_config.append({
                'app': app,
                'custom_order': custom_order,
                'is_favorite': is_favorite,
                'access_count': access_count,
                'last_accessed': last_accessed
            })
    
    # Ordenar por custom_order
    apps_with_config.sort(key=lambda x: x['custom_order'])
    
    # Apps recientes
    recent_apps = []
    if preferences.show_recent_apps:
        recent_configs = UserAppConfig.objects.filter(
            user=user,
            last_accessed__isnull=False,
            app__active=True
        ).select_related('app').order_by('-last_accessed')[:preferences.recent_apps_count]
        
        recent_apps = [
            {
                'app': config.app,
                'last_accessed': config.last_accessed,
                'access_count': config.access_count
            }
            for config in recent_configs
            if config.app.is_accessible_by_user(user)
        ]
    
    # Apps favoritas
    favorite_apps = [
        item for item in apps_with_config
        if item['is_favorite']
    ]
    
    # Agrupar por categoría si está habilitado
    apps_by_category = {}
    if preferences.group_by_category:
        for item in apps_with_config:
            app = item['app']
            category_name = app.category.name if app.category else 'Sin categoría'
            
            if category_name not in apps_by_category:
                apps_by_category[category_name] = {
                    'category': app.category,
                    'apps': []
                }
            
            apps_by_category[category_name]['apps'].append(item)
    
    context = {
        'apps_with_config': apps_with_config,
        'recent_apps': recent_apps,
        'favorite_apps': favorite_apps,
        'apps_by_category': apps_by_category,
        'preferences': preferences,
        'total_apps': len(accessible_apps),
        'visible_apps': len(apps_with_config),
        'favorite_count': len(favorite_apps)
    }
    
    return render(request, 'fiori/launchpad.html', context)


@login_required
def app_personalizer(request):
    """
    Vista para personalizar el Launchpad.
    Permite al usuario seleccionar qué apps ver y organizarlas.
    """
    user = request.user
    
    # Obtener todas las apps accesibles
    if user.is_superuser or user.groups.filter(name='Supervisor/Jefe de Área').exists():
        available_apps = FioriApp.objects.filter(active=True)
    else:
        available_apps = FioriApp.objects.filter(
            active=True
        ).filter(
            Q(allowed_groups__in=user.groups.all()) |
            Q(allowed_groups__isnull=True)
        ).distinct()
    
    accessible_apps = [
        app for app in available_apps
        if app.is_accessible_by_user(user)
    ]
    
    # Obtener configuraciones actuales
    user_configs = UserAppConfig.objects.filter(
        user=user,
        app__in=accessible_apps
    ).select_related('app', 'app__category')
    
    config_map = {config.app.id_app: config for config in user_configs}
    
    # Construir datos para el editor
    apps_data = []
    for app in accessible_apps:
        config = config_map.get(app.id_app)
        
        apps_data.append({
            'app': app,
            'is_visible': config.is_visible if config else True,
            'custom_order': config.custom_order if config else app.default_order,
            'is_favorite': config.is_favorite if config else False,
            'custom_group_name': config.custom_group_name if config else ''
        })
    
    # Obtener preferencias
    preferences, _ = UserFioriPreferences.objects.get_or_create(user=user)
    
    context = {
        'apps_data': apps_data,
        'preferences': preferences
    }
    
    return render(request, 'fiori/app-personalizer.html', context)


@login_required
@require_http_methods(["POST"])
def save_app_order(request):
    """
    AJAX endpoint para guardar el orden de las apps.
    
    POST /fiori/api/save-order/
    Body: {"apps": [{"id": 1, "order": 0}, {"id": 2, "order": 1}]}
    """
    import json
    
    try:
        data = json.loads(request.body)
        apps_order = data.get('apps', [])
        user = request.user
        
        for app_data in apps_order:
            app_id = app_data.get('id')
            order = app_data.get('order', 0)
            
            try:
                app = FioriApp.objects.get(id_app=app_id, active=True)
                config, created = UserAppConfig.objects.get_or_create(
                    user=user,
                    app=app,
                    defaults={'custom_order': order}
                )
                
                if not created:
                    config.custom_order = order
                    config.save(update_fields=['custom_order'])
            
            except FioriApp.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'message': 'Orden guardado correctamente'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def toggle_app_visibility(request):
    """
    AJAX endpoint para mostrar/ocultar una app.
    
    POST /fiori/api/toggle-visibility/
    Body: {"app_id": 1, "visible": true}
    """
    import json
    
    try:
        data = json.loads(request.body)
        app_id = data.get('app_id')
        visible = data.get('visible', True)
        user = request.user
        
        app = FioriApp.objects.get(id_app=app_id, active=True)
        
        config, created = UserAppConfig.objects.get_or_create(
            user=user,
            app=app,
            defaults={'is_visible': visible}
        )
        
        if not created:
            config.is_visible = visible
            config.save(update_fields=['is_visible'])
        
        return JsonResponse({
            'success': True,
            'message': f'App {"visible" if visible else "oculta"}'
        })
    
    except FioriApp.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'App no encontrada'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def toggle_favorite(request):
    """
    AJAX endpoint para marcar/desmarcar favorito.
    
    POST /fiori/api/toggle-favorite/
    Body: {"app_id": 1, "favorite": true}
    """
    import json
    
    try:
        data = json.loads(request.body)
        app_id = data.get('app_id')
        favorite = data.get('favorite', False)
        user = request.user
        
        app = FioriApp.objects.get(id_app=app_id, active=True)
        
        config, created = UserAppConfig.objects.get_or_create(
            user=user,
            app=app,
            defaults={'is_favorite': favorite}
        )
        
        if not created:
            config.is_favorite = favorite
            config.save(update_fields=['is_favorite'])
        
        return JsonResponse({
            'success': True,
            'message': f'App {"agregada a" if favorite else "removida de"} favoritas'
        })
    
    except FioriApp.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'App no encontrada'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def dashboard_stats(request):
    """
    Vista JSON con estadísticas del dashboard.
    
    GET /fiori/api/dashboard-stats/
    """
    user = request.user
    
    # Apps disponibles
    if user.is_superuser or user.groups.filter(name='Supervisor/Jefe de Área').exists():
        total_apps = FioriApp.objects.filter(active=True).count()
    else:
        total_apps = FioriApp.objects.filter(
            active=True
        ).filter(
            Q(allowed_groups__in=user.groups.all()) |
            Q(allowed_groups__isnull=True)
        ).distinct().count()
    
    # Configuraciones del usuario
    visible_apps = UserAppConfig.objects.filter(
        user=user,
        is_visible=True,
        app__active=True
    ).count()
    
    favorite_apps = UserAppConfig.objects.filter(
        user=user,
        is_favorite=True,
        app__active=True
    ).count()
    
    # Total de accesos
    total_accesses = UserAppConfig.objects.filter(
        user=user
    ).aggregate(total=models.Sum('access_count'))['total'] or 0
    
    stats = {
        'total_apps': total_apps,
        'visible_apps': visible_apps if visible_apps > 0 else total_apps,
        'favorite_apps': favorite_apps,
        'total_accesses': total_accesses
    }
    
    return JsonResponse(stats)