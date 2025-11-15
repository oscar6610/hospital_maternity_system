from django.db import models


class CatNacionalidad(models.Model):
    id_nacionalidad = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'cat_nacionalidad'
        verbose_name = 'Nacionalidad'
        verbose_name_plural = 'Nacionalidades'
    
    def __str__(self):
        return self.nombre


class CatPuebloOriginario(models.Model):
    id_pueblo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'cat_pueblo_originario'
        verbose_name = 'Pueblo Originario'
        verbose_name_plural = 'Pueblos Originarios'
    
    def __str__(self):
        return self.nombre


class CatComplicacionParto(models.Model):
    id_complicacion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'cat_complicacion_parto'
        verbose_name = 'Complicación de Parto'
        verbose_name_plural = 'Complicaciones de Parto'
    
    def __str__(self):
        return self.nombre


class CatRobson(models.Model):
    id_robson = models.AutoField(primary_key=True)
    grupo = models.CharField(max_length=10)
    descripcion = models.TextField()
    
    class Meta:
        db_table = 'cat_robson'
        verbose_name = 'Clasificación Robson'
        verbose_name_plural = 'Clasificaciones Robson'
    
    def __str__(self):
        return f"Grupo {self.grupo}"


class CatTipoParto(models.Model):
    id_tipo_parto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'cat_tipo_parto'
        verbose_name = 'Tipo de Parto'
        verbose_name_plural = 'Tipos de Parto'
    
    def __str__(self):
        return self.nombre