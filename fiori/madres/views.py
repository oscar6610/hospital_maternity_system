"""
Vistas HTML para la App Fiori de Madres
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from maternity.models import MadrePaciente, Embarazo, Parto
from catalogs.models import CatNacionalidad, CatPuebloOriginario
from core.rbac_utils import requiere_permiso


@login_required
@requiere_permiso('maternity.view_madrepaciente')
def madres_list(request):
    """
    Vista principal de lista de madres.
    Renderiza la plantilla list.html con filtros.
    """
    # Los datos se cargan vía API desde el frontend
    context = {
        'page_title': 'Gestión de Madres Pacientes',
        'has_add_permission': request.user.has_perm('maternity.add_madrepaciente'),
        'has_change_permission': request.user.has_perm('maternity.change_madrepaciente'),
        'has_delete_permission': request.user.has_perm('maternity.delete_madrepaciente'),
    }
    return render(request, 'fiori/madres/list.html', context)


@login_required
@requiere_permiso('maternity.add_madrepaciente')
def madres_create(request):
    """
    Vista de creación de madre.
    """
    # Obtener catálogos para formulario
    nacionalidades = CatNacionalidad.objects.all()
    pueblos_originarios = CatPuebloOriginario.objects.all()
    
    context = {
        'page_title': 'Registrar Madre Paciente',
        'nacionalidades': nacionalidades,
        'pueblos_originarios': pueblos_originarios,
        'action': 'create'
    }
    return render(request, 'fiori/madres/form.html', context)


@login_required
@requiere_permiso('maternity.view_madrepaciente')
def madres_detail(request, id_madre):
    """
    Vista de detalle de una madre.
    """
    madre = get_object_or_404(MadrePaciente, id_madre=id_madre)
    
    context = {
        'page_title': f'Detalle: {madre.nombre_completo()}',
        'madre': madre,
        'has_change_permission': request.user.has_perm('maternity.change_madrepaciente'),
    }
    return render(request, 'fiori/madres/detail.html', context)


@login_required
@requiere_permiso('maternity.change_madrepaciente')
def madres_edit(request, id_madre):
    """
    Vista de edición de madre.
    """
    madre = get_object_or_404(MadrePaciente, id_madre=id_madre)
    nacionalidades = CatNacionalidad.objects.all()
    pueblos_originarios = CatPuebloOriginario.objects.all()
    
    context = {
        'page_title': f'Editar: {madre.nombre_completo()}',
        'madre': madre,
        'nacionalidades': nacionalidades,
        'pueblos_originarios': pueblos_originarios,
        'action': 'edit'
    }
    return render(request, 'fiori/madres/form.html', context)


@login_required
@requiere_permiso('maternity.view_embarazo')
def madres_embarazos(request, id_madre):
    """
    Vista de embarazos de una madre.
    """
    madre = get_object_or_404(MadrePaciente, id_madre=id_madre)
    
    context = {
        'page_title': f'Embarazos: {madre.nombre_completo()}',
        'madre': madre,
    }
    return render(request, 'fiori/madres/embarazos.html', context)


@login_required
@requiere_permiso('maternity.view_parto')
def madres_partos(request, id_madre):
    """
    Vista de partos de una madre.
    """
    madre = get_object_or_404(MadrePaciente, id_madre=id_madre)
    
    context = {
        'page_title': f'Partos: {madre.nombre_completo()}',
        'madre': madre,
    }
    return render(request, 'fiori/madres/partos.html', context)


@login_required
@requiere_permiso('maternity.view_iveatencion')
def ive_list(request):
    """
    Vista de lista de atenciones IVE.
    """
    context = {
        'page_title': 'Atenciones IVE',
        'has_add_permission': request.user.has_perm('maternity.add_iveatencion'),
    }
    return render(request, 'fiori/madres/ive_list.html', context)